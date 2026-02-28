#!/usr/bin/env python3
"""
手動整合測試
============

從源碼模組搬移過來的整合測試函數。
這些測試需要 Neo4j 和 Ollama 服務運行中，不適合自動化 CI 執行。

用法：
    # 執行全部整合測試
    uv run python tests/test_integration_manual.py

    # 只測試嵌入器
    uv run python tests/test_integration_manual.py --embedder

    # 只測試 LLM + Graphiti
    uv run python tests/test_integration_manual.py --graphiti

    # 只測試安全記憶
    uv run python tests/test_integration_manual.py --safe-memory
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime, timezone

# 確保專案根目錄在 sys.path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


async def test_ollama_embedder() -> bool:
    """
    測試 Ollama 嵌入器。

    Returns:
        bool: 所有測試通過返回 True
    """
    from src.ollama_embedder import OllamaEmbedder

    print("測試 Ollama 嵌入器")
    print("=" * 50)

    embedder = OllamaEmbedder(
        model="nomic-embed-text:v1.5", base_url="http://localhost:11434"
    )

    # 測試連接
    print("\n1. 測試連接...")
    connected = await embedder.test_connection()
    if not connected:
        print("連接失敗，請確保 Ollama 正在運行")
        return False

    # 測試單一字串嵌入
    print("\n2. 測試單一字串嵌入...")
    single_text = "TypeScript 是 JavaScript 的超集"
    single_embedding = await embedder.create(single_text)

    if (
        isinstance(single_embedding, list)
        and single_embedding
        and isinstance(single_embedding[0], float)
    ):
        print(f"成功！嵌入維度: {len(single_embedding)}")
        print(f"前5個值: {single_embedding[:5]}")
    else:
        print("單一字串嵌入失敗")
        return False

    # 測試列表嵌入
    print("\n3. 測試列表嵌入...")
    list_embedding = await embedder.create(["TypeScript 是 JavaScript 的超集"])

    if (
        isinstance(list_embedding, list)
        and list_embedding
        and isinstance(list_embedding[0], float)
    ):
        print(f"成功！嵌入維度: {len(list_embedding)}")
    else:
        print("列表嵌入失敗")
        return False

    # 測試批量嵌入
    print("\n4. 測試批量嵌入...")
    batch_texts = [
        "React 18 引入了 Concurrent Features",
        "API 錯誤處理最佳實踐",
        "用戶偏好使用 TypeScript",
    ]
    batch_embeddings = await embedder.create_bulk(batch_texts, batch_size=2)

    if len(batch_embeddings) == len(batch_texts):
        print(f"成功嵌入 {len(batch_embeddings)} 個文本")
        for i, text in enumerate(batch_texts):
            print(f"- '{text[:30]}...' -> 維度 {len(batch_embeddings[i])}")
    else:
        print("批量嵌入失敗")
        return False

    # 獲取模型資訊
    print("\n5. 獲取模型資訊...")
    model_info = await embedder.get_model_info()
    if "error" not in model_info:
        print(f"模型: {embedder.model}")
        if "modelfile" in model_info:
            lines = model_info["modelfile"].split("\n")[:3]
            for line in lines:
                if line:
                    print(f"- {line}")

    print("\n所有測試通過！")
    return True


async def test_graphiti_integration() -> bool:
    """Graphiti + Ollama LLM 整合測試。"""
    from graphiti_core import Graphiti
    from graphiti_core.llm_client.config import LLMConfig
    from src.ollama_embedder import OllamaEmbedder
    from src.ollama_graphiti_client import OptimizedOllamaClient, SimpleCrossEncoder

    print("=" * 70)
    print("優化的 Ollama + Graphiti 解決方案測試")
    print("=" * 70)

    print("\n環境配置:")
    print(f"  Neo4j URI: {os.getenv('NEO4J_URI', 'bolt://localhost:7687')}")
    print(f"  Neo4j User: {os.getenv('NEO4J_USER', 'neo4j')}")
    print("  Model: qwen2.5:14b")
    print("  Embedder: nomic-embed-text:v1.5")

    try:
        # 初始化 LLM
        print("\n初始化 Ollama LLM...")
        llm_config = LLMConfig(
            api_key="not-needed",
            model="qwen2.5:14b",
            base_url="http://localhost:11434",
            temperature=0.1,
        )
        llm_client = OptimizedOllamaClient(llm_config)
        print("  LLM 初始化成功")

        # 初始化嵌入器
        print("\n初始化嵌入器...")
        embedder = OllamaEmbedder(
            model="nomic-embed-text:v1.5", base_url="http://localhost:11434"
        )
        if not await embedder.test_connection():
            print("  嵌入器連接失敗")
            return False
        print("  嵌入器初始化成功")

        # 初始化 Cross-encoder
        print("\n初始化 Cross-encoder...")
        cross_encoder = SimpleCrossEncoder()
        print("  Cross-encoder 初始化成功")

        # 初始化 Graphiti
        print("\n初始化 Graphiti...")
        graphiti = Graphiti(
            uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            user=os.getenv("NEO4J_USER", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", "password"),
            llm_client=llm_client,
            embedder=embedder,
            cross_encoder=cross_encoder,
        )

        await graphiti.build_indices_and_constraints()
        print("  Graphiti 初始化成功")

        # 添加測試記憶
        print("\n添加測試記憶...")
        test_episodes = [
            {"name": "用戶偏好", "content": "用戶 RD-CAT 偏好使用 TypeScript 進行開發。"},
            {"name": "技術知識", "content": "React 18 引入了 Concurrent Features。"},
            {"name": "最佳實踐", "content": "API 錯誤處理應該包含錯誤日誌和重試機制。"},
        ]

        for episode in test_episodes:
            print(f"  添加: {episode['name']}")
            try:
                await graphiti.add_episode(
                    name=episode["name"],
                    episode_body=episode["content"],
                    source_description="Ollama 測試",
                    reference_time=datetime.now(timezone.utc),
                )
            except Exception as e:
                print(f"    錯誤: {e}")

        # 測試搜索
        print("\n測試搜索功能:")
        queries = ["TypeScript", "React", "錯誤處理"]

        for query in queries:
            print(f"\n  搜索: '{query}'")
            try:
                results = await graphiti.search(query=query, num_results=3)
                print(f"    找到 {len(results)} 個結果" if results else "    無結果")
            except Exception as e:
                print(f"    錯誤: {str(e)[:30]}...")

        print("\n" + "=" * 70)
        print("測試完成！")
        print("=" * 70)

    except Exception as e:
        print(f"\n錯誤: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        if "graphiti" in locals():
            await graphiti.close()
            print("\n連接已關閉")

    return True


async def test_safe_memory_method() -> bool:
    """
    測試安全記憶添加方法。

    執行一系列測試案例，驗證安全記憶添加功能的穩定性。
    """
    from graphiti_core import Graphiti
    from graphiti_core.llm_client.config import LLMConfig
    from src.config import load_config
    from src.ollama_embedder import OllamaEmbedder
    from src.ollama_graphiti_client import OptimizedOllamaClient
    from src.safe_memory_add import safe_add_memory

    logger = logging.getLogger(__name__)

    try:
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


def main():
    parser = argparse.ArgumentParser(description="Graphiti 手動整合測試")
    parser.add_argument("--embedder", action="store_true", help="只測試嵌入器")
    parser.add_argument("--graphiti", action="store_true", help="只測試 Graphiti 整合")
    parser.add_argument("--safe-memory", action="store_true", help="只測試安全記憶")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    run_all = not (args.embedder or args.graphiti or args.safe_memory)
    all_passed = True

    if run_all or args.embedder:
        print("\n" + "=" * 70)
        print("[1/3] Ollama 嵌入器測試")
        print("=" * 70)
        if not asyncio.run(test_ollama_embedder()):
            all_passed = False

    if run_all or args.graphiti:
        print("\n" + "=" * 70)
        print("[2/3] Graphiti 整合測試")
        print("=" * 70)
        if not asyncio.run(test_graphiti_integration()):
            all_passed = False

    if run_all or args.safe_memory:
        print("\n" + "=" * 70)
        print("[3/3] 安全記憶添加測試")
        print("=" * 70)
        if not asyncio.run(test_safe_memory_method()):
            all_passed = False

    print("\n" + "=" * 70)
    print("全部通過！" if all_passed else "部分測試失敗")
    print("=" * 70)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
