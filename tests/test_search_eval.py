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


class TestGoldenPersistence:
    def test_round_trip(self, tmp_path):
        from src.search_eval import GoldenItem, load_golden, save_golden
        items = [
            GoldenItem(query="誰負責物流", target_uuid="u1", group_id="g1", target_name="黑貓", kind="node"),
            GoldenItem(query="X 與 Y 的關係", target_uuid="e1", group_id="g1", target_name="關係", kind="edge"),
        ]
        path = tmp_path / "golden.json"
        n = save_golden(items, str(path))
        assert n == 2
        loaded = load_golden(str(path))
        assert len(loaded) == 2
        assert loaded[0].query == "誰負責物流"
        assert loaded[0].kind == "node"
        assert loaded[1].kind == "edge"
        assert loaded[1].target_uuid == "e1"

    def test_kind_defaults_node_when_missing(self, tmp_path):
        import json
        from src.search_eval import load_golden
        path = tmp_path / "legacy.json"
        # 舊格式（無 kind 欄位）應預設 node
        path.write_text(json.dumps({
            "items": [{"query": "q", "target_uuid": "u", "group_id": "g"}]
        }), encoding="utf-8")
        loaded = load_golden(str(path))
        assert len(loaded) == 1
        assert loaded[0].kind == "node"

    def test_skips_incomplete_rows(self, tmp_path):
        import json
        from src.search_eval import load_golden
        path = tmp_path / "partial.json"
        path.write_text(json.dumps({"items": [
            {"query": "ok", "target_uuid": "u", "group_id": "g"},
            {"query": "missing uuid", "group_id": "g"},  # 缺 target_uuid → 跳過
        ]}), encoding="utf-8")
        loaded = load_golden(str(path))
        assert len(loaded) == 1
        assert loaded[0].query == "ok"


class TestBaselineRegression:
    def _metric(self, recipe, recall, mrr):
        from src.search_eval import RecipeMetrics
        return RecipeMetrics(recipe=recipe, recall_at_k=recall, mrr=mrr, hits=0, total=10)

    def test_no_baseline_marks_new(self):
        from src.search_eval import compare_to_baseline
        regs, lines = compare_to_baseline([self._metric("node_rrf", 0.8, 0.5)], None)
        assert regs == []
        assert any("無 baseline" in ln for ln in lines)

    def test_detects_recall_regression(self):
        from src.search_eval import compare_to_baseline, metrics_to_dict
        base = metrics_to_dict([self._metric("node_rrf", 0.90, 0.50)], k=10)
        regs, _ = compare_to_baseline([self._metric("node_rrf", 0.80, 0.50)], base, tol=0.05)
        assert len(regs) == 1
        assert regs[0]["recipe"] == "node_rrf"
        assert regs[0]["d_recall"] < 0

    def test_detects_mrr_regression(self):
        from src.search_eval import compare_to_baseline, metrics_to_dict
        base = metrics_to_dict([self._metric("node_rrf", 0.90, 0.60)], k=10)
        regs, _ = compare_to_baseline([self._metric("node_rrf", 0.90, 0.50)], base, tol=0.05)
        assert len(regs) == 1

    def test_within_tolerance_no_regression(self):
        from src.search_eval import compare_to_baseline, metrics_to_dict
        base = metrics_to_dict([self._metric("node_rrf", 0.90, 0.50)], k=10)
        # 下滑 0.02 < tol 0.05 → 不算回歸
        regs, _ = compare_to_baseline([self._metric("node_rrf", 0.88, 0.49)], base, tol=0.05)
        assert regs == []

    def test_improvement_no_regression(self):
        from src.search_eval import compare_to_baseline, metrics_to_dict
        base = metrics_to_dict([self._metric("node_rrf", 0.80, 0.50)], k=10)
        regs, _ = compare_to_baseline([self._metric("node_rrf", 0.95, 0.70)], base, tol=0.05)
        assert regs == []
