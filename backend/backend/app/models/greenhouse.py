"""
温室模型
Greenhouse Model
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Greenhouse(Base):
    __tablename__ = "greenhouses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    farm_id = Column(UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    crop_id = Column(UUID(as_uuid=True), ForeignKey("crops.id"), nullable=True)
    area_sqm = Column(Numeric(10, 2), nullable=True)  # 面积（平方米）
    location = Column(String(500), nullable=True)
    status = Column(String(20), default="active")  # active, inactive, maintenance
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    farm = relationship("Farm", back_populates="greenhouses")
    crop = relationship("Crop", backref="greenhouses")
    devices = relationship("Device", back_populates="greenhouse", lazy="selectin")
    sensor_readings = relationship("SensorReading", back_populates="greenhouse", lazy="selectin")

    def __repr__(self):
        return f"<Greenhouse {self.name} ({self.id})>"
