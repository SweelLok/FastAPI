from fastapi import FastAPI, Path, Query, Header, HTTPException
from datetime import datetime
from typing import Optional


app = FastAPI()


@app.get("/users/{user_id}")
def greet_user(
    user_id: int = Path(..., description="User ID must be an integer"),
    timestamp: Optional[str] = Query(None, description="Optional timestamp"),
    x_client_version: str = Header(..., alias="X-Client-Version")
):
    
    current_time = timestamp or datetime.today().isoformat()

    return {
        "user_id": user_id,
        "timestamp": current_time,
        "X-Client-Version": x_client_version,
        "message": f"Hello, user {user_id}!"
    }	