# AGENTS.md

Codex 在此 repository 工作時請優先遵守本文件。`CLAUDE.md` 可作為完整背景參考，但本文件是精簡後的 Codex 操作版。

## 專案概覽

Graphiti MCP Server 是一個知識圖譜記憶服務，基於 `getzep/graphiti` 的 MCP server 擴充，整合 Neo4j 與多種 LLM provider：

- LLM provider：`ollama`、`groq`、`glm`、`openrouter`、`deepseek`
- Embedding provider：獨立於 LLM，支援 `ollama` 與 `glm`
- Transport：`http`、`stdio`、`sse`
- Web 管理介面：HTTP 模式下由 `src/web_api.py` 與 `web/` 提供

核心設計：LLM 與 Embedding 解耦、長文本智慧切分、背景記憶處理、去重、重要性追蹤、i18n、多 provider client adapter。

## 常用命令

```bash
# 安裝依賴
uv sync

# HTTP 模式，含 MCP endpoint、REST API、Web 管理介面
uv run python graphiti_mcp_server.py --transport http --port 8000

# STDIO 模式，供 Codex Desktop / MCP client 使用
uv run python graphiti_mcp_server.py --transport stdio

# 使用 JSON config，仍可被環境變數覆蓋
uv run python graphiti_mcp_server.py --config your_config.json --transport http

# PM2
pm2 start ecosystem.config.cjs
pm2 logs graphiti-mcp-http
pm2 restart graphiti-mcp-http --update-env

# Docker
docker build -t graphiti-mcp .
docker run -p 8000:8000 --env-file .env graphiti-mcp
```

## 測試與檢查

```bash
# 全部測試
uv run python -m pytest tests/

# 常用目標測試
uv run python -m pytest tests/test_content_preprocessor.py -v
uv run python -m pytest tests/test_i18n.py -v
uv run python -m pytest tests/test_web_api.py -v

# 快速 import 檢查
uv run python -c "import src.config; print('OK')"
uv run python -c "import src.ollama_embedder; print('OK')"
uv run python -c "from src.ollama_graphiti_client import OptimizedOllamaClient; print('OK')"
uv run python -c "from src.glm_client import GlmClient; print('OK')"
uv run python -c "from src.openrouter_client import OpenRouterClient; print('OK')"
uv run python -c "from src.deepseek_client import DeepSeekClient; print('OK')"

# MCP Inspector
npx @modelcontextprotocol/inspector uv run python graphiti_mcp_server.py --transport stdio
```

注意：`tests/test_integration_manual.py` 內的 async manual integration tests 需要 `pytest-asyncio` 與外部服務，失敗不一定代表一般單元測試壞掉。

## 維護工具

```bash
uv run python tools/status_report.py
uv run python tools/validate_config.py
uv run python tools/inspect_schema.py
uv run python tools/performance_diagnose.py
uv run python tools/batch_reprocess.py
uv run python tools/migrate_embeddings.py
```

## 主要檔案

```text
graphiti_mcp_server.py             # FastMCP 主入口與 MCP tools
src/config.py                      # GraphitiConfig 與所有 provider config
src/web_api.py                     # Web 管理介面 REST API
src/ollama_graphiti_client.py      # Ollama LLM adapter，含雙模型分流
src/openai_compat_client.py        # OpenAI-compatible LLM 基類，GLM/OpenRouter/DeepSeek 共用
src/glm_client.py                  # GLM client（繼承 OpenAICompatClient）
src/openrouter_client.py           # OpenRouter client（繼承 OpenAICompatClient）
src/deepseek_client.py             # DeepSeek client（繼承 OpenAICompatClient）
src/ollama_embedder.py             # Ollama embedding adapter
src/content_preprocessor.py        # 長文本智慧切分
src/deduplication.py               # 記憶去重
src/importance.py                  # 存取追蹤與 stale memory
src/safe_memory_add.py             # 安全模式記憶添加
src/task_store.py                  # 背景任務 SQLite 持久化（TaskStore）
src/i18n.py                        # 後端多語系訊息（33 語言）
src/i18n_generated.py              # 自動生成的語系覆蓋（GENERATED_MESSAGE_OVERRIDES）
src/timezone_utils.py              # 時區顯示轉換
src/exceptions.py                  # 結構化錯誤
src/logging_setup.py               # logging 設定
web/                               # 純 HTML/CSS/JS SPA，無 build pipeline
tools/                             # 診斷、維護、遷移工具
tests/                             # pytest 測試
docs/使用工具的指令.md              # MCP tool 使用指南
docs/graphiti-memory-rules.md      # 記憶規則
.env.example                       # 完整環境變數範例
```

