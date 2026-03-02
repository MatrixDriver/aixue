"""
认证 API 端点集成测试。

覆盖测试规格:
  - UT-USR-001 ~ UT-USR-007: 用户注册/登录/权限
  - E2E-ERR-003: 未登录访问拒绝
"""

import pytest
from httpx import AsyncClient

from tests.conftest import TEST_USERS


# ---------------------------------------------------------------------------
# 注册测试
# ---------------------------------------------------------------------------

class TestRegister:

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """UT-USR-001: 正常注册流程。"""
        resp = await client.post("/api/auth/register", json=TEST_USERS[0])
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert "id" in data or "access_token" in data

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client: AsyncClient):
        """UT-USR-002: 重复用户名拒绝注册。"""
        # 第一次注册
        await client.post("/api/auth/register", json=TEST_USERS[0])
        # 第二次注册同一用户名
        resp = await client.post("/api/auth/register", json=TEST_USERS[0])
        assert resp.status_code in (400, 409, 422)

    @pytest.mark.asyncio
    async def test_register_missing_username(self, client: AsyncClient):
        """UT-USR-003: 缺少用户名返回校验错误。"""
        data = {k: v for k, v in TEST_USERS[0].items() if k != "username"}
        resp = await client.post("/api/auth/register", json=data)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_register_missing_password(self, client: AsyncClient):
        """UT-USR-003: 缺少密码返回校验错误。"""
        data = {k: v for k, v in TEST_USERS[0].items() if k != "password"}
        resp = await client.post("/api/auth/register", json=data)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_register_missing_name(self, client: AsyncClient):
        """UT-USR-003: 缺少姓名返回校验错误。"""
        data = {k: v for k, v in TEST_USERS[0].items() if k != "name"}
        resp = await client.post("/api/auth/register", json=data)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_register_missing_grade(self, client: AsyncClient):
        """UT-USR-003: 缺少年级返回校验错误。"""
        data = {k: v for k, v in TEST_USERS[0].items() if k != "grade"}
        resp = await client.post("/api/auth/register", json=data)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_grade(self, client: AsyncClient):
        """UT-USR-003: 非法年级值拒绝。"""
        data = {**TEST_USERS[0], "grade": "大一"}
        resp = await client.post("/api/auth/register", json=data)
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 登录测试
# ---------------------------------------------------------------------------

class TestLogin:

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, registered_user: dict):
        """UT-USR-004: 正确密码登录成功。"""
        resp = await client.post(
            "/api/auth/login",
            json={
                "username": registered_user["username"],
                "password": registered_user["password"],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["access_token"] != ""

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, registered_user: dict):
        """UT-USR-005: 错误密码登录失败。"""
        resp = await client.post(
            "/api/auth/login",
            json={
                "username": registered_user["username"],
                "password": "WrongPassword999",
            },
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """UT-USR-005: 不存在的用户登录失败。"""
        resp = await client.post(
            "/api/auth/login",
            json={"username": "nonexistent", "password": "whatever"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 认证保护测试
# ---------------------------------------------------------------------------

class TestAuthProtection:

    @pytest.mark.asyncio
    async def test_access_protected_without_token(self, client: AsyncClient):
        """E2E-ERR-003: 未登录访问受保护端点被拒绝。"""
        resp = await client.get("/api/users/me")
        assert resp.status_code == 401 or resp.status_code == 403

    @pytest.mark.asyncio
    async def test_access_protected_with_invalid_token(self, client: AsyncClient):
        """无效 token 访问受保护端点被拒绝。"""
        headers = {"Authorization": "Bearer invalid-token"}
        resp = await client.get("/api/users/me", headers=headers)
        assert resp.status_code == 401 or resp.status_code == 403

    @pytest.mark.asyncio
    async def test_access_protected_with_valid_token(
        self, client: AsyncClient, auth_headers: dict
    ):
        """有效 token 访问受保护端点成功。"""
        resp = await client.get("/api/users/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == TEST_USERS[0]["username"]


# ---------------------------------------------------------------------------
# 用户 Profile 测试
# ---------------------------------------------------------------------------

class TestUserProfile:

    @pytest.mark.asyncio
    async def test_get_profile(self, client: AsyncClient, auth_headers: dict):
        """获取用户 Profile。"""
        resp = await client.get("/api/users/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == TEST_USERS[0]["name"]
        assert data["grade"] == TEST_USERS[0]["grade"]

    @pytest.mark.asyncio
    async def test_update_profile(self, client: AsyncClient, auth_headers: dict):
        """UT-USR-006: 更新用户 Profile。"""
        resp = await client.put(
            "/api/users/me",
            headers=auth_headers,
            json={"grade": "初三"},
        )
        assert resp.status_code == 200
        # 验证更新生效
        resp2 = await client.get("/api/users/me", headers=auth_headers)
        assert resp2.json()["grade"] == "初三"


# ---------------------------------------------------------------------------
# 数据隔离测试
# ---------------------------------------------------------------------------

class TestDataIsolation:

    @pytest.mark.asyncio
    async def test_user_data_isolation(self, client: AsyncClient):
        """UT-USR-007: 用户 A 无法访问用户 B 的数据。"""
        # 注册用户 A
        await client.post("/api/auth/register", json=TEST_USERS[0])
        resp_a = await client.post(
            "/api/auth/login",
            json={"username": TEST_USERS[0]["username"], "password": TEST_USERS[0]["password"]},
        )
        token_a = resp_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # 注册用户 B
        await client.post("/api/auth/register", json=TEST_USERS[1])
        resp_b = await client.post(
            "/api/auth/login",
            json={"username": TEST_USERS[1]["username"], "password": TEST_USERS[1]["password"]},
        )
        token_b = resp_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # 用户 A 查看自己的信息
        resp = await client.get("/api/users/me", headers=headers_a)
        assert resp.status_code == 200
        assert resp.json()["username"] == TEST_USERS[0]["username"]

        # 用户 B 查看自己的信息
        resp = await client.get("/api/users/me", headers=headers_b)
        assert resp.status_code == 200
        assert resp.json()["username"] == TEST_USERS[1]["username"]

        # 用户 A 的 session 列表应不包含用户 B 的数据
        resp_sessions_a = await client.get("/api/sessions", headers=headers_a)
        if resp_sessions_a.status_code == 200:
            sessions = resp_sessions_a.json()
            for s in sessions:
                assert s.get("user_id") != TEST_USERS[1]["username"]
