#!/usr/bin/env python3
"""Generate the publication figures for the RAG experiment (Task 4.6).

Reads ``data/analysis/evaluation_summary.csv`` (Task 4.2) and writes three
300 DPI PNGs to ``data/analysis/figures/`` (heatmap, retrieval bars, interaction
plot).

Usage:
    .venv310/bin/python scripts/generate_plots.py
    .venv310/bin/python scripts/generate_plots.py --metric hit_at_5
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag_service.statistics.plots import PlotError, generate_all  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the experiment result figures.")
    parser.add_argument(
        "--summary",
        default=str(PROJECT_ROOT / "data" / "analysis" / "evaluation_summary.csv"),
        help="Aggregate summary CSV produced by scripts/evaluate.py.",
    )
    parser.add_argument(
        "--out-dir",
        default=str(PROJECT_ROOT / "data" / "analysis" / "figures"),
        help="Directory for the PNG figures.",
    )
    parser.add_argument(
        "--metric",
        default="faithfulness_mean",
        help="Metric for the heatmap and interaction plot (default: faithfulness_mean).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary_path = Path(args.summary)
    if not summary_path.exists():
        print(
            json.dumps(
                {
                    "status": "error",
                    "message": f"summary not found: {summary_path}",
                    "hint": "Jalankan scripts/run_experiments.py lalu scripts/evaluate.py.",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    summary = pd.read_csv(summary_path)
    try:
        figures = generate_all(summary, Path(args.out_dir), metric=args.metric)
    except PlotError as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    print(
        json.dumps(
            {
                "status": "ok",
                "metric": args.metric,
                "figures": {name: str(path) for name, path in figures.items()},
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
