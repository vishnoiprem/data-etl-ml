"""Three end-to-end pipeline solutions from the mock interviews.

The mock interviews (lessons 28, 29, 30) describe three production
pipelines at the whiteboard level. This file shows what they look
like in code, using the abstractions from modules 02-06.

The three solutions:

  1. ``run_netflix_clickstream_pipeline`` — Kafka-style event
     ingestion + a Flink-equivalent windowed aggregator that
     computes per-user play counts. Uses the ``InMemoryBroker``
     and ``IdempotencyCache`` from module 05.

  2. ``run_document_processing_pipeline`` — S3-style upload,
     a format router (PDF / DOCX / IMAGE), field extraction,
     and a dual write to a search index and a structured
     table. Uses ``QueryRunner`` from common.

  3. ``run_banking_cdc_pipeline`` — Postgres-style source,
     Debezium-style CDC event stream, Kafka-style broker,
     Flink-style per-user feature store, and a Delta Lake-style
     bronze + silver layer. Uses ``CDCPipeline`` from module
     03, ``InMemoryBroker`` from module 05.

Each solution has a small ``run_*`` function that wires it
together with realistic test data. The test file in
``tests/test_solutions.py`` exercises each one.

Author: Prem Vishnoi <pvishnoi@avilx.com>
"""

from __future__ import annotations

import importlib.util
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from common import QueryRunner

# ----------------------------------------------------------------------------
# Module loading: each solution uses code from earlier modules, but we can't
# import by dotted name (the directory `03_extraction` starts with a digit).
# So we load the modules by path and register them in sys.modules.
# ----------------------------------------------------------------------------

HERE = Path(__file__).resolve().parent
COURSE_ROOT = HERE.parents[2]
TRACK_ROOT = HERE.parents[1]

# Make `common` importable.
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))


def _load_module(name: str, rel_path: str):
    path = TRACK_ROOT / rel_path
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {name} from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


_streaming_mod = _load_module(
    "data_pipeline_design_07_streaming",
    "05_loading/code/streaming_loader.py",
)
_idempotency_mod = _load_module(
    "data_pipeline_design_07_idempotency",
    "05_loading/code/idempotency.py",
)
_cdc_mod = _load_module(
    "data_pipeline_design_07_cdc",
    "03_extraction/code/cdc.py",
)

InMemoryBroker = _streaming_mod.InMemoryBroker
StreamEvent = _streaming_mod.StreamEvent
StreamingLoader = _streaming_mod.StreamingLoader
IdempotencyCache = _idempotency_mod.IdempotencyCache
dedup_by_key = _idempotency_mod.dedup_by_key
CDCPipeline = _cdc_mod.CDCPipeline
CDCEvent = _cdc_mod.CDCEvent


# ============================================================================
# Solution 1 — Netflix clickstream pipeline
# ============================================================================
#
# Architecture (from lesson 28):
#
#   client → API gateway → Kafka (partitioned by user_id) →
#     ├─► Flink (1-minute tumbling window per user) → Redis (features)
#     └─► S3 (raw events) → Spark → Snowflake (BI / A/B)
#
# In code: the "client" is just a function that generates events;
# the "API gateway" is the InMemoryBroker.publish(); the "Flink
# job" is a small Python function that walks partitions and
# aggregates; the "Redis features" is an in-memory dict; the
# "S3 / Snowflake" is a SQLite table via QueryRunner.


@dataclass
class ClickstreamSolution:
    """End-to-end Netflix-style clickstream pipeline.

    A ``ClickstreamSolution`` is the result of
    :func:`run_netflix_clickstream_pipeline`. Tests use the
    public fields to inspect what happened: ``events_published``,
    ``events_processed``, ``user_play_counts``, ``feature_store``.
    """

    broker: InMemoryBroker
    feature_store: Dict[str, Dict[str, int]]
    warehouse: QueryRunner
    events_published: int = 0
    events_processed: int = 0
    user_play_counts: Dict[str, int] = field(default_factory=dict)
    _cache: IdempotencyCache = field(default_factory=IdempotencyCache)


def build_netflix_clickstream_pipeline(
    num_partitions: int = 4,
) -> ClickstreamSolution:
    """Build the Netflix clickstream pipeline components.

    Returns a :class:`ClickstreamSolution` with the broker,
    feature store, and warehouse ready to ingest events.
    """
    broker = InMemoryBroker()
    broker.create_topic("events.plays", partitions=num_partitions)
    warehouse = QueryRunner(":memory:")
    warehouse.execute(
        "CREATE TABLE fact_events ("
        "  event_id TEXT PRIMARY KEY,"
        "  user_id TEXT,"
        "  event_type TEXT,"
        "  title_id TEXT,"
        "  ts_ms INTEGER"
        ")"
    )
    return ClickstreamSolution(
        broker=broker,
        feature_store=defaultdict(
            lambda: {
                "rolling_1h_play_count": 0,
                "last_play_ts_ms": 0,
            }
        ),
        warehouse=warehouse,
    )


