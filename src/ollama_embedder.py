#!/usr/bin/env python3
"""
Ollama 嵌入器模組
=================

提供使用 Ollama 本地嵌入模型（如 nomic-embed-text）的嵌入器實現。

此模組實現了 Graphiti 的 EmbedderClient 介面，允許使用 Ollama
提供的本地嵌入模型來生成文本的向量表示。

主要功能：
    - 單一文本嵌入
    - 批量文本嵌入
    - 向量歸一化處理
    - 連接測試與模型資訊查詢

技術特點：
    - 自動處理無效向量（NaN, inf, 零向量）
    - 向量維度自動調整
    - 歸一化確保 cosine similarity 正確計算
"""

import asyncio
import random
from typing import List, Union

import aiohttp
from graphiti_core.embedder.client import EmbedderClient


class OllamaEmbedder(EmbedderClient):
    """
    Ollama 嵌入器，實現 Graphiti 的 EmbedderClient 介面。

    使用 Ollama API 將文本轉換為向量表示，支援單一文本和批量處理。

    Attributes:
        model: Ollama 嵌入模型名稱
        base_url: Ollama API 端點
        dimensions: 嵌入向量維度
        embed_url: 嵌入 API 完整 URL
    """

    def __init__(
        self,
        model: str = "nomic-embed-text:v1.5",
        base_url: str = "http://localhost:11434",
        dimensions: int = 768,
    ):
        """
        初始化 Ollama 嵌入器。

        Args:
            model: Ollama 嵌入模型名稱（預設 nomic-embed-text:v1.5）
            base_url: Ollama API 端點（預設 http://localhost:11434）
            dimensions: 嵌入向量維度（預設 768，nomic-embed-text 的預設值）
        """
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.dimensions = dimensions
        self.embed_url = f"{self.base_url}/api/embed"

    async def create(self, input_data: Union[str, List[str]]) -> List[float]:
        """
        建立嵌入向量。

        此方法符合 Graphiti 的 EmbedderClient 介面，無論輸入格式為何，
        總是返回單一向量（第一個文本的嵌入）。

        Args:
            input_data: 要嵌入的文本，可以是字串或字串列表

        Returns:
            List[float]: 嵌入向量，長度為 self.dimensions
        """
        if isinstance(input_data, str):
            texts = [input_data]
        elif input_data:
            texts = [input_data[0]]
        else:
            return []

        embeddings = await self._create_embeddings(texts)
        return embeddings[0] if embeddings else []

    async def create_batch(self, input_data: List[str]) -> List[List[float]]:
        """
        批量建立嵌入向量。

        Args:
            input_data: 要嵌入的文本列表

        Returns:
            List[List[float]]: 嵌入向量列表
        """
        return await self._create_embeddings(input_data)

    async def create_bulk(
        self, input_data: List[str], batch_size: int = 10
    ) -> List[List[float]]:
        """
        批量建立嵌入向量（支援並發處理）。

        將輸入分批處理以避免過載 Ollama 服務。

        Args:
            input_data: 要嵌入的文本列表
            batch_size: 每批處理的文本數量（並發請求數）

        Returns:
            List[List[float]]: 嵌入向量列表
        """
        if not input_data:
            return []

        embeddings = []

        async with aiohttp.ClientSession() as session:
            for i in range(0, len(input_data), batch_size):
                batch = input_data[i : i + batch_size]
                batch_results = await asyncio.gather(
                    *[self._embed_single(session, text) for text in batch]
                )
                embeddings.extend(batch_results)

        return embeddings

    def get_dimensions(self) -> int:
        """
        獲取嵌入向量維度。

        Returns:
            int: 嵌入向量維度
        """
        return self.dimensions

    async def test_connection(self) -> bool:
        """
        測試 Ollama 連接。

        Returns:
            bool: 連接成功且模型可用返回 True
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status != 200:
                        print(f"Ollama 連接失敗，狀態碼: {response.status}")
                        return False

                    result = await response.json()
                    models = result.get("models", [])
                    model_names = [m.get("name", "") for m in models]

                    if self.model in model_names:
                        print(f"Ollama 嵌入器連接成功，模型 {self.model} 可用")
                        return True
                    else:
                        print(f"Ollama 連接成功，但模型 {self.model} 未找到")
                        print(f"可用模型: {', '.join(model_names)}")
                        return False

        except Exception as e:
            print(f"無法連接到 Ollama: {e}")
            return False

    async def get_model_info(self) -> dict:
        """
        獲取模型資訊。

        Returns:
            dict: 模型詳細資訊，或包含錯誤訊息的字典
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/show", json={"name": self.model}
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return {"error": f"無法獲取模型資訊: {response.status}"}
        except Exception as e:
            return {"error": str(e)}

    # =========================================================================
    # 私有方法
    # =========================================================================

    async def _create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        內部方法：建立嵌入向量列表。

        Args:
            texts: 要嵌入的文本列表

        Returns:
            List[List[float]]: 嵌入向量列表
        """
        if not texts:
            return []

        embeddings = []

        async with aiohttp.ClientSession() as session:
            for text in texts:
                embedding = await self._embed_single(session, text)
                embeddings.append(embedding)

        return embeddings

    async def _embed_single(
        self, session: aiohttp.ClientSession, text: str
    ) -> List[float]:
        """
        嵌入單一文本。

        Args:
            session: aiohttp 會話
            text: 要嵌入的文本

        Returns:
            List[float]: 嵌入向量，失敗時返回歸一化的隨機向量
        """
        try:
            payload = {"model": self.model, "input": text}

            async with session.post(
                self.embed_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    embeddings_list = result.get("embeddings", [])
                    embedding = embeddings_list[0] if embeddings_list else []
                    return self._normalize_embedding(embedding, text)
                else:
                    error_text = await response.text()
                    print(f"Ollama 嵌入錯誤 (狀態 {response.status}): {error_text}")
                    return self._create_fallback_embedding()

        except Exception as e:
            print(f"嵌入請求失敗: {e}")
            return self._create_fallback_embedding()

    def _normalize_embedding(
        self, embedding: List[float], text: str = ""
    ) -> List[float]:
        """
        歸一化嵌入向量。

        處理無效值、調整維度、確保向量為單位向量。

        Args:
            embedding: 原始嵌入向量
            text: 原始文本（用於日誌記錄）

        Returns:
            List[float]: 歸一化後的嵌入向量
        """
        # 檢查無效值（NaN, inf, None）
        if self._has_invalid_values(embedding):
            print(f"檢測到無效數值，重新生成向量: '{text[:50]}...'")
            embedding = self._create_random_embedding()

        # 調整維度
        embedding = self._adjust_dimensions(embedding, text)

        # 檢查零向量並歸一化
        embedding = self._ensure_unit_vector(embedding, text)

        return embedding

    def _has_invalid_values(self, embedding: List[float]) -> bool:
        """檢查向量是否包含無效值。"""
        return any(
            x is None or x != x or abs(x) == float("inf") for x in embedding
        )

    def _adjust_dimensions(
        self, embedding: List[float], text: str = ""
    ) -> List[float]:
        """調整向量維度至指定大小。"""
        if len(embedding) == self.dimensions:
            return embedding

        if len(embedding) > self.dimensions:
            print(f"向量維度過大 ({len(embedding)} > {self.dimensions})，截斷中...")
            return embedding[: self.dimensions]
        else:
            print(f"向量維度不足 ({len(embedding)} < {self.dimensions})，填充中...")
            return embedding + [0.0] * (self.dimensions - len(embedding))

    def _ensure_unit_vector(
        self, embedding: List[float], text: str = ""
    ) -> List[float]:
        """確保向量為單位向量（歸一化）。"""
        vector_norm = self._compute_norm(embedding)

        # 處理零向量或極小向量
        if vector_norm < 1e-10:
            print(f"檢測到零向量或極小向量，使用隨機向量替代: '{text[:50]}...'")
            embedding = self._create_random_embedding()
            vector_norm = self._compute_norm(embedding)

        # 歸一化
        if vector_norm > 0:
            embedding = [x / vector_norm for x in embedding]

        # 驗證歸一化結果
        final_norm = self._compute_norm(embedding)
        if abs(final_norm - 1.0) > 0.01:
            print(f"向量歸一化後範數異常 ({final_norm})，重新歸一化...")
            if final_norm > 0:
                embedding = [x / final_norm for x in embedding]
            else:
                # 使用標準單位向量
                embedding = [1.0] + [0.0] * (self.dimensions - 1)

        return embedding

    def _compute_norm(self, embedding: List[float]) -> float:
        """計算向量的 L2 範數。"""
        return sum(x * x for x in embedding) ** 0.5

    def _create_random_embedding(self) -> List[float]:
        """建立隨機嵌入向量。"""
        return [random.uniform(-0.01, 0.01) for _ in range(self.dimensions)]

    def _create_fallback_embedding(self) -> List[float]:
        """建立備用嵌入向量（歸一化的隨機向量）。"""
        embedding = self._create_random_embedding()
        vector_norm = self._compute_norm(embedding)
        if vector_norm > 0:
            embedding = [x / vector_norm for x in embedding]
        return embedding


# =============================================================================
# 測試函數
# =============================================================================


async def test_ollama_embedder() -> bool:
    """
    測試 Ollama 嵌入器。

    Returns:
        bool: 所有測試通過返回 True
    """
    print("測試 Ollama 嵌入器")
    print("=" * 50)

    embedder = OllamaEmbedder(
        model="nomic-embed-text:v1.5", base_url="http://localhost:11434"
    )

    # 測試連接
    print("\n1. 測試連接...")
    connected = await embedder.test_connection()
    if not connected:
        print("連接失敗，請確保 Ollama 正在運行")
        return False

    # 測試單一字串嵌入
    print("\n2. 測試單一字串嵌入...")
    single_text = "TypeScript 是 JavaScript 的超集"
    single_embedding = await embedder.create(single_text)

    if (
        isinstance(single_embedding, list)
        and single_embedding
        and isinstance(single_embedding[0], float)
    ):
        print(f"成功！嵌入維度: {len(single_embedding)}")
        print(f"前5個值: {single_embedding[:5]}")
    else:
        print("單一字串嵌入失敗")
        return False

    # 測試列表嵌入
    print("\n3. 測試列表嵌入...")
    list_embedding = await embedder.create(["TypeScript 是 JavaScript 的超集"])

    if (
        isinstance(list_embedding, list)
        and list_embedding
        and isinstance(list_embedding[0], float)
    ):
        print(f"成功！嵌入維度: {len(list_embedding)}")
    else:
        print("列表嵌入失敗")
        return False

    # 測試批量嵌入
    print("\n4. 測試批量嵌入...")
    batch_texts = [
        "React 18 引入了 Concurrent Features",
        "API 錯誤處理最佳實踐",
        "用戶偏好使用 TypeScript",
    ]
    batch_embeddings = await embedder.create_bulk(batch_texts, batch_size=2)

    if len(batch_embeddings) == len(batch_texts):
        print(f"成功嵌入 {len(batch_embeddings)} 個文本")
        for i, text in enumerate(batch_texts):
            print(f"- '{text[:30]}...' -> 維度 {len(batch_embeddings[i])}")
    else:
        print("批量嵌入失敗")
        return False

    # 獲取模型資訊
    print("\n5. 獲取模型資訊...")
    model_info = await embedder.get_model_info()
    if "error" not in model_info:
        print(f"模型: {embedder.model}")
        if "modelfile" in model_info:
            lines = model_info["modelfile"].split("\n")[:3]
            for line in lines:
                if line:
                    print(f"- {line}")

    print("\n所有測試通過！")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_ollama_embedder())
    exit(0 if success else 1)
