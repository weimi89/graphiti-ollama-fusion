#!/usr/bin/env python3
"""
快速診斷測試 - 找出關鍵問題
"""
import asyncio
import time
from graphiti_mcp_server import (
    add_memory_simple, AddMemoryArgs,
    search_memory_nodes, SearchNodesArgs,
    test_connection,
    initialize_graphiti
)

class QuickDiagnostic:
    def __init__(self):
        self.issues = []

    async def test_connection_speed(self):
        """測試連接速度"""
        print("🔌 測試連接速度...")
        start_time = time.time()
        result = await test_connection()
        duration = time.time() - start_time
        print(f"   連接測試耗時: {duration:.2f}s")
        if duration > 5:
            self.issues.append(f"連接測試過慢: {duration:.2f}s")
        return result

    async def test_initialization_speed(self):
        """測試初始化速度"""
        print("⚡ 測試初始化速度...")
        start_time = time.time()
        graphiti = await initialize_graphiti()
        duration = time.time() - start_time
        print(f"   初始化耗時: {duration:.2f}s")
        if duration > 10:
            self.issues.append(f"初始化過慢: {duration:.2f}s")
        return graphiti

    async def test_simple_memory_operation(self):
        """測試簡單記憶操作"""
        print("📝 測試簡單記憶操作...")
        start_time = time.time()
        result = await add_memory_simple(AddMemoryArgs(
            name="快速測試",
            episode_body="這是一個快速測試記憶",
            group_id="quick_test"
        ))
        duration = time.time() - start_time
        print(f"   添加記憶耗時: {duration:.2f}s")
        print(f"   結果: {result}")

        if duration > 30:
            self.issues.append(f"添加記憶過慢: {duration:.2f}s")
        if result.get('error'):
            self.issues.append(f"添加記憶錯誤: {result.get('message', '未知錯誤')}")

        return result

    async def test_search_operation(self):
        """測試搜索操作"""
        print("🔍 測試搜索操作...")
        start_time = time.time()
        result = await search_memory_nodes(SearchNodesArgs(
            query="快速測試",
            max_nodes=5
        ))
        duration = time.time() - start_time
        print(f"   搜索耗時: {duration:.2f}s")
        print(f"   結果: {result}")

        if duration > 5:
            self.issues.append(f"搜索過慢: {duration:.2f}s")
        if result.get('error'):
            self.issues.append(f"搜索錯誤: {result.get('message', '未知錯誤')}")

        return result

    async def run_diagnostic(self):
        """運行快速診斷"""
        print("🚀 開始快速診斷...")

        # 測試連接
        await self.test_connection_speed()

        # 測試初始化
        await self.test_initialization_speed()

        # 測試記憶操作
        await self.test_simple_memory_operation()

        # 等待一下讓記憶處理完成
        await asyncio.sleep(2)

        # 測試搜索
        await self.test_search_operation()

        # 報告結果
        print("\n" + "="*50)
        if self.issues:
            print(f"❌ 發現 {len(self.issues)} 個問題:")
            for issue in self.issues:
                print(f"  • {issue}")
        else:
            print("✅ 所有測試都通過！")

        return len(self.issues) == 0

async def main():
    diagnostic = QuickDiagnostic()
    success = await diagnostic.run_diagnostic()
    return diagnostic.issues

if __name__ == "__main__":
    issues = asyncio.run(main())
    if issues:
        print(f"\n🛑 診斷完成，發現 {len(issues)} 個問題需要修正")
        exit(1)
    else:
        print("\n🎉 診斷完成，系統運行正常")
        exit(0)