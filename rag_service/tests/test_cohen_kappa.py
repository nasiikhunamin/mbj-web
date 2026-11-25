"""Tests for the atomic-claim Cohen's kappa module (Task 4.4)."""

import csv
import json
from pathlib import Path

import pytest

from rag_service.statistics.cohen_kappa import (
    KappaError,
    bootstrap_ci,
    build_report,
    cohen_kappa,
    interpret_kappa,
    load_annotations,
    normalize_label,
    sample_template,
)


def pairs_from_counts(both_1, both_0, human_1_judge_0, human_0_judge_1):
    return (
        [(1, 1)] * both_1
        + [(0, 0)] * both_0
        + [(1, 0)] * human_1_judge_0
        + [(0, 1)] * human_0_judge_1
    )


# ----------------------------------------------------------------------
# Core calculation
# ----------------------------------------------------------------------


def test_kappa_known_example():
    # po = 0.70, pe = 0.50 -> kappa = 0.40
    pairs = pairs_from_counts(40, 30, 10, 20)
    result = cohen_kappa(pairs, bootstrap=200)

    assert result.n == 100
    assert result.observed_agreement == pytest.approx(0.70)
    assert result.expected_agreement == pytest.approx(0.50)
    assert result.kappa == pytest.approx(0.40)
    assert result.interpretation == "fair"
    assert result.meets_target is False


def test_kappa_perfect_agreement():
    pairs = pairs_from_counts(50, 50, 0, 0)
    result = cohen_kappa(pairs, bootstrap=100)

    assert result.kappa == pytest.approx(1.0)
    assert result.interpretation == "almost perfect"
    assert result.meets_target is True


def test_kappa_is_undefined_when_both_raters_are_constant():
    result = cohen_kappa([(1, 1)] * 20, bootstrap=100)

    assert result.kappa is None
    assert result.ci_low is None
    assert result.ci_high is None
    assert result.interpretation == "tidak terdefinisi"
    assert result.meets_target is False


def test_bootstrap_ci_contains_point_estimate_and_is_reproducible():
    pairs = pairs_from_counts(40, 30, 10, 20)
    low, high = bootstrap_ci(pairs, iterations=500, seed=7)

    assert low is not None and high is not None
    assert low <= 0.40 <= high
    assert bootstrap_ci(pairs, iterations=500, seed=7) == (low, high)


def test_kappa_rejects_empty_input():
    with pytest.raises(KappaError):
        cohen_kappa([])


def test_interpretation_bands():
    assert interpret_kappa(None) == "tidak terdefinisi"
    assert interpret_kappa(-0.1) == "poor"
    assert interpret_kappa(0.1) == "slight"
    assert interpret_kappa(0.3) == "fair"
    assert interpret_kappa(0.5) == "moderate"
    assert interpret_kappa(0.7) == "substantial"
    assert interpret_kappa(0.9) == "almost perfect"


def test_normalize_label_accepts_common_variants():
    assert normalize_label(1) == 1
    assert normalize_label(0) == 0
    assert normalize_label(True) == 1
    assert normalize_label(False) == 0
    assert normalize_label("ya") == 1
    assert normalize_label("TIDAK") == 0
    assert normalize_label("valid") == 1
    assert normalize_label("not_supported") == 0

    with pytest.raises(KappaError, match="tidak valid"):
        normalize_label("mungkin")


# ----------------------------------------------------------------------
# Annotation loading
# ----------------------------------------------------------------------


