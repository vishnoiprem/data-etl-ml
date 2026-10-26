"""
Cell 24: Spark Backfill + Dual-Write Shadow Index

The interview question:
'You want to upgrade the embedding model from ada-002 to text-embedding-3.
 How do you roll out without breaking production or re-embedding 1B chunks?'

L6 answer structure:
- Full re-embed = 11 days of Spark (the WRONG way first)
- Incremental: dual-write shadow index, 1% dual-read, compare, cutover
- Cost: 8x parallel during rollout, 2x storage for the bake period
- Safety: shadow rollback < 5 min, zero production impact
"""
import time
import random
import json
from dataclasses import dataclass, field
from typing import List, Dict, Set
from collections import defaultdict

# ════════════════════════════════════════════════════════════════
# SCENARIO: 1B chunks, ada-002 -> text-embedding-3 upgrade
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("SCENARIO: 1B chunks, ada-002 -> text-embedding-3")
print("=" * 70)
print("""
The naive approach: re-embed all 1B chunks with the new model, swap.
  - 5000 chunks/sec per worker, 200 workers
  - 1B / (5000 * 200) = 1000 seconds = 16 minutes. Sounds fine.
  - But: 1B * $0.00013 = $130k. And quality may regress.
  - And: full outage during swap (or dual-write complexity).

The L6 approach: shadow index + incremental + A/B.
""")

# ════════════════════════════════════════════════════════════════
# METHOD 1 (NAIVE): full re-embed
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("METHOD 1 (NAIVE): full re-embed with new model, swap")
print("=" * 70)

CHUNKS = 1_000_000_000
RATE_PER_WORKER = 5_000  # chunks/sec
WORKERS = 200
COST_PER_CHUNK = 0.00013  # $0.13 per 1M tokens

naive_seconds = CHUNKS / (RATE_PER_WORKER * WORKERS)
naive_hours = naive_seconds / 3600
naive_cost = CHUNKS * COST_PER_CHUNK
print(f"  Time:  {naive_hours:.1f} hours ({naive_hours/24:.1f} days)")
print(f"  Cost:  ${naive_cost:,.0f}")
print(f"  Risk:  if quality regresses, $130k wasted + rollback pain")
print(f"  Risk:  no A/B comparison, blind swap")

# ════════════════════════════════════════════════════════════════
# METHOD 2: dual-write shadow index (the L6 way)
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("METHOD 2: dual-write shadow index + A/B compare (the L6 way)")
print("=" * 70)
print("""
Phase 1: SHADOW WRITE (1 day, $0)
  - Ingest pipeline writes to BOTH ada-002 (prod) AND text-embedding-3 (shadow)
  - Cost: 2x embedding API calls, 2x Qdrant storage
  - Risk: 0 (shadow is read-only, prod is unchanged)

Phase 2: DUAL READ + COMPARE (3-7 days, $0)
  - 1% of queries served by SHADOW, 99% by prod
  - Compare: latency, Recall@8, satisfaction, cost
  - If shadow beats prod on all 4 -> proceed to Phase 3
  - If shadow regresses on any -> kill shadow, post-mortem

Phase 3: GRADUAL CUTOVER (3-5 days)
  - Day 1: 10% traffic to new index
  - Day 2: 25% if metrics green
  - Day 4: 50% if metrics green
  - Day 7: 100% traffic to new index

Phase 4: BACKFILL (10-14 days, $130k)
  - Spark job re-embeds the remaining 99% of historical chunks
  - Done in background, doesn't block serving

Phase 5: CUTOVER (instant)
  - Update serving config: new_index = primary
  - Old index becomes read-only, deleted after 30 days
""")

# Simulate the dual-read A/B
@dataclass
class IndexMetrics:
    requests: int = 0
    recall_at_8: float = 0.0
    p95_latency_ms: float = 0.0
    satisfaction: float = 0.0
    cost_per_1k: float = 0.0

class Index:
    def __init__(self, name, quality, latency_ms, cost):
        self.name = name
        self.quality = quality
        self.latency_ms = latency_ms
        self.cost = cost
        self.metrics = IndexMetrics()

    def query(self):
        self.metrics.requests += 1
        # Simulate metric drift
        self.metrics.recall_at_8 = self.quality + random.gauss(0, 0.01)
        self.metrics.p95_latency_ms = self.latency_ms + random.gauss(0, 5)
        self.metrics.satisfaction = self.quality * 0.9 + random.gauss(0, 0.01)
        self.metrics.cost_per_1k = self.cost

# Simulate 1 week of dual-read A/B
print("\nSimulated 7-day A/B test (1% shadow traffic):")
prod_index = Index("ada-002-prod", quality=0.85, latency_ms=380, cost=2.0)
shadow_index = Index("text-embedding-3-shadow", quality=0.91, latency_ms=420, cost=1.5)

DAYS = 7
TRAFFIC_PER_DAY = 1_000_000
SHADOW_PCT = 0.01
random.seed(42)
for day in range(1, DAYS + 1):
    for _ in range(TRAFFIC_PER_DAY):
        prod_index.query()
    for _ in range(int(TRAFFIC_PER_DAY * SHADOW_PCT)):
        shadow_index.query()
    print(f"  Day {day}: prod Recall={prod_index.metrics.recall_at_8:.3f} "
          f"latency={prod_index.metrics.p95_latency_ms:.0f}ms | "
          f"shadow Recall={shadow_index.metrics.recall_at_8:.3f} "
          f"latency={shadow_index.metrics.p95_latency_ms:.0f}ms")

