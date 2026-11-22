#!/usr/bin/env python3
"""Build data/processed/corpus/metadata.json and apply content-type labels (Task 1.2).

Usage:
    # refresh token counts / section lists, preserve existing labels
    .venv310/bin/python scripts/build_corpus_metadata.py

    # apply labels from a JSON mapping {"doc_id": "narrative", ...}
    .venv310/bin/python scripts/build_corpus_metadata.py --labels data/processed/content_types.json
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag_service.ingestion import (  # noqa: E402
    CONTENT_TYPES,
    MetadataError,
    apply_content_types,
    build_metadata,
    load_corpus_documents,
    load_labels,
)
from rag_service.ingestion.metadata import write_metadata  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the corpus metadata.json with content-type labels."
    )
    parser.add_argument(
        "--corpus-dir",
        default=str(PROJECT_ROOT / "data" / "processed" / "corpus"),
        help="Directory holding the canonical corpus JSON files.",
    )
    parser.add_argument(
        "--labels",
        default=None,
        help="Optional JSON file mapping doc_id -> content_type.",
    )
    parser.add_argument(
        "--no-token-count",
        action="store_true",
        help="Skip E5 token counting for documents that lack it.",
    )
    parser.add_argument("--quiet", action="store_true", help="Only print the summary.")
    return parser.parse_args()


def load_label_file(path: Path) -> dict:
    """Read an explicit doc_id -> content_type mapping."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise MetadataError(f"{path} must contain a JSON object mapping doc_id -> content_type")
    return {str(key): str(value) for key, value in payload.items()}


def main() -> int:
    args = parse_args()
    corpus_dir = Path(args.corpus_dir)

    try:
        documents = load_corpus_documents(corpus_dir)
        labels = load_labels(corpus_dir)
        if args.labels:
            labels.update(load_label_file(Path(args.labels)))
    except (MetadataError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    unknown = sorted(set(labels) - {d["doc_id"] for d in documents})
    if unknown:
        print(
            json.dumps(
                {
                    "status": "error",
                    "message": f"label untuk doc_id tak dikenal: {unknown}",
                    "hint": f"content_type yang valid: {list(CONTENT_TYPES)}",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    tokenizer = None
    if not args.no_token_count:
        from rag_service.chunkers.tokenizer import E5Tokenizer

        tokenizer = E5Tokenizer()

    try:
        payload = build_metadata(documents, tokenizer=tokenizer, labels=labels)
    except MetadataError as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    metadata_path = write_metadata(payload, corpus_dir)
    updated = apply_content_types(corpus_dir, labels)
    unlabeled = [entry["doc_id"] for entry in payload["documents"] if not entry["content_type"]]

    if not args.quiet:
        for entry in payload["documents"]:
            label = entry["content_type"] or "(belum dilabeli)"
            print(f"{entry['doc_id']}: {entry['source_type']} · {label} · {entry['token_count_e5']} token")

    print(
        json.dumps(
            {
                "status": "ok",
                "metadata_path": str(metadata_path),
                "documents": len(payload["documents"]),
                "labeled": len(payload["documents"]) - len(unlabeled),
                "documents_patched": updated,
                "unlabeled": unlabeled,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
