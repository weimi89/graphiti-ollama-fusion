# Graphiti MCP 使用指南

## 專案結構

```
graphiti/
├── graphiti_mcp_server.py      # 主要 MCP 服務器
├── ollama_embedder.py          # 自定義 Ollama 嵌入器
├── ollama_graphiti_client.py   # 優化的 Ollama 客戶端
├── .env.example                # 環境配置範本
├── README.md                   # 專案說明
├── pyproject.toml              # Python 專案配置
├── docs/                       # 文檔
│   ├── CLAUDE.md               # 開發記錄
│   └── USAGE.md                # 使用指南（本文件）
├── tests/                      # 測試文件
│   ├── test_simple_memory.py   # 基本功能測試
│   ├── test_mcp_complete.py    # 完整功能測試
│   ├── test_embedding.py       # 嵌入功能測試
│   └── ...                     # 其他測試文件
└── tools/                      # 工具腳本
    ├── debug_ollama.py         # Ollama 調試工具
    └── performance_diagnose.py # 性能診斷工具
```

## 快速開始

### 1. 環境設置

```bash
# 複製環境配置
cp .env.example .env

# 編輯環境變數
vim .env
```

### 2. 安裝依賴

```bash
# 使用 UV 安裝依賴
uv sync
```

### 3. 啟動 Ollama 和 Neo4j

```bash
# 啟動 Ollama
ollama serve

# 安裝推薦的模型
ollama pull qwen2.5:7b
ollama pull nomic-embed-text:v1.5

# 啟動 Neo4j (Docker)
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/YOUR_PASSWORD \
  neo4j:latest
```

### 4. 運行 MCP 服務器

```bash
# SSE 模式
uv run python graphiti_mcp_server.py --transport sse --port 8000

# STDIO 模式
uv run python graphiti_mcp_server.py --transport stdio
```

### 5. 基本測試

```bash
# 測試基本功能
uv run python tests/test_simple_memory.py

# 測試嵌入功能
uv run python tests/test_embedding.py
```

## MCP 工具說明

### 1. add_memory_simple
添加記憶到知識圖譜

```python
{
    "name": "記憶名稱",
    "episode_body": "記憶內容",
    "group_id": "分組ID"
}
```

### 2. search_memory_nodes
搜索知識圖譜中的節點

```python
{
    "query": "搜索查詢",
    "group_id": "分組ID",
    "limit": 5
}
```

### 3. search_memory_facts
搜索知識圖譜中的事實關係

```python
{
    "query": "搜索查詢",
    "group_id": "分組ID",
    "limit": 5
}
```

### 4. get_episodes
獲取指定分組的記憶節點

```python
{
    "group_id": "分組ID"
}
```

### 5. test_connection
測試所有連接狀態

### 6. clear_graph
清空整個知識圖譜（謹慎使用）

## 性能優化

### 推薦配置
```bash
# 在 .env 中設置
MODEL_NAME=qwen2.5:7b           # 平衡性能和效果
EMBEDDER_MODEL_NAME=nomic-embed-text:v1.5
LLM_TEMPERATURE=0.1             # 較低溫度提高穩定性
SEMAPHORE_LIMIT=3               # 並發限制
```

### 性能基準
- 簡單記憶添加：3-5秒
- 複雜實體關係：8-15秒
- 搜索操作：1-3秒

## 故障排除

### 常見問題

1. **Connection Error**
   ```bash
   # 檢查 Ollama 狀態
   ollama list

   # 檢查 Neo4j 狀態
   neo4j status
   ```

2. **模型未找到**
   ```bash
   # 安裝必要的模型
   ollama pull qwen2.5:7b
   ollama pull nomic-embed-text:v1.5
   ```

3. **性能問題**
   ```bash
   # 運行性能診斷
   uv run python tools/performance_diagnose.py
   ```

4. **向量相似度錯誤**
   - 已修正：向量歸一化
   - 簡單記憶正常，複雜關係可能仍有問題

### 調試工具

```bash
# Ollama 連接調試
uv run python tools/debug_ollama.py

# 完整性能診斷
uv run python tools/performance_diagnose.py
```

## 開發注意事項

### 程式碼結構
- `graphiti_mcp_server.py`: MCP 服務器主程式
- `ollama_embedder.py`: 嵌入器實現（包含向量歸一化修正）
- `ollama_graphiti_client.py`: LLM 客戶端（包含 Pydantic 驗證修正）

### 關鍵修正
1. ✅ 性能優化：從 70+s 降到 3-15s
2. ✅ 向量歸一化：解決 cosine similarity 錯誤
3. ✅ Pydantic 字段映射：修正實體和關係字段
4. ⚠️ 複雜關係：仍需進一步調查

### 測試策略
- 使用 `tests/test_simple_memory.py` 測試基本功能
- 使用 `tests/test_mcp_complete.py` 測試完整功能
- 定期運行性能測試確保穩定性