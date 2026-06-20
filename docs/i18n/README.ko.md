# Graphiti MCP Server

지식 그래프 메모리 서비스 — 여러 LLM 제공자(Ollama / GLM / GROQ / OpenRouter / DeepSeek)와 Neo4j 그래프 데이터베이스를 통합한 MCP 서버.

[getzep/graphiti](https://github.com/getzep/graphiti)를 기반으로 확장 개발되었으며, 로컬 Ollama와 클라우드 LLM 간 유연한 전환을 지원하고 Embedding 제공자를 독립적으로 지정할 수 있습니다(LLM과 분리).

## 주요 기능

- **지능형 메모리 관리** — 지식 그래프를 사용하여 복잡한 메모리 관계를 저장하고 검색
- **의미 검색** — 벡터 임베딩 기반의 하이브리드 검색(벡터 + 키워드 + 그래프 순회)
- **16가지 검색 전략** — 고급 검색은 RRF, MMR, Cross-Encoder 등 다양한 재정렬 방식을 지원
- **다중 LLM 제공자** — Ollama(로컬), GLM(智谱 AI 무료), GROQ(고속 추론), OpenRouter(여러 업체 모델 통합), DeepSeek(深度求索)를 지원하며 환경 변수로 한 번에 전환 가능
- **Embedding과 LLM 분리** — `EMBEDDING_PROVIDER`로 임베딩 제공자를 독립적으로 지정할 수 있으며, 클라우드 LLM은 자동으로 로컬 `bge-m3`로 폴백
- **이중 모델 분기** — Ollama 모드에서 복잡한 작업은 주 모델을 사용하고, 간단한 작업은 자동으로 소형 모델로 전환하여 성능 향상
- **지능형 콘텐츠 분할** — 긴 텍스트를 자동으로 분할 처리하여 LLM 부하를 낮춤(임계값 설정 가능)
- **백그라운드 메모리 처리** — 메모리 추가를 백그라운드에서 실행할 수 있으며, MCP 호출은 즉시 반환; 작업 상태는 SQLite에 영속화되어 재시작 후 미완료 작업이 자동으로 복원됨
- **메모리 중복 제거** — 매우 유사한 기존 메모리를 자동으로 감지하여 중복 저장을 방지
- **충돌 감지** — 두 엔티티 간의 모순되는 사실을 감지하고, 이미 무효화된 정보와 유효한 정보를 식별
- **커뮤니티 감지** — Label Propagation 알고리즘을 기반으로 관련 엔티티를 자동으로 클러스터링
- **중요도 추적** — 엔티티 접근 빈도를 자동으로 기록하고, 검색 결과를 중요도에 따라 정렬
- **지능형 망각** — 오래되고 접근량이 낮은 메모리를 식별하고 정리하여 그래프를 간결하게 유지
- **대량 가져오기** — 한 번에 여러 메모리를 제출하여 대량 데이터 마이그레이션에 적합
- **구조화된 트리플** — "주체-관계-객체"를 직접 추가하여 LLM 추출을 건너뛰고 즉시 완료
- **Web 관리 인터페이스** — 대시보드, 탐색, 검색, 지식 그래프 시각화, AI 질의응답, 커뮤니티 탐색, 품질 유지 관리, 일괄 가져오기, 런타임 설정 내장
- **다국어(i18n)** — 응답 메시지가 33가지 언어를 지원(zh-TW / en / zh-CN / ja / pt-BR / ko / es / de / fr 등 포함; zh-TW/en/zh-CN/ja는 수동 작성, 나머지는 generated 레이어에서 제공); MCP 도구는 `SERVER_LANG`에 따르고, REST API는 HTTP `Accept-Language`에 따라 자동 협상
- **다크/라이트 테마** — Web 인터페이스에서 테마 전환 지원
- **안전 모드** — 엔티티 추출을 건너뛰는 빠른 메모리 추가를 선택 가능
- **Docker 지원** — Dockerfile 내장, 컨테이너화 배포 지원
- **동시성 안전** — asyncio.Lock으로 초기화를 보호하여 경쟁 조건 방지
- **계층화된 헬스 체크** — `/health`(liveness) + `/health/ready`(readiness)

## 시스템 요구 사항

| 항목 | 요구 사항 |
|------|------|
| Python | 3.10+(3.11+ 권장) |
| Neo4j | 4.0+(`bolt://localhost:7687`) |
| LLM 제공자 | Ollama / GLM / GROQ / OpenRouter / DeepSeek(다섯 중 하나 선택) |
| Node.js | 18+(PM2 백그라운드 실행에만 사용, 선택) |
| 디스크 공간 | ~3GB(Ollama 모델 + Neo4j 데이터) |

### LLM 제공자 선택

`LLM_PROVIDER` 환경 변수로 전환(`ollama` / `glm` / `groq` / `openrouter` / `deepseek`):

| 제공자 | 특징 | LLM 모델 | Embedding | 적합한 시나리오 |
|--------|------|----------|-----------|----------|
| **Ollama**(기본값) | 완전 로컬, 데이터가 기기를 벗어나지 않음 | `qwen2.5:3b` | `bge-m3`(중국어 + RAG 우수) | GPU 보유, 프라이버시 중시 |
| **GLM** | 무료 클라우드, 안정적이고 무제한 | `glm-4-flash`(무료) | `embedding-3` | GPU 없음, 검색 집약적 시나리오 |
| **GROQ** | 초고속 추론 | `llama-3.3-70b-versatile` | Ollama `bge-m3`로 폴백 | 가끔 쓰기, 품질 추구 |
| **OpenRouter** | 여러 업체 모델 통합, 무료 할당량 포함 | `stepfun/step-3.5-flash:free` 등 | Ollama `bge-m3`로 폴백 | 특정 클라우드 모델 사용 희망 |
| **DeepSeek** | 深度求索 클라우드, 가성비 높음 | `deepseek-v4-flash` / `deepseek-v4-pro` | Ollama `bge-m3`로 폴백 | 중국어 이해, 저비용 클라우드 |

> **Embedding과 LLM 분리**: 임베딩 제공자는 `EMBEDDING_PROVIDER`(`ollama` / `glm`)로 독립적으로 지정하며, 설정하지 않으면 `LLM_PROVIDER`를 따릅니다. 실제로는 `glm`만 GLM `embedding-3`를 사용하고, 나머지(GROQ / OpenRouter / DeepSeek 등 Embedding을 제공하지 않는 클라우드 LLM 포함)는 모두 자동으로 Ollama `bge-m3`를 사용합니다. **따라서 어떤 클라우드 LLM을 사용하더라도 여전히 로컬 Ollama가 임베딩 서비스를 제공해야 합니다(embedding도 glm으로 설정한 경우는 제외).**

#### Ollama 모드(로컬)

```bash
# LLM 주 모델(qwen2.5:3b 권장, 속도와 안정성의 최적 균형)
ollama pull qwen2.5:3b

# 임베딩 모델(필수, 벡터 검색에 사용)
ollama pull bge-m3
```

> **모델 선택 주의 사항**:
> - `qwen2.5:3b` — 권장, ~2s/call, ~100 t/s, graphiti-core 구조화 출력 100% 안정
> - `qwen2.5:7b` — 효과가 더 좋지만 5-10배 느림, 품질을 추구하는 시나리오에 적합
> - `qwen2.5:1.5b` — 속도는 가장 빠르지만 **불안정**(구조화 JSON 성공률 33%에 불과), 사용 권장하지 않음

#### GLM 모드(智谱 AI 클라우드)

```bash
# .env 설정
LLM_PROVIDER=glm
GLM_API_KEY=your_api_key          # https://open.bigmodel.cn 에서 발급
GLM_MODEL=glm-4-flash             # 무료 모델
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768      # Neo4j 벡터 인덱스 차원과 일치해야 함
```

> **GLM 성능 참고**: 쓰기 ~22s(짧은 텍스트), 검색 ~0.34s, Rate Limit 오류 없음, 로컬 Ollama보다 2-5배 느리지만 완전 무료.

#### GROQ 모드(고속 추론)

```bash
# .env 설정
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key         # https://console.groq.com 에서 발급
GROQ_MODEL=llama-3.3-70b-versatile
```

> **주의**: GROQ는 Embedding 서비스를 제공하지 않으므로 Ollama 임베딩 제공자와 함께 사용하거나(자동 폴백) `EMBEDDING_PROVIDER`를 glm으로 설정해야 합니다. GROQ는 엄격한 Rate Limit이 있어 고빈도 사용 시 대량의 재시도가 발생합니다.

#### OpenRouter 모드(여러 업체 모델 통합)

```bash
# .env 설정
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_api_key       # https://openrouter.ai/keys 에서 발급
OPENROUTER_MODEL=stepfun/step-3.5-flash:free   # 임의의 OpenRouter 모델로 변경 가능
```

> **주의**: OpenRouter는 Embedding을 제공하지 않으며, 자동으로 Ollama `bge-m3`로 폴백합니다. 모델 목록은 https://openrouter.ai/models 참조(여러 `:free` 무료 모델 포함).

#### DeepSeek 모드(深度求索)

```bash
# .env 설정
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key         # https://platform.deepseek.com 에서 발급
DEEPSEEK_MODEL=deepseek-v4-flash      # 권장; 또는 deepseek-v4-pro(효과가 더 좋음)
```

> **주의**: DeepSeek는 Embedding을 제공하지 않으며, 자동으로 Ollama `bge-m3`로 폴백합니다. `deepseek-chat` / `deepseek-reasoner`는 2026-07-24에 종료될 예정이므로 `deepseek-v4-flash` / `deepseek-v4-pro` 사용을 권장합니다. DeepSeek는 `json_object` 모드의 prompt에 "json" 문자열을 포함하도록 엄격하게 요구하며, 클라이언트에 이미 안전장치가 내장되어 있어 추가 설정이 필요 없습니다.

## 빠른 시작

### 1. 사전 준비

Neo4j가 로컬에서 실행 중인지 확인하고, 선택한 LLM 제공자에 따라 해당 서비스를 준비합니다:

```bash
# Neo4j 실행 확인(필수)
neo4j status
# 또는 Docker 사용: docker run -d -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/your_password neo4j:latest

# Ollama 모드: Ollama 실행 확인
ollama list
# 시작되지 않은 경우: ollama serve

# GLM / GROQ 모드: 유효한 API Key만 필요하며, 로컬 서비스는 필요 없음
```

### 2. 의존성 설치

```bash
git clone <repo-url>
cd graphiti
uv sync
```

> **주의**: 본 프로젝트는 [uv](https://github.com/astral-sh/uv)를 사용하여 의존성을 관리합니다. 설치되지 않은 경우: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 3. 환경 구성

```bash
cp .env.example .env
```

`.env`를 편집하여 **최소한** 다음 항목을 수정해야 합니다:

```bash
NEO4J_PASSWORD=your_actual_password  # 필수: Neo4j 비밀번호
LLM_PROVIDER=ollama                  # ollama / glm / groq / openrouter / deepseek
OLLAMA_MODEL=qwen2.5:3b              # Ollama 모드: 로컬 LLM 모델
# GLM_API_KEY=your_key               # GLM 모드: 智谱 AI API Key
# GROQ_API_KEY=your_key              # GROQ 모드: GROQ API Key
# OPENROUTER_API_KEY=your_key        # OpenRouter 모드: API Key
# DEEPSEEK_API_KEY=your_key          # DeepSeek 모드: API Key
```

### 4. 서비스 시작

```bash
# HTTP 모드(권장, Web 관리 인터페이스 포함)
uv run python graphiti_mcp_server.py --transport http --port 8000

# 또는 PM2로 백그라운드 실행(장기 운영 권장)
pm2 start ecosystem.config.cjs
```

### 5. 서비스 검증

시작 후 다음 엔드포인트에 접근할 수 있습니다:

| 엔드포인트 | 설명 |
|------|------|
| http://localhost:8000/ | Web 관리 인터페이스 |
| http://localhost:8000/mcp | MCP 엔드포인트(MCP 클라이언트 연결용) |
| http://localhost:8000/health | 헬스 체크(liveness) |
| http://localhost:8000/health/ready | 심층 체크(Neo4j 연결 포함) |
| http://localhost:8000/api/stats | REST API 통계 |

## 프로젝트 구조

```
graphiti/
├── graphiti_mcp_server.py        # 메인 진입점 — MCP 도구 정의(19개 도구)
├── src/
│   ├── config.py                 # 구성 관리(GraphitiConfig, JSON/.env 계층 중첩 지원)
│   ├── web_api.py                # Web 관리 인터페이스 REST API(30개 이상 엔드포인트)
│   ├── ollama_graphiti_client.py  # Ollama LLM 클라이언트(이중 모델 분기)
│   ├── openai_compat_client.py   # OpenAI 호환 LLM 기반 클래스(json_object + 간소화 schema + json 보호)
│   ├── glm_client.py             # GLM(智谱 AI) LLM 클라이언트(OpenAICompatClient 상속)
│   ├── openrouter_client.py      # OpenRouter LLM 클라이언트(OpenAICompatClient 상속)
│   ├── deepseek_client.py        # DeepSeek LLM 클라이언트(OpenAICompatClient 상속)
│   ├── ollama_embedder.py        # Ollama 임베딩 모델 어댑터
│   ├── content_preprocessor.py   # 지능형 콘텐츠 분할(긴 텍스트 자동 분할)
│   ├── deduplication.py          # 메모리 중복 제거(코사인 유사도 비교)
│   ├── importance.py             # 중요도 추적 및 지능형 망각
│   ├── safe_memory_add.py        # 안전 메모리 추가(엔티티 추출 건너뜀)
│   ├── task_store.py             # 백그라운드 작업 SQLite 영속화(TaskStore)
│   ├── timezone_utils.py         # 시간대 변환(UTC→로컬 시간대 표시)
│   ├── i18n.py                   # 백엔드 다국어(REST는 Accept-Language, MCP는 SERVER_LANG에 따름)
│   ├── i18n_generated.py         # 자동 생성된 언어 오버라이드(GENERATED_MESSAGE_OVERRIDES)
│   ├── exceptions.py             # 구조화된 예외 처리(12가지 예외 클래스)
│   └── logging_setup.py          # 로깅 시스템(시간 순환 + 성능 모니터링)
├── web/                          # Web 관리 인터페이스 프런트엔드(SPA, 빌드 없음)
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js                # REST API 래퍼
│       ├── components.js         # UI 컴포넌트 렌더링(커뮤니티 페이지 포함)
│       └── app.js                # SPA 라우팅, 상태 관리
├── tests/                        # 테스트 스위트(203개 테스트)
│   ├── test_content_preprocessor.py  # 분할 로직 테스트(17개)
│   ├── test_new_features.py      # 신규 기능 테스트(32개)
│   ├── test_i18n.py             # 다국어 테스트(57개)
│   ├── test_unit.py              # 단위 테스트
│   ├── test_web_api.py           # Web API 테스트
│   ├── test_web_ui_features.py   # Web UI 기능 테스트
│   ├── test_integration_manual.py # 수동 통합 테스트
│   └── bench_deepseek_flash_vs_pro.py # DeepSeek flash/pro 성능 벤치마크 스크립트
├── tools/                        # 개발 진단 도구
│   ├── status_report.py          # 통합 상태 보고서
│   ├── validate_config.py        # 구성 검증
│   ├── performance_diagnose.py   # 성능 진단
│   ├── inspect_schema.py         # Neo4j 구조 검사
│   ├── batch_reprocess.py        # 일괄 재처리
│   └── migrate_embeddings.py     # Embedding 모델 마이그레이션
├── docs/                         # 문서
├── logs/                         # 로그(시간 순환, 기본 30일 보관)
├── Dockerfile                    # Docker 컨테이너화 배포
└── ecosystem.config.cjs          # PM2 구성
```

## MCP 클라이언트 설정

### HTTP 모드(권장)

Claude Code, Cline 등 HTTP를 지원하는 MCP 클라이언트에 적합합니다:

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

### STDIO 모드

Claude Desktop 등 프로세스를 직접 시작해야 하는 클라이언트에 적합합니다:

**구성 파일 위치:**
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

> **주의**: SSE 모드(`--transport sse`)는 더 이상 권장되지 않습니다. MCP 1.x에는 session 초기화 호환성 문제가 있으므로 HTTP 모드를 사용하세요.

## MCP 도구(19개)

### 메모리 관리(7개)

| 도구 | 설명 |
|------|------|
| `add_memory_simple` | 지식 그래프에 메모리 추가(백그라운드 처리, 지능형 분할, 중복 제거 검사 지원) |
| `add_episode_bulk` | 여러 메모리를 일괄 추가(기본 백그라운드 처리) |
| `add_triplet` | 구조화된 트리플 추가(LLM 건너뜀, 즉시 완료) |
| `search_memory_nodes` | 메모리 노드 검색(16가지 검색 전략, 시간 필터링 지원) |
| `search_memory_facts` | 메모리 사실 검색(관계 유형 필터링, 시간 범위, 유효성 필터링 지원) |
| `advanced_search` | 고급 검색(16가지 전략, 노드+엣지+커뮤니티+에피소드 반환) |
| `get_episodes` | 최근 메모리 에피소드 가져오기 |

### 지식 분석(3개)

| 도구 | 설명 |
|------|------|
| `check_conflicts` | 두 엔티티 간의 사실 충돌 감지(유효 vs 무효화됨) |
| `get_node_edges` | 노드의 입력 엣지와 출력 엣지 관계 탐색 |
| `build_communities` | 커뮤니티 감지 및 클러스터링 트리거(기본 백그라운드 처리) |

### 메모리 유지 관리(2개)

| 도구 | 설명 |
|------|------|
| `get_stale_memories` | 오래되고 접근량이 낮은 메모리 조회 |
| `cleanup_stale_memories` | 오래된 메모리 정리(기본 dry_run 미리보기 모드) |

### 작업 관리

| 도구 | 설명 |
|------|------|
| `get_memory_task_status` | 백그라운드 메모리 처리 작업의 진행 상황과 결과 조회 |

### 삭제 및 조회

| 도구 | 설명 |
|------|------|
| `delete_episode` | 메모리 에피소드 삭제 |
| `delete_entity_edge` | 엔티티 엣지(관계) 삭제 |
| `get_entity_edge` | 엔티티 엣지 상세 정보 가져오기 |

### 시스템 관리

| 도구 | 설명 |
|------|------|
| `get_status` | 서비스 상태 가져오기(Neo4j, LLM, 임베딩 제공자) |
| `test_connection` | Neo4j / LLM / 임베딩 제공자 연결 테스트 |
| `clear_graph` | 그래프 데이터베이스 지우기(group_id별 지우기 지원) |

## 도구 매개변수

### add_memory_simple

| 매개변수 | 유형 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| `name` | string | Y | | 메모리 이름 |
| `episode_body` | string | Y | | 메모리 내용(800자 초과 시 자동 분할) |
| `group_id` | string | | `"default"` | 그룹 ID(프로젝트별 분리 권장) |
| `source` | string | | `"text"` | 소스 유형: `text` / `json` / `message` |
| `source_description` | string | | `"MCP Server"` | 소스 설명 |
| `use_safe_mode` | bool | | `false` | 안전 모드(엔티티 추출 건너뜀, 빠르지만 메모리를 검색할 수 없음) |
| `background` | bool | | `false` | 백그라운드 처리(즉시 task_id 반환, 긴 텍스트에 적합) |
| `force` | bool | | `false` | 중복 제거 검사 건너뛰기(강제 추가) |
| `excluded_entity_types` | list | | | 제외할 엔티티 유형(불필요한 추출량 감소) |

> **성능 팁**:
> - 짧은 텍스트(<800자): 직접 처리, 보통 30-40초 내 완료
> - 긴 텍스트(>800자): 자동으로 여러 단락으로 분할하여 `add_episode_bulk`로 동시 처리(직렬보다 ~33% 빠름)
> - `background=true`를 사용하면 MCP 호출 차단을 방지하고 `get_memory_task_status`로 진행 상황 추적 가능
> - `use_safe_mode=true`는 즉시 완료되지만 메모리를 search 도구로 찾을 수 없음
> - 중복 제거가 활성화된 경우 매우 유사한 메모리에 경고가 표시됨(`force=true`로 건너뛸 수 있음)

### add_episode_bulk

| 매개변수 | 유형 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| `episodes` | list | Y | | 메모리 목록, 각 항목은 `name`과 `content`를 포함 |
| `group_id` | string | | `"default"` | 그룹 ID |
| `source` | string | | `"text"` | 소스 유형 |
| `background` | bool | | `true` | 백그라운드 처리(일괄 처리는 보통 시간이 소요됨) |

### add_triplet

| 매개변수 | 유형 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| `source_name` | string | Y | | 소스 엔티티 이름(예: "Alice") |
| `target_name` | string | Y | | 대상 엔티티 이름(예: "Google") |
| `relation_name` | string | Y | | 관계 이름(예: "works_at") |
| `fact` | string | Y | | 사실 설명(예: "Alice works at Google") |
| `group_id` | string | | `"default"` | 그룹 ID |
| `source_labels` | list | | | 소스 엔티티 레이블 |
| `target_labels` | list | | | 대상 엔티티 레이블 |

### search_memory_nodes

| 매개변수 | 유형 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| `query` | string | Y | | 검색 키워드(자연어) |
| `max_nodes` | int | | `10` | 최대 반환 수량 |
| `group_ids` | list | | | 그룹 필터링(여러 group 연합 검색) |
| `entity_types` | list | | | 엔티티 유형 필터링 |
| `search_recipe` | string | | | 검색 전략(고급 검색 참조) |
| `created_after` | string | | | 생성 시간 하한(ISO datetime) |
| `created_before` | string | | | 생성 시간 상한(ISO datetime) |

### search_memory_facts

| 매개변수 | 유형 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| `query` | string | Y | | 검색 키워드 |
| `max_facts` | int | | `10` | 최대 반환 수량 |
| `group_ids` | list | | | 그룹 필터링 |
| `center_node_uuid` | string | | | 중심 노드 UUID(특정 노드의 관계 탐색) |
| `edge_types` | list | | | 관계 유형 필터링(예: `["works_at"]`) |
| `created_after` | string | | | 생성 시간 하한(ISO datetime) |
| `created_before` | string | | | 생성 시간 상한(ISO datetime) |
| `only_valid` | bool | | `false` | 무효화되지 않은 사실만 반환 |

### advanced_search

| 매개변수 | 유형 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| `query` | string | Y | | 검색 키워드 |
| `search_recipe` | string | | `"combined_rrf"` | 검색 전략(16가지 선택 가능) |
| `max_results` | int | | `10` | 최대 반환 수량 |
| `group_ids` | list | | | 그룹 필터링 |
| `center_node_uuid` | string | | | 중심 노드 UUID |

**사용 가능한 검색 전략(search_recipe):**

| 분류 | 전략 | 설명 |
|------|------|------|
| 종합 | `combined_rrf` | 종합 RRF 융합(기본값, 권장) |
| 종합 | `combined_mmr` | 종합 MMR 다양성 재정렬 |
| 종합 | `combined_cross_encoder` | 종합 Cross-Encoder 정밀 정렬 |
| 엣지 | `edge_rrf` / `edge_mmr` / `edge_cross_encoder` | 엣지 검색(3가지 정렬) |
| 엣지 | `edge_node_distance` / `edge_episode_mentions` | 엣지 검색(그래프 거리/인용 횟수) |
| 노드 | `node_rrf` / `node_mmr` / `node_cross_encoder` | 노드 검색(3가지 정렬) |
| 노드 | `node_node_distance` / `node_episode_mentions` | 노드 검색(그래프 거리/인용 횟수) |
| 커뮤니티 | `community_rrf` / `community_mmr` / `community_cross_encoder` | 커뮤니티 검색 |

### check_conflicts

| 매개변수 | 유형 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| `source_name` | string | Y | | 소스 엔티티 이름 |
| `target_name` | string | Y | | 대상 엔티티 이름 |
| `group_id` | string | | `"default"` | 그룹 ID |

### get_node_edges

| 매개변수 | 유형 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| `node_uuid` | string | Y | | 노드 UUID |
| `include_inbound` | bool | | `true` | 입력 엣지 포함 |
| `include_outbound` | bool | | `true` | 출력 엣지 포함 |
| `max_edges` | int | | `50` | 최대 반환 수량 |

### build_communities

| 매개변수 | 유형 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| `group_ids` | list | | | 지정 그룹(비워두면 전체) |
| `background` | bool | | `true` | 백그라운드 처리 |

### get_stale_memories

| 매개변수 | 유형 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | 며칠 이상 접근하지 않으면 오래된 것으로 간주 |
| `min_access_count` | int | | `2` | 접근 횟수가 이 값보다 낮을 때만 포함 |
| `group_id` | string | | | 그룹 필터링 |
| `limit` | int | | `50` | 최대 반환 수량 |

### cleanup_stale_memories

| 매개변수 | 유형 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | 오래됨 일수 임계값 |
| `min_access_count` | int | | `2` | 최저 접근 횟수 임계값 |
| `group_id` | string | | | 그룹 필터링 |
| `dry_run` | bool | | `true` | 미리보기 모드(실제로 삭제하지 않음) |
| `limit` | int | | `50` | 최대 처리 수량 |

### get_memory_task_status

| 매개변수 | 유형 | 필수 | 설명 |
|------|------|------|------|
| `task_id` | string | Y | 백그라운드 작업 ID(`add_memory_simple(background=true)`에서 반환됨) |

## Web 관리 인터페이스

HTTP 모드에서 `http://localhost:8000/`에 접속하면 사용할 수 있습니다.

**기능:**
- 대시보드 — 노드 수, 사실 수, 메모리 에피소드 수 통계
- 엔티티 노드 — 탐색, 필터링, 벡터 검색
- 사실 관계 — 탐색, 필터링, 벡터 검색
- 메모리 에피소드 — 탐색, 전문 검색, 삭제
- 커뮤니티 탐색 — 커뮤니티 노드 목록, 요약, 커뮤니티 빌드 트리거
- 트리플 폼 — "주체-관계-객체" 구조화 지식 직접 추가
- Group 관리 — 그룹별 필터링, 일괄 삭제
- 지식 그래프 시각화 — 노드 관계 그래픽 표시
- AI 질의응답 — 지식 그래프 기반 지능형 질의응답
- 품질 유지 관리 — 메모리 품질 지표 및 정리 도구
- 일괄 가져오기 — 여러 메모리 에피소드를 한 번에 가져오기(JSON, 1회 최대 500개)
- 런타임 설정 — 현재 활성 설정 확인 및 재시작 없이 일부 파라미터 조정 가능
- 테마 전환 — 다크/라이트 테마

**REST API:**

| 엔드포인트 | 메서드 | 설명 |
|------|------|------|
| `/api/stats` | GET | 대시보드 통계 |
| `/api/groups` | GET | 모든 group_id 가져오기 |
| `/api/groups/stats` | GET | 각 group의 노드/사실/에피소드 통계 |
| `/api/nodes` | GET | 엔티티 노드 탐색(페이지 매김) |
| `/api/facts` | GET | 사실 탐색(페이지 매김) |
| `/api/episodes` | GET | 메모리 에피소드 탐색(페이지 매김) |
| `/api/nodes/{uuid}/relations` | GET | 노드의 입력/출력 엣지 관계 가져오기 |
| `/api/search/nodes` | GET | 벡터 검색 노드 |
| `/api/search/facts` | GET | 벡터 검색 사실 |
| `/api/search/episodes` | GET | 메모리 에피소드 검색 |
| `/api/search/advanced` | GET | 고급 검색(16가지 전략) |
| `/api/communities` | GET | 커뮤니티 노드 탐색(페이지 매김) |
| `/api/communities/build` | POST | 커뮤니티 빌드 트리거 |
| `/api/memory/add` | POST | 단일 메모리 추가 |
| `/api/memory/add-bulk` | POST | 일괄 메모리 추가 |
| `/api/memory/add-triplet` | POST | 트리플 추가 |
| `/api/import/episodes` | POST | 메모리 에피소드 일괄 가져오기(JSON, 1회 최대 500개) |
| `/api/memory/tasks` | GET | 백그라운드 작업 나열(상태 필터링 지원) |
| `/api/memory/tasks/{id}` | GET | 단일 작업 상태 조회 |
| `/api/timeline` | GET | 타임라인 탐색 |
| `/api/graph/subgraph` | GET | 서브그래프 가져오기(시각화) |
| `/api/graph/all` | GET | 전체 그래프 가져오기(시각화) |
| `/api/ask` | GET | AI 질의응답(그래프 기반 검색) |
| `/api/analytics/top-nodes` | GET | 연결도/접근 횟수가 높은 노드 |
| `/api/analytics/quality` | GET | 지식 그래프 품질 지표 |
| `/api/analytics/stale` | GET | 오래된 메모리 조회 |
| `/api/analytics/cleanup` | POST | 오래된 메모리 정리 |
| `/api/config` | GET | 현재 활성 설정 가져오기(API key 제외) |
| `/api/config` | PATCH | 런타임 설정 업데이트(현재 프로세스에만 적용, 재시작 시 초기화) |
| `/api/nodes/{uuid}` | DELETE | 노드 삭제 |
| `/api/episodes/{uuid}` | DELETE | 메모리 에피소드 삭제 |
| `/api/facts/{uuid}` | DELETE | 사실 삭제 |
| `/api/groups/{group_id}` | DELETE | 전체 group 삭제 |

## 구성

### 환경 변수(.env)

구성은 계층 중첩 메커니즘을 사용합니다: JSON 구성 파일을 기반으로 하고, 환경 변수가 개별 값을 덮어씁니다.

```bash
# === 필수 ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password        # 반드시 수정

# === LLM 제공자 선택 ===
LLM_PROVIDER=ollama                 # ollama / glm / groq / openrouter / deepseek

# === Embedding 제공자(선택, 기본값은 LLM_PROVIDER를 따름) ===
# glm만 GLM Embedding을 사용하고, 나머지는 모두 Ollama bge-m3를 사용
# EMBEDDING_PROVIDER=ollama         # ollama / glm

# === Ollama 구성(LLM_PROVIDER=ollama 일 때 사용) ===
OLLAMA_MODEL=qwen2.5:3b             # 주 모델(qwen2.5:3b 권장)
OLLAMA_SMALL_MODEL=qwen2.5:3b       # 소형 모델(간단한 작업용, 다른 모델 선택 가능)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.1

# === GLM 구성(LLM_PROVIDER=glm 일 때 사용) ===
GLM_API_KEY=your_api_key            # https://open.bigmodel.cn 에서 발급
GLM_MODEL=glm-4-flash               # 무료 모델
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768

# === GROQ 구성(LLM_PROVIDER=groq 일 때 사용) ===
GROQ_API_KEY=your_api_key           # https://console.groq.com 에서 발급
GROQ_MODEL=llama-3.3-70b-versatile

# === OpenRouter 구성(LLM_PROVIDER=openrouter 일 때 사용) ===
OPENROUTER_API_KEY=your_api_key     # https://openrouter.ai/keys 에서 발급
OPENROUTER_MODEL=stepfun/step-3.5-flash:free

# === DeepSeek 구성(LLM_PROVIDER=deepseek 일 때 사용) ===
DEEPSEEK_API_KEY=your_api_key       # https://platform.deepseek.com 에서 발급
DEEPSEEK_MODEL=deepseek-v4-flash    # 또는 deepseek-v4-pro

# === Ollama 임베딩 모델(glm 임베딩이 아닐 때 모두 사용) ===
OLLAMA_EMBEDDING_MODEL=bge-m3
OLLAMA_EMBEDDING_DIMENSIONS=768

# === 표시 및 언어(선택) ===
GRAPHITI_DISPLAY_TIMEZONE=Asia/Taipei # API 반환 타임스탬프 표시 시간대(IANA 이름; 저장은 UTC 유지)
SERVER_LANG=zh-TW                     # MCP 도구 응답 언어(전체 locale은 src/i18n.py 참조); REST API는 Accept-Language를 따름

# === 메모리 성능(선택) ===
GRAPHITI_CHUNK_THRESHOLD=800         # 지능형 분할을 트리거하는 글자 수 임계값
GRAPHITI_MAX_CHUNK_SIZE=600          # 단락별 최대 글자 수
GRAPHITI_MAX_COROUTINES=10            # 최대 동시 코루틴 수
GRAPHITI_DEFAULT_BACKGROUND=false    # 기본 백그라운드 처리 여부
TASK_DB_PATH=data/tasks.db           # 백그라운드 작업 SQLite 영속화 경로

# === 중요도 추적 및 지능형 망각(선택) ===
ENABLE_IMPORTANCE_TRACKING=true      # 접근 추적 활성화
IMPORTANCE_WEIGHT=0.1                # 중요도 가중치
STALE_DAYS_THRESHOLD=30              # 오래됨 일수 임계값
STALE_MIN_ACCESS_COUNT=2             # 최저 접근 횟수

# === 로그 ===
LOG_FILE=logs/graphiti_mcp_server.log
LOG_LEVEL=INFO
```

> **전체 환경 변수 목록**은 `.env.example`을 참조하세요

### JSON 구성 파일

버전 관리가 필요한 구성에 적합합니다(환경 변수로 여전히 덮어쓸 수 있음):

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

## PM2 백그라운드 실행

```bash
npm install -g pm2

pm2 start ecosystem.config.cjs      # 시작
pm2 status                           # 상태
pm2 logs graphiti-mcp-http           # 실시간 로그
pm2 restart graphiti-mcp-http --update-env  # 재시작(.env 다시 로드)

pm2 save && pm2 startup              # 부팅 시 자동 시작 설정
```

> **팁**: `.env`를 수정한 후에는 반드시 `--update-env` 플래그로 재시작해야 하며, 그렇지 않으면 환경 변수가 업데이트되지 않습니다.

## Docker 배포

```bash
docker build -t graphiti-mcp .

# 주의: Docker 컨테이너는 Neo4j와 Ollama에 연결할 수 있어야 함
# host network 사용이 가장 간단함
docker run -p 8000:8000 --env-file .env --network host graphiti-mcp

# 또는 외부 서비스 주소를 명시적으로 지정
docker run -p 8000:8000 \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --env-file .env graphiti-mcp
```

## 테스트

```bash
# 모든 테스트 실행(203개, 약 1초)
uv run python -m pytest tests/

# 상세 출력
uv run python -m pytest tests/ -v

# 특정 테스트만 실행
uv run python -m pytest tests/test_content_preprocessor.py -v
uv run python -m pytest tests/test_new_features.py -v
uv run python -m pytest tests/test_unit.py -v
```

> **주의**: `test_integration_manual.py`의 async 테스트 3개는 `pytest-asyncio` 설치가 필요하며, 설치되지 않으면 Failed로 표시되지만 다른 테스트에는 영향을 주지 않습니다. `bench_deepseek_flash_vs_pro.py`는 성능 벤치마크 스크립트이며 단위 테스트가 아닙니다.

## 문제 해결

### Neo4j 연결 실패

```bash
neo4j status                              # 서비스 상태 확인
cypher-shell -u neo4j -p your_password    # 비밀번호 정확성 확인
curl http://localhost:7474                 # HTTP 포트 확인
```

일반적인 원인:
- Neo4j가 시작되지 않음
- 비밀번호 오류(`.env`의 `NEO4J_PASSWORD`)
- 포트가 점유되었거나 방화벽이 차단함

### LLM 연결 실패

**Ollama 모드:**
```bash
ollama serve                # Ollama 서비스 시작
ollama list                 # 설치된 모델 확인
ollama pull qwen2.5:3b      # 누락된 모델 설치
```

일반적인 원인: Ollama가 시작되지 않음, 모델이 설치되지 않음, GPU 메모리 부족

**GLM 모드:**
- `GLM_API_KEY`가 정확한지 확인
- `GLM_EMBEDDING_DIMENSIONS=768`인지 확인(Neo4j 벡터 인덱스와 일치해야 함)
- GLM API 엔드포인트: `https://open.bigmodel.cn/api/paas/v4/`

**GROQ 모드:**
- `GROQ_API_KEY`가 정확한지 확인
- Rate Limit이 빈번하면 GLM 모드로 전환 고려
- GROQ는 Embedding을 제공하지 않으므로 Ollama 임베딩 제공자가 사용 가능한지 확인 필요

**OpenRouter 모드:**
- `OPENROUTER_API_KEY`가 정확하고 `OPENROUTER_MODEL`이 유효한 모델 ID인지 확인(https://openrouter.ai/models 참조)
- Embedding을 제공하지 않으므로 Ollama 임베딩 제공자가 사용 가능한지 확인 필요

**DeepSeek 모드:**
- `DEEPSEEK_API_KEY`가 정확한지 확인
- `Prompt must contain the word 'json'`이 나타나는 경우: 이는 DeepSeek `json_object` 모드의 필수 요구 사항이며, 클라이언트에 이미 안전장치가 내장되어 있음; 여전히 나타난다면 최신 버전의 `src/deepseek_client.py`를 사용하고 있는지 확인하고 서비스를 재시작
- Embedding을 제공하지 않으므로 Ollama 임베딩 제공자가 사용 가능한지 확인 필요

### MCP 연결 오류

`Invalid request parameters` 또는 `Received request before initialization was complete`가 나타나는 경우:

1. HTTP 전송 모드를 사용하는지 확인(**SSE를 사용하지 말 것**)
2. 클라이언트가 `"type": "http"`, `"url": "http://localhost:8000/mcp"`로 설정되었는지 확인
3. 서비스 재시작: `pm2 restart graphiti-mcp-http --update-env`
4. Claude Code에서 `/mcp`를 실행하여 다시 연결

### 메모리 추가 속도가 느림

- **Ollama**: 모델 크기 확인(`qwen2.5:3b`가 `7b`보다 5-10배 빠름), GPU 사용 여부 확인(`ollama ps`)
- **GLM**: 각 add_episode마다 10-20회 이상의 LLM 네트워크 왕복이 필요하며, 짧은 텍스트 ~22s는 정상 값
- **GROQ**: Rate Limit으로 인해 대량의 재시도가 발생하므로 빈번하게 사용하는 경우 GLM 또는 Ollama로 전환 권장
- `background=true`를 사용하여 차단 방지
- `GRAPHITI_CHUNK_THRESHOLD`를 낮춰 긴 텍스트가 더 일찍 분할되도록 함

### PM2 문제

```bash
pm2 status                                        # 상태 확인
pm2 logs graphiti-mcp-http --err --lines 50        # 오류 로그
lsof -i :8000                                     # 포트 점유 확인
pm2 delete graphiti-mcp-http && pm2 start ecosystem.config.cjs  # 완전 재시작
```

## 개발 진단 도구

```bash
uv run python tools/status_report.py           # 통합 상태 보고서(Neo4j + Ollama + 구성)
uv run python tools/validate_config.py         # .env 및 구성 무결성 검증
uv run python tools/performance_diagnose.py    # LLM 성능 진단
uv run python tools/inspect_schema.py          # Neo4j 인덱스 및 제약 조건 검사
uv run python tools/migrate_embeddings.py      # Embedding 모델 마이그레이션(모델 전환 후 벡터 재생성)
```

### Embedding 모델 마이그레이션

embedding 모델을 전환한 후(예: `nomic-embed-text` → `bge-m3`), 마이그레이션 도구를 사용하여 모든 기존 벡터를 재생성하여 검색 품질의 일관성을 보장할 수 있습니다:

```bash
# 마이그레이션이 필요한 수량 미리보기
uv run python tools/migrate_embeddings.py --dry-run

# 전체 마이그레이션(중단점 이어 실행 지원)
uv run python tools/migrate_embeddings.py

# 지정한 group만 마이그레이션
uv run python tools/migrate_embeddings.py --group-id myproject

# 중단점에서 계속(중단 후 재실행)
uv run python tools/migrate_embeddings.py --resume
```

> **호환성**: `bge-m3`는 기본 1024차원이며, 시스템이 자동으로 768차원으로 잘라내어 기존 Neo4j 벡터 인덱스와 호환되도록 합니다. 마이그레이션 전후의 데이터는 공존할 수 있지만, 최상의 검색 품질을 얻으려면 전체 마이그레이션을 실행하는 것이 좋습니다.

## 문서

- [도구 사용 지침](../使用工具的指令.md) — MCP 도구 사용 가이드 및 모범 사례
- [Graphiti Memory Rules](../graphiti-memory-rules.md) — 메모리 규칙 설명

## 라이선스

MIT License
