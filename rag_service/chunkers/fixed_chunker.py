"""Fixed-size token chunker with strict E5 token limits."""

from typing import Any, Dict, List, Optional
from rag_service.chunkers.base import BaseChunker, Chunk
from rag_service.chunkers.tokenizer import E5Tokenizer


class FixedSizeChunker(BaseChunker):
    """Chunks text into uniform windows of N tokens with a fixed token overlap.

    Does not respect sentence or paragraph boundaries, matching the experimental
    definition of the Fixed-Size baseline in the research paper.
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        tokenizer: Optional[E5Tokenizer] = None,
    ):
        super().__init__(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            tokenizer=tokenizer,
        )

    def chunk_text(
        self,
        text: str,
        doc_id: str = "doc",
        source_type: str = "text",
        source_title: str = "Untitled",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Chunk]:
        """Split text into fixed-size token chunks."""
        text = text.strip()
        if not text:
            return []

        metadata = dict(metadata or {})
        total_tokens = self.tokenizer.count_tokens(text)

        # If text is already within chunk_size, return as single chunk
        if total_tokens <= self.chunk_size:
            return [
                Chunk(
                    chunk_id=f"{doc_id}_fix_0000",
                    doc_id=doc_id,
                    source_type=source_type,
                    source_title=source_title,
                    content=text,
                    token_count=total_tokens,
                    start_char=0,
                    end_char=len(text),
                    metadata={**metadata, "chunk_index": 0, "strategy": "fixed"},
                )
            ]

        # Use HuggingFace tokenizer fast encoding if present
        hf_tok = self.tokenizer._hf_tokenizer
        if hf_tok is not None:
            return self._chunk_with_hf_tokenizer(
                text=text,
                doc_id=doc_id,
                source_type=source_type,
                source_title=source_title,
                metadata=metadata,
                hf_tok=hf_tok,
            )

        return self._chunk_with_fallback_tokenizer(
            text=text,
            doc_id=doc_id,
            source_type=source_type,
            source_title=source_title,
            metadata=metadata,
        )

    def _chunk_with_hf_tokenizer(
        self,
        text: str,
        doc_id: str,
        source_type: str,
        source_title: str,
        metadata: Dict[str, Any],
        hf_tok: Any,
    ) -> List[Chunk]:
        """Chunk using HuggingFace tokenizer offsets for character-level fidelity."""
        encoding = hf_tok(text, add_special_tokens=False, return_offsets_mapping=True)
        input_ids = encoding["input_ids"]
        offsets = encoding["offset_mapping"]

        step = max(1, self.chunk_size - self.chunk_overlap)
        chunks: List[Chunk] = []
        chunk_idx = 0

        for start_idx in range(0, len(input_ids), step):
            end_idx = min(start_idx + self.chunk_size, len(input_ids))
            sub_ids = input_ids[start_idx:end_idx]

            start_char = offsets[start_idx][0]
            end_char = offsets[end_idx - 1][1]
            chunk_text = text[start_char:end_char].strip()

            chunks.append(
                Chunk(
                    chunk_id=f"{doc_id}_fix_{chunk_idx:04d}",
                    doc_id=doc_id,
                    source_type=source_type,
                    source_title=source_title,
                    content=chunk_text,
                    token_count=len(sub_ids),
                    start_char=start_char,
                    end_char=end_char,
                    metadata={**metadata, "chunk_index": chunk_idx, "strategy": "fixed"},
                )
            )
            chunk_idx += 1
            if end_idx >= len(input_ids):
                break

        return chunks

    def _chunk_with_fallback_tokenizer(
        self,
        text: str,
        doc_id: str,
        source_type: str,
        source_title: str,
        metadata: Dict[str, Any],
    ) -> List[Chunk]:
        """Word/whitespace sliding window fallback when HF tokenizer is offline."""
        import re

        # Split into tokens matching E5Tokenizer fallback
        matches = list(re.finditer(r"\w+|[^\w\s]|\s+", text, flags=re.UNICODE))
        if not matches:
            return []

        step = max(1, self.chunk_size - self.chunk_overlap)
        chunks: List[Chunk] = []
        chunk_idx = 0

        for start_idx in range(0, len(matches), step):
            end_idx = min(start_idx + self.chunk_size, len(matches))
            start_char = matches[start_idx].start()
            end_char = matches[end_idx - 1].end()
            chunk_text = text[start_char:end_char].strip()
            token_count = end_idx - start_idx

            chunks.append(
                Chunk(
                    chunk_id=f"{doc_id}_fix_{chunk_idx:04d}",
                    doc_id=doc_id,
                    source_type=source_type,
                    source_title=source_title,
                    content=chunk_text,
                    token_count=token_count,
                    start_char=start_char,
                    end_char=end_char,
                    metadata={**metadata, "chunk_index": chunk_idx, "strategy": "fixed"},
                )
            )
            chunk_idx += 1
            if end_idx >= len(matches):
                break

        return chunks
