"""供應商回空字串時要重試,不能直接放棄。

實測 DeepSeek 會偶發回空 content(既不是截斷也不是錯誤回應)。直接回 {} 的話,
那個空字典會一路傳到 ExtractedEntities(**{}) 變成 pydantic 驗證錯誤,而
graphiti-core 只重試 RateLimitError 與 JSONDecodeError、不會重試它 ——
那一則記憶就靜默降級成沒有實體、搜尋永遠命不中的孤兒節點。
"""
import asyncio
import types

from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.prompts.models import Message

from src.openai_compat_client import EMPTY_RESPONSE_RETRIES, OpenAICompatClient


def _response(content):
    return types.SimpleNamespace(
        choices=[types.SimpleNamespace(
            message=types.SimpleNamespace(content=content), finish_reason="stop")])


def _client():
    return OpenAICompatClient(LLMConfig(api_key="x", model="m", base_url="http://x"))


def test_retries_then_gives_up_on_persistent_empty():
    """一直回空 → 打滿 EMPTY_RESPONSE_RETRIES + 1 次才放棄(不是無限重試)。"""
    calls = {"n": 0}
    c = _client()

    async def always_empty(**kw):
        calls["n"] += 1
        return _response("")

    c.client.chat.completions.create = always_empty
    out = asyncio.run(c._generate_response([Message(role="user", content="json")]))
    assert calls["n"] == EMPTY_RESPONSE_RETRIES + 1
    assert out == {}


def test_recovers_when_a_later_attempt_returns_content():
    """第二次就拿到內容 → 只打 2 次,而且結果要真的回傳出來。"""
    calls = {"n": 0}
    c = _client()

    async def empty_then_ok(**kw):
        calls["n"] += 1
        return _response("" if calls["n"] == 1 else '{"ok": true}')

    c.client.chat.completions.create = empty_then_ok
    out = asyncio.run(c._generate_response([Message(role="user", content="json")]))
    assert calls["n"] == 2
    assert out.get("ok") is True
