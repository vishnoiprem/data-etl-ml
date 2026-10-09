"""
service/telemetry.py — Metrics + structured logging for PacificFreight Phase 3.

What this file does
-------------------
Three small primitives, all stdlib (no `prometheus-client` required):

1. **MetricsRegistry** — counters, gauges, and histograms keyed by name+labels.
   Exposes `render_prometheus()` which produces the Prometheus text exposition
   format. A `prometheus_client` shim could be swapped in 1-line later (A7).

2. **JsonLogger** — emits one JSON object per line to `usage.jsonl` (or any
   other path). Each line has: ts, request_id, user_id, latency_ms, model,
   cost_usd, circuit_state, outcome. Same line format that Phase 2's
   `usage.jsonl` already used, plus the new Phase 3 fields.

3. **request_id_middleware** — FastAPI middleware that generates an 8-char
   `request_id` per request, stores it in `request.state.request_id`, and
   echoes it back in the `X-Request-Id` response header. Mirrors the pattern
   in `hardcode/level-3-streaming/01-realtime-chat-websocket.py::lifespan`.

How to run / import
-------------------
    from telemetry import REGISTRY, JsonLogger, request_id_middleware
    REGISTRY.counter("pf_drafts_total", labels={"outcome": "ok"}).inc()
    print(REGISTRY.render_prometheus())
    logger = JsonLogger("usage.jsonl")
    logger.log(request_id="abc12345", latency_ms=42, model="gpt-4o-mini",
               cost_usd=0.0003, circuit_state="closed", outcome="ok")
"""
from __future__ import annotations

import json
import math
import statistics
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

# ---------------------------------------------------------------------------
# Metrics primitives
# ---------------------------------------------------------------------------
@dataclass
class _Counter:
    name: str
    help: str
    labels: dict[str, str] = field(default_factory=dict)
    value: float = 0.0

    def inc(self, n: float = 1.0) -> None:
        self.value += n

    def render(self) -> str:
        labels_str = ",".join(f'{k}="{v}"' for k, v in sorted(self.labels.items()))
        if labels_str:
            return f'{self.name}{{{labels_str}}} {self.value}'
        return f"{self.name} {self.value}"


@dataclass
class _Gauge:
    name: str
    help: str
    labels: dict[str, str] = field(default_factory=dict)
    value: float = 0.0

    def set(self, v: float) -> None:
        self.value = v

    def inc(self, n: float = 1.0) -> None:
        self.value += n

    def dec(self, n: float = 1.0) -> None:
        self.value -= n

    def render(self) -> str:
        labels_str = ",".join(f'{k}="{v}"' for k, v in sorted(self.labels.items()))
        if labels_str:
            return f'{self.name}{{{labels_str}}} {self.value}'
        return f"{self.name} {self.value}"


@dataclass
class _Histogram:
    """A simple Histogram with fixed buckets. No fancy reservoir sampling.

    Buckets are cumulative (Prometheus convention): a bucket `le=0.5` counts
    all observations <= 0.5. We also emit `_count` and `_sum`.
    """
    name: str
    help: str
    labels: dict[str, str] = field(default_factory=dict)
    buckets: tuple[float, ...] = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
    counts: list[int] = field(default_factory=list)  # len == len(buckets) + 1 (the +Inf bucket)
    sum_obs: float = 0.0
    n_obs: int = 0

    def __post_init__(self) -> None:
        if not self.counts:
            self.counts = [0] * (len(self.buckets) + 1)

    def observe(self, v: float) -> None:
        self.sum_obs += v
        self.n_obs += 1
        # Place v in the first bucket where v <= bucket, or in the +Inf bucket.
        for i, b in enumerate(self.buckets):
            if v <= b:
                self.counts[i] += 1
                # Also increment all later buckets (Prometheus cumulative convention).
                for j in range(i + 1, len(self.counts)):
                    self.counts[j] += 1
                return
        # Larger than every finite bucket — just bump +Inf.
        self.counts[-1] += 1

    def render(self) -> list[str]:
        labels_str = ",".join(f'{k}="{v}"' for k, v in sorted(self.labels.items()))
        base = f"{self.name}"
        if labels_str:
            base = f"{self.name}{{{labels_str}}}"
        out: list[str] = []
        for b, c in zip(self.buckets, self.counts[:-1]):
            le = f",le=\"{b}\""
            if labels_str:
                out.append(f'{self.name}{{{labels_str}{le}}} {c}')
            else:
                out.append(f'{self.name}{{{le[1:]}}} {c}')
        # +Inf bucket — same as total count
        if labels_str:
            out.append(f'{self.name}{{{labels_str},le="+Inf"}} {self.counts[-1]}')
        else:
            out.append(f'{self.name}{{le="+Inf"}} {self.counts[-1]}')
        out.append(f"{self.name}_count{('{' + labels_str + '}') if labels_str else ''} {self.n_obs}")
        out.append(f"{self.name}_sum{('{' + labels_str + '}') if labels_str else ''} {self.sum_obs:.6f}")
        return out


