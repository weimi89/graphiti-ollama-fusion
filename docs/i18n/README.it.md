# Graphiti MCP Server

Servizio di memoria a grafo della conoscenza — un server MCP che integra molteplici fornitori LLM (Ollama / GLM / GROQ / OpenRouter / DeepSeek) con il database a grafo Neo4j.

Sviluppato come estensione di [getzep/graphiti](https://github.com/getzep/graphiti), supporta il passaggio flessibile tra Ollama locale e LLM cloud, e consente di specificare in modo indipendente il fornitore di Embedding (disaccoppiato dall'LLM).

## Funzionalità principali

- **Gestione intelligente della memoria** — utilizza un grafo della conoscenza per memorizzare e recuperare relazioni di memoria complesse
- **Ricerca semantica** — ricerca ibrida basata su embedding vettoriali (vettoriale + parole chiave + attraversamento del grafo)
- **16 strategie di ricerca** — la ricerca avanzata supporta molteplici metodi di riordino come RRF, MMR, Cross-Encoder
- **Molteplici fornitori LLM** — supporta Ollama (locale), GLM (Zhipu AI gratuito), GROQ (inferenza ad alta velocità), OpenRouter (aggregatore di vari modelli), DeepSeek (Shenzhen Qiusuo), con commutazione tramite variabile d'ambiente con un solo comando
- **Embedding disaccoppiato dall'LLM** — è possibile specificare in modo indipendente l'embedder con `EMBEDDING_PROVIDER`, gli LLM cloud ricadono automaticamente sul `bge-m3` locale
- **Distribuzione su doppio modello** — in modalità Ollama, i task complessi usano il modello principale, mentre i task semplici passano automaticamente al modello piccolo per migliorare le prestazioni
- **Segmentazione intelligente del contenuto** — i testi lunghi vengono elaborati automaticamente per segmenti, riducendo il carico dell'LLM (soglia configurabile)
- **Elaborazione della memoria in background** — l'aggiunta di memoria può essere eseguita in background, e la chiamata MCP restituisce immediatamente
- **Deduplicazione della memoria** — rileva automaticamente le memorie esistenti altamente simili, evitando archiviazioni duplicate
- **Rilevamento dei conflitti** — rileva fatti contraddittori tra due entità, identificando le informazioni già invalidate e quelle valide
- **Rilevamento delle comunità** — raggruppa automaticamente le entità correlate sulla base dell'algoritmo di Label Propagation
- **Tracciamento dell'importanza** — registra automaticamente la frequenza di accesso alle entità, ordinando i risultati della ricerca per importanza
- **Oblio intelligente** — identifica e ripulisce le memorie obsolete e a basso accesso, mantenendo il grafo snello
- **Importazione in blocco** — invio di molteplici memorie in una sola volta, adatto a migrazioni di grandi quantità di dati
- **Triple strutturate** — aggiunta diretta di «soggetto-relazione-oggetto», saltando l'estrazione tramite LLM, completata in un istante
- **Interfaccia di gestione Web** — dashboard, navigazione, ricerca, visualizzazione del grafo della conoscenza, domande e risposte con AI, navigazione delle comunità integrati
- **Internazionalizzazione (i18n)** — i messaggi di risposta supportano oltre 30 locale (tra cui zh-TW / en / zh-CN / ja / pt-BR / ko / es / de / fr ecc.); gli strumenti MCP si basano su `SERVER_LANG`, mentre le REST API negoziano automaticamente in base all'header HTTP `Accept-Language`
- **Tema scuro/chiaro** — l'interfaccia Web supporta il cambio di tema
- **Modalità sicura** — aggiunta rapida di memoria con la possibilità di saltare l'estrazione delle entità
- **Supporto Docker** — Dockerfile integrato, supporta il deployment containerizzato
- **Sicurezza in concorrenza** — asyncio.Lock protegge l'inizializzazione, prevenendo le condizioni di gara
- **Controllo di salute a livelli** — `/health` (liveness) + `/health/ready` (readiness)

## Requisiti di sistema

| Voce | Requisito |
|------|------|
| Python | 3.10+ (consigliato 3.11+) |
| Neo4j | 4.0+ (`bolt://localhost:7687`) |
| Fornitore LLM | Ollama / GLM / GROQ / OpenRouter / DeepSeek (uno dei cinque) |
| Node.js | 18+ (solo per l'esecuzione in background con PM2, opzionale) |
| Spazio su disco | ~3GB (modelli Ollama + dati Neo4j) |

### Scelta del fornitore LLM

Commutazione tramite la variabile d'ambiente `LLM_PROVIDER` (`ollama` / `glm` / `groq` / `openrouter` / `deepseek`):

| Fornitore | Caratteristiche | Modello LLM | Embedding | Scenari adatti |
|--------|------|----------|-----------|----------|
| **Ollama** (predefinito) | Completamente locale, i dati non lasciano la macchina | `qwen2.5:3b` | `bge-m3` (eccellente per cinese + RAG) | Con GPU, attenti alla privacy |
| **GLM** | Cloud gratuito, stabile senza limiti | `glm-4-flash` (gratuito) | `embedding-3` | Senza GPU, scenari di ricerca intensiva |
| **GROQ** | Inferenza ad altissima velocità | `llama-3.3-70b-versatile` | Ricade su Ollama `bge-m3` | Scritture occasionali, ricerca di qualità |
| **OpenRouter** | Aggregatore di vari modelli, con quote gratuite | `stepfun/step-3.5-flash:free` ecc. | Ricade su Ollama `bge-m3` | Si vuole usare uno specifico modello cloud |
| **DeepSeek** | Cloud Shenzhen Qiusuo, ottimo rapporto qualità-prezzo | `deepseek-v4-flash` / `deepseek-v4-pro` | Ricade su Ollama `bge-m3` | Comprensione del cinese, cloud a basso costo |

> **Embedding disaccoppiato dall'LLM**: l'embedder viene specificato in modo indipendente tramite `EMBEDDING_PROVIDER` (`ollama` / `glm`); se non impostato, segue `LLM_PROVIDER`. In pratica, solo `glm` usa GLM `embedding-3`, mentre tutti gli altri (compresi GROQ / OpenRouter / DeepSeek e altri LLM cloud che non forniscono Embedding) usano automaticamente Ollama `bge-m3`. **Pertanto, quando si usa un qualsiasi LLM cloud, è comunque necessario un Ollama locale che fornisca il servizio di embedding (a meno che anche l'embedding non sia impostato su glm).**

#### Modalità Ollama (locale)

```bash
# Modello LLM principale (consigliato qwen2.5:3b, miglior equilibrio tra velocità e stabilità)
ollama pull qwen2.5:3b

# Modello di embedding (obbligatorio, usato per la ricerca vettoriale)
ollama pull bge-m3
```

> **Note sulla scelta del modello**:
> - `qwen2.5:3b` — consigliato, ~2s/call, ~100 t/s, output strutturato di graphiti-core stabile al 100%
> - `qwen2.5:7b` — risultati migliori ma 5-10 volte più lento, adatto a scenari in cui si cerca la qualità
> - `qwen2.5:1.5b` — il più veloce ma **instabile** (tasso di successo del JSON strutturato solo del 33%), uso sconsigliato

#### Modalità GLM (cloud Zhipu AI)

```bash
# Impostazioni .env
LLM_PROVIDER=glm
GLM_API_KEY=your_api_key          # Ottenibile da https://open.bigmodel.cn
GLM_MODEL=glm-4-flash             # Modello gratuito
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768      # Deve coincidere con la dimensione dell'indice vettoriale Neo4j
```

> **Riferimenti prestazionali GLM**: scrittura ~22s (testo breve), ricerca ~0,34s, zero errori di Rate Limit, 2-5 volte più lento dell'Ollama locale ma completamente gratuito.

#### Modalità GROQ (inferenza ad alta velocità)

```bash
# Impostazioni .env
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key         # Ottenibile da https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile
```

> **Nota**: GROQ non fornisce il servizio di Embedding, è necessario abbinarlo all'embedder Ollama (fallback automatico) oppure impostare `EMBEDDING_PROVIDER` su glm. GROQ ha un Rate Limit rigoroso, e un uso ad alta frequenza scatenerà numerosi tentativi di ripetizione.

#### Modalità OpenRouter (aggregatore di vari modelli)

```bash
# Impostazioni .env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_api_key       # Ottenibile da https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free   # Modificabile con qualsiasi modello OpenRouter
```

> **Nota**: OpenRouter non fornisce Embedding, ricade automaticamente su Ollama `bge-m3`. L'elenco dei modelli è disponibile su https://openrouter.ai/models (con diversi modelli gratuiti `:free`).

#### Modalità DeepSeek (Shenzhen Qiusuo)

```bash
# Impostazioni .env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key         # Ottenibile da https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash      # Consigliato; oppure deepseek-v4-pro (risultati migliori)
```

> **Nota**: DeepSeek non fornisce Embedding, ricade automaticamente su Ollama `bge-m3`. `deepseek-chat` / `deepseek-reasoner` verranno dismessi il 2026-07-24, si consiglia di passare a `deepseek-v4-flash` / `deepseek-v4-pro`. DeepSeek richiede rigorosamente che il prompt in modalità `json_object` contenga la stringa "json"; il client integra già una protezione di sicurezza, senza necessità di impostazioni aggiuntive.

## Avvio rapido

### 1. Preparazione preliminare

Verificare che Neo4j sia in esecuzione sulla macchina locale e preparare il servizio corrispondente in base al fornitore LLM scelto:

```bash
# Verificare che Neo4j sia in esecuzione (obbligatorio)
neo4j status
# Oppure usare Docker: docker run -d -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/your_password neo4j:latest

# Modalità Ollama: verificare che Ollama sia in esecuzione
ollama list
# Se non avviato: ollama serve

# Modalità GLM / GROQ: serve solo una API Key valida, nessun servizio locale necessario
```

### 2. Installazione delle dipendenze

```bash
git clone <repo-url>
cd graphiti
uv sync
```

> **Nota**: questo progetto usa [uv](https://github.com/astral-sh/uv) per gestire le dipendenze. Se non installato: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 3. Configurazione dell'ambiente

```bash
cp .env.example .env
```

Modificare `.env`, è necessario modificare **almeno** le seguenti voci:

```bash
NEO4J_PASSWORD=your_actual_password  # Obbligatorio: password di Neo4j
LLM_PROVIDER=ollama                  # ollama / glm / groq / openrouter / deepseek
OLLAMA_MODEL=qwen2.5:3b              # Modalità Ollama: modello LLM locale
# GLM_API_KEY=your_key               # Modalità GLM: API Key di Zhipu AI
# GROQ_API_KEY=your_key              # Modalità GROQ: API Key di GROQ
# OPENROUTER_API_KEY=your_key        # Modalità OpenRouter: API Key
# DEEPSEEK_API_KEY=your_key          # Modalità DeepSeek: API Key
```

### 4. Avvio del servizio

```bash
# Modalità HTTP (consigliata, include l'interfaccia di gestione Web)
uv run python graphiti_mcp_server.py --transport http --port 8000

# Oppure esecuzione in background con PM2 (consigliata per l'esecuzione a lungo termine)
pm2 start ecosystem.config.cjs
```

### 5. Verifica del servizio

Dopo l'avvio è possibile accedere ai seguenti endpoint:

| Endpoint | Descrizione |
|------|------|
| http://localhost:8000/ | Interfaccia di gestione Web |
| http://localhost:8000/mcp | Endpoint MCP (per la connessione dei client MCP) |
| http://localhost:8000/health | Controllo di salute (liveness) |
| http://localhost:8000/health/ready | Controllo approfondito (con connessione a Neo4j) |
| http://localhost:8000/api/stats | Statistiche REST API |

## Struttura del progetto

```
graphiti/
├── graphiti_mcp_server.py        # Punto di ingresso principale — definizione degli strumenti MCP (19 strumenti)
├── src/
│   ├── config.py                 # Gestione della configurazione (GraphitiConfig, supporta sovrapposizione JSON/.env)
│   ├── web_api.py                # REST API dell'interfaccia di gestione Web (20+ endpoint)
│   ├── ollama_graphiti_client.py  # Client LLM Ollama (distribuzione su doppio modello)
│   ├── glm_client.py             # Client LLM GLM (Zhipu AI) (API compatibile con OpenAI)
│   ├── openrouter_client.py      # Client LLM OpenRouter (aggregatore di vari modelli)
│   ├── deepseek_client.py        # Client LLM DeepSeek (json_object + protezione di sicurezza json)
│   ├── ollama_embedder.py        # Adattatore del modello di embedding Ollama
│   ├── content_preprocessor.py   # Segmentazione intelligente del contenuto (segmentazione automatica dei testi lunghi)
│   ├── deduplication.py          # Deduplicazione della memoria (confronto della similarità del coseno)
│   ├── importance.py             # Tracciamento dell'importanza e oblio intelligente
│   ├── safe_memory_add.py        # Aggiunta sicura della memoria (salta l'estrazione delle entità)
│   ├── timezone_utils.py         # Conversione del fuso orario (visualizzazione UTC→fuso orario locale)
│   ├── i18n.py                   # Internazionalizzazione del backend (REST in base ad Accept-Language, MCP in base a SERVER_LANG)
│   ├── exceptions.py             # Gestione strutturata delle eccezioni (12 classi di eccezioni)
│   └── logging_setup.py          # Sistema di log (rotazione temporale + monitoraggio delle prestazioni)
├── web/                          # Frontend dell'interfaccia di gestione Web (SPA, senza build)
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js                # Wrapper della REST API
│       ├── components.js         # Rendering dei componenti UI (con pagina delle comunità)
│       └── app.js                # Routing SPA, gestione dello stato
├── tests/                        # Suite di test (183 test)
│   ├── test_content_preprocessor.py  # Test della logica di segmentazione (17)
│   ├── test_new_features.py      # Test delle nuove funzionalità (32)
│   ├── test_i18n.py             # Test dell'internazionalizzazione (37)
│   ├── test_unit.py              # Test unitari
│   ├── test_web_api.py           # Test della Web API
│   ├── test_web_ui_features.py   # Test delle funzionalità della Web UI
│   ├── test_integration_manual.py # Test di integrazione manuali
│   └── bench_deepseek_flash_vs_pro.py # Script di benchmark prestazionale DeepSeek flash/pro
├── tools/                        # Strumenti di sviluppo e diagnostica
│   ├── status_report.py          # Report di stato integrato
│   ├── validate_config.py        # Validazione della configurazione
│   ├── performance_diagnose.py   # Diagnostica delle prestazioni
│   ├── inspect_schema.py         # Ispezione della struttura Neo4j
│   └── batch_reprocess.py        # Rielaborazione in blocco
├── docs/                         # Documentazione
├── logs/                         # Log (rotazione temporale, conservati per 30 giorni per impostazione predefinita)
├── Dockerfile                    # Deployment containerizzato Docker
└── ecosystem.config.cjs          # Configurazione PM2
```

## Configurazione del client MCP

### Modalità HTTP (consigliata)

Adatta ai client MCP che supportano HTTP come Claude Code, Cline, ecc.:

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

### Modalità STDIO

Adatta ai client che necessitano di avviare direttamente il processo, come Claude Desktop:

**Posizione del file di configurazione:**
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

> **Nota**: la modalità SSE (`--transport sse`) è sconsigliata. MCP 1.x presenta problemi di compatibilità nell'inizializzazione della sessione; passare alla modalità HTTP.

## Strumenti MCP (19)

### Gestione della memoria (7)

| Strumento | Descrizione |
|------|------|
| `add_memory_simple` | Aggiunge memoria al grafo della conoscenza (supporta elaborazione in background, segmentazione intelligente, controllo di deduplicazione) |
| `add_episode_bulk` | Aggiunta in blocco di molteplici memorie (elaborazione in background per impostazione predefinita) |
| `add_triplet` | Aggiunta di triple strutturate (salta l'LLM, completata in un istante) |
| `search_memory_nodes` | Ricerca dei nodi di memoria (supporta 16 strategie di ricerca, filtro temporale) |
| `search_memory_facts` | Ricerca dei fatti di memoria (supporta filtro per tipo di relazione, intervallo temporale, filtro di validità) |
| `advanced_search` | Ricerca avanzata (16 strategie, restituisce nodi+archi+comunità+frammenti) |
| `get_episodes` | Recupera i frammenti di memoria recenti |

### Analisi della conoscenza (3)

| Strumento | Descrizione |
|------|------|
| `check_conflicts` | Rileva conflitti tra fatti di due entità (valido vs già invalidato) |
| `get_node_edges` | Esplora le relazioni degli archi entranti e uscenti di un nodo |
| `build_communities` | Attiva il rilevamento e il raggruppamento delle comunità (elaborazione in background per impostazione predefinita) |

### Manutenzione della memoria (2)

| Strumento | Descrizione |
|------|------|
| `get_stale_memories` | Interroga le memorie obsolete e a basso accesso |
| `cleanup_stale_memories` | Ripulisce le memorie obsolete (modalità di anteprima dry_run per impostazione predefinita) |

### Gestione dei task

| Strumento | Descrizione |
|------|------|
| `get_memory_task_status` | Interroga il progresso e i risultati del task di elaborazione della memoria in background |

### Eliminazione e query

| Strumento | Descrizione |
|------|------|
| `delete_episode` | Elimina un frammento di memoria |
| `delete_entity_edge` | Elimina un arco di entità (relazione) |
| `get_entity_edge` | Recupera le informazioni dettagliate di un arco di entità |

### Gestione del sistema

| Strumento | Descrizione |
|------|------|
| `get_status` | Recupera lo stato del servizio (Neo4j, LLM, embedder) |
| `test_connection` | Testa la connessione Neo4j / LLM / embedder |
| `clear_graph` | Cancella il database a grafo (supporta la cancellazione per group_id) |

## Parametri degli strumenti

### add_memory_simple

| Parametro | Tipo | Obbligatorio | Valore predefinito | Descrizione |
|------|------|------|--------|------|
| `name` | string | Y | | Nome della memoria |
| `episode_body` | string | Y | | Contenuto della memoria (segmentazione automatica oltre 800 caratteri) |
| `group_id` | string | | `"default"` | ID del gruppo (consigliato isolare per progetto) |
| `source` | string | | `"text"` | Tipo di origine: `text` / `json` / `message` |
| `source_description` | string | | `"MCP Server"` | Descrizione dell'origine |
| `use_safe_mode` | bool | | `false` | Modalità sicura (salta l'estrazione delle entità, veloce ma la memoria non è ricercabile) |
| `background` | bool | | `false` | Elaborazione in background (restituisce immediatamente task_id, adatta a testi lunghi) |
| `force` | bool | | `false` | Salta il controllo di deduplicazione (aggiunta forzata) |
| `excluded_entity_types` | list | | | Tipi di entità da escludere (riduce le estrazioni non necessarie) |

> **Suggerimenti sulle prestazioni**:
> - Testi brevi (<800 caratteri): elaborazione diretta, di solito completata in 30-40 secondi
> - Testi lunghi (>800 caratteri): segmentazione automatica in più parti, elaborazione concorrente con `add_episode_bulk` (~33% più veloce rispetto a quella seriale)
> - L'uso di `background=true` evita il blocco della chiamata MCP, tracciando il progresso tramite `get_memory_task_status`
> - `use_safe_mode=true` si completa in un istante ma la memoria non può essere trovata dagli strumenti di ricerca
> - Quando la deduplicazione è abilitata, le memorie altamente simili vengono segnalate (`force=true` consente di saltare)

### add_episode_bulk

| Parametro | Tipo | Obbligatorio | Valore predefinito | Descrizione |
|------|------|------|--------|------|
| `episodes` | list | Y | | Elenco delle memorie, ogni elemento contiene `name` e `content` |
| `group_id` | string | | `"default"` | ID del gruppo |
| `source` | string | | `"text"` | Tipo di origine |
| `background` | bool | | `true` | Elaborazione in background (l'operazione in blocco è di solito dispendiosa in termini di tempo) |

### add_triplet

| Parametro | Tipo | Obbligatorio | Valore predefinito | Descrizione |
|------|------|------|--------|------|
| `source_name` | string | Y | | Nome dell'entità di origine (es. "Alice") |
| `target_name` | string | Y | | Nome dell'entità di destinazione (es. "Google") |
| `relation_name` | string | Y | | Nome della relazione (es. "works_at") |
| `fact` | string | Y | | Descrizione del fatto (es. "Alice works at Google") |
| `group_id` | string | | `"default"` | ID del gruppo |
| `source_labels` | list | | | Etichette dell'entità di origine |
| `target_labels` | list | | | Etichette dell'entità di destinazione |

### search_memory_nodes

| Parametro | Tipo | Obbligatorio | Valore predefinito | Descrizione |
|------|------|------|--------|------|
| `query` | string | Y | | Parole chiave di ricerca (linguaggio naturale) |
| `max_nodes` | int | | `10` | Numero massimo di risultati restituiti |
| `group_ids` | list | | | Filtro per gruppo (ricerca congiunta su più gruppi) |
| `entity_types` | list | | | Filtro per tipo di entità |
| `search_recipe` | string | | | Strategia di ricerca (vedi ricerca avanzata) |
| `created_after` | string | | | Limite inferiore del tempo di creazione (ISO datetime) |
| `created_before` | string | | | Limite superiore del tempo di creazione (ISO datetime) |

### search_memory_facts

| Parametro | Tipo | Obbligatorio | Valore predefinito | Descrizione |
|------|------|------|--------|------|
| `query` | string | Y | | Parole chiave di ricerca |
| `max_facts` | int | | `10` | Numero massimo di risultati restituiti |
| `group_ids` | list | | | Filtro per gruppo |
| `center_node_uuid` | string | | | UUID del nodo centrale (esplora le relazioni di un nodo specifico) |
| `edge_types` | list | | | Filtro per tipo di relazione (es. `["works_at"]`) |
| `created_after` | string | | | Limite inferiore del tempo di creazione (ISO datetime) |
| `created_before` | string | | | Limite superiore del tempo di creazione (ISO datetime) |
| `only_valid` | bool | | `false` | Restituisce solo i fatti non invalidati |

### advanced_search

| Parametro | Tipo | Obbligatorio | Valore predefinito | Descrizione |
|------|------|------|--------|------|
| `query` | string | Y | | Parole chiave di ricerca |
| `search_recipe` | string | | `"combined_rrf"` | Strategia di ricerca (16 opzioni) |
| `max_results` | int | | `10` | Numero massimo di risultati restituiti |
| `group_ids` | list | | | Filtro per gruppo |
| `center_node_uuid` | string | | | UUID del nodo centrale |

**Strategie di ricerca disponibili (search_recipe):**

| Categoria | Strategia | Descrizione |
|------|------|------|
| Combinata | `combined_rrf` | Fusione RRF combinata (predefinita, consigliata) |
| Combinata | `combined_mmr` | Riordino per diversità MMR combinato |
| Combinata | `combined_cross_encoder` | Ordinamento fine Cross-Encoder combinato |
| Archi | `edge_rrf` / `edge_mmr` / `edge_cross_encoder` | Ricerca sugli archi (3 ordinamenti) |
| Archi | `edge_node_distance` / `edge_episode_mentions` | Ricerca sugli archi (distanza nel grafo/numero di citazioni) |
| Nodi | `node_rrf` / `node_mmr` / `node_cross_encoder` | Ricerca sui nodi (3 ordinamenti) |
| Nodi | `node_node_distance` / `node_episode_mentions` | Ricerca sui nodi (distanza nel grafo/numero di citazioni) |
| Comunità | `community_rrf` / `community_mmr` / `community_cross_encoder` | Ricerca sulle comunità |

### check_conflicts

| Parametro | Tipo | Obbligatorio | Valore predefinito | Descrizione |
|------|------|------|--------|------|
| `source_name` | string | Y | | Nome dell'entità di origine |
| `target_name` | string | Y | | Nome dell'entità di destinazione |
| `group_id` | string | | `"default"` | ID del gruppo |

### get_node_edges

| Parametro | Tipo | Obbligatorio | Valore predefinito | Descrizione |
|------|------|------|--------|------|
| `node_uuid` | string | Y | | UUID del nodo |
| `include_inbound` | bool | | `true` | Include gli archi entranti |
| `include_outbound` | bool | | `true` | Include gli archi uscenti |
| `max_edges` | int | | `50` | Numero massimo di risultati restituiti |

### build_communities

| Parametro | Tipo | Obbligatorio | Valore predefinito | Descrizione |
|------|------|------|--------|------|
| `group_ids` | list | | | Gruppi specificati (se vuoto, tutti) |
| `background` | bool | | `true` | Elaborazione in background |

### get_stale_memories

| Parametro | Tipo | Obbligatorio | Valore predefinito | Descrizione |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Dopo quanti giorni senza accesso è considerata obsoleta |
| `min_access_count` | int | | `2` | Inclusa solo se il numero di accessi è inferiore a questo valore |
| `group_id` | string | | | Filtro per gruppo |
| `limit` | int | | `50` | Numero massimo di risultati restituiti |

### cleanup_stale_memories

| Parametro | Tipo | Obbligatorio | Valore predefinito | Descrizione |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Soglia dei giorni di obsolescenza |
| `min_access_count` | int | | `2` | Soglia del numero minimo di accessi |
| `group_id` | string | | | Filtro per gruppo |
| `dry_run` | bool | | `true` | Modalità di anteprima (non elimina effettivamente) |
| `limit` | int | | `50` | Numero massimo da elaborare |

### get_memory_task_status

| Parametro | Tipo | Obbligatorio | Descrizione |
|------|------|------|------|
| `task_id` | string | Y | ID del task in background (restituito da `add_memory_simple(background=true)`) |

## Interfaccia di gestione Web

In modalità HTTP è accessibile da `http://localhost:8000/`.

**Funzionalità:**
- Dashboard — statistiche su numero di nodi, fatti, frammenti di memoria
- Nodi entità — navigazione, filtro, ricerca vettoriale
- Relazioni tra fatti — navigazione, filtro, ricerca vettoriale
- Frammenti di memoria — navigazione, ricerca full-text, eliminazione
- Navigazione delle comunità — elenco dei nodi delle comunità, riassunto, attivazione della costruzione delle comunità
- Modulo delle triple — aggiunta diretta di conoscenza strutturata «soggetto-relazione-oggetto»
- Gestione dei gruppi — filtro per gruppo, eliminazione in blocco
- Visualizzazione del grafo della conoscenza — rappresentazione grafica delle relazioni tra nodi
- Domande e risposte con AI — domande e risposte intelligenti basate sul grafo della conoscenza
- Analisi della qualità — analisi della qualità e della copertura della memoria
- Cambio di tema — tema scuro/chiaro

**REST API:**

| Endpoint | Metodo | Descrizione |
|------|------|------|
| `/api/stats` | GET | Statistiche della dashboard |
| `/api/groups` | GET | Recupera tutti i group_id |
| `/api/nodes` | GET | Naviga i nodi entità (paginato) |
| `/api/facts` | GET | Naviga i fatti (paginato) |
| `/api/episodes` | GET | Naviga i frammenti di memoria (paginato) |
| `/api/search/nodes` | GET | Ricerca vettoriale dei nodi |
| `/api/search/facts` | GET | Ricerca vettoriale dei fatti |
| `/api/search/advanced` | GET | Ricerca avanzata (16 strategie) |
| `/api/communities` | GET | Naviga i nodi delle comunità (paginato) |
| `/api/communities/build` | POST | Attiva la costruzione delle comunità |
| `/api/memory/add-bulk` | POST | Aggiunta in blocco di memoria |
| `/api/memory/add-triplet` | POST | Aggiunta di triple |
| `/api/memory/tasks` | GET | Elenca i task in background (supporta il filtro per stato) |
| `/api/memory/tasks/{id}` | GET | Interroga lo stato di un singolo task |
| `/api/analytics/stale` | GET | Interroga le memorie obsolete |
| `/api/analytics/cleanup` | POST | Ripulisce le memorie obsolete |
| `/api/nodes/{uuid}` | DELETE | Elimina un nodo |
| `/api/episodes/{uuid}` | DELETE | Elimina un frammento di memoria |
| `/api/facts/{uuid}` | DELETE | Elimina un fatto |
| `/api/groups/{group_id}` | DELETE | Elimina un intero gruppo |

## Configurazione

### Variabili d'ambiente (.env)

La configurazione usa un meccanismo a sovrapposizione: il file di configurazione JSON come base, le variabili d'ambiente sovrascrivono i singoli valori.

```bash
# === Obbligatorio ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password        # Deve essere modificato

# === Scelta del fornitore LLM ===
LLM_PROVIDER=ollama                 # ollama / glm / groq / openrouter / deepseek

# === Fornitore di Embedding (opzionale, per impostazione predefinita segue LLM_PROVIDER) ===
# Solo glm usa GLM Embedding, tutti gli altri usano Ollama bge-m3
# EMBEDDING_PROVIDER=ollama         # ollama / glm

# === Configurazione Ollama (usata quando LLM_PROVIDER=ollama) ===
OLLAMA_MODEL=qwen2.5:3b             # Modello principale (consigliato qwen2.5:3b)
OLLAMA_SMALL_MODEL=qwen2.5:3b       # Modello piccolo (per task semplici, può essere un modello diverso)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.1

# === Configurazione GLM (usata quando LLM_PROVIDER=glm) ===
GLM_API_KEY=your_api_key            # Ottenibile da https://open.bigmodel.cn
GLM_MODEL=glm-4-flash               # Modello gratuito
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768

# === Configurazione GROQ (usata quando LLM_PROVIDER=groq) ===
GROQ_API_KEY=your_api_key           # Ottenibile da https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile

# === Configurazione OpenRouter (usata quando LLM_PROVIDER=openrouter) ===
OPENROUTER_API_KEY=your_api_key     # Ottenibile da https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free

# === Configurazione DeepSeek (usata quando LLM_PROVIDER=deepseek) ===
DEEPSEEK_API_KEY=your_api_key       # Ottenibile da https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash    # Oppure deepseek-v4-pro

# === Modello di embedding Ollama (usato in tutti i casi di embedding diversi da glm) ===
OLLAMA_EMBEDDING_MODEL=bge-m3
OLLAMA_EMBEDDING_DIMENSIONS=768

# === Visualizzazione e lingua (opzionale) ===
GRAPHITI_DISPLAY_TIMEZONE=Asia/Taipei # Fuso orario di visualizzazione dei timestamp restituiti dall'API (nome IANA; l'archiviazione resta in UTC)
SERVER_LANG=zh-TW                     # Lingua di risposta degli strumenti MCP (locale complete in src/i18n.py); le REST API si basano su Accept-Language

# === Prestazioni della memoria (opzionale) ===
GRAPHITI_CHUNK_THRESHOLD=800         # Soglia di caratteri che attiva la segmentazione intelligente
GRAPHITI_MAX_CHUNK_SIZE=600          # Numero massimo di caratteri per segmento
GRAPHITI_MAX_COROUTINES=10            # Numero massimo di coroutine concorrenti
GRAPHITI_DEFAULT_BACKGROUND=false    # Se l'elaborazione in background è predefinita

# === Tracciamento dell'importanza e oblio intelligente (opzionale) ===
ENABLE_IMPORTANCE_TRACKING=true      # Abilita il tracciamento degli accessi
IMPORTANCE_WEIGHT=0.1                # Peso dell'importanza
STALE_DAYS_THRESHOLD=30              # Soglia dei giorni di obsolescenza
STALE_MIN_ACCESS_COUNT=2             # Numero minimo di accessi

# === Log ===
LOG_FILE=logs/graphiti_mcp_server.log
LOG_LEVEL=INFO
```

> **Per l'elenco completo delle variabili d'ambiente** consultare `.env.example`

### File di configurazione JSON

Adatto a configurazioni che necessitano di controllo di versione (le variabili d'ambiente possono comunque sovrascrivere):

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

## Esecuzione in background con PM2

```bash
npm install -g pm2

pm2 start ecosystem.config.cjs      # Avvio
pm2 status                           # Stato
pm2 logs graphiti-mcp-http           # Log in tempo reale
pm2 restart graphiti-mcp-http --update-env  # Riavvio (ricarica .env)

pm2 save && pm2 startup              # Imposta l'avvio automatico all'accensione
```

> **Suggerimento**: dopo aver modificato `.env` è necessario riavviare con il flag `--update-env`, altrimenti le variabili d'ambiente non verranno aggiornate.

## Deployment Docker

```bash
docker build -t graphiti-mcp .

# Nota: il container Docker deve essere in grado di connettersi a Neo4j e Ollama
# L'uso della host network è il modo più semplice
docker run -p 8000:8000 --env-file .env --network host graphiti-mcp

# Oppure specificare esplicitamente gli indirizzi dei servizi esterni
docker run -p 8000:8000 \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --env-file .env graphiti-mcp
```

## Test

```bash
# Esegue tutti i test (183, circa 1 secondo)
uv run python -m pytest tests/

# Output dettagliato
uv run python -m pytest tests/ -v

# Esegue solo test specifici
uv run python -m pytest tests/test_content_preprocessor.py -v
uv run python -m pytest tests/test_new_features.py -v
uv run python -m pytest tests/test_unit.py -v
```

> **Nota**: i 3 test async in `test_integration_manual.py` richiedono l'installazione di `pytest-asyncio`; se mancante, verranno visualizzati come Failed ma senza influire sugli altri test. `bench_deepseek_flash_vs_pro.py` è uno script di benchmark prestazionale, non un test unitario.

## Risoluzione dei problemi

### Connessione a Neo4j fallita

```bash
neo4j status                              # Controlla lo stato del servizio
cypher-shell -u neo4j -p your_password    # Verifica che la password sia corretta
curl http://localhost:7474                 # Verifica la porta HTTP
```

Cause comuni:
- Neo4j non avviato
- Password errata (`NEO4J_PASSWORD` in `.env`)
- Porta occupata o bloccata dal firewall

### Connessione LLM fallita

**Modalità Ollama:**
```bash
ollama serve                # Avvia il servizio Ollama
ollama list                 # Controlla i modelli installati
ollama pull qwen2.5:3b      # Installa il modello mancante
```

Cause comuni: Ollama non avviato, modello non installato, memoria GPU insufficiente

**Modalità GLM:**
- Verificare che `GLM_API_KEY` sia corretta
- Verificare che `GLM_EMBEDDING_DIMENSIONS=768` (deve coincidere con l'indice vettoriale Neo4j)
- Endpoint API GLM: `https://open.bigmodel.cn/api/paas/v4/`

**Modalità GROQ:**
- Verificare che `GROQ_API_KEY` sia corretta
- Se il Rate Limit è frequente, considerare il passaggio alla modalità GLM
- GROQ non fornisce Embedding, è necessario garantire che l'embedder Ollama sia disponibile

**Modalità OpenRouter:**
- Verificare che `OPENROUTER_API_KEY` sia corretta e che `OPENROUTER_MODEL` sia un ID modello valido (vedi https://openrouter.ai/models)
- Non fornisce Embedding, è necessario garantire che l'embedder Ollama sia disponibile

**Modalità DeepSeek:**
- Verificare che `DEEPSEEK_API_KEY` sia corretta
- Se compare `Prompt must contain the word 'json'`: questo è un requisito rigido della modalità `json_object` di DeepSeek; il client integra già una protezione di sicurezza; se persiste, verificare di usare la versione più recente di `src/deepseek_client.py` e riavviare il servizio
- Non fornisce Embedding, è necessario garantire che l'embedder Ollama sia disponibile

### Errore di connessione MCP

Se compare `Invalid request parameters` o `Received request before initialization was complete`:

1. Verificare di usare la modalità di trasporto HTTP (**non usare SSE**)
2. Verificare che il client sia impostato su `"type": "http"`, `"url": "http://localhost:8000/mcp"`
3. Riavviare il servizio: `pm2 restart graphiti-mcp-http --update-env`
4. Eseguire `/mcp` in Claude Code per riconnettersi

### Aggiunta della memoria lenta

- **Ollama**: controllare la dimensione del modello (`qwen2.5:3b` è 5-10 volte più veloce di `7b`), verificare l'uso della GPU (`ollama ps`)
- **GLM**: ogni add_episode richiede oltre 10-20 round trip di rete LLM, ~22s per testo breve è un valore normale
- **GROQ**: il Rate Limit causa numerosi tentativi di ripetizione; in caso di uso frequente si consiglia di passare a GLM o Ollama
- Usare `background=true` per evitare il blocco
- Abbassare `GRAPHITI_CHUNK_THRESHOLD` per segmentare prima i testi lunghi

### Problemi con PM2

```bash
pm2 status                                        # Controlla lo stato
pm2 logs graphiti-mcp-http --err --lines 50        # Log degli errori
lsof -i :8000                                     # Controlla l'occupazione della porta
pm2 delete graphiti-mcp-http && pm2 start ecosystem.config.cjs  # Riavvio completo
```

## Strumenti di sviluppo e diagnostica

```bash
uv run python tools/status_report.py           # Report di stato integrato (Neo4j + Ollama + configurazione)
uv run python tools/validate_config.py         # Valida la completezza di .env e della configurazione
uv run python tools/performance_diagnose.py    # Diagnostica delle prestazioni LLM
uv run python tools/inspect_schema.py          # Controllo degli indici e dei vincoli Neo4j
uv run python tools/migrate_embeddings.py      # Migrazione del modello di embedding (rigenera i vettori dopo il cambio di modello)
```

### Migrazione del modello di embedding

Dopo aver cambiato il modello di embedding (ad es. `nomic-embed-text` → `bge-m3`), è possibile usare lo strumento di migrazione per rigenerare tutti i vettori esistenti, garantendo una qualità di ricerca coerente:

```bash
# Anteprima del numero da migrare
uv run python tools/migrate_embeddings.py --dry-run

# Migrazione completa (supporta la ripresa da checkpoint)
uv run python tools/migrate_embeddings.py

# Migra solo un gruppo specificato
uv run python tools/migrate_embeddings.py --group-id myproject

# Riprende da checkpoint (riesecuzione dopo un'interruzione)
uv run python tools/migrate_embeddings.py --resume
```

> **Compatibilità**: `bge-m3` è nativamente a 1024 dimensioni, il sistema lo tronca automaticamente a 768 dimensioni per compatibilità con l'indice vettoriale Neo4j esistente. I dati prima e dopo la migrazione possono coesistere, ma si consiglia di eseguire una migrazione completa per ottenere la migliore qualità di ricerca.

## Documentazione

- [Istruzioni per l'uso degli strumenti](../使用工具的指令.md) — guida all'uso degli strumenti MCP e migliori pratiche
- [Graphiti Memory Rules](../graphiti-memory-rules.md) — spiegazione delle regole di memoria

## Licenza

MIT License