## 架構規則

### MCP tools

- MCP tools 都定義在 `graphiti_mcp_server.py`，使用 `@mcp.tool()`。
- 新增或修改工具時，維持既有回傳格式與錯誤處理模式。
- 涉及使用者可見訊息時，優先走 `src/i18n.py` 的 `t()`。
- `clear_graph` 後需確保 Neo4j indexes 會被重建。

### Provider client

- LLM provider 由 `LLM_PROVIDER` 控制：`ollama`、`groq`、`glm`、`openrouter`、`deepseek`。
- `_create_llm_client()` 負責 provider routing；新增 provider 時同步補 config、factory、status/test_connection 顯示。
- `GraphitiConfig.get_active_model()` 是模型顯示與狀態回報的集中來源，不要在多處重寫 if/elif。
- `glm`、`openrouter`、`deepseek` 都走 OpenAI-compatible API，共同邏輯（`json_object` 模式、簡化 schema 注入、json 保底防護）抽到基類 `src/openai_compat_client.py` 的 `OpenAICompatClient`，三個 client 繼承它，只補各自 base_url 與模型差異；schema 注入策略不同於 Ollama。
- DeepSeek 使用 `json_object` 模式時 prompt 必須包含 `json` 字串；基類 `OpenAICompatClient._generate_response` 已有保底防護（涵蓋所有呼叫路徑），修改基類時不要移除。
- 此防護由基類提供，GLM/OpenRouter 一併受惠，避免 endpoint 行為變更造成復發。

### Embedding

- `EMBEDDING_PROVIDER` 獨立於 `LLM_PROVIDER`；未設定時由 `GraphitiConfig.get_embedding_provider()` 回退。
- 實際支援：`glm` 使用 GLM `embedding-3`，其他情況使用 Ollama embedding。
- Ollama 預設 embedding model 是 `bge-m3`。其 1024 維向量會截斷成 768 以相容 Neo4j index。
- `OllamaEmbedder.create_batch()` 使用 `asyncio.gather` 並發，避免改成串行。

### 記憶寫入

- `add_memory_simple` 預設 `use_safe_mode=False`，會走完整實體/關係提取，搜尋才完整可用。
- `use_safe_mode=True` 只建立 `EpisodicNode`，速度快但無法被 nodes/facts 搜尋完整命中。
- 長文本透過 `src/content_preprocessor.py` 的 `smart_chunk()` 切分，切分後使用 bulk 並發寫入。
- `background=True` 會建立 `asyncio.Task` 並回傳 `task_id`；狀態由 `_memory_tasks`（`src/task_store.py` 的 `TaskStore`）追蹤，採 SQLite 持久化（預設 `data/tasks.db`，`TASK_DB_PATH` 可覆寫），重啟後會還原未完成任務。
- 去重由 `src/deduplication.py` 的 cosine similarity 處理，`force=True` 才跳過。

### 搜尋與維護

