"""
================================================================
M11 L11  --  Observability and Cost
================================================================

Run:    python3 lessons/m11-observability/L11-observability-cost.py
Keys:   none

Builds a tiny observability + cost stack from scratch:
  * Metrics: counter, gauge, histogram (with P50/P95/P99)
  * Traces:  parent/child spans, duration, attributes
  * Logs:    structured JSON, level-filtered
  * Cost:    per-call USD, aggregates by model/user/feature
  * Alerter: threshold rules with severity (info, warn, error, page)
  * Dashboard: P50 / P95 / P99, error rate, total cost, top-N

The lesson's point: "the system is up" is not observability.
You need the three pillars (metrics, logs, traces) plus cost.
Cost is the fourth pillar of LLM apps.
"""

from __future__ import annotations

import json
import math
import random
import statistics
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable


# =================================================================
# CONFIG
# =================================================================

LESSON_NUMBER = "M11.L11"
SEED = 19

# Cost rates (USD per 1K tokens) -- representative, not real prices
COST_PER_1K_INPUT = {
    "gpt-4o": 0.0050,
    "gpt-4o-mini": 0.000150,
    "claude-sonnet": 0.0030,
    "claude-haiku": 0.000250,
    "mock-llm": 0.000000,
}
COST_PER_1K_OUTPUT = {
    "gpt-4o": 0.0150,
    "gpt-4o-mini": 0.000600,
    "claude-sonnet": 0.0150,
    "claude-haiku": 0.001250,
    "mock-llm": 0.000000,
}

# Latency distributions (ms) per model: (mean, stdev)
LATENCY_PROFILE = {
    "gpt-4o": (800, 200),
    "gpt-4o-mini": (300, 80),
    "claude-sonnet": (700, 180),
    "claude-haiku": (250, 70),
    "mock-llm": (5, 2),
}

# Error rate (fraction of calls that fail)
ERROR_RATE = 0.04


# =================================================================
# SECTION 1  --  Metrics
# =================================================================

@dataclass
class Metric:
    """A single metric observation: name + value + tags + timestamp."""
    name: str
    value: float
    tags: dict[str, str] = field(default_factory=dict)
    ts_ms: int = 0


class Counter:
    """A monotonically increasing counter (e.g., total calls, total errors)."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._value: float = 0.0

    def inc(self, amount: float = 1.0) -> None:
        if amount < 0:
            raise ValueError("Counter cannot decrease")
        self._value += amount

    @property
    def value(self) -> float:
        return self._value

    def __repr__(self) -> str:
        return f"Counter({self.name}={self._value})"


class Gauge:
    """A point-in-time value that can go up or down (e.g., queue depth)."""

    def __init__(self, name: str, value: float = 0.0) -> None:
        self.name = name
        self._value: float = value

    def set(self, value: float) -> None:
        self._value = value

    def inc(self, amount: float = 1.0) -> None:
        self._value += amount

    def dec(self, amount: float = 1.0) -> None:
        self._value -= amount

    @property
    def value(self) -> float:
        return self._value

    def __repr__(self) -> str:
        return f"Gauge({self.name}={self._value})"


class Histogram:
    """A distribution of values; computes P50/P95/P99 on demand."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._values: list[float] = []

    def observe(self, value: float) -> None:
        self._values.append(value)

    @property
    def count(self) -> int:
        return len(self._values)

    @property
    def mean(self) -> float:
        return statistics.mean(self._values) if self._values else 0.0

    def percentile(self, p: float) -> float:
        """Return the p-th percentile (0-100) of observed values."""
        if not self._values:
            return 0.0
        s = sorted(self._values)
        # Linear interpolation between closest ranks
        k = (len(s) - 1) * (p / 100.0)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return s[int(k)]
        return s[f] * (c - k) + s[c] * (k - f)

    def p50(self) -> float:
        return self.percentile(50)

    def p95(self) -> float:
        return self.percentile(95)

    def p99(self) -> float:
        return self.percentile(99)

    def __repr__(self) -> str:
        return f"Histogram({self.name} n={self.count} mean={self.mean:.2f})"


