"""
认证 API
Authentication API
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, timezone

from app.core.database import get_db
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    decode_token,
)
from app.models.user import User, UserRole
from app.models.tenant import Tenant, TenantStatus
from app.schemas.auth import (
    UserRegisterRequest,
    TokenResponse,
    UserResponse,
    TokenRefreshRequest,
)

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register(
    payload: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    用户自主注册
    - 创建 Pending 状态租户
    - 创建 Tenant Admin 用户
    - 发送注册确认邮件（logging 占位）
    """
    # 检查用户名
    existing = await db.execute(
        select(User).where(User.username == payload.username)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 检查邮箱
    existing_email = await db.execute(
        select(User).where(User.email == payload.email)
    )
    if existing_email.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="邮箱已被注册")

    # 创建租户（pending 状态，待平台管理员审核）
    tenant = Tenant(
        name=payload.tenant_name,
        contact_email=payload.email,
        status=TenantStatus.PENDING.value,
        plan_type="free",
    )
    db.add(tenant)
    await db.flush()  # 获取 tenant.id

    # 创建租户管理员用户
    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        role=UserRole.TENANT_ADMIN.value,
        tenant_id=tenant.id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # TODO: 发送注册确认邮件（logging 占位）
    print(f"[EMAIL] 注册确认邮件已发送至 {payload.email}")

    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """用户登录获取 Token"""
    result = await db.execute(
        select(User).where(User.username == form_data.username)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="账户已被禁用")

    # 检查租户状态
    if user.tenant:
        if user.tenant.status == TenantStatus.PENDING.value:
            raise HTTPException(
                status_code=403,
                detail="租户正在等待审核，请联系平台管理员",
            )
        if user.tenant.status == TenantStatus.SUSPENDED.value:
            raise HTTPException(
                status_code=403,
                detail="租户已被暂停，请联系平台管理员",
            )
        if user.tenant.status == TenantStatus.DELETED.value:
            raise HTTPException(
                status_code=403,
                detail="租户已被删除",
            )

    # 更新最后登录时间
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    # 生成 JWT
    token = create_access_token(
        data={
            "sub": str(user.id),
            "tenant_id": str(user.tenant_id) if user.tenant_id else None,
            "role": user.role,
        }
    )
    return TokenResponse(access_token=token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    payload: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    刷新 Token
    验证 token payload，返回新的 access_token
    """
    payload_data = decode_token(payload.token)
    user_id: str = payload_data.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="无效 Token")

    # 验证用户仍然存在且活跃
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="用户不存在或已禁用")

    new_token = create_access_token(
        data={
            "sub": str(user.id),
            "tenant_id": str(user.tenant_id) if user.tenant_id else None,
            "role": user.role,
        }
    )
    return TokenResponse(access_token=new_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user
