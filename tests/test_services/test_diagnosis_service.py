"""
学情诊断服务单元测试。

覆盖测试规格:
  - IT-DIA-001 ~ IT-DIA-004: 学情诊断集成
  - QA-DIA-001 ~ QA-DIA-003: 诊断质量(框架)
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from aixue.services.diagnosis_service import DiagnosisService


@pytest_asyncio.fixture
async def mock_llm():
    llm = AsyncMock()
    llm.chat = AsyncMock(
        return_value='{"knowledge_gaps": ["一元二次方程"], "weak_points": ["韦达定理"]}'
    )
    llm.recognize_image = AsyncMock(
        return_value=(
            '[{"number": 1, "question": "x^2-3x+2=0", '
            '"student_answer": "x=1", "correct_answer": "x=1 或 x=2", '
            '"status": "incorrect"}]'
        )
    )
    return llm


@pytest_asyncio.fixture
async def diagnosis_service(mock_llm):
    return DiagnosisService(llm=mock_llm)


def _make_mock_record(**kwargs):
    """创建模拟的解题记录。"""
    record = MagicMock()
    record.verification_status = kwargs.get("verification_status", "pending")
    record.question_text = kwargs.get("question_text", "测试题目")
    record.subject = kwargs.get("subject", "数学")
    return record


# ---------------------------------------------------------------------------
# 诊断管线测试
# ---------------------------------------------------------------------------

class TestDiagnosisPipeline:

    @pytest.mark.asyncio
    async def test_cold_start_llm_analysis(self, diagnosis_service, mock_llm):
        """IT-DIA-004: 数据不足时使用 LLM 基础分析。"""
        mock_db = AsyncMock()

        # Mock user query
        mock_user = MagicMock()
        mock_user.grade = "初二"
        user_result = MagicMock()
        user_result.scalar_one_or_none.return_value = mock_user

        # Mock records query (5 条记录)
        mock_records = [_make_mock_record() for _ in range(5)]
        records_result = MagicMock()
        records_result.scalars.return_value.all.return_value = mock_records

        mock_db.execute = AsyncMock(side_effect=[user_result, records_result])

        # Mock 报告保存
        mock_report = MagicMock()
        mock_report.id = "report-1"

        with patch.object(
            diagnosis_service,
            "_save_report",
            new_callable=AsyncMock,
            return_value=mock_report,
        ):
            result = await diagnosis_service.analyze(
                user_id="user1",
                scope="full",
                subject=None,
                db=mock_db,
            )

        assert result is not None
        # LLM 被调用做分析
        mock_llm.chat.assert_called()

    @pytest.mark.asyncio
    async def test_full_diagnosis_analysis(self, diagnosis_service, mock_llm):
        """IT-DIA-002: 数据充足时生成诊断报告。"""
        mock_db = AsyncMock()

        mock_user = MagicMock()
        mock_user.grade = "初二"
        user_result = MagicMock()
        user_result.scalar_one_or_none.return_value = mock_user

        mock_records = [_make_mock_record(subject="数学") for _ in range(25)]
        records_result = MagicMock()
        records_result.scalars.return_value.all.return_value = mock_records

        mock_db.execute = AsyncMock(side_effect=[user_result, records_result])

        mock_llm.chat = AsyncMock(
            return_value=(
                '{"overall_score": 72.5, "knowledge_gaps": [], '
                '"thinking_patterns": [], "habit_analysis": [], '
                '"cognitive_level": {}}'
            )
        )

        mock_report = MagicMock()
        mock_report.id = "report-2"

        with patch.object(
            diagnosis_service,
            "_save_report",
            new_callable=AsyncMock,
            return_value=mock_report,
        ):
            result = await diagnosis_service.analyze(
                user_id="user1",
                scope="full",
                subject="数学",
                db=mock_db,
            )

        assert result is not None
        assert "report_id" in result

    @pytest.mark.asyncio
    async def test_exam_import(self, diagnosis_service, mock_llm):
        """IT-DIA-001: 试卷导入完整流程。"""
        mock_images = [
            (b"fake_image_1", "image/png"),
            (b"fake_image_2", "image/jpeg"),
        ]
        result = await diagnosis_service.import_exam(
            user_id="user1",
            images=mock_images,
            db=AsyncMock(),
        )
        assert result is not None
        assert "imported_count" in result
        # LLM 识别被调用 (每张图片一次)
        assert mock_llm.recognize_image.call_count == 2

    @pytest.mark.asyncio
    async def test_no_records_returns_error(self, diagnosis_service):
        """IT-DIA-003: 无解题记录时返回提示。"""
        mock_db = AsyncMock()

        mock_user = MagicMock()
        mock_user.grade = "初二"
        user_result = MagicMock()
        user_result.scalar_one_or_none.return_value = mock_user

        records_result = MagicMock()
        records_result.scalars.return_value.all.return_value = []

        mock_db.execute = AsyncMock(side_effect=[user_result, records_result])

        result = await diagnosis_service.analyze(
            user_id="user1",
            scope="full",
            subject=None,
            db=mock_db,
        )
        assert "error" in result

    @pytest.mark.asyncio
    async def test_user_not_found_returns_error(self, diagnosis_service):
        """用户不存在时返回错误。"""
        mock_db = AsyncMock()

        user_result = MagicMock()
        user_result.scalar_one_or_none.return_value = None

        mock_db.execute = AsyncMock(return_value=user_result)

        result = await diagnosis_service.analyze(
            user_id="nonexistent",
            scope="full",
            subject=None,
            db=mock_db,
        )
        assert "error" in result
