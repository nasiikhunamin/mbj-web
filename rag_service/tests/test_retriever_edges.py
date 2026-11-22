"""Edge-case coverage for hybrid retrieval fusion (Task 2.16)."""

import unittest

from rag_service.retrievers import HybridRetriever, RetrievedChunk


class ExplodingRetriever:
    """Fail loudly if a blank query is forwarded to a real retriever."""

    def retrieve(self, query, top_k=5):
        raise AssertionError("blank queries must not reach the stores")


class TestHybridRetrieverEdges(unittest.TestCase):
    def test_constructor_rejects_non_positive_rrf_k(self):
        with self.assertRaises(ValueError):
            HybridRetriever(None, None, rrf_k=0)

    def test_blank_query_short_circuits_both_retrievers(self):
        hybrid = HybridRetriever(ExplodingRetriever(), ExplodingRetriever())
        self.assertEqual(hybrid.retrieve("   \n\t "), [])

    def test_candidates_without_chunk_id_are_ignored(self):
        valid = RetrievedChunk(chunk_id="valid", content="isi", score=0.1)
        invalid = RetrievedChunk(chunk_id="", content="tanpa id", score=0.9)

        fused = HybridRetriever.rrf_fuse([[invalid, valid], [invalid]], top_k=5)

        self.assertEqual([chunk.chunk_id for chunk in fused], ["valid"])
        self.assertAlmostEqual(fused[0].score, 1 / 62)

    def test_empty_result_lists_return_no_chunks(self):
        self.assertEqual(HybridRetriever.rrf_fuse([[], []], top_k=5), [])


if __name__ == "__main__":
    unittest.main()
