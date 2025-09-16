# Graphiti + Ollama MCP 服務器

基於 **Graphiti 知識圖譜** 和 **Ollama 本地 LLM** 的 Model Context Protocol (MCP) 服務器，為 AI 助手提供持久記憶功能。

## ✨ 特色功能

🧠 **持久記憶** - 透過 Neo4j 知識圖譜儲存跨會話記憶
🦙 **本地 LLM** - 使用 Ollama 進行實體提取，無需 API 金鑰
🔍 **語義搜索** - 基於嵌入向量的智能搜索功能
👥 **多租戶** - 支援群組隔離的記憶管理
⚡ **實時同步** - MCP 協議確保即時資料同步
🔧 **簡單部署** - 一鍵啟動，無複雜配置

## 🏗️ 系統架構

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Claude Code   │◄──►│  MCP 服務器       │◄──►│   Neo4j 圖庫    │
│                 │    │  (FastMCP)       │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌──────────────────┐    ┌─────────────────┐
                    │  Ollama Client   │◄──►│  Ollama 服務    │
                    │  (實體提取)       │    │  qwen2.5:7b    │
                    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Ollama Embedder │
                    │  nomic-embed-text│
                    └──────────────────┘
```

## 🚀 快速開始

### 1. 前置需求

```bash
# 確認 Python 版本 (需要 3.10+)
python --version

# 安裝 uv (Python 套件管理器)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 確認 Neo4j 正在運行 (應該已經在 localhost:7687)
# 檢查連接
cypher-shell -u neo4j -p YOUR_PASSWORD "RETURN 'Neo4j is running' as status"

# 啟動 Ollama 並安裝模型
ollama serve
ollama pull qwen2.5:7b
ollama pull nomic-embed-text:v1.5
```

### 2. 環境配置

```bash
# 複製環境設定檔
cp .env.example .env

# .env 檔案已經預設配置，包含：
# NEO4J_PASSWORD=YOUR_PASSWORD (請設定你的 Neo4j 密碼)
# MODEL_NAME=qwen2.5:7b (Ollama 模型)
# 請根據你的實際設定修改密碼
```

### 3. 安裝與啟動

```bash
# 安裝依賴
uv sync

# 啟動 MCP 服務器 (STDIO 模式，用於 Claude Desktop)
uv run graphiti_mcp_server.py --transport stdio

# 或啟動 SSE 模式 (用於 Cursor 等)
uv run graphiti_mcp_server.py --transport sse --host 0.0.0.0 --port 8000
```

## 📁 專案結構

```
graphiti/
├── 📄 graphiti_mcp_server.py      # 主要 MCP 服務器
├── 🧲 ollama_embedder.py          # 自定義 Ollama 嵌入器
├── 🤖 ollama_graphiti_client.py   # 優化的 Ollama 客戶端
├── ⚙️ .env.example                # 環境配置範本
├── 📋 pyproject.toml              # Python 專案配置
├── 📚 docs/                       # 文檔
│   ├── CLAUDE.md                   # 開發記錄
│   └── USAGE.md                    # 使用指南
├── 🧪 tests/                      # 測試文件
│   ├── test_simple_memory.py       # 基本功能測試
│   ├── test_mcp_complete.py        # 完整功能測試
│   ├── test_embedding.py           # 嵌入功能測試
│   └── ...                         # 其他測試文件
└── 🔧 tools/                      # 工具腳本
    ├── debug_ollama.py             # Ollama 調試工具
    └── performance_diagnose.py     # 性能診斷工具
