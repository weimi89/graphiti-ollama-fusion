# Graphiti MCP Server

บริการหน่วยความจำกราฟความรู้ (Knowledge Graph) — เซิร์ฟเวอร์ MCP ที่ผสานผู้ให้บริการ LLM หลายราย (Ollama / GLM / GROQ / OpenRouter / DeepSeek) เข้ากับฐานข้อมูลกราฟ Neo4j

พัฒนาต่อยอดจาก [getzep/graphiti](https://github.com/getzep/graphiti) รองรับการสลับระหว่าง Ollama ในเครื่องและ LLM บนคลาวด์ได้อย่างยืดหยุ่น และสามารถระบุผู้ให้บริการ Embedding แยกอิสระได้ (แยกขาดจาก LLM)

## คุณสมบัติเด่น

- **การจัดการหน่วยความจำอัจฉริยะ** — ใช้กราฟความรู้ในการจัดเก็บและสืบค้นความสัมพันธ์ของหน่วยความจำที่ซับซ้อน
- **การค้นหาเชิงความหมาย** — การค้นหาแบบผสมที่อิงกับเวกเตอร์ฝังตัว (เวกเตอร์ + คำสำคัญ + การท่องกราฟ)
- **กลยุทธ์การค้นหา 16 แบบ** — การค้นหาขั้นสูงรองรับวิธีจัดอันดับใหม่หลากหลายเช่น RRF, MMR, Cross-Encoder เป็นต้น
- **ผู้ให้บริการ LLM หลายราย** — รองรับ Ollama (ในเครื่อง), GLM (智谱 AI ฟรี), GROQ (การอนุมานความเร็วสูง), OpenRouter (รวมโมเดลจากหลายค่าย), DeepSeek (深度求索) สลับได้ในคลิกเดียวผ่านตัวแปรสภาพแวดล้อม
- **แยก Embedding ออกจาก LLM** — สามารถใช้ `EMBEDDING_PROVIDER` ระบุตัวสร้าง embedding แยกอิสระได้ LLM บนคลาวด์จะถอยกลับไปใช้ `bge-m3` ในเครื่องโดยอัตโนมัติ
- **การแยกงานสองโมเดล** — ในโหมด Ollama งานที่ซับซ้อนจะใช้โมเดลหลัก ส่วนงานที่ง่ายจะสลับไปใช้โมเดลเล็กโดยอัตโนมัติเพื่อเพิ่มประสิทธิภาพ
- **การตัดแบ่งเนื้อหาอัจฉริยะ** — ข้อความยาวจะถูกแบ่งเป็นส่วน ๆ โดยอัตโนมัติเพื่อลดภาระของ LLM (กำหนดค่าเกณฑ์ได้)
- **การประมวลผลหน่วยความจำเบื้องหลัง** — การเพิ่มหน่วยความจำสามารถทำงานในเบื้องหลังได้ การเรียก MCP จะส่งคืนผลทันที สถานะงานจะถูกบันทึกด้วย SQLite และงานที่ยังไม่เสร็จจะถูกกู้คืนอัตโนมัติหลังรีสตาร์ท
- **การกำจัดหน่วยความจำซ้ำ** — ตรวจจับหน่วยความจำเดิมที่มีความคล้ายคลึงกันสูงโดยอัตโนมัติ เพื่อหลีกเลี่ยงการจัดเก็บซ้ำ
- **การตรวจจับความขัดแย้ง** — ตรวจจับข้อเท็จจริงที่ขัดแย้งกันระหว่างสองเอนทิตี ระบุข้อมูลที่หมดอายุและที่ยังใช้ได้
- **การตรวจจับชุมชน (Community)** — จัดกลุ่มเอนทิตีที่เกี่ยวข้องโดยอัตโนมัติด้วยอัลกอริทึม Label Propagation
- **การติดตามความสำคัญ** — บันทึกความถี่ในการเข้าถึงเอนทิตีโดยอัตโนมัติ ผลการค้นหาจะเรียงลำดับตามความสำคัญ
- **การลืมอัจฉริยะ** — ระบุและล้างหน่วยความจำที่ล้าสมัยและมีปริมาณการเข้าถึงต่ำ เพื่อรักษากราฟให้กระชับ
- **การนำเข้าจำนวนมาก** — ส่งหน่วยความจำหลายรายการในครั้งเดียว เหมาะสำหรับการย้ายข้อมูลปริมาณมาก
- **ทริปเปิลเชิงโครงสร้าง** — เพิ่ม "ประธาน-ความสัมพันธ์-กรรม" โดยตรง ข้ามขั้นตอนการสกัดด้วย LLM เสร็จในพริบตา
- **อินเทอร์เฟซจัดการแบบ Web** — มีแดชบอร์ด การเรียกดู การค้นหา การแสดงผลกราฟความรู้ การถาม-ตอบด้วย AI การเรียกดูชุมชน การบำรุงรักษาคุณภาพ การนำเข้าแบบกลุ่ม และการตั้งค่าขณะทำงานในตัว
- **รองรับหลายภาษา (i18n)** — ข้อความตอบกลับรองรับ 33 ภาษา (รวมถึง zh-TW / en / zh-CN / ja / pt-BR / ko / es / de / fr ฯลฯ; zh-TW/en/zh-CN/ja เขียนด้วยมือ ส่วนที่เหลือให้บริการโดย generated layer); เครื่องมือ MCP อิงตาม `SERVER_LANG`, REST API เจรจาอัตโนมัติตาม HTTP `Accept-Language`
- **ธีมมืด/สว่าง** — อินเทอร์เฟซ Web รองรับการสลับธีม
- **โหมดปลอดภัย** — สามารถเลือกเพิ่มหน่วยความจำแบบรวดเร็วที่ข้ามการสกัดเอนทิตีได้
- **รองรับ Docker** — มี Dockerfile ในตัว รองรับการปรับใช้แบบคอนเทนเนอร์
- **ความปลอดภัยในการทำงานพร้อมกัน** — asyncio.Lock ปกป้องการเริ่มต้น ป้องกันสภาวะแข่งขัน (race condition)
- **การตรวจสุขภาพแบบหลายชั้น** — `/health` (liveness) + `/health/ready` (readiness)

## ความต้องการของระบบ

| รายการ | ความต้องการ |
|------|------|
| Python | 3.10+ (แนะนำ 3.11+) |
| Neo4j | 4.0+ (`bolt://localhost:7687`) |
| ผู้ให้บริการ LLM | Ollama / GLM / GROQ / OpenRouter / DeepSeek (เลือกหนึ่งจากห้า) |
| Node.js | 18+ (ใช้สำหรับการทำงานเบื้องหลังด้วย PM2 เท่านั้น ไม่บังคับ) |
| พื้นที่ดิสก์ | ~3GB (โมเดล Ollama + ข้อมูล Neo4j) |

### การเลือกผู้ให้บริการ LLM

สลับผ่านตัวแปรสภาพแวดล้อม `LLM_PROVIDER` (`ollama` / `glm` / `groq` / `openrouter` / `deepseek`):

| ผู้ให้บริการ | จุดเด่น | โมเดล LLM | Embedding | สถานการณ์ที่เหมาะสม |
|--------|------|----------|-----------|----------|
| **Ollama** (ค่าเริ่มต้น) | ในเครื่องทั้งหมด ข้อมูลไม่ออกจากเครื่อง | `qwen2.5:3b` | `bge-m3` (ภาษาจีน + RAG ยอดเยี่ยม) | มี GPU ให้ความสำคัญกับความเป็นส่วนตัว |
| **GLM** | คลาวด์ฟรี เสถียร ไม่จำกัดอัตรา | `glm-4-flash` (ฟรี) | `embedding-3` | ไม่มี GPU สถานการณ์ที่ค้นหาเข้มข้น |
| **GROQ** | การอนุมานความเร็วสูงพิเศษ | `llama-3.3-70b-versatile` | ถอยกลับไป Ollama `bge-m3` | เขียนเป็นครั้งคราว เน้นคุณภาพ |
| **OpenRouter** | รวมโมเดลจากหลายค่าย มีโควต้าฟรี | `stepfun/step-3.5-flash:free` ฯลฯ | ถอยกลับไป Ollama `bge-m3` | ต้องการใช้โมเดลคลาวด์เฉพาะ |
| **DeepSeek** | คลาวด์ 深度求索 คุ้มค่าสูง | `deepseek-v4-flash` / `deepseek-v4-pro` | ถอยกลับไป Ollama `bge-m3` | ความเข้าใจภาษาจีน คลาวด์ต้นทุนต่ำ |

> **แยก Embedding ออกจาก LLM**: ตัวสร้าง embedding ระบุแยกอิสระผ่าน `EMBEDDING_PROVIDER` (`ollama` / `glm`) เมื่อไม่ได้ตั้งค่าจะตามค่า `LLM_PROVIDER` ในความเป็นจริงมีเพียง `glm` เท่านั้นที่ใช้ GLM `embedding-3` ส่วนที่เหลือ (รวมถึง LLM บนคลาวด์ที่ไม่มี Embedding เช่น GROQ / OpenRouter / DeepSeek) จะใช้ Ollama `bge-m3` โดยอัตโนมัติทั้งหมด **ดังนั้นเมื่อใช้ LLM บนคลาวด์ใด ๆ ยังคงต้องมี Ollama ในเครื่องให้บริการ embedding (เว้นแต่ตั้งค่า embedding เป็น glm ด้วย)**

#### โหมด Ollama (ในเครื่อง)

```bash
# โมเดล LLM หลัก (แนะนำ qwen2.5:3b สมดุลความเร็วและความเสถียรดีที่สุด)
ollama pull qwen2.5:3b

# โมเดล embedding (จำเป็น ใช้สำหรับการค้นหาเวกเตอร์)
ollama pull bge-m3
```

> **ข้อควรระวังในการเลือกโมเดล**:
> - `qwen2.5:3b` — แนะนำ, ~2 วินาที/การเรียก, ~100 t/s, ผลลัพธ์เชิงโครงสร้างของ graphiti-core เสถียร 100%
> - `qwen2.5:7b` — ผลลัพธ์ดีกว่าแต่ช้ากว่า 5-10 เท่า เหมาะสำหรับสถานการณ์ที่เน้นคุณภาพ
> - `qwen2.5:1.5b` — เร็วที่สุดแต่**ไม่เสถียร** (อัตราความสำเร็จของ JSON เชิงโครงสร้างเพียง 33%) ไม่แนะนำให้ใช้

#### โหมด GLM (智谱 AI คลาวด์)

```bash
# การตั้งค่า .env
LLM_PROVIDER=glm
GLM_API_KEY=your_api_key          # รับได้จาก https://open.bigmodel.cn
GLM_MODEL=glm-4-flash             # โมเดลฟรี
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768      # ต้องตรงกับมิติของดัชนีเวกเตอร์ Neo4j
```

> **ข้อมูลอ้างอิงประสิทธิภาพ GLM**: การเขียน ~22 วินาที (ข้อความสั้น), การค้นหา ~0.34 วินาที, ข้อผิดพลาด Rate Limit เป็นศูนย์, ช้ากว่า Ollama ในเครื่อง 2-5 เท่าแต่ฟรีโดยสมบูรณ์

#### โหมด GROQ (การอนุมานความเร็วสูง)

```bash
# การตั้งค่า .env
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key         # รับได้จาก https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile
```

> **หมายเหตุ**: GROQ ไม่ให้บริการ Embedding จำเป็นต้องใช้ร่วมกับตัวสร้าง embedding ของ Ollama (ถอยกลับโดยอัตโนมัติ) หรือตั้งค่า `EMBEDDING_PROVIDER` เป็น glm GROQ มี Rate Limit ที่เข้มงวด การใช้งานความถี่สูงจะกระตุ้นการลองใหม่จำนวนมาก

#### โหมด OpenRouter (รวมโมเดลจากหลายค่าย)

```bash
# การตั้งค่า .env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_api_key       # รับได้จาก https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free   # เปลี่ยนเป็นโมเดล OpenRouter ใดก็ได้
```

> **หมายเหตุ**: OpenRouter ไม่ให้บริการ Embedding จะถอยกลับไปใช้ Ollama `bge-m3` โดยอัตโนมัติ ดูรายการโมเดลได้ที่ https://openrouter.ai/models (มีโมเดลฟรี `:free` หลายตัว)

#### โหมด DeepSeek (深度求索)

```bash
# การตั้งค่า .env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key         # รับได้จาก https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash      # แนะนำ; หรือ deepseek-v4-pro (ผลลัพธ์ดีกว่า)
```

> **หมายเหตุ**: DeepSeek ไม่ให้บริการ Embedding จะถอยกลับไปใช้ Ollama `bge-m3` โดยอัตโนมัติ `deepseek-chat` / `deepseek-reasoner` จะถูกปลดระวางในวันที่ 2026-07-24 แนะนำให้เปลี่ยนไปใช้ `deepseek-v4-flash` / `deepseek-v4-pro` DeepSeek กำหนดอย่างเข้มงวดว่า prompt ในโหมด `json_object` ต้องมีสตริง "json" ไคลเอนต์มีการป้องกันสำรองในตัวแล้ว ไม่ต้องตั้งค่าเพิ่มเติม

## เริ่มต้นใช้งานอย่างรวดเร็ว

### 1. การเตรียมการล่วงหน้า

ยืนยันว่า Neo4j ทำงานอยู่บนเครื่อง และเตรียมบริการที่สอดคล้องตามผู้ให้บริการ LLM ที่เลือก:

```bash
# ยืนยันว่า Neo4j กำลังทำงาน (จำเป็น)
neo4j status
# หรือใช้ Docker: docker run -d -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/your_password neo4j:latest

# โหมด Ollama: ยืนยันว่า Ollama กำลังทำงาน
ollama list
# หากยังไม่ได้เริ่ม: ollama serve

# โหมด GLM / GROQ: ต้องการเพียง API Key ที่ใช้ได้ ไม่ต้องมีบริการในเครื่อง
```

### 2. ติดตั้ง dependencies

```bash
git clone <repo-url>
cd graphiti
uv sync
```

> **หมายเหตุ**: โปรเจกต์นี้ใช้ [uv](https://github.com/astral-sh/uv) ในการจัดการ dependencies หากยังไม่ได้ติดตั้ง: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 3. กำหนดค่าสภาพแวดล้อม

```bash
cp .env.example .env
```

แก้ไข `.env` โดย**อย่างน้อย**ต้องแก้ไขรายการต่อไปนี้:

```bash
NEO4J_PASSWORD=your_actual_password  # จำเป็น: รหัสผ่าน Neo4j
LLM_PROVIDER=ollama                  # ollama / glm / groq / openrouter / deepseek
OLLAMA_MODEL=qwen2.5:3b              # โหมด Ollama: โมเดล LLM ในเครื่อง
# GLM_API_KEY=your_key               # โหมด GLM: 智谱 AI API Key
# GROQ_API_KEY=your_key              # โหมด GROQ: GROQ API Key
# OPENROUTER_API_KEY=your_key        # โหมด OpenRouter: API Key
# DEEPSEEK_API_KEY=your_key          # โหมด DeepSeek: API Key
```

### 4. เริ่มบริการ

```bash
# โหมด HTTP (แนะนำ มีอินเทอร์เฟซจัดการแบบ Web)
uv run python graphiti_mcp_server.py --transport http --port 8000

# หรือใช้ PM2 ทำงานเบื้องหลัง (แนะนำสำหรับการทำงานระยะยาว)
pm2 start ecosystem.config.cjs
```

### 5. ตรวจสอบบริการ

หลังจากเริ่มแล้วสามารถเข้าถึงปลายทางต่อไปนี้:

| ปลายทาง | คำอธิบาย |
|------|------|
| http://localhost:8000/ | อินเทอร์เฟซจัดการแบบ Web |
| http://localhost:8000/mcp | ปลายทาง MCP (สำหรับให้ไคลเอนต์ MCP เชื่อมต่อ) |
| http://localhost:8000/health | การตรวจสุขภาพ (liveness) |
| http://localhost:8000/health/ready | การตรวจสอบเชิงลึก (รวมการเชื่อมต่อ Neo4j) |
| http://localhost:8000/api/stats | สถิติ REST API |

## โครงสร้างโปรเจกต์

```
graphiti/
├── graphiti_mcp_server.py        # จุดเข้าหลัก — นิยามเครื่องมือ MCP (19 เครื่องมือ)
├── src/
│   ├── config.py                 # การจัดการการตั้งค่า (GraphitiConfig, รองรับการซ้อนทับ JSON/.env)
│   ├── web_api.py                # REST API ของอินเทอร์เฟซจัดการแบบ Web (30+ ปลายทาง)
│   ├── ollama_graphiti_client.py  # ไคลเอนต์ LLM Ollama (การแยกงานสองโมเดล)
│   ├── openai_compat_client.py   # คลาสฐาน LLM ที่เข้ากันได้กับ OpenAI (json_object + schema แบบย่อ + การป้องกัน json)
│   ├── glm_client.py             # ไคลเอนต์ LLM GLM (智谱 AI) (สืบทอดจาก OpenAICompatClient)
│   ├── openrouter_client.py      # ไคลเอนต์ LLM OpenRouter (สืบทอดจาก OpenAICompatClient)
│   ├── deepseek_client.py        # ไคลเอนต์ LLM DeepSeek (สืบทอดจาก OpenAICompatClient)
│   ├── ollama_embedder.py        # อะแดปเตอร์โมเดล embedding Ollama
│   ├── content_preprocessor.py   # การตัดแบ่งเนื้อหาอัจฉริยะ (ข้อความยาวแบ่งส่วนอัตโนมัติ)
│   ├── deduplication.py          # การกำจัดหน่วยความจำซ้ำ (เปรียบเทียบความคล้ายเชิงโคไซน์)
│   ├── importance.py             # การติดตามความสำคัญและการลืมอัจฉริยะ
│   ├── safe_memory_add.py        # การเพิ่มหน่วยความจำแบบปลอดภัย (ข้ามการสกัดเอนทิตี)
│   ├── task_store.py             # การบันทึกงานเบื้องหลังด้วย SQLite (TaskStore)
│   ├── timezone_utils.py         # การแปลงเขตเวลา (UTC→แสดงเขตเวลาท้องถิ่น)
│   ├── i18n.py                   # หลายภาษาฝั่งแบ็กเอนด์ (REST อิงตาม Accept-Language, MCP อิงตาม SERVER_LANG)
│   ├── i18n_generated.py         # การครอบคลุมภาษาที่สร้างขึ้นอัตโนมัติ (GENERATED_MESSAGE_OVERRIDES)
│   ├── exceptions.py             # การจัดการข้อยกเว้นเชิงโครงสร้าง (12 ประเภทข้อยกเว้น)
│   └── logging_setup.py          # ระบบบันทึก (หมุนเวียนตามเวลา + การตรวจสอบประสิทธิภาพ)
├── web/                          # ฟรอนต์เอนด์อินเทอร์เฟซจัดการแบบ Web (SPA, ไม่มี build)
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js                # การห่อหุ้ม REST API
│       ├── components.js         # การเรนเดอร์คอมโพเนนต์ UI (รวมหน้าชุมชน)
│       └── app.js                # การกำหนดเส้นทาง SPA, การจัดการสถานะ
├── tests/                        # ชุดทดสอบ (203 การทดสอบ)
│   ├── test_content_preprocessor.py  # การทดสอบตรรกะการตัดแบ่ง (17 รายการ)
│   ├── test_new_features.py      # การทดสอบฟีเจอร์ใหม่ (32 รายการ)
│   ├── test_i18n.py             # การทดสอบหลายภาษา (57 รายการ)
│   ├── test_unit.py              # การทดสอบหน่วย
│   ├── test_web_api.py           # การทดสอบ Web API
│   ├── test_web_ui_features.py   # การทดสอบฟีเจอร์ Web UI
│   ├── test_integration_manual.py # การทดสอบการรวมแบบแมนนวล
│   └── bench_deepseek_flash_vs_pro.py # สคริปต์เกณฑ์มาตรฐานประสิทธิภาพ DeepSeek flash/pro
├── tools/                        # เครื่องมือวินิจฉัยสำหรับการพัฒนา
│   ├── status_report.py          # รายงานสถานะแบบรวม
│   ├── validate_config.py        # การตรวจสอบการตั้งค่า
│   ├── performance_diagnose.py   # การวินิจฉัยประสิทธิภาพ
│   ├── inspect_schema.py         # การตรวจสอบโครงสร้าง Neo4j
│   ├── batch_reprocess.py        # การประมวลผลใหม่แบบกลุ่ม
│   └── migrate_embeddings.py     # การย้ายโมเดล Embedding (สร้างเวกเตอร์ใหม่หลังเปลี่ยนโมเดล)
├── docs/                         # เอกสาร
├── logs/                         # บันทึก (หมุนเวียนตามเวลา ค่าเริ่มต้นเก็บ 30 วัน)
├── Dockerfile                    # การปรับใช้แบบคอนเทนเนอร์ Docker
└── ecosystem.config.cjs          # การตั้งค่า PM2
```

## การตั้งค่าไคลเอนต์ MCP

### โหมด HTTP (แนะนำ)

เหมาะสำหรับไคลเอนต์ MCP ที่รองรับ HTTP เช่น Claude Code, Cline:

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

### โหมด STDIO

เหมาะสำหรับไคลเอนต์ที่ต้องเริ่มกระบวนการโดยตรง เช่น Claude Desktop:

**ตำแหน่งไฟล์การตั้งค่า:**
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

> **หมายเหตุ**: โหมด SSE (`--transport sse`) ไม่แนะนำให้ใช้แล้ว MCP 1.x มีปัญหาความเข้ากันได้ในการเริ่มต้น session โปรดเปลี่ยนไปใช้โหมด HTTP

## เครื่องมือ MCP (19 เครื่องมือ)

### การจัดการหน่วยความจำ (7 เครื่องมือ)

| เครื่องมือ | คำอธิบาย |
|------|------|
| `add_memory_simple` | เพิ่มหน่วยความจำเข้าสู่กราฟความรู้ (รองรับการประมวลผลเบื้องหลัง การตัดแบ่งอัจฉริยะ การตรวจสอบความซ้ำ) |
| `add_episode_bulk` | เพิ่มหน่วยความจำหลายรายการแบบกลุ่ม (ค่าเริ่มต้นประมวลผลเบื้องหลัง) |
| `add_triplet` | เพิ่มทริปเปิลเชิงโครงสร้าง (ข้าม LLM เสร็จในพริบตา) |
| `search_memory_nodes` | ค้นหาโหนดหน่วยความจำ (รองรับกลยุทธ์การค้นหา 16 แบบ การกรองตามเวลา) |
| `search_memory_facts` | ค้นหาข้อเท็จจริงในหน่วยความจำ (รองรับการกรองประเภทความสัมพันธ์ ช่วงเวลา การกรองความถูกต้อง) |
| `advanced_search` | การค้นหาขั้นสูง (16 กลยุทธ์ ส่งคืนโหนด+ขอบ+ชุมชน+ส่วนความจำ) |
| `get_episodes` | ดึงส่วนความจำล่าสุด |

### การวิเคราะห์ความรู้ (3 เครื่องมือ)

| เครื่องมือ | คำอธิบาย |
|------|------|
| `check_conflicts` | ตรวจจับความขัดแย้งของข้อเท็จจริงระหว่างสองเอนทิตี (ใช้ได้ vs หมดอายุ) |
| `get_node_edges` | สำรวจความสัมพันธ์ขอบขาเข้าและขอบขาออกของโหนด |
| `build_communities` | กระตุ้นการตรวจจับและจัดกลุ่มชุมชน (ค่าเริ่มต้นประมวลผลเบื้องหลัง) |

### การบำรุงรักษาหน่วยความจำ (2 เครื่องมือ)

| เครื่องมือ | คำอธิบาย |
|------|------|
| `get_stale_memories` | สอบถามหน่วยความจำที่ล้าสมัยและมีปริมาณการเข้าถึงต่ำ |
| `cleanup_stale_memories` | ล้างหน่วยความจำที่ล้าสมัย (ค่าเริ่มต้นโหมดดูตัวอย่าง dry_run) |

### การจัดการงาน

| เครื่องมือ | คำอธิบาย |
|------|------|
| `get_memory_task_status` | สอบถามความคืบหน้าและผลลัพธ์ของงานประมวลผลหน่วยความจำเบื้องหลัง |

### การลบและการสอบถาม

| เครื่องมือ | คำอธิบาย |
|------|------|
| `delete_episode` | ลบส่วนความจำ |
| `delete_entity_edge` | ลบขอบเอนทิตี (ความสัมพันธ์) |
| `get_entity_edge` | ดึงข้อมูลรายละเอียดขอบเอนทิตี |

### การจัดการระบบ

| เครื่องมือ | คำอธิบาย |
|------|------|
| `get_status` | ดึงสถานะบริการ (Neo4j, LLM, ตัวสร้าง embedding) |
| `test_connection` | ทดสอบการเชื่อมต่อ Neo4j / LLM / ตัวสร้าง embedding |
| `clear_graph` | ล้างฐานข้อมูลกราฟ (รองรับการล้างตาม group_id) |

## พารามิเตอร์ของเครื่องมือ

### add_memory_simple

| พารามิเตอร์ | ประเภท | จำเป็น | ค่าเริ่มต้น | คำอธิบาย |
|------|------|------|--------|------|
| `name` | string | Y | | ชื่อหน่วยความจำ |
| `episode_body` | string | Y | | เนื้อหาหน่วยความจำ (เกิน 800 อักขระจะตัดแบ่งอัตโนมัติ) |
| `group_id` | string | | `"default"` | ID กลุ่ม (แนะนำให้แยกตามโปรเจกต์) |
| `source` | string | | `"text"` | ประเภทแหล่งที่มา: `text` / `json` / `message` |
| `source_description` | string | | `"MCP Server"` | คำอธิบายแหล่งที่มา |
| `use_safe_mode` | bool | | `false` | โหมดปลอดภัย (ข้ามการสกัดเอนทิตี เร็วแต่หน่วยความจำค้นหาไม่ได้) |
| `background` | bool | | `false` | การประมวลผลเบื้องหลัง (ส่งคืน task_id ทันที เหมาะกับข้อความยาว) |
| `force` | bool | | `false` | ข้ามการตรวจสอบความซ้ำ (บังคับเพิ่ม) |
| `excluded_entity_types` | list | | | ประเภทเอนทิตีที่ยกเว้น (ลดปริมาณการสกัดที่ไม่ต้องการ) |

> **คำแนะนำด้านประสิทธิภาพ**:
> - ข้อความสั้น (<800 อักขระ): ประมวลผลโดยตรง โดยทั่วไปเสร็จใน 30-40 วินาที
> - ข้อความยาว (>800 อักขระ): ตัดแบ่งเป็นหลายส่วนอัตโนมัติ ใช้ `add_episode_bulk` ประมวลผลพร้อมกัน (เร็วกว่าแบบอนุกรม ~33%)
> - ใช้ `background=true` เพื่อหลีกเลี่ยงการบล็อกการเรียก MCP ติดตามความคืบหน้าผ่าน `get_memory_task_status`
> - `use_safe_mode=true` เสร็จในพริบตาแต่เครื่องมือ search ค้นหาหน่วยความจำไม่ได้
> - เมื่อเปิดการกำจัดความซ้ำ หน่วยความจำที่คล้ายคลึงกันสูงจะถูกเตือน (`force=true` ข้ามได้)

### add_episode_bulk

| พารามิเตอร์ | ประเภท | จำเป็น | ค่าเริ่มต้น | คำอธิบาย |
|------|------|------|--------|------|
| `episodes` | list | Y | | รายการหน่วยความจำ แต่ละรายการมี `name` และ `content` |
| `group_id` | string | | `"default"` | ID กลุ่ม |
| `source` | string | | `"text"` | ประเภทแหล่งที่มา |
| `background` | bool | | `true` | การประมวลผลเบื้องหลัง (แบบกลุ่มมักใช้เวลานาน) |

### add_triplet

| พารามิเตอร์ | ประเภท | จำเป็น | ค่าเริ่มต้น | คำอธิบาย |
|------|------|------|--------|------|
| `source_name` | string | Y | | ชื่อเอนทิตีต้นทาง (เช่น "Alice") |
| `target_name` | string | Y | | ชื่อเอนทิตีปลายทาง (เช่น "Google") |
| `relation_name` | string | Y | | ชื่อความสัมพันธ์ (เช่น "works_at") |
| `fact` | string | Y | | คำอธิบายข้อเท็จจริง (เช่น "Alice works at Google") |
| `group_id` | string | | `"default"` | ID กลุ่ม |
| `source_labels` | list | | | ป้ายกำกับเอนทิตีต้นทาง |
| `target_labels` | list | | | ป้ายกำกับเอนทิตีปลายทาง |

### search_memory_nodes

| พารามิเตอร์ | ประเภท | จำเป็น | ค่าเริ่มต้น | คำอธิบาย |
|------|------|------|--------|------|
| `query` | string | Y | | คำสำคัญในการค้นหา (ภาษาธรรมชาติ) |
| `max_nodes` | int | | `10` | จำนวนสูงสุดที่ส่งคืน |
| `group_ids` | list | | | การกรองกลุ่ม (ค้นหาหลายกลุ่มรวมกัน) |
| `entity_types` | list | | | การกรองประเภทเอนทิตี |
| `search_recipe` | string | | | กลยุทธ์การค้นหา (ดูการค้นหาขั้นสูง) |
| `created_after` | string | | | ขอบล่างของเวลาสร้าง (ISO datetime) |
| `created_before` | string | | | ขอบบนของเวลาสร้าง (ISO datetime) |

### search_memory_facts

| พารามิเตอร์ | ประเภท | จำเป็น | ค่าเริ่มต้น | คำอธิบาย |
|------|------|------|--------|------|
| `query` | string | Y | | คำสำคัญในการค้นหา |
| `max_facts` | int | | `10` | จำนวนสูงสุดที่ส่งคืน |
| `group_ids` | list | | | การกรองกลุ่ม |
| `center_node_uuid` | string | | | UUID ของโหนดศูนย์กลาง (สำรวจความสัมพันธ์ของโหนดเฉพาะ) |
| `edge_types` | list | | | การกรองประเภทความสัมพันธ์ (เช่น `["works_at"]`) |
| `created_after` | string | | | ขอบล่างของเวลาสร้าง (ISO datetime) |
| `created_before` | string | | | ขอบบนของเวลาสร้าง (ISO datetime) |
| `only_valid` | bool | | `false` | ส่งคืนเฉพาะข้อเท็จจริงที่ยังไม่หมดอายุ |

### advanced_search

| พารามิเตอร์ | ประเภท | จำเป็น | ค่าเริ่มต้น | คำอธิบาย |
|------|------|------|--------|------|
| `query` | string | Y | | คำสำคัญในการค้นหา |
| `search_recipe` | string | | `"combined_rrf"` | กลยุทธ์การค้นหา (เลือกได้ 16 แบบ) |
| `max_results` | int | | `10` | จำนวนสูงสุดที่ส่งคืน |
| `group_ids` | list | | | การกรองกลุ่ม |
| `center_node_uuid` | string | | | UUID ของโหนดศูนย์กลาง |

**กลยุทธ์การค้นหาที่ใช้ได้ (search_recipe):**

| ประเภท | กลยุทธ์ | คำอธิบาย |
|------|------|------|
| รวม | `combined_rrf` | การหลอมรวม RRF แบบรวม (ค่าเริ่มต้น แนะนำ) |
| รวม | `combined_mmr` | การจัดอันดับใหม่เพื่อความหลากหลายแบบ MMR รวม |
| รวม | `combined_cross_encoder` | การจัดอันดับละเอียด Cross-Encoder รวม |
| ขอบ | `edge_rrf` / `edge_mmr` / `edge_cross_encoder` | การค้นหาขอบ (การจัดเรียง 3 แบบ) |
| ขอบ | `edge_node_distance` / `edge_episode_mentions` | การค้นหาขอบ (ระยะทางกราฟ/จำนวนการอ้างอิง) |
| โหนด | `node_rrf` / `node_mmr` / `node_cross_encoder` | การค้นหาโหนด (การจัดเรียง 3 แบบ) |
| โหนด | `node_node_distance` / `node_episode_mentions` | การค้นหาโหนด (ระยะทางกราฟ/จำนวนการอ้างอิง) |
| ชุมชน | `community_rrf` / `community_mmr` / `community_cross_encoder` | การค้นหาชุมชน |

### check_conflicts

| พารามิเตอร์ | ประเภท | จำเป็น | ค่าเริ่มต้น | คำอธิบาย |
|------|------|------|--------|------|
| `source_name` | string | Y | | ชื่อเอนทิตีต้นทาง |
| `target_name` | string | Y | | ชื่อเอนทิตีปลายทาง |
| `group_id` | string | | `"default"` | ID กลุ่ม |

### get_node_edges

| พารามิเตอร์ | ประเภท | จำเป็น | ค่าเริ่มต้น | คำอธิบาย |
|------|------|------|--------|------|
| `node_uuid` | string | Y | | UUID ของโหนด |
| `include_inbound` | bool | | `true` | รวมขอบขาเข้า |
| `include_outbound` | bool | | `true` | รวมขอบขาออก |
| `max_edges` | int | | `50` | จำนวนสูงสุดที่ส่งคืน |

### build_communities

| พารามิเตอร์ | ประเภท | จำเป็น | ค่าเริ่มต้น | คำอธิบาย |
|------|------|------|--------|------|
| `group_ids` | list | | | ระบุกลุ่ม (เว้นว่างคือทั้งหมด) |
| `background` | bool | | `true` | การประมวลผลเบื้องหลัง |

### get_stale_memories

| พารามิเตอร์ | ประเภท | จำเป็น | ค่าเริ่มต้น | คำอธิบาย |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | ไม่ถูกเข้าถึงเกินกี่วันถือว่าล้าสมัย |
| `min_access_count` | int | | `2` | จำนวนการเข้าถึงต่ำกว่าค่านี้จึงจะรวมเข้ามา |
| `group_id` | string | | | การกรองกลุ่ม |
| `limit` | int | | `50` | จำนวนสูงสุดที่ส่งคืน |

### cleanup_stale_memories

| พารามิเตอร์ | ประเภท | จำเป็น | ค่าเริ่มต้น | คำอธิบาย |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | เกณฑ์จำนวนวันที่ล้าสมัย |
| `min_access_count` | int | | `2` | เกณฑ์จำนวนการเข้าถึงต่ำสุด |
| `group_id` | string | | | การกรองกลุ่ม |
| `dry_run` | bool | | `true` | โหมดดูตัวอย่าง (ไม่ลบจริง) |
| `limit` | int | | `50` | จำนวนสูงสุดที่ประมวลผล |

### get_memory_task_status

| พารามิเตอร์ | ประเภท | จำเป็น | คำอธิบาย |
|------|------|------|------|
| `task_id` | string | Y | ID งานเบื้องหลัง (ส่งคืนโดย `add_memory_simple(background=true)`) |

## อินเทอร์เฟซจัดการแบบ Web

ในโหมด HTTP เข้าถึง `http://localhost:8000/` ก็สามารถใช้งานได้

**คุณสมบัติ:**
- แดชบอร์ด — สถิติจำนวนโหนด จำนวนข้อเท็จจริง จำนวนส่วนความจำ
- โหนดเอนทิตี — เรียกดู กรอง ค้นหาเวกเตอร์
- ความสัมพันธ์ข้อเท็จจริง — เรียกดู กรอง ค้นหาเวกเตอร์
- ส่วนความจำ — เรียกดู ค้นหาแบบเต็มข้อความ ลบ
- การเรียกดูชุมชน — รายการโหนดชุมชน สรุป กระตุ้นการสร้างชุมชน
- ฟอร์มทริปเปิล — เพิ่มความรู้เชิงโครงสร้าง "ประธาน-ความสัมพันธ์-กรรม" โดยตรง
- การจัดการ Group — กรองตามกลุ่ม ลบแบบกลุ่ม
- การแสดงผลกราฟความรู้ — แสดงความสัมพันธ์ของโหนดในรูปแบบกราฟิก
- การถาม-ตอบด้วย AI — การถาม-ตอบอัจฉริยะที่อิงกับกราฟความรู้
- การบำรุงรักษาคุณภาพ — ตัวชี้วัดคุณภาพหน่วยความจำและเครื่องมือทำความสะอาด
- การนำเข้าแบบกลุ่ม — นำเข้าหน่วยความจำหลายรายการในครั้งเดียว (JSON สูงสุด 500 รายการ)
- การตั้งค่าขณะทำงาน — ดูการตั้งค่าที่มีผลอยู่และปรับบางพารามิเตอร์โดยไม่ต้องรีสตาร์ท
- การสลับธีม — ธีมมืด/สว่าง

**REST API:**

| ปลายทาง | เมธอด | คำอธิบาย |
|------|------|------|
| `/api/stats` | GET | สถิติแดชบอร์ด |
| `/api/groups` | GET | ดึง group_id ทั้งหมด |
| `/api/groups/stats` | GET | สถิติโหนด/ข้อเท็จจริง/ส่วนความจำของแต่ละ group |
| `/api/nodes` | GET | เรียกดูโหนดเอนทิตี (แบ่งหน้า) |
| `/api/facts` | GET | เรียกดูข้อเท็จจริง (แบ่งหน้า) |
| `/api/episodes` | GET | เรียกดูส่วนความจำ (แบ่งหน้า) |
| `/api/nodes/{uuid}/relations` | GET | ดึงความสัมพันธ์ขอบขาเข้า/ขาออกของโหนด |
| `/api/search/nodes` | GET | ค้นหาเวกเตอร์โหนด |
| `/api/search/facts` | GET | ค้นหาเวกเตอร์ข้อเท็จจริง |
| `/api/search/episodes` | GET | ค้นหาส่วนความจำ |
| `/api/search/advanced` | GET | การค้นหาขั้นสูง (16 กลยุทธ์) |
| `/api/communities` | GET | เรียกดูโหนดชุมชน (แบ่งหน้า) |
| `/api/communities/build` | POST | กระตุ้นการสร้างชุมชน |
| `/api/memory/add` | POST | เพิ่มหน่วยความจำรายการเดียว |
| `/api/memory/add-bulk` | POST | เพิ่มหน่วยความจำแบบกลุ่ม |
| `/api/memory/add-triplet` | POST | เพิ่มทริปเปิล |
| `/api/import/episodes` | POST | นำเข้าส่วนความจำแบบกลุ่ม (JSON สูงสุด 500 รายการ) |
| `/api/memory/tasks` | GET | แสดงรายการงานเบื้องหลัง (รองรับการกรองสถานะ) |
| `/api/memory/tasks/{id}` | GET | สอบถามสถานะงานเดี่ยว |
| `/api/timeline` | GET | เรียกดูตามเส้นเวลา |
| `/api/graph/subgraph` | GET | ดึงกราฟย่อย (การแสดงผล) |
| `/api/graph/all` | GET | ดึงกราฟทั้งหมด (การแสดงผล) |
| `/api/ask` | GET | การถาม-ตอบด้วย AI (อิงการสืบค้นจากกราฟ) |
| `/api/analytics/top-nodes` | GET | โหนดที่มีการเชื่อมต่อสูง/เข้าถึงบ่อย |
| `/api/analytics/quality` | GET | ตัวชี้วัดคุณภาพกราฟความรู้ |
| `/api/analytics/stale` | GET | สอบถามหน่วยความจำที่ล้าสมัย |
| `/api/analytics/cleanup` | POST | ล้างหน่วยความจำที่ล้าสมัย |
| `/api/config` | GET | ดึงการตั้งค่าที่มีผลอยู่ (ไม่รวม API key) |
| `/api/config` | PATCH | อัปเดตการตั้งค่าที่แก้ไขได้ขณะทำงาน (มีผลเฉพาะกระบวนการนี้ รีสตาร์ทจะคืนค่า) |
| `/api/nodes/{uuid}` | DELETE | ลบโหนด |
| `/api/episodes/{uuid}` | DELETE | ลบส่วนความจำ |
| `/api/facts/{uuid}` | DELETE | ลบข้อเท็จจริง |
| `/api/groups/{group_id}` | DELETE | ลบทั้ง group |

## การกำหนดค่า

### ตัวแปรสภาพแวดล้อม (.env)

การกำหนดค่าใช้กลไกการซ้อนทับ: ไฟล์การตั้งค่า JSON เป็นพื้นฐาน ตัวแปรสภาพแวดล้อมเขียนทับค่าแต่ละรายการ

```bash
# === จำเป็น ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password        # ต้องแก้ไข

# === การเลือกผู้ให้บริการ LLM ===
LLM_PROVIDER=ollama                 # ollama / glm / groq / openrouter / deepseek

# === ผู้ให้บริการ Embedding (ไม่บังคับ ค่าเริ่มต้นตาม LLM_PROVIDER) ===
# มีเพียง glm เท่านั้นที่ใช้ GLM Embedding ส่วนที่เหลือใช้ Ollama bge-m3 ทั้งหมด
# EMBEDDING_PROVIDER=ollama         # ollama / glm

# === การตั้งค่า Ollama (ใช้เมื่อ LLM_PROVIDER=ollama) ===
OLLAMA_MODEL=qwen2.5:3b             # โมเดลหลัก (แนะนำ qwen2.5:3b)
OLLAMA_SMALL_MODEL=qwen2.5:3b       # โมเดลเล็ก (ใช้กับงานง่าย เลือกโมเดลต่างกันได้)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.1

# === การตั้งค่า GLM (ใช้เมื่อ LLM_PROVIDER=glm) ===
GLM_API_KEY=your_api_key            # รับได้จาก https://open.bigmodel.cn
GLM_MODEL=glm-4-flash               # โมเดลฟรี
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768

# === การตั้งค่า GROQ (ใช้เมื่อ LLM_PROVIDER=groq) ===
GROQ_API_KEY=your_api_key           # รับได้จาก https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile

# === การตั้งค่า OpenRouter (ใช้เมื่อ LLM_PROVIDER=openrouter) ===
OPENROUTER_API_KEY=your_api_key     # รับได้จาก https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free

# === การตั้งค่า DeepSeek (ใช้เมื่อ LLM_PROVIDER=deepseek) ===
DEEPSEEK_API_KEY=your_api_key       # รับได้จาก https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash    # หรือ deepseek-v4-pro

# === โมเดล embedding Ollama (ใช้ทุกครั้งที่ไม่ใช่การ embed ด้วย glm) ===
OLLAMA_EMBEDDING_MODEL=bge-m3
OLLAMA_EMBEDDING_DIMENSIONS=768

# === การแสดงผลและภาษา (ไม่บังคับ) ===
GRAPHITI_DISPLAY_TIMEZONE=Asia/Taipei # เขตเวลาแสดงผลของ timestamp ที่ API ส่งคืน (ชื่อ IANA; การจัดเก็บยังคงเป็น UTC)
SERVER_LANG=zh-TW                     # ภาษาตอบกลับของเครื่องมือ MCP (locale ครบถ้วนดู src/i18n.py); REST API เปลี่ยนไปอิงตาม Accept-Language

# === ประสิทธิภาพหน่วยความจำ (ไม่บังคับ) ===
GRAPHITI_CHUNK_THRESHOLD=800         # เกณฑ์จำนวนอักขระที่กระตุ้นการตัดแบ่งอัจฉริยะ
GRAPHITI_MAX_CHUNK_SIZE=600          # จำนวนอักขระสูงสุดต่อส่วน
GRAPHITI_MAX_COROUTINES=10            # จำนวน coroutine ขนานสูงสุด
GRAPHITI_DEFAULT_BACKGROUND=false    # ประมวลผลเบื้องหลังเป็นค่าเริ่มต้นหรือไม่
TASK_DB_PATH=data/tasks.db           # เส้นทางบันทึกงานเบื้องหลังด้วย SQLite

# === การติดตามความสำคัญและการลืมอัจฉริยะ (ไม่บังคับ) ===
ENABLE_IMPORTANCE_TRACKING=true      # เปิดการติดตามการเข้าถึง
IMPORTANCE_WEIGHT=0.1                # น้ำหนักความสำคัญ
STALE_DAYS_THRESHOLD=30              # เกณฑ์จำนวนวันที่ล้าสมัย
STALE_MIN_ACCESS_COUNT=2             # จำนวนการเข้าถึงต่ำสุด

# === บันทึก ===
LOG_FILE=logs/graphiti_mcp_server.log
LOG_LEVEL=INFO
```

> **รายการตัวแปรสภาพแวดล้อมครบถ้วน**โปรดดู `.env.example`

### ไฟล์การตั้งค่า JSON

เหมาะสำหรับการตั้งค่าที่ต้องการการควบคุมเวอร์ชัน (ตัวแปรสภาพแวดล้อมยังคงเขียนทับได้):

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

## การทำงานเบื้องหลังด้วย PM2

```bash
npm install -g pm2

pm2 start ecosystem.config.cjs      # เริ่ม
pm2 status                           # สถานะ
pm2 logs graphiti-mcp-http           # บันทึกแบบเรียลไทม์
pm2 restart graphiti-mcp-http --update-env  # รีสตาร์ท (โหลด .env ใหม่)

pm2 save && pm2 startup              # ตั้งค่าให้เริ่มอัตโนมัติเมื่อเปิดเครื่อง
```

> **คำแนะนำ**: หลังแก้ไข `.env` ต้องใช้แฟล็ก `--update-env` ในการรีสตาร์ท ไม่เช่นนั้นตัวแปรสภาพแวดล้อมจะไม่อัปเดต

## การปรับใช้ Docker

```bash
docker build -t graphiti-mcp .

# หมายเหตุ: คอนเทนเนอร์ Docker ต้องสามารถเชื่อมต่อกับ Neo4j และ Ollama ได้
# ใช้ host network ง่ายที่สุด
docker run -p 8000:8000 --env-file .env --network host graphiti-mcp

# หรือระบุที่อยู่บริการภายนอกอย่างชัดเจน
docker run -p 8000:8000 \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --env-file .env graphiti-mcp
```

## การทดสอบ

```bash
# รันการทดสอบทั้งหมด (203 รายการ ประมาณ 1 วินาที)
uv run python -m pytest tests/

# เอาต์พุตแบบละเอียด
uv run python -m pytest tests/ -v

# รันเฉพาะการทดสอบที่ระบุ
uv run python -m pytest tests/test_content_preprocessor.py -v
uv run python -m pytest tests/test_new_features.py -v
uv run python -m pytest tests/test_unit.py -v
```

> **หมายเหตุ**: การทดสอบ async 3 รายการใน `test_integration_manual.py` ต้องติดตั้ง `pytest-asyncio` หากไม่มีจะแสดง Failed แต่ไม่กระทบการทดสอบอื่น `bench_deepseek_flash_vs_pro.py` เป็นสคริปต์เกณฑ์มาตรฐานประสิทธิภาพ ไม่ใช่การทดสอบหน่วย

## การแก้ไขปัญหา

### การเชื่อมต่อ Neo4j ล้มเหลว

```bash
neo4j status                              # ตรวจสอบสถานะบริการ
cypher-shell -u neo4j -p your_password    # ยืนยันรหัสผ่านถูกต้อง
curl http://localhost:7474                 # ยืนยันพอร์ต HTTP
```

สาเหตุที่พบบ่อย:
- Neo4j ยังไม่ได้เริ่ม
- รหัสผ่านผิด (`NEO4J_PASSWORD` ใน `.env`)
- พอร์ตถูกใช้งานอยู่หรือไฟร์วอลล์บล็อก

### การเชื่อมต่อ LLM ล้มเหลว

**โหมด Ollama:**
```bash
ollama serve                # เริ่มบริการ Ollama
ollama list                 # ตรวจสอบโมเดลที่ติดตั้งแล้ว
ollama pull qwen2.5:3b      # ติดตั้งโมเดลที่ขาดหาย
```

สาเหตุที่พบบ่อย: Ollama ยังไม่ได้เริ่ม โมเดลยังไม่ได้ติดตั้ง หน่วยความจำ GPU ไม่เพียงพอ

**โหมด GLM:**
- ยืนยันว่า `GLM_API_KEY` ถูกต้อง
- ยืนยันว่า `GLM_EMBEDDING_DIMENSIONS=768` (ต้องตรงกับดัชนีเวกเตอร์ Neo4j)
- ปลายทาง GLM API: `https://open.bigmodel.cn/api/paas/v4/`

**โหมด GROQ:**
- ยืนยันว่า `GROQ_API_KEY` ถูกต้อง
- เมื่อ Rate Limit บ่อยให้พิจารณาเปลี่ยนไปใช้โหมด GLM
- GROQ ไม่ให้บริการ Embedding ต้องตรวจสอบให้แน่ใจว่าตัวสร้าง embedding ของ Ollama ใช้งานได้

**โหมด OpenRouter:**
- ยืนยันว่า `OPENROUTER_API_KEY` ถูกต้อง และ `OPENROUTER_MODEL` เป็น ID โมเดลที่ใช้ได้ (ดู https://openrouter.ai/models)
- ไม่ให้บริการ Embedding ต้องตรวจสอบให้แน่ใจว่าตัวสร้าง embedding ของ Ollama ใช้งานได้

**โหมด DeepSeek:**
- ยืนยันว่า `DEEPSEEK_API_KEY` ถูกต้อง
- หากปรากฏ `Prompt must contain the word 'json'`: นี่เป็นข้อกำหนดบังคับของโหมด `json_object` ของ DeepSeek ไคลเอนต์มีการป้องกันสำรองในตัวแล้ว หากยังปรากฏ ให้ยืนยันว่าใช้ `src/deepseek_client.py` เวอร์ชันล่าสุดและรีสตาร์ทบริการ
- ไม่ให้บริการ Embedding ต้องตรวจสอบให้แน่ใจว่าตัวสร้าง embedding ของ Ollama ใช้งานได้

### ข้อผิดพลาดการเชื่อมต่อ MCP

หากปรากฏ `Invalid request parameters` หรือ `Received request before initialization was complete`:

1. ยืนยันว่าใช้โหมดการส่งผ่าน HTTP (**อย่าใช้ SSE**)
2. ยืนยันว่าไคลเอนต์ตั้งค่าเป็น `"type": "http"`, `"url": "http://localhost:8000/mcp"`
3. รีสตาร์ทบริการ: `pm2 restart graphiti-mcp-http --update-env`
4. รัน `/mcp` ใน Claude Code เพื่อเชื่อมต่อใหม่

### การเพิ่มหน่วยความจำช้า

- **Ollama**: ตรวจสอบขนาดโมเดล (`qwen2.5:3b` เร็วกว่า `7b` 5-10 เท่า) ยืนยันว่าใช้ GPU (`ollama ps`)
- **GLM**: แต่ละ add_episode ต้องใช้การรับส่งข้อมูลเครือข่าย LLM 10-20+ รอบ ข้อความสั้น ~22 วินาทีเป็นค่าปกติ
- **GROQ**: Rate Limit จะทำให้เกิดการลองใหม่จำนวนมาก หากใช้บ่อยแนะนำให้เปลี่ยนไปใช้ GLM หรือ Ollama
- ใช้ `background=true` เพื่อหลีกเลี่ยงการบล็อก
- ลด `GRAPHITI_CHUNK_THRESHOLD` เพื่อให้ข้อความยาวถูกตัดแบ่งเร็วขึ้น

### ปัญหา PM2

```bash
pm2 status                                        # ตรวจสอบสถานะ
pm2 logs graphiti-mcp-http --err --lines 50        # บันทึกข้อผิดพลาด
lsof -i :8000                                     # ตรวจสอบการใช้งานพอร์ต
pm2 delete graphiti-mcp-http && pm2 start ecosystem.config.cjs  # รีสตาร์ททั้งหมด
```

## เครื่องมือวินิจฉัยสำหรับการพัฒนา

```bash
uv run python tools/status_report.py           # รายงานสถานะแบบรวม (Neo4j + Ollama + การตั้งค่า)
uv run python tools/validate_config.py         # ตรวจสอบความสมบูรณ์ของ .env และการตั้งค่า
uv run python tools/performance_diagnose.py    # การวินิจฉัยประสิทธิภาพ LLM
uv run python tools/inspect_schema.py          # ตรวจสอบดัชนีและข้อจำกัดของ Neo4j
uv run python tools/migrate_embeddings.py      # การย้ายโมเดล Embedding (สร้างเวกเตอร์ใหม่หลังเปลี่ยนโมเดล)
```

### การย้ายโมเดล Embedding

หลังเปลี่ยนโมเดล embedding (เช่น `nomic-embed-text` → `bge-m3`) สามารถใช้เครื่องมือย้ายข้อมูลเพื่อสร้างเวกเตอร์ที่มีอยู่ทั้งหมดใหม่ เพื่อให้คุณภาพการค้นหาสอดคล้องกัน:

```bash
# ดูตัวอย่างจำนวนที่ต้องย้าย
uv run python tools/migrate_embeddings.py --dry-run

# ย้ายทั้งหมด (รองรับการรันต่อจากจุดหยุด)
uv run python tools/migrate_embeddings.py

# ย้ายเฉพาะ group ที่ระบุ
uv run python tools/migrate_embeddings.py --group-id myproject

# ดำเนินการต่อจากจุดหยุด (รันใหม่หลังถูกขัดจังหวะ)
uv run python tools/migrate_embeddings.py --resume
```

> **ความเข้ากันได้**: `bge-m3` มีขนาด 1024 มิติตามต้นฉบับ ระบบจะตัดให้เหลือ 768 มิติโดยอัตโนมัติเพื่อให้เข้ากันได้กับดัชนีเวกเตอร์ Neo4j ที่มีอยู่ ข้อมูลก่อนและหลังการย้ายสามารถอยู่ร่วมกันได้ แต่แนะนำให้ทำการย้ายทั้งหมดเพื่อให้ได้คุณภาพการค้นหาที่ดีที่สุด

## เอกสาร

- [คำสั่งการใช้เครื่องมือ](../使用工具的指令.md) — คู่มือการใช้งานเครื่องมือ MCP และแนวทางปฏิบัติที่ดีที่สุด
- [Graphiti Memory Rules](../graphiti-memory-rules.md) — คำอธิบายกฎของหน่วยความจำ

## สัญญาอนุญาต

MIT License
