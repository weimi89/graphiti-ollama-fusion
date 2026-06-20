"""
搜尋命中率評估核心
==================

提供與 I/O 解耦的純函數，計算 recall@k、MRR 等檢索品質度量，供
tools/evaluate_search.py 對不同 search recipe 做 A/B 對比。

設計為純資料處理（不碰 Neo4j/LLM），以便單元測試。
"""

from dataclasses import dataclass, field
from typing import List, Sequence, Tuple


@dataclass
class GoldenItem:
    """一筆評估樣本：query 與其預期應命中的目標 uuid。"""

    query: str
    target_uuid: str
    group_id: str
    target_name: str = ""


@dataclass
class RecipeMetrics:
    """單一 recipe 的彙總度量。"""

    recipe: str
    recall_at_k: float
    mrr: float
    hits: int
    total: int
    avg_duration: float = 0.0
    per_query: List[float] = field(default_factory=list)  # 每筆的 reciprocal rank


def reciprocal_rank(ranked_uuids: Sequence[str], target_uuid: str, k: int) -> float:
    """目標在 top-k 中的 reciprocal rank（1/排名）；不在則 0。"""
    for i, uuid in enumerate(ranked_uuids[:k]):
        if uuid == target_uuid:
            return 1.0 / (i + 1)
    return 0.0


def compute_metrics(
    recipe: str,
    results: Sequence[Tuple[Sequence[str], str]],
    k: int,
    durations: Sequence[float] = (),
) -> RecipeMetrics:
    """
    彙總一個 recipe 的度量。

    Args:
        recipe: recipe 名稱
        results: 每筆 (排序後的 uuid 清單, 目標 uuid)
        k: top-k
        durations: 每筆搜尋耗時（可選）

    Returns:
        RecipeMetrics: recall@k、MRR、命中數等
    """
    rr_list = [reciprocal_rank(ranked, target, k) for ranked, target in results]
    hits = sum(1 for rr in rr_list if rr > 0)
    total = len(rr_list)
    denom = total or 1
    avg_dur = sum(durations) / len(durations) if durations else 0.0
    return RecipeMetrics(
        recipe=recipe,
        recall_at_k=hits / denom,
        mrr=sum(rr_list) / denom,
        hits=hits,
        total=total,
        avg_duration=round(avg_dur, 3),
        per_query=rr_list,
    )


def format_comparison_table(metrics: Sequence[RecipeMetrics], k: int) -> str:
    """將多個 recipe 的度量格式化為對比表（純文字）。"""
    if not metrics:
        return "（無評估結果）"

    header = f"{'recipe':<26} {'recall@'+str(k):>10} {'MRR':>8} {'hits':>10} {'avg_s':>8}"
    lines = [header, "-" * len(header)]
    # 依 recall 由高到低排序
    for m in sorted(metrics, key=lambda x: (x.recall_at_k, x.mrr), reverse=True):
        lines.append(
            f"{m.recipe:<26} {m.recall_at_k:>10.3f} {m.mrr:>8.3f} "
            f"{str(m.hits)+'/'+str(m.total):>10} {m.avg_duration:>8.2f}"
        )
    return "\n".join(lines)
