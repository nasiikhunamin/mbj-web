"""Tests for Task 2.12: generator client, refusal prompting, snapshot tracking."""

import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from rag_service.llm import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL_NAME,
    REFUSAL_MESSAGE,
    SYSTEM_PROMPT,
    GenerationConfig,
    GeneratorClient,
    GeneratorError,
)
from rag_service.retrievers import RetrievedChunk

IN_SCOPE_ANSWER = (
    "Syarat usia calon peserta magang adalah 18 sampai 30 tahun.\n\n"
    "[Sumber: Panduan_Pendaftaran.pdf]\n"
    "[Sumber: FAQ_Web]"
)


def make_chunk(
    chunk_id: str = "c1",
    content: str = "Syarat usia calon peserta magang adalah 18 sampai 30 tahun.",
    title: str = "Panduan_Pendaftaran.pdf",
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        content=content,
        score=0.9,
        doc_id="doc_1",
        source_type="pdf",
        source_title=title,
        token_count=len(content.split()),
        metadata={"strategy": "structure_aware"},
        rank=1,
    )


def make_response(
    content: str,
    model: str = DEFAULT_MODEL_NAME,
    fingerprint: str = "fp_abc123",
    prompt_tokens: int = 320,
    completion_tokens: int = 48,
):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
        model=model,
        system_fingerprint=fingerprint,
        created=1763700000,
        usage=SimpleNamespace(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        ),
    )


class FakeCompletions:
    """Capture request kwargs and return a canned completion."""

    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.response


class FakeClient:
    def __init__(self, response=None, error=None):
        self.completions = FakeCompletions(response=response, error=error)
        self.chat = SimpleNamespace(completions=self.completions)


def build_client(response=None, error=None, **config_overrides):
    fake = FakeClient(response=response, error=error)
    config = GenerationConfig(**config_overrides)
    return GeneratorClient(config=config, client=fake), fake


class TestRefusalPrompting(unittest.TestCase):
    """Out-of-scope questions must produce the canonical refusal sentence."""

    def test_out_of_scope_answer_is_detected_as_refusal(self):
        client, _ = build_client(make_response(REFUSAL_MESSAGE))
        result = client.generate("Siapa presiden Jepang?", [make_chunk()])

        self.assertTrue(result.is_refusal)
        self.assertEqual(result.answer, REFUSAL_MESSAGE)
        self.assertEqual(result.sources, [])

    def test_refusal_with_surrounding_whitespace_is_still_detected(self):
        client, _ = build_client(make_response(f"  {REFUSAL_MESSAGE}  "))
        result = client.generate("Berapa harga tiket pesawat?", [make_chunk()])

        self.assertTrue(result.is_refusal)
        self.assertEqual(result.sources, [])

    def test_empty_context_refuses_without_calling_the_api(self):
        client, fake = build_client(make_response(REFUSAL_MESSAGE))
        result = client.generate("Apa syarat pendaftaran?", [])

        self.assertTrue(result.is_refusal)
        self.assertEqual(result.answer, REFUSAL_MESSAGE)
        self.assertEqual(result.prompt_tokens, 0)
        self.assertEqual(result.completion_tokens, 0)
        self.assertEqual(fake.completions.calls, [])
        self.assertEqual(result.snapshot["refusal_reason"], "empty_context")


class TestGroundedAnswer(unittest.TestCase):
    """In-scope answers must expose the cited documents."""

    def test_sources_are_extracted_and_deduplicated(self):
        answer = (
            "Usia 18-30 tahun.\n"
            "[Sumber: Panduan_Pendaftaran.pdf]\n"
            "[Sumber: FAQ_Web]\n"
            "[Sumber: Panduan_Pendaftaran.pdf]"
        )
        client, _ = build_client(make_response(answer))
        result = client.generate("Apa syarat usia?", [make_chunk()])

        self.assertFalse(result.is_refusal)
        self.assertEqual(
            result.sources, ["Panduan_Pendaftaran.pdf", "FAQ_Web"]
        )

    def test_answer_without_citation_is_flagged(self):
        client, _ = build_client(make_response("Usia 18-30 tahun."))
        result = client.generate("Apa syarat usia?", [make_chunk()])

        self.assertEqual(result.sources, [])
        self.assertTrue(result.snapshot["citation_missing"])

    def test_context_and_question_are_sent_to_the_model(self):
        client, fake = build_client(make_response(IN_SCOPE_ANSWER))
        client.generate(
            "Apa syarat usia?",
            [
                make_chunk(content="Peserta berusia 18 sampai 30 tahun."),
                make_chunk(
                    chunk_id="c2",
                    content="Pendaftaran dilakukan secara online.",
                    title="FAQ_Web",
                ),
            ],
        )

        request = fake.completions.calls[0]
        system_message, user_message = request["messages"]
        self.assertEqual(system_message["content"], SYSTEM_PROMPT)
        self.assertIn("Apa syarat usia?", user_message["content"])
        self.assertIn("Peserta berusia 18 sampai 30 tahun.", user_message["content"])
        self.assertIn("[1] Sumber: Panduan_Pendaftaran.pdf", user_message["content"])
        self.assertIn("[2] Sumber: FAQ_Web", user_message["content"])

    def test_dict_chunks_are_accepted(self):
        client, _ = build_client(make_response(IN_SCOPE_ANSWER))
        chunk = make_chunk().to_dict()
        result = client.generate("Apa syarat usia?", [chunk])

        self.assertFalse(result.is_refusal)
        self.assertEqual(result.sources, ["Panduan_Pendaftaran.pdf", "FAQ_Web"])


