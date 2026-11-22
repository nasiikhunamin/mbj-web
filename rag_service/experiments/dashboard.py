"""Data assembly for the Streamlit evaluation dashboard (Task 3.6).

Keeps every dataframe-building step free of Streamlit so the dashboard data can
be unit tested. ``scripts/dashboard.py`` only renders what these helpers return.

Artifacts read (all optional — the dashboard must still open before Phase 1/4
finish):

* ``data/analysis/evaluation_summary.csv`` — one row per experiment (Task 4.2)
* ``data/analysis/evaluation_details.json`` — per-item metrics (Task 4.2)
* ``data/evaluation/ground_truth.json`` — questions/sources (Task 1.3)
* ``data/results/E{XX}_results.json`` — raw answers (Task 4.1)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

import pandas as pd

EXPERIMENT_CODES = tuple(f"E{number:02d}" for number in range(1, 17))
SOURCE_TYPES = ("pdf", "docx", "web")

SUMMARY_COLUMNS = (
    "experiment_code",
    "chunking_strategy",
    "retrieval_method",
    "reranker_enabled",
    "items_total",
    "in_domain_items",
    "refusal_answers",
    "out_of_scope_items",
    "rejection_accuracy",
    "faithfulness_mean",
    "faithfulness_scored",
    "hit_at_5",
    "mrr_at_5",
    "ndcg_at_5",
    "ir_scored",
    "context_tokens_mean",
    "latency_ms_mean",
)

ITEM_COLUMNS = (
    "experiment_code",
    "id",
    "question",
    "category",
    "source_type",
    "is_out_of_scope",
    "is_refusal",
    "answer",
    "ground_truth_answer",
    "faithfulness",
    "hit_at_5",
    "mrr_at_5",
    "ndcg_at_5",
    "context_tokens",
    "latency_ms",
)

SUMMARY_METRICS = ("faithfulness_mean", "hit_at_5", "latency_ms_mean")


def load_summary(path: Path) -> pd.DataFrame:
    """Load the aggregate summary CSV, returning an empty frame when absent."""
    path = Path(path)
    if not path.exists():
        return pd.DataFrame(columns=list(SUMMARY_COLUMNS))
    return pd.read_csv(path)


def load_details(path: Path) -> List[Dict[str, Any]]:
    """Load the per-item details JSON (``experiments`` list), or ``[]``."""
    path = Path(path)
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    experiments = payload.get("experiments") if isinstance(payload, dict) else None
    return experiments if isinstance(experiments, list) else []


def load_ground_truth(path: Path) -> Dict[str, Dict[str, Any]]:
    """Index the ground-truth items by id. Returns ``{}`` when absent/invalid."""
    path = Path(path)
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    items = payload.get("items") if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        return {}
    return {
        str(item["id"]): item
        for item in items
        if isinstance(item, dict) and item.get("id")
    }


def load_answers(results_dir: Path) -> Dict[tuple, str]:
    """Map ``(experiment_code, item_id) -> answer`` from the raw result files."""
    results_dir = Path(results_dir)
    answers: Dict[tuple, str] = {}
    if not results_dir.exists():
        return answers
    for path in sorted(results_dir.glob("E*_results.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        code = str(payload.get("experiment_code") or path.stem.replace("_results", ""))
        for item in payload.get("items") or []:
            if isinstance(item, dict) and item.get("id"):
                answers[(code, str(item["id"]))] = str(item.get("answer") or "")
    return answers


def build_item_table(
    details: Sequence[Dict[str, Any]],
    ground_truth: Dict[str, Dict[str, Any]],
    answers: Dict[tuple, str],
) -> pd.DataFrame:
    """Merge per-item metrics with the answers and ground-truth text."""
    rows: List[Dict[str, Any]] = []
    for experiment in details:
        code = str(experiment.get("experiment_code") or "")
        for item in experiment.get("items") or []:
            if not isinstance(item, dict):
                continue
            item_id = str(item.get("id") or "")
            truth = ground_truth.get(item_id, {})
            rows.append(
                {
                    "experiment_code": code,
                    "id": item_id,
                    "question": item.get("question") or truth.get("question"),
                    "category": item.get("category") or truth.get("category"),
                    "source_type": truth.get("source_type"),
                    "is_out_of_scope": item.get("is_out_of_scope"),
                    "is_refusal": item.get("is_refusal"),
                    "answer": answers.get((code, item_id)),
                    "ground_truth_answer": truth.get("ground_truth_answer"),
                    "faithfulness": item.get("faithfulness"),
                    "hit_at_5": item.get("hit_at_5"),
                    "mrr_at_5": item.get("mrr_at_5"),
                    "ndcg_at_5": item.get("ndcg_at_5"),
                    "context_tokens": item.get("context_tokens"),
                    "latency_ms": item.get("latency_ms"),
                }
            )
    return pd.DataFrame(rows, columns=list(ITEM_COLUMNS))


def filter_items(
    items: pd.DataFrame,
    *,
    codes: Optional[Iterable[str]] = None,
    source_types: Optional[Iterable[str]] = None,
    categories: Optional[Iterable[str]] = None,
) -> pd.DataFrame:
    """Filter per-item rows by experiment code, source type, and category."""
    filtered = items
    for column, selected in (
        ("experiment_code", codes),
        ("source_type", source_types),
        ("category", categories),
    ):
        chosen = list(selected) if selected else []
        if chosen and column in filtered.columns:
            filtered = filtered[filtered[column].isin(chosen)]
    return filtered


def metric_means(summary: pd.DataFrame) -> pd.DataFrame:
    """Average each headline metric across the selected experiments."""
    if summary.empty:
        return pd.DataFrame(columns=["metric", "value"])
    rows = [
        {"metric": metric, "value": summary[metric].mean()}
        for metric in SUMMARY_METRICS
        if metric in summary.columns
    ]
    return pd.DataFrame(rows, columns=["metric", "value"])


def available_values(items: pd.DataFrame, column: str) -> List[str]:
    """Sorted distinct values of a column, ignoring nulls."""
    if items.empty or column not in items.columns:
        return []
    values = items[column].dropna().unique().tolist()
    return sorted(str(value) for value in values)
