# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Graphiti MCP Server — 知識圖譜記憶服務，整合多 LLM 提供者（Ollama / GLM / GROQ / OpenRouter / DeepSeek）與 Neo4j 圖資料庫的 MCP (Model Context Protocol) 服務器。基於 [getzep/graphiti](https://github.com/getzep/graphiti) 擴充開發，支援本地 Ollama 和雲端 LLM 彈性切換，並可獨立指定 Embedding 提供者（與 LLM 解耦）。

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
# 運行所有測試（203 個測試）
uv run python -m pytest tests/

# 僅執行內容切分測試
uv run python -m pytest tests/test_content_preprocessor.py -v

# 驗證模組語法（快速檢查是否有 import 錯誤）
uv run python -c "import src.config; print('OK')"
uv run python -c "import src.ollama_embedder; print('OK')"
uv run python -c "from src.ollama_graphiti_client import OptimizedOllamaClient; print('OK')"
uv run python -c "from src.glm_client import GlmClient; print('OK')"
uv run python -c "from src.openrouter_client import OpenRouterClient; print('OK')"
uv run python -c "from src.deepseek_client import DeepSeekClient; print('OK')"

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
uv run python tools/migrate_embeddings.py      # Embedding 模型遷移
```

## Architecture

```
graphiti_mcp_server.py           # 主入口 — FastMCP 應用，定義所有 MCP 工具（19 個）
├── src/
│   ├── config.py                # 配置管理（GraphitiConfig）支援 JSON/.env 層疊載入
│   ├── web_api.py               # Web 管理介面 REST API 路由（30+ 端點）
│   ├── ollama_graphiti_client.py # Ollama LLM 客戶端適配器（支援雙模型分流）
│   ├── openai_compat_client.py  # OpenAI 相容 LLM 客戶端基類（json_object 模式 + 簡化 schema 注入 + json 保底防護，GLM/OpenRouter/DeepSeek 共用）
│   ├── glm_client.py            # GLM（智谱 AI）LLM 客戶端（繼承 OpenAICompatClient）
│   ├── openrouter_client.py     # OpenRouter LLM 客戶端（繼承 OpenAICompatClient，聚合多家模型）
│   ├── deepseek_client.py       # DeepSeek LLM 客戶端（繼承 OpenAICompatClient）
│   ├── ollama_embedder.py       # Ollama 嵌入模型適配器（支援 bge-m3，並發 batch）
│   ├── content_preprocessor.py  # 智慧內容切分（長文本自動分段處理）
│   ├── deduplication.py         # 記憶去重（餘弦相似度比對）
│   ├── importance.py            # 重要性追蹤與智慧遺忘
│   ├── safe_memory_add.py       # 安全記憶添加（跳過實體提取）
│   ├── task_store.py            # 背景任務 SQLite 持久化（TaskStore，in-memory dict + SQLite，啟動還原未完成任務）
│   ├── timezone_utils.py        # 時區轉換工具（UTC→本地時區顯示轉換）
│   ├── i18n.py                  # 後端多國語系（REST 依 Accept-Language、MCP 依 SERVER_LANG；33 語言，zh-TW/en/zh-CN/ja 手寫基準 + 其餘 generated）
│   ├── i18n_generated.py        # 自動生成的 29 種語言訊息覆蓋（GENERATED_MESSAGE_OVERRIDES，以 en 為底套用）
│   ├── exceptions.py            # 結構化異常處理（12 種異常類別）
│   └── logging_setup.py         # 日誌配置（時間輪轉 + 性能監控）
├── web/                         # Web 管理介面前端（SPA，純 HTML/CSS/JS，無 build）
│   ├── index.html               # 主頁面（含社群導航、三元組表單）
│   ├── css/style.css            # 主題系統（深色/淺色）與佈局
│   └── js/
│       ├── api.js               # REST API 封裝
│       ├── components.js        # UI 組件渲染（含社群頁面）
│       └── app.js               # SPA 路由、狀態管理、主題切換
├── tools/                       # 診斷與維護工具
│   ├── status_report.py         # 統合狀態報告
│   ├── validate_config.py       # 配置驗證工具
│   ├── batch_reprocess.py       # 批次重新處理
│   ├── migrate_embeddings.py    # Embedding 模型遷移（切換模型後重新生成向量）
│   ├── inspect_schema.py        # Neo4j 結構檢查
│   └── performance_diagnose.py  # 性能診斷
├── tests/                       # 測試套件（203 個測試）
│   ├── test_content_preprocessor.py # 智慧切分邏輯測試（17 個）
│   ├── test_new_features.py     # 新功能測試（32 個）
│   ├── test_i18n.py             # 多國語系測試（57 個，驗證 33 語言 key/佔位符對齊、無英文殘留、非 CJK 語言不含 CJK 字）
│   ├── test_unit.py             # 單元測試
│   ├── test_web_api.py          # Web API 測試
│   ├── test_web_ui_features.py  # Web UI 功能測試
│   ├── test_integration_manual.py # 手動整合測試（需 pytest-asyncio）
│   └── bench_deepseek_flash_vs_pro.py # DeepSeek flash/pro 寫入效能基準腳本（非單元測試）
├── docs/                        # 文檔
├── Dockerfile                   # Docker 容器化部署
└── ecosystem.config.cjs         # PM2 部署配置
```

### Key Patterns

**MCP 工具定義**：在 `graphiti_mcp_server.py` 中使用 `@mcp.tool()` 裝飾器定義，所有工具都有標準化的錯誤處理模式。

**配置層級**：JSON 配置檔為基礎 + 環境變數覆蓋（支援 Docker 部署場景）。主要配置類為 `GraphitiConfig`，支援 `get_errors()` 返回具體驗證錯誤。重要子配置：`OllamaConfig`（含 `small_model`）、`GroqConfig`、`GlmConfig`、`OpenRouterConfig`、`DeepSeekConfig`、`OllamaEmbedderConfig`、`MemoryPerformanceConfig`（切分閾值、並行度）。`GraphitiConfig.get_active_model()` 集中各提供者的模型對應，供啟動日誌、狀態回報、`test_connection` 共用，避免多處 if/elif 鏈遺漏新提供者。

**多 LLM 提供者架構**：透過 `LLM_PROVIDER` 環境變數切換提供者（`ollama` / `groq` / `glm` / `openrouter` / `deepseek`）。`_create_llm_client()` 根據設定路由到對應工廠函數（`_create_ollama_client` / `_create_glm_client` / `_create_groq_client` / `_create_openrouter_client` / `_create_deepseek_client`）。`openrouter`、`deepseek` 與 `glm` 皆透過 OpenAI 相容 SDK 連接，差別在 base_url 與 schema 注入策略。三者共同的 `json_object` 模式、簡化 schema 注入與 json 保底防護已抽到基類 `src/openai_compat_client.py` 的 `OpenAICompatClient`，各 client 僅覆寫 provider 專屬差異。

**Embedding 與 LLM 解耦**：`EMBEDDING_PROVIDER` 環境變數獨立指定嵌入器（`ollama` / `glm`），未設定時 `GraphitiConfig.get_embedding_provider()` 回退為 `llm_provider`。實際選擇邏輯：只有 embedding provider 為 `glm` 時使用 GLM Embedding（`embedding-3`），其餘一律使用 Ollama 嵌入器（預設 `bge-m3`，中文和 RAG 品質優異）。因此 `groq` / `openrouter` / `deepseek` 等不提供 Embedding 的雲端 LLM，會自動落到 Ollama `bge-m3`。`OllamaEmbedder.create_batch()` 使用 `asyncio.gather` 並發請求，非串行。

**GLM 客戶端**：`src/glm_client.py` 繼承 `OpenAICompatClient`，透過 OpenAI 相容 API 連接智谱 AI。基類已負責簡化 schema 注入（只注入字段名稱列表，避免 GLM 將完整 `$defs` JSON Schema 當資料回傳）與強制 `json_object` 模式（GLM 不支援 `json_schema`）；client 只補 base_url 與模型差異。

**OpenRouter 客戶端**：`src/openrouter_client.py` 繼承 `OpenAICompatClient`，透過 OpenAI 相容 API（`https://openrouter.ai/api/v1`）聚合各家模型（如 `stepfun/step-3.5-flash:free`）。schema 注入與 json 防護沿用基類。不提供 Embedding。

