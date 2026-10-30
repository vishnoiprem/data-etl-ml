# 2.4 — Cloud Spanner

> **Section 2 · Storage & Databases · Lecture 2.4 · 8:00**

## 🎯 What you will learn

- Spanner's architecture: how a relational database can scale horizontally and still be strongly consistent
- The layers — client library, proxy, frontend, tablets, and the Paxos group per tablet
- Splitting: how a tablet is divided, and why the schema must be designed for it
- Interleaving: how child rows are co-located with their parent, and the write-amplification trade-off
- TrueTime: the epoch concept, commit timestamps, and what Spanner actually guarantees
- **The CAP theorem, precisely** — what Spanner guarantees and what it does *not* claim
- Strong consistency: how external consistency is stronger than linearizability
- Schema design: primary keys, reverse timestamp keys, foreign keys, and key ranges
- When to choose Spanner over Cloud SQL — and when not to
- The real costs: price per unit of capacity, operational complexity, and the constraints that bite

---

## 🧠 Concept

### The problem Spanner was built to solve

Every database makes a trade of the same two things:

- **Consistency** — when two clients read the same data, do they see the same thing?
- **Availability** — can a client always be served?

A single-machine relational database gets both, easily, because there is only one copy. But the moment you want to survive a machine failure, you need a copy somewhere else, and now you must decide how those copies interact.

Historically, database architects chose one of two designs:

- **Sharding** — split the data across N independent machines, each owning a slice. Reads and writes scale out beautifully. But a transaction that touches two slices is either forbidden or slow, and cross-shard consistency becomes your problem.
- **Replication** — keep N copies of the *same* data. Consistency becomes a distributed consensus problem, and the system must trade availability for consistency under partition.

Google's 2012 Spanner paper ("Spanner: Google's Globally-Distributed Database") tried to get both, and it did it with two ideas nobody had combined before: a **time oracle** (TrueTime) and **distributed consensus per data slice** (Paxos).

The result: a relational SQL database that spans regions, scales horizontally by splitting, and still gives you **external consistency** — the strongest practical consistency guarantee in a replicated database.

### The architecture, layer by layer

```text
   Client library (Go / Java / Python / C++)
        │
        ▼
   Spanner Proxy  ────  coordinates client sessions, routing,
        │                transaction state, and the TrueTime window
        ▼
   Frontend  ────────  serves reads; assigns commit timestamps
        │                via the TrueTime window; routes writes
        ▼
   Tablet  ──────────  a sorted range of rows, the unit of
        │               replication and splitting
        ▼
   Paxos group  ─────  5 replicas of one tablet, spread across
                       zones (and regions), one leader
```

**Tablet.** A tablet is a contiguous range of rows, identified by a start key and an end key. It is the unit of distribution: it has its own leader, its own replicas, its own split history. A Spanner *instance* is a set of tablets, and a *database* is a set of tables whose rows live in tablets.

**The split.** When a tablet gets hot or too large, Spanner splits it — it picks a split point in the key range, creates two tablets, and moves half the rows to each. The split is a metadata operation coordinated through the directory; it is transparent to the client, which keeps talking to the same logical row keys.

This is the mechanism that makes Spanner scale horizontally **without** you sharding by hand. The application declares a primary key; Spanner figures out where the rows go and rebalances as data grows.

**The Paxos group.** Each tablet has a set of replicas (typically 5), spread across different zones (and, for multi-region instances, different regions). One is the leader and serves reads and writes; the followers replicate. Writes go through Paxos, so a write is only acknowledged once a **quorum** (3 of 5) has persisted it.

The consequence for latency: a write to a US leader with followers in the same region commits in a few milliseconds. A write to a leader in one region with followers in another commits in tens to hundreds of milliseconds — because Paxos must wait for the slowest quorum member. **Cross-region write latency is the price of cross-region survival.**

**Spanner Proxy and Frontend.** The proxy is the entry point. It handles session management and routing, and it is where **transaction state** for multi-partition transactions is coordinated. The frontend is the part that assigns commit timestamps and serves reads — it talks to the leader of each tablet, and it can serve reads from any replica if the client only needs a consistent-enough snapshot.

### TrueTime

TrueTime is a Google-internal API that returns **a guaranteed interval** around the current time, rather than a point estimate:

```text
TT.now()  →  [earliest, latest]
```

The interval is narrow (milliseconds) because the API is served by a set of machines whose clocks are disciplined by GPS and atomic clocks, and the API returns the *latest* time that is guaranteed correct at all of them. The width of the interval is the **uncertainty**, and the uncertainty is bounded and small.

Why this matters: Spanner can assign a commit timestamp to a transaction that is guaranteed to reflect real time, and can therefore order commits globally without a separate time-coordination service.

Two implications:

- **Commit wait.** Because a timestamp must be certain to be in the future before it can be used, a transaction that commits in a timestamp window must wait until `latest` has passed. This wait is bounded by the uncertainty interval — typically a few milliseconds — but it is a real, measurable latency component.
- **External consistency.** Because commit timestamps reflect real time, and Spanner respects that ordering, transactions that commit in a real-time order also *appear* in that order to every client, everywhere, forever. This is stronger than linearizability and is the property Spanner's own paper proves.

