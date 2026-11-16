"""
SCB AML Platform — Realtime Kafka Consumer
===========================================

Consumes wire-transfer events from `scb.wire_transfers.raw` and applies
a focused, **sub-second** AML rule set against a rolling 5-minute window.
Output: realtime alerts appended to `output/alerts/realtime_alerts.parquet`
and optionally published to `scb.realtime.alerts`.

Why a separate realtime path:
  The batch pipeline (Sqoop → Spark → Rules) runs T+1, taking ~5 hours.
  High-risk wire transfers need a "stop-and-hold" decision in <1s while
  the payment is still in-flight. This consumer:
    1. Maintains an in-memory rolling window of recent wires per customer
    2. Applies 4 realtime rules (CTR, velocity, high-risk dest, structuring)
    3. Auto-blocks wires scoring >= REALTIME_BLOCK_SCORE
    4. Emits alerts to disk + Kafka for downstream SLAs

In production: Kafka Streams or Apache Flink (Flink SQL) with the same rules.
Here: kafka-python consumer + a tiny in-memory state store, so it runs on
a fresh checkout without a Kafka broker (falls back to file-simulation mode).
"""

import sys
import json
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from scb_aml_platform.config.settings import (
    BASE_DIR, KAFKA_BOOTSTRAP, KAFKA_TOPIC_WIRE,
    KAFKA_TOPIC_REALTIME_ALERTS, KAFKA_CONSUMER_GROUP,
    REALTIME_WINDOW_SECONDS, REALTIME_VELOCITY_THRESHOLD,
    REALTIME_CTR_THRESHOLD_USD, REALTIME_HIGH_RISK_DEST,
)
from scb_aml_platform.ingestion.kafka_producer import _get_producer, MockProducer  # noqa: E402

OUTPUT_DIR = Path(BASE_DIR) / "output" / "alerts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REALTIME_PATH = OUTPUT_DIR / "realtime_alerts.parquet"


# ─────────────────────────────────────────────
# STATE STORE
# ─────────────────────────────────────────────
class RollingWindow:
    """Per-customer rolling window of recent wire events.

    A deque per customer_id holding (timestamp, amount_usd, receiver_country).
    Eviction is O(N) worst case (one sweep on each insert) which is fine
    for the synthetic data scale (~500 customers).
    """

    def __init__(self, window_seconds: int = REALTIME_WINDOW_SECONDS):
        self.window = timedelta(seconds=window_seconds)
        self._store: dict[str, deque] = defaultdict(deque)

    def record(self, customer_id: str, ts: datetime, amount: float, country: str):
        dq = self._store[customer_id]
        dq.append((ts, amount, country))
        self._evict(dq, ts)

    def recent(self, customer_id: str) -> list[tuple]:
        return list(self._store[customer_id])

    def count_recent(self, customer_id: str, ts: datetime) -> int:
        self._evict(self._store[customer_id], ts)
        return len(self._store[customer_id])

    def total_recent(self, customer_id: str, ts: datetime) -> float:
        self._evict(self._store[customer_id], ts)
        return sum(amt for _, amt, _ in self._store[customer_id])

    def _evict(self, dq: deque, ts: datetime):
        cutoff = ts - self.window
        while dq and dq[0][0] < cutoff:
            dq.popleft()


# ─────────────────────────────────────────────
# REALTIME RULES
# ─────────────────────────────────────────────
def _score(event: dict, window: RollingWindow) -> tuple[list[str], int]:
    """Apply realtime rules to a single event.

    Returns (triggered_rule_ids, alert_score).
    """
    rules = []
    score = 0
    cust = event.get("sender_customer_id") or event.get("customer_id", "UNKNOWN")
    amt = float(event.get("amount_usd", 0))
    rcv = event.get("receiver_country", "")
    ts = datetime.fromisoformat(event["event_time"].replace("Z", "+00:00")) \
        if isinstance(event.get("event_time"), str) else datetime.utcnow()

    # RR01: Single wire ≥ CTR threshold
    if amt >= REALTIME_CTR_THRESHOLD_USD:
        rules.append("RR01")
        score = max(score, 60)

    # RR02: High-risk destination
    if rcv in REALTIME_HIGH_RISK_DEST:
        rules.append("RR02")
        score = max(score, 70)

    # RR03: Velocity — ≥ N wires in the rolling window
    window.record(cust, ts, amt, rcv)
    n = window.count_recent(cust, ts)
    if n >= REALTIME_VELOCITY_THRESHOLD:
        rules.append("RR03")
        score = max(score, 65)

    # RR04: Structuring (3+ wires 85–100% of CTR in window)
    suspect = [a for _, a, _ in window.recent(cust)
               if REALTIME_CTR_THRESHOLD_USD * 0.85 <= a < REALTIME_CTR_THRESHOLD_USD]
    if len(suspect) >= 3:
        rules.append("RR04")
        score = max(score, 80)

    return rules, score


