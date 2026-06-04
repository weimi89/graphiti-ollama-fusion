# Graphiti MCP Server

نالج گراف میموری سروس — متعدد LLM فراہم کنندگان (Ollama / GLM / GROQ / OpenRouter / DeepSeek) اور Neo4j گراف ڈیٹابیس کو مربوط کرنے والا MCP سرور۔

[getzep/graphiti](https://github.com/getzep/graphiti) کی بنیاد پر توسیع شدہ، مقامی Ollama اور کلاؤڈ LLM کے درمیان لچکدار تبدیلی کی حمایت کرتا ہے، اور Embedding فراہم کنندہ کو آزادانہ طور پر متعین کیا جا سکتا ہے (LLM سے علیحدہ)۔

## نمایاں خصوصیات

- **ذہین میموری مینجمنٹ** — پیچیدہ میموری تعلقات کو محفوظ اور بازیافت کرنے کے لیے نالج گراف کا استعمال
- **معنوی تلاش (Semantic Search)** — ویکٹر ایمبیڈنگ پر مبنی ہائبرڈ تلاش (ویکٹر + کلیدی الفاظ + گراف ٹریورسل)
- **16 تلاش کی حکمت عملیاں** — جدید تلاش RRF، MMR، Cross-Encoder سمیت متعدد دوبارہ ترتیب دینے کے طریقوں کی حمایت کرتی ہے
- **متعدد LLM فراہم کنندگان** — Ollama (مقامی)، GLM (Zhipu AI مفت)، GROQ (تیز رفتار انفرنس)، OpenRouter (متعدد ماڈلز کا مجموعہ)، DeepSeek کی حمایت، ماحولیاتی متغیرات کے ذریعے ایک کلک سے تبدیلی
- **Embedding اور LLM کی علیحدگی** — `EMBEDDING_PROVIDER` کے ذریعے ایمبیڈر کو آزادانہ طور پر متعین کیا جا سکتا ہے، کلاؤڈ LLM خود بخود مقامی `bge-m3` پر واپس آ جاتا ہے
- **دوہرا ماڈل تقسیم** — Ollama موڈ میں پیچیدہ کاموں کے لیے بنیادی ماڈل، سادہ کاموں کے لیے کارکردگی بڑھانے کے لیے خود بخود چھوٹے ماڈل پر تبدیلی
- **ذہین مواد کی تقسیم** — طویل متن خود بخود حصوں میں تقسیم ہو کر پروسیس ہوتا ہے، LLM کا بوجھ کم کرتا ہے (قابلِ ترتیب حد)
- **پس منظر میں میموری پروسیسنگ** — میموری شامل کرنا پس منظر میں چل سکتا ہے، MCP کال فوری طور پر واپس آ جاتی ہے
- **میموری ڈی ڈپلیکیشن** — انتہائی مشابہ موجودہ میموریز کا خود بخود پتہ لگاتا ہے، تکراری ذخیرے سے بچتا ہے
- **تنازع کی شناخت** — دو اداروں کے درمیان متضاد حقائق کا پتہ لگاتا ہے، غیر مؤثر اور مؤثر معلومات کی شناخت کرتا ہے
- **کمیونٹی کی شناخت** — Label Propagation الگورتھم کی بنیاد پر متعلقہ اداروں کو خود بخود گروپ بندی کرتا ہے
- **اہمیت کی ٹریکنگ** — ادارے تک رسائی کی تعدد کو خود بخود ریکارڈ کرتا ہے، تلاش کے نتائج اہمیت کے مطابق ترتیب دیتا ہے
- **ذہین فراموشی** — پرانی، کم رسائی والی میموریز کی شناخت اور صفائی کرتا ہے، گراف کو مختصر رکھتا ہے
- **بلک امپورٹ** — ایک ساتھ متعدد میموریز جمع کرواتا ہے، بڑی مقدار میں ڈیٹا منتقلی کے لیے موزوں
- **ساختہ ٹرپلٹ** — براہ راست "موضوع-تعلق-مفعول" شامل کرتا ہے، LLM نکالنے کو نظر انداز کرتے ہوئے فوری طور پر مکمل ہوتا ہے
- **Web مینجمنٹ انٹرفیس** — بلٹ ان ڈیش بورڈ، براؤزنگ، تلاش، نالج گراف ویژولائزیشن، AI سوال و جواب، کمیونٹی براؤزنگ
- **کثیر لسانی (i18n)** — جوابی پیغامات 30+ لوکیلز کی حمایت کرتے ہیں (بشمول zh-TW / en / zh-CN / ja / pt-BR / ko / es / de / fr وغیرہ)؛ MCP ٹولز `SERVER_LANG` کے مطابق، REST API HTTP `Accept-Language` کے مطابق خود بخود مذاکرات کرتا ہے
- **تاریک/روشن تھیم** — Web انٹرفیس تھیم کی تبدیلی کی حمایت کرتا ہے
- **محفوظ موڈ** — ادارے نکالنے کو نظر انداز کرتے ہوئے تیز رفتار میموری شامل کرنے کا اختیاری انتخاب
- **Docker سپورٹ** — بلٹ ان Dockerfile، کنٹینرائزڈ تعیناتی کی حمایت کرتا ہے
- **ہم وقتی تحفظ (Concurrency Safety)** — asyncio.Lock ابتدائیہ کو محفوظ کرتا ہے، ریس کنڈیشنز سے بچاتا ہے
- **پرتوں والی صحت کی جانچ** — `/health` (liveness) + `/health/ready` (readiness)

## نظام کی ضروریات

| آئٹم | ضرورت |
|------|------|
| Python | 3.10+ (3.11+ تجویز کردہ) |
| Neo4j | 4.0+ (`bolt://localhost:7687`) |
| LLM فراہم کنندہ | Ollama / GLM / GROQ / OpenRouter / DeepSeek (پانچ میں سے ایک) |
| Node.js | 18+ (صرف PM2 پس منظر میں چلانے کے لیے، اختیاری) |
| ڈسک اسپیس | ~3GB (Ollama ماڈل + Neo4j ڈیٹا) |

### LLM فراہم کنندہ کا انتخاب

`LLM_PROVIDER` ماحولیاتی متغیر کے ذریعے تبدیل کریں (`ollama` / `glm` / `groq` / `openrouter` / `deepseek`):

| فراہم کنندہ | خصوصیات | LLM ماڈل | Embedding | موزوں منظر |
|--------|------|----------|-----------|----------|
| **Ollama** (ڈیفالٹ) | مکمل طور پر مقامی، ڈیٹا مشین سے باہر نہیں جاتا | `qwen2.5:3b` | `bge-m3` (چینی + RAG عمدہ) | GPU موجود، رازداری اہم |
| **GLM** | مفت کلاؤڈ، مستحکم بلا حد | `glm-4-flash` (مفت) | `embedding-3` | GPU نہیں، تلاش پر مبنی منظر |
| **GROQ** | انتہائی تیز رفتار انفرنس | `llama-3.3-70b-versatile` | Ollama `bge-m3` پر واپسی | کبھی کبھار تحریر، معیار کی طلب |
| **OpenRouter** | متعدد ماڈلز کا مجموعہ، مفت کوٹہ سمیت | `stepfun/step-3.5-flash:free` وغیرہ | Ollama `bge-m3` پر واپسی | مخصوص کلاؤڈ ماڈل استعمال کرنا چاہیں |
| **DeepSeek** | DeepSeek کلاؤڈ، اعلیٰ قیمت کارکردگی تناسب | `deepseek-v4-flash` / `deepseek-v4-pro` | Ollama `bge-m3` پر واپسی | چینی فہم، کم لاگت کلاؤڈ |

> **Embedding اور LLM کی علیحدگی**: ایمبیڈر `EMBEDDING_PROVIDER` (`ollama` / `glm`) کے ذریعے آزادانہ طور پر متعین ہوتا ہے، متعین نہ ہونے پر `LLM_PROVIDER` کی پیروی کرتا ہے۔ درحقیقت صرف `glm` GLM `embedding-3` استعمال کرتا ہے، باقی (بشمول GROQ / OpenRouter / DeepSeek جیسے کلاؤڈ LLM جو Embedding فراہم نہیں کرتے) سب خود بخود Ollama `bge-m3` استعمال کرتے ہیں۔ **لہٰذا کوئی بھی کلاؤڈ LLM استعمال کرتے وقت، ایمبیڈنگ سروس فراہم کرنے کے لیے اب بھی مقامی Ollama کی ضرورت ہے (سوائے اس کے کہ embedding کو بھی glm پر سیٹ کیا گیا ہو)۔**

#### Ollama موڈ (مقامی)

```bash
# LLM بنیادی ماڈل (qwen2.5:3b تجویز کردہ، رفتار اور استحکام کا بہترین توازن)
ollama pull qwen2.5:3b

# ایمبیڈنگ ماڈل (لازمی، ویکٹر تلاش کے لیے)
ollama pull bge-m3
```

> **ماڈل انتخاب کے نکات**:
> - `qwen2.5:3b` — تجویز کردہ، ~2s/call، ~100 t/s، graphiti-core ساختہ آؤٹ پٹ 100% مستحکم
> - `qwen2.5:7b` — بہتر نتائج لیکن 5-10 گنا سست، معیار کی طلب والے منظر کے لیے موزوں
> - `qwen2.5:1.5b` — سب سے تیز لیکن **غیر مستحکم** (ساختہ JSON کامیابی کی شرح صرف 33%)، استعمال کرنے کی سفارش نہیں

#### GLM موڈ (Zhipu AI کلاؤڈ)

```bash
# .env ترتیبات
LLM_PROVIDER=glm
GLM_API_KEY=your_api_key          # https://open.bigmodel.cn سے حاصل کریں
GLM_MODEL=glm-4-flash             # مفت ماڈل
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768      # Neo4j ویکٹر انڈیکس کی جہت کے مطابق ہونا چاہیے
```

> **GLM کارکردگی کا حوالہ**: تحریر ~22s (مختصر متن)، تلاش ~0.34s، صفر Rate Limit خرابیاں، مقامی Ollama سے 2-5 گنا سست لیکن مکمل طور پر مفت۔

#### GROQ موڈ (تیز رفتار انفرنس)

```bash
# .env ترتیبات
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key         # https://console.groq.com سے حاصل کریں
GROQ_MODEL=llama-3.3-70b-versatile
```

> **نوٹ**: GROQ Embedding سروس فراہم نہیں کرتا، اسے Ollama ایمبیڈر کے ساتھ (خود بخود واپسی) استعمال کرنا یا `EMBEDDING_PROVIDER` کو glm پر سیٹ کرنا ضروری ہے۔ GROQ میں سخت Rate Limit ہے، زیادہ استعمال بہت سی دوبارہ کوششوں کو متحرک کرتا ہے۔

#### OpenRouter موڈ (متعدد ماڈلز کا مجموعہ)

```bash
# .env ترتیبات
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_api_key       # https://openrouter.ai/keys سے حاصل کریں
OPENROUTER_MODEL=stepfun/step-3.5-flash:free   # کسی بھی OpenRouter ماڈل میں تبدیل کیا جا سکتا ہے
```

> **نوٹ**: OpenRouter Embedding فراہم نہیں کرتا، خود بخود Ollama `bge-m3` پر واپس آ جاتا ہے۔ ماڈلز کی فہرست https://openrouter.ai/models پر دیکھیں (متعدد `:free` مفت ماڈلز سمیت)۔

#### DeepSeek موڈ (DeepSeek)

```bash
# .env ترتیبات
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key         # https://platform.deepseek.com سے حاصل کریں
DEEPSEEK_MODEL=deepseek-v4-flash      # تجویز کردہ؛ یا deepseek-v4-pro (بہتر نتائج)
```

> **نوٹ**: DeepSeek Embedding فراہم نہیں کرتا، خود بخود Ollama `bge-m3` پر واپس آ جاتا ہے۔ `deepseek-chat` / `deepseek-reasoner` 2026-07-24 کو بند ہو جائیں گے، `deepseek-v4-flash` / `deepseek-v4-pro` پر تبدیل کرنے کی سفارش کی جاتی ہے۔ DeepSeek سختی سے تقاضا کرتا ہے کہ `json_object` موڈ کے prompt میں "json" لفظ شامل ہو، کلائنٹ میں بلٹ ان حفاظتی تحفظ موجود ہے، اضافی ترتیب کی ضرورت نہیں۔

## فوری آغاز

### 1. ابتدائی تیاری

تصدیق کریں کہ Neo4j مقامی مشین پر چل رہا ہے، اور منتخب کردہ LLM فراہم کنندہ کے مطابق متعلقہ سروس تیار کریں:

```bash
# تصدیق کریں کہ Neo4j چل رہا ہے (لازمی)
neo4j status
# یا Docker استعمال کریں: docker run -d -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/your_password neo4j:latest

# Ollama موڈ: تصدیق کریں کہ Ollama چل رہا ہے
ollama list
# اگر شروع نہیں ہوا: ollama serve

# GLM / GROQ موڈ: صرف ایک درست API Key کی ضرورت ہے، مقامی سروس کی ضرورت نہیں
```

### 2. انحصارات کی تنصیب

```bash
git clone <repo-url>
cd graphiti
uv sync
```

> **نوٹ**: یہ پروجیکٹ انحصارات کے انتظام کے لیے [uv](https://github.com/astral-sh/uv) استعمال کرتا ہے۔ اگر تنصیب نہیں ہے: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 3. ماحول کی ترتیب

```bash
cp .env.example .env
```

`.env` میں ترمیم کریں، **کم از کم** درج ذیل آئٹمز میں ترمیم کرنے کی ضرورت ہے:

```bash
NEO4J_PASSWORD=your_actual_password  # لازمی: Neo4j پاس ورڈ
LLM_PROVIDER=ollama                  # ollama / glm / groq / openrouter / deepseek
OLLAMA_MODEL=qwen2.5:3b              # Ollama موڈ: مقامی LLM ماڈل
# GLM_API_KEY=your_key               # GLM موڈ: Zhipu AI API Key
# GROQ_API_KEY=your_key              # GROQ موڈ: GROQ API Key
# OPENROUTER_API_KEY=your_key        # OpenRouter موڈ: API Key
# DEEPSEEK_API_KEY=your_key          # DeepSeek موڈ: API Key
```

### 4. سروس شروع کریں

```bash
# HTTP موڈ (تجویز کردہ، Web مینجمنٹ انٹرفیس سمیت)
uv run python graphiti_mcp_server.py --transport http --port 8000

# یا PM2 پس منظر میں چلانے کا استعمال کریں (طویل مدتی چلانے کے لیے تجویز کردہ)
pm2 start ecosystem.config.cjs
```

### 5. سروس کی تصدیق

شروع کرنے کے بعد درج ذیل اینڈ پوائنٹس تک رسائی حاصل کی جا سکتی ہے:

| اینڈ پوائنٹ | وضاحت |
|------|------|
| http://localhost:8000/ | Web مینجمنٹ انٹرفیس |
| http://localhost:8000/mcp | MCP اینڈ پوائنٹ (MCP کلائنٹ کنکشن کے لیے) |
| http://localhost:8000/health | صحت کی جانچ (liveness) |
| http://localhost:8000/health/ready | گہری جانچ (Neo4j کنکشن سمیت) |
| http://localhost:8000/api/stats | REST API شماریات |

## پروجیکٹ ساخت

```
graphiti/
├── graphiti_mcp_server.py        # مرکزی داخلہ — MCP ٹول تعریف (19 ٹولز)
├── src/
│   ├── config.py                 # ترتیب مینجمنٹ (GraphitiConfig، JSON/.env پرتوں کی حمایت)
│   ├── web_api.py                # Web مینجمنٹ انٹرفیس REST API (20+ اینڈ پوائنٹس)
│   ├── ollama_graphiti_client.py  # Ollama LLM کلائنٹ (دوہرا ماڈل تقسیم)
│   ├── glm_client.py             # GLM (Zhipu AI) LLM کلائنٹ (OpenAI ہم آہنگ API)
│   ├── openrouter_client.py      # OpenRouter LLM کلائنٹ (متعدد ماڈلز کا مجموعہ)
│   ├── deepseek_client.py        # DeepSeek LLM کلائنٹ (json_object + حفاظتی json تحفظ)
│   ├── ollama_embedder.py        # Ollama ایمبیڈنگ ماڈل اڈاپٹر
│   ├── content_preprocessor.py   # ذہین مواد کی تقسیم (طویل متن خود بخود حصوں میں)
│   ├── deduplication.py          # میموری ڈی ڈپلیکیشن (cosine مماثلت موازنہ)
│   ├── importance.py             # اہمیت کی ٹریکنگ اور ذہین فراموشی
│   ├── safe_memory_add.py        # محفوظ میموری شامل کرنا (ادارے نکالنے کو نظر انداز)
│   ├── timezone_utils.py         # ٹائم زون تبدیلی (UTC→مقامی ٹائم زون ڈسپلے)
│   ├── i18n.py                   # بیک اینڈ کثیر لسانی (REST Accept-Language کے مطابق، MCP SERVER_LANG کے مطابق)
│   ├── exceptions.py             # ساختہ استثنا ہینڈلنگ (12 استثنا اقسام)
│   └── logging_setup.py          # لاگنگ سسٹم (وقتی روٹیشن + کارکردگی مانیٹرنگ)
├── web/                          # Web مینجمنٹ انٹرفیس فرنٹ اینڈ (SPA، بغیر build)
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js                # REST API ریپر
│       ├── components.js         # UI کمپوننٹ رینڈرنگ (کمیونٹی صفحہ سمیت)
│       └── app.js                # SPA روٹنگ، اسٹیٹ مینجمنٹ
├── tests/                        # ٹیسٹ سویٹ (183 ٹیسٹس)
│   ├── test_content_preprocessor.py  # تقسیم منطق ٹیسٹ (17)
│   ├── test_new_features.py      # نئی خصوصیات کا ٹیسٹ (32)
│   ├── test_i18n.py             # کثیر لسانی ٹیسٹ (37)
│   ├── test_unit.py              # یونٹ ٹیسٹ
│   ├── test_web_api.py           # Web API ٹیسٹ
│   ├── test_web_ui_features.py   # Web UI فیچر ٹیسٹ
│   ├── test_integration_manual.py # دستی انضمام ٹیسٹ
│   └── bench_deepseek_flash_vs_pro.py # DeepSeek flash/pro کارکردگی بینچ مارک اسکرپٹ
├── tools/                        # ترقیاتی تشخیصی ٹولز
│   ├── status_report.py          # مجموعی حالت رپورٹ
│   ├── validate_config.py        # ترتیب کی تصدیق
│   ├── performance_diagnose.py   # کارکردگی تشخیص
│   ├── inspect_schema.py         # Neo4j ساخت جانچ
│   └── batch_reprocess.py        # بیچ دوبارہ پروسیسنگ
├── docs/                         # دستاویزات
├── logs/                         # لاگز (وقتی روٹیشن، ڈیفالٹ 30 دن محفوظ)
├── Dockerfile                    # Docker کنٹینرائزڈ تعیناتی
└── ecosystem.config.cjs          # PM2 ترتیب
```

## MCP کلائنٹ ترتیب

### HTTP موڈ (تجویز کردہ)

Claude Code، Cline وغیرہ جیسے HTTP کی حمایت کرنے والے MCP کلائنٹس کے لیے موزوں:

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

### STDIO موڈ

Claude Desktop وغیرہ جیسے کلائنٹس کے لیے موزوں جنہیں براہ راست پروسیس شروع کرنے کی ضرورت ہوتی ہے:

**ترتیب فائل کا مقام:**
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

> **نوٹ**: SSE موڈ (`--transport sse`) کی سفارش نہیں کی جاتی۔ MCP 1.x میں session ابتدائیہ کی ہم آہنگی کے مسائل ہیں، براہ کرم HTTP موڈ استعمال کریں۔

## MCP ٹولز (19)

### میموری مینجمنٹ (7)

| ٹول | وضاحت |
|------|------|
| `add_memory_simple` | نالج گراف میں میموری شامل کریں (پس منظر پروسیسنگ، ذہین تقسیم، ڈی ڈپلیکیشن جانچ کی حمایت) |
| `add_episode_bulk` | متعدد میموریز کا بلک اضافہ (ڈیفالٹ پس منظر پروسیسنگ) |
| `add_triplet` | ساختہ ٹرپلٹ اضافہ (LLM کو نظر انداز، فوری مکمل) |
| `search_memory_nodes` | میموری نوڈز کی تلاش (16 تلاش حکمت عملیوں، وقتی فلٹرنگ کی حمایت) |
| `search_memory_facts` | میموری حقائق کی تلاش (تعلق کی قسم فلٹرنگ، وقتی حد، درستگی فلٹرنگ کی حمایت) |
| `advanced_search` | جدید تلاش (16 حکمت عملیاں، نوڈز+کنارے+کمیونٹیز+ٹکڑے واپس) |
| `get_episodes` | حالیہ میموری ٹکڑے حاصل کریں |

### نالج تجزیہ (3)

| ٹول | وضاحت |
|------|------|
| `check_conflicts` | دو اداروں کے درمیان حقائق کے تنازعات کا پتہ لگائیں (مؤثر vs غیر مؤثر) |
| `get_node_edges` | نوڈ کے داخلی اور خارجی کنارے تعلقات کی کھوج کریں |
| `build_communities` | کمیونٹی شناخت اور گروپ بندی کو متحرک کریں (ڈیفالٹ پس منظر پروسیسنگ) |

### میموری دیکھ بھال (2)

| ٹول | وضاحت |
|------|------|
| `get_stale_memories` | پرانی، کم رسائی والی میموریز کی تلاش کریں |
| `cleanup_stale_memories` | پرانی میموریز کی صفائی کریں (ڈیفالٹ dry_run پیش نظارہ موڈ) |

### ٹاسک مینجمنٹ

| ٹول | وضاحت |
|------|------|
| `get_memory_task_status` | پس منظر میموری پروسیسنگ ٹاسک کی پیش رفت اور نتائج کی تلاش کریں |

### حذف اور استفسار

| ٹول | وضاحت |
|------|------|
| `delete_episode` | میموری ٹکڑا حذف کریں |
| `delete_entity_edge` | ادارہ کنارہ (تعلق) حذف کریں |
| `get_entity_edge` | ادارہ کنارے کی تفصیلی معلومات حاصل کریں |

### سسٹم مینجمنٹ

| ٹول | وضاحت |
|------|------|
| `get_status` | سروس کی حالت حاصل کریں (Neo4j، LLM، ایمبیڈر) |
| `test_connection` | Neo4j / LLM / ایمبیڈر کنکشن ٹیسٹ کریں |
| `clear_graph` | گراف ڈیٹابیس صاف کریں (group_id کے مطابق صفائی کی حمایت) |

## ٹول پیرامیٹرز

### add_memory_simple

| پیرامیٹر | قسم | لازمی | ڈیفالٹ | وضاحت |
|------|------|------|--------|------|
| `name` | string | Y | | میموری کا نام |
| `episode_body` | string | Y | | میموری کا مواد (800 حروف سے زیادہ خود بخود تقسیم) |
| `group_id` | string | | `"default"` | گروپ ID (پروجیکٹ کے مطابق علیحدہ کرنے کی سفارش) |
| `source` | string | | `"text"` | ماخذ کی قسم: `text` / `json` / `message` |
| `source_description` | string | | `"MCP Server"` | ماخذ کی وضاحت |
| `use_safe_mode` | bool | | `false` | محفوظ موڈ (ادارے نکالنے کو نظر انداز، تیز لیکن میموری تلاش نہیں ہو سکتی) |
| `background` | bool | | `false` | پس منظر پروسیسنگ (فوری task_id واپس، طویل متن کے لیے موزوں) |
| `force` | bool | | `false` | ڈی ڈپلیکیشن جانچ کو نظر انداز کریں (زبردستی اضافہ) |
| `excluded_entity_types` | list | | | خارج کردہ ادارہ اقسام (غیر ضروری نکالنے کی مقدار کم کریں) |

> **کارکردگی نکات**:
> - مختصر متن (<800 حروف): براہ راست پروسیس، عام طور پر 30-40 سیکنڈ میں مکمل
> - طویل متن (>800 حروف): خود بخود متعدد حصوں میں تقسیم، `add_episode_bulk` کا استعمال کرتے ہوئے ہم وقتی پروسیسنگ (سلسلہ وار سے ~33% تیز)
> - `background=true` استعمال کرنے سے MCP کال بلاک ہونے سے بچا جا سکتا ہے، `get_memory_task_status` کے ذریعے پیش رفت ٹریک کریں
> - `use_safe_mode=true` فوری مکمل ہوتا ہے لیکن میموری search ٹولز سے نہیں مل سکتی
> - ڈی ڈپلیکیشن فعال ہونے پر، انتہائی مشابہ میموریز کو وارننگ دی جائے گی (`force=true` نظر انداز کر سکتا ہے)

### add_episode_bulk

| پیرامیٹر | قسم | لازمی | ڈیفالٹ | وضاحت |
|------|------|------|--------|------|
| `episodes` | list | Y | | میموریز کی فہرست، ہر آئٹم میں `name` اور `content` |
| `group_id` | string | | `"default"` | گروپ ID |
| `source` | string | | `"text"` | ماخذ کی قسم |
| `background` | bool | | `true` | پس منظر پروسیسنگ (بلک عام طور پر وقت طلب) |

### add_triplet

| پیرامیٹر | قسم | لازمی | ڈیفالٹ | وضاحت |
|------|------|------|--------|------|
| `source_name` | string | Y | | ماخذ ادارے کا نام (جیسے "Alice") |
| `target_name` | string | Y | | ہدف ادارے کا نام (جیسے "Google") |
| `relation_name` | string | Y | | تعلق کا نام (جیسے "works_at") |
| `fact` | string | Y | | حقیقت کی وضاحت (جیسے "Alice works at Google") |
| `group_id` | string | | `"default"` | گروپ ID |
| `source_labels` | list | | | ماخذ ادارہ لیبلز |
| `target_labels` | list | | | ہدف ادارہ لیبلز |

### search_memory_nodes

| پیرامیٹر | قسم | لازمی | ڈیفالٹ | وضاحت |
|------|------|------|--------|------|
| `query` | string | Y | | تلاش کے کلیدی الفاظ (قدرتی زبان) |
| `max_nodes` | int | | `10` | زیادہ سے زیادہ واپسی کی تعداد |
| `group_ids` | list | | | گروپ فلٹرنگ (متعدد گروپ مشترکہ تلاش) |
| `entity_types` | list | | | ادارہ قسم فلٹرنگ |
| `search_recipe` | string | | | تلاش حکمت عملی (جدید تلاش دیکھیں) |
| `created_after` | string | | | تخلیق وقت کی نچلی حد (ISO datetime) |
| `created_before` | string | | | تخلیق وقت کی اوپری حد (ISO datetime) |

### search_memory_facts

| پیرامیٹر | قسم | لازمی | ڈیفالٹ | وضاحت |
|------|------|------|--------|------|
| `query` | string | Y | | تلاش کے کلیدی الفاظ |
| `max_facts` | int | | `10` | زیادہ سے زیادہ واپسی کی تعداد |
| `group_ids` | list | | | گروپ فلٹرنگ |
| `center_node_uuid` | string | | | مرکزی نوڈ UUID (مخصوص نوڈ کے تعلقات کی کھوج) |
| `edge_types` | list | | | تعلق قسم فلٹرنگ (جیسے `["works_at"]`) |
| `created_after` | string | | | تخلیق وقت کی نچلی حد (ISO datetime) |
| `created_before` | string | | | تخلیق وقت کی اوپری حد (ISO datetime) |
| `only_valid` | bool | | `false` | صرف غیر منسوخ حقائق واپس کریں |

### advanced_search

| پیرامیٹر | قسم | لازمی | ڈیفالٹ | وضاحت |
|------|------|------|--------|------|
| `query` | string | Y | | تلاش کے کلیدی الفاظ |
| `search_recipe` | string | | `"combined_rrf"` | تلاش حکمت عملی (16 اختیاری) |
| `max_results` | int | | `10` | زیادہ سے زیادہ واپسی کی تعداد |
| `group_ids` | list | | | گروپ فلٹرنگ |
| `center_node_uuid` | string | | | مرکزی نوڈ UUID |

**دستیاب تلاش حکمت عملیاں (search_recipe):**

| زمرہ | حکمت عملی | وضاحت |
|------|------|------|
| جامع | `combined_rrf` | جامع RRF فیوژن (ڈیفالٹ، تجویز کردہ) |
| جامع | `combined_mmr` | جامع MMR تنوع دوبارہ ترتیب |
| جامع | `combined_cross_encoder` | جامع Cross-Encoder درست ترتیب |
| کنارہ | `edge_rrf` / `edge_mmr` / `edge_cross_encoder` | کنارہ تلاش (3 ترتیبات) |
| کنارہ | `edge_node_distance` / `edge_episode_mentions` | کنارہ تلاش (گراف فاصلہ/حوالہ تعداد) |
| نوڈ | `node_rrf` / `node_mmr` / `node_cross_encoder` | نوڈ تلاش (3 ترتیبات) |
| نوڈ | `node_node_distance` / `node_episode_mentions` | نوڈ تلاش (گراف فاصلہ/حوالہ تعداد) |
| کمیونٹی | `community_rrf` / `community_mmr` / `community_cross_encoder` | کمیونٹی تلاش |

### check_conflicts

| پیرامیٹر | قسم | لازمی | ڈیفالٹ | وضاحت |
|------|------|------|--------|------|
| `source_name` | string | Y | | ماخذ ادارے کا نام |
| `target_name` | string | Y | | ہدف ادارے کا نام |
| `group_id` | string | | `"default"` | گروپ ID |

### get_node_edges

| پیرامیٹر | قسم | لازمی | ڈیفالٹ | وضاحت |
|------|------|------|--------|------|
| `node_uuid` | string | Y | | نوڈ UUID |
| `include_inbound` | bool | | `true` | داخلی کنارے شامل کریں |
| `include_outbound` | bool | | `true` | خارجی کنارے شامل کریں |
| `max_edges` | int | | `50` | زیادہ سے زیادہ واپسی کی تعداد |

### build_communities

| پیرامیٹر | قسم | لازمی | ڈیفالٹ | وضاحت |
|------|------|------|--------|------|
| `group_ids` | list | | | مخصوص گروپ (خالی چھوڑیں تو سب) |
| `background` | bool | | `true` | پس منظر پروسیسنگ |

### get_stale_memories

| پیرامیٹر | قسم | لازمی | ڈیفالٹ | وضاحت |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | کتنے دن سے رسائی نہ ہونے پر پرانی تصور کی جائے |
| `min_access_count` | int | | `2` | اس قدر سے کم رسائی تعداد ہی شامل ہو |
| `group_id` | string | | | گروپ فلٹرنگ |
| `limit` | int | | `50` | زیادہ سے زیادہ واپسی کی تعداد |

### cleanup_stale_memories

| پیرامیٹر | قسم | لازمی | ڈیفالٹ | وضاحت |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | پرانے دن کی حد |
| `min_access_count` | int | | `2` | کم از کم رسائی تعداد کی حد |
| `group_id` | string | | | گروپ فلٹرنگ |
| `dry_run` | bool | | `true` | پیش نظارہ موڈ (حقیقت میں حذف نہیں) |
| `limit` | int | | `50` | زیادہ سے زیادہ پروسیسنگ کی تعداد |

### get_memory_task_status

| پیرامیٹر | قسم | لازمی | وضاحت |
|------|------|------|------|
| `task_id` | string | Y | پس منظر ٹاسک ID (`add_memory_simple(background=true)` سے واپس) |

## Web مینجمنٹ انٹرفیس

HTTP موڈ میں `http://localhost:8000/` تک رسائی حاصل کر کے استعمال کیا جا سکتا ہے۔

**خصوصیات:**
- ڈیش بورڈ — نوڈز کی تعداد، حقائق کی تعداد، میموری ٹکڑوں کی تعداد کی شماریات
- ادارہ نوڈز — براؤزنگ، فلٹرنگ، ویکٹر تلاش
- حقائق تعلقات — براؤزنگ، فلٹرنگ، ویکٹر تلاش
- میموری ٹکڑے — براؤزنگ، مکمل متن تلاش، حذف
- کمیونٹی براؤزنگ — کمیونٹی نوڈ فہرست، خلاصہ، کمیونٹی تعمیر متحرک کریں
- ٹرپلٹ فارم — براہ راست "موضوع-تعلق-مفعول" ساختہ علم شامل کریں
- Group مینجمنٹ — گروپ کے مطابق فلٹرنگ، بیچ حذف
- نالج گراف ویژولائزیشن — نوڈ تعلقات کی گرافیکل نمائش
- AI سوال و جواب — نالج گراف پر مبنی ذہین سوال و جواب
- معیار تجزیہ — میموری معیار اور احاطہ کا تجزیہ
- تھیم تبدیلی — تاریک/روشن تھیم

**REST API:**

| اینڈ پوائنٹ | طریقہ | وضاحت |
|------|------|------|
| `/api/stats` | GET | ڈیش بورڈ شماریات |
| `/api/groups` | GET | تمام group_id حاصل کریں |
| `/api/nodes` | GET | ادارہ نوڈز براؤز کریں (صفحہ بندی) |
| `/api/facts` | GET | حقائق براؤز کریں (صفحہ بندی) |
| `/api/episodes` | GET | میموری ٹکڑے براؤز کریں (صفحہ بندی) |
| `/api/search/nodes` | GET | نوڈز کی ویکٹر تلاش |
| `/api/search/facts` | GET | حقائق کی ویکٹر تلاش |
| `/api/search/advanced` | GET | جدید تلاش (16 حکمت عملیاں) |
| `/api/communities` | GET | کمیونٹی نوڈز براؤز کریں (صفحہ بندی) |
| `/api/communities/build` | POST | کمیونٹی تعمیر متحرک کریں |
| `/api/memory/add-bulk` | POST | بلک میموری شامل کریں |
| `/api/memory/add-triplet` | POST | ٹرپلٹ شامل کریں |
| `/api/memory/tasks` | GET | پس منظر ٹاسکس کی فہرست (حالت فلٹرنگ کی حمایت) |
| `/api/memory/tasks/{id}` | GET | واحد ٹاسک کی حالت کی تلاش |
| `/api/analytics/stale` | GET | پرانی میموریز کی تلاش |
| `/api/analytics/cleanup` | POST | پرانی میموریز کی صفائی |
| `/api/nodes/{uuid}` | DELETE | نوڈ حذف کریں |
| `/api/episodes/{uuid}` | DELETE | میموری ٹکڑا حذف کریں |
| `/api/facts/{uuid}` | DELETE | حقیقت حذف کریں |
| `/api/groups/{group_id}` | DELETE | پورا group حذف کریں |

## ترتیب

### ماحولیاتی متغیرات (.env)

ترتیب پرتوں والے میکانزم کا استعمال کرتی ہے: JSON ترتیب فائل بنیاد ہے، ماحولیاتی متغیرات انفرادی اقدار کو اوور رائیڈ کرتے ہیں۔

```bash
# === لازمی ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password        # ضرور تبدیل کریں

# === LLM فراہم کنندہ انتخاب ===
LLM_PROVIDER=ollama                 # ollama / glm / groq / openrouter / deepseek

# === Embedding فراہم کنندہ (اختیاری، ڈیفالٹ LLM_PROVIDER کی پیروی کرتا ہے) ===
# صرف glm GLM Embedding استعمال کرتا ہے، باقی سب Ollama bge-m3 استعمال کرتے ہیں
# EMBEDDING_PROVIDER=ollama         # ollama / glm

# === Ollama ترتیب (LLM_PROVIDER=ollama پر استعمال) ===
OLLAMA_MODEL=qwen2.5:3b             # بنیادی ماڈل (qwen2.5:3b تجویز کردہ)
OLLAMA_SMALL_MODEL=qwen2.5:3b       # چھوٹا ماڈل (سادہ کاموں کے لیے، مختلف ماڈل اختیاری)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.1

# === GLM ترتیب (LLM_PROVIDER=glm پر استعمال) ===
GLM_API_KEY=your_api_key            # https://open.bigmodel.cn سے حاصل کریں
GLM_MODEL=glm-4-flash               # مفت ماڈل
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768

# === GROQ ترتیب (LLM_PROVIDER=groq پر استعمال) ===
GROQ_API_KEY=your_api_key           # https://console.groq.com سے حاصل کریں
GROQ_MODEL=llama-3.3-70b-versatile

# === OpenRouter ترتیب (LLM_PROVIDER=openrouter پر استعمال) ===
OPENROUTER_API_KEY=your_api_key     # https://openrouter.ai/keys سے حاصل کریں
OPENROUTER_MODEL=stepfun/step-3.5-flash:free

# === DeepSeek ترتیب (LLM_PROVIDER=deepseek پر استعمال) ===
DEEPSEEK_API_KEY=your_api_key       # https://platform.deepseek.com سے حاصل کریں
DEEPSEEK_MODEL=deepseek-v4-flash    # یا deepseek-v4-pro

# === Ollama ایمبیڈنگ ماڈل (غیر glm ایمبیڈنگ پر ہمیشہ استعمال) ===
OLLAMA_EMBEDDING_MODEL=bge-m3
OLLAMA_EMBEDDING_DIMENSIONS=768

# === ڈسپلے اور لسانیات (اختیاری) ===
GRAPHITI_DISPLAY_TIMEZONE=Asia/Taipei # API واپسی ٹائم سٹیمپ ڈسپلے ٹائم زون (IANA نام؛ ذخیرہ UTC میں برقرار)
SERVER_LANG=zh-TW                     # MCP ٹول جوابی زبان (مکمل locale src/i18n.py میں دیکھیں)؛ REST API Accept-Language کے مطابق

# === میموری کارکردگی (اختیاری) ===
GRAPHITI_CHUNK_THRESHOLD=800         # ذہین تقسیم کو متحرک کرنے والی حروف کی تعداد کی حد
GRAPHITI_MAX_CHUNK_SIZE=600          # ہر حصے میں زیادہ سے زیادہ حروف کی تعداد
GRAPHITI_MAX_COROUTINES=10            # زیادہ سے زیادہ متوازی coroutine کی تعداد
GRAPHITI_DEFAULT_BACKGROUND=false    # آیا ڈیفالٹ پس منظر پروسیسنگ ہو

# === اہمیت کی ٹریکنگ اور ذہین فراموشی (اختیاری) ===
ENABLE_IMPORTANCE_TRACKING=true      # رسائی ٹریکنگ فعال کریں
IMPORTANCE_WEIGHT=0.1                # اہمیت کا وزن
STALE_DAYS_THRESHOLD=30              # پرانے دن کی حد
STALE_MIN_ACCESS_COUNT=2             # کم از کم رسائی تعداد

# === لاگنگ ===
LOG_FILE=logs/graphiti_mcp_server.log
LOG_LEVEL=INFO
```

> **مکمل ماحولیاتی متغیرات کی فہرست** کے لیے براہ کرم `.env.example` دیکھیں

### JSON ترتیب فائل

ورژن کنٹرول کی ضرورت والی ترتیب کے لیے موزوں (ماحولیاتی متغیرات اب بھی اوور رائیڈ کر سکتے ہیں):

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

## PM2 پس منظر میں چلانا

```bash
npm install -g pm2

pm2 start ecosystem.config.cjs      # شروع کریں
pm2 status                           # حالت
pm2 logs graphiti-mcp-http           # براہ راست لاگز
pm2 restart graphiti-mcp-http --update-env  # دوبارہ شروع کریں (.env دوبارہ لوڈ کریں)

pm2 save && pm2 startup              # بوٹ پر خود کار شروعات سیٹ کریں
```

> **اشارہ**: `.env` میں ترمیم کے بعد `--update-env` فلیگ کے ساتھ دوبارہ شروع کرنا ضروری ہے، ورنہ ماحولیاتی متغیرات اپ ڈیٹ نہیں ہوں گے۔

## Docker تعیناتی

```bash
docker build -t graphiti-mcp .

# نوٹ: Docker کنٹینر کو Neo4j اور Ollama سے کنکشن کے قابل ہونا ضروری ہے
# host network استعمال کرنا سب سے آسان ہے
docker run -p 8000:8000 --env-file .env --network host graphiti-mcp

# یا واضح طور پر بیرونی سروس ایڈریس متعین کریں
docker run -p 8000:8000 \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --env-file .env graphiti-mcp
```

## ٹیسٹنگ

```bash
# تمام ٹیسٹس چلائیں (183، تقریباً 1 سیکنڈ)
uv run python -m pytest tests/

# تفصیلی آؤٹ پٹ
uv run python -m pytest tests/ -v

# صرف مخصوص ٹیسٹ چلائیں
uv run python -m pytest tests/test_content_preprocessor.py -v
uv run python -m pytest tests/test_new_features.py -v
uv run python -m pytest tests/test_unit.py -v
```

> **نوٹ**: `test_integration_manual.py` میں 3 async ٹیسٹس کو `pytest-asyncio` تنصیب کی ضرورت ہے، نہ ہونے پر Failed دکھائے گا لیکن دوسرے ٹیسٹس پر اثر نہیں ڈالتا۔ `bench_deepseek_flash_vs_pro.py` کارکردگی بینچ مارک اسکرپٹ ہے، یونٹ ٹیسٹ نہیں۔

## مسائل کا حل

### Neo4j کنکشن ناکامی

```bash
neo4j status                              # سروس کی حالت جانچیں
cypher-shell -u neo4j -p your_password    # پاس ورڈ درست ہونے کی تصدیق کریں
curl http://localhost:7474                 # HTTP پورٹ کی تصدیق کریں
```

عام وجوہات:
- Neo4j شروع نہیں ہوا
- غلط پاس ورڈ (`.env` میں `NEO4J_PASSWORD`)
- پورٹ مصروف یا فائر وال کی رکاوٹ

### LLM کنکشن ناکامی

**Ollama موڈ:**
```bash
ollama serve                # Ollama سروس شروع کریں
ollama list                 # نصب شدہ ماڈلز جانچیں
ollama pull qwen2.5:3b      # غائب ماڈل نصب کریں
```

عام وجوہات: Ollama شروع نہیں ہوا، ماڈل نصب نہیں، GPU میموری ناکافی

**GLM موڈ:**
- `GLM_API_KEY` درست ہونے کی تصدیق کریں
- `GLM_EMBEDDING_DIMENSIONS=768` کی تصدیق کریں (Neo4j ویکٹر انڈیکس کے مطابق ہونا ضروری)
- GLM API اینڈ پوائنٹ: `https://open.bigmodel.cn/api/paas/v4/`

**GROQ موڈ:**
- `GROQ_API_KEY` درست ہونے کی تصدیق کریں
- Rate Limit بار بار ہونے پر GLM موڈ پر تبدیل کرنے پر غور کریں
- GROQ Embedding فراہم نہیں کرتا، Ollama ایمبیڈر دستیاب ہونا یقینی بنائیں

**OpenRouter موڈ:**
- `OPENROUTER_API_KEY` درست ہونے، `OPENROUTER_MODEL` ایک درست ماڈل ID ہونے کی تصدیق کریں (دیکھیں https://openrouter.ai/models)
- Embedding فراہم نہیں کرتا، Ollama ایمبیڈر دستیاب ہونا یقینی بنائیں

**DeepSeek موڈ:**
- `DEEPSEEK_API_KEY` درست ہونے کی تصدیق کریں
- اگر `Prompt must contain the word 'json'` ظاہر ہو: یہ DeepSeek `json_object` موڈ کا سخت تقاضا ہے، کلائنٹ میں بلٹ ان حفاظتی تحفظ موجود ہے؛ اگر اب بھی ظاہر ہو تو تصدیق کریں کہ تازہ ترین ورژن `src/deepseek_client.py` استعمال ہو رہا ہے اور سروس دوبارہ شروع کریں
- Embedding فراہم نہیں کرتا، Ollama ایمبیڈر دستیاب ہونا یقینی بنائیں

### MCP کنکشن خرابی

اگر `Invalid request parameters` یا `Received request before initialization was complete` ظاہر ہو:

1. تصدیق کریں کہ HTTP ٹرانسپورٹ موڈ استعمال ہو رہا ہے (**SSE استعمال نہ کریں**)
2. تصدیق کریں کہ کلائنٹ `"type": "http"`، `"url": "http://localhost:8000/mcp"` پر سیٹ ہے
3. سروس دوبارہ شروع کریں: `pm2 restart graphiti-mcp-http --update-env`
4. Claude Code میں `/mcp` چلائیں اور دوبارہ کنکٹ کریں

### میموری شامل کرنے کی سست رفتار

- **Ollama**: ماڈل کا سائز جانچیں (`qwen2.5:3b`، `7b` سے 5-10 گنا تیز)، تصدیق کریں کہ GPU استعمال ہو رہا ہے (`ollama ps`)
- **GLM**: ہر add_episode کو 10-20+ LLM نیٹ ورک راؤنڈ ٹرپس کی ضرورت ہوتی ہے، مختصر متن ~22s معمول کی قدر ہے
- **GROQ**: Rate Limit بہت سی دوبارہ کوششوں کا سبب بنتا ہے، بار بار استعمال پر GLM یا Ollama پر تبدیل کرنے کی سفارش
- بلاکنگ سے بچنے کے لیے `background=true` استعمال کریں
- طویل متن کو جلد تقسیم کرنے کے لیے `GRAPHITI_CHUNK_THRESHOLD` کم کریں

### PM2 مسائل

```bash
pm2 status                                        # حالت جانچیں
pm2 logs graphiti-mcp-http --err --lines 50        # خرابی لاگز
lsof -i :8000                                     # پورٹ کے قبضے کی جانچ
pm2 delete graphiti-mcp-http && pm2 start ecosystem.config.cjs  # مکمل دوبارہ شروع
```

## ترقیاتی تشخیصی ٹولز

```bash
uv run python tools/status_report.py           # مجموعی حالت رپورٹ (Neo4j + Ollama + ترتیب)
uv run python tools/validate_config.py         # .env اور ترتیب کی مکملیت کی تصدیق
uv run python tools/performance_diagnose.py    # LLM کارکردگی تشخیص
uv run python tools/inspect_schema.py          # Neo4j انڈیکس اور رکاوٹوں کی جانچ
uv run python tools/migrate_embeddings.py      # Embedding ماڈل منتقلی (ماڈل تبدیلی کے بعد ویکٹر دوبارہ تخلیق)
```

### Embedding ماڈل منتقلی

embedding ماڈل تبدیل کرنے کے بعد (جیسے `nomic-embed-text` → `bge-m3`)، منتقلی ٹول کا استعمال کرتے ہوئے تمام موجودہ ویکٹرز کو دوبارہ تخلیق کیا جا سکتا ہے، تاکہ تلاش کا معیار مستقل رہے:

```bash
# منتقلی کی ضرورت والی تعداد کا پیش نظارہ
uv run python tools/migrate_embeddings.py --dry-run

# مکمل منتقلی (بریک پوائنٹ سے دوبارہ چلانے کی حمایت)
uv run python tools/migrate_embeddings.py

# صرف مخصوص group منتقل کریں
uv run python tools/migrate_embeddings.py --group-id myproject

# بریک پوائنٹ سے جاری رکھیں (رکاوٹ کے بعد دوبارہ چلائیں)
uv run python tools/migrate_embeddings.py --resume
```

> **مطابقت**: `bge-m3` اصل طور پر 1024 جہتوں کا ہے، سسٹم موجودہ Neo4j ویکٹر انڈیکس کے ساتھ مطابقت کے لیے خود بخود 768 جہتوں تک کاٹ دیتا ہے۔ منتقلی سے پہلے اور بعد کا ڈیٹا ساتھ موجود رہ سکتا ہے، لیکن بہترین تلاش معیار حاصل کرنے کے لیے مکمل منتقلی انجام دینے کی سفارش کی جاتی ہے۔

## دستاویزات

- [ٹولز استعمال کرنے کی ہدایات](../使用工具的指令.md) — MCP ٹول استعمال گائیڈ اور بہترین طریقے
- [Graphiti Memory Rules](../graphiti-memory-rules.md) — میموری قواعد کی وضاحت

## لائسنس

MIT License
