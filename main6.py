from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
from typing import List
from datetime import datetime

app = FastAPI()
movies_db = []


class Movie(BaseModel):
    id: int
    title: str
    director: str
    release_year: int = Field(..., example=2024)
    rating: float = Field(..., ge=0, le=10, example=8.5)

    @validator('release_year')
    def validate_release_year(cls, value):
        current_year = datetime.now().year
        if value > current_year:
            raise ValueError("Рік випуску не може бути у майбутньому.")
        return value


class MovieCreate(BaseModel):
    title: str
    director: str
    release_year: int = Field(..., example=2022)
    rating: float = Field(..., ge=0, le=10, example=8.5)

    @validator('release_year')
    def validate_release_year(cls, value):
        current_year = datetime.now().year
        if value > current_year:
            raise ValueError("Рік випуску не може бути у майбутньому.")
        return value


@app.get("/movies/", response_model=List[Movie])
def get_all_movies():
    return movies_db


@app.post("/movies/", response_model=Movie, status_code=201)
def add_movie(movie: MovieCreate):
    new_id = len(movies_db) + 1
    new_movie = Movie(id=new_id, **movie.dict())
    movies_db.append(new_movie)
    return new_movie


@app.get("/movies/{id}/", response_model=Movie)
def get_movie(id: int):
    for movie in movies_db:
        if movie.id == id:
            return movie
    raise HTTPException(status_code=404, detail="Фільм не знайдено")


@app.delete("/movies/{id}/", status_code=204)
def delete_movie(id: int):
    for i, movie in enumerate(movies_db):
        if movie.id == id:
            del movies_db[i]
            return
    raise HTTPException(status_code=404, detail="Фільм не знайдено")