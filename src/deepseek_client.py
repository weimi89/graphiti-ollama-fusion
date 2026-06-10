#!/usr/bin/env python3
"""
DeepSeek LLM 客戶端
===================

透過 OpenAI 相容 API 連接 DeepSeek（deepseek-chat / deepseek-v4-flash / deepseek-v4-pro）。
繼承 OpenAICompatClient 共用 json_object 模式與簡化 schema 注入邏輯。

DeepSeek 嚴格要求：json_object 模式下 prompt 必須含 "json" 字串，
否則 API 直接回 "Prompt must contain the word 'json'"。
OpenAICompatClient._generate_response 已內建保底防護涵蓋所有呼叫路徑。
"""

from openai import AsyncOpenAI

from graphiti_core.llm_client.config import LLMConfig

from src.openai_compat_client import OpenAICompatClient, DEFAULT_MAX_TOKENS

DEFAULT_MODEL = "deepseek-v4-flash"
DEFAULT_BASE_URL = "https://api.deepseek.com"


class DeepSeekClient(OpenAICompatClient):
    """DeepSeek LLM 客戶端（OpenAI 相容，json_object 模式含 json 保底防護）。"""

    _provider_name = "DeepSeek"

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
