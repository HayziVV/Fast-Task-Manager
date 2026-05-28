from fastapi import APIRouter, Request, Form, Response
from fastapi.responses import RedirectResponse
from datetime import datetime
from database import get_connection
import sqlite3
import re

router = APIRouter()


@router.post("/tasks/notes/save")
async def save_note(
    request: Request,
    content: str = Form(""),
    task_id: int = Form(...),
):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)
    
    initialDate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT note_id FROM notes WHERE task_id = ? AND user_id = ?", (task_id, user_id))
        existing_note = cursor.fetchone()
        if existing_note:
            cursor.execute(
                "UPDATE notes SET content = ?, initialDate = ? WHERE task_id = ? AND user_id = ?",
                (content, initialDate, task_id, user_id)
            )
        else: 
            cursor.execute(
                        """INSERT INTO notes(user_id, content, task_id, initialDate) 
                           VALUES (?, ?, ?, ?) """, (user_id, content, task_id, initialDate))
        conn.commit()
        return RedirectResponse(url=f"/tasks/notes?task_id={task_id}", status_code=303)
    except sqlite3.Error:
        return RedirectResponse(url=f"/tasks/notes?task_id={task_id}&error=Erro ao criar nota.", status_code=303)
    finally:
        if conn:
            conn.close()

@router.post("/tasks/notes/remove")
async def remove_note(
    request: Request,
    task_id: int = Form(...),
):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""DELETE FROM notes WHERE task_id = ? AND user_id = ?""", 
                    (task_id, user_id))
        conn.commit()
        return RedirectResponse(url=f"/tasks?task_id={task_id}", status_code=303)
    except sqlite3.Error:
        return RedirectResponse(url=f"/tasks?task_id={task_id}&error=Erro ao remover nota.", status_code=303)
    finally:
        if conn:
            conn.close()

@router.get("/tasks/notes/download/txt")
async def download_note_txt(request: Request, task_id: int):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)
    
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM notes WHERE task_id = ? AND user_id = ?", (task_id, user_id))
        note = cursor.fetchone()
        
        content_html = note[0] if note else ""
        
        content_html = content_html.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
        content_html = content_html.replace("<div>", "").replace("</div>", "\n")
        content_html = content_html.replace("<p>", "").replace("</p>", "\n")
        
   
        clean_text = re.sub(r'<[^>]+>', '', content_html)
        
        headers = {
            "Content-Disposition": f"attachment; filename=nota_tarefa_{task_id}.txt"
        }
        return Response(content=clean_text, media_type="text/plain", headers=headers)
        
    except sqlite3.Error:
        return RedirectResponse(url=f"/tasks/notes?task_id={task_id}&error=Erro ao baixar arquivo.", status_code=303)
    finally:
        if conn:
            conn.close()