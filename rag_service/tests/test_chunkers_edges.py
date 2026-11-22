"""Edge-case coverage for chunkers and the E5 tokenizer (Task 2.16)."""

import re
import unittest
from unittest import mock

from rag_service.chunkers import (
    E5Tokenizer,
    FixedSizeChunker,
    RecursiveCharacterChunker,
    SemanticChunker,
    StructureAwareChunker,
)
from rag_service.chunkers import tokenizer as tokenizer_module
from rag_service.chunkers.semantic_chunker import (
    _cosine_similarity,
    _default_bag_of_words_embed,
)


class FakeHFTokenizer:
    """Minimal HuggingFace-tokenizer lookalike (no model download)."""

    def encode(self, text, add_special_tokens=False):
        return [10 + index for index, _ in enumerate(text.split())]

    def decode(self, token_ids, skip_special_tokens=True):
        return "|".join(str(token_id) for token_id in token_ids)


class CharTokenizer:
    """Offline tokenizer where one token equals one character."""

    _hf_tokenizer = None

    def count_tokens(self, text):
        return len(text)


class RegexTokenizer:
    """Offline tokenizer matching the E5Tokenizer fallback regex."""

    _hf_tokenizer = None

    def count_tokens(self, text):
        return len(re.findall(r"\w+|[^\w\s]|\s+", text, flags=re.UNICODE))


class WordTokenizer:
    """Cheap word counter for semantic tests."""

    _hf_tokenizer = None

    def count_tokens(self, text):
        return len(re.findall(r"\w+", text))


class TestE5TokenizerEdges(unittest.TestCase):
    """Tokenizer fallback and HuggingFace branches without downloading a model."""

    def test_hf_branch_count_encode_decode_and_truncate(self):
        tokenizer = E5Tokenizer()
        tokenizer._hf_tokenizer = FakeHFTokenizer()

        self.assertEqual(tokenizer.count_tokens("dua kata"), 2)
        self.assertEqual(tokenizer.encode("satu dua tiga"), [10, 11, 12])
        self.assertEqual(tokenizer.decode([10, 11]), "10|11")
        self.assertEqual(tokenizer.truncate_tokens("satu dua tiga", max_tokens=2), "10|11")

    def test_offline_fallback_branches(self):
        tokenizer = E5Tokenizer()
        tokenizer._hf_tokenizer = None

        self.assertGreater(tokenizer.count_tokens("satu dua"), 0)
        self.assertEqual(len(tokenizer.encode("satu dua")), 3)
        self.assertEqual(tokenizer.decode([1, 2, 3]), "[Decoded 3 tokens]")
        self.assertEqual(tokenizer.decode([]), "")
        self.assertEqual(
            tokenizer.truncate_tokens("satu dua tiga empat", max_tokens=2),
            "satu ",
        )
        self.assertEqual(tokenizer.truncate_tokens("pendek", max_tokens=20), "pendek")

    def test_tokenizer_load_failure_falls_back_cleanly(self):
        with mock.patch.object(
            tokenizer_module.AutoTokenizer, "from_pretrained"
        ) as from_pretrained:
            from_pretrained.side_effect = OSError("model not cached")
            tokenizer = E5Tokenizer("missing-model")

        self.assertIsNone(tokenizer._hf_tokenizer)
        self.assertGreater(tokenizer.count_tokens("teks cadangan"), 0)

    def test_missing_transformers_is_tolerated(self):
        with mock.patch.object(tokenizer_module, "HAS_TRANSFORMERS", False):
            tokenizer = E5Tokenizer("missing-model")

        self.assertIsNone(tokenizer._hf_tokenizer)


class TestBaseChunkerValidation(unittest.TestCase):
    """All chunkers must reject impossible window settings."""

    def test_invalid_window_settings(self):
        for kwargs in (
            {"chunk_size": 0},
            {"chunk_size": -1},
            {"chunk_size": 10, "chunk_overlap": -1},
            {"chunk_size": 10, "chunk_overlap": 10},
            {"chunk_size": 10, "chunk_overlap": 11},
        ):
            with self.assertRaises(ValueError, msg=kwargs):
                FixedSizeChunker(**kwargs)


