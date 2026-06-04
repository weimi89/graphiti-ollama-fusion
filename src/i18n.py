"""後端多國語系（i18n）模組。

提供 REST API（依 Accept-Language）與 MCP 工具（依 SERVER_LANG 環境變數）
共用的訊息字典與翻譯函數。

設計要點：
- 支援語言：zh-TW（基準/fallback）、en、zh-CN、ja，以及多個新增目標語系。
- ``t(key, lang, **params)``：取對應語言模板並以 ``str.format`` 插值；
  缺 key 或缺語言時回退 zh-TW，再缺則回 key 本身；格式化失敗絕不冒泡成例外。
- ``parse_accept_language(header)``：解析 HTTP Accept-Language（含 q 值排序），
  對應到支援語言集，裸 ``zh`` 視為 ``zh-TW``。

新增語言時只需在 ``SUPPORTED_LANGUAGES`` / ``_ALIASES_BY_LANGUAGE`` 增加語言碼；
若尚未完成逐句翻譯，會先使用英文訊息作為該語言的 fallback。新增訊息時所有
語言會透過合成後的 ``MESSAGES`` 保持 key 對齊（``tests/test_i18n.py`` 會驗證）。
"""

from __future__ import annotations

from src.i18n_generated import GENERATED_MESSAGE_OVERRIDES

# 支援的語言碼（正規化形式）
SUPPORTED_LANGUAGES = (
    "zh-TW",
    "en",
    "zh-CN",
    "ja",
    "pt-PT",
    "pt-BR",
    "ko",
    "es",
    "de",
    "fr",
    "he",
    "ar",
    "ru",
    "pl",
    "cs",
    "nl",
    "tr",
    "uk",
    "vi",
    "tl",
    "id",
    "th",
    "hi",
    "bn",
    "ur",
    "ro",
    "sv",
    "it",
    "el",
    "hu",
    "fi",
    "da",
    "no",
)
DEFAULT_LANGUAGE = "zh-TW"
FALLBACK_LANGUAGE = "en"

LANGUAGE_DISPLAY_NAMES = {
    "zh-TW": "🇹🇼 繁體中文",
    "en": "English",
    "zh-CN": "🇨🇳 中文",
    "ja": "🇯🇵 日本語",
    "pt-PT": "🇵🇹 Português",
    "pt-BR": "🇧🇷 Português",
    "ko": "🇰🇷 한국어",
    "es": "🇪🇸 Español",
    "de": "🇩🇪 Deutsch",
    "fr": "🇫🇷 Français",
    "he": "🇮🇱 עברית",
    "ar": "🇸🇦 العربية",
    "ru": "🇷🇺 Русский",
    "pl": "🇵🇱 Polski",
    "cs": "🇨🇿 Čeština",
    "nl": "🇳🇱 Nederlands",
    "tr": "🇹🇷 Türkçe",
    "uk": "🇺🇦 Українська",
    "vi": "🇻🇳 Tiếng Việt",
    "tl": "🇵🇭 Tagalog",
    "id": "🇮🇩 Indonesia",
    "th": "🇹🇭 ไทย",
    "hi": "🇮🇳 हिन्दी",
    "bn": "🇧🇩 বাংলা",
    "ur": "🇵🇰 اردو",
    "ro": "🇷🇴 Română",
    "sv": "🇸🇪 Svenska",
    "it": "🇮🇹 Italiano",
    "el": "🇬🇷 Ελληνικά",
    "hu": "🇭🇺 Magyar",
    "fi": "🇫🇮 Suomi",
    "da": "🇩🇰 Dansk",
    "no": "🇳🇴 Norsk",
}

