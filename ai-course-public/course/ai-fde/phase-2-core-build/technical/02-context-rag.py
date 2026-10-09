"""
Lesson 02 — Context engineering and RAG foundations.

What this file does
-------------------
This is the *lesson* version of the RAG module. The full module lives
in `../service/rag.py`. This file:

  1. Imports the full RAG module from `../service/rag.py`.
  2. Runs 4 worked examples that show what retrieval looks like for
     different queries, and how `build_rag_prompt` composes the final
     system prompt.

How to run
----------
    python3 02-context-rag.py

What you should be able to explain to a client after this lesson
----------------------------------------------------------------
- Why we chunk the style guide (don't paste 130 lines into every prompt).
- Why a mock vector store is the right call for Phase 2 (deterministic,
  no API keys, same interface as Pinecone for the demo).
- Why the retrieval score is F1 with a length bonus, not raw overlap.
- Why `build_rag_prompt` puts the persona first and the email last.

What to read next
-----------------
- 03-eval-reliability.md / .py — how to measure if RAG is actually working
- ../service/rag.py — the production version of this code
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _import_rag_module():
    """Load `../service/rag.py` as a module so the lesson is runnable."""
    rag_path = Path(__file__).parent.parent / "service" / "rag.py"
    spec = importlib.util.spec_from_file_location("pf_rag", rag_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["pf_rag"] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    rag = _import_rag_module()
    store = rag.MockVectorStore()

    print("=" * 70)
    print(f"Vector store loaded: {len(store.chunks)} chunks")
    print(f"  policy chunks  : {sum(1 for c in store.chunks if c.source == 'policy')}")
    print(f"  shipment chunks: {sum(1 for c in store.chunks if c.source == 'shipment')}")
    print()

    # Example 1 — top policy chunks for "customs duty import"
    print("=" * 70)
    print('Query: "customs duty import"  (source_filter=policy, k=3)')
    print("=" * 70)
    for c in store.retrieve("customs duty import", k=3, source_filter="policy"):
        print(f"  [{c.id:20s}] score={c.score:.4f}  {c.metadata.get('section', '?')[:60]}")

    # Example 2 — top shipment chunks for "PF-1003 held at customs"
    print()
    print("=" * 70)
    print('Query: "PF-1003 held at customs"  (source_filter=shipment, k=3)')
    print("=" * 70)
    for c in store.retrieve("PF-1003 held at customs", k=3, source_filter="shipment"):
        meta = c.metadata
        print(f"  [{c.id:25s}] score={c.score:.4f}  status={meta.get('status', '?')}")

    # Example 3 — top chunks (both kinds) for an angry exception email
    print()
    print("=" * 70)
    print('Query: "PF-1004 angry delivery failed exception"  (k=5, both kinds)')
    print("=" * 70)
    for c in store.retrieve("PF-1004 angry delivery failed exception", k=5):
        print(f"  [{c.source:8s}] [{c.id:25s}] score={c.score:.4f}")

    # Example 4 — show the final RAG-augmented system prompt
    print()
    print("=" * 70)
    print("build_rag_prompt example (PF-1003, with retrieved context)")
    print("=" * 70)
    policy = store.retrieve("customs duty held at import", k=2, source_filter="policy")
    shipment = store.retrieve("PF-1003 held at customs", k=1, source_filter="shipment")
    chunks = policy + shipment

    # Use a tiny fake shipment dict to show the prompt shape.
    fake_shipment = {
        "id": "PF-1003",
        "status": "held_customs",
        "customer_name": "Mei Lin",
        "last_event": "Held at Singapore customs",
    }
    prompt = rag.build_rag_prompt(
        base_system="You are PacificFreight's customer-service drafter. Follow the style guide.",
        email="Where is PF-1003? Stuck at customs. — Mei Lin",
        shipment=fake_shipment,
        chunks=chunks,
    )
    # Print just the structure (not the whole text), to keep output small.
    for line in prompt.split("\n"):
        if line.startswith("Retrieved") or line.startswith("Provided") or line.startswith("Customer") or line.startswith("---") or line.startswith("Draft a"):
            print(f"  {line}")
        elif line.startswith("[") and "]" in line and "score=" in line:
            print(f"  {line}")
    print(f"  ... ({len(prompt.split())} total tokens)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
