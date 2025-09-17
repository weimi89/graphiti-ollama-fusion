#!/usr/bin/env python3
"""
Graphiti Ollama MCP Server - 優化版本
解決索引錯誤和提升穩定性
"""

import argparse
import asyncio
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
from graphiti_core.nodes import EpisodicNode
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

# 參數模型
class AddMemoryArgs(BaseModel):
    name: str = Field(description="記憶片段的名稱")
    episode_body: str = Field(description="記憶片段的內容")
    group_id: str = Field(default="default", description="記憶分組 ID")
    source_description: str = Field(default="MCP Server", description="來源描述")

class SearchNodesArgs(BaseModel):
    query: str = Field(description="搜尋關鍵字")
    max_nodes: int = Field(default=10, description="返回節點的最大數量")
    group_ids: Optional[List[str]] = Field(default=None, description="用於篩選的分組 ID")

class SearchFactsArgs(BaseModel):
    query: str = Field(description="搜尋關鍵字")
    max_facts: int = Field(default=10, description="返回事實的最大數量")
    group_ids: Optional[List[str]] = Field(default=None, description="用於篩選的分組 ID")

class GetEpisodesArgs(BaseModel):
    last_n: int = Field(default=10, description="獲取最近記憶片段的數量")
    group_id: str = Field(default="", description="用於篩選的分組 ID")

