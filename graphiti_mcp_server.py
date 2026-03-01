#!/usr/bin/env python3
"""
Graphiti Ollama MCP Server
==========================

基於知識圖譜的 AI 代理記憶服務，使用 Ollama 作為本地 LLM 後端。

主要功能：
    - 記憶添加與檢索（支援安全模式和完整模式）
    - 節點與事實搜索
    - 記憶片段管理
    - 多種傳輸模式支援（stdio, SSE, HTTP streamable）

技術特點：
    - 解決 IndexError 問題，提升穩定性
    - 支援 Pydantic 驗證修復
    - 完整的錯誤處理機制
    - 並發安全的初始化機制

作者：RD-CAT
版本：1.0.0
"""

import argparse
import asyncio
import logging
import os
import sys
import time
import uuid as uuid_mod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# 載入本地模組
from src.config import GraphitiConfig, load_config
from src.exceptions import (
    GraphitiMCPError,
    handle_exception,
    create_error_response,
    CommonErrors,
)
from src.logging_setup import (
    setup_logging,
    log_system_info,
    log_config_summary,
    log_operation_start,
    log_operation_success,
    log_operation_error,
)
from src.ollama_graphiti_client import OptimizedOllamaClient
from src.ollama_embedder import OllamaEmbedder

# 載入 Graphiti 核心模組
from graphiti_core import Graphiti
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.edges import EntityEdge
from graphiti_core.nodes import EpisodicNode, EpisodeType
from graphiti_core.search.search_config_recipes import NODE_HYBRID_SEARCH_RRF
from graphiti_core.search.search_filters import SearchFilters
from graphiti_core.utils.maintenance.graph_data_operations import clear_data

# 載入內容預處理模組
from src.content_preprocessor import smart_chunk, should_chunk

# 載入環境變數
load_dotenv()


# ============================================================================
# 背景任務資料結構
# ============================================================================


@dataclass
class MemoryTask:
    """背景記憶處理任務狀態。"""

    task_id: str
    name: str
    group_id: str
    status: str = "pending"  # pending, processing, completed, failed
    created_at: str = ""
    completed_at: Optional[str] = None
    result: Optional[dict] = None
    error: Optional[str] = None
    chunks_total: int = 0
    chunks_done: int = 0

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "group_id": self.group_id,
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "chunks_total": self.chunks_total,
            "chunks_done": self.chunks_done,
            "result": self.result,
            "error": self.error,
        }


# ============================================================================
# 全域變數
# ============================================================================

app_config: GraphitiConfig = None  # 應用程式配置
logger = None  # 日誌記錄器
graphiti_instance = None  # Graphiti 實例快取
_init_lock = asyncio.Lock()  # 初始化鎖，防止並發競態
default_group_id: str = os.getenv("GROUP_ID", "default")  # 預設記憶分組 ID
_memory_tasks: Dict[str, MemoryTask] = {}  # 背景記憶任務儲存

# ============================================================================
# MCP 伺服器配置
# ============================================================================

GRAPHITI_MCP_INSTRUCTIONS = """
Graphiti 是一個基於知識圖譜的 AI 代理記憶服務。

主要功能：
1. add_memory_simple - 添加記憶（文字、訊息或 JSON）到知識圖譜
2. search_memory_nodes - 使用自然語言查詢搜索節點（實體）
3. search_memory_facts - 搜索相關事實（實體間的關係）
4. get_episodes - 獲取最近的記憶片段
5. delete_episode / delete_entity_edge - 刪除記憶或關係
6. get_entity_edge - 獲取特定實體邊的詳細資訊
7. get_status / test_connection - 檢查服務狀態
8. clear_graph - 清除圖資料庫

每條資訊按 group_id 組織，讓您可以維護獨立的知識領域。
"""

# 建立 FastMCP 應用程式
mcp = FastMCP("graphiti-ollama-memory", instructions=GRAPHITI_MCP_INSTRUCTIONS)


# ============================================================================
# 核心功能函數
# ============================================================================


async def initialize_graphiti() -> Graphiti:
    """
    初始化並返回 Graphiti 實例。

    使用快取機制和 asyncio.Lock 避免重複初始化和並發競態。

    Returns:
        Graphiti: 已初始化的 Graphiti 實例

    Raises:
        GraphitiMCPError: 當初始化失敗時拋出

    Note:
        - LLM 客戶端初始化失敗時會設為 None，不影響其他功能
        - 併發數量限制為 3 以避免 IndexError
        - 初始化時自動建立索引和約束
    """
    global graphiti_instance

    if graphiti_instance is not None:
        return graphiti_instance

    async with _init_lock:
        # Double-check：取得鎖後再次檢查（其他協程可能已完成初始化）
        if graphiti_instance is not None:
            return graphiti_instance

        start_time = time.time()
        log_operation_start("initialize_graphiti")

        try:
            # 初始化 LLM 客戶端（失敗時設為 None）
            llm_client = _create_llm_client()

            # 建立嵌入器
            embedder = OllamaEmbedder(
                model=app_config.embedder.model,
                base_url=app_config.embedder.base_url,
                dimensions=app_config.embedder.dimensions,
            )

            # 建立 Graphiti 實例
            max_coroutines = app_config.memory_performance.max_coroutines if app_config else 5
            graphiti_instance = Graphiti(
                uri=app_config.neo4j.uri,
                user=app_config.neo4j.user,
                password=app_config.neo4j.password,
                llm_client=llm_client,
                embedder=embedder,
                max_coroutines=max_coroutines,
            )

            # 確保索引和約束已建立（clear_graph 後重建）
            await graphiti_instance.build_indices_and_constraints()

            duration = time.time() - start_time
            log_operation_success("initialize_graphiti", duration)

            return graphiti_instance

        except Exception as e:
            graphiti_instance = None  # 確保失敗時不留殘留
            duration = time.time() - start_time
            log_operation_error("initialize_graphiti", e, duration=duration)

            if isinstance(e, GraphitiMCPError):
                raise
            raise handle_exception(e, "Graphiti 初始化失敗")


