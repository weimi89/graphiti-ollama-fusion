#!/usr/bin/env python3
"""
並發性和資源管理測試
"""
import asyncio
import time
import psutil
import os
from graphiti_mcp_server import (
    add_memory_simple, AddMemoryArgs,
    search_memory_nodes, SearchNodesArgs,
    search_memory_facts, SearchFactsArgs,
    get_episodes, GetEpisodesArgs
)

class ConcurrencyTester:
    def __init__(self):
        self.results = []
        self.issues = []

    def get_system_resources(self):
        """獲取系統資源使用情況"""
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_available': psutil.virtual_memory().available / 1024 / 1024 / 1024  # GB
        }

    async def test_concurrent_memory_operations(self, concurrent_count=5):
        """測試並發記憶操作"""
        print(f"\n🔄 測試 {concurrent_count} 個並發記憶操作")

        # 記錄開始資源
        start_resources = self.get_system_resources()
        print(f"   開始時資源: CPU {start_resources['cpu_percent']:.1f}%, 記憶體 {start_resources['memory_percent']:.1f}%")

        # 創建並發任務
        tasks = []
        start_time = time.time()

        for i in range(concurrent_count):
            task = add_memory_simple(AddMemoryArgs(
                name=f"並發測試記憶 {i}",
                episode_body=f"這是第 {i} 個並發測試記憶，用於測試系統的並發處理能力",
                group_id="concurrency_test"
            ))
            tasks.append(task)

        # 執行並發任務
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time

        # 記錄結束資源
        end_resources = self.get_system_resources()
        print(f"   結束時資源: CPU {end_resources['cpu_percent']:.1f}%, 記憶體 {end_resources['memory_percent']:.1f}%")

        # 分析結果
        success_count = 0
        error_count = 0

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_count += 1
                print(f"   ❌ 任務 {i}: {str(result)}")
            elif result and not result.get('error'):
                success_count += 1
            else:
                error_count += 1
                print(f"   ❌ 任務 {i}: {result.get('message', '未知錯誤')}")

        print(f"   📊 成功: {success_count}/{concurrent_count}, 總耗時: {total_time:.2f}s")
        print(f"   📊 平均每個任務: {total_time/concurrent_count:.2f}s")

        # 檢查資源變化
        memory_increase = end_resources['memory_percent'] - start_resources['memory_percent']
        if memory_increase > 10:
            self.issues.append(f"記憶體使用增加過多: {memory_increase:.1f}%")

        return {
            'success_count': success_count,
            'total_count': concurrent_count,
            'total_time': total_time,
            'avg_time': total_time / concurrent_count,
            'memory_increase': memory_increase
        }

    async def test_concurrent_searches(self, concurrent_count=10):
        """測試並發搜索操作"""
        print(f"\n🔍 測試 {concurrent_count} 個並發搜索操作")

        # 先添加一些測試數據
        await add_memory_simple(AddMemoryArgs(
            name="搜索測試數據",
            episode_body="這是用於測試並發搜索的測試數據",
            group_id="search_test"
        ))

        start_time = time.time()
        start_resources = self.get_system_resources()

        # 創建並發搜索任務
        tasks = []
        for i in range(concurrent_count):
            task = search_memory_nodes(SearchNodesArgs(
                query="測試",
                max_nodes=5
            ))
            tasks.append(task)

        # 執行並發任務
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time

        end_resources = self.get_system_resources()

        # 分析結果
        success_count = sum(1 for r in results if not isinstance(r, Exception) and not r.get('error'))

        print(f"   📊 成功: {success_count}/{concurrent_count}, 總耗時: {total_time:.2f}s")
        print(f"   📊 平均每個搜索: {total_time/concurrent_count:.2f}s")

        return {
            'success_count': success_count,
            'total_count': concurrent_count,
            'total_time': total_time
        }

    async def test_mixed_operations(self):
        """測試混合操作（讀寫並發）"""
        print(f"\n🔀 測試混合操作（讀寫並發）")

        start_time = time.time()

        # 創建混合任務：添加記憶、搜索、獲取記憶段
        tasks = [
            # 3 個添加任務
            add_memory_simple(AddMemoryArgs(
                name="混合測試1", episode_body="混合操作測試1", group_id="mixed_test")),
            add_memory_simple(AddMemoryArgs(
                name="混合測試2", episode_body="混合操作測試2", group_id="mixed_test")),
            add_memory_simple(AddMemoryArgs(
                name="混合測試3", episode_body="混合操作測試3", group_id="mixed_test")),

            # 3 個搜索任務
            search_memory_nodes(SearchNodesArgs(query="測試", max_nodes=3)),
            search_memory_nodes(SearchNodesArgs(query="並發", max_nodes=3)),
            search_memory_facts(SearchFactsArgs(query="", max_facts=3)),

            # 2 個獲取任務
            get_episodes(GetEpisodesArgs(last_n=5, group_id="mixed_test")),
            get_episodes(GetEpisodesArgs(last_n=3, group_id="concurrency_test"))
        ]

        # 執行混合任務
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time

        success_count = sum(1 for r in results if not isinstance(r, Exception) and not r.get('error'))

        print(f"   📊 成功: {success_count}/{len(tasks)}, 總耗時: {total_time:.2f}s")

        return {
            'success_count': success_count,
            'total_count': len(tasks),
            'total_time': total_time
        }

    async def test_resource_limits(self):
        """測試資源限制"""
        print(f"\n⚡ 測試資源限制和恢復能力")

        # 檢查可用記憶體
        available_memory = psutil.virtual_memory().available / 1024 / 1024 / 1024  # GB
        print(f"   可用記憶體: {available_memory:.2f} GB")

        if available_memory < 2:
            print(f"   ⚠️ 記憶體不足，跳過壓力測試")
            return {'skipped': True}

        # 逐漸增加並發數量
        concurrent_counts = [5, 10, 15, 20]
        results = []

        for count in concurrent_counts:
            print(f"   測試 {count} 個並發操作...")

            start_resources = self.get_system_resources()
            if start_resources['memory_percent'] > 90:
                print(f"   ⚠️ 記憶體使用過高 ({start_resources['memory_percent']:.1f}%)，停止測試")
                break

            try:
                result = await self.test_concurrent_memory_operations(count)
                results.append({
                    'concurrent_count': count,
                    'success_rate': result['success_count'] / result['total_count'],
                    'avg_time': result['avg_time']
                })

                # 如果成功率低於 80%，停止測試
                if result['success_count'] / result['total_count'] < 0.8:
                    print(f"   ⚠️ 成功率過低，停止增加並發數")
                    break

            except Exception as e:
                print(f"   ❌ 測試失敗: {e}")
                break

        return results

    async def run_all_tests(self):
        """運行所有並發和資源測試"""
        print("🚀 開始並發性和資源管理測試")
        print("=" * 60)

        # 系統信息
        print(f"💻 系統信息:")
        print(f"   CPU 核心數: {psutil.cpu_count()}")
        print(f"   總記憶體: {psutil.virtual_memory().total / 1024 / 1024 / 1024:.2f} GB")
        print(f"   可用記憶體: {psutil.virtual_memory().available / 1024 / 1024 / 1024:.2f} GB")

        # 測試1: 基本並發操作
        await self.test_concurrent_memory_operations(5)

        # 等待一下
        await asyncio.sleep(2)

        # 測試2: 並發搜索
        await self.test_concurrent_searches(10)

        # 等待一下
        await asyncio.sleep(2)

        # 測試3: 混合操作
        await self.test_mixed_operations()

        # 等待一下
        await asyncio.sleep(2)

        # 測試4: 資源限制測試
        await self.test_resource_limits()

        # 生成報告
        print(f"\n" + "=" * 60)
        print("📊 並發性和資源管理測試結果")

        if self.issues:
            print(f"❌ 發現 {len(self.issues)} 個問題:")
            for issue in self.issues:
                print(f"   • {issue}")
        else:
            print("✅ 並發性和資源管理測試通過")

        return len(self.issues) == 0

async def main():
    tester = ConcurrencyTester()
    success = await tester.run_all_tests()
    return tester.issues

if __name__ == "__main__":
    issues = asyncio.run(main())
    if issues:
        print(f"\n🛑 發現 {len(issues)} 個並發性問題")
        exit(1)
    else:
        print(f"\n🎉 並發性和資源管理測試完成")
        exit(0)