#!/usr/bin/env python3
"""Ingest public PDF/DOCX/Blade documents into canonical corpus JSON (Task 1.1).

Usage:
    .venv310/bin/python scripts/ingest_documents.py
    .venv310/bin/python scripts/ingest_documents.py --sources pdf docx
    .venv310/bin/python scripts/ingest_documents.py --limit 3 --quiet
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag_service.ingestion import discover_sources, ingest  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parse PDF/DOCX/Blade files into data/processed/corpus/*.json."
    )
    parser.add_argument(
        "--raw-dir",
        default=str(PROJECT_ROOT / "data" / "raw"),
        help="Directory holding the pdf/ and docx/ subfolders.",
    )
    parser.add_argument(
        "--views-dir",
        default=str(PROJECT_ROOT / "resources" / "views" / "pages"),
        help="Directory holding the Blade web pages.",
    )
    parser.add_argument(
        "--out-dir",
        default=str(PROJECT_ROOT / "data" / "processed" / "corpus"),
        help="Output directory for the canonical JSON files.",
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=["pdf", "docx", "web"],
        default=["pdf", "docx", "web"],
        help="Source types to ingest (default: all).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Ingest at most N documents (smoke testing).",
    )
    parser.add_argument(
        "--no-token-count",
        action="store_true",
        help="Skip E5 token counting (faster; Task 1.2 can add it later).",
    )
    parser.add_argument("--quiet", action="store_true", help="Only print the summary.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw_dir = Path(args.raw_dir)
    views_dir = Path(args.views_dir) if "web" in args.sources else None

    sources = [
        (path, source_type)
        for path, source_type in discover_sources(raw_dir, views_dir)
        if source_type in args.sources
    ]
    if args.limit is not None:
        sources = sources[: args.limit]

    if not sources:
        print(
            json.dumps(
                {
                    "status": "error",
                    "message": "tidak ada berkas sumber ditemukan",
                    "hint": (
                        "Taruh PDF di data/raw/pdf dan DOCX di data/raw/docx "
                        "(Task 1.1 manual)."
                    ),
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

    def on_progress(index: int, total: int, document: dict) -> None:
        if not args.quiet:
            print(f"[{index}/{total}] {document['source_type']}: {document['doc_id']}")

    report = ingest(
        sources,
        Path(args.out_dir),
        views_dir=views_dir,
        tokenizer=tokenizer,
        on_progress=on_progress,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
