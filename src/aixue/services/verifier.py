"""SymPy 数学验证模块：前置求解、步骤验证、答案比对。"""

import asyncio
import logging
from typing import Any

from sympy import N, latex, simplify, solve, symbols, sympify
from sympy.parsing.latex import parse_latex

from aixue.config import Settings

logger = logging.getLogger(__name__)

settings = Settings()


class MathVerifier:
    """数学验证器：使用 SymPy 对 LLM 生成的解题结果进行交叉验证。"""

    def __init__(self) -> None:
        self.timeout = settings.sympy_timeout

    async def pre_solve(self, question_latex: str) -> dict[str, Any] | None:
        """第一级验证：SymPy 前置求解，获取数学真值。

        Args:
            question_latex: LaTeX 格式的数学表达式

        Returns:
            求解结果字典或 None（无法求解时）
        """
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(self._sympy_solve, question_latex),
                timeout=self.timeout,
            )
            return result
        except asyncio.TimeoutError:
            logger.warning("SymPy 求解超时: timeout=%ds", self.timeout)
            return None
        except Exception:
            logger.exception("SymPy 前置求解异常: latex=%s", question_latex[:100])
            return None

    async def verify_steps(self, steps: list[dict]) -> list[dict]:
        """第二级验证：对关键步骤进行 assert 断言验证。

        Args:
            steps: 解题步骤列表，每步含 expression 和 expected_result

        Returns:
            验证后的步骤列表，每步新增 verified 字段
        """
        verified_steps = []
        for step in steps:
            expr_str = step.get("expression", "")
            expected = step.get("expected_result", "")
            try:
                result = await asyncio.to_thread(
                    self._verify_step, expr_str, expected
                )
                step["verified"] = result
            except Exception:
                logger.warning("步骤验证失败: expression=%s", expr_str[:50])
                step["verified"] = False
            verified_steps.append(step)
        return verified_steps

    async def verify_answer(
        self, student_answer: str, correct_answer: str
    ) -> bool:
        """验证学生答案是否与正确答案等价。

        Args:
            student_answer: 学生给出的答案（LaTeX 格式）
            correct_answer: 正确答案（LaTeX 格式）

        Returns:
            True 表示答案正确
        """
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    self._compare_answers, student_answer, correct_answer
                ),
                timeout=self.timeout,
            )
            return result
        except asyncio.TimeoutError:
            logger.warning("答案比对超时")
            return False
        except Exception:
            logger.exception(
                "答案比对异常: student=%s, correct=%s",
                student_answer[:50],
                correct_answer[:50],
            )
            return False

    def _sympy_solve(self, latex_expr: str) -> dict[str, Any] | None:
        """同步 SymPy 求解（在 executor 中运行）。"""
        try:
            expr = parse_latex(latex_expr)
            result = solve(expr)
            if not result:
                return None
            return {
                "solved": True,
                "result": result,
                "latex": latex(result),
            }
        except Exception:
            # parse_latex 可能无法处理所有格式，降级为 sympify 解析
            logger.debug("parse_latex 失败，尝试 sympify: %s", latex_expr[:50])
            try:
                x = symbols("x")
                expr = sympify(latex_expr)
                result = solve(expr, x)
                if not result:
                    return None
                return {
                    "solved": True,
                    "result": result,
                    "latex": latex(result),
                }
            except Exception:
                return None

    def _verify_step(self, expression: str, expected: str) -> bool:
        """验证单个步骤的计算结果。"""
        try:
            expr = parse_latex(expression)
            exp = parse_latex(expected)
            return bool(simplify(expr - exp) == 0)
        except Exception:
            return False

    def _compare_answers(self, student: str, correct: str) -> bool:
        """比较两个 LaTeX 答案是否数学等价。"""
        try:
            s_expr = parse_latex(student)
            c_expr = parse_latex(correct)

            # 方法1: 直接化简差值
            diff = simplify(s_expr - c_expr)
            if diff == 0:
                return True

            # 方法2: 数值比较（处理无理数等情况）
            s_val = complex(N(s_expr))
            c_val = complex(N(c_expr))
            return abs(s_val - c_val) < 1e-10

        except Exception:
            # LaTeX 解析失败，退化为字符串比较
            return student.strip() == correct.strip()
