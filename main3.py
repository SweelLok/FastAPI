from fastapi import FastAPI
import uvicorn
import aiomysql
import os


app = FastAPI()


MYSQL_CONNECTION_DATA = {
    "host": os.environ.get("MYSQL_HOST"),
    "port": int(os.environ.get("MYSQL_PORT", 3306)),
    "user": os.environ.get("MYSQL_USER"),
    "password": os.environ.get("MYSQL_PASSWORD"),
    "db": os.environ.get("MYSQL_DB"),
}


@app.get("/todo/")
async def get_todo():
		conn = await aiomysql.connect(**MYSQL_CONNECTION_DATA)
		
		try:
			async with conn.cursor() as cursor:
				await cursor.execute("SELECT * FROM todo")
				result = await cursor.fetchall()
				if not result:
					return {"error": "No todos found"}
				
		except Exception as e:
			return {"error": str(e)}
		
		finally:
			conn.close()

		return result


@app.get("/todo/{todo_id}")
async def get_todo_by_id(todo_id: int):
		conn = await aiomysql.connect(**MYSQL_CONNECTION_DATA)
		
		try:
			async with conn.cursor() as cursor:
				await cursor.execute("SELECT * FROM todo WHERE todo_id = %s", (todo_id,))
				result = await cursor.fetchone()
				if not result:
					return {"error": "Todo not found"}
				
		except Exception as e:
			return {"error": str(e)}
		
		finally:
			conn.close()

		return result


@app.post("/add_todo/")
async def add_todo(name: str, description: str):
		conn = await aiomysql.connect(**MYSQL_CONNECTION_DATA)
		
		try:
			async with conn.cursor() as cursor:
				await cursor.execute(
					"INSERT INTO todo (name, description) VALUES (%s, %s)",
					(name, description)
				)
				await conn.commit()
				
		except Exception as e:
			return {"error": str(e)}
		
		finally:
			conn.close()

		return {"message": "Todo added successfully"}


@app.put("/update_todo/{todo_id}")
async def update_todo(todo_id: int, name: str, description: str):
		conn = await aiomysql.connect(**MYSQL_CONNECTION_DATA)
		
		try:
			async with conn.cursor() as cursor:
				await cursor.execute("SELECT * FROM todo WHERE todo_id = %s", (todo_id,))
				todo = await cursor.fetchone()
				
				if not todo:
					return {"error": "Todo not found"}
				
				await cursor.execute(
					"UPDATE todo SET name = %s, description = %s WHERE todo_id = %s",
					(name, description, todo_id)
				)
				await conn.commit()
				
		except Exception as e:
			return {"error": str(e)}
		
		finally:
			conn.close()

		return {"message": "Todo updated successfully"}


@app.delete("/delete_todo/{todo_id}")
async def delete_todo(todo_id: int):
		conn = await aiomysql.connect(**MYSQL_CONNECTION_DATA)
		
		try:
			async with conn.cursor() as cursor:
				await cursor.execute("SELECT * FROM todo WHERE todo_id = %s", (todo_id,))
				todo = await cursor.fetchone()
				
				if not todo:
					return {"error": "Todo not found"}
				
				await cursor.execute("DELETE FROM todo WHERE todo_id = %s", (todo_id,))
				await conn.commit()
				
		except Exception as e:
			return {"error": str(e)}
		
		finally:
			conn.close()

		return {"message": "Todo deleted successfully"}


if __name__ == "__main__":
    uvicorn.run("main3:app", reload=True)