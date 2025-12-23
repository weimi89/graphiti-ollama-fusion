#!/usr/bin/env python3
"""
Graphiti Ollama MCP Server
解決索引錯誤和提升穩定性
"""

import argparse
import asyncio
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

# 導入新的配置和錯誤處理系統
from src.config import GraphitiConfig, load_config
from src.exceptions import (
    GraphitiMCPError, OllamaError, Neo4jError, EmbeddingError,
    handle_exception, create_error_response, CommonErrors
)
from src.logging_setup import (
    setup_logging, log_system_info, log_config_summary,
    log_operation_start, log_operation_success, log_operation_error,
    performance_logger
)

# 使用我們的自定義 Ollama 組件
from src.ollama_graphiti_client import OptimizedOllamaClient
from src.ollama_embedder import OllamaEmbedder
from graphiti_core import Graphiti
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.edges import EntityEdge
from graphiti_core.nodes import EpisodicNode, EpisodeType
from graphiti_core.search.search_config_recipes import (
    NODE_HYBRID_SEARCH_NODE_DISTANCE,
    NODE_HYBRID_SEARCH_RRF,
)
from graphiti_core.search.search_filters import SearchFilters

load_dotenv()

# 全局配置和日誌
app_config: GraphitiConfig = None
logger = None
graphiti_instance = None  # 快取 Graphiti 實例

# 隊列系統 (從官方版本移植)
episode_queues: dict[str, asyncio.Queue] = {}
queue_workers: dict[str, bool] = {}

# MCP 工具不再需要 Pydantic 模型參數，已改為標準函數參數

async def process_episode_queue(group_id: str):
    """處理特定 group_id 的記憶片段隊列"""
    global queue_workers

    logging.info(f'Starting episode queue worker for group_id: {group_id}')
    queue_workers[group_id] = True

    try:
        while True:
            # 從隊列獲取下一個處理函數
            process_func = await episode_queues[group_id].get()

            try:
                # 處理記憶片段
                await process_func()
            except Exception as e:
                logging.error(f'Error processing queued episode for group_id {group_id}: {str(e)}')
            finally:
                # 標記任務完成
                episode_queues[group_id].task_done()
    except asyncio.CancelledError:
        logging.info(f'Episode queue worker for group_id {group_id} was cancelled')
    except Exception as e:
        logging.error(f'Unexpected error in queue worker for group_id {group_id}: {str(e)}')
    finally:
        queue_workers[group_id] = False
        logging.info(f'Stopped episode queue worker for group_id: {group_id}')


async def initialize_graphiti():
    """初始化 Graphiti 實例（使用快取機制）"""
    global graphiti_instance

    if graphiti_instance is not None:
        return graphiti_instance

    start_time = time.time()
    log_operation_start("initialize_graphiti")

    try:
        # 嘗試創建 Ollama LLM 客戶端，失敗時設為 None
        llm_client = None
        try:
            llm_config = LLMConfig(
                base_url=app_config.ollama.base_url,
                model=app_config.ollama.model,
                temperature=app_config.ollama.temperature
            )
            llm_client = OptimizedOllamaClient(config=llm_config)
            print("✅ LLM 客戶端初始化成功")
        except Exception as e:
            print(f"⚠️ LLM 客戶端初始化失敗，使用 None: {e}")
            llm_client = None

        # 創建 Ollama 嵌入器
        embedder = OllamaEmbedder(
            model=app_config.embedder.model,
            base_url=app_config.embedder.base_url,
            dimensions=app_config.embedder.dimensions
        )

        # 創建 Graphiti 實例
        graphiti_instance = Graphiti(
            uri=app_config.neo4j.uri,
            user=app_config.neo4j.user,
            password=app_config.neo4j.password,
            llm_client=llm_client,
            embedder=embedder,
            max_coroutines=3  # 限制併發數量避免 IndexError
        )

        duration = time.time() - start_time
        log_operation_success("initialize_graphiti", duration)

        return graphiti_instance

    except Exception as e:
        duration = time.time() - start_time
        log_operation_error("initialize_graphiti", e, duration=duration)

        # 轉換為結構化異常
        if isinstance(e, GraphitiMCPError):
            raise e
        else:
            raise handle_exception(e, "Graphiti 初始化失敗")

# 創建 FastMCP 應用
mcp = FastMCP("graphiti-ollama-memory")

