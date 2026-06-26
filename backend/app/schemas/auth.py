from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timezone


class UserRegister(BaseModel):
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str


class UserResponse(BaseModel):
    id: str
    email: str
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}