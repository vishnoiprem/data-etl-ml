# 4.3 — Datastream & CDC

> **Section 4 · Streaming & Ingestion · Lecture 4.3 · 8:00**

## 🎯 What you will learn

- Change data capture fundamentals: the write-ahead log and the binlog as the source of truth
- The **log-position problem** and why timestamp-based CDC misses, duplicates, and reorders rows
- Why "just poll `updated_at`" is not CDC
- Datastream's architecture: streams, stream jobs, connection profiles, and the source→destination model
- The supported sources and destinations, and the two canonical flows
- The **change streams**: INSERT, UPDATE, DELETE — and how UPDATE is represented
- Snapshot + change stream consistency, and the "read your own writes" guarantee
- Cloud SQL → BigQuery and Cloud SQL → Pub/Sub in detail
- Cost control and the idle-stream trap
- When to use Datastream versus a Fivetran-style connector versus writing your own CDC

---

## 🧠 Concept

### Why CDC exists at all

A classic nightly batch pipeline has a structural problem: **it can only see the current state of a table, and it sees it late.** At 02:00, it reads `orders` and gets the current row for every order. If an order was created at 09:00, updated at 11:00, and deleted at 13:00, the nightly job sees only the deletion — or nothing at all if the batch ran between the delete and the next insert. Every intermediate state is lost.

Three common workarounds, and why each fails:

**Workaround 1 — poll on a timestamp column.**

```sql
SELECT * FROM orders WHERE updated_at > :last_run;
```

The failure modes are numerous and subtle:

- **Ties.** Two rows updated in the same second with the same `updated_at` value are indistinguishable. `>` skips the second row entirely. The fix `>=` produces duplicates. Neither is correct.
- **Non-monotonic clocks.** The `updated_at` value is written by the application or the database; a clock skew, a manually-set value, or a timezone bug makes the comparison meaningless.
- **No delete signal.** A hard delete leaves no trace in the table at all. There is no `updated_at` on a row that no longer exists.
- **In-place updates lose history.** You see the *new* value, not the old one. You cannot reconstruct "revenue was 100, then 120, then 90" — only "revenue is 90".
- **Long transactions.** A row updated inside a transaction that commits after your poll window is invisible to that poll but visible to the next, with a `updated_at` from before the transaction started — producing an out-of-order sequence.

**Workaround 2 — read the full table every night.** Correct, but O(table size) per run and up to 24 hours stale. For a 500 GB table this is a significant, recurring cost, and it cannot support anything below batch latency.

**Workaround 3 — triggers.** Every write fires a trigger that publishes to a queue. This works but it is invasive: it modifies the source schema, adds overhead to every write on the production database, misses writes from other paths (direct SQL, admin tools, replication), and creates a partial ordering problem across many triggers.

**Change Data Capture** avoids all three by reading the database's own write-ahead log.

### The write-ahead log

Every serious database maintains a **write-ahead log (WAL)**: before a write is applied to the data pages, the change is written to a durable log. This is what makes crash recovery possible — on restart, the database replays the log to reach a consistent state.

The critical insight for CDC: **the WAL contains every change, in the exact order the database applied them, with the exact values before and after the change.** It is not a summary of state; it is a complete, ordered history of mutations.

- **MySQL**: the **binlog** (binary log), in `ROW`, `STATEMENT`, or `MIXED` format. CDC requires `ROW`.
- **PostgreSQL**: the **WAL**, exposed via logical decoding with a replication slot.
- **Oracle**: the **redo log**, exposed via LogMiner or XStream.
- **SQL Server**: the transaction log, exposed via CDC tables.

**The binlog is the source of truth for changes.** Not the table, not the `updated_at` column, not a trigger.

### The log-position problem

If the log contains everything, why not just read the whole log? Because logs are unbounded and you only want the part you have not processed yet.

You need a **position** — a cursor into the log that says "I have processed up to here". The naive approach is a timestamp, and it fails for the same reason `updated_at` fails: the log position must be **monotonic, dense, and unambiguous**.

| Property | Timestamp position | Log position |
|---|---|---|
| Monotonic | No — clock skew, manual values | **Yes — the log position is assigned by the engine** |
| Dense | No — many changes share a timestamp | **Yes — every change has a distinct position** |
| Unambiguous | No — timestamp collisions | **Yes — position is unique within the log** |
| Deletes visible | No | **Yes** |
| Before/after values | No | **Yes** (in ROW format) |

The canonical log position formats:

- **MySQL binlog**: `filename:position` — e.g. `mysql-bin.000042:1234567`. The filename changes on rotation; the position resets to 4 at the start of each new file.
- **PostgreSQL**: `LSN` (log sequence number) — a 64-bit position, e.g. `0/16B3748`, monotonically increasing.
- **Oracle**: `SCN` (system change number) — a global, monotonically increasing number.
- **SQL Server**: `LSN` pairs.

**The rotation trap** is the classic mistake. If you store only the numeric position and the binlog file rotates, your next read starts at a completely unrelated place — you will either miss a large window of changes or re-read one. You must store **both** the filename and the position, and treat a filename change as a signal to move to the next file.

### Datastream's architecture

Datastream is Google's managed CDC service. It has four concepts:

- A **connection profile** describes how to reach a source database: type, host, port, credentials, network path. It holds secrets and is reusable across streams.
- A **stream** binds **one connection profile** to **one destination**, and defines the objects to capture. A stream represents the CDC channel itself.
- A **stream job** defines **what to do with the data from a stream**: which destination objects to write to, how to map schema, whether to include the change table and CDC metadata.
- A **change stream** is the actual output: an ordered sequence of change events, each with an operation type, the row's before/after values, and the CDC metadata (log position, timestamp, transaction ID).

