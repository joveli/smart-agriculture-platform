"""
农场/温室/设备 Schema
Farm, Greenhouse, Device Schemas
"""

from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


# ============ Farm ============
class FarmCreate(BaseModel):
    name: str
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None
    area_mu: Optional[float] = None


class FarmUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    area_mu: Optional[float] = None


class FarmResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    location: Optional[str]
    area_mu: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Greenhouse ============
class GreenhouseCreate(BaseModel):
    farm_id: UUID
    name: str
    crop_id: Optional[UUID] = None
    area_sqm: Optional[float] = None
    location: Optional[str] = None
    status: str = "active"
    description: Optional[str] = None


class GreenhouseUpdate(BaseModel):
    name: Optional[str] = None
    crop_id: Optional[UUID] = None
    area_sqm: Optional[float] = None
    status: Optional[str] = None
    description: Optional[str] = None


class GreenhouseResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    farm_id: UUID
    name: str
    crop_id: Optional[UUID]
    area_sqm: Optional[float]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Device ============
class DeviceCreate(BaseModel):
    greenhouse_id: UUID
    name: str
    device_type: str
    model: Optional[str] = None
    sn: Optional[str] = None
    manufacturer: Optional[str] = None
    mqtt_topic: Optional[str] = None
    sampling_interval_sec: int = 60


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    model: Optional[str] = None
    status: Optional[str] = None
    mqtt_topic: Optional[str] = None
    sampling_interval_sec: Optional[int] = None


class DeviceResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    greenhouse_id: UUID
    name: str
    device_type: str
    model: Optional[str]
    sn: Optional[str]
    status: str
    is_active: bool
    last_seen_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class DeviceCommand(BaseModel):
    command: str
    params: Optional[dict] = None
