"""LLM 服务封装：通过 OpenRouter (OpenAI 兼容 API) 调用多种模型。"""

import asyncio
import base64
import logging
from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from aixue.config import Settings

_MAX_RETRIES = 3
_RETRY_DELAYS = (1, 3, 5)  # 秒

logger = logging.getLogger(__name__)


class LLMService:
    """异步 LLM 服务，通过 OpenRouter 的 OpenAI 兼容端点调用多模型。"""

    def __init__(self) -> None:
        self.settings = Settings()
        self.client = AsyncOpenAI(
            api_key=self.settings.openrouter_api_key,
            base_url=self.settings.openrouter_base_url,
        )

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

        # 如果有 system prompt，插入到消息列表最前面
        all_messages = []
        if system:
            all_messages.append({"role": "system", "content": system})
        all_messages.extend(self._normalize_messages(messages))

        logger.info("LLM 请求: model=%s, messages=%d条", model, len(all_messages))

        for attempt in range(_MAX_RETRIES):
            response = await self.client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                messages=all_messages,
            )

            if response.choices:
                content = response.choices[0].message.content or ""
                usage = response.usage
                if usage:
                    logger.info(
                        "LLM 响应: tokens(in=%d, out=%d)",
                        usage.prompt_tokens,
                        usage.completion_tokens,
                    )
                return content

            # choices 为空，记录并重试
            logger.warning(
                "LLM 返回空 choices (第%d/%d次): model=%s, id=%s, usage=%s",
                attempt + 1,
                _MAX_RETRIES,
                model,
                getattr(response, "id", None),
                getattr(response, "usage", None),
            )
            if attempt < _MAX_RETRIES - 1:
                delay = _RETRY_DELAYS[attempt]
                logger.info("等待 %d 秒后重试...", delay)
                await asyncio.sleep(delay)

        raise ValueError(
            f"LLM 连续 {_MAX_RETRIES} 次返回空内容，模型可能暂时不可用，请稍后重试"
        )

    async def chat_stream(
        self,
        messages: list[dict],
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        """流式发送消息，逐块返回文本。"""
        model = model or self.settings.llm_model

        all_messages = []
        if system:
            all_messages.append({"role": "system", "content": system})
        all_messages.extend(self._normalize_messages(messages))

        logger.info("LLM 流式请求: model=%s", model)
        stream = await self.client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=all_messages,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content

    async def recognize_image(
        self,
        image_data: bytes,
        media_type: str,
        prompt: str,
        max_tokens: int = 4096,
    ) -> str:
        """多模态 LLM 图片识别。

        Args:
            image_data: 图片二进制数据
            media_type: MIME 类型，如 "image/png"
            prompt: 识别指令
            max_tokens: 最大生成 token 数

        Returns:
            LLM 对图片内容的文字描述
        """
        image_b64 = base64.b64encode(image_data).decode("utf-8")
        data_url = f"data:{media_type};base64,{image_b64}"

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_url}},
                    {"type": "text", "text": prompt},
                ],
            }
        ]

        logger.info("LLM 图片识别请求: media_type=%s, size=%d bytes", media_type, len(image_data))
        return await self.chat(messages, model=self.settings.llm_model, max_tokens=max_tokens)

    def _normalize_messages(self, messages: list[dict]) -> list[dict]:
        """标准化消息格式，确保兼容 OpenAI API。

        处理 Anthropic 特有的多模态消息格式，转换为 OpenAI 格式。
        """
        normalized = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if isinstance(content, str):
                normalized.append({"role": role, "content": content})
            elif isinstance(content, list):
                # 多模态内容：转换 Anthropic image 格式为 OpenAI image_url 格式
                parts = []
                for block in content:
                    if block.get("type") == "text":
                        parts.append({"type": "text", "text": block["text"]})
                    elif block.get("type") == "image":
                        source = block["source"]
                        data_url = f"data:{source['media_type']};base64,{source['data']}"
                        parts.append({"type": "image_url", "image_url": {"url": data_url}})
                    elif block.get("type") == "image_url":
                        parts.append(block)
                    else:
                        parts.append(block)
                normalized.append({"role": role, "content": parts})
            else:
                normalized.append({"role": role, "content": str(content)})

        return normalized
