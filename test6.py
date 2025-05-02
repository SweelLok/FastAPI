import aiosqlite
from fastapi import FastAPI, Query, Request, Path, HTTPException


DATABASE_URL = "./mydb.db"


async def init_dabase():
	async with aiosqlite.connect(DATABASE_URL) as connection:
		cursor = await connection.cursor()
		await cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name VARCHAR(50) NOT NULL,
                phone VARCHAR(50) NOT NULL,
                email VARCHAR(50) NOT NULL,
                age INTEGER NOT NULL
							)
						""");


app = FastAPI(title="Users API", on_startup=(init_dabase,))


@app.get("users")
async def get_users(request: Request, 
										skip: int = Query(
											0, title="Scip", description="Amount of query to skip"
											), 
										limit: int = Query(
											100, title="Limit", description="Maximum amount records to return"
											)):
	print(f"Parameters query:{request.query_params}")

	async with aiosqlite.connect(DATABASE_URL) as connection:
		connection.row_factory = aiosqlite.Row
		cursor = await connection.cursor()
		await cursor.execute("SELECT * FROM users LIMIT ? OFFSET ?", (limit, skip))
		users = await cursor.fetchall()

	return users


@app.get("/users/search")
async def search_users(request: Request, 
												name: str = Query(
													None, title="Name", description="Name of the user to search"
													), 
												age: int = Query(
													None, lt=101,gt=29,title="Age", description="Age of the user to search"
													)):
	print(f"Parameters query:{request.query_params}")

	async with aiosqlite.connect(DATABASE_URL) as connection:
		connection.row_factory = aiosqlite.Row
		cursor = await connection.cursor()

		if age is not None and name is not None:
			await cursor.execute("SELECT * FROM users WHERE name LIKE ? AND age = ?;", (f"%{name}%", age))
		else:
			await cursor.execute("SELECT * FROM users WHERE name LIKE ?;", (f"%{name}%",))

		users = await cursor.fetchall()
	
	return users


@app.get("/users/{user_id}")
async def get_user(request: Request, user_id: int = Path(gt=0, description="ID of the user")):
	print(f"Parameters query:{request.query_params}")

	async with aiosqlite.connect(DATABASE_URL) as connection:
		connection.row_factory = aiosqlite.Row
		cursor = await connection.cursor()
		await cursor.execute("SELECT * FROM users WHERE id = ?;", (user_id,))
		user = await cursor.fetchone()

		if user is None:
			raise HTTPException(404, "User does not exist.")
		
	return user