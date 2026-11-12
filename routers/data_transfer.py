import io
import json
import os
import sqlite3
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime
from fastapi import APIRouter, Form, Request, Response
from fastapi.responses import RedirectResponse

from database import get_connection

EXPORTS_DIR = "exports"

router = APIRouter()


def normalize_github_issues_url(repo_or_url: str) -> tuple[str, str]:
    if not repo_or_url or not isinstance(repo_or_url, str):
        raise ValueError("Formato de repositório ou URL inválido. Use owner/repo ou URL do GitHub.")

    cleaned = repo_or_url.strip().rstrip("/")
    if not cleaned:
        raise ValueError("Formato de repositório ou URL inválido. Use owner/repo ou URL do GitHub.")

    if cleaned.startswith("http://") or cleaned.startswith("https://"):
        parsed = urllib.parse.urlparse(cleaned)
        netloc = parsed.netloc.lower()
        path_parts = [p for p in parsed.path.strip("/").split("/") if p]

        if netloc == "github.com":
            if len(path_parts) >= 2:
                owner, repo = path_parts[0], path_parts[1]
                if repo.endswith(".git"):
                    repo = repo[:-4]
                label = f"{owner}/{repo}"
                api_url = f"https://api.github.com/repos/{label}/issues?per_page=10"
                return api_url, label
            raise ValueError("Formato de repositório ou URL inválido. Use owner/repo ou URL do GitHub.")
        elif netloc == "api.github.com":
            if len(path_parts) >= 3 and path_parts[0] == "repos":
                owner, repo = path_parts[1], path_parts[2]
                label = f"{owner}/{repo}"
                base_path = f"https://api.github.com/repos/{label}/issues"
                if parsed.query:
                    api_url = f"{base_path}?{parsed.query}"
                else:
                    api_url = f"{base_path}?per_page=10"
                return api_url, label
            raise ValueError("Formato de repositório ou URL inválido. Use owner/repo ou URL do GitHub.")
        else:
            raise ValueError("Formato de repositório ou URL inválido. Use owner/repo ou URL do GitHub.")
    else:
        parts = [p for p in cleaned.split("/") if p]
        if len(parts) == 2:
            owner, repo = parts[0], parts[1]
            if repo.endswith(".git"):
                repo = repo[:-4]
            if " " in owner or " " in repo or ":" in owner or ":" in repo:
                raise ValueError("Formato de repositório ou URL inválido. Use owner/repo ou URL do GitHub.")
            label = f"{owner}/{repo}"
            api_url = f"https://api.github.com/repos/{label}/issues?per_page=10"
            return api_url, label
        else:
            raise ValueError("Formato de repositório ou URL inválido. Use owner/repo ou URL do GitHub.")


def build_export_zip_bytes() -> bytes:
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT status_id, statusName FROM status")
        status_rows = cursor.fetchall()
        status_list = [{"status_id": r[0], "statusName": r[1]} for r in status_rows]

        cursor.execute("SELECT user_id, username FROM users")
        users_rows = cursor.fetchall()
        users_list = [{"user_id": r[0], "username": r[1]} for r in users_rows]

        cursor.execute("SELECT project_id, user_id, projectName, projectDescription, initialDate FROM projects")
        projects_rows = cursor.fetchall()
        projects_list = [
            {
                "project_id": r[0],
                "user_id": r[1],
                "projectName": r[2],
                "projectDescription": r[3],
                "initialDate": r[4],
            }
            for r in projects_rows
        ]

        cursor.execute("SELECT task_id, user_id, project_id, status_id, taskName, taskDescription, initialDate, expirationDate FROM tasks")
        tasks_rows = cursor.fetchall()
        tasks_list = [
            {
                "task_id": r[0],
                "user_id": r[1],
                "project_id": r[2],
                "status_id": r[3],
                "taskName": r[4],
                "taskDescription": r[5],
                "initialDate": r[6],
                "expirationDate": r[7],
            }
            for r in tasks_rows
        ]

        cursor.execute("SELECT note_id, task_id, user_id, content, initialDate FROM notes")
        notes_rows = cursor.fetchall()
        notes_list = [
            {
                "note_id": r[0],
                "task_id": r[1],
                "user_id": r[2],
                "content": r[3],
                "initialDate": r[4],
            }
            for r in notes_rows
        ]

        cursor.execute("SELECT import_id, user_id, issue_number, title, body, state, repo_url, html_url, imported_at FROM imported_issues")
        issues_rows = cursor.fetchall()
        issues_list = [
            {
                "import_id": r[0],
                "user_id": r[1],
                "issue_number": r[2],
                "title": r[3],
                "body": r[4],
                "state": r[5],
                "repo_url": r[6],
                "html_url": r[7],
                "imported_at": r[8],
            }
            for r in issues_rows
        ]

        data = {
            "status": status_list,
            "users": users_list,
            "projects": projects_list,
            "tasks": tasks_list,
            "notes": notes_list,
            "imported_issues": issues_list,
        }

        json_content = json.dumps(data, indent=4, ensure_ascii=False)

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("fast_task_manager_export.json", json_content.encode("utf-8"))

        return buf.getvalue()
    finally:
        if conn:
            conn.close()