```

詳細使用說明請參閱 [docs/USAGE.md](docs/USAGE.md)

## 🔧 MCP 客戶端配置

### Claude Desktop 配置

在 `~/.claude/config.json` 中添加：

```json
{
  "mcpServers": {
    "graphiti-memory": {
      "transport": "stdio",
      "command": "/Users/你的用戶名/.local/bin/uv",
      "args": [
        "run",
        "--isolated",
        "--project",
        ".",
        "graphiti_mcp_server.py",
        "--transport",
        "stdio"
      ],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "YOUR_PASSWORD"
      }
    }
  }
}
```

### Cursor 配置

在 Cursor 設定中添加：

```json
{
  "mcpServers": {
    "graphiti-memory": {
      "transport": "sse",
      "url": "http://localhost:8000/sse"
    }
  }
}
```

## 🛠️ 可用工具

| 工具名稱 | 功能描述 | 使用範例 |
|---------|---------|----------|
| `add_memory_simple` | 添加記憶到知識圖譜 | 儲存會話內容、學習筆記 |
| `search_memory_nodes` | 搜索實體節點 | 查找特定人物、概念 |
| `search_memory_facts` | 搜索關係事實 | 查找實體間關係 |
| `get_episodes` | 獲取記憶段 | 回顧歷史對話 |
| `clear_graph` | 清空知識圖譜 | 重置記憶系統 |
| `test_connection` | 測試連接狀態 | 診斷系統問題 |

## 📊 使用範例

### 添加記憶
```
使用 add_memory_simple:
- name: "專案會議記錄"
- episode_body: "今天討論了新功能的實作方案，決定使用 React + Node.js 架構"
- group_id: "project_alpha"
```

### 搜索記憶
```
使用 search_memory_nodes:
- query: "React"
- group_ids: ["project_alpha"]
→ 找到相關的技術決策和討論記錄
```

### 查找關係
```
使用 search_memory_facts:
- query: "使用"
→ 找到 "React 使用於前端開發" 等關係事實
```

## ⚙️ 環境變數說明

### Neo4j 配置
```env
NEO4J_URI=bolt://localhost:7687          # Neo4j 連接 URI
NEO4J_USER=neo4j                         # Neo4j 使用者名稱
NEO4J_PASSWORD=YOUR_PASSWORD             # Neo4j 密碼 (請設定你的密碼)
```

### Ollama 配置
```env
MODEL_NAME=qwen2.5:7b                   # 主要 LLM 模型
EMBEDDER_MODEL_NAME=nomic-embed-text:v1.5 # 嵌入模型
OLLAMA_BASE_URL=http://localhost:11434   # Ollama 服務地址
LLM_TEMPERATURE=0.1                      # LLM 溫度參數
```

### 系統配置
```env
GROUP_ID=your_namespace                  # 預設群組 ID
SEMAPHORE_LIMIT=3                        # 並發限制
GRAPHITI_TELEMETRY_ENABLED=false         # 停用遙測
```

## 🔍 故障排除

### 常見問題

**Q: 連接失敗怎麼辦？**
```bash
# 檢查 Neo4j 是否運行
docker ps | grep neo4j

# 檢查 Ollama 是否運行
curl http://localhost:11434/api/tags
```

**Q: 搜索沒有結果？**
```bash
# 確認資料已儲存
cypher-shell -u neo4j -p YOUR_PASSWORD "MATCH (n) RETURN count(n)"

# 檢查節點標籤
cypher-shell -u neo4j -p YOUR_PASSWORD "MATCH (n) RETURN DISTINCT labels(n)"
```

**Q: Pydantic 驗證錯誤？**
- 檢查 `ollama_graphiti_client.py` 中的 ID 解析邏輯
- 確認 Ollama 模型回應格式正確

### 除錯模式

```bash
# 啟用除錯模式
export DEBUG=1
uv run graphiti_mcp_server.py --transport sse

# 檢視詳細日誌
tail -f /tmp/graphiti_debug.log
```

## 🎯 最佳實踐

### 記憶組織
- 使用有意義的 `group_id` 進行分類
- 為不同專案或主題建立獨立群組
- 定期清理無用的記憶資料

### 效能優化
- 調整 `SEMAPHORE_LIMIT` 控制並發數
- 使用適合的 LLM 溫度參數
- 定期重建 Neo4j 索引

### 安全建議
- 設定強密碼保護 Neo4j
- 避免在記憶中儲存敏感資訊
- 定期備份知識圖譜資料

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

## 📄 授權

本專案採用與 Graphiti 主專案相同的授權條款。

---

**💡 提示**: 這是基於 [Graphiti](https://github.com/getzep/graphiti) 的本地化實現，專為中文使用者和本地 LLM 環境優化。