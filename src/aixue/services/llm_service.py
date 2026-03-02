"""LLM 服务封装：统一管理 Anthropic Claude API 调用。"""

import base64
import logging
from collections.abc import AsyncGenerator

import anthropic

from aixue.config import Settings

logger = logging.getLogger(__name__)


class LLMService:
    """异步 LLM 服务，封装 Anthropic Messages API。"""

    def __init__(self) -> None:
        self.settings = Settings()
        kwargs: dict = {"api_key": self.settings.anthropic_api_key}
        if self.settings.anthropic_base_url:
            kwargs["base_url"] = self.settings.anthropic_base_url
        self.client = anthropic.AsyncAnthropic(**kwargs)

    async def chat(
        self,
        messages: list[dict],
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
    ) -> str:
        """发送消息并获取完整响应。

        Args:
            messages: 对话消息列表，格式 [{"role": "user", "content": "..."}]
            system: 系统提示词
            model: 模型名称，默认使用 settings.llm_model
            max_tokens: 最大生成 token 数

        Returns:
            LLM 生成的文本内容
        """
        model = model or self.settings.llm_model
        kwargs: dict = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system

        logger.info("LLM 请求: model=%s, messages=%d条", model, len(messages))
        response = await self.client.messages.create(**kwargs)
        content = response.content[0].text
        logger.info(
            "LLM 响应: tokens(in=%d, out=%d)",
            response.usage.input_tokens,
            response.usage.output_tokens,
        )
        return content

    async def chat_stream(
        self,
        messages: list[dict],
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        """流式发送消息，逐块返回文本。"""
        model = model or self.settings.llm_model
        kwargs: dict = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system

        logger.info("LLM 流式请求: model=%s", model)
        async with self.client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text

    async def recognize_image(
        self,
        image_data: bytes,
        media_type: str,
        prompt: str,
    ) -> str:
        """多模态 LLM 图片识别。

        Args:
            image_data: 图片二进制数据
            media_type: MIME 类型，如 "image/png"
            prompt: 识别指令

        Returns:
            LLM 对图片内容的文字描述
        """
        image_b64 = base64.b64encode(image_data).decode("utf-8")
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt,
                    },
                ],
            }
        ]

        logger.info("LLM 图片识别请求: media_type=%s, size=%d bytes", media_type, len(image_data))
        return await self.chat(messages, model=self.settings.llm_model)
