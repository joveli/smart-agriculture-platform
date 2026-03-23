"""
API 集成测试
API Integration Tests
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone

from app.main import app
from app.core.security import get_password_hash, create_access_token


class TestAuthAPI:
    """认证 API 测试"""

    @pytest_asyncio.fixture
    async def client(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_login_success(self, client):
        """正常登录应返回 Token"""
        with patch("app.api.v1.auth.db") as mock_db:
            mock_user = MagicMock()
            mock_user.id = uuid4()
            mock_user.username = "testuser"
            mock_user.hashed_password = get_password_hash("TestPass123")
            mock_user.is_active = True
            mock_user.tenant = MagicMock()
            mock_user.tenant.status = "active"
            mock_user.tenant_id = uuid4()
            mock_user.role = "tenant_admin"
            mock_user.last_login_at = None

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_user
            mock_db.execute.return_value = mock_result
            mock_db.commit = AsyncMock()

            response = await client.post(
                "/api/v1/auth/login",
                data={"username": "testuser", "password": "TestPass123"},
            )
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client):
        """错误密码应返回 401"""
        with patch("app.api.v1.auth.db") as mock_db:
            mock_user = MagicMock()
            mock_user.hashed_password = get_password_hash("TestPass123")
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_user
            mock_db.execute.return_value = mock_result

            response = await client.post(
                "/api/v1/auth/login",
                data={"username": "testuser", "password": "WrongPass"},
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_user_not_found(self, client):
        """用户不存在应返回 401"""
        with patch("app.api.v1.auth.db") as mock_db:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result

            response = await client.post(
                "/api/v1/auth/login",
                data={"username": "nonexistent", "password": "TestPass123"},
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_tenant_pending(self, client):
        """Pending 租户应返回 403"""
        with patch("app.api.v1.auth.db") as mock_db:
            mock_user = MagicMock()
            mock_user.hashed_password = get_password_hash("TestPass123")
            mock_user.is_active = True
            mock_user.tenant = MagicMock()
            mock_user.tenant.status = "pending"
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_user
            mock_db.execute.return_value = mock_result

            response = await client.post(
                "/api/v1/auth/login",
                data={"username": "testuser", "password": "TestPass123"},
            )
            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client):
        """弱密码应返回 422"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "weak",
                "tenant_name": "测试农场",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_short_username(self, client):
        """过短用户名应返回 422"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "ab",
                "email": "test@example.com",
                "password": "TestPass123",
                "tenant_name": "测试农场",
            },
        )
        assert response.status_code == 422


class TestTenantAPI:
    """租户管理 API 测试"""

    def _make_admin_headers(self):
        """生成平台管理员 JWT header"""
        token = create_access_token({
            "sub": str(uuid4()),
            "tenant_id": None,
            "role": "platform_admin",
        })
        return {"Authorization": f"Bearer {token}"}

    def _make_tenant_admin_headers(self, tenant_id):
        """生成租户管理员 JWT header"""
        token = create_access_token({
            "sub": str(uuid4()),
            "tenant_id": str(tenant_id),
            "role": "tenant_admin",
        })
        return {"Authorization": f"Bearer {token}"}

    @pytest.mark.asyncio
    async def test_list_tenants_requires_admin(self):
        """普通用户无法列出所有租户"""
        with AsyncClient(base_url="http://test") as client:
            # 租户管理员 Token
            token = create_access_token({
                "sub": str(uuid4()),
                "tenant_id": str(uuid4()),
                "role": "tenant_admin",
            })
            headers = {"Authorization": f"Bearer {token}"}
            with patch("app.api.v1.tenants.db") as mock_db:
                mock_result = MagicMock()
                mock_result.scalars.return_value.all.return_value = []
                mock_db.execute.return_value = mock_result

                response = await client.get("/api/v1/tenants/", headers=headers)
                # tenant_admin 没有 platform_admin 角色，应返回 403
                assert response.status_code in [403, 401]

    @pytest.mark.asyncio
    async def test_get_me_returns_user_info(self):
        """获取当前用户信息"""
        user_id = uuid4()
        token = create_access_token({
            "sub": str(user_id),
            "tenant_id": str(uuid4()),
            "role": "tenant_admin",
        })
        headers = {"Authorization": f"Bearer {token}"}

        with AsyncClient(base_url="http://test") as client:
            with patch("app.core.security.db") as mock_db:
                mock_user = MagicMock()
                mock_user.id = user_id
                mock_user.username = "testuser"
                mock_user.email = "test@example.com"
                mock_user.full_name = "Test User"
                mock_user.role = "tenant_admin"
                mock_user.tenant_id = uuid4()
                mock_user.is_active = True
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = mock_user
                mock_db.execute.return_value = mock_result

                response = await client.get("/api/v1/auth/me", headers=headers)
                assert response.status_code == 200
                data = response.json()
                assert data["username"] == "testuser"
                assert data["role"] == "tenant_admin"


class TestMultiTenantIsolation:
    """多租户隔离测试"""

    def test_jwt_payload_contains_tenant_id(self):
        """JWT payload 应包含 tenant_id"""
        tenant_id = str(uuid4())
        token = create_access_token({
            "sub": str(uuid4()),
            "tenant_id": tenant_id,
            "role": "tenant_admin",
        })
        from app.core.security import decode_token
        decoded = decode_token(token)
        assert decoded["tenant_id"] == tenant_id

    def test_jwt_payload_platform_admin_no_tenant(self):
        """平台管理员 JWT payload tenant_id 应为 None"""
        token = create_access_token({
            "sub": str(uuid4()),
            "tenant_id": None,
            "role": "platform_admin",
        })
        from app.core.security import decode_token
        decoded = decode_token(token)
        assert decoded["tenant_id"] is None
        assert decoded["role"] == "platform_admin"


class TestSecurityTests:
    """安全测试"""

    def test_sql_injection_in_username(self):
        """测试 SQL 注入防护（Schema 层面）"""
        # 用户名只允许字母数字，Pydantic 已做限制
        from app.schemas.auth import UserRegisterRequest
        with pytest.raises(ValueError):
            UserRegisterRequest(
                username="admin'; DROP TABLE users;--",
                email="test@example.com",
                password="TestPass123",
                tenant_name="Test",
            )

    def test_token_without_sub_rejected(self):
        """Token 没有 sub claim 应被拒绝"""
        from jose import jwt
        from app.core.config import settings
        from fastapi import HTTPException

        # 构造没有 sub 的 token
        bad_token = jwt.encode(
            {"tenant_id": str(uuid4()), "role": "admin"},
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        from app.core.security import decode_token
        with pytest.raises(HTTPException) as exc:
            decode_token(bad_token)
        assert exc.value.status_code == 401

    def test_expired_token_rejected(self):
        """过期 Token 应被拒绝（decode 层面会被 jose 拦截）"""
        from jose import jwt
        from app.core.config import settings
        from datetime import datetime, timedelta
        from fastapi import HTTPException

        past = datetime.now(timezone.utc) - timedelta(hours=1)
        expired_token = jwt.encode(
            {"sub": str(uuid4()), "exp": past},
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        from app.core.security import decode_token
        with pytest.raises(HTTPException) as exc:
            decode_token(expired_token)
        assert exc.value.status_code == 401
