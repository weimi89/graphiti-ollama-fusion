"""
重要性評分與存取追蹤模組
========================

追蹤節點和邊的存取頻率，為搜尋結果提供重要性加權依據。
透過 Neo4j 自定義屬性 access_count 和 last_accessed 實現。
"""

import logging
from datetime import datetime, timezone
from typing import Any, List

from src.timezone_utils import format_timestamp

logger = logging.getLogger(__name__)


async def update_access_metadata(driver: Any, uuids: List[str]) -> None:
    """
    非同步更新節點/邊的存取中繼資料。

    為指定的 UUID 遞增 access_count 並更新 last_accessed 時戳。
    此函數設計為 fire-and-forget 使用，不應阻塞搜尋回傳。

    Args:
        driver: Neo4j driver 實例
        uuids: 要更新的節點/邊 UUID 列表
    """
    if not uuids:
        return

    try:
        now_iso = datetime.now(timezone.utc).isoformat()

        # 更新 Entity 節點
        node_query = """
        UNWIND $uuids AS uid
        MATCH (n:Entity {uuid: uid})
        SET n.access_count = COALESCE(n.access_count, 0) + 1,
            n.last_accessed = $now
        """

        # 更新 EntityEdge 關係
        edge_query = """
        UNWIND $uuids AS uid
        MATCH ()-[r:RELATES_TO {uuid: uid}]->()
        SET r.access_count = COALESCE(r.access_count, 0) + 1,
            r.last_accessed = $now
        """

        async with driver.session() as session:
            await session.run(node_query, {"uuids": uuids, "now": now_iso})
            await session.run(edge_query, {"uuids": uuids, "now": now_iso})

        logger.debug(f"已更新 {len(uuids)} 個項目的存取中繼資料")

    except Exception as e:
        logger.warning(f"更新存取中繼資料失敗（不影響搜尋結果）: {e}")


async def get_stale_entities(
    driver: Any,
    days_threshold: int = 30,
    min_access_count: int = 2,
    group_id: str = "",
    limit: int = 50,
) -> dict:
    """
    查詢過時的節點和邊（長時間未存取且存取次數低）。

    Args:
        driver: Neo4j driver 實例
        days_threshold: 超過此天數未存取的視為過時
        min_access_count: 存取次數低於此值的才列入
        group_id: 可選的分組篩選
        limit: 回傳上限

    Returns:
        dict: 包含 stale_nodes 和 stale_edges 的字典
    """
    try:
        cutoff = f"datetime() - duration('P{days_threshold}D')"

        # 查詢過時節點
        node_query = f"""
        MATCH (n:Entity)
        WHERE (n.access_count IS NULL OR n.access_count < $min_count)
          AND (n.last_accessed IS NULL OR datetime(n.last_accessed) < {cutoff})
          {'AND n.group_id = $group_id' if group_id else ''}
        RETURN n.uuid AS uuid, n.name AS name, n.group_id AS group_id,
               COALESCE(n.access_count, 0) AS access_count,
               n.last_accessed AS last_accessed,
               n.created_at AS created_at
        ORDER BY COALESCE(n.access_count, 0) ASC, n.created_at ASC
        LIMIT $limit
        """

        # 查詢過時邊
        edge_query = f"""
        MATCH (s:Entity)-[r:RELATES_TO]->(t:Entity)
        WHERE (r.access_count IS NULL OR r.access_count < $min_count)
          AND (r.last_accessed IS NULL OR datetime(r.last_accessed) < {cutoff})
          {'AND r.group_id = $group_id' if group_id else ''}
        RETURN r.uuid AS uuid, r.name AS name, r.fact AS fact,
               r.group_id AS group_id,
               s.name AS source_name, t.name AS target_name,
               COALESCE(r.access_count, 0) AS access_count,
               r.last_accessed AS last_accessed,
               r.created_at AS created_at
        ORDER BY COALESCE(r.access_count, 0) ASC, r.created_at ASC
        LIMIT $limit
        """

        params = {"min_count": min_access_count, "limit": limit}
        if group_id:
            params["group_id"] = group_id

        stale_nodes = []
        stale_edges = []

        async with driver.session() as session:
            result = await session.run(node_query, params)
            async for record in result:
                stale_nodes.append({
                    "uuid": record["uuid"],
                    "name": record["name"],
                    "group_id": record["group_id"],
                    "access_count": record["access_count"],
                    "last_accessed": record["last_accessed"],
                    "created_at": format_timestamp(record["created_at"]),
                })

            result = await session.run(edge_query, params)
            async for record in result:
                stale_edges.append({
                    "uuid": record["uuid"],
                    "name": record["name"],
                    "fact": record["fact"],
                    "group_id": record["group_id"],
                    "source_name": record["source_name"],
                    "target_name": record["target_name"],
                    "access_count": record["access_count"],
                    "last_accessed": record["last_accessed"],
                    "created_at": format_timestamp(record["created_at"]),
                })

        return {
            "stale_nodes": stale_nodes,
            "stale_edges": stale_edges,
            "total": len(stale_nodes) + len(stale_edges),
        }

    except Exception as e:
        logger.error(f"查詢過時記憶失敗: {e}")
        return {"stale_nodes": [], "stale_edges": [], "total": 0, "error": str(e)[:200]}


