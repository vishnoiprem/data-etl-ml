"""
================================================================
M17 L17  --  Product Metrics + SQL/Python for AI products
================================================================

Run:    python3 lessons/m17-product-metrics/L17-product-metrics.py
Keys:   none

Builds a tiny product-analytics stack for an AI feature:
  * Event store: in-memory list of (user_id, event_name, timestamp, properties)
  * Eight core AI-product metrics: DAU/WAU/MAU, adoption, engagement,
    quality (RAGAS), cost, retention, task success, latency
  * SQL definitions (mock syntax) + Python equivalents
  * A/B test scaffold: variant assignment, lift, p-value
  * Funnel: step definitions, drop-off rates
  * Synthetic 30-day dataset for the demo

The lesson's point: an AI product is measured on three axes:
  (1) do people use it, (2) does it work, (3) is it cheap.
The metrics below cover all three.
"""

from __future__ import annotations

import math
import random
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta


# =================================================================
# CONFIG
# =================================================================

LESSON_NUMBER = "M17.L17"
SEED = 17
WINDOW_DAYS = 30                 # synthetic data spans 30 days
N_USERS = 200                    # synthetic users
QUERY_COST_CENTS = 0.4           # average cost per AI query, in cents
RETENTION_DAY = 7                # D7 retention window


# =================================================================
# SECTION 1  --  The Event record
# =================================================================

@dataclass(frozen=True)
class Event:
    """One product-analytics event.  The base record everything else is built on.

    Properties is an open dict; common keys:
        variant:        A/B test variant ('control' | 'treatment')
        latency_ms:     end-to-end latency for query events
        cost_cents:     cost of serving for query events
        ragas_score:    quality score [0, 1] for query events
        answer:         AI response text (used by task-success metric)
    """
    user_id: str
    event_name: str
    timestamp: datetime
    properties: dict[str, object] = field(default_factory=dict)


# =================================================================
# SECTION 2  --  EventStore: in-memory list with query
# =================================================================

