#!/usr/bin/env python3
"""
Web API 路由測試
================

使用 Starlette TestClient 測試 Web API 端點。
所有 Neo4j 操作均透過 mock 處理，不需要外部服務。
"""

import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from starlette.testclient import TestClient
from starlette.applications import Starlette
from starlette.routing import Route

from src.web_api import create_web_routes, _RateLimiter


# ============================================================
# Mock 工具
# ============================================================

class MockRecord:
    """模擬 Neo4j record。"""
    def __init__(self, data: dict):
        self._data = data

    def __getitem__(self, key):
        return self._data[key]


class MockResult:
    """模擬 Neo4j async result（支援 async for）。"""
    def __init__(self, records: list[dict]):
        self._records = [MockRecord(r) for r in records]

    def __aiter__(self):
        return self._iter()

    async def _iter(self):
        for r in self._records:
            yield r


class MockSession:
    """模擬 Neo4j async session。"""
    def __init__(self, results: list[list[dict]]):
        self._results = results
        self._call_idx = 0

    async def run(self, query: str, params=None):
        if self._call_idx < len(self._results):
            result = MockResult(self._results[self._call_idx])
            self._call_idx += 1
            return result
        return MockResult([])

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class MockDriver:
    """模擬 Neo4j driver。"""
    def __init__(self, session_results: list[list[dict]] = None):
        self._session_results = session_results or []
        self._query_idx = 0

    def session(self):
        return MockSession(self._session_results)

    async def execute_query(self, query: str, **kwargs):
        """模擬 driver.execute_query()（用於 delete 端點）。"""
        if self._query_idx < len(self._session_results):
            records = [MockRecord(r) for r in self._session_results[self._query_idx]]
            self._query_idx += 1
            return records, None, None
        return [], None, None


class MockGraphiti:
    """模擬 Graphiti 實例。"""
    def __init__(self, session_results: list[list[dict]] = None):
        self.driver = MockDriver(session_results)


def create_test_app(session_results: list[list[dict]] = None):
    """建立測試用的 Starlette 應用。"""
    mock_graphiti = MockGraphiti(session_results or [])

    async def get_graphiti():
        return mock_graphiti

    routes = create_web_routes(get_graphiti_fn=get_graphiti)
    # 只取 API 路由（不含 static files mount，因為測試環境可能沒有 web/ 目錄）
    api_routes = [r for r in routes if isinstance(r, Route)]
    return Starlette(routes=api_routes)


# ============================================================
# 測試
# ============================================================

class TestApiStats:
    """測試 /api/stats 端點。"""

    def test_returns_stats(self):
        app = create_test_app([
            [{"count": 10}],   # 節點數
            [{"count": 5}],    # 事實數
            [{"count": 20}],   # 片段數
        ])
        client = TestClient(app)
        resp = client.get("/api/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["nodes"] == 10
        assert data["facts"] == 5
        assert data["episodes"] == 20

    def test_with_group_filter(self):
        app = create_test_app([
            [{"count": 3}],
            [{"count": 2}],
            [{"count": 8}],
        ])
        client = TestClient(app)
        resp = client.get("/api/stats?group_id=test-group")
        assert resp.status_code == 200
        data = resp.json()
        assert data["group_id"] == "test-group"


class TestApiGroups:
    """測試 /api/groups 端點。"""

    def test_returns_groups(self):
        app = create_test_app([
            [{"gid": "group-a"}, {"gid": "group-b"}],
        ])
        client = TestClient(app)
        resp = client.get("/api/groups")
        assert resp.status_code == 200
        data = resp.json()
        assert "group-a" in data["groups"]
        assert "group-b" in data["groups"]

    def test_empty_groups(self):
        app = create_test_app([[]])
        client = TestClient(app)
        resp = client.get("/api/groups")
        assert resp.status_code == 200
        assert resp.json()["groups"] == []


class TestApiNodes:
    """測試 /api/nodes 端點。"""

    def test_returns_paginated_nodes(self):
        app = create_test_app([
            [{"total": 1}],  # count query
            [{"uuid": "u1", "name": "Node1", "summary": "s1", "group_id": "g1", "created_at": "2026-01-01", "labels": ["Entity"]}],
        ])
        client = TestClient(app)
        resp = client.get("/api/nodes")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["nodes"]) == 1
        assert data["nodes"][0]["name"] == "Node1"

    def test_pagination_params(self):
        app = create_test_app([
            [{"total": 50}],
            [],  # 空結果（page 3）
        ])
        client = TestClient(app)
        resp = client.get("/api/nodes?page=3&limit=10")
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 3
        assert data["pages"] == 5  # ceil(50/10)


