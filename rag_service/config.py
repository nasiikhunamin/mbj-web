"""Experiment configuration loader for E01-E16 (Task 2.13 / 2.15).

The pipeline is driven entirely by YAML so the 4x4 factorial design stays
reproducible. This module turns an experiment YAML (Appendix B of the PRD) into
an immutable :class:`ExperimentConfig` shared by the pipeline, the API, and the
experiment runner.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

import yaml

from rag_service.llm.generator import (
    DEFAULT_API_KEY_ENV,
    DEFAULT_BASE_URL,
    DEFAULT_MODEL_NAME,
    GenerationConfig,
)

CONFIG_DIR = Path(__file__).resolve().parent / "configs"

CHUNKING_STRATEGIES = ("fixed", "recursive", "semantic", "structure_aware")
RETRIEVAL_METHODS = ("dense", "sparse_bm25", "hybrid_rrf", "hybrid_rerank")
LOCKED_TOKEN_LIMIT = 512
LOCKED_TOKEN_OVERLAP = 50
LOCKED_RRF_K = 60
LOCKED_FINAL_TOP_N = 5
LOCKED_INITIAL_CANDIDATES = 20

_HYBRID_METHODS = ("hybrid_rrf", "hybrid_rerank")

_METHOD_ALIASES = {
    "dense": "dense",
    "sparse": "sparse_bm25",
    "sparse_bm25": "sparse_bm25",
    "bm25": "sparse_bm25",
    "hybrid": "hybrid_rrf",
    "hybrid_rrf": "hybrid_rrf",
    "hybrid_rerank": "hybrid_rerank",
    "hybrid+rerank": "hybrid_rerank",
}


class ConfigError(ValueError):
    """Raised when an experiment configuration is invalid or incomplete."""


def _require_mapping(value: Any, name: str) -> Dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ConfigError(f"section `{name}` must be a mapping, got {type(value).__name__}")
    return value


def _positive_int(value: Any, name: str) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"`{name}` must be an integer, got {value!r}") from exc
    if number <= 0:
        raise ConfigError(f"`{name}` must be positive, got {number}")
    return number


def _parse_generation(raw: Dict[str, Any]) -> GenerationConfig:
    """Map the YAML ``generation`` block onto :class:`GenerationConfig`."""
    raw = _require_mapping(raw, "generation")
    model_name = raw.get("model_name") or raw.get("model") or DEFAULT_MODEL_NAME
    max_output = raw.get("max_output_tokens", raw.get("max_tokens", 600))
    seed = raw.get("seed")
    return GenerationConfig(
        model_name=str(model_name),
        base_url=str(raw.get("base_url") or DEFAULT_BASE_URL),
        api_key_env=str(raw.get("api_key_env") or DEFAULT_API_KEY_ENV),
        temperature=float(raw.get("temperature", 0.0)),
        max_output_tokens=int(max_output),
        seed=None if seed is None else int(seed),
        disable_thinking=bool(raw.get("disable_thinking", True)),
        timeout_seconds=float(raw.get("timeout_seconds", 30.0)),
        max_retries=int(raw.get("max_retries", 2)),
    )


@dataclass(frozen=True)
class ExperimentConfig:
    """Immutable, validated description of one factorial experiment (E01-E16)."""

    code: str
    chunking_strategy: str
    retrieval_method: str
    description: str = ""
    version: str = ""
    execution_date: str = ""
    token_limit: int = 512
    token_overlap: int = 50
    tokenizer_model: str = "intfloat/multilingual-e5-base"
    embedding_model: str = "intfloat/multilingual-e5-base"
    initial_candidates: int = 20
    rrf_k: int = 60
    final_top_n: int = 5
    reranker_enabled: bool = False
    reranker_model: str = "BAAI/bge-reranker-v2-m3"
    reranker_top_n: int = 5
    chroma_directory: str = "data/vectordb/chroma"
    bm25_directory: str = "data/vectordb/bm25"
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not self.code or not self.code.strip():
            raise ConfigError("experiment code must not be empty")
        if self.chunking_strategy not in CHUNKING_STRATEGIES:
            raise ConfigError(
                f"unknown chunking strategy {self.chunking_strategy!r}; "
                f"expected one of {CHUNKING_STRATEGIES}"
            )
        if self.retrieval_method not in RETRIEVAL_METHODS:
            raise ConfigError(
                f"unknown retrieval method {self.retrieval_method!r}; "
                f"expected one of {RETRIEVAL_METHODS}"
            )
        if self.token_limit <= 0:
            raise ConfigError("token_limit must be positive")
        if not 0 <= self.token_overlap < self.token_limit:
            raise ConfigError("token_overlap must be >= 0 and smaller than token_limit")
        if self.initial_candidates < self.final_top_n:
            raise ConfigError(
                "initial_candidates must be >= final_top_n "
                f"({self.initial_candidates} < {self.final_top_n})"
            )
        if self.reranker_enabled and self.retrieval_method != "hybrid_rerank":
            raise ConfigError(
                "reranker_enabled=true is only valid for retrieval_method=hybrid_rerank"
            )
        if self.retrieval_method == "hybrid_rerank" and not self.reranker_enabled:
            raise ConfigError(
                "retrieval_method=hybrid_rerank requires reranker_enabled=true"
            )
        if self.reranker_enabled and not 0 < self.reranker_top_n <= self.initial_candidates:
            raise ConfigError(
                "reranker_top_n must be within 1..initial_candidates "
                f"({self.reranker_top_n} not in 1..{self.initial_candidates})"
            )

    @property
    def dense_collection(self) -> str:
        return f"chroma_{self.chunking_strategy}"

    @property
    def bm25_index(self) -> str:
        return f"bm25_{self.chunking_strategy}"

    @classmethod
    def from_dict(
        cls, payload: Dict[str, Any], source: str = "<dict>"
    ) -> "ExperimentConfig":
        """Build a validated config from a parsed YAML mapping."""
        if not isinstance(payload, dict):
            raise ConfigError(f"{source}: configuration root must be a mapping")

        experiment = _require_mapping(payload.get("experiment"), "experiment")
        chunking = _require_mapping(payload.get("chunking"), "chunking")
        embedding = _require_mapping(payload.get("embedding"), "embedding")
        retrieval = _require_mapping(payload.get("retrieval"), "retrieval")
        reranker = _require_mapping(payload.get("reranker"), "reranker")
        storage = _require_mapping(payload.get("storage"), "storage")

        code = str(experiment.get("code") or "").strip()
        if not code:
            raise ConfigError(f"{source}: `experiment.code` is required")

        strategy = str(chunking.get("strategy") or "").strip().replace("-", "_")
        if not strategy:
            raise ConfigError(f"{source}: `chunking.strategy` is required")

        raw_method = str(retrieval.get("method") or "").strip().lower()
        method = _METHOD_ALIASES.get(raw_method)
        if method is None:
            raise ConfigError(
                f"{source}: unknown retrieval method {raw_method!r}; "
                f"expected one of {RETRIEVAL_METHODS}"
            )

        expected_dense = f"chroma_{strategy}"
        declared_dense = retrieval.get("dense_collection")
        if declared_dense and declared_dense != expected_dense:
            raise ConfigError(
                f"{source}: dense_collection {declared_dense!r} does not match "
                f"chunking strategy {strategy!r} (expected {expected_dense!r})"
            )

        expected_bm25 = f"bm25_{strategy}"
        declared_bm25 = retrieval.get("bm25_index")
        if declared_bm25 and declared_bm25 != expected_bm25:
            raise ConfigError(
                f"{source}: bm25_index {declared_bm25!r} does not match "
                f"chunking strategy {strategy!r} (expected {expected_bm25!r})"
            )

        reranker_enabled = bool(reranker.get("enabled", method == "hybrid_rerank"))

        return cls(
            code=code,
            chunking_strategy=strategy,
            retrieval_method=method,
            description=str(experiment.get("description") or ""),
            version=str(experiment.get("version") or ""),
            execution_date=str(experiment.get("execution_date") or ""),
            token_limit=int(chunking.get("token_limit", 512)),
            token_overlap=int(chunking.get("token_overlap", 50)),
            tokenizer_model=str(
                chunking.get("tokenizer_model", "intfloat/multilingual-e5-base")
            ),
            embedding_model=str(
                embedding.get(
                    "model_name",
                    chunking.get("tokenizer_model", "intfloat/multilingual-e5-base"),
                )
            ),
            initial_candidates=_positive_int(
                retrieval.get("initial_candidates", 20), "retrieval.initial_candidates"
            ),
            rrf_k=_positive_int(retrieval.get("rrf_k", 60), "retrieval.rrf_k"),
            final_top_n=_positive_int(
                retrieval.get("final_top_n", 5), "retrieval.final_top_n"
            ),
            reranker_enabled=reranker_enabled,
            reranker_model=str(
                reranker.get("model_name", "BAAI/bge-reranker-v2-m3")
            ),
            reranker_top_n=int(reranker.get("top_n", 5)),
            chroma_directory=str(
                storage.get("chroma_directory", "data/vectordb/chroma")
            ),
            bm25_directory=str(storage.get("bm25_directory", "data/vectordb/bm25")),
            generation=_parse_generation(payload.get("generation")),
            raw=payload,
        )

    @classmethod
    def from_yaml(cls, path: Union[str, Path]) -> "ExperimentConfig":
        """Load and validate an experiment YAML file."""
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"configuration file not found: {config_path}")
        with config_path.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle)
        return cls.from_dict(payload or {}, source=str(config_path))


def config_directory() -> Path:
    """Return the directory that holds the E01-E16 YAML files."""
    return Path(os.getenv("RAG_CONFIG_DIR", CONFIG_DIR))


def available_configs() -> List[str]:
    """List the experiment codes that have a YAML file."""
    directory = config_directory()
    if not directory.exists():
        return []
    return sorted(path.stem for path in directory.glob("E*.yaml"))


def expected_experiment_matrix() -> Dict[str, Tuple[str, str]]:
    """Return the locked 4x4 mapping ``code -> (chunking, retrieval)``.

    The PRD numbers experiments row-major: E01-E04 are the four retrieval
    methods on Fixed-Size, E05-E08 on Recursive, E09-E12 on Semantic, and
    E13-E16 on Structure-Aware.
    """
    matrix: Dict[str, Tuple[str, str]] = {}
    for chunk_index, chunking in enumerate(CHUNKING_STRATEGIES):
        for retrieval_index, retrieval in enumerate(RETRIEVAL_METHODS):
            code = f"E{chunk_index * len(RETRIEVAL_METHODS) + retrieval_index + 1:02d}"
            matrix[code] = (chunking, retrieval)
    return matrix


def _validate_locked_values(code: str, config: "ExperimentConfig") -> List[str]:
    """Check the parameters that must be identical across all 16 runs."""
    errors: List[str] = []
    expected = expected_experiment_matrix()[code]

    if config.code != code:
        errors.append(f"{code}: experiment.code is {config.code!r}")
    if config.chunking_strategy != expected[0]:
        errors.append(
            f"{code}: chunking strategy is {config.chunking_strategy!r}, "
            f"expected {expected[0]!r}"
        )
    if config.retrieval_method != expected[1]:
        errors.append(
            f"{code}: retrieval method is {config.retrieval_method!r}, "
            f"expected {expected[1]!r}"
        )

    if config.token_limit != LOCKED_TOKEN_LIMIT:
        errors.append(f"{code}: token_limit must be {LOCKED_TOKEN_LIMIT}")
    if config.token_overlap != LOCKED_TOKEN_OVERLAP:
        errors.append(f"{code}: token_overlap must be {LOCKED_TOKEN_OVERLAP}")
    if config.tokenizer_model != "intfloat/multilingual-e5-base":
        errors.append(f"{code}: tokenizer_model must be intfloat/multilingual-e5-base")
    if config.embedding_model != "intfloat/multilingual-e5-base":
        errors.append(f"{code}: embedding model must be intfloat/multilingual-e5-base")
    if config.rrf_k != LOCKED_RRF_K:
        errors.append(f"{code}: rrf_k must be {LOCKED_RRF_K}")
    if config.final_top_n != LOCKED_FINAL_TOP_N:
        errors.append(f"{code}: final_top_n must be {LOCKED_FINAL_TOP_N}")

    expected_candidates = (
        LOCKED_INITIAL_CANDIDATES
        if config.retrieval_method in _HYBRID_METHODS
        else LOCKED_FINAL_TOP_N
    )
    if config.initial_candidates != expected_candidates:
        errors.append(
            f"{code}: initial_candidates must be {expected_candidates} "
            f"for retrieval_method={config.retrieval_method}"
        )

    expects_reranker = config.retrieval_method == "hybrid_rerank"
    if config.reranker_enabled != expects_reranker:
        errors.append(
            f"{code}: reranker_enabled must be {expects_reranker} "
            f"for retrieval_method={config.retrieval_method}"
        )
    if expects_reranker and config.reranker_model != "BAAI/bge-reranker-v2-m3":
        errors.append(f"{code}: reranker model must be BAAI/bge-reranker-v2-m3")
    if expects_reranker and config.reranker_top_n != 5:
        errors.append(f"{code}: reranker top_n must be 5")

    embedding = config.raw.get("embedding") or {}
    if embedding.get("dimension") != 768:
        errors.append(f"{code}: embedding.dimension must be 768")
    if embedding.get("prefix_document") != "passage: ":
        errors.append(f"{code}: embedding.prefix_document must be 'passage: '")
    if embedding.get("prefix_query") != "query: ":
        errors.append(f"{code}: embedding.prefix_query must be 'query: '")

    retrieval = config.raw.get("retrieval") or {}
    if retrieval.get("bm25_stemming") is not True:
        errors.append(f"{code}: retrieval.bm25_stemming must be true")
    if retrieval.get("bm25_language") != "indonesian":
        errors.append(f"{code}: retrieval.bm25_language must be 'indonesian'")

    generation = config.raw.get("generation") or {}
    if generation.get("model_name") != DEFAULT_MODEL_NAME:
        errors.append(f"{code}: generator must be {DEFAULT_MODEL_NAME}")
    if float(generation.get("temperature", 0.0)) != 0.0:
        errors.append(f"{code}: generator temperature must be 0.0")

    evaluation = config.raw.get("evaluation") or {}
    expected_output = f"data/results/{code}_results.json"
    if evaluation.get("output_results_path") != expected_output:
        errors.append(
            f"{code}: evaluation.output_results_path must be {expected_output}"
        )

    return errors


def validate_configs(directory: Union[str, Path, None] = None) -> List[str]:
    """Validate all 16 experiment YAML files and return a list of errors.

    An empty list means the 4x4 matrix is complete, every file loads through
    :class:`ExperimentConfig`, and the locked parameters match the PRD.
    """
    target = Path(directory) if directory is not None else config_directory()
    if not target.exists():
        return [f"configuration directory not found: {target}"]

    expected = expected_experiment_matrix()
    present = {path.stem for path in target.glob("E*.yaml")}
    errors: List[str] = []

    missing = sorted(set(expected) - present)
    unexpected = sorted(present - set(expected))
    if missing:
        errors.append(f"missing configuration files: {', '.join(missing)}")
    if unexpected:
        errors.append(f"unexpected configuration files: {', '.join(unexpected)}")

    for code in sorted(expected):
        path = target / f"{code}.yaml"
        if not path.exists():
            continue
        try:
            config = ExperimentConfig.from_yaml(path)
        except Exception as exc:  # noqa: BLE001 - report all config problems
            errors.append(f"{code}: invalid YAML/config: {exc}")
            continue
        errors.extend(_validate_locked_values(code, config))

    return errors


def resolve_config_path(code: str) -> Path:
    """Map an experiment code (``E16``) or path to a YAML file."""
    candidate = Path(code)
    if candidate.suffix in (".yaml", ".yml") or candidate.exists():
        return candidate
    path = config_directory() / f"{code}.yaml"
    if not path.exists():
        available = ", ".join(available_configs()) or "(none)"
        raise FileNotFoundError(
            f"no configuration for {code!r} in {config_directory()} "
            f"(available: {available})"
        )
    return path


def load_config(source: Union[str, Path]) -> ExperimentConfig:
    """Load a config from a YAML path or an experiment code like ``E16``."""
    return ExperimentConfig.from_yaml(resolve_config_path(str(source)))
