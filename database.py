import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()

class OpenDatabase:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
    def __enter__ (self):   
            try:
                print("Підключаюсь до бази...")
                self.conn = psycopg2.connect(self.db_url)
                return self.conn   
            except psycopg2.Error as e:
                print(f"Критична помилка підключення до БД: {e}")
                raise e

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
             self.conn.commit()
             self.conn.close()


def add_transactions (category, amount, trans_type,user_id ):
    try:
        with OpenDatabase() as conn:
                with conn.cursor() as cursor:
                    sql = "INSERT INTO transactions (category, amount, type, user_id) VALUES (%s, %s, %s, %s) "
                    cursor.execute(sql, (category, amount, trans_type, user_id))
                    print('всьо заєбісь ')
    except psycopg2.Error as e:
        print(e)            

def add_goals(amount, user_id):
    try:    
        with OpenDatabase() as conn:
                with conn.cursor() as cursor:
                    sql = "UPDATE goals  SET amount = %s WHERE id = %s "
                    cursor.execute(sql, (amount,user_id))
                print("чотко всьо  ")
    except psycopg2.Error as e:
                print(e)



def get_statistics(period, user_id):
    with OpenDatabase() as conn:
        try:
            cursor = conn.cursor()
            if period == 'stats_week':
                    sql = "SELECT * FROM transactions WHERE DATE(date) >= CURRENT_DATE - INTERVAL '7 days' AND user_id = %s"
            elif period == 'stats_month':
                    sql = "SELECT * FROM transactions WHERE DATE(date) >= CURRENT_DATE - INTERVAL '30 days' AND user_id = %s"
            elif period == 'stats_year':
                    sql = "SELECT * FROM transactions WHERE DATE(date) >= CURRENT_DATE - INTERVAL '365 days' AND user_id = %s"
            elif period == 'stats_all':
                    sql = "SELECT * FROM transactions WHERE user_id = %s"
            cursor.execute(sql, (user_id,))
            rows = cursor.fetchall()
            return rows

        except psycopg2.Error as e:
            print(e)
            return []



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