def netflix_publish_event(
    sol: ClickstreamSolution,
    *,
    event_id: str,
    user_id: str,
    title_id: str,
    ts_ms: int,
    event_type: str = "play",
) -> StreamEvent:
    """Publish one clickstream event through the broker.

    The partition key is ``user_id`` so all events for a user
    land on the same partition (matches the lesson's design).
    """
    event = sol.broker.publish(
        "events.plays",
        key=user_id,
        value={
            "event_id": event_id,
            "user_id": user_id,
            "title_id": title_id,
            "event_type": event_type,
            "ts_ms": ts_ms,
        },
    )
    sol.events_published += 1
    return event


def netflix_consume_batch(
    sol: ClickstreamSolution,
    *,
    max_records: int = 100,
) -> int:
    """Consume one batch from the broker.

    Each event is deduped on ``event_id``. Plays update the
    per-user feature store and the per-user play counter; all
    events are bulk-loaded into the ``fact_events`` warehouse
    table. Returns the number of events loaded.
    """
    events = sol.broker.poll("flink", "events.plays", max_records=max_records)
    if not events:
        return 0

    deduped, _ = dedup_by_key(
        [{"_e": e} for e in events],
        key_fn=lambda d: d["_e"].value["event_id"],
        cache=sol._cache,
    )

    rows: List[Dict[str, Any]] = []
    for d in deduped:
        ev: StreamEvent = d["_e"]
        v = ev.value
        rows.append(
            {
                "event_id": v["event_id"],
                "user_id": v["user_id"],
                "event_type": v["event_type"],
                "title_id": v.get("title_id", ""),
                "ts_ms": int(v.get("ts_ms", 0)),
            }
        )
        if v["event_type"] == "play":
            sol.user_play_counts[v["user_id"]] = (
                sol.user_play_counts.get(v["user_id"], 0) + 1
            )
            sol.feature_store[v["user_id"]]["rolling_1h_play_count"] += 1
            sol.feature_store[v["user_id"]]["last_play_ts_ms"] = int(
                v.get("ts_ms", 0)
            )

    if rows:
        # Idempotent insert keyed on event_id.
        for r in rows:
            existing = sol.warehouse.query_one(
                "SELECT event_id FROM fact_events WHERE event_id = ?",
                (r["event_id"],),
            )
            if existing is not None:
                continue
            sol.warehouse.execute(
                "INSERT INTO fact_events (event_id, user_id, event_type,"
                " title_id, ts_ms) VALUES (?, ?, ?, ?, ?)",
                (
                    r["event_id"],
                    r["user_id"],
                    r["event_type"],
                    r["title_id"],
                    r["ts_ms"],
                ),
            )
        sol.events_processed += len(rows)

    # Commit offsets after successful load.
    sol.broker.commit("flink", "events.plays", events)
    return len(rows)


def run_netflix_clickstream_pipeline(
    events: Sequence[Dict[str, Any]],
) -> ClickstreamSolution:
    """Run the clickstream pipeline against a synthetic event stream.

    Each event dict must have: ``event_id``, ``user_id``,
    ``title_id``, ``ts_ms``. Optional: ``event_type`` (default
    "play"). Returns the populated solution.
    """
    sol = build_netflix_clickstream_pipeline()
    for e in events:
        netflix_publish_event(sol, **e)
    # Drain the broker.
    while netflix_consume_batch(sol) > 0:
        pass
    return sol


# ============================================================================
# Solution 2 — Document processing pipeline
# ============================================================================
#
# Architecture (from lesson 29):
#
#   user → upload → S3 → SQS → worker →
#     ├─► format router (PDF / DOCX / IMAGE) → text
#     ├─► field extractor (regex / model) → fields
#     └─► Elasticsearch (full text) + Postgres (fields)
#
# In code: "S3" is the filesystem, "SQS" is an in-memory queue,
# "worker" is a function that processes one message at a time,
# "Elasticsearch" is an in-memory dict, "Postgres" is QueryRunner.


@dataclass
class DocProcessingSolution:
    """Result of :func:`run_document_processing_pipeline`."""

    warehouse: QueryRunner
    search_index: Dict[str, Dict[str, Any]]
    processed: int = 0
    dlq: List[Dict[str, Any]] = field(default_factory=list)


