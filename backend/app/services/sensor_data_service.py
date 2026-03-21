"""
传感器数据处理服务
Sensor Data Processing Service - Batch Write to TimescaleDB
"""

import asyncio
import json
from datetime import datetime
from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.models.sensor_reading import SensorReading
from app.models.device import Device
from app.core.database import async_session_maker


class SensorDataService:
    """
    传感器数据处理服务

    功能：
    - 接收 MQTT 传感器数据
    - 批量写入 TimescaleDB（batch_size=100 或 5秒刷盘）
    - 租户隔离
    - 触发规则引擎评估
    """

    def __init__(
        self,
        batch_size: int = 100,
        flush_interval_sec: float = 5.0,
    ):
        self.batch_size = batch_size
        self.flush_interval_sec = flush_interval_sec

        self._buffer: list[dict] = []
        self._flush_lock = asyncio.Lock()
        self._flush_task: Optional[asyncio.Task] = None
        self._rule_engine = None  # 延迟导入避免循环

    async def start(self):
        """启动服务"""
        self._flush_task = asyncio.create_task(self._flush_loop())
        print(f"✅ SensorDataService started (batch={self.batch_size}, flush={self.flush_interval_sec}s)")

    async def stop(self):
        """停止服务，刷新剩余数据"""
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        # 最后刷新一次
        await self._flush()
        print("✅ SensorDataService stopped")

    async def ingest(self, data: dict):
        """
        接收一条传感器数据（从 MQTT 来）

        data 格式：
        {
            "tenant_id": "uuid",
            "device_id": "uuid",
            "topic": "...",
            "temperature": 25.5,  # 或
            "temperature": 25.5, "humidity": 70, ...
            # 或单指标模式：
            "metric": "temperature",
            "value": 25.5,
            "timestamp": "..." (optional)
        }
        """
        # 转换为标准格式（支持单指标和批量）
        reading = self._normalize_data(data)
        if reading is None:
            return

        async with self._flush_lock:
            self._buffer.append(reading)
            if len(self._buffer) >= self.batch_size:
                await self._flush()

    def _normalize_data(self, data: dict) -> Optional[dict]:
        """将 MQTT payload 规范化为 SensorReading 字典"""
        try:
            tenant_id = data.get("tenant_id")
            device_id = data.get("device_id")

            if not tenant_id or not device_id:
                return None

            # 时间戳
            timestamp = data.get("timestamp")
            if timestamp:
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            else:
                timestamp = datetime.utcnow()

            # 温室ID需要从device查询（device_id → greenhouse_id）
            greenhouse_id = data.get("greenhouse_id")

            result = {
                "tenant_id": UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id,
                "device_id": UUID(device_id) if isinstance(device_id, str) else device_id,
                "greenhouse_id": UUID(greenhouse_id) if greenhouse_id else None,
                "time": timestamp,
                "temperature": self._to_float(data.get("temperature")),
                "humidity": self._to_float(data.get("humidity")),
                "light": self._to_float(data.get("light")),
                "co2": self._to_float(data.get("co2")),
                "soil_temperature": self._to_float(data.get("soil_temperature")),
                "soil_humidity": self._to_float(data.get("soil_humidity")),
                "soil_ec": self._to_float(data.get("soil_ec")),
                "raw_payload": json.dumps(data, ensure_ascii=False)[:1000],
            }
            return result
        except Exception as e:
            print(f"⚠️ Normalize data error: {e}")
            return None

    def _to_float(self, value) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    async def _flush_loop(self):
        """定时刷盘循环"""
        while True:
            await asyncio.sleep(self.flush_interval_sec)
            try:
                await self._flush()
            except Exception as e:
                print(f"⚠️ Flush error: {e}")

    async def _flush(self):
        """批量写入数据库"""
        if not self._buffer:
            return

        buffer_copy = self._buffer[:]
        self._buffer.clear()

        try:
            async with async_session_maker() as session:
                # 查询 device → greenhouse_id 映射（补充缺失的 greenhouse_id）
                device_ids = list({r["device_id"] for r in buffer_copy})
                device_result = await session.execute(
                    select(Device).where(Device.id.in_(device_ids))
                )
                device_map = {d.id: d.greenhouse_id for d in device_result.scalars().all()}

                readings = []
                for r in buffer_copy:
                    # 补充 greenhouse_id
                    if r["greenhouse_id"] is None:
                        r["greenhouse_id"] = device_map.get(r["device_id"])

                    if r["greenhouse_id"] is None:
                        continue  # 跳过无法确定温室的数据

                    reading = SensorReading(**r)
                    readings.append(reading)

                if readings:
                    session.add_all(readings)
                    await session.commit()
                    print(f"💾 Flushed {len(readings)} sensor readings to TimescaleDB")
        except Exception as e:
            print(f"❌ Failed to flush sensor readings: {e}")
            # 写回缓冲区（不丢失数据）
            self._buffer = buffer_copy + self._buffer


# 全局单例
sensor_data_service: Optional[SensorDataService] = None


def get_sensor_data_service() -> SensorDataService:
    global sensor_data_service
    if sensor_data_service is None:
        sensor_data_service = SensorDataService(
            batch_size=100,
            flush_interval_sec=5.0,
        )
    return sensor_data_service
