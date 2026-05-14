from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import sqlite3
import uvicorn

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.get("/")
async def sign_in_screen(request: Request):
    return templates.TemplateResponse(request=request, name="sign_in.html")


@app.get("/sign_up")
async def sign_up_screen(request: Request):
    return templates.TemplateResponse(request=request, name="sign_up.html")

@app.get("/dashboard")
async def sign_up_screen(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html")

@app.post("/signup")
async def sign_up(request: Request, username: str = Form(...), password: str = Form(...), confirm_password: str = Form(...)):
    if password != confirm_password:
        return "Erro, as senhas não coincidem."
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return RedirectResponse(url="/", status_code=303)
    except sqlite3.IntegrityError:
        return templates.TemplateResponse(
            request=request, 
            name="sign_up.html", 
            context={
                "error": "Usuário já existe.",
            }
        )

@app.post("/signin", response_class=HTMLResponse)
async def sign_in(request: Request, username: str = Form(...), password: str = Form(...)):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close

    if user:
        return RedirectResponse(url="/dashboard", status_code=303)
    else:
       return templates.TemplateResponse(
            request=request, 
            name="sign_in.html", 
            context={
                "error": "Usuário ou senha incorretos.",
            }
        )

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)