# 2.6 — Selecting a Database

> **Section 2 · Storage & Databases · Lecture 2.6 · 8:00**

## 🎯 What you will learn

- OLTP vs OLAP: the two workloads, the two access patterns, and why one database cannot do both well
- Vertical vs horizontal scaling, and how each service on GCP implements them
- RPO vs RTO: two different numbers that describe two different failures
- Availability vs durability: why they are independent, and how to buy each one
- The full decision matrix across Cloud SQL, Spanner, Bigtable, Datastore, Firestore, Memorystore, BigQuery and Persistent Disk
- A repeatable process for choosing, that does not start with a service name
- The anti-pattern of choosing a database by trend — and the four symptoms of it
- How to write the decision record that survives the next review

---

## 🧠 Concept

### The synthesis

The previous five chapters covered six services in detail. This chapter turns them into a decision you can defend.

The most important idea in this chapter is that **the database is chosen last, not first.** The order is:

```text
1. What does the data look like?            (shape)
2. How is it accessed?                      (access pattern)
3. How much of it, how fast, how reliably?  (scale, RPO, RTO)
4. Now — and only now — which service?
```

Choosing the service first is choosing by brand. Choosing by access pattern is choosing by engineering.

### OLTP vs OLAP

**OLTP — Online Transaction Processing.** Many small transactions, each touching a few rows. Reads and writes are roughly balanced. Each transaction must be correct and durable. Latency is measured in milliseconds and is a hard SLO.

```text
INSERT INTO orders (order_id, user_id, amount, status) VALUES (...);
UPDATE accounts SET balance = balance - 100 WHERE account_id = 'a1';
SELECT status FROM orders WHERE order_id = 'o1';
```

**OLAP — Online Analytical Processing.** Few large queries, each scanning many rows and columns. Read-only in the main. Latency is measured in seconds and is a soft target. The queries are aggregations over historical data.

```text
SELECT region, COUNT(*), SUM(amount_eur)
FROM events
WHERE event_dt BETWEEN '2026-01-01' AND '2026-01-15'
GROUP BY region;
```

**Why one database cannot do both well.** This is not a matter of taste; the requirements are structurally incompatible.

| Dimension | OLTP wants | OLAP wants |
|---|---|---|
| Storage layout | Row store (rows adjacent) | Column store (columns adjacent) |
| Query | Point lookup by index | Scan a column across millions of rows |
| Concurrency | Many short transactions, row-level locking | Few long queries, no locking |
| Indexes | Many, maintained on every write | Few, because it reads everything anyway |
| Compression | Row-oriented, per-row overhead | Column-oriented, excellent compression |
| Durability | Every commit fsynced | Batch loads, bulk append |
| Data lifetime | Current state, mutable | History, append-only |

The killer is the **write cost of indexes**. In an OLTP system, every `INSERT` must update every index. In an OLAP system you deliberately have *no* secondary indexes, because a query reads whole columns directly and an index would only add write cost and storage without accelerating anything.

Put an OLTP workload in a columnar warehouse and every point lookup becomes a full scan. Put an OLAP workload in a row store and the query becomes millions of individual row fetches, each with its own index lookups and page faults. Both are catastrophic, in opposite directions.

**The consequence for architecture: separate them.** The transactional system owns the current state and its invariants. The warehouse owns the history and the analysis. Change data capture moves changes from one to the other. This is why the reference architecture in every chapter of this course has Cloud SQL feeding BigQuery.

### Vertical vs horizontal scaling

**Vertical scaling** means buying a bigger machine: more vCPUs, more RAM, faster disk. The data stays in one place; one process owns it.

- **Pros**: simple, no coordination, transactions keep working, your SQL keeps working, backups are simple.
- **Cons**: there is a ceiling. A machine cannot be infinitely big. And a single machine is a single point of failure, so you need replicas, and replicas need failover, and failover with vertical scaling means the standby must be as big as the primary.

**Horizontal scaling** means distributing the data across many machines and routing requests to the right one. The classic implementation is **sharding**: partition the key space, and each shard owns a slice.

- **Pros**: scale past one machine's ceiling; add capacity incrementally; a shard failure affects only its slice.
- **Cons**: cross-shard queries and cross-shard transactions are hard; rebalancing is hard; the routing layer is a new thing to get wrong.

**How each GCP service implements this:**

| Service | Scaling model | Mechanism |
|---|---|---|
| Cloud SQL | Vertical | Bigger instance tiers; read replicas for read scale-out |
| Cloud Spanner | Horizontal | Automatic tablet splitting; the client is a router |
| Bigtable | Horizontal | Tablet splitting; tablet servers added to the cluster |
| Datastore / Firestore | Automatic horizontal | The service partitions and routes; you never shard |
| BigQuery | Elastic | Slots scale; data is distributed automatically; you never shard |
| Memorystore | Vertical + clustering | Bigger node sizes; Redis Cluster for horizontal |
| Persistent Disk | Vertical | A bigger disk (64 TB ceiling) |

The key insight for the decision: **horizontal scaling requires that your key space can be partitioned, and that the common queries do not cross partitions.** Spanner and Bigtable make this work by *splitting automatically and routing for you*. If your queries are inherently cross-cutting — a join across every order and every customer — no amount of horizontal scaling helps, because the answer genuinely requires touching everything.

### RPO and RTO

Two numbers that describe two different things, routinely confused.

**RPO — Recovery Point Objective.** How much data can you afford to lose. Measured in time.

> "In a disaster, we accept losing up to 15 minutes of writes."

