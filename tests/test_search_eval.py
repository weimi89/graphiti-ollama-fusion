#!/usr/bin/env python3
"""搜尋命中率評估核心度量測試（src/search_eval.py）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestReciprocalRank:
    def test_rank_positions(self):
        from src.search_eval import reciprocal_rank
        assert reciprocal_rank(["a", "b", "c"], "a", 10) == 1.0
        assert reciprocal_rank(["a", "b", "c"], "b", 10) == 0.5
        assert abs(reciprocal_rank(["a", "b", "c"], "c", 10) - 1 / 3) < 1e-9
        assert reciprocal_rank(["a", "b", "c"], "z", 10) == 0.0

    def test_beyond_k_not_counted(self):
        from src.search_eval import reciprocal_rank
        assert reciprocal_rank(["a", "b", "c"], "c", 2) == 0.0

    def test_empty_ranked(self):
        from src.search_eval import reciprocal_rank
        assert reciprocal_rank([], "a", 10) == 0.0


class TestComputeMetrics:
    def test_metrics(self):
        from src.search_eval import compute_metrics
        results = [(["t", "x"], "t"), (["x", "t"], "t"), (["x", "y"], "t")]
        m = compute_metrics("r", results, k=10, durations=[0.1, 0.2, 0.3])
        assert m.hits == 2
        assert m.total == 3
        assert abs(m.recall_at_k - 2 / 3) < 1e-9
        assert abs(m.mrr - (1.0 + 0.5 + 0.0) / 3) < 1e-9
        assert m.avg_duration == 0.2

    def test_perfect(self):
        from src.search_eval import compute_metrics
        m = compute_metrics("r", [(["t"], "t"), (["t", "y"], "t")], k=5)
        assert m.recall_at_k == 1.0
        assert m.mrr == 1.0

    def test_empty(self):
        from src.search_eval import compute_metrics
        m = compute_metrics("r", [], k=10)
        assert m.recall_at_k == 0.0
        assert m.mrr == 0.0
        assert m.total == 0


class TestFormatTable:
    def test_sorted_by_recall_desc(self):
        from src.search_eval import compute_metrics, format_comparison_table
        m_hi = compute_metrics("good", [(["t"], "t")], 10)
        m_lo = compute_metrics("bad", [(["x"], "t")], 10)
        table = format_comparison_table([m_lo, m_hi], 10)
        assert "recall@10" in table
        # 高 recall 的 recipe 應排在前面
        assert table.index("good") < table.index("bad")

    def test_empty(self):
        from src.search_eval import format_comparison_table
        assert "無" in format_comparison_table([], 10)