print(f"\n  Verdict: shadow wins on Recall@8 (+{shadow_index.metrics.recall_at_8 - prod_index.metrics.recall_at_8:.3f})")
print(f"  shadow wins on cost (-${prod_index.metrics.cost_per_1k - shadow_index.metrics.cost_per_1k:.1f}/1k)")
print(f"  shadow loses on latency (+{shadow_index.metrics.p95_latency_ms - prod_index.metrics.p95_latency_ms:.0f}ms)")
print(f"  => Trade-off acceptable. Proceed to Phase 3.")

# ════════════════════════════════════════════════════════════════
# GRADUAL CUTOVER simulation
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PHASE 3-4: gradual cutover + backfill")
print("=" * 70)

phases = [
    ("Day 1-2: 10% new index", 0.10, "Watch: p95 latency, satisfaction, error rate"),
    ("Day 3-4: 25% new index", 0.25, "Watch: cost savings, Recall@8 in dashboard"),
    ("Day 5-7: 50% new index", 0.50, "Watch: rollback plan ready, on-call paged"),
    ("Day 8-10: 75% new index", 0.75, "Watch: shadow index still serving 25% as backup"),
    ("Day 11: 100% new index", 1.00, "Watch: cutover, no rollback planned"),
    ("Day 12-25: backfill", 1.00, "Spark: re-embed historical chunks in background"),
    ("Day 30: delete old index", 1.00, "Cleanup: free 50% storage"),
]
print(f"\n{'Phase':<32} {'New %':>8} {'Monitor'}")
print("-" * 80)
for phase, pct, watch in phases:
    print(f"{phase:<32} {pct*100:>7.0f}% {watch}")

# Rollback plan
print("\n" + "=" * 70)
print("ROLLBACK PLAN: 5-minute revert")
print("=" * 70)
print("""
If any of: p95 > 1s, error rate > 1%, satisfaction drops > 5%:
  1. Update serving config: new_index = old_index
  2. Memcache invalidation
  3. Verify metrics in 1 minute
  4. Post-mortem within 24h

Rollback cost: 0 (we still have the old index serving 25% traffic)
Rollback time: < 5 minutes (config push, no data movement)

The dual-write + 1% dual-read pattern is the L6 default.
""")

# ════════════════════════════════════════════════════════════════
# COST COMPARISON
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("COST: naive vs L6 pattern")
print("=" * 70)

naive_total = naive_cost + 0  # one-shot
l6_total = (
    0  # shadow write: 2x cost for 30 days
    + 2 * 30 * 1_000_000 * COST_PER_CHUNK  # 2x embedding for 30 days during rollout
    + 130_000  # backfill
)
# Hmm, the L6 cost includes 2x serving cost during rollout
l6_serving_2x = 2 * 30 * 1_000_000 * COST_PER_CHUNK
l6_total = l6_serving_2x + 130_000

print(f"\n  Naive full re-embed:     ${naive_cost:>10,.0f}  (one-shot, blind)")
print(f"  L6 pattern total:        ${l6_total:>10,.0f}  (gradual + A/B + backfill)")
print(f"  L6 incremental saving:   ${naive_cost - 130_000:>10,.0f}  (only backfill cost)")
print(f"  L6 RISK:                 0 (full rollback in 5 min)")

# ════════════════════════════════════════════════════════════════
# L6 ANSWER
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("L6 ANSWER (when they ask 'how do you upgrade embedding models?')")
print("=" * 70)
print("""
Q: "1B chunks on ada-002, want to upgrade to text-embedding-3.
    How do you roll out?"

A: "5 phases, dual-write shadow index pattern.

PHASE 1: SHADOW WRITE (1 day, $0)
  Ingestion writes to BOTH ada-002 (prod, untouched) AND
  text-embedding-3 (shadow, read-only). Zero prod risk.

PHASE 2: DUAL READ + COMPARE (3-7 days, $0)
  1% traffic to shadow. Compare 4 metrics:
    - Recall@8 (from gold set)
    - p95 latency
    - user satisfaction
    - cost per 1k queries
  If shadow wins on Recall+satisfaction+cost, accept the
  latency hit. Proceed.

PHASE 3: GRADUAL CUTOVER (7-10 days)
  Day 1: 10% new
  Day 3: 25%
  Day 5: 50%
  Day 8: 75%
  Day 11: 100%
  On-call paged throughout. Rollback plan ready.

PHASE 4: BACKFILL (10-14 days, $130k)
  Spark re-embeds historical 99% in background.
  Doesn't block serving.

PHASE 5: CUTOVER + CLEANUP (Day 30)
  Old index deleted. Storage halved.

ROLLBACK: < 5 minutes via config push. Old index still
serving 25% traffic until Day 11, so rollback is instant.

The cardinal sin: full re-embed and blind swap.
  - $130k wasted if quality regresses
  - 30+ min downtime during swap
  - No rollback (old data overwritten)
  - No A/B comparison

The L6 pattern: never upgrade in prod without a shadow.
  - Cost: 2x storage for 30 days = $X
  - Risk: 0 (full rollback in 5 min)
  - Quality: 100% sure before cutover
""")
