"""Edge-case coverage for the multilingual reranker (Task 2.16)."""

import unittest
from unittest import mock

from rag_service.rerankers import BGEReranker
from rag_service.rerankers import bge_reranker as reranker_module
from rag_service.rerankers.bge_reranker import _char_trigrams
from rag_service.retrievers import RetrievedChunk


def candidate(chunk_id, content):
    return RetrievedChunk(chunk_id=chunk_id, content=content, score=0.0)


class FakeCrossEncoder:
    """No-op cross-encoder used to exercise the model-backed branches."""

    init_calls = []

    def __init__(self, model_name, **kwargs):
        FakeCrossEncoder.init_calls.append((model_name, kwargs))

    def predict(self, pairs, batch_size=16, show_progress_bar=False):
        return [0.5 for _ in pairs]


class FakePredictModel:
    """Model stub returning mixed scalar/list scores."""

    def predict(self, pairs, batch_size=16, show_progress_bar=False):
        return [0.2, [0.9]][: len(pairs)]


class TestRerankerEdges(unittest.TestCase):
    def test_invalid_model_dimensions(self):
        with self.assertRaises(ValueError):
            BGEReranker(max_length=0)
        with self.assertRaises(ValueError):
            BGEReranker(batch_size=0)

    def test_unsupported_candidate_type(self):
        reranker = BGEReranker()
        reranker._load_attempted = True
        reranker._model = None

        with self.assertRaises(TypeError):
            reranker.rerank("biaya", [object()])

    def test_backend_reports_fallback_without_loading_models(self):
        reranker = BGEReranker()
        reranker._load_attempted = True
        reranker._model = None

        self.assertEqual(reranker.backend, "lexical-fallback")

    def test_model_backend_and_cross_encoder_cache(self):
        unique_model = "fake/cross-encoder-cache-test"
        cache_key = (unique_model, "cpu", 128)
        reranker_module._CROSS_ENCODER_CACHE.pop(cache_key, None)
        FakeCrossEncoder.init_calls.clear()

        with mock.patch.object(reranker_module, "HAS_CROSS_ENCODER", True), \
             mock.patch.object(reranker_module, "CrossEncoder", FakeCrossEncoder):
            first = BGEReranker(
                model_name=unique_model,
                device="cpu",
                max_length=128,
                allow_fallback=False,
            )
            second = BGEReranker(
                model_name=unique_model,
                device="cpu",
                max_length=128,
                allow_fallback=False,
            )

            self.assertEqual(first.backend, "cross-encoder")
            self.assertEqual(second.backend, "cross-encoder")

        reranker_module._CROSS_ENCODER_CACHE.pop(cache_key, None)
        self.assertEqual(len(FakeCrossEncoder.init_calls), 1)
        self.assertEqual(FakeCrossEncoder.init_calls[0][1], {"max_length": 128, "device": "cpu"})

    def test_model_load_failure_without_fallback_raises(self):
        unique_model = "fake/broken-model-test"

        with mock.patch.object(reranker_module, "HAS_CROSS_ENCODER", True), \
             mock.patch.object(
                 reranker_module,
                 "CrossEncoder",
                 side_effect=RuntimeError("weights unavailable"),
             ):
            reranker = BGEReranker(model_name=unique_model, allow_fallback=False)
            with self.assertRaises(RuntimeError):
                reranker.backend

    def test_model_load_failure_with_fallback_uses_lexical_scorer(self):
        unique_model = "fake/broken-model-fallback-test"

        with mock.patch.object(reranker_module, "HAS_CROSS_ENCODER", True), \
             mock.patch.object(
                 reranker_module,
                 "CrossEncoder",
                 side_effect=RuntimeError("weights unavailable"),
             ):
            reranker = BGEReranker(model_name=unique_model, allow_fallback=True)
            self.assertEqual(reranker.backend, "lexical-fallback")

    def test_missing_cross_encoder_is_explained_when_fallback_disabled(self):
        with mock.patch.object(reranker_module, "HAS_CROSS_ENCODER", False):
            reranker = BGEReranker(allow_fallback=False)
            with self.assertRaises(RuntimeError) as ctx:
                reranker.backend

        self.assertIn("sentence-transformers", str(ctx.exception))

    def test_model_scores_including_list_payloads_are_used(self):
        reranker = BGEReranker(top_n=2)
        reranker._load_attempted = True
        reranker._model = FakePredictModel()

        results = reranker.rerank(
            "biaya asrama",
            [
                candidate("low", "Informasi umum tentang asrama."),
                candidate("high", "Biaya asrama tiga puluh ribu Yen."),
            ],
        )

        self.assertEqual([item.chunk_id for item in results], ["high", "low"])
        self.assertEqual(results[0].score, 0.9)
        self.assertEqual(results[0].metadata["rerank_backend"], "cross-encoder")

    def test_lexical_score_edge_cases(self):
        self.assertEqual(BGEReranker._lexical_score("", "apa saja"), 0.0)
        self.assertEqual(BGEReranker._lexical_score("a b", "c d"), 0.0)
        self.assertEqual(_char_trigrams("a b"), set())

    def test_empty_candidate_content_scores_zero(self):
        reranker = BGEReranker(top_n=1)
        reranker._load_attempted = True
        reranker._model = None
        results = reranker.rerank("biaya", [candidate("empty", "")])

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].score, 0.0)


if __name__ == "__main__":
    unittest.main()
