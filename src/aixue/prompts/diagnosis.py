"""学情分析 Prompt 模板。"""

DIAGNOSIS_PROMPT = """你是一位经验丰富的教育诊断专家。请根据以下学生的解题记录进行五维错因分析。

学生信息:
- 年级: {grade}
- 学科: {subject}

解题记录:
{records_summary}

请从以下五个维度进行分析, 并以 JSON 格式返回结果:

1. **知识漏洞检测** (knowledge_gaps):
   - 列出学生明显薄弱的知识点
   - 标注严重程度(1-5)

2. **思维路径回溯** (thinking_patterns):
   - 分析学生常见的思维错误模式
   - 识别是概念混淆还是计算失误

3. **概念关联分析** (concept_links):
   - 分析学生对知识点之间关联的理解程度
   - 识别断裂的概念链

4. **解题习惯诊断** (habit_analysis):
   - 分析答题速度、审题习惯、验算习惯
   - 识别粗心类型

5. **认知水平评估** (cognitive_level):
   - 按 Bloom 分类法评估学生认知层级
   - 给出当前水平和提升建议

请返回以下 JSON 格式(不要额外的 markdown 标记):
{{
  "overall_score": 75.0,
  "knowledge_gaps": [{{"point": "...", "severity": 3, "description": "..."}}],
  "thinking_patterns": [{{"pattern": "...", "frequency": "...", "suggestion": "..."}}],
  "concept_links": [{{"from": "...", "to": "...", "status": "weak/broken"}}],
  "habit_analysis": [{{"habit": "...", "issue": "...", "improvement": "..."}}],
  "cognitive_level": {{"current": "...", "target": "...", "path": "..."}}
}}
"""


def build_diagnosis_prompt(
    grade: str,
    subject: str,
    records_summary: str,
) -> str:
    """构建学情分析 Prompt。"""
    return DIAGNOSIS_PROMPT.format(
        grade=grade,
        subject=subject,
        records_summary=records_summary,
    )
