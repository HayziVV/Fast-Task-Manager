import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import uvicorn

from database import init_db
from routers import auth, data_transfer, notes, projects, tasks, views

os.chdir(os.path.dirname(os.path.abspath(__file__)))
SESSION_KEY = "Fast_task_manager_development_test_key"

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=SESSION_KEY)
app.mount("/static", StaticFiles(directory="static"), name="static")

init_db()

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(views.router)
app.include_router(notes.router)
app.include_router(data_transfer.router)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.ico")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
