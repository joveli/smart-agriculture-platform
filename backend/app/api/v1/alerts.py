"""
告警管理 API
Alert Management API
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.alert import Alert, AlertRule
from app.schemas.alert import (
    AlertRuleCreate, AlertRuleUpdate, AlertRuleResponse,
    AlertResponse, AlertAcknowledge,
)

router = APIRouter()


# ============ Alert Rules ============
@router.get("/rules", response_model=List[AlertRuleResponse])
async def list_alert_rules(
    greenhouse_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取告警规则列表"""
    query = select(AlertRule)
    if current_user.role != "platform_admin":
        query = query.where(AlertRule.tenant_id == current_user.tenant_id)
    if greenhouse_id:
        query = query.where(AlertRule.greenhouse_id == greenhouse_id)
    result = await db.execute(query)
    return [AlertRuleResponse.model_validate(r) for r in result.scalars().all()]


@router.post("/rules", response_model=AlertRuleResponse)
async def create_alert_rule(
    payload: AlertRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建告警规则"""
    rule = AlertRule(
        tenant_id=current_user.tenant_id,
        **payload.model_dump(),
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return AlertRuleResponse.model_validate(rule)


@router.patch("/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(
    rule_id: UUID,
    payload: AlertRuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新告警规则"""
    query = select(AlertRule).where(AlertRule.id == rule_id)
    if current_user.role != "platform_admin":
        query = query.where(AlertRule.tenant_id == current_user.tenant_id)
    result = await db.execute(query)
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    await db.commit()
    await db.refresh(rule)
    return AlertRuleResponse.model_validate(rule)


@router.delete("/rules/{rule_id}")
async def delete_alert_rule(
    rule_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除告警规则"""
    query = select(AlertRule).where(AlertRule.id == rule_id)
    if current_user.role != "platform_admin":
        query = query.where(AlertRule.tenant_id == current_user.tenant_id)
    result = await db.execute(query)
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    await db.delete(rule)
    await db.commit()
    return {"message": "Alert rule deleted"}


# ============ Alerts ============
@router.get("/", response_model=List[AlertResponse])
async def list_alerts(
    greenhouse_id: Optional[UUID] = Query(None),
    level: Optional[str] = Query(None),
    resolved: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取告警列表"""
    query = select(Alert)
    if current_user.role != "platform_admin":
        query = query.where(Alert.tenant_id == current_user.tenant_id)
    if greenhouse_id:
        query = query.where(Alert.greenhouse_id == greenhouse_id)
    if level:
        query = query.where(Alert.level == level)
    if resolved is not None:
        resolved_filter = "resolved" if resolved else "pending"
        query = query.where(Alert.status == resolved_filter)
    query = query.order_by(Alert.created_at.desc())
    result = await db.execute(query)
    return [AlertResponse.model_validate(a) for a in result.scalars().all()]


@router.post("/", response_model=AlertResponse)
async def create_alert(
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    """
    创建告警（内部服务调用，非用户 API）
    通常由 MQTT 数据订阅服务或 APScheduler 定时任务触发
    """
    alert = Alert(**payload)
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return AlertResponse.model_validate(alert)


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: UUID,
    payload: AlertAcknowledge,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """确认/处理告警"""
    query = select(Alert).where(Alert.id == alert_id)
    if current_user.role != "platform_admin":
        query = query.where(Alert.tenant_id == current_user.tenant_id)
    result = await db.execute(query)
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = "acknowledged"
    await db.commit()
    return {"alert_id": str(alert_id), "status": "acknowledged"}


@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """解决告警"""
    query = select(Alert).where(Alert.id == alert_id)
    if current_user.role != "platform_admin":
        query = query.where(Alert.tenant_id == current_user.tenant_id)
    result = await db.execute(query)
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = "resolved"
    alert.resolved_at = datetime.utcnow()
    alert.resolved_by = current_user.id
    await db.commit()
    return {"alert_id": str(alert_id), "status": "resolved"}