@router.get("/data/export")
async def export_data(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)

    try:
        zip_bytes = build_export_zip_bytes()
        try:
            os.makedirs(EXPORTS_DIR, exist_ok=True)
            export_path = os.path.join(EXPORTS_DIR, "fast_task_manager_export.zip")
            with open(export_path, "wb") as f:
                f.write(zip_bytes)
        except OSError:
            pass

        headers = {
            "Content-Disposition": "attachment; filename=fast_task_manager_export.zip"
        }
        return Response(content=zip_bytes, media_type="application/zip", headers=headers)
    except Exception as e:
        return RedirectResponse(url=f"/data?error={urllib.parse.quote('Erro ao exportar dados: ' + str(e))}", status_code=303)


@router.post("/data/export-local")
async def export_data_local(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)

    try:
        zip_bytes = build_export_zip_bytes()
        os.makedirs(EXPORTS_DIR, exist_ok=True)
        export_path = os.path.join(EXPORTS_DIR, "fast_task_manager_export.zip")
        with open(export_path, "wb") as f:
            f.write(zip_bytes)
        return RedirectResponse(url=f"/data?success=Dados exportados com sucesso em {export_path}", status_code=303)
    except Exception as e:
        return RedirectResponse(url=f"/data?error={urllib.parse.quote('Erro ao exportar dados: ' + str(e))}", status_code=303)


@router.post("/data/import-github")
async def import_github_issues(request: Request, repo_or_url: str = Form(...)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)

    try:
        api_url, repo_label = normalize_github_issues_url(repo_or_url)

        req = urllib.request.Request(
            api_url,
            headers={
                "User-Agent": "FastTaskManager/1.0",
                "Accept": "application/vnd.github+json",
            }
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode("utf-8")

        items = json.loads(content)
        if not isinstance(items, list):
            return RedirectResponse(url="/data?error=Formato inesperado retornado pela API do GitHub.", status_code=303)

        imported_count = 0
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            for item in items:
                if "pull_request" in item:
                    continue
                issue_number = item.get("number")
                title = item.get("title", "")
                body = item.get("body") or ""
                state = item.get("state", "open")
                repo_url = repo_label
                html_url = item.get("html_url")

                cursor.execute(
                    """
                    INSERT INTO imported_issues (user_id, issue_number, title, body, state, repo_url, html_url, imported_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, issue_number, title, body, state, repo_url, html_url, now_str)
                )
                imported_count += 1
            conn.commit()
        finally:
            if conn:
                conn.close()

        return RedirectResponse(
            url=f"/data?success={imported_count} issues importadas com sucesso do repositório {repo_label}!",
            status_code=303
        )
    except ValueError as e:
        return RedirectResponse(url=f"/data?error={urllib.parse.quote(str(e))}", status_code=303)
    except urllib.error.HTTPError as e:
        return RedirectResponse(url=f"/data?error=Erro ao acessar GitHub ({e.code}): {urllib.parse.quote(str(e.reason))}", status_code=303)
    except urllib.error.URLError as e:
        return RedirectResponse(url=f"/data?error=Erro de conexão com GitHub: {urllib.parse.quote(str(e.reason))}", status_code=303)
    except (json.JSONDecodeError, sqlite3.Error, Exception) as e:
        return RedirectResponse(url=f"/data?error={urllib.parse.quote(str(e))}", status_code=303)


@router.post("/data/imported/to-task")
async def convert_imported_to_task(request: Request, import_id: int = Form(...)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT title, body, repo_url, state FROM imported_issues WHERE import_id = ? AND user_id = ?",
            (import_id, user_id)
        )
        row = cursor.fetchone()
        if not row:
            return RedirectResponse(url="/data?error=Registro não encontrado.", status_code=303)

        title, body, repo_url, state = row
        if state == "Convertida":
            return RedirectResponse(
                url=f"/data?error={urllib.parse.quote('Esta issue já foi convertida em tarefa.')}",
                status_code=303,
            )

        task_desc = body.strip() if (body and body.strip()) else f"Importada do GitHub ({repo_url})"
        initial_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            """
            INSERT INTO tasks (user_id, project_id, taskName, taskDescription, expirationDate, initialDate)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, None, title, task_desc, None, initial_date)
        )
        cursor.execute(
            "UPDATE imported_issues SET state = 'Convertida' WHERE import_id = ? AND user_id = ?",
            (import_id, user_id)
        )
        conn.commit()
        return RedirectResponse(url="/data?success=Issue convertida em tarefa com sucesso!", status_code=303)
    except sqlite3.Error as e:
        return RedirectResponse(url=f"/data?error={urllib.parse.quote('Erro ao converter issue: ' + str(e))}", status_code=303)
    finally:
        if conn:
            conn.close()


@router.post("/data/imported/delete")
async def delete_imported_issue(request: Request, import_id: int = Form(...)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM imported_issues WHERE import_id = ? AND user_id = ?",
            (import_id, user_id)
        )
        conn.commit()
        return RedirectResponse(url="/data?success=Registro removido.", status_code=303)
    except sqlite3.Error as e:
        return RedirectResponse(url=f"/data?error={urllib.parse.quote('Erro ao remover registro: ' + str(e))}", status_code=303)
    finally:
        if conn:
            conn.close()
