# 7.1 — Capstone: The Complete Project

> **Section 7 · Capstone · Lecture 7.1 · 35 min**

## 🎯 What you will learn

- The complete project, assembled from every chapter — and the order to
  build it in
- The **five properties** a CDC pipeline must have, and how to test each
  one
- How to build a **reconciliation harness** that validates the destination
  against the source
- What to put in the runbook, so the next person can operate it
- How to answer "is this pipeline correct?" with a number, not a feeling

---

## 🧠 Concept

### The project

A CDC pipeline that replicates a `customers` table from MySQL into
BigQuery, plus a Kafka path that lands transactions in Cloud SQL.

```text
  ┌──────────────────────────────────────────────────────────────────┐
  │  PATH A — Datastream                                            │
  │                                                                  │
  │  MySQL ──binlog──▶ Datastream ──merge──▶ BigQuery               │
  │                      │                                           │
  │              network config, source config,                      │
  │              destination config, stream                          │
  └──────────────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────────────────────┐
  │  PATH B — Confluent Kafka                                       │
  │                                                                  │
  │  Kafka topic ──GCF sink──▶ Cloud Run Function ──▶ Cloud SQL      │
  │                              │                                  │
  │                    fetch secret → parse → insert                │
  └──────────────────────────────────────────────────────────────────┘
```

Both paths share one idea: **a keyed merge, and a database that enforces
uniqueness.**

### Build order

The order is not arbitrary. Each step is verifiable before the next one
exists.

| # | Step | Verified by |
|---|---|---|
| 1 | The source is configured for CDC | `SHOW VARIABLES LIKE 'binlog_format'` |
| 2 | The merge logic is implemented and tested | `pytest project/tests/` |
| 3 | The destination table exists, partitioned and clustered | `bq show --table` |
| 4 | The network config and connection profile work | `gcloud datastream connection-profiles describe` |
| 5 | The stream runs and the table fills | Row count grows |
| 6 | The values are correct | **The reconciliation harness** |
| 7 | The Kafka path lands rows exactly once | Duplicate count is zero |
| 8 | The runbook exists | Someone else can operate it |

Step 6 is separate from step 5 on purpose. A table that is *filling* is
not a table that is *correct*, and the only thing that distinguishes them
is a value-level comparison.

### The five properties

A CDC pipeline is correct when all five hold. Each is testable, and each
has failed in production.

| # | Property | Test | Failure it prevents |
|---|---|---|---|
| 1 | **Convergence** | Two independent replays give the same table | Non-deterministic merges |
| 2 | **Idempotency** | Replaying onto a populated table changes nothing | Duplicate rows after a retry |
| 3 | **Order-sensitivity is understood** | Delete-then-insert differs from insert-then-delete | Silent divergence from the source |
| 4 | **Completeness** | Every source row is represented | Missing rows, dropped events |
| 5 | **Correctness** | Every row matches the source's values | Wrong merge key, wrong schema |

Properties 1–3 are properties of the *merge*, and they are pure logic —
they need no cloud and they run in milliseconds. Properties 4 and 5 are
properties of the *pipeline*, and they need the source.

This split is why the course's testing strategy is what it is: test the
merge exhaustively and cheaply, test the pipeline end to end and
occasionally.

### The reconciliation harness

The harness is the most valuable piece of the project, and the one teams
most often skip.

```python
def reconcile(destination_rows, source_rows, key="customer_id"):
    """Return the rows that differ between the destination and the source.

    A row is "the same" when every field except the ingestion metadata
    matches. The harness compares *values*, never counts.
    """
    dest = {row[key]: row for row in destination_rows}
    src = {row[key]: row for row in source_rows}

    missing = set(src) - set(dest)
    extra = set(dest) - set(src)
    differing = {
        k for k in set(src) & set(dest)
        if dest[k] != src[k]
    }

    return {
        "missing": sorted(missing),
        "extra": sorted(extra),
        "differing": sorted(differing),
        "in_sync": not (missing or extra or differing),
    }
```

