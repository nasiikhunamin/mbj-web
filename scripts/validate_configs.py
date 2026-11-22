#!/usr/bin/env python3
"""Validate the locked E01-E16 experiment configuration files (Task 2.15).

Usage (from the repository root)::

    .venv310/bin/python scripts/validate_configs.py

The validator checks that:

* exactly the 16 expected YAML files exist,
* each file loads through :class:`rag_service.config.ExperimentConfig`,
* the code, chunking strategy, and retrieval method match the 4x4 matrix,
* tokenizer, token limits, RRF, embedding prefixes, reranker, generator, and
  output paths match the parameters locked by the PRD.
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag_service.config import (  # noqa: E402
    expected_experiment_matrix,
    validate_configs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the E01-E16 experiment YAML files."
    )
    parser.add_argument(
        "--config-dir",
        default=None,
        help="Directory containing E01.yaml-E16.yaml (default: rag_service/configs).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    expected = expected_experiment_matrix()
    errors = validate_configs(args.config_dir)

    print("Experiment matrix:")
    print(f"  {'Code':<6}{'Chunking':<18}{'Retrieval':<16}Rerank")
    for code in sorted(expected):
        chunking, retrieval = expected[code]
        rerank = "yes" if retrieval == "hybrid_rerank" else "no"
        print(f"  {code:<6}{chunking:<18}{retrieval:<16}{rerank}")

    if errors:
        print("\nINVALID CONFIGURATION")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(f"\nOK: {len(expected)} experiment configurations are valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
