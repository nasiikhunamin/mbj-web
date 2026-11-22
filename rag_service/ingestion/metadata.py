"""Document metadata and content-type labeling (Task 1.2).

Builds ``data/processed/corpus/metadata.json``: one entry per corpus document
with its content type, E5 token length, and section list. The content type is a
human decision (the researcher picks one of the eight labels); this module only
validates and propagates it.

If a label is present, it is also written back into the document JSON as the
top-level ``content_type`` field so the structure-aware chunker can use it.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

CONTENT_TYPES = (
    "narrative",
    "procedural",
    "qa_pairs",
    "comparison",
    "numeric",
    "catalog",
    "curriculum",
    "legal",
)

METADATA_FILENAME = "metadata.json"


class MetadataError(RuntimeError):
    """Raised when metadata cannot be assembled or a label is invalid."""


def load_corpus_documents(corpus_dir: Path) -> List[Dict[str, Any]]:
    """Load canonical corpus documents (``metadata.json`` is skipped)."""
    corpus_dir = Path(corpus_dir)
    if not corpus_dir.exists():
        raise MetadataError(f"corpus directory not found: {corpus_dir}")

    documents: List[Dict[str, Any]] = []
    for path in sorted(corpus_dir.glob("*.json")):
        if path.name == METADATA_FILENAME:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise MetadataError(f"{path} is not valid JSON: {exc}") from exc
        if isinstance(payload, list):
            documents.extend(item for item in payload if isinstance(item, dict))
        elif isinstance(payload, dict):
            documents.append(payload)

    if not documents:
        raise MetadataError(f"no corpus documents found in {corpus_dir}")
    return documents


def load_labels(corpus_dir: Path) -> Dict[str, str]:
    """Read the already-assigned content types from an existing metadata.json."""
    path = Path(corpus_dir) / METADATA_FILENAME
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    documents = payload.get("documents") if isinstance(payload, dict) else payload
    if not isinstance(documents, list):
        return {}
    return {
        str(entry["doc_id"]): str(entry["content_type"])
        for entry in documents
        if isinstance(entry, dict)
        and entry.get("doc_id")
        and entry.get("content_type")
    }


def _section_labels(document: Dict[str, Any]) -> List[str]:
    labels: List[str] = []
    for section in document.get("sections") or []:
        if isinstance(section, dict):
            heading = str(section.get("heading") or "").strip()
            if heading:
                labels.append(heading)
    return labels


def _token_count(document: Dict[str, Any], tokenizer: Optional[Any]) -> Optional[int]:
    existing = (document.get("metadata") or {}).get("token_count_e5")
    if isinstance(existing, int):
        return existing
    if tokenizer is None:
        return None
    return tokenizer.count_tokens(document.get("clean_text", ""))


def build_metadata(
    documents: Sequence[Dict[str, Any]],
    tokenizer: Optional[Any] = None,
    labels: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Assemble the metadata payload for every corpus document."""
    labels = dict(labels or {})
    entries: List[Dict[str, Any]] = []

    for document in documents:
        doc_id = str(document.get("doc_id") or "")
        if not doc_id:
            raise MetadataError("every document must have a doc_id")

        content_type = labels.get(doc_id) or document.get("content_type")
        if content_type and content_type not in CONTENT_TYPES:
            raise MetadataError(
                f"{doc_id}: unknown content_type {content_type!r}; "
                f"expected one of {CONTENT_TYPES}"
            )

        entries.append(
            {
                "doc_id": doc_id,
                "source_type": document.get("source_type", ""),
                "title": document.get("title", ""),
                "content_type": content_type,
                "token_count_e5": _token_count(document, tokenizer),
                "char_count": (document.get("metadata") or {}).get(
                    "char_count", len(document.get("clean_text", ""))
                ),
                "section_count": len(document.get("sections") or []),
                "sections": _section_labels(document),
            }
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "content_types": list(CONTENT_TYPES),
        "documents": entries,
    }


def write_metadata(payload: Dict[str, Any], corpus_dir: Path) -> Path:
    """Write the metadata payload to ``corpus_dir/metadata.json``."""
    path = Path(corpus_dir) / METADATA_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def apply_content_types(corpus_dir: Path, labels: Dict[str, str]) -> int:
    """Copy the chosen content types into each document JSON. Returns the count."""
    corpus_dir = Path(corpus_dir)
    updated = 0
    for doc_id, content_type in labels.items():
        if content_type not in CONTENT_TYPES:
            raise MetadataError(
                f"{doc_id}: unknown content_type {content_type!r}"
            )
        path = corpus_dir / f"{doc_id}.json"
        if not path.exists():
            continue
        document = json.loads(path.read_text(encoding="utf-8"))
        if document.get("content_type") == content_type:
            continue
        document["content_type"] = content_type
        metadata = dict(document.get("metadata") or {})
        metadata["content_type"] = content_type
        document["metadata"] = metadata
        path.write_text(
            json.dumps(document, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        updated += 1
    return updated
