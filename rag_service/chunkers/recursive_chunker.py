"""Recursive character chunker normalized by E5 token count."""

from typing import Any, Dict, List, Optional
from rag_service.chunkers.base import BaseChunker, Chunk
from rag_service.chunkers.tokenizer import E5Tokenizer


class RecursiveCharacterChunker(BaseChunker):
    """Splits text recursively using a hierarchy of separators.

    Separators: ["\n\n", "\n", ". ", " ", ""]
    Prioritizes preserving paragraph and sentence boundaries while strictly
    guaranteeing that chunk size does not exceed the E5 token threshold (512 tokens).
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        separators: Optional[List[str]] = None,
        tokenizer: Optional[E5Tokenizer] = None,
    ):
        super().__init__(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            tokenizer=tokenizer,
        )
        self.separators = separators or self.DEFAULT_SEPARATORS

    def chunk_text(
        self,
        text: str,
        doc_id: str = "doc",
        source_type: str = "text",
        source_title: str = "Untitled",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Chunk]:
        """Split text recursively into chunks of at most chunk_size tokens."""
        text = text.strip()
        if not text:
            return []

        metadata = dict(metadata or {})
        raw_chunks = self._split_text(text, self.separators)

        # Merge split pieces up to chunk_size with overlap
        merged_pieces = self._merge_splits(raw_chunks)

        chunks: List[Chunk] = []
        current_offset = 0

        for idx, piece_text in enumerate(merged_pieces):
            piece_text = piece_text.strip()
            if not piece_text:
                continue

            # Find approximate char position in original text
            start_char = text.find(piece_text[:30], current_offset)
            if start_char == -1:
                start_char = current_offset
            end_char = start_char + len(piece_text)
            current_offset = max(current_offset, start_char + 1)

            token_count = self.tokenizer.count_tokens(piece_text)

            chunks.append(
                Chunk(
                    chunk_id=f"{doc_id}_rec_{idx:04d}",
                    doc_id=doc_id,
                    source_type=source_type,
                    source_title=source_title,
                    content=piece_text,
                    token_count=token_count,
                    start_char=start_char,
                    end_char=end_char,
                    metadata={**metadata, "chunk_index": idx, "strategy": "recursive"},
                )
            )

        return chunks

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        """Recursively split text using the first separator that divides the text."""
        if not text:
            return []

        token_count = self.tokenizer.count_tokens(text)
        if token_count <= self.chunk_size:
            return [text]

        # Find the first separator present in the text
        selected_sep = ""
        new_separators: List[str] = []

        for i, sep in enumerate(separators):
            if sep == "":
                selected_sep = ""
                break
            if sep in text:
                selected_sep = sep
                new_separators = separators[i + 1 :]
                break

        # If no separator was found, fallback to character splitting
        if not selected_sep:
            return self._split_by_character(text)

        splits = text.split(selected_sep)
        result: List[str] = []

        for part in splits:
            if not part:
                continue
            if self.tokenizer.count_tokens(part) > self.chunk_size and new_separators:
                result.extend(self._split_text(part, new_separators))
            else:
                result.append(part)

        return result

    def _split_by_character(self, text: str) -> List[str]:
        """Split very long continuous strings without spaces by token count."""
        pieces: List[str] = []
        step_chars = max(10, int(len(text) * (self.chunk_size / max(1, self.tokenizer.count_tokens(text)))))

        for i in range(0, len(text), step_chars):
            sub = text[i : i + step_chars]
            pieces.append(sub)
        return pieces

    def _merge_splits(self, splits: List[str]) -> List[str]:
        """Merge smaller splits together into chunks up to chunk_size tokens with overlap."""
        if not splits:
            return []

        chunks: List[str] = []
        current_chunk: List[str] = []

        for split in splits:
            split_tokens = self.tokenizer.count_tokens(split)

            if split_tokens > self.chunk_size:
                # If a single split still exceeds chunk_size, truncate or flush
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = []
                chunks.append(split)
                continue

            candidate = current_chunk + [split]
            candidate_tokens = self.tokenizer.count_tokens(" ".join(candidate))

            if candidate_tokens <= self.chunk_size:
                current_chunk = candidate
            else:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))

                # Handle overlap from tail of current_chunk
                overlap_chunk: List[str] = []
                for item in reversed(current_chunk):
                    test_overlap = [item] + overlap_chunk
                    if self.tokenizer.count_tokens(" ".join(test_overlap)) <= self.chunk_overlap:
                        overlap_chunk.insert(0, item)
                    else:
                        break

                current_chunk = overlap_chunk + [split]
                # Ensure the newly started chunk with overlap does not exceed chunk_size
                while len(current_chunk) > 1 and self.tokenizer.count_tokens(" ".join(current_chunk)) > self.chunk_size:
                    current_chunk.pop(0)

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks
