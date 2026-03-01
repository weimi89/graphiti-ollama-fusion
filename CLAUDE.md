# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Graphiti MCP Server — 本地化知識圖譜記憶服務，整合 Ollama 本地 LLM 與 Neo4j 圖資料庫的 MCP (Model Context Protocol) 服務器。基於 [getzep/graphiti](https://github.com/getzep/graphiti) 擴充開發，專為本地 Ollama 環境優化。

## Build and Run Commands

```bash
# 安裝依賴
uv sync

# 啟動服務 - HTTP 模式（推薦，支援 Web 管理介面）
uv run python graphiti_mcp_server.py --transport http --port 8000

# 啟動服務 - STDIO 模式（Claude Desktop CLI）
uv run python graphiti_mcp_server.py --transport stdio

# 使用自定義配置（JSON 為基礎，環境變數覆蓋）
uv run python graphiti_mcp_server.py --config your_config.json --transport http

# PM2 背景執行
pm2 start ecosystem.config.cjs
pm2 logs graphiti-mcp-http
pm2 restart graphiti-mcp-http --update-env  # 重啟並重新載入環境變數

# Docker 部署
docker build -t graphiti-mcp .
docker run -p 8000:8000 --env-file .env graphiti-mcp
```

## Testing

```bash
# 運行所有測試（111 個單元測試）
uv run python -m pytest tests/

# 僅執行內容切分測試
uv run python -m pytest tests/test_content_preprocessor.py -v

# 驗證模組語法（快速檢查是否有 import 錯誤）
uv run python -c "import src.config; print('OK')"
uv run python -c "import src.ollama_embedder; print('OK')"
uv run python -c "from src.ollama_graphiti_client import OptimizedOllamaClient; print('OK')"

# MCP Inspector 互動測試
npx @modelcontextprotocol/inspector uv run python graphiti_mcp_server.py --transport stdio
```

> **注意**：`tests/test_integration_manual.py` 中的 3 個 async 測試需要 `pytest-asyncio`，目前會顯示 Failed 但不影響其他測試。

## Development Tools

```bash
uv run python tools/performance_diagnose.py   # 性能診斷
uv run python tools/inspect_schema.py          # Neo4j 結構檢查
uv run python tools/status_report.py           # 統合狀態報告
uv run python tools/validate_config.py         # 配置驗證
uv run python tools/batch_reprocess.py         # 批次重新處理
```

## Architecture

```
graphiti_mcp_server.py           # 主入口 — FastMCP 應用，定義所有 MCP 工具（11 個）
├── src/
│   ├── config.py                # 配置管理（GraphitiConfig）支援 JSON/.env 層疊載入
│   ├── web_api.py               # Web 管理介面 REST API 路由
│   ├── ollama_graphiti_client.py # Ollama LLM 客戶端適配器（支援雙模型分流）
│   ├── ollama_embedder.py       # Ollama 嵌入模型適配器
│   ├── content_preprocessor.py  # 智慧內容切分（長文本自動分段處理）
│   ├── safe_memory_add.py       # 安全記憶添加（跳過實體提取）
│   ├── exceptions.py            # 結構化異常處理（12 種異常類別）
│   └── logging_setup.py         # 日誌配置（時間輪轉 + 性能監控）
├── web/                         # Web 管理介面前端（SPA，純 HTML/CSS/JS，無 build）
│   ├── index.html               # 主頁面
│   ├── css/style.css            # 主題系統（深色/淺色）與佈局
│   └── js/
│       ├── api.js               # REST API 封裝
│       ├── components.js        # UI 組件渲染
│       └── app.js               # SPA 路由、狀態管理、主題切換
├── tools/                       # 診斷與維護工具
│   ├── status_report.py         # 統合狀態報告
│   ├── validate_config.py       # 配置驗證工具
│   ├── batch_reprocess.py       # 批次重新處理
│   ├── inspect_schema.py        # Neo4j 結構檢查
│   └── performance_diagnose.py  # 性能診斷
├── tests/                       # 測試套件（111 個測試）
│   ├── test_content_preprocessor.py # 智慧切分邏輯測試（17 個）
│   ├── test_unit.py             # 單元測試
│   ├── test_web_api.py          # Web API 測試
│   ├── test_web_ui_features.py  # Web UI 功能測試
│   └── test_integration_manual.py # 手動整合測試（需 pytest-asyncio）
├── docs/                        # 文檔
├── Dockerfile                   # Docker 容器化部署
└── ecosystem.config.cjs         # PM2 部署配置
```

