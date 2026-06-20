#!/usr/bin/env python3
"""
Cross-Encoder（重排序）客戶端模組
==================================

提供本專案可切換的 reranker 實作，解決 graphiti-core 預設行為的命中率問題：

graphiti-core 在未注入 cross_encoder 時，預設使用
`OpenAIRerankerClient(model='gpt-4.1-nano')`，並透過 OPENAI_BASE_URL 打向
本機 Ollama endpoint。Ollama 既無 `gpt-4.1-nano` 模型、也不支援 reranker
所需的 logprobs/logit_bias，導致所有 `*_cross_encoder` recipe（含 advanced_search
與 Web 進階搜尋的預設）在執行 rank() 時直接拋錯，搜尋回傳失敗。

本模組提供：
    - PassthroughCrossEncoder: 安全 no-op，永不拋錯（保底，預設）
    - LLMRerankerClient: 用任意 OpenAI 相容 provider 做相關性評分（Commit 2 補上）
    - make_bge_reranker(): 本地 BAAI/bge-reranker-v2-m3（Commit 2 補上）

選擇邏輯集中在 graphiti_mcp_server._create_cross_encoder()，依
CROSS_ENCODER_PROVIDER（llm / bge / none）路由，任何失敗都降級為 Passthrough，
確保搜尋永不因 reranker 崩潰。
"""

import logging
from typing import List, Tuple

from graphiti_core.cross_encoder.client import CrossEncoderClient

logger = logging.getLogger(__name__)


class PassthroughCrossEncoder(CrossEncoderClient):
    """
    安全的 no-op cross-encoder。

    對所有 passage 回傳固定分數，保持輸入順序（等同不重排）。
    用途：當未設定真實 reranker（CROSS_ENCODER_PROVIDER=none）或 reranker
    初始化失敗時的保底實作，避免 `*_cross_encoder` recipe 因缺少 reranker
    而拋出例外。實際的相關性排序由初篩階段（BM25 + 向量 + RRF）負責。
    """

    async def rank(self, query: str, passages: List[str]) -> List[Tuple[str, float]]:
        return [(passage, 1.0) for passage in passages]
