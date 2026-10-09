"""SLA tracker: success rate and p95 duration over a sliding window.

The course provides a tiny in-memory SLA tracker. Each call
to ``record_job`` adds a sample; ``success_rate`` and
``p95_duration`` compute the metric over the last N
minutes.

In production this is a Prometheus / DataDog / CloudWatch
metric; the interface is the same.

Author: Prem Vishnoi <prem.vishnoi@example.com>
"""

from __future__ import annotations

import bisect
import time
from collections import defaultdict, deque
from typing import Deque, Dict, List, Tuple


class _Sample:
    __slots__ = ("ts", "duration_ms", "success")

    def __init__(self, ts: float, duration_ms: float, success: bool) -> None:
        self.ts = ts
        self.duration_ms = duration_ms
        self.success = success


class SLATracker:
    """Track per-job success and duration over a sliding window.

    Usage::

        tracker = SLATracker(window_minutes=60)
        tracker.record_job("daily_orders", duration_ms=45_000, success=True)
        print(tracker.success_rate("daily_orders"))
        print(tracker.p95_duration("daily_orders"))
    """

    def __init__(self, window_minutes: int = 60) -> None:
        if window_minutes < 1:
            raise ValueError("window_minutes must be >= 1")
        self.window_seconds = window_minutes * 60
        self._samples: Dict[str, Deque[_Sample]] = defaultdict(deque)

    def record_job(
        self, name: str, duration_ms: float, success: bool
    ) -> None:
        """Record a job run. Negative duration is rejected."""
        if duration_ms < 0:
            raise ValueError("duration_ms must be >= 0")
        s = _Sample(time.time(), duration_ms, success)
        self._samples[name].append(s)
        # Evict samples older than the window. We don't pop the
        # left in a tight loop; once per call is fine for a
        # teaching implementation.
        cutoff = time.time() - self.window_seconds
        dq = self._samples[name]
        while dq and dq[0].ts < cutoff:
            dq.popleft()

    def _in_window(self, name: str) -> List[_Sample]:
        cutoff = time.time() - self.window_seconds
        dq = self._samples[name]
        # Evict stale again at query time.
        while dq and dq[0].ts < cutoff:
            dq.popleft()
        return list(dq)

    def success_rate(self, name: str, window_minutes: int = 60) -> float:
        """Return the success rate in [0.0, 1.0] over the last
        ``window_minutes``. ``0.0`` if no samples.
        """
        samples = self._recent(name, window_minutes)
        if not samples:
            return 0.0
        n_success = sum(1 for s in samples if s.success)
        return n_success / len(samples)

    def p95_duration(self, name: str, window_minutes: int = 60) -> float:
        """Return the p95 duration in ms over the last
        ``window_minutes``. ``0.0`` if no samples.
        """
        samples = self._recent(name, window_minutes)
        if not samples:
            return 0.0
        durations = sorted(s.duration_ms for s in samples)
        # 95th percentile by nearest-rank.
        idx = max(0, int(round(0.95 * (len(durations) - 1))))
        return durations[idx]

    def p50_duration(self, name: str, window_minutes: int = 60) -> float:
        samples = self._recent(name, window_minutes)
        if not samples:
            return 0.0
        durations = sorted(s.duration_ms for s in samples)
        idx = max(0, int(round(0.50 * (len(durations) - 1))))
        return durations[idx]

    def n_samples(self, name: str, window_minutes: int = 60) -> int:
        return len(self._recent(name, window_minutes))

    def _recent(self, name: str, window_minutes: int) -> List[_Sample]:
        # Override the default window for this query.
        cutoff = time.time() - window_minutes * 60
        dq = self._samples[name]
        return [s for s in dq if s.ts >= cutoff]
