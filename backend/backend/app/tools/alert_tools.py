"""
告警管理工具
Alert Management Tools for LLM Agent
"""

from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert, AlertRule


async def list_alerts(
    db: AsyncSession,
    tenant_id: UUID,
    greenhouse_id: Optional[UUID] = None,
    level: Optional[str] = None,
    resolved: Optional[bool] = None,
    limit: int = 20,
) -> dict:
    """
    查询告警列表
    """
    query = select(Alert).where(Alert.tenant_id == tenant_id)
    if greenhouse_id:
        query = query.where(Alert.greenhouse_id == greenhouse_id)
    if level:
        query = query.where(Alert.level == level)
    if resolved is not None:
        query = query.where(Alert.resolved == resolved)
    query = query.order_by(desc(Alert.created_at)).limit(limit)

    result = await db.execute(query)
    alerts = result.scalars().all()

    return {
        "count": len(alerts),
        "alerts": [
            {
                "id": str(a.id),
                "greenhouse_id": str(a.greenhouse_id),
                "alert_type": a.alert_type,
                "level": a.level,
                "message": a.message,
                "resolved": a.resolved,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in alerts
        ],
    }


async def create_alert_rule(
    db: AsyncSession,
    tenant_id: UUID,
    name: str,
    metric: str,
    operator: str,
    threshold: float,
    level: str = "warning",
    greenhouse_id: Optional[UUID] = None,
    notification_channels: Optional[list[str]] = None,
    cooldown_minutes: int = 5,
) -> dict:
    """
    创建告警规则
    """
    rule = AlertRule(
        tenant_id=tenant_id,
        greenhouse_id=greenhouse_id,
        name=name,
        metric=metric,
        operator=operator,
        threshold=str(threshold),  # 存为字符串便于比较
        level=level,
        notification_channels=notification_channels or ["websocket"],
        cooldown_minutes=cooldown_minutes,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)

    return {
        "id": str(rule.id),
        "name": rule.name,
        "metric": rule.metric,
        "operator": rule.operator,
        "threshold": rule.threshold,
        "level": rule.level,
        "enabled": rule.enabled,
        "message": f"Alert rule '{name}' created successfully",
    }


async def get_alert_summary(
    db: AsyncSession,
    tenant_id: UUID,
    greenhouse_id: Optional[UUID] = None,
) -> dict:
    """
    获取告警统计摘要
    """
    query = select(Alert).where(Alert.tenant_id == tenant_id)
    if greenhouse_id:
        query = query.where(Alert.greenhouse_id == greenhouse_id)

    result = await db.execute(query)
    alerts = result.scalars().all()

    # 统计
    total = len(alerts)
    critical = sum(1 for a in alerts if a.level == "critical")
    warning = sum(1 for a in alerts if a.level == "warning")
    info = sum(1 for a in alerts if a.level == "info")
    unresolved = sum(1 for a in alerts if not a.resolved)

    # 最近24小时
    from datetime import timedelta
    day_ago = datetime.utcnow() - timedelta(hours=24)
    recent = sum(1 for a in alerts if a.created_at and a.created_at >= day_ago)

    return {
        "total": total,
        "critical": critical,
        "warning": warning,
        "info": info,
        "unresolved": unresolved,
        "last_24h": recent,
    }


def get_alert_tools() -> list[dict]:
    """返回告警相关的 Tool 定义"""
    return [
        {
            "type": "function",
            "function": {
                "name": "get_alert_summary",
                "description": "获取告警统计摘要（各级别数量、未解决数量、最近24小时告警数）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "greenhouse_id": {"type": "string", "description": "温室UUID（可选，不填则查全部）"},
                    },
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_alerts",
                "description": "查询最近告警列表",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "greenhouse_id": {"type": "string", "description": "温室UUID（可选）"},
                        "level": {"type": "string", "description": "告警级别：critical/warning/info"},
                        "resolved": {"type": "boolean", "description": "是否已解决"},
                        "limit": {"type": "integer", "description": "返回数量，默认20"},
                    },
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "create_alert_rule",
                "description": "创建新的告警规则",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "规则名称"},
                        "metric": {
                            "type": "string",
                            "description": "监控指标",
                            "enum": ["temperature", "humidity", "light", "co2", "soil_temperature", "soil_humidity", "soil_ec"],
                        },
                        "operator": {
                            "type": "string",
                            "description": "比较运算符",
                            "enum": ["gt", "lt", "gte", "lte", "eq"],
                        },
                        "threshold": {"type": "number", "description": "阈值"},
                        "level": {
                            "type": "string",
                            "description": "告警级别",
                            "enum": ["critical", "warning", "info"],
                            "default": "warning",
                        },
                        "greenhouse_id": {"type": "string", "description": "温室UUID（可选）"},
                        "cooldown_minutes": {"type": "integer", "description": "告警收敛时间（分钟）", "default": 5},
                    },
                    "required": ["name", "metric", "operator", "threshold"],
                },
            },
        },
    ]
