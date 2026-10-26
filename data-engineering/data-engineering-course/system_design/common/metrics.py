"""Lightweight in-memory metrics.

Every service exposes a /metrics endpoint that scrapes these. Counters
track request volumes; Histograms track latency. No external deps.
"""

from __future__ import annotations

import time
from collections import defaultdict
from threading import RLock
from typing import Iterable


class Counter:
    def __init__(self, name: str, help_: str = ""):
        self.name = name
        self.help = help_
        self._value = 0
        self._lock = RLock()

    def inc(self, n: int = 1) -> None:
        with self._lock:
            self._value += n

    def value(self) -> int:
        with self._lock:
            return self._value

    def render(self) -> str:
        return f"# HELP {self.name} {self.help}\n# TYPE {self.name} counter\n{self.name} {self._value}\n"


class Histogram:
    """Fixed-bucket histogram. Tracks p50/p95/p99 across requests."""

    _BUCKETS_MS = (1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000)

    def __init__(self, name: str, help_: str = ""):
        self.name = name
        self.help = help_
        self._samples: list[float] = []
        self._count = 0
        self._lock = RLock()

    def observe_ms(self, ms: float) -> None:
        with self._lock:
            self._samples.append(ms)
            self._count += 1
            # Keep last 10k samples — bounded memory.
            if len(self._samples) > 10_000:
                self._samples = self._samples[-10_000:]

    def count(self) -> int:
        with self._lock:
            return self._count

    def quantile(self, q: float) -> float:
        with self._lock:
            if not self._samples:
                return 0.0
            s = sorted(self._samples)
            idx = max(0, min(len(s) - 1, int(q * (len(s) - 1))))
            return s[idx]

    def render(self) -> str:
        with self._lock:
            lines = [
                f"# HELP {self.name} {self.help}",
                f"# TYPE {self.name} summary",
                f"{self.name}_count {self._count}",
                f"{self.name}_p50 {self.quantile(0.50):.2f}",
                f"{self.name}_p95 {self.quantile(0.95):.2f}",
                f"{self.name}_p99 {self.quantile(0.99):.2f}",
            ]
        return "\n".join(lines) + "\n"


class MetricsRegistry:
    """A bag of named metrics. Every service has exactly one of these."""

    def __init__(self):
        self._counters: dict[str, Counter] = {}
        self._histograms: dict[str, Histogram] = {}
        self._lock = RLock()

    def counter(self, name: str, help_: str = "") -> Counter:
        with self._lock:
            if name not in self._counters:
                self._counters[name] = Counter(name, help_)
            return self._counters[name]

    def histogram(self, name: str, help_: str = "") -> Histogram:
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = Histogram(name, help_)
            return self._histograms[name]

    def render(self) -> str:
        chunks: list[str] = []
        for c in self._counters.values():
            chunks.append(c.render())
        for h in self._histograms.values():
            chunks.append(h.render())
        return "\n".join(chunks)


def time_ms(fn):
    """Decorator: time a function in ms and record into a histogram.

    The decorated function should accept ``metrics`` as a kwarg, or the
    histogram is found by name on a global registry passed in via
    ``metrics_hist`` kwarg.
    """
    from functools import wraps

    @wraps(fn)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return fn(*args, **kwargs)
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            metrics = kwargs.get("metrics")
            hist = kwargs.get("metrics_hist")
            if metrics is not None and hist is not None:
                metrics.histogram(hist).observe_ms(elapsed_ms)

    return wrapper
