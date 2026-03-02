#!/usr/bin/env python3
"""
新功能單元測試
==============

測試十大功能擴展中新增的模組和工具：
- src/deduplication.py（去重邏輯）
- src/importance.py（存取追蹤）
- graphiti_mcp_server.py 中的輔助函數和搜尋配方
- src/config.py 新增配置項
"""

import math
import os
import sys
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================
# src/deduplication.py 測試
# ============================================================


class TestCosineSimlarity:
    """測試餘弦相似度計算。"""

    def test_identical_vectors(self):
        from src.deduplication import cosine_similarity
        vec = [1.0, 2.0, 3.0]
        assert cosine_similarity(vec, vec) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        from src.deduplication import cosine_similarity
        vec_a = [1.0, 0.0, 0.0]
        vec_b = [0.0, 1.0, 0.0]
        assert cosine_similarity(vec_a, vec_b) == pytest.approx(0.0)

    def test_opposite_vectors(self):
        from src.deduplication import cosine_similarity
        vec_a = [1.0, 0.0]
        vec_b = [-1.0, 0.0]
        assert cosine_similarity(vec_a, vec_b) == pytest.approx(-1.0)

    def test_empty_vectors(self):
        from src.deduplication import cosine_similarity
        assert cosine_similarity([], []) == 0.0

    def test_different_lengths(self):
        from src.deduplication import cosine_similarity
        assert cosine_similarity([1.0, 2.0], [1.0]) == 0.0

    def test_zero_vector(self):
        from src.deduplication import cosine_similarity
        assert cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0

    def test_similar_vectors(self):
        from src.deduplication import cosine_similarity
        vec_a = [1.0, 2.0, 3.0]
        vec_b = [1.1, 2.1, 3.1]
        sim = cosine_similarity(vec_a, vec_b)
        assert sim > 0.99  # 非常相似


class TestDuplicateCheckResult:
    """測試 DuplicateCheckResult 資料類別。"""

    def test_create_non_duplicate(self):
        from src.deduplication import DuplicateCheckResult
        result = DuplicateCheckResult(
            is_duplicate=False,
            max_similarity=0.5,
            message="no duplicate",
        )
        assert not result.is_duplicate
        assert result.max_similarity == 0.5
        assert result.similar_episode_uuid is None

    def test_create_duplicate(self):
        from src.deduplication import DuplicateCheckResult
        result = DuplicateCheckResult(
            is_duplicate=True,
            max_similarity=0.95,
            similar_episode_uuid="abc-123",
            similar_episode_name="test memory",
            message="found duplicate",
        )
        assert result.is_duplicate
        assert result.similar_episode_uuid == "abc-123"


# ============================================================
# src/importance.py 測試
# ============================================================


class TestImportanceModule:
    """測試重要性追蹤模組的存在和基本結構。"""

    def test_module_imports(self):
        from src.importance import (
            update_access_metadata,
            get_stale_entities,
            cleanup_stale_entities,
        )
        assert callable(update_access_metadata)
        assert callable(get_stale_entities)
        assert callable(cleanup_stale_entities)


# ============================================================
# src/config.py 新增配置項測試
# ============================================================


