"""Unit tests for RAG Chunker suite (Tasks 2.2, 2.3, 2.4, 2.5)."""

import unittest
from rag_service.chunkers import (
    Chunk,
    E5Tokenizer,
    FixedSizeChunker,
    RecursiveCharacterChunker,
    SemanticChunker,
    StructureAwareChunker,
)


class TestE5Tokenizer(unittest.TestCase):
    """Test token counter and encoding utilities."""

    def setUp(self):
        self.tokenizer = E5Tokenizer()

    def test_empty_string(self):
        self.assertEqual(self.tokenizer.count_tokens(""), 0)
        self.assertEqual(self.tokenizer.encode(""), [])

    def test_token_counting(self):
        text = "LPK Matahari Bulan Jepang Indonesia menyelenggarakan pelatihan bahasa Jepang."
        count = self.tokenizer.count_tokens(text)
        self.assertGreater(count, 5)

    def test_token_truncation(self):
        text = "Satu dua tiga empat lima enam tujuh delapan sembilan sepuluh."
        truncated = self.tokenizer.truncate_tokens(text, max_tokens=4)
        self.assertLessEqual(self.tokenizer.count_tokens(truncated), 4)


class TestFixedSizeChunker(unittest.TestCase):
    """Test Task 2.2: Fixed-Size Chunker."""

    def setUp(self):
        self.tokenizer = E5Tokenizer()
        self.chunker = FixedSizeChunker(chunk_size=50, chunk_overlap=10, tokenizer=self.tokenizer)

    def test_empty_text(self):
        chunks = self.chunker.chunk_text("", doc_id="test")
        self.assertEqual(len(chunks), 0)

    def test_short_text_single_chunk(self):
        text = "Ini adalah contoh teks pendek yang kurang dari lima puluh token."
        chunks = self.chunker.chunk_text(text, doc_id="doc_short", source_type="web", source_title="Short Doc")
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].chunk_id, "doc_short_fix_0000")
        self.assertEqual(chunks[0].source_type, "web")
        self.assertLessEqual(chunks[0].token_count, 50)

    def test_long_text_split_and_overlap(self):
        # Generate text > 150 tokens
        words = ["Program", "pemagangan", "ke", "Jepang", "memerlukan", "sertifikat", "kompetensi", "dan", "bahasa"] * 25
        long_text = " ".join(words)
        chunks = self.chunker.chunk_text(long_text, doc_id="doc_long")

        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(chunk.token_count, 50)
            self.assertTrue(chunk.chunk_id.startswith("doc_long_fix_"))
            self.assertEqual(chunk.metadata["strategy"], "fixed")


