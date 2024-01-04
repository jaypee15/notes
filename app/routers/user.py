import os
from datetime import timedelta

from fastapi import APIRouter, HTTPException, status
from fastapi.params import Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from starlette.status import HTTP_401_UNAUTHORIZED

from app.crud import user_crud
from app.database.db import get_db
from app.models.user_model import UserModel
from app.schemas.token_schemas import TokenSchema
from app.schemas.user_schemas import (
    UserBaseSchema,
    UserOutSchema,
    UserCreateSchema,
    UserWithTokenSchema,
)
from app.utils.utils import (
    authenticate_user,
    create_access_token,
    invalidate_access_token,
)

from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=list[UserBaseSchema], summary="Get all users")
def get_users(db: Session = Depends(get_db)):
    """
    Returns a list of all users
    """
    users = user_crud.get_all_users(db)
    return list(users)

@router.get(
    "/me", response_model=UserOutSchema, summary="get the currently logged in user"
)
def get_current_user(user_data: UserModel = Depends(user_crud.get_current_user)):
    """
    This endpoints exposes the currently authenticated user
    """

    if user_data is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )
    return user_data


@router.get("/{email}", response_model=UserOutSchema, summary="Get user by email")
def get_user(email: str, db: Session = Depends(get_db), current_user: UserModel=Depends(user_crud.get_current_user)):
    """ "
    Return a user by passing email as a URL parameter
    Returns a 404 if email does not exist in database
    """
    user = user_crud.get_user_by_email(db, email)
    if user:
        return user
    else:
        raise HTTPException(status_code=404, detail=f"No User with email: {email}")


@router.post("/", response_model=UserWithTokenSchema, summary="Signup as a new user")
def sign_up(user_data: UserCreateSchema, db: Session = Depends(get_db)):
    """
    Create a new user with the following information:

    - **email**: each user must have a unique email
    - **password**: strong password

    """
    user = user_crud.get_user_by_email(db, user_data.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="email exists",
        )
    new_user = user_crud.add_user(db, user_data)

    token_expires_date = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # Generate an access token for the new user
    access_token = create_access_token(
        data={"sub": new_user.email},
        expires_delta=token_expires_date,
    )
    response = {
        "email": new_user.email,
        "access_token": access_token,
        "token_type": "bearer",
    }
    return response


@router.post(
    "/login", response_model=TokenSchema, summary="Login using email and password"
)
def login_for_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Login/Signin with the following information:

    - **email**: This is required
    - **password**: This is required

    **NB** : username is treated as email
    """
    user_data = authenticate_user(db, form_data.username, form_data.password)
    if not user_data:
        raise HTTPException(
            HTTP_401_UNAUTHORIZED,
            detail="invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token_expires_date = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_data.email},
        expires_delta=token_expires_date,
    )
    return {"access_token": access_token, "token_type": "bearer"}




@router.post("/logout", summary="Logout and invalidate the access token")
def logout(
    current_user: UserModel = Depends(user_crud.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Log out the currently authenticated user and invalidate the access token.
    """

    # Invalidate the access token
    invalidate_access_token(current_user.email, db)

    return {"message": "Logout successful"}
