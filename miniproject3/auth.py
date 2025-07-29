import bcrypt
import base64
import sqlite3

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field, SecretStr, field_validator
from .config import DB_NAME, oauth2_scheme
from fastapi import APIRouter

router = APIRouter()

class User(BaseModel):
    name: str
    email: EmailStr
    password: SecretStr
    
class Token(BaseModel):
    """Модель токена доступу."""

    token_type: str = Field(description="type of the token", examples=["bearer"])
    access_token: str = Field(description="Token Value", examples=["YmasdeQ=="])

class UserShow(User):
    id: int

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Name of user can't be none")
        return v

    @field_validator("email")
    @classmethod
    def email_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Email of user can't be none")
        if not (v.endswith("@gmail.com") or v.endswith("@example.com")):
            raise ValueError("Email might be in domen @gmail.com")
        return v

    @field_validator("password")
    @classmethod
    def password_not_empty(cls, v):
        if not v.get_secret_value().strip():
            raise ValueError("Password of user can't be none")
        if len(v) < 8:
            raise ValueError("Password should be at least 8 characters long")
        return v

async def decode_token(token: str):

    try:
        decoded_user_email = (
            base64.urlsafe_b64decode(token).split(b"-")[0].decode("utf-8")
        )
    except (UnicodeDecodeError, ValueError):
        return None

    return decoded_user_email

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


@router.post(
    "/register/",
    status_code=status.HTTP_201_CREATED,
    summary="Реєстрація користувача",
    description="Реєстрація нового користувача з хешуванням паролю.",
    tags=["Аутентифікація"],
    responses={
        201: {"description": "Користувача успішно зареєстровано"},
        400: {"description": "Email вже зареєстрований або некоректні дані"},
    }
)
async def register_user(user: User):
    with sqlite3.connect(DB_NAME) as connection:
        cursor: sqlite3.Cursor = connection.cursor()
        cursor.execute(
            "SELECT 1 FROM users WHERE email = ?",
            (user.email,),
        )
        if cursor.fetchone() is not None:
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed_password = hash_password(user.password.get_secret_value())

        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (user.name, user.email, hashed_password),
        )
        connection.commit()

    return {"message": f"User {user.name} registered successfully"}

async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    with sqlite3.connect(DB_NAME) as connection:
        connection.row_factory = sqlite3.Row
        cursor: sqlite3.Cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE email = ?", (form_data.username,)
        )

        db_user = cursor.fetchone()

        if db_user is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User does not exist.")

    user = UserShow(**dict(db_user))

    if not verify_password(form_data.password, user.password.get_secret_value()):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Incorrect password.")

    return Token(
        access_token=base64.urlsafe_b64encode(
            f"{user.email}-{user.name}".encode("utf-8")
        ).decode("utf-8"),
        token_type="bearer",
    )

@router.post(
    "/token",
    response_model=Token,
    summary="Отримання токену доступу",
    description="Отримання JWT токену за email та паролем (логін).",
    tags=["Аутентифікація"],
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Токен отримано успішно"},
        400: {"description": "Неправильний пароль"},
        404: {"description": "Користувача не знайдено"},
    }
)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    return await login(form_data)

@router.get(
    "/test/",
    summary="Тестовий ендпоінт",
    description="Тестовий ендпоінт, який вимагає передачі токена авторизації.",
    tags=["Тести"],
    status_code=status.HTTP_200_OK,
)
async def test(token: str = Depends(oauth2_scheme)):
    return "hello"