#!/usr/bin/env python3
"""
批次重新處理知識圖譜記憶
========================

將現有 EpisodicNode 重新透過 graphiti.add_episode() 完整模式處理，
觸發實體提取（Entity）和關係建立（Fact），提升搜尋命中率。

背景：
    歷史上 use_safe_mode 預設為 True，導致大量記憶只建立了 EpisodicNode，
    沒有進行實體提取，因此無法被 search_memory_nodes / search_memory_facts 搜尋。

用法：
    # Dry run — 確認查詢數量
    uv run python tools/batch_reprocess.py --dry-run

    # 小範圍測試
    uv run python tools/batch_reprocess.py --group-id DouyinTikTokDownloadAPI --limit 5

    # 全量處理（支援斷點續跑）
    uv run python tools/batch_reprocess.py --resume

    # 跳過特定 group
    uv run python tools/batch_reprocess.py --skip-groups boundary_test,stress_test
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

# 確保專案根目錄在 sys.path 中
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from graphiti_core import Graphiti
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.nodes import EpisodeType

from src.config import GraphitiConfig, load_config
from src.ollama_embedder import OllamaEmbedder
from src.ollama_graphiti_client import OptimizedOllamaClient

# ============================================================================
# 常數
# ============================================================================

PROGRESS_FILE = PROJECT_ROOT / "logs" / "reprocess_progress.json"
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"

# ============================================================================
# 日誌設定
# ============================================================================

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("batch_reprocess")


# ============================================================================
# 進度管理
# ============================================================================


def load_progress() -> dict:
    """載入斷點進度檔案。"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "started_at": None,
        "last_updated": None,
        "completed": [],
        "failed": {},
        "stats": {"total": 0, "processed": 0, "failed": 0, "skipped": 0},
    }


def save_progress(progress: dict) -> None:
    """儲存進度到檔案。"""
    progress["last_updated"] = datetime.now(timezone.utc).isoformat()
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    # 排除內部追蹤欄位
    output = {k: v for k, v in progress.items() if not k.startswith("_")}
    if "stats" in output:
        output["stats"] = {k: v for k, v in output["stats"].items() if not k.startswith("_")}
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)


# ============================================================================
# Graphiti 初始化
# ============================================================================


def create_graphiti_instance(config: GraphitiConfig) -> Graphiti:
    """建立 Graphiti 實例，複用主伺服器的初始化邏輯。"""
    # LLM 客戶端
    llm_client = None
    try:
        llm_config = LLMConfig(
            base_url=config.ollama.base_url,
            model=config.ollama.model,
            temperature=config.ollama.temperature,
        )
        llm_client = OptimizedOllamaClient(config=llm_config)
        logger.info(f"LLM 客戶端初始化成功: {config.ollama.model}")
    except Exception as e:
        logger.warning(f"LLM 客戶端初始化失敗: {e}")

    # 嵌入器
    embedder = OllamaEmbedder(
        model=config.embedder.model,
        base_url=config.embedder.base_url,
        dimensions=config.embedder.dimensions,
    )
    logger.info(f"嵌入器初始化成功: {config.embedder.model}")

    # Graphiti 實例
    graphiti = Graphiti(
        uri=config.neo4j.uri,
        user=config.neo4j.user,
        password=config.neo4j.password,
        llm_client=llm_client,
        embedder=embedder,
        max_coroutines=3,
    )
    logger.info("Graphiti 實例建立成功")
    return graphiti


# ============================================================================
# Neo4j 查詢
# ============================================================================


