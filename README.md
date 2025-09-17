# Graphiti MCP Server

🇹🇼 **本地化知識圖譜記憶服務** - 整合 Ollama 本地 LLM 與 Graphiti 的企業級 MCP 服務器

## 🌟 特色功能

- 🧠 **智能記憶管理** - 使用知識圖譜儲存和檢索複雜的記憶關係
- 🔍 **語意搜尋** - 基於向量嵌入的智能搜尋，理解語意而非僅文字匹配
- 🏠 **完全本地化** - 無需外部 API，使用 Ollama 本地 LLM 和嵌入模型
- 🇹🇼 **繁體中文** - 完整的中文界面和回應，專為台灣用戶設計
- 🏗️ **企業級架構** - 結構化配置、異常處理、日誌系統和監控

## 🏗️ 專案結構

```
graphiti/
├── src/                          # 核心模組
│   ├── config.py                 # 配置管理系統
│   ├── exceptions.py             # 結構化異常處理
│   ├── logging_setup.py          # 日誌記錄系統
│   ├── ollama_embedder.py        # Ollama 嵌入器
│   └── ollama_graphiti_client.py # Ollama LLM 客戶端
├── tools/                        # 實用工具
├── docs/                         # 文檔
│   └── 使用工具的指令.md          # 工具使用指令和最佳實踐
├── logs/                         # 日誌檔案
└── graphiti_mcp_server.py        # 主服務器
```

## 🚀 快速啟動

> **📖 重要提醒：** 設定完成後，請務必閱讀 [使用工具的指令](docs/使用工具的指令.md) 以了解如何正確使用 Graphiti MCP 工具！

### 1. 系統需求

