# 3.1 — Data Warehousing Concepts

> **Section 3 · Analytics & Warehousing · Lecture 3.1 · 8:00**

## 🎯 What you will learn

- Why OLTP and OLAP are structurally incompatible workloads, not just "different query styles"
- What a data warehouse actually is, defined by its properties rather than by its vendor
- The Kimball dimensional model: facts, dimensions, grains, star and snowflake schemas, conformed dimensions
- **Fact grain** — the single most important concept in warehousing, and how to defend it
- Why columnar storage is a requirement for analytical queries and not an optimisation
- ACID in the OLTP context and why the warehouse deliberately gives it up
- The ETL staging architecture: raw, staging, curated, serving
- Data marts, and why they multiply
- The lakehouse emergence, and what it actually changes versus a classic warehouse
- How the course pipeline maps onto these layers

---

## 🧠 Concept

### Why this chapter comes first

The previous two sections were about **systems that hold data for a purpose**: a transaction, a document, a key. Section 3 is about the system that holds data for **questions you have not asked yet**.

That distinction is the entire reason warehousing is a discipline and not a product category. A database is designed around the queries you know. A warehouse is designed so that you can ask questions you did not anticipate — and still get an answer in seconds, on data you did not structure for that question.

BigQuery, BigLake, Dataplex and Data Catalog are the Google Cloud implementations of this discipline. But the discipline came first, in the 1990s, and the tooling is a late arrival. If you learn the tools without the model, you will build a pipeline that works for the one query in the ticket and cannot answer the follow-up question in the review meeting.

### OLTP vs OLAP

**OLTP — Online Transaction Processing.** Many small transactions, each touching a few rows. Reads and writes roughly balanced. Each transaction must be correct and durable. Latency is measured in milliseconds and is a hard SLO.

```sql
INSERT INTO orders (order_id, user_id, amount, status) VALUES (...);
UPDATE accounts SET balance = balance - 100 WHERE account_id = 'a1';
SELECT status FROM orders WHERE order_id = 'o1';
```

**OLAP — Online Analytical Processing.** Few large queries, each scanning many rows and columns. Read-dominated. Latency measured in seconds and is a soft target. The query is an aggregation over history.

```sql
SELECT region, COUNT(*), SUM(amount_eur)
FROM events
WHERE event_dt BETWEEN '2026-01-01' AND '2026-01-15'
GROUP BY region;
```

The differences are not cosmetic. They are **structurally incompatible**, and the reason is the write cost of indexes.

| Dimension | OLTP wants | OLAP wants |
|---|---|---|
| Storage layout | Row store — whole rows adjacent | Column store — whole columns adjacent |
| Read unit | A row, by key or index | A column, across millions of rows |
| Indexes | Many, maintained on every write | None — it reads everything anyway |
| Concurrency | Many short transactions, row locks | Few long queries, no locks |
| Compression | Row-oriented, per-row overhead | Column-oriented, excellent ratios |
| Durability | Every commit fsynced | Bulk loads, append-only |
| Data lifetime | Current state, mutable | History, append-only |
| Optimisation target | Time to *complete one operation* | Time to *finish the whole query* |

**The killer is index maintenance.** Every `INSERT` in an OLTP system must update every index on the table. An OLAP system deliberately has *no* secondary indexes: a query reads whole columns straight from storage, and an index would add write cost and storage without accelerating anything. This is why BigQuery has no `CREATE INDEX` and never will.

**The consequence for architecture: separate them.** The transactional system owns current state and its invariants. The warehouse owns history and analysis. Data movement between them is the job of CDC, batch export, or streaming ingest.

### What a data warehouse is

A warehouse is not "a big database". It is a store with a specific set of properties. Inmon's classic definition (the "read-optimized" dimension) and Kimball's (the "integrated" and "time-variant" dimensions) still describe the same thing. The definitional properties:

1. **Subject-oriented.** Organised around business subjects — sales, customers, events — not around application processes. The warehouse does not have an "orders service" schema; it has an *orders* subject that draws from whatever systems produced them.
2. **Integrated.** Data from many sources, reconciled: currencies normalised, time zones converted, codes mapped to a shared dimension. The reconciliation is the hard part and it is where warehousing projects actually live or die.
3. **Non-volatile.** History is retained and not overwritten. A new sale does not change the sale last quarter; it is appended.
4. **Time-variant.** Every record has a time dimension. The warehouse always knows "as of".
5. **Read-optimised.** Designed for scan-and-aggregate, not for row-level transactional updates.
6. **Large scale.** Measured in terabytes, queried in aggregates, across years.

**The one-sentence version:** a warehouse is an integrated, time-variant, non-volatile, subject-oriented store, optimised for read-heavy aggregation over large volumes, and deliberately decoupled from the transactional systems that produce the data.

Notice what is *not* in that list: real-time updates, referential integrity enforcement, normalised third normal form. A warehouse that enforced foreign keys and 3NF and allowed `UPDATE` would be an OLTP system wearing a costume.

### The Kimball dimensional model

Kimball's approach is the one Google Cloud tooling assumes, and the one this course teaches, because it is the model that makes ad-hoc questions cheap.

**The core idea:** split your data into two kinds of table with completely different jobs.

**Facts** — the measurements. Narrow tables of numbers, mostly foreign keys plus numeric measures. "1238 orders, 464848.02 EUR". Facts are the things you count and sum. They are numerous, they are append-only, and their grain is the single most important property of the entire model.

**Dimensions** — the context. Wider tables of descriptive attributes. "AMER", "mobile", "order", "EUR". Dimensions are numerous, they are slowly changing, and they are the things you group by and filter on. Dimensions are shared across fact tables; that sharing is the point.

```text
                dim_region        dim_channel
                (4 rows)          (3 rows)
                    |                 |
                    |                 |
                    +--------+--------+
                             |
                 +-----------+-----------+
                 |                       |
           fact_sales              fact_events
        (grain: one row per      (grain: one row per
         order line)             event)
```

### Fact grain — the single most important concept

**The grain is the answer to: "what does one row of this table represent?"**

This is the concept that most often separates a working warehouse from an unusable one, because a table with two grains cannot answer any question correctly. It can only answer the question that accidentally matches one of them.

Common grains:

| Fact table | One row represents |
|---|---|
| `fact_sales_line` | one line item on one invoice |
| `fact_sales` | one invoice |
| `fact_events` | one event |
| `fact_daily_snapshot` | one day, per account, per metric |
| `fact_hourly_aggregate` | one hour, per region, per channel |

