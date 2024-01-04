import os
from jose import JWTError, jwt
from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.schemas.user_schemas import UserCreateSchema
from app.schemas.token_schemas import TokenDataSchema
from app.database.db import get_db
from app.models.user_model import UserModel
from app.utils.utils import hash_password, is_token_valid

from dotenv import load_dotenv
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

oauth2scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_user_by_email(db: Session, email: str) -> UserModel | None:
    return db.query(UserModel).filter(UserModel.email == email).first()

def get_all_users(db: Session) -> list[UserModel]:
    return db.query(UserModel).filter().all()


def add_user(db:Session, user_data: UserCreateSchema) -> UserCreateSchema:
    hashed_password = hash_password(user_data.password)
    db_user = UserModel(email=user_data.email, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_current_user(token: str=Depends(oauth2scheme), db: Session = Depends(get_db)) -> UserModel:
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not is_token_valid(token):
        raise credential_exception
    
    try: 
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credential_exception
        token_data = TokenDataSchema(email=email)
    except JWTError:
        raise credential_exception
    user = get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credential_exception
    return user



