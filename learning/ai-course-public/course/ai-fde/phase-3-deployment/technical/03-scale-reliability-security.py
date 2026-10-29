"""
T3 — Scale, reliability, and security failure handling (lesson-runnable shim).

This file exists so the lesson is runnable as
`python3 technical/03-scale-reliability-security.py`. It runs the three
demos from `service/circuit.py` and adds a "trip the breaker" walkthrough
that mirrors what happens during a real OpenAI outage.

How to run:
    python3 technical/03-scale-reliability-security.py

What you should be able to explain after running it:
- The 3 failure modes (silent quality, latency spike, cost spike) and which
  primitive catches each.
- The wrap order: redact → rate-limit → breaker → telemetry, and why.
- The "circuit breaker is observability, not safety" insight — the breaker
  doesn't fix the LLM, it routes around it.

What to read next:
- ../service/circuit.py                          — Redactor, TokenBucketRateLimiter, CircuitBreaker, TTLCache
- ../service/app.py::GET /circuit/state          — the endpoint Daniel hits at 2am
- ../../hardcode/level-9-failure-handling/17-circuit-breaker-llm.py
                                               — the 1072-line production version (pybreaker, retries, etc.)
"""
from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path


def _import_circuit_module():
    """Load ../service/circuit.py as an importable module."""
    svc_dir = Path(__file__).parent.parent / "service"
    if str(svc_dir) not in sys.path:
        sys.path.insert(0, str(svc_dir))
    spec = importlib.util.spec_from_file_location("pf_circuit", svc_dir / "circuit.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["pf_circuit"] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    c = _import_circuit_module()

    print("=" * 70)
    print("T3 — Scale, reliability, and security: the 3 failure-mode primitives")
    print("=" * 70)

    # ----------------------------------------------------------------
    # Demo 1: Redactor
    # ----------------------------------------------------------------
    print("\n--- 1. Redactor (PII stripper — runs BEFORE the LLM call) ---")
    rd = c.Redactor()
    sample = (
        "Hi, please email jane.doe@example.com or call +65 9123 4567. "
        "My passport is A1234567 and I have a backup at jane.doe@pf.com.sg."
    )
    redacted = rd.redact(sample)
    print(f"  before: {sample}")
    print(f"  after : {redacted}")
    print(f"  stats : {rd.stats()}")
    print(
        "  \n  The redactor is dual-purpose: (a) it protects PII, (b) it "
        "shrinks the\n  prompt so the LLM call costs less. The usage.jsonl log line "
        "records\n  n_redactions=N — never the redacted text."
    )

    # ----------------------------------------------------------------
    # Demo 2: Rate limiter
    # ----------------------------------------------------------------
    print("\n--- 2. TokenBucketRateLimiter (capacity=3, refill_rate=1/s) ---")
    print("  Mei has 8 tabs open and triggers 6 drafts in 1 second:")
    rl = c.TokenBucketRateLimiter(capacity=3, refill_rate=1.0)
    for i in range(6):
        ok = rl.try_acquire("mei@pf.com")
        verdict = "ALLOWED" if ok else "REJECTED (429-equivalent)"
        print(f"  draft #{i+1}  {verdict}  (allowed={rl.n_allowed}, rejected={rl.n_rejected})")
    print("\n  After 2s, the bucket refills (refill_rate=1/s × 2s = 2 tokens):")
    time.sleep(2.1)
    for i in range(3):
        ok = rl.try_acquire("mei@pf.com")
        verdict = "ALLOWED" if ok else "REJECTED"
        print(f"  retry #{i+1}  {verdict}  (allowed={rl.n_allowed}, rejected={rl.n_rejected})")
    print(
        "  \n  The rate limiter is cost control, not anti-abuse. With a "
        "single-worker\n  VM (Daniel's setup) the in-process bucket is correct. "
        "With multiple\n  workers, swap to Redis. See the lesson for the caveat."
    )

    # ----------------------------------------------------------------
    # Demo 3: Circuit breaker trip + recovery
    # ----------------------------------------------------------------
    print("\n--- 3. CircuitBreaker (failure_threshold=0.5, min_calls=3) ---")
    print("  Simulating an OpenAI outage: every other call returns 5xx.")
    cfg = c.CircuitBreakerConfig(
        failure_threshold=0.5, min_calls_in_window=3, cooldown_seconds=2.0
    )
    cache = c.TTLCache()
    fb = c.make_tiered_fallback(cache, cheaper_fn=None)
    cb = c.CircuitBreaker(name="openai", fallback=fb, config=cfg)

    def flaky_llm(n: int) -> dict:
        if n % 2 == 0:
            raise RuntimeError("simulated 5xx from OpenAI")
        return {
            "ok": True,
            "draft": f"draft for call {n}",
            "model": "gpt-4o-mini",
            "is_mock": True,
            "cost_usd": 0.0005,
            "latency_ms": 1800,
        }

    print("\n  Initial state:", c.STATE_NAME[cb.state])
    print("  Watch the state machine as failures accumulate:\n")

    for i in range(8):
        try:
            r = cb.call(flaky_llm, i)
            tier = r.get("fallback_tier", "primary")
            draft_preview = (r.get("draft") or "")[:50].replace("\n", " ")
            print(
                f"  call {i}: state={c.STATE_NAME[cb.state]:10s}  "
                f"tier={tier:8s}  draft={draft_preview!r}"
            )
        except Exception as e:
            print(f"  call {i}: state={c.STATE_NAME[cb.state]:10s}  RAISED {type(e).__name__}: {e}")

    print(f"\n  /circuit/state response (what Daniel sees at 2am):")
    snap = cb.snapshot()
    for k, v in snap.items():
        if k == "recent_transitions":
            print(f"    {k}:")
            for t in v:
                print(f"      {t}")
        else:
            print(f"    {k}: {v}")

    # ----------------------------------------------------------------
    # Wrap-up
    # ----------------------------------------------------------------
    print("\n" + "-" * 70)
    print("Key takeaways:")
    print("-" * 70)
    print(
        "1. The 3 primitives are not 3 features — they are one defense in\n"
        "   depth. Each catches what the others miss:\n"
        "     - Redactor  → PII / token cost\n"
        "     - RateLimit → per-user cost ceiling\n"
        "     - Breaker   → routes around outages via 3-tier fallback\n"
        "2. The wrap order (redact → rate-limit → breaker → telemetry) is\n"
        "   deliberate. A rate-limited call shouldn't consume an LLM token\n"
        "   or a breaker slot. A tripped breaker should return fast, not\n"
        "   redact first.\n"
        "3. The breaker is observability, not safety. It tells you the LLM\n"
        "   is degraded; it doesn't fix the LLM. The 3-tier fallback\n"
        "   (cache → cheaper LLM → stub) is what keeps Mei productive\n"
        "   during the 10-min outage.\n"
        "4. The `min_calls_in_window=5` knob prevents the breaker from\n"
        "   tripping on 1-of-1 — a single blip should not open the circuit.\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
