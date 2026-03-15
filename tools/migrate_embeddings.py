#!/usr/bin/env python3
"""
Embedding 模型遷移工具
======================

切換 embedding 模型後，將所有現有的 EntityNode、EntityEdge、CommunityNode
的向量重新生成，確保搜索品質一致。

特點：
    - 支援 dry-run 預覽
    - 斷點續跑（進度檔案）
    - 批量 embedding（利用 create_batch 並發）
    - 按 group_id 篩選
    - 自動偵測維度變化

用法：
    # 預覽：查看需要遷移的數量
    uv run python tools/migrate_embeddings.py --dry-run

    # 小範圍測試
    uv run python tools/migrate_embeddings.py --group-id myproject --batch-size 10

    # 全量遷移
    uv run python tools/migrate_embeddings.py

    # 從斷點繼續
    uv run python tools/migrate_embeddings.py --resume

    # 只遷移節點（跳過邊和社群）
    uv run python tools/migrate_embeddings.py --only nodes
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from src.config import load_config
from src.ollama_embedder import OllamaEmbedder

# ============================================================================
# 常數
# ============================================================================

PROGRESS_FILE = PROJECT_ROOT / "logs" / "migrate_embeddings_progress.json"
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
DEFAULT_BATCH_SIZE = 20

# ============================================================================
# 日誌
# ============================================================================

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("migrate_embeddings")


# ============================================================================
# 進度管理
# ============================================================================


def load_progress() -> dict:
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "started_at": None,
        "last_updated": None,
        "completed_nodes": [],
        "completed_edges": [],
        "completed_communities": [],
        "failed": {},
        "stats": {
            "nodes_total": 0, "nodes_done": 0,
            "edges_total": 0, "edges_done": 0,
            "communities_total": 0, "communities_done": 0,
            "failed": 0,
        },
    }


def save_progress(progress: dict) -> None:
    progress["last_updated"] = datetime.now(timezone.utc).isoformat()
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


# ============================================================================
# Neo4j 查詢
# ============================================================================


async def get_driver(config):
    """建立 Neo4j driver。"""
    from graphiti_core.driver.neo4j_driver import Neo4jDriver

    driver = Neo4jDriver(
        uri=config.neo4j.uri,
        user=config.neo4j.user,
        password=config.neo4j.password,
    )
    return driver


async def query_entity_nodes(driver, group_id=None) -> list[dict]:
    """查詢所有 EntityNode 的 uuid 和 name。"""
    where = "WHERE n.group_id = $group_id" if group_id else ""
    params = {"group_id": group_id} if group_id else {}
    query = f"""
    MATCH (n:Entity)
    {where}
    RETURN n.uuid AS uuid, n.name AS name, n.group_id AS group_id
    ORDER BY n.group_id, n.name
    """
    records, _, _ = await driver.execute_query(query, **params)
    return [{"uuid": r["uuid"], "name": r["name"], "group_id": r["group_id"]} for r in records]


async def query_entity_edges(driver, group_id=None) -> list[dict]:
    """查詢所有 EntityEdge 的 uuid 和 fact。"""
    where = "WHERE e.group_id = $group_id" if group_id else ""
    params = {"group_id": group_id} if group_id else {}
    query = f"""
    MATCH (s:Entity)-[e:RELATES_TO]->(t:Entity)
    {where}
    RETURN e.uuid AS uuid, e.fact AS fact, e.group_id AS group_id
    ORDER BY e.group_id
    """
    records, _, _ = await driver.execute_query(query, **params)
    return [{"uuid": r["uuid"], "fact": r["fact"], "group_id": r["group_id"]} for r in records]


async def query_community_nodes(driver, group_id=None) -> list[dict]:
    """查詢所有 CommunityNode 的 uuid 和 name。"""
    where = "WHERE c.group_id = $group_id" if group_id else ""
    params = {"group_id": group_id} if group_id else {}
    query = f"""
    MATCH (c:Community)
    {where}
    RETURN c.uuid AS uuid, c.name AS name, c.group_id AS group_id
    ORDER BY c.group_id, c.name
    """
    records, _, _ = await driver.execute_query(query, **params)
    return [{"uuid": r["uuid"], "name": r["name"], "group_id": r["group_id"]} for r in records]


async def update_node_embedding(driver, uuid: str, embedding: list[float]):
    """更新 EntityNode 的 name_embedding。"""
    query = """
    MATCH (n:Entity {uuid: $uuid})
    SET n.name_embedding = $embedding
    """
    await driver.execute_query(query, uuid=uuid, embedding=embedding)


async def update_edge_embedding(driver, uuid: str, embedding: list[float]):
    """更新 EntityEdge 的 fact_embedding。"""
    query = """
    MATCH (s:Entity)-[e:RELATES_TO {uuid: $uuid}]->(t:Entity)
    SET e.fact_embedding = $embedding
    """
    await driver.execute_query(query, uuid=uuid, embedding=embedding)


async def update_community_embedding(driver, uuid: str, embedding: list[float]):
    """更新 CommunityNode 的 name_embedding。"""
    query = """
    MATCH (c:Community {uuid: $uuid})
    SET c.name_embedding = $embedding
    """
    await driver.execute_query(query, uuid=uuid, embedding=embedding)


# ============================================================================
# 批量遷移核心
# ============================================================================


async def migrate_batch(
    driver,
    embedder: OllamaEmbedder,
    items: list[dict],
    text_field: str,
    update_fn,
    label: str,
    completed_set: set,
    progress: dict,
    completed_key: str,
    done_key: str,
) -> tuple[int, int]:
    """批量遷移一組 items 的 embedding。"""
    # 過濾已完成和無效項
    pending = [
        item for item in items
        if item["uuid"] not in completed_set and item.get(text_field)
    ]

    if not pending:
        logger.info(f"  {label}: 沒有需要遷移的項目")
        return 0, 0

    total = len(pending)
    done = 0
    failed = 0

    # 分批處理
    batch_size = DEFAULT_BATCH_SIZE
    for i in range(0, total, batch_size):
        batch = pending[i:i + batch_size]
        texts = [item[text_field].replace("\n", " ") for item in batch]

        try:
            # 批量 embedding
            embeddings = await embedder.create_batch(texts)

            # 逐一更新 Neo4j
            for item, embedding in zip(batch, embeddings):
                try:
                    await update_fn(driver, item["uuid"], embedding)
                    completed_set.add(item["uuid"])
                    progress[completed_key].append(item["uuid"])
                    done += 1
                except Exception as e:
                    failed += 1
                    progress["failed"][item["uuid"]] = f"{label}: {str(e)[:150]}"
                    logger.error(f"    更新失敗 {item['uuid']}: {e}")

        except Exception as e:
            # 整批 embedding 失敗，逐一重試
            logger.warning(f"    批量 embedding 失敗，逐一重試: {e}")
            for item in batch:
                try:
                    text = item[text_field].replace("\n", " ")
                    emb = await embedder.create(text)
                    await update_fn(driver, item["uuid"], emb)
                    completed_set.add(item["uuid"])
                    progress[completed_key].append(item["uuid"])
                    done += 1
                except Exception as e2:
                    failed += 1
                    progress["failed"][item["uuid"]] = f"{label}: {str(e2)[:150]}"

        # 更新進度
        progress["stats"][done_key] = done
        progress["stats"]["failed"] = sum(1 for _ in progress["failed"])

        processed = i + len(batch)
        logger.info(
            f"  {label}: {processed}/{total} "
            f"(成功: {done}, 失敗: {failed})"
        )

        # 每 5 批儲存一次進度
        if (i // batch_size) % 5 == 4:
            save_progress(progress)

    return done, failed


# ============================================================================
# 主流程
# ============================================================================


async def main(args: argparse.Namespace) -> None:
    config = load_config()

    logger.info("=" * 60)
    logger.info("Embedding 模型遷移工具")
    logger.info("=" * 60)
    logger.info(f"Embedding 模型: {config.embedder.model}")
    logger.info(f"向量維度: {config.embedder.dimensions}")
    logger.info(f"Neo4j: {config.neo4j.uri}")

    # 建立 embedder
    embedder = OllamaEmbedder(
        model=config.embedder.model,
        base_url=config.embedder.base_url,
        dimensions=config.embedder.dimensions,
    )

    # 測試 embedder
    logger.info("測試 embedding 模型連接...")
    test_ok = await embedder.test_connection()
    if not test_ok:
        logger.error(f"無法連接 embedding 模型 {config.embedder.model}，請確認 Ollama 已啟動並已安裝模型")
        return
    logger.info(f"Embedding 模型 {config.embedder.model} 連接正常")

    # 建立 driver
    driver = await get_driver(config)

    # 決定遷移範圍
    only = args.only  # "nodes", "edges", "communities", or None (all)

    # 查詢現有資料
    nodes, edges, communities = [], [], []

    if only is None or only == "nodes":
        nodes = await query_entity_nodes(driver, args.group_id)
    if only is None or only == "edges":
        edges = await query_entity_edges(driver, args.group_id)
    if only is None or only == "communities":
        communities = await query_community_nodes(driver, args.group_id)

    # 統計
    logger.info(f"\n遷移範圍:")
    if nodes:
        groups = {}
        for n in nodes:
            groups[n["group_id"]] = groups.get(n["group_id"], 0) + 1
        logger.info(f"  EntityNode: {len(nodes)} 個")
        for gid, cnt in sorted(groups.items(), key=lambda x: -x[1])[:10]:
            logger.info(f"    {gid}: {cnt}")
    if edges:
        logger.info(f"  EntityEdge: {len(edges)} 個")
    if communities:
        logger.info(f"  CommunityNode: {len(communities)} 個")

    total_items = len(nodes) + len(edges) + len(communities)
    if total_items == 0:
        logger.info("沒有需要遷移的資料")
        await driver.close()
        return

    # Dry run
    if args.dry_run:
        logger.info(f"\n[Dry Run] 共 {total_items} 個項目需要遷移")
        logger.info(f"  預估 embedding 請求: ~{total_items} 次")
        if embedder._session and not embedder._session.closed:
            await embedder._session.close()
        await driver.close()
        return

    # 載入進度
    if args.resume:
        progress = load_progress()
        logger.info(f"從斷點續跑")
    else:
        progress = load_progress()
        progress["started_at"] = datetime.now(timezone.utc).isoformat()
        progress["completed_nodes"] = []
        progress["completed_edges"] = []
        progress["completed_communities"] = []
        progress["failed"] = {}
        progress["stats"] = {
            "nodes_total": len(nodes),
            "nodes_done": 0,
            "edges_total": len(edges),
            "edges_done": 0,
            "communities_total": len(communities),
            "communities_done": 0,
            "failed": 0,
        }

    start_time = time.time()

    # 遷移 EntityNode
    if nodes:
        logger.info(f"\n--- 遷移 EntityNode ({len(nodes)} 個) ---")
        completed_set = set(progress["completed_nodes"])
        n_done, n_failed = await migrate_batch(
            driver, embedder, nodes, "name", update_node_embedding,
            "EntityNode", completed_set, progress,
            "completed_nodes", "nodes_done",
        )
        save_progress(progress)
        logger.info(f"  EntityNode 完成: 成功 {n_done}, 失敗 {n_failed}")

    # 遷移 EntityEdge
    if edges:
        logger.info(f"\n--- 遷移 EntityEdge ({len(edges)} 個) ---")
        completed_set = set(progress["completed_edges"])
        e_done, e_failed = await migrate_batch(
            driver, embedder, edges, "fact", update_edge_embedding,
            "EntityEdge", completed_set, progress,
            "completed_edges", "edges_done",
        )
        save_progress(progress)
        logger.info(f"  EntityEdge 完成: 成功 {e_done}, 失敗 {e_failed}")

    # 遷移 CommunityNode
    if communities:
        logger.info(f"\n--- 遷移 CommunityNode ({len(communities)} 個) ---")
        completed_set = set(progress["completed_communities"])
        c_done, c_failed = await migrate_batch(
            driver, embedder, communities, "name", update_community_embedding,
            "CommunityNode", completed_set, progress,
            "completed_communities", "communities_done",
        )
        save_progress(progress)
        logger.info(f"  CommunityNode 完成: 成功 {c_done}, 失敗 {c_failed}")

    # 最終摘要
    elapsed = time.time() - start_time
    stats = progress["stats"]
    total_done = stats["nodes_done"] + stats["edges_done"] + stats["communities_done"]
    total_failed = stats["failed"]

    logger.info("\n" + "=" * 60)
    logger.info("遷移完成！")
    logger.info(f"  Embedding 模型: {config.embedder.model}")
    logger.info(f"  向量維度: {config.embedder.dimensions}")
    logger.info(f"  EntityNode: {stats['nodes_done']}/{stats['nodes_total']}")
    logger.info(f"  EntityEdge: {stats['edges_done']}/{stats['edges_total']}")
    logger.info(f"  CommunityNode: {stats['communities_done']}/{stats['communities_total']}")
    logger.info(f"  總計: {total_done} 成功, {total_failed} 失敗")
    logger.info(f"  耗時: {elapsed:.1f}s ({elapsed/60:.1f} 分鐘)")
    logger.info(f"  進度檔: {PROGRESS_FILE}")

    if total_failed > 0:
        logger.warning(f"有 {total_failed} 個項目遷移失敗，可用 --resume 重試")

    if embedder._session and not embedder._session.closed:
        await embedder._session.close()
    await driver.close()


# ============================================================================
# CLI
# ============================================================================


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Embedding 模型遷移工具 — 切換模型後重新生成所有向量",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  %(prog)s --dry-run                        # 預覽需要遷移的數量
  %(prog)s --group-id myproject             # 只遷移指定 group
  %(prog)s --only nodes                     # 只遷移節點
  %(prog)s --resume                         # 從斷點繼續
  %(prog)s --batch-size 50                  # 加大批次（雲端模型適用）
        """,
    )
    parser.add_argument("--group-id", help="只遷移指定的 group_id")
    parser.add_argument("--dry-run", action="store_true", help="只預覽，不執行")
    parser.add_argument("--resume", action="store_true", help="從斷點繼續")
    parser.add_argument(
        "--only",
        choices=["nodes", "edges", "communities"],
        help="只遷移指定類型",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"每批 embedding 數量（預設 {DEFAULT_BATCH_SIZE}）",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    DEFAULT_BATCH_SIZE = args.batch_size
    asyncio.run(main(args))
