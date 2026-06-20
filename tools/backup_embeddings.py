#!/usr/bin/env python3
"""
backup_embeddings.py — 備份 Neo4j 所有 embedding 到 backups/{timestamp}/
========================================================================

在 embedding 維度遷移（如 768→1024）前執行，匯出現有向量供必要時還原。
匯出格式為 JSONL，每行 {"type", "uuid", "emb"}。還原可讀此檔以 update Cypher 寫回。

用法：
    uv run python tools/backup_embeddings.py
"""
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

_QUERIES = [
    ("entity", "MATCH (n:Entity) WHERE n.name_embedding IS NOT NULL "
               "RETURN n.uuid AS uuid, n.name_embedding AS emb"),
    ("edge", "MATCH ()-[e:RELATES_TO]->() WHERE e.fact_embedding IS NOT NULL "
             "RETURN e.uuid AS uuid, e.fact_embedding AS emb"),
    ("community", "MATCH (c:Community) WHERE c.name_embedding IS NOT NULL "
                  "RETURN c.uuid AS uuid, c.name_embedding AS emb"),
]


async def main():
    import graphiti_mcp_server as server
    from src.config import load_config

    server.app_config = load_config()
    g = await server.initialize_graphiti()

    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    out_dir = Path(__file__).resolve().parent.parent / "backups" / ts
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "embeddings_backup.jsonl"

    count, dims = 0, set()
    with open(out_file, "w", encoding="utf-8") as f:
        async with g.driver.session() as s:
            for typ, q in _QUERIES:
                result = await s.run(q)
                async for rec in result:
                    emb = rec["emb"]
                    dims.add(len(emb) if emb else 0)
                    f.write(json.dumps({"type": typ, "uuid": rec["uuid"], "emb": emb}) + "\n")
                    count += 1

    print(f"備份完成: {count} 筆 embedding（維度 {sorted(dims)}）→ {out_file}")


if __name__ == "__main__":
    asyncio.run(main())
