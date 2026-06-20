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

    def test_advanced_search_default_recipe_is_rrf(self):
        """advanced_search 預設 recipe 必須是可運作的 combined_rrf，
        而非會在無真實 cross_encoder 時失敗的 combined_cross_encoder。"""
        import inspect
        from graphiti_mcp_server import advanced_search
        sig = inspect.signature(advanced_search)
        assert sig.parameters["search_recipe"].default == "combined_rrf"


class TestExcludedEntityTypesKwarg:
    """回歸測試：excluded_entity_types 須以正確 kwarg 傳給 graphiti-core。

    歷史 bug：誤用 entity_types（需 dict）導致 graphiti-core 的
    validate_entity_types 拋 AttributeError，被外層 except 靜默降級為
    safe_mode（只建立不可搜尋的 EpisodicNode），使該記憶 recall=0。
    """

    def test_excluded_entity_types_uses_correct_kwarg(self):
        import asyncio
        import time
        from unittest.mock import AsyncMock
        from graphiti_core.nodes import EpisodeType
        from graphiti_mcp_server import _add_memory_full_mode

        graphiti = AsyncMock()
        result = asyncio.run(_add_memory_full_mode(
            graphiti=graphiti,
            name="t",
            episode_body="short body",
            group_id="g",
            source_description="d",
            episode_type=EpisodeType.text,
            episode_uuid=None,
            source="text",
            start_time=time.time(),
            excluded_entity_types=["Preference"],
        ))

        graphiti.add_episode.assert_awaited_once()
        kwargs = graphiti.add_episode.await_args.kwargs
        assert kwargs.get("excluded_entity_types") == ["Preference"]
        assert "entity_types" not in kwargs
        assert result["success"] is True

    def test_no_excluded_entity_types_passes_nothing(self):
        import asyncio
        import time
        from unittest.mock import AsyncMock
        from graphiti_core.nodes import EpisodeType
        from graphiti_mcp_server import _add_memory_full_mode

        graphiti = AsyncMock()
        asyncio.run(_add_memory_full_mode(
            graphiti=graphiti,
            name="t",
            episode_body="short body",
            group_id="g",
            source_description="d",
            episode_type=EpisodeType.text,
            episode_uuid=None,
            source="text",
            start_time=time.time(),
        ))
        kwargs = graphiti.add_episode.await_args.kwargs
        assert "excluded_entity_types" not in kwargs
        assert "entity_types" not in kwargs


class TestCrossEncoderClients:
    """測試可切換的 reranker 實作。"""

    def test_passthrough_keeps_order_and_scores(self):
        import asyncio
        from src.cross_encoder_client import PassthroughCrossEncoder
        out = asyncio.run(PassthroughCrossEncoder().rank("q", ["a", "b", "c"]))
        assert out == [("a", 1.0), ("b", 1.0), ("c", 1.0)]

    def test_llm_reranker_reorders_by_score(self):
        import asyncio
        import json
        from unittest.mock import AsyncMock, MagicMock
        from src.cross_encoder_client import LLMRerankerClient

        rr = LLMRerankerClient(model="m", base_url="http://x/v1", api_key="k", top_n=10)
        payload = {"scores": [
            {"index": 0, "score": 0.1},
            {"index": 1, "score": 0.9},
            {"index": 2, "score": 0.5},
        ]}
        msg = MagicMock(); msg.content = json.dumps(payload)
        choice = MagicMock(); choice.message = msg
        resp = MagicMock(); resp.choices = [choice]
        rr._client = MagicMock()
        rr._client.chat.completions.create = AsyncMock(return_value=resp)

        out = asyncio.run(rr.rank("q", ["p0", "p1", "p2"]))
        assert [p for p, _ in out] == ["p1", "p2", "p0"]

    def test_llm_reranker_fallback_keeps_order_on_error(self):
        import asyncio
        from unittest.mock import AsyncMock, MagicMock
        from src.cross_encoder_client import LLMRerankerClient

        rr = LLMRerankerClient(model="m")
        rr._client = MagicMock()
        rr._client.chat.completions.create = AsyncMock(side_effect=RuntimeError("boom"))
        out = asyncio.run(rr.rank("q", ["a", "b"]))
        assert [p for p, _ in out] == ["a", "b"]

    def test_llm_reranker_top_n_limits_scoring(self):
        import asyncio
        import json
        from unittest.mock import AsyncMock, MagicMock
        from src.cross_encoder_client import LLMRerankerClient

        rr = LLMRerankerClient(model="m", top_n=1)
        payload = {"scores": [{"index": 0, "score": 0.3}]}
        msg = MagicMock(); msg.content = json.dumps(payload)
        choice = MagicMock(); choice.message = msg
        resp = MagicMock(); resp.choices = [choice]
        rr._client = MagicMock()
        rr._client.chat.completions.create = AsyncMock(return_value=resp)

        out = asyncio.run(rr.rank("q", ["a", "b", "c"]))
        # 只有 a 被評分；b、c 未送評分，給 0 分排在後並保持原序
        assert out[0][0] == "a"
        assert [p for p, _ in out[1:]] == ["b", "c"]

    def test_llm_reranker_empty(self):
        import asyncio
        from src.cross_encoder_client import LLMRerankerClient
        assert asyncio.run(LLMRerankerClient(model="m").rank("q", [])) == []

    def test_bge_reranker_degrades_when_missing_dep(self):
        # 環境未安裝 sentence-transformers 時應回 None（降級），不拋錯
        from src.cross_encoder_client import make_bge_reranker
        result = make_bge_reranker()
        assert result is None or result.__class__.__name__ == "BGERerankerClient"