Run it on a sample every night, and alert on `in_sync: false`. This
catches:

- a wrong merge key (many rows "differing" or "extra")
- dropped events (some rows "differing")
- a failed delete (rows "extra")
- a schema change (columns "differing")

**Sample, do not compare everything.** A full comparison on a large table
is expensive and slow. A random sample of 10,000 rows per night catches a
systematic problem immediately and a rare one eventually. That is the right
trade for a safety net.

### The runbook

The runbook is not documentation. It is the thing you read at 3am. It
should be short enough to read in full while a stream is down.

```markdown
## CDC pipeline runbook

### Is the stream running?
gcloud datastream streams describe main-stream --location=us-central1 \
  --format="value(streamState)"

### The stream is READY but the table is stale
1. Check the source is producing changes:
   SHOW BINARY LOGS;  SHOW MASTER STATUS;
2. Check the source's privileges:
   SHOW GRANTS FOR 'datastream_user'@'%';
3. Check the binary log settings:
   SHOW VARIABLES LIKE 'binlog_format';
   SHOW VARIABLES LIKE 'binlog_row_image';
4. Check the firewall allows the Datastream IP:
   gcloud datastream network-configs ip-pools list --location=us-central1

### The stream is FAILED
The error message names the object. Common ones:
  - "Failed to connect"      → host/port/firewall
  - "does not have REPLICATION" → GRANT REPLICATION SLAVE, REPLICATION CLIENT
  - "binlog_format is not ROW" → fix the source config
  - "The merge key does not exist" → fix the destination config

### The table is filling but the values are wrong
1. Check the merge key:
   gcloud datastream destination-configs describe bigquery-destination \
     --location=us-central1 --format="value(bigqueryDestinationConfig.sourceTables)"
2. Run the reconciliation harness.
3. If the merge key is wrong → fix it and rebuild (see below).

### Rebuild the destination
1. Pause the stream.
2. DROP TABLE `PROJECT.datastream.customers`;
3. Recreate it (see sql/create_customers.sql).
4. Update the stream with --backfill-all.
5. Resume the stream.
```

---

## 🛠️ Hands-On: The Full Project

### Run everything

```bash
cd data-engineering/data-Course/google/Datastream

python3 -m venv .venv
source .venv/bin/activate
pip install -r project/requirements.txt

# 1. Generate the sample data
python resources/sample_data.py --output-dir ./sample_data

# 2. Run the CDC pipeline
python project/cdc_pipeline.py \
    --input ./sample_data/changes.ndjson \
    --output ./out/customers \
    --merge-keys customer_id

# 3. Run the Kafka path
python project/kafka_to_gcp.py \
    --messages ./sample_data/transactions.ndjson \
    --dry-run

# 4. Run the tests
python -m pytest project/tests/ -q

# 5. Lint the course
python resources/audit_course.py
```

### Property 1 — convergence

```python
import json
from pathlib import Path
from cdc import CdcState

events = [
    json.loads(line)
    for line in Path("./sample_data/changes.ndjson").read_text().splitlines()
    if line.strip()
]

first = CdcState(merge_keys=["customer_id"])
first.apply_events(events)

second = CdcState(merge_keys=["customer_id"])
second.apply_events(events)

print("convergent:", first.snapshot() == second.snapshot())
```

```text
convergent: True
```

### Property 2 — idempotency

```python
third = CdcState(merge_keys=["customer_id"])
third.apply_events(events)
before = third.snapshot()
third.apply_events(events)

print("idempotent:", before == third.snapshot())
print("rows:", third.row_count())
```

```text
idempotent: True
rows: 186
```

### Property 3 — order sensitivity

