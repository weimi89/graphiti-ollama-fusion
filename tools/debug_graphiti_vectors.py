#!/usr/bin/env python3
"""
調試 Graphiti 內部向量處理
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
sys.path.append('/Users/RD-CAT/MCP/graphiti')
from ollama_graphiti_client import OptimizedOllamaClient
from ollama_embedder import OllamaEmbedder

async def debug_internal_vectors():
    """調試 Graphiti 內部向量處理"""

    neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
    neo4j_password = os.environ.get('NEO4J_PASSWORD', '24927108')

    print("🔍 調試 Graphiti 內部向量處理")
    print(f"連接到: {neo4j_uri}")

    try:
        # 初始化自定義組件
        from graphiti_core.llm_client.config import LLMConfig

        config = LLMConfig(
            model="qwen2.5:7b",
            base_url="http://localhost:11434"
        )
        llm_client = OptimizedOllamaClient(config)
        embedder = OllamaEmbedder()

        # 測試嵌入器單獨運行
        print("\n1️⃣ 測試嵌入器...")
        test_texts = ["Alice", "TypeScript", "React 18", "Concurrent Features"]
        embeddings = await embedder.create(test_texts)

        print(f"   生成了 {len(embeddings)} 個嵌入向量")
        for i, (text, emb) in enumerate(zip(test_texts, embeddings)):
            norm = sum(x*x for x in emb) ** 0.5
            print(f"   - '{text}': 維度={len(emb)}, 範數={norm:.6f}")

        # 檢查向量品質
        for i, emb in enumerate(embeddings):
            if any(x is None or x != x or abs(x) == float('inf') for x in emb):
                print(f"   ❌ 向量 {i} 包含無效值!")
            elif len(emb) != 768:
                print(f"   ❌ 向量 {i} 維度錯誤: {len(emb)}")
            elif sum(x*x for x in emb) ** 0.5 < 0.9 or sum(x*x for x in emb) ** 0.5 > 1.1:
                print(f"   ⚠️ 向量 {i} 範數異常: {sum(x*x for x in emb) ** 0.5:.6f}")
            else:
                print(f"   ✅ 向量 {i} 正常")

        print("\n2️⃣ 初始化 Graphiti...")
        graphiti = Graphiti(
            neo4j_uri,
            neo4j_user,
            neo4j_password,
            llm_client=llm_client,
            embedder=embedder
        )

        # 清理資料
        print("   清理測試資料...")
        await graphiti.driver.execute_query("MATCH (n {group_id: 'debug_test'}) DETACH DELETE n")

        print("\n3️⃣ 添加第一個記憶 (簡單)...")
        try:
            await graphiti.add_episode(
                name="簡單測試",
                episode_body="Alice 是一個開發者",
                source=EpisodeType.text,
                source_description="調試測試",
                reference_time=datetime.now(timezone.utc),
                group_id="debug_test"
            )
            print("   ✅ 第一個記憶添加成功")

            # 檢查生成的向量
            entity_check = await graphiti.driver.execute_query(
                "MATCH (e:Entity {group_id: 'debug_test'}) RETURN e.name, e.name_embedding, size(e.name_embedding) as size"
            )

            print(f"   生成了 {len(entity_check.records)} 個實體:")
            for record in entity_check.records:
                name = record['e.name']
                embedding = record['e.name_embedding']
                size = record['size']
                norm = sum(x*x for x in embedding) ** 0.5 if embedding else 0
                print(f"   - 實體 '{name}': 維度={size}, 範數={norm:.6f}")

        except Exception as e:
            print(f"   ❌ 第一個記憶失敗: {str(e)}")

        print("\n4️⃣ 添加第二個記憶 (可能觸發錯誤)...")
        try:
            await graphiti.add_episode(
                name="複雜測試",
                episode_body="Alice 使用 TypeScript 開發 React 應用程式，她很重視類型安全。",
                source=EpisodeType.text,
                source_description="調試測試",
                reference_time=datetime.now(timezone.utc),
                group_id="debug_test"
            )
            print("   ✅ 第二個記憶添加成功")

        except Exception as e:
            print(f"   ❌ 第二個記憶失敗: {str(e)}")
            if "cosine" in str(e).lower():
                print("   🎯 這是 cosine similarity 錯誤！")

                print("\n5️⃣ 檢查現有向量...")
                # 檢查資料庫中的所有向量
                all_entities = await graphiti.driver.execute_query(
                    "MATCH (e:Entity {group_id: 'debug_test'}) RETURN e.name, e.name_embedding"
                )

                print(f"   當前有 {len(all_entities.records)} 個實體")
                for i, record in enumerate(all_entities.records):
                    name = record['e.name']
                    embedding = record['e.name_embedding']

                    if embedding:
                        norm = sum(x*x for x in embedding) ** 0.5
                        has_invalid = any(x is None or x != x or abs(x) == float('inf') for x in embedding)
                        print(f"   實體 {i+1} '{name}': 維度={len(embedding)}, 範數={norm:.6f}, 無效值={has_invalid}")

                        if has_invalid:
                            print(f"     ❌ 發現無效值: {[x for x in embedding[:10] if x is None or x != x or abs(x) == float('inf')]}")
                    else:
                        print(f"   實體 {i+1} '{name}': 沒有嵌入向量")

                print("\n6️⃣ 手動測試 cosine similarity...")
                if len(all_entities.records) >= 2:
                    try:
                        cosine_test = await graphiti.driver.execute_query("""
                            MATCH (e1:Entity {group_id: 'debug_test'}), (e2:Entity {group_id: 'debug_test'})
                            WHERE e1.name_embedding IS NOT NULL
                              AND e2.name_embedding IS NOT NULL
                              AND e1.uuid <> e2.uuid
                            WITH e1, e2 LIMIT 1
                            RETURN e1.name, e2.name,
                                   vector.similarity.cosine(e1.name_embedding, e2.name_embedding) as similarity
                        """)

                        if cosine_test.records:
                            record = cosine_test.records[0]
                            print(f"   ✅ Cosine similarity 測試成功: {record['e1.name']} vs {record['e2.name']} = {record['similarity']}")
                        else:
                            print("   ⚠️ 沒有足夠的實體進行測試")

                    except Exception as cos_e:
                        print(f"   ❌ Cosine similarity 測試失敗: {str(cos_e)}")
                        print("   這確認了向量品質問題！")

        await graphiti.driver.close()

    except Exception as e:
        print(f"❌ 調試過程中發生錯誤: {str(e)}")
        return False

    return True

if __name__ == "__main__":
    success = asyncio.run(debug_internal_vectors())
    sys.exit(0 if success else 1)