```text
┌──────────────────────┐
│  Connection Profile  │  ← credentials, host, port, network
└──────────┬───────────┘
           │ referenced by
           ▼
┌──────────────────────┐        ┌────────────────────────────┐
│       Stream         │───────▶│      Stream Job            │
│  (source → dest      │        │  (object mapping, options) │
│   + objects to CDC)  │        └──────────────┬─────────────┘
└──────────────────────┘                       │
                                               ▼
                                    ┌──────────────────────┐
                                    │    Change Stream     │
                                    │  INSERT/UPDATE/      │
                                    │  DELETE + metadata   │
                                    └──────────┬───────────┘
                                               │
                            ┌──────────────────┴────────────────┐
                            ▼                                   ▼
                   ┌─────────────────┐              ┌────────────────────┐
                   │ BigQuery        │              │ Pub/Sub            │
                   │ (change table)  │              │ (JSON messages)    │
                   └─────────────────┘              └────────────────────┘
```

**A stream is 1:1 with a source→destination pair.** If you want the same Cloud SQL instance feeding both BigQuery and Pub/Sub, that is **two streams** — and therefore two stream-hours of charges and two sets of replication slots hammering the source. This is the structural reason behind the "idle stream cost trap" below.

### Supported sources and destinations

**Sources** (at the time of writing):

| Source | Notes |
|---|---|
| Cloud SQL for MySQL | 5.7, 8.0 |
| Cloud SQL for PostgreSQL | 9.6, 11, 13, 14, 15 |
| Cloud SQL for SQL Server | 2016, 2017, 2019, 2022 |
| AlloyDB for PostgreSQL | Supported |
| Self-managed MySQL | Via the Datastream JDBC/agent |
| Self-managed PostgreSQL | Via the Datastream JDBC agent |
| Self-managed Oracle | Via the Datastream agent |
| Salesforce | SaaS source |
| ServiceNow | SaaS source |

**Destinations**:

| Destination | Shape |
|---|---|
| BigQuery | Appends into a dataset with a per-source change table |
| Pub/Sub | Publishes change events as JSON messages |
| Cloud Storage | Writes change records as files (Hive-compatible layout) |
| Bigtable | Writes change events |
| Oracle (alloydb) | Writes to AlloyDB |
| Kafka/Confluent | Via a sink |
| Elastic | Via a sink |

**Google-managed sources** (Cloud SQL, AlloyDB) use a **server-side, log-based** path — no agent, no separate VM, no agent to babysit. **Self-managed sources** require the **Datastream JDBC agent**, a set of processes you run on-premises or in your VPC. The agent is an operational liability: it must be patched, it holds credentials, and it is a single point of failure if you run one.

**The Cloud SQL requirement that trips people up:** for MySQL, `binlog_format` must be `ROW` and `binlog_row_image` must be `FULL` (the default) — `MINIMAL` omits unchanged columns, which breaks change capture. For PostgreSQL, you must set `wal_level=logical` and `max_replication_slots` and `max_wal_senders` high enough for the number of slots. **Changing `wal_level` requires a database restart** — plan that, and confirm `max_replication_slots` before you need it, because a missing replication slot blocks the slot creation.

### The change stream

Every change event carries three things:

1. **The operation type**: `INSERT`, `UPDATE`, or `DELETE`.
2. **The row values**: before, after, or both.
3. **The CDC metadata**: the log position, the commit timestamp, the transaction ID, and the source object name.

**How UPDATE is represented** depends on the destination and is worth being precise about:

- **MySQL binlog ROW format** emits a `UPDATE_ROWS` event containing **both the before-image and the after-image**. The before-image is the row as it was; the after-image is the row as it is now.
- **PostgreSQL logical decoding** (and `REPLICA IDENTITY FULL`) also gives before and after. With the default `REPLICA IDENTITY DEFAULT`, only the **key columns** appear in the before-image — the full prior values are not available unless you set `REPLICA IDENTITY FULL`.
- **Oracle** LogMiner gives the full before and after.

The practical impact: **for audit-grade history and for slowly-changing-dimension (SCD) type-2 tables, you need before-images.** If your CDC source does not provide them, you cannot build type-2 SCD from CDC alone — you would need to snapshot the table and diff it.

The BigQuery destination model is specific and important:

- Datastream creates a **change table** per captured table, and each change table has a special **`ModDate` partition column** whose value is the **CDC commit timestamp**. This is how Datastream makes the data partitionable — and it is why you get *arrival-time* partitioning, not event-time partitioning, out of the box.
- The change table also has a **`change_type` column** with values `INSERT`, `UPDATE`, `DELETE`, and `INSERT` (for the initial snapshot, which is also marked `INSERT` with a special flag).
- **The initial snapshot and the subsequent change stream are combined into the same table.** This is the snapshot + change stream consistency model.

**The snapshot + change stream consistency mechanism.** When a stream starts:

1. Datastream establishes a consistent position in the source log.
2. It performs the **initial snapshot** — reading all existing rows. This is written with `change_type = INSERT`.
3. **Changes that occur during the snapshot are captured concurrently and buffered.**
4. The buffer is applied **after** the snapshot completes.

This means the snapshot and the change stream are **consistent**: no change is lost between the snapshot read and the start of the change stream. This is the same technique used by `VACUUM` in PostgreSQL and by MySQL's `START TRANSACTION WITH CONSISTENT SNAPSHOT`.

But note the ordering guarantee you get and the one you do not:

