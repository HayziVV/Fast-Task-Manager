from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from database import init_db
from routers import auth, projects, tasks, views, notes
import uvicorn
import os

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise ValueError("ERRO: A variável de ambiente SECRET_KEY não foi definida no arquivo .env!")

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.mount("/static", StaticFiles(directory="static"), name="static")

init_db()

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(views.router)
app.include_router(notes.router)


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)