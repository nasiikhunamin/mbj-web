"""RAG orchestrator pipeline (Task 2.13).

Connects the retrieval stage (dense / sparse / hybrid RRF), the optional
cross-encoder reranker, and the generator client, while recording the latency
breakdown and the context token length required by the experiment.

The pipeline is config-driven: the four factors of E01-E16 are selected from the
YAML experiment file, and components are injected so the orchestrator can be
tested end-to-end without loading real models.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Union

from rag_service.config import ExperimentConfig, load_config
from rag_service.llm.generator import GeneratorClient
from rag_service.retrievers.base import RetrievedChunk


@dataclass(frozen=True)
class PipelineResult:
    """Complete response payload plus the metrics needed for evaluation."""

    experiment_code: str
    question: str
    answer: str
    sources: List[str]
    chunks: List[RetrievedChunk]
    retrieved_sources: List[str]
    retrieval_method: str
    chunking_strategy: str
    latency_ms: float
    retrieval_latency_ms: float
    generation_latency_ms: float
    rerank_latency_ms: float
    context_tokens: int
    context_chunks: int
    is_refusal: bool
    generator_snapshot: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable payload for the FastAPI layer and logs."""
        return {
            "experiment_code": self.experiment_code,
            "question": self.question,
            "answer": self.answer,
            "sources": list(self.sources),
            "retrieved_sources": list(self.retrieved_sources),
            "chunks": [chunk.to_dict() for chunk in self.chunks],
            "retrieval_method": self.retrieval_method,
            "chunking_strategy": self.chunking_strategy,
            "latency_ms": self.latency_ms,
            "retrieval_latency_ms": self.retrieval_latency_ms,
            "generation_latency_ms": self.generation_latency_ms,
            "rerank_latency_ms": self.rerank_latency_ms,
            "context_tokens": self.context_tokens,
            "context_chunks": self.context_chunks,
            "is_refusal": self.is_refusal,
            "generator": dict(self.generator_snapshot),
        }


def _normalize_chunks(chunks: Sequence[Any]) -> List[RetrievedChunk]:
    normalized: List[RetrievedChunk] = []
    for chunk in chunks:
        if isinstance(chunk, RetrievedChunk):
            normalized.append(chunk)
        elif isinstance(chunk, dict):
            normalized.append(RetrievedChunk.from_record(chunk))
        else:
            raise TypeError(f"unsupported chunk type: {type(chunk)!r}")
    return normalized


def _unique_sources(chunks: Sequence[RetrievedChunk]) -> List[str]:
    sources: List[str] = []
    for chunk in chunks:
        title = (chunk.source_title or chunk.doc_id or "").strip()
        if title and title not in sources:
            sources.append(title)
    return sources


