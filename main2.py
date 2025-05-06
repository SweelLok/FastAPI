from fastapi import FastAPI, HTTPException
import aiohttp
import aiomysql
import os

app = FastAPI()

URL = "https://jsonplaceholder.typicode.com/users"
MYSQL_CONNECTION_DATA = {
    "host": os.environ.get("MYSQL_HOST"),
    "port": int(os.environ.get("MYSQL_PORT", 3306)),
    "user": os.environ.get("MYSQL_USER"),
    "password": os.environ.get("MYSQL_PASSWORD"),
    "db": os.environ.get("MYSQL_DB"),
}


async def get_connection():
    return await aiomysql.connect(**MYSQL_CONNECTION_DATA)


@app.get("/api_users/")
async def get_users_api():
    async with aiohttp.ClientSession() as session:
        async with session.get(URL) as response:
            data = await response.json()
            return data


@app.get("/db_users/")
async def get_users_db():
    conn = await get_connection()
    try:
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT * FROM users")
            result = await cursor.fetchall()
            if not result:
                raise HTTPException(status_code=404, detail="No users found.")
            return result
    except aiomysql.Error as e:
        raise HTTPException(status_code=500, detail=f"MySQL error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    finally:
        conn.close()


@app.post("/add_user/")
async def add_user_to_db(user: str, email: str):
    if not user or not email:
        raise HTTPException(status_code=400, detail="User and email are required.")

    conn = await get_connection()
    try:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO users (name, email) VALUES (%s, %s)",
                (user, email)
            )
            await conn.commit()
            return {"status": "User added successfully"}
    except aiomysql.Error as e:
        raise HTTPException(status_code=500, detail=f"MySQL error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    finally:
        conn.close()


@app.post("/delete_user/{user_id}/")
async def delete_user(user_id: int):
    conn = await get_connection()
    try:
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = await cursor.fetchone()
            if not user:
                raise HTTPException(status_code=404, detail="User not found.")

            await cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            await conn.commit()
            return {"status": "User deleted successfully"}
    except aiomysql.Error as e:
        raise HTTPException(status_code=500, detail=f"MySQL error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    finally:
        conn.close()
