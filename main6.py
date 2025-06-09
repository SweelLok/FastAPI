from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import List
from datetime import datetime

app = FastAPI()

movies_db = []

class Movie(BaseModel):
    id: int
    title: str
    director: str
    release_year: int = Field(..., examples=[2024])
    rating: float = Field(..., ge=0, le=10)

    @field_validator("release_year")
    @classmethod
    def year_check(cls, val):
        if val > datetime.now().year:
            raise ValueError("Рік випуску не може бути у майбутньому")
        return val


class MovieCreate(BaseModel):
    title: str
    director: str
    release_year: int = Field(..., examples=[2023])
    rating: float = Field(..., ge=0, le=10)

    @field_validator("release_year")
    @classmethod
    def no_future_year(cls, v):
        if v > datetime.now().year:
            raise ValueError("Рік має бути не пізніше поточного")
        return v


@app.get("/movies/")
def fetch_movies():
    return movies_db


@app.post("/movies/", status_code=201)
def create_movie(movie: MovieCreate):
    new_id = len(movies_db) + 1
    film = Movie(id=new_id, **movie.model_dump())
    movies_db.append(film)
    return film


@app.get("/movies/{movie_id}")
def fetch_movie(movie_id: int):
    for m in movies_db:
        if m.id == movie_id:
            return m
    raise HTTPException(status_code=404, detail="Фільм не знайдено")


@app.delete("/movies/{movie_id}")
def remove_movie(movie_id: int):
    for index, m in enumerate(movies_db):
        if m.id == movie_id:
            movies_db.pop(index)
            return {"message": "Фільм видалено"}
    raise HTTPException(status_code=404, detail="Фільм не знайдено")