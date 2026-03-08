#!/usr/bin/env python3
"""
Graphiti MCP Server 單元測試
============================

使用 mock 測試核心邏輯，不需要外部服務（Neo4j、Ollama）。

測試範圍：
- OllamaClient 字段映射與修復
- 異常處理模組
- 速率限制器
- 輔助函數
"""

import logging
import sys
import os
import time
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

# 確保能 import 專案模組
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================
# OllamaClient 字段映射常量
# ============================================================

from src.ollama_graphiti_client import (
    TOP_LEVEL_FIELD_MAP,
    ENTITY_FIELD_MAP,
    ENTITY_DEFAULT_FIELDS,
    ENTITY_REMOVE_FIELDS,
    EDGE_SOURCE_KEYS,
    EDGE_TARGET_KEYS,
    EDGE_RELATION_KEYS,
    EDGE_DEFAULT_FIELDS,
    RESOLUTION_FIELD_MAP,
    RESOLUTION_DEFAULT_FIELDS,
    OptimizedOllamaClient,
)
from graphiti_core.llm_client.config import LLMConfig


@pytest.fixture
def client():
    """建立測試用的 OllamaClient。"""
    cfg = LLMConfig(api_key="test", model="test", base_url="http://localhost:11434")
    return OptimizedOllamaClient(cfg)


class TestFieldMappingConstants:
    """測試集中化字段映射常量的正確性。"""

    def test_top_level_map(self):
        assert "實體" in TOP_LEVEL_FIELD_MAP
        assert TOP_LEVEL_FIELD_MAP["實體"] == "extracted_entities"

    def test_entity_field_map(self):
        assert ENTITY_FIELD_MAP["entity_name"] == "name"
        assert ENTITY_FIELD_MAP["entity_type_name"] == "entity_type"

    def test_edge_source_keys(self):
        assert "source_id" in EDGE_SOURCE_KEYS
        assert "subject_id" in EDGE_SOURCE_KEYS

    def test_edge_target_keys(self):
        assert "target_id" in EDGE_TARGET_KEYS
        assert "object_id" in EDGE_TARGET_KEYS

    def test_edge_relation_keys(self):
        assert "relationship" in EDGE_RELATION_KEYS
        assert "predicate" in EDGE_RELATION_KEYS

    def test_resolution_field_map(self):
        assert RESOLUTION_FIELD_MAP["duplication_idx"] == "duplicate_idx"


# ============================================================
# OllamaClient 實體字段修復
# ============================================================

class TestFixEntityFields:
    """測試 _fix_entity_fields 方法。"""

    def test_entity_name_mapping(self, client):
        entity = {"entity_name": "Alice", "entity_type": "Person"}
        result = client._fix_entity_fields(entity)
        assert result["name"] == "Alice"
        assert "entity_name" not in result

    def test_entity_type_name_mapping(self, client):
        entity = {"name": "Bob", "entity_type_name": "Person"}
        result = client._fix_entity_fields(entity)
        assert result["entity_type"] == "Person"
        assert "entity_type_name" not in result

    def test_no_overwrite_existing_name(self, client):
        entity = {"entity_name": "Wrong", "name": "Right", "entity_type": "Person"}
        result = client._fix_entity_fields(entity)
        assert result["name"] == "Right"

    def test_summary_dict_to_string(self, client):
        entity = {"name": "X", "summary": {"description": "desc here"}}
        result = client._fix_entity_fields(entity)
        assert result["summary"] == "desc here"

    def test_summary_none_fallback(self, client):
        entity = {"name": "X", "observation": "obs text"}
        result = client._fix_entity_fields(entity)
        assert result["summary"] == "obs text"

    def test_default_fields_added(self, client):
        entity = {"name": "X"}
        result = client._fix_entity_fields(entity)
        for key, default in ENTITY_DEFAULT_FIELDS.items():
            assert result[key] == default

    def test_unwanted_fields_removed(self, client):
        entity = {"name": "X", "description": "d", "score": 0.9, "mentioned": True}
        result = client._fix_entity_fields(entity)
        for key in ENTITY_REMOVE_FIELDS:
            assert key not in result

    def test_entity_type_id_forced_zero(self, client):
        entity = {"name": "X", "entity_type_id": 99}
        result = client._fix_entity_fields(entity)
        assert result["entity_type_id"] == 0

    def test_observations_string_to_list(self, client):
        entity = {"name": "X", "observations": "single obs"}
        result = client._fix_entity_fields(entity)
        assert result["observations"] == ["single obs"]


