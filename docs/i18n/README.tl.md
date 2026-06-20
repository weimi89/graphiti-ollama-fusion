# Graphiti MCP Server

Serbisyo ng memorya ng knowledge graph — isang MCP server na nag-iintegrate ng maraming LLM provider (Ollama / GLM / GROQ / OpenRouter / DeepSeek) at ng Neo4j graph database.

Binuo bilang ekstensiyon batay sa [getzep/graphiti](https://github.com/getzep/graphiti), sinusuportahan ang flexible na paglipat sa pagitan ng lokal na Ollama at cloud LLM, at maaaring tukuyin nang hiwalay ang Embedding provider (hiwalay sa LLM).

## Mga Tampok na Katangian

- **Matalinong pamamahala ng memorya** — Gumagamit ng knowledge graph upang mag-imbak at kumuha ng masalimuot na relasyon ng memorya
- **Semantic na paghahanap** — Hybrid search batay sa vector embedding (vector + keyword + graph traversal)
- **16 na estratehiya ng paghahanap** — Sinusuportahan ng advanced search ang iba't ibang paraan ng reranking tulad ng RRF, MMR, Cross-Encoder, atbp.
- **Maraming LLM provider** — Sinusuportahan ang Ollama (lokal), GLM (libre ng Zhipu AI), GROQ (mataas na bilis na inference), OpenRouter (pinagsasama ang mga modelo ng iba't ibang kompanya), DeepSeek (深度求索), at maaaring lumipat nang one-click sa pamamagitan ng environment variables
- **Hiwalayan ng Embedding at LLM** — Maaaring tukuyin nang hiwalay ang embedder gamit ang `EMBEDDING_PROVIDER`, awtomatikong bumabalik ang cloud LLM sa lokal na `bge-m3`
- **Pagbabahagi sa dalawang modelo** — Sa Ollama mode, gumagamit ng pangunahing modelo ang masalimuot na mga gawain, awtomatikong lumilipat sa maliit na modelo ang mga simpleng gawain upang mapabuti ang performance
- **Matalinong paghahati ng nilalaman** — Awtomatikong pinaghahati ng bahagi-bahagi ang mahabang teksto, binabawasan ang load ng LLM (maaaring i-configure ang threshold)
- **Background na pagproseso ng memorya** — Maaaring tumakbo sa background ang pagdaragdag ng memorya, agad na bumabalik ang tawag ng MCP; ang estado ng gawain ay pinapanatili sa SQLite, awtomatikong naibabalik ang mga hindi pa natapos na gawain pagkatapos mag-restart
- **Pag-aalis ng duplikadong memorya** — Awtomatikong tinutukoy ang mga umiiral na memorya na lubos na magkapareho, iniiwasan ang paulit-ulit na pag-iimbak
- **Pagtukoy ng salungatan** — Tinutukoy ang magkasalungat na katotohanan sa pagitan ng dalawang entity, kinikilala ang impormasyong wala na sa bisa at may bisa pa
- **Pagtukoy ng komunidad** — Awtomatikong pinagsasama-sama ang mga kaugnay na entity batay sa Label Propagation algorithm
- **Pagsubaybay sa kahalagahan** — Awtomatikong nirerekord ang dalas ng pag-access sa entity, inaayos ang resulta ng paghahanap ayon sa kahalagahan
- **Matalinong paglimot** — Tinutukoy at nililinis ang lipas na, mababang-access na memorya, pinapanatiling makinis ang graph
- **Bulk na pag-import** — Nagsusumite ng maraming memorya nang sabay-sabay, angkop para sa malakihang paglilipat ng datos
- **Structured na triple** — Direktang nagdaragdag ng "subject-relation-object", nilalaktawan ang pagkuha ng LLM, natatapos sa ilang segundo
- **Web management interface** — May built-in na dashboard, pag-browse, paghahanap, visualization ng knowledge graph, AI Q&A, pag-browse ng komunidad, pagpapanatili ng kalidad, bulk na pag-import, at runtime na pagsasaayos
- **Maraming wika (i18n)** — Sinusuportahan ng mga mensahe ng tugon ang 33 na wika (kabilang ang zh-TW / en / zh-CN / ja / pt-BR / ko / es / de / fr atbp.; zh-TW/en/zh-CN/ja ay nakasulat ng kamay, ang iba ay ibinibigay ng generated layer); ang MCP tools ay batay sa `SERVER_LANG`, ang REST API ay awtomatikong nakikipag-ayos batay sa HTTP `Accept-Language`
- **Madilim/maliwanag na tema** — Sinusuportahan ng Web interface ang paglipat ng tema
- **Safe mode** — Maaaring piliin ang mabilis na pagdaragdag ng memorya na nilalaktawan ang pagkuha ng entity
- **Suporta sa Docker** — May built-in na Dockerfile, sinusuportahan ang containerized deployment
- **Ligtas sa concurrency** — Pinoprotektahan ng asyncio.Lock ang initialization, pinipigilan ang race condition
- **Layered na health check** — `/health` (liveness) + `/health/ready` (readiness)

## Mga Kinakailangan ng Sistema

| Item | Kinakailangan |
|------|------|
| Python | 3.10+ (inirerekomenda ang 3.11+) |
| Neo4j | 4.0+ (`bolt://localhost:7687`) |
| LLM provider | Ollama / GLM / GROQ / OpenRouter / DeepSeek (pumili ng isa sa lima) |
| Node.js | 18+ (gamit lamang para sa PM2 background execution, opsiyonal) |
| Espasyo sa disk | ~3GB (Ollama models + Neo4j data) |

### Pagpili ng LLM Provider

Lumipat sa pamamagitan ng `LLM_PROVIDER` environment variable (`ollama` / `glm` / `groq` / `openrouter` / `deepseek`):

| Provider | Katangian | LLM Model | Embedding | Angkop na Sitwasyon |
|--------|------|----------|-----------|----------|
| **Ollama** (default) | Ganap na lokal, hindi umaalis ang datos sa makina | `qwen2.5:3b` | `bge-m3` (mahusay sa Chinese + RAG) | May GPU, pinahahalagahan ang privacy |
| **GLM** | Libreng cloud, matatag na walang limitasyon | `glm-4-flash` (libre) | `embedding-3` | Walang GPU, sitwasyon na masinsinan sa paghahanap |
| **GROQ** | Napakabilis na inference | `llama-3.3-70b-versatile` | Bumabalik sa Ollama `bge-m3` | Paminsanang pagsulat, hinahabol ang kalidad |
| **OpenRouter** | Pinagsasama ang mga modelo ng iba't ibang kompanya, may libreng quota | `stepfun/step-3.5-flash:free` atbp. | Bumabalik sa Ollama `bge-m3` | Gustong gumamit ng partikular na cloud model |
| **DeepSeek** | Cloud ng 深度求索, mataas na halaga-sa-presyo | `deepseek-v4-flash` / `deepseek-v4-pro` | Bumabalik sa Ollama `bge-m3` | Pag-unawa sa Chinese, mababang-gastos na cloud |

> **Hiwalayan ng Embedding at LLM**: Ang embedder ay tinutukoy nang hiwalay sa pamamagitan ng `EMBEDDING_PROVIDER` (`ollama` / `glm`), kapag hindi naitakda ay sumusunod sa `LLM_PROVIDER`. Sa totoo lang, tanging `glm` lamang ang gumagamit ng GLM `embedding-3`, ang iba (kabilang ang GROQ / OpenRouter / DeepSeek at iba pang cloud LLM na hindi nagbibigay ng Embedding) ay awtomatikong gumagamit ng Ollama `bge-m3`. **Kaya kapag gumagamit ng anumang cloud LLM, kailangan pa rin ng lokal na Ollama upang magbigay ng serbisyo ng embedding (maliban kung ang embedding ay naitakda rin sa glm).**

#### Ollama Mode (lokal)

```bash
# Pangunahing LLM model (inirerekomenda ang qwen2.5:3b, pinakamahusay na balanse ng bilis at katatagan)
ollama pull qwen2.5:3b

# Embedding model (kinakailangan, gamit para sa vector search)
ollama pull bge-m3
```

> **Mga dapat tandaan sa pagpili ng modelo**:
> - `qwen2.5:3b` — Inirerekomenda, ~2s/call, ~100 t/s, 100% matatag ang structured output ng graphiti-core
> - `qwen2.5:7b` — Mas mahusay ang resulta ngunit 5-10 beses na mas mabagal, angkop sa sitwasyong humahabol ng kalidad
> - `qwen2.5:1.5b` — Pinakamabilis ngunit **hindi matatag** (33% lamang ang tagumpay sa structured JSON), hindi inirerekomenda

#### GLM Mode (cloud ng Zhipu AI)

```bash
# .env na setting
LLM_PROVIDER=glm
GLM_API_KEY=your_api_key          # Kunin mula sa https://open.bigmodel.cn
GLM_MODEL=glm-4-flash             # Libreng modelo
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768      # Kailangang tugma sa dimensyon ng Neo4j vector index
```

> **Sanggunian sa performance ng GLM**: Pagsulat ~22s (maikling teksto), paghahanap ~0.34s, walang Rate Limit error, 2-5 beses na mas mabagal kaysa lokal na Ollama ngunit ganap na libre.

#### GROQ Mode (mataas na bilis na inference)

```bash
# .env na setting
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key         # Kunin mula sa https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile
```

> **Paalala**: Hindi nagbibigay ang GROQ ng serbisyo ng Embedding, kailangang isama sa Ollama embedder (awtomatikong bumabalik) o itakda ang `EMBEDDING_PROVIDER` sa glm. May mahigpit na Rate Limit ang GROQ, mag-uudyok ng maraming retry ang madalas na paggamit.

#### OpenRouter Mode (pinagsasama ang mga modelo ng iba't ibang kompanya)

```bash
# .env na setting
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_api_key       # Kunin mula sa https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free   # Maaaring palitan ng anumang OpenRouter model
```

> **Paalala**: Hindi nagbibigay ang OpenRouter ng Embedding, awtomatikong bumabalik sa Ollama `bge-m3`. Tingnan ang listahan ng mga modelo sa https://openrouter.ai/models (kabilang ang maraming `:free` na libreng modelo).

#### DeepSeek Mode (深度求索)

```bash
# .env na setting
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key         # Kunin mula sa https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash      # Inirerekomenda; o deepseek-v4-pro (mas mahusay ang resulta)
```

> **Paalala**: Hindi nagbibigay ang DeepSeek ng Embedding, awtomatikong bumabalik sa Ollama `bge-m3`. Ang `deepseek-chat` / `deepseek-reasoner` ay aalisin sa 2026-07-24, inirerekomendang lumipat sa `deepseek-v4-flash` / `deepseek-v4-pro`. Mahigpit na kinakailangan ng DeepSeek na ang prompt sa `json_object` mode ay maglaman ng string na "json", may built-in nang panangga ang kliyente, hindi na kailangan ng karagdagang setting.

## Mabilis na Pagsisimula

### 1. Paghahanda Bago Magsimula

Kumpirmahin na tumatakbo na ang Neo4j sa lokal na makina, at maghanda ng kaukulang serbisyo batay sa napiling LLM provider:

```bash
# Kumpirmahin na tumatakbo ang Neo4j (kinakailangan)
neo4j status
# O gumamit ng Docker: docker run -d -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/your_password neo4j:latest

# Ollama mode: kumpirmahin na tumatakbo ang Ollama
ollama list
# Kung hindi pa nakasimula: ollama serve

# GLM / GROQ mode: kailangan lamang ng valid na API Key, walang kailangang lokal na serbisyo
```

### 2. I-install ang mga Dependency

```bash
git clone <repo-url>
cd graphiti
uv sync
```

> **Paalala**: Gumagamit ang proyektong ito ng [uv](https://github.com/astral-sh/uv) upang pamahalaan ang mga dependency. Kung hindi pa nai-install: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 3. I-configure ang Environment

```bash
cp .env.example .env
```

I-edit ang `.env`, **kahit paano** ay kailangang baguhin ang mga sumusunod na item:

```bash
NEO4J_PASSWORD=your_actual_password  # Kinakailangan: password ng Neo4j
LLM_PROVIDER=ollama                  # ollama / glm / groq / openrouter / deepseek
OLLAMA_MODEL=qwen2.5:3b              # Ollama mode: lokal na LLM model
# GLM_API_KEY=your_key               # GLM mode: API Key ng Zhipu AI
# GROQ_API_KEY=your_key              # GROQ mode: GROQ API Key
# OPENROUTER_API_KEY=your_key        # OpenRouter mode: API Key
# DEEPSEEK_API_KEY=your_key          # DeepSeek mode: API Key
```

### 4. Simulan ang Serbisyo

```bash
# HTTP mode (inirerekomenda, kasama ang Web management interface)
uv run python graphiti_mcp_server.py --transport http --port 8000

# O gumamit ng PM2 background execution (inirerekomenda para sa matagalang pagtakbo)
pm2 start ecosystem.config.cjs
```

### 5. I-verify ang Serbisyo

Pagkatapos magsimula, maaaring ma-access ang mga sumusunod na endpoint:

| Endpoint | Paliwanag |
|------|------|
| http://localhost:8000/ | Web management interface |
| http://localhost:8000/mcp | MCP endpoint (para sa pagkonekta ng MCP client) |
| http://localhost:8000/health | Health check (liveness) |
| http://localhost:8000/health/ready | Malalim na pagsusuri (kasama ang koneksyon sa Neo4j) |
| http://localhost:8000/api/stats | REST API statistics |

## Istruktura ng Proyekto

```
graphiti/
├── graphiti_mcp_server.py        # Pangunahing entry — kahulugan ng MCP tools (19 na tool)
├── src/
│   ├── config.py                 # Pamamahala ng konfigurasyon (GraphitiConfig, sinusuportahan ang JSON/.env na layering)
│   ├── web_api.py                # REST API ng Web management interface (30+ na endpoint)
│   ├── ollama_graphiti_client.py  # Ollama LLM client (pagbabahagi sa dalawang modelo)
│   ├── openai_compat_client.py   # OpenAI-compatible LLM base class (json_object + simplified schema + json fallback protection)
│   ├── glm_client.py             # GLM (Zhipu AI) LLM client (nagmamana sa OpenAICompatClient)
│   ├── openrouter_client.py      # OpenRouter LLM client (nagmamana sa OpenAICompatClient)
│   ├── deepseek_client.py        # DeepSeek LLM client (nagmamana sa OpenAICompatClient)
│   ├── ollama_embedder.py        # Ollama embedding model adapter
│   ├── content_preprocessor.py   # Matalinong paghahati ng nilalaman (awtomatikong paghahati ng mahabang teksto)
│   ├── deduplication.py          # Pag-aalis ng duplikadong memorya (paghahambing ng cosine similarity)
│   ├── importance.py             # Pagsubaybay sa kahalagahan at matalinong paglimot
│   ├── safe_memory_add.py        # Ligtas na pagdaragdag ng memorya (nilalaktawan ang pagkuha ng entity)
│   ├── task_store.py             # SQLite persistence ng background task (TaskStore)
│   ├── timezone_utils.py         # Pag-convert ng timezone (pagpapakita ng UTC→lokal na timezone)
│   ├── i18n.py                   # Backend na maraming wika (REST batay sa Accept-Language, MCP batay sa SERVER_LANG)
│   ├── i18n_generated.py         # Awtomatikong nabuo na mga override ng wika (GENERATED_MESSAGE_OVERRIDES)
│   ├── exceptions.py             # Structured na paghawak ng exception (12 na klase ng exception)
│   └── logging_setup.py          # Sistema ng log (time rotation + performance monitoring)
├── web/                          # Frontend ng Web management interface (SPA, walang build)
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js                # REST API wrapper
│       ├── components.js         # Pag-render ng UI component (kasama ang pahina ng komunidad)
│       └── app.js                # SPA routing, pamamahala ng estado
├── tests/                        # Test suite (203 na test)
│   ├── test_content_preprocessor.py  # Test ng lohika ng paghahati (17 na test)
│   ├── test_new_features.py      # Test ng bagong tampok (32 na test)
│   ├── test_i18n.py             # Test ng maraming wika (57 na test)
│   ├── test_unit.py              # Unit test
│   ├── test_web_api.py           # Web API test
│   ├── test_web_ui_features.py   # Test ng tampok ng Web UI
│   ├── test_integration_manual.py # Manwal na integration test
│   └── bench_deepseek_flash_vs_pro.py # DeepSeek flash/pro performance benchmark script
├── tools/                        # Mga tool sa pag-develop at pag-diagnose
│   ├── status_report.py          # Pinag-isang ulat ng estado
│   ├── validate_config.py        # Pag-validate ng konfigurasyon
│   ├── performance_diagnose.py   # Pag-diagnose ng performance
│   ├── inspect_schema.py         # Pagsusuri ng istruktura ng Neo4j
│   ├── batch_reprocess.py        # Batch na muling pagproseso
│   └── migrate_embeddings.py     # Paglilipat ng Embedding model
├── docs/                         # Dokumentasyon
├── logs/                         # Log (time rotation, default na pinapanatili ng 30 araw)
├── Dockerfile                    # Docker containerized deployment
└── ecosystem.config.cjs          # Konfigurasyon ng PM2
```

## Setting ng MCP Client

### HTTP Mode (inirerekomenda)

Angkop para sa Claude Code, Cline, at iba pang MCP client na sumusuporta sa HTTP:

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

Angkop para sa Claude Desktop at iba pang client na kailangang direktang magsimula ng proseso:

**Lokasyon ng configuration file:**
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

> **Paalala**: Hindi na inirerekomenda ang SSE mode (`--transport sse`). May isyu ng compatibility sa session initialization ang MCP 1.x, pakipalitan ng HTTP mode.

## MCP Tools (19 na tool)

### Pamamahala ng Memorya (7 na tool)

| Tool | Paliwanag |
|------|------|
| `add_memory_simple` | Magdagdag ng memorya sa knowledge graph (sinusuportahan ang background processing, matalinong paghahati, pagsusuri ng duplikasyon) |
| `add_episode_bulk` | Bulk na pagdaragdag ng maraming memorya (default na background processing) |
| `add_triplet` | Structured na pagdaragdag ng triple (nilalaktawan ang LLM, natatapos sa ilang segundo) |
| `search_memory_nodes` | Maghanap ng mga memory node (sinusuportahan ang 16 na estratehiya ng paghahanap, pag-filter ayon sa oras) |
| `search_memory_facts` | Maghanap ng mga memory fact (sinusuportahan ang pag-filter ng uri ng relasyon, saklaw ng oras, pag-filter ng bisa) |
| `advanced_search` | Advanced search (16 na estratehiya, ibinabalik ang node+edge+komunidad+episode) |
| `get_episodes` | Kunin ang pinakabagong mga memory episode |

### Pagsusuri ng Kaalaman (3 na tool)

| Tool | Paliwanag |
|------|------|
| `check_conflicts` | Tukuyin ang salungatan ng katotohanan sa pagitan ng dalawang entity (may bisa vs wala na sa bisa) |
| `get_node_edges` | Tuklasin ang mga inbound at outbound edge na relasyon ng node |
| `build_communities` | I-trigger ang pagtukoy at pagsasama-sama ng komunidad (default na background processing) |

### Pagpapanatili ng Memorya (2 na tool)

| Tool | Paliwanag |
|------|------|
| `get_stale_memories` | Maghanap ng lipas na, mababang-access na memorya |
| `cleanup_stale_memories` | Linisin ang lipas na memorya (default na dry_run preview mode) |

### Pamamahala ng Gawain

| Tool | Paliwanag |
|------|------|
| `get_memory_task_status` | Suriin ang progreso at resulta ng background memory processing task |

### Pagbura at Pagtatanong

| Tool | Paliwanag |
|------|------|
| `delete_episode` | Burahin ang memory episode |
| `delete_entity_edge` | Burahin ang entity edge (relasyon) |
| `get_entity_edge` | Kunin ang detalyadong impormasyon ng entity edge |

### Pamamahala ng Sistema

| Tool | Paliwanag |
|------|------|
| `get_status` | Kunin ang estado ng serbisyo (Neo4j, LLM, embedder) |
| `test_connection` | Subukan ang koneksyon ng Neo4j / LLM / embedder |
| `clear_graph` | Linisin ang graph database (sinusuportahan ang paglilinis ayon sa group_id) |

## Mga Parameter ng Tool

### add_memory_simple

| Parameter | Uri | Kinakailangan | Default na Halaga | Paliwanag |
|------|------|------|--------|------|
| `name` | string | Y | | Pangalan ng memorya |
| `episode_body` | string | Y | | Nilalaman ng memorya (awtomatikong hinahati kung lampas sa 800 character) |
| `group_id` | string | | `"default"` | Group ID (inirerekomendang ihiwalay ayon sa proyekto) |
| `source` | string | | `"text"` | Uri ng pinagmulan: `text` / `json` / `message` |
| `source_description` | string | | `"MCP Server"` | Paglalarawan ng pinagmulan |
| `use_safe_mode` | bool | | `false` | Safe mode (nilalaktawan ang pagkuha ng entity, mabilis ngunit hindi mahahanap ang memorya) |
| `background` | bool | | `false` | Background processing (agad na nagbabalik ng task_id, angkop sa mahabang teksto) |
| `force` | bool | | `false` | Laktawan ang pagsusuri ng duplikasyon (sapilitang pagdaragdag) |
| `excluded_entity_types` | list | | | Mga uri ng entity na hindi isasama (binabawasan ang hindi kailangang pagkuha) |

> **Tip sa performance**:
> - Maikling teksto (<800 character): direktang pinoproseso, karaniwang natatapos sa 30-40 segundo
> - Mahabang teksto (>800 character): awtomatikong hinahati sa maraming bahagi, gumagamit ng `add_episode_bulk` na concurrent processing (~33% na mas mabilis kaysa serial)
> - Ang paggamit ng `background=true` ay umiiwas sa pag-block ng tawag ng MCP, subaybayan ang progreso sa pamamagitan ng `get_memory_task_status`
> - Ang `use_safe_mode=true` ay natatapos sa ilang segundo ngunit hindi mahahanap ng search tool ang memorya
> - Kapag pinagana ang pag-aalis ng duplikasyon, babalaan ang mga lubos na magkaparehong memorya (`force=true` ang maaaring lumaktaw)

### add_episode_bulk

| Parameter | Uri | Kinakailangan | Default na Halaga | Paliwanag |
|------|------|------|--------|------|
| `episodes` | list | Y | | Listahan ng memorya, bawat item ay may `name` at `content` |
| `group_id` | string | | `"default"` | Group ID |
| `source` | string | | `"text"` | Uri ng pinagmulan |
| `background` | bool | | `true` | Background processing (karaniwang matagal ang bulk) |

### add_triplet

| Parameter | Uri | Kinakailangan | Default na Halaga | Paliwanag |
|------|------|------|--------|------|
| `source_name` | string | Y | | Pangalan ng source entity (hal. "Alice") |
| `target_name` | string | Y | | Pangalan ng target entity (hal. "Google") |
| `relation_name` | string | Y | | Pangalan ng relasyon (hal. "works_at") |
| `fact` | string | Y | | Paglalarawan ng katotohanan (hal. "Alice works at Google") |
| `group_id` | string | | `"default"` | Group ID |
| `source_labels` | list | | | Mga label ng source entity |
| `target_labels` | list | | | Mga label ng target entity |

### search_memory_nodes

| Parameter | Uri | Kinakailangan | Default na Halaga | Paliwanag |
|------|------|------|--------|------|
| `query` | string | Y | | Keyword ng paghahanap (natural na wika) |
| `max_nodes` | int | | `10` | Maximum na bilang ng ibabalik |
| `group_ids` | list | | | Pag-filter ng grupo (pinagsamang paghahanap sa maraming group) |
| `entity_types` | list | | | Pag-filter ng uri ng entity |
| `search_recipe` | string | | | Estratehiya ng paghahanap (tingnan ang advanced search) |
| `created_after` | string | | | Pinakamababang oras ng paglikha (ISO datetime) |
| `created_before` | string | | | Pinakamataas na oras ng paglikha (ISO datetime) |

### search_memory_facts

| Parameter | Uri | Kinakailangan | Default na Halaga | Paliwanag |
|------|------|------|--------|------|
| `query` | string | Y | | Keyword ng paghahanap |
| `max_facts` | int | | `10` | Maximum na bilang ng ibabalik |
| `group_ids` | list | | | Pag-filter ng grupo |
| `center_node_uuid` | string | | | UUID ng center node (tuklasin ang relasyon ng partikular na node) |
| `edge_types` | list | | | Pag-filter ng uri ng relasyon (hal. `["works_at"]`) |
| `created_after` | string | | | Pinakamababang oras ng paglikha (ISO datetime) |
| `created_before` | string | | | Pinakamataas na oras ng paglikha (ISO datetime) |
| `only_valid` | bool | | `false` | Ibalik lamang ang mga katotohanang may bisa pa |

### advanced_search

| Parameter | Uri | Kinakailangan | Default na Halaga | Paliwanag |
|------|------|------|--------|------|
| `query` | string | Y | | Keyword ng paghahanap |
| `search_recipe` | string | | `"combined_rrf"` | Estratehiya ng paghahanap (16 na mapagpipilian) |
| `max_results` | int | | `10` | Maximum na bilang ng ibabalik |
| `group_ids` | list | | | Pag-filter ng grupo |
| `center_node_uuid` | string | | | UUID ng center node |

**Mga magagamit na estratehiya ng paghahanap (search_recipe):**

| Kategorya | Estratehiya | Paliwanag |
|------|------|------|
| Pinagsama | `combined_rrf` | Pinagsamang RRF fusion (default, inirerekomenda) |
| Pinagsama | `combined_mmr` | Pinagsamang MMR diversity reranking |
| Pinagsama | `combined_cross_encoder` | Pinagsamang Cross-Encoder precision ranking |
| Edge | `edge_rrf` / `edge_mmr` / `edge_cross_encoder` | Edge search (3 na uri ng pag-aayos) |
| Edge | `edge_node_distance` / `edge_episode_mentions` | Edge search (graph distance/bilang ng banggit) |
| Node | `node_rrf` / `node_mmr` / `node_cross_encoder` | Node search (3 na uri ng pag-aayos) |
| Node | `node_node_distance` / `node_episode_mentions` | Node search (graph distance/bilang ng banggit) |
| Komunidad | `community_rrf` / `community_mmr` / `community_cross_encoder` | Community search |

### check_conflicts

| Parameter | Uri | Kinakailangan | Default na Halaga | Paliwanag |
|------|------|------|--------|------|
| `source_name` | string | Y | | Pangalan ng source entity |
| `target_name` | string | Y | | Pangalan ng target entity |
| `group_id` | string | | `"default"` | Group ID |

### get_node_edges

| Parameter | Uri | Kinakailangan | Default na Halaga | Paliwanag |
|------|------|------|--------|------|
| `node_uuid` | string | Y | | UUID ng node |
| `include_inbound` | bool | | `true` | Isama ang mga inbound edge |
| `include_outbound` | bool | | `true` | Isama ang mga outbound edge |
| `max_edges` | int | | `50` | Maximum na bilang ng ibabalik |

### build_communities

| Parameter | Uri | Kinakailangan | Default na Halaga | Paliwanag |
|------|------|------|--------|------|
| `group_ids` | list | | | Tukuyin ang grupo (iwanang blanko para sa lahat) |
| `background` | bool | | `true` | Background processing |

### get_stale_memories

| Parameter | Uri | Kinakailangan | Default na Halaga | Paliwanag |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Ilang araw na hindi na-access bago ituring na lipas na |
| `min_access_count` | int | | `2` | Isasama lamang kung mas mababa sa halagang ito ang bilang ng access |
| `group_id` | string | | | Pag-filter ng grupo |
| `limit` | int | | `50` | Maximum na bilang ng ibabalik |

### cleanup_stale_memories

| Parameter | Uri | Kinakailangan | Default na Halaga | Paliwanag |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Threshold ng bilang ng araw ng pagkalipas |
| `min_access_count` | int | | `2` | Threshold ng pinakamababang bilang ng access |
| `group_id` | string | | | Pag-filter ng grupo |
| `dry_run` | bool | | `true` | Preview mode (hindi aktwal na binubura) |
| `limit` | int | | `50` | Maximum na bilang na pinoproseso |

### get_memory_task_status

| Parameter | Uri | Kinakailangan | Paliwanag |
|------|------|------|------|
| `task_id` | string | Y | ID ng background task (ibinabalik ng `add_memory_simple(background=true)`) |

## Web Management Interface

Sa HTTP mode, i-access ang `http://localhost:8000/` upang magamit.

**Mga Tampok:**
- Dashboard — istatistika ng bilang ng node, fact, at memory episode
- Entity node — pag-browse, pag-filter, vector search
- Fact relation — pag-browse, pag-filter, vector search
- Memory episode — pag-browse, full-text search, pagbura
- Pag-browse ng komunidad — listahan ng community node, buod, pag-trigger ng pagbuo ng komunidad
- Triple form — direktang magdagdag ng structured na kaalamang "subject-relation-object"
- Pamamahala ng Group — pag-filter ayon sa grupo, batch na pagbura
- Visualization ng knowledge graph — graphical na pagpapakita ng relasyon ng node
- AI Q&A — matalinong Q&A batay sa knowledge graph
- Pagpapanatili ng kalidad — mga sukatan ng kalidad ng memorya at mga tool sa paglilinis
- Bulk na pag-import — mag-import ng maraming memory episode nang sabay-sabay (JSON, hanggang 500 bawat batch)
- Runtime na pagsasaayos — tingnan ang kasalukuyang epektibong setting, at maaaring ayusin ang ilang parameter nang hindi nagre-restart
- Paglipat ng tema — madilim/maliwanag na tema

**REST API:**

| Endpoint | Method | Paliwanag |
|------|------|------|
| `/api/stats` | GET | Istatistika ng dashboard |
| `/api/groups` | GET | Kunin ang lahat ng group_id |
| `/api/groups/stats` | GET | Istatistika ng node/fact/episode bawat group |
| `/api/nodes` | GET | Mag-browse ng entity node (paginated) |
| `/api/facts` | GET | Mag-browse ng fact (paginated) |
| `/api/episodes` | GET | Mag-browse ng memory episode (paginated) |
| `/api/nodes/{uuid}/relations` | GET | Kunin ang mga inbound/outbound na relasyon ng node |
| `/api/search/nodes` | GET | Vector search ng node |
| `/api/search/facts` | GET | Vector search ng fact |
| `/api/search/episodes` | GET | Maghanap ng memory episode |
| `/api/search/advanced` | GET | Advanced search (16 na estratehiya) |
| `/api/communities` | GET | Mag-browse ng community node (paginated) |
| `/api/communities/build` | POST | I-trigger ang pagbuo ng komunidad |
| `/api/memory/add` | POST | Magdagdag ng isang memorya |
| `/api/memory/add-bulk` | POST | Bulk na pagdaragdag ng memorya |
| `/api/memory/add-triplet` | POST | Magdagdag ng triple |
| `/api/import/episodes` | POST | Bulk na pag-import ng memory episode (JSON, hanggang 500 bawat batch) |
| `/api/memory/tasks` | GET | Ilista ang mga background task (sinusuportahan ang pag-filter ng estado) |
| `/api/memory/tasks/{id}` | GET | Suriin ang estado ng isang task |
| `/api/timeline` | GET | Pag-browse ng timeline |
| `/api/graph/subgraph` | GET | Kunin ang subgraph (visualization) |
| `/api/graph/all` | GET | Kunin ang kumpletong graph (visualization) |
| `/api/ask` | GET | AI Q&A (batay sa graph retrieval) |
| `/api/analytics/top-nodes` | GET | Mga node na may mataas na koneksyon/access |
| `/api/analytics/quality` | GET | Mga sukatan ng kalidad ng knowledge graph |
| `/api/analytics/stale` | GET | Maghanap ng lipas na memorya |
| `/api/analytics/cleanup` | POST | Linisin ang lipas na memorya |
| `/api/config` | GET | Kunin ang kasalukuyang epektibong setting (hindi kasama ang API key) |
| `/api/config` | PATCH | I-update ang mababagong setting sa runtime (epektibo lamang sa kasalukuyang proseso, mare-reset pagkatapos mag-restart) |
| `/api/nodes/{uuid}` | DELETE | Burahin ang node |
| `/api/episodes/{uuid}` | DELETE | Burahin ang memory episode |
| `/api/facts/{uuid}` | DELETE | Burahin ang fact |
| `/api/groups/{group_id}` | DELETE | Burahin ang buong group |

## Konfigurasyon

### Environment Variables (.env)

Gumagamit ang konfigurasyon ng layering mechanism: ang JSON configuration file ang batayan, at ino-override ng environment variables ang mga indibidwal na halaga.

```bash
# === Kinakailangan ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password        # Kailangang baguhin

# === Pagpili ng LLM provider ===
LLM_PROVIDER=ollama                 # ollama / glm / groq / openrouter / deepseek

# === Embedding provider (opsiyonal, default na sumusunod sa LLM_PROVIDER) ===
# Tanging glm lamang ang gumagamit ng GLM Embedding, ang iba ay gumagamit ng Ollama bge-m3
# EMBEDDING_PROVIDER=ollama         # ollama / glm

# === Konfigurasyon ng Ollama (ginagamit kapag LLM_PROVIDER=ollama) ===
OLLAMA_MODEL=qwen2.5:3b             # Pangunahing modelo (inirerekomenda ang qwen2.5:3b)
OLLAMA_SMALL_MODEL=qwen2.5:3b       # Maliit na modelo (para sa simpleng gawain, maaaring ibang modelo)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.1

# === Konfigurasyon ng GLM (ginagamit kapag LLM_PROVIDER=glm) ===
GLM_API_KEY=your_api_key            # Kunin mula sa https://open.bigmodel.cn
GLM_MODEL=glm-4-flash               # Libreng modelo
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768

# === Konfigurasyon ng GROQ (ginagamit kapag LLM_PROVIDER=groq) ===
GROQ_API_KEY=your_api_key           # Kunin mula sa https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile

# === Konfigurasyon ng OpenRouter (ginagamit kapag LLM_PROVIDER=openrouter) ===
OPENROUTER_API_KEY=your_api_key     # Kunin mula sa https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free

# === Konfigurasyon ng DeepSeek (ginagamit kapag LLM_PROVIDER=deepseek) ===
DEEPSEEK_API_KEY=your_api_key       # Kunin mula sa https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash    # O deepseek-v4-pro

# === Ollama embedding model (ginagamit kapag hindi glm ang embedding) ===
OLLAMA_EMBEDDING_MODEL=bge-m3
OLLAMA_EMBEDDING_DIMENSIONS=768

# === Pagpapakita at wika (opsiyonal) ===
GRAPHITI_DISPLAY_TIMEZONE=Asia/Taipei # Display timezone ng timestamp na ibinabalik ng API (IANA name; pinapanatiling UTC ang imbakan)
SERVER_LANG=zh-TW                     # Wika ng tugon ng MCP tools (tingnan ang buong locale sa src/i18n.py); ang REST API ay batay sa Accept-Language

# === Performance ng memorya (opsiyonal) ===
GRAPHITI_CHUNK_THRESHOLD=800         # Threshold ng bilang ng character na nag-tri-trigger ng matalinong paghahati
GRAPHITI_MAX_CHUNK_SIZE=600          # Maximum na bilang ng character bawat bahagi
GRAPHITI_MAX_COROUTINES=10            # Maximum na bilang ng parallel coroutine
GRAPHITI_DEFAULT_BACKGROUND=false    # Kung default na background processing
TASK_DB_PATH=data/tasks.db           # Landas ng SQLite persistence ng background task

# === Pagsubaybay sa kahalagahan at matalinong paglimot (opsiyonal) ===
ENABLE_IMPORTANCE_TRACKING=true      # Paganahin ang pagsubaybay sa access
IMPORTANCE_WEIGHT=0.1                # Timbang ng kahalagahan
STALE_DAYS_THRESHOLD=30              # Threshold ng bilang ng araw ng pagkalipas
STALE_MIN_ACCESS_COUNT=2             # Pinakamababang bilang ng access

# === Log ===
LOG_FILE=logs/graphiti_mcp_server.log
LOG_LEVEL=INFO
```

> **Para sa kumpletong listahan ng environment variables** pakitingnan ang `.env.example`

### JSON Configuration File

Angkop para sa konfigurasyon na nangangailangan ng version control (maaari pa ring i-override ng environment variables):

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

pm2 start ecosystem.config.cjs      # Simulan
pm2 status                           # Estado
pm2 logs graphiti-mcp-http           # Real-time na log
pm2 restart graphiti-mcp-http --update-env  # I-restart (muling i-load ang .env)

pm2 save && pm2 startup              # Itakda ang awtomatikong pagsisimula kapag nag-boot
```

> **Tip**: Pagkatapos baguhin ang `.env`, kailangang gamitin ang flag na `--update-env` upang mag-restart, kung hindi ay hindi mag-a-update ang environment variables.

## Docker Deployment

```bash
docker build -t graphiti-mcp .

# Paalala: Kailangang makakonekta ang Docker container sa Neo4j at Ollama
# Pinakasimple ang paggamit ng host network
docker run -p 8000:8000 --env-file .env --network host graphiti-mcp

# O malinaw na tukuyin ang address ng panlabas na serbisyo
docker run -p 8000:8000 \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --env-file .env graphiti-mcp
```

## Pagsubok

```bash
# Patakbuhin ang lahat ng test (203, mga 1 segundo)
uv run python -m pytest tests/

# Detalyadong output
uv run python -m pytest tests/ -v

# Patakbuhin lamang ang partikular na test
uv run python -m pytest tests/test_content_preprocessor.py -v
uv run python -m pytest tests/test_new_features.py -v
uv run python -m pytest tests/test_unit.py -v
```

> **Paalala**: Ang 3 na async test sa `test_integration_manual.py` ay nangangailangan ng pag-install ng `pytest-asyncio`, kapag wala ito ay ipapakita bilang Failed ngunit hindi makakaapekto sa ibang test. Ang `bench_deepseek_flash_vs_pro.py` ay isang performance benchmark script, hindi unit test.

## Pag-troubleshoot

### Bigo ang Koneksyon sa Neo4j

```bash
neo4j status                              # Suriin ang estado ng serbisyo
cypher-shell -u neo4j -p your_password    # Kumpirmahin na tama ang password
curl http://localhost:7474                 # Kumpirmahin ang HTTP port
```

Mga karaniwang dahilan:
- Hindi nakasimula ang Neo4j
- Maling password (ang `NEO4J_PASSWORD` sa `.env`)
- Nakuha na ang port o naka-block ng firewall

### Bigo ang Koneksyon sa LLM

**Ollama mode:**
```bash
ollama serve                # Simulan ang serbisyo ng Ollama
ollama list                 # Suriin ang mga naka-install na modelo
ollama pull qwen2.5:3b      # I-install ang nawawalang modelo
```

Mga karaniwang dahilan: hindi nakasimula ang Ollama, hindi naka-install ang modelo, kulang ang GPU memory

**GLM mode:**
- Kumpirmahin na tama ang `GLM_API_KEY`
- Kumpirmahin na `GLM_EMBEDDING_DIMENSIONS=768` (kailangang tugma sa Neo4j vector index)
- Endpoint ng GLM API: `https://open.bigmodel.cn/api/paas/v4/`

**GROQ mode:**
- Kumpirmahin na tama ang `GROQ_API_KEY`
- Kapag madalas ang Rate Limit, isaalang-alang ang paglipat sa GLM mode
- Hindi nagbibigay ang GROQ ng Embedding, kailangang tiyakin na magagamit ang Ollama embedder

**OpenRouter mode:**
- Kumpirmahin na tama ang `OPENROUTER_API_KEY`, at na ang `OPENROUTER_MODEL` ay valid na model ID (tingnan ang https://openrouter.ai/models)
- Hindi nagbibigay ng Embedding, kailangang tiyakin na magagamit ang Ollama embedder

**DeepSeek mode:**
- Kumpirmahin na tama ang `DEEPSEEK_API_KEY`
- Kung lumitaw ang `Prompt must contain the word 'json'`: ito ay mahigpit na kinakailangan ng `json_object` mode ng DeepSeek, may built-in nang panangga ang kliyente; kung lumilitaw pa rin, kumpirmahin na ginagamit ang pinakabagong bersyon ng `src/deepseek_client.py` at i-restart ang serbisyo
- Hindi nagbibigay ng Embedding, kailangang tiyakin na magagamit ang Ollama embedder

### Error sa Koneksyon ng MCP

Kung lumitaw ang `Invalid request parameters` o `Received request before initialization was complete`:

1. Kumpirmahin na ginagamit ang HTTP transport mode (**huwag gamitin ang SSE**)
2. Kumpirmahin na naka-set ang client sa `"type": "http"`, `"url": "http://localhost:8000/mcp"`
3. I-restart ang serbisyo: `pm2 restart graphiti-mcp-http --update-env`
4. Patakbuhin ang `/mcp` sa Claude Code upang muling kumonekta

### Mabagal ang Bilis ng Pagdaragdag ng Memorya

- **Ollama**: Suriin ang laki ng modelo (`qwen2.5:3b` ay 5-10 beses na mas mabilis kaysa `7b`), kumpirmahin na gumagamit ng GPU (`ollama ps`)
- **GLM**: Bawat add_episode ay nangangailangan ng 10-20+ na LLM network round-trip, normal lamang ang ~22s para sa maikling teksto
- **GROQ**: Magdudulot ng maraming retry ang Rate Limit, kung madalas ang paggamit ay inirerekomendang lumipat sa GLM o Ollama
- Gamitin ang `background=true` upang umiwas sa pag-block
- Babaan ang `GRAPHITI_CHUNK_THRESHOLD` upang mas maaga mahati ang mahabang teksto

### Mga Isyu sa PM2

```bash
pm2 status                                        # Suriin ang estado
pm2 logs graphiti-mcp-http --err --lines 50        # Error log
lsof -i :8000                                     # Suriin ang paggamit ng port
pm2 delete graphiti-mcp-http && pm2 start ecosystem.config.cjs  # Ganap na i-restart
```

## Mga Tool sa Pag-develop at Pag-diagnose

```bash
uv run python tools/status_report.py           # Pinag-isang ulat ng estado (Neo4j + Ollama + konfigurasyon)
uv run python tools/validate_config.py         # I-validate ang .env at kabuuan ng konfigurasyon
uv run python tools/performance_diagnose.py    # Pag-diagnose ng performance ng LLM
uv run python tools/inspect_schema.py          # Pagsusuri ng index at constraint ng Neo4j
uv run python tools/migrate_embeddings.py      # Paglilipat ng embedding model (muling pagbuo ng vector pagkatapos lumipat ng modelo)
```

### Paglilipat ng Embedding Model

Pagkatapos lumipat ng embedding model (hal. `nomic-embed-text` → `bge-m3`), maaaring gamitin ang migration tool upang muling buuin ang lahat ng umiiral na vector, tinitiyak ang pare-parehong kalidad ng paghahanap:

```bash
# I-preview ang bilang na kailangang ilipat
uv run python tools/migrate_embeddings.py --dry-run

# Buong paglilipat (sinusuportahan ang pagpapatuloy mula sa breakpoint)
uv run python tools/migrate_embeddings.py

# Ilipat lamang ang tinukoy na group
uv run python tools/migrate_embeddings.py --group-id myproject

# Magpatuloy mula sa breakpoint (muling patakbuhin pagkatapos maputol)
uv run python tools/migrate_embeddings.py --resume
```

> **Compatibility**: Ang `bge-m3` ay natural na 1024 na dimensyon, awtomatikong pinuputol ng sistema sa 768 na dimensyon upang maging compatible sa umiiral na Neo4j vector index. Maaaring magkasama ang datos bago at pagkatapos ng paglilipat, ngunit inirerekomendang isagawa ang buong paglilipat upang makamit ang pinakamahusay na kalidad ng paghahanap.

## Dokumentasyon

- [Mga Tagubilin sa Paggamit ng Tool](../使用工具的指令.md) — Gabay sa paggamit ng MCP tools at pinakamahusay na kasanayan
- [Graphiti Memory Rules](../graphiti-memory-rules.md) — Paliwanag ng mga panuntunan ng memorya

## Lisensya

MIT License
