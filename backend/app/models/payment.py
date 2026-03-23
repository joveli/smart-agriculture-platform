"""支付数据模型"""
from datetime import datetime
from uuid import UUID
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    contract_id = Column(PGUUID(as_uuid=True), ForeignKey("contracts.id"), nullable=True)
    
    order_id = Column(String(50), unique=True, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="CNY")
    
    payment_method = Column(String(20), default="alipay")
    status = Column(String(20), default="pending")
    transaction_id = Column(String(100), nullable=True)
    
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant = relationship("Tenant", back_populates="payments")
    contract = relationship("Contract", back_populates="payments")
