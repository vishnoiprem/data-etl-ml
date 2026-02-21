"""
MySQL Binlog CDC Producer → Kafka
Captures row-level changes from MySQL and publishes to Kafka topics.
Uses python-mysql-replication for binlog streaming.

Topics:
  ecomm.cdc.orders      - order create/update events
  ecomm.cdc.order_items - item-level events
  ecomm.cdc.inventory   - stock change events
  ecomm.cdc.user_events - clickstream (real-time)
  ecomm.cdc.payments    - payment events
"""
import json
import logging
import signal
import sys
from datetime import datetime
from decimal import Decimal

from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic
from pymysqlreplication import BinLogStreamReader
from pymysqlreplication.row_event import (
    DeleteRowsEvent, UpdateRowsEvent, WriteRowsEvent,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("cdc-producer")

# ── Config ────────────────────────────────────────────────────
MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "replication_user",
    "passwd": "replication_pass",
    "db": "ecommerce_db",
}

KAFKA_CONFIG = {
    "bootstrap.servers": "localhost:9092",
    "client.id": "ecomm-cdc-producer",
    "acks": "all",
    "retries": 5,
    "retry.backoff.ms": 500,
    "compression.type": "snappy",
    "linger.ms": 5,
    "batch.size": 65536,
}

# Table → Kafka topic mapping
TABLE_TOPIC_MAP = {
    "orders":       "ecomm.cdc.orders",
    "order_items":  "ecomm.cdc.order_items",
    "inventory":    "ecomm.cdc.inventory",
    "user_events":  "ecomm.cdc.user_events",
    "payments":     "ecomm.cdc.payments",
    "shipments":    "ecomm.cdc.shipments",
    "product_skus": "ecomm.cdc.product_skus",
    "reviews":      "ecomm.cdc.reviews",
}

TOPIC_CONFIGS = {
    topic: {"num_partitions": 6, "replication_factor": 1}
    for topic in TABLE_TOPIC_MAP.values()
}


# ── Kafka Setup ───────────────────────────────────────────────
def create_topics():
    admin = AdminClient({"bootstrap.servers": KAFKA_CONFIG["bootstrap.servers"]})
    topics = [
        NewTopic(name, num_partitions=cfg["num_partitions"],
                 replication_factor=cfg["replication_factor"])
        for name, cfg in TOPIC_CONFIGS.items()
    ]
    fs = admin.create_topics(topics, validate_only=False)
    for topic, f in fs.items():
        try:
            f.result()
            logger.info(f"Topic created: {topic}")
        except Exception as e:
            logger.warning(f"Topic {topic}: {e}")


def delivery_report(err, msg):
    if err:
        logger.error(f"Delivery failed for {msg.topic()}: {err}")
    else:
        logger.debug(f"Delivered to {msg.topic()}[{msg.partition()}] @{msg.offset()}")


# ── Serializer ────────────────────────────────────────────────
def serialize_row(row: dict) -> dict:
    """Convert MySQL row to JSON-serializable dict."""
    result = {}
    for k, v in row.items():
        if isinstance(v, datetime):
            result[k] = v.isoformat()
        elif isinstance(v, Decimal):
            result[k] = float(v)
        elif isinstance(v, bytes):
            result[k] = v.decode("utf-8", errors="replace")
        elif isinstance(v, dict):
            result[k] = v  # JSON column already parsed
        else:
            result[k] = v
    return result


def build_cdc_envelope(op: str, table: str, row: dict, before: dict = None) -> dict:
    """Wrap row change in CDC envelope format (Debezium-compatible)."""
    return {
        "schema": "ecommerce_db",
        "table": table,
        "op": op,           # c=create, u=update, d=delete
        "ts_ms": int(datetime.utcnow().timestamp() * 1000),
        "before": serialize_row(before) if before else None,
        "after": serialize_row(row) if row else None,
    }


def get_partition_key(table: str, row: dict) -> str:
    """Determine Kafka partition key for ordering guarantees."""
    key_map = {
        "orders":      "order_id",
        "order_items": "order_id",
        "inventory":   "sku_id",
        "user_events": "user_id",
        "payments":    "order_id",
        "shipments":   "order_id",
        "product_skus": "product_id",
        "reviews":     "product_id",
    }
    key_col = key_map.get(table, list(row.keys())[0])
    return str(row.get(key_col, "unknown"))


# ── CDC Stream ────────────────────────────────────────────────
class CDCProducer:
    def __init__(self):
        self.producer = Producer(KAFKA_CONFIG)
        self.running = True
        self.stats = {t: {"creates": 0, "updates": 0, "deletes": 0}
                      for t in TABLE_TOPIC_MAP}
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    def _shutdown(self, signum, frame):
        logger.info("Shutdown signal received. Flushing producer...")
        self.running = False
        self.producer.flush(timeout=30)
        logger.info(f"Final stats: {self.stats}")
        sys.exit(0)

    def publish(self, table: str, op: str, row: dict, before: dict = None):
        topic = TABLE_TOPIC_MAP.get(table)
        if not topic:
            return

        envelope = build_cdc_envelope(op, table, row, before)
        key = get_partition_key(table, row or before)

        self.producer.produce(
            topic=topic,
            key=key.encode("utf-8"),
            value=json.dumps(envelope).encode("utf-8"),
            on_delivery=delivery_report,
        )
        self.producer.poll(0)  # trigger delivery callbacks

        op_name = {"c": "creates", "u": "updates", "d": "deletes"}[op]
        self.stats[table][op_name] += 1

    def run(self, resume_file: str = "/tmp/binlog_position.json"):
        """Start binlog streaming. Resumes from last position if file exists."""
        # Load saved position
        log_file = None
        log_pos = None
        try:
            with open(resume_file) as f:
                pos = json.load(f)
                log_file = pos.get("log_file")
                log_pos = pos.get("log_pos")
                logger.info(f"Resuming from {log_file}:{log_pos}")
        except FileNotFoundError:
            logger.info("Starting from latest binlog position")

        stream = BinLogStreamReader(
            connection_settings=MYSQL_CONFIG,
            server_id=100,
            only_tables=list(TABLE_TOPIC_MAP.keys()),
            only_schemas=["ecommerce_db"],
            resume_stream=True,
            log_file=log_file,
            log_pos=log_pos,
            blocking=True,
            freeze_schema=False,
        )

        event_count = 0
        logger.info("CDC stream started. Listening for changes...")

        for binlog_event in stream:
            if not self.running:
                break

            table = binlog_event.table
            if not isinstance(binlog_event, (WriteRowsEvent, UpdateRowsEvent, DeleteRowsEvent)):
                continue

            for row in binlog_event.rows:
                if isinstance(binlog_event, WriteRowsEvent):
                    self.publish(table, "c", row["values"])
                elif isinstance(binlog_event, UpdateRowsEvent):
                    self.publish(table, "u", row["after_values"], row["before_values"])
                elif isinstance(binlog_event, DeleteRowsEvent):
                    self.publish(table, "d", row["values"])

            event_count += 1

            # Save position every 1000 events
            if event_count % 1000 == 0:
                pos = {"log_file": stream.log_file, "log_pos": stream.log_pos}
                with open(resume_file, "w") as f:
                    json.dump(pos, f)
                self.producer.flush()
                logger.info(f"Checkpoint saved. Events processed: {event_count}")

        stream.close()
        self.producer.flush(timeout=30)
        logger.info(f"Stream ended. Total events: {event_count}")


if __name__ == "__main__":
    create_topics()
    cdc = CDCProducer()
    cdc.run()
