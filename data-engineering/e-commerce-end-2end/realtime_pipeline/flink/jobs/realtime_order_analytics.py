"""
Apache Flink Job: Real-Time Order Analytics
Consumes CDC events from Kafka, performs windowed aggregations,
writes results to ClickHouse for real-time dashboards.

Pipeline:
  Kafka(ecomm.cdc.orders) → Flink → ClickHouse(rt_order_metrics)
  Kafka(ecomm.cdc.user_events) → Flink → ClickHouse(rt_funnel_metrics)
"""
import json
import logging
from datetime import datetime

from pyflink.common import WatermarkStrategy, Duration
from pyflink.common.serialization import SimpleStringSchema
from pyflink.common.typeinfo import Types
from pyflink.datastream import StreamExecutionEnvironment, RuntimeExecutionMode
from pyflink.datastream.connectors.kafka import (
    KafkaSource, KafkaOffsetsInitializer
)
from pyflink.datastream.window import TumblingEventTimeWindows, SlidingEventTimeWindows
from pyflink.datastream.functions import (
    MapFunction, FlatMapFunction, ReduceFunction,
    ProcessWindowFunction, KeyedProcessFunction
)
from pyflink.datastream.state import ValueStateDescriptor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("flink-order-analytics")

KAFKA_BOOTSTRAP = "localhost:9092"
CLICKHOUSE_HOST = "localhost"
CLICKHOUSE_PORT = 9000
CLICKHOUSE_DB = "ecomm_realtime"


# ── Parse Functions ───────────────────────────────────────────
class ParseOrderEvent(MapFunction):
    """Parse CDC envelope → order dict."""
    def map(self, value: str):
        try:
            msg = json.loads(value)
            row = msg.get("after") or msg.get("before") or {}
            return {
                "order_id": row.get("order_id"),
                "user_id": row.get("user_id"),
                "seller_id": row.get("seller_id"),
                "status": row.get("status"),
                "payment_method": row.get("payment_method"),
                "total_amount": float(row.get("total_amount") or 0),
                "op": msg.get("op"),
                "event_time": int(datetime.utcnow().timestamp() * 1000),
                "city": (json.loads(row.get("shipping_address") or "{}")).get("city", "Unknown"),
            }
        except Exception as e:
            logger.warning(f"Parse error: {e}")
            return None


class ParseUserEvent(MapFunction):
    """Parse user clickstream events."""
    def map(self, value: str):
        try:
            msg = json.loads(value)
            row = msg.get("after") or {}
            return {
                "user_id": row.get("user_id"),
                "event_type": row.get("event_type"),
                "entity_id": row.get("entity_id"),
                "session_id": row.get("session_id"),
                "device_type": row.get("device_type"),
                "platform": row.get("platform"),
                "event_time": int(datetime.utcnow().timestamp() * 1000),
            }
        except Exception:
            return None


# ── Aggregation Functions ─────────────────────────────────────
class OrderWindowAgg(ProcessWindowFunction):
    """
    1-minute tumbling window: compute GMV, order count, unique buyers.
    Output: (window_start, window_end, city, gmv, order_count, unique_buyers)
    """
    def process(self, key, context, elements):
        window = context.window()
        orders = list(elements)
        gmv = sum(o["total_amount"] for o in orders)
        order_count = len(orders)
        unique_buyers = len(set(o["user_id"] for o in orders if o["user_id"]))
        yield {
            "window_start": datetime.utcfromtimestamp(window.start / 1000).isoformat(),
            "window_end": datetime.utcfromtimestamp(window.end / 1000).isoformat(),
            "city": key,
            "gmv": round(gmv, 2),
            "order_count": order_count,
            "unique_buyers": unique_buyers,
            "avg_order_value": round(gmv / order_count, 2) if order_count > 0 else 0,
            "computed_at": datetime.utcnow().isoformat(),
        }


class FunnelWindowAgg(ProcessWindowFunction):
    """
    5-minute tumbling window: compute conversion funnel metrics.
    """
    def process(self, key, context, elements):
        events = list(elements)
        window = context.window()
        counts = {}
        for e in events:
            et = e["event_type"]
            counts[et] = counts.get(et, 0) + 1

        views = counts.get("view", 0)
        carts = counts.get("add_to_cart", 0)
        purchases = counts.get("purchase", 0)

        yield {
            "window_start": datetime.utcfromtimestamp(window.start / 1000).isoformat(),
            "window_end": datetime.utcfromtimestamp(window.end / 1000).isoformat(),
            "platform": key,
            "views": views,
            "add_to_cart": carts,
            "purchases": purchases,
            "view_to_cart_rate": round(carts / views * 100, 2) if views > 0 else 0,
            "cart_to_purchase_rate": round(purchases / carts * 100, 2) if carts > 0 else 0,
            "overall_conversion_rate": round(purchases / views * 100, 2) if views > 0 else 0,
            "computed_at": datetime.utcnow().isoformat(),
        }


