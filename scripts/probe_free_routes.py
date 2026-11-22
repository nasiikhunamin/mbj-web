"""List every Token Harbor model whose :free route is currently active."""
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
for env_file in (ROOT / ".env", ROOT / "rag_service" / ".env"):
    if env_file.exists():
        load_dotenv(env_file, override=False)

client = OpenAI(api_key=os.environ["TOKENHARBOR_API_KEY"], base_url="https://tokenharbor.ai/v1")

models = sorted(m.id for m in client.models.list().data if m.id)
active, inactive, paid_only = [], [], []

for model in models:
    if model.endswith(":free"):
        continue
    try:
        response = client.chat.completions.create(
            model=f"{model}:free",
            max_tokens=4,
            messages=[{"role": "user", "content": "ping"}],
        )
        active.append((model, response.model))
        print(f"FREE OK   {model}")
    except Exception as exc:
        message = str(exc)
        if "402" in message or "No active plan" in message:
            paid_only.append(model)
        else:
            inactive.append(model)
    time.sleep(0.15)

print("\n===== RINGKASAN =====")
print(f"total model di gateway      : {len(models)}")
print(f"rute :free AKTIF            : {len(active)}  -> {[m for m, _ in active]}")
print(f"rute :free TIDAK aktif      : {len(inactive)}")
print(f"butuh plan berbayar (402)   : {len(paid_only)}")

print("\n=== rute :free yang benar-benar bisa dipakai ===")
for model, served in active:
    print(f"  diminta={model:26s} dilayani={served}")
