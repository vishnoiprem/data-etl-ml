# Google Cloud Datastream & Change Data Capture — Master the Log, the Merge, and the Stream

A complete, hands-on guide to **change data capture** and **Google Cloud Datastream** for data
engineers — and to the **Confluent Kafka → GCP** path that runs alongside it.

Every topic is taught from first principles — the write-ahead log, the keyed merge, the merge key,
the read consistency window, backfills, schema evolution, reconciliation, and the Kafka consumer
contract — and then exercised for real through a **working project that runs locally with no GCP
account, no credentials and no bill**.

> **Duration:** 4 modules · 7 chapters · 6 notebooks · ~32 hours
> **Audience:** Data engineers, analytics engineers, and platform engineers who build or operate
> replication pipelines.

---

## What You Will Learn

- **CDC from first principles** — the write-ahead log, the three layers (log → transport → sink),
  and why polling *structurally cannot* detect deletes or respect transaction boundaries.
- **The keyed merge** — every clause, every skip reason, and why idempotency falls out of the
  merge's shape rather than being a feature you configure.
- **The merge key** — why it must be **unique, immutable and minimal**, and what silently breaks
  when it is not.
- **Source configuration** — `binlog_format=ROW`, `binlog_row_image=FULL`, `wal_level=logical`,
  replication slots, the replication user's privileges, and the VPC path to the source.
- **Schema evolution** — new columns, dropped columns, changed types, and the three defensible
  responses to each.
- **Backfills and recovery** — the three backfill modes, why the destination must be empty, and
  how to rebuild a corrupted destination from the log.
- **Operations** — telling a *lagging* pipeline from a *broken* one, the four metrics that matter,
  the reconciliation query that compares **values** rather than counts, and the cost model.
- **The Kafka path** — at-least-once delivery, consumer groups, why the **partitioning key must
  equal the merge key**, the Confluent GCF sink connector, the 4xx/5xx contract, and dead-letter
  queues.
- **The Cloud Run function** — the three stages (fetch secret → parse → insert), why the INSERT
  must be parameterised, and where the database password belongs.
- **56 + 50 interview questions** with answers written the way a senior engineer answers them.

---

## Course Structure

### Module 1 — The Foundations

| # | Chapter | Covers |
|---|---------|--------|
| 1.1 | [What Is Change Data Capture?](chapters/01-what-is-change-data-capture.md) | The log vs the table; why polling cannot detect deletes; event amplification; the read consistency window; streaming vs synchronised merge |

### Module 2 — The Merge

| # | Chapter | Covers |
|---|---------|--------|
| 2.1 | [The Merge & Merge Keys](chapters/02-the-merge-and-merge-keys.md) | Every clause of the `MERGE`; the merge key rules; idempotency; the event envelope; BigQuery clustering and partitioning; the cost model |

### Module 3 — The Source

| # | Chapter | Covers |
|---|---------|--------|
| 3.1 | [Sources & the Binary Log](chapters/03-sources-and-the-binary-log.md) | `ROW` vs `STATEMENT`; `binlog_row_image`; `wal_level`; the replication user as a security concern; the VPC path and its firewall |
| 3.2 | [Schema Evolution & Backfills](chapters/04-schema-evolution-and-backfills.md) | New/dropped/changed columns; the three responses; the backfill modes; recovery from a truncated log; migration windows |

### Module 4 — Operations, Kafka & the Capstone

| # | Chapter | Covers |
|---|---------|--------|
| 4.1 | [Kafka & Confluent](chapters/05-kafka-and-confluent.md) | Consumer groups; partition key = merge key; the GCF sink connector; 4xx vs 5xx; poison messages and DLQs; Confluent's byte-based billing |
| 4.2 | [Operations & Troubleshooting](chapters/06-operations-and-troubleshooting.md) | Lagging vs broken; the triage sequence; latency vs lag; reconciliation; the DML quota; cost levers |
| 4.3 | [Capstone Project](chapters/07-capstone-project.md) | The full pipeline end to end: the Datastream side, the Kafka side, the deployment, and the runbook |

---

## Hands-On Notebooks

Six notebooks, each of which **executes top-to-bottom with no GCP account**. Every cloud cell is
gated behind an environment check, so the notebooks run identically on a laptop and in Colab.

