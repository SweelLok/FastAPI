from fastapi import FastAPI
import httpx
import asyncio


app = FastAPI()


async def httpx_example(id):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://jsonplaceholder.typicode.com/posts/{id}")

    return response.json()


@app.get("/")
async def test():
    result = await httpx_example(1)
    return f"{result}"


@app.get("/{id}/")
async def by_id(id):
    result = await httpx_example(id)
    return f"{result}"


@app.get("/multiple-users/")
async def multiple_users():
    async with httpx.AsyncClient() as client:
        responses = await asyncio.gather(
            client.get("https://jsonplaceholder.typicode.com/posts/1"),
            client.get("https://jsonplaceholder.typicode.com/posts/2"),
            client.get("https://jsonplaceholder.typicode.com/posts/3"),
        )
    return [post.json() for post in responses]
