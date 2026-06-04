# Graphiti MCP Server

Knowledge graph memory service for MCP, built on Graphiti and Neo4j with multi-LLM provider support, a Web management UI, background memory processing, and expanded multilingual i18n.

## Documentation Languages

| Language | Locale | File | Status |
| --- | --- | --- | --- |
| 繁體中文 | `zh-TW` | [README.zh-TW.md](docs/i18n/README.zh-TW.md) | Complete (source) |
| English | `en` | [README.en.md](docs/i18n/README.en.md) | Complete |
| 中文 | `zh-CN` | [README.zh-CN.md](docs/i18n/README.zh-CN.md) | Complete |
| 日本語 | `ja` | [README.ja.md](docs/i18n/README.ja.md) | Complete |
| Português (Portugal) | `pt-PT` | [README.pt-PT.md](docs/i18n/README.pt-PT.md) | Complete |
| Português (Brasil) | `pt-BR` | [README.pt-BR.md](docs/i18n/README.pt-BR.md) | Complete |
| 한국어 | `ko` | [README.ko.md](docs/i18n/README.ko.md) | Complete |
| Español | `es` | [README.es.md](docs/i18n/README.es.md) | Complete |
| Deutsch | `de` | [README.de.md](docs/i18n/README.de.md) | Complete |
| Français | `fr` | [README.fr.md](docs/i18n/README.fr.md) | Complete |
| עברית | `he` | [README.he.md](docs/i18n/README.he.md) | Complete |
| العربية | `ar` | [README.ar.md](docs/i18n/README.ar.md) | Complete |
| Русский | `ru` | [README.ru.md](docs/i18n/README.ru.md) | Complete |
| Polski | `pl` | [README.pl.md](docs/i18n/README.pl.md) | Complete |
| Čeština | `cs` | [README.cs.md](docs/i18n/README.cs.md) | Complete |
| Nederlands | `nl` | [README.nl.md](docs/i18n/README.nl.md) | Complete |
| Türkçe | `tr` | [README.tr.md](docs/i18n/README.tr.md) | Complete |
| Українська | `uk` | [README.uk.md](docs/i18n/README.uk.md) | Complete |
| Tiếng Việt | `vi` | [README.vi.md](docs/i18n/README.vi.md) | Complete |
| Tagalog | `tl` | [README.tl.md](docs/i18n/README.tl.md) | Complete |
| Indonesia | `id` | [README.id.md](docs/i18n/README.id.md) | Complete |
| ไทย | `th` | [README.th.md](docs/i18n/README.th.md) | Complete |
| हिन्दी | `hi` | [README.hi.md](docs/i18n/README.hi.md) | Complete |
| বাংলা | `bn` | [README.bn.md](docs/i18n/README.bn.md) | Complete |
| اردو | `ur` | [README.ur.md](docs/i18n/README.ur.md) | Complete |
| Română | `ro` | [README.ro.md](docs/i18n/README.ro.md) | Complete |
| Svenska | `sv` | [README.sv.md](docs/i18n/README.sv.md) | Complete |
| Italiano | `it` | [README.it.md](docs/i18n/README.it.md) | Complete |
| Ελληνικά | `el` | [README.el.md](docs/i18n/README.el.md) | Complete |
| Magyar | `hu` | [README.hu.md](docs/i18n/README.hu.md) | Complete |
| Suomi | `fi` | [README.fi.md](docs/i18n/README.fi.md) | Complete |
| Dansk | `da` | [README.da.md](docs/i18n/README.da.md) | Complete |
| Norsk | `no` | [README.no.md](docs/i18n/README.no.md) | Complete |

`README.zh-TW.md` is the canonical source and the most detailed project documentation; every other locale listed above is a complete translation of it. All localized READMEs live under `docs/i18n/`, following the file-naming pattern:

```text
docs/i18n/README.<locale>.md
```

Use the locale codes defined in `src/i18n.py`.

## Quick Start

```bash
uv sync
cp .env.example .env
uv run python graphiti_mcp_server.py --transport http --port 8000
```

Open the Web UI:

```text
http://localhost:8000/
```

Useful endpoints:

| Endpoint | Purpose |
| --- | --- |
| `/mcp` | MCP HTTP endpoint |
| `/` | Web management UI |
| `/api/*` | REST API |
| `/health` | Liveness check |
| `/health/ready` | Readiness check with Neo4j validation |

## Supported Runtime Locales

Application i18n currently supports:

```text
zh-TW, en, zh-CN, ja, pt-PT, pt-BR, ko, es, de, fr, he, ar, ru, pl,
cs, nl, tr, uk, vi, tl, id, th, hi, bn, ur, ro, sv, it, el, hu, fi,
da, no
```

Runtime language selection:

| Surface | Language Source |
| --- | --- |
| MCP tools | `SERVER_LANG` |
| REST API | HTTP `Accept-Language` |

## Common Commands

```bash
# Install dependencies
uv sync

# HTTP mode
uv run python graphiti_mcp_server.py --transport http --port 8000

# STDIO mode
uv run python graphiti_mcp_server.py --transport stdio

# Run tests
uv run python -m pytest tests/

# Run i18n tests
uv run python -m pytest tests/test_i18n.py -v
```

## Core Services

| Service | Default |
| --- | --- |
| Neo4j | `bolt://localhost:7687` |
| Ollama | `http://localhost:11434` |
| Web UI | `http://localhost:8000/` |

Supported LLM providers:

```text
ollama, groq, glm, openrouter, deepseek
```

Supported embedding providers:

```text
ollama, glm
```

## More Details

For architecture, MCP tools, REST API endpoints, deployment notes, model recommendations, and complete environment variable documentation, read:

- [繁體中文完整文件](docs/i18n/README.zh-TW.md)
- [English README](docs/i18n/README.en.md)
- [MCP tool guide](docs/使用工具的指令.md)
- [Memory rules](docs/graphiti-memory-rules.md)
- [Environment example](.env.example)