| # | Notebook | Module | What you build |
|---|----------|--------|----------------|
| 01 | [Setup & the CDC Mental Model](notebooks/01-setup-and-cdc-mental-model.ipynb) | 1.1 | The log → transport → sink model; event amplification; the merge, live |
| 02 | [Change Events & Schema](notebooks/02-change-events-and-schema.ipynb) | 2.1, 3.2 | Parse a change event; the before/after images; schema evolution; a custom consumer |
| 03 | [The Merge & BigQuery](notebooks/03-the-merge-and-bigquery.ipynb) | 2.1 | Write the `MERGE`; clustering and partitioning; the merge key rules |
| 04 | [Source Configuration](notebooks/04-source-configuration.ipynb) | 3.1 | The source config, the privileges, the network path; what to check when nothing arrives |
| 05 | [The Kafka → GCP Pipeline](notebooks/05-kafka-to-gcp-pipeline.ipynb) | 4.1 | Consumer groups, the partition key, the function's three stages, the 4xx/5xx contract |
| 06 | [End-to-End Project](notebooks/06-end-to-end-project.ipynb) | All | The full pipeline, run and cross-validated against the source |

---

## The Project

A working CDC project that runs **locally with no GCP account, no credentials, and no bill**. The
same code deploys to Datastream and Cloud Run by changing the configuration, not the logic.

```
project/
├── cdc.py               # The merge engine — pure stdlib, no GCP, no dependencies
├── cdc_pipeline.py      # CLI: read change events → apply the merge → write CSV + JSON + audit
├── kafka_to_gcp.py      # The Confluent path: parse → validate → parameterised INSERT → Postgres
├── cloud_function.py    # The deployable Cloud Run / Cloud Functions handler
├── terraform/           # Network config, source config, destination config, stream
└── tests/               # 83 tests (82 pass, 1 skipped without the Secret Manager SDK)
```

The design decision that makes it work: **`cdc.py` is pure standard library**. The merge semantics
are the hard part, and they must be testable without a network, a credential, or a bill. Every
other CDC tool — Debezium, Fivetran, a hand-rolled consumer — reimplements the same four merge
behaviours, and `cdc.py` is them, in about forty readable lines.

```bash
python resources/sample_data.py --output-dir ./sample_data

python project/cdc_pipeline.py \
    --input ./sample_data/changes.ndjson \
    --output ./out/customers \
    --merge-keys customer_id
# CDC replay summary
# ----------------------------------------------------
#   events read          : 377
#   rows in table        : 186
#   changes applied      : 374
#   events skipped       : 8
#   skip reasons:
#     delete_of_absent_row      : 2
#     duplicate_insert          : 5
#     missing_merge_key         : 1

python project/kafka_to_gcp.py \
    --messages ./sample_data/transactions.ndjson \
    --dry-run
# Kafka → GCP replay summary
# ----------------------------------------------------
#   messages read    : 500
#   ingested         : 500
#   rejected         : 0
```

The sample data is deterministic (`SEED = 42`) and deliberately imperfect: it contains **duplicate
inserts**, a **delete for a row that was never inserted**, and **one malformed event** — so the
skip counters above are real, not decorative.

See [`project/README.md`](project/README.md) for the full walkthrough and the deploy path.

---

## Resources

| Resource | Purpose |
|----------|---------|
| [`resources/SETUP.md`](resources/SETUP.md) | The 5-minute local path, the optional GCP and Confluent paths, troubleshooting |
| [`resources/CHEATSHEET.md`](resources/CHEATSHEET.md) | The merge table, merge key rules, source settings, the `gcloud` commands, the reconciliation query |
| [`resources/GLOSSARY.md`](resources/GLOSSARY.md) | Every CDC, Datastream and Kafka term, defined |
| [`resources/FAQ.md`](resources/FAQ.md) | The questions students actually ask |
| [`resources/sample_data.py`](resources/sample_data.py) | Deterministic sample data — 200 customers, 377 change events, 500 transactions |
| [`resources/audit_course.py`](resources/audit_course.py) | The course linter — see below |
| [`resources/test_course.py`](resources/test_course.py) | The course's structural test suite |
| [`resources/build_notebooks.py`](resources/build_notebooks.py) | Generates the notebooks from `resources/notebook_0*.py` — the source of truth |
| [`resources/run_notebooks.py`](resources/run_notebooks.py) | Executes every notebook headless, so the worked examples are known to run |

### SQL

