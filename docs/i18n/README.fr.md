# Graphiti MCP Server

Service de mémoire à graphe de connaissances — un serveur MCP intégrant plusieurs fournisseurs de LLM (Ollama / GLM / GROQ / OpenRouter / DeepSeek) et la base de données à graphe Neo4j.

Développé comme une extension de [getzep/graphiti](https://github.com/getzep/graphiti), il prend en charge la commutation flexible entre Ollama local et les LLM cloud, et permet de spécifier indépendamment le fournisseur d'Embedding (découplé du LLM).

## Fonctionnalités

- **Gestion intelligente de la mémoire** — Stocke et récupère des relations de mémoire complexes à l'aide d'un graphe de connaissances
- **Recherche sémantique** — Recherche hybride basée sur les vecteurs d'embedding (vecteur + mot-clé + parcours de graphe)
- **16 stratégies de recherche** — La recherche avancée prend en charge plusieurs méthodes de reclassement telles que RRF, MMR, Cross-Encoder, etc.
- **Plusieurs fournisseurs de LLM** — Prend en charge Ollama (local), GLM (Zhipu AI, gratuit), GROQ (inférence haute vitesse), OpenRouter (agrégation de modèles de divers fournisseurs), DeepSeek, avec commutation par variable d'environnement
- **Découplage de l'Embedding et du LLM** — Vous pouvez spécifier l'embedder indépendamment avec `EMBEDDING_PROVIDER` ; les LLM cloud se replient automatiquement sur le `bge-m3` local
- **Répartition entre deux modèles** — En mode Ollama, les tâches complexes utilisent le modèle principal et les tâches simples basculent automatiquement vers un petit modèle pour améliorer les performances
- **Découpage intelligent du contenu** — Les textes longs sont automatiquement segmentés pour réduire la charge du LLM (seuil configurable)
- **Traitement de la mémoire en arrière-plan** — L'ajout de mémoire peut s'exécuter en arrière-plan, et l'appel MCP retourne immédiatement ; l'état des tâches est persisté dans SQLite et les tâches inachevées sont automatiquement restaurées après redémarrage
- **Déduplication de la mémoire** — Détecte automatiquement les mémoires existantes très similaires pour éviter les stockages redondants
- **Détection de conflits** — Détecte les faits contradictoires entre deux entités et identifie les informations devenues invalides et valides
- **Détection de communautés** — Regroupe automatiquement les entités liées à l'aide de l'algorithme de propagation d'étiquettes (Label Propagation)
- **Suivi de l'importance** — Enregistre automatiquement la fréquence d'accès aux entités, les résultats de recherche étant triés par importance
- **Oubli intelligent** — Identifie et nettoie les mémoires obsolètes à faible taux d'accès pour garder le graphe concis
- **Import en masse** — Soumet plusieurs mémoires en une fois, adapté aux migrations de grandes quantités de données
- **Triplets structurés** — Ajoute directement « sujet-relation-objet », en sautant l'extraction par LLM, pour un résultat instantané
- **Interface d'administration Web** — Tableau de bord intégré, navigation, recherche, visualisation du graphe de connaissances, questions-réponses par IA, navigation des communautés, maintenance de la qualité, import en masse, paramètres à l'exécution
- **Multilingue (i18n)** — Les messages de réponse prennent en charge 33 langues (dont zh-TW / en / zh-CN / ja / pt-BR / ko / es / de / fr, etc. ; zh-TW/en/zh-CN/ja écrits à la main, les autres fournis par la couche generated) ; les outils MCP suivent `SERVER_LANG`, et la REST API négocie automatiquement selon l'en-tête HTTP `Accept-Language`
- **Thème sombre/clair** — L'interface Web prend en charge le changement de thème
- **Mode sûr** — Ajout rapide de mémoire pouvant ignorer l'extraction d'entités
- **Prise en charge de Docker** — Dockerfile intégré, prenant en charge le déploiement conteneurisé
- **Sécurité de la concurrence** — asyncio.Lock protège l'initialisation pour prévenir les conditions de course
- **Vérifications de santé en couches** — `/health` (liveness) + `/health/ready` (readiness)

## Configuration requise

| Élément | Exigence |
|------|------|
| Python | 3.10+ (3.11+ recommandé) |
| Neo4j | 4.0+ (`bolt://localhost:7687`) |
| Fournisseur de LLM | Ollama / GLM / GROQ / OpenRouter / DeepSeek (un parmi cinq) |
| Node.js | 18+ (uniquement pour l'exécution en arrière-plan avec PM2, optionnel) |
| Espace disque | ~3 Go (modèles Ollama + données Neo4j) |

### Choix du fournisseur de LLM

Commutation via la variable d'environnement `LLM_PROVIDER` (`ollama` / `glm` / `groq` / `openrouter` / `deepseek`) :

| Fournisseur | Caractéristiques | Modèle LLM | Embedding | Scénario adapté |
|--------|------|----------|-----------|----------|
| **Ollama** (par défaut) | Entièrement local, les données ne quittent pas la machine | `qwen2.5:3b` | `bge-m3` (excellent en chinois + RAG) | Avec GPU, soucieux de la confidentialité |
| **GLM** | Cloud gratuit, stable et sans limitation de débit | `glm-4-flash` (gratuit) | `embedding-3` | Sans GPU, scénarios à forte densité de recherches |
| **GROQ** | Inférence ultra-rapide | `llama-3.3-70b-versatile` | Repli sur Ollama `bge-m3` | Écritures occasionnelles, recherche de qualité |
| **OpenRouter** | Agrégation de modèles de divers fournisseurs, avec quota gratuit | `stepfun/step-3.5-flash:free`, etc. | Repli sur Ollama `bge-m3` | Souhaite utiliser un modèle cloud spécifique |
| **DeepSeek** | Cloud de DeepSeek, excellent rapport qualité-prix | `deepseek-v4-flash` / `deepseek-v4-pro` | Repli sur Ollama `bge-m3` | Compréhension du chinois, cloud à faible coût |

> **Découplage de l'Embedding et du LLM** : l'embedder est spécifié indépendamment via `EMBEDDING_PROVIDER` (`ollama` / `glm`) ; lorsqu'il n'est pas défini, il suit `LLM_PROVIDER`. En pratique, seul `glm` utilise le GLM `embedding-3`, tous les autres (y compris les LLM cloud comme GROQ / OpenRouter / DeepSeek qui ne fournissent pas d'Embedding) utilisent automatiquement le `bge-m3` d'Ollama. **Par conséquent, lors de l'utilisation de tout LLM cloud, vous avez toujours besoin d'Ollama local pour fournir le service d'embedding (sauf si l'embedding est également défini sur glm).**

#### Mode Ollama (local)

```bash
# Modèle LLM principal (qwen2.5:3b recommandé, meilleur équilibre entre vitesse et stabilité)
ollama pull qwen2.5:3b

# Modèle d'embedding (obligatoire, utilisé pour la recherche vectorielle)
ollama pull bge-m3
```

> **Remarques sur le choix du modèle** :
> - `qwen2.5:3b` — recommandé, ~2 s/appel, ~100 t/s, sortie structurée graphiti-core stable à 100 %
> - `qwen2.5:7b` — meilleurs résultats mais 5 à 10 fois plus lent, adapté aux scénarios exigeant de la qualité
> - `qwen2.5:1.5b` — le plus rapide mais **instable** (taux de réussite du JSON structuré de seulement 33 %), déconseillé

#### Mode GLM (cloud Zhipu AI)

```bash
# Configuration .env
LLM_PROVIDER=glm
GLM_API_KEY=your_api_key          # à obtenir depuis https://open.bigmodel.cn
GLM_MODEL=glm-4-flash             # modèle gratuit
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768      # doit correspondre à la dimension de l'index vectoriel Neo4j
```

> **Référence de performance GLM** : écriture ~22 s (texte court), recherche ~0,34 s, zéro erreur de Rate Limit, 2 à 5 fois plus lent qu'Ollama local mais totalement gratuit.

#### Mode GROQ (inférence haute vitesse)

```bash
# Configuration .env
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key         # à obtenir depuis https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile
```

> **Remarque** : GROQ ne fournit pas de service d'Embedding ; il faut l'associer à l'embedder Ollama (repli automatique) ou définir `EMBEDDING_PROVIDER` sur glm. GROQ applique un Rate Limit strict ; une utilisation à haute fréquence déclenchera de nombreuses tentatives de réessai.

#### Mode OpenRouter (agrégation de modèles de divers fournisseurs)

```bash
# Configuration .env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_api_key       # à obtenir depuis https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free   # peut être remplacé par n'importe quel modèle OpenRouter
```

> **Remarque** : OpenRouter ne fournit pas d'Embedding et se replie automatiquement sur le `bge-m3` d'Ollama. La liste des modèles est disponible sur https://openrouter.ai/models (avec plusieurs modèles gratuits `:free`).

#### Mode DeepSeek (DeepSeek)

```bash
# Configuration .env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key         # à obtenir depuis https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash      # recommandé ; ou deepseek-v4-pro (meilleurs résultats)
```

> **Remarque** : DeepSeek ne fournit pas d'Embedding et se replie automatiquement sur le `bge-m3` d'Ollama. `deepseek-chat` / `deepseek-reasoner` seront retirés le 2026-07-24 ; il est recommandé de passer à `deepseek-v4-flash` / `deepseek-v4-pro`. DeepSeek exige strictement que le prompt du mode `json_object` contienne la chaîne « json » ; le client dispose d'une protection de secours intégrée, sans configuration supplémentaire nécessaire.

## Démarrage rapide

### 1. Préparation préalable

Vérifiez que Neo4j est en cours d'exécution sur la machine locale et préparez le service correspondant au fournisseur de LLM choisi :

```bash
# Vérifier que Neo4j est en cours d'exécution (obligatoire)
neo4j status
# Ou utiliser Docker : docker run -d -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/your_password neo4j:latest

# Mode Ollama : vérifier qu'Ollama est en cours d'exécution
ollama list
# S'il n'est pas démarré : ollama serve

# Mode GLM / GROQ : nécessite uniquement une clé API valide, aucun service local requis
```

### 2. Installer les dépendances

```bash
git clone <repo-url>
cd graphiti
uv sync
```

> **Remarque** : ce projet utilise [uv](https://github.com/astral-sh/uv) pour la gestion des dépendances. S'il n'est pas installé : `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 3. Configurer l'environnement

```bash
cp .env.example .env
```

Modifiez `.env` ; vous devez **au minimum** modifier les éléments suivants :

```bash
NEO4J_PASSWORD=your_actual_password  # obligatoire : mot de passe Neo4j
LLM_PROVIDER=ollama                  # ollama / glm / groq / openrouter / deepseek
OLLAMA_MODEL=qwen2.5:3b              # mode Ollama : modèle LLM local
# GLM_API_KEY=your_key               # mode GLM : clé API Zhipu AI
# GROQ_API_KEY=your_key              # mode GROQ : clé API GROQ
# OPENROUTER_API_KEY=your_key        # mode OpenRouter : clé API
# DEEPSEEK_API_KEY=your_key          # mode DeepSeek : clé API
```

### 4. Démarrer le service

```bash
# Mode HTTP (recommandé, inclut l'interface d'administration Web)
uv run python graphiti_mcp_server.py --transport http --port 8000

# Ou utiliser PM2 pour l'exécution en arrière-plan (recommandé pour un fonctionnement à long terme)
pm2 start ecosystem.config.cjs
```

### 5. Vérifier le service

Après le démarrage, vous pouvez accéder aux points de terminaison suivants :

| Point de terminaison | Description |
|------|------|
| http://localhost:8000/ | Interface d'administration Web |
| http://localhost:8000/mcp | Point de terminaison MCP (pour la connexion des clients MCP) |
| http://localhost:8000/health | Vérification de santé (liveness) |
| http://localhost:8000/health/ready | Vérification approfondie (incluant la connexion Neo4j) |
| http://localhost:8000/api/stats | Statistiques de la REST API |

## Structure du projet

```
graphiti/
├── graphiti_mcp_server.py        # Point d'entrée principal — définition des outils MCP (19 outils)
├── src/
│   ├── config.py                 # Gestion de la configuration (GraphitiConfig, prise en charge de la superposition JSON/.env)
│   ├── web_api.py                # REST API de l'interface d'administration Web (30+ points de terminaison)
│   ├── ollama_graphiti_client.py  # Client LLM Ollama (répartition entre deux modèles)
│   ├── openai_compat_client.py   # Classe de base LLM compatible OpenAI (json_object + schema simplifié + protection json de secours)
│   ├── glm_client.py             # Client LLM GLM (Zhipu AI) (hérite de OpenAICompatClient)
│   ├── openrouter_client.py      # Client LLM OpenRouter (hérite de OpenAICompatClient)
│   ├── deepseek_client.py        # Client LLM DeepSeek (hérite de OpenAICompatClient)
│   ├── ollama_embedder.py        # Adaptateur de modèle d'embedding Ollama
│   ├── content_preprocessor.py   # Découpage intelligent du contenu (segmentation automatique des textes longs)
│   ├── deduplication.py          # Déduplication de la mémoire (comparaison par similarité cosinus)
│   ├── importance.py             # Suivi de l'importance et oubli intelligent
│   ├── safe_memory_add.py        # Ajout sûr de mémoire (saut de l'extraction d'entités)
│   ├── task_store.py             # Persistance SQLite des tâches en arrière-plan (TaskStore)
│   ├── timezone_utils.py         # Conversion de fuseau horaire (affichage UTC→fuseau local)
│   ├── i18n.py                   # Multilingue backend (REST selon Accept-Language, MCP selon SERVER_LANG)
│   ├── i18n_generated.py         # Surcharges de langues générées automatiquement (GENERATED_MESSAGE_OVERRIDES)
│   ├── exceptions.py             # Gestion structurée des exceptions (12 catégories d'exceptions)
│   └── logging_setup.py          # Système de journalisation (rotation temporelle + surveillance des performances)
├── web/                          # Frontend de l'interface d'administration Web (SPA, sans build)
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js                # Encapsulation de la REST API
│       ├── components.js         # Rendu des composants UI (incluant la page des communautés)
│       └── app.js                # Routage SPA, gestion de l'état
├── tests/                        # Suite de tests (203 tests)
│   ├── test_content_preprocessor.py  # Tests de la logique de découpage (17)
│   ├── test_new_features.py      # Tests des nouvelles fonctionnalités (32)
│   ├── test_i18n.py             # Tests multilingues (57)
│   ├── test_unit.py              # Tests unitaires
│   ├── test_web_api.py           # Tests de la Web API
│   ├── test_web_ui_features.py   # Tests des fonctionnalités de la Web UI
│   ├── test_integration_manual.py # Tests d'intégration manuels
│   └── bench_deepseek_flash_vs_pro.py # Script de référence de performance flash/pro DeepSeek
├── tools/                        # Outils de diagnostic de développement
│   ├── status_report.py          # Rapport d'état consolidé
│   ├── validate_config.py        # Validation de la configuration
│   ├── performance_diagnose.py   # Diagnostic de performance
│   ├── inspect_schema.py         # Inspection de la structure Neo4j
│   ├── batch_reprocess.py        # Retraitement par lots
│   └── migrate_embeddings.py     # Migration du modèle d'Embedding
├── docs/                         # Documentation
├── logs/                         # Journaux (rotation temporelle, conservés 30 jours par défaut)
├── Dockerfile                    # Déploiement conteneurisé Docker
└── ecosystem.config.cjs          # Configuration PM2
```

## Configuration du client MCP

### Mode HTTP (recommandé)

Adapté aux clients MCP prenant en charge HTTP, tels que Claude Code, Cline, etc. :

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

Adapté aux clients devant démarrer directement le processus, tels que Claude Desktop :

**Emplacement du fichier de configuration :**
- macOS : `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows : `%APPDATA%/Claude/claude_desktop_config.json`

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

> **Remarque** : le mode SSE (`--transport sse`) est déconseillé. MCP 1.x présente des problèmes de compatibilité d'initialisation de session ; veuillez utiliser le mode HTTP à la place.

## Outils MCP (19 outils)

### Gestion de la mémoire (7)

| Outil | Description |
|------|------|
| `add_memory_simple` | Ajoute une mémoire au graphe de connaissances (prend en charge le traitement en arrière-plan, le découpage intelligent, la vérification de déduplication) |
| `add_episode_bulk` | Ajoute plusieurs mémoires en masse (traitement en arrière-plan par défaut) |
| `add_triplet` | Ajout de triplet structuré (saute le LLM, résultat instantané) |
| `search_memory_nodes` | Recherche des nœuds de mémoire (prend en charge 16 stratégies de recherche, filtrage temporel) |
| `search_memory_facts` | Recherche des faits de mémoire (prend en charge le filtrage par type de relation, plage temporelle, validité) |
| `advanced_search` | Recherche avancée (16 stratégies, retourne nœuds + arêtes + communautés + épisodes) |
| `get_episodes` | Récupère les épisodes de mémoire récents |

### Analyse des connaissances (3)

| Outil | Description |
|------|------|
| `check_conflicts` | Détecte les conflits de faits entre deux entités (valide vs invalidé) |
| `get_node_edges` | Explore les relations d'arêtes entrantes et sortantes d'un nœud |
| `build_communities` | Déclenche la détection et le regroupement de communautés (traitement en arrière-plan par défaut) |

### Maintenance de la mémoire (2)

| Outil | Description |
|------|------|
| `get_stale_memories` | Interroge les mémoires obsolètes à faible taux d'accès |
| `cleanup_stale_memories` | Nettoie les mémoires obsolètes (mode aperçu dry_run par défaut) |

### Gestion des tâches

| Outil | Description |
|------|------|
| `get_memory_task_status` | Interroge la progression et le résultat d'une tâche de traitement de mémoire en arrière-plan |

### Suppression et requête

| Outil | Description |
|------|------|
| `delete_episode` | Supprime un épisode de mémoire |
| `delete_entity_edge` | Supprime une arête d'entité (relation) |
| `get_entity_edge` | Récupère les informations détaillées d'une arête d'entité |

### Administration système

| Outil | Description |
|------|------|
| `get_status` | Récupère l'état du service (Neo4j, LLM, embedder) |
| `test_connection` | Teste la connexion Neo4j / LLM / embedder |
| `clear_graph` | Efface la base de données à graphe (prend en charge l'effacement par group_id) |

## Paramètres des outils

### add_memory_simple

| Paramètre | Type | Obligatoire | Valeur par défaut | Description |
|------|------|------|--------|------|
| `name` | string | Y | | Nom de la mémoire |
| `episode_body` | string | Y | | Contenu de la mémoire (découpage automatique au-delà de 800 caractères) |
| `group_id` | string | | `"default"` | ID de groupe (isolation par projet recommandée) |
| `source` | string | | `"text"` | Type de source : `text` / `json` / `message` |
| `source_description` | string | | `"MCP Server"` | Description de la source |
| `use_safe_mode` | bool | | `false` | Mode sûr (saute l'extraction d'entités, rapide mais la mémoire n'est pas recherchable) |
| `background` | bool | | `false` | Traitement en arrière-plan (retourne immédiatement task_id, adapté aux textes longs) |
| `force` | bool | | `false` | Saute la vérification de déduplication (ajout forcé) |
| `excluded_entity_types` | list | | | Types d'entités exclus (réduit la quantité d'extraction inutile) |

> **Conseils de performance** :
> - Texte court (<800 caractères) : traitement direct, généralement terminé en 30-40 secondes
> - Texte long (>800 caractères) : découpé automatiquement en plusieurs segments, traités en parallèle avec `add_episode_bulk` (~33 % plus rapide qu'en série)
> - Utilisez `background=true` pour éviter le blocage de l'appel MCP, et suivez la progression avec `get_memory_task_status`
> - `use_safe_mode=true` se termine instantanément mais la mémoire ne peut pas être trouvée par les outils de recherche
> - Lorsque la déduplication est activée, les mémoires très similaires reçoivent un avertissement (`force=true` permet de l'ignorer)

### add_episode_bulk

| Paramètre | Type | Obligatoire | Valeur par défaut | Description |
|------|------|------|--------|------|
| `episodes` | list | Y | | Liste des mémoires, chaque élément contenant `name` et `content` |
| `group_id` | string | | `"default"` | ID de groupe |
| `source` | string | | `"text"` | Type de source |
| `background` | bool | | `true` | Traitement en arrière-plan (le traitement en masse est généralement long) |

### add_triplet

| Paramètre | Type | Obligatoire | Valeur par défaut | Description |
|------|------|------|--------|------|
| `source_name` | string | Y | | Nom de l'entité source (ex. « Alice ») |
| `target_name` | string | Y | | Nom de l'entité cible (ex. « Google ») |
| `relation_name` | string | Y | | Nom de la relation (ex. « works_at ») |
| `fact` | string | Y | | Description du fait (ex. « Alice works at Google ») |
| `group_id` | string | | `"default"` | ID de groupe |
| `source_labels` | list | | | Étiquettes de l'entité source |
| `target_labels` | list | | | Étiquettes de l'entité cible |

### search_memory_nodes

| Paramètre | Type | Obligatoire | Valeur par défaut | Description |
|------|------|------|--------|------|
| `query` | string | Y | | Mot-clé de recherche (langage naturel) |
| `max_nodes` | int | | `10` | Nombre maximal de résultats retournés |
| `group_ids` | list | | | Filtrage par groupe (recherche conjointe sur plusieurs groupes) |
| `entity_types` | list | | | Filtrage par type d'entité |
| `search_recipe` | string | | | Stratégie de recherche (voir recherche avancée) |
| `created_after` | string | | | Borne inférieure de la date de création (datetime ISO) |
| `created_before` | string | | | Borne supérieure de la date de création (datetime ISO) |

### search_memory_facts

| Paramètre | Type | Obligatoire | Valeur par défaut | Description |
|------|------|------|--------|------|
| `query` | string | Y | | Mot-clé de recherche |
| `max_facts` | int | | `10` | Nombre maximal de résultats retournés |
| `group_ids` | list | | | Filtrage par groupe |
| `center_node_uuid` | string | | | UUID du nœud central (explore les relations d'un nœud spécifique) |
| `edge_types` | list | | | Filtrage par type de relation (ex. `["works_at"]`) |
| `created_after` | string | | | Borne inférieure de la date de création (datetime ISO) |
| `created_before` | string | | | Borne supérieure de la date de création (datetime ISO) |
| `only_valid` | bool | | `false` | Ne retourne que les faits non invalidés |

### advanced_search

| Paramètre | Type | Obligatoire | Valeur par défaut | Description |
|------|------|------|--------|------|
| `query` | string | Y | | Mot-clé de recherche |
| `search_recipe` | string | | `"combined_rrf"` | Stratégie de recherche (16 options) |
| `max_results` | int | | `10` | Nombre maximal de résultats retournés |
| `group_ids` | list | | | Filtrage par groupe |
| `center_node_uuid` | string | | | UUID du nœud central |

**Stratégies de recherche disponibles (search_recipe) :**

| Catégorie | Stratégie | Description |
|------|------|------|
| Combinée | `combined_rrf` | Fusion RRF combinée (par défaut, recommandée) |
| Combinée | `combined_mmr` | Reclassement par diversité MMR combiné |
| Combinée | `combined_cross_encoder` | Reclassement fin Cross-Encoder combiné |
| Arête | `edge_rrf` / `edge_mmr` / `edge_cross_encoder` | Recherche d'arêtes (3 tris) |
| Arête | `edge_node_distance` / `edge_episode_mentions` | Recherche d'arêtes (distance dans le graphe / nombre de citations) |
| Nœud | `node_rrf` / `node_mmr` / `node_cross_encoder` | Recherche de nœuds (3 tris) |
| Nœud | `node_node_distance` / `node_episode_mentions` | Recherche de nœuds (distance dans le graphe / nombre de citations) |
| Communauté | `community_rrf` / `community_mmr` / `community_cross_encoder` | Recherche de communautés |

### check_conflicts

| Paramètre | Type | Obligatoire | Valeur par défaut | Description |
|------|------|------|--------|------|
| `source_name` | string | Y | | Nom de l'entité source |
| `target_name` | string | Y | | Nom de l'entité cible |
| `group_id` | string | | `"default"` | ID de groupe |

### get_node_edges

| Paramètre | Type | Obligatoire | Valeur par défaut | Description |
|------|------|------|--------|------|
| `node_uuid` | string | Y | | UUID du nœud |
| `include_inbound` | bool | | `true` | Inclure les arêtes entrantes |
| `include_outbound` | bool | | `true` | Inclure les arêtes sortantes |
| `max_edges` | int | | `50` | Nombre maximal de résultats retournés |

### build_communities

| Paramètre | Type | Obligatoire | Valeur par défaut | Description |
|------|------|------|--------|------|
| `group_ids` | list | | | Groupes spécifiés (vide = tous) |
| `background` | bool | | `true` | Traitement en arrière-plan |

### get_stale_memories

| Paramètre | Type | Obligatoire | Valeur par défaut | Description |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Considérée comme obsolète au-delà de ce nombre de jours sans accès |
| `min_access_count` | int | | `2` | Incluse uniquement si le nombre d'accès est inférieur à cette valeur |
| `group_id` | string | | | Filtrage par groupe |
| `limit` | int | | `50` | Nombre maximal de résultats retournés |

### cleanup_stale_memories

| Paramètre | Type | Obligatoire | Valeur par défaut | Description |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Seuil de jours d'obsolescence |
| `min_access_count` | int | | `2` | Seuil minimal du nombre d'accès |
| `group_id` | string | | | Filtrage par groupe |
| `dry_run` | bool | | `true` | Mode aperçu (sans suppression réelle) |
| `limit` | int | | `50` | Nombre maximal d'éléments traités |

### get_memory_task_status

| Paramètre | Type | Obligatoire | Description |
|------|------|------|------|
| `task_id` | string | Y | ID de la tâche en arrière-plan (retourné par `add_memory_simple(background=true)`) |

## Interface d'administration Web

En mode HTTP, accédez à `http://localhost:8000/` pour l'utiliser.

**Fonctionnalités :**
- Tableau de bord — statistiques du nombre de nœuds, de faits, d'épisodes de mémoire
- Nœuds d'entité — navigation, filtrage, recherche vectorielle
- Relations de faits — navigation, filtrage, recherche vectorielle
- Épisodes de mémoire — navigation, recherche en texte intégral, suppression
- Navigation des communautés — liste des nœuds de communauté, résumés, déclenchement de la construction de communautés
- Formulaire de triplet — ajout direct de connaissances structurées « sujet-relation-objet »
- Gestion des groupes — filtrage par groupe, suppression par lots
- Visualisation du graphe de connaissances — présentation graphique des relations entre nœuds
- Questions-réponses par IA — questions-réponses intelligentes basées sur le graphe de connaissances
- Maintenance de la qualité — indicateurs de qualité de la mémoire et outils de nettoyage
- Import en masse — importer plusieurs épisodes de mémoire en une fois (JSON, limite de 500 par requête)
- Paramètres à l'exécution — consulter la configuration actuelle et ajuster certains paramètres sans redémarrage
- Changement de thème — thème sombre/clair

**REST API :**

| Point de terminaison | Méthode | Description |
|------|------|------|
| `/api/stats` | GET | Statistiques du tableau de bord |
| `/api/groups` | GET | Récupère tous les group_id |
| `/api/groups/stats` | GET | Statistiques nœuds/faits/épisodes par groupe |
| `/api/nodes` | GET | Parcourt les nœuds d'entité (paginé) |
| `/api/facts` | GET | Parcourt les faits (paginé) |
| `/api/episodes` | GET | Parcourt les épisodes de mémoire (paginé) |
| `/api/nodes/{uuid}/relations` | GET | Récupère les arêtes entrantes/sortantes d'un nœud |
| `/api/search/nodes` | GET | Recherche vectorielle de nœuds |
| `/api/search/facts` | GET | Recherche vectorielle de faits |
| `/api/search/episodes` | GET | Recherche d'épisodes de mémoire |
| `/api/search/advanced` | GET | Recherche avancée (16 stratégies) |
| `/api/communities` | GET | Parcourt les nœuds de communauté (paginé) |
| `/api/communities/build` | POST | Déclenche la construction de communautés |
| `/api/memory/add` | POST | Ajoute une mémoire unique |
| `/api/memory/add-bulk` | POST | Ajoute des mémoires en masse |
| `/api/memory/add-triplet` | POST | Ajoute un triplet |
| `/api/import/episodes` | POST | Import en masse d'épisodes de mémoire (JSON, limite 500 par requête) |
| `/api/memory/tasks` | GET | Liste les tâches en arrière-plan (prend en charge le filtrage par état) |
| `/api/memory/tasks/{id}` | GET | Interroge l'état d'une tâche unique |
| `/api/timeline` | GET | Navigation chronologique |
| `/api/graph/subgraph` | GET | Récupère un sous-graphe (visualisation) |
| `/api/graph/all` | GET | Récupère le graphe complet (visualisation) |
| `/api/ask` | GET | Questions-réponses par IA (basé sur la recherche dans le graphe) |
| `/api/analytics/top-nodes` | GET | Nœuds à haute connectivité/fort taux d'accès |
| `/api/analytics/quality` | GET | Indicateurs de qualité du graphe de connaissances |
| `/api/analytics/stale` | GET | Interroge les mémoires obsolètes |
| `/api/analytics/cleanup` | POST | Nettoie les mémoires obsolètes |
| `/api/config` | GET | Récupère la configuration actuelle (sans les clés API) |
| `/api/config` | PATCH | Met à jour les paramètres modifiables à l'exécution (effet limité au processus courant, réinitialisé au redémarrage) |
| `/api/nodes/{uuid}` | DELETE | Supprime un nœud |
| `/api/episodes/{uuid}` | DELETE | Supprime un épisode de mémoire |
| `/api/facts/{uuid}` | DELETE | Supprime un fait |
| `/api/groups/{group_id}` | DELETE | Supprime un groupe entier |

## Configuration

### Variables d'environnement (.env)

La configuration utilise un mécanisme de superposition : le fichier de configuration JSON sert de base, et les variables d'environnement remplacent les valeurs individuelles.

```bash
# === Obligatoire ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password        # doit être modifié

# === Choix du fournisseur de LLM ===
LLM_PROVIDER=ollama                 # ollama / glm / groq / openrouter / deepseek

# === Fournisseur d'Embedding (optionnel, suit LLM_PROVIDER par défaut) ===
# Seul glm utilise GLM Embedding, tous les autres utilisent Ollama bge-m3
# EMBEDDING_PROVIDER=ollama         # ollama / glm

# === Configuration Ollama (utilisée lorsque LLM_PROVIDER=ollama) ===
OLLAMA_MODEL=qwen2.5:3b             # modèle principal (qwen2.5:3b recommandé)
OLLAMA_SMALL_MODEL=qwen2.5:3b       # petit modèle (pour tâches simples, modèle différent possible)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.1

# === Configuration GLM (utilisée lorsque LLM_PROVIDER=glm) ===
GLM_API_KEY=your_api_key            # à obtenir depuis https://open.bigmodel.cn
GLM_MODEL=glm-4-flash               # modèle gratuit
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768

# === Configuration GROQ (utilisée lorsque LLM_PROVIDER=groq) ===
GROQ_API_KEY=your_api_key           # à obtenir depuis https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile

# === Configuration OpenRouter (utilisée lorsque LLM_PROVIDER=openrouter) ===
OPENROUTER_API_KEY=your_api_key     # à obtenir depuis https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free

# === Configuration DeepSeek (utilisée lorsque LLM_PROVIDER=deepseek) ===
DEEPSEEK_API_KEY=your_api_key       # à obtenir depuis https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash    # ou deepseek-v4-pro

# === Modèle d'embedding Ollama (utilisé pour tout embedding non-glm) ===
OLLAMA_EMBEDDING_MODEL=bge-m3
OLLAMA_EMBEDDING_DIMENSIONS=768

# === Affichage et langue (optionnel) ===
GRAPHITI_DISPLAY_TIMEZONE=Asia/Taipei # fuseau horaire d'affichage des horodatages retournés par l'API (nom IANA ; le stockage reste en UTC)
SERVER_LANG=zh-TW                     # langue de réponse des outils MCP (locales complètes dans src/i18n.py) ; la REST API suit Accept-Language

# === Performance de la mémoire (optionnel) ===
GRAPHITI_CHUNK_THRESHOLD=800         # seuil de nombre de caractères déclenchant le découpage intelligent
GRAPHITI_MAX_CHUNK_SIZE=600          # nombre maximal de caractères par segment
GRAPHITI_MAX_COROUTINES=10            # nombre maximal de coroutines parallèles
GRAPHITI_DEFAULT_BACKGROUND=false    # traitement en arrière-plan par défaut
TASK_DB_PATH=data/tasks.db           # chemin de persistance SQLite des tâches en arrière-plan

# === Suivi de l'importance et oubli intelligent (optionnel) ===
ENABLE_IMPORTANCE_TRACKING=true      # active le suivi des accès
IMPORTANCE_WEIGHT=0.1                # poids de l'importance
STALE_DAYS_THRESHOLD=30              # seuil de jours d'obsolescence
STALE_MIN_ACCESS_COUNT=2             # nombre d'accès minimal

# === Journalisation ===
LOG_FILE=logs/graphiti_mcp_server.log
LOG_LEVEL=INFO
```

> **La liste complète des variables d'environnement** est disponible dans `.env.example`

### Fichier de configuration JSON

Adapté aux configurations nécessitant un contrôle de version (les variables d'environnement peuvent toujours remplacer) :

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

## Exécution en arrière-plan avec PM2

```bash
npm install -g pm2

pm2 start ecosystem.config.cjs      # démarrer
pm2 status                           # état
pm2 logs graphiti-mcp-http           # journaux en temps réel
pm2 restart graphiti-mcp-http --update-env  # redémarrer (recharge .env)

pm2 save && pm2 startup              # configurer le démarrage automatique au boot
```

> **Conseil** : après avoir modifié `.env`, vous devez redémarrer avec le drapeau `--update-env`, sinon les variables d'environnement ne seront pas mises à jour.

## Déploiement Docker

```bash
docker build -t graphiti-mcp .

# Remarque : le conteneur Docker doit pouvoir se connecter à Neo4j et Ollama
# Utiliser le host network est le plus simple
docker run -p 8000:8000 --env-file .env --network host graphiti-mcp

# Ou spécifier explicitement les adresses des services externes
docker run -p 8000:8000 \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --env-file .env graphiti-mcp
```

## Tests

```bash
# Exécuter tous les tests (203, environ 1 seconde)
uv run python -m pytest tests/

# Sortie détaillée
uv run python -m pytest tests/ -v

# Exécuter uniquement un test spécifique
uv run python -m pytest tests/test_content_preprocessor.py -v
uv run python -m pytest tests/test_new_features.py -v
uv run python -m pytest tests/test_unit.py -v
```

> **Remarque** : les 3 tests async de `test_integration_manual.py` nécessitent l'installation de `pytest-asyncio` ; en son absence, ils s'afficheront en Failed sans affecter les autres tests. `bench_deepseek_flash_vs_pro.py` est un script de référence de performance, pas un test unitaire.

## Dépannage

### Échec de la connexion Neo4j

```bash
neo4j status                              # vérifier l'état du service
cypher-shell -u neo4j -p your_password    # confirmer que le mot de passe est correct
curl http://localhost:7474                 # confirmer le port HTTP
```

Causes fréquentes :
- Neo4j n'est pas démarré
- Mot de passe incorrect (`NEO4J_PASSWORD` dans `.env`)
- Port occupé ou bloqué par un pare-feu

### Échec de la connexion au LLM

**Mode Ollama :**
```bash
ollama serve                # démarrer le service Ollama
ollama list                 # vérifier les modèles installés
ollama pull qwen2.5:3b      # installer le modèle manquant
```

Causes fréquentes : Ollama non démarré, modèle non installé, mémoire GPU insuffisante

**Mode GLM :**
- Confirmer que `GLM_API_KEY` est correct
- Confirmer que `GLM_EMBEDDING_DIMENSIONS=768` (doit correspondre à l'index vectoriel Neo4j)
- Point de terminaison de l'API GLM : `https://open.bigmodel.cn/api/paas/v4/`

**Mode GROQ :**
- Confirmer que `GROQ_API_KEY` est correct
- En cas de Rate Limit fréquent, envisager de passer au mode GLM
- GROQ ne fournit pas d'Embedding ; il faut s'assurer que l'embedder Ollama est disponible

**Mode OpenRouter :**
- Confirmer que `OPENROUTER_API_KEY` est correct et que `OPENROUTER_MODEL` est un ID de modèle valide (voir https://openrouter.ai/models)
- Ne fournit pas d'Embedding ; il faut s'assurer que l'embedder Ollama est disponible

**Mode DeepSeek :**
- Confirmer que `DEEPSEEK_API_KEY` est correct
- Si `Prompt must contain the word 'json'` apparaît : il s'agit d'une exigence stricte du mode `json_object` de DeepSeek ; le client dispose d'une protection de secours intégrée ; si l'erreur persiste, vérifiez que vous utilisez la dernière version de `src/deepseek_client.py` et redémarrez le service
- Ne fournit pas d'Embedding ; il faut s'assurer que l'embedder Ollama est disponible

### Erreur de connexion MCP

Si `Invalid request parameters` ou `Received request before initialization was complete` apparaît :

1. Confirmer l'utilisation du mode de transport HTTP (**ne pas utiliser SSE**)
2. Confirmer que le client est configuré avec `"type": "http"`, `"url": "http://localhost:8000/mcp"`
3. Redémarrer le service : `pm2 restart graphiti-mcp-http --update-env`
4. Exécuter `/mcp` dans Claude Code pour reconnecter

### Ajout de mémoire lent

- **Ollama** : vérifier la taille du modèle (`qwen2.5:3b` est 5 à 10 fois plus rapide que `7b`), confirmer l'utilisation du GPU (`ollama ps`)
- **GLM** : chaque add_episode nécessite 10 à 20+ allers-retours réseau LLM ; ~22 s pour un texte court est une valeur normale
- **GROQ** : le Rate Limit entraîne de nombreuses tentatives de réessai ; en cas d'utilisation fréquente, il est recommandé de passer à GLM ou Ollama
- Utiliser `background=true` pour éviter le blocage
- Réduire `GRAPHITI_CHUNK_THRESHOLD` pour que les textes longs soient découpés plus tôt

### Problèmes PM2

```bash
pm2 status                                        # vérifier l'état
pm2 logs graphiti-mcp-http --err --lines 50        # journaux d'erreurs
lsof -i :8000                                     # vérifier l'occupation du port
pm2 delete graphiti-mcp-http && pm2 start ecosystem.config.cjs  # redémarrage complet
```

## Outils de diagnostic de développement

```bash
uv run python tools/status_report.py           # rapport d'état consolidé (Neo4j + Ollama + configuration)
uv run python tools/validate_config.py         # valider l'intégrité de .env et de la configuration
uv run python tools/performance_diagnose.py    # diagnostic de performance du LLM
uv run python tools/inspect_schema.py          # inspection des index et contraintes Neo4j
uv run python tools/migrate_embeddings.py      # migration du modèle d'Embedding (régénération des vecteurs après changement de modèle)
```

### Migration du modèle d'Embedding

Après avoir changé de modèle d'embedding (ex. `nomic-embed-text` → `bge-m3`), vous pouvez utiliser l'outil de migration pour régénérer tous les vecteurs existants, garantissant une qualité de recherche cohérente :

```bash
# Prévisualiser le nombre d'éléments à migrer
uv run python tools/migrate_embeddings.py --dry-run

# Migration complète (prend en charge la reprise après interruption)
uv run python tools/migrate_embeddings.py

# Migrer uniquement un groupe spécifié
uv run python tools/migrate_embeddings.py --group-id myproject

# Reprendre à partir du point d'interruption (relancer après une interruption)
uv run python tools/migrate_embeddings.py --resume
```

> **Compatibilité** : `bge-m3` est nativement en 1024 dimensions ; le système le tronque automatiquement à 768 dimensions pour rester compatible avec l'index vectoriel Neo4j existant. Les données avant et après la migration peuvent coexister, mais il est recommandé d'effectuer une migration complète pour obtenir la meilleure qualité de recherche.

## Documentation

- [Instructions d'utilisation des outils](../使用工具的指令.md) — guide d'utilisation des outils MCP et bonnes pratiques
- [Graphiti Memory Rules](../graphiti-memory-rules.md) — explication des règles de mémoire

## Licence

MIT License