- `search_memory_facts` 使用 `graphiti.search_()`，不是舊式直查。
- 進階搜尋 recipe 集中在 `SEARCH_RECIPES`，簡化參數透過 `_build_search_filters()` 轉 `SearchFilters`。
- 搜尋後的重要性追蹤用背景 task 更新 `access_count`、`last_accessed`。
- `get_stale_memories` 與 `cleanup_stale_memories` 依 importance metadata 判斷，cleanup 預設應保持 dry-run 友善。

### i18n

- `src/i18n.py` 維護 33 種語言的 `MESSAGES`：`zh-TW`（基準/fallback）、`en`、`zh-CN`、`ja` 為手寫，其餘 29 種由 `src/i18n_generated.py` 的 `GENERATED_MESSAGE_OVERRIDES` 提供。
- 合成邏輯每個語言以 `en` 為底，依序套用手寫覆蓋 → generated → manual overrides，確保所有語言 key 與 `zh-TW` 對齊（缺翻譯回退英文）。
- key 使用扁平命名，如 `group.action`；`t(key, lang, **params)` 以 `str.format` 插值，fallback 順序 `lang → zh-TW → key`，格式化失敗不冒泡成例外。
- 新增訊息時只需補 `zh-TW`；新增/擴充語系時所有語言必須同步補齊同一組 key；`tests/test_i18n.py` 會檢查 key 與 placeholder 對齊。
- MCP 工具語言依 `SERVER_LANG` / `app_config.server_lang`。
- REST API 語言依每個 request 的 `Accept-Language`，由 `parse_accept_language()` 處理。
- `src/exceptions.py` 的技術性 context 目前不屬於 i18n 範圍。

支援語系：

| Locale | 顯示名稱 |
| --- | --- |
| `zh-CN` | 🇨🇳 中文 |
| `zh-TW` | 🇹🇼 繁體中文 |
| `en` | English |
| `ja` | 🇯🇵 日本語 |
| `pt-PT` | 🇵🇹 Português |
| `pt-BR` | 🇧🇷 Português |
| `ko` | 🇰🇷 한국어 |
| `es` | 🇪🇸 Español |
| `de` | 🇩🇪 Deutsch |
| `fr` | 🇫🇷 Français |
| `he` | 🇮🇱 עברית |
| `ar` | 🇸🇦 العربية |
| `ru` | 🇷🇺 Русский |
| `pl` | 🇵🇱 Polski |
| `cs` | 🇨🇿 Čeština |
| `nl` | 🇳🇱 Nederlands |
| `tr` | 🇹🇷 Türkçe |
| `uk` | 🇺🇦 Українська |
| `vi` | 🇻🇳 Tiếng Việt |
| `tl` | 🇵🇭 Tagalog |
| `id` | 🇮🇩 Indonesia |
| `th` | 🇹🇭 ไทย |
| `hi` | 🇮🇳 हिन्दी |
| `bn` | 🇧🇩 বাংলা |
| `ur` | 🇵🇰 اردو |
| `ro` | 🇷🇴 Română |
| `sv` | 🇸🇪 Svenska |
| `it` | 🇮🇹 Italiano |
| `el` | 🇬🇷 Ελληνικά |
| `hu` | 🇭🇺 Magyar |
| `fi` | 🇫🇮 Suomi |
| `da` | 🇩🇰 Dansk |
| `no` | 🇳🇴 Norsk |

### Web UI

- `web/` 是純 HTML/CSS/JS SPA，沒有 build step。
- API 封裝在 `web/js/api.js`，渲染在 `web/js/components.js`，路由/狀態在 `web/js/app.js`。
- 後端 REST API 在 `src/web_api.py`。
- Web 改動後可用 HTTP 模式手動檢查 `http://localhost:8000/`。

## MCP tools 一覽

目前主工具共 19 個：