Determined by: how often you take backups, whether you archive transaction logs (PITR), and how stale your read replicas are.

**RTO — Recovery Time Objective.** How long can you be down. Measured in time.

> "We need to be serving traffic again within 30 minutes."

Determined by: how fast you can provision new capacity, restore a backup, and shift traffic.

**The relationship, and the trap.** RPO and RTO are *not* independent. They are both determined by the same recovery mechanism, and there is a strong economic pull in the opposite direction:

- **Frequent backups and continuous log archiving → low RPO.** Restoring and replaying logs takes time → higher RTO.
- **Rare backups → fast restore of an old snapshot → potentially low RTO, but a large RPO.**

This is the classic trade, and it is where the money goes. Reducing RPO from 24 hours to 5 minutes might require log archiving, which might take your RTO from 20 minutes to 2 hours, because restoring a large database and replaying a day of logs is slow.

**Worked example with the course's own services:**

| Configuration | RPO | RTO | Notes |
|---|---|---|---|
| Cloud SQL, daily backup only | 24 hours | 30–60 min | Restore a snapshot; simple, slow |
| Cloud SQL, daily backup + PITR | ~1 transaction | 30–120 min | Restore + replay logs; the log replay dominates |
| Cloud SQL, HA regional | 0 (synchronous standby) | 30–90 s | Automatic promotion; the standby is current |
| Spanner, multi-region | 0 (synchronous) | < 60 s | Consensus across regions |
| BigQuery | n/a | minutes | Backed by GCS; you re-run the load |
| Object storage + versioning | 0 (soft delete) | minutes | Restore an object version |

The pattern: **every step down the RPO ladder costs RTO, except the one step that costs both.** The step from "single instance, daily backup" to "regional HA" cuts RPO from 24 hours to 0 and cuts RTO from an hour to a minute. It is the only move that improves both — because it moves the problem from *recovery* to *failover*, and failover is fast while recovery is slow.

That is the real reason to pay for HA. **HA is not about uptime; it is about RPO.** The RTO improvement is a bonus.

### Availability vs durability

Two more words that get conflated, and the distinction is fundamental.

**Durability** — the data is still there. Once a write is acknowledged, it survives any subsequent failure. It is a property of the *storage layer*.

**Availability** — the service is answering. You can get a response. It is a property of the *service layer*.

Consider a database with three replicas on the same rack:

- If the rack's power fails, the replicas are all gone → **not durable**.
- If one replica's process crashes, the other two form a quorum → the service keeps serving → **available**.

Now consider a database with one replica on three continents, where a network partition isolates the users in one region:

- The data is intact everywhere → **durable**.
- But the isolated region cannot form a quorum → it cannot commit writes → **not available** for writes.

**Availability is a spectrum, durability is a binary.** In the CAP framing (chapter 2.4), Spanner chose to keep durability perfect and let availability degrade during a partition. A system could choose the opposite — serve stale reads rather than block writes — which keeps availability high and durability intact, but risks two clients disagreeing about the state of the world.

**How to buy each one:**

| Want | Mechanism | GCP examples |
|---|---|---|
| Durability | Replication, synchronous commit, WAL, backups | Cloud SQL HA, Spanner, Bigtable replication |
| Availability | Redundancy across zones/regions, health checks, failover | Regional HA, multi-region instances, multi-zone clusters |
| Both cheaply | Managed services with automated failover | Cloud SQL HA is one checkbox |

### The full decision matrix

Here is every service from this module, side by side. Read it horizontally for a service, vertically for a criterion.

| | **Cloud SQL** | **Spanner** | **Bigtable** | **Datastore** | **Firestore** | **Memorystore** | **BigQuery** | **Persistent Disk** |
|---|---|---|---|---|---|---|---|---|
| **Model** | Relational (SQL) | Relational (SQL subset) | Wide-column | Document | Document | Key-value | Columnar table | Block device |
| **Workload** | OLTP | Global OLTP | Huge key-value / time-series | App entities | App entities + sync | Cache | OLAP | OS + local DB |
| **Scaling** | Vertical | Horizontal (auto-split) | Horizontal (auto-split) | Automatic | Automatic | Vertical / cluster | Elastic (slots) | Vertical |
| **Consistency** | Strong | External (strong) | Strong per row | Eventual (non-ancestor) / strong (ancestor) | Strong per doc | Strong (single node) | Strong (per-query snapshot) | Strong |
| **Multi-region** | Read replica only | Yes, first-class | Yes | Regional only | Regional + multi-region (emulator) | Regional only | Yes | N/A |
| **Transactions** | Full ACID | Serializable, read-write | Single-row only | Per entity group | Per document | Single-key atomic | Per-statement | Delegated to the DB |
| **Joins** | Yes | Limited (JOIN, no cross-shard in some cases) | No | No (ancestor only) | No | No | Yes | Delegated |
| **Indexes** | Many, maintained | Few, secondary indexes | None (use key design) | Automatic + composite | Automatic + composite | N/A | Cluster + search | Delegated |
| **Schema** | Rigid | Rigid-ish (DDL) | Flexible | Flexible | Flexible | None | Flexible | N/A |
| **Max scale** | ~64 TB / instance | Effectively unbounded | Effectively unbounded | Large | Large | In-memory size | Effectively unbounded | 64 TB / disk |
| **Operational effort** | Low | Medium | Medium-high | Low | Low | Low | None | Medium |
| **Best at** | The app database | Global transactions | Events at scale | Simple app entities | Mobile/web sync | Sub-ms cache | Analytics | Local DB files |