**The test.** Take any fact table and state its grain in one sentence, phrased as "one row per X". Then check every measure: is it additive at that grain?

- At grain *one event*, `SUM(amount_eur)` is additive. `COUNT(*)` is additive.
- At grain *one event*, a *running balance* is **not** additive — summing running balances is meaningless. It is semi-additive, and it needs a snapshot fact table with its own grain.
- At grain *one invoice*, `SUM(line_total)` is additive, but `COUNT(*)` over the invoice fact counts invoices, not line items. If you want "how many items sold", you need the line grain.

**Why this is the hardest thing in the course.** The course's pipeline produces 4,800 events. The natural instinct is to load them all into one table `fact_events` at grain *one event*, and then aggregate. That works, and it is what `pipeline_logic.py` does:

```text
region,event_count,revenue_eur
AMER,1238,464848.02
APAC,1159,421049.85
EMEA,1176,432544.17
LATAM,1227,445554.36
```

4,800 rows in, 4 rows out. Clean. But note what the aggregate table's grain is: **one row per region, per day**. That is a *different grain* from the detail table. It belongs in a separate table, `fact_daily_region`, and the two must not be joined into one fact.

**The grain rules, in order of force:**

1. State the grain in the table's documentation, as a comment and as a `description` on the table itself. Not in a wiki nobody reads.
2. Every foreign key in a fact table must point to a dimension at *the same grain's* conformance. If `fact_events` is one row per event, and `dim_region` is one row per region, the join is many-to-one and correct.
3. A fact table may have a different grain only if it is a **different table**. Never two grains in one table. Ever.
4. Never `UPDATE` a fact row to "correct" it. Append a corrected row at the same grain and mark the original. The history is the point.
5. When someone asks "can we get revenue by channel by region by hour?", do not add a column. Ask what the grain would have to be. If the answer is a new combination, build a new aggregate fact table at that grain.

### Star vs snowflake

A **star schema** has a fact table at the centre and dimension tables directly attached, denormalised. The dimension table holds the descriptive attributes; it does not point at other tables.

```text
              dim_channel
                  |
dim_region -- fact_sales -- dim_date
                  |
              dim_customer
```

A **snowflake schema** normalises the dimensions — a `dim_channel` might point at a `dim_channel_category` table, and `dim_customer` might point at a `dim_address`.

**Opinionated position: use the star.** Snowflaking dimensions buys you a little storage and costs you a join on every query, and the join is exactly the thing the warehouse is trying to avoid. The classic reason to snowflake was normalised OLTP storage; in a warehouse, storage is the *cheapest* resource you have (BigQuery storage is $0.02/GB-month; a scan is $6.25/TB). You trade a cheap resource for an expensive one.

The one legitimate reason to normalise a dimension is a **very large, very stable, shared lookup** — a country-code table, a currency table with 150 rows, a hierarchical org chart with thousands of nodes and multiple parents. Even then, a common compromise is to keep a small flattened copy of the frequently-joined attributes alongside the reference.

**Conformed dimensions** are the other half of the star's value. A `dim_date` used by `fact_sales`, `fact_events` and `fact_traffic` — the *same* dimension, the same meaning of `date_id`, the same attributes — is conformed. This is what lets you build a combined business question ("revenue from mobile orders in AMER, against marketing spend in AMER") without a bespoke join or a reconciliation project.

Conformed dimensions are the actual reason dimensional modelling survives. Not compression, not query speed — the ability to combine facts across subject areas without lying.

### Columnar vs row-oriented storage

This is the mechanism underneath everything above.

**Row-oriented (row store):** bytes of a row are laid out consecutively on disk or in a page.

```text
[ id | name | region | amount | ts | ... ] [ id | name | region | amount | ts | ... ]
```

**Column-oriented (column store):** all values of one column are laid out consecutively.

```text
[ id   id   id   id   ... ] [ name name name name ... ] [ amount amount amount ... ]
```

**Why a column store wins for analytics.** Take a 1-billion-row table with 20 columns, and query `SELECT SUM(amount) FROM t WHERE region = 'AMER'`.

- **Row store:** the engine must fetch each of the 1 billion rows, and with each row it drags along `name`, `email`, `description` — 20 columns' worth of bytes — even though it needs two. It then applies the `region` predicate per row. Effective I/O is ~20× what the question needs.
- **Column store:** the engine reads *only* the `region` and `amount` column segments. `name` and `email` are never touched. Effective I/O is 2/20 of the row store, before any predicate pushdown, and the `region` filter can skip entire segments or whole row groups.

Two secondary benefits that matter in practice:

- **Compression.** In a column of 1 billion amounts, adjacent values are often similar or repeated. Run-length encoding and dictionary encoding collapse them enormously. A row store must encode each row independently and cannot exploit adjacency.
- **Vectorised execution.** With a column in hand, the engine processes values in batches (vectors) and applies SIMD to the filter and the sum. Modern column engines are not merely "less I/O"; they are faster per byte because the CPU work is vectorised too.

The **row-group / strip** concept completes the picture. Column stores do not read a column one value at a time; they read **row groups** (typically a few thousand rows, or a fraction of a column-chunk). Each row group stores, per column, a min/max and sometimes a null count, plus a bitmap for nulls. A predicate on a column can then **skip entire row groups** whose min/max range cannot match. This is why the predicate order and the statistics matter so much, and why BigQuery's physical reordering (below) is such a big win.

**Columnar is not free.** Column stores are bad at point lookups (you must find the row group, then the offset within the column — the classic "read the whole column to get one value" problem), bad at frequent small updates (rewriting a column chunk to change one value), and bad at short transactions. This is exactly why the warehouse and the transactional database are separate systems, and why BigQuery's `UPDATE`/`DELETE` on large tables is a batch operation, not a transactional one.

### ACID, and why the warehouse gives it up

ACID — Atomicity, Consistency, Isolation, Durability — is the OLTP contract:

- **Atomicity:** the transaction happens entirely or not at all.
- **Consistency:** the transaction moves the database from one valid state to another.
- **Isolation:** concurrent transactions do not see each other's partial work.
- **Durability:** a committed transaction survives a crash.

A warehouse trades all four for throughput, and it does so deliberately:

| Property | OLTP | Warehouse | Mechanism in BigQuery |
|---|---|---|---|
| Atomicity | Yes | Weakened | Multi-statement transactions exist, but the default is autocommit per statement; `MERGE` is not atomic across partitions by default |
| Consistency | Strict | Read-committed snapshot | A single query sees a consistent snapshot of the tables it reads |
| Isolation | Full serialisable | Snapshot | Snapshot isolation; write skew possible across row groups |
| Durability | Every commit fsynced | Bulk load semantics | Storage is durable; a job's atomicity is scoped to the job |

