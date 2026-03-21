"""
计量计费 Schema
Billing & Usage Schemas
"""

from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class PlanResponse(BaseModel):
    id: UUID
    name: str
    display_name: str
    price_monthly: float
    device_limit: int
    data_point_limit: int
    api_call_limit: int
    alert_limit: int
    storage_gb_limit: float
    user_limit: int

    class Config:
        from_attributes = True


class UsageRecordResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    resource_type: str
    period_month: str
    usage_value: float
    overage_value: float
    overage_cost: float

    class Config:
        from_attributes = True


class TenantUsageResponse(BaseModel):
    tenant_id: UUID
    period_month: str
    records: List[UsageRecordResponse]
