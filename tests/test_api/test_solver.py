"""
解题 API 端点集成测试。

覆盖测试规格:
  - IT-SOL-001 ~ IT-SOL-007: 解题管线 API 层
  - E2E-001 ~ E2E-005: 核心解题流程
  - E2E-ERR-001, E2E-ERR-002, E2E-ERR-005: 异常流程
"""

import io
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


def _mock_solve_result(**overrides):
    """创建模拟的解题结果。"""
    base = {
        "session_id": "test-session-id",
        "subject": "数学",
        "question": "x^2 - 5x + 6 = 0",
        "content": "第一步: ...\n第二步: ...\n答案: x=2 或 x=3",
        "mode": "direct",
        "verified": True,
        "attempts": 1,
        "sympy_result": None,
    }
    base.update(overrides)
    return base


@pytest.fixture
def mock_solver_service():
    """Mock SolverService 以避免真实 LLM 调用。"""
    with patch("aixue.api.endpoints.solver.SolverService") as MockCls:
        instance = MockCls.return_value
        instance.solve = AsyncMock(return_value=_mock_solve_result())
        instance.follow_up = AsyncMock(return_value={
            "session_id": "test-session-id",
            "content": "因式分解是将多项式分解为...",
            "mode": "direct",
        })
        yield instance


# ---------------------------------------------------------------------------
# 解题端点测试
# ---------------------------------------------------------------------------

class TestSolveEndpoint:

    @pytest.mark.asyncio
    async def test_solve_with_text_input(
        self, client: AsyncClient, auth_headers: dict, mock_solver_service
    ):
        """文本输入解题。"""
        resp = await client.post(
            "/api/solve",
            headers=auth_headers,
            data={
                "text": "x^2 - 5x + 6 = 0",
                "subject": "数学",
                "mode": "direct",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data
        assert "content" in data

    @pytest.mark.asyncio
    async def test_solve_with_image_upload(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_math_image: bytes,
        mock_solver_service,
    ):
        """E2E-001: 图片上传解题。"""
        resp = await client.post(
            "/api/solve",
            headers=auth_headers,
            data={"mode": "direct"},
            files={"image": ("math.png", io.BytesIO(sample_math_image), "image/png")},
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_solve_socratic_mode(
        self, client: AsyncClient, auth_headers: dict, mock_solver_service
    ):
        """E2E-002: 苏格拉底引导模式。"""
        mock_solver_service.solve = AsyncMock(
            return_value=_mock_solve_result(mode="socratic")
        )
        resp = await client.post(
            "/api/solve",
            headers=auth_headers,
            data={
                "text": "2x + 3 = 7",
                "subject": "数学",
                "mode": "socratic",
            },
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_solve_direct_mode(
        self, client: AsyncClient, auth_headers: dict, mock_solver_service
    ):
        """E2E-003: 完整解答模式。"""
        resp = await client.post(
            "/api/solve",
            headers=auth_headers,
            data={
                "text": "2x + 3 = 7",
                "subject": "数学",
                "mode": "direct",
            },
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_solve_physics(
        self, client: AsyncClient, auth_headers: dict, mock_solver_service
    ):
        """E2E-005: 理化生解题。"""
        mock_solver_service.solve = AsyncMock(
            return_value=_mock_solve_result(subject="物理")
        )
        resp = await client.post(
            "/api/solve",
            headers=auth_headers,
            data={
                "text": "一个质量为 2kg 的物体受 10N 推力, 求加速度",
                "subject": "物理",
                "mode": "direct",
            },
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_solve_no_input(self, client: AsyncClient, auth_headers: dict):
        """无输入(既无文本也无图片)应返回错误。"""
        resp = await client.post(
            "/api/solve",
            headers=auth_headers,
            data={"mode": "direct"},
        )
        assert resp.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_solve_oversized_image(
        self, client: AsyncClient, auth_headers: dict, oversized_image: bytes
    ):
        """E2E-ERR-005: 大文件上传拒绝。"""
        resp = await client.post(
            "/api/solve",
            headers=auth_headers,
            data={"mode": "direct"},
            files={"image": ("big.png", io.BytesIO(oversized_image), "image/png")},
        )
        assert resp.status_code in (400, 413, 422)


# ---------------------------------------------------------------------------
# 追问端点测试
# ---------------------------------------------------------------------------

class TestFollowUpEndpoint:

    @pytest.mark.asyncio
    async def test_follow_up(
        self, client: AsyncClient, auth_headers: dict, mock_solver_service
    ):
        """IT-SOL-006: 多轮追问。"""
        resp = await client.post(
            "/api/solve/test-session-id/follow-up",
            headers=auth_headers,
            data={"message": "为什么用因式分解法？"},
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_follow_up_invalid_session(
        self, client: AsyncClient, auth_headers: dict, mock_solver_service
    ):
        """追问不存在的会话返回 404。"""
        mock_solver_service.follow_up = AsyncMock(
            return_value={"error": "会话不存在"}
        )
        resp = await client.post(
            "/api/solve/nonexistent-session/follow-up",
            headers=auth_headers,
            data={"message": "test"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_follow_up_missing_message(
        self, client: AsyncClient, auth_headers: dict
    ):
        """追问缺少消息字段应返回 422。"""
        resp = await client.post(
            "/api/solve/some-session/follow-up",
            headers=auth_headers,
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 解题历史端点测试
# ---------------------------------------------------------------------------

class TestSessionHistory:

    @pytest.mark.asyncio
    async def test_list_sessions(self, client: AsyncClient, auth_headers: dict):
        """E2E-007: 解题历史列表。"""
        resp = await client.get("/api/sessions", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @pytest.mark.asyncio
    async def test_get_nonexistent_session(
        self, client: AsyncClient, auth_headers: dict
    ):
        """查看不存在的会话返回 404。"""
        resp = await client.get(
            "/api/sessions/nonexistent-id", headers=auth_headers
        )
        assert resp.status_code == 404
