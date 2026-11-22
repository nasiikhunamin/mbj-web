"""Tests for Task 2.13: RAG orchestrator pipeline and experiment config loader."""

import json
import os
import re
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from rag_service.config import (
    ExperimentConfig,
    ConfigError,
    available_configs,
    load_config,
    resolve_config_path,
)
from rag_service.llm import (
    REFUSAL_MESSAGE,
    GenerationResult,
    GeneratorClient,
)
from rag_service.pipeline import RAGPipeline, build_pipeline
from rag_service.retrievers import HybridRetriever, RetrievedChunk

ANSWER = (
    "Syarat usia calon peserta magang adalah 18 sampai 30 tahun.\n"
    "[Sumber: Panduan_Pendaftaran.pdf]"
)


def make_chunk(
    chunk_id: str,
    content: str,
    title: str,
    score: float = 0.9,
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        content=content,
        score=score,
        doc_id=f"doc_{chunk_id}",
        source_type="pdf",
        source_title=title,
        token_count=len(content.split()),
        metadata={"strategy": "structure_aware"},
    )


CHUNKS = [
    make_chunk("c1", "Peserta berusia 18 sampai 30 tahun.", "Panduan_Pendaftaran.pdf"),
    make_chunk("c2", "Pendaftaran dilakukan secara online.", "FAQ_Web"),
    make_chunk("c3", "Biaya asrama sekitar tiga puluh ribu Yen per bulan.", "Brosur_Program.pdf"),
    make_chunk("c4", "Peserta wajib lulus tes kesehatan.", "Panduan_Pendaftaran.pdf"),
    make_chunk("c5", "Program SSW memberi upah standar industri Jepang.", "Regulasi_SO.pdf"),
    make_chunk("c6", "Silabus bahasa Jepang terdiri dari tiga bulan pelatihan.", "Silabus.docx"),
]


def make_generation(
    answer: str = ANSWER,
    sources=None,
    is_refusal: bool = False,
) -> GenerationResult:
    return GenerationResult(
        answer=answer,
        sources=list(sources if sources is not None else ["Panduan_Pendaftaran.pdf"]),
        is_refusal=is_refusal,
        requested_model="deepseek-v4.1-flash:free",
        returned_model="deepseek-v4.1-flash:free",
        provider="tokenharbor",
        system_fingerprint="fp_test",
        created_at=1763700000,
        prompt_tokens=120,
        completion_tokens=30,
        latency_ms=1.0,
        snapshot={"thinking": "disabled", "execution_date": "2026-11-21T00:00:00Z"},
    )


class FakeRetriever:
    """Return canned chunks and record the requested top_k."""

    def __init__(self, chunks):
        self.chunks = list(chunks)
        self.calls = []

    def retrieve(self, query, top_k=5):
        self.calls.append({"query": query, "top_k": top_k})
        return self.chunks[:top_k]


class FakeReranker:
    """Deterministic reranker that keeps the scored order and trims Top-N."""

    def __init__(self):
        self.calls = []

    def rerank(self, query, candidates, top_n=None):
        self.calls.append(
            {"query": query, "candidates": len(candidates), "top_n": top_n}
        )
        ordered = sorted(candidates, key=lambda chunk: (-chunk.score, chunk.chunk_id))
        limit = top_n if top_n is not None else len(ordered)
        return [
            replace(chunk, rank=rank)
            for rank, chunk in enumerate(ordered[:limit], start=1)
        ]


class FakeGenerator:
    """Mimic the generator contract, including empty-context refusal."""

    def __init__(self, generation=None):
        self.generation = generation or make_generation()
        self.calls = []

    def generate(self, question, chunks):
        self.calls.append({"question": question, "chunks": list(chunks)})
        if not chunks:
            return make_generation(
                answer=REFUSAL_MESSAGE,
                sources=[],
                is_refusal=True,
            )
        return self.generation


class WordTokenizer:
    """Cheap token counter so tests never load the E5 tokenizer."""

    def count_tokens(self, text):
        return len(re.findall(r"\w+", text))


