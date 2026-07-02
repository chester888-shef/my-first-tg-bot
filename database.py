import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()
password =os.getenv('password')
host = "localhost"
port = '5432'
user = ('postgres')
database = 'finance_bot_db'

def get_connection():
    try:
        # Додай цей рядок прямо перед conn = psycopg2.connect(...)
        print(
            f"--- ДЕБАГ БАЗИ --- \nHost: {host}\nPort: {port}\nUser: {user}\nDB: {database}\nPassword: {password}\n------------------")
        conn = psycopg2.connect(password = password ,host = host , port = port, user = user, database = database)
        return conn
    except psycopg2.Error as e:
        print(e)
if __name__ == "__main__":
    alert = get_connection()
    if alert is not None:
        print('Всьо канає ')
        alert.close()

def add_transactions(category, amount, trans_type):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = "INSERT INTO transactions (category, amount, type) VALUES (%s, %s, %s)"
        cursor.execute(sql, (category, amount, trans_type))
        conn.commit()
        cursor.close()
        print('всьо заєбісь ')
    except psycopg2.Error as e:
        print(e)
    finally:
        conn.close()

def add_goals(amount):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = "UPDATE goals SET amount = %s "
        cursor.execute(sql, (amount,))
        conn.commit()
        cursor.close()
        print("чотко всьо нахуй ")
    except psycopg2.Error as e:
        print(e)
    finally:
        conn.close()


def get_statistics(period):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if period == 'stats_week':
            sql = "SELECT*FROM transactions WHERE DATE(date) >= CURRENT_DATE - INTERVAL '7 days'"
        elif period == 'stats_month':
            sql = "SELECT*FROM transactions WHERE DATE(date) >= CURRENT_DATE - INTERVAL '30 days'"
        elif period == 'stats_year':
            sql = "SELECT*FROM transactions WHERE DATE(date) >= CURRENT_DATE - INTERVAL '365 days'"
        elif period == 'stats_all':
            sql = "SELECT * FROM transactions "
        cursor.execute(sql)
        rows = cursor.fetchall()
        return rows

    except psycopg2.Error as e:
        print(e)
        return []
    finally:
        cursor.close()
        conn.close()


def get_current_goal():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = "SELECT amount FROM goals ORDER BY id DESC LIMIT 1"
        cursor.execute(sql)
        row = cursor.fetchone()

        if row:
            return row[0]
        return None

    except psycopg2.Error as e:
        print(e)
        return None
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    add_transactions('Чайові Гастробюро', 850, 'expense_me')