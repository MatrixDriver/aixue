"""完整解答模式 Prompt 模板。"""

DIRECT_PROMPT = """请给出这道题的完整解答过程。

格式要求:
1. 分步骤编号(第一步、第二步...)
2. 每步标注使用的定理/知识点(用【】括起)
3. 计算过程使用 LaTeX 公式
4. 最终答案用 \\boxed{{}} 框起

{sympy_constraint}
"""


def build_direct_prompt(sympy_constraint: str = "") -> str:
    """构建完整解答 Prompt。

    Args:
        sympy_constraint: SymPy 验证约束(确保 LLM 输出与数学真值一致)
    """
    constraint_text = ""
    if sympy_constraint:
        constraint_text = (
            f"[硬约束] 数学引擎已验证正确答案为: {sympy_constraint}\n"
            "你的解答最终结果必须与此一致, 如有冲突请检查推导过程。"
        )
    return DIRECT_PROMPT.format(sympy_constraint=constraint_text)
