"""Tests for the RAGAS faithfulness scorer (Task 4.2). No network is used."""

import pytest

from rag_service.evaluation import judge as judge_module
from rag_service.evaluation.faithfulness import (
    FaithfulnessError,
    RagasFaithfulnessScorer,
)
from rag_service.evaluation.judge import JudgeConfig, JudgeError


class _FakeMetric:
    """Stand-in for ``ragas.metrics.faithfulness``."""

    def __init__(self, result=0.75, error=None):
        self.result = result
        self.error = error
        self.rows = []

    def score(self, row):
        self.rows.append(row)
        if self.error is not None:
            raise self.error
        return self.result


@pytest.fixture
def isolated_env(monkeypatch):
    monkeypatch.setattr(judge_module, "_env_loaded", True)
    for name in ("JUDGE_MODEL", "JUDGE_BASE_URL", "JUDGE_API_KEY_ENV"):
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


def test_scorer_returns_the_metric_value(isolated_env):
    metric = _FakeMetric(result=2 / 3)
    scorer = RagasFaithfulnessScorer(config=JudgeConfig(), metric=metric)

    result = scorer.score("Apa syarat usia?", "18-30 tahun. Biaya Rp500.000.", ["usia 18 sampai 30 tahun"])

    assert result.score == pytest.approx(2 / 3)
    assert result.requested_model == JudgeConfig().model_name
    assert result.judge_family == "mimo"
    assert result.latency_ms >= 0


def test_scorer_passes_the_ragas_question_answer_contexts_row(isolated_env):
    metric = _FakeMetric()
    scorer = RagasFaithfulnessScorer(config=JudgeConfig(), metric=metric)

    scorer.score("q", "a", ["c1", "c2"])

    assert metric.rows[0] == {"question": "q", "answer": "a", "contexts": ["c1", "c2"]}


def test_blank_contexts_are_dropped(isolated_env):
    metric = _FakeMetric()
    scorer = RagasFaithfulnessScorer(config=JudgeConfig(), metric=metric)

    scorer.score("q", "a", ["c1", "   ", ""])

    assert metric.rows[0]["contexts"] == ["c1"]


def test_empty_contexts_are_rejected(isolated_env):
    scorer = RagasFaithfulnessScorer(config=JudgeConfig(), metric=_FakeMetric())
    with pytest.raises(ValueError, match="contexts must contain"):
        scorer.score("q", "a", [])


def test_empty_question_or_answer_is_rejected(isolated_env):
    scorer = RagasFaithfulnessScorer(config=JudgeConfig(), metric=_FakeMetric())
    with pytest.raises(ValueError, match="question must not be empty"):
        scorer.score("  ", "a", ["c"])
    with pytest.raises(ValueError, match="answer must not be empty"):
        scorer.score("q", "  ", ["c"])


def test_metric_failure_is_wrapped(isolated_env):
    scorer = RagasFaithfulnessScorer(config=JudgeConfig(), metric=_FakeMetric(error=RuntimeError("gateway 502")))
    with pytest.raises(FaithfulnessError, match="faithfulness scoring failed"):
        scorer.score("q", "a", ["c"])


def test_non_numeric_metric_value_is_rejected(isolated_env):
    scorer = RagasFaithfulnessScorer(config=JudgeConfig(), metric=_FakeMetric(result="bukan angka"))
    with pytest.raises(FaithfulnessError, match="non-numeric"):
        scorer.score("q", "a", ["c"])


def test_same_family_judge_is_refused(isolated_env):
    with pytest.raises(JudgeError, match="same family as the generator"):
        RagasFaithfulnessScorer(
            config=JudgeConfig(model_name="deepseek-v4.1-flash:free"),
            metric=_FakeMetric(),
        )


def test_snapshot_metadata_records_the_dynamic_endpoint(isolated_env):
    scorer = RagasFaithfulnessScorer(
        config=JudgeConfig(model_name="gemini-3.8-flash", base_url="https://example.test/v1"),
        metric=_FakeMetric(),
    )
    snapshot = scorer.snapshot_metadata()

    assert snapshot["framework"] == "ragas==0.1.21"
    assert snapshot["base_url"] == "https://example.test/v1"
    assert snapshot["requested_model"] == "gemini-3.8-flash"
    assert snapshot["independent_family"] is True


def test_missing_api_key_is_reported_clearly(isolated_env):
    isolated_env.delenv("MISSING_JUDGE_KEY", raising=False)
    scorer = RagasFaithfulnessScorer(
        config=JudgeConfig(api_key_env="MISSING_JUDGE_KEY"),
    )
    with pytest.raises(FaithfulnessError, match="MISSING_JUDGE_KEY is not set"):
        scorer.score("q", "a", ["c"])
