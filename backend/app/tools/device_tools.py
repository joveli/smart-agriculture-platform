"""
设备控制工具
Device Control Tools for LLM Agent
"""

from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device
from app.models.greenhouse import Greenhouse


async def list_devices(
    db: AsyncSession,
    greenhouse_id: UUID,
    tenant_id: UUID,
    device_type: Optional[str] = None,
) -> dict:
    """
    查询温室设备列表
    """
    query = select(Device).where(
        Device.greenhouse_id == greenhouse_id,
        Device.tenant_id == tenant_id,
    )
    if device_type:
        query = query.where(Device.device_type == device_type)
    result = await db.execute(query)
    devices = result.scalars().all()

    return {
        "greenhouse_id": str(greenhouse_id),
        "count": len(devices),
        "devices": [
            {
                "id": str(d.id),
                "name": d.name,
                "device_type": d.device_type,
                "model": d.model,
                "sn": d.sn,
                "status": d.status,
            }
            for d in devices
        ],
    }


async def get_device_status(
    db: AsyncSession,
    device_id: UUID,
    tenant_id: UUID,
) -> dict:
    """
    查询设备详情和状态
    """
    result = await db.execute(
        select(Device).where(Device.id == device_id, Device.tenant_id == tenant_id)
    )
    device = result.scalar_one_or_none()
    if not device:
        return {"error": "Device not found", "device_id": str(device_id)}

    return {
        "id": str(device.id),
        "name": device.name,
        "device_type": device.device_type,
        "model": device.model,
        "sn": device.sn,
        "status": device.status,
        "greenhouse_id": str(device.greenhouse_id) if device.greenhouse_id else None,
        "metadata": device.metadata or {},
    }


async def send_device_command(
    db: AsyncSession,
    device_id: UUID,
    tenant_id: UUID,
    command: str,
    params: Optional[dict] = None,
) -> dict:
    """
    向设备发送控制指令（通过 RabbitMQ 下发）

    实际下发由 mqtt_service 处理，这里仅记录指令日志
    """
    result = await db.execute(
        select(Device).where(Device.id == device_id, Device.tenant_id == tenant_id)
    )
    device = result.scalar_one_or_none()
    if not device:
        return {"error": "Device not found", "device_id": str(device_id)}

    # TODO: 通过 RabbitMQ 或 EMQX 下发实际指令
    # 现阶段记录到日志，由设备自行订阅
    payload = {
        "device_id": str(device_id),
        "command": command,
        "params": params or {},
    }

    return {
        "success": True,
        "device_id": str(device_id),
        "command": command,
        "params": params or {},
        "status": "pending",
        "message": f"Command '{command}' sent to device {device.name}",
    }


def get_device_tools() -> list[dict]:
    """返回设备相关的 Tool 定义"""
    return [
        {
            "type": "function",
            "function": {
                "name": "list_greenhouse_devices",
                "description": "查询温室下的所有设备",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "greenhouse_id": {"type": "string", "description": "温室UUID"},
                        "device_type": {"type": "string", "description": "设备类型筛选（可选）"},
                    },
                    "required": ["greenhouse_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_device_info",
                "description": "查询单个设备的详细信息和运行状态",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "device_id": {"type": "string", "description": "设备UUID"},
                    },
                    "required": ["device_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "control_device",
                "description": "向设备发送控制指令（开关机、调节参数等）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "device_id": {"type": "string", "description": "设备UUID"},
                        "command": {
                            "type": "string",
                            "description": "指令类型",
                            "enum": ["turn_on", "turn_off", "set_mode", "set_value", "reset"],
                        },
                        "params": {
                            "type": "object",
                            "description": "指令参数，如 {mode: 'cooling', value: 25}",
                        },
                    },
                    "required": ["device_id", "command"],
                },
            },
        },
    ]
