"""支付 Schema"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class PaymentCreate(BaseModel):
    contract_id: Optional[UUID] = None
    amount: float = Field(..., gt=0)
    currency: str = Field(default="CNY", max_length=3)
    payment_method: str = Field(default="alipay")


class PaymentCallback(BaseModel):
    transaction_id: str
    status: str


class PaymentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    contract_id: Optional[UUID] = None
    order_id: str
    amount: float
    currency: str
    payment_method: str
    status: str
    transaction_id: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentStats(BaseModel):
    total_income: float
    pending_amount: float
    completed_amount: float
    refunded_amount: float