@mcp.tool()
async def add_memory_simple(
    name: str,
    episode_body: str,
    group_id: str = "default",
    source_description: str = "MCP Server"
) -> dict:
    """使用安全方法添加記憶 - 完全避開 IndexError 問題
    
    Args:
        name: 記憶片段的名稱
        episode_body: 記憶片段的內容
        group_id: 記憶分組 ID (預設: default)
        source_description: 來源描述 (預設: MCP Server)
    """
    start_time = time.time()
    log_operation_start("add_memory_safe", name=name[:50])

    try:
        from src.safe_memory_add import safe_add_memory

        graphiti = await initialize_graphiti()

        # 使用安全方法添加記憶 - 直接創建 EpisodicNode
        result = await safe_add_memory(
            graphiti,
            name=name,
            content=episode_body,
            group_id=group_id,
            source_description=source_description
        )

        duration = time.time() - start_time

        if result["success"]:
            log_operation_success("add_memory_safe", duration, name=name)
            return {
                "success": True,
                "message": result["message"],
                "uuid": result["uuid"],
                "group_id": group_id,
                "processing_time": f"{duration:.2f}s",
                "method": "safe_direct_node_creation",
                "note": "使用安全方法，完全避開實體提取以防止 IndexError"
            }
        else:
            log_operation_error("add_memory_safe", Exception(result["error"]), duration=duration)
            return create_error_response(
                CommonErrors.operation_failed("add_memory_safe", result["error"]),
                f"安全記憶添加失敗: {result['error']}")

    except Exception as e:
        duration = time.time() - start_time
        log_operation_error("add_memory_safe", e, duration=duration)
        return create_error_response(
            CommonErrors.operation_failed("add_memory_safe", str(e)),
            f"記憶添加過程中發生錯誤: {str(e)}")

@mcp.tool()
async def search_memory_nodes(
    query: str,
    max_nodes: int = 10,
    group_ids: Optional[List[str]] = None
) -> dict:
    """搜索記憶節點
    
    Args:
        query: 搜尋關鍵字
        max_nodes: 返回節點的最大數量 (預設: 10)
        group_ids: 用於篩選的分組 ID (預設: None)
    """
    start_time = time.time()
    log_operation_start("search_nodes", query=query[:50])

    try:
        graphiti = await initialize_graphiti()

        # 創建搜索過濾器
        search_filters = SearchFilters(
            group_ids=group_ids or []
        )

        # 配置搜索
        search_config = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
        search_config.limit = min(max_nodes, 50)

        # 執行搜索 (使用私有 _search 方法)
        search_results = await graphiti._search(
            query=query,
            config=search_config,
            group_ids=group_ids or [],
            search_filter=search_filters
        )

        # 從搜索結果中獲取節點
        nodes = search_results.nodes if search_results.nodes else []

        duration = time.time() - start_time
        log_operation_success("search_nodes", duration, result_count=len(nodes))

        # 簡化節點資訊
        simplified_nodes = []
        for node in nodes:
            simplified_nodes.append({
                "name": getattr(node, 'name', ''),
                "uuid": str(getattr(node, 'uuid', '')),
                "created_at": str(getattr(node, 'created_at', '')),
                "summary": getattr(node, 'summary', '')[:200],  # 限制摘要長度
                "group_id": getattr(node, 'group_id', ''),
                "labels": getattr(node, 'labels', [])
            })

        return {
            "message": f"找到 {len(nodes)} 個相關節點",
            "nodes": simplified_nodes,
            "duration": round(duration, 2)
        }

    except Exception as e:
        duration = time.time() - start_time
        log_operation_error("search_nodes", e, query=query[:50], duration=duration)
        return create_error_response(e, "搜索節點失敗")

@mcp.tool()
async def search_memory_facts(
    query: str,
    max_facts: int = 10,
    group_ids: Optional[List[str]] = None
) -> dict:
    """搜索記憶事實
    
    Args:
        query: 搜尋關鍵字
        max_facts: 返回事實的最大數量 (預設: 10)
        group_ids: 用於篩選的分組 ID (預設: None)
    """
    start_time = time.time()
    log_operation_start("search_facts", query=query[:50])

    try:
        graphiti = await initialize_graphiti()

        # 創建搜索過濾器
        search_filters = SearchFilters(
            group_ids=group_ids or []
        )

        # 執行搜索
        edges = await graphiti.search(
            query=query,
            num_results=min(max_facts, 50),  # 限制最大結果數
            search_filter=search_filters
        )

        duration = time.time() - start_time
        log_operation_success("search_facts", duration, result_count=len(edges))

        # 簡化邊資訊
        simplified_edges = []
        for edge in edges:
            simplified_edges.append({
                "relation_type": getattr(edge, 'relation_type', ''),
                "uuid": str(getattr(edge, 'uuid', '')),
                "created_at": str(getattr(edge, 'created_at', '')),
                "fact": getattr(edge, 'fact', '')[:200],  # 限制事實長度
                "group_id": getattr(edge, 'group_id', ''),
                "source_node_uuid": str(getattr(edge, 'source_node_uuid', '')),
                "target_node_uuid": str(getattr(edge, 'target_node_uuid', ''))
            })

        return {
            "message": f"找到 {len(edges)} 個相關事實",
            "facts": simplified_edges,
            "duration": round(duration, 2)
        }

    except Exception as e:
        duration = time.time() - start_time
        log_operation_error("search_facts", e, query=query[:50], duration=duration)
        return create_error_response(e, "搜索事實失敗")

