# Graphiti MCP Server

ナレッジグラフ記憶サービス — 複数の LLM プロバイダー（Ollama / GLM / GROQ / OpenRouter / DeepSeek）と Neo4j グラフデータベースを統合した MCP サーバー。

[getzep/graphiti](https://github.com/getzep/graphiti) をベースに拡張開発されており、ローカルの Ollama とクラウド LLM を柔軟に切り替えられ、さらに Embedding プロバイダーを独立して指定できます（LLM とのデカップリング）。

## 主な機能

- **インテリジェントな記憶管理** — ナレッジグラフを使用して複雑な記憶関係を保存・検索
- **意味検索** — ベクトル埋め込みに基づくハイブリッド検索（ベクトル + キーワード + グラフ走査）
- **16 種類の検索戦略** — 高度な検索が RRF、MMR、Cross-Encoder などの複数の再ランキング方式をサポート
- **複数の LLM プロバイダー** — Ollama（ローカル）、GLM（智谱 AI 無料）、GROQ（高速推論）、OpenRouter（各社モデルを集約）、DeepSeek（深度求索）をサポートし、環境変数でワンクリック切り替え
- **Embedding と LLM のデカップリング** — `EMBEDDING_PROVIDER` で埋め込み器を独立して指定可能。クラウド LLM は自動的にローカル `bge-m3` にフォールバック
- **デュアルモデル振り分け** — Ollama モードでは複雑なタスクにメインモデルを使用し、単純なタスクは自動的に小型モデルに切り替えてパフォーマンスを向上
- **インテリジェントなコンテンツ分割** — 長文を自動的に分割処理し、LLM の負荷を軽減（閾値は設定可能）
- **バックグラウンド記憶処理** — 記憶の追加をバックグラウンドで実行可能。MCP 呼び出しは即座に返る
- **記憶の重複排除** — 高度に類似する既存の記憶を自動検出し、重複保存を回避
- **競合検出** — 2 つのエンティティ間の矛盾する事実を検出し、無効化された情報と有効な情報を識別
- **コミュニティ検出** — Label Propagation アルゴリズムに基づいて関連エンティティを自動クラスタリング
- **重要度トラッキング** — エンティティのアクセス頻度を自動記録し、検索結果を重要度順にソート
- **インテリジェントな忘却** — 古く、アクセス量の少ない記憶を識別・整理し、グラフを簡潔に保つ
- **一括インポート** — 一度に複数の記憶を送信。大量のデータ移行に最適
- **構造化トリプレット** — 「主体-関係-客体」を直接追加し、LLM 抽出をスキップして瞬時に完了
- **Web 管理インターフェース** — ダッシュボード、ブラウジング、検索、ナレッジグラフ可視化、AI 質問応答、コミュニティブラウジングを内蔵
- **多言語対応（i18n）** — 応答メッセージが 30 以上のロケールをサポート（zh-TW / en / zh-CN / ja / pt-BR / ko / es / de / fr など）。MCP ツールは `SERVER_LANG`、REST API は HTTP `Accept-Language` に基づいて自動ネゴシエーション
- **ダーク/ライトテーマ** — Web インターフェースがテーマ切り替えをサポート
- **セーフモード** — エンティティ抽出をスキップする高速記憶追加を選択可能
- **Docker サポート** — Dockerfile を内蔵し、コンテナ化デプロイをサポート
- **並行安全性** — asyncio.Lock が初期化を保護し、競合状態を防止
- **階層型ヘルスチェック** — `/health`（liveness）+ `/health/ready`（readiness）

## システム要件

| 項目 | 要件 |
|------|------|
| Python | 3.10+（3.11+ 推奨） |
| Neo4j | 4.0+（`bolt://localhost:7687`） |
| LLM プロバイダー | Ollama / GLM / GROQ / OpenRouter / DeepSeek（5 つから 1 つ選択） |
| Node.js | 18+（PM2 バックグラウンド実行のみに使用。オプション） |
| ディスク容量 | 約 3GB（Ollama モデル + Neo4j データ） |

### LLM プロバイダーの選択

`LLM_PROVIDER` 環境変数で切り替えます（`ollama` / `glm` / `groq` / `openrouter` / `deepseek`）：

| プロバイダー | 特徴 | LLM モデル | Embedding | 適したシナリオ |
|--------|------|----------|-----------|----------|
| **Ollama**（デフォルト） | 完全ローカル。データは端末外に出ない | `qwen2.5:3b` | `bge-m3`（中国語 + RAG が優秀） | GPU があり、プライバシーを重視 |
| **GLM** | 無料クラウド。安定して無制限 | `glm-4-flash`（無料） | `embedding-3` | GPU なし、検索集約型シナリオ |
| **GROQ** | 超高速推論 | `llama-3.3-70b-versatile` | Ollama `bge-m3` にフォールバック | 時々書き込み、品質を追求 |
| **OpenRouter** | 各社モデルを集約、無料枠を含む | `stepfun/step-3.5-flash:free` など | Ollama `bge-m3` にフォールバック | 特定のクラウドモデルを使いたい |
| **DeepSeek** | 深度求索クラウド、コストパフォーマンスが高い | `deepseek-v4-flash` / `deepseek-v4-pro` | Ollama `bge-m3` にフォールバック | 中国語理解、低コストクラウド |

> **Embedding と LLM のデカップリング**：埋め込み器は `EMBEDDING_PROVIDER`（`ollama` / `glm`）で独立して指定し、未設定の場合は `LLM_PROVIDER` に従います。実際には `glm` のみが GLM `embedding-3` を使用し、それ以外（GROQ / OpenRouter / DeepSeek など Embedding を提供しないクラウド LLM を含む）はすべて自動的に Ollama `bge-m3` を使用します。**したがって、いずれかのクラウド LLM を使用する場合でも、依然としてローカルの Ollama が埋め込みサービスを提供する必要があります（embedding も glm に設定する場合を除く）。**

#### Ollama モード（ローカル）

```bash
# LLM メインモデル（qwen2.5:3b を推奨。速度と安定性のバランスが最良）
ollama pull qwen2.5:3b

# 埋め込みモデル（必須。ベクトル検索に使用）
ollama pull bge-m3
```

> **モデル選択の注意事項**：
> - `qwen2.5:3b` — 推奨。~2s/call、~100 t/s、graphiti-core の構造化出力が 100% 安定
> - `qwen2.5:7b` — 効果はより良いが 5-10 倍遅い。品質を追求するシナリオに適する
> - `qwen2.5:1.5b` — 速度は最速だが**不安定**（構造化 JSON の成功率はわずか 33%）。使用は推奨しない

#### GLM モード（智谱 AI クラウド）

```bash
# .env 設定
LLM_PROVIDER=glm
GLM_API_KEY=your_api_key          # https://open.bigmodel.cn から取得
GLM_MODEL=glm-4-flash             # 無料モデル
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768      # Neo4j ベクトルインデックスの次元と一致させる必要がある
```

> **GLM パフォーマンス参考**：書き込み ~22s（短文）、検索 ~0.34s、Rate Limit エラーゼロ。ローカルの Ollama より 2-5 倍遅いが完全無料。

#### GROQ モード（高速推論）

```bash
# .env 設定
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key         # https://console.groq.com から取得
GROQ_MODEL=llama-3.3-70b-versatile
```

> **注意**：GROQ は Embedding サービスを提供しないため、Ollama 埋め込み器（自動フォールバック）と組み合わせるか、`EMBEDDING_PROVIDER` を glm に設定する必要があります。GROQ には厳格な Rate Limit があり、高頻度の使用では大量のリトライが発生します。

#### OpenRouter モード（各社モデルを集約）

```bash
# .env 設定
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_api_key       # https://openrouter.ai/keys から取得
OPENROUTER_MODEL=stepfun/step-3.5-flash:free   # 任意の OpenRouter モデルに変更可能
```

> **注意**：OpenRouter は Embedding を提供せず、自動的に Ollama `bge-m3` にフォールバックします。モデル一覧は https://openrouter.ai/models を参照（複数の `:free` 無料モデルを含む）。

#### DeepSeek モード（深度求索）

```bash
# .env 設定
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key         # https://platform.deepseek.com から取得
DEEPSEEK_MODEL=deepseek-v4-flash      # 推奨。または deepseek-v4-pro（効果がより良い）
```

> **注意**：DeepSeek は Embedding を提供せず、自動的に Ollama `bge-m3` にフォールバックします。`deepseek-chat` / `deepseek-reasoner` は 2026-07-24 に廃止されるため、`deepseek-v4-flash` / `deepseek-v4-pro` への変更を推奨します。DeepSeek は `json_object` モードの prompt に "json" 文字列を含むことを厳格に要求しますが、クライアントには予備の防護が内蔵されているため、追加設定は不要です。

## クイックスタート

### 1. 事前準備

Neo4j がローカルで実行されていることを確認し、選択した LLM プロバイダーに応じて対応するサービスを準備します：

```bash
# Neo4j が実行中であることを確認（必須）
neo4j status
# または Docker を使用: docker run -d -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/your_password neo4j:latest

# Ollama モード: Ollama が実行中であることを確認
ollama list
# 未起動の場合: ollama serve

# GLM / GROQ モード: 有効な API Key のみ必要。ローカルサービスは不要
```

### 2. 依存関係のインストール

```bash
git clone <repo-url>
cd graphiti
uv sync
```

> **注意**：本プロジェクトは [uv](https://github.com/astral-sh/uv) を使用して依存関係を管理します。未インストールの場合：`curl -LsSf https://astral.sh/uv/install.sh | sh`

### 3. 環境の設定

```bash
cp .env.example .env
```

`.env` を編集し、**少なくとも**以下の項目を変更する必要があります：

```bash
NEO4J_PASSWORD=your_actual_password  # 必須: Neo4j パスワード
LLM_PROVIDER=ollama                  # ollama / glm / groq / openrouter / deepseek
OLLAMA_MODEL=qwen2.5:3b              # Ollama モード: ローカル LLM モデル
# GLM_API_KEY=your_key               # GLM モード: 智谱 AI API Key
# GROQ_API_KEY=your_key              # GROQ モード: GROQ API Key
# OPENROUTER_API_KEY=your_key        # OpenRouter モード: API Key
# DEEPSEEK_API_KEY=your_key          # DeepSeek モード: API Key
```

### 4. サービスの起動

```bash
# HTTP モード（推奨。Web 管理インターフェースを含む）
uv run python graphiti_mcp_server.py --transport http --port 8000

# または PM2 でバックグラウンド実行（長期運用に推奨）
pm2 start ecosystem.config.cjs
```

### 5. サービスの検証

起動後、以下のエンドポイントにアクセスできます：

| エンドポイント | 説明 |
|------|------|
| http://localhost:8000/ | Web 管理インターフェース |
| http://localhost:8000/mcp | MCP エンドポイント（MCP クライアント接続用） |
| http://localhost:8000/health | ヘルスチェック（liveness） |
| http://localhost:8000/health/ready | 詳細チェック（Neo4j 接続を含む） |
| http://localhost:8000/api/stats | REST API 統計 |

## プロジェクト構造

```
graphiti/
├── graphiti_mcp_server.py        # メインエントリ — MCP ツール定義（19 個のツール）
├── src/
│   ├── config.py                 # 設定管理（GraphitiConfig、JSON/.env のレイヤード読み込みをサポート）
│   ├── web_api.py                # Web 管理インターフェース REST API（20+ エンドポイント）
│   ├── ollama_graphiti_client.py  # Ollama LLM クライアント（デュアルモデル振り分け）
│   ├── glm_client.py             # GLM（智谱 AI）LLM クライアント（OpenAI 互換 API）
│   ├── openrouter_client.py      # OpenRouter LLM クライアント（各社モデルを集約）
│   ├── deepseek_client.py        # DeepSeek LLM クライアント（json_object + 予備の json 防護）
│   ├── ollama_embedder.py        # Ollama 埋め込みモデルアダプター
│   ├── content_preprocessor.py   # インテリジェントなコンテンツ分割（長文を自動分割）
│   ├── deduplication.py          # 記憶の重複排除（コサイン類似度比較）
│   ├── importance.py             # 重要度トラッキングとインテリジェントな忘却
│   ├── safe_memory_add.py        # 安全な記憶追加（エンティティ抽出をスキップ）
│   ├── timezone_utils.py         # タイムゾーン変換（UTC→ローカルタイムゾーン表示）
│   ├── i18n.py                   # バックエンド多言語対応（REST は Accept-Language、MCP は SERVER_LANG に従う）
│   ├── exceptions.py             # 構造化例外処理（12 種類の例外クラス）
│   └── logging_setup.py          # ロギングシステム（時間ローテーション + パフォーマンス監視）
├── web/                          # Web 管理インターフェースフロントエンド（SPA、ビルド不要）
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js                # REST API ラッパー
│       ├── components.js         # UI コンポーネントレンダリング（コミュニティページを含む）
│       └── app.js                # SPA ルーティング、状態管理
├── tests/                        # テストスイート（183 個のテスト）
│   ├── test_content_preprocessor.py  # 分割ロジックテスト（17 個）
│   ├── test_new_features.py      # 新機能テスト（32 個）
│   ├── test_i18n.py             # 多言語対応テスト（37 個）
│   ├── test_unit.py              # ユニットテスト
│   ├── test_web_api.py           # Web API テスト
│   ├── test_web_ui_features.py   # Web UI 機能テスト
│   ├── test_integration_manual.py # 手動統合テスト
│   └── bench_deepseek_flash_vs_pro.py # DeepSeek flash/pro パフォーマンスベンチマークスクリプト
├── tools/                        # 開発診断ツール
│   ├── status_report.py          # 統合状態レポート
│   ├── validate_config.py        # 設定検証
│   ├── performance_diagnose.py   # パフォーマンス診断
│   ├── inspect_schema.py         # Neo4j 構造チェック
│   └── batch_reprocess.py        # バッチ再処理
├── docs/                         # ドキュメント
├── logs/                         # ログ（時間ローテーション、デフォルトで 30 日間保持）
├── Dockerfile                    # Docker コンテナ化デプロイ
└── ecosystem.config.cjs          # PM2 設定
```

## MCP クライアント設定

### HTTP モード（推奨）

Claude Code、Cline など HTTP をサポートする MCP クライアントに適しています：

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

### STDIO モード

Claude Desktop などプロセスを直接起動する必要があるクライアントに適しています：

**設定ファイルの場所：**
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

> **注意**：SSE モード（`--transport sse`）は推奨されなくなりました。MCP 1.x には session 初期化の互換性問題があるため、HTTP モードに変更してください。

## MCP ツール（19 個）

### 記憶管理（7 個）

| ツール | 説明 |
|------|------|
| `add_memory_simple` | ナレッジグラフに記憶を追加（バックグラウンド処理、インテリジェントな分割、重複排除チェックをサポート） |
| `add_episode_bulk` | 複数の記憶を一括追加（デフォルトでバックグラウンド処理） |
| `add_triplet` | 構造化トリプレットの追加（LLM をスキップし、瞬時に完了） |
| `search_memory_nodes` | 記憶ノードを検索（16 種類の検索戦略、時間フィルタリングをサポート） |
| `search_memory_facts` | 記憶事実を検索（関係タイプフィルタリング、時間範囲、有効性フィルタリングをサポート） |
| `advanced_search` | 高度な検索（16 種類の戦略。ノード+エッジ+コミュニティ+エピソードを返す） |
| `get_episodes` | 最近の記憶エピソードを取得 |

### 知識分析（3 個）

| ツール | 説明 |
|------|------|
| `check_conflicts` | 2 つのエンティティ間の事実の競合を検出（有効 vs 無効化済み） |
| `get_node_edges` | ノードの入力エッジと出力エッジの関係を探索 |
| `build_communities` | コミュニティ検出とクラスタリングをトリガー（デフォルトでバックグラウンド処理） |

### 記憶メンテナンス（2 個）

| ツール | 説明 |
|------|------|
| `get_stale_memories` | 古く、アクセス量の少ない記憶を照会 |
| `cleanup_stale_memories` | 古い記憶を整理（デフォルトで dry_run プレビューモード） |

### タスク管理

| ツール | 説明 |
|------|------|
| `get_memory_task_status` | バックグラウンド記憶処理タスクの進捗と結果を照会 |

### 削除と照会

| ツール | 説明 |
|------|------|
| `delete_episode` | 記憶エピソードを削除 |
| `delete_entity_edge` | エンティティエッジ（関係）を削除 |
| `get_entity_edge` | エンティティエッジの詳細情報を取得 |

### システム管理

| ツール | 説明 |
|------|------|
| `get_status` | サービス状態を取得（Neo4j、LLM、埋め込み器） |
| `test_connection` | Neo4j / LLM / 埋め込み器の接続をテスト |
| `clear_graph` | グラフデータベースを消去（group_id 単位での消去をサポート） |

## ツールパラメータ

### add_memory_simple

| パラメータ | 型 | 必須 | デフォルト値 | 説明 |
|------|------|------|--------|------|
| `name` | string | Y | | 記憶名 |
| `episode_body` | string | Y | | 記憶内容（800 文字を超えると自動分割） |
| `group_id` | string | | `"default"` | グループ ID（プロジェクトごとに分離することを推奨） |
| `source` | string | | `"text"` | ソースタイプ: `text` / `json` / `message` |
| `source_description` | string | | `"MCP Server"` | ソースの説明 |
| `use_safe_mode` | bool | | `false` | セーフモード（エンティティ抽出をスキップ。高速だが記憶は検索不可） |
| `background` | bool | | `false` | バックグラウンド処理（即座に task_id を返す。長文に適する） |
| `force` | bool | | `false` | 重複排除チェックをスキップ（強制追加） |
| `excluded_entity_types` | list | | | 除外するエンティティタイプ（不要な抽出量を削減） |

> **パフォーマンスのヒント**：
> - 短文（<800 文字）：直接処理。通常 30-40 秒で完了
> - 長文（>800 文字）：自動的に複数のセグメントに分割し、`add_episode_bulk` で並行処理（直列より ~33% 速い）
> - `background=true` を使用すると MCP 呼び出しのブロックを回避でき、`get_memory_task_status` で進捗を追跡可能
> - `use_safe_mode=true` は瞬時に完了するが、記憶は search ツールで見つけられない
> - 重複排除を有効にすると、高度に類似する記憶は警告される（`force=true` でスキップ可能）

### add_episode_bulk

| パラメータ | 型 | 必須 | デフォルト値 | 説明 |
|------|------|------|--------|------|
| `episodes` | list | Y | | 記憶リスト。各項目は `name` と `content` を含む |
| `group_id` | string | | `"default"` | グループ ID |
| `source` | string | | `"text"` | ソースタイプ |
| `background` | bool | | `true` | バックグラウンド処理（一括処理は通常時間がかかる） |

### add_triplet

| パラメータ | 型 | 必須 | デフォルト値 | 説明 |
|------|------|------|--------|------|
| `source_name` | string | Y | | ソースエンティティ名（例: "Alice"） |
| `target_name` | string | Y | | ターゲットエンティティ名（例: "Google"） |
| `relation_name` | string | Y | | 関係名（例: "works_at"） |
| `fact` | string | Y | | 事実の記述（例: "Alice works at Google"） |
| `group_id` | string | | `"default"` | グループ ID |
| `source_labels` | list | | | ソースエンティティのラベル |
| `target_labels` | list | | | ターゲットエンティティのラベル |

### search_memory_nodes

| パラメータ | 型 | 必須 | デフォルト値 | 説明 |
|------|------|------|--------|------|
| `query` | string | Y | | 検索キーワード（自然言語） |
| `max_nodes` | int | | `10` | 最大返却数 |
| `group_ids` | list | | | グループフィルタリング（複数の group を統合検索） |
| `entity_types` | list | | | エンティティタイプフィルタリング |
| `search_recipe` | string | | | 検索戦略（高度な検索を参照） |
| `created_after` | string | | | 作成時刻の下限（ISO datetime） |
| `created_before` | string | | | 作成時刻の上限（ISO datetime） |

### search_memory_facts

| パラメータ | 型 | 必須 | デフォルト値 | 説明 |
|------|------|------|--------|------|
| `query` | string | Y | | 検索キーワード |
| `max_facts` | int | | `10` | 最大返却数 |
| `group_ids` | list | | | グループフィルタリング |
| `center_node_uuid` | string | | | 中心ノード UUID（特定ノードの関係を探索） |
| `edge_types` | list | | | 関係タイプフィルタリング（例: `["works_at"]`） |
| `created_after` | string | | | 作成時刻の下限（ISO datetime） |
| `created_before` | string | | | 作成時刻の上限（ISO datetime） |
| `only_valid` | bool | | `false` | 無効化されていない事実のみを返す |

### advanced_search

| パラメータ | 型 | 必須 | デフォルト値 | 説明 |
|------|------|------|--------|------|
| `query` | string | Y | | 検索キーワード |
| `search_recipe` | string | | `"combined_rrf"` | 検索戦略（16 種類から選択可能） |
| `max_results` | int | | `10` | 最大返却数 |
| `group_ids` | list | | | グループフィルタリング |
| `center_node_uuid` | string | | | 中心ノード UUID |

**利用可能な検索戦略（search_recipe）：**

| カテゴリ | 戦略 | 説明 |
|------|------|------|
| 総合 | `combined_rrf` | 総合 RRF 融合（デフォルト、推奨） |
| 総合 | `combined_mmr` | 総合 MMR 多様性再ランキング |
| 総合 | `combined_cross_encoder` | 総合 Cross-Encoder 精密ランキング |
| エッジ | `edge_rrf` / `edge_mmr` / `edge_cross_encoder` | エッジ検索（3 種類のランキング） |
| エッジ | `edge_node_distance` / `edge_episode_mentions` | エッジ検索（グラフ距離/引用回数） |
| ノード | `node_rrf` / `node_mmr` / `node_cross_encoder` | ノード検索（3 種類のランキング） |
| ノード | `node_node_distance` / `node_episode_mentions` | ノード検索（グラフ距離/引用回数） |
| コミュニティ | `community_rrf` / `community_mmr` / `community_cross_encoder` | コミュニティ検索 |

### check_conflicts

| パラメータ | 型 | 必須 | デフォルト値 | 説明 |
|------|------|------|--------|------|
| `source_name` | string | Y | | ソースエンティティ名 |
| `target_name` | string | Y | | ターゲットエンティティ名 |
| `group_id` | string | | `"default"` | グループ ID |

### get_node_edges

| パラメータ | 型 | 必須 | デフォルト値 | 説明 |
|------|------|------|--------|------|
| `node_uuid` | string | Y | | ノード UUID |
| `include_inbound` | bool | | `true` | 入力エッジを含む |
| `include_outbound` | bool | | `true` | 出力エッジを含む |
| `max_edges` | int | | `50` | 最大返却数 |

### build_communities

| パラメータ | 型 | 必須 | デフォルト値 | 説明 |
|------|------|------|--------|------|
| `group_ids` | list | | | グループを指定（空の場合は全部） |
| `background` | bool | | `true` | バックグラウンド処理 |

### get_stale_memories

| パラメータ | 型 | 必須 | デフォルト値 | 説明 |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | 何日アクセスがないと古いとみなすか |
| `min_access_count` | int | | `2` | アクセス回数がこの値未満の場合のみ対象に含める |
| `group_id` | string | | | グループフィルタリング |
| `limit` | int | | `50` | 最大返却数 |

### cleanup_stale_memories

| パラメータ | 型 | 必須 | デフォルト値 | 説明 |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | 古い日数の閾値 |
| `min_access_count` | int | | `2` | 最低アクセス回数の閾値 |
| `group_id` | string | | | グループフィルタリング |
| `dry_run` | bool | | `true` | プレビューモード（実際には削除しない） |
| `limit` | int | | `50` | 最大処理数 |

### get_memory_task_status

| パラメータ | 型 | 必須 | 説明 |
|------|------|------|------|
| `task_id` | string | Y | バックグラウンドタスク ID（`add_memory_simple(background=true)` が返す） |

## Web 管理インターフェース

HTTP モードで `http://localhost:8000/` にアクセスすれば使用できます。

**機能：**
- ダッシュボード — ノード数、事実数、記憶エピソード数の統計
- エンティティノード — ブラウジング、フィルタリング、ベクトル検索
- 事実関係 — ブラウジング、フィルタリング、ベクトル検索
- 記憶エピソード — ブラウジング、全文検索、削除
- コミュニティブラウジング — コミュニティノード一覧、概要、コミュニティ構築のトリガー
- トリプレットフォーム — 「主体-関係-客体」構造化知識を直接追加
- Group 管理 — グループ別フィルタリング、バッチ削除
- ナレッジグラフ可視化 — ノード関係をグラフィカルに表示
- AI 質問応答 — ナレッジグラフに基づくインテリジェントな質問応答
- 品質分析 — 記憶の品質とカバレッジの分析
- テーマ切り替え — ダーク/ライトテーマ

**REST API：**

| エンドポイント | メソッド | 説明 |
|------|------|------|
| `/api/stats` | GET | ダッシュボード統計 |
| `/api/groups` | GET | すべての group_id を取得 |
| `/api/nodes` | GET | エンティティノードをブラウズ（ページネーション） |
| `/api/facts` | GET | 事実をブラウズ（ページネーション） |
| `/api/episodes` | GET | 記憶エピソードをブラウズ（ページネーション） |
| `/api/search/nodes` | GET | ノードをベクトル検索 |
| `/api/search/facts` | GET | 事実をベクトル検索 |
| `/api/search/advanced` | GET | 高度な検索（16 種類の戦略） |
| `/api/communities` | GET | コミュニティノードをブラウズ（ページネーション） |
| `/api/communities/build` | POST | コミュニティ構築をトリガー |
| `/api/memory/add-bulk` | POST | 記憶を一括追加 |
| `/api/memory/add-triplet` | POST | トリプレットを追加 |
| `/api/memory/tasks` | GET | バックグラウンドタスク一覧（状態フィルタリングをサポート） |
| `/api/memory/tasks/{id}` | GET | 単一タスクの状態を照会 |
| `/api/analytics/stale` | GET | 古い記憶を照会 |
| `/api/analytics/cleanup` | POST | 古い記憶を整理 |
| `/api/nodes/{uuid}` | DELETE | ノードを削除 |
| `/api/episodes/{uuid}` | DELETE | 記憶エピソードを削除 |
| `/api/facts/{uuid}` | DELETE | 事実を削除 |
| `/api/groups/{group_id}` | DELETE | group 全体を削除 |

## 設定

### 環境変数（.env）

設定はレイヤード機構を使用します：JSON 設定ファイルをベースとし、環境変数が個別の値を上書きします。

```bash
# === 必須 ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password        # 必ず変更すること

# === LLM プロバイダーの選択 ===
LLM_PROVIDER=ollama                 # ollama / glm / groq / openrouter / deepseek

# === Embedding プロバイダー（オプション。デフォルトは LLM_PROVIDER に従う） ===
# glm のみが GLM Embedding を使用し、それ以外はすべて Ollama bge-m3 を使用
# EMBEDDING_PROVIDER=ollama         # ollama / glm

# === Ollama 設定（LLM_PROVIDER=ollama のとき使用） ===
OLLAMA_MODEL=qwen2.5:3b             # メインモデル（qwen2.5:3b を推奨）
OLLAMA_SMALL_MODEL=qwen2.5:3b       # 小型モデル（単純タスク用。異なるモデルを選択可能）
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.1

# === GLM 設定（LLM_PROVIDER=glm のとき使用） ===
GLM_API_KEY=your_api_key            # https://open.bigmodel.cn から取得
GLM_MODEL=glm-4-flash               # 無料モデル
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768

# === GROQ 設定（LLM_PROVIDER=groq のとき使用） ===
GROQ_API_KEY=your_api_key           # https://console.groq.com から取得
GROQ_MODEL=llama-3.3-70b-versatile

# === OpenRouter 設定（LLM_PROVIDER=openrouter のとき使用） ===
OPENROUTER_API_KEY=your_api_key     # https://openrouter.ai/keys から取得
OPENROUTER_MODEL=stepfun/step-3.5-flash:free

# === DeepSeek 設定（LLM_PROVIDER=deepseek のとき使用） ===
DEEPSEEK_API_KEY=your_api_key       # https://platform.deepseek.com から取得
DEEPSEEK_MODEL=deepseek-v4-flash    # または deepseek-v4-pro

# === Ollama 埋め込みモデル（glm 埋め込み以外のときはすべて使用） ===
OLLAMA_EMBEDDING_MODEL=bge-m3
OLLAMA_EMBEDDING_DIMENSIONS=768

# === 表示と言語（オプション） ===
GRAPHITI_DISPLAY_TIMEZONE=Asia/Taipei # API が返すタイムスタンプの表示タイムゾーン（IANA 名。保存は UTC を維持）
SERVER_LANG=zh-TW                     # MCP ツールの応答言語（完全な locale は src/i18n.py を参照）。REST API は Accept-Language に従う

# === 記憶パフォーマンス（オプション） ===
GRAPHITI_CHUNK_THRESHOLD=800         # インテリジェントな分割をトリガーする文字数の閾値
GRAPHITI_MAX_CHUNK_SIZE=600          # 各セグメントの最大文字数
GRAPHITI_MAX_COROUTINES=10            # 最大並行コルーチン数
GRAPHITI_DEFAULT_BACKGROUND=false    # デフォルトでバックグラウンド処理するかどうか

# === 重要度トラッキングとインテリジェントな忘却（オプション） ===
ENABLE_IMPORTANCE_TRACKING=true      # アクセストラッキングを有効化
IMPORTANCE_WEIGHT=0.1                # 重要度の重み
STALE_DAYS_THRESHOLD=30              # 古い日数の閾値
STALE_MIN_ACCESS_COUNT=2             # 最低アクセス回数

# === ログ ===
LOG_FILE=logs/graphiti_mcp_server.log
LOG_LEVEL=INFO
```

> **完全な環境変数リスト**は `.env.example` を参照してください

### JSON 設定ファイル

バージョン管理が必要な設定に適しています（環境変数で上書き可能）：

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

## PM2 バックグラウンド実行

```bash
npm install -g pm2

pm2 start ecosystem.config.cjs      # 起動
pm2 status                           # 状態
pm2 logs graphiti-mcp-http           # リアルタイムログ
pm2 restart graphiti-mcp-http --update-env  # 再起動（.env を再読み込み）

pm2 save && pm2 startup              # 起動時の自動起動を設定
```

> **ヒント**：`.env` を変更した後は必ず `--update-env` フラグを使用して再起動する必要があります。さもないと環境変数は更新されません。

## Docker デプロイ

```bash
docker build -t graphiti-mcp .

# 注意: Docker コンテナは Neo4j と Ollama に接続できる必要がある
# host network を使用するのが最も簡単
docker run -p 8000:8000 --env-file .env --network host graphiti-mcp

# または外部サービスアドレスを明示的に指定
docker run -p 8000:8000 \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --env-file .env graphiti-mcp
```

## テスト

```bash
# すべてのテストを実行（183 個、約 1 秒）
uv run python -m pytest tests/

# 詳細出力
uv run python -m pytest tests/ -v

# 特定のテストのみ実行
uv run python -m pytest tests/test_content_preprocessor.py -v
uv run python -m pytest tests/test_new_features.py -v
uv run python -m pytest tests/test_unit.py -v
```

> **注意**：`test_integration_manual.py` 内の 3 つの async テストは `pytest-asyncio` のインストールが必要です。欠けている場合は Failed と表示されますが、他のテストには影響しません。`bench_deepseek_flash_vs_pro.py` はパフォーマンスベンチマークスクリプトであり、ユニットテストではありません。

## トラブルシューティング

### Neo4j 接続失敗

```bash
neo4j status                              # サービス状態を確認
cypher-shell -u neo4j -p your_password    # パスワードが正しいか確認
curl http://localhost:7474                 # HTTP ポートを確認
```

よくある原因：
- Neo4j が起動していない
- パスワードが間違っている（`.env` 内の `NEO4J_PASSWORD`）
- ポートが使用中、またはファイアウォールにブロックされている

### LLM 接続失敗

**Ollama モード：**
```bash
ollama serve                # Ollama サービスを起動
ollama list                 # インストール済みモデルを確認
ollama pull qwen2.5:3b      # 欠けているモデルをインストール
```

よくある原因：Ollama が起動していない、モデルがインストールされていない、GPU メモリ不足

**GLM モード：**
- `GLM_API_KEY` が正しいことを確認
- `GLM_EMBEDDING_DIMENSIONS=768` であることを確認（Neo4j ベクトルインデックスと一致させる必要がある）
- GLM API エンドポイント：`https://open.bigmodel.cn/api/paas/v4/`

**GROQ モード：**
- `GROQ_API_KEY` が正しいことを確認
- Rate Limit が頻繁な場合は GLM モードへの切り替えを検討
- GROQ は Embedding を提供しないため、Ollama 埋め込み器が利用可能であることを確認

**OpenRouter モード：**
- `OPENROUTER_API_KEY` が正しいこと、`OPENROUTER_MODEL` が有効なモデル ID であることを確認（https://openrouter.ai/models を参照）
- Embedding を提供しないため、Ollama 埋め込み器が利用可能であることを確認

**DeepSeek モード：**
- `DEEPSEEK_API_KEY` が正しいことを確認
- `Prompt must contain the word 'json'` が表示される場合：これは DeepSeek `json_object` モードの必須要件で、クライアントには予備の防護が内蔵されています。それでも表示される場合は、最新版の `src/deepseek_client.py` を使用していることを確認し、サービスを再起動してください
- Embedding を提供しないため、Ollama 埋め込み器が利用可能であることを確認

### MCP 接続エラー

`Invalid request parameters` または `Received request before initialization was complete` が表示される場合：

1. HTTP 伝送モードを使用していることを確認（**SSE は使用しないこと**）
2. クライアント設定が `"type": "http"`, `"url": "http://localhost:8000/mcp"` であることを確認
3. サービスを再起動：`pm2 restart graphiti-mcp-http --update-env`
4. Claude Code で `/mcp` を実行して再接続

### 記憶追加が遅い

- **Ollama**：モデルサイズを確認（`qwen2.5:3b` は `7b` より 5-10 倍速い）、GPU を使用していることを確認（`ollama ps`）
- **GLM**：各 add_episode は 10-20+ 回の LLM ネットワーク往復が必要。短文 ~22s は正常値
- **GROQ**：Rate Limit が大量のリトライを引き起こす。頻繁に使用する場合は GLM または Ollama への切り替えを推奨
- `background=true` を使用してブロックを回避
- `GRAPHITI_CHUNK_THRESHOLD` を下げて長文をより早く分割させる

### PM2 の問題

```bash
pm2 status                                        # 状態を確認
pm2 logs graphiti-mcp-http --err --lines 50        # エラーログ
lsof -i :8000                                     # ポート使用状況を確認
pm2 delete graphiti-mcp-http && pm2 start ecosystem.config.cjs  # 完全に再起動
```

## 開発診断ツール

```bash
uv run python tools/status_report.py           # 統合状態レポート（Neo4j + Ollama + 設定）
uv run python tools/validate_config.py         # .env と設定の完全性を検証
uv run python tools/performance_diagnose.py    # LLM パフォーマンス診断
uv run python tools/inspect_schema.py          # Neo4j インデックスと制約のチェック
uv run python tools/migrate_embeddings.py      # Embedding モデルの移行（モデル切り替え後にベクトルを再生成）
```

### Embedding モデルの移行

embedding モデルを切り替えた後（例: `nomic-embed-text` → `bge-m3`）、移行ツールを使用してすべての既存ベクトルを再生成し、検索品質の一貫性を確保できます：

```bash
# 移行が必要な数をプレビュー
uv run python tools/migrate_embeddings.py --dry-run

# 全量移行（中断ポイントからの再開をサポート）
uv run python tools/migrate_embeddings.py

# 指定した group のみ移行
uv run python tools/migrate_embeddings.py --group-id myproject

# 中断ポイントから継続（中断後に再実行）
uv run python tools/migrate_embeddings.py --resume
```

> **互換性**：`bge-m3` はネイティブで 1024 次元ですが、システムは既存の Neo4j ベクトルインデックスとの互換性のために自動的に 768 次元に切り詰めます。移行前後のデータは共存できますが、最適な検索品質を得るために完全な移行を実行することを推奨します。

## ドキュメント

- [ツール使用の指示](../使用工具的指令.md) — MCP ツール使用ガイドとベストプラクティス
- [Graphiti Memory Rules](../graphiti-memory-rules.md) — 記憶ルールの説明

## ライセンス

MIT License
