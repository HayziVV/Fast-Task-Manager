import calendar
from datetime import date, datetime
from fastapi import APIRouter, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from database import get_connection
import math
import sqlite3


router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/")
async def sign_in_screen(request: Request, error: str = None):
    return templates.TemplateResponse(request=request, name="sign_in.html", context={"request": request, "error": error})


@router.get("/sign_up")
async def sign_up_screen(request: Request):
    return templates.TemplateResponse(request=request, name="sign_up.html", )

@router.get("/dashboard")
async def dashboard_screen(request: Request, page: int = 1, error: str = None):
    user_id = request.session.get("user_id")
    username = request.session.get("username")
    
    if not user_id:
        return RedirectResponse(url="/?error=Acesso negado. Faça login primeiro.", status_code=303)
    
    conn = None
    try:
        limit = 10
        offset = (page - 1) * limit
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ?", (user_id,))
        total_tasks = cursor.fetchone()[0]
        total_pages = math.ceil(total_tasks / limit) or 1
        
        cursor.execute("""
            SELECT t.task_id, t.taskName, t.taskDescription, t.expirationDate, p.projectName 
            FROM tasks t
            LEFT JOIN projects p ON t.project_id = p.project_id
            WHERE t.user_id = ?
            ORDER BY CASE WHEN t.expirationDate IS NULL OR t.expirationDate = '' THEN 1 ELSE 0 END, t.expirationDate ASC
            LIMIT ? OFFSET ?
        """, (user_id, limit, offset))
        user_tasks = cursor.fetchall()
        
        cursor.execute("""
            SELECT project_id, projectName, projectDescription, initialDate
            FROM projects 
            WHERE user_id = ?
            ORDER BY project_id DESC
        """, (user_id,))
        user_projects = cursor.fetchall()
        
        context = {
            "request": request,
            "page_title": "Dashboard",
            "page": "dashboard",
            "user_id": user_id,
            "username": username,
            "tasks": user_tasks,
            "projects": user_projects,
            "current_page": page,
            "total_pages": total_pages,
            "error": error
        }
        return templates.TemplateResponse(request = request, name="dashboard.html", context=context)
        
    except sqlite3.Error as e:
        return templates.TemplateResponse(
            request=request, 
            name="dashboard.html", 
            context={
                "request": request,
                "tasks": [],
                "projects": [],
                "error": f"Erro ao processar o painel de consulta rápida: {str(e)}"
            }
        )
    finally:
        if conn:
            conn.close()

@router.get("/tasks")
async def tasks_screen(request: Request, page: int = 1, status_id: str = None, error: str = None):

    user_id = request.session.get("user_id")
    username = request.session.get("username")
    if not user_id:
        return RedirectResponse(url="/?error=Acesso negado. Faça login primeiro.", status_code=303)
    
    conn = None
    try:
        limit = 12
        offset = (page - 1) * limit
        conn = get_connection()
        cursor = conn.cursor()
        count_query = "SELECT COUNT(*) FROM tasks WHERE user_id = ?"
        tasks_query = """
            SELECT task_id, taskName, taskDescription, initialDate, expirationDate, status_id
            FROM tasks 
            WHERE user_id = ?
        """
        count_params = [user_id]
        tasks_params = [user_id] 

        if status_id is not None and status_id != "all" and str(status_id).isdigit():
            status_id_int = int(status_id)
            count_query += " AND status_id = ?"
            tasks_query += " AND status_id = ?"
            count_params.append(status_id_int)
            tasks_params.append(status_id_int)

        cursor.execute(count_query, count_params)
        total_tasks = cursor.fetchone()[0]
        total_pages = math.ceil(total_tasks / limit) or 1
        tasks_query += " ORDER BY initialDate DESC LIMIT ? OFFSET ?"
        tasks_params.extend([limit, offset])
        cursor.execute(tasks_query, tasks_params)
        user_tasks = cursor.fetchall()
        cursor.execute(
                    """SELECT project_id, projectName 
                       FROM projects WHERE user_id = ?""", (user_id,))
        user_projects = cursor.fetchall()
        cursor.execute("SELECT status_id, statusName FROM status ORDER BY status_id ASC")
        all_statuses = cursor.fetchall()
        context = {
            "request": request,
            "page_title": "Tarefas",
            "page": "tasks",
            "user_id": user_id,
            "tasks": user_tasks,
            "projects": user_projects,
            "statuses": all_statuses,       
            "current_status_id": status_id,
            "current_page": page,
            "total_pages": total_pages,
            "username": username,
            "error": error
        }
        return templates.TemplateResponse(request=request, name="tasks.html", context=context)
    except sqlite3.Error:
        return RedirectResponse(url="/dashboard?error=Erro ao carregar tarefas.", status_code=303)
    finally:
        if conn:
            conn.close()

@router.get("/reports")
async def reports_screen(request: Request):

    user_id = request.session.get("user_id")
    username = request.session.get("username")
    if not user_id:
        return RedirectResponse(url="/?error=Acesso negado. Faça login primeiro.", status_code=303)
    
    context = {
        "request": request,
        "page_title": "Relatorios",
        "page": "reports",
        "username": username,
        "user_id": user_id
    }
    return templates.TemplateResponse(request=request, name="reports.html", context=context)