class TestFixedChunkerFallback(unittest.TestCase):
    """The regex fallback keeps the service usable without a cached HF model."""

    def test_sliding_window_without_hf_tokenizer(self):
        chunker = FixedSizeChunker(
            chunk_size=12, chunk_overlap=3, tokenizer=RegexTokenizer()
        )
        text = " ".join(["pelatihan", "bahasa", "jepang", "level", "n5"] * 8)

        chunks = chunker.chunk_text(
            text, doc_id="fallback", metadata={"origin": "test"}
        )

        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(chunk.token_count, 12)
            self.assertEqual(chunk.metadata["origin"], "test")

    def test_metadata_is_preserved_on_single_chunk(self):
        chunker = FixedSizeChunker(chunk_size=100, tokenizer=RegexTokenizer())
        chunks = chunker.chunk_text(
            "Teks pendek.", doc_id="one", metadata={"content_type": "narrative"}
        )

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].metadata["content_type"], "narrative")
        self.assertEqual(chunks[0].metadata["chunk_index"], 0)


class TestRecursiveChunkerEdges(unittest.TestCase):
    """Recursive splitting, overlap, and impossible-separator fallbacks."""

    def test_split_empty_text(self):
        chunker = RecursiveCharacterChunker(
            chunk_size=10, chunk_overlap=0, tokenizer=CharTokenizer()
        )
        self.assertEqual(chunker._split_text("", []), [])

    def test_character_split_when_no_separator_exists(self):
        chunker = RecursiveCharacterChunker(
            chunk_size=10, chunk_overlap=2, tokenizer=CharTokenizer()
        )
        chunks = chunker.chunk_text("A" * 45, doc_id="chars")

        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(chunk.token_count, 10)

    def test_oversized_word_is_split_recursively(self):
        chunker = RecursiveCharacterChunker(
            chunk_size=10, chunk_overlap=0, tokenizer=CharTokenizer()
        )
        text = f"{'a' * 25} {'b' * 25}"

        chunks = chunker.chunk_text(text, doc_id="long_words")

        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(chunk.token_count, 10)

    def test_merge_flushes_before_oversized_split(self):
        chunker = RecursiveCharacterChunker(
            chunk_size=10, chunk_overlap=2, tokenizer=CharTokenizer()
        )
        merged = chunker._merge_splits(["aa", "b" * 15, "cc"])

        self.assertEqual(merged[0], "aa")
        self.assertEqual(merged[1], "b" * 15)

    def test_overlap_is_trimmed_when_it_exceeds_chunk_size(self):
        chunker = RecursiveCharacterChunker(
            chunk_size=10, chunk_overlap=8, tokenizer=CharTokenizer()
        )
        merged = chunker._merge_splits(["aa", "bb", "cc", "dd", "ee"])

        for piece in merged:
            self.assertLessEqual(chunker.tokenizer.count_tokens(piece), 10)
        self.assertTrue(merged)

    def test_blank_piece_and_missing_offset_are_handled(self):
        chunker = RecursiveCharacterChunker(
            chunk_size=20, chunk_overlap=0, tokenizer=CharTokenizer()
        )
        with mock.patch.object(chunker, "_merge_splits", return_value=["", "tidak ada"]):
            chunks = chunker.chunk_text("teks asli", doc_id="offset")

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].content, "tidak ada")
        self.assertEqual(chunks[0].start_char, 0)