class TestConfigNewFields:
    """測試新增的配置欄位。"""

    def test_default_importance_tracking(self):
        from src.config import GraphitiConfig
        config = GraphitiConfig()
        assert config.enable_importance_tracking is True
        assert config.importance_weight == 0.1

    def test_default_stale_settings(self):
        from src.config import GraphitiConfig
        config = GraphitiConfig()
        assert config.stale_days_threshold == 30
        assert config.stale_min_access_count == 2

    def test_env_override_importance(self):
        from src.config import GraphitiConfig
        with patch.dict(os.environ, {
            "ENABLE_IMPORTANCE_TRACKING": "false",
            "IMPORTANCE_WEIGHT": "0.2",
        }):
            config = GraphitiConfig.from_env()
            assert config.enable_importance_tracking is False
            assert config.importance_weight == 0.2

    def test_env_override_stale(self):
        from src.config import GraphitiConfig
        with patch.dict(os.environ, {
            "STALE_DAYS_THRESHOLD": "60",
            "STALE_MIN_ACCESS_COUNT": "5",
        }):
            config = GraphitiConfig.from_env()
            assert config.stale_days_threshold == 60
            assert config.stale_min_access_count == 5

    def test_config_summary_includes_importance(self):
        from src.config import GraphitiConfig
        config = GraphitiConfig()
        summary = config.get_summary()
        assert "importance_tracking" in summary

    def test_save_to_file_includes_new_fields(self):
        """測試 save_to_file 輸出包含新欄位。"""
        import json
        import tempfile
        from src.config import GraphitiConfig

        config = GraphitiConfig()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name

        try:
            config.save_to_file(path)
            with open(path, "r") as f:
                data = json.load(f)
            assert "enable_importance_tracking" in data
            assert "stale_days_threshold" in data
        finally:
            os.unlink(path)


# ============================================================
# 搜尋配方對照表測試
# ============================================================


class TestSearchRecipes:
    """測試搜尋策略對照表。"""

    def test_all_16_recipes_exist(self):
        from graphiti_mcp_server import SEARCH_RECIPES
        assert len(SEARCH_RECIPES) == 16

    def test_recipe_keys(self):
        from graphiti_mcp_server import SEARCH_RECIPES
        expected_keys = {
            "combined_rrf", "combined_mmr", "combined_cross_encoder",
            "edge_rrf", "edge_mmr", "edge_node_distance",
            "edge_episode_mentions", "edge_cross_encoder",
            "node_rrf", "node_mmr", "node_node_distance",
            "node_episode_mentions", "node_cross_encoder",
            "community_rrf", "community_mmr", "community_cross_encoder",
        }
        assert set(SEARCH_RECIPES.keys()) == expected_keys

    def test_recipes_are_search_config(self):
        from graphiti_mcp_server import SEARCH_RECIPES
        from graphiti_core.search.search_config import SearchConfig
        for name, config in SEARCH_RECIPES.items():
            assert isinstance(config, SearchConfig), f"{name} is not a SearchConfig"


# ============================================================
# _build_search_filters 測試
# ============================================================


class TestBuildSearchFilters:
    """測試搜尋過濾器建構函數。"""

    def test_empty_filters(self):
        from graphiti_mcp_server import _build_search_filters
        filters = _build_search_filters()
        assert filters.node_labels is None
        assert filters.edge_types is None
        assert filters.created_at is None
        assert filters.invalid_at is None

    def test_node_labels_filter(self):
        from graphiti_mcp_server import _build_search_filters
        filters = _build_search_filters(node_labels=["Person", "Org"])
        assert filters.node_labels == ["Person", "Org"]

    def test_edge_types_filter(self):
        from graphiti_mcp_server import _build_search_filters
        filters = _build_search_filters(edge_types=["works_at"])
        assert filters.edge_types == ["works_at"]

    def test_created_after_filter(self):
        from graphiti_mcp_server import _build_search_filters
        filters = _build_search_filters(created_after="2025-01-01T00:00:00+00:00")
        assert filters.created_at is not None
        assert len(filters.created_at) == 1
        assert len(filters.created_at[0]) == 1

    def test_created_range_filter(self):
        from graphiti_mcp_server import _build_search_filters
        filters = _build_search_filters(
            created_after="2025-01-01T00:00:00+00:00",
            created_before="2025-12-31T23:59:59+00:00",
        )
        assert filters.created_at is not None
        assert len(filters.created_at[0]) == 2

    def test_only_valid_filter(self):
        from graphiti_mcp_server import _build_search_filters
        filters = _build_search_filters(only_valid=True)
        assert filters.invalid_at is not None


# ============================================================
# MemoryTask 測試
# ============================================================


