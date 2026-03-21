"""
规则引擎 - 阈值告警规则引擎
Rule Engine - Threshold-based Alert Engine
"""

import operator
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert, AlertRule, AlertLevel
from app.models.sensor_reading import SensorReading


# 操作符映射
OPERATORS = {
    "gt": operator.gt,      # >
    "lt": operator.lt,      # <
    "gte": operator.ge,      # >=
    "lte": operator.le,      # <=
    "eq": operator.eq,       # ==
}


class RuleEngine:
    """
    告警规则引擎

    支持两种模式：
    1. 实时检测（SensorData 流入时触发）
    2. 定时巡检（APScheduler 周期执行）
    """

    def __init__(self):
        pass

    async def evaluate_sensor_reading(
        self,
        db: AsyncSession,
        reading: SensorReading,
        tenant_id: UUID,
    ) -> list[Alert]:
        """
        评估单条传感器数据，触发匹配的告警规则

        Returns:
            创建的 Alert 对象列表
        """
        alerts_created = []

        # 查询该租户所有启用的规则
        result = await db.execute(
            select(AlertRule).where(
                AlertRule.tenant_id == tenant_id,
                AlertRule.enabled == True,
            )
        )
        rules = result.scalars().all()

        for rule in rules:
            # 检查是否适用于该温室（null = 全温室）
            if rule.greenhouse_id and rule.greenhouse_id != reading.greenhouse_id:
                continue

            # 获取传感器读数
            metric_value = getattr(reading, rule.metric, None)
            if metric_value is None:
                continue

            # 阈值比较
            try:
                threshold = float(rule.threshold)
                metric_value_float = float(metric_value)
            except (ValueError, TypeError):
                continue

            op_func = OPERATORS.get(rule.operator)
            if not op_func:
                continue

            if op_func(metric_value_float, threshold):
                # 触发告警，检查收敛
                if await self._should_fire_alert(db, rule, reading.greenhouse_id):
                    alert = await self._create_alert(db, reading, rule, tenant_id)
                    alerts_created.append(alert)

        return alerts_created

    async def evaluate_greenhouse(
        self,
        db: AsyncSession,
        greenhouse_id: UUID,
        tenant_id: UUID,
    ) -> list[Alert]:
        """
        对整个温室进行定时巡检（最新一条传感器数据）

        Returns:
            创建的 Alert 对象列表
        """
        # 获取温室最新传感器数据
        result = await db.execute(
            select(SensorReading)
            .where(
                SensorReading.greenhouse_id == greenhouse_id,
                SensorReading.tenant_id == tenant_id,
            )
            .order_by(SensorReading.time.desc())
            .limit(1)
        )
        reading = result.scalar_one_or_none()
        if not reading:
            return []

        return await self.evaluate_sensor_reading(db, reading, tenant_id)

    async def _should_fire_alert(
        self,
        db: AsyncSession,
        rule: AlertRule,
        greenhouse_id: UUID,
    ) -> bool:
        """
        检查告警是否应该触发（收敛控制）

        如果最近 cooldown_minutes 内有同类告警，则跳过
        """
        if rule.cooldown_minutes <= 0:
            return True

        since = datetime.utcnow() - timedelta(minutes=rule.cooldown_minutes)
        result = await db.execute(
            select(Alert).where(
                Alert.rule_id == rule.id,
                Alert.greenhouse_id == greenhouse_id,
                Alert.created_at >= since,
            )
        )
        recent = result.scalars().first()
        return recent is None

    async def _create_alert(
        self,
        db: AsyncSession,
        reading: SensorReading,
        rule: AlertRule,
        tenant_id: UUID,
    ) -> Alert:
        """创建告警记录"""
        metric_value = getattr(reading, rule.metric, None)
        metric_display = getattr(reading, rule.metric, None)

        alert = Alert(
            tenant_id=tenant_id,
            greenhouse_id=reading.greenhouse_id,
            device_id=reading.device_id,
            rule_id=rule.id,
            alert_type=rule.metric,
            level=rule.level,
            message=self._build_alert_message(rule, metric_value),
            resolved=False,
        )
        db.add(alert)
        await db.commit()
        await db.refresh(alert)
        return alert

    def _build_alert_message(self, rule: AlertRule, metric_value: float) -> str:
        """构建告警消息"""
        op_text = {
            "gt": "高于",
            "lt": "低于",
            "gte": "高于或等于",
            "lte": "低于或等于",
            "eq": "等于",
        }.get(rule.operator, rule.operator)

        metric_names = {
            "temperature": "温度",
            "humidity": "湿度",
            "light": "光照",
            "co2": "CO2浓度",
            "soil_temperature": "土壤温度",
            "soil_humidity": "土壤湿度",
            "soil_ec": "土壤EC值",
        }
        name = metric_names.get(rule.metric, rule.metric)

        level_text = {
            "critical": "🔴 严重",
            "warning": "🟡 警告",
            "info": "🔵 提示",
        }.get(rule.level, rule.level)

        return f"{level_text} {name} {op_text} {rule.threshold}（当前值：{metric_value}）"


# 全局实例
rule_engine = RuleEngine()
