"""
成本优化 — OCR 服务测试。

覆盖测试规格:
  - CO-OCR-001 ~ CO-OCR-004: OCR 阶段模型选择与行为
"""

from unittest.mock import AsyncMock, MagicMock, PropertyMock

import pytest

from aixue.services.ocr_service import (
    OCRService,
    RECOGNITION_FOCUSED_PROMPT,
    RECOGNITION_PROMPT,
)


def _make_mock_llm(ocr_model: str = "ocr-model", light_model: str = "light-model"):
    """创建 mock LLM 服务。"""
    llm = AsyncMock()
    settings = MagicMock()
    settings.llm_model_ocr = ocr_model
    settings.llm_model_light = light_model
    settings.llm_model = "reasoning-model"
    llm.settings = settings
    llm.recognize_image = AsyncMock(return_value="$x^2 + 3x - 4 = 0$")
    return llm


class TestOCRServiceCost:
    """OCR 服务成本优化测试。"""

    @pytest.mark.asyncio
    async def test_ocr_returns_structured_text(self):
        """CO-OCR-002: OCR 输出结构化文本。"""
        llm = _make_mock_llm()
        ocr = OCRService(llm)
        result = await ocr.recognize(b"\x89PNG", "image/png")
        assert result  # 非空字符串
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_ocr_empty_result(self):
        """CO-OCR-003: OCR 结果为空时返回空字符串。"""
        llm = _make_mock_llm()
        llm.recognize_image = AsyncMock(return_value="")
        ocr = OCRService(llm)
        result = await ocr.recognize(b"\x89PNG", "image/png")
        assert result == ""

    @pytest.mark.asyncio
    async def test_ocr_focused_prompt_with_hint(self):
        """CO-OCR-004: 聚焦指定题目功能保留。"""
        llm = _make_mock_llm()
        ocr = OCRService(llm)
        await ocr.recognize(b"\x89PNG", "image/png", user_hint="第14题")

        # 检查 recognize_image 调用时的 prompt 参数包含用户提示
        call_args = llm.recognize_image.call_args
        prompt = call_args.kwargs.get("prompt", call_args.args[2] if len(call_args.args) > 2 else "")
        assert "第14题" in prompt
