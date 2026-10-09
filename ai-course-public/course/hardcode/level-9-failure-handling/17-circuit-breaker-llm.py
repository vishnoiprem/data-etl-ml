"""
Lab 17: Circuit Breaker for LLM Calls
=====================================

A production-grade circuit breaker for probabilistic AI/LLM services. The
breaker handles the unique failure modes of LLMs:
- Non-deterministic failure rate (a model may degrade for hours then recover).
- Latency spikes (long-tail completion times).
- Token cost spikes (a model quietly started using much more output).
- Quality drops (the same prompt returns nonsense, but with 200 OK).

It implements:
- A classic three-state circuit breaker (closed / half-open / open).
- Multi-signal tripping: failure rate, latency p99, token cost overrun.
- Exponential backoff + full jitter for retries.
- A "model degradation detector" that compares current response quality
  to a recent baseline (length, perplexity proxy, entropy).
- A cheaper-model fallback (or cached response) when open.
- A dashboard endpoint + Prometheus metrics.
- Logs every state transition for debugging.

Architecture
------------

    +----------+       +-----------------+       +----------------+
    |  Caller  | ----> | CircuitBreaker  | ----> | Primary LLM    |
    +----------+       | (state machine) |       +----------------+
                       +--------+--------+
                                |
                                | (on open)
                                v
                       +-----------------+
                       |  Fallback (LLM  |
                       |   cheaper, or   |
                       |   cache)        |
                       +-----------------+

   +-----------[ Model Degradation Detector ]-------------+
   | - response length vs baseline                         |
   | - perplexity proxy (avg token log-prob)               |
   | - entropy of next-token distribution                 |
   | - failure to follow a known canary prompt             |
   +--------------------------------------------------------+

Components
----------
1. CircuitBreaker: state machine with rolling failure/latency/cost windows.
2. RetryPolicy: exponential backoff with full jitter.
3. ModelDegradationDetector: heuristics to catch silent quality drops.
4. CachedFallback: an in-memory LRU + TTL cache for safe defaults.
5. FallbackLLM: a cheap "model" used when the breaker is open.
6. DashboardServer: /dashboard, /metrics, /healthz endpoints.
7. FailureInjector: a controllable failure source for the demo.

How to run
----------
$ python 17-circuit-breaker-llm.py --mode demo
$ python 17-circuit-breaker-llm.py --mode loadtest
$ python 17-circuit-breaker-llm.py --mode gateway

Configuration (env vars)
------------------------
- CB_FAILURE_THRESHOLD     (float, default 0.5)
- CB_WINDOW_SEC            (float, default 60)
- CB_LATENCY_P99_MS        (float, default 2000)
- CB_COST_PER_MIN_USD      (float, default 5.0)
- CB_COOLDOWN_SEC          (float, default 30)
- CB_HALF_OPEN_TRIALS      (int, default 3)
- CB_RETRY_MAX             (int, default 4)
- CB_RETRY_BASE_MS         (int, default 50)
- CB_FAKE_LATENCY_MS       (int, default 80)
- CB_FAKE_ERROR_RATE       (float, default 0.05)
- CB_FAKE_DEGRADATION_RATE (float, default 0.02)
- CB_DASHBOARD_PORT        (int, default 8085)
- CB_CACHE_TTL_SEC         (float, default 120)
- CB_PROBABILISTIC_MODE    (int, 1)            # see notes on stochastic LLM

Dependencies
------------
- aiohttp (HTTP)
- prometheus_client (optional)
- Standard library (asyncio, math, time, statistics, json)

Failure modes
-------------
- All retries fail -> open the breaker -> serve fallback.
- Latency p99 exceeds budget -> open even at low error rate.
- Cost per minute exceeds budget -> open to protect spend.
- Quality degradation detected -> open and increment a "degradation" counter.
- Fallback also fails -> return last-known-good cached response (if any).

What makes it production-grade
------------------------------
- Multi-signal state machine (not just failure rate).
- Real backoff (full-jitter) for retries.
- Quality degradation detection (catches silent model regressions).
- Per-state metrics + state transition log.
- Per-state Prometheus gauges.
- Graceful shutdown.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import dataclasses
import json
import logging
import math
import os
import random
import signal
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

try:
    from aiohttp import web  # type: ignore
    AIOHTTP_AVAILABLE = True
except Exception:  # pragma: no cover
    AIOHTTP_AVAILABLE = False

try:
    from prometheus_client import (  # type: ignore
        Counter, Gauge, Histogram, CollectorRegistry,
        generate_latest, CONTENT_TYPE_LATEST,
    )
    PROMETHEUS_AVAILABLE = True
except Exception:  # pragma: no cover
    PROMETHEUS_AVAILABLE = False


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "ts": time.time(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
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
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(JsonFormatter())
        logger.addHandler(h)
        logger.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())
        logger.propagate = False
    return logger


log = _build_logger("circuit-breaker-llm")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class BreakerConfig:
    failure_threshold: float = float(os.environ.get("CB_FAILURE_THRESHOLD", "0.5"))
    window_sec: float = float(os.environ.get("CB_WINDOW_SEC", "60"))
    latency_p99_ms: float = float(os.environ.get("CB_LATENCY_P99_MS", "2000"))
    cost_per_min_usd: float = float(os.environ.get("CB_COST_PER_MIN_USD", "5.0"))
    cooldown_sec: float = float(os.environ.get("CB_COOLDOWN_SEC", "30"))
    half_open_trials: int = int(os.environ.get("CB_HALF_OPEN_TRIALS", "3"))
    retry_max: int = int(os.environ.get("CB_RETRY_MAX", "4"))
    retry_base_ms: int = int(os.environ.get("CB_RETRY_BASE_MS", "50"))
    fake_latency_ms: int = int(os.environ.get("CB_FAKE_LATENCY_MS", "80"))
    fake_error_rate: float = float(os.environ.get("CB_FAKE_ERROR_RATE", "0.05"))
    fake_degradation_rate: float = float(
        os.environ.get("CB_FAKE_DEGRADATION_RATE", "0.02")
    )
    dashboard_port: int = int(os.environ.get("CB_DASHBOARD_PORT", "8085"))
    dashboard_host: str = os.environ.get("CB_DASHBOARD_HOST", "127.0.0.1")
    cache_ttl_sec: float = float(os.environ.get("CB_CACHE_TTL_SEC", "120"))
    cost_per_1k_tokens_usd: float = float(
        os.environ.get("CB_COST_PER_1K_TOKENS", "0.01")
    )
    min_window_samples: int = int(os.environ.get("CB_MIN_SAMPLES", "10"))


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
class Metrics:
    def __init__(self) -> None:
        self.use_prom = PROMETHEUS_AVAILABLE
        if self.use_prom:
            self.registry = CollectorRegistry()
            self.calls = Counter(
                "cb_calls_total",
                "Total breaker-mediated calls.",
                ["outcome"],
                registry=self.registry,
            )
            self.latency = Histogram(
                "cb_call_latency_seconds",
                "Call latency (including retries).",
                ["outcome"],
                buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
                registry=self.registry,
            )
            self.state = Gauge(
                "cb_state",
                "Current breaker state (0=closed, 1=half_open, 2=open).",
                registry=self.registry,
            )
            self.transitions = Counter(
                "cb_transitions_total",
                "State transitions.",
                ["from_state", "to_state", "reason"],
                registry=self.registry,
            )
            self.degradations = Counter(
                "cb_degradations_total",
                "Detected quality degradations.",
                registry=self.registry,
            )
            self.cost = Counter(
                "cb_cost_usd_total",
                "Cumulative cost in USD.",
                ["model"],
                registry=self.registry,
            )
            self.tokens = Counter(
                "cb_tokens_total",
                "Total tokens processed.",
                ["model", "direction"],
                registry=self.registry,
            )
            self.retries = Counter(
                "cb_retries_total",
                "Total retries.",
                registry=self.registry,
            )
            self.cache_hits = Counter(
                "cb_cache_hits_total",
                "Fallback served from cache.",
                registry=self.registry,
            )
        else:
            self._counters: Dict[str, int] = {}

    def inc_call(self, outcome: str) -> None:
        if self.use_prom:
            self.calls.labels(outcome=outcome).inc()
        else:
            self._counters[f"call:{outcome}"] = self._counters.get(f"call:{outcome}", 0) + 1

    def observe_latency(self, outcome: str, sec: float) -> None:
        if self.use_prom:
            self.latency.labels(outcome=outcome).observe(sec)
        else:
            pass

    def set_state(self, state: int) -> None:
        if self.use_prom:
            self.state.set(state)
        else:
            self._counters["state"] = state

    def inc_transition(self, frm: int, to: int, reason: str) -> None:
        if self.use_prom:
            self.transitions.labels(
                from_state=str(frm), to_state=str(to), reason=reason
            ).inc()
        else:
            self._counters[f"tr:{frm}->{to}:{reason}"] = (
                self._counters.get(f"tr:{frm}->{to}:{reason}", 0) + 1
            )

    def inc_degradation(self) -> None:
        if self.use_prom:
            self.degradations.inc()
        else:
            self._counters["deg"] = self._counters.get("deg", 0) + 1

    def add_cost(self, usd: float, model: str, tokens_in: int, tokens_out: int) -> None:
        if self.use_prom:
            self.cost.labels(model=model).inc(usd)
            self.tokens.labels(model=model, direction="in").inc(tokens_in)
            self.tokens.labels(model=model, direction="out").inc(tokens_out)
        else:
            self._counters[f"cost:{model}"] = self._counters.get(f"cost:{model}", 0) + usd

    def inc_retry(self) -> None:
        if self.use_prom:
            self.retries.inc()
        else:
            self._counters["retry"] = self._counters.get("retry", 0) + 1

    def inc_cache_hit(self) -> None:
        if self.use_prom:
            self.cache_hits.inc()
        else:
            self._counters["cache_hit"] = self._counters.get("cache_hit", 0) + 1

    def render(self) -> Tuple[bytes, str]:
        if self.use_prom:
            return generate_latest(self.registry), CONTENT_TYPE_LATEST
        return (
            json.dumps({"counters": self._counters}, indent=2).encode(),
            "application/json",
        )


# ---------------------------------------------------------------------------
# Retry policy
# ---------------------------------------------------------------------------
class RetryPolicy:
    def __init__(self, *, max_retries: int, base_ms: int) -> None:
        self.max_retries = max_retries
        self.base_ms = base_ms

    async def sleep(self, attempt: int) -> None:
        # Exponential backoff with full jitter.
        cap = self.base_ms * (2 ** attempt)
        delay_ms = random.uniform(0, cap)
        await asyncio.sleep(delay_ms / 1000.0)


# ---------------------------------------------------------------------------
# LRU TTL cache
# ---------------------------------------------------------------------------
class TTLCache:
    def __init__(self, ttl_sec: float) -> None:
        self.ttl = ttl_sec
        self._store: Dict[str, Tuple[float, str]] = {}

    def get(self, key: str) -> Optional[str]:
        item = self._store.get(key)
        if not item:
            return None
        ts, value = item
        if time.monotonic() - ts > self.ttl:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: str) -> None:
        self._store[key] = (time.monotonic(), value)

    def __len__(self) -> int:
        return len(self._store)


# ---------------------------------------------------------------------------
# Mock LLM clients
# ---------------------------------------------------------------------------
class LLMError(Exception):
    pass


class LLMResponse:
    def __init__(
        self,
        *,
        text: str,
        tokens_in: int,
        tokens_out: int,
        latency_sec: float,
        perplexity: float = 0.0,
        entropy: float = 0.0,
        model: str = "primary",
    ) -> None:
        self.text = text
        self.tokens_in = tokens_in
        self.tokens_out = tokens_out
        self.latency_sec = latency_sec
        self.perplexity = perplexity
        self.entropy = entropy
        self.model = model

    @property
    def cost_usd(self) -> float:
        # Used by the breaker; the cost is computed at call site.
        return 0.0


class MockLLM:
    """A mock LLM that simulates non-deterministic behavior.

    The mock is *probabilistic*: error rate, latency, and degradation are
    random per-call. It also exposes `perplexity` and `entropy` so the
    degradation detector has something to look at.
    """

    def __init__(
        self,
        *,
        name: str,
        avg_latency_ms: int,
        error_rate: float,
        degradation_rate: float,
    ) -> None:
        self.name = name
        self.avg_latency_ms = avg_latency_ms
        self.error_rate = error_rate
        self.degradation_rate = degradation_rate
        self.total_calls = 0
        self.total_errors = 0
        self.total_degradations = 0

    async def complete(self, prompt: str, max_tokens: int) -> LLMResponse:
        self.total_calls += 1
        # Latency
        start = time.monotonic()
        await asyncio.sleep(
            self.avg_latency_ms / 1000.0 * random.uniform(0.5, 2.5)
        )
        latency = time.monotonic() - start
        # Error
        if random.random() < self.error_rate:
            self.total_errors += 1
            raise LLMError(f"{self.name} simulated error")
        # Quality metrics (low perplexity, mid entropy when healthy)
        degraded = random.random() < self.degradation_rate
        if degraded:
            self.total_degradations += 1
            # Simulate nonsense: tiny output, very high perplexity
            text = "###ERR###"
            perplexity = 8.0
            entropy = 6.0
        else:
            text = (
                f"[{self.name}] response to: "
                + " ".join(prompt.split()[:10])
                + " ..."
            )
            perplexity = random.uniform(0.5, 1.5)
            entropy = random.uniform(2.0, 4.0)
        tokens_in = len(prompt.split())
        tokens_out = len(text.split())
        return LLMResponse(
            text=text,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_sec=latency,
            perplexity=perplexity,
            entropy=entropy,
            model=self.name,
        )


# ---------------------------------------------------------------------------
# Model degradation detector
# ---------------------------------------------------------------------------
class ModelDegradationDetector:
    """Tracks response quality over time and flags sudden drops.

    Signals used:
    - mean response length vs baseline (drops => degradation)
    - mean perplexity vs baseline (rises => degradation)
    - mean entropy vs baseline (very high or very low => degradation)
    - canary prompt -- a fixed prompt we expect a known answer from.
    """

    def __init__(self, *, window_sec: float = 300.0) -> None:
        self.window_sec = window_sec
        self._samples: Deque[Tuple[float, float, float, float]] = deque()
        # Canary: prompt -> expected token count
        self._canary_prompt = "What is 2+2?"
        self._canary_expected_min = 2
        self._canary_expected_max = 8
        self._degradations = 0

    def observe(
        self, *, length: int, perplexity: float, entropy: float
    ) -> None:
        now = time.time()
        self._samples.append((now, length, perplexity, entropy))
        cutoff = now - self.window_sec
        while self._samples and self._samples[0][0] < cutoff:
            self._samples.popleft()

    def is_degraded(self) -> Tuple[bool, str]:
        if len(self._samples) < 20:
            return False, "insufficient_data"
        # Compare last 20 to the prior 100.
        recent = list(self._samples)[-20:]
        older = list(self._samples)[:-20]
        if len(older) < 10:
            return False, "no_baseline"
        recent_len = sum(s[1] for s in recent) / len(recent)
        older_len = sum(s[1] for s in older) / len(older)
        recent_perp = sum(s[2] for s in recent) / len(recent)
        older_perp = sum(s[2] for s in older) / len(older)
        recent_ent = sum(s[3] for s in recent) / len(recent)
        # Heuristics:
        if older_len > 0 and recent_len < older_len * 0.4:
            self._degradations += 1
            return True, "response_length_collapse"
        if older_perp > 0 and recent_perp > older_perp * 2.5:
            self._degradations += 1
            return True, "perplexity_spike"
        if recent_ent > 5.5:
            self._degradations += 1
            return True, "high_entropy"
        return False, "ok"

    def check_canary(self, response_text: str) -> bool:
        words = response_text.split()
        if not (
            self._canary_expected_min
            <= len(words)
            <= self._canary_expected_max
        ):
            return False
        if "4" not in response_text and "four" not in response_text.lower():
            return False
        return True

    def stats(self) -> Dict[str, Any]:
        if not self._samples:
            return {"samples": 0}
        n = len(self._samples)
        lens = [s[1] for s in self._samples]
        perps = [s[2] for s in self._samples]
        ents = [s[3] for s in self._samples]
        return {
            "samples": n,
            "mean_length": sum(lens) / n,
            "mean_perplexity": sum(perps) / n,
            "mean_entropy": sum(ents) / n,
            "degradations_total": self._degradations,
        }


# ---------------------------------------------------------------------------
# Circuit breaker
# ---------------------------------------------------------------------------
class State(int, Enum):
    CLOSED = 0
    HALF_OPEN = 1
    OPEN = 2


@dataclass
class CallRecord:
    ts: float
    success: bool
    latency_sec: float
    cost_usd: float


class CircuitBreaker:
    """A multi-signal circuit breaker for LLM calls.

    The breaker tracks:
    - failure rate in a rolling window
    - latency p99 in the same window
    - cost per minute
    - quality degradation flag

    If ANY signal crosses its threshold, the breaker opens.
    """

    def __init__(
        self,
        cfg: BreakerConfig,
        metrics: Metrics,
        retry: RetryPolicy,
        primary: MockLLM,
        fallback: MockLLM,
        cache: TTLCache,
        degradation: ModelDegradationDetector,
    ) -> None:
        self.cfg = cfg
        self.metrics = metrics
        self.retry = retry
        self.primary = primary
        self.fallback = fallback
        self.cache = cache
        self.degradation = degradation
        self.state = State.CLOSED
        self._records: Deque[CallRecord] = deque()
        self._cost_window: Deque[Tuple[float, float]] = deque()
        self._opened_at: Optional[float] = None
        self._half_open_trials_left = 0
        self._lock = asyncio.Lock()
        self.transition_log: Deque[Dict[str, Any]] = deque(maxlen=200)
        self.metrics.set_state(int(self.state))

    async def call(self, prompt: str, max_tokens: int) -> Tuple[LLMResponse, str]:
        """Returns (response, source) where source is 'primary'/'fallback'/'cache'."""
        async with self._lock:
            # State-dependent entry policy.
            if self.state == State.OPEN:
                if (
                    self._opened_at is not None
                    and time.monotonic() - self._opened_at >= self.cfg.cooldown_sec
                ):
                    await self._transition(State.HALF_OPEN, "cooldown_elapsed")
                    self._half_open_trials_left = self.cfg.half_open_trials
                else:
                    return await self._serve_fallback(prompt, max_tokens)
            if self.state == State.HALF_OPEN:
                if self._half_open_trials_left <= 0:
                    return await self._serve_fallback(prompt, max_tokens)
                self._half_open_trials_left -= 1
        # Call primary with retries.
        start = time.monotonic()
        last_exc: Optional[Exception] = None
        for attempt in range(self.cfg.retry_max + 1):
            try:
                resp = await self.primary.complete(prompt, max_tokens)
                # Run quality checks
                self.degradation.observe(
                    length=len(resp.text.split()),
                    perplexity=resp.perplexity,
                    entropy=resp.entropy,
                )
                degraded, reason = self.degradation.is_degraded()
                cost = (resp.tokens_in + resp.tokens_out) / 1000.0 * self.cfg.cost_per_1k_tokens_usd
                # canary check (cheap, do it occasionally)
                if (
                    random.random() < 0.05
                    and not self.degradation.check_canary(resp.text)
                ):
                    degraded = True
                    reason = "canary_failed"
                if degraded:
                    self.metrics.inc_degradation()
                    log.warning("quality_degraded", extra={"reason": reason})
                    await self._record_call(
                        success=False,
                        latency_sec=time.monotonic() - start,
                        cost_usd=cost,
                    )
                    await self._maybe_open(reason=f"degradation:{reason}")
                    return await self._serve_fallback(prompt, max_tokens)
                # success path
                await self._record_call(
                    success=True,
                    latency_sec=time.monotonic() - start,
                    cost_usd=cost,
                )
                self.metrics.add_cost(cost, self.primary.name, resp.tokens_in, resp.tokens_out)
                if self.state == State.HALF_OPEN:
                    await self._transition(State.CLOSED, "half_open_success")
                return resp, "primary"
            except Exception as exc:
                last_exc = exc
                self.metrics.inc_retry()
                if attempt < self.cfg.retry_max:
                    await self.retry.sleep(attempt)
                    continue
                # exhausted
                cost = (max_tokens + len(prompt.split())) / 1000.0 * self.cfg.cost_per_1k_tokens_usd
                await self._record_call(
                    success=False,
                    latency_sec=time.monotonic() - start,
                    cost_usd=cost,
                )
                await self._maybe_open(reason=f"errors:{type(exc).__name__}")
                return await self._serve_fallback(prompt, max_tokens)
        # Should not reach.
        return await self._serve_fallback(prompt, max_tokens)

    async def _serve_fallback(self, prompt: str, max_tokens: int) -> Tuple[LLMResponse, str]:
        # 1. cache
        cache_key = f"{(prompt, max_tokens)}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            self.metrics.inc_cache_hit()
            r = LLMResponse(
                text=cached,
                tokens_in=len(prompt.split()),
                tokens_out=len(cached.split()),
                latency_sec=0.0,
                model="cache",
            )
            return r, "cache"
        # 2. fallback LLM
        try:
            r = await self.fallback.complete(prompt, max_tokens)
            self.cache.set(cache_key, r.text)
            self.metrics.add_cost(
                (r.tokens_in + r.tokens_out)
                / 1000.0
                * self.cfg.cost_per_1k_tokens_usd,
                self.fallback.name,
                r.tokens_in,
                r.tokens_out,
            )
            return r, "fallback"
        except Exception as exc:
            log.error("fallback_failed", extra={"err": str(exc)})
            r = LLMResponse(
                text="[unavailable]",
                tokens_in=len(prompt.split()),
                tokens_out=1,
                latency_sec=0.0,
                model="none",
            )
            return r, "none"

    async def _record_call(
        self, *, success: bool, latency_sec: float, cost_usd: float
    ) -> None:
        now = time.monotonic()
        self._records.append(CallRecord(now, success, latency_sec, cost_usd))
        self._cost_window.append((now, cost_usd))
        await self._evict(now)
        # Re-evaluate trip conditions periodically.
        await self._evaluate()

    async def _evaluate(self) -> None:
        # Failure rate
        fails = sum(1 for r in self._records if not r.success)
        total = len(self._records)
        if total >= self.cfg.min_window_samples:
            fail_rate = fails / total
            if fail_rate >= self.cfg.failure_threshold:
                await self._maybe_open(reason="fail_rate")
        # Latency p99
        if self._records:
            lats = sorted(r.latency_sec for r in self._records)
            idx = max(0, int(0.99 * (len(lats) - 1)))
            p99 = lats[idx]
            if p99 * 1000 >= self.cfg.latency_p99_ms:
                await self._maybe_open(reason="latency_p99")
        # Cost per minute
        now = time.monotonic()
        recent_cost = sum(c for ts, c in self._cost_window if now - ts <= 60)
        if recent_cost >= self.cfg.cost_per_min_usd:
            await self._maybe_open(reason="cost_budget")

    async def _evict(self, now: float) -> None:
        cutoff = now - self.cfg.window_sec
        while self._records and self._records[0].ts < cutoff:
            self._records.popleft()
        while self._cost_window and self._cost_window[0][0] < cutoff:
            self._cost_window.popleft()

    async def _maybe_open(self, *, reason: str) -> None:
        if self.state == State.OPEN:
            return
        await self._transition(State.OPEN, reason=reason)

    async def _transition(self, new_state: State, reason: str) -> None:
        old = self.state
        if old == new_state:
            return
        self.state = new_state
        self.metrics.set_state(int(new_state))
        self.metrics.inc_transition(int(old), int(new_state), reason)
        if new_state == State.OPEN:
            self._opened_at = time.monotonic()
        if new_state == State.CLOSED:
            self._opened_at = None
            self._records.clear()
        if new_state == State.HALF_OPEN:
            self._half_open_trials_left = self.cfg.half_open_trials
        entry = {
            "ts": time.time(),
            "from": int(old),
            "to": int(new_state),
            "reason": reason,
        }
        self.transition_log.appendleft(entry)
        log.info("breaker_transition", extra=entry)

    def stats(self) -> Dict[str, Any]:
        now = time.monotonic()
        recent_cost = sum(c for ts, c in self._cost_window if now - ts <= 60)
        fails = sum(1 for r in self._records if not r.success)
        total = len(self._records)
        lats = sorted(r.latency_sec for r in self._records)
        p99 = lats[int(0.99 * (len(lats) - 1))] if lats else 0.0
        return {
            "state": int(self.state),
            "samples": total,
            "failures": fails,
            "fail_rate": (fails / total) if total else 0.0,
            "latency_p99_ms": round(p99 * 1000, 2),
            "cost_per_min_usd": round(recent_cost, 4),
            "transitions": list(self.transition_log)[:10],
        }


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
if AIOHTTP_AVAILABLE:

    class Dashboard:
        def __init__(
            self,
            cfg: BreakerConfig,
            metrics: Metrics,
            breaker: CircuitBreaker,
            primary: MockLLM,
            fallback: MockLLM,
            cache: TTLCache,
            degradation: ModelDegradationDetector,
        ) -> None:
            self.cfg = cfg
            self.metrics = metrics
            self.breaker = breaker
            self.primary = primary
            self.fallback = fallback
            self.cache = cache
            self.degradation = degradation
            self._app = web.Application()
            self._app.router.add_get("/healthz", self._healthz)
            self._app.router.add_get("/metrics", self._metrics)
            self._app.router.add_get("/dashboard", self._dashboard)
            self._app.router.add_get("/transitions", self._transitions)
            self._runner: Optional[web.AppRunner] = None

        async def start(self) -> None:
            self._runner = web.AppRunner(self._app)
            await self._runner.setup()
            site = web.TCPSite(self._runner, host=self.cfg.dashboard_host, port=self.cfg.dashboard_port)
            await site.start()
            log.info(
                "dashboard_started",
                extra={"host": self.cfg.dashboard_host, "port": self.cfg.dashboard_port},
            )

        async def stop(self) -> None:
            if self._runner:
                await self._runner.cleanup()

        async def _healthz(self, _: web.Request) -> web.Response:
            return web.json_response({"status": "ok"})

        async def _metrics(self, _: web.Request) -> web.Response:
            body, ctype = self.metrics.render()
            return web.Response(body=body, content_type=ctype)

        async def _transitions(self, _: web.Request) -> web.Response:
            return web.json_response(
                {"transitions": list(self.breaker.transition_log)}
            )

        async def _dashboard(self, _: web.Request) -> web.Response:
            return web.json_response(
                {
                    "breaker": self.breaker.stats(),
                    "primary": {
                        "name": self.primary.name,
                        "total_calls": self.primary.total_calls,
                        "total_errors": self.primary.total_errors,
                        "total_degradations": self.primary.total_degradations,
                    },
                    "fallback": {
                        "name": self.fallback.name,
                        "total_calls": self.fallback.total_calls,
                        "total_errors": self.fallback.total_errors,
                    },
                    "cache": {"size": len(self.cache)},
                    "degradation": self.degradation.stats(),
                    "config": {
                        "failure_threshold": self.cfg.failure_threshold,
                        "latency_p99_ms": self.cfg.latency_p99_ms,
                        "cost_per_min_usd": self.cfg.cost_per_min_usd,
                        "cooldown_sec": self.cfg.cooldown_sec,
                    },
                }
            )


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------
class Service:
    def __init__(self, cfg: Optional[BreakerConfig] = None) -> None:
        self.cfg = cfg or BreakerConfig()
        self.metrics = Metrics()
        self.retry = RetryPolicy(
            max_retries=self.cfg.retry_max, base_ms=self.cfg.retry_base_ms
        )
        self.cache = TTLCache(self.cfg.cache_ttl_sec)
        self.primary = MockLLM(
            name="primary-large",
            avg_latency_ms=self.cfg.fake_latency_ms,
            error_rate=self.cfg.fake_error_rate,
            degradation_rate=self.cfg.fake_degradation_rate,
        )
        self.fallback = MockLLM(
            name="fallback-small",
            avg_latency_ms=self.cfg.fake_latency_ms // 4,
            error_rate=0.001,
            degradation_rate=0.0,
        )
        self.degradation = ModelDegradationDetector()
        self.breaker = CircuitBreaker(
            cfg=self.cfg,
            metrics=self.metrics,
            retry=self.retry,
            primary=self.primary,
            fallback=self.fallback,
            cache=self.cache,
            degradation=self.degradation,
        )
        self.dashboard: Optional["Dashboard"] = None

    async def start(self) -> None:
        if AIOHTTP_AVAILABLE:
            self.dashboard = Dashboard(
                self.cfg, self.metrics, self.breaker,
                self.primary, self.fallback, self.cache, self.degradation,
            )
            await self.dashboard.start()

    async def stop(self) -> None:
        if self.dashboard:
            await self.dashboard.stop()

    async def query(self, prompt: str, max_tokens: int = 64) -> Dict[str, Any]:
        start = time.monotonic()
        resp, source = await self.breaker.call(prompt, max_tokens)
        elapsed = time.monotonic() - start
        self.metrics.inc_call(source)
        self.metrics.observe_latency(source, elapsed)
        return {
            "text": resp.text,
            "source": source,
            "model": resp.model,
            "latency_sec": round(elapsed, 4),
            "tokens_in": resp.tokens_in,
            "tokens_out": resp.tokens_out,
        }


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
async def _run_demo() -> None:
    cfg = BreakerConfig(
        failure_threshold=0.4,
        latency_p99_ms=500.0,
        cost_per_min_usd=2.0,
        cooldown_sec=10,
        half_open_trials=3,
        fake_error_rate=0.10,
        fake_degradation_rate=0.06,
    )
    svc = Service(cfg=cfg)
    await svc.start()
    loop = asyncio.get_running_loop()

    def _stop() -> None:
        pass

    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, _stop)
    results = []
    # Run a burst of queries
    for i in range(120):
        try:
            r = await svc.query(
                prompt=f"Question {i}: what is the meaning of life?",
                max_tokens=random.randint(20, 80),
            )
            results.append(r["source"])
        except Exception as exc:
            log.warning("query_error", extra={"err": str(exc), "i": i})
        await asyncio.sleep(0.05)
    counts: Dict[str, int] = {}
    for s in results:
        counts[s] = counts.get(s, 0) + 1
    print("\nRESULT SOURCES:", json.dumps(counts, indent=2))
    print("\nBREAKER STATS:")
    print(json.dumps(svc.breaker.stats(), indent=2))
    print("\nDEGRADATION:", json.dumps(svc.degradation.stats(), indent=2))
    body, _ = svc.metrics.render()
    text = body.decode()
    if PROMETHEUS_AVAILABLE:
        keys = ("cb_calls_total", "cb_state", "cb_transitions_total",
                "cb_degradations_total", "cb_cost_usd_total",
                "cb_retries_total", "cb_cache_hits_total")
        print("\nMETRICS (filtered):")
        for line in text.splitlines():
            if any(k in line for k in keys):
                print(" ", line)
    else:
        print("\nMETRICS (fallback):")
        print(text[:1500])
    await svc.stop()


async def _run_loadtest() -> None:
    cfg = BreakerConfig(
        fake_error_rate=0.05,
        fake_degradation_rate=0.03,
        failure_threshold=0.5,
    )
    svc = Service(cfg=cfg)
    await svc.start()
    n = 0
    for i in range(500):
        r = await svc.query(f"Q{i}: explain something", max_tokens=32)
        n += 1
    print(f"completed {n} queries")
    print(json.dumps(svc.breaker.stats(), indent=2))
    await svc.stop()


async def _run_gateway() -> None:
    cfg = BreakerConfig()
    svc = Service(cfg=cfg)
    await svc.start()
    print(f"Dashboard on http://{cfg.dashboard_host}:{cfg.dashboard_port}/dashboard")
    try:
        await asyncio.Event().wait()
    finally:
        await svc.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Circuit Breaker for LLM Calls")
    parser.add_argument(
        "--mode",
        choices=["demo", "loadtest", "gateway"],
        default=os.environ.get("CB_MODE", "demo"),
    )
    args = parser.parse_args()
    if args.mode == "demo":
        asyncio.run(_run_demo())
    elif args.mode == "loadtest":
        asyncio.run(_run_loadtest())
    else:
        asyncio.run(_run_gateway())


if __name__ == "__main__":
    main()
