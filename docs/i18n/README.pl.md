# Graphiti MCP Server

Usługa pamięci grafu wiedzy — serwer MCP integrujący wielu dostawców LLM (Ollama / GLM / GROQ / OpenRouter / DeepSeek) z bazą grafową Neo4j.

Rozwinięty na bazie [getzep/graphiti](https://github.com/getzep/graphiti), obsługuje elastyczne przełączanie między lokalnym Ollama a chmurowymi LLM oraz pozwala niezależnie wskazać dostawcę Embedding (odsprzężony od LLM).

## Funkcje wyróżniające

- **Inteligentne zarządzanie pamięcią** — wykorzystuje graf wiedzy do przechowywania i odzyskiwania złożonych relacji pamięci
- **Wyszukiwanie semantyczne** — hybrydowe wyszukiwanie oparte na osadzeniach wektorowych (wektory + słowa kluczowe + przechodzenie grafu)
- **16 strategii wyszukiwania** — zaawansowane wyszukiwanie obsługuje RRF, MMR, Cross-Encoder i wiele innych metod ponownego rankingu
- **Wielu dostawców LLM** — obsługa Ollama (lokalnie), GLM (智谱 AI, darmowy), GROQ (szybkie wnioskowanie), OpenRouter (agregacja modeli różnych dostawców), DeepSeek (深度求索), przełączanie jednym kliknięciem przez zmienne środowiskowe
- **Odsprzężenie Embedding i LLM** — za pomocą `EMBEDDING_PROVIDER` można niezależnie wskazać enkoder osadzeń, chmurowe LLM automatycznie wracają do lokalnego `bge-m3`
- **Podział na dwa modele** — w trybie Ollama złożone zadania używają modelu głównego, a proste zadania automatycznie przełączają się na mały model, aby poprawić wydajność
- **Inteligentny podział treści** — długie teksty są automatycznie dzielone na segmenty, co zmniejsza obciążenie LLM (próg konfigurowalny)
- **Przetwarzanie pamięci w tle** — dodawanie pamięci może odbywać się w tle, a wywołanie MCP zwraca wynik natychmiast; stan zadań jest utrwalany w SQLite i automatycznie przywracany po restarcie
- **Deduplikacja pamięci** — automatyczne wykrywanie wysoce podobnych istniejących pamięci, aby uniknąć powtórnego przechowywania
- **Wykrywanie konfliktów** — wykrywa sprzeczne fakty między dwiema encjami, identyfikuje informacje wygasłe i ważne
- **Wykrywanie społeczności** — automatyczne grupowanie powiązanych encji w oparciu o algorytm Label Propagation
- **Śledzenie istotności** — automatyczne rejestrowanie częstotliwości dostępu do encji, wyniki wyszukiwania są sortowane według istotności
- **Inteligentne zapominanie** — identyfikuje i usuwa przestarzałe pamięci o niskim poziomie dostępu, utrzymując graf zwięzłym
- **Import masowy** — przesyłanie wielu pamięci naraz, odpowiednie do migracji dużych ilości danych
- **Strukturalne trójki** — bezpośrednie dodawanie „podmiot-relacja-przedmiot", pomijając ekstrakcję LLM, ukończenie w sekundę
- **Interfejs zarządzania Web** — wbudowany pulpit, przeglądanie, wyszukiwanie, wizualizacja grafu wiedzy, pytania i odpowiedzi AI, przeglądanie społeczności, konserwacja jakości, import masowy, ustawienia czasu wykonania
- **Wielojęzyczność (i18n)** — komunikaty odpowiedzi obsługują 33 języki (w tym zh-TW / en / zh-CN / ja / pt-BR / ko / es / de / fr itp.; zh-TW/en/zh-CN/ja pisane ręcznie, pozostałe dostarczane przez warstwę generated); narzędzia MCP według `SERVER_LANG`, REST API automatycznie negocjuje według nagłówka HTTP `Accept-Language`
- **Motyw ciemny/jasny** — interfejs Web obsługuje przełączanie motywów
- **Tryb bezpieczny** — opcjonalne szybkie dodawanie pamięci z pominięciem ekstrakcji encji
- **Wsparcie Docker** — wbudowany Dockerfile, obsługa wdrożenia kontenerowego
- **Bezpieczeństwo współbieżności** — asyncio.Lock chroni inicjalizację, zapobiegając warunkom wyścigu
- **Warstwowe kontrole stanu zdrowia** — `/health` (liveness) + `/health/ready` (readiness)

## Wymagania systemowe

| Pozycja | Wymaganie |
|------|------|
| Python | 3.10+ (zalecane 3.11+) |
| Neo4j | 4.0+ (`bolt://localhost:7687`) |
| Dostawca LLM | Ollama / GLM / GROQ / OpenRouter / DeepSeek (jeden z pięciu) |
| Node.js | 18+ (tylko do uruchamiania w tle PM2, opcjonalne) |
| Miejsce na dysku | ~3GB (modele Ollama + dane Neo4j) |

### Wybór dostawcy LLM

Przełączanie za pomocą zmiennej środowiskowej `LLM_PROVIDER` (`ollama` / `glm` / `groq` / `openrouter` / `deepseek`):

| Dostawca | Cechy | Model LLM | Embedding | Odpowiedni scenariusz |
|--------|------|----------|-----------|----------|
| **Ollama** (domyślny) | W pełni lokalny, dane nie opuszczają maszyny | `qwen2.5:3b` | `bge-m3` (doskonały dla chińskiego + RAG) | Posiadasz GPU, cenisz prywatność |
| **GLM** | Darmowa chmura, stabilna bez limitów | `glm-4-flash` (darmowy) | `embedding-3` | Brak GPU, scenariusze intensywnego wyszukiwania |
| **GROQ** | Wnioskowanie o ultra wysokiej prędkości | `llama-3.3-70b-versatile` | Powrót do Ollama `bge-m3` | Sporadyczny zapis, dążenie do jakości |
| **OpenRouter** | Agregacja modeli różnych dostawców, w tym darmowy limit | `stepfun/step-3.5-flash:free` itp. | Powrót do Ollama `bge-m3` | Chcesz użyć określonego modelu chmurowego |
| **DeepSeek** | Chmura 深度求索, wysoka opłacalność | `deepseek-v4-flash` / `deepseek-v4-pro` | Powrót do Ollama `bge-m3` | Rozumienie chińskiego, niskobudżetowa chmura |

> **Odsprzężenie Embedding i LLM**: enkoder osadzeń jest wskazywany niezależnie przez `EMBEDDING_PROVIDER` (`ollama` / `glm`), a gdy nie jest ustawiony, podąża za `LLM_PROVIDER`. W praktyce tylko `glm` używa GLM `embedding-3`, a pozostałe (w tym GROQ / OpenRouter / DeepSeek i inne chmurowe LLM nieoferujące Embedding) zawsze automatycznie używają Ollama `bge-m3`. **Dlatego przy korzystaniu z dowolnego chmurowego LLM nadal potrzebny jest lokalny Ollama zapewniający usługę osadzeń (chyba że embedding również jest ustawiony na glm).**

#### Tryb Ollama (lokalny)

```bash
# Główny model LLM (zalecany qwen2.5:3b, najlepsza równowaga prędkości i stabilności)
ollama pull qwen2.5:3b

# Model osadzeń (wymagany, do wyszukiwania wektorowego)
ollama pull bge-m3
```

> **Uwagi dotyczące wyboru modelu**:
> - `qwen2.5:3b` — zalecany, ~2s/wywołanie, ~100 t/s, ustrukturyzowane wyjście graphiti-core stabilne w 100%
> - `qwen2.5:7b` — lepszy efekt, ale 5-10 razy wolniejszy, odpowiedni dla scenariuszy dążących do jakości
> - `qwen2.5:1.5b` — najszybszy, ale **niestabilny** (skuteczność strukturalnego JSON tylko 33%), niezalecany

#### Tryb GLM (chmura 智谱 AI)

```bash
# Konfiguracja .env
LLM_PROVIDER=glm
GLM_API_KEY=your_api_key          # Pobierz z https://open.bigmodel.cn
GLM_MODEL=glm-4-flash             # Darmowy model
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768      # Musi być zgodny z wymiarem indeksu wektorowego Neo4j
```

> **Wydajność GLM dla odniesienia**: zapis ~22s (krótki tekst), wyszukiwanie ~0,34s, zero błędów Rate Limit, 2-5 razy wolniejszy niż lokalny Ollama, ale całkowicie darmowy.

#### Tryb GROQ (szybkie wnioskowanie)

```bash
# Konfiguracja .env
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key         # Pobierz z https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile
```

> **Uwaga**: GROQ nie oferuje usługi Embedding, należy go połączyć z enkoderem Ollama (automatyczny powrót) lub ustawić `EMBEDDING_PROVIDER` na glm. GROQ ma surowy Rate Limit, częste użycie wywoła wiele ponownych prób.

#### Tryb OpenRouter (agregacja modeli różnych dostawców)

```bash
# Konfiguracja .env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_api_key       # Pobierz z https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free   # Można zmienić na dowolny model OpenRouter
```

> **Uwaga**: OpenRouter nie oferuje Embedding, automatycznie wraca do Ollama `bge-m3`. Lista modeli na https://openrouter.ai/models (zawiera wiele darmowych modeli `:free`).

#### Tryb DeepSeek (深度求索)

```bash
# Konfiguracja .env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key         # Pobierz z https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash      # Zalecany; lub deepseek-v4-pro (lepszy efekt)
```

> **Uwaga**: DeepSeek nie oferuje Embedding, automatycznie wraca do Ollama `bge-m3`. `deepseek-chat` / `deepseek-reasoner` zostaną wycofane 2026-07-24, zaleca się przejście na `deepseek-v4-flash` / `deepseek-v4-pro`. DeepSeek surowo wymaga, aby prompt trybu `json_object` zawierał ciąg "json", klient ma wbudowane zabezpieczenie awaryjne, nie wymaga dodatkowej konfiguracji.

## Szybki start

### 1. Przygotowanie wstępne

Upewnij się, że Neo4j działa na lokalnej maszynie, i przygotuj odpowiednią usługę w zależności od wybranego dostawcy LLM:

```bash
# Potwierdź, że Neo4j działa (wymagane)
neo4j status
# Lub użyj Docker: docker run -d -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/your_password neo4j:latest

# Tryb Ollama: potwierdź, że Ollama działa
ollama list
# Jeśli nie uruchomiony: ollama serve

# Tryb GLM / GROQ: wymagany jest tylko ważny klucz API, bez lokalnej usługi
```

### 2. Instalacja zależności

```bash
git clone <repo-url>
cd graphiti
uv sync
```

> **Uwaga**: Ten projekt używa [uv](https://github.com/astral-sh/uv) do zarządzania zależnościami. Jeśli nie jest zainstalowany: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 3. Konfiguracja środowiska

```bash
cp .env.example .env
```

Edytuj `.env`, **co najmniej** należy zmienić następujące pozycje:

```bash
NEO4J_PASSWORD=your_actual_password  # Wymagane: hasło Neo4j
LLM_PROVIDER=ollama                  # ollama / glm / groq / openrouter / deepseek
OLLAMA_MODEL=qwen2.5:3b              # Tryb Ollama: lokalny model LLM
# GLM_API_KEY=your_key               # Tryb GLM: klucz API 智谱 AI
# GROQ_API_KEY=your_key              # Tryb GROQ: klucz API GROQ
# OPENROUTER_API_KEY=your_key        # Tryb OpenRouter: klucz API
# DEEPSEEK_API_KEY=your_key          # Tryb DeepSeek: klucz API
```

### 4. Uruchomienie usługi

```bash
# Tryb HTTP (zalecany, zawiera interfejs zarządzania Web)
uv run python graphiti_mcp_server.py --transport http --port 8000

# Lub uruchom w tle za pomocą PM2 (zalecane przy długotrwałym działaniu)
pm2 start ecosystem.config.cjs
```

### 5. Weryfikacja usługi

Po uruchomieniu można uzyskać dostęp do następujących punktów końcowych:

| Punkt końcowy | Opis |
|------|------|
| http://localhost:8000/ | Interfejs zarządzania Web |
| http://localhost:8000/mcp | Punkt końcowy MCP (dla połączenia klienta MCP) |
| http://localhost:8000/health | Kontrola stanu zdrowia (liveness) |
| http://localhost:8000/health/ready | Kontrola dogłębna (w tym połączenie Neo4j) |
| http://localhost:8000/api/stats | Statystyki REST API |

## Struktura projektu

```
graphiti/
├── graphiti_mcp_server.py        # Główne wejście — definicje narzędzi MCP (19 narzędzi)
├── src/
│   ├── config.py                 # Zarządzanie konfiguracją (GraphitiConfig, obsługa nakładania JSON/.env)
│   ├── web_api.py                # REST API interfejsu zarządzania Web (30+ punktów końcowych)
│   ├── ollama_graphiti_client.py  # Klient LLM Ollama (podział na dwa modele)
│   ├── openai_compat_client.py   # Klasa bazowa LLM zgodna z OpenAI (json_object + uproszczony schemat + zabezpieczenie json)
│   ├── glm_client.py             # Klient LLM GLM (智谱 AI) (dziedziczy OpenAICompatClient)
│   ├── openrouter_client.py      # Klient LLM OpenRouter (dziedziczy OpenAICompatClient)
│   ├── deepseek_client.py        # Klient LLM DeepSeek (dziedziczy OpenAICompatClient)
│   ├── ollama_embedder.py        # Adapter modelu osadzeń Ollama
│   ├── content_preprocessor.py   # Inteligentny podział treści (automatyczne dzielenie długich tekstów)
│   ├── deduplication.py          # Deduplikacja pamięci (porównanie podobieństwa cosinusowego)
│   ├── importance.py             # Śledzenie istotności i inteligentne zapominanie
│   ├── safe_memory_add.py        # Bezpieczne dodawanie pamięci (pominięcie ekstrakcji encji)
│   ├── task_store.py             # Utrwalanie zadań w tle w SQLite (TaskStore)
│   ├── timezone_utils.py         # Konwersja strefy czasowej (UTC→wyświetlanie lokalnej strefy)
│   ├── i18n.py                   # Wielojęzyczność backendu (REST według Accept-Language, MCP według SERVER_LANG)
│   ├── i18n_generated.py         # Automatycznie generowane nadpisania języków (GENERATED_MESSAGE_OVERRIDES)
│   ├── exceptions.py             # Strukturalna obsługa wyjątków (12 klas wyjątków)
│   └── logging_setup.py          # System logowania (rotacja czasowa + monitorowanie wydajności)
├── web/                          # Frontend interfejsu zarządzania Web (SPA, bez build)
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js                # Opakowanie REST API
│       ├── components.js         # Renderowanie komponentów UI (w tym strona społeczności)
│       └── app.js                # Routing SPA, zarządzanie stanem
├── tests/                        # Zestaw testów (203 testy)
│   ├── test_content_preprocessor.py  # Testy logiki podziału (17)
│   ├── test_new_features.py      # Testy nowych funkcji (32)
│   ├── test_i18n.py             # Testy wielojęzyczności (57)
│   ├── test_unit.py              # Testy jednostkowe
│   ├── test_web_api.py           # Testy Web API
│   ├── test_web_ui_features.py   # Testy funkcji Web UI
│   ├── test_integration_manual.py # Ręczne testy integracyjne
│   └── bench_deepseek_flash_vs_pro.py # Skrypt benchmarku wydajności flash/pro DeepSeek
├── tools/                        # Narzędzia diagnostyczne deweloperskie
│   ├── status_report.py          # Zintegrowany raport stanu
│   ├── validate_config.py        # Walidacja konfiguracji
│   ├── performance_diagnose.py   # Diagnostyka wydajności
│   ├── inspect_schema.py         # Kontrola struktury Neo4j
│   ├── batch_reprocess.py        # Masowe ponowne przetwarzanie
│   └── migrate_embeddings.py     # Migracja modelu Embedding
├── docs/                         # Dokumentacja
├── logs/                         # Logi (rotacja czasowa, domyślnie przechowywane 30 dni)
├── Dockerfile                    # Wdrożenie kontenerowe Docker
└── ecosystem.config.cjs          # Konfiguracja PM2
```

## Konfiguracja klienta MCP

### Tryb HTTP (zalecany)

Odpowiedni dla klientów MCP obsługujących HTTP, takich jak Claude Code, Cline:

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

### Tryb STDIO

Odpowiedni dla klientów wymagających bezpośredniego uruchomienia procesu, takich jak Claude Desktop:

**Lokalizacja pliku konfiguracyjnego:**
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

> **Uwaga**: Tryb SSE (`--transport sse`) jest już niezalecany. MCP 1.x ma problemy ze zgodnością inicjalizacji sesji, należy przejść na tryb HTTP.

## Narzędzia MCP (19)

### Zarządzanie pamięcią (7)

| Narzędzie | Opis |
|------|------|
| `add_memory_simple` | Dodaj pamięć do grafu wiedzy (obsługa przetwarzania w tle, inteligentnego podziału, kontroli deduplikacji) |
| `add_episode_bulk` | Masowe dodawanie wielu pamięci (domyślnie przetwarzanie w tle) |
| `add_triplet` | Dodawanie strukturalnych trójek (pomija LLM, ukończenie w sekundę) |
| `search_memory_nodes` | Wyszukiwanie węzłów pamięci (obsługa 16 strategii wyszukiwania, filtrowania czasu) |
| `search_memory_facts` | Wyszukiwanie faktów pamięci (obsługa filtrowania typu relacji, zakresu czasu, filtrowania ważności) |
| `advanced_search` | Wyszukiwanie zaawansowane (16 strategii, zwraca węzły+krawędzie+społeczności+fragmenty) |
| `get_episodes` | Pobierz najnowsze fragmenty pamięci |

### Analiza wiedzy (3)

| Narzędzie | Opis |
|------|------|
| `check_conflicts` | Wykryj konflikty faktów między dwiema encjami (ważne vs wygasłe) |
| `get_node_edges` | Eksploruj relacje krawędzi wejściowych i wyjściowych węzła |
| `build_communities` | Wywołaj wykrywanie i grupowanie społeczności (domyślnie przetwarzanie w tle) |

### Konserwacja pamięci (2)

| Narzędzie | Opis |
|------|------|
| `get_stale_memories` | Zapytaj o przestarzałe pamięci o niskim poziomie dostępu |
| `cleanup_stale_memories` | Usuń przestarzałe pamięci (domyślnie tryb podglądu dry_run) |

### Zarządzanie zadaniami

| Narzędzie | Opis |
|------|------|
| `get_memory_task_status` | Zapytaj o postęp i wynik zadania przetwarzania pamięci w tle |

### Usuwanie i zapytania

| Narzędzie | Opis |
|------|------|
| `delete_episode` | Usuń fragment pamięci |
| `delete_entity_edge` | Usuń krawędź encji (relację) |
| `get_entity_edge` | Pobierz szczegółowe informacje o krawędzi encji |

### Zarządzanie systemem

| Narzędzie | Opis |
|------|------|
| `get_status` | Pobierz stan usługi (Neo4j, LLM, enkoder) |
| `test_connection` | Przetestuj połączenie Neo4j / LLM / enkodera |
| `clear_graph` | Wyczyść bazę grafową (obsługa czyszczenia według group_id) |

## Parametry narzędzi

### add_memory_simple

| Parametr | Typ | Wymagany | Wartość domyślna | Opis |
|------|------|------|--------|------|
| `name` | string | Y | | Nazwa pamięci |
| `episode_body` | string | Y | | Treść pamięci (powyżej 800 znaków automatyczny podział) |
| `group_id` | string | | `"default"` | ID grupy (zalecana izolacja według projektu) |
| `source` | string | | `"text"` | Typ źródła: `text` / `json` / `message` |
| `source_description` | string | | `"MCP Server"` | Opis źródła |
| `use_safe_mode` | bool | | `false` | Tryb bezpieczny (pomija ekstrakcję encji, szybki, ale pamięć niewyszukiwalna) |
| `background` | bool | | `false` | Przetwarzanie w tle (natychmiastowy zwrot task_id, odpowiednie dla długich tekstów) |
| `force` | bool | | `false` | Pominięcie kontroli deduplikacji (wymuszone dodawanie) |
| `excluded_entity_types` | list | | | Wykluczone typy encji (zmniejszenie niepotrzebnej ekstrakcji) |

> **Wskazówki wydajnościowe**:
> - Krótki tekst (<800 znaków): przetwarzanie bezpośrednie, zwykle ukończenie w 30-40 sekund
> - Długi tekst (>800 znaków): automatyczny podział na wiele segmentów, przetwarzanie współbieżne za pomocą `add_episode_bulk` (~33% szybsze niż szeregowe)
> - Użycie `background=true` pozwala uniknąć blokowania wywołania MCP, śledzenie postępu przez `get_memory_task_status`
> - `use_safe_mode=true` ukończenie w sekundę, ale pamięć nie może zostać znaleziona przez narzędzia search
> - Przy włączonej deduplikacji wysoce podobne pamięci będą ostrzegane (`force=true` pozwala pominąć)

### add_episode_bulk

| Parametr | Typ | Wymagany | Wartość domyślna | Opis |
|------|------|------|--------|------|
| `episodes` | list | Y | | Lista pamięci, każdy element zawiera `name` i `content` |
| `group_id` | string | | `"default"` | ID grupy |
| `source` | string | | `"text"` | Typ źródła |
| `background` | bool | | `true` | Przetwarzanie w tle (masowe zwykle czasochłonne) |

### add_triplet

| Parametr | Typ | Wymagany | Wartość domyślna | Opis |
|------|------|------|--------|------|
| `source_name` | string | Y | | Nazwa encji źródłowej (np. "Alice") |
| `target_name` | string | Y | | Nazwa encji docelowej (np. "Google") |
| `relation_name` | string | Y | | Nazwa relacji (np. "works_at") |
| `fact` | string | Y | | Opis faktu (np. "Alice works at Google") |
| `group_id` | string | | `"default"` | ID grupy |
| `source_labels` | list | | | Etykiety encji źródłowej |
| `target_labels` | list | | | Etykiety encji docelowej |

### search_memory_nodes

| Parametr | Typ | Wymagany | Wartość domyślna | Opis |
|------|------|------|--------|------|
| `query` | string | Y | | Słowa kluczowe wyszukiwania (język naturalny) |
| `max_nodes` | int | | `10` | Maksymalna liczba zwracanych wyników |
| `group_ids` | list | | | Filtrowanie grup (wspólne wyszukiwanie wielu grup) |
| `entity_types` | list | | | Filtrowanie typu encji |
| `search_recipe` | string | | | Strategia wyszukiwania (patrz wyszukiwanie zaawansowane) |
| `created_after` | string | | | Dolna granica czasu utworzenia (ISO datetime) |
| `created_before` | string | | | Górna granica czasu utworzenia (ISO datetime) |

### search_memory_facts

| Parametr | Typ | Wymagany | Wartość domyślna | Opis |
|------|------|------|--------|------|
| `query` | string | Y | | Słowa kluczowe wyszukiwania |
| `max_facts` | int | | `10` | Maksymalna liczba zwracanych wyników |
| `group_ids` | list | | | Filtrowanie grup |
| `center_node_uuid` | string | | | UUID węzła centralnego (eksploracja relacji określonego węzła) |
| `edge_types` | list | | | Filtrowanie typu relacji (np. `["works_at"]`) |
| `created_after` | string | | | Dolna granica czasu utworzenia (ISO datetime) |
| `created_before` | string | | | Górna granica czasu utworzenia (ISO datetime) |
| `only_valid` | bool | | `false` | Zwracaj tylko niewygasłe fakty |

### advanced_search

| Parametr | Typ | Wymagany | Wartość domyślna | Opis |
|------|------|------|--------|------|
| `query` | string | Y | | Słowa kluczowe wyszukiwania |
| `search_recipe` | string | | `"combined_rrf"` | Strategia wyszukiwania (16 do wyboru) |
| `max_results` | int | | `10` | Maksymalna liczba zwracanych wyników |
| `group_ids` | list | | | Filtrowanie grup |
| `center_node_uuid` | string | | | UUID węzła centralnego |

**Dostępne strategie wyszukiwania (search_recipe):**

| Kategoria | Strategia | Opis |
|------|------|------|
| Łączone | `combined_rrf` | Łączona fuzja RRF (domyślna, zalecana) |
| Łączone | `combined_mmr` | Łączone ponowne rankingowanie różnorodności MMR |
| Łączone | `combined_cross_encoder` | Łączone precyzyjne rankingowanie Cross-Encoder |
| Krawędź | `edge_rrf` / `edge_mmr` / `edge_cross_encoder` | Wyszukiwanie krawędzi (3 metody sortowania) |
| Krawędź | `edge_node_distance` / `edge_episode_mentions` | Wyszukiwanie krawędzi (odległość grafu/liczba odniesień) |
| Węzeł | `node_rrf` / `node_mmr` / `node_cross_encoder` | Wyszukiwanie węzłów (3 metody sortowania) |
| Węzeł | `node_node_distance` / `node_episode_mentions` | Wyszukiwanie węzłów (odległość grafu/liczba odniesień) |
| Społeczność | `community_rrf` / `community_mmr` / `community_cross_encoder` | Wyszukiwanie społeczności |

### check_conflicts

| Parametr | Typ | Wymagany | Wartość domyślna | Opis |
|------|------|------|--------|------|
| `source_name` | string | Y | | Nazwa encji źródłowej |
| `target_name` | string | Y | | Nazwa encji docelowej |
| `group_id` | string | | `"default"` | ID grupy |

### get_node_edges

| Parametr | Typ | Wymagany | Wartość domyślna | Opis |
|------|------|------|--------|------|
| `node_uuid` | string | Y | | UUID węzła |
| `include_inbound` | bool | | `true` | Uwzględnij krawędzie wejściowe |
| `include_outbound` | bool | | `true` | Uwzględnij krawędzie wyjściowe |
| `max_edges` | int | | `50` | Maksymalna liczba zwracanych wyników |

### build_communities

| Parametr | Typ | Wymagany | Wartość domyślna | Opis |
|------|------|------|--------|------|
| `group_ids` | list | | | Określ grupy (pozostaw puste dla wszystkich) |
| `background` | bool | | `true` | Przetwarzanie w tle |

### get_stale_memories

| Parametr | Typ | Wymagany | Wartość domyślna | Opis |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Ile dni bez dostępu uznaje się za przestarzałe |
| `min_access_count` | int | | `2` | Liczone tylko gdy liczba dostępów poniżej tej wartości |
| `group_id` | string | | | Filtrowanie grup |
| `limit` | int | | `50` | Maksymalna liczba zwracanych wyników |

### cleanup_stale_memories

| Parametr | Typ | Wymagany | Wartość domyślna | Opis |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Próg dni przestarzałości |
| `min_access_count` | int | | `2` | Próg minimalnej liczby dostępów |
| `group_id` | string | | | Filtrowanie grup |
| `dry_run` | bool | | `true` | Tryb podglądu (bez faktycznego usuwania) |
| `limit` | int | | `50` | Maksymalna liczba przetwarzanych |

### get_memory_task_status

| Parametr | Typ | Wymagany | Opis |
|------|------|------|------|
| `task_id` | string | Y | ID zadania w tle (zwrócone przez `add_memory_simple(background=true)`) |

## Interfejs zarządzania Web

W trybie HTTP wystarczy uzyskać dostęp do `http://localhost:8000/`.

**Funkcje:**
- Pulpit — statystyki liczby węzłów, faktów, fragmentów pamięci
- Węzły encji — przeglądanie, filtrowanie, wyszukiwanie wektorowe
- Relacje faktów — przeglądanie, filtrowanie, wyszukiwanie wektorowe
- Fragmenty pamięci — przeglądanie, wyszukiwanie pełnotekstowe, usuwanie
- Przeglądanie społeczności — lista węzłów społeczności, podsumowanie, wywołanie budowania społeczności
- Formularz trójek — bezpośrednie dodawanie strukturalnej wiedzy „podmiot-relacja-przedmiot"
- Zarządzanie grupami — filtrowanie według grupy, masowe usuwanie
- Wizualizacja grafu wiedzy — graficzna prezentacja relacji węzłów
- Pytania i odpowiedzi AI — inteligentne pytania i odpowiedzi oparte na grafie wiedzy
- Konserwacja jakości — wskaźniki jakości pamięci i narzędzia czyszczenia
- Import masowy — import wielu fragmentów pamięci naraz (JSON, limit 500 na raz)
- Ustawienia czasu wykonania — wyświetlanie aktualnie obowiązujących ustawień z możliwością zmiany wybranych parametrów bez restartu
- Przełączanie motywu — motyw ciemny/jasny

**REST API:**

| Punkt końcowy | Metoda | Opis |
|------|------|------|
| `/api/stats` | GET | Statystyki pulpitu |
| `/api/groups` | GET | Pobierz wszystkie group_id |
| `/api/groups/stats` | GET | Statystyki węzłów/faktów/fragmentów dla każdej grupy |
| `/api/nodes` | GET | Przeglądaj węzły encji (paginacja) |
| `/api/facts` | GET | Przeglądaj fakty (paginacja) |
| `/api/episodes` | GET | Przeglądaj fragmenty pamięci (paginacja) |
| `/api/nodes/{uuid}/relations` | GET | Pobierz krawędzie wejściowe/wyjściowe węzła |
| `/api/search/nodes` | GET | Wyszukiwanie wektorowe węzłów |
| `/api/search/facts` | GET | Wyszukiwanie wektorowe faktów |
| `/api/search/episodes` | GET | Wyszukiwanie fragmentów pamięci |
| `/api/search/advanced` | GET | Wyszukiwanie zaawansowane (16 strategii) |
| `/api/communities` | GET | Przeglądaj węzły społeczności (paginacja) |
| `/api/communities/build` | POST | Wywołaj budowanie społeczności |
| `/api/memory/add` | POST | Dodaj pojedynczą pamięć |
| `/api/memory/add-bulk` | POST | Masowe dodawanie pamięci |
| `/api/memory/add-triplet` | POST | Dodaj trójkę |
| `/api/import/episodes` | POST | Masowy import fragmentów pamięci (JSON, limit 500 na raz) |
| `/api/memory/tasks` | GET | Lista zadań w tle (obsługa filtrowania stanu) |
| `/api/memory/tasks/{id}` | GET | Zapytaj o stan pojedynczego zadania |
| `/api/timeline` | GET | Przeglądanie osi czasu |
| `/api/graph/subgraph` | GET | Pobierz podgraf (wizualizacja) |
| `/api/graph/all` | GET | Pobierz pełny graf (wizualizacja) |
| `/api/ask` | GET | Pytania i odpowiedzi AI (wyszukiwanie oparte na grafie) |
| `/api/analytics/top-nodes` | GET | Węzły o wysokim stopniu połączeń/wysokim dostępie |
| `/api/analytics/quality` | GET | Wskaźniki jakości grafu wiedzy |
| `/api/analytics/stale` | GET | Zapytaj o przestarzałe pamięci |
| `/api/analytics/cleanup` | POST | Usuń przestarzałe pamięci |
| `/api/config` | GET | Pobierz aktualnie obowiązujące ustawienia (bez kluczy API) |
| `/api/config` | PATCH | Aktualizuj modyfikowalne ustawienia w czasie wykonania (dotyczy tylko bieżącego procesu, reset po restarcie) |
| `/api/nodes/{uuid}` | DELETE | Usuń węzeł |
| `/api/episodes/{uuid}` | DELETE | Usuń fragment pamięci |
| `/api/facts/{uuid}` | DELETE | Usuń fakt |
| `/api/groups/{group_id}` | DELETE | Usuń całą grupę |

## Konfiguracja

### Zmienne środowiskowe (.env)

Konfiguracja używa mechanizmu nakładania: plik konfiguracyjny JSON jako podstawa, zmienne środowiskowe nadpisują poszczególne wartości.

```bash
# === Wymagane ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password        # Musi zostać zmienione

# === Wybór dostawcy LLM ===
LLM_PROVIDER=ollama                 # ollama / glm / groq / openrouter / deepseek

# === Dostawca Embedding (opcjonalny, domyślnie podąża za LLM_PROVIDER) ===
# Tylko glm używa GLM Embedding, pozostałe zawsze używają Ollama bge-m3
# EMBEDDING_PROVIDER=ollama         # ollama / glm

# === Konfiguracja Ollama (używana gdy LLM_PROVIDER=ollama) ===
OLLAMA_MODEL=qwen2.5:3b             # Główny model (zalecany qwen2.5:3b)
OLLAMA_SMALL_MODEL=qwen2.5:3b       # Mały model (do prostych zadań, opcjonalnie inny model)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.1

# === Konfiguracja GLM (używana gdy LLM_PROVIDER=glm) ===
GLM_API_KEY=your_api_key            # Pobierz z https://open.bigmodel.cn
GLM_MODEL=glm-4-flash               # Darmowy model
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768

# === Konfiguracja GROQ (używana gdy LLM_PROVIDER=groq) ===
GROQ_API_KEY=your_api_key           # Pobierz z https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile

# === Konfiguracja OpenRouter (używana gdy LLM_PROVIDER=openrouter) ===
OPENROUTER_API_KEY=your_api_key     # Pobierz z https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free

# === Konfiguracja DeepSeek (używana gdy LLM_PROVIDER=deepseek) ===
DEEPSEEK_API_KEY=your_api_key       # Pobierz z https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash    # Lub deepseek-v4-pro

# === Model osadzeń Ollama (używany przy osadzaniu innym niż glm) ===
OLLAMA_EMBEDDING_MODEL=bge-m3
OLLAMA_EMBEDDING_DIMENSIONS=768

# === Wyświetlanie i język (opcjonalne) ===
GRAPHITI_DISPLAY_TIMEZONE=Asia/Taipei # Strefa czasowa wyświetlania znaczników czasu zwracanych przez API (nazwa IANA; przechowywanie pozostaje UTC)
SERVER_LANG=zh-TW                     # Język odpowiedzi narzędzi MCP (pełne locale w src/i18n.py); REST API według Accept-Language

# === Wydajność pamięci (opcjonalne) ===
GRAPHITI_CHUNK_THRESHOLD=800         # Próg liczby znaków wyzwalający inteligentny podział
GRAPHITI_MAX_CHUNK_SIZE=600          # Maksymalna liczba znaków na segment
GRAPHITI_MAX_COROUTINES=10            # Maksymalna liczba współbieżnych korutyn
GRAPHITI_DEFAULT_BACKGROUND=false    # Czy domyślnie przetwarzać w tle
TASK_DB_PATH=data/tasks.db           # Ścieżka utrwalania zadań w tle w SQLite

# === Śledzenie istotności i inteligentne zapominanie (opcjonalne) ===
ENABLE_IMPORTANCE_TRACKING=true      # Włącz śledzenie dostępu
IMPORTANCE_WEIGHT=0.1                # Waga istotności
STALE_DAYS_THRESHOLD=30              # Próg dni przestarzałości
STALE_MIN_ACCESS_COUNT=2             # Minimalna liczba dostępów

# === Logowanie ===
LOG_FILE=logs/graphiti_mcp_server.log
LOG_LEVEL=INFO
```

> **Pełna lista zmiennych środowiskowych** znajduje się w `.env.example`

### Plik konfiguracyjny JSON

Odpowiedni dla konfiguracji wymagającej kontroli wersji (zmienne środowiskowe nadal mogą nadpisywać):

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

## Uruchamianie w tle PM2

```bash
npm install -g pm2

pm2 start ecosystem.config.cjs      # Uruchom
pm2 status                           # Stan
pm2 logs graphiti-mcp-http           # Logi w czasie rzeczywistym
pm2 restart graphiti-mcp-http --update-env  # Restart (ponowne wczytanie .env)

pm2 save && pm2 startup              # Ustaw automatyczne uruchamianie przy starcie systemu
```

> **Wskazówka**: Po zmianie `.env` należy zrestartować z flagą `--update-env`, w przeciwnym razie zmienne środowiskowe nie zostaną zaktualizowane.

## Wdrożenie Docker

```bash
docker build -t graphiti-mcp .

# Uwaga: kontener Docker musi mieć możliwość połączenia z Neo4j i Ollama
# Użycie host network jest najprostsze
docker run -p 8000:8000 --env-file .env --network host graphiti-mcp

# Lub wyraźnie określ adresy usług zewnętrznych
docker run -p 8000:8000 \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --env-file .env graphiti-mcp
```

## Testy

```bash
# Wykonaj wszystkie testy (203, około 1 sekunda)
uv run python -m pytest tests/

# Szczegółowe wyjście
uv run python -m pytest tests/ -v

# Wykonaj tylko określone testy
uv run python -m pytest tests/test_content_preprocessor.py -v
uv run python -m pytest tests/test_new_features.py -v
uv run python -m pytest tests/test_unit.py -v
```

> **Uwaga**: 3 testy async w `test_integration_manual.py` wymagają zainstalowania `pytest-asyncio`, w przypadku braku pokażą Failed, ale nie wpływa to na inne testy. `bench_deepseek_flash_vs_pro.py` jest skryptem benchmarku wydajności, a nie testem jednostkowym.

## Rozwiązywanie problemów

### Niepowodzenie połączenia Neo4j

```bash
neo4j status                              # Sprawdź stan usługi
cypher-shell -u neo4j -p your_password    # Potwierdź poprawność hasła
curl http://localhost:7474                 # Potwierdź port HTTP
```

Częste przyczyny:
- Neo4j nie został uruchomiony
- Błędne hasło (`NEO4J_PASSWORD` w `.env`)
- Port zajęty lub zablokowany przez zaporę

### Niepowodzenie połączenia LLM

**Tryb Ollama:**
```bash
ollama serve                # Uruchom usługę Ollama
ollama list                 # Sprawdź zainstalowane modele
ollama pull qwen2.5:3b      # Zainstaluj brakujący model
```

Częste przyczyny: Ollama nie uruchomiony, model nie zainstalowany, niewystarczająca pamięć GPU

**Tryb GLM:**
- Potwierdź poprawność `GLM_API_KEY`
- Potwierdź `GLM_EMBEDDING_DIMENSIONS=768` (musi być zgodny z indeksem wektorowym Neo4j)
- Punkt końcowy API GLM: `https://open.bigmodel.cn/api/paas/v4/`

**Tryb GROQ:**
- Potwierdź poprawność `GROQ_API_KEY`
- Przy częstym Rate Limit rozważ przełączenie na tryb GLM
- GROQ nie oferuje Embedding, należy zapewnić dostępność enkodera Ollama

**Tryb OpenRouter:**
- Potwierdź poprawność `OPENROUTER_API_KEY`, `OPENROUTER_MODEL` jako prawidłowe ID modelu (patrz https://openrouter.ai/models)
- Nie oferuje Embedding, należy zapewnić dostępność enkodera Ollama

**Tryb DeepSeek:**
- Potwierdź poprawność `DEEPSEEK_API_KEY`
- Jeśli pojawi się `Prompt must contain the word 'json'`: jest to twardy wymóg trybu `json_object` DeepSeek, klient ma wbudowane zabezpieczenie awaryjne; jeśli nadal się pojawia, potwierdź użycie najnowszej wersji `src/deepseek_client.py` i zrestartuj usługę
- Nie oferuje Embedding, należy zapewnić dostępność enkodera Ollama

### Błąd połączenia MCP

Jeśli pojawi się `Invalid request parameters` lub `Received request before initialization was complete`:

1. Potwierdź użycie trybu transportu HTTP (**nie używaj SSE**)
2. Potwierdź, że klient jest ustawiony na `"type": "http"`, `"url": "http://localhost:8000/mcp"`
3. Zrestartuj usługę: `pm2 restart graphiti-mcp-http --update-env`
4. W Claude Code wykonaj `/mcp`, aby ponownie połączyć

### Wolne dodawanie pamięci

- **Ollama**: sprawdź rozmiar modelu (`qwen2.5:3b` jest 5-10 razy szybszy niż `7b`), potwierdź użycie GPU (`ollama ps`)
- **GLM**: każde add_episode wymaga ponad 10-20 podróży sieciowych LLM, ~22s dla krótkiego tekstu to wartość normalna
- **GROQ**: Rate Limit powoduje wiele ponownych prób, przy częstym użyciu zaleca się przełączenie na GLM lub Ollama
- Użyj `background=true`, aby uniknąć blokowania
- Obniż `GRAPHITI_CHUNK_THRESHOLD`, aby długie teksty były dzielone wcześniej

### Problemy z PM2

```bash
pm2 status                                        # Sprawdź stan
pm2 logs graphiti-mcp-http --err --lines 50        # Logi błędów
lsof -i :8000                                     # Sprawdź zajęcie portu
pm2 delete graphiti-mcp-http && pm2 start ecosystem.config.cjs  # Pełny restart
```

## Narzędzia diagnostyczne deweloperskie

```bash
uv run python tools/status_report.py           # Zintegrowany raport stanu (Neo4j + Ollama + konfiguracja)
uv run python tools/validate_config.py         # Walidacja kompletności .env i konfiguracji
uv run python tools/performance_diagnose.py    # Diagnostyka wydajności LLM
uv run python tools/inspect_schema.py          # Kontrola indeksów i ograniczeń Neo4j
uv run python tools/migrate_embeddings.py      # Migracja modelu Embedding (ponowne generowanie wektorów po zmianie modelu)
```

### Migracja modelu Embedding

Po przełączeniu modelu embedding (np. `nomic-embed-text` → `bge-m3`) można użyć narzędzia migracji, aby ponownie wygenerować wszystkie istniejące wektory, zapewniając spójną jakość wyszukiwania:

```bash
# Podgląd liczby do migracji
uv run python tools/migrate_embeddings.py --dry-run

# Pełna migracja (obsługa wznawiania od punktu przerwania)
uv run python tools/migrate_embeddings.py

# Migracja tylko określonej grupy
uv run python tools/migrate_embeddings.py --group-id myproject

# Kontynuacja od punktu przerwania (ponowne uruchomienie po przerwaniu)
uv run python tools/migrate_embeddings.py --resume
```

> **Zgodność**: `bge-m3` natywnie 1024 wymiary, system automatycznie obcina do 768 wymiarów dla zgodności z istniejącym indeksem wektorowym Neo4j. Dane sprzed i po migracji mogą współistnieć, ale zaleca się wykonanie pełnej migracji w celu uzyskania najlepszej jakości wyszukiwania.

## Dokumentacja

- [Instrukcje korzystania z narzędzi](../使用工具的指令.md) — przewodnik użycia narzędzi MCP i najlepsze praktyki
- [Graphiti Memory Rules](../graphiti-memory-rules.md) — opis reguł pamięci

## Licencja

MIT License