async def cleanup_stale_entities(
    driver: Any,
    days_threshold: int = 30,
    min_access_count: int = 2,
    group_id: str = "",
    limit: int = 50,
    dry_run: bool = True,
) -> dict:
    """
    清理過時的節點和邊。

    Args:
        driver: Neo4j driver 實例
        days_threshold: 超過此天數未存取的視為過時
        min_access_count: 存取次數低於此值的才清理
        group_id: 可選的分組篩選
        limit: 清理上限
        dry_run: True 時僅預覽不實際刪除

    Returns:
        dict: 清理結果
    """
    # 先查詢要清理的項目
    stale = await get_stale_entities(
        driver, days_threshold, min_access_count, group_id, limit
    )

    if dry_run:
        return {
            "mode": "dry_run",
            "would_delete_nodes": len(stale["stale_nodes"]),
            "would_delete_edges": len(stale["stale_edges"]),
            "stale_nodes": stale["stale_nodes"],
            "stale_edges": stale["stale_edges"],
            "message": "預覽模式 — 未實際刪除任何資料。設定 dry_run=False 以執行清理。",
        }

    # 實際刪除
    deleted_nodes = 0
    deleted_edges = 0

    try:
        async with driver.session() as session:
            # 刪除過時邊
            edge_uuids = [e["uuid"] for e in stale["stale_edges"]]
            if edge_uuids:
                result = await session.run(
                    "UNWIND $uuids AS uid "
                    "MATCH ()-[r:RELATES_TO {uuid: uid}]->() "
                    "DELETE r RETURN count(r) AS cnt",
                    {"uuids": edge_uuids},
                )
                records = [r async for r in result]
                deleted_edges = records[0]["cnt"] if records else 0

            # 刪除過時節點（只刪沒有任何關係的孤立節點）
            node_uuids = [n["uuid"] for n in stale["stale_nodes"]]
            if node_uuids:
                result = await session.run(
                    "UNWIND $uuids AS uid "
                    "MATCH (n:Entity {uuid: uid}) "
                    "WHERE NOT (n)--() "
                    "DELETE n RETURN count(n) AS cnt",
                    {"uuids": node_uuids},
                )
                records = [r async for r in result]
                deleted_nodes = records[0]["cnt"] if records else 0

        logger.info(f"清理完成: 刪除 {deleted_nodes} 個節點, {deleted_edges} 個邊")

        return {
            "mode": "execute",
            "deleted_nodes": deleted_nodes,
            "deleted_edges": deleted_edges,
            "message": f"已刪除 {deleted_nodes} 個過時節點和 {deleted_edges} 個過時邊",
        }

    except Exception as e:
        logger.error(f"清理過時記憶失敗: {e}")
        return {
            "mode": "execute",
            "deleted_nodes": deleted_nodes,
            "deleted_edges": deleted_edges,
            "error": str(e)[:200],
        }