def make_config(**overrides) -> ExperimentConfig:
    values = dict(
        code="E16",
        chunking_strategy="structure_aware",
        retrieval_method="hybrid_rerank",
        reranker_enabled=True,
        initial_candidates=20,
        final_top_n=5,
        reranker_top_n=5,
    )
    values.update(overrides)
    return ExperimentConfig(**values)


class TestExperimentConfig(unittest.TestCase):
    """YAML-driven experiment configuration."""

    def test_e16_yaml_is_loaded_with_locked_generator(self):
        config = load_config("E16")

        self.assertEqual(config.code, "E16")
        self.assertEqual(config.chunking_strategy, "structure_aware")
        self.assertEqual(config.retrieval_method, "hybrid_rerank")
        self.assertTrue(config.reranker_enabled)
        self.assertEqual(config.initial_candidates, 20)
        self.assertEqual(config.final_top_n, 5)
        self.assertEqual(config.dense_collection, "chroma_structure_aware")
        self.assertEqual(config.bm25_index, "bm25_structure_aware")
        self.assertEqual(config.embedding_model, "intfloat/multilingual-e5-base")
        self.assertEqual(config.generation.model_name, "deepseek-v4.1-flash:free")
        self.assertEqual(config.generation.base_url, "https://tokenharbor.ai/v1")
        self.assertEqual(config.generation.temperature, 0.0)
        self.assertTrue(config.generation.disable_thinking)
        self.assertIsNone(config.generation.seed)

    def test_config_directory_resolves_by_code(self):
        path = resolve_config_path("E16")
        self.assertTrue(path.name == "E16.yaml")
        self.assertTrue(path.exists())
        self.assertIn("E16", available_configs())

    def test_unknown_code_reports_available_configs(self):
        with self.assertRaises(FileNotFoundError) as ctx:
            load_config("E99")
        self.assertIn("E16", str(ctx.exception))

    def test_yaml_can_be_loaded_from_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "probe.yaml"
            path.write_text(
                "experiment:\n  code: E01\n"
                "chunking:\n  strategy: fixed\n"
                "retrieval:\n  method: dense\n",
                encoding="utf-8",
            )
            config = load_config(path)

        self.assertEqual(config.code, "E01")
        self.assertEqual(config.retrieval_method, "dense")
        self.assertFalse(config.reranker_enabled)
        self.assertEqual(config.chunking_strategy, "fixed")

    def test_method_aliases_are_normalized(self):
        config = ExperimentConfig.from_dict(
            {
                "experiment": {"code": "E02"},
                "chunking": {"strategy": "fixed"},
                "retrieval": {"method": "sparse"},
            }
        )
        self.assertEqual(config.retrieval_method, "sparse_bm25")

    def test_collection_names_must_match_chunking_strategy(self):
        with self.assertRaises(ConfigError):
            ExperimentConfig.from_dict(
                {
                    "experiment": {"code": "E03"},
                    "chunking": {"strategy": "fixed"},
                    "retrieval": {
                        "method": "hybrid_rrf",
                        "dense_collection": "chroma_semantic",
                    },
                }
            )

    def test_unknown_strategy_and_method_are_rejected(self):
        with self.assertRaises(ConfigError):
            ExperimentConfig.from_dict(
                {
                    "experiment": {"code": "E04"},
                    "chunking": {"strategy": "magic"},
                    "retrieval": {"method": "dense"},
                }
            )
        with self.assertRaises(ConfigError):
            ExperimentConfig.from_dict(
                {
                    "experiment": {"code": "E05"},
                    "chunking": {"strategy": "fixed"},
                    "retrieval": {"method": "telepathy"},
                }
            )

    def test_reranker_must_match_retrieval_method(self):
        with self.assertRaises(ConfigError):
            make_config(retrieval_method="hybrid_rrf", reranker_enabled=True)
        with self.assertRaises(ConfigError):
            make_config(retrieval_method="hybrid_rerank", reranker_enabled=False)

    def test_token_overlap_must_be_smaller_than_limit(self):
        with self.assertRaises(ConfigError):
            make_config(token_limit=512, token_overlap=512)