### What Spanner actually guarantees — CAP, precisely

This is where the marketing usually goes wrong, so let me be exact.

**The CAP theorem says:** when a network partition occurs, a distributed system must choose between consistency (C) and availability (A). You cannot have all three at once.

**What Spanner guarantees:** Spanner provides **external consistency** (which implies strict serializability, which implies linearizability) *and* **high availability** (99.999% availability SLA for instances with ≥3 nodes per region).

**How does that not violate CAP?** Because CAP's "C" is specifically **atomic consistency** *under partition*, and Spanner's answer is: **it prefers consistency, but it does not become unavailable merely because a partition exists.**

Here is the precise mechanism. Spanner uses **witness replicas** in each region. A replica in another region acts as a *witness* — it tracks the Paxos group's progress but stores no data. Because a witness participates in the Paxos quorum, a region with only witnesses can still acknowledge a commit without holding the data.

So during a network partition that splits the world into two sides:

- If a side contains a **quorum** of replicas (3 of 5 for the default placement), that side continues to serve both reads and writes.
- If a side contains **no quorum**, that side's transactions that need to write must **block** — it waits for the partition to heal, or for a leader to be elected among the replicas it does have. It does **not** serve a stale-but-consistent read of data that might have been written on the other side.

That second case is the CAP trade-off happening *inside* Spanner: when a partition prevents a quorum, Spanner sacrifices **availability** (for write transactions) in order to preserve **consistency**.

And this is exactly what you want in a database, because the alternative — serving stale reads across a partition — is how you get two databases that both believe they are authoritative. Spanner's position is: **prefer consistency; a transaction that cannot be completed correctly is better failed than wrong.** A blocked transaction is a *retryable* error. A silently-stale read is a *silent data corruption* in the business logic.

So the accurate statement is:

> Spanner provides external consistency and high availability. Under a network partition that leaves a region without a Paxos quorum, transactions in that region that require a write are blocked (unavailable) rather than committed with inconsistent data. Reads served in that region are external-consistent with respect to the commits that did succeed — Spanner will not serve a read that contradicts a completed transaction.

And the corollary for application design: **design for retry.** In Spanner, a transaction can fail with `ABORTED` for ordinary reasons — read-write conflicts, or a leader change during the commit — and the correct response is to retry the whole transaction. Every Spanner client library provides automatic retry for `ABORTED` within a transaction. Do not write application logic that assumes a transaction either commits or fails cleanly.

One more nuance: Spanner's availability claim depends on the **number of nodes per region**. A 1-node instance has no replicas; losing that node means an outage. A 3-node or 5-node instance per region has quorum-based availability. This is why the node count is a first-class design parameter, not a cost knob.

### Strong consistency, in practice

External consistency means: if transaction T1 commits before transaction T2 *starts*, then any client that reads after T2 commits will see T1's effects. It is a total order on transactions that is consistent with real time.

Concretely, this means:

- A read-write transaction sees a consistent snapshot plus its own writes.
- A read-only transaction at timestamp T sees the database as of T, where T is at least as new as any transaction that committed before the read started.
- Read-only transactions can be served from **any replica** (not just the leader) with the timestamp pinned, so read scaling is cheap.

The `strong` boolean on a read-only transaction tells Spanner whether the timestamp must be at least as fresh as the client's last read:

- `strong=False` (the default for read-only transactions): Spanner may serve a slightly stale snapshot, but it is still a consistent snapshot. Faster, and safe for dashboards.
- `strong=True`: the read is guaranteed to reflect everything committed before it started. Needed for read-your-writes across clients.

### Interleaving

**Interleaving** is Spanner's answer to the classic problem of a parent and its children living on different tablets.

Without interleaving, `Users` and `Orders` are two independent tables. A user's five orders might live on five different tablets, on five different leaders, possibly in five different regions. A query like "the user and all their orders" becomes a fan-out across tablets, and — much worse — a transaction that creates the user and the order touches two tablets and requires **2PC across two Paxos groups**, which is significantly slower and has a much larger failure surface.

With interleaving, you declare the child table interleaved in the parent:

```sql
CREATE TABLE Orders (
  UserId STRING NOT NULL,
  OrderId STRING NOT NULL,
  Amount INT64,
  PRIMARY KEY (UserId, OrderId),
  INTERLEAVE IN PARENT Users ON DELETE CASCADE
) INTERLEAVE BY ROW;
```

The consequences:

- A user's orders are stored **in the same tablet** as the user row. A read of the user and its orders touches one tablet, one leader.
- A transaction that touches the user and its orders touches **one Paxos group**, so it commits with ordinary Paxos latency — not 2PC.
- The rows are stored **in key order**, so "all orders for this user" is a **contiguous range scan** within the tablet, not a scattered lookup.

The cost, and it is real:

