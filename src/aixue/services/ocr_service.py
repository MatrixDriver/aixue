"""OCR 识别服务：使用多模态 LLM 识别题目图片。"""

import logging

from aixue.services.llm_service import LLMService

logger = logging.getLogger(__name__)

# 题目识别 Prompt（无指定题号）
RECOGNITION_PROMPT = """请仔细识别这张图片中的题目内容，严格按照原始排版还原。

输出格式要求（必须严格遵守）:
1. 完整提取题目文字，包括题号、条件、问题和所有小问
2. 数学公式**只能用 LaTeX 格式**:
   - 行内公式用 $...$ 包裹，如 $F = ma$
   - 独立公式用 $$...$$ 包裹
   - **严禁使用 MathML、HTML 标签或任何 XML 格式**
3. 表格用 Markdown 表格语法还原（| 列1 | 列2 | 格式）
4. 保持原始的段落结构、缩进、编号层级（如 (1)(2)(3)）
5. 如有图形/图表，用 [图: 简要描述] 标注位置
6. 只输出题目内容，不要添加解答或分析

如果图片模糊或无法识别，请说明无法识别的部分。"""

# 题目识别 Prompt（有用户补充说明，聚焦特定题目）
RECOGNITION_FOCUSED_PROMPT = """请仔细识别这张图片中的题目内容，严格按照原始排版还原。

用户指定: {user_hint}

输出格式要求（必须严格遵守）:
1. 只提取用户指定的那道题目，忽略图片中的其他题目
2. 完整提取该题的文字，包括题号、条件、问题和所有小问
3. 数学公式**只能用 LaTeX 格式**:
   - 行内公式用 $...$ 包裹，如 $F = ma$
   - 独立公式用 $$...$$ 包裹
   - **严禁使用 MathML、HTML 标签或任何 XML 格式**
4. 表格用 Markdown 表格语法还原（| 列1 | 列2 | 格式）
5. 保持原始的段落结构、缩进、编号层级（如 (1)(2)(3)）
6. 如有图形/图表，用 [图: 简要描述] 标注位置
7. 只输出题目内容，不要添加解答或分析

如果图片模糊或无法识别，请说明无法识别的部分。"""

# OCR 识别最大 token 数
_OCR_MAX_TOKENS = 2048

# 学科判定 Prompt
SUBJECT_DETECTION_PROMPT = """请判断以下题目属于哪个学科。

题目:
{question}

只回答一个学科名称，从以下选项中选择:
- 数学
- 物理
- 化学
- 生物

回答格式: 只输出学科名称，不要其他内容。"""


MULTI_QUESTION_DETECTION_PROMPT = """请分析这张图片中包含的所有题目，输出 JSON 格式结果。

分析要求:
1. 识别每道题的题号（如"第1题"、"14."等）
2. 判断每道题是否完整（题目文字是否被截断、是否缺少关键条件或问题）
3. 用一句话概括每道题的内容（不超过20字）
4. 最多识别5道题

输出格式（严格 JSON，不要包含其他文字）:
{"question_count": 数字, "questions": [{"index": 1, "label": "题号文字", "summary": "一句话概括", "complete": true}]}

如果图片中没有可识别的题目，返回: {"question_count": 0, "questions": []}"""

_DETECT_MAX_TOKENS = 512


class OCRService:
    """题目识别服务。"""

    def __init__(self, llm: LLMService) -> None:
        self.llm = llm

    async def recognize(
        self,
        image_data: bytes,
        media_type: str,
        user_hint: str | None = None,
    ) -> str:
        """识别图片中的题目内容。

        Args:
            image_data: 图片二进制数据
            media_type: MIME 类型
            user_hint: 用户补充说明（如 "第14题"），用于聚焦识别

        Returns:
            识别出的题目文本（含 LaTeX 公式）
        """
        if user_hint:
            prompt = RECOGNITION_FOCUSED_PROMPT.format(user_hint=user_hint)
            logger.info(
                "开始识别题目图片(聚焦): size=%d bytes, hint=%s",
                len(image_data),
                user_hint,
            )
        else:
            prompt = RECOGNITION_PROMPT
            logger.info("开始识别题目图片: size=%d bytes", len(image_data))

        result = await self.llm.recognize_image(
            image_data=image_data,
            media_type=media_type,
            prompt=prompt,
            max_tokens=_OCR_MAX_TOKENS,
        )
        logger.info("题目识别完成: text_length=%d", len(result))
        return result

    async def detect_questions(
        self,
        image_data: bytes,
        media_type: str,
    ) -> dict:
        """检测图片中的题目数量和完整性。

        Returns:
            包含 question_count 和 questions 列表的字典
        """
        logger.info("开始多题检测: size=%d bytes", len(image_data))
        raw = await self.llm.recognize_image(
            image_data=image_data,
            media_type=media_type,
            prompt=MULTI_QUESTION_DETECTION_PROMPT,
            max_tokens=_DETECT_MAX_TOKENS,
        )
        result = self._parse_detection_result(raw)
        logger.info(
            "多题检测完成: question_count=%d",
            result.get("question_count", 0),
        )
        return result

    def _parse_detection_result(self, raw: str) -> dict:
        """解析 LLM 返回的多题检测 JSON，带容错。"""
        import json
        import re

        # 尝试直接解析
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
        # 尝试提取 JSON 块
        match = re.search(r'\{[\s\S]*\}', raw)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        # 兜底：回退为单题
        logger.warning("多题检测 JSON 解析失败，回退为单题: raw=%s", raw[:200])
        return {
            "question_count": 1,
            "questions": [
                {"index": 1, "label": "1", "summary": "", "complete": True}
            ],
        }

    async def detect_subject(self, question: str) -> str:
        """自动判定题目学科。

        Args:
            question: 题目文本

        Returns:
            学科名称: 数学/物理/化学/生物
        """
        prompt = SUBJECT_DETECTION_PROMPT.format(question=question)
        messages = [{"role": "user", "content": prompt}]
        result = await self.llm.chat(
            messages, model=self.llm.settings.llm_model_light
        )
        subject = result.strip()

        # 容错：确保返回值在有效范围内
        valid_subjects = {"数学", "物理", "化学", "生物"}
        if subject not in valid_subjects:
            logger.warning(
                "学科判定结果异常: '%s', 默认返回'数学'", subject
            )
            subject = "数学"

        logger.info("学科判定结果: %s", subject)
        return subject
