"""Build the four dense collections and four BM25 indices (Task 2.7).

Chunking is the only factor that changes the index. Retrieval methods reuse the
same four index pairs and never create extra collections.
"""

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union

from rag_service.chunkers import (
    FixedSizeChunker,
    RecursiveCharacterChunker,
    SemanticChunker,
    StructureAwareChunker,
)
from rag_service.embeddings.e5_encoder import E5Encoder
from rag_service.stores.bm25_manager import BM25Manager
from rag_service.stores.chroma_manager import ChromaManager

STRATEGIES = ("fixed", "recursive", "semantic", "structure_aware")


def create_chunker(strategy: str, chunk_size: int = 512, chunk_overlap: int = 50):
    """Instantiate the chunker for a strategy code."""
    if strategy == "fixed":
        return FixedSizeChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    if strategy == "recursive":
        return RecursiveCharacterChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    if strategy == "semantic":
        return SemanticChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    if strategy == "structure_aware":
        return StructureAwareChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    raise ValueError(f"unknown strategy {strategy!r}; expected one of {STRATEGIES}")


def _normalize_document(document: Dict[str, Any]) -> Dict[str, Any]:
    """Accept canonical corpus documents and tolerate minor field variants."""
    normalized = dict(document)
    if "doc_id" not in normalized:
        file_name = normalized.get("source_file") or normalized.get("file_name") or "doc"
        normalized["doc_id"] = Path(str(file_name)).stem
    if "clean_text" not in normalized:
        normalized["clean_text"] = normalized.get("content", "") or normalized.get("text", "")
    normalized.setdefault("source_type", "web")
    normalized.setdefault("title", normalized["doc_id"])
    normalized.setdefault("metadata", {})
    return normalized


def load_corpus(corpus_directory: Union[str, Path]) -> List[Dict[str, Any]]:
    """Load canonical JSON documents from a corpus directory."""
    directory = Path(corpus_directory)
    if not directory.exists():
        raise FileNotFoundError(f"corpus directory not found: {directory}")

    documents: List[Dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        if path.name == "metadata.json":
            continue
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        if isinstance(payload, list):
            documents.extend(_normalize_document(item) for item in payload)
        elif isinstance(payload, dict) and isinstance(payload.get("documents"), list):
            documents.extend(_normalize_document(item) for item in payload["documents"])
        elif isinstance(payload, dict):
            documents.append(_normalize_document(payload))

    return documents


def build_indexes(
    documents: Sequence[Dict[str, Any]],
    vectordb_directory: Union[str, Path] = "data/vectordb",
    encoder: Optional[E5Encoder] = None,
    strategies: Iterable[str] = STRATEGIES,
    reset: bool = True,
    batch_size: Optional[int] = None,
) -> Dict[str, Any]:
    """Chunk all documents and build four dense + four sparse indices."""
    documents = [_normalize_document(document) for document in documents]
    strategies = tuple(strategies)
    base = Path(vectordb_directory)

    encoder = encoder or E5Encoder(batch_size=batch_size or 32)
    chroma = ChromaManager(persist_directory=base / "chroma", strategies=strategies)
    bm25 = BM25Manager(persist_directory=base / "bm25", strategies=strategies)

    if reset:
        chroma.reset()
        for strategy in strategies:
            path = bm25.index_path(strategy)
            if path.exists():
                path.unlink()

    report: Dict[str, Any] = {
        "documents": len(documents),
        "dense_backend": chroma.backend,
        "sparse_backend": bm25.backend,
        "embedding_backend": encoder.backend,
        "strategies": {},
    }

    for strategy in strategies:
        chunker = create_chunker(strategy)
        chunks = []
        for document in documents:
            chunks.extend(chunker.chunk_document(document))

        embeddings = encoder.embed_documents([chunk.content for chunk in chunks])
        chroma.add_chunks(strategy, chunks, embeddings)
        bm25.build(strategy, chunks)

        report["strategies"][strategy] = {
            "chunks": len(chunks),
            "dense_count": chroma.count(strategy),
            "sparse_count": bm25.count(strategy),
            "avg_tokens": round(
                (sum(chunk.token_count for chunk in chunks) / len(chunks)) if chunks else 0.0,
                2,
            ),
        }

    return report
