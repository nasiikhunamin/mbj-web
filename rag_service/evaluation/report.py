"""Assemble per-item and aggregate evaluation results (Task 4.2).

Reads the raw runner output (``data/results/E{XX}_results.json``, Task 4.1),
merges it with the ground truth (``data/evaluation/ground_truth.json``,
Task 1.3), and produces:

* ``data/analysis/evaluation_summary.csv`` — one row per experiment (E01–E16),
  the file required by Task 4.2.
* ``data/analysis/evaluation_details.json`` — per-item metrics plus the judge
  identity, used later by Task 4.4 (atomic-claim annotation sampling).

Expected raw-results contract::

    {
      "experiment_code": "E16",
      "generated_at": "2026-11-21T10:00:00Z",
      "items": [
        {
          "id": "gt-001",
          "question": "...",
          "answer": "...",
          "contexts": ["passage 1", "passage 2"],
          "retrieved": [{"chunk_id": "c1", "doc_id": "panduan_pendaftaran", "rank": 1}],
          "is_refusal": false,
          "context_tokens": 512,
          "latency_ms": 1234.5
        }
      ]
    }

Faithfulness is skipped (and counted) for out-of-scope questions, refusals, and
items without retrieved context, per PRD section 8.1.
"""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from rag_service.evaluation.faithfulness import FaithfulnessError
from rag_service.evaluation.metrics import (
    ir_metrics,
    ranked_document_ids,
    relevant_documents,
)

DEFAULT_K = 5

logger = logging.getLogger(__name__)


class EvaluationError(RuntimeError):
    """Raised when the inputs cannot be evaluated."""


def _is_number(value: Any) -> bool:
    """True for scored metrics; NaN means the judge could not score the item."""
    return isinstance(value, (int, float)) and not (
        isinstance(value, float) and math.isnan(value)
    )


def answer_fingerprint(answer: str) -> str:
    """Short hash of an answer, used to invalidate cached judge scores."""
    return hashlib.sha256((answer or "").encode("utf-8")).hexdigest()[:16]


