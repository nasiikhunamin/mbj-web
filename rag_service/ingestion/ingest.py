"""Corpus ingestion orchestration (Task 1.1).

Discovers the public source files (PDF/DOCX under ``data/raw`` and the Laravel
Blade pages under ``resources/views/pages``), parses them with
``rag_service.ingestion.parsers``, and writes one canonical JSON file per
document to ``data/processed/corpus/<doc_id>.json``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from rag_service.ingestion.parsers import finalize_document, parse_file


class IngestionError(RuntimeError):
    """Raised when the corpus cannot be ingested."""


def discover_sources(
    raw_dir: Path,
    views_dir: Optional[Path] = None,
) -> List[Tuple[Path, str]]:
    """Return ``(path, source_type)`` pairs for every supported input file."""
    raw_dir = Path(raw_dir)
    sources: List[Tuple[Path, str]] = []

    for source_type, pattern in (("pdf", "*.pdf"), ("docx", "*.docx")):
        directory = raw_dir / source_type
        if directory.exists():
            sources.extend((path, source_type) for path in sorted(directory.glob(pattern)))

    if views_dir is not None:
        views_dir = Path(views_dir)
        if views_dir.exists():
            sources.extend(
                (path, "web") for path in sorted(views_dir.rglob("*.blade.php"))
            )
    return sources


def _parse(path: Path, source_type: str, views_dir: Optional[Path]) -> Dict[str, Any]:
    if source_type == "web":
        return parse_file(path, views_root=views_dir)
    return parse_file(path)


def ingest(
    sources: Sequence[Tuple[Path, str]],
    out_dir: Path,
    *,
    views_dir: Optional[Path] = None,
    tokenizer: Optional[Any] = None,
    on_progress: Optional[Callable[[int, int, Dict[str, Any]], None]] = None,
) -> Dict[str, Any]:
    """Parse every source and write one canonical JSON per document."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    documents: List[Dict[str, Any]] = []
    seen: Dict[str, Path] = {}

    for index, (path, source_type) in enumerate(sources, start=1):
        document = finalize_document(
            _parse(path, source_type, views_dir), tokenizer=tokenizer
        )
        doc_id = document["doc_id"]
        if doc_id in seen:
            raise IngestionError(
                f"duplicate doc_id {doc_id!r}: {seen[doc_id]} and {path}"
            )
        seen[doc_id] = path

        (out_dir / f"{doc_id}.json").write_text(
            json.dumps(document, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        documents.append(
            {
                "doc_id": doc_id,
                "source_type": document["source_type"],
                "title": document["title"],
                "source_file": str(document.get("source_file") or path.name),
                "char_count": document["metadata"].get("char_count", 0),
                "token_count_e5": document["metadata"].get("token_count_e5"),
            }
        )

        if on_progress is not None:
            on_progress(index, len(sources), documents[-1])

    return {
        "status": "ok",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "corpus_dir": str(out_dir),
        "documents": documents,
        "counts": _counts_by_type(documents),
    }


def _counts_by_type(documents: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for document in documents:
        source_type = document.get("source_type", "unknown")
        counts[source_type] = counts.get(source_type, 0) + 1
    return counts
