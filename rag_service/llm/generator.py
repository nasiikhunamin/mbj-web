"""Generator client, refusal prompting, and snapshot tracking (Task 2.12).

Generator model: ``deepseek-v4.1-flash:free`` served through the Token Harbor
gateway (``https://tokenharbor.ai/v1``), which is OpenAI-API compatible.

Design notes
------------
* The generator is a *controlled constant* for the 4x4 experiment (E01-E16):
  the same model must be used for every configuration and every run.
* DeepSeek V4 enables thinking mode by default, and ``temperature`` has no
  effect in thinking mode. Thinking is therefore disabled explicitly so the
  locked ``temperature=0.0`` actually applies and latency stays low.
* This provider does not expose a ``seed`` parameter, so ``seed`` is optional
  and only sent when configured.
* Every response records the model identity echoed by the API
  (``model``, ``system_fingerprint``, ``created``) plus the execution date, so
  the run can be audited even though the ``:free`` route has no dated snapshot.
"""

from __future__ import annotations

import logging
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from rag_service.retrievers.base import RetrievedChunk

try:
    from openai import BadRequestError, OpenAI

    HAS_OPENAI = True
except ImportError:  # pragma: no cover - exercised only without the SDK
    BadRequestError = None  # type: ignore
    OpenAI = None  # type: ignore
    HAS_OPENAI = False

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dotenv is optional
    load_dotenv = None  # type: ignore

logger = logging.getLogger(__name__)

DEFAULT_MODEL_NAME = "deepseek-v4.1-flash:free"
DEFAULT_BASE_URL = "https://tokenharbor.ai/v1"
DEFAULT_API_KEY_ENV = "TOKENHARBOR_API_KEY"

#: Canonical refusal sentence required by PRD section 6.5.
REFUSAL_MESSAGE = (
    "Maaf, informasi mengenai hal tersebut tidak tersedia pada dokumen resmi "
    "publik LPK MBJ Indonesia. Silakan konsultasikan langsung dengan admin kami "
    "via WhatsApp."
)

#: Strict system prompt from PRD section 6.5.
SYSTEM_PROMPT = """Anda adalah asisten virtual resmi LPK Matahari Bulan Jepang Indonesia (MBJ Indonesia).
Tugas Anda adalah menjawab pertanyaan calon peserta magang dan SSW HANYA berdasarkan konteks dokumen resmi yang disertakan.

ATURAN KETAT:
1. Jawab HANYA menggunakan fakta yang tertulis eksplisit pada konteks di bawah.
2. JANGAN PERNAH menyimpulkan, mengasumsikan, atau menambahkan informasi dari pengetahuan luar Anda.
3. Jika konteks yang diberikan TIDAK MEMUAT jawaban yang ditanyakan, Anda WAJIB menjawab persis dengan kalimat:
   "Maaf, informasi mengenai hal tersebut tidak tersedia pada dokumen resmi publik LPK MBJ Indonesia. Silakan konsultasikan langsung dengan admin kami via WhatsApp."
4. Tuliskan jawaban dalam Bahasa Indonesia yang formal, ramah, dan ringkas.
5. Cantumkan rujukan nama dokumen sumber pada akhir jawaban dalam format: [Sumber: Nama Dokumen/File].
"""

_CITATION_PATTERN = re.compile(r"\[Sumber:\s*([^\]\n]+?)\s*\]", re.IGNORECASE)
_WHITESPACE_PATTERN = re.compile(r"\s+")

_REPO_ROOT = Path(__file__).resolve().parents[2]
_ENV_FILES = (_REPO_ROOT / ".env", _REPO_ROOT / "rag_service" / ".env")
_env_loaded = False


class GeneratorError(RuntimeError):
    """Raised when the generator cannot produce a valid completion."""


def _load_env_files_once() -> None:
    """Load API keys from the project .env files without overriding real env vars."""
    global _env_loaded
    if _env_loaded:
        return
    _env_loaded = True
    if load_dotenv is None:
        return
    for env_path in _ENV_FILES:
        if env_path.exists():
            load_dotenv(env_path, override=False)


def _normalize_whitespace(text: str) -> str:
    return _WHITESPACE_PATTERN.sub(" ", (text or "").strip())


def _as_chunk(chunk: Union[RetrievedChunk, Dict[str, Any]]) -> RetrievedChunk:
    if isinstance(chunk, RetrievedChunk):
        return chunk
    if isinstance(chunk, dict):
        return RetrievedChunk.from_record(chunk)
    raise TypeError(f"unsupported chunk type: {type(chunk)!r}")


