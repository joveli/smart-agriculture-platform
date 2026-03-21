"""
作物管理 API
Crop Management API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.crop import Crop

router = APIRouter()


@router.get("/")
async def list_crops(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取作物列表"""
    result = await db.execute(select(Crop).order_by(Crop.name))
    crops = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "variety": c.variety,
            "growth_cycle_days": c.growth_cycle_days,
        }
        for c in crops
    ]