class RAGPipeline:
    """Orchestrate retrieval, reranking, and generation for one experiment config."""

    def __init__(
        self,
        config: ExperimentConfig,
        generator: Any,
        dense: Optional[Any] = None,
        sparse: Optional[Any] = None,
        hybrid: Optional[Any] = None,
        reranker: Optional[Any] = None,
        tokenizer: Optional[Any] = None,
    ):
        if not isinstance(config, ExperimentConfig):
            raise TypeError("config must be an ExperimentConfig instance")
        if generator is None:
            raise ValueError("generator is required")

        method = config.retrieval_method
        if method == "dense" and dense is None:
            raise ValueError("dense retriever is required for retrieval_method=dense")
        if method == "sparse_bm25" and sparse is None:
            raise ValueError(
                "sparse retriever is required for retrieval_method=sparse_bm25"
            )
        if method in ("hybrid_rrf", "hybrid_rerank") and hybrid is None:
            raise ValueError(
                f"hybrid retriever is required for retrieval_method={method}"
            )
        if method == "hybrid_rerank" and reranker is None:
            raise ValueError(
                "reranker is required for retrieval_method=hybrid_rerank"
            )

        if tokenizer is None:
            from rag_service.chunkers.tokenizer import E5Tokenizer

            tokenizer = E5Tokenizer(config.tokenizer_model)

        self.config = config
        self.generator = generator
        self.dense = dense
        self.sparse = sparse
        self.hybrid = hybrid
        self.reranker = reranker
        self.tokenizer = tokenizer

    @classmethod
    def from_config(
        cls, source: Union[ExperimentConfig, str]
    ) -> "RAGPipeline":
        """Build the real pipeline from an experiment config or YAML path/code."""
        config = source if isinstance(source, ExperimentConfig) else load_config(source)
        return build_pipeline(config)

    def _retrieve(self, question: str) -> tuple[List[RetrievedChunk], float]:
        """Run the configured retrieval method and return chunks + rerank latency."""
        method = self.config.retrieval_method
        rerank_latency_ms = 0.0

        if method == "dense":
            chunks = self.dense.retrieve(question, top_k=self.config.final_top_n)
        elif method == "sparse_bm25":
            chunks = self.sparse.retrieve(question, top_k=self.config.final_top_n)
        elif method == "hybrid_rrf":
            chunks = self.hybrid.retrieve(
                question,
                top_k=self.config.final_top_n,
                candidate_k=self.config.initial_candidates,
            )
        elif method == "hybrid_rerank":
            candidates = self.hybrid.retrieve(
                question,
                top_k=self.config.initial_candidates,
                candidate_k=self.config.initial_candidates,
            )
            rerank_started = time.perf_counter()
            chunks = self.reranker.rerank(
                question,
                candidates,
                top_n=self.config.reranker_top_n,
            )
            rerank_latency_ms = (time.perf_counter() - rerank_started) * 1000.0
        else:  # pragma: no cover - ExperimentConfig already validates this
            raise ValueError(f"unsupported retrieval method: {method!r}")

        return _normalize_chunks(chunks), rerank_latency_ms

    def ask(self, question: str) -> PipelineResult:
        """Answer one question and record the full latency/metric payload."""
        if not question or not question.strip():
            raise ValueError("question must not be empty")
        question = question.strip()

        started = time.perf_counter()

        retrieval_started = time.perf_counter()
        chunks, rerank_latency_ms = self._retrieve(question)
        retrieval_latency_ms = (time.perf_counter() - retrieval_started) * 1000.0

        generation_started = time.perf_counter()
        generation = self.generator.generate(question, chunks)
        generation_latency_ms = (time.perf_counter() - generation_started) * 1000.0

        total_latency_ms = (time.perf_counter() - started) * 1000.0

        context_text = GeneratorClient.build_context(chunks) if chunks else ""
        context_tokens = (
            int(self.tokenizer.count_tokens(context_text)) if context_text else 0
        )

        return PipelineResult(
            experiment_code=self.config.code,
            question=question,
            answer=generation.answer,
            sources=list(generation.sources),
            chunks=chunks,
            retrieved_sources=_unique_sources(chunks),
            retrieval_method=self.config.retrieval_method,
            chunking_strategy=self.config.chunking_strategy,
            latency_ms=total_latency_ms,
            retrieval_latency_ms=retrieval_latency_ms,
            generation_latency_ms=generation_latency_ms,
            rerank_latency_ms=rerank_latency_ms,
            context_tokens=context_tokens,
            context_chunks=len(chunks),
            is_refusal=bool(generation.is_refusal),
            generator_snapshot=dict(generation.snapshot),
        )


def build_pipeline(config: ExperimentConfig) -> RAGPipeline:
    """Construct the real pipeline (E5, Chroma, BM25, reranker, generator)."""
    from rag_service.embeddings.e5_encoder import E5Encoder
    from rag_service.rerankers.bge_reranker import BGEReranker
    from rag_service.retrievers.dense_retriever import DenseRetriever
    from rag_service.retrievers.hybrid_retriever import HybridRetriever
    from rag_service.retrievers.sparse_retriever import SparseRetriever
    from rag_service.stores.bm25_manager import BM25Manager
    from rag_service.stores.chroma_manager import ChromaManager

    # Build the generator first so a missing API key fails before loading models.
    generator = GeneratorClient(config.generation)

    dense_store = ChromaManager(persist_directory=config.chroma_directory)
    bm25_store = BM25Manager(persist_directory=config.bm25_directory)
    encoder = E5Encoder(model_name=config.embedding_model)

    dense = DenseRetriever(
        dense_store,
        strategy=config.chunking_strategy,
        encoder=encoder,
    )
    sparse = SparseRetriever(bm25_store, strategy=config.chunking_strategy)
    hybrid = HybridRetriever(dense, sparse, rrf_k=config.rrf_k)

    reranker = None
    if config.reranker_enabled:
        reranker = BGEReranker(model_name=config.reranker_model, top_n=config.reranker_top_n)

    from rag_service.chunkers.tokenizer import E5Tokenizer

    return RAGPipeline(
        config=config,
        generator=generator,
        dense=dense,
        sparse=sparse,
        hybrid=hybrid,
        reranker=reranker,
        tokenizer=E5Tokenizer(config.tokenizer_model),
    )
