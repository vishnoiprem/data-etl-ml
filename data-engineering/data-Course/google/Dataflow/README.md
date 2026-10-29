# Google Dataflow with Apache Beam — Master the Unified Batch & Streaming Model

A complete, hands-on guide to **Google Cloud Dataflow** and the **Apache Beam** programming model
for data engineers.

Every topic is taught from first principles — the programming model, the runner, windowing and
triggers, state, exactly-once semantics, templates, autoscaling and the cost model — and then
exercised for real through a **working project** that runs on the **Direct Runner with no GCP
account, no credentials and no bill**.

> **Duration:** 8 modules · 52 chapters · ~42 hours
> **Audience:** Data engineers, streaming engineers, and analytics engineers who design, build,
> operate or cost out Dataflow pipelines.

---

## What You Will Learn

- **The Beam model from the ground up** — `PCollection`, `PTransform`, `PRunner`, bundles, fusion,
  the shuffle, and why the runner is allowed to rearrange your graph.
- **Every core transform, with the mechanism explained** — `Map`, `FlatMap`, `Filter`, `Flatten`,
  `ParDo`, `CombinePerKey`, `GroupByKey`, `CoGroupByKey`, `Reshuffle`, side inputs, and the
  `CombineFn` accumulator contract.
- **I/O and coders** — text, CSV, JSON, Avro, Parquet, GCS, BigQuery, Pub/Sub; the coder hierarchy;
  and how to pick one deliberately instead of letting Beam guess.
- **GCP setup that actually works** — the project, the APIs, the bucket, and the **three distinct
  service identities** Dataflow needs (the one BigQuery never asks for).
- **Dataflow deployment** — flex templates, the `gcloud dataflow` CLI, staging and temp locations,
  the SDK-version pinning trap, and the job lifecycle.
- **Batch engineering** — design patterns, idempotency, exactly-once, error handling and DLQs,
  backfills, and re-runs.
- **Streaming** — event time, watermarks, allowed lateness, the four window types, the trigger
  catalogue, accumulation modes, and stateful `DoFn`s with timers.
- **Production operations** — testing, monitoring, autoscaling, skew and hot keys, the **vCPU-hour**
  cost model, CMEK, and a 3am troubleshooting runbook.
- **116 + 50 interview questions** with answers written the way a senior engineer answers them.

---

## Course Structure

### Module 1 — Beam Fundamentals & Model

| # | Chapter | Covers |
|---|---------|--------|
| 1.1 | [What Is Apache Beam?](chapters/01-what-is-apache-beam.md) | The three abstractions, immutability, laziness, why Beam exists |
| 1.2 | [Architecture & Portability](chapters/02-architecture-and-portability.md) | The Runner API, SDK harnesses, what portability really means |
| 1.3 | [Pipeline Flow & the Runner](chapters/03-pipeline-flow-and-the-runner.md) | Bundles, fusion, checkpointing, the Direct Runner family |
| 1.4 | [Batch vs Streaming & the Model](chapters/04-batch-vs-streaming-and-the-model.md) | Bounded vs unbounded, the watermark, the four guarantees |
| 1.5 | [Dataflow vs Dataproc](chapters/05-dataflow-vs-dataproc.md) | Managed runner vs managed cluster, and the third option |

### Module 2 — SDK & Core Transforms

| # | Chapter | Covers |
|---|---------|--------|
| 2.1 | [SDK Setup & Google Colab](chapters/06-sdk-setup-and-colab.md) | Installing Beam, version support, the Colab pitfalls |
| 2.2 | [Read Inputs](chapters/07-read-inputs.md) | Text, CSV, JSON, Avro, Parquet, Pub/Sub, BigQuery, Kafka |
| 2.3 | [Write Outputs](chapters/08-write-outputs.md) | `WriteToText` sharding, Avro, Parquet, BigQuery dispositions |
| 2.4 | [Map & FlatMap](chapters/09-map-and-flatmap.md) | 1→1 vs 1→N, tuples, side inputs, `Reshuffle` |
| 2.5 | [Filter & Flatten](chapters/10-filter-and-flatten.md) | `FilterInto`, merging sources, fusion interactions |
| 2.6 | [ParDo & DoFn](chapters/11-pardo-and-dofn.md) | The `DoFn` lifecycle, parameters, state, timers |
| 2.7 | [CombinePerKey & combiners.Count.PerKey](chapters/12-combineperkey-and-combiners.md) | The accumulator contract, associativity, the built-in combiners |
| 2.8 | [CoGroupByKey & GroupByKey](chapters/13-cogroupbykey-and-groupbykey.md) | Keyed joins without a round-trip, and when GBK is right |

