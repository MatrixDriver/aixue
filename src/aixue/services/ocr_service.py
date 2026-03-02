"""OCR 识别服务：使用多模态 LLM 识别题目图片。"""

import logging

from aixue.services.llm_service import LLMService

logger = logging.getLogger(__name__)

# 题目识别 Prompt
RECOGNITION_PROMPT = """请仔细识别这张图片中的题目内容。

要求:
1. 完整提取题目文字，包括题号、条件、问题
2. 数学公式用 LaTeX 格式表示（用 $ 包裹行内公式，$$ 包裹独立公式）
3. 如有图形描述，用文字说明
4. 保持原始题目结构和编号
5. 只输出题目内容，不要添加解答

如果图片模糊或无法识别，请说明无法识别的部分。"""

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


class OCRService:
    """题目识别服务。"""

    def __init__(self, llm: LLMService) -> None:
        self.llm = llm

    async def recognize(self, image_data: bytes, media_type: str) -> str:
        """识别图片中的题目内容。

        Args:
            image_data: 图片二进制数据
            media_type: MIME 类型

        Returns:
            识别出的题目文本（含 LaTeX 公式）
        """
        logger.info("开始识别题目图片: size=%d bytes", len(image_data))
        result = await self.llm.recognize_image(
            image_data=image_data,
            media_type=media_type,
            prompt=RECOGNITION_PROMPT,
        )
        logger.info("题目识别完成: text_length=%d", len(result))
        return result

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
