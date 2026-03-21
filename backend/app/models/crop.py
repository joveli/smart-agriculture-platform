"""
作物模型
Crop Model
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class Crop(Base):
    __tablename__ = "crops"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    variety = Column(String(255), nullable=True)
    growth_cycle_days = Column(Integer, nullable=True)  # 生长周期（天）
    optimal_temp_min = Column(Numeric(5, 2), nullable=True)  # 最佳温度下限（°C）
    optimal_temp_max = Column(Numeric(5, 2), nullable=True)  # 最佳温度上限（°C）
    optimal_humidity_min = Column(Numeric(5, 2), nullable=True)  # 最佳湿度下限（%）
    optimal_humidity_max = Column(Numeric(5, 2), nullable=True)  # 最佳湿度上限（%）
    optimal_light_min = Column(Numeric(10, 2), nullable=True)  # 最佳光照下限（lux）
    optimal_light_max = Column(Numeric(10, 2), nullable=True)  # 最佳光照上限（lux）
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Crop {self.name} ({self.variety})>"
