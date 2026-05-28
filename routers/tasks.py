from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from datetime import datetime
from database import get_connection
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
    page_to_go_back = request.headers.get("referer")
    url_to_go = page_to_go_back if page_to_go_back else "/tasks"
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)
    
    initialDate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO tasks(user_id, project_id,taskName, taskDescription, expirationDate, initialDate) VALUES (?, ?, ?, ?, ?, ?) """, 
                    (user_id, project_id ,taskName, taskDescription, expirationDate, initialDate))
        conn.commit()
        return RedirectResponse(url=url_to_go, status_code=303)
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
    page_to_go_back = request.headers.get("referer")
    url_to_go = page_to_go_back if page_to_go_back else "/tasks"
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""DELETE FROM tasks WHERE task_id = ? AND user_id = ?""", 
                    (task_id, user_id))
        conn.commit()
        return RedirectResponse(url=url_to_go, status_code=303)
    except sqlite3.IntegrityError:
        return RedirectResponse(
            url="/tasks?error=Não é possível excluir esta tarefa. Remova as notas vinculadas a ela primeiro.", 
            status_code=303
        )
    except sqlite3.Error:
        return RedirectResponse(url="/tasks?error=Erro ao remover tarefa.", status_code=303)
    finally:
        if conn:
            conn.close()

@router.post("/tasks/update-status")
async def update_task_status(
    request: Request,
    task_id: int = Form(...),
    taskName: str = Form(...),
    status_id: int = Form(...)
):
    page_to_go_back = request.headers.get("referer")
    url_to_go = page_to_go_back if page_to_go_back else "/tasks"
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)
    
    conn = None
    try:
    
        conn = get_connection()
        cursor = conn.cursor()
  
        cursor.execute(
            """UPDATE tasks 
               SET status_id = ?, taskName = ? 
               WHERE task_id = ? AND user_id = ?""",
            (status_id, taskName, task_id, user_id)
        )
        conn.commit()
        
        
        return RedirectResponse(url=url_to_go, status_code=303)
        
    except sqlite3.Error:
        return RedirectResponse(url="/tasks?error=Erro ao atualizar o estado da tarefa.", status_code=303)
    finally:
        if conn:
            conn.close()