"""
认证 Schema
Authentication Schemas
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    tenant_id: Optional[UUID] = None  # null = 平台管理员注册


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    full_name: Optional[str]
    role: str
    tenant_id: Optional[UUID]
    is_active: bool

    class Config:
        from_attributes = True
