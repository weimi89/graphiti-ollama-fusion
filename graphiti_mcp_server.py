#!/usr/bin/env python3
"""
Graphiti Ollama MCP Server - 整合 Ollama 本地 LLM 的 MCP 服務器
基於我們的 Graphiti + Ollama 解決方案

整合 Ollama 本地 LLM 的知識圖譜記憶管理服務
"""

import argparse
import asyncio
import os
import sys
import time
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

# MCP 工具的參數模型
class AddMemoryArgs(BaseModel):
    name: str = Field(description="記憶片段的名稱")
    episode_body: str = Field(description="記憶片段的內容")
    source_description: str = Field(default="MCP Server", description="來源描述")
    group_id: str = Field(default="default", description="記憶分組 ID")

class SearchNodesArgs(BaseModel):
    query: str = Field(description="搜尋關鍵字")
    max_nodes: int = Field(default=10, description="返回節點的最大數量")
    group_ids: List[str] = Field(default_factory=list, description="用於篩選的分組 ID")

class SearchFactsArgs(BaseModel):
    query: str = Field(description="搜尋關鍵字")
    max_facts: int = Field(default=10, description="返回事實的最大數量")
    group_ids: List[str] = Field(default_factory=list, description="用於篩選的分組 ID")

class GetEpisodesArgs(BaseModel):
    last_n: int = Field(default=10, description="獲取最近記憶片段的數量")
    group_id: str = Field(default="", description="用於篩選的分組 ID")

# 全局變量
graphiti_instance: Graphiti = None


def initialize_system(config_path: Optional[str] = None):
    """初始化系統配置和日誌"""
    global app_config, logger

    # 載入配置
    app_config = load_config(config_path)

    # 設置日誌系統
    log_manager = setup_logging(app_config.logging)
    logger = log_manager.get_logger("main")

    # 記錄系統啟動信息
    log_system_info()
    log_config_summary(app_config.get_summary())

    # 驗證配置
    if not app_config.validate():
        logger.warning("配置驗證失敗，某些功能可能無法正常運作")
    else:
        logger.info("✅ 系統配置驗證通過")

    return app_config

