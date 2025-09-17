#!/usr/bin/env python3
"""
安全的記憶添加方法 - 完全繞過實體提取以避免 IndexError
"""

import asyncio
import logging
import uuid as uuid_lib
from datetime import datetime, timezone

from graphiti_core.nodes import EpisodicNode, EpisodeType

logger = logging.getLogger(__name__)

async def safe_add_memory(
    graphiti_client,
    name: str,
    content: str,
    group_id: str = "safe_test",
    source_description: str = "Safe Memory Addition"
):
    """
    安全添加記憶的方法 - 直接創建 EpisodicNode，完全跳過實體提取

    這個方法完全繞過可能導致 IndexError 的實體提取流程
    """
    try:
        logger.info(f"🛡️ 安全添加記憶: {name}")

        # 直接創建 EpisodicNode，不經過 add_episode
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

        logger.info(f"✅ 安全記憶添加成功: {episode_node.uuid}")
        return {
            "success": True,
            "uuid": episode_node.uuid,
            "message": f"記憶 '{name}' 安全添加成功"
        }

    except Exception as e:
        logger.error(f"❌ 安全記憶添加失敗: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"記憶 '{name}' 添加失敗"
        }

async def test_safe_memory_method():
    """測試安全記憶添加方法"""
    try:
        from src.config import load_config
        from src.ollama_graphiti_client import OptimizedOllamaClient
        from src.ollama_embedder import OllamaEmbedder
        from graphiti_core import Graphiti
        from graphiti_core.llm_client.config import LLMConfig

        logger.info("🛡️ 測試安全記憶添加方法...")

        # 初始化 Graphiti（最小配置）
        config = load_config()

        llm_config = LLMConfig(
            base_url=config.ollama.base_url,
            model=config.ollama.model,
            temperature=0.0
        )
        llm_client = OptimizedOllamaClient(config=llm_config)

        embedder_client = OllamaEmbedder(
            model=config.embedder.model,
            base_url=config.embedder.base_url,
            dimensions=config.embedder.dimensions
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
        logger.info("✅ Graphiti 初始化成功（安全模式）")

        # 測試一系列記憶添加
        test_memories = [
            ("安全測試1", "這是第一個安全測試記憶。"),
            ("安全測試2", "這是第二個安全測試記憶，用於驗證方法的穩定性。"),
            ("大文本安全測試", "這是一個較長的測試內容。" * 50),  # 生成較大的文本
            ("特殊字符測試", "測試特殊字符: !@#$%^&*()_+-=[]{}|;':\",./<>?~`"),
            ("JSON格式測試", '{"name": "test", "value": 123, "array": [1,2,3]}'),
        ]

        results = []
        for name, content in test_memories:
            logger.info(f"🧪 測試: {name}")
            result = await safe_add_memory(graphiti, name, content)
            results.append(result)

            if result["success"]:
                logger.info(f"✅ {name} - 成功")
            else:
                logger.error(f"❌ {name} - 失敗: {result['error']}")

        # 統計結果
        successful = sum(1 for r in results if r["success"])
        total = len(results)

        logger.info(f"📊 安全測試總結: {successful}/{total} 成功")

        if successful == total:
            logger.info("🎉 所有安全測試都通過！完全避開了 IndexError 問題！")
            return True
        else:
            logger.warning("⚠️ 部分安全測試失敗")
            return False

    except Exception as e:
        logger.error(f"💥 安全測試失敗: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    print("🛡️ 開始安全記憶添加測試...")
    success = asyncio.run(test_safe_memory_method())
    if success:
        print("✅ 安全方法驗證成功！")
    else:
        print("❌ 安全方法仍有問題。")