**DeepSeek 客戶端**：`src/deepseek_client.py` 繼承 `OpenAICompatClient`，透過 OpenAI 相容 API（`https://api.deepseek.com`）連接深度求索模型（`deepseek-chat` / `deepseek-v4-flash` / `deepseek-v4-pro`）。與 GLM/OpenRouter 共用基類的簡化 schema 注入。關鍵差異：DeepSeek 嚴格遵循 OpenAI 規範，使用 `json_object` 模式時**強制要求送出的 messages 內容必須包含 "json" 字串**，否則 API 直接回 `Prompt must contain the word 'json'`。因此基類 `OpenAICompatClient._generate_response` 在設定 `response_format` 前有保底防護：若所有訊息皆不含 "json"（不分大小寫），自動在最後一則補上 JSON 指示，涵蓋 `response_model=None` 等所有呼叫路徑；GLM/OpenRouter 共用基類自動受惠，避免換 endpoint 復發。不提供 Embedding。

**並發安全**：使用 `asyncio.Lock` 保護 Graphiti 初始化，防止並發競態。`clear_graph` 後自動重建 Neo4j 索引。

**雙模型分流**：`OptimizedOllamaClient` 實作 `_get_model_for_size(model_size)`，graphiti-core pipeline 在簡單任務（去重判斷、摘要生成、時間解析）傳入 `ModelSize.small`，複雜任務（實體提取、邊提取）使用 `ModelSize.medium`。透過 `OLLAMA_SMALL_MODEL` 環境變數配置小模型。