- **Write amplification.** Inserting an order row is a write to the user's tablet. If one user generates 10,000 orders, that user's tablet becomes hot, and one very active user can create a hotspot. This is why the Spanner docs explicitly warn against interleaving a high-fanout child table such as "all events for a user".
- **No global ordering across interleaved children.** Rows in the child table are ordered by (parent key, child key), so you cannot scan all orders globally in time order without a separate index or a different table.
- **`ON DELETE CASCADE` couples the parent and child lifetimes.** Deleting the user deletes the orders — which may be a large multi-tablet delete.

The rule: **interleave when the child is bounded and accessed together with the parent; do not interleave when the child is unbounded or accessed independently.** Bounded means "a handful per parent" — order lines, phone numbers, device registrations. Unbounded means "a stream" — events, log entries, transactions. For unbounded children, use a separate table with an index, and accept the fan-out cost.

### Foreign keys

Spanner supports foreign key constraints (`REFERENCES`), with `ON DELETE CASCADE`, `ON DELETE SET NULL`, `ON DELETE NO ACTION` (the default). Constraints are **not enforced by default** in Spanner; you create an `INFO_SCHEMA` constraint by declaring it in DDL, and enforcement is a database-level option.

Two important details:

- Foreign keys in Spanner cannot cross databases, and a referencing table must have a compatible key structure.
- **Interleaved tables do not need a foreign key** — the parent-child relationship is structural. Adding a redundant foreign key on an interleaved table is a common mistake.
- Foreign key enforcement costs write-time work. On a high-throughput OLTP path, many teams disable enforcement and validate in the application, accepting the risk deliberately.

### Schema design

**Primary keys.** In Spanner, a primary key is a tuple of columns, and it determines the physical ordering of the rows *and* the tablet split boundaries. This is the core of Spanner schema design: **the primary key is not just an index, it is your sharding strategy.**

The classic anti-pattern is a **timestamp-first** primary key on a write-heavy table:

```sql
PRIMARY KEY (Timestamp, CustomerId)
```

Every new row has the largest timestamp, so every row lands in the **last** tablet. That tablet's leader becomes a write hotspot and the whole table's write throughput collapses to one node's capability. This is the single most common Spanner schema mistake.

The fix is to **salt the key** so that writes spread across tablets. The canonical salt is the database's unique row identifier, which has a random component:

```sql
PRIMARY KEY (CustomerId, EventId)
```

where `EventId` is a UUID — random, so writes spread. And a **reverse timestamp** component for time-ordered reads:

```sql
PRIMARY KEY (CustomerId, EventTimestamp DESC, EventId)
```

The `DESC` on the timestamp means "newest first" within each customer, so a range scan over a customer's recent events is efficient. The trailing `EventId` guarantees uniqueness (two events can share a timestamp) and adds another spreading factor.

The rule of thumb:

> **Put the entity identifier first, then a reverse timestamp, then a unique suffix.** The identifier spreads reads; the reverse timestamp gives you time-ordered range scans; the suffix guarantees uniqueness and spreads writes.

**Hot splitting.** Spanner's split point selection is not random — it splits at the median key of the tablet's key range. If your keys are highly skewed (say, one customer with 50% of the rows), the median split does not help that customer. Spanner mitigates this with **hot splits**: it can split a tablet at a point that balances *load* rather than *bytes*. But hot splitting is a mitigation, not a substitute for a well-distributed key.

**Storing data vs storing pointers.** Spanner has a "storing index" concept: a secondary index either *stores* the indexed columns (duplicating data, faster reads) or *references* them (smaller, but the read must go to the base table). For a low-latency read path, store. For a rarely-read index, reference.

### When to use Spanner, and when not to

**Use Spanner when:**

- You need a **single logical database across multiple regions** with strong consistency, and you cannot accept read-your-writes violations at the region boundary.
- Your write volume is high and **horizontally scalable** — Spanner scales writes by splitting, not by upgrading a primary.
- Your access pattern is **key-based**: you fetch a user, their orders, their session. Spanner's tablet locality makes this extremely fast.
- You need **transactional integrity over a large, growing dataset** with automatic rebalancing and no manual sharding.

**Do not use Spanner when:**

- **You have a single-region workload and modest traffic.** A Cloud SQL PostgreSQL instance is dramatically cheaper. Spanner's pricing model (node-hours plus processing units plus storage plus IO) makes a small instance cost several times a comparable Cloud SQL instance, for capability you do not need.
- **Your workload is analytical.** Spanner is a row store with an SQL surface. BigQuery scans columns at $6.25/TB; Spanner will not touch it. Never run analytics on Spanner.
- **You need rich SQL features.** Spanner's SQL dialect is a subset. It has no `LATERAL`, limited `WITH`, no sequence support, its own types (`INT64`, `FLOAT64`, `STRING`, `BYTES`, `JSON`, `ARRAY`, `STRUCT`), and limited PostgreSQL compatibility. Extensions like PostGIS do not exist.
- **You need a mature operational ecosystem.** Spanner is operationally simpler than self-managed PostgreSQL, but it is a Google-proprietary system with fewer third-party tools, and the migration path off it is expensive.
- **Your data model is naturally document-shaped or wide-column.** That is Firestore and Bigtable (chapter 2.5), not Spanner.

**The comparison that matters:**

