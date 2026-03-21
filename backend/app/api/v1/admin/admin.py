"""
超级管理员 API
Admin API - Platform-wide management
Prefix: /api/v1/admin
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, timezone
from uuid import UUID

from app.core.database import get_db
from app.core.security import require_role
from app.models.user import User
from app.models.tenant import Tenant
from app.models.audit_log import AuditLog

router = APIRouter()


@router.get("/audit-logs")
async def list_audit_logs(
    tenant_id: Optional[UUID] = Query(None),
    user_id: Optional[UUID] = Query(None),
    action: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("platform_admin")),
):
    """审计日志查询（仅平台管理员）"""
    query = select(AuditLog).order_by(AuditLog.created_at.desc())
    if tenant_id:
        query = query.where(AuditLog.tenant_id == tenant_id)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if action:
        query = query.where(AuditLog.action == action)
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    logs = result.scalars().all()
    return [
        {
            "id": str(log.id),
            "tenant_id": str(log.tenant_id) if log.tenant_id else None,
            "user_id": str(log.user_id) if log.user_id else None,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "request_path": log.request_path,
            "response_status": log.response_status,
            "client_ip": log.client_ip,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]


@router.get("/tenants/stats")
async def get_tenant_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("platform_admin")),
):
    """平台租户统计"""
    result = await db.execute(select(Tenant))
    tenants = result.scalars().all()
    stats = {
        "total": len(tenants),
        "active": len([t for t in tenants if t.status == "active"]),
        "suspended": len([t for t in tenants if t.status == "suspended"]),
        "pending": len([t for t in tenants if t.status == "pending"]),
    }
    return stats
