import aiosqlite

from enum import StrEnum
from fastapi import FastAPI, HTTPException, Request, Response, status, Depends
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from pydantic import BaseModel, EmailStr, field_validator


class JobTitles(StrEnum):
    """Посади для співробітників."""

    DEVELOPER = "developer"
    TESTER = "tester"
    HR = "hr"
    COPYWRITER = "copywriter"
    MANAGER = "manager"
    ANALYST = "analyst"


class DepartmentCreate(BaseModel):
    """Поля для створення підрозділу."""

    name: str


class DepartmentInfo(BaseModel):
    """Поля для отримання інформації про підрозділ."""

    id: int
    name: str


class EmployeeCreate(BaseModel):
    """Поля для створення співробітника."""

    name: str
    email: str
    job_title: JobTitles
    salary: float
    department_id: int

    @field_validator("email")
    @classmethod
    def email_validation(cls, email: str) -> str:
        """Додаткова валідація поля для електронної пошти."""
        if "@" not in email:
            raise ValueError("Email should contain @ symbol.")

        return email


class EmployeeInfo(BaseModel):
    """Поля для отримання інформації про співробітника."""

    id: int
    name: str
    # стандартна валідація пошти за допомогою поля EmailStr
    email: EmailStr
    job_title: JobTitles
    salary: float
    department_id: int


SQLITE_DB_NAME = "corproration.db"

async def get_connetcion():
    async with aiosqlite.connect(SQLITE_DB_NAME) as connection:
        connection.row_factory = aiosqlite.Row
        yield connection
        await connection.commit()
        

async def create_tables() -> None:
    """Створення таблиць в БД при старті програми та автоматичне закриття з'єднання після завершення."""
    async with aiosqlite.connect(SQLITE_DB_NAME) as connection:
        cursor: aiosqlite.Cursor = await connection.cursor()
        await cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS employees (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    name            VARCHAR(30) NOT NULL,
                    email           VARCHAR(50) NOT NULL,
                    job_title       VARCHAR(30) NOT NULL,
                    salary          INTEGER,
                    department_id   INTEGER,
                    FOREIGN KEY (department_id) REFERENCES departments(id)
                );
            """
        )
        await cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS departments (
                    id      INTEGER PRIMARY KEY AUTOINCREMENT,
                    name    VARCHAR(50) UNIQUE NOT NULL
                );
            """
        )
        await connection.commit()


app = FastAPI

@app.post("/departments/", status_code=status.HTTP_201_CREATED, Response_model=DepartmentInfo)
async def create_department(data: DepartmentCreate, connection: aiosqlite.Connection = Depends(get_connetcion)):
    async with connection.cursor() as cursor:
        await cursor.execute("SELECT * FROM departments WHERE name = ?", (data.name,))
        department = await cursor.fetchone()
        
        if department is not None:
          raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Department already exists.")
        
        await cursor.execute("INSERT INTO departments (name) VALUES (?) RETURNING id", (data.name,))
        last_inserted = await cursor.fetchone()
        await connection.commit()
        
    return DepartmentInfo(id=last_inserted["id"], name=data.name)