### Module 3 — I/O & Multi-Source Pipelines

| # | Chapter | Covers |
|---|---------|--------|
| 3.1 | [I/O Catalogue & Coders](chapters/14-io-catalogue-and-coders.md) | The full catalogue, the coder hierarchy, type-hint inference |
| 3.2 | [Multi-Source & Multi-Sink](chapters/15-multi-source-and-multi-sink.md) | `Flatten`, the tag pattern, read-once fan-out, fusion barriers |
| 3.3 | [Text/Avro/JSON/Parquet](chapters/16-text-avro-json-parquet.md) | Format trade-offs, compression, schema evolution |
| 3.4 | [GCS & BigQuery I/O](chapters/17-gcs-and-bigquery-io.md) | `gs://` paths, shard explosion, BigQuery dispositions, the sharding myth |
| 3.5 | [Cloud Workbench & Beam Basics](chapters/18-cloud-workbench-and-beam-basics.md) | Explore first, then engineer; the pure reference implementation |

### Module 4 — GCP Setup & Local Execution

| # | Chapter | Covers |
|---|---------|--------|
| 4.1 | [GCP Project, Billing & APIs](chapters/19-gcp-project-billing-and-apis.md) | The APIs you actually need, budget alerts, region alignment |
| 4.2 | [Service Accounts & Bucket](chapters/20-service-accounts-and-bucket.md) | **Three identities**, least privilege, the role-caching gotcha |
| 4.3 | [Direct Runner](chapters/21-direct-runner.md) | The runner family, Prism's limitations, measuring both |
| 4.4 | [Saving to GCS](chapters/22-saving-to-gcs.md) | `gs://` paths, the shard-explosion trap, lifecycle rules |
| 4.5 | [PipelineOptions Deep Dive](chapters/23-pipelineoptions-deep-dive.md) | The subclass hierarchy, `view_as`, custom option classes |

### Module 5 — Dataflow Templates & Deployment

| # | Chapter | Covers |
|---|---------|--------|
| 5.1 | [Dataflow Service Architecture](chapters/24-dataflow-service-architecture.md) | The job lifecycle, stages, workers, the zombie job |
| 5.2 | [Creating a Flex Template](chapters/25-creating-a-flex-template.md) | Build vs run, parameters, the SDK-version pinning trap |
| 5.3 | [Executing a Batch Job](chapters/26-executing-a-batch-job.md) | Every required flag, autoscaling, the metrics worth watching |
| 5.4 | [Template → BigQuery](chapters/27-template-to-bigquery.md) | Dispositions, partitioning, idempotent writes |
| 5.5 | [Executing Batch → BigQuery](chapters/28-executing-batch-to-bigquery.md) | The end-to-end runbook, and when BigQuery SQL is the better answer |
| 5.6 | [gcloud Dataflow CLI](chapters/29-gcloud-dataflow-cli.md) | A complete command reference with jq recipes |

### Module 6 — Batch Pipeline Engineering

