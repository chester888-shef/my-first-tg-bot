"""
Робота з PostgreSQL.

ЗМІНИ порівняно з оригіналом:
1. OpenDatabase.__exit__ тепер робить rollback(), якщо всередині with
   стався виняток, і commit() — тільки якщо все пройшло успішно.
   Раніше commit() викликався завжди, незалежно від помилок.
2. goals тепер прив'язані до конкретного користувача (upsert), а не
   до "останнього рядка в таблиці" — інакше всі користувачі бота
   ділили одну спільну ціль.
   СХЕМА БД: в таблиці goals немає окремої колонки user_id — колонка
   `id` і є telegram user_id (саме так, судячи з оригінального
   запиту `WHERE id = %s` з user_id як параметром, це й задумувалось
   автором). Тому окремих ALTER TABLE не потрібно — просто робимо
   INSERT ... ON CONFLICT (id) DO UPDATE замість "голого" UPDATE,
   який мовчки нічого не робив для нового користувача (0 рядків
   оновлено, бо рядка з таким id ще не існувало).
3. get_statistics використовує RealDictCursor — рядки повертаються як
   dict (row['amount'] замість row[3]), щоб код у function.py не
   залежав від порядку колонок.
4. Прибрано друки з ненормативною лексикою, додано logging замість print.
5. Підключення знову через ОДНУ змінну DATABASE_URL (вона вже й так
   стояла на Render — не треба нічого додатково там налаштовувати).
   Але тепер рядок розбирається через urllib.parse.urlsplit (надійний,
   вбудований у Python парсер URL, який правильно обробляє
   percent-encoded символи) — і кожна частина (host, port, user,
   password, dbname) передається в psycopg2.connect() ОКРЕМИМ
   параметром, а не одним конкатенованим рядком. Так спецсимволи в
   паролі більше не зможуть "зсунути" сусідні частини рядка
   (саме це раніше стало причиною помилки: шматок пароля потрапив
   туди, де мав бути порт).
   Якщо колись знадобиться — код так само підхопить окремі
   DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD, якщо DATABASE_URL
   не задано (пріоритет: DATABASE_URL, якщо він є).
"""

import logging
import os
from urllib.parse import urlsplit, unquote

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class OpenDatabase:
    """Контекстний менеджер для підключення до БД з коректним commit/rollback."""

    def __init__(self):
        db_url = os.getenv("DATABASE_URL")

        if db_url:
            parsed = urlsplit(db_url)
            self.host = parsed.hostname
            self.port = parsed.port or 5432
            self.dbname = (parsed.path or "/postgres").lstrip("/") or "postgres"
            self.user = unquote(parsed.username) if parsed.username else None
            self.password = unquote(parsed.password) if parsed.password else None
        else:
            self.host = os.getenv("DB_HOST")
            self.port = os.getenv("DB_PORT", "5432")
            self.dbname = os.getenv("DB_NAME", "postgres")
            self.user = os.getenv("DB_USER")
            self.password = os.getenv("DB_PASSWORD")

        self.conn = None

        missing = [
            name
            for name, value in [
                ("host", self.host),
                ("user", self.user),
                ("password", self.password),
            ]
            if not value
        ]
        if missing:
            raise RuntimeError(
                f"Не вдалося визначити параметри підключення до БД "
                f"(відсутні: {', '.join(missing)}). Перевірте, що "
                f"DATABASE_URL у Render Environment задано і має "
                f"правильний формат postgresql://user:pass@host:port/db."
            )

    def __enter__(self):
        logger.info("Підключаюсь до бази...")
        # Кожен параметр передається окремо — пароль ніде не
        # конкатенується в один рядок, тож спецсимволи в ньому
        # (@ : / $ ! тощо) нічого не зламають.
        self.conn = psycopg2.connect(
            host=self.host,
            port=self.port,
            dbname=self.dbname,
            user=self.user,
            password=self.password,
        )
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn is None:
            return False

        if exc_type is None:
            self.conn.commit()
        else:
            # Був виняток всередині блоку with — не комітимо биту транзакцію
            logger.error("Помилка в транзакції, роблю rollback: %s", exc_val)
            self.conn.rollback()

        self.conn.close()
        # False -> не гасимо виняток, хай піде далі й буде оброблений
        # у функції, що викликала with OpenDatabase()
        return False