@dataclass(frozen=True)
class GenerationConfig:
    """Locked generation parameters for the chatbot."""

    model_name: str = DEFAULT_MODEL_NAME
    base_url: str = DEFAULT_BASE_URL
    api_key_env: str = DEFAULT_API_KEY_ENV
    temperature: float = 0.0
    max_output_tokens: int = 600
    seed: Optional[int] = None
    disable_thinking: bool = True
    timeout_seconds: float = 30.0
    max_retries: int = 2

    def __post_init__(self) -> None:
        if not self.model_name or not self.model_name.strip():
            raise ValueError("model_name must not be empty")
        if not self.base_url.startswith(("http://", "https://")):
            raise ValueError(f"base_url must be an HTTP(S) URL, got {self.base_url!r}")
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError(
                f"temperature must be between 0 and 2, got {self.temperature}"
            )
        if self.max_output_tokens <= 0:
            raise ValueError(
                f"max_output_tokens must be positive, got {self.max_output_tokens}"
            )
        if self.seed is not None and self.seed < 0:
            raise ValueError(f"seed must be non-negative, got {self.seed}")
        if self.timeout_seconds <= 0:
            raise ValueError(
                f"timeout_seconds must be positive, got {self.timeout_seconds}"
            )
        if self.max_retries < 0:
            raise ValueError(f"max_retries must be non-negative, got {self.max_retries}")

    @classmethod
    def from_env(cls, **overrides: Any) -> "GenerationConfig":
        """Build a config from environment variables, then apply overrides."""
        _load_env_files_once()
        values: Dict[str, Any] = {
            "model_name": os.getenv("GENERATOR_MODEL", DEFAULT_MODEL_NAME),
            "base_url": os.getenv("GENERATOR_BASE_URL", DEFAULT_BASE_URL),
            "api_key_env": os.getenv("GENERATOR_API_KEY_ENV", DEFAULT_API_KEY_ENV),
            "temperature": float(os.getenv("GENERATOR_TEMPERATURE", "0.0")),
            "max_output_tokens": int(os.getenv("GENERATOR_MAX_OUTPUT_TOKENS", "600")),
        }
        raw_seed = os.getenv("GENERATOR_SEED")
        if raw_seed:
            values["seed"] = int(raw_seed)
        values.update(overrides)
        return cls(**values)


