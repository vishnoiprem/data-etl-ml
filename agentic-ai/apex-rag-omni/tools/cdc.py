"""Flink CDC pipeline: Postgres WAL -> Kafka -> indexer.

5-min end-to-end freshness SLA. The CDC pipeline tails the Postgres WAL
via Debezium, publishes to Kafka, and the indexer consumes + writes to
both Qdrant (vectors) and Elasticsearch (BM25) + Postgres (metadata).
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

logger = logging.getLogger(__name__)


@dataclass
class CDCEvent:
    """A single CDC event from the WAL."""
    doc_id: str
    table: str
    op: str  # INSERT, UPDATE, DELETE
    ts: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    payload: dict = field(default_factory=dict)


@dataclass
class FreshnessStats:
    """End-to-end freshness stats over a window."""
    sla_minutes: int = 5
    sample_size: int = 0
    p50_lag_seconds: float = 0.0
    p95_lag_seconds: float = 0.0
    p99_lag_seconds: float = 0.0
    sla_violations: int = 0


def freshness_report(samples: list[tuple[datetime, datetime]]) -> FreshnessStats:
    """Compute freshness stats from (indexed_at, source_ts) pairs.

    Lag = indexed_at - source_ts. SLA is 5 min P95.
    """
    if not samples:
        return FreshnessStats()
    lags = sorted((i - s).total_seconds() for s, i in samples)
    n = len(lags)
    p50 = lags[int(0.50 * (n - 1))]
    p95 = lags[int(0.95 * (n - 1))]
    p99 = lags[int(0.99 * (n - 1))]
    violations = sum(1 for l in lags if l > 300)
    return FreshnessStats(
        sla_minutes=5, sample_size=n, p50_lag_seconds=p50,
        p95_lag_seconds=p95, p99_lag_seconds=p99, sla_violations=violations,
    )


def cdc_loop(wal_source: Callable[[], CDCEvent | None],
             kafka_publish: Callable[[CDCEvent], None],
             indexer: Callable[[CDCEvent], None],
             stop_after: int | None = None) -> FreshnessStats:
    """The CDC event loop. Tails the WAL, publishes to Kafka, runs the indexer."""
    samples: list[tuple[datetime, datetime]] = []
    n = 0
    while True:
        if stop_after is not None and n >= stop_after:
            break
        ev = wal_source()
        if ev is None:
            time.sleep(0.01)
            continue
        indexed_at = datetime.now(timezone.utc)
        kafka_publish(ev)
        indexer(ev)
        samples.append((ev.ts, indexed_at))
        n += 1
    return freshness_report(samples)
