from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from datetime import date
import sqlite3

router = APIRouter()


@router.post("/projects/add")
async def add_project(
    request: Request,
    projectName: str = Form(...),
    projectDescription: str = Form(...),
):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)
    
    initialDate = date.today().isoformat()
    conn = None
    try:
        conn = sqlite3.connect("database.db", timeout=20)
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO projects(user_id, projectName, projectDescription, initialDate) VALUES (?, ?, ?, ?) """, 
                    (user_id, projectName, projectDescription, initialDate))
        conn.commit()
        return RedirectResponse(url="/projects", status_code=303)
    except sqlite3.Error:
        return RedirectResponse(url="/projects?error=Erro ao criar projeto.", status_code=303)
    finally:
        if conn:
            conn.close()

@router.post("/projects/remove")
async def remove_project(
    request: Request,
    project_id: int = Form(...),
):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)
    conn = None
    try:
        conn = sqlite3.connect("database.db", timeout=20)
        cursor = conn.cursor()
        cursor.execute("""DELETE FROM projects WHERE project_id = ? AND user_id = ?""", 
                    (project_id, user_id))
        conn.commit()
        return RedirectResponse(url="/projects", status_code=303)
    except sqlite3.Error:
        return RedirectResponse(url="/projects?error=Erro ao remover projeto.", status_code=303)
    finally:
        if conn:
            conn.close()
