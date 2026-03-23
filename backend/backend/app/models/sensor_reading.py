"""
传感器时序数据模型（TimescaleDB 超表）
Sensor Readings - TimescaleDB Hypertable
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class SensorReading(Base):
    """
    传感器时序数据超表
    按月分区，索引: (greenhouse_id, time), (tenant_id, time)
    """
    __tablename__ = "sensor_readings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    greenhouse_id = Column(UUID(as_uuid=True), ForeignKey("greenhouses.id"), nullable=False, index=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False, index=True)
    
    # 时间戳（TimescaleDB 按此分区）
    time = Column(DateTime(timezone=True), nullable=False, index=True, default=datetime.utcnow)
    
    # 传感器指标
    temperature = Column(Numeric(8, 3), nullable=True)      # °C
    humidity = Column(Numeric(8, 3), nullable=True)           # %
    light = Column(Numeric(12, 2), nullable=True)             # lux
    co2 = Column(Numeric(10, 2), nullable=True)               # ppm
    soil_temperature = Column(Numeric(8, 3), nullable=True)   # °C
    soil_humidity = Column(Numeric(8, 3), nullable=True)      # %
    soil_ec = Column(Numeric(10, 4), nullable=True)           # mS/cm
    
    # 元数据
    raw_payload = Column(String(1000), nullable=True)  # 原始 MQTT payload

    __table_args__ = (
        Index("ix_sensor_readings_tenant_time", "tenant_id", "time"),
        Index("ix_sensor_readings_greenhouse_time", "greenhouse_id", "time"),
    )

    def __repr__(self):
        return f"<SensorReading {self.greenhouse_id} @ {self.time}>"
