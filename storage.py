import sqlite3
from pathlib import Path

DB_PATH = Path("data") / "users.db"
DB_PATH.parent.mkdir(exist_ok=True)

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    salary REAL,
                    hours_per_month REAL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS purchases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    amount REAL,
                    hours_needed REAL,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )
            """)
            conn.commit()
        except Exception as e:
            print("Ошибка при создании таблиц:", e)

        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        print("Таблицы в БД:", tables)



def save_user(user_id, salary, hours):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO users (user_id, salary, hours_per_month)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET salary=excluded.salary, hours_per_month=excluded.hours_per_month
        """, (user_id, salary, hours))
        conn.commit()


def load_user(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("""
            SELECT salary, hours_per_month FROM users WHERE user_id = ?
        """, (user_id,)).fetchone()
        return row if row else None

def save_purchase(user_id, amount, hours_needed):
    print(user_id, amount, hours_needed)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO purchases (user_id, amount, hours_needed)
            VALUES (?, ?, ?)
        """, (user_id, amount, hours_needed))
        conn.commit()