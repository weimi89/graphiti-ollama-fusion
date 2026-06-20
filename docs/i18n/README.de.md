# Graphiti MCP Server

Wissensgraph-Gedächtnisdienst — ein MCP-Server, der mehrere LLM-Anbieter (Ollama / GLM / GROQ / OpenRouter / DeepSeek) mit der Neo4j-Graphdatenbank integriert.

Entwickelt als Erweiterung auf Basis von [getzep/graphiti](https://github.com/getzep/graphiti), unterstützt flexibles Umschalten zwischen lokalem Ollama und Cloud-LLMs und ermöglicht die unabhängige Festlegung des Embedding-Anbieters (entkoppelt vom LLM).

## Funktionsmerkmale

- **Intelligente Gedächtnisverwaltung** — Speicherung und Abruf komplexer Gedächtnisbeziehungen mithilfe eines Wissensgraphen
- **Semantische Suche** — hybride Suche auf Basis von Vektor-Embeddings (Vektor + Schlüsselwort + Graphdurchlauf)
- **16 Suchstrategien** — die erweiterte Suche unterstützt RRF, MMR, Cross-Encoder und weitere Neusortierungsverfahren
- **Mehrere LLM-Anbieter** — Unterstützung für Ollama (lokal), GLM (Zhipu AI, kostenlos), GROQ (Hochgeschwindigkeitsinferenz), OpenRouter (aggregiert verschiedene Modelle) und DeepSeek; Umschalten per Umgebungsvariable mit einem Handgriff
- **Entkopplung von Embedding und LLM** — der Embedder kann über `EMBEDDING_PROVIDER` unabhängig festgelegt werden; Cloud-LLMs greifen automatisch auf das lokale `bge-m3` zurück
- **Zwei-Modell-Verteilung** — im Ollama-Modus werden für komplexe Aufgaben das Hauptmodell und für einfache Aufgaben automatisch ein kleines Modell verwendet, um die Leistung zu steigern
- **Intelligente Inhaltsaufteilung** — lange Texte werden automatisch in Abschnitte aufgeteilt, um die LLM-Last zu reduzieren (Schwellenwert konfigurierbar)
- **Hintergrundverarbeitung von Gedächtnis** — das Hinzufügen von Gedächtnis kann im Hintergrund ausgeführt werden, der MCP-Aufruf kehrt sofort zurück; der Aufgabenstatus wird in SQLite persistiert und unvollständige Aufgaben werden nach einem Neustart automatisch wiederhergestellt
- **Gedächtnis-Deduplizierung** — automatische Erkennung hochgradig ähnlicher vorhandener Gedächtnisinhalte zur Vermeidung doppelter Speicherung
- **Konflikterkennung** — Erkennung widersprüchlicher Fakten zwischen zwei Entitäten, Identifizierung bereits ungültiger und gültiger Informationen
- **Community-Erkennung** — automatische Clusterung verwandter Entitäten auf Basis des Label-Propagation-Algorithmus
- **Wichtigkeitsverfolgung** — automatische Erfassung der Zugriffshäufigkeit von Entitäten, Sortierung der Suchergebnisse nach Wichtigkeit
- **Intelligentes Vergessen** — Identifizierung und Bereinigung veralteter, selten zugegriffener Gedächtnisinhalte, um den Graphen schlank zu halten
- **Massenimport** — Übermittlung mehrerer Gedächtniseinträge auf einmal, geeignet für die Migration großer Datenmengen
- **Strukturierte Tripel** — direktes Hinzufügen von „Subjekt-Beziehung-Objekt“, überspringt die LLM-Extraktion und ist in Sekundenschnelle erledigt
- **Web-Verwaltungsoberfläche** — integriertes Dashboard, Durchsuchen, Suchen, Wissensgraph-Visualisierung, KI-Frage-Antwort, Community-Übersicht, Qualitätswartung, Massenimport, Laufzeitkonfiguration
- **Mehrsprachigkeit (i18n)** — Antwortnachrichten unterstützen 33 Sprachen (darunter zh-TW / en / zh-CN / ja / pt-BR / ko / es / de / fr usw.; zh-TW/en/zh-CN/ja handgeschrieben, die übrigen werden durch die Generated-Schicht bereitgestellt); MCP-Tools richten sich nach `SERVER_LANG`, REST API verhandelt automatisch über den HTTP-Header `Accept-Language`
- **Dunkles/helles Design** — die Web-Oberfläche unterstützt einen Designwechsel
- **Sicherer Modus** — optionales schnelles Hinzufügen von Gedächtnis unter Überspringung der Entitätsextraktion
- **Docker-Unterstützung** — integriertes Dockerfile, unterstützt containerisierte Bereitstellung
- **Nebenläufigkeitssicherheit** — asyncio.Lock schützt die Initialisierung und verhindert Wettlaufbedingungen
- **Mehrschichtige Gesundheitsprüfung** — `/health` (liveness) + `/health/ready` (readiness)

## Systemanforderungen

| Punkt | Anforderung |
|------|------|
| Python | 3.10+ (empfohlen 3.11+) |
| Neo4j | 4.0+ (`bolt://localhost:7687`) |
| LLM-Anbieter | Ollama / GLM / GROQ / OpenRouter / DeepSeek (eines von fünf) |
| Node.js | 18+ (nur für PM2-Hintergrundausführung, optional) |
| Speicherplatz | ~3 GB (Ollama-Modelle + Neo4j-Daten) |

### Auswahl des LLM-Anbieters

Umschalten über die Umgebungsvariable `LLM_PROVIDER` (`ollama` / `glm` / `groq` / `openrouter` / `deepseek`):

| Anbieter | Merkmale | LLM-Modell | Embedding | Geeignetes Szenario |
|--------|------|----------|-----------|----------|
| **Ollama** (Standard) | vollständig lokal, Daten verlassen den Rechner nicht | `qwen2.5:3b` | `bge-m3` (Chinesisch + RAG hervorragend) | mit GPU, Wert auf Datenschutz |
| **GLM** | kostenlose Cloud, stabil, ohne Drosselung | `glm-4-flash` (kostenlos) | `embedding-3` | ohne GPU, suchintensive Szenarien |
| **GROQ** | ultraschnelle Inferenz | `llama-3.3-70b-versatile` | Rückfall auf Ollama `bge-m3` | gelegentliches Schreiben, Qualitätsanspruch |
| **OpenRouter** | aggregiert verschiedene Modelle, inkl. Gratiskontingent | `stepfun/step-3.5-flash:free` usw. | Rückfall auf Ollama `bge-m3` | möchte bestimmte Cloud-Modelle nutzen |
| **DeepSeek** | DeepSeek-Cloud, hohes Preis-Leistungs-Verhältnis | `deepseek-v4-flash` / `deepseek-v4-pro` | Rückfall auf Ollama `bge-m3` | chinesisches Verständnis, kostengünstige Cloud |

> **Entkopplung von Embedding und LLM**: Der Embedder wird über `EMBEDDING_PROVIDER` (`ollama` / `glm`) unabhängig festgelegt; ist er nicht gesetzt, folgt er `LLM_PROVIDER`. Tatsächlich verwendet nur `glm` das GLM `embedding-3`, alle anderen (einschließlich Cloud-LLMs wie GROQ / OpenRouter / DeepSeek, die kein Embedding anbieten) verwenden automatisch Ollama `bge-m3`. **Daher wird bei Verwendung eines beliebigen Cloud-LLM weiterhin das lokale Ollama für den Embedding-Dienst benötigt (es sei denn, embedding ist ebenfalls auf glm gesetzt).**

#### Ollama-Modus (lokal)

```bash
# LLM-Hauptmodell (empfohlen qwen2.5:3b, beste Balance aus Geschwindigkeit und Stabilität)
ollama pull qwen2.5:3b

# Embedding-Modell (erforderlich, für die Vektorsuche)
ollama pull bge-m3
```

> **Hinweise zur Modellauswahl**:
> - `qwen2.5:3b` — empfohlen, ~2 s/Aufruf, ~100 t/s, strukturierte Ausgabe von graphiti-core zu 100 % stabil
> - `qwen2.5:7b` — bessere Ergebnisse, aber 5-10-mal langsamer, geeignet für Szenarien mit Qualitätsanspruch
> - `qwen2.5:1.5b` — am schnellsten, aber **instabil** (Erfolgsrate bei strukturiertem JSON nur 33 %), nicht empfohlen

#### GLM-Modus (Zhipu AI Cloud)

```bash
# .env-Einstellungen
LLM_PROVIDER=glm
GLM_API_KEY=your_api_key          # erhältlich unter https://open.bigmodel.cn
GLM_MODEL=glm-4-flash             # kostenloses Modell
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768      # muss mit der Dimension des Neo4j-Vektorindex übereinstimmen
```

> **GLM-Leistungsreferenz**: Schreiben ~22 s (kurzer Text), Suche ~0,34 s, null Rate-Limit-Fehler, 2-5-mal langsamer als lokales Ollama, aber vollständig kostenlos.

#### GROQ-Modus (Hochgeschwindigkeitsinferenz)

```bash
# .env-Einstellungen
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key         # erhältlich unter https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile
```

> **Hinweis**: GROQ bietet keinen Embedding-Dienst und muss mit dem Ollama-Embedder (automatischer Rückfall) kombiniert werden, oder `EMBEDDING_PROVIDER` ist auf glm zu setzen. GROQ hat ein striktes Rate-Limit; hochfrequente Nutzung löst zahlreiche Wiederholungsversuche aus.

#### OpenRouter-Modus (aggregiert verschiedene Modelle)

```bash
# .env-Einstellungen
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_api_key       # erhältlich unter https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free   # kann auf ein beliebiges OpenRouter-Modell geändert werden
```

> **Hinweis**: OpenRouter bietet kein Embedding, es erfolgt ein automatischer Rückfall auf Ollama `bge-m3`. Die Modellliste finden Sie unter https://openrouter.ai/models (enthält mehrere kostenlose `:free`-Modelle).

#### DeepSeek-Modus (DeepSeek)

```bash
# .env-Einstellungen
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key         # erhältlich unter https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash      # empfohlen; oder deepseek-v4-pro (bessere Ergebnisse)
```

> **Hinweis**: DeepSeek bietet kein Embedding, es erfolgt ein automatischer Rückfall auf Ollama `bge-m3`. `deepseek-chat` / `deepseek-reasoner` werden am 24.07.2026 abgeschaltet; es wird empfohlen, auf `deepseek-v4-flash` / `deepseek-v4-pro` umzusteigen. DeepSeek verlangt strikt, dass der Prompt im `json_object`-Modus die Zeichenfolge "json" enthält; der Client verfügt über einen integrierten Fallback-Schutz, sodass keine zusätzlichen Einstellungen erforderlich sind.

## Schnellstart

### 1. Vorbereitung

Stellen Sie sicher, dass Neo4j lokal läuft, und bereiten Sie je nach gewähltem LLM-Anbieter den entsprechenden Dienst vor:

```bash
# Sicherstellen, dass Neo4j läuft (erforderlich)
neo4j status
# Oder mit Docker: docker run -d -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/your_password neo4j:latest

# Ollama-Modus: sicherstellen, dass Ollama läuft
ollama list
# Falls nicht gestartet: ollama serve

# GLM-/GROQ-Modus: es wird nur ein gültiger API Key benötigt, kein lokaler Dienst
```

### 2. Abhängigkeiten installieren

```bash
git clone <repo-url>
cd graphiti
uv sync
```

> **Hinweis**: Dieses Projekt verwendet [uv](https://github.com/astral-sh/uv) zur Verwaltung der Abhängigkeiten. Falls nicht installiert: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 3. Umgebung konfigurieren

```bash
cp .env.example .env
```

Bearbeiten Sie `.env`; **mindestens** müssen folgende Punkte angepasst werden:

```bash
NEO4J_PASSWORD=your_actual_password  # erforderlich: Neo4j-Passwort
LLM_PROVIDER=ollama                  # ollama / glm / groq / openrouter / deepseek
OLLAMA_MODEL=qwen2.5:3b              # Ollama-Modus: lokales LLM-Modell
# GLM_API_KEY=your_key               # GLM-Modus: Zhipu AI API Key
# GROQ_API_KEY=your_key              # GROQ-Modus: GROQ API Key
# OPENROUTER_API_KEY=your_key        # OpenRouter-Modus: API Key
# DEEPSEEK_API_KEY=your_key          # DeepSeek-Modus: API Key
```

### 4. Dienst starten

```bash
# HTTP-Modus (empfohlen, enthält Web-Verwaltungsoberfläche)
uv run python graphiti_mcp_server.py --transport http --port 8000

# Oder PM2-Hintergrundausführung (empfohlen für Dauerbetrieb)
pm2 start ecosystem.config.cjs
```

### 5. Dienst überprüfen

Nach dem Start können folgende Endpunkte aufgerufen werden:

| Endpunkt | Beschreibung |
|------|------|
| http://localhost:8000/ | Web-Verwaltungsoberfläche |
| http://localhost:8000/mcp | MCP-Endpunkt (für die Verbindung von MCP-Clients) |
| http://localhost:8000/health | Gesundheitsprüfung (liveness) |
| http://localhost:8000/health/ready | Tiefenprüfung (inkl. Neo4j-Verbindung) |
| http://localhost:8000/api/stats | REST-API-Statistik |

## Projektstruktur

```
graphiti/
├── graphiti_mcp_server.py        # Haupteinstieg — MCP-Tool-Definitionen (19 Tools)
├── src/
│   ├── config.py                 # Konfigurationsverwaltung (GraphitiConfig, unterstützt JSON/.env-Schichtung)
│   ├── web_api.py                # REST API der Web-Verwaltungsoberfläche (30+ Endpunkte)
│   ├── ollama_graphiti_client.py  # Ollama-LLM-Client (Zwei-Modell-Verteilung)
│   ├── openai_compat_client.py   # OpenAI-kompatibler LLM-Basisklasse (json_object + vereinfachtes Schema + json-Fallback-Schutz)
│   ├── glm_client.py             # GLM-(Zhipu AI)-LLM-Client (erbt von OpenAICompatClient)
│   ├── openrouter_client.py      # OpenRouter-LLM-Client (erbt von OpenAICompatClient)
│   ├── deepseek_client.py        # DeepSeek-LLM-Client (erbt von OpenAICompatClient)
│   ├── ollama_embedder.py        # Ollama-Embedding-Modell-Adapter
│   ├── content_preprocessor.py   # intelligente Inhaltsaufteilung (lange Texte automatisch in Abschnitte teilen)
│   ├── deduplication.py          # Gedächtnis-Deduplizierung (Kosinus-Ähnlichkeitsvergleich)
│   ├── importance.py             # Wichtigkeitsverfolgung und intelligentes Vergessen
│   ├── safe_memory_add.py        # sicheres Hinzufügen von Gedächtnis (überspringt Entitätsextraktion)
│   ├── task_store.py             # SQLite-Persistierung von Hintergrundaufgaben (TaskStore)
│   ├── timezone_utils.py         # Zeitzonenkonvertierung (UTC→Anzeige in lokaler Zeitzone)
│   ├── i18n.py                   # Backend-Mehrsprachigkeit (REST nach Accept-Language, MCP nach SERVER_LANG)
│   ├── i18n_generated.py         # automatisch generierte Sprachüberschreibungen (GENERATED_MESSAGE_OVERRIDES)
│   ├── exceptions.py             # strukturierte Ausnahmebehandlung (12 Ausnahmeklassen)
│   └── logging_setup.py          # Logging-System (zeitbasierte Rotation + Leistungsüberwachung)
├── web/                          # Frontend der Web-Verwaltungsoberfläche (SPA, kein Build)
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js                # REST-API-Kapselung
│       ├── components.js         # Rendering der UI-Komponenten (inkl. Community-Seite)
│       └── app.js                # SPA-Routing, Zustandsverwaltung
├── tests/                        # Testsuite (203 Tests)
│   ├── test_content_preprocessor.py  # Tests der Aufteilungslogik (17 Tests)
│   ├── test_new_features.py      # Tests neuer Funktionen (32 Tests)
│   ├── test_i18n.py             # Mehrsprachigkeitstests (57 Tests)
│   ├── test_unit.py              # Unit-Tests
│   ├── test_web_api.py           # Web-API-Tests
│   ├── test_web_ui_features.py   # Tests der Web-UI-Funktionen
│   ├── test_integration_manual.py # manuelle Integrationstests
│   └── bench_deepseek_flash_vs_pro.py # DeepSeek-flash/pro-Leistungs-Benchmark-Skript
├── tools/                        # Entwicklungs- und Diagnosewerkzeuge
│   ├── status_report.py          # zusammenfassender Statusbericht
│   ├── validate_config.py        # Konfigurationsvalidierung
│   ├── performance_diagnose.py   # Leistungsdiagnose
│   ├── inspect_schema.py         # Neo4j-Strukturprüfung
│   ├── batch_reprocess.py        # Stapelweise Neuverarbeitung
│   └── migrate_embeddings.py     # Embedding-Modell-Migration (Vektoren nach Modellwechsel neu generieren)
├── docs/                         # Dokumentation
├── logs/                         # Logs (zeitbasierte Rotation, standardmäßig 30 Tage aufbewahrt)
├── Dockerfile                    # containerisierte Docker-Bereitstellung
└── ecosystem.config.cjs          # PM2-Konfiguration
```

## MCP-Client-Konfiguration

### HTTP-Modus (empfohlen)

Geeignet für MCP-Clients mit HTTP-Unterstützung wie Claude Code, Cline usw.:

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

### STDIO-Modus

Geeignet für Clients, die den Prozess direkt starten müssen, wie Claude Desktop:

**Speicherort der Konfigurationsdatei:**
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

> **Hinweis**: Der SSE-Modus (`--transport sse`) wird nicht mehr empfohlen. MCP 1.x hat Kompatibilitätsprobleme bei der Session-Initialisierung; verwenden Sie stattdessen den HTTP-Modus.

## MCP-Tools (19 Stück)

### Gedächtnisverwaltung (7 Stück)

| Tool | Beschreibung |
|------|------|
| `add_memory_simple` | Gedächtnis zum Wissensgraphen hinzufügen (unterstützt Hintergrundverarbeitung, intelligente Aufteilung, Deduplizierungsprüfung) |
| `add_episode_bulk` | mehrere Gedächtniseinträge stapelweise hinzufügen (standardmäßig Hintergrundverarbeitung) |
| `add_triplet` | Hinzufügen strukturierter Tripel (überspringt LLM, in Sekundenschnelle erledigt) |
| `search_memory_nodes` | Gedächtnisknoten suchen (unterstützt 16 Suchstrategien, Zeitfilterung) |
| `search_memory_facts` | Gedächtnisfakten suchen (unterstützt Filterung nach Beziehungstyp, Zeitbereich, Gültigkeit) |
| `advanced_search` | erweiterte Suche (16 Strategien, gibt Knoten + Kanten + Communitys + Episoden zurück) |
| `get_episodes` | die neuesten Gedächtnisepisoden abrufen |

### Wissensanalyse (3 Stück)

| Tool | Beschreibung |
|------|------|
| `check_conflicts` | Faktenkonflikte zwischen zwei Entitäten erkennen (gültig vs. ungültig) |
| `get_node_edges` | die ein- und ausgehenden Kantenbeziehungen eines Knotens erkunden |
| `build_communities` | Community-Erkennung und -Clusterung auslösen (standardmäßig Hintergrundverarbeitung) |

### Gedächtniswartung (2 Stück)

| Tool | Beschreibung |
|------|------|
| `get_stale_memories` | veraltete, selten zugegriffene Gedächtnisinhalte abfragen |
| `cleanup_stale_memories` | veraltete Gedächtnisinhalte bereinigen (standardmäßig dry_run-Vorschaumodus) |

### Aufgabenverwaltung

| Tool | Beschreibung |
|------|------|
| `get_memory_task_status` | Fortschritt und Ergebnis einer Hintergrund-Gedächtnisverarbeitungsaufgabe abfragen |

### Löschen und Abfragen

| Tool | Beschreibung |
|------|------|
| `delete_episode` | Gedächtnisepisode löschen |
| `delete_entity_edge` | Entitätskante (Beziehung) löschen |
| `get_entity_edge` | Detailinformationen einer Entitätskante abrufen |

### Systemverwaltung

| Tool | Beschreibung |
|------|------|
| `get_status` | Dienststatus abrufen (Neo4j, LLM, Embedder) |
| `test_connection` | Verbindung zu Neo4j / LLM / Embedder testen |
| `clear_graph` | Graphdatenbank leeren (unterstützt Leeren nach group_id) |

## Tool-Parameter

### add_memory_simple

| Parameter | Typ | Erforderlich | Standardwert | Beschreibung |
|------|------|------|--------|------|
| `name` | string | Y | | Name des Gedächtnisses |
| `episode_body` | string | Y | | Gedächtnisinhalt (über 800 Zeichen automatische Aufteilung) |
| `group_id` | string | | `"default"` | Gruppen-ID (empfohlen, nach Projekt zu isolieren) |
| `source` | string | | `"text"` | Quelltyp: `text` / `json` / `message` |
| `source_description` | string | | `"MCP Server"` | Quellenbeschreibung |
| `use_safe_mode` | bool | | `false` | sicherer Modus (überspringt Entitätsextraktion, schnell, aber Gedächtnis nicht durchsuchbar) |
| `background` | bool | | `false` | Hintergrundverarbeitung (gibt sofort task_id zurück, geeignet für lange Texte) |
| `force` | bool | | `false` | Deduplizierungsprüfung überspringen (erzwungenes Hinzufügen) |
| `excluded_entity_types` | list | | | ausgeschlossene Entitätstypen (reduziert unerwünschte Extraktionsmenge) |

> **Leistungstipps**:
> - Kurze Texte (<800 Zeichen): direkte Verarbeitung, üblicherweise in 30-40 Sekunden abgeschlossen
> - Lange Texte (>800 Zeichen): automatische Aufteilung in mehrere Abschnitte, nebenläufige Verarbeitung mit `add_episode_bulk` (~33 % schneller als seriell)
> - Mit `background=true` lässt sich eine Blockierung des MCP-Aufrufs vermeiden; der Fortschritt wird über `get_memory_task_status` verfolgt
> - `use_safe_mode=true` ist in Sekundenschnelle erledigt, aber das Gedächtnis kann von den Such-Tools nicht gefunden werden
> - Bei aktivierter Deduplizierung wird bei hochgradig ähnlichem Gedächtnis eine Warnung ausgegeben (`force=true` überspringt diese)

### add_episode_bulk

| Parameter | Typ | Erforderlich | Standardwert | Beschreibung |
|------|------|------|--------|------|
| `episodes` | list | Y | | Liste von Gedächtniseinträgen, jeder mit `name` und `content` |
| `group_id` | string | | `"default"` | Gruppen-ID |
| `source` | string | | `"text"` | Quelltyp |
| `background` | bool | | `true` | Hintergrundverarbeitung (Stapelverarbeitung ist üblicherweise zeitaufwendig) |

### add_triplet

| Parameter | Typ | Erforderlich | Standardwert | Beschreibung |
|------|------|------|--------|------|
| `source_name` | string | Y | | Name der Quellentität (z. B. "Alice") |
| `target_name` | string | Y | | Name der Zielentität (z. B. "Google") |
| `relation_name` | string | Y | | Beziehungsname (z. B. "works_at") |
| `fact` | string | Y | | Faktenbeschreibung (z. B. "Alice works at Google") |
| `group_id` | string | | `"default"` | Gruppen-ID |
| `source_labels` | list | | | Labels der Quellentität |
| `target_labels` | list | | | Labels der Zielentität |

### search_memory_nodes

| Parameter | Typ | Erforderlich | Standardwert | Beschreibung |
|------|------|------|--------|------|
| `query` | string | Y | | Suchschlüsselwort (natürliche Sprache) |
| `max_nodes` | int | | `10` | maximale Rückgabeanzahl |
| `group_ids` | list | | | Gruppenfilterung (gemeinsame Suche über mehrere Gruppen) |
| `entity_types` | list | | | Filterung nach Entitätstyp |
| `search_recipe` | string | | | Suchstrategie (siehe erweiterte Suche) |
| `created_after` | string | | | Untergrenze der Erstellungszeit (ISO datetime) |
| `created_before` | string | | | Obergrenze der Erstellungszeit (ISO datetime) |

### search_memory_facts

| Parameter | Typ | Erforderlich | Standardwert | Beschreibung |
|------|------|------|--------|------|
| `query` | string | Y | | Suchschlüsselwort |
| `max_facts` | int | | `10` | maximale Rückgabeanzahl |
| `group_ids` | list | | | Gruppenfilterung |
| `center_node_uuid` | string | | | UUID des Mittelpunktknotens (Beziehungen eines bestimmten Knotens erkunden) |
| `edge_types` | list | | | Filterung nach Beziehungstyp (z. B. `["works_at"]`) |
| `created_after` | string | | | Untergrenze der Erstellungszeit (ISO datetime) |
| `created_before` | string | | | Obergrenze der Erstellungszeit (ISO datetime) |
| `only_valid` | bool | | `false` | nur nicht ungültige Fakten zurückgeben |

### advanced_search

| Parameter | Typ | Erforderlich | Standardwert | Beschreibung |
|------|------|------|--------|------|
| `query` | string | Y | | Suchschlüsselwort |
| `search_recipe` | string | | `"combined_rrf"` | Suchstrategie (16 zur Auswahl) |
| `max_results` | int | | `10` | maximale Rückgabeanzahl |
| `group_ids` | list | | | Gruppenfilterung |
| `center_node_uuid` | string | | | UUID des Mittelpunktknotens |

**Verfügbare Suchstrategien (search_recipe):**

| Kategorie | Strategie | Beschreibung |
|------|------|------|
| Kombiniert | `combined_rrf` | kombinierte RRF-Fusion (Standard, empfohlen) |
| Kombiniert | `combined_mmr` | kombinierte MMR-Diversitäts-Neusortierung |
| Kombiniert | `combined_cross_encoder` | kombinierte Cross-Encoder-Feinsortierung |
| Kante | `edge_rrf` / `edge_mmr` / `edge_cross_encoder` | Kantensuche (3 Sortierungen) |
| Kante | `edge_node_distance` / `edge_episode_mentions` | Kantensuche (Graphdistanz/Anzahl der Erwähnungen) |
| Knoten | `node_rrf` / `node_mmr` / `node_cross_encoder` | Knotensuche (3 Sortierungen) |
| Knoten | `node_node_distance` / `node_episode_mentions` | Knotensuche (Graphdistanz/Anzahl der Erwähnungen) |
| Community | `community_rrf` / `community_mmr` / `community_cross_encoder` | Community-Suche |

### check_conflicts

| Parameter | Typ | Erforderlich | Standardwert | Beschreibung |
|------|------|------|--------|------|
| `source_name` | string | Y | | Name der Quellentität |
| `target_name` | string | Y | | Name der Zielentität |
| `group_id` | string | | `"default"` | Gruppen-ID |

### get_node_edges

| Parameter | Typ | Erforderlich | Standardwert | Beschreibung |
|------|------|------|--------|------|
| `node_uuid` | string | Y | | Knoten-UUID |
| `include_inbound` | bool | | `true` | eingehende Kanten einbeziehen |
| `include_outbound` | bool | | `true` | ausgehende Kanten einbeziehen |
| `max_edges` | int | | `50` | maximale Rückgabeanzahl |

### build_communities

| Parameter | Typ | Erforderlich | Standardwert | Beschreibung |
|------|------|------|--------|------|
| `group_ids` | list | | | angegebene Gruppen (leer lassen für alle) |
| `background` | bool | | `true` | Hintergrundverarbeitung |

### get_stale_memories

| Parameter | Typ | Erforderlich | Standardwert | Beschreibung |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | wie viele Tage ohne Zugriff als veraltet gelten |
| `min_access_count` | int | | `2` | wird nur einbezogen, wenn die Zugriffsanzahl unter diesem Wert liegt |
| `group_id` | string | | | Gruppenfilterung |
| `limit` | int | | `50` | maximale Rückgabeanzahl |

### cleanup_stale_memories

| Parameter | Typ | Erforderlich | Standardwert | Beschreibung |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Schwellenwert für Veraltungstage |
| `min_access_count` | int | | `2` | Schwellenwert für minimale Zugriffsanzahl |
| `group_id` | string | | | Gruppenfilterung |
| `dry_run` | bool | | `true` | Vorschaumodus (löscht nicht tatsächlich) |
| `limit` | int | | `50` | maximale Verarbeitungsanzahl |

### get_memory_task_status

| Parameter | Typ | Erforderlich | Beschreibung |
|------|------|------|------|
| `task_id` | string | Y | ID der Hintergrundaufgabe (zurückgegeben von `add_memory_simple(background=true)`) |

## Web-Verwaltungsoberfläche

Im HTTP-Modus unter `http://localhost:8000/` aufrufbar und nutzbar.

**Funktionen:**
- Dashboard — Statistik über Knotenanzahl, Faktenanzahl, Gedächtnisepisodenanzahl
- Entitätsknoten — durchsuchen, filtern, Vektorsuche
- Faktenbeziehungen — durchsuchen, filtern, Vektorsuche
- Gedächtnisepisoden — durchsuchen, Volltextsuche, löschen
- Community-Übersicht — Liste der Community-Knoten, Zusammenfassungen, Community-Aufbau auslösen
- Tripel-Formular — direktes Hinzufügen von strukturiertem Wissen „Subjekt-Beziehung-Objekt”
- Group-Verwaltung — nach Gruppe filtern, stapelweise löschen
- Wissensgraph-Visualisierung — grafische Darstellung von Knotenbeziehungen
- KI-Frage-Antwort — intelligente Frage-Antwort auf Basis des Wissensgraphen
- Qualitätswartung — Gedächtnisqualitätskennzahlen und Bereinigungswerkzeuge
- Massenimport — mehrere Gedächtnisepisoden auf einmal importieren (JSON, max. 500 Einträge pro Vorgang)
- Laufzeitkonfiguration — aktuelle Einstellungen anzeigen und bestimmte Parameter ohne Neustart anpassen
- Designwechsel — dunkles/helles Design

**REST API:**

| Endpunkt | Methode | Beschreibung |
|------|------|------|
| `/api/stats` | GET | Dashboard-Statistik |
| `/api/groups` | GET | alle group_id abrufen |
| `/api/groups/stats` | GET | Knoten-/Fakten-/Episodenstatistik pro Gruppe |
| `/api/nodes` | GET | Entitätsknoten durchsuchen (paginiert) |
| `/api/facts` | GET | Fakten durchsuchen (paginiert) |
| `/api/episodes` | GET | Gedächtnisepisoden durchsuchen (paginiert) |
| `/api/nodes/{uuid}/relations` | GET | Ein- und ausgehende Beziehungen eines Knotens abrufen |
| `/api/search/nodes` | GET | Vektorsuche nach Knoten |
| `/api/search/facts` | GET | Vektorsuche nach Fakten |
| `/api/search/episodes` | GET | Gedächtnisepisoden suchen |
| `/api/search/advanced` | GET | erweiterte Suche (16 Strategien) |
| `/api/communities` | GET | Community-Knoten durchsuchen (paginiert) |
| `/api/communities/build` | POST | Community-Aufbau auslösen |
| `/api/memory/add` | POST | einzelnes Gedächtnis hinzufügen |
| `/api/memory/add-bulk` | POST | Gedächtnis stapelweise hinzufügen |
| `/api/memory/add-triplet` | POST | Tripel hinzufügen |
| `/api/import/episodes` | POST | Gedächtnisepisoden massenweise importieren (JSON, max. 500 Einträge) |
| `/api/memory/tasks` | GET | Hintergrundaufgaben auflisten (unterstützt Statusfilterung) |
| `/api/memory/tasks/{id}` | GET | Status einer einzelnen Aufgabe abfragen |
| `/api/timeline` | GET | Zeitachsenansicht |
| `/api/graph/subgraph` | GET | Teilgraph abrufen (Visualisierung) |
| `/api/graph/all` | GET | vollständigen Graphen abrufen (Visualisierung) |
| `/api/ask` | GET | KI-Frage-Antwort (auf Basis der Graphsuche) |
| `/api/analytics/top-nodes` | GET | Knoten mit hoher Vernetzung/hohem Zugriff |
| `/api/analytics/quality` | GET | Qualitätskennzahlen des Wissensgraphen |
| `/api/analytics/stale` | GET | veraltete Gedächtnisinhalte abfragen |
| `/api/analytics/cleanup` | POST | veraltete Gedächtnisinhalte bereinigen |
| `/api/config` | GET | aktuelle Einstellungen abrufen (ohne API-Keys) |
| `/api/config` | PATCH | Einstellungen zur Laufzeit aktualisieren (gilt nur für den laufenden Prozess, wird nach Neustart zurückgesetzt) |
| `/api/nodes/{uuid}` | DELETE | Knoten löschen |
| `/api/episodes/{uuid}` | DELETE | Gedächtnisepisode löschen |
| `/api/facts/{uuid}` | DELETE | Fakt löschen |
| `/api/groups/{group_id}` | DELETE | gesamte Group löschen |

## Konfiguration

### Umgebungsvariablen (.env)

Die Konfiguration verwendet einen Schichtungsmechanismus: Die JSON-Konfigurationsdatei bildet die Grundlage, Umgebungsvariablen überschreiben einzelne Werte.

```bash
# === Erforderlich ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password        # muss geändert werden

# === Auswahl des LLM-Anbieters ===
LLM_PROVIDER=ollama                 # ollama / glm / groq / openrouter / deepseek

# === Embedding-Anbieter (optional, folgt standardmäßig LLM_PROVIDER) ===
# Nur glm verwendet GLM Embedding, alle anderen verwenden Ollama bge-m3
# EMBEDDING_PROVIDER=ollama         # ollama / glm

# === Ollama-Konfiguration (verwendet bei LLM_PROVIDER=ollama) ===
OLLAMA_MODEL=qwen2.5:3b             # Hauptmodell (empfohlen qwen2.5:3b)
OLLAMA_SMALL_MODEL=qwen2.5:3b       # kleines Modell (für einfache Aufgaben, kann ein anderes Modell sein)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.1

# === GLM-Konfiguration (verwendet bei LLM_PROVIDER=glm) ===
GLM_API_KEY=your_api_key            # erhältlich unter https://open.bigmodel.cn
GLM_MODEL=glm-4-flash               # kostenloses Modell
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768

# === GROQ-Konfiguration (verwendet bei LLM_PROVIDER=groq) ===
GROQ_API_KEY=your_api_key           # erhältlich unter https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile

# === OpenRouter-Konfiguration (verwendet bei LLM_PROVIDER=openrouter) ===
OPENROUTER_API_KEY=your_api_key     # erhältlich unter https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free

# === DeepSeek-Konfiguration (verwendet bei LLM_PROVIDER=deepseek) ===
DEEPSEEK_API_KEY=your_api_key       # erhältlich unter https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash    # oder deepseek-v4-pro

# === Ollama-Embedding-Modell (wird bei jedem Embedding außer glm verwendet) ===
OLLAMA_EMBEDDING_MODEL=bge-m3
OLLAMA_EMBEDDING_DIMENSIONS=768

# === Anzeige und Sprache (optional) ===
GRAPHITI_DISPLAY_TIMEZONE=Asia/Taipei # Anzeigezeitzone der von der API zurückgegebenen Zeitstempel (IANA-Name; Speicherung bleibt UTC)
SERVER_LANG=zh-TW                     # Antwortsprache der MCP-Tools (vollständige Locales siehe src/i18n.py); REST API richtet sich nach Accept-Language

# === Gedächtnisleistung (optional) ===
GRAPHITI_CHUNK_THRESHOLD=800         # Zeichenanzahl-Schwellenwert zum Auslösen der intelligenten Aufteilung
GRAPHITI_MAX_CHUNK_SIZE=600          # maximale Zeichenanzahl pro Abschnitt
GRAPHITI_MAX_COROUTINES=10            # maximale Anzahl paralleler Koroutinen
GRAPHITI_DEFAULT_BACKGROUND=false    # ob standardmäßig im Hintergrund verarbeitet wird
TASK_DB_PATH=data/tasks.db           # SQLite-Persistierungspfad für Hintergrundaufgaben

# === Wichtigkeitsverfolgung und intelligentes Vergessen (optional) ===
ENABLE_IMPORTANCE_TRACKING=true      # Zugriffsverfolgung aktivieren
IMPORTANCE_WEIGHT=0.1                # Wichtigkeitsgewicht
STALE_DAYS_THRESHOLD=30              # Schwellenwert für Veraltungstage
STALE_MIN_ACCESS_COUNT=2             # minimale Zugriffsanzahl

# === Logging ===
LOG_FILE=logs/graphiti_mcp_server.log
LOG_LEVEL=INFO
```

> **Die vollständige Liste der Umgebungsvariablen** finden Sie in `.env.example`

### JSON-Konfigurationsdatei

Geeignet für Konfigurationen, die versioniert werden müssen (Umgebungsvariablen können weiterhin überschreiben):

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

## PM2-Hintergrundausführung

```bash
npm install -g pm2

pm2 start ecosystem.config.cjs      # starten
pm2 status                           # Status
pm2 logs graphiti-mcp-http           # Echtzeit-Logs
pm2 restart graphiti-mcp-http --update-env  # neu starten (.env neu laden)

pm2 save && pm2 startup              # automatischen Start beim Booten einrichten
```

> **Hinweis**: Nach Änderung von `.env` muss mit dem Flag `--update-env` neu gestartet werden, sonst werden die Umgebungsvariablen nicht aktualisiert.

## Docker-Bereitstellung

```bash
docker build -t graphiti-mcp .

# Hinweis: Der Docker-Container muss sich mit Neo4j und Ollama verbinden können
# Die Verwendung des host network ist am einfachsten
docker run -p 8000:8000 --env-file .env --network host graphiti-mcp

# Oder die Adresse der externen Dienste explizit angeben
docker run -p 8000:8000 \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --env-file .env graphiti-mcp
```

## Tests

```bash
# Alle Tests ausführen (203 Stück, ca. 1 Sekunde)
uv run python -m pytest tests/

# Ausführliche Ausgabe
uv run python -m pytest tests/ -v

# Nur einen bestimmten Test ausführen
uv run python -m pytest tests/test_content_preprocessor.py -v
uv run python -m pytest tests/test_new_features.py -v
uv run python -m pytest tests/test_unit.py -v
```

> **Hinweis**: Die 3 async-Tests in `test_integration_manual.py` erfordern die Installation von `pytest-asyncio`; fehlt diese, werden sie als Failed angezeigt, beeinträchtigen aber die anderen Tests nicht. `bench_deepseek_flash_vs_pro.py` ist ein Leistungs-Benchmark-Skript und kein Unit-Test.

## Fehlerbehebung

### Neo4j-Verbindung fehlgeschlagen

```bash
neo4j status                              # Dienststatus prüfen
cypher-shell -u neo4j -p your_password    # Passwort auf Korrektheit prüfen
curl http://localhost:7474                 # HTTP-Port prüfen
```

Häufige Ursachen:
- Neo4j ist nicht gestartet
- falsches Passwort (`NEO4J_PASSWORD` in `.env`)
- Port belegt oder durch Firewall blockiert

### LLM-Verbindung fehlgeschlagen

**Ollama-Modus:**
```bash
ollama serve                # Ollama-Dienst starten
ollama list                 # installierte Modelle prüfen
ollama pull qwen2.5:3b      # fehlendes Modell installieren
```

Häufige Ursachen: Ollama nicht gestartet, Modell nicht installiert, unzureichender GPU-Speicher

**GLM-Modus:**
- `GLM_API_KEY` auf Korrektheit prüfen
- `GLM_EMBEDDING_DIMENSIONS=768` prüfen (muss mit dem Neo4j-Vektorindex übereinstimmen)
- GLM-API-Endpunkt: `https://open.bigmodel.cn/api/paas/v4/`

**GROQ-Modus:**
- `GROQ_API_KEY` auf Korrektheit prüfen
- Bei häufigem Rate-Limit erwägen, in den GLM-Modus zu wechseln
- GROQ bietet kein Embedding; stellen Sie sicher, dass der Ollama-Embedder verfügbar ist

**OpenRouter-Modus:**
- `OPENROUTER_API_KEY` auf Korrektheit prüfen, `OPENROUTER_MODEL` muss eine gültige Modell-ID sein (siehe https://openrouter.ai/models)
- bietet kein Embedding; stellen Sie sicher, dass der Ollama-Embedder verfügbar ist

**DeepSeek-Modus:**
- `DEEPSEEK_API_KEY` auf Korrektheit prüfen
- Falls `Prompt must contain the word 'json'` erscheint: Dies ist eine zwingende Anforderung des DeepSeek-`json_object`-Modus; der Client verfügt über einen integrierten Fallback-Schutz. Tritt es dennoch auf, stellen Sie sicher, dass die neueste Version von `src/deepseek_client.py` verwendet wird, und starten Sie den Dienst neu
- bietet kein Embedding; stellen Sie sicher, dass der Ollama-Embedder verfügbar ist

### MCP-Verbindungsfehler

Wenn `Invalid request parameters` oder `Received request before initialization was complete` erscheint:

1. Stellen Sie sicher, dass der HTTP-Transportmodus verwendet wird (**nicht SSE verwenden**)
2. Stellen Sie sicher, dass der Client auf `"type": "http"`, `"url": "http://localhost:8000/mcp"` eingestellt ist
3. Dienst neu starten: `pm2 restart graphiti-mcp-http --update-env`
4. In Claude Code `/mcp` ausführen, um die Verbindung neu herzustellen

### Hinzufügen von Gedächtnis ist langsam

- **Ollama**: Modellgröße prüfen (`qwen2.5:3b` ist 5-10-mal schneller als `7b`), GPU-Nutzung sicherstellen (`ollama ps`)
- **GLM**: jedes add_episode benötigt 10-20+ LLM-Netzwerk-Roundtrips, ~22 s bei kurzem Text ist ein Normalwert
- **GROQ**: Rate-Limit führt zu zahlreichen Wiederholungsversuchen; bei häufiger Nutzung wird empfohlen, zu GLM oder Ollama zu wechseln
- Mit `background=true` Blockierung vermeiden
- `GRAPHITI_CHUNK_THRESHOLD` verringern, damit lange Texte früher aufgeteilt werden

### PM2-Probleme

```bash
pm2 status                                        # Status prüfen
pm2 logs graphiti-mcp-http --err --lines 50        # Fehler-Logs
lsof -i :8000                                     # Portbelegung prüfen
pm2 delete graphiti-mcp-http && pm2 start ecosystem.config.cjs  # vollständiger Neustart
```

## Entwicklungs- und Diagnosewerkzeuge

```bash
uv run python tools/status_report.py           # zusammenfassender Statusbericht (Neo4j + Ollama + Konfiguration)
uv run python tools/validate_config.py         # .env und Konfigurationsvollständigkeit validieren
uv run python tools/performance_diagnose.py    # LLM-Leistungsdiagnose
uv run python tools/inspect_schema.py          # Neo4j-Index- und Constraint-Prüfung
uv run python tools/migrate_embeddings.py      # Embedding-Modell-Migration (Vektoren nach Modellwechsel neu generieren)
```

### Embedding-Modell-Migration

Nach dem Wechsel des Embedding-Modells (z. B. `nomic-embed-text` → `bge-m3`) können mit dem Migrationswerkzeug alle vorhandenen Vektoren neu generiert werden, um eine konsistente Suchqualität sicherzustellen:

```bash
# Anzahl der zu migrierenden Einträge in der Vorschau anzeigen
uv run python tools/migrate_embeddings.py --dry-run

# Vollständige Migration (unterstützt Wiederaufnahme nach Unterbrechung)
uv run python tools/migrate_embeddings.py

# Nur eine bestimmte Group migrieren
uv run python tools/migrate_embeddings.py --group-id myproject

# Vom Haltepunkt fortsetzen (nach Unterbrechung erneut ausführen)
uv run python tools/migrate_embeddings.py --resume
```

> **Kompatibilität**: `bge-m3` ist nativ 1024-dimensional; das System schneidet automatisch auf 768 Dimensionen zu, um mit vorhandenen Neo4j-Vektorindizes kompatibel zu sein. Daten vor und nach der Migration können koexistieren, es wird jedoch empfohlen, eine vollständige Migration durchzuführen, um die beste Suchqualität zu erzielen.

## Dokumentation

- [Anweisungen zur Werkzeugnutzung](../使用工具的指令.md) — Leitfaden und bewährte Praktiken zur Nutzung der MCP-Tools
- [Graphiti Memory Rules](../graphiti-memory-rules.md) — Erläuterung der Gedächtnisregeln

## Lizenz

MIT License
