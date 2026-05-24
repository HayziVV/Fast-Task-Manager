from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

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
async def dashboard_screen(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?error=Acesso negado. Faça login primeiro.", status_code=303)
    
    context = {
        "request": request,
        "page_title": "Dashboard",
        "page": "dashboard",
        "user_id": user_id
    }
    return templates.TemplateResponse(request=request, name="dashboard.html", context=context)

@router.get("/tasks")
async def tasks_screen(request: Request, page: int = 1 , error: str = None):

    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?error=Acesso negado. Faça login primeiro.", status_code=303)
    
    conn = None
    try:
        limit = 10
        offset = (page - 1) * limit

        conn = sqlite3.connect("database.db", timeout=20)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ?", (user_id,))
        total_tasks = cursor.fetchone()[0]
        total_pages = math.ceil(total_tasks / limit) or 1

        cursor.execute("SELECT task_id, taskName, taskDescription, initialDate, expirationDate FROM tasks WHERE user_id = ? LIMIT ? OFFSET ?", (user_id, limit, offset))
        user_tasks = cursor.fetchall()

        cursor.execute("SELECT project_id, projectName FROM projects WHERE user_id = ?", (user_id,))
        user_projects = cursor.fetchall()

        context = {
            "request": request,
            "page_title": "Tarefas",
            "page": "tasks",
            "user_id": user_id,
            "tasks": user_tasks,
            "projects": user_projects,
            "current_page": page,
            "total_pages": total_pages,
            "error": error
        }
        return templates.TemplateResponse(request=request, name="tasks.html", context=context)
    except sqlite3.Error:
        return templates.TemplateResponse(request=request, name="dashboard.html", context={"request": request, "error": "Erro ao carregar tarefas."})
    finally:
        if conn:
            conn.close()

@router.get("/reports")
async def reports_screen(request: Request):

    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?error=Acesso negado. Faça login primeiro.", status_code=303)
    
    context = {
        "request": request,
        "page_title": "Relatorios",
        "page": "reports",
        "user_id": user_id
    }
    return templates.TemplateResponse(request=request, name="reports.html", context=context)

@router.get("/team")
async def team_screen(request: Request):

    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?error=Acesso negado. Faça login primeiro.", status_code=303)
    
    context = {
        "request": request,
        "page_title": "Equipe", 
        "page": "team",
        "user_id": user_id
    }
    return templates.TemplateResponse(request=request, name="team.html", context=context)

@router.get("/calendar")
async def calendar_screen(request: Request):

    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?error=Acesso negado. Faça login primeiro.", status_code=303)
    
    context = {
        "request": request,
        "page_title": "Calendario",
        "page": "calendar",
        "user_id": user_id
    }
    return templates.TemplateResponse(request=request, name="calendar.html", context=context)

@router.get("/projects")
async def projects_screen(request: Request):

    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?error=Acesso negado. Faça login primeiro.", status_code=303)
    conn = None
    try:
        conn = sqlite3.connect("database.db", timeout=20)
        cursor = conn.cursor()
        cursor.execute("SELECT project_id, projectName, projectDescription, initialDate FROM projects WHERE user_id = ?", (user_id,))
        user_projects = cursor.fetchall()

        context = {
            "request": request,
            "page_title": "Projetos",
            "page": "projects",
            "user_id": user_id,
            "projects": user_projects
        }
        return templates.TemplateResponse(request=request, name="projects.html", context=context)
    except sqlite3.Error:
        return templates.TemplateResponse(request=request, name="dashboard.html", context={"request": request, "error": "Erro ao carregar projetos."})
    finally:
        if conn:
            conn.close()
