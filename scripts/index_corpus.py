#!/usr/bin/env python3
"""Build the four dense collections and four BM25 indices for the RAG corpus.

Usage:
    python scripts/index_corpus.py
    python scripts/index_corpus.py --corpus-dir data/processed/corpus --vectordb-dir data/vectordb
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag_service.stores.index_builder import STRATEGIES, build_indexes, load_corpus  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Index the RAG corpus into 4 dense + 4 sparse stores.")
    parser.add_argument(
        "--corpus-dir",
        default=str(PROJECT_ROOT / "data" / "processed" / "corpus"),
        help="Directory containing canonical corpus JSON files.",
    )
    parser.add_argument(
        "--vectordb-dir",
        default=str(PROJECT_ROOT / "data" / "vectordb"),
        help="Output directory for ChromaDB and BM25 indices.",
    )
    parser.add_argument(
        "--strategies",
        nargs="+",
        default=list(STRATEGIES),
        choices=list(STRATEGIES),
        help="Chunking strategies to index (default: all four).",
    )
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="Do not reset existing indices before indexing.",
    )
    parser.add_argument(
        "--exclude-file",
        default=str(PROJECT_ROOT / "data" / "processed" / "excluded_doc_ids.json"),
        help="JSON file listing doc_ids to skip (list, or {\"doc_ids\": [...]}).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        documents = load_corpus(args.corpus_dir)
    except FileNotFoundError as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, indent=2))
        return 1

    if not documents:
        print(
            json.dumps(
                {
                    "status": "error",
                    "message": f"no corpus JSON documents found in {args.corpus_dir}",
                },
                indent=2,
            )
        )
        return 1

    excluded: set = set()
    exclude_path = Path(args.exclude_file)
    if exclude_path.exists():
        try:
            payload = json.loads(exclude_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(json.dumps({"status": "error", "message": f"invalid exclude file: {exc}"}, indent=2))
            return 1
        if isinstance(payload, list):
            excluded = {str(x) for x in payload}
        elif isinstance(payload, dict):
            excluded = {str(x) for x in payload.get("doc_ids", [])}

    if excluded:
        kept = [d for d in documents if d.get("doc_id") not in excluded]
        skipped = sorted({d.get("doc_id") for d in documents} & excluded)
        print(f"[exclude] {len(documents) - len(kept)} dokumen dibuang: {skipped}")
        documents = kept

    if not documents:
        print(json.dumps({"status": "error", "message": "all documents were excluded"}, indent=2))
        return 1

    report = build_indexes(
        documents,
        vectordb_directory=args.vectordb_dir,
        strategies=args.strategies,
        reset=not args.keep_existing,
    )
    report["status"] = "ok"
    report["vectordb_dir"] = str(Path(args.vectordb_dir))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
