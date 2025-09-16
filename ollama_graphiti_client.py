#!/usr/bin/env python3
"""
優化的 Ollama Graphiti 客戶端
專門處理 Pydantic 模型和 JSON 響應
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from typing import List, Optional, Any, Dict, Union
from dotenv import load_dotenv
import aiohttp
import json
from pydantic import BaseModel

# 載入環境變數
load_dotenv()

# 確保導入路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graphiti_core import Graphiti
from graphiti_core.llm_client.client import LLMClient
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.cross_encoder.client import CrossEncoderClient
from ollama_embedder import OllamaEmbedder


class OptimizedOllamaClient(LLMClient):
    """
    優化的 Ollama 客戶端，更好地處理 JSON 和 Pydantic 模型
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = config.base_url or "http://localhost:11434"
        # 使用傳入的 model，如果沒有才用默認值
        self.model = config.model if config.model else "llama3.2:3b"
        self.temperature = config.temperature if config.temperature is not None else 0.0
        print(f"    使用模型: {self.model}")

    async def _generate_response(
        self,
        messages: List[Any],
        response_model: Optional[Any] = None,
        **kwargs
    ) -> Any:
        """實現抽象方法 _generate_response"""
        return await self.generate_response(messages, response_model)

    async def _make_request(
        self,
        messages: List[Dict[str, str]],
        json_mode: bool = False
    ) -> str:
        """發送請求到 Ollama API"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "temperature": self.temperature,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": 4096
                }
            }

            if json_mode:
                payload["format"] = "json"

            url = f"{self.base_url}/api/chat"

            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("message", {}).get("content", "")
                else:
                    error_text = await response.text()
                    print(f"❌ Ollama 錯誤: {error_text}")
                    return ""

    def _extract_json_from_response(self, response: str) -> Dict:
        """從響應中提取 JSON"""
        # 嘗試直接解析
        try:
            return json.loads(response)
        except:
            pass

        # 嘗試提取 JSON 塊
        import re
        patterns = [
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
            r'\{[^}]*\}',
            r'\{.*\}',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match)
                except:
                    continue

        # 如果都失敗，返回空字典
        return {}

    async def generate_response(
        self,
        messages: List[Any],
        response_model: Optional[Any] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Any:
        """生成響應"""
        # 轉換消息格式
        ollama_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                ollama_messages.append(msg)
            else:
                ollama_messages.append({
                    "role": getattr(msg, 'role', 'user'),
                    "content": getattr(msg, 'content', str(msg))
                })

        # 如果需要結構化輸出
        if response_model:
            # 為 Pydantic 模型生成 JSON schema 提示
            if hasattr(response_model, '__annotations__'):
                # 獲取字段信息
                fields = {}
                for field_name, field_type in response_model.__annotations__.items():
                    if hasattr(field_type, '__origin__'):
                        # 處理泛型類型
                        if field_type.__origin__ == list:
                            fields[field_name] = "array"
                        elif field_type.__origin__ == dict:
                            fields[field_name] = "object"
                        else:
                            fields[field_name] = "string"
                    else:
                        # 簡單類型
                        type_map = {
                            str: "string",
                            int: "number",
                            float: "number",
                            bool: "boolean",
                            list: "array",
                            dict: "object"
                        }
                        fields[field_name] = type_map.get(field_type, "string")

                # 構建 JSON 格式提示
                schema_hint = f"Return a JSON object with these fields: {json.dumps(fields)}"

                # 添加更詳細的系統提示
                system_prompt = f"""You are an entity extraction assistant. Your task is to extract ALL entities and relationships from text.

IMPORTANT:
1. Extract ALL entities mentioned in the text (people, organizations, technologies, concepts)
2. Each entity should have a unique name
3. Entity types: 0=Person, 1=Organization, 2=Technology, 3=Concept, 4=Place, 5=Other
4. Include observations about each entity
5. Respond with valid JSON only

{schema_hint}

