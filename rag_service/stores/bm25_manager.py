"""Sparse BM25 storage with PySastrawi preprocessing.

Task 2.7 keeps exactly four persistent BM25 indices, one per chunking strategy.
Each index stores the tokenized corpus plus chunk metadata so it can be reloaded
without re-chunking. ``rank_bm25`` is used when available; a pure-Python BM25
implementation with the same parameters (k1=1.5, b=0.75) is used otherwise.
"""

import json
import math
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

from rag_service.chunkers.base import Chunk

try:
    from rank_bm25 import BM25Okapi  # type: ignore

    HAS_RANK_BM25 = True
except ImportError:
    BM25Okapi = None  # type: ignore
    HAS_RANK_BM25 = False

try:
    from Sastrawi.Stemmer.StemmerFactory import StemmerFactory  # type: ignore
    from Sastrawi.StopWordRemover.StopWordRemoverFactory import (  # type: ignore
        StopWordRemoverFactory,
    )

    HAS_SASTRAWI = True
except ImportError:
    StemmerFactory = None  # type: ignore
    StopWordRemoverFactory = None  # type: ignore
    HAS_SASTRAWI = False


STRATEGIES = ("fixed", "recursive", "semantic", "structure_aware")
INDEX_PREFIX = "bm25_"

Record = Dict[str, Any]

_SASTRAWI_STEMMER = None
_SASTRAWI_STOPWORDS: Optional[set] = None


def _get_stemmer():
    """Return a process-wide PySastrawi stemmer, if installed."""
    global _SASTRAWI_STEMMER
    if not HAS_SASTRAWI:
        return None
    if _SASTRAWI_STEMMER is None:
        _SASTRAWI_STEMMER = StemmerFactory().create_stemmer()
    return _SASTRAWI_STEMMER


def _get_stopwords() -> set:
    """Return a process-wide Indonesian stopword set."""
    global _SASTRAWI_STOPWORDS
    if _SASTRAWI_STOPWORDS is None:
        if HAS_SASTRAWI:
            _SASTRAWI_STOPWORDS = set(StopWordRemoverFactory().get_stop_words())
        else:
            _SASTRAWI_STOPWORDS = {
                "adalah",
                "agar",
                "akan",
                "atau",
                "bagi",
                "bahwa",
                "dan",
                "dari",
                "dengan",
                "di",
                "ini",
                "itu",
                "jika",
                "juga",
                "ke",
                "kepada",
                "kita",
                "oleh",
                "pada",
                "para",
                "sebagai",
                "sedang",
                "serta",
                "telah",
                "terhadap",
                "untuk",
                "yang",
            }
    return _SASTRAWI_STOPWORDS