**And the storage services, for completeness:**

| | **Cloud Storage** | **Filestore** |
|---|---|---|
| **Model** | Object | NFS file |
| **Use** | Landing zone, archive, data lake | Shared mutable working set |
| **Fits in a row above?** | No — it is a landing zone, not a database | No — it is a working space, not a database |

### The decision procedure

A repeatable process. Use this in a design review.

**Step 1 — Classify the workload.**

Is it transactional (many small writes, strong correctness) or analytical (few large reads)?

- Analytical → **BigQuery**. There is no contest. Do not run analytics on a transactional database; do not put a transactional workload in BigQuery.
- Transactional → continue.

**Step 2 — Characterise the access pattern.**

Write down the top three queries or operations, literally, with their predicates.

- "Get this aggregate by id" → document store (Firestore / Datastore) or Spanner.
- "Get one row by a key I know" → Bigtable or Firestore.
- "Get a user and their related rows" → Spanner (interleaved) or Firestore (subcollection) or Cloud SQL (join).
- "Join across many entity types with arbitrary predicates" → Cloud SQL.
- "Scan a time range for analytics" → BigQuery, or Bigtable if the data is too big and you need key-based access.

**Step 3 — Check the scale and geography requirements.**

- Single region, moderate scale → Cloud SQL.
- Multi-region, needs strong consistency → Spanner.
- Very large, key-based, high write throughput → Bigtable.
- Multi-region with eventual consistency acceptable → Firestore or Datastore.

**Step 4 — Write down RPO and RTO.**

These are business requirements, and they determine the *configuration*, not usually the *service*. Cloud SQL can be single-zone or HA; Spanner can be regional or multi-region. State the numbers before you pick the service, because they will rule out configurations.

**Step 5 — Price the candidate set.**

Include HA, backups, and egress. The comparison that surprises people is that a multi-region Spanner instance costs several times a single-zone Cloud SQL instance — and for many workloads that Spanner is the right answer, the extra cost is buying the global consistency you need.

**Step 6 — Check the operational and skills constraints.**

Who runs this? A team that has run PostgreSQL for ten years will operate a Cloud SQL instance well and a Spanner instance badly. A managed service you cannot debug is a liability.

### The anti-pattern: choosing a database by trend

The failure mode is remarkably common and worth naming precisely, because naming it is the defence.

**The anti-pattern:**

```text
1. "Firestore is the modern way to do app databases"     → Firestore
2. "Spanner is Google Cloud's flagship database"         → Spanner
3. "NoSQL is the future; relational is legacy"           → Bigtable
```

Each of these picks a *product* before picking an *access pattern*, and each can be catastrophically wrong.

**The four symptoms:**

1. **The justification is architectural, not operational.** "It's serverless." "It's globally distributed." "It's NoSQL." These are properties, not requirements. The question is whether your workload has that property *as a requirement*.
2. **The schema decision was made before the query was written.** If nobody can write the top three queries, there is no access pattern, and there is no basis for the choice.
3. **The comparison is against a strawman.** Comparing Spanner to "a legacy RDBMS" instead of comparing it to the *specific* Cloud SQL instance you would otherwise run. Spanner is a fine choice; it is also five times the price and a different SQL dialect.
4. **The operational cost was not counted.** Firestore's per-document-read billing, Bigtable's row-key design burden, Spanner's key-design constraints — these are real costs that appear *after* the decision, when they are expensive to change.

**A worked example of the anti-pattern going wrong:**

A team builds a new internal dashboard. Someone says "let's use Firestore — it's serverless and mobile-friendly." The dashboard needs to join 4,800 events with a reference table of 50 region records, filter by a date range, and aggregate by region. Firestore can do it, but:

- Each `events` document read is billed separately. 4,800 document reads per dashboard refresh.
- The aggregation happens in the client, not the server.
- The 50-row reference table is fetched 4,800 times unless it is denormalised into every event document.
- The dashboard is slow because it is doing 4,800 sequential network round trips.

The right answer is **BigQuery**: a single scan of a partitioned table, `GROUP BY region`, returning four rows. Cost: $0.03. Time: two seconds.

And the symmetric error: a team with 4800 events and 4 regions picks **BigQuery** for the transactional path, because "we already use BigQuery". Now every `UPDATE accounts SET balance = ...` scans a table. Now the balance calculation is wrong, or slow, or both.

**The correct framing.** The two questions are not "which database is best?" but:

- *What is the shape of the access?*
- *What are the numbers I must hit?*

The service follows from the answers. If you cannot answer both questions, you are not ready to choose, and no amount of market research will help.

### A worked selection for the course pipeline

The course pipeline gives a concrete instance of the procedure.

**Workload A — the raw event landing zone.**
- Shape: immutable blobs written once, read in bulk later.
- Access: "read everything for date D" and "read one object by path".
- RPO: 0 (soft delete + versioning). RTO: minutes.
- Volume: 4,800 events/day in the sample; terabytes in reality.
- **Choice: Cloud Storage.** Object storage is not a database and does not need to be — it is the landing zone. Versioning and soft delete give the durability. Lifecycle manages the cost.

**Workload B — the transactional order system.**
- Shape: relational, with foreign keys between orders and customers.
- Access: point lookups by order id, joins, aggregates over recent orders.
- RPO: 5 minutes (PITR). RTO: 30 minutes.
- Volume: millions of rows, single region.
- **Choice: Cloud SQL for PostgreSQL**, regional HA, PITR enabled. Not Spanner: single region, moderate scale, and the SQL dialect restriction is pure cost. Not Firestore: the access pattern is genuinely relational, and Firestore's per-read billing would be worse.

