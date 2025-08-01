import sqlite3

from fastapi import WebSocket, WebSocketDisconnect, Request, status
from .config import app, templates, DB_NAME


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