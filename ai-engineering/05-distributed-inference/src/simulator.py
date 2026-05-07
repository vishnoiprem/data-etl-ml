"""Inference simulator.

Simulates: realistic difficulty mix, request stream, three strategies:

  S1 = always-Opus baseline (worst)
  S2 = router only (no cache)
  S3 = router + cache (semantic)

Reports cost, latency, and token throughput for each.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable

from src.cache import CacheEntry, SemanticCache
from src.pricing import REGISTRY, cost_usd
from src.router import RouteDecision, classify_difficulty


@dataclass
class SimResult:
    strategy: str
    n_requests: int
    cache_hits: int
    cost_usd: float
    p50_latency_ms: float
    p95_latency_ms: float
    by_model: dict[str, int] = field(default_factory=dict)


def percentile(xs: list[float], p: float) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    k = int(len(s) * p)
    return s[min(k, len(s) - 1)]


def stub_invoke(model_key: str, prompt: str, expected_out: int) -> tuple[int, int, int]:
    """Stub for invoke_model. Returns (in_tokens, out_tokens, latency_ms)."""
    in_tok = max(1, len(prompt.split()))
    out_tok = expected_out
    spec = REGISTRY[model_key]
    # Latency scales mildly with output length
    lat = int(spec.base_latency_ms * (0.6 + 0.4 * (out_tok / 200.0)))
    return in_tok, out_tok, lat


def run_baseline_opus(requests: list[dict]) -> SimResult:
    cost = 0.0
    lat: list[float] = []
    by_model: dict[str, int] = {"opus": 0}
    for r in requests:
        in_t, out_t, l = stub_invoke("opus", r["prompt"], r["expected_out"])
        cost += cost_usd("opus", in_t, out_t)
        lat.append(l)
        by_model["opus"] += 1
    return SimResult(
        strategy="always-Opus", n_requests=len(requests), cache_hits=0, cost_usd=cost,
        p50_latency_ms=percentile(lat, 0.5), p95_latency_ms=percentile(lat, 0.95),
        by_model=by_model,
    )


def run_router_only(requests: list[dict]) -> SimResult:
    cost = 0.0
    lat: list[float] = []
    by_model: dict[str, int] = {}
    for r in requests:
        decision: RouteDecision = classify_difficulty(r["prompt"], r["expected_out"])
        in_t, out_t, l = stub_invoke(decision.model_key, r["prompt"], r["expected_out"])
        cost += cost_usd(decision.model_key, in_t, out_t)
        lat.append(l)
        by_model[decision.model_key] = by_model.get(decision.model_key, 0) + 1
    return SimResult(
        strategy="router-only", n_requests=len(requests), cache_hits=0, cost_usd=cost,
        p50_latency_ms=percentile(lat, 0.5), p95_latency_ms=percentile(lat, 0.95),
        by_model=by_model,
    )


def run_router_with_cache(requests: list[dict]) -> SimResult:
    cache = SemanticCache(max_size=2000)
    cost = 0.0
    lat: list[float] = []
    hits = 0
    by_model: dict[str, int] = {"cache": 0}
    for r in requests:
        decision = classify_difficulty(r["prompt"], r["expected_out"])
        cached = cache.get(r["prompt"], decision.model_key)
        if cached is not None:
            # Cache lookup latency
            lat.append(15)   # fast Redis-class hit
            hits += 1
            by_model["cache"] += 1
            continue
        in_t, out_t, l = stub_invoke(decision.model_key, r["prompt"], r["expected_out"])
        cost += cost_usd(decision.model_key, in_t, out_t)
        lat.append(l)
        by_model[decision.model_key] = by_model.get(decision.model_key, 0) + 1
        cache.put(r["prompt"], decision.model_key,
                  CacheEntry(response="<cached>", model_key=decision.model_key,
                             in_tokens=in_t, out_tokens=out_t))
    return SimResult(
        strategy="router+cache", n_requests=len(requests), cache_hits=hits, cost_usd=cost,
        p50_latency_ms=percentile(lat, 0.5), p95_latency_ms=percentile(lat, 0.95),
        by_model=by_model,
    )


# ---- Synthetic workload ---------------------------------------------------

EASY_PROMPTS = [
    "Extract the policy id from: 'Policy #: AUT-2024-001'",
    "What is the deductible? Policy AUT-2024-001 has $500 deductible.",
    "Find the customer's DOB: born 1985-03-12.",
    "Classify: HO3-99821",
    "List the auto policies in the batch.",
]
MED_PROMPTS = [
    "Summarize the key risks in this declaration page (text follows): " + ("loss of coverage. " * 30),
    "Explain why a homeowner's HO3 policy differs from an HO5 policy at a basic level.",
    "Why was this loan declined given DTI 0.52 and credit 640? Reason concisely.",
    "Recommend a pricing tier given ARR $4M, growth 30%, churn 8%.",
]
HARD_PROMPTS = [
    "Analyze the tradeoffs of switching from a single-tenant to multi-tenant data warehouse for a B2B SaaS at $50M ARR. Compare costs, security, blast radius, and migration risk." + (" Provide a long-form recommendation. " * 5),
    "Compare and contrast three retrieval strategies (BM25, dense, hybrid) for a multilingual support corpus of 20M documents.",
]


def make_workload(n: int = 200, seed: int = 7, mix=(0.45, 0.40, 0.15), repeat_rate: float = 0.30) -> list[dict]:
    """Build a synthetic stream with realistic difficulty mix and repetition.

    `repeat_rate` controls the fraction of prompts that repeat a previous one
    (so the cache has something to hit).
    """
    rng = random.Random(seed)
    requests: list[dict] = []
    history: list[dict] = []
    for _ in range(n):
        if history and rng.random() < repeat_rate:
            requests.append(rng.choice(history))
            continue
        bucket = rng.choices(["easy", "medium", "hard"], weights=mix)[0]
        if bucket == "easy":
            p = rng.choice(EASY_PROMPTS)
            out = rng.randint(20, 80)
        elif bucket == "medium":
            p = rng.choice(MED_PROMPTS)
            out = rng.randint(150, 350)
        else:
            p = rng.choice(HARD_PROMPTS)
            out = rng.randint(500, 1200)
        req = {"prompt": p, "expected_out": out, "bucket": bucket}
        requests.append(req)
        history.append(req)
    return requests
