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
                        "created_at": str(r["created_at"]) if r["created_at"] else "",
                        "labels": [l for l in (r["labels"] or []) if l not in ("Entity", "__Entity__")],
                    })

            return JSONResponse({
                "nodes": nodes,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": max(1, (total + limit - 1) // limit),
            })
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
                        "created_at": str(r["created_at"]) if r["created_at"] else "",
                        "source_name": r["source_name"] or "",
                        "target_name": r["target_name"] or "",
                        "source_uuid": r["source_uuid"] or "",
                        "target_uuid": r["target_uuid"] or "",
                    })

            return JSONResponse({
                "facts": facts,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": max(1, (total + limit - 1) // limit),
            })
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
                        "created_at": str(r["created_at"]) if r["created_at"] else "",
                        "source_description": r["source_description"] or "",
                    })

            return JSONResponse({
                "episodes": episodes,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": max(1, (total + limit - 1) // limit),
            })
        except Exception as e:
            logger.error(f"API episodes error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    async def api_delete_episode(request: Request) -> JSONResponse:
        """刪除記憶片段（事務性：連帶清理關聯邊）。"""
        try:
            uuid = request.path_params["uuid"]
            graphiti = await get_graphiti_fn()
            # 使用 Cypher 事務確保一致性：同時刪除節點和關聯邊
            query = """
            MATCH (e:Episodic {uuid: $uuid})
            OPTIONAL MATCH (e)-[r]-()
            DELETE r, e
            RETURN count(e) AS deleted
            """
            records, _, _ = await graphiti.driver.execute_query(query, parameters_={"uuid": uuid})
            deleted = records[0]["deleted"] if records else 0
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
            query = """
            MATCH ()-[r:RELATES_TO {uuid: $uuid}]-()
            DELETE r
            RETURN count(r) AS deleted
            """
            records, _, _ = await graphiti.driver.execute_query(query, parameters_={"uuid": uuid})
            deleted = records[0]["deleted"] if records else 0
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
            query = """
            MATCH (n:Entity {uuid: $uuid})
            OPTIONAL MATCH (n)-[r]-()
            DELETE r, n
            RETURN count(n) AS deleted
            """
            records, _, _ = await graphiti.driver.execute_query(query, parameters_={"uuid": uuid})
            deleted = records[0]["deleted"] if records else 0
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

            results = await asyncio.wait_for(
                graphiti.search_(
                    query=q,
                    config=search_config,
                    group_ids=group_ids,
                    search_filter=SearchFilters(),
                ),
                timeout=SEARCH_TIMEOUT,
            )

            nodes = []
            for n in (results.nodes or []):
                nodes.append({
                    "uuid": str(getattr(n, "uuid", "")),
                    "name": getattr(n, "name", ""),
                    "summary": (getattr(n, "summary", "") or "")[:200],
                    "group_id": getattr(n, "group_id", ""),
                    "created_at": str(getattr(n, "created_at", "")),
                    "labels": getattr(n, "labels", []),
                })

            return JSONResponse({"nodes": nodes, "query": q, "total": len(nodes)})
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
            edges = await asyncio.wait_for(
                graphiti.search(
                    query=q,
                    group_ids=group_ids,
                    num_results=limit,
                ),
                timeout=SEARCH_TIMEOUT,
            )

            facts = []
            for e in edges:
                facts.append({
                    "uuid": str(getattr(e, "uuid", "")),
                    "name": getattr(e, "name", ""),
                    "fact": (getattr(e, "fact", "") or "")[:300],
                    "group_id": getattr(e, "group_id", ""),
                    "created_at": str(getattr(e, "created_at", "")),
                    "source_node_uuid": str(getattr(e, "source_node_uuid", "")),
                    "target_node_uuid": str(getattr(e, "target_node_uuid", "")),
                })

            return JSONResponse({"facts": facts, "query": q, "total": len(facts)})
        except asyncio.TimeoutError:
            logger.warning(f"搜尋事實超時 ({SEARCH_TIMEOUT}s): {q}")
            return JSONResponse({"error": "搜尋超時，請縮小查詢範圍"}, status_code=504)
        except Exception as e:
            logger.error(f"API search facts error: {e}")
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
    # 組裝路由
    # ------------------------------------------------------------------

    routes: list = [
        # API 端點
        Route("/api/stats", api_stats, methods=["GET"]),
        Route("/api/groups", api_groups, methods=["GET"]),
        Route("/api/nodes", api_nodes, methods=["GET"]),
        Route("/api/facts", api_facts, methods=["GET"]),
        Route("/api/episodes", api_episodes, methods=["GET"]),
        Route("/api/nodes/{uuid}", api_delete_node, methods=["DELETE"]),
        Route("/api/episodes/{uuid}", api_delete_episode, methods=["DELETE"]),
        Route("/api/facts/{uuid}", api_delete_fact, methods=["DELETE"]),
        Route("/api/groups/{group_id}", api_delete_group, methods=["DELETE"]),
        Route("/api/search/nodes", api_search_nodes, methods=["GET"]),
        Route("/api/search/facts", api_search_facts, methods=["GET"]),
    ]

    # 靜態文件（CSS/JS）
    if WEB_DIR.exists():
        routes.append(Mount("/static", app=StaticFiles(directory=str(WEB_DIR)), name="static"))

    # SPA 首頁（放最後，作為 fallback）
    routes.append(Route("/", index_page, methods=["GET"]))

    return routes