def load_ground_truth(path: Path) -> Dict[str, Dict[str, Any]]:
    """Index the ground-truth dataset by item id."""
    if not path.exists():
        raise EvaluationError(f"ground truth not found: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EvaluationError(f"{path} is not valid JSON: {exc}") from exc

    items = payload.get("items") if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        raise EvaluationError(f"{path} must contain a list of ground-truth items")

    index: Dict[str, Dict[str, Any]] = {}
    for item in items:
        if isinstance(item, dict) and item.get("id"):
            index[str(item["id"])] = item
    return index


def load_results(path: Path) -> Dict[str, Any]:
    """Load one raw experiment result file."""
    if not path.exists():
        raise EvaluationError(f"results not found: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EvaluationError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise EvaluationError(f"{path} must contain a JSON object")
    return payload


def result_items(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return the evaluated items of a raw results payload."""
    items = payload.get("items")
    if not isinstance(items, list):
        raise EvaluationError("results payload has no `items` list")
    return [item for item in items if isinstance(item, dict)]


@dataclass
class FaithfulnessCache:
    """Reuse judge scores across runs so a long evaluation can be resumed."""

    path: Optional[Path] = None
    entries: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Optional[Path]) -> "FaithfulnessCache":
        if path is None or not path.exists():
            return cls(path=path)
        try:
            entries = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            entries = {}
        return cls(path=path, entries=entries if isinstance(entries, dict) else {})

    @staticmethod
    def key(code: str, item_id: str, fingerprint: str) -> str:
        return f"{code}|{item_id}|{fingerprint}"

    def get(self, code: str, item_id: str, fingerprint: str) -> Optional[float]:
        entry = self.entries.get(self.key(code, item_id, fingerprint))
        if not entry:
            return None
        value = entry.get("faithfulness")
        return float(value) if isinstance(value, (int, float)) else None

    def put(self, code: str, item_id: str, fingerprint: str, score: float, judge: str) -> None:
        self.entries[self.key(code, item_id, fingerprint)] = {
            "faithfulness": score,
            "judge_model": judge,
        }

    def save(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.entries, ensure_ascii=False, indent=1), encoding="utf-8"
        )


@dataclass
class ExperimentEvaluation:
    """Evaluation output for a single experiment code."""

    code: str
    summary: Dict[str, Any]
    items: List[Dict[str, Any]]
    faithful_scored: int = 0
    faithfulness_skipped: Dict[str, int] = field(default_factory=dict)


def _mean(values: Iterable[Optional[float]]) -> Optional[float]:
    numbers = [float(v) for v in values if _is_number(v)]
    return sum(numbers) / len(numbers) if numbers else None


def rejection_accuracy(rows: Sequence[Dict[str, Any]]) -> Optional[float]:
    """Share of out-of-scope questions that the system correctly refused (Task 4.3).

    Returns ``None`` when the experiment has no out-of-scope questions, so the
    metric is never silently reported as zero.
    """
    out_of_scope = [row for row in rows if row.get("is_out_of_scope")]
    if not out_of_scope:
        return None
    correct = sum(1 for row in out_of_scope if row.get("is_refusal"))
    return correct / len(out_of_scope)


def _compact(value: Optional[float]) -> Optional[float]:
    return round(value, 6) if isinstance(value, float) else value


def evaluate_experiment(
    code: str,
    payload: Dict[str, Any],
    ground_truth: Dict[str, Dict[str, Any]],
    *,
    scorer: Optional[Any] = None,
    k: int = DEFAULT_K,
    cache: Optional[FaithfulnessCache] = None,
    limit: Optional[int] = None,
) -> ExperimentEvaluation:
    """Evaluate one experiment: IR metrics plus per-item faithfulness."""
    rows: List[Dict[str, Any]] = []
    skipped: Dict[str, int] = {}

    for item in result_items(payload):
        if limit is not None and len(rows) >= limit:
            break

        item_id = str(item.get("id") or "")
        truth = ground_truth.get(item_id, {})
        is_out_of_scope = bool(
            item.get("is_out_of_scope", truth.get("is_out_of_scope", False))
        )
        is_refusal = bool(item.get("is_refusal", False))

        row: Dict[str, Any] = {
            "experiment_code": code,
            "id": item_id,
            "question": item.get("question") or truth.get("question"),
            "category": item.get("category") or truth.get("category"),
            "is_out_of_scope": is_out_of_scope,
            "is_refusal": is_refusal,
            "context_tokens": item.get("context_tokens"),
            "latency_ms": item.get("latency_ms"),
            "answer_sha256": answer_fingerprint(str(item.get("answer") or "")),
        }

        # --- retrieval metrics (documents, not chunks) ---
        relevant = relevant_documents(truth)
        retrieved = item.get("retrieved") or []
        row["relevant_doc_ids"] = relevant
        row["retrieved_doc_ids"] = ranked_document_ids(retrieved, k)

        if not relevant:
            row["ir_skipped_reason"] = "no_ground_truth_documents"
        else:
            row.update(ir_metrics(retrieved, relevant, k))

        # --- faithfulness (in-domain, non-refusal answers only) ---
        contexts = [c for c in (item.get("contexts") or []) if c and str(c).strip()]
        skip_reason: Optional[str] = None

        if is_out_of_scope:
            skip_reason = "out_of_scope_question"
        elif is_refusal:
            skip_reason = "refusal_answer"
        elif not contexts:
            skip_reason = "no_retrieved_context"

        if skip_reason:
            row["faithfulness_skipped_reason"] = skip_reason
            skipped[skip_reason] = skipped.get(skip_reason, 0) + 1
        else:
            fingerprint = row["answer_sha256"]
            cached = cache.get(code, item_id, fingerprint) if cache else None

            if cached is not None:
                row["faithfulness"] = cached
                row["faithfulness_cached"] = True
                row["judge_model"] = scorer.config.model_name if scorer else None
            elif scorer is None:
                row["faithfulness_skipped_reason"] = "judge_disabled"
                skipped["judge_disabled"] = skipped.get("judge_disabled", 0) + 1
            else:
                try:
                    score = scorer.score(
                        str(item.get("question") or truth.get("question") or ""),
                        str(item.get("answer") or ""),
                        contexts,
                    )
                except FaithfulnessError as exc:
                    # One slow/flaky judge call must not kill a multi-hour run.
                    logger.warning(
                        "judge gagal menilai %s/%s (%s); item ini tanpa skor: %s",
                        code,
                        item_id,
                        type(exc).__name__,
                        exc,
                    )
                    row["faithfulness_skipped_reason"] = "judge_error"
                    row["faithfulness_error"] = str(exc)
                    skipped["judge_error"] = skipped.get("judge_error", 0) + 1
                else:
                    row["faithfulness"] = score.score
                    row["judge_model"] = score.requested_model
                    row["judge_base_url"] = score.base_url
                    row["judge_latency_ms"] = score.latency_ms
                    if cache and not math.isnan(score.score):
                        cache.put(
                            code, item_id, fingerprint, score.score, score.requested_model
                        )

        rows.append(row)

    summary = summarize(code, rows, payload, k)
    return ExperimentEvaluation(
        code=code,
        summary=summary,
        items=rows,
        faithful_scored=sum(1 for r in rows if _is_number(r.get("faithfulness"))),
        faithfulness_skipped=skipped,
    )


def summarize(code: str, rows: Sequence[Dict[str, Any]], payload: Dict[str, Any], k: int) -> Dict[str, Any]:
    """Aggregate per-item rows into one summary row for the CSV."""
    return {
        "experiment_code": code,
        "chunking_strategy": payload.get("chunking_strategy") or "",
        "retrieval_method": payload.get("retrieval_method") or "",
        "reranker_enabled": payload.get("reranker_enabled", ""),
        "items_total": len(rows),
        "in_domain_items": sum(1 for r in rows if not r["is_out_of_scope"]),
        "refusal_answers": sum(1 for r in rows if r["is_refusal"]),
        "out_of_scope_items": sum(1 for r in rows if r["is_out_of_scope"]),
        "rejection_accuracy": _compact(rejection_accuracy(rows)),
        f"faithfulness_mean": _compact(_mean(r.get("faithfulness") for r in rows)),
        "faithfulness_scored": sum(1 for r in rows if _is_number(r.get("faithfulness"))),
        f"hit_at_{k}": _compact(_mean(r.get(f"hit_at_{k}") for r in rows)),
        f"mrr_at_{k}": _compact(_mean(r.get(f"mrr_at_{k}") for r in rows)),
        f"ndcg_at_{k}": _compact(_mean(r.get(f"ndcg_at_{k}") for r in rows)),
        "ir_scored": sum(1 for r in rows if _is_number(r.get(f"hit_at_{k}"))),
        "context_tokens_mean": _compact(_mean(r.get("context_tokens") for r in rows)),
        "latency_ms_mean": _compact(_mean(r.get("latency_ms") for r in rows)),
    }


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


def write_summary_csv(summaries: Sequence[Dict[str, Any]], path: Path, k: int = DEFAULT_K) -> None:
    """Write the aggregate evaluation summary CSV (Task 4.2 deliverable)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        column.replace("_at_5", f"_at_{k}") for column in SUMMARY_COLUMNS
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in summaries:
            writer.writerow(row)


def write_details_json(evaluations: Sequence[ExperimentEvaluation], path: Path, k: int = DEFAULT_K) -> None:
    """Write per-item details, including judge identity, for Task 4.4 sampling."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "k": k,
        "experiments": [
            {
                "experiment_code": evaluation.code,
                "summary": evaluation.summary,
                "faithfulness_skipped": evaluation.faithfulness_skipped,
                "items": evaluation.items,
            }
            for evaluation in evaluations
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
