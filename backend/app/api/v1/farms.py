"""
农场管理 API
Farm Management API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.farm import Farm
from app.schemas.farm import FarmCreate, FarmUpdate, FarmResponse

router = APIRouter()


@router.get("/", response_model=List[FarmResponse])
async def list_farms(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取农场列表（自动按租户隔离）"""
    query = select(Farm)
    if current_user.role != "platform_admin":
        query = query.where(Farm.tenant_id == current_user.tenant_id)
    result = await db.execute(query)
    farms = result.scalars().all()
    return [FarmResponse.model_validate(f) for f in farms]


@router.post("/", response_model=FarmResponse)
async def create_farm(
    payload: FarmCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建农场"""
    farm = Farm(
        tenant_id=current_user.tenant_id,
        **payload.model_dump(),
    )
    db.add(farm)
    await db.commit()
    await db.refresh(farm)
    return FarmResponse.model_validate(farm)


@router.get("/{farm_id}", response_model=FarmResponse)
async def get_farm(
    farm_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取农场详情"""
    query = select(Farm).where(Farm.id == farm_id)
    if current_user.role != "platform_admin":
        query = query.where(Farm.tenant_id == current_user.tenant_id)
    result = await db.execute(query)
    farm = result.scalar_one_or_none()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return FarmResponse.model_validate(farm)


@router.patch("/{farm_id}", response_model=FarmResponse)
async def update_farm(
    farm_id: UUID,
    payload: FarmUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新农场"""
    query = select(Farm).where(Farm.id == farm_id)
    if current_user.role != "platform_admin":
        query = query.where(Farm.tenant_id == current_user.tenant_id)
    result = await db.execute(query)
    farm = result.scalar_one_or_none()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(farm, field, value)
    await db.commit()
    await db.refresh(farm)
    return FarmResponse.model_validate(farm)


@router.delete("/{farm_id}")
async def delete_farm(
    farm_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除农场"""
    query = select(Farm).where(Farm.id == farm_id)
    if current_user.role != "platform_admin":
        query = query.where(Farm.tenant_id == current_user.tenant_id)
    result = await db.execute(query)
    farm = result.scalar_one_or_none()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    await db.delete(farm)
    await db.commit()
    return {"message": "Farm deleted"}
