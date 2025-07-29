import os
import sqlite3

from fastapi import (
	FastAPI, Query, HTTPException, UploadFile, Form, 
    File, WebSocket, WebSocketDisconnect, status, Depends, Request
)
from fastapi.responses import HTMLResponse
from fastapi.security import (
    OAuth2PasswordBearer,
)
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from miniproject3.auth import router as auth_router


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

app = FastAPI(on_startup=[init_db])
app.include_router(auth_router)
DB_NAME = "ads.db"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
templates = Jinja2Templates(directory="miniproject3/templates")


class Ad(BaseModel):
    id: int
    title: str
    description: str
    price: float
    category: str

def ad_row_to_dict(row) -> dict:
    return {
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "price": row[3],
        "category": row[4],
    }

@app.get(
    "/filters/",
    response_model=List[Ad],
    summary="Список оголошень з фільтрами",
    description=(
        "Повертає список оголошень з можливістю фільтрації за категорією, "
        "мінімальною та максимальною ціною з підтримкою пагінації."
    ),
    tags=["Оголошення"],
    responses={
        200: {"description": "Успішне повернення списку оголошень"},
        400: {"description": "Невірні параметри запиту"},
    }
)
def list_ads(
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0)
):
	conditions = []
	params = []

	if category:
		conditions.append("category = ?")
		params.append(category)
	if min_price is not None:
		conditions.append("price >= ?")
		params.append(min_price)
	if max_price is not None:
		conditions.append("price <= ?")
		params.append(max_price)

	query = "SELECT * FROM ads"
	if conditions:
		query += " WHERE " + " AND ".join(conditions)

	query += " LIMIT ? OFFSET ?"
	params.extend([limit, offset])
	
	conn = sqlite3.connect(DB_NAME)
	cursor = conn.cursor()
	cursor.execute(query, params)
	rows = cursor.fetchall()
	conn.close()
		
	return [ad_row_to_dict(row) for row in rows]

@app.post(
    "/create/",
    summary="Створення оголошення",
    description="Створює нове оголошення з завантаженням зображення. Потрібна аутентифікація через токен.",
    tags=["Оголошення"],
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Оголошення успішно створено"},
        400: {"description": "Некоректне зображення або дані"},
        401: {"description": "Неавторизований доступ"},
    }
)
async def create_ad(
    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    category: str = Form(...),
    image: UploadFile = File(...),
    token: str = Depends(oauth2_scheme)
):
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Файл має бути зображенням")

    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    filename = f"{timestamp}_{image.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        content = await image.read()
        buffer.write(content)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO ads (title, description, price, category, image_path) VALUES (?, ?, ?, ?, ?)",
        (title, description, price, category, file_path)
    )
    conn.commit()
    ad_id = cursor.lastrowid
    conn.close()

    return {
        "id": ad_id,
        "title": title,
        "description": description,
        "price": price,
        "category": category,
        "image_path": file_path,
    }

@app.get(
    "/chat/",
    summary="Сторінка WebSocket чату",
    description="Повертає HTML-сторінку з WebSocket чатом.",
    tags=["Чат"],
    status_code=status.HTTP_200_OK,
)
async def get_chat(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

def ensure_room_exists(room_name: str):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM rooms WHERE name = ?", (room_name,))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO rooms (name) VALUES (?)", (room_name,))
            conn.commit()

connections = {}

@app.websocket(
    "/ws/{room}"
)
async def websocket_endpoint(websocket: WebSocket, room: str):
    await websocket.accept()

    ensure_room_exists(room)

    if room not in connections:
        connections[room] = []

    connections[room].append(websocket)

    try:
        while True:
            data = await websocket.receive_text()

            for client in connections[room]:
                await client.send_text(data)

    except WebSocketDisconnect:
        connections[room].remove(websocket)
        if not connections[room]:
            del connections[room]