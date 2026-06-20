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


async def store_episode_embedding(
    driver: Any, embedder: Any, uuid: str, content: str
) -> None:
    """為指定 Episodic 計算 content 嵌入並存入 e.embedding，供日後去重比對。

    graphiti-core 的 add_episode 只儲存 Episodic 的 content 文本、不計算其嵌入，
    導致 check_episode_similarity 查無可比對對象、去重永遠空轉。寫入記憶後以
    fire-and-forget 方式呼叫本函數補上嵌入，讓去重真正生效。
    """
    if not uuid or not content:
        return
    try:
        # OllamaEmbedder.create 接受 str 並回傳單一向量；勿傳 list[dict]
        emb = await embedder.create(content)
        if not emb:
            return
        async with driver.session() as session:
            await session.run(
                "MATCH (e:Episodic {uuid: $uuid}) SET e.embedding = $emb",
                {"uuid": uuid, "emb": emb},
            )
        logger.debug(f"已存入 Episodic 嵌入: {uuid}")
    except Exception as e:
        logger.warning(f"存 Episodic 嵌入失敗（不影響寫入）: {e}")


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
        # 生成新內容的嵌入（OllamaEmbedder.create 接受 str 回單一向量；
        # 過去誤傳 list[dict] 並取 [0]，使 new_embedding 變成單一 float，相似度全錯）
        new_embedding = await embedder.create(content)
        if not new_embedding:
            return DuplicateCheckResult(
                is_duplicate=False, max_similarity=0.0,
                message="無法生成嵌入向量，跳過去重檢查",
            )

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