**智慧內容切分**：`src/content_preprocessor.py` 提供 `smart_chunk()` 函數，長文本（>800 字元）自動按段落分割，短段落合併，保持語意完整。`add_memory_simple` 自動整合切分邏輯。切分後使用 `add_episode_bulk()` 批量並發處理（非逐段串行），多段寫入加速約 33%。

**背景處理模式**：`add_memory_simple(background=True)` 立即返回 `task_id`，後台 `asyncio.Task` 處理。用 `get_memory_task_status(task_id)` 查詢進度。全域 `_memory_tasks` 由 `src/task_store.py` 的 `TaskStore`（`get_task_store()`）提供，採 SQLite 持久化（預設 `data/tasks.db`，可用 `TASK_DB_PATH` 覆寫）：同時維護 in-memory dict 供快速讀取，寫入時同步落盤，進程啟動時從 SQLite 還原未完成任務，避免重啟後遺失進度。

**傳輸模式**：
- `http` — HTTP Streamable（推薦），支援 MCP 端點（`/mcp`）、Web 管理介面（`/`）、REST API（`/api/*`）、健康檢查（`/health`、`/health/ready`）
- `stdio` — Claude Desktop CLI 整合
- `sse` — Server-Sent Events（已不建議使用，MCP 1.x 有 session 初始化相容性問題）

**完整模式（預設）**：`add_memory_simple` 預設使用 `use_safe_mode=False`，透過完整的實體提取流程建立 Entity 節點和關係，使記憶可被 `search_memory_nodes` 和 `search_memory_facts` 搜尋。安全模式（`use_safe_mode=True`）僅建立 EpisodicNode，速度快但無法被搜尋。

**記憶去重**：`src/deduplication.py` 提供 `check_episode_similarity()` 函數，在 `add_memory_simple` 完整模式前檢查餘弦相似度，超過閾值（預設 0.9）時警告。`force=True` 跳過檢查。

**重要性追蹤**：`src/importance.py` 在搜尋操作完成後，用 `asyncio.create_task()` 非同步更新 `access_count` 和 `last_accessed` 屬性。`get_stale_memories` 和 `cleanup_stale_memories` 工具基於這些屬性識別過時記憶。

**進階搜尋**：`SEARCH_RECIPES` 字典映射 16 個 `SearchConfig` 預設方案，`_build_search_filters()` 輔助函數將簡化參數轉換為 `SearchFilters` 物件。`search_memory_facts` 已升級為使用 `graphiti.search_()` API。

**社群檢測**：`build_communities` 工具包裝 graphiti-core 的 Label Propagation 演算法，預設背景執行。Web UI 新增社群瀏覽頁面。

