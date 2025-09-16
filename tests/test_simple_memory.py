#!/usr/bin/env python3
"""
簡單的記憶測試 - 驗證修正是否有效
"""
import asyncio
import sys
sys.path.append('.')

from graphiti_mcp_server import (
    initialize_graphiti,
    AddMemoryArgs,
    add_memory_simple,
    clear_graph,
    test_connection
)

async def test_simple_memory():
    """測試簡單的記憶添加"""
    print("🧪 測試簡單記憶添加")
    print("=" * 40)

    try:
        # 1. 測試連接
        connection_result = await test_connection()
        if connection_result.get('neo4j') != 'OK':
            raise Exception("Neo4j 連接失敗")

        # 2. 清空數據
        await clear_graph()
        print("✅ 資料庫已清理")

        # 3. 測試非常簡單的內容
        simple_tests = [
            {
                "name": "基本測試",
                "content": "這是基本測試",
                "group_id": "simple_test"
            },
            {
                "name": "用戶測試",
                "content": "用戶 Bob 使用 Python",
                "group_id": "simple_test"
            }
        ]

        for i, test in enumerate(simple_tests, 1):
            print(f"\n{i}. 測試: {test['name']}")
            print(f"   內容: {test['content']}")

            try:
                result = await add_memory_simple(AddMemoryArgs(
                    name=test['name'],
                    episode_body=test['content'],
                    group_id=test['group_id']
                ))

                if result.get('error'):
                    print(f"   ❌ 失敗: {result.get('message')}")
                    return False
                else:
                    print(f"   ✅ 成功: {result.get('message')}")
                    print(f"   節點: {result.get('nodes_extracted', 0)}, 邊: {result.get('edges_created', 0)}")

            except Exception as e:
                print(f"   ❌ 例外: {str(e)}")
                return False

        print(f"\n✅ 所有簡單測試都通過了！")
        return True

    except Exception as e:
        print(f"\n❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_simple_memory())
    sys.exit(0 if success else 1)