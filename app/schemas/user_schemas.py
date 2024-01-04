from pydantic import BaseModel, EmailStr
from datetime import datetime

from app.schemas.token_schemas import TokenSchema


class UserBaseSchema(BaseModel):
    email: EmailStr


class UserOutSchema(UserBaseSchema):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserCreateSchema(UserBaseSchema):
    password: str


class UserWithTokenSchema(UserBaseSchema, TokenSchema):
    class Config:
        from_attributes = True