The important insight is that a warehouse does not need ACID because **it does not own invariants**. The invariant "`balance` must never go negative" lives in the OLTP system, enforced by its transaction. The warehouse holds a *history* of what happened — a history has no invariant to violate. The invariant that the warehouse does have is *"the total revenue for a region equals the sum of its events"*, and that is enforced by reconciliation, not by transactions: you recompute and compare, then alert on the difference.

This is why the modern pattern is **extract into the warehouse, never update the source from the warehouse**. The warehouse is a downstream copy. It can be rebuilt.

### The ETL staging architecture

Raw systems cannot be queried directly — they are slow, shaped for transactions, and behind an API. The warehouse gets its data through layers, each with a job that runs on a schedule.

```text
  SOURCE SYSTEMS                 CLOUD STORAGE                BIGQUERY
  ┌──────────────┐              ┌──────────────┐            ┌──────────────┐
  │  Cloud SQL   │   batch      │  raw zone    │            │  raw tables  │
  │  (OLTP)      ├─────────────>│  (immutable  │   load     │  (JSON/CSV,  │
  │              │  or CDC      │   landing)   ├───────────>│   90 days)   │
  │  Pub/Sub     │   streaming   └──────────────┘            └──────┬───────┘
  │  (events)    ├──────────────────────────────┐                   │
  └──────────────┘                              │              transform
                                                v                   v
                                          ┌──────────────┐    ┌──────────────┐
                                          │  dead letter │    │  staging     │
                                          │  / rejects   │    │  (validated, │
                                          └──────────────┘    │   7 days)    │
                                                                └──────┬───────┘
                                                                       │ transform
                                                                       v
                                                                ┌──────────────┐
                                                                │  curated     │
                                                                │  (dims +     │
                                                                │   facts)     │
                                                                └──────┬───────┘
                                                                       │ publish
                                                                       v
                                                                ┌──────────────┐
                                                                │  serving /   │
                                                                │  marts / BI  │
                                                                └──────────────┘
```

The layers, and what each is for:

- **Raw / landing zone.** Immutable, append-only, exactly as the source delivered it. Retained long enough to reprocess. In BigQuery this is a table; in a lakehouse it is a bucket of Parquet. **Never transform raw data in place.** Its purpose is to let you re-run history when you discover the source was wrong.
- **Staging.** Parsed, typed, validated, but not yet integrated. Where bad rows go to be counted and written to a rejects table. Short retention — it is a workspace.
- **Curated / integrated.** Dims and facts. Reconciled across sources, conformed, business-meaningful names. This is the layer BI tools and analysts query.
- **Serving / marts.** Denormalised, pre-aggregated tables shaped for a specific consumer — a dashboard's view, a model's feature set.

**The course pipeline implements exactly this**, and `pipeline_logic.py` is the model of it:

| Layer | Course artifact | Retention | Notes |
|---|---|---|---|
| Raw | `sample_data/events.ndjson` | long | immutable source of truth |
| Raw (bad) | `sample_data/malformed_events.csv` | long | 12 malformed rows, kept for reprocessing |
| Staging | `ingest_events()` → validated rows | short | 4800 accepted, 0 rejected on clean data |
| Rejects | `render_rejects_csv()`, `reject_counts()` | 30 days | 10 distinct failure reasons |
| Curated | `aggregate_events()` → `EXPECTED_SUMMARY` | long | 4 regions, conformed |
| Serving | `build_bigquery_rows()` → partition `20260115` | long | partitioned table ready for BQ |

The reject path is the part teams skip and then regret. In the course run, malformed data yields **accepted=0, rejected=12** with these counts:

```text
{'wrong_field_count': 2, 'bad_amount': 1, 'unknown_region': 2, 'unknown_channel': 1,
 'unknown_currency': 1, 'unknown_event_type': 1, 'missing_event_id': 1,
 'missing_user_id': 1, 'negative_amount': 1, 'bad_timestamp': 1}
```

Ten distinct failure reasons. A pipeline that silently drops malformed rows produces a dashboard that is *wrong by an unknown amount*. A pipeline that routes them to a rejects table with a reason produces a dashboard that is right, plus a work queue.

### Data marts

A **data mart** is a subject-oriented subset of the warehouse, usually owned by one team, shaped for that team's access patterns. "Marketing mart" with customer segments and campaign attribution. "Finance mart" with revenue recognition.

Marting is where warehouses proliferate and die. The pattern: warehouse is fine, then the marketing team asks for something the curated layer does not support, so they build a mart. Then the finance team builds one. Then the mart starts diverging from the warehouse, because someone "fixed" the revenue logic in the mart and not in the warehouse, and now two systems disagree about revenue.

**Opinionated position: build marts in the warehouse, not beside it.** The difference between a mart and a "shadow warehouse" is the direction of the ETL. A mart built *from* the warehouse with a transformation job is a mart. A mart built by *bypassing* the warehouse and pulling from the same sources is a fork, and forks rot. BigQuery's natural answer is a **dataset** — a mart as a dataset of views or tables within the same project, sharing the same underlying data and the same billing account. Looker Studio, Looker and Dataform all consume it directly.

The cost of marts is real but bounded: storage and duplicated logic. The cost of forks is unbounded: divergent numbers, and a meeting about which number is right.

### The lakehouse emergence

The classic warehouse story: structured data lands in a proprietary storage format (Parquet-on-HDFS, ORC, proprietary tables), and a warehouse engine reads it. The classic data-lake story: everything lands as open files in object storage (S3, GCS) with cheap retention, but then you need Spark to read it, and Spark is slow for single-row lookups, and writes become a rewrite-the-whole-file affair.

The **lakehouse** is the attempt to get both: open, cheap storage *and* warehouse-class SQL performance, with ACID transactions on top of open files.

The technical problems it solves:

1. **Concurrent writes on object storage.** S3 and GCS give you atomic *object* writes, not atomic *table* writes. Two jobs writing the same table would corrupt it. A lakehouse format (Iceberg, Delta Lake, Hudi) introduces a **manifest** and a **transaction log** — a commit protocol layered over the blobs. This is the single biggest piece of machinery in the format.
2. **Schema evolution.** Adding a column to a Parquet file written by yesterday's job would break every reader. Lakehouse formats track schema versions per file and let readers interpret old files correctly.
3. **Small-file problem.** Object stores make small objects cheap and free to write, so a job that writes a file per partition per minute creates millions of files, each with an HTTP round trip and a minimum read cost. Lakehouse formats plan compaction.
4. **Snapshot isolation and time travel.** Readers should see a consistent snapshot as of a commit, and you should be able to query "the table as it was last Tuesday" for debugging.