### Key Patterns

**MCP 工具定義**：在 `graphiti_mcp_server.py` 中使用 `@mcp.tool()` 裝飾器定義，所有工具都有標準化的錯誤處理模式。

**配置層級**：JSON 配置檔為基礎 + 環境變數覆蓋（支援 Docker 部署場景）。主要配置類為 `GraphitiConfig`，支援 `get_errors()` 返回具體驗證錯誤。重要子配置：`OllamaConfig`（含 `small_model`）、`MemoryPerformanceConfig`（切分閾值、並行度）。

**並發安全**：使用 `asyncio.Lock` 保護 Graphiti 初始化，防止並發競態。`clear_graph` 後自動重建 Neo4j 索引。

**雙模型分流**：`OptimizedOllamaClient` 實作 `_get_model_for_size(model_size)`，graphiti-core pipeline 在簡單任務（去重判斷、摘要生成、時間解析）傳入 `ModelSize.small`，複雜任務（實體提取、邊提取）使用 `ModelSize.medium`。透過 `OLLAMA_SMALL_MODEL` 環境變數配置小模型。

**智慧內容切分**：`src/content_preprocessor.py` 提供 `smart_chunk()` 函數，長文本（>800 字元）自動按段落分割，短段落合併，保持語意完整。`add_memory_simple` 自動整合切分邏輯。

**背景處理模式**：`add_memory_simple(background=True)` 立即返回 `task_id`，後台 `asyncio.Task` 處理。用 `get_memory_task_status(task_id)` 查詢進度。全域 `_memory_tasks` 字典追蹤狀態。

**傳輸模式**：
- `http` — HTTP Streamable（推薦），支援 MCP 端點（`/mcp`）、Web 管理介面（`/`）、REST API（`/api/*`）、健康檢查（`/health`、`/health/ready`）
- `stdio` — Claude Desktop CLI 整合
- `sse` — Server-Sent Events（已不建議使用，MCP 1.x 有 session 初始化相容性問題）

**完整模式（預設）**：`add_memory_simple` 預設使用 `use_safe_mode=False`，透過完整的實體提取流程建立 Entity 節點和關係，使記憶可被 `search_memory_nodes` 和 `search_memory_facts` 搜尋。安全模式（`use_safe_mode=True`）僅建立 EpisodicNode，速度快但無法被搜尋。

## MCP Tools (11 tools)

| 類別 | 工具 | 說明 |
|------|------|------|
| 記憶管理 | `add_memory_simple` | 添加記憶（支援背景處理、智慧切分） |
| 記憶管理 | `search_memory_nodes` | 搜尋記憶節點（實體） |
| 記憶管理 | `search_memory_facts` | 搜尋記憶事實（關係） |
| 記憶管理 | `get_episodes` | 獲取最近的記憶片段 |
| 任務管理 | `get_memory_task_status` | 查詢背景記憶處理任務進度 |
| 刪除查詢 | `delete_episode` | 刪除記憶片段 |
| 刪除查詢 | `delete_entity_edge` | 刪除實體邊（關係） |
| 刪除查詢 | `get_entity_edge` | 獲取實體邊詳細資訊 |
| 系統管理 | `get_status` | 獲取服務狀態 |
| 系統管理 | `test_connection` | 測試 Neo4j / LLM / 嵌入器連接 |
| 系統管理 | `clear_graph` | 清除圖資料庫 |

### add_memory_simple 完整參數

| 參數 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| `name` | str | (必填) | 記憶名稱 |
| `episode_body` | str | (必填) | 記憶內容 |
| `group_id` | str | `"default"` | 分組 ID |
| `source_description` | str | `"MCP Server"` | 來源描述 |
| `source` | str | `"text"` | 來源類型（text/json/message） |
| `episode_uuid` | str | None | 自定義 UUID |
| `use_safe_mode` | bool | `False` | 安全模式（跳過實體提取，快但不可搜尋） |
| `background` | bool | `False` | 背景處理（立即返回 task_id） |
| `excluded_entity_types` | list | None | 排除的實體類型（減少提取量） |

