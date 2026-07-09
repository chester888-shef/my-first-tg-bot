import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()
password =os.getenv('password')
host = "localhost"
port = '5432'
user = ('postgres')
database = 'finance_bot_db'

class OpenDatabase:
    def __init__(self):
        self.password = os.getenv('password')
        self.host = "localhost"
        self.port = "5432"
        self.user = "postgres"
        self.database = "finance_bot_db"   
    def __enter__ (self):   
            try:
                print("Підключаюсь до бази...")
                self.conn = psycopg2.connect(
                    password=self.password,
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    database=self.database
                )
                return self.conn   
            except psycopg2.Error as e:
                print(f"Критична помилка підключення до БД: {e}")
                raise e

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
             self.conn.commit()
             self.conn.close()


def add_transactions(category, amount, trans_type):
    try:
        with OpenDatabase() as conn:
                with conn.cursor() as cursor:
                    sql = "INSERT INTO transactions (category, amount, type) VALUES (%s, %s, %s)"
                    cursor.execute(sql, (category, amount, trans_type))
                    print('всьо заєбісь ')
    except psycopg2.Error as e:
        print(e)            

def add_goals(amount):
    try:    
        with OpenDatabase() as conn:
                with conn.cursor() as cursor:
                    sql = "UPDATE goals  SET amount = %s WHERE id = %s "
                    cursor.execute(sql, (amount,id))
                print("чотко всьо  ")
    except psycopg2.Error as e:
                print(e)



def get_statistics(period):
    with OpenDatabase() as conn:
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
    with OpenDatabase() as conn:
        try:
            with conn.cursor() as cursor:
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


