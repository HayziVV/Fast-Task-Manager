from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from datetime import date
import sqlite3


router = APIRouter()

@router.post("/tasks/add")
async def add_task(
    request: Request,
    taskName: str = Form(...),
    taskDescription: str = Form(...),
    expirationDate: str = Form(None),
    project_id: str = Form(None)
):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)
    
    initialDate = date.today().isoformat()
    if not expirationDate:
        expirationDate = None
    
    try:
        if project_id and project_id != "":
            project_id = int(project_id)
        else:
            project_id = None
    except ValueError:
        return RedirectResponse(url="/tasks?error=Erro ao adicionar tarefa, projeto invalido.", status_code=303)

    conn = None
    try:
        conn = sqlite3.connect("database.db", timeout=20)
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO tasks(user_id, project_id,taskName, taskDescription, expirationDate, initialDate) VALUES (?, ?, ?, ?, ?, ?) """, 
                    (user_id, project_id ,taskName, taskDescription, expirationDate, initialDate))
        conn.commit()
        return RedirectResponse(url="/tasks", status_code=303)
    except sqlite3.Error:
        return RedirectResponse(url="/tasks?error=Erro ao adicionar tarefa.", status_code=303)
    finally:
        if conn:
            conn.close()

@router.post("/tasks/remove")
async def remove_task(
    request: Request,
    task_id: int = Form(...),
):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)
    conn = None
    try:
        conn = sqlite3.connect("database.db", timeout=20)
        cursor = conn.cursor()
        cursor.execute("""DELETE FROM tasks WHERE task_id = ? AND user_id = ?""", 
                    (task_id, user_id))
        conn.commit()
        return RedirectResponse(url="/tasks", status_code=303)
    except sqlite3.Error:
        return RedirectResponse(url="/tasks?error=Erro ao remover tarefa.", status_code=303)
    finally:
        if conn:
            conn.close()

    
