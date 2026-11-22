"""Base class and data structures for all document chunkers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from rag_service.chunkers.tokenizer import E5Tokenizer, default_tokenizer


@dataclass
class Chunk:
    """Represents an atomic text chunk output by a chunker."""

    chunk_id: str
    doc_id: str
    source_type: str  # "pdf", "docx", "web", etc.
    source_title: str
    content: str
    token_count: int
    start_char: int = 0
    end_char: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to a JSON-serializable dictionary."""
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "source_type": self.source_type,
            "source_title": self.source_title,
            "content": self.content,
            "token_count": self.token_count,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "metadata": self.metadata,
        }


class BaseChunker(ABC):
    """Abstract base class for all chunking strategies.

    All subclasses normalize length against the E5 token limit (512 tokens).
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        tokenizer: Optional[E5Tokenizer] = None,
    ):
        if chunk_size <= 0:
            raise ValueError(f"chunk_size must be positive, got {chunk_size}")
        if chunk_overlap < 0:
            raise ValueError(f"chunk_overlap cannot be negative, got {chunk_overlap}")
        if chunk_overlap >= chunk_size:
            raise ValueError(
                f"chunk_overlap ({chunk_overlap}) must be strictly less than chunk_size ({chunk_size})"
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.tokenizer = tokenizer or default_tokenizer

    @abstractmethod
    def chunk_text(
        self,
        text: str,
        doc_id: str = "doc",
        source_type: str = "text",
        source_title: str = "Untitled",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Chunk]:
        """Split a string into a list of Chunk objects."""
        pass

    def chunk_document(self, document: Dict[str, Any]) -> List[Chunk]:
        """Split a canonical document dictionary into a list of Chunk objects.

        Expected document fields:
            - doc_id: str
            - source_type: str ("pdf", "docx", "web")
            - title: str
            - clean_text: str
            - metadata: Optional[Dict[str, Any]]
        """
        doc_id = document.get("doc_id", "doc")
        source_type = document.get("source_type", "text")
        source_title = document.get("title", "Untitled")
        clean_text = document.get("clean_text", "")
        doc_metadata = document.get("metadata", {})

        return self.chunk_text(
            text=clean_text,
            doc_id=doc_id,
            source_type=source_type,
            source_title=source_title,
            metadata=doc_metadata,
        )
