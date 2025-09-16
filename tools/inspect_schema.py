#!/usr/bin/env python3
"""
檢查 Neo4j 資料庫中的實際 schema 和屬性名稱
"""

import asyncio
import os
import sys
from graphiti_core import Graphiti

async def inspect_schema():
    """檢查資料庫的 schema"""

    neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
    neo4j_password = os.environ.get('NEO4J_PASSWORD', '24927108')

    print(f"🔍 檢查 Neo4j 資料庫 Schema")
    print(f"連接到: {neo4j_uri}")

    try:
        graphiti = Graphiti(neo4j_uri, neo4j_user, neo4j_password)

        print("\n1️⃣ 檢查所有標籤...")
        labels_query = "CALL db.labels() YIELD label RETURN label"
        labels_results = await graphiti.driver.execute_query(labels_query)

        print("   可用標籤:")
        for record in labels_results.records:
            print(f"   - {record['label']}")

        print("\n2️⃣ 檢查所有屬性...")
        props_query = "CALL db.propertyKeys() YIELD propertyKey RETURN propertyKey ORDER BY propertyKey"
        props_results = await graphiti.driver.execute_query(props_query)

        print("   可用屬性:")
        embedding_props = []
        for record in props_results.records:
            prop = record['propertyKey']
            print(f"   - {prop}")
            if 'embedding' in prop.lower():
                embedding_props.append(prop)

        print(f"\n3️⃣ 嵌入相關屬性: {embedding_props}")

        print("\n4️⃣ 檢查實際節點結構...")

        # 檢查 Entity 節點
        entity_sample_query = "MATCH (e:Entity) RETURN keys(e) as properties LIMIT 1"
        entity_sample_results = await graphiti.driver.execute_query(entity_sample_query)

        if entity_sample_results.records:
            print("   Entity 節點屬性:")
            for prop in entity_sample_results.records[0]['properties']:
                print(f"   - {prop}")
        else:
            print("   沒有找到 Entity 節點")

        # 檢查關係
        edge_sample_query = "MATCH ()-[r:RELATES_TO]-() RETURN keys(r) as properties LIMIT 1"
        edge_sample_results = await graphiti.driver.execute_query(edge_sample_query)

        if edge_sample_results.records:
            print("   RELATES_TO 關係屬性:")
            for prop in edge_sample_results.records[0]['properties']:
                print(f"   - {prop}")

        # 檢查 Episodic 節點
        episodic_sample_query = "MATCH (e:Episodic) RETURN keys(e) as properties LIMIT 1"
        episodic_sample_results = await graphiti.driver.execute_query(episodic_sample_query)

        if episodic_sample_results.records:
            print("   Episodic 節點屬性:")
            for prop in episodic_sample_results.records[0]['properties']:
                print(f"   - {prop}")

        print("\n5️⃣ 檢查所有節點和關係數量...")
        count_query = """
        MATCH (n)
        RETURN labels(n)[0] as label, count(n) as count
        ORDER BY count DESC
        """
        count_results = await graphiti.driver.execute_query(count_query)

        print("   節點統計:")
        for record in count_results.records:
            print(f"   - {record['label']}: {record['count']} 個")

        # 檢查關係統計
        rel_count_query = """
        MATCH ()-[r]-()
        RETURN type(r) as relationship_type, count(r) as count
        """
        rel_count_results = await graphiti.driver.execute_query(rel_count_query)

        print("   關係統計:")
        for record in rel_count_results.records:
            print(f"   - {record['relationship_type']}: {record['count']} 個")

        await graphiti.driver.close()

    except Exception as e:
        print(f"❌ 檢查過程中發生錯誤: {str(e)}")
        return False

    return True

if __name__ == "__main__":
    success = asyncio.run(inspect_schema())
    sys.exit(0 if success else 1)