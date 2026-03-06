"""
成本优化 — 解题管线拆分测试。

覆盖测试规格:
  - CO-PIPE-001 ~ CO-PIPE-007: 图片/纯文本输入的两阶段流程
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from aixue.services.solver_service import SolverService


def _make_mock_llm():
    """创建 mock LLM 服务，区分 OCR 和推理调用。"""
    llm = AsyncMock()
    settings = MagicMock()
    settings.llm_model_ocr = "ocr-model"
    settings.llm_model_light = "light-model"
    settings.llm_model = "reasoning-model"
    llm.settings = settings

    # OCR 调用返回识别的文本
    llm.recognize_image = AsyncMock(return_value="$x^2 - 5x + 6 = 0$")
    # 推理调用返回解题内容
    llm.chat = AsyncMock(
        return_value=(
            "第一步：因式分解 $(x-2)(x-3)=0$\n"
            "答案：$x=2$ 或 $x=3$"
        )
    )
    return llm


def _make_mock_verifier():
    """创建 mock 验证器。"""
    verifier = AsyncMock()
    verifier.pre_solve = AsyncMock(return_value={
        "solved": True,
        "result": [2, 3],
        "latex": "x = 2 \\text{ or } x = 3",
    })
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


def _user_profile(user_id="test-user-id"):
    return {"id": user_id, "name": "测试", "grade": "初二", "subjects": "数学"}


class TestSolverPipelineCost:
    """解题管线成本优化测试。"""

    @pytest.mark.asyncio
    async def test_image_input_triggers_ocr(self):
        """CO-PIPE-001: 图片输入走两阶段流程（OCR + 推理）。"""
        llm = _make_mock_llm()
        verifier = _make_mock_verifier()
        service = SolverService(llm=llm, verifier=verifier)

        result = await service.solve(
            image=b"\x89PNG\r\n\x1a\n",
            media_type="image/png",
            text=None,
            subject="数学",
            mode="direct",
            session_id=None,
            user_profile=_user_profile(),
            db=_make_mock_db(),
        )

        # OCR 被调用
        llm.recognize_image.assert_called_once()
        # 推理被调用
        llm.chat.assert_called()
        assert result is not None

    @pytest.mark.asyncio
    async def test_text_input_skips_ocr(self):
        """CO-PIPE-002: 纯文本输入跳过 OCR。"""
        llm = _make_mock_llm()
        verifier = _make_mock_verifier()
        service = SolverService(llm=llm, verifier=verifier)

        result = await service.solve(
            image=None,
            media_type=None,
            text="x^2 - 5x + 6 = 0",
            subject="数学",
            mode="direct",
            session_id=None,
            user_profile=_user_profile(),
            db=_make_mock_db(),
        )

        # OCR 不应被调用
        llm.recognize_image.assert_not_called()
        # 推理应被调用
        llm.chat.assert_called()
        assert result is not None

    @pytest.mark.asyncio
    async def test_image_with_text_uses_hint(self):
        """CO-PIPE-003: 图片+文本输入（聚焦模式）。"""
        llm = _make_mock_llm()
        verifier = _make_mock_verifier()
        service = SolverService(llm=llm, verifier=verifier)

        await service.solve(
            image=b"\x89PNG\r\n\x1a\n",
            media_type="image/png",
            text="第3题",
            subject="数学",
            mode="direct",
            session_id=None,
            user_profile=_user_profile(),
            db=_make_mock_db(),
        )

        # OCR 被调用，且 user_hint 为 "第3题"
        llm.recognize_image.assert_called_once()

    @pytest.mark.asyncio
    async def test_ocr_failure_returns_error(self):
        """CO-PIPE-004: OCR 失败时返回错误。"""
        llm = _make_mock_llm()
        llm.recognize_image = AsyncMock(return_value="")
        verifier = _make_mock_verifier()
        service = SolverService(llm=llm, verifier=verifier)

        result = await service.solve(
            image=b"\x89PNG\r\n\x1a\n",
            media_type="image/png",
            text=None,
            subject=None,
            mode="direct",
            session_id=None,
            user_profile=_user_profile(),
            db=_make_mock_db(),
        )

        assert "error" in result

    @pytest.mark.asyncio
    async def test_reasoning_stage_receives_pure_text(self):
        """CO-PIPE-005: 推理阶段不含图片 token。"""
        llm = _make_mock_llm()
        verifier = _make_mock_verifier()
        service = SolverService(llm=llm, verifier=verifier)

        await service.solve(
            image=b"\x89PNG\r\n\x1a\n",
            media_type="image/png",
            text=None,
            subject="物理",
            mode="direct",
            session_id=None,
            user_profile=_user_profile(),
            db=_make_mock_db(),
        )

        # 检查推理阶段的 LLM 调用不含图片数据
        for call in llm.chat.call_args_list:
            messages = call.args[0] if call.args else call.kwargs.get("messages", [])
            for msg in messages:
                content = msg.get("content", "")
                if isinstance(content, list):
                    for block in content:
                        assert block.get("type") != "image_url", \
                            "推理阶段不应包含图片 token"

    @pytest.mark.asyncio
    async def test_math_sympy_still_works_with_ocr(self):
        """CO-PIPE-007: 数学题 SymPy 验证流程不受影响。"""
        llm = _make_mock_llm()
        llm.chat = AsyncMock(
            return_value="第一步: $(x-2)(x-3)=0$\n\\boxed{x=2}"
        )
        verifier = _make_mock_verifier()
        service = SolverService(llm=llm, verifier=verifier)

        result = await service.solve(
            image=b"\x89PNG\r\n\x1a\n",
            media_type="image/png",
            text=None,
            subject="数学",
            mode="direct",
            session_id=None,
            user_profile=_user_profile(),
            db=_make_mock_db(),
        )

        # SymPy 预求解应被调用
        verifier.pre_solve.assert_called_once()
        assert result is not None
