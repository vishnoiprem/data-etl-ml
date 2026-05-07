from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.cache import ExactCache, CacheEntry, SemanticCache
from src.pricing import cost_usd
from src.router import classify_difficulty
from src.simulator import make_workload, run_baseline_opus, run_router_with_cache


def test_pricing_haiku_cheaper_than_opus():
    assert cost_usd("haiku", 1000, 200) < cost_usd("opus", 1000, 200)


def test_router_assigns_haiku_for_easy():
    d = classify_difficulty("Extract the policy id from this short doc")
    assert d.model_key == "haiku"


def test_router_assigns_opus_for_hard():
    d = classify_difficulty("Analyze the tradeoffs of multi-tenant data warehouses")
    assert d.model_key == "opus"


def test_exact_cache_hits():
    c = ExactCache()
    assert c.get("p", "m") is None
    c.put("p", "m", CacheEntry("r", "m", 10, 20))
    assert c.get("p", "m") is not None
    assert c.hits == 1


def test_semantic_cache_normalizes():
    c = SemanticCache()
    c.put("Hello, world!", "haiku", CacheEntry("r", "haiku", 1, 1))
    assert c.get("hello world", "haiku") is not None


def test_simulation_router_cheaper_than_opus():
    w = make_workload(n=100, seed=1)
    s1 = run_baseline_opus(w)
    s3 = run_router_with_cache(w)
    assert s3.cost_usd < s1.cost_usd