| # | Chapter | Covers |
|---|---------|--------|
| 6.1 | [Batch Design Patterns](chapters/30-batch-design-patterns.md) | Filter-early, aggregate-early, partition-early, side input vs shuffle |
| 6.2 | [Schema, Coders & Encoders](chapters/31-schema-coders-and-encoders.md) | Coder selection, `RowCoder`, the `infer_schema` trap |
| 6.3 | [Idempotency & Exactly-Once](chapters/32-idempotency-and-exactly-once.md) | What Beam guarantees, idempotent sinks, deterministic pipelines |
| 6.4 | [Error Handling & DLQ](chapters/33-error-handling-and-dlq.md) | Tagged outputs, poison pills, the failure-mode table |
| 6.5 | [Backfills & Re-runs](chapters/34-backfills-and-re-runs.md) | Backfill vs re-run vs reprocess, the safety checklist |
| 6.6 | [Case Study 1 — Template Method](chapters/35-case-study-template-method.md) | A full worked batch pipeline, from requirements to deployment |
| 6.7 | [Multi-Source Batch Joins & Enrichment](chapters/36-multi-source-batch-joins.md) | Side input vs. `CoGroupByKey` vs. BigQuery, the duplicate-read trap, full-refresh vs. incremental joins |

### Module 7 — Streaming Pipelines

| # | Chapter | Covers |
|---|---------|--------|
| 7.1 | [Pub/Sub Architecture & I/O](chapters/37-pubsub-architecture-and-io.md) | At-least-once, the subscription trap, `id_label` dedup |
| 7.2 | [Unbounded Collections & Event Time](chapters/38-unbounded-collections-and-event-time.md) | Re-stamping, the three clocks, backfill-in-streaming |
| 7.3 | [Windowing](chapters/39-windowing.md) | Fixed, sliding, session, global; the zoom-lens pattern |
| 7.4 | [Triggers & Accumulation Modes](chapters/40-triggers-and-accumulation-modes.md) | The full trigger catalogue, `2/4/5` vs `2/2/1` |
| 7.5 | [Watermarks & Allowed Lateness](chapters/41-watermarks-and-allowed-lateness.md) | The watermark precisely, the `MAY_FINISH` error, the stall |
| 7.6 | [State, Timers & Processing-Time Triggers](chapters/42-state-timers-and-processing-time-triggers.md) | Why a plain attribute is **not** durable state |
| 7.7 | [Case Study 3 — Streaming with Pub/Sub](chapters/43-case-study-streaming-with-pubsub.md) | The full streaming pipeline, three input modes, its limits |

### Module 8 — Production Operations

| # | Chapter | Covers |
|---|---------|--------|
| 8.1 | [Testing Beam Pipelines](chapters/44-testing-beam-pipelines.md) | The pyramid, `TestPipeline`, `use_global_window=False` |
| 8.2 | [Monitoring & Autoscaling](chapters/45-monitoring-and-autoscaling.md) | Custom metrics, `Basic` vs `Aggressive`, what to alert on |
| 8.3 | [Skew, Hot Keys & Reshuffle](chapters/46-skew-hot-keys-and-reshuffle.md) | Detecting skew, and why `Reshuffle` is not the fix |
| 8.4 | [Cost Model & Optimization](chapters/47-cost-model-and-optimization.md) | vCPU-hour, the optimisation levers, the $432 weekend |
| 8.5 | [Security, IAM & CMEK](chapters/48-security-iam-and-cmek.md) | Least privilege, VPC-native jobs, CMEK, secrets |
| 8.6 | [Template vs Custom Code](chapters/49-template-vs-custom-code.md) | The decision matrix, and the honest recommendation |
| 8.7 | [Case Study 2 — Custom Batch](chapters/50-case-study-custom-batch.md) | A multi-source batch pipeline with a side input |
| 8.8 | [Beam SQL & DataFrames API](chapters/51-beam-sql-and-dataframes-api.md) | When it helps, when it hurts, and the honest verdict |
| 8.9 | [Troubleshooting & Common Failure Modes](chapters/52-troubleshooting-and-common-failure-modes.md) | The triage method, the error→cause table, the 3am runbook |

---

## Hands-On Notebooks

Ten notebooks, each of which **executes top-to-bottom on the Direct Runner with no GCP account**.
Every GCP cell is gated behind an environment check, so the notebooks run identically on a laptop
and in Colab.

