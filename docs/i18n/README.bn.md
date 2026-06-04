# Graphiti MCP Server

জ্ঞান গ্রাফ মেমরি সার্ভিস — একাধিক LLM প্রদানকারী (Ollama / GLM / GROQ / OpenRouter / DeepSeek) এবং Neo4j গ্রাফ ডেটাবেস সমন্বিত MCP সার্ভার।

[getzep/graphiti](https://github.com/getzep/graphiti) এর উপর ভিত্তি করে সম্প্রসারিতভাবে তৈরি, যা স্থানীয় Ollama এবং ক্লাউড LLM-এর মধ্যে নমনীয় স্যুইচিং সমর্থন করে, এবং স্বাধীনভাবে Embedding প্রদানকারী নির্দিষ্ট করতে পারে (LLM থেকে বিচ্ছিন্ন)।

## বৈশিষ্ট্যসমূহ

- **বুদ্ধিমান মেমরি ব্যবস্থাপনা** — জটিল মেমরি সম্পর্ক সংরক্ষণ ও পুনরুদ্ধার করতে জ্ঞান গ্রাফ ব্যবহার করে
- **শব্দার্থগত অনুসন্ধান** — ভেক্টর এম্বেডিং ভিত্তিক হাইব্রিড অনুসন্ধান (ভেক্টর + কীওয়ার্ড + গ্রাফ ট্রাভার্সাল)
- **১৬টি অনুসন্ধান কৌশল** — উন্নত অনুসন্ধান RRF, MMR, Cross-Encoder সহ বিভিন্ন পুনঃক্রমকরণ পদ্ধতি সমর্থন করে
- **একাধিক LLM প্রদানকারী** — Ollama (স্থানীয়), GLM (Zhipu AI বিনামূল্যে), GROQ (উচ্চগতির ইনফারেন্স), OpenRouter (বিভিন্ন মডেল একত্রিত করে), DeepSeek (Deep Seek) সমর্থন করে, পরিবেশ চলকের মাধ্যমে এক ক্লিকে স্যুইচ করা যায়
- **Embedding এবং LLM বিচ্ছিন্নকরণ** — `EMBEDDING_PROVIDER` ব্যবহার করে স্বাধীনভাবে এম্বেডার নির্দিষ্ট করা যায়, ক্লাউড LLM স্বয়ংক্রিয়ভাবে স্থানীয় `bge-m3`-এ ফিরে আসে
- **দ্বৈত মডেল বিভাজন** — Ollama মোডে জটিল কাজে প্রধান মডেল ব্যবহার করে, সহজ কাজে কর্মক্ষমতা বাড়াতে স্বয়ংক্রিয়ভাবে ছোট মডেলে স্যুইচ করে
- **বুদ্ধিমান বিষয়বস্তু বিভাজন** — দীর্ঘ পাঠ্য স্বয়ংক্রিয়ভাবে খণ্ডে প্রক্রিয়াকরণ করে, LLM লোড কমায় (থ্রেশহোল্ড কনফিগারযোগ্য)
- **পটভূমি মেমরি প্রক্রিয়াকরণ** — মেমরি যোগ পটভূমিতে চলতে পারে, MCP কল অবিলম্বে ফিরে আসে
- **মেমরি ডিডুপ্লিকেশন** — অত্যন্ত অনুরূপ বিদ্যমান মেমরি স্বয়ংক্রিয়ভাবে শনাক্ত করে, পুনরাবৃত্ত সংরক্ষণ এড়ায়
- **দ্বন্দ্ব শনাক্তকরণ** — দুটি সত্তার মধ্যে পরস্পরবিরোধী তথ্য শনাক্ত করে, অকার্যকর ও কার্যকর তথ্য চিহ্নিত করে
- **সম্প্রদায় শনাক্তকরণ** — Label Propagation অ্যালগরিদমের ভিত্তিতে স্বয়ংক্রিয়ভাবে সম্পর্কিত সত্তা ক্লাস্টার করে
- **গুরুত্ব ট্র্যাকিং** — সত্তা অ্যাক্সেস ফ্রিকোয়েন্সি স্বয়ংক্রিয়ভাবে রেকর্ড করে, অনুসন্ধান ফলাফল গুরুত্ব অনুসারে সাজায়
- **বুদ্ধিমান বিস্মৃতি** — পুরনো, কম-অ্যাক্সেসকৃত মেমরি শনাক্ত ও পরিষ্কার করে, গ্রাফকে সংক্ষিপ্ত রাখে
- **ব্যাচ আমদানি** — একবারে একাধিক মেমরি জমা দেয়, বৃহৎ পরিমাণ ডেটা মাইগ্রেশনের জন্য উপযুক্ত
- **কাঠামোগত ট্রিপলেট** — সরাসরি "বিষয়-সম্পর্ক-উদ্দেশ্য" যোগ করে, LLM নিষ্কাশন এড়িয়ে যায়, সেকেন্ডের মধ্যে সম্পন্ন
- **Web ব্যবস্থাপনা ইন্টারফেস** — অন্তর্নির্মিত ড্যাশবোর্ড, ব্রাউজিং, অনুসন্ধান, জ্ঞান গ্রাফ ভিজুয়ালাইজেশন, AI প্রশ্নোত্তর, সম্প্রদায় ব্রাউজিং
- **বহুভাষিক (i18n)** — প্রতিক্রিয়া বার্তা ৩০+ locale সমর্থন করে (zh-TW / en / zh-CN / ja / pt-BR / ko / es / de / fr ইত্যাদি সহ); MCP টুল `SERVER_LANG` অনুসারে, REST API HTTP `Accept-Language` অনুসারে স্বয়ংক্রিয়ভাবে সমঝোতা করে
- **গাঢ়/হালকা থিম** — Web ইন্টারফেস থিম স্যুইচিং সমর্থন করে
- **নিরাপদ মোড** — সত্তা নিষ্কাশন এড়িয়ে দ্রুত মেমরি যোগ করার বিকল্প
- **Docker সমর্থন** — অন্তর্নির্মিত Dockerfile, কন্টেইনারাইজড ডিপ্লয়মেন্ট সমর্থন করে
- **কনকারেন্সি নিরাপত্তা** — asyncio.Lock ইনিশিয়ালাইজেশন সুরক্ষিত করে, রেস কন্ডিশন প্রতিরোধ করে
- **স্তরীয় স্বাস্থ্য পরীক্ষা** — `/health` (liveness) + `/health/ready` (readiness)

## সিস্টেমের প্রয়োজনীয়তা

| আইটেম | প্রয়োজনীয়তা |
|------|------|
| Python | 3.10+ (3.11+ প্রস্তাবিত) |
| Neo4j | 4.0+ (`bolt://localhost:7687`) |
| LLM প্রদানকারী | Ollama / GLM / GROQ / OpenRouter / DeepSeek (পাঁচটির মধ্যে একটি) |
| Node.js | 18+ (শুধুমাত্র PM2 পটভূমি চালানোর জন্য, ঐচ্ছিক) |
| ডিস্ক স্পেস | ~3GB (Ollama মডেল + Neo4j ডেটা) |

### LLM প্রদানকারী নির্বাচন

`LLM_PROVIDER` পরিবেশ চলকের মাধ্যমে স্যুইচ করুন (`ollama` / `glm` / `groq` / `openrouter` / `deepseek`):

| প্রদানকারী | বৈশিষ্ট্য | LLM মডেল | Embedding | উপযুক্ত পরিস্থিতি |
|--------|------|----------|-----------|----------|
| **Ollama** (ডিফল্ট) | সম্পূর্ণ স্থানীয়, ডেটা মেশিন ছাড়ে না | `qwen2.5:3b` | `bge-m3` (চীনা + RAG চমৎকার) | GPU আছে, গোপনীয়তায় গুরুত্ব দেয় |
| **GLM** | বিনামূল্যে ক্লাউড, স্থিতিশীল ও সীমাহীন | `glm-4-flash` (বিনামূল্যে) | `embedding-3` | GPU নেই, অনুসন্ধান-নিবিড় পরিস্থিতি |
| **GROQ** | অতি উচ্চগতির ইনফারেন্স | `llama-3.3-70b-versatile` | Ollama `bge-m3`-এ ফিরে আসে | মাঝে মাঝে লেখা, গুণমান প্রত্যাশা |
| **OpenRouter** | বিভিন্ন মডেল একত্রিত করে, বিনামূল্যে কোটা সহ | `stepfun/step-3.5-flash:free` ইত্যাদি | Ollama `bge-m3`-এ ফিরে আসে | নির্দিষ্ট ক্লাউড মডেল ব্যবহার করতে চাই |
| **DeepSeek** | Deep Seek ক্লাউড, উচ্চ মূল্য-কার্যকারিতা | `deepseek-v4-flash` / `deepseek-v4-pro` | Ollama `bge-m3`-এ ফিরে আসে | চীনা বোঝাপড়া, কম খরচের ক্লাউড |

> **Embedding এবং LLM বিচ্ছিন্নকরণ**: এম্বেডার `EMBEDDING_PROVIDER` (`ollama` / `glm`) এর মাধ্যমে স্বাধীনভাবে নির্দিষ্ট করা হয়, সেট না করলে `LLM_PROVIDER` অনুসরণ করে। প্রকৃতপক্ষে শুধুমাত্র `glm` GLM `embedding-3` ব্যবহার করে, বাকি সব (GROQ / OpenRouter / DeepSeek ইত্যাদি Embedding না প্রদানকারী ক্লাউড LLM সহ) সর্বদা স্বয়ংক্রিয়ভাবে Ollama `bge-m3` ব্যবহার করে। **তাই যেকোনো ক্লাউড LLM ব্যবহার করার সময়, এম্বেডিং সার্ভিস প্রদানের জন্য এখনও স্থানীয় Ollama প্রয়োজন (যদি না embedding-ও glm হিসাবে সেট করা হয়)।**

#### Ollama মোড (স্থানীয়)

```bash
# LLM প্রধান মডেল (qwen2.5:3b প্রস্তাবিত, গতি এবং স্থিতিশীলতার সর্বোত্তম ভারসাম্য)
ollama pull qwen2.5:3b

# এম্বেডিং মডেল (আবশ্যক, ভেক্টর অনুসন্ধানের জন্য)
ollama pull bge-m3
```

> **মডেল নির্বাচনের সতর্কতা**:
> - `qwen2.5:3b` — প্রস্তাবিত, ~2s/call, ~100 t/s, graphiti-core কাঠামোগত আউটপুট ১০০% স্থিতিশীল
> - `qwen2.5:7b` — ভালো ফলাফল কিন্তু ৫-১০ গুণ ধীর, গুণমান প্রত্যাশার পরিস্থিতির জন্য উপযুক্ত
> - `qwen2.5:1.5b` — দ্রুততম কিন্তু **অস্থিতিশীল** (কাঠামোগত JSON সাফল্যের হার মাত্র ৩৩%), ব্যবহার করার পরামর্শ দেওয়া হয় না

#### GLM মোড (Zhipu AI ক্লাউড)

```bash
# .env সেটিং
LLM_PROVIDER=glm
GLM_API_KEY=your_api_key          # https://open.bigmodel.cn থেকে নিন
GLM_MODEL=glm-4-flash             # বিনামূল্যে মডেল
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768      # Neo4j ভেক্টর সূচকের মাত্রার সাথে সামঞ্জস্যপূর্ণ হতে হবে
```

> **GLM কর্মক্ষমতা রেফারেন্স**: লেখা ~22s (সংক্ষিপ্ত পাঠ্য), অনুসন্ধান ~0.34s, শূন্য Rate Limit ত্রুটি, স্থানীয় Ollama থেকে ২-৫ গুণ ধীর কিন্তু সম্পূর্ণ বিনামূল্যে।

#### GROQ মোড (উচ্চগতির ইনফারেন্স)

```bash
# .env সেটিং
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key         # https://console.groq.com থেকে নিন
GROQ_MODEL=llama-3.3-70b-versatile
```

> **লক্ষ্য করুন**: GROQ Embedding সার্ভিস প্রদান করে না, Ollama এম্বেডারের সাথে ব্যবহার করতে হবে (স্বয়ংক্রিয়ভাবে ফিরে আসে) অথবা `EMBEDDING_PROVIDER` glm-এ সেট করুন। GROQ-এর কঠোর Rate Limit আছে, উচ্চ ফ্রিকোয়েন্সি ব্যবহারে প্রচুর পুনঃচেষ্টা ট্রিগার হবে।

#### OpenRouter মোড (বিভিন্ন মডেল একত্রিতকরণ)

```bash
# .env সেটিং
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_api_key       # https://openrouter.ai/keys থেকে নিন
OPENROUTER_MODEL=stepfun/step-3.5-flash:free   # যেকোনো OpenRouter মডেলে পরিবর্তন করা যায়
```

> **লক্ষ্য করুন**: OpenRouter Embedding প্রদান করে না, স্বয়ংক্রিয়ভাবে Ollama `bge-m3`-এ ফিরে আসে। মডেল তালিকা https://openrouter.ai/models-এ দেখুন (একাধিক `:free` বিনামূল্যে মডেল সহ)।

#### DeepSeek মোড (Deep Seek)

```bash
# .env সেটিং
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key         # https://platform.deepseek.com থেকে নিন
DEEPSEEK_MODEL=deepseek-v4-flash      # প্রস্তাবিত; অথবা deepseek-v4-pro (ভালো ফলাফল)
```

> **লক্ষ্য করুন**: DeepSeek Embedding প্রদান করে না, স্বয়ংক্রিয়ভাবে Ollama `bge-m3`-এ ফিরে আসে। `deepseek-chat` / `deepseek-reasoner` 2026-07-24 তারিখে বন্ধ হবে, `deepseek-v4-flash` / `deepseek-v4-pro` ব্যবহারের পরামর্শ দেওয়া হয়। DeepSeek কঠোরভাবে `json_object` মোডের prompt-এ "json" স্ট্রিং থাকা আবশ্যক করে, ক্লায়েন্টে অন্তর্নির্মিত সুরক্ষা রয়েছে, অতিরিক্ত সেটিং প্রয়োজন নেই।

## দ্রুত শুরু

### 1. পূর্বপ্রস্তুতি

নিশ্চিত করুন Neo4j স্থানীয় মেশিনে চলছে, এবং নির্বাচিত LLM প্রদানকারী অনুসারে সংশ্লিষ্ট সার্ভিস প্রস্তুত করুন:

```bash
# Neo4j চলছে কিনা নিশ্চিত করুন (আবশ্যক)
neo4j status
# অথবা Docker ব্যবহার করুন: docker run -d -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/your_password neo4j:latest

# Ollama মোড: Ollama চলছে কিনা নিশ্চিত করুন
ollama list
# যদি শুরু না হয়: ollama serve

# GLM / GROQ মোড: শুধুমাত্র একটি বৈধ API Key প্রয়োজন, স্থানীয় সার্ভিস প্রয়োজন নেই
```

### 2. নির্ভরতা ইনস্টল

```bash
git clone <repo-url>
cd graphiti
uv sync
```

> **লক্ষ্য করুন**: এই প্রকল্প নির্ভরতা পরিচালনার জন্য [uv](https://github.com/astral-sh/uv) ব্যবহার করে। যদি ইনস্টল না থাকে: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 3. পরিবেশ কনফিগার

```bash
cp .env.example .env
```

`.env` সম্পাদনা করুন, **অন্তত** নিম্নলিখিত আইটেমগুলি পরিবর্তন করতে হবে:

```bash
NEO4J_PASSWORD=your_actual_password  # আবশ্যক: Neo4j পাসওয়ার্ড
LLM_PROVIDER=ollama                  # ollama / glm / groq / openrouter / deepseek
OLLAMA_MODEL=qwen2.5:3b              # Ollama মোড: স্থানীয় LLM মডেল
# GLM_API_KEY=your_key               # GLM মোড: Zhipu AI API Key
# GROQ_API_KEY=your_key              # GROQ মোড: GROQ API Key
# OPENROUTER_API_KEY=your_key        # OpenRouter মোড: API Key
# DEEPSEEK_API_KEY=your_key          # DeepSeek মোড: API Key
```

### 4. সার্ভিস শুরু

```bash
# HTTP মোড (প্রস্তাবিত, Web ব্যবস্থাপনা ইন্টারফেস সহ)
uv run python graphiti_mcp_server.py --transport http --port 8000

# অথবা PM2 পটভূমিতে চালান (দীর্ঘমেয়াদী চালানোর জন্য প্রস্তাবিত)
pm2 start ecosystem.config.cjs
```

### 5. সার্ভিস যাচাই

শুরু করার পরে নিম্নলিখিত এন্ডপয়েন্টগুলি অ্যাক্সেস করতে পারেন:

| এন্ডপয়েন্ট | বর্ণনা |
|------|------|
| http://localhost:8000/ | Web ব্যবস্থাপনা ইন্টারফেস |
| http://localhost:8000/mcp | MCP এন্ডপয়েন্ট (MCP ক্লায়েন্ট সংযোগের জন্য) |
| http://localhost:8000/health | স্বাস্থ্য পরীক্ষা (liveness) |
| http://localhost:8000/health/ready | গভীর পরীক্ষা (Neo4j সংযোগ সহ) |
| http://localhost:8000/api/stats | REST API পরিসংখ্যান |

## প্রকল্প কাঠামো

```
graphiti/
├── graphiti_mcp_server.py        # প্রধান প্রবেশপথ — MCP টুল সংজ্ঞা (19টি টুল)
├── src/
│   ├── config.py                 # কনফিগারেশন ব্যবস্থাপনা (GraphitiConfig, JSON/.env স্তরবিন্যাস সমর্থন)
│   ├── web_api.py                # Web ব্যবস্থাপনা ইন্টারফেস REST API (20+ এন্ডপয়েন্ট)
│   ├── ollama_graphiti_client.py  # Ollama LLM ক্লায়েন্ট (দ্বৈত মডেল বিভাজন)
│   ├── glm_client.py             # GLM (Zhipu AI) LLM ক্লায়েন্ট (OpenAI সামঞ্জস্যপূর্ণ API)
│   ├── openrouter_client.py      # OpenRouter LLM ক্লায়েন্ট (বিভিন্ন মডেল একত্রিতকরণ)
│   ├── deepseek_client.py        # DeepSeek LLM ক্লায়েন্ট (json_object + সুরক্ষামূলক json প্রতিরক্ষা)
│   ├── ollama_embedder.py        # Ollama এম্বেডিং মডেল অ্যাডাপ্টার
│   ├── content_preprocessor.py   # বুদ্ধিমান বিষয়বস্তু বিভাজন (দীর্ঘ পাঠ্য স্বয়ংক্রিয় খণ্ডন)
│   ├── deduplication.py          # মেমরি ডিডুপ্লিকেশন (কোসাইন সাদৃশ্য তুলনা)
│   ├── importance.py             # গুরুত্ব ট্র্যাকিং ও বুদ্ধিমান বিস্মৃতি
│   ├── safe_memory_add.py        # নিরাপদ মেমরি যোগ (সত্তা নিষ্কাশন এড়িয়ে যায়)
│   ├── timezone_utils.py         # টাইমজোন রূপান্তর (UTC→স্থানীয় টাইমজোন প্রদর্শন)
│   ├── i18n.py                   # ব্যাকএন্ড বহুভাষিক (REST Accept-Language অনুসারে, MCP SERVER_LANG অনুসারে)
│   ├── exceptions.py             # কাঠামোগত ব্যতিক্রম পরিচালনা (12 ধরনের ব্যতিক্রম শ্রেণি)
│   └── logging_setup.py          # লগ সিস্টেম (সময় রোটেশন + কর্মক্ষমতা পর্যবেক্ষণ)
├── web/                          # Web ব্যবস্থাপনা ইন্টারফেস ফ্রন্টএন্ড (SPA, build ছাড়া)
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js                # REST API র‍্যাপার
│       ├── components.js         # UI কম্পোনেন্ট রেন্ডারিং (সম্প্রদায় পৃষ্ঠা সহ)
│       └── app.js                # SPA রাউটিং, স্টেট ব্যবস্থাপনা
├── tests/                        # টেস্ট স্যুট (183টি টেস্ট)
│   ├── test_content_preprocessor.py  # বিভাজন লজিক টেস্ট (17টি)
│   ├── test_new_features.py      # নতুন বৈশিষ্ট্য টেস্ট (32টি)
│   ├── test_i18n.py             # বহুভাষিক টেস্ট (37টি)
│   ├── test_unit.py              # ইউনিট টেস্ট
│   ├── test_web_api.py           # Web API টেস্ট
│   ├── test_web_ui_features.py   # Web UI বৈশিষ্ট্য টেস্ট
│   ├── test_integration_manual.py # ম্যানুয়াল ইন্টিগ্রেশন টেস্ট
│   └── bench_deepseek_flash_vs_pro.py # DeepSeek flash/pro কর্মক্ষমতা বেঞ্চমার্ক স্ক্রিপ্ট
├── tools/                        # ডেভেলপমেন্ট ডায়াগনস্টিক টুল
│   ├── status_report.py          # সমন্বিত স্ট্যাটাস রিপোর্ট
│   ├── validate_config.py        # কনফিগারেশন যাচাই
│   ├── performance_diagnose.py   # কর্মক্ষমতা ডায়াগনস্টিক
│   ├── inspect_schema.py         # Neo4j কাঠামো পরীক্ষা
│   └── batch_reprocess.py        # ব্যাচ পুনঃপ্রক্রিয়াকরণ
├── docs/                         # ডকুমেন্টেশন
├── logs/                         # লগ (সময় রোটেশন, ডিফল্ট 30 দিন সংরক্ষণ)
├── Dockerfile                    # Docker কন্টেইনারাইজড ডিপ্লয়মেন্ট
└── ecosystem.config.cjs          # PM2 কনফিগারেশন
```

## MCP ক্লায়েন্ট সেটিং

### HTTP মোড (প্রস্তাবিত)

Claude Code, Cline ইত্যাদি HTTP সমর্থনকারী MCP ক্লায়েন্টের জন্য প্রযোজ্য:

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

### STDIO মোড

Claude Desktop ইত্যাদি সরাসরি প্রসেস শুরু করার প্রয়োজন হয় এমন ক্লায়েন্টের জন্য প্রযোজ্য:

**কনফিগারেশন ফাইলের অবস্থান:**
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

> **লক্ষ্য করুন**: SSE মোড (`--transport sse`) ব্যবহারের পরামর্শ দেওয়া হয় না। MCP 1.x-এ session ইনিশিয়ালাইজেশন সামঞ্জস্য সমস্যা রয়েছে, অনুগ্রহ করে HTTP মোড ব্যবহার করুন।

## MCP টুল (19টি)

### মেমরি ব্যবস্থাপনা (7টি)

| টুল | বর্ণনা |
|------|------|
| `add_memory_simple` | জ্ঞান গ্রাফে মেমরি যোগ করুন (পটভূমি প্রক্রিয়াকরণ, বুদ্ধিমান বিভাজন, ডিডুপ্লিকেশন পরীক্ষা সমর্থন করে) |
| `add_episode_bulk` | একাধিক মেমরি ব্যাচে যোগ করুন (ডিফল্ট পটভূমি প্রক্রিয়াকরণ) |
| `add_triplet` | কাঠামোগত ট্রিপলেট যোগ (LLM এড়িয়ে, সেকেন্ডের মধ্যে সম্পন্ন) |
| `search_memory_nodes` | মেমরি নোড অনুসন্ধান (16টি অনুসন্ধান কৌশল, সময় ফিল্টার সমর্থন করে) |
| `search_memory_facts` | মেমরি ফ্যাক্ট অনুসন্ধান (সম্পর্ক ধরন ফিল্টার, সময় পরিসীমা, বৈধতা ফিল্টার সমর্থন করে) |
| `advanced_search` | উন্নত অনুসন্ধান (16টি কৌশল, নোড+এজ+সম্প্রদায়+খণ্ড ফেরত দেয়) |
| `get_episodes` | সাম্প্রতিক মেমরি খণ্ড পান |

### জ্ঞান বিশ্লেষণ (3টি)

| টুল | বর্ণনা |
|------|------|
| `check_conflicts` | দুটি সত্তার মধ্যে তথ্য দ্বন্দ্ব শনাক্ত করুন (কার্যকর vs অকার্যকর) |
| `get_node_edges` | নোডের আগত ও বহির্গামী এজ সম্পর্ক অন্বেষণ করুন |
| `build_communities` | সম্প্রদায় শনাক্তকরণ ও ক্লাস্টারিং ট্রিগার করুন (ডিফল্ট পটভূমি প্রক্রিয়াকরণ) |

### মেমরি রক্ষণাবেক্ষণ (2টি)

| টুল | বর্ণনা |
|------|------|
| `get_stale_memories` | পুরনো, কম-অ্যাক্সেসকৃত মেমরি অনুসন্ধান করুন |
| `cleanup_stale_memories` | পুরনো মেমরি পরিষ্কার করুন (ডিফল্ট dry_run প্রিভিউ মোড) |

### টাস্ক ব্যবস্থাপনা

| টুল | বর্ণনা |
|------|------|
| `get_memory_task_status` | পটভূমি মেমরি প্রক্রিয়াকরণ টাস্কের অগ্রগতি ও ফলাফল অনুসন্ধান করুন |

### মুছে ফেলা ও অনুসন্ধান

| টুল | বর্ণনা |
|------|------|
| `delete_episode` | মেমরি খণ্ড মুছুন |
| `delete_entity_edge` | সত্তা এজ (সম্পর্ক) মুছুন |
| `get_entity_edge` | সত্তা এজের বিস্তারিত তথ্য পান |

### সিস্টেম ব্যবস্থাপনা

| টুল | বর্ণনা |
|------|------|
| `get_status` | সার্ভিস স্ট্যাটাস পান (Neo4j, LLM, এম্বেডার) |
| `test_connection` | Neo4j / LLM / এম্বেডার সংযোগ পরীক্ষা করুন |
| `clear_graph` | গ্রাফ ডেটাবেস পরিষ্কার করুন (group_id অনুসারে পরিষ্কার সমর্থন করে) |

## টুল প্যারামিটার

### add_memory_simple

| প্যারামিটার | ধরন | আবশ্যক | ডিফল্ট মান | বর্ণনা |
|------|------|------|--------|------|
| `name` | string | Y | | মেমরির নাম |
| `episode_body` | string | Y | | মেমরির বিষয়বস্তু (800 অক্ষরের বেশি হলে স্বয়ংক্রিয়ভাবে বিভাজন) |
| `group_id` | string | | `"default"` | গ্রুপিং ID (প্রকল্প অনুসারে বিচ্ছিন্ন করার পরামর্শ) |
| `source` | string | | `"text"` | উৎসের ধরন: `text` / `json` / `message` |
| `source_description` | string | | `"MCP Server"` | উৎসের বর্ণনা |
| `use_safe_mode` | bool | | `false` | নিরাপদ মোড (সত্তা নিষ্কাশন এড়িয়ে যায়, দ্রুত কিন্তু মেমরি অনুসন্ধানযোগ্য নয়) |
| `background` | bool | | `false` | পটভূমি প্রক্রিয়াকরণ (অবিলম্বে task_id ফেরত দেয়, দীর্ঘ পাঠ্যের জন্য উপযুক্ত) |
| `force` | bool | | `false` | ডিডুপ্লিকেশন পরীক্ষা এড়িয়ে যায় (জোরপূর্বক যোগ) |
| `excluded_entity_types` | list | | | বাদ দেওয়া সত্তার ধরন (অপ্রয়োজনীয় নিষ্কাশন পরিমাণ কমায়) |

> **কর্মক্ষমতা টিপস**:
> - সংক্ষিপ্ত পাঠ্য (<800 অক্ষর): সরাসরি প্রক্রিয়াকরণ, সাধারণত 30-40 সেকেন্ডে সম্পন্ন
> - দীর্ঘ পাঠ্য (>800 অক্ষর): স্বয়ংক্রিয়ভাবে একাধিক খণ্ডে বিভক্ত, `add_episode_bulk` ব্যবহার করে সমান্তরাল প্রক্রিয়াকরণ (ক্রমিকের চেয়ে ~33% দ্রুত)
> - `background=true` ব্যবহার করে MCP কল ব্লকিং এড়ানো যায়, `get_memory_task_status` এর মাধ্যমে অগ্রগতি ট্র্যাক করুন
> - `use_safe_mode=true` সেকেন্ডে সম্পন্ন হয় কিন্তু মেমরি search টুল দ্বারা খুঁজে পাওয়া যায় না
> - ডিডুপ্লিকেশন সক্রিয় থাকলে, অত্যন্ত অনুরূপ মেমরি সম্পর্কে সতর্ক করা হবে (`force=true` এড়িয়ে যেতে পারে)

### add_episode_bulk

| প্যারামিটার | ধরন | আবশ্যক | ডিফল্ট মান | বর্ণনা |
|------|------|------|--------|------|
| `episodes` | list | Y | | মেমরি তালিকা, প্রতিটি আইটেমে `name` এবং `content` থাকে |
| `group_id` | string | | `"default"` | গ্রুপিং ID |
| `source` | string | | `"text"` | উৎসের ধরন |
| `background` | bool | | `true` | পটভূমি প্রক্রিয়াকরণ (ব্যাচ সাধারণত সময়সাপেক্ষ) |

### add_triplet

| প্যারামিটার | ধরন | আবশ্যক | ডিফল্ট মান | বর্ণনা |
|------|------|------|--------|------|
| `source_name` | string | Y | | উৎস সত্তার নাম (যেমন "Alice") |
| `target_name` | string | Y | | লক্ষ্য সত্তার নাম (যেমন "Google") |
| `relation_name` | string | Y | | সম্পর্কের নাম (যেমন "works_at") |
| `fact` | string | Y | | তথ্য বর্ণনা (যেমন "Alice works at Google") |
| `group_id` | string | | `"default"` | গ্রুপিং ID |
| `source_labels` | list | | | উৎস সত্তার লেবেল |
| `target_labels` | list | | | লক্ষ্য সত্তার লেবেল |

### search_memory_nodes

| প্যারামিটার | ধরন | আবশ্যক | ডিফল্ট মান | বর্ণনা |
|------|------|------|--------|------|
| `query` | string | Y | | অনুসন্ধান কীওয়ার্ড (প্রাকৃতিক ভাষা) |
| `max_nodes` | int | | `10` | সর্বাধিক ফেরত সংখ্যা |
| `group_ids` | list | | | গ্রুপিং ফিল্টার (একাধিক group যৌথ অনুসন্ধান) |
| `entity_types` | list | | | সত্তার ধরন ফিল্টার |
| `search_recipe` | string | | | অনুসন্ধান কৌশল (উন্নত অনুসন্ধান দেখুন) |
| `created_after` | string | | | তৈরির সময় সর্বনিম্ন সীমা (ISO datetime) |
| `created_before` | string | | | তৈরির সময় সর্বোচ্চ সীমা (ISO datetime) |

### search_memory_facts

| প্যারামিটার | ধরন | আবশ্যক | ডিফল্ট মান | বর্ণনা |
|------|------|------|--------|------|
| `query` | string | Y | | অনুসন্ধান কীওয়ার্ড |
| `max_facts` | int | | `10` | সর্বাধিক ফেরত সংখ্যা |
| `group_ids` | list | | | গ্রুপিং ফিল্টার |
| `center_node_uuid` | string | | | কেন্দ্রীয় নোড UUID (নির্দিষ্ট নোডের সম্পর্ক অন্বেষণ) |
| `edge_types` | list | | | সম্পর্ক ধরন ফিল্টার (যেমন `["works_at"]`) |
| `created_after` | string | | | তৈরির সময় সর্বনিম্ন সীমা (ISO datetime) |
| `created_before` | string | | | তৈরির সময় সর্বোচ্চ সীমা (ISO datetime) |
| `only_valid` | bool | | `false` | শুধুমাত্র অকার্যকর হয়নি এমন তথ্য ফেরত দেয় |

### advanced_search

| প্যারামিটার | ধরন | আবশ্যক | ডিফল্ট মান | বর্ণনা |
|------|------|------|--------|------|
| `query` | string | Y | | অনুসন্ধান কীওয়ার্ড |
| `search_recipe` | string | | `"combined_rrf"` | অনুসন্ধান কৌশল (16টি নির্বাচনযোগ্য) |
| `max_results` | int | | `10` | সর্বাধিক ফেরত সংখ্যা |
| `group_ids` | list | | | গ্রুপিং ফিল্টার |
| `center_node_uuid` | string | | | কেন্দ্রীয় নোড UUID |

**উপলব্ধ অনুসন্ধান কৌশল (search_recipe):**

| শ্রেণি | কৌশল | বর্ণনা |
|------|------|------|
| সমন্বিত | `combined_rrf` | সমন্বিত RRF ফিউশন (ডিফল্ট, প্রস্তাবিত) |
| সমন্বিত | `combined_mmr` | সমন্বিত MMR বৈচিত্র্য পুনঃক্রম |
| সমন্বিত | `combined_cross_encoder` | সমন্বিত Cross-Encoder সূক্ষ্ম ক্রম |
| এজ | `edge_rrf` / `edge_mmr` / `edge_cross_encoder` | এজ অনুসন্ধান (3 ধরনের ক্রম) |
| এজ | `edge_node_distance` / `edge_episode_mentions` | এজ অনুসন্ধান (গ্রাফ দূরত্ব/উল্লেখ সংখ্যা) |
| নোড | `node_rrf` / `node_mmr` / `node_cross_encoder` | নোড অনুসন্ধান (3 ধরনের ক্রম) |
| নোড | `node_node_distance` / `node_episode_mentions` | নোড অনুসন্ধান (গ্রাফ দূরত্ব/উল্লেখ সংখ্যা) |
| সম্প্রদায় | `community_rrf` / `community_mmr` / `community_cross_encoder` | সম্প্রদায় অনুসন্ধান |

### check_conflicts

| প্যারামিটার | ধরন | আবশ্যক | ডিফল্ট মান | বর্ণনা |
|------|------|------|--------|------|
| `source_name` | string | Y | | উৎস সত্তার নাম |
| `target_name` | string | Y | | লক্ষ্য সত্তার নাম |
| `group_id` | string | | `"default"` | গ্রুপিং ID |

### get_node_edges

| প্যারামিটার | ধরন | আবশ্যক | ডিফল্ট মান | বর্ণনা |
|------|------|------|--------|------|
| `node_uuid` | string | Y | | নোড UUID |
| `include_inbound` | bool | | `true` | আগত এজ অন্তর্ভুক্ত |
| `include_outbound` | bool | | `true` | বহির্গামী এজ অন্তর্ভুক্ত |
| `max_edges` | int | | `50` | সর্বাধিক ফেরত সংখ্যা |

### build_communities

| প্যারামিটার | ধরন | আবশ্যক | ডিফল্ট মান | বর্ণনা |
|------|------|------|--------|------|
| `group_ids` | list | | | নির্দিষ্ট গ্রুপিং (খালি রাখলে সব) |
| `background` | bool | | `true` | পটভূমি প্রক্রিয়াকরণ |

### get_stale_memories

| প্যারামিটার | ধরন | আবশ্যক | ডিফল্ট মান | বর্ণনা |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | কত দিন অ্যাক্সেস না হলে পুরনো হিসাবে গণ্য |
| `min_access_count` | int | | `2` | অ্যাক্সেস সংখ্যা এই মানের নিচে হলেই অন্তর্ভুক্ত |
| `group_id` | string | | | গ্রুপিং ফিল্টার |
| `limit` | int | | `50` | সর্বাধিক ফেরত সংখ্যা |

### cleanup_stale_memories

| প্যারামিটার | ধরন | আবশ্যক | ডিফল্ট মান | বর্ণনা |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | পুরনো দিনের থ্রেশহোল্ড |
| `min_access_count` | int | | `2` | সর্বনিম্ন অ্যাক্সেস সংখ্যা থ্রেশহোল্ড |
| `group_id` | string | | | গ্রুপিং ফিল্টার |
| `dry_run` | bool | | `true` | প্রিভিউ মোড (প্রকৃতপক্ষে মুছে ফেলে না) |
| `limit` | int | | `50` | সর্বাধিক প্রক্রিয়াকরণ সংখ্যা |

### get_memory_task_status

| প্যারামিটার | ধরন | আবশ্যক | বর্ণনা |
|------|------|------|------|
| `task_id` | string | Y | পটভূমি টাস্ক ID (`add_memory_simple(background=true)` দ্বারা ফেরত) |

## Web ব্যবস্থাপনা ইন্টারফেস

HTTP মোডে `http://localhost:8000/` অ্যাক্সেস করেই ব্যবহার করা যায়।

**বৈশিষ্ট্য:**
- ড্যাশবোর্ড — নোড সংখ্যা, ফ্যাক্ট সংখ্যা, মেমরি খণ্ড সংখ্যা পরিসংখ্যান
- সত্তা নোড — ব্রাউজিং, ফিল্টারিং, ভেক্টর অনুসন্ধান
- ফ্যাক্ট সম্পর্ক — ব্রাউজিং, ফিল্টারিং, ভেক্টর অনুসন্ধান
- মেমরি খণ্ড — ব্রাউজিং, পূর্ণ-পাঠ্য অনুসন্ধান, মুছে ফেলা
- সম্প্রদায় ব্রাউজিং — সম্প্রদায় নোড তালিকা, সারাংশ, সম্প্রদায় নির্মাণ ট্রিগার
- ট্রিপলেট ফর্ম — সরাসরি "বিষয়-সম্পর্ক-উদ্দেশ্য" কাঠামোগত জ্ঞান যোগ
- Group ব্যবস্থাপনা — গ্রুপিং অনুসারে ফিল্টার, ব্যাচ মুছে ফেলা
- জ্ঞান গ্রাফ ভিজুয়ালাইজেশন — নোড সম্পর্ক গ্রাফিকাল প্রদর্শন
- AI প্রশ্নোত্তর — জ্ঞান গ্রাফ ভিত্তিক বুদ্ধিমান প্রশ্নোত্তর
- গুণমান বিশ্লেষণ — মেমরি গুণমান ও কভারেজ বিশ্লেষণ
- থিম স্যুইচিং — গাঢ়/হালকা থিম

**REST API:**

| এন্ডপয়েন্ট | পদ্ধতি | বর্ণনা |
|------|------|------|
| `/api/stats` | GET | ড্যাশবোর্ড পরিসংখ্যান |
| `/api/groups` | GET | সমস্ত group_id পান |
| `/api/nodes` | GET | সত্তা নোড ব্রাউজ (পেজিনেশন) |
| `/api/facts` | GET | ফ্যাক্ট ব্রাউজ (পেজিনেশন) |
| `/api/episodes` | GET | মেমরি খণ্ড ব্রাউজ (পেজিনেশন) |
| `/api/search/nodes` | GET | ভেক্টর অনুসন্ধান নোড |
| `/api/search/facts` | GET | ভেক্টর অনুসন্ধান ফ্যাক্ট |
| `/api/search/advanced` | GET | উন্নত অনুসন্ধান (16টি কৌশল) |
| `/api/communities` | GET | সম্প্রদায় নোড ব্রাউজ (পেজিনেশন) |
| `/api/communities/build` | POST | সম্প্রদায় নির্মাণ ট্রিগার |
| `/api/memory/add-bulk` | POST | ব্যাচ মেমরি যোগ |
| `/api/memory/add-triplet` | POST | ট্রিপলেট যোগ |
| `/api/memory/tasks` | GET | পটভূমি টাস্ক তালিকাভুক্ত করুন (স্ট্যাটাস ফিল্টার সমর্থন করে) |
| `/api/memory/tasks/{id}` | GET | একক টাস্ক স্ট্যাটাস অনুসন্ধান |
| `/api/analytics/stale` | GET | পুরনো মেমরি অনুসন্ধান |
| `/api/analytics/cleanup` | POST | পুরনো মেমরি পরিষ্কার |
| `/api/nodes/{uuid}` | DELETE | নোড মুছুন |
| `/api/episodes/{uuid}` | DELETE | মেমরি খণ্ড মুছুন |
| `/api/facts/{uuid}` | DELETE | ফ্যাক্ট মুছুন |
| `/api/groups/{group_id}` | DELETE | সম্পূর্ণ group মুছুন |

## কনফিগারেশন

### পরিবেশ চলক (.env)

কনফিগারেশন স্তরবিন্যাস প্রক্রিয়া ব্যবহার করে: JSON কনফিগারেশন ফাইল ভিত্তি হিসাবে, পরিবেশ চলক পৃথক মান ওভাররাইড করে।

```bash
# === আবশ্যক ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password        # পরিবর্তন করতে হবে

# === LLM প্রদানকারী নির্বাচন ===
LLM_PROVIDER=ollama                 # ollama / glm / groq / openrouter / deepseek

# === Embedding প্রদানকারী (ঐচ্ছিক, ডিফল্ট LLM_PROVIDER অনুসরণ করে) ===
# শুধুমাত্র glm GLM Embedding ব্যবহার করে, বাকি সব Ollama bge-m3 ব্যবহার করে
# EMBEDDING_PROVIDER=ollama         # ollama / glm

# === Ollama কনফিগারেশন (LLM_PROVIDER=ollama হলে ব্যবহৃত) ===
OLLAMA_MODEL=qwen2.5:3b             # প্রধান মডেল (qwen2.5:3b প্রস্তাবিত)
OLLAMA_SMALL_MODEL=qwen2.5:3b       # ছোট মডেল (সহজ কাজের জন্য, ভিন্ন মডেল বেছে নেওয়া যায়)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.1

# === GLM কনফিগারেশন (LLM_PROVIDER=glm হলে ব্যবহৃত) ===
GLM_API_KEY=your_api_key            # https://open.bigmodel.cn থেকে নিন
GLM_MODEL=glm-4-flash               # বিনামূল্যে মডেল
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768

# === GROQ কনফিগারেশন (LLM_PROVIDER=groq হলে ব্যবহৃত) ===
GROQ_API_KEY=your_api_key           # https://console.groq.com থেকে নিন
GROQ_MODEL=llama-3.3-70b-versatile

# === OpenRouter কনফিগারেশন (LLM_PROVIDER=openrouter হলে ব্যবহৃত) ===
OPENROUTER_API_KEY=your_api_key     # https://openrouter.ai/keys থেকে নিন
OPENROUTER_MODEL=stepfun/step-3.5-flash:free

# === DeepSeek কনফিগারেশন (LLM_PROVIDER=deepseek হলে ব্যবহৃত) ===
DEEPSEEK_API_KEY=your_api_key       # https://platform.deepseek.com থেকে নিন
DEEPSEEK_MODEL=deepseek-v4-flash    # অথবা deepseek-v4-pro

# === Ollama এম্বেডিং মডেল (glm এম্বেডিং ছাড়া সর্বত্র ব্যবহৃত) ===
OLLAMA_EMBEDDING_MODEL=bge-m3
OLLAMA_EMBEDDING_DIMENSIONS=768

# === প্রদর্শন ও ভাষা (ঐচ্ছিক) ===
GRAPHITI_DISPLAY_TIMEZONE=Asia/Taipei # API ফেরত টাইমস্ট্যাম্প প্রদর্শন টাইমজোন (IANA নাম; সংরক্ষণ UTC বজায় রাখে)
SERVER_LANG=zh-TW                     # MCP টুল প্রতিক্রিয়া ভাষা (সম্পূর্ণ locale src/i18n.py-তে দেখুন); REST API Accept-Language অনুসারে

# === মেমরি কর্মক্ষমতা (ঐচ্ছিক) ===
GRAPHITI_CHUNK_THRESHOLD=800         # বুদ্ধিমান বিভাজন ট্রিগার করার অক্ষর সংখ্যা থ্রেশহোল্ড
GRAPHITI_MAX_CHUNK_SIZE=600          # প্রতি খণ্ডের সর্বোচ্চ অক্ষর সংখ্যা
GRAPHITI_MAX_COROUTINES=10            # সর্বাধিক সমান্তরাল করুটিন সংখ্যা
GRAPHITI_DEFAULT_BACKGROUND=false    # ডিফল্ট পটভূমি প্রক্রিয়াকরণ কিনা

# === গুরুত্ব ট্র্যাকিং ও বুদ্ধিমান বিস্মৃতি (ঐচ্ছিক) ===
ENABLE_IMPORTANCE_TRACKING=true      # অ্যাক্সেস ট্র্যাকিং সক্রিয় করুন
IMPORTANCE_WEIGHT=0.1                # গুরুত্ব ওজন
STALE_DAYS_THRESHOLD=30              # পুরনো দিনের থ্রেশহোল্ড
STALE_MIN_ACCESS_COUNT=2             # সর্বনিম্ন অ্যাক্সেস সংখ্যা

# === লগ ===
LOG_FILE=logs/graphiti_mcp_server.log
LOG_LEVEL=INFO
```

> **সম্পূর্ণ পরিবেশ চলক তালিকা** `.env.example`-এ দেখুন

### JSON কনফিগারেশন ফাইল

ভার্সন কন্ট্রোলের প্রয়োজন এমন কনফিগারেশনের জন্য প্রযোজ্য (পরিবেশ চলক এখনও ওভাররাইড করতে পারে):

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

## PM2 পটভূমিতে চালানো

```bash
npm install -g pm2

pm2 start ecosystem.config.cjs      # শুরু
pm2 status                           # স্ট্যাটাস
pm2 logs graphiti-mcp-http           # রিয়েল-টাইম লগ
pm2 restart graphiti-mcp-http --update-env  # পুনরায় শুরু (.env পুনরায় লোড)

pm2 save && pm2 startup              # বুট-টাইম স্বয়ংক্রিয় শুরু সেট করুন
```

> **টিপস**: `.env` পরিবর্তন করার পর অবশ্যই `--update-env` ফ্ল্যাগ ব্যবহার করে পুনরায় শুরু করতে হবে, অন্যথায় পরিবেশ চলক আপডেট হবে না।

## Docker ডিপ্লয়মেন্ট

```bash
docker build -t graphiti-mcp .

# লক্ষ্য করুন: Docker কন্টেইনারের Neo4j এবং Ollama-এর সাথে সংযোগ করতে সক্ষম হতে হবে
# host network ব্যবহার করা সবচেয়ে সহজ
docker run -p 8000:8000 --env-file .env --network host graphiti-mcp

# অথবা স্পষ্টভাবে বহিরাগত সার্ভিস ঠিকানা নির্দিষ্ট করুন
docker run -p 8000:8000 \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --env-file .env graphiti-mcp
```

## টেস্টিং

```bash
# সমস্ত টেস্ট চালান (183টি, প্রায় 1 সেকেন্ড)
uv run python -m pytest tests/

# বিস্তারিত আউটপুট
uv run python -m pytest tests/ -v

# শুধুমাত্র নির্দিষ্ট টেস্ট চালান
uv run python -m pytest tests/test_content_preprocessor.py -v
uv run python -m pytest tests/test_new_features.py -v
uv run python -m pytest tests/test_unit.py -v
```

> **লক্ষ্য করুন**: `test_integration_manual.py`-এর 3টি async টেস্টের জন্য `pytest-asyncio` ইনস্টল করতে হবে, অনুপস্থিত থাকলে Failed দেখাবে কিন্তু অন্যান্য টেস্টে প্রভাব ফেলবে না। `bench_deepseek_flash_vs_pro.py` একটি কর্মক্ষমতা বেঞ্চমার্ক স্ক্রিপ্ট, ইউনিট টেস্ট নয়।

## সমস্যা সমাধান

### Neo4j সংযোগ ব্যর্থ

```bash
neo4j status                              # সার্ভিস স্ট্যাটাস পরীক্ষা করুন
cypher-shell -u neo4j -p your_password    # পাসওয়ার্ড সঠিক কিনা নিশ্চিত করুন
curl http://localhost:7474                 # HTTP পোর্ট নিশ্চিত করুন
```

সাধারণ কারণ:
- Neo4j শুরু হয়নি
- পাসওয়ার্ড ভুল (`.env`-এর `NEO4J_PASSWORD`)
- পোর্ট দখলকৃত বা ফায়ারওয়াল দ্বারা অবরুদ্ধ

### LLM সংযোগ ব্যর্থ

**Ollama মোড:**
```bash
ollama serve                # Ollama সার্ভিস শুরু করুন
ollama list                 # ইনস্টল করা মডেল পরীক্ষা করুন
ollama pull qwen2.5:3b      # অনুপস্থিত মডেল ইনস্টল করুন
```

সাধারণ কারণ: Ollama শুরু হয়নি, মডেল ইনস্টল হয়নি, GPU মেমরি অপর্যাপ্ত

**GLM মোড:**
- `GLM_API_KEY` সঠিক কিনা নিশ্চিত করুন
- `GLM_EMBEDDING_DIMENSIONS=768` নিশ্চিত করুন (Neo4j ভেক্টর সূচকের সাথে সামঞ্জস্যপূর্ণ হতে হবে)
- GLM API এন্ডপয়েন্ট: `https://open.bigmodel.cn/api/paas/v4/`

**GROQ মোড:**
- `GROQ_API_KEY` সঠিক কিনা নিশ্চিত করুন
- Rate Limit ঘন ঘন হলে GLM মোডে স্যুইচ করার কথা বিবেচনা করুন
- GROQ Embedding প্রদান করে না, Ollama এম্বেডার উপলব্ধ কিনা নিশ্চিত করুন

**OpenRouter মোড:**
- `OPENROUTER_API_KEY` সঠিক কিনা, `OPENROUTER_MODEL` বৈধ মডেল ID কিনা নিশ্চিত করুন (https://openrouter.ai/models দেখুন)
- Embedding প্রদান করে না, Ollama এম্বেডার উপলব্ধ কিনা নিশ্চিত করুন

**DeepSeek মোড:**
- `DEEPSEEK_API_KEY` সঠিক কিনা নিশ্চিত করুন
- যদি `Prompt must contain the word 'json'` দেখা যায়: এটি DeepSeek `json_object` মোডের কঠোর প্রয়োজনীয়তা, ক্লায়েন্টে অন্তর্নির্মিত সুরক্ষা রয়েছে; যদি এখনও দেখা যায়, নিশ্চিত করুন আপনি সর্বশেষ সংস্করণের `src/deepseek_client.py` ব্যবহার করছেন এবং সার্ভিস পুনরায় শুরু করুন
- Embedding প্রদান করে না, Ollama এম্বেডার উপলব্ধ কিনা নিশ্চিত করুন

### MCP সংযোগ ত্রুটি

যদি `Invalid request parameters` বা `Received request before initialization was complete` দেখা যায়:

1. HTTP ট্রান্সপোর্ট মোড ব্যবহার নিশ্চিত করুন (**SSE ব্যবহার করবেন না**)
2. ক্লায়েন্ট `"type": "http"`, `"url": "http://localhost:8000/mcp"` সেট করা নিশ্চিত করুন
3. সার্ভিস পুনরায় শুরু করুন: `pm2 restart graphiti-mcp-http --update-env`
4. Claude Code-এ `/mcp` চালিয়ে পুনরায় সংযোগ করুন

### মেমরি যোগের গতি ধীর

- **Ollama**: মডেলের আকার পরীক্ষা করুন (`qwen2.5:3b` `7b`-এর চেয়ে 5-10 গুণ দ্রুত), GPU ব্যবহার নিশ্চিত করুন (`ollama ps`)
- **GLM**: প্রতিটি add_episode-এর জন্য 10-20+ বার LLM নেটওয়ার্ক রাউন্ড-ট্রিপ প্রয়োজন, সংক্ষিপ্ত পাঠ্যে ~22s স্বাভাবিক মান
- **GROQ**: Rate Limit প্রচুর পুনঃচেষ্টার কারণ হয়, ঘন ঘন ব্যবহার করলে GLM বা Ollama-তে স্যুইচ করার পরামর্শ দেওয়া হয়
- `background=true` ব্যবহার করে ব্লকিং এড়ান
- `GRAPHITI_CHUNK_THRESHOLD` কমিয়ে দীর্ঘ পাঠ্য আগে বিভাজন করুন

### PM2 সমস্যা

```bash
pm2 status                                        # স্ট্যাটাস পরীক্ষা করুন
pm2 logs graphiti-mcp-http --err --lines 50        # ত্রুটি লগ
lsof -i :8000                                     # পোর্ট দখল পরীক্ষা করুন
pm2 delete graphiti-mcp-http && pm2 start ecosystem.config.cjs  # সম্পূর্ণ পুনরায় শুরু
```

## ডেভেলপমেন্ট ডায়াগনস্টিক টুল

```bash
uv run python tools/status_report.py           # সমন্বিত স্ট্যাটাস রিপোর্ট (Neo4j + Ollama + কনফিগারেশন)
uv run python tools/validate_config.py         # .env এবং কনফিগারেশন সম্পূর্ণতা যাচাই
uv run python tools/performance_diagnose.py    # LLM কর্মক্ষমতা ডায়াগনস্টিক
uv run python tools/inspect_schema.py          # Neo4j সূচক ও সীমাবদ্ধতা পরীক্ষা
uv run python tools/migrate_embeddings.py      # Embedding মডেল মাইগ্রেশন (মডেল স্যুইচের পর ভেক্টর পুনর্গঠন)
```

### Embedding মডেল মাইগ্রেশন

embedding মডেল স্যুইচ করার পর (যেমন `nomic-embed-text` → `bge-m3`), মাইগ্রেশন টুল ব্যবহার করে সমস্ত বিদ্যমান ভেক্টর পুনর্গঠন করা যায়, যাতে অনুসন্ধান গুণমান সামঞ্জস্যপূর্ণ থাকে:

```bash
# মাইগ্রেশনের প্রয়োজন এমন সংখ্যা প্রিভিউ করুন
uv run python tools/migrate_embeddings.py --dry-run

# সম্পূর্ণ মাইগ্রেশন (চেকপয়েন্ট রিজিউম সমর্থন করে)
uv run python tools/migrate_embeddings.py

# শুধুমাত্র নির্দিষ্ট group মাইগ্রেট করুন
uv run python tools/migrate_embeddings.py --group-id myproject

# চেকপয়েন্ট থেকে চালিয়ে যান (বাধার পর পুনরায় চালান)
uv run python tools/migrate_embeddings.py --resume
```

> **সামঞ্জস্য**: `bge-m3` মূলত 1024 মাত্রার, সিস্টেম স্বয়ংক্রিয়ভাবে বিদ্যমান Neo4j ভেক্টর সূচকের সাথে সামঞ্জস্যের জন্য 768 মাত্রায় ছাঁটাই করে। মাইগ্রেশনের আগে ও পরের ডেটা সহাবস্থান করতে পারে, তবে সর্বোত্তম অনুসন্ধান গুণমানের জন্য সম্পূর্ণ মাইগ্রেশন চালানোর পরামর্শ দেওয়া হয়।

## ডকুমেন্টেশন

- [টুল ব্যবহারের নির্দেশনা](../使用工具的指令.md) — MCP টুল ব্যবহারের গাইড ও সর্বোত্তম অনুশীলন
- [Graphiti Memory Rules](../graphiti-memory-rules.md) — মেমরি নিয়ম ব্যাখ্যা

## লাইসেন্স

MIT License
