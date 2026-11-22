"""Dense vector storage with exactly four ChromaDB collections.

Task 2.7 requires one dense collection per chunking strategy. ChromaDB is used
when installed; otherwise a persistent JSON cosine store with the same interface
is used so the pipeline remains runnable offline.
"""

import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union

from rag_service.chunkers.base import Chunk

try:
    import chromadb  # type: ignore
    from chromadb.config import Settings  # type: ignore

    HAS_CHROMADB = True
except ImportError:
    chromadb = None  # type: ignore
    Settings = None  # type: ignore
    HAS_CHROMADB = False


COLLECTION_PREFIX = "chroma_"
STRATEGIES = ("fixed", "recursive", "semantic", "structure_aware")

Record = Dict[str, Any]


def _chunk_to_dict(chunk: Union[Chunk, Record]) -> Record:
    """Normalize a Chunk object or dictionary into a plain record."""
    if isinstance(chunk, Chunk):
        return chunk.to_dict()
    if isinstance(chunk, dict):
        return dict(chunk)
    raise TypeError(f"unsupported chunk type: {type(chunk)!r}")


def _cosine_similarity(vec_a: Sequence[float], vec_b: Sequence[float]) -> float:
    """Compute cosine similarity without requiring numpy."""
    if len(vec_a) != len(vec_b) or not vec_a:
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