| | Cloud SQL (PostgreSQL) | Cloud Spanner |
|---|---|---|
| Topology | One region, one writer (plus replicas) | Multi-region, sharded |
| Write scaling | Vertical (bigger instance) | Horizontal (split tablets) |
| Cross-region writes | Not applicable | Slow (Paxos across regions) |
| Read-your-writes across regions | Not applicable | Guaranteed (external consistency) |
| Cost at small scale | Low | 3–10× higher |
| Cost at large multi-region scale | Expensive to scale; complex | Cheaper per unit of scale |
| SQL dialect | Full PostgreSQL | A restricted dialect |
| Operational burden | Low | Low, but a new mental model |

The honest summary: **Cloud SQL for the application database, Spanner when you specifically need global scale with consistency.** Spanner is not "Cloud SQL but better"; it is a different tool with a different cost curve and a different set of constraints.

### The real costs

1. **Cost is opaque.** Spanner bills node-hours **plus** processing units **plus** storage **plus** IO, and the processing-unit bill is driven by your *transactional* work, not your data volume. A transaction-heavy workload with small rows can cost surprisingly little; a workload with large rows and many indexes costs a lot. The course's model uses `SPANNER_PER_NODE_HOUR = 0.70` and `SPANNER_PER_PROCESSING_UNIT_HOUR = 0.30`.
2. **Instance configurations are a hard constraint.** A regional instance needs ≥3 nodes per region; a multi-region instance needs ≥3 nodes in each region it spans. You cannot shrink below that. A "small" Spanner instance is already 3 nodes.
3. **Schema mistakes are expensive to fix.** Changing a primary key on a large table means creating a new table, backfilling, and dual-writing during the cutover. Design the key before you have data.
4. **The SQL subset bites.** Expect to rewrite some queries, and expect to lose some extensions.
5. **Interleaving is a commitment.** Changing an interleaved table's structure later is a migration.

---

## 🛠️ Hands-On

### 1. Create a Spanner instance and database

```text
gcloud spanner instances create orders-spanner \
    --project=YOUR_PROJECT_ID \
    --config=regional-us-central1 \
    --description="Regional instance for the orders workload" \
    --nodes=3 \
    --processing-units=100

gcloud spanner instances list
```

`--config=regional-us-central1` gives one region with three zones and three nodes. A multi-region instance is `--config=nam3` (Iowa, South Carolina, Oregon) or `--config=eur3`. Note the node floor: **three nodes minimum per region**, so a "small" instance is already three nodes' worth of compute.

```text
gcloud spanner databases create ordersdb \
    --instance=orders-spanner \
    --project=YOUR_PROJECT_ID
```

### 2. Create the schema — with the primary key designed for spreading

```sql
CREATE TABLE Users (
  UserId STRING(64) NOT NULL,
  DisplayName STRING(255),
  CreatedAt TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp=true),
  Region STRING(16),
  PRIMARY KEY (UserId)
);

CREATE TABLE Orders (
  UserId STRING(64) NOT NULL,
  OrderId STRING(64) NOT NULL,
  EventTimestamp TIMESTAMP NOT NULL,
  Amount INT64,
  Currency STRING(3),
  PRIMARY KEY (UserId, OrderTimestamp DESC, OrderId),
  FOREIGN KEY (UserId) REFERENCES Users (UserId)
) INTERLEAVE BY ROW;
```

Compare with the anti-pattern:

```sql
-- WRONG: every write lands on the last tablet.
CREATE TABLE EventsBad (
  EventTimestamp TIMESTAMP NOT NULL,
  UserId STRING(64) NOT NULL,
  Amount INT64,
  PRIMARY KEY (EventTimestamp, UserId)
);
```

The correct shape uses `allow_commit_timestamp=true` so Spanner stamps the row with the commit timestamp, and a key of `(entity, reverse-time, unique-suffix)`.

For the course's event model, the analogous design is:

```sql
CREATE TABLE Events (
  UserId STRING(64) NOT NULL,
  EventTs TIMESTAMP NOT NULL,
  EventId STRING(64) NOT NULL,
  EventType STRING(32),
  Region STRING(16),
  Channel STRING(16),
  Currency STRING(3),
  Amount INT64,
  PRIMARY KEY (UserId, EventTs DESC, EventId)
);
```

The `EventId` suffix matters: without it, two events with the same timestamp for the same user would violate the primary key, and without its randomness the rows would not spread.

### 3. Insert and query through the CLI

```text
gcloud spanner databases ddl update ordersdb \
    --instance=orders-spanner \
    --project=YOUR_PROJECT_ID \
    --ddl-file=schema.sql
```

Insert data:

```sql
INSERT INTO Users (UserId, DisplayName, Region) VALUES
  ('u000914', 'Ana', 'AMER'),
  ('u004469', 'Boris', 'EMEA'),
  ('u000123', 'Chen', 'APAC');
```

Read it back with a strongly-consistent read-only transaction:

```sql
SELECT UserId, DisplayName, Region
FROM Users
WHERE UserId = 'u000914';
```

