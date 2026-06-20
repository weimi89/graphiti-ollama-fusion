"""
雙記憶混合搜尋橋接
==================

橋接 claude-mem 工作記憶 worker 的 HTTP API，讓 Graphiti 知識圖譜搜尋能融合
claude-mem 的即時 session 歷史，各取所長：
  - Graphiti：結構化實體/關係、跨 session 推理（Neo4j 圖）
  - claude-mem：即時、自動捕獲的工作記憶（SQLite FTS + Chroma）

claude-mem worker 預設在 http://localhost:37777，提供 GET /api/search?query=&project=&limit=
回傳 {"content": [{"type": "text", "text": "..."}]}（markdown 結果）。

任何連線/逾時失敗都優雅降級（回 None），不影響 Graphiti 主搜尋。
"""
import logging
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)


async def query_claude_mem(
    base_url: str,
    query: str,
    project: Optional[str] = None,
    limit: int = 5,
    timeout: float = 8.0,
) -> Optional[str]:
    """
    查詢 claude-mem worker 的工作記憶。

    Args:
        base_url: claude-mem worker base URL（如 http://localhost:37777）
        query: 查詢字串
        project: 限定專案（可選）
        limit: 結果上限
        timeout: 逾時秒數

    Returns:
        str: claude-mem 回傳的 markdown 文字結果；連線/逾時/非 200 失敗時回 None（降級）
    """
    if not base_url or not query:
        return None

    params = {"query": query, "limit": str(limit)}
    if project:
        params["project"] = project

    url = f"{base_url.rstrip('/')}/api/search"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, params=params, timeout=aiohttp.ClientTimeout(total=timeout)
            ) as resp:
                if resp.status != 200:
                    logger.warning(f"claude-mem 查詢回應 {resp.status}（降級為純 Graphiti）")
                    return None
                data = await resp.json()
        content = data.get("content", []) if isinstance(data, dict) else []
        texts = [c.get("text", "") for c in content if c.get("type") == "text" and c.get("text")]
        return "\n".join(texts) if texts else None
    except Exception as e:
        logger.warning(f"claude-mem 查詢失敗（降級為純 Graphiti）: {e}")
        return None
