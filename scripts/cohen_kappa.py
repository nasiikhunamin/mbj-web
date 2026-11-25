#!/usr/bin/env python3
"""Cohen's kappa for atomic-claim validation (Task 4.4).

Two modes:

1. **Calculate** agreement from a filled annotation file::

       .venv310/bin/python scripts/cohen_kappa.py \
           --input data/analysis/cohen_kappa_annotations.csv

   Writes ``data/analysis/cohen_kappa.json`` and prints the overall kappa,
   95% bootstrap CI, interpretation, and whether the 0.70 target is met.

2. **Create the 20% annotation template** from the experiment results::

       .venv310/bin/python scripts/cohen_kappa.py --make-template \
           --results-dir data/results \
           --output data/analysis/cohen_kappa_annotations.csv

   One row is written per sampled response. The annotator duplicates a row for
   every atomic claim, then fills ``claim_id``, ``claim_text``,
   ``human_label`` and ``judge_label`` (0/1).
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag_service.statistics.cohen_kappa import (  # noqa: E402
    DEFAULT_BOOTSTRAP,
    DEFAULT_SEED,
    DEFAULT_TARGET,
    KappaError,
    build_report,
    load_annotations,
    sample_template,
    write_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Hitung Cohen's kappa untuk validasi juri LLM vs anotasi manusia."
    )
    parser.add_argument(
        "--input",
        default=str(PROJECT_ROOT / "data" / "analysis" / "cohen_kappa_annotations.csv"),
        help="File anotasi CSV/JSON dengan kolom human_label dan judge_label.",
    )
    parser.add_argument(
        "--output",
        default=str(PROJECT_ROOT / "data" / "analysis" / "cohen_kappa.json"),
        help="Lokasi laporan JSON (mode hitung) atau template CSV (mode template).",
    )
    parser.add_argument(
        "--target",
        type=float,
        default=DEFAULT_TARGET,
        help="Ambang kappa minimum (default 0.70).",
    )
    parser.add_argument(
        "--bootstrap",
        type=int,
        default=DEFAULT_BOOTSTRAP,
        help="Jumlah resampel bootstrap untuk CI 95%% (default 2000).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Seed bootstrap/sampling agar reproducible (default 42).",
    )
    parser.add_argument(
        "--make-template",
        action="store_true",
        help="Buat template anotasi 20%% dari data/results, bukan menghitung kappa.",
    )
    parser.add_argument(
        "--results-dir",
        default=str(PROJECT_ROOT / "data" / "results"),
        help="Folder E*_results.json untuk mode template.",
    )
    parser.add_argument(
        "--fraction",
        type=float,
        default=0.20,
        help="Proporsi respons yang disampel per eksperimen (default 0.20).",
    )
    parser.add_argument(
        "--include-refusals",
        action="store_true",
        help="Ikutkan jawaban refusal dalam sampel (default: hanya jawaban in-domain).",
    )
    parser.add_argument("--quiet", action="store_true", help="Hanya cetak ringkasan JSON.")
    return parser.parse_args()


def _format_interval(result: dict) -> str:
    low, high = result.get("ci95") or [None, None]
    if low is None or high is None:
        return "CI tidak tersedia"
    return f"95% CI {low:.3f}–{high:.3f}"


def main() -> int:
    args = parse_args()

    try:
        if args.make_template:
            output_path = Path(args.output)
            # Bila user memakai default tanpa --output khusus, arahkan ke CSV agar mudah dibuka di Excel
            if output_path.suffix == ".json" and args.output == str(PROJECT_ROOT / "data" / "analysis" / "cohen_kappa.json"):
                output_path = PROJECT_ROOT / "data" / "analysis" / "cohen_kappa_annotations.csv"

            count = sample_template(
                Path(args.results_dir),
                output_path,
                fraction=args.fraction,
                seed=args.seed,
                include_refusals=args.include_refusals,
            )
            print(
                json.dumps(
                    {
                        "status": "ok",
                        "mode": "template",
                        "output": str(output_path),
                        "rows_sampled": count,
                        "fraction": args.fraction,
                        "seed": args.seed,
                        "hint": "Buka file CSV di Excel/Google Sheets, lalu isi kolom claim_id, claim_text, human_label (1/0), dan judge_label (1/0).",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0

        annotations = load_annotations(Path(args.input))
        report = build_report(
            annotations,
            input_path=Path(args.input),
            target=args.target,
            bootstrap=args.bootstrap,
            seed=args.seed,
        )
        write_report(report, Path(args.output))
    except KappaError as exc:
        print(
            json.dumps(
                {
                    "status": "error",
                    "message": str(exc),
                    "hint": (
                        "Jalankan --make-template lebih dulu, isi anotasinya, "
                        "lalu jalankan tanpa --make-template."
                    ),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    overall = report["overall"]
    agreement = report.get("percent_agreement", {})
    if not args.quiet:
        agr_pct = agreement.get("percentage")
        if agr_pct is not None:
            agr_low, agr_high = agreement.get("ci95") or [None, None]
            interval = (
                f" [{agr_low * 100:.1f}%–{agr_high * 100:.1f}%]"
                if agr_low is not None and agr_high is not None
                else ""
            )
            print(
                f"Percent agreement (n={overall['n']} klaim): "
                f"{agr_pct:.2f}%{interval} — {agreement.get('interpretation')}"
            )
            print(
                f"Target agreement {agreement.get('target', 0.90):.2f}: "
                f"{'TERCAPAI' if agreement.get('meets_target') else 'BELUM tercapai'}"
            )
        print(
            f"Cohen's kappa (n={overall['n']} klaim): "
            f"{overall['kappa']:.3f} "
            f"[{_format_interval(overall)}] — {overall['interpretation']}"
        )
        print(
            f"Target kappa {overall['target']:.2f}: "
            f"{'TERCAPAI' if overall['meets_target'] else 'BELUM tercapai'}"
        )
        for code, result in report["by_experiment"].items():
            kappa = result["kappa"]
            shown = "tidak terdefinisi" if kappa is None else f"{kappa:.3f}"
            print(f"  {code}: kappa={shown} ({result['interpretation']}, n={result['n']})")

    print(
        json.dumps(
            {
                "status": "ok",
                "mode": "calculate",
                "output": str(Path(args.output)),
                "rows_used": report["rows_used"],
                "percent_agreement": report.get("percent_agreement"),
                "overall": overall,
                "by_experiment": report["by_experiment"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
