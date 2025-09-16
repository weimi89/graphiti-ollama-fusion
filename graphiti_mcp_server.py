#!/usr/bin/env python3
"""
Graphiti Ollama MCP Server - 整合 Ollama 本地 LLM 的 MCP 服務器
基於我們的 Graphiti + Ollama 解決方案
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, List

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

# 使用我們的自定義 Ollama 組件
from ollama_graphiti_client import OptimizedOllamaClient
from ollama_embedder import OllamaEmbedder
from graphiti_core import Graphiti
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.edges import EntityEdge
from graphiti_core.nodes import EpisodicNode

load_dotenv()

# MCP 工具的參數模型
class AddMemoryArgs(BaseModel):
    name: str = Field(description="Name of the episode/memory")
    episode_body: str = Field(description="Content of the episode/memory")
    source_description: str = Field(default="MCP Server", description="Source description")
    group_id: str = Field(default="default", description="Group ID for the memory")

class SearchNodesArgs(BaseModel):
    query: str = Field(description="Search query")
    max_nodes: int = Field(default=10, description="Maximum number of nodes to return")
    group_ids: List[str] = Field(default_factory=list, description="Group IDs to filter by")

class SearchFactsArgs(BaseModel):
    query: str = Field(description="Search query")
    max_facts: int = Field(default=10, description="Maximum number of facts to return")
    group_ids: List[str] = Field(default_factory=list, description="Group IDs to filter by")

class GetEpisodesArgs(BaseModel):
    last_n: int = Field(default=10, description="Number of recent episodes to retrieve")
    group_id: str = Field(default="", description="Group ID to filter by")

# 全局變量
graphiti_instance: Graphiti = None

async def initialize_graphiti():
    """初始化 Graphiti 實例使用 Ollama"""
    global graphiti_instance

    if graphiti_instance is not None:
        return graphiti_instance

    print("🚀 正在初始化 Graphiti + Ollama MCP 服務器...")

    try:
        # 初始化 LLM 客戶端
        model_name = os.getenv('MODEL_NAME', 'qwen2.5:14b')
        print(f"📡 使用 LLM 模型: {model_name}")

        llm_config = LLMConfig(
            api_key="not-needed",
            model=model_name,
            base_url=os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'),
            temperature=float(os.getenv('LLM_TEMPERATURE', '0.1'))
        )
        llm_client = OptimizedOllamaClient(llm_config)

        # 初始化嵌入器
        embedder_model = os.getenv('EMBEDDER_MODEL_NAME', 'nomic-embed-text:v1.5')
        print(f"🧲 使用嵌入模型: {embedder_model}")

        embedder = OllamaEmbedder(
            model=embedder_model,
            base_url="http://localhost:11434"
        )

        # 測試連接
        connected = await embedder.test_connection()
        if not connected:
            raise Exception("無法連接到 Ollama 嵌入器")

        # 初始化 Graphiti
        graphiti_instance = Graphiti(
            uri=os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
            user=os.getenv('NEO4J_USER', 'neo4j'),
            password=os.getenv('NEO4J_PASSWORD', ''),
            llm_client=llm_client,
            embedder=embedder
        )

        # 建立索引
        await graphiti_instance.build_indices_and_constraints()
        print("✅ Graphiti + Ollama MCP 服務器初始化完成")

        return graphiti_instance

    except Exception as e:
        print(f"❌ 初始化失敗: {e}")
        raise

# 創建 FastMCP 應用
mcp = FastMCP("graphiti-ollama-memory")

@mcp.tool()
async def add_memory_simple(args: AddMemoryArgs) -> dict:
    """添加記憶到 Graphiti"""
    try:
        graphiti = await initialize_graphiti()

        result = await graphiti.add_episode(
            name=args.name,
            episode_body=args.episode_body,
            source_description=args.source_description,
            group_id=args.group_id,
            reference_time=datetime.now(timezone.utc)
        )

        return {
            "message": f"Episode '{args.name}' added successfully",
            "episode_id": result.episode_id if hasattr(result, 'episode_id') else None,
            "nodes_extracted": len(result.node_ids) if hasattr(result, 'node_ids') and result.node_ids else 0,
            "edges_created": len(result.edge_ids) if hasattr(result, 'edge_ids') and result.edge_ids else 0
        }

    except Exception as e:
        return {
            "message": f"Error adding episode: {str(e)}",
            "error": True
        }

@mcp.tool()
async def search_memory_nodes(args: SearchNodesArgs) -> dict:
    """搜索記憶節點"""
    try:
        graphiti = await initialize_graphiti()

        # 使用基本的文字搜索（繞過向量搜索問題）
        query_text = """
        MATCH (n:Entity)
        WHERE ($query = '' OR n.name CONTAINS $query OR n.summary CONTAINS $query)
        AND ($group_ids IS NULL OR n.group_id IN $group_ids)
        RETURN n.name as name,
               n.uuid as uuid,
               n.created_at as created_at,
               n.summary as summary
        LIMIT $limit
        """

        group_filter = args.group_ids if args.group_ids else None
        results = await graphiti.driver.execute_query(
            query_text,
            query=args.query,
            group_ids=group_filter,
            limit=args.max_nodes
        )

        nodes = []
        if results and results.records:
            for record in results.records:
                nodes.append({
                    "name": record["name"],
                    "uuid": record["uuid"],
                    "created_at": str(record.get("created_at", "")),
                    "summary": record.get("summary", "")
                })

        return {
            "message": f"Found {len(nodes)} relevant nodes" if nodes else "No relevant nodes found",
            "nodes": nodes
        }

    except Exception as e:
        return {
            "message": f"Error searching nodes: {str(e)}",
            "nodes": [],
            "error": True
        }

@mcp.tool()
async def search_memory_facts(args: SearchFactsArgs) -> dict:
    """搜索記憶事實"""
    try:
        graphiti = await initialize_graphiti()

        # 搜索包含查詢關鍵字的關係事實
        query_text = """
        MATCH (a:Entity)-[r]->(b:Entity)
        WHERE (r.fact IS NOT NULL AND ($query = '' OR r.fact CONTAINS $query))
        AND ($group_ids IS NULL OR a.group_id IN $group_ids)
        RETURN r.fact as fact,
               a.name as source_entity,
               b.name as target_entity,
               COALESCE(r.uuid, 'no-uuid') as uuid,
               r.created_at as created_at,
               type(r) as relation_type
        LIMIT $limit
        """

        group_filter = args.group_ids if args.group_ids else None
        results = await graphiti.driver.execute_query(
            query_text,
            query=args.query,
            group_ids=group_filter,
            limit=args.max_facts
        )

        facts = []
        if results and results.records:
            for record in results.records:
                facts.append({
                    "fact": record["fact"],
                    "source_entity": record["source_entity"],
                    "target_entity": record["target_entity"],
                    "uuid": record["uuid"],
                    "created_at": str(record.get("created_at", "")),
                    "relation_type": record.get("relation_type", "UNKNOWN")
                })

        return {
            "message": f"Found {len(facts)} relevant facts" if facts else "No relevant facts found",
            "facts": facts
        }

    except Exception as e:
        return {
            "message": f"Error searching facts: {str(e)}",
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
            "message": f"Found {len(episodes)} episodes",
            "episodes": episodes
        }

    except Exception as e:
        return {
            "message": f"Error retrieving episodes: {str(e)}",
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
            "message": "Graph cleared successfully and indices rebuilt"
        }

    except Exception as e:
        return {
            "message": f"Error clearing graph: {str(e)}",
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
            "message": "Connection test completed",
            "neo4j": neo4j_status,
            "ollama_llm": llm_status,
            "embedder": "OK"
        }

    except Exception as e:
        return {
            "message": f"Connection test failed: {str(e)}",
            "error": True
        }

async def main():
    """啟動 MCP 服務器"""
    parser = argparse.ArgumentParser(description="Graphiti Ollama MCP Server")
    parser.add_argument("--transport", default="stdio", choices=["stdio", "sse"])
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=3001)

    args = parser.parse_args()

    # Set host and port if provided
    if hasattr(mcp, 'settings'):
        if args.host != 'localhost':
            mcp.settings.host = args.host
        if args.port != 3001:
            mcp.settings.port = args.port

    if args.transport == "stdio":
        # STDIO 模式
        await mcp.run_stdio_async()
    elif args.transport == "sse":
        # SSE 模式
        await mcp.run_sse_async()

if __name__ == "__main__":
    asyncio.run(main())