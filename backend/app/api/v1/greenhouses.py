"""
温室管理模块
Greenhouse Management Module
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()


class GreenhouseBase(BaseModel):
    name: str
    area: float
    type: str = "standard"
    status: str = "active"


class GreenhouseCreate(GreenhouseBase):
    farm_id: str


class GreenhouseResponse(GreenhouseBase):
    id: str
    farm_id: str

    class Config:
        from_attributes = True


class SensorData(BaseModel):
    temperature: float
    humidity: float
    light_intensity: float
    co2: float
    soil_moisture: float
    soil_temperature: float


@router.get("/", response_model=List[GreenhouseResponse])
async def list_greenhouses(farm_id: str):
    """获取温室列表"""
    # TODO: 实现温室列表查询
    return []


@router.post("/", response_model=GreenhouseResponse)
async def create_greenhouse(greenhouse: GreenhouseCreate):
    """创建温室"""
    # TODO: 实现温室创建
    return {"id": "mock_id", **greenhouse.model_dump()}


@router.get("/{greenhouse_id}", response_model=GreenhouseResponse)
async def get_greenhouse(greenhouse_id: str):
    """获取温室详情"""
    # TODO: 实现温室详情查询
    return {"id": greenhouse_id, "name": "Mock Greenhouse", "area": 500.0, "farm_id": "mock_farm"}


@router.get("/{greenhouse_id}/sensors", response_model=SensorData)
async def get_sensor_data(greenhouse_id: str):
    """获取传感器数据"""
    # TODO: 实现传感器数据查询
    return SensorData(
        temperature=25.5,
        humidity=75.2,
        light_intensity=450,
        co2=450,
        soil_moisture=65,
        soil_temperature=18
    )
