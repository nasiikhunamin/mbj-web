"""Live smoke test for the Task 2.12 generator client.

Usage (from the repository root)::

    .venv310/bin/python scripts/check_generator.py

Requires ``TOKENHARBOR_API_KEY`` in the project ``.env`` or the environment.
The script checks four things:

1. the gateway accepts the request and echoes a model identity,
2. an in-scope question is answered from the supplied context,
3. an out-of-scope question returns the canonical refusal sentence,
4. a program-cost question redirects to WhatsApp (canonical refusal).
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag_service.llm import REFUSAL_MESSAGE, GenerationConfig, GeneratorClient  # noqa: E402
from rag_service.retrievers import RetrievedChunk  # noqa: E402

PROBE_CHUNK = RetrievedChunk(
    chunk_id="probe-1",
    content=(
        "Calon peserta program magang LPK MBJ Indonesia harus berusia 18 sampai "
        "30 tahun dan berpendidikan minimal SMA/SMK."
    ),
    score=0.0,
    doc_id="probe",
    source_type="web",
    source_title="Panduan Pendaftaran (probe)",
)

COST_PROBE_CHUNK = RetrievedChunk(
    chunk_id="probe-cost",
    content=(
        "Biaya program magang mencakup biaya pendaftaran, pelatihan bahasa Jepang, "
        "pemeriksaan medis, pengurusan visa, dan administrasi lainnya."
    ),
    score=0.0,
    doc_id="probe-cost",
    source_type="web",
    source_title="FAQ (probe)",
)


def main() -> int:
    client = GeneratorClient(config=GenerationConfig.from_env())

    print("Konfigurasi generator:")
    for key, value in client.snapshot_metadata().items():
        print(f"  {key}: {value}")

    print("\n[1] Pertanyaan in-scope...")
    in_scope = client.generate("Apa syarat usia peserta magang?", [PROBE_CHUNK])
    print(f"  jawaban   : {in_scope.answer}")
    print(f"  sumber    : {in_scope.sources or '(tidak ada kutipan)'}")
    print(f"  model     : {in_scope.returned_model}")
    print(f"  fingerprint: {in_scope.system_fingerprint}")
    print(f"  token     : {in_scope.prompt_tokens} in / {in_scope.completion_tokens} out")
    print(f"  latensi   : {in_scope.latency_ms:.0f} ms")

    print("\n[2] Pertanyaan out-of-scope...")
    out_of_scope = client.generate("Siapa presiden Jepang saat ini?", [PROBE_CHUNK])
    print(f"  jawaban   : {out_of_scope.answer}")
    print(f"  penolakan : {out_of_scope.is_refusal}")

    print("\n[3] Pertanyaan biaya program (harus diarahkan ke WhatsApp)...")
    cost = client.generate("Berapa biaya program magang dan bisa dicicil?", [COST_PROBE_CHUNK])
    print(f"  jawaban   : {cost.answer}")
    print(f"  penolakan : {cost.is_refusal}")

    failed = False
    if out_of_scope.answer.strip() != REFUSAL_MESSAGE:
        print("\nGAGAL: jawaban out-of-scope tidak sama persis dengan kalimat penolakan baku.")
        failed = True
    if cost.answer.strip() != REFUSAL_MESSAGE:
        print("\nGAGAL: pertanyaan biaya program tidak diarahkan ke WhatsApp (tidak pakai kalimat baku).")
        failed = True
    if in_scope.is_refusal:
        print("\nGAGAL: pertanyaan in-scope justru ditolak.")
        failed = True
    if not in_scope.sources:
        print("\nPERINGATAN: jawaban in-scope tidak menyertakan format [Sumber: ...].")
    if in_scope.returned_model != client.config.model_name:
        print(
            "\nPERINGATAN: gateway mengembalikan model "
            f"{in_scope.returned_model!r}, diminta {client.config.model_name!r}."
        )

    if failed:
        return 1

    print("\nOK: generator berjalan dan aturan penolakan dipatuhi.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
