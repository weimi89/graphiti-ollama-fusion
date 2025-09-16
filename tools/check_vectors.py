#!/usr/bin/env python3
"""
檢查 Neo4j 資料庫中的向量品質
發現並修復可能導致 cosine similarity 錯誤的無效向量
"""

import asyncio
import os
import sys
from graphiti_core import Graphiti
from graphiti_core.driver.neo4j_driver import Neo4jDriver

async def check_vectors():
    """檢查資料庫中的向量品質"""

    # 從環境變數獲取連接資訊
    neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
    neo4j_password = os.environ.get('NEO4J_PASSWORD', '24927108')

    print(f"🔍 檢查 Neo4j 資料庫中的向量品質")
    print(f"連接到: {neo4j_uri}")

    try:
        # 初始化 Graphiti
        graphiti = Graphiti(
            neo4j_uri,
            neo4j_user,
            neo4j_password
        )

        print("\n1️⃣ 檢查所有節點的嵌入向量...")

        # 檢查 Entity 節點的嵌入向量 (使用正確的屬性名稱)
        entity_query = """
        MATCH (e:Entity)
        WHERE e.name_embedding IS NOT NULL
        RETURN e.uuid, e.name, e.name_embedding, size(e.name_embedding) as embedding_size
        LIMIT 50
        """

        entity_results = await graphiti.driver.execute_query(entity_query)
        print(f"   找到 {len(entity_results.records)} 個 Entity 節點有嵌入向量")

        invalid_entity_vectors = []
        for record in entity_results.records:
            uuid = record['e.uuid']
            name = record['e.name']
            embedding = record['e.name_embedding']
            size = record['embedding_size']

            print(f"   - Entity '{name}' (UUID: {uuid[:8]}...): 向量維度 {size}")

            # 檢查向量品質
            if embedding:
                # 檢查是否為零向量
                vector_norm = sum(x*x for x in embedding) ** 0.5
                if vector_norm == 0.0:
                    print(f"     ⚠️ 零向量檢測到！")
                    invalid_entity_vectors.append((uuid, name, "zero_vector"))
                elif vector_norm < 1e-10:
                    print(f"     ⚠️ 向量範數過小: {vector_norm}")
                    invalid_entity_vectors.append((uuid, name, "small_norm"))
                elif any(not isinstance(x, (int, float)) or x != x for x in embedding):  # NaN check
                    print(f"     ⚠️ 無效數值檢測到！")
                    invalid_entity_vectors.append((uuid, name, "invalid_values"))
                else:
                    print(f"     ✅ 向量正常 (範數: {vector_norm:.6f})")

        print(f"\n2️⃣ 檢查所有邊的嵌入向量...")

        # 檢查 EntityEdge 的嵌入向量
        edge_query = """
        MATCH ()-[r:RELATES_TO]-()
        WHERE r.fact_embedding IS NOT NULL
        RETURN r.uuid, r.fact, r.fact_embedding, size(r.fact_embedding) as embedding_size
        LIMIT 50
        """

        edge_results = await graphiti.driver.execute_query(edge_query)
        print(f"   找到 {len(edge_results.records)} 個關係邊有嵌入向量")

        invalid_edge_vectors = []
        for record in edge_results.records:
            uuid = record['r.uuid']
            fact = record['r.fact']
            embedding = record['r.fact_embedding']
            size = record['embedding_size']

            print(f"   - 關係 '{fact[:50]}...' (UUID: {uuid[:8]}...): 向量維度 {size}")

            # 檢查向量品質
            if embedding:
                vector_norm = sum(x*x for x in embedding) ** 0.5
                if vector_norm == 0.0:
                    print(f"     ⚠️ 零向量檢測到！")
                    invalid_edge_vectors.append((uuid, fact, "zero_vector"))
                elif vector_norm < 1e-10:
                    print(f"     ⚠️ 向量範數過小: {vector_norm}")
                    invalid_edge_vectors.append((uuid, fact, "small_norm"))
                elif any(not isinstance(x, (int, float)) or x != x for x in embedding):
                    print(f"     ⚠️ 無效數值檢測到！")
                    invalid_edge_vectors.append((uuid, fact, "invalid_values"))
                else:
                    print(f"     ✅ 向量正常 (範數: {vector_norm:.6f})")

        print(f"\n3️⃣ 檢查 cosine similarity 函數...")

        # 測試 Neo4j 的 cosine similarity 函數
        if len(entity_results.records) >= 2:
            test_query = """
            MATCH (e1:Entity), (e2:Entity)
            WHERE e1.name_embedding IS NOT NULL
              AND e2.name_embedding IS NOT NULL
              AND e1.uuid <> e2.uuid
            WITH e1, e2 LIMIT 1
            RETURN e1.name, e2.name,
                   vector.similarity.cosine(e1.name_embedding, e2.name_embedding) as similarity
            """

            try:
                similarity_results = await graphiti.driver.execute_query(test_query)
                if similarity_results.records:
                    record = similarity_results.records[0]
                    print(f"   ✅ Cosine similarity 測試成功: {record['e1.name']} vs {record['e2.name']} = {record['similarity']}")
                else:
                    print(f"   ⚠️ 沒有找到足夠的向量進行 cosine similarity 測試")
            except Exception as e:
                print(f"   ❌ Cosine similarity 測試失敗: {str(e)}")
                print(f"   這可能是導致錯誤的根本原因！")

        print(f"\n4️⃣ 摘要報告")
        print("=" * 50)

        if invalid_entity_vectors:
            print(f"❌ 發現 {len(invalid_entity_vectors)} 個無效的實體向量:")
            for uuid, name, issue in invalid_entity_vectors:
                print(f"   - {name} ({uuid[:8]}...): {issue}")
        else:
            print("✅ 所有實體向量都正常")

        if invalid_edge_vectors:
            print(f"❌ 發現 {len(invalid_edge_vectors)} 個無效的關係向量:")
            for uuid, fact, issue in invalid_edge_vectors:
                print(f"   - {fact[:30]}... ({uuid[:8]}...): {issue}")
        else:
            print("✅ 所有關係向量都正常")

        # 建議修復措施
        if invalid_entity_vectors or invalid_edge_vectors:
            print(f"\n🔧 建議修復措施:")
            print("1. 清理無效向量資料")
            print("2. 重新生成有問題的嵌入向量")
            print("3. 確保嵌入器正確歸一化向量")

            # 提供清理腳本
            print(f"\n💡 執行以下查詢來清理無效向量:")
            if invalid_entity_vectors:
                print("// 刪除有問題的實體向量")
                for uuid, name, issue in invalid_entity_vectors:
                    print(f"MATCH (e:Entity {{uuid: '{uuid}'}}) SET e.summary_embedding = null;")

            if invalid_edge_vectors:
                print("// 刪除有問題的關係向量")
                for uuid, fact, issue in invalid_edge_vectors:
                    print(f"MATCH ()-[r:RELATES_TO {{uuid: '{uuid}'}}]-() SET r.fact_embedding = null;")

        await graphiti.driver.close()

    except Exception as e:
        print(f"❌ 檢查過程中發生錯誤: {str(e)}")
        return False

    return True

if __name__ == "__main__":
    success = asyncio.run(check_vectors())
    sys.exit(0 if success else 1)