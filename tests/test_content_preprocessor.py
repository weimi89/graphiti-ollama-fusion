#!/usr/bin/env python3
"""
content_preprocessor 單元測試
==============================

測試智慧內容切分邏輯的正確性。
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.content_preprocessor import should_chunk, smart_chunk, ChunkResult


# ============================================================
# should_chunk 測試
# ============================================================


class TestShouldChunk:
    def test_short_text_no_chunk(self):
        assert should_chunk("短文本", threshold=800) is False

    def test_exact_threshold_no_chunk(self):
        text = "a" * 800
        assert should_chunk(text, threshold=800) is False

    def test_over_threshold_needs_chunk(self):
        text = "a" * 801
        assert should_chunk(text, threshold=800) is True

    def test_empty_text(self):
        assert should_chunk("", threshold=800) is False

    def test_whitespace_only(self):
        assert should_chunk("   \n\n  ", threshold=800) is False

    def test_custom_threshold(self):
        text = "a" * 500
        assert should_chunk(text, threshold=400) is True
        assert should_chunk(text, threshold=600) is False


# ============================================================
# smart_chunk 測試
# ============================================================


class TestSmartChunk:
    def test_short_text_not_chunked(self):
        result = smart_chunk("短文本", max_chunk_size=600, threshold=800)
        assert result.was_chunked is False
        assert result.chunks == ["短文本"]
        assert result.original_length == 3

    def test_empty_text(self):
        result = smart_chunk("", max_chunk_size=600, threshold=800)
        assert result.was_chunked is False
        assert result.chunks == []

    def test_paragraph_splitting(self):
        text = ("段落一" + "x" * 300) + "\n\n" + ("段落二" + "y" * 300) + "\n\n" + ("段落三" + "z" * 300)
        result = smart_chunk(text, max_chunk_size=400, threshold=100)
        assert result.was_chunked is True
        assert len(result.chunks) >= 2
        # 每段都不應超過 max_chunk_size 太多
        for chunk in result.chunks:
            assert len(chunk) <= 500  # 合併段落可能略超

    def test_short_paragraphs_merged(self):
        text = "短段一\n\n短段二\n\n短段三"
        result = smart_chunk(text, max_chunk_size=600, threshold=5)
        # 三個短段落應該被合併成一個 chunk
        assert len(result.chunks) == 1
        assert "短段一" in result.chunks[0]
        assert "短段二" in result.chunks[0]
        assert "短段三" in result.chunks[0]

    def test_mixed_lengths(self):
        short = "短段"
        long = "長段" + "a" * 500
        text = short + "\n\n" + long + "\n\n" + short
        result = smart_chunk(text, max_chunk_size=400, threshold=100)
        assert result.was_chunked is True
        assert len(result.chunks) >= 2

    def test_single_long_paragraph_sentence_split(self):
        # 單一超長段落，有句子邊界
        text = "第一句話。" * 50 + "第二句話。" * 50
        result = smart_chunk(text, max_chunk_size=100, threshold=50)
        assert result.was_chunked is True
        assert len(result.chunks) >= 2
        # 所有內容應被保留
        joined = "".join(result.chunks)
        assert "第一句話" in joined
        assert "第二句話" in joined

    def test_preserves_all_content(self):
        paragraphs = [f"段落{i}的內容" + "x" * 100 for i in range(5)]
        text = "\n\n".join(paragraphs)
        result = smart_chunk(text, max_chunk_size=200, threshold=100)
        # 所有段落關鍵內容都應存在於某個 chunk 中
        all_text = " ".join(result.chunks)
        for i in range(5):
            assert f"段落{i}的內容" in all_text

    def test_only_whitespace_paragraphs_filtered(self):
        text = "內容\n\n   \n\n更多內容"
        result = smart_chunk(text, max_chunk_size=600, threshold=5)
        for chunk in result.chunks:
            assert chunk.strip()

    def test_chunk_result_metadata(self):
        text = "a" * 1000
        result = smart_chunk(text, max_chunk_size=400, threshold=500)
        assert result.original_length == 1000
        assert result.was_chunked is True

    def test_no_chunk_below_threshold(self):
        text = "a" * 700
        result = smart_chunk(text, max_chunk_size=600, threshold=800)
        assert result.was_chunked is False
        assert result.chunks == [text]

    def test_real_world_example(self):
        """模擬真實的記憶內容切分場景"""
        text = """Web UI 20 項 UX 優化完成摘要

實現了以下改善：
1. 載入狀態動畫效果
2. 統計卡片點擊指針樣式
3. 刪除按鈕交互設計改進

技術細節：
- 使用 CSS @keyframes 實現骨架屏動畫
- 按鈕新增 hover 和 active 狀態
- 刪除操作新增二次確認對話框

測試驗證：
所有 20 項改善已在多種瀏覽器中測試通過。深色和淺色主題下均表現正常。響應式佈局在移動設備和桌面端均可正確顯示。"""

        result = smart_chunk(text, max_chunk_size=200, threshold=100)
        assert result.was_chunked is True
        assert len(result.chunks) >= 2
        # 確保內容完整
        all_text = " ".join(result.chunks)
        assert "載入狀態動畫" in all_text
        assert "測試驗證" in all_text
