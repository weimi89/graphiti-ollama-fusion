# Graphiti MCP Server

知识图谱记忆服务 — 整合多 LLM 提供者（Ollama / GLM / GROQ / OpenRouter / DeepSeek）与 Neo4j 图数据库的 MCP 服务器。

基于 [getzep/graphiti](https://github.com/getzep/graphiti) 扩充开发，支持本地 Ollama 和云端 LLM 弹性切换，并可独立指定 Embedding 提供者（与 LLM 解耦）。

## 特色功能

- **智能记忆管理** — 使用知识图谱存储和检索复杂的记忆关系
- **语义搜索** — 基于向量嵌入的混合搜索（向量 + 关键字 + 图遍历）
- **16 种搜索策略** — 高级搜索支持 RRF、MMR、Cross-Encoder 等多种重排序方式
- **多 LLM 提供者** — 支持 Ollama（本地）、GLM（智谱 AI 免费）、GROQ（高速推理）、OpenRouter（聚合各家模型）、DeepSeek（深度求索），通过环境变量一键切换
- **Embedding 与 LLM 解耦** — 可用 `EMBEDDING_PROVIDER` 独立指定嵌入器，云端 LLM 自动回退本地 `bge-m3`
- **双模型分流** — Ollama 模式下复杂任务使用主模型，简单任务自动切换小模型以提升性能
- **智能内容切分** — 长文本自动分段处理，降低 LLM 负载（可配置阈值）
- **后台记忆处理** — 记忆添加可在后台执行，MCP 调用立即返回
- **记忆去重** — 自动检测高度相似的既有记忆，避免重复存储
- **冲突检测** — 检测两实体间的矛盾事实，识别已失效与有效的信息
- **社群检测** — 基于 Label Propagation 算法自动聚类相关实体
- **重要性追踪** — 自动记录实体访问频率，搜索结果依重要性排序
- **智能遗忘** — 识别并清理过时、低访问量的记忆，保持图谱精简
- **批量导入** — 一次提交多笔记忆，适合大量数据迁移
- **结构化三元组** — 直接添加“主体-关系-客体”，跳过 LLM 提取，秒速完成
- **Web 管理界面** — 内置仪表板、浏览、搜索、知识图谱可视化、AI 问答、社群浏览
- **多国语系（i18n）** — 响应消息支持 30+ locale（含 zh-TW / en / zh-CN / ja / pt-BR / ko / es / de / fr 等）；MCP 工具依 `SERVER_LANG`、REST API 依 HTTP `Accept-Language` 自动协商
- **深色/浅色主题** — Web 界面支持主题切换
- **安全模式** — 可选择跳过实体提取的快速记忆添加
- **Docker 支持** — 内置 Dockerfile，支持容器化部署
- **并发安全** — asyncio.Lock 保护初始化，防止竞态条件
- **分层健康检查** — `/health`（liveness）+ `/health/ready`（readiness）

## 系统需求

| 项目 | 需求 |
|------|------|
| Python | 3.10+（推荐 3.11+） |
| Neo4j | 4.0+（`bolt://localhost:7687`） |
| LLM 提供者 | Ollama / GLM / GROQ / OpenRouter / DeepSeek（五选一） |
| Node.js | 18+（仅用于 PM2 后台执行，可选） |
| 磁盘空间 | ~3GB（Ollama 模型 + Neo4j 数据） |

### LLM 提供者选择

通过 `LLM_PROVIDER` 环境变量切换（`ollama` / `glm` / `groq` / `openrouter` / `deepseek`）：

| 提供者 | 特点 | LLM 模型 | Embedding | 适合场景 |
|--------|------|----------|-----------|----------|
| **Ollama**（默认） | 完全本地，数据不离机 | `qwen2.5:3b` | `bge-m3`（中文 + RAG 优异） | 有 GPU、重视隐私 |
| **GLM** | 免费云端，稳定无限流 | `glm-4-flash`（免费） | `embedding-3` | 无 GPU、搜索密集场景 |
| **GROQ** | 超高速推理 | `llama-3.3-70b-versatile` | 回退 Ollama `bge-m3` | 偶尔写入、追求质量 |
| **OpenRouter** | 聚合各家模型，含免费额度 | `stepfun/step-3.5-flash:free` 等 | 回退 Ollama `bge-m3` | 想用特定云端模型 |
| **DeepSeek** | 深度求索云端，性价比高 | `deepseek-v4-flash` / `deepseek-v4-pro` | 回退 Ollama `bge-m3` | 中文理解、低成本云端 |

> **Embedding 与 LLM 解耦**：嵌入器通过 `EMBEDDING_PROVIDER`（`ollama` / `glm`）独立指定，未设定时跟随 `LLM_PROVIDER`。实际上只有 `glm` 使用 GLM `embedding-3`，其余（含 GROQ / OpenRouter / DeepSeek 等不提供 Embedding 的云端 LLM）一律自动使用 Ollama `bge-m3`。**因此使用任何云端 LLM 时，仍需本地 Ollama 提供嵌入服务（除非 embedding 也设为 glm）。**

#### Ollama 模式（本地）

```bash
# LLM 主模型（推荐 qwen2.5:3b，速度与稳定性最佳平衡）
ollama pull qwen2.5:3b

# 嵌入模型（必须，用于向量搜索）
ollama pull bge-m3
```

> **模型选择注意事项**：
> - `qwen2.5:3b` — 推荐，~2s/call、~100 t/s，graphiti-core 结构化输出 100% 稳定
> - `qwen2.5:7b` — 效果更好但慢 5-10 倍，适合追求质量的场景
> - `qwen2.5:1.5b` — 速度最快但**不稳定**（结构化 JSON 成功率仅 33%），不建议使用

#### GLM 模式（智谱 AI 云端）

```bash
# .env 设定
LLM_PROVIDER=glm
GLM_API_KEY=your_api_key          # 从 https://open.bigmodel.cn 取得
GLM_MODEL=glm-4-flash             # 免费模型
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768      # 需与 Neo4j 向量索引维度一致
```

> **GLM 性能参考**：写入 ~22s（短文本）、搜索 ~0.34s、零 Rate Limit 错误、比本地 Ollama 慢 2-5 倍但完全免费。

#### GROQ 模式（高速推理）

```bash
# .env 设定
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key         # 从 https://console.groq.com 取得
GROQ_MODEL=llama-3.3-70b-versatile
```

> **注意**：GROQ 不提供 Embedding 服务，需搭配 Ollama 嵌入器（自动回退）或将 `EMBEDDING_PROVIDER` 设为 glm。GROQ 有严格的 Rate Limit，高频使用会触发大量重试。

#### OpenRouter 模式（聚合各家模型）

```bash
# .env 设定
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_api_key       # 从 https://openrouter.ai/keys 取得
OPENROUTER_MODEL=stepfun/step-3.5-flash:free   # 可改为任意 OpenRouter 模型
```

> **注意**：OpenRouter 不提供 Embedding，自动回退 Ollama `bge-m3`。模型清单见 https://openrouter.ai/models（含多个 `:free` 免费模型）。

#### DeepSeek 模式（深度求索）

```bash
# .env 设定
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key         # 从 https://platform.deepseek.com 取得
DEEPSEEK_MODEL=deepseek-v4-flash      # 推荐；或 deepseek-v4-pro（效果更佳）
```

> **注意**：DeepSeek 不提供 Embedding，自动回退 Ollama `bge-m3`。`deepseek-chat` / `deepseek-reasoner` 将于 2026-07-24 下线，建议改用 `deepseek-v4-flash` / `deepseek-v4-pro`。DeepSeek 严格要求 `json_object` 模式的 prompt 含 "json" 字符串，客户端已内置保底防护，无需额外设定。

## 快速启动

### 1. 前置准备

确认 Neo4j 已在本机运行，并根据选择的 LLM 提供者准备对应服务：

```bash
# 确认 Neo4j 运行中（必须）
neo4j status
# 或者使用 Docker: docker run -d -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/your_password neo4j:latest

# Ollama 模式：确认 Ollama 运行中
ollama list
# 若未启动: ollama serve

# GLM / GROQ 模式：只需要有效的 API Key，无需本地服务
```

### 2. 安装依赖

```bash
git clone <repo-url>
cd graphiti
uv sync
```

> **注意**：本项目使用 [uv](https://github.com/astral-sh/uv) 管理依赖。若未安装：`curl -LsSf https://astral.sh/uv/install.sh | sh`

### 3. 配置环境

```bash
cp .env.example .env
```

编辑 `.env`，**至少**需要修改以下项目：

```bash
NEO4J_PASSWORD=your_actual_password  # 必填：Neo4j 密码
LLM_PROVIDER=ollama                  # ollama / glm / groq / openrouter / deepseek
OLLAMA_MODEL=qwen2.5:3b              # Ollama 模式：本地 LLM 模型
# GLM_API_KEY=your_key               # GLM 模式：智谱 AI API Key
# GROQ_API_KEY=your_key              # GROQ 模式：GROQ API Key
# OPENROUTER_API_KEY=your_key        # OpenRouter 模式：API Key
# DEEPSEEK_API_KEY=your_key          # DeepSeek 模式：API Key
```

### 4. 启动服务

```bash
# HTTP 模式（推荐，包含 Web 管理界面）
uv run python graphiti_mcp_server.py --transport http --port 8000

# 或使用 PM2 后台执行（推荐长期运行）
pm2 start ecosystem.config.cjs
```

### 5. 验证服务

启动后可访问以下端点：

| 端点 | 说明 |
|------|------|
| http://localhost:8000/ | Web 管理界面 |
| http://localhost:8000/mcp | MCP 端点（供 MCP 客户端连接） |
| http://localhost:8000/health | 健康检查（liveness） |
| http://localhost:8000/health/ready | 深度检查（含 Neo4j 连接） |
| http://localhost:8000/api/stats | REST API 统计 |

## 项目结构

```
graphiti/
├── graphiti_mcp_server.py        # 主入口 — MCP 工具定义（19 个工具）
├── src/
│   ├── config.py                 # 配置管理（GraphitiConfig，支持 JSON/.env 层叠）
│   ├── web_api.py                # Web 管理界面 REST API（20+ 端点）
│   ├── ollama_graphiti_client.py  # Ollama LLM 客户端（双模型分流）
│   ├── glm_client.py             # GLM（智谱 AI）LLM 客户端（OpenAI 兼容 API）
│   ├── openrouter_client.py      # OpenRouter LLM 客户端（聚合各家模型）
│   ├── deepseek_client.py        # DeepSeek LLM 客户端（json_object + 保底 json 防护）
│   ├── ollama_embedder.py        # Ollama 嵌入模型适配器
│   ├── content_preprocessor.py   # 智能内容切分（长文本自动分段）
│   ├── deduplication.py          # 记忆去重（余弦相似度比对）
│   ├── importance.py             # 重要性追踪与智能遗忘
│   ├── safe_memory_add.py        # 安全记忆添加（跳过实体提取）
│   ├── timezone_utils.py         # 时区转换（UTC→本地时区显示）
│   ├── i18n.py                   # 后端多国语系（REST 依 Accept-Language、MCP 依 SERVER_LANG）
│   ├── exceptions.py             # 结构化异常处理（12 种异常类别）
│   └── logging_setup.py          # 日志系统（时间轮转 + 性能监控）
├── web/                          # Web 管理界面前端（SPA，无 build）
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js                # REST API 封装
│       ├── components.js         # UI 组件渲染（含社群页面）
│       └── app.js                # SPA 路由、状态管理
├── tests/                        # 测试套件（183 个测试）
│   ├── test_content_preprocessor.py  # 切分逻辑测试（17 个）
│   ├── test_new_features.py      # 新功能测试（32 个）
│   ├── test_i18n.py             # 多国语系测试（37 个）
│   ├── test_unit.py              # 单元测试
│   ├── test_web_api.py           # Web API 测试
│   ├── test_web_ui_features.py   # Web UI 功能测试
│   ├── test_integration_manual.py # 手动整合测试
│   └── bench_deepseek_flash_vs_pro.py # DeepSeek flash/pro 性能基准脚本
├── tools/                        # 开发诊断工具
│   ├── status_report.py          # 统合状态报告
│   ├── validate_config.py        # 配置验证
│   ├── performance_diagnose.py   # 性能诊断
│   ├── inspect_schema.py         # Neo4j 结构检查
│   └── batch_reprocess.py        # 批次重新处理
├── docs/                         # 文档
├── logs/                         # 日志（时间轮转，默认保留 30 天）
├── Dockerfile                    # Docker 容器化部署
└── ecosystem.config.cjs          # PM2 配置
```

## MCP 客户端设定

### HTTP 模式（推荐）

适用于 Claude Code、Cline 等支持 HTTP 的 MCP 客户端：

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

适用于 Claude Desktop 等需要直接启动进程的客户端：

**配置文件位置：**
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

> **注意**：SSE 模式（`--transport sse`）已不建议使用。MCP 1.x 有 session 初始化兼容性问题，请改用 HTTP 模式。

## MCP 工具（19 个）

### 记忆管理（7 个）

| 工具 | 说明 |
|------|------|
| `add_memory_simple` | 添加记忆到知识图谱（支持后台处理、智能切分、去重检查） |
| `add_episode_bulk` | 批量添加多笔记忆（默认后台处理） |
| `add_triplet` | 结构化三元组添加（跳过 LLM，秒速完成） |
| `search_memory_nodes` | 搜索记忆节点（支持 16 种搜索策略、时间过滤） |
| `search_memory_facts` | 搜索记忆事实（支持关系类型过滤、时间范围、有效性过滤） |
| `advanced_search` | 高级搜索（16 种策略，返回节点+边+社群+片段） |
| `get_episodes` | 获取最近的记忆片段 |

### 知识分析（3 个）

| 工具 | 说明 |
|------|------|
| `check_conflicts` | 检测两实体间的事实冲突（有效 vs 已失效） |
| `get_node_edges` | 探索节点的入边和出边关系 |
| `build_communities` | 触发社群检测与聚类（默认后台处理） |

### 记忆维护（2 个）

| 工具 | 说明 |
|------|------|
| `get_stale_memories` | 查询过时、低访问量的记忆 |
| `cleanup_stale_memories` | 清理过时记忆（默认 dry_run 预览模式） |

### 任务管理

| 工具 | 说明 |
|------|------|
| `get_memory_task_status` | 查询后台记忆处理任务的进度和结果 |

### 删除与查询

| 工具 | 说明 |
|------|------|
| `delete_episode` | 删除记忆片段 |
| `delete_entity_edge` | 删除实体边（关系） |
| `get_entity_edge` | 获取实体边详细信息 |

### 系统管理

| 工具 | 说明 |
|------|------|
| `get_status` | 获取服务状态（Neo4j、LLM、嵌入器） |
| `test_connection` | 测试 Neo4j / LLM / 嵌入器连接 |
| `clear_graph` | 清除图数据库（支持按 group_id 清除） |

## 工具参数

### add_memory_simple

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `name` | string | Y | | 记忆名称 |
| `episode_body` | string | Y | | 记忆内容（超过 800 字符自动切分） |
| `group_id` | string | | `"default"` | 分组 ID（建议按项目隔离） |
| `source` | string | | `"text"` | 来源类型: `text` / `json` / `message` |
| `source_description` | string | | `"MCP Server"` | 来源描述 |
| `use_safe_mode` | bool | | `false` | 安全模式（跳过实体提取，快但记忆不可被搜索） |
| `background` | bool | | `false` | 后台处理（立即返回 task_id，适合长文本） |
| `force` | bool | | `false` | 跳过去重检查（强制添加） |
| `excluded_entity_types` | list | | | 排除的实体类型（减少不需要的提取量） |

> **性能提示**：
> - 短文本（<800 字符）：直接处理，通常 30-40 秒完成
> - 长文本（>800 字符）：自动切分为多段，使用 `add_episode_bulk` 并发处理（比串行快 ~33%）
> - 使用 `background=true` 可避免 MCP 调用阻塞，通过 `get_memory_task_status` 追踪进度
> - `use_safe_mode=true` 秒速完成但记忆无法被 search 工具找到
> - 启用去重时，高度相似的记忆会被警告（`force=true` 可跳过）

### add_episode_bulk

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `episodes` | list | Y | | 记忆列表，每项含 `name` 和 `content` |
| `group_id` | string | | `"default"` | 分组 ID |
| `source` | string | | `"text"` | 来源类型 |
| `background` | bool | | `true` | 后台处理（批量通常耗时） |

### add_triplet

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `source_name` | string | Y | | 来源实体名称（如 "Alice"） |
| `target_name` | string | Y | | 目标实体名称（如 "Google"） |
| `relation_name` | string | Y | | 关系名称（如 "works_at"） |
| `fact` | string | Y | | 事实描述（如 "Alice works at Google"） |
| `group_id` | string | | `"default"` | 分组 ID |
| `source_labels` | list | | | 来源实体标签 |
| `target_labels` | list | | | 目标实体标签 |

### search_memory_nodes

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `query` | string | Y | | 搜索关键字（自然语言） |
| `max_nodes` | int | | `10` | 最大返回数量 |
| `group_ids` | list | | | 分组过滤（多个 group 联合搜索） |
| `entity_types` | list | | | 实体类型过滤 |
| `search_recipe` | string | | | 搜索策略（见高级搜索） |
| `created_after` | string | | | 创建时间下限（ISO datetime） |
| `created_before` | string | | | 创建时间上限（ISO datetime） |

### search_memory_facts

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `query` | string | Y | | 搜索关键字 |
| `max_facts` | int | | `10` | 最大返回数量 |
| `group_ids` | list | | | 分组过滤 |
| `center_node_uuid` | string | | | 中心节点 UUID（探索特定节点的关系） |
| `edge_types` | list | | | 关系类型过滤（如 `["works_at"]`） |
| `created_after` | string | | | 创建时间下限（ISO datetime） |
| `created_before` | string | | | 创建时间上限（ISO datetime） |
| `only_valid` | bool | | `false` | 仅返回未失效的事实 |

### advanced_search

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `query` | string | Y | | 搜索关键字 |
| `search_recipe` | string | | `"combined_rrf"` | 搜索策略（16 种可选） |
| `max_results` | int | | `10` | 最大返回数量 |
| `group_ids` | list | | | 分组过滤 |
| `center_node_uuid` | string | | | 中心节点 UUID |

**可用搜索策略（search_recipe）：**

| 类别 | 策略 | 说明 |
|------|------|------|
| 综合 | `combined_rrf` | 综合 RRF 融合（默认，推荐） |
| 综合 | `combined_mmr` | 综合 MMR 多样性重排 |
| 综合 | `combined_cross_encoder` | 综合 Cross-Encoder 精排 |
| 边 | `edge_rrf` / `edge_mmr` / `edge_cross_encoder` | 边搜索（3 种排序） |
| 边 | `edge_node_distance` / `edge_episode_mentions` | 边搜索（图距离/引用次数） |
| 节点 | `node_rrf` / `node_mmr` / `node_cross_encoder` | 节点搜索（3 种排序） |
| 节点 | `node_node_distance` / `node_episode_mentions` | 节点搜索（图距离/引用次数） |
| 社群 | `community_rrf` / `community_mmr` / `community_cross_encoder` | 社群搜索 |

### check_conflicts

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `source_name` | string | Y | | 来源实体名称 |
| `target_name` | string | Y | | 目标实体名称 |
| `group_id` | string | | `"default"` | 分组 ID |

### get_node_edges

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `node_uuid` | string | Y | | 节点 UUID |
| `include_inbound` | bool | | `true` | 包含入边 |
| `include_outbound` | bool | | `true` | 包含出边 |
| `max_edges` | int | | `50` | 最大返回数量 |

### build_communities

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `group_ids` | list | | | 指定分组（留空则全部） |
| `background` | bool | | `true` | 后台处理 |

### get_stale_memories

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | 超过多少天未访问视为过时 |
| `min_access_count` | int | | `2` | 访问次数低于此值才列入 |
| `group_id` | string | | | 分组过滤 |
| `limit` | int | | `50` | 最大返回数量 |

### cleanup_stale_memories

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | 过时天数阈值 |
| `min_access_count` | int | | `2` | 最低访问次数阈值 |
| `group_id` | string | | | 分组过滤 |
| `dry_run` | bool | | `true` | 预览模式（不实际删除） |
| `limit` | int | | `50` | 最大处理数量 |

### get_memory_task_status

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `task_id` | string | Y | 后台任务 ID（由 `add_memory_simple(background=true)` 返回） |

## Web 管理界面

HTTP 模式下访问 `http://localhost:8000/` 即可使用。

**功能：**
- 仪表板 — 节点数、事实数、记忆片段数统计
- 实体节点 — 浏览、筛选、向量搜索
- 事实关系 — 浏览、筛选、向量搜索
- 记忆片段 — 浏览、全文搜索、删除
- 社群浏览 — 社群节点列表、摘要、触发社群构建
- 三元组表单 — 直接添加“主体-关系-客体”结构化知识
- Group 管理 — 按分组过滤、批次删除
- 知识图谱可视化 — 节点关系图形化展示
- AI 问答 — 基于知识图谱的智能问答
- 质量分析 — 记忆质量与覆盖度分析
- 主题切换 — 深色/浅色主题

**REST API：**

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/stats` | GET | 仪表板统计 |
| `/api/groups` | GET | 取得所有 group_id |
| `/api/nodes` | GET | 浏览实体节点（分页） |
| `/api/facts` | GET | 浏览事实（分页） |
| `/api/episodes` | GET | 浏览记忆片段（分页） |
| `/api/search/nodes` | GET | 向量搜索节点 |
| `/api/search/facts` | GET | 向量搜索事实 |
| `/api/search/advanced` | GET | 高级搜索（16 种策略） |
| `/api/communities` | GET | 浏览社群节点（分页） |
| `/api/communities/build` | POST | 触发社群构建 |
| `/api/memory/add-bulk` | POST | 批量添加记忆 |
| `/api/memory/add-triplet` | POST | 添加三元组 |
| `/api/memory/tasks` | GET | 列出后台任务（支持状态筛选） |
| `/api/memory/tasks/{id}` | GET | 查询单一任务状态 |
| `/api/analytics/stale` | GET | 查询过时记忆 |
| `/api/analytics/cleanup` | POST | 清理过时记忆 |
| `/api/nodes/{uuid}` | DELETE | 删除节点 |
| `/api/episodes/{uuid}` | DELETE | 删除记忆片段 |
| `/api/facts/{uuid}` | DELETE | 删除事实 |
| `/api/groups/{group_id}` | DELETE | 删除整个 group |

## 配置

### 环境变量（.env）

配置使用层叠机制：JSON 配置文件为基础，环境变量覆盖个别值。

```bash
# === 必填 ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password        # 必须修改

# === LLM 提供者选择 ===
LLM_PROVIDER=ollama                 # ollama / glm / groq / openrouter / deepseek

# === Embedding 提供者（可选，默认跟随 LLM_PROVIDER） ===
# 仅 glm 使用 GLM Embedding，其余一律使用 Ollama bge-m3
# EMBEDDING_PROVIDER=ollama         # ollama / glm

# === Ollama 配置（LLM_PROVIDER=ollama 时使用） ===
OLLAMA_MODEL=qwen2.5:3b             # 主模型（推荐 qwen2.5:3b）
OLLAMA_SMALL_MODEL=qwen2.5:3b       # 小模型（简单任务用，可选不同模型）
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.1

# === GLM 配置（LLM_PROVIDER=glm 时使用） ===
GLM_API_KEY=your_api_key            # 从 https://open.bigmodel.cn 取得
GLM_MODEL=glm-4-flash               # 免费模型
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768

# === GROQ 配置（LLM_PROVIDER=groq 时使用） ===
GROQ_API_KEY=your_api_key           # 从 https://console.groq.com 取得
GROQ_MODEL=llama-3.3-70b-versatile

# === OpenRouter 配置（LLM_PROVIDER=openrouter 时使用） ===
OPENROUTER_API_KEY=your_api_key     # 从 https://openrouter.ai/keys 取得
OPENROUTER_MODEL=stepfun/step-3.5-flash:free

# === DeepSeek 配置（LLM_PROVIDER=deepseek 时使用） ===
DEEPSEEK_API_KEY=your_api_key       # 从 https://platform.deepseek.com 取得
DEEPSEEK_MODEL=deepseek-v4-flash    # 或 deepseek-v4-pro

# === Ollama 嵌入模型（非 glm 嵌入时皆使用） ===
OLLAMA_EMBEDDING_MODEL=bge-m3
OLLAMA_EMBEDDING_DIMENSIONS=768

# === 显示与语系（可选） ===
GRAPHITI_DISPLAY_TIMEZONE=Asia/Taipei # API 返回时间戳显示时区（IANA 名称；存储维持 UTC）
SERVER_LANG=zh-TW                     # MCP 工具响应语言（完整 locale 见 src/i18n.py）；REST API 改依 Accept-Language

# === 记忆性能（可选） ===
GRAPHITI_CHUNK_THRESHOLD=800         # 触发智能切分的字符数阈值
GRAPHITI_MAX_CHUNK_SIZE=600          # 每段最大字符数
GRAPHITI_MAX_COROUTINES=10            # 最大并行协程数
GRAPHITI_DEFAULT_BACKGROUND=false    # 是否默认后台处理

# === 重要性追踪与智能遗忘（可选） ===
ENABLE_IMPORTANCE_TRACKING=true      # 启用访问追踪
IMPORTANCE_WEIGHT=0.1                # 重要性权重
STALE_DAYS_THRESHOLD=30              # 过时天数阈值
STALE_MIN_ACCESS_COUNT=2             # 最低访问次数

# === 日志 ===
LOG_FILE=logs/graphiti_mcp_server.log
LOG_LEVEL=INFO
```

> **完整环境变量列表**请参见 `.env.example`

### JSON 配置文件

适用于需要版本控制的配置（环境变量仍可覆盖）：

```bash
uv run python graphiti_mcp_server.py --config config.json --transport http
```

```json
{
  "llm_provider": "ollama",
  "embedding_provider": "",
  "ollama": {
    "model": "qwen2.5:3b",
    "small_model": "qwen2.5:3b",
    "base_url": "http://localhost:11434"
  },
  "glm": {
    "api_key": "your_api_key",
    "model": "glm-4-flash",
    "embedding_model": "embedding-3",
    "embedding_dimensions": 768
  },
  "groq": {
    "api_key": "your_api_key",
    "model": "llama-3.3-70b-versatile"
  },
  "openrouter": {
    "api_key": "your_api_key",
    "model": "stepfun/step-3.5-flash:free"
  },
  "deepseek": {
    "api_key": "your_api_key",
    "model": "deepseek-v4-flash"
  },
  "embedder": {
    "model": "bge-m3",
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
    "max_coroutines": 10,
    "default_background": false
  }
}
```

## PM2 后台执行

```bash
npm install -g pm2

pm2 start ecosystem.config.cjs      # 启动
pm2 status                           # 状态
pm2 logs graphiti-mcp-http           # 实时日志
pm2 restart graphiti-mcp-http --update-env  # 重启（重新载入 .env）

pm2 save && pm2 startup              # 设定开机自动启动
```

> **提示**：修改 `.env` 后必须使用 `--update-env` 旗标重启，否则环境变量不会更新。

## Docker 部署

```bash
docker build -t graphiti-mcp .

# 注意：Docker 容器需要能够连接到 Neo4j 和 Ollama
# 使用 host network 最简单
docker run -p 8000:8000 --env-file .env --network host graphiti-mcp

# 或者明确指定外部服务地址
docker run -p 8000:8000 \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --env-file .env graphiti-mcp
```

## 测试

```bash
# 执行所有测试（183 个，约 1 秒）
uv run python -m pytest tests/

# 详细输出
uv run python -m pytest tests/ -v

# 仅执行特定测试
uv run python -m pytest tests/test_content_preprocessor.py -v
uv run python -m pytest tests/test_new_features.py -v
uv run python -m pytest tests/test_unit.py -v
```

> **注意**：`test_integration_manual.py` 中的 3 个 async 测试需要安装 `pytest-asyncio`，缺少时会显示 Failed 但不影响其他测试。`bench_deepseek_flash_vs_pro.py` 为性能基准脚本，非单元测试。

## 故障排除

### Neo4j 连接失败

```bash
neo4j status                              # 检查服务状态
cypher-shell -u neo4j -p your_password    # 确认密码正确
curl http://localhost:7474                 # 确认 HTTP 端口
```

常见原因：
- Neo4j 未启动
- 密码错误（`.env` 中的 `NEO4J_PASSWORD`）
- 端口被占用或防火墙阻挡

### LLM 连接失败

**Ollama 模式：**
```bash
ollama serve                # 启动 Ollama 服务
ollama list                 # 检查已安装模型
ollama pull qwen2.5:3b      # 安装缺少的模型
```

常见原因：Ollama 未启动、模型未安装、GPU 内存不足

**GLM 模式：**
- 确认 `GLM_API_KEY` 正确
- 确认 `GLM_EMBEDDING_DIMENSIONS=768`（需与 Neo4j 向量索引一致）
- GLM API 端点：`https://open.bigmodel.cn/api/paas/v4/`

**GROQ 模式：**
- 确认 `GROQ_API_KEY` 正确
- Rate Limit 频繁时考虑切换至 GLM 模式
- GROQ 不提供 Embedding，需确保 Ollama 嵌入器可用

**OpenRouter 模式：**
- 确认 `OPENROUTER_API_KEY` 正确、`OPENROUTER_MODEL` 为有效模型 ID（见 https://openrouter.ai/models）
- 不提供 Embedding，需确保 Ollama 嵌入器可用

**DeepSeek 模式：**
- 确认 `DEEPSEEK_API_KEY` 正确
- 若出现 `Prompt must contain the word 'json'`：这是 DeepSeek `json_object` 模式的硬性要求，客户端已内置保底防护；若仍出现，确认使用的是最新版 `src/deepseek_client.py` 并重启服务
- 不提供 Embedding，需确保 Ollama 嵌入器可用

### MCP 连接错误

如果出现 `Invalid request parameters` 或 `Received request before initialization was complete`：

1. 确认使用 HTTP 传输模式（**不要用 SSE**）
2. 确认客户端设定为 `"type": "http"`, `"url": "http://localhost:8000/mcp"`
3. 重启服务：`pm2 restart graphiti-mcp-http --update-env`
4. 在 Claude Code 中执行 `/mcp` 重新连接

### 记忆添加速度慢

- **Ollama**：检查模型大小（`qwen2.5:3b` 比 `7b` 快 5-10 倍），确认有使用 GPU（`ollama ps`）
- **GLM**：每个 add_episode 需 10-20+ 次 LLM 网络往返，短文本 ~22s 为正常值
- **GROQ**：Rate Limit 会导致大量重试，如频繁使用建议切换至 GLM 或 Ollama
- 使用 `background=true` 避免阻塞
- 调低 `GRAPHITI_CHUNK_THRESHOLD` 让长文本更早切分

### PM2 问题

```bash
pm2 status                                        # 检查状态
pm2 logs graphiti-mcp-http --err --lines 50        # 错误日志
lsof -i :8000                                     # 检查端口占用
pm2 delete graphiti-mcp-http && pm2 start ecosystem.config.cjs  # 完全重启
```

## 开发诊断工具

```bash
uv run python tools/status_report.py           # 统合状态报告（Neo4j + Ollama + 配置）
uv run python tools/validate_config.py         # 验证 .env 和配置完整性
uv run python tools/performance_diagnose.py    # LLM 性能诊断
uv run python tools/inspect_schema.py          # Neo4j 索引和约束检查
uv run python tools/migrate_embeddings.py      # Embedding 模型迁移（切换模型后重新生成向量）
```

### Embedding 模型迁移

切换 embedding 模型（如 `nomic-embed-text` → `bge-m3`）后，可使用迁移工具将所有现有向量重新生成，确保搜索质量一致：

```bash
# 预览需要迁移的数量
uv run python tools/migrate_embeddings.py --dry-run

# 全量迁移（支持断点续跑）
uv run python tools/migrate_embeddings.py

# 只迁移指定 group
uv run python tools/migrate_embeddings.py --group-id myproject

# 从断点继续（中断后重跑）
uv run python tools/migrate_embeddings.py --resume
```

> **兼容性**：`bge-m3` 原生 1024 维，系统自动截断为 768 维以兼容现有 Neo4j 向量索引。迁移前后的数据可共存，但建议执行完整迁移以获得最佳搜索质量。

## 文档

- [使用工具的指令](../使用工具的指令.md) — MCP 工具使用指南与最佳实践
- [Graphiti Memory Rules](../graphiti-memory-rules.md) — 记忆规则说明

## 授权

MIT License
