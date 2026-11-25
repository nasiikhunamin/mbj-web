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
import math
import os
import re
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


#: Bracketed source labels the generator appends ("[Sumber: ...]") are not claims.
_SOURCE_LABEL = re.compile(r"^\[?\s*sumber\s*:", re.IGNORECASE)
_TERMINAL_PUNCTUATION = (".", "!", "?", ":", ";")

_METRIC_CLASS: Optional[type] = None


def prompt_sentences(segments: Sequence[str], *, drop_sources: bool = True) -> List[str]:
    """Turn answer segments into the numbered sentence list RAGAS asks about.

    RAGAS 0.1.21 keeps only sentences whose stripped text ends with ``.``. Most
    Indonesian answers are numbered/bulleted lists without a closing period per
    line, so every sentence is dropped, the judge is asked to break down an
    empty list, and the score silently becomes ``NaN``. Keeping all non-empty
    segments (with a closing period added when missing) avoids that.
    """
    sentences: List[str] = []
    for raw in segments:
        text = " ".join(str(raw).split())
        if not text:
            continue
        if drop_sources and _SOURCE_LABEL.match(text):
            continue
        if not text.endswith(_TERMINAL_PUNCTUATION):
            text += "."
        sentences.append(text)
    return sentences


def _metric_class() -> type:
    """Build the RAGAS metric subclass once, on first use (ragas is optional)."""
    global _METRIC_CLASS
    if _METRIC_CLASS is not None:
        return _METRIC_CLASS

    from ragas.metrics import Faithfulness

    class BulletTolerantFaithfulness(Faithfulness):
        """RAGAS faithfulness that also reads bulleted/numbered answers."""

        def _create_statements_prompt(self, row: Dict[str, Any]) -> Any:
            answer = row["answer"]
            segments = self.sentence_segmenter.segment(answer)
            sentences = prompt_sentences(segments)
            if not sentences:  # answer is only a source label or whitespace
                sentences = prompt_sentences([answer], drop_sources=False)
            numbered = "\n".join(
                f"{index}:{sentence}" for index, sentence in enumerate(sentences)
            )
            return self.statement_prompt.format(
                question=row["question"], answer=answer, sentences=numbered
            )

    _METRIC_CLASS = BulletTolerantFaithfulness
    return _METRIC_CLASS


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
            from ragas.metrics import Faithfulness
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
                f"faithfulness. JUDGE_API_KEY_ENV must hold the *name* of the variable "
                f"that contains the key (for example TOKENHARBOR_API_KEY), and that "
                f"variable must be set in .env."
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

        # Our own metric instance (RAGAS ships a module-level singleton) so the
        # bulleted-answer fix stays local to this process.
        # Two retries because free reasoning routes occasionally spend the whole
        # token budget on reasoning and return an empty completion.
        faithfulness = _metric_class()()
        faithfulness.max_retries = 2
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
            hint = ""
            if "timeout" in f"{type(exc).__name__} {exc}".lower():
                hint = (
                    f" The judge did not answer within "
                    f"{self.config.timeout_seconds:.0f}s; slow `:free` routes may need a"
                    f" larger JUDGE_TIMEOUT_SECONDS."
                )
            raise FaithfulnessError(
                f"faithfulness scoring failed: {type(exc).__name__}: {exc}{hint}"
            ) from exc
        latency_ms = (time.perf_counter() - started) * 1000.0

        try:
            score_value = float(value)
        except (TypeError, ValueError) as exc:
            raise FaithfulnessError(
                f"faithfulness returned a non-numeric value: {value!r}"
            ) from exc

        if math.isnan(score_value):
            logger.warning(
                "judge %s produced an empty or unparsable completion, so "
                "faithfulness is NaN for this item; raise JUDGE_MAX_OUTPUT_TOKENS "
                "if this repeats.",
                self.config.model_name,
            )

        return FaithfulnessScore(
            score=score_value,
            requested_model=self.config.model_name,
            base_url=self.config.base_url,
            judge_family=self.judge_family,
            latency_ms=latency_ms,
        )
