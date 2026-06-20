# Graphiti MCP Server

خدمة ذاكرة الرسم البياني المعرفي — خادم MCP الذي يدمج مزوّدي LLM متعددين (Ollama / GLM / GROQ / OpenRouter / DeepSeek) مع قاعدة بيانات الرسم البياني Neo4j.

تم تطويره كامتداد لمشروع [getzep/graphiti](https://github.com/getzep/graphiti)، ويدعم التبديل المرن بين Ollama المحلي وLLM السحابي، ويمكنه تحديد مزوّد Embedding بشكل مستقل (مفصول عن LLM).

## الميزات المتميزة

- **إدارة ذاكرة ذكية** — استخدام الرسم البياني المعرفي لتخزين واسترجاع علاقات الذاكرة المعقدة
- **البحث الدلالي** — بحث هجين قائم على التضمينات المتجهة (متجه + كلمة مفتاحية + اجتياز الرسم البياني)
- **16 استراتيجية بحث** — يدعم البحث المتقدم أساليب إعادة ترتيب متعددة مثل RRF وMMR وCross-Encoder
- **مزوّدو LLM متعددون** — يدعم Ollama (محلي)، وGLM (الذكاء الاصطناعي من Zhipu، مجاني)، وGROQ (استدلال عالي السرعة)، وOpenRouter (تجميع نماذج من مزوّدين متعددين)، وDeepSeek، مع التبديل بنقرة واحدة عبر متغيرات البيئة
- **فصل Embedding عن LLM** — يمكن تحديد المُضمِّن بشكل مستقل عبر `EMBEDDING_PROVIDER`، ويعود LLM السحابي تلقائيًا إلى `bge-m3` المحلي
- **توزيع نموذجين** — في وضع Ollama، تستخدم المهام المعقدة النموذج الرئيسي، بينما تتحول المهام البسيطة تلقائيًا إلى النموذج الصغير لتحسين الأداء
- **تقسيم المحتوى الذكي** — تتم معالجة النصوص الطويلة بالتقسيم التلقائي إلى أجزاء، مما يقلل الحمل على LLM (عتبة قابلة للتهيئة)
- **معالجة الذاكرة في الخلفية** — يمكن تنفيذ إضافة الذاكرة في الخلفية، مع عودة فورية لاستدعاء MCP؛ تُحفَظ حالات المهام في SQLite وتُستعاد تلقائيًا بعد إعادة التشغيل
- **إزالة تكرار الذاكرة** — كشف تلقائي للذاكرة الموجودة شديدة التشابه، لتجنب التخزين المكرر
- **كشف التعارض** — كشف الحقائق المتناقضة بين كيانين، وتمييز المعلومات الملغاة من السارية
- **كشف المجتمعات** — تجميع تلقائي للكيانات ذات الصلة بناءً على خوارزمية Label Propagation
- **تتبّع الأهمية** — تسجيل تلقائي لتكرار الوصول إلى الكيانات، وترتيب نتائج البحث حسب الأهمية
- **النسيان الذكي** — تحديد وتنظيف الذاكرة القديمة قليلة الوصول، للحفاظ على رشاقة الرسم البياني
- **الاستيراد بالجملة** — تقديم عدة سجلات ذاكرة دفعة واحدة، مناسب لترحيل كميات كبيرة من البيانات
- **الثلاثيات المهيكلة** — إضافة «فاعل-علاقة-مفعول» مباشرة، مع تخطّي استخراج LLM، يكتمل في ثوانٍ
- **واجهة الإدارة عبر الويب** — تتضمن لوحة معلومات وتصفّحًا وبحثًا وتصوّرًا للرسم البياني المعرفي وأسئلة وأجوبة بالذكاء الاصطناعي وتصفّح المجتمعات وصيانة الجودة والاستيراد بالجملة والإعدادات في وقت التشغيل
- **تعدّد اللغات (i18n)** — تدعم رسائل الاستجابة 33 لغة (تشمل zh-TW / en / zh-CN / ja / pt-BR / ko / es / de / fr وغيرها؛ zh-TW/en/zh-CN/ja مكتوبة يدويًا، والبقية يوفّرها الطبقة المُولَّدة)؛ تعتمد أدوات MCP على `SERVER_LANG`، بينما تتفاوض REST API تلقائيًا اعتمادًا على ترويسة HTTP `Accept-Language`
- **سمة داكنة/فاتحة** — تدعم واجهة الويب تبديل السمة
- **الوضع الآمن** — إضافة ذاكرة سريعة مع خيار تخطّي استخراج الكيانات
- **دعم Docker** — يتضمن Dockerfile مدمجًا، ويدعم النشر بالحاويات
- **أمان التزامن** — يحمي asyncio.Lock عملية التهيئة، لمنع ظروف التسابق
- **فحص صحة متعدد الطبقات** — `/health` (liveness) + `/health/ready` (readiness)

## متطلبات النظام

| العنصر | المتطلب |
|------|------|
| Python | 3.10+ (يُوصى بـ 3.11+) |
| Neo4j | 4.0+ (`bolt://localhost:7687`) |
| مزوّد LLM | Ollama / GLM / GROQ / OpenRouter / DeepSeek (اختَر واحدًا من خمسة) |
| Node.js | 18+ (يُستخدم فقط لتشغيل PM2 في الخلفية، اختياري) |
| مساحة القرص | ~3GB (نماذج Ollama + بيانات Neo4j) |

### اختيار مزوّد LLM

التبديل عبر متغير البيئة `LLM_PROVIDER` (`ollama` / `glm` / `groq` / `openrouter` / `deepseek`):

| المزوّد | المميزات | نموذج LLM | Embedding | السيناريو المناسب |
|--------|------|----------|-----------|----------|
| **Ollama** (افتراضي) | محلي بالكامل، لا تغادر البيانات الجهاز | `qwen2.5:3b` | `bge-m3` (ممتاز للصينية + RAG) | يمتلك GPU، يهتم بالخصوصية |
| **GLM** | سحابي مجاني، مستقر بلا حدود معدّل | `glm-4-flash` (مجاني) | `embedding-3` | بلا GPU، سيناريوهات كثيفة البحث |
| **GROQ** | استدلال فائق السرعة | `llama-3.3-70b-versatile` | يعود إلى Ollama `bge-m3` | كتابة عرضية، السعي للجودة |
| **OpenRouter** | تجميع نماذج من مزوّدين متعددين، يشمل حصة مجانية | `stepfun/step-3.5-flash:free` وغيرها | يعود إلى Ollama `bge-m3` | الرغبة في استخدام نموذج سحابي محدد |
| **DeepSeek** | سحابة DeepSeek، عالية القيمة مقابل السعر | `deepseek-v4-flash` / `deepseek-v4-pro` | يعود إلى Ollama `bge-m3` | فهم الصينية، سحابة منخفضة التكلفة |

> **فصل Embedding عن LLM**: يُحدَّد المُضمِّن بشكل مستقل عبر `EMBEDDING_PROVIDER` (`ollama` / `glm`)، وعند عدم تعيينه يتبع `LLM_PROVIDER`. في الواقع، يستخدم `glm` فقط GLM `embedding-3`، بينما تستخدم البقية (بما في ذلك LLM السحابي الذي لا يوفر Embedding مثل GROQ / OpenRouter / DeepSeek) تلقائيًا Ollama `bge-m3`. **لذلك عند استخدام أي LLM سحابي، لا يزال يلزم Ollama المحلي لتوفير خدمة التضمين (ما لم يُضبط embedding أيضًا على glm).**

#### وضع Ollama (محلي)

```bash
# نموذج LLM الرئيسي (يُوصى بـ qwen2.5:3b، أفضل توازن بين السرعة والاستقرار)
ollama pull qwen2.5:3b

# نموذج التضمين (إلزامي، يُستخدم للبحث المتجهي)
ollama pull bge-m3
```

> **ملاحظات حول اختيار النموذج**:
> - `qwen2.5:3b` — مُوصى به، ~2 ثانية/استدعاء، ~100 رمز/ثانية، إخراج مهيكل من graphiti-core مستقر بنسبة 100%
> - `qwen2.5:7b` — تأثير أفضل لكنه أبطأ بـ 5-10 مرات، مناسب لسيناريوهات تسعى للجودة
> - `qwen2.5:1.5b` — الأسرع لكنه **غير مستقر** (معدّل نجاح JSON المهيكل 33% فقط)، لا يُوصى باستخدامه

#### وضع GLM (سحابة الذكاء الاصطناعي من Zhipu)

```bash
# إعدادات .env
LLM_PROVIDER=glm
GLM_API_KEY=your_api_key          # احصل عليه من https://open.bigmodel.cn
GLM_MODEL=glm-4-flash             # نموذج مجاني
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768      # يجب أن يطابق أبعاد فهرس المتجهات في Neo4j
```

> **مرجع أداء GLM**: الكتابة ~22 ثانية (نص قصير)، البحث ~0.34 ثانية، صفر أخطاء Rate Limit، أبطأ بـ 2-5 مرات من Ollama المحلي لكنه مجاني تمامًا.

#### وضع GROQ (استدلال عالي السرعة)

```bash
# إعدادات .env
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key         # احصل عليه من https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile
```

> **ملاحظة**: لا يوفر GROQ خدمة Embedding، ويلزم إقرانه بمُضمِّن Ollama (العودة التلقائية) أو ضبط `EMBEDDING_PROVIDER` على glm. يمتلك GROQ حدود معدّل صارمة، والاستخدام عالي التردد سيؤدي إلى عدد كبير من إعادات المحاولة.

#### وضع OpenRouter (تجميع نماذج من مزوّدين متعددين)

```bash
# إعدادات .env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_api_key       # احصل عليه من https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free   # يمكن تغييره إلى أي نموذج من OpenRouter
```

> **ملاحظة**: لا يوفر OpenRouter خدمة Embedding، ويعود تلقائيًا إلى Ollama `bge-m3`. قائمة النماذج على https://openrouter.ai/models (تتضمن عدة نماذج `:free` مجانية).

#### وضع DeepSeek

```bash
# إعدادات .env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key         # احصل عليه من https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash      # مُوصى به؛ أو deepseek-v4-pro (تأثير أفضل)
```

> **ملاحظة**: لا يوفر DeepSeek خدمة Embedding، ويعود تلقائيًا إلى Ollama `bge-m3`. سيتم إيقاف `deepseek-chat` / `deepseek-reasoner` بتاريخ 2026-07-24، ويُوصى بالتحول إلى `deepseek-v4-flash` / `deepseek-v4-pro`. يشترط DeepSeek بصرامة أن يحتوي الموجِّه (prompt) في وضع `json_object` على سلسلة "json"، وقد تم تضمين حماية احتياطية في العميل، فلا حاجة لإعدادات إضافية.

## البدء السريع

### 1. التحضير المسبق

تأكد من أن Neo4j يعمل محليًا، وحضّر الخدمة المقابلة وفقًا لمزوّد LLM المختار:

```bash
# تأكد من أن Neo4j قيد التشغيل (إلزامي)
neo4j status
# أو استخدم Docker: docker run -d -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/your_password neo4j:latest

# وضع Ollama: تأكد من أن Ollama قيد التشغيل
ollama list
# إذا لم يبدأ: ollama serve

# وضع GLM / GROQ: يلزم فقط مفتاح API صالح، دون حاجة لخدمة محلية
```

### 2. تثبيت التبعيات

```bash
git clone <repo-url>
cd graphiti
uv sync
```

> **ملاحظة**: يستخدم هذا المشروع [uv](https://github.com/astral-sh/uv) لإدارة التبعيات. إذا لم يكن مثبّتًا: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 3. تهيئة البيئة

```bash
cp .env.example .env
```

عدّل `.env`، **بحدّ أدنى** تحتاج إلى تعديل العناصر التالية:

```bash
NEO4J_PASSWORD=your_actual_password  # إلزامي: كلمة مرور Neo4j
LLM_PROVIDER=ollama                  # ollama / glm / groq / openrouter / deepseek
OLLAMA_MODEL=qwen2.5:3b              # وضع Ollama: نموذج LLM المحلي
# GLM_API_KEY=your_key               # وضع GLM: مفتاح API للذكاء الاصطناعي من Zhipu
# GROQ_API_KEY=your_key              # وضع GROQ: مفتاح API لـ GROQ
# OPENROUTER_API_KEY=your_key        # وضع OpenRouter: مفتاح API
# DEEPSEEK_API_KEY=your_key          # وضع DeepSeek: مفتاح API
```

### 4. بدء الخدمة

```bash
# وضع HTTP (مُوصى به، يتضمن واجهة الإدارة عبر الويب)
uv run python graphiti_mcp_server.py --transport http --port 8000

# أو استخدم PM2 للتشغيل في الخلفية (مُوصى به للتشغيل طويل الأمد)
pm2 start ecosystem.config.cjs
```

### 5. التحقق من الخدمة

بعد البدء يمكن الوصول إلى نقاط النهاية التالية:

| نقطة النهاية | الوصف |
|------|------|
| http://localhost:8000/ | واجهة الإدارة عبر الويب |
| http://localhost:8000/mcp | نقطة نهاية MCP (لاتصال عملاء MCP) |
| http://localhost:8000/health | فحص الصحة (liveness) |
| http://localhost:8000/health/ready | فحص عميق (يشمل اتصال Neo4j) |
| http://localhost:8000/api/stats | إحصائيات REST API |

## بنية المشروع

```
graphiti/
├── graphiti_mcp_server.py        # المدخل الرئيسي — تعريف أدوات MCP (19 أداة)
├── src/
│   ├── config.py                 # إدارة التهيئة (GraphitiConfig، يدعم التحميل المتراكب JSON/.env)
│   ├── web_api.py                # REST API لواجهة الإدارة عبر الويب (30+ نقطة نهاية)
│   ├── ollama_graphiti_client.py  # عميل LLM لـ Ollama (توزيع نموذجين)
│   ├── openai_compat_client.py   # فئة أساسية لـ LLM المتوافق مع OpenAI (json_object + تبسيط schema + حماية json احتياطية)
│   ├── glm_client.py             # عميل LLM لـ GLM (الذكاء الاصطناعي من Zhipu) (يرث OpenAICompatClient)
│   ├── openrouter_client.py      # عميل LLM لـ OpenRouter (يرث OpenAICompatClient)
│   ├── deepseek_client.py        # عميل LLM لـ DeepSeek (يرث OpenAICompatClient)
│   ├── ollama_embedder.py        # مُحوِّل نموذج تضمين Ollama
│   ├── content_preprocessor.py   # تقسيم المحتوى الذكي (تقسيم تلقائي للنصوص الطويلة)
│   ├── deduplication.py          # إزالة تكرار الذاكرة (مقارنة تشابه الجيب التمام)
│   ├── importance.py             # تتبّع الأهمية والنسيان الذكي
│   ├── safe_memory_add.py        # إضافة ذاكرة آمنة (تخطّي استخراج الكيانات)
│   ├── task_store.py             # تخزين مهام الخلفية في SQLite (TaskStore)
│   ├── timezone_utils.py         # تحويل المنطقة الزمنية (عرض UTC→المنطقة المحلية)
│   ├── i18n.py                   # تعدّد اللغات للخلفية (REST اعتمادًا على Accept-Language، MCP اعتمادًا على SERVER_LANG)
│   ├── i18n_generated.py         # تغطية لغوية مُولَّدة تلقائيًا (GENERATED_MESSAGE_OVERRIDES)
│   ├── exceptions.py             # معالجة الاستثناءات المهيكلة (12 فئة استثناء)
│   └── logging_setup.py          # نظام السجلات (تدوير زمني + مراقبة الأداء)
├── web/                          # واجهة الإدارة عبر الويب الأمامية (SPA، بلا build)
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js                # تغليف REST API
│       ├── components.js         # عرض مكوّنات الواجهة (يشمل صفحة المجتمعات)
│       └── app.js                # توجيه SPA، إدارة الحالة
├── tests/                        # حزمة الاختبارات (203 اختبارًا)
│   ├── test_content_preprocessor.py  # اختبار منطق التقسيم (17 اختبارًا)
│   ├── test_new_features.py      # اختبار الميزات الجديدة (32 اختبارًا)
│   ├── test_i18n.py             # اختبار تعدّد اللغات (57 اختبارًا)
│   ├── test_unit.py              # اختبار الوحدة
│   ├── test_web_api.py           # اختبار Web API
│   ├── test_web_ui_features.py   # اختبار ميزات Web UI
│   ├── test_integration_manual.py # اختبار تكامل يدوي
│   └── bench_deepseek_flash_vs_pro.py # سكريبت معيار أداء flash/pro لـ DeepSeek
├── tools/                        # أدوات تشخيص التطوير
│   ├── status_report.py          # تقرير حالة موحّد
│   ├── validate_config.py        # التحقق من التهيئة
│   ├── performance_diagnose.py   # تشخيص الأداء
│   ├── inspect_schema.py         # فحص بنية Neo4j
│   ├── batch_reprocess.py        # إعادة المعالجة بالدفعات
│   └── migrate_embeddings.py     # ترحيل نموذج Embedding (إعادة توليد المتجهات بعد تبديل النموذج)
├── docs/                         # التوثيق
├── logs/                         # السجلات (تدوير زمني، يُحتفظ بها افتراضيًا 30 يومًا)
├── Dockerfile                    # نشر بحاويات Docker
└── ecosystem.config.cjs          # تهيئة PM2
```

## إعداد عميل MCP

### وضع HTTP (مُوصى به)

مناسب لعملاء MCP الذين يدعمون HTTP مثل Claude Code وCline:

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

### وضع STDIO

مناسب للعملاء الذين يحتاجون إلى بدء العملية مباشرة مثل Claude Desktop:

**موقع ملف التهيئة:**
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

> **ملاحظة**: لم يعد يُوصى باستخدام وضع SSE (`--transport sse`). يوجد في MCP 1.x مشكلة توافق في تهيئة الجلسة، يُرجى التحول إلى وضع HTTP.

## أدوات MCP (19 أداة)

### إدارة الذاكرة (7 أدوات)

| الأداة | الوصف |
|------|------|
| `add_memory_simple` | إضافة ذاكرة إلى الرسم البياني المعرفي (يدعم المعالجة في الخلفية، التقسيم الذكي، فحص إزالة التكرار) |
| `add_episode_bulk` | إضافة عدة سجلات ذاكرة بالجملة (معالجة في الخلفية افتراضيًا) |
| `add_triplet` | إضافة ثلاثية مهيكلة (تخطّي LLM، يكتمل في ثوانٍ) |
| `search_memory_nodes` | البحث في عُقد الذاكرة (يدعم 16 استراتيجية بحث، تصفية زمنية) |
| `search_memory_facts` | البحث في حقائق الذاكرة (يدعم تصفية نوع العلاقة، النطاق الزمني، تصفية السريان) |
| `advanced_search` | البحث المتقدم (16 استراتيجية، يعيد العُقد + الحواف + المجتمعات + المقاطع) |
| `get_episodes` | الحصول على أحدث مقاطع الذاكرة |

### تحليل المعرفة (3 أدوات)

| الأداة | الوصف |
|------|------|
| `check_conflicts` | كشف تعارض الحقائق بين كيانين (ساري مقابل ملغى) |
| `get_node_edges` | استكشاف علاقات الحواف الواردة والصادرة للعقدة |
| `build_communities` | تشغيل كشف المجتمعات والتجميع (معالجة في الخلفية افتراضيًا) |

### صيانة الذاكرة (أداتان)

| الأداة | الوصف |
|------|------|
| `get_stale_memories` | الاستعلام عن الذاكرة القديمة قليلة الوصول |
| `cleanup_stale_memories` | تنظيف الذاكرة القديمة (وضع المعاينة dry_run افتراضيًا) |

### إدارة المهام

| الأداة | الوصف |
|------|------|
| `get_memory_task_status` | الاستعلام عن تقدّم ونتيجة مهمة معالجة الذاكرة في الخلفية |

### الحذف والاستعلام

| الأداة | الوصف |
|------|------|
| `delete_episode` | حذف مقطع ذاكرة |
| `delete_entity_edge` | حذف حافة كيان (علاقة) |
| `get_entity_edge` | الحصول على معلومات تفصيلية لحافة الكيان |

### إدارة النظام

| الأداة | الوصف |
|------|------|
| `get_status` | الحصول على حالة الخدمة (Neo4j، LLM، المُضمِّن) |
| `test_connection` | اختبار اتصال Neo4j / LLM / المُضمِّن |
| `clear_graph` | مسح قاعدة بيانات الرسم البياني (يدعم المسح حسب group_id) |

## معاملات الأدوات

### add_memory_simple

| المعامل | النوع | إلزامي | القيمة الافتراضية | الوصف |
|------|------|------|--------|------|
| `name` | string | Y | | اسم الذاكرة |
| `episode_body` | string | Y | | محتوى الذاكرة (يُقسَّم تلقائيًا إذا تجاوز 800 حرف) |
| `group_id` | string | | `"default"` | معرّف المجموعة (يُوصى بالعزل حسب المشروع) |
| `source` | string | | `"text"` | نوع المصدر: `text` / `json` / `message` |
| `source_description` | string | | `"MCP Server"` | وصف المصدر |
| `use_safe_mode` | bool | | `false` | الوضع الآمن (تخطّي استخراج الكيانات، سريع لكن لا يمكن البحث في الذاكرة) |
| `background` | bool | | `false` | المعالجة في الخلفية (عودة فورية لـ task_id، مناسب للنصوص الطويلة) |
| `force` | bool | | `false` | تخطّي فحص إزالة التكرار (الإضافة بالإجبار) |
| `excluded_entity_types` | list | | | أنواع الكيانات المستبعدة (تقليل الاستخراج غير المطلوب) |

> **نصائح الأداء**:
> - النص القصير (<800 حرف): معالجة مباشرة، عادةً يكتمل في 30-40 ثانية
> - النص الطويل (>800 حرف): يُقسَّم تلقائيًا إلى أجزاء، باستخدام `add_episode_bulk` للمعالجة المتزامنة (أسرع بـ ~33% من المعالجة التسلسلية)
> - استخدام `background=true` يتجنب حجب استدعاء MCP، وتتبّع التقدّم عبر `get_memory_task_status`
> - `use_safe_mode=true` يكتمل في ثوانٍ لكن لا يمكن لأدوات البحث العثور على الذاكرة
> - عند تفعيل إزالة التكرار، يُحذَّر من الذاكرة شديدة التشابه (يمكن تخطّيها بـ `force=true`)

### add_episode_bulk

| المعامل | النوع | إلزامي | القيمة الافتراضية | الوصف |
|------|------|------|--------|------|
| `episodes` | list | Y | | قائمة الذاكرة، كل عنصر يحتوي على `name` و`content` |
| `group_id` | string | | `"default"` | معرّف المجموعة |
| `source` | string | | `"text"` | نوع المصدر |
| `background` | bool | | `true` | المعالجة في الخلفية (المعالجة بالجملة عادةً تستغرق وقتًا) |

### add_triplet

| المعامل | النوع | إلزامي | القيمة الافتراضية | الوصف |
|------|------|------|--------|------|
| `source_name` | string | Y | | اسم الكيان المصدر (مثل "Alice") |
| `target_name` | string | Y | | اسم الكيان الهدف (مثل "Google") |
| `relation_name` | string | Y | | اسم العلاقة (مثل "works_at") |
| `fact` | string | Y | | وصف الحقيقة (مثل "Alice works at Google") |
| `group_id` | string | | `"default"` | معرّف المجموعة |
| `source_labels` | list | | | تسميات الكيان المصدر |
| `target_labels` | list | | | تسميات الكيان الهدف |

### search_memory_nodes

| المعامل | النوع | إلزامي | القيمة الافتراضية | الوصف |
|------|------|------|--------|------|
| `query` | string | Y | | كلمة البحث المفتاحية (لغة طبيعية) |
| `max_nodes` | int | | `10` | أقصى عدد للإرجاع |
| `group_ids` | list | | | تصفية المجموعات (بحث مشترك لعدة مجموعات) |
| `entity_types` | list | | | تصفية نوع الكيان |
| `search_recipe` | string | | | استراتيجية البحث (انظر البحث المتقدم) |
| `created_after` | string | | | الحد الأدنى لوقت الإنشاء (ISO datetime) |
| `created_before` | string | | | الحد الأقصى لوقت الإنشاء (ISO datetime) |

### search_memory_facts

| المعامل | النوع | إلزامي | القيمة الافتراضية | الوصف |
|------|------|------|--------|------|
| `query` | string | Y | | كلمة البحث المفتاحية |
| `max_facts` | int | | `10` | أقصى عدد للإرجاع |
| `group_ids` | list | | | تصفية المجموعات |
| `center_node_uuid` | string | | | UUID للعقدة المركزية (استكشاف علاقات عقدة محددة) |
| `edge_types` | list | | | تصفية نوع العلاقة (مثل `["works_at"]`) |
| `created_after` | string | | | الحد الأدنى لوقت الإنشاء (ISO datetime) |
| `created_before` | string | | | الحد الأقصى لوقت الإنشاء (ISO datetime) |
| `only_valid` | bool | | `false` | إرجاع الحقائق غير الملغاة فقط |

### advanced_search

| المعامل | النوع | إلزامي | القيمة الافتراضية | الوصف |
|------|------|------|--------|------|
| `query` | string | Y | | كلمة البحث المفتاحية |
| `search_recipe` | string | | `"combined_rrf"` | استراتيجية البحث (16 خيارًا) |
| `max_results` | int | | `10` | أقصى عدد للإرجاع |
| `group_ids` | list | | | تصفية المجموعات |
| `center_node_uuid` | string | | | UUID للعقدة المركزية |

**استراتيجيات البحث المتاحة (search_recipe):**

| الفئة | الاستراتيجية | الوصف |
|------|------|------|
| مدمجة | `combined_rrf` | دمج RRF المدمج (افتراضي، مُوصى به) |
| مدمجة | `combined_mmr` | إعادة ترتيب التنوّع MMR المدمج |
| مدمجة | `combined_cross_encoder` | الترتيب الدقيق Cross-Encoder المدمج |
| حافة | `edge_rrf` / `edge_mmr` / `edge_cross_encoder` | بحث الحواف (3 طرق ترتيب) |
| حافة | `edge_node_distance` / `edge_episode_mentions` | بحث الحواف (مسافة الرسم البياني/عدد الاقتباسات) |
| عقدة | `node_rrf` / `node_mmr` / `node_cross_encoder` | بحث العُقد (3 طرق ترتيب) |
| عقدة | `node_node_distance` / `node_episode_mentions` | بحث العُقد (مسافة الرسم البياني/عدد الاقتباسات) |
| مجتمع | `community_rrf` / `community_mmr` / `community_cross_encoder` | بحث المجتمعات |

### check_conflicts

| المعامل | النوع | إلزامي | القيمة الافتراضية | الوصف |
|------|------|------|--------|------|
| `source_name` | string | Y | | اسم الكيان المصدر |
| `target_name` | string | Y | | اسم الكيان الهدف |
| `group_id` | string | | `"default"` | معرّف المجموعة |

### get_node_edges

| المعامل | النوع | إلزامي | القيمة الافتراضية | الوصف |
|------|------|------|--------|------|
| `node_uuid` | string | Y | | UUID للعقدة |
| `include_inbound` | bool | | `true` | تضمين الحواف الواردة |
| `include_outbound` | bool | | `true` | تضمين الحواف الصادرة |
| `max_edges` | int | | `50` | أقصى عدد للإرجاع |

### build_communities

| المعامل | النوع | إلزامي | القيمة الافتراضية | الوصف |
|------|------|------|--------|------|
| `group_ids` | list | | | تحديد المجموعات (اتركها فارغة لجميعها) |
| `background` | bool | | `true` | المعالجة في الخلفية |

### get_stale_memories

| المعامل | النوع | إلزامي | القيمة الافتراضية | الوصف |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | تجاوز كم يومًا دون وصول يُعتبر قديمًا |
| `min_access_count` | int | | `2` | يُدرَج فقط إذا كان عدد الوصول أقل من هذه القيمة |
| `group_id` | string | | | تصفية المجموعات |
| `limit` | int | | `50` | أقصى عدد للإرجاع |

### cleanup_stale_memories

| المعامل | النوع | إلزامي | القيمة الافتراضية | الوصف |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | عتبة أيام القِدَم |
| `min_access_count` | int | | `2` | عتبة الحد الأدنى لعدد الوصول |
| `group_id` | string | | | تصفية المجموعات |
| `dry_run` | bool | | `true` | وضع المعاينة (دون حذف فعلي) |
| `limit` | int | | `50` | أقصى عدد للمعالجة |

### get_memory_task_status

| المعامل | النوع | إلزامي | الوصف |
|------|------|------|------|
| `task_id` | string | Y | معرّف المهمة الخلفية (يُعاد بواسطة `add_memory_simple(background=true)`) |

## واجهة الإدارة عبر الويب

في وضع HTTP يمكن الوصول إلى `http://localhost:8000/` للاستخدام.

**الميزات:**
- لوحة المعلومات — إحصائيات عدد العُقد، عدد الحقائق، عدد مقاطع الذاكرة
- عُقد الكيانات — التصفّح، التصفية، البحث المتجهي
- علاقات الحقائق — التصفّح، التصفية، البحث المتجهي
- مقاطع الذاكرة — التصفّح، البحث في النص الكامل، الحذف
- تصفّح المجتمعات — قائمة عُقد المجتمعات، الملخص، تشغيل بناء المجتمعات
- نموذج الثلاثيات — إضافة معرفة مهيكلة «فاعل-علاقة-مفعول» مباشرة
- إدارة المجموعات — التصفية حسب المجموعة، الحذف بالدفعات
- تصوّر الرسم البياني المعرفي — عرض رسومي لعلاقات العُقد
- أسئلة وأجوبة بالذكاء الاصطناعي — أسئلة وأجوبة ذكية قائمة على الرسم البياني المعرفي
- تحليل الجودة — تحليل جودة الذاكرة والتغطية
- صيانة الجودة — مؤشرات جودة الذاكرة وأدوات التنظيف
- الاستيراد بالجملة — استيراد عدة مقاطع ذاكرة دفعة واحدة (JSON، حد أقصى 500 سجل في المرة)
- الإعدادات في وقت التشغيل — عرض الإعدادات الحالية السارية وتعديل بعض المعاملات دون إعادة التشغيل
- تبديل السمة — سمة داكنة/فاتحة

**REST API:**

| نقطة النهاية | الطريقة | الوصف |
|------|------|------|
| `/api/stats` | GET | إحصائيات لوحة المعلومات |
| `/api/groups` | GET | الحصول على جميع group_id |
| `/api/groups/stats` | GET | إحصائيات العُقد/الحقائق/المقاطع لكل مجموعة |
| `/api/nodes` | GET | تصفّح عُقد الكيانات (بترقيم الصفحات) |
| `/api/facts` | GET | تصفّح الحقائق (بترقيم الصفحات) |
| `/api/episodes` | GET | تصفّح مقاطع الذاكرة (بترقيم الصفحات) |
| `/api/nodes/{uuid}/relations` | GET | الحصول على الحواف الواردة/الصادرة للعقدة |
| `/api/search/nodes` | GET | بحث متجهي عن العُقد |
| `/api/search/facts` | GET | بحث متجهي عن الحقائق |
| `/api/search/episodes` | GET | البحث في مقاطع الذاكرة |
| `/api/search/advanced` | GET | البحث المتقدم (16 استراتيجية) |
| `/api/communities` | GET | تصفّح عُقد المجتمعات (بترقيم الصفحات) |
| `/api/communities/build` | POST | تشغيل بناء المجتمعات |
| `/api/memory/add` | POST | إضافة سجل ذاكرة واحد |
| `/api/memory/add-bulk` | POST | إضافة ذاكرة بالجملة |
| `/api/memory/add-triplet` | POST | إضافة ثلاثية |
| `/api/import/episodes` | POST | استيراد مقاطع ذاكرة بالجملة (JSON، حد أقصى 500 سجل) |
| `/api/memory/tasks` | GET | سرد المهام الخلفية (يدعم تصفية الحالة) |
| `/api/memory/tasks/{id}` | GET | الاستعلام عن حالة مهمة واحدة |
| `/api/timeline` | GET | تصفّح الجدول الزمني |
| `/api/graph/subgraph` | GET | الحصول على رسم بياني فرعي (للتصوّر) |
| `/api/graph/all` | GET | الحصول على الرسم البياني الكامل (للتصوّر) |
| `/api/ask` | GET | أسئلة وأجوبة بالذكاء الاصطناعي (قائمة على البحث في الرسم البياني) |
| `/api/analytics/top-nodes` | GET | العُقد عالية الترابط/الوصول |
| `/api/analytics/quality` | GET | مؤشرات جودة الرسم البياني المعرفي |
| `/api/analytics/stale` | GET | الاستعلام عن الذاكرة القديمة |
| `/api/analytics/cleanup` | POST | تنظيف الذاكرة القديمة |
| `/api/config` | GET | الحصول على الإعدادات السارية حاليًا (باستثناء مفاتيح API) |
| `/api/config` | PATCH | تحديث الإعدادات القابلة للتعديل في وقت التشغيل (ساري على العملية الحالية فقط، يُستعاد عند إعادة التشغيل) |
| `/api/nodes/{uuid}` | DELETE | حذف عقدة |
| `/api/episodes/{uuid}` | DELETE | حذف مقطع ذاكرة |
| `/api/facts/{uuid}` | DELETE | حذف حقيقة |
| `/api/groups/{group_id}` | DELETE | حذف مجموعة كاملة |

## التهيئة

### متغيرات البيئة (.env)

تستخدم التهيئة آلية تراكب: ملف تهيئة JSON كأساس، ومتغيرات البيئة تتجاوز القيم الفردية.

```bash
# === إلزامي ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password        # يجب تعديله

# === اختيار مزوّد LLM ===
LLM_PROVIDER=ollama                 # ollama / glm / groq / openrouter / deepseek

# === مزوّد Embedding (اختياري، يتبع LLM_PROVIDER افتراضيًا) ===
# يستخدم glm فقط GLM Embedding، وتستخدم البقية جميعًا Ollama bge-m3
# EMBEDDING_PROVIDER=ollama         # ollama / glm

# === تهيئة Ollama (تُستخدم عند LLM_PROVIDER=ollama) ===
OLLAMA_MODEL=qwen2.5:3b             # النموذج الرئيسي (يُوصى بـ qwen2.5:3b)
OLLAMA_SMALL_MODEL=qwen2.5:3b       # النموذج الصغير (للمهام البسيطة، يمكن اختيار نموذج مختلف)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.1

# === تهيئة GLM (تُستخدم عند LLM_PROVIDER=glm) ===
GLM_API_KEY=your_api_key            # احصل عليه من https://open.bigmodel.cn
GLM_MODEL=glm-4-flash               # نموذج مجاني
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768

# === تهيئة GROQ (تُستخدم عند LLM_PROVIDER=groq) ===
GROQ_API_KEY=your_api_key           # احصل عليه من https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile

# === تهيئة OpenRouter (تُستخدم عند LLM_PROVIDER=openrouter) ===
OPENROUTER_API_KEY=your_api_key     # احصل عليه من https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free

# === تهيئة DeepSeek (تُستخدم عند LLM_PROVIDER=deepseek) ===
DEEPSEEK_API_KEY=your_api_key       # احصل عليه من https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash    # أو deepseek-v4-pro

# === نموذج تضمين Ollama (يُستخدم في كل تضمين غير glm) ===
OLLAMA_EMBEDDING_MODEL=bge-m3
OLLAMA_EMBEDDING_DIMENSIONS=768

# === العرض واللغة (اختياري) ===
GRAPHITI_DISPLAY_TIMEZONE=Asia/Taipei # المنطقة الزمنية لعرض الطابع الزمني الذي تعيده API (اسم IANA؛ يبقى التخزين بـ UTC)
SERVER_LANG=zh-TW                     # لغة استجابة أدوات MCP (اللغات المحلية الكاملة في src/i18n.py)؛ تعتمد REST API على Accept-Language

# === أداء الذاكرة (اختياري) ===
GRAPHITI_CHUNK_THRESHOLD=800         # عتبة عدد الأحرف لتشغيل التقسيم الذكي
GRAPHITI_MAX_CHUNK_SIZE=600          # أقصى عدد أحرف لكل جزء
GRAPHITI_MAX_COROUTINES=10            # أقصى عدد للكوروتينات المتزامنة
GRAPHITI_DEFAULT_BACKGROUND=false    # هل المعالجة في الخلفية افتراضية
TASK_DB_PATH=data/tasks.db           # مسار تخزين مهام الخلفية في SQLite

# === تتبّع الأهمية والنسيان الذكي (اختياري) ===
ENABLE_IMPORTANCE_TRACKING=true      # تفعيل تتبّع الوصول
IMPORTANCE_WEIGHT=0.1                # وزن الأهمية
STALE_DAYS_THRESHOLD=30              # عتبة أيام القِدَم
STALE_MIN_ACCESS_COUNT=2             # الحد الأدنى لعدد الوصول

# === السجلات ===
LOG_FILE=logs/graphiti_mcp_server.log
LOG_LEVEL=INFO
```

> **للحصول على قائمة متغيرات البيئة الكاملة** يُرجى الرجوع إلى `.env.example`

### ملف تهيئة JSON

مناسب للتهيئة التي تتطلب التحكم في الإصدارات (لا تزال متغيرات البيئة قادرة على التجاوز):

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

## التشغيل في الخلفية بـ PM2

```bash
npm install -g pm2

pm2 start ecosystem.config.cjs      # البدء
pm2 status                           # الحالة
pm2 logs graphiti-mcp-http           # السجلات الفورية
pm2 restart graphiti-mcp-http --update-env  # إعادة التشغيل (إعادة تحميل .env)

pm2 save && pm2 startup              # إعداد البدء التلقائي عند الإقلاع
```

> **تلميح**: بعد تعديل `.env` يجب إعادة التشغيل باستخدام علم `--update-env`، وإلا فلن تُحدَّث متغيرات البيئة.

## نشر Docker

```bash
docker build -t graphiti-mcp .

# ملاحظة: تحتاج حاوية Docker إلى القدرة على الاتصال بـ Neo4j وOllama
# استخدام host network هو الأبسط
docker run -p 8000:8000 --env-file .env --network host graphiti-mcp

# أو حدّد بوضوح عناوين الخدمات الخارجية
docker run -p 8000:8000 \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --env-file .env graphiti-mcp
```

## الاختبار

```bash
# تنفيذ جميع الاختبارات (203 اختبارًا، حوالي ثانية واحدة)
uv run python -m pytest tests/

# إخراج تفصيلي
uv run python -m pytest tests/ -v

# تنفيذ اختبار محدد فقط
uv run python -m pytest tests/test_content_preprocessor.py -v
uv run python -m pytest tests/test_new_features.py -v
uv run python -m pytest tests/test_unit.py -v
```

> **ملاحظة**: تحتاج الاختبارات async الثلاثة في `test_integration_manual.py` إلى تثبيت `pytest-asyncio`، وعند غيابه ستظهر بحالة Failed لكنها لا تؤثر على الاختبارات الأخرى. `bench_deepseek_flash_vs_pro.py` هو سكريبت معيار أداء، وليس اختبار وحدة.

## استكشاف الأخطاء وإصلاحها

### فشل اتصال Neo4j

```bash
neo4j status                              # فحص حالة الخدمة
cypher-shell -u neo4j -p your_password    # تأكد من صحة كلمة المرور
curl http://localhost:7474                 # تأكد من منفذ HTTP
```

الأسباب الشائعة:
- Neo4j لم يبدأ
- كلمة مرور خاطئة (`NEO4J_PASSWORD` في `.env`)
- المنفذ مشغول أو محجوب بجدار الحماية

### فشل اتصال LLM

**وضع Ollama:**
```bash
ollama serve                # بدء خدمة Ollama
ollama list                 # فحص النماذج المثبّتة
ollama pull qwen2.5:3b      # تثبيت النموذج المفقود
```

الأسباب الشائعة: Ollama لم يبدأ، النموذج غير مثبّت، ذاكرة GPU غير كافية

**وضع GLM:**
- تأكد من صحة `GLM_API_KEY`
- تأكد من `GLM_EMBEDDING_DIMENSIONS=768` (يجب أن يطابق فهرس المتجهات في Neo4j)
- نقطة نهاية GLM API: `https://open.bigmodel.cn/api/paas/v4/`

**وضع GROQ:**
- تأكد من صحة `GROQ_API_KEY`
- عند تكرار Rate Limit، فكّر في التحول إلى وضع GLM
- لا يوفر GROQ خدمة Embedding، ويجب التأكد من توفّر مُضمِّن Ollama

**وضع OpenRouter:**
- تأكد من صحة `OPENROUTER_API_KEY`، وأن `OPENROUTER_MODEL` معرّف نموذج صالح (انظر https://openrouter.ai/models)
- لا يوفر خدمة Embedding، ويجب التأكد من توفّر مُضمِّن Ollama

**وضع DeepSeek:**
- تأكد من صحة `DEEPSEEK_API_KEY`
- إذا ظهر `Prompt must contain the word 'json'`: هذا متطلب صارم لوضع `json_object` في DeepSeek، وقد تم تضمين حماية احتياطية في العميل؛ إذا استمر الظهور، تأكد من استخدام أحدث إصدار من `src/deepseek_client.py` وأعد تشغيل الخدمة
- لا يوفر خدمة Embedding، ويجب التأكد من توفّر مُضمِّن Ollama

### خطأ اتصال MCP

إذا ظهر `Invalid request parameters` أو `Received request before initialization was complete`:

1. تأكد من استخدام وضع نقل HTTP (**لا تستخدم SSE**)
2. تأكد من ضبط العميل على `"type": "http"`, `"url": "http://localhost:8000/mcp"`
3. أعد تشغيل الخدمة: `pm2 restart graphiti-mcp-http --update-env`
4. نفّذ `/mcp` في Claude Code لإعادة الاتصال

### بطء سرعة إضافة الذاكرة

- **Ollama**: افحص حجم النموذج (`qwen2.5:3b` أسرع بـ 5-10 مرات من `7b`)، وتأكد من استخدام GPU (`ollama ps`)
- **GLM**: يحتاج كل add_episode إلى 10-20+ رحلة شبكية ذهابًا وإيابًا إلى LLM، و~22 ثانية للنص القصير قيمة طبيعية
- **GROQ**: يؤدي Rate Limit إلى عدد كبير من إعادات المحاولة، وعند الاستخدام المتكرر يُوصى بالتحول إلى GLM أو Ollama
- استخدم `background=true` لتجنب الحجب
- اخفض `GRAPHITI_CHUNK_THRESHOLD` لجعل النصوص الطويلة تُقسَّم مبكرًا

### مشاكل PM2

```bash
pm2 status                                        # فحص الحالة
pm2 logs graphiti-mcp-http --err --lines 50        # سجل الأخطاء
lsof -i :8000                                     # فحص إشغال المنفذ
pm2 delete graphiti-mcp-http && pm2 start ecosystem.config.cjs  # إعادة تشغيل كاملة
```

## أدوات تشخيص التطوير

```bash
uv run python tools/status_report.py           # تقرير حالة موحّد (Neo4j + Ollama + التهيئة)
uv run python tools/validate_config.py         # التحقق من اكتمال .env والتهيئة
uv run python tools/performance_diagnose.py    # تشخيص أداء LLM
uv run python tools/inspect_schema.py          # فحص فهارس وقيود Neo4j
uv run python tools/migrate_embeddings.py      # ترحيل نموذج Embedding (إعادة توليد المتجهات بعد تبديل النموذج)
```

### ترحيل نموذج Embedding

بعد تبديل نموذج embedding (مثل `nomic-embed-text` → `bge-m3`)، يمكن استخدام أداة الترحيل لإعادة توليد جميع المتجهات الحالية، لضمان اتساق جودة البحث:

```bash
# معاينة العدد المطلوب ترحيله
uv run python tools/migrate_embeddings.py --dry-run

# ترحيل كامل (يدعم الاستئناف من نقطة التوقف)
uv run python tools/migrate_embeddings.py

# ترحيل مجموعة محددة فقط
uv run python tools/migrate_embeddings.py --group-id myproject

# الاستئناف من نقطة التوقف (إعادة التشغيل بعد الانقطاع)
uv run python tools/migrate_embeddings.py --resume
```

> **التوافق**: `bge-m3` بأبعاد 1024 أصليًا، ويقتطعه النظام تلقائيًا إلى 768 بُعدًا للتوافق مع فهرس المتجهات الحالي في Neo4j. يمكن للبيانات قبل وبعد الترحيل التعايش، لكن يُوصى بتنفيذ ترحيل كامل للحصول على أفضل جودة بحث.

## التوثيق

- [تعليمات استخدام الأدوات](../使用工具的指令.md) — دليل استخدام أدوات MCP وأفضل الممارسات
- [قواعد ذاكرة Graphiti](../graphiti-memory-rules.md) — شرح قواعد الذاكرة

## الترخيص

MIT License
