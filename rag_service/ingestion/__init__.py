"""Corpus ingestion: multi-format parsers and orchestration (Task 1.1)."""

from rag_service.ingestion.ingest import (
    IngestionError,
    discover_sources,
    ingest,
)
from rag_service.ingestion.metadata import (
    CONTENT_TYPES,
    MetadataError,
    build_metadata,
    load_corpus_documents,
    load_labels,
    apply_content_types,
)
from rag_service.ingestion.parsers import (
    finalize_document,
    make_doc_id,
    parse_blade,
    parse_docx,
    parse_file,
    parse_pdf,
)

__all__ = [
    "CONTENT_TYPES",
    "IngestionError",
    "MetadataError",
    "apply_content_types",
    "build_metadata",
    "discover_sources",
    "finalize_document",
    "ingest",
    "load_corpus_documents",
    "load_labels",
    "make_doc_id",
    "parse_blade",
    "parse_docx",
    "parse_file",
    "parse_pdf",
]
