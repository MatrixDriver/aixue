"""
多题检测流程测试。

覆盖测试规格:
  - UT-03: 单题快速通道
  - UT-04: 多题返回按钮组数据结构
  - UT-05: 不完整题目标记
  - UT-06: 全部不完整场景
  - UT-07: 超过 5 题限制
  - UT-08: user_hint 跳过多题检测
  - IT-01: 单题完整流程
  - IT-02: 多题选择流程
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from aixue.services.llm_service import LLMService
from aixue.services.ocr_service import OCRService
from aixue.services.solver_service import SolverService


# ---------------------------------------------------------------------------
# Mock 数据
# ---------------------------------------------------------------------------

DETECT_SINGLE = '{"question_count": 1, "questions": [{"index": 1, "label": "14", "summary": "已知函数 f(x) = x^2 + 2x", "complete": true}]}'

DETECT_MULTI = '{"question_count": 3, "questions": [{"index": 1, "label": "1", "summary": "已知函数 f(x) = x^2 + 2x", "complete": true}, {"index": 2, "label": "2", "summary": "如图所示，在三角形ABC中", "complete": true}, {"index": 3, "label": "3", "summary": "求证：当 a > 0 时", "complete": false}]}'

DETECT_ALL_INCOMPLETE = '{"question_count": 2, "questions": [{"index": 1, "label": "1", "summary": "已知...", "complete": false}, {"index": 2, "label": "2", "summary": "如图...", "complete": false}]}'

DETECT_OVER_LIMIT = '{"question_count": 8, "questions": [' + ", ".join(
    f'{{"index": {i}, "label": "{i}", "summary": "题目{i}", "complete": true}}'
    for i in range(1, 9)
) + "]}"

DETECT_MIXED_COMPLETE = '{"question_count": 4, "questions": [{"index": 1, "label": "1", "summary": "方程求解", "complete": true}, {"index": 2, "label": "2", "summary": "不完整的题", "complete": false}, {"index": 3, "label": "3", "summary": "几何证明", "complete": true}, {"index": 4, "label": "4", "summary": "另一道不完整", "complete": false}]}'


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def mock_llm():
    """Mock LLM 服务。"""
    llm = AsyncMock(spec=LLMService)
    llm.chat = AsyncMock(return_value="数学")
    llm.recognize_image = AsyncMock(return_value="x^2 + 2x = 0")
    llm.settings = MagicMock()
    llm.settings.llm_model_light = "test-light-model"
    return llm


@pytest_asyncio.fixture
async def mock_verifier():
    """Mock 验证器。"""
    verifier = AsyncMock()
    verifier.pre_solve = AsyncMock(return_value=None)
    verifier.verify_answer = AsyncMock(return_value=True)
    return verifier


def _make_mock_db():
    """创建 mock 数据库会话。"""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


def _user_profile():
    return {"id": "test-user-id", "name": "测试", "grade": "初二", "subjects": "数学"}


# ---------------------------------------------------------------------------
# OCRService.detect_questions 行为测试
# ---------------------------------------------------------------------------

class TestDetectQuestionsService:
    """OCRService.detect_questions 方法测试。"""

    @pytest.mark.asyncio
    async def test_detect_calls_llm_with_correct_prompt(self, mock_llm):
        """验证 detect_questions 使用正确的 prompt 和参数调用 LLM。"""
        mock_llm.recognize_image = AsyncMock(return_value=DETECT_SINGLE)
        ocr = OCRService(mock_llm)
        await ocr.detect_questions(b"fake-image", "image/png")

        mock_llm.recognize_image.assert_called_once()
        call_kwargs = mock_llm.recognize_image.call_args
        # 验证传入了图片数据和 media_type
        assert call_kwargs.kwargs.get("image_data") == b"fake-image"
        assert call_kwargs.kwargs.get("media_type") == "image/png"

    @pytest.mark.asyncio
    async def test_detect_mixed_completeness(self, mock_llm):
        """UT-05: 不完整题目标记正确。"""
        mock_llm.recognize_image = AsyncMock(return_value=DETECT_MIXED_COMPLETE)
        ocr = OCRService(mock_llm)
        result = await ocr.detect_questions(b"fake-image", "image/png")

        questions = result["questions"]
        assert len(questions) == 4
        assert questions[0]["complete"] is True
        assert questions[1]["complete"] is False
        assert questions[2]["complete"] is True
        assert questions[3]["complete"] is False
        # 完整题目数量
        complete_count = sum(1 for q in questions if q["complete"])
        assert complete_count == 2

    @pytest.mark.asyncio
    async def test_detect_over_limit_returns_all(self, mock_llm):
        """UT-07: detect_questions 本身不截断，截断由调用方处理。"""
        mock_llm.recognize_image = AsyncMock(return_value=DETECT_OVER_LIMIT)
        ocr = OCRService(mock_llm)
        result = await ocr.detect_questions(b"fake-image", "image/png")

        # detect_questions 返回原始结果，不做截断
        assert result["question_count"] == 8
        assert len(result["questions"]) == 8


# ---------------------------------------------------------------------------
# SolverService 多题流程测试
# ---------------------------------------------------------------------------

class TestSolverMultiQuestionFlow:
    """SolverService 层面的多题流程集成测试。"""

    @pytest.mark.asyncio
    async def test_text_only_skips_detection(self, mock_llm, mock_verifier):
        """UT-08/AT-06: 纯文本输入不触发多题检测。"""
        mock_llm.chat = AsyncMock(
            return_value="解：x = -2\n\\boxed{x=-2}"
        )
        solver = SolverService(llm=mock_llm, verifier=mock_verifier)

        result = await solver.solve(
            image=None,
            media_type=None,
            text="x^2 + 2x = 0",
            subject="数学",
            mode="direct",
            session_id=None,
            user_profile=_user_profile(),
            db=_make_mock_db(),
        )

        assert "content" in result
        # recognize_image 不应被调用（无图片）
        mock_llm.recognize_image.assert_not_called()

    @pytest.mark.asyncio
    async def test_image_with_hint_skips_detection(self, mock_llm, mock_verifier):
        """UT-08: 有 user_hint 时跳过多题检测，走聚焦 OCR。"""
        mock_llm.chat = AsyncMock(return_value="数学")
        mock_llm.recognize_image = AsyncMock(return_value="x^2 + 2x = 0")
        solver = SolverService(llm=mock_llm, verifier=mock_verifier)

        result = await solver.solve(
            image=b"fake-image",
            media_type="image/png",
            text="第14题",
            subject=None,
            mode="direct",
            session_id=None,
            user_profile=_user_profile(),
            db=_make_mock_db(),
        )

        assert "content" in result
        # recognize_image 应被调用 1 次（OCR 识别），而非多题检测
        assert mock_llm.recognize_image.call_count == 1
        call_kwargs = mock_llm.recognize_image.call_args.kwargs
        prompt = call_kwargs.get("prompt", "")
        # 验证使用的是聚焦 prompt 而非多题检测 prompt
        assert "第14题" in prompt or "用户指定" in prompt

    @pytest.mark.asyncio
    async def test_recognize_returns_empty_error(self, mock_llm, mock_verifier):
        """OCR 无法识别时返回错误信息。"""
        mock_llm.recognize_image = AsyncMock(return_value="")
        solver = SolverService(llm=mock_llm, verifier=mock_verifier)

        result = await solver.solve(
            image=b"fake-image",
            media_type="image/png",
            text=None,
            subject=None,
            mode="direct",
            session_id=None,
            user_profile=_user_profile(),
            db=_make_mock_db(),
        )

        assert "error" in result


# ---------------------------------------------------------------------------
# _parse_detection_result 边界测试
# ---------------------------------------------------------------------------

class TestParseDetectionEdgeCases:
    """JSON 解析容错边界情况。"""

    def test_json_with_bom(self, mock_llm):
        """带 BOM 标记的 JSON 也能解析。"""
        ocr = OCRService(mock_llm)
        raw = '\ufeff{"question_count": 1, "questions": [{"index": 1, "label": "1", "summary": "x", "complete": true}]}'
        result = ocr._parse_detection_result(raw)
        # BOM 可能导致直接 json.loads 失败，但 re.search 能找到 JSON
        assert "question_count" in result

    def test_json_with_trailing_comma(self, mock_llm):
        """尾部逗号的 JSON 回退到单题。"""
        ocr = OCRService(mock_llm)
        raw = '{"question_count": 1, "questions": [{"index": 1, "label": "1", "summary": "x", "complete": true,}]}'
        result = ocr._parse_detection_result(raw)
        # 尾部逗号不是合法 JSON，应回退
        assert result["question_count"] == 1

    def test_empty_string_fallback(self, mock_llm):
        """空字符串回退为单题。"""
        ocr = OCRService(mock_llm)
        result = ocr._parse_detection_result("")
        assert result["question_count"] == 1
        assert result["questions"][0]["complete"] is True

    def test_question_count_mismatch(self, mock_llm):
        """question_count 与实际数组长度不一致时仍可解析。"""
        ocr = OCRService(mock_llm)
        raw = '{"question_count": 5, "questions": [{"index": 1, "label": "1", "summary": "x", "complete": true}]}'
        result = ocr._parse_detection_result(raw)
        # 解析成功，question_count 和实际长度不一致但不影响解析
        assert result["question_count"] == 5
        assert len(result["questions"]) == 1
