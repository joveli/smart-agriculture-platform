"""合同 Schema"""
from datetime import date, datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ContractCreate(BaseModel):
    name: str = Field(..., max_length=200)
    contract_type: str = Field(default="service")
    amount: float = Field(..., ge=0)
    currency: str = Field(default="CNY", max_length=3)
    start_date: date
    end_date: date
    file_url: Optional[str] = Field(None, max_length=500)


class ContractUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    contract_type: Optional[str] = None
    amount: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None
    file_url: Optional[str] = Field(None, max_length=500)


class ContractResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    contract_type: str
    amount: float
    currency: str
    start_date: date
    end_date: date
    status: str
    file_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
