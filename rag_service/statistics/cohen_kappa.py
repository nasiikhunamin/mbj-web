"""Cohen's kappa for atomic-claim validation (Task 4.4).

The RAGAS faithfulness score is produced by an LLM judge. Before it can be
reported in the thesis, a human annotator must label a sample of atomic claims
and the agreement between the human and the judge must be measured. This module
provides the calculator; ``scripts/cohen_kappa.py`` provides the CLI and a
template generator for the 20% sample.

Input contract (CSV or JSON): one row per atomic claim with the columns
``human_label`` and ``judge_label`` (0/1). Optional columns are
``experiment_code``, ``item_id``, ``claim_id`` and ``claim_text``.

Example::

    experiment_code,item_id,claim_id,claim_text,human_label,judge_label
    E16,gt-001,c1,"Peserta berusia 18-30 tahun",1,1
    E16,gt-001,c2,"Peserta minimal SMA/SMK",1,0

Rows where both labels are blank are ignored (they are unfilled template rows).
A row with only one label filled is rejected so half-annotated data cannot be
silently counted.
"""

from __future__ import annotations

import csv
import json
import math
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


class KappaError(RuntimeError):
    """Raised when annotations or configuration cannot be processed."""


POSITIVE_LABELS = {
    "1",
    "true",
    "yes",
    "y",
    "ya",
    "valid",
    "supported",
    "faithful",
    "didukung",
}
NEGATIVE_LABELS = {
    "0",
    "false",
    "no",
    "n",
    "tidak",
    "invalid",
    "unsupported",
    "unfaithful",
    "not_supported",
    "tidak_didukung",
}

DEFAULT_TARGET = 0.70
DEFAULT_BOOTSTRAP = 2000
DEFAULT_SEED = 42


@dataclass(frozen=True)
class KappaResult:
    """Agreement statistics for one set of claim-level labels."""

    n: int
    observed_agreement: float
    expected_agreement: float
    kappa: Optional[float]
    ci_low: Optional[float]
    ci_high: Optional[float]
    agreement_ci_low: Optional[float]
    agreement_ci_high: Optional[float]
    interpretation: str
    meets_target: bool
    target: float
    confusion: Dict[str, int]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "n": self.n,
            "observed_agreement": self.observed_agreement,
            "expected_agreement": self.expected_agreement,
            "kappa": self.kappa,
            "ci95": [self.ci_low, self.ci_high],
            "agreement_ci95": [self.agreement_ci_low, self.agreement_ci_high],
            "interpretation": self.interpretation,
            "target": self.target,
            "meets_target": self.meets_target,
            "confusion": dict(self.confusion),
        }


def normalize_label(value: Any, *, field: str = "label", row: Optional[int] = None) -> int:
    """Normalize a human/judge label to 0 or 1.

    Accepts ``0/1``, booleans, and common Indonesian/English words. Anything
    else raises :class:`KappaError` instead of being silently coerced.
    """
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if float(value).is_integer() and int(value) in (0, 1):
            return int(value)

    text = str(value).strip().lower()
    if text in POSITIVE_LABELS:
        return 1
    if text in NEGATIVE_LABELS:
        return 0

    location = f" (row {row})" if row is not None else ""
    raise KappaError(
        f"{field}{location}: label tidak valid {value!r}; gunakan 0/1 atau ya/tidak"
    )


def _blank(value: Any) -> bool:
    return value is None or str(value).strip() == ""


def _counts(pairs: Sequence[Tuple[int, int]]) -> Dict[str, int]:
    both_1 = sum(1 for human, judge in pairs if human == 1 and judge == 1)
    both_0 = sum(1 for human, judge in pairs if human == 0 and judge == 0)
    human_1_judge_0 = sum(1 for human, judge in pairs if human == 1 and judge == 0)
    human_0_judge_1 = sum(1 for human, judge in pairs if human == 0 and judge == 1)
    return {
        "both_1": both_1,
        "both_0": both_0,
        "human_1_judge_0": human_1_judge_0,
        "human_0_judge_1": human_0_judge_1,
    }