def _create_llm_client() -> Optional[OptimizedOllamaClient]:
    """
    建立 Ollama LLM 客戶端。

    Returns:
        OptimizedOllamaClient: 成功時返回客戶端實例
        None: 初始化失敗時返回 None

    Note:
        此函數不會拋出例外，失敗時僅記錄警告並返回 None。
    """
    try:
        llm_config = LLMConfig(
            base_url=app_config.ollama.base_url,
            model=app_config.ollama.model,
            temperature=app_config.ollama.temperature,
        )
        client = OptimizedOllamaClient(config=llm_config)
        logging.getLogger("graphiti").info("LLM 客戶端初始化成功")
        return client
    except Exception as e:
        logging.getLogger("graphiti").warning(f"LLM 客戶端初始化失敗，使用 None: {e}")
        return None


# ============================================================================
# MCP 工具函數
# ============================================================================


@mcp.tool()
async def add_memory_simple(
    name: str,
    episode_body: str,
    group_id: Optional[str] = None,
    source_description: str = "MCP Server",
    source: str = "text",
    episode_uuid: Optional[str] = None,
    use_safe_mode: bool = False,
    background: bool = False,
    excluded_entity_types: Optional[List[str]] = None,
) -> dict:
    """
    添加記憶到知識圖譜。

    支援兩種模式：
    - 完整模式（預設）：使用完整流程，包含實體提取和關係建立，記憶可被搜尋
    - 安全模式：直接建立節點，跳過實體提取，速度快但記憶無法被搜尋

    效能優化：
    - 長文本自動切分為多段處理，減少每段 LLM 呼叫次數
    - 支援背景非同步處理（background=True），立刻返回 task_id
    - 可排除不需要的實體類型以減少提取量

    Args:
        name: 記憶片段的名稱
        episode_body: 記憶片段的內容（source='json' 時應為 JSON 字串）
        group_id: 記憶分組 ID，用於組織不同領域的記憶
        source_description: 來源描述
        source: 來源類型 ('text', 'json', 'message')
        episode_uuid: 可選的記憶片段 UUID
        use_safe_mode: 是否使用安全模式
        background: 是否在背景非同步處理（立刻返回 task_id）
        excluded_entity_types: 排除的實體類型列表，減少不需要的實體提取

    Returns:
        dict: 包含操作結果的字典
            - success: 是否成功
            - message: 結果訊息
            - uuid: 記憶片段 UUID
            - processing_time: 處理時間
            - method: 使用的方法
            - task_id: （僅 background=True）背景任務 ID
    """
    # 使用環境變數的預設 group_id
    if group_id is None:
        group_id = default_group_id

    # 背景模式：建立 task 後立刻返回
    if background:
        task_id = str(uuid_mod.uuid4())[:8]
        task = MemoryTask(
            task_id=task_id,
            name=name,
            group_id=group_id,
            status="pending",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        _memory_tasks[task_id] = task

        asyncio.create_task(
            _background_add_memory(
                task, name, episode_body, group_id, source_description,
                source, episode_uuid, use_safe_mode, excluded_entity_types,
            )
        )

        return {
            "success": True,
            "message": f"記憶 '{name}' 已加入背景處理佇列",
            "task_id": task_id,
            "method": "background",
            "note": "使用 get_memory_task_status(task_id) 查詢進度",
        }

    # 同步模式
    return await _sync_add_memory(
        name, episode_body, group_id, source_description,
        source, episode_uuid, use_safe_mode, excluded_entity_types,
    )


async def _sync_add_memory(
    name: str,
    episode_body: str,
    group_id: str,
    source_description: str,
    source: str,
    episode_uuid: Optional[str],
    use_safe_mode: bool,
    excluded_entity_types: Optional[List[str]],
) -> dict:
    """同步執行記憶添加。"""
    start_time = time.time()
    log_operation_start("add_memory", name=name[:50], source=source)

    try:
        graphiti = await initialize_graphiti()
        episode_type = _parse_episode_type(source)

        if use_safe_mode:
            return await _add_memory_safe_mode(
                graphiti, name, episode_body, group_id, source_description, source, start_time
            )
        else:
            try:
                return await _add_memory_full_mode(
                    graphiti, name, episode_body, group_id, source_description,
                    episode_type, episode_uuid, source, start_time,
                    excluded_entity_types=excluded_entity_types,
                )
            except Exception as full_err:
                logger.warning(
                    f"完整模式失敗，自動降級到安全模式: {str(full_err)[:200]}"
                )
                safe_result = await _add_memory_safe_mode(
                    graphiti, name, episode_body, group_id,
                    source_description, source, start_time
                )
                safe_result["mode_used"] = "safe"
                safe_result["fallback_reason"] = str(full_err)[:200]
                safe_result["note"] = "完整模式失敗，已自動降級到安全模式保底"
                return safe_result

    except Exception as e:
        duration = time.time() - start_time
        log_operation_error("add_memory", e, duration=duration)
        return create_error_response(
            CommonErrors.operation_failed("add_memory", str(e)),
            f"記憶添加過程中發生錯誤: {e}",
        )


async def _background_add_memory(
    task: MemoryTask,
    name: str,
    episode_body: str,
    group_id: str,
    source_description: str,
    source: str,
    episode_uuid: Optional[str],
    use_safe_mode: bool,
    excluded_entity_types: Optional[List[str]],
) -> None:
    """背景執行記憶添加任務。"""
    task.status = "processing"
    try:
        result = await _sync_add_memory(
            name, episode_body, group_id, source_description,
            source, episode_uuid, use_safe_mode, excluded_entity_types,
        )
        task.result = result
        task.status = "completed" if result.get("success") else "failed"
        task.error = result.get("error") if not result.get("success") else None
    except Exception as e:
        task.status = "failed"
        task.error = str(e)[:500]
        logger.error(f"背景任務 {task.task_id} 失敗: {e}")
    finally:
        task.completed_at = datetime.now(timezone.utc).isoformat()


def _parse_episode_type(source: str) -> EpisodeType:
    """
    解析來源類型字串為 EpisodeType 列舉。

    Args:
        source: 來源類型字串

    Returns:
        EpisodeType: 對應的列舉值，無效時返回 text
    """
    try:
        return EpisodeType[source.lower()]
    except (KeyError, AttributeError):
        logger.warning(f"未知的 source 類型 '{source}'，使用 'text' 作為預設")
        return EpisodeType.text


async def _add_memory_safe_mode(
    graphiti: Graphiti,
    name: str,
    content: str,
    group_id: str,
    source_description: str,
    source: str,
    start_time: float,
) -> dict:
    """
    使用安全模式添加記憶（跳過實體提取）。

    Args:
        graphiti: Graphiti 實例
        name: 記憶名稱
        content: 記憶內容
        group_id: 分組 ID
        source_description: 來源描述
        source: 來源類型
        start_time: 開始時間（用於計算處理時間）

    Returns:
        dict: 操作結果
    """
    from src.safe_memory_add import safe_add_memory

    result = await safe_add_memory(
        graphiti,
        name=name,
        content=content,
        group_id=group_id,
        source_description=source_description,
    )

    duration = time.time() - start_time

    if result["success"]:
        log_operation_success("add_memory_safe", duration, name=name)
        return {
            "success": True,
            "message": result["message"],
            "uuid": result["uuid"],
            "group_id": group_id,
            "source": source,
            "processing_time": f"{duration:.2f}s",
            "method": "safe_direct_node_creation",
            "note": "使用安全模式，跳過實體提取",
        }
    else:
        log_operation_error("add_memory_safe", Exception(result["error"]), duration=duration)
        return create_error_response(
            CommonErrors.operation_failed("add_memory_safe", result["error"]),
            f"安全記憶添加失敗: {result['error']}",
        )


async def _add_memory_full_mode(
    graphiti: Graphiti,
    name: str,
    episode_body: str,
    group_id: str,
    source_description: str,
    episode_type: EpisodeType,
    episode_uuid: Optional[str],
    source: str,
    start_time: float,
    excluded_entity_types: Optional[List[str]] = None,
) -> dict:
    """
    使用完整模式添加記憶（包含實體提取）。

    長文本會自動切分為多段循序處理，減少每段的 LLM 呼叫次數。

    Args:
        graphiti: Graphiti 實例
        name: 記憶名稱
        episode_body: 記憶內容
        group_id: 分組 ID
        source_description: 來源描述
        episode_type: 記憶類型
        episode_uuid: 可選的 UUID
        source: 來源類型字串
        start_time: 開始時間
        excluded_entity_types: 排除的實體類型列表

    Returns:
        dict: 操作結果
    """
    # 準備 add_episode 的額外參數
    add_episode_kwargs: dict[str, Any] = {}
    if excluded_entity_types:
        add_episode_kwargs["entity_types"] = excluded_entity_types

    # 取得切分配置
    chunk_threshold = 800
    max_chunk_size = 600
    if app_config and hasattr(app_config, "memory_performance"):
        chunk_threshold = app_config.memory_performance.chunk_threshold
        max_chunk_size = app_config.memory_performance.max_chunk_size

    # 智慧切分
    chunk_result = smart_chunk(episode_body, max_chunk_size=max_chunk_size, threshold=chunk_threshold)

    if not chunk_result.was_chunked:
        # 不需切分，直接處理
        await graphiti.add_episode(
            name=name,
            episode_body=episode_body,
            source_description=source_description,
            source=episode_type,
            group_id=group_id,
            reference_time=datetime.now(timezone.utc),
            uuid=episode_uuid,
            **add_episode_kwargs,
        )

        duration = time.time() - start_time
        log_operation_success("add_memory_full", duration, name=name)

        return {
            "success": True,
            "message": f"記憶 '{name}' 已成功添加（完整模式）",
            "uuid": episode_uuid or "auto-generated",
            "group_id": group_id,
            "source": source,
            "processing_time": f"{duration:.2f}s",
            "method": "full_entity_extraction",
            "note": "使用完整模式，包含實體提取和關係建立",
        }

    # 切分後循序處理每段
    total_chunks = len(chunk_result.chunks)
    chunk_times: List[float] = []
    logger.info(f"內容已切分為 {total_chunks} 段，開始循序處理")

    for i, chunk in enumerate(chunk_result.chunks, 1):
        chunk_start = time.time()
        chunk_name = f"{name} (part {i}/{total_chunks})"

        await graphiti.add_episode(
            name=chunk_name,
            episode_body=chunk,
            source_description=source_description,
            source=episode_type,
            group_id=group_id,
            reference_time=datetime.now(timezone.utc),
            **add_episode_kwargs,
        )

        chunk_duration = time.time() - chunk_start
        chunk_times.append(chunk_duration)
        logger.info(f"段落 {i}/{total_chunks} 完成，耗時 {chunk_duration:.1f}s")

    duration = time.time() - start_time
    log_operation_success("add_memory_full_chunked", duration, name=name, chunks=total_chunks)

    return {
        "success": True,
        "message": f"記憶 '{name}' 已成功添加（完整模式，{total_chunks} 段）",
        "uuid": episode_uuid or "auto-generated",
        "group_id": group_id,
        "source": source,
        "processing_time": f"{duration:.2f}s",
        "method": "full_entity_extraction_chunked",
        "chunks": total_chunks,
        "chunk_times": [f"{t:.1f}s" for t in chunk_times],
        "note": f"長文本自動切分為 {total_chunks} 段處理",
    }


@mcp.tool()
async def get_memory_task_status(task_id: str) -> dict:
    """
    查詢背景記憶處理任務的狀態。

    當使用 add_memory_simple(background=True) 時，會返回 task_id，
    可用此工具追蹤處理進度。

    Args:
        task_id: 背景任務 ID

    Returns:
        dict: 任務狀態資訊
            - task_id: 任務 ID
            - status: pending / processing / completed / failed
            - result: 完成時的結果
            - error: 失敗時的錯誤訊息
    """
    task = _memory_tasks.get(task_id)
    if not task:
        return {
            "success": False,
            "error": f"找不到任務 {task_id}",
            "available_tasks": list(_memory_tasks.keys())[-10:],
        }
    return {"success": True, **task.to_dict()}


@mcp.tool()
async def search_memory_nodes(
    query: str,
    max_nodes: int = 10,
    group_ids: Optional[List[str]] = None,
    entity_types: Optional[List[str]] = None,
) -> dict:
    """
    搜索記憶節點（實體）。

    使用混合搜索策略（向量搜索 + 關鍵字搜索）尋找相關的實體節點。

    Args:
        query: 搜尋關鍵字或自然語言查詢
        max_nodes: 返回節點的最大數量（上限 50）
        group_ids: 用於篩選的分組 ID 列表
        entity_types: 用於篩選的實體類型列表
            例如: ["Person", "Organization", "Location"]

    Returns:
        dict: 包含搜索結果的字典
            - nodes: 符合條件的節點列表
            - query: 原始查詢
            - filters: 使用的篩選條件
            - duration: 搜索耗時
    """
    start_time = time.time()
    log_operation_start("search_nodes", query=query[:50])

    try:
        graphiti = await initialize_graphiti()

        # 建立搜索過濾器
        search_filters = SearchFilters(node_labels=entity_types)

        # 配置搜索參數
        search_config = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
        search_config.limit = min(max_nodes, 50)

        # 執行搜索
        search_results = await graphiti.search_(
            query=query,
            config=search_config,
            group_ids=group_ids or [],
            search_filter=search_filters,
        )

        nodes = search_results.nodes if search_results.nodes else []
        duration = time.time() - start_time
        log_operation_success("search_nodes", duration, result_count=len(nodes))

        # 簡化節點資訊
        simplified_nodes = [_simplify_node(node) for node in nodes]

        return {
            "message": f"找到 {len(nodes)} 個相關節點",
            "nodes": simplified_nodes,
            "query": query,
            "filters": {"group_ids": group_ids, "entity_types": entity_types},
            "duration": round(duration, 2),
        }

    except Exception as e:
        duration = time.time() - start_time
        log_operation_error("search_nodes", e, query=query[:50], duration=duration)
        return create_error_response(e, "搜索節點失敗")


def _simplify_node(node: Any) -> dict:
    """
    簡化節點資訊，移除不必要的欄位。

    Args:
        node: 原始節點物件

    Returns:
        dict: 簡化後的節點資訊
    """
    # 過濾掉 embedding 相關欄位
    attrs = getattr(node, "attributes", {}) or {}
    attrs = {k: v for k, v in attrs.items() if "embedding" not in k.lower()}

    return {
        "name": getattr(node, "name", ""),
        "uuid": str(getattr(node, "uuid", "")),
        "created_at": str(getattr(node, "created_at", "")),
        "summary": getattr(node, "summary", "")[:200],
        "group_id": getattr(node, "group_id", ""),
        "labels": getattr(node, "labels", []),
        "attributes": attrs,
    }


@mcp.tool()
async def search_memory_facts(
    query: str,
    max_facts: int = 10,
    group_ids: Optional[List[str]] = None,
    center_node_uuid: Optional[str] = None,
) -> dict:
    """
    搜索記憶事實（實體間的關係）。

    事實代表兩個實體之間的關係，例如「張三 -> 任職於 -> ABC 公司」。

    Args:
        query: 搜尋關鍵字
        max_facts: 返回事實的最大數量（上限 50）
        group_ids: 用於篩選的分組 ID 列表
        center_node_uuid: 可選的中心節點 UUID，以該節點為中心搜索相關事實

    Returns:
        dict: 包含搜索結果的字典
            - facts: 符合條件的事實列表
            - query: 原始查詢
            - filters: 使用的篩選條件
            - duration: 搜索耗時
    """
    start_time = time.time()
    log_operation_start("search_facts", query=query[:50])

    try:
        # 驗證參數
        if max_facts <= 0:
            return create_error_response(
                ValueError("max_facts 必須為正整數"),
                "參數錯誤: max_facts 必須為正整數",
            )

        graphiti = await initialize_graphiti()

        # 執行搜索
        edges = await graphiti.search(
            query=query,
            group_ids=group_ids or [],
            num_results=min(max_facts, 50),
            center_node_uuid=center_node_uuid,
        )

        duration = time.time() - start_time
        log_operation_success("search_facts", duration, result_count=len(edges))

        # 簡化邊資訊
        simplified_edges = [_simplify_edge(edge) for edge in edges]

        return {
            "message": f"找到 {len(edges)} 個相關事實",
            "facts": simplified_edges,
            "query": query,
            "filters": {"group_ids": group_ids, "center_node_uuid": center_node_uuid},
            "duration": round(duration, 2),
        }

    except Exception as e:
        duration = time.time() - start_time
        log_operation_error("search_facts", e, query=query[:50], duration=duration)
        return create_error_response(e, "搜索事實失敗")


def _simplify_edge(edge: Any) -> dict:
    """
    簡化邊（事實）資訊。

    Args:
        edge: 原始邊物件

    Returns:
        dict: 簡化後的邊資訊
    """
    invalid_at = getattr(edge, "invalid_at", None)
    return {
        "uuid": str(getattr(edge, "uuid", "")),
        "name": getattr(edge, "name", ""),
        "fact": getattr(edge, "fact", ""),
        "group_id": getattr(edge, "group_id", ""),
        "source_node_uuid": str(getattr(edge, "source_node_uuid", "")),
        "target_node_uuid": str(getattr(edge, "target_node_uuid", "")),
        "created_at": str(getattr(edge, "created_at", "")),
        "valid_at": str(getattr(edge, "valid_at", "")),
        "invalid_at": str(invalid_at) if invalid_at else None,
        "episodes": getattr(edge, "episodes", []),
    }


@mcp.tool()
async def get_episodes(last_n: int = 10, group_id: str = "") -> dict:
    """
    獲取最近的記憶片段。

    Args:
        last_n: 獲取最近記憶片段的數量（上限 50）
        group_id: 用於篩選的分組 ID

    Returns:
        dict: 包含記憶片段列表的字典
            - episodes: 記憶片段列表
            - duration: 查詢耗時
    """
    start_time = time.time()
    log_operation_start("get_episodes", last_n=last_n)

    try:
        graphiti = await initialize_graphiti()

        # 獲取記憶片段
        episodes = await graphiti.retrieve_episodes(
            reference_time=datetime.now(timezone.utc),
            group_ids=[group_id] if group_id else None,
            last_n=min(last_n, 50),
        )

        duration = time.time() - start_time
        log_operation_success("get_episodes", duration, result_count=len(episodes))

        # 簡化記憶片段資訊
        simplified_episodes = [
            {
                "name": getattr(ep, "name", ""),
                "content": getattr(ep, "content", "")[:500],
                "uuid": str(getattr(ep, "uuid", "")),
                "group_id": getattr(ep, "group_id", ""),
                "created_at": str(getattr(ep, "created_at", "")),
            }
            for ep in episodes
        ]

        return {
            "message": f"找到 {len(episodes)} 個記憶片段",
            "episodes": simplified_episodes,
            "duration": round(duration, 2),
        }

    except Exception as e:
        duration = time.time() - start_time
        log_operation_error("get_episodes", e, last_n=last_n, duration=duration)
        return create_error_response(e, "獲取記憶片段失敗")


@mcp.tool()
async def test_connection() -> dict:
    """
    測試各組件的連接狀態。

    測試項目：
    - Neo4j 資料庫連接
    - Ollama LLM 服務
    - 嵌入器服務

    Returns:
        dict: 包含各組件狀態的字典
    """
    try:
        start_time = time.time()

        graphiti = await initialize_graphiti()

        # 並行測試 LLM 和嵌入器
        llm_status, embedder_status = await asyncio.gather(
            _test_llm(graphiti),
            _test_embedder(graphiti),
        )

        duration = time.time() - start_time

        return {
            "message": "連接測試完成",
            "neo4j": "OK",
            "ollama_llm": llm_status,
            "embedder": embedder_status,
            "duration": round(duration, 2),
        }

    except Exception as e:
        return create_error_response(e, "連接測試失敗")


async def _test_llm(graphiti: Graphiti) -> str:
    """測試 LLM 連接。"""
    try:
        test_response = await graphiti.llm_client.generate_response(
            [{"role": "user", "content": "請回答：1+1=?"}]
        )
        return "OK" if test_response else "回應為空"
    except Exception as e:
        return f"錯誤: {str(e)[:100]}"


async def _test_embedder(graphiti: Graphiti) -> str:
    """測試嵌入器連接。"""
    try:
        test_embedding = await graphiti.embedder.create([{"text": "測試"}])
        return "正常" if test_embedding and len(test_embedding) > 0 else "嵌入生成失敗"
    except Exception as e:
        return f"錯誤: {str(e)[:100]}"


@mcp.tool()
async def clear_graph(group_ids: Optional[List[str]] = None) -> dict:
    """
    清除圖資料庫。

    Args:
        group_ids: 要清除的分組 ID 列表。若為 None 則清除所有資料。

    Returns:
        dict: 操作結果

    Warning:
        此操作不可逆，請謹慎使用。
    """
    try:
        start_time = time.time()
        graphiti = await initialize_graphiti()

        if group_ids:
            await clear_data(graphiti.driver, group_ids=group_ids)
            message = f"已清除分組: {', '.join(group_ids)}"
        else:
            await graphiti.clear()
            message = "圖資料庫已完全清除"

        # 重置快取的實例
        global graphiti_instance
        graphiti_instance = None

        duration = time.time() - start_time

        return {"message": message, "duration": round(duration, 2)}

    except Exception as e:
        return create_error_response(e, "清除圖資料庫失敗")


@mcp.tool()
async def delete_entity_edge(uuid: str) -> dict:
    """
    刪除圖中的實體邊（關係）。

    Args:
        uuid: 要刪除的實體邊 UUID

    Returns:
        dict: 操作結果
    """
    start_time = time.time()
    log_operation_start("delete_entity_edge", uuid=uuid)

    try:
        graphiti = await initialize_graphiti()

        entity_edge = await EntityEdge.get_by_uuid(graphiti.driver, uuid)
        await entity_edge.delete(graphiti.driver)

        duration = time.time() - start_time
        log_operation_success("delete_entity_edge", duration, uuid=uuid)

        return {
            "success": True,
            "message": f"實體邊 {uuid} 已成功刪除",
            "duration": round(duration, 2),
        }

    except Exception as e:
        duration = time.time() - start_time
        log_operation_error("delete_entity_edge", e, uuid=uuid, duration=duration)
        return create_error_response(e, f"刪除實體邊失敗: {uuid}")


@mcp.tool()
async def delete_episode(uuid: str) -> dict:
    """
    刪除記憶片段。

    Args:
        uuid: 要刪除的記憶片段 UUID

    Returns:
        dict: 操作結果
    """
    start_time = time.time()
    log_operation_start("delete_episode", uuid=uuid)

    try:
        graphiti = await initialize_graphiti()

        episodic_node = await EpisodicNode.get_by_uuid(graphiti.driver, uuid)
        await episodic_node.delete(graphiti.driver)

        duration = time.time() - start_time
        log_operation_success("delete_episode", duration, uuid=uuid)

        return {
            "success": True,
            "message": f"記憶片段 {uuid} 已成功刪除",
            "duration": round(duration, 2),
        }

    except Exception as e:
        duration = time.time() - start_time
        log_operation_error("delete_episode", e, uuid=uuid, duration=duration)
        return create_error_response(e, f"刪除記憶片段失敗: {uuid}")


@mcp.tool()
async def get_entity_edge(uuid: str) -> dict:
    """
    獲取特定實體邊的詳細資訊。

    Args:
        uuid: 實體邊的 UUID

    Returns:
        dict: 包含實體邊詳細資訊的字典
    """
    start_time = time.time()
    log_operation_start("get_entity_edge", uuid=uuid)

    try:
        graphiti = await initialize_graphiti()

        entity_edge = await EntityEdge.get_by_uuid(graphiti.driver, uuid)

        duration = time.time() - start_time
        log_operation_success("get_entity_edge", duration, uuid=uuid)

        invalid_at = getattr(entity_edge, "invalid_at", None)

        return {
            "success": True,
            "edge": {
                "uuid": str(entity_edge.uuid),
                "source_node_uuid": str(entity_edge.source_node_uuid),
                "target_node_uuid": str(entity_edge.target_node_uuid),
                "fact": getattr(entity_edge, "fact", ""),
                "name": getattr(entity_edge, "name", ""),
                "group_id": getattr(entity_edge, "group_id", ""),
                "created_at": str(getattr(entity_edge, "created_at", "")),
                "valid_at": str(getattr(entity_edge, "valid_at", "")),
                "invalid_at": str(invalid_at) if invalid_at else None,
                "episodes": getattr(entity_edge, "episodes", []),
            },
            "duration": round(duration, 2),
        }

    except Exception as e:
        duration = time.time() - start_time
        log_operation_error("get_entity_edge", e, uuid=uuid, duration=duration)
        return create_error_response(e, f"獲取實體邊失敗: {uuid}")


@mcp.tool()
async def get_status() -> dict:
    """
    獲取服務狀態和資料庫連接狀況。

    Returns:
        dict: 包含各組件狀態的詳細資訊
    """
    try:
        start_time = time.time()

        status_info = {
            "service": "graphiti-ollama-mcp",
            "status": "checking",
            "components": {},
        }

        # 並行測試所有組件
        db_status, llm_status, emb_status = await asyncio.gather(
            _check_database_status(),
            _check_llm_status(),
            _check_embedder_status(),
        )
        status_info["components"]["database"] = db_status
        status_info["components"]["llm"] = llm_status
        status_info["components"]["embedder"] = emb_status

        # 判斷整體狀態
        all_connected = all(
            comp.get("status") in ["connected", "not_configured"]
            for comp in status_info["components"].values()
        )
        status_info["status"] = "healthy" if all_connected else "degraded"
        status_info["duration"] = round(time.time() - start_time, 2)

        return status_info

    except Exception as e:
        return {
            "service": "graphiti-ollama-mcp",
            "status": "error",
            "error": str(e),
            "message": "服務狀態檢查失敗",
        }


async def _check_database_status() -> dict:
    """檢查資料庫連接狀態。"""
    try:
        graphiti = await initialize_graphiti()

        async with graphiti.driver.session() as session:
            result = await session.run("MATCH (n) RETURN count(n) as count")
            records = [record async for record in result]
            node_count = records[0]["count"] if records else 0

        return {"status": "connected", "type": "Neo4j", "node_count": node_count}
    except Exception as e:
        return {"status": "error", "error": str(e)[:100]}


async def _check_llm_status() -> dict:
    """檢查 LLM 連接狀態。"""
    try:
        graphiti = await initialize_graphiti()

        if graphiti.llm_client:
            test_response = await graphiti.llm_client.generate_response(
                [{"role": "user", "content": "回答: 1"}]
            )
            return {
                "status": "connected" if test_response else "no_response",
                "model": app_config.ollama.model,
            }
        return {"status": "not_configured"}
    except Exception as e:
        return {"status": "error", "error": str(e)[:100]}


async def _check_embedder_status() -> dict:
    """檢查嵌入器連接狀態。"""
    try:
        graphiti = await initialize_graphiti()

        test_embedding = await graphiti.embedder.create([{"text": "test"}])
        return {
            "status": "connected" if test_embedding else "no_response",
            "model": app_config.embedder.model,
            "dimensions": app_config.embedder.dimensions,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)[:100]}