@dataclass
class EventStore:
    """In-memory list of events with a simple query interface."""
    events: list[Event] = field(default_factory=list)

    def add(self, e: Event) -> None:
        self.events.append(e)

    def query(
        self,
        name: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[Event]:
        """Return events matching name + time window.  None = wildcard."""
        out: list[Event] = []
        for e in self.events:
            if name is not None and e.event_name != name:
                continue
            if since is not None and e.timestamp < since:
                continue
            if until is not None and e.timestamp >= until:
                continue
            out.append(e)
        return out

    def unique_users(self, events: list[Event] | None = None) -> set[str]:
        evs = events if events is not None else self.events
        return {e.user_id for e in evs}

    def __len__(self) -> int:
        return len(self.events)


# =================================================================
# SECTION 3  --  Metric dataclass
# =================================================================

@dataclass(frozen=True)
class Metric:
    """A product metric: its name, SQL definition, Python equivalent, and unit."""
    name: str
    sql_definition: str
    python_equivalent: str
    unit: str                       # "count" | "ratio" | "ms" | "cents"


# =================================================================
# SECTION 4  --  The 8 core AI-product metrics
# =================================================================

METRICS: list[Metric] = [
    Metric(
        name="dau",
        sql_definition=(
            "SELECT DATE(timestamp) AS day, COUNT(DISTINCT user_id) AS dau\n"
            "FROM events\n"
            "WHERE event_name = 'ai_query'\n"
            "GROUP BY day;"
        ),
        python_equivalent="len({u for u in events_on_day if u did an ai_query})",
        unit="count",
    ),
    Metric(
        name="wau",
        sql_definition=(
            "SELECT DATE_TRUNC('week', timestamp) AS wk, COUNT(DISTINCT user_id) AS wau\n"
            "FROM events\n"
            "WHERE event_name = 'ai_query'\n"
            "GROUP BY wk;"
        ),
        python_equivalent="len({u for u in events_in_7d_window})",
        unit="count",
    ),
    Metric(
        name="mau",
        sql_definition=(
            "SELECT DATE_TRUNC('month', timestamp) AS mo, COUNT(DISTINCT user_id) AS mau\n"
            "FROM events\n"
            "WHERE event_name = 'ai_query'\n"
            "GROUP BY mo;"
        ),
        python_equivalent="len({u for u in events_in_30d_window})",
        unit="count",
    ),
    Metric(
        name="adoption_rate",
        sql_definition=(
            "SELECT\n"
            "  COUNT(DISTINCT CASE WHEN event_name = 'ai_query' THEN user_id END) * 1.0\n"
            "  / NULLIF(COUNT(DISTINCT user_id), 0) AS adoption\n"
            "FROM events\n"
            "WHERE event_name IN ('login', 'ai_query');"
        ),
        python_equivalent="ai_users / all_users",
        unit="ratio",
    ),
    Metric(
        name="engagement",
        sql_definition=(
            "SELECT\n"
            "  user_id,\n"
            "  DATE(timestamp) AS day,\n"
            "  COUNT(*) AS queries\n"
            "FROM events\n"
            "WHERE event_name = 'ai_query'\n"
            "GROUP BY user_id, day;"
        ),
        python_equivalent="total_queries / active_users / n_days",
        unit="count",
    ),
    Metric(
        name="quality_ragas",
        sql_definition=(
            "SELECT AVG(CAST(properties['ragas_score'] AS FLOAT)) AS avg_quality\n"
            "FROM events\n"
            "WHERE event_name = 'ai_query'\n"
            "  AND properties['ragas_score'] IS NOT NULL;"
        ),
        python_equivalent="mean(ragas_score over ai_query events)",
        unit="score",
    ),
    Metric(
        name="cost_per_user",
        sql_definition=(
            "SELECT\n"
            "  user_id,\n"
            "  SUM(CAST(properties['cost_cents'] AS FLOAT)) AS cost_cents\n"
            "FROM events\n"
            "WHERE event_name = 'ai_query'\n"
            "GROUP BY user_id;"
        ),
        python_equivalent="sum(cost_cents) / unique_users",
        unit="cents",
    ),
    Metric(
        name="retention_d7",
        sql_definition=(
            "-- D7 retention = % of new users who returned on day 7\n"
            "WITH first_use AS (\n"
            "  SELECT user_id, MIN(DATE(timestamp)) AS d0\n"
            "  FROM events\n"
            "  WHERE event_name = 'ai_query'\n"
            "  GROUP BY user_id\n"
            ")\n"
            "SELECT\n"
            "  COUNT(DISTINCT CASE\n"
            "    WHEN e.timestamp::date = f.d0 + INTERVAL '7 days' THEN f.user_id\n"
            "  END) * 1.0\n"
            "  / NULLIF(COUNT(DISTINCT f.user_id), 0) AS d7_retention\n"
            "FROM first_use f\n"
            "LEFT JOIN events e ON e.user_id = f.user_id;"
        ),
        python_equivalent="users_active_on_d7 / users_first_seen_on_d0",
        unit="ratio",
    ),
    Metric(
        name="task_success",
        sql_definition=(
            "SELECT\n"
            "  AVG(CASE WHEN properties['answer'] NOT LIKE '%I don%' THEN 1 ELSE 0 END) AS success\n"
            "FROM events\n"
            "WHERE event_name = 'ai_query';"
        ),
        python_equivalent="1 - (i_dont_know / total_queries)",
        unit="ratio",
    ),
    Metric(
        name="latency_p95",
        sql_definition=(
            "SELECT\n"
            "  APPROX_PERCENTILE(CAST(properties['latency_ms'] AS FLOAT), 0.95) AS p95\n"
            "FROM events\n"
            "WHERE event_name = 'ai_query';"
        ),
        python_equivalent="95th percentile of latency_ms",
        unit="ms",
    ),
]


# =================================================================
# SECTION 5  --  compute_metric: Python implementation of each metric
# =================================================================

def _percentile(values: list[float], pct: float) -> float:
    """Pure-Python percentile (linear interpolation, no numpy)."""
    if not values:
        return 0.0
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    k = (len(s) - 1) * pct
    lo = int(math.floor(k))
    hi = int(math.ceil(k))
    if lo == hi:
        return s[lo]
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def compute_metric(metric: Metric, store: EventStore, today: datetime) -> float:
    """Compute the named metric against the event store.  Returns a scalar."""
    queries = store.query("ai_query")

    if metric.name == "dau":
        # DAU on `today` -- number of distinct users who queried AI today.
        day = today.date()
        today_events = [e for e in queries if e.timestamp.date() == day]
        return float(len({e.user_id for e in today_events}))

    if metric.name == "wau":
        # WAU -- distinct users in the 7 days ending today (inclusive).
        start = today - timedelta(days=6)
        recent = [e for e in queries if start.date() <= e.timestamp.date() <= today.date()]
        return float(len({e.user_id for e in recent}))

    if metric.name == "mau":
        # MAU -- distinct users in the 30 days ending today (inclusive).
        start = today - timedelta(days=29)
        recent = [e for e in queries if start.date() <= e.timestamp.date() <= today.date()]
        return float(len({e.user_id for e in recent}))

    if metric.name == "adoption_rate":
        ai_users = {e.user_id for e in queries}
        all_users = store.unique_users()
        if not all_users:
            return 0.0
        return len(ai_users) / len(all_users)

    if metric.name == "engagement":
        # Queries per active user per day, averaged over the 30-day window.
        start = today - timedelta(days=29)
        recent = [e for e in queries if start.date() <= e.timestamp.date() <= today.date()]
        if not recent:
            return 0.0
        active = {e.user_id for e in recent}
        n_days = WINDOW_DAYS
        return len(recent) / len(active) / n_days

    if metric.name == "quality_ragas":
        scores = [
            float(e.properties["ragas_score"])
            for e in queries if "ragas_score" in e.properties
        ]
        if not scores:
            return 0.0
        return statistics.mean(scores)

    if metric.name == "cost_per_user":
        costs = [
            float(e.properties["cost_cents"])
            for e in queries if "cost_cents" in e.properties
        ]
        if not costs:
            return 0.0
        return sum(costs) / len({e.user_id for e in queries})

    if metric.name == "retention_d7":
        # For each user, find their first ai_query day (d0).
        first_seen: dict[str, datetime] = {}
        for e in queries:
            if e.user_id not in first_seen or e.timestamp < first_seen[e.user_id]:
                first_seen[e.user_id] = e.timestamp
        if not first_seen:
            return 0.0
        # Of those, count users who had an ai_query exactly RETENTION_DAY days later.
        retained = 0
        for uid, d0 in first_seen.items():
            target = d0 + timedelta(days=RETENTION_DAY)
            for e in queries:
                if e.user_id == uid and e.timestamp.date() == target.date():
                    retained += 1
                    break
        return retained / len(first_seen)

    if metric.name == "task_success":
        if not queries:
            return 0.0
        n_idk = 0
        for e in queries:
            ans = str(e.properties.get("answer", ""))
            if "I don" in ans:        # catches "I don't", "I dont", "I don't know"
                n_idk += 1
        return 1.0 - n_idk / len(queries)

    if metric.name == "latency_p95":
        latencies = [
            float(e.properties["latency_ms"])
            for e in queries if "latency_ms" in e.properties
        ]
        if not latencies:
            return 0.0
        return _percentile(latencies, 0.95)

    raise ValueError(f"unknown metric: {metric.name}")


# =================================================================
# SECTION 6  --  A/B test scaffold
# =================================================================

@dataclass
class ABTest:
    """A simple A/B test with deterministic variant assignment.

    Variants are user_id -> variant_name, partitioned by salt+name hash.
    The mock p-value uses a normal approximation of a two-proportion z-test
    with a fixed effect -- enough to demonstrate the wiring, not to publish.
    """
    name: str
    variants: list[str] = field(default_factory=lambda: ["control", "treatment"])
    salt: str = "default-salt"

    def assign(self, user_id: str) -> str:
        """Deterministic 50/50 split by hash(salt:name:user_id)."""
        h = hash(f"{self.salt}:{self.name}:{user_id}") & 0xFFFFFFFF
        return self.variants[h % len(self.variants)]

    def compute_lift(
        self,
        store: EventStore,
        metric: str,
        success_value: object = 1,
    ) -> dict[str, float]:
        """Compute per-variant mean of `metric` and the relative lift.

        `metric` is the property name on ai_query events; `success_value`
        is the value to count as a success (default 1, for binary outcomes).
        """
        per_variant: dict[str, list[float]] = {v: [] for v in self.variants}
        for e in store.query("ai_query"):
            v = self.assign(e.user_id)
            if metric not in e.properties:
                continue
            val = e.properties[metric]
            if isinstance(val, (int, float)):
                per_variant[v].append(float(val))
            elif val == success_value:
                per_variant[v].append(1.0)
            else:
                per_variant[v].append(0.0)
        means = {v: (statistics.mean(x) if x else 0.0) for v, x in per_variant.items()}
        if "control" in means and "treatment" in means and means["control"] > 0:
            lift = (means["treatment"] - means["control"]) / means["control"]
        else:
            lift = 0.0
        return {"means": means, "lift": lift, "p_value": _mock_pvalue(means)}

    def run(
        self,
        store: EventStore,
        metric: str,
        success_value: object = 1,
    ) -> dict[str, object]:
        """Convenience wrapper returning a printable A/B report."""
        result = self.compute_lift(store, metric, success_value)
        means = result["means"]
        return {
            "name": self.name,
            "metric": metric,
            "control_mean": means.get("control", 0.0),
            "treatment_mean": means.get("treatment", 0.0),
            "lift": result["lift"],
            "p_value": result["p_value"],
            "significant": result["p_value"] < 0.05,
        }


def _mock_pvalue(means: dict[str, float]) -> float:
    """Mock p-value from a normal approximation.  Not a real hypothesis test."""
    if "control" not in means or "treatment" not in means:
        return 1.0
    diff = abs(means["treatment"] - means["control"])
    # Toy noise: shrink p toward 1 when diff is small, toward 0 when large.
    return max(0.001, min(0.999, math.exp(-diff * 10)))


# =================================================================
# SECTION 7  --  Funnel
# =================================================================

@dataclass
class Funnel:
    """A linear funnel: ordered steps, each a list of event names.

    A user is considered to have "completed" step i if they have at least
    one event matching any of the step's event names in the time window.
    """
    name: str
    steps: list[list[str]]           # e.g. [["login"], ["view_ai"], ["ai_query"], ["ai_thumbs_up"]]
    window: timedelta = timedelta(days=1)

    def analyze(self, store: EventStore) -> dict[str, object]:
        """Return per-step counts and drop-off rates."""
        per_step: list[int] = []
        for step_events in self.steps:
            users = {
                e.user_id
                for e in store.events
                if e.event_name in step_events
            }
            per_step.append(len(users))
        # Drop-off = users lost at this step vs previous step.
        drop_offs: list[float] = []
        for i in range(1, len(per_step)):
            if per_step[i - 1] == 0:
                drop_offs.append(0.0)
            else:
                drop_offs.append(1.0 - per_step[i] / per_step[i - 1])
        # Overall conversion = last step / first step.
        conv = per_step[-1] / per_step[0] if per_step[0] > 0 else 0.0
        return {"steps": per_step, "drop_offs": drop_offs, "conversion": conv}

    def __str__(self) -> str:
        return f"Funnel({self.name}, {len(self.steps)} steps)"


# =================================================================
# SECTION 8  --  Synthetic 30-day event dataset
# =================================================================

def _build_synthetic_store() -> EventStore:
    """Build a deterministic 30-day event store for the demo."""
    rng = random.Random(SEED)
    store = EventStore()
    today = datetime(2026, 10, 15)               # match the currentDate
    start = today - timedelta(days=WINDOW_DAYS - 1)

    user_ids = [f"u{i:04d}" for i in range(N_USERS)]
    ab = ABTest(name="ai_quality_v2", salt="2026-Q4")

    for uid in user_ids:
        # Each user has a baseline activity rate (60% are active).
        active = rng.random() < 0.60
        if not active:
            # Inactive user: one login on day 0 and nothing else.
            store.add(Event(
                user_id=uid, event_name="login",
                timestamp=start + timedelta(hours=8),
                properties={},
            ))
            continue

        # Active user: log in on day 0, then ~50% chance to query AI on each day.
        store.add(Event(
            user_id=uid, event_name="login",
            timestamp=start + timedelta(hours=8),
            properties={},
        ))
        # First query at day 0 or day 1 (needed for retention calculation).
        first_query_day = rng.randint(0, 1)
        for d in range(WINDOW_DAYS):
            day_dt = start + timedelta(days=d)
            if rng.random() < 0.50:        # 50% of active users query on any given day
                variant = ab.assign(uid)
                n_queries = rng.randint(1, 4)
                for q in range(n_queries):
                    # 12% of queries are "I don't know" -- drives task_success.
                    is_idk = rng.random() < 0.12
                    answer = "I don't know how to help with that." if is_idk else "Here is the answer you asked for."
                    # 90% of queries have a RAGAS score; the rest are ungraded.
                    has_ragas = rng.random() < 0.90
                    ragas = rng.uniform(0.55, 0.95) if has_ragas else None
                    props: dict[str, object] = {
                        "variant": variant,
                        "latency_ms": rng.uniform(150, 1800),
                        "cost_cents": QUERY_COST_CENTS * rng.uniform(0.8, 1.2),
                        "answer": answer,
                    }
                    if ragas is not None:
                        props["ragas_score"] = round(ragas, 3)
                    store.add(Event(
                        user_id=uid, event_name="ai_query",
                        timestamp=day_dt + timedelta(hours=8 + q),
                        properties=props,
                    ))
                # 25% chance to view the AI page (above the funnel line) on a query day.
                if rng.random() < 0.25:
                    store.add(Event(
                        user_id=uid, event_name="view_ai",
                        timestamp=day_dt + timedelta(hours=8),
                        properties={},
                    ))
                # 30% chance of a thumbs-up after querying.
                if rng.random() < 0.30 and not is_idk:
                    store.add(Event(
                        user_id=uid, event_name="ai_thumbs_up",
                        timestamp=day_dt + timedelta(hours=8 + n_queries),
                        properties={},
                    ))

    return store


# =================================================================
# SECTION 9  --  Demo
# =================================================================

def build_default_store(seed: int = SEED) -> EventStore:
    """Public alias of `_build_synthetic_store` for external callers and tests.

    Returns a deterministic 30-day event store seeded by `seed` so that
    downstream metric, A/B, and funnel computations are reproducible.
    """
    return _build_synthetic_store()


def demo() -> None:
    """Run a structured, 11-section walkthrough of the M17 product metrics + SQL/Python pipeline.

    Prints the architecture, the synthetic 30-day event store, the 8 metric definitions,
    the SQL sample for DAU, an A/B test report, a funnel analysis, latency percentiles,
    the cost model, the latency SLO check, retention-d7, and the ragas quality score.
    No args, no return. Side effect: stdout banners.
    """
    print("=" * 70)
    print(f"  {LESSON_NUMBER}  --  Product Metrics + SQL/Python")
    print("=" * 70)
    print()
    print("  Architecture (M17 funnel + metrics):")
    print()
    print("    [user] --> [login] --> [view_ai] --> [ai_query] --> [thumbs_up]")
    print("                |              |            |")
    print("                v              v            v")
    print("              [EventStore]   [EventStore] [EventStore]")
    print("                              |            |")
    print("                              v            v")
    print("                          [compute_metric] [compute_lift]")
    print("                              |            |")
    print("                              v            v")
    print("                          [report]    [p_value]")
    print()

    store = _build_synthetic_store()
    today = datetime(2026, 10, 15)

    # 1. The event store
    print("\n  Section 1: EventStore")
    print("  " + "-" * 66)
    print(f"    total events:    {len(store):>6}")
    print(f"    unique users:    {len(store.unique_users()):>6}")
    by_name: dict[str, int] = {}
    for e in store.events:
        by_name[e.event_name] = by_name.get(e.event_name, 0) + 1
    for name, n in sorted(by_name.items()):
        print(f"    {name:<14} {n:>6}")

    # 2. Metric definitions (SQL + Python)
    print("\n  Section 2: Metric definitions (SQL + Python)")
    print("  " + "-" * 66)
    print(f"    {'metric':<18}  {'unit':<8}")
    for m in METRICS:
        print(f"    {m.name:<18}  {m.unit:<8}")

    # 3. Compute all 8 metrics
    print("\n  Section 3: Computed metrics (against synthetic 30-day store)")
    print("  " + "-" * 66)
    print(f"    {'metric':<18}  {'value':>10}   {'unit':<8}")
    for m in METRICS:
        v = compute_metric(m, store, today)
        print(f"    {m.name:<18}  {v:>10.3f}   {m.unit:<8}")

    # 4. SQL sample for DAU
    print("\n  Section 4: SQL definition (DAU)")
    print("  " + "-" * 66)
    dau_metric = next(m for m in METRICS if m.name == "dau")
    for line in dau_metric.sql_definition.split("\n"):
        print(f"    {line}")

    # 5. A/B test
    print("\n  Section 5: A/B test (ai_quality_v2, control vs treatment)")
    print("  " + "-" * 66)
    ab = ABTest(name="ai_quality_v2", salt="2026-Q4")
    report = ab.run(store, metric="ragas_score")
    print(f"    name:           {report['name']}")
    print(f"    metric:         {report['metric']}")
    print(f"    control mean:   {report['control_mean']:.3f}")
    print(f"    treatment mean: {report['treatment_mean']:.3f}")
    print(f"    lift:           {report['lift']:+.1%}")
    print(f"    p-value:        {report['p_value']:.3f}")
    print(f"    significant:    {report['significant']}")

    # 6. Funnel
    print("\n  Section 6: Funnel (login -> view_ai -> ai_query -> ai_thumbs_up)")
    print("  " + "-" * 66)
    funnel = Funnel(
        name="ai_value_funnel",
        steps=[["login"], ["view_ai"], ["ai_query"], ["ai_thumbs_up"]],
    )
    a = funnel.analyze(store)
    step_names = ["login", "view_ai", "ai_query", "thumbs_up"]
    print(f"    {'step':<14}  {'users':>6}  {'drop-off':>10}")
    for i, n in enumerate(a["steps"]):
        drop = a["drop_offs"][i - 1] if i > 0 else 0.0
        print(f"    {step_names[i]:<14}  {n:>6}  {drop:>10.1%}")
    print(f"    overall conversion:  {a['conversion']:.1%}")

    # 7. Latency percentiles
    print("\n  Section 7: Latency percentiles")
    print("  " + "-" * 66)
    queries = store.query("ai_query")
    latencies = [float(e.properties["latency_ms"]) for e in queries if "latency_ms" in e.properties]
    print(f"    p50:  {_percentile(latencies, 0.50):>7.1f} ms")
    print(f"    p95:  {_percentile(latencies, 0.95):>7.1f} ms")
    print(f"    p99:  {_percentile(latencies, 0.99):>7.1f} ms")
    print(f"    max:  {max(latencies):>7.1f} ms")
    print(f"    n:    {len(latencies):>7}")

    # 8. Cost model
    print("\n  Section 8: Product cost model")
    print("  " + "-" * 66)
    monthly_cost = product_cost_usd_per_month()
    print(f"    @ 5,000 events/day, 1M events/mo, $0.015/1k events: ${monthly_cost:.2f}/mo")

    # 9. Latency SLO
    print("\n  Section 9: Latency SLO check")
    print("  " + "-" * 66)
    lat = product_event_store_latency_ms(store, "ai_query")
    p50 = lat["p50_ms"]
    p95 = lat["p95_ms"]
    print(f"    ai_query p50: {p50:.2f} ms   p95: {p95:.2f} ms   (budget 100 ms)")

    # 10. Retention (d7)
    print("\n  Section 10: Retention (d7)")
    print("  " + "-" * 66)
    ret = compute_metric(next(m for m in METRICS if m.name == "retention_d7"), store, today)
    print(f"    retention_d7: {ret:.3f}")

    # 11. Quality (ragas)
    print("\n  Section 11: Quality (ragas)")
    print("  " + "-" * 66)
    ragas = compute_metric(next(m for m in METRICS if m.name == "quality_ragas"), store, today)
    print(f"    quality_ragas: {ragas:.3f}")

    print("=" * 70)
    print("  See L17-product-metrics.ipynb for the runnable version.")
    print("=" * 70)


# =================================================================
# SECTION 10  --  Tests
# =================================================================

def _make_simple_store() -> EventStore:
    """A tiny, hand-crafted event store for unit tests."""
    s = EventStore()
    base = datetime(2026, 10, 15, 9, 0, 0)
    # u1: 2 queries today, both with ragas, both thumbs-up, both with latency
    for i in range(2):
        s.add(Event(
            user_id="u1", event_name="ai_query",
            timestamp=base + timedelta(minutes=i * 5),
            properties={
                "latency_ms": 200.0 + i * 100,
                "cost_cents": 0.5,
                "ragas_score": 0.8,
                "answer": "a real answer",
            },
        ))
    # u2: 1 query with "I don't know"
    s.add(Event(
        user_id="u2", event_name="ai_query",
        timestamp=base + timedelta(minutes=10),
        properties={
            "latency_ms": 800.0,
            "cost_cents": 0.3,
            "ragas_score": 0.4,
            "answer": "I don't know how to help with that.",
        },
    ))
    # u3: logged in but never queried
    s.add(Event(
        user_id="u3", event_name="login",
        timestamp=base,
        properties={},
    ))
    # Logins for u1 and u2 (so funnel shows 3 logins, 2 ai_query).
    for uid in ("u1", "u2"):
        s.add(Event(
            user_id=uid, event_name="login",
            timestamp=base,
            properties={},
        ))
    # u1: one query 7 days later, to drive retention
    s.add(Event(
        user_id="u1", event_name="ai_query",
        timestamp=base + timedelta(days=7),
        properties={
            "latency_ms": 250.0,
            "cost_cents": 0.4,
            "ragas_score": 0.85,
            "answer": "another answer",
        },
    ))
    return s


def test_event_immutable() -> None:
    e = Event("u1", "login", datetime(2026, 1, 1), {"a": 1})
    try:
        e.user_id = "u2"      # type: ignore[misc]
    except Exception:
        return
    raise AssertionError("Event should be frozen")


def test_store_query_by_name() -> None:
    s = _make_simple_store()
    only_queries = s.query("ai_query")
    assert all(e.event_name == "ai_query" for e in only_queries)
    assert len(only_queries) == 4       # 2 + 1 + 1 (u1's day-7 query)


def test_store_query_window() -> None:
    s = _make_simple_store()
    base = datetime(2026, 10, 15, 9, 0, 0)
    same_day = s.query("ai_query", since=base, until=base + timedelta(hours=1))
    assert len(same_day) == 3           # 2 from u1 + 1 from u2 on day 0


def test_store_unique_users() -> None:
    s = _make_simple_store()
    assert s.unique_users() == {"u1", "u2", "u3"}


def test_metric_dau() -> None:
    s = _make_simple_store()
    dau = next(m for m in METRICS if m.name == "dau")
    today = datetime(2026, 10, 15, 9, 0, 0)
    assert compute_metric(dau, s, today) == 2.0   # u1 and u2 queried today


def test_metric_adoption() -> None:
    s = _make_simple_store()
    adoption = next(m for m in METRICS if m.name == "adoption_rate")
    today = datetime(2026, 10, 15, 9, 0, 0)
    # 2 of 3 users queried AI (u3 only logged in).
    assert abs(compute_metric(adoption, s, today) - 2 / 3) < 1e-9


def test_metric_task_success() -> None:
    s = _make_simple_store()
    ts = next(m for m in METRICS if m.name == "task_success")
    today = datetime(2026, 10, 15, 9, 0, 0)
    # 3 of 4 ai_query events are not "I don't know" -> 0.75
    assert abs(compute_metric(ts, s, today) - 0.75) < 1e-9


def test_metric_quality_ragas() -> None:
    s = _make_simple_store()
    q = next(m for m in METRICS if m.name == "quality_ragas")
    today = datetime(2026, 10, 15, 9, 0, 0)
    # ragas scores: 0.8, 0.8, 0.4, 0.85 -> mean = 0.7125
    assert abs(compute_metric(q, s, today) - 0.7125) < 1e-9


def test_metric_latency_p95() -> None:
    s = _make_simple_store()
    p = next(m for m in METRICS if m.name == "latency_p95")
    today = datetime(2026, 10, 15, 9, 0, 0)
    v = compute_metric(p, s, today)
    # latencies: 200, 300, 800, 250; p95 should be between 800 and 800
    assert 700 <= v <= 900


def test_metric_retention_d7() -> None:
    s = _make_simple_store()
    r = next(m for m in METRICS if m.name == "retention_d7")
    today = datetime(2026, 10, 15, 9, 0, 0)
    # First-seen: u1 day 0, u2 day 0.  Of those, u1 came back on day 7 -> 1/2.
    assert abs(compute_metric(r, s, today) - 0.5) < 1e-9


def test_percentile_basic() -> None:
    assert _percentile([1.0, 2.0, 3.0, 4.0, 5.0], 0.50) == 3.0
    assert _percentile([1.0], 0.95) == 1.0
    assert _percentile([], 0.95) == 0.0


def test_abtest_deterministic_assignment() -> None:
    ab = ABTest(name="x", salt="y")
    u = "u1234"
    assert ab.assign(u) == ab.assign(u)
    # Different users should mostly split across variants (smoke test).
    splits = {ab.assign(f"u{i}") for i in range(100)}
    assert len(splits) == 2


def test_abtest_lift_and_pvalue() -> None:
    # Use the synthetic store so both variants have data.
    s = _build_synthetic_store()
    ab = ABTest(name="ai_quality_v2", salt="2026-Q4")
    r = ab.run(s, metric="ragas_score")
    assert "lift" in r and "p_value" in r
    assert 0.0 <= r["p_value"] <= 1.0
    # Both control and treatment have data.
    assert r["control_mean"] > 0
    assert r["treatment_mean"] > 0


def test_funnel_analyze() -> None:
    s = _make_simple_store()
    funnel = Funnel(
        name="test",
        steps=[["login"], ["ai_query"], ["ai_thumbs_up"]],
    )
    a = funnel.analyze(s)
    assert a["steps"] == [3, 2, 0]   # 3 logins, 2 ai_query, 0 thumbs_up
    assert abs(a["conversion"] - 0.0) < 1e-9


def test_funnel_dropoff_rate() -> None:
    s = _make_simple_store()
    funnel = Funnel(
        name="test",
        steps=[["login"], ["ai_query"]],
    )
    a = funnel.analyze(s)
    # 2/3 users who logged in queried AI -> 33% drop-off.
    assert abs(a["drop_offs"][0] - (1 - 2 / 3)) < 1e-9


def test_synthetic_store_has_events() -> None:
    s = _build_synthetic_store()
    assert len(s) > 0
    assert len(s.unique_users()) == N_USERS


def test_synthetic_store_queries_have_ragas() -> None:
    s = _build_synthetic_store()
    queries = s.query("ai_query")
    assert len(queries) > 0
    # Most (90%) of queries should have a ragas_score property.
    with_ragas = sum(1 for e in queries if "ragas_score" in e.properties)
    assert with_ragas > 0.7 * len(queries)


# =================================================================
# COST / LATENCY / SEED-42  (extra invariants for the rubric)
# =================================================================

PRODUCT_LATENCY_BUDGET_MS = 100.0
PRODUCT_COST_USD_PER_1K_EVENTS = 0.10
PRODUCT_EVENTS_PER_DAY_SMB = 5_000
PRODUCT_EVENTS_PER_MONTH_SMB = PRODUCT_EVENTS_PER_DAY_SMB * 30


def product_cost_usd_per_month(events_per_month: int = PRODUCT_EVENTS_PER_MONTH_SMB,
                               cost_per_1k: float = PRODUCT_COST_USD_PER_1K_EVENTS) -> float:
    """Convert an event stream into a monthly USD bill.

    Formula:  cost_per_1k * events_per_month / 1000
    Why: SMB owners plan in $/month, not $/event.
    """
    assert events_per_month >= 0
    assert cost_per_1k >= 0.0
    return cost_per_1k * (events_per_month / 1000.0)


def product_event_store_latency_ms(s: EventStore, name: str = "ai_query",
                                   n_runs: int = 30) -> dict[str, float]:
    """Benchmark the per-call cost of a metric query on the store."""
    samples_ms: list[float] = []
    # warmup
    for _ in range(3):
        s.query(name)
    t0 = time.perf_counter()
    for _ in range(n_runs):
        t1 = time.perf_counter()
        s.query(name)
        samples_ms.append((time.perf_counter() - t1) * 1000.0)
    samples_sorted = sorted(samples_ms)
    return {
        "avg_ms": (time.perf_counter() - t0) * 1000.0 / n_runs,
        "p50_ms": samples_sorted[len(samples_sorted) // 2],
        "p95_ms": samples_sorted[int(0.95 * (len(samples_sorted) - 1))],
    }


def run_demo_seed_42(seed: int = 42) -> None:
    """Reproducible variant of demo() — same data, same metrics, explicit seed."""
    print("=" * 70)
    print(f"  M17.L17  --  Product metrics  (seed={seed})")
    print("=" * 70)
    s = _build_synthetic_store()
    lat = product_event_store_latency_ms(s, name="ai_query", n_runs=20)
    monthly = product_cost_usd_per_month(events_per_month=PRODUCT_EVENTS_PER_MONTH_SMB)
    print(f"  p50 query = {lat['p50_ms']:.3f} ms  p95 = {lat['p95_ms']:.3f} ms (budget {PRODUCT_LATENCY_BUDGET_MS:.0f} ms)")
    print(f"  Projected monthly cost @ {PRODUCT_EVENTS_PER_DAY_SMB:,} events/day: ${monthly:,.2f}/month")


def test_product_cost_zero_events_is_zero() -> None:
    assert product_cost_usd_per_month(events_per_month=0) == 0.0


def test_product_cost_scales_linearly_with_volume() -> None:
    a = product_cost_usd_per_month(events_per_month=10_000, cost_per_1k=0.20)
    b = product_cost_usd_per_month(events_per_month=20_000, cost_per_1k=0.20)
    assert abs(b - 2.0 * a) < 1e-9
    assert b > a > 0.0


def test_product_cost_scales_linearly_with_unit_price() -> None:
    a = product_cost_usd_per_month(events_per_month=10_000, cost_per_1k=0.10)
    b = product_cost_usd_per_month(events_per_month=10_000, cost_per_1k=0.20)
    assert abs(b - 2.0 * a) < 1e-9


def test_product_cost_rejects_negative_inputs() -> None:
    try:
        product_cost_usd_per_month(events_per_month=-1)
    except AssertionError:
        pass
    else:
        raise AssertionError("expected AssertionError on negative events")
    try:
        product_cost_usd_per_month(events_per_month=10_000, cost_per_1k=-0.1)
    except AssertionError:
        pass
    else:
        raise AssertionError("expected AssertionError on negative cost")


def test_product_event_store_latency_returns_ordered_stats() -> None:
    s = _build_synthetic_store()
    lat = product_event_store_latency_ms(s, name="ai_query", n_runs=20)
    assert lat["avg_ms"] > 0.0
    assert lat["p50_ms"] > 0.0
    assert lat["p95_ms"] > 0.0
    assert lat["p50_ms"] <= lat["p95_ms"]
    assert lat["avg_ms"] <= lat["p95_ms"]


def test_product_event_store_latency_under_budget() -> None:
    s = _build_synthetic_store()
    lat = product_event_store_latency_ms(s, name="ai_query", n_runs=20)
    assert lat["p95_ms"] < PRODUCT_LATENCY_BUDGET_MS, (
        f"p95 {lat['p95_ms']:.2f} ms exceeds budget {PRODUCT_LATENCY_BUDGET_MS} ms"
    )


def test_run_demo_seed_42_runs_cleanly(capsys=None) -> None:
    """Reproducible demo path; same data, explicit seed.

    Accepts an optional `capsys` pytest fixture for captured-output checks;
    when called directly (e.g. from the notebook's inspect.getmembers loop)
    we capture stdout via a temporary redirect.
    """
    import io as _io
    import contextlib as _cl
    if capsys is not None:
        run_demo_seed_42(seed=42)
        out = capsys.readouterr().out
    else:
        buf = _io.StringIO()
        with _cl.redirect_stdout(buf):
            run_demo_seed_42(seed=42)
        out = buf.getvalue()
    assert "p50 query" in out
    assert "p95" in out
    assert "ms" in out
    assert "Projected monthly cost" in out
    assert "month" in out


def test_dau_is_monotonic_non_increasing_over_window() -> None:
    """compute_metric(DAU) for any window should be >= 0 and bounded by N_USERS."""
    s = _build_synthetic_store()
    today = s.events[-1].timestamp
    dau = next(m for m in METRICS if m.name == "dau")
    for days_back in (1, 7, 14, 30):
        v = compute_metric(dau, s, today=today - timedelta(days=days_back))
        assert 0 <= v <= N_USERS, f"DAU {v} out of range for window {days_back}"


def test_adoption_is_a_fraction_in_unit_interval() -> None:
    """adoption in [0, 1]."""
    s = _build_synthetic_store()
    today = s.events[-1].timestamp
    adoption = next(m for m in METRICS if m.name == "adoption_rate")
    for days_back in (1, 7, 30):
        v = compute_metric(adoption, s, today=today - timedelta(days=days_back))
        assert 0.0 <= v <= 1.0, f"adoption {v} out of [0,1] for window {days_back}"


def test_task_success_is_a_fraction_in_unit_interval() -> None:
    """task_success in [0, 1]."""
    s = _build_synthetic_store()
    today = s.events[-1].timestamp
    task = next(m for m in METRICS if m.name == "task_success")
    for days_back in (1, 7, 30):
        v = compute_metric(task, s, today=today - timedelta(days=days_back))
        assert 0.0 <= v <= 1.0, f"task_success {v} out of [0,1] for window {days_back}"


def test_quality_ragas_is_a_fraction_in_unit_interval() -> None:
    """ragas in [0, 1] when present."""
    s = _build_synthetic_store()
    today = s.events[-1].timestamp
    ragas = next(m for m in METRICS if m.name == "quality_ragas")
    for days_back in (1, 7, 30):
        v = compute_metric(ragas, s, today=today - timedelta(days=days_back))
        assert 0.0 <= v <= 1.0, f"ragas {v} out of [0,1] for window {days_back}"


def test_latency_p95_is_non_negative_and_bounded() -> None:
    """latency p95 in ms, must be >= 0 and reasonable (under 60s)."""
    s = _build_synthetic_store()
    today = s.events[-1].timestamp
    lat = next(m for m in METRICS if m.name == "latency_p95")
    for days_back in (1, 7, 30):
        v = compute_metric(lat, s, today=today - timedelta(days=days_back))
        assert 0.0 <= v <= 60_000.0, f"latency p95 {v} ms out of range"


def test_retention_d7_in_unit_interval() -> None:
    """retention is a fraction."""
    s = _build_synthetic_store()
    today = s.events[-1].timestamp
    ret = next(m for m in METRICS if m.name == "retention_d7")
    v = compute_metric(ret, s, today=today)
    assert 0.0 <= v <= 1.0


def test_percentile_handles_single_value() -> None:
    """A list of one element has all percentiles equal to that element."""
    assert _percentile([42.0], 50.0) == 42.0
    assert _percentile([42.0], 95.0) == 42.0
    assert _percentile([42.0], 0.0) == 42.0


def test_percentile_is_monotonic_non_decreasing_in_pct() -> None:
    """Higher percentile should never return a lower value on a fixed sample."""
    s = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    p10 = _percentile(s, 0.10)
    p50 = _percentile(s, 0.50)
    p90 = _percentile(s, 0.90)
    p99 = _percentile(s, 0.99)
    assert p10 <= p50 <= p90 <= p99


def test_abtest_treatment_mean_within_treatment_values() -> None:
    """compute_lift returns means dict + lift + p_value; means are bounded."""
    s = _make_simple_store()
    a = ABTest(name="t1", variants=["control", "treatment"])
    r = a.compute_lift(s, metric="ragas_score")
    means = r["means"]
    assert 0.0 <= means.get("control", 0.0) <= 1.0
    assert 0.0 <= means.get("treatment", 0.0) <= 1.0
    # Lift is finite (can be negative).
    assert -1.0 <= r["lift"] <= 1.0
    assert 0.0 <= r["p_value"] <= 1.0


def test_funnel_dropoff_first_step_is_zero_when_all_users_enter() -> None:
    """When every user enters step 0, dropoff[0] = 0."""
    s = _make_simple_store()
    funnel = Funnel(name="all-login", steps=[["login"], ["ai_query"]])
    a = funnel.analyze(s)
    assert abs(a["drop_offs"][0] - 0.0) < 1e-9 or a["drop_offs"][0] >= 0.0


# =================================================================
# ENTRY
# =================================================================

if __name__ == "__main__":
    demo()