BigLake is Google Cloud's implementation: it puts Iceberg, Delta Lake and Hudi tables on Cloud Storage, and exposes them through BigQuery's SQL engine, Dataplex's catalog, and Spark. Chapter 3.4 covers the mechanics.

**The honest framing:** a lakehouse does not replace the warehouse's *model*. You still need facts, dimensions and a stated grain. What the lakehouse replaces is the warehouse's *storage format and engine coupling* — open files instead of proprietary tables, one catalog instead of a silo per tool. The dimensional model is orthogonal to the storage format, which is exactly why BigLake can serve a Kimball model stored as Iceberg.

### How the course pipeline maps onto the layers

```text
sample_data/events.ndjson       raw landing        (immutable)
sample_data/malformed_events.csv raw landing        (12 bad rows, kept)
        │
        ▼  ingest_events() + validate_event()
   accepted rows  ─────────────▶  staging            (4800 accepted, 0 rejected)
   rejected rows  ─────────────▶  rejects table      (10 reason codes)
        │
        ▼  aggregate_events()
   region summary               curated             (4 rows, conformed)
        │
        ▼  build_bigquery_rows() + partition_for_date()
   partition 20260115           serving             (BigQuery partitioned table)
```

The important detail: the malformed file is **not** deleted and **not** fixed. It sits in the raw zone. When someone later discovers that `unknown_currency` should accept `GBP` as a valid currency, the fix is a code change to `validate_event()` plus a re-run over the raw zone. That is the whole point of the raw layer, and it is the difference between a pipeline that can be corrected and one that cannot.

---

## 🛠️ Hands-On

### 1. Build a grain registry — the fact you must never lose

The first executable artefact of a dimensional model is a registry that states, for every fact table, exactly what one row means. This is the code that makes the "one grain per table" rule enforceable rather than aspirational.

```python
from dataclasses import dataclass, field


@dataclass(frozen=True)
class FactDefinition:
    """One fact table and its declared grain.

    Attributes:
        name: The table name.
        grain: One sentence: "one row per ...".
        measures: The numeric columns in the fact.
        additive: Which measures are additive at this grain.
        semi_additive: Which measures are semi-additive at this grain.
        dimensions: The dimension keys this fact joins to.
    """

    name: str
    grain: str
    measures: tuple[str, ...]
    additive: tuple[str, ...]
    semi_additive: tuple[str, ...]
    dimensions: tuple[str, ...]


@dataclass
class ModelRegistry:
    """A registry of facts and dimensions for a warehouse.

    Attributes:
        facts: Fact definitions, keyed by table name.
        dimensions: Dimension definitions, keyed by table name.
        errors: Violations found by :meth:`validate`.
    """

    facts: dict[str, FactDefinition] = field(default_factory=dict)
    dimensions: dict[str, set[str]] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def add_fact(self, fact: FactDefinition) -> None:
        """Register a fact table.

        Args:
            fact: The fact definition.
        """
        self.facts[fact.name] = fact

    def add_dimension(self, name: str, keys: set[str]) -> None:
        """Register a dimension and the keys that identify it.

        Args:
            name: The dimension name.
            keys: The columns that form the dimension's key.
        """
        self.dimensions[name] = keys

    def validate(self) -> list[str]:
        """Check the registry for grain and keying violations.

        Returns:
            A list of human-readable violations.
        """
        self.errors = []
        for fact in self.facts.values():
            if not fact.grain.lower().startswith("one row per"):
                self.errors.append(
                    f"{fact.name}: grain must be phrased as 'one row per ...', "
                    f"got {fact.grain!r}"
                )
            overlap = set(fact.additive) & set(fact.semi_additive)
            if overlap:
                self.errors.append(
                    f"{fact.name}: measure(s) {sorted(overlap)} cannot be both "
                    "additive and semi-additive at the same grain"
                )
            for dim_name, keys in self.dimensions.items():
                if dim_name in fact.dimensions and not keys:
                    self.errors.append(
                        f"{fact.name}: dimension {dim_name} has no key columns"
                    )
        return self.errors


registry = ModelRegistry()
registry.add_dimension("dim_region", {"region_key"})
registry.add_dimension("dim_channel", {"channel_key"})

registry.add_fact(
    FactDefinition(
        name="fact_events",
        grain="one row per accepted event",
        measures=("amount_eur",),
        additive=("amount_eur",),
        semi_additive=(),
        dimensions=("dim_region", "dim_channel"),
    )
)

registry.add_fact(
    FactDefinition(
        name="fact_daily_region",
        grain="one row per region per event date",
        measures=("event_count", "revenue_eur"),
        additive=("event_count", "revenue_eur"),
        semi_additive=(),
        dimensions=("dim_region",),
    )
)

problems = registry.validate()
print("violations:", problems)
print("fact tables:", sorted(registry.facts))
```

The registry earns its keep the moment someone asks to add `refund_amount` to a running-balance fact. `validate()` catches the measure being marked both additive and semi-additive, and the conversation starts from "what is the grain?" rather than "can we add the column?".

### 2. Prove that a fact table has exactly one grain

A table with two grains cannot be detected by inspection at small scale — you have to check the key that is supposed to be unique. This check is cheap and belongs in CI.

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import ingest_events

import csv
from pathlib import Path


def load_raw_rows(path: str) -> list[dict]:
    """Load raw CSV rows without validating them.

    Args:
        path: Path to the CSV file.

    Returns:
        The raw rows as dicts.
    """
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def check_grain_uniqueness(
    rows: list[dict],
    key_columns: tuple[str, ...],
) -> tuple[int, list[str]]:
    """Check that a candidate key is unique and report duplicates.

    Args:
        rows: The rows to check.
        key_columns: The columns that should form a unique key.

    Returns:
        A ``(duplicate_count, example_duplicates)`` tuple.
    """
    seen: set[tuple] = set()
    duplicates: list[str] = []
    for row in rows:
        key = tuple(str(row.get(col, "")) for col in key_columns)
        if key in seen:
            duplicates.append("|".join(key))
        else:
            seen.add(key)
    return len(duplicates), duplicates[:5]


