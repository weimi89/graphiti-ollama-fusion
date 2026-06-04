# Graphiti MCP Server

Сервіс пам'яті на основі графа знань — MCP-сервер, що інтегрує кількох постачальників LLM (Ollama / GLM / GROQ / OpenRouter / DeepSeek) із графовою базою даних Neo4j.

Розроблено як розширення на основі [getzep/graphiti](https://github.com/getzep/graphiti), підтримує гнучке перемикання між локальним Ollama та хмарними LLM, а також дає змогу незалежно вказати постачальника Embedding (відокремленого від LLM).

## Можливості

- **Інтелектуальне керування пам'яттю** — використовує граф знань для зберігання та пошуку складних взаємозв'язків пам'яті
- **Семантичний пошук** — гібридний пошук на основі векторних вкладень (вектор + ключові слова + обхід графа)
- **16 стратегій пошуку** — розширений пошук підтримує різноманітні методи переранжування, як-от RRF, MMR, Cross-Encoder тощо
- **Кілька постачальників LLM** — підтримка Ollama (локальний), GLM (безкоштовний від Zhipu AI), GROQ (швидкісне виведення), OpenRouter (агрегація моделей різних постачальників), DeepSeek (Deepseek), з перемиканням одним рухом через змінну середовища
- **Відокремлення Embedding від LLM** — можна незалежно вказати вкладник через `EMBEDDING_PROVIDER`, хмарні LLM автоматично повертаються до локального `bge-m3`
- **Розподіл за двома моделями** — у режимі Ollama складні завдання використовують основну модель, а прості завдання автоматично перемикаються на малу модель для підвищення продуктивності
- **Інтелектуальне розбиття вмісту** — довгі тексти автоматично сегментуються для обробки, що зменшує навантаження на LLM (поріг можна налаштувати)
- **Фонова обробка пам'яті** — додавання пам'яті може виконуватися у фоновому режимі, виклик MCP повертається негайно
- **Дедуплікація пам'яті** — автоматичне виявлення дуже схожих наявних спогадів, щоб уникнути дублювання зберігання
- **Виявлення конфліктів** — виявлення суперечливих фактів між двома сутностями, розпізнавання застарілої та чинної інформації
- **Виявлення спільнот** — автоматична кластеризація пов'язаних сутностей на основі алгоритму Label Propagation
- **Відстеження важливості** — автоматичне записування частоти доступу до сутностей, результати пошуку впорядковуються за важливістю
- **Інтелектуальне забування** — розпізнавання та очищення застарілих спогадів із низькою частотою доступу для збереження стрункості графа
- **Масовий імпорт** — подання кількох спогадів за один раз, зручно для масштабної міграції даних
- **Структуровані трійки** — пряме додавання «суб'єкт-відношення-об'єкт», обходить вилучення LLM і завершується миттєво
- **Веб-інтерфейс керування** — вбудована панель моніторингу, перегляд, пошук, візуалізація графа знань, AI-запитання та відповіді, перегляд спільнот
- **Багатомовність (i18n)** — повідомлення відповідей підтримують 30+ локалей (включно з zh-TW / en / zh-CN / ja / pt-BR / ko / es / de / fr тощо); інструменти MCP залежать від `SERVER_LANG`, REST API автоматично узгоджує за HTTP `Accept-Language`
- **Темна/світла тема** — веб-інтерфейс підтримує перемикання теми
- **Безпечний режим** — за бажанням можна пропустити вилучення сутностей для швидкого додавання пам'яті
- **Підтримка Docker** — вбудований Dockerfile, підтримка контейнеризованого розгортання
- **Конкурентна безпека** — asyncio.Lock захищає ініціалізацію, запобігаючи станам гонитви
- **Багаторівнева перевірка справності** — `/health` (liveness) + `/health/ready` (readiness)

## Системні вимоги

| Пункт | Вимога |
|------|------|
| Python | 3.10+ (рекомендовано 3.11+) |
| Neo4j | 4.0+ (`bolt://localhost:7687`) |
| Постачальник LLM | Ollama / GLM / GROQ / OpenRouter / DeepSeek (один із п'яти) |
| Node.js | 18+ (лише для фонового виконання PM2, необов'язково) |
| Дисковий простір | ~3GB (моделі Ollama + дані Neo4j) |

### Вибір постачальника LLM

Перемикання через змінну середовища `LLM_PROVIDER` (`ollama` / `glm` / `groq` / `openrouter` / `deepseek`):

| Постачальник | Особливості | Модель LLM | Embedding | Доречний сценарій |
|--------|------|----------|-----------|----------|
| **Ollama** (за замовчуванням) | Повністю локально, дані не залишають машину | `qwen2.5:3b` | `bge-m3` (відмінна якість для китайської + RAG) | Є GPU, цінується приватність |
| **GLM** | Безкоштовна хмара, стабільна, без обмежень потоку | `glm-4-flash` (безкоштовно) | `embedding-3` | Немає GPU, сценарії з інтенсивним пошуком |
| **GROQ** | Надшвидке виведення | `llama-3.3-70b-versatile` | Повернення до Ollama `bge-m3` | Зрідка записування, прагнення до якості |
| **OpenRouter** | Агрегує моделі різних постачальників, включно з безкоштовною квотою | `stepfun/step-3.5-flash:free` тощо | Повернення до Ollama `bge-m3` | Бажання використати конкретну хмарну модель |
| **DeepSeek** | Хмара Deepseek, висока ефективність витрат | `deepseek-v4-flash` / `deepseek-v4-pro` | Повернення до Ollama `bge-m3` | Розуміння китайської, недорога хмара |

> **Відокремлення Embedding від LLM**: вкладник вказується незалежно через `EMBEDDING_PROVIDER` (`ollama` / `glm`), а якщо не встановлено, слідує за `LLM_PROVIDER`. Фактично лише `glm` використовує GLM `embedding-3`, а решта (включно з хмарними LLM, що не надають Embedding, як-от GROQ / OpenRouter / DeepSeek) завжди автоматично використовують Ollama `bge-m3`. **Тому під час використання будь-якого хмарного LLM усе одно потрібен локальний Ollama для надання служби вкладень (якщо тільки embedding також не встановлено на glm).**

#### Режим Ollama (локальний)

```bash
# Основна модель LLM (рекомендовано qwen2.5:3b, найкращий баланс швидкості та стабільності)
ollama pull qwen2.5:3b

# Модель вкладень (обов'язкова, для векторного пошуку)
ollama pull bge-m3
```

> **Зауваження щодо вибору моделі**:
> - `qwen2.5:3b` — рекомендовано, ~2с/виклик, ~100 т/с, структуроване виведення graphiti-core стабільне на 100%
> - `qwen2.5:7b` — кращий результат, але в 5-10 разів повільніший, доречний для сценаріїв із прагненням до якості
> - `qwen2.5:1.5b` — найшвидший, але **нестабільний** (рівень успіху структурованого JSON лише 33%), використовувати не рекомендується

#### Режим GLM (хмара Zhipu AI)

```bash
# Налаштування .env
LLM_PROVIDER=glm
GLM_API_KEY=your_api_key          # Отримати з https://open.bigmodel.cn
GLM_MODEL=glm-4-flash             # Безкоштовна модель
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768      # Має збігатися з розмірністю векторного індексу Neo4j
```

> **Орієнтир продуктивності GLM**: записування ~22с (короткий текст), пошук ~0.34с, нуль помилок Rate Limit, у 2-5 разів повільніше за локальний Ollama, але повністю безкоштовно.

#### Режим GROQ (швидкісне виведення)

```bash
# Налаштування .env
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key         # Отримати з https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile
```

> **Зауваження**: GROQ не надає служби Embedding, потрібен вкладник Ollama (автоматичне повернення) або встановлення `EMBEDDING_PROVIDER` на glm. GROQ має суворі обмеження Rate Limit, високочастотне використання спричинить багато повторних спроб.

#### Режим OpenRouter (агрегація моделей різних постачальників)

```bash
# Налаштування .env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_api_key       # Отримати з https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free   # Можна змінити на будь-яку модель OpenRouter
```

> **Зауваження**: OpenRouter не надає Embedding, автоматично повертається до Ollama `bge-m3`. Перелік моделей див. на https://openrouter.ai/models (включно з кількома безкоштовними моделями `:free`).

#### Режим DeepSeek (Deepseek)

```bash
# Налаштування .env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key         # Отримати з https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash      # Рекомендовано; або deepseek-v4-pro (кращий результат)
```

> **Зауваження**: DeepSeek не надає Embedding, автоматично повертається до Ollama `bge-m3`. `deepseek-chat` / `deepseek-reasoner` будуть виведені з експлуатації 2026-07-24, рекомендується перейти на `deepseek-v4-flash` / `deepseek-v4-pro`. DeepSeek суворо вимагає, щоб prompt у режимі `json_object` містив рядок "json", клієнт уже має вбудований запобіжний захист, додаткового налаштування не потрібно.

## Швидкий запуск

### 1. Попередня підготовка

Переконайтеся, що Neo4j уже працює на локальній машині, і підготуйте відповідну службу відповідно до обраного постачальника LLM:

```bash
# Переконайтеся, що Neo4j працює (обов'язково)
neo4j status
# Або скористайтеся Docker: docker run -d -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/your_password neo4j:latest

# Режим Ollama: переконайтеся, що Ollama працює
ollama list
# Якщо не запущено: ollama serve

# Режим GLM / GROQ: потрібен лише дійсний API Key, локальна служба не потрібна
```

### 2. Встановлення залежностей

```bash
git clone <repo-url>
cd graphiti
uv sync
```

> **Зауваження**: цей проєкт використовує [uv](https://github.com/astral-sh/uv) для керування залежностями. Якщо не встановлено: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 3. Налаштування середовища

```bash
cp .env.example .env
```

Відредагуйте `.env`, **щонайменше** потрібно змінити такі пункти:

```bash
NEO4J_PASSWORD=your_actual_password  # Обов'язково: пароль Neo4j
LLM_PROVIDER=ollama                  # ollama / glm / groq / openrouter / deepseek
OLLAMA_MODEL=qwen2.5:3b              # Режим Ollama: локальна модель LLM
# GLM_API_KEY=your_key               # Режим GLM: API Key Zhipu AI
# GROQ_API_KEY=your_key              # Режим GROQ: GROQ API Key
# OPENROUTER_API_KEY=your_key        # Режим OpenRouter: API Key
# DEEPSEEK_API_KEY=your_key          # Режим DeepSeek: API Key
```

### 4. Запуск служби

```bash
# Режим HTTP (рекомендовано, включає веб-інтерфейс керування)
uv run python graphiti_mcp_server.py --transport http --port 8000

# Або фонове виконання через PM2 (рекомендовано для тривалої роботи)
pm2 start ecosystem.config.cjs
```

### 5. Перевірка служби

Після запуску можна відвідати такі кінцеві точки:

| Кінцева точка | Опис |
|------|------|
| http://localhost:8000/ | Веб-інтерфейс керування |
| http://localhost:8000/mcp | Кінцева точка MCP (для підключення MCP-клієнтів) |
| http://localhost:8000/health | Перевірка справності (liveness) |
| http://localhost:8000/health/ready | Глибока перевірка (включно зі з'єднанням Neo4j) |
| http://localhost:8000/api/stats | Статистика REST API |

## Структура проєкту

```
graphiti/
├── graphiti_mcp_server.py        # Головна точка входу — визначення інструментів MCP (19 інструментів)
├── src/
│   ├── config.py                 # Керування конфігурацією (GraphitiConfig, підтримка нашарування JSON/.env)
│   ├── web_api.py                # REST API веб-інтерфейсу керування (20+ кінцевих точок)
│   ├── ollama_graphiti_client.py  # Клієнт LLM Ollama (розподіл за двома моделями)
│   ├── glm_client.py             # Клієнт LLM GLM (Zhipu AI) (API, сумісний з OpenAI)
│   ├── openrouter_client.py      # Клієнт LLM OpenRouter (агрегація моделей різних постачальників)
│   ├── deepseek_client.py        # Клієнт LLM DeepSeek (json_object + запобіжний захист json)
│   ├── ollama_embedder.py        # Адаптер моделі вкладень Ollama
│   ├── content_preprocessor.py   # Інтелектуальне розбиття вмісту (автоматична сегментація довгих текстів)
│   ├── deduplication.py          # Дедуплікація пам'яті (порівняння за косинусною подібністю)
│   ├── importance.py             # Відстеження важливості та інтелектуальне забування
│   ├── safe_memory_add.py        # Безпечне додавання пам'яті (обхід вилучення сутностей)
│   ├── timezone_utils.py         # Перетворення часового поясу (відображення UTC→локальний часовий пояс)
│   ├── i18n.py                   # Серверна багатомовність (REST залежить від Accept-Language, MCP — від SERVER_LANG)
│   ├── exceptions.py             # Структуроване оброблення винятків (12 класів винятків)
│   └── logging_setup.py          # Система журналювання (часова ротація + моніторинг продуктивності)
├── web/                          # Фронтенд веб-інтерфейсу керування (SPA, без build)
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js                # Обгортка REST API
│       ├── components.js         # Рендеринг UI-компонентів (включно зі сторінкою спільнот)
│       └── app.js                # Маршрутизація SPA, керування станом
├── tests/                        # Набір тестів (183 тести)
│   ├── test_content_preprocessor.py  # Тести логіки розбиття (17 шт.)
│   ├── test_new_features.py      # Тести нових функцій (32 шт.)
│   ├── test_i18n.py             # Тести багатомовності (37 шт.)
│   ├── test_unit.py              # Модульні тести
│   ├── test_web_api.py           # Тести Web API
│   ├── test_web_ui_features.py   # Тести функцій Web UI
│   ├── test_integration_manual.py # Ручні інтеграційні тести
│   └── bench_deepseek_flash_vs_pro.py # Скрипт еталона продуктивності DeepSeek flash/pro
├── tools/                        # Інструменти діагностики розробки
│   ├── status_report.py          # Зведений звіт про стан
│   ├── validate_config.py        # Перевірка конфігурації
│   ├── performance_diagnose.py   # Діагностика продуктивності
│   ├── inspect_schema.py         # Перевірка структури Neo4j
│   └── batch_reprocess.py        # Пакетна повторна обробка
├── docs/                         # Документація
├── logs/                         # Журнали (часова ротація, за замовчуванням зберігаються 30 днів)
├── Dockerfile                    # Контейнеризоване розгортання Docker
└── ecosystem.config.cjs          # Конфігурація PM2
```

## Налаштування MCP-клієнта

### Режим HTTP (рекомендовано)

Підходить для MCP-клієнтів, що підтримують HTTP, як-от Claude Code, Cline:

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

### Режим STDIO

Підходить для клієнтів, що потребують прямого запуску процесу, як-от Claude Desktop:

**Розташування файлу конфігурації:**
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

> **Зауваження**: режим SSE (`--transport sse`) не рекомендується використовувати. MCP 1.x має проблеми сумісності з ініціалізацією сесії, будь ласка, перейдіть на режим HTTP.

## Інструменти MCP (19 шт.)

### Керування пам'яттю (7 шт.)

| Інструмент | Опис |
|------|------|
| `add_memory_simple` | Додавання пам'яті до графа знань (підтримка фонової обробки, інтелектуального розбиття, перевірки дедуплікації) |
| `add_episode_bulk` | Масове додавання кількох спогадів (за замовчуванням фонова обробка) |
| `add_triplet` | Додавання структурованої трійки (обходить LLM, завершується миттєво) |
| `search_memory_nodes` | Пошук вузлів пам'яті (підтримка 16 стратегій пошуку, фільтрації за часом) |
| `search_memory_facts` | Пошук фактів пам'яті (підтримка фільтрації за типом відношення, часовим діапазоном, чинністю) |
| `advanced_search` | Розширений пошук (16 стратегій, повертає вузли+ребра+спільноти+фрагменти) |
| `get_episodes` | Отримання найновіших фрагментів пам'яті |

### Аналіз знань (3 шт.)

| Інструмент | Опис |
|------|------|
| `check_conflicts` | Виявлення конфліктів фактів між двома сутностями (чинні vs застарілі) |
| `get_node_edges` | Дослідження вхідних і вихідних ребер вузла |
| `build_communities` | Запуск виявлення та кластеризації спільнот (за замовчуванням фонова обробка) |

### Обслуговування пам'яті (2 шт.)

| Інструмент | Опис |
|------|------|
| `get_stale_memories` | Запит застарілих спогадів із низькою частотою доступу |
| `cleanup_stale_memories` | Очищення застарілих спогадів (за замовчуванням режим попереднього перегляду dry_run) |

### Керування завданнями

| Інструмент | Опис |
|------|------|
| `get_memory_task_status` | Запит прогресу та результату фонового завдання обробки пам'яті |

### Видалення та запити

| Інструмент | Опис |
|------|------|
| `delete_episode` | Видалення фрагмента пам'яті |
| `delete_entity_edge` | Видалення ребра сутності (відношення) |
| `get_entity_edge` | Отримання детальної інформації про ребро сутності |

### Системне керування

| Інструмент | Опис |
|------|------|
| `get_status` | Отримання стану служби (Neo4j, LLM, вкладник) |
| `test_connection` | Тестування з'єднання Neo4j / LLM / вкладника |
| `clear_graph` | Очищення графової бази даних (підтримка очищення за group_id) |

## Параметри інструментів

### add_memory_simple

| Параметр | Тип | Обов'язково | За замовчуванням | Опис |
|------|------|------|--------|------|
| `name` | string | Y | | Назва пам'яті |
| `episode_body` | string | Y | | Вміст пам'яті (понад 800 символів автоматично розбивається) |
| `group_id` | string | | `"default"` | ID групи (рекомендовано ізолювати за проєктом) |
| `source` | string | | `"text"` | Тип джерела: `text` / `json` / `message` |
| `source_description` | string | | `"MCP Server"` | Опис джерела |
| `use_safe_mode` | bool | | `false` | Безпечний режим (обходить вилучення сутностей, швидко, але пам'ять неможливо знайти пошуком) |
| `background` | bool | | `false` | Фонова обробка (негайно повертає task_id, доречно для довгих текстів) |
| `force` | bool | | `false` | Пропуск перевірки дедуплікації (примусове додавання) |
| `excluded_entity_types` | list | | | Виключені типи сутностей (зменшення непотрібного обсягу вилучення) |

> **Підказки щодо продуктивності**:
> - Короткий текст (<800 символів): пряма обробка, зазвичай завершується за 30-40 секунд
> - Довгий текст (>800 символів): автоматично розбивається на кілька сегментів, конкурентна обробка через `add_episode_bulk` (на ~33% швидше за послідовну)
> - Використання `background=true` дає змогу уникнути блокування виклику MCP, відстежуйте прогрес через `get_memory_task_status`
> - `use_safe_mode=true` завершується миттєво, але пам'ять неможливо знайти інструментами search
> - Коли ввімкнено дедуплікацію, дуже схожі спогади видаватимуть попередження (`force=true` дає змогу пропустити)

### add_episode_bulk

| Параметр | Тип | Обов'язково | За замовчуванням | Опис |
|------|------|------|--------|------|
| `episodes` | list | Y | | Перелік спогадів, кожен елемент містить `name` і `content` |
| `group_id` | string | | `"default"` | ID групи |
| `source` | string | | `"text"` | Тип джерела |
| `background` | bool | | `true` | Фонова обробка (масове зазвичай тривале) |

### add_triplet

| Параметр | Тип | Обов'язково | За замовчуванням | Опис |
|------|------|------|--------|------|
| `source_name` | string | Y | | Назва вихідної сутності (наприклад, "Alice") |
| `target_name` | string | Y | | Назва цільової сутності (наприклад, "Google") |
| `relation_name` | string | Y | | Назва відношення (наприклад, "works_at") |
| `fact` | string | Y | | Опис факту (наприклад, "Alice works at Google") |
| `group_id` | string | | `"default"` | ID групи |
| `source_labels` | list | | | Мітки вихідної сутності |
| `target_labels` | list | | | Мітки цільової сутності |

### search_memory_nodes

| Параметр | Тип | Обов'язково | За замовчуванням | Опис |
|------|------|------|--------|------|
| `query` | string | Y | | Ключове слово пошуку (природна мова) |
| `max_nodes` | int | | `10` | Максимальна кількість, що повертається |
| `group_ids` | list | | | Фільтрація за групами (об'єднаний пошук по кількох групах) |
| `entity_types` | list | | | Фільтрація за типом сутності |
| `search_recipe` | string | | | Стратегія пошуку (див. розширений пошук) |
| `created_after` | string | | | Нижня межа часу створення (ISO datetime) |
| `created_before` | string | | | Верхня межа часу створення (ISO datetime) |

### search_memory_facts

| Параметр | Тип | Обов'язково | За замовчуванням | Опис |
|------|------|------|--------|------|
| `query` | string | Y | | Ключове слово пошуку |
| `max_facts` | int | | `10` | Максимальна кількість, що повертається |
| `group_ids` | list | | | Фільтрація за групами |
| `center_node_uuid` | string | | | UUID центрального вузла (дослідження відношень конкретного вузла) |
| `edge_types` | list | | | Фільтрація за типом відношення (наприклад, `["works_at"]`) |
| `created_after` | string | | | Нижня межа часу створення (ISO datetime) |
| `created_before` | string | | | Верхня межа часу створення (ISO datetime) |
| `only_valid` | bool | | `false` | Повертати лише нескасовані факти |

### advanced_search

| Параметр | Тип | Обов'язково | За замовчуванням | Опис |
|------|------|------|--------|------|
| `query` | string | Y | | Ключове слово пошуку |
| `search_recipe` | string | | `"combined_rrf"` | Стратегія пошуку (16 на вибір) |
| `max_results` | int | | `10` | Максимальна кількість, що повертається |
| `group_ids` | list | | | Фільтрація за групами |
| `center_node_uuid` | string | | | UUID центрального вузла |

**Доступні стратегії пошуку (search_recipe):**

| Категорія | Стратегія | Опис |
|------|------|------|
| Комбінований | `combined_rrf` | Комбіноване злиття RRF (за замовчуванням, рекомендовано) |
| Комбінований | `combined_mmr` | Комбіноване переранжування різноманітності MMR |
| Комбінований | `combined_cross_encoder` | Комбіноване точне ранжування Cross-Encoder |
| Ребро | `edge_rrf` / `edge_mmr` / `edge_cross_encoder` | Пошук ребер (3 види впорядкування) |
| Ребро | `edge_node_distance` / `edge_episode_mentions` | Пошук ребер (графова відстань/кількість згадувань) |
| Вузол | `node_rrf` / `node_mmr` / `node_cross_encoder` | Пошук вузлів (3 види впорядкування) |
| Вузол | `node_node_distance` / `node_episode_mentions` | Пошук вузлів (графова відстань/кількість згадувань) |
| Спільнота | `community_rrf` / `community_mmr` / `community_cross_encoder` | Пошук спільнот |

### check_conflicts

| Параметр | Тип | Обов'язково | За замовчуванням | Опис |
|------|------|------|--------|------|
| `source_name` | string | Y | | Назва вихідної сутності |
| `target_name` | string | Y | | Назва цільової сутності |
| `group_id` | string | | `"default"` | ID групи |

### get_node_edges

| Параметр | Тип | Обов'язково | За замовчуванням | Опис |
|------|------|------|--------|------|
| `node_uuid` | string | Y | | UUID вузла |
| `include_inbound` | bool | | `true` | Включати вхідні ребра |
| `include_outbound` | bool | | `true` | Включати вихідні ребра |
| `max_edges` | int | | `50` | Максимальна кількість, що повертається |

### build_communities

| Параметр | Тип | Обов'язково | За замовчуванням | Опис |
|------|------|------|--------|------|
| `group_ids` | list | | | Указати групи (залиште порожнім — усі) |
| `background` | bool | | `true` | Фонова обробка |

### get_stale_memories

| Параметр | Тип | Обов'язково | За замовчуванням | Опис |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Скільки днів без доступу вважати застарілим |
| `min_access_count` | int | | `2` | Зараховувати лише з кількістю доступів нижче цього значення |
| `group_id` | string | | | Фільтрація за групами |
| `limit` | int | | `50` | Максимальна кількість, що повертається |

### cleanup_stale_memories

| Параметр | Тип | Обов'язково | За замовчуванням | Опис |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Поріг застарілих днів |
| `min_access_count` | int | | `2` | Поріг мінімальної кількості доступів |
| `group_id` | string | | | Фільтрація за групами |
| `dry_run` | bool | | `true` | Режим попереднього перегляду (без фактичного видалення) |
| `limit` | int | | `50` | Максимальна кількість для обробки |

### get_memory_task_status

| Параметр | Тип | Обов'язково | Опис |
|------|------|------|------|
| `task_id` | string | Y | ID фонового завдання (повертається `add_memory_simple(background=true)`) |

## Веб-інтерфейс керування

У режимі HTTP можна користуватися, відвідавши `http://localhost:8000/`.

**Функції:**
- Панель моніторингу — статистика кількості вузлів, фактів, фрагментів пам'яті
- Вузли сутностей — перегляд, фільтрація, векторний пошук
- Факти-відношення — перегляд, фільтрація, векторний пошук
- Фрагменти пам'яті — перегляд, повнотекстовий пошук, видалення
- Перегляд спільнот — перелік вузлів спільнот, зведення, запуск побудови спільнот
- Форма трійок — пряме додавання структурованих знань «суб'єкт-відношення-об'єкт»
- Керування Group — фільтрація за групами, пакетне видалення
- Візуалізація графа знань — графічне відображення відношень вузлів
- AI-запитання та відповіді — інтелектуальні запитання та відповіді на основі графа знань
- Аналіз якості — аналіз якості та покриття пам'яті
- Перемикання теми — темна/світла тема

**REST API:**

| Кінцева точка | Метод | Опис |
|------|------|------|
| `/api/stats` | GET | Статистика панелі моніторингу |
| `/api/groups` | GET | Отримання всіх group_id |
| `/api/nodes` | GET | Перегляд вузлів сутностей (посторінково) |
| `/api/facts` | GET | Перегляд фактів (посторінково) |
| `/api/episodes` | GET | Перегляд фрагментів пам'яті (посторінково) |
| `/api/search/nodes` | GET | Векторний пошук вузлів |
| `/api/search/facts` | GET | Векторний пошук фактів |
| `/api/search/advanced` | GET | Розширений пошук (16 стратегій) |
| `/api/communities` | GET | Перегляд вузлів спільнот (посторінково) |
| `/api/communities/build` | POST | Запуск побудови спільнот |
| `/api/memory/add-bulk` | POST | Масове додавання пам'яті |
| `/api/memory/add-triplet` | POST | Додавання трійки |
| `/api/memory/tasks` | GET | Перелік фонових завдань (підтримка фільтрації за станом) |
| `/api/memory/tasks/{id}` | GET | Запит стану окремого завдання |
| `/api/analytics/stale` | GET | Запит застарілих спогадів |
| `/api/analytics/cleanup` | POST | Очищення застарілих спогадів |
| `/api/nodes/{uuid}` | DELETE | Видалення вузла |
| `/api/episodes/{uuid}` | DELETE | Видалення фрагмента пам'яті |
| `/api/facts/{uuid}` | DELETE | Видалення факту |
| `/api/groups/{group_id}` | DELETE | Видалення цілої group |

## Конфігурація

### Змінні середовища (.env)

Конфігурація використовує механізм нашарування: файл конфігурації JSON як основа, змінні середовища перевизначають окремі значення.

```bash
# === Обов'язково ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password        # Має бути змінено

# === Вибір постачальника LLM ===
LLM_PROVIDER=ollama                 # ollama / glm / groq / openrouter / deepseek

# === Постачальник Embedding (необов'язково, за замовчуванням слідує за LLM_PROVIDER) ===
# Лише glm використовує GLM Embedding, решта завжди використовує Ollama bge-m3
# EMBEDDING_PROVIDER=ollama         # ollama / glm

# === Конфігурація Ollama (використовується, коли LLM_PROVIDER=ollama) ===
OLLAMA_MODEL=qwen2.5:3b             # Основна модель (рекомендовано qwen2.5:3b)
OLLAMA_SMALL_MODEL=qwen2.5:3b       # Мала модель (для простих завдань, можна іншу модель)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.1

# === Конфігурація GLM (використовується, коли LLM_PROVIDER=glm) ===
GLM_API_KEY=your_api_key            # Отримати з https://open.bigmodel.cn
GLM_MODEL=glm-4-flash               # Безкоштовна модель
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768

# === Конфігурація GROQ (використовується, коли LLM_PROVIDER=groq) ===
GROQ_API_KEY=your_api_key           # Отримати з https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile

# === Конфігурація OpenRouter (використовується, коли LLM_PROVIDER=openrouter) ===
OPENROUTER_API_KEY=your_api_key     # Отримати з https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free

# === Конфігурація DeepSeek (використовується, коли LLM_PROVIDER=deepseek) ===
DEEPSEEK_API_KEY=your_api_key       # Отримати з https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash    # Або deepseek-v4-pro

# === Модель вкладень Ollama (використовується завжди, окрім вкладень glm) ===
OLLAMA_EMBEDDING_MODEL=bge-m3
OLLAMA_EMBEDDING_DIMENSIONS=768

# === Відображення та мова (необов'язково) ===
GRAPHITI_DISPLAY_TIMEZONE=Asia/Taipei # Часовий пояс відображення часових міток, що повертаються API (назва IANA; зберігання залишається UTC)
SERVER_LANG=zh-TW                     # Мова відповідей інструментів MCP (повні локалі див. src/i18n.py); REST API натомість залежить від Accept-Language

# === Продуктивність пам'яті (необов'язково) ===
GRAPHITI_CHUNK_THRESHOLD=800         # Поріг кількості символів, що запускає інтелектуальне розбиття
GRAPHITI_MAX_CHUNK_SIZE=600          # Максимальна кількість символів на сегмент
GRAPHITI_MAX_COROUTINES=10            # Максимальна кількість конкурентних корутин
GRAPHITI_DEFAULT_BACKGROUND=false    # Чи обробляти за замовчуванням у фоновому режимі

# === Відстеження важливості та інтелектуальне забування (необов'язково) ===
ENABLE_IMPORTANCE_TRACKING=true      # Увімкнути відстеження доступу
IMPORTANCE_WEIGHT=0.1                # Вага важливості
STALE_DAYS_THRESHOLD=30              # Поріг застарілих днів
STALE_MIN_ACCESS_COUNT=2             # Мінімальна кількість доступів

# === Журналювання ===
LOG_FILE=logs/graphiti_mcp_server.log
LOG_LEVEL=INFO
```

> **Повний перелік змінних середовища** див. у `.env.example`

### Файл конфігурації JSON

Підходить для конфігурації, що потребує контролю версій (змінні середовища все одно можуть перевизначати):

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

## Фонове виконання PM2

```bash
npm install -g pm2

pm2 start ecosystem.config.cjs      # Запуск
pm2 status                           # Стан
pm2 logs graphiti-mcp-http           # Журнали в реальному часі
pm2 restart graphiti-mcp-http --update-env  # Перезапуск (повторне завантаження .env)

pm2 save && pm2 startup              # Налаштувати автозапуск під час завантаження
```

> **Підказка**: після зміни `.env` обов'язково перезапустіть з прапорцем `--update-env`, інакше змінні середовища не оновляться.

## Розгортання Docker

```bash
docker build -t graphiti-mcp .

# Зауваження: контейнер Docker має бути здатним підключатися до Neo4j та Ollama
# Використання host network — найпростіше
docker run -p 8000:8000 --env-file .env --network host graphiti-mcp

# Або явно вкажіть адреси зовнішніх служб
docker run -p 8000:8000 \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --env-file .env graphiti-mcp
```

## Тестування

```bash
# Виконати всі тести (183 шт., близько 1 секунди)
uv run python -m pytest tests/

# Детальний вивід
uv run python -m pytest tests/ -v

# Виконати лише конкретний тест
uv run python -m pytest tests/test_content_preprocessor.py -v
uv run python -m pytest tests/test_new_features.py -v
uv run python -m pytest tests/test_unit.py -v
```

> **Зауваження**: 3 async-тести у `test_integration_manual.py` потребують встановлення `pytest-asyncio`, за відсутності показуватимуть Failed, але це не впливає на інші тести. `bench_deepseek_flash_vs_pro.py` — це скрипт еталона продуктивності, а не модульний тест.

## Усунення несправностей

### Збій з'єднання Neo4j

```bash
neo4j status                              # Перевірити стан служби
cypher-shell -u neo4j -p your_password    # Підтвердити правильність пароля
curl http://localhost:7474                 # Підтвердити HTTP-порт
```

Поширені причини:
- Neo4j не запущено
- Неправильний пароль (`NEO4J_PASSWORD` у `.env`)
- Порт зайнято або блокується брандмауером

### Збій з'єднання LLM

**Режим Ollama:**
```bash
ollama serve                # Запустити службу Ollama
ollama list                 # Перевірити встановлені моделі
ollama pull qwen2.5:3b      # Встановити відсутню модель
```

Поширені причини: Ollama не запущено, модель не встановлено, недостатньо пам'яті GPU

**Режим GLM:**
- Підтвердьте правильність `GLM_API_KEY`
- Підтвердьте `GLM_EMBEDDING_DIMENSIONS=768` (має збігатися з векторним індексом Neo4j)
- Кінцева точка GLM API: `https://open.bigmodel.cn/api/paas/v4/`

**Режим GROQ:**
- Підтвердьте правильність `GROQ_API_KEY`
- За частих Rate Limit розгляньте перемикання на режим GLM
- GROQ не надає Embedding, потрібно переконатися, що вкладник Ollama доступний

**Режим OpenRouter:**
- Підтвердьте правильність `OPENROUTER_API_KEY`, а `OPENROUTER_MODEL` — дійсний ID моделі (див. https://openrouter.ai/models)
- Не надає Embedding, потрібно переконатися, що вкладник Ollama доступний

**Режим DeepSeek:**
- Підтвердьте правильність `DEEPSEEK_API_KEY`
- Якщо з'являється `Prompt must contain the word 'json'`: це жорстка вимога режиму `json_object` DeepSeek, клієнт уже має вбудований запобіжний захист; якщо все одно з'являється, підтвердьте, що використовується найновіша версія `src/deepseek_client.py`, і перезапустіть службу
- Не надає Embedding, потрібно переконатися, що вкладник Ollama доступний

### Помилка з'єднання MCP

Якщо з'являється `Invalid request parameters` або `Received request before initialization was complete`:

1. Підтвердьте використання транспортного режиму HTTP (**не використовуйте SSE**)
2. Підтвердьте, що клієнт налаштовано на `"type": "http"`, `"url": "http://localhost:8000/mcp"`
3. Перезапустіть службу: `pm2 restart graphiti-mcp-http --update-env`
4. У Claude Code виконайте `/mcp` для повторного підключення

### Повільне додавання пам'яті

- **Ollama**: перевірте розмір моделі (`qwen2.5:3b` у 5-10 разів швидша за `7b`), підтвердьте використання GPU (`ollama ps`)
- **GLM**: кожен add_episode потребує 10-20+ мережевих обходів LLM, ~22с для короткого тексту є нормальним значенням
- **GROQ**: Rate Limit спричинить багато повторних спроб, за частого використання рекомендується перейти на GLM або Ollama
- Використовуйте `background=true`, щоб уникнути блокування
- Зменшіть `GRAPHITI_CHUNK_THRESHOLD`, щоб довгі тексти розбивалися раніше

### Проблеми PM2

```bash
pm2 status                                        # Перевірити стан
pm2 logs graphiti-mcp-http --err --lines 50        # Журнал помилок
lsof -i :8000                                     # Перевірити зайнятість порту
pm2 delete graphiti-mcp-http && pm2 start ecosystem.config.cjs  # Повний перезапуск
```

## Інструменти діагностики розробки

```bash
uv run python tools/status_report.py           # Зведений звіт про стан (Neo4j + Ollama + конфігурація)
uv run python tools/validate_config.py         # Перевірка цілісності .env та конфігурації
uv run python tools/performance_diagnose.py    # Діагностика продуктивності LLM
uv run python tools/inspect_schema.py          # Перевірка індексів та обмежень Neo4j
uv run python tools/migrate_embeddings.py      # Міграція моделі Embedding (повторне генерування векторів після зміни моделі)
```

### Міграція моделі Embedding

Після перемикання моделі embedding (наприклад, `nomic-embed-text` → `bge-m3`) можна скористатися інструментом міграції для повторного генерування всіх наявних векторів, щоб забезпечити узгоджену якість пошуку:

```bash
# Попередній перегляд кількості, що потребує міграції
uv run python tools/migrate_embeddings.py --dry-run

# Повна міграція (підтримка продовження з контрольної точки)
uv run python tools/migrate_embeddings.py

# Мігрувати лише вказану group
uv run python tools/migrate_embeddings.py --group-id myproject

# Продовжити з контрольної точки (повторний запуск після переривання)
uv run python tools/migrate_embeddings.py --resume
```

> **Сумісність**: `bge-m3` нативно має 1024 виміри, система автоматично обрізає до 768 вимірів для сумісності з наявним векторним індексом Neo4j. Дані до та після міграції можуть співіснувати, але рекомендується виконати повну міграцію для досягнення найкращої якості пошуку.

## Документація

- [Інструкції з використання інструментів](../使用工具的指令.md) — Посібник із використання інструментів MCP та найкращі практики
- [Graphiti Memory Rules](../graphiti-memory-rules.md) — Опис правил пам'яті

## Ліцензія

MIT License
