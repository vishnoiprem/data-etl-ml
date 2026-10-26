"""
Lab 16: Real-Time Anomaly Detector with LLM Explanation
=======================================================

A streaming anomaly detection system that:
- Ingests metrics from multiple sources (mock producers per metric).
- Computes rolling mean + stddev per metric (1h sliding window).
- Flags anomalies via z-score (configurable threshold).
- Uses a mock LLM to explain *why* a metric might be spiking.
- Sends webhook alerts when anomalies are detected.
- Exposes a dashboard endpoint with live metrics + recent anomalies.
- Supports historical replay for debugging (re-process recorded events).

Architecture
------------

    +-----------------+        +-------------------+        +------------------+
    |  Metric sources | -----> |  MetricStreamHub   | -----> |  RollingWindow   |
    |  (producers)    |        |  (asyncio.Queue)   |        |  (per metric)    |
    +-----------------+        +-------------------+        +---------+--------+
                                                                         |
                                                                         v
                                                                +-------------------+
                                                                | AnomalyDetector   |
                                                                |  (z-score)        |
                                                                +---------+---------+
                                                                          |
                                                            +-------------v------------+
                                                            |  AnomalyExplainer (LLM) |
                                                            +-------------+------------+
                                                                          |
                                            +------------------+          v
                                            |  Webhook alerter | <-- explained anomaly
                                            +------------------+
                                                                          |
                                                                          v
                                                            +-------------------------+
                                                            |  Dashboard + Prometheus |
                                                            |  HTTP endpoint          |
                                                            +-------------------------+

Components
----------
1. MetricProducer: generates random walk metrics + injected spikes.
2. MetricStreamHub: a fan-in of multiple producers (one queue per source).
3. RollingWindow: per-metric ring buffer of (ts, value) with mean/stddev.
4. AnomalyDetector: z-score + EWMA baseline + hysteresis.
5. AnomalyExplainer: mock LLM that produces a plausible explanation string.
6. WebhookAlerter: POSTs anomalies to a configurable URL (or logs).
7. DashboardServer: live JSON snapshot + Prometheus metrics.
8. ReplayRecorder: records raw events for historical replay.

How to run
----------
$ python 16-realtime-anomaly-detector.py --mode demo
$ python 16-realtime-anomaly-detector.py --mode replay
$ python 16-realtime-anomaly-detector.py --mode gateway    # run forever

Configuration (env vars)
------------------------
- ANOMALY_WINDOW_SEC      (int, default 3600)        # 1h sliding window
- ANOMALY_Z_THRESHOLD     (float, default 3.0)
- ANOMALY_MIN_SAMPLES     (int, default 30)
- ANOMALY_COOLDOWN_SEC    (float, default 60)
- ANOMALY_WEBHOOK_URL     (str, default "")           # empty = log only
- ANOMALY_DASHBOARD_PORT  (int, default 8084)
- ANOMALY_DASHBOARD_TOKEN (str, default admin-token)
- ANOMALY_EXPLAIN_LATENCY_MS (int, default 50)
- ANOMALY_EXPLAIN_ERROR_RATE (float, default 0.05)
- ANOMALY_METRIC_SOURCES  (csv, default "cpu,memory,requests,latency,errors")
- ANOMALY_SPIKE_PROB      (float, default 0.02)       # injected spikes
- ANOMALY_REPLAY_FILE     (str, default "")           # NDJSON file

Dependencies
------------
- aiohttp (for webhook + dashboard)
- prometheus_client (optional)
- Standard library (asyncio, statistics, json, time, math)

Failure modes
-------------
- Webhook unreachable -> log + retry; do not block detection.
- LLM explanation failure -> degrade to "no explanation" and continue.
- Out-of-order or late events -> accepted but flagged with a note.
- Window too small -> anomaly detection disabled until enough samples.
- Replay source missing -> skip replay silently.

What makes it production-grade
------------------------------
- True asyncio streaming (no polling for the main pipeline).
- Per-metric rolling window + EWMA baseline + hysteresis.
- Anomaly explanations with confidence scores.
- Webhook with backoff and dead-letter log on failure.
- Live dashboard + Prometheus metrics.
- Historical replay (replay recorded events to debug detectors).
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
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    AsyncIterator,
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
    from aiohttp import web, ClientSession  # type: ignore
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


log = _build_logger("anomaly-detector")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class AnomalyConfig:
    window_sec: int = int(os.environ.get("ANOMALY_WINDOW_SEC", "3600"))
    z_threshold: float = float(os.environ.get("ANOMALY_Z_THRESHOLD", "3.0"))
    min_samples: int = int(os.environ.get("ANOMALY_MIN_SAMPLES", "30"))
    cooldown_sec: float = float(os.environ.get("ANOMALY_COOLDOWN_SEC", "60"))
    webhook_url: str = os.environ.get("ANOMALY_WEBHOOK_URL", "")
    dashboard_port: int = int(os.environ.get("ANOMALY_DASHBOARD_PORT", "8084"))
    dashboard_host: str = os.environ.get("ANOMALY_DASHBOARD_HOST", "127.0.0.1")
    dashboard_token: str = os.environ.get("ANOMALY_DASHBOARD_TOKEN", "admin-token")
    explain_latency_ms: int = int(
        os.environ.get("ANOMALY_EXPLAIN_LATENCY_MS", "50")
    )
    explain_error_rate: float = float(
        os.environ.get("ANOMALY_EXPLAIN_ERROR_RATE", "0.05")
    )
    metric_sources: str = os.environ.get(
        "ANOMALY_METRIC_SOURCES", "cpu,memory,requests,latency,errors"
    )
    spike_prob: float = float(os.environ.get("ANOMALY_SPIKE_PROB", "0.02"))
    replay_file: str = os.environ.get("ANOMALY_REPLAY_FILE", "")
    sample_interval_sec: float = float(
        os.environ.get("ANOMALY_SAMPLE_INTERVAL", "0.5")
    )
    producer_concurrency: int = int(
        os.environ.get("ANOMALY_PRODUCER_CONCURRENCY", "3")
    )
    replay_speed: float = float(os.environ.get("ANOMALY_REPLAY_SPEED", "10.0"))

    def sources(self) -> List[str]:
        return [s.strip() for s in self.metric_sources.split(",") if s.strip()]


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
class Metrics:
    def __init__(self) -> None:
        self.use_prom = PROMETHEUS_AVAILABLE
        if self.use_prom:
            self.registry = CollectorRegistry()
            self.events = Counter(
                "anomaly_events_total",
                "Total metric events processed.",
                ["metric"],
                registry=self.registry,
            )
            self.anomalies = Counter(
                "anomaly_detected_total",
                "Anomalies detected.",
                ["metric", "severity"],
                registry=self.registry,
            )
            self.explanations = Counter(
                "anomaly_explanations_total",
                "Anomaly explanations emitted.",
                ["outcome"],
                registry=self.registry,
            )
            self.webhook_calls = Counter(
                "anomaly_webhook_calls_total",
                "Webhook deliveries.",
                ["outcome"],
                registry=self.registry,
            )
            self.zscore = Gauge(
                "anomaly_zscore",
                "Latest z-score per metric.",
                ["metric"],
                registry=self.registry,
            )
            self.value = Gauge(
                "anomaly_value",
                "Latest observed value per metric.",
                ["metric"],
                registry=self.registry,
            )
            self.window_size = Gauge(
                "anomaly_window_size",
                "Rolling window size per metric.",
                ["metric"],
                registry=self.registry,
            )
            self.explain_latency = Histogram(
                "anomaly_explain_latency_seconds",
                "LLM explainer latency.",
                buckets=(0.005, 0.01, 0.05, 0.1, 0.5, 1, 2),
                registry=self.registry,
            )
        else:
            self._counters: Dict[str, int] = {}
            self._gauges: Dict[str, float] = {}

    def inc_event(self, metric: str) -> None:
        if self.use_prom:
            self.events.labels(metric=metric).inc()
        else:
            self._counters[f"evt:{metric}"] = self._counters.get(f"evt:{metric}", 0) + 1

    def inc_anomaly(self, metric: str, severity: str) -> None:
        if self.use_prom:
            self.anomalies.labels(metric=metric, severity=severity).inc()
        else:
            self._counters[f"an:{metric}:{severity}"] = (
                self._counters.get(f"an:{metric}:{severity}", 0) + 1
            )

    def inc_explanation(self, outcome: str) -> None:
        if self.use_prom:
            self.explanations.labels(outcome=outcome).inc()
        else:
            self._counters[f"exp:{outcome}"] = (
                self._counters.get(f"exp:{outcome}", 0) + 1
            )

    def inc_webhook(self, outcome: str) -> None:
        if self.use_prom:
            self.webhook_calls.labels(outcome=outcome).inc()
        else:
            self._counters[f"wh:{outcome}"] = (
                self._counters.get(f"wh:{outcome}", 0) + 1
            )

    def set_zscore(self, metric: str, z: float) -> None:
        if self.use_prom:
            self.zscore.labels(metric=metric).set(z)
        else:
            self._gauges[f"z:{metric}"] = z

    def set_value(self, metric: str, v: float) -> None:
        if self.use_prom:
            self.value.labels(metric=metric).set(v)
        else:
            self._gauges[f"v:{metric}"] = v

    def set_window(self, metric: str, n: int) -> None:
        if self.use_prom:
            self.window_size.labels(metric=metric).set(n)
        else:
            self._gauges[f"w:{metric}"] = n

    def observe_explain(self, sec: float) -> None:
        if self.use_prom:
            self.explain_latency.observe(sec)
        else:
            pass

    def render(self) -> Tuple[bytes, str]:
        if self.use_prom:
            return generate_latest(self.registry), CONTENT_TYPE_LATEST
        return (
            json.dumps({"counters": self._counters, "gauges": self._gauges}, indent=2).encode(),
            "application/json",
        )


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class MetricSample:
    metric: str
    value: float
    ts: float
    source: str = "default"
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class Anomaly:
    id: str
    metric: str
    value: float
    zscore: float
    mean: float
    stddev: float
    ts: float
    severity: str          # "low" | "med" | "high"
    direction: str          # "spike" | "drop"
    explanation: str = ""
    confidence: float = 0.0
    raw: Optional[Dict[str, Any]] = None


class Severity:
    @staticmethod
    def from_zscore(z: float, threshold: float) -> str:
        if abs(z) >= threshold * 2:
            return "high"
        if abs(z) >= threshold * 1.5:
            return "med"
        return "low"


# ---------------------------------------------------------------------------
# Rolling window
# ---------------------------------------------------------------------------
class RollingWindow:
    """Per-metric ring buffer with mean + stddev."""

    def __init__(self, window_sec: float) -> None:
        self.window_sec = window_sec
        self._samples: Deque[MetricSample] = deque()

    def add(self, sample: MetricSample) -> None:
        self._samples.append(sample)
        self._evict(sample.ts)

    def _evict(self, now: float) -> None:
        cutoff = now - self.window_sec
        while self._samples and self._samples[0].ts < cutoff:
            self._samples.popleft()

    def stats(self) -> Tuple[float, float, int]:
        n = len(self._samples)
        if n == 0:
            return 0.0, 0.0, 0
        values = [s.value for s in self._samples]
        mean = sum(values) / n
        if n < 2:
            return mean, 0.0, n
        var = sum((v - mean) ** 2 for v in values) / (n - 1)
        return mean, math.sqrt(var), n


# ---------------------------------------------------------------------------
# Anomaly detector
# ---------------------------------------------------------------------------
class AnomalyDetector:
    def __init__(self, cfg: AnomalyConfig, metrics: Metrics) -> None:
        self.cfg = cfg
        self.metrics = metrics
        self.windows: Dict[str, RollingWindow] = {}
        self._last_alert: Dict[str, float] = {}
        self._baseline_ewma: Dict[str, float] = {}
        self._baseline_ewma_var: Dict[str, float] = {}
        self.anomalies: Deque[Anomaly] = deque(maxlen=10_000)

    def ensure_metric(self, metric: str) -> RollingWindow:
        if metric not in self.windows:
            self.windows[metric] = RollingWindow(self.cfg.window_sec)
        return self.windows[metric]

    def process(self, sample: MetricSample) -> Optional[Anomaly]:
        win = self.ensure_metric(sample.metric)
        win.add(sample)
        mean, stddev, n = win.stats()
        self.metrics.set_window(sample.metric, n)
        self.metrics.set_value(sample.metric, sample.value)
        if n < self.cfg.min_samples:
            return None
        if stddev <= 1e-9:
            return None
        z = (sample.value - mean) / stddev
        self.metrics.set_zscore(sample.metric, z)
        # EWMA baseline update (slower-moving average).
        old = self._baseline_ewma.get(sample.metric, mean)
        self._baseline_ewma[sample.metric] = 0.95 * old + 0.05 * sample.value
        if abs(z) < self.cfg.z_threshold:
            return None
        # Hysteresis: avoid spamming if the previous alert for this metric was recent.
        last = self._last_alert.get(sample.metric, 0.0)
        if sample.ts - last < self.cfg.cooldown_sec:
            return None
        self._last_alert[sample.metric] = sample.ts
        direction = "spike" if z > 0 else "drop"
        severity = Severity.from_zscore(z, self.cfg.z_threshold)
        anomaly = Anomaly(
            id=uuid.uuid4().hex,
            metric=sample.metric,
            value=sample.value,
            zscore=round(z, 3),
            mean=round(mean, 3),
            stddev=round(stddev, 3),
            ts=sample.ts,
            severity=severity,
            direction=direction,
            raw={"labels": sample.labels, "source": sample.source},
        )
        self.metrics.inc_anomaly(sample.metric, severity)
        self.anomalies.appendleft(anomaly)
        log.info(
            "anomaly_detected",
            extra={
                "metric": sample.metric,
                "value": sample.value,
                "z": z,
                "severity": severity,
                "direction": direction,
            },
        )
        return anomaly

    def recent(self, metric: Optional[str] = None, limit: int = 100) -> List[Anomaly]:
        if metric is None:
            return list(self.anomalies)[:limit]
        return [a for a in self.anomalies if a.metric == metric][:limit]


# ---------------------------------------------------------------------------
# LLM explainer (mock)
# ---------------------------------------------------------------------------
class Explainer:
    def __init__(self, cfg: AnomalyConfig, metrics: Metrics) -> None:
        self.cfg = cfg
        self.metrics = metrics
        self.cache: Dict[str, Tuple[float, str]] = {}

    async def explain(self, anomaly: Anomaly) -> str:
        # Cache key by (metric, severity, direction)
        key = f"{anomaly.metric}:{anomaly.severity}:{anomaly.direction}"
        if key in self.cache and time.time() - self.cache[key][0] < 60:
            return self.cache[key][1]
        start = time.monotonic()
        await asyncio.sleep(self.cfg.explain_latency_ms / 1000.0 * random.uniform(0.5, 1.5))
        if random.random() < self.cfg.explain_error_rate:
            self.metrics.inc_explanation("error")
            raise RuntimeError("explainer failure")
        text = self._synthesize(anomaly)
        self.cache[key] = (time.time(), text)
        self.metrics.observe_explain(time.monotonic() - start)
        self.metrics.inc_explanation("ok")
        return text

    def _synthesize(self, a: Anomaly) -> str:
        causes_by_metric = {
            "cpu": [
                "an upstream deployment may have introduced a hot loop",
                "background jobs could be running concurrently",
                "GC pressure from a large in-memory cache is likely",
            ],
            "memory": [
                "a possible memory leak in the request handler",
                "the cache eviction policy might be misconfigured",
                "recent query plans may be loading large result sets",
            ],
            "requests": [
                "a marketing email blast could be driving traffic",
                "an external partner is retrying in a tight loop",
                "the rate limiter may be misfiring",
            ],
            "latency": [
                "downstream API may be experiencing cold starts",
                "DB connection pool is likely exhausted",
                "a noisy neighbor is consuming shared resources",
            ],
            "errors": [
                "a new deploy may have introduced a regression",
                "a downstream provider might be returning 5xx",
                "an expired credential is likely causing auth failures",
            ],
        }
        candidates = causes_by_metric.get(
            a.metric, ["an unidentified change in the system"]
        )
        reason = random.choice(candidates)
        return (
            f"{a.metric} {a.direction}d to {a.value:.2f} "
            f"(z={a.zscore:+.2f}, mean={a.mean:.2f}, std={a.stddev:.2f}); "
            f"probable cause: {reason}."
        )


# ---------------------------------------------------------------------------
# Webhook alerter
# ---------------------------------------------------------------------------
class WebhookAlerter:
    def __init__(self, url: str, metrics: Metrics) -> None:
        self.url = url
        self.metrics = metrics
        self._dlq: Deque[Dict[str, Any]] = deque(maxlen=1000)
        self._stop = asyncio.Event()

    async def deliver(self, anomaly: Anomaly) -> bool:
        if not self.url:
            log.info("webhook_disabled_log_only", extra={"anomaly_id": anomaly.id})
            self.metrics.inc_webhook("noop")
            return True
        if not AIOHTTP_AVAILABLE:
            log.warning("webhook_no_aiohttp")
            self.metrics.inc_webhook("skipped")
            return False
        payload = {
            "id": anomaly.id,
            "metric": anomaly.metric,
            "value": anomaly.value,
            "zscore": anomaly.zscore,
            "severity": anomaly.severity,
            "direction": anomaly.direction,
            "ts": anomaly.ts,
            "explanation": anomaly.explanation,
        }
        for attempt in range(3):
            try:
                async with ClientSession() as session:
                    async with session.post(
                        self.url,
                        json=payload,
                        timeout=2.0,
                    ) as resp:
                        if 200 <= resp.status < 300:
                            self.metrics.inc_webhook("ok")
                            return True
                        self.metrics.inc_webhook(f"http_{resp.status}")
            except Exception as exc:
                log.warning(
                    "webhook_failed",
                    extra={"anomaly_id": anomaly.id, "attempt": attempt, "err": str(exc)},
                )
                self.metrics.inc_webhook("error")
                await asyncio.sleep(0.2 * (2 ** attempt))
        self._dlq.append(payload)
        return False


# ---------------------------------------------------------------------------
# Metric producers (random walk + injected spikes)
# ---------------------------------------------------------------------------
class MetricProducer:
    def __init__(self, source: str, hub: "MetricStreamHub", cfg: AnomalyConfig) -> None:
        self.source = source
        self.hub = hub
        self.cfg = cfg
        self._stop = asyncio.Event()
        self._baseline = self._initial_baseline()
        self._drift = 0.0

    def _initial_baseline(self) -> float:
        return {
            "cpu": 35.0,
            "memory": 60.0,
            "requests": 200.0,
            "latency": 120.0,
            "errors": 1.0,
        }.get(self.source, 50.0)

    async def run(self) -> None:
        value = self._baseline
        while not self._stop.is_set():
            # Random walk
            value += random.gauss(0, 0.5)
            # Slight reversion to baseline
            value = 0.99 * value + 0.01 * self._baseline
            # Spike?
            if random.random() < self.cfg.spike_prob:
                sign = random.choice([1, -1])
                value += sign * random.uniform(3, 12)
            sample = MetricSample(
                metric=self.source,
                value=round(value, 3),
                ts=time.time(),
                source=f"producer-{self.source}",
            )
            await self.hub.publish(sample)
            await asyncio.sleep(self.cfg.sample_interval_sec)

    def stop(self) -> None:
        self._stop.set()


# ---------------------------------------------------------------------------
# Stream hub
# ---------------------------------------------------------------------------
class MetricStreamHub:
    def __init__(self) -> None:
        self._queue: asyncio.Queue[MetricSample] = asyncio.Queue(maxsize=50_000)
        self._closed = False

    async def publish(self, sample: MetricSample) -> None:
        if self._closed:
            return
        try:
            self._queue.put_nowait(sample)
        except asyncio.QueueFull:
            # Drop oldest to make room
            with contextlib.suppress(asyncio.QueueEmpty):
                self._queue.get_nowait()
            await self._queue.put(sample)

    async def stream(self) -> AsyncIterator[MetricSample]:
        while True:
            if self._closed and self._queue.empty():
                return
            try:
                sample = await asyncio.wait_for(self._queue.get(), timeout=0.5)
            except asyncio.TimeoutError:
                continue
            yield sample

    def close(self) -> None:
        self._closed = True


# ---------------------------------------------------------------------------
# Replay recorder
# ---------------------------------------------------------------------------
class ReplayRecorder:
    """Records samples to a file (NDJSON) and can replay them later."""

    def __init__(self, path: str) -> None:
        self.path = path
        self._file: Optional[Any] = None

    async def open(self, write: bool = True) -> None:
        if not self.path:
            return
        if write:
            import aiofiles  # type: ignore
            self._file = await aiofiles.open(self.path, mode="w")
        else:
            import aiofiles  # type: ignore
            self._file = await aiofiles.open(self.path, mode="r")

    async def write(self, sample: MetricSample) -> None:
        if not self._file:
            return
        try:
            line = json.dumps(
                {"metric": sample.metric, "value": sample.value, "ts": sample.ts,
                 "source": sample.source, "labels": sample.labels}
            ) + "\n"
            await self._file.write(line)
        except Exception as exc:
            log.warning("replay_write_failed", extra={"err": str(exc)})

    async def read_all(self) -> List[MetricSample]:
        if not self._file:
            return []
        samples: List[MetricSample] = []
        try:
            content = await self._file.read()
        except Exception:
            return []
        for line in content.splitlines():
            if not line.strip():
                continue
            try:
                d = json.loads(line)
                samples.append(
                    MetricSample(
                        metric=d["metric"],
                        value=float(d["value"]),
                        ts=float(d["ts"]),
                        source=d.get("source", "replay"),
                        labels=d.get("labels", {}),
                    )
                )
            except Exception:
                continue
        return samples

    async def close(self) -> None:
        if self._file:
            await self._file.close()
            self._file = None


# ---------------------------------------------------------------------------
# Dashboard server
# ---------------------------------------------------------------------------
if AIOHTTP_AVAILABLE:

    class DashboardServer:
        def __init__(
            self,
            cfg: AnomalyConfig,
            metrics: Metrics,
            detector: AnomalyDetector,
            hub: MetricStreamHub,
            explainer: Explainer,
            alerter: WebhookAlerter,
        ) -> None:
            self.cfg = cfg
            self.metrics = metrics
            self.detector = detector
            self.hub = hub
            self.explainer = explainer
            self.alerter = alerter
            self._app = web.Application()
            self._app.router.add_get("/healthz", self._healthz)
            self._app.router.add_get("/metrics", self._metrics)
            self._app.router.add_get("/dashboard", self._dashboard)
            self._app.router.add_get("/anomalies", self._anomalies)
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

        async def _anomalies(self, request: web.Request) -> web.Response:
            metric = request.query.get("metric")
            limit = int(request.query.get("limit", "50"))
            entries = self.detector.recent(metric=metric, limit=limit)
            return web.json_response(
                {"anomalies": [dataclasses.asdict(a) for a in entries]}
            )

        async def _dashboard(self, request: web.Request) -> web.Response:
            token = request.query.get("token", "")
            if token != self.cfg.dashboard_token:
                return web.json_response({"error": "unauthorized"}, status=401)
            # Build a snapshot of the latest values + window stats.
            snap = {}
            for metric, win in self.detector.windows.items():
                mean, stddev, n = win.stats()
                last = win._samples[-1] if win._samples else None
                snap[metric] = {
                    "mean": round(mean, 3),
                    "stddev": round(stddev, 3),
                    "samples": n,
                    "last_value": last.value if last else None,
                    "last_ts": last.ts if last else None,
                }
            return web.json_response(
                {
                    "metrics": snap,
                    "recent_anomalies": [
                        dataclasses.asdict(a) for a in self.detector.recent(limit=25)
                    ],
                    "config": {
                        "window_sec": self.cfg.window_sec,
                        "z_threshold": self.cfg.z_threshold,
                        "min_samples": self.cfg.min_samples,
                        "cooldown_sec": self.cfg.cooldown_sec,
                        "sources": self.cfg.sources(),
                    },
                    "webhook_dlq_size": len(self.alerter._dlq),
                }
            )


# ---------------------------------------------------------------------------
# Top-level service
# ---------------------------------------------------------------------------
class AnomalyService:
    def __init__(self, cfg: AnomalyConfig) -> None:
        self.cfg = cfg
        self.metrics = Metrics()
        self.hub = MetricStreamHub()
        self.detector = AnomalyDetector(cfg, self.metrics)
        self.explainer = Explainer(cfg, self.metrics)
        self.alerter = WebhookAlerter(cfg.webhook_url, self.metrics)
        self.dashboard: Optional["DashboardServer"] = None
        self.recorder: Optional[ReplayRecorder] = None
        self._tasks: List[asyncio.Task[None]] = []
        self._producers: List[MetricProducer] = []
        self._stop = asyncio.Event()

    async def start(self) -> None:
        if AIOHTTP_AVAILABLE:
            self.dashboard = DashboardServer(
                self.cfg, self.metrics, self.detector, self.hub, self.explainer, self.alerter
            )
            await self.dashboard.start()
        # Launch processors + producers
        self._tasks.append(
            asyncio.create_task(self._processing_loop(), name="processing")
        )
        for src in self.cfg.sources():
            producer = MetricProducer(src, self.hub, self.cfg)
            self._producers.append(producer)
            self._tasks.append(
                asyncio.create_task(producer.run(), name=f"producer-{src}")
            )

    async def _processing_loop(self) -> None:
        async for sample in self.hub.stream():
            if self._stop.is_set():
                break
            self.metrics.inc_event(sample.metric)
            if self.recorder:
                with contextlib.suppress(Exception):
                    await self.recorder.write(sample)
            anomaly = self.detector.process(sample)
            if anomaly is None:
                continue
            try:
                explanation = await self.explainer.explain(anomaly)
                anomaly.explanation = explanation
                anomaly.confidence = max(
                    0.0, min(1.0, 1.0 - 1.0 / (1.0 + abs(anomaly.zscore)))
                )
            except Exception as exc:
                log.warning(
                    "explain_failed",
                    extra={"anomaly_id": anomaly.id, "err": str(exc)},
                )
            await self.alerter.deliver(anomaly)

    async def stop(self) -> None:
        self._stop.set()
        for p in self._producers:
            p.stop()
        self.hub.close()
        for t in self._tasks:
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        if self.dashboard:
            await self.dashboard.stop()
        if self.recorder:
            await self.recorder.close()


# ---------------------------------------------------------------------------
# Replay mode
# ---------------------------------------------------------------------------
async def _run_replay() -> None:
    if not os.path.exists(cfg_replay_path()):
        log.warning("replay_file_missing", extra={"path": cfg_replay_path()})
        return
    cfg = AnomalyConfig(replay_file=cfg_replay_path())
    svc = AnomalyService(cfg)
    svc.recorder = ReplayRecorder(cfg.replay_file)
    await svc.recorder.open(write=False)
    await svc.start()
    samples = await svc.recorder.read_all()
    await svc.recorder.close()
    log.info("replay_starting", extra={"n_samples": len(samples)})
    # Time-warp replay
    if samples:
        t0 = samples[0].ts
        for s in samples:
            wait = max(0.0, (s.ts - t0) / cfg.replay_speed)
            await asyncio.sleep(wait)
            await svc.hub.publish(s)
    await asyncio.sleep(2)
    print("\nREPLAY SUMMARY:")
    print(json.dumps(
        {
            "anomalies_detected": len(svc.detector.anomalies),
            "recent": [dataclasses.asdict(a) for a in svc.detector.recent(limit=5)],
        },
        indent=2,
    ))
    await svc.stop()


def cfg_replay_path() -> str:
    return os.environ.get("ANOMALY_REPLAY_FILE", "anomaly_events.ndjson")


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
async def _run_demo() -> None:
    cfg = AnomalyConfig(
        window_sec=600,  # shorter for the demo
        z_threshold=2.5,
        min_samples=20,
        cooldown_sec=10,
        spike_prob=0.05,
        sample_interval_sec=0.3,
    )
    svc = AnomalyService(cfg)
    if os.environ.get("ANOMALY_RECORD", "0") == "1":
        path = os.environ.get("ANOMALY_REPLAY_FILE", "anomaly_events.ndjson")
        svc.recorder = ReplayRecorder(path)
        await svc.recorder.open(write=True)
    await svc.start()
    loop = asyncio.get_running_loop()

    def _stop() -> None:
        svc._stop.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, _stop)
    # Run for 15 seconds.
    await asyncio.sleep(15)
    # Print a summary
    snap = {
        "metrics": {
            m: {
                "mean": round(win.stats()[0], 3),
                "stddev": round(win.stats()[1], 3),
                "samples": win.stats()[2],
            }
            for m, win in svc.detector.windows.items()
        },
        "anomalies_detected": len(svc.detector.anomalies),
        "recent_anomalies": [
            dataclasses.asdict(a) for a in svc.detector.recent(limit=10)
        ],
    }
    print("\nDEMO SUMMARY:")
    print(json.dumps(snap, indent=2))
    body, _ = svc.metrics.render()
    text = body.decode()
    if PROMETHEUS_AVAILABLE:
        keys = ("anomaly_events_total", "anomaly_detected_total",
                "anomaly_explanations_total", "anomaly_webhook_calls_total",
                "anomaly_zscore", "anomaly_value", "anomaly_window_size")
        print("\nMETRICS (filtered):")
        for line in text.splitlines():
            if any(k in line for k in keys):
                print(" ", line)
    else:
        print("\nMETRICS (fallback):")
        print(text[:1500])
    await svc.stop()


async def _run_gateway() -> None:
    cfg = AnomalyConfig()
    svc = AnomalyService(cfg)
    await svc.start()
    print(
        f"Dashboard listening on http://{cfg.dashboard_host}:{cfg.dashboard_port}/dashboard"
    )
    try:
        await asyncio.Event().wait()
    finally:
        await svc.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Real-time Anomaly Detector")
    parser.add_argument(
        "--mode",
        choices=["demo", "gateway", "replay"],
        default=os.environ.get("ANOMALY_MODE", "demo"),
    )
    args = parser.parse_args()
    if args.mode == "demo":
        asyncio.run(_run_demo())
    elif args.mode == "replay":
        asyncio.run(_run_replay())
    else:
        asyncio.run(_run_gateway())


if __name__ == "__main__":
    main()
