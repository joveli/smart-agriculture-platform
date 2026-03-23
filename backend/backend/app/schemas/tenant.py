"""
租户 Schema
Tenant Schemas
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime


class TenantCreate(BaseModel):
    name: str
    contact_email: EmailStr
    contact_phone: Optional[str] = None
    plan_type: str = "free"


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    status: Optional[str] = None


class TenantResponse(BaseModel):
    id: UUID
    name: str
    contact_email: str
    contact_phone: Optional[str]
    plan_type: str
    status: str
    storage_quota_gb: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