**多國語系（i18n）**：`src/i18n.py` 維護 **33 種語言** 的訊息字典 `MESSAGES`，key 採 `group.action` 扁平命名。其中 `zh-TW`（基準/fallback）、`en`、`zh-CN`、`ja` 為手寫，其餘 29 種語言由 `src/i18n_generated.py` 的 `GENERATED_MESSAGE_OVERRIDES` 提供。合成邏輯（i18n.py 末段迴圈）每個語言以 `MESSAGES['en']` 為底，依序套用手寫覆蓋 → `GENERATED_MESSAGE_OVERRIDES` → `MANUAL_MESSAGE_OVERRIDES`，確保所有語言 key 與 `zh-TW` 完全對齊（缺翻譯自動回退英文）。`t(key, lang, **params)` 取模板並以 `str.format` 插值，fallback 順序為 `lang → zh-TW → key`，格式化失敗絕不冒泡成例外。兩條輸出路徑共用此字典但語言來源不同：**MCP 工具** 依 `app_config.server_lang`（`SERVER_LANG` 環境變數，透過模組級 `_srv_lang()` 取得）；**REST API** 依每個請求的 HTTP `Accept-Language` header，由 `parse_accept_language()`（含 q 值排序、裸 `zh`→`zh-TW`、萬用字元忽略）解析。新增訊息時只需補上 `zh-TW`，未翻譯語言會先回退英文；`tests/test_i18n.py` 會驗證所有語言 key 與佔位符對齊。注意：`create_error_response()` 餵入的技術性例外 context（如「搜索節點失敗」）由 `src/exceptions.py` 產生，未納入此 i18n 範圍。

## MCP Tools (19 tools)

| 類別 | 工具 | 說明 |
|------|------|------|
| 記憶管理 | `add_memory_simple` | 添加記憶（支援背景處理、智慧切分、去重檢查） |
| 記憶管理 | `add_episode_bulk` | 批量添加多筆記憶（預設背景處理） |
| 記憶管理 | `add_triplet` | 結構化三元組添加（跳過 LLM，秒速完成） |
| 記憶管理 | `search_memory_nodes` | 搜尋記憶節點（支援搜尋策略、時間過濾） |
| 記憶管理 | `search_memory_facts` | 搜尋記憶事實（支援關係類型、時間、有效性過濾） |
| 記憶管理 | `advanced_search` | 進階搜尋（16 種策略，回傳完整結果） |
| 記憶管理 | `get_episodes` | 獲取最近的記憶片段 |
| 知識分析 | `check_conflicts` | 檢測兩實體間的事實衝突 |
| 知識分析 | `get_node_edges` | 探索節點的入邊和出邊關係 |
| 知識分析 | `build_communities` | 社群檢測與聚類（預設背景處理） |
| 記憶維護 | `get_stale_memories` | 查詢過時、低存取量的記憶 |
| 記憶維護 | `cleanup_stale_memories` | 清理過時記憶（預設 dry_run） |
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
| `force` | bool | `False` | 跳過去重檢查（強制添加） |
| `excluded_entity_types` | list | None | 排除的實體類型（減少提取量） |

## Web 管理介面

HTTP 模式下自動啟用，訪問 `http://localhost:8000/` 即可使用。

**功能**：儀表板統計、實體節點/事實/記憶片段瀏覽與搜尋、社群瀏覽與建構、三元組表單、group 篩選與刪除、深色/淺色主題、節點/事實/片段刪除操作、資料匯出與批量匯入、知識圖譜視覺化、AI 問答、品質維護分析、運行時設定檢視/調整。

**REST API**：

| 端點 | 說明 |
|------|------|
| `GET /api/stats` | 儀表板統計 |
| `GET /api/groups` | 取得所有 group_id |
| `GET /api/groups/stats` | 各 group 的節點/事實/片段統計 |
| `GET /api/nodes` | 瀏覽實體節點（分頁） |
| `GET /api/facts` | 瀏覽事實（分頁） |
| `GET /api/episodes` | 瀏覽記憶片段（分頁） |
| `GET /api/nodes/{uuid}/relations` | 取得節點的入邊/出邊關係 |
| `GET /api/search/nodes` | 向量搜尋節點 |
| `GET /api/search/facts` | 向量搜尋事實 |
| `GET /api/search/episodes` | 搜尋記憶片段 |
| `GET /api/search/advanced` | 進階搜尋（16 種策略） |
| `GET /api/communities` | 瀏覽社群節點（分頁） |
| `POST /api/communities/build` | 觸發社群建構 |
| `POST /api/memory/add` | 添加單筆記憶 |
| `POST /api/memory/add-bulk` | 批量添加記憶 |
| `POST /api/memory/add-triplet` | 添加三元組 |
| `POST /api/import/episodes` | 批量匯入記憶片段（JSON，單次上限 500 筆） |
| `GET /api/memory/tasks` | 列出背景記憶處理任務 |
| `GET /api/memory/tasks/{id}` | 查詢單一任務狀態 |
| `GET /api/timeline` | 時間軸瀏覽 |
| `GET /api/graph/subgraph` | 取得子圖（視覺化） |
| `GET /api/graph/all` | 取得完整圖（視覺化） |
| `GET /api/ask` | AI 問答（基於圖譜檢索） |
| `GET /api/analytics/top-nodes` | 高連結度/高存取節點 |
| `GET /api/analytics/quality` | 知識圖譜品質指標 |
| `GET /api/analytics/stale` | 查詢過時記憶 |
| `POST /api/analytics/cleanup` | 清理過時記憶 |
| `GET /api/config` | 取得目前生效設定（不含 API key） |
| `PATCH /api/config` | 運行時更新可修改設定（僅本進程生效，重啟還原） |
| `DELETE /api/nodes/{uuid}` | 刪除節點 |
| `DELETE /api/episodes/{uuid}` | 刪除記憶片段 |
| `DELETE /api/facts/{uuid}` | 刪除事實 |
| `DELETE /api/groups/{group_id}` | 刪除整個 group |

