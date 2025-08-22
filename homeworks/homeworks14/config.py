import sqlite3

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );
    """)
    conn.commit()
    conn.close()

app = FastAPI(on_startup=[init_db])
templates = Jinja2Templates(directory="homeworks/homeworks14/templates")
DB_NAME = "chat.db"

SECRET_KEY = "q"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30