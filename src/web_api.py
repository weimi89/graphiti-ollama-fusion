"""
Graphiti Web 管理介面 REST API
==============================

提供知識圖譜資料的 REST API 端點，包含：
- 統計資訊
- 實體節點瀏覽/搜尋
- 事實關係瀏覽/搜尋
- 記憶片段瀏覽
- 刪除操作
- Group 管理
"""

import asyncio
import json
import logging
import os
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Coroutine, Any, List

from src.timezone_utils import format_timestamp
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse, Response
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 簡易速率限制器（記憶體內，按 IP）
# ---------------------------------------------------------------------------

# 搜尋超時秒數
SEARCH_TIMEOUT = 30

class _RateLimiter:
    """每分鐘每 IP 最多 N 次請求的簡易速率限制器。"""

    def __init__(self, max_requests: int = 15, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._call_count = 0

    def is_allowed(self, ip: str) -> bool:
        now = time.monotonic()
        # 每 100 次呼叫全域清理一次，移除不再活躍的 IP 條目
        self._call_count += 1
        if self._call_count % 100 == 0:
            self._hits = {
                k: [t for t in v if now - t < self.window]
                for k, v in self._hits.items()
                if any(now - t < self.window for t in v)
            }
        hits = self._hits[ip]
        # 清除當前 IP 的過期記錄
        self._hits[ip] = [t for t in hits if now - t < self.window]
        if len(self._hits[ip]) >= self.max_requests:
            return False
        self._hits[ip].append(now)
        return True

_search_limiter = _RateLimiter(max_requests=15, window_seconds=60)

# 專案根目錄下的 web/ 資料夾
WEB_DIR = Path(__file__).parent.parent / "web"


def get_cors_middleware(cors_origins: List[str] | None = None) -> Middleware:
    """建立 CORS 中間件。"""
    origins = cors_origins or ["*"]
    return Middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )


