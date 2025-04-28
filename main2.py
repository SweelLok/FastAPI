from fastapi import FastAPI
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


@app.get("/api_users/")
async def get_users_api():
    async with aiohttp.ClientSession() as session:
        async with session.get(URL) as response:
            data = await response.json()
            return data


@app.get("/db_users/")
async def get_users_db():
	conn = await aiomysql.connect(**MYSQL_CONNECTION_DATA)

	try:
		async with conn.cursor() as cursor:
			await cursor.execute("SELECT * FROM users")
			result = await cursor.fetchall()
			if not result:
				return {"error": "No users found"}            
			
	except Exception as e:
		return {"error": str(e)}
	finally:
		conn.close()

	return result


@app.post("/add_user/")
async def add_user_to_db(user: str, email: str):
	conn = await aiomysql.connect(**MYSQL_CONNECTION_DATA)

	if not user or not email:
		return {"error": "User and email are required"}
	
	try:
		async with conn.cursor() as cursor:
			await cursor.execute(
				"INSERT INTO users (name, email) VALUES (%s, %s)",
				(user, email)
			)
			await conn.commit()
	except Exception as e:
		return {"error": str(e)}
	finally:
		conn.close()

	return {"status": "User added successfully"}


@app.post("/delete_user/{user_id}/")
async def delete_user(user_id: int):
	conn = await aiomysql.connect(**MYSQL_CONNECTION_DATA)

	try:
		async with conn.cursor() as cursor:
			await cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
			user = await cursor.fetchone()
			
			if not user:
				return {"error": "User not found"}
			
			await cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
			await conn.commit()
			return {"status": "User deleted successfully"}
	except Exception as e:
		return {"error": str(e)}
	finally:
		conn.close()