raw = load_raw_rows("sample_data/events.csv")
dup_count, examples = check_grain_uniqueness(raw, ("event_id",))
print(f"rows={len(raw)} duplicate event_ids={dup_count}")
print("examples:", examples)

# The dedup helper in the project uses (event_id, partition) because the
# same event can legitimately arrive in two different daily partitions.
from pipeline_logic import dedup_key, partition_for_date

target_date = "2026-01-15"
partition = partition_for_date(target_date)
keys = {
    dedup_key(row["event_id"], partition)
    for row in raw
    if row.get("event_dt")
}
print(f"partition={partition} distinct dedup keys={len(keys)}")
```

Note the subtlety in the second half: `event_id` alone is *not* the natural key, because `partition_for_date()` and `partition_for_event()` can place the same logical event in different partitions. The project's `dedup_key(event_id, partition)` captures that: dedup is **within** a partition. This is exactly the kind of thing that a "one row per event" grain statement would have hidden, and exactly why grain and key are two different concepts.

### 3. Build the dimensional schema — dims, facts, and the star

The schema for the course's events, expressed as the DDL a warehouse would actually run. Note the choices: integer surrogate keys on dimensions, a date dimension with conformed attributes, and the aggregate fact at its own grain in its own table.

```sql
-- Conformed dimension: the date dimension shared by every fact table.
CREATE TABLE IF NOT EXISTS `YOUR_PROJECT_ID.curated.dim_date` (
  date_key      INT64  NOT NULL,
  date          DATE   NOT NULL,
  year          INT64  NOT NULL,
  quarter       INT64  NOT NULL,
  month         INT64  NOT NULL,
  day_of_month  INT64  NOT NULL,
  day_of_week   INT64  NOT NULL,
  week_of_year  INT64  NOT NULL,
  is_weekend    BOOL   NOT NULL,
  month_name    STRING NOT NULL
)
PARTITION BY date
CLUSTER BY year, month;

-- A conformed dimension for region. Surrogate key, natural code, and the
-- descriptive attributes analysts actually group by.
CREATE TABLE IF NOT EXISTS `YOUR_PROJECT_ID.curated.dim_region` (
  region_key    INT64  NOT NULL,
  region_code   STRING NOT NULL,
  region_name   STRING NOT NULL,
  geography     STRING NOT NULL,   -- AMERICAS / EMEA / APAC / LATAM
  continent     STRING NOT NULL
)
CLUSTER BY region_code;

-- Fact at grain: one row per accepted event.
CREATE TABLE IF NOT EXISTS `YOUR_PROJECT_ID.curated.fact_events` (
  event_id        STRING NOT NULL,
  event_dt        DATE   NOT NULL,
  event_ts        TIMESTAMP NOT NULL,
  date_key        INT64  NOT NULL,
  region_key      INT64  NOT NULL,
  channel_key     INT64  NOT NULL,
  event_type      STRING NOT NULL,
  currency        STRING NOT NULL,
  amount_eur      FLOAT64 NOT NULL
)
PARTITION BY event_dt
CLUSTER BY region_key, event_type;

-- A SECOND fact at a DIFFERENT grain, in a SEPARATE table.
-- Grain: one row per region per day.
CREATE TABLE IF NOT EXISTS `YOUR_PROJECT_ID.curated.fact_daily_region` (
  event_dt        DATE   NOT NULL,
  region_key      INT64  NOT NULL,
  event_count      INT64  NOT NULL,
  revenue_eur      FLOAT64 NOT NULL
)
PARTITION BY event_dt
CLUSTER BY region_key;
```

Two things to notice. First, `fact_daily_region` is a separate table from `fact_events` because the grain differs — this is the rule being enforced structurally, not by convention. Second, both facts partition by `event_dt` and cluster by `region_key`, which is the subject of chapter 3.3.

### 4. Model the ETL staging layers as code

The staging architecture, expressed as a set of pure transformations over the raw zone. This is the shape every production pipeline should have: the raw zone is immutable, and every layer is a pure function of the layer below.

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import (
    aggregate_events,
    ingest_events,
    render_rejects_csv,
    reject_counts,
    filter_rows_for_partition,
    partition_for_date,
    build_bigquery_rows,
)


def run_staging_pipeline(raw_lines: list[str], logical_date: str) -> dict:
    """Run raw -> staging -> curated -> serving.

    Args:
        raw_lines: The raw lines from the landing zone, unvalidated.
        logical_date: The logical processing date, ``YYYY-MM-DD``.

    Returns:
        A dict with the layer outputs.
    """
    accepted, rejected = ingest_events(raw_lines)

    summary = aggregate_events(accepted)
    rejects = reject_counts(rejected)
    partition = partition_for_date(logical_date)

    # The serving layer is the partition that this run produced. Select it
    # with the project's partition filter rather than a date comparison:
    # ``event_dt`` is a timestamp, and the filter compares the partition
    # decorator the row belongs to.
    partition_rows = filter_rows_for_partition(accepted, partition)
    serving_rows = build_bigquery_rows(partition_rows)

    return {
        "staging": {
            "accepted": len(accepted),
            "rejected": len(rejected),
            "rejects": rejects,
        },
        "curated": summary,
        "serving": {
            "partition": partition,
            "rows": len(serving_rows),
        },
        "rejects_csv": render_rejects_csv(rejected),
    }


def load_lines(path: str) -> list[str]:
    """Load raw lines from the landing zone.

    Args:
        path: Path to the file.

    Returns:
        The lines, without trailing newlines.
    """
    with open(path, encoding="utf-8") as handle:
        return [line.rstrip("\n") for line in handle if line.strip()]


clean = run_staging_pipeline(load_lines("sample_data/events.csv"), "2026-01-15")
print("clean run:", clean["staging"]["accepted"], "accepted,",
      clean["staging"]["rejected"], "rejected")
print("curated summary:", clean["curated"])

dirty = run_staging_pipeline(
    load_lines("sample_data/malformed_events.csv"), "2026-01-15"
)
print("malformed run:", dirty["staging"]["accepted"], "accepted,",
      dirty["staging"]["rejected"], "rejected")
print("rejects:", dirty["staging"]["rejects"])
```

Running this on the course data gives `4800 accepted, 0 rejected` for the clean file and `0 accepted, 12 rejected` for the malformed file, with the ten distinct reason codes. The interesting production question — which the code makes visible — is what happens when a file is *partially* bad. The pipeline still loads the good rows and quarantines the bad ones; a pipeline that rejects a whole batch on one bad line is a pipeline that will eventually stall on a poison message.

