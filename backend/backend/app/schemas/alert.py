"""
告警 Schema
Alert Schemas
"""

from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class AlertRuleCreate(BaseModel):
    greenhouse_id: Optional[UUID] = None
    name: str
    metric: str  # temperature, humidity, light, co2...
    operator: str  # gt, lt, gte, lte
    threshold: float
    level: str = "warning"  # critical, warning, info
    notification_channels: Optional[List[str]] = ["websocket"]
    cooldown_minutes: int = 5


class AlertRuleUpdate(BaseModel):
    name: Optional[str] = None
    metric: Optional[str] = None
    operator: Optional[str] = None
    threshold: Optional[float] = None
    level: Optional[str] = None
    enabled: Optional[bool] = None
    notification_channels: Optional[List[str]] = None
    cooldown_minutes: Optional[int] = None


class AlertRuleResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    greenhouse_id: Optional[UUID]
    name: str
    metric: str
    operator: str
    threshold: float
    level: str
    enabled: bool
    notification_channels: Optional[List[str]]
    cooldown_minutes: int
    created_at: datetime

    class Config:
        from_attributes = True


class AlertResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    greenhouse_id: UUID
    device_id: Optional[UUID]
    alert_type: str
    level: str
    message: str
    metric_value: Optional[str]
    status: str
    resolved_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class AlertAcknowledge(BaseModel):
    note: Optional[str] = None
