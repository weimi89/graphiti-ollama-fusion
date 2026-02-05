#!/usr/bin/env python3
"""
安全記憶添加模組
================

提供安全的記憶添加方法，完全繞過實體提取流程以避免 IndexError。

此模組的主要目的是在 Graphiti 的實體提取過程可能產生錯誤時，
提供一個可靠的替代方案，直接建立 EpisodicNode 節點。

主要功能：
    - safe_add_memory: 安全添加記憶（跳過實體提取）
    - test_safe_memory_method: 測試安全記憶添加功能

使用場景：
    - 當完整的實體提取流程產生 IndexError 時
    - 需要快速可靠地儲存記憶而不需要實體關係時
    - 批量匯入資料時避免處理失敗
"""

import asyncio
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


async def test_safe_memory_method() -> bool:
    """
    測試安全記憶添加方法。

    執行一系列測試案例，驗證安全記憶添加功能的穩定性。

    Returns:
        bool: 所有測試都通過返回 True

    Test Cases:
        - 基本文字記憶
        - 長文字記憶
        - 特殊字符處理
        - JSON 格式資料
    """
    try:
        from src.config import load_config
        from src.ollama_graphiti_client import OptimizedOllamaClient
        from src.ollama_embedder import OllamaEmbedder
        from graphiti_core import Graphiti
        from graphiti_core.llm_client.config import LLMConfig

        logger.info("測試安全記憶添加方法...")

        # 初始化 Graphiti
        config = load_config()

        llm_config = LLMConfig(
            base_url=config.ollama.base_url,
            model=config.ollama.model,
            temperature=0.0,
        )
        llm_client = OptimizedOllamaClient(config=llm_config)

        embedder_client = OllamaEmbedder(
            model=config.embedder.model,
            base_url=config.embedder.base_url,
            dimensions=config.embedder.dimensions,
        )

        graphiti = Graphiti(
            uri=config.neo4j.uri,
            user=config.neo4j.user,
            password=config.neo4j.password,
            llm_client=llm_client,
            embedder=embedder_client,
            max_coroutines=3,
        )

        await graphiti.build_indices_and_constraints()
        logger.info("Graphiti 初始化成功（安全模式）")

        # 定義測試案例
        test_cases = [
            ("安全測試1", "這是第一個安全測試記憶。"),
            ("安全測試2", "這是第二個安全測試記憶，用於驗證方法的穩定性。"),
            ("大文本安全測試", "這是一個較長的測試內容。" * 50),
            ("特殊字符測試", "測試特殊字符: !@#$%^&*()_+-=[]{}|;':\",./<>?~`"),
            ("JSON格式測試", '{"name": "test", "value": 123, "array": [1,2,3]}'),
        ]

        # 執行測試
        results = []
        for name, content in test_cases:
            logger.info(f"測試: {name}")
            result = await safe_add_memory(graphiti, name, content)
            results.append(result)

            if result["success"]:
                logger.info(f"{name} - 成功")
            else:
                logger.error(f"{name} - 失敗: {result['error']}")

        # 統計結果
        successful = sum(1 for r in results if r["success"])
        total = len(results)

        logger.info(f"安全測試總結: {successful}/{total} 成功")

        if successful == total:
            logger.info("所有安全測試都通過！完全避開了 IndexError 問題！")
            return True
        else:
            logger.warning("部分安全測試失敗")
            return False

    except Exception as e:
        logger.error(f"安全測試失敗: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    print("開始安全記憶添加測試...")
    success = asyncio.run(test_safe_memory_method())
    print("安全方法驗證成功！" if success else "安全方法仍有問題。")
