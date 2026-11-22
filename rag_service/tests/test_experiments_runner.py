"""Tests for the batch experiment runner (Task 4.1)."""

import json
from types import SimpleNamespace

import pytest

from rag_service.experiments.runner import (
    RunnerError,
    build_record,
    load_questions,
    run_all,
    run_experiment,
)


QUESTIONS = [
    {
        "id": "gt-001",
        "question": "Apa syarat usia?",
        "category": "factual",
        "source_type": "pdf",
        "is_out_of_scope": False,
    },
    {
        "id": "gt-002",
        "question": "Bagaimana alur pendaftaran?",
        "category": "procedural",
        "source_type": "pdf",
        "is_out_of_scope": False,
    },
    {
        "id": "gt-003",
        "question": "Siapa presiden Jepang?",
        "category": "out_of_scope",
        "source_type": "web",
        "is_out_of_scope": True,
    },
]


class FakePipeline:
    """Minimal stand-in for ``RAGPipeline`` returning a plain dict payload."""

    def __init__(self, code="E16"):
        self.config = SimpleNamespace(
            code=code,
            chunking_strategy="structure_aware",
            retrieval_method="hybrid_rerank",
            reranker_enabled=True,
        )
        self.calls = []

    def ask(self, question):
        self.calls.append(question)
        return {
            "question": question,
            "answer": f"jawaban: {question}",
            "chunks": [
                {
                    "chunk_id": "c1",
                    "doc_id": "doc_a",
                    "content": "isi konteks satu",
                    "rank": 1,
                },
                {
                    "chunk_id": "c2",
                    "doc_id": "doc_b",
                    "content": "",
                    "rank": 2,
                },
            ],
            "sources": ["doc_a"],
            "retrieved_sources": ["doc_a", "doc_b"],
            "is_refusal": False,
            "context_tokens": 42,
            "latency_ms": 12.5,
        }


def write_ground_truth(path, code="utf-8"):
    path.write_text(json.dumps(QUESTIONS), encoding=code)


def test_load_questions_accepts_bare_list(tmp_path):
    path = tmp_path / "gt.json"
    write_ground_truth(path)
    assert [q["id"] for q in load_questions(path)] == ["gt-001", "gt-002", "gt-003"]


def test_load_questions_accepts_items_wrapper(tmp_path):
    path = tmp_path / "gt.json"
    path.write_text(json.dumps({"items": QUESTIONS}), encoding="utf-8")
    assert len(load_questions(path)) == 3


def test_load_questions_rejects_missing_file(tmp_path):
    with pytest.raises(RunnerError):
        load_questions(tmp_path / "nope.json")


def test_load_questions_rejects_items_without_id(tmp_path):
    path = tmp_path / "gt.json"
    path.write_text(json.dumps([{"question": "x"}]), encoding="utf-8")
    with pytest.raises(RunnerError):
        load_questions(path)


def test_build_record_maps_contexts_and_retrieved():
    record = build_record(QUESTIONS[0], FakePipeline().ask("Apa syarat usia?"))
    assert record["id"] == "gt-001"
    assert record["category"] == "factual"
    assert record["source_type"] == "pdf"
    assert record["contexts"] == ["isi konteks satu"]
    assert record["retrieved"] == [
        {"chunk_id": "c1", "doc_id": "doc_a", "rank": 1},
        {"chunk_id": "c2", "doc_id": "doc_b", "rank": 2},
    ]


def test_run_experiment_writes_contract(tmp_path):
    pipeline = FakePipeline()
    path = tmp_path / "E16_results.json"
    payload = run_experiment("E16", QUESTIONS, pipeline, path)

    written = json.loads(path.read_text(encoding="utf-8"))
    assert written["experiment_code"] == "E16"
    assert written["chunking_strategy"] == "structure_aware"
    assert written["retrieval_method"] == "hybrid_rerank"
    assert written["reranker_enabled"] is True
    assert len(written["items"]) == 3
    assert len(pipeline.calls) == 3
    assert payload["generated_at"]


def test_run_experiment_resumes_from_completed_items(tmp_path):
    path = tmp_path / "E16_results.json"
    path.write_text(
        json.dumps({"experiment_code": "E16", "items": [{"id": "gt-001", "answer": "lama"}]}),
        encoding="utf-8",
    )
    pipeline = FakePipeline()
    payload = run_experiment("E16", QUESTIONS, pipeline, path)

    assert [item["id"] for item in payload["items"]] == ["gt-001", "gt-002", "gt-003"]
    assert payload["items"][0]["answer"] == "lama"
    assert pipeline.calls == [QUESTIONS[1]["question"], QUESTIONS[2]["question"]]


def test_run_experiment_no_resume_reruns_everything(tmp_path):
    path = tmp_path / "E16_results.json"
    path.write_text(
        json.dumps({"experiment_code": "E16", "items": [{"id": "gt-001", "answer": "lama"}]}),
        encoding="utf-8",
    )
    pipeline = FakePipeline()
    run_experiment("E16", QUESTIONS, pipeline, path, resume=False)
    assert len(pipeline.calls) == 3


def test_run_experiment_limit(tmp_path):
    pipeline = FakePipeline()
    payload = run_experiment(
        "E16", QUESTIONS, pipeline, tmp_path / "E16_results.json", limit=1
    )
    assert [item["id"] for item in payload["items"]] == ["gt-001"]
    assert len(pipeline.calls) == 1


def test_run_experiment_progress_callback(tmp_path):
    seen = []
    run_experiment(
        "E16",
        QUESTIONS,
        FakePipeline(),
        tmp_path / "E16_results.json",
        on_progress=lambda code, record, done, total: seen.append((code, done, total)),
    )
    assert seen == [("E16", 1, 3), ("E16", 2, 3), ("E16", 3, 3)]


def test_run_all_runs_each_code(tmp_path):
    factory = FakePipeline
    payloads = run_all(["E01", "E02"], QUESTIONS, tmp_path, factory)
    assert [p["experiment_code"] for p in payloads] == ["E01", "E02"]
    assert (tmp_path / "E01_results.json").exists()
    assert (tmp_path / "E02_results.json").exists()
