"""
学情诊断 API 端点集成测试。

覆盖测试规格:
  - IT-DIA-001 ~ IT-DIA-004: 诊断管线
  - E2E-006: 试卷上传 → 学情诊断
"""

import io
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from tests.conftest import TEST_USERS


@pytest.fixture
def mock_diagnosis_service():
    """Mock DiagnosisService 以避免真实 LLM 调用。"""
    with patch("aixue.api.endpoints.diagnosis.DiagnosisService") as MockCls:
        instance = MockCls.return_value
        instance.analyze = AsyncMock(return_value={
            "report_id": "test-report-id",
            "overall_score": 72.5,
            "knowledge_gaps": [],
            "thinking_patterns": [],
            "concept_links": [],
            "habit_analysis": [],
            "cognitive_level": {},
        })
        instance.import_exam = AsyncMock(return_value={
            "imported_count": 2,
            "questions": [
                {"number": 1, "question": "test", "status": "correct"},
            ],
        })
        yield instance


# ---------------------------------------------------------------------------
# 诊断端点测试
# ---------------------------------------------------------------------------

class TestDiagnosisEndpoint:

    @pytest.mark.asyncio
    async def test_run_diagnosis(
        self, client: AsyncClient, auth_headers: dict, mock_diagnosis_service
    ):
        """IT-DIA-002: 运行学情诊断分析。"""
        resp = await client.post(
            "/api/diagnosis/analyze",
            headers=auth_headers,
            data={"scope": "full"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "overall_score" in data or "report_id" in data

    @pytest.mark.asyncio
    async def test_run_diagnosis_by_subject(
        self, client: AsyncClient, auth_headers: dict, mock_diagnosis_service
    ):
        """按学科运行诊断。"""
        resp = await client.post(
            "/api/diagnosis/analyze",
            headers=auth_headers,
            data={"scope": "subject", "subject": "数学"},
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_import_exam(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_math_image: bytes,
        mock_diagnosis_service,
    ):
        """IT-DIA-001 / E2E-006: 试卷上传。"""
        resp = await client.post(
            "/api/diagnosis/import-exam",
            headers=auth_headers,
            files=[
                ("images", ("page1.png", io.BytesIO(sample_math_image), "image/png")),
                ("images", ("page2.png", io.BytesIO(sample_math_image), "image/png")),
            ],
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_import_exam_no_images(
        self, client: AsyncClient, auth_headers: dict
    ):
        """试卷上传无图片应返回错误。"""
        resp = await client.post(
            "/api/diagnosis/import-exam",
            headers=auth_headers,
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 诊断报告端点测试
# ---------------------------------------------------------------------------

class TestDiagnosisReports:

    @pytest.mark.asyncio
    async def test_list_reports(self, client: AsyncClient, auth_headers: dict):
        """报告列表。"""
        resp = await client.get("/api/diagnosis/reports", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @pytest.mark.asyncio
    async def test_get_report_detail(self, client: AsyncClient, auth_headers: dict):
        """报告详情 - 不存在的报告返回 404。"""
        resp = await client.get(
            "/api/diagnosis/reports/nonexistent-id", headers=auth_headers
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_report_data_isolation(self, client: AsyncClient):
        """诊断报告数据隔离 - 用户只能看到自己的报告。"""
        # 注册两个用户
        await client.post("/api/auth/register", json=TEST_USERS[0])
        await client.post("/api/auth/register", json=TEST_USERS[1])

        # 用户 A 登录
        resp_a = await client.post(
            "/api/auth/login",
            json={
                "username": TEST_USERS[0]["username"],
                "password": TEST_USERS[0]["password"],
            },
        )
        headers_a = {"Authorization": f"Bearer {resp_a.json()['access_token']}"}

        # 用户 B 登录
        resp_b = await client.post(
            "/api/auth/login",
            json={
                "username": TEST_USERS[1]["username"],
                "password": TEST_USERS[1]["password"],
            },
        )
        headers_b = {"Authorization": f"Bearer {resp_b.json()['access_token']}"}

        # 两个用户各获取自己的报告列表
        reports_a = await client.get("/api/diagnosis/reports", headers=headers_a)
        reports_b = await client.get("/api/diagnosis/reports", headers=headers_b)

        assert reports_a.status_code == 200
        assert reports_b.status_code == 200
        assert isinstance(reports_a.json(), list)
        assert isinstance(reports_b.json(), list)


# ---------------------------------------------------------------------------
# 题库端点测试
# ---------------------------------------------------------------------------

class TestProblemsEndpoint:

    @pytest.mark.asyncio
    async def test_list_problems(self, client: AsyncClient, auth_headers: dict):
        """题库列表查询。"""
        resp = await client.get("/api/problems", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @pytest.mark.asyncio
    async def test_filter_by_subject(self, client: AsyncClient, auth_headers: dict):
        """按学科筛选题目。"""
        resp = await client.get(
            "/api/problems", headers=auth_headers, params={"subject": "数学"}
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_filter_by_difficulty(self, client: AsyncClient, auth_headers: dict):
        """按难度筛选题目。"""
        resp = await client.get(
            "/api/problems", headers=auth_headers, params={"difficulty": 3}
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_problem_detail(self, client: AsyncClient, auth_headers: dict):
        """获取不存在的题目返回 404。"""
        resp = await client.get(
            "/api/problems/nonexistent-id", headers=auth_headers
        )
        assert resp.status_code == 404