@dataclass
class MetricSeries:
    """A bundle of related counters, gauges, and histograms for one subsystem."""
    counters: dict[str, Counter] = field(default_factory=dict)
    gauges: dict[str, Gauge] = field(default_factory=dict)
    histograms: dict[str, Histogram] = field(default_factory=dict)

    def counter(self, name: str) -> Counter:
        if name not in self.counters:
            self.counters[name] = Counter(name)
        return self.counters[name]

    def gauge(self, name: str) -> Gauge:
        if name not in self.gauges:
            self.gauges[name] = Gauge(name)
        return self.gauges[name]

    def histogram(self, name: str) -> Histogram:
        if name not in self.histograms:
            self.histograms[name] = Histogram(name)
        return self.histograms[name]


# =================================================================
# SECTION 2  --  Traces
# =================================================================

@dataclass
class Span:
    """One unit of work in a trace.  Parent spans contain child spans."""
    span_id: str
    parent_id: str | None
    name: str
    start_ms: float
    end_ms: float = 0.0
    attributes: dict[str, Any] = field(default_factory=dict)
    status: str = "ok"           # "ok" | "error"
    children: list[str] = field(default_factory=list)

    @property
    def duration_ms(self) -> float:
        return max(0.0, self.end_ms - self.start_ms)

    def finish(self, end_ms: float | None = None, status: str = "ok") -> None:
        self.end_ms = end_ms if end_ms is not None else time.time() * 1000.0
        self.status = status


@dataclass
class Trace:
    """A trace = a tree of spans sharing a trace_id."""
    trace_id: str
    spans: dict[str, Span] = field(default_factory=dict)
    root_id: str | None = None

    def start_span(self, name: str, parent_id: str | None = None,
                   attributes: dict[str, Any] | None = None) -> Span:
        """Start a new span.  Returns the Span; call .finish() when done."""
        span_id = f"{self.trace_id}-s{len(self.spans)}"
        span = Span(
            span_id=span_id,
            parent_id=parent_id,
            name=name,
            start_ms=time.time() * 1000.0,
            attributes=attributes or {},
        )
        self.spans[span_id] = span
        if parent_id is not None and parent_id in self.spans:
            self.spans[parent_id].children.append(span_id)
        if self.root_id is None:
            self.root_id = span_id
        return span

    def total_duration_ms(self) -> float:
        """Total wall-clock from root start to last span end."""
        if self.root_id is None or not self.spans:
            return 0.0
        starts = [s.start_ms for s in self.spans.values()]
        ends = [s.end_ms for s in self.spans.values() if s.end_ms > 0]
        if not ends:
            return 0.0
        return max(ends) - min(starts)

    def span_count(self) -> int:
        return len(self.spans)


# =================================================================
# SECTION 3  --  Cost tracker
# =================================================================

@dataclass
class CostRecord:
    """One LLM call's cost record."""
    call_id: str
    ts_ms: int
    model: str
    feature: str
    user_id: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: float
    error: bool = False


def compute_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    """Compute USD cost for a call given a model and token counts."""
    in_rate = COST_PER_1K_INPUT.get(model, 0.0)
    out_rate = COST_PER_1K_OUTPUT.get(model, 0.0)
    return (input_tokens / 1000.0) * in_rate + (output_tokens / 1000.0) * out_rate


class CostTracker:
    """Aggregates cost records; supports breakdowns by model/user/feature."""

    def __init__(self) -> None:
        self.records: list[CostRecord] = []

    def add(self, record: CostRecord) -> None:
        self.records.append(record)

    def total_cost_usd(self) -> float:
        return sum(r.cost_usd for r in self.records)

    def total_input_tokens(self) -> int:
        return sum(r.input_tokens for r in self.records)

    def total_output_tokens(self) -> int:
        return sum(r.output_tokens for r in self.records)

    def total_calls(self) -> int:
        return len(self.records)

    def error_count(self) -> int:
        return sum(1 for r in self.records if r.error)

    def error_rate(self) -> float:
        if not self.records:
            return 0.0
        return self.error_count() / len(self.records)

    def by_model(self) -> dict[str, float]:
        out: dict[str, float] = defaultdict(float)
        for r in self.records:
            out[r.model] += r.cost_usd
        return dict(out)

    def by_user(self) -> dict[str, float]:
        out: dict[str, float] = defaultdict(float)
        for r in self.records:
            out[r.user_id] += r.cost_usd
        return dict(out)

    def by_feature(self) -> dict[str, float]:
        out: dict[str, float] = defaultdict(float)
        for r in self.records:
            out[r.feature] += r.cost_usd
        return dict(out)

    def top_n(self, group_by: str, n: int = 5) -> list[tuple[str, float]]:
        """Return the top-N keys by cost for a given grouping field."""
        if group_by == "model":
            agg = self.by_model()
        elif group_by == "user":
            agg = self.by_user()
        elif group_by == "feature":
            agg = self.by_feature()
        else:
            raise ValueError(f"unknown group_by: {group_by}")
        return sorted(agg.items(), key=lambda kv: kv[1], reverse=True)[:n]


