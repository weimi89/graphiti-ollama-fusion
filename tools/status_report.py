#!/usr/bin/env python3
"""
Graphiti MCP Server 即時狀態報告
================================

動態查詢系統各組件的實時狀態，取代舊版靜態報告工具。

用法：
    uv run python tools/status_report.py
    uv run python tools/status_report.py --json     # JSON 格式輸出
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from src.config import load_config

logging.basicConfig(level=logging.WARNING)


async def gather_status() -> dict:
    """收集系統各組件的實時狀態。"""
    config = load_config()
    report: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config": {
            "neo4j_uri": config.neo4j.uri,
            "ollama_model": config.ollama.model,
            "embedder_model": config.embedder.model,
        },
        "components": {},
        "graph_stats": {},
    }

    # --- Neo4j 連接 ---
    try:
        from graphiti_core import Graphiti

        graphiti = Graphiti(
            uri=config.neo4j.uri,
            user=config.neo4j.user,
            password=config.neo4j.password,
        )

        # 節點 / 事實 / 片段統計
        count_query = """
        MATCH (n)
        RETURN labels(n)[0] AS label, count(n) AS cnt
        """
        records, _, _ = await graphiti.driver.execute_query(count_query)
        stats = {r["label"]: r["cnt"] for r in records}
        report["graph_stats"] = {
            "entities": stats.get("Entity", 0),
            "episodic": stats.get("Episodic", 0),
        }

        # 關係
        rel_query = """
        MATCH ()-[r]-()
        RETURN type(r) AS rel, count(r) AS cnt
        """
        rel_records, _, _ = await graphiti.driver.execute_query(rel_query)
        report["graph_stats"]["relationships"] = {
            r["rel"]: r["cnt"] for r in rel_records
        }

        # group 統計
        group_query = """
        MATCH (e:Episodic)
        RETURN e.group_id AS gid, count(e) AS cnt
        ORDER BY cnt DESC LIMIT 10
        """
        grp_records, _, _ = await graphiti.driver.execute_query(group_query)
        report["graph_stats"]["top_groups"] = [
            {"group_id": r["gid"], "count": r["cnt"]} for r in grp_records
        ]

        report["components"]["neo4j"] = "OK"

        # --- Neo4j 索引檢查 ---
        try:
            idx_records, _, _ = await graphiti.driver.execute_query("SHOW INDEXES")
            index_names = sorted(r.get("name", "") for r in idx_records)
            report["indices"] = {
                "total": len(index_names),
                "names": index_names,
            }
        except Exception as idx_err:
            report["indices"] = {"error": str(idx_err)}

        await graphiti.driver.close()
    except Exception as e:
        report["components"]["neo4j"] = f"ERROR: {e}"

    # --- Ollama LLM ---
    try:
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{config.ollama.base_url}/api/tags", timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    models = [m["name"] for m in data.get("models", [])]
                    if config.ollama.model in models:
                        report["components"]["ollama_llm"] = "OK"
                    else:
                        report["components"]["ollama_llm"] = f"模型 {config.ollama.model} 未找到"
                    report["components"]["ollama_available_models"] = models
                else:
                    report["components"]["ollama_llm"] = f"HTTP {resp.status}"
    except Exception as e:
        report["components"]["ollama_llm"] = f"ERROR: {e}"

    # --- Embedder ---
    try:
        from src.ollama_embedder import OllamaEmbedder

        embedder = OllamaEmbedder(
            model=config.embedder.model,
            base_url=config.embedder.base_url,
            dimensions=config.embedder.dimensions,
        )
        connected = await embedder.test_connection()
        report["components"]["embedder"] = "OK" if connected else "模型不可用"
        report["components"]["embedder_dimensions"] = config.embedder.dimensions
    except Exception as e:
        report["components"]["embedder"] = f"ERROR: {e}"

    # --- 依賴版本 ---
    try:
        import graphiti_core

        report["versions"] = {
            "graphiti_core": getattr(graphiti_core, "__version__", "unknown"),
            "python": sys.version.split()[0],
        }
    except Exception:
        report["versions"] = {"graphiti_core": "unknown", "python": sys.version.split()[0]}

    return report


def print_report(report: dict) -> None:
    """格式化輸出報告。"""
    print("=" * 60)
    print("Graphiti MCP Server 即時狀態報告")
    print(f"時間: {report['timestamp']}")
    print("=" * 60)

    print("\n組件狀態:")
    for k, v in report.get("components", {}).items():
        if k.startswith("ollama_available") or k.endswith("dimensions"):
            continue
        icon = "OK" if v == "OK" else "!!"
        print(f"  [{icon}] {k}: {v}")

    dims = report.get("components", {}).get("embedder_dimensions")
    if dims:
        print(f"       嵌入維度: {dims}")

    models = report.get("components", {}).get("ollama_available_models", [])
    if models:
        print(f"       可用模型: {', '.join(models[:8])}")

    stats = report.get("graph_stats", {})
    if stats:
        print("\n知識圖譜統計:")
        print(f"  實體節點: {stats.get('entities', 0)}")
        print(f"  記憶片段: {stats.get('episodic', 0)}")
        rels = stats.get("relationships", {})
        for rel, cnt in rels.items():
            print(f"  關係 {rel}: {cnt}")
        top = stats.get("top_groups", [])
        if top:
            print(f"\n  前 {len(top)} 大群組:")
            for g in top:
                print(f"    {g['group_id']}: {g['count']} 筆")

    indices = report.get("indices", {})
    if indices:
        print("\nNeo4j 索引:")
        if "error" in indices:
            print(f"  [!!] 索引查詢失敗: {indices['error']}")
        else:
            total = indices.get("total", 0)
            print(f"  已建立索引數: {total}")
            names = indices.get("names", [])
            for name in names:
                print(f"    - {name}")

    versions = report.get("versions", {})
    if versions:
        print(f"\n版本資訊:")
        for k, v in versions.items():
            print(f"  {k}: {v}")

    print("\n配置:")
    for k, v in report.get("config", {}).items():
        print(f"  {k}: {v}")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Graphiti MCP Server 即時狀態報告")
    parser.add_argument("--json", action="store_true", help="JSON 格式輸出")
    args = parser.parse_args()

    report = asyncio.run(gather_status())

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_report(report)


if __name__ == "__main__":
    main()