def _kappa_from_counts(confusion: Mapping[str, int]) -> Tuple[float, float, Optional[float]]:
    """Return ``(observed_agreement, expected_agreement, kappa)``."""
    n = sum(int(value) for value in confusion.values())
    if n <= 0:
        raise KappaError("no annotations to score")

    both_1 = int(confusion["both_1"])
    both_0 = int(confusion["both_0"])
    human_1_judge_0 = int(confusion["human_1_judge_0"])
    human_0_judge_1 = int(confusion["human_0_judge_1"])

    observed = (both_1 + both_0) / n
    human_positive = (both_1 + human_1_judge_0) / n
    judge_positive = (both_1 + human_0_judge_1) / n
    expected = (
        human_positive * judge_positive
        + (1.0 - human_positive) * (1.0 - judge_positive)
    )

    if math.isclose(expected, 1.0):
        return observed, expected, None

    kappa = (observed - expected) / (1.0 - expected)
    return observed, expected, kappa


def _percentile(sorted_values: Sequence[float], percentile: float) -> Optional[float]:
    """Linear-interpolation percentile for a sorted sequence."""
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return float(sorted_values[0])

    position = (len(sorted_values) - 1) * percentile / 100.0
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return float(sorted_values[lower])

    fraction = position - lower
    return float(
        sorted_values[lower]
        + (sorted_values[upper] - sorted_values[lower]) * fraction
    )


def bootstrap_ci(
    pairs: Sequence[Tuple[int, int]],
    *,
    iterations: int = DEFAULT_BOOTSTRAP,
    seed: int = DEFAULT_SEED,
    confidence: float = 95.0,
) -> Tuple[Optional[float], Optional[float]]:
    """Percentile bootstrap confidence interval for Cohen's kappa."""
    if not pairs:
        return None, None
    if iterations <= 0:
        raise KappaError("bootstrap iterations must be positive")
    if not 0 < confidence < 100:
        raise KappaError("confidence must be between 0 and 100")

    rng = random.Random(seed)
    values: List[float] = []
    n = len(pairs)
    for _ in range(iterations):
        sample = [pairs[rng.randrange(n)] for _ in range(n)]
        _, _, kappa = _kappa_from_counts(_counts(sample))
        if kappa is not None:
            values.append(kappa)

    if not values:
        return None, None

    values.sort()
    tail = (100.0 - confidence) / 2.0
    return _percentile(values, tail), _percentile(values, 100.0 - tail)


def bootstrap_agreement_ci(
    pairs: Sequence[Tuple[int, int]],
    *,
    iterations: int = DEFAULT_BOOTSTRAP,
    seed: int = DEFAULT_SEED,
    confidence: float = 95.0,
) -> Tuple[Optional[float], Optional[float]]:
    """Percentile bootstrap confidence interval for observed agreement."""
    if not pairs:
        return None, None
    if iterations <= 0:
        raise KappaError("bootstrap iterations must be positive")

    rng = random.Random(seed)
    values: List[float] = []
    n = len(pairs)
    for _ in range(iterations):
        sample = [pairs[rng.randrange(n)] for _ in range(n)]
        confusion = _counts(sample)
        values.append(
            (confusion["both_1"] + confusion["both_0"]) / n
        )

    values.sort()
    tail = (100.0 - confidence) / 2.0
    return _percentile(values, tail), _percentile(values, 100.0 - tail)


def interpret_kappa(kappa: Optional[float]) -> str:
    """Landis & Koch (1977) interpretation bands."""
    if kappa is None:
        return "tidak terdefinisi"
    if kappa < 0:
        return "poor"
    if kappa <= 0.20:
        return "slight"
    if kappa <= 0.40:
        return "fair"
    if kappa <= 0.60:
        return "moderate"
    if kappa <= 0.80:
        return "substantial"
    return "almost perfect"