- **You get**: every row that existed at snapshot time is present, and every change after the snapshot position is present.
- **You do not get**: the snapshot rows and the change rows are not in one globally ordered sequence. The snapshot rows carry their original table state; the change rows carry post-snapshot states. If you `SELECT` the change table and see both an `INSERT` from the snapshot and a later `UPDATE` for the same key, you must apply them in order to get the current state — and the ordering is by `ModDate`, then by the CDC metadata, which is why Datastream exposes a `commit_timestamp` for tie-breaking.

**The critical gotcha: `UPDATE` does not mean "the row is now this".** A change table is a *log of changes*. The current state of a row is:

```sql
-- Last-writer-wins reconstruction of current state
SELECT * EXCEPT(row_number) FROM (
  SELECT t.*, ROW_NUMBER() OVER (
    PARTITION BY your_business_key
    ORDER BY ModDate DESC, commit_timestamp DESC
  ) AS row_number
  FROM `project.dataset.your_table_change_stream`
  WHERE change_type IN ('INSERT', 'UPDATE')
) WHERE row_number = 1;
```

If you forget the `DELETE` filter and the `ROW_NUMBER`, you will double-count. This is the most common Datastream mistake.

### Cloud SQL to BigQuery: the canonical flow

This is the flow the certification expects you to be able to build.

```bash
# 1. Enable binlog on the Cloud SQL instance
gcloud sql instances patch my-instance \
  --database-flags="binlog_format=ROW,binlog_row_image=FULL,log-bin-trust-function-creators=1"

# NOTE: log-bin is ON by default for Cloud SQL MySQL, but binlog_format
# defaults to STATEMENT. ROW is required for CDC.

# 2. Create the connection profile (contains the DB credentials)
gcloud datastream connection-profiles create mysql-cp \
  --location=us-central1 \
  --display-name="MySQL connection" \
  --mysql-host=10.0.0.5 --mysql-port=3306 \
  --mysql-username="cdc_user" \
  --mysql-password="..." \
  --network=projects/my-project/global/networks/default

# 3. Create the stream (source + destination + objects to capture)
gcloud datastream streams create mysql-to-bq \
  --location=us-central1 \
  --display-name="MySQL to BigQuery" \
  --source-config=mysql-cp \
  --destination-config=bigquery \
  --backfill-all=TABLE \
  --backfill-include-tables=orders,customers \
  --include-tables=orders,customers

# 4. Create the stream job (mapping + options)
gcloud datastream stream-jobs create orders-job \
  --stream=mysql-to-bq \
  --display-name="Orders" \
  --destination-config=bigquery \
  --bigquery-dataset=analytics \
  --bigquery-table=orders_change_stream

# 5. Run it
gcloud datastream stream-jobs run orders-job
```

**The critical BigQuery configuration detail:** the change table is partitioned by `ModDate`, and the `ModDate` value is the **CDC commit timestamp, which is the *source* commit time, not the arrival time at BigQuery**. So the partition reflects when the change happened in the source database. This means late-arriving changes land in the correct historical partition — which is exactly what you want for restating historical aggregates.

However, the **`ModDate` partition is the commit timestamp of the source**, and Datastream's own arrival latency means a change committed at 14:00 might be written to BigQuery at 14:00:30. If your dashboard query reads "today's partition", it will change as the partition fills. For a stable, monotonically-growing read, partition by an ingestion-time column instead — which means adding your own `_ingest_time` column in a downstream transform.

### Cloud SQL to Pub/Sub: the canonical flow

This is the flow for a real-time system — a Dataflow pipeline consuming change events, a fraud model, a live cache.

```bash
gcloud datastream connection-profiles create mysql-cp \
  --location=us-central1 --display-name="MySQL connection" \
  --mysql-host=10.0.0.5 --mysql-port=3306 \
  --mysql-username="cdc_user" --mysql-password="..." \
  --network=projects/my-project/global/networks/default

gcloud datastream streams create mysql-to-ps \
  --location=us-central1 --display-name="MySQL to Pub/Sub" \
  --source-config=mysql-cp \
  --destination-config=pubsub \
  --pubsub-topic=projects/my-project/topics/orders-changes \
  --include-tables=orders

gcloud datastream stream-jobs create orders-job \
  --stream=mysql-to-ps \
  --display-name="Orders to Pub/Sub" \
  --destination-config=pubsub \
  --pubsub-topic=projects/my-project/topics/orders-changes
```

**The Pub/Sub message shape.** Each message's data is JSON containing the change metadata and the row:

```json
{
  "data": {
    "columns": [
      {"name": "order_id", "type": "int64", "value": "10042"},
      {"name": "status", "type": "string", "value": "SHIPPED"},
      {"name": "total", "type": "double", "value": "249.99"}
    ],
    "modDate": "2026-01-15T14:00:00Z",
    "sourceMetadata": {
      "sourceType": "MYSQL",
      "sourceName": "orders",
      "sourceSchema": "shop"
    },
    "cdcOperation": "UPDATE",
    "commitTimestamp": "2026-01-15T14:00:02Z"
  }
}
```

Three things to notice, and they matter:

1. **Values are strings**, even for numeric types. You must cast. This trips up every new user — `total` arrives as `"249.99"`, and summing it without a cast gives a type error or a zero.
2. **`cdcOperation` distinguishes INSERT / UPDATE / DELETE.** For a `DELETE`, the `columns` array holds the **before-image** — the row as it was before deletion. This is how you learn what was deleted.
3. **`commitTimestamp` and `modDate` are the source-side times.** Use `commitTimestamp` for ordering; `modDate` is the partition key.

**Pub/Sub delivery and CDC semantics compose badly if you ignore them.** Datastream publishes to Pub/Sub, and Pub/Sub is at-least-once. So your consumer will see the same change more than once. **The CDC metadata is your dedup key** — `commitTimestamp` plus the source object name plus the primary key is deterministic and unique per change. This is the same principle as the project's `dedup_key`, and it is the reason `dedup_key` is built from data rather than from arrival time.

