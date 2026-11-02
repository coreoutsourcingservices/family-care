"""Read-only local launcher regression tests, runnable without a DB.

From backend/: python -m unittest discover -s tests -p test_local_launcher.py
"""
import subprocess
import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from server import database_status


class LauncherTests(unittest.TestCase):
    def test_missing_db_is_not_ready(self):
        app = type('TestApp', (), {'extensions': {'database_engine': None}})()
        ready, status = database_status(app)
        self.assertFalse(ready)
        self.assertIn('DATABASE_URL', status)

    def test_private_db_exception_is_not_leaked(self):
        class FakeEngine:
            def connect(self):
                raise RuntimeError('password=DO_NOT_LOG_THIS')
        app = type('TestApp', (), {'extensions': {'database_engine': FakeEngine()}})()
        ready, status = database_status(app)
        self.assertFalse(ready)
        self.assertNotIn('DO_NOT_LOG_THIS', status)
        self.assertIn('database unreachable', status)

    def test_help_requires_no_database(self):
        result = subprocess.run([sys.executable, str(BACKEND/'server.py'), '--help'],
                                capture_output=True, text=True, cwd=BACKEND, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('--check', result.stdout)


if __name__ == '__main__':
    unittest.main()