# Accept-Language / SERVER_LANG 別名 → 正規化語言碼（比對時一律轉小寫）
_ALIASES_BY_LANGUAGE = {
    "zh-TW": ("zh", "zh-tw", "zh-hant", "zh-hant-tw", "zh-hk", "zh-mo"),
    "en": ("en", "en-us", "en-gb", "en-au", "en-ca", "en-nz"),
    "zh-CN": ("zh-cn", "zh-hans", "zh-hans-cn", "zh-sg"),
    "ja": ("ja", "ja-jp"),
    "pt-PT": ("pt-pt", "pt"),
    "pt-BR": ("pt-br",),
    "ko": ("ko", "ko-kr"),
    "es": ("es", "es-es", "es-mx", "es-419"),
    "de": ("de", "de-de", "de-at", "de-ch"),
    "fr": ("fr", "fr-fr", "fr-ca", "fr-ch"),
    "he": ("he", "he-il", "iw", "iw-il"),
    "ar": ("ar", "ar-sa", "ar-ae", "ar-eg"),
    "ru": ("ru", "ru-ru"),
    "pl": ("pl", "pl-pl"),
    "cs": ("cs", "cs-cz"),
    "nl": ("nl", "nl-nl", "nl-be"),
    "tr": ("tr", "tr-tr"),
    "uk": ("uk", "uk-ua"),
    "vi": ("vi", "vi-vn"),
    "tl": ("tl", "tl-ph", "fil", "fil-ph"),
    "id": ("id", "id-id", "in", "in-id"),
    "th": ("th", "th-th"),
    "hi": ("hi", "hi-in"),
    "bn": ("bn", "bn-bd", "bn-in"),
    "ur": ("ur", "ur-pk", "ur-in"),
    "ro": ("ro", "ro-ro"),
    "sv": ("sv", "sv-se"),
    "it": ("it", "it-it"),
    "el": ("el", "el-gr"),
    "hu": ("hu", "hu-hu"),
    "fi": ("fi", "fi-fi"),
    "da": ("da", "da-dk"),
    "no": ("no", "nb", "nb-no", "nn", "nn-no", "no-no"),
}
_ALIAS = {
    alias: language
    for language, aliases in _ALIASES_BY_LANGUAGE.items()
    for alias in aliases
}

# ============================================================
# 訊息字典（key 採 group.action 扁平命名）
# ============================================================