### Cost control and the idle-stream trap

Datastream is priced per component, and the components have different lifetimes:

| Component | Unit price | What drives it |
|---|---|---|
| CDC processing | $0.0000075 per **row change** | Volume of changes |
| Stream | $0.015 per **stream-hour** | Streams × hours running |
| Active CDC slots | $0.20 per **CDC slot-hour** | Slots on the source |
| Snapshots | $0.02 per GB | One-off snapshot cost |
| BigQuery destination | Standard BQ costs | Bytes written |

```python
import sys
sys.path.insert(0, "project/core")

from cost_model import DATASTREAM_PER_CDC_ROW, DATASTREAM_PER_STREAM_HOUR, estimate

# 1M row changes/day, one stream, 24/7
row_changes = 1_000_000 * 30
est = estimate("datastream", rows=row_changes, stream_hours=24 * 30)
for line in est.lines:
    print(f"  {line.label:<16} {line.quantity:>14,.0f} {line.unit:<14} ${line.cost:>10,.2f}")
print(f"  {'TOTAL':<16} {'':>14} {'':<14} ${est.total:>10,.2f}")
```
Expected output:

```text
  CDC processing       30,000,000 row            $    225.00
  Streams                     720 stream-hour    $     10.80
  TOTAL                                          $    235.80
```

**The idle-stream trap, stated precisely:**

A Datastream **stream** is a continuously running object. The `$0.015/stream-hour` charge accrues **whether or not the stream job is running and whether or not any data flows**. A stream with a stream job that has not been run in three months still bills $0.015/hour for every hour it exists.

The same applies to the **active CDC slot**: it occupies a slot on the source database the entire time the stream exists, not just while a job runs.

The trap in practice: teams create a stream per environment and per migration experiment, run the job once to validate, and then leave the stream running. Six environments × two databases × 24 × 30 hours × $0.015 = about $130/month of pure idle cost, plus the CDC slot charges, plus the source database's own resource consumption from the replication slot.

**The fix:** delete streams you are not using, and check for them monthly:

```bash
gcloud datastream streams list --location=us-central1
gcloud datastream stream-jobs list --stream=mysql-to-bq --location=us-central1

# Delete the stream, which also releases the CDC slot on the source
gcloud datastream streams delete mysql-to-bq --location=us-central1 --force
```

**The second cost trap: the snapshot.** The initial snapshot reads the entire table and writes every row to the destination. For a 500 GB table that is a 500 GB BigQuery load — charged at BigQuery ingestion rates, plus $0.02/GB for the snapshot itself, plus the BigQuery storage. It is a one-off cost, but it is a large one, and it is billed to the month you run it. Plan for it, and consider running the snapshot separately from the change stream if the table is enormous.

**The third trap: CDC row changes are not the same as rows.** An `UPDATE` counts as one row change. A `DELETE` counts as one. A single row updated 100 times counts as 100. **A hot table with frequent updates is far more expensive than its size suggests.** Cost per change, not per byte.

### Datastream versus alternatives

**Datastream** — Google-managed CDC for Google-managed databases.

- Pros: no agent to operate for Cloud SQL / AlloyDB sources; log-based (no polling load on the source); snapshot + change stream consistency built in; supports both BigQuery and Pub/Sub destinations; integrates with Dataflow.
- Cons: another proprietary service in the estate; per-row-change pricing can exceed alternatives at high change volumes; the source database must be configured for logical replication, and `wal_level` changes need a restart; limited to the supported source list.

**Fivetran-style SaaS connectors** — a managed connector product sold by a third party (Fivetran, Airbyte, Striim).

- Pros: extremely broad source coverage (hundreds of SaaS systems, which Datastream barely touches); mature, opinionated schema mapping; good normalisation into a common model; typically lower per-row pricing.
- Cons: **data leaves your GCP project and travels to the vendor's infrastructure and then back** — a material data-residency and compliance decision, and often a violation of your data-processing agreements; a recurring per-connector subscription; limited integration with BigQuery-specific features.

The GCP-native equivalent is **BigQuery Data Transfer Service** (covered in the next chapter), which is Datastream's batch-oriented cousin and keeps data in-project.

**Writing your own CDC** — using Debezium, LinkedIn's change-data-capture library.

- Pros: open source, no per-change fee, no data leaves your environment, full control over the transformation; Debezium integrates with Kafka and with Pub/Sub via the Debezium Pub/Sub connector; supports more databases than Datastream.
- Cons: **you now own an operational system**: connector deployment, schema history storage, offset management, upgrades, and on-call; Debezium's Postgres connector is famously sensitive to schema changes and can fail on `ALTER TABLE`; the Kafka (or Pub/Sub) infrastructure becomes a dependency you must run.

**My recommendation:** use Datastream for Cloud SQL and AlloyDB sources — it is genuinely less work and the log-based path is more efficient than anything you would deploy yourself. Use a SaaS connector (or BigQuery DTS) for SaaS sources where there is no Google-managed path. Reach for Debezium only when you need a source Datastream does not support, when data residency forbids a third-party connector, or when the per-row-change economics make Datastream indefensible at your volume.

---

## 🛠️ Hands-On

### Lab 1 — Model the change stream and reconstruct current state

This is the core Datastream skill: applying a change log to get current state.

