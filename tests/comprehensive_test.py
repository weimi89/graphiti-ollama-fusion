#!/usr/bin/env python3
"""
全面測試 Graphiti MCP 服務器
測試所有功能的邊界條件、異常情況和潛在問題
"""
import asyncio
import json
import time
from datetime import datetime, timezone
from graphiti_mcp_server import (
    add_memory_simple, AddMemoryArgs,
    search_memory_nodes, SearchNodesArgs,
    search_memory_facts, SearchFactsArgs,
    get_episodes, GetEpisodesArgs,
    clear_graph,
    test_connection,
    initialize_graphiti
)

class ComprehensiveTest:
    def __init__(self):
        self.passed_tests = 0
        self.failed_tests = 0
        self.issues_found = []

    def log_test(self, test_name, passed, issue=None):
        """記錄測試結果"""
        if passed:
            self.passed_tests += 1
            print(f"  ✅ {test_name}")
        else:
            self.failed_tests += 1
            print(f"  ❌ {test_name}")
            if issue:
                self.issues_found.append(f"{test_name}: {issue}")

    async def test_connection_reliability(self):
        """測試連接可靠性"""
        print("\n🔌 測試連接可靠性")
        print("-" * 30)

        # 測試基本連接
        result = await test_connection()
        self.log_test("基本連接測試", not result.get('error'))

        # 測試多重連接
        try:
            graphiti1 = await initialize_graphiti()
            graphiti2 = await initialize_graphiti()
            self.log_test("多重連接測試", graphiti1 is graphiti2)  # 應該是同一個實例
        except Exception as e:
            self.log_test("多重連接測試", False, str(e))

    async def test_memory_operations_edge_cases(self):
        """測試記憶操作的邊界條件"""
        print("\n🧠 測試記憶操作邊界條件")
        print("-" * 30)

        # 測試空內容
        result = await add_memory_simple(AddMemoryArgs(
            name="空內容測試",
            episode_body="",
            group_id="test"
        ))
        self.log_test("空內容記憶", not result.get('error'))

        # 測試極長內容
        long_content = "這是一個極長的測試內容。" * 1000
        result = await add_memory_simple(AddMemoryArgs(
            name="極長內容測試",
            episode_body=long_content,
            group_id="test"
        ))
        self.log_test("極長內容記憶", not result.get('error'))

        # 測試特殊字符
        special_content = "測試特殊字符: !@#$%^&*()_+-=[]{}|;:,.<>? 中文《》「」—…"
        result = await add_memory_simple(AddMemoryArgs(
            name="特殊字符測試",
            episode_body=special_content,
            group_id="test"
        ))
        self.log_test("特殊字符記憶", not result.get('error'))

        # 測試 JSON 內容
        json_content = '{"user": "張三", "action": "登入", "timestamp": "2025-01-01T00:00:00Z"}'
        result = await add_memory_simple(AddMemoryArgs(
            name="JSON內容測試",
            episode_body=json_content,
            group_id="test"
        ))
        self.log_test("JSON內容記憶", not result.get('error'))

        # 測試極長名稱
        long_name = "極長名稱測試" * 100
        result = await add_memory_simple(AddMemoryArgs(
            name=long_name,
            episode_body="測試極長名稱的處理",
            group_id="test"
        ))
        self.log_test("極長名稱記憶", not result.get('error'))

    async def test_search_edge_cases(self):
        """測試搜索功能的邊界條件"""
        print("\n🔍 測試搜索功能邊界條件")
        print("-" * 30)

        # 測試空查詢
        result = await search_memory_nodes(SearchNodesArgs(query=""))
        self.log_test("空查詢搜索", not result.get('error'))

        # 測試非常長的查詢
        long_query = "這是一個極長的搜索查詢" * 100
        result = await search_memory_nodes(SearchNodesArgs(query=long_query))
        self.log_test("極長查詢搜索", not result.get('error'))

        # 測試特殊字符查詢
        special_query = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        result = await search_memory_nodes(SearchNodesArgs(query=special_query))
        self.log_test("特殊字符查詢", not result.get('error'))

        # 測試 SQL 注入嘗試
        sql_injection = "'; DROP TABLE Entity; --"
        result = await search_memory_nodes(SearchNodesArgs(query=sql_injection))
        self.log_test("SQL注入防護", not result.get('error'))

        # 測試 Cypher 注入嘗試
        cypher_injection = "MATCH (n) DELETE n"
        result = await search_memory_nodes(SearchNodesArgs(query=cypher_injection))
        self.log_test("Cypher注入防護", not result.get('error'))

        # 測試極大的max_nodes值
        result = await search_memory_nodes(SearchNodesArgs(query="測試", max_nodes=999999))
        self.log_test("極大max_nodes", not result.get('error'))

        # 測試負數max_nodes值
        result = await search_memory_nodes(SearchNodesArgs(query="測試", max_nodes=-1))
        self.log_test("負數max_nodes", not result.get('error'))

    async def test_facts_search_edge_cases(self):
        """測試事實搜索的邊界條件"""
        print("\n🔗 測試事實搜索邊界條件")
        print("-" * 30)

        # 測試不存在的關係類型
        result = await search_memory_facts(SearchFactsArgs(query="NONEXISTENT_RELATION"))
        self.log_test("不存在關係搜索", not result.get('error'))

        # 測試空事實查詢
        result = await search_memory_facts(SearchFactsArgs(query=""))
        self.log_test("空事實查詢", not result.get('error'))

        # 測試極大max_facts值
        result = await search_memory_facts(SearchFactsArgs(query="", max_facts=999999))
        self.log_test("極大max_facts", not result.get('error'))

    async def test_group_operations(self):
        """測試群組操作"""
        print("\n👥 測試群組操作")
        print("-" * 30)

        # 測試不存在的群組
        result = await search_memory_nodes(SearchNodesArgs(
            query="", group_ids=["nonexistent_group"]
        ))
        self.log_test("不存在群組搜索", not result.get('error'))

        # 測試空群組列表
        result = await search_memory_nodes(SearchNodesArgs(
            query="", group_ids=[]
        ))
        self.log_test("空群組列表搜索", not result.get('error'))

        # 測試極長群組名
        long_group = "extremely_long_group_name" * 50
        result = await add_memory_simple(AddMemoryArgs(
            name="極長群組測試",
            episode_body="測試極長群組名稱",
            group_id=long_group
        ))
        self.log_test("極長群組名", not result.get('error'))

    async def test_concurrency(self):
        """測試並發操作"""
        print("\n⚡ 測試並發操作")
        print("-" * 30)

        try:
            # 並發添加記憶
            tasks = []
            for i in range(5):
                task = add_memory_simple(AddMemoryArgs(
                    name=f"並發測試{i}",
                    episode_body=f"這是並發測試記憶{i}",
                    group_id="concurrent_test"
                ))
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for r in results if not isinstance(r, Exception) and not r.get('error'))
            self.log_test(f"並發添加記憶 ({success_count}/5)", success_count == 5)

            # 並發搜索
            search_tasks = []
            for i in range(3):
                task = search_memory_nodes(SearchNodesArgs(query="並發"))
                search_tasks.append(task)

            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            search_success = sum(1 for r in search_results if not isinstance(r, Exception) and not r.get('error'))
            self.log_test(f"並發搜索 ({search_success}/3)", search_success == 3)

        except Exception as e:
            self.log_test("並發操作", False, str(e))

    async def test_data_consistency(self):
        """測試資料一致性"""
        print("\n🔄 測試資料一致性")
        print("-" * 30)

        # 添加測試記憶
        memory_name = f"一致性測試{time.time()}"
        add_result = await add_memory_simple(AddMemoryArgs(
            name=memory_name,
            episode_body="這是資料一致性測試記憶",
            group_id="consistency_test"
        ))

        if not add_result.get('error'):
            # 立即搜索應該找到
            search_result = await search_memory_nodes(SearchNodesArgs(
                query=memory_name,
                group_ids=["consistency_test"]
            ))

            # 檢查是否能在記憶段中找到
            episodes_result = await get_episodes(GetEpisodesArgs(
                group_id="consistency_test",
                last_n=10
            ))

            episode_found = any(memory_name in ep.get('name', '') for ep in episodes_result.get('episodes', []))
            self.log_test("資料一致性檢查", episode_found)
        else:
            self.log_test("資料一致性檢查", False, "添加記憶失敗")

    async def test_error_recovery(self):
        """測試錯誤恢復"""
        print("\n🛠️ 測試錯誤恢復")
        print("-" * 30)

        # 測試無效參數恢復
        try:
            result = await search_memory_nodes(SearchNodesArgs(
                query="測試",
                max_nodes=0
            ))
            self.log_test("零max_nodes處理", not result.get('error'))
        except Exception as e:
            self.log_test("零max_nodes處理", False, str(e))

        # 測試空記憶名稱
        try:
            result = await add_memory_simple(AddMemoryArgs(
                name="",
                episode_body="空名稱測試",
                group_id="test"
            ))
            self.log_test("空名稱處理", not result.get('error'))
        except Exception as e:
            self.log_test("空名稱處理", False, str(e))

    async def test_memory_limits(self):
        """測試記憶體限制"""
        print("\n💾 測試記憶體和性能限制")
        print("-" * 30)

        # 測試大量記憶添加
        large_batch_success = 0
        for i in range(10):  # 減少數量避免測試時間過長
            result = await add_memory_simple(AddMemoryArgs(
                name=f"批量測試{i}",
                episode_body=f"這是第{i}個批量測試記憶",
                group_id="batch_test"
            ))
            if not result.get('error'):
                large_batch_success += 1

        self.log_test(f"大量記憶添加 ({large_batch_success}/10)", large_batch_success >= 8)

        # 測試搜索性能
        start_time = time.time()
        result = await search_memory_nodes(SearchNodesArgs(query="測試", max_nodes=100))
        search_time = time.time() - start_time

        self.log_test(f"搜索性能 ({search_time:.2f}s)", search_time < 10.0)

    async def run_all_tests(self):
        """運行所有測試"""
        print("🚀 開始全面測試 Graphiti MCP 服務器")
        print("=" * 60)

        # 運行各項測試
        await self.test_connection_reliability()
        await self.test_memory_operations_edge_cases()
        await self.test_search_edge_cases()
        await self.test_facts_search_edge_cases()
        await self.test_group_operations()
        await self.test_concurrency()
        await self.test_data_consistency()
        await self.test_error_recovery()
        await self.test_memory_limits()

        # 輸出測試結果
        print("\n" + "=" * 60)
        print("📊 測試結果總結")
        print(f"✅ 通過測試: {self.passed_tests}")
        print(f"❌ 失敗測試: {self.failed_tests}")
        print(f"📈 成功率: {self.passed_tests/(self.passed_tests+self.failed_tests)*100:.1f}%")

        if self.issues_found:
            print(f"\n⚠️  發現的問題 ({len(self.issues_found)}個):")
            for issue in self.issues_found:
                print(f"  • {issue}")
        else:
            print("\n🎉 所有測試都通過了！")

        return len(self.issues_found) == 0

async def main():
    tester = ComprehensiveTest()
    success = await tester.run_all_tests()
    return tester.issues_found

if __name__ == "__main__":
    issues = asyncio.run(main())
    if issues:
        exit(1)  # 有問題時返回錯誤碼
    else:
        exit(0)  # 所有測試通過