```python
row = {"customer_id": "c1", "tier": "gold"}

delete_first = CdcState(merge_keys=["customer_id"])
delete_first.apply_event({"op": "DELETE", "before": row})
delete_first.apply_event({"op": "INSERT", "after": row})

insert_first = CdcState(merge_keys=["customer_id"])
insert_first.apply_event({"op": "INSERT", "after": row})
insert_first.apply_event({"op": "DELETE", "before": row})

print("delete then insert ->", delete_first.row_count(), "row(s)")
print("insert then delete ->", insert_first.row_count(), "row(s)")
```

```text
delete then insert -> 1 row(s)
insert then delete -> 0 row(s)
```

### Property 4 — completeness

```python
# Every customer that was inserted and not deleted must be in the table.
inserted = {
    e["after"]["customer_id"]
    for e in events
    if e.get("op") == "INSERT" and e.get("after")
}
deleted = {
    e["before"]["customer_id"]
    for e in events
    if e.get("op") == "DELETE" and e.get("before")
}
expected = inserted - deleted
actual = {r["customer_id"] for r in first.snapshot()}

print("expected rows:", len(expected))
print("actual rows  :", len(actual))
print("missing      :", sorted(expected - actual))
print("extra        :", sorted(actual - expected))
```

```text
expected rows: 186
actual rows  : 186
missing      : []
extra        : []
```

### Property 5 — correctness

```python
# Compare against the source, field by field.
def reconcile(destination_rows, source_rows, key="customer_id"):
    dest = {row[key]: row for row in destination_rows}
    src = {row[key]: row for row in source_rows}

    missing = set(src) - set(dest)
    extra = set(dest) - set(src)
    differing = {k for k in set(src) & set(dest) if dest[k] != src[k]}

    return {
        "missing": sorted(missing),
        "extra": sorted(extra),
        "differing": sorted(differing),
        "in_sync": not (missing or extra or differing),
    }


# Reconstruct the expected table directly from the events.
expected_rows = {}
for event in events:
    op = event.get("op")
    image = event.get("after") if op in ("INSERT", "UPDATE") else event.get("before")
    if image is None:
        continue
    key = image.get("customer_id")
    if key is None:
        continue
    if op == "DELETE":
        expected_rows.pop(key, None)
    else:
        expected_rows[key] = dict(image)

result = reconcile(first.snapshot(), list(expected_rows.values()))
print("in sync:", result["in_sync"])
print("missing:", len(result["missing"]))
print("extra  :", len(result["extra"]))
print("differing:", len(result["differing"]))
```

```text
in sync: True
missing: 0
extra  : 0
differing: 0
```

That is the answer to "is this pipeline correct?" — a boolean and three
counts, computed from an independent reconstruction of the expected table.

### The destination DDL

```sql
CREATE TABLE IF NOT EXISTS `YOUR_PROJECT_ID.datastream.customers` (
    customer_id STRING NOT NULL,
    first_name  STRING,
    last_name   STRING,
    email       STRING,
    region      STRING,
    tier        STRING,
    created_at  TIMESTAMP,
    ingested_at TIMESTAMP
)
PARTITION BY DATE(_PARTITIONTIME)
CLUSTER BY customer_id;
```

Two things matter here:

- `customer_id STRING NOT NULL` — the merge key cannot be NULL, because
  a NULL key cannot be matched.
- `CLUSTER BY customer_id` — the merge sorts on this column. Clustering
  on the merge key is the single most effective BigQuery optimisation for
  a CDC destination.

The full DDL is in `sql/create_customers.sql`.

### Deploying the infrastructure

```bash
cd project/terraform

terraform init
terraform plan -var="project_id=YOUR_PROJECT_ID" -var="region=us-central1"
terraform apply -var="project_id=YOUR_PROJECT_ID" -var="region=us-central1"
```

The Terraform creates the network config, IP allocation, connection
profiles, source config, destination config and stream. The
`merge_keys` variable is the one to get right:

```hcl
variable "merge_keys" {
  description = "The merge key columns. These identify a row uniquely in the destination."
  type        = list(string)
  default     = ["customer_id"]
}
```

