"""Compare candidate RAGAS judge models on a faithfulness-style task.

Uses the same dynamic :class:`~rag_service.evaluation.JudgeClient` as the real
evaluation, so whatever is reported here is what the pipeline will do. Model id
and base URL come from ``JUDGE_MODEL`` / ``JUDGE_BASE_URL`` for the first
candidate; the rest are probed with explicit overrides for comparison.

Only models with an active ``:free`` route on Token Harbor are usable with the
current account — see ``scripts/probe_free_routes.py``.

Usage:
    .venv310/bin/python scripts/probe_judge_models.py
    JUDGE_MODEL=mimo-v2.6-flash:free .venv310/bin/python scripts/probe_judge_models.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag_service.evaluation.judge import (  # noqa: E402
    JudgeClient,
    JudgeConfig,
    JudgeError,
    model_family,
)

# Context supports the first three claims but NOT the registration fee.
CONTEXT = (
    "Calon peserta program magang LPK MBJ Indonesia harus berusia 18 sampai 30 tahun "
    "dan berpendidikan minimal SMA/SMK. Pendaftaran dilakukan melalui halaman /daftar "
    "dengan melampirkan KTP, ijazah, dan pas foto."
)
ANSWER = (
    "Syarat usia peserta magang adalah 18 sampai 30 tahun. Pendidikan minimal SMA/SMK. "
    "Pendaftar wajib melampirkan KTP dan ijazah, serta membayar biaya pendaftaran Rp500.000."
)
UNSUPPORTED_MARKER = "biaya pendaftaran"

PROMPT = f"""Tugas: ekstraksi klaim faktual atomik.

KONTEKS:
{CONTEXT}

JAWABAN:
{ANSWER}

Pecah jawaban menjadi klaim atomik. Untuk setiap klaim, tentukan apakah didukung konteks.
Balas HANYA JSON valid dengan skema:
{{"claims": [{{"claim": "...", "supported": true}}]}}"""

# First entry is the configured judge; the rest are free-route alternatives.
CANDIDATES = [
    None,  # -> JUDGE_MODEL from the environment
    "mimo-v2.6-flash:free",
    "mimo-v2.5:free",
    "deepseek-v4-flash:free",
]
REPEATS = 3


def probe(model_name, index):
    config = JudgeConfig.from_env(allow_same_family=True)
    label = model_name or config.model_name
    if model_name:
        config = JudgeConfig.from_env(model_name=model_name, allow_same_family=True)

    client = JudgeClient(config=config)

    json_ok = caught = 0
    latencies = []
    print(f"\n--- [{index}] {label}  (family={client.family}, endpoint={config.base_url}) ---")

    for attempt in range(1, REPEATS + 1):
        try:
            result = client.complete_json(PROMPT)
            json_ok += 1
            latencies.append(result.latency_ms)
            claims = (result.data or {}).get("claims") or []
            unsupported = [c.get("claim") for c in claims if c.get("supported") is False]
            hit = any(UNSUPPORTED_MARKER in (c or "").lower() for c in unsupported)
            caught += int(hit)
            print(
                f"  #{attempt} {result.latency_ms/1000:5.1f}s  JSON ok, {len(claims)} klaim, "
                f"menandai klaim tak didukung: {hit} (percobaan ke-{result.attempts})"
            )
            if not hit:
                print(f"      supported=false -> {unsupported or '(kosong)'}")
        except JudgeError as exc:
            print(f"  #{attempt} GAGAL: {str(exc)[:120]}")

    if latencies:
        average = sum(latencies) / len(latencies) / 1000
        print(
            f"  ringkas: JSON valid {json_ok}/{REPEATS}, menangkap halusinasi {caught}/{REPEATS}, "
            f"latensi rata-rata {average:.1f}s"
        )
    return json_ok, caught


def main() -> int:
    print(f"Generator family (tidak boleh dipakai juri): "
          f"{model_family('deepseek-v4.1-flash:free')}")
    failed = 0
    for index, model_name in enumerate(CANDIDATES, start=1):
        try:
            json_ok, caught = probe(model_name, index)
        except JudgeError as exc:
            print(f"\n--- [{index}] {model_name or 'env'} TIDAK BISA DIPAKAI: {str(exc)[:120]}")
            failed += 1
            continue
        if json_ok < REPEATS or caught < REPEATS:
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
