"""Tests for the FastAPI service endpoints (Task 2.14).

Uses ``httpx.ASGITransport`` instead of Starlette's ``TestClient`` so the
suite also works with httpx 0.28+ (``TestClient`` currently requires <0.28).
"""

import unittest

from rag_service.main import (
    DEFAULT_EXPERIMENT_CODE,
    HAS_FASTAPI,
    app,
    clear_pipeline_cache,
    set_pipeline_factory,
)

try:
    import httpx

    HAS_HTTPX = True
except ImportError:  # pragma: no cover - httpx not installed
    httpx = None  # type: ignore
    HAS_HTTPX = False


ANSWER = (
    "Syarat usia calon peserta magang adalah 18 sampai 30 tahun.\n"
    "[Sumber: Panduan_Pendaftaran.pdf]"
)

RESULT_PAYLOAD = {
    "experiment_code": "E16",
    "question": "Apa syarat usia program magang?",
    "answer": ANSWER,
    "sources": ["Panduan_Pendaftaran.pdf"],
    "retrieved_sources": ["Panduan_Pendaftaran.pdf", "FAQ_Web"],
    "chunks": [
        {
            "chunk_id": "doc_panduan_c1",
            "content": "Peserta berusia 18 sampai 30 tahun.",
            "score": 0.91,
            "doc_id": "doc_panduan",
            "source_type": "pdf",
            "source_title": "Panduan_Pendaftaran.pdf",
            "token_count": 42,
            "metadata": {"strategy": "structure_aware"},
            "rank": 1,
        },
        {
            "chunk_id": "faq_web_c3",
            "content": "Pendaftaran dilakukan secara online.",
            "score": 0.84,
            "doc_id": "faq_web",
            "source_type": "web",
            "source_title": "FAQ_Web",
            "token_count": 18,
            "metadata": {"strategy": "structure_aware"},
            "rank": 2,
        },
    ],
    "retrieval_method": "hybrid_rerank",
    "chunking_strategy": "structure_aware",
    "latency_ms": 321.5,
    "retrieval_latency_ms": 120.0,
    "generation_latency_ms": 200.0,
    "rerank_latency_ms": 15.5,
    "context_tokens": 310,
    "context_chunks": 2,
    "is_refusal": False,
}


class FakePipeline:
    """Canned pipeline that records the received questions."""

    def __init__(self, config, payload=None):
        self.config = config
        self.payload = dict(payload or RESULT_PAYLOAD)
        self.questions = []

    def ask(self, question):
        self.questions.append(question)
        payload = dict(self.payload)
        payload["question"] = question
        payload["experiment_code"] = self.config.code
        return payload


