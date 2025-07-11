import os
import pathlib
import time

import aiofiles
import httpx
import uvicorn
import yagmail
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

app = FastAPI(title="Background Tasks")


class User(BaseModel):
    """Модель користувача."""

    name: str = Field(examples=["John", "Josh"])
    email: EmailStr = Field(examples=["john@example.com"])
    phone: str = Field(examples=["+380661234567"])


users_db: list[User] = []


async def simulate_io_delay() -> None:
    async with httpx.AsyncClient() as client:
        response = await client.get("https://httpbin.org/delay/3", timeout=10)
        print(response.json())


@app.post("/register", status_code=status.HTTP_201_CREATED, response_model=User)
async def user_registration(user_data: User, bg_tasks: BackgroundTasks) -> User:
    if user_data.email in {u.email for u in users_db}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User exists"
        )
    users_db.append(user_data)

    bg_tasks.add_task(simulate_io_delay)
    print([(task.func.__name__, task.kwargs, task.args) for task in bg_tasks.tasks])
    return User(**user_data.model_dump())


if __name__ == "__main__":
    uvicorn.run("test10:app", port=8000, reload=True)