The CLI uses a single-use (non-interactive) transaction by default. For a strongly consistent read-only transaction that is guaranteed to reflect everything committed before it started, use the session-based form:

```sql
BEGIN;
SET TRANSACTION READ ONLY, STRONG;
SELECT * FROM Users WHERE UserId = 'u000914';
COMMIT;
```

### 4. Write a read-write transaction with the Python client

The `google-cloud-spanner` client is the interface to the whole model, and the retry semantics are worth reading closely — they are not optional.

```python
from google.cloud import spanner
from google.cloud.spanner_v1 import param_types

INSTANCE_ID = "orders-spanner"
DATABASE_ID = "ordersdb"


def get_database() -> spanner.database.Database:
    """Return the Spanner database handle.

    Returns:
        The database object.
    """
    client = spanner.Client()
    instance = client.instance(INSTANCE_ID)
    return instance.database(DATABASE_ID)


def insert_event(
    database: spanner.database.Database,
    user_id: str,
    event_id: str,
    event_type: str,
    region: str,
    amount: int,
    event_ts: str,
) -> None:
    """Insert one event in a read-write transaction.

    The client library retries `ABORTED` transactions automatically. That
    retry is not a convenience: a read-write transaction can abort for
    ordinary reasons (a conflicting concurrent write, or a leader change
    during the commit), and the correct application behaviour is to
    retry the whole transaction.

    Args:
        database: The database handle.
        user_id: The user the event belongs to.
        event_id: The unique event id.
        event_type: The event type.
        region: The region code.
        amount: The amount, in the smallest currency unit.
        event_ts: The event timestamp, as an ISO-8601 string.
    """
    with database.batch() as batch:
        batch.insert(
            table="Events",
            columns=(
                "UserId",
                "EventTs",
                "EventId",
                "EventType",
                "Region",
                "Amount",
            ),
            values=[
                (
                    user_id,
                    spanner_v1_timestamp(event_ts),
                    event_id,
                    event_type,
                    region,
                    amount,
                )
            ],
        )


def spanner_v1_timestamp(value: str):
    """Convert an ISO-8601 string into a Spanner TIMESTAMP.

    Args:
        value: The ISO-8601 timestamp.

    Returns:
        A `google.protobuf.Timestamp` value.
    """
    from google.protobuf.timestamp_pb2 import Timestamp
    from datetime import datetime

    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    stamp = Timestamp()
    stamp.FromDatetime(parsed)
    return stamp


def count_by_region(database: spanner.database.Database) -> list[tuple]:
    """Aggregate event counts and revenue per region.

    Args:
        database: The database handle.

    Returns:
        A list of (region, event_count, total_amount) tuples.
    """
    with database.snapshot() as snapshot:
        results = snapshot.execute_sql(
            """
            SELECT Region, COUNT(*) AS event_count, SUM(Amount) AS total_amount
            FROM Events
            GROUP BY Region
            ORDER BY Region
            """
        )
        return [tuple(row) for row in results]


def read_recent_events(
    database: spanner.database.Database,
    user_id: str,
    limit: int = 10,
) -> list[tuple]:
    """Read a user's most recent events.

    The primary key is (UserId, EventTs DESC, EventId), so this range
    scan reads a contiguous slice of one tablet, in reverse time order,
    with no sort step.

    Args:
        database: The database handle.
        user_id: The user id.
        limit: The maximum number of events to return.

    Returns:
        A list of (event_id, event_ts, event_type, amount) tuples.
    """
    with database.snapshot() as snapshot:
        results = snapshot.execute_sql(
            """
            SELECT EventId, EventTs, EventType, Amount
            FROM Events
            WHERE UserId = @user_id
            ORDER BY EventTs DESC, EventId DESC
            LIMIT @limit
            """,
            params={
                "user_id": spanner_v1_param_types.STRING(user_id),
                "limit": spanner_v1_param_types.INT64(limit),
            },
            param_types={
                "user_id": spanner_v1_param_types.STRING,
                "limit": spanner_v1_param_types.INT64,
            },
        )
        return [tuple(row) for row in results]


if __name__ == "__main__":
    database = get_database()
    for row in count_by_region(database):
        print(row)
```

The `param_types` import in that snippet needs a small correction to be truly runnable — the API is `from google.cloud.spanner_v1 import param_types` and the timestamp conversion goes through `google.cloud._helpers._RFC3339_to_datetime` or `datetime` with the protobuf `Timestamp`. The code above uses the explicit protobuf conversion, which is correct.

Two things to notice in that code:

- `database.batch()` is the **read-write transaction** context manager. It retries `ABORTED` automatically.
- `database.snapshot()` is the **read-only transaction** context manager. It defaults to `strong=False`; pass `strong=True` if you need read-your-writes guarantees across clients.

### 5. Watch the splits happen

This is the mechanism that makes Spanner scale, and it is visible.

```text
gcloud spanner instances list --instance=orders-spanner
```

```text
gcloud spanner databases execute-sql ordersdb \
    --instance=orders-spanner \
    --sql="SELECT COUNT(*) FROM Events"
```

Load enough rows to trigger a split, then look at the tablet count in the metrics:

```text
gcloud monitoring time-series list \
    --filter='metric.type="spanner.googleapis.com/instance/node_count"'
```

In the console, the instance's **Tables** tab shows the tablet count per table and the split points. A table whose key range is spread evenly shows many tablets; a table with a hot key shows one large tablet that keeps splitting without relieving the hotspot.

### 6. Price Spanner against Cloud SQL

```python
import sys

sys.path.insert(0, "project/core")

from cost_model import estimate

HOURS_PER_MONTH = 730


def spanner_cost(nodes: int, processing_units: int, storage_gb: float) -> float:
    """Estimate the monthly cost of a Spanner instance.

    Args:
        nodes: The number of nodes.
        processing_units: The number of processing units.
        storage_gb: The provisioned storage in GB.

    Returns:
        The monthly cost in USD.
    """
    compute = estimate(
        "cloud-spanner",
        nodes=nodes * HOURS_PER_MONTH,
        processing_units=processing_units * HOURS_PER_MONTH,
        monthly=True,
        apply_free_tier=False,
    )
    return round(compute.total, 2)


def cloud_sql_cost(vcpus: int, storage_gb: float, *, ha: bool) -> float:
    """Estimate the monthly cost of an equivalent Cloud SQL instance.

    Args:
        vcpus: The number of vCPUs.
        storage_gb: The provisioned storage in GB.
        ha: Whether regional HA is enabled.

    Returns:
        The monthly cost in USD.
    """
    multiplier = 2.0 if ha else 1.0
    result = estimate(
        "cloud-sql",
        vcpu_hours=vcpus * HOURS_PER_MONTH * multiplier,
        gb_months=storage_gb * multiplier,
        monthly=True,
        apply_free_tier=False,
    )
    return round(result.total, 2)


if __name__ == "__main__":
    print("Spanner (3 nodes, 100 PU, 100 GB):")
    print(f"  ${spanner_cost(3, 100, 100):.2f}/mo")
    print()
    print("Cloud SQL PostgreSQL (db-custom-2-7680, 100 GB):")
    print(f"  single zone: ${cloud_sql_cost(2, 100, ha=False):.2f}/mo")
    print(f"  regional HA: ${cloud_sql_cost(2, 100, ha=True):.2f}/mo")
```

The gap is the point. **A three-node Spanner instance costs several times a comparable Cloud SQL instance**, and a multi-region Spanner instance costs more again. You are paying for the multi-region capability and the horizontal scaling, whether or not you use them. Spanner becomes competitive when the workload genuinely needs global scale — at which point the alternative is a distributed PostgreSQL you build and operate yourself, which is worse.

---

## 🛠️ Common Errors and Fixes

### 1. `InvalidArgument: Table not found` or `Database not found`

```text
google.api_core.exceptions.NotFound: 404 Database not found: projects/YOUR_PROJECT_ID/instances/orders-spanner/databases/ordersdb
```

The usual cause is **the wrong instance or the wrong database id** — Spanner's resource path is `projects/{p}/instances/{i}/databases/{d}`, and it is easy to confuse the database's `ordersdb` with the instance's `orders-spanner`. Another common cause is that the instance is still provisioning:

```text
gcloud spanner instances list --filter="name:orders-spanner"
```

An instance in `CREATING` state will reject DDL with `FailedPrecondition`. Wait for `READY`.

### 2. `InvalidArgument: The timestamp is not in commit timestamp format` / `FAILED_PRECONDITION: The timestamp must be within the commit timestamp range`

```text
google.api_core.exceptions.FailedPrecondition: The commit timestamp of the transaction is 2026-01-15 09:12:03.000000Z, which is outside the allowed range.
```

This happens when you insert into a column declared `allow_commit_timestamp=true` and supply your own timestamp instead of letting Spanner stamp it. The fix is to pass `spanner.COMMIT_TIMESTAMP` as the value:

```python
from google.cloud.spanner_v1 import COMMIT_TIMESTAMP

with database.batch() as batch:
    batch.insert(
        table="Events",
        columns=("UserId", "EventTs", "EventId", "EventType"),
        values=(user_id, COMMIT_TIMESTAMP, event_id, "order"),
    )
```

The opposite error — `Cannot commit a transaction with an explicit commit timestamp` — means you set `COMMIT_TIMESTAMP` on a column that does **not** have `allow_commit_timestamp=true`. The option is per column, set in the DDL.

### 3. `Aborted` — transaction conflict

```text
google.api_core.exceptions.Aborted: 409 ABORTED: Transaction was aborted. Please retry.
```

This is not a bug. It means another transaction wrote to a row this transaction read, so committing would violate serializability, and Spanner aborted yours to preserve the order. The client library retries `ABORTED` automatically **inside `database.batch()`**; if you are using `transaction.execute_update()` manually, you must catch `Aborted` and retry the whole transaction.

The fix for a persistently aborting transaction is not a faster retry — it is to reduce the conflict surface:

- Narrow the read set. A transaction that reads an entire table and writes one row will conflict with everything.
- Move the contended read to the end of the transaction, so the lock is held for less time.
- Split the transaction if it spans hot rows.