MESSAGES: dict[str, dict[str, str]] = {
    "zh-TW": {
        # memory
        "memory.added": "記憶 '{name}' 已成功添加",
        "memory.added_full": "記憶 '{name}' 已成功添加（完整模式）",
        "memory.added_full_chunked": "記憶 '{name}' 已成功添加（完整模式，{count} 段，bulk 並發）",
        "memory.add_safe_failed": "安全記憶添加失敗: {reason}",
        "memory.duplicate_detected": "偵測到重複記憶: {detail}",
        "memory.name_content_required": "名稱和內容為必填",
        "memory.queued_background": "記憶 '{name}' 已加入背景處理佇列",
        "memory.note_force": "使用 force=True 跳過去重檢查強制添加",
        "memory.note_safe_mode": "使用安全模式，跳過實體提取",
        "memory.note_full_mode": "使用完整模式，包含實體提取和關係建立",
        "memory.note_chunked": "長文本自動切分為 {count} 段，使用 bulk 並發處理",
        # episode / fact / node / edge / entity
        "episode.deleted": "記憶片段 {uuid} 已刪除（含關聯邊）",
        "episode.deleted_simple": "記憶片段 {uuid} 已成功刪除",
        "episode.not_found": "記憶片段 {uuid} 不存在",
        "fact.deleted": "事實 {uuid} 已刪除",
        "fact.not_found": "事實 {uuid} 不存在",
        "node.deleted": "實體節點 {uuid} 已刪除（含關聯邊）",
        "node.not_found": "實體節點 {uuid} 不存在",
        "edge.deleted": "實體邊 {uuid} 已成功刪除",
        "edge.delete_failed": "刪除實體邊失敗: {uuid}",
        "entity.not_found": "找不到實體: {name}",
        "episodes.found": "找到 {count} 個記憶片段",
        # bulk
        "bulk.empty_list": "episodes 列表不能為空",
        "bulk.invalid_format": "第 {index} 個 episode 格式錯誤，需包含 name 和 content 欄位",
        "bulk.added": "成功批量添加 {count} 條記憶",
        "bulk.queued_background": "批量添加 {count} 條記憶已加入背景處理",
        "bulk.failed": "批量添加失敗: {reason}",
        # triplet
        "triplet.added": "三元組已添加: {source} --[{relation}]--> {target}",
        "triplet.fields_required": "source_name, relation_name, target_name, fact 為必填",
        # search
        "search.missing_query": "缺少搜尋參數 q",
        "search.rate_limited": "搜尋請求過於頻繁，請稍後再試",
        "search.timeout": "搜尋超時，請縮小查詢範圍",
        "search.unknown_recipe": "未知的搜尋策略: {recipe}",
        "search.advanced_done": "進階搜尋完成（策略: {recipe}）",
        "search.nodes_found": "找到 {count} 個相關節點",
        "search.facts_found": "找到 {count} 個相關事實",
        # community
        "community.built": "社群建構完成",
        "community.built_detail": "社群建構完成: {node_count} 個社群, {edge_count} 個連接",
        "community.queued_background": "社群建構已加入背景處理",
        "community.build_failed": "社群建構失敗",
        # conflict
        "conflict.summary": "發現 {active} 個有效事實和 {invalidated} 個已失效事實",
        "conflict.summary_conflict": "發現 {active} 個有效事實和 {invalidated} 個已失效事實，存在衝突！",
        # node_edges
        "node_edges.found": "找到 {inbound} 個入邊和 {outbound} 個出邊",
        # group / graph
        "group.cleared": "群組 {group_id} 已清除",
        "graph.missing_uuid": "缺少參數 uuid",
        "graph.cleared_groups": "已清除分組: {groups}",
        "graph.cleared_all": "圖資料庫已完全清除",
        "graph.clear_failed": "清除圖資料庫失敗",
        # stale / connection / status / task / system
        "stale.found": "找到 {total} 個過時記憶",
        "stale.note_cleanup": "使用 cleanup_stale_memories() 清理過時記憶",
        "connection.test_done": "連接測試完成",
        "status.check_failed": "服務狀態檢查失敗",
        "task.not_found": "找不到任務 {task_id}",
        "task.note_query_status": "使用 get_memory_task_status(task_id) 查詢進度",
        "system.index_missing": "web/index.html 不存在",
        # common / ask
        "common.all": "(全部)",
        "ask.context_entities": "## 相關實體",
        "ask.context_facts": "## 相關事實",
        "ask.no_knowledge": "（未找到相關知識）",
    },
    "en": {
        # memory
        "memory.added": "Memory '{name}' added successfully",
        "memory.added_full": "Memory '{name}' added successfully (full mode)",
        "memory.added_full_chunked": "Memory '{name}' added successfully (full mode, {count} chunks, bulk concurrent)",
        "memory.add_safe_failed": "Safe memory add failed: {reason}",
        "memory.duplicate_detected": "Duplicate memory detected: {detail}",
        "memory.name_content_required": "Name and content are required",
        "memory.queued_background": "Memory '{name}' queued for background processing",
        "memory.note_force": "Skipped deduplication check (force=True)",
        "memory.note_safe_mode": "Safe mode used; entity extraction skipped",
        "memory.note_full_mode": "Full mode used; includes entity extraction and relationship building",
        "memory.note_chunked": "Long text was split into {count} chunks and processed concurrently in bulk",
        # episode / fact / node / edge / entity
        "episode.deleted": "Episode {uuid} deleted (including related edges)",
        "episode.deleted_simple": "Episode {uuid} deleted successfully",
        "episode.not_found": "Episode {uuid} not found",
        "fact.deleted": "Fact {uuid} deleted",
        "fact.not_found": "Fact {uuid} not found",
        "node.deleted": "Entity node {uuid} deleted (including related edges)",
        "node.not_found": "Entity node {uuid} not found",
        "edge.deleted": "Entity edge {uuid} deleted successfully",
        "edge.delete_failed": "Failed to delete entity edge: {uuid}",
        "entity.not_found": "Entity not found: {name}",
        "episodes.found": "Found {count} episode(s)",
        # bulk
        "bulk.empty_list": "The episodes list cannot be empty",
        "bulk.invalid_format": "Episode #{index} has invalid format; it must include 'name' and 'content' fields",
        "bulk.added": "Successfully bulk-added {count} memories",
        "bulk.queued_background": "Bulk add of {count} memories queued for background processing",
        "bulk.failed": "Bulk add failed: {reason}",
        # triplet
        "triplet.added": "Triplet added: {source} --[{relation}]--> {target}",
        "triplet.fields_required": "source_name, relation_name, target_name and fact are required",
        # search
        "search.missing_query": "Missing search parameter 'q'",
        "search.rate_limited": "Too many search requests; please try again later",
        "search.timeout": "Search timed out; please narrow your query",
        "search.unknown_recipe": "Unknown search recipe: {recipe}",
        "search.advanced_done": "Advanced search complete (recipe: {recipe})",
        "search.nodes_found": "Found {count} related node(s)",
        "search.facts_found": "Found {count} related fact(s)",
        # community
        "community.built": "Community building complete",
        "community.built_detail": "Community building complete: {node_count} communities, {edge_count} connections",
        "community.queued_background": "Community building queued for background processing",
        "community.build_failed": "Community building failed",
        # conflict
        "conflict.summary": "Found {active} valid fact(s) and {invalidated} invalidated fact(s)",
        "conflict.summary_conflict": "Found {active} valid fact(s) and {invalidated} invalidated fact(s) — conflict exists!",
        # node_edges
        "node_edges.found": "Found {inbound} inbound edge(s) and {outbound} outbound edge(s)",
        # group / graph
        "group.cleared": "Group {group_id} cleared",
        "graph.missing_uuid": "Missing parameter 'uuid'",
        "graph.cleared_groups": "Cleared groups: {groups}",
        "graph.cleared_all": "Graph database fully cleared",
        "graph.clear_failed": "Failed to clear graph database",
        # stale / connection / status / task / system
        "stale.found": "Found {total} stale memory(ies)",
        "stale.note_cleanup": "Use cleanup_stale_memories() to clean up stale memories",
        "connection.test_done": "Connection test complete",
        "status.check_failed": "Service status check failed",
        "task.not_found": "Task {task_id} not found",
        "task.note_query_status": "Use get_memory_task_status(task_id) to check progress",
        "system.index_missing": "web/index.html not found",
        # common / ask
        "common.all": "(All)",
        "ask.context_entities": "## Related Entities",
        "ask.context_facts": "## Related Facts",
        "ask.no_knowledge": "(No related knowledge found)",
    },
    "zh-CN": {
        # memory
        "memory.added": "记忆 '{name}' 已成功添加",
        "memory.added_full": "记忆 '{name}' 已成功添加（完整模式）",
        "memory.added_full_chunked": "记忆 '{name}' 已成功添加（完整模式，{count} 段，bulk 并发）",
        "memory.add_safe_failed": "安全记忆添加失败: {reason}",
        "memory.duplicate_detected": "检测到重复记忆: {detail}",
        "memory.name_content_required": "名称和内容为必填",
        "memory.queued_background": "记忆 '{name}' 已加入后台处理队列",
        "memory.note_force": "使用 force=True 跳过去重检查强制添加",
        "memory.note_safe_mode": "使用安全模式，跳过实体提取",
        "memory.note_full_mode": "使用完整模式，包含实体提取和关系建立",
        "memory.note_chunked": "长文本自动切分为 {count} 段，使用 bulk 并发处理",
        # episode / fact / node / edge / entity
        "episode.deleted": "记忆片段 {uuid} 已删除（含关联边）",
        "episode.deleted_simple": "记忆片段 {uuid} 已成功删除",
        "episode.not_found": "记忆片段 {uuid} 不存在",
        "fact.deleted": "事实 {uuid} 已删除",
        "fact.not_found": "事实 {uuid} 不存在",
        "node.deleted": "实体节点 {uuid} 已删除（含关联边）",
        "node.not_found": "实体节点 {uuid} 不存在",
        "edge.deleted": "实体边 {uuid} 已成功删除",
        "edge.delete_failed": "删除实体边失败: {uuid}",
        "entity.not_found": "找不到实体: {name}",
        "episodes.found": "找到 {count} 个记忆片段",
        # bulk
        "bulk.empty_list": "episodes 列表不能为空",
        "bulk.invalid_format": "第 {index} 个 episode 格式错误，需包含 name 和 content 字段",
        "bulk.added": "成功批量添加 {count} 条记忆",
        "bulk.queued_background": "批量添加 {count} 条记忆已加入后台处理",
        "bulk.failed": "批量添加失败: {reason}",
        # triplet
        "triplet.added": "三元组已添加: {source} --[{relation}]--> {target}",
        "triplet.fields_required": "source_name, relation_name, target_name, fact 为必填",
        # search
        "search.missing_query": "缺少搜索参数 q",
        "search.rate_limited": "搜索请求过于频繁，请稍后再试",
        "search.timeout": "搜索超时，请缩小查询范围",
        "search.unknown_recipe": "未知的搜索策略: {recipe}",
        "search.advanced_done": "高级搜索完成（策略: {recipe}）",
        "search.nodes_found": "找到 {count} 个相关节点",
        "search.facts_found": "找到 {count} 个相关事实",
        # community
        "community.built": "社群建构完成",
        "community.built_detail": "社群建构完成: {node_count} 个社群, {edge_count} 个连接",
        "community.queued_background": "社群建构已加入后台处理",
        "community.build_failed": "社群建构失败",
        # conflict
        "conflict.summary": "发现 {active} 个有效事实和 {invalidated} 个已失效事实",
        "conflict.summary_conflict": "发现 {active} 个有效事实和 {invalidated} 个已失效事实，存在冲突！",
        # node_edges
        "node_edges.found": "找到 {inbound} 个入边和 {outbound} 个出边",
        # group / graph
        "group.cleared": "群组 {group_id} 已清除",
        "graph.missing_uuid": "缺少参数 uuid",
        "graph.cleared_groups": "已清除分组: {groups}",
        "graph.cleared_all": "图数据库已完全清除",
        "graph.clear_failed": "清除图数据库失败",
        # stale / connection / status / task / system
        "stale.found": "找到 {total} 个过时记忆",
        "stale.note_cleanup": "使用 cleanup_stale_memories() 清理过时记忆",
        "connection.test_done": "连接测试完成",
        "status.check_failed": "服务状态检查失败",
        "task.not_found": "找不到任务 {task_id}",
        "task.note_query_status": "使用 get_memory_task_status(task_id) 查询进度",
        "system.index_missing": "web/index.html 不存在",
        # common / ask
        "common.all": "(全部)",
        "ask.context_entities": "## 相关实体",
        "ask.context_facts": "## 相关事实",
        "ask.no_knowledge": "（未找到相关知识）",
    },
    "ja": {
        # memory
        "memory.added": "メモリ '{name}' を追加しました",
        "memory.added_full": "メモリ '{name}' を追加しました（フルモード）",
        "memory.added_full_chunked": "メモリ '{name}' を追加しました（フルモード、{count} 分割、bulk 並列）",
        "memory.add_safe_failed": "セーフモードでのメモリ追加に失敗しました: {reason}",
        "memory.duplicate_detected": "重複したメモリを検出しました: {detail}",
        "memory.name_content_required": "名前と内容は必須です",
        "memory.queued_background": "メモリ '{name}' をバックグラウンド処理キューに追加しました",
        "memory.note_force": "force=True により重複チェックをスキップして追加しました",
        "memory.note_safe_mode": "セーフモードを使用し、エンティティ抽出をスキップしました",
        "memory.note_full_mode": "フルモードを使用し、エンティティ抽出と関係構築を含みます",
        "memory.note_chunked": "長文を {count} 分割し、bulk で並列処理しました",
        # episode / fact / node / edge / entity
        "episode.deleted": "エピソード {uuid} を削除しました（関連エッジを含む）",
        "episode.deleted_simple": "エピソード {uuid} を削除しました",
        "episode.not_found": "エピソード {uuid} が見つかりません",
        "fact.deleted": "ファクト {uuid} を削除しました",
        "fact.not_found": "ファクト {uuid} が見つかりません",
        "node.deleted": "エンティティノード {uuid} を削除しました（関連エッジを含む）",
        "node.not_found": "エンティティノード {uuid} が見つかりません",
        "edge.deleted": "エンティティエッジ {uuid} を削除しました",
        "edge.delete_failed": "エンティティエッジの削除に失敗しました: {uuid}",
        "entity.not_found": "エンティティが見つかりません: {name}",
        "episodes.found": "{count} 件のエピソードが見つかりました",
        # bulk
        "bulk.empty_list": "episodes リストを空にすることはできません",
        "bulk.invalid_format": "{index} 番目の episode の形式が不正です。'name' と 'content' フィールドが必要です",
        "bulk.added": "{count} 件のメモリを一括追加しました",
        "bulk.queued_background": "{count} 件のメモリの一括追加をバックグラウンド処理に追加しました",
        "bulk.failed": "一括追加に失敗しました: {reason}",
        # triplet
        "triplet.added": "トリプルを追加しました: {source} --[{relation}]--> {target}",
        "triplet.fields_required": "source_name、relation_name、target_name、fact は必須です",
        # search
        "search.missing_query": "検索パラメータ q がありません",
        "search.rate_limited": "検索リクエストが頻繁すぎます。しばらくしてから再試行してください",
        "search.timeout": "検索がタイムアウトしました。クエリ範囲を絞ってください",
        "search.unknown_recipe": "不明な検索レシピです: {recipe}",
        "search.advanced_done": "高度な検索が完了しました（レシピ: {recipe}）",
        "search.nodes_found": "{count} 件の関連ノードが見つかりました",
        "search.facts_found": "{count} 件の関連ファクトが見つかりました",
        # community
        "community.built": "コミュニティ構築が完了しました",
        "community.built_detail": "コミュニティ構築が完了しました: {node_count} 個のコミュニティ、{edge_count} 個の接続",
        "community.queued_background": "コミュニティ構築をバックグラウンド処理に追加しました",
        "community.build_failed": "コミュニティ構築に失敗しました",
        # conflict
        "conflict.summary": "{active} 件の有効なファクトと {invalidated} 件の失効したファクトが見つかりました",
        "conflict.summary_conflict": "{active} 件の有効なファクトと {invalidated} 件の失効したファクトが見つかりました。矛盾があります！",
        # node_edges
        "node_edges.found": "{inbound} 件の入力エッジと {outbound} 件の出力エッジが見つかりました",
        # group / graph
        "group.cleared": "グループ {group_id} をクリアしました",
        "graph.missing_uuid": "パラメータ uuid がありません",
        "graph.cleared_groups": "クリアしたグループ: {groups}",
        "graph.cleared_all": "グラフデータベースを完全にクリアしました",
        "graph.clear_failed": "グラフデータベースのクリアに失敗しました",
        # stale / connection / status / task / system
        "stale.found": "{total} 件の古いメモリが見つかりました",
        "stale.note_cleanup": "cleanup_stale_memories() で古いメモリをクリーンアップしてください",
        "connection.test_done": "接続テストが完了しました",
        "status.check_failed": "サービス状態のチェックに失敗しました",
        "task.not_found": "タスク {task_id} が見つかりません",
        "task.note_query_status": "get_memory_task_status(task_id) で進捗を確認してください",
        "system.index_missing": "web/index.html が見つかりません",
        # common / ask
        "common.all": "(すべて)",
        "ask.context_entities": "## 関連エンティティ",
        "ask.context_facts": "## 関連ファクト",
        "ask.no_knowledge": "（関連する知識は見つかりませんでした）",
    },
}

