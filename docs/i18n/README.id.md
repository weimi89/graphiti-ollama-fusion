# Graphiti MCP Server

Layanan memori graf pengetahuan — server MCP yang mengintegrasikan berbagai penyedia LLM (Ollama / GLM / GROQ / OpenRouter / DeepSeek) dengan basis data graf Neo4j.

Dikembangkan sebagai perluasan dari [getzep/graphiti](https://github.com/getzep/graphiti), mendukung peralihan fleksibel antara Ollama lokal dan LLM cloud, serta memungkinkan penentuan penyedia Embedding secara independen (terpisah dari LLM).

## Fitur Unggulan

- **Manajemen memori cerdas** — menggunakan graf pengetahuan untuk menyimpan dan mengambil relasi memori yang kompleks
- **Pencarian semantik** — pencarian hibrida berbasis embedding vektor (vektor + kata kunci + penelusuran graf)
- **16 strategi pencarian** — pencarian lanjutan mendukung berbagai metode peringkatan ulang seperti RRF, MMR, Cross-Encoder, dan lainnya
- **Berbagai penyedia LLM** — mendukung Ollama (lokal), GLM (gratis dari Zhipu AI), GROQ (inferensi berkecepatan tinggi), OpenRouter (agregat berbagai model), DeepSeek (DeepSeek AI), dapat dialihkan dengan satu variabel lingkungan
- **Embedding terpisah dari LLM** — dapat menentukan embedder secara independen dengan `EMBEDDING_PROVIDER`, LLM cloud otomatis kembali ke `bge-m3` lokal
- **Pemisahan dua model** — dalam mode Ollama, tugas kompleks menggunakan model utama, sedangkan tugas sederhana otomatis beralih ke model kecil untuk meningkatkan kinerja
- **Pemotongan konten cerdas** — teks panjang otomatis dipecah menjadi segmen untuk mengurangi beban LLM (ambang batas dapat dikonfigurasi)
- **Pemrosesan memori di latar belakang** — penambahan memori dapat dijalankan di latar belakang, panggilan MCP langsung mengembalikan hasil
- **Deduplikasi memori** — otomatis mendeteksi memori yang sudah ada dan sangat mirip untuk menghindari penyimpanan ganda
- **Deteksi konflik** — mendeteksi fakta yang bertentangan antara dua entitas, mengidentifikasi informasi yang sudah tidak berlaku dan yang masih berlaku
- **Deteksi komunitas** — otomatis mengelompokkan entitas terkait berdasarkan algoritma Label Propagation
- **Pelacakan kepentingan** — otomatis mencatat frekuensi akses entitas, hasil pencarian diurutkan berdasarkan kepentingan
- **Pelupaan cerdas** — mengidentifikasi dan membersihkan memori yang usang dan jarang diakses untuk menjaga graf tetap ramping
- **Impor massal** — mengirimkan beberapa memori sekaligus, cocok untuk migrasi data dalam jumlah besar
- **Triplet terstruktur** — langsung menambahkan "subjek-relasi-objek", melewati ekstraksi LLM, selesai dalam sekejap
- **Antarmuka manajemen Web** — dilengkapi dasbor, penjelajahan, pencarian, visualisasi graf pengetahuan, tanya jawab AI, dan penjelajahan komunitas
- **Multibahasa (i18n)** — pesan respons mendukung 30+ locale (termasuk zh-TW / en / zh-CN / ja / pt-BR / ko / es / de / fr dan lainnya); tool MCP mengikuti `SERVER_LANG`, REST API otomatis bernegosiasi berdasarkan HTTP `Accept-Language`
- **Tema gelap/terang** — antarmuka Web mendukung peralihan tema
- **Mode aman** — opsi penambahan memori cepat yang melewati ekstraksi entitas
- **Dukungan Docker** — dilengkapi Dockerfile, mendukung penerapan dalam kontainer
- **Aman terhadap konkurensi** — asyncio.Lock melindungi inisialisasi, mencegah kondisi balapan
- **Pemeriksaan kesehatan berlapis** — `/health` (liveness) + `/health/ready` (readiness)

## Persyaratan Sistem

| Item | Persyaratan |
|------|------|
| Python | 3.10+ (disarankan 3.11+) |
| Neo4j | 4.0+ (`bolt://localhost:7687`) |
| Penyedia LLM | Ollama / GLM / GROQ / OpenRouter / DeepSeek (pilih salah satu dari lima) |
| Node.js | 18+ (hanya untuk eksekusi latar belakang PM2, opsional) |
| Ruang disk | ~3GB (model Ollama + data Neo4j) |

### Pemilihan Penyedia LLM

Dialihkan melalui variabel lingkungan `LLM_PROVIDER` (`ollama` / `glm` / `groq` / `openrouter` / `deepseek`):

| Penyedia | Karakteristik | Model LLM | Embedding | Skenario yang Cocok |
|--------|------|----------|-----------|----------|
| **Ollama** (default) | Sepenuhnya lokal, data tidak meninggalkan mesin | `qwen2.5:3b` | `bge-m3` (unggul untuk bahasa Tionghoa + RAG) | Memiliki GPU, mementingkan privasi |
| **GLM** | Cloud gratis, stabil tanpa batas | `glm-4-flash` (gratis) | `embedding-3` | Tanpa GPU, skenario padat pencarian |
| **GROQ** | Inferensi berkecepatan sangat tinggi | `llama-3.3-70b-versatile` | Kembali ke Ollama `bge-m3` | Penulisan sesekali, mengejar kualitas |
| **OpenRouter** | Agregat berbagai model, termasuk kuota gratis | `stepfun/step-3.5-flash:free` dll. | Kembali ke Ollama `bge-m3` | Ingin menggunakan model cloud tertentu |
| **DeepSeek** | Cloud DeepSeek AI, hemat biaya | `deepseek-v4-flash` / `deepseek-v4-pro` | Kembali ke Ollama `bge-m3` | Pemahaman bahasa Tionghoa, cloud berbiaya rendah |

> **Embedding terpisah dari LLM**: embedder ditentukan secara independen melalui `EMBEDDING_PROVIDER` (`ollama` / `glm`), jika tidak diatur akan mengikuti `LLM_PROVIDER`. Pada kenyataannya hanya `glm` yang menggunakan GLM `embedding-3`, selebihnya (termasuk LLM cloud seperti GROQ / OpenRouter / DeepSeek yang tidak menyediakan Embedding) semuanya otomatis menggunakan Ollama `bge-m3`. **Oleh karena itu, saat menggunakan LLM cloud apa pun, Ollama lokal tetap diperlukan untuk menyediakan layanan embedding (kecuali embedding juga diatur ke glm).**

#### Mode Ollama (lokal)

```bash
# Model utama LLM (disarankan qwen2.5:3b, keseimbangan terbaik antara kecepatan dan stabilitas)
ollama pull qwen2.5:3b

# Model embedding (wajib, digunakan untuk pencarian vektor)
ollama pull bge-m3
```

> **Catatan pemilihan model**:
> - `qwen2.5:3b` — disarankan, ~2 detik/panggilan, ~100 t/s, keluaran terstruktur graphiti-core 100% stabil
> - `qwen2.5:7b` — hasil lebih baik tetapi 5-10 kali lebih lambat, cocok untuk skenario yang mengejar kualitas
> - `qwen2.5:1.5b` — paling cepat tetapi **tidak stabil** (tingkat keberhasilan JSON terstruktur hanya 33%), tidak disarankan digunakan

#### Mode GLM (cloud Zhipu AI)

```bash
# Pengaturan .env
LLM_PROVIDER=glm
GLM_API_KEY=your_api_key          # Diperoleh dari https://open.bigmodel.cn
GLM_MODEL=glm-4-flash             # Model gratis
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768      # Harus konsisten dengan dimensi indeks vektor Neo4j
```

> **Referensi kinerja GLM**: penulisan ~22 detik (teks pendek), pencarian ~0,34 detik, nol kesalahan Rate Limit, 2-5 kali lebih lambat dari Ollama lokal tetapi sepenuhnya gratis.

#### Mode GROQ (inferensi berkecepatan tinggi)

```bash
# Pengaturan .env
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key         # Diperoleh dari https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile
```

> **Catatan**: GROQ tidak menyediakan layanan Embedding, perlu dipadukan dengan embedder Ollama (kembali secara otomatis) atau atur `EMBEDDING_PROVIDER` ke glm. GROQ memiliki Rate Limit yang ketat, penggunaan frekuensi tinggi akan memicu banyak percobaan ulang.

#### Mode OpenRouter (agregat berbagai model)

```bash
# Pengaturan .env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_api_key       # Diperoleh dari https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free   # Dapat diubah menjadi model OpenRouter apa pun
```

> **Catatan**: OpenRouter tidak menyediakan Embedding, otomatis kembali ke Ollama `bge-m3`. Daftar model lihat di https://openrouter.ai/models (termasuk beberapa model gratis `:free`).

#### Mode DeepSeek (DeepSeek AI)

```bash
# Pengaturan .env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key         # Diperoleh dari https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash      # Disarankan; atau deepseek-v4-pro (hasil lebih baik)
```

> **Catatan**: DeepSeek tidak menyediakan Embedding, otomatis kembali ke Ollama `bge-m3`. `deepseek-chat` / `deepseek-reasoner` akan dihentikan pada 2026-07-24, disarankan beralih ke `deepseek-v4-flash` / `deepseek-v4-pro`. DeepSeek secara ketat mensyaratkan prompt mode `json_object` mengandung string "json", klien telah dilengkapi perlindungan cadangan bawaan, tidak perlu pengaturan tambahan.

## Mulai Cepat

### 1. Persiapan Awal

Pastikan Neo4j sudah berjalan di mesin lokal, dan siapkan layanan yang sesuai berdasarkan penyedia LLM yang dipilih:

```bash
# Pastikan Neo4j sedang berjalan (wajib)
neo4j status
# Atau gunakan Docker: docker run -d -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/your_password neo4j:latest

# Mode Ollama: pastikan Ollama sedang berjalan
ollama list
# Jika belum dimulai: ollama serve

# Mode GLM / GROQ: hanya memerlukan API Key yang valid, tidak perlu layanan lokal
```

### 2. Instal Dependensi

```bash
git clone <repo-url>
cd graphiti
uv sync
```

> **Catatan**: Proyek ini menggunakan [uv](https://github.com/astral-sh/uv) untuk mengelola dependensi. Jika belum terinstal: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 3. Konfigurasi Lingkungan

```bash
cp .env.example .env
```

Edit `.env`, **minimal** perlu mengubah item-item berikut:

```bash
NEO4J_PASSWORD=your_actual_password  # Wajib: kata sandi Neo4j
LLM_PROVIDER=ollama                  # ollama / glm / groq / openrouter / deepseek
OLLAMA_MODEL=qwen2.5:3b              # Mode Ollama: model LLM lokal
# GLM_API_KEY=your_key               # Mode GLM: API Key Zhipu AI
# GROQ_API_KEY=your_key              # Mode GROQ: API Key GROQ
# OPENROUTER_API_KEY=your_key        # Mode OpenRouter: API Key
# DEEPSEEK_API_KEY=your_key          # Mode DeepSeek: API Key
```

### 4. Jalankan Layanan

```bash
# Mode HTTP (disarankan, mencakup antarmuka manajemen Web)
uv run python graphiti_mcp_server.py --transport http --port 8000

# Atau gunakan eksekusi latar belakang PM2 (disarankan untuk operasi jangka panjang)
pm2 start ecosystem.config.cjs
```

### 5. Verifikasi Layanan

Setelah dimulai, Anda dapat mengakses endpoint berikut:

| Endpoint | Keterangan |
|------|------|
| http://localhost:8000/ | Antarmuka manajemen Web |
| http://localhost:8000/mcp | Endpoint MCP (untuk koneksi klien MCP) |
| http://localhost:8000/health | Pemeriksaan kesehatan (liveness) |
| http://localhost:8000/health/ready | Pemeriksaan mendalam (termasuk koneksi Neo4j) |
| http://localhost:8000/api/stats | Statistik REST API |

## Struktur Proyek

```
graphiti/
├── graphiti_mcp_server.py        # Titik masuk utama — definisi tool MCP (19 tool)
├── src/
│   ├── config.py                 # Manajemen konfigurasi (GraphitiConfig, mendukung penumpukan JSON/.env)
│   ├── web_api.py                # REST API antarmuka manajemen Web (20+ endpoint)
│   ├── ollama_graphiti_client.py  # Klien LLM Ollama (pemisahan dua model)
│   ├── glm_client.py             # Klien LLM GLM (Zhipu AI) (API kompatibel OpenAI)
│   ├── openrouter_client.py      # Klien LLM OpenRouter (agregat berbagai model)
│   ├── deepseek_client.py        # Klien LLM DeepSeek (json_object + perlindungan json cadangan)
│   ├── ollama_embedder.py        # Adaptor model embedding Ollama
│   ├── content_preprocessor.py   # Pemotongan konten cerdas (teks panjang otomatis dipecah)
│   ├── deduplication.py          # Deduplikasi memori (perbandingan kemiripan kosinus)
│   ├── importance.py             # Pelacakan kepentingan dan pelupaan cerdas
│   ├── safe_memory_add.py        # Penambahan memori aman (melewati ekstraksi entitas)
│   ├── timezone_utils.py         # Konversi zona waktu (UTC→tampilan zona waktu lokal)
│   ├── i18n.py                   # Multibahasa backend (REST mengikuti Accept-Language, MCP mengikuti SERVER_LANG)
│   ├── exceptions.py             # Penanganan pengecualian terstruktur (12 kategori pengecualian)
│   └── logging_setup.py          # Sistem log (rotasi waktu + pemantauan kinerja)
├── web/                          # Frontend antarmuka manajemen Web (SPA, tanpa build)
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js                # Pembungkus REST API
│       ├── components.js         # Render komponen UI (termasuk halaman komunitas)
│       └── app.js                # Routing SPA, manajemen status
├── tests/                        # Rangkaian pengujian (183 pengujian)
│   ├── test_content_preprocessor.py  # Pengujian logika pemotongan (17 pengujian)
│   ├── test_new_features.py      # Pengujian fitur baru (32 pengujian)
│   ├── test_i18n.py             # Pengujian multibahasa (37 pengujian)
│   ├── test_unit.py              # Pengujian unit
│   ├── test_web_api.py           # Pengujian Web API
│   ├── test_web_ui_features.py   # Pengujian fitur Web UI
│   ├── test_integration_manual.py # Pengujian integrasi manual
│   └── bench_deepseek_flash_vs_pro.py # Skrip tolok ukur kinerja flash/pro DeepSeek
├── tools/                        # Tool diagnostik pengembangan
│   ├── status_report.py          # Laporan status terintegrasi
│   ├── validate_config.py        # Validasi konfigurasi
│   ├── performance_diagnose.py   # Diagnosis kinerja
│   ├── inspect_schema.py         # Pemeriksaan struktur Neo4j
│   └── batch_reprocess.py        # Pemrosesan ulang batch
├── docs/                         # Dokumentasi
├── logs/                         # Log (rotasi waktu, default disimpan 30 hari)
├── Dockerfile                    # Penerapan kontainer Docker
└── ecosystem.config.cjs          # Konfigurasi PM2
```

## Pengaturan Klien MCP

### Mode HTTP (disarankan)

Cocok untuk klien MCP yang mendukung HTTP seperti Claude Code, Cline, dan lainnya:

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

### Mode STDIO

Cocok untuk klien yang perlu memulai proses secara langsung seperti Claude Desktop:

**Lokasi file konfigurasi:**
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

> **Catatan**: Mode SSE (`--transport sse`) tidak lagi disarankan untuk digunakan. MCP 1.x memiliki masalah kompatibilitas inisialisasi session, harap beralih ke mode HTTP.

## Tool MCP (19 tool)

### Manajemen Memori (7 tool)

| Tool | Keterangan |
|------|------|
| `add_memory_simple` | Menambahkan memori ke graf pengetahuan (mendukung pemrosesan latar belakang, pemotongan cerdas, pemeriksaan deduplikasi) |
| `add_episode_bulk` | Menambahkan beberapa memori secara massal (default pemrosesan latar belakang) |
| `add_triplet` | Penambahan triplet terstruktur (melewati LLM, selesai dalam sekejap) |
| `search_memory_nodes` | Mencari node memori (mendukung 16 strategi pencarian, penyaringan waktu) |
| `search_memory_facts` | Mencari fakta memori (mendukung penyaringan jenis relasi, rentang waktu, penyaringan validitas) |
| `advanced_search` | Pencarian lanjutan (16 strategi, mengembalikan node+edge+komunitas+episode) |
| `get_episodes` | Mendapatkan episode memori terbaru |

### Analisis Pengetahuan (3 tool)

| Tool | Keterangan |
|------|------|
| `check_conflicts` | Mendeteksi konflik fakta antara dua entitas (berlaku vs sudah tidak berlaku) |
| `get_node_edges` | Menjelajahi relasi edge masuk dan keluar dari sebuah node |
| `build_communities` | Memicu deteksi dan pengelompokan komunitas (default pemrosesan latar belakang) |

### Pemeliharaan Memori (2 tool)

| Tool | Keterangan |
|------|------|
| `get_stale_memories` | Menanyakan memori yang usang dan jarang diakses |
| `cleanup_stale_memories` | Membersihkan memori usang (default mode pratinjau dry_run) |

### Manajemen Tugas

| Tool | Keterangan |
|------|------|
| `get_memory_task_status` | Menanyakan progres dan hasil tugas pemrosesan memori latar belakang |

### Penghapusan dan Kueri

| Tool | Keterangan |
|------|------|
| `delete_episode` | Menghapus episode memori |
| `delete_entity_edge` | Menghapus edge entitas (relasi) |
| `get_entity_edge` | Mendapatkan informasi rinci edge entitas |

### Manajemen Sistem

| Tool | Keterangan |
|------|------|
| `get_status` | Mendapatkan status layanan (Neo4j, LLM, embedder) |
| `test_connection` | Menguji koneksi Neo4j / LLM / embedder |
| `clear_graph` | Membersihkan basis data graf (mendukung pembersihan berdasarkan group_id) |

## Parameter Tool

### add_memory_simple

| Parameter | Jenis | Wajib | Nilai Default | Keterangan |
|------|------|------|--------|------|
| `name` | string | Y | | Nama memori |
| `episode_body` | string | Y | | Isi memori (otomatis dipotong jika melebihi 800 karakter) |
| `group_id` | string | | `"default"` | ID grup (disarankan dipisahkan per proyek) |
| `source` | string | | `"text"` | Jenis sumber: `text` / `json` / `message` |
| `source_description` | string | | `"MCP Server"` | Deskripsi sumber |
| `use_safe_mode` | bool | | `false` | Mode aman (melewati ekstraksi entitas, cepat tetapi memori tidak dapat dicari) |
| `background` | bool | | `false` | Pemrosesan latar belakang (langsung mengembalikan task_id, cocok untuk teks panjang) |
| `force` | bool | | `false` | Melewati pemeriksaan deduplikasi (penambahan paksa) |
| `excluded_entity_types` | list | | | Jenis entitas yang dikecualikan (mengurangi ekstraksi yang tidak diperlukan) |

> **Tips kinerja**:
> - Teks pendek (<800 karakter): diproses langsung, biasanya selesai dalam 30-40 detik
> - Teks panjang (>800 karakter): otomatis dipotong menjadi beberapa segmen, menggunakan `add_episode_bulk` untuk pemrosesan paralel (~33% lebih cepat dari serial)
> - Gunakan `background=true` untuk menghindari pemblokiran panggilan MCP, lacak progres melalui `get_memory_task_status`
> - `use_safe_mode=true` selesai dalam sekejap tetapi memori tidak dapat ditemukan oleh tool search
> - Saat deduplikasi diaktifkan, memori yang sangat mirip akan diberi peringatan (`force=true` dapat melewatinya)

### add_episode_bulk

| Parameter | Jenis | Wajib | Nilai Default | Keterangan |
|------|------|------|--------|------|
| `episodes` | list | Y | | Daftar memori, setiap item berisi `name` dan `content` |
| `group_id` | string | | `"default"` | ID grup |
| `source` | string | | `"text"` | Jenis sumber |
| `background` | bool | | `true` | Pemrosesan latar belakang (operasi massal biasanya memakan waktu) |

### add_triplet

| Parameter | Jenis | Wajib | Nilai Default | Keterangan |
|------|------|------|--------|------|
| `source_name` | string | Y | | Nama entitas sumber (mis. "Alice") |
| `target_name` | string | Y | | Nama entitas target (mis. "Google") |
| `relation_name` | string | Y | | Nama relasi (mis. "works_at") |
| `fact` | string | Y | | Deskripsi fakta (mis. "Alice works at Google") |
| `group_id` | string | | `"default"` | ID grup |
| `source_labels` | list | | | Label entitas sumber |
| `target_labels` | list | | | Label entitas target |

### search_memory_nodes

| Parameter | Jenis | Wajib | Nilai Default | Keterangan |
|------|------|------|--------|------|
| `query` | string | Y | | Kata kunci pencarian (bahasa alami) |
| `max_nodes` | int | | `10` | Jumlah maksimum yang dikembalikan |
| `group_ids` | list | | | Penyaringan grup (pencarian gabungan beberapa grup) |
| `entity_types` | list | | | Penyaringan jenis entitas |
| `search_recipe` | string | | | Strategi pencarian (lihat pencarian lanjutan) |
| `created_after` | string | | | Batas bawah waktu pembuatan (ISO datetime) |
| `created_before` | string | | | Batas atas waktu pembuatan (ISO datetime) |

### search_memory_facts

| Parameter | Jenis | Wajib | Nilai Default | Keterangan |
|------|------|------|--------|------|
| `query` | string | Y | | Kata kunci pencarian |
| `max_facts` | int | | `10` | Jumlah maksimum yang dikembalikan |
| `group_ids` | list | | | Penyaringan grup |
| `center_node_uuid` | string | | | UUID node pusat (menjelajahi relasi node tertentu) |
| `edge_types` | list | | | Penyaringan jenis relasi (mis. `["works_at"]`) |
| `created_after` | string | | | Batas bawah waktu pembuatan (ISO datetime) |
| `created_before` | string | | | Batas atas waktu pembuatan (ISO datetime) |
| `only_valid` | bool | | `false` | Hanya mengembalikan fakta yang belum kedaluwarsa |

### advanced_search

| Parameter | Jenis | Wajib | Nilai Default | Keterangan |
|------|------|------|--------|------|
| `query` | string | Y | | Kata kunci pencarian |
| `search_recipe` | string | | `"combined_rrf"` | Strategi pencarian (16 pilihan) |
| `max_results` | int | | `10` | Jumlah maksimum yang dikembalikan |
| `group_ids` | list | | | Penyaringan grup |
| `center_node_uuid` | string | | | UUID node pusat |

**Strategi pencarian yang tersedia (search_recipe):**

| Kategori | Strategi | Keterangan |
|------|------|------|
| Gabungan | `combined_rrf` | Fusi RRF gabungan (default, disarankan) |
| Gabungan | `combined_mmr` | Peringkatan ulang keberagaman MMR gabungan |
| Gabungan | `combined_cross_encoder` | Peringkatan halus Cross-Encoder gabungan |
| Edge | `edge_rrf` / `edge_mmr` / `edge_cross_encoder` | Pencarian edge (3 jenis peringkatan) |
| Edge | `edge_node_distance` / `edge_episode_mentions` | Pencarian edge (jarak graf/jumlah kutipan) |
| Node | `node_rrf` / `node_mmr` / `node_cross_encoder` | Pencarian node (3 jenis peringkatan) |
| Node | `node_node_distance` / `node_episode_mentions` | Pencarian node (jarak graf/jumlah kutipan) |
| Komunitas | `community_rrf` / `community_mmr` / `community_cross_encoder` | Pencarian komunitas |

### check_conflicts

| Parameter | Jenis | Wajib | Nilai Default | Keterangan |
|------|------|------|--------|------|
| `source_name` | string | Y | | Nama entitas sumber |
| `target_name` | string | Y | | Nama entitas target |
| `group_id` | string | | `"default"` | ID grup |

### get_node_edges

| Parameter | Jenis | Wajib | Nilai Default | Keterangan |
|------|------|------|--------|------|
| `node_uuid` | string | Y | | UUID node |
| `include_inbound` | bool | | `true` | Menyertakan edge masuk |
| `include_outbound` | bool | | `true` | Menyertakan edge keluar |
| `max_edges` | int | | `50` | Jumlah maksimum yang dikembalikan |

### build_communities

| Parameter | Jenis | Wajib | Nilai Default | Keterangan |
|------|------|------|--------|------|
| `group_ids` | list | | | Menentukan grup (kosongkan untuk semua) |
| `background` | bool | | `true` | Pemrosesan latar belakang |

### get_stale_memories

| Parameter | Jenis | Wajib | Nilai Default | Keterangan |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Dianggap usang jika tidak diakses melebihi sekian hari |
| `min_access_count` | int | | `2` | Hanya disertakan jika jumlah akses di bawah nilai ini |
| `group_id` | string | | | Penyaringan grup |
| `limit` | int | | `50` | Jumlah maksimum yang dikembalikan |

### cleanup_stale_memories

| Parameter | Jenis | Wajib | Nilai Default | Keterangan |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Ambang batas jumlah hari usang |
| `min_access_count` | int | | `2` | Ambang batas jumlah akses minimum |
| `group_id` | string | | | Penyaringan grup |
| `dry_run` | bool | | `true` | Mode pratinjau (tidak benar-benar menghapus) |
| `limit` | int | | `50` | Jumlah maksimum yang diproses |

### get_memory_task_status

| Parameter | Jenis | Wajib | Keterangan |
|------|------|------|------|
| `task_id` | string | Y | ID tugas latar belakang (dikembalikan oleh `add_memory_simple(background=true)`) |

## Antarmuka Manajemen Web

Dalam mode HTTP, akses `http://localhost:8000/` untuk menggunakannya.

**Fitur:**
- Dasbor — statistik jumlah node, jumlah fakta, jumlah episode memori
- Node entitas — penjelajahan, penyaringan, pencarian vektor
- Relasi fakta — penjelajahan, penyaringan, pencarian vektor
- Episode memori — penjelajahan, pencarian teks lengkap, penghapusan
- Penjelajahan komunitas — daftar node komunitas, ringkasan, memicu pembangunan komunitas
- Formulir triplet — langsung menambahkan pengetahuan terstruktur "subjek-relasi-objek"
- Manajemen Group — penyaringan berdasarkan grup, penghapusan batch
- Visualisasi graf pengetahuan — penyajian grafis relasi node
- Tanya jawab AI — tanya jawab cerdas berbasis graf pengetahuan
- Analisis kualitas — analisis kualitas dan cakupan memori
- Peralihan tema — tema gelap/terang

**REST API:**

| Endpoint | Metode | Keterangan |
|------|------|------|
| `/api/stats` | GET | Statistik dasbor |
| `/api/groups` | GET | Mendapatkan semua group_id |
| `/api/nodes` | GET | Menjelajahi node entitas (paginasi) |
| `/api/facts` | GET | Menjelajahi fakta (paginasi) |
| `/api/episodes` | GET | Menjelajahi episode memori (paginasi) |
| `/api/search/nodes` | GET | Pencarian vektor node |
| `/api/search/facts` | GET | Pencarian vektor fakta |
| `/api/search/advanced` | GET | Pencarian lanjutan (16 strategi) |
| `/api/communities` | GET | Menjelajahi node komunitas (paginasi) |
| `/api/communities/build` | POST | Memicu pembangunan komunitas |
| `/api/memory/add-bulk` | POST | Menambahkan memori secara massal |
| `/api/memory/add-triplet` | POST | Menambahkan triplet |
| `/api/memory/tasks` | GET | Menampilkan daftar tugas latar belakang (mendukung penyaringan status) |
| `/api/memory/tasks/{id}` | GET | Menanyakan status tugas tunggal |
| `/api/analytics/stale` | GET | Menanyakan memori usang |
| `/api/analytics/cleanup` | POST | Membersihkan memori usang |
| `/api/nodes/{uuid}` | DELETE | Menghapus node |
| `/api/episodes/{uuid}` | DELETE | Menghapus episode memori |
| `/api/facts/{uuid}` | DELETE | Menghapus fakta |
| `/api/groups/{group_id}` | DELETE | Menghapus seluruh group |

## Konfigurasi

### Variabel Lingkungan (.env)

Konfigurasi menggunakan mekanisme penumpukan: file konfigurasi JSON sebagai dasar, variabel lingkungan menimpa nilai individual.

```bash
# === Wajib ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password        # Harus diubah

# === Pemilihan penyedia LLM ===
LLM_PROVIDER=ollama                 # ollama / glm / groq / openrouter / deepseek

# === Penyedia Embedding (opsional, default mengikuti LLM_PROVIDER) ===
# Hanya glm yang menggunakan GLM Embedding, selebihnya semua menggunakan Ollama bge-m3
# EMBEDDING_PROVIDER=ollama         # ollama / glm

# === Konfigurasi Ollama (digunakan saat LLM_PROVIDER=ollama) ===
OLLAMA_MODEL=qwen2.5:3b             # Model utama (disarankan qwen2.5:3b)
OLLAMA_SMALL_MODEL=qwen2.5:3b       # Model kecil (untuk tugas sederhana, dapat memilih model berbeda)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.1

# === Konfigurasi GLM (digunakan saat LLM_PROVIDER=glm) ===
GLM_API_KEY=your_api_key            # Diperoleh dari https://open.bigmodel.cn
GLM_MODEL=glm-4-flash               # Model gratis
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768

# === Konfigurasi GROQ (digunakan saat LLM_PROVIDER=groq) ===
GROQ_API_KEY=your_api_key           # Diperoleh dari https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile

# === Konfigurasi OpenRouter (digunakan saat LLM_PROVIDER=openrouter) ===
OPENROUTER_API_KEY=your_api_key     # Diperoleh dari https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free

# === Konfigurasi DeepSeek (digunakan saat LLM_PROVIDER=deepseek) ===
DEEPSEEK_API_KEY=your_api_key       # Diperoleh dari https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash    # Atau deepseek-v4-pro

# === Model embedding Ollama (digunakan saat embedding bukan glm) ===
OLLAMA_EMBEDDING_MODEL=bge-m3
OLLAMA_EMBEDDING_DIMENSIONS=768

# === Tampilan dan bahasa (opsional) ===
GRAPHITI_DISPLAY_TIMEZONE=Asia/Taipei # Zona waktu tampilan timestamp yang dikembalikan API (nama IANA; penyimpanan tetap UTC)
SERVER_LANG=zh-TW                     # Bahasa respons tool MCP (locale lengkap lihat src/i18n.py); REST API mengikuti Accept-Language

# === Kinerja memori (opsional) ===
GRAPHITI_CHUNK_THRESHOLD=800         # Ambang batas jumlah karakter yang memicu pemotongan cerdas
GRAPHITI_MAX_CHUNK_SIZE=600          # Jumlah karakter maksimum per segmen
GRAPHITI_MAX_COROUTINES=10            # Jumlah maksimum koroutin paralel
GRAPHITI_DEFAULT_BACKGROUND=false    # Apakah default pemrosesan latar belakang

# === Pelacakan kepentingan dan pelupaan cerdas (opsional) ===
ENABLE_IMPORTANCE_TRACKING=true      # Mengaktifkan pelacakan akses
IMPORTANCE_WEIGHT=0.1                # Bobot kepentingan
STALE_DAYS_THRESHOLD=30              # Ambang batas jumlah hari usang
STALE_MIN_ACCESS_COUNT=2             # Jumlah akses minimum

# === Log ===
LOG_FILE=logs/graphiti_mcp_server.log
LOG_LEVEL=INFO
```

> **Daftar variabel lingkungan lengkap** silakan lihat `.env.example`

### File Konfigurasi JSON

Cocok untuk konfigurasi yang memerlukan kontrol versi (variabel lingkungan masih dapat menimpa):

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

## Eksekusi Latar Belakang PM2

```bash
npm install -g pm2

pm2 start ecosystem.config.cjs      # Mulai
pm2 status                           # Status
pm2 logs graphiti-mcp-http           # Log real-time
pm2 restart graphiti-mcp-http --update-env  # Mulai ulang (memuat ulang .env)

pm2 save && pm2 startup              # Mengatur mulai otomatis saat boot
```

> **Tips**: Setelah mengubah `.env`, harus memulai ulang dengan flag `--update-env`, jika tidak variabel lingkungan tidak akan diperbarui.

## Penerapan Docker

```bash
docker build -t graphiti-mcp .

# Catatan: kontainer Docker perlu dapat terhubung ke Neo4j dan Ollama
# Menggunakan host network adalah yang paling sederhana
docker run -p 8000:8000 --env-file .env --network host graphiti-mcp

# Atau secara eksplisit menentukan alamat layanan eksternal
docker run -p 8000:8000 \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --env-file .env graphiti-mcp
```

## Pengujian

```bash
# Menjalankan semua pengujian (183 pengujian, sekitar 1 detik)
uv run python -m pytest tests/

# Keluaran terperinci
uv run python -m pytest tests/ -v

# Hanya menjalankan pengujian tertentu
uv run python -m pytest tests/test_content_preprocessor.py -v
uv run python -m pytest tests/test_new_features.py -v
uv run python -m pytest tests/test_unit.py -v
```

> **Catatan**: 3 pengujian async dalam `test_integration_manual.py` memerlukan instalasi `pytest-asyncio`, jika tidak ada akan menampilkan Failed tetapi tidak memengaruhi pengujian lainnya. `bench_deepseek_flash_vs_pro.py` adalah skrip tolok ukur kinerja, bukan pengujian unit.

## Pemecahan Masalah

### Koneksi Neo4j Gagal

```bash
neo4j status                              # Memeriksa status layanan
cypher-shell -u neo4j -p your_password    # Memastikan kata sandi benar
curl http://localhost:7474                 # Memastikan port HTTP
```

Penyebab umum:
- Neo4j belum dimulai
- Kata sandi salah (`NEO4J_PASSWORD` dalam `.env`)
- Port terpakai atau diblokir firewall

### Koneksi LLM Gagal

**Mode Ollama:**
```bash
ollama serve                # Memulai layanan Ollama
ollama list                 # Memeriksa model yang terinstal
ollama pull qwen2.5:3b      # Menginstal model yang hilang
```

Penyebab umum: Ollama belum dimulai, model belum terinstal, memori GPU tidak cukup

**Mode GLM:**
- Memastikan `GLM_API_KEY` benar
- Memastikan `GLM_EMBEDDING_DIMENSIONS=768` (harus konsisten dengan indeks vektor Neo4j)
- Endpoint API GLM: `https://open.bigmodel.cn/api/paas/v4/`

**Mode GROQ:**
- Memastikan `GROQ_API_KEY` benar
- Pertimbangkan beralih ke mode GLM saat Rate Limit sering terjadi
- GROQ tidak menyediakan Embedding, perlu memastikan embedder Ollama tersedia

**Mode OpenRouter:**
- Memastikan `OPENROUTER_API_KEY` benar, `OPENROUTER_MODEL` adalah ID model yang valid (lihat https://openrouter.ai/models)
- Tidak menyediakan Embedding, perlu memastikan embedder Ollama tersedia

**Mode DeepSeek:**
- Memastikan `DEEPSEEK_API_KEY` benar
- Jika muncul `Prompt must contain the word 'json'`: ini adalah persyaratan keras mode `json_object` DeepSeek, klien telah dilengkapi perlindungan cadangan bawaan; jika masih muncul, pastikan menggunakan versi terbaru `src/deepseek_client.py` dan mulai ulang layanan
- Tidak menyediakan Embedding, perlu memastikan embedder Ollama tersedia

### Kesalahan Koneksi MCP

Jika muncul `Invalid request parameters` atau `Received request before initialization was complete`:

1. Pastikan menggunakan mode transport HTTP (**jangan gunakan SSE**)
2. Pastikan pengaturan klien adalah `"type": "http"`, `"url": "http://localhost:8000/mcp"`
3. Mulai ulang layanan: `pm2 restart graphiti-mcp-http --update-env`
4. Jalankan `/mcp` di Claude Code untuk menyambung kembali

### Penambahan Memori Lambat

- **Ollama**: periksa ukuran model (`qwen2.5:3b` 5-10 kali lebih cepat dari `7b`), pastikan menggunakan GPU (`ollama ps`)
- **GLM**: setiap add_episode memerlukan 10-20+ kali bolak-balik jaringan LLM, ~22 detik untuk teks pendek adalah nilai normal
- **GROQ**: Rate Limit akan menyebabkan banyak percobaan ulang, jika sering digunakan disarankan beralih ke GLM atau Ollama
- Gunakan `background=true` untuk menghindari pemblokiran
- Turunkan `GRAPHITI_CHUNK_THRESHOLD` agar teks panjang dipotong lebih awal

### Masalah PM2

```bash
pm2 status                                        # Memeriksa status
pm2 logs graphiti-mcp-http --err --lines 50        # Log kesalahan
lsof -i :8000                                     # Memeriksa penggunaan port
pm2 delete graphiti-mcp-http && pm2 start ecosystem.config.cjs  # Mulai ulang sepenuhnya
```

## Tool Diagnostik Pengembangan

```bash
uv run python tools/status_report.py           # Laporan status terintegrasi (Neo4j + Ollama + konfigurasi)
uv run python tools/validate_config.py         # Memvalidasi kelengkapan .env dan konfigurasi
uv run python tools/performance_diagnose.py    # Diagnosis kinerja LLM
uv run python tools/inspect_schema.py          # Pemeriksaan indeks dan batasan Neo4j
uv run python tools/migrate_embeddings.py      # Migrasi model Embedding (membuat ulang vektor setelah mengganti model)
```

### Migrasi Model Embedding

Setelah mengganti model embedding (mis. `nomic-embed-text` → `bge-m3`), Anda dapat menggunakan tool migrasi untuk membuat ulang semua vektor yang ada, memastikan kualitas pencarian tetap konsisten:

```bash
# Pratinjau jumlah yang perlu dimigrasi
uv run python tools/migrate_embeddings.py --dry-run

# Migrasi penuh (mendukung lanjut dari titik henti)
uv run python tools/migrate_embeddings.py

# Hanya memigrasi group tertentu
uv run python tools/migrate_embeddings.py --group-id myproject

# Melanjutkan dari titik henti (jalankan ulang setelah terputus)
uv run python tools/migrate_embeddings.py --resume
```

> **Kompatibilitas**: `bge-m3` secara native 1024 dimensi, sistem otomatis memotongnya menjadi 768 dimensi agar kompatibel dengan indeks vektor Neo4j yang ada. Data sebelum dan sesudah migrasi dapat berdampingan, tetapi disarankan menjalankan migrasi penuh untuk mendapatkan kualitas pencarian terbaik.

## Dokumentasi

- [Instruksi Penggunaan Tool](../使用工具的指令.md) — panduan penggunaan tool MCP dan praktik terbaik
- [Graphiti Memory Rules](../graphiti-memory-rules.md) — penjelasan aturan memori

## Lisensi

MIT License