# =================================================================
# SECTION 4  --  Structured logger
# =================================================================

LEVELS = {"debug": 10, "info": 20, "warn": 30, "error": 40}


class Logger:
    """Structured (JSON) logger with level filtering."""

    def __init__(self, level: str = "info", sink: list[dict[str, Any]] | None = None) -> None:
        self.level = level
        self.threshold = LEVELS.get(level, 20)
        # Default sink is an in-memory list; production would write to stdout/files
        self.sink: list[dict[str, Any]] = sink if sink is not None else []

    def _emit(self, level: str, message: str, **fields: Any) -> None:
        if LEVELS.get(level, 0) < self.threshold:
            return
        record = {
            "ts_ms": int(time.time() * 1000),
            "level": level,
            "message": message,
            **fields,
        }
        self.sink.append(record)

    def debug(self, message: str, **fields: Any) -> None:
        self._emit("debug", message, **fields)

    def info(self, message: str, **fields: Any) -> None:
        self._emit("info", message, **fields)

    def warn(self, message: str, **fields: Any) -> None:
        self._emit("warn", message, **fields)

    def error(self, message: str, **fields: Any) -> None:
        self._emit("error", message, **fields)

    def lines(self) -> list[str]:
        """Return the log as a list of JSON strings (one per record)."""
        return [json.dumps(r, sort_keys=True) for r in self.sink]

    def filter(self, level: str) -> list[dict[str, Any]]:
        return [r for r in self.sink if r["level"] == level]


# =================================================================
# SECTION 5  --  Alerter
# =================================================================

# Severity ordering: info < warn < error < page
SEVERITY_ORDER = {"info": 0, "warn": 1, "error": 2, "page": 3}


@dataclass(frozen=True)
class AlertRule:
    """A threshold rule: when the metric crosses threshold, fire severity."""
    name: str
    metric: str                 # e.g., "error_rate", "p95_latency_ms", "cost_usd"
    comparator: str             # ">", ">=", "<", "<="
    threshold: float
    severity: str               # info | warn | error | page

    def fires(self, value: float) -> bool:
        if self.comparator == ">":
            return value > self.threshold
        if self.comparator == ">=":
            return value >= self.threshold
        if self.comparator == "<":
            return value < self.threshold
        if self.comparator == "<=":
            return value <= self.threshold
        raise ValueError(f"unknown comparator: {self.comparator}")


@dataclass
class Alert:
    rule: AlertRule
    value: float
    ts_ms: int
    message: str

    def __str__(self) -> str:
        return f"[{self.rule.severity.upper():<5}] {self.rule.name}: {self.rule.metric}={self.value} {self.rule.comparator} {self.rule.threshold}"


class Alerter:
    """Evaluates a set of rules against current metric values; fires alerts."""

    def __init__(self, rules: list[AlertRule] | None = None) -> None:
        self.rules: list[AlertRule] = rules if rules is not None else []
        self.fired: list[Alert] = []

    def add_rule(self, rule: AlertRule) -> None:
        self.rules.append(rule)

    def evaluate(self, values: dict[str, float]) -> list[Alert]:
        """Check every rule against the provided metric values."""
        fired: list[Alert] = []
        for rule in self.rules:
            if rule.metric in values and rule.fires(values[rule.metric]):
                alert = Alert(
                    rule=rule,
                    value=values[rule.metric],
                    ts_ms=int(time.time() * 1000),
                    message=f"{rule.name} fired: {rule.metric}={values[rule.metric]}",
                )
                self.fired.append(alert)
                fired.append(alert)
        return fired

    def highest_severity(self) -> str:
        if not self.fired:
            return "info"
        return max(
            (a.rule.severity for a in self.fired),
            key=lambda s: SEVERITY_ORDER.get(s, 0),
        )