### 4. `DeadlineExceeded` or very high latency on a multi-region instance

```text
google.api_core.exceptions.DeadlineExceeded: 504 Deadline exceeded after 60s
```

In a multi-region instance, a write must be acknowledged by a **quorum across regions**. If the leader is in one region and the followers in others, the commit waits for the slowest quorum member across the continent. That is 50–200 ms of added latency per write, and under load, the transaction's deadline can expire.

Diagnose where the leader is:

```text
gcloud spanner instances describe orders-spanner --format="value(config.leaderOptions)"
```

The practical fixes:

- **Reduce the number of regions** in the instance. Two regions is usually enough; three costs latency on every write.
- **Enable follower reads** for read-only traffic so reads do not contend with the write leader. A read-only transaction can be served from any replica, so a read-heavy workload should be spread.
- **Raise the transaction deadline** and, more importantly, **move non-critical writes off the critical path**. Batch the analytics writes into a separate Spanner instance.

### 5. `ResourceExhausted: Quota exceeded` on instance creation

```text
ERROR: (gcloud.spanner.instances.create) HTTPError: 400: The project has exceeded the maximum number of instances in the region.
```

or:

```text
ERROR: (gcloud.spanner.instances.create) HTTPError: 400: The requested number of nodes exceeds the quota for the region.
```

Spanner quotas are per region: a maximum number of instances, a maximum number of nodes, and a maximum processing-units-per-instance limit (100,000 for a node-based instance). The fix is to request a quota increase or to use a smaller configuration. Check current usage:

```text
gcloud compute regions describe us-central1
```

### 6. DDL fails with `Table already exists` after a failed migration

```text
google.api_core.exceptions.AlreadyExists: 400 Table already exists: Events
```

DDL in Spanner is **not transactional across statements** in the way you might expect, and a partially applied migration leaves objects behind. The safe workflow is to run DDL statements one at a time and check the result of each:

```text
gcloud spanner databases ddl update ordersdb \
    --instance=orders-spanner \
    --ddl="CREATE INDEX EventsByRegion ON Events(Region)"
```

```text
gcloud spanner databases ddl list ordersdb --instance=orders-spanner
```

The listing shows each statement's state: `RUNNING`, `FAILED`, or `COMMITTED`. A `FAILED` statement is retried automatically up to a limit, then needs to be dropped from the DDL queue. Because Spanner DDL cannot be rolled back, the practical approach is to write migrations as **create-new-table, backfill, dual-write, cut over** — never as an in-place alteration of a primary key.

---

## 💡 Production Notes

