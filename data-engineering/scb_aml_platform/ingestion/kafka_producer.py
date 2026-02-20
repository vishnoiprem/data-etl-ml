"""
SCB AML Platform — Kafka Producer Simulator
Simulates near-real-time wire transfer and large cash deposit streams
that bypass Sqoop batch and land directly in Kafka topics.

Topics:
  scb.transactions.raw     — high-value retail transactions
  scb.wire_transfers.raw   — SWIFT MT103/MT202 messages

In production: Kafka Connect source connectors with Debezium CDC
Here: publishes messages to local Kafka (or prints if no broker available)
"""

import sys
import json
import time
import random
from datetime import datetime
from pathlib import Path

import pandas as pd
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from scb_aml_platform.config.settings import (
    DUMMY_DIR, KAFKA_BOOTSTRAP, KAFKA_TOPIC_TXN, KAFKA_TOPIC_WIRE,
    CTR_THRESHOLD_USD
)

DUMMY_DIR = Path(DUMMY_DIR)


def _get_producer():
    """Return a real Kafka producer or a mock."""
    try:
        from kafka import KafkaProducer
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        logger.info(f"Connected to Kafka: {KAFKA_BOOTSTRAP}")
        return producer
    except Exception as e:
        logger.warning(f"Kafka not available ({e}). Using mock producer.")
        return None


class MockProducer:
    """Prints messages to stdout when no Kafka broker is available."""
    def send(self, topic: str, value: dict, key=None):
        logger.debug(f"[MOCK KAFKA] topic={topic} | {json.dumps(value)[:120]}...")
        return self

    def flush(self):
        pass


def stream_wire_transfers(n: int = 50, delay_ms: int = 100):
    """
    Stream high-value wire transfers as near-real-time Kafka events.
    Simulates CIB systems pushing SWIFT messages to Kafka Connect.
    """
    producer = _get_producer() or MockProducer()
    df = pd.read_parquet(DUMMY_DIR / "wire_transfers.parquet")

    # Focus on large transfers (likely to trigger alerts)
    large = df[df["amount_usd"] > CTR_THRESHOLD_USD]
    if large.empty:
        large = df

    sample = large.sample(min(n, len(large)), replace=True)
    logger.info(f"Streaming {len(sample)} wire transfer events to {KAFKA_TOPIC_WIRE}")

    for _, row in sample.iterrows():
        msg = row.to_dict()
        msg["event_time"] = datetime.utcnow().isoformat()
        msg["kafka_partition_key"] = row.get("sender_country", "SG")

        producer.send(
            KAFKA_TOPIC_WIRE,
            value=msg,
            key=msg["kafka_partition_key"].encode() if hasattr(producer, "send") else None
        )
        time.sleep(delay_ms / 1000.0)

    producer.flush()
    logger.success(f"Streamed {len(sample)} wire transfer events")


def stream_large_cash_transactions(n: int = 30, delay_ms: int = 200):
    """
    Stream large cash transactions (potential CTR triggers).
    Partitioned by country_code for ordered per-country processing.
    """
    producer = _get_producer() or MockProducer()
    df = pd.read_parquet(DUMMY_DIR / "transactions.parquet")

    # Transactions >= 85% of CTR threshold in USD
    ctr_suspect = df[df["amount_usd"] >= CTR_THRESHOLD_USD * 0.85]
    if ctr_suspect.empty:
        ctr_suspect = df.nlargest(n, "amount_usd")

    sample = ctr_suspect.sample(min(n, len(ctr_suspect)), replace=True)
    logger.info(f"Streaming {len(sample)} large-cash events to {KAFKA_TOPIC_TXN}")

    for _, row in sample.iterrows():
        msg = row.to_dict()
        msg["event_time"] = datetime.utcnow().isoformat()
        msg["exceeds_ctr"] = float(row.get("amount_usd", 0)) >= CTR_THRESHOLD_USD
        producer.send(KAFKA_TOPIC_TXN, value=msg)
        time.sleep(delay_ms / 1000.0)

    producer.flush()
    logger.success(f"Streamed {len(sample)} large-cash transaction events")


if __name__ == "__main__":
    logger.info("=== Kafka Producer: Near-Real-Time Ingestion ===")
    stream_wire_transfers(n=20, delay_ms=50)
    stream_large_cash_transactions(n=15, delay_ms=50)
