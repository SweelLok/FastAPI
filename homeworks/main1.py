import uvicorn

from fastapi import FastAPI, HTTPException


app = FastAPI()

names = []


@app.post("/add-name/{name}")
async def add_name(name: str):
    if name in names:
        raise HTTPException(status_code=400, detail="Ім'я вже існує в списку")
    names.append(name)
    return {"message": "Ім'я було успішно додано"}

@app.get("/get-names/")
async def get_names():
    return {"names": names}

@app.post("/delete-name/{name}")
async def delete_name(name: str):
    try:
        names.remove(name)
        return {"message": "Ім'я було успішно видалено"}
    except ValueError:
        raise HTTPException(status_code=404, detail="Ім'я не знайдено в списку")


if __name__ == "__main__":
    uvicorn.run("main1:app", reload=True)