#!/usr/bin/env python3
"""
evaluate_search.py — 命中率評估框架（recipe A/B 對比）
======================================================

自動建立 golden query set 並量化各 search recipe 的命中率，用來客觀比較不同
策略/設定的 recall@k 與 MRR，驗證命中率改善是否真的有效。

流程：
  1. 隨機取樣 N 個有 summary 的 Entity 作為「目標」
  2. 用 LLM 從每個 summary 生成一個自然語言查詢（刻意不含實體名稱，避免 trivial 命中）
  3. 對每個 recipe 用 graphiti.search_ 跑查詢，檢查目標是否在 top-k
  4. 計算 recall@k / MRR，輸出對比表

用法：
    uv run python tools/evaluate_search.py
    uv run python tools/evaluate_search.py --sample 30 --k 10
    uv run python tools/evaluate_search.py --recipes combined_rrf,combined_cross_encoder
    uv run python tools/evaluate_search.py --group-id global --seed 42

注意：含 *_cross_encoder 的 recipe 會對每筆查詢呼叫 LLM 重排，評估較慢。
"""
import argparse
import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import BaseModel

DEFAULT_RECIPES = [
    "node_rrf",
    "node_mmr",
    "node_cross_encoder",
    "combined_rrf",
    "combined_cross_encoder",
]


class _EvalQuery(BaseModel):
    query: str


async def _gen_query(llm, name: str, summary: str) -> str:
    """用 LLM 從 entity summary 生成查詢（不含 name）；失敗時退回 summary 片段。"""
    fallback = (summary or name)[:60]
    if llm is None:
        return fallback
    try:
        from graphiti_core.prompts.models import Message

        msgs = [
            Message(
                role="system",
                content=(
                    "You generate ONE natural-language search query a user might type "
                    "to find the described entity in a knowledge graph. Do NOT include "
                    "the entity's exact name; describe it by its properties/context. "
                    "Keep it under 15 words."
                ),
            ),
            Message(
                role="user",
                content=(
                    f"Entity name (do NOT reuse this name): {name}\n"
                    f"Description: {summary}\n"
                    'Return JSON: {"query": "..."}'
                ),
            ),
        ]
        r = await llm.generate_response(msgs, response_model=_EvalQuery)
        q = (r.get("query", "") if isinstance(r, dict) else "").strip()
        return q or fallback
    except Exception:
        return fallback


async def _build_golden(graphiti, n, group_id, seed):
    from src.search_eval import GoldenItem

    where = "WHERE n.summary IS NOT NULL AND size(n.summary) > 20"
    params = {"n": n}
    if group_id:
        where += " AND n.group_id = $group_id"
        params["group_id"] = group_id
    # 用 rand(seed) 取樣（Neo4j rand 無 seed，改抓較多再由 Python seed 取樣）
    query = (
        f"MATCH (n:Entity) {where} "
        "RETURN n.uuid AS uuid, n.name AS name, n.summary AS summary, "
        "n.group_id AS group_id LIMIT $pool"
    )
    params["pool"] = max(n * 5, n)
    async with graphiti.driver.session() as s:
        result = await s.run(query, params)
        rows = await result.data()

    import random

    rng = random.Random(seed)
    rng.shuffle(rows)
    rows = rows[:n]

    llm = getattr(graphiti, "llm_client", None)
    golden = []
    for row in rows:
        q = await _gen_query(llm, row["name"], row["summary"])
        golden.append(GoldenItem(
            query=q, target_uuid=row["uuid"],
            group_id=row["group_id"], target_name=row["name"],
        ))
    return golden


async def main():
    parser = argparse.ArgumentParser(description="命中率評估框架（recipe A/B 對比）")
    parser.add_argument("--sample", type=int, default=20, help="golden 樣本數")
    parser.add_argument("--k", type=int, default=10, help="top-k")
    parser.add_argument("--recipes", default=None, help="逗號分隔的 recipe；預設常用 5 種")
    parser.add_argument("--group-id", default=None, help="限定取樣與搜尋的 group")
    parser.add_argument("--seed", type=int, default=13, help="取樣亂數種子（可重現）")
    parser.add_argument("--mmr-lambda", type=float, default=None, help="覆寫 mmr_lambda（掃描調參用）")
    parser.add_argument("--sim-min-score", type=float, default=None, help="覆寫 sim_min_score")
    parser.add_argument("--verbose", action="store_true", help="印出每筆 query 與命中情形")
    args = parser.parse_args()

    import graphiti_mcp_server as server
    from src.config import load_config
    from src.search_eval import compute_metrics, format_comparison_table

    server.app_config = load_config()
    graphiti = await server.initialize_graphiti()
    recipes = (
        [r.strip() for r in args.recipes.split(",") if r.strip()]
        if args.recipes else DEFAULT_RECIPES
    )
    recipes = [r for r in recipes if r in server.SEARCH_RECIPES]

    try:
        print(f"建立 golden query set（取樣 {args.sample} 個 Entity，生成查詢中）...")
        golden = await _build_golden(graphiti, args.sample, args.group_id, args.seed)
        print(f"golden 樣本數: {len(golden)}；評估 recipe: {recipes}\n")
        if not golden:
            print("無可取樣的 Entity，請確認圖譜有資料。")
            return

        all_metrics = []
        for recipe_name in recipes:
            config = server.SEARCH_RECIPES[recipe_name].model_copy(deep=True)
            config.limit = max(args.k, 10)
            if args.mmr_lambda is not None or args.sim_min_score is not None:
                server._apply_search_tuning(
                    config, sim_min_score=args.sim_min_score, mmr_lambda=args.mmr_lambda
                )
            results, durations = [], []
            for item in golden:
                t0 = time.monotonic()
                try:
                    res = await graphiti.search_(
                        query=item.query, config=config, group_ids=[item.group_id]
                    )
                    ranked = [str(n.uuid) for n in (res.nodes or [])]
                except Exception as e:
                    ranked = []
                    if args.verbose:
                        print(f"  [錯誤] {recipe_name} / {item.query[:30]}: {e}")
                durations.append(time.monotonic() - t0)
                results.append((ranked, item.target_uuid))
                if args.verbose:
                    hit = item.target_uuid in ranked[: args.k]
                    print(f"  {recipe_name} | {'✓' if hit else '✗'} | {item.query[:50]}")
            m = compute_metrics(recipe_name, results, args.k, durations)
            all_metrics.append(m)
            print(f"  完成 {recipe_name}: recall@{args.k}={m.recall_at_k:.3f}, MRR={m.mrr:.3f}")

        print("\n" + "=" * 60)
        print(f"命中率評估結果（n={len(golden)}, k={args.k}）")
        print("=" * 60)
        print(format_comparison_table(all_metrics, args.k))
    finally:
        sess = getattr(getattr(graphiti, "embedder", None), "_session", None)
        if sess and not sess.closed:
            await sess.close()


if __name__ == "__main__":
    asyncio.run(main())
