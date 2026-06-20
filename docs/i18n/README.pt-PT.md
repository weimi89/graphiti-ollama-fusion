# Graphiti MCP Server

Serviço de memória de grafo de conhecimento — um servidor MCP que integra múltiplos fornecedores de LLM (Ollama / GLM / GROQ / OpenRouter / DeepSeek) com a base de dados de grafos Neo4j.

Desenvolvido como uma extensão de [getzep/graphiti](https://github.com/getzep/graphiti), suporta a alternância flexível entre Ollama local e LLM na nuvem, e permite especificar de forma independente o fornecedor de Embedding (desacoplado do LLM).

## Funcionalidades em Destaque

- **Gestão inteligente de memória** — Utiliza um grafo de conhecimento para armazenar e recuperar relações de memória complexas
- **Pesquisa semântica** — Pesquisa híbrida baseada em embeddings vetoriais (vetorial + palavras-chave + travessia de grafo)
- **16 estratégias de pesquisa** — A pesquisa avançada suporta RRF, MMR, Cross-Encoder e diversos outros métodos de reordenação
- **Múltiplos fornecedores de LLM** — Suporta Ollama (local), GLM (Zhipu AI, gratuito), GROQ (inferência de alta velocidade), OpenRouter (agrega modelos de diversos fornecedores), DeepSeek (Deep Seek), com alternância através de variáveis de ambiente com um único comando
- **Embedding desacoplado do LLM** — Pode especificar o embedder de forma independente com `EMBEDDING_PROVIDER`; os LLM na nuvem recorrem automaticamente ao `bge-m3` local
- **Distribuição por modelo duplo** — No modo Ollama, as tarefas complexas utilizam o modelo principal e as tarefas simples mudam automaticamente para o modelo pequeno, melhorando o desempenho
- **Segmentação inteligente de conteúdo** — Textos longos são processados automaticamente em segmentos, reduzindo a carga do LLM (limiar configurável)
- **Processamento de memória em segundo plano** — A adição de memória pode ser executada em segundo plano, retornando imediatamente a chamada MCP; o estado das tarefas é persistido em SQLite, sendo as tarefas inacabadas automaticamente restauradas após reinício
- **Desduplicação de memória** — Deteta automaticamente memórias existentes altamente semelhantes, evitando armazenamento duplicado
- **Deteção de conflitos** — Deteta factos contraditórios entre duas entidades, identificando informação já invalidada e válida
- **Deteção de comunidades** — Agrupa automaticamente entidades relacionadas com base no algoritmo de Label Propagation
- **Acompanhamento de importância** — Regista automaticamente a frequência de acesso das entidades, ordenando os resultados de pesquisa por importância
- **Esquecimento inteligente** — Identifica e limpa memórias obsoletas e de baixo acesso, mantendo o grafo conciso
- **Importação em lote** — Submete várias memórias de uma vez, ideal para migração de grandes volumes de dados
- **Triplos estruturados** — Adiciona diretamente «sujeito-relação-objeto», ignorando a extração por LLM, concluído em segundos
- **Interface de gestão Web** — Painel de controlo, navegação, pesquisa, visualização de grafo de conhecimento, perguntas e respostas com IA, navegação de comunidades, manutenção de qualidade, importação em lote e configurações em tempo de execução integrados
- **Internacionalização (i18n)** — As mensagens de resposta suportam 33 idiomas (incluindo zh-TW / en / zh-CN / ja / pt-BR / ko / es / de / fr, entre outros; zh-TW/en/zh-CN/ja escritos manualmente, os restantes fornecidos pela camada generated); as ferramentas MCP seguem `SERVER_LANG` e a REST API negoceia automaticamente segundo o cabeçalho HTTP `Accept-Language`
- **Tema escuro/claro** — A interface Web suporta a alternância de tema
- **Modo seguro** — Adição rápida de memória com opção de ignorar a extração de entidades
- **Suporte a Docker** — Dockerfile integrado, suportando implementação em contentores
- **Segurança concorrente** — asyncio.Lock protege a inicialização, evitando condições de corrida
- **Verificação de saúde em camadas** — `/health` (liveness) + `/health/ready` (readiness)

## Requisitos do Sistema

| Item | Requisito |
|------|------|
| Python | 3.10+ (recomendado 3.11+) |
| Neo4j | 4.0+ (`bolt://localhost:7687`) |
| Fornecedor de LLM | Ollama / GLM / GROQ / OpenRouter / DeepSeek (escolher um de cinco) |
| Node.js | 18+ (apenas para execução em segundo plano com PM2, opcional) |
| Espaço em disco | ~3GB (modelos Ollama + dados Neo4j) |

### Escolha do Fornecedor de LLM

Alterne através da variável de ambiente `LLM_PROVIDER` (`ollama` / `glm` / `groq` / `openrouter` / `deepseek`):

| Fornecedor | Características | Modelo LLM | Embedding | Cenário adequado |
|--------|------|----------|-----------|----------|
| **Ollama** (predefinido) | Totalmente local, os dados não saem da máquina | `qwen2.5:3b` | `bge-m3` (excelente em chinês + RAG) | Com GPU, valoriza a privacidade |
| **GLM** | Nuvem gratuita, estável e sem limites | `glm-4-flash` (gratuito) | `embedding-3` | Sem GPU, cenários de pesquisa intensiva |
| **GROQ** | Inferência ultrarrápida | `llama-3.3-70b-versatile` | Recorre ao `bge-m3` do Ollama | Escrita ocasional, em busca de qualidade |
| **OpenRouter** | Agrega modelos de diversos fornecedores, inclui quota gratuita | `stepfun/step-3.5-flash:free`, etc. | Recorre ao `bge-m3` do Ollama | Quer usar um modelo de nuvem específico |
| **DeepSeek** | Nuvem da Deep Seek, ótima relação custo-benefício | `deepseek-v4-flash` / `deepseek-v4-pro` | Recorre ao `bge-m3` do Ollama | Compreensão de chinês, nuvem de baixo custo |

> **Embedding desacoplado do LLM**: O embedder é especificado de forma independente através de `EMBEDDING_PROVIDER` (`ollama` / `glm`); quando não definido, segue o `LLM_PROVIDER`. Na prática, apenas `glm` utiliza o GLM `embedding-3`, enquanto todos os restantes (incluindo LLM de nuvem que não fornecem Embedding, como GROQ / OpenRouter / DeepSeek) utilizam automaticamente o `bge-m3` do Ollama. **Por conseguinte, ao usar qualquer LLM de nuvem, continua a ser necessário o Ollama local para fornecer o serviço de embedding (a menos que o embedding também esteja definido como glm).**

#### Modo Ollama (local)

```bash
# Modelo LLM principal (recomendado qwen2.5:3b, o melhor equilíbrio entre velocidade e estabilidade)
ollama pull qwen2.5:3b

# Modelo de embedding (obrigatório, usado para pesquisa vetorial)
ollama pull bge-m3
```

> **Notas sobre a escolha do modelo**:
> - `qwen2.5:3b` — Recomendado, ~2s/chamada, ~100 t/s, saída estruturada do graphiti-core 100% estável
> - `qwen2.5:7b` — Melhores resultados mas 5-10 vezes mais lento, adequado para cenários que exigem qualidade
> - `qwen2.5:1.5b` — O mais rápido, mas **instável** (taxa de sucesso de JSON estruturado de apenas 33%), não recomendado

#### Modo GLM (nuvem Zhipu AI)

```bash
# Configuração do .env
LLM_PROVIDER=glm
GLM_API_KEY=your_api_key          # Obtenha em https://open.bigmodel.cn
GLM_MODEL=glm-4-flash             # Modelo gratuito
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768      # Tem de coincidir com a dimensão do índice vetorial do Neo4j
```

> **Referência de desempenho do GLM**: Escrita ~22s (texto curto), pesquisa ~0,34s, zero erros de Rate Limit, 2-5 vezes mais lento do que o Ollama local mas totalmente gratuito.

#### Modo GROQ (inferência de alta velocidade)

```bash
# Configuração do .env
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key         # Obtenha em https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile
```

> **Nota**: O GROQ não fornece serviço de Embedding, sendo necessário combiná-lo com o embedder do Ollama (recurso automático) ou definir `EMBEDDING_PROVIDER` como glm. O GROQ tem um Rate Limit rigoroso; a utilização de alta frequência irá desencadear numerosas tentativas de repetição.

#### Modo OpenRouter (agrega modelos de diversos fornecedores)

```bash
# Configuração do .env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_api_key       # Obtenha em https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free   # Pode ser alterado para qualquer modelo do OpenRouter
```

> **Nota**: O OpenRouter não fornece Embedding, recorrendo automaticamente ao `bge-m3` do Ollama. A lista de modelos está disponível em https://openrouter.ai/models (inclui vários modelos gratuitos `:free`).

#### Modo DeepSeek (Deep Seek)

```bash
# Configuração do .env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key         # Obtenha em https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash      # Recomendado; ou deepseek-v4-pro (melhores resultados)
```

> **Nota**: O DeepSeek não fornece Embedding, recorrendo automaticamente ao `bge-m3` do Ollama. `deepseek-chat` / `deepseek-reasoner` serão descontinuados a 2026-07-24; recomenda-se a mudança para `deepseek-v4-flash` / `deepseek-v4-pro`. O DeepSeek exige rigorosamente que o prompt no modo `json_object` contenha a cadeia de caracteres "json"; o cliente já inclui uma proteção de salvaguarda integrada, não sendo necessária configuração adicional.

## Início Rápido

### 1. Preparação Prévia

Confirme que o Neo4j está em execução na máquina local e prepare o serviço correspondente de acordo com o fornecedor de LLM escolhido:

```bash
# Confirme que o Neo4j está em execução (obrigatório)
neo4j status
# Ou utilize o Docker: docker run -d -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/your_password neo4j:latest

# Modo Ollama: confirme que o Ollama está em execução
ollama list
# Se não estiver iniciado: ollama serve

# Modo GLM / GROQ: basta uma API Key válida, não é necessário serviço local
```

### 2. Instalar Dependências

```bash
git clone <repo-url>
cd graphiti
uv sync
```

> **Nota**: Este projeto utiliza o [uv](https://github.com/astral-sh/uv) para gerir dependências. Se não estiver instalado: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 3. Configurar o Ambiente

```bash
cp .env.example .env
```

Edite o `.env` e, **no mínimo**, é necessário modificar os seguintes itens:

```bash
NEO4J_PASSWORD=your_actual_password  # Obrigatório: palavra-passe do Neo4j
LLM_PROVIDER=ollama                  # ollama / glm / groq / openrouter / deepseek
OLLAMA_MODEL=qwen2.5:3b              # Modo Ollama: modelo LLM local
# GLM_API_KEY=your_key               # Modo GLM: API Key da Zhipu AI
# GROQ_API_KEY=your_key              # Modo GROQ: API Key do GROQ
# OPENROUTER_API_KEY=your_key        # Modo OpenRouter: API Key
# DEEPSEEK_API_KEY=your_key          # Modo DeepSeek: API Key
```

### 4. Iniciar o Serviço

```bash
# Modo HTTP (recomendado, inclui a interface de gestão Web)
uv run python graphiti_mcp_server.py --transport http --port 8000

# Ou execute em segundo plano com PM2 (recomendado para execução prolongada)
pm2 start ecosystem.config.cjs
```

### 5. Verificar o Serviço

Após o arranque, é possível aceder aos seguintes endpoints:

| Endpoint | Descrição |
|------|------|
| http://localhost:8000/ | Interface de gestão Web |
| http://localhost:8000/mcp | Endpoint MCP (para ligação de clientes MCP) |
| http://localhost:8000/health | Verificação de saúde (liveness) |
| http://localhost:8000/health/ready | Verificação profunda (inclui ligação ao Neo4j) |
| http://localhost:8000/api/stats | Estatísticas da REST API |

## Estrutura do Projeto

```
graphiti/
├── graphiti_mcp_server.py        # Ponto de entrada principal — definição das ferramentas MCP (19 ferramentas)
├── src/
│   ├── config.py                 # Gestão de configuração (GraphitiConfig, suporta sobreposição JSON/.env)
│   ├── web_api.py                # REST API da interface de gestão Web (30+ endpoints)
│   ├── ollama_graphiti_client.py  # Cliente LLM Ollama (distribuição por modelo duplo)
│   ├── openai_compat_client.py   # Classe base LLM compatível com OpenAI (json_object + schema simplificado + proteção de salvaguarda json)
│   ├── glm_client.py             # Cliente LLM GLM (Zhipu AI) (herda OpenAICompatClient)
│   ├── openrouter_client.py      # Cliente LLM OpenRouter (herda OpenAICompatClient)
│   ├── deepseek_client.py        # Cliente LLM DeepSeek (herda OpenAICompatClient)
│   ├── ollama_embedder.py        # Adaptador do modelo de embedding Ollama
│   ├── content_preprocessor.py   # Segmentação inteligente de conteúdo (segmentação automática de texto longo)
│   ├── deduplication.py          # Desduplicação de memória (comparação por similaridade de cosseno)
│   ├── importance.py             # Acompanhamento de importância e esquecimento inteligente
│   ├── safe_memory_add.py        # Adição segura de memória (ignora a extração de entidades)
│   ├── task_store.py             # Persistência SQLite de tarefas em segundo plano (TaskStore)
│   ├── timezone_utils.py         # Conversão de fuso horário (apresentação UTC→fuso horário local)
│   ├── i18n.py                   # Internacionalização no backend (REST segue Accept-Language, MCP segue SERVER_LANG)
│   ├── i18n_generated.py         # Sobreposições de idioma geradas automaticamente (GENERATED_MESSAGE_OVERRIDES)
│   ├── exceptions.py             # Tratamento estruturado de exceções (12 categorias de exceções)
│   └── logging_setup.py          # Sistema de registo (rotação por tempo + monitorização de desempenho)
├── web/                          # Frontend da interface de gestão Web (SPA, sem build)
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js                # Encapsulamento da REST API
│       ├── components.js         # Renderização de componentes da UI (inclui a página de comunidades)
│       └── app.js                # Encaminhamento da SPA, gestão de estado
├── tests/                        # Conjunto de testes (203 testes)
│   ├── test_content_preprocessor.py  # Testes da lógica de segmentação (17 testes)
│   ├── test_new_features.py      # Testes de novas funcionalidades (32 testes)
│   ├── test_i18n.py             # Testes de internacionalização (57 testes)
│   ├── test_unit.py              # Testes unitários
│   ├── test_web_api.py           # Testes da Web API
│   ├── test_web_ui_features.py   # Testes das funcionalidades da Web UI
│   ├── test_integration_manual.py # Testes de integração manuais
│   └── bench_deepseek_flash_vs_pro.py # Script de benchmark de desempenho DeepSeek flash/pro
├── tools/                        # Ferramentas de diagnóstico de desenvolvimento
│   ├── status_report.py          # Relatório de estado consolidado
│   ├── validate_config.py        # Validação de configuração
│   ├── performance_diagnose.py   # Diagnóstico de desempenho
│   ├── inspect_schema.py         # Verificação da estrutura do Neo4j
│   ├── batch_reprocess.py        # Reprocessamento em lote
│   └── migrate_embeddings.py     # Migração do modelo de embedding
├── docs/                         # Documentação
├── logs/                         # Registos (rotação por tempo, conservados por 30 dias por predefinição)
├── Dockerfile                    # Implementação em contentor Docker
└── ecosystem.config.cjs          # Configuração do PM2
```

## Configuração do Cliente MCP

### Modo HTTP (recomendado)

Adequado a clientes MCP que suportam HTTP, como o Claude Code, o Cline, etc.:

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

### Modo STDIO

Adequado a clientes que necessitam de iniciar o processo diretamente, como o Claude Desktop:

**Localização do ficheiro de configuração:**
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

> **Nota**: O modo SSE (`--transport sse`) já não é recomendado. O MCP 1.x tem problemas de compatibilidade na inicialização de sessão; utilize antes o modo HTTP.

## Ferramentas MCP (19 ferramentas)

### Gestão de Memória (7 ferramentas)

| Ferramenta | Descrição |
|------|------|
| `add_memory_simple` | Adiciona memória ao grafo de conhecimento (suporta processamento em segundo plano, segmentação inteligente, verificação de desduplicação) |
| `add_episode_bulk` | Adiciona várias memórias em lote (processamento em segundo plano por predefinição) |
| `add_triplet` | Adição de triplo estruturado (ignora o LLM, concluído em segundos) |
| `search_memory_nodes` | Pesquisa nós de memória (suporta 16 estratégias de pesquisa, filtragem temporal) |
| `search_memory_facts` | Pesquisa factos de memória (suporta filtragem por tipo de relação, intervalo temporal, filtragem por validade) |
| `advanced_search` | Pesquisa avançada (16 estratégias, retorna nós + arestas + comunidades + episódios) |
| `get_episodes` | Obtém os episódios de memória mais recentes |

### Análise de Conhecimento (3 ferramentas)

| Ferramenta | Descrição |
|------|------|
| `check_conflicts` | Deteta conflitos factuais entre duas entidades (válido vs. já invalidado) |
| `get_node_edges` | Explora as relações de arestas de entrada e de saída de um nó |
| `build_communities` | Desencadeia a deteção e o agrupamento de comunidades (processamento em segundo plano por predefinição) |

### Manutenção de Memória (2 ferramentas)

| Ferramenta | Descrição |
|------|------|
| `get_stale_memories` | Consulta memórias obsoletas e de baixo acesso |
| `cleanup_stale_memories` | Limpa memórias obsoletas (modo de pré-visualização dry_run por predefinição) |

### Gestão de Tarefas

| Ferramenta | Descrição |
|------|------|
| `get_memory_task_status` | Consulta o progresso e o resultado de uma tarefa de processamento de memória em segundo plano |

### Eliminação e Consulta

| Ferramenta | Descrição |
|------|------|
| `delete_episode` | Elimina um episódio de memória |
| `delete_entity_edge` | Elimina uma aresta de entidade (relação) |
| `get_entity_edge` | Obtém informação detalhada de uma aresta de entidade |

### Gestão do Sistema

| Ferramenta | Descrição |
|------|------|
| `get_status` | Obtém o estado do serviço (Neo4j, LLM, embedder) |
| `test_connection` | Testa a ligação Neo4j / LLM / embedder |
| `clear_graph` | Limpa a base de dados de grafos (suporta limpeza por group_id) |

## Parâmetros das Ferramentas

### add_memory_simple

| Parâmetro | Tipo | Obrigatório | Valor predefinido | Descrição |
|------|------|------|--------|------|
| `name` | string | Y | | Nome da memória |
| `episode_body` | string | Y | | Conteúdo da memória (segmentado automaticamente acima de 800 caracteres) |
| `group_id` | string | | `"default"` | ID do grupo (recomenda-se isolamento por projeto) |
| `source` | string | | `"text"` | Tipo de origem: `text` / `json` / `message` |
| `source_description` | string | | `"MCP Server"` | Descrição da origem |
| `use_safe_mode` | bool | | `false` | Modo seguro (ignora a extração de entidades, rápido mas a memória não é pesquisável) |
| `background` | bool | | `false` | Processamento em segundo plano (retorna imediatamente o task_id, adequado a texto longo) |
| `force` | bool | | `false` | Ignora a verificação de desduplicação (adição forçada) |
| `excluded_entity_types` | list | | | Tipos de entidade a excluir (reduz a extração desnecessária) |

> **Dicas de desempenho**:
> - Texto curto (<800 caracteres): processamento direto, normalmente concluído em 30-40 segundos
> - Texto longo (>800 caracteres): segmentado automaticamente em vários segmentos, processados em paralelo com `add_episode_bulk` (~33% mais rápido do que em série)
> - Utilizar `background=true` evita o bloqueio da chamada MCP, acompanhando o progresso através de `get_memory_task_status`
> - `use_safe_mode=true` conclui em segundos, mas a memória não pode ser encontrada pelas ferramentas de pesquisa
> - Quando a desduplicação está ativada, memórias altamente semelhantes geram um aviso (`force=true` permite ignorar)

### add_episode_bulk

| Parâmetro | Tipo | Obrigatório | Valor predefinido | Descrição |
|------|------|------|--------|------|
| `episodes` | list | Y | | Lista de memórias, cada item contém `name` e `content` |
| `group_id` | string | | `"default"` | ID do grupo |
| `source` | string | | `"text"` | Tipo de origem |
| `background` | bool | | `true` | Processamento em segundo plano (o processamento em lote costuma ser demorado) |

### add_triplet

| Parâmetro | Tipo | Obrigatório | Valor predefinido | Descrição |
|------|------|------|--------|------|
| `source_name` | string | Y | | Nome da entidade de origem (ex.: "Alice") |
| `target_name` | string | Y | | Nome da entidade de destino (ex.: "Google") |
| `relation_name` | string | Y | | Nome da relação (ex.: "works_at") |
| `fact` | string | Y | | Descrição do facto (ex.: "Alice works at Google") |
| `group_id` | string | | `"default"` | ID do grupo |
| `source_labels` | list | | | Etiquetas da entidade de origem |
| `target_labels` | list | | | Etiquetas da entidade de destino |

### search_memory_nodes

| Parâmetro | Tipo | Obrigatório | Valor predefinido | Descrição |
|------|------|------|--------|------|
| `query` | string | Y | | Palavra-chave de pesquisa (linguagem natural) |
| `max_nodes` | int | | `10` | Número máximo de resultados retornados |
| `group_ids` | list | | | Filtragem por grupo (pesquisa conjunta em vários grupos) |
| `entity_types` | list | | | Filtragem por tipo de entidade |
| `search_recipe` | string | | | Estratégia de pesquisa (ver pesquisa avançada) |
| `created_after` | string | | | Limite inferior do tempo de criação (ISO datetime) |
| `created_before` | string | | | Limite superior do tempo de criação (ISO datetime) |

### search_memory_facts

| Parâmetro | Tipo | Obrigatório | Valor predefinido | Descrição |
|------|------|------|--------|------|
| `query` | string | Y | | Palavra-chave de pesquisa |
| `max_facts` | int | | `10` | Número máximo de resultados retornados |
| `group_ids` | list | | | Filtragem por grupo |
| `center_node_uuid` | string | | | UUID do nó central (explora as relações de um nó específico) |
| `edge_types` | list | | | Filtragem por tipo de relação (ex.: `["works_at"]`) |
| `created_after` | string | | | Limite inferior do tempo de criação (ISO datetime) |
| `created_before` | string | | | Limite superior do tempo de criação (ISO datetime) |
| `only_valid` | bool | | `false` | Retorna apenas factos não invalidados |

### advanced_search

| Parâmetro | Tipo | Obrigatório | Valor predefinido | Descrição |
|------|------|------|--------|------|
| `query` | string | Y | | Palavra-chave de pesquisa |
| `search_recipe` | string | | `"combined_rrf"` | Estratégia de pesquisa (16 opções) |
| `max_results` | int | | `10` | Número máximo de resultados retornados |
| `group_ids` | list | | | Filtragem por grupo |
| `center_node_uuid` | string | | | UUID do nó central |

**Estratégias de pesquisa disponíveis (search_recipe):**

| Categoria | Estratégia | Descrição |
|------|------|------|
| Combinada | `combined_rrf` | Fusão RRF combinada (predefinida, recomendada) |
| Combinada | `combined_mmr` | Reordenação por diversidade MMR combinada |
| Combinada | `combined_cross_encoder` | Reordenação fina Cross-Encoder combinada |
| Aresta | `edge_rrf` / `edge_mmr` / `edge_cross_encoder` | Pesquisa por arestas (3 ordenações) |
| Aresta | `edge_node_distance` / `edge_episode_mentions` | Pesquisa por arestas (distância de grafo/número de referências) |
| Nó | `node_rrf` / `node_mmr` / `node_cross_encoder` | Pesquisa por nós (3 ordenações) |
| Nó | `node_node_distance` / `node_episode_mentions` | Pesquisa por nós (distância de grafo/número de referências) |
| Comunidade | `community_rrf` / `community_mmr` / `community_cross_encoder` | Pesquisa por comunidades |

### check_conflicts

| Parâmetro | Tipo | Obrigatório | Valor predefinido | Descrição |
|------|------|------|--------|------|
| `source_name` | string | Y | | Nome da entidade de origem |
| `target_name` | string | Y | | Nome da entidade de destino |
| `group_id` | string | | `"default"` | ID do grupo |

### get_node_edges

| Parâmetro | Tipo | Obrigatório | Valor predefinido | Descrição |
|------|------|------|--------|------|
| `node_uuid` | string | Y | | UUID do nó |
| `include_inbound` | bool | | `true` | Incluir arestas de entrada |
| `include_outbound` | bool | | `true` | Incluir arestas de saída |
| `max_edges` | int | | `50` | Número máximo de resultados retornados |

### build_communities

| Parâmetro | Tipo | Obrigatório | Valor predefinido | Descrição |
|------|------|------|--------|------|
| `group_ids` | list | | | Grupos especificados (deixar vazio para todos) |
| `background` | bool | | `true` | Processamento em segundo plano |

### get_stale_memories

| Parâmetro | Tipo | Obrigatório | Valor predefinido | Descrição |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Considerada obsoleta após este número de dias sem acesso |
| `min_access_count` | int | | `2` | Apenas incluída se o número de acessos for inferior a este valor |
| `group_id` | string | | | Filtragem por grupo |
| `limit` | int | | `50` | Número máximo de resultados retornados |

### cleanup_stale_memories

| Parâmetro | Tipo | Obrigatório | Valor predefinido | Descrição |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Limiar de dias para obsolescência |
| `min_access_count` | int | | `2` | Limiar do número mínimo de acessos |
| `group_id` | string | | | Filtragem por grupo |
| `dry_run` | bool | | `true` | Modo de pré-visualização (não elimina efetivamente) |
| `limit` | int | | `50` | Número máximo de itens a processar |

### get_memory_task_status

| Parâmetro | Tipo | Obrigatório | Descrição |
|------|------|------|------|
| `task_id` | string | Y | ID da tarefa em segundo plano (retornado por `add_memory_simple(background=true)`) |

## Interface de Gestão Web

No modo HTTP, aceda a `http://localhost:8000/` para utilizar.

**Funcionalidades:**
- Painel de controlo — Estatísticas do número de nós, factos e episódios de memória
- Nós de entidade — Navegação, filtragem, pesquisa vetorial
- Relações de factos — Navegação, filtragem, pesquisa vetorial
- Episódios de memória — Navegação, pesquisa de texto integral, eliminação
- Navegação de comunidades — Lista de nós de comunidade, resumos, desencadear a construção de comunidades
- Formulário de triplos — Adiciona diretamente conhecimento estruturado «sujeito-relação-objeto»
- Gestão de grupos — Filtragem por grupo, eliminação em lote
- Visualização do grafo de conhecimento — Apresentação gráfica das relações entre nós
- Perguntas e respostas com IA — Perguntas e respostas inteligentes baseadas no grafo de conhecimento
- Manutenção de qualidade — Indicadores de qualidade da memória e ferramentas de limpeza
- Importação em lote — Importa múltiplos episódios de memória de uma vez (JSON, limite de 500 por operação)
- Configurações em tempo de execução — Visualiza as configurações atualmente em vigor e permite ajustar alguns parâmetros sem reiniciar
- Alternância de tema — Tema escuro/claro

**REST API:**

| Endpoint | Método | Descrição |
|------|------|------|
| `/api/stats` | GET | Estatísticas do painel de controlo |
| `/api/groups` | GET | Obtém todos os group_id |
| `/api/groups/stats` | GET | Estatísticas de nós/factos/episódios por grupo |
| `/api/nodes` | GET | Navega pelos nós de entidade (paginado) |
| `/api/facts` | GET | Navega pelos factos (paginado) |
| `/api/episodes` | GET | Navega pelos episódios de memória (paginado) |
| `/api/nodes/{uuid}/relations` | GET | Obtém as arestas de entrada/saída de um nó |
| `/api/search/nodes` | GET | Pesquisa vetorial de nós |
| `/api/search/facts` | GET | Pesquisa vetorial de factos |
| `/api/search/episodes` | GET | Pesquisa episódios de memória |
| `/api/search/advanced` | GET | Pesquisa avançada (16 estratégias) |
| `/api/communities` | GET | Navega pelos nós de comunidade (paginado) |
| `/api/communities/build` | POST | Desencadeia a construção de comunidades |
| `/api/memory/add` | POST | Adiciona uma única memória |
| `/api/memory/add-bulk` | POST | Adiciona memórias em lote |
| `/api/memory/add-triplet` | POST | Adiciona um triplo |
| `/api/import/episodes` | POST | Importa episódios de memória em lote (JSON, limite de 500 por operação) |
| `/api/memory/tasks` | GET | Lista tarefas em segundo plano (suporta filtragem por estado) |
| `/api/memory/tasks/{id}` | GET | Consulta o estado de uma única tarefa |
| `/api/timeline` | GET | Navegação cronológica |
| `/api/graph/subgraph` | GET | Obtém um subgrafo (visualização) |
| `/api/graph/all` | GET | Obtém o grafo completo (visualização) |
| `/api/ask` | GET | Perguntas e respostas com IA (baseadas na recuperação do grafo) |
| `/api/analytics/top-nodes` | GET | Nós com maior conectividade/acesso |
| `/api/analytics/quality` | GET | Indicadores de qualidade do grafo de conhecimento |
| `/api/analytics/stale` | GET | Consulta memórias obsoletas |
| `/api/analytics/cleanup` | POST | Limpa memórias obsoletas |
| `/api/config` | GET | Obtém as configurações atualmente em vigor (sem chaves de API) |
| `/api/config` | PATCH | Atualiza configurações modificáveis em tempo de execução (apenas para o processo atual, reposto após reinício) |
| `/api/nodes/{uuid}` | DELETE | Elimina um nó |
| `/api/episodes/{uuid}` | DELETE | Elimina um episódio de memória |
| `/api/facts/{uuid}` | DELETE | Elimina um facto |
| `/api/groups/{group_id}` | DELETE | Elimina um grupo inteiro |

## Configuração

### Variáveis de Ambiente (.env)

A configuração utiliza um mecanismo de sobreposição: o ficheiro de configuração JSON serve de base e as variáveis de ambiente substituem valores individuais.

```bash
# === Obrigatório ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password        # Tem de ser modificado

# === Escolha do fornecedor de LLM ===
LLM_PROVIDER=ollama                 # ollama / glm / groq / openrouter / deepseek

# === Fornecedor de Embedding (opcional, segue LLM_PROVIDER por predefinição) ===
# Apenas glm utiliza o Embedding do GLM, todos os restantes utilizam o bge-m3 do Ollama
# EMBEDDING_PROVIDER=ollama         # ollama / glm

# === Configuração Ollama (utilizada quando LLM_PROVIDER=ollama) ===
OLLAMA_MODEL=qwen2.5:3b             # Modelo principal (recomendado qwen2.5:3b)
OLLAMA_SMALL_MODEL=qwen2.5:3b       # Modelo pequeno (para tarefas simples, pode ser um modelo diferente)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.1

# === Configuração GLM (utilizada quando LLM_PROVIDER=glm) ===
GLM_API_KEY=your_api_key            # Obtenha em https://open.bigmodel.cn
GLM_MODEL=glm-4-flash               # Modelo gratuito
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768

# === Configuração GROQ (utilizada quando LLM_PROVIDER=groq) ===
GROQ_API_KEY=your_api_key           # Obtenha em https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile

# === Configuração OpenRouter (utilizada quando LLM_PROVIDER=openrouter) ===
OPENROUTER_API_KEY=your_api_key     # Obtenha em https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free

# === Configuração DeepSeek (utilizada quando LLM_PROVIDER=deepseek) ===
DEEPSEEK_API_KEY=your_api_key       # Obtenha em https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash    # Ou deepseek-v4-pro

# === Modelo de embedding Ollama (utilizado sempre que o embedding não for glm) ===
OLLAMA_EMBEDDING_MODEL=bge-m3
OLLAMA_EMBEDDING_DIMENSIONS=768

# === Apresentação e idioma (opcional) ===
GRAPHITI_DISPLAY_TIMEZONE=Asia/Taipei # Fuso horário de apresentação do timestamp retornado pela API (nome IANA; o armazenamento mantém-se em UTC)
SERVER_LANG=zh-TW                     # Idioma de resposta das ferramentas MCP (locales completos em src/i18n.py); a REST API segue Accept-Language

# === Desempenho de memória (opcional) ===
GRAPHITI_CHUNK_THRESHOLD=800         # Limiar do número de caracteres que desencadeia a segmentação inteligente
GRAPHITI_MAX_CHUNK_SIZE=600          # Número máximo de caracteres por segmento
GRAPHITI_MAX_COROUTINES=10            # Número máximo de corrotinas em paralelo
GRAPHITI_DEFAULT_BACKGROUND=false    # Processar em segundo plano por predefinição
TASK_DB_PATH=data/tasks.db           # Caminho de persistência SQLite das tarefas em segundo plano

# === Acompanhamento de importância e esquecimento inteligente (opcional) ===
ENABLE_IMPORTANCE_TRACKING=true      # Ativa o acompanhamento de acessos
IMPORTANCE_WEIGHT=0.1                # Peso da importância
STALE_DAYS_THRESHOLD=30              # Limiar de dias para obsolescência
STALE_MIN_ACCESS_COUNT=2             # Número mínimo de acessos

# === Registo ===
LOG_FILE=logs/graphiti_mcp_server.log
LOG_LEVEL=INFO
```

> **A lista completa de variáveis de ambiente** está disponível em `.env.example`

### Ficheiro de Configuração JSON

Adequado a configurações que necessitam de controlo de versão (as variáveis de ambiente continuam a poder substituir):

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

## Execução em Segundo Plano com PM2

```bash
npm install -g pm2

pm2 start ecosystem.config.cjs      # Iniciar
pm2 status                           # Estado
pm2 logs graphiti-mcp-http           # Registos em tempo real
pm2 restart graphiti-mcp-http --update-env  # Reiniciar (recarregar o .env)

pm2 save && pm2 startup              # Configurar arranque automático no sistema
```

> **Dica**: Após modificar o `.env`, é necessário reiniciar com a flag `--update-env`, caso contrário as variáveis de ambiente não serão atualizadas.

## Implementação com Docker

```bash
docker build -t graphiti-mcp .

# Nota: o contentor Docker precisa de conseguir ligar-se ao Neo4j e ao Ollama
# Usar host network é a forma mais simples
docker run -p 8000:8000 --env-file .env --network host graphiti-mcp

# Ou especifique explicitamente o endereço dos serviços externos
docker run -p 8000:8000 \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --env-file .env graphiti-mcp
```

## Testes

```bash
# Executar todos os testes (203 testes, cerca de 1 segundo)
uv run python -m pytest tests/

# Saída detalhada
uv run python -m pytest tests/ -v

# Executar apenas testes específicos
uv run python -m pytest tests/test_content_preprocessor.py -v
uv run python -m pytest tests/test_new_features.py -v
uv run python -m pytest tests/test_unit.py -v
```

> **Nota**: Os 3 testes async em `test_integration_manual.py` requerem a instalação de `pytest-asyncio`; na sua ausência aparecem como Failed, mas não afetam os restantes testes. `bench_deepseek_flash_vs_pro.py` é um script de benchmark de desempenho, não um teste unitário.

## Resolução de Problemas

### Falha na Ligação ao Neo4j

```bash
neo4j status                              # Verificar o estado do serviço
cypher-shell -u neo4j -p your_password    # Confirmar que a palavra-passe está correta
curl http://localhost:7474                 # Confirmar a porta HTTP
```

Causas comuns:
- O Neo4j não está iniciado
- Palavra-passe incorreta (`NEO4J_PASSWORD` no `.env`)
- Porta ocupada ou bloqueada por firewall

### Falha na Ligação ao LLM

**Modo Ollama:**
```bash
ollama serve                # Iniciar o serviço Ollama
ollama list                 # Verificar os modelos instalados
ollama pull qwen2.5:3b      # Instalar o modelo em falta
```

Causas comuns: o Ollama não está iniciado, o modelo não está instalado, memória de GPU insuficiente

**Modo GLM:**
- Confirme que `GLM_API_KEY` está correto
- Confirme que `GLM_EMBEDDING_DIMENSIONS=768` (tem de coincidir com o índice vetorial do Neo4j)
- Endpoint da API GLM: `https://open.bigmodel.cn/api/paas/v4/`

**Modo GROQ:**
- Confirme que `GROQ_API_KEY` está correto
- Quando o Rate Limit ocorrer com frequência, considere mudar para o modo GLM
- O GROQ não fornece Embedding; é necessário garantir que o embedder do Ollama está disponível

**Modo OpenRouter:**
- Confirme que `OPENROUTER_API_KEY` está correto e que `OPENROUTER_MODEL` é um ID de modelo válido (ver https://openrouter.ai/models)
- Não fornece Embedding; é necessário garantir que o embedder do Ollama está disponível

**Modo DeepSeek:**
- Confirme que `DEEPSEEK_API_KEY` está correto
- Se surgir `Prompt must contain the word 'json'`: trata-se de um requisito obrigatório do modo `json_object` do DeepSeek; o cliente já inclui uma proteção de salvaguarda integrada; se ainda assim ocorrer, confirme que está a utilizar a versão mais recente de `src/deepseek_client.py` e reinicie o serviço
- Não fornece Embedding; é necessário garantir que o embedder do Ollama está disponível

### Erro de Ligação MCP

Se surgir `Invalid request parameters` ou `Received request before initialization was complete`:

1. Confirme que está a utilizar o modo de transporte HTTP (**não utilize SSE**)
2. Confirme que o cliente está definido como `"type": "http"`, `"url": "http://localhost:8000/mcp"`
3. Reinicie o serviço: `pm2 restart graphiti-mcp-http --update-env`
4. No Claude Code, execute `/mcp` para voltar a ligar

### Adição de Memória Lenta

- **Ollama**: verifique o tamanho do modelo (`qwen2.5:3b` é 5-10 vezes mais rápido do que `7b`), confirme que está a utilizar a GPU (`ollama ps`)
- **GLM**: cada add_episode requer mais de 10-20 idas e voltas de rede ao LLM; ~22s para texto curto é um valor normal
- **GROQ**: o Rate Limit provoca numerosas tentativas de repetição; se for usado com frequência, recomenda-se mudar para GLM ou Ollama
- Utilize `background=true` para evitar o bloqueio
- Reduza `GRAPHITI_CHUNK_THRESHOLD` para que o texto longo seja segmentado mais cedo

### Problemas com o PM2

```bash
pm2 status                                        # Verificar o estado
pm2 logs graphiti-mcp-http --err --lines 50        # Registos de erro
lsof -i :8000                                     # Verificar a ocupação da porta
pm2 delete graphiti-mcp-http && pm2 start ecosystem.config.cjs  # Reinício completo
```

## Ferramentas de Diagnóstico de Desenvolvimento

```bash
uv run python tools/status_report.py           # Relatório de estado consolidado (Neo4j + Ollama + configuração)
uv run python tools/validate_config.py         # Valida a integridade do .env e da configuração
uv run python tools/performance_diagnose.py    # Diagnóstico de desempenho do LLM
uv run python tools/inspect_schema.py          # Verificação dos índices e restrições do Neo4j
uv run python tools/migrate_embeddings.py      # Migração do modelo de embedding (regenera os vetores após mudar de modelo)
```

### Migração do Modelo de Embedding

Após mudar de modelo de embedding (ex.: `nomic-embed-text` → `bge-m3`), pode utilizar a ferramenta de migração para regenerar todos os vetores existentes, garantindo uma qualidade de pesquisa consistente:

```bash
# Pré-visualizar a quantidade que precisa de ser migrada
uv run python tools/migrate_embeddings.py --dry-run

# Migração total (suporta retoma a partir de ponto de interrupção)
uv run python tools/migrate_embeddings.py

# Migrar apenas um grupo específico
uv run python tools/migrate_embeddings.py --group-id myproject

# Continuar a partir do ponto de interrupção (reexecutar após interrupção)
uv run python tools/migrate_embeddings.py --resume
```

> **Compatibilidade**: O `bge-m3` tem nativamente 1024 dimensões; o sistema trunca automaticamente para 768 dimensões para compatibilidade com o índice vetorial existente do Neo4j. Os dados de antes e depois da migração podem coexistir, mas recomenda-se executar uma migração completa para obter a melhor qualidade de pesquisa.

## Documentação

- [Instruções de utilização das ferramentas](../使用工具的指令.md) — Guia de utilização e melhores práticas das ferramentas MCP
- [Graphiti Memory Rules](../graphiti-memory-rules.md) — Explicação das regras de memória

## Licença

MIT License