class MetricsRegistry:
    """A tiny Prometheus-compatible registry.

    Counters, gauges, and histograms are auto-created on first access.
    Series are keyed by (name, frozenset(labels.items())) so the same
    (name, labels) tuple always returns the same series object.
    """
    def __init__(self) -> None:
        self._counters: dict[tuple[str, frozenset], _Counter] = {}
        self._gauges: dict[tuple[str, frozenset], _Gauge] = {}
        self._histograms: dict[tuple[str, frozenset], _Histogram] = {}
        self._meta: dict[str, str] = {}  # name -> help text

    def _key(self, name: str, labels: dict[str, str] | None) -> tuple[str, frozenset]:
        return (name, frozenset((labels or {}).items()))

    def counter(self, name: str, *, help: str = "", labels: dict[str, str] | None = None) -> _Counter:
        k = self._key(name, labels)
        if k not in self._counters:
            self._counters[k] = _Counter(name=name, help=help, labels=dict(labels or {}))
            if help:
                self._meta[name] = help
        return self._counters[k]

    def gauge(self, name: str, *, help: str = "", labels: dict[str, str] | None = None) -> _Gauge:
        k = self._key(name, labels)
        if k not in self._gauges:
            self._gauges[k] = _Gauge(name=name, help=help, labels=dict(labels or {}))
            if help:
                self._meta[name] = help
        return self._gauges[k]

    def histogram(
        self,
        name: str,
        *,
        help: str = "",
        labels: dict[str, str] | None = None,
        buckets: Iterable[float] | None = None,
    ) -> _Histogram:
        k = self._key(name, labels)
        if k not in self._histograms:
            kwargs: dict[str, Any] = dict(name=name, help=help, labels=dict(labels or {}))
            if buckets is not None:
                kwargs["buckets"] = tuple(buckets)
            self._histograms[k] = _Histogram(**kwargs)
            if help:
                self._meta[name] = help
        return self._histograms[k]

    def render_prometheus(self) -> str:
        """Render all series in Prometheus text exposition format."""
        lines: list[str] = []
        # Help lines (one per unique metric name)
        seen_help: set[str] = set()
        for c in self._counters.values():
            if c.name in seen_help:
                continue
            seen_help.add(c.name)
            lines.append(f"# HELP {c.name} {c.help}")
            lines.append(f"# TYPE {c.name} counter")
        for g in self._gauges.values():
            if g.name in seen_help:
                continue
            seen_help.add(g.name)
            lines.append(f"# HELP {g.name} {g.help}")
            lines.append(f"# TYPE {g.name} gauge")
        for h in self._histograms.values():
            if h.name in seen_help:
                continue
            seen_help.add(h.name)
            lines.append(f"# HELP {h.name} {h.help}")
            lines.append(f"# TYPE {h.name} histogram")
        # Sample lines
        for c in self._counters.values():
            lines.append(c.render())
        for g in self._gauges.values():
            lines.append(g.render())
        for h in self._histograms.values():
            lines.extend(h.render())
        return "\n".join(lines) + "\n"

    def snapshot(self) -> dict[str, Any]:
        """A pure-Python dict snapshot, useful for tests and the iteration report."""
        return {
            "counters": [
                {"name": c.name, "labels": c.labels, "value": c.value}
                for c in self._counters.values()
            ],
            "gauges": [
                {"name": g.name, "labels": g.labels, "value": g.value}
                for g in self._gauges.values()
            ],
            "histograms": [
                {
                    "name": h.name,
                    "labels": h.labels,
                    "n": h.n_obs,
                    "sum": h.sum_obs,
                    "mean": (h.sum_obs / h.n_obs) if h.n_obs else 0.0,
                    "p50": _percentile_from_counts(h.buckets, h.counts, 0.50),
                    "p95": _percentile_from_counts(h.buckets, h.counts, 0.95),
                    "p99": _percentile_from_counts(h.buckets, h.counts, 0.99),
                }
                for h in self._histograms.values()
            ],
        }


def _percentile_from_counts(
    buckets: tuple[float, ...], counts: list[int], pct: float
) -> float:
    """Estimate a percentile from a cumulative-count histogram (Prom-style)."""
    n = counts[-1]  # +Inf bucket = total count
    if n == 0:
        return 0.0
    target = pct * n
    for b, c in zip(buckets, counts[:-1]):
        if c >= target:
            return float(b)
    return float(buckets[-1])


# Module-level singleton (FastAPI app shares this).
REGISTRY = MetricsRegistry()