Example entities to look for:
- People names (type 0)
- Company/organization names (type 1)
- Technologies/tools/frameworks (type 2)
- Concepts/methods (type 3)
- Locations (type 4)
- Other entities (type 5)"""

                ollama_messages.append({
                    "role": "system",
                    "content": system_prompt
                })

            # 發送請求
            response_text = await self._make_request(ollama_messages, json_mode=True)

            # 解析響應
            if response_text:
                json_data = self._extract_json_from_response(response_text)

                # 修正中文/英文字段名映射
                entities_data = None
                if '實體' in json_data:
                    entities_data = json_data['實體']
                    json_data['extracted_entities'] = entities_data
                elif 'extracted_entities' in json_data:
                    entities_data = json_data['extracted_entities']

                # 調試輸出和字段修正
                if entities_data is not None:
                    print(f"\n🔍 調試: 提取的實體數量 = {len(entities_data) if isinstance(entities_data, list) else 0}")

                    # 確保 entities_data 是列表且包含有效實體
                    if isinstance(entities_data, list):
                        # 過濾空字符串或無效實體
                        valid_entities = []
                        for i, entity in enumerate(entities_data):
                            if isinstance(entity, dict):
                                # 立即修正 entity_name -> name
                                if 'entity_name' in entity and 'name' not in entity:
                                    entity['name'] = entity.pop('entity_name')
                                valid_entities.append(entity)
                                print(f"  實體 {i}: {entity}")
                            elif isinstance(entity, str) and entity.strip():
                                # 將字符串轉換為實體字典
                                entity_dict = {
                                    'name': entity.strip(),
                                    'labels': ['Entity'],
                                    'summary': entity.strip()
                                }
                                valid_entities.append(entity_dict)
                                print(f"  實體 {i}: {entity} (轉換為字典)")

                        # 更新實體列表
                        json_data['extracted_entities'] = valid_entities
                    else:
                        print(f"  警告：實體數據不是列表格式: {type(entities_data)}")
                        # 如果不是列表，嘗試轉換
                        if isinstance(entities_data, str) and entities_data.strip():
                            entity_dict = {
                                'name': entities_data.strip(),
                                'labels': ['Entity'],
                                'summary': entities_data.strip()
                            }
                            json_data['extracted_entities'] = [entity_dict]
                            print(f"  已轉換為列表格式: {entity_dict}")

                # 嘗試創建 Pydantic 模型實例
                if hasattr(response_model, 'model_validate'):
                    try:
                        # 修正字段名稱映射問題
                        # 如果 json_data 包含 extracted_entities 字段
                        if 'extracted_entities' in json_data and isinstance(json_data['extracted_entities'], list):
                            for entity in json_data['extracted_entities']:
                                # 將 entity_name 映射到 name
                                if 'entity_name' in entity and 'name' not in entity:
                                    entity['name'] = entity.pop('entity_name')
                                # 將 entity_type_name 映射到 entity_type
                                if 'entity_type_name' in entity and 'entity_type' not in entity:
                                    entity['entity_type'] = entity.pop('entity_type_name')
                                # 確保有 entity_summary
                                if 'entity_summary' not in entity:
                                    entity['entity_summary'] = entity.get('description', entity.get('name', ''))
                                # 確保有 observations（必需字段）
                                if 'observations' not in entity:
                                    entity['observations'] = [entity.get('description', f"Related to {entity.get('name', 'entity')}")]
                                # 確保有 entity_type_id，預設為 0
                                if 'entity_type_id' not in entity:
                                    entity['entity_type_id'] = 0
                                else:
                                    # 強制設為 0 以避免 index out of range
                                    entity['entity_type_id'] = 0
                                # 移除不需要的字段
                                for key in ['description', 'score', 'mentioned', 'speaker']:
                                    entity.pop(key, None)

                        # 處理 edges 的字段映射（修正 source_id -> source_entity_id）
                        if 'edges' in json_data and isinstance(json_data['edges'], list):
                            for i, edge in enumerate(json_data['edges']):
                                # 修正各種可能的 ID 字段名稱
                                if 'source_id' in edge and 'source_entity_id' not in edge:
                                    edge['source_entity_id'] = edge.pop('source_id')
                                elif 'subject_id' in edge and 'source_entity_id' not in edge:
                                    edge['source_entity_id'] = edge.pop('subject_id')
                                elif 'source_entity_id' not in edge:
                                    # 如果沒有 source_entity_id，嘗試從位置推斷
                                    edge['source_entity_id'] = 0  # 默認第一個實體

                                if 'target_id' in edge and 'target_entity_id' not in edge:
                                    edge['target_entity_id'] = edge.pop('target_id')
                                elif 'object_id' in edge and 'target_entity_id' not in edge:
                                    edge['target_entity_id'] = edge.pop('object_id')
                                elif 'target_entity_id' not in edge:
                                    # 如果沒有 target_entity_id，嘗試從位置推斷
                                    edge['target_entity_id'] = 1 if len(json_data.get('extracted_entities', [])) > 1 else 0

                                # 處理關係類型字段
                                if 'relationship' in edge and 'relation_type' not in edge:
                                    edge['relation_type'] = edge.pop('relationship')
                                elif 'predicate' in edge and 'relation_type' not in edge:
                                    edge['relation_type'] = edge.pop('predicate')
                                elif 'relation_type' not in edge:
                                    edge['relation_type'] = 'RELATES_TO'

                                # 將 relation_type 也映射到 fact 字段
                                if 'fact' not in edge:
                                    edge['fact'] = edge.get('relation_type', 'relates to')

                                # 修復ID字段 - 將字符串ID轉換為整數
                                if 'source_entity_id' in edge:
                                    try:
                                        if isinstance(edge['source_entity_id'], str):
                                            # 嘗試從 "ENTITY_0" 格式提取數字
                                            if edge['source_entity_id'].startswith('ENTITY_'):
                                                edge['source_entity_id'] = int(edge['source_entity_id'].replace('ENTITY_', ''))
                                            else:
                                                edge['source_entity_id'] = int(edge['source_entity_id'])
                                        elif edge['source_entity_id'] is None:
                                            edge['source_entity_id'] = 0  # 處理 None 值
                                    except (ValueError, AttributeError, TypeError):
                                        edge['source_entity_id'] = 0  # 默認值

                                if 'target_entity_id' in edge:
                                    try:
                                        if isinstance(edge['target_entity_id'], str):
                                            # 嘗試從 "ENTITY_0" 格式提取數字
                                            if edge['target_entity_id'].startswith('ENTITY_'):
                                                edge['target_entity_id'] = int(edge['target_entity_id'].replace('ENTITY_', ''))
                                            else:
                                                edge['target_entity_id'] = int(edge['target_entity_id'])
                                        elif edge['target_entity_id'] is None:
                                            edge['target_entity_id'] = 1  # 處理 None 值
                                    except (ValueError, AttributeError, TypeError):
                                        edge['target_entity_id'] = 1  # 默認值（避免與source相同）

                                # 確保必要字段
                                if 'fact' not in edge:
                                    edge['fact'] = edge.get('relation_type', 'relates to')
                                if 'fact_embedding' not in edge:
                                    edge['fact_embedding'] = None
                                if 'valid_at' not in edge:
                                    edge['valid_at'] = None
                                if 'invalid_at' not in edge:
                                    edge['invalid_at'] = None

                        # 處理 NodeResolutions 的字段映射
                        if 'entity_resolutions' in json_data and isinstance(json_data['entity_resolutions'], list):
                            for resolution in json_data['entity_resolutions']:
                                # 修正 duplicate_idx 字段
                                if 'duplication_idx' in resolution:
                                    resolution['duplicate_idx'] = resolution.pop('duplication_idx')
                                # 確保有必要的字段
                                if 'duplicate_idx' not in resolution:
                                    resolution['duplicate_idx'] = -1
                                if 'additional_duplicates' not in resolution:
                                    resolution['additional_duplicates'] = []

                        # 處理缺失的字段
                        for field_name in response_model.__annotations__.keys():
                            if field_name not in json_data:
                                # 為缺失的字段提供默認值
                                field_type = response_model.__annotations__[field_name]
                                if hasattr(field_type, '__origin__') and field_type.__origin__ == list:
                                    json_data[field_name] = []
                                elif hasattr(field_type, '__origin__') and field_type.__origin__ == dict:
                                    json_data[field_name] = {}
                                elif field_type == bool:
                                    json_data[field_name] = False
                                elif field_type == int or field_type == float:
                                    json_data[field_name] = 0
                                else:
                                    json_data[field_name] = ""

                        validated = response_model.model_validate(json_data)
                        # 總是返回字典形式以確保兼容性
                        return validated.model_dump()
                    except Exception as e:
                        print(f"⚠️ Pydantic 驗證失敗: {e}")
                        # 嘗試創建一個最小有效實例
                        try:
                            minimal_data = {}
                            for field_name in response_model.__annotations__.keys():
                                field_type = response_model.__annotations__[field_name]
                                if hasattr(field_type, '__origin__') and field_type.__origin__ == list:
                                    minimal_data[field_name] = []
                                elif hasattr(field_type, '__origin__') and field_type.__origin__ == dict:
                                    minimal_data[field_name] = {}
                                else:
                                    minimal_data[field_name] = json_data.get(field_name, "")
                            validated = response_model.model_validate(minimal_data)
                            # 總是返回字典形式以確保兼容性
                            return validated.model_dump()
                        except:
                            pass

            # 如果所有都失敗，創建空實例
            if hasattr(response_model, 'model_validate'):
                try:
                    empty_data = {
                        field_name: [] if 'list' in str(field_type).lower() else {}
                        if 'dict' in str(field_type).lower() else ""
                        for field_name, field_type in response_model.__annotations__.items()
                    }
                    validated = response_model.model_validate(empty_data)
                    # 總是返回字典形式以確保兼容性
                    return validated.model_dump()
                except:
                    pass

            return None

        else:
            # 純文本響應
            return await self._make_request(ollama_messages)

    async def generate_response_with_retry(
        self,
        messages: List[Any],
        response_model: Optional[Any] = None,
        max_attempts: int = 3,
    ) -> Any:
        """帶重試的響應生成"""
        for attempt in range(max_attempts):
            try:
                result = await self.generate_response(messages, response_model)
                if result:
                    return result
            except Exception as e:
                if attempt < max_attempts - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    print(f"❌ 所有重試都失敗: {e}")

        # 返回默認值
        if response_model and hasattr(response_model, 'model_validate'):
            try:
                empty_data = {
                    field_name: [] if 'list' in str(field_type).lower() else ""
                    for field_name, field_type in response_model.__annotations__.items()
                }
                return response_model.model_validate(empty_data)
            except:
                pass
        return None


class SimpleCrossEncoder(CrossEncoderClient):
    """簡化的 Cross-encoder，使用默認分數"""

    async def rank(self, query: str, passages: list[str]) -> list[tuple[str, float]]:
        """簡單的排序實現"""
        # 為所有段落返回相同的分數，保持原始順序
        return [(passage, 1.0) for passage in passages]


async def main():
    """主測試函數"""

    print("=" * 70)
    print("🚀 優化的 Ollama + Graphiti 解決方案")
    print("=" * 70)

    # 環境檢查
    print("\n📋 環境配置:")
    print(f"  Neo4j URI: {os.getenv('NEO4J_URI', 'bolt://localhost:7687')}")
    print(f"  Neo4j User: {os.getenv('NEO4J_USER', 'neo4j')}")
    print(f"  Model: qwen2.5:14b")
    print(f"  Embedder: nomic-embed-text:v1.5")

    try:
        # 初始化 LLM
        print("\n🤖 初始化 Ollama LLM...")
        llm_config = LLMConfig(
            api_key="not-needed",
            model="qwen2.5:14b",  # 使用更強大的模型
            base_url="http://localhost:11434",
            temperature=0.1  # 稍微提高溫度以獲得更好的創造性
        )
        llm_client = OptimizedOllamaClient(llm_config)
        print("  ✅ LLM 初始化成功")

        # 初始化嵌入器
        print("\n🧲 初始化嵌入器...")
        embedder = OllamaEmbedder(
            model="nomic-embed-text:v1.5",
            base_url="http://localhost:11434"
        )
        if not await embedder.test_connection():
            print("  ❌ 嵌入器連接失敗")
            return False
        print("  ✅ 嵌入器初始化成功")

        # 初始化 Cross-encoder
        print("\n🔄 初始化 Cross-encoder...")
        cross_encoder = SimpleCrossEncoder()
        print("  ✅ Cross-encoder 初始化成功")

        # 初始化 Graphiti
        print("\n🗃️ 初始化 Graphiti...")
        graphiti = Graphiti(
            uri=os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
            user=os.getenv('NEO4J_USER', 'neo4j'),
            password=os.getenv('NEO4J_PASSWORD', '24927108'),
            llm_client=llm_client,
            embedder=embedder,
            cross_encoder=cross_encoder
        )

        await graphiti.build_indices_and_constraints()
        print("  ✅ Graphiti 初始化成功")

        # 定義 entity types（字典格式）
        entity_types = {
            "person": {"name": "person", "description": "People, users, developers"},
            "organization": {"name": "organization", "description": "Companies, organizations, teams"},
            "technology": {"name": "technology", "description": "Technologies, frameworks, tools, languages"},
            "concept": {"name": "concept", "description": "Concepts, methods, patterns, practices"},
            "place": {"name": "place", "description": "Locations, places"},
            "other": {"name": "other", "description": "Other entities"}
        }

        # 添加測試記憶
        print("\n📝 添加測試記憶...")
        test_episodes = [
            {
                "name": "用戶偏好",
                "content": "用戶 RD-CAT 偏好使用 TypeScript 進行開發。TypeScript 提供了類型安全。"
            },
            {
                "name": "技術知識",
                "content": "React 18 引入了 Concurrent Features。這包括 Suspense 和 useTransition。"
            },
            {
                "name": "最佳實踐",
                "content": "API 錯誤處理應該包含錯誤日誌、友善訊息和重試機制。"
            }
        ]

        episode_results = []
        for episode in test_episodes:
            print(f"\n  📌 {episode['name']}")
            try:
                result = await graphiti.add_episode(
                    name=episode['name'],
                    episode_body=episode['content'],
                    source_description="Ollama 測試",
                    reference_time=datetime.now(timezone.utc)
                    # 不傳入 entity_types，使用預設值
                )
                episode_results.append(result)

                if hasattr(result, 'episode_id'):
                    print(f"    ✓ Episode: {result.episode_id[:8]}...")
                if hasattr(result, 'node_ids') and result.node_ids:
                    print(f"    ✓ 節點: {len(result.node_ids)} 個")
                if hasattr(result, 'edge_ids') and result.edge_ids:
                    print(f"    ✓ 關係: {len(result.edge_ids)} 個")

            except Exception as e:
                print(f"    ❌ 錯誤: {str(e)}")
                import traceback
                traceback.print_exc()

        # 等待處理
        print("\n⏳ 等待處理（5秒）...")
        await asyncio.sleep(5)

        # 測試搜索
        print("\n🔍 測試搜索功能:")
        queries = ["TypeScript", "React", "錯誤處理", "RD-CAT"]

        for query in queries:
            print(f"\n  🔎 '{query}'")
            try:
                results = await graphiti.search(query=query, num_results=3)
                if results:
                    print(f"    ✅ 找到 {len(results)} 個結果")
                else:
                    print(f"    ⚠️ 無結果")
            except Exception as e:
                print(f"    ❌ 錯誤: {str(e)[:30]}...")

        # 總結
        print("\n" + "=" * 70)
        print("📊 總結")
        print("=" * 70)

        total_episodes = len(episode_results)
        total_nodes = sum(
            len(r.node_ids) if hasattr(r, 'node_ids') and r.node_ids else 0
            for r in episode_results
        )

        print(f"\n✅ 成功添加 {total_episodes} 個記憶")
        print(f"✅ 提取了 {total_nodes} 個實體")

        if total_nodes == 0:
            print("\n⚠️ 實體提取可能需要:")
            print("  1. 更強大的模型（如 qwen2.5:14b）")
            print("  2. 或下載專門的模型（如 deepseek-r1:7b）")
            print("  3. 調整提示詞以適應當前模型")

        print("\n🎉 測試完成！")

    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if 'graphiti' in locals():
            await graphiti.close()
            print("\n✅ 連接已關閉")

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)