@mcp.tool()
async def get_episodes(
    last_n: int = 10,
    group_id: str = ""
) -> dict:
    """獲取最近的記憶片段
    
    Args:
        last_n: 獲取最近記憶片段的數量 (預設: 10)
        group_id: 用於篩選的分組 ID (預設: "")
    """
    start_time = time.time()
    log_operation_start("get_episodes", last_n=last_n)

    try:
        graphiti = await initialize_graphiti()

        # 獲取最近的記憶片段
        episodes = await graphiti.retrieve_episodes(
            reference_time=datetime.now(timezone.utc),
            group_ids=[group_id] if group_id else None,
            last_n=min(last_n, 50)  # 限制最大數量
        )

        duration = time.time() - start_time
        log_operation_success("get_episodes", duration, result_count=len(episodes))

        # 簡化記憶片段資訊
        simplified_episodes = []
        for episode in episodes:
            simplified_episodes.append({
                "name": getattr(episode, 'name', ''),
                "content": getattr(episode, 'content', '')[:500],  # 限制內容長度
                "uuid": str(getattr(episode, 'uuid', '')),
                "group_id": getattr(episode, 'group_id', ''),
                "created_at": str(getattr(episode, 'created_at', ''))
            })

        return {
            "message": f"找到 {len(episodes)} 個記憶片段",
            "episodes": simplified_episodes,
            "duration": round(duration, 2)
        }

    except Exception as e:
        duration = time.time() - start_time
        log_operation_error("get_episodes", e, last_n=last_n, duration=duration)
        return create_error_response(e, "獲取記憶片段失敗")

@mcp.tool()
async def test_connection() -> dict:
    """測試連接狀態"""
    try:
        start_time = time.time()

        # 測試 Neo4j 連接
        graphiti = await initialize_graphiti()

        # 測試 Ollama LLM
        llm_status = "OK"
        try:
            # 使用正確的訊息列表格式
            test_response = await graphiti.llm_client.generate_response([
                {"role": "user", "content": "請回答：1+1=?"}
            ])
            if not test_response:
                llm_status = "回應為空"
        except Exception as e:
            llm_status = f"錯誤: {str(e)[:100]}"

        # 測試嵌入器
        embedder_status = "正常"
        try:
            test_embedding = await graphiti.embedder.create([{"text": "測試"}])
            if not test_embedding or len(test_embedding) == 0:
                embedder_status = "嵌入生成失敗"
        except Exception as e:
            embedder_status = f"錯誤: {str(e)[:100]}"

        duration = time.time() - start_time

        return {
            "message": "連接測試完成",
            "neo4j": "OK",
            "ollama_llm": llm_status,
            "embedder": embedder_status,
            "duration": round(duration, 2)
        }

    except Exception as e:
        return create_error_response(e, "連接測試失敗")

@mcp.tool()
async def clear_graph() -> dict:
    """清除圖資料庫"""
    try:
        start_time = time.time()
        graphiti = await initialize_graphiti()

        # 清除圖資料庫
        await graphiti.clear()

        # 重置快取的實例
        global graphiti_instance
        graphiti_instance = None

        duration = time.time() - start_time

        return {
            "message": "圖資料庫已清除",
            "duration": round(duration, 2)
        }

    except Exception as e:
        return create_error_response(e, "清除圖資料庫失敗")

def main():
    """主程序入口點"""
    global app_config, logger

    parser = argparse.ArgumentParser(description="Graphiti Ollama MCP Server")
    parser.add_argument("--transport", default="stdio", choices=["stdio", "sse"])
    parser.add_argument("--config", help="配置檔案路徑")
    parser.add_argument("--host", default="localhost", help="SSE 模式主機地址")
    parser.add_argument("--port", type=int, default=8000, help="SSE 模式端口")
    parser.add_argument("--group-id", help="圖形命名空間 ID，用於組織相關數據")

    args = parser.parse_args()

    try:
        # 載入配置
        app_config = load_config(args.config)

        # 設置日誌
        logger = setup_logging(app_config.logging)

        # 記錄系統信息
        log_system_info()

        # 轉換配置為字典格式
        config_dict = {
            "ollama_model": app_config.ollama.model,
            "neo4j_uri": app_config.neo4j.uri,
            "embedder_model": app_config.embedder.model,
            "log_level": app_config.logging.level
        }
        log_config_summary(config_dict)

        import logging
        main_logger = logging.getLogger("main")
        main_logger.info("✅ Graphiti + Ollama MCP 服務器初始化完成")

        # 根據傳輸方式運行
        if args.transport == "stdio":
            import asyncio
            asyncio.run(mcp.run_stdio_async())
        elif args.transport == "sse":
            import asyncio
            asyncio.run(mcp.run_sse_async())

    except KeyboardInterrupt:
        import logging
        main_logger = logging.getLogger("main")
        main_logger.info("👋 服務器已停止")
        sys.exit(0)
    except Exception as e:
        import logging
        error_logger = logging.getLogger("main")
        error_logger.error(f"❌ 服務器啟動失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()