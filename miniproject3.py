import os
import sqlite3
import bcrypt
import base64

from fastapi import (
	FastAPI, Query, HTTPException, UploadFile, Form, 
    File, WebSocket, WebSocketDisconnect, status, Depends
)
from fastapi.responses import HTMLResponse
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
)
from pydantic import EmailStr, BaseModel, field_validator, Field , SecretStr
from typing import List, Optional
from datetime import datetime


app = FastAPI()
DB_NAME = "ads.db"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>WebSocket Chat</title>
</head>
<body>
    <h1>WebSocket Chat</h1>
    <h1><a href='https://bytecraft.com.ua'>Bytecraft</a></h1>
    <label>Room: <input id="roomInput" value="main" /></label>
    <button onclick="connect()">Connect</button>

    <form onsubmit="sendMessage(event)">
        <input type="text" id="messageText" autocomplete="off" />
        <button>Send</button>
    </form>

    <ul id="messages"></ul>

    <img src="https://res2.weblium.site/res/683deb0bde7b8dfb78b055e5/6873aab3ccd53279455bfb44_optimized_953_c953x953-0x0.webp" alt="Фото" width="200"/>
    <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQiHPN_CyosGu2C0kDyVFwyrQoFuQBiFMn9gQ&s" alt="Фото" width="200"/>

<script>
    let ws = null;
    let connected = false;

    function connect() {
        if (connected) {
            appendSystem("Уже подключён.");
            return;
        }

        const room = document.getElementById("roomInput").value;
        ws = new WebSocket(`ws://127.0.0.1:8000/ws/${room}`);

        ws.onopen = () => {
            connected = true;
            appendSystem("Connected to " + room);
        };

        ws.onmessage = (e) => appendMessage(e.data);

        ws.onclose = () => {
            connected = false;
            appendSystem("Disconnected");
        };
    }

    function sendMessage(e) {
        e.preventDefault();
        const input = document.getElementById("messageText");
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(input.value);
            input.value = '';
        }
    }

    function appendMessage(text) {
        const li = document.createElement('li');
        li.textContent = text;
        document.getElementById("messages").appendChild(li);
    }

    function appendSystem(text) {
        const li = document.createElement('li');
        li.style.color = "gray";
        li.textContent = text;
        document.getElementById("messages").appendChild(li);
    }
</script>
</body>
</html>
"""

class Token(BaseModel):
    """Модель токена доступу."""

    token_type: str = Field(description="type of the token", examples=["bearer"])
    access_token: str = Field(description="Token Value", examples=["YmasdeQ=="])

class User(BaseModel):
    name: str
    email: EmailStr
    password: SecretStr

class UserShow(User):
    id: int

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Name of user can't be none")
        return v

    @field_validator("email")
    @classmethod
    def email_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Email of user can't be none")
        if not (v.endswith("@gmail.com") or v.endswith("@example.com")):
            raise ValueError("Email might be in domen @gmail.com")
        return v

    @field_validator("password")
    @classmethod
    def password_not_empty(cls, v):
        if not v.get_secret_value().strip():
            raise ValueError("Password of user can't be none")
        if len(v) < 8:
            raise ValueError("Password should be at least 8 characters long")
        return v

class Ad(BaseModel):
    id: int
    title: str
    description: str
    price: float
    category: str

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL,
            category TEXT NOT NULL,
            image_path TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()


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
async def get_chat():
    return HTMLResponse(html)

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

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


async def decode_token(token: str):

    try:
        decoded_user_email = (
            base64.urlsafe_b64decode(token).split(b"-")[0].decode("utf-8")
        )
    except (UnicodeDecodeError, ValueError):
        return None

    return decoded_user_email

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def init_db():
    with sqlite3.connect(DB_NAME) as connection:
        cursor: sqlite3.Cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                name      VARCHAR(30) NOT NULL,
                email     VARCHAR(32) UNIQUE NOT NULL,
                password      VARCHAR(30) NOT NULL
            )
        """)
        connection.commit()

init_db()

@app.post(
    "/register/",
    status_code=status.HTTP_201_CREATED,
    summary="Реєстрація користувача",
    description="Реєстрація нового користувача з хешуванням паролю.",
    tags=["Аутентифікація"],
    responses={
        201: {"description": "Користувача успішно зареєстровано"},
        400: {"description": "Email вже зареєстрований або некоректні дані"},
    }
)
async def register_user(user: User):
    with sqlite3.connect(DB_NAME) as connection:
        cursor: sqlite3.Cursor = connection.cursor()
        cursor.execute(
            "SELECT 1 FROM users WHERE email = ?",
            (user.email,),
        )
        if cursor.fetchone() is not None:
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed_password = hash_password(user.password.get_secret_value())

        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (user.name, user.email, hashed_password),
        )
        connection.commit()

    return {"message": f"User {user.name} registered successfully"}

async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    with sqlite3.connect(DB_NAME) as connection:
        connection.row_factory = sqlite3.Row
        cursor: sqlite3.Cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE email = ?", (form_data.username,)
        )

        db_user = cursor.fetchone()

        if db_user is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User does not exist.")

    user = UserShow(**dict(db_user))

    if not verify_password(form_data.password, user.password.get_secret_value()):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Incorrect password.")

    return Token(
        access_token=base64.urlsafe_b64encode(
            f"{user.email}-{user.name}".encode("utf-8")
        ).decode("utf-8"),
        token_type="bearer",
    )

@app.post(
    "/token",
    response_model=Token,
    summary="Отримання токену доступу",
    description="Отримання JWT токену за email та паролем (логін).",
    tags=["Аутентифікація"],
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Токен отримано успішно"},
        400: {"description": "Неправильний пароль"},
        404: {"description": "Користувача не знайдено"},
    }
)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    return await login(form_data)

@app.get(
    "/test/",
    summary="Тестовий ендпоінт",
    description="Тестовий ендпоінт, який вимагає передачі токена авторизації.",
    tags=["Тести"],
    status_code=status.HTTP_200_OK,
)
async def test(token: str = Depends(oauth2_scheme)):
    return "hello"