class TestMemoryTask:
    """測試 MemoryTask 資料結構。"""

    def test_to_dict(self):
        from graphiti_mcp_server import MemoryTask
        task = MemoryTask(
            task_id="abc123",
            name="test",
            group_id="default",
            status="pending",
            created_at="2025-01-01T00:00:00Z",
        )
        d = task.to_dict()
        assert d["task_id"] == "abc123"
        assert d["status"] == "pending"
        assert d["chunks_total"] == 0


# ============================================================
# _simplify 輔助函數測試
# ============================================================


class TestSimplifyHelpers:
    """測試簡化輔助函數。"""

    def test_simplify_node(self):
        from graphiti_mcp_server import _simplify_node
        node = SimpleNamespace(
            name="Test Node",
            uuid="abc-123",
            created_at="2025-01-01",
            summary="A test node" * 100,
            group_id="default",
            labels=["Entity"],
            attributes={"key": "val", "name_embedding": [0.1]},
        )
        result = _simplify_node(node)
        assert result["name"] == "Test Node"
        assert "name_embedding" not in result["attributes"]
        assert len(result["summary"]) <= 200

    def test_simplify_edge(self):
        from graphiti_mcp_server import _simplify_edge
        edge = SimpleNamespace(
            uuid="edge-1",
            name="works_at",
            fact="Alice works at Google",
            group_id="default",
            source_node_uuid="s-1",
            target_node_uuid="t-1",
            created_at="2025-01-01",
            valid_at="2025-01-01",
            invalid_at=None,
            episodes=["ep1"],
        )
        result = _simplify_edge(edge)
        assert result["name"] == "works_at"
        assert result["invalid_at"] is None

    def test_simplify_community_node(self):
        from graphiti_mcp_server import _simplify_community_node
        node = SimpleNamespace(
            uuid="c-1",
            name="Tech Community",
            summary="A tech community" * 50,
            group_id="default",
            created_at="2025-01-01",
        )
        result = _simplify_community_node(node)
        assert result["name"] == "Tech Community"
        assert len(result["summary"]) <= 300

    def test_simplify_search_results(self):
        from graphiti_mcp_server import _simplify_search_results
        results = SimpleNamespace(
            nodes=[],
            edges=[],
            episodes=[],
            communities=[],
        )
        simplified = _simplify_search_results(results)
        assert simplified["nodes"] == []
        assert simplified["edges"] == []
        assert simplified["episodes"] == []
        assert simplified["communities"] == []


# ============================================================
# Web API 新端點 URL 測試（不啟動伺服器）
# ============================================================


class TestWebApiRouteExists:
    """驗證新 API 端點路由已正確註冊。"""

    def test_new_routes_in_create_web_routes(self):
        """確認 create_web_routes 輸出包含新路由路徑。"""
        import importlib
        from unittest.mock import AsyncMock

        from src.web_api import create_web_routes
        routes = create_web_routes(
            get_graphiti_fn=AsyncMock(),
            cors_origins=["*"],
        )
        route_paths = [getattr(r, "path", "") for r in routes]

        expected_paths = [
            "/api/memory/add-bulk",
            "/api/memory/add-triplet",
            "/api/communities",
            "/api/communities/build",
            "/api/search/advanced",
            "/api/analytics/stale",
            "/api/analytics/cleanup",
        ]

        for path in expected_paths:
            assert path in route_paths, f"缺少路由: {path}"


# ============================================================
# GRAPHITI_MCP_INSTRUCTIONS 測試
# ============================================================


class TestMCPInstructions:
    """測試 MCP 說明文字是否更新。"""

    def test_instructions_mention_new_tools(self):
        from graphiti_mcp_server import GRAPHITI_MCP_INSTRUCTIONS
        for tool in [
            "add_episode_bulk",
            "add_triplet",
            "build_communities",
            "advanced_search",
            "check_conflicts",
            "get_node_edges",
            "get_stale_memories",
            "cleanup_stale_memories",
        ]:
            assert tool in GRAPHITI_MCP_INSTRUCTIONS, f"說明缺少工具: {tool}"