- **Python**: 3.11+
- **Neo4j**: 4.0+ (bolt://localhost:7687)
- **Ollama**: 本地運行 (http://localhost:11434)
- **必需模型**:
  - `qwen2.5:7b` (LLM)
  - `nomic-embed-text:v1.5` (嵌入)

### 💻 硬體效能建議

選擇合適的模型搭配您的電腦效能，獲得最佳體驗：

#### M1/M2 Mac (8-16GB RAM)
```bash
# 🏆 最佳推薦組合 - 速度與品質完美平衡
ollama pull qwen2.5:3b        # LLM (0.72秒回應，品質很好)
ollama pull nomic-embed-text:v1.5

# ⚡ 極速組合 - 優先回應速度
ollama pull qwen2.5:0.5b      # LLM (0.68秒回應，基本品質)
ollama pull nomic-embed-text:v1.5

# 💎 高品質組合 - 專業用途
ollama pull qwen2.5:7b        # LLM (1.50秒回應，優秀品質)
ollama pull nomic-embed-text:v1.5
```

#### Intel/AMD 桌機 (16GB+ RAM)
```bash
# 平衡組合
ollama pull qwen2.5:3b        # 或 llama3.2:3b
ollama pull nomic-embed-text:v1.5

# 高性能組合 (32GB+ RAM)
ollama pull qwen2.5:7b        # 原建議模型
ollama pull nomic-embed-text:v1.5
```

#### 效能比較表
| 模型 | 大小 | GPU記憶體 | 回應時間* | 回應品質 | 推薦指數 |
|------|------|----------|----------|----------|----------|
| **qwen2.5:0.5b** | 397 MB | 1.3 GB | 0.68秒 | 基本 | ⭐⭐⭐⭐⭐ |
| **qwen2.5:1.5b** | 986 MB | 1.9 GB | 0.71秒 | 良好 | ⭐⭐⭐⭐⭐ |
| **qwen2.5:3b** | 1.9 GB | 2.0 GB | 0.72秒 | 很好 | ⭐⭐⭐⭐⭐ |
| **qwen2.5:7b** | 4.7 GB | 4.0+ GB | 1.50秒 | 優秀 | ⭐⭐⭐⭐ |
| llama3.2:1b | 1.3 GB | 1.5 GB | 1.03秒 | 中等 | ⭐⭐⭐ |
| gemma3:1b | 815 MB | 1.9 GB | 0.87秒 | 良好 | ⭐⭐⭐⭐ |
| deepseek-r1:1.5b | 1.1 GB | 2.0 GB | 2.31秒† | 分析型 | ⭐⭐⭐ |

> **註：** *實測於 M2 MacBook Pro，† R1模型包含思考過程較慢

> **⚠️ 重要提醒**：以上數據依個人電腦的測試而有所不同，建議先做好測試再選擇模組。

#### 📊 性能測試指南
在選擇模型前，建議先測試各模型在您硬體上的實際表現：

```bash
# 測試各模型回應時間
time ollama run qwen2.5:0.5b "你好，請簡短回應"
time ollama run qwen2.5:1.5b "你好，請簡短回應"
time ollama run qwen2.5:3b "你好，請簡短回應"

# 檢查系統資源使用
top -l 1 -n 0 | grep -E "CPU|Memory"
ollama ps  # 查看模型記憶體使用量
```

#### 切換模型設定
在配置檔案中修改模型名稱：
```json
{
  "ollama": {
    "model": "qwen2.5:1.5b",  // 改為適合的模型
    "base_url": "http://localhost:11434"
  }
}
```

### 2. 安裝 Python 和 uv

#### Python 3.11+ 安裝

**macOS:**
```bash
# 使用 Homebrew 安裝 (推薦)
brew install python@3.11

# 或使用 pyenv 管理多版本
brew install pyenv
pyenv install 3.11.0
pyenv global 3.11.0

# 驗證安裝
python3 --version  # 應顯示 3.11.x
```

**Windows:**
```powershell
# 使用 Chocolatey 安裝
choco install python --version=3.11.0

# 或使用 Scoop 安裝
scoop install python

# 或從官網下載安裝
# https://www.python.org/downloads/windows/

# 驗證安裝
python --version  # 應顯示 3.11.x
```

**Linux (Ubuntu/Debian):**
```bash
# 更新套件列表
sudo apt update

# 安裝 Python 3.11
sudo apt install python3.11 python3.11-pip python3.11-venv

# 設定預設版本
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# 驗證安裝
python3 --version  # 應顯示 3.11.x
```

#### uv 套件管理器安裝

**macOS/Linux:**
```bash
# 使用官方安裝腳本 (推薦)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 Homebrew (macOS)
brew install uv

# 或使用 pip 安裝
pip install uv

# 驗證安裝
uv --version
```

**Windows:**
```powershell
# 使用 PowerShell 安裝腳本
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 或使用 Scoop
scoop install uv

# 或使用 pip 安裝
pip install uv

# 驗證安裝
uv --version
```

### 3. 安裝專案依賴

```bash
# 克隆專案
git clone https://github.com/weimi89/graphiti-ollama-fusion.git
cd graphiti-mcp-server

# 使用 uv 安裝依賴
uv sync

# 如果沒有 uv，也可以使用傳統方式
# python -m venv .venv
# source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate     # Windows
# pip install -r requirements.txt
```

#### 安裝其他必需服務

**Neo4j 圖資料庫:**
```bash
# macOS (使用 Homebrew)
brew install neo4j
brew services start neo4j

# Windows (使用 Chocolatey)
choco install neo4j-community

# Linux (Ubuntu/Debian)
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable 4.0' | sudo tee /etc/apt/sources.list.d/neo4j.list
sudo apt update && sudo apt install neo4j

# Docker 方式 (跨平台)
docker run -d -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password \
  neo4j:5

# 驗證安裝 - 瀏覽器開啟 http://localhost:7474
```

**Ollama 本地 LLM:**
```bash
# macOS
brew install ollama
ollama serve  # 啟動服務

# Linux
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve  # 啟動服務

# Windows - 從官網下載
# https://ollama.ai/download/windows

# 下載必需模型
ollama pull qwen2.5:7b
ollama pull nomic-embed-text:v1.5

# 驗證安裝
ollama list  # 檢查已安裝的模型
```

### 4. 配置環境

```bash
# 複製環境變數範例
cp .env.example .env

# 編輯配置 (設定 Neo4j 密碼等)
nano .env
```

### 5. 啟動服務

```bash
# STDIO 模式 (Claude Desktop 使用)
uv run python graphiti_mcp_server.py --transport stdio

# SSE 模式 (網頁客戶端使用)
uv run python graphiti_mcp_server.py --transport sse --port 8000

# 使用自定義配置
uv run python graphiti_mcp_server.py --config your_config.json --transport sse
```

## 🔗 MCP 客戶端設定

### 模式選擇

本服務器支援兩種運行模式：

| 模式 | 適用場景 | 優點 | 缺點 |
|------|----------|------|------|
| **STDIO** | Claude Desktop, MCP Inspector | 直接整合、穩定 | 僅限本地使用 |
| **SSE** | 網頁應用、遠端客戶端 | 網路存取、靈活部署 | 需要網路配置 |

---

### 模式一：STDIO 模式（適用於 Claude Desktop CLI）

> **⚠️ 重要：** STDIO 模式僅適用於 **Claude Desktop CLI** 版本，不適用於 IDE 整合。

#### Claude Desktop CLI 設定

**配置檔案位置：**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

**完整配置範例：**
```json
{
  "mcpServers": {
    "graphiti-memory": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/your/graphiti",
        "python",
        "graphiti_mcp_server.py",
        "--transport",
        "stdio"
      ],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "your_password",
        "NEO4J_DATABASE": "graphiti-db",
        "OPENAI_API_KEY": "ollama",
        "OPENAI_BASE_URL": "http://localhost:11434/v1",
        "MODEL_NAME": "qwen2.5:7b",
        "EMBEDDER_MODEL_NAME": "nomic-embed-text:v1.5",
        "GROUP_ID": "claude_desktop",
        "SEMAPHORE_LIMIT": "3",
        "LOG_FILE": "logs/graphiti_mcp_server.log",
        "LOG_LEVEL": "INFO",
        "OLLAMA_MODEL": "qwen2.5:7b",
        "OLLAMA_TEMPERATURE": "0.1",
        "OLLAMA_EMBEDDING_MODEL": "nomic-embed-text:v1.5",
        "OLLAMA_EMBEDDING_DIMENSIONS": "768",
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "SEARCH_LIMIT": "20",
        "ENABLE_DEDUPLICATION": "true",
        "PYDANTIC_VALIDATION_FIXES": "true",
        "COSINE_SIMILARITY_THRESHOLD": "0.8"
      }
    }
  }
}
```

**啟動測試：**
```bash
# 手動測試 STDIO 模式
cd /path/to/your/graphiti
uv run python graphiti_mcp_server.py --transport stdio

# 使用 MCP Inspector 測試
npx @modelcontextprotocol/inspector uv run python graphiti_mcp_server.py --transport stdio
```

---

### 模式二：SSE 模式（適用於網頁應用）

#### 基本 SSE 服務器設定

**1. 啟動 SSE 服務器**
```bash
# 預設端口 8000
uv run python graphiti_mcp_server.py --transport sse

# 自定義端口和主機
uv run python graphiti_mcp_server.py --transport sse --host 0.0.0.0 --port 8080

# 使用配置檔案
uv run python graphiti_mcp_server.py --config your_config.json --transport sse
```

**2. 服務器狀態檢查**
```bash
# 檢查服務器是否運行
curl -f http://localhost:8000/health || echo "服務器未運行"

# 查看可用工具
curl http://localhost:8000/tools
```

#### Claude Desktop SSE 模式設定

如果你想在 Claude Desktop 中使用 SSE 模式（適用於遠端服務器或容器化部署），可以這樣配置：

**配置檔案位置：**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

**SSE 模式配置範例：**
```json
{
  "mcpServers": {
    "graphiti-memory-sse": {
      "command": "curl",
      "args": [
        "-X", "POST",
        "-H", "Content-Type: application/json",
        "-d", "{\"method\":\"initialize\",\"params\":{}}",
        "http://localhost:8000/mcp"
      ],
      "env": {
        "MCP_SERVER_URL": "http://localhost:8000"
      }
    }
  }
}
```

**遠端服務器 SSE 配置：**
```json
{
  "mcpServers": {
    "graphiti-memory-remote": {
      "transport": {
        "type": "sse",
        "url": "http://your-server-ip:8000/sse"
      },
      "env": {
        "MCP_API_KEY": "your_api_key_if_needed"
      }
    }
  }
}
```

**使用 Docker 部署的 SSE 配置：**
```json
{
  "mcpServers": {
    "graphiti-memory-docker": {
      "transport": {
        "type": "sse",
        "url": "http://localhost:8000/sse"
      },
      "env": {
        "DOCKER_CONTAINER": "graphiti-mcp"
      }
    }
  }
}
```

#### 網頁客戶端整合

**JavaScript 客戶端範例：**
```javascript
// SSE 連接
const eventSource = new EventSource('http://localhost:8000/sse');

eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('收到訊息:', data);
};

// 調用 MCP 工具
async function addMemory(name, content, groupId = 'web_client') {
    const response = await fetch('http://localhost:8000/call', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            method: 'tools/call',
            params: {
                name: 'add_memory_simple',
                arguments: {
                    name: name,
                    episode_body: content,
                    group_id: groupId
                }
            }
        })
    });

    return await response.json();
}

// 搜尋記憶
async function searchMemory(query, maxResults = 10) {
    const response = await fetch('http://localhost:8000/call', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            method: 'tools/call',
            params: {
                name: 'search_memory_nodes',
                arguments: {
                    query: query,
                    max_nodes: maxResults
                }
            }
        })
    });

    return await response.json();
}
```

#### Docker 部署（SSE 模式）

**Dockerfile 範例：**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install uv
RUN uv sync

EXPOSE 8000

CMD ["uv", "run", "python", "graphiti_mcp_server.py", "--transport", "sse", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml 範例：**
```yaml
version: '3.8'
services:
  graphiti-mcp:
    build: .
    ports:
      - "8000:8000"
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=your_password
      - OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      - neo4j
      - ollama

  neo4j:
    image: neo4j:5
    ports:
      - "7687:7687"
      - "7474:7474"
    environment:
      - NEO4J_AUTH=neo4j/your_password

  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    command: ["serve"]

volumes:
  ollama_data:
```

### 其他 MCP 客戶端設定

#### 1. Inspector 模式（調試用）
```bash
# 使用 MCP Inspector 測試
npx @modelcontextprotocol/inspector uv run python graphiti_mcp_server.py --transport stdio
```

#### 2. 自定義 MCP 客戶端
```python
from mcp import ClientSession, StdioServerParameters
import asyncio

async def main():
    server_params = StdioServerParameters(
        command="uv",
        args=[
            "run", "python", "graphiti_mcp_server.py",
            "--transport", "stdio"
        ],
        env={
            "NEO4J_PASSWORD": "your_password"
        }
    )

    async with ClientSession(server_params) as session:
        # 使用 MCP 工具
        result = await session.call_tool(
            "add_memory_simple",
            {
                "name": "測試記憶",
                "episode_body": "這是一個測試記憶片段",
                "group_id": "test_group"
            }
        )
        print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

### 配置檢查

啟動 Claude Desktop 後，你應該能在工具列表中看到以下 MCP 工具：

- `add_memory_simple` - 添加記憶片段
- `search_memory_nodes` - 搜尋記憶節點
- `search_memory_facts` - 搜尋記憶事實
- `get_episodes` - 獲取記憶片段
- `test_connection` - 測試連接
- `clear_graph` - 清除圖資料庫

### 故障排除

如果 MCP 連接失敗，請檢查：

1. **路徑設定**
   ```bash
   # 確認專案路徑正確
   which uv
   cd /path/to/your/graphiti && pwd
   ```

2. **環境變數**
   ```bash
   # 測試環境變數載入
   echo $NEO4J_PASSWORD
   ```

3. **服務狀態**
   ```bash
   # 檢查 Neo4j 和 Ollama 服務
   neo4j status
   ollama list
   ```

4. **手動測試**
   ```bash
   # 手動啟動服務器測試
   uv run python graphiti_mcp_server.py --transport stdio
   ```

## 🔧 配置管理

### JSON 配置檔案範例

```json
{
  "ollama": {
    "model": "qwen2.5:7b",
    "base_url": "http://localhost:11434",
    "temperature": 0.1
  },
  "embedder": {
    "model": "nomic-embed-text:v1.5",
    "base_url": "http://localhost:11434",
    "dimensions": 768
  },
  "neo4j": {
    "uri": "bolt://localhost:7687",
    "user": "neo4j",
    "password": "your_neo4j_password"
  },
  "logging": {
    "level": "INFO",
    "file_path": "logs/graphiti_mcp.log",
    "backup_count": 30,
    "rotation_type": "time",
    "rotation_interval": "midnight"
  }
}
```

### 環境變數配置 (`.env`)

```bash
# ======================
# Neo4j 圖資料庫配置
# ======================
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password
NEO4J_DATABASE=graphiti-db

# ======================
# Ollama LLM 配置
# ======================
# 覆蓋 OpenAI 設定，使用 Ollama
OPENAI_API_KEY=ollama
OPENAI_BASE_URL=http://localhost:11434/v1

# 推薦的 LLM 模型
MODEL_NAME=qwen2.5:7b
SMALL_MODEL_NAME=qwen2.5:7b

# 嵌入模型（必須安裝）
EMBEDDER_MODEL_NAME=nomic-embed-text:v1.5

# ======================
# Graphiti 配置
# ======================
# 記憶分組 ID
GROUP_ID=your_group_id

# 並發限制（本地 LLM 建議較低值）
SEMAPHORE_LIMIT=3

# 關閉遙測
GRAPHITI_TELEMETRY_ENABLED=false

# ======================
# 進階配置
# ======================
# Ollama 服務器地址
OLLAMA_BASE_URL=http://localhost:11434

# LLM 溫度設定（0.0-1.0）
LLM_TEMPERATURE=0.1

# ======================
# 日誌配置
# ======================
# 日誌檔案路徑
LOG_FILE=logs/graphiti_mcp_server.log
LOG_LEVEL=INFO

# 日誌輪轉設定
LOG_ROTATION_TYPE=time
LOG_ROTATION_INTERVAL=midnight
LOG_BACKUP_COUNT=30

# ======================
# 其他重要設定
# ======================
# Ollama 模型設定（對應 config.py 中的變數名）
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_TEMPERATURE=0.1
OLLAMA_EMBEDDING_MODEL=nomic-embed-text:v1.5
OLLAMA_EMBEDDING_DIMENSIONS=768
OLLAMA_EMBEDDING_BASE_URL=http://localhost:11434

# 搜尋限制
SEARCH_LIMIT=20

# 功能開關
ENABLE_DEDUPLICATION=true
PYDANTIC_VALIDATION_FIXES=true

# 相似度閾值
COSINE_SIMILARITY_THRESHOLD=0.8
```

## 📋 日誌檔案管理

### 日誌檔案命名格式

系統使用每日輪轉的日誌檔案，命名格式如下：

```
logs/
├── graphiti_mcp_server_2025-09-17.log    # 當前日期的日誌
├── graphiti_mcp_server_2025-09-16.log    # 前一天的日誌
├── graphiti_mcp_server_2025-09-15.log    # 更早的日誌
└── ... (保留30天)
```

**命名規則：**
- 基本格式：`graphiti_mcp_server_YYYY-MM-DD.log`
- 每日午夜自動輪轉
- 保留30天的歷史檔案
- 自動清理過期檔案

**設定選項：**
```bash
# 日誌輪轉配置
LOG_ROTATION_TYPE=time          # 時間輪轉
LOG_ROTATION_INTERVAL=midnight  # 每日午夜
LOG_BACKUP_COUNT=30            # 保留30天
```

## 📚 API 功能

### 🔧 使用工具指令

**重要：** 在使用 Graphiti MCP 工具之前，請先閱讀 **[使用工具的指令](docs/使用工具的指令.md)**。

該文件包含：
- **搜索優先原則** - 開始任務前先搜索相關資訊
- **資訊儲存規範** - 如何正確儲存偏好、程序和事實
- **工作流程指引** - 最佳實踐和注意事項
- **工具使用範例** - 實際操作示範

**關鍵原則：**
```
1. 開始前先搜索：search_memory_nodes + search_memory_facts
2. 立即儲存重要資訊：add_memory_simple
3. 遵循發現的偏好和程序
4. 維持記憶的一致性和完整性
```

### 記憶管理

- **`add_memory_simple`** - 新增記憶片段到知識圖譜
  ```json
  {
    "name": "學習 Python",
    "episode_body": "今天學習了 Python 的類別和物件導向程式設計概念",
    "group_id": "學習記錄"
  }
  ```

- **`search_memory_nodes`** - 搜尋記憶節點 (實體)
  ```json
  {
    "query": "Python 程式設計",
    "max_nodes": 10,
    "group_ids": ["學習記錄"]
  }
  ```

- **`search_memory_facts`** - 搜尋記憶事實 (關係)
  ```json
  {
    "query": "程式語言學習",
    "max_facts": 10,
    "group_ids": ["學習記錄"]
  }
  ```

- **`get_episodes`** - 獲取最近的記憶片段
  ```json
  {
    "last_n": 5,
    "group_id": "學習記錄"
  }
  ```

### 系統管理

- **`test_connection`** - 測試系統連接狀態
- **`clear_graph`** - 清除所有圖資料庫資料

## 🔍 搜尋功能詳解

### 語意搜尋特色

- **智能理解**: 不只是關鍵字匹配，能理解查詢的語意
- **向量嵌入**: 使用 Ollama 嵌入模型進行向量相似度計算
- **混合搜尋**: 結合關鍵字搜尋和向量搜尋的優勢
- **相關性排序**: 自動按相關度排序搜尋結果

### 搜尋範例

```bash
# 搜尋程式相關記憶
query: "Python 學習"
# 能找到: "程式設計課程", "編程技巧", "開發經驗" 等相關內容

# 搜尋工作相關事實
query: "專案管理"
# 能找到: "團隊協作", "進度追蹤", "需求分析" 等關聯關係
```

## 📊 監控和日誌

### 結構化日誌

#### 日誌檔案命名規則

系統使用按日期分割的日誌檔案，避免單一檔案過大：

```bash
logs/
├── graphiti_mcp_2025-01-15.log  # 今天的日誌
├── graphiti_mcp_2025-01-14.log  # 昨天的日誌
├── graphiti_mcp_2025-01-13.log  # 前天的日誌
└── ...                          # 保留 30 天

# 查看今天的日誌
tail -f logs/graphiti_mcp_$(date +%Y-%m-%d).log

# 查看所有日誌
tail -f logs/graphiti_mcp_*.log

# 搜尋特定操作（所有日期）
grep "add_memory" logs/graphiti_mcp_*.log

# 搜尋今天的特定操作
grep "add_memory" logs/graphiti_mcp_$(date +%Y-%m-%d).log
```

#### 日誌輪轉配置

在配置檔案中可以調整日誌輪轉設定：

```json
{
  "logging": {
    "rotation_type": "time",      // "time" 或 "size"
    "rotation_interval": "midnight", // 輪轉時間點
    "backup_count": 30,           // 保留檔案數量
    "max_file_size": 10485760     // 大小輪轉時的檔案大小限制
  }
}
```

**時間輪轉選項：**
- `midnight` - 每天午夜輪轉 (預設)
- `H` - 每小時輪轉
- `D` - 每天輪轉
- `W0`-`W6` - 每週特定日期輪轉

**大小輪轉：**
- 檔案達到指定大小時自動輪轉
- 適合高頻使用的場景

### 性能監控

- ⏱️ **操作執行時間追蹤**
- 📈 **記憶添加性能指標**
- 🔍 **Neo4j 查詢性能分析**
- 🧲 **嵌入生成效能監控**

## 🧪 測試

```bash
# 運行核心測試
uv run python -m pytest tests/

# 運行完整集成測試
uv run python tests/comprehensive_test.py

# 運行性能測試
uv run python tests/model_performance_test.py
```

## 🔧 故障排除

### 常見問題

1. **Neo4j 連接失敗**
   - 檢查 Neo4j 服務是否運行
   - 確認密碼和連接設定正確

2. **Ollama 連接失敗**
   - 確認 Ollama 服務運行: `ollama serve`
   - 檢查模型是否已下載: `ollama pull qwen2.5:7b`

3. **搜尋無結果**
   - 確認已有記憶資料
   - 檢查 group_ids 篩選條件
   - 查看日誌檔案了解詳細錯誤

### 日誌分析

```bash
# 查看錯誤日誌
grep "ERROR\|WARN" logs/graphiti_mcp.log

# 監控性能
grep "duration" logs/graphiti_mcp.log
```

## 🛠️ 開發工具

```bash
# 性能診斷
uv run python tools/performance_diagnose.py

# 結構檢查
uv run python tools/inspect_schema.py

# 狀態報告
uv run python tools/final_status_report.py
```

## 🔄 與原版差異

### 優化改進

- 🏗️ **企業級架構**: 模組化設計和結構化異常處理
- 🇹🇼 **完整中文化**: API 回應和使用者介面全中文
- ⚡ **性能優化**: 智能配置管理和連接池
- 📊 **完整監控**: 結構化日誌和性能追蹤
- 🔍 **改進搜尋**: 使用正確的 Graphiti API 進行語意搜尋

### 保持相容

- ✅ **API 相容**: 與原版 MCP 工具參數完全相容
- ✅ **功能完整**: 保留所有原版核心功能
- ✅ **配置彈性**: 支援 JSON 配置和環境變數

## 📜 授權

MIT License

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

---

**專為台灣開發者打造的本地化知識圖譜解決方案** 🇹🇼