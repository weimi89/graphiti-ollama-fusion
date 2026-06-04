# Graphiti MCP Server

Servicio de memoria con grafo de conocimiento — un servidor MCP que integra múltiples proveedores de LLM (Ollama / GLM / GROQ / OpenRouter / DeepSeek) con la base de datos de grafos Neo4j.

Desarrollado como una ampliación basada en [getzep/graphiti](https://github.com/getzep/graphiti), admite el cambio flexible entre Ollama local y LLM en la nube, y permite especificar de forma independiente el proveedor de Embedding (desacoplado del LLM).

## Características

- **Gestión inteligente de memoria** — utiliza un grafo de conocimiento para almacenar y recuperar relaciones de memoria complejas
- **Búsqueda semántica** — búsqueda híbrida basada en embeddings vectoriales (vector + palabra clave + recorrido del grafo)
- **16 estrategias de búsqueda** — la búsqueda avanzada admite múltiples métodos de reordenamiento como RRF, MMR, Cross-Encoder, etc.
- **Múltiples proveedores de LLM** — admite Ollama (local), GLM (Zhipu AI gratuito), GROQ (inferencia de alta velocidad), OpenRouter (agregador de varios modelos), DeepSeek (DeepSeek), con cambio mediante una sola variable de entorno
- **Embedding desacoplado del LLM** — se puede especificar el embedder de forma independiente con `EMBEDDING_PROVIDER`; los LLM en la nube recurren automáticamente al `bge-m3` local
- **Enrutamiento de doble modelo** — en modo Ollama, las tareas complejas usan el modelo principal y las tareas simples cambian automáticamente a un modelo pequeño para mejorar el rendimiento
- **División inteligente de contenido** — los textos largos se procesan dividiéndolos en segmentos automáticamente, reduciendo la carga del LLM (umbral configurable)
- **Procesamiento de memoria en segundo plano** — la adición de memoria puede ejecutarse en segundo plano y la llamada MCP retorna de inmediato
- **Deduplicación de memoria** — detecta automáticamente memorias existentes altamente similares, evitando el almacenamiento duplicado
- **Detección de conflictos** — detecta hechos contradictorios entre dos entidades, identificando la información ya invalidada y la vigente
- **Detección de comunidades** — agrupa automáticamente entidades relacionadas basándose en el algoritmo de Label Propagation
- **Seguimiento de importancia** — registra automáticamente la frecuencia de acceso de las entidades; los resultados de búsqueda se ordenan según su importancia
- **Olvido inteligente** — identifica y limpia memorias obsoletas y de bajo acceso, manteniendo el grafo conciso
- **Importación masiva** — envía múltiples memorias de una vez, ideal para migraciones de grandes volúmenes de datos
- **Tripletas estructuradas** — añade directamente «sujeto-relación-objeto», omitiendo la extracción del LLM y completándose en segundos
- **Interfaz de administración Web** — panel de control, navegación, búsqueda, visualización del grafo de conocimiento, preguntas y respuestas con IA y exploración de comunidades integrados
- **Internacionalización (i18n)** — los mensajes de respuesta admiten más de 30 locales (incluidos zh-TW / en / zh-CN / ja / pt-BR / ko / es / de / fr, etc.); las herramientas MCP siguen `SERVER_LANG` y la REST API negocia automáticamente según el `Accept-Language` HTTP
- **Tema oscuro/claro** — la interfaz Web admite el cambio de tema
- **Modo seguro** — adición rápida de memoria que opcionalmente omite la extracción de entidades
- **Soporte para Docker** — incluye un Dockerfile integrado, compatible con el despliegue en contenedores
- **Seguridad en concurrencia** — asyncio.Lock protege la inicialización, previniendo condiciones de carrera
- **Comprobación de salud por capas** — `/health` (liveness) + `/health/ready` (readiness)

## Requisitos del sistema

| Elemento | Requisito |
|------|------|
| Python | 3.10+ (se recomienda 3.11+) |
| Neo4j | 4.0+ (`bolt://localhost:7687`) |
| Proveedor de LLM | Ollama / GLM / GROQ / OpenRouter / DeepSeek (uno de los cinco) |
| Node.js | 18+ (solo para la ejecución en segundo plano con PM2, opcional) |
| Espacio en disco | ~3GB (modelos de Ollama + datos de Neo4j) |

### Selección del proveedor de LLM

Se cambia mediante la variable de entorno `LLM_PROVIDER` (`ollama` / `glm` / `groq` / `openrouter` / `deepseek`):

| Proveedor | Características | Modelo de LLM | Embedding | Escenario adecuado |
|--------|------|----------|-----------|----------|
| **Ollama** (predeterminado) | Totalmente local, los datos no salen de la máquina | `qwen2.5:3b` | `bge-m3` (excelente en chino + RAG) | Con GPU, prioriza la privacidad |
| **GLM** | Nube gratuita, estable y sin límite de tasa | `glm-4-flash` (gratuito) | `embedding-3` | Sin GPU, escenarios con búsquedas intensivas |
| **GROQ** | Inferencia de altísima velocidad | `llama-3.3-70b-versatile` | Recurre a Ollama `bge-m3` | Escrituras ocasionales, busca calidad |
| **OpenRouter** | Agrega varios modelos, incluye cuota gratuita | `stepfun/step-3.5-flash:free`, etc. | Recurre a Ollama `bge-m3` | Quiere usar un modelo en la nube específico |
| **DeepSeek** | Nube de DeepSeek, buena relación calidad-precio | `deepseek-v4-flash` / `deepseek-v4-pro` | Recurre a Ollama `bge-m3` | Comprensión del chino, nube de bajo costo |

> **Embedding desacoplado del LLM**: el embedder se especifica de forma independiente mediante `EMBEDDING_PROVIDER` (`ollama` / `glm`); si no se configura, sigue a `LLM_PROVIDER`. En la práctica, solo `glm` usa GLM `embedding-3`; el resto (incluidos los LLM en la nube que no proporcionan Embedding como GROQ / OpenRouter / DeepSeek) usan siempre Ollama `bge-m3` automáticamente. **Por lo tanto, al usar cualquier LLM en la nube, sigue siendo necesario que Ollama local proporcione el servicio de embedding (a menos que el embedding también esté configurado como glm).**

#### Modo Ollama (local)

```bash
# Modelo principal de LLM (se recomienda qwen2.5:3b, mejor equilibrio entre velocidad y estabilidad)
ollama pull qwen2.5:3b

# Modelo de embedding (obligatorio, para la búsqueda vectorial)
ollama pull bge-m3
```

> **Consideraciones sobre la selección del modelo**:
> - `qwen2.5:3b` — recomendado, ~2s/llamada, ~100 t/s, salida estructurada de graphiti-core 100% estable
> - `qwen2.5:7b` — mejor resultado pero 5-10 veces más lento, adecuado para escenarios que buscan calidad
> - `qwen2.5:1.5b` — el más rápido pero **inestable** (la tasa de éxito de JSON estructurado es solo del 33%), no se recomienda su uso

#### Modo GLM (nube de Zhipu AI)

```bash
# Configuración de .env
LLM_PROVIDER=glm
GLM_API_KEY=your_api_key          # Obtenerla de https://open.bigmodel.cn
GLM_MODEL=glm-4-flash             # Modelo gratuito
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768      # Debe coincidir con la dimensión del índice vectorial de Neo4j
```

> **Referencia de rendimiento de GLM**: escritura ~22s (texto corto), búsqueda ~0.34s, cero errores de Rate Limit, 2-5 veces más lento que Ollama local pero completamente gratuito.

#### Modo GROQ (inferencia de alta velocidad)

```bash
# Configuración de .env
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key         # Obtenerla de https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile
```

> **Nota**: GROQ no proporciona servicio de Embedding, por lo que debe combinarse con el embedder de Ollama (recurso automático) o configurar `EMBEDDING_PROVIDER` como glm. GROQ tiene un Rate Limit estricto; el uso de alta frecuencia provocará numerosos reintentos.

#### Modo OpenRouter (agregador de varios modelos)

```bash
# Configuración de .env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_api_key       # Obtenerla de https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free   # Se puede cambiar a cualquier modelo de OpenRouter
```

> **Nota**: OpenRouter no proporciona Embedding y recurre automáticamente a Ollama `bge-m3`. La lista de modelos está en https://openrouter.ai/models (incluye varios modelos gratuitos `:free`).

#### Modo DeepSeek (DeepSeek)

```bash
# Configuración de .env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key         # Obtenerla de https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash      # Recomendado; o deepseek-v4-pro (mejor resultado)
```

> **Nota**: DeepSeek no proporciona Embedding y recurre automáticamente a Ollama `bge-m3`. `deepseek-chat` / `deepseek-reasoner` se retirarán el 2026-07-24, se recomienda cambiar a `deepseek-v4-flash` / `deepseek-v4-pro`. DeepSeek exige estrictamente que el prompt del modo `json_object` contenga la cadena "json"; el cliente ya incluye una protección de respaldo integrada, sin necesidad de configuración adicional.

## Inicio rápido

### 1. Preparación previa

Confirma que Neo4j ya esté en ejecución en la máquina local y prepara el servicio correspondiente según el proveedor de LLM elegido:

```bash
# Confirmar que Neo4j está en ejecución (obligatorio)
neo4j status
# O usar Docker: docker run -d -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/your_password neo4j:latest

# Modo Ollama: confirmar que Ollama está en ejecución
ollama list
# Si no está iniciado: ollama serve

# Modo GLM / GROQ: solo se necesita una API Key válida, sin servicio local
```

### 2. Instalar dependencias

```bash
git clone <repo-url>
cd graphiti
uv sync
```

> **Nota**: Este proyecto usa [uv](https://github.com/astral-sh/uv) para gestionar las dependencias. Si no está instalado: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 3. Configurar el entorno

```bash
cp .env.example .env
```

Edita `.env`, necesitas modificar **al menos** los siguientes elementos:

```bash
NEO4J_PASSWORD=your_actual_password  # Obligatorio: contraseña de Neo4j
LLM_PROVIDER=ollama                  # ollama / glm / groq / openrouter / deepseek
OLLAMA_MODEL=qwen2.5:3b              # Modo Ollama: modelo de LLM local
# GLM_API_KEY=your_key               # Modo GLM: API Key de Zhipu AI
# GROQ_API_KEY=your_key              # Modo GROQ: API Key de GROQ
# OPENROUTER_API_KEY=your_key        # Modo OpenRouter: API Key
# DEEPSEEK_API_KEY=your_key          # Modo DeepSeek: API Key
```

### 4. Iniciar el servicio

```bash
# Modo HTTP (recomendado, incluye la interfaz de administración Web)
uv run python graphiti_mcp_server.py --transport http --port 8000

# O usar PM2 para la ejecución en segundo plano (recomendado para ejecución prolongada)
pm2 start ecosystem.config.cjs
```

### 5. Verificar el servicio

Tras el inicio, puedes acceder a los siguientes endpoints:

| Endpoint | Descripción |
|------|------|
| http://localhost:8000/ | Interfaz de administración Web |
| http://localhost:8000/mcp | Endpoint MCP (para que se conecten los clientes MCP) |
| http://localhost:8000/health | Comprobación de salud (liveness) |
| http://localhost:8000/health/ready | Comprobación profunda (incluye la conexión a Neo4j) |
| http://localhost:8000/api/stats | Estadísticas de la REST API |

## Estructura del proyecto

```
graphiti/
├── graphiti_mcp_server.py        # Punto de entrada principal — definición de herramientas MCP (19 herramientas)
├── src/
│   ├── config.py                 # Gestión de configuración (GraphitiConfig, admite superposición JSON/.env)
│   ├── web_api.py                # REST API de la interfaz de administración Web (20+ endpoints)
│   ├── ollama_graphiti_client.py  # Cliente LLM de Ollama (enrutamiento de doble modelo)
│   ├── glm_client.py             # Cliente LLM de GLM (Zhipu AI) (API compatible con OpenAI)
│   ├── openrouter_client.py      # Cliente LLM de OpenRouter (agregador de varios modelos)
│   ├── deepseek_client.py        # Cliente LLM de DeepSeek (json_object + protección de respaldo json)
│   ├── ollama_embedder.py        # Adaptador del modelo de embedding de Ollama
│   ├── content_preprocessor.py   # División inteligente de contenido (segmentación automática de textos largos)
│   ├── deduplication.py          # Deduplicación de memoria (comparación por similitud del coseno)
│   ├── importance.py             # Seguimiento de importancia y olvido inteligente
│   ├── safe_memory_add.py        # Adición segura de memoria (omite la extracción de entidades)
│   ├── timezone_utils.py         # Conversión de zona horaria (UTC→visualización en zona horaria local)
│   ├── i18n.py                   # Internacionalización del backend (REST según Accept-Language, MCP según SERVER_LANG)
│   ├── exceptions.py             # Manejo estructurado de excepciones (12 clases de excepciones)
│   └── logging_setup.py          # Sistema de registro (rotación temporal + monitoreo de rendimiento)
├── web/                          # Frontend de la interfaz de administración Web (SPA, sin build)
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js                # Encapsulación de la REST API
│       ├── components.js         # Renderizado de componentes de UI (incluye la página de comunidades)
│       └── app.js                # Enrutamiento SPA, gestión de estado
├── tests/                        # Suite de pruebas (183 pruebas)
│   ├── test_content_preprocessor.py  # Pruebas de la lógica de división (17 pruebas)
│   ├── test_new_features.py      # Pruebas de nuevas funciones (32 pruebas)
│   ├── test_i18n.py             # Pruebas de internacionalización (37 pruebas)
│   ├── test_unit.py              # Pruebas unitarias
│   ├── test_web_api.py           # Pruebas de la Web API
│   ├── test_web_ui_features.py   # Pruebas de funciones de la Web UI
│   ├── test_integration_manual.py # Pruebas de integración manuales
│   └── bench_deepseek_flash_vs_pro.py # Script de referencia de rendimiento de DeepSeek flash/pro
├── tools/                        # Herramientas de diagnóstico de desarrollo
│   ├── status_report.py          # Informe de estado consolidado
│   ├── validate_config.py        # Validación de configuración
│   ├── performance_diagnose.py   # Diagnóstico de rendimiento
│   ├── inspect_schema.py         # Inspección de la estructura de Neo4j
│   └── batch_reprocess.py        # Reprocesamiento por lotes
├── docs/                         # Documentación
├── logs/                         # Registros (rotación temporal, se conservan 30 días por defecto)
├── Dockerfile                    # Despliegue en contenedor Docker
└── ecosystem.config.cjs          # Configuración de PM2
```

## Configuración del cliente MCP

### Modo HTTP (recomendado)

Adecuado para clientes MCP que admiten HTTP como Claude Code, Cline, etc.:

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

Adecuado para clientes que necesitan iniciar el proceso directamente, como Claude Desktop:

**Ubicación del archivo de configuración:**
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

> **Nota**: El modo SSE (`--transport sse`) ya no se recomienda. MCP 1.x tiene problemas de compatibilidad con la inicialización de sesiones; usa el modo HTTP en su lugar.

## Herramientas MCP (19 herramientas)

### Gestión de memoria (7 herramientas)

| Herramienta | Descripción |
|------|------|
| `add_memory_simple` | Añadir memoria al grafo de conocimiento (admite procesamiento en segundo plano, división inteligente, comprobación de deduplicación) |
| `add_episode_bulk` | Añadir múltiples memorias por lotes (procesamiento en segundo plano por defecto) |
| `add_triplet` | Adición de tripletas estructuradas (omite el LLM, se completa en segundos) |
| `search_memory_nodes` | Buscar nodos de memoria (admite 16 estrategias de búsqueda, filtrado temporal) |
| `search_memory_facts` | Buscar hechos de memoria (admite filtrado por tipo de relación, rango temporal, filtrado por validez) |
| `advanced_search` | Búsqueda avanzada (16 estrategias, retorna nodos+aristas+comunidades+fragmentos) |
| `get_episodes` | Obtener los fragmentos de memoria más recientes |

### Análisis de conocimiento (3 herramientas)

| Herramienta | Descripción |
|------|------|
| `check_conflicts` | Detectar conflictos de hechos entre dos entidades (vigente vs invalidado) |
| `get_node_edges` | Explorar las relaciones de aristas entrantes y salientes de un nodo |
| `build_communities` | Activar la detección y agrupación de comunidades (procesamiento en segundo plano por defecto) |

### Mantenimiento de memoria (2 herramientas)

| Herramienta | Descripción |
|------|------|
| `get_stale_memories` | Consultar memorias obsoletas y de bajo acceso |
| `cleanup_stale_memories` | Limpiar memorias obsoletas (modo de vista previa dry_run por defecto) |

### Gestión de tareas

| Herramienta | Descripción |
|------|------|
| `get_memory_task_status` | Consultar el progreso y el resultado de las tareas de procesamiento de memoria en segundo plano |

### Eliminación y consulta

| Herramienta | Descripción |
|------|------|
| `delete_episode` | Eliminar un fragmento de memoria |
| `delete_entity_edge` | Eliminar una arista de entidad (relación) |
| `get_entity_edge` | Obtener información detallada de una arista de entidad |

### Administración del sistema

| Herramienta | Descripción |
|------|------|
| `get_status` | Obtener el estado del servicio (Neo4j, LLM, embedder) |
| `test_connection` | Probar la conexión a Neo4j / LLM / embedder |
| `clear_graph` | Limpiar la base de datos de grafos (admite limpieza por group_id) |

## Parámetros de las herramientas

### add_memory_simple

| Parámetro | Tipo | Obligatorio | Valor predeterminado | Descripción |
|------|------|------|--------|------|
| `name` | string | Y | | Nombre de la memoria |
| `episode_body` | string | Y | | Contenido de la memoria (se divide automáticamente si supera los 800 caracteres) |
| `group_id` | string | | `"default"` | ID de grupo (se recomienda aislar por proyecto) |
| `source` | string | | `"text"` | Tipo de origen: `text` / `json` / `message` |
| `source_description` | string | | `"MCP Server"` | Descripción del origen |
| `use_safe_mode` | bool | | `false` | Modo seguro (omite la extracción de entidades, rápido pero la memoria no es buscable) |
| `background` | bool | | `false` | Procesamiento en segundo plano (retorna task_id de inmediato, adecuado para textos largos) |
| `force` | bool | | `false` | Omitir la comprobación de deduplicación (adición forzada) |
| `excluded_entity_types` | list | | | Tipos de entidad excluidos (reduce la cantidad de extracción innecesaria) |

> **Consejos de rendimiento**:
> - Texto corto (<800 caracteres): procesamiento directo, normalmente se completa en 30-40 segundos
> - Texto largo (>800 caracteres): se divide automáticamente en varios segmentos, usando `add_episode_bulk` para procesamiento concurrente (~33% más rápido que en serie)
> - Usar `background=true` evita el bloqueo de la llamada MCP; sigue el progreso mediante `get_memory_task_status`
> - `use_safe_mode=true` se completa en segundos pero la memoria no puede ser encontrada por las herramientas de búsqueda
> - Con la deduplicación habilitada, las memorias altamente similares serán advertidas (`force=true` permite omitirlo)

### add_episode_bulk

| Parámetro | Tipo | Obligatorio | Valor predeterminado | Descripción |
|------|------|------|--------|------|
| `episodes` | list | Y | | Lista de memorias, cada elemento contiene `name` y `content` |
| `group_id` | string | | `"default"` | ID de grupo |
| `source` | string | | `"text"` | Tipo de origen |
| `background` | bool | | `true` | Procesamiento en segundo plano (los lotes suelen tardar) |

### add_triplet

| Parámetro | Tipo | Obligatorio | Valor predeterminado | Descripción |
|------|------|------|--------|------|
| `source_name` | string | Y | | Nombre de la entidad de origen (p. ej. "Alice") |
| `target_name` | string | Y | | Nombre de la entidad de destino (p. ej. "Google") |
| `relation_name` | string | Y | | Nombre de la relación (p. ej. "works_at") |
| `fact` | string | Y | | Descripción del hecho (p. ej. "Alice works at Google") |
| `group_id` | string | | `"default"` | ID de grupo |
| `source_labels` | list | | | Etiquetas de la entidad de origen |
| `target_labels` | list | | | Etiquetas de la entidad de destino |

### search_memory_nodes

| Parámetro | Tipo | Obligatorio | Valor predeterminado | Descripción |
|------|------|------|--------|------|
| `query` | string | Y | | Palabra clave de búsqueda (lenguaje natural) |
| `max_nodes` | int | | `10` | Cantidad máxima a retornar |
| `group_ids` | list | | | Filtrado por grupo (búsqueda conjunta de varios grupos) |
| `entity_types` | list | | | Filtrado por tipo de entidad |
| `search_recipe` | string | | | Estrategia de búsqueda (ver búsqueda avanzada) |
| `created_after` | string | | | Límite inferior de tiempo de creación (ISO datetime) |
| `created_before` | string | | | Límite superior de tiempo de creación (ISO datetime) |

### search_memory_facts

| Parámetro | Tipo | Obligatorio | Valor predeterminado | Descripción |
|------|------|------|--------|------|
| `query` | string | Y | | Palabra clave de búsqueda |
| `max_facts` | int | | `10` | Cantidad máxima a retornar |
| `group_ids` | list | | | Filtrado por grupo |
| `center_node_uuid` | string | | | UUID del nodo central (explorar las relaciones de un nodo específico) |
| `edge_types` | list | | | Filtrado por tipo de relación (p. ej. `["works_at"]`) |
| `created_after` | string | | | Límite inferior de tiempo de creación (ISO datetime) |
| `created_before` | string | | | Límite superior de tiempo de creación (ISO datetime) |
| `only_valid` | bool | | `false` | Retornar solo los hechos no invalidados |

### advanced_search

| Parámetro | Tipo | Obligatorio | Valor predeterminado | Descripción |
|------|------|------|--------|------|
| `query` | string | Y | | Palabra clave de búsqueda |
| `search_recipe` | string | | `"combined_rrf"` | Estrategia de búsqueda (16 opciones) |
| `max_results` | int | | `10` | Cantidad máxima a retornar |
| `group_ids` | list | | | Filtrado por grupo |
| `center_node_uuid` | string | | | UUID del nodo central |

**Estrategias de búsqueda disponibles (search_recipe):**

| Categoría | Estrategia | Descripción |
|------|------|------|
| Combinada | `combined_rrf` | Fusión RRF combinada (predeterminada, recomendada) |
| Combinada | `combined_mmr` | Reordenamiento por diversidad MMR combinado |
| Combinada | `combined_cross_encoder` | Reordenamiento fino Cross-Encoder combinado |
| Arista | `edge_rrf` / `edge_mmr` / `edge_cross_encoder` | Búsqueda de aristas (3 ordenamientos) |
| Arista | `edge_node_distance` / `edge_episode_mentions` | Búsqueda de aristas (distancia en el grafo/número de menciones) |
| Nodo | `node_rrf` / `node_mmr` / `node_cross_encoder` | Búsqueda de nodos (3 ordenamientos) |
| Nodo | `node_node_distance` / `node_episode_mentions` | Búsqueda de nodos (distancia en el grafo/número de menciones) |
| Comunidad | `community_rrf` / `community_mmr` / `community_cross_encoder` | Búsqueda de comunidades |

### check_conflicts

| Parámetro | Tipo | Obligatorio | Valor predeterminado | Descripción |
|------|------|------|--------|------|
| `source_name` | string | Y | | Nombre de la entidad de origen |
| `target_name` | string | Y | | Nombre de la entidad de destino |
| `group_id` | string | | `"default"` | ID de grupo |

### get_node_edges

| Parámetro | Tipo | Obligatorio | Valor predeterminado | Descripción |
|------|------|------|--------|------|
| `node_uuid` | string | Y | | UUID del nodo |
| `include_inbound` | bool | | `true` | Incluir aristas entrantes |
| `include_outbound` | bool | | `true` | Incluir aristas salientes |
| `max_edges` | int | | `50` | Cantidad máxima a retornar |

### build_communities

| Parámetro | Tipo | Obligatorio | Valor predeterminado | Descripción |
|------|------|------|--------|------|
| `group_ids` | list | | | Grupos especificados (vacío para todos) |
| `background` | bool | | `true` | Procesamiento en segundo plano |

### get_stale_memories

| Parámetro | Tipo | Obligatorio | Valor predeterminado | Descripción |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Cuántos días sin acceso se considera obsoleto |
| `min_access_count` | int | | `2` | Solo se incluye si el número de accesos es inferior a este valor |
| `group_id` | string | | | Filtrado por grupo |
| `limit` | int | | `50` | Cantidad máxima a retornar |

### cleanup_stale_memories

| Parámetro | Tipo | Obligatorio | Valor predeterminado | Descripción |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Umbral de días de obsolescencia |
| `min_access_count` | int | | `2` | Umbral mínimo de número de accesos |
| `group_id` | string | | | Filtrado por grupo |
| `dry_run` | bool | | `true` | Modo de vista previa (no elimina realmente) |
| `limit` | int | | `50` | Cantidad máxima a procesar |

### get_memory_task_status

| Parámetro | Tipo | Obligatorio | Descripción |
|------|------|------|------|
| `task_id` | string | Y | ID de la tarea en segundo plano (retornado por `add_memory_simple(background=true)`) |

## Interfaz de administración Web

En modo HTTP, accede a `http://localhost:8000/` para usarla.

**Funciones:**
- Panel de control — estadísticas del número de nodos, hechos y fragmentos de memoria
- Nodos de entidad — navegación, filtrado, búsqueda vectorial
- Relaciones de hechos — navegación, filtrado, búsqueda vectorial
- Fragmentos de memoria — navegación, búsqueda de texto completo, eliminación
- Exploración de comunidades — lista de nodos de comunidad, resumen, activación de la construcción de comunidades
- Formulario de tripletas — añadir directamente conocimiento estructurado «sujeto-relación-objeto»
- Gestión de grupos — filtrado por grupo, eliminación por lotes
- Visualización del grafo de conocimiento — presentación gráfica de las relaciones de nodos
- Preguntas y respuestas con IA — preguntas y respuestas inteligentes basadas en el grafo de conocimiento
- Análisis de calidad — análisis de la calidad y cobertura de la memoria
- Cambio de tema — tema oscuro/claro

**REST API:**

| Endpoint | Método | Descripción |
|------|------|------|
| `/api/stats` | GET | Estadísticas del panel de control |
| `/api/groups` | GET | Obtener todos los group_id |
| `/api/nodes` | GET | Navegar por los nodos de entidad (paginado) |
| `/api/facts` | GET | Navegar por los hechos (paginado) |
| `/api/episodes` | GET | Navegar por los fragmentos de memoria (paginado) |
| `/api/search/nodes` | GET | Búsqueda vectorial de nodos |
| `/api/search/facts` | GET | Búsqueda vectorial de hechos |
| `/api/search/advanced` | GET | Búsqueda avanzada (16 estrategias) |
| `/api/communities` | GET | Navegar por los nodos de comunidad (paginado) |
| `/api/communities/build` | POST | Activar la construcción de comunidades |
| `/api/memory/add-bulk` | POST | Añadir memorias por lotes |
| `/api/memory/add-triplet` | POST | Añadir una tripleta |
| `/api/memory/tasks` | GET | Listar las tareas en segundo plano (admite filtrado por estado) |
| `/api/memory/tasks/{id}` | GET | Consultar el estado de una sola tarea |
| `/api/analytics/stale` | GET | Consultar memorias obsoletas |
| `/api/analytics/cleanup` | POST | Limpiar memorias obsoletas |
| `/api/nodes/{uuid}` | DELETE | Eliminar un nodo |
| `/api/episodes/{uuid}` | DELETE | Eliminar un fragmento de memoria |
| `/api/facts/{uuid}` | DELETE | Eliminar un hecho |
| `/api/groups/{group_id}` | DELETE | Eliminar un grupo completo |

## Configuración

### Variables de entorno (.env)

La configuración usa un mecanismo de superposición: el archivo de configuración JSON como base, y las variables de entorno sobrescriben valores individuales.

```bash
# === Obligatorio ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password        # Debe modificarse

# === Selección del proveedor de LLM ===
LLM_PROVIDER=ollama                 # ollama / glm / groq / openrouter / deepseek

# === Proveedor de Embedding (opcional, sigue a LLM_PROVIDER por defecto) ===
# Solo glm usa GLM Embedding, el resto usa siempre Ollama bge-m3
# EMBEDDING_PROVIDER=ollama         # ollama / glm

# === Configuración de Ollama (se usa cuando LLM_PROVIDER=ollama) ===
OLLAMA_MODEL=qwen2.5:3b             # Modelo principal (se recomienda qwen2.5:3b)
OLLAMA_SMALL_MODEL=qwen2.5:3b       # Modelo pequeño (para tareas simples, puede ser un modelo distinto)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.1

# === Configuración de GLM (se usa cuando LLM_PROVIDER=glm) ===
GLM_API_KEY=your_api_key            # Obtenerla de https://open.bigmodel.cn
GLM_MODEL=glm-4-flash               # Modelo gratuito
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768

# === Configuración de GROQ (se usa cuando LLM_PROVIDER=groq) ===
GROQ_API_KEY=your_api_key           # Obtenerla de https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile

# === Configuración de OpenRouter (se usa cuando LLM_PROVIDER=openrouter) ===
OPENROUTER_API_KEY=your_api_key     # Obtenerla de https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free

# === Configuración de DeepSeek (se usa cuando LLM_PROVIDER=deepseek) ===
DEEPSEEK_API_KEY=your_api_key       # Obtenerla de https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash    # O deepseek-v4-pro

# === Modelo de embedding de Ollama (se usa siempre que el embedding no sea glm) ===
OLLAMA_EMBEDDING_MODEL=bge-m3
OLLAMA_EMBEDDING_DIMENSIONS=768

# === Visualización e idioma (opcional) ===
GRAPHITI_DISPLAY_TIMEZONE=Asia/Taipei # Zona horaria de visualización de las marcas de tiempo retornadas por la API (nombre IANA; el almacenamiento se mantiene en UTC)
SERVER_LANG=zh-TW                     # Idioma de respuesta de las herramientas MCP (locales completos en src/i18n.py); la REST API usa Accept-Language

# === Rendimiento de memoria (opcional) ===
GRAPHITI_CHUNK_THRESHOLD=800         # Umbral de número de caracteres que activa la división inteligente
GRAPHITI_MAX_CHUNK_SIZE=600          # Número máximo de caracteres por segmento
GRAPHITI_MAX_COROUTINES=10            # Número máximo de corrutinas concurrentes
GRAPHITI_DEFAULT_BACKGROUND=false    # Si se usa el procesamiento en segundo plano por defecto

# === Seguimiento de importancia y olvido inteligente (opcional) ===
ENABLE_IMPORTANCE_TRACKING=true      # Habilitar el seguimiento de acceso
IMPORTANCE_WEIGHT=0.1                # Peso de importancia
STALE_DAYS_THRESHOLD=30              # Umbral de días de obsolescencia
STALE_MIN_ACCESS_COUNT=2             # Número mínimo de accesos

# === Registro ===
LOG_FILE=logs/graphiti_mcp_server.log
LOG_LEVEL=INFO
```

> **Para la lista completa de variables de entorno**, consulta `.env.example`

### Archivo de configuración JSON

Adecuado para configuraciones que requieren control de versiones (las variables de entorno aún pueden sobrescribir):

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

## Ejecución en segundo plano con PM2

```bash
npm install -g pm2

pm2 start ecosystem.config.cjs      # Iniciar
pm2 status                           # Estado
pm2 logs graphiti-mcp-http           # Registros en tiempo real
pm2 restart graphiti-mcp-http --update-env  # Reiniciar (recarga .env)

pm2 save && pm2 startup              # Configurar el inicio automático al arrancar
```

> **Consejo**: Tras modificar `.env`, debes reiniciar usando el flag `--update-env`, de lo contrario las variables de entorno no se actualizarán.

## Despliegue con Docker

```bash
docker build -t graphiti-mcp .

# Nota: el contenedor Docker necesita poder conectarse a Neo4j y Ollama
# Usar host network es lo más sencillo
docker run -p 8000:8000 --env-file .env --network host graphiti-mcp

# O especificar explícitamente las direcciones de los servicios externos
docker run -p 8000:8000 \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --env-file .env graphiti-mcp
```

## Pruebas

```bash
# Ejecutar todas las pruebas (183, ~1 segundo)
uv run python -m pytest tests/

# Salida detallada
uv run python -m pytest tests/ -v

# Ejecutar solo una prueba específica
uv run python -m pytest tests/test_content_preprocessor.py -v
uv run python -m pytest tests/test_new_features.py -v
uv run python -m pytest tests/test_unit.py -v
```

> **Nota**: Las 3 pruebas async en `test_integration_manual.py` requieren la instalación de `pytest-asyncio`; al faltar, se mostrarán como Failed pero no afectan a las demás pruebas. `bench_deepseek_flash_vs_pro.py` es un script de referencia de rendimiento, no una prueba unitaria.

## Resolución de problemas

### Fallo de conexión a Neo4j

```bash
neo4j status                              # Comprobar el estado del servicio
cypher-shell -u neo4j -p your_password    # Confirmar que la contraseña es correcta
curl http://localhost:7474                 # Confirmar el puerto HTTP
```

Causas comunes:
- Neo4j no está iniciado
- Contraseña incorrecta (`NEO4J_PASSWORD` en `.env`)
- Puerto ocupado o bloqueado por el firewall

### Fallo de conexión al LLM

**Modo Ollama:**
```bash
ollama serve                # Iniciar el servicio Ollama
ollama list                 # Comprobar los modelos instalados
ollama pull qwen2.5:3b      # Instalar el modelo que falte
```

Causas comunes: Ollama no está iniciado, el modelo no está instalado, memoria de GPU insuficiente

**Modo GLM:**
- Confirmar que `GLM_API_KEY` es correcta
- Confirmar `GLM_EMBEDDING_DIMENSIONS=768` (debe coincidir con el índice vectorial de Neo4j)
- Endpoint de la API de GLM: `https://open.bigmodel.cn/api/paas/v4/`

**Modo GROQ:**
- Confirmar que `GROQ_API_KEY` es correcta
- Si el Rate Limit es frecuente, considera cambiar al modo GLM
- GROQ no proporciona Embedding, asegúrate de que el embedder de Ollama esté disponible

**Modo OpenRouter:**
- Confirmar que `OPENROUTER_API_KEY` es correcta y que `OPENROUTER_MODEL` es un ID de modelo válido (ver https://openrouter.ai/models)
- No proporciona Embedding, asegúrate de que el embedder de Ollama esté disponible

**Modo DeepSeek:**
- Confirmar que `DEEPSEEK_API_KEY` es correcta
- Si aparece `Prompt must contain the word 'json'`: este es un requisito estricto del modo `json_object` de DeepSeek; el cliente ya incluye una protección de respaldo integrada; si aún aparece, confirma que estás usando la versión más reciente de `src/deepseek_client.py` y reinicia el servicio
- No proporciona Embedding, asegúrate de que el embedder de Ollama esté disponible

### Error de conexión MCP

Si aparece `Invalid request parameters` o `Received request before initialization was complete`:

1. Confirma que usas el modo de transporte HTTP (**no uses SSE**)
2. Confirma que el cliente está configurado como `"type": "http"`, `"url": "http://localhost:8000/mcp"`
3. Reinicia el servicio: `pm2 restart graphiti-mcp-http --update-env`
4. Ejecuta `/mcp` en Claude Code para reconectar

### Adición de memoria lenta

- **Ollama**: comprueba el tamaño del modelo (`qwen2.5:3b` es 5-10 veces más rápido que `7b`), confirma que se usa la GPU (`ollama ps`)
- **GLM**: cada add_episode necesita más de 10-20 viajes de red al LLM; ~22s para texto corto es un valor normal
- **GROQ**: el Rate Limit provoca numerosos reintentos; si el uso es frecuente, se recomienda cambiar a GLM u Ollama
- Usa `background=true` para evitar el bloqueo
- Reduce `GRAPHITI_CHUNK_THRESHOLD` para que los textos largos se dividan antes

### Problemas con PM2

```bash
pm2 status                                        # Comprobar el estado
pm2 logs graphiti-mcp-http --err --lines 50        # Registros de errores
lsof -i :8000                                     # Comprobar la ocupación del puerto
pm2 delete graphiti-mcp-http && pm2 start ecosystem.config.cjs  # Reinicio completo
```

## Herramientas de diagnóstico de desarrollo

```bash
uv run python tools/status_report.py           # Informe de estado consolidado (Neo4j + Ollama + configuración)
uv run python tools/validate_config.py         # Validar la integridad de .env y la configuración
uv run python tools/performance_diagnose.py    # Diagnóstico de rendimiento del LLM
uv run python tools/inspect_schema.py          # Inspección de índices y restricciones de Neo4j
uv run python tools/migrate_embeddings.py      # Migración del modelo de Embedding (regenera los vectores tras cambiar de modelo)
```

### Migración del modelo de Embedding

Tras cambiar el modelo de embedding (p. ej. `nomic-embed-text` → `bge-m3`), puedes usar la herramienta de migración para regenerar todos los vectores existentes, garantizando una calidad de búsqueda consistente:

```bash
# Previsualizar la cantidad que necesita migración
uv run python tools/migrate_embeddings.py --dry-run

# Migración completa (admite reanudación desde un punto de interrupción)
uv run python tools/migrate_embeddings.py

# Migrar solo un grupo específico
uv run python tools/migrate_embeddings.py --group-id myproject

# Continuar desde un punto de interrupción (volver a ejecutar tras una interrupción)
uv run python tools/migrate_embeddings.py --resume
```

> **Compatibilidad**: `bge-m3` es nativamente de 1024 dimensiones; el sistema lo trunca automáticamente a 768 dimensiones para ser compatible con el índice vectorial existente de Neo4j. Los datos anteriores y posteriores a la migración pueden coexistir, pero se recomienda ejecutar una migración completa para obtener la mejor calidad de búsqueda.

## Documentación

- [Instrucciones de uso de las herramientas](../使用工具的指令.md) — guía de uso de las herramientas MCP y mejores prácticas
- [Graphiti Memory Rules](../graphiti-memory-rules.md) — explicación de las reglas de memoria

## Licencia

MIT License
