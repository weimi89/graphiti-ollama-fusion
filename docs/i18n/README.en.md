# Graphiti MCP Server

A knowledge graph memory service — an MCP server integrating multiple LLM providers (Ollama / GLM / GROQ / OpenRouter / DeepSeek) with the Neo4j graph database.

Built as an extension of [getzep/graphiti](https://github.com/getzep/graphiti), it supports flexible switching between local Ollama and cloud LLMs, and lets you independently specify the Embedding provider (decoupled from the LLM).

## Key Features

- **Intelligent memory management** — Stores and retrieves complex memory relationships using a knowledge graph
- **Semantic search** — Hybrid search based on vector embeddings (vector + keyword + graph traversal)
- **16 search strategies** — Advanced search supports multiple reranking methods such as RRF, MMR, and Cross-Encoder
- **Multiple LLM providers** — Supports Ollama (local), GLM (Zhipu AI, free), GROQ (high-speed inference), OpenRouter (aggregates models from many vendors), and DeepSeek, switchable with a single environment variable
- **Embedding decoupled from LLM** — Use `EMBEDDING_PROVIDER` to independently specify the embedder; cloud LLMs automatically fall back to local `bge-m3`
- **Dual-model routing** — In Ollama mode, complex tasks use the main model while simple tasks automatically switch to the small model for better performance
- **Smart content chunking** — Long text is automatically split into segments to reduce LLM load (configurable threshold)
- **Background memory processing** — Memory additions can run in the background, with MCP calls returning immediately
- **Memory deduplication** — Automatically detects highly similar existing memories to avoid duplicate storage
- **Conflict detection** — Detects contradictory facts between two entities, identifying invalidated versus valid information
- **Community detection** — Automatically clusters related entities using the Label Propagation algorithm
- **Importance tracking** — Automatically records entity access frequency and ranks search results by importance
- **Smart forgetting** — Identifies and cleans up stale, low-access memories to keep the graph lean
- **Bulk import** — Submit multiple memories at once, ideal for large-scale data migration
- **Structured triplets** — Directly add "subject-relation-object" entries, skipping LLM extraction for instant completion
- **Web management interface** — Built-in dashboard, browsing, search, knowledge graph visualization, AI Q&A, and community browsing
- **Internationalization (i18n)** — Response messages support 30+ locales (including zh-TW / en / zh-CN / ja / pt-BR / ko / es / de / fr, etc.); MCP tools follow `SERVER_LANG`, while the REST API automatically negotiates based on the HTTP `Accept-Language` header
- **Dark/light themes** — The Web interface supports theme switching
- **Safe mode** — Optional fast memory addition that skips entity extraction
- **Docker support** — Built-in Dockerfile for containerized deployment
- **Concurrency safety** — asyncio.Lock protects initialization, preventing race conditions
- **Layered health checks** — `/health` (liveness) + `/health/ready` (readiness)

## System Requirements

| Item | Requirement |
|------|------|
| Python | 3.10+ (3.11+ recommended) |
| Neo4j | 4.0+ (`bolt://localhost:7687`) |
| LLM provider | Ollama / GLM / GROQ / OpenRouter / DeepSeek (choose one of five) |
| Node.js | 18+ (only used for PM2 background execution, optional) |
| Disk space | ~3GB (Ollama models + Neo4j data) |

### Choosing an LLM Provider

Switch via the `LLM_PROVIDER` environment variable (`ollama` / `glm` / `groq` / `openrouter` / `deepseek`):

| Provider | Characteristics | LLM model | Embedding | Suitable scenario |
|--------|------|----------|-----------|----------|
| **Ollama** (default) | Fully local, data never leaves the machine | `qwen2.5:3b` | `bge-m3` (excellent for Chinese + RAG) | Has GPU, values privacy |
| **GLM** | Free cloud, stable with no rate limiting | `glm-4-flash` (free) | `embedding-3` | No GPU, search-intensive scenarios |
| **GROQ** | Ultra-high-speed inference | `llama-3.3-70b-versatile` | Falls back to Ollama `bge-m3` | Occasional writes, pursuing quality |
| **OpenRouter** | Aggregates models from many vendors, includes free quota | `stepfun/step-3.5-flash:free`, etc. | Falls back to Ollama `bge-m3` | Want to use a specific cloud model |
| **DeepSeek** | DeepSeek cloud, high cost-effectiveness | `deepseek-v4-flash` / `deepseek-v4-pro` | Falls back to Ollama `bge-m3` | Chinese comprehension, low-cost cloud |

> **Embedding decoupled from LLM**: The embedder is independently specified via `EMBEDDING_PROVIDER` (`ollama` / `glm`); when unset, it follows `LLM_PROVIDER`. In practice only `glm` uses GLM `embedding-3`; everything else (including cloud LLMs that do not provide Embedding, such as GROQ / OpenRouter / DeepSeek) automatically uses Ollama `bge-m3`. **Therefore, when using any cloud LLM, you still need local Ollama to provide the embedding service (unless embedding is also set to glm).**

#### Ollama Mode (Local)

```bash
# Main LLM model (qwen2.5:3b recommended, best balance of speed and stability)
ollama pull qwen2.5:3b

# Embedding model (required, used for vector search)
ollama pull bge-m3
```

> **Notes on model selection**:
> - `qwen2.5:3b` — Recommended, ~2s/call, ~100 t/s, 100% stable for graphiti-core structured output
> - `qwen2.5:7b` — Better results but 5-10x slower, suitable for quality-focused scenarios
> - `qwen2.5:1.5b` — Fastest but **unstable** (only 33% success rate for structured JSON), not recommended

#### GLM Mode (Zhipu AI Cloud)

```bash
# .env settings
LLM_PROVIDER=glm
GLM_API_KEY=your_api_key          # Obtain from https://open.bigmodel.cn
GLM_MODEL=glm-4-flash             # Free model
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768      # Must match the Neo4j vector index dimensions
```

> **GLM performance reference**: Writes ~22s (short text), search ~0.34s, zero Rate Limit errors, 2-5x slower than local Ollama but completely free.

#### GROQ Mode (High-Speed Inference)

```bash
# .env settings
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key         # Obtain from https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile
```

> **Note**: GROQ does not provide an Embedding service; it must be paired with the Ollama embedder (automatic fallback) or you must set `EMBEDDING_PROVIDER` to glm. GROQ has strict Rate Limits, and high-frequency usage will trigger numerous retries.

#### OpenRouter Mode (Aggregating Models from Many Vendors)

```bash
# .env settings
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_api_key       # Obtain from https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free   # Can be changed to any OpenRouter model
```

> **Note**: OpenRouter does not provide Embedding and automatically falls back to Ollama `bge-m3`. See the model list at https://openrouter.ai/models (includes several `:free` free models).

#### DeepSeek Mode (DeepSeek)

```bash
# .env settings
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key         # Obtain from https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash      # Recommended; or deepseek-v4-pro (better results)
```

> **Note**: DeepSeek does not provide Embedding and automatically falls back to Ollama `bge-m3`. `deepseek-chat` / `deepseek-reasoner` will be retired on 2026-07-24; it is recommended to switch to `deepseek-v4-flash` / `deepseek-v4-pro`. DeepSeek strictly requires that the prompt in `json_object` mode contain the string "json"; the client has built-in fallback protection, so no additional configuration is needed.

## Quick Start

### 1. Prerequisites

Confirm Neo4j is running locally, and prepare the corresponding service based on your chosen LLM provider:

```bash
# Confirm Neo4j is running (required)
neo4j status
# Or use Docker: docker run -d -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/your_password neo4j:latest

# Ollama mode: confirm Ollama is running
ollama list
# If not started: ollama serve

# GLM / GROQ mode: only a valid API Key is needed, no local service required
```

### 2. Install Dependencies

```bash
git clone <repo-url>
cd graphiti
uv sync
```

> **Note**: This project uses [uv](https://github.com/astral-sh/uv) to manage dependencies. If not installed: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 3. Configure the Environment

```bash
cp .env.example .env
```

Edit `.env`, and **at minimum** modify the following items:

```bash
NEO4J_PASSWORD=your_actual_password  # Required: Neo4j password
LLM_PROVIDER=ollama                  # ollama / glm / groq / openrouter / deepseek
OLLAMA_MODEL=qwen2.5:3b              # Ollama mode: local LLM model
# GLM_API_KEY=your_key               # GLM mode: Zhipu AI API Key
# GROQ_API_KEY=your_key              # GROQ mode: GROQ API Key
# OPENROUTER_API_KEY=your_key        # OpenRouter mode: API Key
# DEEPSEEK_API_KEY=your_key          # DeepSeek mode: API Key
```

### 4. Start the Service

```bash
# HTTP mode (recommended, includes the Web management interface)
uv run python graphiti_mcp_server.py --transport http --port 8000

# Or use PM2 for background execution (recommended for long-term running)
pm2 start ecosystem.config.cjs
```

### 5. Verify the Service

After starting, you can access the following endpoints:

| Endpoint | Description |
|------|------|
| http://localhost:8000/ | Web management interface |
| http://localhost:8000/mcp | MCP endpoint (for MCP clients to connect) |
| http://localhost:8000/health | Health check (liveness) |
| http://localhost:8000/health/ready | Deep check (includes Neo4j connection) |
| http://localhost:8000/api/stats | REST API statistics |

## Project Structure

```
graphiti/
├── graphiti_mcp_server.py        # Main entry point — MCP tool definitions (19 tools)
├── src/
│   ├── config.py                 # Configuration management (GraphitiConfig, supports JSON/.env layering)
│   ├── web_api.py                # Web management interface REST API (20+ endpoints)
│   ├── ollama_graphiti_client.py  # Ollama LLM client (dual-model routing)
│   ├── glm_client.py             # GLM (Zhipu AI) LLM client (OpenAI-compatible API)
│   ├── openrouter_client.py      # OpenRouter LLM client (aggregates models from many vendors)
│   ├── deepseek_client.py        # DeepSeek LLM client (json_object + fallback json protection)
│   ├── ollama_embedder.py        # Ollama embedding model adapter
│   ├── content_preprocessor.py   # Smart content chunking (auto-segments long text)
│   ├── deduplication.py          # Memory deduplication (cosine similarity comparison)
│   ├── importance.py             # Importance tracking and smart forgetting
│   ├── safe_memory_add.py        # Safe memory addition (skips entity extraction)
│   ├── timezone_utils.py         # Timezone conversion (UTC→local timezone display)
│   ├── i18n.py                   # Backend internationalization (REST follows Accept-Language, MCP follows SERVER_LANG)
│   ├── exceptions.py             # Structured exception handling (12 exception classes)
│   └── logging_setup.py          # Logging system (time-based rotation + performance monitoring)
├── web/                          # Web management interface frontend (SPA, no build)
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js                # REST API wrapper
│       ├── components.js         # UI component rendering (includes community pages)
│       └── app.js                # SPA routing, state management
├── tests/                        # Test suite (183 tests)
│   ├── test_content_preprocessor.py  # Chunking logic tests (17)
│   ├── test_new_features.py      # New feature tests (32)
│   ├── test_i18n.py             # Internationalization tests (37)
│   ├── test_unit.py              # Unit tests
│   ├── test_web_api.py           # Web API tests
│   ├── test_web_ui_features.py   # Web UI feature tests
│   ├── test_integration_manual.py # Manual integration tests
│   └── bench_deepseek_flash_vs_pro.py # DeepSeek flash/pro performance benchmark script
├── tools/                        # Development diagnostic tools
│   ├── status_report.py          # Consolidated status report
│   ├── validate_config.py        # Configuration validation
│   ├── performance_diagnose.py   # Performance diagnosis
│   ├── inspect_schema.py         # Neo4j schema inspection
│   └── batch_reprocess.py        # Batch reprocessing
├── docs/                         # Documentation
├── logs/                         # Logs (time-based rotation, retained 30 days by default)
├── Dockerfile                    # Docker containerized deployment
└── ecosystem.config.cjs          # PM2 configuration
```

## MCP Client Setup

### HTTP Mode (Recommended)

Suitable for MCP clients that support HTTP, such as Claude Code and Cline:

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

### STDIO Mode

Suitable for clients that need to launch the process directly, such as Claude Desktop:

**Configuration file location:**
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

> **Note**: SSE mode (`--transport sse`) is no longer recommended. MCP 1.x has session initialization compatibility issues; please use HTTP mode instead.

## MCP Tools (19 Tools)

### Memory Management (7)

| Tool | Description |
|------|------|
| `add_memory_simple` | Add memory to the knowledge graph (supports background processing, smart chunking, deduplication checking) |
| `add_episode_bulk` | Bulk-add multiple memories (background processing by default) |
| `add_triplet` | Structured triplet addition (skips LLM, completes instantly) |
| `search_memory_nodes` | Search memory nodes (supports 16 search strategies, time filtering) |
| `search_memory_facts` | Search memory facts (supports relation type filtering, time range, validity filtering) |
| `advanced_search` | Advanced search (16 strategies, returns nodes + edges + communities + episodes) |
| `get_episodes` | Retrieve recent memory episodes |

### Knowledge Analysis (3)

| Tool | Description |
|------|------|
| `check_conflicts` | Detect factual conflicts between two entities (valid vs. invalidated) |
| `get_node_edges` | Explore a node's inbound and outbound edge relationships |
| `build_communities` | Trigger community detection and clustering (background processing by default) |

### Memory Maintenance (2)

| Tool | Description |
|------|------|
| `get_stale_memories` | Query stale, low-access memories |
| `cleanup_stale_memories` | Clean up stale memories (dry_run preview mode by default) |

### Task Management

| Tool | Description |
|------|------|
| `get_memory_task_status` | Query the progress and results of a background memory processing task |

### Deletion and Querying

| Tool | Description |
|------|------|
| `delete_episode` | Delete a memory episode |
| `delete_entity_edge` | Delete an entity edge (relation) |
| `get_entity_edge` | Retrieve detailed information about an entity edge |

### System Management

| Tool | Description |
|------|------|
| `get_status` | Retrieve service status (Neo4j, LLM, embedder) |
| `test_connection` | Test Neo4j / LLM / embedder connections |
| `clear_graph` | Clear the graph database (supports clearing by group_id) |

## Tool Parameters

### add_memory_simple

| Parameter | Type | Required | Default | Description |
|------|------|------|--------|------|
| `name` | string | Y | | Memory name |
| `episode_body` | string | Y | | Memory content (automatically chunked if over 800 characters) |
| `group_id` | string | | `"default"` | Group ID (isolation by project recommended) |
| `source` | string | | `"text"` | Source type: `text` / `json` / `message` |
| `source_description` | string | | `"MCP Server"` | Source description |
| `use_safe_mode` | bool | | `false` | Safe mode (skips entity extraction, fast but memory is not searchable) |
| `background` | bool | | `false` | Background processing (returns task_id immediately, suitable for long text) |
| `force` | bool | | `false` | Skip the deduplication check (force addition) |
| `excluded_entity_types` | list | | | Excluded entity types (reduces unwanted extraction) |

> **Performance tips**:
> - Short text (<800 characters): processed directly, usually completes in 30-40 seconds
> - Long text (>800 characters): automatically split into multiple segments, processed concurrently via `add_episode_bulk` (~33% faster than serial)
> - Use `background=true` to avoid blocking the MCP call, and track progress via `get_memory_task_status`
> - `use_safe_mode=true` completes instantly but the memory cannot be found by search tools
> - When deduplication is enabled, highly similar memories will be warned (`force=true` to skip)

### add_episode_bulk

| Parameter | Type | Required | Default | Description |
|------|------|------|--------|------|
| `episodes` | list | Y | | Memory list, each item containing `name` and `content` |
| `group_id` | string | | `"default"` | Group ID |
| `source` | string | | `"text"` | Source type |
| `background` | bool | | `true` | Background processing (bulk operations are usually time-consuming) |

### add_triplet

| Parameter | Type | Required | Default | Description |
|------|------|------|--------|------|
| `source_name` | string | Y | | Source entity name (e.g., "Alice") |
| `target_name` | string | Y | | Target entity name (e.g., "Google") |
| `relation_name` | string | Y | | Relation name (e.g., "works_at") |
| `fact` | string | Y | | Fact description (e.g., "Alice works at Google") |
| `group_id` | string | | `"default"` | Group ID |
| `source_labels` | list | | | Source entity labels |
| `target_labels` | list | | | Target entity labels |

### search_memory_nodes

| Parameter | Type | Required | Default | Description |
|------|------|------|--------|------|
| `query` | string | Y | | Search keywords (natural language) |
| `max_nodes` | int | | `10` | Maximum number to return |
| `group_ids` | list | | | Group filter (joint search across multiple groups) |
| `entity_types` | list | | | Entity type filter |
| `search_recipe` | string | | | Search strategy (see Advanced Search) |
| `created_after` | string | | | Creation time lower bound (ISO datetime) |
| `created_before` | string | | | Creation time upper bound (ISO datetime) |

### search_memory_facts

| Parameter | Type | Required | Default | Description |
|------|------|------|--------|------|
| `query` | string | Y | | Search keywords |
| `max_facts` | int | | `10` | Maximum number to return |
| `group_ids` | list | | | Group filter |
| `center_node_uuid` | string | | | Center node UUID (explore the relationships of a specific node) |
| `edge_types` | list | | | Relation type filter (e.g., `["works_at"]`) |
| `created_after` | string | | | Creation time lower bound (ISO datetime) |
| `created_before` | string | | | Creation time upper bound (ISO datetime) |
| `only_valid` | bool | | `false` | Return only non-invalidated facts |

### advanced_search

| Parameter | Type | Required | Default | Description |
|------|------|------|--------|------|
| `query` | string | Y | | Search keywords |
| `search_recipe` | string | | `"combined_rrf"` | Search strategy (16 options) |
| `max_results` | int | | `10` | Maximum number to return |
| `group_ids` | list | | | Group filter |
| `center_node_uuid` | string | | | Center node UUID |

**Available search strategies (search_recipe):**

| Category | Strategy | Description |
|------|------|------|
| Combined | `combined_rrf` | Combined RRF fusion (default, recommended) |
| Combined | `combined_mmr` | Combined MMR diversity reranking |
| Combined | `combined_cross_encoder` | Combined Cross-Encoder fine reranking |
| Edge | `edge_rrf` / `edge_mmr` / `edge_cross_encoder` | Edge search (3 rankings) |
| Edge | `edge_node_distance` / `edge_episode_mentions` | Edge search (graph distance / mention count) |
| Node | `node_rrf` / `node_mmr` / `node_cross_encoder` | Node search (3 rankings) |
| Node | `node_node_distance` / `node_episode_mentions` | Node search (graph distance / mention count) |
| Community | `community_rrf` / `community_mmr` / `community_cross_encoder` | Community search |

### check_conflicts

| Parameter | Type | Required | Default | Description |
|------|------|------|--------|------|
| `source_name` | string | Y | | Source entity name |
| `target_name` | string | Y | | Target entity name |
| `group_id` | string | | `"default"` | Group ID |

### get_node_edges

| Parameter | Type | Required | Default | Description |
|------|------|------|--------|------|
| `node_uuid` | string | Y | | Node UUID |
| `include_inbound` | bool | | `true` | Include inbound edges |
| `include_outbound` | bool | | `true` | Include outbound edges |
| `max_edges` | int | | `50` | Maximum number to return |

### build_communities

| Parameter | Type | Required | Default | Description |
|------|------|------|--------|------|
| `group_ids` | list | | | Specify groups (leave empty for all) |
| `background` | bool | | `true` | Background processing |

### get_stale_memories

| Parameter | Type | Required | Default | Description |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Days without access beyond which a memory is considered stale |
| `min_access_count` | int | | `2` | Only included if the access count is below this value |
| `group_id` | string | | | Group filter |
| `limit` | int | | `50` | Maximum number to return |

### cleanup_stale_memories

| Parameter | Type | Required | Default | Description |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Stale days threshold |
| `min_access_count` | int | | `2` | Minimum access count threshold |
| `group_id` | string | | | Group filter |
| `dry_run` | bool | | `true` | Preview mode (does not actually delete) |
| `limit` | int | | `50` | Maximum number to process |

### get_memory_task_status

| Parameter | Type | Required | Description |
|------|------|------|------|
| `task_id` | string | Y | Background task ID (returned by `add_memory_simple(background=true)`) |

## Web Management Interface

Access `http://localhost:8000/` in HTTP mode to use it.

**Features:**
- Dashboard — Statistics for node count, fact count, and memory episode count
- Entity nodes — Browse, filter, vector search
- Fact relationships — Browse, filter, vector search
- Memory episodes — Browse, full-text search, delete
- Community browsing — Community node list, summaries, trigger community building
- Triplet form — Directly add "subject-relation-object" structured knowledge
- Group management — Filter by group, batch delete
- Knowledge graph visualization — Graphical display of node relationships
- AI Q&A — Intelligent question answering based on the knowledge graph
- Quality analysis — Memory quality and coverage analysis
- Theme switching — Dark/light themes

**REST API:**

| Endpoint | Method | Description |
|------|------|------|
| `/api/stats` | GET | Dashboard statistics |
| `/api/groups` | GET | Retrieve all group_ids |
| `/api/nodes` | GET | Browse entity nodes (paginated) |
| `/api/facts` | GET | Browse facts (paginated) |
| `/api/episodes` | GET | Browse memory episodes (paginated) |
| `/api/search/nodes` | GET | Vector search nodes |
| `/api/search/facts` | GET | Vector search facts |
| `/api/search/advanced` | GET | Advanced search (16 strategies) |
| `/api/communities` | GET | Browse community nodes (paginated) |
| `/api/communities/build` | POST | Trigger community building |
| `/api/memory/add-bulk` | POST | Bulk-add memories |
| `/api/memory/add-triplet` | POST | Add a triplet |
| `/api/memory/tasks` | GET | List background tasks (supports status filtering) |
| `/api/memory/tasks/{id}` | GET | Query a single task's status |
| `/api/analytics/stale` | GET | Query stale memories |
| `/api/analytics/cleanup` | POST | Clean up stale memories |
| `/api/nodes/{uuid}` | DELETE | Delete a node |
| `/api/episodes/{uuid}` | DELETE | Delete a memory episode |
| `/api/facts/{uuid}` | DELETE | Delete a fact |
| `/api/groups/{group_id}` | DELETE | Delete an entire group |

## Configuration

### Environment Variables (.env)

Configuration uses a layering mechanism: the JSON config file is the base, and environment variables override individual values.

```bash
# === Required ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password        # Must be changed

# === LLM provider selection ===
LLM_PROVIDER=ollama                 # ollama / glm / groq / openrouter / deepseek

# === Embedding provider (optional, follows LLM_PROVIDER by default) ===
# Only glm uses GLM Embedding; everything else uses Ollama bge-m3
# EMBEDDING_PROVIDER=ollama         # ollama / glm

# === Ollama configuration (used when LLM_PROVIDER=ollama) ===
OLLAMA_MODEL=qwen2.5:3b             # Main model (qwen2.5:3b recommended)
OLLAMA_SMALL_MODEL=qwen2.5:3b       # Small model (for simple tasks, a different model can be chosen)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.1

# === GLM configuration (used when LLM_PROVIDER=glm) ===
GLM_API_KEY=your_api_key            # Obtain from https://open.bigmodel.cn
GLM_MODEL=glm-4-flash               # Free model
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768

# === GROQ configuration (used when LLM_PROVIDER=groq) ===
GROQ_API_KEY=your_api_key           # Obtain from https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile

# === OpenRouter configuration (used when LLM_PROVIDER=openrouter) ===
OPENROUTER_API_KEY=your_api_key     # Obtain from https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free

# === DeepSeek configuration (used when LLM_PROVIDER=deepseek) ===
DEEPSEEK_API_KEY=your_api_key       # Obtain from https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash    # Or deepseek-v4-pro

# === Ollama embedding model (used whenever embedding is not glm) ===
OLLAMA_EMBEDDING_MODEL=bge-m3
OLLAMA_EMBEDDING_DIMENSIONS=768

# === Display and locale (optional) ===
GRAPHITI_DISPLAY_TIMEZONE=Asia/Taipei # Display timezone for timestamps returned by the API (IANA name; storage remains UTC)
SERVER_LANG=zh-TW                     # MCP tool response language (see src/i18n.py for the full locale list); the REST API follows Accept-Language instead

# === Memory performance (optional) ===
GRAPHITI_CHUNK_THRESHOLD=800         # Character count threshold that triggers smart chunking
GRAPHITI_MAX_CHUNK_SIZE=600          # Maximum characters per segment
GRAPHITI_MAX_COROUTINES=10            # Maximum number of concurrent coroutines
GRAPHITI_DEFAULT_BACKGROUND=false    # Whether to process in the background by default

# === Importance tracking and smart forgetting (optional) ===
ENABLE_IMPORTANCE_TRACKING=true      # Enable access tracking
IMPORTANCE_WEIGHT=0.1                # Importance weight
STALE_DAYS_THRESHOLD=30              # Stale days threshold
STALE_MIN_ACCESS_COUNT=2             # Minimum access count

# === Logging ===
LOG_FILE=logs/graphiti_mcp_server.log
LOG_LEVEL=INFO
```

> For the **full list of environment variables**, see `.env.example`

### JSON Configuration File

Suitable for configurations that need version control (environment variables can still override):

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

## PM2 Background Execution

```bash
npm install -g pm2

pm2 start ecosystem.config.cjs      # Start
pm2 status                           # Status
pm2 logs graphiti-mcp-http           # Live logs
pm2 restart graphiti-mcp-http --update-env  # Restart (reload .env)

pm2 save && pm2 startup              # Set up automatic startup on boot
```

> **Tip**: After modifying `.env`, you must restart with the `--update-env` flag, otherwise environment variables will not be updated.

## Docker Deployment

```bash
docker build -t graphiti-mcp .

# Note: The Docker container needs to be able to connect to Neo4j and Ollama
# Using host network is the simplest
docker run -p 8000:8000 --env-file .env --network host graphiti-mcp

# Or explicitly specify external service addresses
docker run -p 8000:8000 \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --env-file .env graphiti-mcp
```

## Testing

```bash
# Run all tests (183, about 1 second)
uv run python -m pytest tests/

# Verbose output
uv run python -m pytest tests/ -v

# Run only specific tests
uv run python -m pytest tests/test_content_preprocessor.py -v
uv run python -m pytest tests/test_new_features.py -v
uv run python -m pytest tests/test_unit.py -v
```

> **Note**: The 3 async tests in `test_integration_manual.py` require `pytest-asyncio` to be installed; without it they will show as Failed but do not affect other tests. `bench_deepseek_flash_vs_pro.py` is a performance benchmark script, not a unit test.

## Troubleshooting

### Neo4j Connection Failure

```bash
neo4j status                              # Check service status
cypher-shell -u neo4j -p your_password    # Confirm the password is correct
curl http://localhost:7474                 # Confirm the HTTP port
```

Common causes:
- Neo4j is not started
- Wrong password (`NEO4J_PASSWORD` in `.env`)
- Port is occupied or blocked by a firewall

### LLM Connection Failure

**Ollama mode:**
```bash
ollama serve                # Start the Ollama service
ollama list                 # Check installed models
ollama pull qwen2.5:3b      # Install the missing model
```

Common causes: Ollama not started, model not installed, insufficient GPU memory

**GLM mode:**
- Confirm `GLM_API_KEY` is correct
- Confirm `GLM_EMBEDDING_DIMENSIONS=768` (must match the Neo4j vector index)
- GLM API endpoint: `https://open.bigmodel.cn/api/paas/v4/`

**GROQ mode:**
- Confirm `GROQ_API_KEY` is correct
- Consider switching to GLM mode if Rate Limits occur frequently
- GROQ does not provide Embedding; ensure the Ollama embedder is available

**OpenRouter mode:**
- Confirm `OPENROUTER_API_KEY` is correct and `OPENROUTER_MODEL` is a valid model ID (see https://openrouter.ai/models)
- Does not provide Embedding; ensure the Ollama embedder is available

**DeepSeek mode:**
- Confirm `DEEPSEEK_API_KEY` is correct
- If `Prompt must contain the word 'json'` appears: this is a hard requirement of DeepSeek's `json_object` mode; the client has built-in fallback protection. If it still appears, confirm you are using the latest version of `src/deepseek_client.py` and restart the service
- Does not provide Embedding; ensure the Ollama embedder is available

### MCP Connection Errors

If `Invalid request parameters` or `Received request before initialization was complete` appears:

1. Confirm you are using HTTP transport mode (**do not use SSE**)
2. Confirm the client is set to `"type": "http"`, `"url": "http://localhost:8000/mcp"`
3. Restart the service: `pm2 restart graphiti-mcp-http --update-env`
4. Run `/mcp` in Claude Code to reconnect

### Slow Memory Addition

- **Ollama**: Check the model size (`qwen2.5:3b` is 5-10x faster than `7b`), and confirm GPU is being used (`ollama ps`)
- **GLM**: Each add_episode requires 10-20+ LLM network round trips; ~22s for short text is normal
- **GROQ**: Rate Limits cause numerous retries; if used frequently, consider switching to GLM or Ollama
- Use `background=true` to avoid blocking
- Lower `GRAPHITI_CHUNK_THRESHOLD` to chunk long text earlier

### PM2 Issues

```bash
pm2 status                                        # Check status
pm2 logs graphiti-mcp-http --err --lines 50        # Error logs
lsof -i :8000                                     # Check port occupancy
pm2 delete graphiti-mcp-http && pm2 start ecosystem.config.cjs  # Full restart
```

## Development Diagnostic Tools

```bash
uv run python tools/status_report.py           # Consolidated status report (Neo4j + Ollama + config)
uv run python tools/validate_config.py         # Validate .env and configuration integrity
uv run python tools/performance_diagnose.py    # LLM performance diagnosis
uv run python tools/inspect_schema.py          # Neo4j index and constraint inspection
uv run python tools/migrate_embeddings.py      # Embedding model migration (regenerate vectors after switching models)
```

### Embedding Model Migration

After switching the embedding model (e.g., `nomic-embed-text` → `bge-m3`), you can use the migration tool to regenerate all existing vectors, ensuring consistent search quality:

```bash
# Preview the number that need migration
uv run python tools/migrate_embeddings.py --dry-run

# Full migration (supports resuming from a checkpoint)
uv run python tools/migrate_embeddings.py

# Migrate only a specified group
uv run python tools/migrate_embeddings.py --group-id myproject

# Continue from a checkpoint (rerun after an interruption)
uv run python tools/migrate_embeddings.py --resume
```

> **Compatibility**: `bge-m3` is natively 1024-dimensional; the system automatically truncates it to 768 dimensions to be compatible with the existing Neo4j vector index. Data before and after migration can coexist, but a full migration is recommended for the best search quality.

## Documentation

- [Instructions for Using the Tools](../使用工具的指令.md) — MCP tool usage guide and best practices
- [Graphiti Memory Rules](../graphiti-memory-rules.md) — Explanation of the memory rules

## License

MIT License
