import os
import secrets
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

# --- Configuration ---
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-please")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# OAuth2 scheme for dependency injection
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- Password Utilities ---
def hash_password(pw: str):
    return pwd_context.hash(pw)


def verify_password(pw: str, hashed: str):
    return pwd_context.verify(pw, hashed)


# --- JWT Logic ---
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token: No user ID")
            
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token: Signature mismatch")


# --- API Key Logic ---
def generate_api_key():
    return secrets.token_urlsafe(32)
