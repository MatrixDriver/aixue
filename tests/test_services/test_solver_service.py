"""
解题服务单元测试。

覆盖测试规格:
  - IT-SOL-001 ~ IT-SOL-007: 解题管线集成
  - IT-PER-001 ~ IT-PER-002: 年级个性化
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from aixue.services.solver_service import SolverService


@pytest_asyncio.fixture
async def mock_llm():
    """Mock LLM 服务。"""
    llm = AsyncMock()
    llm.chat = AsyncMock(
        return_value=(
            "第一步：解方程 $x^2 - 5x + 6 = 0$\n"
            "第二步：因式分解 $(x-2)(x-3)=0$\n"
            "答案：$x=2$ 或 $x=3$"
        )
    )
    llm.recognize_image = AsyncMock(return_value="x^2 - 5x + 6 = 0")
    return llm


@pytest_asyncio.fixture
async def mock_verifier():
    """Mock 验证器。"""
    verifier = AsyncMock()
    verifier.pre_solve = AsyncMock(return_value={
        "solved": True,
        "result": [2, 3],
        "latex": "x = 2 \\text{ or } x = 3",
    })
    verifier.verify_answer = AsyncMock(return_value=True)
    return verifier


def _make_mock_db():
    """创建合适的 mock 数据库会话。"""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


def _user_profile(user_id="test-user-id"):
    return {"id": user_id, "name": "测试", "grade": "初二", "subjects": "数学"}


@pytest_asyncio.fixture
async def solver_service(mock_llm, mock_verifier):
    """创建带 mock 依赖的 SolverService。"""
    return SolverService(llm=mock_llm, verifier=mock_verifier)


# ---------------------------------------------------------------------------
# 解题管线测试
# ---------------------------------------------------------------------------

class TestSolverPipeline:
    """解题管线集成测试。"""

    @pytest.mark.asyncio
    async def test_math_full_pipeline(self, solver_service, mock_llm, mock_verifier):
        """IT-SOL-001: 完整数学解题管线。"""
        result = await solver_service.solve(
            image=None,
            media_type=None,
            text="x^2 - 5x + 6 = 0",
            subject="数学",
            mode="direct",
            session_id=None,
            user_profile=_user_profile(),
            db=_make_mock_db(),
        )
        assert result is not None
        assert "content" in result
        # SymPy 预求解被调用
        mock_verifier.pre_solve.assert_called_once()
        # LLM 被调用生成解题步骤
        mock_llm.chat.assert_called()

    @pytest.mark.asyncio
    async def test_math_sympy_degradation(self, solver_service, mock_verifier, mock_llm):
        """IT-SOL-002: SymPy 无法求解时降级。"""
        mock_verifier.pre_solve = AsyncMock(return_value=None)
        result = await solver_service.solve(
            image=None,
            media_type=None,
            text="证明三角形 ABC 全等于三角形 DEF",
            subject="数学",
            mode="direct",
            session_id=None,
            user_profile=_user_profile(),
            db=_make_mock_db(),
        )
        assert result is not None
        assert "content" in result

    @pytest.mark.asyncio
    async def test_physics_pipeline(self, solver_service, mock_llm, mock_verifier):
        """IT-SOL-003: 理化生直接走 LLM, 无 SymPy 调用。"""
        result = await solver_service.solve(
            image=None,
            media_type=None,
            text="一个物体在水平面上受力分析",
            subject="物理",
            mode="direct",
            session_id=None,
            user_profile=_user_profile(),
            db=_make_mock_db(),
        )
        assert result is not None
        # 物理题不应调用 SymPy 验证
        mock_verifier.pre_solve.assert_not_called()

    @pytest.mark.asyncio
    async def test_socratic_mode(self, solver_service, mock_llm):
        """IT-SOL-004: 苏格拉底引导模式。"""
        mock_llm.chat = AsyncMock(
            return_value="你能从这道题中找出哪些已知条件呢？试着把它们列出来。"
        )
        result = await solver_service.solve(
            image=None,
            media_type=None,
            text="2x + 3 = 7",
            subject="数学",
            mode="socratic",
            session_id=None,
            user_profile=_user_profile(),
            db=_make_mock_db(),
        )
        assert result is not None
        assert "content" in result

    @pytest.mark.asyncio
    async def test_direct_mode(self, solver_service, mock_llm):
        """IT-SOL-005: 完整解答模式返回完整步骤。"""
        mock_llm.chat = AsyncMock(
            return_value="第一步：移项 2x = 4\n第二步：两边除以 2, x = 2\n\\boxed{x=2}"
        )
        result = await solver_service.solve(
            image=None,
            media_type=None,
            text="2x + 3 = 7",
            subject="数学",
            mode="direct",
            session_id=None,
            user_profile=_user_profile(),
            db=_make_mock_db(),
        )
        assert result is not None
        assert "content" in result

    @pytest.mark.asyncio
    async def test_follow_up_context(self, solver_service, mock_llm):
        """IT-SOL-006: 多轮追问上下文保持。"""
        mock_llm.chat = AsyncMock(
            return_value="因式分解法是将多项式分解为两个因式的乘积..."
        )

        # 构造 mock db 返回合适的会话对象
        mock_db = AsyncMock()
        mock_session = MagicMock()
        mock_session.user_id = "test-user-id"
        mock_session.mode = "direct"
        mock_session.messages = [
            MagicMock(role="user", content="x^2 - 5x + 6 = 0"),
            MagicMock(role="assistant", content="解题步骤..."),
        ]
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        result = await solver_service.follow_up(
            session_id="test-session",
            message_text="为什么用因式分解法？",
            user_profile=_user_profile(),
            db=mock_db,
        )
        assert result is not None
        assert "content" in result
        # LLM 调用时应包含历史消息
        call_args = mock_llm.chat.call_args
        messages = (
            call_args.args[0]
            if call_args.args
            else call_args.kwargs.get("messages", [])
        )
        assert len(messages) >= 2  # 至少包含前轮记录和当前追问

    @pytest.mark.asyncio
    async def test_verification_retry(self, solver_service, mock_verifier, mock_llm):
        """IT-SOL-007: 验证失败触发自动重试。"""
        # LLM 返回含 \boxed{} 的响应, 以便 _verify_response 调用 verify_answer
        mock_llm.chat = AsyncMock(
            return_value="第一步: 移项 2x = 4\n第二步: x = 2\n\\boxed{x=2}"
        )
        # 第一次 verify_answer 失败, 第二次成功
        mock_verifier.verify_answer = AsyncMock(side_effect=[False, True])

        await solver_service.solve(
            image=None,
            media_type=None,
            text="2x + 3 = 7",
            subject="数学",
            mode="direct",
            session_id=None,
            user_profile=_user_profile(),
            db=_make_mock_db(),
        )
        # verify_answer 应被调用 2 次 (第一次失败, 第二次成功)
        assert mock_verifier.verify_answer.call_count == 2
        # LLM 应被调用至少 2 次
        assert mock_llm.chat.call_count >= 2


# ---------------------------------------------------------------------------
# 年级个性化测试
# ---------------------------------------------------------------------------

class TestPersonalization:
    """年级适配测试。"""

    @pytest.mark.asyncio
    async def test_grade_profile_injection(self, solver_service, mock_llm):
        """IT-PER-002: Profile 信息注入到 LLM Prompt 中。"""
        await solver_service.solve(
            image=None,
            media_type=None,
            text="2x + 3 = 7",
            subject="数学",
            mode="direct",
            session_id=None,
            user_profile={
                "id": "u1",
                "name": "张三",
                "grade": "初二",
                "subjects": "数学",
            },
            db=_make_mock_db(),
        )
        # 检查 LLM 调用的 system prompt 或 messages 中包含年级信息
        call_args = mock_llm.chat.call_args
        system = call_args.kwargs.get("system", "")
        messages_str = str(call_args.kwargs.get("messages", []))
        combined = system + messages_str
        assert "初二" in combined or "grade" in combined.lower()
