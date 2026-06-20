#!/usr/bin/env python3
"""雙記憶混合搜尋橋接測試（src/hybrid_search.py）。"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _mock_session(monkeypatch, status=200, payload=None, raise_exc=None):
    from unittest.mock import AsyncMock, MagicMock
    import src.hybrid_search as hs

    if raise_exc is not None:
        def boom():
            raise raise_exc
        monkeypatch.setattr(hs.aiohttp, "ClientSession", boom)
        return

    resp = MagicMock()
    resp.status = status
    resp.json = AsyncMock(return_value=payload or {})
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=False)
    sess = MagicMock()
    sess.get = MagicMock(return_value=resp)
    sess.__aenter__ = AsyncMock(return_value=sess)
    sess.__aexit__ = AsyncMock(return_value=False)
    monkeypatch.setattr(hs.aiohttp, "ClientSession", lambda: sess)


class TestQueryClaudeMem:
    def test_empty_inputs_return_none(self):
        from src.hybrid_search import query_claude_mem
        assert asyncio.run(query_claude_mem("", "q")) is None
        assert asyncio.run(query_claude_mem("http://x", "")) is None

    def test_parse_success(self, monkeypatch):
        from src.hybrid_search import query_claude_mem
        _mock_session(monkeypatch, 200, {"content": [{"type": "text", "text": "hello"}]})
        assert asyncio.run(query_claude_mem("http://x", "q")) == "hello"

    def test_multi_text_joined(self, monkeypatch):
        from src.hybrid_search import query_claude_mem
        _mock_session(monkeypatch, 200, {"content": [
            {"type": "text", "text": "a"}, {"type": "text", "text": "b"},
        ]})
        assert asyncio.run(query_claude_mem("http://x", "q")) == "a\nb"

    def test_non_200_returns_none(self, monkeypatch):
        from src.hybrid_search import query_claude_mem
        _mock_session(monkeypatch, 500, {})
        assert asyncio.run(query_claude_mem("http://x", "q")) is None

    def test_empty_content_returns_none(self, monkeypatch):
        from src.hybrid_search import query_claude_mem
        _mock_session(monkeypatch, 200, {"content": []})
        assert asyncio.run(query_claude_mem("http://x", "q")) is None

    def test_connection_error_degrades(self, monkeypatch):
        from src.hybrid_search import query_claude_mem
        _mock_session(monkeypatch, raise_exc=OSError("connection refused"))
        # 連線失敗應優雅降級回 None，不拋例外
        assert asyncio.run(query_claude_mem("http://x", "q")) is None