**Workload C — the regional summary dashboard.**
- Shape: aggregate over a historical table.
- Access: "total revenue by region for date range D".
- RPO: n/a — rebuildable from the pipeline.
- Volume: 4 rows of output, from 4,800 rows of input.
- **Choice: BigQuery**, partitioned by `event_dt`, with the summary query aggregating to exactly the course's expected output: AMER 1238/464848.02, APAC 1159/421049.85, EMEA 1176/432544.17, LATAM 1227/445554.36, totalling 4,800 events across 24 hourly windows.

**Workload D — the per-user activity feed.**
- Shape: one user's recent events, newest first.
- Access: "the last N events for user U".
- RPO: seconds. RTO: minutes.
- Volume: hot, high read rate, small per user.
- **Choice: Firestore** (subcollection under the user, ordered by `event_ts DESC`) if the client is mobile and needs offline; **Bigtable** (row key `user_id#reverse_timestamp#event_id`) if it is a server-side feed at scale. Both are right for their own reasons, and the deciding question is "does the client need offline sync?"

**Workload E — the session cache.**
- Shape: key-value, ephemeral.
- Access: point lookup by session id.
- RPO: 0 (sessions are re-creatable). RTO: seconds.
- **Choice: Memorystore for Redis**, with a TTL on every key.

Note how the *same data* lands in three different services: raw in Cloud Storage, curated in BigQuery, and the hot per-user view in Firestore or Bigtable. **This is not duplication; it is different data products for different access patterns.** The raw copy in Cloud Storage has a 7-year retention and is read by a batch job. The curated copy in BigQuery is read by analysts. The hot copy is read by a mobile client 10,000 times a second. They have different access patterns, so they need different storage.

---

## 🛠️ Hands-On

### 1. Encode the decision procedure as code

```python
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Requirements:
    """The requirements for a database choice, gathered before any service.

    Attributes:
        name: A human-readable name.
        workload: "oltp" or "olap".
        access_patterns: The top operations, described in prose.
        needs_joins: Whether the workload joins across entity types.
        needs_multi_region: Whether the data must span regions.
        needs_strict_consistency: Whether a stale read is unacceptable.
        unbounded_children: Whether one parent can have unbounded children.
        needs_offline_sync: Whether clients are mobile and offline.
        rpo_minutes: The acceptable data loss, in minutes.
        rto_minutes: The acceptable downtime, in minutes.
        expected_gb: The expected size in GB.
        write_throughput_per_sec: The sustained write rate.
    """

    name: str
    workload: str
    access_patterns: tuple[str, ...]
    needs_joins: bool = False
    needs_multi_region: bool = False
    needs_strict_consistency: bool = True
    unbounded_children: bool = False
    needs_offline_sync: bool = False
    rpo_minutes: float = 60.0
    rto_minutes: float = 60.0
    expected_gb: float = 100.0
    write_throughput_per_sec: int = 100


@dataclass(frozen=True)
class Recommendation:
    """The outcome of a selection.

    Attributes:
        service: The recommended service id, or a zone name.
        reasons: The reasons the service was chosen.
        rejected: Service id -> why it was rejected.
    """

    service: str
    reasons: tuple[str, ...]
    rejected: dict[str, str] = field(default_factory=dict)


def select_database(req: Requirements) -> Recommendation:
    """Choose a database from requirements, not from a favourite.

    The order of the checks is the argument. The workload split comes
    first because it is the largest structural difference. Within OLTP,
    the join requirement comes next, because joins are what relational
    databases are for and no NoSQL service can replace them without a
    denormalisation project. Multi-region and consistency come after,
    because they change the *configuration* more often than the service.

    Args:
        req: The requirements.

    Returns:
        The recommendation.
    """
    rejected: dict[str, str] = {}

    if req.workload == "olap":
        return Recommendation(
            service="bigquery",
            reasons=(
                "the workload is analytical: few large scans, aggregations "
                "over history, and no transactional invariants to protect",
                "a columnar warehouse stores and scans columns, which is "
                "exactly the shape of the question",
                "the result set is small even when the input is huge — the "
                "course's 4,800 events aggregate to four rows",
            ),
            rejected={
                "cloud-sql": "point lookups and index maintenance on a "
                "transactional store are the wrong engine for a scan",
                "firestore": "per-document billing and client-side "
                "aggregation for a workload that reads every row",
                "cloud-spanner": "a row store with transaction overhead "
                "scanning a full column",
            },
        )

    if req.workload != "oltp":
        raise ValueError(f"unknown workload: {req.workload!r}")

    if req.needs_joins:
        return Recommendation(
            service="cloud-sql",
            reasons=(
                "the workload joins across entity types with arbitrary "
                "predicates — no NoSQL service does this without a "
                "denormalisation project",
                "the data fits in a single region at the expected size",
                "the team already operates relational engines",
            ),
            rejected={
                "firestore": "no joins; the equivalent is a fan-out read "
                "of every related document",
                "bigtable": "no joins and no secondary indexes",
                "cloud-spanner": "supports joins but costs several times "
                "more for a single-region workload",
            },
        )

    if req.needs_multi_region and req.needs_strict_consistency:
        return Recommendation(
            service="cloud-spanner",
            reasons=(
                "the data spans regions and a stale read is unacceptable",
                "external consistency gives read-your-writes across "
                "regions, which no other service here provides",
                "horizontal scaling means the write throughput is not "
                "capped by one primary",
            ),
            rejected={
                "cloud-sql": "a read replica gives a stale read in another "
                "region; writes still go to one primary",
                "firestore": "multi-region Firestore converges "
                "asynchronously",
                "bigtable": "strong per row, but no multi-row relational "
                "semantics",
            },
        )

    if req.needs_multi_region and not req.needs_strict_consistency:
        return Recommendation(
            service="firestore",
            reasons=(
                "the data spans regions and eventual consistency is "
                "acceptable",
                "documents match the aggregate shape of the access pattern",
            ),
            rejected={
                "cloud-spanner": "strong consistency is more than the "
                "workload needs, and it costs more",
            },
        )

    if req.needs_offline_sync:
        return Recommendation(
            service="firestore",
            reasons=(
                "clients are offline-capable, which is a product feature "
                "not a storage feature",
                "documents map to the client's object model without a "
                "serialisation layer",
            ),
            rejected={
                "datastore": "no offline sync in the client SDK",
            },
        )

    if req.unbounded_children:
        return Recommendation(
            service="bigtable",
            reasons=(
                "one parent can have unbounded children, which breaks "
                "interleaving and subcollection modelling",
                "the access pattern is key-based: a range scan over the "
                "parent's children",
            ),
            rejected={
                "cloud-spanner": "interleaving a high-fanout child table "
                "creates a write hotspot on exactly the hottest parents",
            },
        )

    return Recommendation(
        service="cloud-sql",
        reasons=(
            "the workload is transactional, single-region, and "
            "relation-shaped",
            "Cloud SQL is the cheapest way to get strong consistency and "
            "full SQL at this scale",
        ),
    )


if __name__ == "__main__":
    cases = [
        Requirements(
            name="order service",
            workload="oltp",
            access_patterns=("get order by id", "orders for a customer"),
            needs_joins=True,
            rpo_minutes=5,
            rto_minutes=30,
        ),
        Requirements(
            name="global ledger",
            workload="oltp",
            access_patterns=("post transaction", "read balance"),
            needs_multi_region=True,
            needs_strict_consistency=True,
        ),
        Requirements(
            name="mobile profile",
            workload="oltp",
            access_patterns=("fetch profile", "update settings"),
            needs_offline_sync=True,
        ),
        Requirements(
            name="clickstream archive",
            workload="oltp",
            access_patterns=("events by user, newest first"),
            unbounded_children=True,
            write_throughput_per_sec=50000,
        ),
        Requirements(
            name="regional revenue dashboard",
            workload="olap",
            access_patterns=("revenue by region for a date range"),
        ),
    ]
    for case in cases:
        result = select_database(case)
        print(f"{case.name}")
        print(f"  → {result.service}")
        for reason in result.reasons:
            print(f"    · {reason}")
        print()
```

