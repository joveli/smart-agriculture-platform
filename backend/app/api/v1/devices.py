"""
设备管理模块
Device Management Module
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()


class DeviceBase(BaseModel):
    name: str
    device_type: str
    model: str = ""
    sn: str = ""


class DeviceCreate(DeviceBase):
    greenhouse_id: str


class DeviceResponse(DeviceBase):
    id: str
    greenhouse_id: str
    status: str = "online"

    class Config:
        from_attributes = True


@router.get("/", response_model=List[DeviceResponse])
async def list_devices(greenhouse_id: str):
    """获取设备列表"""
    # TODO: 实现设备列表查询
    return []


@router.post("/", response_model=DeviceResponse)
async def create_device(device: DeviceCreate):
    """创建设备"""
    # TODO: 实现设备创建
    return {"id": "mock_id", **device.model_dump()}


@router.post("/{device_id}/command")
async def send_command(device_id: str, command: str, params: dict = None):
    """发送设备控制指令"""
    # TODO: 实现设备指令下发
    return {"device_id": device_id, "command": command, "status": "pending"}
