# Graphiti MCP Server

Kunnskapsgraf-minnetjeneste — en MCP-server som integrerer flere LLM-leverandører (Ollama / GLM / GROQ / OpenRouter / DeepSeek) med Neo4j-grafdatabasen.

Utviklet som en utvidelse basert på [getzep/graphiti](https://github.com/getzep/graphiti), med støtte for fleksibel veksling mellom lokal Ollama og sky-LLM, og mulighet til å angi Embedding-leverandør uavhengig (frikoblet fra LLM).

## Funksjoner

- **Intelligent minnehåndtering** — bruker en kunnskapsgraf for å lagre og hente komplekse minnerelasjoner
- **Semantisk søk** — hybridsøk basert på vektorinnebygginger (vektor + nøkkelord + grafgjennomgang)
- **16 søkestrategier** — avansert søk støtter flere reordningsmetoder som RRF, MMR, Cross-Encoder med mer
- **Flere LLM-leverandører** — støtter Ollama (lokal), GLM (Zhipu AI, gratis), GROQ (høyhastighetsinferens), OpenRouter (aggregerer modeller fra ulike leverandører), DeepSeek (Deep Seek), med veksling via miljøvariabler med ett tastetrykk
- **Embedding frikoblet fra LLM** — kan angi innebyggingsmotor uavhengig med `EMBEDDING_PROVIDER`, sky-LLM faller automatisk tilbake til lokal `bge-m3`
- **Tomodellsfordeling** — i Ollama-modus bruker komplekse oppgaver hovedmodellen, mens enkle oppgaver automatisk veksler til en liten modell for bedre ytelse
- **Intelligent innholdsoppdeling** — lange tekster behandles automatisk i segmenter, noe som reduserer LLM-belastningen (konfigurerbar terskel)
- **Bakgrunnsbehandling av minne** — minneinnlegging kan kjøres i bakgrunnen, MCP-kallet returnerer umiddelbart
- **Minne-deduplisering** — oppdager automatisk svært likt eksisterende minne for å unngå dobbeltlagring
- **Konfliktdeteksjon** — oppdager motstridende fakta mellom to entiteter og identifiserer utdatert og gyldig informasjon
- **Fellesskapsdeteksjon** — grupperer automatisk relaterte entiteter basert på Label Propagation-algoritmen
- **Viktighetssporing** — registrerer automatisk hvor ofte entiteter aksesseres, og sorterer søkeresultater etter viktighet
- **Intelligent glemming** — identifiserer og rydder opp i utdatert minne med lav tilgangsfrekvens for å holde grafen kompakt
- **Bulk-import** — sender inn flere minner samtidig, egnet for migrering av store datamengder
- **Strukturerte tripler** — legg til «subjekt-relasjon-objekt» direkte, hopp over LLM-ekstraksjon og fullfør på sekunder
- **Web-administrasjonsgrensesnitt** — innebygd dashbord, bla gjennom, søk, visualisering av kunnskapsgraf, AI-spørsmål og svar, fellesskapsvisning
- **Flerspråklighet (i18n)** — svarmeldinger støtter 30+ locale (inkludert zh-TW / en / zh-CN / ja / pt-BR / ko / es / de / fr osv.); MCP-verktøy følger `SERVER_LANG`, REST API forhandler automatisk etter HTTP `Accept-Language`
- **Mørkt/lyst tema** — Web-grensesnittet støtter temaveksling
- **Sikker modus** — valgfri rask minneinnlegging som hopper over entitetsekstraksjon
- **Docker-støtte** — innebygd Dockerfile, støtter containerisert distribusjon
- **Samtidighetssikker** — asyncio.Lock beskytter initialisering og forhindrer kappløpstilstander
- **Lagdelt helsesjekk** — `/health` (liveness) + `/health/ready` (readiness)

## Systemkrav

| Element | Krav |
|------|------|
| Python | 3.10+ (3.11+ anbefales) |
| Neo4j | 4.0+ (`bolt://localhost:7687`) |
| LLM-leverandør | Ollama / GLM / GROQ / OpenRouter / DeepSeek (velg én av fem) |
| Node.js | 18+ (kun for PM2-bakgrunnskjøring, valgfritt) |
| Diskplass | ~3GB (Ollama-modeller + Neo4j-data) |

### Valg av LLM-leverandør

Veksle via miljøvariabelen `LLM_PROVIDER` (`ollama` / `glm` / `groq` / `openrouter` / `deepseek`):

| Leverandør | Egenskaper | LLM-modell | Embedding | Egnet scenario |
|--------|------|----------|-----------|----------|
| **Ollama** (standard) | Helt lokal, data forlater ikke maskinen | `qwen2.5:3b` | `bge-m3` (utmerket for kinesisk + RAG) | Har GPU, verdsetter personvern |
| **GLM** | Gratis sky, stabil og uten hastighetsgrense | `glm-4-flash` (gratis) | `embedding-3` | Ingen GPU, søkeintensive scenarier |
| **GROQ** | Svært rask inferens | `llama-3.3-70b-versatile` | Faller tilbake til Ollama `bge-m3` | Sporadisk innlegging, høy kvalitet |
| **OpenRouter** | Aggregerer modeller fra ulike leverandører, med gratis kvote | `stepfun/step-3.5-flash:free` osv. | Faller tilbake til Ollama `bge-m3` | Ønsker å bruke en spesifikk skymodell |
| **DeepSeek** | Deep Seek-sky, god pris/ytelse | `deepseek-v4-flash` / `deepseek-v4-pro` | Faller tilbake til Ollama `bge-m3` | Kinesisk forståelse, rimelig sky |

> **Embedding frikoblet fra LLM**: Innebyggingsmotoren angis uavhengig via `EMBEDDING_PROVIDER` (`ollama` / `glm`), og følger `LLM_PROVIDER` når den ikke er satt. I praksis er det bare `glm` som bruker GLM `embedding-3`, mens alle andre (inkludert sky-LLM-er som GROQ / OpenRouter / DeepSeek som ikke tilbyr Embedding) automatisk bruker Ollama `bge-m3`. **Derfor trengs fortsatt lokal Ollama for å levere innebyggingstjenesten ved bruk av en hvilken som helst sky-LLM (med mindre embedding også er satt til glm).**

#### Ollama-modus (lokal)

```bash
# LLM-hovedmodell (qwen2.5:3b anbefales, beste balanse mellom hastighet og stabilitet)
ollama pull qwen2.5:3b

# Innebyggingsmodell (påkrevd, brukes til vektorsøk)
ollama pull bge-m3
```

> **Merknader om modellvalg**:
> - `qwen2.5:3b` — anbefalt, ~2s/kall, ~100 t/s, 100 % stabil strukturert utdata i graphiti-core
> - `qwen2.5:7b` — bedre resultat, men 5-10 ganger tregere, egnet for scenarier der kvalitet prioriteres
> - `qwen2.5:1.5b` — raskest, men **ustabil** (kun 33 % suksessrate for strukturert JSON), anbefales ikke

#### GLM-modus (Zhipu AI-sky)

```bash
# .env-innstillinger
LLM_PROVIDER=glm
GLM_API_KEY=your_api_key          # hentes fra https://open.bigmodel.cn
GLM_MODEL=glm-4-flash             # gratis modell
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768      # må samsvare med dimensjonen til Neo4j-vektorindeksen
```

> **GLM-ytelsesreferanse**: skriving ~22s (kort tekst), søk ~0,34s, null Rate Limit-feil, 2-5 ganger tregere enn lokal Ollama, men helt gratis.

#### GROQ-modus (høyhastighetsinferens)

```bash
# .env-innstillinger
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key         # hentes fra https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile
```

> **Merk**: GROQ tilbyr ikke Embedding-tjeneste, og må kombineres med Ollama-innebyggingsmotoren (automatisk tilbakefall) eller sette `EMBEDDING_PROVIDER` til glm. GROQ har strenge Rate Limit-grenser, og hyppig bruk vil utløse mange gjenforsøk.

#### OpenRouter-modus (aggregerer modeller fra ulike leverandører)

```bash
# .env-innstillinger
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_api_key       # hentes fra https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free   # kan endres til en hvilken som helst OpenRouter-modell
```

> **Merk**: OpenRouter tilbyr ikke Embedding, og faller automatisk tilbake til Ollama `bge-m3`. Modelliste finnes på https://openrouter.ai/models (inkludert flere `:free`-gratismodeller).

#### DeepSeek-modus (Deep Seek)

```bash
# .env-innstillinger
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key         # hentes fra https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash      # anbefalt; eller deepseek-v4-pro (bedre resultat)
```

> **Merk**: DeepSeek tilbyr ikke Embedding, og faller automatisk tilbake til Ollama `bge-m3`. `deepseek-chat` / `deepseek-reasoner` vil bli tatt ut av drift 2026-07-24, og det anbefales å bytte til `deepseek-v4-flash` / `deepseek-v4-pro`. DeepSeek krever strengt at prompten i `json_object`-modus inneholder strengen "json", klienten har innebygd sikkerhetsbeskyttelse, og ingen ekstra konfigurasjon er nødvendig.

## Hurtigstart

### 1. Forberedelser

Bekreft at Neo4j kjører lokalt, og forbered den tilsvarende tjenesten basert på valgt LLM-leverandør:

```bash
# Bekreft at Neo4j kjører (påkrevd)
neo4j status
# Eller bruk Docker: docker run -d -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/your_password neo4j:latest

# Ollama-modus: bekreft at Ollama kjører
ollama list
# Hvis ikke startet: ollama serve

# GLM / GROQ-modus: trenger bare en gyldig API Key, ingen lokal tjeneste nødvendig
```

### 2. Installer avhengigheter

```bash
git clone <repo-url>
cd graphiti
uv sync
```

> **Merk**: Dette prosjektet bruker [uv](https://github.com/astral-sh/uv) til å håndtere avhengigheter. Hvis det ikke er installert: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 3. Konfigurer miljøet

```bash
cp .env.example .env
```

Rediger `.env`, og du må **minst** endre følgende elementer:

```bash
NEO4J_PASSWORD=your_actual_password  # påkrevd: Neo4j-passord
LLM_PROVIDER=ollama                  # ollama / glm / groq / openrouter / deepseek
OLLAMA_MODEL=qwen2.5:3b              # Ollama-modus: lokal LLM-modell
# GLM_API_KEY=your_key               # GLM-modus: Zhipu AI API Key
# GROQ_API_KEY=your_key              # GROQ-modus: GROQ API Key
# OPENROUTER_API_KEY=your_key        # OpenRouter-modus: API Key
# DEEPSEEK_API_KEY=your_key          # DeepSeek-modus: API Key
```

### 4. Start tjenesten

```bash
# HTTP-modus (anbefalt, inkluderer Web-administrasjonsgrensesnitt)
uv run python graphiti_mcp_server.py --transport http --port 8000

# Eller bruk PM2-bakgrunnskjøring (anbefalt for langvarig kjøring)
pm2 start ecosystem.config.cjs
```

### 5. Verifiser tjenesten

Etter oppstart kan du besøke følgende endepunkter:

| Endepunkt | Beskrivelse |
|------|------|
| http://localhost:8000/ | Web-administrasjonsgrensesnitt |
| http://localhost:8000/mcp | MCP-endepunkt (for tilkobling av MCP-klienter) |
| http://localhost:8000/health | Helsesjekk (liveness) |
| http://localhost:8000/health/ready | Dyp sjekk (inkludert Neo4j-tilkobling) |
| http://localhost:8000/api/stats | REST API-statistikk |

## Prosjektstruktur

```
graphiti/
├── graphiti_mcp_server.py        # Hovedinngang — MCP-verktøydefinisjoner (19 verktøy)
├── src/
│   ├── config.py                 # Konfigurasjonshåndtering (GraphitiConfig, støtter JSON/.env-lagdeling)
│   ├── web_api.py                # Web-administrasjonsgrensesnitt REST API (20+ endepunkter)
│   ├── ollama_graphiti_client.py  # Ollama LLM-klient (tomodellsfordeling)
│   ├── glm_client.py             # GLM (Zhipu AI) LLM-klient (OpenAI-kompatibel API)
│   ├── openrouter_client.py      # OpenRouter LLM-klient (aggregerer modeller fra ulike leverandører)
│   ├── deepseek_client.py        # DeepSeek LLM-klient (json_object + reserve-json-beskyttelse)
│   ├── ollama_embedder.py        # Ollama innebyggingsmodell-adapter
│   ├── content_preprocessor.py   # Intelligent innholdsoppdeling (automatisk segmentering av lang tekst)
│   ├── deduplication.py          # Minne-deduplisering (sammenligning av kosinuslikhet)
│   ├── importance.py             # Viktighetssporing og intelligent glemming
│   ├── safe_memory_add.py        # Sikker minneinnlegging (hopper over entitetsekstraksjon)
│   ├── timezone_utils.py         # Tidssonekonvertering (UTC→visning i lokal tidssone)
│   ├── i18n.py                   # Backend-flerspråklighet (REST følger Accept-Language, MCP følger SERVER_LANG)
│   ├── exceptions.py             # Strukturert unntakshåndtering (12 unntaksklasser)
│   └── logging_setup.py          # Loggsystem (tidsrotasjon + ytelsesovervåking)
├── web/                          # Web-administrasjonsgrensesnitt frontend (SPA, ingen build)
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js                # REST API-innpakning
│       ├── components.js         # UI-komponentrendering (inkludert fellesskapsside)
│       └── app.js                # SPA-ruting, tilstandshåndtering
├── tests/                        # Testpakke (183 tester)
│   ├── test_content_preprocessor.py  # Oppdelingslogikktester (17 stk.)
│   ├── test_new_features.py      # Tester for nye funksjoner (32 stk.)
│   ├── test_i18n.py             # Flerspråklighetstester (37 stk.)
│   ├── test_unit.py              # Enhetstester
│   ├── test_web_api.py           # Web API-tester
│   ├── test_web_ui_features.py   # Web UI-funksjonstester
│   ├── test_integration_manual.py # Manuelle integrasjonstester
│   └── bench_deepseek_flash_vs_pro.py # DeepSeek flash/pro ytelsesbenchmark-skript
├── tools/                        # Utviklings- og diagnoseverktøy
│   ├── status_report.py          # Samlet statusrapport
│   ├── validate_config.py        # Konfigurasjonsvalidering
│   ├── performance_diagnose.py   # Ytelsesdiagnose
│   ├── inspect_schema.py         # Neo4j-strukturkontroll
│   └── batch_reprocess.py        # Batch-reprosessering
├── docs/                         # Dokumentasjon
├── logs/                         # Logger (tidsrotasjon, beholdes i 30 dager som standard)
├── Dockerfile                    # Docker-containerisert distribusjon
└── ecosystem.config.cjs          # PM2-konfigurasjon
```

## Oppsett av MCP-klient

### HTTP-modus (anbefalt)

Egnet for MCP-klienter som støtter HTTP, slik som Claude Code, Cline osv.:

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

Egnet for klienter som trenger å starte prosessen direkte, slik som Claude Desktop:

**Plassering av konfigurasjonsfilen:**
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

> **Merk**: SSE-modus (`--transport sse`) anbefales ikke lenger. MCP 1.x har kompatibilitetsproblemer med session-initialisering, bruk HTTP-modus i stedet.

## MCP-verktøy (19 stk.)

### Minnehåndtering (7 stk.)

| Verktøy | Beskrivelse |
|------|------|
| `add_memory_simple` | Legg til minne i kunnskapsgrafen (støtter bakgrunnsbehandling, intelligent oppdeling, dedupliseringssjekk) |
| `add_episode_bulk` | Legg til flere minner i bulk (bakgrunnsbehandling som standard) |
| `add_triplet` | Strukturert tripel-innlegging (hopper over LLM, fullføres på sekunder) |
| `search_memory_nodes` | Søk i minnenoder (støtter 16 søkestrategier, tidsfiltrering) |
| `search_memory_facts` | Søk i minnefakta (støtter filtrering på relasjonstype, tidsintervall, gyldighet) |
| `advanced_search` | Avansert søk (16 strategier, returnerer noder + kanter + fellesskap + episoder) |
| `get_episodes` | Hent de nyeste minneepisodene |

### Kunnskapsanalyse (3 stk.)

| Verktøy | Beskrivelse |
|------|------|
| `check_conflicts` | Oppdag faktakonflikter mellom to entiteter (gyldig vs. utdatert) |
| `get_node_edges` | Utforsk en nodes inngående og utgående kantrelasjoner |
| `build_communities` | Utløs fellesskapsdeteksjon og gruppering (bakgrunnsbehandling som standard) |

### Minnevedlikehold (2 stk.)

| Verktøy | Beskrivelse |
|------|------|
| `get_stale_memories` | Spør etter utdatert minne med lav tilgangsfrekvens |
| `cleanup_stale_memories` | Rydd opp i utdatert minne (dry_run forhåndsvisningsmodus som standard) |

### Oppgavehåndtering

| Verktøy | Beskrivelse |
|------|------|
| `get_memory_task_status` | Spør etter fremdrift og resultat for en bakgrunnsoppgave for minnebehandling |

### Sletting og oppslag

| Verktøy | Beskrivelse |
|------|------|
| `delete_episode` | Slett en minneepisode |
| `delete_entity_edge` | Slett en entitetskant (relasjon) |
| `get_entity_edge` | Hent detaljert informasjon om en entitetskant |

### Systemadministrasjon

| Verktøy | Beskrivelse |
|------|------|
| `get_status` | Hent tjenestestatus (Neo4j, LLM, innebyggingsmotor) |
| `test_connection` | Test tilkobling til Neo4j / LLM / innebyggingsmotor |
| `clear_graph` | Tøm grafdatabasen (støtter tømming etter group_id) |

## Verktøyparametere

### add_memory_simple

| Parameter | Type | Påkrevd | Standardverdi | Beskrivelse |
|------|------|------|--------|------|
| `name` | string | Y | | Minnenavn |
| `episode_body` | string | Y | | Minneinnhold (deles automatisk ved over 800 tegn) |
| `group_id` | string | | `"default"` | Gruppe-ID (anbefales isolert per prosjekt) |
| `source` | string | | `"text"` | Kildetype: `text` / `json` / `message` |
| `source_description` | string | | `"MCP Server"` | Kildebeskrivelse |
| `use_safe_mode` | bool | | `false` | Sikker modus (hopper over entitetsekstraksjon, raskt, men minnet kan ikke søkes) |
| `background` | bool | | `false` | Bakgrunnsbehandling (returnerer task_id umiddelbart, egnet for lang tekst) |
| `force` | bool | | `false` | Hopp over dedupliseringssjekk (tving innlegging) |
| `excluded_entity_types` | list | | | Ekskluderte entitetstyper (reduserer unødvendig ekstraksjon) |

> **Ytelsestips**:
> - Kort tekst (<800 tegn): behandles direkte, fullføres vanligvis på 30-40 sekunder
> - Lang tekst (>800 tegn): deles automatisk i flere segmenter, behandles samtidig med `add_episode_bulk` (~33 % raskere enn seriell behandling)
> - Bruk `background=true` for å unngå at MCP-kallet blokkerer, og spor fremdrift via `get_memory_task_status`
> - `use_safe_mode=true` fullføres på sekunder, men minnet kan ikke finnes av søkeverktøyene
> - Når deduplisering er aktivert, blir svært lignende minner varslet (`force=true` kan hoppe over)

### add_episode_bulk

| Parameter | Type | Påkrevd | Standardverdi | Beskrivelse |
|------|------|------|--------|------|
| `episodes` | list | Y | | Minneliste, hvert element inneholder `name` og `content` |
| `group_id` | string | | `"default"` | Gruppe-ID |
| `source` | string | | `"text"` | Kildetype |
| `background` | bool | | `true` | Bakgrunnsbehandling (bulk er vanligvis tidkrevende) |

### add_triplet

| Parameter | Type | Påkrevd | Standardverdi | Beskrivelse |
|------|------|------|--------|------|
| `source_name` | string | Y | | Navn på kildeentitet (f.eks. "Alice") |
| `target_name` | string | Y | | Navn på målentitet (f.eks. "Google") |
| `relation_name` | string | Y | | Relasjonsnavn (f.eks. "works_at") |
| `fact` | string | Y | | Faktabeskrivelse (f.eks. "Alice works at Google") |
| `group_id` | string | | `"default"` | Gruppe-ID |
| `source_labels` | list | | | Etiketter for kildeentitet |
| `target_labels` | list | | | Etiketter for målentitet |

### search_memory_nodes

| Parameter | Type | Påkrevd | Standardverdi | Beskrivelse |
|------|------|------|--------|------|
| `query` | string | Y | | Søkenøkkelord (naturlig språk) |
| `max_nodes` | int | | `10` | Maksimalt antall returnerte |
| `group_ids` | list | | | Gruppefiltrering (felles søk på tvers av flere grupper) |
| `entity_types` | list | | | Filtrering på entitetstype |
| `search_recipe` | string | | | Søkestrategi (se avansert søk) |
| `created_after` | string | | | Nedre grense for opprettelsestid (ISO datetime) |
| `created_before` | string | | | Øvre grense for opprettelsestid (ISO datetime) |

### search_memory_facts

| Parameter | Type | Påkrevd | Standardverdi | Beskrivelse |
|------|------|------|--------|------|
| `query` | string | Y | | Søkenøkkelord |
| `max_facts` | int | | `10` | Maksimalt antall returnerte |
| `group_ids` | list | | | Gruppefiltrering |
| `center_node_uuid` | string | | | UUID for sentrumsnode (utforsk relasjoner til en spesifikk node) |
| `edge_types` | list | | | Filtrering på relasjonstype (f.eks. `["works_at"]`) |
| `created_after` | string | | | Nedre grense for opprettelsestid (ISO datetime) |
| `created_before` | string | | | Øvre grense for opprettelsestid (ISO datetime) |
| `only_valid` | bool | | `false` | Returner kun ikke-utdaterte fakta |

### advanced_search

| Parameter | Type | Påkrevd | Standardverdi | Beskrivelse |
|------|------|------|--------|------|
| `query` | string | Y | | Søkenøkkelord |
| `search_recipe` | string | | `"combined_rrf"` | Søkestrategi (16 valgmuligheter) |
| `max_results` | int | | `10` | Maksimalt antall returnerte |
| `group_ids` | list | | | Gruppefiltrering |
| `center_node_uuid` | string | | | UUID for sentrumsnode |

**Tilgjengelige søkestrategier (search_recipe):**

| Kategori | Strategi | Beskrivelse |
|------|------|------|
| Kombinert | `combined_rrf` | Kombinert RRF-fusjon (standard, anbefalt) |
| Kombinert | `combined_mmr` | Kombinert MMR-mangfoldsreordning |
| Kombinert | `combined_cross_encoder` | Kombinert Cross-Encoder-finsortering |
| Kant | `edge_rrf` / `edge_mmr` / `edge_cross_encoder` | Kantsøk (3 sorteringer) |
| Kant | `edge_node_distance` / `edge_episode_mentions` | Kantsøk (grafavstand/antall referanser) |
| Node | `node_rrf` / `node_mmr` / `node_cross_encoder` | Nodesøk (3 sorteringer) |
| Node | `node_node_distance` / `node_episode_mentions` | Nodesøk (grafavstand/antall referanser) |
| Fellesskap | `community_rrf` / `community_mmr` / `community_cross_encoder` | Fellesskapssøk |

### check_conflicts

| Parameter | Type | Påkrevd | Standardverdi | Beskrivelse |
|------|------|------|--------|------|
| `source_name` | string | Y | | Navn på kildeentitet |
| `target_name` | string | Y | | Navn på målentitet |
| `group_id` | string | | `"default"` | Gruppe-ID |

### get_node_edges

| Parameter | Type | Påkrevd | Standardverdi | Beskrivelse |
|------|------|------|--------|------|
| `node_uuid` | string | Y | | Node-UUID |
| `include_inbound` | bool | | `true` | Inkluder inngående kanter |
| `include_outbound` | bool | | `true` | Inkluder utgående kanter |
| `max_edges` | int | | `50` | Maksimalt antall returnerte |

### build_communities

| Parameter | Type | Påkrevd | Standardverdi | Beskrivelse |
|------|------|------|--------|------|
| `group_ids` | list | | | Angitte grupper (alle hvis tom) |
| `background` | bool | | `true` | Bakgrunnsbehandling |

### get_stale_memories

| Parameter | Type | Påkrevd | Standardverdi | Beskrivelse |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Antall dager uten tilgang før det regnes som utdatert |
| `min_access_count` | int | | `2` | Inkluderes kun hvis tilgangsantallet er lavere enn denne verdien |
| `group_id` | string | | | Gruppefiltrering |
| `limit` | int | | `50` | Maksimalt antall returnerte |

### cleanup_stale_memories

| Parameter | Type | Påkrevd | Standardverdi | Beskrivelse |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Terskel for antall dager til utdatering |
| `min_access_count` | int | | `2` | Terskel for minste tilgangsantall |
| `group_id` | string | | | Gruppefiltrering |
| `dry_run` | bool | | `true` | Forhåndsvisningsmodus (sletter ikke faktisk) |
| `limit` | int | | `50` | Maksimalt antall som behandles |

### get_memory_task_status

| Parameter | Type | Påkrevd | Beskrivelse |
|------|------|------|------|
| `task_id` | string | Y | ID for bakgrunnsoppgave (returnert av `add_memory_simple(background=true)`) |

## Web-administrasjonsgrensesnitt

I HTTP-modus kan du bruke det ved å besøke `http://localhost:8000/`.

**Funksjoner:**
- Dashbord — statistikk over antall noder, fakta og minneepisoder
- Entitetsnoder — bla gjennom, filtrer, vektorsøk
- Faktarelasjoner — bla gjennom, filtrer, vektorsøk
- Minneepisoder — bla gjennom, fulltekstsøk, slett
- Fellesskapsvisning — liste over fellesskapsnoder, sammendrag, utløs fellesskapsbygging
- Tripel-skjema — legg til strukturert kunnskap «subjekt-relasjon-objekt» direkte
- Gruppehåndtering — filtrer etter gruppe, batch-sletting
- Visualisering av kunnskapsgraf — grafisk fremstilling av noderelasjoner
- AI-spørsmål og svar — intelligente spørsmål og svar basert på kunnskapsgrafen
- Kvalitetsanalyse — analyse av minnekvalitet og dekning
- Temaveksling — mørkt/lyst tema

**REST API:**

| Endepunkt | Metode | Beskrivelse |
|------|------|------|
| `/api/stats` | GET | Dashbordstatistikk |
| `/api/groups` | GET | Hent alle group_id |
| `/api/nodes` | GET | Bla gjennom entitetsnoder (paginering) |
| `/api/facts` | GET | Bla gjennom fakta (paginering) |
| `/api/episodes` | GET | Bla gjennom minneepisoder (paginering) |
| `/api/search/nodes` | GET | Vektorsøk i noder |
| `/api/search/facts` | GET | Vektorsøk i fakta |
| `/api/search/advanced` | GET | Avansert søk (16 strategier) |
| `/api/communities` | GET | Bla gjennom fellesskapsnoder (paginering) |
| `/api/communities/build` | POST | Utløs fellesskapsbygging |
| `/api/memory/add-bulk` | POST | Legg til minner i bulk |
| `/api/memory/add-triplet` | POST | Legg til tripel |
| `/api/memory/tasks` | GET | List opp bakgrunnsoppgaver (støtter statusfiltrering) |
| `/api/memory/tasks/{id}` | GET | Spør etter status for én enkelt oppgave |
| `/api/analytics/stale` | GET | Spør etter utdatert minne |
| `/api/analytics/cleanup` | POST | Rydd opp i utdatert minne |
| `/api/nodes/{uuid}` | DELETE | Slett node |
| `/api/episodes/{uuid}` | DELETE | Slett minneepisode |
| `/api/facts/{uuid}` | DELETE | Slett faktum |
| `/api/groups/{group_id}` | DELETE | Slett hele gruppen |

## Konfigurasjon

### Miljøvariabler (.env)

Konfigurasjonen bruker en lagdelingsmekanisme: JSON-konfigurasjonsfilen er grunnlaget, og miljøvariabler overstyrer enkeltverdier.

```bash
# === Påkrevd ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password        # må endres

# === Valg av LLM-leverandør ===
LLM_PROVIDER=ollama                 # ollama / glm / groq / openrouter / deepseek

# === Embedding-leverandør (valgfritt, følger LLM_PROVIDER som standard) ===
# Kun glm bruker GLM Embedding, alle andre bruker Ollama bge-m3
# EMBEDDING_PROVIDER=ollama         # ollama / glm

# === Ollama-konfigurasjon (brukes når LLM_PROVIDER=ollama) ===
OLLAMA_MODEL=qwen2.5:3b             # hovedmodell (qwen2.5:3b anbefales)
OLLAMA_SMALL_MODEL=qwen2.5:3b       # liten modell (for enkle oppgaver, kan velge en annen modell)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.1

# === GLM-konfigurasjon (brukes når LLM_PROVIDER=glm) ===
GLM_API_KEY=your_api_key            # hentes fra https://open.bigmodel.cn
GLM_MODEL=glm-4-flash               # gratis modell
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768

# === GROQ-konfigurasjon (brukes når LLM_PROVIDER=groq) ===
GROQ_API_KEY=your_api_key           # hentes fra https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile

# === OpenRouter-konfigurasjon (brukes når LLM_PROVIDER=openrouter) ===
OPENROUTER_API_KEY=your_api_key     # hentes fra https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free

# === DeepSeek-konfigurasjon (brukes når LLM_PROVIDER=deepseek) ===
DEEPSEEK_API_KEY=your_api_key       # hentes fra https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash    # eller deepseek-v4-pro

# === Ollama innebyggingsmodell (brukes alltid ved ikke-glm-innebygging) ===
OLLAMA_EMBEDDING_MODEL=bge-m3
OLLAMA_EMBEDDING_DIMENSIONS=768

# === Visning og språk (valgfritt) ===
GRAPHITI_DISPLAY_TIMEZONE=Asia/Taipei # visningstidssone for tidsstempler returnert av API (IANA-navn; lagring forblir UTC)
SERVER_LANG=zh-TW                     # svarspråk for MCP-verktøy (komplett locale se src/i18n.py); REST API følger Accept-Language

# === Minneytelse (valgfritt) ===
GRAPHITI_CHUNK_THRESHOLD=800         # tegnterskel som utløser intelligent oppdeling
GRAPHITI_MAX_CHUNK_SIZE=600          # maksimalt antall tegn per segment
GRAPHITI_MAX_COROUTINES=10            # maksimalt antall samtidige koroutiner
GRAPHITI_DEFAULT_BACKGROUND=false    # om bakgrunnsbehandling skal være standard

# === Viktighetssporing og intelligent glemming (valgfritt) ===
ENABLE_IMPORTANCE_TRACKING=true      # aktiver tilgangssporing
IMPORTANCE_WEIGHT=0.1                # viktighetsvekt
STALE_DAYS_THRESHOLD=30              # terskel for antall dager til utdatering
STALE_MIN_ACCESS_COUNT=2             # minste tilgangsantall

# === Logging ===
LOG_FILE=logs/graphiti_mcp_server.log
LOG_LEVEL=INFO
```

> **Komplett liste over miljøvariabler** finnes i `.env.example`

### JSON-konfigurasjonsfil

Egnet for konfigurasjon som trenger versjonskontroll (miljøvariabler kan fortsatt overstyre):

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

## PM2-bakgrunnskjøring

```bash
npm install -g pm2

pm2 start ecosystem.config.cjs      # start
pm2 status                           # status
pm2 logs graphiti-mcp-http           # sanntidslogger
pm2 restart graphiti-mcp-http --update-env  # omstart (last inn .env på nytt)

pm2 save && pm2 startup              # konfigurer automatisk oppstart ved boot
```

> **Tips**: Etter å ha endret `.env` må du starte på nytt med flagget `--update-env`, ellers oppdateres ikke miljøvariablene.

## Docker-distribusjon

```bash
docker build -t graphiti-mcp .

# Merk: Docker-containeren må kunne koble til Neo4j og Ollama
# Å bruke host network er enklest
docker run -p 8000:8000 --env-file .env --network host graphiti-mcp

# Eller angi eksterne tjenesteadresser eksplisitt
docker run -p 8000:8000 \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --env-file .env graphiti-mcp
```

## Testing

```bash
# Kjør alle tester (183 stk., ca. 1 sekund)
uv run python -m pytest tests/

# Detaljert utdata
uv run python -m pytest tests/ -v

# Kjør kun en spesifikk test
uv run python -m pytest tests/test_content_preprocessor.py -v
uv run python -m pytest tests/test_new_features.py -v
uv run python -m pytest tests/test_unit.py -v
```

> **Merk**: De 3 async-testene i `test_integration_manual.py` krever installasjon av `pytest-asyncio`, og vises som Failed når den mangler, men dette påvirker ikke de andre testene. `bench_deepseek_flash_vs_pro.py` er et ytelsesbenchmark-skript, ikke en enhetstest.

## Feilsøking

### Neo4j-tilkobling mislykkes

```bash
neo4j status                              # sjekk tjenestestatus
cypher-shell -u neo4j -p your_password    # bekreft at passordet er riktig
curl http://localhost:7474                 # bekreft HTTP-porten
```

Vanlige årsaker:
- Neo4j er ikke startet
- Feil passord (`NEO4J_PASSWORD` i `.env`)
- Porten er opptatt eller blokkert av brannmur

### LLM-tilkobling mislykkes

**Ollama-modus:**
```bash
ollama serve                # start Ollama-tjenesten
ollama list                 # sjekk installerte modeller
ollama pull qwen2.5:3b      # installer manglende modell
```

Vanlige årsaker: Ollama er ikke startet, modellen er ikke installert, utilstrekkelig GPU-minne

**GLM-modus:**
- Bekreft at `GLM_API_KEY` er riktig
- Bekreft at `GLM_EMBEDDING_DIMENSIONS=768` (må samsvare med Neo4j-vektorindeksen)
- GLM API-endepunkt: `https://open.bigmodel.cn/api/paas/v4/`

**GROQ-modus:**
- Bekreft at `GROQ_API_KEY` er riktig
- Vurder å bytte til GLM-modus ved hyppige Rate Limit
- GROQ tilbyr ikke Embedding, sørg for at Ollama-innebyggingsmotoren er tilgjengelig

**OpenRouter-modus:**
- Bekreft at `OPENROUTER_API_KEY` er riktig og at `OPENROUTER_MODEL` er en gyldig modell-ID (se https://openrouter.ai/models)
- Tilbyr ikke Embedding, sørg for at Ollama-innebyggingsmotoren er tilgjengelig

**DeepSeek-modus:**
- Bekreft at `DEEPSEEK_API_KEY` er riktig
- Hvis `Prompt must contain the word 'json'` oppstår: dette er et hardt krav i DeepSeeks `json_object`-modus, klienten har innebygd sikkerhetsbeskyttelse; hvis det fortsatt oppstår, bekreft at du bruker den nyeste versjonen av `src/deepseek_client.py` og start tjenesten på nytt
- Tilbyr ikke Embedding, sørg for at Ollama-innebyggingsmotoren er tilgjengelig

### MCP-tilkoblingsfeil

Hvis `Invalid request parameters` eller `Received request before initialization was complete` oppstår:

1. Bekreft at du bruker HTTP-transportmodus (**ikke bruk SSE**)
2. Bekreft at klienten er konfigurert med `"type": "http"`, `"url": "http://localhost:8000/mcp"`
3. Start tjenesten på nytt: `pm2 restart graphiti-mcp-http --update-env`
4. Kjør `/mcp` i Claude Code for å koble til på nytt

### Treg minneinnlegging

- **Ollama**: sjekk modellstørrelsen (`qwen2.5:3b` er 5-10 ganger raskere enn `7b`), bekreft at GPU brukes (`ollama ps`)
- **GLM**: hvert add_episode krever 10-20+ LLM-nettverksrundturer, ~22s for kort tekst er normalt
- **GROQ**: Rate Limit fører til mange gjenforsøk, anbefaler å bytte til GLM eller Ollama ved hyppig bruk
- Bruk `background=true` for å unngå blokkering
- Senk `GRAPHITI_CHUNK_THRESHOLD` for å la lang tekst deles tidligere

### PM2-problemer

```bash
pm2 status                                        # sjekk status
pm2 logs graphiti-mcp-http --err --lines 50        # feillogger
lsof -i :8000                                     # sjekk portbruk
pm2 delete graphiti-mcp-http && pm2 start ecosystem.config.cjs  # full omstart
```

## Utviklings- og diagnoseverktøy

```bash
uv run python tools/status_report.py           # samlet statusrapport (Neo4j + Ollama + konfigurasjon)
uv run python tools/validate_config.py         # valider .env og konfigurasjonens fullstendighet
uv run python tools/performance_diagnose.py    # LLM-ytelsesdiagnose
uv run python tools/inspect_schema.py          # kontroll av Neo4j-indekser og -begrensninger
uv run python tools/migrate_embeddings.py      # Embedding-modellmigrering (regenerer vektorer etter modellbytte)
```

### Embedding-modellmigrering

Etter bytte av embedding-modell (f.eks. `nomic-embed-text` → `bge-m3`), kan du bruke migreringsverktøyet til å regenerere alle eksisterende vektorer for å sikre konsistent søkekvalitet:

```bash
# Forhåndsvis antallet som må migreres
uv run python tools/migrate_embeddings.py --dry-run

# Full migrering (støtter gjenopptak fra bruddpunkt)
uv run python tools/migrate_embeddings.py

# Migrer kun en angitt gruppe
uv run python tools/migrate_embeddings.py --group-id myproject

# Fortsett fra bruddpunkt (kjør på nytt etter avbrudd)
uv run python tools/migrate_embeddings.py --resume
```

> **Kompatibilitet**: `bge-m3` har 1024 dimensjoner opprinnelig, systemet trunkerer automatisk til 768 dimensjoner for å være kompatibel med den eksisterende Neo4j-vektorindeksen. Data fra før og etter migrering kan eksistere side om side, men det anbefales å utføre en full migrering for å oppnå best søkekvalitet.

## Dokumentasjon

- [Instruksjoner for bruk av verktøy](../使用工具的指令.md) — bruksveiledning og beste praksis for MCP-verktøy
- [Graphiti Memory Rules](../graphiti-memory-rules.md) — forklaring av minneregler

## Lisens

MIT License
