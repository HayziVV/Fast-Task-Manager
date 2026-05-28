import sqlite3

def get_connection():
    conn = sqlite3.connect("database.db", timeout=20)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS status (
                status_id INTEGER PRIMARY KEY,
                statusName TEXT NOT NULL UNIQUE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                project_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                projectName TEXT NOT NULL,
                projectDescription TEXT NOT NULL,
                initialDate TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE RESTRICT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                project_id INTEGER,
                status_id INTEGER DEFAULT 0, 
                taskName TEXT NOT NULL,
                taskDescription TEXT NOT NULL,
                initialDate TEXT NOT NULL,
                expirationDate TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE RESTRICT,
                FOREIGN KEY (project_id) REFERENCES projects (project_id) ON DELETE RESTRICT,
                FOREIGN KEY (status_id) REFERENCES status (status_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes(
                note_id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                initialDate TEXT NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks (task_id) ON DELETE RESTRICT
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE RESTRICT
            )
         """)
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM status")
        if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO status (status_id, statusName) VALUES (0, 'Em Progresso')")
                cursor.execute("INSERT INTO status (status_id, statusName) VALUES (1, 'Concluído')")
                cursor.execute("INSERT INTO status (status_id, statusName) VALUES (2, 'Suspenso')")
                conn.commit()

    except sqlite3.Error as e:
        print(f"Erro ao inicializar o banco: {e}")
    finally:
        if conn:
            conn.close()