### 5. Build the conformed dimension and prove conformity

Conformity is a property you can check: the same dimension key must mean the same thing, with the same attributes, in every fact that references it.

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import ingest_events, aggregate_events


def load_lines(path: str) -> list[str]:
    """Load raw lines.

    Args:
        path: Path to the file.

    Returns:
        The lines.
    """
    with open(path, encoding="utf-8") as handle:
        return [line.rstrip("\n") for line in handle if line.strip()]


# Two facts that both reference the same region dimension.
fact_sales_rows = [
    {"region": "AMER", "amount_eur": 100.0, "event_dt": "2026-01-15"},
    {"region": "EMEA", "amount_eur": 250.0, "event_dt": "2026-01-15"},
]

fact_traffic_rows = [
    {"region": "AMER", "sessions": 10, "event_dt": "2026-01-15"},
    {"region": "APAC", "sessions": 7, "event_dt": "2026-01-15"},
]


def build_dim_region(all_rows: list[dict]) -> dict[str, dict]:
    """Build the conformed region dimension from every fact's rows.

    The dimension is built by unioning the regions referenced by all
    facts. If a fact referenced a region the others did not, the
    dimension would need a row for it — and the region codes must
    mean the same thing everywhere.

    Args:
        all_rows: Rows from every fact table.

    Returns:
        A mapping of region code to dimension attributes.
    """
    codes = sorted({row["region"] for row in all_rows})
    return {
        code: {
            "region_key": index + 1,
            "region_code": code,
            "region_name": code,
            "geography": {
                "AMER": "AMERICAS",
                "LATAM": "AMERICAS",
                "EMEA": "EMEA",
                "APAC": "APAC",
            }[code],
        }
        for index, code in enumerate(codes)
    }


dim_region = build_dim_region(fact_sales_rows + fact_traffic_rows)
print("dim_region:")
for code, attrs in dim_region.items():
    print(f"  {attrs['region_key']} {code} -> {attrs['geography']}")

# Every fact resolves its region through the SAME dimension.
sales_joined = [
    {
        "region_key": dim_region[row["region"]]["region_key"],
        "geography": dim_region[row["region"]]["geography"],
        "amount_eur": row["amount_eur"],
    }
    for row in fact_sales_rows
]
traffic_joined = [
    {
        "region_key": dim_region[row["region"]]["region_key"],
        "geography": dim_region[row["region"]]["geography"],
        "sessions": row["sessions"],
    }
    for row in fact_traffic_rows
]

print("sales by geography:", sorted(
    {(r["geography"]): r["amount_eur"] for r in sales_joined}.items()
))
print("traffic by geography:", sorted(
    {(r["geography"]): r["sessions"] for r in traffic_joined}.items()
))
```

The point of the exercise is the join at the end: sales and traffic, two different subject areas, combined on a conformed dimension, with no bespoke mapping table and no reconciliation. That is the payoff of dimensional modelling, and it is why conformed dimensions — not compression — are the reason to keep stars.

### 6. Compute the cost of the two storage layouts

Columnar versus row-oriented is not an argument; it is arithmetic. Here it is priced against the course's own pricing model.

```python
import sys
sys.path.insert(0, "project/core")

from cost_model import estimate, compare_architectures, format_comparison
from pipeline_logic import ingest_events

import csv


def load_rows(path: str) -> list[dict]:
    """Load rows from a CSV.

    Args:
        path: Path to the CSV.

    Returns:
        The rows.
    """
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


rows = load_rows("sample_data/events.csv")
regions = {row["region"] for row in rows}
print(f"detail rows: {len(rows)}")
print(f"summary rows: {len(regions)}")

# The whole warehouse re-read every day, no partitioning: the classic
# "we scan the fact table in the dashboard" mistake.
full_scan = estimate(
    "bigquery",
    scanned_tb=1.0,
    monthly=False,
    apply_free_tier=False,
)
print(full_scan)

# The same table, partitioned, reading one day out of a hundred.
partitioned = estimate(
    "bigquery",
    scanned_tb=1.0 * 0.01,
    monthly=False,
    apply_free_tier=False,
)
print(partitioned)

print(format_comparison(compare_architectures(scanned_tb=1.0)))
```

`estimate()` prints the line items; `compare_architectures()` produces the table the decision is made from. Note the shape of the output: **1.0 TB scanned costs $6.25, and 0.01 TB costs $0.0625** — a hundred-fold reduction for the same question. Chapter 3.3 does this arithmetic properly with the full cost model.

The other half of the columnar argument is that the row store would have read all twenty columns. BigQuery's columnar layout means the query above reads only `region` and `amount_eur` — a 10× reduction before any partitioning is applied. Row-oriented storage would have paid the full width.

---

## 🛠️ Common Errors and Fixes

### 1. The warehouse table where two grains live in one table

```text
ERROR: Column order mismatch for column amount_eur
```

or, more commonly and much more dangerously, no error at all — the query just returns wrong numbers:

```text
-- fact_events contains both one row per event AND, after the
-- "aggregate" job appended to it, one row per region per day.
SELECT region, SUM(amount_eur) FROM fact_events GROUP BY region;
-- Returns 464848.02 + 464848.02 = 929696.04 for AMER.
-- The summary row was added to the detail rows.
```

This is the single most destructive modelling mistake, because the query succeeds. The fix is structural: separate tables, separate grains, and a grain statement on each.

```sql
-- WRONG: one table, two grains.
-- RIGHT: two tables, one grain each.

CREATE TABLE `YOUR_PROJECT_ID.curated.fact_events` (
  event_id STRING NOT NULL, ... ) PARTITION BY event_dt;

