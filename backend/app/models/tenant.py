"""
租户模型
Tenant Model
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import enum


class TenantStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"
    DELETED = "deleted"


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=False, unique=True)
    contact_phone = Column(String(50), nullable=True)
    plan_type = Column(String(50), default="free")
    status = Column(String(20), default=TenantStatus.PENDING.value)
    storage_quota_gb = Column(String(20), default="1")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    users = relationship("User", back_populates="tenant")
    farms = relationship("Farm", back_populates="tenant")
    devices = relationship("Device", back_populates="tenant")
    contracts = relationship("Contract", back_populates="tenant")
    payments = relationship("Payment", back_populates="tenant")

    def __repr__(self):
        return f"<Tenant {self.name} ({self.id})>"