# ============================================================
# OllamaClient 邊字段修復
# ============================================================

class TestFixEdgeFields:
    """測試 _fix_edge_fields 方法。"""

    def test_source_id_mapping(self, client):
        json_data = {"extracted_entities": [{"name": "A"}, {"name": "B"}]}
        edge = {"source_id": 0, "target_id": 1}
        result = client._fix_edge_fields(edge, json_data)
        assert result["source_entity_id"] == 0
        assert result["target_entity_id"] == 1

    def test_subject_object_mapping(self, client):
        json_data = {"extracted_entities": [{"name": "A"}, {"name": "B"}]}
        edge = {"subject_id": 0, "object_id": 1}
        result = client._fix_edge_fields(edge, json_data)
        assert result["source_entity_id"] == 0
        assert result["target_entity_id"] == 1

    def test_relation_type_mapping(self, client):
        json_data = {"extracted_entities": [{"name": "A"}, {"name": "B"}]}
        edge = {"source_entity_id": 0, "target_entity_id": 1, "relationship": "likes"}
        result = client._fix_edge_fields(edge, json_data)
        assert result["relation_type"] == "likes"

    def test_predicate_mapping(self, client):
        json_data = {"extracted_entities": [{"name": "A"}, {"name": "B"}]}
        edge = {"source_entity_id": 0, "target_entity_id": 1, "predicate": "works_at"}
        result = client._fix_edge_fields(edge, json_data)
        assert result["relation_type"] == "works_at"

    def test_default_relation_type(self, client):
        json_data = {"extracted_entities": [{"name": "A"}]}
        edge = {"source_entity_id": 0, "target_entity_id": 0}
        result = client._fix_edge_fields(edge, json_data)
        assert result["relation_type"] == "RELATES_TO"

    def test_default_fields_added(self, client):
        json_data = {"extracted_entities": [{"name": "A"}]}
        edge = {"source_entity_id": 0, "target_entity_id": 0}
        result = client._fix_edge_fields(edge, json_data)
        for key, default in EDGE_DEFAULT_FIELDS.items():
            assert result[key] == default


# ============================================================
# OllamaClient 實體 ID 解析
# ============================================================

class TestResolveEntityId:
    """測試 _resolve_entity_id 方法。"""

    def test_none_returns_fallback(self, client):
        entities = [{"name": "A"}, {"name": "B"}]
        assert client._resolve_entity_id(None, entities, fallback=1) == 1

    def test_int_clamped_to_range(self, client):
        entities = [{"name": "A"}, {"name": "B"}]
        assert client._resolve_entity_id(99, entities) == 1
        assert client._resolve_entity_id(-5, entities) == 0

    def test_entity_format(self, client):
        entities = [{"name": "A"}, {"name": "B"}, {"name": "C"}]
        assert client._resolve_entity_id("ENTITY_2", entities) == 2

    def test_numeric_string(self, client):
        entities = [{"name": "A"}, {"name": "B"}]
        assert client._resolve_entity_id("1", entities) == 1

    def test_name_exact_match(self, client):
        entities = [{"name": "Alice"}, {"name": "Bob"}]
        assert client._resolve_entity_id("Bob", entities) == 1

    def test_name_case_insensitive(self, client):
        entities = [{"name": "Alice"}, {"name": "Bob"}]
        assert client._resolve_entity_id("bob", entities) == 1

    def test_name_partial_match(self, client):
        entities = [{"name": "Alice Smith"}, {"name": "Bob Jones"}]
        assert client._resolve_entity_id("Alice", entities) == 0

    def test_empty_entities_returns_zero(self, client):
        assert client._resolve_entity_id("anything", []) == 0


# ============================================================
# OllamaClient 頂層字段映射
# ============================================================

