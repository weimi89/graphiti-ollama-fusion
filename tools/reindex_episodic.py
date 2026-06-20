#!/usr/bin/env python3
"""
reindex_episodic.py — 補建 safe-mode 孤兒 EpisodicNode 的實體
=============================================================

safe mode 或完整模式降級（full mode 失敗 fallback）會寫出只有 EpisodicNode、
無 Entity/關係邊的記憶。這類記憶無法被 search_memory_nodes / search_memory_facts
命中（recall=0）。本工具掃描這類「孤兒」Episodic（無 MENTIONS→Entity 出邊），
重跑實體提取補建，救回靜默損失的可搜尋性。

用法：
    uv run python tools/reindex_episodic.py                 # dry-run，只報告
    uv run python tools/reindex_episodic.py --execute       # 實際重建實體
    uv run python tools/reindex_episodic.py --group-id foo  # 限定 group
    uv run python tools/reindex_episodic.py --exclude-group boundary_test,boundary_extreme  # 排除測試資料
    uv run python tools/reindex_episodic.py --limit 50      # 限制處理數量
    uv run python tools/reindex_episodic.py --execute --delete-orphans  # 重建後刪除舊孤兒
"""
import argparse
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


async def _find_orphans(driver, group_id, limit, exclude_groups=None):
    """查詢無 MENTIONS→Entity 出邊的 Episodic（safe-mode 殘留）。

    exclude_groups：排除的 group 清單（如 boundary 測試資料），避免對無意義
    內容重跑 LLM 提取、產生雜訊實體。
    """
    where = "WHERE NOT (e)-[:MENTIONS]->(:Entity)"
    params = {"limit": limit}
    if group_id:
        where += " AND e.group_id = $group_id"
        params["group_id"] = group_id
    if exclude_groups:
        where += " AND NOT e.group_id IN $exclude_groups"
        params["exclude_groups"] = exclude_groups
    query = f"""
    MATCH (e:Episodic)
    {where}
    RETURN e.uuid AS uuid, e.name AS name, e.content AS content,
           e.group_id AS group_id, e.source_description AS source_description
    ORDER BY e.created_at DESC
    LIMIT $limit
    """
    async with driver.session() as session:
        result = await session.run(query, params)
        return await result.data()


async def _delete_episode(driver, uuid):
    async with driver.session() as session:
        await session.run(
            "MATCH (e:Episodic {uuid: $uuid}) DETACH DELETE e", {"uuid": uuid}
        )


async def main():
    parser = argparse.ArgumentParser(
        description="補建 safe-mode 孤兒 EpisodicNode 的實體（提升可搜尋性）"
    )
    parser.add_argument("--execute", action="store_true", help="實際重建（預設 dry-run）")
    parser.add_argument("--group-id", default=None, help="限定 group_id")
    parser.add_argument(
        "--exclude-group", default=None,
        help="排除的 group（逗號分隔，如測試資料 boundary_test,boundary_extreme）",
    )
    parser.add_argument("--limit", type=int, default=1000, help="最多處理數量")
    parser.add_argument(
        "--delete-orphans", action="store_true", help="重建成功後刪除舊孤兒節點（避免重複）"
    )
    args = parser.parse_args()

    import graphiti_mcp_server as server
    from src.config import load_config

    server.app_config = load_config()
    graphiti = await server.initialize_graphiti()

    exclude_groups = (
        [g.strip() for g in args.exclude_group.split(",") if g.strip()]
        if args.exclude_group else None
    )
    orphans = await _find_orphans(graphiti.driver, args.group_id, args.limit, exclude_groups)
    print(f"找到 {len(orphans)} 個孤兒 Episodic（無 Entity，不可被向量搜尋）")
    if not orphans:
        return

    for o in orphans[:5]:
        print(f"  - [{o['group_id']}] {o['name']}: {(o['content'] or '')[:60]}")
    if len(orphans) > 5:
        print(f"  ... 還有 {len(orphans) - 5} 個")

    if not args.execute:
        print("\n[dry-run] 加 --execute 實際重建（--delete-orphans 可刪除舊孤兒）。")
        return

    from graphiti_core.nodes import EpisodeType

    ok, fail = 0, 0
    for o in orphans:
        content = (o.get("content") or "").strip()
        if not content:
            continue
        try:
            await graphiti.add_episode(
                name=o["name"] or "reindexed",
                episode_body=content,
                source_description=o.get("source_description") or "reindex_episodic",
                source=EpisodeType.text,
                group_id=o["group_id"],
                reference_time=datetime.now(timezone.utc),
            )
            if args.delete_orphans:
                await _delete_episode(graphiti.driver, o["uuid"])
            ok += 1
            print(f"  ✓ 重建: {o['name']}")
        except Exception as e:
            fail += 1
            print(f"  ✗ 失敗: {o['name']}: {e}")

    print(
        f"\n完成：成功 {ok}，失敗 {fail}"
        + ("，已刪除舊孤兒節點" if args.delete_orphans else "（舊孤兒節點保留，可加 --delete-orphans 清除）")
    )


if __name__ == "__main__":
    asyncio.run(main())