async def initialize_graphiti():
    """初始化 Graphiti 實例（使用快取機制）"""
    global graphiti_instance

    if graphiti_instance is not None:
        return graphiti_instance

    start_time = time.time()
    log_operation_start("initialize_graphiti")

    try:
        # 創建 Ollama LLM 客戶端
        llm_client = OptimizedOllamaClient(
            base_url=app_config.ollama.base_url,
            model=app_config.ollama.model,
            temperature=app_config.ollama.temperature,
            timeout=30.0  # 增加超時時間
        )

        # 創建 Ollama 嵌入器
        embedder = OllamaEmbedder(
            model_name=app_config.embedder.model,
            base_url=app_config.embedder.base_url,
            dimensions=app_config.embedder.dimensions,
            timeout=30.0  # 增加超時時間
        )

        # 創建 Graphiti 實例
        graphiti_instance = Graphiti(
            uri=app_config.neo4j.uri,
            user=app_config.neo4j.user,
            password=app_config.neo4j.password,
            llm_client=llm_client,
            embedder=embedder,
            search_config=NODE_HYBRID_SEARCH_RRF  # 使用 RRF 搜索配置
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
async def add_memory_simple(args: AddMemoryArgs) -> dict:
    """添加記憶到 Graphiti（優化版本）"""
    start_time = time.time()
    log_operation_start("add_memory", name=args.name, group_id=args.group_id)

    try:
        # 輸入驗證和清理
        clean_name = args.name.strip()[:100]  # 限制標題長度
        clean_body = args.episode_body.strip()[:2000]  # 限制內容長度
        clean_group_id = args.group_id.strip() if args.group_id else "default"

        if not clean_name or not clean_body:
            raise GraphitiMCPError("記憶名稱和內容不能為空")

        graphiti = await initialize_graphiti()

        # 添加重試機制
        max_retries = 3
        last_exception = None

        for attempt in range(max_retries):
            try:
                # 生成唯一的源描述以避免衝突
                unique_source = f"{args.source_description}_{uuid.uuid4().hex[:8]}"

                result = await graphiti.add_episode(
                    name=clean_name,
                    episode_body=clean_body,
                    source_description=unique_source,
                    group_id=clean_group_id,
                    reference_time=datetime.now(timezone.utc)
                )

                # 如果成功，跳出重試循環
                break

            except (IndexError, KeyError) as e:
                last_exception = e
                if attempt < max_retries - 1:
                    logger.warning(f"添加記憶失敗，嘗試重試 {attempt + 1}/{max_retries}: {e}")
                    await asyncio.sleep(1.0 * (attempt + 1))  # 指數退避
                    continue
                else:
                    raise e
            except Exception as e:
                # 其他異常不重試
                raise e

        duration = time.time() - start_time

        # 簡化的成功記錄
        log_operation_success(
            "add_memory",
            duration,
            episode_id=getattr(result, 'episode_id', None)
        )

        # 記錄性能指標
        performance_logger.log_memory_add_performance(
            len(clean_body), duration, True
        )

        return {
            "success": True,
            "message": f"記憶 '{clean_name}' 新增成功",
            "episode_id": getattr(result, 'episode_id', None),
            "duration": round(duration, 2),
            "content_length": len(clean_body)
        }

    except Exception as e:
        duration = time.time() - start_time
        log_operation_error("add_memory", e, name=args.name, duration=duration)

        # 記錄失敗的性能指標
        performance_logger.log_memory_add_performance(
            len(args.episode_body), duration, False
        )

        return create_error_response(e, "新增記憶失敗")

@mcp.tool()
async def search_memory_nodes(args: SearchNodesArgs) -> dict:
    """搜索記憶節點（優化版本）"""
    start_time = time.time()
    log_operation_start("search_nodes", query=args.query[:50])

    try:
        graphiti = await initialize_graphiti()

        # 創建搜索過濾器
        search_filters = SearchFilters(
            group_ids=args.group_ids or []
        )

        # 執行搜索
        nodes = await graphiti.search_nodes(
            query=args.query,
            limit=min(args.max_nodes, 50),  # 限制最大結果數
            search_config=NODE_HYBRID_SEARCH_RRF,
            filters=search_filters
        )

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
        log_operation_error("search_nodes", e, query=args.query[:50], duration=duration)
        return create_error_response(e, "搜索節點失敗")

@mcp.tool()
async def search_memory_facts(args: SearchFactsArgs) -> dict:
    """搜索記憶事實（優化版本）"""
    start_time = time.time()
    log_operation_start("search_facts", query=args.query[:50])

    try:
        graphiti = await initialize_graphiti()

        # 創建搜索過濾器
        search_filters = SearchFilters(
            group_ids=args.group_ids or []
        )

        # 執行搜索
        edges = await graphiti.search_edges(
            query=args.query,
            limit=min(args.max_facts, 50),  # 限制最大結果數
            filters=search_filters
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
        log_operation_error("search_facts", e, query=args.query[:50], duration=duration)
        return create_error_response(e, "搜索事實失敗")

@mcp.tool()
async def get_episodes(args: GetEpisodesArgs) -> dict:
    """獲取最近的記憶片段（優化版本）"""
    start_time = time.time()
    log_operation_start("get_episodes", last_n=args.last_n)

    try:
        graphiti = await initialize_graphiti()

        # 獲取最近的記憶片段
        episodes = await graphiti.get_episodes(
            group_id=args.group_id if args.group_id else None,
            last_n=min(args.last_n, 50)  # 限制最大數量
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
        log_operation_error("get_episodes", e, last_n=args.last_n, duration=duration)
        return create_error_response(e, "獲取記憶片段失敗")

@mcp.tool()
async def test_connection() -> dict:
    """測試連接狀態（優化版本）"""
    try:
        start_time = time.time()

        # 測試 Neo4j 連接
        graphiti = await initialize_graphiti()

        # 測試 Ollama LLM
        llm_status = "OK"
        try:
            test_response = await graphiti.llm_client.generate_response("測試")
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
    """清除圖資料庫（優化版本）"""
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

    parser = argparse.ArgumentParser(description="Graphiti Ollama MCP Server - 優化版本")
    parser.add_argument("--transport", default="stdio", choices=["stdio", "sse"])
    parser.add_argument("--config", help="配置檔案路徑")
    parser.add_argument("--host", default="localhost", help="SSE 模式主機地址")
    parser.add_argument("--port", type=int, default=8000, help="SSE 模式端口")

    args = parser.parse_args()

    try:
        # 載入配置
        app_config = load_config(args.config)

        # 設置日誌
        logger = setup_logging(app_config.logging)

        # 記錄系統信息
        log_system_info()
        log_config_summary(app_config)

        logger.info("✅ Graphiti + Ollama MCP 服務器初始化完成（優化版本）")

        # 根據傳輸方式運行
        if args.transport == "stdio":
            mcp.run()
        elif args.transport == "sse":
            mcp.run_sse(host=args.host, port=args.port)

    except KeyboardInterrupt:
        logger.info("👋 服務器已停止")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ 服務器啟動失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()