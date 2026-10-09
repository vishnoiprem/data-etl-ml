"""
Lesson 01 — LLM applications and workflows.

What this file does
-------------------
This is the *lesson* version of the FastAPI service. The full, runnable
service lives in `../service/app.py` (with rag.py + eval.py + tests).
This file:

  1. Imports the full service's `_draft_pipeline` so the lesson is runnable
     end-to-end without the rest of the service being on disk.
  2. Adds a tiny `if __name__ == "__main__"` block so you can
     `python3 01-llm-applications.py` and see a worked example.

How to run
----------
    # From the technical/ directory:
    python3 01-llm-applications.py
    # → prints a sample /health response and a /draft response for PF-1003

    # To boot the actual service, see ../service/app.py and run:
    cd ../service && uvicorn app:app --host 0.0.0.0 --port 8000

What you should be able to explain to a client after this lesson
----------------------------------------------------------------
- Why FastAPI over Flask (async-native, OpenAPI built-in, Pydantic-validated).
- Why a `/health` endpoint is non-negotiable in production.
- Why the Pydantic `DraftResponse` includes `cost_usd` and `latency_ms`
  (the customer asks in the first 10 minutes of the demo).
- Why we reuse Phase 1's `complete()` via importlib instead of
  duplicating the mock-LLM code.

What to read next
-----------------
- 02-context-rag.md / .py — the /retrieve endpoint + RAG
- 03-eval-reliability.md / .py — the /eval endpoint + regression check
- ../service/app.py — the full service this lesson wraps
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _import_service_module():
    """Load the service's `app.py` as a module so we can reuse its pipeline.

    Same importlib pattern as Phase 1's `04-first-ai-tool.py`. The reason:
    we want this lesson file to be runnable as a script, but the actual
    pipeline code lives in `service/app.py` (so the service is one
    place, not three). Importing keeps them in sync.
    """
    service_path = Path(__file__).parent.parent / "service" / "app.py"
    spec = importlib.util.spec_from_file_location("pf_phase2_app", service_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["pf_phase2_app"] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    app_mod = _import_service_module()

    # 1. Simulate GET /health.
    print("=" * 70)
    print("GET /health")
    print("=" * 70)
    n_chunks = len(app_mod._get_vector_store().chunks)
    print(f'{{"ok": true, "service": "pf-phase2", "n_chunks_loaded": {n_chunks}}}')

    # 2. Simulate POST /draft for a known shipment.
    print()
    print("=" * 70)
    print("POST /draft  { email: 'Where is PF-1003?', shipment_id: 'PF-1003' }")
    print("=" * 70)
    DraftRequest = app_mod.DraftRequest
    req = DraftRequest(email="Where is PF-1003?", shipment_id="PF-1003")
    resp = app_mod._draft_pipeline(req)
    print(f"ok            : {resp.ok}")
    print(f"shipment_id   : {resp.shipment_id}")
    print(f"is_mock       : {resp.is_mock}")
    print(f"cost_usd      : {resp.cost_usd}")
    print(f"latency_ms    : {resp.latency_ms}")
    print(f"n_contexts    : {len(resp.contexts)}")
    print(f"context_ids   : {[c.id for c in resp.contexts]}")
    print("--- draft ---")
    print(resp.draft)

    # 3. Simulate POST /draft where the ID is extracted from the email.
    print()
    print("=" * 70)
    print("POST /draft  { email: 'PF-1001 missing! — Aisha' }   (ID auto-extracted)")
    print("=" * 70)
    req2 = DraftRequest(email="PF-1001 missing! — Aisha")
    resp2 = app_mod._draft_pipeline(req2)
    print(f"shipment_id   : {resp2.shipment_id}")
    print("--- draft ---")
    print(resp2.draft)

    # 4. Simulate POST /draft where there is no ID.
    print()
    print("=" * 70)
    print("POST /draft  { email: 'Hi, where is my parcel?' }    (no ID)")
    print("=" * 70)
    req3 = DraftRequest(email="Hi, where is my parcel?")
    resp3 = app_mod._draft_pipeline(req3)
    print(f"shipment_id   : {resp3.shipment_id}")
    print("--- draft ---")
    print(resp3.draft)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
