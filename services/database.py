import sqlite3

DB_PATH = "bot_database.db"


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                username TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT,
                url TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def add_user(self, user_id, first_name, username):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO users (user_id, first_name, username) VALUES (?, ?, ?)",
            (user_id, first_name, username)
        )
        self.conn.commit()

    def add_history(self, user_id, action, url):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO history (user_id, action, url) VALUES (?, ?, ?)",
            (user_id, action, url)
        )
        self.conn.commit()

    def get_history(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM history WHERE user_id = ? ORDER BY timestamp DESC",
            (user_id,)
        )
        return cursor.fetchall()
