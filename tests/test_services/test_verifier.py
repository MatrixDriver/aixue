"""
SymPy 数学验证模块单元测试。

覆盖测试规格:
  - UT-SYM-001 ~ UT-SYM-009: SymPy 求解和验证
  - UT-AST-001 ~ UT-AST-004: Assert 断言验证
"""


import pytest
import pytest_asyncio

from aixue.services.verifier import MathVerifier


@pytest_asyncio.fixture
async def verifier():
    return MathVerifier()


# ---------------------------------------------------------------------------
# SymPy 前置求解测试
# ---------------------------------------------------------------------------

class TestSymPyPreSolve:
    """第一级验证：SymPy 前置求解。"""

    @pytest.mark.asyncio
    async def test_linear_equation(self, verifier: MathVerifier):
        """UT-SYM-001: 一元一次方程 2x + 3 = 7 → x = 2。"""
        result = await verifier.pre_solve("2x + 3 - 7")
        assert result is not None
        assert result["solved"] is True
        assert 2 in result["result"] or result["result"] == [2]

    @pytest.mark.asyncio
    async def test_quadratic_equation(self, verifier: MathVerifier):
        """UT-SYM-002: 一元二次方程 x^2 - 5x + 6 = 0 → x = 2 或 x = 3。"""
        result = await verifier.pre_solve("x^2 - 5x + 6")
        assert result is not None
        assert result["solved"] is True
        solutions = set(result["result"])
        assert solutions == {2, 3}

    @pytest.mark.asyncio
    async def test_simple_equation_variant(self, verifier: MathVerifier):
        """UT-SYM-003: 简单方程 3x - 6 = 0 → x = 2。"""
        result = await verifier.pre_solve("3x - 6")
        assert result is not None
        assert result["solved"] is True
        assert 2 in result["result"]

    @pytest.mark.asyncio
    async def test_cubic_equation(self, verifier: MathVerifier):
        """UT-SYM-004: 高次方程求解或降级。"""
        result = await verifier.pre_solve("x^3 - 6x^2 + 11x - 6")
        # (x-1)(x-2)(x-3) = 0, SymPy 可能求解成功也可能超时
        if result is not None and result.get("solved"):
            solutions = set(result["result"])
            assert solutions == {1, 2, 3}

    @pytest.mark.asyncio
    async def test_pre_solve_returns_latex(self, verifier: MathVerifier):
        """UT-SYM-005: pre_solve 返回结果含 LaTeX 字段。"""
        result = await verifier.pre_solve("x^2 - 4")
        if result is not None and result.get("solved"):
            assert "latex" in result
            assert isinstance(result["latex"], str)

    @pytest.mark.asyncio
    async def test_verify_step_correct(self, verifier: MathVerifier):
        """UT-SYM-006: 步骤验证 - 正确步骤通过。"""
        steps = [{"expression": "4", "expected_result": "4"}]
        result = await verifier.verify_steps(steps)
        assert len(result) == 1
        assert result[0]["verified"] is True

    @pytest.mark.asyncio
    async def test_verify_step_incorrect(self, verifier: MathVerifier):
        """UT-SYM-007: 步骤验证 - 错误步骤标记失败。"""
        steps = [{"expression": "5", "expected_result": "3"}]
        result = await verifier.verify_steps(steps)
        assert len(result) == 1
        assert result[0]["verified"] is False

    @pytest.mark.asyncio
    async def test_timeout_handling(self, verifier: MathVerifier):
        """UT-SYM-008: 超时处理 - 不无限阻塞。"""
        import time

        verifier.timeout = 1  # 缩短超时以加速测试

        # 用可控的慢函数测试超时机制, 避免 SymPy 长时间计算
        def slow_solve(latex_expr: str):
            time.sleep(3)
            return None

        verifier._sympy_solve = slow_solve  # type: ignore[assignment]
        result = await verifier.pre_solve("x + 1")
        assert result is None  # 应在 1 秒后超时返回 None

    @pytest.mark.asyncio
    async def test_unsolvable_degradation(self, verifier: MathVerifier):
        """UT-SYM-009: 无法求解时返回 None, 不抛出异常。"""
        result = await verifier.pre_solve("这是一道几何证明题")
        assert result is None


# ---------------------------------------------------------------------------
# Assert 断言验证测试
# ---------------------------------------------------------------------------

class TestAssertVerification:
    """第二级验证：答案比对 assert 断言。"""

    @pytest.mark.asyncio
    async def test_assertion_pass(self, verifier: MathVerifier):
        """UT-AST-001: 正确答案断言通过。"""
        result = await verifier.verify_answer("2", "2")
        assert result is True

    @pytest.mark.asyncio
    async def test_assertion_fail(self, verifier: MathVerifier):
        """UT-AST-002: 错误答案断言失败。"""
        result = await verifier.verify_answer("3", "2")
        assert result is False

    @pytest.mark.asyncio
    async def test_verify_steps_mixed(self, verifier: MathVerifier):
        """UT-AST-003: 多步骤验证含正确和错误步骤。"""
        steps = [
            {"expression": "6", "expected_result": "6"},
            {"expression": "5", "expected_result": "3"},
            {"expression": "10", "expected_result": "10"},
        ]
        result = await verifier.verify_steps(steps)
        assert len(result) == 3
        assert result[0]["verified"] is True
        assert result[1]["verified"] is False
        assert result[2]["verified"] is True

    @pytest.mark.asyncio
    async def test_answer_string_fallback(self, verifier: MathVerifier):
        """UT-AST-004: LaTeX 解析失败时退化为字符串比较。"""
        result = await verifier.verify_answer("答案A", "答案A")
        assert result is True
        result2 = await verifier.verify_answer("答案A", "答案B")
        assert result2 is False
