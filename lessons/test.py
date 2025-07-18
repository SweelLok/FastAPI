import aiomysql

from fastapi import FastAPI, HTTPException


async def get_connection_pool():
        conn = await aiomysql.create_pool(
            host="lteproxy.ddns.net",
            port=33060,
            user="root",
            password="root",
            db="examples"
        )

        return conn

async def shutdown():
     pool = await get_connection_pool()
     pool.close()
     await pool.wait_closed()


app = FastAPI(on_shutdown=(shutdown,))


@app.post("/users/{user_name}/{user_email}")
async def create_user(user_name: str, email: str):
    pool = await get_connection_pool()

    async with pool.acquire() as connection:
        async with connection.cursor() as cur:
            await cur.execute("SELECT * FROM users WHERE email=%s", (email,))
            existing_user = await cur.fetchone()

    if existing_user is not None:
        raise HTTPException(
            status_code=400, detail="User with this name already exists."
        )

    async with pool.acquire() as connection:
        async with connection.cursor() as cur:
            await cur.execute(
                "INSERT INTO users (name, email) VALUES (%s, %s);", (user_name, email)
            )
            await connection.commit()

    return {"user_name": user_name}

@app.get("/all_users/")
async def get_all_users():
    pool = await get_connection_pool()

    async with pool.acquire() as connection:
          async with connection.cursor() as cur:
                  await cur.execute("SELECT * FROM users")
                  all_users = await cur.fetchall()
                  return {"all_users": all_users}                                    