async def query_episodic_nodes(
    graphiti: Graphiti,
    group_id: str | None = None,
    skip_groups: list[str] | None = None,
    limit: int | None = None,
) -> list[dict]:
    """從 Neo4j 查詢所有 EpisodicNode。"""
    conditions = []
    params = {}

    if group_id:
        conditions.append("e.group_id = $group_id")
        params["group_id"] = group_id

    if skip_groups:
        conditions.append("NOT e.group_id IN $skip_groups")
        params["skip_groups"] = skip_groups

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    limit_clause = f"LIMIT {limit}" if limit else ""

    query = f"""
    MATCH (e:Episodic)
    {where_clause}
    RETURN e.uuid AS uuid,
           e.name AS name,
           e.content AS content,
           e.group_id AS group_id,
           e.source_description AS source_description,
           e.source AS source,
           e.created_at AS created_at
    ORDER BY e.group_id, e.created_at
    {limit_clause}
    """

    records, _, _ = await graphiti.driver.execute_query(query, **params)

    episodes = []
    for record in records:
        episodes.append({
            "uuid": record["uuid"],
            "name": record["name"],
            "content": record["content"],
            "group_id": record["group_id"],
            "source_description": record["source_description"],
            "source": record["source"],
            "created_at": record["created_at"],
        })

    return episodes


# ============================================================================
# 核心重新處理
# ============================================================================


async def reprocess_episode(
    graphiti: Graphiti,
    episode: dict,
    index: int,
    total: int,
) -> bool:
    """重新處理單筆 EpisodicNode，觸發完整實體提取。"""
    uuid = episode["uuid"]
    name = episode["name"] or "unnamed"
    group_id = episode["group_id"] or "default"
    content = episode["content"] or ""

    if not content.strip():
        logger.warning(f"  [{index}/{total}] 跳過空內容: {uuid} ({name})")
        return False

    logger.info(
        f"  [{index}/{total}] 處理中: {name[:50]}... "
        f"(group={group_id}, {len(content)} chars)"
    )

    start = time.time()

    await graphiti.add_episode(
        name=name,
        episode_body=content,
        source_description=episode["source_description"] or "batch reprocessed",
        source=EpisodeType.text,
        group_id=group_id,
        reference_time=datetime.now(timezone.utc),
        uuid=uuid,
    )

    duration = time.time() - start
    logger.info(f"  [{index}/{total}] 完成: {name[:50]}... ({duration:.1f}s)")
    return True


# ============================================================================
# 主流程
# ============================================================================