# 人工微調覆蓋層（優先級高於 generated）。多數語言已由 src/i18n_generated.py 完全本地化，
# 此處僅保留 generated 層仍有殘留或需特定人工措辭的少數語言。
MANUAL_MESSAGE_OVERRIDES: dict[str, dict[str, str]] = {
    "he": {
        "ask.context_entities": "## ישויות קשורות",
        "ask.no_knowledge": "(לא נמצא ידע קשור)",
        "community.built_detail": "בניית הקהילות הושלמה: {node_count} קהילות, {edge_count} חיבורים",
        "episode.deleted": "הפרק {uuid} נמחק (כולל קשתות קשורות)",
        "memory.name_content_required": "שם ותוכן הם שדות חובה",
        "memory.note_safe_mode": "נעשה שימוש במצב בטוח; חילוץ ישויות דולג",
        "node.deleted": "צומת הישות {uuid} נמחק (כולל קשתות קשורות)",
        "node_edges.found": "נמצאו {inbound} קשתות נכנסות ו-{outbound} קשתות יוצאות",
        "search.advanced_done": "החיפוש המתקדם הושלם (מתכון: {recipe})",
        "search.rate_limited": "יותר מדי בקשות חיפוש; נסה שוב מאוחר יותר",
        "search.timeout": "החיפוש חרג מזמן ההמתנה; צמצם את השאילתה",
    },
    "uk": {
        "ask.context_entities": "## Пов'язані сутності",
        "ask.context_facts": "## Пов'язані факти",
        "ask.no_knowledge": "(Пов'язаних знань не знайдено)",
        "bulk.added": "Успішно пакетно додано {count} спогадів",
        "bulk.failed": "Пакетне додавання не вдалося: {reason}",
        "bulk.queued_background": "Пакетне додавання {count} спогадів поставлено в чергу фонового оброблення",
        "community.build_failed": "Побудова спільнот не вдалася",
        "community.built": "Побудову спільнот завершено",
        "community.built_detail": "Побудову спільнот завершено: {node_count} спільнот, {edge_count} зв'язків",
        "community.queued_background": "Побудову спільнот поставлено в чергу фонового оброблення",
        "conflict.summary": "Знайдено {active} чинних фактів і {invalidated} скасованих фактів",
        "conflict.summary_conflict": "Знайдено {active} чинних фактів і {invalidated} скасованих фактів — існує конфлікт!",
        "connection.test_done": "Тест підключення завершено",
        "edge.delete_failed": "Не вдалося видалити ребро сутності: {uuid}",
        "edge.deleted": "Ребро сутності {uuid} успішно видалено",
        "entity.not_found": "Сутність не знайдено: {name}",
        "episode.deleted": "Епізод {uuid} видалено (разом із пов'язаними ребрами)",
        "episode.deleted_simple": "Епізод {uuid} успішно видалено",
        "episode.not_found": "Епізод {uuid} не знайдено",
        "episodes.found": "Знайдено епізодів: {count}",
        "fact.deleted": "Факт {uuid} видалено",
        "fact.not_found": "Факт {uuid} не знайдено",
        "graph.clear_failed": "Не вдалося очистити графову базу даних",
        "graph.cleared_all": "Графову базу даних повністю очищено",
        "graph.missing_uuid": "Відсутній параметр 'uuid'",
        "memory.add_safe_failed": "Безпечне додавання пам'яті не вдалося: {reason}",
        "memory.added": "Пам'ять '{name}' успішно додано",
        "memory.added_full": "Пам'ять '{name}' успішно додано (повний режим)",
        "memory.added_full_chunked": "Пам'ять '{name}' успішно додано (повний режим, {count} фрагментів, паралельна bulk-обробка)",
        "memory.duplicate_detected": "Виявлено дубль пам'яті: {detail}",
        "memory.name_content_required": "Назва і вміст є обов'язковими",
        "memory.note_chunked": "Довгий текст розділено на {count} фрагментів і паралельно оброблено в bulk-режимі",
        "memory.note_force": "Перевірку на дублікати пропущено (force=True)",
        "memory.note_full_mode": "Використано повний режим; включено вилучення сутностей і побудову зв'язків",
        "memory.note_safe_mode": "Використано безпечний режим; вилучення сутностей пропущено",
        "memory.queued_background": "Пам'ять '{name}' поставлено в чергу фонового оброблення",
        "node.deleted": "Вузол сутності {uuid} видалено (разом із пов'язаними ребрами)",
        "node.not_found": "Вузол сутності {uuid} не знайдено",
        "node_edges.found": "Знайдено {inbound} вхідних ребер і {outbound} вихідних ребер",
        "search.advanced_done": "Розширений пошук завершено (стратегія: {recipe})",
        "search.facts_found": "Знайдено пов'язаних фактів: {count}",
        "search.missing_query": "Відсутній параметр пошуку 'q'",
        "search.nodes_found": "Знайдено пов'язаних вузлів: {count}",
        "search.rate_limited": "Забагато пошукових запитів; повторіть пізніше",
        "search.timeout": "Пошук перевищив час очікування; звузьте запит",
        "search.unknown_recipe": "Невідома стратегія пошуку: {recipe}",
        "stale.found": "Знайдено застарілих записів пам'яті: {total}",
        "stale.note_cleanup": "Використайте cleanup_stale_memories(), щоб очистити застарілу пам'ять",
        "status.check_failed": "Перевірка стану сервісу не вдалася",
        "triplet.added": "Трійку додано: {source} --[{relation}]--> {target}",
        "triplet.fields_required": "source_name, relation_name, target_name і fact є обов'язковими",
    },
    "sv": {
        "bulk.added": "{count} minnen lades till i bulk",
        "bulk.failed": "Bulk-inläggning misslyckades: {reason}",
        "bulk.queued_background": "Bulk-inläggning av {count} minnen har lagts i kö för bakgrundsbehandling",
        "common.all": "(Alla)",
        "connection.test_done": "Anslutningstestet är klart",
        "graph.missing_uuid": "Parametern 'uuid' saknas",
        "memory.add_safe_failed": "Säker minnesinläggning misslyckades: {reason}",
        "memory.added": "Minnet '{name}' har lagts till",
        "memory.added_full": "Minnet '{name}' har lagts till (fullständigt läge)",
        "memory.added_full_chunked": "Minnet '{name}' har lagts till (fullständigt läge, {count} delar, parallell bulkbehandling)",
        "memory.duplicate_detected": "Dubblettminne upptäckt: {detail}",
        "memory.note_chunked": "Lång text delades upp i {count} delar och behandlades parallellt i bulk",
        "memory.note_full_mode": "Fullständigt läge användes; inkluderar entitetsextrahering och relationsbygge",
        "memory.note_safe_mode": "Säkert läge användes; entitetsextrahering hoppades över",
        "memory.queued_background": "Minnet '{name}' har lagts i kö för bakgrundsbehandling",
        "search.advanced_done": "Avancerad sökning klar (strategi: {recipe})",
        "search.unknown_recipe": "Okänd sökstrategi: {recipe}",
        "stale.found": "Hittade {total} inaktuella minnen",
        "stale.note_cleanup": "Använd cleanup_stale_memories() för att rensa inaktuella minnen",
        "task.not_found": "Uppgiften {task_id} hittades inte",
    },
    "fi": {
        "ask.context_entities": "## Liittyvät entiteetit",
        "ask.context_facts": "## Liittyvät faktat",
        "ask.no_knowledge": "(Liittyvää tietoa ei löytynyt)",
        "bulk.added": "{count} muistia lisättiin bulk-toiminnolla",
        "bulk.failed": "Bulk-lisäys epäonnistui: {reason}",
        "bulk.queued_background": "{count} muistin bulk-lisäys asetettiin taustakäsittelyjonoon",
        "connection.test_done": "Yhteystesti valmis",
        "search.advanced_done": "Tarkennettu haku valmis (strategia: {recipe})",
        "search.unknown_recipe": "Tuntematon hakustrategia: {recipe}",
        "task.not_found": "Tehtävää {task_id} ei löytynyt",
    },
}

