# Graphiti MCP Server

Bilgi grafiği bellek hizmeti — çoklu LLM sağlayıcılarını (Ollama / GLM / GROQ / OpenRouter / DeepSeek) ve Neo4j grafik veritabanını entegre eden bir MCP sunucusu.

[getzep/graphiti](https://github.com/getzep/graphiti) temel alınarak geliştirilmiştir; yerel Ollama ile bulut LLM arasında esnek geçişi destekler ve Embedding sağlayıcısı bağımsız olarak belirtilebilir (LLM'den ayrıştırılmış).

## Öne Çıkan Özellikler

- **Akıllı bellek yönetimi** — Karmaşık bellek ilişkilerini depolamak ve almak için bilgi grafiği kullanır
- **Anlamsal arama** — Vektör gömmelerine dayalı hibrit arama (vektör + anahtar kelime + grafik gezinme)
- **16 arama stratejisi** — Gelişmiş arama; RRF, MMR, Cross-Encoder gibi çeşitli yeniden sıralama yöntemlerini destekler
- **Çoklu LLM sağlayıcısı** — Ollama (yerel), GLM (Zhipu AI ücretsiz), GROQ (yüksek hızlı çıkarım), OpenRouter (çeşitli modelleri toplar), DeepSeek (Deepseek) desteklenir; ortam değişkenleriyle tek tuşla geçiş yapılır
- **Embedding ile LLM'in ayrıştırılması** — `EMBEDDING_PROVIDER` ile gömücü bağımsız olarak belirtilebilir; bulut LLM otomatik olarak yerel `bge-m3`'e geri döner
- **Çift model dağıtımı** — Ollama modunda karmaşık görevler ana modeli kullanır, basit görevler performansı artırmak için otomatik olarak küçük modele geçer
- **Akıllı içerik bölütleme** — Uzun metinler otomatik olarak parçalara ayrılarak işlenir, LLM yükü azaltılır (eşik yapılandırılabilir)
- **Arka planda bellek işleme** — Bellek ekleme arka planda çalıştırılabilir, MCP çağrısı anında geri döner; görev durumu SQLite ile kalıcı olarak saklanır, yeniden başlatma sonrasında tamamlanmamış görevler otomatik olarak geri yüklenir
- **Bellek tekilleştirme** — Mevcut yüksek benzerlikteki bellekleri otomatik olarak tespit ederek yinelenen depolamayı önler
- **Çelişki tespiti** — İki varlık arasındaki çelişkili gerçekleri tespit eder, geçersiz ve geçerli bilgileri ayırt eder
- **Topluluk tespiti** — Label Propagation algoritmasına dayalı olarak ilgili varlıkları otomatik olarak kümeler
- **Önem takibi** — Varlık erişim sıklığını otomatik olarak kaydeder, arama sonuçları öneme göre sıralanır
- **Akıllı unutma** — Eski, düşük erişimli bellekleri tespit edip temizler, grafiği sade tutar
- **Toplu içe aktarma** — Tek seferde birden fazla bellek gönderir, büyük veri taşımalarına uygundur
- **Yapılandırılmış üçlüler** — "Özne-İlişki-Nesne" doğrudan eklenir, LLM çıkarımı atlanır, saniyeler içinde tamamlanır
- **Web yönetim arayüzü** — Yerleşik gösterge paneli, gözatma, arama, bilgi grafiği görselleştirme, AI soru-cevap, topluluk gözatma, kalite bakımı, toplu içe aktarma, çalışma zamanı ayarları
- **Çok dilli destek (i18n)** — Yanıt mesajları 33 dili destekler (zh-TW / en / zh-CN / ja / pt-BR / ko / es / de / fr vb. dahil; zh-TW/en/zh-CN/ja elle yazılmış, geri kalanlar generated katmanı tarafından sağlanmaktadır); MCP araçları `SERVER_LANG`'a, REST API ise HTTP `Accept-Language`'e göre otomatik olarak müzakere eder
- **Koyu/açık tema** — Web arayüzü tema değiştirmeyi destekler
- **Güvenli mod** — Varlık çıkarımını atlayan hızlı bellek eklemesi seçilebilir
- **Docker desteği** — Yerleşik Dockerfile, konteynerli dağıtımı destekler
- **Eşzamanlılık güvenliği** — asyncio.Lock başlatmayı korur, yarış durumlarını önler
- **Katmanlı sağlık kontrolü** — `/health` (liveness) + `/health/ready` (readiness)

## Sistem Gereksinimleri

| Öğe | Gereksinim |
|------|------|
| Python | 3.10+ (3.11+ önerilir) |
| Neo4j | 4.0+ (`bolt://localhost:7687`) |
| LLM sağlayıcısı | Ollama / GLM / GROQ / OpenRouter / DeepSeek (beşinden biri) |
| Node.js | 18+ (yalnızca PM2 arka plan çalıştırması için, isteğe bağlı) |
| Disk alanı | ~3GB (Ollama modelleri + Neo4j verileri) |

### LLM Sağlayıcı Seçimi

`LLM_PROVIDER` ortam değişkeniyle geçiş yapılır (`ollama` / `glm` / `groq` / `openrouter` / `deepseek`):

| Sağlayıcı | Özellikler | LLM modeli | Embedding | Uygun senaryo |
|--------|------|----------|-----------|----------|
| **Ollama** (varsayılan) | Tamamen yerel, veriler cihazdan ayrılmaz | `qwen2.5:3b` | `bge-m3` (Çince + RAG'da üstün) | GPU'su olan, gizliliğe önem veren |
| **GLM** | Ücretsiz bulut, kararlı ve limitsiz | `glm-4-flash` (ücretsiz) | `embedding-3` | GPU'su olmayan, arama yoğun senaryolar |
| **GROQ** | Ultra yüksek hızlı çıkarım | `llama-3.3-70b-versatile` | Ollama `bge-m3`'e geri döner | Ara sıra yazma, kaliteyi önemseyen |
| **OpenRouter** | Çeşitli modelleri toplar, ücretsiz kotalar dahil | `stepfun/step-3.5-flash:free` vb. | Ollama `bge-m3`'e geri döner | Belirli bulut modeli kullanmak isteyen |
| **DeepSeek** | Deepseek bulutu, yüksek maliyet/performans | `deepseek-v4-flash` / `deepseek-v4-pro` | Ollama `bge-m3`'e geri döner | Çince anlama, düşük maliyetli bulut |

> **Embedding ile LLM'in ayrıştırılması**: Gömücü `EMBEDDING_PROVIDER` (`ollama` / `glm`) ile bağımsız olarak belirtilir; ayarlanmadığında `LLM_PROVIDER`'ı takip eder. Aslında yalnızca `glm` GLM `embedding-3` kullanır; geri kalanlar (Embedding sunmayan GROQ / OpenRouter / DeepSeek gibi bulut LLM'ler dahil) tümü otomatik olarak Ollama `bge-m3` kullanır. **Bu nedenle herhangi bir bulut LLM kullanırken, gömme hizmeti için yine de yerel Ollama gereklidir (embedding de glm olarak ayarlanmadıkça).**

#### Ollama modu (yerel)

```bash
# LLM ana modeli (qwen2.5:3b önerilir, hız ve kararlılık arasında en iyi denge)
ollama pull qwen2.5:3b

# Gömme modeli (zorunlu, vektör araması için kullanılır)
ollama pull bge-m3
```

> **Model seçimi notları**:
> - `qwen2.5:3b` — Önerilir, ~2s/çağrı, ~100 t/s, graphiti-core yapılandırılmış çıktıda %100 kararlı
> - `qwen2.5:7b` — Daha iyi sonuç verir ancak 5-10 kat daha yavaş, kaliteyi önemseyen senaryolara uygun
> - `qwen2.5:1.5b` — En hızlı ancak **kararsız** (yapılandırılmış JSON başarı oranı yalnızca %33), kullanımı önerilmez

#### GLM modu (Zhipu AI bulutu)

```bash
# .env ayarları
LLM_PROVIDER=glm
GLM_API_KEY=your_api_key          # https://open.bigmodel.cn adresinden alınır
GLM_MODEL=glm-4-flash             # Ücretsiz model
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768      # Neo4j vektör indeksi boyutuyla tutarlı olmalı
```

> **GLM performans referansı**: Yazma ~22s (kısa metin), arama ~0.34s, sıfır Rate Limit hatası, yerel Ollama'dan 2-5 kat daha yavaş ancak tamamen ücretsiz.

#### GROQ modu (yüksek hızlı çıkarım)

```bash
# .env ayarları
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key         # https://console.groq.com adresinden alınır
GROQ_MODEL=llama-3.3-70b-versatile
```

> **Not**: GROQ Embedding hizmeti sunmaz; Ollama gömücüsü (otomatik geri dönüş) ile eşleştirilmeli ya da `EMBEDDING_PROVIDER` glm olarak ayarlanmalıdır. GROQ'un katı bir Rate Limit'i vardır, yüksek frekanslı kullanım çok sayıda yeniden deneme tetikler.

#### OpenRouter modu (çeşitli modelleri toplar)

```bash
# .env ayarları
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_api_key       # https://openrouter.ai/keys adresinden alınır
OPENROUTER_MODEL=stepfun/step-3.5-flash:free   # Herhangi bir OpenRouter modeliyle değiştirilebilir
```

> **Not**: OpenRouter Embedding sunmaz, otomatik olarak Ollama `bge-m3`'e geri döner. Model listesi için https://openrouter.ai/models adresine bakın (birden fazla `:free` ücretsiz model dahil).

#### DeepSeek modu (Deepseek)

```bash
# .env ayarları
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key         # https://platform.deepseek.com adresinden alınır
DEEPSEEK_MODEL=deepseek-v4-flash      # Önerilir; ya da deepseek-v4-pro (daha iyi sonuç)
```

> **Not**: DeepSeek Embedding sunmaz, otomatik olarak Ollama `bge-m3`'e geri döner. `deepseek-chat` / `deepseek-reasoner` 2026-07-24 tarihinde kullanımdan kaldırılacaktır; `deepseek-v4-flash` / `deepseek-v4-pro` kullanmanız önerilir. DeepSeek, `json_object` modunda prompt'un "json" dizesini içermesini katı şekilde gerektirir; istemcide yerleşik bir güvence koruması bulunur, ek ayar gerekmez.

## Hızlı Başlangıç

### 1. Ön Hazırlık

Neo4j'nin yerel makinede çalıştığını doğrulayın ve seçtiğiniz LLM sağlayıcısına göre ilgili hizmetleri hazırlayın:

```bash
# Neo4j'nin çalıştığını doğrulayın (zorunlu)
neo4j status
# Ya da Docker kullanın: docker run -d -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/your_password neo4j:latest

# Ollama modu: Ollama'nın çalıştığını doğrulayın
ollama list
# Başlatılmamışsa: ollama serve

# GLM / GROQ modu: yalnızca geçerli bir API Key gerekir, yerel hizmet gerekmez
```

### 2. Bağımlılıkları Kurun

```bash
git clone <repo-url>
cd graphiti
uv sync
```

> **Not**: Bu proje bağımlılıkları yönetmek için [uv](https://github.com/astral-sh/uv) kullanır. Kurulu değilse: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 3. Ortamı Yapılandırın

```bash
cp .env.example .env
```

`.env` dosyasını düzenleyin, **en az** aşağıdaki öğelerin değiştirilmesi gerekir:

```bash
NEO4J_PASSWORD=your_actual_password  # Zorunlu: Neo4j şifresi
LLM_PROVIDER=ollama                  # ollama / glm / groq / openrouter / deepseek
OLLAMA_MODEL=qwen2.5:3b              # Ollama modu: yerel LLM modeli
# GLM_API_KEY=your_key               # GLM modu: Zhipu AI API Key
# GROQ_API_KEY=your_key              # GROQ modu: GROQ API Key
# OPENROUTER_API_KEY=your_key        # OpenRouter modu: API Key
# DEEPSEEK_API_KEY=your_key          # DeepSeek modu: API Key
```

### 4. Hizmeti Başlatın

```bash
# HTTP modu (önerilir, Web yönetim arayüzünü içerir)
uv run python graphiti_mcp_server.py --transport http --port 8000

# Ya da PM2 arka plan çalıştırması kullanın (uzun süreli çalışma için önerilir)
pm2 start ecosystem.config.cjs
```

### 5. Hizmeti Doğrulayın

Başlattıktan sonra aşağıdaki uç noktalara erişebilirsiniz:

| Uç nokta | Açıklama |
|------|------|
| http://localhost:8000/ | Web yönetim arayüzü |
| http://localhost:8000/mcp | MCP uç noktası (MCP istemcilerinin bağlanması için) |
| http://localhost:8000/health | Sağlık kontrolü (liveness) |
| http://localhost:8000/health/ready | Derin kontrol (Neo4j bağlantısı dahil) |
| http://localhost:8000/api/stats | REST API istatistikleri |

## Proje Yapısı

```
graphiti/
├── graphiti_mcp_server.py        # Ana giriş — MCP araç tanımları (19 araç)
├── src/
│   ├── config.py                 # Yapılandırma yönetimi (GraphitiConfig, JSON/.env katmanlamayı destekler)
│   ├── web_api.py                # Web yönetim arayüzü REST API (30+ uç nokta)
│   ├── ollama_graphiti_client.py  # Ollama LLM istemcisi (çift model dağıtımı)
│   ├── openai_compat_client.py   # OpenAI uyumlu LLM temel sınıfı (json_object + basitleştirilmiş şema + json güvence koruması)
│   ├── glm_client.py             # GLM (Zhipu AI) LLM istemcisi (OpenAICompatClient'tan türetilmiş)
│   ├── openrouter_client.py      # OpenRouter LLM istemcisi (OpenAICompatClient'tan türetilmiş)
│   ├── deepseek_client.py        # DeepSeek LLM istemcisi (OpenAICompatClient'tan türetilmiş)
│   ├── ollama_embedder.py        # Ollama gömme modeli adaptörü
│   ├── content_preprocessor.py   # Akıllı içerik bölütleme (uzun metin otomatik parçalama)
│   ├── deduplication.py          # Bellek tekilleştirme (kosinüs benzerliği karşılaştırması)
│   ├── importance.py             # Önem takibi ve akıllı unutma
│   ├── safe_memory_add.py        # Güvenli bellek ekleme (varlık çıkarımını atlar)
│   ├── task_store.py             # Arka plan görevi SQLite kalıcı depolama (TaskStore)
│   ├── timezone_utils.py         # Saat dilimi dönüştürme (UTC→yerel saat dilimi gösterimi)
│   ├── i18n.py                   # Arka uç çok dilli destek (REST Accept-Language'e, MCP SERVER_LANG'e göre)
│   ├── i18n_generated.py         # Otomatik oluşturulan dil katmanı geçersiz kılmaları (GENERATED_MESSAGE_OVERRIDES)
│   ├── exceptions.py             # Yapılandırılmış istisna işleme (12 istisna sınıfı)
│   └── logging_setup.py          # Günlük sistemi (zaman tabanlı döndürme + performans izleme)
├── web/                          # Web yönetim arayüzü ön ucu (SPA, build yok)
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js                # REST API sarmalayıcısı
│       ├── components.js         # UI bileşeni render (topluluk sayfası dahil)
│       └── app.js                # SPA yönlendirme, durum yönetimi
├── tests/                        # Test paketi (203 test)
│   ├── test_content_preprocessor.py  # Bölütleme mantığı testi (17 adet)
│   ├── test_new_features.py      # Yeni özellik testi (32 adet)
│   ├── test_i18n.py             # Çok dilli destek testi (57 adet)
│   ├── test_unit.py              # Birim testi
│   ├── test_web_api.py           # Web API testi
│   ├── test_web_ui_features.py   # Web UI işlev testi
│   ├── test_integration_manual.py # Manuel entegrasyon testi
│   └── bench_deepseek_flash_vs_pro.py # DeepSeek flash/pro performans karşılaştırma betiği
├── tools/                        # Geliştirme tanılama araçları
│   ├── status_report.py          # Birleşik durum raporu
│   ├── validate_config.py        # Yapılandırma doğrulaması
│   ├── performance_diagnose.py   # Performans tanılaması
│   ├── inspect_schema.py         # Neo4j yapı kontrolü
│   ├── batch_reprocess.py        # Toplu yeniden işleme
│   └── migrate_embeddings.py     # Embedding model taşıması (model değiştirildikten sonra vektörleri yeniden oluştur)
├── docs/                         # Belgeler
├── logs/                         # Günlükler (zaman tabanlı döndürme, varsayılan 30 gün saklanır)
├── Dockerfile                    # Docker konteynerli dağıtım
└── ecosystem.config.cjs          # PM2 yapılandırması
```

## MCP İstemci Ayarları

### HTTP modu (önerilir)

Claude Code, Cline gibi HTTP destekleyen MCP istemcileri için uygundur:

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

### STDIO modu

Claude Desktop gibi süreci doğrudan başlatması gereken istemciler için uygundur:

**Yapılandırma dosyası konumu:**
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

> **Not**: SSE modu (`--transport sse`) artık önerilmemektedir. MCP 1.x'te session başlatma uyumluluk sorunları vardır; lütfen HTTP modunu kullanın.

## MCP Araçları (19 adet)

### Bellek Yönetimi (7 adet)

| Araç | Açıklama |
|------|------|
| `add_memory_simple` | Bilgi grafiğine bellek ekler (arka plan işleme, akıllı bölütleme, tekilleştirme kontrolü destekler) |
| `add_episode_bulk` | Birden fazla belleği toplu ekler (varsayılan olarak arka plan işleme) |
| `add_triplet` | Yapılandırılmış üçlü ekleme (LLM atlanır, saniyeler içinde tamamlanır) |
| `search_memory_nodes` | Bellek düğümlerini arar (16 arama stratejisi, zaman filtresi destekler) |
| `search_memory_facts` | Bellek gerçeklerini arar (ilişki türü filtresi, zaman aralığı, geçerlilik filtresi destekler) |
| `advanced_search` | Gelişmiş arama (16 strateji, düğüm+kenar+topluluk+parça döndürür) |
| `get_episodes` | Son bellek parçalarını alır |

### Bilgi Analizi (3 adet)

| Araç | Açıklama |
|------|------|
| `check_conflicts` | İki varlık arasındaki gerçek çelişkilerini tespit eder (geçerli vs geçersiz) |
| `get_node_edges` | Bir düğümün gelen ve giden kenar ilişkilerini keşfeder |
| `build_communities` | Topluluk tespiti ve kümelemeyi tetikler (varsayılan olarak arka plan işleme) |

### Bellek Bakımı (2 adet)

| Araç | Açıklama |
|------|------|
| `get_stale_memories` | Eski, düşük erişimli bellekleri sorgular |
| `cleanup_stale_memories` | Eski bellekleri temizler (varsayılan dry_run önizleme modu) |

### Görev Yönetimi

| Araç | Açıklama |
|------|------|
| `get_memory_task_status` | Arka plan bellek işleme görevinin ilerlemesini ve sonuçlarını sorgular |

### Silme ve Sorgulama

| Araç | Açıklama |
|------|------|
| `delete_episode` | Bellek parçasını siler |
| `delete_entity_edge` | Varlık kenarını (ilişki) siler |
| `get_entity_edge` | Varlık kenarı ayrıntılı bilgisini alır |

### Sistem Yönetimi

| Araç | Açıklama |
|------|------|
| `get_status` | Hizmet durumunu alır (Neo4j, LLM, gömücü) |
| `test_connection` | Neo4j / LLM / gömücü bağlantısını test eder |
| `clear_graph` | Grafik veritabanını temizler (group_id'ye göre temizlemeyi destekler) |

## Araç Parametreleri

### add_memory_simple

| Parametre | Tür | Zorunlu | Varsayılan | Açıklama |
|------|------|------|--------|------|
| `name` | string | E | | Bellek adı |
| `episode_body` | string | E | | Bellek içeriği (800 karakteri aşarsa otomatik bölütlenir) |
| `group_id` | string | | `"default"` | Grup ID'si (projeye göre yalıtım önerilir) |
| `source` | string | | `"text"` | Kaynak türü: `text` / `json` / `message` |
| `source_description` | string | | `"MCP Server"` | Kaynak açıklaması |
| `use_safe_mode` | bool | | `false` | Güvenli mod (varlık çıkarımını atlar, hızlı ancak bellek aranamaz) |
| `background` | bool | | `false` | Arka plan işleme (anında task_id döndürür, uzun metinler için uygun) |
| `force` | bool | | `false` | Tekilleştirme kontrolünü atlar (zorla ekleme) |
| `excluded_entity_types` | list | | | Hariç tutulan varlık türleri (gereksiz çıkarım miktarını azaltır) |

> **Performans ipuçları**:
> - Kısa metin (<800 karakter): doğrudan işlenir, genellikle 30-40 saniyede tamamlanır
> - Uzun metin (>800 karakter): otomatik olarak birden fazla parçaya bölünür, `add_episode_bulk` ile eşzamanlı işlenir (sıralı işlemeden ~%33 daha hızlı)
> - `background=true` kullanarak MCP çağrısının bloke olmasını önleyebilir, `get_memory_task_status` ile ilerlemeyi takip edebilirsiniz
> - `use_safe_mode=true` saniyeler içinde tamamlanır ancak bellek search araçlarıyla bulunamaz
> - Tekilleştirme etkinken, yüksek benzerlikteki bellekler hakkında uyarı verilir (`force=true` ile atlanabilir)

### add_episode_bulk

| Parametre | Tür | Zorunlu | Varsayılan | Açıklama |
|------|------|------|--------|------|
| `episodes` | list | E | | Bellek listesi, her öğe `name` ve `content` içerir |
| `group_id` | string | | `"default"` | Grup ID'si |
| `source` | string | | `"text"` | Kaynak türü |
| `background` | bool | | `true` | Arka plan işleme (toplu işlem genellikle zaman alır) |

### add_triplet

| Parametre | Tür | Zorunlu | Varsayılan | Açıklama |
|------|------|------|--------|------|
| `source_name` | string | E | | Kaynak varlık adı (örn. "Alice") |
| `target_name` | string | E | | Hedef varlık adı (örn. "Google") |
| `relation_name` | string | E | | İlişki adı (örn. "works_at") |
| `fact` | string | E | | Gerçek açıklaması (örn. "Alice works at Google") |
| `group_id` | string | | `"default"` | Grup ID'si |
| `source_labels` | list | | | Kaynak varlık etiketleri |
| `target_labels` | list | | | Hedef varlık etiketleri |

### search_memory_nodes

| Parametre | Tür | Zorunlu | Varsayılan | Açıklama |
|------|------|------|--------|------|
| `query` | string | E | | Arama anahtar kelimesi (doğal dil) |
| `max_nodes` | int | | `10` | Maksimum döndürülen sayı |
| `group_ids` | list | | | Grup filtresi (birden fazla grupta ortak arama) |
| `entity_types` | list | | | Varlık türü filtresi |
| `search_recipe` | string | | | Arama stratejisi (gelişmiş aramaya bakın) |
| `created_after` | string | | | Oluşturulma zamanı alt sınırı (ISO datetime) |
| `created_before` | string | | | Oluşturulma zamanı üst sınırı (ISO datetime) |

### search_memory_facts

| Parametre | Tür | Zorunlu | Varsayılan | Açıklama |
|------|------|------|--------|------|
| `query` | string | E | | Arama anahtar kelimesi |
| `max_facts` | int | | `10` | Maksimum döndürülen sayı |
| `group_ids` | list | | | Grup filtresi |
| `center_node_uuid` | string | | | Merkez düğüm UUID'si (belirli düğümün ilişkilerini keşfetme) |
| `edge_types` | list | | | İlişki türü filtresi (örn. `["works_at"]`) |
| `created_after` | string | | | Oluşturulma zamanı alt sınırı (ISO datetime) |
| `created_before` | string | | | Oluşturulma zamanı üst sınırı (ISO datetime) |
| `only_valid` | bool | | `false` | Yalnızca geçersiz olmayan gerçekleri döndür |

### advanced_search

| Parametre | Tür | Zorunlu | Varsayılan | Açıklama |
|------|------|------|--------|------|
| `query` | string | E | | Arama anahtar kelimesi |
| `search_recipe` | string | | `"combined_rrf"` | Arama stratejisi (16 seçenek) |
| `max_results` | int | | `10` | Maksimum döndürülen sayı |
| `group_ids` | list | | | Grup filtresi |
| `center_node_uuid` | string | | | Merkez düğüm UUID'si |

**Kullanılabilir arama stratejileri (search_recipe):**

| Kategori | Strateji | Açıklama |
|------|------|------|
| Birleşik | `combined_rrf` | Birleşik RRF füzyonu (varsayılan, önerilir) |
| Birleşik | `combined_mmr` | Birleşik MMR çeşitlilik yeniden sıralaması |
| Birleşik | `combined_cross_encoder` | Birleşik Cross-Encoder ince sıralama |
| Kenar | `edge_rrf` / `edge_mmr` / `edge_cross_encoder` | Kenar araması (3 sıralama) |
| Kenar | `edge_node_distance` / `edge_episode_mentions` | Kenar araması (grafik mesafesi/atıf sayısı) |
| Düğüm | `node_rrf` / `node_mmr` / `node_cross_encoder` | Düğüm araması (3 sıralama) |
| Düğüm | `node_node_distance` / `node_episode_mentions` | Düğüm araması (grafik mesafesi/atıf sayısı) |
| Topluluk | `community_rrf` / `community_mmr` / `community_cross_encoder` | Topluluk araması |

### check_conflicts

| Parametre | Tür | Zorunlu | Varsayılan | Açıklama |
|------|------|------|--------|------|
| `source_name` | string | E | | Kaynak varlık adı |
| `target_name` | string | E | | Hedef varlık adı |
| `group_id` | string | | `"default"` | Grup ID'si |

### get_node_edges

| Parametre | Tür | Zorunlu | Varsayılan | Açıklama |
|------|------|------|--------|------|
| `node_uuid` | string | E | | Düğüm UUID'si |
| `include_inbound` | bool | | `true` | Gelen kenarları dahil et |
| `include_outbound` | bool | | `true` | Giden kenarları dahil et |
| `max_edges` | int | | `50` | Maksimum döndürülen sayı |

### build_communities

| Parametre | Tür | Zorunlu | Varsayılan | Açıklama |
|------|------|------|--------|------|
| `group_ids` | list | | | Grup belirt (boş bırakılırsa tümü) |
| `background` | bool | | `true` | Arka plan işleme |

### get_stale_memories

| Parametre | Tür | Zorunlu | Varsayılan | Açıklama |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Kaç günden fazla erişilmeyenler eski sayılır |
| `min_access_count` | int | | `2` | Erişim sayısı bu değerin altında olanlar listelenir |
| `group_id` | string | | | Grup filtresi |
| `limit` | int | | `50` | Maksimum döndürülen sayı |

### cleanup_stale_memories

| Parametre | Tür | Zorunlu | Varsayılan | Açıklama |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Eskime gün eşiği |
| `min_access_count` | int | | `2` | Minimum erişim sayısı eşiği |
| `group_id` | string | | | Grup filtresi |
| `dry_run` | bool | | `true` | Önizleme modu (gerçekte silmez) |
| `limit` | int | | `50` | Maksimum işlenecek sayı |

### get_memory_task_status

| Parametre | Tür | Zorunlu | Açıklama |
|------|------|------|------|
| `task_id` | string | E | Arka plan görev ID'si (`add_memory_simple(background=true)` tarafından döndürülür) |

## Web Yönetim Arayüzü

HTTP modunda `http://localhost:8000/` adresine erişerek kullanabilirsiniz.

**İşlevler:**
- Gösterge paneli — Düğüm sayısı, gerçek sayısı, bellek parçası sayısı istatistikleri
- Varlık düğümleri — Gözatma, filtreleme, vektör araması
- Gerçek ilişkileri — Gözatma, filtreleme, vektör araması
- Bellek parçaları — Gözatma, tam metin araması, silme
- Topluluk gözatma — Topluluk düğümü listesi, özet, topluluk oluşturmayı tetikleme
- Üçlü formu — "Özne-İlişki-Nesne" yapılandırılmış bilgiyi doğrudan ekleme
- Grup yönetimi — Gruba göre filtreleme, toplu silme
- Bilgi grafiği görselleştirme — Düğüm ilişkilerinin grafiksel gösterimi
- AI soru-cevap — Bilgi grafiğine dayalı akıllı soru-cevap
- Kalite bakımı — Bellek kalitesi metrikleri ve temizleme araçları
- Toplu içe aktarma — Tek seferde birden fazla bellek parçası içe aktarma (JSON, tek seferinde 500 kayıt sınırı)
- Çalışma zamanı ayarları — Geçerli ayarları görüntüleme ve yeniden başlatmadan bazı parametreleri ayarlama
- Tema değiştirme — Koyu/açık tema

**REST API:**

| Uç nokta | Yöntem | Açıklama |
|------|------|------|
| `/api/stats` | GET | Gösterge paneli istatistikleri |
| `/api/groups` | GET | Tüm group_id'leri al |
| `/api/groups/stats` | GET | Her grup için düğüm/gerçek/parça istatistikleri |
| `/api/nodes` | GET | Varlık düğümlerini gözat (sayfalı) |
| `/api/facts` | GET | Gerçekleri gözat (sayfalı) |
| `/api/episodes` | GET | Bellek parçalarını gözat (sayfalı) |
| `/api/nodes/{uuid}/relations` | GET | Düğümün gelen/giden kenar ilişkilerini al |
| `/api/search/nodes` | GET | Vektör araması ile düğüm ara |
| `/api/search/facts` | GET | Vektör araması ile gerçek ara |
| `/api/search/episodes` | GET | Bellek parçalarını ara |
| `/api/search/advanced` | GET | Gelişmiş arama (16 strateji) |
| `/api/communities` | GET | Topluluk düğümlerini gözat (sayfalı) |
| `/api/communities/build` | POST | Topluluk oluşturmayı tetikle |
| `/api/memory/add` | POST | Tekil bellek ekle |
| `/api/memory/add-bulk` | POST | Toplu bellek ekle |
| `/api/memory/add-triplet` | POST | Üçlü ekle |
| `/api/import/episodes` | POST | Bellek parçalarını toplu içe aktar (JSON, tek seferinde 500 kayıt sınırı) |
| `/api/memory/tasks` | GET | Arka plan görevlerini listele (durum filtresi destekler) |
| `/api/memory/tasks/{id}` | GET | Tek görev durumunu sorgula |
| `/api/timeline` | GET | Zaman çizelgesi gözatma |
| `/api/graph/subgraph` | GET | Alt grafı al (görselleştirme) |
| `/api/graph/all` | GET | Tam grafı al (görselleştirme) |
| `/api/ask` | GET | AI soru-cevap (grafik tabanlı arama) |
| `/api/analytics/top-nodes` | GET | Yüksek bağlantılı/yüksek erişimli düğümler |
| `/api/analytics/quality` | GET | Bilgi grafiği kalite metrikleri |
| `/api/analytics/stale` | GET | Eski bellekleri sorgula |
| `/api/analytics/cleanup` | POST | Eski bellekleri temizle |
| `/api/config` | GET | Geçerli ayarları al (API anahtarı hariç) |
| `/api/config` | PATCH | Çalışma zamanında değiştirilebilir ayarları güncelle (yalnızca mevcut süreç için geçerli, yeniden başlatmada sıfırlanır) |
| `/api/nodes/{uuid}` | DELETE | Düğümü sil |
| `/api/episodes/{uuid}` | DELETE | Bellek parçasını sil |
| `/api/facts/{uuid}` | DELETE | Gerçeği sil |
| `/api/groups/{group_id}` | DELETE | Tüm grubu sil |

## Yapılandırma

### Ortam değişkenleri (.env)

Yapılandırma katmanlama mekanizması kullanır: JSON yapılandırma dosyası temeldir, ortam değişkenleri tek tek değerleri geçersiz kılar.

```bash
# === Zorunlu ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password        # Değiştirilmesi zorunlu

# === LLM sağlayıcı seçimi ===
LLM_PROVIDER=ollama                 # ollama / glm / groq / openrouter / deepseek

# === Embedding sağlayıcısı (isteğe bağlı, varsayılan olarak LLM_PROVIDER'ı takip eder) ===
# Yalnızca glm GLM Embedding kullanır, geri kalanlar Ollama bge-m3 kullanır
# EMBEDDING_PROVIDER=ollama         # ollama / glm

# === Ollama yapılandırması (LLM_PROVIDER=ollama olduğunda kullanılır) ===
OLLAMA_MODEL=qwen2.5:3b             # Ana model (qwen2.5:3b önerilir)
OLLAMA_SMALL_MODEL=qwen2.5:3b       # Küçük model (basit görevler için, farklı model seçilebilir)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.1

# === GLM yapılandırması (LLM_PROVIDER=glm olduğunda kullanılır) ===
GLM_API_KEY=your_api_key            # https://open.bigmodel.cn adresinden alınır
GLM_MODEL=glm-4-flash               # Ücretsiz model
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768

# === GROQ yapılandırması (LLM_PROVIDER=groq olduğunda kullanılır) ===
GROQ_API_KEY=your_api_key           # https://console.groq.com adresinden alınır
GROQ_MODEL=llama-3.3-70b-versatile

# === OpenRouter yapılandırması (LLM_PROVIDER=openrouter olduğunda kullanılır) ===
OPENROUTER_API_KEY=your_api_key     # https://openrouter.ai/keys adresinden alınır
OPENROUTER_MODEL=stepfun/step-3.5-flash:free

# === DeepSeek yapılandırması (LLM_PROVIDER=deepseek olduğunda kullanılır) ===
DEEPSEEK_API_KEY=your_api_key       # https://platform.deepseek.com adresinden alınır
DEEPSEEK_MODEL=deepseek-v4-flash    # Ya da deepseek-v4-pro

# === Ollama gömme modeli (glm gömme dışında her zaman kullanılır) ===
OLLAMA_EMBEDDING_MODEL=bge-m3
OLLAMA_EMBEDDING_DIMENSIONS=768

# === Gösterim ve dil (isteğe bağlı) ===
GRAPHITI_DISPLAY_TIMEZONE=Asia/Taipei # API'nin döndürdüğü zaman damgası gösterim saat dilimi (IANA adı; depolama UTC olarak kalır)
SERVER_LANG=zh-TW                     # MCP araçları yanıt dili (tam locale için src/i18n.py'ye bakın); REST API Accept-Language'e göre değişir

# === Bellek performansı (isteğe bağlı) ===
GRAPHITI_CHUNK_THRESHOLD=800         # Akıllı bölütlemeyi tetikleyen karakter sayısı eşiği
GRAPHITI_MAX_CHUNK_SIZE=600          # Her parçanın maksimum karakter sayısı
GRAPHITI_MAX_COROUTINES=10            # Maksimum eşzamanlı coroutine sayısı
GRAPHITI_DEFAULT_BACKGROUND=false    # Varsayılan olarak arka planda işlenip işlenmeyeceği
TASK_DB_PATH=data/tasks.db           # Arka plan görevi SQLite kalıcı depolama yolu

# === Önem takibi ve akıllı unutma (isteğe bağlı) ===
ENABLE_IMPORTANCE_TRACKING=true      # Erişim takibini etkinleştir
IMPORTANCE_WEIGHT=0.1                # Önem ağırlığı
STALE_DAYS_THRESHOLD=30              # Eskime gün eşiği
STALE_MIN_ACCESS_COUNT=2             # Minimum erişim sayısı

# === Günlük ===
LOG_FILE=logs/graphiti_mcp_server.log
LOG_LEVEL=INFO
```

> **Tam ortam değişkeni listesi** için `.env.example` dosyasına bakın

### JSON yapılandırma dosyası

Sürüm kontrolü gerektiren yapılandırma için uygundur (ortam değişkenleri yine de geçersiz kılabilir):

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

## PM2 Arka Plan Çalıştırması

```bash
npm install -g pm2

pm2 start ecosystem.config.cjs      # Başlat
pm2 status                           # Durum
pm2 logs graphiti-mcp-http           # Anlık günlükler
pm2 restart graphiti-mcp-http --update-env  # Yeniden başlat (.env'i yeniden yükler)

pm2 save && pm2 startup              # Açılışta otomatik başlatmayı ayarla
```

> **İpucu**: `.env` dosyasını değiştirdikten sonra `--update-env` bayrağıyla yeniden başlatmanız gerekir, aksi takdirde ortam değişkenleri güncellenmez.

## Docker Dağıtımı

```bash
docker build -t graphiti-mcp .

# Not: Docker konteyneri Neo4j ve Ollama'ya bağlanabilmelidir
# host network kullanmak en basit yöntemdir
docker run -p 8000:8000 --env-file .env --network host graphiti-mcp

# Ya da harici hizmet adreslerini açıkça belirtin
docker run -p 8000:8000 \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --env-file .env graphiti-mcp
```

## Test

```bash
# Tüm testleri çalıştır (203 adet, yaklaşık 1 saniye)
uv run python -m pytest tests/

# Ayrıntılı çıktı
uv run python -m pytest tests/ -v

# Yalnızca belirli testleri çalıştır
uv run python -m pytest tests/test_content_preprocessor.py -v
uv run python -m pytest tests/test_new_features.py -v
uv run python -m pytest tests/test_unit.py -v
```

> **Not**: `test_integration_manual.py` içindeki 3 async test `pytest-asyncio` kurulumunu gerektirir; eksik olduğunda Failed gösterir ancak diğer testleri etkilemez. `bench_deepseek_flash_vs_pro.py` bir performans karşılaştırma betiğidir, birim testi değildir.

## Sorun Giderme

### Neo4j bağlantı hatası

```bash
neo4j status                              # Hizmet durumunu kontrol et
cypher-shell -u neo4j -p your_password    # Şifrenin doğru olduğunu doğrula
curl http://localhost:7474                 # HTTP portunu doğrula
```

Yaygın nedenler:
- Neo4j başlatılmamış
- Şifre yanlış (`.env` içindeki `NEO4J_PASSWORD`)
- Port meşgul ya da güvenlik duvarı tarafından engelleniyor

### LLM bağlantı hatası

**Ollama modu:**
```bash
ollama serve                # Ollama hizmetini başlat
ollama list                 # Kurulu modelleri kontrol et
ollama pull qwen2.5:3b      # Eksik modeli kur
```

Yaygın nedenler: Ollama başlatılmamış, model kurulu değil, GPU belleği yetersiz

**GLM modu:**
- `GLM_API_KEY`'in doğru olduğunu doğrulayın
- `GLM_EMBEDDING_DIMENSIONS=768` olduğunu doğrulayın (Neo4j vektör indeksiyle tutarlı olmalı)
- GLM API uç noktası: `https://open.bigmodel.cn/api/paas/v4/`

**GROQ modu:**
- `GROQ_API_KEY`'in doğru olduğunu doğrulayın
- Rate Limit sık oluyorsa GLM moduna geçmeyi düşünün
- GROQ Embedding sunmaz, Ollama gömücüsünün kullanılabilir olduğundan emin olun

**OpenRouter modu:**
- `OPENROUTER_API_KEY`'in doğru, `OPENROUTER_MODEL`'in geçerli bir model ID'si olduğunu doğrulayın (bkz. https://openrouter.ai/models)
- Embedding sunmaz, Ollama gömücüsünün kullanılabilir olduğundan emin olun

**DeepSeek modu:**
- `DEEPSEEK_API_KEY`'in doğru olduğunu doğrulayın
- `Prompt must contain the word 'json'` hatası çıkarsa: bu, DeepSeek `json_object` modunun katı bir gereksinimidir; istemcide yerleşik güvence koruması bulunur; yine de çıkarsa en güncel `src/deepseek_client.py` sürümünü kullandığınızdan emin olun ve hizmeti yeniden başlatın
- Embedding sunmaz, Ollama gömücüsünün kullanılabilir olduğundan emin olun

### MCP bağlantı hatası

`Invalid request parameters` ya da `Received request before initialization was complete` hatası çıkarsa:

1. HTTP aktarım modunu kullandığınızı doğrulayın (**SSE kullanmayın**)
2. İstemci ayarının `"type": "http"`, `"url": "http://localhost:8000/mcp"` olduğunu doğrulayın
3. Hizmeti yeniden başlatın: `pm2 restart graphiti-mcp-http --update-env`
4. Claude Code'da `/mcp` çalıştırarak yeniden bağlanın

### Bellek ekleme hızı yavaş

- **Ollama**: Model boyutunu kontrol edin (`qwen2.5:3b`, `7b`'den 5-10 kat daha hızlıdır), GPU kullanıldığını doğrulayın (`ollama ps`)
- **GLM**: Her add_episode 10-20+ LLM ağ gidiş-dönüşü gerektirir, kısa metin için ~22s normal değerdir
- **GROQ**: Rate Limit çok sayıda yeniden denemeye yol açar, sık kullanılıyorsa GLM ya da Ollama'ya geçmeniz önerilir
- Bloke olmamak için `background=true` kullanın
- Uzun metnin daha erken bölütlenmesi için `GRAPHITI_CHUNK_THRESHOLD` değerini düşürün

### PM2 sorunları

```bash
pm2 status                                        # Durumu kontrol et
pm2 logs graphiti-mcp-http --err --lines 50        # Hata günlükleri
lsof -i :8000                                     # Port kullanımını kontrol et
pm2 delete graphiti-mcp-http && pm2 start ecosystem.config.cjs  # Tamamen yeniden başlat
```

## Geliştirme Tanılama Araçları

```bash
uv run python tools/status_report.py           # Birleşik durum raporu (Neo4j + Ollama + yapılandırma)
uv run python tools/validate_config.py         # .env ve yapılandırma bütünlüğünü doğrula
uv run python tools/performance_diagnose.py    # LLM performans tanılaması
uv run python tools/inspect_schema.py          # Neo4j indeks ve kısıtlama kontrolü
uv run python tools/migrate_embeddings.py      # Embedding model taşıması (model değiştirildikten sonra vektörleri yeniden oluştur)
```

### Embedding model taşıması

Embedding modelini değiştirdikten sonra (örn. `nomic-embed-text` → `bge-m3`), arama kalitesinin tutarlılığını sağlamak için taşıma aracını kullanarak tüm mevcut vektörleri yeniden oluşturabilirsiniz:

```bash
# Taşınması gereken miktarı önizle
uv run python tools/migrate_embeddings.py --dry-run

# Tam taşıma (kesme noktasından devam etmeyi destekler)
uv run python tools/migrate_embeddings.py

# Yalnızca belirtilen grubu taşı
uv run python tools/migrate_embeddings.py --group-id myproject

# Kesme noktasından devam et (kesintiden sonra yeniden çalıştır)
uv run python tools/migrate_embeddings.py --resume
```

> **Uyumluluk**: `bge-m3` yerel olarak 1024 boyutludur, sistem mevcut Neo4j vektör indeksiyle uyumlu olması için otomatik olarak 768 boyuta keser. Taşıma öncesi ve sonrası veriler bir arada bulunabilir, ancak en iyi arama kalitesi için tam taşıma yapmanız önerilir.

## Belgeler

- [Araç Kullanım Talimatları](../使用工具的指令.md) — MCP araç kullanım kılavuzu ve en iyi uygulamalar
- [Graphiti Memory Rules](../graphiti-memory-rules.md) — Bellek kuralları açıklaması

## Lisans

MIT License