class TestSemanticChunkerEdges(unittest.TestCase):
    """Normal clustering plus fallbacks that are not exercised by the main suite."""

    def test_cosine_similarity_zero_vectors(self):
        self.assertEqual(_cosine_similarity([0.0, 0.0], [1.0, 2.0]), 0.0)
        self.assertEqual(_cosine_similarity([], []), 0.0)

    def test_default_bag_of_words_embedding_is_normalized(self):
        vectors = _default_bag_of_words_embed(
            ["biaya asrama", "biaya asrama", "program ssw"]
        )

        self.assertEqual(len(vectors), 3)
        for vector in vectors:
            norm = sum(value * value for value in vector) ** 0.5
            self.assertAlmostEqual(norm, 1.0)

    def test_threshold_without_distances(self):
        chunker = SemanticChunker(
            chunk_size=10, chunk_overlap=0, tokenizer=WordTokenizer()
        )
        self.assertEqual(chunker._compute_threshold([]), 0.5)

    def test_single_sentence_over_limit_uses_recursive_fallback(self):
        chunker = SemanticChunker(
            chunk_size=10, chunk_overlap=2, tokenizer=CharTokenizer()
        )
        chunks = chunker.chunk_text("A" * 40, doc_id="one_sentence")

        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(chunk.token_count, 10)

    def test_small_clusters_take_the_normal_path(self):
        sentences = (
            "satu dua tiga. empat lima enam. tujuh delapan sembilan. "
            "sepuluh sebelas dua belas."
        )
        chunker = SemanticChunker(
            chunk_size=8,
            chunk_overlap=0,
            breakpoint_percentile_threshold=50.0,
            embedding_fn=lambda _: [[1.0, 0.0], [1.0, 0.0], [0.0, 1.0], [0.0, 1.0]],
            tokenizer=WordTokenizer(),
        )

        chunks = chunker.chunk_text(sentences, doc_id="clusters")

        self.assertEqual(len(chunks), 2)
        self.assertIn("satu dua tiga", chunks[0].content)
        self.assertIn("tujuh delapan sembilan", chunks[1].content)
        self.assertEqual(
            [chunk.metadata["strategy"] for chunk in chunks],
            ["semantic", "semantic"],
        )
        for chunk in chunks:
            self.assertLessEqual(chunk.token_count, 8)


