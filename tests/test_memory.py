import os
import sqlite3
import tempfile
import unittest

from watchtower.core.memory import MemoryStore, new_run_id

try:
    import langchain_core  # noqa: F401
    _HAS_LANGCHAIN = True
except Exception:
    _HAS_LANGCHAIN = False


class RunScopingTests(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

    def tearDown(self):
        try:
            os.unlink(self.path)
        except OSError:
            pass

    def test_findings_are_scoped_by_run(self):
        m1 = MemoryStore(self.path, run_id="r1")
        m1.start_run("target-one")
        m1.log_finding("target-one", "Finding A", {"severity": "High"})

        m2 = MemoryStore(self.path, run_id="r2")
        m2.start_run("target-two")
        m2.log_finding("target-two", "Finding B", {"severity": "Low"})

        reader = MemoryStore(self.path)
        self.assertEqual(len(reader.get_all_findings("r1")), 1)
        self.assertEqual(len(reader.get_all_findings("r2")), 1)
        self.assertEqual(len(reader.get_all_findings()), 2)

    def test_latest_run_id_is_most_recent(self):
        MemoryStore(self.path, run_id="r1").start_run("t1")
        MemoryStore(self.path, run_id="r2").start_run("t2")
        self.assertEqual(MemoryStore(self.path).latest_run_id(), "r2")

    def test_new_run_id_is_unique(self):
        self.assertNotEqual(new_run_id(), new_run_id())

    def test_migrates_pre_scoping_database(self):
        conn = sqlite3.connect(self.path)
        conn.execute(
            "CREATE TABLE observations (id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "target TEXT, tool TEXT, output TEXT)"
        )
        conn.execute(
            "CREATE TABLE findings (id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "target TEXT, vulnerability TEXT, details TEXT)"
        )
        conn.execute(
            "INSERT INTO findings (target, vulnerability, details) VALUES (?, ?, ?)",
            ("legacy-target", "Legacy Finding", "{}"),
        )
        conn.commit()
        conn.close()

        # Opening the store must add the new columns without losing old rows.
        m = MemoryStore(self.path)
        cols = [row[1] for row in m.cursor.execute("PRAGMA table_info(findings)").fetchall()]
        self.assertIn("run_id", cols)
        self.assertIn("created_at", cols)

        rows = m.get_all_findings()
        self.assertTrue(any(r[1] == "Legacy Finding" for r in rows))


class AnalystImportTests(unittest.TestCase):
    @unittest.skipUnless(_HAS_LANGCHAIN, "langchain is not installed in this environment")
    def test_analyst_module_has_logging(self):
        import watchtower.agents.analyst as analyst
        self.assertTrue(hasattr(analyst, "logging"))


if __name__ == "__main__":
    unittest.main()
