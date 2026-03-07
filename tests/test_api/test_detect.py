"""
多题检测 API 端点测试。

覆盖测试规格:
  - AT-01: POST /detect - 多题检测响应
  - AT-04: POST /solve - user_hint 快捷路径（回归）
  - AT-06: 回归 - 纯文本输入不受影响
"""

import io
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


def _mock_detect_result(**overrides):
    """创建模拟的多题检测结果。"""
    base = {
        "question_count": 3,
        "questions": [
            {"index": 1, "label": "1", "summary": "已知函数 f(x) = x^2", "complete": True},
            {"index": 2, "label": "2", "summary": "三角形 ABC 中", "complete": True},
            {"index": 3, "label": "3", "summary": "求证当 a > 0", "complete": False},
        ],
    }
    base.update(overrides)
    return base


def _mock_solve_result(**overrides):
    """创建模拟的解题结果。"""
    base = {
        "session_id": "test-session-id",
        "subject": "数学",
        "question": "x^2 + 2x = 0",
        "content": "解：因式分解得 x(x+2) = 0，所以 x=0 或 x=-2",
        "mode": "direct",
        "verified": False,
        "attempts": 1,
        "sympy_result": None,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# /detect 端点测试
# ---------------------------------------------------------------------------

class TestDetectEndpoint:
    """多题检测 API 端点测试。"""

    @pytest.mark.asyncio
    async def test_detect_requires_auth(self, client: AsyncClient):
        """未认证请求返回 401。"""
        resp = await client.post("/api/detect")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_detect_requires_image(
        self, client: AsyncClient, auth_headers: dict
    ):
        """缺少图片返回 422。"""
        resp = await client.post("/api/detect", headers=auth_headers)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_detect_oversized_image(
        self, client: AsyncClient, auth_headers: dict, oversized_image: bytes
    ):
        """超大图片返回 413。"""
        resp = await client.post(
            "/api/detect",
            headers=auth_headers,
            files={"image": ("big.png", io.BytesIO(oversized_image), "image/png")},
        )
        assert resp.status_code == 413

    @pytest.mark.asyncio
    async def test_detect_returns_question_list(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_math_image: bytes,
    ):
        """AT-01: 上传图片返回题目列表。"""
        with patch("aixue.api.endpoints.solver.LLMService") as MockLLM, \
             patch("aixue.api.endpoints.solver.OCRService") as MockOCR:
            mock_ocr_instance = MockOCR.return_value
            mock_ocr_instance.detect_questions = AsyncMock(
                return_value=_mock_detect_result()
            )

            resp = await client.post(
                "/api/detect",
                headers=auth_headers,
                files={
                    "image": ("math.png", io.BytesIO(sample_math_image), "image/png")
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["question_count"] == 3
        assert len(data["questions"]) == 3
        assert "message" in data
        # 验证每个题目的字段结构
        for q in data["questions"]:
            assert "index" in q
            assert "label" in q
            assert "summary" in q
            assert "complete" in q

    @pytest.mark.asyncio
    async def test_detect_all_incomplete_message(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_math_image: bytes,
    ):
        """全部不完整时返回提示信息。"""
        with patch("aixue.api.endpoints.solver.LLMService"), \
             patch("aixue.api.endpoints.solver.OCRService") as MockOCR:
            mock_ocr_instance = MockOCR.return_value
            mock_ocr_instance.detect_questions = AsyncMock(
                return_value=_mock_detect_result(
                    question_count=2,
                    questions=[
                        {"index": 1, "label": "1", "summary": "...", "complete": False},
                        {"index": 2, "label": "2", "summary": "...", "complete": False},
                    ],
                )
            )

            resp = await client.post(
                "/api/detect",
                headers=auth_headers,
                files={
                    "image": ("math.png", io.BytesIO(sample_math_image), "image/png")
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert "不完整" in data["message"] or "重新拍照" in data["message"]

    @pytest.mark.asyncio
    async def test_detect_over_limit_truncates(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_math_image: bytes,
    ):
        """超过 5 题时截断并提示分批拍照。"""
        questions_8 = [
            {"index": i, "label": str(i), "summary": f"题目{i}", "complete": True}
            for i in range(1, 9)
        ]
        with patch("aixue.api.endpoints.solver.LLMService"), \
             patch("aixue.api.endpoints.solver.OCRService") as MockOCR:
            mock_ocr_instance = MockOCR.return_value
            mock_ocr_instance.detect_questions = AsyncMock(
                return_value={"question_count": 8, "questions": questions_8}
            )

            resp = await client.post(
                "/api/detect",
                headers=auth_headers,
                files={
                    "image": ("math.png", io.BytesIO(sample_math_image), "image/png")
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["questions"]) <= 5
        assert "5" in data["message"] or "分批" in data["message"]

    @pytest.mark.asyncio
    async def test_detect_zero_questions(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_math_image: bytes,
    ):
        """无题目时返回空列表和提示。"""
        with patch("aixue.api.endpoints.solver.LLMService"), \
             patch("aixue.api.endpoints.solver.OCRService") as MockOCR:
            mock_ocr_instance = MockOCR.return_value
            mock_ocr_instance.detect_questions = AsyncMock(
                return_value={"question_count": 0, "questions": []}
            )

            resp = await client.post(
                "/api/detect",
                headers=auth_headers,
                files={
                    "image": ("math.png", io.BytesIO(sample_math_image), "image/png")
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["question_count"] == 0
        assert len(data["questions"]) == 0
        assert "未检测到" in data["message"] or "重新拍照" in data["message"]


# ---------------------------------------------------------------------------
# 回归测试 - 确保现有功能不受影响
# ---------------------------------------------------------------------------

class TestSolveRegressionWithMultiDetect:
    """确保多题检测功能不影响现有解题流程。"""

    @pytest.fixture
    def mock_solver_service(self):
        """Mock SolverService 以避免真实 LLM 调用。"""
        with patch("aixue.api.endpoints.solver.SolverService") as MockCls:
            instance = MockCls.return_value
            instance.solve = AsyncMock(return_value=_mock_solve_result())
            yield instance

    @pytest.mark.asyncio
    async def test_solve_text_only_unchanged(
        self,
        client: AsyncClient,
        auth_headers: dict,
        mock_solver_service,
    ):
        """AT-06: 纯文本解题流程不受多题检测影响。"""
        resp = await client.post(
            "/api/solve",
            headers=auth_headers,
            data={
                "text": "求解 x^2 = 4",
                "subject": "数学",
                "mode": "direct",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data
        assert "content" in data

    @pytest.mark.asyncio
    async def test_solve_with_hint_unchanged(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_math_image: bytes,
        mock_solver_service,
    ):
        """AT-04: 图片 + user_hint 走现有聚焦流程，不触发多题检测。"""
        resp = await client.post(
            "/api/solve",
            headers=auth_headers,
            data={
                "text": "第14题",
                "mode": "direct",
            },
            files={
                "image": ("math.png", io.BytesIO(sample_math_image), "image/png")
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data
        assert "content" in data

    @pytest.mark.asyncio
    async def test_solve_image_only_unchanged(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_math_image: bytes,
        mock_solver_service,
    ):
        """图片无文字的解题请求仍走 /solve 端点正常处理。"""
        resp = await client.post(
            "/api/solve",
            headers=auth_headers,
            data={"mode": "direct"},
            files={
                "image": ("math.png", io.BytesIO(sample_math_image), "image/png")
            },
        )
        assert resp.status_code == 200
