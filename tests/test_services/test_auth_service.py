"""
认证服务单元测试。

覆盖测试规格:
  - UT-USR-001 ~ UT-USR-005: 注册/登录流程
"""

import pytest

from aixue.services.auth_service import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


# ---------------------------------------------------------------------------
# 密码哈希测试
# ---------------------------------------------------------------------------

class TestPasswordHashing:
    """测试 bcrypt 密码加密和验证。"""

    def test_hash_password_not_plaintext(self):
        """UT-USR-001: 密码以 bcrypt 哈希存储，不是明文。"""
        password = "Abc12345"
        hashed = hash_password(password)
        assert hashed != password
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    def test_verify_correct_password(self):
        """UT-USR-004: 正确密码能通过验证。"""
        password = "Abc12345"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_wrong_password(self):
        """UT-USR-005: 错误密码验证失败。"""
        hashed = hash_password("Abc12345")
        assert verify_password("WrongPass", hashed) is False

    def test_different_hashes_for_same_password(self):
        """同一密码多次哈希结果不同（salt 不同）。"""
        password = "Abc12345"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2
        # 但两个哈希都能通过验证
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


# ---------------------------------------------------------------------------
# JWT Token 测试
# ---------------------------------------------------------------------------

class TestJWTToken:
    """测试 JWT 令牌生成和解码。"""

    def test_create_and_decode_token(self):
        """令牌包含正确的 user_id。"""
        user_id = "test-user-123"
        token = create_access_token(user_id)
        decoded_user_id = decode_access_token(token)
        assert decoded_user_id == user_id

    def test_decode_invalid_token(self):
        """无效令牌解码失败。"""
        with pytest.raises(Exception):
            decode_access_token("invalid-token-string")

    def test_decode_tampered_token(self):
        """篡改的令牌解码失败。"""
        token = create_access_token("user-123")
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(Exception):
            decode_access_token(tampered)
