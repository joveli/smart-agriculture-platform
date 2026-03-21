"""
传感器数据查询工具
Sensor Data Query Tools for LLM Agent
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sensor_reading import SensorReading
from app.models.greenhouse import Greenhouse


async def query_latest_sensor_data(
    db: AsyncSession,
    greenhouse_id: UUID,
    tenant_id: UUID,
) -> dict:
    """
    查询温室最新传感器数据

    Returns:
        最新传感器读数，包含所有指标
    """
    result = await db.execute(
        select(SensorReading)
        .where(
            SensorReading.greenhouse_id == greenhouse_id,
            SensorReading.tenant_id == tenant_id,
        )
        .order_by(desc(SensorReading.time))
        .limit(1)
    )
    reading = result.scalar_one_or_none()
    if not reading:
        return {"error": "No sensor data available", "greenhouse_id": str(greenhouse_id)}

    return {
        "greenhouse_id": str(greenhouse_id),
        "timestamp": reading.time.isoformat() if reading.time else None,
        "temperature": float(reading.temperature) if reading.temperature else None,
        "humidity": float(reading.humidity) if reading.humidity else None,
        "light": float(reading.light) if reading.light else None,
        "co2": float(reading.co2) if reading.co2 else None,
        "soil_temperature": float(reading.soil_temperature) if reading.soil_temperature else None,
        "soil_humidity": float(reading.soil_humidity) if reading.soil_humidity else None,
        "soil_ec": float(reading.soil_ec) if reading.soil_ec else None,
    }


async def query_sensor_history(
    db: AsyncSession,
    greenhouse_id: UUID,
    tenant_id: UUID,
    hours: int = 24,
    metric: Optional[str] = None,
) -> dict:
    """
    查询历史传感器数据

    Args:
        hours: 查询最近多少小时的数据
        metric: 可选，指定特定指标 (temperature/humidity/light/co2/soil_*)
    """
    since = datetime.utcnow() - timedelta(hours=hours)
    query = select(SensorReading).where(
        SensorReading.greenhouse_id == greenhouse_id,
        SensorReading.tenant_id == tenant_id,
        SensorReading.time >= since,
    ).order_by(desc(SensorReading.time))

    result = await db.execute(query)
    readings = result.scalars().all()

    if not readings:
        return {"error": "No historical data", "greenhouse_id": str(greenhouse_id), "hours": hours}

    # 聚合统计
    metrics = ["temperature", "humidity", "light", "co2", "soil_temperature", "soil_humidity", "soil_ec"]
    stats = {}
    for m in metrics:
        if metric and m != metric:
            continue
        values = [getattr(r, m) for r in readings if getattr(r, m) is not None]
        if values:
            stats[m] = {
                "latest": float(values[0]),
                "min": float(min(values)),
                "max": float(max(values)),
                "avg": float(sum(values) / len(values)),
                "count": len(values),
            }

    return {
        "greenhouse_id": str(greenhouse_id),
        "period_hours": hours,
        "record_count": len(readings),
        "stats": stats,
        "latest_timestamp": readings[0].time.isoformat() if readings else None,
    }


def get_sensor_tools() -> list[dict]:
    """返回传感器相关的 Tool 定义（用于 LLM Function Calling）"""
    return [
        {
            "type": "function",
            "function": {
                "name": "get_latest_sensor_data",
                "description": "获取温室最新传感器读数（温度、湿度、光照、CO2、土壤数据）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "greenhouse_id": {
                            "type": "string",
                            "description": "温室UUID",
                        },
                    },
                    "required": ["greenhouse_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_sensor_history",
                "description": "查询历史传感器数据统计（最近N小时的平均值、最大值、最小值）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "greenhouse_id": {
                            "type": "string",
                            "description": "温室UUID",
                        },
                        "hours": {
                            "type": "integer",
                            "description": "查询最近多少小时的数据，默认24",
                            "default": 24,
                        },
                        "metric": {
                            "type": "string",
                            "description": "指定特定指标 (temperature/humidity/light/co2/soil_temperature/soil_humidity/soil_ec)，不指定则返回全部",
                            "enum": ["temperature", "humidity", "light", "co2", "soil_temperature", "soil_humidity", "soil_ec"],
                        },
                    },
                    "required": ["greenhouse_id"],
                },
            },
        },
    ]
