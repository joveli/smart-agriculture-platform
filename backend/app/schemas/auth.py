"""
认证 Schema
Authentication Schemas
"""

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from uuid import UUID


class UserRegisterRequest(BaseModel):
    """用户注册请求（含租户创建）"""
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    tenant_name: str = ""

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("密码至少 8 个字符")
        if not any(c.isalpha() for c in v):
            raise ValueError("密码必须包含字母")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含数字")
        return v

    @field_validator("username")
    @classmethod
    def username_length(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError("用户名至少 3 个字符")
        if not v.isalnum():
            raise ValueError("用户名只能包含字母和数字")
        return v


class UserRegister(BaseModel):
    """用户注册（内部使用，非 API）"""
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    tenant_id: Optional[UUID] = None


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenRefreshRequest(BaseModel):
    token: str


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
