"""支付管理 API"""
from datetime import datetime
from typing import Optional
from uuid import UUID
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.payment import Payment
from app.schemas.payment import PaymentCreate, PaymentCallback, PaymentResponse, PaymentStats


router = APIRouter()


def generate_order_id() -> str:
    return f"PAY{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"


@router.get("/", response_model=list[PaymentResponse])
async def list_payments(
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Payment).where(Payment.tenant_id == current_user.tenant_id)
    if status_filter:
        query = query.where(Payment.status == status_filter)
    query = query.offset(skip).limit(limit).order_by(Payment.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/stats", response_model=PaymentStats)
async def get_payment_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0))
        .where(Payment.tenant_id == current_user.tenant_id, Payment.status == "completed")
    )
    completed = float(result.scalar() or 0)
    
    result = await db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0))
        .where(Payment.tenant_id == current_user.tenant_id, Payment.status == "pending")
    )
    pending = float(result.scalar() or 0)
    
    result = await db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0))
        .where(Payment.tenant_id == current_user.tenant_id, Payment.status == "refunded")
    )
    refunded = float(result.scalar() or 0)
    
    return PaymentStats(total_income=completed, pending_amount=pending, completed_amount=completed, refunded_amount=refunded)


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Payment).where(Payment.id == payment_id, Payment.tenant_id == current_user.tenant_id)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="支付记录不存在")
    return payment


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_data: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payment = Payment(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        order_id=generate_order_id(),
        status="pending",
        **payment_data.model_dump()
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


@router.post("/{payment_id}/callback", response_model=PaymentResponse)
async def payment_callback(
    payment_id: UUID,
    callback_data: PaymentCallback,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Payment).where(Payment.id == payment_id, Payment.tenant_id == current_user.tenant_id)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="支付记录不存在")
    payment.transaction_id = callback_data.transaction_id
    payment.status = callback_data.status
    if callback_data.status == "completed":
        payment.paid_at = datetime.utcnow()
    await db.commit()
    await db.refresh(payment)
    return payment


@router.post("/{payment_id}/complete", response_model=PaymentResponse)
async def complete_payment(
    payment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Payment).where(Payment.id == payment_id, Payment.tenant_id == current_user.tenant_id)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="支付记录不存在")
    payment.status = "completed"
    payment.paid_at = datetime.utcnow()
    payment.transaction_id = f"TXN{uuid.uuid4().hex[:16].upper()}"
    await db.commit()
    await db.refresh(payment)
    return payment