# =================================================================
# SECTION 6  --  Dashboard
# =================================================================

@dataclass
class Dashboard:
    """A read-only summary view over metrics + cost + alerts."""
    metrics: MetricSeries
    tracker: CostTracker
    alerter: Alerter

    def summary(self) -> dict[str, Any]:
        lat = self.metrics.histograms.get("latency_ms")
        return {
            "total_calls": self.tracker.total_calls(),
            "error_count": self.tracker.error_count(),
            "error_rate": round(self.tracker.error_rate(), 4),
            "p50_ms": round(lat.p50(), 2) if lat else 0.0,
            "p95_ms": round(lat.p95(), 2) if lat else 0.0,
            "p99_ms": round(lat.p99(), 2) if lat else 0.0,
            "total_cost_usd": round(self.tracker.total_cost_usd(), 6),
            "total_input_tokens": self.tracker.total_input_tokens(),
            "total_output_tokens": self.tracker.total_output_tokens(),
            "active_alerts": len(self.alerter.fired),
            "highest_severity": self.alerter.highest_severity(),
        }

    def print_summary(self) -> None:
        s = self.summary()
        print(f"    total_calls:        {s['total_calls']}")
        print(f"    error_count:        {s['error_count']}  (rate={s['error_rate']:.2%})")
        print(f"    p50 / p95 / p99:    {s['p50_ms']:>7.1f} / {s['p95_ms']:>7.1f} / {s['p99_ms']:>7.1f} ms")
        print(f"    total_cost_usd:     ${s['total_cost_usd']:.4f}")
        print(f"    input/output tok:   {s['total_input_tokens']} / {s['total_output_tokens']}")
        print(f"    alerts fired:       {s['active_alerts']}  (max severity={s['highest_severity']})")


# =================================================================
# SECTION 7  --  Mock LLM call generator
# =================================================================

MODELS = ["gpt-4o", "gpt-4o-mini", "claude-sonnet", "claude-haiku", "mock-llm"]
USERS = ["u-alice", "u-bob", "u-carol", "u-dave", "u-erin"]
FEATURES = ["rag", "summarize", "classify", "extract", "chat"]


def _rand_int(lo: int, hi: int, rng: random.Random) -> int:
    return rng.randint(lo, hi)


def simulate_call(call_id: str, rng: random.Random) -> CostRecord:
    """Generate one simulated LLM call record."""
    model = rng.choice(MODELS)
    user = rng.choice(USERS)
    feature = rng.choice(FEATURES)
    mean, stdev = LATENCY_PROFILE[model]
    latency = max(1.0, rng.gauss(mean, stdev))
    in_tok = _rand_int(200, 4000, rng)
    out_tok = _rand_int(50, 1500, rng)
    error = rng.random() < ERROR_RATE
    cost = compute_cost_usd(model, in_tok, out_tok) if not error else 0.0
    return CostRecord(
        call_id=call_id,
        ts_ms=int(time.time() * 1000) + _rand_int(0, 1000, rng),
        model=model,
        feature=feature,
        user_id=user,
        input_tokens=in_tok,
        output_tokens=out_tok,
        cost_usd=cost,
        latency_ms=latency,
        error=error,
    )


# =================================================================
# SECTION 8  --  End-to-end pipeline
# =================================================================

