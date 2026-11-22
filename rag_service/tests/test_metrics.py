"""Tests for the IR metrics (Task 4.2)."""

import pytest

from rag_service.evaluation.metrics import (
    document_id,
    hit_at_k,
    ir_metrics,
    ndcg_at_k,
    ranked_document_ids,
    reciprocal_rank_at_k,
    relevant_documents,
)


class _Chunk:
    def __init__(self, doc_id):
        self.doc_id = doc_id


def test_document_id_reads_dicts_strings_and_objects():
    assert document_id({"doc_id": "a"}) == "a"
    assert document_id({"document_id": "b"}) == "b"
    assert document_id("c") == "c"
    assert document_id(_Chunk("d")) == "d"
    assert document_id(None) == ""
    assert document_id({}) == ""


def test_ranked_document_ids_deduplicates_keeping_the_best_rank():
    retrieved = [
        {"doc_id": "a", "rank": 1},
        {"doc_id": "b", "rank": 2},
        {"doc_id": "a", "rank": 3},
        {"doc_id": "c", "rank": 4},
    ]
    assert ranked_document_ids(retrieved) == ["a", "b", "c"]


def test_ranked_document_ids_sorts_by_rank_field():
    retrieved = [
        {"doc_id": "b", "rank": 2},
        {"doc_id": "a", "rank": 1},
    ]
    assert ranked_document_ids(retrieved) == ["a", "b"]


def test_ranked_document_ids_honours_k():
    retrieved = [{"doc_id": f"d{i}", "rank": i} for i in range(1, 6)]
    assert ranked_document_ids(retrieved, 2) == ["d1", "d2"]


def test_relevant_documents_handles_missing_and_scalar_values():
    assert relevant_documents({"source_doc_ids": ["a", "b"]}) == ["a", "b"]
    assert relevant_documents({"doc_ids": "solo"}) == ["solo"]
    assert relevant_documents({}) == []


def test_hit_at_k_finds_a_relevant_document_inside_the_cutoff():
    retrieved = [{"doc_id": "x", "rank": 1}, {"doc_id": "a", "rank": 2}]
    assert hit_at_k(retrieved, ["a"], 5) == 1.0
    assert hit_at_k(retrieved, ["a"], 1) == 0.0


def test_hit_at_k_is_zero_without_ground_truth_documents():
    assert hit_at_k([{"doc_id": "x", "rank": 1}], [], 5) == 0.0


def test_reciprocal_rank_uses_the_first_relevant_document():
    retrieved = [
        {"doc_id": "x", "rank": 1},
        {"doc_id": "y", "rank": 2},
        {"doc_id": "a", "rank": 3},
    ]
    assert reciprocal_rank_at_k(retrieved, ["a"], 5) == pytest.approx(1 / 3)
    assert reciprocal_rank_at_k(retrieved, ["a"], 2) == 0.0


def test_ndcg_is_one_for_a_perfect_ranking():
    retrieved = [{"doc_id": "a", "rank": 1}, {"doc_id": "b", "rank": 2}]
    assert ndcg_at_k(retrieved, ["a", "b"], 5) == pytest.approx(1.0)


def test_ndcg_discounts_a_relevant_document_found_late():
    retrieved = [{"doc_id": "x", "rank": 1}, {"doc_id": "a", "rank": 2}]
    assert ndcg_at_k(retrieved, ["a"], 5) == pytest.approx(0.6309297, rel=1e-6)


def test_ndcg_with_two_relevant_documents():
    retrieved = [
        {"doc_id": "c", "rank": 1},
        {"doc_id": "a", "rank": 2},
        {"doc_id": "b", "rank": 3},
    ]
    assert ndcg_at_k(retrieved, ["a", "b"], 5) == pytest.approx(0.6934264, rel=1e-6)


def test_ndcg_is_zero_when_nothing_relevant_is_retrieved():
    retrieved = [{"doc_id": "x", "rank": 1}]
    assert ndcg_at_k(retrieved, ["a"], 5) == 0.0
    assert ndcg_at_k(retrieved, [], 5) == 0.0


def test_ir_metrics_reports_all_three_metrics_with_the_cutoff_in_the_name():
    retrieved = [{"doc_id": "a", "rank": 1}]
    result = ir_metrics(retrieved, ["a"], k=3)
    assert set(result) == {"hit_at_3", "mrr_at_3", "ndcg_at_3"}
    assert all(value == 1.0 for value in result.values())
