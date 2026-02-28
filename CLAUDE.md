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

# 使用自定義配置
uv run python graphiti_mcp_server.py --config your_config.json --transport http

# PM2 背景執行
pm2 start ecosystem.config.cjs
pm2 logs graphiti-mcp-sse
pm2 restart graphiti-mcp-sse
```

## Testing

```bash
# 運行測試
uv run python -m pytest tests/

# 完整集成測試
uv run python tests/final_comprehensive_test.py

# 驗證模組語法
uv run python -c "import src.config; print('OK')"
uv run python -c "import src.ollama_embedder; print('OK')"

# MCP Inspector 測試
npx @modelcontextprotocol/inspector uv run python graphiti_mcp_server.py --transport stdio
```

## Development Tools

```bash
uv run python tools/performance_diagnose.py   # 性能診斷
uv run python tools/inspect_schema.py          # 結構檢查
uv run python tools/final_status_report.py     # 狀態報告
```

## Architecture

```
graphiti_mcp_server.py           # 主入口 — FastMCP 應用，定義所有 MCP 工具
├── src/
│   ├── config.py                # 配置管理（GraphitiConfig）支援 JSON/.env
│   ├── web_api.py               # Web 管理介面 REST API 路由
│   ├── ollama_graphiti_client.py # Ollama LLM 客戶端適配器
│   ├── ollama_embedder.py       # Ollama 嵌入模型適配器
│   ├── safe_memory_add.py       # 安全記憶添加（跳過實體提取）
│   ├── exceptions.py            # 結構化異常處理（12 種異常類別）
│   └── logging_setup.py         # 日誌配置（時間輪轉 + 性能監控）
├── web/                         # Web 管理介面前端（SPA，純 HTML/CSS/JS）
│   ├── index.html               # 主頁面
│   ├── css/style.css            # 主題系統（深色/淺色）與佈局
│   └── js/
│       ├── api.js               # REST API 封裝
│       ├── components.js        # UI 組件渲染
│       └── app.js               # SPA 路由、狀態管理、主題切換
├── tools/                       # 診斷與維護工具
├── tests/                       # 測試套件
├── docs/                        # 文檔
└── ecosystem.config.cjs         # PM2 部署配置
```

### Key Patterns

**MCP 工具定義**：在 `graphiti_mcp_server.py` 中使用 `@mcp.tool()` 裝飾器定義，所有工具都有標準化的錯誤處理模式。

**配置層級**：JSON 配置檔為基礎 + 環境變數覆蓋（支援 Docker 部署場景）。主要配置類為 `GraphitiConfig`，支援 `get_errors()` 返回具體驗證錯誤。

**傳輸模式**：
- `http` — HTTP Streamable（推薦），支援 MCP 端點（`/mcp/`）、Web 管理介面（`/`）、REST API（`/api/*`）、健康檢查（`/health`）
- `stdio` — Claude Desktop CLI 整合
- `sse` — Server-Sent Events（已不建議使用，MCP 1.x 有 session 初始化相容性問題）

**完整模式（預設）**：`add_memory_simple` 預設使用 `use_safe_mode=False`，透過完整的實體提取流程建立 Entity 節點和關係，使記憶可被 `search_memory_nodes` 和 `search_memory_facts` 搜尋。安全模式（`use_safe_mode=True`）僅建立 EpisodicNode，速度快但無法被搜尋。

## MCP Tools (10 tools)

| 類別 | 工具 |
|------|------|
| 記憶管理 | `add_memory_simple`, `search_memory_nodes`, `search_memory_facts`, `get_episodes` |
| 刪除查詢 | `delete_episode`, `delete_entity_edge`, `get_entity_edge` |
| 系統管理 | `get_status`, `test_connection`, `clear_graph` |

## Web 管理介面

HTTP 模式下自動啟用，訪問 `http://localhost:8000/` 即可使用。

**功能**：儀表板統計、實體節點/事實/記憶片段瀏覽與搜尋、group 篩選與刪除、深色/淺色主題、節點/事實/片段刪除操作、資料匯出。

**REST API**：`/api/stats`、`/api/groups`、`/api/nodes`、`/api/facts`、`/api/episodes`、`/api/search/nodes`、`/api/search/facts`、`DELETE /api/nodes/{uuid}`、`DELETE /api/episodes/{uuid}`、`DELETE /api/facts/{uuid}`、`DELETE /api/groups/{group_id}`

**健康檢查**：`/health`（liveness）、`/health/ready`（readiness，實際檢查 Neo4j 連線）

**架構**：`src/web_api.py`（後端 API + CORS 中間件）+ `web/`（前端 SPA，無 build pipeline）。瀏覽用 Cypher 直查、搜尋用 `graphiti.search_()` 向量搜尋。

## Required Services

- **Neo4j**: `bolt://localhost:7687`
- **Ollama**: `http://localhost:11434`
  - LLM: `qwen2.5:7b`（或其他 qwen2.5 變體）
  - Embedder: `nomic-embed-text:v1.5`

## Key Files to Read

- `docs/使用工具的指令.md` — MCP 工具使用指南和最佳實踐
- `docs/graphiti-memory-rules.md` — 記憶規則說明
- `.env.example` — 環境變數範例

## Upstream Reference

本專案基於 [getzep/graphiti/mcp_server](https://github.com/getzep/graphiti/tree/main/mcp_server) 擴充開發。本地新增功能包括：Ollama 深度適配、Web 管理介面、安全模式（Safe Mode）、完整異常/日誌系統。上游使用 graphiti-core 0.28.1，本地目前使用 >=0.24.3。