The output demonstrates the point of the whole chapter: **the same five requirement sets produce five different services, and every one of them is defensible.** Nothing in the function knows which services are trendy.

### 2. Model the RPO/RTO trade-off explicitly

```python
import sys

sys.path.insert(0, "project/core")

from dataclasses import dataclass

from cost_model import estimate

HOURS_PER_MONTH = 730


@dataclass(frozen=True)
class RecoveryOption:
    """One way to recover, and what it costs.

    Attributes:
        name: A human-readable name.
        rpo_minutes: The worst-case data loss, in minutes.
        rto_minutes: The worst-case downtime, in minutes.
        monthly_cost: The monthly cost in USD.
        description: How it works.
    """

    name: str
    rpo_minutes: float
    rto_minutes: float
    monthly_cost: float
    description: str


def recovery_options() -> list[RecoveryOption]:
    """Build the recovery option table for a 100 GB PostgreSQL database.

    Returns:
        The options, ordered from cheapest to most expensive.
    """
    base_compute = estimate(
        "cloud-sql",
        vcpu_hours=2 * HOURS_PER_MONTH,
        gb_months=100,
        monthly=True,
        apply_free_tier=False,
    ).total
    base_storage = 100 * 0.17

    single = base_compute + base_storage
    ha = (base_compute * 2) + (base_storage * 2)

    return [
        RecoveryOption(
            name="single zone, daily backup",
            rpo_minutes=60 * 24,
            rto_minutes=60,
            monthly_cost=round(single, 2),
            description="restore a nightly snapshot; everything since is lost",
        ),
        RecoveryOption(
            name="single zone, backup + PITR",
            rpo_minutes=1,
            rto_minutes=120,
            monthly_cost=round(single + 100 * 0.17, 2),
            description="restore a snapshot and replay the transaction log",
        ),
        RecoveryOption(
            name="regional HA, PITR",
            rpo_minutes=0,
            rto_minutes=1.5,
            monthly_cost=round(ha + 100 * 0.17, 2),
            description="synchronous standby; failover promotes the standby",
        ),
    ]


if __name__ == "__main__":
    print(f"{'option':<32} {'RPO':>8} {'RTO':>8} {'$/mo':>10}")
    print("-" * 62)
    for option in recovery_options():
        print(
            f"{option.name:<32} "
            f"{option.rpo_minutes:>7.1f}m "
            f"{option.rto_minutes:>7.1f}m "
            f"${option.monthly_cost:>9.2f}"
        )
```

The table makes the trade visible: **the step from a single zone to regional HA is the only one that improves both RPO and RTO simultaneously.** Everything else is a straight trade of one against the other, paid for in money or in engineering effort.

### 3. Check the choices against the course's service catalogue