class TestPipelineRetrievalWiring(unittest.TestCase):
    """The pipeline must call exactly the component requested by the config."""

    def setUp(self):
        self.dense = FakeRetriever(CHUNKS)
        self.sparse = FakeRetriever(list(reversed(CHUNKS)))
        self.hybrid = HybridRetriever(self.dense, self.sparse, rrf_k=60)
        self.reranker = FakeReranker()
        self.generator = FakeGenerator()
        self.tokenizer = WordTokenizer()

    def build(self, **overrides):
        config = make_config(**overrides)
        pipeline = RAGPipeline(
            config=config,
            generator=self.generator,
            dense=self.dense,
            sparse=self.sparse,
            hybrid=self.hybrid,
            reranker=self.reranker,
            tokenizer=self.tokenizer,
        )
        return pipeline, config

    def test_dense_method_returns_final_top_n_without_reranking(self):
        pipeline, _ = self.build(
            retrieval_method="dense", reranker_enabled=False
        )
        result = pipeline.ask("Apa syarat usia?")

        self.assertEqual(self.dense.calls[0]["top_k"], 5)
        self.assertEqual(len(result.chunks), 5)
        self.assertEqual(self.reranker.calls, [])
        self.assertEqual(result.retrieval_method, "dense")

    def test_sparse_method_uses_sparse_retriever(self):
        pipeline, _ = self.build(
            retrieval_method="sparse_bm25", reranker_enabled=False
        )
        result = pipeline.ask("Apa syarat usia?")

        self.assertEqual(self.sparse.calls[0]["top_k"], 5)
        self.assertEqual(len(result.chunks), 5)
        self.assertEqual(result.retrieval_method, "sparse_bm25")

    def test_hybrid_rrf_uses_initial_candidates_for_both_sources(self):
        pipeline, _ = self.build(
            retrieval_method="hybrid_rrf", reranker_enabled=False
        )
        result = pipeline.ask("Apa syarat usia?")

        self.assertEqual(self.dense.calls[0]["top_k"], 20)
        self.assertEqual(self.sparse.calls[0]["top_k"], 20)
        self.assertEqual(self.reranker.calls, [])
        self.assertEqual(len(result.chunks), 5)
        self.assertEqual(result.rerank_latency_ms, 0.0)

    def test_hybrid_rerank_feeds_twenty_candidates_into_the_reranker(self):
        pipeline, _ = self.build()
        result = pipeline.ask("Apa syarat usia?")

        self.assertEqual(self.dense.calls[0]["top_k"], 20)
        self.assertEqual(self.sparse.calls[0]["top_k"], 20)
        self.assertEqual(self.reranker.calls[0]["candidates"], len(CHUNKS))
        self.assertEqual(self.reranker.calls[0]["top_n"], 5)
        self.assertEqual(len(result.chunks), 5)
        self.assertEqual([chunk.rank for chunk in result.chunks], [1, 2, 3, 4, 5])
        self.assertGreaterEqual(result.rerank_latency_ms, 0.0)

    def test_generator_receives_the_final_chunks(self):
        pipeline, _ = self.build()
        pipeline.ask("Apa syarat usia?")

        sent = self.generator.calls[0]["chunks"]
        self.assertEqual(len(sent), 5)
        self.assertEqual(self.generator.calls[0]["question"], "Apa syarat usia?")


