import base64

import aiosqlite
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import (
    HTTPBasic,
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
)
from pydantic import BaseModel, EmailStr, SecretStr

# pip install python-multipart

SQLITE_DB_NAME = "mydb.db"


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
security = HTTPBasic()


async def get_db():
    """Створення там повернення з'єднання з БД."""
    async with aiosqlite.connect(SQLITE_DB_NAME) as connection:
        connection.row_factory = aiosqlite.Row
        yield connection

        await connection.close()


async def create_tables() -> None:
    """Створення таблиць в БД при старті програми та автоматичне закриття з'єднання після завершення."""
    async with aiosqlite.connect(SQLITE_DB_NAME) as connection:
        cursor: aiosqlite.Cursor = await connection.cursor()
        await cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS users (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    name      VARCHAR(30) NOT NULL,
                    email     VARCHAR(50) NOT NULL,
                    password  VARCHAR(30) NOT NULL,
                    is_active BOOLEAN NOT NULL CHECK (is_active IN (0, 1))
                );
            """
        )
        await connection.commit()
        await connection.close()


app = FastAPI(on_startup=(create_tables,))


# id: 1
# name: "John Doe"
# email: "john.doe@example.com"
# password: "super-password"
# is_active: 1
class UserCreate(BaseModel):
    """Модель користувача для створення."""

    name: str
    email: EmailStr
    password: SecretStr  # * * * * *


class UserShow(UserCreate):
    """Модель користувача для відображення."""

    id: int
    is_active: bool = False


class Token(BaseModel):
    """Модель токена доступу."""

    token_type: str
    access_token: str


@app.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    connection: aiosqlite.Connection = Depends(get_db),
):
    async with connection.cursor() as cursor:
        await cursor.execute(
            "SELECT * FROM users WHERE email = ?", (form_data.username,)
        )

        db_user = await cursor.fetchone()

        if db_user is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User does not exist.")

    user = UserShow(**db_user)

    if user.password.get_secret_value() != form_data.password:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Incorrect password.")

    # кодування токена доступу в base64 кодування ([a-z], [A-Z], [0-9] -, _)
    # безпечне для передавання в URL
    # bob@example.com-Bob --> Ym9iQGV4YW1wbGUuY29tLUJvYg
    return Token(
        access_token=base64.urlsafe_b64encode(
            f"{user.email}-{user.name}".encode("utf-8")
        ).decode("utf-8"),
        token_type="bearer",
    )


async def decode_token(token: str):
    """
    Декодування токену доступу отриманого з заголовку Authorization.
    Приклад: Authorization: Bearer am9obi5kb2VAZXhhbXBsZS5jb20tSm9obiBEb2U=
    """
    try:
        # email-name.split("-")[0] --> email
        # Ym9iQGV4YW1wbGUuY29tLUJvYg -> [bob@example.com, Bob][0] -> email
        decoded_user_email = (
            base64.urlsafe_b64decode(token).split(b"-")[0].decode("utf-8")
        )
    except (UnicodeDecodeError, ValueError):
        return None

    return decoded_user_email


@app.get("/users/me", response_model=UserShow)
async def get_user_me(
    token: str = Depends(oauth2_scheme),
    connection: aiosqlite.Connection = Depends(get_db),
):
    decoded_email = await decode_token(token)
    async with connection.cursor() as cursor:
        await cursor.execute("SELECT * FROM users WHERE email = ?", (decoded_email,))
        db_user = await cursor.fetchone()
				

        if db_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    decoded_user = UserShow(**db_user)

    if not decoded_user.is_active:
        raise HTTPException(400, "User is not active.")

    return decoded_user


@app.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserShow)
async def user_registration(
    user_data: UserCreate, connection: aiosqlite.Connection = Depends(get_db)
) -> UserShow:
    """Реєстрацію користувача в базі даних."""
    async with connection.cursor() as cursor:
        await cursor.execute("SELECT 1 FROM users WHERE email = ?;", (user_data.email,))
        db_user = await cursor.fetchone()

        if db_user is not None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "User exists.")

        await cursor.execute(
            "INSERT INTO users (name, email, password, is_active) VALUES (?, ?, ?, ?) RETURNING id;",
            (
                user_data.name,
                user_data.email,
                # необхідно явно записати в БД пароль, а не *****
                user_data.password.get_secret_value(),
                True,
            ),
        )

        last_inserted = await cursor.fetchone()
        await connection.commit()

    return UserShow(
        **user_data.model_dump(exclude={"is_active"}),
        id=last_inserted["id"],
        is_active=True,
    )
