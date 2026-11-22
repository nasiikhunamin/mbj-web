"""Tests for Task 2.7: four dense collections and four BM25 indices."""

import json
import tempfile
import unittest
from pathlib import Path

from rag_service.embeddings import E5Encoder
from rag_service.stores import BM25Manager, ChromaManager, build_indexes, load_corpus
from rag_service.stores.index_builder import STRATEGIES

DOCUMENTS = [
    {
        "doc_id": "faq_publik",
        "source_type": "web",
        "title": "FAQ Publik",
        "content_type": "qa_pairs",
        "clean_text": (
            "Pertanyaan 1: Berapa biaya asrama?\nJawaban: Biaya asrama sekitar tiga puluh ribu Yen per bulan.\n\n"
            "Pertanyaan 2: Apakah wajib lulus JLPT?\nJawaban: Peserta minimal memiliki sertifikat N5 atau JFT Basic."
        ),
        "metadata": {"section": "faq"},
    },
    {
        "doc_id": "panduan_pdf",
        "source_type": "pdf",
        "title": "Panduan Pendaftaran Publik",
        "content_type": "numeric",
        "clean_text": (
            "Pendaftaran magang memerlukan ijazah SMA, paspor, dan surat izin orang tua.\n"
            "Peserta mengikuti tes kesehatan dan wawancara sebelum keberangkatan."
        ),
        "tables": [
            {
                "caption": "Rincian Biaya",
                "markdown_table": "| Komponen | Nominal |\n|---|---|\n| Asrama | ¥30,000 |\n| Makan | ¥20,000 |",
            }
        ],
        "metadata": {"pages": 2},
    },
    {
        "doc_id": "silabus_docx",
        "source_type": "docx",
        "title": "Silabus Pelatihan",
        "content_type": "curriculum",
        "clean_text": "",
        "sections": [
            {
                "heading": "Modul Bahasa Jepang N5",
                "text": "Pelatihan hiragana, katakana, dan percakapan dasar selama tiga bulan.",
            },
            {
                "heading": "Modul Budaya Kerja",
                "text": "Peserta mempelajari etika kerja, keselamatan, dan disiplin industri Jepang.",
            },
        ],
        "metadata": {"author": "LPK MBJ"},
    },
]


class TestDualStorageIndexing(unittest.TestCase):
    """Verify that indexing produces exactly four dense and four sparse stores."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.base = Path(self.temp_dir.name)

    def test_builds_four_dense_and_four_sparse_indices(self):
        report = build_indexes(
            DOCUMENTS,
            vectordb_directory=self.base / "vectordb",
            encoder=E5Encoder(),
        )

        self.assertEqual(set(report["strategies"]), set(STRATEGIES))
        for strategy in STRATEGIES:
            stats = report["strategies"][strategy]
            self.assertGreater(stats["chunks"], 0)
            self.assertEqual(stats["dense_count"], stats["chunks"])
            self.assertEqual(stats["sparse_count"], stats["chunks"])

        bm25_files = sorted((self.base / "vectordb" / "bm25").glob("bm25_*.json"))
        self.assertEqual([path.stem for path in bm25_files], [f"bm25_{s}" for s in STRATEGIES])

        chroma = ChromaManager(persist_directory=self.base / "vectordb" / "chroma")
        for strategy in STRATEGIES:
            self.assertEqual(chroma.collection_name(strategy), f"chroma_{strategy}")
            self.assertEqual(chroma.count(strategy), report["strategies"][strategy]["chunks"])
            if chroma.backend == "json_fallback":
                self.assertTrue(
                    (self.base / "vectordb" / "chroma" / f"chroma_{strategy}.json").exists()
                )

    def test_rebuild_resets_without_duplicates(self):
        first = build_indexes(
            DOCUMENTS,
            vectordb_directory=self.base / "vectordb",
            encoder=E5Encoder(),
        )
        second = build_indexes(
            DOCUMENTS,
            vectordb_directory=self.base / "vectordb",
            encoder=E5Encoder(),
        )
        self.assertEqual(first["strategies"], second["strategies"])

    def test_dense_and_sparse_searches_work_after_reload(self):
        build_indexes(
            DOCUMENTS,
            vectordb_directory=self.base / "vectordb",
            encoder=E5Encoder(),
        )

        bm25 = BM25Manager(persist_directory=self.base / "vectordb" / "bm25")
        results = bm25.search("fixed", "biaya asrama", top_k=3)
        self.assertTrue(results)
        self.assertIn("asrama", results[0]["content"].lower())

        chroma = ChromaManager(persist_directory=self.base / "vectordb" / "chroma")
        self.assertGreater(chroma.count("structure_aware"), 0)

    def test_retrieval_method_does_not_create_collections(self):
        build_indexes(
            DOCUMENTS,
            vectordb_directory=self.base / "vectordb",
            encoder=E5Encoder(),
        )
        chroma = ChromaManager(persist_directory=self.base / "vectordb" / "chroma")
        before = {strategy: chroma.count(strategy) for strategy in STRATEGIES}

        # Querying each collection must not create additional collections.
        encoder = E5Encoder()
        for strategy in STRATEGIES:
            chroma.query(strategy, encoder.embed_query("biaya asrama"), top_k=2)

        after = {strategy: chroma.count(strategy) for strategy in STRATEGIES}
        self.assertEqual(before, after)
        self.assertEqual(len(STRATEGIES), 4)


class TestCorpusLoader(unittest.TestCase):
    """Verify canonical JSON loading for single docs, lists, and wrapped payloads."""

    def test_loads_supported_shapes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            corpus = Path(temp_dir)
            (corpus / "single.json").write_text(json.dumps(DOCUMENTS[0]), encoding="utf-8")
            (corpus / "list.json").write_text(json.dumps(DOCUMENTS[1:2]), encoding="utf-8")
            (corpus / "wrapped.json").write_text(
                json.dumps({"documents": [DOCUMENTS[2]]}), encoding="utf-8"
            )
            (corpus / "metadata.json").write_text(json.dumps({"ignored": True}), encoding="utf-8")

            documents = load_corpus(corpus)
            self.assertEqual(len(documents), 3)
            self.assertEqual(
                {document["doc_id"] for document in documents},
                {"faq_publik", "panduan_pdf", "silabus_docx"},
            )


if __name__ == "__main__":
    unittest.main()
