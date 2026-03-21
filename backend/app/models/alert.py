"""
告警模型
Alert Models
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Boolean, Integer, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class AlertLevel(str, enum.Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class AlertStatus(str, enum.Enum):
    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class AlertRule(Base):
    """告警规则"""
    __tablename__ = "alert_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    greenhouse_id = Column(UUID(as_uuid=True), ForeignKey("greenhouses.id"), nullable=True)  # null = 全温室
    name = Column(String(255), nullable=False)
    metric = Column(String(50), nullable=False)  # temperature, humidity, light, co2, ...
    operator = Column(String(10), nullable=False)  # gt, lt, gte, lte, eq
    threshold = Column(String(50), nullable=False)
    level = Column(String(20), nullable=False, default=AlertLevel.WARNING.value)
    enabled = Column(Boolean, default=True)
    notification_channels = Column(JSON, nullable=True)  # ["websocket", "dingtalk", "feishu"]
    cooldown_minutes = Column(Integer, default=5)  # 告警收敛：同类告警间隔（分钟）
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<AlertRule {self.name} ({self.metric} {self.operator} {self.threshold})>"


class Alert(Base):
    """告警记录"""
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    greenhouse_id = Column(UUID(as_uuid=True), ForeignKey("greenhouses.id"), nullable=False, index=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=True)
    rule_id = Column(UUID(as_uuid=True), ForeignKey("alert_rules.id"), nullable=True)
    
    alert_type = Column(String(50), nullable=False)  # 告警类型：temperature, humidity...
    level = Column(String(20), nullable=False, default=AlertLevel.WARNING.value)
    message = Column(Text, nullable=False)
    metric_value = Column(String(50), nullable=True)  # 触发时的指标值
    threshold_value = Column(String(50), nullable=True)  # 阈值
    status = Column(String(20), default=AlertStatus.PENDING.value)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    notification_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    greenhouse = relationship("Greenhouse", backref="alerts")
    device = relationship("Device", backref="alerts")

    def __repr__(self):
        return f"<Alert {self.alert_type} ({self.level}) - {self.status}>"
