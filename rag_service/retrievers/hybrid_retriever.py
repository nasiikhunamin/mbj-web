"""Hybrid retrieval with Reciprocal Rank Fusion (Task 2.10).

RRF is deterministic and weight-free:

    score(d) = sum(1 / (k + rank_i(d)))   with k = 60, ranks starting at 1

No alpha weighting is applied, matching the locked experiment design.
"""

from typing import Dict, List, Sequence

from rag_service.retrievers.base import RetrievedChunk
from rag_service.retrievers.dense_retriever import DenseRetriever
from rag_service.retrievers.sparse_retriever import SparseRetriever


class HybridRetriever:
    """Fuse dense and sparse rankings using pure RRF."""

    def __init__(
        self,
        dense_retriever: DenseRetriever,
        sparse_retriever: SparseRetriever,
        rrf_k: int = 60,
    ):
        if rrf_k <= 0:
            raise ValueError(f"rrf_k must be positive, got {rrf_k}")
        self.dense_retriever = dense_retriever
        self.sparse_retriever = sparse_retriever
        self.rrf_k = rrf_k

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        candidate_k: int = 20,
    ) -> List[RetrievedChunk]:
        """Retrieve Top-N from both sources, deduplicate, fuse, return Top-K."""
        if not query or not query.strip():
            return []

        dense_results = self.dense_retriever.retrieve(query, top_k=candidate_k)
        sparse_results = self.sparse_retriever.retrieve(query, top_k=candidate_k)
        return self.rrf_fuse(
            [dense_results, sparse_results],
            rrf_k=self.rrf_k,
            top_k=top_k,
        )

    @staticmethod
    def rrf_fuse(
        result_lists: Sequence[Sequence[RetrievedChunk]],
        rrf_k: int = 60,
        top_k: int = 5,
    ) -> List[RetrievedChunk]:
        """Fuse ranked lists with RRF, preserving the first seen chunk payload."""
        if rrf_k <= 0:
            raise ValueError(f"rrf_k must be positive, got {rrf_k}")
        if top_k <= 0:
            raise ValueError(f"top_k must be positive, got {top_k}")

        scores: Dict[str, float] = {}
        payloads: Dict[str, RetrievedChunk] = {}
        source_ranks: Dict[str, Dict[str, int]] = {}

        for source_name, results in zip(("dense", "sparse"), result_lists):
            for rank, chunk in enumerate(results, start=1):
                if not chunk.chunk_id:
                    continue
                scores[chunk.chunk_id] = scores.get(chunk.chunk_id, 0.0) + (
                    1.0 / (rrf_k + rank)
                )
                if chunk.chunk_id not in payloads:
                    payloads[chunk.chunk_id] = chunk
                source_ranks.setdefault(chunk.chunk_id, {})[source_name] = rank

        ranked_ids = sorted(scores, key=lambda chunk_id: (-scores[chunk_id], chunk_id))

        fused: List[RetrievedChunk] = []
        for rank, chunk_id in enumerate(ranked_ids[:top_k], start=1):
            base = payloads[chunk_id]
            fused.append(
                RetrievedChunk(
                    chunk_id=base.chunk_id,
                    content=base.content,
                    score=scores[chunk_id],
                    doc_id=base.doc_id,
                    source_type=base.source_type,
                    source_title=base.source_title,
                    token_count=base.token_count,
                    metadata={**base.metadata, "rrf_candidate_ranks": source_ranks[chunk_id]},
                    rank=rank,
                )
            )
        return fused
