"""後端多國語系（i18n）模組測試。

涵蓋：
- 所有支援語言訊息字典 key 完全對齊（避免漏譯）。
- ``t()`` 翻譯與 fallback 行為（缺 key / 缺語言 / 格式化失敗皆不冒泡）。
- ``normalize_language()`` 別名與主標籤回退。
- ``parse_accept_language()`` 的 q 值排序、裸 zh、萬用字元與空字串處理。
"""

import pytest

from src.i18n import (
    MESSAGES,
    SUPPORTED_LANGUAGES,
    DEFAULT_LANGUAGE,
    LANGUAGE_DISPLAY_NAMES,
    normalize_language,
    parse_accept_language,
    t,
)


# ============================================================
# 字典完整性
# ============================================================

def test_supported_languages_all_present_in_messages():
    """SUPPORTED_LANGUAGES 中每個語言都要有對應字典。"""
    for lang in SUPPORTED_LANGUAGES:
        assert lang in MESSAGES, f"MESSAGES 缺少語言 {lang}"


def test_default_language_is_supported():
    assert DEFAULT_LANGUAGE in SUPPORTED_LANGUAGES
    assert DEFAULT_LANGUAGE in MESSAGES


def test_supported_languages_all_have_display_names():
    assert set(LANGUAGE_DISPLAY_NAMES) == set(SUPPORTED_LANGUAGES)
    for lang, name in LANGUAGE_DISPLAY_NAMES.items():
        assert name.strip(), f"{lang} display name is empty"


def test_all_languages_have_identical_keys():
    """四語言的 key 集合必須完全一致（基準為 DEFAULT_LANGUAGE）。"""
    base_keys = set(MESSAGES[DEFAULT_LANGUAGE].keys())
    for lang in SUPPORTED_LANGUAGES:
        keys = set(MESSAGES[lang].keys())
        missing = base_keys - keys
        extra = keys - base_keys
        assert not missing, f"{lang} 缺少 key: {sorted(missing)}"
        assert not extra, f"{lang} 多出 key: {sorted(extra)}"


def test_format_placeholders_aligned_across_languages():
    """同一 key 在四語言中的 ``{placeholder}`` 名稱集合需一致。"""
    import string

    def placeholders(tmpl: str) -> set:
        return {
            field
            for _, field, _, _ in string.Formatter().parse(tmpl)
            if field
        }

    for key in MESSAGES[DEFAULT_LANGUAGE]:
        base = placeholders(MESSAGES[DEFAULT_LANGUAGE][key])
        for lang in SUPPORTED_LANGUAGES:
            assert placeholders(MESSAGES[lang][key]) == base, (
                f"key {key!r} 在 {lang} 的佔位符與基準不一致"
            )


def test_no_empty_message_values():
    for lang in SUPPORTED_LANGUAGES:
        for key, val in MESSAGES[lang].items():
            assert val.strip(), f"{lang}/{key} 為空字串"


def test_no_internal_placeholder_tokens_leak_to_messages():
    for lang in SUPPORTED_LANGUAGES:
        for key, val in MESSAGES[lang].items():
            assert "__PH" not in val, f"{lang}/{key} 殘留內部 placeholder token: {val}"


def test_non_cjk_languages_do_not_contain_cjk_glyphs():
    import re

    cjk = re.compile(r"[\u4e00-\u9fff]")
    cjk_languages = {"zh-TW", "zh-CN", "ja", "ko"}
    for lang in SUPPORTED_LANGUAGES:
        if lang in cjk_languages:
            continue
        for key, val in MESSAGES[lang].items():
            assert not cjk.search(val), f"{lang}/{key} 含非預期漢字: {val}"


def test_generated_messages_do_not_contain_known_bad_fragments():
    import re

    bad_fragments = re.compile(
        r"Заметка|едгер|статіль|Эпізод|чанг|मेमोरी|एनडेटम|गँज़ाइल|"
        r"मूल चीर|ماریہ|کبیر|ملکی|معلوم نہ ہو گی|"
        r"μνημόνιο|ενσωμβ|μεταγωγ|Sukkerlag|oldelem|"
        r"Dubbeltoning|Tidskriv|মেঘাল্য|বৈংক|বৈংলা|ব্লাক্সে|ডিগ্রিউলেশন"
    )
    for lang in SUPPORTED_LANGUAGES:
        for key, val in MESSAGES[lang].items():
            assert not bad_fragments.search(val), f"{lang}/{key} 含已知壞片段: {val}"


def test_recipe_placeholder_is_not_repeated_or_standalone():
    for lang in SUPPORTED_LANGUAGES:
        for key, val in MESSAGES[lang].items():
            assert val.count("{recipe}") <= 1, f"{lang}/{key} 重複 recipe placeholder: {val}"
            if key == "search.unknown_recipe":
                assert val.strip() != "{recipe}", f"{lang}/{key} 只有 placeholder"


def test_non_english_generated_languages_do_not_fall_back_to_english():
    for lang in SUPPORTED_LANGUAGES:
        if lang in {"zh-TW", "en", "zh-CN", "ja"}:
            continue
        untranslated = [
            key
            for key, value in MESSAGES[lang].items()
            if value == MESSAGES["en"][key]
        ]
        assert not untranslated, f"{lang} 仍有英文 fallback: {untranslated}"