def _build_alert(event: dict, rules: list[str], score: int) -> dict:
    return {
        "alert_id": f"RT_{event.get('wire_id', '?')}_{int(time.time()*1000)}",
        "rule_ids": "+".join(rules),
        "customer_id": event.get("sender_customer_id") or event.get("customer_id", "UNKNOWN"),
        "amount_usd": float(event.get("amount_usd", 0)),
        "receiver_country": event.get("receiver_country", ""),
        "alert_score": score,
        "action": "BLOCK" if score >= 80 else "REVIEW",
        "event_time": event.get("event_time", datetime.utcnow().isoformat()),
        "processed_at": datetime.utcnow().isoformat(),
    }


# ─────────────────────────────────────────────
# CONSUMER
# ─────────────────────────────────────────────
class _MockConsumer:
    """File-backed mock — replays a parquet wire_transfers file as if
    it were a Kafka topic. Used when no broker is available."""

    def __init__(self, topic: str, source_parquet: Path):
        self.topic = topic
        self._iter = pd.read_parquet(source_parquet).to_dict("records")
        # Add event_time so realtime rules can run
        for rec in self._iter:
            rec.setdefault("event_time", datetime.utcnow().isoformat())
        logger.info(f"MockConsumer: {len(self._iter)} events from {source_parquet.name}")

    def __iter__(self):
        return self

    def __next__(self):
        if not self._iter:
            raise StopIteration
        return self._iter.pop(0)


def _get_consumer(topic: str):
    """Return a real KafkaConsumer or the file-based mock."""
    try:
        from kafka import KafkaConsumer
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=KAFKA_BOOTSTRAP,
            group_id=KAFKA_CONSUMER_GROUP,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="earliest",
            consumer_timeout_ms=2000,
        )
        logger.info(f"Connected to Kafka: {KAFKA_BOOTSTRAP} (topic={topic})")
        return consumer
    except Exception as e:
        logger.warning(f"Kafka not available ({e}). Using mock consumer (replays wire_transfers.parquet).")
        return _MockConsumer(topic, Path(BASE_DIR) / "data" / "dummy" / "wire_transfers.parquet")


def process_events(events, window: RollingWindow, sink: list) -> int:
    """Apply realtime rules to a stream of events.

    Args:
        events: iterable of dict-like events
        window: shared rolling-window state store
        sink: list to which alerts are appended (also returned)

    Returns the number of events processed.
    """
    n_processed = 0
    n_alerts = 0
    for raw in events:
        # KafkaConsumer yields (topic, partition, offset, value); mock yields dict
        if isinstance(raw, tuple) and len(raw) == 4:
            event = raw[3]
        else:
            event = raw
        if not isinstance(event, dict):
            continue
        rules, score = _score(event, window)
        n_processed += 1
        if rules:
            alert = _build_alert(event, rules, score)
            sink.append(alert)
            n_alerts += 1
    logger.info(f"Processed {n_processed} events, generated {n_alerts} realtime alerts")
    return n_processed


def run(max_events: Optional[int] = None) -> pd.DataFrame:
    """Consume wire events, apply realtime rules, persist alerts.

    Args:
        max_events: stop after this many events (for tests / smoke runs).
    """
    window = RollingWindow()
    alerts: list[dict] = []

    consumer = _get_consumer(KAFKA_TOPIC_WIRE)

    if max_events is None:
        try:
            for raw in consumer:
                if isinstance(raw, tuple) and len(raw) == 4:
                    process_events([raw], window, alerts)
                else:
                    process_events([raw], window, alerts)
        except StopIteration:
            pass
    else:
        batch = []
        for raw in consumer:
            batch.append(raw)
            if len(batch) >= max_events:
                break
        process_events(batch[:max_events], window, alerts)

    df = pd.DataFrame(alerts)
    if df.empty:
        logger.warning("Realtime: 0 alerts generated")
        return df

    # Persist to parquet (append, idempotent)
    if REALTIME_PATH.exists():
        existing = pd.read_parquet(REALTIME_PATH)
        df = pd.concat([existing, df], ignore_index=True)
    df.to_parquet(REALTIME_PATH, index=False)
    logger.success(f"Realtime: {len(alerts)} alerts written to {REALTIME_PATH}")

    # Publish to scb.realtime.alerts (best-effort)
    producer = _get_producer() or MockProducer()
    for alert in alerts:
        producer.send(KAFKA_TOPIC_REALTIME_ALERTS, value=alert)
    producer.flush()
    return df


# ─────────────────────────────────────────────
# REUSABLE API (for tests + downstream services)
# ─────────────────────────────────────────────
def score_event(event: dict, window: Optional[RollingWindow] = None) -> dict:
    """Score a single event. Returns the alert dict (or {} if no rules fire).

    Public so the FastAPI app and the ML feature store can score events
    in-process without spinning up a Kafka consumer.
    """
    window = window or RollingWindow()
    rules, score = _score(event, window)
    if not rules:
        return {}
    return _build_alert(event, rules, score)


if __name__ == "__main__":
    run()