CREATE TABLE `YOUR_PROJECT_ID.curated.fact_daily_region` (
  event_dt DATE NOT NULL, region_key INT64 NOT NULL,
  event_count INT64 NOT NULL, revenue_eur FLOAT64 NOT NULL
) PARTITION BY event_dt;
```

Then add a test that asserts the grain holds — uniqueness of the candidate key — so the mistake cannot reach production.

### 2. Running the aggregate on the transactional database

```text
ERROR: 400 Bad Request: Job exceeded rate limits: resources: too many concurrent queries
```

or, painfully, the query succeeds but takes 47 seconds and holds locks:

```text
ERROR: canceling statement due to lock timeout
```

The symptom is a dashboard query on the transactional store that used to be fast and became slow right after the transactional workload grew. The cause is running an analytical aggregate against the OLTP store. The fix is to extract and aggregate in the warehouse:

```sql
-- Run in Cloud SQL: stream out without holding locks for the aggregation.
EXPORT DATA OPTIONS (
  uri 'gs://YOUR_BUCKET/exports/orders-*.csv',
  format 'CSV',
  overwrite true
);
```

```sql
-- Then in BigQuery:
SELECT region, COUNT(*) AS event_count, SUM(amount_eur) AS revenue_eur
FROM `YOUR_PROJECT_ID.curated.events`
WHERE event_dt BETWEEN '2026-01-01' AND '2026-01-15'
GROUP BY region
ORDER BY region;
```

### 3. The dimension table that is a `SELECT *` over the source

```text
ERROR: Column order mismatch for column region_code
```

or the subtler version — a dimension rebuilt nightly from the source, whose surrogate keys **change every night** because the row order changed:

```text
-- Yesterday: AMER had region_key = 1.
-- Today:     AMER has region_key = 3.
-- Every historical fact row now points at the wrong dimension row.
```

The symptom is a dashboard where last month's revenue by region no longer matches last month's report. The fix is a **stable surrogate key**, assigned once and never recomputed, with the natural code as an attribute and a uniqueness constraint on the code.

```sql
-- Assign surrogate keys once, from a deterministic source, and keep them.
-- Never: ROW_NUMBER() OVER (ORDER BY code) recomputed nightly.
```

```python
# The safe pattern: allocate from a max-ever counter, not from row order.
def allocate_keys(existing: dict[str, int], codes: list[str]) -> dict[str, int]:
    """Assign stable surrogate keys to dimension codes.

    Args:
        existing: Existing code -> key mapping, loaded from the dimension table.
        codes: The codes that need a key.

    Returns:
        The full code -> key mapping, including newly allocated keys.
    """
    result = dict(existing)
    next_key = max(existing.values(), default=0) + 1
    for code in sorted(codes):
        if code not in result:
            result[code] = next_key
            next_key += 1
    return result
```

The same discipline applies to the course's dimension build: `dim_region` must map `AMER` to a key that stays put while new regions are added.

### 4. Snowflaking the dimensions "to save space"

```text
-- The symptom, not an error: queries got 3x slower and cost 3x more.
SELECT c.segment_name, COUNT(*) FROM fact_sales f
JOIN dim_customer c ON f.customer_key = c.customer_key
JOIN dim_segment s ON c.segment_key = s.segment_key
GROUP BY c.segment_name;
```

The snowflake added a join on every query to save a few megabytes of dimension storage. At $0.02/GB-month, a dimension of 10 million rows costs about $2/month to store. The join costs seconds and dollars per query, forever.

The fix is to flatten: bring the attributes you actually group by into the dimension itself, and keep the normalised reference only for genuinely large, shared, multi-parent structures.

### 5. The raw zone that was transformed in place

```text
ERROR: Could not parse JSON: Unexpected token at [row 1, byte 447]
```

The symptom appears weeks later, when a source bug is discovered and the pipeline is re-run over the raw zone — and the raw zone no longer contains the original data, because the transform overwrote it.

The fix is immutability by construction: write raw data to a new path, never update an existing object. In BigQuery, use `CREATE TABLE ... AS SELECT` into a dated partition, and never `UPDATE` a raw table. In Cloud Storage, use object versioning on the landing bucket.

```bash
# Enable versioning on the landing bucket so an overwrite is recoverable.
gcloud storage buckets update gs://YOUR_RAW_BUCKET --versioning
```

The rule: **the raw zone is append-only, and the only write mode is "create a new object".**

### 6. The silent drop of malformed rows

No error message. The pipeline logs `ingest: 4800 accepted, 0 rejected` on a good day and `ingest: 4790 accepted, 0 rejected` on a bad day, and nobody notices for three weeks.

The cause is an ingest function that returns only the good rows, with the bad ones discarded inside a `try/except: pass`. The fix is to make rejection a first-class output with a reason code and a persisted rejects table — which is exactly what the course project does:

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import ingest_events, reject_counts, render_rejects_csv

with open("sample_data/malformed_events.csv", encoding="utf-8") as handle:
    lines = [line.rstrip("\n") for line in handle if line.strip()]

accepted, rejected = ingest_events(lines)
counts = reject_counts(rejected)

print(f"accepted={len(accepted)} rejected={len(rejected)}")
for reason, count in sorted(counts.items()):
    print(f"  {reason}: {count}")
```

The output for the course's malformed file:

```text
accepted=0 rejected=12
  bad_amount: 1
  bad_timestamp: 1
  missing_event_id: 1
  missing_user_id: 1
  negative_amount: 1
  unknown_channel: 1
  unknown_currency: 1
  unknown_event_type: 1
  unknown_region: 2
  wrong_field_count: 2
```

Ten reason codes from twelve rows. A pipeline that drops these rows produces a report that is wrong by an unknown amount; a pipeline that counts them produces a report that is right plus a work queue.

---

## 💡 Production Notes

- **Write the grain on the table, not in a wiki.** Set the table `description` to "Grain: one row per accepted event" and put a `COMMENT`/description on the grain column. The next engineer will not read your wiki; they *will* read the table they are querying.
- **Treat the raw layer as immutable and the curated layer as rebuildable.** If you cannot rebuild the curated layer from raw in under an hour, you do not have a warehouse — you have a pile of tables with dependencies. Rebuildability is what makes schema changes cheap.
- **Never `UPDATE` a fact row.** Append a corrected row and mark the original. Overwriting history in a warehouse destroys the only thing the warehouse is for. Corrections are new rows.
- **Keep surrogate keys stable forever.** Allocate them once from a monotonic counter, never from `ROW_NUMBER() OVER (ORDER BY ...)`. A nightly-recomputed surrogate key silently corrupts every historical fact row that references it.
- **Reject with a reason code and persist the rejects.** The course's ten reason codes — `wrong_field_count`, `bad_amount`, `unknown_region` — are not decoration. They are the difference between "the dashboard is slightly off" and "we know exactly which 12 rows are bad and why".
- **Model `NULL` explicitly.** In a fact table, a `NULL` measure usually means "not applicable" or "not yet loaded" — two very different things. Use a sentinel or a separate flag column, and never let `NULL` silently propagate into a `SUM`.
- **Reconcile, do not enforce.** The warehouse's correctness control is a daily comparison of an aggregate computed two ways (for example the sum of `fact_daily_region` against a re-aggregation of `fact_events`), alerting on the difference. Transactions are the wrong tool for a warehouse; reconciliation is the right one.
- **Put marts inside the warehouse as datasets.** A mart that is a dataset of views shares data, billing and lineage with the warehouse. A mart that pulls from the source systems is a fork, and forks rot into two disagreeing revenue numbers.
- **Enforce "one grain per table" in CI.** A uniqueness check on the fact's candidate key runs in seconds and prevents the most expensive modelling mistake you can make — one that usually produces no error at all.

