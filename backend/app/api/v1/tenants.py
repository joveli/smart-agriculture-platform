"""
租户管理 API
Tenant Management API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.models.tenant import Tenant, TenantStatus
from app.schemas.tenant import TenantCreate, TenantUpdate, TenantResponse

router = APIRouter()


def tenant_to_response(tenant: Tenant) -> TenantResponse:
    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        contact_email=tenant.contact_email,
        contact_phone=tenant.contact_phone,
        plan_type=tenant.plan_type,
        status=tenant.status,
        storage_quota_gb=tenant.storage_quota_gb,
        created_at=tenant.created_at,
    )


@router.get("/", response_model=List[TenantResponse])
async def list_tenants(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("platform_admin")),
):
    """获取所有租户列表（仅平台管理员）"""
    result = await db.execute(select(Tenant).where(Tenant.status != TenantStatus.DELETED.value))
    tenants = result.scalars().all()
    return [tenant_to_response(t) for t in tenants]


@router.post("/", response_model=TenantResponse)
async def create_tenant(
    payload: TenantCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("platform_admin")),
):
    """创建租户（仅平台管理员）"""
    tenant = Tenant(
        name=payload.name,
        contact_email=payload.contact_email,
        contact_phone=payload.contact_phone,
        plan_type=payload.plan_type,
        status=TenantStatus.ACTIVE.value,
    )
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant_to_response(tenant)


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取租户详情"""
    # 权限检查：平台管理员可查所有，租户管理员只能查自己
    if current_user.role != "platform_admin" and str(current_user.tenant_id) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant_to_response(tenant)


@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: UUID,
    payload: TenantUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("platform_admin", "tenant_admin")),
):
    """更新租户信息"""
    if current_user.role == "tenant_admin" and str(current_user.tenant_id) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tenant, field, value)

    await db.commit()
    await db.refresh(tenant)
    return tenant_to_response(tenant)


@router.delete("/{tenant_id}")
async def delete_tenant(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("platform_admin")),
):
    """删除租户（软删除）"""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    tenant.status = TenantStatus.DELETED.value
    from datetime import datetime, timezone
    tenant.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return {"message": "Tenant deleted"}