def run_pipeline(n_calls: int = 100, seed: int = SEED) -> tuple[MetricSeries, CostTracker, Logger, Alerter, Trace]:
    """Run n_calls simulated LLM calls; collect metrics, traces, cost, logs, alerts."""
    rng = random.Random(seed)
    metrics = MetricSeries()
    metrics.counter("calls_total")
    metrics.counter("errors_total")
    metrics.histogram("latency_ms")
    metrics.gauge("queue_depth")
    tracker = CostTracker()
    logger = Logger(level="info")
    trace = Trace(trace_id=f"t-{seed}")
    root = trace.start_span("pipeline_run", attributes={"n_calls": n_calls})

    for i in range(n_calls):
        call_id = f"c{i:04d}"
        child = trace.start_span("llm_call", parent_id=root.span_id,
                                 attributes={"call_id": call_id})
        rec = simulate_call(call_id, rng)
        tracker.add(rec)
        metrics.counter("calls_total").inc()
        if rec.error:
            metrics.counter("errors_total").inc()
            logger.error("llm_call_failed", call_id=call_id, model=rec.model)
        else:
            logger.info("llm_call_ok", call_id=call_id, model=rec.model,
                        cost_usd=round(rec.cost_usd, 6))
        metrics.histogram("latency_ms").observe(rec.latency_ms)
        child.finish(status="error" if rec.error else "ok")

    root.finish()
    return metrics, tracker, logger, _default_alerter(), trace


def _default_alerter() -> Alerter:
    """Default alert rules for the dashboard."""
    return Alerter(rules=[
        AlertRule("high_error_rate", "error_rate", ">", 0.05, "page"),
        AlertRule("slow_p95", "p95_latency_ms", ">", 1000.0, "error"),
        AlertRule("slow_p99", "p99_latency_ms", ">", 2000.0, "error"),
        AlertRule("cost_ceiling", "cost_usd", ">", 1.0, "warn"),
        AlertRule("healthy_throughput", "calls_total", ">", 0, "info"),
    ])


def evaluate_alerts(metrics: MetricSeries, tracker: CostTracker) -> Alerter:
    """Run the default alerter against the current metrics + tracker."""
    alerter = _default_alerter()
    lat = metrics.histograms["latency_ms"]
    values = {
        "error_rate": tracker.error_rate(),
        "p95_latency_ms": lat.p95(),
        "p99_latency_ms": lat.p99(),
        "cost_usd": tracker.total_cost_usd(),
        "calls_total": float(tracker.total_calls()),
    }
    alerter.evaluate(values)
    return alerter


# =================================================================
# SECTION 9  --  Demo
# =================================================================

def demo() -> None:
    print("=" * 70)
    print(f"  {LESSON_NUMBER}  --  Observability and Cost")
    print("=" * 70)

    # 1. Run the pipeline
    print("\n  Section 1: Run pipeline (100 simulated LLM calls)")
    print("  " + "-" * 66)
    metrics, tracker, logger, _, trace = run_pipeline(n_calls=100, seed=SEED)
    print(f"    calls:        {tracker.total_calls()}")
    print(f"    errors:       {tracker.error_count()}")
    print(f"    total cost:   ${tracker.total_cost_usd():.4f}")
    print(f"    trace spans:  {trace.span_count()}  (root={trace.root_id})")

    # 2. Metrics
    print("\n  Section 2: Metrics (counter, gauge, histogram)")
    print("  " + "-" * 66)
    for name, c in metrics.counters.items():
        print(f"    counter  {name:<14} = {c.value}")
    for name, g in metrics.gauges.items():
        print(f"    gauge    {name:<14} = {g.value}")
    lat = metrics.histograms["latency_ms"]
    print(f"    hist     latency_ms       n={lat.count} mean={lat.mean:.1f}  p50={lat.p50():.1f}  p95={lat.p95():.1f}  p99={lat.p99():.1f}")

    # 3. Cost breakdowns
    print("\n  Section 3: Cost breakdowns")
    print("  " + "-" * 66)
    print(f"    by model   (top 3): {[(k, round(v, 4)) for k, v in tracker.top_n('model', 3)]}")
    print(f"    by user    (top 3): {[(k, round(v, 4)) for k, v in tracker.top_n('user', 3)]}")
    print(f"    by feature (top 3): {[(k, round(v, 4)) for k, v in tracker.top_n('feature', 3)]}")

    # 4. Logs (sample)
    print("\n  Section 4: Structured logs (first 3)")
    print("  " + "-" * 66)
    for line in logger.lines()[:3]:
        print(f"    {line}")

    # 5. Traces
    print("\n  Section 5: Trace tree (root + 2 children shown)")
    print("  " + "-" * 66)
    if trace.root_id:
        root_span = trace.spans[trace.root_id]
        print(f"    ROOT  {root_span.name:<14}  dur={root_span.duration_ms:.1f}ms  children={len(root_span.children)}")
        for cid in root_span.children[:2]:
            cs = trace.spans[cid]
            print(f"      CHILD  {cs.name:<10}  dur={cs.duration_ms:.1f}ms  status={cs.status}")
    print(f"    total trace duration: {trace.total_duration_ms():.1f}ms")

    # 6. Alerts
    print("\n  Section 6: Alerts")
    print("  " + "-" * 66)
    alerter = evaluate_alerts(metrics, tracker)
    if alerter.fired:
        for a in alerter.fired:
            print(f"    {a}")
    else:
        print("    no alerts fired")
    print(f"    highest severity: {alerter.highest_severity()}")

    # 7. Dashboard
    print("\n  Section 7: Dashboard summary")
    print("  " + "-" * 66)
    dash = Dashboard(metrics=metrics, tracker=tracker, alerter=alerter)
    dash.print_summary()

    print("=" * 70)
    print("  See L11-observability-cost.ipynb for the runnable version.")
    print("=" * 70)