# ---------------------------------------------------------------------------
# JSON logger
# ---------------------------------------------------------------------------
class JsonLogger:
    """Append-only NDJSON logger for usage events.

    Each call to `log(...)` produces one JSON object on one line. The set of
    fields is fixed by the schema below — adding a field is a one-line change
    here and a one-line change in the consumer (e.g., the iteration report).
    """
    REQUIRED_FIELDS = (
        "ts", "request_id", "outcome", "latency_ms", "model",
        "cost_usd", "circuit_state",
    )
    OPTIONAL_FIELDS = (
        "user_id", "shipment_id", "input_tokens", "output_tokens",
        "n_contexts", "feedback_rating", "note",
    )

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, **fields: Any) -> None:
        """Write one event. Missing required fields raise."""
        # `ts` is auto-injected; check the rest of the required fields explicitly.
        missing = [f for f in self.REQUIRED_FIELDS if f != "ts" and f not in fields]
        if missing:
            raise ValueError(f"JsonLogger: missing required fields {missing}")
        unknown = set(fields) - set(self.REQUIRED_FIELDS) - set(self.OPTIONAL_FIELDS)
        if unknown:
            raise ValueError(f"JsonLogger: unknown fields {sorted(unknown)}")
        row = {"ts": time.time(), **fields}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def tail(self, n: int = 100) -> list[dict[str, Any]]:
        """Read the last `n` events. Useful for the iteration report."""
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as f:
            lines = f.readlines()
        out: list[dict[str, Any]] = []
        for line in lines[-n:]:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return out


# ---------------------------------------------------------------------------
# FastAPI middleware
# ---------------------------------------------------------------------------
def new_request_id() -> str:
    return uuid.uuid4().hex[:8]


def request_id_middleware(app: Any) -> Any:
    """Decorator-style FastAPI middleware. Pass it to `app.middleware("http")`.

    Generates a request_id, stashes it in `request.state.request_id`, and
    echoes it back as the `X-Request-Id` response header. Also records the
    request duration in the `pf_request_duration_seconds` histogram.
    """
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request

    class _Middleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next: Any) -> Any:
            rid = request.headers.get("x-request-id") or new_request_id()
            request.state.request_id = rid
            started = time.monotonic()
            try:
                response = await call_next(request)
            except Exception:
                elapsed = time.monotonic() - started
                REGISTRY.histogram(
                    "pf_request_duration_seconds",
                    help="HTTP request duration in seconds",
                    labels={"path": request.url.path, "outcome": "error"},
                ).observe(elapsed)
                raise
            elapsed = time.monotonic() - started
            REGISTRY.histogram(
                "pf_request_duration_seconds",
                help="HTTP request duration in seconds",
                labels={"path": request.url.path, "outcome": str(response.status_code)},
            ).observe(elapsed)
            response.headers["X-Request-Id"] = rid
            return response

    app.middleware("http")(_Middleware)
    return app


# ---------------------------------------------------------------------------
# CLI demo
# ---------------------------------------------------------------------------
def main() -> int:
    print("=" * 70)
    print("service/telemetry.py — demo")
    print("=" * 70)

    # Pre-seed some metrics.
    REGISTRY.counter("pf_drafts_total", help="Total /draft calls",
                     labels={"outcome": "ok"}).inc(17)
    REGISTRY.counter("pf_drafts_total", help="Total /draft calls",
                     labels={"outcome": "rate_limited"}).inc(2)
    REGISTRY.gauge("pf_circuit_state", help="0=closed 1=half_open 2=open",
                   labels={"downstream": "openai"}).set(0)
    REGISTRY.gauge("pf_active_workers", help="LLM worker pool size").set(2)
    h = REGISTRY.histogram("pf_draft_latency_seconds",
                           help="/draft latency seconds",
                           labels={"outcome": "ok"})
    for v in (0.12, 0.34, 0.55, 0.81, 1.20, 1.45, 2.10, 2.85, 3.20, 4.50):
        h.observe(v)

    print("\n--- Prometheus text format (first 1500 chars) ---")
    print(REGISTRY.render_prometheus()[:1500])

    print("\n--- Snapshot ---")
    snap = REGISTRY.snapshot()
    print(f"counters : {len(snap['counters'])}")
    print(f"gauges   : {len(snap['gauges'])}")
    print(f"histograms: {len(snap['histograms'])}")
    for hh in snap["histograms"]:
        print(f"  {hh['name']:35s}  n={hh['n']:2d}  p50={hh['p50']:.2f}s  "
              f"p95={hh['p95']:.2f}s  p99={hh['p99']:.2f}s")

    # JSON logger
    import tempfile, os
    with tempfile.TemporaryDirectory() as d:
        log_path = os.path.join(d, "usage.jsonl")
        jl = JsonLogger(log_path)
        jl.log(request_id="abc12345", outcome="ok", latency_ms=120, model="gpt-4o-mini",
               cost_usd=0.0003, circuit_state="closed", user_id="mei@pf.com",
               shipment_id="PF-1003", n_contexts=3)
        jl.log(request_id="def67890", outcome="rate_limited", latency_ms=2, model="gpt-4o-mini",
               cost_usd=0.0, circuit_state="closed", user_id="carmen@pf.com",
               note="rate_limiter_rejected")
        print(f"\n--- JsonLogger: 2 events written to {log_path} ---")
        for ev in jl.tail(n=10):
            print("  " + json.dumps(ev))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