class _PurePythonBM25:
    """Minimal BM25Okapi-compatible scorer used when rank_bm25 is absent."""

    def __init__(self, tokenized_corpus: Sequence[Sequence[str]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus = [list(tokens) for tokens in tokenized_corpus]
        self.doc_len = [len(tokens) for tokens in self.corpus]
        self.doc_freqs: List[Dict[str, int]] = []
        self.idf: Dict[str, float] = {}

        document_frequency: Dict[str, int] = {}
        for tokens in self.corpus:
            frequencies: Dict[str, int] = {}
            for token in tokens:
                frequencies[token] = frequencies.get(token, 0) + 1
            self.doc_freqs.append(frequencies)
            for token in frequencies:
                document_frequency[token] = document_frequency.get(token, 0) + 1

        total_docs = len(self.corpus)
        for token, freq in document_frequency.items():
            self.idf[token] = math.log(total_docs - freq + 0.5) - math.log(freq + 0.5)

        self.avgdl = (sum(self.doc_len) / total_docs) if total_docs else 0.0

    def get_scores(self, query_tokens: Sequence[str]) -> List[float]:
        scores: List[float] = []
        for index, frequencies in enumerate(self.doc_freqs):
            score = 0.0
            length_norm = self.k1 * (
                1.0 - self.b + self.b * (self.doc_len[index] / self.avgdl if self.avgdl else 0.0)
            )
            for token in query_tokens:
                if token not in frequencies:
                    continue
                frequency = frequencies[token]
                score += self.idf.get(token, 0.0) * (
                    (frequency * (self.k1 + 1.0)) / (frequency + length_norm)
                )
            scores.append(score)
        return scores


def _chunk_to_dict(chunk: Union[Chunk, Record]) -> Record:
    """Normalize a Chunk object or dictionary into a plain record."""
    if isinstance(chunk, Chunk):
        return chunk.to_dict()
    if isinstance(chunk, dict):
        return dict(chunk)
    raise TypeError(f"unsupported chunk type: {type(chunk)!r}")


class BM25Manager:
    """Build, persist, and query the four sparse BM25 indices."""

    def __init__(
        self,
        persist_directory: Union[str, Path] = "data/vectordb/bm25",
        strategies: Iterable[str] = STRATEGIES,
        k1: float = 1.5,
        b: float = 0.75,
        use_stemming: bool = True,
        use_stopwords: bool = True,
    ):
        if k1 <= 0:
            raise ValueError(f"k1 must be positive, got {k1}")
        if not 0.0 <= b <= 1.0:
            raise ValueError(f"b must be within [0, 1], got {b}")

        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.strategies = tuple(strategies)
        self.k1 = k1
        self.b = b
        self.use_stemming = use_stemming
        self.use_stopwords = use_stopwords

        self._bm25: Dict[str, Any] = {}
        self._payloads: Dict[str, Dict[str, Any]] = {}
        self._stemmer = _get_stemmer() if use_stemming else None
        self._stopwords = _get_stopwords() if use_stopwords else set()

        self.backend = "rank_bm25" if HAS_RANK_BM25 else "pure_python_fallback"

    def index_path(self, strategy: str) -> Path:
        """Return the persistence path for a strategy index."""
        if strategy not in self.strategies:
            raise ValueError(
                f"unknown strategy {strategy!r}; expected one of {self.strategies}"
            )
        return self.persist_directory / f"{INDEX_PREFIX}{strategy}.json"

    def tokenize(self, text: str) -> List[str]:
        """Lowercase, remove Indonesian stopwords, and stem tokens."""
        tokens = re.findall(r"\w+", (text or "").lower(), flags=re.UNICODE)
        if self.use_stopwords:
            tokens = [token for token in tokens if token not in self._stopwords]
        if self.use_stemming and self._stemmer is not None:
            tokens = [self._stemmer.stem(token) for token in tokens]
        return [token for token in tokens if token]

    def build(self, strategy: str, chunks: Sequence[Union[Chunk, Record]]) -> int:
        """Tokenize and persist an index for one chunking strategy."""
        path = self.index_path(strategy)

        records: List[Record] = []
        tokenized: List[List[str]] = []
        for chunk in chunks:
            record = _chunk_to_dict(chunk)
            tokens = self.tokenize(record.get("content", ""))
            if not tokens:
                continue
            records.append(record)
            tokenized.append(tokens)

        payload = {
            "strategy": strategy,
            "k1": self.k1,
            "b": self.b,
            "stemming": self.use_stemming,
            "stopwords": self.use_stopwords,
            "chunks": records,
            "tokenized": tokenized,
        }
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False)

        self._payloads[strategy] = payload
        self._bm25[strategy] = self._instantiate(tokenized)
        return len(records)

    def _instantiate(self, tokenized: List[List[str]]) -> Any:
        """Create a BM25 scorer from tokenized documents."""
        if HAS_RANK_BM25:
            return BM25Okapi(tokenized, k1=self.k1, b=self.b)
        return _PurePythonBM25(tokenized, k1=self.k1, b=self.b)

    def _load(self, strategy: str) -> Optional[Dict[str, Any]]:
        """Lazily load a persisted index payload."""
        if strategy in self._payloads:
            return self._payloads[strategy]

        path = self.index_path(strategy)
        if not path.exists():
            return None

        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        self._payloads[strategy] = payload
        self._bm25[strategy] = self._instantiate(payload.get("tokenized", []))
        return payload

    def search(self, strategy: str, query: str, top_k: int = 5) -> List[Record]:
        """Return the top-k positive BM25 scoring chunks for a query."""
        if top_k <= 0:
            raise ValueError(f"top_k must be positive, got {top_k}")
        payload = self._load(strategy)
        if not payload:
            return []

        query_tokens = self.tokenize(query)
        if not query_tokens:
            return []

        scores = self._bm25[strategy].get_scores(query_tokens)
        query_terms = set(query_tokens)
        ranked: List[Tuple[float, Record]] = []
        for score, record, document_tokens in zip(
            scores,
            payload.get("chunks", []),
            payload.get("tokenized", []),
        ):
            score = float(score)
            # A term can be present while its IDF is zero in a tiny corpus.
            # Keep lexical matches so recall does not collapse on small indices.
            is_match = any(term in document_tokens for term in query_terms)
            if math.isfinite(score) and (score > 0.0 or is_match):
                ranked.append((score, record))

        ranked.sort(key=lambda pair: (-pair[0], pair[1].get("chunk_id", "")))
        results: List[Record] = []
        for score, record in ranked[:top_k]:
            results.append(
                {
                    "chunk_id": record.get("chunk_id", ""),
                    "content": record.get("content", ""),
                    "doc_id": record.get("doc_id", ""),
                    "source_type": record.get("source_type", ""),
                    "source_title": record.get("source_title", ""),
                    "token_count": int(record.get("token_count", 0) or 0),
                    "metadata": record.get("metadata", {}),
                    "score": score,
                }
            )
        return results

    def count(self, strategy: str) -> int:
        """Return the number of indexed chunks for a strategy."""
        payload = self._load(strategy)
        return len(payload.get("chunks", [])) if payload else 0
