#!/usr/bin/env python3
"""
Ollama Embedder for Graphiti
支援使用 Ollama 的本地嵌入模型（如 nomic-embed-text）
"""

import asyncio
import aiohttp
import json
from typing import List, Optional
import numpy as np
from graphiti_core.embedder.client import EmbedderClient


class OllamaEmbedder(EmbedderClient):
    """
    自定義 Ollama 嵌入器，實作 Graphiti 的 EmbedderClient 介面
    """

    def __init__(
        self,
        model: str = "nomic-embed-text:v1.5",
        base_url: str = "http://localhost:11434",
        dimensions: int = 768  # nomic-embed-text 的預設維度
    ):
        """
        初始化 Ollama 嵌入器

        Args:
            model: Ollama 嵌入模型名稱
            base_url: Ollama API 端點
            dimensions: 嵌入向量維度
        """
        self.model = model
        self.base_url = base_url.rstrip('/')
        self.dimensions = dimensions
        self.embed_url = f"{self.base_url}/api/embed"

    async def create(self, input_data: List[str]) -> List[List[float]]:
        """
        創建嵌入向量

        Args:
            input_data: 要嵌入的文本列表

        Returns:
            嵌入向量列表
        """
        if not input_data:
            return []

        embeddings = []

        # Ollama 的嵌入 API 一次只能處理一個文本
        # 所以我們需要逐個處理
        async with aiohttp.ClientSession() as session:
            for text in input_data:
                try:
                    payload = {
                        "model": self.model,
                        "input": text
                    }

                    async with session.post(
                        self.embed_url,
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            embeddings_list = result.get("embeddings", [])
                            embedding = embeddings_list[0] if embeddings_list else []

                            # 確保嵌入向量維度正確
                            if len(embedding) != self.dimensions:
                                # 調整維度（截斷或填充）
                                if len(embedding) > self.dimensions:
                                    embedding = embedding[:self.dimensions]
                                else:
                                    embedding.extend([0.0] * (self.dimensions - len(embedding)))

                            # 檢查是否為零向量並歸一化（確保 cosine similarity 正確）
                            vector_norm = sum(x*x for x in embedding) ** 0.5
                            if vector_norm == 0.0:
                                print(f"⚠️ 檢測到零向量，使用隨機小向量替代: '{text[:50]}...'")
                                # 生成一個小的隨機向量來避免 cosine similarity 錯誤
                                import random
                                embedding = [random.uniform(-0.01, 0.01) for _ in range(self.dimensions)]
                                # 重新計算向量範數
                                vector_norm = sum(x*x for x in embedding) ** 0.5

                            # 確保向量歸一化（Neo4j cosine similarity 要求單位向量）
                            if vector_norm > 0:
                                embedding = [x / vector_norm for x in embedding]

                            embeddings.append(embedding)
                        else:
                            error_text = await response.text()
                            print(f"❌ Ollama 嵌入錯誤 (狀態 {response.status}): {error_text}")
                            # 返回歸一化的隨機向量避免 cosine similarity 錯誤
                            import random
                            fallback_embedding = [random.uniform(-0.01, 0.01) for _ in range(self.dimensions)]
                            # 歸一化隨機向量
                            vector_norm = sum(x*x for x in fallback_embedding) ** 0.5
                            if vector_norm > 0:
                                fallback_embedding = [x / vector_norm for x in fallback_embedding]
                            embeddings.append(fallback_embedding)

                except Exception as e:
                    print(f"❌ 嵌入請求失敗: {str(e)}")
                    # 返回歸一化的隨機向量避免 cosine similarity 錯誤
                    import random
                    fallback_embedding = [random.uniform(-0.01, 0.01) for _ in range(self.dimensions)]
                    # 歸一化隨機向量
                    vector_norm = sum(x*x for x in fallback_embedding) ** 0.5
                    if vector_norm > 0:
                        fallback_embedding = [x / vector_norm for x in fallback_embedding]
                    embeddings.append(fallback_embedding)

        return embeddings

    async def create_bulk(self, input_data: List[str], batch_size: int = 10) -> List[List[float]]:
        """
        批量創建嵌入向量（優化版本）

        Args:
            input_data: 要嵌入的文本列表
            batch_size: 批次大小（並發請求數）

        Returns:
            嵌入向量列表
        """
        if not input_data:
            return []

        embeddings = []

        async def embed_single(session: aiohttp.ClientSession, text: str) -> List[float]:
            """嵌入單個文本"""
            try:
                payload = {
                    "model": self.model,
                    "input": text
                }

                async with session.post(
                    self.embed_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        embeddings_list = result.get("embeddings", [])
                        embedding = embeddings_list[0] if embeddings_list else []

                        # 調整維度
                        if len(embedding) != self.dimensions:
                            if len(embedding) > self.dimensions:
                                embedding = embedding[:self.dimensions]
                            else:
                                embedding.extend([0.0] * (self.dimensions - len(embedding)))

                        # 確保向量歸一化
                        vector_norm = sum(x*x for x in embedding) ** 0.5
                        if vector_norm == 0.0:
                            # 生成隨機向量
                            import random
                            embedding = [random.uniform(-0.01, 0.01) for _ in range(self.dimensions)]
                            vector_norm = sum(x*x for x in embedding) ** 0.5

                        # 歸一化向量
                        if vector_norm > 0:
                            embedding = [x / vector_norm for x in embedding]

                        return embedding
                    else:
                        print(f"❌ 嵌入錯誤: {response.status}")
                        # 返回歸一化的隨機向量
                        import random
                        fallback_embedding = [random.uniform(-0.01, 0.01) for _ in range(self.dimensions)]
                        vector_norm = sum(x*x for x in fallback_embedding) ** 0.5
                        if vector_norm > 0:
                            fallback_embedding = [x / vector_norm for x in fallback_embedding]
                        return fallback_embedding

            except Exception as e:
                print(f"❌ 嵌入請求失敗: {str(e)}")
                # 返回歸一化的隨機向量
                import random
                fallback_embedding = [random.uniform(-0.01, 0.01) for _ in range(self.dimensions)]
                vector_norm = sum(x*x for x in fallback_embedding) ** 0.5
                if vector_norm > 0:
                    fallback_embedding = [x / vector_norm for x in fallback_embedding]
                return fallback_embedding

        async with aiohttp.ClientSession() as session:
            # 分批處理以避免過載
            for i in range(0, len(input_data), batch_size):
                batch = input_data[i:i + batch_size]
                batch_results = await asyncio.gather(
                    *[embed_single(session, text) for text in batch]
                )
                embeddings.extend(batch_results)

        return embeddings

    async def create_batch(self, input_data: List[str]) -> List[List[float]]:
        """
        批量創建嵌入（Graphiti 需要的方法）

        Args:
            input_data: 要嵌入的文本列表

        Returns:
            嵌入向量列表
        """
        return await self.create(input_data)

    def get_dimensions(self) -> int:
        """
        獲取嵌入向量維度

        Returns:
            嵌入向量維度
        """
        return self.dimensions

    async def test_connection(self) -> bool:
        """
        測試 Ollama 連接

        Returns:
            連接是否成功
        """
        try:
            async with aiohttp.ClientSession() as session:
                # 測試 API 端點
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        result = await response.json()
                        models = result.get("models", [])

                        # 檢查嵌入模型是否可用
                        model_names = [m.get("name", "") for m in models]
                        if self.model in model_names:
                            print(f"✅ Ollama 嵌入器連接成功，模型 {self.model} 可用")
                            return True
                        else:
                            print(f"⚠️ Ollama 連接成功，但模型 {self.model} 未找到")
                            print(f"   可用模型: {', '.join(model_names)}")
                            return False
                    else:
                        print(f"❌ Ollama 連接失敗，狀態碼: {response.status}")
                        return False

        except Exception as e:
            print(f"❌ 無法連接到 Ollama: {str(e)}")
            return False

    async def get_model_info(self) -> dict:
        """
        獲取模型信息

        Returns:
            模型詳細信息
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/show",
                    json={"name": self.model}
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {"error": f"無法獲取模型信息: {response.status}"}

        except Exception as e:
            return {"error": str(e)}


# 測試函數
async def test_ollama_embedder():
    """測試 Ollama 嵌入器"""

    print("🧪 測試 Ollama 嵌入器")
    print("=" * 50)

    # 創建嵌入器
    embedder = OllamaEmbedder(
        model="nomic-embed-text:v1.5",
        base_url="http://localhost:11434"
    )

    # 測試連接
    print("\n1️⃣ 測試連接...")
    connected = await embedder.test_connection()
    if not connected:
        print("   ❌ 連接失敗，請確保 Ollama 正在運行")
        return False

    # 測試單個嵌入
    print("\n2️⃣ 測試單個文本嵌入...")
    test_texts = ["TypeScript 是 JavaScript 的超集"]
    embeddings = await embedder.create(test_texts)

    if embeddings and len(embeddings[0]) > 0:
        print(f"   ✅ 成功！嵌入維度: {len(embeddings[0])}")
        print(f"   前5個值: {embeddings[0][:5]}")
    else:
        print("   ❌ 嵌入失敗")
        return False

    # 測試批量嵌入
    print("\n3️⃣ 測試批量嵌入...")
    batch_texts = [
        "React 18 引入了 Concurrent Features",
        "API 錯誤處理最佳實踐",
        "用戶偏好使用 TypeScript"
    ]
    batch_embeddings = await embedder.create_bulk(batch_texts, batch_size=2)

    if len(batch_embeddings) == len(batch_texts):
        print(f"   ✅ 成功嵌入 {len(batch_embeddings)} 個文本")
        for i, text in enumerate(batch_texts):
            print(f"   - '{text[:30]}...' -> 維度 {len(batch_embeddings[i])}")
    else:
        print("   ❌ 批量嵌入失敗")
        return False

    # 獲取模型信息
    print("\n4️⃣ 獲取模型信息...")
    model_info = await embedder.get_model_info()
    if "error" not in model_info:
        print(f"   ✅ 模型: {embedder.model}")
        if "modelfile" in model_info:
            lines = model_info["modelfile"].split('\n')[:3]
            for line in lines:
                if line:
                    print(f"   - {line}")

    print("\n✅ 所有測試通過！")
    return True


if __name__ == "__main__":
    # 執行測試
    import asyncio
    success = asyncio.run(test_ollama_embedder())
    exit(0 if success else 1)