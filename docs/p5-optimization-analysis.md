# P5 — 深度優化分析報告

> **分析日期**: 2026-02-28
> **分析範圍**: 全部核心模組、前端、測試、工具、配置與部署
> **排除項目**: 已在 P0–P4 中完成的所有優化項目
> **方法**: 逐檔程式碼審查 + 架構分析

---

## 目錄

- [P0 — 緊急修復（影響正確性與安全性）](#p0--緊急修復影響正確性與安全性)
- [P1 — 高優先級（效能與可靠性）](#p1--高優先級效能與可靠性)
- [P2 — 中優先級（健壯性與可維護性）](#p2--中優先級健壯性與可維護性)
- [P3 — 低優先級（功能增強）](#p3--低優先級功能增強)
- [總結](#總結)
- [不做的項目](#不做的項目)

---

## P0 — 緊急修復（影響正確性與安全性）

### P5-01: 並發安全 — `graphiti_instance` 初始化競態條件

| 屬性 | 內容 |
|------|------|
| **涉及檔案** | `graphiti_mcp_server.py:146-203` |
| **影響範圍** | 伺服器啟動後首批並發請求 |

**問題描述**：
`initialize_graphiti()` 使用 `global graphiti_instance` 做快取，但沒有任何鎖保護。當多個並發 MCP 工具呼叫同時到達且 `graphiti_instance is None` 時，可能同時建立多個 Graphiti 實例和多個 Neo4j driver 連線，造成資源浪費和潛在的連線池衝突。

**建議方案**：
使用 `asyncio.Lock` 保護初始化過程（double-check locking）：

```python
_init_lock = asyncio.Lock()

async def initialize_graphiti():
    global graphiti_instance
    if graphiti_instance is not None:
        return graphiti_instance
    async with _init_lock:
        if graphiti_instance is not None:  # double-check
            return graphiti_instance
        # ... 初始化邏輯
```

---

### P5-02: `clear_graph` 後索引遺失

| 屬性 | 內容 |
|------|------|
| **涉及檔案** | `graphiti_mcp_server.py:752-785` |
| **影響範圍** | `clear_graph` 後所有向量搜尋可能失敗 |

**問題描述**：
呼叫 `clear_graph` 後將 `graphiti_instance` 設為 `None`，下次使用會重新初始化。但 `await graphiti.clear()` 會清除所有資料（包括索引），而 `initialize_graphiti()` 中沒有呼叫 `build_indices_and_constraints()`，導致清除後的知識圖譜缺少必要索引。

**建議方案**：
在 `initialize_graphiti()` 中加入索引重建：

```python
graphiti_instance = Graphiti(...)
await graphiti_instance.build_indices_and_constraints()
```

或在 `clear_graph` 後顯式重建索引。

---

### P5-03: `_RateLimiter` 記憶體洩漏

| 屬性 | 內容 |
|------|------|
| **涉及檔案** | `src/web_api.py:38-55` |
| **影響範圍** | 長期運行的生產伺服器記憶體持續增長 |

**問題描述**：
`_hits` 字典只在 `is_allowed` 被呼叫時清理**當前 IP** 的過期記錄，但從未清理不再出現的 IP 條目。長時間運行下，如果有大量不同 IP 訪問搜尋端點，`_hits` 字典會無限增長。

**建議方案**：
加入定期清理機制——每 N 次呼叫時掃描並移除所有過期 IP 條目，或限制 `_hits` 最大 key 數：

```python
def is_allowed(self, ip: str) -> bool:
    now = time.monotonic()
    # 每 100 次呼叫全域清理一次
    self._call_count += 1
    if self._call_count % 100 == 0:
        self._hits = {
            k: [t for t in v if now - t < self.window]
            for k, v in self._hits.items()
            if any(now - t < self.window for t in v)
        }
    # ... 原有邏輯
```

---

### P5-04: Web API 刪除端點 Cypher 參數綁定風險

| 屬性 | 內容 |
|------|------|
| **涉及檔案** | `src/web_api.py:342-368` |
| **影響範圍** | Web UI 刪除操作可能未實際生效 |

**問題描述**：
`api_delete_episode` 和 `api_delete_fact` 中，Cypher 查詢使用 `$uuid` 作為參數佔位符，但 `execute_query()` 傳入的關鍵字參數是 `uuid_=uuid`（帶底線）。這依賴 Neo4j Python driver 對 `_` 後綴的特殊處理行為，不同版本可能行為不一致。

**建議方案**：
統一使用不帶底線的參數名，或改用 `parameters` 字典：

```python
records, _, _ = await graphiti.driver.execute_query(
    query, parameters_={"uuid": uuid}
)
```

---

## P1 — 高優先級（效能與可靠性）

### P5-05: `aiohttp.ClientSession` 每次請求建立新連線

| 屬性 | 內容 |
|------|------|
| **涉及檔案** | `src/ollama_graphiti_client.py:249`, `src/ollama_embedder.py:129,229` |
| **影響範圍** | 每次嵌入或 LLM 請求額外 5-20ms TCP 握手開銷 |

**問題描述**：
`_make_request()` 和 `_create_embeddings()` 每次呼叫都 `async with aiohttp.ClientSession() as session`，建立新的 TCP 連接。根據 aiohttp 官方文檔，應該重用 session 以利用 HTTP keep-alive 和連線池。

**建議方案**：
在 `__init__` 中建立 session 實例，在物件生命週期內重用：

```python
class OptimizedOllamaClient:
    def __init__(self, ...):
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(...)
        return self._session
```

---

### P5-06: 隊列系統死代碼

| 屬性 | 內容 |
|------|------|
| **涉及檔案** | `graphiti_mcp_server.py:77-78, 109-143` |
| **影響範圍** | 程式碼可讀性、維護成本 |

**問題描述**：
`episode_queues`、`queue_workers` 全域變數已定義，`process_episode_queue()` 函數已實作，但從未被任何地方呼叫。`_add_memory_full_mode` 直接同步呼叫 `graphiti.add_episode()`，完全繞過隊列。

**建議方案**：
- **方案 A**: 移除死代碼（`episode_queues`、`queue_workers`、`process_episode_queue`）以降低認知負擔
- **方案 B**: 正式啟用隊列機制，讓記憶添加可以非同步背景處理

---

### P5-07: `get_status` 串行檢測效率低

| 屬性 | 內容 |
|------|------|
| **涉及檔案** | `graphiti_mcp_server.py:905-947` |
| **影響範圍** | `get_status` 響應時間為三個組件測試時間之和 |

**問題描述**：
`get_status` 的 `_check_database_status`、`_check_llm_status`、`_check_embedder_status` 是**串行**呼叫，而功能類似的 `test_connection` 已使用 `asyncio.gather` **並行**測試。

**建議方案**：
```python
db_status, llm_status, emb_status = await asyncio.gather(
    _check_database_status(),
    _check_llm_status(),
    _check_embedder_status(),
)
```

---

### P5-08: Neo4j 連線無 graceful shutdown

| 屬性 | 內容 |
|------|------|
| **涉及檔案** | `graphiti_mcp_server.py` |
| **影響範圍** | Neo4j 連線池耗盡（頻繁重啟時） |

**問題描述**：
程式中沒有任何地方呼叫 `graphiti.driver.close()`。當伺服器透過 PM2 重啟或 `KeyboardInterrupt` 停止時，Neo4j driver 連線未正確關閉，殘留連線直到超時。

**建議方案**：
在 `main()` 的 `KeyboardInterrupt` 處理中加入清理邏輯：

```python
except KeyboardInterrupt:
    if graphiti_instance:
        asyncio.run(graphiti_instance.driver.close())
    logging.getLogger("main").info("服務器已停止")
```

---

### P5-09: `/health` 端點不實際檢查連線狀態

| 屬性 | 內容 |
|------|------|
| **涉及檔案** | `graphiti_mcp_server.py:1021-1026` |
| **影響範圍** | 負載均衡器和 PM2 無法正確偵測服務降級 |

**問題描述**：
`/health` 端點只返回固定的 `"status": "healthy"`，不實際檢查 Neo4j 或 Ollama 連線狀態。即使所有後端服務都斷線，健康檢查仍返回 healthy。

**建議方案**：
提供兩個層級的健康檢查：
- `/health`（輕量 liveness）— 僅確認程序存活
- `/health/ready`（深度 readiness）— 實際檢查 Neo4j 連線

---

### P5-10: 配置不支援 JSON + 環境變數層疊

| 屬性 | 內容 |
|------|------|
| **涉及檔案** | `src/config.py:494-514` |
| **影響範圍** | Docker/K8s 部署場景的配置靈活性 |

**問題描述**：
`load_config()` 的邏輯是：有 JSON 就全用 JSON，沒有就用環境變數。但 Docker 場景中，用戶通常想用 JSON 做基礎配置，再用環境變數覆蓋部分值（如密碼、端口）。目前不支援這種層疊。

**建議方案**：
改為先載入 JSON 基礎，再用環境變數覆蓋非空值：

```python
def load_config(config_path=None):
    config = GraphitiConfig.from_file(config_path) if config_path else GraphitiConfig()
    config.apply_env_overrides()  # 新方法：只覆蓋有設定的環境變數
    return config
```

---

## P2 — 中優先級（健壯性與可維護性）

### P5-11: `_create_llm_client` 仍使用 `print()` 而非 `logging`

| 屬性 | 內容 |
|------|------|
| **涉及檔案** | `graphiti_mcp_server.py:223-227` |
| **影響範圍** | 生產環境無法透過日誌追蹤 LLM 初始化狀態 |

**問題描述**：
`_create_llm_client()` 使用 `print()` 輸出初始化結果，但此時 `logger` 已初始化完成。`print()` 的輸出不會被寫入日誌檔案。

**建議方案**：
改用 `logging.getLogger("graphiti").info/warning(...)`。

---

### P5-12: 嵌入器 fallback 隨機向量污染搜尋結果

| 屬性 | 內容 |
|------|------|
| **涉及檔案** | `src/ollama_embedder.py:352-362` |
| **影響範圍** | 搜尋結果準確性隨失敗次數累積而下降 |

**問題描述**：
嵌入請求失敗時，`_create_fallback_embedding()` 返回歸一化的隨機向量。這個隨機向量被存入 Neo4j，後續向量搜尋時會隨機匹配到不相關的結果。

**建議方案**：
- 失敗時拋出異常而非靜默返回隨機向量，讓上層決定如何處理
- 或標記使用 fallback 向量的節點，搜尋時排除

---

### P5-13: 前端 XSS 防護不完整 — UUID 注入

| 屬性 | 內容 |
|------|------|
| **涉及檔案** | `web/js/components.js` 多處 |
| **影響範圍** | 潛在的 XSS 攻擊向量（低風險但應防禦） |

**問題描述**：
模板字串中直接插入 `node.uuid`、`ep.uuid` 到 `onclick` 屬性中（如 `onclick="App.deleteEpisode('${ep.uuid}')"`），沒有經過跳脫。如果資料庫中的 UUID 被惡意篡改含有單引號，就能注入 JavaScript。

**建議方案**：
- 對 UUID 使用正則驗證（只允許 hex 和 `-`）
- 或改用 `data-uuid` 屬性 + event delegation 取代 inline `onclick`

---

### P5-14: 日誌檔案雙日期命名問題

| 屬性 | 內容 |
|------|------|
| **涉及檔案** | `src/logging_setup.py:154-181` |
| **影響範圍** | 日誌檔案命名混亂，不便管理 |

**問題描述**：
`_create_time_rotating_handler` 在初始檔案名稱中加入今天日期（`app_2026-02-28.log`），但 `TimedRotatingFileHandler` 輪轉時又加日期後綴，導致出現 `app_2026-02-28_2026-02-28.log` 的雙日期格式。

**建議方案**：
不在初始檔名中加日期，讓 `TimedRotatingFileHandler` 自行管理命名。

---

### P5-15: 匯出功能 `limit: 9999` vs 後端上限 100

| 屬性 | 內容 |
|------|------|
| **涉及檔案** | `web/js/api.js:78-85`, `src/web_api.py` |
| **影響範圍** | 匯出資料不完整，用戶誤以為已全部匯出 |

**問題描述**：
前端 `exportData` 使用 `limit: 9999` 一次拉取所有資料，但後端 API 限制 `limit` 最大為 `100`（`min(int(...), 100)`）。實際只能匯出 100 筆。

**建議方案**：
- 前端改用迴圈分頁拉取直到資料為空
- 或後端提供專用的 `/api/export` 端點不受分頁限制

---

### P5-16: 配置驗證只返回 `bool`，不返回具體錯誤

| 屬性 | 內容 |
|------|------|
| **涉及檔案** | `src/config.py` 各 `validate()` 方法 |
| **影響範圍** | 部署診斷效率 |

**問題描述**：
所有 `validate()` 方法只返回 `True/False`，無法告訴用戶**哪個欄位**有問題、**期望值**是什麼。URL 格式也未驗證。

**建議方案**：
返回錯誤列表而非 `bool`：

```python
def validate(self) -> list[str]:
    errors = []
    if not self.model:
        errors.append("ollama.model 不能為空")
    if not self.base_url.startswith(("http://", "https://")):
        errors.append(f"ollama.base_url 格式無效: {self.base_url}")
    return errors
```

---

### P5-17: Web API 缺少 CORS 配置

| 屬性 | 內容 |
|------|------|
| **涉及檔案** | `src/web_api.py`, `src/config.py` |
| **影響範圍** | 跨域整合場景 |

**問題描述**：
`ServerConfig` 中已定義 `cors_origins` 設定但從未使用。如果未來前端獨立部署（如開發時用 vite dev server），API 呼叫會被瀏覽器阻擋。

**建議方案**：
加入 Starlette `CORSMiddleware`，使用配置中的 `cors_origins`。

---

## P3 — 低優先級（功能增強）

### P5-18: 缺少 Node 刪除功能

| 屬性 | 內容 |
|------|------|
| **涉及檔案** | `src/web_api.py`, `graphiti_mcp_server.py` |
| **影響範圍** | 知識圖譜資料修正能力 |

**問題描述**：
Web API 和 MCP 工具都只能刪除 Episode 和 Fact（邊），但無法刪除 Entity 節點。如果實體提取產生了錯誤的節點，用戶無法透過介面移除。

**建議方案**：
新增 `DELETE /api/nodes/{uuid}` 端點和 `delete_entity_node` MCP 工具，刪除時級聯清理相關的邊。

---

### P5-19: 前端缺少 Group 刪除 UI

| 屬性 | 內容 |
|------|------|
| **涉及檔案** | `web/js/app.js`, `web/js/components.js` |
| **影響範圍** | 用戶無法通過 Web UI 清理整個群組 |

**問題描述**：
後端已有 `DELETE /api/groups/{group_id}` 端點，前端 `API.deleteGroup()` 也已封裝，但前端 UI 中沒有任何按鈕或入口觸發群組刪除。

**建議方案**：
在 Group 下拉選單旁加入群組管理功能（刪除按鈕 + 確認對話框）。

---

### P5-20: `.env.example` 含未使用的環境變數

| 屬性 | 內容 |
|------|------|
| **涉及檔案** | `.env.example` |
| **影響範圍** | 新用戶部署時的困惑 |

**問題描述**：
`.env.example` 定義了 `MODEL_NAME`、`SMALL_MODEL_NAME`、`OPENAI_API_KEY`、`OPENAI_BASE_URL`，但 `config.py` 實際讀取的是 `OLLAMA_MODEL`。這些都是歷史遺留，會誤導用戶。

**建議方案**：
清理 `.env.example`，只保留實際被 `config.py` 讀取的環境變數，並加上註解說明。

---

### P5-21: `pyproject.toml` 可能含不必要的依賴

| 屬性 | 內容 |
|------|------|
| **涉及檔案** | `pyproject.toml` |
| **影響範圍** | 安裝時間增加、依賴體積增大 |

**問題描述**：
依賴列表包含 `openai>=2.14.0` 和 `azure-identity>=1.25.1`，但本專案是純 Ollama 方案。可能是 `graphiti-core` 的間接依賴。

**建議方案**：
確認是否為 `graphiti-core` 的必要間接依賴。如果是，移除頂層宣告讓 pip 自動解析。

---

### P5-22: 源碼模組內含測試用 `main()` 函數

| 屬性 | 內容 |
|------|------|
| **涉及檔案** | `src/ollama_graphiti_client.py:699-810`, `src/ollama_embedder.py:370-455`, `src/safe_memory_add.py:112-210` |
| **影響範圍** | 程式碼組織和可維護性 |

**問題描述**：
多個源碼模組底部有完整的 `main()` 測試函數和 `if __name__ == "__main__"` 入口。在正式模組中不適當。

**建議方案**：
將這些測試函數移到 `tests/` 目錄，作為集成測試。

---

### P5-23: PM2 進程名稱已過時

| 屬性 | 內容 |
|------|------|
| **涉及檔案** | `ecosystem.config.cjs` |
| **影響範圍** | 運維人員理解 |

**問題描述**：
PM2 進程名稱是 `graphiti-mcp-sse`，但實際傳輸模式已改為 `--transport http`。

**建議方案**：
更名為 `graphiti-mcp-http` 或 `graphiti-mcp-server`。

---

### P5-24: 前端缺少重試按鈕和自動重連

| 屬性 | 內容 |
|------|------|
| **涉及檔案** | `web/js/app.js:110-135` |
| **影響範圍** | 使用者體驗 |

**問題描述**：
`_renderCurrentPage` 捕獲錯誤後只顯示靜態錯誤訊息，不提供重試按鈕。伺服器暫時不可用時，用戶必須手動重新整理。

**建議方案**：
在錯誤狀態中加入「重試」按鈕；可選加入心跳檢測，伺服器恢復時自動重新載入。

---

### P5-25: 缺少 Dockerfile

| 屬性 | 內容 |
|------|------|
| **涉及檔案** | 專案根目錄 |
| **影響範圍** | 部署彈性 |

**問題描述**：
專案只有 PM2 部署配置，沒有 Dockerfile。雲端或伺服器部署需要容器化。

**建議方案**：
建立多階段 Dockerfile：

```dockerfile
FROM python:3.11-slim AS base
RUN pip install uv
COPY . /app
WORKDIR /app
RUN uv sync --no-dev
CMD ["uv", "run", "python", "graphiti_mcp_server.py", "--transport", "http"]
```

---

## 總結

| 優先級 | 數量 | 重點領域 |
|--------|------|----------|
| **P0** | 4 項 | 並發安全、索引遺失、記憶體洩漏、參數綁定 |
| **P1** | 6 項 | Session 重用、死代碼、健康檢查、graceful shutdown、配置層疊 |
| **P2** | 7 項 | print→logger、隨機向量、XSS、日誌命名、匯出上限、CORS |
| **P3** | 8 項 | Node 刪除、Group UI、依賴清理、容器化、前端重連 |
| **合計** | **25 項** | |

---

## 不做的項目（及原因）

| 項目 | 原因 |
|------|------|
| Neo4j 連線池參數透傳 | 上游 `Neo4jDriver` 不接受這些參數（P4 已確認） |
| 全域變數重構 | 風險高、破壞面大、收益有限（P3 已評估） |
| 動態配置重載 | 需要大量基礎設施，暫不需要 |
| 資料庫備份/還原 | Neo4j 有原生備份工具（`neo4j-admin dump`） |
| API 版本控制 | 目前無多版本需求，過早設計 |
| 行動端觸控優化 | Web UI 主要為桌面管理場景，非必需 |

---

## 建議實施順序

1. **Phase 1** — P0 全部（4 項）：並發鎖、索引重建、記憶體清理、參數綁定
2. **Phase 2** — P1 高影響（P5-05, P5-07, P5-08, P5-09）：Session 重用、並行檢測、shutdown、健康檢查
3. **Phase 3** — P1 低影響 + P2 高影響（P5-06, P5-10, P5-11, P5-12, P5-15）
4. **Phase 4** — P2 剩餘 + P3 選擇性實施
