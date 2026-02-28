#!/usr/bin/env python3
"""
安全記憶添加模組
================

提供安全的記憶添加方法，完全繞過實體提取流程以避免 IndexError。

此模組的主要目的是在 Graphiti 的實體提取過程可能產生錯誤時，
提供一個可靠的替代方案，直接建立 EpisodicNode 節點。

主要功能：
    - safe_add_memory: 安全添加記憶（跳過實體提取）

使用場景：
    - 當完整的實體提取流程產生 IndexError 時
    - 需要快速可靠地儲存記憶而不需要實體關係時
    - 批量匯入資料時避免處理失敗
"""

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from graphiti_core.nodes import EpisodicNode, EpisodeType

if TYPE_CHECKING:
    from graphiti_core import Graphiti

logger = logging.getLogger(__name__)


async def safe_add_memory(
    graphiti_client: "Graphiti",
    name: str,
    content: str,
    group_id: str = "safe_test",
    source_description: str = "Safe Memory Addition",
) -> dict:
    """
    安全添加記憶到知識圖譜。

    此方法直接建立 EpisodicNode，完全跳過可能導致 IndexError 的實體提取流程。
    適合在需要高可靠性但不需要實體關係提取的場景使用。

    Args:
        graphiti_client: 已初始化的 Graphiti 客戶端實例
        name: 記憶片段的名稱
        content: 記憶片段的內容
        group_id: 記憶分組 ID，用於組織不同領域的記憶
        source_description: 記憶來源的描述

    Returns:
        dict: 操作結果字典
            - success (bool): 操作是否成功
            - uuid (str): 成功時返回記憶片段的 UUID
            - message (str): 結果訊息
            - error (str): 失敗時的錯誤訊息

    Examples:
        >>> from graphiti_core import Graphiti
        >>> graphiti = await initialize_graphiti()
        >>> result = await safe_add_memory(
        ...     graphiti,
        ...     name="會議記錄",
        ...     content="今天討論了新產品發布計畫",
        ...     group_id="meetings"
        ... )
        >>> if result["success"]:
        ...     print(f"記憶已儲存，UUID: {result['uuid']}")

    Note:
        此方法不會建立實體節點或關係邊，僅建立記憶片段節點。
        如果需要完整的實體提取功能，請使用 graphiti.add_episode()。
    """
    try:
        logger.info(f"安全添加記憶: {name}")

        # 直接建立 EpisodicNode，不經過 add_episode
        episode_node = EpisodicNode(
            name=name,
            group_id=group_id,
            labels=[],
            source=EpisodeType.text,
            content=content,
            source_description=source_description,
            created_at=datetime.now(timezone.utc),
            valid_at=datetime.now(timezone.utc),
        )

        # 直接保存到資料庫
        await episode_node.save(graphiti_client.driver)

        logger.info(f"安全記憶添加成功: {episode_node.uuid}")

        return {
            "success": True,
            "uuid": episode_node.uuid,
            "message": f"記憶 '{name}' 安全添加成功",
        }

    except Exception as e:
        logger.error(f"安全記憶添加失敗: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"記憶 '{name}' 添加失敗",
        }
