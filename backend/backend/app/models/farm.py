"""
农场模型
Farm Model
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Farm(Base):
    __tablename__ = "farms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    location = Column(String(500), nullable=True)
    latitude = Column(Numeric(10, 7), nullable=True)
    longitude = Column(Numeric(10, 7), nullable=True)
    description = Column(Text, nullable=True)
    area_mu = Column(Numeric(10, 2), nullable=True)  # 面积（亩）
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    greenhouses = relationship("Greenhouse", back_populates="farm", lazy="selectin")

    def __repr__(self):
        return f"<Farm {self.name} ({self.id})>"
