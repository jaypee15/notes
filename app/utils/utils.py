import os
from datetime import timedelta, datetime
from typing import Set

from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.services import user_services
from app.models.user_model import UserModel
from app.database.db import get_db

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
INVALIDATED_TOKENS: Set[str] = set()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def invalidate_access_token(email: str, db: Session = Depends(get_db)):
    """
    Invalidate the access token for a user by adding it to the set of invalidated tokens.
    """
    user = user_services.get_user_by_email(db, email)
    if user:
        token_data = {"sub": user.email}
        access_token = create_access_token(data=token_data)
        INVALIDATED_TOKENS.add(access_token)


def authenticate_user(db: Session, email: str, password: str) -> bool | UserModel:
    user: UserModel = user_services.get_user_by_email(db, email)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expires = datetime.utcnow() + expires_delta
    else:
        expires = datetime.utcnow() + timedelta(ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expires})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def is_token_valid(token: str):
    """
    Check if a token is valid by verifying it and ensuring it is not in the set of invalidated tokens.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload["sub"] in INVALIDATED_TOKENS:
            return False
        return True
    except JWTError:
        return False
