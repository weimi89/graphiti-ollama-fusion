# Graphiti MCP Server

Kunskapsgrafsbaserad minnestjänst — en MCP-server som integrerar flera LLM-leverantörer (Ollama / GLM / GROQ / OpenRouter / DeepSeek) med Neo4j-grafdatabasen.

Utvecklad som en utökning av [getzep/graphiti](https://github.com/getzep/graphiti), med stöd för flexibel växling mellan lokal Ollama och moln-LLM, och möjlighet att ange en Embedding-leverantör separat (frikopplad från LLM).

## Funktioner

- **Intelligent minneshantering** — använder en kunskapsgraf för att lagra och hämta komplexa minnesrelationer
- **Semantisk sökning** — hybridsökning baserad på vektorinbäddningar (vektor + nyckelord + grafgenomgång)
- **16 sökstrategier** — avancerad sökning stöder flera omrankningsmetoder som RRF, MMR, Cross-Encoder med mera
- **Flera LLM-leverantörer** — stöder Ollama (lokal), GLM (Zhipu AI, gratis), GROQ (höghastighetsinferens), OpenRouter (aggregerar modeller från olika leverantörer), DeepSeek (Deep Seek), med växling via en miljövariabel med ett enda kommando
- **Embedding frikopplat från LLM** — du kan ange inbäddaren separat med `EMBEDDING_PROVIDER`; moln-LLM faller automatiskt tillbaka till lokal `bge-m3`
- **Dubbel modellfördelning** — i Ollama-läge används huvudmodellen för komplexa uppgifter, medan enklare uppgifter automatiskt växlar till en mindre modell för bättre prestanda
- **Intelligent innehållssegmentering** — långa texter delas automatiskt upp i segment, vilket minskar LLM-belastningen (tröskelvärde kan konfigureras)
- **Bakgrundsbearbetning av minne** — minnestillägg kan köras i bakgrunden så att MCP-anropet returnerar omedelbart; uppgiftsstatus sparas i SQLite och ofullständiga uppgifter återställs automatiskt efter omstart
- **Minnesdeduplicering** — upptäcker automatiskt befintliga minnen som är mycket lika, för att undvika dubbellagring
- **Konfliktdetektering** — upptäcker motstridiga fakta mellan två entiteter och identifierar inaktuell respektive giltig information
- **Communitydetektering** — klustrar automatiskt relaterade entiteter baserat på Label Propagation-algoritmen
- **Viktighetsspårning** — registrerar automatiskt entiteters åtkomstfrekvens och rankar sökresultaten efter viktighet
- **Intelligent glömska** — identifierar och rensar inaktuella minnen med låg åtkomstfrekvens för att hålla grafen kompakt
- **Bulkimport** — skicka in flera minnen på en gång, lämpligt för migrering av stora datamängder
- **Strukturerade trippletter** — lägg till "subjekt-relation-objekt" direkt, hoppa över LLM-extraktion och slutför på sekunder
- **Webbaserat administrationsgränssnitt** — inbyggd instrumentpanel, bläddring, sökning, visualisering av kunskapsgraf, AI-frågor, communitybläddring, kvalitetsunderhåll, bulkimport och körningsinställningar
- **Internationalisering (i18n)** — svarsmeddelanden stöder 33 språk (inklusive zh-TW / en / zh-CN / ja / pt-BR / ko / es / de / fr m.fl.; zh-TW/en/zh-CN/ja är handskrivna, övriga tillhandahålls av det genererade lagret); MCP-verktyg följer `SERVER_LANG`, REST API förhandlar automatiskt via HTTP `Accept-Language`
- **Mörkt/ljust tema** — webbgränssnittet stöder temaväxling
- **Säkert läge** — alternativ för snabbt minnestillägg som hoppar över entitetsextraktion
- **Docker-stöd** — inbyggd Dockerfile med stöd för containeriserad driftsättning
- **Samtidighetssäkerhet** — asyncio.Lock skyddar initieringen och förhindrar tävlingsvillkor
- **Hälsokontroller i lager** — `/health` (liveness) + `/health/ready` (readiness)

## Systemkrav

| Objekt | Krav |
|------|------|
| Python | 3.10+ (3.11+ rekommenderas) |
| Neo4j | 4.0+ (`bolt://localhost:7687`) |
| LLM-leverantör | Ollama / GLM / GROQ / OpenRouter / DeepSeek (välj en av fem) |
| Node.js | 18+ (endast för PM2-bakgrundskörning, valfritt) |
| Diskutrymme | ~3GB (Ollama-modeller + Neo4j-data) |

### Val av LLM-leverantör

Växla via miljövariabeln `LLM_PROVIDER` (`ollama` / `glm` / `groq` / `openrouter` / `deepseek`):

| Leverantör | Egenskaper | LLM-modell | Embedding | Lämpliga scenarier |
|--------|------|----------|-----------|----------|
| **Ollama** (standard) | Helt lokal, data lämnar aldrig maskinen | `qwen2.5:3b` | `bge-m3` (utmärkt för kinesiska + RAG) | Har GPU, värdesätter integritet |
| **GLM** | Gratis moln, stabilt utan hastighetsbegränsning | `glm-4-flash` (gratis) | `embedding-3` | Ingen GPU, sökintensiva scenarier |
| **GROQ** | Ultrasnabb inferens | `llama-3.3-70b-versatile` | Faller tillbaka till Ollama `bge-m3` | Tillfälliga skrivningar, eftersträvar kvalitet |
| **OpenRouter** | Aggregerar modeller från olika leverantörer, inkl. gratiskvot | `stepfun/step-3.5-flash:free` m.fl. | Faller tillbaka till Ollama `bge-m3` | Vill använda en specifik molnmodell |
| **DeepSeek** | Deep Seek-moln, hög prisprestanda | `deepseek-v4-flash` / `deepseek-v4-pro` | Faller tillbaka till Ollama `bge-m3` | Kinesisk förståelse, lågkostnadsmoln |

> **Embedding frikopplat från LLM**: inbäddaren anges separat via `EMBEDDING_PROVIDER` (`ollama` / `glm`); när den inte är inställd följer den `LLM_PROVIDER`. I praktiken använder endast `glm` GLM `embedding-3`, medan resten (inklusive moln-LLM som GROQ / OpenRouter / DeepSeek som inte erbjuder Embedding) alltid automatiskt använder Ollama `bge-m3`. **Därför behöver du fortfarande lokal Ollama för att tillhandahålla inbäddningstjänsten när du använder någon moln-LLM (om inte embedding också är inställt på glm).**

#### Ollama-läge (lokal)

```bash
# LLM-huvudmodell (qwen2.5:3b rekommenderas, bäst balans mellan hastighet och stabilitet)
ollama pull qwen2.5:3b

# Inbäddningsmodell (obligatorisk, används för vektorsökning)
ollama pull bge-m3
```

> **Att tänka på vid modellval**:
> - `qwen2.5:3b` — rekommenderas, ~2s/anrop, ~100 t/s, 100 % stabil strukturerad utdata i graphiti-core
> - `qwen2.5:7b` — bättre resultat men 5-10 gånger långsammare, lämplig när kvalitet eftersträvas
> - `qwen2.5:1.5b` — snabbast men **instabil** (endast 33 % framgångsfrekvens för strukturerad JSON), rekommenderas inte

#### GLM-läge (Zhipu AI-moln)

```bash
# .env-inställningar
LLM_PROVIDER=glm
GLM_API_KEY=your_api_key          # Hämtas från https://open.bigmodel.cn
GLM_MODEL=glm-4-flash             # Gratis modell
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768      # Måste matcha dimensionen för Neo4j-vektorindexet
```

> **GLM-prestandareferens**: skrivning ~22s (kort text), sökning ~0,34s, noll Rate Limit-fel, 2-5 gånger långsammare än lokal Ollama men helt gratis.

#### GROQ-läge (höghastighetsinferens)

```bash
# .env-inställningar
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key         # Hämtas från https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile
```

> **Obs**: GROQ erbjuder ingen Embedding-tjänst och måste kombineras med Ollama-inbäddaren (automatisk fallback) eller med `EMBEDDING_PROVIDER` inställt på glm. GROQ har strikta Rate Limits och högfrekvent användning utlöser många försök på nytt.

#### OpenRouter-läge (aggregerar modeller från olika leverantörer)

```bash
# .env-inställningar
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_api_key       # Hämtas från https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free   # Kan ändras till valfri OpenRouter-modell
```

> **Obs**: OpenRouter erbjuder ingen Embedding och faller automatiskt tillbaka till Ollama `bge-m3`. Modellistan finns på https://openrouter.ai/models (inklusive flera `:free`-modeller).

#### DeepSeek-läge (Deep Seek)

```bash
# .env-inställningar
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key         # Hämtas från https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash      # Rekommenderas; eller deepseek-v4-pro (bättre resultat)
```

> **Obs**: DeepSeek erbjuder ingen Embedding och faller automatiskt tillbaka till Ollama `bge-m3`. `deepseek-chat` / `deepseek-reasoner` kommer att tas ur drift 2026-07-24; det rekommenderas att byta till `deepseek-v4-flash` / `deepseek-v4-pro`. DeepSeek kräver strikt att prompten i `json_object`-läge innehåller strängen "json"; klienten har inbyggt skyddsmekanism, så ingen ytterligare inställning krävs.

## Snabbstart

### 1. Förberedelser

Bekräfta att Neo4j körs lokalt och förbered motsvarande tjänst beroende på vald LLM-leverantör:

```bash
# Bekräfta att Neo4j körs (obligatoriskt)
neo4j status
# Eller använd Docker: docker run -d -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/your_password neo4j:latest

# Ollama-läge: bekräfta att Ollama körs
ollama list
# Om den inte är startad: ollama serve

# GLM / GROQ-läge: behöver bara en giltig API Key, ingen lokal tjänst krävs
```

### 2. Installera beroenden

```bash
git clone <repo-url>
cd graphiti
uv sync
```

> **Obs**: Detta projekt använder [uv](https://github.com/astral-sh/uv) för att hantera beroenden. Om det inte är installerat: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 3. Konfigurera miljön

```bash
cp .env.example .env
```

Redigera `.env` och ändra **åtminstone** följande objekt:

```bash
NEO4J_PASSWORD=your_actual_password  # Obligatoriskt: Neo4j-lösenord
LLM_PROVIDER=ollama                  # ollama / glm / groq / openrouter / deepseek
OLLAMA_MODEL=qwen2.5:3b              # Ollama-läge: lokal LLM-modell
# GLM_API_KEY=your_key               # GLM-läge: Zhipu AI API Key
# GROQ_API_KEY=your_key              # GROQ-läge: GROQ API Key
# OPENROUTER_API_KEY=your_key        # OpenRouter-läge: API Key
# DEEPSEEK_API_KEY=your_key          # DeepSeek-läge: API Key
```

### 4. Starta tjänsten

```bash
# HTTP-läge (rekommenderas, inkluderar webbaserat administrationsgränssnitt)
uv run python graphiti_mcp_server.py --transport http --port 8000

# Eller använd PM2 för bakgrundskörning (rekommenderas för långvarig drift)
pm2 start ecosystem.config.cjs
```

### 5. Verifiera tjänsten

Efter start kan du nå följande slutpunkter:

| Slutpunkt | Beskrivning |
|------|------|
| http://localhost:8000/ | Webbaserat administrationsgränssnitt |
| http://localhost:8000/mcp | MCP-slutpunkt (för anslutning av MCP-klienter) |
| http://localhost:8000/health | Hälsokontroll (liveness) |
| http://localhost:8000/health/ready | Djupkontroll (inkl. Neo4j-anslutning) |
| http://localhost:8000/api/stats | REST API-statistik |

## Projektstruktur

```
graphiti/
├── graphiti_mcp_server.py        # Huvudingång — MCP-verktygsdefinitioner (19 verktyg)
├── src/
│   ├── config.py                 # Konfigurationshantering (GraphitiConfig, stöder överlagring av JSON/.env)
│   ├── web_api.py                # REST API för webbaserat administrationsgränssnitt (30+ slutpunkter)
│   ├── ollama_graphiti_client.py  # Ollama LLM-klient (dubbel modellfördelning)
│   ├── openai_compat_client.py   # OpenAI-kompatibel LLM-basklass (json_object + förenklat schema + json-skyddsmekanism)
│   ├── glm_client.py             # GLM (Zhipu AI) LLM-klient (ärver OpenAICompatClient)
│   ├── openrouter_client.py      # OpenRouter LLM-klient (ärver OpenAICompatClient)
│   ├── deepseek_client.py        # DeepSeek LLM-klient (ärver OpenAICompatClient)
│   ├── ollama_embedder.py        # Adapter för Ollama-inbäddningsmodell
│   ├── content_preprocessor.py   # Intelligent innehållssegmentering (automatisk segmentering av lång text)
│   ├── deduplication.py          # Minnesdeduplicering (cosinuslikhetsjämförelse)
│   ├── importance.py             # Viktighetsspårning och intelligent glömska
│   ├── safe_memory_add.py        # Säkert minnestillägg (hoppar över entitetsextraktion)
│   ├── task_store.py             # SQLite-persistens för bakgrundsuppgifter (TaskStore)
│   ├── timezone_utils.py         # Tidszonskonvertering (UTC→visning i lokal tidszon)
│   ├── i18n.py                   # Backend-internationalisering (REST följer Accept-Language, MCP följer SERVER_LANG)
│   ├── i18n_generated.py         # Automatiskt genererade språköversättningar (GENERATED_MESSAGE_OVERRIDES)
│   ├── exceptions.py             # Strukturerad undantagshantering (12 undantagsklasser)
│   └── logging_setup.py          # Loggsystem (tidsrotation + prestandaövervakning)
├── web/                          # Frontend för webbaserat administrationsgränssnitt (SPA, ingen build)
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js                # REST API-inkapsling
│       ├── components.js         # Rendering av UI-komponenter (inkl. communitysida)
│       └── app.js                # SPA-routing, tillståndshantering
├── tests/                        # Testsvit (203 tester)
│   ├── test_content_preprocessor.py  # Test av segmenteringslogik (17 st)
│   ├── test_new_features.py      # Test av nya funktioner (32 st)
│   ├── test_i18n.py             # Internationaliseringstest (57 st)
│   ├── test_unit.py              # Enhetstester
│   ├── test_web_api.py           # Web API-tester
│   ├── test_web_ui_features.py   # Test av Web UI-funktioner
│   ├── test_integration_manual.py # Manuella integrationstester
│   └── bench_deepseek_flash_vs_pro.py # Prestandabenchmark-skript för DeepSeek flash/pro
├── tools/                        # Diagnostikverktyg för utveckling
│   ├── status_report.py          # Samlad statusrapport
│   ├── validate_config.py        # Konfigurationsvalidering
│   ├── performance_diagnose.py   # Prestandadiagnostik
│   ├── inspect_schema.py         # Kontroll av Neo4j-struktur
│   ├── batch_reprocess.py        # Bearbetning i batch på nytt
│   └── migrate_embeddings.py     # Migrering av Embedding-modell
├── docs/                         # Dokumentation
├── logs/                         # Loggar (tidsrotation, behålls i 30 dagar som standard)
├── Dockerfile                    # Docker-containeriserad driftsättning
└── ecosystem.config.cjs          # PM2-konfiguration
```

## Inställningar för MCP-klient

### HTTP-läge (rekommenderas)

Lämpligt för MCP-klienter som stöder HTTP, såsom Claude Code, Cline m.fl.:

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

### STDIO-läge

Lämpligt för klienter som behöver starta processen direkt, såsom Claude Desktop:

**Plats för konfigurationsfilen:**
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

> **Obs**: SSE-läge (`--transport sse`) rekommenderas inte längre. MCP 1.x har kompatibilitetsproblem med sessioninitiering; använd HTTP-läget istället.

## MCP-verktyg (19 st)

### Minneshantering (7 st)

| Verktyg | Beskrivning |
|------|------|
| `add_memory_simple` | Lägg till minne till kunskapsgrafen (stöder bakgrundsbearbetning, intelligent segmentering, dedupliceringskontroll) |
| `add_episode_bulk` | Lägg till flera minnen i batch (bakgrundsbearbetning som standard) |
| `add_triplet` | Strukturerat tripplettillägg (hoppar över LLM, slutförs på sekunder) |
| `search_memory_nodes` | Sök minnesnoder (stöder 16 sökstrategier, tidsfiltrering) |
| `search_memory_facts` | Sök minnesfakta (stöder filtrering på relationstyp, tidsintervall, giltighetsfiltrering) |
| `advanced_search` | Avancerad sökning (16 strategier, returnerar noder+kanter+communities+segment) |
| `get_episodes` | Hämta de senaste minnessegmenten |

### Kunskapsanalys (3 st)

| Verktyg | Beskrivning |
|------|------|
| `check_conflicts` | Upptäck faktakonflikter mellan två entiteter (giltig vs inaktuell) |
| `get_node_edges` | Utforska en nods in- och utgående kantrelationer |
| `build_communities` | Utlös communitydetektering och klustring (bakgrundsbearbetning som standard) |

### Minnesunderhåll (2 st)

| Verktyg | Beskrivning |
|------|------|
| `get_stale_memories` | Sök efter inaktuella minnen med låg åtkomstfrekvens |
| `cleanup_stale_memories` | Rensa inaktuella minnen (dry_run-förhandsgranskningsläge som standard) |

### Uppgiftshantering

| Verktyg | Beskrivning |
|------|------|
| `get_memory_task_status` | Fråga om förlopp och resultat för bakgrundsuppgift för minnesbearbetning |

### Borttagning och frågor

| Verktyg | Beskrivning |
|------|------|
| `delete_episode` | Ta bort minnessegment |
| `delete_entity_edge` | Ta bort entitetskant (relation) |
| `get_entity_edge` | Hämta detaljerad information om entitetskant |

### Systemhantering

| Verktyg | Beskrivning |
|------|------|
| `get_status` | Hämta tjänstens status (Neo4j, LLM, inbäddare) |
| `test_connection` | Testa anslutning till Neo4j / LLM / inbäddare |
| `clear_graph` | Rensa grafdatabasen (stöder rensning per group_id) |

## Verktygsparametrar

### add_memory_simple

| Parameter | Typ | Obligatorisk | Standardvärde | Beskrivning |
|------|------|------|--------|------|
| `name` | string | Y | | Minnesnamn |
| `episode_body` | string | Y | | Minnesinnehåll (segmenteras automatiskt över 800 tecken) |
| `group_id` | string | | `"default"` | Grupp-ID (rekommenderas att isolera per projekt) |
| `source` | string | | `"text"` | Källtyp: `text` / `json` / `message` |
| `source_description` | string | | `"MCP Server"` | Källbeskrivning |
| `use_safe_mode` | bool | | `false` | Säkert läge (hoppar över entitetsextraktion, snabbt men minnet kan inte sökas) |
| `background` | bool | | `false` | Bakgrundsbearbetning (returnerar task_id omedelbart, lämpligt för lång text) |
| `force` | bool | | `false` | Hoppa över dedupliceringskontroll (tvinga tillägg) |
| `excluded_entity_types` | list | | | Uteslutna entitetstyper (minskar onödig extraktionsmängd) |

> **Prestandatips**:
> - Kort text (<800 tecken): bearbetas direkt, slutförs vanligtvis på 30-40 sekunder
> - Lång text (>800 tecken): segmenteras automatiskt i flera delar och bearbetas samtidigt med `add_episode_bulk` (~33 % snabbare än seriellt)
> - Använd `background=true` för att undvika att MCP-anropet blockeras; spåra förloppet med `get_memory_task_status`
> - `use_safe_mode=true` slutförs på sekunder men minnet kan inte hittas av sökverktygen
> - När deduplicering är aktiverat varnas det för mycket lika minnen (`force=true` kan hoppa över)

### add_episode_bulk

| Parameter | Typ | Obligatorisk | Standardvärde | Beskrivning |
|------|------|------|--------|------|
| `episodes` | list | Y | | Minneslista, varje post innehåller `name` och `content` |
| `group_id` | string | | `"default"` | Grupp-ID |
| `source` | string | | `"text"` | Källtyp |
| `background` | bool | | `true` | Bakgrundsbearbetning (batch tar vanligtvis tid) |

### add_triplet

| Parameter | Typ | Obligatorisk | Standardvärde | Beskrivning |
|------|------|------|--------|------|
| `source_name` | string | Y | | Namn på källentitet (t.ex. "Alice") |
| `target_name` | string | Y | | Namn på målentitet (t.ex. "Google") |
| `relation_name` | string | Y | | Relationsnamn (t.ex. "works_at") |
| `fact` | string | Y | | Faktabeskrivning (t.ex. "Alice works at Google") |
| `group_id` | string | | `"default"` | Grupp-ID |
| `source_labels` | list | | | Etiketter för källentitet |
| `target_labels` | list | | | Etiketter för målentitet |

### search_memory_nodes

| Parameter | Typ | Obligatorisk | Standardvärde | Beskrivning |
|------|------|------|--------|------|
| `query` | string | Y | | Sökord (naturligt språk) |
| `max_nodes` | int | | `10` | Maximalt antal returnerade |
| `group_ids` | list | | | Gruppfiltrering (kombinerad sökning över flera grupper) |
| `entity_types` | list | | | Filtrering på entitetstyp |
| `search_recipe` | string | | | Sökstrategi (se avancerad sökning) |
| `created_after` | string | | | Nedre gräns för skapandetid (ISO datetime) |
| `created_before` | string | | | Övre gräns för skapandetid (ISO datetime) |

### search_memory_facts

| Parameter | Typ | Obligatorisk | Standardvärde | Beskrivning |
|------|------|------|--------|------|
| `query` | string | Y | | Sökord |
| `max_facts` | int | | `10` | Maximalt antal returnerade |
| `group_ids` | list | | | Gruppfiltrering |
| `center_node_uuid` | string | | | UUID för centernod (utforska en specifik nods relationer) |
| `edge_types` | list | | | Filtrering på relationstyp (t.ex. `["works_at"]`) |
| `created_after` | string | | | Nedre gräns för skapandetid (ISO datetime) |
| `created_before` | string | | | Övre gräns för skapandetid (ISO datetime) |
| `only_valid` | bool | | `false` | Returnera endast icke-inaktuella fakta |

### advanced_search

| Parameter | Typ | Obligatorisk | Standardvärde | Beskrivning |
|------|------|------|--------|------|
| `query` | string | Y | | Sökord |
| `search_recipe` | string | | `"combined_rrf"` | Sökstrategi (16 valbara) |
| `max_results` | int | | `10` | Maximalt antal returnerade |
| `group_ids` | list | | | Gruppfiltrering |
| `center_node_uuid` | string | | | UUID för centernod |

**Tillgängliga sökstrategier (search_recipe):**

| Kategori | Strategi | Beskrivning |
|------|------|------|
| Kombinerad | `combined_rrf` | Kombinerad RRF-fusion (standard, rekommenderas) |
| Kombinerad | `combined_mmr` | Kombinerad MMR-omrankning för mångfald |
| Kombinerad | `combined_cross_encoder` | Kombinerad Cross-Encoder finrankning |
| Kant | `edge_rrf` / `edge_mmr` / `edge_cross_encoder` | Kantsökning (3 rankningssätt) |
| Kant | `edge_node_distance` / `edge_episode_mentions` | Kantsökning (grafavstånd/antal omnämnanden) |
| Nod | `node_rrf` / `node_mmr` / `node_cross_encoder` | Nodsökning (3 rankningssätt) |
| Nod | `node_node_distance` / `node_episode_mentions` | Nodsökning (grafavstånd/antal omnämnanden) |
| Community | `community_rrf` / `community_mmr` / `community_cross_encoder` | Communitysökning |

### check_conflicts

| Parameter | Typ | Obligatorisk | Standardvärde | Beskrivning |
|------|------|------|--------|------|
| `source_name` | string | Y | | Namn på källentitet |
| `target_name` | string | Y | | Namn på målentitet |
| `group_id` | string | | `"default"` | Grupp-ID |

### get_node_edges

| Parameter | Typ | Obligatorisk | Standardvärde | Beskrivning |
|------|------|------|--------|------|
| `node_uuid` | string | Y | | Nod-UUID |
| `include_inbound` | bool | | `true` | Inkludera ingående kanter |
| `include_outbound` | bool | | `true` | Inkludera utgående kanter |
| `max_edges` | int | | `50` | Maximalt antal returnerade |

### build_communities

| Parameter | Typ | Obligatorisk | Standardvärde | Beskrivning |
|------|------|------|--------|------|
| `group_ids` | list | | | Ange grupper (lämna tomt för alla) |
| `background` | bool | | `true` | Bakgrundsbearbetning |

### get_stale_memories

| Parameter | Typ | Obligatorisk | Standardvärde | Beskrivning |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Antal dagar utan åtkomst innan det betraktas som inaktuellt |
| `min_access_count` | int | | `2` | Tas endast med om åtkomstantalet är lägre än detta värde |
| `group_id` | string | | | Gruppfiltrering |
| `limit` | int | | `50` | Maximalt antal returnerade |

### cleanup_stale_memories

| Parameter | Typ | Obligatorisk | Standardvärde | Beskrivning |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Tröskelvärde för antal dagar inaktuellt |
| `min_access_count` | int | | `2` | Tröskelvärde för lägsta åtkomstantal |
| `group_id` | string | | | Gruppfiltrering |
| `dry_run` | bool | | `true` | Förhandsgranskningsläge (tar inte bort på riktigt) |
| `limit` | int | | `50` | Maximalt antal bearbetade |

### get_memory_task_status

| Parameter | Typ | Obligatorisk | Beskrivning |
|------|------|------|------|
| `task_id` | string | Y | ID för bakgrundsuppgift (returneras av `add_memory_simple(background=true)`) |

## Webbaserat administrationsgränssnitt

I HTTP-läge når du det genom att besöka `http://localhost:8000/`.

**Funktioner:**
- Instrumentpanel — statistik över antal noder, fakta och minnessegment
- Entitetsnoder — bläddra, filtrera, vektorsöka
- Faktarelationer — bläddra, filtrera, vektorsöka
- Minnessegment — bläddra, fulltextsöka, ta bort
- Communitybläddring — lista över communitynoder, sammanfattningar, utlösa communitybyggnad
- Tripplettformulär — lägg till strukturerad kunskap i form av "subjekt-relation-objekt" direkt
- Grupphantering — filtrera per grupp, ta bort i batch
- Visualisering av kunskapsgraf — grafisk presentation av nodrelationer
- AI-frågor — intelligent frågefunktion baserad på kunskapsgrafen
- Kvalitetsunderhåll — minneskvalitetsmätningar och rensningsverktyg
- Bulkimport — importera flera minnessegment på en gång (JSON, max 500 poster per omgång)
- Körningsinställningar — visa aktuella inställningar och justera vissa parametrar utan omstart
- Temaväxling — mörkt/ljust tema

**REST API:**

| Slutpunkt | Metod | Beskrivning |
|------|------|------|
| `/api/stats` | GET | Statistik för instrumentpanel |
| `/api/groups` | GET | Hämta alla group_id |
| `/api/groups/stats` | GET | Statistik per grupp (noder/fakta/segment) |
| `/api/nodes` | GET | Bläddra bland entitetsnoder (paginerat) |
| `/api/facts` | GET | Bläddra bland fakta (paginerat) |
| `/api/episodes` | GET | Bläddra bland minnessegment (paginerat) |
| `/api/nodes/{uuid}/relations` | GET | Hämta en nods inkommande/utgående kantrelationer |
| `/api/search/nodes` | GET | Vektorsök noder |
| `/api/search/facts` | GET | Vektorsök fakta |
| `/api/search/episodes` | GET | Sök minnessegment |
| `/api/search/advanced` | GET | Avancerad sökning (16 strategier) |
| `/api/communities` | GET | Bläddra bland communitynoder (paginerat) |
| `/api/communities/build` | POST | Utlös communitybyggnad |
| `/api/memory/add` | POST | Lägg till ett enskilt minne |
| `/api/memory/add-bulk` | POST | Lägg till minnen i batch |
| `/api/memory/add-triplet` | POST | Lägg till tripplett |
| `/api/import/episodes` | POST | Bulkimportera minnessegment (JSON, max 500 poster) |
| `/api/memory/tasks` | GET | Lista bakgrundsuppgifter (stöder statusfiltrering) |
| `/api/memory/tasks/{id}` | GET | Fråga om status för en enskild uppgift |
| `/api/timeline` | GET | Tidslinjevy |
| `/api/graph/subgraph` | GET | Hämta undergraf (visualisering) |
| `/api/graph/all` | GET | Hämta fullständig graf (visualisering) |
| `/api/ask` | GET | AI-frågor (baserat på grafretrieval) |
| `/api/analytics/top-nodes` | GET | Noder med hög anslutningsgrad/åtkomst |
| `/api/analytics/quality` | GET | Kvalitetsmätningar för kunskapsgrafen |
| `/api/analytics/stale` | GET | Sök inaktuella minnen |
| `/api/analytics/cleanup` | POST | Rensa inaktuella minnen |
| `/api/config` | GET | Hämta aktuella inställningar (utan API-nycklar) |
| `/api/config` | PATCH | Uppdatera ändringsbara inställningar under körning (gäller endast aktuell process, återställs vid omstart) |
| `/api/nodes/{uuid}` | DELETE | Ta bort nod |
| `/api/episodes/{uuid}` | DELETE | Ta bort minnessegment |
| `/api/facts/{uuid}` | DELETE | Ta bort fakta |
| `/api/groups/{group_id}` | DELETE | Ta bort en hel grupp |

## Konfiguration

### Miljövariabler (.env)

Konfigurationen använder en överlagringsmekanism: JSON-konfigurationsfilen utgör basen, och miljövariabler skriver över enskilda värden.

```bash
# === Obligatoriskt ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password        # Måste ändras

# === Val av LLM-leverantör ===
LLM_PROVIDER=ollama                 # ollama / glm / groq / openrouter / deepseek

# === Embedding-leverantör (valfritt, följer LLM_PROVIDER som standard) ===
# Endast glm använder GLM Embedding, resten använder alltid Ollama bge-m3
# EMBEDDING_PROVIDER=ollama         # ollama / glm

# === Ollama-konfiguration (används när LLM_PROVIDER=ollama) ===
OLLAMA_MODEL=qwen2.5:3b             # Huvudmodell (qwen2.5:3b rekommenderas)
OLLAMA_SMALL_MODEL=qwen2.5:3b       # Liten modell (för enkla uppgifter, kan vara en annan modell)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.1

# === GLM-konfiguration (används när LLM_PROVIDER=glm) ===
GLM_API_KEY=your_api_key            # Hämtas från https://open.bigmodel.cn
GLM_MODEL=glm-4-flash               # Gratis modell
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768

# === GROQ-konfiguration (används när LLM_PROVIDER=groq) ===
GROQ_API_KEY=your_api_key           # Hämtas från https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile

# === OpenRouter-konfiguration (används när LLM_PROVIDER=openrouter) ===
OPENROUTER_API_KEY=your_api_key     # Hämtas från https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free

# === DeepSeek-konfiguration (används när LLM_PROVIDER=deepseek) ===
DEEPSEEK_API_KEY=your_api_key       # Hämtas från https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash    # Eller deepseek-v4-pro

# === Ollama-inbäddningsmodell (används vid all inbäddning som inte är glm) ===
OLLAMA_EMBEDDING_MODEL=bge-m3
OLLAMA_EMBEDDING_DIMENSIONS=768

# === Visning och språk (valfritt) ===
GRAPHITI_DISPLAY_TIMEZONE=Asia/Taipei # Visningstidszon för tidsstämplar som API returnerar (IANA-namn; lagring förblir UTC)
SERVER_LANG=zh-TW                     # Svarsspråk för MCP-verktyg (fullständig locale-lista i src/i18n.py); REST API följer Accept-Language istället

# === Minnesprestanda (valfritt) ===
GRAPHITI_CHUNK_THRESHOLD=800         # Teckentröskel som utlöser intelligent segmentering
GRAPHITI_MAX_CHUNK_SIZE=600          # Maximalt antal tecken per segment
GRAPHITI_MAX_COROUTINES=10            # Maximalt antal samtidiga coroutiner
GRAPHITI_DEFAULT_BACKGROUND=false    # Om bakgrundsbearbetning ska vara standard
TASK_DB_PATH=data/tasks.db           # SQLite-persistenssökväg för bakgrundsuppgifter

# === Viktighetsspårning och intelligent glömska (valfritt) ===
ENABLE_IMPORTANCE_TRACKING=true      # Aktivera åtkomstspårning
IMPORTANCE_WEIGHT=0.1                # Viktighetsvikt
STALE_DAYS_THRESHOLD=30              # Tröskelvärde för antal dagar inaktuellt
STALE_MIN_ACCESS_COUNT=2             # Lägsta åtkomstantal

# === Loggning ===
LOG_FILE=logs/graphiti_mcp_server.log
LOG_LEVEL=INFO
```

> **Fullständig lista över miljövariabler** finns i `.env.example`

### JSON-konfigurationsfil

Lämplig för konfiguration som behöver versionshantering (miljövariabler kan fortfarande skriva över):

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

## PM2-bakgrundskörning

```bash
npm install -g pm2

pm2 start ecosystem.config.cjs      # Starta
pm2 status                           # Status
pm2 logs graphiti-mcp-http           # Loggar i realtid
pm2 restart graphiti-mcp-http --update-env  # Starta om (ladda om .env)

pm2 save && pm2 startup              # Ställ in automatisk start vid uppstart
```

> **Tips**: Efter att ha ändrat `.env` måste du starta om med flaggan `--update-env`, annars uppdateras inte miljövariablerna.

## Docker-driftsättning

```bash
docker build -t graphiti-mcp .

# Obs: Docker-containern måste kunna ansluta till Neo4j och Ollama
# Att använda host network är enklast
docker run -p 8000:8000 --env-file .env --network host graphiti-mcp

# Eller ange explicit adresserna till externa tjänster
docker run -p 8000:8000 \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --env-file .env graphiti-mcp
```

## Testning

```bash
# Kör alla tester (203 st, cirka 1 sekund)
uv run python -m pytest tests/

# Detaljerad utdata
uv run python -m pytest tests/ -v

# Kör endast specifika tester
uv run python -m pytest tests/test_content_preprocessor.py -v
uv run python -m pytest tests/test_new_features.py -v
uv run python -m pytest tests/test_unit.py -v
```

> **Obs**: De 3 async-testerna i `test_integration_manual.py` kräver att `pytest-asyncio` är installerat; om det saknas visas Failed men det påverkar inte övriga tester. `bench_deepseek_flash_vs_pro.py` är ett prestandabenchmark-skript, inte ett enhetstest.

## Felsökning

### Neo4j-anslutning misslyckas

```bash
neo4j status                              # Kontrollera tjänstens status
cypher-shell -u neo4j -p your_password    # Bekräfta att lösenordet är korrekt
curl http://localhost:7474                 # Bekräfta HTTP-porten
```

Vanliga orsaker:
- Neo4j är inte startat
- Felaktigt lösenord (`NEO4J_PASSWORD` i `.env`)
- Porten är upptagen eller blockeras av brandväggen

### LLM-anslutning misslyckas

**Ollama-läge:**
```bash
ollama serve                # Starta Ollama-tjänsten
ollama list                 # Kontrollera installerade modeller
ollama pull qwen2.5:3b      # Installera saknad modell
```

Vanliga orsaker: Ollama är inte startat, modellen är inte installerad, otillräckligt GPU-minne

**GLM-läge:**
- Bekräfta att `GLM_API_KEY` är korrekt
- Bekräfta `GLM_EMBEDDING_DIMENSIONS=768` (måste matcha Neo4j-vektorindexet)
- GLM API-slutpunkt: `https://open.bigmodel.cn/api/paas/v4/`

**GROQ-läge:**
- Bekräfta att `GROQ_API_KEY` är korrekt
- Överväg att byta till GLM-läge vid frekvent Rate Limit
- GROQ erbjuder ingen Embedding; säkerställ att Ollama-inbäddaren är tillgänglig

**OpenRouter-läge:**
- Bekräfta att `OPENROUTER_API_KEY` är korrekt och att `OPENROUTER_MODEL` är ett giltigt modell-ID (se https://openrouter.ai/models)
- Erbjuder ingen Embedding; säkerställ att Ollama-inbäddaren är tillgänglig

**DeepSeek-läge:**
- Bekräfta att `DEEPSEEK_API_KEY` är korrekt
- Om `Prompt must contain the word 'json'` uppstår: detta är ett hårt krav för DeepSeeks `json_object`-läge, och klienten har inbyggt skydd; om det ändå uppstår, bekräfta att du använder den senaste versionen av `src/deepseek_client.py` och starta om tjänsten
- Erbjuder ingen Embedding; säkerställ att Ollama-inbäddaren är tillgänglig

### MCP-anslutningsfel

Om `Invalid request parameters` eller `Received request before initialization was complete` uppstår:

1. Bekräfta att du använder HTTP-transportläget (**använd inte SSE**)
2. Bekräfta att klienten är inställd på `"type": "http"`, `"url": "http://localhost:8000/mcp"`
3. Starta om tjänsten: `pm2 restart graphiti-mcp-http --update-env`
4. Kör `/mcp` i Claude Code för att återansluta

### Minnestillägg är långsamt

- **Ollama**: kontrollera modellstorleken (`qwen2.5:3b` är 5-10 gånger snabbare än `7b`), bekräfta att GPU används (`ollama ps`)
- **GLM**: varje add_episode kräver 10-20+ nätverksrundresor till LLM; ~22s för kort text är ett normalvärde
- **GROQ**: Rate Limit orsakar många försök på nytt; vid frekvent användning rekommenderas byte till GLM eller Ollama
- Använd `background=true` för att undvika blockering
- Sänk `GRAPHITI_CHUNK_THRESHOLD` så att lång text segmenteras tidigare

### PM2-problem

```bash
pm2 status                                        # Kontrollera status
pm2 logs graphiti-mcp-http --err --lines 50        # Felloggar
lsof -i :8000                                     # Kontrollera portanvändning
pm2 delete graphiti-mcp-http && pm2 start ecosystem.config.cjs  # Fullständig omstart
```

## Diagnostikverktyg för utveckling

```bash
uv run python tools/status_report.py           # Samlad statusrapport (Neo4j + Ollama + konfiguration)
uv run python tools/validate_config.py         # Validera .env och konfigurationens fullständighet
uv run python tools/performance_diagnose.py    # LLM-prestandadiagnostik
uv run python tools/inspect_schema.py          # Kontroll av Neo4j-index och begränsningar
uv run python tools/migrate_embeddings.py      # Migrering av Embedding-modell (generera om vektorer efter modellbyte)
```

### Migrering av Embedding-modell

Efter att ha bytt embedding-modell (t.ex. `nomic-embed-text` → `bge-m3`) kan du använda migreringsverktyget för att generera om alla befintliga vektorer och säkerställa enhetlig sökkvalitet:

```bash
# Förhandsgranska antalet som behöver migreras
uv run python tools/migrate_embeddings.py --dry-run

# Fullständig migrering (stöder återupptagning från brytpunkt)
uv run python tools/migrate_embeddings.py

# Migrera endast en angiven grupp
uv run python tools/migrate_embeddings.py --group-id myproject

# Fortsätt från brytpunkt (kör om efter avbrott)
uv run python tools/migrate_embeddings.py --resume
```

> **Kompatibilitet**: `bge-m3` är 1024-dimensionell ursprungligen; systemet trunkerar automatiskt till 768 dimensioner för att vara kompatibelt med det befintliga Neo4j-vektorindexet. Data före och efter migreringen kan samexistera, men det rekommenderas att utföra en fullständig migrering för bästa sökkvalitet.

## Dokumentation

- [Instruktioner för verktygsanvändning](../使用工具的指令.md) — guide och bästa praxis för användning av MCP-verktyg
- [Graphiti Memory Rules](../graphiti-memory-rules.md) — beskrivning av minnesregler

## Licens

MIT License
