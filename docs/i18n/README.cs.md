# Graphiti MCP Server

Služba paměti znalostního grafu — MCP server integrující více poskytovatelů LLM (Ollama / GLM / GROQ / OpenRouter / DeepSeek) s grafovou databází Neo4j.

Vyvinuto jako rozšíření [getzep/graphiti](https://github.com/getzep/graphiti), podporuje pružné přepínání mezi lokálním Ollama a cloudovými LLM a umožňuje nezávisle určit poskytovatele Embeddingu (odděleně od LLM).

## Klíčové funkce

- **Inteligentní správa paměti** — ukládání a vyhledávání složitých paměťových vztahů pomocí znalostního grafu
- **Sémantické vyhledávání** — hybridní vyhledávání založené na vektorových embeddinzích (vektor + klíčová slova + procházení grafu)
- **16 vyhledávacích strategií** — pokročilé vyhledávání podporuje RRF, MMR, Cross-Encoder a další způsoby přeřazování
- **Více poskytovatelů LLM** — podpora Ollama (lokální), GLM (Zhipu AI zdarma), GROQ (vysokorychlostní inference), OpenRouter (agregace modelů různých výrobců), DeepSeek (Deep Seek), přepínání jedním krokem přes proměnnou prostředí
- **Oddělení Embeddingu a LLM** — embedder lze nezávisle určit pomocí `EMBEDDING_PROVIDER`, cloudové LLM automaticky přejdou na lokální `bge-m3`
- **Rozdělení mezi dva modely** — v režimu Ollama používají složité úlohy hlavní model, jednoduché úlohy automaticky přepnou na malý model pro zvýšení výkonu
- **Inteligentní dělení obsahu** — dlouhé texty se automaticky rozdělují na segmenty, čímž se snižuje zátěž LLM (konfigurovatelný práh)
- **Zpracování paměti na pozadí** — přidávání paměti může běžet na pozadí, volání MCP se vrací okamžitě; stav úloh je trvale uložen v SQLite, po restartu se automaticky obnoví nedokončené úlohy
- **Deduplikace paměti** — automatické rozpoznání vysoce podobných existujících pamětí, zamezení duplicitnímu ukládání
- **Detekce konfliktů** — rozpoznání rozporných faktů mezi dvěma entitami, identifikace neplatných a platných informací
- **Detekce komunit** — automatické shlukování souvisejících entit pomocí algoritmu Label Propagation
- **Sledování důležitosti** — automatické zaznamenávání frekvence přístupu k entitám, řazení výsledků vyhledávání podle důležitosti
- **Inteligentní zapomínání** — identifikace a vyčištění zastaralých pamětí s nízkou frekvencí přístupu, udržení grafu kompaktního
- **Hromadný import** — odeslání více pamětí najednou, vhodné pro migraci velkého množství dat
- **Strukturované trojice** — přímé přidání „subjekt-vztah-objekt“, přeskočení extrakce LLM, dokončení během sekundy
- **Web UI pro správu** — vestavěný dashboard, prohlížení, vyhledávání, vizualizace znalostního grafu, AI dotazy, prohlížení komunit, správa kvality, hromadný import, nastavení za běhu
- **Vícejazyčnost (i18n)** — zprávy odpovědí podporují 33 jazyků (včetně zh-TW / en / zh-CN / ja / pt-BR / ko / es / de / fr atd.; zh-TW/en/zh-CN/ja jsou ručně psané, ostatní poskytuje generovaná vrstva); MCP nástroje podle `SERVER_LANG`, REST API automaticky vyjednává podle HTTP `Accept-Language`
- **Tmavý/světlý motiv** — Web UI podporuje přepínání motivů
- **Bezpečný režim** — volitelné rychlé přidání paměti s přeskočením extrakce entit
- **Podpora Docker** — vestavěný Dockerfile, podpora nasazení v kontejneru
- **Bezpečnost při souběhu** — asyncio.Lock chrání inicializaci, zabraňuje souběžným podmínkám (race conditions)
- **Vrstvená kontrola zdraví** — `/health` (liveness) + `/health/ready` (readiness)

## Systémové požadavky

| Položka | Požadavek |
|------|------|
| Python | 3.10+ (doporučeno 3.11+) |
| Neo4j | 4.0+ (`bolt://localhost:7687`) |
| Poskytovatel LLM | Ollama / GLM / GROQ / OpenRouter / DeepSeek (jeden z pěti) |
| Node.js | 18+ (pouze pro běh na pozadí přes PM2, volitelné) |
| Místo na disku | ~3 GB (modely Ollama + data Neo4j) |

### Výběr poskytovatele LLM

Přepínání přes proměnnou prostředí `LLM_PROVIDER` (`ollama` / `glm` / `groq` / `openrouter` / `deepseek`):

| Poskytovatel | Vlastnosti | Model LLM | Embedding | Vhodné scénáře |
|--------|------|----------|-----------|----------|
| **Ollama** (výchozí) | Plně lokální, data neopouštějí počítač | `qwen2.5:3b` | `bge-m3` (vynikající čínština + RAG) | s GPU, důraz na soukromí |
| **GLM** | Cloud zdarma, stabilní bez omezení toku | `glm-4-flash` (zdarma) | `embedding-3` | bez GPU, vyhledávací náročné scénáře |
| **GROQ** | Ultrarychlá inference | `llama-3.3-70b-versatile` | přejde na Ollama `bge-m3` | občasný zápis, důraz na kvalitu |
| **OpenRouter** | Agregace modelů různých výrobců, včetně bezplatné kvóty | `stepfun/step-3.5-flash:free` atd. | přejde na Ollama `bge-m3` | chcete použít konkrétní cloudový model |
| **DeepSeek** | Cloud Deep Seek, vysoký poměr cena/výkon | `deepseek-v4-flash` / `deepseek-v4-pro` | přejde na Ollama `bge-m3` | porozumění čínštině, nízkonákladový cloud |

> **Oddělení Embeddingu a LLM**: embedder se nezávisle určuje přes `EMBEDDING_PROVIDER` (`ollama` / `glm`), pokud není nastaven, řídí se podle `LLM_PROVIDER`. Ve skutečnosti pouze `glm` používá GLM `embedding-3`, ostatní (včetně cloudových LLM jako GROQ / OpenRouter / DeepSeek, které neposkytují Embedding) vždy automaticky používají Ollama `bge-m3`. **Proto při použití jakéhokoli cloudového LLM je stále potřeba lokální Ollama poskytující službu embeddingu (pokud není embedding také nastaven na glm).**

#### Režim Ollama (lokální)

```bash
# Hlavní model LLM (doporučeno qwen2.5:3b, nejlepší rovnováha rychlosti a stability)
ollama pull qwen2.5:3b

# Model embeddingu (povinný, používá se pro vektorové vyhledávání)
ollama pull bge-m3
```

> **Poznámky k výběru modelu**:
> - `qwen2.5:3b` — doporučeno, ~2 s/volání, ~100 t/s, strukturovaný výstup graphiti-core 100% stabilní
> - `qwen2.5:7b` — lepší výsledky, ale 5–10krát pomalejší, vhodné pro scénáře s důrazem na kvalitu
> - `qwen2.5:1.5b` — nejrychlejší, ale **nestabilní** (úspěšnost strukturovaného JSON pouze 33 %), nedoporučuje se používat

#### Režim GLM (cloud Zhipu AI)

```bash
# Nastavení .env
LLM_PROVIDER=glm
GLM_API_KEY=your_api_key          # získejte na https://open.bigmodel.cn
GLM_MODEL=glm-4-flash             # model zdarma
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768      # musí odpovídat dimenzi vektorového indexu Neo4j
```

> **Referenční výkon GLM**: zápis ~22 s (krátký text), vyhledávání ~0,34 s, nula chyb Rate Limit, 2–5krát pomalejší než lokální Ollama, ale zcela zdarma.

#### Režim GROQ (vysokorychlostní inference)

```bash
# Nastavení .env
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key         # získejte na https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile
```

> **Poznámka**: GROQ neposkytuje službu Embedding, je potřeba ji kombinovat s embedderem Ollama (automatický přechod) nebo nastavit `EMBEDDING_PROVIDER` na glm. GROQ má přísný Rate Limit, vysokofrekvenční použití spustí mnoho opakovaných pokusů.

#### Režim OpenRouter (agregace modelů různých výrobců)

```bash
# Nastavení .env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_api_key       # získejte na https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free   # lze změnit na libovolný model OpenRouter
```

> **Poznámka**: OpenRouter neposkytuje Embedding, automaticky přejde na Ollama `bge-m3`. Seznam modelů viz https://openrouter.ai/models (včetně více bezplatných modelů `:free`).

#### Režim DeepSeek (Deep Seek)

```bash
# Nastavení .env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key         # získejte na https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash      # doporučeno; nebo deepseek-v4-pro (lepší výsledky)
```

> **Poznámka**: DeepSeek neposkytuje Embedding, automaticky přejde na Ollama `bge-m3`. `deepseek-chat` / `deepseek-reasoner` budou vyřazeny 2026-07-24, doporučuje se přejít na `deepseek-v4-flash` / `deepseek-v4-pro`. DeepSeek přísně vyžaduje, aby prompt v režimu `json_object` obsahoval řetězec „json“, klient má vestavěnou záložní ochranu, není potřeba žádné další nastavení.

## Rychlé spuštění

### 1. Příprava

Ověřte, že Neo4j běží na lokálním počítači, a podle zvoleného poskytovatele LLM připravte odpovídající službu:

```bash
# Ověřte, že Neo4j běží (povinné)
neo4j status
# Nebo použijte Docker: docker run -d -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/your_password neo4j:latest

# Režim Ollama: ověřte, že Ollama běží
ollama list
# Pokud není spuštěna: ollama serve

# Režim GLM / GROQ: stačí platný API Key, lokální služba není potřeba
```

### 2. Instalace závislostí

```bash
git clone <repo-url>
cd graphiti
uv sync
```

> **Poznámka**: Tento projekt používá ke správě závislostí [uv](https://github.com/astral-sh/uv). Pokud není nainstalován: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 3. Konfigurace prostředí

```bash
cp .env.example .env
```

Upravte `.env`, je potřeba změnit **alespoň** následující položky:

```bash
NEO4J_PASSWORD=your_actual_password  # povinné: heslo Neo4j
LLM_PROVIDER=ollama                  # ollama / glm / groq / openrouter / deepseek
OLLAMA_MODEL=qwen2.5:3b              # režim Ollama: lokální model LLM
# GLM_API_KEY=your_key               # režim GLM: API Key Zhipu AI
# GROQ_API_KEY=your_key              # režim GROQ: API Key GROQ
# OPENROUTER_API_KEY=your_key        # režim OpenRouter: API Key
# DEEPSEEK_API_KEY=your_key          # režim DeepSeek: API Key
```

### 4. Spuštění služby

```bash
# Režim HTTP (doporučeno, obsahuje Web UI pro správu)
uv run python graphiti_mcp_server.py --transport http --port 8000

# Nebo běh na pozadí přes PM2 (doporučeno pro dlouhodobý provoz)
pm2 start ecosystem.config.cjs
```

### 5. Ověření služby

Po spuštění lze přistupovat k následujícím koncovým bodům:

| Koncový bod | Popis |
|------|------|
| http://localhost:8000/ | Web UI pro správu |
| http://localhost:8000/mcp | Koncový bod MCP (pro připojení MCP klientů) |
| http://localhost:8000/health | Kontrola zdraví (liveness) |
| http://localhost:8000/health/ready | Hloubková kontrola (včetně připojení Neo4j) |
| http://localhost:8000/api/stats | Statistiky REST API |

## Struktura projektu

```
graphiti/
├── graphiti_mcp_server.py        # Hlavní vstupní bod — definice MCP nástrojů (19 nástrojů)
├── src/
│   ├── config.py                 # Správa konfigurace (GraphitiConfig, podpora vrstvení JSON/.env)
│   ├── web_api.py                # REST API Web UI pro správu (30+ koncových bodů)
│   ├── ollama_graphiti_client.py  # Klient Ollama LLM (rozdělení mezi dva modely)
│   ├── openai_compat_client.py   # Základní třída OpenAI kompatibilního LLM (json_object + zjednodušené schéma + záložní ochrana json)
│   ├── glm_client.py             # Klient GLM (Zhipu AI) LLM (dědí OpenAICompatClient)
│   ├── openrouter_client.py      # Klient OpenRouter LLM (dědí OpenAICompatClient)
│   ├── deepseek_client.py        # Klient DeepSeek LLM (dědí OpenAICompatClient)
│   ├── ollama_embedder.py        # Adaptér modelu embeddingu Ollama
│   ├── content_preprocessor.py   # Inteligentní dělení obsahu (automatické segmentování dlouhého textu)
│   ├── deduplication.py          # Deduplikace paměti (porovnání kosinové podobnosti)
│   ├── importance.py             # Sledování důležitosti a inteligentní zapomínání
│   ├── safe_memory_add.py        # Bezpečné přidání paměti (přeskočení extrakce entit)
│   ├── task_store.py             # Trvalé ukládání úloh na pozadí v SQLite (TaskStore)
│   ├── timezone_utils.py         # Převod časového pásma (zobrazení UTC→lokální časové pásmo)
│   ├── i18n.py                   # Backendová vícejazyčnost (REST podle Accept-Language, MCP podle SERVER_LANG)
│   ├── i18n_generated.py         # Automaticky generované jazykové přepisy (GENERATED_MESSAGE_OVERRIDES)
│   ├── exceptions.py             # Strukturované zpracování výjimek (12 typů tříd výjimek)
│   └── logging_setup.py          # Systém protokolování (časová rotace + monitorování výkonu)
├── web/                          # Frontend Web UI pro správu (SPA, bez buildu)
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js                # Obal REST API
│       ├── components.js         # Vykreslování UI komponent (včetně stránky komunit)
│       └── app.js                # Routování SPA, správa stavu
├── tests/                        # Testovací sada (203 testů)
│   ├── test_content_preprocessor.py  # Testy logiky dělení (17 testů)
│   ├── test_new_features.py      # Testy nových funkcí (32 testů)
│   ├── test_i18n.py             # Testy vícejazyčnosti (57 testů)
│   ├── test_unit.py              # Jednotkové testy
│   ├── test_web_api.py           # Testy Web API
│   ├── test_web_ui_features.py   # Testy funkcí Web UI
│   ├── test_integration_manual.py # Manuální integrační testy
│   └── bench_deepseek_flash_vs_pro.py # Skript pro benchmark výkonu DeepSeek flash/pro
├── tools/                        # Vývojářské diagnostické nástroje
│   ├── status_report.py          # Souhrnná zpráva o stavu
│   ├── validate_config.py        # Validace konfigurace
│   ├── performance_diagnose.py   # Diagnostika výkonu
│   ├── inspect_schema.py         # Kontrola struktury Neo4j
│   ├── batch_reprocess.py        # Dávkové opětovné zpracování
│   └── migrate_embeddings.py     # Migrace modelu Embedding (opětovné generování vektorů po změně modelu)
├── docs/                         # Dokumentace
├── logs/                         # Protokoly (časová rotace, výchozí uchování 30 dní)
├── Dockerfile                    # Nasazení v kontejneru Docker
└── ecosystem.config.cjs          # Konfigurace PM2
```

## Nastavení MCP klienta

### Režim HTTP (doporučeno)

Vhodné pro MCP klienty podporující HTTP, jako Claude Code, Cline atd.:

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

### Režim STDIO

Vhodné pro klienty, kteří potřebují přímo spustit proces, jako Claude Desktop atd.:

**Umístění konfiguračního souboru:**
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

> **Poznámka**: Režim SSE (`--transport sse`) se již nedoporučuje. MCP 1.x má problémy s kompatibilitou inicializace session, použijte prosím režim HTTP.

## MCP nástroje (19 nástrojů)

### Správa paměti (7 nástrojů)

| Nástroj | Popis |
|------|------|
| `add_memory_simple` | Přidání paměti do znalostního grafu (podpora zpracování na pozadí, inteligentního dělení, kontroly deduplikace) |
| `add_episode_bulk` | Hromadné přidání více pamětí (výchozí zpracování na pozadí) |
| `add_triplet` | Přidání strukturované trojice (přeskočení LLM, dokončení během sekundy) |
| `search_memory_nodes` | Vyhledávání paměťových uzlů (podpora 16 vyhledávacích strategií, časového filtrování) |
| `search_memory_facts` | Vyhledávání paměťových faktů (podpora filtrování typu vztahu, časového rozsahu, filtrování platnosti) |
| `advanced_search` | Pokročilé vyhledávání (16 strategií, vrací uzly+hrany+komunity+epizody) |
| `get_episodes` | Získání nedávných paměťových epizod |

### Analýza znalostí (3 nástroje)

| Nástroj | Popis |
|------|------|
| `check_conflicts` | Detekce faktických konfliktů mezi dvěma entitami (platné vs. neplatné) |
| `get_node_edges` | Prozkoumání vztahů příchozích a odchozích hran uzlu |
| `build_communities` | Spuštění detekce a shlukování komunit (výchozí zpracování na pozadí) |

### Údržba paměti (2 nástroje)

| Nástroj | Popis |
|------|------|
| `get_stale_memories` | Dotaz na zastaralé paměti s nízkou frekvencí přístupu |
| `cleanup_stale_memories` | Vyčištění zastaralých pamětí (výchozí režim náhledu dry_run) |

### Správa úloh

| Nástroj | Popis |
|------|------|
| `get_memory_task_status` | Dotaz na průběh a výsledek úlohy zpracování paměti na pozadí |

### Mazání a dotazy

| Nástroj | Popis |
|------|------|
| `delete_episode` | Smazání paměťové epizody |
| `delete_entity_edge` | Smazání hrany entity (vztahu) |
| `get_entity_edge` | Získání podrobných informací o hraně entity |

### Správa systému

| Nástroj | Popis |
|------|------|
| `get_status` | Získání stavu služby (Neo4j, LLM, embedder) |
| `test_connection` | Test připojení Neo4j / LLM / embedder |
| `clear_graph` | Vyčištění grafové databáze (podpora čištění podle group_id) |

## Parametry nástrojů

### add_memory_simple

| Parametr | Typ | Povinné | Výchozí hodnota | Popis |
|------|------|------|--------|------|
| `name` | string | Y | | Název paměti |
| `episode_body` | string | Y | | Obsah paměti (automatické dělení nad 800 znaků) |
| `group_id` | string | | `"default"` | ID skupiny (doporučuje se izolace podle projektu) |
| `source` | string | | `"text"` | Typ zdroje: `text` / `json` / `message` |
| `source_description` | string | | `"MCP Server"` | Popis zdroje |
| `use_safe_mode` | bool | | `false` | Bezpečný režim (přeskočení extrakce entit, rychlé, ale paměť nelze vyhledat) |
| `background` | bool | | `false` | Zpracování na pozadí (okamžitě vrací task_id, vhodné pro dlouhý text) |
| `force` | bool | | `false` | Přeskočení kontroly deduplikace (vynucené přidání) |
| `excluded_entity_types` | list | | | Vyloučené typy entit (snížení nepotřebné extrakce) |

> **Tipy k výkonu**:
> - Krátký text (<800 znaků): přímé zpracování, obvykle dokončeno za 30–40 sekund
> - Dlouhý text (>800 znaků): automatické dělení na více segmentů, souběžné zpracování pomocí `add_episode_bulk` (~33 % rychlejší než sériové)
> - Použití `background=true` zabrání blokování volání MCP, průběh lze sledovat přes `get_memory_task_status`
> - `use_safe_mode=true` dokončí během sekundy, ale paměť nelze najít vyhledávacími nástroji
> - Při zapnuté deduplikaci budou vysoce podobné paměti varovány (`force=true` umožní přeskočení)

### add_episode_bulk

| Parametr | Typ | Povinné | Výchozí hodnota | Popis |
|------|------|------|--------|------|
| `episodes` | list | Y | | Seznam pamětí, každá položka obsahuje `name` a `content` |
| `group_id` | string | | `"default"` | ID skupiny |
| `source` | string | | `"text"` | Typ zdroje |
| `background` | bool | | `true` | Zpracování na pozadí (hromadné zpracování je obvykle časově náročné) |

### add_triplet

| Parametr | Typ | Povinné | Výchozí hodnota | Popis |
|------|------|------|--------|------|
| `source_name` | string | Y | | Název zdrojové entity (např. „Alice“) |
| `target_name` | string | Y | | Název cílové entity (např. „Google“) |
| `relation_name` | string | Y | | Název vztahu (např. „works_at“) |
| `fact` | string | Y | | Popis faktu (např. „Alice works at Google“) |
| `group_id` | string | | `"default"` | ID skupiny |
| `source_labels` | list | | | Štítky zdrojové entity |
| `target_labels` | list | | | Štítky cílové entity |

### search_memory_nodes

| Parametr | Typ | Povinné | Výchozí hodnota | Popis |
|------|------|------|--------|------|
| `query` | string | Y | | Klíčová slova vyhledávání (přirozený jazyk) |
| `max_nodes` | int | | `10` | Maximální počet vrácených |
| `group_ids` | list | | | Filtrování podle skupiny (společné vyhledávání ve více skupinách) |
| `entity_types` | list | | | Filtrování podle typu entity |
| `search_recipe` | string | | | Vyhledávací strategie (viz pokročilé vyhledávání) |
| `created_after` | string | | | Dolní mez času vytvoření (ISO datetime) |
| `created_before` | string | | | Horní mez času vytvoření (ISO datetime) |

### search_memory_facts

| Parametr | Typ | Povinné | Výchozí hodnota | Popis |
|------|------|------|--------|------|
| `query` | string | Y | | Klíčová slova vyhledávání |
| `max_facts` | int | | `10` | Maximální počet vrácených |
| `group_ids` | list | | | Filtrování podle skupiny |
| `center_node_uuid` | string | | | UUID centrálního uzlu (prozkoumání vztahů konkrétního uzlu) |
| `edge_types` | list | | | Filtrování podle typu vztahu (např. `["works_at"]`) |
| `created_after` | string | | | Dolní mez času vytvoření (ISO datetime) |
| `created_before` | string | | | Horní mez času vytvoření (ISO datetime) |
| `only_valid` | bool | | `false` | Vrátit pouze neplatné fakty |

### advanced_search

| Parametr | Typ | Povinné | Výchozí hodnota | Popis |
|------|------|------|--------|------|
| `query` | string | Y | | Klíčová slova vyhledávání |
| `search_recipe` | string | | `"combined_rrf"` | Vyhledávací strategie (16 na výběr) |
| `max_results` | int | | `10` | Maximální počet vrácených |
| `group_ids` | list | | | Filtrování podle skupiny |
| `center_node_uuid` | string | | | UUID centrálního uzlu |

**Dostupné vyhledávací strategie (search_recipe):**

| Kategorie | Strategie | Popis |
|------|------|------|
| Komplexní | `combined_rrf` | Komplexní fúze RRF (výchozí, doporučeno) |
| Komplexní | `combined_mmr` | Komplexní přeřazení podle diverzity MMR |
| Komplexní | `combined_cross_encoder` | Komplexní jemné řazení Cross-Encoder |
| Hrana | `edge_rrf` / `edge_mmr` / `edge_cross_encoder` | Vyhledávání hran (3 způsoby řazení) |
| Hrana | `edge_node_distance` / `edge_episode_mentions` | Vyhledávání hran (vzdálenost v grafu/počet odkazů) |
| Uzel | `node_rrf` / `node_mmr` / `node_cross_encoder` | Vyhledávání uzlů (3 způsoby řazení) |
| Uzel | `node_node_distance` / `node_episode_mentions` | Vyhledávání uzlů (vzdálenost v grafu/počet odkazů) |
| Komunita | `community_rrf` / `community_mmr` / `community_cross_encoder` | Vyhledávání komunit |

### check_conflicts

| Parametr | Typ | Povinné | Výchozí hodnota | Popis |
|------|------|------|--------|------|
| `source_name` | string | Y | | Název zdrojové entity |
| `target_name` | string | Y | | Název cílové entity |
| `group_id` | string | | `"default"` | ID skupiny |

### get_node_edges

| Parametr | Typ | Povinné | Výchozí hodnota | Popis |
|------|------|------|--------|------|
| `node_uuid` | string | Y | | UUID uzlu |
| `include_inbound` | bool | | `true` | Zahrnout příchozí hrany |
| `include_outbound` | bool | | `true` | Zahrnout odchozí hrany |
| `max_edges` | int | | `50` | Maximální počet vrácených |

### build_communities

| Parametr | Typ | Povinné | Výchozí hodnota | Popis |
|------|------|------|--------|------|
| `group_ids` | list | | | Určení skupin (ponechte prázdné pro všechny) |
| `background` | bool | | `true` | Zpracování na pozadí |

### get_stale_memories

| Parametr | Typ | Povinné | Výchozí hodnota | Popis |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Po kolika dnech bez přístupu je považováno za zastaralé |
| `min_access_count` | int | | `2` | Zahrnuto pouze pokud je počet přístupů nižší než tato hodnota |
| `group_id` | string | | | Filtrování podle skupiny |
| `limit` | int | | `50` | Maximální počet vrácených |

### cleanup_stale_memories

| Parametr | Typ | Povinné | Výchozí hodnota | Popis |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Práh počtu dní zastarání |
| `min_access_count` | int | | `2` | Práh minimálního počtu přístupů |
| `group_id` | string | | | Filtrování podle skupiny |
| `dry_run` | bool | | `true` | Režim náhledu (bez skutečného mazání) |
| `limit` | int | | `50` | Maximální počet zpracovaných |

### get_memory_task_status

| Parametr | Typ | Povinné | Popis |
|------|------|------|------|
| `task_id` | string | Y | ID úlohy na pozadí (vráceno z `add_memory_simple(background=true)`) |

## Web UI pro správu

V režimu HTTP přistupte na `http://localhost:8000/` a můžete jej používat.

**Funkce:**
- Dashboard — statistiky počtu uzlů, faktů, paměťových epizod
- Entitní uzly — prohlížení, filtrování, vektorové vyhledávání
- Faktické vztahy — prohlížení, filtrování, vektorové vyhledávání
- Paměťové epizody — prohlížení, fulltextové vyhledávání, mazání
- Prohlížení komunit — seznam uzlů komunit, souhrny, spuštění tvorby komunit
- Formulář trojic — přímé přidání strukturovaných znalostí „subjekt-vztah-objekt“
- Správa Group — filtrování podle skupiny, dávkové mazání
- Vizualizace znalostního grafu — grafické zobrazení vztahů uzlů
- AI dotazy — inteligentní dotazování založené na znalostním grafu
- Správa kvality — metriky kvality paměti a nástroje pro čištění
- Hromadný import — import více paměťových epizod najednou (JSON, max. 500 položek)
- Nastavení za běhu — zobrazení aktuálně platné konfigurace, úprava vybraných parametrů bez restartu
- Přepínání motivu — tmavý/světlý motiv

**REST API:**

| Koncový bod | Metoda | Popis |
|------|------|------|
| `/api/stats` | GET | Statistiky dashboardu |
| `/api/groups` | GET | Získání všech group_id |
| `/api/groups/stats` | GET | Statistiky uzlů/faktů/epizod pro každou group |
| `/api/nodes` | GET | Prohlížení entitních uzlů (stránkování) |
| `/api/facts` | GET | Prohlížení faktů (stránkování) |
| `/api/episodes` | GET | Prohlížení paměťových epizod (stránkování) |
| `/api/nodes/{uuid}/relations` | GET | Získání příchozích/odchozích vztahů uzlu |
| `/api/search/nodes` | GET | Vektorové vyhledávání uzlů |
| `/api/search/facts` | GET | Vektorové vyhledávání faktů |
| `/api/search/episodes` | GET | Vyhledávání paměťových epizod |
| `/api/search/advanced` | GET | Pokročilé vyhledávání (16 strategií) |
| `/api/communities` | GET | Prohlížení uzlů komunit (stránkování) |
| `/api/communities/build` | POST | Spuštění tvorby komunit |
| `/api/memory/add` | POST | Přidání jedné paměti |
| `/api/memory/add-bulk` | POST | Hromadné přidání paměti |
| `/api/memory/add-triplet` | POST | Přidání trojice |
| `/api/import/episodes` | POST | Hromadný import paměťových epizod (JSON, max. 500 položek) |
| `/api/memory/tasks` | GET | Výpis úloh na pozadí (podpora filtrování podle stavu) |
| `/api/memory/tasks/{id}` | GET | Dotaz na stav jedné úlohy |
| `/api/timeline` | GET | Prohlížení časové osy |
| `/api/graph/subgraph` | GET | Získání podgrafu (vizualizace) |
| `/api/graph/all` | GET | Získání celého grafu (vizualizace) |
| `/api/ask` | GET | AI dotaz (vyhledávání v grafu) |
| `/api/analytics/top-nodes` | GET | Uzly s vysokou konektivitou/přístupností |
| `/api/analytics/quality` | GET | Metriky kvality znalostního grafu |
| `/api/analytics/stale` | GET | Dotaz na zastaralé paměti |
| `/api/analytics/cleanup` | POST | Vyčištění zastaralých pamětí |
| `/api/config` | GET | Získání aktuálně platné konfigurace (bez API klíčů) |
| `/api/config` | PATCH | Aktualizace upravitelných nastavení za běhu (platí pouze pro aktuální proces, po restartu se obnoví) |
| `/api/nodes/{uuid}` | DELETE | Smazání uzlu |
| `/api/episodes/{uuid}` | DELETE | Smazání paměťové epizody |
| `/api/facts/{uuid}` | DELETE | Smazání faktu |
| `/api/groups/{group_id}` | DELETE | Smazání celé group |

## Konfigurace

### Proměnné prostředí (.env)

Konfigurace používá vrstvený mechanismus: konfigurační soubor JSON jako základ, proměnné prostředí přepisují jednotlivé hodnoty.

```bash
# === Povinné ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password        # musí být změněno

# === Výběr poskytovatele LLM ===
LLM_PROVIDER=ollama                 # ollama / glm / groq / openrouter / deepseek

# === Poskytovatel Embeddingu (volitelné, výchozí podle LLM_PROVIDER) ===
# Pouze glm používá GLM Embedding, ostatní vždy používají Ollama bge-m3
# EMBEDDING_PROVIDER=ollama         # ollama / glm

# === Konfigurace Ollama (použito při LLM_PROVIDER=ollama) ===
OLLAMA_MODEL=qwen2.5:3b             # hlavní model (doporučeno qwen2.5:3b)
OLLAMA_SMALL_MODEL=qwen2.5:3b       # malý model (pro jednoduché úlohy, lze zvolit jiný model)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.1

# === Konfigurace GLM (použito při LLM_PROVIDER=glm) ===
GLM_API_KEY=your_api_key            # získejte na https://open.bigmodel.cn
GLM_MODEL=glm-4-flash               # model zdarma
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768

# === Konfigurace GROQ (použito při LLM_PROVIDER=groq) ===
GROQ_API_KEY=your_api_key           # získejte na https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile

# === Konfigurace OpenRouter (použito při LLM_PROVIDER=openrouter) ===
OPENROUTER_API_KEY=your_api_key     # získejte na https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free

# === Konfigurace DeepSeek (použito při LLM_PROVIDER=deepseek) ===
DEEPSEEK_API_KEY=your_api_key       # získejte na https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash    # nebo deepseek-v4-pro

# === Model embeddingu Ollama (použito vždy, když embedding není glm) ===
OLLAMA_EMBEDDING_MODEL=bge-m3
OLLAMA_EMBEDDING_DIMENSIONS=768

# === Zobrazení a jazyk (volitelné) ===
GRAPHITI_DISPLAY_TIMEZONE=Asia/Taipei # časové pásmo zobrazení časových razítek vrácených API (IANA název; uložení zůstává v UTC)
SERVER_LANG=zh-TW                     # jazyk odpovědí MCP nástrojů (úplné locale viz src/i18n.py); REST API podle Accept-Language

# === Výkon paměti (volitelné) ===
GRAPHITI_CHUNK_THRESHOLD=800         # práh počtu znaků pro spuštění inteligentního dělení
GRAPHITI_MAX_CHUNK_SIZE=600          # maximální počet znaků na segment
GRAPHITI_MAX_COROUTINES=10            # maximální počet souběžných korutin
GRAPHITI_DEFAULT_BACKGROUND=false    # zda zpracovávat na pozadí ve výchozím nastavení
TASK_DB_PATH=data/tasks.db           # cesta k trvalému úložišti úloh na pozadí v SQLite

# === Sledování důležitosti a inteligentní zapomínání (volitelné) ===
ENABLE_IMPORTANCE_TRACKING=true      # zapnutí sledování přístupů
IMPORTANCE_WEIGHT=0.1                # váha důležitosti
STALE_DAYS_THRESHOLD=30              # práh počtu dní zastarání
STALE_MIN_ACCESS_COUNT=2             # minimální počet přístupů

# === Protokolování ===
LOG_FILE=logs/graphiti_mcp_server.log
LOG_LEVEL=INFO
```

> **Úplný seznam proměnných prostředí** najdete v `.env.example`

### Konfigurační soubor JSON

Vhodné pro konfiguraci, která vyžaduje verzování (proměnné prostředí stále mohou přepsat):

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

## Běh na pozadí přes PM2

```bash
npm install -g pm2

pm2 start ecosystem.config.cjs      # spuštění
pm2 status                           # stav
pm2 logs graphiti-mcp-http           # protokoly v reálném čase
pm2 restart graphiti-mcp-http --update-env  # restart (znovu načte .env)

pm2 save && pm2 startup              # nastavení automatického spuštění při startu
```

> **Tip**: Po úpravě `.env` je nutné restartovat s příznakem `--update-env`, jinak se proměnné prostředí neaktualizují.

## Nasazení Docker

```bash
docker build -t graphiti-mcp .

# Poznámka: Kontejner Docker se musí umět připojit k Neo4j a Ollama
# Použití host network je nejjednodušší
docker run -p 8000:8000 --env-file .env --network host graphiti-mcp

# Nebo explicitně zadejte adresy externích služeb
docker run -p 8000:8000 \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --env-file .env graphiti-mcp
```

## Testování

```bash
# Spuštění všech testů (203 testů, přibližně 1 sekunda)
uv run python -m pytest tests/

# Podrobný výstup
uv run python -m pytest tests/ -v

# Spuštění pouze konkrétního testu
uv run python -m pytest tests/test_content_preprocessor.py -v
uv run python -m pytest tests/test_new_features.py -v
uv run python -m pytest tests/test_unit.py -v
```

> **Poznámka**: 3 async testy v `test_integration_manual.py` vyžadují instalaci `pytest-asyncio`, při chybějícím zobrazí Failed, ale neovlivní ostatní testy. `bench_deepseek_flash_vs_pro.py` je skript pro benchmark výkonu, nikoli jednotkový test.

## Řešení potíží

### Selhání připojení Neo4j

```bash
neo4j status                              # kontrola stavu služby
cypher-shell -u neo4j -p your_password    # ověření správnosti hesla
curl http://localhost:7474                 # ověření HTTP portu
```

Časté příčiny:
- Neo4j není spuštěno
- Špatné heslo (`NEO4J_PASSWORD` v `.env`)
- Port je obsazen nebo blokován firewallem

### Selhání připojení LLM

**Režim Ollama:**
```bash
ollama serve                # spuštění služby Ollama
ollama list                 # kontrola nainstalovaných modelů
ollama pull qwen2.5:3b      # instalace chybějícího modelu
```

Časté příčiny: Ollama není spuštěna, model není nainstalován, nedostatek paměti GPU

**Režim GLM:**
- Ověřte správnost `GLM_API_KEY`
- Ověřte `GLM_EMBEDDING_DIMENSIONS=768` (musí odpovídat vektorovému indexu Neo4j)
- Koncový bod GLM API: `https://open.bigmodel.cn/api/paas/v4/`

**Režim GROQ:**
- Ověřte správnost `GROQ_API_KEY`
- Při častém Rate Limitu zvažte přepnutí na režim GLM
- GROQ neposkytuje Embedding, je potřeba zajistit dostupnost embedderu Ollama

**Režim OpenRouter:**
- Ověřte správnost `OPENROUTER_API_KEY`, `OPENROUTER_MODEL` je platné ID modelu (viz https://openrouter.ai/models)
- Neposkytuje Embedding, je potřeba zajistit dostupnost embedderu Ollama

**Režim DeepSeek:**
- Ověřte správnost `DEEPSEEK_API_KEY`
- Pokud se objeví `Prompt must contain the word 'json'`: jde o tvrdý požadavek režimu `json_object` DeepSeeku, klient má vestavěnou záložní ochranu; pokud se stále objevuje, ověřte, že používáte nejnovější verzi `src/deepseek_client.py`, a restartujte službu
- Neposkytuje Embedding, je potřeba zajistit dostupnost embedderu Ollama

### Chyba připojení MCP

Pokud se objeví `Invalid request parameters` nebo `Received request before initialization was complete`:

1. Ověřte použití transportního režimu HTTP (**nepoužívejte SSE**)
2. Ověřte nastavení klienta na `"type": "http"`, `"url": "http://localhost:8000/mcp"`
3. Restartujte službu: `pm2 restart graphiti-mcp-http --update-env`
4. V Claude Code spusťte `/mcp` pro opětovné připojení

### Pomalé přidávání paměti

- **Ollama**: zkontrolujte velikost modelu (`qwen2.5:3b` je 5–10krát rychlejší než `7b`), ověřte použití GPU (`ollama ps`)
- **GLM**: každý add_episode vyžaduje 10–20+ síťových obrátek LLM, ~22 s pro krátký text je normální hodnota
- **GROQ**: Rate Limit způsobí mnoho opakovaných pokusů, při častém použití doporučujeme přepnout na GLM nebo Ollama
- Použijte `background=true` pro zabránění blokování
- Snižte `GRAPHITI_CHUNK_THRESHOLD`, aby se dlouhý text dělil dříve

### Problémy s PM2

```bash
pm2 status                                        # kontrola stavu
pm2 logs graphiti-mcp-http --err --lines 50        # protokoly chyb
lsof -i :8000                                     # kontrola obsazení portu
pm2 delete graphiti-mcp-http && pm2 start ecosystem.config.cjs  # úplný restart
```

## Vývojářské diagnostické nástroje

```bash
uv run python tools/status_report.py           # souhrnná zpráva o stavu (Neo4j + Ollama + konfigurace)
uv run python tools/validate_config.py         # validace .env a úplnosti konfigurace
uv run python tools/performance_diagnose.py    # diagnostika výkonu LLM
uv run python tools/inspect_schema.py          # kontrola indexů a omezení Neo4j
uv run python tools/migrate_embeddings.py      # migrace modelu Embedding (znovu generuje vektory po změně modelu)
```

### Migrace modelu Embedding

Po změně modelu embeddingu (např. `nomic-embed-text` → `bge-m3`) lze pomocí migračního nástroje znovu vygenerovat všechny stávající vektory, aby byla zajištěna konzistentní kvalita vyhledávání:

```bash
# Náhled počtu k migraci
uv run python tools/migrate_embeddings.py --dry-run

# Úplná migrace (podpora pokračování z bodu přerušení)
uv run python tools/migrate_embeddings.py

# Migrace pouze určené group
uv run python tools/migrate_embeddings.py --group-id myproject

# Pokračování z bodu přerušení (opětovné spuštění po přerušení)
uv run python tools/migrate_embeddings.py --resume
```

> **Kompatibilita**: `bge-m3` má nativně 1024 dimenzí, systém automaticky ořezává na 768 dimenzí pro kompatibilitu se stávajícím vektorovým indexem Neo4j. Data před a po migraci mohou koexistovat, ale doporučuje se provést úplnou migraci pro nejlepší kvalitu vyhledávání.

## Dokumentace

- [Pokyny k používání nástrojů](../使用工具的指令.md) — průvodce používáním MCP nástrojů a osvědčené postupy
- [Graphiti Memory Rules](../graphiti-memory-rules.md) — popis pravidel paměti

## Licence

MIT License
