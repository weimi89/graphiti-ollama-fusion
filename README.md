# Graphiti MCP Server

本地化知識圖譜記憶服務 — 整合 Ollama 本地 LLM 與 Neo4j 圖資料庫的 MCP 服務器。

基於 [getzep/graphiti](https://github.com/getzep/graphiti) 擴充開發，專為本地 Ollama 環境優化。

## 特色功能

- **智能記憶管理** — 使用知識圖譜儲存和檢索複雜的記憶關係
- **語意搜尋** — 基於向量嵌入的混合搜尋（向量 + 關鍵字）
- **完全本地化** — 使用 Ollama 本地 LLM，無需外部 API
- **Web 管理介面** — 內建儀表板、瀏覽、搜尋、刪除等視覺化管理功能
- **繁體中文** — 完整的中文界面和回應
- **深色/淺色主題** — Web 介面支援主題切換
- **安全模式** — 可選擇跳過實體提取的快速記憶添加

## 系統需求

| 項目 | 需求 |
|------|------|
| Python | 3.10+（推薦 3.11+） |
| Neo4j | 4.0+（`bolt://localhost:7687`） |
| Ollama | 本地運行（`http://localhost:11434`） |
| Node.js | 18+（用於 PM2，可選） |

**必需模型：**

```bash
ollama pull qwen2.5:7b            # LLM
ollama pull nomic-embed-text:v1.5  # 嵌入模型
```

## 快速啟動

### 1. 安裝依賴

```bash
git clone <repo-url>
cd graphiti
uv sync
```

### 2. 配置環境

```bash
cp .env.example .env
# 編輯 .env，設定 Neo4j 密碼等
```

### 3. 啟動服務

```bash
# HTTP 模式（推薦，包含 Web 管理介面）
uv run python graphiti_mcp_server.py --transport http --port 8000

# STDIO 模式（Claude Desktop CLI）
uv run python graphiti_mcp_server.py --transport stdio

# PM2 背景執行
pm2 start ecosystem.config.cjs
```

啟動後：
- **Web 管理介面**：http://localhost:8000/
- **MCP 端點**：http://localhost:8000/mcp/
- **健康檢查**：http://localhost:8000/health
- **REST API**：http://localhost:8000/api/*

## 專案結構

```
graphiti/
├── graphiti_mcp_server.py        # 主入口 — MCP 工具定義
├── src/
│   ├── config.py                 # 配置管理
│   ├── web_api.py                # Web 管理介面 REST API
│   ├── ollama_graphiti_client.py  # Ollama LLM 客戶端適配器
│   ├── ollama_embedder.py        # Ollama 嵌入模型適配器
│   ├── safe_memory_add.py        # 安全記憶添加
│   ├── exceptions.py             # 結構化異常處理
│   └── logging_setup.py          # 日誌系統
├── web/                          # Web 管理介面前端（SPA）
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js
│       ├── components.js
│       └── app.js
├── docs/                         # 文檔
├── tests/                        # 測試
├── tools/                        # 開發診斷工具
├── logs/                         # 日誌
└── ecosystem.config.cjs          # PM2 配置
```

## MCP 客戶端設定

### HTTP 模式（推薦）

適用於 Claude Code、Cline 等支援 Streamable HTTP 的 MCP 客戶端：

```json
{
  "mcpServers": {
    "graphiti-memory": {
      "type": "streamable-http",
      "url": "http://localhost:8000/mcp/"
    }
  }
}
```

### STDIO 模式

適用於 Claude Desktop 等需要直接啟動進程的客戶端：

**配置檔案位置：**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "graphiti-memory": {
      "command": "uv",
      "args": [
        "run", "--directory", "/path/to/graphiti",
        "python", "graphiti_mcp_server.py", "--transport", "stdio"
      ],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "your_password"
      }
    }
  }
}
```

## MCP 工具

### 記憶管理

| 工具 | 說明 |
|------|------|
| `add_memory_simple` | 添加記憶到知識圖譜 |
| `search_memory_nodes` | 搜尋記憶節點（實體） |
| `search_memory_facts` | 搜尋記憶事實（關係） |
| `get_episodes` | 獲取最近的記憶片段 |

### 刪除與查詢

| 工具 | 說明 |
|------|------|
| `delete_episode` | 刪除記憶片段 |
| `delete_entity_edge` | 刪除實體邊（關係） |
| `get_entity_edge` | 獲取實體邊詳細資訊 |

### 系統管理

| 工具 | 說明 |
|------|------|
| `get_status` | 獲取服務狀態 |
| `test_connection` | 測試 Neo4j / LLM / 嵌入器連接 |
| `clear_graph` | 清除圖資料庫 |

## 工具參數

### add_memory_simple

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `name` | string | ✅ | 記憶名稱 |
| `episode_body` | string | ✅ | 記憶內容 |
| `group_id` | string | | 分組 ID（預設: `"default"`） |
| `source` | string | | 來源類型: `text` / `json` / `message` |
| `use_safe_mode` | bool | | 安全模式（預設: `false`，使用完整實體提取） |

### search_memory_nodes

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `query` | string | ✅ | 搜尋關鍵字 |
| `max_nodes` | int | | 最大返回數量（預設: 10） |
| `group_ids` | list | | 分組過濾 |
| `entity_types` | list | | 實體類型過濾 |

### search_memory_facts

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `query` | string | ✅ | 搜尋關鍵字 |
| `max_facts` | int | | 最大返回數量（預設: 10） |
| `group_ids` | list | | 分組過濾 |
| `center_node_uuid` | string | | 中心節點 UUID |

## Web 管理介面

HTTP 模式下訪問 `http://localhost:8000/` 即可使用。