| # | Notebook | Module | What you build |
|---|----------|--------|----------------|
| 01 | [Setup & Authentication](notebooks/01-setup-and-authentication.ipynb) | 2.1 | Verify the install, read the job graph, catch a real error |
| 02 | [The Beam Model & Core Transforms](notebooks/02-beam-model-and-transforms.ipynb) | 2.2–2.4 | A real aggregation; a combiner's merge-order independence |
| 03 | [I/O & File Formats](notebooks/03-io-and-file-formats.ipynb) | 3.1–3.3 | Read and write every format; measure the size difference |
| 04 | [The Batch Pipeline](notebooks/04-batch-pipeline.ipynb) | 6.1–6.6 | The pipeline step by step; a DLQ; a backfill |
| 05 | [Streaming: Windowing & Triggers](notebooks/05-streaming-windowing-and-triggers.ipynb) | 7.1–7.4 | Event-time windows; `ACCUMULATING` vs `DISCARDING` |
| 06 | [Testing Beam Pipelines](notebooks/06-testing-beam-pipelines.ipynb) | 8.1 | The pyramid; the `WindowedValue` matcher; `TestStream` |
| 07 | [Templates & Deployment](notebooks/07-dataflow-templates-and-deployment.ipynb) | 5.1–5.6 | The job lifecycle; the flex-template workflow |
| 08 | [Monitoring & Cost](notebooks/08-monitoring-and-cost.ipynb) | 8.2–8.4 | Custom metrics; a worked cost worksheet |
| 09 | [Patterns & Case Studies](notebooks/09-patterns-and-case-studies.ipynb) | 5–8 | Hot keys, DLQs, backfills; the three case studies |
| 10 | [End-to-End Project](notebooks/10-end-to-end-project.ipynb) | All | The full project, run and cross-validated |

---

## The Project

A working Apache Beam project that runs **locally with no GCP account, no credentials, and no
bill**. The same code deploys to Dataflow by changing two things: the `--runner` flag and the
path prefix.

```
project/
├── transforms.py           # Pure logic + Beam DoFn/CombineFn — one file, two halves
├── beam_options.py         # Runner and option resolution, .env loading
├── batch_pipeline.py       # Orders → validate → convert currency → revenue per region
├── streaming_pipeline.py   # Events → fixed windows → counts and totals per region
├── templates/              # Dataflow flex templates for both pipelines
└── tests/                  # 51 pure tests (no Beam needed) + integration tests
```

The design decision that makes it work: `transforms.py` splits into a **pure half** (standard
library only) and a **Beam half** (`ParseOrderFn`, `RevenueByRegionFn`). That is why
`tests/test_transforms.py` runs in 0.05 seconds with **apache-beam not installed** — and why the
Beam result can be cross-validated against a pure reference implementation.

```bash
python resources/sample_data.py --output-dir ./sample_data

python project/batch_pipeline.py --input ./sample_data/orders.csv --output ./out/summary
# region,order_count,revenue_eur
# AMER,318,113592.19
# APAC,285,108194.92
# EMEA,322,118423.22
# LATAM,320,110646.18

python project/streaming_pipeline.py --input ./sample_data/events.ndjson \
    --output ./out/streaming --window-seconds 3600
# region,event_count,total_value
# APAC,207,13203.97
# AMER,201,12389.69
# ... one row per (event-time window, region) — 96 rows for a 24-hour dataset
```

The streaming pipeline stamps every element with its **event-time** timestamp before
windowing. Skip that step and the pipeline still produces the right *totals* — which is
exactly why the bug is so easy to miss — but every event collapses into a single window.
See `project/tests/test_pipelines.py::TestStreamingPipeline` for the regression test.

See [`project/README.md`](project/README.md) for the full walkthrough and the deploy path.

---

## Resources

| Resource | Purpose |
|----------|---------|
| [`resources/SETUP.md`](resources/SETUP.md) | The 5-minute local path, the optional GCP path, troubleshooting |
| [`resources/CHEATSHEET.md`](resources/CHEATSHEET.md) | Transforms ↔ SQL, options flags, `gcloud`, windows and triggers |
| [`resources/GLOSSARY.md`](resources/GLOSSARY.md) | Every Beam and Dataflow term, defined |
| [`resources/FAQ.md`](resources/FAQ.md) | The questions students actually ask |
| [`resources/sample_data.py`](resources/sample_data.py) | Deterministic sample data, with `--hot-key-rate` and `--late-events` |
| [`resources/beam_client.py`](resources/beam_client.py) | Environment discovery and job submission helpers |
| [`resources/audit_course.py`](resources/audit_course.py) | The course linter — see below |
| [`resources/test_course.py`](resources/test_course.py) | The course's structural test suite |

