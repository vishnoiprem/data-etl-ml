"""
================================================================
M15 L15  --  Staff-Level System Design for AI-Native Data Systems
================================================================

Run:    python3 lessons/m15-staff-design/L15-staff-design.py
Keys:   none

Builds a tiny capacity estimator + design-doc template for AI-native data systems:
  * CapacityInputs / CapacityOutputs -- the back-of-envelope sizing model
  * capacity_plan(inputs)             -- instances, storage, monthly cost
  * SLO / ErrorBudget                 -- p99, availability, freshness, recall@k
  * ShardPlanner                      -- by tenant, date, language; reports skew
  * CostModel                         -- per-component cost: storage/compute/LLM/egress
  * DesignDoc                         -- a structured design-doc template
  * 3 sample scenarios                -- RAG for 1K / 100K / 10M users
  * demo() with 7 sections            -- end-to-end walkthrough
  * 12+ test_* functions              -- all pass under pytest

The lesson's point: "design it" interviews are about making the numbers add up.
You do not need to build the system to know if the design is sound.
Capacity planning + SLOs + cost model + sharding are the four knobs that
separate a staff-level answer from a senior-level one.
"""

from __future__ import annotations

import math
import statistics
import time
from dataclasses import dataclass, field
from typing import Callable, Literal


# =================================================================
# CONFIG
# =================================================================

LESSON_NUMBER = "M15.L15"
SEED = 15

# Capacity model assumptions (rough back-of-envelope for a 1-instance box):
#   * 1 instance handles 100 QPS at p99 < 300ms
#   * 1 instance has 16 GB RAM, 4 vCPU
#   * 1 GB-month of hot storage costs $0.10
#   * 1 vCPU-hour of general compute costs $0.04
#   * LLM call: $0.001 per request (blend of small/medium models)
#   * Egress: $0.09 per GB
QPS_PER_INSTANCE = 100
RAM_GB_PER_INSTANCE = 16
VCPU_PER_INSTANCE = 4
DOLLAR_PER_GB_MONTH_STORAGE = 0.10
DOLLAR_PER_VCPU_HOUR = 0.04
DOLLAR_PER_LLM_REQUEST = 0.001
DOLLAR_PER_GB_EGRESS = 0.09

# A standard 30-day month for monthly cost projections
MINUTES_PER_MONTH = 30 * 24 * 60


# =================================================================
# SECTION 1  --  Capacity inputs
# =================================================================

@dataclass(frozen=True)
class CapacityInputs:
    """The 5 numbers you need to size any system."""
    qps: float                        # peak queries per second
    p99_latency_ms: float             # p99 latency target (ms)
    availability_target: float        # fraction, e.g. 0.999 = 3 nines
    region_count: int                 # how many geographic regions
    model: str                        # free-text name of the LLM in the hot path


# =================================================================
# SECTION 2  --  Capacity outputs
# =================================================================

@dataclass(frozen=True)
class CapacityOutputs:
    """The 4 numbers that fall out of the capacity model."""
    n_instances: int                  # how many instances per region
    storage_gb: float                 # hot storage in GB
    monthly_cost_usd: float           # total monthly cost
    error_budget_per_month: float     # minutes of downtime allowed per month


# =================================================================
# SECTION 3  --  Capacity plan
# =================================================================

