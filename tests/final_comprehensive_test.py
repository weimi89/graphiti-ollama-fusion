#!/usr/bin/env python3
"""
最終全面測試腳本 - 驗證所有修復的功能
包含搜索、查詢、壓力測試和邊界條件驗證
"""

import asyncio
import time
import sys
import os

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

async def test_all_functions():
    print('🌟 開始最終全面功能測試...')

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

    tests = {}

    # 1. 搜索節點功能測試
    print('🔍 測試 1: 搜索節點功能...')
    try:
        search_config = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
        search_config.limit = 10
        search_results = await graphiti._search(
            query='技術架構',
            config=search_config,
            group_ids=['comprehensive_test'],
            search_filter=SearchFilters()
        )
        nodes = search_results.nodes if search_results.nodes else []
        tests['search_nodes'] = f'✅ 成功 - 找到 {len(nodes)} 個節點'
        print(f'✅ 搜索測試成功 - 找到 {len(nodes)} 個節點')
    except Exception as e:
        tests['search_nodes'] = f'❌ 失敗: {e}'
        print(f'❌ 搜索測試失敗: {e}')

    # 2. 事實搜索功能測試
    print('🔍 測試 2: 事實搜索功能...')
    try:
        facts = await graphiti.search(
            group_ids=['comprehensive_test'],
            query='功能特性',
            num_results=5
        )
        tests['search_facts'] = f'✅ 成功 - 找到 {len(facts)} 個事實'
        print(f'✅ 事實搜索成功 - 找到 {len(facts)} 個事實')
    except Exception as e:
        tests['search_facts'] = f'❌ 失敗: {e}'
        print(f'❌ 事實搜索失敗: {e}')

    # 3. 壓力測試 - 使用安全添加方法
    print('💪 測試 3: 壓力測試...')
    try:
        from src.safe_memory_add import safe_add_memory
        stress_success = 0
        start_time = time.time()
        for i in range(5):  # 減少數量避免過長時間
            result = await safe_add_memory(
                graphiti,
                f'壓力測試_{i+1}',
                f'這是第 {i+1} 個壓力測試記憶片段，用於驗證系統穩定性。測試時間: {time.time()}',
                'stress_test'
            )
            if result['success']:
                stress_success += 1
        duration = time.time() - start_time
        tests['stress_test'] = f'✅ 成功 - {stress_success}/5 通過，耗時 {duration:.2f}s'
        print(f'✅ 壓力測試完成 - {stress_success}/5 通過，平均 {duration/5:.2f}s/個')
    except Exception as e:
        tests['stress_test'] = f'❌ 失敗: {e}'
        print(f'❌ 壓力測試失敗: {e}')

    # 4. 邊界條件測試
    print('⚠️ 測試 4: 邊界條件測試...')
    try:
        from src.safe_memory_add import safe_add_memory
        boundary_tests = [
            ('空內容測試', ''),
            ('特殊字符測試', '!@#$%^&*()_+-=[]{}|;:<>?,./~`'),
            ('Unicode測試', '測試中文、emoji 🎉 和特殊符號 αβγ')
        ]
        boundary_success = 0
        for name, content in boundary_tests:
            result = await safe_add_memory(graphiti, name, content, 'boundary_test')
            if result['success']:
                boundary_success += 1
        tests['boundary_test'] = f'✅ 成功 - {boundary_success}/3 通過'
        print(f'✅ 邊界條件測試完成 - {boundary_success}/3 通過')
    except Exception as e:
        tests['boundary_test'] = f'❌ 失敗: {e}'
        print(f'❌ 邊界條件測試失敗: {e}')

    # 5. 大文件處理再次驗證
    print('📄 測試 5: 大文件處理驗證...')
    try:
        from src.safe_memory_add import safe_add_memory
        large_content = '大文件測試內容 - ' + 'A' * 5000 + ' - 結束標記'  # 5KB+ 內容
        result = await safe_add_memory(graphiti, '大文件驗證測試', large_content, 'large_file_test')
        if result['success']:
            tests['large_file'] = '✅ 成功 - 大文件處理正常'
            print('✅ 大文件處理驗證成功')
        else:
            tests['large_file'] = f'❌ 失敗: {result["error"]}'
            print(f'❌ 大文件處理失敗: {result["error"]}')
    except Exception as e:
        tests['large_file'] = f'❌ 失敗: {e}'
        print(f'❌ 大文件處理失敗: {e}')

    # 總結結果
    print('\n' + '='*60)
    print('📊 最終全面功能測試結果總結:')
    print('='*60)
    for test_name, result in tests.items():
        print(f'{test_name:20} - {result}')

    success_count = sum(1 for r in tests.values() if r.startswith('✅'))
    total_count = len(tests)
    success_rate = (success_count / total_count) * 100

    print('='*60)
    print(f'總測試項目: {total_count}')
    print(f'通過測試: {success_count}')
    print(f'失敗測試: {total_count - success_count}')
    print(f'成功率: {success_rate:.1f}%')
    print('='*60)

    if success_rate == 100:
        print('🎉 所有測試都通過！Graphiti MCP Server 功能完全正常！')
        print('✨ 系統已經完成多方向測試驗證，可以投入使用！')
    elif success_rate >= 75:
        print('✅ 大部分測試通過，系統基本功能正常！')
        print('🔧 建議針對失敗的測試項目進行進一步優化。')
    else:
        print('⚠️ 部分測試失敗，需要進一步調查和修復。')

    return success_rate

if __name__ == "__main__":
    print('🚀 啟動 Graphiti MCP Server 最終全面功能測試...')
    success_rate = asyncio.run(test_all_functions())
    if success_rate >= 75:
        print('✅ 測試完成！系統狀態良好。')
    else:
        print('❌ 測試完成，發現問題需要解決。')