# Graphiti MCP Server

本地化知識圖譜記憶服務 - 整合 Ollama 本地 LLM 與 Graphiti 的 MCP 服務器

## 特色功能

- **智能記憶管理** - 使用知識圖譜儲存和檢索複雜的記憶關係
- **語意搜尋** - 基於向量嵌入的智能搜尋
- **完全本地化** - 使用 Ollama 本地 LLM，無需外部 API
- **繁體中文** - 完整的中文界面和回應
- **多傳輸模式** - 支援 STDIO、SSE、HTTP Streamable
- **健康檢查** - 內建 `/health` 端點

## 專案結構

```
graphiti/
├── src/                          # 核心模組
│   ├── config.py                 # 配置管理
│   ├── exceptions.py             # 異常處理
│   ├── logging_setup.py          # 日誌系統
│   ├── ollama_embedder.py        # Ollama 嵌入器
│   ├── ollama_graphiti_client.py # Ollama LLM 客戶端
│   └── safe_memory_add.py        # 安全記憶添加
├── docs/                         # 文檔
│   ├── 使用工具的指令.md          # 工具使用指南
│   └── graphiti-memory-rules.md  # 記憶規則說明
├── tests/                        # 測試
├── tools/                        # 開發工具
├── logs/                         # 日誌
├── ecosystem.config.cjs          # PM2 配置
└── graphiti_mcp_server.py        # 主服務器
```

## 系統需求

| 項目 | 需求 |
|------|------|
| Python | 3.10+（推薦 3.11+） |
| Neo4j | 4.0+（bolt://localhost:7687） |
| Ollama | 本地運行（http://localhost:11434） |
| Node.js | 18+（用於 pm2） |

**必需模型：**
```bash
ollama pull qwen2.5:7b            # LLM
ollama pull nomic-embed-text:v1.5 # 嵌入
```

## 快速啟動

### 1. 安裝依賴

```bash
# 克隆專案
git clone https://github.com/weimi89/graphiti-ollama-fusion.git
cd graphiti-mcp-server

# 安裝依賴
uv sync
```

### 2. 配置環境

```bash
cp .env.example .env
nano .env  # 設定 Neo4j 密碼等
```

### 3. 啟動服務

```bash
# HTTP 模式（推薦）
uv run python graphiti_mcp_server.py --transport http --port 8000

# STDIO 模式（Claude Desktop CLI）
uv run python graphiti_mcp_server.py --transport stdio

# SSE 模式
uv run python graphiti_mcp_server.py --transport sse --port 8000

# PM2 背景執行
pm2 start ecosystem.config.cjs
```

## MCP 客戶端設定

### 傳輸模式比較

| 模式 | 適用場景 | 說明 |
|------|----------|------|
| **HTTP** | 推薦 | 官方推薦，支援健康檢查 |
| **STDIO** | Claude Desktop CLI | 直接整合 |
| **SSE** | 網頁應用 | 遠端客戶端 |

### HTTP 模式設定（推薦）

```json
{
  "mcpServers": {
    "graphiti-memory": {
      "url": "http://localhost:8000/mcp/"
    }
  }
}
```

### STDIO 模式設定

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

### SSE 模式設定

```json
{
  "mcpServers": {
    "graphiti-memory": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```

## MCP 工具

### 記憶管理

| 工具 | 說明 |
|------|------|
| `add_memory_simple` | 添加記憶片段 |
| `search_memory_nodes` | 搜尋記憶節點 |
| `search_memory_facts` | 搜尋記憶事實 |
| `get_episodes` | 獲取記憶片段 |

### 刪除與查詢

| 工具 | 說明 |
|------|------|
| `delete_episode` | 刪除記憶片段 |
| `delete_entity_edge` | 刪除實體邊 |
| `get_entity_edge` | 獲取實體邊詳細資訊 |

### 系統管理

| 工具 | 說明 |
|------|------|
| `get_status` | 獲取服務狀態 |
| `test_connection` | 測試連接 |
| `clear_graph` | 清除圖資料庫 |

## 工具參數

### add_memory_simple

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `name` | string | ✅ | 記憶名稱 |
| `episode_body` | string | ✅ | 記憶內容 |
| `group_id` | string | | 分組 ID（預設: "default"） |
| `source` | string | | 來源類型: text/json/message |
| `use_safe_mode` | bool | | 安全模式（預設: true） |

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
# 安裝
npm install -g pm2

# 啟動
pm2 start ecosystem.config.cjs

# 管理
pm2 status
pm2 logs graphiti-mcp-sse
pm2 restart graphiti-mcp-sse
pm2 stop graphiti-mcp-sse

# 開機自動啟動
pm2 save
pm2 startup
```

## 測試

```bash
# 運行測試
uv run python -m pytest tests/

# 集成測試
uv run python tests/final_comprehensive_test.py
```

## 開發工具

```bash
# 性能診斷
uv run python tools/performance_diagnose.py

# 結構檢查
uv run python tools/inspect_schema.py

# 狀態報告
uv run python tools/final_status_report.py
```

## 故障排除

### Neo4j 連接失敗

```bash
# 檢查服務
neo4j status

# 確認密碼正確
cypher-shell -u neo4j -p your_password
```

### Ollama 連接失敗

```bash
# 啟動服務
ollama serve

# 檢查模型
ollama list
```

### PM2 問題

```bash
# 檢查狀態
pm2 status

# 查看錯誤日誌
pm2 logs graphiti-mcp-sse --err --lines 50

# 檢查端口
lsof -i :8000
```

## 文檔

- [使用工具的指令](docs/使用工具的指令.md) - MCP 工具使用指南
- [Graphiti Memory Rules](docs/graphiti-memory-rules.md) - 記憶規則說明

## 授權

MIT License
