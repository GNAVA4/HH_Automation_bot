import sqlite3
import logging
from datetime import datetime
import os

logger = logging.getLogger("HH_Bot")


class DBManager:
    def __init__(self, db_name=os.path.join("data", "hh_bot.db")):
        self.db_name = db_name
        if not os.path.exists("data"):
            os.makedirs("data")
        self.init_db()

    def init_db(self):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                # Добавили поле profile
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS applications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        vacancy_title TEXT,
                        company_name TEXT,
                        url TEXT,
                        status TEXT,
                        profile TEXT, 
                        timestamp DATETIME
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"DB Init Error: {e}")

    def add_application(self, title, company, url, profile, status="success"):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO applications (vacancy_title, company_name, url, status, profile, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (title, company, url, status, profile, datetime.now()))
                conn.commit()
        except Exception as e:
            logger.error(f"DB Add Error: {e}")

    def get_all_applications(self, profile_filter=None):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                if profile_filter:
                    cursor.execute(
                        "SELECT vacancy_title, company_name, timestamp, profile FROM applications WHERE profile=? ORDER BY id DESC",
                        (profile_filter,))
                else:
                    cursor.execute(
                        "SELECT vacancy_title, company_name, timestamp, profile FROM applications ORDER BY id DESC")
                return cursor.fetchall()
        except Exception as e:
            return []

    def get_stats(self, profile_filter=None):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()

                query_total = "SELECT COUNT(*) FROM applications WHERE status='success'"
                query_today = "SELECT COUNT(*) FROM applications WHERE status='success' AND date(timestamp) = date('now')"
                params = []

                if profile_filter:
                    query_total += " AND profile=?"
                    query_today += " AND profile=?"
                    params = [profile_filter]

                cursor.execute(query_total, params)
                total = cursor.fetchone()[0]

                cursor.execute(query_today, params)
                today = cursor.fetchone()[0]

                return total, today
        except:
            return 0, 0