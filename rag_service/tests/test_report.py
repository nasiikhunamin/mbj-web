"""Tests for the evaluation report assembly and CSV export (Task 4.2)."""

import csv
import json
from types import SimpleNamespace

import pytest

from rag_service.evaluation.faithfulness import FaithfulnessScore
from rag_service.evaluation.report import (
    DEFAULT_K,
    EvaluationError,
    FaithfulnessCache,
    evaluate_experiment,
    load_ground_truth,
    load_results,
    write_details_json,
    write_summary_csv,
)

GROUND_TRUTH = [
    {
        "id": "gt-001",
        "question": "Apa syarat usia?",
        "ground_truth_answer": "18-30 tahun",
        "source_doc_ids": ["panduan_pendaftaran"],
        "source_type": "pdf",
        "evidence_text": "usia 18 sampai 30 tahun",
        "category": "factual",
        "is_out_of_scope": False,
    },
    {
        "id": "gt-002",
        "question": "Bagaimana alur pendaftaran?",
        "ground_truth_answer": "Lewat halaman /daftar",
        "source_doc_ids": ["panduan_pendaftaran"],
        "source_type": "pdf",
        "evidence_text": "pendaftaran melalui halaman /daftar",
        "category": "procedural",
        "is_out_of_scope": False,
    },
    {
        "id": "gt-003",
        "question": "Siapa presiden Jepang?",
        "ground_truth_answer": "(di luar korpus)",
        "source_doc_ids": [],
        "source_type": "web",
        "evidence_text": "",
        "category": "out_of_scope",
        "is_out_of_scope": True,
    },
]

RESULTS = {
    "experiment_code": "E16",
    "chunking_strategy": "structure_aware",
    "retrieval_method": "hybrid_rerank",
    "reranker_enabled": True,
    "items": [
        {
            "id": "gt-001",
            "question": "Apa syarat usia?",
            "answer": "18-30 tahun.",
            "contexts": ["usia 18 sampai 30 tahun"],
            "retrieved": [
                {"chunk_id": "c1", "doc_id": "panduan_pendaftaran", "rank": 1},
                {"chunk_id": "c2", "doc_id": "silabus", "rank": 2},
            ],
            "is_refusal": False,
            "context_tokens": 500,
            "latency_ms": 4000.0,
        },
        {
            "id": "gt-002",
            "question": "Bagaimana alur pendaftaran?",
            "answer": "Lewat halaman /daftar.",
            "contexts": ["pendaftaran melalui halaman /daftar"],
            "retrieved": [{"chunk_id": "c3", "doc_id": "silabus", "rank": 1}],
            "is_refusal": False,
            "context_tokens": 300,
            "latency_ms": 3000.0,
        },
        {
            "id": "gt-003",
            "question": "Siapa presiden Jepang?",
            "answer": "Maaf, informasi mengenai hal tersebut tidak tersedia.",
            "contexts": ["usia 18 sampai 30 tahun"],
            "retrieved": [{"chunk_id": "c1", "doc_id": "panduan_pendaftaran", "rank": 1}],
            "is_refusal": True,
            "context_tokens": 200,
            "latency_ms": 2000.0,
        },
    ],
}


class _StubScorer:
    """Deterministic stand-in for :class:`RagasFaithfulnessScorer`."""

    def __init__(self, value=0.5):
        self.value = value
        self.calls = []
        self.config = SimpleNamespace(model_name="mimo-v2.6-flash:free")

    def score(self, question, answer, contexts):
        self.calls.append((question, answer, tuple(contexts)))
        return FaithfulnessScore(
            score=self.value,
            requested_model=self.config.model_name,
            base_url="https://tokenharbor.ai/v1",
            judge_family="mimo",
            latency_ms=1234.0,
        )


@pytest.fixture
def ground_truth_file(tmp_path):
    path = tmp_path / "ground_truth.json"
    path.write_text(json.dumps(GROUND_TRUTH), encoding="utf-8")
    return path


@pytest.fixture
def results_file(tmp_path):
    path = tmp_path / "E16_results.json"
    path.write_text(json.dumps(RESULTS), encoding="utf-8")
    return path


# ----------------------------------------------------------------------
# loading
# ----------------------------------------------------------------------


def test_load_ground_truth_indexes_by_id(ground_truth_file):
    index = load_ground_truth(ground_truth_file)
    assert set(index) == {"gt-001", "gt-002", "gt-003"}


def test_load_ground_truth_accepts_an_items_envelope(tmp_path):
    path = tmp_path / "gt.json"
    path.write_text(json.dumps({"items": GROUND_TRUTH}), encoding="utf-8")
    assert len(load_ground_truth(path)) == 3


def test_load_ground_truth_reports_missing_file(tmp_path):
    with pytest.raises(EvaluationError, match="ground truth not found"):
        load_ground_truth(tmp_path / "nope.json")