class TestFixFieldMappings:
    """測試 _fix_field_mappings 方法。"""

    def test_chinese_entity_key(self, client):
        data = {"實體": [{"entity_name": "X"}]}
        result = client._fix_field_mappings(data)
        assert "extracted_entities" in result
        assert "實體" not in result

    def test_entity_list_items_fixed(self, client):
        data = {"extracted_entities": [{"entity_name": "Test", "entity_type": "Thing"}]}
        result = client._fix_field_mappings(data)
        assert result["extracted_entities"][0]["name"] == "Test"

    def test_non_dict_entities_filtered(self, client):
        data = {"extracted_entities": [{"name": "OK"}, "invalid", 123]}
        result = client._fix_field_mappings(data)
        assert len(result["extracted_entities"]) == 1

    def test_edges_fixed(self, client):
        data = {
            "extracted_entities": [{"name": "A"}, {"name": "B"}],
            "edges": [{"source_id": 0, "target_id": 1, "relationship": "knows"}],
        }
        result = client._fix_field_mappings(data)
        assert result["edges"][0]["relation_type"] == "knows"


# ============================================================
# OllamaClient 解析字段修復
# ============================================================

class TestFixResolutionFields:
    """測試 _fix_resolution_fields 方法。"""

    def test_duplication_idx_renamed(self, client):
        r = {"duplication_idx": 3}
        result = client._fix_resolution_fields(r)
        assert result["duplicate_idx"] == 3
        assert "duplication_idx" not in result

    def test_defaults_set(self, client):
        result = client._fix_resolution_fields({})
        for key, default in RESOLUTION_DEFAULT_FIELDS.items():
            assert result[key] == default


# ============================================================
# OllamaClient _fix_summary_fields（迭代版）
# ============================================================

class TestFixSummaryFields:
    """測試迭代式 _fix_summary_fields 方法。"""

    def test_nested_dict_summary(self, client):
        data = {"result": {"summary": {"description": "test desc"}}}
        client._fix_summary_fields(data)
        assert data["result"]["summary"] == "test desc"

    def test_list_with_summary(self, client):
        data = {"items": [{"summary": {"content": "c1"}}, {"summary": "already string"}]}
        client._fix_summary_fields(data)
        assert data["items"][0]["summary"] == "c1"
        assert data["items"][1]["summary"] == "already string"

    def test_deeply_nested(self, client):
        data = {"a": {"b": {"c": {"summary": {"description": "deep"}}}}}
        client._fix_summary_fields(data)
        assert data["a"]["b"]["c"]["summary"] == "deep"


# ============================================================
# 異常處理模組
# ============================================================

from src.exceptions import (
    GraphitiMCPError,
    ConfigurationError,
    OllamaError,
    EmbeddingError,
    Neo4jError,
    PydanticValidationError,
    CosineSimilarityError,
    handle_exception,
    create_error_response,
    CommonErrors,
)


class TestGraphitiMCPError:
    """測試基礎異常類別。"""

    def test_basic_error(self):
        err = GraphitiMCPError("test error")
        assert err.message == "test error"
        assert err.error_code == "GRAPHITI_ERROR"

    def test_to_dict(self):
        err = GraphitiMCPError("msg", error_code="TEST", details={"key": "val"})
        d = err.to_dict()
        assert d["error"] is True
        assert d["error_code"] == "TEST"
        assert d["details"]["key"] == "val"

    def test_traceback_truncation(self):
        err = GraphitiMCPError("msg")
        err.traceback_str = "x" * 2000
        d = err.to_dict()
        assert len(d["traceback"]) == 1003  # 1000 + "..."

    def test_str_format(self):
        err = GraphitiMCPError("msg", details={"a": 1}, cause=ValueError("inner"))
        s = str(err)
        assert "[GRAPHITI_ERROR]" in s
        assert "Caused by" in s


class TestHandleException:
    """測試異常分類函數。"""

    def test_already_graphiti_error(self):
        err = OllamaError("existing")
        result = handle_exception(err)
        assert result is err

    def test_connection_error_classified(self):
        err = ConnectionError("refused")
        result = handle_exception(err)
        assert isinstance(result, OllamaError)

    def test_timeout_classified(self):
        err = TimeoutError("timed out")
        result = handle_exception(err)
        assert isinstance(result, OllamaError)

    def test_neo4j_by_message(self):
        err = RuntimeError("neo4j connection failed")
        result = handle_exception(err)
        assert isinstance(result, Neo4jError)

    def test_ollama_by_message(self):
        err = RuntimeError("ollama service error")
        result = handle_exception(err)
        assert isinstance(result, OllamaError)

    def test_cosine_by_message(self):
        err = RuntimeError("cosine similarity computation failed")
        result = handle_exception(err)
        assert isinstance(result, CosineSimilarityError)

    def test_embed_error_requires_both_keywords(self):
        # "embedding 已完成" 不應被歸類為 EmbeddingError
        err = RuntimeError("embedding 已完成 successfully")
        result = handle_exception(err)
        assert not isinstance(result, EmbeddingError)

    def test_embed_error_with_both(self):
        err = RuntimeError("embed vector error occurred")
        result = handle_exception(err)
        assert isinstance(result, EmbeddingError)

    def test_unknown_error(self):
        err = RuntimeError("something random")
        result = handle_exception(err)
        assert result.error_code == "UNKNOWN_ERROR"

    def test_context_included(self):
        err = RuntimeError("some failure")
        result = handle_exception(err, context="during test")
        assert "during test" in result.message


