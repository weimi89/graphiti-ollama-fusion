# Graphiti MCP Server

שירות זיכרון מבוסס גרף ידע — שרת MCP המשלב מספר ספקי LLM ‏(Ollama / GLM / GROQ / OpenRouter / DeepSeek) עם מסד נתוני הגרף Neo4j.

פותח כהרחבה של [getzep/graphiti](https://github.com/getzep/graphiti), תומך במעבר גמיש בין Ollama מקומי ל‑LLM ענני, וניתן לציין ספק Embedding באופן עצמאי (מנותק מה‑LLM).

## תכונות בולטות

- **ניהול זיכרון חכם** — שימוש בגרף ידע לאחסון ואחזור של יחסי זיכרון מורכבים
- **חיפוש סמנטי** — חיפוש היברידי מבוסס הטמעות וקטוריות (וקטור + מילות מפתח + מעבר על הגרף)
- **‏16 אסטרטגיות חיפוש** — חיפוש מתקדם התומך בשיטות דירוג מחדש מרובות כגון RRF,‏ MMR,‏ Cross-Encoder
- **מספר ספקי LLM** — תמיכה ב‑Ollama ‏(מקומי), ‏GLM ‏(智谱 AI חינמי), ‏GROQ ‏(הסקה מהירה), ‏OpenRouter ‏(אגרגציה של מודלים מספקים שונים), ‏DeepSeek ‏(深度求索), עם מעבר בלחיצה אחת באמצעות משתני סביבה
- **ניתוק Embedding מ‑LLM** — ניתן לציין את מנוע ההטמעה באופן עצמאי באמצעות `EMBEDDING_PROVIDER`, ו‑LLM ענני נסוג אוטומטית ל‑`bge-m3` מקומי
- **חלוקת מודל כפולה** — במצב Ollama משימות מורכבות משתמשות במודל הראשי, ומשימות פשוטות עוברות אוטומטית למודל קטן לשיפור הביצועים
- **חלוקה חכמה של תוכן** — טקסט ארוך מעובד אוטומטית בקטעים, מה שמפחית את העומס על ה‑LLM ‏(סף ניתן להגדרה)
- **עיבוד זיכרון ברקע** — הוספת זיכרון יכולה לרוץ ברקע, וקריאת ה‑MCP חוזרת מיד; מצב המשימות נשמר ב‑SQLite, ומשימות שלא הושלמו משוחזרות אוטומטית לאחר הפעלה מחדש
- **הסרת כפילויות בזיכרון** — מזהה אוטומטית זיכרונות קיימים דומים מאוד, נמנע מאחסון כפול
- **זיהוי קונפליקטים** — מזהה עובדות סותרות בין שתי ישויות, ומבחין בין מידע שפג תוקפו לבין מידע תקף
- **זיהוי קהילות** — אשכול אוטומטי של ישויות קשורות מבוסס אלגוריתם Label Propagation
- **מעקב חשיבות** — רישום אוטומטי של תדירות הגישה לישויות, ותוצאות חיפוש ממוינות לפי חשיבות
- **שכחה חכמה** — זיהוי וניקוי של זיכרונות מיושנים בעלי גישה נמוכה, לשמירת גרף תמציתי
- **ייבוא בכמות גדולה** — הגשת מספר זיכרונות בבת אחת, מתאים להעברת נתונים בכמות גדולה
- **שלשות מובנות** — הוספה ישירה של "נושא-יחס-מושא", מדלגת על חילוץ ה‑LLM ומסתיימת בשנייה
- **ממשק ניהול Web** — לוח מחוונים מובנה, עיון, חיפוש, הדמיית גרף ידע, שאלות ותשובות מבוססות AI, עיון בקהילות, תחזוקת איכות, ייבוא בכמות גדולה, הגדרות בזמן ריצה
- **רב‑לשוניות ‏(i18n)** — הודעות התגובה תומכות ב‑33 שפות (כולל zh-TW / en / zh-CN / ja / pt-BR / ko / es / de / fr ועוד; zh-TW/en/zh-CN/ja נכתבו ידנית, השאר מסופקים על ידי שכבת generated); כלי MCP לפי `SERVER_LANG`, ו‑REST API מנהל משא ומתן אוטומטי לפי כותרת HTTP‏ `Accept-Language`
- **ערכת נושא כהה/בהירה** — ממשק ה‑Web תומך במעבר בין ערכות נושא
- **מצב בטוח** — אפשרות להוספת זיכרון מהירה המדלגת על חילוץ ישויות
- **תמיכה ב‑Docker** — Dockerfile מובנה, תומך בפריסה מבוססת קונטיינרים
- **בטיחות בו‑זמנית** — asyncio.Lock מגן על האתחול, מונע תנאי מרוץ
- **בדיקת בריאות שכבתית** — `/health` ‏(liveness) + `/health/ready` ‏(readiness)

## דרישות מערכת

| פריט | דרישה |
|------|------|
| Python | ‏3.10+ ‏(מומלץ 3.11+) |
| Neo4j | ‏4.0+ ‏(`bolt://localhost:7687`) |
| ספק LLM | ‏Ollama / GLM / GROQ / OpenRouter / DeepSeek ‏(אחד מתוך חמישה) |
| Node.js | ‏18+ ‏(בשימוש רק עבור הרצה ברקע עם PM2, אופציונלי) |
| שטח דיסק | ‏~3GB ‏(מודלי Ollama + נתוני Neo4j) |

### בחירת ספק LLM

מעבר באמצעות משתנה הסביבה `LLM_PROVIDER` ‏(`ollama` / `glm` / `groq` / `openrouter` / `deepseek`):

| ספק | מאפיינים | מודל LLM | Embedding | תרחיש מתאים |
|--------|------|----------|-----------|----------|
| **Ollama** ‏(ברירת מחדל) | מקומי לחלוטין, הנתונים לא יוצאים מהמכונה | `qwen2.5:3b` | `bge-m3` ‏(מצוין לסינית + RAG) | יש GPU, מייחס חשיבות לפרטיות |
| **GLM** | ענן חינמי, יציב ללא הגבלת קצב | `glm-4-flash` ‏(חינמי) | `embedding-3` | אין GPU, תרחישים אינטנסיביים בחיפוש |
| **GROQ** | הסקה במהירות גבוהה במיוחד | `llama-3.3-70b-versatile` | נסיגה ל‑Ollama‏ `bge-m3` | כתיבה מדי פעם, חתירה לאיכות |
| **OpenRouter** | אגרגציה של מודלים מספקים שונים, כולל מכסה חינמית | `stepfun/step-3.5-flash:free` וכו' | נסיגה ל‑Ollama‏ `bge-m3` | רוצים להשתמש במודל ענני מסוים |
| **DeepSeek** | ענן 深度求索, תמורה גבוהה למחיר | `deepseek-v4-flash` / `deepseek-v4-pro` | נסיגה ל‑Ollama‏ `bge-m3` | הבנת סינית, ענן בעלות נמוכה |

> **ניתוק Embedding מ‑LLM**: מנוע ההטמעה מצוין באופן עצמאי באמצעות `EMBEDDING_PROVIDER` ‏(`ollama` / `glm`), וכשאינו מוגדר הוא עוקב אחר `LLM_PROVIDER`. בפועל רק `glm` משתמש ב‑GLM‏ `embedding-3`, וכל השאר (כולל LLM ענני שאינו מספק Embedding כגון GROQ / OpenRouter / DeepSeek) משתמש אוטומטית ב‑Ollama‏ `bge-m3`. **לכן בעת שימוש בכל LLM ענני, עדיין נדרש Ollama מקומי לאספקת שירות הטמעה (אלא אם embedding מוגדר אף הוא ל‑glm).**

#### מצב Ollama ‏(מקומי)

```bash
# מודל LLM ראשי (מומלץ qwen2.5:3b, האיזון הטוב ביותר בין מהירות ליציבות)
ollama pull qwen2.5:3b

# מודל הטמעה (חובה, בשימוש לחיפוש וקטורי)
ollama pull bge-m3
```

> **הערות לבחירת מודל**:
> - `qwen2.5:3b` — מומלץ, ‏~2 שניות/קריאה, ‏~100 t/s, פלט מובנה של graphiti-core יציב ב‑100%
> - `qwen2.5:7b` — אפקטיבי יותר אך איטי פי 5-10, מתאים לתרחישים החותרים לאיכות
> - `qwen2.5:1.5b` — המהיר ביותר אך **לא יציב** ‏(שיעור הצלחה של JSON מובנה רק 33%), לא מומלץ לשימוש

#### מצב GLM ‏(ענן 智谱 AI)

```bash
# הגדרת .env
LLM_PROVIDER=glm
GLM_API_KEY=your_api_key          # מתקבל מ‑https://open.bigmodel.cn
GLM_MODEL=glm-4-flash             # מודל חינמי
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768      # חייב להתאים לממד אינדקס הווקטורים של Neo4j
```

> **התייחסות לביצועי GLM**: כתיבה ~22 שניות (טקסט קצר), חיפוש ~0.34 שניות, אפס שגיאות Rate Limit, איטי פי 2-5 מ‑Ollama מקומי אך חינמי לחלוטין.

#### מצב GROQ ‏(הסקה מהירה)

```bash
# הגדרת .env
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key         # מתקבל מ‑https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile
```

> **הערה**: GROQ אינו מספק שירות Embedding, יש לשלב עם מנוע ההטמעה של Ollama ‏(נסיגה אוטומטית) או להגדיר את `EMBEDDING_PROVIDER` ל‑glm. ל‑GROQ יש Rate Limit מחמיר, ושימוש בתדירות גבוהה יפעיל ניסיונות חוזרים רבים.

#### מצב OpenRouter ‏(אגרגציה של מודלים מספקים שונים)

```bash
# הגדרת .env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_api_key       # מתקבל מ‑https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free   # ניתן לשנות לכל מודל OpenRouter
```

> **הערה**: OpenRouter אינו מספק Embedding, נסוג אוטומטית ל‑Ollama‏ `bge-m3`. רשימת המודלים זמינה ב‑https://openrouter.ai/models ‏(כולל מספר מודלים חינמיים `:free`).

#### מצב DeepSeek ‏(深度求索)

```bash
# הגדרת .env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key         # מתקבל מ‑https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash      # מומלץ; או deepseek-v4-pro (אפקטיבי יותר)
```

> **הערה**: DeepSeek אינו מספק Embedding, נסוג אוטומטית ל‑Ollama‏ `bge-m3`. ‏`deepseek-chat` / `deepseek-reasoner` יוצאו משימוש ב‑2026-07-24, מומלץ לעבור ל‑`deepseek-v4-flash` / `deepseek-v4-pro`. ‏DeepSeek דורש באופן מחמיר שה‑prompt במצב `json_object` יכיל את המחרוזת "json", ובלקוח כבר מובנה מנגנון הגנה כברירת מחדל, ללא צורך בהגדרה נוספת.

## הפעלה מהירה

### 1. הכנה מקדימה

ודאו ש‑Neo4j כבר פועל במכונה המקומית, והכינו את השירות המתאים בהתאם לספק ה‑LLM שנבחר:

```bash
# ודאו ש‑Neo4j פועל (חובה)
neo4j status
# או השתמשו ב‑Docker: docker run -d -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/your_password neo4j:latest

# מצב Ollama: ודאו ש‑Ollama פועל
ollama list
# אם לא הופעל: ollama serve

# מצב GLM / GROQ: נדרש רק API Key תקף, ללא צורך בשירות מקומי
```

### 2. התקנת תלויות

```bash
git clone <repo-url>
cd graphiti
uv sync
```

> **הערה**: פרויקט זה משתמש ב‑[uv](https://github.com/astral-sh/uv) לניהול תלויות. אם לא הותקן: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 3. הגדרת הסביבה

```bash
cp .env.example .env
```

ערכו את `.env`, **לכל הפחות** יש לשנות את הפריטים הבאים:

```bash
NEO4J_PASSWORD=your_actual_password  # חובה: סיסמת Neo4j
LLM_PROVIDER=ollama                  # ollama / glm / groq / openrouter / deepseek
OLLAMA_MODEL=qwen2.5:3b              # מצב Ollama: מודל LLM מקומי
# GLM_API_KEY=your_key               # מצב GLM: מפתח API של 智谱 AI
# GROQ_API_KEY=your_key              # מצב GROQ: מפתח API של GROQ
# OPENROUTER_API_KEY=your_key        # מצב OpenRouter: מפתח API
# DEEPSEEK_API_KEY=your_key          # מצב DeepSeek: מפתח API
```

### 4. הפעלת השירות

```bash
# מצב HTTP (מומלץ, כולל ממשק ניהול Web)
uv run python graphiti_mcp_server.py --transport http --port 8000

# או הרצה ברקע עם PM2 (מומלץ להרצה ארוכת טווח)
pm2 start ecosystem.config.cjs
```

### 5. אימות השירות

לאחר ההפעלה ניתן לגשת לנקודות הקצה הבאות:

| נקודת קצה | תיאור |
|------|------|
| http://localhost:8000/ | ממשק ניהול Web |
| http://localhost:8000/mcp | נקודת קצה MCP ‏(לחיבור לקוחות MCP) |
| http://localhost:8000/health | בדיקת בריאות ‏(liveness) |
| http://localhost:8000/health/ready | בדיקה מעמיקה ‏(כולל חיבור Neo4j) |
| http://localhost:8000/api/stats | סטטיסטיקות REST API |

## מבנה הפרויקט

```
graphiti/
├── graphiti_mcp_server.py        # נקודת כניסה ראשית — הגדרת כלי MCP (19 כלים)
├── src/
│   ├── config.py                 # ניהול תצורה (GraphitiConfig, תומך בערימה JSON/.env)
│   ├── web_api.py                # REST API של ממשק ניהול Web (30+ נקודות קצה)
│   ├── ollama_graphiti_client.py  # לקוח LLM של Ollama (חלוקת מודל כפולה)
│   ├── openai_compat_client.py   # מחלקת בסיס LLM תואמת OpenAI (json_object + schema פשוט + הגנת json)
│   ├── glm_client.py             # לקוח LLM של GLM (智谱 AI) (יורש OpenAICompatClient)
│   ├── openrouter_client.py      # לקוח LLM של OpenRouter (יורש OpenAICompatClient)
│   ├── deepseek_client.py        # לקוח LLM של DeepSeek (יורש OpenAICompatClient)
│   ├── ollama_embedder.py        # מתאם מודל הטמעה של Ollama
│   ├── content_preprocessor.py   # חלוקה חכמה של תוכן (חלוקה אוטומטית של טקסט ארוך)
│   ├── deduplication.py          # הסרת כפילויות זיכרון (השוואת דמיון קוסינוס)
│   ├── importance.py             # מעקב חשיבות ושכחה חכמה
│   ├── safe_memory_add.py        # הוספת זיכרון בטוחה (מדלגת על חילוץ ישויות)
│   ├── task_store.py             # שמירת משימות ברקע ב‑SQLite (TaskStore)
│   ├── timezone_utils.py         # המרת אזור זמן (UTC→תצוגת אזור זמן מקומי)
│   ├── i18n.py                   # רב‑לשוניות בצד השרת (REST לפי Accept-Language, MCP לפי SERVER_LANG)
│   ├── i18n_generated.py         # כיסויי שפה שנוצרו אוטומטית (GENERATED_MESSAGE_OVERRIDES)
│   ├── exceptions.py             # טיפול מובנה בחריגות (12 מחלקות חריגה)
│   └── logging_setup.py          # מערכת לוגים (סבב לפי זמן + ניטור ביצועים)
├── web/                          # צד הלקוח של ממשק ניהול Web (SPA, ללא build)
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js                # עטיפת REST API
│       ├── components.js         # רינדור רכיבי UI (כולל דף קהילות)
│       └── app.js                # ניתוב SPA, ניהול מצב
├── tests/                        # ערכת בדיקות (203 בדיקות)
│   ├── test_content_preprocessor.py  # בדיקת לוגיקת חלוקה (17 בדיקות)
│   ├── test_new_features.py      # בדיקת תכונות חדשות (32 בדיקות)
│   ├── test_i18n.py             # בדיקת רב‑לשוניות (57 בדיקות)
│   ├── test_unit.py              # בדיקות יחידה
│   ├── test_web_api.py           # בדיקות Web API
│   ├── test_web_ui_features.py   # בדיקות תכונות Web UI
│   ├── test_integration_manual.py # בדיקות אינטגרציה ידניות
│   └── bench_deepseek_flash_vs_pro.py # סקריפט מדד ביצועים DeepSeek flash/pro
├── tools/                        # כלי אבחון לפיתוח
│   ├── status_report.py          # דוח מצב משולב
│   ├── validate_config.py        # אימות תצורה
│   ├── performance_diagnose.py   # אבחון ביצועים
│   ├── inspect_schema.py         # בדיקת מבנה Neo4j
│   ├── batch_reprocess.py        # עיבוד מחדש באצווה
│   └── migrate_embeddings.py     # העברת מודל Embedding (יצירה מחדש של וקטורים לאחר החלפת מודל)
├── docs/                         # תיעוד
├── logs/                         # לוגים (סבב לפי זמן, ברירת מחדל לשמירה 30 ימים)
├── Dockerfile                    # פריסת קונטיינר Docker
└── ecosystem.config.cjs          # תצורת PM2
```

## הגדרת לקוח MCP

### מצב HTTP ‏(מומלץ)

מתאים ללקוחות MCP התומכים ב‑HTTP כגון Claude Code,‏ Cline:

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

### מצב STDIO

מתאים ללקוחות הזקוקים להפעלה ישירה של תהליך כגון Claude Desktop:

**מיקום קובץ התצורה:**
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

> **הערה**: מצב SSE ‏(`--transport sse`) אינו מומלץ עוד. ל‑MCP 1.x יש בעיות תאימות באתחול session, אנא עברו למצב HTTP.

## כלי MCP ‏(19 כלים)

### ניהול זיכרון ‏(7 כלים)

| כלי | תיאור |
|------|------|
| `add_memory_simple` | הוספת זיכרון לגרף הידע (תומך בעיבוד ברקע, חלוקה חכמה, בדיקת כפילויות) |
| `add_episode_bulk` | הוספת מספר זיכרונות באצווה (ברירת מחדל עיבוד ברקע) |
| `add_triplet` | הוספת שלשה מובנית (מדלגת על LLM, מסתיימת בשנייה) |
| `search_memory_nodes` | חיפוש צמתי זיכרון (תומך ב‑16 אסטרטגיות חיפוש, סינון לפי זמן) |
| `search_memory_facts` | חיפוש עובדות זיכרון (תומך בסינון לפי סוג יחס, טווח זמן, סינון תקפות) |
| `advanced_search` | חיפוש מתקדם (16 אסטרטגיות, מחזיר צמתים+קשתות+קהילות+קטעים) |
| `get_episodes` | קבלת קטעי הזיכרון האחרונים |

### ניתוח ידע ‏(3 כלים)

| כלי | תיאור |
|------|------|
| `check_conflicts` | זיהוי קונפליקטים עובדתיים בין שתי ישויות (תקף לעומת פג תוקף) |
| `get_node_edges` | חקירת קשתות הנכנסות והיוצאות של צומת |
| `build_communities` | הפעלת זיהוי ואשכול קהילות (ברירת מחדל עיבוד ברקע) |

### תחזוקת זיכרון ‏(2 כלים)

| כלי | תיאור |
|------|------|
| `get_stale_memories` | שאילתת זיכרונות מיושנים בעלי גישה נמוכה |
| `cleanup_stale_memories` | ניקוי זיכרונות מיושנים (ברירת מחדל מצב תצוגה מקדימה dry_run) |

### ניהול משימות

| כלי | תיאור |
|------|------|
| `get_memory_task_status` | שאילתת ההתקדמות והתוצאה של משימת עיבוד זיכרון ברקע |

### מחיקה ושאילתה

| כלי | תיאור |
|------|------|
| `delete_episode` | מחיקת קטע זיכרון |
| `delete_entity_edge` | מחיקת קשת ישות (יחס) |
| `get_entity_edge` | קבלת פרטי קשת ישות |

### ניהול מערכת

| כלי | תיאור |
|------|------|
| `get_status` | קבלת מצב השירות (Neo4j,‏ LLM, מנוע הטמעה) |
| `test_connection` | בדיקת חיבור Neo4j / LLM / מנוע הטמעה |
| `clear_graph` | ניקוי מסד נתוני הגרף (תומך בניקוי לפי group_id) |

## פרמטרים של כלים

### add_memory_simple

| פרמטר | סוג | חובה | ברירת מחדל | תיאור |
|------|------|------|--------|------|
| `name` | string | Y | | שם הזיכרון |
| `episode_body` | string | Y | | תוכן הזיכרון (מעל 800 תווים מחולק אוטומטית) |
| `group_id` | string | | `"default"` | מזהה קבוצה (מומלץ לבודד לפי פרויקט) |
| `source` | string | | `"text"` | סוג מקור: `text` / `json` / `message` |
| `source_description` | string | | `"MCP Server"` | תיאור המקור |
| `use_safe_mode` | bool | | `false` | מצב בטוח (מדלג על חילוץ ישויות, מהיר אך הזיכרון אינו ניתן לחיפוש) |
| `background` | bool | | `false` | עיבוד ברקע (חוזר מיד עם task_id, מתאים לטקסט ארוך) |
| `force` | bool | | `false` | דילוג על בדיקת כפילויות (הוספה כפויה) |
| `excluded_entity_types` | list | | | סוגי ישויות שהוחרגו (מפחית כמות חילוץ שאינה נחוצה) |

> **טיפים לביצועים**:
> - טקסט קצר ‏(<800 תווים): עיבוד ישיר, בדרך כלל מסתיים תוך 30-40 שניות
> - טקסט ארוך ‏(>800 תווים): מחולק אוטומטית למספר קטעים, עיבוד בו‑זמני באמצעות `add_episode_bulk` ‏(מהיר ~33% מעיבוד טורי)
> - שימוש ב‑`background=true` נמנע מחסימת קריאת MCP, ומאפשר מעקב התקדמות באמצעות `get_memory_task_status`
> - `use_safe_mode=true` מסתיים בשנייה אך הזיכרון אינו ניתן למציאה על ידי כלי החיפוש
> - בעת הפעלת הסרת כפילויות, זיכרונות דומים מאוד יקבלו אזהרה ‏(`force=true` מאפשר דילוג)

### add_episode_bulk

| פרמטר | סוג | חובה | ברירת מחדל | תיאור |
|------|------|------|--------|------|
| `episodes` | list | Y | | רשימת זיכרונות, כל פריט מכיל `name` ו‑`content` |
| `group_id` | string | | `"default"` | מזהה קבוצה |
| `source` | string | | `"text"` | סוג מקור |
| `background` | bool | | `true` | עיבוד ברקע (אצווה בדרך כלל גוזלת זמן) |

### add_triplet

| פרמטר | סוג | חובה | ברירת מחדל | תיאור |
|------|------|------|--------|------|
| `source_name` | string | Y | | שם ישות המקור (כגון "Alice") |
| `target_name` | string | Y | | שם ישות היעד (כגון "Google") |
| `relation_name` | string | Y | | שם היחס (כגון "works_at") |
| `fact` | string | Y | | תיאור העובדה (כגון "Alice works at Google") |
| `group_id` | string | | `"default"` | מזהה קבוצה |
| `source_labels` | list | | | תוויות ישות המקור |
| `target_labels` | list | | | תוויות ישות היעד |

### search_memory_nodes

| פרמטר | סוג | חובה | ברירת מחדל | תיאור |
|------|------|------|--------|------|
| `query` | string | Y | | מילת מפתח לחיפוש (שפה טבעית) |
| `max_nodes` | int | | `10` | מספר התוצאות המרבי המוחזר |
| `group_ids` | list | | | סינון קבוצה (חיפוש משולב במספר קבוצות) |
| `entity_types` | list | | | סינון לפי סוג ישות |
| `search_recipe` | string | | | אסטרטגיית חיפוש (ראו חיפוש מתקדם) |
| `created_after` | string | | | גבול תחתון של זמן יצירה (ISO datetime) |
| `created_before` | string | | | גבול עליון של זמן יצירה (ISO datetime) |

### search_memory_facts

| פרמטר | סוג | חובה | ברירת מחדל | תיאור |
|------|------|------|--------|------|
| `query` | string | Y | | מילת מפתח לחיפוש |
| `max_facts` | int | | `10` | מספר התוצאות המרבי המוחזר |
| `group_ids` | list | | | סינון קבוצה |
| `center_node_uuid` | string | | | UUID של צומת מרכזי (חקירת יחסי צומת מסוים) |
| `edge_types` | list | | | סינון לפי סוג יחס (כגון `["works_at"]`) |
| `created_after` | string | | | גבול תחתון של זמן יצירה (ISO datetime) |
| `created_before` | string | | | גבול עליון של זמן יצירה (ISO datetime) |
| `only_valid` | bool | | `false` | מחזיר רק עובדות שלא פג תוקפן |

### advanced_search

| פרמטר | סוג | חובה | ברירת מחדל | תיאור |
|------|------|------|--------|------|
| `query` | string | Y | | מילת מפתח לחיפוש |
| `search_recipe` | string | | `"combined_rrf"` | אסטרטגיית חיפוש (16 אפשרויות) |
| `max_results` | int | | `10` | מספר התוצאות המרבי המוחזר |
| `group_ids` | list | | | סינון קבוצה |
| `center_node_uuid` | string | | | UUID של צומת מרכזי |

**אסטרטגיות חיפוש זמינות ‏(search_recipe):**

| קטגוריה | אסטרטגיה | תיאור |
|------|------|------|
| משולב | `combined_rrf` | מיזוג RRF משולב (ברירת מחדל, מומלץ) |
| משולב | `combined_mmr` | דירוג מחדש בגיוון MMR משולב |
| משולב | `combined_cross_encoder` | דירוג מדויק Cross-Encoder משולב |
| קשת | `edge_rrf` / `edge_mmr` / `edge_cross_encoder` | חיפוש קשתות (3 מיונים) |
| קשת | `edge_node_distance` / `edge_episode_mentions` | חיפוש קשתות (מרחק גרף/מספר אזכורים) |
| צומת | `node_rrf` / `node_mmr` / `node_cross_encoder` | חיפוש צמתים (3 מיונים) |
| צומת | `node_node_distance` / `node_episode_mentions` | חיפוש צמתים (מרחק גרף/מספר אזכורים) |
| קהילה | `community_rrf` / `community_mmr` / `community_cross_encoder` | חיפוש קהילות |

### check_conflicts

| פרמטר | סוג | חובה | ברירת מחדל | תיאור |
|------|------|------|--------|------|
| `source_name` | string | Y | | שם ישות המקור |
| `target_name` | string | Y | | שם ישות היעד |
| `group_id` | string | | `"default"` | מזהה קבוצה |

### get_node_edges

| פרמטר | סוג | חובה | ברירת מחדל | תיאור |
|------|------|------|--------|------|
| `node_uuid` | string | Y | | UUID של הצומת |
| `include_inbound` | bool | | `true` | כולל קשתות נכנסות |
| `include_outbound` | bool | | `true` | כולל קשתות יוצאות |
| `max_edges` | int | | `50` | מספר התוצאות המרבי המוחזר |

### build_communities

| פרמטר | סוג | חובה | ברירת מחדל | תיאור |
|------|------|------|--------|------|
| `group_ids` | list | | | ציון קבוצות (ריק = הכול) |
| `background` | bool | | `true` | עיבוד ברקע |

### get_stale_memories

| פרמטר | סוג | חובה | ברירת מחדל | תיאור |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | מעבר לכמה ימים ללא גישה נחשב מיושן |
| `min_access_count` | int | | `2` | נכלל רק אם מספר הגישות נמוך מערך זה |
| `group_id` | string | | | סינון קבוצה |
| `limit` | int | | `50` | מספר התוצאות המרבי המוחזר |

### cleanup_stale_memories

| פרמטר | סוג | חובה | ברירת מחדל | תיאור |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | סף ימי התיישנות |
| `min_access_count` | int | | `2` | סף מספר גישות מינימלי |
| `group_id` | string | | | סינון קבוצה |
| `dry_run` | bool | | `true` | מצב תצוגה מקדימה (ללא מחיקה בפועל) |
| `limit` | int | | `50` | מספר הפריטים המרבי לעיבוד |

### get_memory_task_status

| פרמטר | סוג | חובה | תיאור |
|------|------|------|------|
| `task_id` | string | Y | מזהה משימת רקע (מוחזר על ידי `add_memory_simple(background=true)`) |

## ממשק ניהול Web

במצב HTTP ניתן לגשת ל‑`http://localhost:8000/` לשימוש.

**תכונות:**
- לוח מחוונים — סטטיסטיקות מספר צמתים, מספר עובדות, מספר קטעי זיכרון
- צמתי ישויות — עיון, סינון, חיפוש וקטורי
- יחסי עובדות — עיון, סינון, חיפוש וקטורי
- קטעי זיכרון — עיון, חיפוש טקסט מלא, מחיקה
- עיון בקהילות — רשימת צמתי קהילה, תקציר, הפעלת בניית קהילות
- טופס שלשות — הוספה ישירה של ידע מובנה "נושא-יחס-מושא"
- ניהול Group — סינון לפי קבוצה, מחיקה באצווה
- הדמיית גרף ידע — הצגה גרפית של יחסי צמתים
- שאלות ותשובות AI — מענה חכם מבוסס גרף ידע
- תחזוקת איכות — מדדי איכות זיכרון וכלי ניקוי
- ייבוא בכמות גדולה — ייבוא מספר קטעי זיכרון בבת אחת (JSON, עד 500 פריטים בבקשה אחת)
- הגדרות בזמן ריצה — צפייה בהגדרות הפעילות כעת, עם אפשרות לשנות חלק מהפרמטרים ללא הפעלה מחדש
- מעבר ערכת נושא — ערכת נושא כהה/בהירה

**REST API:**

| נקודת קצה | שיטה | תיאור |
|------|------|------|
| `/api/stats` | GET | סטטיסטיקות לוח מחוונים |
| `/api/groups` | GET | קבלת כל ה‑group_id |
| `/api/groups/stats` | GET | סטטיסטיקות צמתים/עובדות/קטעים לכל group |
| `/api/nodes` | GET | עיון בצמתי ישויות (עמודים) |
| `/api/facts` | GET | עיון בעובדות (עמודים) |
| `/api/episodes` | GET | עיון בקטעי זיכרון (עמודים) |
| `/api/nodes/{uuid}/relations` | GET | קבלת קשתות נכנסות/יוצאות של צומת |
| `/api/search/nodes` | GET | חיפוש וקטורי של צמתים |
| `/api/search/facts` | GET | חיפוש וקטורי של עובדות |
| `/api/search/episodes` | GET | חיפוש קטעי זיכרון |
| `/api/search/advanced` | GET | חיפוש מתקדם (16 אסטרטגיות) |
| `/api/communities` | GET | עיון בצמתי קהילה (עמודים) |
| `/api/communities/build` | POST | הפעלת בניית קהילות |
| `/api/memory/add` | POST | הוספת זיכרון בודד |
| `/api/memory/add-bulk` | POST | הוספת זיכרונות באצווה |
| `/api/memory/add-triplet` | POST | הוספת שלשה |
| `/api/import/episodes` | POST | ייבוא קטעי זיכרון בכמות גדולה (JSON, עד 500 פריטים בבקשה אחת) |
| `/api/memory/tasks` | GET | רשימת משימות רקע (תומך בסינון לפי מצב) |
| `/api/memory/tasks/{id}` | GET | שאילתת מצב משימה בודדת |
| `/api/timeline` | GET | עיון לפי ציר זמן |
| `/api/graph/subgraph` | GET | קבלת תת‑גרף (להדמיה) |
| `/api/graph/all` | GET | קבלת הגרף המלא (להדמיה) |
| `/api/ask` | GET | שאלות ותשובות AI (מבוסס אחזור מהגרף) |
| `/api/analytics/top-nodes` | GET | צמתים בעלי קישוריות/גישה גבוהה |
| `/api/analytics/quality` | GET | מדדי איכות גרף הידע |
| `/api/analytics/stale` | GET | שאילתת זיכרונות מיושנים |
| `/api/analytics/cleanup` | POST | ניקוי זיכרונות מיושנים |
| `/api/config` | GET | קבלת ההגדרות הפעילות כעת (ללא מפתחות API) |
| `/api/config` | PATCH | עדכון הגדרות ניתנות לשינוי בזמן ריצה (בתוקף לתהליך הנוכחי בלבד, מתאפס בהפעלה מחדש) |
| `/api/nodes/{uuid}` | DELETE | מחיקת צומת |
| `/api/episodes/{uuid}` | DELETE | מחיקת קטע זיכרון |
| `/api/facts/{uuid}` | DELETE | מחיקת עובדה |
| `/api/groups/{group_id}` | DELETE | מחיקת group שלם |

## תצורה

### משתני סביבה ‏(.env)

התצורה משתמשת במנגנון ערימה: קובץ תצורת JSON כבסיס, ומשתני סביבה דורסים ערכים בודדים.

```bash
# === חובה ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password        # חובה לשנות

# === בחירת ספק LLM ===
LLM_PROVIDER=ollama                 # ollama / glm / groq / openrouter / deepseek

# === ספק Embedding (אופציונלי, ברירת מחדל עוקב אחר LLM_PROVIDER) ===
# רק glm משתמש ב‑GLM Embedding, כל השאר משתמשים ב‑Ollama bge-m3
# EMBEDDING_PROVIDER=ollama         # ollama / glm

# === תצורת Ollama (בשימוש כאשר LLM_PROVIDER=ollama) ===
OLLAMA_MODEL=qwen2.5:3b             # מודל ראשי (מומלץ qwen2.5:3b)
OLLAMA_SMALL_MODEL=qwen2.5:3b       # מודל קטן (למשימות פשוטות, ניתן לבחור מודל אחר)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.1

# === תצורת GLM (בשימוש כאשר LLM_PROVIDER=glm) ===
GLM_API_KEY=your_api_key            # מתקבל מ‑https://open.bigmodel.cn
GLM_MODEL=glm-4-flash               # מודל חינמי
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768

# === תצורת GROQ (בשימוש כאשר LLM_PROVIDER=groq) ===
GROQ_API_KEY=your_api_key           # מתקבל מ‑https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile

# === תצורת OpenRouter (בשימוש כאשר LLM_PROVIDER=openrouter) ===
OPENROUTER_API_KEY=your_api_key     # מתקבל מ‑https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free

# === תצורת DeepSeek (בשימוש כאשר LLM_PROVIDER=deepseek) ===
DEEPSEEK_API_KEY=your_api_key       # מתקבל מ‑https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash    # או deepseek-v4-pro

# === מודל הטמעה של Ollama (בשימוש בכל הטמעה שאינה glm) ===
OLLAMA_EMBEDDING_MODEL=bge-m3
OLLAMA_EMBEDDING_DIMENSIONS=768

# === תצוגה ושפה (אופציונלי) ===
GRAPHITI_DISPLAY_TIMEZONE=Asia/Taipei # אזור הזמן לתצוגת חותמות הזמן המוחזרות מ‑API (שם IANA; האחסון נשאר UTC)
SERVER_LANG=zh-TW                     # שפת תגובת כלי MCP (locale מלא ב‑src/i18n.py); REST API לפי Accept-Language

# === ביצועי זיכרון (אופציונלי) ===
GRAPHITI_CHUNK_THRESHOLD=800         # סף מספר תווים להפעלת חלוקה חכמה
GRAPHITI_MAX_CHUNK_SIZE=600          # מספר תווים מרבי בכל קטע
GRAPHITI_MAX_COROUTINES=10            # מספר מרבי של קורוטינות מקבילות
GRAPHITI_DEFAULT_BACKGROUND=false    # האם לעבד ברקע כברירת מחדל
TASK_DB_PATH=data/tasks.db           # נתיב שמירת משימות ברקע ב‑SQLite

# === מעקב חשיבות ושכחה חכמה (אופציונלי) ===
ENABLE_IMPORTANCE_TRACKING=true      # הפעלת מעקב גישה
IMPORTANCE_WEIGHT=0.1                # משקל חשיבות
STALE_DAYS_THRESHOLD=30              # סף ימי התיישנות
STALE_MIN_ACCESS_COUNT=2             # מספר גישות מינימלי

# === לוגים ===
LOG_FILE=logs/graphiti_mcp_server.log
LOG_LEVEL=INFO
```

> **רשימת משתני הסביבה המלאה** ראו ב‑`.env.example`

### קובץ תצורת JSON

מתאים לתצורות הזקוקות לבקרת גרסאות (משתני סביבה עדיין יכולים לדרוס):

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

## הרצה ברקע עם PM2

```bash
npm install -g pm2

pm2 start ecosystem.config.cjs      # הפעלה
pm2 status                           # מצב
pm2 logs graphiti-mcp-http           # לוגים בזמן אמת
pm2 restart graphiti-mcp-http --update-env  # הפעלה מחדש (טעינה מחדש של .env)

pm2 save && pm2 startup              # הגדרת הפעלה אוטומטית בעת אתחול
```

> **טיפ**: לאחר שינוי `.env` חובה להשתמש בדגל `--update-env` בהפעלה מחדש, אחרת משתני הסביבה לא יתעדכנו.

## פריסת Docker

```bash
docker build -t graphiti-mcp .

# הערה: קונטיינר Docker צריך להיות מסוגל להתחבר ל‑Neo4j ול‑Ollama
# שימוש ב‑host network הוא הפשוט ביותר
docker run -p 8000:8000 --env-file .env --network host graphiti-mcp

# או ציון מפורש של כתובות שירותים חיצוניים
docker run -p 8000:8000 \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --env-file .env graphiti-mcp
```

## בדיקות

```bash
# הרצת כל הבדיקות (203, כשנייה אחת)
uv run python -m pytest tests/

# פלט מפורט
uv run python -m pytest tests/ -v

# הרצת בדיקה ספציפית בלבד
uv run python -m pytest tests/test_content_preprocessor.py -v
uv run python -m pytest tests/test_new_features.py -v
uv run python -m pytest tests/test_unit.py -v
```

> **הערה**: 3 בדיקות async ב‑`test_integration_manual.py` דורשות התקנה של `pytest-asyncio`, ובהיעדרו יוצג Failed אך ללא השפעה על בדיקות אחרות. ‏`bench_deepseek_flash_vs_pro.py` הוא סקריפט מדד ביצועים, לא בדיקת יחידה.

## פתרון תקלות

### כשל בחיבור Neo4j

```bash
neo4j status                              # בדיקת מצב השירות
cypher-shell -u neo4j -p your_password    # ודאו שהסיסמה נכונה
curl http://localhost:7474                 # ודאו את פורט ה‑HTTP
```

סיבות נפוצות:
- Neo4j לא הופעל
- סיסמה שגויה (`NEO4J_PASSWORD` ב‑`.env`)
- הפורט תפוס או חסום על ידי חומת אש

### כשל בחיבור LLM

**מצב Ollama:**
```bash
ollama serve                # הפעלת שירות Ollama
ollama list                 # בדיקת מודלים מותקנים
ollama pull qwen2.5:3b      # התקנת מודל חסר
```

סיבות נפוצות: Ollama לא הופעל, המודל לא הותקן, זיכרון GPU לא מספיק

**מצב GLM:**
- ודאו ש‑`GLM_API_KEY` נכון
- ודאו ש‑`GLM_EMBEDDING_DIMENSIONS=768` ‏(חייב להתאים לאינדקס הווקטורים של Neo4j)
- נקודת קצה של GLM API:‏ `https://open.bigmodel.cn/api/paas/v4/`

**מצב GROQ:**
- ודאו ש‑`GROQ_API_KEY` נכון
- בעת Rate Limit תכוף שקלו לעבור למצב GLM
- GROQ אינו מספק Embedding, יש לוודא שמנוע ההטמעה של Ollama זמין

**מצב OpenRouter:**
- ודאו ש‑`OPENROUTER_API_KEY` נכון, ו‑`OPENROUTER_MODEL` הוא מזהה מודל תקף (ראו https://openrouter.ai/models)
- אינו מספק Embedding, יש לוודא שמנוע ההטמעה של Ollama זמין

**מצב DeepSeek:**
- ודאו ש‑`DEEPSEEK_API_KEY` נכון
- אם מופיע `Prompt must contain the word 'json'`: זוהי דרישה מחמירה של מצב `json_object` של DeepSeek, ובלקוח כבר מובנה מנגנון הגנה כברירת מחדל; אם עדיין מופיע, ודאו שאתם משתמשים בגרסה העדכנית של `src/deepseek_client.py` והפעילו את השירות מחדש
- אינו מספק Embedding, יש לוודא שמנוע ההטמעה של Ollama זמין

### שגיאת חיבור MCP

אם מופיע `Invalid request parameters` או `Received request before initialization was complete`:

1. ודאו שאתם משתמשים במצב תעבורה HTTP ‏(**אל תשתמשו ב‑SSE**)
2. ודאו שתצורת הלקוח היא `"type": "http"`,‏ `"url": "http://localhost:8000/mcp"`
3. הפעילו מחדש את השירות: `pm2 restart graphiti-mcp-http --update-env`
4. הריצו `/mcp` ב‑Claude Code כדי להתחבר מחדש

### הוספת זיכרון איטית

- **Ollama**: בדקו את גודל המודל ‏(`qwen2.5:3b` מהיר פי 5-10 מ‑`7b`), ודאו ש‑GPU בשימוש ‏(`ollama ps`)
- **GLM**: כל add_episode דורש 10-20+ סבבי רשת LLM, ‏~22 שניות לטקסט קצר הוא ערך תקין
- **GROQ**: ‏Rate Limit יגרום לניסיונות חוזרים רבים, בשימוש תכוף מומלץ לעבור ל‑GLM או Ollama
- השתמשו ב‑`background=true` כדי להימנע מחסימה
- הורידו את `GRAPHITI_CHUNK_THRESHOLD` כדי לחלק טקסט ארוך מוקדם יותר

### בעיות PM2

```bash
pm2 status                                        # בדיקת מצב
pm2 logs graphiti-mcp-http --err --lines 50        # לוג שגיאות
lsof -i :8000                                     # בדיקת תפיסת פורט
pm2 delete graphiti-mcp-http && pm2 start ecosystem.config.cjs  # הפעלה מחדש מלאה
```

## כלי אבחון לפיתוח

```bash
uv run python tools/status_report.py           # דוח מצב משולב (Neo4j + Ollama + תצורה)
uv run python tools/validate_config.py         # אימות שלמות .env והתצורה
uv run python tools/performance_diagnose.py    # אבחון ביצועי LLM
uv run python tools/inspect_schema.py          # בדיקת אינדקסים ואילוצים של Neo4j
uv run python tools/migrate_embeddings.py      # העברת מודל Embedding (יצירה מחדש של וקטורים לאחר החלפת מודל)
```

### העברת מודל Embedding

לאחר החלפת מודל embedding (כגון `nomic-embed-text` → `bge-m3`), ניתן להשתמש בכלי ההעברה כדי ליצור מחדש את כל הווקטורים הקיימים, להבטחת איכות חיפוש עקבית:

```bash
# תצוגה מקדימה של הכמות הזקוקה להעברה
uv run python tools/migrate_embeddings.py --dry-run

# העברה מלאה (תומך בהמשך מנקודת עצירה)
uv run python tools/migrate_embeddings.py

# העברת group מסוים בלבד
uv run python tools/migrate_embeddings.py --group-id myproject

# המשך מנקודת עצירה (הרצה מחדש לאחר הפסקה)
uv run python tools/migrate_embeddings.py --resume
```

> **תאימות**: `bge-m3` הוא 1024 ממדים במקור, והמערכת חותכת אותו אוטומטית ל‑768 ממדים לתאימות עם אינדקס הווקטורים הקיים של Neo4j. הנתונים לפני ואחרי ההעברה יכולים להתקיים יחד, אך מומלץ לבצע העברה מלאה לקבלת איכות החיפוש הטובה ביותר.

## תיעוד

- [הוראות שימוש בכלים](../使用工具的指令.md) — מדריך שימוש בכלי MCP ושיטות עבודה מומלצות
- [Graphiti Memory Rules](../graphiti-memory-rules.md) — הסבר על כללי הזיכרון

## רישיון

MIT License
