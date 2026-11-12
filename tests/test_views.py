import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import unquote
from starlette.requests import Request
import database
from routers import views


class TestViews(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.temp_db_fd)

        self.patcher_db = patch("database.get_connection", side_effect=self._get_test_connection)
        self.patcher_views = patch("routers.views.get_connection", side_effect=self._get_test_connection)
        self.patcher_db.start()
        self.patcher_views.start()

        database.init_db()

    def tearDown(self):
        self.patcher_views.stop()
        self.patcher_db.stop()
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def _get_test_connection(self):
        conn = sqlite3.connect(self.temp_db_path, timeout=20)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _create_request(self, path="/", session=None, query_string=""):
        scope = {
            "type": "http",
            "method": "GET",
            "path": path,
            "query_string": query_string.encode("utf-8"),
            "headers": [],
            "session": session or {},
        }
        return Request(scope)

    def test_minimum_ten_ui_templates_exist(self):
        ui_templates = [
            "sign_in.html",
            "sign_up.html",
            "dashboard.html",
            "tasks.html",
            "projects.html",
            "project_tasks.html",
            "notes.html",
            "calendar.html",
            "reports.html",
            "data_transfer.html",
            "about.html",
        ]
        for tpl in ui_templates:
            self.assertTrue(os.path.exists(os.path.join("templates", tpl)), f"Template ausente: {tpl}")
        self.assertGreaterEqual(len(ui_templates), 10)

    def test_base_html_sidebar_navigation_items(self):
        base_path = os.path.join("templates", "base.html")
        self.assertTrue(os.path.exists(base_path), "templates/base.html ausente")
        with open(base_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn('href="/reports"', content)
        self.assertIn('Relatórios', content)
        self.assertIn("{% if page == 'reports' %}active{% endif %}", content)

        self.assertIn('href="/data"', content)
        self.assertIn('Importar / Exportar', content)
        self.assertIn("{% if page == 'data' %}active{% endif %}", content)

        self.assertIn('href="/about"', content)
        self.assertIn('Sobre', content)
        self.assertIn("{% if page == 'about' %}active{% endif %}", content)

    async def test_reports_screen_unauthorized_redirects_home(self):
        req = self._create_request(path="/reports", session={})
        res = await views.reports_screen(req)
        self.assertEqual(res.status_code, 303)
        self.assertEqual(unquote(res.headers["location"]), "/?error=Acesso negado. Faça login primeiro.")

    async def test_reports_screen_authorized_renders_stats(self):
        conn = self._get_test_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (user_id, username, password) VALUES (1, 'tester', 'hash123')")
        cursor.execute("INSERT INTO users (user_id, username, password) VALUES (2, 'other', 'hash456')")
        cursor.execute("INSERT INTO projects (project_id, user_id, projectName, projectDescription, initialDate) VALUES (1, 1, 'Proj 1', 'Desc 1', '2026-01-01')")
        cursor.execute("INSERT INTO projects (project_id, user_id, projectName, projectDescription, initialDate) VALUES (2, 1, 'Proj 2', 'Desc 2', '2026-01-01')")
        # Other user's project
        cursor.execute("INSERT INTO projects (project_id, user_id, projectName, projectDescription, initialDate) VALUES (3, 2, 'Proj Other', 'Desc', '2026-01-01')")

        # Tasks for user 1: 1 in progress (0), 2 completed (1), 1 suspended (2)
        cursor.execute("INSERT INTO tasks (task_id, user_id, project_id, status_id, taskName, taskDescription, initialDate) VALUES (1, 1, 1, 0, 'Task 1', 'Desc', '2026-01-01')")
        cursor.execute("INSERT INTO tasks (task_id, user_id, project_id, status_id, taskName, taskDescription, initialDate) VALUES (2, 1, 1, 1, 'Task 2', 'Desc', '2026-01-01')")
        cursor.execute("INSERT INTO tasks (task_id, user_id, project_id, status_id, taskName, taskDescription, initialDate) VALUES (3, 1, 2, 1, 'Task 3', 'Desc', '2026-01-01')")
        cursor.execute("INSERT INTO tasks (task_id, user_id, project_id, status_id, taskName, taskDescription, initialDate) VALUES (4, 1, 2, 2, 'Task 4', 'Desc', '2026-01-01')")
        # Other user's task
        cursor.execute("INSERT INTO tasks (task_id, user_id, project_id, status_id, taskName, taskDescription, initialDate) VALUES (5, 2, 3, 0, 'Task Other', 'Desc', '2026-01-01')")

        # Notes for user 1: 3 notes
        cursor.execute("INSERT INTO notes (note_id, task_id, user_id, content, initialDate) VALUES (1, 1, 1, 'Note 1', '2026-01-01')")
        cursor.execute("INSERT INTO notes (note_id, task_id, user_id, content, initialDate) VALUES (2, 1, 1, 'Note 2', '2026-01-01')")
        cursor.execute("INSERT INTO notes (note_id, task_id, user_id, content, initialDate) VALUES (3, 2, 1, 'Note 3', '2026-01-01')")
        # Other user's note
        cursor.execute("INSERT INTO notes (note_id, task_id, user_id, content, initialDate) VALUES (4, 5, 2, 'Note Other', '2026-01-01')")

        # Imported issues for user 1: 2 issues
        cursor.execute("INSERT INTO imported_issues (import_id, user_id, issue_number, title, body, state, repo_url, html_url, imported_at) VALUES (1, 1, 101, 'Issue A', 'Body A', 'open', 'org/repo', 'https://github.com/org/repo/issues/101', '2026-01-01')")
        cursor.execute("INSERT INTO imported_issues (import_id, user_id, issue_number, title, body, state, repo_url, html_url, imported_at) VALUES (2, 1, 102, 'Issue B', 'Body B', 'closed', 'org/repo', 'https://github.com/org/repo/issues/102', '2026-01-01')")
        # Other user's imported issue
        cursor.execute("INSERT INTO imported_issues (import_id, user_id, issue_number, title, body, state, repo_url, html_url, imported_at) VALUES (3, 2, 103, 'Issue C', 'Body C', 'open', 'org/repo', 'https://github.com/org/repo/issues/103', '2026-01-01')")

        conn.commit()
        conn.close()

        req = self._create_request(path="/reports", session={"user_id": 1, "username": "tester"})
        res = await views.reports_screen(req)
        self.assertEqual(res.status_code, 200)

        # Extract rendered template response context
        context = getattr(res, "context", {})
        self.assertEqual(context.get("page"), "reports")
        self.assertEqual(context.get("page_title"), "Relatórios")
        self.assertEqual(context.get("total_tasks"), 4)
        self.assertEqual(context.get("tasks_in_progress"), 1)
        self.assertEqual(context.get("tasks_completed"), 2)
        self.assertEqual(context.get("tasks_suspended"), 1)
        self.assertEqual(context.get("total_projects"), 2)
        self.assertEqual(context.get("total_notes"), 3)
        self.assertEqual(context.get("total_imported"), 2)

    async def test_data_transfer_screen_unauthorized_redirects_home(self):
        self.assertTrue(hasattr(views, "data_transfer_screen"), "views.data_transfer_screen ausente")
        req = self._create_request(path="/data", session={})
        res = await views.data_transfer_screen(req)
        self.assertEqual(res.status_code, 303)
        self.assertEqual(unquote(res.headers["location"]), "/?error=Acesso negado. Faça login primeiro.")

    async def test_data_transfer_screen_authorized_renders_list(self):
        self.assertTrue(hasattr(views, "data_transfer_screen"), "views.data_transfer_screen ausente")
        conn = self._get_test_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (user_id, username, password) VALUES (1, 'tester', 'hash123')")
        cursor.execute("INSERT INTO imported_issues (import_id, user_id, issue_number, title, body, state, repo_url, html_url, imported_at) VALUES (1, 1, 10, 'First Issue', 'Body 1', 'open', 'org/repo', 'https://github.com/org/repo/issues/10', '2026-01-01')")
        cursor.execute("INSERT INTO imported_issues (import_id, user_id, issue_number, title, body, state, repo_url, html_url, imported_at) VALUES (2, 1, 20, 'Second Issue', 'Body 2', 'Convertida', 'org/repo', 'https://github.com/org/repo/issues/20', '2026-01-02')")
        conn.commit()
        conn.close()

        req = self._create_request(path="/data", session={"user_id": 1, "username": "tester"})
        res = await views.data_transfer_screen(req, success="Operação concluída com sucesso!")
        self.assertEqual(res.status_code, 200)

        context = getattr(res, "context", {})
        self.assertEqual(context.get("page"), "data")
        self.assertEqual(context.get("page_title"), "Importar e Exportar Dados")
        self.assertEqual(context.get("success"), "Operação concluída com sucesso!")
        imported_issues = context.get("imported_issues", [])
        self.assertEqual(len(imported_issues), 2)
        # Ordered by import_id DESC
        self.assertEqual(imported_issues[0][0], 2)
        self.assertEqual(imported_issues[1][0], 1)

    async def test_about_screen_unauthorized_redirects_home(self):
        self.assertTrue(hasattr(views, "about_screen"), "views.about_screen ausente")
        req = self._create_request(path="/about", session={})
        res = await views.about_screen(req)
        self.assertEqual(res.status_code, 303)
        self.assertEqual(unquote(res.headers["location"]), "/?error=Acesso negado. Faça login primeiro.")

    async def test_about_screen_authorized_renders_about_page(self):
        self.assertTrue(hasattr(views, "about_screen"), "views.about_screen ausente")
        req = self._create_request(path="/about", session={"user_id": 1, "username": "tester"})
        res = await views.about_screen(req)
        self.assertEqual(res.status_code, 200)

        context = getattr(res, "context", {})
        self.assertEqual(context.get("page"), "about")
        self.assertEqual(context.get("page_title"), "Sobre o Projeto")

    def test_templates_content_structure(self):
        # reports.html
        reports_path = os.path.join("templates", "reports.html")
        self.assertTrue(os.path.exists(reports_path), "templates/reports.html ausente")
        with open(reports_path, "r", encoding="utf-8") as f:
            reports_content = f.read()
        self.assertIn('{% extends "base.html" %}', reports_content)
        self.assertIn("total_tasks", reports_content)
        self.assertIn("tasks_in_progress", reports_content)
        self.assertIn("tasks_completed", reports_content)
        self.assertIn("tasks_suspended", reports_content)
        self.assertIn("total_projects", reports_content)
        self.assertIn("total_notes", reports_content)
        self.assertIn("total_imported", reports_content)

        # data_transfer.html
        dt_path = os.path.join("templates", "data_transfer.html")
        self.assertTrue(os.path.exists(dt_path), "templates/data_transfer.html ausente")
        with open(dt_path, "r", encoding="utf-8") as f:
            dt_content = f.read()
        self.assertIn('{% extends "base.html" %}', dt_content)
        self.assertIn('/data/export', dt_content)
        self.assertIn('/data/export-local', dt_content)
        self.assertIn('/data/import-github', dt_content)
        self.assertIn('name="repo_or_url"', dt_content)
        self.assertIn('/data/imported/to-task', dt_content)
        self.assertIn('/data/imported/delete', dt_content)

        # about.html
        about_path = os.path.join("templates", "about.html")
        self.assertTrue(os.path.exists(about_path), "templates/about.html ausente")
        with open(about_path, "r", encoding="utf-8") as f:
            about_content = f.read()
        self.assertIn('{% extends "base.html" %}', about_content)
        self.assertIn("Sistema de Gestão de Tarefas e Produtividade Pessoal — Fast Task Manager", about_content)
        self.assertIn("Objetivo do Projeto", about_content)
        self.assertIn("Desenvolvedores do Projeto", about_content)
        self.assertIn("Desenvolvedor 1", about_content)
        self.assertIn("Desenvolvedor 2", about_content)
        self.assertIn("Desenvolvedor 3", about_content)
        self.assertIn("Nome Completo", about_content)
        self.assertIn("Código de Matrícula", about_content)