class TestCreateErrorResponse:
    """測試標準化錯誤響應。"""

    def test_returns_dict(self):
        result = create_error_response(RuntimeError("test"))
        assert isinstance(result, dict)
        assert result["error"] is True

    def test_preserves_error_code(self):
        result = create_error_response(OllamaError("fail"))
        assert result["error_code"] == "OLLAMA_ERROR"


class TestCommonErrors:
    """測試預定義錯誤工廠。"""

    def test_ollama_connection_failed(self):
        err = CommonErrors.ollama_connection_failed("http://localhost:11434")
        assert isinstance(err, OllamaError)
        assert "localhost" in str(err.details)

    def test_neo4j_connection_failed(self):
        err = CommonErrors.neo4j_connection_failed("bolt://localhost:7687")
        assert isinstance(err, Neo4jError)


# ============================================================
# 速率限制器
# ============================================================

from src.web_api import _RateLimiter, SEARCH_TIMEOUT


class TestRateLimiter:
    """測試速率限制器。"""

    def test_allows_within_limit(self):
        limiter = _RateLimiter(max_requests=3, window_seconds=60)
        assert limiter.is_allowed("1.2.3.4") is True
        assert limiter.is_allowed("1.2.3.4") is True
        assert limiter.is_allowed("1.2.3.4") is True

    def test_blocks_over_limit(self):
        limiter = _RateLimiter(max_requests=2, window_seconds=60)
        limiter.is_allowed("1.2.3.4")
        limiter.is_allowed("1.2.3.4")
        assert limiter.is_allowed("1.2.3.4") is False

    def test_different_ips_independent(self):
        limiter = _RateLimiter(max_requests=1, window_seconds=60)
        assert limiter.is_allowed("1.1.1.1") is True
        assert limiter.is_allowed("2.2.2.2") is True
        assert limiter.is_allowed("1.1.1.1") is False

    def test_search_timeout_is_reasonable(self):
        assert 10 <= SEARCH_TIMEOUT <= 120


# ============================================================
# MCP 工具輔助函數
# ============================================================


class TestSimplifyNode:
    """測試 _simplify_node 輔助函數。"""

    def test_basic_simplification(self):
        from graphiti_mcp_server import _simplify_node

        node = SimpleNamespace(
            name="Test Node",
            uuid="abc-123",
            created_at="2026-01-01",
            summary="A short summary",
            group_id="test-group",
            labels=["Entity"],
            attributes={"key": "val", "name_embedding": [0.1, 0.2]},
        )
        result = _simplify_node(node)
        assert result["name"] == "Test Node"
        assert result["uuid"] == "abc-123"
        assert result["group_id"] == "test-group"
        # embedding 字段應被過濾
        assert "name_embedding" not in result["attributes"]
        assert "key" in result["attributes"]

    def test_missing_attributes(self):
        from graphiti_mcp_server import _simplify_node

        node = SimpleNamespace(name="No attrs", uuid="x", created_at="", summary="", group_id="", labels=[])
        result = _simplify_node(node)
        assert result["attributes"] == {}

    def test_summary_truncation(self):
        from graphiti_mcp_server import _simplify_node

        node = SimpleNamespace(
            name="X", uuid="x", created_at="", summary="a" * 500,
            group_id="", labels=[], attributes={},
        )
        result = _simplify_node(node)
        assert len(result["summary"]) == 200


