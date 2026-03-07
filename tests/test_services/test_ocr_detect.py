"""多题检测服务单元测试。"""

from unittest.mock import AsyncMock

import pytest

from aixue.services.llm_service import LLMService
from aixue.services.ocr_service import OCRService


@pytest.fixture
def mock_llm():
    llm = AsyncMock(spec=LLMService)
    return llm


@pytest.fixture
def ocr_service(mock_llm):
    return OCRService(mock_llm)


class TestDetectQuestions:
    """多题检测测试。"""

    @pytest.mark.asyncio
    async def test_single_complete_question(self, ocr_service, mock_llm):
        """单题完整：返回 1 道题。"""
        mock_llm.recognize_image = AsyncMock(
            return_value='{"question_count": 1, "questions": [{"index": 1, "label": "14", "summary": "求解方程", "complete": true}]}'
        )
        result = await ocr_service.detect_questions(b"fake-image", "image/png")
        assert result["question_count"] == 1
        assert len(result["questions"]) == 1
        assert result["questions"][0]["complete"] is True

    @pytest.mark.asyncio
    async def test_multiple_questions(self, ocr_service, mock_llm):
        """多题：返回多道题。"""
        mock_llm.recognize_image = AsyncMock(
            return_value='{"question_count": 3, "questions": [{"index": 1, "label": "1", "summary": "方程", "complete": true}, {"index": 2, "label": "2", "summary": "几何", "complete": true}, {"index": 3, "label": "3", "summary": "不完整", "complete": false}]}'
        )
        result = await ocr_service.detect_questions(b"fake-image", "image/png")
        assert result["question_count"] == 3
        assert len(result["questions"]) == 3
        complete = [q for q in result["questions"] if q["complete"]]
        assert len(complete) == 2

    @pytest.mark.asyncio
    async def test_no_questions(self, ocr_service, mock_llm):
        """无题目：返回空列表。"""
        mock_llm.recognize_image = AsyncMock(
            return_value='{"question_count": 0, "questions": []}'
        )
        result = await ocr_service.detect_questions(b"fake-image", "image/png")
        assert result["question_count"] == 0
        assert len(result["questions"]) == 0

    @pytest.mark.asyncio
    async def test_json_with_markdown_wrapper(self, ocr_service, mock_llm):
        """LLM 返回 markdown 包裹的 JSON 也能解析。"""
        mock_llm.recognize_image = AsyncMock(
            return_value='```json\n{"question_count": 1, "questions": [{"index": 1, "label": "1", "summary": "test", "complete": true}]}\n```'
        )
        result = await ocr_service.detect_questions(b"fake-image", "image/png")
        assert result["question_count"] == 1

    @pytest.mark.asyncio
    async def test_invalid_json_fallback(self, ocr_service, mock_llm):
        """JSON 解析失败时回退为单题。"""
        mock_llm.recognize_image = AsyncMock(
            return_value="这不是 JSON 格式的内容"
        )
        result = await ocr_service.detect_questions(b"fake-image", "image/png")
        assert result["question_count"] == 1
        assert result["questions"][0]["complete"] is True


class TestParseDetectionResult:
    """JSON 解析容错测试。"""

    def test_valid_json(self, ocr_service):
        result = ocr_service._parse_detection_result(
            '{"question_count": 2, "questions": []}'
        )
        assert result["question_count"] == 2

    def test_json_with_extra_text(self, ocr_service):
        result = ocr_service._parse_detection_result(
            '分析结果如下：\n{"question_count": 1, "questions": [{"index": 1, "label": "1", "summary": "x", "complete": true}]}\n以上'
        )
        assert result["question_count"] == 1

    def test_completely_invalid(self, ocr_service):
        result = ocr_service._parse_detection_result("无法解析")
        assert result["question_count"] == 1  # 回退为单题
