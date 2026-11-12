import io
import json
import os
import sqlite3
import tempfile
import unittest
import urllib.error
from urllib.parse import unquote
from unittest.mock import MagicMock, patch
import zipfile

import database
from routers.data_transfer import (
    normalize_github_issues_url,
    build_export_zip_bytes,
    export_data,
    export_data_local,
    import_github_issues,
    convert_imported_to_task,
    delete_imported_issue,
)


def test_normalize_github_url_variants():
    api_url, label = normalize_github_issues_url("tiangolo/fastapi")
    assert api_url == "https://api.github.com/repos/tiangolo/fastapi/issues?per_page=10"
    assert label == "tiangolo/fastapi"

    api_url2, label2 = normalize_github_issues_url("https://github.com/pallets/flask")
    assert api_url2 == "https://api.github.com/repos/pallets/flask/issues?per_page=10"
    assert label2 == "pallets/flask"


def test_build_export_zip_contains_all_tables():
    database.init_db()
    zip_bytes = build_export_zip_bytes()
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        assert "fast_task_manager_export.json" in zf.namelist()
        data = json.loads(zf.read("fast_task_manager_export.json").decode("utf-8"))
        for table in ["status", "users", "projects", "tasks", "notes", "imported_issues"]:
            assert table in data


class TestDataTransfer(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.temp_db_fd)

        self.patcher_db = patch("database.get_connection", side_effect=self._get_test_connection)
        self.patcher_dt = patch("routers.data_transfer.get_connection", side_effect=self._get_test_connection)
        self.patcher_db.start()
        self.patcher_dt.start()

        database.init_db()

    def tearDown(self):
        self.patcher_dt.stop()
        self.patcher_db.stop()
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)
        if os.path.exists("exports/fast_task_manager_export.zip"):
            try:
                os.remove("exports/fast_task_manager_export.zip")
            except OSError:
                pass

    def _get_test_connection(self):
        conn = sqlite3.connect(self.temp_db_path, timeout=20)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def test_normalize_github_url_variants(self):
        api_url, label = normalize_github_issues_url("tiangolo/fastapi")
        self.assertEqual(api_url, "https://api.github.com/repos/tiangolo/fastapi/issues?per_page=10")
        self.assertEqual(label, "tiangolo/fastapi")

        api_url2, label2 = normalize_github_issues_url("https://github.com/pallets/flask")
        self.assertEqual(api_url2, "https://api.github.com/repos/pallets/flask/issues?per_page=10")
        self.assertEqual(label2, "pallets/flask")

        api_url3, label3 = normalize_github_issues_url("https://github.com/pallets/flask/issues")
        self.assertEqual(api_url3, "https://api.github.com/repos/pallets/flask/issues?per_page=10")
        self.assertEqual(label3, "pallets/flask")

        api_url4, label4 = normalize_github_issues_url("https://api.github.com/repos/octocat/Hello-World/issues")
        self.assertEqual(api_url4, "https://api.github.com/repos/octocat/Hello-World/issues?per_page=10")
        self.assertEqual(label4, "octocat/Hello-World")

        api_url5, label5 = normalize_github_issues_url("https://api.github.com/repos/octocat/Hello-World/issues?per_page=5")
        self.assertEqual(api_url5, "https://api.github.com/repos/octocat/Hello-World/issues?per_page=5")
        self.assertEqual(label5, "octocat/Hello-World")

    def test_normalize_github_url_invalid(self):
        invalid_inputs = ["", "   ", "invalid", "https://google.com/foo", "http://github.com/"]
        for inp in invalid_inputs:
            with self.subTest(inp=inp):
                with self.assertRaises(ValueError):
                    normalize_github_issues_url(inp)

    def test_build_export_zip_contains_all_tables_and_excludes_passwords(self):
        conn = self._get_test_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (user_id, username, password) VALUES (1, 'alice', 'secret_hash')")
        cursor.execute("INSERT INTO projects (project_id, user_id, projectName, projectDescription, initialDate) VALUES (10, 1, 'Proj A', 'Desc A', '2026-01-01')")
        cursor.execute("INSERT INTO tasks (task_id, user_id, project_id, status_id, taskName, taskDescription, initialDate) VALUES (20, 1, 10, 0, 'Task A', 'Desc Task', '2026-01-01')")
        cursor.execute("INSERT INTO notes (note_id, task_id, user_id, content, initialDate) VALUES (30, 20, 1, 'Note content', '2026-01-01')")
        cursor.execute("INSERT INTO imported_issues (import_id, user_id, issue_number, title, body, state, repo_url, html_url, imported_at) VALUES (40, 1, 99, 'Issue 99', 'Body text', 'open', 'owner/repo', 'https://github.com/owner/repo/issues/99', '2026-01-01')")
        conn.commit()
        conn.close()

        zip_bytes = build_export_zip_bytes()
        self.assertIsInstance(zip_bytes, bytes)

        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            self.assertIn("fast_task_manager_export.json", zf.namelist())
            data = json.loads(zf.read("fast_task_manager_export.json").decode("utf-8"))

            for table in ["status", "users", "projects", "tasks", "notes", "imported_issues"]:
                self.assertIn(table, data)

            self.assertEqual(len(data["users"]), 1)
            self.assertEqual(data["users"][0]["username"], "alice")
            self.assertNotIn("password", data["users"][0])

            self.assertEqual(len(data["projects"]), 1)
            self.assertEqual(data["projects"][0]["projectName"], "Proj A")

            self.assertEqual(len(data["tasks"]), 1)
            self.assertEqual(data["tasks"][0]["taskName"], "Task A")

            self.assertEqual(len(data["notes"]), 1)
            self.assertEqual(data["notes"][0]["content"], "Note content")

            self.assertEqual(len(data["imported_issues"]), 1)
            self.assertEqual(data["imported_issues"][0]["title"], "Issue 99")

    async def test_export_get_unauthorized_and_authorized(self):
        req_unauth = MagicMock()
        req_unauth.session = {}
        res_unauth = await export_data(req_unauth)
        self.assertEqual(res_unauth.status_code, 303)
        self.assertEqual(res_unauth.headers["location"], "/")

        req_auth = MagicMock()
        req_auth.session = {"user_id": 1}
        res_auth = await export_data(req_auth)
        self.assertEqual(res_auth.status_code, 200)
        self.assertEqual(res_auth.media_type, "application/zip")
        self.assertIn("attachment; filename=fast_task_manager_export.zip", res_auth.headers.get("content-disposition", ""))
        self.assertTrue(os.path.exists("exports/fast_task_manager_export.zip"))

    async def test_export_local_post(self):
        req_unauth = MagicMock()
        req_unauth.session = {}
        res_unauth = await export_data_local(req_unauth)
        self.assertEqual(res_unauth.status_code, 303)
        self.assertEqual(res_unauth.headers["location"], "/")

        req_auth = MagicMock()
        req_auth.session = {"user_id": 1}
        res_auth = await export_data_local(req_auth)
        self.assertEqual(res_auth.status_code, 303)
        self.assertTrue(res_auth.headers["location"].startswith("/data?success="))
        self.assertTrue(os.path.exists("exports/fast_task_manager_export.zip"))

    async def test_import_github_issues_success_and_skip_prs(self):
        conn = self._get_test_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (user_id, username, password) VALUES (1, 'bob', 'pass')")
        conn.commit()
        conn.close()

        req = MagicMock()
        req.session = {"user_id": 1}

        github_payload = [
            {
                "number": 101,
                "title": "Bug in login",
                "body": "Details about bug",
                "state": "open",
                "html_url": "https://github.com/tiangolo/fastapi/issues/101",
            },
            {
                "number": 102,
                "title": "Add feature PR",
                "body": "PR description",
                "state": "open",
                "html_url": "https://github.com/tiangolo/fastapi/pull/102",
                "pull_request": {"url": "https://api.github.com/repos/tiangolo/fastapi/pulls/102"},
            },
        ]
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(github_payload).encode("utf-8")
        mock_response.__enter__.return_value = mock_response

        with patch("urllib.request.urlopen", return_value=mock_response):
            res = await import_github_issues(req, repo_or_url="tiangolo/fastapi")

        self.assertEqual(res.status_code, 303)
        self.assertIn("/data?success=", unquote(res.headers["location"]))

        conn = self._get_test_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT issue_number, title, body, state, repo_url, html_url FROM imported_issues WHERE user_id = 1")
        rows = cursor.fetchall()
        conn.close()

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], 101)
        self.assertEqual(rows[0][1], "Bug in login")
        self.assertEqual(rows[0][2], "Details about bug")
        self.assertEqual(rows[0][3], "open")
        self.assertEqual(rows[0][4], "tiangolo/fastapi")
        self.assertEqual(rows[0][5], "https://github.com/tiangolo/fastapi/issues/101")

    async def test_import_github_issues_error_handling(self):
        req = MagicMock()
        req.session = {"user_id": 1}

        # Invalid format
        res_invalid = await import_github_issues(req, repo_or_url="invalid_format_without_slash")
        self.assertEqual(res_invalid.status_code, 303)
        self.assertIn("/data?error=", unquote(res_invalid.headers["location"]))

        # HTTP error
        with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError("url", 404, "Not Found", {}, None)):
            res_http_err = await import_github_issues(req, repo_or_url="owner/repo")
            self.assertEqual(res_http_err.status_code, 303)
            self.assertIn("/data?error=", unquote(res_http_err.headers["location"]))

    async def test_convert_imported_to_task(self):
        conn = self._get_test_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (user_id, username, password) VALUES (1, 'carol', 'pass')")
        cursor.execute("""
            INSERT INTO imported_issues (import_id, user_id, issue_number, title, body, state, repo_url, html_url, imported_at)
            VALUES (55, 1, 42, 'Refactor DB', 'Need to refactor connection pool', 'open', 'owner/repo', 'https://github.com/owner/repo/issues/42', '2026-01-01 10:00:00')
        """)
        conn.commit()
        conn.close()

        req = MagicMock()
        req.session = {"user_id": 1}

        res = await convert_imported_to_task(req, import_id=55)
        self.assertEqual(res.status_code, 303)
        self.assertEqual(unquote(res.headers["location"]), "/data?success=Issue convertida em tarefa com sucesso!")

        conn = self._get_test_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT taskName, taskDescription FROM tasks WHERE user_id = 1")
        task_row = cursor.fetchone()
        self.assertIsNotNone(task_row)
        self.assertEqual(task_row[0], "Refactor DB")
        self.assertEqual(task_row[1], "Need to refactor connection pool")

        cursor.execute("SELECT state FROM imported_issues WHERE import_id = 55")
        issue_row = cursor.fetchone()
        conn.close()
        self.assertEqual(issue_row[0], "Convertida")

    async def test_delete_imported_issue(self):
        conn = self._get_test_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (user_id, username, password) VALUES (1, 'dave', 'pass')")
        cursor.execute("""
            INSERT INTO imported_issues (import_id, user_id, issue_number, title, body, state, repo_url, html_url, imported_at)
            VALUES (77, 1, 10, 'Issue to delete', 'Body', 'open', 'owner/repo', 'https://github.com/owner/repo/issues/10', '2026-01-01 10:00:00')
        """)
        conn.commit()
        conn.close()

        req = MagicMock()
        req.session = {"user_id": 1}

        res = await delete_imported_issue(req, import_id=77)
        self.assertEqual(res.status_code, 303)
        self.assertEqual(unquote(res.headers["location"]), "/data?success=Registro removido.")

        conn = self._get_test_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM imported_issues WHERE import_id = 77")
        count = cursor.fetchone()[0]
        conn.close()
        self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