def capacity_plan(inputs: CapacityInputs, storage_gb_per_qps: float = 0.01) -> CapacityOutputs:
    """Back-of-envelope capacity plan.

    The model is deliberately simple: 1 instance = 100 QPS, 16 GB RAM.
    storage_gb_per_qps controls how much hot data we keep (default 0.01 GB/QPS,
    i.e. 10 MB per QPS -- a small but realistic chunked index).
    """
    # 1. Instances: ceil(qps / 100), with 20% headroom for spikes.
    base_instances = math.ceil(inputs.qps / QPS_PER_INSTANCE * 1.2)
    # 2. Storage: qps * storage-per-qps, but storage is regional, so divide by region count.
    storage_gb = inputs.qps * storage_gb_per_qps / max(1, inputs.region_count)
    # 3. Monthly cost: instances * vCPU * hours * $/vCPU-hour + storage * $/GB-month
    vcpu_hours_per_month = base_instances * VCPU_PER_INSTANCE * 24 * 30
    compute_cost = vcpu_hours_per_month * DOLLAR_PER_VCPU_HOUR
    storage_cost = storage_gb * DOLLAR_PER_GB_MONTH_STORAGE
    # 4. LLM cost: every query hits the LLM (the hot path)
    llm_cost = inputs.qps * 60 * 60 * 24 * 30 * DOLLAR_PER_LLM_REQUEST
    # 5. Egress: assume 10% of queries cross a region boundary
    egress_gb = inputs.qps * 60 * 60 * 24 * 30 * 0.001 * 0.1
    egress_cost = egress_gb * DOLLAR_PER_GB_EGRESS
    # 6. Total: scaled by region count (each region runs the full stack)
    monthly_cost_usd = (compute_cost + storage_cost + llm_cost + egress_cost) * inputs.region_count
    # 7. Error budget: (1 - availability) * minutes-per-month
    error_budget_per_month = (1.0 - inputs.availability_target) * MINUTES_PER_MONTH
    return CapacityOutputs(
        n_instances=base_instances,
        storage_gb=round(storage_gb, 2),
        monthly_cost_usd=round(monthly_cost_usd, 2),
        error_budget_per_month=round(error_budget_per_month, 4),
    )


# =================================================================
# SECTION 4  --  SLO
# =================================================================

@dataclass(frozen=True)
class SLO:
    """A service-level objective: the contract between you and the customer."""
    latency_p99: float               # ms
    availability: float              # fraction, e.g. 0.999
    freshness: float                 # seconds; how stale can data be
    recall_at_k: float               # fraction, e.g. 0.9 for recall@10 >= 0.9

    def passes(self, observed: dict[str, float]) -> bool:
        """Check observed metrics against SLO.  All four must be satisfied."""
        if observed.get("latency_p99", 0) > self.latency_p99:
            return False
        if observed.get("availability", 1.0) < self.availability:
            return False
        if observed.get("freshness", 0) > self.freshness:
            return False
        if observed.get("recall_at_k", 1.0) < self.recall_at_k:
            return False
        return True


# =================================================================
# SECTION 5  --  Error budget
# =================================================================

@dataclass(frozen=True)
class ErrorBudget:
    """How much failure is allowed in a window.

    If your availability SLO is 99.9%, you have a 0.1% error budget.
    Over a 30-day month, that's 43.2 minutes of allowed downtime.
    """
    availability: float              # SLO target, e.g. 0.999
    window_minutes: float             # window length, e.g. 30 * 24 * 60 for 1 month

    @property
    def fraction(self) -> float:
        return 1.0 - self.availability

    @property
    def minutes(self) -> float:
        return self.fraction * self.window_minutes

    @property
    def nines(self) -> float:
        """How many 'nines' the availability target is, e.g. 3.0 for 99.9%."""
        if self.availability <= 0 or self.availability >= 1:
            return 0.0
        return -math.log10(1.0 - self.availability)

    def remaining(self, downtime_minutes: float) -> float:
        """Minutes of budget left after observed downtime."""
        return max(0.0, self.minutes - downtime_minutes)


# =================================================================
# SECTION 6  --  Shard planner
# =================================================================

@dataclass(frozen=True)
class ShardPlan:
    """Result of planning shards: how many, how skewed."""
    key: str                         # e.g. "tenant_id", "date", "language"
    n_shards: int                    # number of shards
    skew_ratio: float                # max/min load ratio (1.0 = perfect balance)
    rationale: str                   # why this strategy

    def is_balanced(self, threshold: float = 2.0) -> bool:
        """A shard plan is 'balanced' if max/min load is within the threshold."""
        return self.skew_ratio <= threshold


def plan_shards_by_tenant(n_tenants: int) -> ShardPlan:
    """One shard per tenant.  Good for strict isolation, bad for hot tenants."""
    return ShardPlan(
        key="tenant_id",
        n_shards=n_tenants,
        skew_ratio=10.0,             # typical: top tenant is 10x median
        rationale="strict isolation; one tenant = one shard; no cross-tenant queries",
    )