def test_load_ground_truth_reports_invalid_json(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(EvaluationError, match="not valid JSON"):
        load_ground_truth(path)


def test_load_results_reports_missing_and_invalid(tmp_path):
    with pytest.raises(EvaluationError, match="results not found"):
        load_results(tmp_path / "nope.json")
    bad = tmp_path / "bad.json"
    bad.write_text("[]", encoding="utf-8")
    with pytest.raises(EvaluationError, match="must contain a JSON object"):
        load_results(bad)


# ----------------------------------------------------------------------
# evaluation
# ----------------------------------------------------------------------


def test_ir_metrics_are_computed_per_item(ground_truth_file, results_file):
    evaluation = evaluate_experiment(
        "E16", load_results(results_file), load_ground_truth(ground_truth_file), scorer=None
    )

    first = evaluation.items[0]
    assert first["hit_at_5"] == 1.0
    assert first["mrr_at_5"] == 1.0
    assert first["ndcg_at_5"] == 1.0

    second = evaluation.items[1]
    assert second["hit_at_5"] == 0.0
    assert second["retrieved_doc_ids"] == ["silabus"]


def test_out_of_scope_items_skip_ir_metrics(ground_truth_file, results_file):
    evaluation = evaluate_experiment(
        "E16", load_results(results_file), load_ground_truth(ground_truth_file), scorer=None
    )
    third = evaluation.items[2]
    assert third["ir_skipped_reason"] == "no_ground_truth_documents"
    assert "hit_at_5" not in third


def test_faithfulness_is_scored_only_for_in_domain_non_refusal_answers(ground_truth_file, results_file):
    scorer = _StubScorer(value=0.8)
    evaluation = evaluate_experiment(
        "E16", load_results(results_file), load_ground_truth(ground_truth_file), scorer=scorer
    )

    assert len(scorer.calls) == 2
    assert evaluation.items[0]["faithfulness"] == 0.8
    assert evaluation.items[1]["faithfulness"] == 0.8
    assert evaluation.items[2]["faithfulness_skipped_reason"] == "out_of_scope_question"
    assert evaluation.faithfulness_skipped == {"out_of_scope_question": 1}
    assert evaluation.faithful_scored == 2


def test_a_refused_in_domain_answer_is_skipped(ground_truth_file, results_file):
    payload = json.loads(json.dumps(RESULTS))
    payload["items"][0]["is_refusal"] = True

    evaluation = evaluate_experiment(
        "E16", payload, load_ground_truth(ground_truth_file), scorer=_StubScorer()
    )

    assert evaluation.items[0]["faithfulness_skipped_reason"] == "refusal_answer"
    assert evaluation.faithfulness_skipped == {
        "refusal_answer": 1,
        "out_of_scope_question": 1,
    }


def test_judge_disabled_marks_every_in_domain_item(ground_truth_file, results_file):
    evaluation = evaluate_experiment(
        "E16", load_results(results_file), load_ground_truth(ground_truth_file), scorer=None
    )
    assert evaluation.items[0]["faithfulness_skipped_reason"] == "judge_disabled"
    assert evaluation.faithful_scored == 0


def test_missing_context_is_skipped(ground_truth_file, results_file):
    payload = json.loads(json.dumps(RESULTS))
    payload["items"][0]["contexts"] = []
    evaluation = evaluate_experiment(
        "E16", payload, load_ground_truth(ground_truth_file), scorer=_StubScorer()
    )
    assert evaluation.items[0]["faithfulness_skipped_reason"] == "no_retrieved_context"


def test_summary_averages_only_scored_items(ground_truth_file, results_file):
    evaluation = evaluate_experiment(
        "E16", load_results(results_file), load_ground_truth(ground_truth_file), scorer=_StubScorer(0.5)
    )
    summary = evaluation.summary

    assert summary["experiment_code"] == "E16"
    assert summary["chunking_strategy"] == "structure_aware"
    assert summary["retrieval_method"] == "hybrid_rerank"
    assert summary["items_total"] == 3
    assert summary["in_domain_items"] == 2
    assert summary["refusal_answers"] == 1
    assert summary["faithfulness_mean"] == 0.5
    assert summary["faithfulness_scored"] == 2
    assert summary["hit_at_5"] == pytest.approx(0.5)
    assert summary["mrr_at_5"] == pytest.approx(0.5)
    assert summary["ndcg_at_5"] == pytest.approx(0.5)
    assert summary["ir_scored"] == 2


def test_limit_caps_the_number_of_items(ground_truth_file, results_file):
    evaluation = evaluate_experiment(
        "E16", load_results(results_file), load_ground_truth(ground_truth_file),
        scorer=None, limit=1,
    )
    assert evaluation.summary["items_total"] == 1


# ----------------------------------------------------------------------
# caching (resume support)
# ----------------------------------------------------------------------


def test_cache_reuses_scores_for_an_unchanged_answer(ground_truth_file, results_file):
    cache = FaithfulnessCache(path=None)
    scorer = _StubScorer(0.9)

    evaluate_experiment("E16", load_results(results_file), load_ground_truth(ground_truth_file),
                        scorer=scorer, cache=cache)
    assert len(scorer.calls) == 2

    second = evaluate_experiment("E16", load_results(results_file), load_ground_truth(ground_truth_file),
                                 scorer=scorer, cache=cache)
    assert len(scorer.calls) == 2  # nothing new was judged
    assert second.items[0]["faithfulness"] == 0.9
    assert second.items[0]["faithfulness_cached"] is True


def test_cache_is_invalidated_when_the_answer_changes(ground_truth_file, results_file):
    cache = FaithfulnessCache(path=None)
    scorer = _StubScorer(0.9)
    payload = load_results(results_file)

    evaluate_experiment("E16", payload, load_ground_truth(ground_truth_file), scorer=scorer, cache=cache)

    changed = json.loads(json.dumps(payload))
    changed["items"][0]["answer"] = "jawaban yang berbeda"
    evaluate_experiment("E16", changed, load_ground_truth(ground_truth_file), scorer=scorer, cache=cache)

    assert len(scorer.calls) == 3


def test_cache_round_trips_through_disk(tmp_path):
    path = tmp_path / "cache" / "E16.json"
    cache = FaithfulnessCache.load(path)
    cache.put("E16", "gt-001", "abc123", 0.42, "mimo-v2.6-flash:free")
    cache.save()

    reloaded = FaithfulnessCache.load(path)
    assert reloaded.get("E16", "gt-001", "abc123") == 0.42
    assert reloaded.get("E16", "gt-001", "different") is None


def test_cache_tolerates_a_corrupt_file(tmp_path):
    path = tmp_path / "E16.json"
    path.write_text("{broken", encoding="utf-8")
    assert FaithfulnessCache.load(path).entries == {}


# ----------------------------------------------------------------------
# writers
# ----------------------------------------------------------------------


def test_summary_csv_is_written_with_numeric_columns(ground_truth_file, results_file, tmp_path):
    evaluation = evaluate_experiment(
        "E16", load_results(results_file), load_ground_truth(ground_truth_file), scorer=_StubScorer(0.5)
    )
    out = tmp_path / "analysis" / "evaluation_summary.csv"
    write_summary_csv([evaluation.summary], out, k=DEFAULT_K)

    with out.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 1
    row = rows[0]
    assert row["experiment_code"] == "E16"
    for column in ("faithfulness_mean", "hit_at_5", "mrr_at_5", "ndcg_at_5", "context_tokens_mean", "latency_ms_mean"):
        float(row[column])  # raises if the CSV holds a non-numeric value
    assert float(row["hit_at_5"]) == pytest.approx(0.5)
    assert float(row["rejection_accuracy"]) == pytest.approx(1.0)


def test_summary_csv_respects_a_custom_k(ground_truth_file, results_file, tmp_path):
    evaluation = evaluate_experiment(
        "E16", load_results(results_file), load_ground_truth(ground_truth_file), scorer=None, k=5
    )
    out = tmp_path / "summary.csv"
    write_summary_csv([evaluation.summary], out, k=5)
    header = out.read_text(encoding="utf-8").splitlines()[0]
    assert "hit_at_5" in header


def test_details_json_contains_judge_identity(ground_truth_file, results_file, tmp_path):
    evaluation = evaluate_experiment(
        "E16", load_results(results_file), load_ground_truth(ground_truth_file), scorer=_StubScorer(0.5)
    )
    out = tmp_path / "details.json"
    write_details_json([evaluation], out, k=DEFAULT_K)

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["k"] == 5
    assert payload["experiments"][0]["experiment_code"] == "E16"
    assert payload["experiments"][0]["items"][0]["judge_model"] == "mimo-v2.6-flash:free"


# ----------------------------------------------------------------------
# rejection accuracy (Task 4.3)
# ----------------------------------------------------------------------


def test_rejection_accuracy_counts_correct_refusals(ground_truth_file, results_file):
    evaluation = evaluate_experiment(
        "E16", load_results(results_file), load_ground_truth(ground_truth_file), scorer=None
    )
    assert evaluation.summary["out_of_scope_items"] == 1
    assert evaluation.summary["rejection_accuracy"] == 1.0


def test_rejection_accuracy_is_zero_when_out_of_scope_is_answered(
    ground_truth_file, results_file
):
    payload = json.loads(json.dumps(RESULTS))
    payload["items"][2]["is_refusal"] = False
    evaluation = evaluate_experiment(
        "E16", payload, load_ground_truth(ground_truth_file), scorer=None
    )
    assert evaluation.summary["rejection_accuracy"] == 0.0


def test_rejection_accuracy_is_none_without_out_of_scope_items(
    ground_truth_file, results_file
):
    payload = json.loads(json.dumps(RESULTS))
    payload["items"] = payload["items"][:2]
    evaluation = evaluate_experiment(
        "E16", payload, load_ground_truth(ground_truth_file), scorer=None
    )
    assert evaluation.summary["out_of_scope_items"] == 0
    assert evaluation.summary["rejection_accuracy"] is None