```python
from dataclasses import dataclass


@dataclass
class ChangeEvent:
    operation: str      # INSERT | UPDATE | DELETE
    key: str
    values: dict[str, str]
    commit_ts: str


# A change stream for one order: snapshot INSERT, then two UPDATEs, then DELETE.
stream = [
    ChangeEvent("INSERT", "10042", {"status": "CREATED", "total": "100.00"}, "2026-01-15T13:00:00Z"),
    ChangeEvent("UPDATE", "10042", {"status": "PAID", "total": "100.00"}, "2026-01-15T13:05:00Z"),
    ChangeEvent("UPDATE", "10042", {"status": "SHIPPED", "total": "249.99"}, "2026-01-15T14:00:00Z"),
    ChangeEvent("DELETE", "10042", {"status": "SHIPPED", "total": "249.99"}, "2026-01-15T15:00:00Z"),
]


def current_state(events: list[ChangeEvent]) -> list[dict[str, str]]:
    """Reconstruct current state from a change stream (last-writer-wins)."""
    state: dict[str, dict[str, str]] = {}
    for event in sorted(events, key=lambda e: e.commit_ts):
        if event.operation == "DELETE":
            state.pop(event.key, None)
        else:
            state[event.key] = dict(event.values)
    return list(state.values())


result = current_state(stream)
print(f"changes in stream: {len(stream)}")
print(f"rows in current state: {len(result)}")
print(f"state: {result}")
```

Expected output:

```text
changes in stream: 4
rows in current state: 0
state: []
```

Four changes, zero surviving rows. The `DELETE` removed the row. Now remove the DELETE and see why the naive "last value wins" is wrong:

```python
from dataclasses import dataclass


@dataclass
class ChangeEvent:
    operation: str      # INSERT | UPDATE | DELETE
    key: str
    values: dict[str, str]
    commit_ts: str


# The same change stream as Lab 1, repeated here so this block runs alone.
stream = [
    ChangeEvent("INSERT", "10042", {"status": "CREATED", "total": "100.00"}, "2026-01-15T13:00:00Z"),
    ChangeEvent("UPDATE", "10042", {"status": "PAID", "total": "100.00"}, "2026-01-15T13:05:00Z"),
    ChangeEvent("UPDATE", "10042", {"status": "SHIPPED", "total": "249.99"}, "2026-01-15T14:00:00Z"),
    ChangeEvent("DELETE", "10042", {"status": "SHIPPED", "total": "249.99"}, "2026-01-15T15:00:00Z"),
]

# The naive mistake: ignoring the DELETE leaves a phantom row.
naive = {e.key: e.values for e in sorted(stream, key=lambda e: e.commit_ts)}
print(f"naive (ignoring DELETE): {naive}")

# And ignoring operation types entirely double-counts on a naive SUM.
total = sum(float(e.values["total"]) for e in stream)
print(f"naive SUM of all changes: {total}")
```

Expected output:

```text
naive (ignoring DELETE): {'10042': {'status': 'SHIPPED', 'total': '249.99'}}
naive SUM of all changes: 699.98
```

The naive sum is $699.98 for a single order worth $249.99. **This is exactly the bug that happens when someone sums a change table directly**, and it is why the `WHERE change_type IN ('INSERT','UPDATE')` + `ROW_NUMBER()` pattern exists.

### Lab 2 — Simulate the snapshot + change stream consistency model

```python
from dataclasses import dataclass, field


@dataclass
class Table:
    rows: dict[str, dict[str, str]] = field(default_factory=dict)


@dataclass
class Datastream:
    table: Table
    snapshot_rows: list[str] = field(default_factory=list)
    buffered_changes: list[tuple[str, str, dict[str, str]]] = field(default_factory=list)
    applied_changes: list[tuple[str, str, dict[str, str]]] = field(default_factory=list)

    def start(self) -> None:
        """Take the snapshot AND capture the log position."""
        self.snapshot_rows = sorted(self.table.rows)

    def capture(self, op: str, key: str, values: dict[str, str]) -> None:
        """A change arrives; buffer it if the snapshot has not finished."""
        self.buffered_changes.append((op, key, values))

    def finish_snapshot(self) -> None:
        """Apply buffered changes after the snapshot, preserving log order."""
        self.applied_changes = list(self.buffered_changes)

    def apply(self) -> None:
        for op, key, values in self.applied_changes:
            if op == "DELETE":
                self.table.rows.pop(key, None)
            else:
                self.table.rows[key] = values


# The source table at snapshot time.
table = Table({
    "A": {"status": "NEW"},
    "B": {"status": "NEW"},
})

ds = Datastream(table=table)
ds.start()

# A write happens DURING the snapshot. It must not be lost.
ds.capture("UPDATE", "A", {"status": "PAID"})
ds.capture("INSERT", "C", {"status": "NEW"})

ds.finish_snapshot()
ds.apply()

print(f"snapshot rows  : {ds.snapshot_rows}")
print(f"buffered changes: {len(ds.buffered_changes)}")
print(f"final state    : {dict(sorted(table.rows.items()))}")
```

Expected output:

```text
snapshot rows  : ['A', 'B']
buffered changes: 2
final state    : {'A': {'status': 'PAID'}, 'B': {'status': 'NEW'}, 'C': {'status': 'NEW'}}
```

The `UPDATE` to `A` and the `INSERT` of `C` both survived — and `A` shows the post-change value, not the snapshot value. That is the consistency guarantee.

### Lab 3 — Log-position tracking with the rotation trap