# =================================================================
# SECTION 10  --  Tests
# =================================================================

def test_counter_inc() -> None:
    c = Counter("x")
    c.inc()
    c.inc(5.0)
    assert c.value == 6.0


def test_counter_cannot_decrease() -> None:
    c = Counter("x")
    try:
        c.inc(-1.0)
        assert False, "should have raised"
    except ValueError:
        pass


def test_gauge_up_down() -> None:
    g = Gauge("q", 10.0)
    g.inc(5.0)
    g.dec(3.0)
    assert g.value == 12.0


def test_histogram_percentiles() -> None:
    h = Histogram("lat")
    for v in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
        h.observe(v)
    assert h.count == 10
    assert h.p50() == 55.0
    assert h.p95() == 95.5
    assert h.p99() == 99.1


def test_histogram_empty() -> None:
    h = Histogram("lat")
    assert h.count == 0
    assert h.p50() == 0.0
    assert h.p95() == 0.0
    assert h.p99() == 0.0


def test_metric_series_get_or_create() -> None:
    ms = MetricSeries()
    a = ms.counter("calls")
    b = ms.counter("calls")
    assert a is b
    assert a.value == 0


def test_trace_root_and_children() -> None:
    t = Trace("t1")
    root = t.start_span("root")
    child1 = t.start_span("c1", parent_id=root.span_id)
    child2 = t.start_span("c2", parent_id=root.span_id)
    child1.finish()
    child2.finish()
    root.finish()
    assert t.root_id == root.span_id
    assert t.span_count() == 3
    assert len(root.children) == 2


def test_span_duration() -> None:
    t = Trace("t2")
    s = t.start_span("work")
    s.finish()
    assert s.duration_ms >= 0.0
    assert s.status == "ok"


def test_compute_cost_usd_known() -> None:
    # 1000 in + 500 out at gpt-4o-mini: 0.00015 + 0.0003 = 0.00045
    c = compute_cost_usd("gpt-4o-mini", 1000, 500)
    assert abs(c - 0.00045) < 1e-9


def test_compute_cost_usd_unknown_model() -> None:
    c = compute_cost_usd("never-seen-model", 1000, 500)
    assert c == 0.0


def test_cost_tracker_aggregates() -> None:
    ct = CostTracker()
    ct.add(CostRecord("c1", 0, "gpt-4o", "rag", "u1", 1000, 500, 0.01, 200.0))
    ct.add(CostRecord("c2", 0, "gpt-4o", "chat", "u2", 2000, 1000, 0.02, 300.0))
    ct.add(CostRecord("c3", 0, "gpt-4o-mini", "rag", "u1", 500, 250, 0.0001, 100.0))
    assert abs(ct.total_cost_usd() - 0.0301) < 1e-9
    assert ct.total_input_tokens() == 3500
    assert ct.by_model()["gpt-4o"] == 0.03
    assert abs(ct.by_user()["u1"] - 0.0101) < 1e-9