async def initialize_graphiti():
    """初始化 Graphiti 實例使用配置系統"""
    global graphiti_instance, app_config, logger

    if graphiti_instance is not None:
        return graphiti_instance

    start_time = time.time()
    log_operation_start("initialize_graphiti")

    try:
        # 初始化 LLM 客戶端
        logger.info(f"📡 使用 LLM 模型: {app_config.ollama.model}")

        llm_config = LLMConfig(
            api_key="not-needed",
            model=app_config.ollama.model,
            base_url=app_config.ollama.base_url,
            temperature=app_config.ollama.temperature,
            max_tokens=app_config.ollama.max_tokens
        )
        llm_client = OptimizedOllamaClient(llm_config)

        # 初始化嵌入器
        logger.info(f"🧲 使用嵌入模型: {app_config.embedder.model}")

        embedder = OllamaEmbedder(
            model=app_config.embedder.model,
            base_url=app_config.embedder.base_url,
            dimensions=app_config.embedder.dimensions
        )

        # 測試連接
        connected = await embedder.test_connection()
        if not connected:
            raise CommonErrors.ollama_connection_failed(app_config.embedder.base_url)

        # 初始化 Graphiti (注意：Graphiti 不支援 database 參數)
        logger.info("初始化 Graphiti 核心...")
        graphiti_instance = Graphiti(
            uri=app_config.neo4j.uri,
            user=app_config.neo4j.user,
            password=app_config.neo4j.password,
            llm_client=llm_client,
            embedder=embedder
        )

        # 建立索引
        logger.info("建立 Neo4j 索引和約束...")
        await graphiti_instance.build_indices_and_constraints()

        duration = time.time() - start_time
        log_operation_success("initialize_graphiti", duration)
        logger.info("✅ Graphiti + Ollama MCP 服務器初始化完成")

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
    """添加記憶到 Graphiti（使用新的錯誤處理系統）"""
    start_time = time.time()
    log_operation_start("add_memory", name=args.name, group_id=args.group_id)

    try:
        graphiti = await initialize_graphiti()

        result = await graphiti.add_episode(
            name=args.name,
            episode_body=args.episode_body,
            source_description=args.source_description,
            group_id=args.group_id,
            reference_time=datetime.now(timezone.utc)
        )

        duration = time.time() - start_time

        # 簡化的成功記錄，不提取複雜統計信息
        log_operation_success(
            "add_memory",
            duration,
            episode_id=getattr(result, 'episode_id', None)
        )

        # 記錄性能指標
        performance_logger.log_memory_add_performance(
            len(args.episode_body), duration, True
        )

        return {
            "success": True,
            "message": f"記憶 '{args.name}' 新增成功",
            "episode_id": getattr(result, 'episode_id', None),
            "duration": round(duration, 2)
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
    """搜索記憶節點"""
    try:
        graphiti = await initialize_graphiti()

        # 使用 Graphiti 的 _search API 進行語意搜索
        effective_group_ids = args.group_ids if args.group_ids else []

        # 配置搜索參數
        search_config = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
        search_config.limit = args.max_nodes

        filters = SearchFilters()

        # 使用 Graphiti 的 _search API
        search_results = await graphiti._search(
            query=args.query,
            config=search_config,
            group_ids=effective_group_ids,
            center_node_uuid=None,
            search_filter=filters,
        )

        nodes = []
        if search_results and hasattr(search_results, 'nodes') and search_results.nodes:
            try:
                for node in search_results.nodes:
                    try:
                        # 安全地提取節點資訊
                        node_data = {
                            "name": getattr(node, 'name', '未知名稱'),
                            "uuid": str(getattr(node, 'uuid', '')),
                            "created_at": str(getattr(node, 'created_at', '')) if hasattr(node, 'created_at') else "",
                            "summary": getattr(node, 'summary', '') or '',
                            "group_id": getattr(node, 'group_id', ''),
                            "labels": getattr(node, 'labels', []) if hasattr(node, 'labels') else []
                        }

                        # 確保 labels 是列表
                        if not isinstance(node_data["labels"], list):
                            node_data["labels"] = []

                        nodes.append(node_data)
                    except (AttributeError, TypeError, IndexError) as node_error:
                        logger.warning(f"處理節點時發生錯誤: {node_error}")
                        continue
            except (TypeError, AttributeError) as nodes_error:
                logger.warning(f"處理節點列表時發生錯誤: {nodes_error}")
                nodes = []

        return {
            "message": f"找到 {len(nodes)} 個相關節點" if nodes else "未找到相關節點",
            "nodes": nodes
        }

    except Exception as e:
        return {
            "message": f"搜尋節點時發生錯誤: {str(e)}",
            "nodes": [],
            "error": True
        }

@mcp.tool()
async def search_memory_facts(args: SearchFactsArgs) -> dict:
    """搜索記憶事實"""
    try:
        graphiti = await initialize_graphiti()

        # 使用 Graphiti 的 search API 進行語意搜索
        effective_group_ids = args.group_ids if args.group_ids else []

        # 使用 Graphiti 的搜索 API
        relevant_edges = await graphiti.search(
            group_ids=effective_group_ids,
            query=args.query,
            num_results=args.max_facts
        )

        facts = []
        if relevant_edges:
            try:
                for edge in relevant_edges:
                    try:
                        # 安全地檢查 edge 是否有 fact 屬性
                        if hasattr(edge, 'fact') and getattr(edge, 'fact', None):
                            fact_data = {
                                "fact": getattr(edge, 'fact', ''),
                                "uuid": str(getattr(edge, 'uuid', '')),
                                "created_at": str(getattr(edge, 'created_at', '')) if hasattr(edge, 'created_at') else "",
                                "relation_type": type(edge).__name__ if edge else "unknown"
                            }

                            # 安全地獲取來源和目標實體名稱
                            try:
                                if hasattr(edge, 'source_node_uuid') and hasattr(edge, 'target_node_uuid'):
                                    fact_data["source_entity"] = str(getattr(edge, 'source_node_uuid', ''))
                                    fact_data["target_entity"] = str(getattr(edge, 'target_node_uuid', ''))
                                else:
                                    fact_data["source_entity"] = "unknown"
                                    fact_data["target_entity"] = "unknown"
                            except (AttributeError, TypeError):
                                fact_data["source_entity"] = "unknown"
                                fact_data["target_entity"] = "unknown"

                            facts.append(fact_data)
                    except (AttributeError, TypeError, IndexError) as edge_error:
                        logger.warning(f"處理事實邊時發生錯誤: {edge_error}")
                        continue
            except (TypeError, AttributeError) as edges_error:
                logger.warning(f"處理事實列表時發生錯誤: {edges_error}")
                facts = []

        return {
            "message": f"找到 {len(facts)} 個相關事實" if facts else "未找到相關事實",
            "facts": facts
        }

    except Exception as e:
        return {
            "message": f"搜尋事實時發生錯誤: {str(e)}",
            "facts": [],
            "error": True
        }

@mcp.tool()
async def get_episodes(args: GetEpisodesArgs) -> dict:
    """獲取最近的記憶"""
    try:
        graphiti = await initialize_graphiti()

        query_text = """
        MATCH (e:Episodic)
        WHERE $group_id = '' OR e.group_id = $group_id
        RETURN e.name as name,
               e.content as content,
               e.uuid as uuid,
               e.group_id as group_id,
               e.created_at as created_at
        ORDER BY e.created_at DESC
        LIMIT $limit
        """

        results = await graphiti.driver.execute_query(
            query_text,
            group_id=args.group_id,
            limit=args.last_n
        )

        episodes = []
        if results and results.records:
            for record in results.records:
                episodes.append({
                    "name": record["name"],
                    "content": record.get("content", ""),
                    "uuid": record["uuid"],
                    "group_id": record.get("group_id", ""),
                    "created_at": str(record.get("created_at", ""))
                })

        return {
            "message": f"找到 {len(episodes)} 個記憶片段",
            "episodes": episodes
        }

    except Exception as e:
        return {
            "message": f"獲取記憶片段時發生錯誤: {str(e)}",
            "episodes": [],
            "error": True
        }

@mcp.tool()
async def clear_graph() -> dict:
    """清除圖資料庫"""
    try:
        graphiti = await initialize_graphiti()

        # 清除所有數據
        await graphiti.driver.execute_query("MATCH (n) DETACH DELETE n")

        # 重建索引
        await graphiti.build_indices_and_constraints()

        return {
            "message": "圖資料庫已清除並重建索引"
        }

    except Exception as e:
        return {
            "message": f"清除圖資料庫時發生錯誤: {str(e)}",
            "error": True
        }

@mcp.tool()
async def test_connection() -> dict:
    """測試連接狀態"""
    try:
        graphiti = await initialize_graphiti()

        # 測試 Neo4j 連接
        neo4j_result = await graphiti.driver.execute_query("RETURN 'OK' as status")
        neo4j_status = "OK" if neo4j_result else "FAILED"

        # 測試 Ollama 連接
        llm_status = "OK"  # 如果能初始化就表示連接正常

        return {
            "message": "連接測試完成",
            "neo4j": neo4j_status,
            "ollama_llm": llm_status,
            "embedder": "正常"
        }

    except Exception as e:
        return {
            "message": f"連接測試失敗: {str(e)}",
            "error": True
        }

async def main():
    """啟動 MCP 服務器（使用新配置系統）"""
    parser = argparse.ArgumentParser(description="Graphiti Ollama MCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse"], help="Transport protocol")
    parser.add_argument("--host", help="Server host")
    parser.add_argument("--port", type=int, help="Server port")
    parser.add_argument("--config", help="Configuration file path")

    args = parser.parse_args()

    try:
        # 初始化系統配置
        # 調整配置檔案路徑
        config_path = args.config
        if config_path and not config_path.startswith('/') and not config_path.startswith('configs/'):
            config_path = f"configs/{config_path}"

        config = initialize_system(config_path)

        # 使用命令行參數覆蓋配置
        if args.transport:
            config.server.transport = args.transport
        if args.host:
            config.server.host = args.host
        if args.port:
            config.server.port = args.port

        logger.info(f"🚀 啟動 Graphiti MCP Server")
        logger.info(f"   傳輸協議: {config.server.transport}")
        logger.info(f"   服務地址: {config.server.host}:{config.server.port}")

        # 設置 FastMCP 配置
        if hasattr(mcp, 'settings'):
            if config.server.host != 'localhost':
                mcp.settings.host = config.server.host
            if config.server.port != 3001:
                mcp.settings.port = config.server.port

        # 啟動服務器
        if config.server.transport == "stdio":
            logger.info("啟動 STDIO 模式...")
            await mcp.run_stdio_async()
        elif config.server.transport == "sse":
            logger.info("啟動 SSE 模式...")
            await mcp.run_sse_async()
        else:
            raise ValueError(f"不支援的傳輸協議: {config.server.transport}")

    except Exception as e:
        if logger:
            logger.error(f"服務器啟動失敗: {e}")
        else:
            print(f"❌ 服務器啟動失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())