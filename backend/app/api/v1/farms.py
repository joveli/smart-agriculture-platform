"""
农场管理模块
Farm Management Module
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

router = APIRouter()


class FarmBase(BaseModel):
    name: str
    area: float
    location: str = ""


class FarmCreate(FarmBase):
    tenant_id: str


class FarmResponse(FarmBase):
    id: str
    tenant_id: str

    class Config:
        from_attributes = True


@router.get("/", response_model=List[FarmResponse])
async def list_farms(tenant_id: str):
    """获取农场列表"""
    # TODO: 实现农场列表查询
    return []


@router.post("/", response_model=FarmResponse)
async def create_farm(farm: FarmCreate):
    """创建农场"""
    # TODO: 实现农场创建
    return {"id": "mock_id", **farm.model_dump()}


@router.get("/{farm_id}", response_model=FarmResponse)
async def get_farm(farm_id: str):
    """获取农场详情"""
    # TODO: 实现农场详情查询
    return {"id": farm_id, "name": "Mock Farm", "area": 1000.0, "tenant_id": "mock_tenant"}
