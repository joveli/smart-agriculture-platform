"""合同管理 API"""
from typing import Optional
import uuid
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.contract import Contract
from app.schemas.contract import ContractCreate, ContractUpdate, ContractResponse


router = APIRouter()


@router.get("/", response_model=list[ContractResponse])
async def list_contracts(
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Contract).where(Contract.tenant_id == current_user.tenant_id)
    if status_filter:
        query = query.where(Contract.status == status_filter)
    query = query.offset(skip).limit(limit).order_by(Contract.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{contract_id}", response_model=ContractResponse)
async def get_contract(
    contract_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Contract).where(Contract.id == contract_id, Contract.tenant_id == current_user.tenant_id)
    )
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")
    return contract


@router.post("/", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
async def create_contract(
    contract_data: ContractCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contract = Contract(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        status="draft",
        **contract_data.model_dump()
    )
    db.add(contract)
    await db.commit()
    await db.refresh(contract)
    return contract


@router.patch("/{contract_id}", response_model=ContractResponse)
async def update_contract(
    contract_id: UUID,
    contract_data: ContractUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Contract).where(Contract.id == contract_id, Contract.tenant_id == current_user.tenant_id)
    )
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")
    for key, value in contract_data.model_dump(exclude_unset=True).items():
        setattr(contract, key, value)
    await db.commit()
    await db.refresh(contract)
    return contract


@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contract(
    contract_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Contract).where(Contract.id == contract_id, Contract.tenant_id == current_user.tenant_id)
    )
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")
    await db.delete(contract)
    await db.commit()
