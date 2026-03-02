"""
記憶去重模組
============

提供記憶片段的相似度檢查，避免重複添加高度相似的內容。

使用嵌入向量的餘弦相似度比對最近的 episodes，
超過閾值時回傳警告，讓呼叫端決定是否繼續。
"""

import logging
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class DuplicateCheckResult:
    """去重檢查結果。"""

    is_duplicate: bool
    max_similarity: float
    similar_episode_uuid: Optional[str] = None
    similar_episode_name: Optional[str] = None
    message: str = ""


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """計算兩個向量的餘弦相似度。"""
    if len(vec_a) != len(vec_b) or not vec_a:
        return 0.0

    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


async def check_episode_similarity(
    driver: Any,
    embedder: Any,
    content: str,
    group_id: str,
    threshold: float = 0.9,
    max_compare: int = 20,
) -> DuplicateCheckResult:
    """
    檢查新內容與最近 episodes 的相似度。

    Args:
        driver: Neo4j driver 實例
        embedder: 嵌入器實例
        content: 要檢查的新內容
        group_id: 分組 ID
        threshold: 相似度閾值（超過視為重複）
        max_compare: 最多比較的 episode 數量

    Returns:
        DuplicateCheckResult: 檢查結果
    """
    try:
        # 生成新內容的嵌入
        embeddings = await embedder.create([{"text": content}])
        if not embeddings or not embeddings[0]:
            return DuplicateCheckResult(
                is_duplicate=False, max_similarity=0.0,
                message="無法生成嵌入向量，跳過去重檢查",
            )
        new_embedding = embeddings[0]

        # 從 Neo4j 取得最近的 episodes（含嵌入）
        query = """
        MATCH (e:Episodic)
        WHERE e.group_id = $group_id AND e.embedding IS NOT NULL
        RETURN e.uuid AS uuid, e.name AS name, e.embedding AS embedding
        ORDER BY e.created_at DESC
        LIMIT $limit
        """

        async with driver.session() as session:
            result = await session.run(
                query, {"group_id": group_id, "limit": max_compare}
            )
            records = [record async for record in result]

        if not records:
            return DuplicateCheckResult(
                is_duplicate=False, max_similarity=0.0,
                message="無現有 episodes，跳過去重檢查",
            )

        # 逐一比較相似度
        max_sim = 0.0
        best_uuid = None
        best_name = None

        for record in records:
            existing_embedding = record["embedding"]
            if not existing_embedding:
                continue

            sim = cosine_similarity(new_embedding, existing_embedding)
            if sim > max_sim:
                max_sim = sim
                best_uuid = record["uuid"]
                best_name = record["name"]

        is_dup = max_sim >= threshold

        if is_dup:
            msg = (
                f"發現高度相似的記憶 (相似度: {max_sim:.3f}): "
                f"'{best_name}' (uuid: {best_uuid})"
            )
            logger.info(msg)
        else:
            msg = f"未發現重複記憶 (最高相似度: {max_sim:.3f})"

        return DuplicateCheckResult(
            is_duplicate=is_dup,
            max_similarity=round(max_sim, 4),
            similar_episode_uuid=best_uuid if is_dup else None,
            similar_episode_name=best_name if is_dup else None,
            message=msg,
        )

    except Exception as e:
        logger.warning(f"去重檢查失敗，跳過: {e}")
        return DuplicateCheckResult(
            is_duplicate=False, max_similarity=0.0,
            message=f"去重檢查失敗: {str(e)[:200]}",
        )
