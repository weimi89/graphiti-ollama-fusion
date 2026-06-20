# Graphiti MCP Server

Geheugenservice op basis van een kennisgraaf — een MCP-server die meerdere LLM-providers (Ollama / GLM / GROQ / OpenRouter / DeepSeek) integreert met de Neo4j-grafendatabase.

Ontwikkeld als uitbreiding op [getzep/graphiti](https://github.com/getzep/graphiti), met flexibele schakeling tussen lokale Ollama en cloud-LLM's, en de mogelijkheid om de Embedding-provider afzonderlijk op te geven (ontkoppeld van de LLM).

## Kenmerken

- **Intelligent geheugenbeheer** — gebruikt een kennisgraaf om complexe geheugenrelaties op te slaan en op te halen
- **Semantisch zoeken** — hybride zoeken op basis van vectorinbeddingen (vector + trefwoord + grafdoorloop)
- **16 zoekstrategieën** — geavanceerd zoeken ondersteunt diverse herrangschikkingsmethoden zoals RRF, MMR, Cross-Encoder
- **Meerdere LLM-providers** — ondersteunt Ollama (lokaal), GLM (Zhipu AI, gratis), GROQ (snelle inferentie), OpenRouter (aggregeert diverse modellen), DeepSeek (Deep Seek), met schakelen via één omgevingsvariabele
- **Embedding ontkoppeld van LLM** — de inbedder kan afzonderlijk worden opgegeven met `EMBEDDING_PROVIDER`; cloud-LLM's vallen automatisch terug op lokaal `bge-m3`
- **Dubbele-model-verdeling** — in Ollama-modus gebruiken complexe taken het hoofdmodel en schakelen eenvoudige taken automatisch over naar een klein model voor betere prestaties
- **Intelligente inhoudssegmentatie** — lange teksten worden automatisch in segmenten verwerkt om de LLM-belasting te verlagen (drempel configureerbaar)
- **Geheugenverwerking op de achtergrond** — geheugen toevoegen kan op de achtergrond draaien, waarbij de MCP-aanroep onmiddellijk terugkeert; taakstatus wordt persistent opgeslagen in SQLite en onvoltooide taken worden automatisch hersteld na herstart
- **Geheugendeduplicatie** — detecteert automatisch sterk gelijkende bestaande herinneringen om dubbele opslag te voorkomen
- **Conflictdetectie** — detecteert tegenstrijdige feiten tussen twee entiteiten en identificeert verouderde en geldige informatie
- **Gemeenschapsdetectie** — clustert automatisch gerelateerde entiteiten op basis van het Label Propagation-algoritme
- **Belangrijkheidstracering** — registreert automatisch de toegangsfrequentie van entiteiten; zoekresultaten worden gerangschikt op belangrijkheid
- **Intelligent vergeten** — identificeert en ruimt verouderde herinneringen met weinig toegang op om de graaf compact te houden
- **Bulkimport** — meerdere herinneringen in één keer indienen, geschikt voor grootschalige datamigratie
- **Gestructureerde triples** — voeg direct "subject-relatie-object" toe en sla LLM-extractie over voor bliksemsnelle voltooiing
- **Webbeheerinterface** — ingebouwd dashboard, bladeren, zoeken, kennisgraafvisualisatie, AI-vraag-en-antwoord, gemeenschapsbrowsen, kwaliteitsonderhoud, bulkimport, runtime-instellingen
- **Meertaligheid (i18n)** — responsberichten ondersteunen 33 talen (waaronder zh-TW / en / zh-CN / ja / pt-BR / ko / es / de / fr enz.; zh-TW/en/zh-CN/ja handgeschreven, overige via de generated-laag); MCP-tools volgen `SERVER_LANG`, REST API onderhandelt automatisch op basis van HTTP `Accept-Language`
- **Donker/licht thema** — de webinterface ondersteunt themawisseling
- **Veilige modus** — optionele snelle geheugentoevoeging die entiteitextractie overslaat
- **Docker-ondersteuning** — ingebouwde Dockerfile, ondersteunt implementatie in containers
- **Concurrentieveiligheid** — asyncio.Lock beschermt de initialisatie en voorkomt raceomstandigheden
- **Gelaagde gezondheidscontrole** — `/health` (liveness) + `/health/ready` (readiness)

## Systeemvereisten

| Onderdeel | Vereiste |
|------|------|
| Python | 3.10+ (3.11+ aanbevolen) |
| Neo4j | 4.0+ (`bolt://localhost:7687`) |
| LLM-provider | Ollama / GLM / GROQ / OpenRouter / DeepSeek (één van de vijf) |
| Node.js | 18+ (alleen voor PM2-achtergronduitvoering, optioneel) |
| Schijfruimte | ~3GB (Ollama-modellen + Neo4j-gegevens) |

### Keuze van LLM-provider

Schakelen via de omgevingsvariabele `LLM_PROVIDER` (`ollama` / `glm` / `groq` / `openrouter` / `deepseek`):

| Provider | Kenmerken | LLM-model | Embedding | Geschikt scenario |
|--------|------|----------|-----------|----------|
| **Ollama** (standaard) | Volledig lokaal, gegevens verlaten de machine niet | `qwen2.5:3b` | `bge-m3` (uitstekend voor Chinees + RAG) | Met GPU, focus op privacy |
| **GLM** | Gratis cloud, stabiel zonder ratelimiet | `glm-4-flash` (gratis) | `embedding-3` | Geen GPU, zoekintensieve scenario's |
| **GROQ** | Ultrasnelle inferentie | `llama-3.3-70b-versatile` | Valt terug op Ollama `bge-m3` | Occasioneel schrijven, focus op kwaliteit |
| **OpenRouter** | Aggregeert diverse modellen, inclusief gratis quota | `stepfun/step-3.5-flash:free` enz. | Valt terug op Ollama `bge-m3` | Wil een specifiek cloudmodel gebruiken |
| **DeepSeek** | Deep Seek cloud, hoge prijs-kwaliteitverhouding | `deepseek-v4-flash` / `deepseek-v4-pro` | Valt terug op Ollama `bge-m3` | Chinees begrip, goedkope cloud |

> **Embedding ontkoppeld van LLM**: de inbedder wordt afzonderlijk opgegeven via `EMBEDDING_PROVIDER` (`ollama` / `glm`); indien niet ingesteld volgt deze `LLM_PROVIDER`. In de praktijk gebruikt alleen `glm` GLM `embedding-3`; alle overige (inclusief cloud-LLM's zonder Embedding zoals GROQ / OpenRouter / DeepSeek) gebruiken automatisch Ollama `bge-m3`. **Daarom is bij gebruik van een cloud-LLM nog steeds lokale Ollama nodig voor de inbeddingsdienst (tenzij embedding ook op glm is ingesteld).**

#### Ollama-modus (lokaal)

```bash
# LLM-hoofdmodel (qwen2.5:3b aanbevolen, beste balans tussen snelheid en stabiliteit)
ollama pull qwen2.5:3b

# Inbeddingsmodel (vereist, voor vectorzoeken)
ollama pull bge-m3
```

> **Aandachtspunten bij modelkeuze**:
> - `qwen2.5:3b` — aanbevolen, ~2s/aanroep, ~100 t/s, gestructureerde uitvoer van graphiti-core 100% stabiel
> - `qwen2.5:7b` — betere resultaten maar 5-10 keer trager, geschikt voor scenario's gericht op kwaliteit
> - `qwen2.5:1.5b` — snelst maar **onstabiel** (gestructureerde JSON slechts 33% slaagkans), niet aanbevolen

#### GLM-modus (Zhipu AI cloud)

```bash
# .env-instellingen
LLM_PROVIDER=glm
GLM_API_KEY=your_api_key          # verkrijgbaar via https://open.bigmodel.cn
GLM_MODEL=glm-4-flash             # gratis model
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768      # moet overeenkomen met de dimensie van de Neo4j-vectorindex
```

> **GLM-prestatiereferentie**: schrijven ~22s (korte tekst), zoeken ~0,34s, nul Rate Limit-fouten, 2-5 keer trager dan lokale Ollama maar volledig gratis.

#### GROQ-modus (snelle inferentie)

```bash
# .env-instellingen
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key         # verkrijgbaar via https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile
```

> **Opmerking**: GROQ biedt geen Embedding-dienst en moet worden gecombineerd met de Ollama-inbedder (automatische terugval) of stel `EMBEDDING_PROVIDER` in op glm. GROQ heeft een strikte Rate Limit; hoogfrequent gebruik leidt tot veel herhaalpogingen.

#### OpenRouter-modus (aggregeert diverse modellen)

```bash
# .env-instellingen
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_api_key       # verkrijgbaar via https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free   # kan worden gewijzigd in elk OpenRouter-model
```

> **Opmerking**: OpenRouter biedt geen Embedding en valt automatisch terug op Ollama `bge-m3`. Voor de modellenlijst zie https://openrouter.ai/models (inclusief meerdere `:free` gratis modellen).

#### DeepSeek-modus (Deep Seek)

```bash
# .env-instellingen
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key         # verkrijgbaar via https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash      # aanbevolen; of deepseek-v4-pro (betere resultaten)
```

> **Opmerking**: DeepSeek biedt geen Embedding en valt automatisch terug op Ollama `bge-m3`. `deepseek-chat` / `deepseek-reasoner` worden op 2026-07-24 buiten gebruik gesteld; het wordt aanbevolen over te stappen op `deepseek-v4-flash` / `deepseek-v4-pro`. DeepSeek vereist strikt dat de prompt in de `json_object`-modus het woord "json" bevat; de client heeft een ingebouwde veiligheidsbescherming, dus geen extra instelling nodig.

## Snel starten

### 1. Voorbereiding

Bevestig dat Neo4j lokaal draait en bereid de bijbehorende dienst voor op basis van de gekozen LLM-provider:

```bash
# Bevestig dat Neo4j draait (vereist)
neo4j status
# Of via Docker: docker run -d -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/your_password neo4j:latest

# Ollama-modus: bevestig dat Ollama draait
ollama list
# Indien niet gestart: ollama serve

# GLM / GROQ-modus: alleen een geldige API Key nodig, geen lokale dienst vereist
```

### 2. Afhankelijkheden installeren

```bash
git clone <repo-url>
cd graphiti
uv sync
```

> **Opmerking**: dit project gebruikt [uv](https://github.com/astral-sh/uv) voor afhankelijkhedenbeheer. Indien niet geïnstalleerd: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 3. Omgeving configureren

```bash
cp .env.example .env
```

Bewerk `.env`; je moet **ten minste** de volgende items wijzigen:

```bash
NEO4J_PASSWORD=your_actual_password  # vereist: Neo4j-wachtwoord
LLM_PROVIDER=ollama                  # ollama / glm / groq / openrouter / deepseek
OLLAMA_MODEL=qwen2.5:3b              # Ollama-modus: lokaal LLM-model
# GLM_API_KEY=your_key               # GLM-modus: Zhipu AI API Key
# GROQ_API_KEY=your_key              # GROQ-modus: GROQ API Key
# OPENROUTER_API_KEY=your_key        # OpenRouter-modus: API Key
# DEEPSEEK_API_KEY=your_key          # DeepSeek-modus: API Key
```

### 4. Dienst starten

```bash
# HTTP-modus (aanbevolen, inclusief webbeheerinterface)
uv run python graphiti_mcp_server.py --transport http --port 8000

# Of gebruik PM2-achtergronduitvoering (aanbevolen voor langdurig draaien)
pm2 start ecosystem.config.cjs
```

### 5. Dienst verifiëren

Na het starten kun je de volgende endpoints bezoeken:

| Endpoint | Beschrijving |
|------|------|
| http://localhost:8000/ | Webbeheerinterface |
| http://localhost:8000/mcp | MCP-endpoint (voor verbinding door MCP-clients) |
| http://localhost:8000/health | Gezondheidscontrole (liveness) |
| http://localhost:8000/health/ready | Diepe controle (inclusief Neo4j-verbinding) |
| http://localhost:8000/api/stats | REST API-statistieken |

## Projectstructuur

```
graphiti/
├── graphiti_mcp_server.py        # Hoofdingang — MCP-tooldefinities (19 tools)
├── src/
│   ├── config.py                 # Configuratiebeheer (GraphitiConfig, ondersteunt JSON/.env gelaagd)
│   ├── web_api.py                # REST API van webbeheerinterface (30+ endpoints)
│   ├── ollama_graphiti_client.py  # Ollama LLM-client (dubbele-model-verdeling)
│   ├── openai_compat_client.py   # OpenAI-compatibele LLM-basisklasse (json_object + vereenvoudigde schema + json-beveiliging)
│   ├── glm_client.py             # GLM (Zhipu AI) LLM-client (erft van OpenAICompatClient)
│   ├── openrouter_client.py      # OpenRouter LLM-client (erft van OpenAICompatClient)
│   ├── deepseek_client.py        # DeepSeek LLM-client (erft van OpenAICompatClient)
│   ├── ollama_embedder.py        # Ollama-inbeddingsmodeladapter
│   ├── content_preprocessor.py   # Intelligente inhoudssegmentatie (automatische segmentatie van lange tekst)
│   ├── deduplication.py          # Geheugendeduplicatie (cosinusgelijkenisvergelijking)
│   ├── importance.py             # Belangrijkheidstracering en intelligent vergeten
│   ├── safe_memory_add.py        # Veilige geheugentoevoeging (slaat entiteitextractie over)
│   ├── task_store.py             # SQLite-persistentie voor achtergrondtaken (TaskStore)
│   ├── timezone_utils.py         # Tijdzoneconversie (UTC→lokale tijdzoneweergave)
│   ├── i18n.py                   # Backend-meertaligheid (REST volgt Accept-Language, MCP volgt SERVER_LANG)
│   ├── i18n_generated.py         # Automatisch gegenereerde taaloverrides (GENERATED_MESSAGE_OVERRIDES)
│   ├── exceptions.py             # Gestructureerde uitzonderingsafhandeling (12 uitzonderingsklassen)
│   └── logging_setup.py          # Logsysteem (tijdrotatie + prestatiemonitoring)
├── web/                          # Frontend van webbeheerinterface (SPA, geen build)
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js                # REST API-wrapper
│       ├── components.js         # UI-componentrendering (inclusief gemeenschapspagina)
│       └── app.js                # SPA-routing, statusbeheer
├── tests/                        # Testsuite (203 tests)
│   ├── test_content_preprocessor.py  # Segmentatielogicatests (17 stuks)
│   ├── test_new_features.py      # Tests voor nieuwe functies (32 stuks)
│   ├── test_i18n.py             # Meertaligheidstests (57 stuks)
│   ├── test_unit.py              # Unittests
│   ├── test_web_api.py           # Web API-tests
│   ├── test_web_ui_features.py   # Web UI-functietests
│   ├── test_integration_manual.py # Handmatige integratietests
│   └── bench_deepseek_flash_vs_pro.py # DeepSeek flash/pro prestatiebenchmarkscript
├── tools/                        # Diagnostische ontwikkeltools
│   ├── status_report.py          # Geïntegreerd statusrapport
│   ├── validate_config.py        # Configuratievalidatie
│   ├── performance_diagnose.py   # Prestatiediagnose
│   ├── inspect_schema.py         # Neo4j-structuurcontrole
│   ├── batch_reprocess.py        # Batchherverwerking
│   └── migrate_embeddings.py     # Embedding-modelmigratie
├── docs/                         # Documentatie
├── logs/                         # Logs (tijdrotatie, standaard 30 dagen bewaard)
├── Dockerfile                    # Docker-containerimplementatie
└── ecosystem.config.cjs          # PM2-configuratie
```

## MCP-clientinstellingen

### HTTP-modus (aanbevolen)

Geschikt voor MCP-clients die HTTP ondersteunen, zoals Claude Code, Cline:

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

### STDIO-modus

Geschikt voor clients die het proces rechtstreeks moeten starten, zoals Claude Desktop:

**Locatie van configuratiebestand:**
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

> **Opmerking**: de SSE-modus (`--transport sse`) wordt niet langer aanbevolen. MCP 1.x heeft compatibiliteitsproblemen met sessie-initialisatie; gebruik in plaats daarvan de HTTP-modus.

## MCP-tools (19 stuks)

### Geheugenbeheer (7 stuks)

| Tool | Beschrijving |
|------|------|
| `add_memory_simple` | Voegt geheugen toe aan de kennisgraaf (ondersteunt achtergrondverwerking, intelligente segmentatie, deduplicatiecontrole) |
| `add_episode_bulk` | Voegt meerdere herinneringen in bulk toe (achtergrondverwerking standaard) |
| `add_triplet` | Gestructureerde triple-toevoeging (slaat LLM over, bliksemsnel voltooid) |
| `search_memory_nodes` | Zoekt geheugenknooppunten (ondersteunt 16 zoekstrategieën, tijdfiltering) |
| `search_memory_facts` | Zoekt geheugenfeiten (ondersteunt filtering op relatietype, tijdsbereik, geldigheid) |
| `advanced_search` | Geavanceerd zoeken (16 strategieën, retourneert knooppunten+randen+gemeenschappen+fragmenten) |
| `get_episodes` | Haalt recente geheugenfragmenten op |

### Kennisanalyse (3 stuks)

| Tool | Beschrijving |
|------|------|
| `check_conflicts` | Detecteert feitenconflicten tussen twee entiteiten (geldig vs. verouderd) |
| `get_node_edges` | Verkent de inkomende en uitgaande randrelaties van een knooppunt |
| `build_communities` | Activeert gemeenschapsdetectie en clustering (achtergrondverwerking standaard) |

### Geheugenonderhoud (2 stuks)

| Tool | Beschrijving |
|------|------|
| `get_stale_memories` | Zoekt verouderde herinneringen met weinig toegang |
| `cleanup_stale_memories` | Ruimt verouderde herinneringen op (standaard dry_run-voorbeeldmodus) |

### Taakbeheer

| Tool | Beschrijving |
|------|------|
| `get_memory_task_status` | Vraagt de voortgang en resultaten van een achtergrondgeheugentaak op |

### Verwijderen en opvragen

| Tool | Beschrijving |
|------|------|
| `delete_episode` | Verwijdert een geheugenfragment |
| `delete_entity_edge` | Verwijdert een entiteitrand (relatie) |
| `get_entity_edge` | Haalt gedetailleerde informatie over een entiteitrand op |

### Systeembeheer

| Tool | Beschrijving |
|------|------|
| `get_status` | Haalt de dienststatus op (Neo4j, LLM, inbedder) |
| `test_connection` | Test de Neo4j / LLM / inbedderverbinding |
| `clear_graph` | Wist de grafendatabase (ondersteunt wissen per group_id) |

## Toolparameters

### add_memory_simple

| Parameter | Type | Vereist | Standaardwaarde | Beschrijving |
|------|------|------|--------|------|
| `name` | string | Y | | Geheugennaam |
| `episode_body` | string | Y | | Geheugeninhoud (automatisch gesegmenteerd boven 800 tekens) |
| `group_id` | string | | `"default"` | Groeperings-ID (aanbevolen om per project te isoleren) |
| `source` | string | | `"text"` | Brontype: `text` / `json` / `message` |
| `source_description` | string | | `"MCP Server"` | Bronbeschrijving |
| `use_safe_mode` | bool | | `false` | Veilige modus (slaat entiteitextractie over, snel maar geheugen is niet doorzoekbaar) |
| `background` | bool | | `false` | Achtergrondverwerking (retourneert onmiddellijk task_id, geschikt voor lange tekst) |
| `force` | bool | | `false` | Slaat deduplicatiecontrole over (gedwongen toevoeging) |
| `excluded_entity_types` | list | | | Uitgesloten entiteitstypes (vermindert onnodige extractie) |

> **Prestatietips**:
> - Korte tekst (<800 tekens): direct verwerkt, doorgaans voltooid in 30-40 seconden
> - Lange tekst (>800 tekens): automatisch gesegmenteerd in meerdere delen, verwerkt met `add_episode_bulk` gelijktijdig (~33% sneller dan serieel)
> - Gebruik `background=true` om blokkering van de MCP-aanroep te voorkomen, volg de voortgang via `get_memory_task_status`
> - `use_safe_mode=true` voltooit bliksemsnel maar het geheugen kan niet door zoektools worden gevonden
> - Wanneer deduplicatie is ingeschakeld, worden sterk gelijkende herinneringen gewaarschuwd (`force=true` slaat dit over)

### add_episode_bulk

| Parameter | Type | Vereist | Standaardwaarde | Beschrijving |
|------|------|------|--------|------|
| `episodes` | list | Y | | Geheugenlijst, elk item bevat `name` en `content` |
| `group_id` | string | | `"default"` | Groeperings-ID |
| `source` | string | | `"text"` | Brontype |
| `background` | bool | | `true` | Achtergrondverwerking (bulk is doorgaans tijdrovend) |

### add_triplet

| Parameter | Type | Vereist | Standaardwaarde | Beschrijving |
|------|------|------|--------|------|
| `source_name` | string | Y | | Naam van bronentiteit (bijv. "Alice") |
| `target_name` | string | Y | | Naam van doelentiteit (bijv. "Google") |
| `relation_name` | string | Y | | Relatienaam (bijv. "works_at") |
| `fact` | string | Y | | Feitbeschrijving (bijv. "Alice works at Google") |
| `group_id` | string | | `"default"` | Groeperings-ID |
| `source_labels` | list | | | Labels van bronentiteit |
| `target_labels` | list | | | Labels van doelentiteit |

### search_memory_nodes

| Parameter | Type | Vereist | Standaardwaarde | Beschrijving |
|------|------|------|--------|------|
| `query` | string | Y | | Zoektrefwoord (natuurlijke taal) |
| `max_nodes` | int | | `10` | Maximaal aantal te retourneren |
| `group_ids` | list | | | Groepfiltering (gecombineerd zoeken over meerdere groepen) |
| `entity_types` | list | | | Entiteitstypefiltering |
| `search_recipe` | string | | | Zoekstrategie (zie geavanceerd zoeken) |
| `created_after` | string | | | Ondergrens aanmaaktijd (ISO datetime) |
| `created_before` | string | | | Bovengrens aanmaaktijd (ISO datetime) |

### search_memory_facts

| Parameter | Type | Vereist | Standaardwaarde | Beschrijving |
|------|------|------|--------|------|
| `query` | string | Y | | Zoektrefwoord |
| `max_facts` | int | | `10` | Maximaal aantal te retourneren |
| `group_ids` | list | | | Groepfiltering |
| `center_node_uuid` | string | | | UUID van middelpuntknooppunt (verkent relaties van een specifiek knooppunt) |
| `edge_types` | list | | | Relatietypefiltering (bijv. `["works_at"]`) |
| `created_after` | string | | | Ondergrens aanmaaktijd (ISO datetime) |
| `created_before` | string | | | Bovengrens aanmaaktijd (ISO datetime) |
| `only_valid` | bool | | `false` | Retourneert alleen niet-verlopen feiten |

### advanced_search

| Parameter | Type | Vereist | Standaardwaarde | Beschrijving |
|------|------|------|--------|------|
| `query` | string | Y | | Zoektrefwoord |
| `search_recipe` | string | | `"combined_rrf"` | Zoekstrategie (16 opties) |
| `max_results` | int | | `10` | Maximaal aantal te retourneren |
| `group_ids` | list | | | Groepfiltering |
| `center_node_uuid` | string | | | UUID van middelpuntknooppunt |

**Beschikbare zoekstrategieën (search_recipe):**

| Categorie | Strategie | Beschrijving |
|------|------|------|
| Gecombineerd | `combined_rrf` | Gecombineerde RRF-fusie (standaard, aanbevolen) |
| Gecombineerd | `combined_mmr` | Gecombineerde MMR-diversiteitsherrangschikking |
| Gecombineerd | `combined_cross_encoder` | Gecombineerde Cross-Encoder-fijnrangschikking |
| Rand | `edge_rrf` / `edge_mmr` / `edge_cross_encoder` | Randzoeken (3 rangschikkingen) |
| Rand | `edge_node_distance` / `edge_episode_mentions` | Randzoeken (grafafstand/aantal verwijzingen) |
| Knooppunt | `node_rrf` / `node_mmr` / `node_cross_encoder` | Knooppuntzoeken (3 rangschikkingen) |
| Knooppunt | `node_node_distance` / `node_episode_mentions` | Knooppuntzoeken (grafafstand/aantal verwijzingen) |
| Gemeenschap | `community_rrf` / `community_mmr` / `community_cross_encoder` | Gemeenschapszoeken |

### check_conflicts

| Parameter | Type | Vereist | Standaardwaarde | Beschrijving |
|------|------|------|--------|------|
| `source_name` | string | Y | | Naam van bronentiteit |
| `target_name` | string | Y | | Naam van doelentiteit |
| `group_id` | string | | `"default"` | Groeperings-ID |

### get_node_edges

| Parameter | Type | Vereist | Standaardwaarde | Beschrijving |
|------|------|------|--------|------|
| `node_uuid` | string | Y | | Knooppunt-UUID |
| `include_inbound` | bool | | `true` | Inclusief inkomende randen |
| `include_outbound` | bool | | `true` | Inclusief uitgaande randen |
| `max_edges` | int | | `50` | Maximaal aantal te retourneren |

### build_communities

| Parameter | Type | Vereist | Standaardwaarde | Beschrijving |
|------|------|------|--------|------|
| `group_ids` | list | | | Specificeer groepen (leeg laten voor alle) |
| `background` | bool | | `true` | Achtergrondverwerking |

### get_stale_memories

| Parameter | Type | Vereist | Standaardwaarde | Beschrijving |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Aantal dagen zonder toegang om als verouderd te beschouwen |
| `min_access_count` | int | | `2` | Alleen opgenomen als het aantal toegangen onder deze waarde ligt |
| `group_id` | string | | | Groepfiltering |
| `limit` | int | | `50` | Maximaal aantal te retourneren |

### cleanup_stale_memories

| Parameter | Type | Vereist | Standaardwaarde | Beschrijving |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Drempel voor verouderde dagen |
| `min_access_count` | int | | `2` | Drempel voor minimaal aantal toegangen |
| `group_id` | string | | | Groepfiltering |
| `dry_run` | bool | | `true` | Voorbeeldmodus (verwijdert niet daadwerkelijk) |
| `limit` | int | | `50` | Maximaal aantal te verwerken |

### get_memory_task_status

| Parameter | Type | Vereist | Beschrijving |
|------|------|------|------|
| `task_id` | string | Y | Achtergrondtaak-ID (geretourneerd door `add_memory_simple(background=true)`) |

## Webbeheerinterface

Bezoek in HTTP-modus `http://localhost:8000/` om te gebruiken.

**Functies:**
- Dashboard — statistieken van aantal knooppunten, feiten en geheugenfragmenten
- Entiteitknooppunten — bladeren, filteren, vectorzoeken
- Feitrelaties — bladeren, filteren, vectorzoeken
- Geheugenfragmenten — bladeren, volledige-tekst zoeken, verwijderen
- Gemeenschapsbrowsen — lijst van gemeenschapsknooppunten, samenvattingen, gemeenschapsopbouw activeren
- Tripleformulier — voeg direct gestructureerde kennis "subject-relatie-object" toe
- Groepbeheer — filteren per groep, batchverwijdering
- Kennisgraafvisualisatie — grafische weergave van knooppuntrelaties
- AI-vraag-en-antwoord — intelligente vraag-en-antwoord op basis van de kennisgraaf
- Kwaliteitsonderhoud — kwaliteitsindicatoren voor geheugen en opruimtools
- Bulkimport — meerdere geheugenfragmenten tegelijk importeren (JSON, maximaal 500 per keer)
- Runtime-instellingen — huidige actieve instellingen bekijken en sommige parameters aanpassen zonder herstart
- Themawisseling — donker/licht thema

**REST API:**

| Endpoint | Methode | Beschrijving |
|------|------|------|
| `/api/stats` | GET | Dashboardstatistieken |
| `/api/groups` | GET | Alle group_id's ophalen |
| `/api/groups/stats` | GET | Statistieken per group (knooppunten/feiten/fragmenten) |
| `/api/nodes` | GET | Entiteitknooppunten bladeren (gepagineerd) |
| `/api/facts` | GET | Feiten bladeren (gepagineerd) |
| `/api/episodes` | GET | Geheugenfragmenten bladeren (gepagineerd) |
| `/api/nodes/{uuid}/relations` | GET | Inkomende/uitgaande relaties van een knooppunt ophalen |
| `/api/search/nodes` | GET | Vectorzoeken naar knooppunten |
| `/api/search/facts` | GET | Vectorzoeken naar feiten |
| `/api/search/episodes` | GET | Geheugenfragmenten doorzoeken |
| `/api/search/advanced` | GET | Geavanceerd zoeken (16 strategieën) |
| `/api/communities` | GET | Gemeenschapsknooppunten bladeren (gepagineerd) |
| `/api/communities/build` | POST | Gemeenschapsopbouw activeren |
| `/api/memory/add` | POST | Enkel geheugen toevoegen |
| `/api/memory/add-bulk` | POST | Geheugen in bulk toevoegen |
| `/api/memory/add-triplet` | POST | Triple toevoegen |
| `/api/import/episodes` | POST | Geheugenfragmenten in bulk importeren (JSON, maximaal 500 per keer) |
| `/api/memory/tasks` | GET | Achtergrondtaken weergeven (ondersteunt statusfiltering) |
| `/api/memory/tasks/{id}` | GET | Status van enkele taak opvragen |
| `/api/timeline` | GET | Tijdlijnweergave |
| `/api/graph/subgraph` | GET | Subgraaf ophalen (visualisatie) |
| `/api/graph/all` | GET | Volledige graaf ophalen (visualisatie) |
| `/api/ask` | GET | AI-vraag-en-antwoord (op basis van graafopzoeking) |
| `/api/analytics/top-nodes` | GET | Knooppunten met hoge connectiviteit/toegang |
| `/api/analytics/quality` | GET | Kwaliteitsindicatoren van de kennisgraaf |
| `/api/analytics/stale` | GET | Verouderde herinneringen opvragen |
| `/api/analytics/cleanup` | POST | Verouderde herinneringen opruimen |
| `/api/config` | GET | Huidige actieve instellingen ophalen (zonder API-sleutels) |
| `/api/config` | PATCH | Runtime-instellingen bijwerken (alleen geldig voor dit proces, hersteld na herstart) |
| `/api/nodes/{uuid}` | DELETE | Knooppunt verwijderen |
| `/api/episodes/{uuid}` | DELETE | Geheugenfragment verwijderen |
| `/api/facts/{uuid}` | DELETE | Feit verwijderen |
| `/api/groups/{group_id}` | DELETE | Hele groep verwijderen |

## Configuratie

### Omgevingsvariabelen (.env)

De configuratie gebruikt een gelaagd mechanisme: het JSON-configuratiebestand vormt de basis, omgevingsvariabelen overschrijven individuele waarden.

```bash
# === Vereist ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password        # moet worden gewijzigd

# === Keuze van LLM-provider ===
LLM_PROVIDER=ollama                 # ollama / glm / groq / openrouter / deepseek

# === Embedding-provider (optioneel, volgt standaard LLM_PROVIDER) ===
# Alleen glm gebruikt GLM Embedding, alle overige gebruiken Ollama bge-m3
# EMBEDDING_PROVIDER=ollama         # ollama / glm

# === Ollama-configuratie (gebruikt wanneer LLM_PROVIDER=ollama) ===
OLLAMA_MODEL=qwen2.5:3b             # hoofdmodel (qwen2.5:3b aanbevolen)
OLLAMA_SMALL_MODEL=qwen2.5:3b       # klein model (voor eenvoudige taken, optioneel ander model)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.1

# === GLM-configuratie (gebruikt wanneer LLM_PROVIDER=glm) ===
GLM_API_KEY=your_api_key            # verkrijgbaar via https://open.bigmodel.cn
GLM_MODEL=glm-4-flash               # gratis model
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768

# === GROQ-configuratie (gebruikt wanneer LLM_PROVIDER=groq) ===
GROQ_API_KEY=your_api_key           # verkrijgbaar via https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile

# === OpenRouter-configuratie (gebruikt wanneer LLM_PROVIDER=openrouter) ===
OPENROUTER_API_KEY=your_api_key     # verkrijgbaar via https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free

# === DeepSeek-configuratie (gebruikt wanneer LLM_PROVIDER=deepseek) ===
DEEPSEEK_API_KEY=your_api_key       # verkrijgbaar via https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash    # of deepseek-v4-pro

# === Ollama-inbeddingsmodel (gebruikt bij alle niet-glm-inbeddingen) ===
OLLAMA_EMBEDDING_MODEL=bge-m3
OLLAMA_EMBEDDING_DIMENSIONS=768

# === Weergave en taal (optioneel) ===
GRAPHITI_DISPLAY_TIMEZONE=Asia/Taipei # weergavetijdzone van door API geretourneerde tijdstempels (IANA-naam; opslag blijft UTC)
SERVER_LANG=zh-TW                     # responstaal van MCP-tools (zie src/i18n.py voor volledige locale); REST API volgt Accept-Language

# === Geheugenprestaties (optioneel) ===
GRAPHITI_CHUNK_THRESHOLD=800         # tekendrempel die intelligente segmentatie activeert
GRAPHITI_MAX_CHUNK_SIZE=600          # maximaal aantal tekens per segment
GRAPHITI_MAX_COROUTINES=10            # maximaal aantal gelijktijdige coroutines
GRAPHITI_DEFAULT_BACKGROUND=false    # of standaard achtergrondverwerking wordt gebruikt
TASK_DB_PATH=data/tasks.db           # SQLite-persistentiepad voor achtergrondtaken

# === Belangrijkheidstracering en intelligent vergeten (optioneel) ===
ENABLE_IMPORTANCE_TRACKING=true      # toegangstracering inschakelen
IMPORTANCE_WEIGHT=0.1                # belangrijkheidsgewicht
STALE_DAYS_THRESHOLD=30              # drempel voor verouderde dagen
STALE_MIN_ACCESS_COUNT=2             # minimaal aantal toegangen

# === Logs ===
LOG_FILE=logs/graphiti_mcp_server.log
LOG_LEVEL=INFO
```

> **Voor de volledige lijst met omgevingsvariabelen** zie `.env.example`

### JSON-configuratiebestand

Geschikt voor configuratie die versiebeheer nodig heeft (omgevingsvariabelen kunnen nog steeds overschrijven):

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

## PM2-achtergronduitvoering

```bash
npm install -g pm2

pm2 start ecosystem.config.cjs      # starten
pm2 status                           # status
pm2 logs graphiti-mcp-http           # realtime logs
pm2 restart graphiti-mcp-http --update-env  # herstarten (.env opnieuw laden)

pm2 save && pm2 startup              # automatisch starten bij opstarten instellen
```

> **Tip**: na het wijzigen van `.env` moet je opnieuw starten met de `--update-env`-vlag, anders worden de omgevingsvariabelen niet bijgewerkt.

## Docker-implementatie

```bash
docker build -t graphiti-mcp .

# Opmerking: de Docker-container moet verbinding kunnen maken met Neo4j en Ollama
# Het host network gebruiken is het eenvoudigst
docker run -p 8000:8000 --env-file .env --network host graphiti-mcp

# Of geef expliciet de adressen van externe diensten op
docker run -p 8000:8000 \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --env-file .env graphiti-mcp
```

## Testen

```bash
# Alle tests uitvoeren (203 stuks, ongeveer 1 seconde)
uv run python -m pytest tests/

# Gedetailleerde uitvoer
uv run python -m pytest tests/ -v

# Alleen specifieke tests uitvoeren
uv run python -m pytest tests/test_content_preprocessor.py -v
uv run python -m pytest tests/test_new_features.py -v
uv run python -m pytest tests/test_unit.py -v
```

> **Opmerking**: de 3 async-tests in `test_integration_manual.py` vereisen de installatie van `pytest-asyncio`; bij afwezigheid worden ze als Failed weergegeven maar dit beïnvloedt de andere tests niet. `bench_deepseek_flash_vs_pro.py` is een prestatiebenchmarkscript, geen unittest.

## Probleemoplossing

### Neo4j-verbinding mislukt

```bash
neo4j status                              # dienststatus controleren
cypher-shell -u neo4j -p your_password    # bevestig dat het wachtwoord juist is
curl http://localhost:7474                 # HTTP-poort bevestigen
```

Veelvoorkomende oorzaken:
- Neo4j is niet gestart
- Verkeerd wachtwoord (`NEO4J_PASSWORD` in `.env`)
- Poort is bezet of geblokkeerd door firewall

### LLM-verbinding mislukt

**Ollama-modus:**
```bash
ollama serve                # Ollama-dienst starten
ollama list                 # geïnstalleerde modellen controleren
ollama pull qwen2.5:3b      # ontbrekend model installeren
```

Veelvoorkomende oorzaken: Ollama niet gestart, model niet geïnstalleerd, onvoldoende GPU-geheugen

**GLM-modus:**
- Bevestig dat `GLM_API_KEY` correct is
- Bevestig `GLM_EMBEDDING_DIMENSIONS=768` (moet overeenkomen met de Neo4j-vectorindex)
- GLM API-endpoint: `https://open.bigmodel.cn/api/paas/v4/`

**GROQ-modus:**
- Bevestig dat `GROQ_API_KEY` correct is
- Overweeg over te stappen naar de GLM-modus wanneer de Rate Limit vaak optreedt
- GROQ biedt geen Embedding; zorg dat de Ollama-inbedder beschikbaar is

**OpenRouter-modus:**
- Bevestig dat `OPENROUTER_API_KEY` correct is en `OPENROUTER_MODEL` een geldige model-ID is (zie https://openrouter.ai/models)
- Biedt geen Embedding; zorg dat de Ollama-inbedder beschikbaar is

**DeepSeek-modus:**
- Bevestig dat `DEEPSEEK_API_KEY` correct is
- Als `Prompt must contain the word 'json'` verschijnt: dit is een harde vereiste van DeepSeeks `json_object`-modus; de client heeft een ingebouwde veiligheidsbescherming; als het toch verschijnt, bevestig dan dat je de nieuwste versie van `src/deepseek_client.py` gebruikt en herstart de dienst
- Biedt geen Embedding; zorg dat de Ollama-inbedder beschikbaar is

### MCP-verbindingsfout

Als `Invalid request parameters` of `Received request before initialization was complete` verschijnt:

1. Bevestig dat je de HTTP-transportmodus gebruikt (**niet SSE**)
2. Bevestig dat de client is ingesteld op `"type": "http"`, `"url": "http://localhost:8000/mcp"`
3. Herstart de dienst: `pm2 restart graphiti-mcp-http --update-env`
4. Voer `/mcp` uit in Claude Code om opnieuw verbinding te maken

### Geheugen toevoegen verloopt traag

- **Ollama**: controleer de modelgrootte (`qwen2.5:3b` is 5-10 keer sneller dan `7b`), bevestig dat de GPU wordt gebruikt (`ollama ps`)
- **GLM**: elke add_episode vereist 10-20+ LLM-netwerkrondes; ~22s voor korte tekst is normaal
- **GROQ**: de Rate Limit veroorzaakt veel herhaalpogingen; bij frequent gebruik is overstappen naar GLM of Ollama aanbevolen
- Gebruik `background=true` om blokkering te voorkomen
- Verlaag `GRAPHITI_CHUNK_THRESHOLD` om lange tekst eerder te segmenteren

### PM2-problemen

```bash
pm2 status                                        # status controleren
pm2 logs graphiti-mcp-http --err --lines 50        # foutlogs
lsof -i :8000                                     # poortgebruik controleren
pm2 delete graphiti-mcp-http && pm2 start ecosystem.config.cjs  # volledig herstarten
```

## Diagnostische ontwikkeltools

```bash
uv run python tools/status_report.py           # geïntegreerd statusrapport (Neo4j + Ollama + configuratie)
uv run python tools/validate_config.py         # .env en configuratie-integriteit valideren
uv run python tools/performance_diagnose.py    # LLM-prestatiediagnose
uv run python tools/inspect_schema.py          # Neo4j-index- en beperkingencontrole
uv run python tools/migrate_embeddings.py      # Embedding-modelmigratie (vectoren opnieuw genereren na modelwissel)
```

### Embedding-modelmigratie

Na het wisselen van embedding-model (bijv. `nomic-embed-text` → `bge-m3`) kun je de migratietool gebruiken om alle bestaande vectoren opnieuw te genereren en zo een consistente zoekkwaliteit te waarborgen:

```bash
# Voorbeeld van het te migreren aantal
uv run python tools/migrate_embeddings.py --dry-run

# Volledige migratie (ondersteunt hervatten vanaf onderbrekingspunt)
uv run python tools/migrate_embeddings.py

# Alleen een opgegeven groep migreren
uv run python tools/migrate_embeddings.py --group-id myproject

# Doorgaan vanaf onderbrekingspunt (opnieuw uitvoeren na onderbreking)
uv run python tools/migrate_embeddings.py --resume
```

> **Compatibiliteit**: `bge-m3` is van nature 1024-dimensionaal; het systeem kapt automatisch af naar 768 dimensies om compatibel te zijn met de bestaande Neo4j-vectorindex. Gegevens van vóór en na de migratie kunnen naast elkaar bestaan, maar het wordt aanbevolen een volledige migratie uit te voeren voor de beste zoekkwaliteit.

## Documentatie

- [Instructies voor het gebruik van tools](../使用工具的指令.md) — gids en beste praktijken voor het gebruik van MCP-tools
- [Graphiti Memory Rules](../graphiti-memory-rules.md) — uitleg over geheugenregels

## Licentie

MIT License