def test_cost_tracker_top_n() -> None:
    ct = CostTracker()
    for i in range(5):
        ct.add(CostRecord(f"c{i}", 0, "gpt-4o", "rag", f"u{i % 2}", 1000, 500, 0.01 * (i + 1), 100.0))
    top = ct.top_n("user", 2)
    assert len(top) == 2
    # top user is the one that got the bigger costs; u0 gets indices 0,2,4 (0.01+0.03+0.05=0.09)
    assert top[0][0] == "u0"
    assert abs(top[0][1] - 0.09) < 1e-9


def test_logger_level_filtering() -> None:
    sink: list[dict[str, Any]] = []
    lg = Logger(level="warn", sink=sink)
    lg.info("ignored")
    lg.warn("kept")
    lg.error("kept too")
    assert len(sink) == 2
    assert all(r["level"] in ("warn", "error") for r in sink)


def test_logger_json_output() -> None:
    sink: list[dict[str, Any]] = []
    lg = Logger(level="debug", sink=sink)
    lg.info("event", call_id="c1", cost=0.001)
    line = lg.lines()[0]
    parsed = json.loads(line)
    assert parsed["message"] == "event"
    assert parsed["call_id"] == "c1"
    assert parsed["cost"] == 0.001


def test_alert_rule_fires_gt() -> None:
    r = AlertRule("r1", "latency", ">", 100.0, "warn")
    assert r.fires(150.0)
    assert not r.fires(50.0)
    assert not r.fires(100.0)  # strict


def test_alert_rule_fires_lt() -> None:
    r = AlertRule("r1", "queue", "<", 5.0, "info")
    assert r.fires(3.0)
    assert not r.fires(5.0)
    assert not r.fires(10.0)


def test_alerter_evaluate_fires_matching() -> None:
    al = Alerter(rules=[
        AlertRule("err", "error_rate", ">", 0.05, "error"),
        AlertRule("slow", "p95", ">", 1000.0, "warn"),
    ])
    fired = al.evaluate({"error_rate": 0.10, "p95": 500.0})
    assert len(fired) == 1
    assert fired[0].rule.name == "err"


def test_alerter_highest_severity() -> None:
    al = Alerter(rules=[
        AlertRule("a", "x", ">", 0.0, "info"),
        AlertRule("b", "y", ">", 0.0, "page"),
        AlertRule("c", "z", ">", 0.0, "warn"),
    ])
    al.evaluate({"x": 1.0, "y": 1.0, "z": 1.0})
    assert al.highest_severity() == "page"


def test_dashboard_summary_keys() -> None:
    ms = MetricSeries()
    hist = ms.histogram("latency_ms")
    for v in [100, 200, 300, 400, 500]:
        hist.observe(v)
    ct = CostTracker()
    ct.add(CostRecord("c1", 0, "gpt-4o-mini", "rag", "u1", 1000, 500, 0.001, 200.0))
    al = Alerter()
    dash = Dashboard(metrics=ms, tracker=ct, alerter=al)
    s = dash.summary()
    for k in ("total_calls", "error_count", "error_rate", "p50_ms", "p95_ms", "p99_ms",
              "total_cost_usd", "total_input_tokens", "total_output_tokens",
              "active_alerts", "highest_severity"):
        assert k in s
    assert s["total_calls"] == 1
    assert s["p50_ms"] == 300.0


def test_run_pipeline_smoke() -> None:
    metrics, tracker, logger, _, trace = run_pipeline(n_calls=20, seed=42)
    assert tracker.total_calls() == 20
    assert metrics.histograms["latency_ms"].count == 20
    assert trace.span_count() == 21   # 1 root + 20 children
    assert len(logger.sink) == 20


def test_simulate_call_realistic() -> None:
    rng = random.Random(0)
    rec = simulate_call("c0001", rng)
    assert rec.call_id == "c0001"
    assert rec.model in MODELS
    assert rec.user_id in USERS
    assert rec.feature in FEATURES
    assert 200 <= rec.input_tokens <= 4000
    assert 50 <= rec.output_tokens <= 1500
    assert rec.latency_ms > 0


# =================================================================
# ENTRY
# =================================================================

if __name__ == "__main__":
    demo()