# ============================================================================
# 伺服器配置與啟動
# ============================================================================


def configure_uvicorn_logging() -> None:
    """配置 uvicorn 日誌格式。"""
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    for logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access"]:
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.handlers.clear()
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
        uvicorn_logger.addHandler(handler)
        uvicorn_logger.propagate = False


# 嘗試添加健康檢查端點與 Web 管理介面
try:
    from starlette.responses import JSONResponse

    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(request) -> JSONResponse:
        """輕量 liveness 檢查 — 僅確認程序存活。"""
        return JSONResponse(
            {"status": "healthy", "service": "graphiti-ollama-mcp", "version": "1.0.0"}
        )

    @mcp.custom_route("/health/ready", methods=["GET"])
    async def health_ready(request) -> JSONResponse:
        """深度 readiness 檢查 — 實際檢查 Neo4j 連線狀態。"""
        try:
            graphiti = await initialize_graphiti()
            async with graphiti.driver.session() as session:
                result = await session.run("RETURN 1 AS ok")
                _ = [r async for r in result]
            return JSONResponse(
                {"status": "ready", "neo4j": "connected", "service": "graphiti-ollama-mcp"}
            )
        except Exception as e:
            return JSONResponse(
                {"status": "not_ready", "error": str(e)[:200], "service": "graphiti-ollama-mcp"},
                status_code=503,
            )

    # 注入 Web 管理介面路由（含 CORS 配置）
    from src.web_api import create_web_routes

    _web_routes = create_web_routes(
        get_graphiti_fn=initialize_graphiti,
        cors_origins=app_config.server.cors_origins if app_config else ["*"],
    )
    mcp._custom_starlette_routes.extend(_web_routes)

