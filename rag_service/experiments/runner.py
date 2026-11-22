"""Batch experiment runner (Task 4.1).

Runs every E01-E16 pipeline over the ground-truth questions and stores the raw
answers in ``data/results/E{XX}_results.json``. That file is the input contract
consumed by the evaluation pipeline (Task 4.2, ``scripts/evaluate.py``)::

    {
      "experiment_code": "E16",
      "generated_at": "2026-11-21T10:00:00Z",
      "chunking_strategy": "structure_aware",
      "retrieval_method": "hybrid_rerank",
      "reranker_enabled": true,
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

Answers are appended and persisted after every question, so an interrupted run
(e.g. a dropped gateway connection) resumes from the last finished item instead
of paying for the whole batch again. The resume check compares item ids.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence


class RunnerError(RuntimeError):
    """Raised when the runner cannot proceed with the given inputs."""


def load_questions(path: Path) -> List[Dict[str, Any]]:
    """Load the ordered ground-truth questions from Task 1.3.

    Accepts either a bare JSON list or an object with an ``items`` list. Items
    without an ``id`` cannot be resumed and are rejected.
    """
    path = Path(path)
    if not path.exists():
        raise RunnerError(f"ground truth not found: {path}")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RunnerError(f"{path} is not valid JSON: {exc}") from exc

    items = payload.get("items") if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        raise RunnerError(f"{path} must contain a list of ground-truth items")

    questions = [item for item in items if isinstance(item, dict)]
    missing_id = [i for i, item in enumerate(questions) if not str(item.get("id") or "")]
    if missing_id:
        raise RunnerError(f"{path}: items at index {missing_id} have no id")
    if not questions:
        raise RunnerError(f"{path}: no ground-truth questions found")
    return questions


def _as_payload(result: Any) -> Dict[str, Any]:
    """Normalize a ``PipelineResult`` or plain mapping into a JSON dict."""
    if hasattr(result, "to_dict"):
        return result.to_dict()
    if isinstance(result, dict):
        return dict(result)
    raise RunnerError(f"unsupported pipeline result type: {type(result)!r}")


def _contexts(chunks: Sequence[Any]) -> List[str]:
    """Return the non-empty chunk texts used as the generator context."""
    contexts: List[str] = []
    for chunk in chunks:
        if isinstance(chunk, dict):
            content = chunk.get("content", "")
        else:
            content = getattr(chunk, "content", "")
        if content and str(content).strip():
            contexts.append(str(content))
    return contexts


def _retrieved(chunks: Sequence[Any]) -> List[Dict[str, Any]]:
    """Return the ranked ``{chunk_id, doc_id, rank}`` records used by IR metrics."""

    def read(chunk: Any, name: str, default: Any = "") -> Any:
        if isinstance(chunk, dict):
            return chunk.get(name, default)
        return getattr(chunk, name, default)

    retrieved: List[Dict[str, Any]] = []
    for position, chunk in enumerate(chunks, start=1):
        retrieved.append(
            {
                "chunk_id": str(read(chunk, "chunk_id") or ""),
                "doc_id": str(read(chunk, "doc_id") or ""),
                "rank": int(read(chunk, "rank", 0) or position),
            }
        )
    return retrieved


def build_record(question: Dict[str, Any], result_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Merge one ground-truth question with one pipeline result."""
    chunks = result_payload.get("chunks") or []
    return {
        "id": str(question["id"]),
        "question": result_payload.get("question") or question.get("question") or "",
        "answer": str(result_payload.get("answer") or ""),
        "contexts": _contexts(chunks),
        "retrieved": _retrieved(chunks),
        "sources": list(result_payload.get("sources") or []),
        "retrieved_sources": list(result_payload.get("retrieved_sources") or []),
        "is_refusal": bool(result_payload.get("is_refusal")),
        "context_tokens": int(result_payload.get("context_tokens") or 0),
        "latency_ms": float(result_payload.get("latency_ms") or 0.0),
        "category": question.get("category"),
        "source_type": question.get("source_type"),
        "is_out_of_scope": bool(question.get("is_out_of_scope")),
    }


def _experiment_labels(pipeline: Any) -> Dict[str, Any]:
    """Read chunking/retrieval labels from the pipeline config when present."""
    config = getattr(pipeline, "config", None)
    if config is None:
        return {"chunking_strategy": "", "retrieval_method": "", "reranker_enabled": ""}
    return {
        "chunking_strategy": getattr(config, "chunking_strategy", ""),
        "retrieval_method": getattr(config, "retrieval_method", ""),
        "reranker_enabled": getattr(config, "reranker_enabled", ""),
    }


def build_payload(code: str, pipeline: Any, items: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Assemble the raw-results payload for one experiment."""
    payload: Dict[str, Any] = {"experiment_code": code, "items": list(items)}
    payload.update(_experiment_labels(pipeline))
    return payload


def _load_completed(path: Path) -> Dict[str, Dict[str, Any]]:
    """Index the already-finished items of an earlier run by id."""
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    items = payload.get("items") if isinstance(payload, dict) else None
    if not isinstance(items, list):
        return {}
    return {
        str(item["id"]): item
        for item in items
        if isinstance(item, dict) and item.get("id")
    }


def write_payload(path: Path, payload: Dict[str, Any]) -> None:
    """Write the payload atomically so a crash never truncates the results file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    os.replace(temp_path, path)


def run_experiment(
    code: str,
    questions: Sequence[Dict[str, Any]],
    pipeline: Any,
    results_path: Path,
    *,
    resume: bool = True,
    limit: Optional[int] = None,
    on_progress: Optional[Callable[[str, Dict[str, Any], int, int], None]] = None,
) -> Dict[str, Any]:
    """Run one experiment over ``questions``, writing each answer as it finishes."""
    results_path = Path(results_path)
    ordered = list(questions[:limit]) if limit is not None else list(questions)
    completed = _load_completed(results_path) if resume else {}

    items: List[Dict[str, Any]] = []
    for question in ordered:
        question_id = str(question["id"])
        existing = completed.get(question_id)
        if existing is not None:
            items.append(existing)
            continue

        result = pipeline.ask(question.get("question") or "")
        record = build_record(question, _as_payload(result))
        items.append(record)
        write_payload(results_path, build_payload(code, pipeline, items))

        if on_progress is not None:
            on_progress(code, record, len(items), len(ordered))

    payload = build_payload(code, pipeline, items)
    payload["generated_at"] = datetime.now(timezone.utc).isoformat()
    write_payload(results_path, payload)
    return payload


def run_all(
    codes: Sequence[str],
    questions: Sequence[Dict[str, Any]],
    results_dir: Path,
    pipeline_factory: Callable[[str], Any],
    *,
    resume: bool = True,
    limit: Optional[int] = None,
    on_progress: Optional[Callable[[str, Dict[str, Any], int, int], None]] = None,
) -> List[Dict[str, Any]]:
    """Run every experiment code sequentially and return the written payloads."""
    results_dir = Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    payloads: List[Dict[str, Any]] = []
    for code in codes:
        pipeline = pipeline_factory(code)
        payload = run_experiment(
            code,
            questions,
            pipeline,
            results_dir / f"{code}_results.json",
            resume=resume,
            limit=limit,
            on_progress=on_progress,
        )
        payloads.append(payload)
    return payloads
