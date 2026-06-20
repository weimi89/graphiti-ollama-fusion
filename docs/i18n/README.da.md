# Graphiti MCP Server

Hukommelsestjeneste til vidensgrafer — en MCP-server, der integrerer flere LLM-udbydere (Ollama / GLM / GROQ / OpenRouter / DeepSeek) med Neo4j-grafdatabasen.

Udviklet som en udvidelse af [getzep/graphiti](https://github.com/getzep/graphiti), med understøttelse af fleksibel skift mellem lokal Ollama og cloud-baserede LLM'er, og hvor Embedding-udbyderen kan angives uafhængigt (afkoblet fra LLM'en).

## Funktioner

- **Intelligent hukommelseshåndtering** — brug af vidensgrafer til at gemme og hente komplekse hukommelsesrelationer
- **Semantisk søgning** — hybrid søgning baseret på vektor-embeddings (vektor + nøgleord + grafgennemløb)
- **16 søgestrategier** — avanceret søgning understøtter flere genrangeringsmetoder som RRF, MMR, Cross-Encoder m.fl.
- **Flere LLM-udbydere** — understøtter Ollama (lokal), GLM (Zhipu AI, gratis), GROQ (hurtig inferens), OpenRouter (samler modeller fra flere udbydere) og DeepSeek, med skift via en enkelt miljøvariabel
- **Embedding afkoblet fra LLM** — `EMBEDDING_PROVIDER` kan angive embedder uafhængigt, og cloud-LLM'er falder automatisk tilbage til lokal `bge-m3`
- **Dobbeltmodel-fordeling** — i Ollama-tilstand bruger komplekse opgaver hovedmodellen, mens enkle opgaver automatisk skifter til en mindre model for at forbedre ydeevnen
- **Intelligent indholdsopdeling** — lange tekster opdeles automatisk i afsnit for at reducere LLM-belastningen (tærskel kan konfigureres)
- **Hukommelsesbehandling i baggrunden** — tilføjelse af hukommelse kan køre i baggrunden, så MCP-kaldet returnerer øjeblikkeligt; opgavestatus gemmes vedvarende i SQLite og ufuldstændige opgaver gendannes automatisk efter genstart
- **Hukommelses-deduplikering** — registrerer automatisk eksisterende hukommelser, der ligner hinanden meget, for at undgå dobbeltlagring
- **Konfliktregistrering** — registrerer modstridende fakta mellem to entiteter og identificerer udløbet og gyldig information
- **Fællesskabsregistrering** — automatisk klyngedannelse af relaterede entiteter baseret på Label Propagation-algoritmen
- **Vigtighedssporing** — registrerer automatisk adgangsfrekvensen for entiteter, og søgeresultater rangeres efter vigtighed
- **Intelligent glemsel** — identificerer og rydder forældede hukommelser med lav adgang for at holde grafen kompakt
- **Bulk-import** — indsend flere hukommelser på én gang, velegnet til migrering af store datamængder
- **Strukturerede tripler** — tilføj direkte "subjekt-relation-objekt", spring LLM-udtrækning over og fuldfør på sekunder
- **Web-administrationsgrænseflade** — indbygget dashboard, gennemsyn, søgning, visualisering af vidensgraf, AI-spørgsmål-og-svar, fællesskabsgennemsyn, kvalitetsvedligeholdelse, bulk-import og kørselsindstillinger
- **Flersproget (i18n)** — svarbeskeder understøtter 33 sprog (inkl. zh-TW / en / zh-CN / ja / pt-BR / ko / es / de / fr m.fl.; zh-TW/en/zh-CN/ja er håndskrevne, øvrige leveres af det genererede lag); MCP-værktøjer følger `SERVER_LANG`, mens REST API automatisk forhandler ud fra HTTP `Accept-Language`
- **Mørkt/lyst tema** — Web-grænsefladen understøtter temaskift
- **Sikker tilstand** — valgfri hurtig hukommelsestilføjelse, der springer entitetsudtrækning over
- **Docker-understøttelse** — indbygget Dockerfile med understøttelse af containeriseret udrulning
- **Samtidighedssikker** — asyncio.Lock beskytter initialisering og forhindrer race conditions
- **Lagdelt sundhedstjek** — `/health` (liveness) + `/health/ready` (readiness)

## Systemkrav

| Punkt | Krav |
|------|------|
| Python | 3.10+ (3.11+ anbefales) |
| Neo4j | 4.0+ (`bolt://localhost:7687`) |
| LLM-udbyder | Ollama / GLM / GROQ / OpenRouter / DeepSeek (vælg én af fem) |
| Node.js | 18+ (kun til PM2-baggrundskørsel, valgfrit) |
| Diskplads | ~3 GB (Ollama-modeller + Neo4j-data) |

### Valg af LLM-udbyder

Skift via miljøvariablen `LLM_PROVIDER` (`ollama` / `glm` / `groq` / `openrouter` / `deepseek`):

| Udbyder | Kendetegn | LLM-model | Embedding | Velegnet til |
|--------|------|----------|-----------|----------|
| **Ollama** (standard) | Fuldt lokal, data forlader ikke maskinen | `qwen2.5:3b` | `bge-m3` (fremragende til kinesisk + RAG) | Har GPU, lægger vægt på privatliv |
| **GLM** | Gratis cloud, stabil uden ratebegrænsning | `glm-4-flash` (gratis) | `embedding-3` | Ingen GPU, søgningsintensive scenarier |
| **GROQ** | Ultrahurtig inferens | `llama-3.3-70b-versatile` | Falder tilbage til Ollama `bge-m3` | Lejlighedsvis skrivning, fokus på kvalitet |
| **OpenRouter** | Samler modeller fra flere udbydere, inkl. gratis kvote | `stepfun/step-3.5-flash:free` m.fl. | Falder tilbage til Ollama `bge-m3` | Ønsker at bruge en bestemt cloud-model |
| **DeepSeek** | DeepSeek cloud, høj pris-ydelse | `deepseek-v4-flash` / `deepseek-v4-pro` | Falder tilbage til Ollama `bge-m3` | Kinesisk forståelse, billig cloud |

> **Embedding afkoblet fra LLM**: embedderen angives uafhængigt via `EMBEDDING_PROVIDER` (`ollama` / `glm`), og følger `LLM_PROVIDER`, når den ikke er angivet. I praksis bruger kun `glm` GLM `embedding-3`, mens alle øvrige (inkl. cloud-LLM'er som GROQ / OpenRouter / DeepSeek, der ikke tilbyder Embedding) automatisk bruger Ollama `bge-m3`. **Derfor kræves der stadig en lokal Ollama til embeddingtjenesten, når man bruger en hvilken som helst cloud-LLM (medmindre embedding også er sat til glm).**

#### Ollama-tilstand (lokal)

```bash
# LLM-hovedmodel (qwen2.5:3b anbefales, bedste balance mellem hastighed og stabilitet)
ollama pull qwen2.5:3b

# Embedding-model (påkrævet, bruges til vektorsøgning)
ollama pull bge-m3
```

> **Bemærkninger om modelvalg**:
> - `qwen2.5:3b` — anbefales, ~2s/kald, ~100 t/s, 100 % stabil med graphiti-cores strukturerede output
> - `qwen2.5:7b` — bedre resultater, men 5-10 gange langsommere, velegnet til scenarier med fokus på kvalitet
> - `qwen2.5:1.5b` — hurtigst, men **ustabil** (kun 33 % succesrate for struktureret JSON), anbefales ikke

#### GLM-tilstand (Zhipu AI cloud)

```bash
# .env-indstilling
LLM_PROVIDER=glm
GLM_API_KEY=your_api_key          # Hentes fra https://open.bigmodel.cn
GLM_MODEL=glm-4-flash             # Gratis model
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768      # Skal stemme overens med Neo4j-vektorindeksets dimension
```

> **GLM-ydelsesreference**: skrivning ~22s (kort tekst), søgning ~0,34s, nul ratebegrænsningsfejl, 2-5 gange langsommere end lokal Ollama, men helt gratis.

#### GROQ-tilstand (hurtig inferens)

```bash
# .env-indstilling
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key         # Hentes fra https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile
```

> **Bemærk**: GROQ tilbyder ikke en Embedding-tjeneste og skal kombineres med Ollama-embedderen (automatisk tilbagefald), eller `EMBEDDING_PROVIDER` skal sættes til glm. GROQ har en streng ratebegrænsning, og højfrekvent brug udløser mange genforsøg.

#### OpenRouter-tilstand (samler modeller fra flere udbydere)

```bash
# .env-indstilling
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_api_key       # Hentes fra https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free   # Kan ændres til en hvilken som helst OpenRouter-model
```

> **Bemærk**: OpenRouter tilbyder ikke Embedding og falder automatisk tilbage til Ollama `bge-m3`. Modellisten findes på https://openrouter.ai/models (inkl. flere `:free`-gratis modeller).

#### DeepSeek-tilstand (DeepSeek)

```bash
# .env-indstilling
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key         # Hentes fra https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash      # Anbefales; eller deepseek-v4-pro (bedre resultater)
```

> **Bemærk**: DeepSeek tilbyder ikke Embedding og falder automatisk tilbage til Ollama `bge-m3`. `deepseek-chat` / `deepseek-reasoner` udfases den 2026-07-24, og det anbefales at skifte til `deepseek-v4-flash` / `deepseek-v4-pro`. DeepSeek kræver strengt, at prompten i `json_object`-tilstand indeholder strengen "json"; klienten har en indbygget fail-safe-beskyttelse, så ingen yderligere indstillinger er nødvendige.

## Hurtig start

### 1. Forberedelse

Bekræft, at Neo4j allerede kører på den lokale maskine, og forbered den tilsvarende tjeneste afhængigt af den valgte LLM-udbyder:

```bash
# Bekræft, at Neo4j kører (påkrævet)
neo4j status
# Eller brug Docker: docker run -d -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/your_password neo4j:latest

# Ollama-tilstand: bekræft, at Ollama kører
ollama list
# Hvis ikke startet: ollama serve

# GLM / GROQ-tilstand: kræver kun en gyldig API-nøgle, ingen lokal tjeneste nødvendig
```

### 2. Installér afhængigheder

```bash
git clone <repo-url>
cd graphiti
uv sync
```

> **Bemærk**: Dette projekt bruger [uv](https://github.com/astral-sh/uv) til at håndtere afhængigheder. Hvis det ikke er installeret: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 3. Konfigurér miljøet

```bash
cp .env.example .env
```

Redigér `.env`, og som **minimum** skal følgende punkter ændres:

```bash
NEO4J_PASSWORD=your_actual_password  # Påkrævet: Neo4j-adgangskode
LLM_PROVIDER=ollama                  # ollama / glm / groq / openrouter / deepseek
OLLAMA_MODEL=qwen2.5:3b              # Ollama-tilstand: lokal LLM-model
# GLM_API_KEY=your_key               # GLM-tilstand: Zhipu AI API-nøgle
# GROQ_API_KEY=your_key              # GROQ-tilstand: GROQ API-nøgle
# OPENROUTER_API_KEY=your_key        # OpenRouter-tilstand: API-nøgle
# DEEPSEEK_API_KEY=your_key          # DeepSeek-tilstand: API-nøgle
```

### 4. Start tjenesten

```bash
# HTTP-tilstand (anbefales, inkluderer Web-administrationsgrænseflade)
uv run python graphiti_mcp_server.py --transport http --port 8000

# Eller brug PM2-baggrundskørsel (anbefales til langvarig drift)
pm2 start ecosystem.config.cjs
```

### 5. Verificér tjenesten

Efter start kan følgende endpoints tilgås:

| Endpoint | Beskrivelse |
|------|------|
| http://localhost:8000/ | Web-administrationsgrænseflade |
| http://localhost:8000/mcp | MCP-endpoint (til forbindelse fra MCP-klienter) |
| http://localhost:8000/health | Sundhedstjek (liveness) |
| http://localhost:8000/health/ready | Dybdetjek (inkl. Neo4j-forbindelse) |
| http://localhost:8000/api/stats | REST API-statistik |

## Projektstruktur

```
graphiti/
├── graphiti_mcp_server.py        # Hovedindgang — MCP-værktøjsdefinitioner (19 værktøjer)
├── src/
│   ├── config.py                 # Konfigurationshåndtering (GraphitiConfig, understøtter lagdeling af JSON/.env)
│   ├── web_api.py                # Web-administrationsgrænseflade REST API (30+ endpoints)
│   ├── ollama_graphiti_client.py  # Ollama LLM-klient (dobbeltmodel-fordeling)
│   ├── openai_compat_client.py   # OpenAI-kompatibel LLM-basisklasse (json_object + forenklet schema + json fail-safe)
│   ├── glm_client.py             # GLM (Zhipu AI) LLM-klient (arver OpenAICompatClient)
│   ├── openrouter_client.py      # OpenRouter LLM-klient (arver OpenAICompatClient)
│   ├── deepseek_client.py        # DeepSeek LLM-klient (arver OpenAICompatClient)
│   ├── ollama_embedder.py        # Ollama embedding-modeladapter
│   ├── content_preprocessor.py   # Intelligent indholdsopdeling (lange tekster opdeles automatisk)
│   ├── deduplication.py          # Hukommelses-deduplikering (sammenligning af cosinus-lighed)
│   ├── importance.py             # Vigtighedssporing og intelligent glemsel
│   ├── safe_memory_add.py        # Sikker hukommelsestilføjelse (springer entitetsudtrækning over)
│   ├── task_store.py             # SQLite-persistering af baggrundsopgaver (TaskStore)
│   ├── timezone_utils.py         # Tidszonekonvertering (UTC→visning i lokal tidszone)
│   ├── i18n.py                   # Backend flersproget (REST følger Accept-Language, MCP følger SERVER_LANG)
│   ├── i18n_generated.py         # Automatisk genererede sprogoverstyringer (GENERATED_MESSAGE_OVERRIDES)
│   ├── exceptions.py             # Struktureret undtagelseshåndtering (12 undtagelsesklasser)
│   └── logging_setup.py          # Logsystem (tidsbaseret rotation + ydelsesovervågning)
├── web/                          # Web-administrationsgrænseflade frontend (SPA, ingen build)
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js                # REST API-indpakning
│       ├── components.js         # UI-komponentrendering (inkl. fællesskabsside)
│       └── app.js                # SPA-routing, tilstandshåndtering
├── tests/                        # Testpakke (203 tests)
│   ├── test_content_preprocessor.py  # Test af opdelingslogik (17 stk.)
│   ├── test_new_features.py      # Test af nye funktioner (32 stk.)
│   ├── test_i18n.py             # Test af flersproget (57 stk.)
│   ├── test_unit.py              # Enhedstests
│   ├── test_web_api.py           # Web API-tests
│   ├── test_web_ui_features.py   # Test af Web UI-funktioner
│   ├── test_integration_manual.py # Manuel integrationstest
│   └── bench_deepseek_flash_vs_pro.py # DeepSeek flash/pro ydelses-benchmark-script
├── tools/                        # Udviklings- og diagnoseværktøjer
│   ├── status_report.py          # Samlet statusrapport
│   ├── validate_config.py        # Konfigurationsvalidering
│   ├── performance_diagnose.py   # Ydelsesdiagnose
│   ├── inspect_schema.py         # Tjek af Neo4j-struktur
│   ├── batch_reprocess.py        # Batch-genbehandling
│   └── migrate_embeddings.py     # Migrering af Embedding-model
├── docs/                         # Dokumentation
├── logs/                         # Logge (tidsbaseret rotation, gemmes som standard i 30 dage)
├── Dockerfile                    # Docker containeriseret udrulning
└── ecosystem.config.cjs          # PM2-konfiguration
```

## Opsætning af MCP-klient

### HTTP-tilstand (anbefales)

Velegnet til MCP-klienter, der understøtter HTTP, såsom Claude Code, Cline m.fl.:

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

### STDIO-tilstand

Velegnet til klienter, der skal starte processen direkte, såsom Claude Desktop:

**Placering af konfigurationsfil:**
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

> **Bemærk**: SSE-tilstand (`--transport sse`) anbefales ikke længere. MCP 1.x har kompatibilitetsproblemer med session-initialisering; brug i stedet HTTP-tilstand.

## MCP-værktøjer (19 stk.)

### Hukommelseshåndtering (7 stk.)

| Værktøj | Beskrivelse |
|------|------|
| `add_memory_simple` | Tilføj hukommelse til vidensgrafen (understøtter baggrundsbehandling, intelligent opdeling, deduplikeringstjek) |
| `add_episode_bulk` | Tilføj flere hukommelser i bulk (baggrundsbehandling som standard) |
| `add_triplet` | Tilføjelse af struktureret tripel (springer LLM over, fuldfører på sekunder) |
| `search_memory_nodes` | Søg i hukommelsesknuder (understøtter 16 søgestrategier, tidsfiltrering) |
| `search_memory_facts` | Søg i hukommelsesfakta (understøtter filtrering efter relationstype, tidsinterval, gyldighedsfiltrering) |
| `advanced_search` | Avanceret søgning (16 strategier, returnerer knuder+kanter+fællesskaber+segmenter) |
| `get_episodes` | Hent de seneste hukommelsessegmenter |

### Vidensanalyse (3 stk.)

| Værktøj | Beskrivelse |
|------|------|
| `check_conflicts` | Registrér faktakonflikter mellem to entiteter (gyldig vs. udløbet) |
| `get_node_edges` | Udforsk en knudes indgående og udgående kantrelationer |
| `build_communities` | Udløs fællesskabsregistrering og klyngedannelse (baggrundsbehandling som standard) |

### Hukommelsesvedligeholdelse (2 stk.)

| Værktøj | Beskrivelse |
|------|------|
| `get_stale_memories` | Forespørg på forældede hukommelser med lav adgang |
| `cleanup_stale_memories` | Ryd forældede hukommelser (dry_run-forhåndsvisningstilstand som standard) |

### Opgavehåndtering

| Værktøj | Beskrivelse |
|------|------|
| `get_memory_task_status` | Forespørg på fremdrift og resultat af baggrundsopgaver til hukommelsesbehandling |

### Sletning og forespørgsel

| Værktøj | Beskrivelse |
|------|------|
| `delete_episode` | Slet hukommelsessegment |
| `delete_entity_edge` | Slet entitetskant (relation) |
| `get_entity_edge` | Hent detaljerede oplysninger om entitetskant |

### Systemadministration

| Værktøj | Beskrivelse |
|------|------|
| `get_status` | Hent tjenestestatus (Neo4j, LLM, embedder) |
| `test_connection` | Test forbindelse til Neo4j / LLM / embedder |
| `clear_graph` | Ryd grafdatabasen (understøtter rydning efter group_id) |

## Værktøjsparametre

### add_memory_simple

| Parameter | Type | Påkrævet | Standardværdi | Beskrivelse |
|------|------|------|--------|------|
| `name` | string | Y | | Hukommelsesnavn |
| `episode_body` | string | Y | | Hukommelsesindhold (opdeles automatisk over 800 tegn) |
| `group_id` | string | | `"default"` | Gruppe-ID (anbefales adskilt pr. projekt) |
| `source` | string | | `"text"` | Kildetype: `text` / `json` / `message` |
| `source_description` | string | | `"MCP Server"` | Kildebeskrivelse |
| `use_safe_mode` | bool | | `false` | Sikker tilstand (springer entitetsudtrækning over, hurtig, men hukommelsen kan ikke søges) |
| `background` | bool | | `false` | Baggrundsbehandling (returnerer øjeblikkeligt task_id, velegnet til lange tekster) |
| `force` | bool | | `false` | Spring deduplikeringstjek over (tving tilføjelse) |
| `excluded_entity_types` | list | | | Udelukkede entitetstyper (reducerer unødvendig udtrækningsmængde) |

> **Ydelsestips**:
> - Kort tekst (<800 tegn): behandles direkte, fuldføres typisk på 30-40 sekunder
> - Lang tekst (>800 tegn): opdeles automatisk i flere segmenter, behandles samtidigt med `add_episode_bulk` (~33 % hurtigere end seriel)
> - Brug `background=true` for at undgå, at MCP-kaldet blokerer, og spor fremdriften via `get_memory_task_status`
> - `use_safe_mode=true` fuldfører på sekunder, men hukommelsen kan ikke findes af søgeværktøjer
> - Når deduplikering er aktiveret, advares der om meget lignende hukommelser (`force=true` kan springe det over)

### add_episode_bulk

| Parameter | Type | Påkrævet | Standardværdi | Beskrivelse |
|------|------|------|--------|------|
| `episodes` | list | Y | | Hukommelsesliste, hvor hvert element indeholder `name` og `content` |
| `group_id` | string | | `"default"` | Gruppe-ID |
| `source` | string | | `"text"` | Kildetype |
| `background` | bool | | `true` | Baggrundsbehandling (bulk er typisk tidskrævende) |

### add_triplet

| Parameter | Type | Påkrævet | Standardværdi | Beskrivelse |
|------|------|------|--------|------|
| `source_name` | string | Y | | Navn på kildeentitet (f.eks. "Alice") |
| `target_name` | string | Y | | Navn på målentitet (f.eks. "Google") |
| `relation_name` | string | Y | | Relationsnavn (f.eks. "works_at") |
| `fact` | string | Y | | Faktabeskrivelse (f.eks. "Alice works at Google") |
| `group_id` | string | | `"default"` | Gruppe-ID |
| `source_labels` | list | | | Etiketter for kildeentitet |
| `target_labels` | list | | | Etiketter for målentitet |

### search_memory_nodes

| Parameter | Type | Påkrævet | Standardværdi | Beskrivelse |
|------|------|------|--------|------|
| `query` | string | Y | | Søgenøgleord (naturligt sprog) |
| `max_nodes` | int | | `10` | Maksimalt antal returnerede |
| `group_ids` | list | | | Gruppefiltrering (forenet søgning på tværs af flere grupper) |
| `entity_types` | list | | | Filtrering efter entitetstype |
| `search_recipe` | string | | | Søgestrategi (se avanceret søgning) |
| `created_after` | string | | | Nedre grænse for oprettelsestidspunkt (ISO datetime) |
| `created_before` | string | | | Øvre grænse for oprettelsestidspunkt (ISO datetime) |

### search_memory_facts

| Parameter | Type | Påkrævet | Standardværdi | Beskrivelse |
|------|------|------|--------|------|
| `query` | string | Y | | Søgenøgleord |
| `max_facts` | int | | `10` | Maksimalt antal returnerede |
| `group_ids` | list | | | Gruppefiltrering |
| `center_node_uuid` | string | | | UUID for centerknude (udforsk relationer for en bestemt knude) |
| `edge_types` | list | | | Filtrering efter relationstype (f.eks. `["works_at"]`) |
| `created_after` | string | | | Nedre grænse for oprettelsestidspunkt (ISO datetime) |
| `created_before` | string | | | Øvre grænse for oprettelsestidspunkt (ISO datetime) |
| `only_valid` | bool | | `false` | Returnér kun fakta, der ikke er udløbet |

### advanced_search

| Parameter | Type | Påkrævet | Standardværdi | Beskrivelse |
|------|------|------|--------|------|
| `query` | string | Y | | Søgenøgleord |
| `search_recipe` | string | | `"combined_rrf"` | Søgestrategi (16 valgmuligheder) |
| `max_results` | int | | `10` | Maksimalt antal returnerede |
| `group_ids` | list | | | Gruppefiltrering |
| `center_node_uuid` | string | | | UUID for centerknude |

**Tilgængelige søgestrategier (search_recipe):**

| Kategori | Strategi | Beskrivelse |
|------|------|------|
| Samlet | `combined_rrf` | Samlet RRF-fusion (standard, anbefales) |
| Samlet | `combined_mmr` | Samlet MMR-mangfoldighedsgenrangering |
| Samlet | `combined_cross_encoder` | Samlet Cross-Encoder-finrangering |
| Kant | `edge_rrf` / `edge_mmr` / `edge_cross_encoder` | Kantsøgning (3 rangeringer) |
| Kant | `edge_node_distance` / `edge_episode_mentions` | Kantsøgning (grafafstand/antal henvisninger) |
| Knude | `node_rrf` / `node_mmr` / `node_cross_encoder` | Knudesøgning (3 rangeringer) |
| Knude | `node_node_distance` / `node_episode_mentions` | Knudesøgning (grafafstand/antal henvisninger) |
| Fællesskab | `community_rrf` / `community_mmr` / `community_cross_encoder` | Fællesskabssøgning |

### check_conflicts

| Parameter | Type | Påkrævet | Standardværdi | Beskrivelse |
|------|------|------|--------|------|
| `source_name` | string | Y | | Navn på kildeentitet |
| `target_name` | string | Y | | Navn på målentitet |
| `group_id` | string | | `"default"` | Gruppe-ID |

### get_node_edges

| Parameter | Type | Påkrævet | Standardværdi | Beskrivelse |
|------|------|------|--------|------|
| `node_uuid` | string | Y | | Knude-UUID |
| `include_inbound` | bool | | `true` | Inkludér indgående kanter |
| `include_outbound` | bool | | `true` | Inkludér udgående kanter |
| `max_edges` | int | | `50` | Maksimalt antal returnerede |

### build_communities

| Parameter | Type | Påkrævet | Standardværdi | Beskrivelse |
|------|------|------|--------|------|
| `group_ids` | list | | | Angiv grupper (lad være tom for alle) |
| `background` | bool | | `true` | Baggrundsbehandling |

### get_stale_memories

| Parameter | Type | Påkrævet | Standardværdi | Beskrivelse |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Antal dage uden adgang, før det betragtes som forældet |
| `min_access_count` | int | | `2` | Medtages kun, hvis adgangsantallet er lavere end denne værdi |
| `group_id` | string | | | Gruppefiltrering |
| `limit` | int | | `50` | Maksimalt antal returnerede |

### cleanup_stale_memories

| Parameter | Type | Påkrævet | Standardværdi | Beskrivelse |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Tærskel for forældelsesdage |
| `min_access_count` | int | | `2` | Tærskel for minimumsadgangsantal |
| `group_id` | string | | | Gruppefiltrering |
| `dry_run` | bool | | `true` | Forhåndsvisningstilstand (sletter ikke reelt) |
| `limit` | int | | `50` | Maksimalt antal behandlede |

### get_memory_task_status

| Parameter | Type | Påkrævet | Beskrivelse |
|------|------|------|------|
| `task_id` | string | Y | Baggrundsopgave-ID (returneres af `add_memory_simple(background=true)`) |

## Web-administrationsgrænseflade

I HTTP-tilstand kan den tilgås på `http://localhost:8000/`.

**Funktioner:**
- Dashboard — statistik over antal knuder, fakta og hukommelsessegmenter
- Entitetsknuder — gennemsyn, filtrering, vektorsøgning
- Faktarelationer — gennemsyn, filtrering, vektorsøgning
- Hukommelsessegmenter — gennemsyn, fuldtekstsøgning, sletning
- Fællesskabsgennemsyn — liste over fællesskabsknuder, resuméer, udløsning af fællesskabsopbygning
- Tripel-formular — tilføj direkte struktureret viden i formen "subjekt-relation-objekt"
- Gruppehåndtering — filtrering efter gruppe, batch-sletning
- Visualisering af vidensgraf — grafisk fremstilling af knuderelationer
- AI-spørgsmål-og-svar — intelligent spørgsmål-og-svar baseret på vidensgrafen
- Kvalitetsvedligeholdelse — hukommelseskvalitetsmålinger og oprydningsværktøjer
- Bulk-import — importér flere hukommelsessegmenter på én gang (JSON, maks. 500 pr. gang)
- Kørselsindstillinger — vis aktuelle effektive indstillinger og justér udvalgte parametre uden genstart
- Temaskift — mørkt/lyst tema

**REST API:**

| Endpoint | Metode | Beskrivelse |
|------|------|------|
| `/api/stats` | GET | Dashboard-statistik |
| `/api/groups` | GET | Hent alle group_id |
| `/api/groups/stats` | GET | Knude-/fakta-/segmentstatistik pr. gruppe |
| `/api/nodes` | GET | Gennemse entitetsknuder (sidevisning) |
| `/api/facts` | GET | Gennemse fakta (sidevisning) |
| `/api/episodes` | GET | Gennemse hukommelsessegmenter (sidevisning) |
| `/api/nodes/{uuid}/relations` | GET | Hent indgående/udgående kantrelationer for en knude |
| `/api/search/nodes` | GET | Vektorsøgning i knuder |
| `/api/search/facts` | GET | Vektorsøgning i fakta |
| `/api/search/episodes` | GET | Søg i hukommelsessegmenter |
| `/api/search/advanced` | GET | Avanceret søgning (16 strategier) |
| `/api/communities` | GET | Gennemse fællesskabsknuder (sidevisning) |
| `/api/communities/build` | POST | Udløs fællesskabsopbygning |
| `/api/memory/add` | POST | Tilføj enkelt hukommelse |
| `/api/memory/add-bulk` | POST | Tilføj hukommelser i bulk |
| `/api/memory/add-triplet` | POST | Tilføj tripel |
| `/api/import/episodes` | POST | Bulk-import af hukommelsessegmenter (JSON, maks. 500 pr. gang) |
| `/api/memory/tasks` | GET | List baggrundsopgaver (understøtter statusfiltrering) |
| `/api/memory/tasks/{id}` | GET | Forespørg på status for en enkelt opgave |
| `/api/timeline` | GET | Tidslinje-gennemsyn |
| `/api/graph/subgraph` | GET | Hent delgraf (visualisering) |
| `/api/graph/all` | GET | Hent komplet graf (visualisering) |
| `/api/ask` | GET | AI-spørgsmål-og-svar (baseret på grafsøgning) |
| `/api/analytics/top-nodes` | GET | Knuder med høj forbindelsesgrad/høj adgangsfrekvens |
| `/api/analytics/quality` | GET | Kvalitetsmålinger for vidensgrafen |
| `/api/analytics/stale` | GET | Forespørg på forældede hukommelser |
| `/api/analytics/cleanup` | POST | Ryd forældede hukommelser |
| `/api/config` | GET | Hent aktuelle effektive indstillinger (uden API-nøgler) |
| `/api/config` | PATCH | Opdatér redigerbare indstillinger under kørsel (gælder kun denne proces, nulstilles ved genstart) |
| `/api/nodes/{uuid}` | DELETE | Slet knude |
| `/api/episodes/{uuid}` | DELETE | Slet hukommelsessegment |
| `/api/facts/{uuid}` | DELETE | Slet faktum |
| `/api/groups/{group_id}` | DELETE | Slet hele gruppen |

## Konfiguration

### Miljøvariabler (.env)

Konfigurationen bruger en lagdelingsmekanisme: JSON-konfigurationsfilen som grundlag, og miljøvariabler overstyrer enkelte værdier.

```bash
# === Påkrævet ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password        # Skal ændres

# === Valg af LLM-udbyder ===
LLM_PROVIDER=ollama                 # ollama / glm / groq / openrouter / deepseek

# === Embedding-udbyder (valgfri, følger som standard LLM_PROVIDER) ===
# Kun glm bruger GLM Embedding, alle øvrige bruger Ollama bge-m3
# EMBEDDING_PROVIDER=ollama         # ollama / glm

# === Ollama-konfiguration (bruges når LLM_PROVIDER=ollama) ===
OLLAMA_MODEL=qwen2.5:3b             # Hovedmodel (qwen2.5:3b anbefales)
OLLAMA_SMALL_MODEL=qwen2.5:3b       # Lille model (til enkle opgaver, kan vælges en anden model)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.1

# === GLM-konfiguration (bruges når LLM_PROVIDER=glm) ===
GLM_API_KEY=your_api_key            # Hentes fra https://open.bigmodel.cn
GLM_MODEL=glm-4-flash               # Gratis model
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768

# === GROQ-konfiguration (bruges når LLM_PROVIDER=groq) ===
GROQ_API_KEY=your_api_key           # Hentes fra https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile

# === OpenRouter-konfiguration (bruges når LLM_PROVIDER=openrouter) ===
OPENROUTER_API_KEY=your_api_key     # Hentes fra https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free

# === DeepSeek-konfiguration (bruges når LLM_PROVIDER=deepseek) ===
DEEPSEEK_API_KEY=your_api_key       # Hentes fra https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash    # Eller deepseek-v4-pro

# === Ollama embedding-model (bruges altid ved embedding, der ikke er glm) ===
OLLAMA_EMBEDDING_MODEL=bge-m3
OLLAMA_EMBEDDING_DIMENSIONS=768

# === Visning og sprog (valgfri) ===
GRAPHITI_DISPLAY_TIMEZONE=Asia/Taipei # Visningstidszone for tidsstempler returneret af API (IANA-navn; lagring forbliver UTC)
SERVER_LANG=zh-TW                     # Svarsprog for MCP-værktøjer (fulde locales ses i src/i18n.py); REST API følger i stedet Accept-Language

# === Hukommelsesydelse (valgfri) ===
GRAPHITI_CHUNK_THRESHOLD=800         # Tegntærskel, der udløser intelligent opdeling
GRAPHITI_MAX_CHUNK_SIZE=600          # Maksimalt antal tegn pr. segment
GRAPHITI_MAX_COROUTINES=10            # Maksimalt antal samtidige coroutiner
GRAPHITI_DEFAULT_BACKGROUND=false    # Om baggrundsbehandling er standard
TASK_DB_PATH=data/tasks.db           # SQLite-persisteringssti for baggrundsopgaver

# === Vigtighedssporing og intelligent glemsel (valgfri) ===
ENABLE_IMPORTANCE_TRACKING=true      # Aktivér adgangssporing
IMPORTANCE_WEIGHT=0.1                # Vigtighedsvægt
STALE_DAYS_THRESHOLD=30              # Tærskel for forældelsesdage
STALE_MIN_ACCESS_COUNT=2             # Minimumsadgangsantal

# === Logge ===
LOG_FILE=logs/graphiti_mcp_server.log
LOG_LEVEL=INFO
```

> **Den fulde liste over miljøvariabler** findes i `.env.example`

### JSON-konfigurationsfil

Velegnet til konfiguration, der kræver versionsstyring (miljøvariabler kan stadig overstyre):

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

## PM2-baggrundskørsel

```bash
npm install -g pm2

pm2 start ecosystem.config.cjs      # Start
pm2 status                           # Status
pm2 logs graphiti-mcp-http           # Live-logge
pm2 restart graphiti-mcp-http --update-env  # Genstart (genindlæs .env)

pm2 save && pm2 startup              # Indstil automatisk start ved opstart
```

> **Tip**: Efter ændring af `.env` skal der genstartes med flaget `--update-env`, ellers opdateres miljøvariablerne ikke.

## Docker-udrulning

```bash
docker build -t graphiti-mcp .

# Bemærk: Docker-containeren skal kunne forbinde til Neo4j og Ollama
# Det enkleste er at bruge host network
docker run -p 8000:8000 --env-file .env --network host graphiti-mcp

# Eller angiv eksplicit adresserne på eksterne tjenester
docker run -p 8000:8000 \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --env-file .env graphiti-mcp
```

## Test

```bash
# Kør alle tests (203 stk., ca. 1 sekund)
uv run python -m pytest tests/

# Detaljeret output
uv run python -m pytest tests/ -v

# Kør kun en bestemt test
uv run python -m pytest tests/test_content_preprocessor.py -v
uv run python -m pytest tests/test_new_features.py -v
uv run python -m pytest tests/test_unit.py -v
```

> **Bemærk**: De 3 async-tests i `test_integration_manual.py` kræver, at `pytest-asyncio` er installeret; når den mangler, vises Failed, men det påvirker ikke de øvrige tests. `bench_deepseek_flash_vs_pro.py` er et ydelses-benchmark-script og ikke en enhedstest.

## Fejlfinding

### Neo4j-forbindelse mislykkes

```bash
neo4j status                              # Tjek tjenestestatus
cypher-shell -u neo4j -p your_password    # Bekræft, at adgangskoden er korrekt
curl http://localhost:7474                 # Bekræft HTTP-porten
```

Almindelige årsager:
- Neo4j er ikke startet
- Forkert adgangskode (`NEO4J_PASSWORD` i `.env`)
- Porten er optaget, eller firewallen blokerer

### LLM-forbindelse mislykkes

**Ollama-tilstand:**
```bash
ollama serve                # Start Ollama-tjenesten
ollama list                 # Tjek installerede modeller
ollama pull qwen2.5:3b      # Installér den manglende model
```

Almindelige årsager: Ollama er ikke startet, modellen er ikke installeret, utilstrækkelig GPU-hukommelse

**GLM-tilstand:**
- Bekræft, at `GLM_API_KEY` er korrekt
- Bekræft `GLM_EMBEDDING_DIMENSIONS=768` (skal stemme overens med Neo4j-vektorindekset)
- GLM API-endpoint: `https://open.bigmodel.cn/api/paas/v4/`

**GROQ-tilstand:**
- Bekræft, at `GROQ_API_KEY` er korrekt
- Overvej at skifte til GLM-tilstand ved hyppig ratebegrænsning
- GROQ tilbyder ikke Embedding; sørg for, at Ollama-embedderen er tilgængelig

**OpenRouter-tilstand:**
- Bekræft, at `OPENROUTER_API_KEY` er korrekt, og at `OPENROUTER_MODEL` er et gyldigt model-ID (se https://openrouter.ai/models)
- Tilbyder ikke Embedding; sørg for, at Ollama-embedderen er tilgængelig

**DeepSeek-tilstand:**
- Bekræft, at `DEEPSEEK_API_KEY` er korrekt
- Hvis `Prompt must contain the word 'json'` opstår: dette er et hårdt krav i DeepSeeks `json_object`-tilstand, og klienten har en indbygget fail-safe-beskyttelse; hvis det stadig opstår, så bekræft, at du bruger den nyeste version af `src/deepseek_client.py`, og genstart tjenesten
- Tilbyder ikke Embedding; sørg for, at Ollama-embedderen er tilgængelig

### MCP-forbindelsesfejl

Hvis `Invalid request parameters` eller `Received request before initialization was complete` opstår:

1. Bekræft, at HTTP-transporttilstand bruges (**brug ikke SSE**)
2. Bekræft, at klienten er indstillet til `"type": "http"`, `"url": "http://localhost:8000/mcp"`
3. Genstart tjenesten: `pm2 restart graphiti-mcp-http --update-env`
4. Kør `/mcp` i Claude Code for at genoprette forbindelsen

### Hukommelsestilføjelse er langsom

- **Ollama**: tjek modelstørrelsen (`qwen2.5:3b` er 5-10 gange hurtigere end `7b`), bekræft, at GPU bruges (`ollama ps`)
- **GLM**: hver add_episode kræver 10-20+ netværksrundture til LLM'en, ~22s for kort tekst er en normal værdi
- **GROQ**: ratebegrænsning forårsager mange genforsøg; ved hyppig brug anbefales at skifte til GLM eller Ollama
- Brug `background=true` for at undgå blokering
- Sænk `GRAPHITI_CHUNK_THRESHOLD` for at opdele lange tekster tidligere

### PM2-problemer

```bash
pm2 status                                        # Tjek status
pm2 logs graphiti-mcp-http --err --lines 50        # Fejllogge
lsof -i :8000                                     # Tjek portoptagelse
pm2 delete graphiti-mcp-http && pm2 start ecosystem.config.cjs  # Fuld genstart
```

## Udviklings- og diagnoseværktøjer

```bash
uv run python tools/status_report.py           # Samlet statusrapport (Neo4j + Ollama + konfiguration)
uv run python tools/validate_config.py         # Validér .env og konfigurationsfuldstændighed
uv run python tools/performance_diagnose.py    # LLM-ydelsesdiagnose
uv run python tools/inspect_schema.py          # Tjek af Neo4j-indekser og -begrænsninger
uv run python tools/migrate_embeddings.py      # Migrering af Embedding-model (regenerér vektorer efter modelskift)
```

### Migrering af Embedding-model

Efter skift af embedding-model (f.eks. `nomic-embed-text` → `bge-m3`) kan migreringsværktøjet bruges til at regenerere alle eksisterende vektorer for at sikre ensartet søgekvalitet:

```bash
# Forhåndsvis antallet, der skal migreres
uv run python tools/migrate_embeddings.py --dry-run

# Fuld migrering (understøtter genoptagelse fra breakpoint)
uv run python tools/migrate_embeddings.py

# Migrér kun en bestemt gruppe
uv run python tools/migrate_embeddings.py --group-id myproject

# Fortsæt fra breakpoint (genkør efter afbrydelse)
uv run python tools/migrate_embeddings.py --resume
```

> **Kompatibilitet**: `bge-m3` har oprindeligt 1024 dimensioner, og systemet trunkerer automatisk til 768 dimensioner for at være kompatibelt med det eksisterende Neo4j-vektorindeks. Data før og efter migreringen kan eksistere side om side, men det anbefales at udføre en fuld migrering for at opnå den bedste søgekvalitet.

## Dokumentation

- [Instruktioner til brug af værktøjerne](../使用工具的指令.md) — vejledning og bedste praksis til brug af MCP-værktøjer
- [Graphiti Memory Rules](../graphiti-memory-rules.md) — beskrivelse af hukommelsesregler

## Licens

MIT License
