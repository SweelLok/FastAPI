from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List

app = FastAPI(
    title="Library API",
    description="Простий API для керування книгами та користувачами.",
    version="1.0.0"
)

# ======== Pydantic моделі ========

class Book(BaseModel):
    id: int
    title: str = Field(..., example="Війна і мир")
    author: str = Field(..., example="Лев Толстой")
    year: int = Field(..., ge=0, le=2100, example=1869)

class User(BaseModel):
    id: int
    name: str = Field(..., example="Олександр")
    email: str = Field(..., example="user@example.com")

# ======== Фейкові бази даних ========
books_db: List[Book] = []
users_db: List[User] = []

# ======== Роути ========

@app.get(
    "/books/",
    response_model=List[Book],
    tags=["Books"],
    summary="Отримати список усіх книг",
    description="Повертає всі книги, що зберігаються у базі даних.",
    responses={200: {"description": "Список книг успішно отримано"}},
    include_in_schema=True
)
async def get_books():
    """Повертає список усіх книг."""
    return books_db


@app.post(
    "/books/",
    response_model=Book,
    tags=["Books"],
    summary="Додати нову книгу",
    description="Додає нову книгу до бази даних.",
    responses={
        201: {"description": "Книга успішно додана"},
        400: {"description": "Помилка у даних"}
    },
    include_in_schema=True
)
async def create_book(book: Book):
    """Додає нову книгу до списку."""
    books_db.append(book)
    return book


@app.get(
    "/users/",
    response_model=List[User],
    tags=["Users"],
    summary="Отримати список користувачів",
    description="Повертає список усіх зареєстрованих користувачів.",
    responses={200: {"description": "Список користувачів отримано"}},
    include_in_schema=True
)
async def get_users():
    """Повертає список користувачів."""
    return users_db


@app.post(
    "/users/",
    response_model=User,
    tags=["Users"],
    summary="Створити нового користувача",
    description="Додає нового користувача до бази даних.",
    responses={201: {"description": "Користувача додано"}, 400: {"description": "Помилка в даних"}},
    include_in_schema=True
)
async def create_user(user: User):
    """Додає нового користувача до бази."""
    users_db.append(user)
    return user