| File | Purpose |
|------|---------|
| [`sql/create_customers.sql`](sql/create_customers.sql) | The BigQuery destination — `NOT NULL` merge key, `CLUSTER BY customer_id`, partitioned by `_PARTITIONTIME` |
| [`sql/create_transactions.sql`](sql/create_transactions.sql) | The Postgres transactions table — `transaction_id TEXT PRIMARY KEY` is the idempotency guarantee for the Kafka path |
| [`sql/reconciliation.sql`](sql/reconciliation.sql) | The nightly safety net — a three-way value comparison: `MISSING`, `EXTRA`, `VALUE_MISMATCH` |

---

## Getting Started

```bash
cd data-engineering/data-Course/google/Datastream

python3 -m venv .venv
source .venv/bin/activate
pip install -r project/requirements.txt

# Generate the deterministic dataset
python resources/sample_data.py --output-dir ./sample_data

# Run the CDC replay — no GCP account required
python project/cdc_pipeline.py \
    --input ./sample_data/changes.ndjson \
    --output ./out/customers \
    --merge-keys customer_id

# Run the tests
python3 -m pytest project/tests/ -q

# Lint the course
python resources/audit_course.py
```

---

## The Course Linter

The course ships with a static audit harness that catches the mistakes a reader would otherwise
only hit on a worker, hours into a job:

```bash
python resources/audit_course.py
```

It checks that:

- every notebook parses and has valid `nbformat` structure;
- every Python snippet in the chapters, notebooks and project parses;
- **every GCP SDK attribute access resolves against the installed library** — this catches a
  misspelled method (`client.access_secret` vs `client.access_secret_version`) automatically;
- every SQL file parses and no leftover unresolved markers or placeholders remain;
- every README/chapter/notebook relative link resolves;
- every Terraform file has balanced braces and brackets.

And a structural test suite that checks the course itself — including a test that the merge
semantics implemented in `project/cdc.py` are the ones the chapters teach:

```bash
python resources/test_course.py
```

And a headless runner that executes every notebook, so the worked examples are known to run:

```bash
python resources/run_notebooks.py
```

---

## Course Conventions

- **Chapters** are `NN-kebab-case.md`, numbered from 01, in eight sections: What you will learn,
  Concept, Hands-On, Common Errors and Fixes, Production Notes, Key Takeaways, Practice Exercises,
  Further Reading.
- **The merge table is the source of truth.** `project/cdc.py` → `CdcState.apply()` implements it
  exactly, and `resources/test_course.py` asserts that the two agree.
- **Placeholders** like `YOUR_PROJECT_ID` are expected in shell commands and must be replaced with
  your own values.
- **Every error message quoted in this course is real** — reproduced from a running pipeline.
- **`WHEN NOT MATCHED BY SOURCE THEN DELETE` never appears as something to write.** It belongs to a
  synchronised merge; in a streaming merge it empties the table every time the stream goes quiet.
  The linter's companion test enforces this.

---

## Interview Preparation

A bank of **56 module questions plus a top-50**, written the way a senior engineer answers them: a
direct answer, the mechanism, the trade-off, a production failure story, and numbers.

| File | Questions | Theme |
|------|-----------|-------|
| [`interview/01-foundations-and-cdc.md`](interview/01-foundations-and-cdc.md) | 14 | What CDC is, the log, the model, when not to use it |
| [`interview/02-the-merge-and-bigquery.md`](interview/02-the-merge-and-bigquery.md) | 14 | The merge, the merge key, schema, clustering, cost |
| [`interview/03-operations-and-recovery.md`](interview/03-operations-and-recovery.md) | 14 | Backfills, recovery, triage, reconciliation, ordering |
| [`interview/04-kafka-and-streaming.md`](interview/04-kafka-and-streaming.md) | 14 | At-least-once, consumer groups, the connector, the DLQ |
| [`interview/top-50.md`](interview/top-50.md) | 50 | The highest-yield subset — read this the night before |

See [`interview/README.md`](interview/README.md) for the study plan.

---

## Related Courses

- **[BigQuery for Big Data Engineers](../BigQuery/README.md)** — the warehouse course. Read it
  first if BigQuery is new to you; this course assumes you know what a partition is.
- **[Google Dataflow with Apache Beam](../Dataflow/README.md)** — the streaming course. Read this
  if Pub/Sub and windowing are new; this course assumes you know what a watermark is.

---

*Built to be run, not just read. Every command in this course has been executed, and every error
message has been reproduced.*