async def main(args: argparse.Namespace) -> None:
    """主執行流程。"""
    # 載入配置
    config = load_config()
    logger.info("=" * 60)
    logger.info("批次重新處理知識圖譜記憶")
    logger.info("=" * 60)
    logger.info(f"Neo4j: {config.neo4j.uri}")
    logger.info(f"Ollama LLM: {config.ollama.model}")
    logger.info(f"Embedder: {config.embedder.model}")

    # 建立 Graphiti 實例
    graphiti = create_graphiti_instance(config)

    # 解析 skip-groups
    skip_groups = None
    if args.skip_groups:
        skip_groups = [g.strip() for g in args.skip_groups.split(",")]
        logger.info(f"跳過的群組: {skip_groups}")

    # 查詢 EpisodicNode
    logger.info("查詢 EpisodicNode...")
    episodes = await query_episodic_nodes(
        graphiti,
        group_id=args.group_id,
        skip_groups=skip_groups,
        limit=args.limit,
    )

    if not episodes:
        logger.info("沒有找到需要處理的 EpisodicNode")
        await graphiti.close()
        return

    # 按 group_id 統計
    group_counts: dict[str, int] = {}
    for ep in episodes:
        gid = ep["group_id"] or "default"
        group_counts[gid] = group_counts.get(gid, 0) + 1

    logger.info(f"找到 {len(episodes)} 筆 EpisodicNode，分布在 {len(group_counts)} 個群組:")
    for gid, count in sorted(group_counts.items(), key=lambda x: -x[1])[:20]:
        logger.info(f"  {gid}: {count} 筆")
    if len(group_counts) > 20:
        logger.info(f"  ... 還有 {len(group_counts) - 20} 個群組")

    # Dry run 模式
    if args.dry_run:
        logger.info("Dry run 完成，不進行實際處理")
        await graphiti.close()
        return

    # 載入或初始化進度
    if args.resume:
        progress = load_progress()
        logger.info(
            f"從斷點續跑: 已完成 {progress['stats']['processed']} 筆, "
            f"失敗 {progress['stats']['failed']} 筆"
        )
    else:
        progress = load_progress()
        progress["started_at"] = datetime.now(timezone.utc).isoformat()
        progress["completed"] = []
        progress["failed"] = {}
        progress["stats"] = {"total": len(episodes), "processed": 0, "failed": 0, "skipped": 0}

    completed_set = set(progress["completed"])
    total = len(episodes)
    processed = progress["stats"]["processed"]
    failed = progress["stats"]["failed"]
    skipped = progress["stats"]["skipped"]
    batch_start = time.time()

    logger.info(f"開始處理 {total} 筆記憶（延遲 {args.delay}s/筆）...")
    logger.info("-" * 60)

    for i, episode in enumerate(episodes, 1):
        uuid = episode["uuid"]

        # 跳過已完成的
        if uuid in completed_set:
            skipped += 1
            continue

        try:
            success = await reprocess_episode(graphiti, episode, i, total)
            if success:
                processed += 1
                progress["completed"].append(uuid)
            else:
                skipped += 1

        except Exception as e:
            failed += 1
            error_msg = str(e)[:200]
            progress["failed"][uuid] = error_msg
            logger.error(f"  [{i}/{total}] 失敗: {episode['name'][:50]}... - {error_msg}")

        # 更新統計
        progress["stats"] = {
            "total": total,
            "processed": processed,
            "failed": failed,
            "skipped": skipped,
        }

        # 每 10 筆或每筆失敗時儲存進度
        if i % 10 == 0 or failed > progress["stats"].get("_last_failed", -1):
            save_progress(progress)
            progress["stats"]["_last_failed"] = failed

            # 顯示進度摘要
            elapsed = time.time() - batch_start
            done = processed + failed + skipped
            remaining = total - done
            if processed > 0:
                avg_time = elapsed / (processed + failed)
                eta_seconds = remaining * avg_time
                eta_min = eta_seconds / 60
                logger.info(
                    f"  進度: {done}/{total} ({done*100//total}%) | "
                    f"成功: {processed} | 失敗: {failed} | 跳過: {skipped} | "
                    f"預計剩餘: {eta_min:.1f} 分鐘"
                )

        # 延遲以避免 Ollama 過載
        if i < total:
            await asyncio.sleep(args.delay)

    # 最終儲存
    save_progress(progress)

    # 輸出摘要
    elapsed = time.time() - batch_start
    logger.info("-" * 60)
    logger.info("處理完成！")
    logger.info(f"  總計: {total} 筆")
    logger.info(f"  成功: {processed} 筆")
    logger.info(f"  失敗: {failed} 筆")
    logger.info(f"  跳過: {skipped} 筆")
    logger.info(f"  耗時: {elapsed/60:.1f} 分鐘")
    logger.info(f"  進度檔: {PROGRESS_FILE}")

    if failed > 0:
        logger.warning(f"有 {failed} 筆處理失敗，詳見進度檔案")

    await graphiti.close()


# ============================================================================
# CLI 入口
# ============================================================================


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="批次重新處理知識圖譜記憶，觸發實體提取",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  %(prog)s --dry-run                              # 查看數量，不處理
  %(prog)s --group-id MyProject --limit 5         # 小範圍測試
  %(prog)s --resume                               # 從上次中斷處繼續
  %(prog)s --skip-groups test1,test2 --delay 5    # 跳過測試群組
        """,
    )
    parser.add_argument(
        "--group-id",
        help="只處理指定的 group_id",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="最多處理 n 筆",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=3.0,
        help="每筆間隔秒數（預設 3）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只查詢不處理，顯示將要處理的數量",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="從上次中斷處繼續（讀取進度檔案）",
    )
    parser.add_argument(
        "--skip-groups",
        help="跳過指定的 group_id（逗號分隔）",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(args))