class TestStructureAwareChunkerEdges(unittest.TestCase):
    """Web/DOCX/PDF branches and oversized structural units."""

    def test_empty_text_returns_no_chunks(self):
        chunker = StructureAwareChunker(
            chunk_size=50, chunk_overlap=0, tokenizer=WordTokenizer()
        )
        self.assertEqual(chunker.chunk_text("   \n "), [])

    def test_generic_source_uses_structured_text_fallback(self):
        chunker = StructureAwareChunker(
            chunk_size=50, chunk_overlap=0, tokenizer=WordTokenizer()
        )
        chunks = chunker.chunk_document(
            {
                "doc_id": "misc",
                "source_type": "txt",
                "title": "Catatan",
                "clean_text": "# Bagian A\nIsi bagian A.\n\n# Bagian B\nIsi bagian B.",
            }
        )

        self.assertEqual(len(chunks), 2)
        self.assertTrue(all(chunk.source_type == "txt" for chunk in chunks))

    def test_text_fallback_splits_qa_and_plain_paragraphs(self):
        chunker = StructureAwareChunker(
            chunk_size=50, chunk_overlap=0, tokenizer=WordTokenizer()
        )

        qa_chunks = chunker.chunk_text(
            "Pertanyaan: Apa syarat?\nJawaban: Lulus SMA.\n\n"
            "Pertanyaan: Berapa biaya?\nJawaban: Tiga puluh ribu Yen.",
            doc_id="qa",
            metadata={"content_type": "qa_pairs"},
        )
        plain_chunks = chunker.chunk_text(
            "Paragraf pertama.\n\nParagraf kedua.", doc_id="plain"
        )

        self.assertGreaterEqual(len(qa_chunks), 2)
        self.assertEqual(len(plain_chunks), 2)
        self.assertEqual(qa_chunks[0].metadata["structure"], "qa_pair")

    def test_web_procedural_steps_are_grouped(self):
        chunker = StructureAwareChunker(chunk_size=80, tokenizer=WordTokenizer())
        text = (
            "Langkah 1 mengisi formulir pendaftaran.\n"
            "Langkah 2 melengkapi berkas administrasi.\n"
            "Langkah 3 mengikuti tes kesehatan."
        )

        chunks = chunker.chunk_document(
            {
                "doc_id": "alur_pendaftaran",
                "source_type": "web",
                "title": "Alur Pendaftaran",
                "content_type": "procedural",
                "clean_text": text,
            }
        )

        self.assertEqual(len(chunks), 2)
        self.assertEqual(
            chunks[0].metadata["structure"], "procedural_grouped"
        )
        self.assertIn("Langkah 1", chunks[0].content)
        self.assertIn("Langkah 2", chunks[0].content)
        self.assertIn("Langkah 3", chunks[1].content)

    def test_web_default_blocks_and_faq_detection(self):
        chunker = StructureAwareChunker(chunk_size=80, tokenizer=WordTokenizer())

        blocks = chunker.chunk_document(
            {
                "doc_id": "profil",
                "source_type": "web",
                "title": "Profil LPK",
                "content_type": "narrative",
                "clean_text": "Blok pertama profil lembaga.\n\nBlok kedua visi misi.",
            }
        )
        faq = chunker.chunk_document(
            {
                "doc_id": "faq_page",
                "source_type": "web",
                "title": "FAQ",
                "clean_text": "Pertanyaan 1: Apa itu SSW?\nJawaban: Pekerja terampil.",
            }
        )

        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0].metadata["structure_type"], "web_block")
        self.assertEqual(faq[0].metadata["structure_type"], "qa_item")

    def test_docx_without_sections_splits_on_markdown_headings(self):
        chunker = StructureAwareChunker(chunk_size=80, tokenizer=WordTokenizer())
        chunks = chunker.chunk_document(
            {
                "doc_id": "docx_plain",
                "source_type": "docx",
                "title": "Silabus",
                "clean_text": "# Modul 1\nMateri dasar.\n\n# Modul 2\nMateri lanjutan.",
            }
        )

        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0].metadata["structure_type"], "docx_block")

    def test_pdf_page_breaks_become_separate_units(self):
        chunker = StructureAwareChunker(chunk_size=80, tokenizer=WordTokenizer())
        chunks = chunker.chunk_document(
            {
                "doc_id": "pdf_pages",
                "source_type": "pdf",
                "title": "Brosur",
                "clean_text": (
                    "--- Page 1 ---\nProfil lembaga LPK MBJ.\n"
                    "--- Page 2 ---\nSyarat pendaftaran peserta."
                ),
                "tables": [{"caption": "Tanpa isi", "markdown_table": ""}],
            }
        )

        self.assertGreaterEqual(len(chunks), 2)
        self.assertEqual(chunks[0].metadata["structure_type"], "pdf_section")

    def test_qa_text_handles_an_empty_payload(self):
        chunker = StructureAwareChunker(chunk_size=80, tokenizer=WordTokenizer())
        chunks = chunker._chunk_qa_text(
            "",
            "qa_fallback",
            "web",
            "FAQ",
            {},
        )

        self.assertEqual(chunks, [])

    def test_blank_units_are_skipped(self):
        chunker = StructureAwareChunker(chunk_size=80, tokenizer=WordTokenizer())
        chunks = chunker._pack_units_into_chunks(
            units=["", "   ", "Isi valid."],
            doc_id="blank_units",
            source_type="web",
            source_title="Blank",
            metadata={},
            structure_tag="web_block",
        )

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].content, "Isi valid.")

    def test_oversized_unit_uses_recursive_fallback(self):
        chunker = StructureAwareChunker(
            chunk_size=10, chunk_overlap=2, tokenizer=CharTokenizer()
        )
        chunks = chunker.chunk_document(
            {
                "doc_id": "docx_long",
                "source_type": "docx",
                "title": "Modul Panjang",
                "clean_text": "",
                "sections": [{"heading": "Modul", "text": "A" * 45}],
            }
        )

        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(chunk.token_count, 10)
            self.assertEqual(chunk.metadata["strategy"], "structure_aware")
            self.assertTrue(
                chunk.metadata["structure_type"].endswith("_split")
            )


if __name__ == "__main__":
    unittest.main()