def create_web_routes(
    get_graphiti_fn: Callable[[], Coroutine[Any, Any, Any]],
    cors_origins: List[str] | None = None,
) -> list:
    """
    建立 Web 管理介面所需的所有路由。

    Args:
        get_graphiti_fn: 取得 Graphiti 實例的非同步函數
        cors_origins: CORS 允許的來源列表

    Returns:
        list: Starlette Route/Mount 列表
    """

    # ------------------------------------------------------------------
    # API 端點
    # ------------------------------------------------------------------

    async def api_stats(request: Request) -> JSONResponse:
        """取得儀表板統計資訊。"""
        try:
            graphiti = await get_graphiti_fn()
            group_id = request.query_params.get("group_id", "")

            async with graphiti.driver.session() as session:
                group_filter = "WHERE n.group_id = $group_id" if group_id else ""
                params = {"group_id": group_id} if group_id else {}

                # 節點數
                result = await session.run(
                    f"MATCH (n:Entity) {group_filter} RETURN count(n) as count", params
                )
                records = [r async for r in result]
                node_count = records[0]["count"] if records else 0

                # 事實數
                edge_filter = "WHERE r.group_id = $group_id" if group_id else ""
                result = await session.run(
                    f"MATCH ()-[r:RELATES_TO]->() {edge_filter} RETURN count(r) as count",
                    params,
                )
                records = [r async for r in result]
                fact_count = records[0]["count"] if records else 0

                # 記憶片段數
                ep_filter = "WHERE e.group_id = $group_id" if group_id else ""
                result = await session.run(
                    f"MATCH (e:Episodic) {ep_filter} RETURN count(e) as count", params
                )
                records = [r async for r in result]
                episode_count = records[0]["count"] if records else 0

            return JSONResponse({
                "nodes": node_count,
                "facts": fact_count,
                "episodes": episode_count,
                "group_id": group_id or "(全部)",
            })
        except Exception as e:
            logger.error(f"API stats error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    async def api_groups(request: Request) -> JSONResponse:
        """取得所有 group_id。"""
        try:
            graphiti = await get_graphiti_fn()
            async with graphiti.driver.session() as session:
                result = await session.run("""
                    CALL {
                        MATCH (n:Entity) WHERE n.group_id IS NOT NULL
                        RETURN DISTINCT n.group_id AS gid
                        UNION
                        MATCH (e:Episodic) WHERE e.group_id IS NOT NULL
                        RETURN DISTINCT e.group_id AS gid
                        UNION
                        MATCH ()-[r:RELATES_TO]->() WHERE r.group_id IS NOT NULL
                        RETURN DISTINCT r.group_id AS gid
                    }
                    RETURN DISTINCT gid ORDER BY gid
                """)
                groups = [r["gid"] async for r in result if r["gid"]]

            return JSONResponse({"groups": groups})
        except Exception as e:
            logger.error(f"API groups error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    async def api_nodes(request: Request) -> JSONResponse:
        """瀏覽實體節點（分頁）。"""
        try:
            graphiti = await get_graphiti_fn()
            group_id = request.query_params.get("group_id", "")
            page = int(request.query_params.get("page", "1"))
            limit = min(int(request.query_params.get("limit", "20")), 100)
            search = request.query_params.get("search", "").strip()
            skip = (page - 1) * limit

            conditions = []
            params: dict[str, Any] = {"skip": skip, "limit": limit}

            if group_id:
                conditions.append("n.group_id = $group_id")
                params["group_id"] = group_id

            if search:
                conditions.append("(toLower(n.name) CONTAINS toLower($search) OR toLower(n.summary) CONTAINS toLower($search))")
                params["search"] = search

            where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

            t0 = time.monotonic() if search else None
            async with graphiti.driver.session() as session:
                # 總數
                result = await session.run(
                    f"MATCH (n:Entity) {where} RETURN count(n) as total", params
                )
                records = [r async for r in result]
                total = records[0]["total"] if records else 0

                # 資料
                result = await session.run(
                    f"""MATCH (n:Entity) {where}
                    RETURN n.uuid AS uuid, n.name AS name, n.summary AS summary,
                           n.group_id AS group_id, n.created_at AS created_at,
                           labels(n) AS labels
                    ORDER BY n.created_at DESC
                    SKIP $skip LIMIT $limit""",
                    params,
                )
                nodes = []
                async for r in result:
                    nodes.append({
                        "uuid": r["uuid"],
                        "name": r["name"] or "",
                        "summary": (r["summary"] or "")[:200],
                        "group_id": r["group_id"] or "",
                        "created_at": format_timestamp(r["created_at"]),
                        "labels": [l for l in (r["labels"] or []) if l not in ("Entity", "__Entity__")],
                    })
            duration = round(time.monotonic() - t0, 2) if t0 is not None else None

            resp = {
                "nodes": nodes,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": max(1, (total + limit - 1) // limit),
            }
            if search:
                resp["search"] = search
            if duration is not None:
                resp["duration"] = duration
            return JSONResponse(resp)
        except Exception as e:
            logger.error(f"API nodes error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    async def api_facts(request: Request) -> JSONResponse:
        """瀏覽事實關係（分頁）。"""
        try:
            graphiti = await get_graphiti_fn()
            group_id = request.query_params.get("group_id", "")
            page = int(request.query_params.get("page", "1"))
            limit = min(int(request.query_params.get("limit", "20")), 100)
            search = request.query_params.get("search", "").strip()
            skip = (page - 1) * limit

            conditions = []
            params: dict[str, Any] = {"skip": skip, "limit": limit}

            if group_id:
                conditions.append("r.group_id = $group_id")
                params["group_id"] = group_id

            if search:
                conditions.append("(toLower(r.name) CONTAINS toLower($search) OR toLower(r.fact) CONTAINS toLower($search))")
                params["search"] = search

            where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

            t0 = time.monotonic() if search else None
            async with graphiti.driver.session() as session:
                result = await session.run(
                    f"MATCH (s)-[r:RELATES_TO]->(t) {where} RETURN count(r) as total",
                    params,
                )
                records = [r async for r in result]
                total = records[0]["total"] if records else 0

                result = await session.run(
                    f"""MATCH (s)-[r:RELATES_TO]->(t) {where}
                    RETURN r.uuid AS uuid, r.name AS name, r.fact AS fact,
                           r.group_id AS group_id, r.created_at AS created_at,
                           s.name AS source_name, t.name AS target_name,
                           s.uuid AS source_uuid, t.uuid AS target_uuid
                    ORDER BY r.created_at DESC
                    SKIP $skip LIMIT $limit""",
                    params,
                )
                facts = []
                async for r in result:
                    facts.append({
                        "uuid": r["uuid"],
                        "name": r["name"] or "",
                        "fact": (r["fact"] or "")[:300],
                        "group_id": r["group_id"] or "",
                        "created_at": format_timestamp(r["created_at"]),
                        "source_name": r["source_name"] or "",
                        "target_name": r["target_name"] or "",
                        "source_uuid": r["source_uuid"] or "",
                        "target_uuid": r["target_uuid"] or "",
                    })
            duration = round(time.monotonic() - t0, 2) if t0 is not None else None

            resp = {
                "facts": facts,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": max(1, (total + limit - 1) // limit),
            }
            if search:
                resp["search"] = search
            if duration is not None:
                resp["duration"] = duration
            return JSONResponse(resp)
        except Exception as e:
            logger.error(f"API facts error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    async def api_episodes(request: Request) -> JSONResponse:
        """瀏覽記憶片段（分頁，支援關鍵字搜尋）。"""
        try:
            graphiti = await get_graphiti_fn()
            group_id = request.query_params.get("group_id", "")
            page = int(request.query_params.get("page", "1"))
            limit = min(int(request.query_params.get("limit", "20")), 100)
            search = request.query_params.get("search", "").strip()
            skip = (page - 1) * limit

            conditions = []
            params: dict[str, Any] = {"skip": skip, "limit": limit}

            if group_id:
                conditions.append("e.group_id = $group_id")
                params["group_id"] = group_id

            if search:
                conditions.append("(toLower(e.name) CONTAINS toLower($search) OR toLower(e.content) CONTAINS toLower($search))")
                params["search"] = search

            where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

            t0 = time.monotonic() if search else None
            async with graphiti.driver.session() as session:
                result = await session.run(
                    f"MATCH (e:Episodic) {where} RETURN count(e) as total", params
                )
                records = [r async for r in result]
                total = records[0]["total"] if records else 0

                result = await session.run(
                    f"""MATCH (e:Episodic) {where}
                    RETURN e.uuid AS uuid, e.name AS name, e.content AS content,
                           e.group_id AS group_id, e.created_at AS created_at,
                           e.source_description AS source_description
                    ORDER BY e.created_at DESC
                    SKIP $skip LIMIT $limit""",
                    params,
                )
                episodes = []
                async for r in result:
                    episodes.append({
                        "uuid": r["uuid"],
                        "name": r["name"] or "",
                        "content": (r["content"] or "")[:500],
                        "group_id": r["group_id"] or "",
                        "created_at": format_timestamp(r["created_at"]),
                        "source_description": r["source_description"] or "",
                    })
            duration = round(time.monotonic() - t0, 2) if t0 is not None else None

            resp = {
                "episodes": episodes,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": max(1, (total + limit - 1) // limit),
            }
            if search:
                resp["search"] = search
            if duration is not None:
                resp["duration"] = duration
            return JSONResponse(resp)
        except Exception as e:
            logger.error(f"API episodes error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    async def api_delete_episode(request: Request) -> JSONResponse:
        """刪除記憶片段（事務性：連帶清理關聯邊）。"""
        try:
            uuid = request.path_params["uuid"]
            graphiti = await get_graphiti_fn()
            async with graphiti.driver.session() as session:
                result = await session.run(
                    """
                    MATCH (e:Episodic {uuid: $uuid})
                    OPTIONAL MATCH (e)-[r]-()
                    DELETE r, e
                    RETURN count(e) AS deleted
                    """,
                    {"uuid": uuid},
                )
                record = await result.single()
                deleted = record["deleted"] if record else 0
            if deleted == 0:
                return JSONResponse({"error": f"記憶片段 {uuid} 不存在"}, status_code=404)
            return JSONResponse({"success": True, "message": f"記憶片段 {uuid} 已刪除（含關聯邊）"})
        except Exception as e:
            logger.error(f"API delete episode error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    async def api_delete_fact(request: Request) -> JSONResponse:
        """刪除事實（事務性）。"""
        try:
            uuid = request.path_params["uuid"]
            graphiti = await get_graphiti_fn()
            async with graphiti.driver.session() as session:
                result = await session.run(
                    """
                    MATCH ()-[r:RELATES_TO {uuid: $uuid}]-()
                    DELETE r
                    RETURN count(r) AS deleted
                    """,
                    {"uuid": uuid},
                )
                record = await result.single()
                deleted = record["deleted"] if record else 0
            if deleted == 0:
                return JSONResponse({"error": f"事實 {uuid} 不存在"}, status_code=404)
            return JSONResponse({"success": True, "message": f"事實 {uuid} 已刪除"})
        except Exception as e:
            logger.error(f"API delete fact error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    async def api_delete_node(request: Request) -> JSONResponse:
        """刪除實體節點（事務性：連帶清理關聯邊）。"""
        try:
            uuid = request.path_params["uuid"]
            graphiti = await get_graphiti_fn()
            async with graphiti.driver.session() as session:
                result = await session.run(
                    """
                    MATCH (n:Entity {uuid: $uuid})
                    OPTIONAL MATCH (n)-[r]-()
                    DELETE r, n
                    RETURN count(n) AS deleted
                    """,
                    {"uuid": uuid},
                )
                record = await result.single()
                deleted = record["deleted"] if record else 0
            if deleted == 0:
                return JSONResponse({"error": f"實體節點 {uuid} 不存在"}, status_code=404)
            return JSONResponse({"success": True, "message": f"實體節點 {uuid} 已刪除（含關聯邊）"})
        except Exception as e:
            logger.error(f"API delete node error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    async def api_delete_group(request: Request) -> JSONResponse:
        """清除特定 group 的所有資料。"""
        try:
            from graphiti_core.utils.maintenance.graph_data_operations import clear_data

            group_id = request.path_params["group_id"]
            graphiti = await get_graphiti_fn()
            await clear_data(graphiti.driver, group_ids=[group_id])
            return JSONResponse({"success": True, "message": f"群組 {group_id} 已清除"})
        except Exception as e:
            logger.error(f"API delete group error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    async def api_search_nodes(request: Request) -> JSONResponse:
        """向量搜尋節點（含速率限制和超時）。"""
        try:
            client_ip = request.client.host if request.client else "unknown"
            if not _search_limiter.is_allowed(client_ip):
                return JSONResponse(
                    {"error": "搜尋請求過於頻繁，請稍後再試"}, status_code=429
                )

            from graphiti_core.search.search_config_recipes import NODE_HYBRID_SEARCH_RRF
            from graphiti_core.search.search_filters import SearchFilters

            q = request.query_params.get("q", "").strip()
            if not q:
                return JSONResponse({"error": "缺少搜尋參數 q"}, status_code=400)

            group_ids_str = request.query_params.get("group_ids", "")
            group_ids = [g.strip() for g in group_ids_str.split(",") if g.strip()] if group_ids_str else []
            limit = min(int(request.query_params.get("limit", "10")), 50)

            graphiti = await get_graphiti_fn()
            search_config = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
            search_config.limit = limit

            t0 = time.monotonic()
            results = await asyncio.wait_for(
                graphiti.search_(
                    query=q,
                    config=search_config,
                    group_ids=group_ids,
                    search_filter=SearchFilters(),
                ),
                timeout=SEARCH_TIMEOUT,
            )
            duration = round(time.monotonic() - t0, 2)

            nodes = []
            for n in (results.nodes or []):
                nodes.append({
                    "uuid": str(getattr(n, "uuid", "")),
                    "name": getattr(n, "name", ""),
                    "summary": (getattr(n, "summary", "") or "")[:200],
                    "group_id": getattr(n, "group_id", ""),
                    "created_at": format_timestamp(getattr(n, "created_at", "")),
                    "labels": getattr(n, "labels", []),
                })

            return JSONResponse({"nodes": nodes, "query": q, "total": len(nodes), "duration": duration})
        except asyncio.TimeoutError:
            logger.warning(f"搜尋節點超時 ({SEARCH_TIMEOUT}s): {q}")
            return JSONResponse({"error": "搜尋超時，請縮小查詢範圍"}, status_code=504)
        except Exception as e:
            logger.error(f"API search nodes error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    async def api_search_facts(request: Request) -> JSONResponse:
        """向量搜尋事實（含速率限制和超時）。"""
        try:
            client_ip = request.client.host if request.client else "unknown"
            if not _search_limiter.is_allowed(client_ip):
                return JSONResponse(
                    {"error": "搜尋請求過於頻繁，請稍後再試"}, status_code=429
                )

            q = request.query_params.get("q", "").strip()
            if not q:
                return JSONResponse({"error": "缺少搜尋參數 q"}, status_code=400)

            group_ids_str = request.query_params.get("group_ids", "")
            group_ids = [g.strip() for g in group_ids_str.split(",") if g.strip()] if group_ids_str else []
            limit = min(int(request.query_params.get("limit", "10")), 50)

            graphiti = await get_graphiti_fn()
            t0 = time.monotonic()
            edges = await asyncio.wait_for(
                graphiti.search(
                    query=q,
                    group_ids=group_ids,
                    num_results=limit,
                ),
                timeout=SEARCH_TIMEOUT,
            )
            duration = round(time.monotonic() - t0, 2)

            facts = []
            for e in edges:
                facts.append({
                    "uuid": str(getattr(e, "uuid", "")),
                    "name": getattr(e, "name", ""),
                    "fact": (getattr(e, "fact", "") or "")[:300],
                    "group_id": getattr(e, "group_id", ""),
                    "created_at": format_timestamp(getattr(e, "created_at", "")),
                    "source_node_uuid": str(getattr(e, "source_node_uuid", "")),
                    "target_node_uuid": str(getattr(e, "target_node_uuid", "")),
                })

            return JSONResponse({"facts": facts, "query": q, "total": len(facts), "duration": duration})
        except asyncio.TimeoutError:
            logger.warning(f"搜尋事實超時 ({SEARCH_TIMEOUT}s): {q}")
            return JSONResponse({"error": "搜尋超時，請縮小查詢範圍"}, status_code=504)
        except Exception as e:
            logger.error(f"API search facts error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    async def api_search_episodes(request: Request) -> JSONResponse:
        """全文搜尋記憶片段（BM25）。"""
        try:
            client_ip = request.client.host if request.client else "unknown"
            if not _search_limiter.is_allowed(client_ip):
                return JSONResponse(
                    {"error": "搜尋請求過於頻繁，請稍後再試"}, status_code=429
                )

            from graphiti_core.search.search_config import (
                SearchConfig,
                EpisodeSearchConfig,
                EpisodeSearchMethod,
            )

            q = request.query_params.get("q", "").strip()
            if not q:
                return JSONResponse({"error": "缺少搜尋參數 q"}, status_code=400)

            group_ids_str = request.query_params.get("group_ids", "")
            group_ids = (
                [g.strip() for g in group_ids_str.split(",") if g.strip()]
                if group_ids_str
                else []
            )
            limit = min(int(request.query_params.get("limit", "10")), 50)

            graphiti = await get_graphiti_fn()
            config = SearchConfig(
                episode_config=EpisodeSearchConfig(
                    search_methods=[EpisodeSearchMethod.bm25]
                ),
                limit=limit,
            )
            t0 = time.monotonic()
            results = await asyncio.wait_for(
                graphiti.search_(query=q, config=config, group_ids=group_ids),
                timeout=SEARCH_TIMEOUT,
            )
            duration = round(time.monotonic() - t0, 2)

            episodes = [
                {
                    "uuid": str(getattr(ep, "uuid", "")),
                    "name": getattr(ep, "name", ""),
                    "content": (getattr(ep, "content", "") or "")[:500],
                    "group_id": getattr(ep, "group_id", ""),
                    "created_at": format_timestamp(getattr(ep, "created_at", "")),
                    "source_description": getattr(ep, "source_description", ""),
                }
                for ep in (results.episodes or [])
            ]

            return JSONResponse(
                {"episodes": episodes, "query": q, "total": len(episodes), "duration": duration}
            )
        except asyncio.TimeoutError:
            logger.warning(f"搜尋記憶片段超時 ({SEARCH_TIMEOUT}s): {q}")
            return JSONResponse({"error": "搜尋超時，請縮小查詢範圍"}, status_code=504)
        except Exception as e:
            logger.error(f"API search episodes error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    async def api_node_relations(request: Request) -> JSONResponse:
        """取得節點的所有關係（事實）。"""
        try:
            uuid = request.path_params["uuid"]
            graphiti = await get_graphiti_fn()
            async with graphiti.driver.session() as session:
                result = await session.run(
                    """
                    MATCH (n:Entity {uuid: $uuid})-[r:RELATES_TO]->(t:Entity)
                    RETURN r.uuid AS uuid, r.name AS name, r.fact AS fact,
                           n.name AS source_name, t.name AS target_name, 'outgoing' AS direction
                    UNION
                    MATCH (s:Entity)-[r:RELATES_TO]->(n:Entity {uuid: $uuid})
                    RETURN r.uuid AS uuid, r.name AS name, r.fact AS fact,
                           s.name AS source_name, n.name AS target_name, 'incoming' AS direction
                    """,
                    {"uuid": uuid},
                )
                relations = [
                    {
                        "uuid": r["uuid"],
                        "name": r["name"] or "",
                        "fact": (r["fact"] or "")[:300],
                        "source_name": r["source_name"] or "",
                        "target_name": r["target_name"] or "",
                        "direction": r["direction"],
                    }
                    async for r in result
                ]
            return JSONResponse({"relations": relations, "total": len(relations)})
        except Exception as e:
            logger.error(f"API node relations error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    # ------------------------------------------------------------------
    # 新增 API 端點：Phase 2-4 功能
    # ------------------------------------------------------------------

    async def api_groups_stats(request: Request) -> JSONResponse:
        """取得各 Group 的統計和健康度資訊。"""
        try:
            graphiti = await get_graphiti_fn()
            async with graphiti.driver.session() as session:
                # 節點數 by group
                result = await session.run("""
                    MATCH (n:Entity)
                    WHERE n.group_id IS NOT NULL
                    RETURN n.group_id AS group_id, count(n) AS count
                    ORDER BY count DESC
                """)
                node_counts = {r["group_id"]: r["count"] async for r in result}

                # 事實數 by group
                result = await session.run("""
                    MATCH ()-[r:RELATES_TO]->()
                    WHERE r.group_id IS NOT NULL
                    RETURN r.group_id AS group_id, count(r) AS count
                    ORDER BY count DESC
                """)
                fact_counts = {r["group_id"]: r["count"] async for r in result}

                # 片段數 by group
                result = await session.run("""
                    MATCH (e:Episodic)
                    WHERE e.group_id IS NOT NULL
                    RETURN e.group_id AS group_id, count(e) AS count
                    ORDER BY count DESC
                """)
                episode_counts = {r["group_id"]: r["count"] async for r in result}

                # 每 group top 5 實體（按 degree）
                result = await session.run("""
                    MATCH (n:Entity)
                    WHERE n.group_id IS NOT NULL
                    OPTIONAL MATCH (n)-[r:RELATES_TO]-()
                    WITH n.group_id AS group_id, n.name AS name, n.uuid AS uuid,
                         count(DISTINCT r) AS degree
                    ORDER BY degree DESC
                    WITH group_id, collect({name: name, uuid: uuid, degree: degree})[0..5] AS top5
                    RETURN group_id, top5
                """)
                top_entities = {r["group_id"]: r["top5"] async for r in result}

                # 最後更新時間 by group
                result = await session.run("""
                    MATCH (n:Entity)
                    WHERE n.group_id IS NOT NULL AND n.created_at IS NOT NULL
                    RETURN n.group_id AS group_id, max(n.created_at) AS last_updated
                """)
                last_updated = {
                    r["group_id"]: str(r["last_updated"]) if r["last_updated"] else ""
                    async for r in result
                }

            # 合併所有 group_id
            all_groups = sorted(set(
                list(node_counts) + list(fact_counts) + list(episode_counts)
            ))

            groups = []
            for gid in all_groups:
                groups.append({
                    "group_id": gid,
                    "nodes": node_counts.get(gid, 0),
                    "facts": fact_counts.get(gid, 0),
                    "episodes": episode_counts.get(gid, 0),
                    "top_entities": top_entities.get(gid, []),
                    "last_updated": last_updated.get(gid, ""),
                })

            return JSONResponse({"groups": groups})
        except Exception as e:
            logger.error(f"API groups stats error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    async def api_timeline(request: Request) -> JSONResponse:
        """取得時間線資料（按天聚合）。"""
        try:
            graphiti = await get_graphiti_fn()
            group_id = request.query_params.get("group_id", "")
            days = min(int(request.query_params.get("days", "30")), 365)

            group_filter_n = "AND n.group_id = $group_id" if group_id else ""
            group_filter_r = "AND r.group_id = $group_id" if group_id else ""
            group_filter_e = "AND e.group_id = $group_id" if group_id else ""
            params: dict[str, Any] = {"days": days}
            if group_id:
                params["group_id"] = group_id

            async with graphiti.driver.session() as session:
                # 節點 by day
                result = await session.run(f"""
                    MATCH (n:Entity)
                    WHERE n.created_at IS NOT NULL
                      AND date(n.created_at) >= date() - duration({{days: $days}})
                      {group_filter_n}
                    RETURN toString(date(n.created_at)) AS day, count(n) AS count
                    ORDER BY day
                """, params)
                node_days = {r["day"]: r["count"] async for r in result}

                # 事實 by day
                result = await session.run(f"""
                    MATCH ()-[r:RELATES_TO]->()
                    WHERE r.created_at IS NOT NULL
                      AND date(r.created_at) >= date() - duration({{days: $days}})
                      {group_filter_r}
                    RETURN toString(date(r.created_at)) AS day, count(r) AS count
                    ORDER BY day
                """, params)
                fact_days = {r["day"]: r["count"] async for r in result}

                # 片段 by day
                result = await session.run(f"""
                    MATCH (e:Episodic)
                    WHERE e.created_at IS NOT NULL
                      AND date(e.created_at) >= date() - duration({{days: $days}})
                      {group_filter_e}
                    RETURN toString(date(e.created_at)) AS day, count(e) AS count
                    ORDER BY day
                """, params)
                episode_days = {r["day"]: r["count"] async for r in result}

            # 合併所有日期
            all_dates = sorted(set(
                list(node_days) + list(fact_days) + list(episode_days)
            ), reverse=True)
            timeline = [
                {
                    "date": d,
                    "nodes": node_days.get(d, 0),
                    "facts": fact_days.get(d, 0),
                    "episodes": episode_days.get(d, 0),
                }
                for d in all_dates
            ]

            return JSONResponse({"timeline": timeline, "days": days})
        except Exception as e:
            logger.error(f"API timeline error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    async def api_analytics_top_nodes(request: Request) -> JSONResponse:
        """取得影響力最大的節點（按 degree 排序）。"""
        try:
            graphiti = await get_graphiti_fn()
            group_id = request.query_params.get("group_id", "")
            limit = min(int(request.query_params.get("limit", "20")), 100)

            group_filter = "WHERE n.group_id = $group_id" if group_id else ""
            params: dict[str, Any] = {"limit": limit}
            if group_id:
                params["group_id"] = group_id

            async with graphiti.driver.session() as session:
                result = await session.run(f"""
                    MATCH (n:Entity)
                    {group_filter}
                    OPTIONAL MATCH (n)-[r:RELATES_TO]-()
                    WITH n, count(DISTINCT r) AS degree
                    RETURN n.uuid AS uuid, n.name AS name, n.summary AS summary,
                           n.group_id AS group_id, n.created_at AS created_at,
                           degree
                    ORDER BY degree DESC
                    LIMIT $limit
                """, params)
                nodes = []
                async for r in result:
                    nodes.append({
                        "uuid": r["uuid"],
                        "name": r["name"] or "",
                        "summary": (r["summary"] or "")[:200],
                        "group_id": r["group_id"] or "",
                        "created_at": format_timestamp(r["created_at"]),
                        "degree": r["degree"],
                    })

            return JSONResponse({"nodes": nodes, "total": len(nodes)})
        except Exception as e:
            logger.error(f"API analytics top nodes error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    async def api_analytics_quality(request: Request) -> JSONResponse:
        """取得知識品質指標。"""
        try:
            graphiti = await get_graphiti_fn()
            group_id = request.query_params.get("group_id", "")

            group_filter = "WHERE n.group_id = $group_id" if group_id else ""
            params: dict[str, Any] = {}
            if group_id:
                params["group_id"] = group_id

            async with graphiti.driver.session() as session:
                # 孤立節點（無任何 RELATES_TO 連結）
                result = await session.run(f"""
                    MATCH (n:Entity)
                    {group_filter}
                    WHERE NOT (n)-[:RELATES_TO]-()
                    RETURN n.uuid AS uuid, n.name AS name
                    LIMIT 50
                """, params)
                orphans = [{"uuid": r["uuid"], "name": r["name"] or ""} async for r in result]

                # 空 summary 節點
                empty_filter = ("WHERE n.group_id = $group_id AND" if group_id
                                else "WHERE")
                result = await session.run(f"""
                    MATCH (n:Entity)
                    {empty_filter} (n.summary IS NULL OR n.summary = '')
                    RETURN n.uuid AS uuid, n.name AS name
                    LIMIT 50
                """, params)
                empty_summaries = [{"uuid": r["uuid"], "name": r["name"] or ""} async for r in result]

                # 重複名稱
                result = await session.run(f"""
                    MATCH (n:Entity)
                    {group_filter}
                    WITH toLower(n.name) AS lower_name, collect(n.uuid) AS uuids, count(n) AS cnt
                    WHERE cnt > 1
                    RETURN lower_name AS name, cnt AS count, uuids[0..5] AS sample_uuids
                    ORDER BY cnt DESC
                    LIMIT 20
                """, params)
                duplicates = [
                    {"name": r["name"], "count": r["count"], "sample_uuids": r["sample_uuids"]}
                    async for r in result
                ]

                # 總節點數（用於前端百分比計算）
                result = await session.run(f"""
                    MATCH (n:Entity)
                    {group_filter}
                    RETURN count(n) AS total
                """, params)
                total_rec = await result.single()
                total_nodes = total_rec["total"] if total_rec else 0

            return JSONResponse({
                "orphan_nodes": {"count": len(orphans), "items": orphans},
                "empty_summaries": {"count": len(empty_summaries), "items": empty_summaries},
                "duplicate_names": {"count": len(duplicates), "items": duplicates},
                "total_nodes": total_nodes,
            })
        except Exception as e:
            logger.error(f"API analytics quality error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    async def api_graph_subgraph(request: Request) -> JSONResponse:
        """取得以某節點為中心的子圖（用於 D3 視覺化）。"""
        try:
            graphiti = await get_graphiti_fn()
            uuid = request.query_params.get("uuid", "").strip()
            if not uuid:
                return JSONResponse({"error": "缺少參數 uuid"}, status_code=400)

            depth = min(int(request.query_params.get("depth", "2")), 3)
            limit = min(int(request.query_params.get("limit", "50")), 100)

            async with graphiti.driver.session() as session:
                # 取得子圖節點
                result = await session.run("""
                    MATCH p=(start:Entity {uuid: $uuid})-[:RELATES_TO*0..""" + str(depth) + """]->(n:Entity)
                    WITH DISTINCT n
                    LIMIT $limit
                    RETURN n.uuid AS uuid, n.name AS name, n.group_id AS group_id
                    UNION
                    MATCH p=(n:Entity)-[:RELATES_TO*0..""" + str(depth) + """]->(start:Entity {uuid: $uuid})
                    WITH DISTINCT n
                    LIMIT $limit
                    RETURN n.uuid AS uuid, n.name AS name, n.group_id AS group_id
                """, {"uuid": uuid, "limit": limit})

                nodes_map = {}
                async for r in result:
                    if r["uuid"] not in nodes_map:
                        nodes_map[r["uuid"]] = {
                            "uuid": r["uuid"],
                            "name": r["name"] or "",
                            "group_id": r["group_id"] or "",
                        }

                if not nodes_map:
                    return JSONResponse({"nodes": [], "edges": [], "center": uuid})

                node_uuids = list(nodes_map.keys())

                # 取得這些節點之間的邊
                result = await session.run("""
                    MATCH (s:Entity)-[r:RELATES_TO]->(t:Entity)
                    WHERE s.uuid IN $uuids AND t.uuid IN $uuids
                    RETURN r.uuid AS uuid, r.name AS name, r.fact AS fact,
                           s.uuid AS source, t.uuid AS target
                """, {"uuids": node_uuids})

                edges = []
                async for r in result:
                    edges.append({
                        "uuid": r["uuid"],
                        "name": r["name"] or "",
                        "fact": (r["fact"] or "")[:200],
                        "source": r["source"],
                        "target": r["target"],
                    })

            return JSONResponse({
                "nodes": list(nodes_map.values()),
                "edges": edges,
                "center": uuid,
            })
        except Exception as e:
            logger.error(f"API graph subgraph error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    async def api_ask(request: Request) -> JSONResponse:
        """AI 問答測試：並行搜尋 nodes + facts，組合為上下文。"""
        try:
            client_ip = request.client.host if request.client else "unknown"
            if not _search_limiter.is_allowed(client_ip):
                return JSONResponse(
                    {"error": "搜尋請求過於頻繁，請稍後再試"}, status_code=429
                )

            q = request.query_params.get("q", "").strip()
            if not q:
                return JSONResponse({"error": "缺少搜尋參數 q"}, status_code=400)

            group_ids_str = request.query_params.get("group_ids", "")
            group_ids = [g.strip() for g in group_ids_str.split(",") if g.strip()] if group_ids_str else []

            from graphiti_core.search.search_config_recipes import NODE_HYBRID_SEARCH_RRF
            from graphiti_core.search.search_filters import SearchFilters

            graphiti = await get_graphiti_fn()
            t0 = time.monotonic()

            # 並行搜尋 nodes 和 facts
            node_config = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
            node_config.limit = 10

            async def search_nodes():
                return await asyncio.wait_for(
                    graphiti.search_(
                        query=q, config=node_config,
                        group_ids=group_ids, search_filter=SearchFilters(),
                    ),
                    timeout=SEARCH_TIMEOUT,
                )

            async def search_facts():
                return await asyncio.wait_for(
                    graphiti.search(query=q, group_ids=group_ids, num_results=10),
                    timeout=SEARCH_TIMEOUT,
                )

            node_results, fact_results = await asyncio.gather(
                search_nodes(), search_facts(), return_exceptions=True,
            )

            duration = round(time.monotonic() - t0, 2)

            nodes = []
            if not isinstance(node_results, Exception):
                for n in (node_results.nodes or []):
                    nodes.append({
                        "uuid": str(getattr(n, "uuid", "")),
                        "name": getattr(n, "name", ""),
                        "summary": (getattr(n, "summary", "") or "")[:300],
                        "group_id": getattr(n, "group_id", ""),
                    })

            facts = []
            if not isinstance(fact_results, Exception):
                for e in fact_results:
                    facts.append({
                        "uuid": str(getattr(e, "uuid", "")),
                        "name": getattr(e, "name", ""),
                        "fact": (getattr(e, "fact", "") or "")[:300],
                        "source_name": getattr(e, "source_node_name", "") or "",
                        "target_name": getattr(e, "target_node_name", "") or "",
                    })

            # 組合 AI 上下文
            context_parts = []
            if nodes:
                context_parts.append("## 相關實體\n")
                for n in nodes:
                    context_parts.append(f"- **{n['name']}**: {n['summary']}")
            if facts:
                context_parts.append("\n## 相關事實\n")
                for f in facts:
                    context_parts.append(f"- {f['source_name']} → {f['target_name']}: {f['fact']}")

            context = "\n".join(context_parts) if context_parts else "（未找到相關知識）"

            return JSONResponse({
                "query": q,
                "context": context,
                "nodes": nodes,
                "facts": facts,
                "duration": duration,
                "errors": {
                    "nodes": str(node_results) if isinstance(node_results, Exception) else None,
                    "facts": str(fact_results) if isinstance(fact_results, Exception) else None,
                },
            })
        except Exception as e:
            logger.error(f"API ask error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    async def api_add_memory(request: Request) -> JSONResponse:
        """透過 Web UI 新增記憶。"""
        try:
            body = await request.json()
            name = body.get("name", "").strip()
            content = body.get("content", "").strip()
            group_id = body.get("group_id", "").strip()
            source = body.get("source", "text")

            if not name or not content:
                return JSONResponse(
                    {"error": "名稱和內容為必填"}, status_code=400
                )

            from graphiti_core.nodes import EpisodeType

            graphiti = await get_graphiti_fn()
            try:
                episode_type = EpisodeType[source.lower()]
            except (KeyError, AttributeError):
                episode_type = EpisodeType.text

            await graphiti.add_episode(
                name=name,
                episode_body=content,
                source_description="Web UI",
                source=episode_type,
                group_id=group_id or "default",
                reference_time=datetime.now(timezone.utc),
            )
            return JSONResponse(
                {"success": True, "message": f"記憶 '{name}' 已成功添加"}
            )
        except Exception as e:
            logger.error(f"API add memory error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    # ------------------------------------------------------------------
    # 批量添加 API（F1）
    # ------------------------------------------------------------------

    async def api_add_bulk(request: Request) -> JSONResponse:
        """透過 Web API 批量添加記憶。"""
        try:
            body = await request.json()
            episodes = body.get("episodes", [])
            group_id = body.get("group_id", "default")

            if not episodes:
                return JSONResponse({"error": "episodes 列表不能為空"}, status_code=400)

            for i, ep in enumerate(episodes):
                if not isinstance(ep, dict) or "name" not in ep or "content" not in ep:
                    return JSONResponse(
                        {"error": f"第 {i+1} 個 episode 格式錯誤"},
                        status_code=400,
                    )

            from graphiti_core.utils.bulk_utils import RawEpisode
            from graphiti_core.nodes import EpisodeType

            graphiti = await get_graphiti_fn()
            now = datetime.now(timezone.utc)

            raw_episodes = [
                RawEpisode(
                    name=ep["name"],
                    content=ep["content"],
                    source_description="Web UI Bulk",
                    source=EpisodeType.text,
                    reference_time=now,
                )
                for ep in episodes
            ]

            await graphiti.add_episode_bulk(
                bulk_episodes=raw_episodes,
                group_id=group_id,
            )

            return JSONResponse({
                "success": True,
                "message": f"成功批量添加 {len(episodes)} 條記憶",
                "count": len(episodes),
            })
        except Exception as e:
            logger.error(f"API add bulk error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    # ------------------------------------------------------------------
    # 三元組添加 API（F2）
    # ------------------------------------------------------------------

    async def api_add_triplet(request: Request) -> JSONResponse:
        """透過 Web API 添加三元組。"""
        try:
            body = await request.json()
            source_name = body.get("source_name", "").strip()
            relation_name = body.get("relation_name", "").strip()
            target_name = body.get("target_name", "").strip()
            fact = body.get("fact", "").strip()
            group_id = body.get("group_id", "default")

            if not all([source_name, relation_name, target_name, fact]):
                return JSONResponse(
                    {"error": "source_name, relation_name, target_name, fact 為必填"},
                    status_code=400,
                )

            from graphiti_core.nodes import EntityNode
            from graphiti_core.edges import EntityEdge

            graphiti = await get_graphiti_fn()
            now = datetime.now(timezone.utc)

            source_node = EntityNode(
                name=source_name, group_id=group_id,
                labels=body.get("source_labels", []), created_at=now,
            )
            target_node = EntityNode(
                name=target_name, group_id=group_id,
                labels=body.get("target_labels", []), created_at=now,
            )
            edge = EntityEdge(
                name=relation_name, group_id=group_id,
                source_node_uuid=source_node.uuid,
                target_node_uuid=target_node.uuid,
                fact=fact, created_at=now, episodes=[],
            )

            await graphiti.add_triplet(
                source_node=source_node, edge=edge, target_node=target_node,
            )

            return JSONResponse({
                "success": True,
                "message": f"三元組已添加: {source_name} --[{relation_name}]--> {target_name}",
                "source_uuid": source_node.uuid,
                "target_uuid": target_node.uuid,
                "edge_uuid": edge.uuid,
            })
        except Exception as e:
            logger.error(f"API add triplet error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    # ------------------------------------------------------------------
    # 社群 API（F3）
    # ------------------------------------------------------------------

    async def api_communities(request: Request) -> JSONResponse:
        """瀏覽社群節點。"""
        try:
            graphiti = await get_graphiti_fn()
            group_id = request.query_params.get("group_id", "")
            page = int(request.query_params.get("page", 1))
            limit = min(int(request.query_params.get("limit", 20)), 100)
            skip = (page - 1) * limit

            group_clause = "WHERE n.group_id = $group_id" if group_id else ""
            params = {"skip": skip, "limit": limit}
            if group_id:
                params["group_id"] = group_id

            async with graphiti.driver.session() as session:
                # 計數
                count_q = f"MATCH (n:Community) {group_clause} RETURN count(n) AS total"
                result = await session.run(count_q, params)
                records = [r async for r in result]
                total = records[0]["total"] if records else 0

                # 分頁查詢
                query = f"""
                MATCH (n:Community) {group_clause}
                RETURN n.uuid AS uuid, n.name AS name, n.summary AS summary,
                       n.group_id AS group_id, n.created_at AS created_at
                ORDER BY n.created_at DESC
                SKIP $skip LIMIT $limit
                """
                result = await session.run(query, params)
                communities = []
                async for record in result:
                    communities.append({
                        "uuid": record["uuid"],
                        "name": record["name"],
                        "summary": (record["summary"] or "")[:300],
                        "group_id": record["group_id"],
                        "created_at": format_timestamp(record["created_at"]),
                    })

            pages = max(1, (total + limit - 1) // limit)
            return JSONResponse({
                "communities": communities,
                "total": total,
                "page": page,
                "pages": pages,
            })
        except Exception as e:
            logger.error(f"API communities error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    async def api_build_communities(request: Request) -> JSONResponse:
        """觸發社群建構。"""
        try:
            body = await request.json()
            group_ids = body.get("group_ids")

            graphiti = await get_graphiti_fn()
            community_nodes, community_edges = await graphiti.build_communities(
                group_ids=group_ids,
            )

            return JSONResponse({
                "success": True,
                "message": f"社群建構完成",
                "community_nodes": len(community_nodes),
                "community_edges": len(community_edges),
            })
        except Exception as e:
            logger.error(f"API build communities error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    # ------------------------------------------------------------------
    # 進階搜尋 API（F4）
    # ------------------------------------------------------------------

    async def api_advanced_search(request: Request) -> JSONResponse:
        """進階搜尋（支援搜尋策略選擇）。"""
        try:
            q = request.query_params.get("q", "").strip()
            if not q:
                return JSONResponse({"error": "缺少查詢參數 q"}, status_code=400)

            recipe = request.query_params.get("recipe", "combined_cross_encoder")
            limit_val = min(int(request.query_params.get("limit", 10)), 50)
            group_ids_str = request.query_params.get("group_ids", "")
            group_ids = [g.strip() for g in group_ids_str.split(",") if g.strip()] if group_ids_str else []

            from graphiti_core.search.search_config_recipes import (
                COMBINED_HYBRID_SEARCH_CROSS_ENCODER,
            )

            # 動態載入配方
            import graphiti_mcp_server as server
            recipes = getattr(server, "SEARCH_RECIPES", {})
            if recipe not in recipes:
                return JSONResponse({
                    "error": f"未知的搜尋策略: {recipe}",
                    "available": list(recipes.keys()),
                }, status_code=400)

            search_config = recipes[recipe].model_copy(deep=True)
            search_config.limit = limit_val

            graphiti = await get_graphiti_fn()
            results = await asyncio.wait_for(
                graphiti.search_(
                    query=q, config=search_config, group_ids=group_ids,
                ),
                timeout=SEARCH_TIMEOUT,
            )

            # 簡化結果
            simplified = {
                "nodes": [
                    {
                        "name": getattr(n, "name", ""),
                        "uuid": str(getattr(n, "uuid", "")),
                        "summary": getattr(n, "summary", "")[:200],
                        "group_id": getattr(n, "group_id", ""),
                    }
                    for n in (results.nodes or [])
                ],
                "edges": [
                    {
                        "uuid": str(getattr(e, "uuid", "")),
                        "name": getattr(e, "name", ""),
                        "fact": getattr(e, "fact", ""),
                    }
                    for e in (results.edges or [])
                ],
                "communities": [
                    {
                        "uuid": str(getattr(c, "uuid", "")),
                        "name": getattr(c, "name", ""),
                        "summary": getattr(c, "summary", "")[:200],
                    }
                    for c in (results.communities or [])
                ],
            }

            return JSONResponse({
                "query": q,
                "recipe": recipe,
                "results": simplified,
            })
        except asyncio.TimeoutError:
            return JSONResponse({"error": "搜尋超時"}, status_code=504)
        except Exception as e:
            logger.error(f"API advanced search error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    # ------------------------------------------------------------------
    # 過時記憶分析 API（F10）
    # ------------------------------------------------------------------

    async def api_analytics_stale(request: Request) -> JSONResponse:
        """查詢過時記憶。"""
        try:
            from src.importance import get_stale_entities

            graphiti = await get_graphiti_fn()
            days = int(request.query_params.get("days", 30))
            min_count = int(request.query_params.get("min_count", 2))
            group_id = request.query_params.get("group_id", "")
            limit_val = min(int(request.query_params.get("limit", 50)), 200)

            result = await get_stale_entities(
                driver=graphiti.driver,
                days_threshold=days,
                min_access_count=min_count,
                group_id=group_id,
                limit=limit_val,
            )

            return JSONResponse(result)
        except Exception as e:
            logger.error(f"API stale analysis error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    async def api_analytics_cleanup(request: Request) -> JSONResponse:
        """清理過時記憶。"""
        try:
            from src.importance import cleanup_stale_entities

            body = await request.json()
            graphiti = await get_graphiti_fn()

            result = await cleanup_stale_entities(
                driver=graphiti.driver,
                days_threshold=body.get("days_threshold", 30),
                min_access_count=body.get("min_access_count", 2),
                group_id=body.get("group_id", ""),
                limit=min(body.get("limit", 50), 200),
                dry_run=body.get("dry_run", True),
            )

            return JSONResponse(result)
        except Exception as e:
            logger.error(f"API cleanup error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    # ------------------------------------------------------------------
    # 首頁（提供 SPA 入口）
    # ------------------------------------------------------------------

    async def index_page(request: Request) -> Response:
        """回傳 SPA 首頁。"""
        index_path = WEB_DIR / "index.html"
        if index_path.exists():
            return HTMLResponse(index_path.read_text(encoding="utf-8"))
        return HTMLResponse("<h1>Graphiti Web UI</h1><p>web/index.html 不存在</p>", status_code=404)

    # ------------------------------------------------------------------
    # 背景任務 API
    # ------------------------------------------------------------------

    async def api_memory_tasks(request: Request) -> JSONResponse:
        """列出所有背景記憶處理任務。"""
        try:
            from graphiti_mcp_server import _memory_tasks

            status_filter = request.query_params.get("status", "")
            tasks = list(_memory_tasks.values())
            if status_filter:
                tasks = [t for t in tasks if t.status == status_filter]

            # 按建立時間倒序
            tasks.sort(key=lambda t: t.created_at, reverse=True)

            # 分頁
            limit = min(int(request.query_params.get("limit", "20")), 100)
            offset = int(request.query_params.get("offset", "0"))
            paginated = tasks[offset : offset + limit]

            return JSONResponse({
                "tasks": [t.to_dict() for t in paginated],
                "total": len(tasks),
                "limit": limit,
                "offset": offset,
            })
        except Exception as e:
            logger.error(f"API memory tasks error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    async def api_memory_task_detail(request: Request) -> JSONResponse:
        """查詢單一背景任務狀態。"""
        try:
            from graphiti_mcp_server import _memory_tasks

            task_id = request.path_params["task_id"]
            task = _memory_tasks.get(task_id)
            if not task:
                return JSONResponse({"error": f"找不到任務 {task_id}"}, status_code=404)
            return JSONResponse(task.to_dict())
        except Exception as e:
            logger.error(f"API memory task detail error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    # ------------------------------------------------------------------
    # 組裝路由
    # ------------------------------------------------------------------

    routes: list = [
        # API 端點
        Route("/api/stats", api_stats, methods=["GET"]),
        Route("/api/groups", api_groups, methods=["GET"]),
        Route("/api/groups/stats", api_groups_stats, methods=["GET"]),
        Route("/api/nodes", api_nodes, methods=["GET"]),
        Route("/api/facts", api_facts, methods=["GET"]),
        Route("/api/episodes", api_episodes, methods=["GET"]),
        Route("/api/nodes/{uuid}", api_delete_node, methods=["DELETE"]),
        Route("/api/episodes/{uuid}", api_delete_episode, methods=["DELETE"]),
        Route("/api/facts/{uuid}", api_delete_fact, methods=["DELETE"]),
        Route("/api/groups/{group_id}", api_delete_group, methods=["DELETE"]),
        Route("/api/search/nodes", api_search_nodes, methods=["GET"]),
        Route("/api/search/facts", api_search_facts, methods=["GET"]),
        Route("/api/search/episodes", api_search_episodes, methods=["GET"]),
        Route("/api/nodes/{uuid}/relations", api_node_relations, methods=["GET"]),
        Route("/api/memory/add", api_add_memory, methods=["POST"]),
        Route("/api/memory/tasks", api_memory_tasks, methods=["GET"]),
        Route("/api/memory/tasks/{task_id}", api_memory_task_detail, methods=["GET"]),
        Route("/api/timeline", api_timeline, methods=["GET"]),
        Route("/api/analytics/top-nodes", api_analytics_top_nodes, methods=["GET"]),
        Route("/api/analytics/quality", api_analytics_quality, methods=["GET"]),
        Route("/api/graph/subgraph", api_graph_subgraph, methods=["GET"]),
        Route("/api/ask", api_ask, methods=["GET"]),
        # 新功能 API 端點
        Route("/api/memory/add-bulk", api_add_bulk, methods=["POST"]),
        Route("/api/memory/add-triplet", api_add_triplet, methods=["POST"]),
        Route("/api/communities", api_communities, methods=["GET"]),
        Route("/api/communities/build", api_build_communities, methods=["POST"]),
        Route("/api/search/advanced", api_advanced_search, methods=["GET"]),
        Route("/api/analytics/stale", api_analytics_stale, methods=["GET"]),
        Route("/api/analytics/cleanup", api_analytics_cleanup, methods=["POST"]),
    ]

    # 靜態文件（CSS/JS）
    if WEB_DIR.exists():
        routes.append(Mount("/static", app=StaticFiles(directory=str(WEB_DIR)), name="static"))

    # SPA 首頁（放最後，作為 fallback）
    routes.append(Route("/", index_page, methods=["GET"]))

    return routes