@router.get("/calendar")
async def calendar_screen(request: Request, year: int = None, month: int = None):
    user_id = request.session.get("user_id")
    username = request.session.get("username")
    
    if not user_id:
        return RedirectResponse(url="/?error=Acesso negado. Faça login primeiro.", status_code=303)
    
    now = datetime.now()
    current_year = year if year else now.year
    current_month = month if month else now.month
    
    if current_month == 1:
        prev_month = 12
        prev_year = current_year - 1
    else:
        prev_month = current_month - 1
        prev_year = current_year
        
    if current_month == 12:
        next_month = 1
        next_year = current_year + 1
    else:
        next_month = current_month + 1
        next_year = current_year

    months_pt = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
        7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    month_name = months_pt[current_month]


    cal = calendar.Calendar(firstweekday=6)
    weeks = cal.monthdatescalendar(current_year, current_month)

    conn = None
    tasks_by_date = {}
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT task_id, taskName, expirationDate, status_id
            FROM tasks
            WHERE user_id = ? AND expirationDate IS NOT NULL AND expirationDate != ''
        """, (user_id,))
        db_tasks = cursor.fetchall()
        
        for t in db_tasks:
            date_key = t[2]
            if date_key not in tasks_by_date:
                tasks_by_date[date_key] = []
            tasks_by_date[date_key].append({
                "id": t[0],
                "name": t[1],
                "status_id": t[3]
            })
            
    except sqlite3.Error as e:
        print(f"Erro ao processar calendário: {e}")
    finally:
        if conn:
            conn.close()

    context = {
        "request": request,
        "page_title": "Calendário de Prazos",
        "page": "calendar",
        "username": username,
        "year": current_year,
        "month": current_month,
        "month_name": month_name,
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
        "weeks": weeks,
        "tasks_by_date": tasks_by_date,
        "today_str": date.today().isoformat()
    }
    return templates.TemplateResponse(request=request,name="calendar.html", context=context)

@router.get("/projects")
async def projects_screen(request: Request, error: str = None):

    user_id = request.session.get("user_id")
    username = request.session.get("username")
    if not user_id:
        return RedirectResponse(url="/?error=Acesso negado. Faça login primeiro.", status_code=303)
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT project_id, projectName, projectDescription, initialDate 
               FROM projects 
               WHERE user_id = ? 
               ORDER BY initialDate DESC""", (user_id,))
        user_projects = cursor.fetchall()

        context = {
            "request": request,
            "page_title": "Projetos",
            "page": "projects",
            "user_id": user_id,
            "projects": user_projects,
            "username": username,
            "error": error
        }
        return templates.TemplateResponse(request=request, name="projects.html", context=context)
    except sqlite3.Error:
        return RedirectResponse(url="/dashboard?error=Erro ao carregar projetos.", status_code=303)
    finally:
        if conn:
            conn.close()

@router.get("/tasks/notes")
async def notes_screen(request: Request, task_id: int = Query(...), error: str = None):
    user_id = request.session.get("user_id")
    username = request.session.get("username")
    if not user_id:
        return RedirectResponse(url="/?error=Acesso negado. Faça login primeiro.", status_code=303)
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM notes WHERE user_id = ? AND task_id = ?", (user_id, task_id))
        user_notes = cursor.fetchone()

        note_content = user_notes[0] if user_notes else ""

        context = {
            "request": request,
            "page_title": "Notas",
            "page": "notes",
            "user_id": user_id,
            "task_id": task_id,
            "notes": user_notes,
            "note_content": note_content,
            "username": username,
            "error": error
        }
        return templates.TemplateResponse(request=request, name="notes.html", context=context)
    except sqlite3.Error:
        return RedirectResponse(url="/tasks?error=Erro ao carregar notas.", status_code=303)
    finally:
        if conn:
            conn.close()

@router.get('/projects/tasks')
async def project_tasks_screen(request: Request, project_id: int = Query(...), error: str = None):
    user_id = request.session.get("user_id")
    username = request.session.get("username")

    if not user_id:
        return RedirectResponse(url="/?error=Acesso negado. Faça login primeiro.", status_code=303)
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
                        SELECT task_id, taskName, taskDescription, status_id, initialDate, expirationDate
                        FROM tasks 
                        WHERE project_id = ? AND user_id = ?""", 
                        (project_id, user_id))
        project_tasks = cursor.fetchall()

        cursor.execute("""
                    SELECT projectName
                    FROM projects
                    WHERE project_id = ? AND user_id = ?""",
                    (project_id, user_id))
        project_name = cursor.fetchone()
        name_project = project_name[0]

        context = {
            "request": request,
            "page_title": f"Tarefas do projeto {name_project}",
            "page": "projects/tasks",
            "user_id": user_id,
            "project_id": project_id,
            "project_tasks": project_tasks,
            "tasks": project_tasks,
            "username": username,
            "error": error
        }
        return templates.TemplateResponse(request=request, name="project_tasks.html", context=context)
    except sqlite3.Error:
        return RedirectResponse(url="/projects?error=Erro ao carregar as tarefas do projeto.", status_code=303)
    finally:
        if conn:
            conn.close()
