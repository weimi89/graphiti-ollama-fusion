# Graphiti MCP Server

Tudásgráf-alapú memóriaszolgáltatás — MCP-szerver, amely több LLM-szolgáltatót (Ollama / GLM / GROQ / OpenRouter / DeepSeek) integrál a Neo4j gráfadatbázissal.

A [getzep/graphiti](https://github.com/getzep/graphiti) alapján továbbfejlesztve, támogatja a helyi Ollama és a felhős LLM-ek közötti rugalmas váltást, valamint az Embedding-szolgáltató önálló megadását (az LLM-től függetlenül).

## Jellemzők

- **Intelligens memóriakezelés** — tudásgráf használata összetett memóriakapcsolatok tárolására és visszakeresésére
- **Szemantikai keresés** — vektorbeágyazáson alapuló hibrid keresés (vektor + kulcsszó + gráfbejárás)
- **16 keresési stratégia** — a haladó keresés támogatja az RRF, MMR, Cross-Encoder és egyéb újrarangsorolási módszereket
- **Több LLM-szolgáltató** — támogatja az Ollama (helyi), GLM (Zhipu AI, ingyenes), GROQ (nagy sebességű következtetés), OpenRouter (több szolgáltató modelljeit összesítő) és DeepSeek (Shenduqiusuo) szolgáltatókat, környezeti változóval egyetlen kapcsolóval váltható
- **Az Embedding és az LLM szétválasztása** — az `EMBEDDING_PROVIDER` változóval önállóan megadható a beágyazó, a felhős LLM automatikusan visszavált a helyi `bge-m3`-ra
- **Kétmodelles elosztás** — Ollama módban az összetett feladatok a fő modellt használják, az egyszerű feladatok automatikusan a kis modellre váltanak a teljesítmény javítása érdekében
- **Intelligens tartalomdarabolás** — a hosszú szövegek automatikusan szakaszokra bomlanak, csökkentve az LLM terhelését (a küszöb beállítható)
- **Háttérben futó memóriafeldolgozás** — a memóriahozzáadás futhat a háttérben, az MCP-hívás azonnal visszatér; a feladatállapot SQLite-ban perzisztálódik, újraindítás után a befejezetlen feladatok automatikusan visszaállnak
- **Memóriaduplikáció kiszűrése** — automatikusan felismeri a meglévő, nagyon hasonló memóriákat, elkerülve az ismétlődő tárolást
- **Konfliktusészlelés** — felismeri a két entitás közötti ellentmondó tényeket, megkülönböztetve az érvénytelenné vált és az érvényes információkat
- **Közösségfelismerés** — a Label Propagation algoritmus alapján automatikusan klaszterezi a kapcsolódó entitásokat
- **Fontosság követése** — automatikusan rögzíti az entitások hozzáférési gyakoriságát, a keresési eredmények fontosság szerint rendeződnek
- **Intelligens felejtés** — felismeri és eltávolítja az elavult, ritkán használt memóriákat, így a gráf tömör marad
- **Tömeges importálás** — egyszerre több memória beküldése, ideális nagy mennyiségű adat migrálásához
- **Strukturált hármasok** — közvetlen „alany-kapcsolat-tárgy" hozzáadás, az LLM-kinyerés kihagyásával, másodpercek alatt
- **Webes felügyeleti felület** — beépített műszerfal, böngészés, keresés, tudásgráf-vizualizáció, AI kérdés-válasz, közösségböngészés, minőségkarbantartás, tömeges importálás, futásidejű beállítások
- **Többnyelvűség (i18n)** — a válaszüzenetek 33 nyelvet támogatnak (köztük zh-TW / en / zh-CN / ja / pt-BR / ko / es / de / fr stb.; zh-TW/en/zh-CN/ja kézzel írva, a többi a generated rétegtől kapja); az MCP-eszközök a `SERVER_LANG` szerint, a REST API a HTTP `Accept-Language` szerint automatikusan egyeztet
- **Sötét/világos téma** — a webes felület támogatja a témaváltást
- **Biztonságos mód** — opcionálisan kihagyható az entitáskinyerés a gyors memóriahozzáadáshoz
- **Docker-támogatás** — beépített Dockerfile, konténeres telepítés támogatása
- **Konkurenciabiztonság** — az asyncio.Lock védi az inicializálást, megakadályozva a versengési helyzeteket
- **Rétegzett állapotellenőrzés** — `/health` (liveness) + `/health/ready` (readiness)

## Rendszerkövetelmények

| Tétel | Követelmény |
|------|------|
| Python | 3.10+ (ajánlott 3.11+) |
| Neo4j | 4.0+ (`bolt://localhost:7687`) |
| LLM-szolgáltató | Ollama / GLM / GROQ / OpenRouter / DeepSeek (ötből egy) |
| Node.js | 18+ (csak a PM2 háttérfuttatáshoz, opcionális) |
| Lemezterület | ~3 GB (Ollama-modellek + Neo4j-adatok) |

### LLM-szolgáltató kiválasztása

Az `LLM_PROVIDER` környezeti változóval váltható (`ollama` / `glm` / `groq` / `openrouter` / `deepseek`):

| Szolgáltató | Jellemzők | LLM-modell | Embedding | Alkalmas helyzet |
|--------|------|----------|-----------|----------|
| **Ollama** (alapértelmezett) | Teljesen helyi, az adatok nem hagyják el a gépet | `qwen2.5:3b` | `bge-m3` (kínai + RAG kiváló) | Van GPU, fontos az adatvédelem |
| **GLM** | Ingyenes felhő, stabil, korlát nélkül | `glm-4-flash` (ingyenes) | `embedding-3` | Nincs GPU, keresésintenzív helyzet |
| **GROQ** | Ultragyors következtetés | `llama-3.3-70b-versatile` | Visszaesés Ollama `bge-m3`-ra | Alkalmi írás, minőség-orientált |
| **OpenRouter** | Több szolgáltató modelljeit összesíti, ingyenes kerettel | `stepfun/step-3.5-flash:free` stb. | Visszaesés Ollama `bge-m3`-ra | Adott felhős modellt szeretne használni |
| **DeepSeek** | Shenduqiusuo felhő, jó ár-érték arány | `deepseek-v4-flash` / `deepseek-v4-pro` | Visszaesés Ollama `bge-m3`-ra | Kínai szövegértés, alacsony költségű felhő |

> **Az Embedding és az LLM szétválasztása**: a beágyazó az `EMBEDDING_PROVIDER` (`ollama` / `glm`) változóval önállóan megadható; ha nincs beállítva, az `LLM_PROVIDER`-t követi. Valójában csak a `glm` használja a GLM `embedding-3`-at, a többi (beleértve a GROQ / OpenRouter / DeepSeek és egyéb Embeddinget nem kínáló felhős LLM-eket is) mindig automatikusan az Ollama `bge-m3`-at használja. **Ezért bármilyen felhős LLM használatakor a beágyazási szolgáltatást a helyi Ollamának kell biztosítania (kivéve, ha az embedding is glm-re van állítva).**

#### Ollama mód (helyi)

```bash
# Fő LLM-modell (ajánlott a qwen2.5:3b, a sebesség és stabilitás legjobb egyensúlya)
ollama pull qwen2.5:3b

# Beágyazási modell (kötelező, vektoros kereséshez)
ollama pull bge-m3
```

> **Megjegyzések a modellválasztáshoz**:
> - `qwen2.5:3b` — ajánlott, ~2 s/hívás, ~100 t/s, a graphiti-core strukturált kimenet 100%-ig stabil
> - `qwen2.5:7b` — jobb eredmény, de 5-10-szer lassabb, minőség-orientált helyzetekhez
> - `qwen2.5:1.5b` — a leggyorsabb, de **instabil** (a strukturált JSON sikeraránya csak 33%), nem ajánlott

#### GLM mód (Zhipu AI felhő)

```bash
# .env beállítás
LLM_PROVIDER=glm
GLM_API_KEY=your_api_key          # beszerezve innen: https://open.bigmodel.cn
GLM_MODEL=glm-4-flash             # ingyenes modell
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768      # meg kell egyeznie a Neo4j vektorindex dimenziójával
```

> **GLM teljesítmény-referencia**: írás ~22 s (rövid szöveg), keresés ~0,34 s, nulla Rate Limit hiba, 2-5-ször lassabb a helyi Ollamánál, de teljesen ingyenes.

#### GROQ mód (nagy sebességű következtetés)

```bash
# .env beállítás
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key         # beszerezve innen: https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile
```

> **Megjegyzés**: a GROQ nem kínál Embedding szolgáltatást, ezért az Ollama beágyazóval kell párosítani (automatikus visszaesés), vagy az `EMBEDDING_PROVIDER`-t glm-re kell állítani. A GROQ-nak szigorú Rate Limitje van, a gyakori használat sok újrapróbálkozást vált ki.

#### OpenRouter mód (több szolgáltató modelljeit összesíti)

```bash
# .env beállítás
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_api_key       # beszerezve innen: https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free   # bármely OpenRouter-modellre módosítható
```

> **Megjegyzés**: az OpenRouter nem kínál Embeddinget, automatikusan visszaesik az Ollama `bge-m3`-ra. A modellek listája itt található: https://openrouter.ai/models (több `:free` ingyenes modellel).

#### DeepSeek mód (Shenduqiusuo)

```bash
# .env beállítás
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key         # beszerezve innen: https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash      # ajánlott; vagy deepseek-v4-pro (jobb eredmény)
```

> **Megjegyzés**: a DeepSeek nem kínál Embeddinget, automatikusan visszaesik az Ollama `bge-m3`-ra. A `deepseek-chat` / `deepseek-reasoner` 2026-07-24-én megszűnik, ajánlott a `deepseek-v4-flash` / `deepseek-v4-pro` használatára váltani. A DeepSeek szigorúan megköveteli, hogy a `json_object` mód promptja tartalmazza a "json" sztringet; a kliensbe beépített biztonsági védelem van, nincs szükség további beállításra.

## Gyors indítás

### 1. Előkészületek

Győződjön meg róla, hogy a Neo4j fut a helyi gépen, és a kiválasztott LLM-szolgáltatónak megfelelően készítse elő a megfelelő szolgáltatást:

```bash
# Győződjön meg róla, hogy a Neo4j fut (kötelező)
neo4j status
# Vagy Dockerrel: docker run -d -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/your_password neo4j:latest

# Ollama mód: győződjön meg róla, hogy az Ollama fut
ollama list
# Ha nem indult el: ollama serve

# GLM / GROQ mód: csak egy érvényes API Key szükséges, nincs szükség helyi szolgáltatásra
```

### 2. Függőségek telepítése

```bash
git clone <repo-url>
cd graphiti
uv sync
```

> **Megjegyzés**: ez a projekt az [uv](https://github.com/astral-sh/uv) eszközt használja a függőségek kezelésére. Ha nincs telepítve: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 3. Környezet konfigurálása

```bash
cp .env.example .env
```

Szerkessze az `.env` fájlt, **legalább** a következő tételeket kell módosítania:

```bash
NEO4J_PASSWORD=your_actual_password  # kötelező: Neo4j jelszó
LLM_PROVIDER=ollama                  # ollama / glm / groq / openrouter / deepseek
OLLAMA_MODEL=qwen2.5:3b              # Ollama mód: helyi LLM-modell
# GLM_API_KEY=your_key               # GLM mód: Zhipu AI API Key
# GROQ_API_KEY=your_key              # GROQ mód: GROQ API Key
# OPENROUTER_API_KEY=your_key        # OpenRouter mód: API Key
# DEEPSEEK_API_KEY=your_key          # DeepSeek mód: API Key
```

### 4. Szolgáltatás indítása

```bash
# HTTP mód (ajánlott, tartalmazza a webes felügyeleti felületet)
uv run python graphiti_mcp_server.py --transport http --port 8000

# Vagy PM2 háttérfuttatás (ajánlott hosszú távú futtatáshoz)
pm2 start ecosystem.config.cjs
```

### 5. Szolgáltatás ellenőrzése

Indítás után a következő végpontok érhetők el:

| Végpont | Leírás |
|------|------|
| http://localhost:8000/ | Webes felügyeleti felület |
| http://localhost:8000/mcp | MCP-végpont (MCP-kliensek csatlakozásához) |
| http://localhost:8000/health | Állapotellenőrzés (liveness) |
| http://localhost:8000/health/ready | Mélyebb ellenőrzés (Neo4j-kapcsolattal együtt) |
| http://localhost:8000/api/stats | REST API statisztikák |

## Projektstruktúra

```
graphiti/
├── graphiti_mcp_server.py        # Fő belépési pont — MCP-eszközdefiníciók (19 eszköz)
├── src/
│   ├── config.py                 # Konfigurációkezelés (GraphitiConfig, JSON/.env rétegezést támogat)
│   ├── web_api.py                # Webes felügyeleti felület REST API (30+ végpont)
│   ├── ollama_graphiti_client.py  # Ollama LLM-kliens (kétmodelles elosztás)
│   ├── openai_compat_client.py   # OpenAI-kompatibilis LLM alap (json_object + egyszerűsített schema + json biztonsági védelem)
│   ├── glm_client.py             # GLM (Zhipu AI) LLM-kliens (OpenAICompatClient leszármazottja)
│   ├── openrouter_client.py      # OpenRouter LLM-kliens (OpenAICompatClient leszármazottja)
│   ├── deepseek_client.py        # DeepSeek LLM-kliens (OpenAICompatClient leszármazottja)
│   ├── ollama_embedder.py        # Ollama beágyazási modell adapter
│   ├── content_preprocessor.py   # Intelligens tartalomdarabolás (hosszú szöveg automatikus szakaszolása)
│   ├── deduplication.py          # Memóriaduplikáció kiszűrése (koszinusz-hasonlóság összevetése)
│   ├── importance.py             # Fontosság követése és intelligens felejtés
│   ├── safe_memory_add.py        # Biztonságos memóriahozzáadás (entitáskinyerés kihagyása)
│   ├── task_store.py             # Háttérfeladatok SQLite-perzisztenciája (TaskStore)
│   ├── timezone_utils.py         # Időzóna-átalakítás (UTC→helyi időzóna megjelenítése)
│   ├── i18n.py                   # Backend többnyelvűség (REST az Accept-Language, MCP a SERVER_LANG szerint)
│   ├── i18n_generated.py         # Automatikusan generált nyelvi felülírások (GENERATED_MESSAGE_OVERRIDES)
│   ├── exceptions.py             # Strukturált kivételkezelés (12 kivételkategória)
│   └── logging_setup.py          # Naplózási rendszer (időalapú rotáció + teljesítményfigyelés)
├── web/                          # Webes felügyeleti felület frontend (SPA, build nélkül)
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js                # REST API csomagolás
│       ├── components.js         # UI-komponensek renderelése (a közösségoldallal együtt)
│       └── app.js                # SPA-útválasztás, állapotkezelés
├── tests/                        # Tesztcsomag (203 teszt)
│   ├── test_content_preprocessor.py  # Darabolási logika tesztje (17 db)
│   ├── test_new_features.py      # Új funkciók tesztje (32 db)
│   ├── test_i18n.py             # Többnyelvűségi teszt (57 db)
│   ├── test_unit.py              # Egységtesztek
│   ├── test_web_api.py           # Web API tesztek
│   ├── test_web_ui_features.py   # Web UI funkciótesztek
│   ├── test_integration_manual.py # Kézi integrációs teszt
│   └── bench_deepseek_flash_vs_pro.py # DeepSeek flash/pro teljesítmény-benchmark szkript
├── tools/                        # Fejlesztői diagnosztikai eszközök
│   ├── status_report.py          # Összesített állapotjelentés
│   ├── validate_config.py        # Konfigurációvalidálás
│   ├── performance_diagnose.py   # Teljesítménydiagnosztika
│   ├── inspect_schema.py         # Neo4j struktúraellenőrzés
│   ├── batch_reprocess.py        # Kötegelt újrafeldolgozás
│   └── migrate_embeddings.py     # Embedding-modell migrálása
├── docs/                         # Dokumentáció
├── logs/                         # Naplók (időalapú rotáció, alapértelmezetten 30 napig megőrzött)
├── Dockerfile                    # Docker konténeres telepítés
└── ecosystem.config.cjs          # PM2 konfiguráció
```

## MCP-kliens beállítása

### HTTP mód (ajánlott)

Olyan MCP-kliensekhez, amelyek támogatják a HTTP-t, mint a Claude Code, Cline stb.:

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

### STDIO mód

Olyan kliensekhez, amelyeknek közvetlenül kell elindítaniuk a folyamatot, mint a Claude Desktop:

**Konfigurációs fájl helye:**
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

> **Megjegyzés**: az SSE mód (`--transport sse`) használata már nem ajánlott. Az MCP 1.x-ben a session-inicializálással kapcsolatos kompatibilitási problémák vannak, kérjük, használja helyette a HTTP módot.

## MCP-eszközök (19 db)

### Memóriakezelés (7 db)

| Eszköz | Leírás |
|------|------|
| `add_memory_simple` | Memória hozzáadása a tudásgráfhoz (támogatja a háttérfeldolgozást, intelligens darabolást, duplikációellenőrzést) |
| `add_episode_bulk` | Több memória tömeges hozzáadása (alapértelmezetten háttérfeldolgozás) |
| `add_triplet` | Strukturált hármas hozzáadása (az LLM kihagyásával, másodpercek alatt) |
| `search_memory_nodes` | Memóriacsomópontok keresése (16 keresési stratégiát és időszűrést támogat) |
| `search_memory_facts` | Memóriatények keresése (kapcsolattípus-szűrést, időtartományt, érvényességi szűrést támogat) |
| `advanced_search` | Haladó keresés (16 stratégia, csomópontok+élek+közösségek+epizódok visszaadása) |
| `get_episodes` | A legutóbbi memóriaepizódok lekérése |

### Tudáselemzés (3 db)

| Eszköz | Leírás |
|------|------|
| `check_conflicts` | Két entitás közötti ténykonfliktusok észlelése (érvényes vs. érvénytelenné vált) |
| `get_node_edges` | Csomópont bejövő és kimenő éleinek feltárása |
| `build_communities` | Közösségfelismerés és klaszterezés indítása (alapértelmezetten háttérfeldolgozás) |

### Memóriakarbantartás (2 db)

| Eszköz | Leírás |
|------|------|
| `get_stale_memories` | Elavult, ritkán használt memóriák lekérdezése |
| `cleanup_stale_memories` | Elavult memóriák tisztítása (alapértelmezetten dry_run előnézeti mód) |

### Feladatkezelés

| Eszköz | Leírás |
|------|------|
| `get_memory_task_status` | Háttérben futó memóriafeldolgozási feladat előrehaladásának és eredményének lekérdezése |

### Törlés és lekérdezés

| Eszköz | Leírás |
|------|------|
| `delete_episode` | Memóriaepizód törlése |
| `delete_entity_edge` | Entitásél (kapcsolat) törlése |
| `get_entity_edge` | Entitásél részletes adatainak lekérése |

### Rendszerkezelés

| Eszköz | Leírás |
|------|------|
| `get_status` | Szolgáltatás állapotának lekérése (Neo4j, LLM, beágyazó) |
| `test_connection` | Neo4j / LLM / beágyazó kapcsolat tesztelése |
| `clear_graph` | Gráfadatbázis tisztítása (group_id szerinti tisztítást támogat) |

## Eszközparaméterek

### add_memory_simple

| Paraméter | Típus | Kötelező | Alapérték | Leírás |
|------|------|------|--------|------|
| `name` | string | Y | | Memória neve |
| `episode_body` | string | Y | | Memória tartalma (800 karakter felett automatikus darabolás) |
| `group_id` | string | | `"default"` | Csoport-azonosító (ajánlott projektenként elkülöníteni) |
| `source` | string | | `"text"` | Forrástípus: `text` / `json` / `message` |
| `source_description` | string | | `"MCP Server"` | Forrásleírás |
| `use_safe_mode` | bool | | `false` | Biztonságos mód (entitáskinyerés kihagyása, gyors, de a memória nem kereshető) |
| `background` | bool | | `false` | Háttérfeldolgozás (azonnal visszaadja a task_id-t, hosszú szöveghez ajánlott) |
| `force` | bool | | `false` | Duplikációellenőrzés kihagyása (kényszerített hozzáadás) |
| `excluded_entity_types` | list | | | Kizárt entitástípusok (a felesleges kinyerés mennyiségének csökkentése) |

> **Teljesítménytippek**:
> - Rövid szöveg (<800 karakter): közvetlen feldolgozás, általában 30-40 másodperc alatt kész
> - Hosszú szöveg (>800 karakter): automatikusan több szakaszra bomlik, az `add_episode_bulk` segítségével konkurens feldolgozás (~33%-kal gyorsabb a soros feldolgozásnál)
> - A `background=true` használata elkerüli az MCP-hívás blokkolását, az előrehaladás a `get_memory_task_status` segítségével követhető
> - A `use_safe_mode=true` másodpercek alatt elkészül, de a memória nem található meg a search eszközökkel
> - A duplikáció kiszűrésének engedélyezésekor a nagyon hasonló memóriáknál figyelmeztetés jelenik meg (a `force=true` átugorható)

### add_episode_bulk

| Paraméter | Típus | Kötelező | Alapérték | Leírás |
|------|------|------|--------|------|
| `episodes` | list | Y | | Memórialista, minden elem tartalmaz egy `name` és egy `content` mezőt |
| `group_id` | string | | `"default"` | Csoport-azonosító |
| `source` | string | | `"text"` | Forrástípus |
| `background` | bool | | `true` | Háttérfeldolgozás (a tömeges feldolgozás általában időigényes) |

### add_triplet

| Paraméter | Típus | Kötelező | Alapérték | Leírás |
|------|------|------|--------|------|
| `source_name` | string | Y | | Forrásentitás neve (pl. "Alice") |
| `target_name` | string | Y | | Célentitás neve (pl. "Google") |
| `relation_name` | string | Y | | Kapcsolat neve (pl. "works_at") |
| `fact` | string | Y | | Ténymegfogalmazás (pl. "Alice works at Google") |
| `group_id` | string | | `"default"` | Csoport-azonosító |
| `source_labels` | list | | | Forrásentitás címkéi |
| `target_labels` | list | | | Célentitás címkéi |

### search_memory_nodes

| Paraméter | Típus | Kötelező | Alapérték | Leírás |
|------|------|------|--------|------|
| `query` | string | Y | | Keresési kulcsszó (természetes nyelv) |
| `max_nodes` | int | | `10` | Visszaadott elemek maximális száma |
| `group_ids` | list | | | Csoportszűrés (több csoport együttes keresése) |
| `entity_types` | list | | | Entitástípus-szűrés |
| `search_recipe` | string | | | Keresési stratégia (lásd haladó keresés) |
| `created_after` | string | | | Létrehozási idő alsó határa (ISO datetime) |
| `created_before` | string | | | Létrehozási idő felső határa (ISO datetime) |

### search_memory_facts

| Paraméter | Típus | Kötelező | Alapérték | Leírás |
|------|------|------|--------|------|
| `query` | string | Y | | Keresési kulcsszó |
| `max_facts` | int | | `10` | Visszaadott elemek maximális száma |
| `group_ids` | list | | | Csoportszűrés |
| `center_node_uuid` | string | | | Központi csomópont UUID-ja (adott csomópont kapcsolatainak feltárása) |
| `edge_types` | list | | | Kapcsolattípus-szűrés (pl. `["works_at"]`) |
| `created_after` | string | | | Létrehozási idő alsó határa (ISO datetime) |
| `created_before` | string | | | Létrehozási idő felső határa (ISO datetime) |
| `only_valid` | bool | | `false` | Csak az érvénytelenné nem vált tényeket adja vissza |

### advanced_search

| Paraméter | Típus | Kötelező | Alapérték | Leírás |
|------|------|------|--------|------|
| `query` | string | Y | | Keresési kulcsszó |
| `search_recipe` | string | | `"combined_rrf"` | Keresési stratégia (16 választható) |
| `max_results` | int | | `10` | Visszaadott elemek maximális száma |
| `group_ids` | list | | | Csoportszűrés |
| `center_node_uuid` | string | | | Központi csomópont UUID-ja |

**Elérhető keresési stratégiák (search_recipe):**

| Kategória | Stratégia | Leírás |
|------|------|------|
| Összevont | `combined_rrf` | Összevont RRF-fúzió (alapértelmezett, ajánlott) |
| Összevont | `combined_mmr` | Összevont MMR diverzitás-újrarangsorolás |
| Összevont | `combined_cross_encoder` | Összevont Cross-Encoder finomrangsorolás |
| Él | `edge_rrf` / `edge_mmr` / `edge_cross_encoder` | Élkeresés (3 rangsorolás) |
| Él | `edge_node_distance` / `edge_episode_mentions` | Élkeresés (gráftávolság/hivatkozások száma) |
| Csomópont | `node_rrf` / `node_mmr` / `node_cross_encoder` | Csomópontkeresés (3 rangsorolás) |
| Csomópont | `node_node_distance` / `node_episode_mentions` | Csomópontkeresés (gráftávolság/hivatkozások száma) |
| Közösség | `community_rrf` / `community_mmr` / `community_cross_encoder` | Közösségkeresés |

### check_conflicts

| Paraméter | Típus | Kötelező | Alapérték | Leírás |
|------|------|------|--------|------|
| `source_name` | string | Y | | Forrásentitás neve |
| `target_name` | string | Y | | Célentitás neve |
| `group_id` | string | | `"default"` | Csoport-azonosító |

### get_node_edges

| Paraméter | Típus | Kötelező | Alapérték | Leírás |
|------|------|------|--------|------|
| `node_uuid` | string | Y | | Csomópont UUID-ja |
| `include_inbound` | bool | | `true` | Bejövő élek belefoglalása |
| `include_outbound` | bool | | `true` | Kimenő élek belefoglalása |
| `max_edges` | int | | `50` | Visszaadott elemek maximális száma |

### build_communities

| Paraméter | Típus | Kötelező | Alapérték | Leírás |
|------|------|------|--------|------|
| `group_ids` | list | | | Megadott csoportok (üresen hagyva mind) |
| `background` | bool | | `true` | Háttérfeldolgozás |

### get_stale_memories

| Paraméter | Típus | Kötelező | Alapérték | Leírás |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Hány nap hozzáférés-hiány után tekinthető elavultnak |
| `min_access_count` | int | | `2` | Csak az e értéknél kevesebbszer elért elemek kerülnek be |
| `group_id` | string | | | Csoportszűrés |
| `limit` | int | | `50` | Visszaadott elemek maximális száma |

### cleanup_stale_memories

| Paraméter | Típus | Kötelező | Alapérték | Leírás |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Elavultsági napküszöb |
| `min_access_count` | int | | `2` | Minimális hozzáférés-szám küszöb |
| `group_id` | string | | | Csoportszűrés |
| `dry_run` | bool | | `true` | Előnézeti mód (nem töröl ténylegesen) |
| `limit` | int | | `50` | Feldolgozott elemek maximális száma |

### get_memory_task_status

| Paraméter | Típus | Kötelező | Leírás |
|------|------|------|------|
| `task_id` | string | Y | Háttérfeladat azonosítója (az `add_memory_simple(background=true)` adja vissza) |

## Webes felügyeleti felület

HTTP módban a `http://localhost:8000/` címen érhető el.

**Funkciók:**
- Műszerfal — csomópontok, tények, memóriaepizódok számának statisztikája
- Entitáscsomópontok — böngészés, szűrés, vektoros keresés
- Ténykapcsolatok — böngészés, szűrés, vektoros keresés
- Memóriaepizódok — böngészés, teljes szöveges keresés, törlés
- Közösségböngészés — közösségcsomópontok listája, összefoglalók, közösségépítés indítása
- Hármas-űrlap — „alany-kapcsolat-tárgy" strukturált tudás közvetlen hozzáadása
- Csoportkezelés — szűrés csoport szerint, kötegelt törlés
- Tudásgráf-vizualizáció — csomópontkapcsolatok grafikus megjelenítése
- AI kérdés-válasz — tudásgráfon alapuló intelligens kérdés-válasz
- Minőségkarbantartás — memória minőségi mutatói és tisztítóeszközök
- Tömeges importálás — több memóriaepizód egyszerre történő importálása (JSON, egyszeri limit: 500 db)
- Futásidejű beállítások — az aktuálisan érvényes beállítások megtekintése, egyes paraméterek újraindítás nélkül módosíthatók
- Témaváltás — sötét/világos téma

**REST API:**

| Végpont | Metódus | Leírás |
|------|------|------|
| `/api/stats` | GET | Műszerfal-statisztikák |
| `/api/groups` | GET | Az összes group_id lekérése |
| `/api/groups/stats` | GET | Csoportonkénti csomópont/tény/epizód statisztikák |
| `/api/nodes` | GET | Entitáscsomópontok böngészése (lapozással) |
| `/api/facts` | GET | Tények böngészése (lapozással) |
| `/api/episodes` | GET | Memóriaepizódok böngészése (lapozással) |
| `/api/nodes/{uuid}/relations` | GET | Csomópont bejövő/kimenő éleinek lekérése |
| `/api/search/nodes` | GET | Csomópontok vektoros keresése |
| `/api/search/facts` | GET | Tények vektoros keresése |
| `/api/search/episodes` | GET | Memóriaepizódok keresése |
| `/api/search/advanced` | GET | Haladó keresés (16 stratégia) |
| `/api/communities` | GET | Közösségcsomópontok böngészése (lapozással) |
| `/api/communities/build` | POST | Közösségépítés indítása |
| `/api/memory/add` | POST | Egyetlen memória hozzáadása |
| `/api/memory/add-bulk` | POST | Memóriák tömeges hozzáadása |
| `/api/memory/add-triplet` | POST | Hármas hozzáadása |
| `/api/import/episodes` | POST | Memóriaepizódok tömeges importálása (JSON, egyszeri limit: 500 db) |
| `/api/memory/tasks` | GET | Háttérfeladatok listázása (állapotszűrést támogat) |
| `/api/memory/tasks/{id}` | GET | Egyetlen feladat állapotának lekérdezése |
| `/api/timeline` | GET | Idővonal-böngészés |
| `/api/graph/subgraph` | GET | Részgráf lekérése (vizualizációhoz) |
| `/api/graph/all` | GET | Teljes gráf lekérése (vizualizációhoz) |
| `/api/ask` | GET | AI kérdés-válasz (gráfalapú lekérés) |
| `/api/analytics/top-nodes` | GET | Magas csatlakozottságú/hozzáférésű csomópontok |
| `/api/analytics/quality` | GET | Tudásgráf minőségi mutatói |
| `/api/analytics/stale` | GET | Elavult memóriák lekérdezése |
| `/api/analytics/cleanup` | POST | Elavult memóriák tisztítása |
| `/api/config` | GET | Az aktuálisan érvényes beállítások lekérése (API-kulcs nélkül) |
| `/api/config` | PATCH | Futásidejű beállításfrissítés (csak az aktuális folyamatra érvényes, újraindításkor visszaáll) |
| `/api/nodes/{uuid}` | DELETE | Csomópont törlése |
| `/api/episodes/{uuid}` | DELETE | Memóriaepizód törlése |
| `/api/facts/{uuid}` | DELETE | Tény törlése |
| `/api/groups/{group_id}` | DELETE | Teljes csoport törlése |

## Konfiguráció

### Környezeti változók (.env)

A konfiguráció rétegezett mechanizmust használ: a JSON konfigurációs fájl az alap, a környezeti változók felülírják az egyes értékeket.

```bash
# === Kötelező ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password        # módosítani kell

# === LLM-szolgáltató kiválasztása ===
LLM_PROVIDER=ollama                 # ollama / glm / groq / openrouter / deepseek

# === Embedding-szolgáltató (opcionális, alapértelmezetten az LLM_PROVIDER-t követi) ===
# Csak a glm használ GLM Embeddinget, a többi mindig az Ollama bge-m3-at
# EMBEDDING_PROVIDER=ollama         # ollama / glm

# === Ollama konfiguráció (LLM_PROVIDER=ollama esetén használatos) ===
OLLAMA_MODEL=qwen2.5:3b             # Fő modell (ajánlott a qwen2.5:3b)
OLLAMA_SMALL_MODEL=qwen2.5:3b       # Kis modell (egyszerű feladatokhoz, más modell is választható)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.1

# === GLM konfiguráció (LLM_PROVIDER=glm esetén használatos) ===
GLM_API_KEY=your_api_key            # beszerezve innen: https://open.bigmodel.cn
GLM_MODEL=glm-4-flash               # ingyenes modell
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768

# === GROQ konfiguráció (LLM_PROVIDER=groq esetén használatos) ===
GROQ_API_KEY=your_api_key           # beszerezve innen: https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile

# === OpenRouter konfiguráció (LLM_PROVIDER=openrouter esetén használatos) ===
OPENROUTER_API_KEY=your_api_key     # beszerezve innen: https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free

# === DeepSeek konfiguráció (LLM_PROVIDER=deepseek esetén használatos) ===
DEEPSEEK_API_KEY=your_api_key       # beszerezve innen: https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash    # vagy deepseek-v4-pro

# === Ollama beágyazási modell (nem glm beágyazás esetén mindig használatos) ===
OLLAMA_EMBEDDING_MODEL=bge-m3
OLLAMA_EMBEDDING_DIMENSIONS=768

# === Megjelenítés és nyelv (opcionális) ===
GRAPHITI_DISPLAY_TIMEZONE=Asia/Taipei # Az API által visszaadott időbélyeg megjelenítési időzónája (IANA-név; a tárolás UTC marad)
SERVER_LANG=zh-TW                     # Az MCP-eszközök válaszának nyelve (a teljes locale-lista a src/i18n.py-ben); a REST API az Accept-Language szerint

# === Memória-teljesítmény (opcionális) ===
GRAPHITI_CHUNK_THRESHOLD=800         # Az intelligens darabolást kiváltó karakterszám-küszöb
GRAPHITI_MAX_CHUNK_SIZE=600          # Szakaszonkénti maximális karakterszám
GRAPHITI_MAX_COROUTINES=10            # Konkurens korutinok maximális száma
GRAPHITI_DEFAULT_BACKGROUND=false    # Alapértelmezett-e a háttérfeldolgozás
TASK_DB_PATH=data/tasks.db           # Háttérfeladatok SQLite-perzisztenciájának elérési útja

# === Fontosság követése és intelligens felejtés (opcionális) ===
ENABLE_IMPORTANCE_TRACKING=true      # Hozzáférés-követés engedélyezése
IMPORTANCE_WEIGHT=0.1                # Fontosság súlya
STALE_DAYS_THRESHOLD=30              # Elavultsági napküszöb
STALE_MIN_ACCESS_COUNT=2             # Minimális hozzáférés-szám

# === Naplózás ===
LOG_FILE=logs/graphiti_mcp_server.log
LOG_LEVEL=INFO
```

> **A környezeti változók teljes listáját** lásd az `.env.example` fájlban

### JSON konfigurációs fájl

Olyan konfigurációhoz, amelyet verziókezelni kell (a környezeti változók továbbra is felülírhatják):

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

## PM2 háttérfuttatás

```bash
npm install -g pm2

pm2 start ecosystem.config.cjs      # indítás
pm2 status                           # állapot
pm2 logs graphiti-mcp-http           # valós idejű naplók
pm2 restart graphiti-mcp-http --update-env  # újraindítás (.env újratöltése)

pm2 save && pm2 startup              # automatikus indítás beállítása rendszerindításkor
```

> **Tipp**: az `.env` módosítása után kötelezően a `--update-env` jelzővel kell újraindítani, különben a környezeti változók nem frissülnek.

## Docker-telepítés

```bash
docker build -t graphiti-mcp .

# Megjegyzés: a Docker-konténernek képesnek kell lennie csatlakozni a Neo4j-hez és az Ollamához
# A host network használata a legegyszerűbb
docker run -p 8000:8000 --env-file .env --network host graphiti-mcp

# Vagy explicit módon adja meg a külső szolgáltatások címét
docker run -p 8000:8000 \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --env-file .env graphiti-mcp
```

## Tesztelés

```bash
# Az összes teszt futtatása (203 db, kb. 1 másodperc)
uv run python -m pytest tests/

# Részletes kimenet
uv run python -m pytest tests/ -v

# Csak adott teszt futtatása
uv run python -m pytest tests/test_content_preprocessor.py -v
uv run python -m pytest tests/test_new_features.py -v
uv run python -m pytest tests/test_unit.py -v
```

> **Megjegyzés**: a `test_integration_manual.py` 3 async tesztjéhez telepíteni kell a `pytest-asyncio`-t; ennek hiányában Failed jelenik meg, de ez nem befolyásolja a többi tesztet. A `bench_deepseek_flash_vs_pro.py` egy teljesítmény-benchmark szkript, nem egységteszt.

## Hibaelhárítás

### Neo4j-kapcsolat sikertelen

```bash
neo4j status                              # szolgáltatás állapotának ellenőrzése
cypher-shell -u neo4j -p your_password    # a jelszó helyességének ellenőrzése
curl http://localhost:7474                 # a HTTP-port ellenőrzése
```

Gyakori okok:
- A Neo4j nem indult el
- Hibás jelszó (az `.env`-ben lévő `NEO4J_PASSWORD`)
- A port foglalt, vagy a tűzfal blokkolja

### LLM-kapcsolat sikertelen

**Ollama mód:**
```bash
ollama serve                # Ollama-szolgáltatás indítása
ollama list                 # telepített modellek ellenőrzése
ollama pull qwen2.5:3b      # hiányzó modell telepítése
```

Gyakori okok: az Ollama nem indult el, a modell nincs telepítve, a GPU memóriája nem elegendő

**GLM mód:**
- Ellenőrizze, hogy a `GLM_API_KEY` helyes-e
- Ellenőrizze, hogy a `GLM_EMBEDDING_DIMENSIONS=768` (meg kell egyeznie a Neo4j vektorindexszel)
- GLM API-végpont: `https://open.bigmodel.cn/api/paas/v4/`

**GROQ mód:**
- Ellenőrizze, hogy a `GROQ_API_KEY` helyes-e
- Gyakori Rate Limit esetén fontolja meg a GLM módra váltást
- A GROQ nem kínál Embeddinget, biztosítani kell, hogy az Ollama beágyazó elérhető legyen

**OpenRouter mód:**
- Ellenőrizze, hogy az `OPENROUTER_API_KEY` helyes-e, és az `OPENROUTER_MODEL` érvényes modellazonosító-e (lásd https://openrouter.ai/models)
- Nem kínál Embeddinget, biztosítani kell, hogy az Ollama beágyazó elérhető legyen

**DeepSeek mód:**
- Ellenőrizze, hogy a `DEEPSEEK_API_KEY` helyes-e
- Ha megjelenik a `Prompt must contain the word 'json'`: ez a DeepSeek `json_object` módjának kötelező követelménye, a kliensbe beépített biztonsági védelem van; ha mégis megjelenik, ellenőrizze, hogy a legújabb verziójú `src/deepseek_client.py`-t használja, és indítsa újra a szolgáltatást
- Nem kínál Embeddinget, biztosítani kell, hogy az Ollama beágyazó elérhető legyen

### MCP-kapcsolati hiba

Ha megjelenik az `Invalid request parameters` vagy a `Received request before initialization was complete`:

1. Ellenőrizze, hogy a HTTP-átviteli módot használja (**ne használjon SSE-t**)
2. Ellenőrizze, hogy a kliens `"type": "http"`, `"url": "http://localhost:8000/mcp"` értékre van állítva
3. Indítsa újra a szolgáltatást: `pm2 restart graphiti-mcp-http --update-env`
4. A Claude Code-ban futtassa a `/mcp` parancsot az újracsatlakozáshoz

### A memóriahozzáadás lassú

- **Ollama**: ellenőrizze a modell méretét (a `qwen2.5:3b` 5-10-szer gyorsabb a `7b`-nél), győződjön meg róla, hogy GPU-t használ (`ollama ps`)
- **GLM**: minden add_episode 10-20+ LLM-hálózati oda-vissza fordulót igényel, rövid szövegnél a ~22 s normális érték
- **GROQ**: a Rate Limit sok újrapróbálkozást okoz, gyakori használat esetén ajánlott a GLM-re vagy Ollamára váltani
- A `background=true` használata elkerüli a blokkolást
- Csökkentse a `GRAPHITI_CHUNK_THRESHOLD` értékét, hogy a hosszú szöveg korábban daraboljon

### PM2-problémák

```bash
pm2 status                                        # állapot ellenőrzése
pm2 logs graphiti-mcp-http --err --lines 50        # hibanaplók
lsof -i :8000                                     # portfoglaltság ellenőrzése
pm2 delete graphiti-mcp-http && pm2 start ecosystem.config.cjs  # teljes újraindítás
```

## Fejlesztői diagnosztikai eszközök

```bash
uv run python tools/status_report.py           # Összesített állapotjelentés (Neo4j + Ollama + konfiguráció)
uv run python tools/validate_config.py         # Az .env és a konfiguráció teljességének validálása
uv run python tools/performance_diagnose.py    # LLM-teljesítménydiagnosztika
uv run python tools/inspect_schema.py          # Neo4j-indexek és -megszorítások ellenőrzése
uv run python tools/migrate_embeddings.py      # Embedding-modell migrálása (a modellváltás után a vektorok újragenerálása)
```

### Embedding-modell migrálása

Az embedding-modell váltása után (pl. `nomic-embed-text` → `bge-m3`) a migrálóeszközzel az összes meglévő vektor újragenerálható, biztosítva a keresési minőség egységességét:

```bash
# A migrálandó mennyiség előnézete
uv run python tools/migrate_embeddings.py --dry-run

# Teljes migrálás (megszakítás-folytatást támogat)
uv run python tools/migrate_embeddings.py

# Csak adott csoport migrálása
uv run python tools/migrate_embeddings.py --group-id myproject

# Folytatás megszakítási pontról (megszakítás utáni újrafuttatás)
uv run python tools/migrate_embeddings.py --resume
```

> **Kompatibilitás**: a `bge-m3` natívan 1024 dimenziós, a rendszer automatikusan 768 dimenzióra csonkolja a meglévő Neo4j vektorindexszel való kompatibilitás érdekében. A migrálás előtti és utáni adatok együtt létezhetnek, de a legjobb keresési minőség érdekében ajánlott a teljes migrálás végrehajtása.

## Dokumentáció

- [Az eszközhasználat utasításai](../使用工具的指令.md) — MCP-eszközhasználati útmutató és bevált gyakorlatok
- [Graphiti Memory Rules](../graphiti-memory-rules.md) — Memóriaszabályok leírása

## Licenc

MIT License
