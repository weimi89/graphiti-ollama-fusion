#!/usr/bin/env python3
"""
DeepSeek v4-flash vs v4-pro 寫入效能對比
========================================

對相同內容，以兩個 DeepSeek 模型分別跑完整 graphiti add_episode pipeline
（實體提取 + 邊提取 + 去重 + 摘要），共用同一個 Ollama bge-m3 嵌入器，
量測端到端寫入時間與提取的實體/關係數量。

使用獨立 group_id（bench-deepseek-*），測試後可單獨清理，不污染專案記憶。

執行：
    uv run python tests/bench_deepseek_flash_vs_pro.py
"""

import asyncio
import os
import sys
import time

# 確保可從 tests/ 目錄執行時找到專案根的 src 套件
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from graphiti_core import Graphiti
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.nodes import EpisodeType

from src.config import GraphitiConfig
from src.deepseek_client import DeepSeekClient
from src.ollama_embedder import OllamaEmbedder

# 測試內容：一短一中，模擬真實記憶寫入場景
SAMPLES = [
    (
        "短文本",
        "張偉是台北一家科技公司的工程師，專長是後端開發與資料庫優化。",
    ),
    (
        "中等文本",
        "2026 年 5 月，林研發團隊在台中啟動了代號 Falcon 的專案，"
        "目標是為電商平台打造即時推薦系統。團隊由產品經理王小美領導，"
        "技術負責人是陳大文，後端使用 Python 與 PostgreSQL，"
        "前端採用 Vue 3。預計第三季上線。",
    ),
]


async def make_graphiti(model: str, embedder: OllamaEmbedder, cfg: GraphitiConfig) -> Graphiti:
    """以指定 DeepSeek 模型建立 Graphiti 實例，共用傳入的嵌入器。"""
    d = cfg.deepseek
    llm_client = DeepSeekClient(
        LLMConfig(
            api_key=d.api_key,
            base_url=d.base_url,
            model=model,
            temperature=d.temperature,
            max_tokens=d.max_tokens,
        )
    )
    g = Graphiti(
        uri=cfg.neo4j.uri,
        user=cfg.neo4j.user,
        password=cfg.neo4j.password,
        llm_client=llm_client,
        embedder=embedder,
        max_coroutines=cfg.memory_performance.max_coroutines,
    )
    await g.build_indices_and_constraints()
    return g


async def bench_model(model: str, embedder: OllamaEmbedder, cfg: GraphitiConfig) -> dict:
    """對單一模型跑全部樣本，回傳每筆與彙總指標。"""
    group_id = f"bench-deepseek-{model.replace('deepseek-', '')}"
    g = await make_graphiti(model, embedder, cfg)
    rows = []
    try:
        for label, body in SAMPLES:
            t0 = time.time()
            try:
                res = await g.add_episode(
                    name=f"bench-{label}",
                    episode_body=body,
                    source=EpisodeType.text,
                    source_description="bench",
                    reference_time=__import__("datetime").datetime.now(
                        __import__("datetime").timezone.utc
                    ),
                    group_id=group_id,
                )
                elapsed = time.time() - t0
                rows.append({
                    "label": label,
                    "chars": len(body),
                    "seconds": elapsed,
                    "nodes": len(res.nodes),
                    "edges": len(res.edges),
                    "error": None,
                })
            except Exception as e:
                rows.append({
                    "label": label,
                    "chars": len(body),
                    "seconds": time.time() - t0,
                    "nodes": 0,
                    "edges": 0,
                    "error": str(e)[:120],
                })
    finally:
        await g.close()
    return {"model": model, "group_id": group_id, "rows": rows}


def print_report(results: list[dict]) -> None:
    print("\n" + "=" * 72)
    print("DeepSeek v4-flash vs v4-pro 寫入對比（完整模式，bge-m3 嵌入）")
    print("=" * 72)
    for r in results:
        total = sum(row["seconds"] for row in r["rows"])
        print(f"\n■ 模型: {r['model']}  (group_id={r['group_id']})")
        print(f"  {'樣本':<10}{'字數':>6}{'耗時(s)':>10}{'實體':>6}{'關係':>6}  錯誤")
        for row in r["rows"]:
            err = row["error"] or "-"
            print(
                f"  {row['label']:<10}{row['chars']:>6}{row['seconds']:>10.1f}"
                f"{row['nodes']:>6}{row['edges']:>6}  {err}"
            )
        print(f"  {'合計':<10}{'':>6}{total:>10.1f}")

    if len(results) == 2:
        t_flash = sum(row["seconds"] for row in results[0]["rows"])
        t_pro = sum(row["seconds"] for row in results[1]["rows"])
        if t_flash > 0:
            print("\n" + "-" * 72)
            faster = "flash" if t_flash < t_pro else "pro"
            ratio = (max(t_flash, t_pro) / min(t_flash, t_pro)) if min(t_flash, t_pro) > 0 else 0
            print(f"結論: {results[0]['model']} 合計 {t_flash:.1f}s，"
                  f"{results[1]['model']} 合計 {t_pro:.1f}s")
            print(f"      {faster} 較快，約 {ratio:.1f}x")
    print("=" * 72 + "\n")


async def main():
    cfg = GraphitiConfig.from_env()
    if not cfg.deepseek.api_key:
        raise SystemExit("DEEPSEEK_API_KEY 未設定")

    # 共用同一個 bge-m3 嵌入器，確保只比較 LLM 差異
    embedder = OllamaEmbedder(
        model=cfg.embedder.model,
        base_url=cfg.embedder.base_url,
        dimensions=cfg.embedder.dimensions,
    )

    results = []
    for model in ("deepseek-v4-flash", "deepseek-v4-pro"):
        print(f"\n>>> 測試 {model} ...")
        results.append(await bench_model(model, embedder, cfg))

    print_report(results)
    print("提示: 測試資料在 group_id bench-deepseek-v4-flash / bench-deepseek-v4-pro，"
          "可用 DELETE /api/groups/{group_id} 清理。")


if __name__ == "__main__":
    asyncio.run(main())
