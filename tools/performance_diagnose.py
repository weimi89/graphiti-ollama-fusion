#!/usr/bin/env python3
"""
性能診斷工具 - 分析 add_episode 為什麼這麼慢
"""
import asyncio
import time
import cProfile
import io
import pstats
from graphiti_mcp_server import initialize_graphiti, AddMemoryArgs, add_memory_simple

async def profile_add_episode():
    """性能剖析 add_episode 操作"""
    print("🔍 開始性能診斷...")

    # 初始化
    print("1. 初始化 Graphiti...")
    start_time = time.time()
    graphiti = await initialize_graphiti()
    init_time = time.time() - start_time
    print(f"   初始化耗時: {init_time:.2f}s")

    # 準備性能剖析器
    profiler = cProfile.Profile()

    print("2. 開始剖析 add_episode 操作...")

    # 開始剖析
    profiler.enable()

    start_time = time.time()
    result = await add_memory_simple(AddMemoryArgs(
        name="性能診斷測試",
        episode_body="這是一個用於診斷性能問題的測試記憶，內容相對簡單以便分析",
        group_id="performance_test"
    ))
    total_time = time.time() - start_time

    # 停止剖析
    profiler.disable()

    print(f"3. add_episode 總耗時: {total_time:.2f}s")
    print(f"   結果: {result}")

    # 分析性能報告
    print("\n4. 性能分析報告:")
    s = io.StringIO()
    stats = pstats.Stats(profiler, stream=s)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # 顯示前20個最耗時的函數

    profile_output = s.getvalue()
    print(profile_output)

    # 查找最耗時的操作
    print("\n5. 最耗時的操作分析:")
    lines = profile_output.split('\n')
    for line in lines[5:25]:  # 跳過標題行，顯示前20個函數
        if 'seconds' not in line and len(line.strip()) > 0 and not line.startswith(' '):
            continue
        if any(keyword in line.lower() for keyword in ['ollama', 'request', 'http', 'neo4j', 'graphiti', 'llm']):
            print(f"   🚨 {line.strip()}")

    return total_time

async def diagnose_components():
    """診斷各個組件的性能"""
    print("\n📊 組件性能診斷")
    print("-" * 40)

    # 測試 Ollama LLM 響應時間
    print("🦙 測試 Ollama LLM 響應時間...")

    try:
        import aiohttp
        start_time = time.time()

        async with aiohttp.ClientSession() as session:
            payload = {
                "model": "qwen2.5:14b",
                "messages": [{"role": "user", "content": "提取實體: 這是測試"}],
                "format": "json",
                "stream": False
            }

            async with session.post('http://localhost:11434/api/chat', json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    llm_time = time.time() - start_time
                    print(f"   LLM 響應時間: {llm_time:.2f}s")
                    print(f"   響應內容長度: {len(data.get('message', {}).get('content', ''))}")
                else:
                    print(f"   ❌ LLM 請求失敗: {response.status}")

    except Exception as e:
        print(f"   ❌ LLM 測試失敗: {e}")

    # 測試嵌入器響應時間
    print("\n🧲 測試嵌入器響應時間...")
    try:
        start_time = time.time()

        async with aiohttp.ClientSession() as session:
            payload = {
                "model": "nomic-embed-text:v1.5",
                "input": "這是測試文字"
            }

            async with session.post('http://localhost:11434/api/embed', json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    embed_time = time.time() - start_time
                    print(f"   嵌入響應時間: {embed_time:.2f}s")
                    embeddings = data.get('embeddings', [])
                    if embeddings:
                        print(f"   嵌入維度: {len(embeddings[0])}")
                else:
                    print(f"   ❌ 嵌入請求失敗: {response.status}")

    except Exception as e:
        print(f"   ❌ 嵌入測試失敗: {e}")

    # 測試 Neo4j 響應時間
    print("\n🗄️  測試 Neo4j 響應時間...")
    try:
        graphiti = await initialize_graphiti()

        start_time = time.time()
        result = await graphiti.driver.execute_query("RETURN 'test' as message")
        neo4j_time = time.time() - start_time
        print(f"   Neo4j 響應時間: {neo4j_time:.2f}s")

        # 檢查數據庫大小
        start_time = time.time()
        count_result = await graphiti.driver.execute_query("MATCH (n) RETURN count(n) as node_count")
        count_time = time.time() - start_time

        if count_result and count_result.records:
            node_count = count_result.records[0]['node_count']
            print(f"   資料庫節點數量: {node_count}")
            print(f"   統計查詢時間: {count_time:.2f}s")

            if node_count > 10000:
                print(f"   ⚠️ 節點數量較多可能影響性能")

    except Exception as e:
        print(f"   ❌ Neo4j 測試失敗: {e}")

async def suggest_optimizations(total_time):
    """根據診斷結果提出優化建議"""
    print(f"\n💡 優化建議")
    print("-" * 40)

    if total_time > 60:
        print("🚨 嚴重性能問題 (>60秒):")
        print("   • 考慮使用更輕量的 LLM 模型 (qwen2.5:7b 或 llama3.2:3b)")
        print("   • 檢查 Ollama 服務器負載")
        print("   • 考慮清理 Neo4j 數據庫中的舊數據")
        print("   • 檢查系統資源使用情況")
    elif total_time > 30:
        print("⚠️ 性能問題 (>30秒):")
        print("   • 考慮調整 LLM 溫度參數")
        print("   • 檢查並發限制設置")
        print("   • 優化實體提取 prompt")
    elif total_time > 15:
        print("🟡 性能可以改進 (>15秒):")
        print("   • 考慮使用更快的嵌入模型")
        print("   • 檢查網路延遲")
    else:
        print("✅ 性能表現良好 (<15秒)")

    print(f"\n📋 建議的配置優化:")
    print(f"   • MODEL_NAME=qwen2.5:7b  (更快的模型)")
    print(f"   • LLM_TEMPERATURE=0.0    (減少隨機性)")
    print(f"   • SEMAPHORE_LIMIT=1      (避免並發競爭)")

async def main():
    print("🚀 Graphiti 性能診斷工具")
    print("=" * 60)

    # 1. 詳細性能剖析
    total_time = await profile_add_episode()

    # 2. 組件診斷
    await diagnose_components()

    # 3. 優化建議
    await suggest_optimizations(total_time)

    print(f"\n" + "=" * 60)
    print(f"診斷完成。總體 add_episode 耗時: {total_time:.2f}s")

if __name__ == "__main__":
    asyncio.run(main())