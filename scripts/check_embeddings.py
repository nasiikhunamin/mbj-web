#!/usr/bin/env python3
"""Pre-run guard: make sure the real E5 encoder and BGE reranker can load.

The pipeline uses ``allow_fallback=True`` internally, so if the GPU is occupied
or the model is missing it silently swaps in a dummy hashed embedder / lexical
reranker — the experiment still "succeeds" but the numbers are meaningless.

This script forces ``allow_fallback=False`` so a failure is loud. Run it before
``scripts/run_experiments.py``.

Usage:
    .venv310/bin/python scripts/check_embeddings.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    ok = True

    print("[1/2] E5 embedding model (intfloat/multilingual-e5-base)...")
    try:
        from rag_service.embeddings.e5_encoder import E5Encoder

        encoder = E5Encoder(allow_fallback=False)
        vec = encoder.embed_query("uji")
        print(f"      backend : {encoder.backend}")
        print(f"      dim     : {len(vec)}")
        if encoder.backend != "sentence-transformers":
            ok = False
            print("      HASIL  : BUKAN model asli (fallback)")
    except Exception as exc:  # noqa: BLE001
        ok = False
        print(f"      GAGAL   : {type(exc).__name__}: {exc}")

    print("[2/2] BGE reranker (BAAI/bge-reranker-v2-m3)...")
    try:
        from rag_service.rerankers.bge_reranker import BGEReranker

        reranker = BGEReranker(allow_fallback=False)
        print(f"      backend : {reranker.backend}")
        if reranker.backend != "cross-encoder":
            ok = False
            print("      HASIL  : BUKAN cross-encoder (fallback)")
    except Exception as exc:  # noqa: BLE001
        ok = False
        print(f"      GAGAL   : {type(exc).__name__}: {exc}")

    if ok:
        print("\nOK: E5 + reranker aktif (model asli). Aman menjalankan experiment.")
        return 0
    print(
        "\nSTOP: model gagal dimuat / fallback aktif.\n"
        "Pastikan tidak ada proses 'uvicorn' memakai GPU, lalu ulangi.\n"
        "Cek: pgrep -af uvicorn  &&  nvidia-smi"
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
