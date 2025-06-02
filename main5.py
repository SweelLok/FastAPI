from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional
from datetime import datetime


app = FastAPI()


# ==== BOOKS ====

class Book(BaseModel):
    id: int
    title: str
    author: str
    year: Optional[int]
    quantity: Optional[int]


books_db: List[Book] = []


@app.get("/books", response_model=List[Book])
def get_books():
    return books_db


@app.post("/books", status_code=201)
def add_book(book: Book):
    if any(b.id == book.id for b in books_db):
        raise HTTPException(status_code=400, detail="Книга з таким ID вже існує")
    books_db.append(book)
    return {"message": "Книгу додано успішно"}


@app.get("/books/{book_id}", response_model=Book)
def get_book(book_id: int):
    for book in books_db:
        if book.id == book_id:
            return book
    raise HTTPException(status_code=404, detail="Книгу не знайдено")



# ==== USERS ====

class User(BaseModel):
    first_name: str = Field(..., min_length=2)
    last_name: str = Field(..., min_length=2)
    email: EmailStr
    password: str
    phone: str


    @validator("first_name", "last_name")
    def only_letters(cls, v):
        if not v.isalpha():
            raise ValueError("Має містити лише літери")
        return v


    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8 or \
           not any(c.isupper() for c in v) or \
           not any(c.islower() for c in v) or \
           not any(c.isdigit() for c in v) or \
           not any(not c.isalnum() for c in v):
            raise ValueError("Пароль має бути складним")
        return v


    @validator("phone")
    def validate_phone(cls, v):
        digits = ''.join(c for c in v if c.isdigit())
        if len(digits) < 10 or len(digits) > 15:
            raise ValueError("Невірний формат телефону")
        return v


users_db: List[User] = []


@app.post("/register")
def register_user(user: User):
    if any(u.email == user.email for u in users_db):
        raise HTTPException(status_code=409, detail="Email вже зареєстровано")
    users_db.append(user)
    return {"message": "Користувача зареєстровано"}



# ==== EVENTS ====

class Event(BaseModel):
    id: int
    title: str
    date: datetime
    location: str


events_db: List[Event] = []
rsvp_db = {}


@app.post("/events", status_code=201)
def create_event(event: Event):
    if event.date < datetime.now():
        raise HTTPException(status_code=400, detail="Дата має бути у майбутньому")
    events_db.append(event)
    return {"message": "Подію створено"}


@app.get("/events")
def get_events():
    if not events_db:
        return [], 204
    return events_db


@app.get("/events/{event_id}")
def get_event(event_id: int):
    for event in events_db:
        if event.id == event_id:
            return event
    raise HTTPException(status_code=404, detail="Подію не знайдено")


@app.put("/events/{event_id}")
def update_event(event_id: int, updated: Event):
    for i, event in enumerate(events_db):
        if event.id == event_id:
            if updated.date < datetime.now():
                raise HTTPException(status_code=400, detail="Дата має бути у майбутньому")
            events_db[i] = updated
            return updated
    raise HTTPException(status_code=404, detail="Подію не знайдено")


@app.delete("/events/{event_id}")
def delete_event(event_id: int):
    for i, event in enumerate(events_db):
        if event.id == event_id:
            del events_db[i]
            return {"message": "Подію видалено"}
    raise HTTPException(status_code=404, detail="Подію не знайдено")


@app.patch("/events/{event_id}/reschedule")
def reschedule_event(event_id: int, new_date: datetime):
    for event in events_db:
        if event.id == event_id:
            if new_date < datetime.now():
                raise HTTPException(status_code=400, detail="Нова дата неправильна")
            event.date = new_date
            return {"message": "Час події оновлено"}
    raise HTTPException(status_code=404, detail="Подію не знайдено")


@app.post("/events/{event_id}/rsvp")
def rsvp_event(event_id: int, email: EmailStr):
    for event in events_db:
        if event.id == event_id:
            if event_id in rsvp_db and email in rsvp_db[event_id]:
                raise HTTPException(status_code=409, detail="Користувач вже зареєстрований")
            rsvp_db.setdefault(event_id, []).append(email)
            return {"message": "RSVP успішний"}
    raise HTTPException(status_code=404, detail="Подію не знайдено")