---

## Getting Started

```bash
cd data-engineering/data-Course/google/Dataflow

python3 -m venv .venv
source .venv/bin/activate
pip install -r project/requirements.txt

# Generate the deterministic dataset
python resources/sample_data.py --output-dir ./sample_data

# Run the batch pipeline — no GCP account required
python project/batch_pipeline.py --input ./sample_data/orders.csv --output ./out/summary

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
- **every `beam.<attr>` access resolves against the installed SDK** — this catches a misspelled
  transform (`beam.CombinePerKey` vs `beam.combiners.Count.PerKey`) automatically;
- every pipeline in the project has **unique transform labels** — Beam's own error message does not
  tell you which labels collided;
- no leftover unresolved markers, placeholders or unbalanced f-strings;
- every README/chapter/notebook relative link resolves.

And a structural test suite that checks the course itself:

```bash
python resources/test_course.py
```

---

## Course Conventions

- **Chapters** are `NN-kebab-case.md`, numbered from 01, in eight sections: What you will learn,
  Concept, Hands-On, Common Errors and Fixes, Production Notes, Key Takeaways, Practice Exercises,
  Further Reading.
- **Pipeline DAG fragments** use ` ```text ` fences, so the linter does not try to parse a
  fragment as Python.
- **The runner default is `BundleBasedDirectRunner`** — the classic pure-Python runner. Beam 2.60+
  ships a faster Go-based runner called `DirectRunner` (the "Prism" runner), but it does not yet
  support every trigger and panics on `AfterWatermark`. See
  [chapter 4.3](chapters/21-direct-runner.md).
- **Placeholders** like `YOUR_PROJECT_ID` are expected in shell commands and must be replaced with
  your own values.
- **Every error message quoted in this course is real**, copied from Beam 2.77.

---

## Interview Preparation

A bank of **116 module questions plus a top-50**, written the way a senior engineer answers them:
a direct answer, the mechanism, the trade-off, a production failure story, and numbers.

| File | Questions | Theme |
|------|-----------|-------|
| [`interview/01-beam-fundamentals.md`](interview/01-beam-fundamentals.md) | 14 | The model, execution, portability |
| [`interview/02-core-transforms.md`](interview/02-core-transforms.md) | 16 | Transform mechanics and combiners |
| [`interview/03-io-and-coders.md`](interview/03-io-and-coders.md) | 14 | Sources, sinks, coders, formats |
| [`interview/04-gcp-setup-and-runners.md`](interview/04-gcp-setup-and-runners.md) | 12 | IAM, runners, options |
| [`interview/05-templates-and-deployment.md`](interview/05-templates-and-deployment.md) | 14 | Flex templates and job operations |
| [`interview/06-batch-engineering.md`](interview/06-batch-engineering.md) | 14 | Idempotency, DLQs, backfills |
| [`interview/07-streaming.md`](interview/07-streaming.md) | 16 | Event time, windows, state, Pub/Sub |
| [`interview/08-production-ops.md`](interview/08-production-ops.md) | 16 | Testing, monitoring, cost, security |
| [`interview/top-50.md`](interview/top-50.md) | 50 | The highest-yield subset — read this the night before |

See [`interview/README.md`](interview/README.md) for the study plan.

---

## Related Courses

- **[BigQuery for Big Data Engineers](../../../../learning/data-engineering/data-Course/google/BigQuery/README.md)** — the warehouse course. Read it
  first if BigQuery is new to you; this course assumes you know what a partition is.
- **[Apache Airflow](https://airflow.apache.org/)** — for orchestrating *when* your Dataflow jobs
  run, which is a different problem from *how* the pipeline computes.

---

*Built to be run, not just read. Every command in this course has been executed, and every error
message has been reproduced.*