- 記憶管理：`add_memory_simple`、`add_episode_bulk`、`add_triplet`、`search_memory_nodes`、`search_memory_facts`、`advanced_search`、`get_episodes`
- 知識分析：`check_conflicts`、`get_node_edges`、`build_communities`
- 記憶維護：`get_stale_memories`、`cleanup_stale_memories`
- 任務管理：`get_memory_task_status`
- 刪除查詢：`delete_episode`、`delete_entity_edge`、`get_entity_edge`
- 系統管理：`get_status`、`test_connection`、`clear_graph`

`add_memory_simple` 重要參數：

| 參數 | 預設值 | 說明 |
| --- | --- | --- |
| `name` | 必填 | 記憶名稱 |
| `episode_body` | 必填 | 記憶內容 |
| `group_id` | `default` | 分組 ID |
| `source_description` | `MCP Server` | 來源描述 |
| `source` | `text` | `text` / `json` / `message` |
| `episode_uuid` | `None` | 自定義 UUID |
| `use_safe_mode` | `False` | 跳過實體提取 |
| `background` | `False` | 背景處理並回傳 task id |
| `force` | `False` | 跳過去重檢查 |
| `excluded_entity_types` | `None` | 減少實體提取量 |

## REST API 與健康檢查

HTTP 模式下：

- Web UI：`GET /`
- MCP endpoint：`/mcp`
- Liveness：`GET /health`
- Readiness：`GET /health/ready`

主要 REST API：

| 端點 | 說明 |
| --- | --- |
| `GET /api/stats` | 儀表板統計 |
| `GET /api/groups` | group 列表 |
| `GET /api/groups/stats` | 各 group 統計 |
| `GET /api/nodes` | 節點瀏覽 |
| `GET /api/facts` | 事實瀏覽 |
| `GET /api/episodes` | 記憶片段瀏覽 |
| `GET /api/nodes/{uuid}/relations` | 節點關係 |
| `GET /api/search/nodes` | 節點搜尋 |
| `GET /api/search/facts` | 事實搜尋 |
| `GET /api/search/episodes` | 記憶片段搜尋 |
| `GET /api/search/advanced` | 進階搜尋 |
| `GET /api/communities` | 社群瀏覽 |
| `POST /api/communities/build` | 建立社群 |
| `POST /api/memory/add` | 添加單筆記憶 |
| `POST /api/memory/add-bulk` | 批量記憶 |
| `POST /api/memory/add-triplet` | 三元組 |
| `POST /api/import/episodes` | 批量匯入（上限 500 筆） |
| `GET /api/memory/tasks` | 背景任務列表 |
| `GET /api/memory/tasks/{id}` | 單一背景任務 |
| `GET /api/timeline` | 時間軸 |
| `GET /api/graph/subgraph` | 子圖（視覺化） |
| `GET /api/graph/all` | 完整圖（視覺化） |
| `GET /api/ask` | AI 問答 |
| `GET /api/analytics/top-nodes` | 高連結度/高存取節點 |
| `GET /api/analytics/quality` | 品質指標 |
| `GET /api/analytics/stale` | 過時記憶 |
| `POST /api/analytics/cleanup` | 清理過時記憶 |
| `GET /api/config` | 取得生效設定（不含 key） |
| `PATCH /api/config` | 運行時更新設定（僅本進程） |
| `DELETE /api/nodes/{uuid}` | 刪除節點 |
| `DELETE /api/episodes/{uuid}` | 刪除 episode |
| `DELETE /api/facts/{uuid}` | 刪除 fact |
| `DELETE /api/groups/{group_id}` | 刪除 group |

## 重要環境變數

完整列表以 `.env.example` 為準。常用變數：

