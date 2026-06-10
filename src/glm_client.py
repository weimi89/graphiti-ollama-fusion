#!/usr/bin/env python3
"""
GLM（智谱 AI）LLM 客戶端
========================

使用 OpenAI 相容 API 連接智谱 AI 的 GLM 模型。
繼承 OpenAICompatClient 共用 json_object 模式與簡化 schema 注入邏輯。
"""

from openai import AsyncOpenAI

from graphiti_core.llm_client.config import LLMConfig

from src.openai_compat_client import OpenAICompatClient, DEFAULT_MAX_TOKENS

DEFAULT_MODEL = "glm-4-flash"
DEFAULT_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"


class GlmClient(OpenAICompatClient):
    """智谱 AI GLM 客戶端（OpenAI 相容，json_object 模式）。"""

    _provider_name = "GLM"

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