**健康檢查**：`/health`（liveness）、`/health/ready`（readiness，實際檢查 Neo4j 連線）

**架構**：`src/web_api.py`（後端 API + CORS 中間件）+ `web/`（前端 SPA，無 build pipeline）。瀏覽用 Cypher 直查、搜尋用 `graphiti.search_()` 向量搜尋。

## Required Services

- **Neo4j**: `bolt://localhost:7687`（4.0+）
- **LLM 提供者**（五選一，透過 `LLM_PROVIDER` 切換）：
  - **Ollama**（`ollama`，預設）：本地 LLM，`http://localhost:11434`
    - LLM 主模型: `qwen2.5:3b`（推薦）、小模型: `qwen2.5:3b`
    - Embedder: `bge-m3`（原生 1024 維；中文和 RAG 品質優於 nomic-embed-text。graphiti-core 用即時 `vector.similarity.cosine` 計算、無 ANN 索引維度限制，故不需截斷）
  - **GLM**（`glm`）：智谱 AI 雲端，免費 `glm-4-flash` 模型
    - LLM: `glm-4-flash`（免費，穩定，~22s/短文本寫入）
    - Embedder: `embedding-3`（1024 維，與 bge-m3 對齊，設 `GLM_EMBEDDING_DIMENSIONS=1024`）
  - **GROQ**（`groq`）：高速雲端推理
    - LLM: `llama-3.3-70b-versatile`（速度快但有 Rate Limit）
    - 不提供 Embedding，自動回退 Ollama `bge-m3`
  - **OpenRouter**（`openrouter`）：聚合各家模型的雲端閘道
    - LLM: 任意 OpenRouter 模型（如 `stepfun/step-3.5-flash:free`）
    - 不提供 Embedding，自動回退 Ollama `bge-m3`
  - **DeepSeek**（`deepseek`）：深度求索雲端
    - LLM: `deepseek-v4-flash`（推薦，速度快）/ `deepseek-v4-pro`（效果更佳）/ `deepseek-chat`（將於 2026-07-24 下線）
    - 不提供 Embedding，自動回退 Ollama `bge-m3`
- **Embedding 提供者**（透過 `EMBEDDING_PROVIDER` 獨立指定，預設跟隨 `LLM_PROVIDER`）：僅 `glm` 使用 GLM `embedding-3`，其餘一律 Ollama `bge-m3`。

> **模型選擇注意**：
> - Ollama 的 `qwen2.5:1.5b` 在 graphiti-core 結構化 JSON 輸出上不穩定（成功率僅 33%）。`qwen2.5:3b` 是能穩定運行的最小可行模型（成功率 100%）。
> - GLM `glm-4-flash` 免費且穩定（零 Rate Limit 錯誤），但寫入速度比本地 Ollama 慢 2-5 倍。
> - DeepSeek / OpenRouter / GLM 皆走 OpenAI `json_object` 模式。DeepSeek 嚴格要求 prompt 含 "json" 字串，client 已內建保底防護（見上方 DeepSeek 客戶端說明）。

## Key Environment Variables

