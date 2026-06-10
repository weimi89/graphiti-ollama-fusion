#!/usr/bin/env python3
"""
OpenRouter LLM 客戶端
=====================

透過 OpenAI 相容 API 連接 OpenRouter，存取各種模型（如 Step-3.5-Flash）。
繼承 OpenAICompatClient 共用 json_object 模式與簡化 schema 注入邏輯。
"""

from openai import AsyncOpenAI

from graphiti_core.llm_client.config import LLMConfig

from src.openai_compat_client import OpenAICompatClient, DEFAULT_MAX_TOKENS

DEFAULT_MODEL = "stepfun/step-3.5-flash:free"
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterClient(OpenAICompatClient):
    """OpenRouter LLM 客戶端（OpenAI 相容，聚合各家模型）。"""

    _provider_name = "OpenRouter"

    def __init__(self, config: LLMConfig | None = None, cache: bool = False):
        if config is None:
            config = LLMConfig(max_tokens=DEFAULT_MAX_TOKENS)
        elif config.max_tokens is None:
            config.max_tokens = DEFAULT_MAX_TOKENS
        super().__init__(config, cache)
        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url or DEFAULT_BASE_URL,
        )
