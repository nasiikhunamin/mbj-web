"""E5 embedding wrapper with mandatory asymmetric prefixes.

Task 2.6: all corpus passages MUST be embedded as ``"passage: <text>"`` and all
queries as ``"query: <text>"``. The wrapper lazily loads
``intfloat/multilingual-e5-base`` via sentence-transformers and falls back to a
deterministic hashed lexical embedder when the model cannot be loaded (offline
environment or missing torch). The fallback keeps the same 768 dimensions so
downstream storage stays compatible.
"""

import hashlib
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

try:
    from sentence_transformers import SentenceTransformer  # type: ignore

    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    SentenceTransformer = None  # type: ignore
    HAS_SENTENCE_TRANSFORMERS = False


_MODEL_CACHE: Dict[Tuple[str, str], Any] = {}


class E5Encoder:
    """Encode documents and queries for ``intfloat/multilingual-e5-base``."""

    DEFAULT_MODEL_NAME = "intfloat/multilingual-e5-base"
    DOCUMENT_PREFIX = "passage: "
    QUERY_PREFIX = "query: "
    DIMENSION = 768

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        device: Optional[str] = None,
        batch_size: int = 32,
        dimension: int = DIMENSION,
        allow_fallback: bool = True,
    ):
        if batch_size <= 0:
            raise ValueError(f"batch_size must be positive, got {batch_size}")
        if dimension <= 0:
            raise ValueError(f"dimension must be positive, got {dimension}")

        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size
        self.dimension = dimension
        self.allow_fallback = allow_fallback

        self._model = None
        self._load_attempted = False

    @property
    def backend(self) -> str:
        """Return the active embedding backend name."""
        self._ensure_model()
        return "sentence-transformers" if self._model is not None else "hash-fallback"

    def _ensure_model(self) -> None:
        """Load the sentence-transformers model once, if possible."""
        if self._load_attempted:
            return
        self._load_attempted = True

        if not HAS_SENTENCE_TRANSFORMERS:
            if not self.allow_fallback:
                raise RuntimeError(
                    "sentence-transformers is not installed; set allow_fallback=True "
                    "to use the deterministic hashed embedder"
                )
            return

        cache_key = (self.model_name, self.device or "")
        cached_model = _MODEL_CACHE.get(cache_key)
        if cached_model is not None:
            self._model = cached_model
            return

        try:
            kwargs = {}
            if self.device:
                kwargs["device"] = self.device
            self._model = SentenceTransformer(self.model_name, **kwargs)
            _MODEL_CACHE[cache_key] = self._model
        except Exception as exc:  # model missing locally, no network, etc.
            self._model = None
            if not self.allow_fallback:
                raise RuntimeError(
                    f"failed to load embedding model {self.model_name}: {exc}"
                ) from exc

    def embed_documents(self, texts: Sequence[str]) -> List[List[float]]:
        """Embed corpus passages, automatically prepending ``"passage: "``."""
        if isinstance(texts, str):
            raise TypeError("embed_documents expects a sequence of strings, not a single string")
        prefixed = [self.DOCUMENT_PREFIX + text for text in texts]
        return self._encode(prefixed)

    def embed_query(self, text: str) -> List[float]:
        """Embed a search query, automatically prepending ``"query: "``."""
        if not isinstance(text, str):
            raise TypeError("embed_query expects a string")
        vectors = self._encode([self.QUERY_PREFIX + text])
        return vectors[0] if vectors else self._hashed_embedding(self.QUERY_PREFIX + text)

    def _encode(self, prefixed_texts: List[str]) -> List[List[float]]:
        """Encode already-prefixed texts in batches."""
        if not prefixed_texts:
            return []

        self._ensure_model()
        if self._model is not None:
            vectors = self._model.encode(
                prefixed_texts,
                batch_size=self.batch_size,
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
            return [[float(value) for value in vector] for vector in vectors]

        return [self._hashed_embedding(text) for text in prefixed_texts]

    def _hashed_embedding(self, text: str) -> List[float]:
        """Deterministic signed hashing embedder used when the model is unavailable.

        Word unigrams and character trigrams are hashed into ``dimension`` buckets
        with a stable digest, then L2-normalized. Semantics are weak, but retrieval
        stays deterministic and prefix-sensitive for offline tests.
        """
        vector = [0.0] * self.dimension
        lowered = text.lower()
        tokens = re.findall(r"\w+|[^\w\s]", lowered, flags=re.UNICODE)

        features: List[str] = list(tokens)
        for token in tokens:
            if len(token) >= 3 and token.isalnum():
                padded = f"#{token}#"
                features.extend(padded[i : i + 3] for i in range(len(padded) - 2))

        for feature in features:
            digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest[:4], "little") % self.dimension
            sign = 1.0 if digest[4] & 1 else -1.0
            vector[index] += sign

        norm = sum(value * value for value in vector) ** 0.5
        if norm == 0.0:
            return vector
        return [value / norm for value in vector]
