"""数学深度解题服务：SymPy 前置求解 + LLM 生成 + 验证重试。"""

import logging
from typing import Any

from aixue.config import Settings
from aixue.prompts.direct import build_direct_prompt
from aixue.prompts.socratic import build_socratic_prompt
from aixue.prompts.system import build_system_prompt
from aixue.services.llm_service import LLMService
from aixue.services.verifier import MathVerifier

logger = logging.getLogger(__name__)

settings = Settings()


class MathSolver:
    """数学深度解题器：集成 SymPy 验证的数学解题引擎。"""

    def __init__(self, llm: LLMService, verifier: MathVerifier) -> None:
        self.llm = llm
        self.verifier = verifier
        self.max_retries = settings.max_retry_count

    async def solve(
        self, question: str, mode: str, user_profile: dict
    ) -> dict[str, Any]:
        """完整的数学解题流程。

        Args:
            question: 题目文本(含 LaTeX 公式)
            mode: 解题模式 "socratic" 或 "direct"
            user_profile: 用户信息 {"name": ..., "grade": ..., "subjects": ...}

        Returns:
            解题结果字典
        """
        # 第一级: SymPy 前置求解
        sympy_result = await self.verifier.pre_solve(question)
        sympy_hint = ""
        if sympy_result and sympy_result.get("solved"):
            sympy_hint = sympy_result.get("latex", "")
            logger.info("SymPy 前置求解成功: %s", sympy_hint[:50])

        # 构造 Prompt
        system_prompt = build_system_prompt(
            student_name=user_profile.get("name", "同学"),
            grade=user_profile.get("grade", ""),
            subjects=user_profile.get("subjects", ""),
        )

        if mode == "socratic":
            mode_prompt = build_socratic_prompt(sympy_hint)
        else:
            mode_prompt = build_direct_prompt(sympy_hint)

        messages = [
            {
                "role": "user",
                "content": f"{mode_prompt}\n\n题目:\n{question}",
            }
        ]

        # LLM 解题 + 验证重试
        response = ""
        verified = False
        for attempt in range(1, self.max_retries + 1):
            response = await self.llm.chat(messages, system=system_prompt)

            # 第二级: 如果有 SymPy 真值，验证 LLM 结果
            if sympy_result and sympy_result.get("solved") and mode == "direct":
                verified = await self._verify_response(response, sympy_result)
                if verified:
                    logger.info(
                        "数学解题验证通过: attempt=%d/%d", attempt, self.max_retries
                    )
                    break
                logger.warning(
                    "数学解题验证失败, 重试: attempt=%d/%d",
                    attempt,
                    self.max_retries,
                )
                # 追加纠正信息重试
                messages.append({"role": "assistant", "content": response})
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "你的答案与数学验证引擎的结果不一致, "
                            "请重新检查推导过程并给出修正后的解答。"
                        ),
                    }
                )
            else:
                # 苏格拉底模式或无 SymPy 结果时不做严格验证
                verified = sympy_result is None
                break

        return {
            "content": response,
            "verified": verified,
            "attempts": attempt,  # type: ignore[possibly-undefined]
            "sympy_result": sympy_hint if sympy_hint else None,
            "mode": mode,
        }

    async def _verify_response(
        self, response: str, sympy_result: dict[str, Any]
    ) -> bool:
        """验证 LLM 响应中的最终答案是否与 SymPy 结果一致。"""
        # 从响应中提取 \\boxed{} 内容
        import re

        boxed_match = re.search(r"\\boxed\{([^}]+)\}", response)
        if not boxed_match:
            return False

        llm_answer = boxed_match.group(1)
        correct_answer = sympy_result.get("latex", "")

        if not correct_answer:
            return False

        return await self.verifier.verify_answer(llm_answer, correct_answer)
