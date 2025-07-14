from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional
from datetime import datetime


app = FastAPI()


class Book(BaseModel):
    id: int
    title: str
    author: str
    year: Optional[int] = None
    quantity: Optional[int] = None


class Event(BaseModel):
    id: int
    title: str
    date: datetime
    location: str


books_db = []


@app.get("/books/")
def list_books():
    return books_db

@app.post("/books/", status_code=201)
def create_book(book: Book):
    for b in books_db:
        if b.id == book.id:
            raise HTTPException(status_code=400, detail="ID книги вже існує")
    books_db.append(book)
    return book

@app.get("/books/{book_id}")
def retrieve_book(book_id: int):
    for b in books_db:
        if b.id == book_id:
            return b
    raise HTTPException(status_code=404, detail="Книга не знайдена")


class User(BaseModel):
    first_name: str = Field(..., min_length=2)
    last_name: str = Field(..., min_length=2)
    email: EmailStr
    password: str
    phone: str

    @field_validator("first_name", "last_name")
    @classmethod
    def check_names(cls, value):
        if not value.isalpha():
            raise ValueError("Допускаються лише літери")
        return value

    @field_validator("password")
    @classmethod
    def strong_password(cls, val):
        if (
            len(val) < 8
            or not any(c.isupper() for c in val)
            or not any(c.islower() for c in val)
            or not any(c.isdigit() for c in val)
            or not any(not c.isalnum() for c in val)
        ):
            raise ValueError("Пароль надто простий")
        return val

    @field_validator("phone")
    @classmethod
    def phone_format(cls, value):
        digits = "".join(c for c in value if c.isdigit())
        if len(digits) < 10:
            raise ValueError("Занадто короткий номер")
        return value


users_db = []
events_db = []
rsvp_db = {}


@app.post("/register", status_code=201)
def register(user: User):
    for u in users_db:
        if u.email == user.email:
            raise HTTPException(status_code=409, detail="Такий email вже існує")
    users_db.append(user)
    return user

@app.post("/events/", status_code=201)
def add_event(event: Event):
    if event.date <= datetime.now():
        raise HTTPException(status_code=400, detail="Дата події має бути у майбутньому")
    events_db.append(event)
    return event

@app.get("/events/")
def all_events():
    return events_db

@app.get("/events/{event_id}")
def event_detail(event_id: int):
    for ev in events_db:
        if ev.id == event_id:
            return ev
    raise HTTPException(status_code=404, detail="Подію не знайдено")

@app.put("/events/{event_id}")
def modify_event(event_id: int, data: Event):
    for idx, ev in enumerate(events_db):
        if ev.id == event_id:
            if data.date < datetime.now():
                raise HTTPException(status_code=400, detail="Нова дата має бути у майбутньому")
            events_db[idx] = data
            return data
    raise HTTPException(status_code=404, detail="Не знайдено")

@app.delete("/events/{event_id}")
def remove_event(event_id: int):
    for i, ev in enumerate(events_db):
        if ev.id == event_id:
            events_db.pop(i)
            return {"message": "Подію видалено"}
    raise HTTPException(status_code=404, detail="Не знайдено")

@app.patch("/events/{event_id}/reschedule")
def change_event_date(event_id: int, new_date: datetime):
    for ev in events_db:
        if ev.id == event_id:
            if new_date < datetime.now():
                raise HTTPException(status_code=400, detail="Дата в минулому")
            ev.date = new_date
            return ev
    raise HTTPException(status_code=404, detail="Подія не знайдена")

@app.post("/events/{event_id}/rsvp", status_code=201)
def rsvp(event_id: int, email: EmailStr):
    for ev in events_db:
        if ev.id == event_id:
            if rsvp_db.get(event_id) and email in rsvp_db[event_id]:
                raise HTTPException(status_code=409, detail="Вже зареєстровано")
            rsvp_db.setdefault(event_id, []).append(email)
            return {"message": "RSVP збережено"}
    raise HTTPException(status_code=404, detail="Подію не знайдено")