---

## 🔑 Key Takeaways

- **OLTP and OLAP are structurally incompatible**, not merely different query styles: row store vs column store, index maintenance vs full scans, millisecond SLO vs second-level target. Separate the systems and move data between them.
- **A warehouse is integrated, time-variant, non-volatile, subject-oriented, read-optimised, and large.** That is a definition by properties, not by product.
- **Kimball's model is facts and dimensions.** Facts are narrow and measured; dimensions are wide and descriptive. Star schemas denormalise the dimensions deliberately.
- **The fact grain is the single most important concept.** "One row per X", stated in the table, enforced by a uniqueness check. Two grains in one table is the most common and most dangerous modelling mistake, because it usually produces wrong numbers instead of an error.
- **Columnar storage is not an optimisation; it is a requirement for analytics.** Read only the columns you need, exploit adjacency for compression, and use row-group statistics to skip entire blocks. It is also why warehouses are bad at point lookups and updates — the trade is deliberate.
- **ACID is the OLTP contract and the warehouse gives it up deliberately**, because the warehouse owns no invariants. Its correctness control is reconciliation, not transactions.
- **The staging layers are raw → staging → curated → serving.** Raw is immutable and long-retained so history can be reprocessed; curated is a rebuildable function of raw.
- **Conformed dimensions are why dimensional modelling still wins.** They let you combine facts across subject areas without a bespoke mapping and without disagreeing with yourself.
- **Marts belong inside the warehouse, as datasets.** A mart that bypasses the warehouse is a fork, and forks rot.
- **The lakehouse changes the storage format and the catalog, not the model.** Facts, dimensions and grain are still required; Iceberg on Cloud Storage is a way to store a Kimball model, not a way to avoid designing one.

---

## 📚 Practice Exercises

1. **Write the grain registry for a full warehouse.** Extend the `ModelRegistry` from the Hands-On section to cover a complete retail warehouse: `fact_sales_line` (grain: one line item on one invoice), `fact_sales` (one invoice), `fact_inventory_snapshot` (one SKU per warehouse per day), `fact_returns`, and dimensions `dim_date`, `dim_product`, `dim_customer`, `dim_store`, `dim_promotion`. Identify which measures are additive and which are semi-additive at each grain — in particular, why `fact_inventory_snapshot.on_hand_qty` is not additive and what you would need to answer "total stock across the estate".
2. **Build a conformance test suite.** Write `assert_conformed(dims: dict[str, dict]) -> list[str]` that takes the dimension tables as they exist in the warehouse and checks: (a) every fact's dimension key resolves to exactly one dimension row, (b) the same dimension code has the same surrogate key in every table it appears in, (c) no dimension has a null key, (d) every dimension referenced by a fact exists. Run it against the course's data by loading the summary and the detail aggregation and confirming they agree.
3. **Detect the mixed-grain table.** Write `find_grain_violations(rows, key_columns, measure_columns) -> list[str]` that identifies rows whose key is duplicated *and* whose measure values are identical (the signature of an aggregate row appended to a detail table), and rows whose key is duplicated with differing measures (the signature of two legitimate rows sharing a bad key). Apply it to a table you deliberately contaminate with the course's summary rows, and show it catching both signatures.
4. **Model a new mart correctly.** The marketing team wants "revenue by region, channel, and hour for the last 90 days" for a dashboard. Using the dimensional model, decide: is this a new aggregate fact table, a view over `fact_events`, or a change to `fact_daily_region`? State the grain of your answer, write the DDL with a sensible partitioning and clustering scheme, and explain what you would tell the marketing team about data freshness and the cost of the query.
5. **Cost the staging architecture.** Use `estimate()` from `project/core/cost_model.py` to price the course's pipeline for one month, assuming: 4,800 events per day in the raw zone (730 days of run), 12 malformed rows per batch quarantined to a rejects table, 1 TB of curated data, a Dataflow streaming job running 730 hours, Pub/Sub ingest and delivery of the same volume, and Cloud Storage holding the raw zone at Standard with a lifecycle move to Nearline after 30 days. Produce the monthly total, and then produce a second version in which the streaming path is replaced by a nightly batch job and quantify what streaming buys for its cost.
6. **Design the lakehouse equivalent of the curated layer.** Write the Iceberg-style table definition you would use to store `fact_events` — partition spec, sort order, and the metadata columns Iceberg adds — and explain which of the four lakehouse problems (concurrent writes, schema evolution, small files, snapshot isolation) each choice addresses. Then explain why the *grain* statement from exercise 1 is still mandatory with an open table format, and what tool you would use to enforce it.
7. **Write the ADR.** Draft the decision record for the warehouse's storage strategy: raw in BigQuery raw tables vs raw in a Cloud Storage landing zone with a BigLake Iceberg table; the dimensional model (star with conformed dims vs snowflake); the mart strategy (datasets inside the warehouse vs separate projects). Include the rejected options with reasons, and the "what would make us change our mind" clause.

---

## 📖 Further Reading

- [BigQuery architecture overview](https://cloud.google.com/bigquery/docs/introduction) — how the warehouse separates storage from compute
- [BigQuery storage overview](https://cloud.google.com/bigquery/docs/storage-overview) — columnar layout, row groups, and physical reordering
- [Kimball dimensional modeling techniques](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/) — the canonical description of grain, facts and dimensions
- [Dimensional modeling, star schemas and grains](https://cloud.google.com/bigquery/docs/dimensional-modeling) — Google's guidance on warehouse design
- [BigQuery data modeling best practices](https://cloud.google.com/bigquery/docs/best-practices-data-modeling) — Google's concrete modelling guidance
- [BigLake overview](https://cloud.google.com/biglake/docs/introduction) — open table formats on Cloud Storage
- [Apache Iceberg table format](https://iceberg.apache.org/) — the transaction and snapshot model behind lakehouse tables
- [Google Cloud Architecture Framework: Data Analytics](https://cloud.google.com/architecture/data-analytics) — reference patterns for warehouse and lakehouse designs