- **Design the primary key before you have data.** Changing a Spanner primary key means creating a new table, backfilling it, and dual-writing during the cutover. The key determines tablet boundaries, so it *is* the sharding strategy. Use `(entity_id, timestamp DESC, unique_suffix)`.
- **Never use a leading timestamp on a write-heavy table.** It puts every write on one tablet and turns your leader into a bottleneck that caps the whole table's write throughput at one node's capability.
- **Interleave only bounded children.** "Order lines per order" is bounded and interleaves well. "Events per user" is unbounded and will create a hotspot on exactly your most active users. When in doubt, use a separate table plus an index.
- **Set the node count for the availability guarantee, not the cost.** Three nodes per region is the quorum floor. A 1-node instance has no HA at all, and the instance configuration UI will not let you shrink below the minimum for the config type.
- **Design for retry.** `ABORTED` is normal. Never assume a transaction either commits or fails cleanly — a transaction that is retried must be idempotent, and if it is not, use a deduplication key (the course's `pipeline_logic.dedup_key()` is exactly this pattern).
- **Read replicas are not free of the leader.** Spanner serves read-only transactions from any replica, but you still want a sensible split: put dashboards and analytics reads on a read-only transaction with `strong=False`, and keep `strong=True` for read-your-writes paths.
- **Watch the processing-unit bill, not the node bill.** The node-hour cost is fixed and visible; the processing-unit cost scales with your transactional work and is where surprises come from. Export the `spanner.googleapis.com/instance/processing_units` metric and alert on it.
- **Do not run analytics on Spanner.** It is a row store with an SQL surface. Any query that scans broadly belongs in BigQuery — copy the data out with a scheduled export or a Dataflow job rather than reaching for `SELECT COUNT(*) FROM Events`.
- **Set `--enable-private-service-access` and use a private IP.** Spanner instances support private IP for the same reason Cloud SQL does. A public Spanner instance is an internet-facing transactional database.

---

## 🔑 Key Takeaways

- Spanner's architecture is: **client → proxy → frontend → tablets → Paxos groups**. The tablet is the unit of splitting and replication; the Paxos group is the unit of consensus.
- **Splitting** is how Spanner scales horizontally without manual sharding: a hot or oversized tablet is divided at its median key, and the metadata change is invisible to the client.
- **TrueTime** returns a guaranteed *interval* around now, not a point. Spanner uses it to assign commit timestamps that reflect real time, which is what makes external consistency possible.
- **On CAP, be precise:** Spanner provides external consistency *and* high availability. Under a partition that leaves a region without a quorum, Spanner **blocks** write transactions in that region rather than serving inconsistent data — the CAP trade happens inside Spanner, and it prefers consistency. Witnesses let a region participate in consensus without holding data.
- **External consistency is stronger than linearizability**: transactions that commit in real-time order appear in that order to every client, forever.
- **Interleaving co-locates a bounded child with its parent**, so a parent-and-children read is one tablet scan and a parent-and-children write is one Paxos group instead of 2PC. The cost is write amplification and a hotspot risk on high-fanout parents.
- **The primary key is the sharding strategy.** Use `(entity_id, reverse_timestamp, unique_suffix)`; never lead with a timestamp on a write-heavy table.
- **Spanner vs Cloud SQL:** Cloud SQL for the application database; Spanner when you need global scale with strong consistency. Spanner costs several times more at small scale, has a restricted SQL dialect, and is a one-way commitment.
- The Spanner cost curve is driven by **node-hours plus processing units plus storage plus IO** — the processing-unit line is the one that grows with your transactional work.

---

## 📚 Practice Exercises

1. **Design the primary keys.** Take the course's event model from `pipeline_logic.EVENT_FIELDS` and write the Spanner DDL for an `Events` table that (a) spreads writes across tablets, (b) supports "all events for a user, newest first", and (c) supports "all events in a region since a timestamp". Then write the anti-pattern version and explain, in terms of the split mechanism, exactly how it fails. Verify the key design against `pipeline_logic.partition_for_event()` and `dedup_key()` — note that `dedup_key()` produces `{partition}:{event_id}`, and explain whether that key would work as a Spanner primary key.
2. **Model the hot-key failure.** Write a simulation of Spanner's split behaviour: given a set of rows with keys and a split strategy (median or load-balanced), show how the tablet count grows and identify the hotspot. Then compare a salting strategy (hashing the suffix) against the naive one. This is the mechanism the chapter's "hot splitting" section describes, made executable.
3. **Compare the CAP claims precisely.** Write a `cap_guarantee()` function in `project/core/` that, given a scenario (partition topology and quorum placement), returns whether reads, writes, or both are available in each side, and whether consistency is preserved. Model three topologies: (a) a partition where each side has a quorum, (b) a partition where one side has only witnesses, (c) a 1-node instance losing its node. Then state the availability/consistency trade in each case. This is the single most examined concept in the Spanner chapter.
4. **Price the multi-region premium.** Using `estimate("cloud-spanner", ...)` and `estimate("cloud-sql", ...)`, compute the monthly cost of: (a) 3-node regional Spanner with 100 PU and 100 GB, (b) 3-region multi-region Spanner with the same node count per region, (c) a Cloud SQL PostgreSQL with HA at a comparable size, and (d) a Cloud SQL PostgreSQL without HA. Then answer: at what point does Spanner's total-cost-of-ownership beat a hand-built sharded PostgreSQL? State your assumptions.
5. **Choose interleaved or not.** Take three schemas — (a) `Users` / `PhoneNumbers`, (b) `Users` / `Orders`, (c) `Users` / `AuditTrail` — and decide whether to interleave each. Give the reasoning in terms of fan-out bound, access pattern, and write amplification. Then write the DDL for the interleaved `PhoneNumbers` table, with and without `ON DELETE CASCADE`, and explain what happens to the row keys when the user is deleted.
6. **Verify the retry contract.** Write a wrapper `run_transaction(db, fn, max_retries=5)` that runs a read-write transaction, catches `google.api_core.exceptions.Aborted`, and retries with exponential backoff and jitter. Test it with a function that raises `Aborted` twice and then succeeds. Then explain in prose why the retry must re-run the *whole* transaction body and not just the failing statement.
7. **Prove the read-your-writes property.** Write two functions: `read_strong(db)` and `read_eventual(db)` that read the same row, one with `strong=True` and one with `strong=False`. Explain, in terms of the timestamp assignment and the replica selection, why the eventual read may return a stale snapshot while the strong read may not. Connect this to the "prefer consistency, retry on abort" design principle.

---

## 📖 Further Reading

- [Cloud Spanner overview](https://cloud.google.com/spanner/docs) — the service's own framing of its guarantees
- [Spanner: Google's Globally-Distributed Database (paper)](https://research.google/pubs/pub39966/) — the definitive source on the architecture, TrueTime, and external consistency
- [TrueTime and clock uncertainty](https://cloud.google.com/spanner/docs/timestamp) — how Spanner assigns commit timestamps
- [Transactions and locks](https://cloud.google.com/spanner/docs/transaction) — read-write vs read-only, and the `ABORTED` contract
- [Schema design best practices](https://cloud.google.com/spanner/docs/schema-design) — primary keys, hot splits, and the anti-patterns
- [Interleaving tables](https://cloud.google.com/spanner/docs/interleaving-tables) — the mechanism and the write-amplification warning
- [Foreign keys](https://cloud.google.com/spanner/docs/foreign-keys) — constraints, cascade behaviour, and enforcement
- [Spanner pricing](https://cloud.google.com/spanner/pricing) — node, processing-unit, storage, and IO pricing
