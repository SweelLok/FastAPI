import asyncio
import httpx
import uvicorn
import random
import pytest

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr, Field


async def startup_event() -> None:
    asyncio.create_task(process_task_queue())

app = FastAPI(title="Background Tasks", on_startup={startup_event,})

class User(BaseModel):
    """Модель користувача."""

    name: str = Field(examples=["John", "Josh"])
    email: EmailStr = Field(examples=["john@example.com"])
    phone: str = Field(examples=["+380661234567"])

users_db: list[User] = []

task_queue = asyncio.Queue()


async def process_task_queue():
    while True:
        task = await task_queue.get()
        try:
            await task
        except Exception as e:
            print(f"Error: {e}")
        else:
            task_queue.task_done()
                    
        if task_queue.empty():
            print("All tasks have been completed")
        
async def simulate_io_delay() -> None:
    async with httpx.AsyncClient() as client:
        response = await client.get("https://httpbin.org/delay/3", timeout=10)
        print(response.json())

async def run_task(name: str, delay: int) -> None:
    print(f"Task {name}  with delay {delay} started")
    await asyncio.sleep(delay)
    print(f"Task {name} completed in {delay} seconds")
    return {"success": f"Task {name} completed in {delay} seconds"}

@app.post("/add-task/", status_code=status.HTTP_202_ACCEPTED)
async def add_task(name: str):
      await task_queue.put(run_task(name, delay=random.randint(3, 10)))
      return {"message": f"Task {name} has been added to the queue"}

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

@pytest.mark.asyncio
async def test_add_task() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(base_url="http://127.0.0.0:8000") as client:
        response = await client.post("/add-task/", params={"name": "test_task"})

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == {"message": "Task test_task has been added to the queue"}
    assert task_queue.qsize() == 3
      

if __name__ == "__main__":
    uvicorn.run("test10:app", port=8000, reload=True)