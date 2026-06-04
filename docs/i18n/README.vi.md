# Graphiti MCP Server

Dịch vụ bộ nhớ đồ thị tri thức — máy chủ MCP tích hợp nhiều nhà cung cấp LLM (Ollama / GLM / GROQ / OpenRouter / DeepSeek) với cơ sở dữ liệu đồ thị Neo4j.

Phát triển mở rộng dựa trên [getzep/graphiti](https://github.com/getzep/graphiti), hỗ trợ chuyển đổi linh hoạt giữa Ollama cục bộ và LLM trên đám mây, đồng thời có thể chỉ định nhà cung cấp Embedding một cách độc lập (tách rời khỏi LLM).

## Tính năng nổi bật

- **Quản lý bộ nhớ thông minh** — sử dụng đồ thị tri thức để lưu trữ và truy xuất các quan hệ bộ nhớ phức tạp
- **Tìm kiếm ngữ nghĩa** — tìm kiếm kết hợp dựa trên vector embedding (vector + từ khóa + duyệt đồ thị)
- **16 chiến lược tìm kiếm** — tìm kiếm nâng cao hỗ trợ nhiều phương thức tái xếp hạng như RRF, MMR, Cross-Encoder
- **Nhiều nhà cung cấp LLM** — hỗ trợ Ollama (cục bộ), GLM (Zhipu AI miễn phí), GROQ (suy luận tốc độ cao), OpenRouter (tổng hợp các mô hình), DeepSeek (Shenduqiusuo), chuyển đổi một chạm thông qua biến môi trường
- **Tách rời Embedding và LLM** — có thể dùng `EMBEDDING_PROVIDER` để chỉ định bộ embedding độc lập, LLM đám mây tự động dự phòng về `bge-m3` cục bộ
- **Phân luồng mô hình kép** — ở chế độ Ollama, tác vụ phức tạp dùng mô hình chính, tác vụ đơn giản tự động chuyển sang mô hình nhỏ để tăng hiệu suất
- **Phân đoạn nội dung thông minh** — văn bản dài tự động được phân đoạn xử lý, giảm tải cho LLM (ngưỡng có thể cấu hình)
- **Xử lý bộ nhớ nền** — việc thêm bộ nhớ có thể chạy ở chế độ nền, lời gọi MCP trả về ngay lập tức
- **Khử trùng lặp bộ nhớ** — tự động phát hiện các bộ nhớ hiện có có độ tương đồng cao, tránh lưu trữ trùng lặp
- **Phát hiện xung đột** — phát hiện các sự kiện mâu thuẫn giữa hai thực thể, nhận diện thông tin đã hết hiệu lực và còn hiệu lực
- **Phát hiện cộng đồng** — tự động phân cụm các thực thể liên quan dựa trên thuật toán Label Propagation
- **Theo dõi mức độ quan trọng** — tự động ghi lại tần suất truy cập thực thể, kết quả tìm kiếm được sắp xếp theo mức độ quan trọng
- **Lãng quên thông minh** — nhận diện và dọn dẹp các bộ nhớ đã lỗi thời, ít được truy cập, giữ cho đồ thị gọn gàng
- **Nhập hàng loạt** — gửi nhiều bộ nhớ cùng một lúc, thích hợp cho việc di chuyển dữ liệu khối lượng lớn
- **Bộ ba có cấu trúc** — thêm trực tiếp "chủ thể - quan hệ - khách thể", bỏ qua quá trình trích xuất của LLM, hoàn thành trong tích tắc
- **Giao diện quản lý Web** — tích hợp bảng điều khiển, duyệt, tìm kiếm, trực quan hóa đồ thị tri thức, hỏi đáp AI, duyệt cộng đồng
- **Đa ngôn ngữ (i18n)** — thông điệp phản hồi hỗ trợ hơn 30 locale (gồm zh-TW / en / zh-CN / ja / pt-BR / ko / es / de / fr v.v.); công cụ MCP theo `SERVER_LANG`, REST API tự động đàm phán theo HTTP `Accept-Language`
- **Chủ đề tối/sáng** — giao diện Web hỗ trợ chuyển đổi chủ đề
- **Chế độ an toàn** — có thể chọn thêm bộ nhớ nhanh bằng cách bỏ qua việc trích xuất thực thể
- **Hỗ trợ Docker** — tích hợp sẵn Dockerfile, hỗ trợ triển khai container hóa
- **An toàn đồng thời** — asyncio.Lock bảo vệ quá trình khởi tạo, ngăn chặn điều kiện tranh chấp
- **Kiểm tra sức khỏe phân tầng** — `/health` (liveness) + `/health/ready` (readiness)

## Yêu cầu hệ thống

| Hạng mục | Yêu cầu |
|------|------|
| Python | 3.10+ (khuyến nghị 3.11+) |
| Neo4j | 4.0+ (`bolt://localhost:7687`) |
| Nhà cung cấp LLM | Ollama / GLM / GROQ / OpenRouter / DeepSeek (chọn một trong năm) |
| Node.js | 18+ (chỉ dùng cho việc chạy nền PM2, tùy chọn) |
| Dung lượng đĩa | ~3GB (mô hình Ollama + dữ liệu Neo4j) |

### Lựa chọn nhà cung cấp LLM

Chuyển đổi thông qua biến môi trường `LLM_PROVIDER` (`ollama` / `glm` / `groq` / `openrouter` / `deepseek`):

| Nhà cung cấp | Đặc điểm | Mô hình LLM | Embedding | Tình huống phù hợp |
|--------|------|----------|-----------|----------|
| **Ollama** (mặc định) | Hoàn toàn cục bộ, dữ liệu không rời máy | `qwen2.5:3b` | `bge-m3` (tiếng Trung + RAG xuất sắc) | Có GPU, coi trọng quyền riêng tư |
| **GLM** | Đám mây miễn phí, ổn định không giới hạn lưu lượng | `glm-4-flash` (miễn phí) | `embedding-3` | Không có GPU, tình huống tìm kiếm dày đặc |
| **GROQ** | Suy luận siêu tốc | `llama-3.3-70b-versatile` | Dự phòng Ollama `bge-m3` | Thỉnh thoảng ghi, theo đuổi chất lượng |
| **OpenRouter** | Tổng hợp các mô hình, gồm hạn mức miễn phí | `stepfun/step-3.5-flash:free` v.v. | Dự phòng Ollama `bge-m3` | Muốn dùng mô hình đám mây cụ thể |
| **DeepSeek** | Đám mây Shenduqiusuo, hiệu quả về chi phí cao | `deepseek-v4-flash` / `deepseek-v4-pro` | Dự phòng Ollama `bge-m3` | Hiểu tiếng Trung, đám mây chi phí thấp |

> **Tách rời Embedding và LLM**: bộ embedding được chỉ định độc lập qua `EMBEDDING_PROVIDER` (`ollama` / `glm`), khi không đặt sẽ theo `LLM_PROVIDER`. Thực tế chỉ có `glm` dùng GLM `embedding-3`, phần còn lại (bao gồm GROQ / OpenRouter / DeepSeek và các LLM đám mây khác không cung cấp Embedding) đều tự động dùng Ollama `bge-m3`. **Vì vậy khi dùng bất kỳ LLM đám mây nào, vẫn cần Ollama cục bộ cung cấp dịch vụ embedding (trừ khi embedding cũng đặt thành glm).**

#### Chế độ Ollama (cục bộ)

```bash
# Mô hình LLM chính (khuyến nghị qwen2.5:3b, cân bằng tốt nhất giữa tốc độ và độ ổn định)
ollama pull qwen2.5:3b

# Mô hình embedding (bắt buộc, dùng cho tìm kiếm vector)
ollama pull bge-m3
```

> **Lưu ý khi lựa chọn mô hình**:
> - `qwen2.5:3b` — khuyến nghị, ~2s/call, ~100 t/s, đầu ra có cấu trúc của graphiti-core ổn định 100%
> - `qwen2.5:7b` — hiệu quả tốt hơn nhưng chậm 5-10 lần, thích hợp cho tình huống theo đuổi chất lượng
> - `qwen2.5:1.5b` — tốc độ nhanh nhất nhưng **không ổn định** (tỷ lệ thành công JSON có cấu trúc chỉ 33%), không khuyến nghị sử dụng

#### Chế độ GLM (đám mây Zhipu AI)

```bash
# Cấu hình .env
LLM_PROVIDER=glm
GLM_API_KEY=your_api_key          # Lấy từ https://open.bigmodel.cn
GLM_MODEL=glm-4-flash             # Mô hình miễn phí
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768      # Cần khớp với số chiều của chỉ mục vector Neo4j
```

> **Tham khảo hiệu suất GLM**: ghi ~22s (văn bản ngắn), tìm kiếm ~0.34s, không có lỗi Rate Limit, chậm hơn Ollama cục bộ 2-5 lần nhưng hoàn toàn miễn phí.

#### Chế độ GROQ (suy luận tốc độ cao)

```bash
# Cấu hình .env
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key         # Lấy từ https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile
```

> **Lưu ý**: GROQ không cung cấp dịch vụ Embedding, cần kết hợp với bộ embedding Ollama (tự động dự phòng) hoặc đặt `EMBEDDING_PROVIDER` thành glm. GROQ có Rate Limit nghiêm ngặt, sử dụng tần suất cao sẽ kích hoạt nhiều lần thử lại.

#### Chế độ OpenRouter (tổng hợp các mô hình)

```bash
# Cấu hình .env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_api_key       # Lấy từ https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free   # Có thể đổi thành bất kỳ mô hình OpenRouter nào
```

> **Lưu ý**: OpenRouter không cung cấp Embedding, tự động dự phòng Ollama `bge-m3`. Danh sách mô hình xem tại https://openrouter.ai/models (gồm nhiều mô hình miễn phí `:free`).

#### Chế độ DeepSeek (Shenduqiusuo)

```bash
# Cấu hình .env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key         # Lấy từ https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash      # Khuyến nghị; hoặc deepseek-v4-pro (hiệu quả tốt hơn)
```

> **Lưu ý**: DeepSeek không cung cấp Embedding, tự động dự phòng Ollama `bge-m3`. `deepseek-chat` / `deepseek-reasoner` sẽ ngừng hoạt động vào 2026-07-24, khuyến nghị chuyển sang dùng `deepseek-v4-flash` / `deepseek-v4-pro`. DeepSeek yêu cầu nghiêm ngặt prompt của chế độ `json_object` phải chứa chuỗi "json", client đã tích hợp sẵn cơ chế bảo vệ dự phòng, không cần cấu hình thêm.

## Khởi động nhanh

### 1. Chuẩn bị trước

Xác nhận Neo4j đã chạy trên máy cục bộ, và chuẩn bị dịch vụ tương ứng theo nhà cung cấp LLM đã chọn:

```bash
# Xác nhận Neo4j đang chạy (bắt buộc)
neo4j status
# Hoặc dùng Docker: docker run -d -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/your_password neo4j:latest

# Chế độ Ollama: xác nhận Ollama đang chạy
ollama list
# Nếu chưa khởi động: ollama serve

# Chế độ GLM / GROQ: chỉ cần API Key hợp lệ, không cần dịch vụ cục bộ
```

### 2. Cài đặt phụ thuộc

```bash
git clone <repo-url>
cd graphiti
uv sync
```

> **Lưu ý**: Dự án này sử dụng [uv](https://github.com/astral-sh/uv) để quản lý phụ thuộc. Nếu chưa cài đặt: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 3. Cấu hình môi trường

```bash
cp .env.example .env
```

Chỉnh sửa `.env`, **tối thiểu** cần sửa các mục sau:

```bash
NEO4J_PASSWORD=your_actual_password  # Bắt buộc: mật khẩu Neo4j
LLM_PROVIDER=ollama                  # ollama / glm / groq / openrouter / deepseek
OLLAMA_MODEL=qwen2.5:3b              # Chế độ Ollama: mô hình LLM cục bộ
# GLM_API_KEY=your_key               # Chế độ GLM: API Key của Zhipu AI
# GROQ_API_KEY=your_key              # Chế độ GROQ: API Key của GROQ
# OPENROUTER_API_KEY=your_key        # Chế độ OpenRouter: API Key
# DEEPSEEK_API_KEY=your_key          # Chế độ DeepSeek: API Key
```

### 4. Khởi động dịch vụ

```bash
# Chế độ HTTP (khuyến nghị, bao gồm giao diện quản lý Web)
uv run python graphiti_mcp_server.py --transport http --port 8000

# Hoặc dùng PM2 chạy nền (khuyến nghị cho việc vận hành lâu dài)
pm2 start ecosystem.config.cjs
```

### 5. Xác minh dịch vụ

Sau khi khởi động có thể truy cập các điểm cuối sau:

| Điểm cuối | Mô tả |
|------|------|
| http://localhost:8000/ | Giao diện quản lý Web |
| http://localhost:8000/mcp | Điểm cuối MCP (cho client MCP kết nối) |
| http://localhost:8000/health | Kiểm tra sức khỏe (liveness) |
| http://localhost:8000/health/ready | Kiểm tra sâu (gồm kết nối Neo4j) |
| http://localhost:8000/api/stats | Thống kê REST API |

## Cấu trúc dự án

```
graphiti/
├── graphiti_mcp_server.py        # Điểm vào chính — định nghĩa công cụ MCP (19 công cụ)
├── src/
│   ├── config.py                 # Quản lý cấu hình (GraphitiConfig, hỗ trợ chồng lớp JSON/.env)
│   ├── web_api.py                # REST API giao diện quản lý Web (20+ điểm cuối)
│   ├── ollama_graphiti_client.py  # Client LLM Ollama (phân luồng mô hình kép)
│   ├── glm_client.py             # Client LLM GLM (Zhipu AI) (API tương thích OpenAI)
│   ├── openrouter_client.py      # Client LLM OpenRouter (tổng hợp các mô hình)
│   ├── deepseek_client.py        # Client LLM DeepSeek (json_object + bảo vệ json dự phòng)
│   ├── ollama_embedder.py        # Bộ điều hợp mô hình embedding Ollama
│   ├── content_preprocessor.py   # Phân đoạn nội dung thông minh (văn bản dài tự động phân đoạn)
│   ├── deduplication.py          # Khử trùng lặp bộ nhớ (so sánh độ tương đồng cosine)
│   ├── importance.py             # Theo dõi mức độ quan trọng và lãng quên thông minh
│   ├── safe_memory_add.py        # Thêm bộ nhớ an toàn (bỏ qua trích xuất thực thể)
│   ├── timezone_utils.py         # Chuyển đổi múi giờ (UTC→hiển thị múi giờ cục bộ)
│   ├── i18n.py                   # Đa ngôn ngữ phía backend (REST theo Accept-Language, MCP theo SERVER_LANG)
│   ├── exceptions.py             # Xử lý ngoại lệ có cấu trúc (12 loại ngoại lệ)
│   └── logging_setup.py          # Hệ thống nhật ký (xoay vòng theo thời gian + giám sát hiệu suất)
├── web/                          # Frontend giao diện quản lý Web (SPA, không build)
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js                # Đóng gói REST API
│       ├── components.js         # Kết xuất thành phần UI (gồm trang cộng đồng)
│       └── app.js                # Định tuyến SPA, quản lý trạng thái
├── tests/                        # Bộ kiểm thử (183 bài kiểm thử)
│   ├── test_content_preprocessor.py  # Kiểm thử logic phân đoạn (17 bài)
│   ├── test_new_features.py      # Kiểm thử tính năng mới (32 bài)
│   ├── test_i18n.py             # Kiểm thử đa ngôn ngữ (37 bài)
│   ├── test_unit.py              # Kiểm thử đơn vị
│   ├── test_web_api.py           # Kiểm thử Web API
│   ├── test_web_ui_features.py   # Kiểm thử tính năng Web UI
│   ├── test_integration_manual.py # Kiểm thử tích hợp thủ công
│   └── bench_deepseek_flash_vs_pro.py # Script chuẩn hiệu suất DeepSeek flash/pro
├── tools/                        # Công cụ chẩn đoán phát triển
│   ├── status_report.py          # Báo cáo trạng thái tổng hợp
│   ├── validate_config.py        # Xác thực cấu hình
│   ├── performance_diagnose.py   # Chẩn đoán hiệu suất
│   ├── inspect_schema.py         # Kiểm tra cấu trúc Neo4j
│   └── batch_reprocess.py        # Xử lý lại hàng loạt
├── docs/                         # Tài liệu
├── logs/                         # Nhật ký (xoay vòng theo thời gian, mặc định giữ 30 ngày)
├── Dockerfile                    # Triển khai container hóa Docker
└── ecosystem.config.cjs          # Cấu hình PM2
```

## Cấu hình client MCP

### Chế độ HTTP (khuyến nghị)

Áp dụng cho Claude Code, Cline và các client MCP hỗ trợ HTTP:

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

### Chế độ STDIO

Áp dụng cho Claude Desktop và các client cần khởi động tiến trình trực tiếp:

**Vị trí tệp cấu hình:**
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

> **Lưu ý**: Chế độ SSE (`--transport sse`) không còn được khuyến nghị sử dụng. MCP 1.x có vấn đề tương thích khi khởi tạo session, vui lòng chuyển sang dùng chế độ HTTP.

## Công cụ MCP (19 công cụ)

### Quản lý bộ nhớ (7 công cụ)

| Công cụ | Mô tả |
|------|------|
| `add_memory_simple` | Thêm bộ nhớ vào đồ thị tri thức (hỗ trợ xử lý nền, phân đoạn thông minh, kiểm tra khử trùng lặp) |
| `add_episode_bulk` | Thêm hàng loạt nhiều bộ nhớ (mặc định xử lý nền) |
| `add_triplet` | Thêm bộ ba có cấu trúc (bỏ qua LLM, hoàn thành trong tích tắc) |
| `search_memory_nodes` | Tìm kiếm nút bộ nhớ (hỗ trợ 16 chiến lược tìm kiếm, lọc theo thời gian) |
| `search_memory_facts` | Tìm kiếm sự kiện bộ nhớ (hỗ trợ lọc theo loại quan hệ, khoảng thời gian, hiệu lực) |
| `advanced_search` | Tìm kiếm nâng cao (16 chiến lược, trả về nút+cạnh+cộng đồng+phân đoạn) |
| `get_episodes` | Lấy các phân đoạn bộ nhớ gần đây |

### Phân tích tri thức (3 công cụ)

| Công cụ | Mô tả |
|------|------|
| `check_conflicts` | Phát hiện xung đột sự kiện giữa hai thực thể (còn hiệu lực vs đã hết hiệu lực) |
| `get_node_edges` | Khám phá quan hệ cạnh vào và cạnh ra của nút |
| `build_communities` | Kích hoạt phát hiện và phân cụm cộng đồng (mặc định xử lý nền) |

### Bảo trì bộ nhớ (2 công cụ)

| Công cụ | Mô tả |
|------|------|
| `get_stale_memories` | Truy vấn các bộ nhớ lỗi thời, ít được truy cập |
| `cleanup_stale_memories` | Dọn dẹp bộ nhớ lỗi thời (mặc định chế độ xem trước dry_run) |

### Quản lý tác vụ

| Công cụ | Mô tả |
|------|------|
| `get_memory_task_status` | Truy vấn tiến độ và kết quả của tác vụ xử lý bộ nhớ nền |

### Xóa và truy vấn

| Công cụ | Mô tả |
|------|------|
| `delete_episode` | Xóa phân đoạn bộ nhớ |
| `delete_entity_edge` | Xóa cạnh thực thể (quan hệ) |
| `get_entity_edge` | Lấy thông tin chi tiết cạnh thực thể |

### Quản lý hệ thống

| Công cụ | Mô tả |
|------|------|
| `get_status` | Lấy trạng thái dịch vụ (Neo4j, LLM, bộ embedding) |
| `test_connection` | Kiểm tra kết nối Neo4j / LLM / bộ embedding |
| `clear_graph` | Xóa cơ sở dữ liệu đồ thị (hỗ trợ xóa theo group_id) |

## Tham số công cụ

### add_memory_simple

| Tham số | Kiểu | Bắt buộc | Mặc định | Mô tả |
|------|------|------|--------|------|
| `name` | string | Y | | Tên bộ nhớ |
| `episode_body` | string | Y | | Nội dung bộ nhớ (vượt quá 800 ký tự sẽ tự động phân đoạn) |
| `group_id` | string | | `"default"` | ID nhóm (khuyến nghị cô lập theo dự án) |
| `source` | string | | `"text"` | Loại nguồn: `text` / `json` / `message` |
| `source_description` | string | | `"MCP Server"` | Mô tả nguồn |
| `use_safe_mode` | bool | | `false` | Chế độ an toàn (bỏ qua trích xuất thực thể, nhanh nhưng bộ nhớ không thể tìm kiếm được) |
| `background` | bool | | `false` | Xử lý nền (trả về task_id ngay, thích hợp cho văn bản dài) |
| `force` | bool | | `false` | Bỏ qua kiểm tra khử trùng lặp (cưỡng chế thêm) |
| `excluded_entity_types` | list | | | Loại thực thể bị loại trừ (giảm lượng trích xuất không cần thiết) |

> **Gợi ý hiệu suất**:
> - Văn bản ngắn (<800 ký tự): xử lý trực tiếp, thường hoàn thành trong 30-40 giây
> - Văn bản dài (>800 ký tự): tự động phân đoạn thành nhiều phần, dùng `add_episode_bulk` xử lý đồng thời (nhanh hơn xử lý tuần tự ~33%)
> - Dùng `background=true` để tránh chặn lời gọi MCP, theo dõi tiến độ qua `get_memory_task_status`
> - `use_safe_mode=true` hoàn thành trong tích tắc nhưng bộ nhớ không thể được công cụ search tìm thấy
> - Khi bật khử trùng lặp, các bộ nhớ có độ tương đồng cao sẽ bị cảnh báo (`force=true` có thể bỏ qua)

### add_episode_bulk

| Tham số | Kiểu | Bắt buộc | Mặc định | Mô tả |
|------|------|------|--------|------|
| `episodes` | list | Y | | Danh sách bộ nhớ, mỗi mục chứa `name` và `content` |
| `group_id` | string | | `"default"` | ID nhóm |
| `source` | string | | `"text"` | Loại nguồn |
| `background` | bool | | `true` | Xử lý nền (xử lý hàng loạt thường tốn thời gian) |

### add_triplet

| Tham số | Kiểu | Bắt buộc | Mặc định | Mô tả |
|------|------|------|--------|------|
| `source_name` | string | Y | | Tên thực thể nguồn (như "Alice") |
| `target_name` | string | Y | | Tên thực thể đích (như "Google") |
| `relation_name` | string | Y | | Tên quan hệ (như "works_at") |
| `fact` | string | Y | | Mô tả sự kiện (như "Alice works at Google") |
| `group_id` | string | | `"default"` | ID nhóm |
| `source_labels` | list | | | Nhãn thực thể nguồn |
| `target_labels` | list | | | Nhãn thực thể đích |

### search_memory_nodes

| Tham số | Kiểu | Bắt buộc | Mặc định | Mô tả |
|------|------|------|--------|------|
| `query` | string | Y | | Từ khóa tìm kiếm (ngôn ngữ tự nhiên) |
| `max_nodes` | int | | `10` | Số lượng trả về tối đa |
| `group_ids` | list | | | Lọc theo nhóm (tìm kiếm liên kết nhiều group) |
| `entity_types` | list | | | Lọc theo loại thực thể |
| `search_recipe` | string | | | Chiến lược tìm kiếm (xem tìm kiếm nâng cao) |
| `created_after` | string | | | Giới hạn dưới thời gian tạo (ISO datetime) |
| `created_before` | string | | | Giới hạn trên thời gian tạo (ISO datetime) |

### search_memory_facts

| Tham số | Kiểu | Bắt buộc | Mặc định | Mô tả |
|------|------|------|--------|------|
| `query` | string | Y | | Từ khóa tìm kiếm |
| `max_facts` | int | | `10` | Số lượng trả về tối đa |
| `group_ids` | list | | | Lọc theo nhóm |
| `center_node_uuid` | string | | | UUID nút trung tâm (khám phá quan hệ của nút cụ thể) |
| `edge_types` | list | | | Lọc theo loại quan hệ (như `["works_at"]`) |
| `created_after` | string | | | Giới hạn dưới thời gian tạo (ISO datetime) |
| `created_before` | string | | | Giới hạn trên thời gian tạo (ISO datetime) |
| `only_valid` | bool | | `false` | Chỉ trả về các sự kiện chưa hết hiệu lực |

### advanced_search

| Tham số | Kiểu | Bắt buộc | Mặc định | Mô tả |
|------|------|------|--------|------|
| `query` | string | Y | | Từ khóa tìm kiếm |
| `search_recipe` | string | | `"combined_rrf"` | Chiến lược tìm kiếm (16 lựa chọn) |
| `max_results` | int | | `10` | Số lượng trả về tối đa |
| `group_ids` | list | | | Lọc theo nhóm |
| `center_node_uuid` | string | | | UUID nút trung tâm |

**Các chiến lược tìm kiếm khả dụng (search_recipe):**

| Loại | Chiến lược | Mô tả |
|------|------|------|
| Tổng hợp | `combined_rrf` | Hợp nhất RRF tổng hợp (mặc định, khuyến nghị) |
| Tổng hợp | `combined_mmr` | Tái xếp hạng đa dạng MMR tổng hợp |
| Tổng hợp | `combined_cross_encoder` | Xếp hạng tinh Cross-Encoder tổng hợp |
| Cạnh | `edge_rrf` / `edge_mmr` / `edge_cross_encoder` | Tìm kiếm cạnh (3 cách sắp xếp) |
| Cạnh | `edge_node_distance` / `edge_episode_mentions` | Tìm kiếm cạnh (khoảng cách đồ thị/số lần trích dẫn) |
| Nút | `node_rrf` / `node_mmr` / `node_cross_encoder` | Tìm kiếm nút (3 cách sắp xếp) |
| Nút | `node_node_distance` / `node_episode_mentions` | Tìm kiếm nút (khoảng cách đồ thị/số lần trích dẫn) |
| Cộng đồng | `community_rrf` / `community_mmr` / `community_cross_encoder` | Tìm kiếm cộng đồng |

### check_conflicts

| Tham số | Kiểu | Bắt buộc | Mặc định | Mô tả |
|------|------|------|--------|------|
| `source_name` | string | Y | | Tên thực thể nguồn |
| `target_name` | string | Y | | Tên thực thể đích |
| `group_id` | string | | `"default"` | ID nhóm |

### get_node_edges

| Tham số | Kiểu | Bắt buộc | Mặc định | Mô tả |
|------|------|------|--------|------|
| `node_uuid` | string | Y | | UUID nút |
| `include_inbound` | bool | | `true` | Bao gồm cạnh vào |
| `include_outbound` | bool | | `true` | Bao gồm cạnh ra |
| `max_edges` | int | | `50` | Số lượng trả về tối đa |

### build_communities

| Tham số | Kiểu | Bắt buộc | Mặc định | Mô tả |
|------|------|------|--------|------|
| `group_ids` | list | | | Chỉ định nhóm (để trống thì áp dụng tất cả) |
| `background` | bool | | `true` | Xử lý nền |

### get_stale_memories

| Tham số | Kiểu | Bắt buộc | Mặc định | Mô tả |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Vượt quá bao nhiêu ngày không truy cập thì coi là lỗi thời |
| `min_access_count` | int | | `2` | Số lần truy cập thấp hơn giá trị này mới được liệt kê |
| `group_id` | string | | | Lọc theo nhóm |
| `limit` | int | | `50` | Số lượng trả về tối đa |

### cleanup_stale_memories

| Tham số | Kiểu | Bắt buộc | Mặc định | Mô tả |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Ngưỡng số ngày lỗi thời |
| `min_access_count` | int | | `2` | Ngưỡng số lần truy cập tối thiểu |
| `group_id` | string | | | Lọc theo nhóm |
| `dry_run` | bool | | `true` | Chế độ xem trước (không thực sự xóa) |
| `limit` | int | | `50` | Số lượng xử lý tối đa |

### get_memory_task_status

| Tham số | Kiểu | Bắt buộc | Mô tả |
|------|------|------|------|
| `task_id` | string | Y | ID tác vụ nền (do `add_memory_simple(background=true)` trả về) |

## Giao diện quản lý Web

Ở chế độ HTTP truy cập `http://localhost:8000/` là có thể sử dụng.

**Tính năng:**
- Bảng điều khiển — thống kê số nút, số sự kiện, số phân đoạn bộ nhớ
- Nút thực thể — duyệt, lọc, tìm kiếm vector
- Quan hệ sự kiện — duyệt, lọc, tìm kiếm vector
- Phân đoạn bộ nhớ — duyệt, tìm kiếm toàn văn, xóa
- Duyệt cộng đồng — danh sách nút cộng đồng, tóm tắt, kích hoạt xây dựng cộng đồng
- Biểu mẫu bộ ba — thêm trực tiếp tri thức có cấu trúc "chủ thể - quan hệ - khách thể"
- Quản lý Group — lọc theo nhóm, xóa hàng loạt
- Trực quan hóa đồ thị tri thức — trình bày đồ họa quan hệ nút
- Hỏi đáp AI — hỏi đáp thông minh dựa trên đồ thị tri thức
- Phân tích chất lượng — phân tích chất lượng và độ bao phủ bộ nhớ
- Chuyển đổi chủ đề — chủ đề tối/sáng

**REST API:**

| Điểm cuối | Phương thức | Mô tả |
|------|------|------|
| `/api/stats` | GET | Thống kê bảng điều khiển |
| `/api/groups` | GET | Lấy tất cả group_id |
| `/api/nodes` | GET | Duyệt nút thực thể (phân trang) |
| `/api/facts` | GET | Duyệt sự kiện (phân trang) |
| `/api/episodes` | GET | Duyệt phân đoạn bộ nhớ (phân trang) |
| `/api/search/nodes` | GET | Tìm kiếm vector nút |
| `/api/search/facts` | GET | Tìm kiếm vector sự kiện |
| `/api/search/advanced` | GET | Tìm kiếm nâng cao (16 chiến lược) |
| `/api/communities` | GET | Duyệt nút cộng đồng (phân trang) |
| `/api/communities/build` | POST | Kích hoạt xây dựng cộng đồng |
| `/api/memory/add-bulk` | POST | Thêm bộ nhớ hàng loạt |
| `/api/memory/add-triplet` | POST | Thêm bộ ba |
| `/api/memory/tasks` | GET | Liệt kê tác vụ nền (hỗ trợ lọc theo trạng thái) |
| `/api/memory/tasks/{id}` | GET | Truy vấn trạng thái tác vụ đơn lẻ |
| `/api/analytics/stale` | GET | Truy vấn bộ nhớ lỗi thời |
| `/api/analytics/cleanup` | POST | Dọn dẹp bộ nhớ lỗi thời |
| `/api/nodes/{uuid}` | DELETE | Xóa nút |
| `/api/episodes/{uuid}` | DELETE | Xóa phân đoạn bộ nhớ |
| `/api/facts/{uuid}` | DELETE | Xóa sự kiện |
| `/api/groups/{group_id}` | DELETE | Xóa toàn bộ group |

## Cấu hình

### Biến môi trường (.env)

Cấu hình sử dụng cơ chế chồng lớp: tệp cấu hình JSON làm nền tảng, biến môi trường ghi đè các giá trị riêng lẻ.

```bash
# === Bắt buộc ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password        # Bắt buộc phải sửa

# === Lựa chọn nhà cung cấp LLM ===
LLM_PROVIDER=ollama                 # ollama / glm / groq / openrouter / deepseek

# === Nhà cung cấp Embedding (tùy chọn, mặc định theo LLM_PROVIDER) ===
# Chỉ glm dùng GLM Embedding, phần còn lại đều dùng Ollama bge-m3
# EMBEDDING_PROVIDER=ollama         # ollama / glm

# === Cấu hình Ollama (dùng khi LLM_PROVIDER=ollama) ===
OLLAMA_MODEL=qwen2.5:3b             # Mô hình chính (khuyến nghị qwen2.5:3b)
OLLAMA_SMALL_MODEL=qwen2.5:3b       # Mô hình nhỏ (cho tác vụ đơn giản, có thể chọn mô hình khác)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.1

# === Cấu hình GLM (dùng khi LLM_PROVIDER=glm) ===
GLM_API_KEY=your_api_key            # Lấy từ https://open.bigmodel.cn
GLM_MODEL=glm-4-flash               # Mô hình miễn phí
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768

# === Cấu hình GROQ (dùng khi LLM_PROVIDER=groq) ===
GROQ_API_KEY=your_api_key           # Lấy từ https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile

# === Cấu hình OpenRouter (dùng khi LLM_PROVIDER=openrouter) ===
OPENROUTER_API_KEY=your_api_key     # Lấy từ https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free

# === Cấu hình DeepSeek (dùng khi LLM_PROVIDER=deepseek) ===
DEEPSEEK_API_KEY=your_api_key       # Lấy từ https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash    # Hoặc deepseek-v4-pro

# === Mô hình embedding Ollama (dùng khi embedding không phải glm) ===
OLLAMA_EMBEDDING_MODEL=bge-m3
OLLAMA_EMBEDDING_DIMENSIONS=768

# === Hiển thị và ngôn ngữ (tùy chọn) ===
GRAPHITI_DISPLAY_TIMEZONE=Asia/Taipei # Múi giờ hiển thị dấu thời gian API trả về (tên IANA; lưu trữ vẫn giữ UTC)
SERVER_LANG=zh-TW                     # Ngôn ngữ phản hồi công cụ MCP (xem locale đầy đủ trong src/i18n.py); REST API đổi sang theo Accept-Language

# === Hiệu suất bộ nhớ (tùy chọn) ===
GRAPHITI_CHUNK_THRESHOLD=800         # Ngưỡng số ký tự kích hoạt phân đoạn thông minh
GRAPHITI_MAX_CHUNK_SIZE=600          # Số ký tự tối đa mỗi đoạn
GRAPHITI_MAX_COROUTINES=10            # Số coroutine đồng thời tối đa
GRAPHITI_DEFAULT_BACKGROUND=false    # Có mặc định xử lý nền hay không

# === Theo dõi mức độ quan trọng và lãng quên thông minh (tùy chọn) ===
ENABLE_IMPORTANCE_TRACKING=true      # Bật theo dõi truy cập
IMPORTANCE_WEIGHT=0.1                # Trọng số mức độ quan trọng
STALE_DAYS_THRESHOLD=30              # Ngưỡng số ngày lỗi thời
STALE_MIN_ACCESS_COUNT=2             # Số lần truy cập tối thiểu

# === Nhật ký ===
LOG_FILE=logs/graphiti_mcp_server.log
LOG_LEVEL=INFO
```

> **Danh sách biến môi trường đầy đủ** vui lòng xem `.env.example`

### Tệp cấu hình JSON

Áp dụng cho cấu hình cần kiểm soát phiên bản (biến môi trường vẫn có thể ghi đè):

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

## Chạy nền PM2

```bash
npm install -g pm2

pm2 start ecosystem.config.cjs      # Khởi động
pm2 status                           # Trạng thái
pm2 logs graphiti-mcp-http           # Nhật ký thời gian thực
pm2 restart graphiti-mcp-http --update-env  # Khởi động lại (nạp lại .env)

pm2 save && pm2 startup              # Thiết lập tự động khởi động khi bật máy
```

> **Gợi ý**: Sau khi sửa `.env` bắt buộc phải dùng cờ `--update-env` để khởi động lại, nếu không biến môi trường sẽ không được cập nhật.

## Triển khai Docker

```bash
docker build -t graphiti-mcp .

# Lưu ý: container Docker cần có thể kết nối tới Neo4j và Ollama
# Dùng host network là đơn giản nhất
docker run -p 8000:8000 --env-file .env --network host graphiti-mcp

# Hoặc chỉ định rõ địa chỉ dịch vụ bên ngoài
docker run -p 8000:8000 \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --env-file .env graphiti-mcp
```

## Kiểm thử

```bash
# Chạy tất cả bài kiểm thử (183 bài, khoảng 1 giây)
uv run python -m pytest tests/

# Đầu ra chi tiết
uv run python -m pytest tests/ -v

# Chỉ chạy bài kiểm thử cụ thể
uv run python -m pytest tests/test_content_preprocessor.py -v
uv run python -m pytest tests/test_new_features.py -v
uv run python -m pytest tests/test_unit.py -v
```

> **Lưu ý**: 3 bài kiểm thử async trong `test_integration_manual.py` cần cài đặt `pytest-asyncio`, khi thiếu sẽ hiển thị Failed nhưng không ảnh hưởng tới các bài kiểm thử khác. `bench_deepseek_flash_vs_pro.py` là script chuẩn hiệu suất, không phải kiểm thử đơn vị.

## Khắc phục sự cố

### Kết nối Neo4j thất bại

```bash
neo4j status                              # Kiểm tra trạng thái dịch vụ
cypher-shell -u neo4j -p your_password    # Xác nhận mật khẩu đúng
curl http://localhost:7474                 # Xác nhận cổng HTTP
```

Nguyên nhân thường gặp:
- Neo4j chưa khởi động
- Mật khẩu sai (`NEO4J_PASSWORD` trong `.env`)
- Cổng bị chiếm dụng hoặc tường lửa chặn

### Kết nối LLM thất bại

**Chế độ Ollama:**
```bash
ollama serve                # Khởi động dịch vụ Ollama
ollama list                 # Kiểm tra mô hình đã cài đặt
ollama pull qwen2.5:3b      # Cài đặt mô hình còn thiếu
```

Nguyên nhân thường gặp: Ollama chưa khởi động, mô hình chưa cài đặt, bộ nhớ GPU không đủ

**Chế độ GLM:**
- Xác nhận `GLM_API_KEY` đúng
- Xác nhận `GLM_EMBEDDING_DIMENSIONS=768` (cần khớp với chỉ mục vector Neo4j)
- Điểm cuối API GLM: `https://open.bigmodel.cn/api/paas/v4/`

**Chế độ GROQ:**
- Xác nhận `GROQ_API_KEY` đúng
- Khi Rate Limit xảy ra thường xuyên, cân nhắc chuyển sang chế độ GLM
- GROQ không cung cấp Embedding, cần đảm bảo bộ embedding Ollama khả dụng

**Chế độ OpenRouter:**
- Xác nhận `OPENROUTER_API_KEY` đúng, `OPENROUTER_MODEL` là ID mô hình hợp lệ (xem https://openrouter.ai/models)
- Không cung cấp Embedding, cần đảm bảo bộ embedding Ollama khả dụng

**Chế độ DeepSeek:**
- Xác nhận `DEEPSEEK_API_KEY` đúng
- Nếu xuất hiện `Prompt must contain the word 'json'`: đây là yêu cầu cứng của chế độ `json_object` DeepSeek, client đã tích hợp sẵn cơ chế bảo vệ dự phòng; nếu vẫn xuất hiện, xác nhận đang dùng `src/deepseek_client.py` phiên bản mới nhất và khởi động lại dịch vụ
- Không cung cấp Embedding, cần đảm bảo bộ embedding Ollama khả dụng

### Lỗi kết nối MCP

Nếu xuất hiện `Invalid request parameters` hoặc `Received request before initialization was complete`:

1. Xác nhận đang dùng chế độ truyền HTTP (**đừng dùng SSE**)
2. Xác nhận client được cấu hình là `"type": "http"`, `"url": "http://localhost:8000/mcp"`
3. Khởi động lại dịch vụ: `pm2 restart graphiti-mcp-http --update-env`
4. Thực thi `/mcp` trong Claude Code để kết nối lại

### Thêm bộ nhớ chậm

- **Ollama**: kiểm tra kích thước mô hình (`qwen2.5:3b` nhanh hơn `7b` 5-10 lần), xác nhận đang dùng GPU (`ollama ps`)
- **GLM**: mỗi add_episode cần 10-20+ vòng đi-về mạng LLM, văn bản ngắn ~22s là giá trị bình thường
- **GROQ**: Rate Limit sẽ dẫn đến nhiều lần thử lại, nếu sử dụng thường xuyên khuyến nghị chuyển sang GLM hoặc Ollama
- Dùng `background=true` để tránh chặn
- Giảm `GRAPHITI_CHUNK_THRESHOLD` để văn bản dài được phân đoạn sớm hơn

### Vấn đề PM2

```bash
pm2 status                                        # Kiểm tra trạng thái
pm2 logs graphiti-mcp-http --err --lines 50        # Nhật ký lỗi
lsof -i :8000                                     # Kiểm tra cổng bị chiếm dụng
pm2 delete graphiti-mcp-http && pm2 start ecosystem.config.cjs  # Khởi động lại hoàn toàn
```

## Công cụ chẩn đoán phát triển

```bash
uv run python tools/status_report.py           # Báo cáo trạng thái tổng hợp (Neo4j + Ollama + cấu hình)
uv run python tools/validate_config.py         # Xác minh tính đầy đủ của .env và cấu hình
uv run python tools/performance_diagnose.py    # Chẩn đoán hiệu suất LLM
uv run python tools/inspect_schema.py          # Kiểm tra chỉ mục và ràng buộc Neo4j
uv run python tools/migrate_embeddings.py      # Di chuyển mô hình Embedding (tạo lại vector sau khi đổi mô hình)
```

### Di chuyển mô hình Embedding

Sau khi chuyển đổi mô hình embedding (như `nomic-embed-text` → `bge-m3`), có thể dùng công cụ di chuyển để tạo lại tất cả vector hiện có, đảm bảo chất lượng tìm kiếm đồng nhất:

```bash
# Xem trước số lượng cần di chuyển
uv run python tools/migrate_embeddings.py --dry-run

# Di chuyển toàn bộ (hỗ trợ chạy tiếp từ điểm gián đoạn)
uv run python tools/migrate_embeddings.py

# Chỉ di chuyển group được chỉ định
uv run python tools/migrate_embeddings.py --group-id myproject

# Tiếp tục từ điểm gián đoạn (chạy lại sau khi bị ngắt)
uv run python tools/migrate_embeddings.py --resume
```

> **Tính tương thích**: `bge-m3` nguyên gốc 1024 chiều, hệ thống tự động cắt còn 768 chiều để tương thích với chỉ mục vector Neo4j hiện có. Dữ liệu trước và sau khi di chuyển có thể cùng tồn tại, nhưng khuyến nghị thực hiện di chuyển hoàn chỉnh để có chất lượng tìm kiếm tốt nhất.

## Tài liệu

- [Chỉ dẫn sử dụng công cụ](../使用工具的指令.md) — Hướng dẫn sử dụng công cụ MCP và thực hành tốt nhất
- [Graphiti Memory Rules](../graphiti-memory-rules.md) — Thuyết minh quy tắc bộ nhớ

## Giấy phép

MIT License
