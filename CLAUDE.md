# CLAUDE.md

本文件為 Claude Code (claude.ai/code) 在此代碼庫中工作時提供指導。

## 專案概述

這是一個 **Graphiti MCP Server with Ollama Integration** - 一個模型上下文協議（MCP）服務器，通過 Neo4j 支援的知識圖譜和本地 Ollama LLM 提供持久記憶功能。該系統使 AI 代理能夠通過儲存和查詢實體、關係和記憶段來維持跨會話的長期記憶。

## 架構

### 核心組件

- **`graphiti_mcp_server.py`**: 主要 MCP 服務器，實現 FastMCP 和 6 個記憶操作工具
- **`ollama_graphiti_client.py`**: 為 Ollama 優化的自定義 LLM 客戶端，具備 Pydantic 模型處理和 JSON 響應處理
- **`ollama_embedder.py`**: 為 Ollama 嵌入模型（nomic-embed-text）的自定義嵌入器實現

### 技術堆疊

- **知識圖譜**: Neo4j (bolt://localhost:7687) 用於持久儲存
- **LLM**: Ollama 配合 qwen2.5:14b 模型進行實體提取和關係映射
- **嵌入**: nomic-embed-text:v1.5 用於語義搜索
- **MCP 協議**: FastMCP 向 AI 客戶端公開工具
- **傳輸**: 支援 STDIO 和 SSE（Server-Sent Events）兩種模式

### 資料模型

- **記憶段（Episodes）**: 帶有元資料的文字記憶（名稱、內容、group_id、時間戳）
- **實體（Entities）**: 從記憶段中提取，包含名稱、摘要和關係
- **關係（Relationships）**: 用描述性文字連接實體的事實
- **群組（Groups）**: 使用 group_id 進行多租戶場景的邏輯分割

## 常用開發指令

### 環境設置
```bash
# 安裝依賴
uv sync

# 複製環境範本
cp .env.example .env
# 編輯 .env 配置 Neo4j 憑證和模型設定
```

### 啟動服務器
```bash
# STDIO 模式（用於 Claude Desktop）
uv run graphiti_mcp_server.py --transport stdio

# SSE 模式（用於 Cursor、網頁客戶端）
uv run graphiti_mcp_server.py --transport sse --host 0.0.0.0 --port 8000

# 使用自定義參數
uv run graphiti_mcp_server.py --transport sse --group-id my_namespace
```

### 開發與測試
```bash
# 直接用 Python 執行以進行偵錯
python graphiti_mcp_server.py --transport sse

# 測試 Neo4j 連接
python -c "from graphiti_mcp_server import initialize_graphiti; import asyncio; asyncio.run(initialize_graphiti())"

# 檢查 Ollama 模型
ollama list
ollama pull qwen2.5:14b
ollama pull nomic-embed-text:v1.5
```

## 可用的 MCP 工具

1. **`add_memory_simple`**: 向知識圖譜添加記憶段/記憶
2. **`search_memory_nodes`**: 按名稱/摘要搜索實體，支援群組篩選
3. **`search_memory_facts`**: 搜索實體間的關係事實
4. **`get_episodes`**: 按群組檢索最近的記憶段
5. **`clear_graph`**: 重置整個知識圖譜
6. **`test_connection`**: 驗證 Neo4j 和 Ollama 連接

## 配置

### 必需的環境變數
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`: Neo4j 資料庫連接
- `MODEL_NAME`: 用於實體提取的 Ollama 模型（預設: qwen2.5:14b）
- `EMBEDDER_MODEL_NAME`: 嵌入模型（預設: nomic-embed-text:v1.5）
- `OLLAMA_BASE_URL`: Ollama 服務器 URL（預設: http://localhost:11434）

### `.env` 中的關鍵設定
- `GROUP_ID`: 記憶的預設命名空間
- `SEMAPHORE_LIMIT`: 並發控制（本地 LLM 建議為 3）
- `LLM_TEMPERATURE`: 響應隨機性（0.1 以保持一致性）
- `GRAPHITI_TELEMETRY_ENABLED`: false（隱私保護）

## 關鍵實現要點

### Neo4j 查詢模式
服務器使用直接 Cypher 查詢而非 Graphiti 的搜索 API 以獲得更好的控制：
```python
# 始終使用關鍵字參數，而非字典參數
results = await graphiti.driver.execute_query(
    query_text,
    query=args.query,
    group_ids=group_filter,
    limit=args.max_nodes
)
```

### Pydantic 模型處理
`ollama_graphiti_client.py` 包含針對實體 ID 解析的大量錯誤處理：
- 將類似 "ENTITY_0" 的字串 ID 轉換為整數
- 處理來自本地 LLM 的格式錯誤的 JSON 響應
- 為缺失的必需欄位提供後備方案

### Ollama API 差異
使用 `/api/embed` 端點（而非 `/api/embeddings`）和 `input` 參數（而非 `prompt`）：
```python
payload = {"model": self.model, "input": text}
embedding = result.get("embeddings", [])[0]
```

## 故障排除

### 常見問題
- **連接失敗**: 驗證 Neo4j 和 Ollama 是否正在運行
- **搜索結果為空**: 檢查節點標籤（Entity vs Episodic）
- **Pydantic 驗證錯誤**: 更新 ollama_graphiti_client.py 中的實體 ID 解析
- **嵌入失敗**: 確保在 Ollama 中已拉取 nomic-embed-text 模型

### 除錯指令
```bash
# 檢查 Neo4j 連接
cypher-shell -u neo4j -p [password] "MATCH (n) RETURN count(n)"

# 驗證 Ollama 模型
curl http://localhost:11434/api/tags

# 測試嵌入端點
curl -X POST http://localhost:11434/api/embed -d '{"model":"nomic-embed-text:v1.5","input":"test"}'
```