class TestRecursiveCharacterChunker(unittest.TestCase):
    """Test Task 2.3: Recursive Character Chunker."""

    def setUp(self):
        self.tokenizer = E5Tokenizer()
        self.chunker = RecursiveCharacterChunker(chunk_size=60, chunk_overlap=10, tokenizer=self.tokenizer)

    def test_respects_paragraph_boundary(self):
        p1 = "Paragraf pertama menjelaskan visi dan misi lembaga pelatihan kerja ke Jepang secara lengkap."
        p2 = "Paragraf kedua menjelaskan alur pendaftaran peserta mulai dari wawancara hingga medical check up."
        full_text = f"{p1}\n\n{p2}"

        chunks = self.chunker.chunk_text(full_text, doc_id="p_test")
        self.assertGreaterEqual(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(chunk.token_count, 60)
            self.assertTrue(chunk.chunk_id.startswith("p_test_rec_"))

    def test_strictly_bounds_token_size(self):
        large_text = ("Pelatihan bahasa Jepang intensif level N5 dan N4 di LPK MBJ Indonesia. " * 30).strip()
        chunks = self.chunker.chunk_text(large_text, doc_id="large_doc")
        self.assertGreater(len(chunks), 2)
        for chunk in chunks:
            self.assertLessEqual(chunk.token_count, 60)


class TestSemanticChunker(unittest.TestCase):
    """Test Task 2.4: Semantic Chunker with fallback recursive splitting."""

    def setUp(self):
        self.tokenizer = E5Tokenizer()
        self.chunker = SemanticChunker(
            chunk_size=50,
            chunk_overlap=10,
            breakpoint_percentile_threshold=70.0,
            tokenizer=self.tokenizer,
        )

    def test_detects_topic_shifts(self):
        topic_a = "Biaya hidup di Tokyo Jepang mencakup sewa apartemen sekitar 50000 Yen per bulan. Biaya makan harian di supermarket berkisar 20000 Yen."
        topic_b = "Alur pendaftaran magang meliputi tes kesehatan fisik dan wawancara dengan perusahaan penerima. Paspor dan visa CoE diproses setelah dinyatakan lulus."
        combined = f"{topic_a} {topic_b}"

        chunks = self.chunker.chunk_text(combined, doc_id="sem_test")
        self.assertGreaterEqual(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(chunk.token_count, 50)
            self.assertTrue(chunk.chunk_id.startswith("sem_test_sem_"))

    def test_semantic_fallback_when_cluster_exceeds_limit(self):
        # A repetitive single-topic paragraph that exceeds 50 tokens
        repetitive_topic = ("Biaya sewa asrama di prefektur Saitama adalah tiga puluh ribu Yen per bulan. " * 15)
        chunks = self.chunker.chunk_text(repetitive_topic, doc_id="sem_overflow")

        # Must have split safely via fallback
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(chunk.token_count, 50)


class TestStructureAwareChunker(unittest.TestCase):
    """Test Task 2.5: Structure-Aware Chunker on multi-format documents."""

    def setUp(self):
        self.tokenizer = E5Tokenizer()
        self.chunker = StructureAwareChunker(chunk_size=60, chunk_overlap=10, tokenizer=self.tokenizer)

    def test_web_qa_preservation(self):
        qa_doc = {
            "doc_id": "faq_web",
            "source_type": "web",
            "title": "FAQ Komunitas",
            "content_type": "qa_pairs",
            "clean_text": "Pertanyaan 1: Berapa batas usia peserta magang?\nJawaban: Usia peserta minimal 18 tahun dan maksimal 30 tahun.\n\nPertanyaan 2: Apakah ada pelatihan bahasa Jepang?\nJawaban: Ya, peserta mendapatkan pelatihan intensif bahasa Jepang level N5 dan N4.",
            "metadata": {"section": "komunitas"},
        }
        chunks = self.chunker.chunk_document(qa_doc)
        self.assertGreaterEqual(len(chunks), 2)
        # Verify Question and Answer are preserved in the chunk
        self.assertIn("Pertanyaan 1:", chunks[0].content)
        self.assertIn("Jawaban:", chunks[0].content)
        for chunk in chunks:
            self.assertLessEqual(chunk.token_count, 60)

    def test_docx_heading_hierarchy(self):
        docx_doc = {
            "doc_id": "silabus_doc",
            "source_type": "docx",
            "title": "Silabus Pelatihan",
            "content_type": "curriculum",
            "clean_text": "",
            "sections": [
                {
                    "heading": "Modul 1: Pengenalan Huruf Hiragana & Katakana",
                    "text": "Materi mencakup pengenalan 46 karakter dasar serta cara penulisan stroke order yang tepat.",
                },
                {
                    "heading": "Modul 2: Percakapan Bahasa Jepang Sehari-hari",
                    "text": "Latihan percakapan salam perkenalan aisatsu dan komunikasi dasar di lingkungan kerja.",
                },
            ],
            "metadata": {"author": "Sensei MBJ"},
        }
        chunks = self.chunker.chunk_document(docx_doc)
        self.assertEqual(len(chunks), 2)
        self.assertIn("Modul 1:", chunks[0].content)
        self.assertIn("Modul 2:", chunks[1].content)
        for chunk in chunks:
            self.assertLessEqual(chunk.token_count, 60)

    def test_pdf_table_isolation(self):
        pdf_doc = {
            "doc_id": "biaya_pdf",
            "source_type": "pdf",
            "title": "Panduan Rincian Biaya",
            "content_type": "numeric",
            "clean_text": "Berikut adalah estimasi biaya hidup bulanan peserta magang di Jepang.",
            "tables": [
                {
                    "caption": "Tabel Biaya Hidup",
                    "markdown_table": "| Komponen | Nominal |\n|---|---|\n| Asrama | ¥20,000 |\n| Makan | ¥25,000 |\n| Utilitas | ¥10,000 |",
                }
            ],
            "metadata": {"pages": 2},
        }
        chunks = self.chunker.chunk_document(pdf_doc)
        self.assertGreaterEqual(len(chunks), 2)
        # Check table isolation
        table_chunk = next(c for c in chunks if "Tabel Biaya Hidup" in c.content)
        self.assertIn("| Komponen | Nominal |", table_chunk.content)
        self.assertIn("¥20,000", table_chunk.content)
        for chunk in chunks:
            self.assertLessEqual(chunk.token_count, 60)


if __name__ == "__main__":
    unittest.main()
