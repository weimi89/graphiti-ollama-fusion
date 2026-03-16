#!/usr/bin/env python3
"""
OpenRouter LLM 客戶端
=====================

透過 OpenAI 相容 API 連接 OpenRouter，存取各種模型（如 Step-3.5-Flash）。
使用 json_object 模式確保結構化輸出相容性。
基於 GlmClient 模式，簡化 schema 注入以提高相容性。
"""

import json
import logging
import typing

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel

from graphiti_core.llm_client.client import LLMClient, get_extraction_language_instruction
from graphiti_core.llm_client.config import LLMConfig, ModelSize
from graphiti_core.llm_client.errors import RateLimitError
from graphiti_core.prompts.models import Message

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "stepfun/step-3.5-flash:free"
DEFAULT_MAX_TOKENS = 4096


def _build_simple_schema_hint(response_model: type[BaseModel]) -> str:
    """從 Pydantic model 產生簡化的 JSON 範例結構。"""
    try:
        schema = response_model.model_json_schema()
        return json.dumps(
            _simplify_schema(schema, schema.get("$defs", {})),
            ensure_ascii=False,
            indent=2,
        )
    except Exception:
        return ""


def _simplify_schema(schema: dict, defs: dict) -> dict:
    """將 JSON Schema 轉為簡化的範例結構。"""
    if "$ref" in schema:
        ref_name = schema["$ref"].split("/")[-1]
        if ref_name in defs:
            return _simplify_schema(defs[ref_name], defs)
        return {}

    if schema.get("type") == "object":
        result = {}
        for prop_name, prop_schema in schema.get("properties", {}).items():
            result[prop_name] = _simplify_value(prop_schema, defs)
        return result

    return {}


def _simplify_value(schema: dict, defs: dict) -> typing.Any:
    """將單個字段的 schema 轉為範例值。"""
    if "$ref" in schema:
        ref_name = schema["$ref"].split("/")[-1]
        if ref_name in defs:
            return _simplify_value(defs[ref_name], defs)
        return "..."

    if "allOf" in schema:
        for sub in schema["allOf"]:
            return _simplify_value(sub, defs)

    schema_type = schema.get("type", "string")

    if schema_type == "array":
        items = schema.get("items", {})
        item_val = _simplify_value(items, defs)
        return [item_val]

    if schema_type == "object":
        result = {}
        for prop_name, prop_schema in schema.get("properties", {}).items():
            result[prop_name] = _simplify_value(prop_schema, defs)
        return result

    if schema_type == "integer":
        return 0
    if schema_type == "number":
        return 0.0
    if schema_type == "boolean":
        return True

    desc = schema.get("description", "")
    if desc:
        return f"<{desc[:60]}>"
    return "..."


class OpenRouterClient(LLMClient):
    """
    OpenRouter LLM 客戶端。

    使用 OpenAI SDK 透過 OpenRouter API 存取各種模型。
    使用 json_object 模式和簡化 schema 提示確保結構化輸出。
    """

    def __init__(self, config: LLMConfig | None = None, cache: bool = False):
        if config is None:
            config = LLMConfig(max_tokens=DEFAULT_MAX_TOKENS)
        elif config.max_tokens is None:
            config.max_tokens = DEFAULT_MAX_TOKENS
        super().__init__(config, cache)

        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
        )

    async def generate_response(
        self,
        messages: list[Message],
        response_model: type[BaseModel] | None = None,
        max_tokens: int | None = None,
        model_size: ModelSize = ModelSize.medium,
        group_id: str | None = None,
        prompt_name: str | None = None,
    ) -> dict[str, typing.Any]:
        """覆寫基類方法：用簡化 schema 提示取代完整 JSON Schema 注入。"""
        if max_tokens is None:
            max_tokens = self.max_tokens

        if response_model is not None:
            hint = _build_simple_schema_hint(response_model)
            if hint:
                messages[-1].content += (
                    f"\n\nRespond with a JSON object with these fields:\n{hint}"
                )

        messages[0].content += get_extraction_language_instruction(group_id)

        for message in messages:
            message.content = self._clean_input(message.content)

        with self.tracer.start_span("llm.generate") as span:
            attributes = {
                "llm.provider": self._get_provider_type(),
                "model.size": model_size.value,
                "max_tokens": max_tokens,
                "cache.enabled": self.cache_enabled,
            }
            if prompt_name:
                attributes["prompt.name"] = prompt_name
            span.add_attributes(attributes)

            if self.cache_enabled and self.cache_dir is not None:
                cache_key = self._get_cache_key(messages)
                cached_response = self.cache_dir.get(cache_key)
                if cached_response is not None:
                    span.add_attributes({"cache.hit": True})
                    return cached_response

            span.add_attributes({"cache.hit": False})

            try:
                response = await self._generate_response_with_retry(
                    messages, response_model, max_tokens, model_size
                )
            except Exception as e:
                span.set_status("error", str(e))
                span.record_exception(e)
                raise

            if self.cache_enabled and self.cache_dir is not None:
                cache_key = self._get_cache_key(messages)
                self.cache_dir.set(cache_key, response)

            return response

    async def _generate_response(
        self,
        messages: list[Message],
        response_model: type[BaseModel] | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        model_size: ModelSize = ModelSize.medium,
    ) -> dict[str, typing.Any]:
        msgs: list[ChatCompletionMessageParam] = []
        for m in messages:
            if m.role == "user":
                msgs.append({"role": "user", "content": m.content})
            elif m.role == "system":
                msgs.append({"role": "system", "content": m.content})

        try:
            response = await self.client.chat.completions.create(
                model=self.model or DEFAULT_MODEL,
                messages=msgs,
                temperature=self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                response_format={"type": "json_object"},
            )
            result = response.choices[0].message.content or ""
            if not result.strip():
                logger.warning("OpenRouter 回傳空內容")
                return {}
            return json.loads(result)
        except Exception as e:
            if "rate" in str(e).lower() or "429" in str(e):
                raise RateLimitError from e
            logger.error(f"OpenRouter LLM 回應錯誤: {e}")
            raise
