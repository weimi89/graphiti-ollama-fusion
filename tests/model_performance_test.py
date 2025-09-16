#!/usr/bin/env python3
"""
模型效能測試 - 測試不同模型組合的效能表現
適合不同硬體配置的用戶
"""
import asyncio
import time
import os
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class ModelConfig:
    name: str
    llm_model: str
    embed_model: str
    description: str
    hardware_requirement: str

# 定義不同的模型組合
MODEL_CONFIGS = [
    ModelConfig(
        name="高效能組合",
        llm_model="qwen2.5:14b",
        embed_model="nomic-embed-text:v1.5",
        description="最佳效果，需要強大硬體",
        hardware_requirement="16GB+ RAM, GPU 推薦"
    ),
    ModelConfig(
        name="平衡組合",
        llm_model="qwen2.5:7b",
        embed_model="nomic-embed-text:v1.5",
        description="平衡效果和資源使用",
        hardware_requirement="8GB+ RAM"
    ),
    ModelConfig(
        name="輕量組合",
        llm_model="llama3.2:3b",
        embed_model="all-minilm:l6-v2",
        description="資源友好，適合低配硬體",
        hardware_requirement="4GB+ RAM"
    ),
    ModelConfig(
        name="極輕量組合",
        llm_model="phi3.5:3.8b",
        embed_model="all-minilm:l6-v2",
        description="最少資源使用",
        hardware_requirement="2GB+ RAM"
    )
]

