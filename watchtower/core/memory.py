import sqlite3
import json

class MemoryStore:
    def __init__(self, db_path="pentest_memory.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target TEXT,
                tool TEXT,
                output TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target TEXT,
                vulnerability TEXT,
                details TEXT
            )
        """)
        self.conn.commit()
    
    def log_observation(self, target, tool, output):
        self.cursor.execute("INSERT INTO observations (target, tool, output) VALUES (?, ?, ?)", (target, tool, output))
        self.conn.commit()

    def log_finding(self, target, vulnerability, details):
        self.cursor.execute("INSERT INTO findings (target, vulnerability, details) VALUES (?, ?, ?)", (target, vulnerability, json.dumps(details)))
        self.conn.commit()

    def get_all_observations(self):
        self.cursor.execute("SELECT tool, output FROM observations")
        return self.cursor.fetchall()

    def get_all_findings(self):
        self.cursor.execute("SELECT target, vulnerability, details FROM findings")
        return self.cursor.fetchall()