@unittest.skipUnless(
    HAS_FASTAPI and HAS_HTTPX, "FastAPI / httpx is not installed"
)
class TestAPIEndpoints(unittest.IsolatedAsyncioTestCase):
    """HTTP contract of ``/api/health`` and ``/api/ask``."""

    async def asyncSetUp(self):
        clear_pipeline_cache()
        self.built = []
        self.pipelines = []

        def factory(config):
            self.built.append(config.code)
            pipeline = FakePipeline(config)
            self.pipelines.append(pipeline)
            return pipeline

        set_pipeline_factory(factory)
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        )

    async def asyncTearDown(self):
        await self.client.aclose()
        set_pipeline_factory(None)
        clear_pipeline_cache()

    def use_factory_without_sources(self):
        payload = dict(RESULT_PAYLOAD)
        payload["sources"] = []

        def factory(config):
            return FakePipeline(config, payload=payload)

        set_pipeline_factory(factory)
        clear_pipeline_cache()

    # -- health -----------------------------------------------------

    async def test_health_returns_ok_without_loading_pipeline(self):
        response = await self.client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["service"], "rag_backend")
        self.assertIn("structure_aware", payload["supported_chunkers"])
        self.assertIn("hybrid_rerank", payload["supported_retrievers"])
        self.assertIn("E16", payload["available_experiments"])
        self.assertEqual(self.built, [])

    # -- ask success ------------------------------------------------

    async def test_ask_returns_answer_sources_latency_and_chunk_metadata(self):
        response = await self.client.post(
            "/api/ask", json={"question": "Apa syarat usia program magang?"}
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["experiment_code"], DEFAULT_EXPERIMENT_CODE)
        self.assertEqual(payload["answer"], ANSWER)
        self.assertEqual(payload["sources"], ["Panduan_Pendaftaran.pdf"])
        self.assertEqual(
            payload["retrieved_sources"],
            ["Panduan_Pendaftaran.pdf", "FAQ_Web"],
        )
        self.assertEqual(payload["retrieval_method"], "hybrid_rerank")
        self.assertEqual(payload["chunking_strategy"], "structure_aware")
        self.assertAlmostEqual(payload["latency_ms"], 321.5)
        self.assertAlmostEqual(payload["retrieval_latency_ms"], 120.0)
        self.assertAlmostEqual(payload["generation_latency_ms"], 200.0)
        self.assertAlmostEqual(payload["rerank_latency_ms"], 15.5)
        self.assertEqual(payload["context_tokens"], 310)
        self.assertEqual(payload["context_chunks"], 2)
        self.assertFalse(payload["is_refusal"])
        self.assertEqual(payload["question"], "Apa syarat usia program magang?")

        chunks = payload["chunks"]
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0]["chunk_id"], "doc_panduan_c1")
        self.assertEqual(chunks[0]["source_type"], "pdf")
        self.assertEqual(chunks[0]["source_title"], "Panduan_Pendaftaran.pdf")
        self.assertEqual(chunks[0]["token_count"], 42)
        self.assertEqual(chunks[0]["rank"], 1)
        self.assertAlmostEqual(chunks[0]["score"], 0.91)
        # Internal chunk content is not part of the public API contract.
        self.assertNotIn("content", chunks[0])

    async def test_question_is_trimmed_before_reaching_the_pipeline(self):
        response = await self.client.post(
            "/api/ask", json={"question": "  Apa syarat usia?  "}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.pipelines[0].questions, ["Apa syarat usia?"])

    async def test_config_code_is_normalized_and_forwarded(self):
        response = await self.client.post(
            "/api/ask",
            json={"question": "Apa syarat usia?", "config_code": " e16 "},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["experiment_code"], "E16")
        self.assertEqual(self.built, ["E16"])

    async def test_pipeline_is_built_once_and_reused_for_the_same_config(self):
        for _ in range(3):
            response = await self.client.post(
                "/api/ask", json={"question": "Apa syarat usia?"}
            )
            self.assertEqual(response.status_code, 200)

        self.assertEqual(self.built, ["E16"])

    async def test_missing_citation_falls_back_to_retrieved_sources(self):
        self.use_factory_without_sources()

        response = await self.client.post(
            "/api/ask", json={"question": "Apa syarat usia?"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["sources"],
            ["Panduan_Pendaftaran.pdf", "FAQ_Web"],
        )

    async def test_http_errors_do_not_leak_internal_details(self):
        def factory(config):
            raise FileNotFoundError("/srv/secret/path/E16.yaml")

        set_pipeline_factory(factory)
        clear_pipeline_cache()
        response = await self.client.post(
            "/api/ask", json={"question": "Apa syarat usia?"}
        )

        self.assertEqual(response.status_code, 404)
        self.assertNotIn("/srv/secret", response.text)

    # -- validation -------------------------------------------------

    async def test_blank_or_missing_question_is_rejected(self):
        for payload in ({}, {"question": ""}, {"question": "   \n\t "}):
            response = await self.client.post("/api/ask", json=payload)
            self.assertEqual(response.status_code, 422, payload)

        self.assertEqual(self.built, [])

    async def test_question_longer_than_500_characters_is_rejected(self):
        response = await self.client.post(
            "/api/ask", json={"question": "x" * 501}
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.built, [])

    async def test_invalid_config_code_is_rejected(self):
        for code in ("E00", "E17", "E99", "dense", "16"):
            response = await self.client.post(
                "/api/ask",
                json={"question": "Apa syarat usia?", "config_code": code},
            )
            self.assertEqual(response.status_code, 422, code)

        self.assertEqual(self.built, [])

    async def test_config_code_must_be_a_string(self):
        response = await self.client.post(
            "/api/ask",
            json={"question": "Apa syarat usia?", "config_code": 16},
        )

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