def add_transactions(category, amount, trans_type, user_id):
    """
    Повертає True/False — раніше помилка лише логувалась, а виклик
    у main.py завжди показував користувачу "успішно внесено", навіть
    якщо запис у БД насправді провалився.
    """
    try:
        with OpenDatabase() as conn:
            with conn.cursor() as cursor:
                sql = (
                    "INSERT INTO public.transactions (category, amount, type, user_id) "
                    "VALUES (%s, %s, %s, %s)"
                )
                cursor.execute(sql, (category, amount, trans_type, user_id))
        logger.info("Транзакцію додано: user_id=%s, %s %s", user_id, trans_type, amount)
        return True
    except psycopg2.Error:
        logger.exception("Не вдалося додати транзакцію")
        return False


def add_goals(amount, user_id):
    """
    Встановлює/оновлює ціль конкретного користувача (upsert).
    Повертає True/False — раніше помилка лише логувалась, а
    save_target_function у main.py завжди показував "успішно
    прийнята", навіть якщо запис у БД насправді провалився.

    В таблиці goals немає окремої колонки user_id — id рядка і є
    telegram user_id (по одному рядку goals на користувача).
    """
    try:
        with OpenDatabase() as conn:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO public.goals (id, amount)
                    VALUES (%s, %s)
                    ON CONFLICT (id)
                    DO UPDATE SET amount = EXCLUDED.amount
                """
                cursor.execute(sql, (user_id, amount))
        logger.info("Ціль оновлено: user_id=%s, amount=%s", user_id, amount)
        return True
    except psycopg2.Error:
        logger.exception("Не вдалося зберегти ціль")
        return False


def get_statistics(period, user_id):
    period_to_interval = {
        "stats_week": "7 days",
        "stats_month": "30 days",
        "stats_year": "365 days",
    }

    try:
        with OpenDatabase() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                if period in period_to_interval:
                    sql = (
                        "SELECT * FROM public.transactions "
                        "WHERE DATE(date) >= CURRENT_DATE - INTERVAL %s "
                        "AND user_id = %s"
                    )
                    cursor.execute(sql, (period_to_interval[period], user_id))
                elif period == "stats_all":
                    sql = "SELECT * FROM public.transactions WHERE user_id = %s"
                    cursor.execute(sql, (user_id,))
                else:
                    logger.warning("Невідомий період статистики: %s", period)
                    return []

                return cursor.fetchall()
    except psycopg2.Error:
        logger.exception("Не вдалося отримати статистику")
        return []


def get_current_goal(user_id):
    """
    ЗМІНА СИГНАТУРИ: тепер приймає user_id (раніше не приймав жодного
    аргументу і брав `ORDER BY id DESC LIMIT 1` — тобто "чию завгодно
    останню ціль в таблиці", спільну для всіх користувачів).
    Виклик у main.py теж оновлено.
    id в goals = telegram user_id, тому шукаємо просто по id.
    """
    try:
        with OpenDatabase() as conn:
            with conn.cursor() as cursor:
                sql = "SELECT amount FROM public.goals WHERE id = %s"
                cursor.execute(sql, (user_id,))
                row = cursor.fetchone()
            return row[0] if row else None
    except psycopg2.Error:
        logger.exception("Не вдалося отримати поточну ціль")
        return None


def debug_connection_info():
    """
    ТИМЧАСОВА діагностична функція — прибрати після того, як з'ясуємо
    причину "relation does not exist". Виводить у логи, до якої саме
    бази/користувача підключається БОТ і які таблиці він реально бачить.
    Порівнюємо це з тим, що видно в Supabase SQL Editor — якщо
    значення відрізняються, бот підключений не туди, куди дивиться
    людина в браузері.
    """
    try:
        with OpenDatabase() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT current_database(), current_user, current_schemas(true);")
                db_name, db_user, schemas = cursor.fetchone()
                logger.warning(
                    "DEBUG DB INFO: database=%s user=%s visible_schemas=%s",
                    db_name, db_user, schemas,
                )

                cursor.execute(
                    "SELECT table_schema, table_name FROM information_schema.tables "
                    "WHERE table_schema NOT IN ('pg_catalog', 'information_schema') "
                    "ORDER BY table_schema, table_name;"
                )
                tables = cursor.fetchall()
                logger.warning("DEBUG TABLES VISIBLE TO BOT: %s", tables)
    except psycopg2.Error:
        logger.exception("DEBUG: не вдалося отримати діагностичну інформацію")