```python
import sys

sys.path.insert(0, "project/core")

from service_catalog import (
    SERVICES,
    format_service_table,
    get_service,
    services_by_category,
)


def database_role_report() -> list[str]:
    """Report the data_role each database service plays in the platform.

    The catalogue assigns a role to every service. This makes those
    assignments visible so that a selection decision can be checked
    against them.

    Returns:
        One report line per database service.
    """
    lines = []
    for service in services_by_category("Databases"):
        lines.append(
            f"{service.name:<16} role={service.data_role:<12} "
            f"pricing={service.pricing_model}"
        )
    return lines


if __name__ == "__main__":
    print("Database services in the catalogue:")
    for line in database_role_report():
        print(f"  {line}")

    print()
    print("Storage services, for comparison:")
    for service in services_by_category("Storage"):
        print(
            f"  {service.name:<16} role={service.data_role:<12} "
            f"resources={', '.join(service.key_resources)}"
        )

    print()
    print("What the catalogue says about the whole platform:")
    for role, ids in sorted(
        {
            role: sorted(
                s.id for s in SERVICES.values() if s.data_role == role
            )
            for role in {s.data_role for s in SERVICES.values()}
        }.items()
    ):
        print(f"  {role:<12} {', '.join(ids)}")
```

Note the `data_role` assignment in the catalogue: **every database service carries the role `"warehouse"`.** That is a deliberate simplification — the role field in `service_catalog.py` is about the *platform position*, and a database that holds the transactional source is still "the warehouse role" in the sense of "where data is kept". Do not read the role field as a selection criterion; use it to check that your chosen services occupy distinct, sensible positions in the architecture.

### 4. The final check: does the choice survive the questions?

```python
REVIEW_QUESTIONS = (
    "Can you write the top three queries, with their predicates, in one line each?",
    "What is the RPO, in minutes, and who agreed to it?",
    "What is the RTO, in minutes, and who agreed to it?",
    "What is the total monthly cost, including HA, backups and egress?",
    "What happens when the primary region is unavailable?",
    "What is the row-key or partition design, and what is its hot key?",
    "Who on the team has operated this service before?",
    "What is the exit path, and what does the exit cost?",
)


def review_checklist() -> list[str]:
    """Return the review checklist for a database choice.

    Returns:
        The questions, one per line.
    """
    return list(REVIEW_QUESTIONS)
```

The eighth question matters more than people expect. **The exit path is part of the decision.** A Cloud SQL instance exports cleanly with `pg_dump`; a Spanner instance exports to BigQuery and then to Parquet; a Firestore database exports to BigQuery; a Bigtable table exports to BigQuery or to Parquet. Every GCP database has an export path — but the cost of the export and the fidelity of the export differ. If your data is the system of record for a regulated business, ask how you get it out, and how long that takes.

---

## 🛠️ Common Errors and Fixes

### 1. The analytical query on the transactional database

```text
ERROR: 400 Bad Request: Job exceeded rate limits: resources: too many concurrent queries
```

or, more painfully, the query succeeds but takes 47 seconds and holds locks:

```text
ERROR: canceling statement due to lock timeout
```

The symptom is a dashboard or report query on the transactional database that used to be fast and is now slow, right after the transactional workload grew. The cause is the classic mistake: running an analytical aggregate against the OLTP store.

The fix is to move the aggregate to BigQuery and read the result from there:

```sql
-- Instead of, on the Cloud SQL instance:
--   SELECT region, COUNT(*), SUM(amount) FROM orders
--   WHERE created_at > '2026-01-01' GROUP BY region;

-- Export the source, then aggregate in the warehouse:
EXPORT DATA OPTIONS (
  uri 'gs://YOUR_BUCKET/exports/orders-*.csv',
  format 'CSV',
  overwrite true
);
```

Then in BigQuery:

```sql
SELECT region, COUNT(*) AS event_count, SUM(amount_eur) AS revenue_eur
FROM `YOUR_PROJECT_ID.curated.events`
WHERE event_dt BETWEEN '2026-01-01' AND '2026-01-15'
GROUP BY region
ORDER BY region;
```

The `EXPORT DATA` runs in the database but streams to Cloud Storage, so it does not hold the table's locks for the duration of the aggregation. It is the right way to extract from an OLTP source.

### 2. Firestore bills thousands of document reads for one dashboard

```text
# The bill line item that explains it:
Document reads: 1,248,000 (from a dashboard with 4,800 events)
```

This is not a Firestore bug; it is the consequence of storing rows that are read together as separate documents, and of aggregating in the client.

The fix is to change the storage model or the query target:

- **Denormalise** the small aggregates onto a document that the dashboard reads once. If the dashboard needs "total revenue by region", store **one document per region** with a running total, updated by a Cloud Function or a scheduled job. The dashboard then does 4 document reads, not 4,800.
- **Or move the aggregation to BigQuery**, which is what chapter 3 does properly.

The general rule for Firestore: **one document read, one billing unit.** Design the read path first.

### 3. Spanner underperforms because of the primary key

```text
ERROR: RESOURCE_EXHAUSTED: Quota exhausted for quota metric 'Commit operations'
```

or, less obviously, latency climbing with data volume:

```text
# Latency: 12ms at 1M rows, 940ms at 500M rows
```

A timestamp-leading primary key on a write-heavy table puts every write on the last tablet. The tablet's leader saturates, and its Paxos group falls behind, so commits queue and the commit-operation quota is exhausted.

The fix is a new primary key:

