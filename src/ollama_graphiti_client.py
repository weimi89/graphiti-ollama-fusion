#!/usr/bin/env python3
"""
優化的 Ollama Graphiti 客戶端模組
==================================

提供專門針對 Graphiti 框架優化的 Ollama LLM 客戶端。

此模組解決了使用 Ollama 與 Graphiti 整合時常見的問題，包括：
- Pydantic 模型驗證與修復
- JSON 響應解析與欄位映射
- 實體提取的結構化輸出處理

主要類別：
    - OptimizedOllamaClient: 優化的 LLM 客戶端
    - SimpleCrossEncoder: 簡化的 Cross-encoder 實現

技術特點：
    - 自動修復 Pydantic 驗證錯誤
    - 支援多種 JSON 響應格式
    - 實體欄位自動映射
"""

import asyncio
import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)
from dotenv import load_dotenv

from graphiti_core import Graphiti
from graphiti_core.cross_encoder.client import CrossEncoderClient
from graphiti_core.llm_client.client import LLMClient
from graphiti_core.llm_client.config import LLMConfig

from .ollama_embedder import OllamaEmbedder

load_dotenv()

# 確保導入路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class OptimizedOllamaClient(LLMClient):
    """
    優化的 Ollama LLM 客戶端。

    專門為 Graphiti 框架設計，處理 Pydantic 模型驗證和 JSON 響應解析。

    Attributes:
        base_url: Ollama API 端點
        model: 使用的模型名稱
        temperature: 生成溫度
    """

    def __init__(self, config: LLMConfig):
        """
        初始化客戶端。

        Args:
            config: LLM 配置物件
        """
        super().__init__(config)
        self.base_url = config.base_url or "http://localhost:11434"
        self.model = config.model if config.model else "llama3.2:3b"
        self.temperature = config.temperature if config.temperature is not None else 0.0
        logger.info(f"    使用模型: {self.model}")

    async def _generate_response(
        self,
        messages: List[Any],
        response_model: Optional[Any] = None,
        **kwargs,
    ) -> Any:
        """實現抽象方法 _generate_response。"""
        return await self.generate_response(messages, response_model)

    async def generate_response(
        self,
        messages: List[Any],
        response_model: Optional[Any] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> Any:
        """
        生成 LLM 響應。

        Args:
            messages: 訊息列表（字串或訊息物件）
            response_model: 可選的 Pydantic 響應模型
            max_tokens: 最大 token 數（未使用）

        Returns:
            Any: 如果指定 response_model 則返回解析後的字典，否則返回純文字
        """
        # 處理字串輸入
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        # 轉換訊息格式
        ollama_messages = self._convert_messages(messages)

        # 如果需要結構化輸出
        if response_model:
            return await self._generate_structured_response(ollama_messages, response_model)

        # 純文字響應
        return await self._make_request(ollama_messages)

    async def generate_response_with_retry(
        self,
        messages: List[Any],
        response_model: Optional[Any] = None,
        max_attempts: int = 3,
    ) -> Any:
        """
        帶重試機制的響應生成。

        Args:
            messages: 訊息列表
            response_model: 可選的響應模型
            max_attempts: 最大重試次數

        Returns:
            Any: 生成的響應，或失敗時返回預設值
        """
        for attempt in range(max_attempts):
            try:
                result = await self.generate_response(messages, response_model)
                if result:
                    return result
            except Exception as e:
                if attempt < max_attempts - 1:
                    await asyncio.sleep(2**attempt)
                else:
                    logger.error(f"所有重試都失敗: {e}")

        # 返回預設值
        return self._create_fallback_response(response_model)

    # =========================================================================
    # 私有方法
    # =========================================================================

    def _convert_messages(self, messages: List[Any]) -> List[Dict[str, str]]:
        """轉換訊息格式為 Ollama 格式。"""
        ollama_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                ollama_messages.append(msg)
            else:
                ollama_messages.append(
                    {
                        "role": getattr(msg, "role", "user"),
                        "content": getattr(msg, "content", str(msg)),
                    }
                )
        return ollama_messages

    async def _make_request(
        self, messages: List[Dict[str, str]], json_mode: bool = False,
        max_retries: int = 3, timeout: int = 120,
    ) -> str:
        """
        發送請求到 Ollama API，含指數退避重試。

        Args:
            messages: 訊息列表
            json_mode: 是否要求 JSON 格式回應
            max_retries: 最大重試次數
            timeout: 請求超時秒數
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "temperature": self.temperature,
            "options": {"temperature": self.temperature, "num_predict": 4096},
        }

        if json_mode:
            payload["format"] = "json"

        url = f"{self.base_url}/api/chat"

        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url, json=payload,
                        timeout=aiohttp.ClientTimeout(total=timeout),
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            return result.get("message", {}).get("content", "")
                        elif response.status in (503, 429):
                            # 服務暫時不可用或速率限制，重試
                            error_text = await response.text()
                            wait = 2 ** attempt
                            logger.warning(
                                f"Ollama 暫時不可用 (HTTP {response.status})，"
                                f"{wait}s 後重試 ({attempt+1}/{max_retries}): {error_text[:100]}"
                            )
                            await asyncio.sleep(wait)
                            continue
                        else:
                            error_text = await response.text()
                            logger.error(f"Ollama 錯誤 (HTTP {response.status}): {error_text[:200]}")
                            return ""

            except asyncio.TimeoutError:
                wait = 2 ** attempt
                logger.warning(
                    f"Ollama 請求超時 ({timeout}s)，"
                    f"{wait}s 後重試 ({attempt+1}/{max_retries})"
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"Ollama 請求在 {max_retries} 次重試後仍超時")
                    return ""

            except aiohttp.ClientError as e:
                wait = 2 ** attempt
                logger.warning(
                    f"Ollama 連線錯誤: {e}，"
                    f"{wait}s 後重試 ({attempt+1}/{max_retries})"
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"Ollama 連線在 {max_retries} 次重試後仍失敗: {e}")
                    return ""

        return ""

    async def _generate_structured_response(
        self, messages: List[Dict[str, str]], response_model: Any
    ) -> Optional[Dict]:
        """生成結構化響應並解析為 Pydantic 模型。"""
        # 添加實體提取的系統提示
        if hasattr(response_model, "__annotations__"):
            system_prompt = self._build_entity_extraction_prompt(response_model)
            messages.append({"role": "system", "content": system_prompt})

        # 發送請求
        response_text = await self._make_request(messages, json_mode=True)

        if not response_text:
            return self._create_fallback_response(response_model)

        # 解析 JSON
        json_data = self._extract_json_from_response(response_text)

        # 修復欄位映射
        json_data = self._fix_field_mappings(json_data)

        # 驗證並返回
        return self._validate_response(json_data, response_model)

    def _build_entity_extraction_prompt(self, response_model: Any) -> str:
        """建立實體提取的系統提示。"""
        fields = {}
        for field_name, field_type in response_model.__annotations__.items():
            if hasattr(field_type, "__origin__"):
                if field_type.__origin__ == list:
                    fields[field_name] = "array"
                elif field_type.__origin__ == dict:
                    fields[field_name] = "object"
                else:
                    fields[field_name] = "string"
            else:
                type_map = {
                    str: "string",
                    int: "number",
                    float: "number",
                    bool: "boolean",
                    list: "array",
                    dict: "object",
                }
                fields[field_name] = type_map.get(field_type, "string")

        schema_hint = f"Return a JSON object with these fields: {json.dumps(fields)}"

        return f"""You are an entity extraction assistant. Extract ALL entities and relationships from text.

IMPORTANT:
1. Extract ALL entities mentioned (people, organizations, technologies, concepts)
2. Each entity should have a unique name
3. Entity types: 0=Person, 1=Organization, 2=Technology, 3=Concept, 4=Place, 5=Other
4. Include observations about each entity
5. Respond with valid JSON only

{schema_hint}"""

    def _extract_json_from_response(self, response: str) -> Dict:
        """從響應中提取 JSON。"""
        # 嘗試直接解析
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # 嘗試提取 JSON 塊
        patterns = [
            r"```json\s*(.*?)\s*```",
            r"```\s*(.*?)\s*```",
            r"\{[^}]*\}",
            r"\{.*\}",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue

        return {}

    def _fix_field_mappings(self, json_data: Dict) -> Dict:
        """修復常見的欄位名稱映射問題。"""
        # 處理中文欄位名
        if "實體" in json_data:
            json_data["extracted_entities"] = json_data.pop("實體")

        # 修復實體欄位
        if "extracted_entities" in json_data:
            entities = json_data["extracted_entities"]
            if isinstance(entities, list):
                json_data["extracted_entities"] = [
                    self._fix_entity_fields(e) for e in entities if isinstance(e, dict)
                ]

        # 修復邊欄位
        if "edges" in json_data:
            edges = json_data["edges"]
            if isinstance(edges, list):
                json_data["edges"] = [
                    self._fix_edge_fields(e, json_data) for e in edges if isinstance(e, dict)
                ]

        # 修復實體解析欄位
        if "entity_resolutions" in json_data:
            resolutions = json_data["entity_resolutions"]
            if isinstance(resolutions, list):
                json_data["entity_resolutions"] = [
                    self._fix_resolution_fields(r) for r in resolutions if isinstance(r, dict)
                ]

        return json_data

    def _fix_entity_fields(self, entity: Dict) -> Dict:
        """修復單一實體的欄位。"""
        # 名稱欄位映射
        if "entity_name" in entity and "name" not in entity:
            entity["name"] = entity.pop("entity_name")

        # 類型欄位映射
        if "entity_type_name" in entity and "entity_type" not in entity:
            entity["entity_type"] = entity.pop("entity_type_name")

        # 處理 summary 欄位
        summary = entity.get("summary")
        if isinstance(summary, dict):
            entity["summary"] = str(
                summary.get("description", summary.get("content", entity.get("name", "")))
            )
        elif summary is None:
            entity["summary"] = entity.get("observation", entity.get("name", ""))

        # 確保 entity_summary
        if "entity_summary" not in entity:
            entity["entity_summary"] = entity.get(
                "summary", entity.get("description", entity.get("name", ""))
            )
        if isinstance(entity.get("entity_summary"), dict):
            entity["entity_summary"] = str(entity["entity_summary"].get("description", ""))

        # 確保 observations
        if "observations" not in entity:
            entity["observations"] = [
                entity.get(
                    "observation",
                    entity.get("description", f"Related to {entity.get('name', 'entity')}"),
                )
            ]
        elif isinstance(entity.get("observations"), str):
            entity["observations"] = [entity["observations"]]

        # 確保 entity_type_id
        entity["entity_type_id"] = 0  # 強制設為 0 以避免 index out of range

        # 新版本 Graphiti 需要的欄位
        entity.setdefault("duplicates", [])
        entity.setdefault("potential_duplicates", [])

        # 移除不需要的欄位
        for key in ["description", "score", "mentioned", "speaker"]:
            entity.pop(key, None)

        return entity

    def _fix_edge_fields(self, edge: Dict, json_data: Dict) -> Dict:
        """修復單一邊的欄位。"""
        entities = json_data.get("extracted_entities", [])

        # 來源 ID 映射
        for src_key in ["source_id", "subject_id", "source", "subject"]:
            if src_key in edge and "source_entity_id" not in edge:
                edge["source_entity_id"] = edge.pop(src_key)

        # 目標 ID 映射
        for tgt_key in ["target_id", "object_id", "target", "object"]:
            if tgt_key in edge and "target_entity_id" not in edge:
                edge["target_entity_id"] = edge.pop(tgt_key)

        # 嘗試透過名稱查找實體索引（比盲目預設 0/1 更準確）
        edge["source_entity_id"] = self._resolve_entity_id(
            edge.get("source_entity_id"), entities, fallback=0
        )
        edge["target_entity_id"] = self._resolve_entity_id(
            edge.get("target_entity_id"), entities,
            fallback=min(1, len(entities) - 1) if entities else 0,
        )

        # 關係類型映射
        for rel_key in ["relationship", "predicate"]:
            if rel_key in edge and "relation_type" not in edge:
                edge["relation_type"] = edge.pop(rel_key)

        if "relation_type" not in edge:
            edge["relation_type"] = "RELATES_TO"

        # 確保必要欄位
        edge.setdefault("fact", edge.get("relation_type", "relates to"))
        edge.setdefault("fact_embedding", None)
        edge.setdefault("valid_at", None)
        edge.setdefault("invalid_at", None)

        return edge

    def _resolve_entity_id(
        self, value: Any, entities: List[Dict], fallback: int = 0
    ) -> int:
        """
        將 LLM 返回的實體引用解析為正確的整數索引。

        支援多種格式：整數、"ENTITY_X"、實體名稱字串。
        優先透過名稱匹配實體列表，比盲目使用預設值更準確。

        Args:
            value: LLM 返回的實體引用（int / str / None）
            entities: 已提取的實體列表
            fallback: 所有匹配失敗時的預設值

        Returns:
            int: 實體在列表中的索引（已確保在有效範圍內）
        """
        max_idx = max(len(entities) - 1, 0)

        if value is None:
            return min(fallback, max_idx)

        # 整數：直接使用（夾緊到有效範圍）
        if isinstance(value, int):
            return max(0, min(value, max_idx))

        if isinstance(value, str):
            # 格式 "ENTITY_0"
            if value.startswith("ENTITY_"):
                try:
                    idx = int(value.replace("ENTITY_", ""))
                    return max(0, min(idx, max_idx))
                except ValueError:
                    pass

            # 純數字字串
            try:
                idx = int(value)
                return max(0, min(idx, max_idx))
            except ValueError:
                pass

            # 透過實體名稱匹配（核心改進）
            value_lower = value.strip().lower()
            for i, entity in enumerate(entities):
                entity_name = entity.get("name", "").strip().lower()
                if entity_name and entity_name == value_lower:
                    return i

            # 部分匹配（名稱包含或被包含）
            for i, entity in enumerate(entities):
                entity_name = entity.get("name", "").strip().lower()
                if entity_name and (
                    value_lower in entity_name or entity_name in value_lower
                ):
                    return i

        return min(fallback, max_idx)

    def _fix_resolution_fields(self, resolution: Dict) -> Dict:
        """修復實體解析欄位。"""
        if "duplication_idx" in resolution:
            resolution["duplicate_idx"] = resolution.pop("duplication_idx")

        resolution.setdefault("duplicate_idx", -1)
        resolution.setdefault("additional_duplicates", [])
        resolution.setdefault("duplicates", [])
        resolution.setdefault("potential_duplicates", [])

        return resolution

    def _validate_response(
        self, json_data: Dict, response_model: Any
    ) -> Optional[Dict]:
        """驗證響應並轉換為 Pydantic 模型。"""
        if not hasattr(response_model, "model_validate"):
            return json_data

        # 確保所有必要欄位存在
        self._ensure_required_fields(json_data, response_model)

        try:
            validated = response_model.model_validate(json_data)
            return validated.model_dump()
        except Exception as e:
            logger.warning(f"Pydantic 驗證失敗: {e}")

            # 嘗試增強修復
            try:
                self._fix_summary_fields(json_data)
                validated = response_model.model_validate(json_data)
                return validated.model_dump()
            except Exception as retry_e:
                logger.warning(f"增強修復重試失敗: {retry_e}")

            # 嘗試最小有效實例
            return self._create_fallback_response(response_model, json_data)

    def _ensure_required_fields(self, json_data: Dict, response_model: Any) -> None:
        """確保所有必要欄位存在。"""
        if not hasattr(response_model, "__annotations__"):
            return

        for field_name, field_type in response_model.__annotations__.items():
            if field_name not in json_data:
                if hasattr(field_type, "__origin__"):
                    if field_type.__origin__ == list:
                        json_data[field_name] = []
                    elif field_type.__origin__ == dict:
                        json_data[field_name] = {}
                    else:
                        json_data[field_name] = ""
                elif field_type == bool:
                    json_data[field_name] = False
                elif field_type in (int, float):
                    json_data[field_name] = 0
                else:
                    json_data[field_name] = ""

    def _fix_summary_fields(self, data: Any) -> None:
        """迭代修復所有 summary 欄位的類型問題（避免深遞迴）。"""
        stack = [data]
        while stack:
            current = stack.pop()
            if isinstance(current, dict):
                for key, value in current.items():
                    if key == "summary" and isinstance(value, dict):
                        current[key] = str(
                            value.get("description", value.get("content", str(value)))
                        )
                    elif isinstance(value, (dict, list)):
                        stack.append(value)
            elif isinstance(current, list):
                stack.extend(
                    item for item in current if isinstance(item, (dict, list))
                )

    def _create_fallback_response(
        self, response_model: Optional[Any], json_data: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        建立備用響應。

        優先使用 json_data 中的已有值，缺失的欄位用型別預設值填充。
        可替代原本 _create_empty_response 和 _create_minimal_response 的功能。
        """
        if not response_model or not hasattr(response_model, "model_validate"):
            return None

        src = json_data or {}
        try:
            fallback_data: Dict[str, Any] = {}
            for field_name, field_type in response_model.__annotations__.items():
                if field_name in src:
                    fallback_data[field_name] = src[field_name]
                elif hasattr(field_type, "__origin__"):
                    if field_type.__origin__ == list:
                        fallback_data[field_name] = []
                    elif field_type.__origin__ == dict:
                        fallback_data[field_name] = {}
                    else:
                        fallback_data[field_name] = ""
                elif field_type == bool:
                    fallback_data[field_name] = False
                elif field_type in (int, float):
                    fallback_data[field_name] = 0
                else:
                    fallback_data[field_name] = ""

            validated = response_model.model_validate(fallback_data)
            return validated.model_dump()
        except Exception:
            return None


class SimpleCrossEncoder(CrossEncoderClient):
    """
    簡化的 Cross-encoder 實現。

    使用預設分數，適用於不需要精確重排序的場景。
    """

    async def rank(self, query: str, passages: List[str]) -> List[tuple]:
        """
        對段落進行排序。

        Args:
            query: 查詢文字
            passages: 段落列表

        Returns:
            List[tuple]: (段落, 分數) 的列表，所有分數為 1.0
        """
        return [(passage, 1.0) for passage in passages]


# =============================================================================
# 測試函數
# =============================================================================


async def main() -> bool:
    """主測試函數。"""
    print("=" * 70)
    print("優化的 Ollama + Graphiti 解決方案測試")
    print("=" * 70)

    print("\n環境配置:")
    print(f"  Neo4j URI: {os.getenv('NEO4J_URI', 'bolt://localhost:7687')}")
    print(f"  Neo4j User: {os.getenv('NEO4J_USER', 'neo4j')}")
    print("  Model: qwen2.5:14b")
    print("  Embedder: nomic-embed-text:v1.5")

    try:
        # 初始化 LLM
        print("\n初始化 Ollama LLM...")
        llm_config = LLMConfig(
            api_key="not-needed",
            model="qwen2.5:14b",
            base_url="http://localhost:11434",
            temperature=0.1,
        )
        llm_client = OptimizedOllamaClient(llm_config)
        print("  LLM 初始化成功")

        # 初始化嵌入器
        print("\n初始化嵌入器...")
        embedder = OllamaEmbedder(
            model="nomic-embed-text:v1.5", base_url="http://localhost:11434"
        )
        if not await embedder.test_connection():
            print("  嵌入器連接失敗")
            return False
        print("  嵌入器初始化成功")

        # 初始化 Cross-encoder
        print("\n初始化 Cross-encoder...")
        cross_encoder = SimpleCrossEncoder()
        print("  Cross-encoder 初始化成功")

        # 初始化 Graphiti
        print("\n初始化 Graphiti...")
        graphiti = Graphiti(
            uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            user=os.getenv("NEO4J_USER", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", "password"),
            llm_client=llm_client,
            embedder=embedder,
            cross_encoder=cross_encoder,
        )

        await graphiti.build_indices_and_constraints()
        print("  Graphiti 初始化成功")

        # 添加測試記憶
        print("\n添加測試記憶...")
        test_episodes = [
            {"name": "用戶偏好", "content": "用戶 RD-CAT 偏好使用 TypeScript 進行開發。"},
            {"name": "技術知識", "content": "React 18 引入了 Concurrent Features。"},
            {"name": "最佳實踐", "content": "API 錯誤處理應該包含錯誤日誌和重試機制。"},
        ]

        for episode in test_episodes:
            print(f"  添加: {episode['name']}")
            try:
                await graphiti.add_episode(
                    name=episode["name"],
                    episode_body=episode["content"],
                    source_description="Ollama 測試",
                    reference_time=datetime.now(timezone.utc),
                )
            except Exception as e:
                print(f"    錯誤: {e}")

        # 測試搜索
        print("\n測試搜索功能:")
        queries = ["TypeScript", "React", "錯誤處理"]

        for query in queries:
            print(f"\n  搜索: '{query}'")
            try:
                results = await graphiti.search(query=query, num_results=3)
                print(f"    找到 {len(results)} 個結果" if results else "    無結果")
            except Exception as e:
                print(f"    錯誤: {str(e)[:30]}...")

        print("\n" + "=" * 70)
        print("測試完成！")
        print("=" * 70)

    except Exception as e:
        print(f"\n錯誤: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        if "graphiti" in locals():
            await graphiti.close()
            print("\n連接已關閉")

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