# ============================================================
# t() 翻譯與 fallback
# ============================================================

def test_t_basic_translation():
    assert t("connection.test_done", "en") == "Connection test complete"
    assert t("connection.test_done", "zh-TW") == "連接測試完成"
    assert t("connection.test_done", "ja") == "接続テストが完了しました"


def test_t_with_params():
    assert t("search.nodes_found", "en", count=3) == "Found 3 related node(s)"
    assert "5" in t("stale.found", "zh-TW", total=5)


def test_t_missing_key_returns_key_itself():
    assert t("nonexistent.key", "en") == "nonexistent.key"


def test_t_missing_language_falls_back_to_default():
    """不支援的語言碼會被正規化為預設語言。"""
    assert t("connection.test_done", "xx") == MESSAGES[DEFAULT_LANGUAGE][
        "connection.test_done"
    ]


def test_t_new_language_uses_supported_fallback_message():
    assert t("connection.test_done", "fr") == MESSAGES["fr"]["connection.test_done"]
    assert t("connection.test_done", "pt-BR") == MESSAGES["pt-BR"]["connection.test_done"]


def test_t_missing_params_does_not_raise():
    """缺少格式化參數時回傳未格式化模板，不冒泡成例外。"""
    result = t("search.nodes_found", "en")  # 缺 count
    assert "{count}" in result  # 未被替換但不報錯


def test_t_extra_params_ignored():
    assert t("connection.test_done", "en", unused="x") == "Connection test complete"


def test_t_default_language_argument():
    assert t("connection.test_done") == MESSAGES[DEFAULT_LANGUAGE][
        "connection.test_done"
    ]


def test_t_conflict_keys_distinct():
    summary = t("conflict.summary", "en", active=2, invalidated=1)
    conflict = t("conflict.summary_conflict", "en", active=2, invalidated=1)
    assert summary != conflict
    assert "conflict" in conflict.lower()


# ============================================================
# normalize_language
# ============================================================

@pytest.mark.parametrize("raw,expected", [
    ("zh", "zh-TW"),
    ("zh-TW", "zh-TW"),
    ("zh-Hant", "zh-TW"),
    ("zh-HK", "zh-TW"),
    ("zh-CN", "zh-CN"),
    ("zh-Hans", "zh-CN"),
    ("en", "en"),
    ("en-US", "en"),
    ("EN-GB", "en"),
    ("ja", "ja"),
    ("ja-JP", "ja"),
    ("pt-BR", "pt-BR"),
    ("pt", "pt-PT"),
    ("ko-KR", "ko"),
    ("es-MX", "es"),
    ("fr", "fr"),
    ("he-IL", "he"),
    ("iw", "he"),
    ("ar-SA", "ar"),
    ("uk-UA", "uk"),
    ("fil-PH", "tl"),
    ("id-ID", "id"),
    ("nb-NO", "no"),
    ("xx", "zh-TW"),       # 不支援 → 預設
    ("", "zh-TW"),
    (None, "zh-TW"),
])
def test_normalize_language(raw, expected):
    assert normalize_language(raw) == expected


def test_normalize_language_primary_subtag_fallback():
    """未在別名表但主標籤可命中（如 en-XX）→ 取主標籤。"""
    assert normalize_language("en-XX") == "en"
    assert normalize_language("ja-Foo") == "ja"


# ============================================================
# parse_accept_language
# ============================================================

def test_parse_accept_language_simple():
    assert parse_accept_language("en") == "en"
    assert parse_accept_language("zh-TW") == "zh-TW"


def test_parse_accept_language_q_value_ordering():
    """依 q 值由高到低選取最佳匹配。"""
    assert parse_accept_language("en;q=0.8,ja;q=0.9") == "ja"
    assert parse_accept_language("zh-TW,zh;q=0.9,en;q=0.8") == "zh-TW"


def test_parse_accept_language_no_q_defaults_to_one():
    """無 q 值視為 q=1.0，依出現順序取第一個命中者。"""
    assert parse_accept_language("ja,en") == "ja"


def test_parse_accept_language_bare_zh():
    assert parse_accept_language("zh") == "zh-TW"


def test_parse_accept_language_wildcard_ignored():
    """萬用字元 * 不應命中，落到下一個或 default。"""
    assert parse_accept_language("*") == DEFAULT_LANGUAGE
    assert parse_accept_language("*;q=1.0,ja;q=0.5") == "ja"


def test_parse_accept_language_empty_returns_default():
    assert parse_accept_language("") == DEFAULT_LANGUAGE
    assert parse_accept_language(None) == DEFAULT_LANGUAGE


def test_parse_accept_language_all_unmatched_returns_default():
    assert parse_accept_language("xx,yy,zz") == DEFAULT_LANGUAGE


def test_parse_accept_language_custom_default():
    assert parse_accept_language("xx", default="en") == "en"


def test_parse_accept_language_malformed_q_tolerated():
    """q 值格式錯誤時退回 q=1.0，不報錯。"""
    assert parse_accept_language("ja;q=abc") == "ja"


def test_parse_accept_language_new_languages():
    assert parse_accept_language("pt-BR,pt;q=0.8") == "pt-BR"
    assert parse_accept_language("pt;q=0.8") == "pt-PT"
    assert parse_accept_language("fil-PH") == "tl"
    assert parse_accept_language("he-IL") == "he"
