"""Tests for the dynamic LLM judge client (Task 4.2)."""

from types import SimpleNamespace

import pytest

from rag_service.evaluation import judge as judge_module
from rag_service.evaluation.judge import (
    DEFAULT_JUDGE_API_KEY_ENV,
    DEFAULT_JUDGE_BASE_URL,
    DEFAULT_JUDGE_MODEL,
    JudgeClient,
    JudgeConfig,
    JudgeError,
    assert_independent_judge,
    extract_json,
    model_family,
)

JUDGE_ENV_VARS = (
    "JUDGE_MODEL",
    "JUDGE_BASE_URL",
    "JUDGE_API_KEY_ENV",
    "JUDGE_TEMPERATURE",
    "JUDGE_MAX_OUTPUT_TOKENS",
    "JUDGE_JSON_MAX_ATTEMPTS",
    "JUDGE_TIMEOUT_SECONDS",
)


class _FakeCompletions:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class _FakeClient:
    def __init__(self, responses):
        self.completions = _FakeCompletions(responses)
        self.chat = SimpleNamespace(completions=self.completions)


def _response(text, model="mimo-v2.6-flash", fingerprint=None, prompt_tokens=11, completion_tokens=22):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=text))],
        model=model,
        system_fingerprint=fingerprint,
        created=1700000000,
        usage=SimpleNamespace(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens),
    )


@pytest.fixture
def isolated_env(monkeypatch):
    """Keep JUDGE_* tests independent of the developer's .env file."""
    monkeypatch.setattr(judge_module, "_env_loaded", True)
    for name in JUDGE_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


# ----------------------------------------------------------------------
# configuration
# ----------------------------------------------------------------------


def test_constructor_defaults_point_at_the_free_mimo_judge():
    config = JudgeConfig()
    assert config.model_name == DEFAULT_JUDGE_MODEL
    assert config.base_url == DEFAULT_JUDGE_BASE_URL
    assert config.api_key_env == DEFAULT_JUDGE_API_KEY_ENV
    assert config.temperature == 0.0


def test_from_env_falls_back_to_defaults(isolated_env):
    config = JudgeConfig.from_env()
    assert config.model_name == DEFAULT_JUDGE_MODEL
    assert config.base_url == DEFAULT_JUDGE_BASE_URL


def test_from_env_reads_model_and_base_url(isolated_env):
    isolated_env.setenv("JUDGE_MODEL", "gemini-3.8-flash")
    isolated_env.setenv("JUDGE_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
    isolated_env.setenv("JUDGE_API_KEY_ENV", "GEMINI_API_KEY")
    isolated_env.setenv("JUDGE_TEMPERATURE", "0.2")
    isolated_env.setenv("JUDGE_MAX_OUTPUT_TOKENS", "1234")

    config = JudgeConfig.from_env()

    assert config.model_name == "gemini-3.8-flash"
    assert config.base_url == "https://generativelanguage.googleapis.com/v1beta/openai/"
    assert config.api_key_env == "GEMINI_API_KEY"
    assert config.temperature == 0.2
    assert config.max_output_tokens == 1234


def test_from_env_overrides_win(isolated_env):
    isolated_env.setenv("JUDGE_MODEL", "glm-5.3")
    config = JudgeConfig.from_env(model_name="claude-sonnet-5.5")
    assert config.model_name == "claude-sonnet-5.5"


def test_from_mapping_overrides_model_and_base_url(isolated_env):
    config = JudgeConfig.from_mapping(
        {
            "model_name": "grok-4.7",
            "base_url": "https://example.test/v1",
            "temperature": 0.0,
        }
    )
    assert config.model_name == "grok-4.7"
    assert config.base_url == "https://example.test/v1"


def test_from_mapping_rejects_unknown_keys(isolated_env):
    with pytest.raises(ValueError, match="unknown judge config keys"):
        JudgeConfig.from_mapping({"model": "typo-key"})


def test_empty_model_name_rejected():
    with pytest.raises(ValueError, match="model_name must not be empty"):
        JudgeConfig(model_name="  ")


def test_non_http_base_url_rejected():
    with pytest.raises(ValueError, match="base_url must be an HTTP"):
        JudgeConfig(model_name="mimo-v2.6-flash", base_url="tokenharbor.ai")


def test_api_key_env_must_be_named():
    with pytest.raises(ValueError, match="api_key_env"):
        JudgeConfig(model_name="mimo-v2.6-flash", api_key_env="")


def test_api_key_env_rejects_pasted_secret():
    with pytest.raises(ValueError, match="not hold the key itself"):
        JudgeConfig(
            model_name="mimo-v2.6-flash",
            api_key_env="thk_live_abc-DEF_123",
        )


def test_json_max_attempts_must_be_positive():
    with pytest.raises(ValueError, match="json_max_attempts"):
        JudgeConfig(model_name="mimo-v2.6-flash", json_max_attempts=0)


# ----------------------------------------------------------------------
# family independence (PRD 8.4)
# ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "model,family",
    [
        ("deepseek-v4.1-flash:free", "deepseek"),
        ("deepseek-v4-flash", "deepseek"),
        ("mimo-v2.6-flash:free", "mimo"),
        ("mimo-v2.5", "mimo"),
        ("gemini-3.8-flash", "google"),
        ("claude-sonnet-5.5", "anthropic"),
        ("gpt-6.1-terra", "openai"),
        ("qwen3.8-max", "qwen"),
        ("glm-5.3", "zhipu"),
        ("grok-4.7", "xai"),
        ("mistral-large-4", "mistral"),
        ("kimi-k3", "moonshot"),
        ("muse-spark-1.2", "unknown"),
    ],
)
def test_model_family_mapping(model, family):
    assert model_family(model) == family