```python
from dataclasses import dataclass


@dataclass
class LogPosition:
    file: str
    offset: int

    def key(self) -> str:
        return f"{self.file}:{self.offset}"


class BinlogReader:
    """A minimal MySQL binlog reader that handles file rotation."""

    def __init__(self, files: dict[str, list[tuple[int, dict[str, str]]]]) -> None:
        # file -> list of (offset, change)
        self.files = files
        self.position = LogPosition("", 0)

    def read_from(self, position: LogPosition) -> list[tuple[LogPosition, dict[str, str]]]:
        """Read every change strictly after `position`."""
        results: list[tuple[LogPosition, dict[str, str]]] = []
        started = position.file == ""
        for filename in sorted(self.files):
            if not started:
                if filename < position.file:
                    continue
                if filename == position.file:
                    for offset, change in self.files[filename]:
                        if offset > position.offset:
                            results.append((LogPosition(filename, offset), change))
                    continue
            for offset, change in self.files[filename]:
                results.append((LogPosition(filename, offset), change))
            started = False
        return results


logs = {
    "mysql-bin.000041": [(4, {"op": "INSERT", "id": "1"})],
    "mysql-bin.000042": [(4, {"op": "UPDATE", "id": "1"}),
                         (912, {"op": "INSERT", "id": "2"})],
}

reader = BinlogReader(logs)
start = LogPosition("mysql-bin.000041", 4)

print(f"stored position: {start.key()}")
for position, change in reader.read_from(start):
    print(f"  {position.key():<26} {change}")

# THE TRAP: storing only the offset, not the file.
numeric_only = LogPosition("", 4)
print("\nif you stored only the offset (4), you would replay:")
for position, change in reader.read_from(numeric_only):
    print(f"  {position.key():<26} {change}")
```
Expected output:

```text
stored position: mysql-bin.000041:4
  mysql-bin.000042:4         {'op': 'UPDATE', 'id': '1'}
  mysql-bin.000042:912       {'op': 'INSERT', 'id': '2'}

if you stored only the offset (4), you would replay:
  mysql-bin.000041:4         {'op': 'INSERT', 'id': '1'}
  mysql-bin.000042:4         {'op': 'UPDATE', 'id': '1'}
  mysql-bin.000042:912       {'op': 'INSERT', 'id': '2'}
```

Storing only the numeric offset replays the previous file's changes — duplicates you cannot detect by inspecting the offsets. This is why the log position is a composite `(file, offset)`.

### Lab 4 — Model the Pub/Sub delivery of change events and dedup

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import dedup_key, deduplicate, partition_for_event

# Change events as Pub/Sub would deliver them (values are strings!).
delivered = [
    {"event_id": "10042:2026-01-15T14:00:02Z", "event_dt": "2026-01-15T14:00:02+00:00"},
    {"event_id": "10043:2026-01-15T14:00:05Z", "event_dt": "2026-01-15T14:00:05+00:00"},
    {"event_id": "10042:2026-01-15T14:00:02Z", "event_dt": "2026-01-15T14:00:02+00:00"},
]
partition = partition_for_event(delivered[0]["event_dt"])
unique = deduplicate(delivered, partition=partition)
print(f"delivered={len(delivered)} unique={len(unique)}")
print(f"dedup key: {dedup_key('10042:2026-01-15T14:00:02Z', partition)}")
```

Expected output:

```text
delivered=3 unique=2
dedup key: 20260115:10042:2026-01-15T14:00:02Z
```

The key combines the source primary key with the CDC commit timestamp — deterministic per change, which is what makes at-least-once delivery safe.

### Lab 5 — Price the Datastream flows

```python
import sys
sys.path.insert(0, "project/core")

from cost_model import estimate

# Cloud SQL -> BigQuery: 1M row changes/day, one stream, always on.
bq = estimate("datastream", rows=1_000_000 * 30, stream_hours=24 * 30)
print("Cloud SQL -> BigQuery (30 days, 1M changes/day):")
for line in bq.lines:
    print(f"  {line.label:<16} {line.quantity:>14,.0f} {line.unit:<14} ${line.cost:>10,.2f}")
print(f"  {'TOTAL':<16} {'':>14} {'':<14} ${bq.total:>10,.2f}")
print()

# Same source, second destination -> a SECOND stream -> double the stream cost.
two_streams = estimate("datastream", rows=1_000_000 * 30, stream_hours=24 * 30 * 2)
print(f"adding a Pub/Sub destination (2 streams): ${two_streams.total:,.2f}")
print(f"the extra stream costs: ${two_streams.total - bq.total:,.2f}")

# The idle-stream trap: a stream with no data flowing still bills.
idle = estimate("datastream", rows=0, stream_hours=24 * 30)
print(f"\nidle stream, 1 month, zero rows: ${idle.total:,.2f}")
```
Expected output:

```text
Cloud SQL -> BigQuery (30 days, 1M changes/day):
  CDC processing       30,000,000 row            $    225.00
  Streams                     720 stream-hour    $     10.80
  TOTAL                                          $    235.80

adding a Pub/Sub destination (2 streams): $246.60
the extra stream costs: $10.80

idle stream, 1 month, zero rows: $10.80
```

### Lab 6 — Check the Datastream service entry

```python
import sys
sys.path.insert(0, "project/core")

from service_catalog import get_service, regions_for, services_by_category

service = get_service("datastream")
print(f"name      : {service.name}")
print(f"summary   : {service.summary}")
print(f"pricing   : {service.pricing_model}")
print(f"resources : {', '.join(service.key_resources)}")
print(f"regions   : {len(regions_for('datastream'))}")

for other in services_by_category("Streaming & Messaging"):
    print(f"  {other.id:<12} {other.pricing_model}")
```
Expected output:

```text
name      : Datastream
summary   : Change data capture from databases and SaaS into streaming sinks.
pricing   : Per CDC row-change processed plus per-stream-hour.
resources : Stream, Stream Job, Connection Profile, Event
regions   : 10
  datastream   Per CDC row-change processed plus per-stream-hour.
  kafka        Per GB ingested, per GB retained, and per cluster-hour.
  pubsub       Per GB of message data ingested, then per delivery.
