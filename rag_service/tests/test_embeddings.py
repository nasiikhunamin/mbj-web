"""Tests for Task 2.6: E5 embedding module with mandatory prefixes."""

import unittest

from rag_service.embeddings import E5Encoder


class TestE5Encoder(unittest.TestCase):
    """Verify dimensions, prefix behavior, batching, and determinism."""

    def setUp(self):
        self.encoder = E5Encoder(batch_size=4, allow_fallback=True)

    def test_dimension_is_768(self):
        vector = self.encoder.embed_query("berapa biaya hidup di Jepang?")
        self.assertEqual(len(vector), 768)
        self.assertTrue(all(isinstance(value, float) for value in vector[:10]))

    def test_documents_use_passage_prefix(self):
        without_prefix = self.encoder.embed_documents(["syarat usia peserta magang"])[0]
        with_prefix = self.encoder.embed_documents(["passage: syarat usia peserta magang"])[0]
        self.assertNotEqual(without_prefix, with_prefix)

    def test_query_and_document_embeddings_differ(self):
        document = self.encoder.embed_documents(["informasi program SSW"])[0]
        query = self.encoder.embed_query("informasi program SSW")
        self.assertNotEqual(document, query)

    def test_batch_processing_keeps_order_and_size(self):
        texts = ["biaya asrama", "alur pendaftaran", "syarat visa"]
        vectors = self.encoder.embed_documents(texts)
        self.assertEqual(len(vectors), len(texts))
        for vector in vectors:
            self.assertEqual(len(vector), 768)

    def test_empty_sequence(self):
        self.assertEqual(self.encoder.embed_documents([]), [])

    def test_rejects_plain_string_for_documents(self):
        with self.assertRaises(TypeError):
            self.encoder.embed_documents("bukan list")  # type: ignore[arg-type]

    def test_deterministic_across_instances(self):
        first = E5Encoder(allow_fallback=True).embed_documents(["korpus LPK MBJ"])[0]
        second = E5Encoder(allow_fallback=True).embed_documents(["korpus LPK MBJ"])[0]
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
