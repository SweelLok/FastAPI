from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime


app = FastAPI()


class CustomMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        method = request.method
        url = request.url.path
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {method} {url}")

        if "X-Custom-Header" not in request.headers:
            return JSONResponse(
                status_code=400,
                content={"detail": "Missing X-Custom-Header"},
            )

        response = await call_next(request)
        return response


app.add_middleware(CustomMiddleware)


@app.get("/hello/")
async def say_hello():
    return {"message": "Hello world!"}


@app.get("/ping/")
async def ping():
    return {"message": "Pong!"}


@app.post("/echo/")
async def echo(data: dict):
    return {"you_sent": data}