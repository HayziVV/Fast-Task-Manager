from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from database import init_db
from routers import auth, projects, tasks, views, notes
from fastapi.responses import FileResponse
import uvicorn
import threading
import webview
import time


SECRET_KEY = "Fast_task_manager_development_test_key" # Key made for testing.

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.mount("/static", StaticFiles(directory="static"), name="static")


init_db()

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(views.router)
app.include_router(notes.router)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.ico")

def start_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

if __name__ == "__main__":
    t = threading.Thread(target=start_server)
    t.daemon = True
    t.start()
    
    time.sleep(1)

    webview.create_window(
        title="Fast Task Manager", 
        url="http://127.0.0.1:8000",
        width=1200, 
        height=800,
        min_size=(800, 600),
       
    )
    webview.start(icon="static/favicon.ico")