def interpret_percent_agreement(agreement: float) -> str:
    """Plain-English bands for observed (percent) agreement.

    Percent agreement is the primary, most interpretable metric; Cohen's kappa
    is reported alongside it as a chance-corrected supplementary value.
    """
    if agreement >= 0.95:
        return "excellent"
    if agreement >= 0.90:
        return "very good"
    if agreement >= 0.80:
        return "good"
    return "moderate"


DEFAULT_AGREEMENT_TARGET = 0.90


def cohen_kappa(
    pairs: Sequence[Tuple[int, int]],
    *,
    target: float = DEFAULT_TARGET,
    bootstrap: int = DEFAULT_BOOTSTRAP,
    seed: int = DEFAULT_SEED,
) -> KappaResult:
    """Compute Cohen's kappa plus a percentile bootstrap 95% CI."""
    if not pairs:
        raise KappaError("no annotations to score")

    confusion = _counts(pairs)
    observed, expected, kappa = _kappa_from_counts(confusion)
    ci_low, ci_high = bootstrap_ci(pairs, iterations=bootstrap, seed=seed)
    agreement_ci_low, agreement_ci_high = bootstrap_agreement_ci(
        pairs, iterations=bootstrap, seed=seed
    )

    return KappaResult(
        n=len(pairs),
        observed_agreement=observed,
        expected_agreement=expected,
        kappa=kappa,
        ci_low=ci_low,
        ci_high=ci_high,
        agreement_ci_low=agreement_ci_low,
        agreement_ci_high=agreement_ci_high,
        interpretation=interpret_kappa(kappa),
        meets_target=bool(kappa is not None and kappa >= target),
        target=target,
        confusion=confusion,
    )


def _read_rows(path: Path) -> List[Dict[str, Any]]:
    path = Path(path)
    if not path.exists():
        raise KappaError(f"annotation file not found: {path}")

    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]

    if path.suffix.lower() == ".json":
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise KappaError(f"{path} is not valid JSON: {exc}") from exc
        if isinstance(payload, dict):
            payload = payload.get("annotations") or payload.get("claims") or payload.get("items")
        if not isinstance(payload, list):
            raise KappaError(f"{path} must contain a list of annotation rows")
        return [dict(row) for row in payload if isinstance(row, dict)]

    raise KappaError("annotation file must be .csv or .json")


def load_annotations(path: Path) -> List[Dict[str, Any]]:
    """Load and validate claim-level annotations.

    Returns one normalized dict per usable row. Blank template rows are skipped;
    half-filled rows raise an error.
    """
    annotations: List[Dict[str, Any]] = []
    for index, row in enumerate(_read_rows(path), start=2):
        human_raw = row.get("human_label", row.get("human"))
        judge_raw = row.get("judge_label", row.get("judge", row.get("llm_label")))

        if _blank(human_raw) and _blank(judge_raw):
            continue
        if _blank(human_raw) or _blank(judge_raw):
            raise KappaError(
                f"row {index}: human_label dan judge_label harus diisi bersama "
                "(atau dikosongkan bersama untuk baris template)"
            )

        annotations.append(
            {
                "experiment_code": str(row.get("experiment_code") or "").strip(),
                "item_id": str(row.get("item_id") or "").strip(),
                "claim_id": str(row.get("claim_id") or "").strip(),
                "claim_text": str(row.get("claim_text") or "").strip(),
                "human_label": normalize_label(human_raw, field="human_label", row=index),
                "judge_label": normalize_label(judge_raw, field="judge_label", row=index),
            }
        )

    if not annotations:
        raise KappaError(f"{path}: no filled annotations found")
    return annotations


def _pairs(annotations: Iterable[Mapping[str, Any]]) -> List[Tuple[int, int]]:
    return [
        (int(row["human_label"]), int(row["judge_label"]))
        for row in annotations
    ]