class OrderAlertFunction(KeyedProcessFunction):
    """
    Stateful function: detect orders stuck in 'pending' for > 30 min.
    Emits alert events.
    """
    def open(self, runtime_context):
        self.order_state = runtime_context.get_state(
            ValueStateDescriptor("order_info", Types.STRING())
        )
        self.timer_state = runtime_context.get_state(
            ValueStateDescriptor("timer_ts", Types.LONG())
        )

    def process_element(self, value, ctx):
        if value["op"] == "c" and value["status"] == "pending":
            # Register timer 30 minutes from now
            timer_ts = ctx.timestamp() + (30 * 60 * 1000)
            ctx.timer_service().register_event_time_timer(timer_ts)
            self.order_state.update(json.dumps(value))
            self.timer_state.update(timer_ts)
        elif value["op"] == "u" and value["status"] != "pending":
            # Order moved out of pending - cancel timer
            ts = self.timer_state.value()
            if ts:
                ctx.timer_service().delete_event_time_timer(ts)
            self.order_state.clear()
            self.timer_state.clear()

    def on_timer(self, timestamp, ctx):
        order = self.order_state.value()
        if order:
            order_data = json.loads(order)
            yield {
                "alert_type": "STUCK_ORDER",
                "order_id": order_data.get("order_id"),
                "user_id": order_data.get("user_id"),
                "seller_id": order_data.get("seller_id"),
                "stuck_since": datetime.utcfromtimestamp(timestamp / 1000 - 1800).isoformat(),
                "alerted_at": datetime.utcnow().isoformat(),
            }
            self.order_state.clear()


# ── ClickHouse Sink ───────────────────────────────────────────
class ClickHouseSink:
    """Simple ClickHouse writer via HTTP interface."""

    def __init__(self, table: str):
        self.table = table

    def write(self, records: list):
        import clickhouse_driver
        client = clickhouse_driver.Client(host=CLICKHOUSE_HOST, port=9000, database=CLICKHOUSE_DB)
        if records:
            client.execute(f"INSERT INTO {self.table} VALUES", records)


# ── Kafka → Flink → ClickHouse Pipeline ──────────────────────
def build_order_pipeline(env: StreamExecutionEnvironment):
    """Order GMV analytics pipeline."""
    source = (
        KafkaSource.builder()
        .set_bootstrap_servers(KAFKA_BOOTSTRAP)
        .set_topics("ecomm.cdc.orders")
        .set_group_id("flink-order-analytics")
        .set_starting_offsets(KafkaOffsetsInitializer.latest())
        .set_value_only_deserializer(SimpleStringSchema())
        .build()
    )

    watermark_strategy = (
        WatermarkStrategy
        .for_bounded_out_of_orderness(Duration.of_seconds(10))
        .with_timestamp_assigner(lambda e, ts: json.loads(e).get("ts_ms", ts))
    )

    stream = env.from_source(source, watermark_strategy, "Kafka-Orders")

    # Parse → Filter valid → Key by city → 1-min window
    (stream
     .map(ParseOrderEvent())
     .filter(lambda x: x is not None and x["op"] in ("c", "u"))
     .key_by(lambda x: x.get("city", "Unknown"))
     .window(TumblingEventTimeWindows.of(Duration.of_minutes(1)))
     .process(OrderWindowAgg())
     .map(lambda x: json.dumps(x))
     .print()  # In production: replace with ClickHouse/Kafka sink
     )

    # Alert pipeline: key by order_id
    (stream
     .map(ParseOrderEvent())
     .filter(lambda x: x is not None)
     .key_by(lambda x: str(x.get("order_id")))
     .process(OrderAlertFunction())
     .map(lambda x: f"[ALERT] {json.dumps(x)}")
     .print()
     )


def build_funnel_pipeline(env: StreamExecutionEnvironment):
    """User event funnel analytics pipeline."""
    source = (
        KafkaSource.builder()
        .set_bootstrap_servers(KAFKA_BOOTSTRAP)
        .set_topics("ecomm.cdc.user_events")
        .set_group_id("flink-funnel-analytics")
        .set_starting_offsets(KafkaOffsetsInitializer.latest())
        .set_value_only_deserializer(SimpleStringSchema())
        .build()
    )

    watermark_strategy = WatermarkStrategy.for_bounded_out_of_orderness(Duration.of_seconds(5))

    stream = env.from_source(source, watermark_strategy, "Kafka-UserEvents")

    (stream
     .map(ParseUserEvent())
     .filter(lambda x: x is not None)
     .key_by(lambda x: x.get("platform", "web"))
     .window(TumblingEventTimeWindows.of(Duration.of_minutes(5)))
     .process(FunnelWindowAgg())
     .map(lambda x: json.dumps(x))
     .print()
     )


# ── Main ──────────────────────────────────────────────────────
if __name__ == "__main__":
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_runtime_mode(RuntimeExecutionMode.STREAMING)
    env.set_parallelism(4)
    env.enable_checkpointing(60_000)  # checkpoint every 60s

    build_order_pipeline(env)
    build_funnel_pipeline(env)

    logger.info("Submitting Flink job: EComm Real-Time Analytics")
    env.execute("EComm Real-Time Order & Funnel Analytics")
