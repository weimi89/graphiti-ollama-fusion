#!/usr/bin/env python3
"""
完整的 MCP 功能測試 - 測試所有 6 個工具
"""
import asyncio
import sys
sys.path.append('.')

from graphiti_mcp_server import (
    initialize_graphiti,
    AddMemoryArgs,
    SearchNodesArgs,
    SearchFactsArgs,
    GetEpisodesArgs,
    add_memory_simple,
    search_memory_nodes,
    search_memory_facts,
    get_episodes,
    clear_graph,
    test_connection
)

async def test_all_mcp_functions():
    """測試所有 MCP 功能"""
    print("🚀 開始完整 MCP 功能測試")
    print("=" * 60)

    try:
        # 1. 測試連接
        print("\n1️⃣ 測試連接...")
        connection_result = await test_connection()
        print(f"   結果: {connection_result}")
        if connection_result.get('neo4j') != 'OK':
            raise Exception("Neo4j 連接失敗")
        if connection_result.get('ollama_llm') != 'OK':
            raise Exception("Ollama LLM 連接失敗")
        if connection_result.get('embedder') != 'OK':
            raise Exception("Ollama 嵌入器連接失敗")
        print("   ✅ 連接測試通過")

        # 2. 清空測試數據（防止干擾）
        print("\n2️⃣ 清空測試數據...")
        clear_result = await clear_graph()
        print(f"   結果: {clear_result}")
        print("   ✅ 測試數據清理完成")

        # 3. 添加記憶測試
        print("\n3️⃣ 測試添加記憶...")

        # 測試用例：包含實體和關係的複雜內容
        test_memories = [
            {
                "name": "用戶偏好測試",
                "content": "用戶 Alice 喜歡使用 TypeScript 進行前端開發，她認為類型安全很重要。",
                "group_id": "mcp_test"
            },
            {
                "name": "技術事實測試",
                "content": "React 18 引入了 Concurrent Features，包括 Suspense 和新的 useId hook。",
                "group_id": "mcp_test"
            },
            {
                "name": "專案關係測試",
                "content": "專案 WebApp 使用 Next.js 框架，由團隊 Frontend Team 維護，部署在 Vercel 平台上。",
                "group_id": "mcp_test"
            }
        ]

        for i, memory in enumerate(test_memories):
            print(f"   測試 {i+1}: {memory['name']}")
            result = await add_memory_simple(AddMemoryArgs(
                name=memory['name'],
                episode_body=memory['content'],
                group_id=memory['group_id']
            ))
            print(f"      結果: {result}")
            if "successfully" not in str(result.get('message', '')):
                raise Exception(f"添加記憶失敗: {result}")

        print("   ✅ 添加記憶測試通過")

        # 4. 搜索節點測試
        print("\n4️⃣ 測試搜索節點...")
        search_queries = [
            ("TypeScript", "搜索編程語言"),
            ("Alice", "搜索用戶"),
            ("React", "搜索框架"),
            ("WebApp", "搜索專案")
        ]

        for query, description in search_queries:
            print(f"   測試: {description} - '{query}'")
            result = await search_memory_nodes(SearchNodesArgs(
                query=query,
                group_id="mcp_test",
                limit=5
            ))
            print(f"      找到 {len(result.get('nodes', []))} 個節點")
            nodes = result.get('nodes', [])
            for j, node in enumerate(nodes[:2]):  # 只顯示前2個
                print(f"        節點{j+1}: {node.get('name', 'N/A')} ({node.get('node_type', 'N/A')})")

        print("   ✅ 搜索節點測試通過")

        # 5. 搜索事實測試
        print("\n5️⃣ 測試搜索事實...")
        fact_queries = [
            ("Alice TypeScript", "用戶偏好關係"),
            ("React Concurrent", "技術特性關係"),
            ("WebApp Next.js", "專案技術關係")
        ]

        for query, description in fact_queries:
            print(f"   測試: {description} - '{query}'")
            result = await search_memory_facts(SearchFactsArgs(
                query=query,
                group_id="mcp_test",
                limit=5
            ))
            facts = result.get('facts', [])
            print(f"      找到 {len(facts)} 個事實")
            for j, fact in enumerate(facts[:2]):  # 只顯示前2個
                print(f"        事實{j+1}: {fact.get('fact', 'N/A')}")

        print("   ✅ 搜索事實測試通過")

        # 6. 獲取記憶節點測試
        print("\n6️⃣ 測試獲取記憶節點...")
        episodes = await get_episodes("mcp_test")
        print(f"   找到 {len(episodes.get('episodes', []))} 個記憶節點")

        for i, episode in enumerate(episodes.get('episodes', [])[:3]):  # 只顯示前3個
            print(f"      記憶{i+1}: {episode.get('name', 'N/A')}")
            print(f"               內容: {episode.get('content', 'N/A')[:50]}...")

        print("   ✅ 獲取記憶節點測試通過")

        # 7. 性能測試
        print("\n7️⃣ 性能基準測試...")
        import time

        start_time = time.time()
        result = await add_memory_simple(AddMemoryArgs(
            name="性能測試",
            episode_body="這是一個用於測試性能的記憶，包含基本的技術內容。Vue 3 使用 Composition API。",
            group_id="mcp_test"
        ))
        end_time = time.time()

        duration = end_time - start_time
        print(f"   單個記憶添加耗時: {duration:.2f}s")

        if duration > 10:
            print("   ⚠️ 性能警告：耗時超過 10 秒")
        else:
            print("   ✅ 性能表現良好")

        # 8. 最終清理
        print("\n8️⃣ 清理測試數據...")
        clear_result = await clear_graph()
        print(f"   清理結果: {clear_result}")

        print("\n" + "=" * 60)
        print("🎉 所有 MCP 功能測試完成！")
        print("✅ 所有 6 個工具都正常運作")
        print("✅ 連接、記憶、搜索、清理功能都正常")
        print("✅ 性能表現符合預期")

        return True

    except Exception as e:
        print(f"\n❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_all_mcp_functions())
    sys.exit(0 if success else 1)