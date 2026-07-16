

import logging
import os

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class OpenDatabase:

    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")
        self.conn = None

    def __enter__(self):
        logger.info("Підключаюсь до бази...")
        self.conn = psycopg2.connect(self.db_url)
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
    except psycopg2.Error:
        logger.exception("Не вдалося зберегти ціль")


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