class ModelPerformanceTester:
    def __init__(self):
        self.results = []

    async def test_model_availability(self, model_name: str) -> bool:
        """測試模型是否可用"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                # 檢查模型是否存在
                async with session.get('http://localhost:11434/api/tags') as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [m['name'] for m in data.get('models', [])]
                        return model_name in models
            return False
        except:
            return False

    async def test_model_speed(self, config: ModelConfig) -> Dict:
        """測試模型的速度和響應"""
        print(f"\n🧪 測試 {config.name} ({config.llm_model})")
        print(f"   硬體需求: {config.hardware_requirement}")

        # 檢查模型可用性
        llm_available = await self.test_model_availability(config.llm_model)
        embed_available = await self.test_model_availability(config.embed_model)

        if not llm_available:
            print(f"   ❌ LLM 模型 {config.llm_model} 不可用")
            return {
                'config': config,
                'available': False,
                'error': f'LLM 模型 {config.llm_model} 不可用'
            }

        if not embed_available:
            print(f"   ❌ 嵌入模型 {config.embed_model} 不可用")
            return {
                'config': config,
                'available': False,
                'error': f'嵌入模型 {config.embed_model} 不可用'
            }

        print(f"   ✅ 模型可用，開始效能測試...")

        try:
            # 設定環境變數
            os.environ['MODEL_NAME'] = config.llm_model
            os.environ['EMBEDDER_MODEL_NAME'] = config.embed_model

            # 重新導入以使用新設定
            import importlib
            import sys

            # 清除相關模組
            modules_to_reload = []
            for module_name in list(sys.modules.keys()):
                if any(name in module_name for name in ['ollama', 'graphiti_mcp_server']):
                    modules_to_reload.append(module_name)

            for module_name in modules_to_reload:
                if module_name in sys.modules:
                    del sys.modules[module_name]

            # 重新導入
            from graphiti_mcp_server import (
                add_memory_simple, AddMemoryArgs,
                search_memory_nodes, SearchNodesArgs,
                initialize_graphiti
            )

            # 初始化測試
            start_time = time.time()
            await initialize_graphiti()
            init_time = time.time() - start_time

            # 記憶添加測試
            start_time = time.time()
            result = await add_memory_simple(AddMemoryArgs(
                name=f"效能測試-{config.name}",
                episode_body=f"這是使用 {config.llm_model} 模型的效能測試記憶",
                group_id=f"perf_test_{config.name.replace(' ', '_')}"
            ))
            memory_time = time.time() - start_time

            # 搜索測試
            start_time = time.time()
            search_result = await search_memory_nodes(SearchNodesArgs(
                query="效能測試",
                max_nodes=5
            ))
            search_time = time.time() - start_time

            test_result = {
                'config': config,
                'available': True,
                'init_time': init_time,
                'memory_time': memory_time,
                'search_time': search_time,
                'memory_success': not result.get('error', False),
                'search_success': not search_result.get('error', False),
                'nodes_extracted': result.get('nodes_extracted', 0),
                'edges_created': result.get('edges_created', 0),
                'nodes_found': len(search_result.get('nodes', []))
            }

            print(f"   📊 初始化: {init_time:.2f}s")
            print(f"   📊 記憶添加: {memory_time:.2f}s")
            print(f"   📊 搜索: {search_time:.2f}s")
            print(f"   📊 實體提取: {test_result['nodes_extracted']} 個")
            print(f"   📊 關係創建: {test_result['edges_created']} 個")

            return test_result

        except Exception as e:
            print(f"   ❌ 測試失敗: {e}")
            return {
                'config': config,
                'available': True,
                'error': str(e)
            }

    async def run_performance_tests(self):
        """運行所有模型效能測試"""
        print("🚀 開始模型效能測試")
        print("=" * 60)
        print("測試目標：找出最適合不同硬體配置的模型組合")
        print("=" * 60)

        for config in MODEL_CONFIGS:
            result = await self.test_model_speed(config)
            self.results.append(result)

            # 在測試間稍作停頓
            await asyncio.sleep(2)

        # 生成報告
        self.generate_report()

    def generate_report(self):
        """生成測試報告"""
        print("\n" + "=" * 60)
        print("📊 模型效能測試報告")
        print("=" * 60)

        # 按可用性分類
        available_results = [r for r in self.results if r.get('available', False) and 'error' not in r]
        unavailable_results = [r for r in self.results if not r.get('available', False) or 'error' in r]

        if available_results:
            print("\n✅ 可用模型組合:")
            # 按總時間排序（初始化 + 記憶添加）
            available_results.sort(key=lambda x: x.get('init_time', 999) + x.get('memory_time', 999))

            for i, result in enumerate(available_results, 1):
                config = result['config']
                total_time = result.get('init_time', 0) + result.get('memory_time', 0)

                print(f"\n{i}. {config.name} 🏆" if i == 1 else f"\n{i}. {config.name}")
                print(f"   模型: {config.llm_model} + {config.embed_model}")
                print(f"   硬體需求: {config.hardware_requirement}")
                print(f"   總耗時: {total_time:.2f}s (初始化: {result.get('init_time', 0):.2f}s + 記憶: {result.get('memory_time', 0):.2f}s)")
                print(f"   功能性: 實體提取 {result.get('nodes_extracted', 0)} 個, 關係 {result.get('edges_created', 0)} 個")

                # 性能評級
                if total_time < 3:
                    print(f"   ⚡ 效能評級: 極佳")
                elif total_time < 8:
                    print(f"   🟢 效能評級: 良好")
                elif total_time < 15:
                    print(f"   🟡 效能評級: 可接受")
                else:
                    print(f"   🔴 效能評級: 需要優化")

        if unavailable_results:
            print(f"\n❌ 不可用模型組合 ({len(unavailable_results)} 個):")
            for result in unavailable_results:
                config = result['config']
                error = result.get('error', '未知錯誤')
                print(f"   • {config.name}: {error}")

        # 建議
        print(f"\n💡 建議:")
        if available_results:
            best_config = available_results[0]['config']
            print(f"   • 推薦組合: {best_config.name}")
            print(f"   • 適合硬體: {best_config.hardware_requirement}")
            print(f"   • 使用方式: 在 .env 中設定:")
            print(f"     MODEL_NAME={best_config.llm_model}")
            print(f"     EMBEDDER_MODEL_NAME={best_config.embed_model}")
        else:
            print("   • 請先安裝必要的 Ollama 模型")
            print("   • 建議執行: ollama pull qwen2.5:7b && ollama pull nomic-embed-text:v1.5")

async def main():
    tester = ModelPerformanceTester()
    await tester.run_performance_tests()

if __name__ == "__main__":
    asyncio.run(main())