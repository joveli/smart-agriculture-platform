"""
设备模型
Device Model
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Numeric, Integer, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class DeviceType(str, enum.Enum):
    SENSOR = "sensor"
    ACTUATOR = "actuator"
    GATEWAY = "gateway"
    CAMERA = "camera"


class DeviceStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    FAULT = "fault"


class Device(Base):
    __tablename__ = "devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    greenhouse_id = Column(UUID(as_uuid=True), ForeignKey("greenhouses.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    device_type = Column(String(50), nullable=False, default=DeviceType.SENSOR.value)
    model = Column(String(255), nullable=True)
    sn = Column(String(255), nullable=True, unique=True)
    manufacturer = Column(String(255), nullable=True)
    status = Column(String(20), default=DeviceStatus.OFFLINE.value)
    mqtt_topic = Column(String(500), nullable=True)
    config_json = Column(Text, nullable=True)
    calibration_offset = Column(Numeric(10, 4), nullable=True)
    sampling_interval_sec = Column(Integer, default=60)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_seen_at = Column(DateTime, nullable=True)

    greenhouse = relationship("Greenhouse", back_populates="devices")

    def __repr__(self):
        return f"<Device {self.name} ({self.device_type})>"