class TestCrossEncoderConfig:
    """測試 CrossEncoderConfig 驗證與載入。"""

    def test_default_provider_is_none(self):
        from src.config import GraphitiConfig
        assert GraphitiConfig().cross_encoder.provider == "none"

    def test_invalid_provider_rejected(self):
        from src.config import CrossEncoderConfig
        assert CrossEncoderConfig(provider="bad").get_errors()
        assert not CrossEncoderConfig(provider="llm").get_errors()
        assert not CrossEncoderConfig(provider="bge").get_errors()

    def test_bounds_validation(self):
        from src.config import CrossEncoderConfig
        assert CrossEncoderConfig(top_n=0).get_errors()
        assert CrossEncoderConfig(min_score=2.0).get_errors()

    def test_env_override(self):
        import os
        from src.config import load_config
        os.environ["CROSS_ENCODER_PROVIDER"] = "llm"
        os.environ["CROSS_ENCODER_TOP_N"] = "7"
        try:
            cfg = load_config()
            assert cfg.cross_encoder.provider == "llm"
            assert cfg.cross_encoder.top_n == 7
        finally:
            del os.environ["CROSS_ENCODER_PROVIDER"]
            del os.environ["CROSS_ENCODER_TOP_N"]


class TestSearchRecallEnhancements:
    """測試 Commit 3 召回/精度擴充。"""

    def test_candidate_pool_limit(self):
        from graphiti_mcp_server import _candidate_pool_limit
        assert _candidate_pool_limit(10) == 30   # 10*3
        assert _candidate_pool_limit(1) == 20    # 下限
        assert _candidate_pool_limit(50) == 100  # 上限

    def test_combined_mmr_lambda_fixed(self):
        from graphiti_mcp_server import SEARCH_RECIPES
        mmr = SEARCH_RECIPES["combined_mmr"]
        for sub in (mmr.node_config, mmr.edge_config, mmr.community_config):
            if sub is not None:
                assert sub.mmr_lambda == 0.5

    def test_build_filters_valid_at(self):
        from graphiti_mcp_server import _build_search_filters
        sf = _build_search_filters(
            valid_after="2026-01-01T00:00:00Z", valid_before="2026-12-31T00:00:00Z"
        )
        assert sf.valid_at is not None
        assert len(sf.valid_at[0]) == 2

    def test_apply_search_tuning(self):
        from graphiti_mcp_server import SEARCH_RECIPES, _apply_search_tuning
        cfg = SEARCH_RECIPES["node_rrf"].model_copy(deep=True)
        _apply_search_tuning(cfg, reranker_min_score=0.3, sim_min_score=0.7, mmr_lambda=0.4)
        assert cfg.reranker_min_score == 0.3
        assert cfg.node_config.sim_min_score == 0.7

    def test_edge_recipes_whitelist(self):
        from graphiti_mcp_server import _EDGE_SEARCH_RECIPES
        assert _EDGE_SEARCH_RECIPES == {
            "edge_rrf", "edge_mmr", "edge_node_distance",
            "edge_episode_mentions", "edge_cross_encoder",
        }

    def test_facts_signature_has_recipe_and_tuning(self):
        import inspect
        from graphiti_mcp_server import search_memory_facts
        params = inspect.signature(search_memory_facts).parameters
        for p in ("search_recipe", "valid_after", "valid_before",
                  "reranker_min_score", "sim_min_score", "mmr_lambda"):
            assert p in params, f"缺少參數 {p}"

    def test_nodes_signature_has_tuning(self):
        import inspect
        from graphiti_mcp_server import search_memory_nodes
        params = inspect.signature(search_memory_nodes).parameters
        for p in ("reranker_min_score", "sim_min_score", "mmr_lambda"):
            assert p in params, f"缺少參數 {p}"


