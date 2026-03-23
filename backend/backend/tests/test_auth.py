"""
认证模块单元测试
Authentication Module Unit Tests
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_token,
)
from app.schemas.auth import UserRegisterRequest


class TestPasswordHashing:
    """密码哈希测试"""

    def test_hash_and_verify(self):
        """测试哈希和验证流程"""
        password = "TestPass123"
        hashed = get_password_hash(password)
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("WrongPass", hashed) is False

    def test_different_hashes_for_same_password(self):
        """相同密码应产生不同哈希（盐值）"""
        password = "TestPass123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTToken:
    """JWT Token 测试"""

    def test_create_and_decode_token(self):
        """测试 Token 创建和解码"""
        data = {
            "sub": str(uuid4()),
            "tenant_id": str(uuid4()),
            "role": "tenant_admin",
        }
        token = create_access_token(data)
        assert token is not None
        assert isinstance(token, str)

        decoded = decode_token(token)
        assert decoded["sub"] == data["sub"]
        assert decoded["tenant_id"] == data["tenant_id"]
        assert decoded["role"] == data["role"]

    def test_token_contains_exp(self):
        """Token 应包含过期时间"""
        token = create_access_token({"sub": str(uuid4())})
        decoded = decode_token(token)
        assert "exp" in decoded
        assert "iat" in decoded

    def test_invalid_token_raises(self):
        """无效 Token 应抛出异常"""
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            decode_token("invalid.token.here")
        assert exc_info.value.status_code == 401


class TestPasswordValidation:
    """密码强度校验测试"""

    def test_valid_password(self):
        """合法密码应通过"""
        valid = UserRegisterRequest(
            username="testuser",
            email="test@example.com",
            password="SecurePass123",
            tenant_name="测试农场",
        )
        assert valid.password == "SecurePass123"

    def test_short_password_rejected(self):
        """过短密码应被拒绝"""
        with pytest.raises(ValueError, match="至少 8 个字符"):
            UserRegisterRequest(
                username="testuser",
                email="test@example.com",
                password="Short1",
                tenant_name="测试农场",
            )

    def test_password_without_letter_rejected(self):
        """无字母密码应被拒绝"""
        with pytest.raises(ValueError, match="必须包含字母"):
            UserRegisterRequest(
                username="testuser",
                email="test@example.com",
                password="12345678",
                tenant_name="测试农场",
            )

    def test_password_without_digit_rejected(self):
        """无数字密码应被拒绝"""
        with pytest.raises(ValueError, match="必须包含数字"):
            UserRegisterRequest(
                username="testuser",
                email="test@example.com",
                password="abcdefgh",
                tenant_name="测试农场",
            )

    def test_username_too_short(self):
        """过短用户名应被拒绝"""
        with pytest.raises(ValueError, match="至少 3 个字符"):
            UserRegisterRequest(
                username="ab",
                email="test@example.com",
                password="TestPass123",
                tenant_name="测试农场",
            )

    def test_username_with_special_chars_rejected(self):
        """含特殊字符用户名应被拒绝"""
        with pytest.raises(ValueError, match="只能包含字母和数字"):
            UserRegisterRequest(
                username="test_user",
                email="test@example.com",
                password="TestPass123",
                tenant_name="测试农场",
            )