@dataclass(frozen=True)
class GenerationResult:
    """Answer plus the metadata needed for audit and evaluation."""

    answer: str
    sources: List[str]
    is_refusal: bool
    requested_model: str
    returned_model: str
    provider: str
    system_fingerprint: Optional[str]
    created_at: int
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float
    snapshot: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-serializable dictionary."""
        return {
            "answer": self.answer,
            "sources": list(self.sources),
            "is_refusal": self.is_refusal,
            "requested_model": self.requested_model,
            "returned_model": self.returned_model,
            "provider": self.provider,
            "system_fingerprint": self.system_fingerprint,
            "created_at": self.created_at,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "latency_ms": self.latency_ms,
            "snapshot": dict(self.snapshot),
        }


class GeneratorClient:
    """Call the locked generator model with the strict refusal prompt."""

    def __init__(
        self,
        config: Optional[GenerationConfig] = None,
        client: Optional[Any] = None,
        api_key: Optional[str] = None,
    ):
        self.config = config or GenerationConfig.from_env()
        self._client = client
        self._explicit_api_key = api_key

        if client is None:
            self._client = self._build_client()

    def _build_client(self) -> Any:
        if not HAS_OPENAI:
            raise GeneratorError(
                "openai SDK is not installed; install rag_service/requirements.txt"
            )
        _load_env_files_once()
        api_key = self._explicit_api_key or os.getenv(self.config.api_key_env)
        if not api_key:
            raise GeneratorError(
                f"{self.config.api_key_env} is not set. Add it to the project .env "
                f"or export it before running the RAG service."
            )
        return OpenAI(
            api_key=api_key,
            base_url=self.config.base_url,
            timeout=self.config.timeout_seconds,
            max_retries=self.config.max_retries,
        )

    @staticmethod
    def build_context(chunks: Sequence[Union[RetrievedChunk, Dict[str, Any]]]) -> str:
        """Render retrieved chunks as numbered passages with their source titles."""
        blocks: List[str] = []
        for index, raw_chunk in enumerate(chunks, start=1):
            chunk = _as_chunk(raw_chunk)
            title = chunk.source_title or chunk.doc_id or "Dokumen Publik"
            blocks.append(f"[{index}] Sumber: {title}\n{chunk.content.strip()}")
        return "\n\n".join(blocks)

    @staticmethod
    def _extract_sources(answer: str) -> List[str]:
        """Return deduplicated source names cited as ``[Sumber: ...]``."""
        sources: List[str] = []
        for match in _CITATION_PATTERN.findall(answer or ""):
            name = match.strip().strip("[]").strip()
            if name and name not in sources:
                sources.append(name)
        return sources

    def snapshot_metadata(self) -> Dict[str, Any]:
        """Describe the locked generator identity before any call is made."""
        return {
            "provider": "Token Harbor (OpenAI-compatible gateway)",
            "base_url": self.config.base_url,
            "requested_model": self.config.model_name,
            "model_snapshot": "rolling free route (no dated snapshot)",
            "temperature": self.config.temperature,
            "seed": self.config.seed,
            "thinking": "disabled" if self.config.disable_thinking else "enabled",
            "max_output_tokens": self.config.max_output_tokens,
        }

    def _request_kwargs(self, question: str, context: str) -> Dict[str, Any]:
        user_content = (
            "KONTEKS DOKUMEN RESMI:\n"
            f"{context}\n\n"
            "PERTANYAAN PENGGUNA:\n"
            f"{question}\n\n"
            "Jawab hanya berdasarkan konteks di atas."
        )
        kwargs: Dict[str, Any] = {
            "model": self.config.model_name,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_output_tokens,
        }
        if self.config.seed is not None:
            kwargs["seed"] = self.config.seed
        if self.config.disable_thinking:
            # DeepSeek V4: without this, temperature is ignored and latency
            # balloons because the model reasons before answering.
            kwargs["extra_body"] = {"thinking": {"type": "disabled"}}
        return kwargs

    def _create_completion(self, question: str, context: str) -> Any:
        kwargs = self._request_kwargs(question, context)
        try:
            return self._client.chat.completions.create(**kwargs)
        except Exception as exc:
            if (
                "extra_body" in kwargs
                and BadRequestError is not None
                and isinstance(exc, BadRequestError)
                and self._looks_like_unsupported_param(exc)
            ):
                logger.warning(
                    "Gateway rejected the `thinking` parameter; retrying without it. "
                    "temperature=0.0 may be ignored by thinking models."
                )
                kwargs.pop("extra_body")
                try:
                    return self._client.chat.completions.create(**kwargs)
                except Exception as retry_exc:  # pragma: no cover - network path
                    raise GeneratorError(
                        f"generator request failed: {retry_exc}"
                    ) from retry_exc
            raise GeneratorError(f"generator request failed: {exc}") from exc

    @staticmethod
    def _looks_like_unsupported_param(exc: Exception) -> bool:
        message = str(exc).lower()
        markers = ("thinking", "reasoning", "unknown", "unexpected", "extra field")
        return any(marker in message for marker in markers)

    def generate(
        self,
        question: str,
        chunks: Sequence[Union[RetrievedChunk, Dict[str, Any]]],
    ) -> GenerationResult:
        """Answer ``question`` using only ``chunks`` as context."""
        if not question or not question.strip():
            raise ValueError("question must not be empty")

        context = self.build_context(chunks)
        started = time.perf_counter()

        if not context.strip():
            return self._refusal_result(started, reason="empty_context")

        response = self._create_completion(question.strip(), context)
        latency_ms = (time.perf_counter() - started) * 1000.0

        choice = response.choices[0] if getattr(response, "choices", None) else None
        message = getattr(choice, "message", None) if choice else None
        answer = (getattr(message, "content", None) or "").strip()
        if not answer:
            raise GeneratorError("generator returned an empty completion")

        usage = getattr(response, "usage", None)
        prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
        completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
        returned_model = str(getattr(response, "model", "") or self.config.model_name)
        fingerprint = getattr(response, "system_fingerprint", None)
        created_at = int(getattr(response, "created", 0) or 0)

        if returned_model != self.config.model_name:
            logger.warning(
                "Gateway served model %r, expected %r",
                returned_model,
                self.config.model_name,
            )

        is_refusal = _normalize_whitespace(REFUSAL_MESSAGE) in _normalize_whitespace(
            answer
        )
        sources = [] if is_refusal else self._extract_sources(answer)

        snapshot = {
            **self.snapshot_metadata(),
            "returned_model": returned_model,
            "system_fingerprint": fingerprint,
            "execution_date": datetime.now(timezone.utc).isoformat(),
            "citation_missing": bool(not is_refusal and not sources),
        }

        return GenerationResult(
            answer=answer,
            sources=sources,
            is_refusal=is_refusal,
            requested_model=self.config.model_name,
            returned_model=returned_model,
            provider="tokenharbor",
            system_fingerprint=fingerprint,
            created_at=created_at,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
            snapshot=snapshot,
        )

    def _refusal_result(
        self, started: float, reason: str
    ) -> GenerationResult:
        """Return the canonical refusal without spending a generation call."""
        return GenerationResult(
            answer=REFUSAL_MESSAGE,
            sources=[],
            is_refusal=True,
            requested_model=self.config.model_name,
            returned_model=self.config.model_name,
            provider="tokenharbor",
            system_fingerprint=None,
            created_at=0,
            prompt_tokens=0,
            completion_tokens=0,
            latency_ms=(time.perf_counter() - started) * 1000.0,
            snapshot={
                **self.snapshot_metadata(),
                "execution_date": datetime.now(timezone.utc).isoformat(),
                "refusal_reason": reason,
            },
        )
