import os

from fastapi.security import OAuth2PasswordBearer

DB_NAME = "ads.db"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