```

---

## 🛠️ Common Errors and Fixes

### 1. `Could not fetch source schema` / stream creation fails on Cloud SQL MySQL

```text
ERROR: (gcloud.datastream.streams.create) INVALID_ARGUMENT:
Could not fetch source schema from the source database.
Underlying error: Access denied for user 'cdc_user'@'%'.
```

**Cause:** the connection profile credentials lack `REPLICATION CLIENT`, `REPLICATION SLAVE`, and `SELECT` privileges. The Datastream service account needs these to read the binlog and the table metadata.

**Fix:** grant the minimum set. The canonical grant is:

```sql
GRANT SELECT ON shop.* TO 'cdc_user'@'%';
GRANT REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 'cdc_user'@'%';
FLUSH PRIVILEGES;
```

### 2. The stream does not capture changes — the binlog format is wrong

**Symptom:** the stream starts, the snapshot completes, and then nothing arrives. No error, no changes.

**Cause:** `binlog_format` is `STATEMENT` (the MySQL default) or `binlog_row_image` is `MINIMAL`. With `STATEMENT`, the binlog contains SQL statements, not row images — Datastream cannot reconstruct row-level changes. With `MINIMAL`, unchanged columns are omitted, so before-images are incomplete.

**Fix:** set `ROW` and `FULL`. This requires an instance restart.

```bash
gcloud sql instances patch my-instance \
  --database-flags="binlog_format=ROW,binlog_row_image=FULL"
# Restart is required:
gcloud sql instances restart my-instance
```

### 3. `Replication slot "pgdatastreamreplslot" already exists` or `max_replication_slots` exhausted

```text
ERROR: 54000: sorry, too many clients already
ERROR: could not create replication slot "pgdatastreamreplslot"
```

**Cause:** PostgreSQL's `max_replication_slots` (default 10) is exhausted, or a previous Datastream stream left a slot behind when it was deleted without cleaning up.

**Fix:** raise the limit and clean up orphaned slots.

```sql
SELECT slot_name, active, restart_lsn FROM pg_replication_slots;
SELECT pg_drop_replication_slot('pgdatastreamreplslot');
```

```bash
gcloud sql instances patch my-instance \
  --database-flags="max_replication_slots=25,max_wal_senders=25"
```

Also: `wal_level=logical` is required and **changing it requires a restart**. Verify before you create the stream, not after.

```sql
SHOW wal_level;   -- must be 'logical'
```

### 4. `Could not create stream: The source database is not in the same region as the stream`

```text
INVALID_ARGUMENT: The location of the connection profile must match
the location of the stream. Connection profile is in us-central1,
stream is in europe-west4.
```

**Cause:** the connection profile and the stream must be in the same location. The location also determines where the Datastream workers run and where the change stream flows.

**Fix:** create the profile in the same location as the stream.

```bash
gcloud datastream connection-profiles describe mysql-cp --location=us-central1
gcloud datastream connection-profiles create mysql-cp-eu4 \
  --location=europe-west4 --display-name="MySQL EU" \
  --mysql-host=10.0.0.5 --mysql-port=3306 ...
```

### 5. `Invalid resource state: Stream is in the RUNNING state` / `Stream job is not in the right state`

```text
FAILED_PRECONDITION: The stream job can only be run when the stream
is in the RUNNING state. Current state: PENDING.
```

**Cause:** you issued `stream-jobs run` before the stream finished validating its source connection and creating the CDC slot.

**Fix:** wait for the stream to reach `RUNNING` before running the job. Check the state first.

```bash
gcloud datastream streams describe mysql-to-bq --location=us-central1 \
  --format="value(state)"
gcloud datastream stream-jobs describe orders-job --location=us-central1 \
  --format="value(state,percentComplete)"
```

### 6. Duplicate rows in the BigQuery change table

**Symptom:** the same change appears twice in the change table, with the same `ModDate` and the same values.

**Cause:** the stream job was run twice against the same destination, or a job was interrupted and re-run. Datastream's snapshot/change-stream machinery is idempotent *within a run*, but re-running a job against an existing destination can append again.

**Fix:** delete and recreate the destination change table before a re-run, or query defensively with a deduplication:

```sql
SELECT * EXCEPT (rn) FROM (
  SELECT t.*,
         ROW_NUMBER() OVER (
           PARTITION BY order_id, ModDate, commit_timestamp
           ORDER BY ModDate DESC
         ) AS rn
  FROM `analytics.orders_change_stream`
) WHERE rn = 1;
```

### 7. The BigQuery change table has no rows despite an active stream

**Cause:** the stream job was created but never run, or the backfill was scoped to tables you are not querying.

**Fix:** check the job state and the captured table list.

```bash
gcloud datastream stream-jobs describe orders-job --location=us-central1 \
  --format="value(state,destinationConfig.bigqueryDataset)"
