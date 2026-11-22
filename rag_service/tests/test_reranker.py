"""Tests for Task 2.11: multilingual cross-encoder reranker."""

import unittest

from rag_service.rerankers import BGEReranker
from rag_service.retrievers import RetrievedChunk


def make_candidate(chunk_id: str, content: str, rank: int = 0) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        content=content,
        score=0.1,
        doc_id="doc",
        source_type="pdf",
        source_title="Panduan Publik",
        token_count=len(content.split()),
        metadata={"strategy": "fixed"},
        rank=rank,
    )


class TestBGEReranker(unittest.TestCase):
    """Verify Top-N trimming, ordering, payload preservation, and fallback scoring."""

    def setUp(self):
        self.reranker = BGEReranker(top_n=5, allow_fallback=True)

    def test_relevant_candidate_ranked_first(self):
        candidates = [
            make_candidate("visa", "Prosedur pengajuan visa dan Certificate of Eligibility."),
            make_candidate(
                "biaya",
                "Estimasi biaya asrama sekitar tiga puluh ribu Yen per bulan.",
            ),
            make_candidate("ssw", "Program SSW memberikan upah setara standar industri Jepang."),
        ]

        results = self.reranker.rerank("berapa biaya asrama per bulan", candidates)
        self.assertTrue(results)
        self.assertEqual(results[0].chunk_id, "biaya")
        self.assertEqual(
            [chunk.rank for chunk in results],
            list(range(1, len(results) + 1)),
        )

    def test_top_20_to_top_5(self):
        candidates = [
            make_candidate(f"irrelevant_{index}", f"Topik lain nomor {index} tentang budaya kerja.")
            for index in range(19)
        ]
        candidates.append(
            make_candidate(
                "relevant",
                "Biaya asrama dan biaya makan peserta magang di Jepang.",
            )
        )

        results = self.reranker.rerank("biaya asrama", candidates)
        self.assertEqual(len(results), 5)
        self.assertEqual(results[0].chunk_id, "relevant")
        scores = [chunk.score for chunk in results]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_custom_top_n_override(self):
        candidates = [make_candidate(f"c{index}", f"konten {index}") for index in range(10)]
        self.assertEqual(len(self.reranker.rerank("konten", candidates, top_n=3)), 3)

    def test_preserves_payload_and_adds_rerank_metadata(self):
        candidate = make_candidate("c1", "Informasi biaya asrama.", rank=4)
        result = self.reranker.rerank("biaya asrama", [candidate])[0]

        self.assertEqual(result.chunk_id, "c1")
        self.assertEqual(result.doc_id, "doc")
        self.assertEqual(result.source_type, "pdf")
        self.assertEqual(result.source_title, "Panduan Publik")
        self.assertEqual(result.metadata["strategy"], "fixed")
        self.assertEqual(result.metadata["pre_rerank_rank"], 4)
        self.assertIn("rerank_score", result.metadata)
        self.assertIn("rerank_backend", result.metadata)
        self.assertEqual(result.metadata["rerank_model"], "BAAI/bge-reranker-v2-m3")

    def test_accepts_plain_store_records(self):
        records = [
            {
                "chunk_id": "dict_candidate",
                "content": "Syarat usia peserta minimal delapan belas tahun.",
                "score": 0.2,
                "doc_id": "panduan",
                "source_type": "docx",
                "source_title": "Panduan",
                "metadata": {"strategy": "recursive"},
            }
        ]
        results = self.reranker.rerank("syarat usia", records)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].chunk_id, "dict_candidate")

    def test_empty_inputs(self):
        self.assertEqual(self.reranker.rerank("", [make_candidate("c1", "isi")]), [])
        self.assertEqual(self.reranker.rerank("biaya", []), [])

    def test_invalid_parameters(self):
        with self.assertRaises(ValueError):
            BGEReranker(top_n=0)
        with self.assertRaises(ValueError):
            self.reranker.rerank("biaya", [make_candidate("c1", "isi")], top_n=0)

    def test_fallback_is_deterministic(self):
        candidates = [make_candidate("c1", "Biaya asrama tiga puluh ribu Yen.")]

        def forced_fallback() -> BGEReranker:
            reranker = BGEReranker(allow_fallback=True)
            reranker._load_attempted = True
            reranker._model = None
            return reranker

        first = forced_fallback().rerank("biaya asrama", candidates)[0].score
        second = forced_fallback().rerank("biaya asrama", candidates)[0].score
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
