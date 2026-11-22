"""FastAPI application for the RAG backend service (Task 2.14).

Endpoints
---------
``GET /api/health``
    Liveness/readiness probe. Never touches the embedding models, the vector
    store, or the generator, so it stays available while the heavy pipeline is
    still warming up.

``POST /api/ask``
    Run one question through the configured experiment pipeline (default
    ``E16``) and return the answer, the cited source documents, the chunk
    metadata, and the latency/token metrics required by the evaluation.

The pipeline is built lazily and cached per experiment code. Building it loads
the E5 encoder, ChromaDB, BM25, the reranker, and the generator client, so the
process must not fail at import time when the API key or corpus is missing.
"""

from typing import Any, Dict, List, Optional, Tuple

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field, field_validator

    HAS_FASTAPI = True
except ImportError:  # pragma: no cover - exercised only without FastAPI
    HAS_FASTAPI = False
    BaseModel = object  # type: ignore
    Field = lambda *args, **kwargs: None  # type: ignore
    field_validator = None  # type: ignore

if HAS_FASTAPI:
    import logging
    import re
    import threading

    logger = logging.getLogger(__name__)

    DEFAULT_EXPERIMENT_CODE = "E16"
    _CONFIG_CODE_PATTERN = re.compile(r"^E(0[1-9]|1[0-6])$")

    # Experiment codes accepted by the API. Kept here so a typo is rejected by
    # Pydantic (422) instead of failing later while loading the YAML file.
    SUPPORTED_EXPERIMENT_CODES: Tuple[str, ...] = tuple(
        f"E{number:02d}" for number in range(1, 17)
    )

    class AskRequest(BaseModel):
        """Validated payload for ``POST /api/ask``."""

        question: str = Field(
            ...,
            min_length=1,
            max_length=500,
            description="Pertanyaan pengunjung tentang program LPK MBJ Indonesia",
            examples=["Apa syarat usia program magang?"],
        )
        config_code: Optional[str] = Field(
            DEFAULT_EXPERIMENT_CODE,
            description="Kode konfigurasi eksperimen E01-E16",
            examples=["E16"],
        )
        session_id: Optional[str] = Field(
            None,
            max_length=100,
            description="Session ID pengunjung (opsional, untuk korelasi log)",
        )

        @field_validator("question")
        @classmethod
        def _question_must_not_be_blank(cls, value: str) -> str:
            question = value.strip()
            if not question:
                raise ValueError("question must not be blank")
            return question

        @field_validator("config_code")
        @classmethod
        def _normalize_config_code(cls, value: Optional[str]) -> str:
            code = (value or DEFAULT_EXPERIMENT_CODE).strip().upper()
            if not _CONFIG_CODE_PATTERN.fullmatch(code):
                raise ValueError(
                    "config_code must be one of E01-E16"
                )
            return code

    class ChunkMetadata(BaseModel):
        """Source-document metadata for one retrieved chunk."""

        chunk_id: str
        doc_id: str = ""
        source_type: str = ""
        source_title: str = ""
        score: Optional[float] = None
        token_count: int = 0
        rank: int = 0

    class AskResponse(BaseModel):
        """Payload returned to the Laravel ``ChatController``."""

        experiment_code: str
        question: str
        answer: str
        sources: List[str] = Field(
            default_factory=list,
            description="Dokumen yang dirujuk pada jawaban ([Sumber: ...])",
        )
        retrieved_sources: List[str] = Field(
            default_factory=list,
            description="Seluruh dokumen sumber dari chunk hasil retrieval",
        )
        chunks: List[ChunkMetadata] = Field(default_factory=list)
        retrieval_method: str = ""
        chunking_strategy: str = ""
        latency_ms: float = 0.0
        retrieval_latency_ms: float = 0.0
        generation_latency_ms: float = 0.0
        rerank_latency_ms: float = 0.0
        context_tokens: int = 0
        context_chunks: int = 0
        is_refusal: bool = False

    # ------------------------------------------------------------------
    # Pipeline registry (lazy, cached per experiment code)
    # ------------------------------------------------------------------

    _pipeline_cache: Dict[str, Any] = {}
    _pipeline_factory: Optional[Any] = None
    _pipeline_lock = threading.Lock()

    def set_pipeline_factory(factory: Optional[Any]) -> None:
        """Override how pipelines are built (used by tests and scripts).

        Passing ``None`` restores the real :func:`build_pipeline` factory. The
        cache is cleared so a new factory never receives a stale pipeline.
        """
        global _pipeline_factory
        with _pipeline_lock:
            _pipeline_factory = factory
            _pipeline_cache.clear()

    def clear_pipeline_cache() -> None:
        """Drop every cached pipeline (frees the loaded models)."""
        with _pipeline_lock:
            _pipeline_cache.clear()

    def get_pipeline(config_code: str) -> Any:
        """Return the cached pipeline for ``config_code``, building it once."""
        from rag_service.config import load_config

        code = (config_code or DEFAULT_EXPERIMENT_CODE).strip().upper()
        with _pipeline_lock:
            pipeline = _pipeline_cache.get(code)
            if pipeline is not None:
                return pipeline

            config = load_config(code)
            factory = _pipeline_factory
            if factory is None:
                from rag_service.pipeline import build_pipeline

                factory = build_pipeline

            pipeline = factory(config)
            _pipeline_cache[code] = pipeline
            return pipeline

    def _chunk_to_metadata(chunk: Any) -> ChunkMetadata:
        """Normalize a ``RetrievedChunk`` or plain mapping into API metadata."""

        def read(name: str, default: Any = None) -> Any:
            if isinstance(chunk, dict):
                return chunk.get(name, default)
            return getattr(chunk, name, default)

        score = read("score")
        token_count = read("token_count", 0)
        rank = read("rank", 0)
        return ChunkMetadata(
            chunk_id=str(read("chunk_id", "") or ""),
            doc_id=str(read("doc_id", "") or ""),
            source_type=str(read("source_type", "") or ""),
            source_title=str(read("source_title", "") or ""),
            score=None if score is None else float(score),
            token_count=int(token_count or 0),
            rank=int(rank or 0),
        )

    def _to_response(result: Any) -> AskResponse:
        """Map a ``PipelineResult`` (or equivalent) onto the API schema."""
        payload = result.to_dict() if hasattr(result, "to_dict") else dict(result)

        sources = list(payload.get("sources") or [])
        retrieved_sources = list(payload.get("retrieved_sources") or [])
        is_refusal = bool(payload.get("is_refusal"))
        # The generator is instructed to cite its sources inline. If it omits
        # the citation on a non-refusal answer, fall back to the retrieved
        # documents so the widget can still show a source badge.
        if not sources and not is_refusal:
            sources = list(retrieved_sources)

        return AskResponse(
            experiment_code=str(payload.get("experiment_code") or ""),
            question=str(payload.get("question") or ""),
            answer=str(payload.get("answer") or ""),
            sources=sources,
            retrieved_sources=retrieved_sources,
            chunks=[
                _chunk_to_metadata(chunk)
                for chunk in (payload.get("chunks") or [])
            ],
            retrieval_method=str(payload.get("retrieval_method") or ""),
            chunking_strategy=str(payload.get("chunking_strategy") or ""),
            latency_ms=float(payload.get("latency_ms") or 0.0),
            retrieval_latency_ms=float(payload.get("retrieval_latency_ms") or 0.0),
            generation_latency_ms=float(
                payload.get("generation_latency_ms") or 0.0
            ),
            rerank_latency_ms=float(payload.get("rerank_latency_ms") or 0.0),
            context_tokens=int(payload.get("context_tokens") or 0),
            context_chunks=int(payload.get("context_chunks") or 0),
            is_refusal=is_refusal,
        )

    app = FastAPI(
        title="LPK MBJ Indonesia - RAG Chatbot Backend",
        description="Backend API for RAG AI Chatbot experiment on heterogeneous corpus",
        version="2.2.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health_check() -> Dict[str, Any]:
        """Health check endpoint for service monitoring."""
        from rag_service.config import available_configs

        return {
            "status": "ok",
            "service": "rag_backend",
            "version": "2.2.0",
            "supported_chunkers": [
                "fixed",
                "recursive",
                "semantic",
                "structure_aware",
            ],
            "supported_retrievers": [
                "dense",
                "sparse_bm25",
                "hybrid_rrf",
                "hybrid_rerank",
            ],
            "available_experiments": available_configs(),
        }

    @app.post("/api/ask", response_model=AskResponse)
    def ask(request: AskRequest) -> AskResponse:
        """Answer one question through the configured RAG experiment pipeline."""
        from rag_service.config import ConfigError
        from rag_service.llm import GeneratorError

        try:
            pipeline = get_pipeline(request.config_code)
            result = pipeline.ask(request.question)
        except FileNotFoundError as exc:
            raise HTTPException(
                status_code=404,
                detail=f"Konfigurasi eksperimen {request.config_code} tidak ditemukan.",
            ) from exc
        except ConfigError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Konfigurasi eksperimen tidak valid: {exc}",
            ) from exc
        except GeneratorError as exc:
            logger.error("RAG generator unavailable: %s", exc)
            raise HTTPException(
                status_code=503,
                detail=(
                    "Layanan generator sedang tidak tersedia. "
                    "Periksa konfigurasi API key dan koneksi ke gateway."
                ),
            ) from exc
        except (ImportError, ModuleNotFoundError) as exc:
            logger.exception("RAG dependency missing")
            raise HTTPException(
                status_code=503,
                detail="Komponen RAG backend belum terpasang lengkap.",
            ) from exc
        except Exception as exc:  # noqa: BLE001 - boundary of the HTTP service
            logger.exception("RAG pipeline failed")
            raise HTTPException(
                status_code=500,
                detail="Terjadi kesalahan saat memproses pertanyaan.",
            ) from exc

        return _to_response(result)

else:  # pragma: no cover - exercised only without FastAPI
    app = None
    DEFAULT_EXPERIMENT_CODE = "E16"

    def set_pipeline_factory(factory: Optional[Any]) -> None:
        raise RuntimeError("FastAPI is not installed")

    def clear_pipeline_cache() -> None:
        raise RuntimeError("FastAPI is not installed")


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run("rag_service.main:app", host="0.0.0.0", port=8001, reload=False)
