"""Tests for Tasks 2.8, 2.9, and 2.10: dense, sparse, and hybrid retrieval."""

import tempfile
import unittest
from pathlib import Path

from rag_service.chunkers import Chunk
from rag_service.embeddings import E5Encoder
from rag_service.retrievers import (
    DenseRetriever,
    HybridRetriever,
    RetrievedChunk,
    SparseRetriever,
)
from rag_service.stores import BM25Manager, ChromaManager


def make_chunk(chunk_id: str, content: str, doc_id: str = "doc") -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        doc_id=doc_id,
        source_type="pdf",
        source_title="Panduan Publik",
        content=content,
        token_count=len(content.split()),
        metadata={"strategy": "fixed"},
    )


CHUNKS = [
    make_chunk(
        "c1",
        "Estimasi biaya hidup di Jepang mencakup sewa asrama tiga puluh ribu Yen per bulan.",
    ),
    make_chunk(
        "c2",
        "Persyaratan pendaftaran peserta magang meliputi ijazah SMA dan paspor yang masih berlaku.",
    ),
    make_chunk(
        "c3",
        "Program SSW Tokutei Ginou memberikan upah setara standar industri Jepang.",
    ),
]


class TestDenseRetriever(unittest.TestCase):
    """Task 2.8: cosine retrieval from the dense store."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        base = Path(self.temp_dir.name)
        self.encoder = E5Encoder()
        self.store = ChromaManager(persist_directory=base / "chroma")
        embeddings = self.encoder.embed_documents([chunk.content for chunk in CHUNKS])
        self.store.add_chunks("fixed", CHUNKS, embeddings)
        self.retriever = DenseRetriever(self.store, strategy="fixed", encoder=self.encoder)

    def test_returns_relevant_chunk(self):
        results = self.retriever.retrieve("berapa biaya asrama per bulan", top_k=2)
        self.assertTrue(results)
        self.assertEqual(results[0].chunk_id, "c1")
        self.assertGreater(results[0].score, 0.0)
        self.assertEqual(results[0].rank, 1)
        self.assertEqual(results[0].source_title, "Panduan Publik")

    def test_respects_top_k_and_empty_query(self):
        results = self.retriever.retrieve("biaya asrama", top_k=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(self.retriever.retrieve("   "), [])


class TestSparseRetriever(unittest.TestCase):
    """Task 2.9: BM25 with PySastrawi stemming and stopword removal."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        base = Path(self.temp_dir.name)
        self.store = BM25Manager(persist_directory=base / "bm25")
        self.store.build("fixed", CHUNKS)
        self.retriever = SparseRetriever(self.store, strategy="fixed")

    def test_stemmed_query_matches_derived_word(self):
        # "syarat daftar" must match "Persyaratan pendaftaran" after stemming.
        self.assertEqual(self.store.tokenize("Persyaratan pendaftaran")[:2], ["syarat", "daftar"])
        results = self.retriever.retrieve("syarat daftar magang", top_k=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].chunk_id, "c2")
        self.assertGreater(results[0].score, 0.0)

    def test_empty_query_and_missing_strategy(self):
        self.assertEqual(self.retriever.retrieve(""), [])
        other = BM25Manager(persist_directory=Path(self.temp_dir.name) / "bm25")
        self.assertEqual(other.search("recursive", "biaya", top_k=5), [])


class TestHybridRetriever(unittest.TestCase):
    """Task 2.10: pure RRF fusion, deduplication, and Top-K trimming."""

    @staticmethod
    def _chunk(chunk_id: str) -> RetrievedChunk:
        return RetrievedChunk(chunk_id=chunk_id, content=f"isi {chunk_id}", score=0.0)

    def test_rrf_formula_and_ordering(self):
        dense = [self._chunk("a"), self._chunk("b"), self._chunk("c")]
        sparse = [self._chunk("b"), self._chunk("a"), self._chunk("d")]

        fused = HybridRetriever.rrf_fuse([dense, sparse], rrf_k=60, top_k=4)
        scores = {chunk.chunk_id: chunk.score for chunk in fused}

        self.assertAlmostEqual(scores["a"], 1 / 61 + 1 / 62)
        self.assertAlmostEqual(scores["b"], 1 / 62 + 1 / 61)
        self.assertAlmostEqual(scores["c"], 1 / 63)
        self.assertAlmostEqual(scores["d"], 1 / 63)
        # Equal scores are broken deterministically by chunk_id.
        self.assertEqual([chunk.chunk_id for chunk in fused], ["a", "b", "c", "d"])
        self.assertEqual([chunk.rank for chunk in fused], [1, 2, 3, 4])

    def test_deduplicates_and_preserves_payload(self):
        dense = [self._chunk("shared"), self._chunk("only_dense")]
        sparse = [self._chunk("shared"), self._chunk("only_sparse")]

        fused = HybridRetriever.rrf_fuse([dense, sparse], rrf_k=60, top_k=5)
        ids = [chunk.chunk_id for chunk in fused]
        self.assertEqual(len(ids), len(set(ids)))
        shared = next(chunk for chunk in fused if chunk.chunk_id == "shared")
        self.assertEqual(shared.metadata["rrf_candidate_ranks"], {"dense": 1, "sparse": 1})
        self.assertEqual(shared.rank, 1)

    def test_hybrid_end_to_end_with_real_stores(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            encoder = E5Encoder()
            chroma = ChromaManager(persist_directory=base / "chroma")
            bm25 = BM25Manager(persist_directory=base / "bm25")
            chroma.add_chunks(
                "fixed", CHUNKS, encoder.embed_documents([c.content for c in CHUNKS])
            )
            bm25.build("fixed", CHUNKS)

            hybrid = HybridRetriever(
                DenseRetriever(chroma, "fixed", encoder=encoder),
                SparseRetriever(bm25, "fixed"),
                rrf_k=60,
            )
            results = hybrid.retrieve("biaya asrama Jepang", top_k=3, candidate_k=20)

            self.assertTrue(results)
            self.assertEqual(results[0].chunk_id, "c1")
            self.assertEqual(len({chunk.chunk_id for chunk in results}), len(results))
            for chunk in results:
                self.assertIn("rrf_candidate_ranks", chunk.metadata)

    def test_invalid_parameters(self):
        with self.assertRaises(ValueError):
            HybridRetriever.rrf_fuse([], rrf_k=0)
        with self.assertRaises(ValueError):
            HybridRetriever.rrf_fuse([], top_k=0)


if __name__ == "__main__":
    unittest.main()
