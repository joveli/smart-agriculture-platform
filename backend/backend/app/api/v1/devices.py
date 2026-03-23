"""
设备管理 API
Device Management API
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.models.device import Device
from app.models.greenhouse import Greenhouse
from app.schemas.farm import DeviceCreate, DeviceUpdate, DeviceResponse, DeviceCommand

router = APIRouter()


@router.get("/", response_model=List[DeviceResponse])
async def list_devices(
    greenhouse_id: Optional[UUID] = Query(None),
    device_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取设备列表"""
    query = select(Device)
    if current_user.role != "platform_admin":
        query = query.where(Device.tenant_id == current_user.tenant_id)
    if greenhouse_id:
        query = query.where(Device.greenhouse_id == greenhouse_id)
    if device_type:
        query = query.where(Device.device_type == device_type)
    if status:
        query = query.where(Device.status == status)
    result = await db.execute(query)
    return [DeviceResponse.model_validate(d) for d in result.scalars().all()]


@router.post("/", response_model=DeviceResponse)
async def create_device(
    payload: DeviceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建设备"""
    # 验证温室归属
    gh_result = await db.execute(
        select(Greenhouse).where(Greenhouse.id == payload.greenhouse_id)
    )
    gh = gh_result.scalar_one_or_none()
    if not gh or str(gh.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=403, detail="Greenhouse not accessible")

    device = Device(
        tenant_id=current_user.tenant_id,
        **payload.model_dump(),
    )
    # 自动生成 mqtt_topic（未提供时）
    if not device.mqtt_topic:
        device.mqtt_topic = f"/tenants/{current_user.tenant_id}/devices/{device.id}"

    db.add(device)
    await db.commit()
    await db.refresh(device)
    return DeviceResponse.model_validate(device)


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Device).where(Device.id == device_id)
    if current_user.role != "platform_admin":
        query = query.where(Device.tenant_id == current_user.tenant_id)
    result = await db.execute(query)
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return DeviceResponse.model_validate(device)


@router.patch("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: UUID,
    payload: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Device).where(Device.id == device_id)
    if current_user.role != "platform_admin":
        query = query.where(Device.tenant_id == current_user.tenant_id)
    result = await db.execute(query)
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(device, field, value)
    await db.commit()
    await db.refresh(device)
    return DeviceResponse.model_validate(device)


@router.delete("/{device_id}")
async def delete_device(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Device).where(Device.id == device_id)
    if current_user.role != "platform_admin":
        query = query.where(Device.tenant_id == current_user.tenant_id)
    result = await db.execute(query)
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    await db.delete(device)
    await db.commit()
    return {"message": "Device deleted"}


@router.post("/{device_id}/command")
async def send_device_command(
    device_id: UUID,
    payload: DeviceCommand,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发送设备控制指令（通过 MQTT 下发）"""
    query = select(Device).where(Device.id == device_id)
    if current_user.role != "platform_admin":
        query = query.where(Device.tenant_id == current_user.tenant_id)
    result = await db.execute(query)
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # TODO: 通过 EMQX MQTT client 下发指令
    # from app.workers.mqtt import mqtt_client
    # await mqtt_client.publish(device.mqtt_topic + "/commands", payload.model_dump_json())

    return {
        "device_id": str(device_id),
        "command": payload.command,
        "params": payload.params,
        "status": "pending",
    }