class TestApiFacts:
    """測試 /api/facts 端點。"""

    def test_returns_facts(self):
        app = create_test_app([
            [{"total": 1}],
            [{
                "uuid": "f1", "name": "knows", "fact": "A knows B",
                "group_id": "g1", "created_at": "2026-01-01",
                "source_name": "A", "target_name": "B",
                "source_uuid": "su1", "target_uuid": "tu1",
            }],
        ])
        client = TestClient(app)
        resp = client.get("/api/facts")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["facts"][0]["name"] == "knows"


class TestApiEpisodes:
    """測試 /api/episodes 端點。"""

    def test_returns_episodes(self):
        app = create_test_app([
            [{"total": 1}],
            [{
                "uuid": "e1", "name": "ep1", "content": "some content",
                "group_id": "g1", "created_at": "2026-01-01",
                "source_description": "test",
            }],
        ])
        client = TestClient(app)
        resp = client.get("/api/episodes")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["episodes"]) == 1
        assert data["episodes"][0]["name"] == "ep1"


class TestApiDelete:
    """測試刪除端點。"""

    def test_delete_episode_not_found(self):
        app = create_test_app([
            [{"deleted": 0}],  # 沒有刪除任何東西
        ])
        client = TestClient(app)
        resp = client.request("DELETE", "/api/episodes/nonexistent-uuid")
        assert resp.status_code == 404

    def test_delete_episode_success(self):
        app = create_test_app([
            [{"deleted": 1}],
        ])
        client = TestClient(app)
        resp = client.request("DELETE", "/api/episodes/some-uuid")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_delete_fact_not_found(self):
        app = create_test_app([
            [{"deleted": 0}],
        ])
        client = TestClient(app)
        resp = client.request("DELETE", "/api/facts/nonexistent-uuid")
        assert resp.status_code == 404

    def test_delete_fact_success(self):
        app = create_test_app([
            [{"deleted": 1}],
        ])
        client = TestClient(app)
        resp = client.request("DELETE", "/api/facts/some-uuid")
        assert resp.status_code == 200
        assert resp.json()["success"] is True


class TestRateLimiterIntegration:
    """測試速率限制器在 API 中的行為。"""

    def test_rate_limiter_reset(self):
        """測試 _RateLimiter 的基本功能。"""
        limiter = _RateLimiter(max_requests=2, window_seconds=60)
        assert limiter.is_allowed("test-ip") is True
        assert limiter.is_allowed("test-ip") is True
        assert limiter.is_allowed("test-ip") is False

    def test_multiple_ips(self):
        limiter = _RateLimiter(max_requests=1, window_seconds=60)
        assert limiter.is_allowed("ip1") is True
        assert limiter.is_allowed("ip2") is True
        assert limiter.is_allowed("ip1") is False
        assert limiter.is_allowed("ip2") is False


class TestStaticRoutes:
    """測試靜態路由設定。"""

    def test_routes_created(self):
        """確認 create_web_routes 返回正確的路由列表。"""
        async def mock_fn():
            return None

        routes = create_web_routes(get_graphiti_fn=mock_fn)
        assert len(routes) > 0

        # 確認 API 路由存在
        route_paths = [r.path for r in routes if isinstance(r, Route)]
        assert "/api/stats" in route_paths
        assert "/api/groups" in route_paths
        assert "/api/nodes" in route_paths
        assert "/api/facts" in route_paths
        assert "/api/episodes" in route_paths
