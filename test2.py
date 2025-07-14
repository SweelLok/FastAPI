import aiomysql
import os

from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel


load_dotenv(".env")

MYSQL_CONNECTION_DATA = {
    "host": os.environ.get("MYSQL_HOST"),
    "port": int(os.environ.get("MYSQL_PORT", 3306)),
    "user": os.environ.get("MYSQL_USER"),
    "password": os.environ.get("MYSQL_PASSWORD"),
    "db": os.environ.get("MYSQL_DB"),
}


async def get_mysql_connection() -> aiomysql.Connection:
    """Створення та повернення з'єднання."""
    return await aiomysql.connect(**MYSQL_CONNECTION_DATA)

@asynccontextmanager
async def create_tables(_: FastAPI):
    """
    Створення таблиць в БД при старті програми та закриття з'єднання з БД після завершення.
    """
    async with aiomysql.connect(**MYSQL_CONNECTION_DATA) as connection:
        cursor: aiomysql.Cursor = await connection.cursor()
        await cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT,
                name VARCHAR(50),
                email VARCHAR(50),
                PRIMARY KEY(id)
            );
            """
        )
        await cursor.execute(
            """	
            CREATE TABLE IF NOT EXISTS books (
                id INT AUTO_INCREMENT,
                title VARCHAR(50),
                author VARCHAR(50),
                year INTEGER,
                PRIMARY KEY(id)
            );
            """
        )
        await connection.commit()

    yield
    

app = FastAPI(lifespan=create_tables)


class Book(BaseModel):
    """Базова модель книги."""

    title: str
    author: str
    year: int


class BookInfo(Book):
    """Модель книги для відображення."""

    id: int
    title: str
    author: str
    year: int


class BookUpdate(BaseModel):
    """Модель книги для оновлення."""

    title: str | None = None
    author: str | None = None
    year: int | None = None

    
@app.post("/books/")
async def create_book(book: Book) -> BookInfo:
    """Створення книги."""
    connection = await get_mysql_connection()

    try:
        async with connection.cursor() as cursor:
            await cursor.execute("SELECT 1 FROM books WHERE title=%s;", (book.title,))
            db_book = await cursor.fetchone()

            if db_book is not None:
                raise HTTPException(400, "Book is already exists.")

            await cursor.execute(
                "INSERT INTO books (title, author, year) VALUES (%s, %s, %s);",
                (
                    book.title,
                    book.author,
                    book.year,
                ),
            )
            await connection.commit()
            await cursor.execute("SELECT LAST_INSERT_ID();")
            user_id = await cursor.fetchone()
    except aiomysql.Error as e:
        raise e
    finally:
        await connection.ensure_closed()

    return BookInfo(**book.model_dump(), id=user_id[0])

@app.get("/books/")
async def get_books(limit: int=Query(default=100, description="Books count"),) -> list[BookInfo]:
    connection = await get_mysql_connection()

    try:
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM books LIMIT %s;", (limit,))
            books = await cursor.fetchall()
            if not books:
                raise HTTPException(404, "Books not found.")
    except aiomysql.Error as e:
        raise e
    finally:
        await connection.ensure_closed()

    return [BookInfo(**book) for book in books]

@app.get("/books/{book_id}/")
async def get_books(book_id: int) -> BookInfo:
    connection = await get_mysql_connection()

    try:
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM books WHERE id=%s;", (book_id,))
            book = await cursor.fetchone()
            if not book:
                raise HTTPException(404, "Book not found.")
    except aiomysql.Error as e:
        raise e
    finally:
        await connection.ensure_closed()

    return BookInfo(**book)

@app.put("/books/{book_id}/")
async def update_book(book_id: int, book: BookUpdate) -> BookInfo:
    connection = await get_mysql_connection()

    try:
        async with connection.cursor() as cursor:
            await cursor.execute("SELECT * FROM books WHERE id=%s;", (book_id,))
            db_book = await cursor.fetchone()
            if not db_book:
                raise HTTPException(404, "Book not found.")

            await cursor.execute("UPDATE books SET title=%s, author=%s, year=%s WHERE id=%s;", \
                (
                    book.title,
                    book.author,
                    book.year,
                    book_id,
                )
            )
            await connection.commit()
    except aiomysql.Error as e:
        raise e
    finally:
        await connection.ensure_closed()

    return BookInfo(**book.model_dump(), id=book_id)

@app.delete("/books/{book_id}/")
async def delete_book(book_id: int) -> JSONResponse:
    connection = await get_mysql_connection()

    try:
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM books WHERE id=%s;", (book_id,))
            db_book = await cursor.fetchone()
            if not db_book:
                raise HTTPException(404, "Book not found.")

            await cursor.execute("DELETE FROM books WHERE id=%s;", (book_id,))
            await connection.commit()
    except aiomysql.Error as e:
        raise e
    finally:
        await connection.ensure_closed()

    return JSONResponse({"message": "Book deleted successfully."}, status_code=200)