#!/usr/bin/env python3
"""
evaluate_search.py — 命中率評估框架（recipe A/B 對比 + 可重現 regression）
==========================================================================

自動建立 golden query set 並量化各 search recipe 的命中率（recall@k / MRR），
用來客觀比較不同策略/設定，並把改善「可重現地」證明出來、防止退步。

子命令：
  build-golden  生成 golden set 並存檔（LLM 成本一次付清，之後零 LLM 重複評估）
  run           評估 recipe；可載入持久 golden set、對比/更新 baseline

流程（生成 golden set 時）：
  1. 隨機取樣 N 個有 summary 的 Entity（node）或有 fact 的 RELATES_TO 邊（edge）
  2. 用 LLM 從 summary/fact 生成自然語言查詢（刻意不含實體名稱，避免 trivial 命中）
  3. 對每個 recipe 用 graphiti.search_ 跑查詢，檢查目標是否在 top-k
  4. 計算 recall@k / MRR，輸出對比表；可與 baseline 對比偵測回歸

用法：
    # 一次生成可重現的 golden set
    uv run python tools/evaluate_search.py build-golden --sample 30 --out tests/fixtures/golden.json
    uv run python tools/evaluate_search.py build-golden --sample 30 --kind both --out tests/fixtures/golden.json

    # 用持久 golden set 評估（零 LLM、可重現）
    uv run python tools/evaluate_search.py run --golden tests/fixtures/golden.json
    uv run python tools/evaluate_search.py run --golden tests/fixtures/golden.json --compare-baseline
    uv run python tools/evaluate_search.py run --golden tests/fixtures/golden.json --save-baseline

    # 向後相容：無子命令 = 即時生成 + 評估（舊行為）
    uv run python tools/evaluate_search.py --sample 15 --recipes node_rrf,combined_rrf

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
DEFAULT_BASELINE = "data/eval_baseline.json"


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


async def _gen_query_edge(llm, fact: str) -> str:
    """用 LLM 從 edge fact 生成查詢（描述關係本身，避免直接照抄 fact）。"""
    fallback = (fact or "")[:60]
    if llm is None:
        return fallback
    try:
        from graphiti_core.prompts.models import Message

        msgs = [
            Message(
                role="system",
                content=(
                    "You generate ONE natural-language search query a user might type "
                    "to find the described relationship/fact in a knowledge graph. "
                    "Rephrase; do NOT copy the sentence verbatim. Keep it under 15 words."
                ),
            ),
            Message(
                role="user",
                content=(f"Fact: {fact}\n" 'Return JSON: {"query": "..."}'),
            ),
        ]
        r = await llm.generate_response(msgs, response_model=_EvalQuery)
        q = (r.get("query", "") if isinstance(r, dict) else "").strip()
        return q or fallback
    except Exception:
        return fallback


def _shuffle_take(rows, n, seed):
    """Python seed 洗牌後取前 n（Neo4j rand 無 seed，故先抓較大 pool 再取樣）。"""
    import random

    rng = random.Random(seed)
    rng.shuffle(rows)
    return rows[:n]


async def _build_golden_nodes(graphiti, n, group_id, seed):
    from src.search_eval import GoldenItem

    where = "WHERE n.summary IS NOT NULL AND size(n.summary) > 20"
    params = {"pool": max(n * 5, n)}
    if group_id:
        where += " AND n.group_id = $group_id"
        params["group_id"] = group_id
    query = (
        f"MATCH (n:Entity) {where} "
        "RETURN n.uuid AS uuid, n.name AS name, n.summary AS summary, "
        "n.group_id AS group_id LIMIT $pool"
    )
    async with graphiti.driver.session() as s:
        rows = await (await s.run(query, params)).data()
    rows = _shuffle_take(rows, n, seed)

    llm = getattr(graphiti, "llm_client", None)
    golden = []
    for row in rows:
        q = await _gen_query(llm, row["name"], row["summary"])
        golden.append(GoldenItem(
            query=q, target_uuid=row["uuid"], group_id=row["group_id"],
            target_name=row["name"], kind="node",
        ))
    return golden


async def _build_golden_edges(graphiti, n, group_id, seed):
    from src.search_eval import GoldenItem

    where = "WHERE r.fact IS NOT NULL AND size(r.fact) > 20"
    params = {"pool": max(n * 5, n)}
    if group_id:
        where += " AND r.group_id = $group_id"
        params["group_id"] = group_id
    query = (
        f"MATCH (a:Entity)-[r:RELATES_TO]->(b:Entity) {where} "
        "RETURN r.uuid AS uuid, r.fact AS fact, r.name AS name, "
        "r.group_id AS group_id LIMIT $pool"
    )
    async with graphiti.driver.session() as s:
        rows = await (await s.run(query, params)).data()
    rows = _shuffle_take(rows, n, seed)

    llm = getattr(graphiti, "llm_client", None)
    golden = []
    for row in rows:
        q = await _gen_query_edge(llm, row["fact"])
        golden.append(GoldenItem(
            query=q, target_uuid=row["uuid"], group_id=row["group_id"],
            target_name=row.get("name") or (row["fact"][:40]), kind="edge",
        ))
    return golden


async def _build_golden_one(graphiti, n, group_id, seed, kind):
    """單一 group（或全圖）建立 golden set。kind: node | edge | both。"""
    if kind == "edge":
        return await _build_golden_edges(graphiti, n, group_id, seed)
    if kind == "both":
        half = max(n // 2, 1)
        nodes = await _build_golden_nodes(graphiti, n - half, group_id, seed)
        edges = await _build_golden_edges(graphiti, half, group_id, seed + 1)
        return nodes + edges
    return await _build_golden_nodes(graphiti, n, group_id, seed)


def _allocate(total, weights, min_each=1):
    """依權重把 total 分配到各桶（最大餘數法），每桶至少 min_each。"""
    keys = list(weights.keys())
    wsum = sum(weights.values()) or 1
    raw = {k: total * weights[k] / wsum for k in keys}
    alloc = {k: max(min_each, int(raw[k])) for k in keys}
    # 依餘數補足到 total（在不破壞 min_each 的前提下做加減）
    diff = total - sum(alloc.values())
    order = sorted(keys, key=lambda k: raw[k] - int(raw[k]), reverse=True)
    i = 0
    while diff > 0 and order:
        alloc[order[i % len(order)]] += 1
        diff -= 1
        i += 1
    # 若超配，從配額最多者回收（仍守 min_each）
    while diff < 0:
        cand = max(keys, key=lambda k: alloc[k])
        if alloc[cand] <= min_each:
            break
        alloc[cand] -= 1
        diff += 1
    return alloc


async def _build_golden_stratified(graphiti, n, seed, kind, top_groups):
    """分層取樣：依各 group 的 Entity 數比例，從前 top_groups 大 group 取樣，
    避免樣本全落在最大 group。一定納入 global（若存在）。"""
    async with graphiti.driver.session() as s:
        rows = await (await s.run(
            "MATCH (e:Entity) WHERE e.summary IS NOT NULL AND size(e.summary) > 20 "
            "RETURN e.group_id AS g, count(e) AS c ORDER BY c DESC LIMIT $lim",
            {"lim": top_groups},
        )).data()
    weights = {r["g"]: r["c"] for r in rows if r["g"]}
    if not weights:
        return await _build_golden_one(graphiti, n, None, seed, kind)
    # 確保 global 入選
    if "global" not in weights:
        async with graphiti.driver.session() as s:
            gr = await (await s.run(
                "MATCH (e:Entity) WHERE e.group_id='global' RETURN count(e) AS c"
            )).single()
        if gr and gr["c"]:
            weights["global"] = gr["c"]
    alloc = _allocate(n, weights, min_each=2)
    print(f"分層取樣配額（{len(alloc)} groups）: " +
          ", ".join(f"{g}:{a}" for g, a in sorted(alloc.items(), key=lambda x: -x[1])))
    golden = []
    for i, (g, a) in enumerate(sorted(alloc.items())):
        items = await _build_golden_one(graphiti, a, g, seed + i, kind)
        golden.extend(items)
    return golden


async def _build_golden(graphiti, n, group_id, seed, kind="node", stratified=False, top_groups=15):
    """依 kind 建立 golden set。stratified=True 時跨 group 分層取樣（忽略 group_id）。"""
    if stratified and not group_id:
        return await _build_golden_stratified(graphiti, n, seed, kind, top_groups)
    return await _build_golden_one(graphiti, n, group_id, seed, kind)


def _recipe_domain(recipe: str) -> str:
    """recipe 的結果領域：edge | community | node（含 combined）。"""
    if recipe.startswith("edge_"):
        return "edge"
    if recipe.startswith("community_"):
        return "community"
    return "node"  # node_* 與 combined_*


def _extract_objects(res, recipe: str):
    """從 search_ 結果依 recipe 領域取出排序後的物件清單。"""
    domain = _recipe_domain(recipe)
    if domain == "edge":
        return list(res.edges or [])
    if domain == "community":
        return list(res.communities or [])
    return list(res.nodes or [])


def _extract_ranked(res, recipe: str):
    """從 search_ 結果依 recipe 領域取出排序後的 uuid 清單。"""
    return [str(o.uuid) for o in _extract_objects(res, recipe)]


def _item_kind_for_domain(domain: str) -> str:
    """recipe 領域對應到應評估的 golden item kind。"""
    return "edge" if domain == "edge" else "node"


async def _evaluate(graphiti, server, golden, recipes, k, mmr_lambda, sim_min_score, verbose, pool=None, post_rerank=False):
    """對每個 recipe 跑 golden set。

    回傳 (metrics, raw)：
      metrics: RecipeMetrics 清單（跨全部樣本彙總）
      raw: {recipe: [(group_id, ranked, target_uuid), ...]}，供 per-group 拆解

    pool: 候選池大小（config.limit）。None 時用 max(k,10)；設大於 k 可測重排把
          池中第 k+1~pool 名拉進 top-k 的效果。
    """
    from src.search_eval import compute_metrics

    all_metrics = []
    raw = {}
    for recipe_name in recipes:
        domain = _recipe_domain(recipe_name)
        want_kind = _item_kind_for_domain(domain)
        items = [g for g in golden if g.kind == want_kind]
        if not items:
            print(f"  跳過 {recipe_name}（無 {want_kind} 類樣本）")
            continue

        config = server.SEARCH_RECIPES[recipe_name].model_copy(deep=True)
        config.limit = pool if pool else max(k, 10)
        if mmr_lambda is not None or sim_min_score is not None:
            server._apply_search_tuning(config, sim_min_score=sim_min_score, mmr_lambda=mmr_lambda)

        results, durations, recipe_raw = [], [], []
        for item in items:
            t0 = time.monotonic()
            try:
                res = await graphiti.search_(
                    query=item.query, config=config, group_ids=[item.group_id]
                )
                if post_rerank:
                    objs = _extract_objects(res, recipe_name)
                    objs = await server._apply_rerank(item.query, objs, want_kind)
                    ranked = [str(o.uuid) for o in objs]
                else:
                    ranked = _extract_ranked(res, recipe_name)
            except Exception as e:
                ranked = []
                if verbose:
                    print(f"  [錯誤] {recipe_name} / {item.query[:30]}: {e}")
            durations.append(time.monotonic() - t0)
            results.append((ranked, item.target_uuid))
            recipe_raw.append((item.group_id, ranked, item.target_uuid))
            if verbose:
                hit = item.target_uuid in ranked[:k]
                print(f"  {recipe_name} | {'✓' if hit else '✗'} | {item.query[:50]}")
        m = compute_metrics(recipe_name, results, k, durations)
        all_metrics.append(m)
        raw[recipe_name] = recipe_raw
        print(f"  完成 {recipe_name}: recall@{k}={m.recall_at_k:.3f}, MRR={m.mrr:.3f} (n={m.total})")
    return all_metrics, raw


def _format_per_group(raw, k, low_recall=0.8):
    """依 group 拆解每個 recipe 的 recall@k / MRR，標出低於門檻的 group。"""
    from src.search_eval import compute_metrics

    lines = ["", "--- per-group 拆解 ---"]
    weak = []
    for recipe_name, rows in raw.items():
        by_group = {}
        for gid, ranked, target in rows:
            by_group.setdefault(gid, []).append((ranked, target))
        lines.append(f"\n[{recipe_name}]")
        lines.append(f"  {'group':<28} {'recall@'+str(k):>10} {'MRR':>8} {'n':>5}")
        for gid in sorted(by_group, key=lambda g: compute_metrics('', by_group[g], k).recall_at_k):
            m = compute_metrics(recipe_name, by_group[gid], k)
            flag = "  ⚠️ 低召回" if m.recall_at_k < low_recall else ""
            lines.append(f"  {gid:<28} {m.recall_at_k:>10.3f} {m.mrr:>8.3f} {m.total:>5}{flag}")
            if m.recall_at_k < low_recall:
                weak.append((recipe_name, gid, m.recall_at_k, m.total))
    if weak:
        lines.append(f"\n弱點 group（recall<{low_recall}）共 {len(weak)} 項：")
        for r, g, rec, n in sorted(weak, key=lambda x: x[2]):
            lines.append(f"  {r} / {g}: recall={rec:.3f} (n={n})")
    return "\n".join(lines)


def _filter_recipes(recipes_arg, server):
    recipes = (
        [r.strip() for r in recipes_arg.split(",") if r.strip()]
        if recipes_arg else DEFAULT_RECIPES
    )
    return [r for r in recipes if r in server.SEARCH_RECIPES]


async def _close_embedder(graphiti):
    sess = getattr(getattr(graphiti, "embedder", None), "_session", None)
    if sess and not sess.closed:
        await sess.close()


async def cmd_build_golden(args, server, graphiti):
    from src.search_eval import save_golden

    mode = "分層" if getattr(args, "stratified", False) else "單層"
    print(f"建立 golden set（kind={args.kind}, {mode}取樣 {args.sample}，LLM 生成查詢中）...")
    golden = await _build_golden(
        graphiti, args.sample, args.group_id, args.seed, args.kind,
        stratified=getattr(args, "stratified", False),
        top_groups=getattr(args, "top_groups", 15),
    )
    if not golden:
        print("無可取樣的目標，請確認圖譜有資料。")
        return 1
    n = save_golden(golden, args.out)
    print(f"已寫入 {n} 筆 golden 樣本 → {args.out}")
    by_kind = {}
    for g in golden:
        by_kind[g.kind] = by_kind.get(g.kind, 0) + 1
    print(f"分布: {by_kind}")
    return 0


async def cmd_run(args, server, graphiti):
    from src.search_eval import (
        compare_to_baseline,
        format_comparison_table,
        load_golden,
        save_baseline,
    )
    import json

    recipes = _filter_recipes(args.recipes, server)

    if getattr(args, "golden", None):
        golden = load_golden(args.golden)
        print(f"載入 golden set：{args.golden}（{len(golden)} 筆）")
    else:
        print(f"建立 golden query set（即時生成，取樣 {args.sample}）...")
        golden = await _build_golden(graphiti, args.sample, args.group_id, args.seed, args.kind)
    if not golden:
        print("無 golden 樣本，請確認圖譜有資料或 golden 檔。")
        return 1
    print(f"golden 樣本數: {len(golden)}；評估 recipe: {recipes}\n")

    metrics, raw = await _evaluate(
        graphiti, server, golden, recipes, args.k,
        args.mmr_lambda, args.sim_min_score, args.verbose,
        pool=getattr(args, "pool", None),
        post_rerank=getattr(args, "post_rerank", False),
    )

    print("\n" + "=" * 60)
    print(f"命中率評估結果（n={len(golden)}, k={args.k}）")
    print("=" * 60)
    print(format_comparison_table(metrics, args.k))

    if getattr(args, "per_group", False):
        print(_format_per_group(raw, args.k, args.low_recall))

    exit_code = 0
    if getattr(args, "compare_baseline", False):
        baseline = None
        bp = Path(args.baseline)
        if bp.exists():
            baseline = json.loads(bp.read_text(encoding="utf-8"))
        regressions, lines = compare_to_baseline(metrics, baseline, args.tol)
        print("\n--- 對比 baseline ---")
        print("\n".join(lines) if lines else "（無可對比項）")
        if regressions:
            print(f"\n⚠️ 偵測到 {len(regressions)} 項回歸（tol={args.tol}）")
            exit_code = 2

    if getattr(args, "save_baseline", False):
        save_baseline(metrics, args.baseline, args.k)
        print(f"\n已更新 baseline → {args.baseline}")

    return exit_code


def _add_common(p):
    p.add_argument("--sample", type=int, default=20, help="golden 樣本數（即時生成時）")
    p.add_argument("--k", type=int, default=10, help="top-k")
    p.add_argument("--recipes", default=None, help="逗號分隔的 recipe；預設常用 5 種")
    p.add_argument("--group-id", default=None, help="限定取樣與搜尋的 group")
    p.add_argument("--seed", type=int, default=13, help="取樣亂數種子（可重現）")
    p.add_argument("--kind", default="node", choices=["node", "edge", "both"], help="golden 目標型別")
    p.add_argument("--mmr-lambda", type=float, default=None, help="覆寫 mmr_lambda（掃描調參用）")
    p.add_argument("--sim-min-score", type=float, default=None, help="覆寫 sim_min_score")
    p.add_argument("--verbose", action="store_true", help="印出每筆 query 與命中情形")


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="命中率評估框架（recipe A/B + regression）")
    sub = parser.add_subparsers(dest="cmd")

    pb = sub.add_parser("build-golden", help="生成 golden set 並存檔")
    pb.add_argument("--out", required=True, help="輸出 JSON 路徑")
    pb.add_argument("--sample", type=int, default=30)
    pb.add_argument("--group-id", default=None)
    pb.add_argument("--seed", type=int, default=13)
    pb.add_argument("--kind", default="node", choices=["node", "edge", "both"])
    pb.add_argument("--stratified", action="store_true", help="跨 group 依規模分層取樣")
    pb.add_argument("--top-groups", type=int, default=15, help="分層取樣納入的前 N 大 group")

    pr = sub.add_parser("run", help="評估 recipe（可載入 golden / 對比 baseline）")
    _add_common(pr)
    pr.add_argument("--golden", default=None, help="載入持久 golden set（零 LLM）")
    pr.add_argument("--compare-baseline", action="store_true", help="與 baseline 對比偵測回歸")
    pr.add_argument("--save-baseline", action="store_true", help="把本次度量存為新 baseline")
    pr.add_argument("--baseline", default=DEFAULT_BASELINE, help="baseline JSON 路徑")
    pr.add_argument("--tol", type=float, default=0.05, help="回歸容忍下滑幅度")
    pr.add_argument("--per-group", action="store_true", help="輸出各 group 的 recall/MRR 拆解")
    pr.add_argument("--low-recall", type=float, default=0.8, help="per-group 低召回警示門檻")
    pr.add_argument("--pool", type=int, default=None, help="候選池大小（config.limit）；設大於 k 可測重排把第 k+1~pool 名拉進 top-k")
    pr.add_argument("--rerank-top-n", type=int, default=None, help="重排涵蓋筆數（覆寫 cross_encoder.top_n，需 LLM_PROVIDER 的 reranker 啟用）")
    pr.add_argument("--cross-encoder-provider", default=None, choices=["none", "llm", "bge"], help="覆寫 cross_encoder.provider（繞過 .env，量測不同 reranker）")
    pr.add_argument("--post-rerank", action="store_true", help="對 RRF 候選池套用 _apply_rerank post-rerank（乾淨隔離重排效果，不引入 bfs）")

    # 向後相容：無子命令 = run（即時生成）
    _add_common(parser)
    parser.add_argument("--golden", default=None)
    parser.add_argument("--compare-baseline", action="store_true")
    parser.add_argument("--save-baseline", action="store_true")
    parser.add_argument("--baseline", default=DEFAULT_BASELINE)
    parser.add_argument("--tol", type=float, default=0.05)
    return parser.parse_args(argv)


async def main():
    args = _parse_args(sys.argv[1:])

    import graphiti_mcp_server as server
    from src.config import load_config

    server.app_config = load_config()
    # cross_encoder 覆寫（須在 initialize_graphiti 注入 reranker 前設定；繞過 .env override）
    ce_provider = getattr(args, "cross_encoder_provider", None)
    if ce_provider and getattr(server.app_config, "cross_encoder", None):
        server.app_config.cross_encoder.provider = ce_provider
        print(f"[調參] cross_encoder.provider 覆寫為 {ce_provider}")
    rtn = getattr(args, "rerank_top_n", None)
    if rtn and getattr(server.app_config, "cross_encoder", None):
        server.app_config.cross_encoder.top_n = rtn
        print(f"[調參] cross_encoder.top_n 覆寫為 {rtn}")
    graphiti = await server.initialize_graphiti()
    try:
        if args.cmd == "build-golden":
            return await cmd_build_golden(args, server, graphiti)
        return await cmd_run(args, server, graphiti)  # cmd == "run" 或 None
    finally:
        await _close_embedder(graphiti)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()) or 0)