def write_csv(path: Path, rows, fieldnames=None):
    fieldnames = fieldnames or [
        "experiment_code",
        "item_id",
        "claim_id",
        "claim_text",
        "human_label",
        "judge_label",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_load_annotations_skips_blank_template_rows(tmp_path):
    path = tmp_path / "annotations.csv"
    write_csv(
        path,
        [
            {
                "experiment_code": "E16",
                "item_id": "gt-001",
                "claim_id": "c1",
                "claim_text": "Usia 18-30 tahun",
                "human_label": "1",
                "judge_label": "ya",
            },
            {
                "experiment_code": "E16",
                "item_id": "gt-001",
                "claim_id": "c2",
                "claim_text": "",
                "human_label": "",
                "judge_label": "",
            },
            {
                "experiment_code": "E16",
                "item_id": "gt-002",
                "claim_id": "c1",
                "claim_text": "Minimal SMA/SMK",
                "human_label": "0",
                "judge_label": "TIDAK",
            },
        ],
    )

    annotations = load_annotations(path)

    assert len(annotations) == 2
    assert annotations[0]["human_label"] == 1
    assert annotations[0]["judge_label"] == 1
    assert annotations[1]["human_label"] == 0
    assert annotations[1]["judge_label"] == 0


def test_load_annotations_rejects_half_filled_row(tmp_path):
    path = tmp_path / "annotations.csv"
    write_csv(
        path,
        [
            {
                "experiment_code": "E16",
                "item_id": "gt-001",
                "claim_id": "c1",
                "claim_text": "Usia 18-30 tahun",
                "human_label": "1",
                "judge_label": "",
            }
        ],
    )

    with pytest.raises(KappaError, match="harus diisi bersama"):
        load_annotations(path)


def test_load_annotations_accepts_json(tmp_path):
    path = tmp_path / "annotations.json"
    path.write_text(
        json.dumps(
            [
                {"experiment_code": "E16", "human_label": 1, "judge_label": 1},
                {"experiment_code": "E16", "human_label": 0, "judge_label": 0},
            ]
        ),
        encoding="utf-8",
    )

    annotations = load_annotations(path)
    assert len(annotations) == 2


# ----------------------------------------------------------------------
# Report and template
# ----------------------------------------------------------------------


def test_build_report_groups_by_experiment():
    annotations = [
        {"experiment_code": "E16", "human_label": 1, "judge_label": 1},
        {"experiment_code": "E16", "human_label": 0, "judge_label": 0},
        {"experiment_code": "E01", "human_label": 1, "judge_label": 0},
        {"experiment_code": "E01", "human_label": 0, "judge_label": 1},
    ]

    report = build_report(
        annotations,
        input_path=Path("annotations.csv"),
        target=0.70,
        bootstrap=50,
        seed=1,
    )

    assert report["rows_used"] == 4
    assert set(report["by_experiment"]) == {"E01", "E16"}
    assert report["overall"]["n"] == 4


def write_results(path: Path, code: str, items):
    path.write_text(
        json.dumps({"experiment_code": code, "items": items}),
        encoding="utf-8",
    )


def test_sample_template_is_deterministic_and_skips_out_of_scope(tmp_path):
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    items = [
        {
            "id": f"gt-{index:03d}",
            "question": f"Q{index}",
            "answer": f"A{index}",
            "category": "factual",
            "source_type": "web",
            "is_refusal": False,
            "is_out_of_scope": False,
        }
        for index in range(1, 5)
    ]
    items.append(
        {
            "id": "gt-999",
            "question": "Out of scope",
            "answer": "",
            "category": "out_of_scope",
            "source_type": "web",
            "is_refusal": True,
            "is_out_of_scope": True,
        }
    )
    write_results(results_dir / "E01_results.json", "E01", items)
    write_results(results_dir / "E02_results.json", "E02", items)

    first = tmp_path / "first.csv"
    second = tmp_path / "second.csv"
    count = sample_template(
        results_dir, first, fraction=1.0, seed=42
    )
    sample_template(results_dir, second, fraction=1.0, seed=42)

    assert count == 8  # 4 eligible responses x 2 experiments
    assert first.read_text(encoding="utf-8-sig") == second.read_text(encoding="utf-8-sig")

    with first.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 8
    assert {row["experiment_code"] for row in rows} == {"E01", "E02"}
    assert all(row["claim_text"] == "" for row in rows)
    assert all(row["human_label"] == "" for row in rows)
    assert all(row["item_id"] != "gt-999" for row in rows)