| 變數 | 說明 | 預設值 |
|------|------|--------|
| `LLM_PROVIDER` | LLM 提供者（`ollama` / `groq` / `glm` / `openrouter` / `deepseek`） | `ollama` |
| `EMBEDDING_PROVIDER` | Embedding 提供者（`ollama` / `glm`），獨立於 LLM | (跟隨 `LLM_PROVIDER`) |
| `NEO4J_URI` | Neo4j 連接 URI | `bolt://localhost:7687` |
| `NEO4J_PASSWORD` | Neo4j 密碼 | (必填) |
| `OLLAMA_MODEL` | Ollama 主 LLM 模型 | `qwen2.5:7b` |
| `OLLAMA_SMALL_MODEL` | Ollama 小 LLM 模型（簡單任務） | 與主模型相同 |
| `OLLAMA_TARGET_LANGUAGE` | 強制 LLM 輸出語言（如 "Traditional Chinese"） | (未設定) |
| `OLLAMA_EMBEDDING_MODEL` | Ollama 嵌入模型 | `bge-m3` |
| `GLM_API_KEY` | 智谱 AI API Key | (GLM 模式必填) |
| `GLM_MODEL` | GLM LLM 模型 | `glm-4-flash` |
| `GLM_EMBEDDING_MODEL` | GLM 嵌入模型 | `embedding-3` |
| `GLM_EMBEDDING_DIMENSIONS` | GLM 嵌入維度（與 bge-m3 對齊） | `1024` |
| `GROQ_API_KEY` | GROQ API Key | (GROQ 模式必填) |
| `GROQ_MODEL` | GROQ LLM 模型 | `llama-3.3-70b-versatile` |
| `OPENROUTER_API_KEY` | OpenRouter API Key | (OpenRouter 模式必填) |
| `OPENROUTER_MODEL` | OpenRouter 模型 | `stepfun/step-3.5-flash:free` |
| `DEEPSEEK_API_KEY` | DeepSeek API Key | (DeepSeek 模式必填) |
| `DEEPSEEK_MODEL` | DeepSeek LLM 模型 | `deepseek-chat` |
| `GRAPHITI_DISPLAY_TIMEZONE` | API 回傳時間戳的顯示時區（IANA 名稱） | `UTC` |
| `SERVER_LANG` | MCP 工具回應語言（33 語言，完整清單見 `src/i18n.py` 的 `SUPPORTED_LANGUAGES`）；REST API 改依 Accept-Language 協商 | `zh-TW` |
| `GRAPHITI_CHUNK_THRESHOLD` | 觸發智慧切分的字元數 | `800` |
| `GRAPHITI_MAX_CHUNK_SIZE` | 切分後每段最大字元數 | `600` |
| `GRAPHITI_MAX_COROUTINES` | 最大並行協程數 | `10` |
| `GRAPHITI_DEFAULT_BACKGROUND` | 預設背景處理 | `false` |
| `TASK_DB_PATH` | 背景任務 SQLite 持久化路徑 | `data/tasks.db` |
| `ENABLE_IMPORTANCE_TRACKING` | 啟用存取追蹤 | `true` |
| `IMPORTANCE_WEIGHT` | 重要性權重 | `0.1` |
| `STALE_DAYS_THRESHOLD` | 過時天數閾值 | `30` |
| `STALE_MIN_ACCESS_COUNT` | 最低存取次數 | `2` |

完整環境變數列表參見 `.env.example`。

## Key Files to Read

- `docs/使用工具的指令.md` — MCP 工具使用指南和最佳實踐
- `docs/graphiti-memory-rules.md` — 記憶規則說明
- `.env.example` — 環境變數範例（完整列表）

## Upstream Reference

本專案基於 [getzep/graphiti/mcp_server](https://github.com/getzep/graphiti/tree/main/mcp_server) 擴充開發。本地新增功能包括：多 LLM 提供者架構（Ollama / GLM / GROQ / OpenRouter / DeepSeek 動態切換）、Embedding 與 LLM 解耦（`EMBEDDING_PROVIDER`）、Ollama 深度適配（含雙模型分流）、OpenAICompatClient 基類（GLM / OpenRouter / DeepSeek 共用簡化 schema 注入與 DeepSeek json_object 保底防護）、Web 管理介面（含社群瀏覽、三元組表單、批量匯入、運行時設定）、19 個 MCP 工具（含進階搜尋、衝突偵測、去重、重要性追蹤、智慧遺忘）、安全模式（Safe Mode）、智慧內容切分、背景記憶處理（TaskStore SQLite 持久化）、運行時 Config API、33 語言 i18n、完整異常/日誌系統。上游使用 graphiti-core 最新版，本地依賴 >=0.24.3。