---

## 🛠️ Common Errors and Fixes

### The reconciliation reports many "differing" rows

Almost always the merge key. Check it:

```bash
gcloud datastream destination-configs describe bigquery-destination \
    --location=us-central1 \
    --format="value(bigqueryDestinationConfig.sourceTables)"
```

If it is wrong, fixing the config does **not** fix the existing rows —
they were already merged wrongly. Rebuild the destination.

### The reconciliation reports "extra" rows

Deletes are not being applied. Either the source's `binlog_row_image` is
`MINIMAL` (so the delete events cannot identify the row), or the delete
events are not reaching the destination.

### The reconciliation reports "missing" rows

Inserts are being dropped, or the backfill did not cover the table.

### Everything is "in sync" but the data is wrong

The harness compared the destination against a reconstruction from the
**same** stream. If the stream itself is wrong — wrong table, wrong
source — the reconstruction is wrong too. Reconcile against the **source
database**, not against the stream.

### The tests pass but the pipeline does not

The tests cover the merge. The pipeline's failures are in the parts the
merge does not touch: connectivity, IAM, quotas, schema changes. Keep the
reconciliation harness as the test for those.

---

## 💡 Production Notes

- **The reconciliation harness is the deliverable.** The pipeline is
  replaceable; the harness is what tells you whether the replacement
  works.
- **Reconcile against the source, not the stream.** Comparing the
  destination to a reconstruction of the stream proves the merge works.
  Comparing it to the source proves the *pipeline* works. You want the
  second.
- **Run the reconciliation on a sample nightly.** A full comparison is
  expensive; a 10,000-row sample catches systematic problems immediately.
- **Keep the runbook executable.** Every command in it should be a command
  you have actually run.
- **Test the merge exhaustively; test the pipeline end to end.** The
  merge is where the subtle bugs are, and it is free to test.
- **Make the merge key a variable, and log it.** When a stream is
  misconfigured months later, you want to know what key it was configured
  with without reading the terraform.

---

## 🔑 Key Takeaways

- Build in **verifiable order**: merge → schema → network → stream →
  correctness.
- The five properties are **convergence, idempotency, order-sensitivity,
  completeness, correctness**. Each is testable, each has failed in
  production.
- The **reconciliation harness** compares values, not counts, against the
  **source**.
- A table that is **filling** is not a table that is **correct**.
- The runbook should be **short enough to read while the stream is
  down**.
- A wrong merge key is not fixed by correcting the configuration — the
  existing rows must be **rebuilt**.

---

## 📚 Practice Exercises

1. **Complete the reconciliation harness.** Add a `sample` mode that
   compares a random sample of N rows, and a `diff` mode that prints the
   first ten differing rows field by field.

2. **Write the source-side reconciliation.** Write the BigQuery SQL that
   compares the destination against a nightly export from the source, and
   returns only the differing rows.

3. **Extend the runbook.** Add sections for: the Kafka path being down, a
   Cloud SQL connection failure, and the cost of the pipeline being
   higher than expected.

4. **Prove property 5 is necessary.** Construct a case where the
   reconciliation against the stream says "in sync" but the data is wrong.
   Then explain what the source-side reconciliation would report.

5. **Reflection.** Your team wants to replace the nightly reconciliation
   with a row-count check, because the full comparison is expensive.
   Give the three strongest arguments against, using the specific failures
   each one misses.

---

## 📖 Further Reading

- BigQuery table constraints — https://cloud.google.com/bigquery/docs/reference/standard-sql/data-definition-language#table_constraints
- Datastream's backfill and recovery — https://cloud.google.com/datastream/docs/backfill
- Terraform's Datastream resources — https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/datastream_stream
- *Designing Data-Intensive Applications*, Martin Kleppmann, Chapter 11
  ("Streaming Data") — on deriving state from a log
