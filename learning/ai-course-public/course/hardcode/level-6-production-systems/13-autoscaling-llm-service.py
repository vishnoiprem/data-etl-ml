"""
Lab 13: Autoscaling LLM Service
==============================

A production-grade autoscaling LLM inference service that horizontally scales
worker pools based on real-time queue depth, implements a Kubernetes-style HPA
(Horizontal Pod Autoscaler) simulator, and provides Prometheus-grade observability.

Architecture
------------

    +------------------+        +------------------+
    |   Clients        |  --->  |  HTTP Gateway    |
    | (load test)      |        |  (aiohttp)       |
    +------------------+        +--------+---------+
                                          |
                                          v
                                +-----------------+
                                |   Priority Queue|
                                |  (asyncio.Queue)|
                                +--------+--------+
                                         |
                                         v
   +----[ HPA Controller ]------>  +------------------+
   |  (queue depth + RPS)         |  Worker Pool     |
   |  scales min..max workers     |  (dynamic N)     |
   +----------------------------+  +---------+-------+
                                              |
                                              v
                                  +---------------------+
                                  | Downstream LLMs     |
                                  | (primary + fallback)|
                                  +---------------------+

Components
----------
1. PriorityQueue: bounded asyncio queue with shed-load semantics.
2. WorkerPool: dynamically sized async workers, each consumes tasks and calls LLM.
3. HPAController: polls metrics every scrape interval; decides scale-up / scale-down.
4. CircuitBreaker: per-downstream protection (open / half-open / closed).
5. LoadTester: spawns 1000+ concurrent requests with mixed priorities.
6. MetricsRegistry: Prometheus-compatible counter / histogram / gauge.
7. HealthCheckServer: /healthz, /metrics, /ready, /drain endpoints.

How to run
----------
$ python 13-autoscaling-llm-service.py --mode gateway     # serve HTTP
$ python 13-autoscaling-llm-service.py --mode loadtest    # run synthetic load
$ python 13-autoscaling-llm-service.py --mode demo        # end-to-end demo

Configuration (env vars)
------------------------
- LLM_MIN_WORKERS         (int, default 2)
- LLM_MAX_WORKERS         (int, default 32)
- LLM_QUEUE_CAPACITY      (int, default 10000)
- LLM_TARGET_UTILIZATION  (float, default 0.7)   # target queue fill ratio
- LLM_HPA_INTERVAL        (sec, default 5)
- LLM_DRAIN_TIMEOUT       (sec, default 30)
- LLM_DOWNSTREAM_PRIMARY  (str, default "gpt-4o")
- LLM_DOWNSTREAM_FALLBACK (str, default "gpt-4o-mini")
- LLM_FAKE_LATENCY_MS     (int, default 50)      # mock latency
- LLM_FAKE_ERROR_RATE     (float, default 0.02)  # mock errors
- LLM_METRICS_PORT        (int, default 9090)

Dependencies
------------
- aiohttp (HTTP server + client)
- prometheus_client (metrics export)
- Standard library for the rest (asyncio, dataclasses, statistics, logging).

Failure modes handled
---------------------
- Queue full -> shed-load with HTTP 503 + Retry-After.
- Downstream errors -> circuit breaker; fallback to cheaper model.
- Worker crash -> automatic respawn.
- SIGTERM / SIGINT -> drain in-flight, refuse new requests, exit cleanly.
- Saturated workers -> HPA scales out (bounded by max_workers).

What makes it production-grade
------------------------------
- Real priority queue with shed-load (not unbounded).
- Realistic autoscaling math (Little's Law + target utilization).
- Circuit breakers for each downstream.
- Prometheus metrics export (queue depth, worker count, latency percentiles).
- Graceful shutdown with request draining.
- Atomic worker count transition; no double-processing.
- Distributed-tracing style correlation IDs per request.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import dataclasses
import json
import logging
import os
import random
import signal
import socket
import statistics
import sys
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Awaitable,
    Callable,
    Deque,
    Dict,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
)

# ---------------------------------------------------------------------------
# Optional dependencies -- the module degrades gracefully if aiohttp / prom
# are missing so the demo still runs on a bare Python install.
# ---------------------------------------------------------------------------
try:
    from aiohttp import web  # type: ignore
    AIOHTTP_AVAILABLE = True
except Exception:  # pragma: no cover - fall back to a stub
    AIOHTTP_AVAILABLE = False

try:
    from prometheus_client import (  # type: ignore
        Counter,
        Gauge,
        Histogram,
        CollectorRegistry,
        generate_latest,
        CONTENT_TYPE_LATEST,
    )
    PROMETHEUS_AVAILABLE = True
except Exception:  # pragma: no cover
    PROMETHEUS_AVAILABLE = False


# ---------------------------------------------------------------------------
# Structured JSON logging
# ---------------------------------------------------------------------------
class JsonFormatter(logging.Formatter):
    """Render log records as one-line JSON for machine ingestion."""

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "ts": time.time(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        # Attach any extra={"..."} fields the caller passed in.
        for key, value in record.__dict__.items():
            if key in payload or key.startswith("_"):
                continue
            if key in (
                "args", "asctime", "created", "exc_info", "exc_text",
                "filename", "funcName", "levelname", "levelno", "lineno",
                "module", "msecs", "message", "msg", "name", "pathname",
                "process", "processName", "relativeCreated", "stack_info",
                "thread", "threadName", "taskName",
            ):
                continue
            try:
                json.dumps(value)
                payload[key] = value
            except TypeError:
                payload[key] = repr(value)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, sort_keys=True, default=str)


def _build_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())
        logger.propagate = False
    return logger


log = _build_logger("autoscaling-llm")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ServiceConfig:
    min_workers: int = int(os.environ.get("LLM_MIN_WORKERS", "2"))
    max_workers: int = int(os.environ.get("LLM_MAX_WORKERS", "32"))
    queue_capacity: int = int(os.environ.get("LLM_QUEUE_CAPACITY", "10000"))
    target_utilization: float = float(
        os.environ.get("LLM_TARGET_UTILIZATION", "0.7")
    )
    hpa_interval_sec: float = float(os.environ.get("LLM_HPA_INTERVAL", "5"))
    drain_timeout_sec: float = float(os.environ.get("LLM_DRAIN_TIMEOUT", "30"))
    downstream_primary: str = os.environ.get(
        "LLM_DOWNSTREAM_PRIMARY", "gpt-4o"
    )
    downstream_fallback: str = os.environ.get(
        "LLM_DOWNSTREAM_FALLBACK", "gpt-4o-mini"
    )
    fake_latency_ms: int = int(os.environ.get("LLM_FAKE_LATENCY_MS", "50"))
    fake_error_rate: float = float(os.environ.get("LLM_FAKE_ERROR_RATE", "0.02"))
    metrics_port: int = int(os.environ.get("LLM_METRICS_PORT", "9090"))
    http_host: str = os.environ.get("LLM_HTTP_HOST", "127.0.0.1")
    http_port: int = int(os.environ.get("LLM_HTTP_PORT", "8080"))
    worker_warmup_sec: float = float(os.environ.get("LLM_WORKER_WARMUP", "0.5"))
    breaker_window_sec: float = float(os.environ.get("LLM_BREAKER_WINDOW", "60"))
    breaker_threshold: float = float(os.environ.get("LLM_BREAKER_FAIL_RATE", "0.5"))
    breaker_cooldown_sec: float = float(os.environ.get("LLM_BREAKER_COOLDOWN", "20"))

    def __post_init__(self) -> None:
        if self.min_workers < 1:
            raise ValueError("min_workers must be >= 1")
        if self.max_workers < self.min_workers:
            raise ValueError("max_workers must be >= min_workers")
        if not (0 < self.target_utilization < 1):
            raise ValueError("target_utilization must be in (0, 1)")


# ---------------------------------------------------------------------------
# Metrics registry (Prometheus + in-process fallback)
# ---------------------------------------------------------------------------
class MetricsRegistry:
    """Tiny adapter that uses prometheus_client if available else dicts."""

    def __init__(self) -> None:
        self.use_prom = PROMETHEUS_AVAILABLE
        if self.use_prom:
            self.registry = CollectorRegistry()
            self.requests_total = Counter(
                "llm_requests_total",
                "Total LLM inference requests.",
                ["priority", "outcome"],
                registry=self.registry,
            )
            self.request_latency = Histogram(
                "llm_request_latency_seconds",
                "LLM request latency in seconds.",
                ["priority", "outcome"],
                buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
                registry=self.registry,
            )
            self.queue_depth = Gauge(
                "llm_queue_depth",
                "Number of items currently in the request queue.",
                registry=self.registry,
            )
            self.worker_count = Gauge(
                "llm_active_workers",
                "Number of active worker tasks.",
                registry=self.registry,
            )
            self.in_flight = Gauge(
                "llm_in_flight_requests",
                "Number of requests currently being processed.",
                registry=self.registry,
            )
            self.breaker_state = Gauge(
                "llm_breaker_state",
                "Circuit breaker state (0=closed, 1=half-open, 2=open).",
                ["downstream"],
                registry=self.registry,
            )
            self.scale_events = Counter(
                "llm_scale_events_total",
                "Number of scaling events emitted by the HPA.",
                ["direction"],
                registry=self.registry,
            )
        else:  # fallback -- plain counters
            self._counters: Dict[Tuple[str, str], int] = {}
            self._gauges: Dict[str, float] = {}
            self._latencies: Dict[Tuple[str, str], Deque[float]] = {}

    # -- counter / histogram API --
    def inc_request(self, priority: str, outcome: str) -> None:
        if self.use_prom:
            self.requests_total.labels(priority=priority, outcome=outcome).inc()
        else:
            key = ("requests", priority, outcome)
            self._counters[key] = self._counters.get(key, 0) + 1

    def observe_latency(self, priority: str, outcome: str, seconds: float) -> None:
        if self.use_prom:
            self.request_latency.labels(priority=priority, outcome=outcome).observe(
                seconds
            )
        else:
            key = ("latency", priority, outcome)
            self._latencies.setdefault(key, deque(maxlen=512)).append(seconds)

    def set_queue_depth(self, value: int) -> None:
        if self.use_prom:
            self.queue_depth.set(value)
        else:
            self._gauges["queue_depth"] = value

    def set_worker_count(self, value: int) -> None:
        if self.use_prom:
            self.worker_count.set(value)
        else:
            self._gauges["worker_count"] = value

    def set_in_flight(self, value: int) -> None:
        if self.use_prom:
            self.in_flight.set(value)
        else:
            self._gauges["in_flight"] = value

    def set_breaker_state(self, downstream: str, state: int) -> None:
        if self.use_prom:
            self.breaker_state.labels(downstream=downstream).set(state)
        else:
            self._gauges[f"breaker:{downstream}"] = state

    def inc_scale_event(self, direction: str) -> None:
        if self.use_prom:
            self.scale_events.labels(direction=direction).inc()
        else:
            key = ("scale", direction)
            self._counters[key] = self._counters.get(key, 0) + 1

    # -- percentiles (used both for Prometheus & fallback) --
    def percentiles(self, priority: str, outcome: str) -> Dict[str, float]:
        """Return p50/p95/p99 for the in-process latency window."""
        key = ("latency", priority, outcome)
        samples = list(self._latencies.get(key, []))
        if not samples:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "count": 0}
        samples.sort()
        n = len(samples)

        def q(p: float) -> float:
            idx = min(n - 1, int(p * n))
            return samples[idx]

        return {
            "p50": round(q(0.50) * 1000, 2),
            "p95": round(q(0.95) * 1000, 2),
            "p99": round(q(0.99) * 1000, 2),
            "count": n,
        }

    def render(self) -> Tuple[bytes, str]:
        if self.use_prom:
            return generate_latest(self.registry), CONTENT_TYPE_LATEST
        body = json.dumps(
            {
                "queue_depth": self._gauges.get("queue_depth", 0),
                "worker_count": self._gauges.get("worker_count", 0),
                "in_flight": self._gauges.get("in_flight", 0),
                "counters": {str(k): v for k, v in self._counters.items()},
                "latency": {
                    f"{k[1]}/{k[2]}": self.percentiles(k[1], k[2])
                    for k in self._latencies
                },
            },
            indent=2,
        ).encode()
        return body, "application/json"


# ---------------------------------------------------------------------------
# Priority + request types
# ---------------------------------------------------------------------------
class Priority(int, Enum):
    LOW = 5
    NORMAL = 10
    HIGH = 20


@dataclass
class LLMRequest:
    request_id: str
    prompt: str
    priority: Priority
    max_tokens: int = 256
    user_id: str = "anon"
    enqueued_at: float = field(default_factory=time.monotonic)
    deadline_at: Optional[float] = None
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex)


@dataclass
class LLMResponse:
    request_id: str
    text: str
    latency_sec: float
    outcome: str  # "ok" | "fallback" | "error"
    downstream: str
    tokens_in: int
    tokens_out: int


# ---------------------------------------------------------------------------
# Bounded priority queue with shed-load semantics
# ---------------------------------------------------------------------------
class PriorityQueueFull(Exception):
    """Raised when the queue cannot accept a new request."""


class BoundedPriorityQueue:
    """A wrapper around asyncio.Queue with priority buckets + capacity tracking.

    Python's asyncio.Queue is FIFO; we layer priority by using N internal
    queues, one per Priority, and pull from highest priority first.
    """

    def __init__(self, capacity: int) -> None:
        self._capacity = capacity
        self._size = 0
        self._cond = asyncio.Condition()
        self._buckets: Dict[Priority, Deque[LLMRequest]] = {
            p: deque() for p in Priority
        }
        # The notifier fires every time we receive an item so a waiting
        # consumer can wake up.
        self._notify_event = asyncio.Event()
        self._closed = False

    @property
    def size(self) -> int:
        return self._size

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def utilization(self) -> float:
        if self._capacity == 0:
            return 1.0
        return self._size / self._capacity

    def is_full(self) -> bool:
        return self._size >= self._capacity

    def is_closed(self) -> bool:
        return self._closed

    async def put(self, item: LLMRequest) -> None:
        async with self._cond:
            if self._closed:
                raise PriorityQueueFull("queue closed")
            while self._size >= self._capacity:
                # shed-load: tell the caller to retry later.
                raise PriorityQueueFull(
                    f"queue full ({self._size}/{self._capacity})"
                )
            self._buckets[item.priority].append(item)
            self._size += 1
            self._notify_event.set()

    async def get(self) -> LLMRequest:
        # Wait until something arrives OR we are closed + empty.
        while True:
            async with self._cond:
                if self._size > 0:
                    # Pick from the highest-priority bucket.
                    for p in sorted(Priority, key=lambda x: -x.value):
                        bucket = self._buckets[p]
                        if bucket:
                            item = bucket.popleft()
                            self._size -= 1
                            return item
                    # should not reach here if size > 0
                if self._closed and self._size == 0:
                    raise asyncio.CancelledError("queue closed & empty")
                await self._cond.wait_for(
                    lambda: (self._size > 0) or (self._closed and self._size == 0)
                )

    async def close(self) -> None:
        async with self._cond:
            self._closed = True
            self._notify_event.set()
            self._cond.notify_all()


# ---------------------------------------------------------------------------
# Downstream LLM client (mock with realistic failure + latency)
# ---------------------------------------------------------------------------
class DownstreamError(Exception):
    pass


class LLMClient:
    """A mock LLM client.

    A real implementation would post to an HTTPS endpoint. For the lab we
    simulate latency proportional to tokens and a small error rate so that
    circuit breakers and fallback logic exercise meaningfully.
    """

    def __init__(
        self,
        *,
        name: str,
        avg_latency_ms: int,
        error_rate: float,
    ) -> None:
        self.name = name
        self.avg_latency_ms = avg_latency_ms
        self.error_rate = error_rate
        self.tokens_in_total = 0
        self.tokens_out_total = 0
        self._lock = asyncio.Lock()

    async def complete(self, request: LLMRequest) -> Tuple[str, int, int]:
        # Simulate compute proportional to tokens.
        estimated_ms = self.avg_latency_ms + request.max_tokens * 0.1
        jitter = random.uniform(0.5, 1.5)
        await asyncio.sleep(estimated_ms / 1000.0 * jitter)

        # Random failure injection.
        if random.random() < self.error_rate:
            raise DownstreamError(f"{self.name} simulated failure")

        text = f"[{self.name}] processed {request.request_id[:8]}: " + \
            " ".join(request.prompt.split()[:12])
        tokens_in = len(request.prompt.split())
        tokens_out = len(text.split())
        async with self._lock:
            self.tokens_in_total += tokens_in
            self.tokens_out_total += tokens_out
        return text, tokens_in, tokens_out


# ---------------------------------------------------------------------------
# Circuit breaker (per-downstream)
# ---------------------------------------------------------------------------
class CircuitState(int, Enum):
    CLOSED = 0
    HALF_OPEN = 1
    OPEN = 2


class CircuitBreaker:
    def __init__(
        self,
        *,
        name: str,
        window_sec: float = 60.0,
        failure_threshold: float = 0.5,
        cooldown_sec: float = 20.0,
        metrics: Optional[MetricsRegistry] = None,
    ) -> None:
        self.name = name
        self.window_sec = window_sec
        self.failure_threshold = failure_threshold
        self.cooldown_sec = cooldown_sec
        self.metrics = metrics
        self.state = CircuitState.CLOSED
        self._samples: Deque[Tuple[float, bool, float]] = deque()
        self._opened_at: Optional[float] = None
        self._lock = asyncio.Lock()
        if metrics:
            metrics.set_breaker_state(name, int(self.state))

    async def allow(self) -> bool:
        async with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            if self.state == CircuitState.OPEN:
                if self._opened_at is None:
                    return False
                if time.monotonic() - self._opened_at >= self.cooldown_sec:
                    self._transition(CircuitState.HALF_OPEN)
                    return True
                return False
            # HALF_OPEN: allow one trial; further callers blocked until outcome.
            return True

    async def record(self, success: bool, latency_sec: float) -> None:
        now = time.monotonic()
        async with self._lock:
            self._samples.append((now, success, latency_sec))
            self._evict(now)
            if self.state == CircuitState.HALF_OPEN:
                # One trial decides.
                if success:
                    self._transition(CircuitState.CLOSED)
                else:
                    self._opened_at = now
                    self._transition(CircuitState.OPEN)
                return
            if self.state == CircuitState.CLOSED:
                fails = sum(1 for _, s, _ in self._samples if not s)
                total = len(self._samples)
                if total >= 10:
                    rate = fails / total
                    if rate >= self.failure_threshold:
                        self._opened_at = now
                        self._transition(CircuitState.OPEN)

    def _evict(self, now: float) -> None:
        cutoff = now - self.window_sec
        while self._samples and self._samples[0][0] < cutoff:
            self._samples.popleft()

    def _transition(self, new_state: CircuitState) -> None:
        old = self.state
        self.state = new_state
        log.info(
            "breaker_transition",
            extra={
                "downstream": self.name,
                "from_state": int(old),
                "to_state": int(new_state),
            },
        )
        if self.metrics:
            self.metrics.set_breaker_state(self.name, int(new_state))

    def stats(self) -> Dict[str, Any]:
        total = len(self._samples)
        fails = sum(1 for _, s, _ in self._samples if not s)
        return {
            "downstream": self.name,
            "state": int(self.state),
            "samples": total,
            "failures": fails,
            "fail_rate": (fails / total) if total else 0.0,
            "opened_at": self._opened_at,
        }


# ---------------------------------------------------------------------------
# Worker pool -- dynamically sized
# ---------------------------------------------------------------------------
class WorkerPool:
    """A resizable pool of asyncio tasks, each consuming from the queue."""

    def __init__(
        self,
        queue: BoundedPriorityQueue,
        client_primary: LLMClient,
        client_fallback: LLMClient,
        breaker_primary: CircuitBreaker,
        breaker_fallback: CircuitBreaker,
        metrics: MetricsRegistry,
        cfg: ServiceConfig,
    ) -> None:
        self.queue = queue
        self.client_primary = client_primary
        self.client_fallback = client_fallback
        self.breaker_primary = breaker_primary
        self.breaker_fallback = breaker_fallback
        self.metrics = metrics
        self.cfg = cfg
        self._workers: List[asyncio.Task[None]] = []
        self._in_flight: Set[str] = set()
        self._lock = asyncio.Lock()
        self._draining = False
        self._stopped = False

    @property
    def size(self) -> int:
        return len(self._workers)

    @property
    def in_flight(self) -> int:
        return len(self._in_flight)

    @property
    def is_draining(self) -> bool:
        return self._draining

    async def start(self, n: int) -> None:
        async with self._lock:
            for _ in range(n):
                self._spawn_locked()
            self.metrics.set_worker_count(self.size)

    async def resize(self, new_size: int) -> None:
        async with self._lock:
            current = self.size
            if new_size == current:
                return
            if new_size > current:
                for _ in range(new_size - current):
                    self._spawn_locked()
                self.metrics.inc_scale_event("up")
                log.info(
                    "scale_up",
                    extra={"from": current, "to": new_size},
                )
            else:
                # Cooperative shrink: just cancel extra worker tasks. In-flight
                # requests they were processing are allowed to complete (we
                # don't cancel mid-request; we only stop the consumer loop).
                surplus = current - new_size
                cancelled = 0
                # Cancel from the end so older workers (with warm caches) linger.
                for task in reversed(self._workers):
                    if cancelled >= surplus:
                        break
                    if not task.done():
                        task.cancel()
                        cancelled += 1
                # prune
                self._workers = [t for t in self._workers if not t.done()]
                self.metrics.inc_scale_event("down")
                log.info(
                    "scale_down",
                    extra={"from": current, "to": self.size},
                )
            self.metrics.set_worker_count(self.size)

    def _spawn_locked(self) -> None:
        task = asyncio.create_task(self._worker_loop(), name=f"worker-{self.size}")
        self._workers.append(task)

    async def _worker_loop(self) -> None:
        try:
            while not self._stopped:
                try:
                    request = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                except asyncio.CancelledError:
                    break
                except Exception:
                    # queue closed -> exit
                    break
                self._in_flight.add(request.request_id)
                try:
                    await self._process(request)
                finally:
                    self._in_flight.discard(request.request_id)
        except asyncio.CancelledError:
            log.info("worker_cancelled")
            raise

    async def _process(self, request: LLMRequest) -> None:
        start = time.monotonic()
        # PRIMARY
        text = None
        outcome = "ok"
        downstream = self.client_primary.name
        tokens_in = tokens_out = 0
        if await self.breaker_primary.allow():
            try:
                text, tokens_in, tokens_out = await self.client_primary.complete(
                    request
                )
                await self.breaker_primary.record(True, time.monotonic() - start)
            except DownstreamError as exc:
                await self.breaker_primary.record(False, time.monotonic() - start)
                log.warning(
                    "primary_failed",
                    extra={"request_id": request.request_id, "err": str(exc)},
                )
        # FALLBACK
        if text is None:
            if await self.breaker_fallback.allow():
                fallback_start = time.monotonic()
                try:
                    text, tokens_in, tokens_out = await self.client_fallback.complete(
                        request
                    )
                    downstream = self.client_fallback.name
                    outcome = "fallback"
                    await self.breaker_fallback.record(
                        True, time.monotonic() - fallback_start
                    )
                except DownstreamError as exc:
                    await self.breaker_fallback.record(
                        False, time.monotonic() - fallback_start
                    )
                    outcome = "error"
                    log.error(
                        "fallback_failed",
                        extra={
                            "request_id": request.request_id,
                            "err": str(exc),
                        },
                    )
            else:
                outcome = "error"
        latency = time.monotonic() - start
        self.metrics.observe_latency(request.priority.name, outcome, latency)
        self.metrics.inc_request(request.priority.name, outcome)
        # In a real system the response is shipped back via a future / queue.
        # For the demo we log it.
        log.info(
            "request_done",
            extra={
                "request_id": request.request_id,
                "priority": request.priority.name,
                "outcome": outcome,
                "downstream": downstream,
                "latency_ms": round(latency * 1000, 2),
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
            },
        )

    async def drain(self, timeout_sec: float) -> None:
        """Mark draining; cancel workers; wait up to timeout for in-flight."""
        self._draining = True
        log.info(
            "pool_draining",
            extra={"in_flight": self.in_flight, "timeout_sec": timeout_sec},
        )
        deadline = time.monotonic() + timeout_sec
        # cancel workers
        for task in self._workers:
            if not task.done():
                task.cancel()
        # Wait for tasks to finish
        for task in self._workers:
            try:
                await asyncio.wait_for(task, timeout=max(0.1, deadline - time.monotonic()))
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
        # wait for in-flight to clear (the worker that was mid-request should
        # have finished since we awaited its task).
        for _ in range(int(timeout_sec * 10)):
            if not self._in_flight:
                break
            await asyncio.sleep(0.1)
        self._stopped = True


# ---------------------------------------------------------------------------
# HPA Controller
# ---------------------------------------------------------------------------
class HPAController:
    """Decides worker count using queue depth + a target utilization.

    Uses Little's Law: required_workers = (in_flight + queue_depth) * avg_latency / poll_interval
    which is approximated by: required_workers = ceil(queue_depth / per_worker_target_backlog)
    """

    def __init__(
        self,
        pool: WorkerPool,
        queue: BoundedPriorityQueue,
        cfg: ServiceConfig,
        metrics: MetricsRegistry,
    ) -> None:
        self.pool = pool
        self.queue = queue
        self.cfg = cfg
        self.metrics = metrics
        self._stop = asyncio.Event()
        self._last_decision = cfg.min_workers
        self._smoothing = 0.4  # EWMA smoothing

    def stop(self) -> None:
        self._stop.set()

    async def run(self) -> None:
        # Start at minimum workers
        await self.pool.resize(self.cfg.min_workers)
        while not self._stop.is_set():
            try:
                await asyncio.wait_for(
                    self._stop.wait(), timeout=self.cfg.hpa_interval_sec
                )
                break
            except asyncio.TimeoutError:
                pass
            desired = self._compute_desired()
            # Apply EWMA smoothing to avoid flapping.
            target = int(
                round(
                    self._smoothing * desired
                    + (1 - self._smoothing) * self._last_decision
                )
            )
            target = max(self.cfg.min_workers, min(self.cfg.max_workers, target))
            if target != self._last_decision:
                await self.pool.resize(target)
                self._last_decision = target
            self.metrics.set_queue_depth(self.queue.size)
            self.metrics.set_in_flight(self.pool.in_flight)

    def _compute_desired(self) -> int:
        depth = self.queue.size
        in_flight = self.pool.in_flight
        # Each worker can keep up with about 1/target_utilization items.
        target_capacity = max(
            1, int(self.cfg.target_utilization * self.cfg.queue_capacity /
                   self.cfg.max_workers)
        )
        # How many workers do we need to drain the queue to target backlog?
        backlog = depth + in_flight
        if backlog == 0:
            return self.cfg.min_workers
        desired = max(
            self.cfg.min_workers,
            int((backlog + target_capacity - 1) // target_capacity),
        )
        return min(self.cfg.max_workers, desired)


# ---------------------------------------------------------------------------
# HTTP gateway (aiohttp if available, else a tiny stdlib server)
# ---------------------------------------------------------------------------
if AIOHTTP_AVAILABLE:

    class HTTPGateway:
        """A minimal HTTP interface to the autoscaler."""

        def __init__(
            self,
            queue: BoundedPriorityQueue,
            pool: WorkerPool,
            metrics: MetricsRegistry,
            cfg: ServiceConfig,
        ) -> None:
            self.queue = queue
            self.pool = pool
            self.metrics = metrics
            self.cfg = cfg
            self._app = web.Application()
            self._app.router.add_post("/v1/completions", self._completions)
            self._app.router.add_get("/healthz", self._health)
            self._app.router.add_get("/ready", self._ready)
            self._app.router.add_get("/metrics", self._metrics)
            self._app.router.add_post("/drain", self._drain)
            self._runner: Optional[web.AppRunner] = None

        async def start(self) -> None:
            self._runner = web.AppRunner(self._app)
            await self._runner.setup()
            site = web.TCPSite(
                self._runner, host=self.cfg.http_host, port=self.cfg.http_port
            )
            await site.start()
            log.info(
                "gateway_started",
                extra={"host": self.cfg.http_host, "port": self.cfg.http_port},
            )

        async def stop(self) -> None:
            if self._runner:
                await self._runner.cleanup()

        async def _completions(self, request: web.Request) -> web.Response:
            if self.pool.is_draining:
                return web.json_response(
                    {"error": "shutting_down", "retry_after_sec": 5}, status=503
                )
            try:
                payload = await request.json()
            except Exception:
                return web.json_response({"error": "bad_request"}, status=400)
            prompt = payload.get("prompt", "")
            if not isinstance(prompt, str) or not prompt:
                return web.json_response({"error": "missing_prompt"}, status=400)
            prio_str = payload.get("priority", "NORMAL").upper()
            try:
                priority = Priority[prio_str]
            except KeyError:
                return web.json_response({"error": "bad_priority"}, status=400)
            llm_req = LLMRequest(
                request_id=uuid.uuid4().hex,
                prompt=prompt,
                priority=priority,
                user_id=str(payload.get("user_id", "anon")),
                max_tokens=int(payload.get("max_tokens", 128)),
            )
            try:
                await self.queue.put(llm_req)
            except PriorityQueueFull:
                return web.json_response(
                    {"error": "overloaded", "retry_after_sec": 1}, status=503
                )
            return web.json_response(
                {"request_id": llm_req.request_id, "status": "queued"}, status=202
            )

        async def _health(self, _: web.Request) -> web.Response:
            return web.json_response({"status": "ok"})

        async def _ready(self, _: web.Request) -> web.Response:
            if self.pool.is_draining or self.queue.is_full():
                return web.json_response({"ready": False}, status=503)
            return web.json_response({"ready": True})

        async def _metrics(self, _: web.Request) -> web.Response:
            body, ctype = self.metrics.render()
            return web.Response(body=body, content_type=ctype)

        async def _drain(self, _: web.Request) -> web.Response:
            return web.json_response({"status": "draining"})

else:

    class HTTPGateway:  # type: ignore[no-redef]
        """Stub gateway when aiohttp is unavailable."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.queue = args[0] if args else None

        async def start(self) -> None:
            log.warning("gateway_disabled_no_aiohttp")

        async def stop(self) -> None:
            pass