_INVOICE_NUMBER_RE = re.compile(r"INV-\d{4,}")
_TOTAL_RE = re.compile(r"Total:\s*\$?([\d,]+\.\d{2})")
_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def _format_router(content: str, doc_type: str) -> str:
    """Return extracted text. Simulated."""
    if doc_type == "image":
        # OCR stub: assume OCR worked (tests pass typed text).
        return content
    return content


def _field_extractor(text: str, doc_type: str) -> Dict[str, Any]:
    """Regex-based field extraction for invoices and contracts."""
    if doc_type != "invoice":
        return {}
    out: Dict[str, Any] = {}
    m = _INVOICE_NUMBER_RE.search(text)
    if m:
        out["invoice_number"] = m.group(0)
    m = _TOTAL_RE.search(text)
    if m:
        out["total"] = float(m.group(1).replace(",", ""))
    m = _DATE_RE.search(text)
    if m:
        out["date"] = m.group(0)
    return out


def _process_one_doc(
    sol: DocProcessingSolution,
    msg: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Process a single document. Returns the record, or pushes to DLQ."""
    doc_id = msg["doc_id"]
    text = msg.get("text", "")
    doc_type = msg.get("doc_type", "contract")

    try:
        extracted_text = _format_router(text, doc_type)
        if not extracted_text:
            sol.dlq.append({**msg, "reason": "empty after format router"})
            return None
        fields = _field_extractor(extracted_text, doc_type)
    except Exception:  # noqa: BLE001
        sol.dlq.append({**msg, "reason": "processing exception"})
        return None

    # Write to "Elasticsearch" (in-memory).
    sol.search_index[doc_id] = {
        "title": msg.get("title", ""),
        "doc_type": doc_type,
        "body_text": extracted_text,
    }
    # Write to "Postgres" (SQLite).
    sol.warehouse.execute(
        "INSERT INTO extracted_fields (doc_id, doc_type, invoice_number,"
        " total, event_date) VALUES (?, ?, ?, ?, ?)",
        (
            doc_id,
            doc_type,
            fields.get("invoice_number"),
            fields.get("total"),
            fields.get("date"),
        ),
    )
    sol.processed += 1
    return {"doc_id": doc_id, "fields": fields}


def build_document_processing_pipeline() -> DocProcessingSolution:
    """Build the document-processing solution."""
    warehouse = QueryRunner(":memory:")
    warehouse.execute(
        "CREATE TABLE extracted_fields ("
        "  doc_id TEXT PRIMARY KEY,"
        "  doc_type TEXT,"
        "  invoice_number TEXT,"
        "  total REAL,"
        "  event_date TEXT"
        ")"
    )
    return DocProcessingSolution(
        warehouse=warehouse,
        search_index={},
    )


def run_document_processing_pipeline(
    messages: Sequence[Dict[str, Any]],
) -> DocProcessingSolution:
    """Run the document-processing pipeline over a batch of messages.

    Each message: ``{doc_id, text, doc_type, title}``. ``text``
    is the (simulated) extracted text; ``doc_type`` is one of
    "pdf", "docx", "image", "invoice", "contract".
    """
    sol = build_document_processing_pipeline()
    for msg in messages:
        _process_one_doc(sol, msg)
    return sol


# ============================================================================
# Solution 3 — Banking CDC pipeline
# ============================================================================
#
# Architecture (from lesson 30):
#
#   core banking DB → Debezium (WAL reader) → Kafka → Flink →
#     ├─► real-time fraud detector (Redis + ML)
#     └─► Delta Lake bronze → dbt → Snowflake (regulatory)
#
# In code: "core banking DB" is a QueryRunner, "Debezium" is the
# CDCPipeline, "Kafka" is the InMemoryBroker, "Flink" is a
# small per-transaction feature updater, "Delta Lake bronze" is
# a SQLite table, "real-time fraud detector" is a deterministic
# rule-based scorer (the ML model is out of scope for a teaching
# example).


@dataclass
class BankingCDCSolution:
    """Result of :func:`run_banking_cdc_pipeline`."""

    source: QueryRunner
    cdc: Any  # CDCPipeline
    broker: InMemoryBroker
    warehouse: QueryRunner
    events_emitted: int = 0
    fraud_alerts: List[Dict[str, Any]] = field(default_factory=list)
    last_slot_lag_bytes: int = 0


def _fraud_score(amount: float, history: List[float]) -> float:
    """Deterministic fraud scorer.

    Real systems use an ML model; for the demo we use a simple
    z-score against the user's recent transaction history. A
    transaction > 4σ above the mean is a fraud alert (score 0.95);
    > 2σ is medium (score 0.6); otherwise low (score 0.1).
    """
    if not history:
        return 0.1
    mean = sum(history) / len(history)
    var = sum((x - mean) ** 2 for x in history) / len(history)
    std = var ** 0.5
    if std == 0:
        return 0.5 if amount > mean else 0.1
    z = (amount - mean) / std
    if z >= 4:
        return 0.95
    if z >= 2:
        return 0.6
    return 0.1


def _make_broker_sink(broker: InMemoryBroker) -> Any:
    """Build a tiny shim that publishes CDC events to the broker."""

    class _BrokerSink:
        def __init__(self, b: InMemoryBroker) -> None:
            self.broker = b

        def write(self, events: List[Dict[str, Any]]) -> None:
            for e in events:
                key = e.get("key", {}).get("txn_id", "0")
                self.broker.publish(
                    "cdc.transactions",
                    key=str(key),
                    value=e,
                )

    return _BrokerSink(broker)


def build_banking_cdc_pipeline() -> BankingCDCSolution:
    """Build the banking CDC pipeline components."""
    # Source OLTP database (a small transactions table).
    source = QueryRunner(":memory:")
    source.execute(
        "CREATE TABLE accounts ("
        "  account_id INTEGER PRIMARY KEY,"
        "  customer_id INTEGER,"
        "  balance REAL NOT NULL"
        ")"
    )
    source.execute(
        "CREATE TABLE transactions ("
        "  txn_id INTEGER PRIMARY KEY,"
        "  account_id INTEGER NOT NULL,"
        "  amount REAL NOT NULL,"
        "  ts_ms INTEGER NOT NULL"
        ")"
    )

    # Sink for CDC events — a Kafka-style broker.
    broker = InMemoryBroker()
    broker.create_topic("cdc.transactions", partitions=4)
    broker.create_topic("fraud.alerts", partitions=1)

    # Bronze + silver warehouse (Delta Lake stand-in).
    warehouse = QueryRunner(":memory:")
    warehouse.execute(
        "CREATE TABLE bronze_transactions ("
        "  txn_id INTEGER,"
        "  op TEXT,"
        "  account_id INTEGER,"
        "  amount REAL,"
        "  ts_ms INTEGER"
        ")"
    )

    # CDC pipeline writes to the broker.
    cdc_pipeline = CDCPipeline(
        sink=_make_broker_sink(broker),
        table="transactions",
        pk="txn_id",
    )

    return BankingCDCSolution(
        source=source,
        cdc=cdc_pipeline,
        broker=broker,
        warehouse=warehouse,
        events_emitted=0,
    )


def _drain_broker(
    sol: BankingCDCSolution,
    history: Dict[int, List[float]],
) -> int:
    """Pull events from the broker, run the fraud scorer, write bronze."""
    events = sol.broker.poll("flink", "cdc.transactions", max_records=100)
    if not events:
        return 0

    rows: List[Dict[str, Any]] = []
    for ev in events:
        v = ev.value
        before = v.get("before") or {}
        after = v.get("after") or {}
        key_obj = v.get("key", {}) or {}
        txn_id = (
            after.get("txn_id")
            if after.get("txn_id") is not None
            else before.get("txn_id")
            if before.get("txn_id") is not None
            else key_obj.get("txn_id", 0)
        )
        account_id = (
            after.get("account_id")
            if after.get("account_id") is not None
            else before.get("account_id")
            if before.get("account_id") is not None
            else key_obj.get("account_id", 0)
        )
        amount = after.get("amount") if after else None
        rows.append(
            {
                "txn_id": int(txn_id) if txn_id is not None else 0,
                "op": v["op"],
                "account_id": int(account_id) if account_id is not None else 0,
                "amount": float(amount) if amount is not None else 0.0,
                "ts_ms": int(v.get("ts_ms", 0)),
            }
        )

    # Bronze bulk load via executemany.
    if rows:
        sol.warehouse.executemany(
            "INSERT INTO bronze_transactions (txn_id, op, account_id,"
            " amount, ts_ms) VALUES (?, ?, ?, ?, ?)",
            [
                (
                    r["txn_id"],
                    r["op"],
                    r["account_id"],
                    r["amount"],
                    r["ts_ms"],
                )
                for r in rows
            ],
        )

    # Update per-account history and run fraud scorer.
    for r in rows:
        if r["op"] in ("c", "u") and r["amount"] != 0:
            score = _fraud_score(
                r["amount"], list(history[r["account_id"]])
            )
            history[r["account_id"]].append(r["amount"])
            if score >= 0.9:
                sol.broker.publish(
                    "fraud.alerts",
                    key=str(r["account_id"]),
                    value={
                        "txn_id": r["txn_id"],
                        "account_id": r["account_id"],
                        "amount": r["amount"],
                        "score": score,
                    },
                )
                sol.fraud_alerts.append(
                    {
                        "txn_id": r["txn_id"],
                        "account_id": r["account_id"],
                        "amount": r["amount"],
                        "score": score,
                    }
                )

    sol.broker.commit("flink", "cdc.transactions", events)
    sol.events_emitted += len(rows)
    return len(rows)


def run_banking_cdc_pipeline(
    *,
    initial_rows: Sequence[Dict[str, Any]],
    updates: Sequence[Dict[str, Any]],
) -> BankingCDCSolution:
    """Run the banking CDC pipeline through a series of source snapshots.

    ``initial_rows`` seed the transactions table; ``updates`` is
    the next snapshot (may include updates / new rows / drops).
    The pipeline:

      1. Seeds the source with ``initial_rows``.
      2. Runs the CDC pipeline against ``initial_rows`` to emit
         insert events.
      3. Replaces the source with ``updates`` and re-runs to emit
         update / insert / delete events.
      4. Drains the broker and updates per-account history +
         runs the fraud detector + bulk-loads the bronze table.

    Returns the populated solution.
    """
    sol = build_banking_cdc_pipeline()

    # 1. Seed source.
    if initial_rows:
        cols = list(initial_rows[0].keys())
        placeholders = ", ".join("?" for _ in cols)
        cols_csv = ", ".join(cols)
        for r in initial_rows:
            sol.source.execute(
                f"INSERT INTO transactions ({cols_csv}) VALUES ({placeholders})",
                [r[c] for c in cols],
            )

    # Per-account history (the "Redis" feature store).
    history: Dict[int, List[float]] = defaultdict(list)

    # 2. First CDC pass against initial snapshot.
    cdc_run1 = sol.cdc.run_once(list(initial_rows))

    while _drain_broker(sol, history) > 0:
        pass

    # 3. Update source table with the next snapshot.
    sol.source.execute("DELETE FROM transactions")
    if updates:
        cols = list(updates[0].keys())
        placeholders = ", ".join("?" for _ in cols)
        cols_csv = ", ".join(cols)
        for r in updates:
            sol.source.execute(
                f"INSERT INTO transactions ({cols_csv}) VALUES ({placeholders})",
                [r[c] for c in cols],
            )

    cdc_run2 = sol.cdc.run_once(list(updates))
    total_events = len(cdc_run1) + len(cdc_run2)
    sol.last_slot_lag_bytes = total_events * 256  # rough mock

    while _drain_broker(sol, history) > 0:
        pass

    return sol


# ---- helpers --------------------------------------------------------------


def get_solution_summary(sol: Any) -> Dict[str, Any]:
    """Return a summary dict for any of the three solutions."""
    if isinstance(sol, ClickstreamSolution):
        n = sol.warehouse.query_one(
            "SELECT COUNT(*) AS n FROM fact_events"
        )["n"]
        return {
            "events_published": sol.events_published,
            "events_processed": sol.events_processed,
            "unique_users": len(sol.user_play_counts),
            "warehouse_rows": n,
            "feature_store_size": len(sol.feature_store),
        }
    if isinstance(sol, DocProcessingSolution):
        n = sol.warehouse.query_one(
            "SELECT COUNT(*) AS n FROM extracted_fields"
        )["n"]
        return {
            "processed": sol.processed,
            "search_index_size": len(sol.search_index),
            "dlq_size": len(sol.dlq),
            "warehouse_rows": n,
        }
    if isinstance(sol, BankingCDCSolution):
        n = sol.warehouse.query_one(
            "SELECT COUNT(*) AS n FROM bronze_transactions"
        )["n"]
        return {
            "events_emitted": sol.events_emitted,
            "fraud_alerts": len(sol.fraud_alerts),
            "bronze_rows": n,
        }
    return {}


__all__ = [
    "ClickstreamSolution",
    "build_netflix_clickstream_pipeline",
    "netflix_publish_event",
    "netflix_consume_batch",
    "run_netflix_clickstream_pipeline",
    "DocProcessingSolution",
    "build_document_processing_pipeline",
    "run_document_processing_pipeline",
    "BankingCDCSolution",
    "build_banking_cdc_pipeline",
    "run_banking_cdc_pipeline",
    "get_solution_summary",
]
