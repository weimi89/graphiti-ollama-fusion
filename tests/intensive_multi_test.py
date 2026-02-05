#!/usr/bin/env python3
"""
嚴格多次多方向測試腳本
包含重複測試、大量內容建立、壓力測試、極限測試
"""

import asyncio
import time
import json
import random
import string
import sys
import os
from datetime import datetime, timezone

# 添加專案根目錄到路徑，以便導入專案模組
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.config import load_config
from src.ollama_graphiti_client import OptimizedOllamaClient
from src.ollama_embedder import OllamaEmbedder
from graphiti_core import Graphiti
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.search.search_config_recipes import NODE_HYBRID_SEARCH_RRF
from graphiti_core.search.search_filters import SearchFilters

class IntensiveTestRunner:
    def __init__(self):
        self.test_results = {}
        self.round_results = []
        self.total_errors = []

    async def initialize_graphiti(self):
        """初始化 Graphiti"""
        config = load_config()
        llm_config = LLMConfig(
            base_url=config.ollama.base_url,
            model=config.ollama.model,
            temperature=0.0
        )
        llm_client = OptimizedOllamaClient(config=llm_config)
        embedder_client = OllamaEmbedder(
            model=config.embedder.model,
            base_url=config.embedder.base_url,
            dimensions=config.embedder.dimensions
        )

        graphiti = Graphiti(
            uri=config.neo4j.uri,
            user=config.neo4j.user,
            password=config.neo4j.password,
            llm_client=llm_client,
            embedder=embedder_client,
            max_coroutines=3,
        )
        await graphiti.build_indices_and_constraints()
        return graphiti

    def generate_large_content(self, size_kb=10):
        """生成指定大小的測試內容"""
        chars_needed = size_kb * 1024
        # 生成有意義的重複內容而不是隨機字符
        base_content = """
        這是一個大文件測試內容段落。我們需要驗證系統能夠處理較大的文件而不會出現問題。
        內容包含技術細節、多語言文字、特殊符號和結構化數據。
        測試項目：性能測試、穩定性驗證、錯誤處理、邊界條件。
        支援格式：文本、JSON、XML、CSV、Markdown等各種格式。
        系統特性：高可用性、可擴展性、安全性、易用性。
        """
        content_parts = []
        current_size = 0
        counter = 0

        while current_size < chars_needed:
            part = f"[段落-{counter:04d}] {base_content} 時間戳：{datetime.now()} 隨機數：{random.randint(1000,9999)}\n"
            content_parts.append(part)
            current_size += len(part)
            counter += 1

        return ''.join(content_parts)[:chars_needed]

    async def test_connection_stability(self, rounds=5):
        """測試連接穩定性"""
        print(f"🔌 測試連接穩定性（{rounds} 輪）...")
        results = []

        for i in range(rounds):
            try:
                graphiti = await self.initialize_graphiti()
                results.append(True)
                print(f"  輪次 {i+1}: ✅ 連接成功")
                await asyncio.sleep(0.5)  # 短暫間隔
            except Exception as e:
                results.append(False)
                print(f"  輪次 {i+1}: ❌ 連接失敗 - {e}")
                self.total_errors.append(f"連接測試輪次{i+1}: {e}")

        success_rate = (sum(results) / len(results)) * 100
        return success_rate

    async def build_rich_content_library(self, graphiti):
        """建立大量豐富的知識圖庫內容"""
        print("📚 建立大量豐富知識圖庫內容...")

        from src.safe_memory_add import safe_add_memory

        # 技術文檔類內容
        tech_contents = [
            ("Neo4j 圖資料庫架構", "Neo4j 是一個高性能的 NOSQL 圖形資料庫，支援 ACID 事務、索引、約束條件。使用 Cypher 查詢語言進行圖遍歷和模式匹配。適用於推薦系統、社交網絡、欺詐檢測等場景。"),
            ("Ollama 本地 LLM 部署", "Ollama 是一個輕量級的本地 LLM 運行框架，支援 Llama 2、Code Llama、Mistral 等多種模型。提供 REST API 接口，支援流式輸出、模板定制、模型量化等功能。"),
            ("FastMCP 協議實現", "FastMCP 實現了 Model Context Protocol 標準，提供工具調用、資源存取、提示模板等功能。支援異步操作、錯誤處理、類型檢查、日誌記錄等企業級特性。"),
            ("Python 異步編程模式", "使用 asyncio 實現高並發處理，包含事件迴圈、協程、任務、Future 對象。配合 aiohttp、asyncpg 等庫構建高性能 Web 服務和資料庫操作。"),
            ("Docker 容器化部署", "Docker 提供輕量級虛擬化解決方案，支援多階段構建、多平台鏡像、健康檢查。配合 Docker Compose 實現服務編排和環境管理。")
        ]

        # 業務流程類內容
        business_contents = [
            ("軟體開發生命周期", "包含需求分析、系統設計、編碼實現、測試驗證、部署上線、維護優化等階段。採用敏捷開發模式，支援持續集成和持續部署。"),
            ("數據治理最佳實踐", "建立數據品質標準、數據血緣追蹤、訪問控制策略。實施數據分類分級、隱私保護、合規性檢查等治理措施。"),
            ("系統監控和告警", "部署 Prometheus + Grafana 監控堆疊，收集應用指標、系統資源、業務數據。配置多級告警機制和自動化響應策略。"),
            ("安全防護體系", "實施深度防禦策略，包含網絡安全、應用安全、數據安全、身份認證。定期進行安全審計和漏洞掃描。"),
            ("性能優化策略", "從數據庫查詢優化、緩存策略、負載均衡、代碼優化等維度提升系統性能。建立性能基準測試和持續優化機制。")
        ]

        # 創新技術類內容
        innovation_contents = [
            ("人工智慧應用場景", "AI 技術在自然語言處理、計算機視覺、推薦系統、智能客服等領域的應用。包含深度學習、強化學習、聯邦學習等前沿技術。"),
            ("區塊鏈技術原理", "分散式賬本技術，提供去中心化、不可篡改、透明化的數據存儲方案。支援智能合約、共識機制、加密演算法等核心功能。"),
            ("雲原生架構設計", "基於容器、微服務、DevOps 的現代應用架構。採用 Kubernetes 編排、服務網格、可觀測性等技術棧。"),
            ("邊緣計算發展", "將計算能力下沉到網絡邊緣，降低延遲、減少頻寬消耗。適用於 IoT、自動駕駛、AR/VR 等場景。"),
            ("量子計算前景", "基於量子力學原理的新型計算範式，在密碼學、最佳化、機器學習等領域具有顛覆性潛力。")
        ]

        all_contents = tech_contents + business_contents + innovation_contents
        results = []

        for i, (name, content) in enumerate(all_contents):
            try:
                print(f"  📝 添加內容 {i+1}/{len(all_contents)}: {name}")
                result = await safe_add_memory(graphiti, name, content, f"rich_content_round")
                results.append(result['success'])
                await asyncio.sleep(0.1)  # 防止過快調用
            except Exception as e:
                print(f"  ❌ 添加失敗: {name} - {e}")
                results.append(False)
                self.total_errors.append(f"內容添加: {name} - {e}")

        success_rate = (sum(results) / len(results)) * 100
        print(f"📚 內容庫建立完成: {sum(results)}/{len(results)} 成功 ({success_rate:.1f}%)")
        return success_rate

    async def test_large_file_stress(self, graphiti, rounds=3):
        """多次大文件寫入壓力測試"""
        print(f"📄 大文件壓力測試（{rounds} 輪，逐步增大）...")

        from src.safe_memory_add import safe_add_memory
        results = []

        for round_num in range(rounds):
            file_size = (round_num + 1) * 20  # 20KB, 40KB, 60KB
            try:
                print(f"  📄 輪次 {round_num + 1}: 測試 {file_size}KB 文件...")
                large_content = self.generate_large_content(file_size)

                start_time = time.time()
                result = await safe_add_memory(
                    graphiti,
                    f"大文件測試_輪次{round_num+1}_{file_size}KB",
                    large_content,
                    "large_file_stress"
                )
                duration = time.time() - start_time

                if result['success']:
                    print(f"  ✅ 輪次 {round_num + 1} 成功 - {file_size}KB, 耗時 {duration:.2f}s")
                    results.append(True)
                else:
                    print(f"  ❌ 輪次 {round_num + 1} 失敗 - {result.get('error', 'Unknown error')}")
                    results.append(False)
                    self.total_errors.append(f"大文件測試輪次{round_num+1}: {result.get('error')}")

            except Exception as e:
                print(f"  ❌ 輪次 {round_num + 1} 異常 - {e}")
                results.append(False)
                self.total_errors.append(f"大文件測試輪次{round_num+1}: {e}")

        success_rate = (sum(results) / len(results)) * 100
        return success_rate

    async def test_search_stability(self, graphiti, rounds=5):
        """重複搜索查詢功能穩定性驗證"""
        print(f"🔍 搜索功能穩定性測試（{rounds} 輪）...")

        search_queries = ["技術", "系統", "數據", "安全", "性能", "開發", "AI", "雲端"]
        results = []

        for round_num in range(rounds):
            try:
                query = random.choice(search_queries)
                print(f"  🔍 輪次 {round_num + 1}: 搜索 '{query}'...")

                # 節點搜索
                search_config = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
                search_config.limit = 10
                search_results = await graphiti._search(
                    query=query,
                    config=search_config,
                    group_ids=[],
                    search_filter=SearchFilters()
                )
                nodes = search_results.nodes if search_results.nodes else []

                # 事實搜索
                facts = await graphiti.search(query=query, num_results=5)

                print(f"  ✅ 輪次 {round_num + 1} 完成 - 找到 {len(nodes)} 節點, {len(facts)} 事實")
                results.append(True)
                await asyncio.sleep(0.2)

            except Exception as e:
                print(f"  ❌ 輪次 {round_num + 1} 失敗 - {e}")
                results.append(False)
                self.total_errors.append(f"搜索測試輪次{round_num+1}: {e}")

        success_rate = (sum(results) / len(results)) * 100
        return success_rate

    async def test_high_frequency_stress(self, graphiti, count=20):
        """高頻次壓力測試和並發測試"""
        print(f"💪 高頻次壓力測試（{count} 次快速添加）...")

        from src.safe_memory_add import safe_add_memory

        # 並發任務列表
        tasks = []
        for i in range(count):
            content = f"高頻測試內容_{i+1}，時間戳: {datetime.now()}, 隨機值: {random.randint(10000,99999)}"
            task = safe_add_memory(graphiti, f"高頻測試_{i+1}", content, "high_freq_test")
            tasks.append(task)

        # 執行並發測試
        start_time = time.time()
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            duration = time.time() - start_time

            success_count = sum(1 for r in results if isinstance(r, dict) and r.get('success'))
            error_count = sum(1 for r in results if isinstance(r, Exception) or (isinstance(r, dict) and not r.get('success')))

            print(f"  ✅ 高頻測試完成 - {success_count}/{count} 成功, {error_count} 失敗, 總耗時 {duration:.2f}s")
            print(f"  📊 平均速度: {duration/count:.3f}s/個")

            # 記錄錯誤
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.total_errors.append(f"高頻測試第{i+1}個: {result}")
                elif isinstance(result, dict) and not result.get('success'):
                    self.total_errors.append(f"高頻測試第{i+1}個: {result.get('error')}")

            success_rate = (success_count / count) * 100
            return success_rate

        except Exception as e:
            print(f"  ❌ 高頻測試整體失敗 - {e}")
            self.total_errors.append(f"高頻測試整體: {e}")
            return 0.0

    async def test_extreme_boundary_conditions(self, graphiti):
        """極限邊界條件測試"""
        print("⚠️ 極限邊界條件測試...")

        from src.safe_memory_add import safe_add_memory

        boundary_tests = [
            ("空字符串", ""),
            ("單字符", "A"),
            ("極長標題", "A" * 1000),
            ("純數字內容", "1234567890" * 100),
            ("純符號", "!@#$%^&*()_+-=[]{}|;':\",./<>?~`" * 50),
            ("混合Unicode", "測試🎉αβγ中文Русский日本語العربية한국어" * 20),
            ("JSON結構", json.dumps({"nested": {"deep": {"very": {"deep": [1, 2, 3, {"more": "data"}]}}}})),
            ("XML結構", "<root><item id='1'><data>test</data></item></root>" * 100),
            ("超長單行", "This is a very long line " * 500),
            ("多行結構", "Line 1\nLine 2\nLine 3\n" * 200)
        ]

        results = []
        for name, content in boundary_tests:
            try:
                print(f"  🧪 測試邊界條件: {name} (長度: {len(content)})")
                result = await safe_add_memory(graphiti, f"邊界測試_{name}", content, "boundary_extreme")
                results.append(result['success'])
                if result['success']:
                    print(f"    ✅ {name} - 成功")
                else:
                    print(f"    ❌ {name} - 失敗: {result.get('error')}")
                    self.total_errors.append(f"邊界測試{name}: {result.get('error')}")
            except Exception as e:
                print(f"    ❌ {name} - 異常: {e}")
                results.append(False)
                self.total_errors.append(f"邊界測試{name}: {e}")

        success_rate = (sum(results) / len(results)) * 100
        return success_rate

    async def run_complete_test_suite(self, rounds=3):
        """運行完整的測試套件，進行多輪測試"""
        print(f"🚀 開始嚴格多輪次多方向測試 ({rounds} 輪)...")
        print("="*80)

        for round_num in range(rounds):
            print(f"\n🔄 === 第 {round_num + 1} 輪測試開始 ===")
            round_start_time = time.time()
            round_results = {}

            try:
                # 初始化 Graphiti
                graphiti = await self.initialize_graphiti()

                # 1. 連接穩定性測試
                print(f"\n📍 第 {round_num + 1} 輪 - 連接穩定性測試")
                round_results['connection_stability'] = await self.test_connection_stability(5)

                # 2. 建立豐富內容庫
                print(f"\n📍 第 {round_num + 1} 輪 - 建立豐富內容庫")
                round_results['content_library'] = await self.build_rich_content_library(graphiti)

                # 3. 大文件壓力測試
                print(f"\n📍 第 {round_num + 1} 輪 - 大文件壓力測試")
                round_results['large_file_stress'] = await self.test_large_file_stress(graphiti, 3)

                # 4. 搜索功能穩定性測試
                print(f"\n📍 第 {round_num + 1} 輪 - 搜索功能穩定性測試")
                round_results['search_stability'] = await self.test_search_stability(graphiti, 5)

                # 5. 高頻次壓力測試
                print(f"\n📍 第 {round_num + 1} 輪 - 高頻次壓力測試")
                round_results['high_freq_stress'] = await self.test_high_frequency_stress(graphiti, 15)

                # 6. 極限邊界條件測試
                print(f"\n📍 第 {round_num + 1} 輪 - 極限邊界條件測試")
                round_results['boundary_extreme'] = await self.test_extreme_boundary_conditions(graphiti)

                round_duration = time.time() - round_start_time
                round_results['round_duration'] = round_duration
                round_results['round_success'] = True

                print(f"\n✅ 第 {round_num + 1} 輪測試完成，耗時 {round_duration:.2f}s")

            except Exception as e:
                round_results['round_success'] = False
                round_results['round_error'] = str(e)
                print(f"\n❌ 第 {round_num + 1} 輪測試失敗: {e}")
                self.total_errors.append(f"第{round_num+1}輪整體測試: {e}")

            self.round_results.append(round_results)

            # 輪次間暫停
            if round_num < rounds - 1:
                print(f"⏳ 輪次間暫停 3 秒...")
                await asyncio.sleep(3)

        # 生成總結報告
        await self.generate_final_report()

    async def generate_final_report(self):
        """生成最終測試報告"""
        print("\n" + "="*80)
        print("📊 嚴格多輪次多方向測試 - 最終報告")
        print("="*80)

        if not self.round_results:
            print("❌ 沒有測試結果可供分析")
            return

        # 統計各項測試的成功率
        test_categories = ['connection_stability', 'content_library', 'large_file_stress',
                          'search_stability', 'high_freq_stress', 'boundary_extreme']

        category_stats = {}
        for category in test_categories:
            values = [r.get(category, 0) for r in self.round_results if r.get('round_success')]
            if values:
                category_stats[category] = {
                    'avg': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'rounds': len(values)
                }

        # 輸出詳細統計
        print(f"\n📈 各測試項目統計 (總輪次: {len(self.round_results)}):")
        print("-" * 80)
        category_names = {
            'connection_stability': '連接穩定性',
            'content_library': '內容庫建立',
            'large_file_stress': '大文件壓力',
            'search_stability': '搜索穩定性',
            'high_freq_stress': '高頻壓力',
            'boundary_extreme': '極限邊界'
        }

        for category, stats in category_stats.items():
            name = category_names.get(category, category)
            print(f"{name:12} - 平均: {stats['avg']:6.1f}% | 最小: {stats['min']:6.1f}% | 最大: {stats['max']:6.1f}% | 輪次: {stats['rounds']}")

        # 計算整體成功率
        successful_rounds = sum(1 for r in self.round_results if r.get('round_success'))
        total_rounds = len(self.round_results)
        overall_success_rate = (successful_rounds / total_rounds) * 100

        # 計算平均測試項成功率
        all_success_rates = []
        for round_result in self.round_results:
            if round_result.get('round_success'):
                rates = [round_result.get(cat, 0) for cat in test_categories]
                if rates:
                    all_success_rates.extend(rates)

        avg_test_success = sum(all_success_rates) / len(all_success_rates) if all_success_rates else 0

        print("-" * 80)
        print(f"🎯 整體統計:")
        print(f"   成功輪次: {successful_rounds}/{total_rounds} ({overall_success_rate:.1f}%)")
        print(f"   平均測試成功率: {avg_test_success:.1f}%")
        print(f"   總錯誤數: {len(self.total_errors)}")

        # 總耗時
        total_duration = sum(r.get('round_duration', 0) for r in self.round_results)
        print(f"   總測試耗時: {total_duration:.2f}s")

        # 錯誤摘要
        if self.total_errors:
            print(f"\n❌ 錯誤摘要 (前10個):")
            for i, error in enumerate(self.total_errors[:10]):
                print(f"   {i+1}. {error}")
            if len(self.total_errors) > 10:
                print(f"   ... 還有 {len(self.total_errors) - 10} 個錯誤")

        # 最終判定
        print("\n" + "="*80)
        if overall_success_rate >= 90 and avg_test_success >= 85:
            print("🎉 測試結果: 優秀 - 系統穩定性極佳，可以投入生產使用!")
        elif overall_success_rate >= 80 and avg_test_success >= 75:
            print("✅ 測試結果: 良好 - 系統基本穩定，建議修復部分問題後使用")
        elif overall_success_rate >= 70 and avg_test_success >= 65:
            print("⚠️ 測試結果: 一般 - 系統存在一些穩定性問題，需要優化")
        else:
            print("❌ 測試結果: 需要改進 - 系統穩定性不足，不建議直接使用")
        print("="*80)

async def main():
    """主函數"""
    runner = IntensiveTestRunner()
    await runner.run_complete_test_suite(rounds=3)  # 3輪完整測試

if __name__ == "__main__":
    print("🚀 啟動嚴格多輪次多方向測試...")
    asyncio.run(main())