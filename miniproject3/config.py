import os
import sqlite3

from fastapi import FastAPI
from fastapi.security import OAuth2PasswordBearer


DB_NAME = "ads.db"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app = FastAPI(on_startup=["init_db"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL,
            category TEXT NOT NULL,
            image_path TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(30) NOT NULL,
            email VARCHAR(32) UNIQUE NOT NULL,
            password VARCHAR(30) NOT NULL
        );
    """)
    conn.commit()
    conn.close()