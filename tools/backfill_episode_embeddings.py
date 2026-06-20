#!/usr/bin/env python3
"""
backfill_episode_embeddings.py — 回填 Episodic content 嵌入（修復去重空轉）
==========================================================================

graphiti-core 的 add_episode 只儲存 Episodic 的 content 文本、不計算其嵌入，
導致 check_episode_similarity 查無可比對對象、記憶去重永遠空轉（從不擋重複）。

本工具為既有無 embedding 的 Episodic 補算 content 嵌入（與當前 embedder 維度一致），
讓去重比對有對象。新寫入的記憶已由 add_memory 流程自動補存，故本工具僅需執行一次。

用法：
    uv run python tools/backfill_episode_embeddings.py
    uv run python tools/backfill_episode_embeddings.py --group-id foo --batch-size 20
    uv run python tools/backfill_episode_embeddings.py --dry-run
"""
import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


async def main():
    parser = argparse.ArgumentParser(description="回填 Episodic content 嵌入（修復去重空轉）")
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--group-id", default=None, help="限定 group_id")
    parser.add_argument("--limit", type=int, default=100000)
    parser.add_argument("--dry-run", action="store_true", help="只報告數量，不寫入")
    args = parser.parse_args()

    import graphiti_mcp_server as server
    from src.config import load_config

    server.app_config = load_config()
    g = await server.initialize_graphiti()

    try:
        where = "WHERE e.embedding IS NULL AND e.content IS NOT NULL AND e.content <> ''"
        params = {"limit": args.limit}
        if args.group_id:
            where += " AND e.group_id = $group_id"
            params["group_id"] = args.group_id
        query = (
            f"MATCH (e:Episodic) {where} "
            "RETURN e.uuid AS uuid, e.content AS content LIMIT $limit"
        )

        async with g.driver.session() as s:
            result = await s.run(query, params)
            rows = await result.data()

        print(f"待回填 Episodic（無 embedding）: {len(rows)}（embedder 維度 {g.embedder.dimensions}）")
        if not rows or args.dry_run:
            if args.dry_run and rows:
                print("[dry-run] 加上不帶 --dry-run 實際回填。")
            return

        ok = 0
        for i in range(0, len(rows), args.batch_size):
            batch = rows[i : i + args.batch_size]
            embeddings = await g.embedder.create_batch([row["content"] for row in batch])
            async with g.driver.session() as s:
                for row, emb in zip(batch, embeddings):
                    if emb:
                        await s.run(
                            "MATCH (e:Episodic {uuid: $u}) SET e.embedding = $emb",
                            {"u": row["uuid"], "emb": emb},
                        )
                        ok += 1
            print(f"  進度: {min(i + args.batch_size, len(rows))}/{len(rows)}")

        print(f"完成: {ok}/{len(rows)} 回填成功")
    finally:
        # 關閉 embedder 的 aiohttp session，避免 Unclosed client session 警告
        sess = getattr(getattr(g, "embedder", None), "_session", None)
        if sess and not sess.closed:
            await sess.close()


if __name__ == "__main__":
    asyncio.run(main())
