#!/usr/bin/env python3
"""
graph_maintenance.py — 知識圖譜整合維護
=======================================

統合知識圖譜的健康檢查與維護動作，可手動或排程（cron / pm2）執行：

  --report（預設）   偵測並報告：重複實體、孤兒 Episodic、缺去重嵌入的 Episodic
  --merge-duplicates 合併同 group+name 的重複 Entity（dry-run 預設，--execute 實際合併）
  --group-id X       限定 group
  --execute          對破壞性動作實際執行（否則只報告）

其他維護有專屬工具：
  - 孤兒 Episodic 補建：tools/reindex_episodic.py
  - 去重嵌入回填：    tools/backfill_episode_embeddings.py
  - 社群建構：        MCP build_communities / Web /api/communities/build
  - 過時記憶清理：    MCP cleanup_stale_memories

無 APOC 環境下，實體合併以手動 Cypher 重定向關係（RELATES_TO 出入邊 + MENTIONS），
更新 EntityEdge 的 source/target_node_uuid 屬性，並排除 self-loop，最後刪除重複節點。
建議在 --execute 前先用 tools/backup_embeddings.py 或 Neo4j dump 備份。
"""
import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


async def _report(graphiti, group_id):
    gfilter = " AND n.group_id = $gid" if group_id else ""
    efilter = " AND e.group_id = $gid" if group_id else ""
    params = {"gid": group_id} if group_id else {}
    async with graphiti.driver.session() as s:
        dup = (await (await s.run(
            f"MATCH (n:Entity) WHERE true{gfilter} "
            "WITH n.group_id AS g, n.name AS nm, count(*) AS c "
            "WHERE c > 1 RETURN count(*) AS groups, sum(c-1) AS extra", params
        )).data())[0]
        orphan = (await (await s.run(
            f"MATCH (e:Episodic) WHERE NOT (e)-[:MENTIONS]->(:Entity){efilter} "
            "RETURN count(e) AS c", params
        )).data())[0]
        no_emb = (await (await s.run(
            f"MATCH (e:Episodic) WHERE e.embedding IS NULL AND e.content IS NOT NULL{efilter} "
            "RETURN count(e) AS c", params
        )).data())[0]

    print("=== 知識圖譜健康報告 ===")
    print(f"  重複實體群組: {dup['groups'] or 0}（可合併冗餘節點 {dup['extra'] or 0}）"
          f" → graph_maintenance.py --merge-duplicates")
    print(f"  孤兒 Episodic（無 Entity，不可搜尋）: {orphan['c']}"
          f" → tools/reindex_episodic.py --execute")
    print(f"  缺去重嵌入的 Episodic: {no_emb['c']}"
          f" → tools/backfill_episode_embeddings.py")


async def _find_duplicate_groups(graphiti, group_id):
    gfilter = " AND n.group_id = $gid" if group_id else ""
    params = {"gid": group_id} if group_id else {}
    query = (
        f"MATCH (n:Entity) WHERE true{gfilter} "
        "WITH n.group_id AS gid, n.name AS name, "
        "collect({uuid: n.uuid, created: toString(n.created_at)}) AS items, count(*) AS c "
        "WHERE c > 1 RETURN gid, name, items"
    )
    async with graphiti.driver.session() as s:
        rows = await (await s.run(query, params)).data()
    groups = []
    for row in rows:
        # 保留最早建立者為 canonical
        items = sorted(row["items"], key=lambda x: x["created"] or "")
        keep = items[0]["uuid"]
        dups = [it["uuid"] for it in items[1:]]
        groups.append((row["gid"], row["name"], keep, dups))
    return groups


async def _merge_one(session, keep, dup):
    # 出邊：dup -[r]-> b（排除指向 keep 的 self-loop）
    await session.run(
        "MATCH (dup:Entity {uuid:$dup})-[r:RELATES_TO]->(b), (keep:Entity {uuid:$keep}) "
        "WHERE b.uuid <> $keep "
        "CREATE (keep)-[nr:RELATES_TO]->(b) SET nr = properties(r), nr.source_node_uuid = $keep "
        "DELETE r",
        {"dup": dup, "keep": keep},
    )
    # 入邊：a -[r]-> dup（排除來自 keep 的 self-loop）
    await session.run(
        "MATCH (a)-[r:RELATES_TO]->(dup:Entity {uuid:$dup}), (keep:Entity {uuid:$keep}) "
        "WHERE a.uuid <> $keep "
        "CREATE (a)-[nr:RELATES_TO]->(keep) SET nr = properties(r), nr.target_node_uuid = $keep "
        "DELETE r",
        {"dup": dup, "keep": keep},
    )
    # MENTIONS：ep -> dup 改為 ep -> keep（MERGE 去重）
    await session.run(
        "MATCH (ep)-[r:MENTIONS]->(dup:Entity {uuid:$dup}), (keep:Entity {uuid:$keep}) "
        "MERGE (ep)-[:MENTIONS]->(keep) DELETE r",
        {"dup": dup, "keep": keep},
    )
    # 刪除重複節點
    await session.run("MATCH (dup:Entity {uuid:$dup}) DETACH DELETE dup", {"dup": dup})


async def _merge_duplicates(graphiti, group_id, execute):
    groups = await _find_duplicate_groups(graphiti, group_id)
    total_dups = sum(len(d) for _, _, _, d in groups)
    print(f"重複實體群組: {len(groups)}，可合併冗餘節點: {total_dups}")
    for gid, name, keep, dups in groups[:10]:
        print(f"  [{gid}] '{name}': 保留 1 + 合併 {len(dups)}")
    if len(groups) > 10:
        print(f"  ... 還有 {len(groups) - 10} 群組")

    if not execute:
        print("\n[dry-run] 加 --execute 實際合併（建議先備份 Neo4j）。")
        return

    merged = 0
    async with graphiti.driver.session() as s:
        for gid, name, keep, dups in groups:
            for dup in dups:
                try:
                    await _merge_one(s, keep, dup)
                    merged += 1
                except Exception as e:
                    print(f"  ✗ 合併失敗 [{gid}] '{name}' {dup}: {e}")
    print(f"\n完成: 合併 {merged} 個重複節點到各自 canonical")


async def main():
    parser = argparse.ArgumentParser(description="知識圖譜整合維護")
    parser.add_argument("--report", action="store_true", help="健康報告（預設動作）")
    parser.add_argument("--merge-duplicates", action="store_true", help="合併重複實體")
    parser.add_argument("--group-id", default=None, help="限定 group")
    parser.add_argument("--execute", action="store_true", help="實際執行破壞性動作")
    args = parser.parse_args()

    import graphiti_mcp_server as server
    from src.config import load_config

    server.app_config = load_config()
    graphiti = await server.initialize_graphiti()

    try:
        if args.merge_duplicates:
            await _merge_duplicates(graphiti, args.group_id, args.execute)
        else:
            await _report(graphiti, args.group_id)
    finally:
        sess = getattr(getattr(graphiti, "embedder", None), "_session", None)
        if sess and not sess.closed:
            await sess.close()


if __name__ == "__main__":
    asyncio.run(main())
