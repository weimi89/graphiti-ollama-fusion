#!/usr/bin/env python3
"""
嘗試復現複雜實體關係的 cosine similarity 錯誤
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType

async def reproduce_error():
    """嘗試復現 cosine similarity 錯誤"""

    neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
    neo4j_password = os.environ.get('NEO4J_PASSWORD', '24927108')

    print(f"🧪 嘗試復現複雜實體關係的 cosine similarity 錯誤")
    print(f"連接到: {neo4j_uri}")

    try:
        # 使用我們的自定義 Ollama 客戶端
        import sys
        sys.path.append('/Users/RD-CAT/MCP/graphiti')
        from ollama_graphiti_client import OptimizedOllamaClient
        from ollama_embedder import OllamaEmbedder

        # 初始化自定義組件
        llm_client = OptimizedOllamaClient(
            model="qwen2.5:7b",
            base_url="http://localhost:11434"
        )

        embedder = OllamaEmbedder(
            model="nomic-embed-text:v1.5",
            base_url="http://localhost:11434"
        )

        graphiti = Graphiti(
            neo4j_uri,
            neo4j_user,
            neo4j_password,
            llm_client=llm_client,
            embedder=embedder
        )

        print("\n1️⃣ 清理舊資料...")
        # 清理現有測試資料
        await graphiti.driver.execute_query("MATCH (n {group_id: 'cosine_test'}) DETACH DELETE n")

        print("✅ 清理完成")

        print("\n2️⃣ 添加複雜的測試記憶...")

        # 測試用例 1: 複雜的技術討論，包含多個實體和關係
        complex_episode = """
        今天團隊討論了新的架構設計，決定使用 React 18 的 Concurrent Features 來優化使用者介面的回應性。
        John 提出使用 Suspense 來處理非同步資料載入，而 Sarah 建議整合 TypeScript 以提供更好的類型安全。
        我們還討論了如何使用 GraphQL 來優化 API 查詢效能，並且考慮使用 Redis 作為快取層來減少資料庫負載。
        技術決策包括：前端使用 Next.js 框架，後端採用 Node.js 配合 Express，資料庫選擇 PostgreSQL。
        """

        try:
            print(f"   添加複雜記憶: {complex_episode[:100]}...")
            await graphiti.add_episode(
                name="複雜技術架構討論",
                episode_body=complex_episode,
                source=EpisodeType.text,
                reference_time=datetime.now(timezone.utc),
                source_description="團隊會議記錄",
                group_id="cosine_test"
            )
            print("   ✅ 複雜記憶添加成功")

        except Exception as e:
            print(f"   ❌ 添加複雜記憶時發生錯誤: {str(e)}")
            if "cosine" in str(e).lower():
                print(f"   🎯 發現 cosine similarity 錯誤！")
                print(f"   錯誤詳情: {str(e)}")
                return True  # 成功復現錯誤

        print("\n3️⃣ 添加相關聯的後續記憶...")

        # 測試用例 2: 相關的後續討論，會創建更複雜的實體網絡
        followup_episode = """
        經過上次討論後，John 完成了 React Suspense 的 POC 實作。Sarah 設定好了 TypeScript 配置，
        並且整合了 ESLint 和 Prettier 來確保程式碼品質。我們發現 GraphQL 的 N+1 查詢問題，
        決定使用 DataLoader 來解決。Redis 快取策略也已經實作完成，顯著提升了 API 回應時間。
        同時 Tom 負責設定 PostgreSQL 的索引優化，Maria 完成了 Next.js 的 SSR 配置。
        """

        try:
            print(f"   添加後續記憶: {followup_episode[:100]}...")
            await graphiti.add_episode(
                name="技術實作進度更新",
                episode_body=followup_episode,
                source=EpisodeType.text,
                reference_time=datetime.now(timezone.utc),
                source_description="進度追蹤會議",
                group_id="cosine_test"
            )
            print("   ✅ 後續記憶添加成功")

        except Exception as e:
            print(f"   ❌ 添加後續記憶時發生錯誤: {str(e)}")
            if "cosine" in str(e).lower():
                print(f"   🎯 發現 cosine similarity 錯誤！")
                print(f"   錯誤詳情: {str(e)}")
                return True

        print("\n4️⃣ 測試搜索功能...")

        # 測試搜索功能，這可能會觸發 cosine similarity 錯誤
        try:
            print("   搜索技術相關節點...")
            search_results = await graphiti.search(
                query="React TypeScript 技術架構",
                group_id="cosine_test",
                limit=5
            )
            print(f"   ✅ 搜索成功，找到 {len(search_results)} 個結果")

            for i, result in enumerate(search_results):
                print(f"   - 結果 {i+1}: {result[:100]}...")

        except Exception as e:
            print(f"   ❌ 搜索時發生錯誤: {str(e)}")
            if "cosine" in str(e).lower():
                print(f"   🎯 發現 cosine similarity 錯誤！")
                print(f"   錯誤詳情: {str(e)}")
                return True

        print("\n5️⃣ 測試實體相關查詢...")

        # 測試可能觸發實體去重的查詢
        try:
            print("   查詢實體資訊...")
            entity_search = await graphiti.search(
                query="John Sarah 開發者",
                group_id="cosine_test",
                limit=3
            )
            print(f"   ✅ 實體查詢成功，找到 {len(entity_search)} 個結果")

        except Exception as e:
            print(f"   ❌ 實體查詢時發生錯誤: {str(e)}")
            if "cosine" in str(e).lower():
                print(f"   🎯 發現 cosine similarity 錯誤！")
                print(f"   錯誤詳情: {str(e)}")
                return True

        print("\n6️⃣ 檢查生成的實體和關係...")

        # 檢查生成的資料結構
        entity_count_query = "MATCH (e:Entity {group_id: 'cosine_test'}) RETURN count(e) as count"
        entity_count = await graphiti.driver.execute_query(entity_count_query)
        entity_num = entity_count.records[0]['count'] if entity_count.records else 0

        relation_count_query = "MATCH ()-[r:RELATES_TO {group_id: 'cosine_test'}]-() RETURN count(r) as count"
        relation_count = await graphiti.driver.execute_query(relation_count_query)
        relation_num = relation_count.records[0]['count'] if relation_count.records else 0

        print(f"   生成了 {entity_num} 個實體和 {relation_num} 個關係")

        if entity_num > 0 and relation_num > 0:
            print("   ✅ 成功生成複雜的實體關係網絡")
            print("   ❓ 沒有觸發 cosine similarity 錯誤")
            print("   💡 可能錯誤只在特定條件下出現")
        else:
            print("   ⚠️ 沒有生成預期的實體和關係")

        print("\n7️⃣ 嘗試更複雜的多重記憶...")

        # 添加更多記憶來增加複雜度
        additional_episodes = [
            "專案經理 Alice 安排了下週的程式碼審查，重點檢查 React hooks 的使用和 TypeScript 型別定義。",
            "資深工程師 Bob 分享了 GraphQL Federation 的最佳實踐，建議將 API 拆分為多個微服務。",
            "UI/UX 設計師 Carol 提供了新的設計系統，需要整合到 React 元件庫中。",
            "DevOps 工程師 Dave 完成了 CI/CD 管道設定，包含 TypeScript 編譯和測試自動化。"
        ]

        for i, episode in enumerate(additional_episodes):
            try:
                print(f"   添加記憶 {i+1}/4: {episode[:50]}...")
                await graphiti.add_episode(
                    name=f"額外技術討論 {i+1}",
                    episode_body=episode,
                    source=EpisodeType.text,
                    reference_time=datetime.now(timezone.utc),
                    source_description=f"會議記錄 {i+1}",
                    group_id="cosine_test"
                )
                print(f"   ✅ 記憶 {i+1} 添加成功")

            except Exception as e:
                print(f"   ❌ 添加記憶 {i+1} 時發生錯誤: {str(e)}")
                if "cosine" in str(e).lower():
                    print(f"   🎯 在第 {i+1} 個記憶時發現 cosine similarity 錯誤！")
                    print(f"   錯誤詳情: {str(e)}")
                    return True

        print("\n8️⃣ 最終檢查...")

        # 最終統計
        final_entity_count = await graphiti.driver.execute_query(entity_count_query)
        final_entity_num = final_entity_count.records[0]['count'] if final_entity_count.records else 0

        final_relation_count = await graphiti.driver.execute_query(relation_count_query)
        final_relation_num = final_relation_count.records[0]['count'] if final_relation_count.records else 0

        print(f"   最終生成: {final_entity_num} 個實體, {final_relation_num} 個關係")
        print(f"   ✅ 測試完成，沒有發現 cosine similarity 錯誤")
        print(f"   💡 可能需要特定的資料組合才能觸發錯誤")

        await graphiti.driver.close()

    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {str(e)}")
        if "cosine" in str(e).lower():
            print(f"🎯 成功復現 cosine similarity 錯誤！")
            print(f"錯誤詳情: {str(e)}")
            return True
        else:
            print(f"❌ 這不是 cosine similarity 錯誤")
            return False

    return False  # 沒有復現錯誤

if __name__ == "__main__":
    reproduced = asyncio.run(reproduce_error())
    if reproduced:
        print("\n🎯 成功復現錯誤！可以開始調查修復方案。")
        sys.exit(1)  # 表示發現問題
    else:
        print("\n✅ 沒有復現錯誤，系統可能已經修復或需要其他條件。")
        sys.exit(0)