# Graphiti MCP Server

Tietämysgraafiin perustuva muistipalvelu — MCP-palvelin, joka yhdistää useita LLM-tarjoajia (Ollama / GLM / GROQ / OpenRouter / DeepSeek) ja Neo4j-graafitietokannan.

Kehitetty laajentamalla projektia [getzep/graphiti](https://github.com/getzep/graphiti), tukee joustavaa vaihtoa paikallisen Ollaman ja pilvipohjaisten LLM:ien välillä, ja Embedding-tarjoaja voidaan määrittää erikseen (irrotettuna LLM:stä).

## Ominaisuudet

- **Älykäs muistinhallinta** — tallentaa ja hakee monimutkaisia muistisuhteita tietämysgraafin avulla
- **Semanttinen haku** — vektoriupotuksiin perustuva hybridihaku (vektori + avainsana + graafiläpikäynti)
- **16 hakustrategiaa** — edistynyt haku tukee useita uudelleenjärjestelytapoja, kuten RRF, MMR ja Cross-Encoder
- **Useita LLM-tarjoajia** — tukee Ollamaa (paikallinen), GLM:ää (Zhipu AI ilmainen), GROQ:ia (nopea päättely), OpenRouteria (yhdistää useiden tarjoajien mallit) ja DeepSeekiä, vaihto yhdellä napsautuksella ympäristömuuttujan kautta
- **Embedding irrotettu LLM:stä** — upotin voidaan määrittää erikseen muuttujalla `EMBEDDING_PROVIDER`, pilvipohjaiset LLM:t palaavat automaattisesti paikalliseen `bge-m3`:een
- **Kaksoismallin jako** — Ollama-tilassa monimutkaiset tehtävät käyttävät päämallia, yksinkertaiset tehtävät vaihtavat automaattisesti pieneen malliin suorituskyvyn parantamiseksi
- **Älykäs sisällön paloittelu** — pitkä teksti käsitellään automaattisesti osissa, mikä vähentää LLM:n kuormaa (konfiguroitava kynnysarvo)
- **Taustamuistin käsittely** — muistin lisäys voidaan suorittaa taustalla, MCP-kutsu palaa välittömästi
- **Muistin kaksoiskappaleiden poisto** — havaitsee automaattisesti erittäin samankaltaiset olemassa olevat muistit ja välttää päällekkäisen tallennuksen
- **Ristiriitojen havaitseminen** — havaitsee kahden entiteetin väliset ristiriitaiset faktat ja tunnistaa vanhentuneet ja voimassa olevat tiedot
- **Yhteisöjen havaitseminen** — ryhmittelee automaattisesti toisiinsa liittyvät entiteetit Label Propagation -algoritmin avulla
- **Tärkeyden seuranta** — kirjaa automaattisesti entiteettien käyttötiheyden, hakutulokset järjestetään tärkeyden mukaan
- **Älykäs unohtaminen** — tunnistaa ja siivoaa vanhentuneet, vähän käytetyt muistit pitäen graafin tiiviinä
- **Joukkotuonti** — lähetä useita muisteja kerralla, sopii suurten datamäärien siirtoon
- **Rakenteiset kolmikot** — lisää suoraan "kohde-suhde-objekti", ohittaa LLM-poiminnan, valmis sekunneissa
- **Web-hallintakäyttöliittymä** — sisäänrakennettu kojelauta, selaus, haku, tietämysgraafin visualisointi, AI-kysymys ja -vastaus sekä yhteisöjen selaus
- **Monikielisyys (i18n)** — vastausviestit tukevat yli 30 lokaalia (mukaan lukien zh-TW / en / zh-CN / ja / pt-BR / ko / es / de / fr jne.); MCP-työkalut käyttävät muuttujaa `SERVER_LANG`, REST API neuvottelee automaattisesti HTTP `Accept-Language` -otsakkeen perusteella
- **Tumma/vaalea teema** — Web-käyttöliittymä tukee teeman vaihtoa
- **Turvallinen tila** — valinnainen nopea muistin lisäys, joka ohittaa entiteettien poiminnan
- **Docker-tuki** — sisäänrakennettu Dockerfile, tukee säiliöllistettyä käyttöönottoa
- **Samanaikaisuusturvallisuus** — asyncio.Lock suojaa alustuksen ja estää kilpailutilanteet
- **Kerroksittainen terveystarkistus** — `/health` (liveness) + `/health/ready` (readiness)

## Järjestelmävaatimukset

| Kohde | Vaatimus |
|------|------|
| Python | 3.10+ (suositus 3.11+) |
| Neo4j | 4.0+ (`bolt://localhost:7687`) |
| LLM-tarjoaja | Ollama / GLM / GROQ / OpenRouter / DeepSeek (valitse yksi viidestä) |
| Node.js | 18+ (vain PM2-taustakäyttöä varten, valinnainen) |
| Levytila | ~3 Gt (Ollama-mallit + Neo4j-data) |

### LLM-tarjoajan valinta

Vaihda ympäristömuuttujan `LLM_PROVIDER` kautta (`ollama` / `glm` / `groq` / `openrouter` / `deepseek`):

| Tarjoaja | Ominaisuudet | LLM-malli | Embedding | Sopiva käyttötarkoitus |
|--------|------|----------|-----------|----------|
| **Ollama** (oletus) | Täysin paikallinen, data ei poistu koneelta | `qwen2.5:3b` | `bge-m3` (erinomainen kiina + RAG) | GPU saatavilla, yksityisyyttä arvostava |
| **GLM** | Ilmainen pilvi, vakaa ilman nopeusrajoituksia | `glm-4-flash` (ilmainen) | `embedding-3` | Ei GPU:ta, hakuintensiiviset käyttötilanteet |
| **GROQ** | Erittäin nopea päättely | `llama-3.3-70b-versatile` | Palaa Ollaman `bge-m3`:een | Satunnainen kirjoitus, laatua tavoitteleva |
| **OpenRouter** | Yhdistää useiden tarjoajien mallit, sisältää ilmaisen kiintiön | `stepfun/step-3.5-flash:free` jne. | Palaa Ollaman `bge-m3`:een | Halu käyttää tiettyä pilvimallia |
| **DeepSeek** | DeepSeek-pilvi, korkea hinta-laatusuhde | `deepseek-v4-flash` / `deepseek-v4-pro` | Palaa Ollaman `bge-m3`:een | Kiinan ymmärrys, edullinen pilvi |

> **Embedding irrotettu LLM:stä**: upotin määritetään erikseen muuttujalla `EMBEDDING_PROVIDER` (`ollama` / `glm`), ja jos sitä ei ole asetettu, se seuraa muuttujaa `LLM_PROVIDER`. Käytännössä vain `glm` käyttää GLM:n `embedding-3`:a, muut (mukaan lukien pilvipohjaiset LLM:t kuten GROQ / OpenRouter / DeepSeek, jotka eivät tarjoa Embeddingiä) käyttävät automaattisesti Ollaman `bge-m3`:a. **Siksi mitä tahansa pilvipohjaista LLM:ää käytettäessä tarvitaan edelleen paikallinen Ollama tarjoamaan upotuspalvelu (ellei embeddingiä ole myös asetettu glm:ksi).**

#### Ollama-tila (paikallinen)

```bash
# LLM-päämalli (suositus qwen2.5:3b, paras tasapaino nopeuden ja vakauden välillä)
ollama pull qwen2.5:3b

# Upotusmalli (pakollinen, käytetään vektorihakuun)
ollama pull bge-m3
```

> **Huomioita mallin valinnasta**:
> - `qwen2.5:3b` — suositeltu, ~2 s/kutsu, ~100 t/s, graphiti-coren rakenteinen tuloste 100 % vakaa
> - `qwen2.5:7b` — parempi tulos mutta 5–10 kertaa hitaampi, sopii laatua tavoitteleviin tilanteisiin
> - `qwen2.5:1.5b` — nopein mutta **epävakaa** (rakenteisen JSON:n onnistumisaste vain 33 %), ei suositella käytettäväksi

#### GLM-tila (Zhipu AI -pilvi)

```bash
# .env-asetukset
LLM_PROVIDER=glm
GLM_API_KEY=your_api_key          # Hae osoitteesta https://open.bigmodel.cn
GLM_MODEL=glm-4-flash             # Ilmainen malli
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768      # Täytyy vastata Neo4j-vektori-indeksin ulottuvuuksia
```

> **GLM:n suorituskykyviite**: kirjoitus ~22 s (lyhyt teksti), haku ~0,34 s, nolla nopeusrajoitusvirhettä, 2–5 kertaa hitaampi kuin paikallinen Ollama mutta täysin ilmainen.

#### GROQ-tila (nopea päättely)

```bash
# .env-asetukset
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key         # Hae osoitteesta https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile
```

> **Huomautus**: GROQ ei tarjoa Embedding-palvelua, ja se on yhdistettävä Ollama-upottimeen (automaattinen palautus) tai aseta `EMBEDDING_PROVIDER` arvoon glm. GROQ:lla on tiukat nopeusrajoitukset, ja suurtaajuinen käyttö laukaisee paljon uudelleenyrityksiä.

#### OpenRouter-tila (yhdistää useiden tarjoajien mallit)

```bash
# .env-asetukset
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_api_key       # Hae osoitteesta https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free   # Voidaan vaihtaa mihin tahansa OpenRouter-malliin
```

> **Huomautus**: OpenRouter ei tarjoa Embeddingiä, vaan palaa automaattisesti Ollaman `bge-m3`:een. Malliluettelo löytyy osoitteesta https://openrouter.ai/models (sisältää useita `:free`-ilmaismalleja).

#### DeepSeek-tila (DeepSeek)

```bash
# .env-asetukset
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key         # Hae osoitteesta https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash      # Suositeltu; tai deepseek-v4-pro (parempi tulos)
```

> **Huomautus**: DeepSeek ei tarjoa Embeddingiä, vaan palaa automaattisesti Ollaman `bge-m3`:een. `deepseek-chat` / `deepseek-reasoner` poistuvat käytöstä 2026-07-24, joten on suositeltavaa siirtyä malleihin `deepseek-v4-flash` / `deepseek-v4-pro`. DeepSeek vaatii tiukasti, että `json_object`-tilan promptti sisältää merkkijonon "json", ja asiakas on jo varustettu sisäänrakennetulla varmistuksella, joten lisäasetuksia ei tarvita.

## Pikakäynnistys

### 1. Esivalmistelut

Varmista, että Neo4j on käynnissä paikallisesti, ja valmistele vastaava palvelu valitsemasi LLM-tarjoajan mukaan:

```bash
# Varmista, että Neo4j on käynnissä (pakollinen)
neo4j status
# Tai käytä Dockeria: docker run -d -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/your_password neo4j:latest

# Ollama-tila: varmista, että Ollama on käynnissä
ollama list
# Jos ei ole käynnistetty: ollama serve

# GLM / GROQ -tila: tarvitaan vain kelvollinen API-avain, paikallista palvelua ei tarvita
```

### 2. Asenna riippuvuudet

```bash
git clone <repo-url>
cd graphiti
uv sync
```

> **Huomautus**: tämä projekti käyttää riippuvuuksien hallintaan työkalua [uv](https://github.com/astral-sh/uv). Jos sitä ei ole asennettu: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 3. Konfiguroi ympäristö

```bash
cp .env.example .env
```

Muokkaa tiedostoa `.env`, ja **vähintään** seuraavat kohdat on muutettava:

```bash
NEO4J_PASSWORD=your_actual_password  # Pakollinen: Neo4j-salasana
LLM_PROVIDER=ollama                  # ollama / glm / groq / openrouter / deepseek
OLLAMA_MODEL=qwen2.5:3b              # Ollama-tila: paikallinen LLM-malli
# GLM_API_KEY=your_key               # GLM-tila: Zhipu AI API -avain
# GROQ_API_KEY=your_key              # GROQ-tila: GROQ API -avain
# OPENROUTER_API_KEY=your_key        # OpenRouter-tila: API-avain
# DEEPSEEK_API_KEY=your_key          # DeepSeek-tila: API-avain
```

### 4. Käynnistä palvelu

```bash
# HTTP-tila (suositus, sisältää Web-hallintakäyttöliittymän)
uv run python graphiti_mcp_server.py --transport http --port 8000

# Tai käytä PM2-taustakäyttöä (suositus pitkäaikaiseen ajoon)
pm2 start ecosystem.config.cjs
```

### 5. Varmenna palvelu

Käynnistyksen jälkeen voit käyttää seuraavia päätepisteitä:

| Päätepiste | Kuvaus |
|------|------|
| http://localhost:8000/ | Web-hallintakäyttöliittymä |
| http://localhost:8000/mcp | MCP-päätepiste (MCP-asiakkaiden yhdistämiseen) |
| http://localhost:8000/health | Terveystarkistus (liveness) |
| http://localhost:8000/health/ready | Syvätarkistus (sisältää Neo4j-yhteyden) |
| http://localhost:8000/api/stats | REST API -tilastot |

## Projektin rakenne

```
graphiti/
├── graphiti_mcp_server.py        # Pääsisääntulo — MCP-työkalujen määrittely (19 työkalua)
├── src/
│   ├── config.py                 # Konfiguraationhallinta (GraphitiConfig, tukee JSON/.env-kerrostusta)
│   ├── web_api.py                # Web-hallintakäyttöliittymän REST API (20+ päätepistettä)
│   ├── ollama_graphiti_client.py  # Ollama LLM -asiakas (kaksoismallin jako)
│   ├── glm_client.py             # GLM (Zhipu AI) LLM -asiakas (OpenAI-yhteensopiva API)
│   ├── openrouter_client.py      # OpenRouter LLM -asiakas (yhdistää useiden tarjoajien mallit)
│   ├── deepseek_client.py        # DeepSeek LLM -asiakas (json_object + varmistava json-suojaus)
│   ├── ollama_embedder.py        # Ollaman upotusmallin adapteri
│   ├── content_preprocessor.py   # Älykäs sisällön paloittelu (pitkän tekstin automaattinen segmentointi)
│   ├── deduplication.py          # Muistin kaksoiskappaleiden poisto (kosinisamankaltaisuusvertailu)
│   ├── importance.py             # Tärkeyden seuranta ja älykäs unohtaminen
│   ├── safe_memory_add.py        # Turvallinen muistin lisäys (ohittaa entiteettien poiminnan)
│   ├── timezone_utils.py         # Aikavyöhykemuunnos (UTC→paikallinen aikavyöhyke näytössä)
│   ├── i18n.py                   # Taustajärjestelmän monikielisyys (REST käyttää Accept-Languagea, MCP käyttää SERVER_LANGia)
│   ├── exceptions.py             # Rakenteinen poikkeuskäsittely (12 poikkeusluokkaa)
│   └── logging_setup.py          # Lokijärjestelmä (aikapohjainen kierto + suorituskyvyn seuranta)
├── web/                          # Web-hallintakäyttöliittymän frontend (SPA, ei build-vaihetta)
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js                # REST API -kapselointi
│       ├── components.js         # UI-komponenttien renderöinti (sisältää yhteisösivun)
│       └── app.js                # SPA-reititys, tilanhallinta
├── tests/                        # Testikokoelma (183 testiä)
│   ├── test_content_preprocessor.py  # Paloittelulogiikan testit (17 kpl)
│   ├── test_new_features.py      # Uusien ominaisuuksien testit (32 kpl)
│   ├── test_i18n.py             # Monikielisyystestit (37 kpl)
│   ├── test_unit.py              # Yksikkötestit
│   ├── test_web_api.py           # Web API -testit
│   ├── test_web_ui_features.py   # Web UI -ominaisuustestit
│   ├── test_integration_manual.py # Manuaaliset integraatiotestit
│   └── bench_deepseek_flash_vs_pro.py # DeepSeek flash/pro -suorituskyvyn vertailuskripti
├── tools/                        # Kehityksen diagnostiikkatyökalut
│   ├── status_report.py          # Yhdistetty tilaraportti
│   ├── validate_config.py        # Konfiguraation validointi
│   ├── performance_diagnose.py   # Suorituskyvyn diagnostiikka
│   ├── inspect_schema.py         # Neo4j-rakenteen tarkistus
│   └── batch_reprocess.py        # Eräuudelleenkäsittely
├── docs/                         # Dokumentaatio
├── logs/                         # Lokit (aikapohjainen kierto, oletuksena säilytys 30 päivää)
├── Dockerfile                    # Docker-säiliöllistetty käyttöönotto
└── ecosystem.config.cjs          # PM2-konfiguraatio
```

## MCP-asiakkaan asetukset

### HTTP-tila (suositus)

Sopii MCP-asiakkaille, jotka tukevat HTTP:tä, kuten Claude Code ja Cline:

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

### STDIO-tila

Sopii asiakkaille, jotka tarvitsevat prosessin suoran käynnistyksen, kuten Claude Desktop:

**Konfiguraatiotiedoston sijainti:**
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

> **Huomautus**: SSE-tilaa (`--transport sse`) ei enää suositella. MCP 1.x:ssä on session alustuksen yhteensopivuusongelmia, joten käytä sen sijaan HTTP-tilaa.

## MCP-työkalut (19 kpl)

### Muistinhallinta (7 kpl)

| Työkalu | Kuvaus |
|------|------|
| `add_memory_simple` | Lisää muistin tietämysgraafiin (tukee taustakäsittelyä, älykästä paloittelua, kaksoiskappaleiden tarkistusta) |
| `add_episode_bulk` | Lisää useita muisteja joukkona (oletuksena taustakäsittely) |
| `add_triplet` | Rakenteisen kolmikon lisäys (ohittaa LLM:n, valmis sekunneissa) |
| `search_memory_nodes` | Hae muistisolmuja (tukee 16 hakustrategiaa, aikasuodatusta) |
| `search_memory_facts` | Hae muistifaktoja (tukee suhdetyypin suodatusta, aikaväliä, voimassaolon suodatusta) |
| `advanced_search` | Edistynyt haku (16 strategiaa, palauttaa solmut+reunat+yhteisöt+jaksot) |
| `get_episodes` | Hae viimeisimmät muistijaksot |

### Tietämysanalyysi (3 kpl)

| Työkalu | Kuvaus |
|------|------|
| `check_conflicts` | Havaitsee kahden entiteetin väliset faktaristiriidat (voimassa vs. vanhentunut) |
| `get_node_edges` | Tutkii solmun tulo- ja lähtöreunasuhteita |
| `build_communities` | Käynnistää yhteisöjen havaitsemisen ja ryhmittelyn (oletuksena taustakäsittely) |

### Muistin ylläpito (2 kpl)

| Työkalu | Kuvaus |
|------|------|
| `get_stale_memories` | Hae vanhentuneet, vähän käytetyt muistit |
| `cleanup_stale_memories` | Siivoa vanhentuneet muistit (oletuksena dry_run-esikatselutila) |

### Tehtävienhallinta

| Työkalu | Kuvaus |
|------|------|
| `get_memory_task_status` | Kysele taustamuistin käsittelytehtävän edistymistä ja tuloksia |

### Poisto ja kysely

| Työkalu | Kuvaus |
|------|------|
| `delete_episode` | Poista muistijakso |
| `delete_entity_edge` | Poista entiteettireuna (suhde) |
| `get_entity_edge` | Hae entiteettireunan yksityiskohtaiset tiedot |

### Järjestelmänhallinta

| Työkalu | Kuvaus |
|------|------|
| `get_status` | Hae palvelun tila (Neo4j, LLM, upotin) |
| `test_connection` | Testaa Neo4j / LLM / upotin -yhteys |
| `clear_graph` | Tyhjennä graafitietokanta (tukee tyhjennystä group_id:n mukaan) |

## Työkalujen parametrit

### add_memory_simple

| Parametri | Tyyppi | Pakollinen | Oletusarvo | Kuvaus |
|------|------|------|--------|------|
| `name` | string | K | | Muistin nimi |
| `episode_body` | string | K | | Muistin sisältö (yli 800 merkkiä paloitellaan automaattisesti) |
| `group_id` | string | | `"default"` | Ryhmän ID (suositellaan eristämistä projekteittain) |
| `source` | string | | `"text"` | Lähdetyyppi: `text` / `json` / `message` |
| `source_description` | string | | `"MCP Server"` | Lähteen kuvaus |
| `use_safe_mode` | bool | | `false` | Turvallinen tila (ohittaa entiteettien poiminnan, nopea mutta muistia ei voi hakea) |
| `background` | bool | | `false` | Taustakäsittely (palauttaa välittömästi task_id:n, sopii pitkälle tekstille) |
| `force` | bool | | `false` | Ohittaa kaksoiskappaleiden tarkistuksen (pakottaa lisäyksen) |
| `excluded_entity_types` | list | | | Poisluettavat entiteettityypit (vähentää tarpeetonta poimintamäärää) |

> **Suorituskykyvihjeitä**:
> - Lyhyt teksti (<800 merkkiä): käsitellään suoraan, yleensä valmis 30–40 sekunnissa
> - Pitkä teksti (>800 merkkiä): paloitellaan automaattisesti useaan osaan, käsitellään rinnakkain toiminnolla `add_episode_bulk` (~33 % nopeampi kuin sarjallinen)
> - Käyttämällä `background=true` voit välttää MCP-kutsun jumiutumisen ja seurata edistymistä toiminnolla `get_memory_task_status`
> - `use_safe_mode=true` valmistuu sekunneissa mutta muistia ei voi löytää hakutyökaluilla
> - Kun kaksoiskappaleiden poisto on käytössä, erittäin samankaltaisista muisteista varoitetaan (`force=true` ohittaa tarkistuksen)

### add_episode_bulk

| Parametri | Tyyppi | Pakollinen | Oletusarvo | Kuvaus |
|------|------|------|--------|------|
| `episodes` | list | K | | Muistilista, jonka jokainen kohta sisältää kentät `name` ja `content` |
| `group_id` | string | | `"default"` | Ryhmän ID |
| `source` | string | | `"text"` | Lähdetyyppi |
| `background` | bool | | `true` | Taustakäsittely (joukkokäsittely on yleensä aikaa vievää) |

### add_triplet

| Parametri | Tyyppi | Pakollinen | Oletusarvo | Kuvaus |
|------|------|------|--------|------|
| `source_name` | string | K | | Lähde-entiteetin nimi (esim. "Alice") |
| `target_name` | string | K | | Kohde-entiteetin nimi (esim. "Google") |
| `relation_name` | string | K | | Suhteen nimi (esim. "works_at") |
| `fact` | string | K | | Faktan kuvaus (esim. "Alice works at Google") |
| `group_id` | string | | `"default"` | Ryhmän ID |
| `source_labels` | list | | | Lähde-entiteetin tunnisteet |
| `target_labels` | list | | | Kohde-entiteetin tunnisteet |

### search_memory_nodes

| Parametri | Tyyppi | Pakollinen | Oletusarvo | Kuvaus |
|------|------|------|--------|------|
| `query` | string | K | | Hakuavainsana (luonnollinen kieli) |
| `max_nodes` | int | | `10` | Palautettavien määrän enimmäismäärä |
| `group_ids` | list | | | Ryhmäsuodatus (useiden ryhmien yhteishaku) |
| `entity_types` | list | | | Entiteettityypin suodatus |
| `search_recipe` | string | | | Hakustrategia (katso edistynyt haku) |
| `created_after` | string | | | Luontiajan alaraja (ISO datetime) |
| `created_before` | string | | | Luontiajan yläraja (ISO datetime) |

### search_memory_facts

| Parametri | Tyyppi | Pakollinen | Oletusarvo | Kuvaus |
|------|------|------|--------|------|
| `query` | string | K | | Hakuavainsana |
| `max_facts` | int | | `10` | Palautettavien määrän enimmäismäärä |
| `group_ids` | list | | | Ryhmäsuodatus |
| `center_node_uuid` | string | | | Keskussolmun UUID (tietyn solmun suhteiden tutkiminen) |
| `edge_types` | list | | | Suhdetyypin suodatus (esim. `["works_at"]`) |
| `created_after` | string | | | Luontiajan alaraja (ISO datetime) |
| `created_before` | string | | | Luontiajan yläraja (ISO datetime) |
| `only_valid` | bool | | `false` | Palauta vain voimassa olevat faktat |

### advanced_search

| Parametri | Tyyppi | Pakollinen | Oletusarvo | Kuvaus |
|------|------|------|--------|------|
| `query` | string | K | | Hakuavainsana |
| `search_recipe` | string | | `"combined_rrf"` | Hakustrategia (16 valittavissa) |
| `max_results` | int | | `10` | Palautettavien määrän enimmäismäärä |
| `group_ids` | list | | | Ryhmäsuodatus |
| `center_node_uuid` | string | | | Keskussolmun UUID |

**Käytettävissä olevat hakustrategiat (search_recipe):**

| Luokka | Strategia | Kuvaus |
|------|------|------|
| Yhdistetty | `combined_rrf` | Yhdistetty RRF-fuusio (oletus, suositeltu) |
| Yhdistetty | `combined_mmr` | Yhdistetty MMR-monimuotoisuuden uudelleenjärjestely |
| Yhdistetty | `combined_cross_encoder` | Yhdistetty Cross-Encoder -tarkkuusjärjestely |
| Reuna | `edge_rrf` / `edge_mmr` / `edge_cross_encoder` | Reunahaku (3 järjestelytapaa) |
| Reuna | `edge_node_distance` / `edge_episode_mentions` | Reunahaku (graafietäisyys/viittausmäärä) |
| Solmu | `node_rrf` / `node_mmr` / `node_cross_encoder` | Solmuhaku (3 järjestelytapaa) |
| Solmu | `node_node_distance` / `node_episode_mentions` | Solmuhaku (graafietäisyys/viittausmäärä) |
| Yhteisö | `community_rrf` / `community_mmr` / `community_cross_encoder` | Yhteisöhaku |

### check_conflicts

| Parametri | Tyyppi | Pakollinen | Oletusarvo | Kuvaus |
|------|------|------|--------|------|
| `source_name` | string | K | | Lähde-entiteetin nimi |
| `target_name` | string | K | | Kohde-entiteetin nimi |
| `group_id` | string | | `"default"` | Ryhmän ID |

### get_node_edges

| Parametri | Tyyppi | Pakollinen | Oletusarvo | Kuvaus |
|------|------|------|--------|------|
| `node_uuid` | string | K | | Solmun UUID |
| `include_inbound` | bool | | `true` | Sisällytä tuloreunat |
| `include_outbound` | bool | | `true` | Sisällytä lähtöreunat |
| `max_edges` | int | | `50` | Palautettavien määrän enimmäismäärä |

### build_communities

| Parametri | Tyyppi | Pakollinen | Oletusarvo | Kuvaus |
|------|------|------|--------|------|
| `group_ids` | list | | | Määritetyt ryhmät (jätä tyhjäksi kaikille) |
| `background` | bool | | `true` | Taustakäsittely |

### get_stale_memories

| Parametri | Tyyppi | Pakollinen | Oletusarvo | Kuvaus |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Kuinka monta päivää ilman käyttöä katsotaan vanhentuneeksi |
| `min_access_count` | int | | `2` | Otetaan mukaan vain, jos käyttömäärä on tätä pienempi |
| `group_id` | string | | | Ryhmäsuodatus |
| `limit` | int | | `50` | Palautettavien määrän enimmäismäärä |

### cleanup_stale_memories

| Parametri | Tyyppi | Pakollinen | Oletusarvo | Kuvaus |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Vanhentumispäivien kynnysarvo |
| `min_access_count` | int | | `2` | Vähimmäiskäyttömäärän kynnysarvo |
| `group_id` | string | | | Ryhmäsuodatus |
| `dry_run` | bool | | `true` | Esikatselutila (ei poista tosiasiallisesti) |
| `limit` | int | | `50` | Käsiteltävien määrän enimmäismäärä |

### get_memory_task_status

| Parametri | Tyyppi | Pakollinen | Kuvaus |
|------|------|------|------|
| `task_id` | string | K | Taustatehtävän ID (palauttaa `add_memory_simple(background=true)`) |

## Web-hallintakäyttöliittymä

HTTP-tilassa pääset käyttämään sitä siirtymällä osoitteeseen `http://localhost:8000/`.

**Ominaisuudet:**
- Kojelauta — solmujen, faktojen ja muistijaksojen määrätilastot
- Entiteettisolmut — selaus, suodatus, vektorihaku
- Faktasuhteet — selaus, suodatus, vektorihaku
- Muistijaksot — selaus, kokotekstihaku, poisto
- Yhteisöjen selaus — yhteisösolmujen luettelo, tiivistelmät, yhteisön rakentamisen käynnistys
- Kolmikkolomake — lisää suoraan "kohde-suhde-objekti" -rakenteista tietämystä
- Group-hallinta — suodatus ryhmittäin, eräpoisto
- Tietämysgraafin visualisointi — solmusuhteiden graafinen esitys
- AI-kysymys ja -vastaus — tietämysgraafiin perustuva älykäs kysely
- Laatuanalyysi — muistin laadun ja kattavuuden analyysi
- Teeman vaihto — tumma/vaalea teema

**REST API:**

| Päätepiste | Metodi | Kuvaus |
|------|------|------|
| `/api/stats` | GET | Kojelaudan tilastot |
| `/api/groups` | GET | Hae kaikki group_id:t |
| `/api/nodes` | GET | Selaa entiteettisolmuja (sivutus) |
| `/api/facts` | GET | Selaa faktoja (sivutus) |
| `/api/episodes` | GET | Selaa muistijaksoja (sivutus) |
| `/api/search/nodes` | GET | Vektorihaku solmuille |
| `/api/search/facts` | GET | Vektorihaku faktoille |
| `/api/search/advanced` | GET | Edistynyt haku (16 strategiaa) |
| `/api/communities` | GET | Selaa yhteisösolmuja (sivutus) |
| `/api/communities/build` | POST | Käynnistä yhteisön rakentaminen |
| `/api/memory/add-bulk` | POST | Lisää muisteja joukkona |
| `/api/memory/add-triplet` | POST | Lisää kolmikko |
| `/api/memory/tasks` | GET | Listaa taustatehtävät (tukee tilan suodatusta) |
| `/api/memory/tasks/{id}` | GET | Kysele yksittäisen tehtävän tila |
| `/api/analytics/stale` | GET | Hae vanhentuneet muistit |
| `/api/analytics/cleanup` | POST | Siivoa vanhentuneet muistit |
| `/api/nodes/{uuid}` | DELETE | Poista solmu |
| `/api/episodes/{uuid}` | DELETE | Poista muistijakso |
| `/api/facts/{uuid}` | DELETE | Poista fakta |
| `/api/groups/{group_id}` | DELETE | Poista koko group |

## Konfiguraatio

### Ympäristömuuttujat (.env)

Konfiguraatio käyttää kerrostusmekanismia: JSON-konfiguraatiotiedosto on perusta, ja ympäristömuuttujat ohittavat yksittäiset arvot.

```bash
# === Pakollinen ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password        # Täytyy muuttaa

# === LLM-tarjoajan valinta ===
LLM_PROVIDER=ollama                 # ollama / glm / groq / openrouter / deepseek

# === Embedding-tarjoaja (valinnainen, oletuksena seuraa LLM_PROVIDERia) ===
# Vain glm käyttää GLM Embeddingiä, muut käyttävät aina Ollaman bge-m3:a
# EMBEDDING_PROVIDER=ollama         # ollama / glm

# === Ollama-konfiguraatio (käytetään kun LLM_PROVIDER=ollama) ===
OLLAMA_MODEL=qwen2.5:3b             # Päämalli (suositus qwen2.5:3b)
OLLAMA_SMALL_MODEL=qwen2.5:3b       # Pieni malli (yksinkertaisiin tehtäviin, voi olla eri malli)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.1

# === GLM-konfiguraatio (käytetään kun LLM_PROVIDER=glm) ===
GLM_API_KEY=your_api_key            # Hae osoitteesta https://open.bigmodel.cn
GLM_MODEL=glm-4-flash               # Ilmainen malli
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768

# === GROQ-konfiguraatio (käytetään kun LLM_PROVIDER=groq) ===
GROQ_API_KEY=your_api_key           # Hae osoitteesta https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile

# === OpenRouter-konfiguraatio (käytetään kun LLM_PROVIDER=openrouter) ===
OPENROUTER_API_KEY=your_api_key     # Hae osoitteesta https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free

# === DeepSeek-konfiguraatio (käytetään kun LLM_PROVIDER=deepseek) ===
DEEPSEEK_API_KEY=your_api_key       # Hae osoitteesta https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash    # Tai deepseek-v4-pro

# === Ollaman upotusmalli (käytetään aina, kun upotus ei ole glm) ===
OLLAMA_EMBEDDING_MODEL=bge-m3
OLLAMA_EMBEDDING_DIMENSIONS=768

# === Näyttö ja kieli (valinnainen) ===
GRAPHITI_DISPLAY_TIMEZONE=Asia/Taipei # API:n palauttaman aikaleiman näyttöaikavyöhyke (IANA-nimi; tallennus pysyy UTC:nä)
SERVER_LANG=zh-TW                     # MCP-työkalujen vastauskieli (täydellinen lokaali ks. src/i18n.py); REST API käyttää sen sijaan Accept-Languagea

# === Muistin suorituskyky (valinnainen) ===
GRAPHITI_CHUNK_THRESHOLD=800         # Älykkään paloittelun laukaiseva merkkimäärän kynnysarvo
GRAPHITI_MAX_CHUNK_SIZE=600          # Kunkin osan enimmäismerkkimäärä
GRAPHITI_MAX_COROUTINES=10            # Rinnakkaisten korutiinien enimmäismäärä
GRAPHITI_DEFAULT_BACKGROUND=false    # Käytetäänkö taustakäsittelyä oletuksena

# === Tärkeyden seuranta ja älykäs unohtaminen (valinnainen) ===
ENABLE_IMPORTANCE_TRACKING=true      # Ota käyttöseuranta käyttöön
IMPORTANCE_WEIGHT=0.1                # Tärkeyden paino
STALE_DAYS_THRESHOLD=30              # Vanhentumispäivien kynnysarvo
STALE_MIN_ACCESS_COUNT=2             # Vähimmäiskäyttömäärä

# === Lokit ===
LOG_FILE=logs/graphiti_mcp_server.log
LOG_LEVEL=INFO
```

> **Täydellinen ympäristömuuttujien luettelo** löytyy tiedostosta `.env.example`

### JSON-konfiguraatiotiedosto

Sopii konfiguraatiolle, joka tarvitsee versionhallintaa (ympäristömuuttujat voivat silti ohittaa):

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

## PM2-taustakäyttö

```bash
npm install -g pm2

pm2 start ecosystem.config.cjs      # Käynnistä
pm2 status                           # Tila
pm2 logs graphiti-mcp-http           # Reaaliaikaiset lokit
pm2 restart graphiti-mcp-http --update-env  # Käynnistä uudelleen (lataa .env uudelleen)

pm2 save && pm2 startup              # Aseta automaattinen käynnistys käynnistyksen yhteydessä
```

> **Vihje**: tiedoston `.env` muokkaamisen jälkeen on käynnistettävä uudelleen lipulla `--update-env`, muuten ympäristömuuttujia ei päivitetä.

## Docker-käyttöönotto

```bash
docker build -t graphiti-mcp .

# Huomautus: Docker-säiliön on pystyttävä yhdistämään Neo4j:hen ja Ollamaan
# Host network -verkon käyttö on yksinkertaisinta
docker run -p 8000:8000 --env-file .env --network host graphiti-mcp

# Tai määritä ulkoisten palveluiden osoitteet eksplisiittisesti
docker run -p 8000:8000 \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --env-file .env graphiti-mcp
```

## Testaus

```bash
# Suorita kaikki testit (183 kpl, noin 1 sekunti)
uv run python -m pytest tests/

# Yksityiskohtainen tuloste
uv run python -m pytest tests/ -v

# Suorita vain tietty testi
uv run python -m pytest tests/test_content_preprocessor.py -v
uv run python -m pytest tests/test_new_features.py -v
uv run python -m pytest tests/test_unit.py -v
```

> **Huomautus**: tiedoston `test_integration_manual.py` 3 async-testiä vaativat paketin `pytest-asyncio` asennuksen, ja sen puuttuessa ne näyttävät Failed mutta eivät vaikuta muihin testeihin. `bench_deepseek_flash_vs_pro.py` on suorituskyvyn vertailuskripti, ei yksikkötesti.

## Vianmääritys

### Neo4j-yhteys epäonnistuu

```bash
neo4j status                              # Tarkista palvelun tila
cypher-shell -u neo4j -p your_password    # Varmista, että salasana on oikein
curl http://localhost:7474                 # Varmista HTTP-portti
```

Yleiset syyt:
- Neo4j ei ole käynnistetty
- Väärä salasana (`NEO4J_PASSWORD` tiedostossa `.env`)
- Portti varattu tai palomuuri estää

### LLM-yhteys epäonnistuu

**Ollama-tila:**
```bash
ollama serve                # Käynnistä Ollama-palvelu
ollama list                 # Tarkista asennetut mallit
ollama pull qwen2.5:3b      # Asenna puuttuva malli
```

Yleiset syyt: Ollamaa ei ole käynnistetty, mallia ei ole asennettu, GPU-muisti ei riitä

**GLM-tila:**
- Varmista, että `GLM_API_KEY` on oikein
- Varmista `GLM_EMBEDDING_DIMENSIONS=768` (täytyy vastata Neo4j-vektori-indeksiä)
- GLM API -päätepiste: `https://open.bigmodel.cn/api/paas/v4/`

**GROQ-tila:**
- Varmista, että `GROQ_API_KEY` on oikein
- Jos nopeusrajoitukset toistuvat usein, harkitse vaihtoa GLM-tilaan
- GROQ ei tarjoa Embeddingiä, joten varmista, että Ollama-upotin on käytettävissä

**OpenRouter-tila:**
- Varmista, että `OPENROUTER_API_KEY` on oikein ja `OPENROUTER_MODEL` on kelvollinen mallin ID (ks. https://openrouter.ai/models)
- Ei tarjoa Embeddingiä, joten varmista, että Ollama-upotin on käytettävissä

**DeepSeek-tila:**
- Varmista, että `DEEPSEEK_API_KEY` on oikein
- Jos esiintyy `Prompt must contain the word 'json'`: tämä on DeepSeekin `json_object`-tilan ehdoton vaatimus, ja asiakas on jo varustettu sisäänrakennetulla varmistuksella; jos sitä silti esiintyy, varmista, että käytät uusinta versiota tiedostosta `src/deepseek_client.py` ja käynnistä palvelu uudelleen
- Ei tarjoa Embeddingiä, joten varmista, että Ollama-upotin on käytettävissä

### MCP-yhteysvirhe

Jos esiintyy `Invalid request parameters` tai `Received request before initialization was complete`:

1. Varmista, että käytät HTTP-siirtotilaa (**älä käytä SSE:tä**)
2. Varmista, että asiakas on asetettu arvoon `"type": "http"`, `"url": "http://localhost:8000/mcp"`
3. Käynnistä palvelu uudelleen: `pm2 restart graphiti-mcp-http --update-env`
4. Suorita Claude Codessa `/mcp` yhdistääksesi uudelleen

### Muistin lisäys on hidas

- **Ollama**: tarkista mallin koko (`qwen2.5:3b` on 5–10 kertaa nopeampi kuin `7b`), varmista GPU:n käyttö (`ollama ps`)
- **GLM**: jokainen add_episode vaatii 10–20+ LLM-verkkokyselyä, lyhyellä tekstillä ~22 s on normaali arvo
- **GROQ**: nopeusrajoitukset aiheuttavat paljon uudelleenyrityksiä, jos käyttö on toistuvaa, suositellaan vaihtoa GLM:ään tai Ollamaan
- Käytä `background=true` jumiutumisen välttämiseksi
- Pienennä arvoa `GRAPHITI_CHUNK_THRESHOLD`, jotta pitkä teksti paloitellaan aikaisemmin

### PM2-ongelmat

```bash
pm2 status                                        # Tarkista tila
pm2 logs graphiti-mcp-http --err --lines 50        # Virhelokit
lsof -i :8000                                     # Tarkista portin varaus
pm2 delete graphiti-mcp-http && pm2 start ecosystem.config.cjs  # Täydellinen uudelleenkäynnistys
```

## Kehityksen diagnostiikkatyökalut

```bash
uv run python tools/status_report.py           # Yhdistetty tilaraportti (Neo4j + Ollama + konfiguraatio)
uv run python tools/validate_config.py         # Validoi .env ja konfiguraation eheys
uv run python tools/performance_diagnose.py    # LLM-suorituskyvyn diagnostiikka
uv run python tools/inspect_schema.py          # Neo4j-indeksien ja -rajoitteiden tarkistus
uv run python tools/migrate_embeddings.py      # Embedding-mallin migraatio (vektorien uudelleenluonti mallin vaihdon jälkeen)
```

### Embedding-mallin migraatio

Embedding-mallin vaihdon jälkeen (esim. `nomic-embed-text` → `bge-m3`) voit käyttää migraatiotyökalua kaikkien olemassa olevien vektorien uudelleenluontiin varmistaaksesi yhtenäisen hakulaadun:

```bash
# Esikatsele migraatiota vaativaa määrää
uv run python tools/migrate_embeddings.py --dry-run

# Täysi migraatio (tukee katkospisteen jatkamista)
uv run python tools/migrate_embeddings.py

# Migroi vain määritetty group
uv run python tools/migrate_embeddings.py --group-id myproject

# Jatka katkospisteestä (uudelleenajo keskeytyksen jälkeen)
uv run python tools/migrate_embeddings.py --resume
```

> **Yhteensopivuus**: `bge-m3` on natiivisti 1024-ulotteinen, ja järjestelmä typistää sen automaattisesti 768-ulotteiseksi yhteensopivuuden vuoksi olemassa olevan Neo4j-vektori-indeksin kanssa. Migraatiota edeltävä ja sen jälkeinen data voivat olla rinnakkain, mutta on suositeltavaa suorittaa täysi migraatio parhaan hakulaadun saavuttamiseksi.

## Dokumentaatio

- [Työkalujen käyttöohjeet](../使用工具的指令.md) — MCP-työkalujen käyttöopas ja parhaat käytännöt
- [Graphiti Memory Rules](../graphiti-memory-rules.md) — Muistisääntöjen selitys

## Lisenssi

MIT License