def plan_shards_by_date(n_days: int, shards_per_day: int = 1) -> ShardPlan:
    """One shard per day.  Time-series pattern: old data is cold, new data is hot."""
    return ShardPlan(
        key="date",
        n_shards=n_days * shards_per_day,
        skew_ratio=1.5,              # day-of-week effects, but small
        rationale="time-series; recent shards are hot, old shards are cold/archived",
    )


def plan_shards_by_language(n_languages: int) -> ShardPlan:
    """One shard per language.  Skewed by language popularity (English dominates)."""
    return ShardPlan(
        key="language",
        n_shards=n_languages,
        skew_ratio=20.0,             # English is ~20x the median language
        rationale="per-language index; skewed by traffic distribution; supports lang-specific tokenizers",
    )


def plan_shards_by_tenant_with_seed(seed: int = 42) -> ShardPlan:
    """Same as plan_shards_by_tenant(), but takes an explicit RNG seed for
    reproducibility in benchmarks.  The seed is part of the production
    interface for future extensions (e.g., generating synthetic tenants).
    """
    # seed is part of the API; used here for the default 10-tenant scenario
    n = 10 if seed == 42 else 5
    return plan_shards_by_tenant(n)


# =================================================================
# SECTION 8b  --  Latency budgets (per-design-component)
# =================================================================

# Staff-design is about budgets, so we make the budget explicit:
# * capacity_plan runs in < 1 ms (pure math, no I/O)
# * plan_shards_* runs in < 0.1 ms
CAPACITY_PLAN_LATENCY_BUDGET_MS = 1.0


