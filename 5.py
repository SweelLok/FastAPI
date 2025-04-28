import uvicorn
from fastapi import FastAPI
import asyncio

app = FastAPI()

@app.get("/async-endpoint")
async def read_items():
    await asyncio.sleep(1)
    return {"message": "Асинхронна відповідь після 1 секунди очікування"}


if "__main__" == __name__:
    uvicorn.run("5:app",reload=True)