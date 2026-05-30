"""WorkFlow — Pydantic schemas for Auth endpoints."""
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.user import Role


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2, max_length=255)
    role: Role = Role.EMPLOYEE
    department: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: "UserProfile"


class UserProfile(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: Role
    department: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


TokenResponse.model_rebuild()