class TestImportanceBoost:
    """測試 Commit 4 importance-aware 排序。"""

    def test_get_access_count_from_attributes(self):
        from types import SimpleNamespace
        from graphiti_mcp_server import _get_access_count
        assert _get_access_count(SimpleNamespace(attributes={"access_count": 5})) == 5

    def test_get_access_count_from_attr(self):
        from types import SimpleNamespace
        from graphiti_mcp_server import _get_access_count
        assert _get_access_count(SimpleNamespace(access_count=7, attributes={})) == 7

    def test_get_access_count_default_zero(self):
        from types import SimpleNamespace
        from graphiti_mcp_server import _get_access_count
        assert _get_access_count(SimpleNamespace(attributes={})) == 0

    def test_boost_promotes_high_access(self, monkeypatch):
        from types import SimpleNamespace
        import graphiti_mcp_server as s
        monkeypatch.setattr(
            s, "app_config",
            SimpleNamespace(enable_importance_tracking=True, importance_weight=0.1),
        )
        items = [
            SimpleNamespace(attributes={"access_count": 0}),
            SimpleNamespace(attributes={"access_count": 0}),
            SimpleNamespace(attributes={"access_count": 100}),  # 100*0.1=10 名提前
        ]
        out = s._apply_importance_boost(items)
        assert out[0].attributes["access_count"] == 100

    def test_boost_stable_when_equal_access(self, monkeypatch):
        from types import SimpleNamespace
        import graphiti_mcp_server as s
        monkeypatch.setattr(
            s, "app_config",
            SimpleNamespace(enable_importance_tracking=True, importance_weight=0.1),
        )
        items = [SimpleNamespace(name=f"n{i}", attributes={"access_count": 0}) for i in range(4)]
        out = s._apply_importance_boost(items)
        assert [i.name for i in out] == ["n0", "n1", "n2", "n3"]  # 同分保留原序

    def test_boost_disabled_returns_unchanged(self, monkeypatch):
        from types import SimpleNamespace
        import graphiti_mcp_server as s
        monkeypatch.setattr(
            s, "app_config",
            SimpleNamespace(enable_importance_tracking=False, importance_weight=0.1),
        )
        items = [
            SimpleNamespace(attributes={"access_count": 0}),
            SimpleNamespace(attributes={"access_count": 100}),
        ]
        assert s._apply_importance_boost(items) == items


class TestQueryPreprocessing:
    """測試 Commit 5 query 前處理。"""

    def test_normalize_fullwidth_to_halfwidth(self):
        from graphiti_mcp_server import _normalize_query
        assert _normalize_query("ＡＰＩ") == "API"
        assert _normalize_query("ｈｅｌｌｏ１２３") == "hello123"

    def test_normalize_compress_whitespace(self):
        from graphiti_mcp_server import _normalize_query
        assert _normalize_query("  知識   圖譜  ") == "知識 圖譜"

    def test_normalize_fullwidth_space(self):
        from graphiti_mcp_server import _normalize_query
        assert _normalize_query("知識　圖譜") == "知識 圖譜"

    def test_normalize_preserves_chinese(self):
        from graphiti_mcp_server import _normalize_query
        assert _normalize_query("知識圖譜記憶") == "知識圖譜記憶"

    def test_normalize_empty(self):
        from graphiti_mcp_server import _normalize_query
        assert _normalize_query("") == ""

    def test_query_expansion_config_default_off(self):
        from src.config import GraphitiConfig
        cfg = GraphitiConfig()
        assert cfg.enable_query_expansion is False
        assert cfg.query_expansion_terms == 5


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

        from starlette.routing import Mount
        from src.web_api import create_web_routes
        routes = create_web_routes(
            get_graphiti_fn=AsyncMock(),
            cors_origins=["*"],
        )
        # 解包 CORS sub-app（[Mount("/", sub_app)] → sub_app.routes）
        inner = routes[0].app.routes if routes and isinstance(routes[0], Mount) else routes
        route_paths = [getattr(r, "path", "") for r in inner]

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
