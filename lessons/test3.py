from fastapi import FastAPI, HTTPException
from databases import Database
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String


DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL)
metadata = MetaData()
users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String)
)
metadata.create_all(engine)
database = Database(DATABASE_URL)

app = FastAPI()


@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.post("/users/{user_name}")
async def create_user(user_name: str):

    query = users.select().where(users.c.name == user_name)
    existing_user = await database.fetch_one(query)

    if existing_user:
        raise HTTPException(status_code=400, detail="User with this name already exists")
    
    query = users.insert().values(name=user_name)
    await database.execute(query)

    return {"user_name": user_name}

@app.get("/users")
async def read_users():

    query = users.select()
    all_users = await database.fetch_all(query)

    return {"users": all_users}