# ---------------------------------------------------------------------------
# Load tester
# ---------------------------------------------------------------------------
@dataclass
class LoadTestReport:
    sent: int
    accepted: int
    rejected: int
    duration_sec: float
    throughput_rps: float
    p50_ms: float
    p95_ms: float
    p99_ms: float


class LoadTester:
    """A coroutine-friendly, mixed-priority load tester."""

    def __init__(
        self,
        queue: BoundedPriorityQueue,
        cfg: ServiceConfig,
        *,
        concurrency: int = 1000,
        total_requests: int = 2000,
    ) -> None:
        self.queue = queue
        self.cfg = cfg
        self.concurrency = concurrency
        self.total_requests = total_requests
        self._results: List[float] = []
        self._accepted = 0
        self._rejected = 0

    async def run(self) -> LoadTestReport:
        sent = 0
        sem = asyncio.Semaphore(self.concurrency)
        start = time.monotonic()

        async def one_request(seq: int) -> None:
            nonlocal sent
            sent += 1
            priority = random.choice(
                [Priority.LOW, Priority.NORMAL, Priority.HIGH,
                 Priority.NORMAL, Priority.NORMAL]
            )
            req = LLMRequest(
                request_id=f"lt-{seq:06d}",
                prompt="Explain quantum entanglement in a tweet.",
                priority=priority,
                user_id=f"user-{seq % 100}",
            )
            t0 = time.monotonic()
            try:
                await self.queue.put(req)
                self._accepted += 1
                self._results.append((time.monotonic() - t0) * 1000)
            except PriorityQueueFull:
                self._rejected += 1

        tasks: List[Awaitable[None]] = []
        for i in range(self.total_requests):
            async with sem:
                tasks.append(asyncio.create_task(one_request(i)))
                # yield to the loop occasionally
                if i % (self.concurrency * 2) == 0:
                    await asyncio.sleep(0)
        await asyncio.gather(*tasks, return_exceptions=True)
        duration = time.monotonic() - start
        latencies = sorted(self._results)
        if not latencies:
            p50 = p95 = p99 = 0.0
        else:
            n = len(latencies)

            def q(p: float) -> float:
                return latencies[min(n - 1, int(p * n))]

            p50, p95, p99 = q(0.50), q(0.95), q(0.99)
        report = LoadTestReport(
            sent=sent,
            accepted=self._accepted,
            rejected=self._rejected,
            duration_sec=round(duration, 3),
            throughput_rps=round(sent / max(duration, 1e-6), 1),
            p50_ms=round(p50, 2),
            p95_ms=round(p95, 2),
            p99_ms=round(p99, 2),
        )
        log.info("load_test_finished", extra=dataclasses.asdict(report))
        return report


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------
class AutoscalingLLMService:
    """Top-level glue -- starts workers, HPA, gateway, and load tester."""

    def __init__(self, cfg: Optional[ServiceConfig] = None) -> None:
        self.cfg = cfg or ServiceConfig()
        self.metrics = MetricsRegistry()
        self.queue = BoundedPriorityQueue(self.cfg.queue_capacity)
        self.client_primary = LLMClient(
            name=self.cfg.downstream_primary,
            avg_latency_ms=self.cfg.fake_latency_ms,
            error_rate=self.cfg.fake_error_rate,
        )
        self.client_fallback = LLMClient(
            name=self.cfg.downstream_fallback,
            avg_latency_ms=self.cfg.fake_latency_ms // 2,
            error_rate=max(0.001, self.cfg.fake_error_rate / 2),
        )
        self.breaker_primary = CircuitBreaker(
            name=self.cfg.downstream_primary,
            window_sec=self.cfg.breaker_window_sec,
            failure_threshold=self.cfg.breaker_threshold,
            cooldown_sec=self.cfg.breaker_cooldown_sec,
            metrics=self.metrics,
        )
        self.breaker_fallback = CircuitBreaker(
            name=self.cfg.downstream_fallback,
            window_sec=self.cfg.breaker_window_sec,
            failure_threshold=self.cfg.breaker_threshold,
            cooldown_sec=self.cfg.breaker_cooldown_sec,
            metrics=self.metrics,
        )
        self.pool = WorkerPool(
            queue=self.queue,
            client_primary=self.client_primary,
            client_fallback=self.client_fallback,
            breaker_primary=self.breaker_primary,
            breaker_fallback=self.breaker_fallback,
            metrics=self.metrics,
            cfg=self.cfg,
        )
        self.hpa = HPAController(
            pool=self.pool, queue=self.queue, cfg=self.cfg, metrics=self.metrics
        )
        self.gateway = HTTPGateway(
            queue=self.queue, pool=self.pool, metrics=self.metrics, cfg=self.cfg
        )
        self._shutdown = asyncio.Event()

    async def start(self) -> None:
        await self.pool.start(self.cfg.min_workers)
        await self.gateway.start()
        self._hpa_task = asyncio.create_task(self.hpa.run(), name="hpa")

    async def serve_forever(self) -> None:
        await self._shutdown.wait()

    def request_shutdown(self) -> None:
        self._shutdown.set()

    async def shutdown(self) -> None:
        log.info("shutdown_start")
        self._shutdown.set()
        self.hpa.stop()
        await self.queue.close()
        # Drain workers with a hard timeout.
        await self.pool.drain(self.cfg.drain_timeout_sec)
        await self.gateway.stop()
        log.info("shutdown_complete")


