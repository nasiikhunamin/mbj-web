"""Multilingual cross-encoder reranker (Task 2.11).

Primary backend: ``BAAI/bge-reranker-v2-m3`` loaded through sentence-transformers
``CrossEncoder``. When torch/model weights are unavailable, a deterministic
lexical scorer keeps the module usable for offline tests. The public contract is
identical: query + candidates in, reranked Top-N out.
"""

import math
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from rag_service.retrievers.base import RetrievedChunk

try:
    from sentence_transformers import CrossEncoder  # type: ignore

    HAS_CROSS_ENCODER = True
except Exception:  # torch missing, broken install, offline import failure
    CrossEncoder = None  # type: ignore
    HAS_CROSS_ENCODER = False


Candidate = Union[RetrievedChunk, Dict[str, Any]]

_CROSS_ENCODER_CACHE: Dict[Tuple[str, str, int], Any] = {}


def _word_tokens(text: str) -> List[str]:
    """Lowercase word tokens used by the offline lexical scorer."""
    return re.findall(r"\w+", (text or "").lower(), flags=re.UNICODE)


def _char_trigrams(text: str) -> set:
    """Character trigrams for cheap subword matching."""
    lowered = (text or "").lower()
    grams = set()
    for token in re.findall(r"\w+", lowered, flags=re.UNICODE):
        if len(token) < 3:
            continue
        padded = f"#{token}#"
        grams.update(padded[index : index + 3] for index in range(len(padded) - 2))
    return grams


class BGEReranker:
    """Rerank retrieval candidates with a multilingual cross-encoder."""

    DEFAULT_MODEL_NAME = "BAAI/bge-reranker-v2-m3"

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        top_n: int = 5,
        max_length: int = 512,
        batch_size: int = 16,
        device: Optional[str] = None,
        allow_fallback: bool = True,
    ):
        if top_n <= 0:
            raise ValueError(f"top_n must be positive, got {top_n}")
        if max_length <= 0:
            raise ValueError(f"max_length must be positive, got {max_length}")
        if batch_size <= 0:
            raise ValueError(f"batch_size must be positive, got {batch_size}")

        self.model_name = model_name
        self.top_n = top_n
        self.max_length = max_length
        self.batch_size = batch_size
        self.device = device
        self.allow_fallback = allow_fallback

        self._model = None
        self._load_attempted = False

    @property
    def backend(self) -> str:
        """Return the active reranker backend name."""
        self._ensure_model()
        return "cross-encoder" if self._model is not None else "lexical-fallback"

    def _ensure_model(self) -> None:
        """Load the cross-encoder once, if the runtime supports it."""
        if self._load_attempted:
            return
        self._load_attempted = True

        if not HAS_CROSS_ENCODER:
            if not self.allow_fallback:
                raise RuntimeError(
                    "sentence-transformers/torch is not installed; set "
                    "allow_fallback=True to use the lexical scorer"
                )
            return

        try:
            kwargs: Dict[str, Any] = {"max_length": self.max_length}
            if self.device:
                kwargs["device"] = self.device
            cache_key = (self.model_name, self.device or "", self.max_length)
            cached_model = _CROSS_ENCODER_CACHE.get(cache_key)
            if cached_model is not None:
                self._model = cached_model
                return
            self._model = CrossEncoder(self.model_name, **kwargs)
            _CROSS_ENCODER_CACHE[cache_key] = self._model
        except Exception as exc:
            self._model = None
            if not self.allow_fallback:
                raise RuntimeError(
                    f"failed to load reranker {self.model_name}: {exc}"
                ) from exc

    @staticmethod
    def _normalize_candidate(candidate: Candidate) -> RetrievedChunk:
        """Accept a RetrievedChunk or a plain store record."""
        if isinstance(candidate, RetrievedChunk):
            return candidate
        if isinstance(candidate, dict):
            return RetrievedChunk.from_record(candidate)
        raise TypeError(f"unsupported candidate type: {type(candidate)!r}")

    def _predict(self, query: str, candidates: Sequence[RetrievedChunk]) -> List[float]:
        """Score query-candidate relevance with the active backend."""
        if self._model is not None:
            pairs = [[query, candidate.content] for candidate in candidates]
            raw_scores = self._model.predict(
                pairs,
                batch_size=self.batch_size,
                show_progress_bar=False,
            )
            scores: List[float] = []
            for raw in raw_scores:
                if isinstance(raw, (list, tuple)):
                    raw = raw[0]
                scores.append(float(raw))
            return scores

        return [
            self._lexical_score(query, candidate.content) for candidate in candidates
        ]

    @staticmethod
    def _lexical_score(query: str, passage: str) -> float:
        """Deterministic lexical relevance used when the model is unavailable."""
        query_words = set(_word_tokens(query))
        passage_words = set(_word_tokens(passage))
        if not query_words:
            return 0.0

        word_overlap = len(query_words & passage_words) / len(query_words)

        query_grams = _char_trigrams(query)
        passage_grams = _char_trigrams(passage)
        if query_grams or passage_grams:
            trigram_overlap = (
                2.0
                * len(query_grams & passage_grams)
                / (len(query_grams) + len(passage_grams))
            )
        else:
            trigram_overlap = 0.0

        return 0.7 * word_overlap + 0.3 * trigram_overlap

    def rerank(
        self,
        query: str,
        candidates: Sequence[Candidate],
        top_n: Optional[int] = None,
    ) -> List[RetrievedChunk]:
        """Rerank candidates and return the Top-N with cross-encoder scores."""
        if not query or not query.strip() or not candidates:
            return []

        limit = self.top_n if top_n is None else top_n
        if limit <= 0:
            raise ValueError(f"top_n must be positive, got {limit}")

        normalized = [self._normalize_candidate(candidate) for candidate in candidates]
        self._ensure_model()
        scores = self._predict(query, normalized)
        backend = "cross-encoder" if self._model is not None else "lexical-fallback"

        ranked = sorted(
            zip(normalized, scores),
            key=lambda pair: (
                -pair[1] if math.isfinite(pair[1]) else math.inf,
                pair[0].chunk_id,
            ),
        )

        results: List[RetrievedChunk] = []
        for rank, (candidate, score) in enumerate(ranked[:limit], start=1):
            metadata = {
                **candidate.metadata,
                "rerank_score": score,
                "pre_rerank_rank": candidate.rank,
                "rerank_backend": backend,
                "rerank_model": self.model_name,
            }
            results.append(
                RetrievedChunk(
                    chunk_id=candidate.chunk_id,
                    content=candidate.content,
                    score=score,
                    doc_id=candidate.doc_id,
                    source_type=candidate.source_type,
                    source_title=candidate.source_title,
                    token_count=candidate.token_count,
                    metadata=metadata,
                    rank=rank,
                )
            )
        return results
