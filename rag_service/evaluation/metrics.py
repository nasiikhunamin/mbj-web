"""Information-retrieval metrics (Task 4.2, PRD section 8.2).

Evaluation is done at **document level**: several retrieved chunks usually come
from the same document, so the ranked list is deduplicated by ``doc_id``
(keeping the first, best rank) before Hit@k / MRR@k / nDCG@k are computed.
Ground-truth relevance is binary: a document is relevant when its id appears in
the ground-truth item's ``source_doc_ids``.

Because the full document collection is not enumerated in the ground truth, the
ideal DCG is built from ``min(len(source_doc_ids), k)`` relevant documents. That
assumption is documented in the PRD and must be reported in Bab III.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List, Optional, Sequence


def document_id(entry: Any) -> str:
    """Extract a document id from a retrieved chunk (mapping or object)."""
    if entry is None:
        return ""
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict):
        value = entry.get("doc_id") or entry.get("document_id") or entry.get("source")
    else:
        value = getattr(entry, "doc_id", None) or getattr(entry, "document_id", None)
    return str(value or "")


def ranked_document_ids(retrieved: Optional[Sequence[Any]], k: Optional[int] = None) -> List[str]:
    """Deduplicate retrieved chunks into a ranked list of document ids.

    Entries may already be ranked by ``rank``; when every entry carries a rank
    the list is sorted by it first, otherwise the given order is trusted.
    """
    entries = list(retrieved or [])

    if entries and all(isinstance(e, dict) and "rank" in e for e in entries):
        entries.sort(key=lambda e: e.get("rank") or 0)

    ranked: List[str] = []
    for entry in entries:
        doc_id = document_id(entry)
        if doc_id and doc_id not in ranked:
            ranked.append(doc_id)
        if k is not None and len(ranked) >= k:
            break

    return ranked


def relevant_documents(item: Dict[str, Any]) -> List[str]:
    """Return the ground-truth relevant document ids of one ground-truth item."""
    raw = item.get("source_doc_ids") or item.get("doc_ids") or []
    if isinstance(raw, str):
        raw = [raw]
    return [str(value) for value in raw if str(value or "").strip()]


def hit_at_k(retrieved: Sequence[Any], relevant: Iterable[str], k: int = 5) -> float:
    """1.0 when at least one relevant document is inside the top ``k``, else 0.0."""
    relevant_set = set(relevant)
    if not relevant_set:
        return 0.0
    ranked = ranked_document_ids(retrieved, k)
    return 1.0 if any(doc in relevant_set for doc in ranked) else 0.0


def reciprocal_rank_at_k(retrieved: Sequence[Any], relevant: Iterable[str], k: int = 5) -> float:
    """1/rank of the first relevant document inside the top ``k`` (0.0 if absent)."""
    relevant_set = set(relevant)
    if not relevant_set:
        return 0.0
    for rank, doc_id in enumerate(ranked_document_ids(retrieved, k), start=1):
        if doc_id in relevant_set:
            return 1.0 / rank
    return 0.0


def _dcg(gains: Sequence[float]) -> float:
    return sum(gain / math.log2(index + 2) for index, gain in enumerate(gains))


def ndcg_at_k(retrieved: Sequence[Any], relevant: Iterable[str], k: int = 5) -> float:
    """nDCG@k with binary relevance and a ``min(|relevant|, k)`` ideal ranking."""
    relevant_set = set(relevant)
    if not relevant_set:
        return 0.0

    ranked = ranked_document_ids(retrieved, k)
    gains = [1.0 if doc_id in relevant_set else 0.0 for doc_id in ranked]
    ideal = _dcg([1.0] * min(len(relevant_set), k))

    return _dcg(gains) / ideal if ideal else 0.0


def ir_metrics(retrieved: Sequence[Any], relevant: Iterable[str], k: int = 5) -> Dict[str, float]:
    """All three IR metrics for one query."""
    relevant_list = list(relevant)
    return {
        f"hit_at_{k}": hit_at_k(retrieved, relevant_list, k),
        f"mrr_at_{k}": reciprocal_rank_at_k(retrieved, relevant_list, k),
        f"ndcg_at_{k}": ndcg_at_k(retrieved, relevant_list, k),
    }