## Web 管理介面

HTTP 模式下自動啟用，訪問 `http://localhost:8000/` 即可使用。

**功能**：儀表板統計、實體節點/事實/記憶片段瀏覽與搜尋、group 篩選與刪除、深色/淺色主題、節點/事實/片段刪除操作、資料匯出、知識圖譜視覺化、AI 問答、品質分析。

**REST API**：

| 端點 | 說明 |
|------|------|
| `GET /api/stats` | 儀表板統計 |
| `GET /api/groups` | 取得所有 group_id |
| `GET /api/nodes` | 瀏覽實體節點（分頁） |
| `GET /api/facts` | 瀏覽事實（分頁） |
| `GET /api/episodes` | 瀏覽記憶片段（分頁） |
| `GET /api/search/nodes` | 向量搜尋節點 |
| `GET /api/search/facts` | 向量搜尋事實 |
| `GET /api/memory/tasks` | 列出背景記憶處理任務 |
| `GET /api/memory/tasks/{id}` | 查詢單一任務狀態 |
| `DELETE /api/nodes/{uuid}` | 刪除節點 |
| `DELETE /api/episodes/{uuid}` | 刪除記憶片段 |
| `DELETE /api/facts/{uuid}` | 刪除事實 |
| `DELETE /api/groups/{group_id}` | 刪除整個 group |

**健康檢查**：`/health`（liveness）、`/health/ready`（readiness，實際檢查 Neo4j 連線）

**架構**：`src/web_api.py`（後端 API + CORS 中間件）+ `web/`（前端 SPA，無 build pipeline）。瀏覽用 Cypher 直查、搜尋用 `graphiti.search_()` 向量搜尋。

## Required Services

- **Neo4j**: `bolt://localhost:7687`（4.0+）
- **Ollama**: `http://localhost:11434`
  - LLM 主模型: `qwen2.5:3b`（推薦，速度與穩定性最佳平衡）
  - LLM 小模型: `qwen2.5:3b`（用於簡單任務，可替換為更快的模型）
  - Embedder: `nomic-embed-text:v1.5`（768 維向量）

> **模型選擇注意**：`qwen2.5:1.5b` 雖然更快但在 graphiti-core 的結構化 JSON 輸出上不穩定（成功率僅 33%）。`qwen2.5:3b` 是能穩定運行的最小可行模型（成功率 100%）。

## Key Environment Variables

| 變數 | 說明 | 預設值 |
|------|------|--------|
| `OLLAMA_MODEL` | 主 LLM 模型 | `qwen2.5:7b` |
| `OLLAMA_SMALL_MODEL` | 小 LLM 模型（簡單任務） | 與主模型相同 |
| `OLLAMA_EMBEDDING_MODEL` | 嵌入模型 | `nomic-embed-text:v1.5` |
| `NEO4J_URI` | Neo4j 連接 URI | `bolt://localhost:7687` |
| `NEO4J_PASSWORD` | Neo4j 密碼 | (必填) |
| `GRAPHITI_CHUNK_THRESHOLD` | 觸發智慧切分的字元數 | `800` |
| `GRAPHITI_MAX_CHUNK_SIZE` | 切分後每段最大字元數 | `600` |
| `GRAPHITI_MAX_COROUTINES` | 最大並行協程數 | `5` |
| `GRAPHITI_DEFAULT_BACKGROUND` | 預設背景處理 | `false` |

完整環境變數列表參見 `.env.example`。

## Key Files to Read

- `docs/使用工具的指令.md` — MCP 工具使用指南和最佳實踐
- `docs/graphiti-memory-rules.md` — 記憶規則說明
- `.env.example` — 環境變數範例（完整列表）

## Upstream Reference

本專案基於 [getzep/graphiti/mcp_server](https://github.com/getzep/graphiti/tree/main/mcp_server) 擴充開發。本地新增功能包括：Ollama 深度適配（含雙模型分流）、Web 管理介面、安全模式（Safe Mode）、智慧內容切分、背景記憶處理、完整異常/日誌系統。上游使用 graphiti-core 最新版，本地依賴 >=0.24.3。
