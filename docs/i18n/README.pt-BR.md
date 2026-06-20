# Graphiti MCP Server

Serviço de memória de grafo de conhecimento — servidor MCP que integra múltiplos provedores de LLM (Ollama / GLM / GROQ / OpenRouter / DeepSeek) com o banco de dados de grafo Neo4j.

Desenvolvido como extensão de [getzep/graphiti](https://github.com/getzep/graphiti), suporta alternância flexível entre Ollama local e LLMs em nuvem, além de permitir especificar o provedor de Embedding de forma independente (desacoplado do LLM).

## Funcionalidades em destaque

- **Gerenciamento inteligente de memória** — utiliza grafo de conhecimento para armazenar e recuperar relações de memória complexas
- **Busca semântica** — busca híbrida baseada em embeddings vetoriais (vetor + palavra-chave + travessia de grafo)
- **16 estratégias de busca** — a busca avançada suporta diversos métodos de reordenação como RRF, MMR, Cross-Encoder, entre outros
- **Múltiplos provedores de LLM** — suporta Ollama (local), GLM (Zhipu AI gratuito), GROQ (inferência de alta velocidade), OpenRouter (agregação de modelos de diversas empresas) e DeepSeek, com alternância em um clique via variáveis de ambiente
- **Embedding desacoplado do LLM** — é possível especificar o embedder de forma independente com `EMBEDDING_PROVIDER`; LLMs em nuvem revertem automaticamente para o `bge-m3` local
- **Distribuição de modelo duplo** — no modo Ollama, tarefas complexas usam o modelo principal e tarefas simples alternam automaticamente para um modelo menor, aumentando o desempenho
- **Segmentação inteligente de conteúdo** — textos longos são processados em segmentos automaticamente, reduzindo a carga do LLM (limite configurável)
- **Processamento de memória em segundo plano** — a adição de memória pode ser executada em segundo plano, e a chamada MCP retorna imediatamente; o status das tarefas é persistido em SQLite e tarefas inacabadas são restauradas automaticamente após reinicialização
- **Deduplicação de memória** — detecta automaticamente memórias existentes altamente similares, evitando armazenamento duplicado
- **Detecção de conflitos** — detecta fatos contraditórios entre duas entidades, identificando informações já invalidadas e válidas
- **Detecção de comunidades** — agrupa automaticamente entidades relacionadas com base no algoritmo de Label Propagation
- **Rastreamento de importância** — registra automaticamente a frequência de acesso das entidades; os resultados de busca são ordenados por importância
- **Esquecimento inteligente** — identifica e limpa memórias desatualizadas e de baixo acesso, mantendo o grafo enxuto
- **Importação em lote** — envia múltiplas memórias de uma só vez, ideal para migração de grandes volumes de dados
- **Tripletas estruturadas** — adiciona diretamente "sujeito-relação-objeto", ignorando a extração por LLM e concluindo em segundos
- **Interface de administração Web** — painel integrado, navegação, busca, visualização do grafo de conhecimento, perguntas e respostas com IA, navegação de comunidades, manutenção de qualidade, importação em lote e configuração em tempo de execução
- **Internacionalização (i18n)** — as mensagens de resposta suportam 33 idiomas (incluindo zh-TW / en / zh-CN / ja / pt-BR / ko / es / de / fr, entre outros; zh-TW/en/zh-CN/ja são escritos manualmente, os demais são fornecidos pela camada generated); as ferramentas MCP seguem `SERVER_LANG` e a REST API negocia automaticamente conforme o HTTP `Accept-Language`
- **Tema escuro/claro** — a interface Web suporta alternância de tema
- **Modo seguro** — adição rápida de memória com opção de ignorar a extração de entidades
- **Suporte a Docker** — Dockerfile integrado, com suporte a implantação em contêiner
- **Segurança de concorrência** — asyncio.Lock protege a inicialização, evitando condições de corrida
- **Verificação de saúde em camadas** — `/health` (liveness) + `/health/ready` (readiness)

## Requisitos do sistema

| Item | Requisito |
|------|------|
| Python | 3.10+ (recomendado 3.11+) |
| Neo4j | 4.0+ (`bolt://localhost:7687`) |
| Provedor de LLM | Ollama / GLM / GROQ / OpenRouter / DeepSeek (escolha um dos cinco) |
| Node.js | 18+ (apenas para execução em segundo plano com PM2, opcional) |
| Espaço em disco | ~3GB (modelos do Ollama + dados do Neo4j) |

### Escolha do provedor de LLM

Alterne através da variável de ambiente `LLM_PROVIDER` (`ollama` / `glm` / `groq` / `openrouter` / `deepseek`):

| Provedor | Característica | Modelo de LLM | Embedding | Cenário adequado |
|--------|------|----------|-----------|----------|
| **Ollama** (padrão) | Totalmente local, os dados não saem da máquina | `qwen2.5:3b` | `bge-m3` (excelente em chinês + RAG) | Possui GPU, valoriza a privacidade |
| **GLM** | Nuvem gratuita, estável e sem limites | `glm-4-flash` (gratuito) | `embedding-3` | Sem GPU, cenários de busca intensiva |
| **GROQ** | Inferência ultrarrápida | `llama-3.3-70b-versatile` | reverte para Ollama `bge-m3` | Escrita ocasional, busca por qualidade |
| **OpenRouter** | Agrega modelos de diversas empresas, inclui cota gratuita | `stepfun/step-3.5-flash:free` etc. | reverte para Ollama `bge-m3` | Deseja usar um modelo em nuvem específico |
| **DeepSeek** | Nuvem da DeepSeek, ótimo custo-benefício | `deepseek-v4-flash` / `deepseek-v4-pro` | reverte para Ollama `bge-m3` | Compreensão de chinês, nuvem de baixo custo |

> **Embedding desacoplado do LLM**: o embedder é especificado de forma independente através de `EMBEDDING_PROVIDER` (`ollama` / `glm`); quando não definido, segue `LLM_PROVIDER`. Na prática, apenas `glm` usa o GLM `embedding-3`; todos os demais (incluindo GROQ / OpenRouter / DeepSeek e outros LLMs em nuvem que não fornecem Embedding) usam automaticamente o Ollama `bge-m3`. **Portanto, ao usar qualquer LLM em nuvem, ainda é necessário o Ollama local para fornecer o serviço de embedding (a menos que o embedding também esteja definido como glm).**

#### Modo Ollama (local)

```bash
# Modelo principal de LLM (recomendado qwen2.5:3b, melhor equilíbrio entre velocidade e estabilidade)
ollama pull qwen2.5:3b

# Modelo de embedding (obrigatório, usado para busca vetorial)
ollama pull bge-m3
```

> **Observações sobre a escolha do modelo**:
> - `qwen2.5:3b` — recomendado, ~2s/call, ~100 t/s, saída estruturada do graphiti-core 100% estável
> - `qwen2.5:7b` — melhor resultado, mas 5-10 vezes mais lento, adequado para cenários que buscam qualidade
> - `qwen2.5:1.5b` — o mais rápido, mas **instável** (taxa de sucesso de JSON estruturado de apenas 33%), não recomendado

#### Modo GLM (nuvem Zhipu AI)

```bash
# Configuração do .env
LLM_PROVIDER=glm
GLM_API_KEY=your_api_key          # obtenha em https://open.bigmodel.cn
GLM_MODEL=glm-4-flash             # modelo gratuito
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768      # deve coincidir com a dimensão do índice vetorial do Neo4j
```

> **Referência de desempenho do GLM**: escrita ~22s (texto curto), busca ~0,34s, zero erros de Rate Limit, 2-5 vezes mais lento que o Ollama local, mas totalmente gratuito.

#### Modo GROQ (inferência de alta velocidade)

```bash
# Configuração do .env
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key         # obtenha em https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile
```

> **Atenção**: o GROQ não fornece serviço de Embedding, sendo necessário combiná-lo com o embedder do Ollama (reversão automática) ou definir `EMBEDDING_PROVIDER` como glm. O GROQ tem um Rate Limit rigoroso; o uso em alta frequência aciona muitas retentativas.

#### Modo OpenRouter (agregação de modelos de diversas empresas)

```bash
# Configuração do .env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_api_key       # obtenha em https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free   # pode ser alterado para qualquer modelo do OpenRouter
```

> **Atenção**: o OpenRouter não fornece Embedding, revertendo automaticamente para o Ollama `bge-m3`. A lista de modelos está em https://openrouter.ai/models (inclui vários modelos gratuitos `:free`).

#### Modo DeepSeek

```bash
# Configuração do .env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key         # obtenha em https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash      # recomendado; ou deepseek-v4-pro (melhor resultado)
```

> **Atenção**: o DeepSeek não fornece Embedding, revertendo automaticamente para o Ollama `bge-m3`. `deepseek-chat` / `deepseek-reasoner` serão descontinuados em 2026-07-24; recomenda-se migrar para `deepseek-v4-flash` / `deepseek-v4-pro`. O DeepSeek exige rigorosamente que o prompt do modo `json_object` contenha a string "json"; o cliente já possui proteção de reserva integrada, sem necessidade de configuração adicional.

## Início rápido

### 1. Preparação prévia

Confirme que o Neo4j já está em execução na máquina local e prepare o serviço correspondente de acordo com o provedor de LLM escolhido:

```bash
# Confirme que o Neo4j está em execução (obrigatório)
neo4j status
# Ou usando Docker: docker run -d -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/your_password neo4j:latest

# Modo Ollama: confirme que o Ollama está em execução
ollama list
# Se não estiver iniciado: ollama serve

# Modo GLM / GROQ: basta uma API Key válida, sem necessidade de serviço local
```

### 2. Instalar dependências

```bash
git clone <repo-url>
cd graphiti
uv sync
```

> **Atenção**: este projeto usa [uv](https://github.com/astral-sh/uv) para gerenciar dependências. Se não estiver instalado: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 3. Configurar o ambiente

```bash
cp .env.example .env
```

Edite o `.env` e, **no mínimo**, modifique os seguintes itens:

```bash
NEO4J_PASSWORD=your_actual_password  # obrigatório: senha do Neo4j
LLM_PROVIDER=ollama                  # ollama / glm / groq / openrouter / deepseek
OLLAMA_MODEL=qwen2.5:3b              # modo Ollama: modelo de LLM local
# GLM_API_KEY=your_key               # modo GLM: API Key da Zhipu AI
# GROQ_API_KEY=your_key              # modo GROQ: API Key da GROQ
# OPENROUTER_API_KEY=your_key        # modo OpenRouter: API Key
# DEEPSEEK_API_KEY=your_key          # modo DeepSeek: API Key
```

### 4. Iniciar o serviço

```bash
# Modo HTTP (recomendado, inclui a interface de administração Web)
uv run python graphiti_mcp_server.py --transport http --port 8000

# Ou usando execução em segundo plano com PM2 (recomendado para execução prolongada)
pm2 start ecosystem.config.cjs
```

### 5. Verificar o serviço

Após iniciar, é possível acessar os seguintes endpoints:

| Endpoint | Descrição |
|------|------|
| http://localhost:8000/ | Interface de administração Web |
| http://localhost:8000/mcp | Endpoint MCP (para conexão de clientes MCP) |
| http://localhost:8000/health | Verificação de saúde (liveness) |
| http://localhost:8000/health/ready | Verificação aprofundada (inclui conexão com Neo4j) |
| http://localhost:8000/api/stats | Estatísticas da REST API |

## Estrutura do projeto

```
graphiti/
├── graphiti_mcp_server.py        # Entrada principal — definição das ferramentas MCP (19 ferramentas)
├── src/
│   ├── config.py                 # Gerenciamento de configuração (GraphitiConfig, suporta sobreposição JSON/.env)
│   ├── web_api.py                # REST API da interface de administração Web (30+ endpoints)
│   ├── ollama_graphiti_client.py  # Cliente de LLM Ollama (distribuição de modelo duplo)
│   ├── openai_compat_client.py   # Classe base de LLM compatível com OpenAI (json_object + schema simplificado + proteção de reserva json)
│   ├── glm_client.py             # Cliente de LLM GLM (Zhipu AI) (herda OpenAICompatClient)
│   ├── openrouter_client.py      # Cliente de LLM OpenRouter (herda OpenAICompatClient)
│   ├── deepseek_client.py        # Cliente de LLM DeepSeek (herda OpenAICompatClient)
│   ├── ollama_embedder.py        # Adaptador do modelo de embedding Ollama
│   ├── content_preprocessor.py   # Segmentação inteligente de conteúdo (segmentação automática de textos longos)
│   ├── deduplication.py          # Deduplicação de memória (comparação por similaridade de cosseno)
│   ├── importance.py             # Rastreamento de importância e esquecimento inteligente
│   ├── safe_memory_add.py        # Adição segura de memória (ignora a extração de entidades)
│   ├── task_store.py             # Persistência SQLite de tarefas em segundo plano (TaskStore)
│   ├── timezone_utils.py         # Conversão de fuso horário (exibição UTC→fuso horário local)
│   ├── i18n.py                   # Internacionalização do backend (REST segue Accept-Language, MCP segue SERVER_LANG)
│   ├── i18n_generated.py         # Sobreposições de idiomas geradas automaticamente (GENERATED_MESSAGE_OVERRIDES)
│   ├── exceptions.py             # Tratamento estruturado de exceções (12 classes de exceção)
│   └── logging_setup.py          # Sistema de logs (rotação temporal + monitoramento de desempenho)
├── web/                          # Frontend da interface de administração Web (SPA, sem build)
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js                # Encapsulamento da REST API
│       ├── components.js         # Renderização de componentes de UI (inclui página de comunidades)
│       └── app.js                # Roteamento SPA, gerenciamento de estado
├── tests/                        # Conjunto de testes (203 testes)
│   ├── test_content_preprocessor.py  # Teste da lógica de segmentação (17)
│   ├── test_new_features.py      # Teste de novas funcionalidades (32)
│   ├── test_i18n.py             # Teste de internacionalização (57)
│   ├── test_unit.py              # Testes unitários
│   ├── test_web_api.py           # Teste da Web API
│   ├── test_web_ui_features.py   # Teste de funcionalidades da Web UI
│   ├── test_integration_manual.py # Teste de integração manual
│   └── bench_deepseek_flash_vs_pro.py # Script de benchmark de desempenho flash/pro do DeepSeek
├── tools/                        # Ferramentas de diagnóstico de desenvolvimento
│   ├── status_report.py          # Relatório consolidado de status
│   ├── validate_config.py        # Validação de configuração
│   ├── performance_diagnose.py   # Diagnóstico de desempenho
│   ├── inspect_schema.py         # Verificação da estrutura do Neo4j
│   ├── batch_reprocess.py        # Reprocessamento em lote
│   └── migrate_embeddings.py     # Migração do modelo de Embedding (regenera vetores após trocar de modelo)
├── docs/                         # Documentação
├── logs/                         # Logs (rotação temporal, retenção padrão de 30 dias)
├── Dockerfile                    # Implantação em contêiner Docker
└── ecosystem.config.cjs          # Configuração do PM2
```

## Configuração do cliente MCP

### Modo HTTP (recomendado)

Adequado para clientes MCP que suportam HTTP, como Claude Code, Cline, etc.:

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

Adequado para clientes que precisam iniciar o processo diretamente, como o Claude Desktop:

**Localização do arquivo de configuração:**
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

> **Atenção**: o modo SSE (`--transport sse`) não é mais recomendado. O MCP 1.x tem problemas de compatibilidade na inicialização da session; use o modo HTTP.

## Ferramentas MCP (19 ferramentas)

### Gerenciamento de memória (7)

| Ferramenta | Descrição |
|------|------|
| `add_memory_simple` | Adiciona memória ao grafo de conhecimento (suporta processamento em segundo plano, segmentação inteligente, verificação de deduplicação) |
| `add_episode_bulk` | Adiciona múltiplas memórias em lote (processamento em segundo plano por padrão) |
| `add_triplet` | Adição de tripleta estruturada (ignora o LLM, concluído em segundos) |
| `search_memory_nodes` | Busca nós de memória (suporta 16 estratégias de busca, filtro temporal) |
| `search_memory_facts` | Busca fatos de memória (suporta filtro por tipo de relação, intervalo de tempo, filtro de validade) |
| `advanced_search` | Busca avançada (16 estratégias, retorna nós + arestas + comunidades + fragmentos) |
| `get_episodes` | Obtém os fragmentos de memória mais recentes |

### Análise de conhecimento (3)

| Ferramenta | Descrição |
|------|------|
| `check_conflicts` | Detecta conflitos de fatos entre duas entidades (válido vs. invalidado) |
| `get_node_edges` | Explora as relações de arestas de entrada e saída de um nó |
| `build_communities` | Aciona a detecção e o agrupamento de comunidades (processamento em segundo plano por padrão) |

### Manutenção de memória (2)

| Ferramenta | Descrição |
|------|------|
| `get_stale_memories` | Consulta memórias desatualizadas e de baixo acesso |
| `cleanup_stale_memories` | Limpa memórias desatualizadas (modo de visualização dry_run por padrão) |

### Gerenciamento de tarefas

| Ferramenta | Descrição |
|------|------|
| `get_memory_task_status` | Consulta o progresso e o resultado de tarefas de processamento de memória em segundo plano |

### Exclusão e consulta

| Ferramenta | Descrição |
|------|------|
| `delete_episode` | Exclui um fragmento de memória |
| `delete_entity_edge` | Exclui uma aresta de entidade (relação) |
| `get_entity_edge` | Obtém informações detalhadas de uma aresta de entidade |

### Administração do sistema

| Ferramenta | Descrição |
|------|------|
| `get_status` | Obtém o status do serviço (Neo4j, LLM, embedder) |
| `test_connection` | Testa a conexão com Neo4j / LLM / embedder |
| `clear_graph` | Limpa o banco de dados de grafo (suporta limpeza por group_id) |

## Parâmetros das ferramentas

### add_memory_simple

| Parâmetro | Tipo | Obrigatório | Valor padrão | Descrição |
|------|------|------|--------|------|
| `name` | string | Y | | Nome da memória |
| `episode_body` | string | Y | | Conteúdo da memória (segmentado automaticamente acima de 800 caracteres) |
| `group_id` | string | | `"default"` | ID do grupo (recomenda-se isolar por projeto) |
| `source` | string | | `"text"` | Tipo de origem: `text` / `json` / `message` |
| `source_description` | string | | `"MCP Server"` | Descrição da origem |
| `use_safe_mode` | bool | | `false` | Modo seguro (ignora a extração de entidades, rápido, mas a memória não pode ser pesquisada) |
| `background` | bool | | `false` | Processamento em segundo plano (retorna task_id imediatamente, adequado para textos longos) |
| `force` | bool | | `false` | Ignora a verificação de deduplicação (adição forçada) |
| `excluded_entity_types` | list | | | Tipos de entidade excluídos (reduz a quantidade de extração desnecessária) |

> **Dicas de desempenho**:
> - Texto curto (<800 caracteres): processamento direto, geralmente concluído em 30-40 segundos
> - Texto longo (>800 caracteres): segmentado automaticamente em vários trechos, processado de forma concorrente com `add_episode_bulk` (~33% mais rápido que serial)
> - Usar `background=true` evita o bloqueio da chamada MCP; acompanhe o progresso através de `get_memory_task_status`
> - `use_safe_mode=true` é concluído em segundos, mas a memória não pode ser encontrada pelas ferramentas de search
> - Com a deduplicação habilitada, memórias altamente similares geram um aviso (`force=true` pode ignorá-lo)

### add_episode_bulk

| Parâmetro | Tipo | Obrigatório | Valor padrão | Descrição |
|------|------|------|--------|------|
| `episodes` | list | Y | | Lista de memórias, cada item contendo `name` e `content` |
| `group_id` | string | | `"default"` | ID do grupo |
| `source` | string | | `"text"` | Tipo de origem |
| `background` | bool | | `true` | Processamento em segundo plano (lotes geralmente consomem tempo) |

### add_triplet

| Parâmetro | Tipo | Obrigatório | Valor padrão | Descrição |
|------|------|------|--------|------|
| `source_name` | string | Y | | Nome da entidade de origem (ex.: "Alice") |
| `target_name` | string | Y | | Nome da entidade de destino (ex.: "Google") |
| `relation_name` | string | Y | | Nome da relação (ex.: "works_at") |
| `fact` | string | Y | | Descrição do fato (ex.: "Alice works at Google") |
| `group_id` | string | | `"default"` | ID do grupo |
| `source_labels` | list | | | Rótulos da entidade de origem |
| `target_labels` | list | | | Rótulos da entidade de destino |

### search_memory_nodes

| Parâmetro | Tipo | Obrigatório | Valor padrão | Descrição |
|------|------|------|--------|------|
| `query` | string | Y | | Palavra-chave de busca (linguagem natural) |
| `max_nodes` | int | | `10` | Quantidade máxima de retorno |
| `group_ids` | list | | | Filtro por grupo (busca combinada em vários grupos) |
| `entity_types` | list | | | Filtro por tipo de entidade |
| `search_recipe` | string | | | Estratégia de busca (ver busca avançada) |
| `created_after` | string | | | Limite inferior de tempo de criação (ISO datetime) |
| `created_before` | string | | | Limite superior de tempo de criação (ISO datetime) |

### search_memory_facts

| Parâmetro | Tipo | Obrigatório | Valor padrão | Descrição |
|------|------|------|--------|------|
| `query` | string | Y | | Palavra-chave de busca |
| `max_facts` | int | | `10` | Quantidade máxima de retorno |
| `group_ids` | list | | | Filtro por grupo |
| `center_node_uuid` | string | | | UUID do nó central (explora as relações de um nó específico) |
| `edge_types` | list | | | Filtro por tipo de relação (ex.: `["works_at"]`) |
| `created_after` | string | | | Limite inferior de tempo de criação (ISO datetime) |
| `created_before` | string | | | Limite superior de tempo de criação (ISO datetime) |
| `only_valid` | bool | | `false` | Retorna apenas fatos não invalidados |

### advanced_search

| Parâmetro | Tipo | Obrigatório | Valor padrão | Descrição |
|------|------|------|--------|------|
| `query` | string | Y | | Palavra-chave de busca |
| `search_recipe` | string | | `"combined_rrf"` | Estratégia de busca (16 opções) |
| `max_results` | int | | `10` | Quantidade máxima de retorno |
| `group_ids` | list | | | Filtro por grupo |
| `center_node_uuid` | string | | | UUID do nó central |

**Estratégias de busca disponíveis (search_recipe):**

| Categoria | Estratégia | Descrição |
|------|------|------|
| Combinada | `combined_rrf` | Fusão RRF combinada (padrão, recomendado) |
| Combinada | `combined_mmr` | Reordenação por diversidade MMR combinada |
| Combinada | `combined_cross_encoder` | Refinamento Cross-Encoder combinado |
| Aresta | `edge_rrf` / `edge_mmr` / `edge_cross_encoder` | Busca de arestas (3 ordenações) |
| Aresta | `edge_node_distance` / `edge_episode_mentions` | Busca de arestas (distância no grafo/número de menções) |
| Nó | `node_rrf` / `node_mmr` / `node_cross_encoder` | Busca de nós (3 ordenações) |
| Nó | `node_node_distance` / `node_episode_mentions` | Busca de nós (distância no grafo/número de menções) |
| Comunidade | `community_rrf` / `community_mmr` / `community_cross_encoder` | Busca de comunidades |

### check_conflicts

| Parâmetro | Tipo | Obrigatório | Valor padrão | Descrição |
|------|------|------|--------|------|
| `source_name` | string | Y | | Nome da entidade de origem |
| `target_name` | string | Y | | Nome da entidade de destino |
| `group_id` | string | | `"default"` | ID do grupo |

### get_node_edges

| Parâmetro | Tipo | Obrigatório | Valor padrão | Descrição |
|------|------|------|--------|------|
| `node_uuid` | string | Y | | UUID do nó |
| `include_inbound` | bool | | `true` | Inclui arestas de entrada |
| `include_outbound` | bool | | `true` | Inclui arestas de saída |
| `max_edges` | int | | `50` | Quantidade máxima de retorno |

### build_communities

| Parâmetro | Tipo | Obrigatório | Valor padrão | Descrição |
|------|------|------|--------|------|
| `group_ids` | list | | | Grupos especificados (vazio significa todos) |
| `background` | bool | | `true` | Processamento em segundo plano |

### get_stale_memories

| Parâmetro | Tipo | Obrigatório | Valor padrão | Descrição |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Considera desatualizado após quantos dias sem acesso |
| `min_access_count` | int | | `2` | Só inclui se o número de acessos for inferior a este valor |
| `group_id` | string | | | Filtro por grupo |
| `limit` | int | | `50` | Quantidade máxima de retorno |

### cleanup_stale_memories

| Parâmetro | Tipo | Obrigatório | Valor padrão | Descrição |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Limite de dias para desatualização |
| `min_access_count` | int | | `2` | Limite mínimo de número de acessos |
| `group_id` | string | | | Filtro por grupo |
| `dry_run` | bool | | `true` | Modo de visualização (não exclui de fato) |
| `limit` | int | | `50` | Quantidade máxima de processamento |

### get_memory_task_status

| Parâmetro | Tipo | Obrigatório | Descrição |
|------|------|------|------|
| `task_id` | string | Y | ID da tarefa em segundo plano (retornado por `add_memory_simple(background=true)`) |

## Interface de administração Web

No modo HTTP, acesse `http://localhost:8000/` para utilizá-la.

**Funcionalidades:**
- Painel — estatísticas de número de nós, fatos e fragmentos de memória
- Nós de entidade — navegação, filtragem, busca vetorial
- Relações de fato — navegação, filtragem, busca vetorial
- Fragmentos de memória — navegação, busca em texto completo, exclusão
- Navegação de comunidades — lista de nós de comunidade, resumos, acionamento da construção de comunidades
- Formulário de tripletas — adiciona diretamente conhecimento estruturado "sujeito-relação-objeto"
- Gerenciamento de Group — filtragem por grupo, exclusão em lote
- Visualização do grafo de conhecimento — exibição gráfica das relações entre nós
- Perguntas e respostas com IA — perguntas e respostas inteligentes baseadas no grafo de conhecimento
- Manutenção de qualidade — métricas de qualidade da memória e ferramentas de limpeza
- Importação em lote — importa múltiplos fragmentos de memória de uma só vez (JSON, limite de 500 por vez)
- Configuração em tempo de execução — visualiza as configurações atualmente ativas e permite ajustar alguns parâmetros sem reinicialização
- Alternância de tema — tema escuro/claro

**REST API:**

| Endpoint | Método | Descrição |
|------|------|------|
| `/api/stats` | GET | Estatísticas do painel |
| `/api/groups` | GET | Obtém todos os group_id |
| `/api/groups/stats` | GET | Estatísticas de nós/fatos/fragmentos por group |
| `/api/nodes` | GET | Navega pelos nós de entidade (paginado) |
| `/api/facts` | GET | Navega pelos fatos (paginado) |
| `/api/episodes` | GET | Navega pelos fragmentos de memória (paginado) |
| `/api/nodes/{uuid}/relations` | GET | Obtém as arestas de entrada/saída de um nó |
| `/api/search/nodes` | GET | Busca vetorial de nós |
| `/api/search/facts` | GET | Busca vetorial de fatos |
| `/api/search/episodes` | GET | Busca fragmentos de memória |
| `/api/search/advanced` | GET | Busca avançada (16 estratégias) |
| `/api/communities` | GET | Navega pelos nós de comunidade (paginado) |
| `/api/communities/build` | POST | Aciona a construção de comunidades |
| `/api/memory/add` | POST | Adiciona uma única memória |
| `/api/memory/add-bulk` | POST | Adiciona memórias em lote |
| `/api/memory/add-triplet` | POST | Adiciona uma tripleta |
| `/api/import/episodes` | POST | Importa fragmentos de memória em lote (JSON, limite de 500 por vez) |
| `/api/memory/tasks` | GET | Lista tarefas em segundo plano (suporta filtro por status) |
| `/api/memory/tasks/{id}` | GET | Consulta o status de uma única tarefa |
| `/api/timeline` | GET | Navegação por linha do tempo |
| `/api/graph/subgraph` | GET | Obtém subgrafo (visualização) |
| `/api/graph/all` | GET | Obtém o grafo completo (visualização) |
| `/api/ask` | GET | Perguntas e respostas com IA (baseado em recuperação de grafo) |
| `/api/analytics/top-nodes` | GET | Nós com alta conectividade/alto acesso |
| `/api/analytics/quality` | GET | Métricas de qualidade do grafo de conhecimento |
| `/api/analytics/stale` | GET | Consulta memórias desatualizadas |
| `/api/analytics/cleanup` | POST | Limpa memórias desatualizadas |
| `/api/config` | GET | Obtém as configurações atualmente ativas (sem API keys) |
| `/api/config` | PATCH | Atualiza configurações modificáveis em tempo de execução (válido apenas no processo atual, revertido ao reiniciar) |
| `/api/nodes/{uuid}` | DELETE | Exclui um nó |
| `/api/episodes/{uuid}` | DELETE | Exclui um fragmento de memória |
| `/api/facts/{uuid}` | DELETE | Exclui um fato |
| `/api/groups/{group_id}` | DELETE | Exclui um group inteiro |

## Configuração

### Variáveis de ambiente (.env)

A configuração usa um mecanismo de sobreposição: o arquivo de configuração JSON serve de base e as variáveis de ambiente substituem valores individuais.

```bash
# === Obrigatório ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password        # deve ser modificado

# === Escolha do provedor de LLM ===
LLM_PROVIDER=ollama                 # ollama / glm / groq / openrouter / deepseek

# === Provedor de Embedding (opcional, segue LLM_PROVIDER por padrão) ===
# Apenas glm usa o GLM Embedding; todos os demais usam o Ollama bge-m3
# EMBEDDING_PROVIDER=ollama         # ollama / glm

# === Configuração do Ollama (usada quando LLM_PROVIDER=ollama) ===
OLLAMA_MODEL=qwen2.5:3b             # modelo principal (recomendado qwen2.5:3b)
OLLAMA_SMALL_MODEL=qwen2.5:3b       # modelo menor (para tarefas simples, pode ser um modelo diferente)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.1

# === Configuração do GLM (usada quando LLM_PROVIDER=glm) ===
GLM_API_KEY=your_api_key            # obtenha em https://open.bigmodel.cn
GLM_MODEL=glm-4-flash               # modelo gratuito
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768

# === Configuração do GROQ (usada quando LLM_PROVIDER=groq) ===
GROQ_API_KEY=your_api_key           # obtenha em https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile

# === Configuração do OpenRouter (usada quando LLM_PROVIDER=openrouter) ===
OPENROUTER_API_KEY=your_api_key     # obtenha em https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free

# === Configuração do DeepSeek (usada quando LLM_PROVIDER=deepseek) ===
DEEPSEEK_API_KEY=your_api_key       # obtenha em https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash    # ou deepseek-v4-pro

# === Modelo de embedding do Ollama (usado em todos os casos de embedding que não sejam glm) ===
OLLAMA_EMBEDDING_MODEL=bge-m3
OLLAMA_EMBEDDING_DIMENSIONS=768

# === Exibição e idioma (opcional) ===
GRAPHITI_DISPLAY_TIMEZONE=Asia/Taipei # fuso horário de exibição dos timestamps retornados pela API (nome IANA; armazenamento permanece em UTC)
SERVER_LANG=zh-TW                     # idioma de resposta das ferramentas MCP (locales completos em src/i18n.py); a REST API segue o Accept-Language

# === Desempenho de memória (opcional) ===
GRAPHITI_CHUNK_THRESHOLD=800         # limite de caracteres para acionar a segmentação inteligente
GRAPHITI_MAX_CHUNK_SIZE=600          # número máximo de caracteres por segmento
GRAPHITI_MAX_COROUTINES=10            # número máximo de corrotinas concorrentes
GRAPHITI_DEFAULT_BACKGROUND=false    # se o processamento em segundo plano é o padrão
TASK_DB_PATH=data/tasks.db           # caminho de persistência SQLite para tarefas em segundo plano

# === Rastreamento de importância e esquecimento inteligente (opcional) ===
ENABLE_IMPORTANCE_TRACKING=true      # habilita o rastreamento de acessos
IMPORTANCE_WEIGHT=0.1                # peso da importância
STALE_DAYS_THRESHOLD=30              # limite de dias para desatualização
STALE_MIN_ACCESS_COUNT=2             # número mínimo de acessos

# === Logs ===
LOG_FILE=logs/graphiti_mcp_server.log
LOG_LEVEL=INFO
```

> **Lista completa de variáveis de ambiente** consulte `.env.example`

### Arquivo de configuração JSON

Adequado para configurações que precisam de controle de versão (as variáveis de ambiente ainda podem substituir):

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

## Execução em segundo plano com PM2

```bash
npm install -g pm2

pm2 start ecosystem.config.cjs      # iniciar
pm2 status                           # status
pm2 logs graphiti-mcp-http           # logs em tempo real
pm2 restart graphiti-mcp-http --update-env  # reiniciar (recarrega o .env)

pm2 save && pm2 startup              # configurar inicialização automática no boot
```

> **Dica**: após modificar o `.env`, é obrigatório reiniciar usando a flag `--update-env`, caso contrário as variáveis de ambiente não serão atualizadas.

## Implantação com Docker

```bash
docker build -t graphiti-mcp .

# Atenção: o contêiner Docker precisa conseguir se conectar ao Neo4j e ao Ollama
# Usar a host network é o mais simples
docker run -p 8000:8000 --env-file .env --network host graphiti-mcp

# Ou especificar explicitamente os endereços dos serviços externos
docker run -p 8000:8000 \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --env-file .env graphiti-mcp
```

## Testes

```bash
# Executar todos os testes (203, cerca de 1 segundo)
uv run python -m pytest tests/

# Saída detalhada
uv run python -m pytest tests/ -v

# Executar apenas um teste específico
uv run python -m pytest tests/test_content_preprocessor.py -v
uv run python -m pytest tests/test_new_features.py -v
uv run python -m pytest tests/test_unit.py -v
```

> **Atenção**: os 3 testes async em `test_integration_manual.py` requerem a instalação de `pytest-asyncio`; sem ele, serão exibidos como Failed, mas não afetam os outros testes. `bench_deepseek_flash_vs_pro.py` é um script de benchmark de desempenho, não um teste unitário.

## Solução de problemas

### Falha na conexão com o Neo4j

```bash
neo4j status                              # verifica o status do serviço
cypher-shell -u neo4j -p your_password    # confirma se a senha está correta
curl http://localhost:7474                 # confirma a porta HTTP
```

Causas comuns:
- Neo4j não iniciado
- Senha incorreta (`NEO4J_PASSWORD` no `.env`)
- Porta ocupada ou bloqueada pelo firewall

### Falha na conexão com o LLM

**Modo Ollama:**
```bash
ollama serve                # inicia o serviço Ollama
ollama list                 # verifica os modelos instalados
ollama pull qwen2.5:3b      # instala o modelo ausente
```

Causas comuns: Ollama não iniciado, modelo não instalado, memória de GPU insuficiente

**Modo GLM:**
- Confirme que `GLM_API_KEY` está correto
- Confirme que `GLM_EMBEDDING_DIMENSIONS=768` (deve coincidir com o índice vetorial do Neo4j)
- Endpoint da API GLM: `https://open.bigmodel.cn/api/paas/v4/`

**Modo GROQ:**
- Confirme que `GROQ_API_KEY` está correto
- Quando o Rate Limit for frequente, considere mudar para o modo GLM
- O GROQ não fornece Embedding, portanto garanta que o embedder do Ollama esteja disponível

**Modo OpenRouter:**
- Confirme que `OPENROUTER_API_KEY` está correto e que `OPENROUTER_MODEL` é um ID de modelo válido (ver https://openrouter.ai/models)
- Não fornece Embedding, portanto garanta que o embedder do Ollama esteja disponível

**Modo DeepSeek:**
- Confirme que `DEEPSEEK_API_KEY` está correto
- Se aparecer `Prompt must contain the word 'json'`: este é um requisito rígido do modo `json_object` do DeepSeek; o cliente já possui proteção de reserva integrada; se ainda assim ocorrer, confirme que está usando a versão mais recente de `src/deepseek_client.py` e reinicie o serviço
- Não fornece Embedding, portanto garanta que o embedder do Ollama esteja disponível

### Erro de conexão MCP

Se aparecer `Invalid request parameters` ou `Received request before initialization was complete`:

1. Confirme que está usando o modo de transporte HTTP (**não use SSE**)
2. Confirme que o cliente está configurado como `"type": "http"`, `"url": "http://localhost:8000/mcp"`
3. Reinicie o serviço: `pm2 restart graphiti-mcp-http --update-env`
4. Execute `/mcp` no Claude Code para reconectar

### Adição de memória lenta

- **Ollama**: verifique o tamanho do modelo (`qwen2.5:3b` é 5-10 vezes mais rápido que `7b`), confirme o uso de GPU (`ollama ps`)
- **GLM**: cada add_episode requer mais de 10-20 idas e voltas de rede ao LLM; ~22s para texto curto é um valor normal
- **GROQ**: o Rate Limit causa muitas retentativas; em caso de uso frequente, recomenda-se mudar para GLM ou Ollama
- Use `background=true` para evitar bloqueio
- Reduza `GRAPHITI_CHUNK_THRESHOLD` para que textos longos sejam segmentados mais cedo

### Problemas com o PM2

```bash
pm2 status                                        # verifica o status
pm2 logs graphiti-mcp-http --err --lines 50        # logs de erro
lsof -i :8000                                     # verifica a ocupação da porta
pm2 delete graphiti-mcp-http && pm2 start ecosystem.config.cjs  # reinício completo
```

## Ferramentas de diagnóstico de desenvolvimento

```bash
uv run python tools/status_report.py           # relatório consolidado de status (Neo4j + Ollama + configuração)
uv run python tools/validate_config.py         # valida a integridade do .env e da configuração
uv run python tools/performance_diagnose.py    # diagnóstico de desempenho do LLM
uv run python tools/inspect_schema.py          # verificação de índices e restrições do Neo4j
uv run python tools/migrate_embeddings.py      # migração do modelo de Embedding (regenera os vetores após trocar de modelo)
```

### Migração do modelo de Embedding

Após trocar o modelo de embedding (ex.: `nomic-embed-text` → `bge-m3`), é possível usar a ferramenta de migração para regenerar todos os vetores existentes, garantindo qualidade de busca consistente:

```bash
# Visualiza a quantidade a ser migrada
uv run python tools/migrate_embeddings.py --dry-run

# Migração completa (suporta retomada de ponto de interrupção)
uv run python tools/migrate_embeddings.py

# Migra apenas um group específico
uv run python tools/migrate_embeddings.py --group-id myproject

# Continua a partir do ponto de interrupção (reexecutar após interrupção)
uv run python tools/migrate_embeddings.py --resume
```

> **Compatibilidade**: o `bge-m3` é nativamente de 1024 dimensões; o sistema o trunca automaticamente para 768 dimensões para ser compatível com o índice vetorial existente do Neo4j. Os dados de antes e depois da migração podem coexistir, mas recomenda-se executar a migração completa para obter a melhor qualidade de busca.

## Documentação

- [Instruções de uso das ferramentas](../使用工具的指令.md) — guia de uso das ferramentas MCP e melhores práticas
- [Graphiti Memory Rules](../graphiti-memory-rules.md) — explicação das regras de memória

## Licença

MIT License
