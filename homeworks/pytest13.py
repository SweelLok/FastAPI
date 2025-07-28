import pytest
from fastapi.testclient import TestClient
from homework13 import app, SECRET_KEY, ALGORITHM
import jwt
import websockets


client = TestClient(app)


@pytest.fixture
def token():
    return jwt.encode({"sub": "testuser"}, SECRET_KEY, algorithm=ALGORITHM)

def test_chat_page():
    response = client.get("/chat/")
    assert response.status_code == 200
    assert "WebSocket Chat" in response.text

@pytest.mark.asyncio
async def test_websocket_valid_token(token):
    url = f"ws://localhost:8000/ws/?token={token}"
    async with websockets.connect(url) as websocket:
        greeting = await websocket.recv()
        assert "testuser joined the chat." in greeting

        await websocket.send("Hello pytest!")
        response = await websocket.recv()
        assert "you: Hello pytest!" == response

@pytest.mark.asyncio
async def test_websocket_invalid_token():
    url = f"ws://localhost:8000/ws/?token=invalidtoken"
    with pytest.raises(websockets.exceptions.InvalidStatus) as exc_info:
        async with websockets.connect(url) as websocket:
            pass
    assert exc_info.value.response.status_code == 403