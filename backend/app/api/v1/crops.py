"""
作物管理模块
Crop Management Module
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

router = APIRouter()


class CropBase(BaseModel):
    name: str
    variety: str = ""
    growth_cycle_days: int = 0


class CropCreate(CropBase):
    pass


class CropResponse(CropBase):
    id: str

    class Config:
        from_attributes = True


@router.get("/", response_model=List[CropResponse])
async def list_crops():
    """获取作物列表"""
    # TODO: 实现作物列表查询
    return []


@router.post("/", response_model=CropResponse)
async def create_crop(crop: CropCreate):
    """创建作物"""
    # TODO: 实现作物创建
    return {"id": "mock_id", **crop.model_dump()}
