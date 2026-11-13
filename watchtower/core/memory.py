import sqlite3
import json
import uuid
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_run_id() -> str:
    """A sortable, unique identifier for a single pentest run."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"{ts}-{uuid.uuid4().hex[:6]}"


class MemoryStore:
    def __init__(self, db_path="pentest_memory.db", run_id=None):
        self.run_id = run_id
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._create_tables()
        self._migrate()
        self.conn.commit()

    def _create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                target TEXT,
                tool TEXT,
                output TEXT,
                created_at TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                target TEXT,
                vulnerability TEXT,
                details TEXT,
                created_at TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                target TEXT,
                created_at TEXT
            )
        """)

    def _migrate(self):
        # Add run scoping columns to databases created before run scoping existed.
        for table in ("observations", "findings"):
            cols = [row[1] for row in self.cursor.execute(f"PRAGMA table_info({table})").fetchall()]
            if "run_id" not in cols:
                self.cursor.execute(f"ALTER TABLE {table} ADD COLUMN run_id TEXT")
            if "created_at" not in cols:
                self.cursor.execute(f"ALTER TABLE {table} ADD COLUMN created_at TEXT")

    def start_run(self, target):
        """Register the current run and return its id."""
        if not self.run_id:
            self.run_id = new_run_id()
        self.cursor.execute(
            "INSERT OR REPLACE INTO runs (run_id, target, created_at) VALUES (?, ?, ?)",
            (self.run_id, target, _now()),
        )
        self.conn.commit()
        return self.run_id

    def log_observation(self, target, tool, output):
        self.cursor.execute(
            "INSERT INTO observations (run_id, target, tool, output, created_at) VALUES (?, ?, ?, ?, ?)",
            (self.run_id, target, tool, output, _now()),
        )
        self.conn.commit()

    def log_finding(self, target, vulnerability, details):
        self.cursor.execute(
            "INSERT INTO findings (run_id, target, vulnerability, details, created_at) VALUES (?, ?, ?, ?, ?)",
            (self.run_id, target, vulnerability, json.dumps(details), _now()),
        )
        self.conn.commit()

    def latest_run_id(self):
        row = self.cursor.execute(
            "SELECT run_id FROM runs ORDER BY created_at DESC, rowid DESC LIMIT 1"
        ).fetchone()
        if row and row[0]:
            return row[0]
        # Fallback for pre-scoping databases that have no runs table rows.
        row = self.cursor.execute(
            "SELECT run_id FROM findings WHERE run_id IS NOT NULL ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return row[0] if row else None

    def get_run(self, run_id):
        return self.cursor.execute(
            "SELECT run_id, target, created_at FROM runs WHERE run_id = ?", (run_id,)
        ).fetchone()

    def list_runs(self):
        return self.cursor.execute(
            "SELECT run_id, target, created_at FROM runs ORDER BY created_at DESC"
        ).fetchall()

    def get_all_observations(self, run_id=None):
        if run_id is None:
            self.cursor.execute("SELECT tool, output FROM observations")
        else:
            self.cursor.execute("SELECT tool, output FROM observations WHERE run_id = ?", (run_id,))
        return self.cursor.fetchall()

    def get_all_findings(self, run_id=None):
        if run_id is None:
            self.cursor.execute("SELECT target, vulnerability, details FROM findings")
        else:
            self.cursor.execute(
                "SELECT target, vulnerability, details FROM findings WHERE run_id = ?", (run_id,)
            )
        return self.cursor.fetchall()
