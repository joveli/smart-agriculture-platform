"""合同数据模型"""
from datetime import datetime, date
from uuid import UUID
from sqlalchemy import Column, String, Date, DateTime, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Contract(Base):
    __tablename__ = "contracts"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    name = Column(String(200), nullable=False)
    contract_type = Column(String(20), nullable=False, default="service")
    amount = Column(Numeric(12, 2), nullable=False, default=0)
    currency = Column(String(3), default="CNY")
    
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    status = Column(String(20), default="draft")
    file_url = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant = relationship("Tenant", back_populates="contracts")
    payments = relationship("Payment", back_populates="contract")