def test_independent_judge_accepts_a_different_family():
    assert assert_independent_judge("mimo-v2.6-flash:free") == "mimo"


def test_independent_judge_rejects_the_generator_family():
    with pytest.raises(JudgeError, match="same family as the generator"):
        assert_independent_judge("deepseek-v4-flash")


def test_independent_judge_can_be_overridden_for_exploration():
    assert assert_independent_judge("deepseek-v4-flash", allow_same_family=True) == "deepseek"


def test_judge_client_refuses_same_family_by_default():
    with pytest.raises(JudgeError, match="PRD section 8.4"):
        JudgeClient(
            config=JudgeConfig(model_name="deepseek-v4.1-flash:free"),
            client=_FakeClient([]),
        )


# ----------------------------------------------------------------------
# JSON salvage
# ----------------------------------------------------------------------


def test_extract_json_bare_payload():
    assert extract_json('{"claims": []}') == {"claims": []}


def test_extract_json_fenced_block():
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_extract_json_survives_trailing_prose():
    text = '{"claims": [{"claim": "x", "supported": true}]}\n\nSemoga membantu!'
    assert extract_json(text) == {"claims": [{"claim": "x", "supported": True}]}


def test_extract_json_accepts_a_top_level_array():
    assert extract_json('```\n[1, 2, 3]\n```') == [1, 2, 3]


def test_extract_json_ignores_braces_inside_strings():
    text = '{"claim": "pakai tanda { dan } di dalam teks", "supported": true}'
    assert extract_json(text)["supported"] is True


def test_extract_json_raises_without_json():
    with pytest.raises(ValueError, match="no JSON value found"):
        extract_json("Maaf, saya tidak bisa menjawab.")


def test_extract_json_raises_on_empty_text():
    with pytest.raises(ValueError, match="empty response"):
        extract_json("   ")


# ----------------------------------------------------------------------
# calls
# ----------------------------------------------------------------------


def test_complete_returns_raw_text_and_usage(isolated_env):
    client = JudgeClient(config=JudgeConfig(), client=_FakeClient([_response("halo")]))
    result = client.complete("prompt")

    assert result.text == "halo"
    assert result.data is None
    assert result.prompt_tokens == 11
    assert result.completion_tokens == 22
    assert result.attempts == 1


def test_complete_json_parses_fenced_answer(isolated_env):
    client = JudgeClient(
        config=JudgeConfig(),
        client=_FakeClient([_response('```json\n{"claims": [{"claim": "a", "supported": true}]}\n```')]),
    )
    result = client.complete_json("prompt")

    assert result.data == {"claims": [{"claim": "a", "supported": True}]}
    assert result.attempts == 1


def test_complete_json_retries_after_unparseable_output(isolated_env):
    fake = _FakeClient([_response("bukan json sama sekali"), _response('{"ok": true}')])
    client = JudgeClient(config=JudgeConfig(), client=fake)

    result = client.complete_json("prompt")

    assert result.data == {"ok": True}
    assert result.attempts == 2
    assert len(fake.completions.calls) == 2


def test_complete_json_raises_after_max_attempts(isolated_env):
    fake = _FakeClient([_response("nope"), _response("still nope")])
    config = JudgeConfig(json_max_attempts=2)
    client = JudgeClient(config=config, client=fake)

    with pytest.raises(JudgeError, match="did not return valid JSON after 2 attempts"):
        client.complete_json("prompt")
    assert len(fake.completions.calls) == 2


def test_complete_sends_locked_temperature_and_model(isolated_env):
    fake = _FakeClient([_response("{}")])
    client = JudgeClient(config=JudgeConfig(), client=fake)
    client.complete("prompt", system="sistem")

    sent = fake.completions.calls[0]
    assert sent["model"] == DEFAULT_JUDGE_MODEL
    assert sent["temperature"] == 0.0
    assert sent["messages"][0] == {"role": "system", "content": "sistem"}
    assert sent["messages"][1] == {"role": "user", "content": "prompt"}


def test_provider_error_is_wrapped(isolated_env):
    client = JudgeClient(config=JudgeConfig(), client=_FakeClient([RuntimeError("gateway down")]))
    with pytest.raises(JudgeError, match="judge request failed"):
        client.complete("prompt")


def test_empty_completion_is_rejected(isolated_env):
    client = JudgeClient(config=JudgeConfig(), client=_FakeClient([_response("   ")]))
    with pytest.raises(JudgeError, match="empty completion"):
        client.complete("prompt")


def test_empty_prompt_is_rejected(isolated_env):
    client = JudgeClient(config=JudgeConfig(), client=_FakeClient([]))
    with pytest.raises(ValueError, match="prompt must not be empty"):
        client.complete("  ")
    with pytest.raises(ValueError, match="prompt must not be empty"):
        client.complete_json("  ")


def test_snapshot_metadata_records_dynamic_endpoint(isolated_env):
    config = JudgeConfig(model_name="gemini-3.8-flash", base_url="https://example.test/v1")
    client = JudgeClient(config=config, client=_FakeClient([]))
    snapshot = client.snapshot_metadata()

    assert snapshot["base_url"] == "https://example.test/v1"
    assert snapshot["requested_model"] == "gemini-3.8-flash"
    assert snapshot["judge_family"] == "google"
    assert snapshot["independent_family"] is True


def test_served_model_is_recorded_when_it_differs(isolated_env, caplog):
    client = JudgeClient(
        config=JudgeConfig(),
        client=_FakeClient([_response("{}", model="mimo-v2.6-flash-2026-11")]),
    )
    result = client.complete("prompt")

    assert result.returned_model == "mimo-v2.6-flash-2026-11"
    assert result.requested_model == DEFAULT_JUDGE_MODEL
    assert result.snapshot["returned_model"] == "mimo-v2.6-flash-2026-11"
