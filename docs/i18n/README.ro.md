# Graphiti MCP Server

Serviciu de memorie cu graf de cunoștințe — un server MCP care integrează mai mulți furnizori LLM (Ollama / GLM / GROQ / OpenRouter / DeepSeek) cu baza de date orientată pe graf Neo4j.

Dezvoltat ca extensie a [getzep/graphiti](https://github.com/getzep/graphiti), suportă comutarea flexibilă între Ollama local și LLM-uri din cloud, și permite specificarea independentă a furnizorului de Embedding (decuplat de LLM).

## Funcționalități remarcabile

- **Gestionare inteligentă a memoriei** — folosește graful de cunoștințe pentru a stoca și a regăsi relații complexe de memorie
- **Căutare semantică** — căutare hibridă bazată pe încorporări vectoriale (vector + cuvinte-cheie + parcurgere de graf)
- **16 strategii de căutare** — căutarea avansată suportă mai multe metode de reordonare, precum RRF, MMR, Cross-Encoder
- **Mai mulți furnizori LLM** — suportă Ollama (local), GLM (Zhipu AI gratuit), GROQ (inferență de mare viteză), OpenRouter (agregator de modele de la diverși furnizori), DeepSeek (Deep Seek), comutabili printr-o singură variabilă de mediu
- **Decuplare Embedding și LLM** — puteți specifica independent încorporatorul prin `EMBEDDING_PROVIDER`, iar LLM-urile din cloud revin automat la `bge-m3` local
- **Distribuție pe două modele** — în modul Ollama, sarcinile complexe folosesc modelul principal, iar cele simple comută automat la modelul mic pentru a îmbunătăți performanța
- **Segmentare inteligentă a conținutului** — textele lungi sunt procesate automat pe segmente, reducând încărcarea LLM-ului (prag configurabil)
- **Procesare a memoriei în fundal** — adăugarea memoriei poate rula în fundal, iar apelul MCP revine imediat
- **Deduplicarea memoriei** — detectează automat memoriile existente foarte similare, evitând stocarea redundantă
- **Detectarea conflictelor** — detectează fapte contradictorii între două entități, identificând informațiile invalidate și pe cele valide
- **Detectarea comunităților** — grupează automat entitățile înrudite pe baza algoritmului Label Propagation
- **Urmărirea importanței** — înregistrează automat frecvența de accesare a entităților, iar rezultatele căutării sunt ordonate după importanță
- **Uitare inteligentă** — identifică și curăță memoriile învechite, cu acces redus, păstrând graful concis
- **Import în masă** — trimite mai multe memorii odată, potrivit pentru migrarea unor volume mari de date
- **Triplete structurate** — adăugați direct „subiect-relație-obiect", omițând extracția prin LLM, finalizat în secunde
- **Interfață de administrare Web** — tablou de bord, navigare, căutare, vizualizarea grafului de cunoștințe, Q&A AI și navigarea comunităților integrate
- **Internaționalizare (i18n)** — mesajele de răspuns suportă peste 30 de locale (inclusiv zh-TW / en / zh-CN / ja / pt-BR / ko / es / de / fr etc.); instrumentele MCP urmează `SERVER_LANG`, iar REST API negociază automat după `Accept-Language` din HTTP
- **Teme întunecate/luminoase** — interfața Web suportă comutarea temei
- **Mod sigur** — adăugare rapidă a memoriei cu posibilitatea de a omite extracția entităților
- **Suport Docker** — Dockerfile integrat, suportă implementarea în containere
- **Siguranță la concurență** — asyncio.Lock protejează inițializarea, prevenind condițiile de cursă
- **Verificare de sănătate pe niveluri** — `/health` (liveness) + `/health/ready` (readiness)

## Cerințe de sistem

| Element | Cerință |
|------|------|
| Python | 3.10+ (recomandat 3.11+) |
| Neo4j | 4.0+ (`bolt://localhost:7687`) |
| Furnizor LLM | Ollama / GLM / GROQ / OpenRouter / DeepSeek (unul dintre cele cinci) |
| Node.js | 18+ (doar pentru execuția în fundal cu PM2, opțional) |
| Spațiu pe disc | ~3GB (modelele Ollama + datele Neo4j) |

### Alegerea furnizorului LLM

Comutați prin variabila de mediu `LLM_PROVIDER` (`ollama` / `glm` / `groq` / `openrouter` / `deepseek`):

| Furnizor | Caracteristici | Model LLM | Embedding | Scenariu potrivit |
|--------|------|----------|-----------|----------|
| **Ollama** (implicit) | Complet local, datele nu părăsesc mașina | `qwen2.5:3b` | `bge-m3` (excelent pentru chineză + RAG) | Aveți GPU, prețuiți confidențialitatea |
| **GLM** | Cloud gratuit, stabil, fără limitare | `glm-4-flash` (gratuit) | `embedding-3` | Fără GPU, scenarii cu căutare intensivă |
| **GROQ** | Inferență ultrarapidă | `llama-3.3-70b-versatile` | Revenire la Ollama `bge-m3` | Scrieri ocazionale, urmărirea calității |
| **OpenRouter** | Agregator de modele de la diverși furnizori, include cote gratuite | `stepfun/step-3.5-flash:free` etc. | Revenire la Ollama `bge-m3` | Doriți să folosiți un anume model din cloud |
| **DeepSeek** | Cloud Deep Seek, raport calitate-preț ridicat | `deepseek-v4-flash` / `deepseek-v4-pro` | Revenire la Ollama `bge-m3` | Înțelegerea chinezei, cloud cu cost redus |

> **Decuplarea Embedding și LLM**: încorporatorul este specificat independent prin `EMBEDDING_PROVIDER` (`ollama` / `glm`); când nu este setat, urmează `LLM_PROVIDER`. De fapt, doar `glm` folosește GLM `embedding-3`, iar restul (inclusiv GROQ / OpenRouter / DeepSeek și alte LLM-uri din cloud care nu oferă Embedding) folosesc întotdeauna automat Ollama `bge-m3`. **Prin urmare, atunci când folosiți orice LLM din cloud, este în continuare nevoie de Ollama local pentru serviciul de încorporare (cu excepția cazului în care embedding-ul este, de asemenea, setat pe glm).**

#### Modul Ollama (local)

```bash
# Modelul LLM principal (recomandat qwen2.5:3b, cel mai bun echilibru între viteză și stabilitate)
ollama pull qwen2.5:3b

# Modelul de încorporare (obligatoriu, folosit pentru căutarea vectorială)
ollama pull bge-m3
```

> **Atenționări privind alegerea modelului**:
> - `qwen2.5:3b` — recomandat, ~2s/apel, ~100 t/s, ieșirea structurată graphiti-core 100% stabilă
> - `qwen2.5:7b` — rezultate mai bune, dar de 5-10 ori mai lent, potrivit pentru scenarii care urmăresc calitatea
> - `qwen2.5:1.5b` — cel mai rapid, dar **instabil** (rata de succes a JSON-ului structurat doar 33%), nu se recomandă utilizarea

#### Modul GLM (cloud Zhipu AI)

```bash
# Setări .env
LLM_PROVIDER=glm
GLM_API_KEY=your_api_key          # obținut de la https://open.bigmodel.cn
GLM_MODEL=glm-4-flash             # model gratuit
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768      # trebuie să corespundă cu dimensiunea indexului vectorial Neo4j
```

> **Referință de performanță GLM**: scriere ~22s (text scurt), căutare ~0.34s, zero erori de Rate Limit, de 2-5 ori mai lent decât Ollama local, dar complet gratuit.

#### Modul GROQ (inferență de mare viteză)

```bash
# Setări .env
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key         # obținut de la https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile
```

> **Notă**: GROQ nu oferă serviciu de Embedding, fiind necesar să fie însoțit de încorporatorul Ollama (revenire automată) sau să setați `EMBEDDING_PROVIDER` pe glm. GROQ are un Rate Limit strict, iar utilizarea la frecvență înaltă va declanșa numeroase reîncercări.

#### Modul OpenRouter (agregator de modele de la diverși furnizori)

```bash
# Setări .env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_api_key       # obținut de la https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free   # poate fi schimbat cu orice model OpenRouter
```

> **Notă**: OpenRouter nu oferă Embedding, revenind automat la Ollama `bge-m3`. Lista de modele se găsește la https://openrouter.ai/models (include mai multe modele gratuite `:free`).

#### Modul DeepSeek (Deep Seek)

```bash
# Setări .env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key         # obținut de la https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash      # recomandat; sau deepseek-v4-pro (rezultate mai bune)
```

> **Notă**: DeepSeek nu oferă Embedding, revenind automat la Ollama `bge-m3`. `deepseek-chat` / `deepseek-reasoner` vor fi retrase la 2026-07-24, se recomandă trecerea la `deepseek-v4-flash` / `deepseek-v4-pro`. DeepSeek cere strict ca prompt-ul în modul `json_object` să conțină șirul "json", iar clientul are deja o protecție de siguranță integrată, fără a fi necesare setări suplimentare.

## Pornire rapidă

### 1. Pregătiri prealabile

Confirmați că Neo4j rulează deja pe mașina locală și pregătiți serviciul corespunzător în funcție de furnizorul LLM ales:

```bash
# Confirmați că Neo4j rulează (obligatoriu)
neo4j status
# Sau folosiți Docker: docker run -d -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/your_password neo4j:latest

# Modul Ollama: confirmați că Ollama rulează
ollama list
# Dacă nu a pornit: ollama serve

# Modul GLM / GROQ: este nevoie doar de o cheie API validă, fără serviciu local
```

### 2. Instalarea dependențelor

```bash
git clone <repo-url>
cd graphiti
uv sync
```

> **Notă**: Acest proiect folosește [uv](https://github.com/astral-sh/uv) pentru gestionarea dependențelor. Dacă nu este instalat: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 3. Configurarea mediului

```bash
cp .env.example .env
```

Editați `.env`, modificând **cel puțin** următoarele elemente:

```bash
NEO4J_PASSWORD=your_actual_password  # obligatoriu: parola Neo4j
LLM_PROVIDER=ollama                  # ollama / glm / groq / openrouter / deepseek
OLLAMA_MODEL=qwen2.5:3b              # modul Ollama: modelul LLM local
# GLM_API_KEY=your_key               # modul GLM: cheia API Zhipu AI
# GROQ_API_KEY=your_key              # modul GROQ: cheia API GROQ
# OPENROUTER_API_KEY=your_key        # modul OpenRouter: cheia API
# DEEPSEEK_API_KEY=your_key          # modul DeepSeek: cheia API
```

### 4. Pornirea serviciului

```bash
# Modul HTTP (recomandat, include interfața de administrare Web)
uv run python graphiti_mcp_server.py --transport http --port 8000

# Sau folosiți execuția în fundal cu PM2 (recomandat pentru rulare îndelungată)
pm2 start ecosystem.config.cjs
```

### 5. Verificarea serviciului

După pornire puteți accesa următoarele puncte de acces:

| Punct de acces | Descriere |
|------|------|
| http://localhost:8000/ | Interfața de administrare Web |
| http://localhost:8000/mcp | Punctul de acces MCP (pentru conectarea clienților MCP) |
| http://localhost:8000/health | Verificare de sănătate (liveness) |
| http://localhost:8000/health/ready | Verificare aprofundată (include conexiunea Neo4j) |
| http://localhost:8000/api/stats | Statistici REST API |

## Structura proiectului

```
graphiti/
├── graphiti_mcp_server.py        # Punctul de intrare principal — definirea instrumentelor MCP (19 instrumente)
├── src/
│   ├── config.py                 # Gestionarea configurației (GraphitiConfig, suportă suprapunerea JSON/.env)
│   ├── web_api.py                # REST API pentru interfața de administrare Web (peste 20 de puncte de acces)
│   ├── ollama_graphiti_client.py  # Clientul LLM Ollama (distribuție pe două modele)
│   ├── glm_client.py             # Clientul LLM GLM (Zhipu AI) (API compatibil OpenAI)
│   ├── openrouter_client.py      # Clientul LLM OpenRouter (agregator de modele de la diverși furnizori)
│   ├── deepseek_client.py        # Clientul LLM DeepSeek (json_object + protecție de siguranță json)
│   ├── ollama_embedder.py        # Adaptorul modelului de încorporare Ollama
│   ├── content_preprocessor.py   # Segmentare inteligentă a conținutului (segmentare automată a textului lung)
│   ├── deduplication.py          # Deduplicarea memoriei (comparare prin similaritate cosinus)
│   ├── importance.py             # Urmărirea importanței și uitarea inteligentă
│   ├── safe_memory_add.py        # Adăugare sigură a memoriei (omiterea extracției entităților)
│   ├── timezone_utils.py         # Conversia fusului orar (afișare UTC→fus orar local)
│   ├── i18n.py                   # Internaționalizarea în backend (REST după Accept-Language, MCP după SERVER_LANG)
│   ├── exceptions.py             # Gestionare structurată a excepțiilor (12 categorii de excepții)
│   └── logging_setup.py          # Sistem de jurnalizare (rotație temporală + monitorizarea performanței)
├── web/                          # Frontend-ul interfeței de administrare Web (SPA, fără build)
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js                # Încapsularea REST API
│       ├── components.js         # Randarea componentelor UI (include pagina comunităților)
│       └── app.js                # Rutarea SPA, gestionarea stării
├── tests/                        # Suita de teste (183 de teste)
│   ├── test_content_preprocessor.py  # Teste pentru logica de segmentare (17)
│   ├── test_new_features.py      # Teste pentru funcționalitățile noi (32)
│   ├── test_i18n.py             # Teste de internaționalizare (37)
│   ├── test_unit.py              # Teste unitare
│   ├── test_web_api.py           # Teste Web API
│   ├── test_web_ui_features.py   # Teste pentru funcționalitățile Web UI
│   ├── test_integration_manual.py # Teste de integrare manuale
│   └── bench_deepseek_flash_vs_pro.py # Script de evaluare a performanței DeepSeek flash/pro
├── tools/                        # Instrumente de dezvoltare și diagnosticare
│   ├── status_report.py          # Raport de stare integrat
│   ├── validate_config.py        # Validarea configurației
│   ├── performance_diagnose.py   # Diagnosticarea performanței
│   ├── inspect_schema.py         # Verificarea structurii Neo4j
│   └── batch_reprocess.py        # Reprocesare în masă
├── docs/                         # Documentație
├── logs/                         # Jurnale (rotație temporală, păstrate implicit 30 de zile)
├── Dockerfile                    # Implementarea containerizată Docker
└── ecosystem.config.cjs          # Configurația PM2
```

## Configurarea clientului MCP

### Modul HTTP (recomandat)

Potrivit pentru clienți MCP care suportă HTTP, precum Claude Code, Cline:

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

### Modul STDIO

Potrivit pentru clienți care necesită pornirea directă a procesului, precum Claude Desktop:

**Locația fișierului de configurare:**
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

> **Notă**: Modul SSE (`--transport sse`) nu mai este recomandat. MCP 1.x are probleme de compatibilitate la inițializarea sesiunii, vă rugăm să folosiți în schimb modul HTTP.

## Instrumente MCP (19)

### Gestionarea memoriei (7)

| Instrument | Descriere |
|------|------|
| `add_memory_simple` | Adaugă memorie în graful de cunoștințe (suportă procesare în fundal, segmentare inteligentă, verificare de deduplicare) |
| `add_episode_bulk` | Adaugă în masă mai multe memorii (procesare în fundal implicită) |
| `add_triplet` | Adăugare de triplet structurat (omite LLM, finalizat în secunde) |
| `search_memory_nodes` | Caută noduri de memorie (suportă 16 strategii de căutare, filtrare temporală) |
| `search_memory_facts` | Caută fapte de memorie (suportă filtrare după tipul relației, interval temporal, filtrare după valabilitate) |
| `advanced_search` | Căutare avansată (16 strategii, returnează noduri + muchii + comunități + fragmente) |
| `get_episodes` | Obține fragmentele de memorie recente |

### Analiza cunoștințelor (3)

| Instrument | Descriere |
|------|------|
| `check_conflicts` | Detectează conflicte de fapte între două entități (valid vs invalidat) |
| `get_node_edges` | Explorează relațiile de muchii de intrare și de ieșire ale unui nod |
| `build_communities` | Declanșează detectarea și gruparea comunităților (procesare în fundal implicită) |

### Întreținerea memoriei (2)

| Instrument | Descriere |
|------|------|
| `get_stale_memories` | Interoghează memoriile învechite, cu acces redus |
| `cleanup_stale_memories` | Curăță memoriile învechite (mod de previzualizare dry_run implicit) |

### Gestionarea sarcinilor

| Instrument | Descriere |
|------|------|
| `get_memory_task_status` | Interoghează progresul și rezultatul sarcinilor de procesare a memoriei în fundal |

### Ștergere și interogare

| Instrument | Descriere |
|------|------|
| `delete_episode` | Șterge un fragment de memorie |
| `delete_entity_edge` | Șterge o muchie de entitate (relație) |
| `get_entity_edge` | Obține informații detaliate despre o muchie de entitate |

### Administrare de sistem

| Instrument | Descriere |
|------|------|
| `get_status` | Obține starea serviciului (Neo4j, LLM, încorporator) |
| `test_connection` | Testează conexiunea Neo4j / LLM / încorporator |
| `clear_graph` | Curăță baza de date orientată pe graf (suportă curățarea după group_id) |

## Parametrii instrumentelor

### add_memory_simple

| Parametru | Tip | Obligatoriu | Valoare implicită | Descriere |
|------|------|------|--------|------|
| `name` | string | Y | | Numele memoriei |
| `episode_body` | string | Y | | Conținutul memoriei (segmentare automată peste 800 de caractere) |
| `group_id` | string | | `"default"` | ID-ul grupului (se recomandă izolarea pe proiect) |
| `source` | string | | `"text"` | Tipul sursei: `text` / `json` / `message` |
| `source_description` | string | | `"MCP Server"` | Descrierea sursei |
| `use_safe_mode` | bool | | `false` | Mod sigur (omite extracția entităților, rapid, dar memoria nu poate fi căutată) |
| `background` | bool | | `false` | Procesare în fundal (returnează imediat task_id, potrivit pentru text lung) |
| `force` | bool | | `false` | Omite verificarea de deduplicare (adăugare forțată) |
| `excluded_entity_types` | list | | | Tipuri de entități excluse (reduce volumul de extracție inutil) |

> **Sfaturi de performanță**:
> - Text scurt (<800 de caractere): procesare directă, de obicei finalizat în 30-40 de secunde
> - Text lung (>800 de caractere): segmentare automată în mai multe segmente, procesare concurentă cu `add_episode_bulk` (cu ~33% mai rapid decât în serie)
> - Folosirea lui `background=true` evită blocarea apelului MCP, urmăriți progresul prin `get_memory_task_status`
> - `use_safe_mode=true` se finalizează în secunde, dar memoria nu poate fi găsită de instrumentele de căutare
> - Când deduplicarea este activată, memoriile foarte similare vor fi semnalate cu avertisment (`force=true` permite omiterea)

### add_episode_bulk

| Parametru | Tip | Obligatoriu | Valoare implicită | Descriere |
|------|------|------|--------|------|
| `episodes` | list | Y | | Lista de memorii, fiecare element conține `name` și `content` |
| `group_id` | string | | `"default"` | ID-ul grupului |
| `source` | string | | `"text"` | Tipul sursei |
| `background` | bool | | `true` | Procesare în fundal (operațiunile în masă consumă de obicei timp) |

### add_triplet

| Parametru | Tip | Obligatoriu | Valoare implicită | Descriere |
|------|------|------|--------|------|
| `source_name` | string | Y | | Numele entității sursă (ex. "Alice") |
| `target_name` | string | Y | | Numele entității țintă (ex. "Google") |
| `relation_name` | string | Y | | Numele relației (ex. "works_at") |
| `fact` | string | Y | | Descrierea faptului (ex. "Alice works at Google") |
| `group_id` | string | | `"default"` | ID-ul grupului |
| `source_labels` | list | | | Etichetele entității sursă |
| `target_labels` | list | | | Etichetele entității țintă |

### search_memory_nodes

| Parametru | Tip | Obligatoriu | Valoare implicită | Descriere |
|------|------|------|--------|------|
| `query` | string | Y | | Cuvinte-cheie de căutare (limbaj natural) |
| `max_nodes` | int | | `10` | Numărul maxim de rezultate returnate |
| `group_ids` | list | | | Filtrare după grup (căutare combinată în mai multe grupuri) |
| `entity_types` | list | | | Filtrare după tipul entității |
| `search_recipe` | string | | | Strategie de căutare (vezi căutarea avansată) |
| `created_after` | string | | | Limita inferioară a timpului de creare (ISO datetime) |
| `created_before` | string | | | Limita superioară a timpului de creare (ISO datetime) |

### search_memory_facts

| Parametru | Tip | Obligatoriu | Valoare implicită | Descriere |
|------|------|------|--------|------|
| `query` | string | Y | | Cuvinte-cheie de căutare |
| `max_facts` | int | | `10` | Numărul maxim de rezultate returnate |
| `group_ids` | list | | | Filtrare după grup |
| `center_node_uuid` | string | | | UUID-ul nodului central (explorarea relațiilor unui nod specific) |
| `edge_types` | list | | | Filtrare după tipul relației (ex. `["works_at"]`) |
| `created_after` | string | | | Limita inferioară a timpului de creare (ISO datetime) |
| `created_before` | string | | | Limita superioară a timpului de creare (ISO datetime) |
| `only_valid` | bool | | `false` | Returnează doar faptele neinvalidate |

### advanced_search

| Parametru | Tip | Obligatoriu | Valoare implicită | Descriere |
|------|------|------|--------|------|
| `query` | string | Y | | Cuvinte-cheie de căutare |
| `search_recipe` | string | | `"combined_rrf"` | Strategie de căutare (16 opțiuni) |
| `max_results` | int | | `10` | Numărul maxim de rezultate returnate |
| `group_ids` | list | | | Filtrare după grup |
| `center_node_uuid` | string | | | UUID-ul nodului central |

**Strategii de căutare disponibile (search_recipe):**

| Categorie | Strategie | Descriere |
|------|------|------|
| Combinat | `combined_rrf` | Fuziune RRF combinată (implicit, recomandat) |
| Combinat | `combined_mmr` | Reordonare combinată MMR pentru diversitate |
| Combinat | `combined_cross_encoder` | Reordonare fină combinată Cross-Encoder |
| Muchie | `edge_rrf` / `edge_mmr` / `edge_cross_encoder` | Căutare de muchii (3 ordonări) |
| Muchie | `edge_node_distance` / `edge_episode_mentions` | Căutare de muchii (distanță în graf/număr de referințe) |
| Nod | `node_rrf` / `node_mmr` / `node_cross_encoder` | Căutare de noduri (3 ordonări) |
| Nod | `node_node_distance` / `node_episode_mentions` | Căutare de noduri (distanță în graf/număr de referințe) |
| Comunitate | `community_rrf` / `community_mmr` / `community_cross_encoder` | Căutare de comunități |

### check_conflicts

| Parametru | Tip | Obligatoriu | Valoare implicită | Descriere |
|------|------|------|--------|------|
| `source_name` | string | Y | | Numele entității sursă |
| `target_name` | string | Y | | Numele entității țintă |
| `group_id` | string | | `"default"` | ID-ul grupului |

### get_node_edges

| Parametru | Tip | Obligatoriu | Valoare implicită | Descriere |
|------|------|------|--------|------|
| `node_uuid` | string | Y | | UUID-ul nodului |
| `include_inbound` | bool | | `true` | Include muchiile de intrare |
| `include_outbound` | bool | | `true` | Include muchiile de ieșire |
| `max_edges` | int | | `50` | Numărul maxim de rezultate returnate |

### build_communities

| Parametru | Tip | Obligatoriu | Valoare implicită | Descriere |
|------|------|------|--------|------|
| `group_ids` | list | | | Grupuri specificate (lăsați gol pentru toate) |
| `background` | bool | | `true` | Procesare în fundal |

### get_stale_memories

| Parametru | Tip | Obligatoriu | Valoare implicită | Descriere |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Câte zile fără accesare se consideră învechit |
| `min_access_count` | int | | `2` | Se includ doar cele cu număr de accesări sub această valoare |
| `group_id` | string | | | Filtrare după grup |
| `limit` | int | | `50` | Numărul maxim de rezultate returnate |

### cleanup_stale_memories

| Parametru | Tip | Obligatoriu | Valoare implicită | Descriere |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Pragul de zile pentru învechire |
| `min_access_count` | int | | `2` | Pragul minim al numărului de accesări |
| `group_id` | string | | | Filtrare după grup |
| `dry_run` | bool | | `true` | Mod de previzualizare (fără ștergere efectivă) |
| `limit` | int | | `50` | Numărul maxim de procesat |

### get_memory_task_status

| Parametru | Tip | Obligatoriu | Descriere |
|------|------|------|------|
| `task_id` | string | Y | ID-ul sarcinii din fundal (returnat de `add_memory_simple(background=true)`) |

## Interfața de administrare Web

În modul HTTP, accesați `http://localhost:8000/` pentru a o utiliza.

**Funcționalități:**
- Tablou de bord — statistici privind numărul de noduri, fapte, fragmente de memorie
- Noduri de entități — navigare, filtrare, căutare vectorială
- Relații de fapte — navigare, filtrare, căutare vectorială
- Fragmente de memorie — navigare, căutare full-text, ștergere
- Navigarea comunităților — lista de noduri ale comunităților, rezumate, declanșarea construirii comunităților
- Formular de triplete — adăugarea directă a cunoștințelor structurate „subiect-relație-obiect"
- Gestionarea grupurilor — filtrare după grup, ștergere în masă
- Vizualizarea grafului de cunoștințe — prezentarea grafică a relațiilor dintre noduri
- Q&A AI — întrebări și răspunsuri inteligente bazate pe graful de cunoștințe
- Analiza calității — analiza calității și a acoperirii memoriei
- Comutarea temei — temă întunecată/luminoasă

**REST API:**

| Punct de acces | Metodă | Descriere |
|------|------|------|
| `/api/stats` | GET | Statistici pentru tabloul de bord |
| `/api/groups` | GET | Obține toate group_id-urile |
| `/api/nodes` | GET | Navigarea nodurilor de entități (paginat) |
| `/api/facts` | GET | Navigarea faptelor (paginat) |
| `/api/episodes` | GET | Navigarea fragmentelor de memorie (paginat) |
| `/api/search/nodes` | GET | Căutare vectorială de noduri |
| `/api/search/facts` | GET | Căutare vectorială de fapte |
| `/api/search/advanced` | GET | Căutare avansată (16 strategii) |
| `/api/communities` | GET | Navigarea nodurilor de comunități (paginat) |
| `/api/communities/build` | POST | Declanșează construirea comunităților |
| `/api/memory/add-bulk` | POST | Adăugare în masă a memoriei |
| `/api/memory/add-triplet` | POST | Adăugare de triplet |
| `/api/memory/tasks` | GET | Listează sarcinile din fundal (suportă filtrare după stare) |
| `/api/memory/tasks/{id}` | GET | Interoghează starea unei singure sarcini |
| `/api/analytics/stale` | GET | Interoghează memoriile învechite |
| `/api/analytics/cleanup` | POST | Curăță memoriile învechite |
| `/api/nodes/{uuid}` | DELETE | Șterge un nod |
| `/api/episodes/{uuid}` | DELETE | Șterge un fragment de memorie |
| `/api/facts/{uuid}` | DELETE | Șterge un fapt |
| `/api/groups/{group_id}` | DELETE | Șterge un întreg grup |

## Configurare

### Variabile de mediu (.env)

Configurarea folosește un mecanism de suprapunere: fișierul de configurare JSON ca bază, iar variabilele de mediu suprascriu valorile individuale.

```bash
# === Obligatoriu ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password        # trebuie modificat

# === Alegerea furnizorului LLM ===
LLM_PROVIDER=ollama                 # ollama / glm / groq / openrouter / deepseek

# === Furnizorul de Embedding (opțional, implicit urmează LLM_PROVIDER) ===
# Doar glm folosește GLM Embedding, restul folosesc întotdeauna Ollama bge-m3
# EMBEDDING_PROVIDER=ollama         # ollama / glm

# === Configurarea Ollama (folosită când LLM_PROVIDER=ollama) ===
OLLAMA_MODEL=qwen2.5:3b             # modelul principal (recomandat qwen2.5:3b)
OLLAMA_SMALL_MODEL=qwen2.5:3b       # modelul mic (pentru sarcini simple, poate fi un model diferit)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.1

# === Configurarea GLM (folosită când LLM_PROVIDER=glm) ===
GLM_API_KEY=your_api_key            # obținut de la https://open.bigmodel.cn
GLM_MODEL=glm-4-flash               # model gratuit
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768

# === Configurarea GROQ (folosită când LLM_PROVIDER=groq) ===
GROQ_API_KEY=your_api_key           # obținut de la https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile

# === Configurarea OpenRouter (folosită când LLM_PROVIDER=openrouter) ===
OPENROUTER_API_KEY=your_api_key     # obținut de la https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free

# === Configurarea DeepSeek (folosită când LLM_PROVIDER=deepseek) ===
DEEPSEEK_API_KEY=your_api_key       # obținut de la https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash    # sau deepseek-v4-pro

# === Modelul de încorporare Ollama (folosit ori de câte ori încorporarea nu este glm) ===
OLLAMA_EMBEDDING_MODEL=bge-m3
OLLAMA_EMBEDDING_DIMENSIONS=768

# === Afișare și internaționalizare (opțional) ===
GRAPHITI_DISPLAY_TIMEZONE=Asia/Taipei # fusul orar de afișare a marcajelor temporale returnate de API (nume IANA; stocarea rămâne UTC)
SERVER_LANG=zh-TW                     # limba de răspuns a instrumentelor MCP (lista completă a locale-urilor în src/i18n.py); REST API urmează în schimb Accept-Language

# === Performanța memoriei (opțional) ===
GRAPHITI_CHUNK_THRESHOLD=800         # pragul numărului de caractere care declanșează segmentarea inteligentă
GRAPHITI_MAX_CHUNK_SIZE=600          # numărul maxim de caractere per segment
GRAPHITI_MAX_COROUTINES=10            # numărul maxim de corutine concurente
GRAPHITI_DEFAULT_BACKGROUND=false    # dacă procesarea în fundal este implicită

# === Urmărirea importanței și uitarea inteligentă (opțional) ===
ENABLE_IMPORTANCE_TRACKING=true      # activează urmărirea accesului
IMPORTANCE_WEIGHT=0.1                # ponderea importanței
STALE_DAYS_THRESHOLD=30              # pragul de zile pentru învechire
STALE_MIN_ACCESS_COUNT=2             # numărul minim de accesări

# === Jurnalizare ===
LOG_FILE=logs/graphiti_mcp_server.log
LOG_LEVEL=INFO
```

> **Pentru lista completă a variabilelor de mediu**, consultați `.env.example`

### Fișier de configurare JSON

Potrivit pentru configurări care necesită control de versiune (variabilele de mediu pot suprascrie în continuare):

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

## Execuția în fundal cu PM2

```bash
npm install -g pm2

pm2 start ecosystem.config.cjs      # pornire
pm2 status                           # stare
pm2 logs graphiti-mcp-http           # jurnale în timp real
pm2 restart graphiti-mcp-http --update-env  # repornire (reîncarcă .env)

pm2 save && pm2 startup              # configurare pentru pornire automată la boot
```

> **Sfat**: După modificarea fișierului `.env`, trebuie să reporniți cu indicatorul `--update-env`, altfel variabilele de mediu nu vor fi actualizate.

## Implementarea Docker

```bash
docker build -t graphiti-mcp .

# Notă: containerul Docker trebuie să se poată conecta la Neo4j și Ollama
# Folosirea host network este cea mai simplă
docker run -p 8000:8000 --env-file .env --network host graphiti-mcp

# Sau specificați explicit adresa serviciilor externe
docker run -p 8000:8000 \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --env-file .env graphiti-mcp
```

## Testare

```bash
# Execută toate testele (183, aproximativ 1 secundă)
uv run python -m pytest tests/

# Ieșire detaliată
uv run python -m pytest tests/ -v

# Execută doar un test specific
uv run python -m pytest tests/test_content_preprocessor.py -v
uv run python -m pytest tests/test_new_features.py -v
uv run python -m pytest tests/test_unit.py -v
```

> **Notă**: Cele 3 teste async din `test_integration_manual.py` necesită instalarea `pytest-asyncio`; în lipsa acestuia vor apărea ca Failed, dar nu afectează celelalte teste. `bench_deepseek_flash_vs_pro.py` este un script de evaluare a performanței, nu un test unitar.

## Depanare

### Conexiunea Neo4j eșuează

```bash
neo4j status                              # verifică starea serviciului
cypher-shell -u neo4j -p your_password    # confirmă corectitudinea parolei
curl http://localhost:7474                 # confirmă portul HTTP
```

Cauze frecvente:
- Neo4j nu a pornit
- Parolă greșită (`NEO4J_PASSWORD` din `.env`)
- Portul este ocupat sau blocat de firewall

### Conexiunea LLM eșuează

**Modul Ollama:**
```bash
ollama serve                # pornește serviciul Ollama
ollama list                 # verifică modelele instalate
ollama pull qwen2.5:3b      # instalează modelul lipsă
```

Cauze frecvente: Ollama nu a pornit, modelul nu este instalat, memoria GPU insuficientă

**Modul GLM:**
- Confirmați corectitudinea `GLM_API_KEY`
- Confirmați `GLM_EMBEDDING_DIMENSIONS=768` (trebuie să corespundă cu indexul vectorial Neo4j)
- Punctul de acces API GLM: `https://open.bigmodel.cn/api/paas/v4/`

**Modul GROQ:**
- Confirmați corectitudinea `GROQ_API_KEY`
- Când Rate Limit apare frecvent, luați în considerare comutarea la modul GLM
- GROQ nu oferă Embedding, asigurați-vă că încorporatorul Ollama este disponibil

**Modul OpenRouter:**
- Confirmați corectitudinea `OPENROUTER_API_KEY` și că `OPENROUTER_MODEL` este un ID de model valid (vezi https://openrouter.ai/models)
- Nu oferă Embedding, asigurați-vă că încorporatorul Ollama este disponibil

**Modul DeepSeek:**
- Confirmați corectitudinea `DEEPSEEK_API_KEY`
- Dacă apare `Prompt must contain the word 'json'`: aceasta este o cerință strictă a modului `json_object` al DeepSeek, iar clientul are deja o protecție de siguranță integrată; dacă apare în continuare, confirmați că folosiți cea mai recentă versiune a `src/deepseek_client.py` și reporniți serviciul
- Nu oferă Embedding, asigurați-vă că încorporatorul Ollama este disponibil

### Eroare de conexiune MCP

Dacă apare `Invalid request parameters` sau `Received request before initialization was complete`:

1. Confirmați că folosiți modul de transport HTTP (**nu folosiți SSE**)
2. Confirmați că setarea clientului este `"type": "http"`, `"url": "http://localhost:8000/mcp"`
3. Reporniți serviciul: `pm2 restart graphiti-mcp-http --update-env`
4. Executați `/mcp` în Claude Code pentru a vă reconecta

### Adăugarea memoriei este lentă

- **Ollama**: verificați dimensiunea modelului (`qwen2.5:3b` este de 5-10 ori mai rapid decât `7b`), confirmați că folosiți GPU (`ollama ps`)
- **GLM**: fiecare add_episode necesită peste 10-20 de drumuri dus-întors prin rețea către LLM, ~22s pentru text scurt este o valoare normală
- **GROQ**: Rate Limit duce la numeroase reîncercări; dacă este folosit frecvent, se recomandă comutarea la GLM sau Ollama
- Folosiți `background=true` pentru a evita blocarea
- Reduceți `GRAPHITI_CHUNK_THRESHOLD` pentru ca textul lung să fie segmentat mai devreme

### Probleme PM2

```bash
pm2 status                                        # verifică starea
pm2 logs graphiti-mcp-http --err --lines 50        # jurnalul de erori
lsof -i :8000                                     # verifică ocuparea portului
pm2 delete graphiti-mcp-http && pm2 start ecosystem.config.cjs  # repornire completă
```

## Instrumente de dezvoltare și diagnosticare

```bash
uv run python tools/status_report.py           # raport de stare integrat (Neo4j + Ollama + configurație)
uv run python tools/validate_config.py         # validează .env și integritatea configurației
uv run python tools/performance_diagnose.py    # diagnosticarea performanței LLM
uv run python tools/inspect_schema.py          # verificarea indexurilor și constrângerilor Neo4j
uv run python tools/migrate_embeddings.py      # migrarea modelului de Embedding (regenerarea vectorilor după schimbarea modelului)
```

### Migrarea modelului de Embedding

După schimbarea modelului de embedding (ex. `nomic-embed-text` → `bge-m3`), puteți folosi instrumentul de migrare pentru a regenera toți vectorii existenți, asigurând consistența calității căutării:

```bash
# Previzualizează numărul de elemente care necesită migrare
uv run python tools/migrate_embeddings.py --dry-run

# Migrare completă (suportă reluarea de la punctul de întrerupere)
uv run python tools/migrate_embeddings.py

# Migrează doar un grup specificat
uv run python tools/migrate_embeddings.py --group-id myproject

# Continuă de la punctul de întrerupere (reluare după întrerupere)
uv run python tools/migrate_embeddings.py --resume
```

> **Compatibilitate**: `bge-m3` are nativ 1024 de dimensiuni, iar sistemul îl trunchiază automat la 768 de dimensiuni pentru a fi compatibil cu indexul vectorial Neo4j existent. Datele de dinainte și de după migrare pot coexista, dar se recomandă efectuarea unei migrări complete pentru a obține cea mai bună calitate a căutării.

## Documentație

- [Instrucțiuni de utilizare a instrumentelor](../使用工具的指令.md) — ghid de utilizare a instrumentelor MCP și bune practici
- [Graphiti Memory Rules](../graphiti-memory-rules.md) — explicarea regulilor de memorie

## Licență

MIT License