**功能：**
- 儀表板 — 節點數、事實數、記憶片段數統計
- 實體節點 — 瀏覽、篩選、向量搜尋
- 事實關係 — 瀏覽、篩選、向量搜尋
- 記憶片段 — 瀏覽、刪除
- Group 篩選 — 按分組過濾資料
- 主題切換 — 深色/淺色主題

**REST API：**

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/stats` | GET | 儀表板統計 |
| `/api/groups` | GET | 取得所有 group_id |
| `/api/nodes` | GET | 瀏覽實體節點（分頁） |
| `/api/facts` | GET | 瀏覽事實（分頁） |
| `/api/episodes` | GET | 瀏覽記憶片段（分頁） |
| `/api/search/nodes` | GET | 向量搜尋節點 |
| `/api/search/facts` | GET | 向量搜尋事實 |
| `/api/episodes/{uuid}` | DELETE | 刪除記憶片段 |
| `/api/facts/{uuid}` | DELETE | 刪除事實 |
| `/api/groups/{group_id}` | DELETE | 刪除整個 group |

## 配置

### 環境變數（.env）

```bash
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text:v1.5

# 日誌
LOG_FILE=logs/graphiti_mcp_server.log
LOG_LEVEL=INFO
```

### JSON 配置檔案

```json
{
  "ollama": {
    "model": "qwen2.5:7b",
    "base_url": "http://localhost:11434"
  },
  "embedder": {
    "model": "nomic-embed-text:v1.5",
    "dimensions": 768
  },
  "neo4j": {
    "uri": "bolt://localhost:7687",
    "user": "neo4j",
    "password": "your_password"
  }
}
```

## PM2 背景執行

```bash
npm install -g pm2

pm2 start ecosystem.config.cjs     # 啟動
pm2 status                          # 狀態
pm2 logs graphiti-mcp-sse           # 日誌
pm2 restart graphiti-mcp-sse        # 重啟

pm2 save && pm2 startup             # 開機自動啟動
```

## 測試

```bash
uv run python -m pytest tests/                    # 單元測試
uv run python tests/final_comprehensive_test.py    # 集成測試
```

## 故障排除

### Neo4j 連接失敗

```bash
neo4j status                              # 檢查服務
cypher-shell -u neo4j -p your_password    # 確認密碼
```

### Ollama 連接失敗

```bash
ollama serve    # 啟動服務
ollama list     # 檢查模型
```

### MCP 連線錯誤

如果出現 `Invalid request parameters` 或 `Received request before initialization was complete`：

1. 確認使用 HTTP Streamable 傳輸模式（非 SSE）
2. 確認客戶端設定為 `"type": "streamable-http"`, `"url": "http://localhost:8000/mcp/"`
3. 重啟服務：`pm2 restart graphiti-mcp-sse`
4. 在 Claude Code 中執行 `/mcp` 重新連接

### PM2 問題

```bash
pm2 status                                        # 檢查狀態
pm2 logs graphiti-mcp-sse --err --lines 50        # 錯誤日誌
lsof -i :8000                                     # 檢查端口
```

## 文檔

- [使用工具的指令](docs/使用工具的指令.md) — MCP 工具使用指南
- [Graphiti Memory Rules](docs/graphiti-memory-rules.md) — 記憶規則說明

## 授權

MIT License
