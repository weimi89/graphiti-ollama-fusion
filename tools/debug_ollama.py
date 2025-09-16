#!/usr/bin/env python3
"""
調試 Ollama 實體提取響應
"""
import asyncio
import json
from ollama_graphiti_client import OptimizedOllamaClient
from graphiti_core.llm_client.config import LLMConfig

async def test_ollama_response():
    """測試 Ollama 的實際響應格式"""

    config = LLMConfig(
        api_key="not-needed",
        model="qwen2.5:14b",
        base_url="http://localhost:11434",
        temperature=0.1
    )

    client = OptimizedOllamaClient(config)

    # 測試消息
    messages = [{
        "role": "user",
        "content": "提取這段文字的實體: 這是一個快速測試記憶"
    }]

    print("🔍 測試 Ollama 請求和響應...")
    print(f"輸入: {messages[0]['content']}")

    try:
        # 直接調用底層請求方法
        response_text = await client._make_request(messages, json_mode=True)
        print(f"\n📤 原始響應: {repr(response_text)}")

        # 測試 JSON 解析
        json_data = client._extract_json_from_response(response_text)
        print(f"\n📋 解析後的 JSON: {json_data}")

        # 檢查結構
        if 'extracted_entities' in json_data:
            print(f"\n✅ 找到 extracted_entities 字段")
            entities = json_data['extracted_entities']
            print(f"實體類型: {type(entities)}")
            print(f"實體內容: {entities}")

            if isinstance(entities, list):
                print(f"實體數量: {len(entities)}")
                for i, entity in enumerate(entities):
                    print(f"  實體 {i}: {entity} (類型: {type(entity)})")
        else:
            print("❌ 沒有找到 extracted_entities 字段")
            print(f"可用字段: {list(json_data.keys())}")

    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ollama_response())