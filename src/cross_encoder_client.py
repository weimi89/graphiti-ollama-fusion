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
    - LLMRerankerClient: 用任意 OpenAI 相容 provider 做相關性評分（不依賴 logprobs）
    - make_bge_reranker(): 本地 BAAI/bge-reranker-v2-m3（lazy import）

選擇邏輯集中在 graphiti_mcp_server._create_cross_encoder()，依
CROSS_ENCODER_PROVIDER（llm / bge / none）路由，任何失敗都降級為 Passthrough，
確保搜尋永不因 reranker 崩潰。
"""

import json
import logging
from typing import List, Optional, Tuple

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


class LLMRerankerClient(CrossEncoderClient):
    """
    以任意 OpenAI 相容 LLM 做相關性重排的 cross-encoder。

    與 graphiti-core 內建的 OpenAIRerankerClient 不同，本實作**不依賴
    logprobs / logit_bias**（Ollama 不支援、DeepSeek/GLM/OpenRouter 支援度不一），
    改用單次批次 prompt 讓 LLM 對每個 passage 輸出 0.0~1.0 相關性分數（JSON），
    因此對所有 OpenAI 相容端點通用。

    成本控制：只對前 top_n 個候選送 LLM 評分，其餘候選保留初篩順序排在後面，
    既不丟失候選、又限制每次搜尋的 LLM 呼叫成本（單次呼叫）。
    任何評分失敗都退回初篩順序（不拋錯，不影響搜尋可用性）。
    """

    def __init__(
        self,
        model: str,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        top_n: int = 10,
    ):
        # 延遲 import，避免無謂依賴載入
        from openai import AsyncOpenAI

        self.model = model
        self.top_n = max(1, top_n)
        self._client = AsyncOpenAI(api_key=api_key or "not-needed", base_url=base_url or None)

    async def rank(self, query: str, passages: List[str]) -> List[Tuple[str, float]]:
        if not passages:
            return []

        head = list(passages[: self.top_n])
        tail = list(passages[self.top_n :])

        try:
            scores = await self._score(query, head)
        except Exception as e:
            logger.warning(f"LLM reranker 評分失敗，保留初篩順序：{e}")
            scores = [0.5] * len(head)

        ranked: List[Tuple[str, float]] = sorted(
            zip(head, scores), key=lambda x: x[1], reverse=True
        )
        # 超出 top_n 的候選不送評分，給 0 分排在重排結果之後（保持原相對順序）
        ranked.extend((p, 0.0) for p in tail)
        return ranked

    async def _score(self, query: str, passages: List[str]) -> List[float]:
        numbered = "\n".join(f"[{i}] {p}" for i, p in enumerate(passages))
        system = (
            "You are a relevance scoring engine for a knowledge-graph search system. "
            "Score how relevant each passage is to the query."
        )
        user = (
            "Given the QUERY and the numbered PASSAGES, score each passage's relevance "
            "to the query from 0.0 (irrelevant) to 1.0 (highly relevant).\n"
            'Respond ONLY with a JSON object of the form '
            '{"scores": [{"index": <int>, "score": <float>}, ...]} '
            "covering every passage index.\n\n"
            f"QUERY: {query}\n\nPASSAGES:\n{numbered}"
        )

        resp = await self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        content = (resp.choices[0].message.content or "{}").strip()
        data = json.loads(content)

        score_map = {}
        for item in data.get("scores", []):
            try:
                score_map[int(item["index"])] = float(item["score"])
            except (KeyError, TypeError, ValueError):
                continue

        # 缺漏的 index 給中性分 0.5；clamp 至 [0, 1]
        return [max(0.0, min(1.0, score_map.get(i, 0.5))) for i in range(len(passages))]


def make_bge_reranker() -> Optional[CrossEncoderClient]:
    """
    建立本地 BGE reranker（BAAI/bge-reranker-v2-m3）。

    lazy import graphiti-core 的 BGERerankerClient；缺少 sentence-transformers
    套件（或模型載入失敗）時記錄警告並回傳 None，由呼叫端降級為 Passthrough。
    首次使用會下載約 1GB 模型。
    """
    try:
        from graphiti_core.cross_encoder.bge_reranker_client import BGERerankerClient

        return BGERerankerClient()
    except Exception as e:
        logger.warning(
            f"BGE reranker 不可用（需安裝 sentence-transformers：uv sync --extra reranker）：{e}"
        )
        return None
