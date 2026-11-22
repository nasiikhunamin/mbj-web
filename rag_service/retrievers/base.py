"""Shared retrieval data structures."""

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class RetrievedChunk:
    """A chunk returned by a retriever, normalized across dense and sparse stores."""

    chunk_id: str
    content: str
    score: float
    doc_id: str = ""
    source_type: str = ""
    source_title: str = ""
    token_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    rank: int = 0

    @classmethod
    def from_record(cls, record: Dict[str, Any], rank: int = 0) -> "RetrievedChunk":
        """Build a RetrievedChunk from a store result dictionary."""
        return cls(
            chunk_id=record.get("chunk_id", ""),
            content=record.get("content", ""),
            score=float(record.get("score", 0.0) or 0.0),
            doc_id=record.get("doc_id", ""),
            source_type=record.get("source_type", ""),
            source_title=record.get("source_title", ""),
            token_count=int(record.get("token_count", 0) or 0),
            metadata=dict(record.get("metadata") or {}),
            rank=rank,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-serializable dictionary."""
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "score": self.score,
            "doc_id": self.doc_id,
            "source_type": self.source_type,
            "source_title": self.source_title,
            "token_count": self.token_count,
            "metadata": self.metadata,
            "rank": self.rank,
        }
