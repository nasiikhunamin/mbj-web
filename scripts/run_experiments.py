#!/usr/bin/env python3
"""Batch runner for the 16 RAG experiment configurations (Task 4.1).

Runs every ground-truth question through E01-E16 and writes
``data/results/E{XX}_results.json`` for the evaluation pipeline (Task 4.2).

Usage:
    # full run over every configuration
    .venv310/bin/python scripts/run_experiments.py

    # smoke test on one configuration, five questions
    .venv310/bin/python scripts/run_experiments.py --codes E16 --limit 5

    # start over instead of resuming finished questions
    .venv310/bin/python scripts/run_experiments.py --no-resume
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag_service.config import available_configs, load_config  # noqa: E402
from rag_service.experiments.runner import (  # noqa: E402
    RunnerError,
    load_questions,
    run_all,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the E01-E16 RAG experiments over the ground-truth questions."
    )
    parser.add_argument(
        "--ground-truth",
        default=str(PROJECT_ROOT / "data" / "evaluation" / "ground_truth.json"),
        help="Ground-truth dataset produced by Task 1.3.",
    )
    parser.add_argument(
        "--results-dir",
        default=str(PROJECT_ROOT / "data" / "results"),
        help="Directory for the E{XX}_results.json outputs.",
    )
    parser.add_argument(
        "--codes",
        nargs="+",
        default=None,
        help="Experiment codes to run (default: every available E*.yaml).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Run at most N questions per experiment (smoke testing).",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Ignore finished questions and restart each experiment.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print the final summary.",
    )
    return parser.parse_args()


def build_pipeline_factory():
    """Return a factory that builds the real pipeline for an experiment code."""
    from rag_service.pipeline import build_pipeline

    def factory(code: str):
        return build_pipeline(load_config(code))

    return factory


def resolve_codes(requested) -> list:
    """Normalize requested codes against the available YAML configs."""
    if requested:
        return [code.strip().upper() for code in requested]
    return available_configs()


def progress_printer(total_codes: int):
    """Build an on_progress callback that prints one line per finished item."""
    state = {"code": None, "index": 0}

    def callback(code: str, record: dict, done: int, total: int) -> None:
        if code != state["code"]:
            state["code"] = code
            state["index"] += 1
            print(f"[{state['index']}/{total_codes}] {code}", flush=True)
        answer = str(record.get("answer") or "").replace("\n", " ")[:60]
        print(f"  {record['id']} ({done}/{total}): {answer}", flush=True)

    return callback


def main() -> int:
    args = parse_args()
    try:
        questions = load_questions(Path(args.ground_truth))
    except RunnerError as exc:
        print(
            json.dumps(
                {
                    "status": "error",
                    "message": str(exc),
                    "hint": "Ground truth adalah Phase 1 Task 1.3 — belum tersedia.",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    codes = resolve_codes(args.codes)
    if not codes:
        print(
            json.dumps(
                {
                    "status": "error",
                    "message": "tidak ada konfigurasi eksperimen E01-E16",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    if not args.quiet:
        print(f"Menjalankan {len(codes)} konfigurasi × {len(questions)} soal uji")

    on_progress = None if args.quiet else progress_printer(len(codes))
    payloads = []
    failures = []
    for code in codes:
        try:
            result = run_all(
                [code],
                questions,
                Path(args.results_dir),
                build_pipeline_factory(),
                resume=not args.no_resume,
                limit=args.limit,
                on_progress=on_progress,
            )
            payloads.extend(result)
        except Exception as exc:  # noqa: BLE001 - one bad config must not stop the batch
            failures.append({"code": code, "message": str(exc)})
            print(f"GAGAL {code}: {exc}", flush=True)

    summary = {
        "status": "ok" if not failures else "partial",
        "questions": len(questions),
        "experiments": [
            {"code": payload["experiment_code"], "items": len(payload.get("items", []))}
            for payload in payloads
        ],
        "results_dir": str(Path(args.results_dir)),
        "failures": failures,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
