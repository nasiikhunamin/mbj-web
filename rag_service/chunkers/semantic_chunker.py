"""Semantic chunker with similarity breakpoints and strict 512-token recursive fallback."""

import math
import re
from typing import Any, Callable, Dict, List, Optional
from rag_service.chunkers.base import BaseChunker, Chunk
from rag_service.chunkers.recursive_chunker import RecursiveCharacterChunker
from rag_service.chunkers.tokenizer import E5Tokenizer


def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def _default_bag_of_words_embed(texts: List[str]) -> List[List[float]]:
    """Lightweight deterministic character n-gram / word embedding fallback.

    Used when external dense embedding models are offline or during unit tests.
    """
    vocab: Dict[str, int] = {}
    doc_tokens: List[List[str]] = []

    for t in texts:
        words = re.findall(r"\w+", t.lower(), flags=re.UNICODE)
        doc_tokens.append(words)
        for w in words:
            if w not in vocab:
                vocab[w] = len(vocab)

    vectors: List[List[float]] = []
    vocab_size = max(1, len(vocab))

    for words in doc_tokens:
        vec = [0.0] * vocab_size
        for w in words:
            if w in vocab:
                vec[vocab[w]] += 1.0
        # Normalize
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        vectors.append([v / norm for v in vec])

    return vectors


class SemanticChunker(BaseChunker):
    """Splits text based on semantic shifts between adjacent sentences.

    If any semantic cluster exceeds chunk_size (512 E5 tokens), an automatic
    fallback recursive character split is applied to guarantee zero token overflow.
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        breakpoint_percentile_threshold: float = 85.0,
        embedding_fn: Optional[Callable[[List[str]], List[List[float]]]] = None,
        tokenizer: Optional[E5Tokenizer] = None,
    ):
        super().__init__(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            tokenizer=tokenizer,
        )
        self.breakpoint_percentile_threshold = breakpoint_percentile_threshold
        self.embedding_fn = embedding_fn or _default_bag_of_words_embed
        self._fallback_recursive = RecursiveCharacterChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            tokenizer=self.tokenizer,
        )

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences preserving punctuation."""
        raw_sentences = re.split(r"(?<=[.!?\n])\s+", text)
        sentences = [s.strip() for s in raw_sentences if s.strip()]
        return sentences

    def chunk_text(
        self,
        text: str,
        doc_id: str = "doc",
        source_type: str = "text",
        source_title: str = "Untitled",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Chunk]:
        """Split text semantically with strict token limits."""
        text = text.strip()
        if not text:
            return []

        metadata = dict(metadata or {})
        total_tokens = self.tokenizer.count_tokens(text)

        # Quick return if already within chunk size
        if total_tokens <= self.chunk_size:
            return [
                Chunk(
                    chunk_id=f"{doc_id}_sem_0000",
                    doc_id=doc_id,
                    source_type=source_type,
                    source_title=source_title,
                    content=text,
                    token_count=total_tokens,
                    start_char=0,
                    end_char=len(text),
                    metadata={**metadata, "chunk_index": 0, "strategy": "semantic"},
                )
            ]

        sentences = self._split_into_sentences(text)
        if len(sentences) <= 1:
            # Fallback to recursive splitter directly
            return self._fallback_recursive.chunk_text(
                text=text,
                doc_id=doc_id,
                source_type=source_type,
                source_title=source_title,
                metadata={**metadata, "fallback_applied": True},
            )

        # Compute embeddings for sentences
        embeddings = self.embedding_fn(sentences)

        # Compute cosine distances between adjacent sentences (distance = 1 - similarity)
        distances: List[float] = []
        for i in range(len(embeddings) - 1):
            sim = _cosine_similarity(embeddings[i], embeddings[i + 1])
            distances.append(1.0 - sim)

        # Calculate threshold distance based on percentile
        threshold = self._compute_threshold(distances)

        # Group sentences into clusters
        clusters: List[List[str]] = []
        current_cluster: List[str] = [sentences[0]]

        for i, dist in enumerate(distances):
            if dist > threshold:
                # Semantic boundary detected
                clusters.append(current_cluster)
                current_cluster = [sentences[i + 1]]
            else:
                current_cluster.append(sentences[i + 1])

        if current_cluster:
            clusters.append(current_cluster)

        # Final pass: inspect each cluster, applying recursive fallback if > 512 tokens
        final_chunks: List[Chunk] = []
        chunk_idx = 0

        for cluster in clusters:
            cluster_text = " ".join(cluster).strip()
            cluster_tokens = self.tokenizer.count_tokens(cluster_text)

            if cluster_tokens <= self.chunk_size:
                start_char = text.find(cluster_text[:30])
                if start_char == -1:
                    start_char = 0
                end_char = start_char + len(cluster_text)

                final_chunks.append(
                    Chunk(
                        chunk_id=f"{doc_id}_sem_{chunk_idx:04d}",
                        doc_id=doc_id,
                        source_type=source_type,
                        source_title=source_title,
                        content=cluster_text,
                        token_count=cluster_tokens,
                        start_char=start_char,
                        end_char=end_char,
                        metadata={**metadata, "chunk_index": chunk_idx, "strategy": "semantic"},
                    )
                )
                chunk_idx += 1
            else:
                # Critical requirement: cluster exceeded 512 tokens -> fallback recursive split
                sub_chunks = self._fallback_recursive.chunk_text(
                    text=cluster_text,
                    doc_id=f"{doc_id}_sub",
                    source_type=source_type,
                    source_title=source_title,
                    metadata={**metadata, "fallback_applied": True},
                )
                for sc in sub_chunks:
                    sc.chunk_id = f"{doc_id}_sem_{chunk_idx:04d}"
                    sc.metadata["chunk_index"] = chunk_idx
                    sc.metadata["strategy"] = "semantic_fallback"
                    final_chunks.append(sc)
                    chunk_idx += 1

        return final_chunks

    def _compute_threshold(self, distances: List[float]) -> float:
        """Compute the distance threshold based on the specified percentile."""
        if not distances:
            return 0.5
        sorted_d = sorted(distances)
        index = int(len(sorted_d) * (self.breakpoint_percentile_threshold / 100.0))
        index = min(max(0, index), len(sorted_d) - 1)
        return sorted_d[index]