class TestSimplifyEdge:
    """測試 _simplify_edge 輔助函數。"""

    def test_basic_simplification(self):
        from graphiti_mcp_server import _simplify_edge

        edge = SimpleNamespace(
            uuid="edge-1",
            name="knows",
            fact="Alice knows Bob",
            group_id="g1",
            source_node_uuid="n1",
            target_node_uuid="n2",
            created_at="2026-01-01",
            valid_at="2026-01-01",
            invalid_at=None,
            episodes=["ep1"],
        )
        result = _simplify_edge(edge)
        assert result["name"] == "knows"
        assert result["fact"] == "Alice knows Bob"
        assert result["invalid_at"] is None

    def test_with_invalid_at(self):
        from graphiti_mcp_server import _simplify_edge

        edge = SimpleNamespace(
            uuid="e", name="r", fact="f", group_id="g",
            source_node_uuid="s", target_node_uuid="t",
            created_at="", valid_at="", invalid_at="2026-06-01",
            episodes=[],
        )
        result = _simplify_edge(edge)
        assert result["invalid_at"] == "2026-06-01T00:00:00+00:00"


class TestParseEpisodeType:
    """測試 _parse_episode_type 輔助函數。"""

    @pytest.fixture(autouse=True)
    def _patch_logger(self, monkeypatch):
        """graphiti_mcp_server 的 logger 在 main() 前是 None，需要 patch。"""
        import graphiti_mcp_server
        if graphiti_mcp_server.logger is None:
            monkeypatch.setattr(graphiti_mcp_server, "logger", logging.getLogger("test"))

    def test_valid_text(self):
        from graphiti_mcp_server import _parse_episode_type
        from graphiti_core.nodes import EpisodeType

        assert _parse_episode_type("text") == EpisodeType.text

    def test_case_insensitive(self):
        from graphiti_mcp_server import _parse_episode_type
        from graphiti_core.nodes import EpisodeType

        assert _parse_episode_type("Text") == EpisodeType.text

    def test_invalid_returns_text(self):
        from graphiti_mcp_server import _parse_episode_type
        from graphiti_core.nodes import EpisodeType

        assert _parse_episode_type("invalid_type") == EpisodeType.text

    def test_none_returns_text(self):
        from graphiti_mcp_server import _parse_episode_type
        from graphiti_core.nodes import EpisodeType

        assert _parse_episode_type(None) == EpisodeType.text


# ============================================================
# OllamaClient _create_fallback_response
# ============================================================

class TestCreateFallbackResponse:
    """測試統一的 fallback response 方法。"""

    def test_with_no_model(self, client):
        result = client._create_fallback_response(None)
        assert result is None

    def test_no_model_validate_returns_none(self, client):
        # str 沒有 model_validate 屬性，應返回 None
        result = client._create_fallback_response(str, {"key": "val"})
        assert result is None

    def test_with_pydantic_model(self, client):
        from typing import List
        from pydantic import BaseModel

        class DummyModel(BaseModel):
            name: str = "default"
            items: List[str] = []  # 使用 typing.List 以確保 __origin__ 正確

        result = client._create_fallback_response(DummyModel)
        assert result is not None
        # 使用型別預設值填充（str→""），不讀取 Pydantic default
        assert isinstance(result["name"], str)
        assert result["items"] == []


# ============================================================
# Config 模組
# ============================================================

from src.config import load_config


class TestLoadConfig:
    """測試配置載入。"""

    def test_default_config(self):
        cfg = load_config()
        assert cfg.neo4j.uri is not None
        assert cfg.ollama.model is not None
        assert cfg.embedder.model is not None
        assert cfg.embedder.dimensions > 0

    def test_neo4j_default_port(self):
        cfg = load_config()
        assert "7687" in cfg.neo4j.uri


# ============================================================
# OllamaEmbedder 動態批次大小
# ============================================================

from src.ollama_embedder import OllamaEmbedder


class TestComputeBatchSize:
    """測試動態批次大小計算。"""

    def test_short_texts(self):
        texts = ["hi"] * 10
        assert OllamaEmbedder._compute_batch_size(texts) == 30

    def test_medium_texts(self):
        texts = ["a" * 200] * 10
        assert OllamaEmbedder._compute_batch_size(texts) == 15

    def test_long_texts(self):
        texts = ["a" * 500] * 10
        assert OllamaEmbedder._compute_batch_size(texts) == 8

    def test_very_long_texts(self):
        texts = ["a" * 1000] * 10
        assert OllamaEmbedder._compute_batch_size(texts) == 4

    def test_empty_list(self):
        assert OllamaEmbedder._compute_batch_size([]) == 10
