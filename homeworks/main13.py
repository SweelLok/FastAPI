import html
import jwt
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status, HTTPException
from fastapi.responses import HTMLResponse
from typing import List, Tuple

SECRET_KEY = "SUPER_SECRET"
ALGORITHM = "HS256"
app = FastAPI()
active_connections: List[Tuple[str, WebSocket]] = []


def decode_jwt(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None

async def get_user_from_ws(websocket: WebSocket) -> str:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(status_code=403, detail="Missing token")
    user = decode_jwt(token)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(status_code=403, detail="Invalid token")
    return user

def sanitize_message(msg: str) -> str:
    return html.escape(msg.strip())

@app.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket):
    user = await get_user_from_ws(websocket)
    await websocket.accept()
    active_connections.append((user, websocket))
    await broadcast(f"{user} joined the chat.", sender="system")

    try:
        while True:
            data = await websocket.receive_text()
            clean = sanitize_message(data)
            await broadcast(clean, sender=user)
    except WebSocketDisconnect:
        active_connections.remove((user, websocket))
        await broadcast(f"{user} left the chat.", sender="system")
        
async def broadcast(message: str, sender: str):
    for username, connection in active_connections:
        try:
            if username == sender:
                await connection.send_text(f"you: {message}")
            else:
                await connection.send_text(f"{sender}: {message}")
        except:
            continue

html_code = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>WebSocket Chat</title>
</head>
<body>
    <h1>WebSocket Chat</h1>
    <input id="tokenInput" placeholder="Paste your JWT here" style="width: 300px;">
    <button onclick="connect()">Connect</button>

    <form onsubmit="sendMessage(event)">
        <input type="text" id="messageText" autocomplete="off" />
        <button type="submit">Send</button>
    </form>

    <ul id="messages"></ul>

    <script>
        let ws = null;

        function connect() {
            const token = document.getElementById("tokenInput").value;
            ws = new WebSocket("ws://localhost:8000/ws/?token=" + token);

            ws.onopen = function () {
                appendSystemMessage("Connected to chat.");
            };

            ws.onmessage = function (event) {
                const messages = document.getElementById('messages');
                const message = document.createElement('li');
                const content = document.createTextNode(event.data);
                message.appendChild(content);
                messages.appendChild(message);
            };

            ws.onclose = function () {
                appendSystemMessage("Disconnected from chat.");
            };

            ws.onerror = function () {
                appendSystemMessage("WebSocket error.");
            };
        }

        function sendMessage(event) {
            event.preventDefault();
            const input = document.getElementById("messageText");
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(input.value);
                input.value = '';
            } else {
                appendSystemMessage("Not connected.");
            }
        }

        function appendSystemMessage(text) {
            const messages = document.getElementById('messages');
            const message = document.createElement('li');
            message.style.color = "gray";
            message.textContent = text;
            messages.appendChild(message);
        }
    </script>
</body>
</html>
"""

@app.get("/chat/")
async def chat_page():
    return HTMLResponse(html_code)

print(jwt.encode({"sub": "bob"}, "SUPER_SECRET", algorithm="HS256"))