from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from typing import Optional
from pydantic import BaseModel


app = FastAPI()

security = HTTPBasic()


@app.get("/basic-auth/")
def basic_auth(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = "admin"
    correct_password = "1234"

    if credentials.username != correct_username or credentials.password != correct_password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"message": f"Hello, {credentials.username}!"}


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

fake_users = {
    "user1": {
        "username": "user1",
        "password": "pass1",
        "token": "token123"
    }
}


@app.post("/token/")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users.get(form_data.username)
    if not user or user["password"] != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    return {"access_token": user["token"], "token_type": "bearer"}


@app.get("/protected-oauth2/")
def protected_route(token: str = Depends(oauth2_scheme)):
    for user in fake_users.values():
        if user["token"] == token:
            return {"message": f"Welcome, {user['username']}!"}
    raise HTTPException(status_code=401, detail="Invalid token")