def build_report(
    annotations: Sequence[Mapping[str, Any]],
    *,
    input_path: Path,
    target: float = DEFAULT_TARGET,
    bootstrap: int = DEFAULT_BOOTSTRAP,
    seed: int = DEFAULT_SEED,
) -> Dict[str, Any]:
    """Build the JSON report written to ``data/analysis/cohen_kappa.json``."""
    overall = cohen_kappa(_pairs(annotations), target=target, bootstrap=bootstrap, seed=seed)

    by_experiment: Dict[str, Any] = {}
    codes = sorted({str(row.get("experiment_code") or "") for row in annotations})
    for code in codes:
        if not code:
            continue
        subset = [row for row in annotations if str(row.get("experiment_code") or "") == code]
        if subset:
            by_experiment[code] = cohen_kappa(
                _pairs(subset), target=target, bootstrap=bootstrap, seed=seed
            ).to_dict()

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input": str(input_path),
        "method": (
            "Percent agreement (primary) with Cohen's kappa "
            "(chance-corrected, supplementary)"
        ),
        "target_kappa": target,
        "target_agreement": DEFAULT_AGREEMENT_TARGET,
        "bootstrap_iterations": bootstrap,
        "seed": seed,
        "rows_used": len(annotations),
        "percent_agreement": {
            "value": overall.observed_agreement,
            "percentage": overall.observed_agreement * 100.0,
            "ci95": [overall.agreement_ci_low, overall.agreement_ci_high],
            "interpretation": interpret_percent_agreement(overall.observed_agreement),
            "target": DEFAULT_AGREEMENT_TARGET,
            "meets_target": overall.observed_agreement >= DEFAULT_AGREEMENT_TARGET,
        },
        "overall": overall.to_dict(),
        "by_experiment": by_experiment,
    }


def write_report(report: Mapping[str, Any], path: Path) -> Path:
    """Write the kappa report as indented JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def _read_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sample_template(
    results_dir: Path,
    output: Path,
    *,
    fraction: float = 0.20,
    seed: int = DEFAULT_SEED,
    include_refusals: bool = False,
) -> int:
    """Create a CSV template by sampling ``fraction`` of in-domain responses.

    One row is written per sampled response. The annotator splits the answer
    into atomic claims by duplicating the row and filling ``claim_id``,
    ``claim_text``, ``human_label`` and ``judge_label``.
    """
    results_dir = Path(results_dir)
    if not 0 < fraction <= 1:
        raise KappaError("fraction must be in (0, 1]")

    paths = sorted(results_dir.glob("E*_results.json"))
    if not paths:
        raise KappaError(f"no E*_results.json found in {results_dir}")

    rng = random.Random(seed)
    rows: List[Dict[str, Any]] = []

    for path in paths:
        payload = _read_json(path)
        code = str(payload.get("experiment_code") or path.stem.replace("_results", ""))
        items = [
            item
            for item in (payload.get("items") or [])
            if isinstance(item, dict)
            and not item.get("is_out_of_scope")
            and (include_refusals or not item.get("is_refusal"))
            and str(item.get("answer") or "").strip()
        ]
        if not items:
            continue

        sample_size = max(1, math.ceil(len(items) * fraction))
        sampled = rng.sample(items, min(sample_size, len(items)))
        sampled.sort(key=lambda item: str(item.get("id") or ""))

        for item in sampled:
            rows.append(
                {
                    "experiment_code": code,
                    "item_id": str(item.get("id") or ""),
                    "question": str(item.get("question") or ""),
                    "answer": str(item.get("answer") or ""),
                    "category": str(item.get("category") or ""),
                    "source_type": str(item.get("source_type") or ""),
                    "is_refusal": bool(item.get("is_refusal")),
                    "claim_id": "",
                    "claim_text": "",
                    "human_label": "",
                    "judge_label": "",
                    "notes": "",
                }
            )

    if not rows:
        raise KappaError("no eligible responses to sample")

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)
