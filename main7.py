from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, EmailStr
from typing import List
from datetime import datetime, timezone


app = FastAPI()


class Order(BaseModel):
    product_name: str = Field(..., min_length=1)
    quantity: int = Field(default=1, gt=0)
    price_per_unit: float = Field(..., gt=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class User(BaseModel):
    name: str
    email: EmailStr
    orders: List[Order] = Field(default_factory=list)


db = {}


@app.post("/users/", response_model=User)
def create_user(user: User):
    if user.email in db:
        raise HTTPException(status_code=400, detail="Такий користувач вже є")
    db[user.email] = user
    return user

@app.get("/users/", response_model=User)
def get_user(email: EmailStr = Query(...)):
    user = db.get(email)
    if not user:
        raise HTTPException(status_code=404, detail="Користувача не знайдено")
    return user