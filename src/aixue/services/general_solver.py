"""理化生通用解题服务。"""

import logging
from typing import Any

from aixue.prompts.direct import build_direct_prompt
from aixue.prompts.socratic import build_socratic_prompt
from aixue.prompts.system import build_system_prompt
from aixue.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class GeneralSolver:
    """通用解题器：物理、化学、生物等非数学学科。"""

    def __init__(self, llm: LLMService) -> None:
        self.llm = llm

    async def solve(
        self,
        question: str,
        subject: str,
        mode: str,
        user_profile: dict,
    ) -> dict[str, Any]:
        """通用学科解题。

        Args:
            question: 题目文本
            subject: 学科名称
            mode: 解题模式 "socratic" 或 "direct"
            user_profile: 用户信息

        Returns:
            解题结果字典
        """
        system_prompt = build_system_prompt(
            student_name=user_profile.get("name", "同学"),
            grade=user_profile.get("grade", ""),
            subjects=user_profile.get("subjects", ""),
        )

        if mode == "socratic":
            mode_prompt = build_socratic_prompt()
        else:
            mode_prompt = build_direct_prompt()

        # 为不同学科添加学科特定提示
        subject_hint = self._get_subject_hint(subject)

        messages = [
            {
                "role": "user",
                "content": (
                    f"{mode_prompt}\n\n"
                    f"学科: {subject}\n"
                    f"{subject_hint}\n\n"
                    f"题目:\n{question}"
                ),
            }
        ]

        logger.info("通用解题: subject=%s, mode=%s", subject, mode)
        response = await self.llm.chat(messages, system=system_prompt)

        return {
            "content": response,
            "verified": False,  # 理化生暂不支持自动验证
            "attempts": 1,
            "sympy_result": None,
            "mode": mode,
        }

    def _get_subject_hint(self, subject: str) -> str:
        """获取学科特定提示。"""
        hints = {
            "物理": (
                "注意事项:\n"
                "- 明确物理量和单位\n"
                "- 画出受力分析或电路图(用文字描述)\n"
                "- 注明使用的物理定律和公式"
            ),
            "化学": (
                "注意事项:\n"
                "- 化学方程式必须配平\n"
                "- 标注反应条件和状态符号\n"
                "- 涉及计算时注意摩尔质量和化学计量数"
            ),
            "生物": (
                "注意事项:\n"
                "- 使用规范的生物学术语\n"
                "- 涉及遗传题时画出遗传图解\n"
                "- 实验题注意对照组和变量控制"
            ),
        }
        return hints.get(subject, "")
