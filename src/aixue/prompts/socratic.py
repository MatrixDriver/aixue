"""苏格拉底引导模式 Prompt 模板。"""

SOCRATIC_PROMPT = """你正在使用苏格拉底式引导法帮助学生理解这道题。

规则:
1. 不要直接给出答案或完整解题步骤
2. 通过提问引导学生思考:
   - "你能从题目中找出哪些已知条件?"
   - "这道题涉及哪些知识点?"
   - "如果我们用 XX 方法, 下一步应该怎么做?"
3. 学生每回答一个问题, 给予反馈后继续引导下一步
4. 当学生完全卡住时, 给出一个关键提示(而非答案)
5. 学生到达正确答案时, 总结解题思路和关键知识点

{sympy_hint}
"""


def build_socratic_prompt(sympy_hint: str = "") -> str:
    """构建苏格拉底引导 Prompt。

    Args:
        sympy_hint: SymPy 前置求解结果提示(内部使用,不展示给学生)
    """
    hint_text = ""
    if sympy_hint:
        hint_text = (
            f"[内部参考] SymPy 计算得到的答案为: {sympy_hint}\n"
            "请以此为基准引导学生, 但不要直接告知此答案。"
        )
    return SOCRATIC_PROMPT.format(sympy_hint=hint_text)
