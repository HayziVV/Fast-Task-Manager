from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from database import get_connection
import sqlite3


router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.post("/signup")
async def sign_up(
    request: Request, 
    username: str = Form(...),
    password: str = Form(...), 
    confirm_password: str = Form(...)
):
    if password != confirm_password:
        return templates.TemplateResponse(request=request, name="sign_up.html", context={"request": request, "error": "As senhas não coincidem."})

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return RedirectResponse(url="/", status_code=303)
    except sqlite3.IntegrityError:
        return templates.TemplateResponse(request=request, name="sign_up.html", context={"request": request, "error": "Usuário já existe."})
    finally:
        if conn:
            conn.close()

@router.post("/signin", response_class=HTMLResponse)
async def sign_in(
    request: Request, 
    username: str = Form(...), 
    password: str = Form(...)
):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()

        if user:
            request.session["username"] = username
            request.session["user_id"] = int(user[0])
            return RedirectResponse(url="/dashboard", status_code=303)
        else:
            return templates.TemplateResponse(request=request, name="sign_in.html", context={"request": request, "error": "Usuário ou senha incorretos."})
    except sqlite3.Error:
        return templates.TemplateResponse(request=request, name="sign_in.html", context={"request": request, "error": "Erro ao realizar sign-in."})
    finally:
        if conn:
            conn.close()
    

@router.get("/signout")
async def sign_out(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)