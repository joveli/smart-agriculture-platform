"""
温室管理 API
Greenhouse Management API
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.greenhouse import Greenhouse
from app.models.farm import Farm
from app.schemas.farm import GreenhouseCreate, GreenhouseUpdate, GreenhouseResponse

router = APIRouter()


@router.get("/", response_model=List[GreenhouseResponse])
async def list_greenhouses(
    farm_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取温室列表"""
    query = select(Greenhouse)
    if current_user.role != "platform_admin":
        query = query.where(Greenhouse.tenant_id == current_user.tenant_id)
    if farm_id:
        query = query.where(Greenhouse.farm_id == farm_id)
    if status:
        query = query.where(Greenhouse.status == status)
    result = await db.execute(query)
    return [GreenhouseResponse.model_validate(g) for g in result.scalars().all()]


@router.post("/", response_model=GreenhouseResponse)
async def create_greenhouse(
    payload: GreenhouseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建温室"""
    # 验证 farm 归属
    farm_result = await db.execute(select(Farm).where(Farm.id == payload.farm_id))
    farm = farm_result.scalar_one_or_none()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    if str(farm.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=403, detail="Farm does not belong to your tenant")

    greenhouse = Greenhouse(
        tenant_id=current_user.tenant_id,
        **payload.model_dump(),
    )
    db.add(greenhouse)
    await db.commit()
    await db.refresh(greenhouse)
    return GreenhouseResponse.model_validate(greenhouse)


@router.get("/{greenhouse_id}", response_model=GreenhouseResponse)
async def get_greenhouse(
    greenhouse_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Greenhouse).where(Greenhouse.id == greenhouse_id)
    if current_user.role != "platform_admin":
        query = query.where(Greenhouse.tenant_id == current_user.tenant_id)
    result = await db.execute(query)
    greenhouse = result.scalar_one_or_none()
    if not greenhouse:
        raise HTTPException(status_code=404, detail="Greenhouse not found")
    return GreenhouseResponse.model_validate(greenhouse)


@router.patch("/{greenhouse_id}", response_model=GreenhouseResponse)
async def update_greenhouse(
    greenhouse_id: UUID,
    payload: GreenhouseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Greenhouse).where(Greenhouse.id == greenhouse_id)
    if current_user.role != "platform_admin":
        query = query.where(Greenhouse.tenant_id == current_user.tenant_id)
    result = await db.execute(query)
    greenhouse = result.scalar_one_or_none()
    if not greenhouse:
        raise HTTPException(status_code=404, detail="Greenhouse not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(greenhouse, field, value)
    await db.commit()
    await db.refresh(greenhouse)
    return GreenhouseResponse.model_validate(greenhouse)


@router.delete("/{greenhouse_id}")
async def delete_greenhouse(
    greenhouse_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Greenhouse).where(Greenhouse.id == greenhouse_id)
    if current_user.role != "platform_admin":
        query = query.where(Greenhouse.tenant_id == current_user.tenant_id)
    result = await db.execute(query)
    greenhouse = result.scalar_one_or_none()
    if not greenhouse:
        raise HTTPException(status_code=404, detail="Greenhouse not found")
    await db.delete(greenhouse)
    await db.commit()
    return {"message": "Greenhouse deleted"}