class ChromaManager:
    """Manage the four dense collections (fixed, recursive, semantic, structure_aware)."""

    def __init__(
        self,
        persist_directory: Union[str, Path] = "data/vectordb/chroma",
        strategies: Iterable[str] = STRATEGIES,
        collection_prefix: str = COLLECTION_PREFIX,
    ):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.strategies = tuple(strategies)
        self.collection_prefix = collection_prefix

        self._client = None
        self._collections: Dict[str, Any] = {}
        self._fallback_cache: Dict[str, List[Record]] = {}

        self.backend = "json_fallback"
        if HAS_CHROMADB:
            try:
                settings = Settings(anonymized_telemetry=False, allow_reset=True)
                self._client = chromadb.PersistentClient(
                    path=str(self.persist_directory),
                    settings=settings,
                )
                self.backend = "chromadb"
            except Exception:
                self._client = None

    def collection_name(self, strategy: str) -> str:
        """Return the canonical collection name for a chunking strategy."""
        if strategy not in self.strategies:
            raise ValueError(
                f"unknown strategy {strategy!r}; expected one of {self.strategies}"
            )
        return f"{self.collection_prefix}{strategy}"

    def _fallback_path(self, strategy: str) -> Path:
        return self.persist_directory / f"{self.collection_name(strategy)}.json"

    def _get_collection(self, strategy: str) -> Any:
        """Get or create the Chroma collection for a strategy."""
        name = self.collection_name(strategy)
        if name not in self._collections:
            self._collections[name] = self._client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collections[name]

    def _load_fallback(self, strategy: str) -> List[Record]:
        """Load the JSON fallback records for a strategy."""
        if strategy in self._fallback_cache:
            return self._fallback_cache[strategy]

        path = self._fallback_path(strategy)
        records: List[Record] = []
        if path.exists():
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            records = payload.get("records", []) if isinstance(payload, dict) else payload
        self._fallback_cache[strategy] = records
        return records

    def _save_fallback(self, strategy: str, records: List[Record]) -> None:
        """Persist fallback records to disk."""
        path = self._fallback_path(strategy)
        payload = {"strategy": strategy, "records": records}
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False)

    @staticmethod
    def _flatten_metadata(chunk: Record) -> Record:
        """Flatten nested chunk metadata into Chroma-compatible scalar values."""
        metadata: Record = {
            "doc_id": chunk.get("doc_id", ""),
            "source_type": chunk.get("source_type", ""),
            "source_title": chunk.get("source_title", ""),
            "token_count": int(chunk.get("token_count", 0) or 0),
        }
        for key, value in (chunk.get("metadata") or {}).items():
            if value is None:
                continue
            if isinstance(value, (str, int, float, bool)):
                metadata[f"meta_{key}"] = value
            else:
                metadata[f"meta_{key}"] = json.dumps(value, ensure_ascii=False)
        return metadata

    @staticmethod
    def _record_from_chroma(
        chunk_id: str,
        content: str,
        metadata: Optional[Record],
        score: float,
    ) -> Record:
        """Rebuild the common record shape from Chroma query output."""
        metadata = metadata or {}
        nested_metadata = {
            key[len("meta_") :]: value
            for key, value in metadata.items()
            if key.startswith("meta_")
        }
        return {
            "chunk_id": chunk_id,
            "content": content,
            "doc_id": metadata.get("doc_id", ""),
            "source_type": metadata.get("source_type", ""),
            "source_title": metadata.get("source_title", ""),
            "token_count": int(metadata.get("token_count", 0) or 0),
            "metadata": nested_metadata,
            "score": float(score),
        }

    def add_chunks(
        self,
        strategy: str,
        chunks: Sequence[Union[Chunk, Record]],
        embeddings: Sequence[Sequence[float]],
    ) -> int:
        """Insert or update chunks and their embeddings in a strategy collection."""
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"chunks ({len(chunks)}) and embeddings ({len(embeddings)}) must have equal length"
            )
        if not chunks:
            return 0

        records = [_chunk_to_dict(chunk) for chunk in chunks]

        if self.backend == "chromadb":
            collection = self._get_collection(strategy)
            collection.upsert(
                ids=[record["chunk_id"] for record in records],
                documents=[record.get("content", "") for record in records],
                metadatas=[self._flatten_metadata(record) for record in records],
                embeddings=[[float(x) for x in vector] for vector in embeddings],
            )
            return len(records)

        existing = {record["chunk_id"]: record for record in self._load_fallback(strategy)}
        for record, embedding in zip(records, embeddings):
            existing[record["chunk_id"]] = {
                **record,
                "embedding": [float(x) for x in embedding],
            }
        self._fallback_cache[strategy] = list(existing.values())
        self._save_fallback(strategy, self._fallback_cache[strategy])
        return len(records)

    def query(
        self,
        strategy: str,
        query_embedding: Sequence[float],
        top_k: int = 5,
    ) -> List[Record]:
        """Return the top-k most similar chunks for a strategy."""
        if top_k <= 0:
            raise ValueError(f"top_k must be positive, got {top_k}")
        self.collection_name(strategy)  # validate strategy name

        if self.backend == "chromadb":
            collection = self._get_collection(strategy)
            count = collection.count()
            if count == 0:
                return []
            result = collection.query(
                query_embeddings=[[float(x) for x in query_embedding]],
                n_results=min(top_k, count),
                include=["documents", "metadatas", "distances"],
            )
            ids = (result.get("ids") or [[]])[0]
            documents = (result.get("documents") or [[]])[0]
            metadatas = (result.get("metadatas") or [[]])[0]
            distances = (result.get("distances") or [[]])[0]
            return [
                self._record_from_chroma(
                    chunk_id=chunk_id,
                    content=document or "",
                    metadata=metadata,
                    score=1.0 - float(distance),
                )
                for chunk_id, document, metadata, distance in zip(
                    ids, documents, metadatas, distances
                )
            ]

        scored: List[Record] = []
        for record in self._load_fallback(strategy):
            embedding = record.get("embedding") or []
            score = _cosine_similarity(query_embedding, embedding)
            scored.append(
                {
                    key: value
                    for key, value in record.items()
                    if key != "embedding"
                }
                | {"score": score}
            )
        scored.sort(key=lambda item: (-item["score"], item["chunk_id"]))
        return scored[:top_k]

    def count(self, strategy: str) -> int:
        """Return the number of indexed chunks for a strategy."""
        self.collection_name(strategy)  # validate strategy name
        if self.backend == "chromadb":
            return int(self._get_collection(strategy).count())
        return len(self._load_fallback(strategy))

    def reset(self, strategy: Optional[str] = None) -> None:
        """Delete one collection or all four collections."""
        targets = [strategy] if strategy else list(self.strategies)
        for target in targets:
            self.collection_name(target)  # validate strategy name
            name = self.collection_name(target)
            if self.backend == "chromadb":
                try:
                    self._client.delete_collection(name=name)
                except Exception:
                    pass
                self._collections.pop(name, None)
            else:
                path = self._fallback_path(target)
                if path.exists():
                    path.unlink()
                self._fallback_cache.pop(target, None)
