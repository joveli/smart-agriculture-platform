"""
计量计费模型
Billing & Usage Metering Models
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Boolean, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Plan(Base):
    """套餐定义"""
    __tablename__ = "plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(255), nullable=False)
    price_monthly = Column(Numeric(10, 2), default=0)
    price_yearly = Column(Numeric(10, 2), nullable=True)
    device_limit = Column(Integer, nullable=False, default=5)
    data_point_limit = Column(Integer, nullable=False, default=100000)
    api_call_limit = Column(Integer, nullable=False, default=10000)
    alert_limit = Column(Integer, nullable=False, default=50)
    storage_gb_limit = Column(Numeric(10, 2), nullable=False, default=1)
    user_limit = Column(Integer, nullable=False, default=3)
    device_overage = Column(Numeric(10, 2), default=20)
    data_point_overage = Column(Numeric(10, 4), default=0.00005)
    api_call_overage = Column(Numeric(10, 5), default=0.0001)
    alert_overage = Column(Numeric(10, 4), default=0.01)
    storage_overage = Column(Numeric(10, 2), default=2)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Plan {self.name}>"


class TenantPlan(Base):
    """租户当前套餐"""
    __tablename__ = "tenant_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, unique=True, index=True)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    is_trial = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    plan = relationship("Plan")

    def __repr__(self):
        return f"<TenantPlan tenant={self.tenant_id} plan={self.plan_id}>"


class UsageRecord(Base):
    """资源使用量记录（月度聚合）"""
    __tablename__ = "usage_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False)
    period_month = Column(String(7), nullable=False, index=True)
    usage_value = Column(Numeric(20, 4), nullable=False, default=0)
    overage_value = Column(Numeric(20, 4), nullable=False, default=0)
    overage_cost = Column(Numeric(10, 2), nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_usage_tenant_resource_month", "tenant_id", "resource_type", "period_month", unique=True),
    )

    def __repr__(self):
        return f"<UsageRecord {self.tenant_id} {self.resource_type} {self.period_month}>"
