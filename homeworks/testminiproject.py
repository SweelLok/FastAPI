from fastapi.testclient import TestClient
from miniproject import app


def test_parse_page():
    client = TestClient(app)
    response = client.get("/parse/?url=https://example.com")
    
    assert response.status_code == 200
    assert "headers" in response.json()