| 變數 | 預設值 | 說明 |
| --- | --- | --- |
| `LLM_PROVIDER` | `ollama` | `ollama` / `groq` / `glm` / `openrouter` / `deepseek` |
| `EMBEDDING_PROVIDER` | 跟隨 LLM | `ollama` / `glm` |
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j URI |
| `NEO4J_PASSWORD` | 必填 | Neo4j 密碼 |
| `OLLAMA_MODEL` | `qwen2.5:7b` | Ollama 主模型 |
| `OLLAMA_SMALL_MODEL` | 主模型 | 小任務模型 |
| `OLLAMA_EMBEDDING_MODEL` | `bge-m3` | Ollama embedding |
| `GLM_API_KEY` | 必填於 GLM | GLM API key |
| `GLM_MODEL` | `glm-4-flash` | GLM LLM |
| `GLM_EMBEDDING_MODEL` | `embedding-3` | GLM embedding |
| `GLM_EMBEDDING_DIMENSIONS` | `768` | GLM embedding 維度 |
| `GROQ_API_KEY` | 必填於 GROQ | GROQ API key |
| `OPENROUTER_API_KEY` | 必填於 OpenRouter | OpenRouter API key |
| `DEEPSEEK_API_KEY` | 必填於 DeepSeek | DeepSeek API key |
| `DEEPSEEK_MODEL` | `deepseek-chat` | DeepSeek model |
| `GRAPHITI_DISPLAY_TIMEZONE` | `UTC` | API 顯示時區 |
| `SERVER_LANG` | `zh-TW` | MCP 回應語言，需支援 i18n 目標語系 |
| `GRAPHITI_CHUNK_THRESHOLD` | `800` | 觸發切分字數 |
| `GRAPHITI_MAX_CHUNK_SIZE` | `600` | chunk 最大字數 |
| `GRAPHITI_MAX_COROUTINES` | `10` | 最大並行數 |
| `GRAPHITI_DEFAULT_BACKGROUND` | `false` | 預設背景寫入 |
| `TASK_DB_PATH` | `data/tasks.db` | 背景任務 SQLite 持久化路徑 |
| `ENABLE_IMPORTANCE_TRACKING` | `true` | 啟用重要性追蹤 |
| `STALE_DAYS_THRESHOLD` | `30` | stale 判斷天數 |
| `STALE_MIN_ACCESS_COUNT` | `2` | stale 最低存取次數 |

## 依賴服務與模型注意

- Neo4j：預設 `bolt://localhost:7687`。
- Ollama：預設 `http://localhost:11434`，建議至少使用 `qwen2.5:3b`；`qwen2.5:1.5b` 在 graphiti-core JSON 輸出上不穩。
- GROQ、OpenRouter、DeepSeek 不提供 embedding，會落回 Ollama `bge-m3`。
- GLM 可同時作 LLM 與 embedding provider，embedding 維度需與 Neo4j index 一致。
- DeepSeek / OpenRouter / GLM 使用 OpenAI `json_object` 模式時，保留 schema 簡化與 JSON prompt 防護。

## 開發準則

- 優先沿用現有函式、config class、錯誤格式與 i18n pattern。
- 不要把 provider-specific 邏輯散落到多處；集中到 config、client factory 或對應 client。
- 修改使用者可見輸出時同步更新 `tests/test_i18n.py` 相關期待。
- 修改記憶寫入、搜尋、背景任務、provider client 時，至少跑對應單元測試或 import 檢查。
- 修改 Web UI 時保持無 build pipeline，避免引入前端套件管理除非使用者明確要求。
- 不要提交 `.env`、API key、Neo4j 密碼或 runtime logs。

## 上游參考

上游基底：[getzep/graphiti/mcp_server](https://github.com/getzep/graphiti/tree/main/mcp_server)

本地擴充重點：多 LLM provider、Embedding 解耦、Ollama 雙模型分流、OpenAICompatClient 基類（GLM/OpenRouter/DeepSeek 共用 + DeepSeek json_object 防護）、Web 管理介面、進階搜尋、衝突偵測、去重、重要性追蹤、智慧遺忘、安全模式、智慧內容切分、背景記憶處理（TaskStore SQLite 持久化）、運行時 Config API、批量匯入、33 語言 i18n、結構化錯誤與 logging。依賴 graphiti-core `>=0.24.3`。