except ImportError:
    pass  # Starlette 不可用時跳過健康檢查端點與 Web 介面


def main() -> None:
    """
    主程序入口點。

    解析命令列參數並啟動 MCP 伺服器。

    支援的傳輸模式：
        - stdio: 標準輸入輸出（預設）
        - sse: Server-Sent Events
        - http: HTTP streamable（推薦）
    """
    global app_config, logger

    parser = argparse.ArgumentParser(description="Graphiti Ollama MCP Server")
    parser.add_argument(
        "--transport",
        default="stdio",
        choices=["stdio", "sse", "http"],
        help="傳輸模式: stdio, sse, http",
    )
    parser.add_argument("--config", help="配置檔案路徑")
    parser.add_argument("--host", default="0.0.0.0", help="服務器主機地址")
    parser.add_argument("--port", type=int, default=8000, help="服務器端口")
    parser.add_argument("--group-id", help="圖形命名空間 ID")

    args = parser.parse_args()

    try:
        # 載入配置
        app_config = load_config(args.config)

        # 覆蓋命令列指定的參數
        if args.host != "0.0.0.0":
            app_config.server.host = args.host
        if args.port != 8000:
            app_config.server.port = args.port

        # 設置日誌
        logger = setup_logging(app_config.logging)
        log_system_info()

        # 記錄配置摘要
        config_dict = {
            "ollama_model": app_config.ollama.model,
            "neo4j_uri": app_config.neo4j.uri,
            "embedder_model": app_config.embedder.model,
            "log_level": app_config.logging.level,
            "transport": args.transport,
        }
        log_config_summary(config_dict)

        main_logger = logging.getLogger("main")
        main_logger.info("Graphiti + Ollama MCP 服務器初始化完成")

        # 設置 MCP 伺服器
        mcp.settings.host = app_config.server.host
        mcp.settings.port = app_config.server.port

        # 根據傳輸方式啟動
        _run_server(args.transport, main_logger)

    except KeyboardInterrupt:
        main_logger = logging.getLogger("main")
        main_logger.info("正在關閉服務器...")
        if graphiti_instance:
            try:
                asyncio.run(graphiti_instance.driver.close())
                main_logger.info("Neo4j 連線已關閉")
            except Exception:
                pass
        main_logger.info("服務器已停止")
        sys.exit(0)
    except Exception as e:
        logging.getLogger("main").error(f"服務器啟動失敗: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


async def _startup_warmup() -> None:
    """
    啟動時預熱連線：驗證 Neo4j 和 Ollama 是否可達。

    此函數不會阻塞啟動流程。連線失敗時僅記錄 WARNING，
    允許服務先起來，等外部服務恢復後自動重連。
    """
    warmup_logger = logging.getLogger("startup")
    warmup_logger.info("開始啟動連線預熱...")

    try:
        graphiti = await initialize_graphiti()
        warmup_logger.info("✓ Graphiti 實例初始化成功")

        # 驗證 Neo4j 連線
        try:
            async with graphiti.driver.session() as session:
                result = await session.run("RETURN 1 AS ok")
                _ = [r async for r in result]
            warmup_logger.info("✓ Neo4j 連線成功")
        except Exception as e:
            warmup_logger.warning(f"⚠ Neo4j 連線失敗: {e}（將在首次工具呼叫時重試）")

        # 驗證 Ollama LLM
        if graphiti.llm_client:
            warmup_logger.info(f"✓ Ollama LLM 就緒（模型: {app_config.ollama.model}）")
        else:
            warmup_logger.warning("⚠ Ollama LLM 客戶端未初始化")

        # 驗證嵌入器
        warmup_logger.info(f"✓ 嵌入器就緒（模型: {app_config.embedder.model}）")

    except Exception as e:
        warmup_logger.warning(f"⚠ 啟動預熱失敗: {e}（將在首次工具呼叫時重試）")


async def _run_http_with_warmup() -> None:
    """HTTP 模式啟動：先觸發預熱，再啟動 HTTP 伺服器。"""
    # 非同步預熱（不阻塞）
    asyncio.create_task(_startup_warmup())
    await mcp.run_streamable_http_async()


def _run_server(transport: str, main_logger: logging.Logger) -> None:
    """
    根據指定的傳輸模式啟動伺服器。

    Args:
        transport: 傳輸模式
        main_logger: 日誌記錄器
    """
    if transport == "stdio":
        main_logger.info("使用 stdio 傳輸模式")
        asyncio.run(mcp.run_stdio_async())

    elif transport == "sse":
        main_logger.info("使用 SSE 傳輸模式")
        main_logger.info(
            f"服務器地址: http://{app_config.server.host}:{app_config.server.port}/sse"
        )
        asyncio.run(mcp.run_sse_async())

    elif transport == "http":
        display_host = (
            "localhost" if app_config.server.host == "0.0.0.0" else app_config.server.host
        )

        main_logger.info("=" * 60)
        main_logger.info("使用 HTTP Streamable 傳輸模式（推薦）")
        main_logger.info(f"基礎 URL: http://{display_host}:{app_config.server.port}/")
        main_logger.info(f"MCP 端點: http://{display_host}:{app_config.server.port}/mcp/")
        main_logger.info(f"健康檢查: http://{display_host}:{app_config.server.port}/health")
        main_logger.info(f"Web 管理: http://{display_host}:{app_config.server.port}/")
        main_logger.info("=" * 60)

        configure_uvicorn_logging()
        asyncio.run(_run_http_with_warmup())


if __name__ == "__main__":
    main()
