"""Sparse BM25 retriever with PySastrawi preprocessing (Task 2.9)."""

from typing import List

from rag_service.retrievers.base import RetrievedChunk
from rag_service.stores.bm25_manager import BM25Manager


class SparseRetriever:
    """BM25 retrieval using the persisted index for a chunking strategy."""

    def __init__(self, store: BM25Manager, strategy: str = "structure_aware"):
        self.store = store
        self.strategy = strategy
        self.store.index_path(strategy)  # validate strategy early

    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievedChunk]:
        """Return the top-k chunks ranked by BM25 score."""
        if not query or not query.strip():
            return []
        records = self.store.search(self.strategy, query, top_k=top_k)
        return [
            RetrievedChunk.from_record(record, rank=index + 1)
            for index, record in enumerate(records)
        ]
