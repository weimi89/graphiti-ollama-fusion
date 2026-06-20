# Graphiti MCP Server

ज्ञान ग्राफ मेमोरी सेवा — कई LLM प्रदाताओं (Ollama / GLM / GROQ / OpenRouter / DeepSeek) और Neo4j ग्राफ डेटाबेस को एकीकृत करने वाला MCP सर्वर।

[getzep/graphiti](https://github.com/getzep/graphiti) के आधार पर विस्तारित और विकसित, स्थानीय Ollama और क्लाउड LLM के बीच लचीले स्विचिंग का समर्थन करता है, और Embedding प्रदाता को स्वतंत्र रूप से निर्दिष्ट किया जा सकता है (LLM से विसंयुग्मित)।

## विशेषताएँ

- **बुद्धिमान मेमोरी प्रबंधन** — जटिल मेमोरी संबंधों को संग्रहीत और पुनः प्राप्त करने के लिए ज्ञान ग्राफ का उपयोग करता है
- **अर्थपूर्ण खोज** — वेक्टर एम्बेडिंग पर आधारित हाइब्रिड खोज (वेक्टर + कीवर्ड + ग्राफ ट्रैवर्सल)
- **16 खोज रणनीतियाँ** — उन्नत खोज RRF, MMR, Cross-Encoder आदि कई पुनर्रैंकिंग विधियों का समर्थन करती है
- **कई LLM प्रदाता** — Ollama (स्थानीय), GLM (Zhipu AI मुफ़्त), GROQ (उच्च गति अनुमान), OpenRouter (विभिन्न मॉडलों का एकत्रीकरण), DeepSeek का समर्थन करता है, पर्यावरण चर के माध्यम से एक-क्लिक स्विचिंग
- **Embedding और LLM का विसंयुग्मन** — `EMBEDDING_PROVIDER` के साथ एम्बेडर को स्वतंत्र रूप से निर्दिष्ट किया जा सकता है, क्लाउड LLM स्वचालित रूप से स्थानीय `bge-m3` पर वापस आ जाता है
- **दोहरा मॉडल वितरण** — Ollama मोड में जटिल कार्य मुख्य मॉडल का उपयोग करते हैं, सरल कार्य प्रदर्शन सुधारने के लिए स्वचालित रूप से छोटे मॉडल पर स्विच हो जाते हैं
- **बुद्धिमान सामग्री विभाजन** — लंबे टेक्स्ट को स्वचालित रूप से खंडों में संसाधित किया जाता है, LLM लोड को कम करता है (कॉन्फ़िगर करने योग्य सीमा)
- **पृष्ठभूमि मेमोरी प्रसंस्करण** — मेमोरी जोड़ना पृष्ठभूमि में निष्पादित हो सकता है, MCP कॉल तुरंत वापस आ जाती है; कार्य स्थिति SQLite में सततीकृत की जाती है, पुनः आरंभ के बाद अधूरे कार्य स्वचालित रूप से पुनर्स्थापित होते हैं
- **मेमोरी डीडुप्लीकेशन** — अत्यधिक समान मौजूदा मेमोरी का स्वचालित रूप से पता लगाता है, दोहराव से बचता है
- **संघर्ष पहचान** — दो इकाइयों के बीच विरोधाभासी तथ्यों का पता लगाता है, अमान्य और वैध जानकारी की पहचान करता है
- **समुदाय पहचान** — Label Propagation एल्गोरिथम के आधार पर संबंधित इकाइयों को स्वचालित रूप से क्लस्टर करता है
- **महत्व ट्रैकिंग** — इकाई पहुँच आवृत्ति को स्वचालित रूप से रिकॉर्ड करता है, खोज परिणाम महत्व के अनुसार क्रमबद्ध होते हैं
- **बुद्धिमान विस्मृति** — पुरानी, कम पहुँच वाली मेमोरी की पहचान और सफाई करता है, ग्राफ को सुव्यवस्थित रखता है
- **बल्क आयात** — एक बार में कई मेमोरी सबमिट करता है, बड़े पैमाने पर डेटा माइग्रेशन के लिए उपयुक्त
- **संरचित त्रिक** — "विषय-संबंध-वस्तु" को सीधे जोड़ता है, LLM निष्कर्षण को छोड़कर, सेकंड में पूर्ण
- **Web प्रबंधन इंटरफ़ेस** — अंतर्निहित डैशबोर्ड, ब्राउज़िंग, खोज, ज्ञान ग्राफ विज़ुअलाइज़ेशन, AI प्रश्नोत्तर, समुदाय ब्राउज़िंग, गुणवत्ता रखरखाव, बल्क आयात, रनटाइम सेटिंग्स
- **बहुभाषी (i18n)** — प्रतिक्रिया संदेश 33 भाषाओं का समर्थन करते हैं (जिनमें zh-TW / en / zh-CN / ja / pt-BR / ko / es / de / fr आदि शामिल हैं; zh-TW/en/zh-CN/ja हस्तलिखित, शेष generated परत द्वारा प्रदान); MCP उपकरण `SERVER_LANG` के अनुसार, REST API HTTP `Accept-Language` के अनुसार स्वचालित रूप से वार्ता करता है
- **डार्क/लाइट थीम** — Web इंटरफ़ेस थीम स्विचिंग का समर्थन करता है
- **सुरक्षित मोड** — इकाई निष्कर्षण को छोड़ने वाला तीव्र मेमोरी जोड़ना वैकल्पिक रूप से चुना जा सकता है
- **Docker समर्थन** — अंतर्निहित Dockerfile, कंटेनरीकृत परिनियोजन का समर्थन करता है
- **समवर्ती सुरक्षा** — asyncio.Lock आरंभीकरण की सुरक्षा करता है, रेस कंडीशन को रोकता है
- **स्तरित स्वास्थ्य जाँच** — `/health` (liveness) + `/health/ready` (readiness)

## सिस्टम आवश्यकताएँ

| आइटम | आवश्यकता |
|------|------|
| Python | 3.10+ (3.11+ अनुशंसित) |
| Neo4j | 4.0+ (`bolt://localhost:7687`) |
| LLM प्रदाता | Ollama / GLM / GROQ / OpenRouter / DeepSeek (पाँच में से एक) |
| Node.js | 18+ (केवल PM2 पृष्ठभूमि निष्पादन के लिए, वैकल्पिक) |
| डिस्क स्थान | ~3GB (Ollama मॉडल + Neo4j डेटा) |

### LLM प्रदाता चयन

`LLM_PROVIDER` पर्यावरण चर के माध्यम से स्विच करें (`ollama` / `glm` / `groq` / `openrouter` / `deepseek`):

| प्रदाता | विशेषताएँ | LLM मॉडल | Embedding | उपयुक्त परिदृश्य |
|--------|------|----------|-----------|----------|
| **Ollama** (डिफ़ॉल्ट) | पूरी तरह स्थानीय, डेटा मशीन नहीं छोड़ता | `qwen2.5:3b` | `bge-m3` (चीनी + RAG उत्कृष्ट) | GPU उपलब्ध, गोपनीयता को महत्व देता है |
| **GLM** | मुफ़्त क्लाउड, स्थिर असीमित प्रवाह | `glm-4-flash` (मुफ़्त) | `embedding-3` | कोई GPU नहीं, खोज-गहन परिदृश्य |
| **GROQ** | अति-उच्च गति अनुमान | `llama-3.3-70b-versatile` | Ollama `bge-m3` पर वापसी | कभी-कभार लेखन, गुणवत्ता की खोज |
| **OpenRouter** | विभिन्न मॉडलों का एकत्रीकरण, मुफ़्त कोटा सहित | `stepfun/step-3.5-flash:free` आदि | Ollama `bge-m3` पर वापसी | विशिष्ट क्लाउड मॉडल का उपयोग करना चाहते हैं |
| **DeepSeek** | DeepSeek क्लाउड, उच्च लागत-प्रभावशीलता | `deepseek-v4-flash` / `deepseek-v4-pro` | Ollama `bge-m3` पर वापसी | चीनी समझ, कम लागत क्लाउड |

> **Embedding और LLM का विसंयुग्मन**: एम्बेडर को `EMBEDDING_PROVIDER` (`ollama` / `glm`) के माध्यम से स्वतंत्र रूप से निर्दिष्ट किया जाता है, सेट न होने पर `LLM_PROVIDER` का अनुसरण करता है। वास्तव में केवल `glm` GLM `embedding-3` का उपयोग करता है, बाकी (GROQ / OpenRouter / DeepSeek जैसे Embedding प्रदान न करने वाले क्लाउड LLM सहित) सभी स्वचालित रूप से Ollama `bge-m3` का उपयोग करते हैं। **इसलिए किसी भी क्लाउड LLM का उपयोग करते समय, फिर भी स्थानीय Ollama को एम्बेडिंग सेवा प्रदान करने की आवश्यकता होती है (जब तक कि embedding को भी glm पर सेट न किया जाए)।**

#### Ollama मोड (स्थानीय)

```bash
# LLM मुख्य मॉडल (qwen2.5:3b अनुशंसित, गति और स्थिरता का सर्वोत्तम संतुलन)
ollama pull qwen2.5:3b

# एम्बेडिंग मॉडल (आवश्यक, वेक्टर खोज के लिए)
ollama pull bge-m3
```

> **मॉडल चयन संबंधी सावधानियाँ**:
> - `qwen2.5:3b` — अनुशंसित, ~2s/call, ~100 t/s, graphiti-core संरचित आउटपुट 100% स्थिर
> - `qwen2.5:7b` — बेहतर प्रभाव लेकिन 5-10 गुना धीमा, गुणवत्ता की खोज वाले परिदृश्यों के लिए उपयुक्त
> - `qwen2.5:1.5b` — सबसे तेज़ लेकिन **अस्थिर** (संरचित JSON सफलता दर केवल 33%), उपयोग करने की अनुशंसा नहीं है

#### GLM मोड (Zhipu AI क्लाउड)

```bash
# .env सेटिंग्स
LLM_PROVIDER=glm
GLM_API_KEY=your_api_key          # https://open.bigmodel.cn से प्राप्त करें
GLM_MODEL=glm-4-flash             # मुफ़्त मॉडल
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768      # Neo4j वेक्टर इंडेक्स आयाम के अनुरूप होना चाहिए
```

> **GLM प्रदर्शन संदर्भ**: लेखन ~22s (छोटा टेक्स्ट), खोज ~0.34s, शून्य Rate Limit त्रुटियाँ, स्थानीय Ollama से 2-5 गुना धीमा लेकिन पूरी तरह मुफ़्त।

#### GROQ मोड (उच्च गति अनुमान)

```bash
# .env सेटिंग्स
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key         # https://console.groq.com से प्राप्त करें
GROQ_MODEL=llama-3.3-70b-versatile
```

> **ध्यान दें**: GROQ Embedding सेवा प्रदान नहीं करता, Ollama एम्बेडर के साथ संयोजन की आवश्यकता है (स्वचालित वापसी) या `EMBEDDING_PROVIDER` को glm पर सेट करें। GROQ में कठोर Rate Limit है, उच्च-आवृत्ति उपयोग बड़ी संख्या में पुनः प्रयासों को ट्रिगर करेगा।

#### OpenRouter मोड (विभिन्न मॉडलों का एकत्रीकरण)

```bash
# .env सेटिंग्स
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_api_key       # https://openrouter.ai/keys से प्राप्त करें
OPENROUTER_MODEL=stepfun/step-3.5-flash:free   # किसी भी OpenRouter मॉडल में बदला जा सकता है
```

> **ध्यान दें**: OpenRouter Embedding प्रदान नहीं करता, स्वचालित रूप से Ollama `bge-m3` पर वापस आ जाता है। मॉडल सूची के लिए https://openrouter.ai/models देखें (कई `:free` मुफ़्त मॉडल सहित)।

#### DeepSeek मोड (DeepSeek)

```bash
# .env सेटिंग्स
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key         # https://platform.deepseek.com से प्राप्त करें
DEEPSEEK_MODEL=deepseek-v4-flash      # अनुशंसित; या deepseek-v4-pro (बेहतर प्रभाव)
```

> **ध्यान दें**: DeepSeek Embedding प्रदान नहीं करता, स्वचालित रूप से Ollama `bge-m3` पर वापस आ जाता है। `deepseek-chat` / `deepseek-reasoner` 2026-07-24 को बंद हो जाएंगे, `deepseek-v4-flash` / `deepseek-v4-pro` का उपयोग करने की अनुशंसा की जाती है। DeepSeek `json_object` मोड के prompt में "json" स्ट्रिंग की कठोरता से आवश्यकता रखता है, क्लाइंट में अंतर्निहित बैकअप सुरक्षा है, अतिरिक्त सेटिंग्स की आवश्यकता नहीं है।

## त्वरित प्रारंभ

### 1. पूर्व तैयारी

पुष्टि करें कि Neo4j स्थानीय मशीन पर चल रहा है, और चुने गए LLM प्रदाता के अनुसार संबंधित सेवा तैयार करें:

```bash
# पुष्टि करें कि Neo4j चल रहा है (आवश्यक)
neo4j status
# या Docker का उपयोग करें: docker run -d -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/your_password neo4j:latest

# Ollama मोड: पुष्टि करें कि Ollama चल रहा है
ollama list
# यदि शुरू नहीं हुआ है: ollama serve

# GLM / GROQ मोड: केवल एक वैध API Key की आवश्यकता है, स्थानीय सेवा की आवश्यकता नहीं
```

### 2. निर्भरताएँ स्थापित करें

```bash
git clone <repo-url>
cd graphiti
uv sync
```

> **ध्यान दें**: यह प्रोजेक्ट निर्भरताओं को प्रबंधित करने के लिए [uv](https://github.com/astral-sh/uv) का उपयोग करता है। यदि स्थापित नहीं है: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 3. पर्यावरण कॉन्फ़िगर करें

```bash
cp .env.example .env
```

`.env` संपादित करें, **कम से कम** निम्नलिखित आइटम संशोधित करने की आवश्यकता है:

```bash
NEO4J_PASSWORD=your_actual_password  # आवश्यक: Neo4j पासवर्ड
LLM_PROVIDER=ollama                  # ollama / glm / groq / openrouter / deepseek
OLLAMA_MODEL=qwen2.5:3b              # Ollama मोड: स्थानीय LLM मॉडल
# GLM_API_KEY=your_key               # GLM मोड: Zhipu AI API Key
# GROQ_API_KEY=your_key              # GROQ मोड: GROQ API Key
# OPENROUTER_API_KEY=your_key        # OpenRouter मोड: API Key
# DEEPSEEK_API_KEY=your_key          # DeepSeek मोड: API Key
```

### 4. सेवा प्रारंभ करें

```bash
# HTTP मोड (अनुशंसित, Web प्रबंधन इंटरफ़ेस सहित)
uv run python graphiti_mcp_server.py --transport http --port 8000

# या PM2 पृष्ठभूमि निष्पादन का उपयोग करें (दीर्घकालिक संचालन के लिए अनुशंसित)
pm2 start ecosystem.config.cjs
```

### 5. सेवा सत्यापित करें

प्रारंभ करने के बाद निम्नलिखित endpoints तक पहुँचा जा सकता है:

| endpoint | विवरण |
|------|------|
| http://localhost:8000/ | Web प्रबंधन इंटरफ़ेस |
| http://localhost:8000/mcp | MCP endpoint (MCP क्लाइंट कनेक्शन के लिए) |
| http://localhost:8000/health | स्वास्थ्य जाँच (liveness) |
| http://localhost:8000/health/ready | गहन जाँच (Neo4j कनेक्शन सहित) |
| http://localhost:8000/api/stats | REST API सांख्यिकी |

## प्रोजेक्ट संरचना

```
graphiti/
├── graphiti_mcp_server.py        # मुख्य प्रवेश बिंदु — MCP उपकरण परिभाषा (19 उपकरण)
├── src/
│   ├── config.py                 # कॉन्फ़िगरेशन प्रबंधन (GraphitiConfig, JSON/.env स्तरीकरण का समर्थन)
│   ├── web_api.py                # Web प्रबंधन इंटरफ़ेस REST API (30+ endpoints)
│   ├── ollama_graphiti_client.py  # Ollama LLM क्लाइंट (दोहरा मॉडल वितरण)
│   ├── openai_compat_client.py   # OpenAI संगत LLM आधार वर्ग (json_object + सरलीकृत schema + json बैकअप सुरक्षा)
│   ├── glm_client.py             # GLM (Zhipu AI) LLM क्लाइंट (OpenAICompatClient से विरासत)
│   ├── openrouter_client.py      # OpenRouter LLM क्लाइंट (OpenAICompatClient से विरासत)
│   ├── deepseek_client.py        # DeepSeek LLM क्लाइंट (OpenAICompatClient से विरासत)
│   ├── ollama_embedder.py        # Ollama एम्बेडिंग मॉडल अडैप्टर
│   ├── content_preprocessor.py   # बुद्धिमान सामग्री विभाजन (लंबे टेक्स्ट का स्वचालित विभाजन)
│   ├── deduplication.py          # मेमोरी डीडुप्लीकेशन (कोसाइन समानता तुलना)
│   ├── importance.py             # महत्व ट्रैकिंग और बुद्धिमान विस्मृति
│   ├── safe_memory_add.py        # सुरक्षित मेमोरी जोड़ना (इकाई निष्कर्षण को छोड़ना)
│   ├── task_store.py             # पृष्ठभूमि कार्य SQLite सततीकरण (TaskStore)
│   ├── timezone_utils.py         # समय क्षेत्र रूपांतरण (UTC→स्थानीय समय क्षेत्र प्रदर्शन)
│   ├── i18n.py                   # बैकएंड बहुभाषी (REST Accept-Language के अनुसार, MCP SERVER_LANG के अनुसार)
│   ├── i18n_generated.py         # स्वचालित रूप से उत्पन्न भाषा कवरेज (GENERATED_MESSAGE_OVERRIDES)
│   ├── exceptions.py             # संरचित अपवाद प्रबंधन (12 प्रकार के अपवाद वर्ग)
│   └── logging_setup.py          # लॉगिंग सिस्टम (समय रोटेशन + प्रदर्शन निगरानी)
├── web/                          # Web प्रबंधन इंटरफ़ेस फ्रंटएंड (SPA, बिना build)
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js                # REST API रैपर
│       ├── components.js         # UI घटक रेंडरिंग (समुदाय पृष्ठ सहित)
│       └── app.js                # SPA रूटिंग, स्थिति प्रबंधन
├── tests/                        # परीक्षण सूट (203 परीक्षण)
│   ├── test_content_preprocessor.py  # विभाजन तर्क परीक्षण (17)
│   ├── test_new_features.py      # नई सुविधा परीक्षण (32)
│   ├── test_i18n.py             # बहुभाषी परीक्षण (57)
│   ├── test_unit.py              # इकाई परीक्षण
│   ├── test_web_api.py           # Web API परीक्षण
│   ├── test_web_ui_features.py   # Web UI सुविधा परीक्षण
│   ├── test_integration_manual.py # मैनुअल एकीकरण परीक्षण
│   └── bench_deepseek_flash_vs_pro.py # DeepSeek flash/pro प्रदर्शन बेंचमार्क स्क्रिप्ट
├── tools/                        # विकास निदान उपकरण
│   ├── status_report.py          # एकीकृत स्थिति रिपोर्ट
│   ├── validate_config.py        # कॉन्फ़िगरेशन सत्यापन
│   ├── performance_diagnose.py   # प्रदर्शन निदान
│   ├── inspect_schema.py         # Neo4j संरचना जाँच
│   ├── batch_reprocess.py        # बैच पुनर्प्रसंस्करण
│   └── migrate_embeddings.py     # Embedding मॉडल माइग्रेशन
├── docs/                         # दस्तावेज़
├── logs/                         # लॉग (समय रोटेशन, डिफ़ॉल्ट रूप से 30 दिन तक रखे जाते हैं)
├── Dockerfile                    # Docker कंटेनरीकृत परिनियोजन
└── ecosystem.config.cjs          # PM2 कॉन्फ़िगरेशन
```

## MCP क्लाइंट सेटिंग्स

### HTTP मोड (अनुशंसित)

Claude Code, Cline आदि HTTP समर्थन करने वाले MCP क्लाइंट के लिए उपयुक्त:

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

### STDIO मोड

Claude Desktop आदि उन क्लाइंट के लिए उपयुक्त जिन्हें सीधे प्रक्रिया शुरू करने की आवश्यकता होती है:

**कॉन्फ़िगरेशन फ़ाइल स्थान:**
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

> **ध्यान दें**: SSE मोड (`--transport sse`) का उपयोग करने की अनुशंसा नहीं है। MCP 1.x में session आरंभीकरण संगतता समस्याएँ हैं, कृपया HTTP मोड का उपयोग करें।

## MCP उपकरण (19)

### मेमोरी प्रबंधन (7)

| उपकरण | विवरण |
|------|------|
| `add_memory_simple` | ज्ञान ग्राफ में मेमोरी जोड़ें (पृष्ठभूमि प्रसंस्करण, बुद्धिमान विभाजन, डीडुप्लीकेशन जाँच का समर्थन) |
| `add_episode_bulk` | कई मेमोरी बल्क में जोड़ें (डिफ़ॉल्ट पृष्ठभूमि प्रसंस्करण) |
| `add_triplet` | संरचित त्रिक जोड़ना (LLM को छोड़कर, सेकंड में पूर्ण) |
| `search_memory_nodes` | मेमोरी नोड खोजें (16 खोज रणनीतियों, समय फ़िल्टरिंग का समर्थन) |
| `search_memory_facts` | मेमोरी तथ्य खोजें (संबंध प्रकार फ़िल्टरिंग, समय सीमा, वैधता फ़िल्टरिंग का समर्थन) |
| `advanced_search` | उन्नत खोज (16 रणनीतियाँ, नोड+एज+समुदाय+एपिसोड लौटाता है) |
| `get_episodes` | हाल के मेमोरी एपिसोड प्राप्त करें |

### ज्ञान विश्लेषण (3)

| उपकरण | विवरण |
|------|------|
| `check_conflicts` | दो इकाइयों के बीच तथ्यात्मक संघर्षों का पता लगाएँ (वैध vs अमान्य) |
| `get_node_edges` | नोड के इनबाउंड और आउटबाउंड एज संबंधों का अन्वेषण करें |
| `build_communities` | समुदाय पहचान और क्लस्टरिंग को ट्रिगर करें (डिफ़ॉल्ट पृष्ठभूमि प्रसंस्करण) |

### मेमोरी रखरखाव (2)

| उपकरण | विवरण |
|------|------|
| `get_stale_memories` | पुरानी, कम पहुँच वाली मेमोरी की क्वेरी करें |
| `cleanup_stale_memories` | पुरानी मेमोरी साफ़ करें (डिफ़ॉल्ट dry_run पूर्वावलोकन मोड) |

### कार्य प्रबंधन

| उपकरण | विवरण |
|------|------|
| `get_memory_task_status` | पृष्ठभूमि मेमोरी प्रसंस्करण कार्य की प्रगति और परिणाम की क्वेरी करें |

### हटाना और क्वेरी

| उपकरण | विवरण |
|------|------|
| `delete_episode` | मेमोरी एपिसोड हटाएँ |
| `delete_entity_edge` | इकाई एज (संबंध) हटाएँ |
| `get_entity_edge` | इकाई एज विवरण जानकारी प्राप्त करें |

### सिस्टम प्रबंधन

| उपकरण | विवरण |
|------|------|
| `get_status` | सेवा स्थिति प्राप्त करें (Neo4j, LLM, एम्बेडर) |
| `test_connection` | Neo4j / LLM / एम्बेडर कनेक्शन का परीक्षण करें |
| `clear_graph` | ग्राफ डेटाबेस साफ़ करें (group_id द्वारा साफ़ करने का समर्थन) |

## उपकरण पैरामीटर

### add_memory_simple

| पैरामीटर | प्रकार | आवश्यक | डिफ़ॉल्ट मान | विवरण |
|------|------|------|--------|------|
| `name` | string | Y | | मेमोरी नाम |
| `episode_body` | string | Y | | मेमोरी सामग्री (800 अक्षरों से अधिक स्वचालित विभाजन) |
| `group_id` | string | | `"default"` | समूह ID (प्रोजेक्ट द्वारा पृथक्करण अनुशंसित) |
| `source` | string | | `"text"` | स्रोत प्रकार: `text` / `json` / `message` |
| `source_description` | string | | `"MCP Server"` | स्रोत विवरण |
| `use_safe_mode` | bool | | `false` | सुरक्षित मोड (इकाई निष्कर्षण को छोड़ता है, तेज़ लेकिन मेमोरी खोजी नहीं जा सकती) |
| `background` | bool | | `false` | पृष्ठभूमि प्रसंस्करण (तुरंत task_id लौटाता है, लंबे टेक्स्ट के लिए उपयुक्त) |
| `force` | bool | | `false` | डीडुप्लीकेशन जाँच को छोड़ें (बलपूर्वक जोड़ें) |
| `excluded_entity_types` | list | | | बहिष्कृत इकाई प्रकार (अनावश्यक निष्कर्षण मात्रा को कम करें) |

> **प्रदर्शन सुझाव**:
> - छोटा टेक्स्ट (<800 अक्षर): सीधे प्रसंस्करण, आमतौर पर 30-40 सेकंड में पूर्ण
> - लंबा टेक्स्ट (>800 अक्षर): स्वचालित रूप से कई खंडों में विभाजित, `add_episode_bulk` का उपयोग करके समवर्ती प्रसंस्करण (क्रमिक से ~33% तेज़)
> - `background=true` का उपयोग MCP कॉल अवरोधन से बच सकता है, `get_memory_task_status` के माध्यम से प्रगति ट्रैक करें
> - `use_safe_mode=true` सेकंड में पूर्ण लेकिन मेमोरी search उपकरण द्वारा नहीं खोजी जा सकती
> - डीडुप्लीकेशन सक्षम होने पर, अत्यधिक समान मेमोरी के बारे में चेतावनी दी जाएगी (`force=true` से छोड़ा जा सकता है)

### add_episode_bulk

| पैरामीटर | प्रकार | आवश्यक | डिफ़ॉल्ट मान | विवरण |
|------|------|------|--------|------|
| `episodes` | list | Y | | मेमोरी सूची, प्रत्येक आइटम में `name` और `content` शामिल हैं |
| `group_id` | string | | `"default"` | समूह ID |
| `source` | string | | `"text"` | स्रोत प्रकार |
| `background` | bool | | `true` | पृष्ठभूमि प्रसंस्करण (बल्क आमतौर पर समय लेता है) |

### add_triplet

| पैरामीटर | प्रकार | आवश्यक | डिफ़ॉल्ट मान | विवरण |
|------|------|------|--------|------|
| `source_name` | string | Y | | स्रोत इकाई नाम (जैसे "Alice") |
| `target_name` | string | Y | | लक्ष्य इकाई नाम (जैसे "Google") |
| `relation_name` | string | Y | | संबंध नाम (जैसे "works_at") |
| `fact` | string | Y | | तथ्य विवरण (जैसे "Alice works at Google") |
| `group_id` | string | | `"default"` | समूह ID |
| `source_labels` | list | | | स्रोत इकाई लेबल |
| `target_labels` | list | | | लक्ष्य इकाई लेबल |

### search_memory_nodes

| पैरामीटर | प्रकार | आवश्यक | डिफ़ॉल्ट मान | विवरण |
|------|------|------|--------|------|
| `query` | string | Y | | खोज कीवर्ड (प्राकृतिक भाषा) |
| `max_nodes` | int | | `10` | अधिकतम वापसी मात्रा |
| `group_ids` | list | | | समूह फ़िल्टरिंग (कई समूहों की संयुक्त खोज) |
| `entity_types` | list | | | इकाई प्रकार फ़िल्टरिंग |
| `search_recipe` | string | | | खोज रणनीति (उन्नत खोज देखें) |
| `created_after` | string | | | निर्माण समय निचली सीमा (ISO datetime) |
| `created_before` | string | | | निर्माण समय ऊपरी सीमा (ISO datetime) |

### search_memory_facts

| पैरामीटर | प्रकार | आवश्यक | डिफ़ॉल्ट मान | विवरण |
|------|------|------|--------|------|
| `query` | string | Y | | खोज कीवर्ड |
| `max_facts` | int | | `10` | अधिकतम वापसी मात्रा |
| `group_ids` | list | | | समूह फ़िल्टरिंग |
| `center_node_uuid` | string | | | केंद्र नोड UUID (विशिष्ट नोड के संबंधों का अन्वेषण) |
| `edge_types` | list | | | संबंध प्रकार फ़िल्टरिंग (जैसे `["works_at"]`) |
| `created_after` | string | | | निर्माण समय निचली सीमा (ISO datetime) |
| `created_before` | string | | | निर्माण समय ऊपरी सीमा (ISO datetime) |
| `only_valid` | bool | | `false` | केवल अमान्य न हुए तथ्य लौटाएँ |

### advanced_search

| पैरामीटर | प्रकार | आवश्यक | डिफ़ॉल्ट मान | विवरण |
|------|------|------|--------|------|
| `query` | string | Y | | खोज कीवर्ड |
| `search_recipe` | string | | `"combined_rrf"` | खोज रणनीति (16 विकल्प) |
| `max_results` | int | | `10` | अधिकतम वापसी मात्रा |
| `group_ids` | list | | | समूह फ़िल्टरिंग |
| `center_node_uuid` | string | | | केंद्र नोड UUID |

**उपलब्ध खोज रणनीतियाँ (search_recipe):**

| श्रेणी | रणनीति | विवरण |
|------|------|------|
| संयुक्त | `combined_rrf` | संयुक्त RRF संलयन (डिफ़ॉल्ट, अनुशंसित) |
| संयुक्त | `combined_mmr` | संयुक्त MMR विविधता पुनर्रैंकिंग |
| संयुक्त | `combined_cross_encoder` | संयुक्त Cross-Encoder परिशुद्ध रैंकिंग |
| एज | `edge_rrf` / `edge_mmr` / `edge_cross_encoder` | एज खोज (3 प्रकार की रैंकिंग) |
| एज | `edge_node_distance` / `edge_episode_mentions` | एज खोज (ग्राफ दूरी/उद्धरण संख्या) |
| नोड | `node_rrf` / `node_mmr` / `node_cross_encoder` | नोड खोज (3 प्रकार की रैंकिंग) |
| नोड | `node_node_distance` / `node_episode_mentions` | नोड खोज (ग्राफ दूरी/उद्धरण संख्या) |
| समुदाय | `community_rrf` / `community_mmr` / `community_cross_encoder` | समुदाय खोज |

### check_conflicts

| पैरामीटर | प्रकार | आवश्यक | डिफ़ॉल्ट मान | विवरण |
|------|------|------|--------|------|
| `source_name` | string | Y | | स्रोत इकाई नाम |
| `target_name` | string | Y | | लक्ष्य इकाई नाम |
| `group_id` | string | | `"default"` | समूह ID |

### get_node_edges

| पैरामीटर | प्रकार | आवश्यक | डिफ़ॉल्ट मान | विवरण |
|------|------|------|--------|------|
| `node_uuid` | string | Y | | नोड UUID |
| `include_inbound` | bool | | `true` | इनबाउंड एज शामिल करें |
| `include_outbound` | bool | | `true` | आउटबाउंड एज शामिल करें |
| `max_edges` | int | | `50` | अधिकतम वापसी मात्रा |

### build_communities

| पैरामीटर | प्रकार | आवश्यक | डिफ़ॉल्ट मान | विवरण |
|------|------|------|--------|------|
| `group_ids` | list | | | निर्दिष्ट समूह (खाली छोड़ने पर सभी) |
| `background` | bool | | `true` | पृष्ठभूमि प्रसंस्करण |

### get_stale_memories

| पैरामीटर | प्रकार | आवश्यक | डिफ़ॉल्ट मान | विवरण |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | कितने दिनों से अधिक न पहुँचने पर पुराना माना जाए |
| `min_access_count` | int | | `2` | इस मान से कम पहुँच संख्या होने पर ही सूचीबद्ध करें |
| `group_id` | string | | | समूह फ़िल्टरिंग |
| `limit` | int | | `50` | अधिकतम वापसी मात्रा |

### cleanup_stale_memories

| पैरामीटर | प्रकार | आवश्यक | डिफ़ॉल्ट मान | विवरण |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | पुराना दिन सीमा |
| `min_access_count` | int | | `2` | न्यूनतम पहुँच संख्या सीमा |
| `group_id` | string | | | समूह फ़िल्टरिंग |
| `dry_run` | bool | | `true` | पूर्वावलोकन मोड (वास्तव में नहीं हटाता) |
| `limit` | int | | `50` | अधिकतम प्रसंस्करण मात्रा |

### get_memory_task_status

| पैरामीटर | प्रकार | आवश्यक | विवरण |
|------|------|------|------|
| `task_id` | string | Y | पृष्ठभूमि कार्य ID (`add_memory_simple(background=true)` द्वारा लौटाया गया) |

## Web प्रबंधन इंटरफ़ेस

HTTP मोड में `http://localhost:8000/` तक पहुँचकर उपयोग किया जा सकता है।

**विशेषताएँ:**
- डैशबोर्ड — नोड संख्या, तथ्य संख्या, मेमोरी एपिसोड संख्या सांख्यिकी
- इकाई नोड — ब्राउज़िंग, फ़िल्टरिंग, वेक्टर खोज
- तथ्य संबंध — ब्राउज़िंग, फ़िल्टरिंग, वेक्टर खोज
- मेमोरी एपिसोड — ब्राउज़िंग, पूर्ण-पाठ खोज, हटाना
- समुदाय ब्राउज़िंग — समुदाय नोड सूची, सारांश, समुदाय निर्माण को ट्रिगर करना
- त्रिक फ़ॉर्म — "विषय-संबंध-वस्तु" संरचित ज्ञान को सीधे जोड़ना
- Group प्रबंधन — समूह द्वारा फ़िल्टरिंग, बैच हटाना
- ज्ञान ग्राफ विज़ुअलाइज़ेशन — नोड संबंधों का ग्राफिकल प्रदर्शन
- AI प्रश्नोत्तर — ज्ञान ग्राफ पर आधारित बुद्धिमान प्रश्नोत्तर
- गुणवत्ता रखरखाव — मेमोरी गुणवत्ता संकेतक और सफाई उपकरण
- बल्क आयात — एक बार में कई मेमोरी एपिसोड आयात करें (JSON, एकल सत्र सीमा 500)
- रनटाइम सेटिंग्स — वर्तमान प्रभावी सेटिंग्स देखें और पुनः आरंभ किए बिना कुछ मापदंड समायोजित करें
- थीम स्विचिंग — डार्क/लाइट थीम

**REST API:**

| endpoint | विधि | विवरण |
|------|------|------|
| `/api/stats` | GET | डैशबोर्ड सांख्यिकी |
| `/api/groups` | GET | सभी group_id प्राप्त करें |
| `/api/groups/stats` | GET | प्रत्येक group के नोड/तथ्य/एपिसोड सांख्यिकी |
| `/api/nodes` | GET | इकाई नोड ब्राउज़ करें (पृष्ठांकन) |
| `/api/facts` | GET | तथ्य ब्राउज़ करें (पृष्ठांकन) |
| `/api/episodes` | GET | मेमोरी एपिसोड ब्राउज़ करें (पृष्ठांकन) |
| `/api/nodes/{uuid}/relations` | GET | नोड के इनबाउंड/आउटबाउंड संबंध प्राप्त करें |
| `/api/search/nodes` | GET | वेक्टर खोज नोड |
| `/api/search/facts` | GET | वेक्टर खोज तथ्य |
| `/api/search/episodes` | GET | मेमोरी एपिसोड खोजें |
| `/api/search/advanced` | GET | उन्नत खोज (16 रणनीतियाँ) |
| `/api/communities` | GET | समुदाय नोड ब्राउज़ करें (पृष्ठांकन) |
| `/api/communities/build` | POST | समुदाय निर्माण को ट्रिगर करें |
| `/api/memory/add` | POST | एकल मेमोरी जोड़ें |
| `/api/memory/add-bulk` | POST | बल्क मेमोरी जोड़ें |
| `/api/memory/add-triplet` | POST | त्रिक जोड़ें |
| `/api/import/episodes` | POST | मेमोरी एपिसोड बल्क आयात करें (JSON, एकल सत्र सीमा 500) |
| `/api/memory/tasks` | GET | पृष्ठभूमि कार्य सूचीबद्ध करें (स्थिति फ़िल्टरिंग का समर्थन) |
| `/api/memory/tasks/{id}` | GET | एकल कार्य स्थिति की क्वेरी करें |
| `/api/timeline` | GET | समयरेखा ब्राउज़िंग |
| `/api/graph/subgraph` | GET | उप-ग्राफ प्राप्त करें (विज़ुअलाइज़ेशन) |
| `/api/graph/all` | GET | संपूर्ण ग्राफ प्राप्त करें (विज़ुअलाइज़ेशन) |
| `/api/ask` | GET | AI प्रश्नोत्तर (ग्राफ-आधारित खोज) |
| `/api/analytics/top-nodes` | GET | उच्च कनेक्टिविटी/उच्च पहुँच नोड |
| `/api/analytics/quality` | GET | ज्ञान ग्राफ गुणवत्ता संकेतक |
| `/api/analytics/stale` | GET | पुरानी मेमोरी की क्वेरी करें |
| `/api/analytics/cleanup` | POST | पुरानी मेमोरी साफ़ करें |
| `/api/config` | GET | वर्तमान प्रभावी सेटिंग्स प्राप्त करें (API key को छोड़कर) |
| `/api/config` | PATCH | रनटाइम में परिवर्तनीय सेटिंग्स अपडेट करें (केवल इस प्रक्रिया के लिए, पुनः आरंभ पर रीसेट) |
| `/api/nodes/{uuid}` | DELETE | नोड हटाएँ |
| `/api/episodes/{uuid}` | DELETE | मेमोरी एपिसोड हटाएँ |
| `/api/facts/{uuid}` | DELETE | तथ्य हटाएँ |
| `/api/groups/{group_id}` | DELETE | पूरा group हटाएँ |

## कॉन्फ़िगरेशन

### पर्यावरण चर (.env)

कॉन्फ़िगरेशन स्तरीकरण तंत्र का उपयोग करता है: JSON कॉन्फ़िगरेशन फ़ाइल आधार के रूप में, पर्यावरण चर व्यक्तिगत मानों को अधिलेखित करते हैं।

```bash
# === आवश्यक ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password        # संशोधित करना आवश्यक

# === LLM प्रदाता चयन ===
LLM_PROVIDER=ollama                 # ollama / glm / groq / openrouter / deepseek

# === Embedding प्रदाता (वैकल्पिक, डिफ़ॉल्ट रूप से LLM_PROVIDER का अनुसरण) ===
# केवल glm GLM Embedding का उपयोग करता है, बाकी सभी Ollama bge-m3 का उपयोग करते हैं
# EMBEDDING_PROVIDER=ollama         # ollama / glm

# === Ollama कॉन्फ़िगरेशन (LLM_PROVIDER=ollama होने पर उपयोग) ===
OLLAMA_MODEL=qwen2.5:3b             # मुख्य मॉडल (qwen2.5:3b अनुशंसित)
OLLAMA_SMALL_MODEL=qwen2.5:3b       # छोटा मॉडल (सरल कार्यों के लिए, अलग मॉडल वैकल्पिक)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.1

# === GLM कॉन्फ़िगरेशन (LLM_PROVIDER=glm होने पर उपयोग) ===
GLM_API_KEY=your_api_key            # https://open.bigmodel.cn से प्राप्त करें
GLM_MODEL=glm-4-flash               # मुफ़्त मॉडल
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768

# === GROQ कॉन्फ़िगरेशन (LLM_PROVIDER=groq होने पर उपयोग) ===
GROQ_API_KEY=your_api_key           # https://console.groq.com से प्राप्त करें
GROQ_MODEL=llama-3.3-70b-versatile

# === OpenRouter कॉन्फ़िगरेशन (LLM_PROVIDER=openrouter होने पर उपयोग) ===
OPENROUTER_API_KEY=your_api_key     # https://openrouter.ai/keys से प्राप्त करें
OPENROUTER_MODEL=stepfun/step-3.5-flash:free

# === DeepSeek कॉन्फ़िगरेशन (LLM_PROVIDER=deepseek होने पर उपयोग) ===
DEEPSEEK_API_KEY=your_api_key       # https://platform.deepseek.com से प्राप्त करें
DEEPSEEK_MODEL=deepseek-v4-flash    # या deepseek-v4-pro

# === Ollama एम्बेडिंग मॉडल (गैर-glm एम्बेडिंग होने पर सभी उपयोग करते हैं) ===
OLLAMA_EMBEDDING_MODEL=bge-m3
OLLAMA_EMBEDDING_DIMENSIONS=768

# === प्रदर्शन और भाषा (वैकल्पिक) ===
GRAPHITI_DISPLAY_TIMEZONE=Asia/Taipei # API द्वारा लौटाए गए timestamp का प्रदर्शन समय क्षेत्र (IANA नाम; भंडारण UTC में बना रहता है)
SERVER_LANG=zh-TW                     # MCP उपकरण प्रतिक्रिया भाषा (पूर्ण locale के लिए src/i18n.py देखें); REST API Accept-Language के अनुसार

# === मेमोरी प्रदर्शन (वैकल्पिक) ===
GRAPHITI_CHUNK_THRESHOLD=800         # बुद्धिमान विभाजन को ट्रिगर करने वाली अक्षर संख्या सीमा
GRAPHITI_MAX_CHUNK_SIZE=600          # प्रत्येक खंड की अधिकतम अक्षर संख्या
GRAPHITI_MAX_COROUTINES=10            # अधिकतम समवर्ती coroutine संख्या
GRAPHITI_DEFAULT_BACKGROUND=false    # क्या डिफ़ॉल्ट रूप से पृष्ठभूमि प्रसंस्करण
TASK_DB_PATH=data/tasks.db           # पृष्ठभूमि कार्य SQLite सततीकरण पथ

# === महत्व ट्रैकिंग और बुद्धिमान विस्मृति (वैकल्पिक) ===
ENABLE_IMPORTANCE_TRACKING=true      # पहुँच ट्रैकिंग सक्षम करें
IMPORTANCE_WEIGHT=0.1                # महत्व भार
STALE_DAYS_THRESHOLD=30              # पुराना दिन सीमा
STALE_MIN_ACCESS_COUNT=2             # न्यूनतम पहुँच संख्या

# === लॉग ===
LOG_FILE=logs/graphiti_mcp_server.log
LOG_LEVEL=INFO
```

> **पूर्ण पर्यावरण चर सूची** के लिए कृपया `.env.example` देखें

### JSON कॉन्फ़िगरेशन फ़ाइल

संस्करण नियंत्रण की आवश्यकता वाले कॉन्फ़िगरेशन के लिए उपयुक्त (पर्यावरण चर अभी भी अधिलेखित कर सकते हैं):

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

## PM2 पृष्ठभूमि निष्पादन

```bash
npm install -g pm2

pm2 start ecosystem.config.cjs      # प्रारंभ करें
pm2 status                           # स्थिति
pm2 logs graphiti-mcp-http           # रीयल-टाइम लॉग
pm2 restart graphiti-mcp-http --update-env  # पुनः प्रारंभ (.env पुनः लोड करें)

pm2 save && pm2 startup              # बूट पर स्वतः प्रारंभ सेट करें
```

> **सुझाव**: `.env` संशोधित करने के बाद `--update-env` फ़्लैग का उपयोग करके पुनः प्रारंभ करना आवश्यक है, अन्यथा पर्यावरण चर अपडेट नहीं होंगे।

## Docker परिनियोजन

```bash
docker build -t graphiti-mcp .

# ध्यान दें: Docker कंटेनर को Neo4j और Ollama से कनेक्ट करने में सक्षम होना चाहिए
# host network का उपयोग करना सबसे सरल है
docker run -p 8000:8000 --env-file .env --network host graphiti-mcp

# या बाहरी सेवा पते को स्पष्ट रूप से निर्दिष्ट करें
docker run -p 8000:8000 \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --env-file .env graphiti-mcp
```

## परीक्षण

```bash
# सभी परीक्षण चलाएँ (203, लगभग 1 सेकंड)
uv run python -m pytest tests/

# विस्तृत आउटपुट
uv run python -m pytest tests/ -v

# केवल विशिष्ट परीक्षण चलाएँ
uv run python -m pytest tests/test_content_preprocessor.py -v
uv run python -m pytest tests/test_new_features.py -v
uv run python -m pytest tests/test_unit.py -v
```

> **ध्यान दें**: `test_integration_manual.py` में 3 async परीक्षणों को `pytest-asyncio` स्थापित करने की आवश्यकता है, अनुपस्थित होने पर Failed दिखाएगा लेकिन अन्य परीक्षणों को प्रभावित नहीं करता। `bench_deepseek_flash_vs_pro.py` एक प्रदर्शन बेंचमार्क स्क्रिप्ट है, इकाई परीक्षण नहीं।

## समस्या निवारण

### Neo4j कनेक्शन विफल

```bash
neo4j status                              # सेवा स्थिति जाँचें
cypher-shell -u neo4j -p your_password    # पुष्टि करें कि पासवर्ड सही है
curl http://localhost:7474                 # HTTP पोर्ट की पुष्टि करें
```

सामान्य कारण:
- Neo4j शुरू नहीं हुआ
- गलत पासवर्ड (`.env` में `NEO4J_PASSWORD`)
- पोर्ट पर कब्ज़ा या फ़ायरवॉल अवरोधन

### LLM कनेक्शन विफल

**Ollama मोड:**
```bash
ollama serve                # Ollama सेवा प्रारंभ करें
ollama list                 # स्थापित मॉडल जाँचें
ollama pull qwen2.5:3b      # अनुपस्थित मॉडल स्थापित करें
```

सामान्य कारण: Ollama शुरू नहीं हुआ, मॉडल स्थापित नहीं, GPU मेमोरी अपर्याप्त

**GLM मोड:**
- पुष्टि करें कि `GLM_API_KEY` सही है
- पुष्टि करें कि `GLM_EMBEDDING_DIMENSIONS=768` (Neo4j वेक्टर इंडेक्स के अनुरूप होना चाहिए)
- GLM API endpoint: `https://open.bigmodel.cn/api/paas/v4/`

**GROQ मोड:**
- पुष्टि करें कि `GROQ_API_KEY` सही है
- Rate Limit बार-बार होने पर GLM मोड पर स्विच करने पर विचार करें
- GROQ Embedding प्रदान नहीं करता, सुनिश्चित करें कि Ollama एम्बेडर उपलब्ध है

**OpenRouter मोड:**
- पुष्टि करें कि `OPENROUTER_API_KEY` सही है, `OPENROUTER_MODEL` एक वैध मॉडल ID है (https://openrouter.ai/models देखें)
- Embedding प्रदान नहीं करता, सुनिश्चित करें कि Ollama एम्बेडर उपलब्ध है

**DeepSeek मोड:**
- पुष्टि करें कि `DEEPSEEK_API_KEY` सही है
- यदि `Prompt must contain the word 'json'` दिखाई दे: यह DeepSeek `json_object` मोड की कठोर आवश्यकता है, क्लाइंट में अंतर्निहित बैकअप सुरक्षा है; यदि फिर भी दिखाई दे, तो पुष्टि करें कि नवीनतम संस्करण `src/deepseek_client.py` का उपयोग किया जा रहा है और सेवा को पुनः प्रारंभ करें
- Embedding प्रदान नहीं करता, सुनिश्चित करें कि Ollama एम्बेडर उपलब्ध है

### MCP कनेक्शन त्रुटि

यदि `Invalid request parameters` या `Received request before initialization was complete` दिखाई दे:

1. पुष्टि करें कि HTTP ट्रांसपोर्ट मोड का उपयोग किया जा रहा है (**SSE का उपयोग न करें**)
2. पुष्टि करें कि क्लाइंट `"type": "http"`, `"url": "http://localhost:8000/mcp"` पर सेट है
3. सेवा पुनः प्रारंभ करें: `pm2 restart graphiti-mcp-http --update-env`
4. Claude Code में पुनः कनेक्ट करने के लिए `/mcp` निष्पादित करें

### मेमोरी जोड़ने की गति धीमी

- **Ollama**: मॉडल आकार जाँचें (`qwen2.5:3b` `7b` से 5-10 गुना तेज़ है), पुष्टि करें कि GPU का उपयोग हो रहा है (`ollama ps`)
- **GLM**: प्रत्येक add_episode के लिए 10-20+ LLM नेटवर्क राउंड ट्रिप की आवश्यकता होती है, छोटे टेक्स्ट ~22s सामान्य मान है
- **GROQ**: Rate Limit बड़ी संख्या में पुनः प्रयास का कारण बनेगा, बार-बार उपयोग होने पर GLM या Ollama पर स्विच करने की अनुशंसा की जाती है
- `background=true` का उपयोग अवरोधन से बचने के लिए करें
- लंबे टेक्स्ट को जल्दी विभाजित करने के लिए `GRAPHITI_CHUNK_THRESHOLD` कम करें

### PM2 समस्याएँ

```bash
pm2 status                                        # स्थिति जाँचें
pm2 logs graphiti-mcp-http --err --lines 50        # त्रुटि लॉग
lsof -i :8000                                     # पोर्ट कब्ज़ा जाँचें
pm2 delete graphiti-mcp-http && pm2 start ecosystem.config.cjs  # पूर्ण पुनः प्रारंभ
```

## विकास निदान उपकरण

```bash
uv run python tools/status_report.py           # एकीकृत स्थिति रिपोर्ट (Neo4j + Ollama + कॉन्फ़िगरेशन)
uv run python tools/validate_config.py         # .env और कॉन्फ़िगरेशन अखंडता सत्यापित करें
uv run python tools/performance_diagnose.py    # LLM प्रदर्शन निदान
uv run python tools/inspect_schema.py          # Neo4j इंडेक्स और बाधा जाँच
uv run python tools/migrate_embeddings.py      # Embedding मॉडल माइग्रेशन (मॉडल स्विच करने के बाद वेक्टर पुनः उत्पन्न करें)
```

### Embedding मॉडल माइग्रेशन

embedding मॉडल स्विच करने के बाद (जैसे `nomic-embed-text` → `bge-m3`), सभी मौजूदा वेक्टर को पुनः उत्पन्न करने के लिए माइग्रेशन उपकरण का उपयोग किया जा सकता है, जिससे खोज गुणवत्ता सुसंगत रहे:

```bash
# माइग्रेट करने के लिए आवश्यक मात्रा का पूर्वावलोकन करें
uv run python tools/migrate_embeddings.py --dry-run

# पूर्ण माइग्रेशन (ब्रेकपॉइंट निरंतरता का समर्थन)
uv run python tools/migrate_embeddings.py

# केवल निर्दिष्ट group माइग्रेट करें
uv run python tools/migrate_embeddings.py --group-id myproject

# ब्रेकपॉइंट से जारी रखें (रुकावट के बाद पुनः चलाएँ)
uv run python tools/migrate_embeddings.py --resume
```

> **संगतता**: `bge-m3` मूल रूप से 1024 आयाम, सिस्टम मौजूदा Neo4j वेक्टर इंडेक्स के अनुरूप होने के लिए स्वचालित रूप से 768 आयामों में काट देता है। माइग्रेशन से पहले और बाद का डेटा सह-अस्तित्व में रह सकता है, लेकिन सर्वोत्तम खोज गुणवत्ता प्राप्त करने के लिए पूर्ण माइग्रेशन निष्पादित करने की अनुशंसा की जाती है।

## दस्तावेज़

- [उपकरण उपयोग निर्देश](../使用工具的指令.md) — MCP उपकरण उपयोग गाइड और सर्वोत्तम अभ्यास
- [Graphiti Memory Rules](../graphiti-memory-rules.md) — मेमोरी नियम विवरण

## लाइसेंस

MIT License