class TestPipelinePayload(unittest.TestCase):
    """The payload must expose answer, sources, latency breakdown, and tokens."""

    def setUp(self):
        dense = FakeRetriever(CHUNKS)
        sparse = FakeRetriever(list(reversed(CHUNKS)))
        self.pipeline = RAGPipeline(
            config=make_config(),
            generator=FakeGenerator(),
            dense=dense,
            sparse=sparse,
            hybrid=HybridRetriever(dense, sparse),
            reranker=FakeReranker(),
            tokenizer=WordTokenizer(),
        )
        self.result = self.pipeline.ask("Apa syarat usia?")

    def test_payload_contains_required_fields(self):
        payload = self.result.to_dict()
        required = {
            "experiment_code",
            "question",
            "answer",
            "sources",
            "retrieved_sources",
            "chunks",
            "retrieval_method",
            "chunking_strategy",
            "latency_ms",
            "retrieval_latency_ms",
            "generation_latency_ms",
            "rerank_latency_ms",
            "context_tokens",
            "context_chunks",
            "is_refusal",
            "generator",
        }
        self.assertTrue(required.issubset(payload))
        self.assertEqual(payload["answer"], ANSWER)
        self.assertEqual(payload["sources"], ["Panduan_Pendaftaran.pdf"])
        self.assertEqual(
            payload["retrieved_sources"],
            [
                "Panduan_Pendaftaran.pdf",
                "Silabus.docx",
                "FAQ_Web",
                "Regulasi_SO.pdf",
                "Brosur_Program.pdf",
            ],
        )
        self.assertEqual(payload["chunking_strategy"], "structure_aware")
        self.assertEqual(payload["context_chunks"], 5)

    def test_payload_is_json_serializable(self):
        payload = self.result.to_dict()
        encoded = json.dumps(payload, ensure_ascii=False)
        self.assertIn("Syarat usia", encoded)

    def test_context_tokens_match_the_rendered_context(self):
        expected = WordTokenizer().count_tokens(
            GeneratorClient.build_context(self.result.chunks)
        )
        self.assertEqual(self.result.context_tokens, expected)
        self.assertGreater(self.result.context_tokens, 0)

    def test_latency_breakdown_is_consistent(self):
        self.assertGreaterEqual(self.result.latency_ms, 0.0)
        self.assertGreaterEqual(self.result.retrieval_latency_ms, 0.0)
        self.assertGreaterEqual(self.result.generation_latency_ms, 0.0)
        self.assertGreaterEqual(
            self.result.latency_ms,
            self.result.retrieval_latency_ms
            + self.result.generation_latency_ms
            - 1e-6,
        )

    def test_empty_retrieval_returns_refusal_payload(self):
        dense = FakeRetriever([])
        pipeline = RAGPipeline(
            config=make_config(
                retrieval_method="dense", reranker_enabled=False
            ),
            generator=FakeGenerator(),
            dense=dense,
            tokenizer=WordTokenizer(),
        )
        result = pipeline.ask("Apa syarat usia?")

        self.assertTrue(result.is_refusal)
        self.assertEqual(result.answer, REFUSAL_MESSAGE)
        self.assertEqual(result.chunks, [])
        self.assertEqual(result.context_tokens, 0)
        self.assertEqual(result.context_chunks, 0)
        self.assertEqual(result.retrieved_sources, [])


class TestPipelineValidation(unittest.TestCase):
    """Misconfiguration and bad input must fail loudly."""

    def test_missing_component_for_method_raises(self):
        with self.assertRaises(ValueError):
            RAGPipeline(config=make_config(retrieval_method="dense", reranker_enabled=False), generator=FakeGenerator())

    def test_missing_reranker_raises(self):
        dense = FakeRetriever(CHUNKS)
        with self.assertRaises(ValueError):
            RAGPipeline(
                config=make_config(),
                generator=FakeGenerator(),
                hybrid=HybridRetriever(dense, FakeRetriever(CHUNKS)),
                tokenizer=WordTokenizer(),
            )

    def test_config_type_is_enforced(self):
        with self.assertRaises(TypeError):
            RAGPipeline(config={"code": "E16"}, generator=FakeGenerator())

    def test_blank_question_is_rejected(self):
        dense = FakeRetriever(CHUNKS)
        pipeline = RAGPipeline(
            config=make_config(retrieval_method="dense", reranker_enabled=False),
            generator=FakeGenerator(),
            dense=dense,
            tokenizer=WordTokenizer(),
        )
        with self.assertRaises(ValueError):
            pipeline.ask("   ")


class TestBuildPipeline(unittest.TestCase):
    """The factory is importable and refuses to start without an API key."""

    def test_build_pipeline_requires_api_key(self):
        from rag_service.llm import GeneratorError

        config = make_config()
        config = replace(
            config,
            generation=replace(
                config.generation, api_key_env="RAG_TEST_UNSET_KEY"
            ),
        )
        os.environ.pop("RAG_TEST_UNSET_KEY", None)
        with self.assertRaises(GeneratorError):
            build_pipeline(config)


if __name__ == "__main__":
    unittest.main()