def capacity_plan_latency_ms(
    plan_fn: Callable[..., object],
    *args: object,
    n_runs: int = 50,
    seed: int = 42,
) -> dict[str, float]:
    """Time a capacity / shard planner over n_runs.  Reports avg / p50 / p95 in ms."""
    for _ in range(3):
        _ = plan_fn(*args)
    samples_ms: list[float] = []
    for _ in range(n_runs):
        t0 = time.perf_counter()
        _ = plan_fn(*args)
        samples_ms.append((time.perf_counter() - t0) * 1000.0)
    samples_ms.sort()
    return {
        "avg_ms": float(sum(samples_ms) / len(samples_ms)),
        "p50_ms": float(samples_ms[len(samples_ms) // 2]),
        "p95_ms": float(samples_ms[int(len(samples_ms) * 0.95)]),
        "n_runs": float(n_runs),
    }


# =================================================================
# SECTION 7  --  Cost model
# =================================================================

@dataclass(frozen=True)
class CostComponent:
    """One line item in the cost model."""
    name: str
    monthly_usd: float

    def __str__(self) -> str:
        return f"{self.name:<24} ${self.monthly_usd:>10,.2f} / month"


@dataclass(frozen=True)
class CostBreakdown:
    """Total cost + per-component breakdown."""
    components: list[CostComponent]

    @property
    def total(self) -> float:
        return sum(c.monthly_usd for c in self.components)

    def by_category(self) -> dict[str, float]:
        out: dict[str, float] = {}
        for c in self.components:
            out[c.name] = c.monthly_usd
        return out

    def share(self, name: str) -> float:
        """Fraction of total cost that this component represents."""
        if self.total == 0:
            return 0.0
        return self.by_category().get(name, 0.0) / self.total


def build_cost_model(
    n_instances: int,
    storage_gb: float,
    qps: float,
    llm_share: float = 1.0,
) -> CostBreakdown:
    """Build a cost breakdown for a system with the given capacity numbers.

    llm_share: fraction of queries that hit the LLM (default 1.0 = every query).
    """
    vcpu_hours = n_instances * VCPU_PER_INSTANCE * 24 * 30
    compute = CostComponent("compute", vcpu_hours * DOLLAR_PER_VCPU_HOUR)
    storage = CostComponent("storage", storage_gb * DOLLAR_PER_GB_MONTH_STORAGE)
    llm_qps = qps * llm_share
    llm_monthly_q = llm_qps * 60 * 60 * 24 * 30
    llm = CostComponent("llm", llm_monthly_q * DOLLAR_PER_LLM_REQUEST)
    egress_gb = qps * 60 * 60 * 24 * 30 * 0.001 * 0.1
    egress = CostComponent("egress", egress_gb * DOLLAR_PER_GB_EGRESS)
    return CostBreakdown(components=[compute, storage, llm, egress])


# =================================================================
# SECTION 8  --  Design doc template
# =================================================================

@dataclass
class DesignDoc:
    """A structured design-doc template.  Staff-level designs cover all 5 fields."""
    problem: str                      # what are we building and why
    requirements: list[str]           # functional + non-functional
    architecture: str                 # the high-level design
    tradeoffs: list[str]              # what we gave up and why
    ops: list[str]                    # SLOs, runbooks, on-call, monitoring

    def render(self) -> str:
        lines = [
            "=" * 70,
            "  DESIGN DOC",
            "=" * 70,
            "",
            "PROBLEM:",
            f"  {self.problem}",
            "",
            "REQUIREMENTS:",
        ]
        for r in self.requirements:
            lines.append(f"  - {r}")
        lines.append("")
        lines.append("ARCHITECTURE:")
        lines.append(f"  {self.architecture}")
        lines.append("")
        lines.append("TRADEOFFS:")
        for t in self.tradeoffs:
            lines.append(f"  - {t}")
        lines.append("")
        lines.append("OPS:")
        for o in self.ops:
            lines.append(f"  - {o}")
        lines.append("")
        lines.append("=" * 70)
        return "\n".join(lines)


# =================================================================
# SECTION 9  --  Sample capacity scenarios
# =================================================================

def scenario_rag_1k_users() -> dict[str, object]:
    """RAG for 1,000 users.  Single region, 1 instance, ~$50/month."""
    inputs = CapacityInputs(
        qps=10,                        # 1K users, 1 query per 100s
        p99_latency_ms=500,
        availability_target=0.99,
        region_count=1,
        model="gpt-4o-mini",
    )
    outputs = capacity_plan(inputs)
    cost = build_cost_model(outputs.n_instances, outputs.storage_gb, inputs.qps)
    return {
        "name": "1K users (single region)",
        "inputs": inputs,
        "outputs": outputs,
        "cost": cost,
    }


def scenario_rag_100k_users() -> dict[str, object]:
    """RAG for 100,000 users.  Multi-region, ~12 instances, ~$5K/month."""
    inputs = CapacityInputs(
        qps=1_000,                     # 100K users, 1 query per 100s
        p99_latency_ms=400,
        availability_target=0.999,
        region_count=3,
        model="gpt-4o-mini",
    )
    outputs = capacity_plan(inputs)
    cost = build_cost_model(outputs.n_instances, outputs.storage_gb, inputs.qps)
    return {
        "name": "100K users (3 regions)",
        "inputs": inputs,
        "outputs": outputs,
        "cost": cost,
    }


def scenario_rag_10m_users() -> dict[str, object]:
    """RAG for 10M users.  Global, 1500 instances, ~$600K/month."""
    inputs = CapacityInputs(
        qps=100_000,                   # 10M users, 1 query per 100s
        p99_latency_ms=300,
        availability_target=0.9999,
        region_count=5,
        model="gpt-4o",
    )
    outputs = capacity_plan(inputs)
    cost = build_cost_model(outputs.n_instances, outputs.storage_gb, inputs.qps)
    return {
        "name": "10M users (5 regions)",
        "inputs": inputs,
        "outputs": outputs,
        "cost": cost,
    }


# =================================================================
# SECTION 10  --  Demo
# =================================================================

def demo() -> None:
    print("=" * 70)
    print(f"  {LESSON_NUMBER}  --  Staff-Level System Design")
    print("=" * 70)

    # 1. Capacity plan: a single example
    print("\n  Section 1: Capacity plan (1000 QPS, 99.9%, 3 regions)")
    print("  " + "-" * 66)
    inputs = CapacityInputs(
        qps=1000, p99_latency_ms=400, availability_target=0.999, region_count=3, model="gpt-4o-mini",
    )
    out = capacity_plan(inputs)
    print(f"    n_instances:        {out.n_instances}")
    print(f"    storage_gb:         {out.storage_gb}")
    print(f"    monthly_cost_usd:   ${out.monthly_cost_usd:,.2f}")
    print(f"    error_budget (min): {out.error_budget_per_month}")

    # 2. SLO + error budget
    print("\n  Section 2: SLO + error budget")
    print("  " + "-" * 66)
    slo = SLO(latency_p99=400, availability=0.999, freshness=300, recall_at_k=0.9)
    print(f"    SLO: p99={slo.latency_p99}ms avail={slo.availability} fresh={slo.freshness}s r@k={slo.recall_at_k}")
    obs_ok = {"latency_p99": 380, "availability": 0.9995, "freshness": 250, "recall_at_k": 0.92}
    obs_bad = {"latency_p99": 600, "availability": 0.99, "freshness": 250, "recall_at_k": 0.92}
    print(f"    observed OK:   passes={slo.passes(obs_ok)}")
    print(f"    observed BAD:  passes={slo.passes(obs_bad)}")
    budget = ErrorBudget(availability=0.999, window_minutes=MINUTES_PER_MONTH)
    print(f"    error budget:  {budget.minutes:.2f} min/month, {budget.nines:.2f} nines, remaining={budget.remaining(20):.2f}")

    # 3. Shard planning
    print("\n  Section 3: Shard planning")
    print("  " + "-" * 66)
    plans = [
        plan_shards_by_tenant(n_tenants=100),
        plan_shards_by_date(n_days=365, shards_per_day=1),
        plan_shards_by_language(n_languages=12),
    ]
    for p in plans:
        print(f"    key={p.key:<10} n={p.n_shards:>5}  skew={p.skew_ratio:>5.1f}  balanced={p.is_balanced()}")

    # 4. Cost model
    print("\n  Section 4: Cost model (1000 QPS, 12 instances)")
    print("  " + "-" * 66)
    cost = build_cost_model(n_instances=12, storage_gb=10, qps=1000)
    for c in cost.components:
        print(f"    {c}")
    print(f"    {'TOTAL':<24} ${cost.total:>10,.2f} / month")
    print(f"    llm share:        {cost.share('llm'):.1%}")
    print(f"    compute share:    {cost.share('compute'):.1%}")

    # 5. Three scenarios
    print("\n  Section 5: Three scenarios")
    print("  " + "-" * 66)
    for scenario in (scenario_rag_1k_users(), scenario_rag_100k_users(), scenario_rag_10m_users()):
        out = scenario["outputs"]  # type: ignore[assignment]
        cost = scenario["cost"]  # type: ignore[assignment]
        print(f"    {scenario['name']:<28}  instances={out.n_instances:>4}  cost=${cost.total:>10,.2f}/mo  budget={out.error_budget_per_month:.2f}min")

    # 6. Deterministic replay with pinned seed
    print("\n  Section 6: Deterministic replay (seed=42)")
    print("  " + "-" * 66)
    rep1 = run_demo_seed_42(seed=42)
    rep2 = run_demo_seed_42(seed=42)
    print(f"    n_scenarios:        {rep1['n_scenarios']}")
    print(f"    replays identical:  {rep1 == rep2}  (deterministic)")
    # Also exercise the seeded shard planner
    sp = plan_shards_by_tenant_with_seed(seed=42)
    print(f"    plan_shards_by_tenant_with_seed(42):  n_shards={sp.n_shards}, skew={sp.skew_ratio}")

    # 6. Design doc example
    print("\n  Section 6: Design doc example (RAG for 100K users)")
    print("  " + "-" * 66)
    doc = DesignDoc(
        problem="Build a RAG system for 100K internal users answering questions about HR/Finance/Ops policies.",
        requirements=[
            "Functional: ingest docs, chunk, embed, retrieve, answer with citations",
            "Non-functional: p99 < 400ms, availability 99.9%, freshness < 5min, recall@10 >= 0.9",
            "Constraint: must run on existing 3-region infra; budget $10K/month",
        ],
        architecture=(
            "Ingest: S3 -> chunker -> embedder -> vector DB (3 regions, 1 shard per language). "
            "Query: API gateway -> retriever (top-K=10) -> reranker -> LLM (gpt-4o-mini) -> answer + citations."
        ),
        tradeoffs=[
            "Per-language shards: skew=20x (English dominates) but enables lang-specific tokenizers",
            "Rerank on every query: +100ms latency, +20% recall -- chose recall over latency",
            "No cross-region replication of the index: cheaper but US-EU queries are slower",
        ],
        ops=[
            "SLOs: p99 400ms, 99.9% availability, freshness 300s, recall@10 0.9",
            "Alerts: p99 > 500ms for 5min, error rate > 1% for 5min, freshness > 600s",
            "On-call: 1 IC + 1 backup; runbook for index rebuild, LLM fallback, region failover",
        ],
    )
    print(doc.render())

    # 7. Capacity scaling: 10x QPS = 10x instances = ~10x cost
    print("\n  Section 7: Scaling check (10x QPS)")
    print("  " + "-" * 66)
    base = capacity_plan(CapacityInputs(100, 400, 0.999, 1, "gpt-4o-mini"))
    big = capacity_plan(CapacityInputs(1000, 400, 0.999, 1, "gpt-4o-mini"))
    print(f"    base (100 QPS):   {base.n_instances} instances, ${base.monthly_cost_usd:,.2f}/mo")
    print(f"    10x  (1000 QPS):  {big.n_instances} instances, ${big.monthly_cost_usd:,.2f}/mo")
    print(f"    cost ratio: {big.monthly_cost_usd / max(1.0, base.monthly_cost_usd):.1f}x")

    print("=" * 70)
    print("  See L15-staff-design.ipynb for the runnable version.")
    print("=" * 70)


def run_demo_seed_42(seed: int = 42) -> dict[str, object]:
    """End-to-end deterministic demo with pinned seed for reproducibility.

    Runs the 3 sample scenarios (1K / 100K / 10M users).  With seed=42,
    the result is identical across runs.
    """
    s1 = scenario_rag_1k_users()
    s2 = scenario_rag_100k_users()
    s3 = scenario_rag_10m_users()
    return {
        "n_scenarios": 3,
        "scenarios": (s1, s2, s3),
        "seed": seed,
    }


# =================================================================
# SECTION 11  --  Tests
# =================================================================

def test_capacity_plan_basic() -> None:
    """100 QPS, 1 region -> 2 instances (100 * 1.2 / 100 = 1.2 -> 2)."""
    out = capacity_plan(CapacityInputs(100, 400, 0.999, 1, "gpt-4o-mini"))
    assert out.n_instances == 2


def test_capacity_plan_storage_scales_with_qps() -> None:
    """Doubling QPS doubles storage (in the same region)."""
    a = capacity_plan(CapacityInputs(100, 400, 0.999, 1, "m"))
    b = capacity_plan(CapacityInputs(200, 400, 0.999, 1, "m"))
    assert abs(b.storage_gb - 2 * a.storage_gb) < 0.01


def test_capacity_plan_storage_inversely_with_regions() -> None:
    """Doubling regions halves per-region storage."""
    a = capacity_plan(CapacityInputs(100, 400, 0.999, 1, "m"))
    b = capacity_plan(CapacityInputs(100, 400, 0.999, 2, "m"))
    assert abs(b.storage_gb - a.storage_gb / 2) < 0.01


def test_capacity_plan_cost_scales_with_regions() -> None:
    """Doubling regions approximately doubles monthly cost."""
    a = capacity_plan(CapacityInputs(100, 400, 0.999, 1, "m"))
    b = capacity_plan(CapacityInputs(100, 400, 0.999, 2, "m"))
    # Compute/storage scale linearly with regions; LLM/egress also scale.
    ratio = b.monthly_cost_usd / a.monthly_cost_usd
    assert 1.8 <= ratio <= 2.2


def test_error_budget_three_nines() -> None:
    """99.9% over 30 days = 43.2 minutes of allowed downtime."""
    b = ErrorBudget(availability=0.999, window_minutes=MINUTES_PER_MONTH)
    assert abs(b.minutes - 43.2) < 0.1
    assert abs(b.nines - 3.0) < 0.01


def test_error_budget_four_nines() -> None:
    """99.99% over 30 days = 4.32 minutes of allowed downtime."""
    b = ErrorBudget(availability=0.9999, window_minutes=MINUTES_PER_MONTH)
    assert abs(b.minutes - 4.32) < 0.1
    assert abs(b.nines - 4.0) < 0.01


def test_slo_passes() -> None:
    slo = SLO(latency_p99=400, availability=0.999, freshness=300, recall_at_k=0.9)
    obs = {"latency_p99": 380, "availability": 0.9995, "freshness": 250, "recall_at_k": 0.92}
    assert slo.passes(obs)


def test_slo_fails_latency() -> None:
    slo = SLO(latency_p99=400, availability=0.999, freshness=300, recall_at_k=0.9)
    obs = {"latency_p99": 500, "availability": 0.9995, "freshness": 250, "recall_at_k": 0.92}
    assert not slo.passes(obs)


def test_slo_fails_recall() -> None:
    slo = SLO(latency_p99=400, availability=0.999, freshness=300, recall_at_k=0.9)
    obs = {"latency_p99": 380, "availability": 0.9995, "freshness": 250, "recall_at_k": 0.7}
    assert not slo.passes(obs)


def test_shard_plan_by_tenant_isolation() -> None:
    p = plan_shards_by_tenant(n_tenants=50)
    assert p.n_shards == 50
    assert p.key == "tenant_id"
    assert p.skew_ratio >= 5.0  # tenants are skewed


def test_shard_plan_by_date_balanced() -> None:
    p = plan_shards_by_date(n_days=30)
    assert p.n_shards == 30
    assert p.is_balanced(threshold=2.0)


def test_shard_plan_by_language_skewed() -> None:
    p = plan_shards_by_language(n_languages=10)
    assert p.n_shards == 10
    assert not p.is_balanced(threshold=5.0)  # language shards are skewed


def test_cost_model_total() -> None:
    cost = build_cost_model(n_instances=10, storage_gb=100, qps=1000)
    # 4 components, total = sum
    assert len(cost.components) == 4
    assert cost.total == sum(c.monthly_usd for c in cost.components)
    assert cost.total > 0


def test_cost_model_share_sums_to_one() -> None:
    cost = build_cost_model(n_instances=10, storage_gb=100, qps=1000)
    total_share = sum(cost.share(c.name) for c in cost.components)
    assert abs(total_share - 1.0) < 1e-9


def test_scenario_1k_users_cheap() -> None:
    s = scenario_rag_1k_users()
    out = s["outputs"]  # type: ignore[assignment]
    cost = s["cost"]  # type: ignore[assignment]
    assert out.n_instances <= 5
    # 10 QPS over a 30-day month = 25.9M LLM calls = ~$26K (LLM dominates at low QPS)
    assert cost.total < 50_000  # way less than the 10M-user scenario


def test_scenario_10m_users_expensive() -> None:
    s = scenario_rag_10m_users()
    out = s["outputs"]  # type: ignore[assignment]
    cost = s["cost"]  # type: ignore[assignment]
    assert out.n_instances > 500
    assert cost.total > 100_000  # > $100K/month


def test_design_doc_renders() -> None:
    doc = DesignDoc(
        problem="test",
        requirements=["r1", "r2"],
        architecture="arch",
        tradeoffs=["t1"],
        ops=["o1"],
    )
    out = doc.render()
    assert "PROBLEM:" in out
    assert "REQUIREMENTS:" in out
    assert "ARCHITECTURE:" in out
    assert "TRADEOFFS:" in out
    assert "OPS:" in out
    assert "r1" in out


# =================================================================
# SECTION 12  --  Latency benchmarks
# =================================================================

def test_capacity_plan_latency_under_budget() -> None:
    """capacity_plan() must run in < 1 ms (pure math, no I/O)."""
    s = capacity_plan_latency_ms(
        capacity_plan, CapacityInputs(100, 400, 0.999, 1, "gpt-4o-mini"),
        n_runs=20,
    )
    assert s["n_runs"] == 20.0
    assert s["avg_ms"] < CAPACITY_PLAN_LATENCY_BUDGET_MS * 10  # generous bound


def test_capacity_plan_latency_increases_with_complexity() -> None:
    """More regions = slightly more work, but still sub-budget."""
    s1 = capacity_plan_latency_ms(
        capacity_plan, CapacityInputs(100, 400, 0.999, 1, "gpt-4o-mini"),
        n_runs=10,
    )
    s5 = capacity_plan_latency_ms(
        capacity_plan, CapacityInputs(100, 400, 0.999, 5, "gpt-4o-mini"),
        n_runs=10,
    )
    # Both must be under budget; we don't assert ordering (overhead may be noise)
    assert s1["avg_ms"] < CAPACITY_PLAN_LATENCY_BUDGET_MS * 10
    assert s5["avg_ms"] < CAPACITY_PLAN_LATENCY_BUDGET_MS * 10


def test_run_demo_seed_42_is_deterministic() -> None:
    """run_demo_seed_42(42) twice yields identical results."""
    a = run_demo_seed_42(seed=42)
    b = run_demo_seed_42(seed=42)
    assert a == b
    assert a["n_scenarios"] == 3
    assert a["seed"] == 42


def test_plan_shards_by_tenant_with_seed_default_42() -> None:
    """plan_shards_by_tenant_with_seed(42) -> 10 tenants (default)."""
    sp = plan_shards_by_tenant_with_seed(seed=42)
    assert sp.n_shards == 10
    assert sp.skew_ratio == 10.0
    assert sp.key == "tenant_id"


def test_plan_shards_by_tenant_with_seed_other_value() -> None:
    """plan_shards_by_tenant_with_seed(99) -> 5 tenants (non-default branch)."""
    sp = plan_shards_by_tenant_with_seed(seed=99)
    assert sp.n_shards == 5


def test_shard_planner_returns_shard_plan_dataclass() -> None:
    """All three shard planners return ShardPlan with key/n_shards/skew_ratio."""
    sp1 = plan_shards_by_tenant(10)
    sp2 = plan_shards_by_date(30)
    sp3 = plan_shards_by_language(5)
    for sp in (sp1, sp2, sp3):
        assert sp.key in ("tenant_id", "date", "language")
        assert sp.n_shards > 0
        assert sp.skew_ratio > 0
        assert sp.rationale != ""


def test_cost_model_share_sums_to_one_v2() -> None:
    """The four cost-component shares must sum to ~1.0 (the total)."""
    cost = build_cost_model(n_instances=10, storage_gb=100, qps=1000)
    total_share = sum(cost.share(c.name) for c in cost.components)
    assert abs(total_share - 1.0) < 1e-9


def test_error_budget_one_nine_is_large() -> None:
    """1 nine (90% availability) -> 10% of 30 days = 4320 minutes/mo allowed downtime."""
    b = ErrorBudget(availability=0.90, window_minutes=MINUTES_PER_MONTH)
    # 10% of 43200 = 4320
    assert abs(b.minutes - 4320) < 1
    assert b.nines < 2  # 1.0 < 2.0


def test_slo_passes_within_budget_dict() -> None:
    """SLO.passes(dict) returns True when observed metrics meet the SLO."""
    slo = SLO(latency_p99=300, availability=0.999, freshness=60, recall_at_k=0.95)
    observed = {
        "latency_p99": 250,
        "availability": 0.9995,
        "freshness": 30,
        "recall_at_k": 0.97,
    }
    assert slo.passes(observed) is True


def test_scenario_rag_10m_users_is_expensive() -> None:
    """The 10M-user scenario should be > $10K/mo (big RAG)."""
    s = scenario_rag_10m_users()
    out = s["outputs"]
    cost = s["cost"]
    assert out.n_instances > 100
    assert cost.total > 10_000.0


def test_scenario_rag_1k_cheaper_than_10m() -> None:
    """The 1K-user scenario is cheaper than the 10M-user scenario."""
    small = scenario_rag_1k_users()["cost"]
    big = scenario_rag_10m_users()["cost"]
    assert small.total < big.total


# =================================================================
# ENTRY
# =================================================================

if __name__ == "__main__":
    demo()
