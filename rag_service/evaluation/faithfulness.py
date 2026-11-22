"""RAGAS faithfulness scorer wired to the dynamic judge endpoint (Task 4.2).

Faithfulness is RAGAS 0.1.21's definition: the answer is decomposed into atomic
claims and each claim is checked against the retrieved context; the score is the
share of supported claims.

The metric is run through :class:`~rag_service.evaluation.JudgeConfig`, so the
judge model and endpoint stay configuration (``JUDGE_MODEL``, ``JUDGE_BASE_URL``,
``JUDGE_API_KEY_ENV``) rather than code (ADR 0002). ``assert_independent_judge``
still guarantees the judge is not the generator's family.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

from rag_service.evaluation.judge import (
    JudgeConfig,
    assert_independent_judge,
    model_family,
)

logger = logging.getLogger(__name__)


class FaithfulnessError(RuntimeError):
    """Raised when the faithfulness metric cannot be built or executed."""


@dataclass(frozen=True)
class FaithfulnessScore:
    """One faithfulness value plus the judge identity that produced it."""

    score: float
    requested_model: str
    base_url: str
    judge_family: str
    latency_ms: float
    claims_scored: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-serializable dictionary."""
        return {
            "faithfulness": self.score,
            "judge_model": self.requested_model,
            "judge_base_url": self.base_url,
            "judge_family": self.judge_family,
            "judge_latency_ms": self.latency_ms,
        }


class RagasFaithfulnessScorer:
    """Compute RAGAS faithfulness using the configured judge model."""

    def __init__(self, config: Optional[JudgeConfig] = None, metric: Optional[Any] = None):
        self.config = config or JudgeConfig.from_env()
        self.judge_family = assert_independent_judge(
            self.config.model_name,
            self.config.generator_model,
            allow_same_family=self.config.allow_same_family,
        )
        self._metric = metric

    # ------------------------------------------------------------------
    # construction
    # ------------------------------------------------------------------

    def _build_metric(self) -> Any:
        if self._metric is not None:
            return self._metric

        try:
            from langchain_openai import ChatOpenAI
            from ragas.llms import LangchainLLMWrapper
            from ragas.metrics import faithfulness
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise FaithfulnessError(
                "ragas / langchain-openai are not installed; install "
                "rag_service/requirements.txt"
            ) from exc

        from rag_service.evaluation.judge import _load_env_files_once

        _load_env_files_once()
        api_key = os.getenv(self.config.api_key_env)
        if not api_key:
            raise FaithfulnessError(
                f"{self.config.api_key_env} is not set; the judge needs it to score "
                f"faithfulness."
            )

        llm = LangchainLLMWrapper(
            ChatOpenAI(
                model=self.config.model_name,
                base_url=self.config.base_url,
                api_key=api_key,
                temperature=self.config.temperature,
                max_tokens=self.config.max_output_tokens,
                timeout=self.config.timeout_seconds,
            )
        )

        # NOTE: `ragas.metrics.faithfulness` is a module-level singleton, so this
        # wires the process-wide judge. One judge per run is required anyway.
        faithfulness.llm = llm
        self._metric = faithfulness
        return self._metric

    def snapshot_metadata(self) -> Dict[str, Any]:
        """Describe the judge identity used for faithfulness."""
        return {
            "metric": "ragas.faithfulness",
            "framework": "ragas==0.1.21",
            "requested_model": self.config.model_name,
            "base_url": self.config.base_url,
            "judge_family": self.judge_family,
            "generator_family": model_family(self.config.generator_model),
            "independent_family": self.judge_family
            != model_family(self.config.generator_model),
            "temperature": self.config.temperature,
            "evaluation_mode": "question-answer-context",
        }

    # ------------------------------------------------------------------
    # scoring
    # ------------------------------------------------------------------

    def score(
        self,
        question: str,
        answer: str,
        contexts: Sequence[str],
    ) -> FaithfulnessScore:
        """Faithfulness of ``answer`` against ``contexts`` for ``question``."""
        if not question or not question.strip():
            raise ValueError("question must not be empty")
        if not answer or not answer.strip():
            raise ValueError("answer must not be empty")

        usable_contexts: List[str] = [c for c in (contexts or []) if c and c.strip()]
        if not usable_contexts:
            raise ValueError("contexts must contain at least one non-empty passage")

        metric = self._build_metric()
        row = {
            "question": question,
            "answer": answer,
            "contexts": usable_contexts,
        }

        started = time.perf_counter()
        try:
            value = metric.score(row)
        except Exception as exc:  # noqa: BLE001 - judge/gateway boundary
            raise FaithfulnessError(
                f"faithfulness scoring failed: {type(exc).__name__}: {exc}"
            ) from exc
        latency_ms = (time.perf_counter() - started) * 1000.0

        try:
            score_value = float(value)
        except (TypeError, ValueError) as exc:
            raise FaithfulnessError(
                f"faithfulness returned a non-numeric value: {value!r}"
            ) from exc

        return FaithfulnessScore(
            score=score_value,
            requested_model=self.config.model_name,
            base_url=self.config.base_url,
            judge_family=self.judge_family,
            latency_ms=latency_ms,
        )