```sql
-- Before: everything writes to one tablet.
CREATE TABLE Events (EventTs TIMESTAMP NOT NULL, UserId STRING(64), PRIMARY KEY (EventTs, UserId));

-- After: writes spread, and a user's events are still a contiguous range.
CREATE TABLE EventsV2 (
  UserId STRING(64) NOT NULL,
  EventTs TIMESTAMP NOT NULL,
  EventId STRING(64) NOT NULL,
  PRIMARY KEY (UserId, EventTs DESC, EventId)
);
```

The migration is create-new-table, backfill, dual-write, cut over. This is why the key must be designed before there is data.

### 4. Bigtable scans the whole table for every query

```text
# 4,800 rows read, 0 returned, for a single-user query:
google.api_core.exceptions.DeadlineExceeded: 504 Deadline exceeded after 60s
```

The row key is salted, so a per-user query cannot be pruned. The fix, in order of preference:

1. **Change the key layout** so the user prefix comes first: `user_id#timestamp#event_id`. You lose even write distribution but the query becomes a contiguous range scan.
2. **Add an index table** keyed `user_id#event_ts` holding the primary row key, written in the same batch mutation.
3. **Accept the scan** only if the query is rare and the table is small.

The rule: **in Bigtable, a filter is not a query.** Filters are applied after the rows are read.

### 5. Cloud SQL RPO is 24 hours when the business expected 15 minutes

```text
# The instance was created without the right flags:
gcloud sql instances describe orders-db --format="value(settings.backupConfiguration)"
```

```text
pointInTimeRecoveryEnabled: false
transactionLogRetentionDays: 0
backupStartTime: 03:00
```

This is the most expensive kind of mistake, because it is invisible until the incident. The instance had a daily backup and everyone believed recovery was fine.

The fix is to enable PITR, and then to **test the restore**:

```text
gcloud sql instances patch orders-db \
    --enable-point-in-time-recovery \
    --backup-retention-settings=retentionPeriodInDays=7
```

Then actually perform a point-in-time restore into a scratch instance and time it. An untested RTO is a guess.

### 6. The chosen database has no exit path

```text
ERROR: (gcloud.spanner.databases.backup) HTTPError: 400: The database is not eligible for backup.
```

or, on export:

```text
ERROR: (gcloud firestore export) HTTPError: 400: The Firestore database must use the standard configuration to be exported.
```

Not every configuration is exportable, and the restrictions differ per service. The fix is to know the export mechanism before you commit to the service, and to test it with real data:

| Service | Export path |
|---|---|
| Cloud SQL | `gcloud sql export sql` to Cloud Storage |
| Spanner | `gcloud spanner databases export` to Cloud Storage (Avro, Parquet) |
| Bigtable | `gcloud bigtable export` to Cloud Storage (Avro) |
| Firestore | `gcloud firestore export` to BigQuery |
| Datastore | `gcloud datastore export` to Cloud Storage |
| Memorystore | `redis-cli --rdb` for a snapshot |

The exercise is to run the export on day one, not on the day you need it.

---

## 💡 Production Notes

- **Write the access patterns down before you choose.** Not the requirements — the actual queries, with their predicates, in one line each. A decision record without them is a decision record without a basis. Put them in the design document and put them in the review.
- **Never mix OLTP and OLAP in one database.** The moment a report query touches the transactional store, you have a latency problem that will be blamed on "the database" and will be fixed by scaling up, which makes the real problem worse. Extract with `EXPORT DATA` and aggregate in BigQuery.
- **State RPO and RTO as numbers with names attached.** "RPO 15 minutes (agreed by Finance, ticket DATA-142)" is a decision. "We should have good backups" is not. The numbers go in the design document and in the runbook.
- **Use the one move that improves both RPO and RTO: regional HA.** Every other step on the recovery ladder trades one against the other. HA moves you from recovery to failover, and failover is fast.
- **Budget for egress, not for storage.** Storage is $0.02/GB-month; egress is $0.12/GB. A database with a large export, a BI tool reading directly, or a multi-region read pattern will surprise you on the egress line. Use BigQuery's free GCS read tier and keep the extract path in-region.
- **Design the row key or partition before the first row is written.** For Bigtable it is the whole schema. For Spanner it determines the split boundaries. For Firestore it determines the query cost. All three are effectively immutable once data exists.
- **Run the export, on day one, with real data.** The exit path is part of the decision, and an untested export is a hypothesis. Schedule a quarterly restore drill and time it — that is your real RTO.
- **Treat the operational skill in the team as a hard constraint.** A managed service you cannot debug is an outage with a monthly invoice. The cheapest service in the matrix is not the one you should pick; the one your team can run at 3am is.
- **Review the decision on a schedule, and whenever the access patterns change.** The requirement that drove the choice two years ago may have changed, and the cost of migrating grows with the data. Put the review on a calendar, and put the "what would make us change our mind" clause in the original document.

---

## 🔑 Key Takeaways

