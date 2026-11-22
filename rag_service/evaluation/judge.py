"""LLM judge client with a dynamic model id and base URL (Task 4.2).

The RAGAS faithfulness score is produced by a *judge* model that must come from
a **different model family** than the generator, otherwise the evaluation is
biased towards its own output (PRD section 8.4, ADR 0002).

Because the available judge varies over time (free routes expire, paid routes
need credit), the model id and the base URL are **configuration, not code**:

======================  ==============================  ==============================
Environment variable    Default                         Purpose
======================  ==============================  ==============================
``JUDGE_MODEL``         ``mimo-v2.6-flash:free``        judge model id
``JUDGE_BASE_URL``      ``https://tokenharbor.ai/v1``   OpenAI-compatible endpoint
``JUDGE_API_KEY_ENV``   ``TOKENHARBOR_API_KEY``         name of the env var holding the key
``JUDGE_TEMPERATURE``   ``0.0``                         locked for reproducibility
``JUDGE_MAX_OUTPUT_TOKENS``  ``700``                    JSON answers are token-hungry
======================  ==============================  ==============================

Switching to another provider is therefore an ``.env`` edit, for example::

    JUDGE_MODEL=gemini-3.8-flash
    JUDGE_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
    JUDGE_API_KEY_ENV=GEMINI_API_KEY

The same values can also be supplied as a mapping (``JudgeConfig.from_mapping``)
so a YAML experiment config can override them later without touching code.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from openai import OpenAI

    HAS_OPENAI = True
except ImportError:  # pragma: no cover - exercised only without the SDK
    OpenAI = None  # type: ignore
    HAS_OPENAI = False

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dotenv is optional
    load_dotenv = None  # type: ignore

logger = logging.getLogger(__name__)

DEFAULT_JUDGE_MODEL = "mimo-v2.6-flash:free"
DEFAULT_JUDGE_BASE_URL = "https://tokenharbor.ai/v1"
DEFAULT_JUDGE_API_KEY_ENV = "TOKENHARBOR_API_KEY"

#: The generator family, used by :func:`assert_independent_judge` (ADR 0001).
GENERATOR_FAMILY = "deepseek"

DEFAULT_GENERATOR_MODEL = "deepseek-v4.1-flash:free"

_ENV_FILES = (
    Path(__file__).resolve().parents[2] / ".env",
    Path(__file__).resolve().parents[2] / "rag_service" / ".env",
)
_env_loaded = False

_FENCE_PATTERN = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)

#: Longest-first so ``mimo-v2.6`` is not shadowed by a shorter prefix.
_FAMILY_PREFIXES: Tuple[Tuple[str, str], ...] = (
    ("deepseek", "deepseek"),
    ("mimo", "mimo"),
    ("gemini", "google"),
    ("gemma", "google"),
    ("claude", "anthropic"),
    ("gpt", "openai"),
    ("qwen", "qwen"),
    ("glm", "zhipu"),
    ("grok", "xai"),
    ("mistral", "mistral"),
    ("mixtral", "mistral"),
    ("magistral", "mistral"),
    ("kimi", "moonshot"),
    ("moonshot", "moonshot"),
    ("minimax", "minimax"),
    ("ling", "ling"),
)


class JudgeError(RuntimeError):
    """Raised when the judge cannot be built or cannot return usable JSON."""


def _load_env_files_once() -> None:
    """Load keys from the project .env files without overriding real env vars."""
    global _env_loaded
    if _env_loaded:
        return
    _env_loaded = True
    if load_dotenv is None:
        return
    for env_path in _ENV_FILES:
        if env_path.exists():
            load_dotenv(env_path, override=False)


def model_family(model_name: str) -> str:
    """Best-effort provider/family for ``model_name``.

    The ``:free``/``-fast`` route suffixes are ignored, so
    ``deepseek-v4.1-flash:free`` and ``deepseek-v4-flash`` both map to
    ``"deepseek"``. Unknown models return ``"unknown"``.
    """
    name = (model_name or "").strip().lower()
    if not name:
        return "unknown"
    name = name.split(":", 1)[0]
    for prefix, family in _FAMILY_PREFIXES:
        if name.startswith(prefix):
            return family
    return "unknown"


def assert_independent_judge(
    judge_model: str,
    generator_model: str = DEFAULT_GENERATOR_MODEL,
    *,
    allow_same_family: bool = False,
) -> str:
    """Enforce PRD section 8.4: the judge must not share the generator's family.

    Returns the judge family so callers can record it in the results.
    """
    judge_family = model_family(judge_model)
    generator_family = model_family(generator_model)

    if judge_family == "unknown":
        logger.warning(
            "Cannot determine the family of judge model %r; verify manually that it "
            "differs from the generator (%r).",
            judge_model,
            generator_model,
        )
        return judge_family

    if judge_family == generator_family:
        message = (
            f"judge model {judge_model!r} belongs to the same family as the generator "
            f"({generator_model!r} -> {generator_family!r}). PRD section 8.4 requires a "
            f"different family to avoid self-enhancement bias. Set JUDGE_MODEL to another "
            f"family, or pass allow_same_family=True to override for exploratory runs."
        )
        if not allow_same_family:
            raise JudgeError(message)
        logger.warning(message)

    return judge_family


def _first_json_value(text: str) -> Optional[str]:
    """Return the first balanced JSON object/array inside ``text``.

    Handles the common failure mode where a model appends prose after the JSON
    payload (``json.loads`` then reports ``Extra data``).
    """
    depth = 0
    start: Optional[int] = None
    in_string = False
    escaped = False

    for index, char in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char in "{[":
            if depth == 0:
                start = index
            depth += 1
        elif char in "}]":
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    return text[start : index + 1]

    return None


def extract_json(text: str) -> Any:
    """Parse the first JSON value in ``text``.

    Accepts a bare payload, a ```json fenced block, or a payload surrounded by
    prose. Raises :class:`ValueError` when nothing parseable is present.
    """
    if not text or not text.strip():
        raise ValueError("judge returned an empty response")

    candidates: List[str] = [block.strip() for block in _FENCE_PATTERN.findall(text)]
    candidates.append(text.strip())

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

        balanced = _first_json_value(candidate)
        if balanced is not None:
            try:
                return json.loads(balanced)
            except json.JSONDecodeError:
                continue

    raise ValueError("no JSON value found in the judge response")


@dataclass(frozen=True)
class JudgeConfig:
    """Judge identity and call parameters — all dynamically configurable."""

    model_name: str = DEFAULT_JUDGE_MODEL
    base_url: str = DEFAULT_JUDGE_BASE_URL
    api_key_env: str = DEFAULT_JUDGE_API_KEY_ENV
    temperature: float = 0.0
    max_output_tokens: int = 700
    timeout_seconds: float = 60.0
    max_retries: int = 2
    json_max_attempts: int = 3
    allow_same_family: bool = False
    generator_model: str = DEFAULT_GENERATOR_MODEL

    def __post_init__(self) -> None:
        if not self.model_name or not self.model_name.strip():
            raise ValueError("model_name must not be empty")
        if not self.base_url.startswith(("http://", "https://")):
            raise ValueError(f"base_url must be an HTTP(S) URL, got {self.base_url!r}")
        if not self.api_key_env or not self.api_key_env.strip():
            raise ValueError("api_key_env must name an environment variable")
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError(
                f"temperature must be between 0 and 2, got {self.temperature}"
            )
        if self.max_output_tokens <= 0:
            raise ValueError(
                f"max_output_tokens must be positive, got {self.max_output_tokens}"
            )
        if self.timeout_seconds <= 0:
            raise ValueError(
                f"timeout_seconds must be positive, got {self.timeout_seconds}"
            )
        if self.max_retries < 0:
            raise ValueError(f"max_retries must be non-negative, got {self.max_retries}")
        if self.json_max_attempts < 1:
            raise ValueError(
                f"json_max_attempts must be at least 1, got {self.json_max_attempts}"
            )

    @classmethod
    def from_env(cls, **overrides: Any) -> "JudgeConfig":
        """Build a config from ``JUDGE_*`` environment variables, then overrides."""
        _load_env_files_once()
        values: Dict[str, Any] = {
            "model_name": os.getenv("JUDGE_MODEL", DEFAULT_JUDGE_MODEL),
            "base_url": os.getenv("JUDGE_BASE_URL", DEFAULT_JUDGE_BASE_URL),
            "api_key_env": os.getenv("JUDGE_API_KEY_ENV", DEFAULT_JUDGE_API_KEY_ENV),
            "temperature": float(os.getenv("JUDGE_TEMPERATURE", "0.0")),
            "max_output_tokens": int(os.getenv("JUDGE_MAX_OUTPUT_TOKENS", "700")),
        }

        raw_attempts = os.getenv("JUDGE_JSON_MAX_ATTEMPTS")
        if raw_attempts:
            values["json_max_attempts"] = int(raw_attempts)

        raw_timeout = os.getenv("JUDGE_TIMEOUT_SECONDS")
        if raw_timeout:
            values["timeout_seconds"] = float(raw_timeout)

        values.update(overrides)
        return cls(**values)

    @classmethod
    def from_mapping(cls, mapping: Optional[Dict[str, Any]] = None, **overrides: Any) -> "JudgeConfig":
        """Build from a YAML mapping, falling back to env vars then defaults.

        Recognised keys: ``model_name``, ``base_url``, ``api_key_env``,
        ``temperature``, ``max_output_tokens``.
        """
        values = dict(mapping or {})
        allowed = {
            "model_name",
            "base_url",
            "api_key_env",
            "temperature",
            "max_output_tokens",
            "timeout_seconds",
            "max_retries",
            "json_max_attempts",
            "allow_same_family",
            "generator_model",
        }
        unknown = sorted(set(values) - allowed)
        if unknown:
            raise ValueError(f"unknown judge config keys: {', '.join(unknown)}")

        base = cls.from_env()
        merged = {**_as_dict(base), **values, **overrides}
        return cls(**merged)


@dataclass
class JudgeResponse:
    """Raw judge text plus the identity metadata needed for audit."""

    text: str
    data: Any
    requested_model: str
    returned_model: str
    system_fingerprint: Optional[str]
    created_at: int
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float
    attempts: int = 1
    snapshot: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-serializable dictionary."""
        return {
            "data": self.data,
            "requested_model": self.requested_model,
            "returned_model": self.returned_model,
            "system_fingerprint": self.system_fingerprint,
            "created_at": self.created_at,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "latency_ms": self.latency_ms,
            "attempts": self.attempts,
            "snapshot": dict(self.snapshot),
        }


def _as_dict(config: JudgeConfig) -> Dict[str, Any]:
    return {
        "model_name": config.model_name,
        "base_url": config.base_url,
        "api_key_env": config.api_key_env,
        "temperature": config.temperature,
        "max_output_tokens": config.max_output_tokens,
        "timeout_seconds": config.timeout_seconds,
        "max_retries": config.max_retries,
        "json_max_attempts": config.json_max_attempts,
        "allow_same_family": config.allow_same_family,
        "generator_model": config.generator_model,
    }


class JudgeClient:
    """Ask the judge model for JSON answers, with salvage and retry."""

    def __init__(
        self,
        config: Optional[JudgeConfig] = None,
        client: Optional[Any] = None,
        api_key: Optional[str] = None,
    ):
        self.config = config or JudgeConfig.from_env()
        self.family = assert_independent_judge(
            self.config.model_name,
            self.config.generator_model,
            allow_same_family=self.config.allow_same_family,
        )
        self._client = client
        self._explicit_api_key = api_key

        if client is None:
            self._client = self._build_client()

    def _build_client(self) -> Any:
        if not HAS_OPENAI:
            raise JudgeError(
                "openai SDK is not installed; install rag_service/requirements.txt"
            )
        _load_env_files_once()
        api_key = self._explicit_api_key or os.getenv(self.config.api_key_env)
        if not api_key:
            raise JudgeError(
                f"{self.config.api_key_env} is not set. Add it to the project .env "
                f"or export it before running the evaluation."
            )
        return OpenAI(
            api_key=api_key,
            base_url=self.config.base_url,
            timeout=self.config.timeout_seconds,
            max_retries=self.config.max_retries,
        )

    def snapshot_metadata(self) -> Dict[str, Any]:
        """Describe the judge identity and endpoint before any call is made."""
        return {
            "base_url": self.config.base_url,
            "requested_model": self.config.model_name,
            "judge_family": self.family,
            "generator_model": self.config.generator_model,
            "independent_family": self.family != model_family(self.config.generator_model),
            "model_snapshot": "as served by the gateway (no dated snapshot on free routes)",
            "temperature": self.config.temperature,
            "max_output_tokens": self.config.max_output_tokens,
        }

    def _create_completion(self, prompt: str, system: Optional[str]) -> Any:
        messages: List[Dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            return self._client.chat.completions.create(
                model=self.config.model_name,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_output_tokens,
            )
        except Exception as exc:  # noqa: BLE001 - boundary to the provider SDK
            raise JudgeError(f"judge request failed: {exc}") from exc

    @staticmethod
    def _read_response(response: Any, model_name: str, latency_ms: float, attempts: int) -> Tuple[str, Dict[str, Any]]:
        choice = response.choices[0] if getattr(response, "choices", None) else None
        message = getattr(choice, "message", None) if choice else None
        text = (getattr(message, "content", None) or "").strip()

        usage = getattr(response, "usage", None)
        returned_model = str(getattr(response, "model", "") or model_name)
        if returned_model != model_name:
            logger.warning(
                "Gateway served judge model %r, expected %r", returned_model, model_name
            )

        metadata = {
            "requested_model": model_name,
            "returned_model": returned_model,
            "system_fingerprint": getattr(response, "system_fingerprint", None),
            "created_at": int(getattr(response, "created", 0) or 0),
            "prompt_tokens": int(getattr(usage, "prompt_tokens", 0) or 0),
            "completion_tokens": int(getattr(usage, "completion_tokens", 0) or 0),
            "latency_ms": latency_ms,
            "attempts": attempts,
        }
        return text, metadata

    def complete(self, prompt: str, system: Optional[str] = None) -> JudgeResponse:
        """Return the raw judge text (no JSON parsing)."""
        if not prompt or not prompt.strip():
            raise ValueError("prompt must not be empty")

        started = time.perf_counter()
        response = self._create_completion(prompt.strip(), system)
        latency_ms = (time.perf_counter() - started) * 1000.0
        text, metadata = self._read_response(response, self.config.model_name, latency_ms, 1)

        if not text:
            raise JudgeError("judge returned an empty completion")

        return JudgeResponse(
            text=text,
            data=None,
            snapshot={
                **self.snapshot_metadata(),
                "returned_model": metadata["returned_model"],
                "execution_date": datetime.now(timezone.utc).isoformat(),
            },
            **metadata,
        )

    def complete_json(self, prompt: str, system: Optional[str] = None) -> JudgeResponse:
        """Return parsed JSON, retrying while the model emits unusable output."""
        if not prompt or not prompt.strip():
            raise ValueError("prompt must not be empty")

        last_error: Optional[Exception] = None

        for attempt in range(1, self.config.json_max_attempts + 1):
            started = time.perf_counter()
            response = self._create_completion(prompt.strip(), system)
            latency_ms = (time.perf_counter() - started) * 1000.0
            text, metadata = self._read_response(
                response, self.config.model_name, latency_ms, attempt
            )

            try:
                data = extract_json(text)
            except ValueError as exc:
                last_error = exc
                logger.warning(
                    "Judge attempt %d/%d returned unparseable JSON (%s)",
                    attempt,
                    self.config.json_max_attempts,
                    exc,
                )
                continue

            return JudgeResponse(
                text=text,
                data=data,
                snapshot={
                    **self.snapshot_metadata(),
                    "returned_model": metadata["returned_model"],
                    "execution_date": datetime.now(timezone.utc).isoformat(),
                },
                **metadata,
            )

        raise JudgeError(
            f"judge did not return valid JSON after {self.config.json_max_attempts} "
            f"attempts: {last_error}"
        )
