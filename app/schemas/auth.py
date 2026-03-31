from __future__ import annotations

from pydantic import BaseModel, EmailStr
from app.models.user import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: UserRole = UserRole.ra


class UserOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    email: str
    role: UserRole