for language in SUPPORTED_LANGUAGES:
    if language == FALLBACK_LANGUAGE:
        continue
    MESSAGES[language] = {
        **MESSAGES[FALLBACK_LANGUAGE],
        **MESSAGES.get(language, {}),
        **GENERATED_MESSAGE_OVERRIDES.get(language, {}),
        **MANUAL_MESSAGE_OVERRIDES.get(language, {}),
    }


def normalize_language(lang: str | None) -> str:
    """將任意語言碼正規化為支援語言之一，無法對應時回傳預設語言。"""
    if not lang:
        return DEFAULT_LANGUAGE
    code = lang.strip().lower()
    if code in _ALIAS:
        return _ALIAS[code]
    # 退而求其次：取主標籤（primary-subtag → primary）
    primary = code.split("-", 1)[0]
    if primary in _ALIAS:
        return _ALIAS[primary]
    return DEFAULT_LANGUAGE


def parse_accept_language(header: str | None, default: str = DEFAULT_LANGUAGE) -> str:
    """解析 HTTP ``Accept-Language`` header，回傳最佳匹配的支援語言碼。

    依 RFC 7231：無 q 值預設 q=1.0，依 q 由高到低排序後取第一個能命中支援集者。
    例：``"zh-TW,zh;q=0.9,en;q=0.8"`` → ``"zh-TW"``；裸 ``zh`` → ``zh-TW``；
    空字串或全不匹配 → ``default``。
    """
    if not header:
        return default

    parsed: list[tuple[float, int, str]] = []
    for order, part in enumerate(header.split(",")):
        token = part.strip()
        if not token:
            continue
        tag, _, params = token.partition(";")
        tag = tag.strip().lower()
        if not tag or tag == "*":
            continue
        q = 1.0
        params = params.strip()
        if params.lower().startswith("q="):
            try:
                q = float(params[2:])
            except (ValueError, IndexError):
                q = 1.0
        # order 作為次要排序鍵，確保穩定排序（q 相同時保留原始順序）
        parsed.append((q, order, tag))

    # q 由高到低；q 相同時依出現順序
    parsed.sort(key=lambda x: (-x[0], x[1]))

    for _q, _order, tag in parsed:
        if tag in _ALIAS:
            return _ALIAS[tag]
        primary = tag.split("-", 1)[0]
        if primary in _ALIAS:
            return _ALIAS[primary]

    return default


def t(key: str, lang: str = DEFAULT_LANGUAGE, **params) -> str:
    """翻譯 ``key`` 為 ``lang`` 語言並插入參數。

    fallback 順序：``MESSAGES[lang][key]`` → ``MESSAGES[zh-TW][key]`` → ``key``。
    ``str.format`` 失敗（參數不齊或資料含 ``{}``）時回傳未格式化模板，
    絕不讓翻譯失敗冒泡成例外。
    """
    lang = normalize_language(lang)
    template = MESSAGES.get(lang, {}).get(key)
    if template is None:
        template = MESSAGES[DEFAULT_LANGUAGE].get(key, key)
    if not params:
        return template
    try:
        return template.format(**params)
    except (KeyError, IndexError, ValueError):
        return template
