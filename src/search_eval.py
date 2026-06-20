"""
搜尋命中率評估核心
==================

提供與 I/O 解耦的純函數，計算 recall@k、MRR 等檢索品質度量，供
tools/evaluate_search.py 對不同 search recipe 做 A/B 對比。

設計為純資料處理（不碰 Neo4j/LLM），以便單元測試。
"""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


@dataclass
class GoldenItem:
    """一筆評估樣本：query 與其預期應命中的目標 uuid。

    kind 區分目標型別：
      - "node": 目標為 Entity，對 node_* recipe 用 search_().nodes 評估
      - "edge": 目標為 RELATES_TO 邊（fact），對 edge_* recipe 用 search_().edges 評估
    """

    query: str
    target_uuid: str
    group_id: str
    target_name: str = ""
    kind: str = "node"


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


# ---------------------------------------------------------------------------
# golden set 持久化（可重現：生成一次、存檔、之後零 LLM 重複評估）
# ---------------------------------------------------------------------------

_GOLDEN_FIELDS = ("query", "target_uuid", "group_id", "target_name", "kind")


def save_golden(items: Sequence[GoldenItem], path: str) -> int:
    """將 golden set 存成 JSON（穩定排序、UTF-8、可 diff）。回傳寫入筆數。"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": 1, "count": len(items), "items": [asdict(it) for it in items]}
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(items)


def load_golden(path: str) -> List[GoldenItem]:
    """從 JSON 載入 golden set。容忍缺欄位（kind 預設 node），忽略未知欄位。"""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    raw = data.get("items", []) if isinstance(data, dict) else data
    items: List[GoldenItem] = []
    for it in raw:
        kwargs = {k: it[k] for k in _GOLDEN_FIELDS if k in it}
        # 必填欄位缺失則跳過該筆，避免整批載入失敗
        if "query" in kwargs and "target_uuid" in kwargs and "group_id" in kwargs:
            items.append(GoldenItem(**kwargs))
    return items


# ---------------------------------------------------------------------------
# baseline 快照 + 回歸偵測（純函數，供 regression gate）
# ---------------------------------------------------------------------------


def metrics_to_dict(metrics: Sequence[RecipeMetrics], k: int) -> dict:
    """將度量序列化為可存檔/比對的 dict（baseline 快照）。"""
    return {
        "k": k,
        "recipes": {
            m.recipe: {
                "recall_at_k": round(m.recall_at_k, 4),
                "mrr": round(m.mrr, 4),
                "hits": m.hits,
                "total": m.total,
                "avg_duration": m.avg_duration,
            }
            for m in metrics
        },
    }


def save_baseline(metrics: Sequence[RecipeMetrics], path: str, k: int) -> None:
    """存 baseline 快照 JSON。"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(metrics_to_dict(metrics, k), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def compare_to_baseline(
    metrics: Sequence[RecipeMetrics],
    baseline: Optional[dict],
    tol: float = 0.05,
) -> Tuple[List[Dict[str, float]], List[str]]:
    """對比目前度量與 baseline，找出回歸（recall 或 MRR 掉超過 tol）。

    Args:
        metrics: 本次評估度量
        baseline: 先前 metrics_to_dict 的快照（None 表無基線）
        tol: 容忍下滑幅度（預設 0.05）；跌幅超過即視為回歸

    Returns:
        (regressions, report_lines)
        regressions: 每筆 {recipe, d_recall, d_mrr}
        report_lines: 人類可讀的逐 recipe 對比行
    """
    base_recipes = (baseline or {}).get("recipes", {})
    regressions: List[Dict[str, float]] = []
    lines: List[str] = []
    for m in sorted(metrics, key=lambda x: x.recipe):
        b = base_recipes.get(m.recipe)
        if not b:
            lines.append(f"{m.recipe:<26} （無 baseline，新 recipe）")
            continue
        d_recall = m.recall_at_k - b.get("recall_at_k", 0.0)
        d_mrr = m.mrr - b.get("mrr", 0.0)
        flag = ""
        if d_recall < -tol or d_mrr < -tol:
            regressions.append(
                {"recipe": m.recipe, "d_recall": round(d_recall, 4), "d_mrr": round(d_mrr, 4)}
            )
            flag = "  ⚠️ 回歸"
        lines.append(
            f"{m.recipe:<26} Δrecall={d_recall:+.3f}  Δmrr={d_mrr:+.3f}{flag}"
        )
    return regressions, lines
