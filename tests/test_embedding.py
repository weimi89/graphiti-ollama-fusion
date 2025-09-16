#!/usr/bin/env python3
"""
測試嵌入向量問題
"""
import asyncio
from ollama_embedder import OllamaEmbedder

async def test_embeddings():
    """測試嵌入向量生成"""
    print("🧲 測試嵌入向量生成...")

    embedder = OllamaEmbedder(
        model="nomic-embed-text:v1.5",
        base_url="http://localhost:11434"
    )

    # 測試連接
    connected = await embedder.test_connection()
    print(f"連接狀態: {connected}")

    # 測試嵌入生成
    test_texts = [
        "這是一個測試文字",
        "另一個測試句子",
        ""  # 空字符串測試
    ]

    for i, text in enumerate(test_texts):
        print(f"\n測試文字 {i+1}: '{text}'")
        try:
            embeddings = await embedder.create([text])
            if embeddings:
                embedding = embeddings[0]
                print(f"   嵌入維度: {len(embedding)}")
                print(f"   前5個值: {embedding[:5]}")
                print(f"   是否全零: {all(x == 0.0 for x in embedding)}")
                print(f"   向量範數: {sum(x*x for x in embedding)**0.5:.6f}")
            else:
                print("   ❌ 沒有返回嵌入向量")
        except Exception as e:
            print(f"   ❌ 錯誤: {e}")

if __name__ == "__main__":
    asyncio.run(test_embeddings())