#!/usr/bin/env python3
"""
專門測試 cosine similarity 錯誤
"""
import asyncio
import os
import sys
sys.path.append('.')

from graphiti_mcp_server import initialize_graphiti, AddMemoryArgs, add_memory_simple

async def test_cosine_similarity():
    """測試 cosine similarity 問題"""
    print("🔍 測試 cosine similarity 問題...")

    try:
        # 初始化
        print("1. 初始化 Graphiti...")
        graphiti = await initialize_graphiti()
        print("   ✅ 初始化成功")

        # 測試各種可能導致問題的輸入
        test_cases = [
            {
                "name": "空字符串測試",
                "episode_body": "",
                "group_id": "test_empty"
            },
            {
                "name": "空白字符串測試",
                "episode_body": "   ",
                "group_id": "test_whitespace"
            },
            {
                "name": "單個字符測試",
                "episode_body": "a",
                "group_id": "test_single"
            },
            {
                "name": "正常內容測試",
                "episode_body": "這是一個正常的測試內容，包含足夠的信息來生成有效的向量嵌入。",
                "group_id": "test_normal"
            },
            {
                "name": "特殊字符測試",
                "episode_body": "!@#$%^&*()_+-=[]{}|;':\",./<>?",
                "group_id": "test_special"
            }
        ]

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. 測試: {test_case['name']}")
            print(f"   內容: '{test_case['episode_body']}'")

            try:
                result = await add_memory_simple(AddMemoryArgs(
                    name=test_case['name'],
                    episode_body=test_case['episode_body'],
                    group_id=test_case['group_id']
                ))
                print(f"   ✅ 成功: {result}")

            except Exception as e:
                print(f"   ❌ 錯誤: {str(e)}")

                # 如果是 cosine similarity 錯誤，提供詳細信息
                if "cosine" in str(e).lower() or "vector" in str(e).lower():
                    print(f"   🚨 這是向量相似度錯誤！")
                    print(f"   錯誤詳細: {type(e).__name__}: {str(e)}")

                    # 嘗試獲取更多調試信息
                    import traceback
                    print("   調用堆棧:")
                    traceback.print_exc()

    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_cosine_similarity())