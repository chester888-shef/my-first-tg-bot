
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
            logger.error("Помилка в транзакції, роблю rollback: %s", exc_val)
            self.conn.rollback()

        self.conn.close()
        return False


def add_transactions(category, amount, trans_type, user_id):
    try:
        with OpenDatabase() as conn:
            with conn.cursor() as cursor:
                sql = (
                    "INSERT INTO transactions (category, amount, type, user_id) "
                    "VALUES (%s, %s, %s, %s)"
                )
                cursor.execute(sql, (category, amount, trans_type, user_id))
        logger.info("Транзакцію додано: user_id=%s, %s %s", user_id, trans_type, amount)
        return True
    except psycopg2.Error:
        logger.exception("Не вдалося додати транзакцію")
        return False


def add_goals(amount, user_id):

    try:
        with OpenDatabase() as conn:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO goals (id, amount)
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
                        "SELECT * FROM transactions "
                        "WHERE DATE(date) >= CURRENT_DATE - INTERVAL %s "
                        "AND user_id = %s"
                    )
                    cursor.execute(sql, (period_to_interval[period], user_id))
                elif period == "stats_all":
                    sql = "SELECT * FROM transactions WHERE user_id = %s"
                    cursor.execute(sql, (user_id,))
                else:
                    logger.warning("Невідомий період статистики: %s", period)
                    return []

                return cursor.fetchall()
    except psycopg2.Error:
        logger.exception("Не вдалося отримати статистику")
        return []


def get_current_goal(user_id):
    try:
        with OpenDatabase() as conn:
            with conn.cursor() as cursor:
                sql = "SELECT amount FROM goals WHERE id = %s"
                cursor.execute(sql, (user_id,))
                row = cursor.fetchone()
            return row[0] if row else None
    except psycopg2.Error:
        logger.exception("Не вдалося отримати поточну ціль")
        return None