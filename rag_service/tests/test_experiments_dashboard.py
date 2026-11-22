"""Tests for the Streamlit dashboard data assembly (Task 3.6)."""

import json

from rag_service.experiments.dashboard import (
    available_values,
    build_item_table,
    filter_items,
    load_answers,
    load_details,
    load_ground_truth,
    load_summary,
    metric_means,
)

GROUND_TRUTH = [
    {
        "id": "gt-001",
        "question": "Apa syarat usia?",
        "ground_truth_answer": "18-30 tahun",
        "source_type": "pdf",
        "category": "factual",
    },
    {
        "id": "gt-002",
        "question": "Bagaimana alur pendaftaran?",
        "ground_truth_answer": "Lewat /daftar",
        "source_type": "web",
        "category": "procedural",
    },
]

DETAILS = [
    {
        "experiment_code": "E01",
        "items": [
            {
                "id": "gt-001",
                "question": "Apa syarat usia?",
                "category": "factual",
                "faithfulness": 0.9,
                "hit_at_5": 1.0,
                "mrr_at_5": 1.0,
                "ndcg_at_5": 1.0,
                "latency_ms": 100.0,
            },
            {
                "id": "gt-002",
                "question": "Bagaimana alur pendaftaran?",
                "category": "procedural",
                "faithfulness": 0.5,
                "hit_at_5": 0.0,
                "latency_ms": 200.0,
            },
        ],
    },
    {
        "experiment_code": "E02",
        "items": [
            {
                "id": "gt-001",
                "question": "Apa syarat usia?",
                "category": "factual",
                "faithfulness": 1.0,
                "hit_at_5": 1.0,
                "latency_ms": 300.0,
            }
        ],
    },
]


def test_load_summary_missing_returns_empty(tmp_path):
    summary = load_summary(tmp_path / "nope.csv")
    assert summary.empty
    assert "experiment_code" in summary.columns


def test_load_details_missing_and_invalid(tmp_path):
    assert load_details(tmp_path / "nope.json") == []
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    assert load_details(bad) == []


def test_load_ground_truth_indexes_by_id(tmp_path):
    path = tmp_path / "gt.json"
    path.write_text(json.dumps(GROUND_TRUTH), encoding="utf-8")
    index = load_ground_truth(path)
    assert index["gt-001"]["source_type"] == "pdf"
    assert set(index) == {"gt-001", "gt-002"}


def test_load_answers_reads_raw_results(tmp_path):
    path = tmp_path / "E01_results.json"
    path.write_text(
        json.dumps({"experiment_code": "E01", "items": [{"id": "gt-001", "answer": "bot"}]}),
        encoding="utf-8",
    )
    answers = load_answers(tmp_path)
    assert answers[("E01", "gt-001")] == "bot"


def test_build_item_table_merges_answer_and_truth(tmp_path):
    path = tmp_path / "E01_results.json"
    path.write_text(
        json.dumps({"experiment_code": "E01", "items": [{"id": "gt-001", "answer": "bot"}]}),
        encoding="utf-8",
    )
    items = build_item_table(
        DETAILS, load_ground_truth(ground_truth_path(tmp_path)), load_answers(tmp_path)
    )
    row = items[(items["experiment_code"] == "E01") & (items["id"] == "gt-001")].iloc[0]
    assert row["answer"] == "bot"
    assert row["ground_truth_answer"] == "18-30 tahun"
    assert row["source_type"] == "pdf"
    assert items.shape[0] == 3


def ground_truth_path(tmp_path):
    path = tmp_path / "gt.json"
    path.write_text(json.dumps(GROUND_TRUTH), encoding="utf-8")
    return path


def build_items(tmp_path):
    return build_item_table(
        DETAILS, load_ground_truth(ground_truth_path(tmp_path)), {}
    )


def test_filter_items_by_code_source_and_category(tmp_path):
    items = build_items(tmp_path)

    assert set(filter_items(items, codes=["E02"])["experiment_code"]) == {"E02"}
    assert set(filter_items(items, source_types=["web"])["id"]) == {"gt-002"}
    assert set(filter_items(items, categories=["factual"])["id"]) == {"gt-001"}
    assert len(filter_items(items, codes=["E01"], categories=["factual"])) == 1


def test_filter_items_ignores_empty_selection(tmp_path):
    items = build_items(tmp_path)
    assert filter_items(items, codes=[], source_types=None) is items


def test_metric_means(tmp_path):
    summary_path = tmp_path / "evaluation_summary.csv"
    summary_path.write_text(
        "experiment_code,faithfulness_mean,hit_at_5,latency_ms_mean\n"
        "E01,0.7,1.0,100\n"
        "E02,0.9,0.5,300\n",
        encoding="utf-8",
    )
    means = dict(zip(*metric_means(load_summary(summary_path)).values.T))
    assert means["faithfulness_mean"] == 0.8
    assert means["hit_at_5"] == 0.75
    assert means["latency_ms_mean"] == 200.0


def test_metric_means_empty():
    import pandas as pd

    assert metric_means(pd.DataFrame()).empty


def test_available_values(tmp_path):
    items = build_items(tmp_path)
    assert available_values(items, "experiment_code") == ["E01", "E02"]
    assert available_values(items, "id") == ["gt-001", "gt-002"]
    assert available_values(items, "missing") == []
