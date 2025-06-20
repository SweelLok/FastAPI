from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel, Field, SecretStr
from typing import List
from fastapi.security import (
    HTTPBasic,
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
)
import base64


app = FastAPI()
security = HTTPBasic()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Token(BaseModel):
    """Модель токена доступу."""

    token_type: str = Field(description="type of the token", examples=["bearer"])
    access_token: str = Field(description="Token Value", examples=["YmasdeQ=="])

class Hobby(BaseModel):
		name: str = Field(..., description="Name of the hobby", examples=["Reading", "Traveling", "Cooking"])

class User(BaseModel):
		name: str = Field(..., description="Name of the person", examples=["John Doe", "Jane Smith"])
		year: int = Field(..., description="Year of birth", examples=[1990, 1985])
		hobbies: List[Hobby] = Field(..., description="List of hobbies of the person", examples=[{"name": "Reading"}, {"name": "Traveling"}])
		password: SecretStr = Field(..., description="Password for the user", min_length=8, examples=["strongpassword123", "anotherpassword456"])


users = []


@app.post(
    "/token",
    response_model=Token,
    tags=["auth"],
    summary="Get access token by provided name and password",
    description="Endpoint for auth purpose",
    responses={
        200: {"description": "Success"},
        404: {"description": "User not found"},
        400: {"description": "Incorrect password provided"},
    },
    operation_id="get-access-token",
    include_in_schema=True,
    name="get token"
)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    for i in users:
        if i.name == form_data.username:
            db_user = i

            if db_user.password.get_secret_value() != form_data.password:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Incorrect password.")

            return Token(
                access_token=base64.urlsafe_b64encode(f"{db_user.name}".encode("utf-8")).decode("utf-8"),
                token_type="bearer",
            )

    raise HTTPException(status.HTTP_404_NOT_FOUND, "User does not exist.")

@app.post("/users/", 
		response_model=User,
    tags=["Users"],
    summary="Create a new user",
    description="Creates a new user with name, year of birth, and hobbies.",
    responses={200: {"description": "User created successfully"}},
    include_in_schema=True
)
async def create_user(user: User):
		"""
		Create a new user with name, year of birth, and hobbies.
		"""
		users.append(user)
		return user

@app.get("/users/",
		response_model=List[User],
    tags=["Users"],
    summary="Get users",
    description="Get all users in the system.",
    responses={200: {"description": "Users retrieved successfully"}},
    include_in_schema=True
)
async def get_users(token: str = Depends(oauth2_scheme)):
		"""
		Get the list of all users.
		"""
		return users

@app.put("/users/{name}",
		response_model=User,
    tags=["Users"],
    summary="Update a user",
    description="Updates a user's information by name.",
    responses={200: {"description": "User updated successfully"}},
    include_in_schema=True
)
async def update_user(name: str, user: User):
		"""
		Update a user's information by name.
		"""
		for i, existing_user in enumerate(users):
				if existing_user.name == name:
						users[i] = user
						return user
		raise HTTPException(status_code=404, detail="User not found")

@app.delete("/users/{name}",
		response_model=User,
    tags=["Users"],
    summary="Delete a user",
    description="Deletes a user by name.",
    responses={200: {"description": "Deleted user successfully"}},
    include_in_schema=True	
)
async def delete_user(name: str):
		"""
		Delete a user by name.
		"""
		for i, user in enumerate(users):
				if user.name == name:
						return users.pop(i)
		raise HTTPException(status_code=404, detail="User not found")