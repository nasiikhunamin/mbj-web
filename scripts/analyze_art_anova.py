#!/usr/bin/env python3
"""ART ANOVA + Benjamini-Hochberg post-hoc for the experiment results (Task 4.5).

Reads the per-item metrics from ``data/analysis/evaluation_details.json`` (Task
4.2) and writes ``data/analysis/art_anova_results.txt``.

The analysis runs in Python (see ``rag_service/statistics/art_anova.py``). The
ART method follows Wobbrock et al. (2011); results must still be cross-checked
against the reference R ``ARTool`` package before they are reported.

Usage:
    .venv310/bin/python scripts/analyze_art_anova.py
    .venv310/bin/python scripts/analyze_art_anova.py --metric faithfulness --details path.json
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag_service.config import expected_experiment_matrix  # noqa: E402
from rag_service.statistics.art_anova import (  # noqa: E402
    ArtAnovaError,
    art_anova,
    art_contrasts,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run ART ANOVA over the per-item evaluation details.")
    parser.add_argument(
        "--details",
        default=str(PROJECT_ROOT / "data" / "analysis" / "evaluation_details.json"),
        help="Per-item details JSON produced by scripts/evaluate.py (Task 4.2).",
    )
    parser.add_argument(
        "--output",
        default=str(PROJECT_ROOT / "data" / "analysis" / "art_anova_results.txt"),
        help="Text report to write.",
    )
    parser.add_argument(
        "--metric",
        default="faithfulness",
        help="Per-item metric column to analyse (default: faithfulness).",
    )
    parser.add_argument("--quiet", action="store_true", help="Only print the summary.")
    return parser.parse_args()


def load_long_frame(details_path: Path, metric: str) -> pd.DataFrame:
    """Build a long subject x chunking x retrieval x metric frame."""
    payload = json.loads(Path(details_path).read_text(encoding="utf-8"))
    experiments = payload.get("experiments") if isinstance(payload, dict) else None
    if not isinstance(experiments, list) or not experiments:
        raise ArtAnovaError(f"{details_path}: no 'experiments' found")

    matrix = expected_experiment_matrix()
    rows = []
    for experiment in experiments:
        code = str(experiment.get("experiment_code") or "")
        if code not in matrix:
            continue
        chunking, retrieval = matrix[code]
        for item in experiment.get("items") or []:
            value = item.get(metric)
            if not isinstance(value, (int, float)) or item.get("is_out_of_scope") or item.get("is_refusal"):
                continue
            rows.append(
                {
                    "subject": str(item.get("id") or ""),
                    "chunking": chunking,
                    "retrieval": retrieval,
                    metric: float(value),
                }
            )

    frame = pd.DataFrame(rows)
    if frame.empty:
        raise ArtAnovaError(
            f"no {metric!r} values found; run scripts/evaluate.py (Task 4.2) first"
        )
    return frame


def format_report(metric: str, frame: pd.DataFrame, omnibus: dict, contrasts: dict) -> str:
    """Render the ART ANOVA result as a plain-text report."""
    lines = [
        f"ART ANOVA — {metric}",
        "Metode: Aligned Rank Transform (Wobbrock et al. 2011), desain 4x4 within-subject.",
        "CATATAN: implementasi Python; wajib divalidasi silang ke paket R ARTool sebelum dilaporkan.",
        "",
        f"Jumlah subjek (pertanyaan): {frame['subject'].nunique()}",
        f"Jumlah observasi lengkap: {len(frame)}",
        "",
        "== Uji Omnibus ==",
    ]
    labels = {
        "a": "Efek utama Chunking",
        "b": "Efek utama Retrieval",
        "interaction": "Interaksi Chunking x Retrieval",
    }
    for key, result in omnibus.items():
        significant = "signifikan" if result["p"] < 0.05 else "tidak signifikan"
        lines.append(
            f"  {labels[key]}: F = {result['F']:.4f}, p = {result['p']:.6f} ({significant})"
        )

    for key, label in (("a", "Faktor Chunking"), ("b", "Faktor Retrieval")):
        table = contrasts.get(key)
        lines.extend(["", f"== Post-hoc {label} (Benjamini-Hochberg) =="])
        if table is None or table.empty:
            lines.append("  (tidak ada kontras)")
            continue
        for _, row in table.iterrows():
            significant = "signifikan" if row["p_adjusted"] < 0.05 else "tidak signifikan"
            lines.append(
                f"  {row['pair']}: t = {row['t']:.4f}, "
                f"p = {row['p']:.6f}, p_FDR = {row['p_adjusted']:.6f} ({significant})"
            )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    try:
        frame = load_long_frame(Path(args.details), args.metric)
        omnibus = art_anova(
            frame,
            subject="subject",
            factor_a="chunking",
            factor_b="retrieval",
            value=args.metric,
        )
        contrasts = {
            "a": art_contrasts(
                frame,
                subject="subject",
                factor_a="chunking",
                factor_b="retrieval",
                value=args.metric,
                family="a",
            ),
            "b": art_contrasts(
                frame,
                subject="subject",
                factor_a="chunking",
                factor_b="retrieval",
                value=args.metric,
                family="b",
            ),
        }
    except (ArtAnovaError, OSError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {
                    "status": "error",
                    "message": str(exc),
                    "hint": "ART ANOVA butuh data/analysis/evaluation_details.json (Task 4.2).",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    report = format_report(args.metric, frame, omnibus, contrasts)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")

    if not args.quiet:
        print(report)
    print(
        json.dumps(
            {
                "status": "ok",
                "output": str(output_path),
                "metric": args.metric,
                "subjects": frame["subject"].nunique(),
                "observations": len(frame),
                "omnibus": omnibus,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
