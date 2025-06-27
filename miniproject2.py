from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel, Field, SecretStr
from typing import List
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
)
import aiosqlite
import base64


app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

DB_PATH = "users.db"


class Token(BaseModel):
    """Модель токена доступу."""

    token_type: str = Field(description="type of the token", examples=["bearer"])
    access_token: str = Field(description="Token Value", examples=["YmasdeQ=="])

class Hobby(BaseModel):
		name: str = Field(..., description="Name of the hobby", examples=["Reading", "Traveling", "Cooking"])

class User(BaseModel):
		name: str = Field(..., description="Name of the person", examples=["John Doe", "Jane Smith"])
		year: int = Field(..., description="Year of birth", examples=[1990, 1985])
		hobbies: List[Hobby] = Field(..., description="List of hobbies of the person", examples=[[{"name": "Reading"}, {"name": "Traveling"}]])
		password: SecretStr = Field(..., description="Password for the user", min_length=8, examples=["strongpassword123", "anotherpassword456"])

@app.on_event("startup")
async def database():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")

        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                name TEXT PRIMARY KEY,
                year INTEGER NOT NULL,
                password TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS hobbies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT,
                hobby TEXT,
                FOREIGN KEY (user_name) REFERENCES users(name) ON DELETE CASCADE
            )
        """)
        await db.commit()


@app.post(
    "/token",
    response_model=Token,
    tags=["auth"],
    summary="Get access token by provided name and password",
    description="Endpoint for auth purpose",
    responses={
        200: {"description": "Success"},
        404: {"description": "User not found"},
        400: {"description": "Incorrect password provided"},
    },
    operation_id="get-access-token",
    include_in_schema=True,
    name="get token"
)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        result = await db.execute("SELECT * FROM users WHERE name = ?", (form_data.username,))
        user = await result.fetchone()
        if not user:
            raise HTTPException(404, "User not found")
        if user["password"] != form_data.password:
            raise HTTPException(400, "Incorrect password")
        return Token(
            access_token=base64.urlsafe_b64encode(form_data.username.encode()).decode(),
            token_type="bearer"
        )

@app.post("/users/", 
		response_model=User,
    tags=["Users"],
    summary="Create a new user",
    description="Creates a new user with name, year of birth, and hobbies.",
    responses={200: {"description": "User created successfully"}},
    include_in_schema=True
)
async def create_user(user: User):
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute("INSERT INTO users (name, year, password) VALUES (?, ?, ?)",
                             (user.name, user.year, user.password.get_secret_value()))
            for hobby in user.hobbies:
                await db.execute("INSERT INTO hobbies (user_name, hobby) VALUES (?, ?)", (user.name, hobby.name))
            await db.commit()
            return user
        except aiosqlite.IntegrityError:
            raise HTTPException(400, "User already exists")

@app.get("/users/",
		response_model=List[User],
    tags=["Users"],
    summary="Get users",
    description="Get all users in the system.",
    responses={200: {"description": "Users retrieved successfully"}},
    include_in_schema=True
)
async def get_users(token: str = Depends(oauth2_scheme)):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        users_data = await db.execute("SELECT * FROM users")
        users = await users_data.fetchall()

        result = []
        for user in users:
            hobbies_data = await db.execute("SELECT hobby FROM hobbies WHERE user_name = ?", (user["name"],))
            hobbies = [Hobby(name=row["hobby"]) for row in await hobbies_data.fetchall()]
            result.append(User(
                name=user["name"],
                year=user["year"],
                hobbies=hobbies,
                password=SecretStr(user["password"])
            ))
        return result

@app.put("/users/{name}",
		response_model=User,
    tags=["Users"],
    summary="Update a user",
    description="Updates a user's information by name.",
    responses={200: {"description": "User updated successfully"}},
    include_in_schema=True
)
async def update_user(name: str, user: User):
    async with aiosqlite.connect(DB_PATH) as db:
        result = await db.execute("SELECT * FROM users WHERE name = ?", (name,))
        existing = await result.fetchone()
        if not existing:
            raise HTTPException(404, "User not found")

        await db.execute("UPDATE users SET name = ?, year = ?, password = ? WHERE name = ?",
                         (user.name, user.year, user.password.get_secret_value(), name))
        await db.execute("DELETE FROM hobbies WHERE user_name = ?", (name,))
        for hobby in user.hobbies:
            await db.execute("INSERT INTO hobbies (user_name, hobby) VALUES (?, ?)", (user.name, hobby.name))
        await db.commit()
        return user

@app.delete("/users/{name}",
    response_model=User,
    tags=["Users"],
    summary="Delete a user",
    description="Deletes a user by name.",
    responses={200: {"description": "Deleted user successfully"}},
    include_in_schema=True
)
async def delete_user(name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")

        db.row_factory = aiosqlite.Row
        user_data = await db.execute("SELECT * FROM users WHERE name = ?", (name,))
        user = await user_data.fetchone()
        if not user:
            raise HTTPException(404, "User not found")

        hobbies_data = await db.execute("SELECT hobby FROM hobbies WHERE user_name = ?", (name,))
        hobbies = [Hobby(name=row["hobby"]) for row in await hobbies_data.fetchall()]

        await db.execute("DELETE FROM users WHERE name = ?", (name,))
        await db.commit()

        return User(name=user["name"], year=user["year"], hobbies=hobbies, password=SecretStr(user["password"]))
