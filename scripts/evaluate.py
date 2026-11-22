#!/usr/bin/env python3
"""Evaluate the 16 experiment results: RAGAS faithfulness + IR metrics (Task 4.2).

Reads the raw runner output from ``data/results/E{XX}_results.json`` (Task 4.1)
and the ground truth from ``data/evaluation/ground_truth.json`` (Task 1.3), then
writes:

* ``data/analysis/evaluation_summary.csv`` — one row per experiment (this is the
  deliverable required by Task 4.2).
* ``data/analysis/evaluation_details.json`` — per-item metrics and judge
  identity, used by Task 4.4 (atomic-claim annotation).

Faithfulness is skipped for out-of-scope questions, refusals, and items without
retrieved context (PRD section 8.1). Because judging every answer costs a lot of
gateway calls, scores are cached in ``data/analysis/faithfulness/E{XX}.json`` and
reused when the answer text is unchanged.

Usage:
    # full evaluation (needs ground truth + results + judge access)
    .venv310/bin/python scripts/evaluate.py

    # retrieval metrics only, no judge calls
    .venv310/bin/python scripts/evaluate.py --no-judge

    # smoke test on a subset
    .venv310/bin/python scripts/evaluate.py --codes E16 --limit 5
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag_service.evaluation import (  # noqa: E402
    EvaluationError,
    FaithfulnessCache,
    FaithfulnessError,
    RagasFaithfulnessScorer,
    evaluate_experiment,
    load_ground_truth,
    load_results,
    write_details_json,
    write_summary_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate RAG experiment results (faithfulness + IR metrics)."
    )
    parser.add_argument(
        "--results-dir",
        default=str(PROJECT_ROOT / "data" / "results"),
        help="Directory holding E{XX}_results.json files.",
    )
    parser.add_argument(
        "--ground-truth",
        default=str(PROJECT_ROOT / "data" / "evaluation" / "ground_truth.json"),
        help="Ground-truth dataset produced by Task 1.3.",
    )
    parser.add_argument(
        "--output",
        default=str(PROJECT_ROOT / "data" / "analysis" / "evaluation_summary.csv"),
        help="Aggregate summary CSV to write.",
    )
    parser.add_argument(
        "--details",
        default=str(PROJECT_ROOT / "data" / "analysis" / "evaluation_details.json"),
        help="Per-item details JSON to write.",
    )
    parser.add_argument(
        "--cache-dir",
        default=str(PROJECT_ROOT / "data" / "analysis" / "faithfulness"),
        help="Directory for per-experiment faithfulness score caches.",
    )
    parser.add_argument(
        "--codes",
        nargs="+",
        default=None,
        help="Experiment codes to evaluate (default: every E*.json found).",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=5,
        help="Cut-off for Hit@k / MRR@k / nDCG@k (default: 5).",
    )
    parser.add_argument(
        "--no-judge",
        action="store_true",
        help="Skip faithfulness entirely and compute only IR metrics.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Evaluate at most N items per experiment (smoke testing).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print the final summary.",
    )
    return parser.parse_args()


def discover_codes(results_dir: Path, codes) -> list:
    """Return the experiment codes to evaluate, in sorted order."""
    if codes:
        return [code.strip().upper() for code in codes]
    return sorted(path.stem.replace("_results", "") for path in results_dir.glob("E*_results.json"))


def enrich_from_config(code: str, payload: dict) -> dict:
    """Fill chunking/retrieval labels from the YAML config when available."""
    if payload.get("chunking_strategy") and payload.get("retrieval_method"):
        return payload
    try:
        from rag_service.config import load_config

        config = load_config(code)
    except Exception:  # noqa: BLE001 - labels are cosmetic, never fatal
        return payload

    enriched = dict(payload)
    enriched.setdefault("chunking_strategy", config.chunking_strategy)
    enriched.setdefault("retrieval_method", config.retrieval_method)
    enriched.setdefault("reranker_enabled", config.reranker_enabled)
    return enriched


def build_scorer(args) -> "RagasFaithfulnessScorer | None":
    """Create the judge-backed faithfulness scorer unless disabled."""
    if args.no_judge:
        return None
    try:
        scorer = RagasFaithfulnessScorer()
    except (FaithfulnessError, Exception) as exc:  # noqa: BLE001 - setup boundary
        print(
            json.dumps(
                {
                    "status": "error",
                    "message": f"judge tidak bisa disiapkan: {exc}",
                    "hint": "Perbaiki JUDGE_* di .env, atau jalankan dengan --no-judge.",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        raise SystemExit(1)
    if not args.quiet:
        print("Juri faithfulness:")
        for key, value in scorer.snapshot_metadata().items():
            print(f"  {key}: {value}")
    return scorer


def main() -> int:
    args = parse_args()
    results_dir = Path(args.results_dir)
    codes = discover_codes(results_dir, args.codes)

    if not codes:
        print(
            json.dumps(
                {
                    "status": "error",
                    "message": f"tidak ada hasil eksperimen di {results_dir}",
                    "hint": "Jalankan scripts/run_experiments.py (Task 4.1) lebih dulu.",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    try:
        ground_truth = load_ground_truth(Path(args.ground_truth))
    except EvaluationError as exc:
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

    if not ground_truth:
        print(
            json.dumps(
                {"status": "error", "message": "ground truth kosong"},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    scorer = build_scorer(args)
    cache_dir = Path(args.cache_dir)

    evaluations = []
    for code in codes:
        path = results_dir / f"{code}_results.json"
        try:
            payload = enrich_from_config(code, load_results(path))
        except EvaluationError as exc:
            print(f"Lewati {code}: {exc}")
            continue

        cache = FaithfulnessCache.load(cache_dir / f"{code}.json")
        evaluation = evaluate_experiment(
            code,
            payload,
            ground_truth,
            scorer=scorer,
            k=args.k,
            cache=cache,
            limit=args.limit,
        )
        cache.save()
        evaluations.append(evaluation)

        if not args.quiet:
            summary = evaluation.summary
            print(
                f"{code}: {summary['items_total']} item, "
                f"faithfulness={summary[f'faithfulness_mean']} "
                f"({evaluation.faithful_scored} dinilai), "
                f"Hit@{args.k}={summary[f'hit_at_{args.k}']}, "
                f"MRR@{args.k}={summary[f'mrr_at_{args.k}']}, "
                f"nDCG@{args.k}={summary[f'ndcg_at_{args.k}']}"
            )
            if evaluation.faithfulness_skipped:
                print(f"  faithfulness dilewati: {evaluation.faithfulness_skipped}")

    if not evaluations:
        print(json.dumps({"status": "error", "message": "tidak ada yang dievaluasi"}, indent=2))
        return 1

    summary_path = Path(args.output)
    details_path = Path(args.details)
    write_summary_csv([e.summary for e in evaluations], summary_path, k=args.k)
    write_details_json(evaluations, details_path, k=args.k)

    print(
        json.dumps(
            {
                "status": "ok",
                "experiments_evaluated": [e.code for e in evaluations],
                "summary_csv": str(summary_path),
                "details_json": str(details_path),
                "k": args.k,
                "judge_used": scorer is not None,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