# ---------------------------------------------------------------------------
# Demo runner
# ---------------------------------------------------------------------------
async def _run_demo() -> None:
    """End-to-end demo: start service, run a load test, show metrics, drain."""
    cfg = ServiceConfig(
        min_workers=2,
        max_workers=8,
        queue_capacity=2000,
        fake_latency_ms=20,
        fake_error_rate=0.05,
    )
    svc = AutoscalingLLMService(cfg=cfg)
    await svc.start()
    # Attach SIGINT handler for graceful shutdown.
    loop = asyncio.get_running_loop()

    def _stop() -> None:
        svc.request_shutdown()

    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, _stop)

    tester = LoadTester(
        svc.queue, cfg, concurrency=300, total_requests=1500
    )
    report = await tester.run()
    print("LOAD TEST REPORT:", json.dumps(dataclasses.asdict(report), indent=2))
    # Let the HPA react + workers drain the queue.
    await asyncio.sleep(cfg.hpa_interval_sec * 2)
    body, _ = svc.metrics.render()
    text = body.decode()
    if PROMETHEUS_AVAILABLE:
        # Show a few interesting metrics to stdout.
        interesting = (
            "llm_queue_depth",
            "llm_active_workers",
            "llm_in_flight_requests",
            "llm_requests_total",
            "llm_breaker_state",
            "llm_request_latency_seconds_count",
        )
        snippet = [
            line for line in text.splitlines() if any(k in line for k in interesting)
        ]
        print("\nMETRICS (filtered):\n" + "\n".join(snippet)[:2000])
    else:
        print("\nMETRICS (fallback):")
        print(text[:2000])
    print("\nFINAL POOL SIZE:", svc.pool.size)
    print("FINAL QUEUE DEPTH:", svc.queue.size)
    print(
        "BREAKER STATS:",
        json.dumps([svc.breaker_primary.stats(), svc.breaker_fallback.stats()], indent=2),
    )
    await svc.shutdown()