- **Choose the database last.** Shape, then access pattern, then scale and recovery numbers, then the service.
- **OLTP and OLAP are structurally incompatible** — row store vs column store, index maintenance vs full scans. Separate them, and move data between them with CDC or `EXPORT DATA`.
- **Vertical scaling is simple and has a ceiling; horizontal scaling scales past it but needs a partitionable key space and query locality.** Spanner and Bigtable automate it; Cloud SQL and Filestore do not.
- **RPO and RTO are two different numbers describing two different failures**, and they are linked: lower RPO usually costs higher RTO. The one exception — regional HA — improves both, because it turns recovery into failover.
- **Availability is a spectrum; durability is a binary.** Spanner keeps durability perfect and lets availability degrade during a partition, blocking writes rather than serving inconsistent data.
- **The decision matrix**: Cloud SQL for relational OLTP; Spanner for global transactional scale; Bigtable for huge key-based or time-series workloads; Firestore for mobile/offline app data; Datastore for simpler server-side entities; Memorystore for caching; BigQuery for analytics; Persistent Disk for a database's own files.
- **One dataset, three stores, is not duplication** — it is different data products with different access patterns, retention, and read rates.
- **The anti-pattern is choosing by trend.** Its four symptoms: architectural rather than operational justification, schema chosen before the query, comparison against a strawman, and un-counted operational cost.
- **Put the exit path in the decision.** Every GCP database exports, but the cost and the fidelity differ. Test the export on day one and re-test it on a schedule.

---

## 📚 Practice Exercises

1. **Run the selection procedure on five real workloads.** Extend the `select_database()` function with the requirements you would gather from: (a) a multi-tenant SaaS billing system, (b) a IoT telemetry ingest, (c) a genomics research store, (d) an ad-serving auction engine, (e) a collaborative document editor. Use the access patterns you write for each, and show the output. Then write the RPO and RTO you would propose for each, with a one-sentence justification.
2. **Model the RPO/RTO ladder for Spanner.** Extend `recovery_options()` with Spanner configurations — regional (3 nodes), multi-region (3 regions), and a single-node instance — and their RPO/RTO. Price each with `estimate("cloud-spanner", ...)`. Then answer: at what point is multi-region Spanner cheaper than a hand-built multi-region PostgreSQL with a connection pooler, a CDC pipeline, and two people on call?
3. **Write the decision record.** Choose one workload from exercise 1 and write the full decision document: the access patterns, the RPO/RTO with names attached, the candidate set with prices, the chosen service, the rejected alternatives with reasons, the row-key or partition design, and the exit path. Then have a colleague read it and find the weakest argument. This is the deliverable the chapter is really about.
4. **Compare Firestore and BigQuery for the course dashboard.** Using the course's actual data — 4,800 events, 4 regions, the summary from `pipeline_logic.EXPECTED_SUMMARY` — compute the read cost of (a) a Firestore dashboard that reads every event document and aggregates in the client, and (b) a BigQuery dashboard with one partitioned scan. For (a), use the Firestore per-document-read model; for (b), use `estimate("bigquery", scanned_tb=...)` and the course's `estimated_scan_bytes()` helper. Then design the Firestore alternative that would be competitive — one document per region with a running total — and explain the trade it introduces (staleness, write amplification, and the function that maintains it).
5. **Detect the anti-pattern in five arguments.** Write a `detect_trend_antipattern(reasoning: str)` function that scores a justification against the four symptoms: architectural-not-operational justification, schema-chosen-before-query, strawman comparison, and un-counted operational cost. Test it against: (a) "let's use Firestore because it's serverless", (b) "Spanner gives us globally consistent transactions and our users are in three continents with a 5-minute staleness requirement, which Cloud SQL's read replica cannot meet", (c) "Firestore is better than a legacy RDBMS", (d) "we need strong consistency across regions, Spanner provides it, and Cloud SQL would require us to build distributed transaction management ourselves". Explain why (b) and (d) should pass and (a) and (c) should fail.
6. **Cost the full reference architecture.** Build a `reference_architecture_cost()` function in `project/core/` that prices the complete stack from the course's `CURRICULUM.md`: Cloud SQL (HA, 2 vCPU, 100 GB) + Datastream (CDC on 4,800 rows/day) + Pub/Sub + Dataflow (streaming) + BigQuery (partitioned, 1 TB/month) + Cloud Storage (raw landing zone, 10 TB, lifecycle-aged to Nearline) + Composer (1 node) + Data Catalog. Use `estimate()` for each. Then produce the same total with a **batch-only** variant (no Datastream, no Pub/Sub, no Dataflow — a nightly `EXPORT DATA` plus a Dataflow batch job) and quantify what the streaming path buys for what it costs. Include the raw bucket priced at each storage class so the lifecycle decision is visible in the total.
7. **Build the migration plan.** Assume you are moving the course's transactional layer from Cloud SQL to Spanner. Write the plan: the schema translation (including the key change from `event_id` primary key to `(user_id, event_ts DESC, event_id)`), the backfill, the dual-write, the validation query that compares row counts and the per-region totals from `EXPECTED_SUMMARY`, and the cutover. Then write the **rollback** plan, and state the point of no return — the step after which rolling back costs more than proceeding.

---

## 📖 Further Reading

- [Cloud SQL overview](https://cloud.google.com/sql/docs/mysql/overview) — the managed relational service, and its limits
- [Cloud Spanner overview](https://cloud.google.com/spanner/docs) — the global-scale relational service
- [Cloud Bigtable documentation](https://cloud.google.com/bigtable/docs) — the wide-column store
- [Firestore data model](https://cloud.google.com/firestore/docs/data-model) — documents, collections, and subcollections
- [Memorystore for Redis and Memcached](https://cloud.google.com/memorystore/docs) — the cache options
- [BigQuery architecture and storage](https://cloud.google.com/bigquery/docs/introduction) — why the warehouse is a separate system
- [Datastream change data capture](https://cloud.google.com/datastream/docs) — moving changes from OLTP to the warehouse
- [Database Migration Service](https://cloud.google.com/database-migration/docs) — the managed migration path, including to Cloud SQL
