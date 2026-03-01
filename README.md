# Graphiti MCP Server

本地化知識圖譜記憶服務 — 整合 Ollama 本地 LLM 與 Neo4j 圖資料庫的 MCP 服務器。

基於 [getzep/graphiti](https://github.com/getzep/graphiti) 擴充開發，專為本地 Ollama 環境優化。

## 特色功能

- **智能記憶管理** — 使用知識圖譜儲存和檢索複雜的記憶關係
- **語意搜尋** — 基於向量嵌入的混合搜尋（向量 + 關鍵字 + 圖遍歷）
- **完全本地化** — 使用 Ollama 本地 LLM，無需外部 API，資料不離開本機
- **雙模型分流** — 複雜任務使用主模型，簡單任務自動切換小模型以提升效能
- **智慧內容切分** — 長文本自動分段處理，降低 LLM 負載（可配置閾值）
- **背景記憶處理** — 記憶添加可在背景執行，MCP 呼叫立即返回
- **Web 管理介面** — 內建儀表板、瀏覽、搜尋、知識圖譜視覺化、AI 問答
- **深色/淺色主題** — Web 介面支援主題切換
- **安全模式** — 可選擇跳過實體提取的快速記憶添加
- **Docker 支援** — 內建 Dockerfile，支援容器化部署
- **並發安全** — asyncio.Lock 保護初始化，防止競態條件
- **分層健康檢查** — `/health`（liveness）+ `/health/ready`（readiness）

## 系統需求

| 項目 | 需求 |
|------|------|
| Python | 3.10+（推薦 3.11+） |
| Neo4j | 4.0+（`bolt://localhost:7687`） |
| Ollama | 本地運行（`http://localhost:11434`） |
| Node.js | 18+（僅用於 PM2 背景執行，可選） |
| 磁碟空間 | ~3GB（Ollama 模型 + Neo4j 資料） |

### 必需的 Ollama 模型

```bash
# LLM 主模型（推薦 qwen2.5:3b，速度與穩定性最佳平衡）
ollama pull qwen2.5:3b

# 嵌入模型（必須，用於向量搜尋）
ollama pull nomic-embed-text:v1.5
```

> **模型選擇注意事項**：
> - `qwen2.5:3b` — 推薦，~2s/call、~100 t/s，graphiti-core 結構化輸出 100% 穩定
> - `qwen2.5:7b` — 效果更好但慢 5-10 倍，適合追求品質的場景
> - `qwen2.5:1.5b` — 速度最快但**不穩定**（結構化 JSON 成功率僅 33%），不建議使用
> - 小模型（`OLLAMA_SMALL_MODEL`）用於去重判斷、摘要生成等簡單任務，可配置為與主模型不同

## 快速啟動

### 1. 前置準備

確認以下服務已在本機運行：

```bash
# 確認 Neo4j 運行中
neo4j status
# 或者使用 Docker: docker run -d -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/your_password neo4j:latest

# 確認 Ollama 運行中
ollama list
# 若未啟動: ollama serve
```

### 2. 安裝依賴

```bash
git clone <repo-url>
cd graphiti
uv sync
```

> **注意**：本專案使用 [uv](https://github.com/astral-sh/uv) 管理依賴。若未安裝：`curl -LsSf https://astral.sh/uv/install.sh | sh`

### 3. 配置環境

```bash
cp .env.example .env
```

編輯 `.env`，**至少**需要修改以下項目：

```bash
NEO4J_PASSWORD=your_actual_password  # 必填：Neo4j 密碼
OLLAMA_MODEL=qwen2.5:3b              # 推薦：本地 LLM 模型
```

### 4. 啟動服務

```bash
# HTTP 模式（推薦，包含 Web 管理介面）
uv run python graphiti_mcp_server.py --transport http --port 8000

# 或使用 PM2 背景執行（推薦長期運行）
pm2 start ecosystem.config.cjs
```

### 5. 驗證服務

啟動後可訪問以下端點：

| 端點 | 說明 |
|------|------|
| http://localhost:8000/ | Web 管理介面 |
| http://localhost:8000/mcp | MCP 端點（供 MCP 客戶端連接） |
| http://localhost:8000/health | 健康檢查（liveness） |
| http://localhost:8000/health/ready | 深度檢查（含 Neo4j 連線） |
| http://localhost:8000/api/stats | REST API 統計 |

## 專案結構

```
graphiti/
├── graphiti_mcp_server.py        # 主入口 — MCP 工具定義（11 個工具）
├── src/
│   ├── config.py                 # 配置管理（GraphitiConfig，支援 JSON/.env 層疊）
│   ├── web_api.py                # Web 管理介面 REST API
│   ├── ollama_graphiti_client.py  # Ollama LLM 客戶端（雙模型分流）
│   ├── ollama_embedder.py        # Ollama 嵌入模型適配器
│   ├── content_preprocessor.py   # 智慧內容切分（長文本自動分段）
│   ├── safe_memory_add.py        # 安全記憶添加（跳過實體提取）
│   ├── exceptions.py             # 結構化異常處理（12 種異常類別）
│   └── logging_setup.py          # 日誌系統（時間輪轉 + 性能監控）
├── web/                          # Web 管理介面前端（SPA，無 build）
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js                # REST API 封裝
│       ├── components.js         # UI 組件渲染
│       └── app.js                # SPA 路由、狀態管理
├── tests/                        # 測試套件（111 個測試）
│   ├── test_content_preprocessor.py  # 切分邏輯測試
│   ├── test_unit.py              # 單元測試
│   ├── test_web_api.py           # Web API 測試
│   ├── test_web_ui_features.py   # Web UI 功能測試
│   └── test_integration_manual.py # 手動整合測試
├── tools/                        # 開發診斷工具
│   ├── status_report.py          # 統合狀態報告
│   ├── validate_config.py        # 配置驗證
│   ├── performance_diagnose.py   # 性能診斷
│   ├── inspect_schema.py         # Neo4j 結構檢查
│   └── batch_reprocess.py        # 批次重新處理
├── docs/                         # 文檔
├── logs/                         # 日誌（時間輪轉，預設保留 30 天）
├── Dockerfile                    # Docker 容器化部署
└── ecosystem.config.cjs          # PM2 配置
```

## MCP 客戶端設定

### HTTP 模式（推薦）

適用於 Claude Code、Cline 等支援 HTTP 的 MCP 客戶端：

```json
{
  "mcpServers": {
    "graphiti-memory": {
      "type": "http",
      "url": "http://localhost:8000/mcp"
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

> **注意**：SSE 模式（`--transport sse`）已不建議使用。MCP 1.x 有 session 初始化相容性問題，請改用 HTTP 模式。

## MCP 工具（11 個）

### 記憶管理

| 工具 | 說明 |
|------|------|
| `add_memory_simple` | 添加記憶到知識圖譜（支援背景處理、智慧切分） |
| `search_memory_nodes` | 搜尋記憶節點（實體），支援向量 + 關鍵字混合搜尋 |
| `search_memory_facts` | 搜尋記憶事實（關係），支援中心節點搜尋 |
| `get_episodes` | 獲取最近的記憶片段 |

### 任務管理

| 工具 | 說明 |
|------|------|
| `get_memory_task_status` | 查詢背景記憶處理任務的進度和結果 |

### 刪除與查詢

| 工具 | 說明 |
|------|------|
| `delete_episode` | 刪除記憶片段 |
| `delete_entity_edge` | 刪除實體邊（關係） |
| `get_entity_edge` | 獲取實體邊詳細資訊 |

### 系統管理

| 工具 | 說明 |
|------|------|
| `get_status` | 獲取服務狀態（Neo4j、LLM、嵌入器） |
| `test_connection` | 測試 Neo4j / LLM / 嵌入器連接 |
| `clear_graph` | 清除圖資料庫（支援按 group_id 清除） |

## 工具參數

### add_memory_simple

| 參數 | 類型 | 必填 | 預設值 | 說明 |
|------|------|------|--------|------|
| `name` | string | Y | | 記憶名稱 |
| `episode_body` | string | Y | | 記憶內容（超過 800 字元自動切分） |
| `group_id` | string | | `"default"` | 分組 ID（建議按專案隔離） |
| `source` | string | | `"text"` | 來源類型: `text` / `json` / `message` |
| `source_description` | string | | `"MCP Server"` | 來源描述 |
| `use_safe_mode` | bool | | `false` | 安全模式（跳過實體提取，快但記憶不可被搜尋） |
| `background` | bool | | `false` | 背景處理（立即返回 task_id，適合長文本） |
| `excluded_entity_types` | list | | | 排除的實體類型（減少不需要的提取量） |

> **效能提示**：
> - 短文本（<800 字元）：直接處理，通常 30-40 秒完成
> - 長文本（>800 字元）：自動切分為多段，每段獨立處理
> - 使用 `background=true` 可避免 MCP 呼叫阻塞，透過 `get_memory_task_status` 追蹤進度
> - `use_safe_mode=true` 秒速完成但記憶無法被 search 工具找到

### search_memory_nodes

| 參數 | 類型 | 必填 | 預設值 | 說明 |
|------|------|------|--------|------|
| `query` | string | Y | | 搜尋關鍵字（自然語言） |
| `max_nodes` | int | | `10` | 最大返回數量 |
| `group_ids` | list | | | 分組過濾（多個 group 聯合搜尋） |
| `entity_types` | list | | | 實體類型過濾 |

### search_memory_facts

| 參數 | 類型 | 必填 | 預設值 | 說明 |
|------|------|------|--------|------|
| `query` | string | Y | | 搜尋關鍵字 |
| `max_facts` | int | | `10` | 最大返回數量 |
| `group_ids` | list | | | 分組過濾 |
| `center_node_uuid` | string | | | 中心節點 UUID（探索特定節點的關係） |

### get_memory_task_status

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `task_id` | string | Y | 背景任務 ID（由 `add_memory_simple(background=true)` 返回） |

## Web 管理介面

HTTP 模式下訪問 `http://localhost:8000/` 即可使用。

**功能：**
- 儀表板 — 節點數、事實數、記憶片段數統計
- 實體節點 — 瀏覽、篩選、向量搜尋
- 事實關係 — 瀏覽、篩選、向量搜尋
- 記憶片段 — 瀏覽、全文搜尋、刪除
- Group 管理 — 按分組過濾、批次刪除
- 知識圖譜視覺化 — 節點關係圖形化展示
- AI 問答 — 基於知識圖譜的智能問答
- 品質分析 — 記憶品質與覆蓋度分析
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
| `/api/memory/tasks` | GET | 列出背景任務（支援狀態篩選） |
| `/api/memory/tasks/{id}` | GET | 查詢單一任務狀態 |
| `/api/nodes/{uuid}` | DELETE | 刪除節點 |
| `/api/episodes/{uuid}` | DELETE | 刪除記憶片段 |
| `/api/facts/{uuid}` | DELETE | 刪除事實 |
| `/api/groups/{group_id}` | DELETE | 刪除整個 group |

## 配置

### 環境變數（.env）

配置使用層疊機制：JSON 配置檔為基礎，環境變數覆蓋個別值。

```bash
# === 必填 ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password        # 必須修改

# === LLM 模型 ===
OLLAMA_MODEL=qwen2.5:3b             # 主模型（推薦 qwen2.5:3b）
OLLAMA_SMALL_MODEL=qwen2.5:3b       # 小模型（簡單任務用，可選不同模型）
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.1

# === 嵌入模型 ===
OLLAMA_EMBEDDING_MODEL=nomic-embed-text:v1.5
OLLAMA_EMBEDDING_DIMENSIONS=768

# === 記憶效能（可選） ===
GRAPHITI_CHUNK_THRESHOLD=800         # 觸發智慧切分的字元數閾值
GRAPHITI_MAX_CHUNK_SIZE=600          # 每段最大字元數
GRAPHITI_MAX_COROUTINES=5            # 最大並行協程數
GRAPHITI_DEFAULT_BACKGROUND=false    # 是否預設背景處理

# === 日誌 ===
LOG_FILE=logs/graphiti_mcp_server.log
LOG_LEVEL=INFO
```

> **完整環境變數列表**請參見 `.env.example`

### JSON 配置檔案

適用於需要版本控制的配置（環境變數仍可覆蓋）：

```bash
uv run python graphiti_mcp_server.py --config config.json --transport http
```

```json
{
  "ollama": {
    "model": "qwen2.5:3b",
    "small_model": "qwen2.5:3b",
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
  },
  "memory_performance": {
    "chunk_threshold": 800,
    "max_chunk_size": 600,
    "max_coroutines": 5,
    "default_background": false
  }
}
```

## PM2 背景執行

```bash
npm install -g pm2

pm2 start ecosystem.config.cjs      # 啟動
pm2 status                           # 狀態
pm2 logs graphiti-mcp-http           # 即時日誌
pm2 restart graphiti-mcp-http --update-env  # 重啟（重新載入 .env）

pm2 save && pm2 startup              # 設定開機自動啟動
```

> **提示**：修改 `.env` 後必須使用 `--update-env` 旗標重啟，否則環境變數不會更新。

## Docker 部署

```bash
docker build -t graphiti-mcp .

# 注意：Docker 容器需要能夠連接到 Neo4j 和 Ollama
# 使用 host network 最簡單
docker run -p 8000:8000 --env-file .env --network host graphiti-mcp

# 或者明確指定外部服務地址
docker run -p 8000:8000 \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --env-file .env graphiti-mcp
```

## 測試

```bash
# 執行所有測試（111 個，約 1 秒）
uv run python -m pytest tests/

# 詳細輸出
uv run python -m pytest tests/ -v

# 僅執行特定測試
uv run python -m pytest tests/test_content_preprocessor.py -v
uv run python -m pytest tests/test_unit.py -v
```

> **注意**：`test_integration_manual.py` 中的 3 個 async 測試需要安裝 `pytest-asyncio`，缺少時會顯示 Failed 但不影響其他 111 個測試。

## 故障排除

### Neo4j 連接失敗

```bash
neo4j status                              # 檢查服務狀態
cypher-shell -u neo4j -p your_password    # 確認密碼正確
curl http://localhost:7474                 # 確認 HTTP 端口
```

常見原因：
- Neo4j 未啟動
- 密碼錯誤（`.env` 中的 `NEO4J_PASSWORD`）
- 端口被佔用或防火牆阻擋

### Ollama 連接失敗

```bash
ollama serve                # 啟動 Ollama 服務
ollama list                 # 檢查已安裝模型
ollama pull qwen2.5:3b      # 安裝缺少的模型
```

常見原因：
- Ollama 未啟動（`ollama serve`）
- 模型未安裝（`ollama pull <model>`）
- GPU 記憶體不足（嘗試更小的模型）

### MCP 連線錯誤

如果出現 `Invalid request parameters` 或 `Received request before initialization was complete`：

1. 確認使用 HTTP 傳輸模式（**不要用 SSE**）
2. 確認客戶端設定為 `"type": "http"`, `"url": "http://localhost:8000/mcp"`
3. 重啟服務：`pm2 restart graphiti-mcp-http --update-env`
4. 在 Claude Code 中執行 `/mcp` 重新連接

### 記憶添加速度慢

- 檢查使用的模型大小（`qwen2.5:3b` 比 `7b` 快 5-10 倍）
- 使用 `background=true` 避免阻塞
- 調低 `GRAPHITI_CHUNK_THRESHOLD` 讓長文本更早切分
- 確認 Ollama 有使用 GPU 加速（`ollama ps` 檢查）

### PM2 問題

```bash
pm2 status                                        # 檢查狀態
pm2 logs graphiti-mcp-http --err --lines 50        # 錯誤日誌
lsof -i :8000                                     # 檢查端口佔用
pm2 delete graphiti-mcp-http && pm2 start ecosystem.config.cjs  # 完全重啟
```

## 開發診斷工具

```bash
uv run python tools/status_report.py           # 統合狀態報告（Neo4j + Ollama + 配置）
uv run python tools/validate_config.py         # 驗證 .env 和配置完整性
uv run python tools/performance_diagnose.py    # LLM 效能診斷
uv run python tools/inspect_schema.py          # Neo4j 索引和約束檢查
```

## 文檔

- [使用工具的指令](docs/使用工具的指令.md) — MCP 工具使用指南與最佳實踐
- [Graphiti Memory Rules](docs/graphiti-memory-rules.md) — 記憶規則說明

## 授權

MIT License
