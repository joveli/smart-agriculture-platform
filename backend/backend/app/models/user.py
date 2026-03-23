"""
用户模型
User Model
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class UserRole(str, enum.Enum):
    PLATFORM_ADMIN = "platform_admin"
    TENANT_ADMIN = "tenant_admin"
    AGRONOMIST = "agronomist"
    OPERATOR = "operator"
    FARMER = "farmer"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)  # null for platform admin
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), nullable=False, default=UserRole.FARMER.value)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)

    tenant = relationship("Tenant", backref="users")

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"