gcloud datastream stream-jobs run orders-job --location=us-central1
```

---

## 💡 Production Notes

- **CDC reads the write-ahead log; never poll a timestamp column.** A `updated_at` cursor ties on equal timestamps, misses deletes entirely, and loses the before-image. This is the single biggest correctness decision in CDC.

- **Store the log position as a composite `(file, offset)`, not a number.** MySQL binlog rotation resets the offset; a numeric-only position silently replays a whole file of changes.

- **Count cost per row change, not per row or per byte.** A row updated 100 times costs 100 row changes. Hot tables are the ones that hurt.

- **Delete unused streams and audit them monthly.** A stream bills $0.015/hour and occupies a CDC slot whether or not it is running. The idle-stream cost is small per stream and invisible until you have twenty of them.

- **Every CDC destination needs an idempotent write.** Datastream to Pub/Sub is Pub/Sub's at-least-once delivery; the CDC metadata (`commit_timestamp` + primary key) is your deterministic dedup key.

- **Reconstruct current state with `ROW_NUMBER()` filtered to `change_type IN ('INSERT','UPDATE')`.** Summing a change table directly double-counts every updated row. This is the most common Datastream query bug.

- **Test `wal_level`, `binlog_format`, and `max_replication_slots` before creating the stream.** Two of these require a database restart, and restarting a production Cloud SQL instance to change `wal_level` is a scheduling conversation, not a task.

- **Choose the destination deliberately.** BigQuery if the consumer is analytics and you want `ModDate` partitioning. Pub/Sub if the consumer is a real-time system. Both means two streams, two slots, and double the stream charge — that is the price of the second destination, and it is worth paying explicitly rather than by accident.

- **Consider `REPLICA IDENTITY FULL` on PostgreSQL if you need before-images.** The default gives you only key columns in the before-image, which is not enough to build type-2 SCD or audit history.

---

## 🔑 Key Takeaways

- **The write-ahead log contains every change, in order, with before and after values.** Polling a timestamp column is not CDC: it ties, misses deletes, and loses history.
- The **log position is a composite `(file, offset)`** and must be monotonic, dense, and unambiguous. MySQL rotation is the trap that silently replays data.
- **Datastream = connection profile + stream (source→destination) + stream job (object mapping).** A stream is 1:1 with a source/destination pair; two destinations means two streams.
- The change stream carries **INSERT / UPDATE / DELETE**, the row values, and CDC metadata (log position, commit timestamp, transaction ID).
- **Snapshot + change stream is consistent**: changes during the snapshot are buffered and applied after it, so nothing is lost and nothing is double-applied.
- **The BigQuery change table is a log, not a table of current state.** Reconstructing current state requires `ROW_NUMBER()` over `change_type IN ('INSERT','UPDATE')`; a naive SUM double-counts.
- **Pub/Sub values arrive as strings**, even for numbers. Cast them.
- **Cost is per row change plus per stream-hour plus per CDC slot-hour**, plus a one-off snapshot charge. Idle streams bill forever.
- **Datastream for Cloud SQL / AlloyDB**, BigQuery DTS or a SaaS connector for SaaS sources, Debezium when you need coverage Datastream lacks or data residency forbids a third party.
- A **Fivetran-style connector sends your data to a third party and back** — that is a compliance decision before it is a technical one.

---

## 📚 Practice Exercises

1. **Change-stream reconstruction.** Extend Lab 1 to handle a stream with interleaved keys, multiple UPDATEs per key, and a re-insert after a delete. Verify your reconstruction against a hand-computed expected state, and add a check that the final state matches the source table.

2. **Snapshot consistency proof.** Extend the Lab 2 simulation to interleave 100 random changes across the snapshot boundary, with random operation types, and assert that the final state always equals applying every captured change to the snapshot state. Include the case where a key is deleted then re-inserted.

3. **Log-position comparison.** Implement a `TimestampPosition` class alongside the `LogPosition` class and show, with a concrete example, how a timestamp cursor both misses a change (two changes with the same timestamp) and duplicates one (a change whose clock value went backwards). Explain what each failure does to your downstream totals.

4. **BigQuery change-table query.** Write the three queries you need in production: (a) current state per key, (b) the full history of one key in chronological order, (c) net revenue impact including deletes. Test them against a synthetic change table you build in Python.

5. **Datastream cost model.** Extend Lab 5 to model a table with 100M rows where 5% are updated hourly. Compare the annual cost against a nightly `updated_at` poll into BigQuery, and identify the break-even update frequency at which Datastream becomes cheaper.

6. **Source configuration audit.** Write a shell script that checks a Cloud SQL MySQL instance for the required CDC settings (`binlog_format`, `binlog_row_image`, `log_bin`) and a Cloud SQL PostgreSQL instance for `wal_level` and `max_replication_slots`, printing PASS/FAIL per check and the exact remediation command for each failure.

7. **Destination selection.** For each of four workloads, choose BigQuery or Pub/Sub as the Datastream destination and justify with the latency requirement, the consumer type, and the cost: (a) a nightly revenue report, (b) a fraud model scoring in 200 ms, (c) a search index, (d) a data lake landing zone.

8. **CDC dedup at the sink.** Using the `dedup_key` pattern from `project/core/pipeline_logic.py`, write the BigQuery `MERGE` statement and the dedup query for a change stream landing in a `ModDate`-partitioned table, and prove idempotency by applying the same change three times.

---

## 📖 Further Reading

- [Datastream Documentation — Overview](https://docs.cloud.google.com/datastream/docs/overview)
- [Datastream Documentation — Creating a Stream](https://docs.cloud.google.com/datastream/docs/create-a-stream)
- [Datastream Documentation — Stream Jobs](https://docs.cloud.google.com/datastream/docs/run-a-stream)
- [Datastream Documentation — Change Data Capture Overview](https://docs.cloud.google.com/datastream/docs/behavior-overview)
- [Datastream Documentation — Supported Sources](https://docs.cloud.google.com/datastream/docs/sources)
- [Datastream Pricing](https://docs.cloud.google.com/datastream/pricing)
- [MySQL Binary Log Formats and the ROW Requirement](https://dev.mysql.com/doc/refman/8.0/en/binary-log-formats.html)
- [PostgreSQL Logical Replication and `REPLICA IDENTITY`](https://www.postgresql.org/docs/current/logical-replication.html)
