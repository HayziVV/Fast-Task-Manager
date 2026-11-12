import os
import sqlite3
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from urllib.parse import unquote

import database
import routers.projects as projects_module


class TestDatabaseAndProjects(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Create a temp database file for clean test isolation
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.temp_db_fd)

        # Patch get_connection in both modules to use the temp DB
        self.patcher_db = patch("database.get_connection", side_effect=self._get_test_connection)
        self.patcher_proj = patch("routers.projects.get_connection", side_effect=self._get_test_connection)
        self.patcher_db.start()
        self.patcher_proj.start()

    def tearDown(self):
        self.patcher_db.stop()
        self.patcher_proj.stop()
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def _get_test_connection(self):
        conn = sqlite3.connect(self.temp_db_path, timeout=20)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def test_imported_issues_table_exists(self):
        database.init_db()
        conn = self._get_test_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='imported_issues'")
        table = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(table, "Tabela 'imported_issues' deve existir no banco de dados após init_db()")

    def test_imported_issues_columns(self):
        database.init_db()
        conn = self._get_test_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(imported_issues)")
        columns = {row[1]: row[2].upper() for row in cursor.fetchall()}
        conn.close()

        expected_columns = {
            "import_id": "INTEGER",
            "user_id": "INTEGER",
            "issue_number": "INTEGER",
            "title": "TEXT",
            "body": "TEXT",
            "state": "TEXT",
            "repo_url": "TEXT",
            "html_url": "TEXT",
            "imported_at": "TEXT",
        }
        for col, col_type in expected_columns.items():
            self.assertIn(col, columns, f"Coluna '{col}' deve existir na tabela 'imported_issues'")
            self.assertEqual(columns[col], col_type, f"Coluna '{col}' deve ter o tipo '{col_type}'")

    async def test_update_project_success(self):
        database.init_db()
        conn = self._get_test_connection()
        cursor = conn.cursor()
        # Create user
        cursor.execute("INSERT INTO users (user_id, username, password) VALUES (1, 'testuser', 'pass')")
        # Create project
        cursor.execute("INSERT INTO projects (project_id, user_id, projectName, projectDescription, initialDate) VALUES (10, 1, 'Old Name', 'Old Desc', '2026-01-01 00:00:00')")
        conn.commit()
        conn.close()

        self.assertTrue(hasattr(projects_module, "update_project"), "routers.projects deve possuir a função update_project")

        request = MagicMock()
        request.session = {"user_id": 1}

        response = await projects_module.update_project(
            request=request,
            project_id=10,
            projectName="New Project Name",
            projectDescription="New Project Description",
        )

        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers["location"], "/projects")

        conn = self._get_test_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT projectName, projectDescription FROM projects WHERE project_id = 10")
        row = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row[0], "New Project Name")
        self.assertEqual(row[1], "New Project Description")

    async def test_update_project_unauthorized_redirects_home(self):
        self.assertTrue(hasattr(projects_module, "update_project"), "routers.projects deve possuir a função update_project")

        request = MagicMock()
        request.session = {}  # Not logged in

        response = await projects_module.update_project(
            request=request,
            project_id=10,
            projectName="New Project Name",
            projectDescription="New Project Description",
        )

        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers["location"], "/")

    async def test_update_project_different_user_does_not_modify(self):
        database.init_db()
        conn = self._get_test_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (user_id, username, password) VALUES (1, 'owner', 'pass')")
        cursor.execute("INSERT INTO users (user_id, username, password) VALUES (2, 'other', 'pass')")
        cursor.execute("INSERT INTO projects (project_id, user_id, projectName, projectDescription, initialDate) VALUES (20, 1, 'Owner Name', 'Owner Desc', '2026-01-01 00:00:00')")
        conn.commit()
        conn.close()

        self.assertTrue(hasattr(projects_module, "update_project"), "routers.projects deve possuir a função update_project")

        # User 2 tries to update User 1's project
        request = MagicMock()
        request.session = {"user_id": 2}

        response = await projects_module.update_project(
            request=request,
            project_id=20,
            projectName="Hacked Name",
            projectDescription="Hacked Desc",
        )

        self.assertEqual(response.status_code, 303)

        conn = self._get_test_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT projectName, projectDescription FROM projects WHERE project_id = 20")
        row = cursor.fetchone()
        conn.close()

        self.assertEqual(row[0], "Owner Name")
        self.assertEqual(row[1], "Owner Desc")

    async def test_update_project_db_error_redirects_with_error(self):
        self.assertTrue(hasattr(projects_module, "update_project"), "routers.projects deve possuir a função update_project")

        request = MagicMock()
        request.session = {"user_id": 1}

        with patch("routers.projects.get_connection", side_effect=sqlite3.OperationalError("DB Locked")):
            response = await projects_module.update_project(
                request=request,
                project_id=10,
                projectName="Any",
                projectDescription="Any",
            )
            self.assertEqual(response.status_code, 303)
            self.assertEqual(unquote(response.headers["location"]), "/projects?error=Erro ao atualizar projeto.")


def test_imported_issues_table_exists():
    """Module-level function test conforming to the task brief specification."""
    database.init_db()
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='imported_issues'")
    res = cursor.fetchone()
    conn.close()
    assert res is not None, "Tabela 'imported_issues' não encontrada no banco."


if __name__ == "__main__":
    unittest.main()