class TestLockedGenerationParameters(unittest.TestCase):
    """The generator must stay locked to the Token Harbor free DeepSeek model."""

    def test_defaults_match_the_locked_model(self):
        config = GenerationConfig()
        self.assertEqual(config.model_name, DEFAULT_MODEL_NAME)
        self.assertEqual(config.model_name, "deepseek-v4.1-flash:free")
        self.assertEqual(config.base_url, DEFAULT_BASE_URL)
        self.assertEqual(config.base_url, "https://tokenharbor.ai/v1")
        self.assertEqual(config.temperature, 0.0)
        self.assertEqual(config.max_output_tokens, 600)

    def test_request_disables_thinking_and_omits_seed(self):
        client, fake = build_client(make_response(IN_SCOPE_ANSWER))
        client.generate("Apa syarat usia?", [make_chunk()])

        request = fake.completions.calls[0]
        self.assertEqual(request["model"], "deepseek-v4.1-flash:free")
        self.assertEqual(request["temperature"], 0.0)
        self.assertEqual(request["max_tokens"], 600)
        self.assertEqual(request["extra_body"], {"thinking": {"type": "disabled"}})
        self.assertNotIn("seed", request)

    def test_seed_is_only_sent_when_configured(self):
        client, fake = build_client(make_response(IN_SCOPE_ANSWER), seed=42)
        client.generate("Apa syarat usia?", [make_chunk()])

        self.assertEqual(fake.completions.calls[0]["seed"], 42)

    def test_invalid_config_is_rejected(self):
        with self.assertRaises(ValueError):
            GenerationConfig(temperature=3.0)
        with self.assertRaises(ValueError):
            GenerationConfig(base_url="tokenharbor.ai/v1")
        with self.assertRaises(ValueError):
            GenerationConfig(max_output_tokens=0)


class TestSnapshotTracking(unittest.TestCase):
    """Every response must record the model identity and execution metadata."""

    def test_snapshot_captures_returned_model_and_fingerprint(self):
        response = make_response(
            IN_SCOPE_ANSWER,
            model="deepseek-v4.1-flash-free-2026-10",
            fingerprint="fp_live_42",
        )
        client, _ = build_client(response)
        result = client.generate("Apa syarat usia?", [make_chunk()])

        self.assertEqual(result.requested_model, "deepseek-v4.1-flash:free")
        self.assertEqual(result.returned_model, "deepseek-v4.1-flash-free-2026-10")
        self.assertEqual(result.system_fingerprint, "fp_live_42")
        self.assertEqual(result.prompt_tokens, 320)
        self.assertEqual(result.completion_tokens, 48)
        self.assertEqual(result.snapshot["thinking"], "disabled")
        self.assertIn("execution_date", result.snapshot)

    def test_snapshot_metadata_describes_dynamic_free_route(self):
        client, _ = build_client(make_response(IN_SCOPE_ANSWER))
        snapshot = client.snapshot_metadata()

        self.assertEqual(snapshot["provider"], "Token Harbor (OpenAI-compatible gateway)")
        self.assertEqual(snapshot["base_url"], "https://tokenharbor.ai/v1")
        self.assertEqual(snapshot["requested_model"], "deepseek-v4.1-flash:free")
        self.assertIn("no dated snapshot", snapshot["model_snapshot"])


class TestErrorHandling(unittest.TestCase):
    """Failures must surface as GeneratorError, never as silent empty answers."""

    def test_empty_completion_raises(self):
        client, _ = build_client(make_response(""))
        with self.assertRaises(GeneratorError):
            client.generate("Apa syarat usia?", [make_chunk()])

    def test_provider_error_is_wrapped(self):
        client, _ = build_client(error=RuntimeError("upstream 503"))
        with self.assertRaises(GeneratorError):
            client.generate("Apa syarat usia?", [make_chunk()])

    def test_missing_api_key_raises_helpful_error(self):
        env_name = "RAG_TEST_MISSING_API_KEY"
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop(env_name, None)
            with self.assertRaises(GeneratorError) as ctx:
                GeneratorClient(config=GenerationConfig(api_key_env=env_name))
        self.assertIn(env_name, str(ctx.exception))

    def test_blank_question_is_rejected(self):
        client, _ = build_client(make_response(IN_SCOPE_ANSWER))
        with self.assertRaises(ValueError):
            client.generate("   ", [make_chunk()])


class TestConfigFromEnv(unittest.TestCase):
    """Environment overrides keep the module usable outside the unit tests."""

    def test_env_values_are_used(self):
        with patch.dict(
            os.environ,
            {
                "GENERATOR_MODEL": "custom-model",
                "GENERATOR_BASE_URL": "https://example.test/v1",
                "GENERATOR_TEMPERATURE": "0.2",
                "GENERATOR_MAX_OUTPUT_TOKENS": "128",
            },
        ):
            config = GenerationConfig.from_env()

        self.assertEqual(config.model_name, "custom-model")
        self.assertEqual(config.base_url, "https://example.test/v1")
        self.assertEqual(config.temperature, 0.2)
        self.assertEqual(config.max_output_tokens, 128)

    def test_explicit_overrides_win_over_env(self):
        with patch.dict(os.environ, {"GENERATOR_MODEL": "from-env"}):
            config = GenerationConfig.from_env(model_name="explicit")

        self.assertEqual(config.model_name, "explicit")


if __name__ == "__main__":
    unittest.main()
