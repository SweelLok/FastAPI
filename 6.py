from fastapi import FastAPI

app = FastAPI()

names = []

@app.post("/add-name/{name}")
async def add_name(name: str):
    names.append(name)
    return {"message": f"Ім'я {name} було успішно додано"}

@app.get("/get-names")
async def get_names():
    return {"names": names}