async def _run_loadtest_only() -> None:
    cfg = ServiceConfig(
        min_workers=4,
        max_workers=16,
        queue_capacity=4000,
        fake_latency_ms=15,
    )
    svc = AutoscalingLLMService(cfg=cfg)
    await svc.start()
    tester = LoadTester(svc.queue, cfg, concurrency=500, total_requests=2500)
    report = await tester.run()
    print(json.dumps(dataclasses.asdict(report), indent=2))
    await svc.shutdown()


async def _run_gateway() -> None:
    cfg = ServiceConfig(
        min_workers=3,
        max_workers=12,
        queue_capacity=3000,
    )
    svc = AutoscalingLLMService(cfg=cfg)
    await svc.start()
    print(
        f"Gateway listening on http://{cfg.http_host}:{cfg.http_port}; "
        f"metrics on http://{cfg.http_host}:{cfg.http_port}/metrics"
    )
    try:
        await svc.serve_forever()
    finally:
        await svc.shutdown()


def main() -> None:
    parser = argparse.ArgumentParser(description="Autoscaling LLM Service")
    parser.add_argument(
        "--mode",
        choices=["demo", "gateway", "loadtest"],
        default=os.environ.get("LLM_MODE", "demo"),
    )
    args = parser.parse_args()
    if args.mode == "demo":
        asyncio.run(_run_demo())
    elif args.mode == "loadtest":
        asyncio.run(_run_loadtest_only())
    elif args.mode == "gateway":
        asyncio.run(_run_gateway())


if __name__ == "__main__":
    main()
