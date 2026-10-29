# Google Cloud Composer with Apache Airflow — Master Orchestration Without a Local Install

A complete, hands-on guide to **Google Cloud Composer** and the **Apache Airflow**
programming model for data engineers.

Every topic is taught from first principles — the DAG model, the scheduler, the
metadata database, executors, templating, XCom, branching, SLAs and reliability — and
then exercised for real through a **working project that runs on a plain Python
install, with no Airflow, no credentials and no bill**.

> **Duration:** 3 modules · 16 chapters · ~9 hours
> **Audience:** Data engineers, analytics engineers, and platform engineers who design,
> build or operate orchestration.

---

## The Premise — and Why It Matters

Most Airflow courses start with `pip install apache-airflow`. That install is heavy,
version-sensitive, and it puts a version of Airflow on your laptop that is almost
certainly *not* the version Composer runs. You then learn against a system that does
not match the one you will actually use.

This course takes the opposite approach:

> **Learn Airflow through Composer, and verify everything locally without Airflow.**

The trick is a deliberate separation:

| Layer | Lives in | Imports Airflow? |
|---|---|---|
| **Business logic** | `project/core/` | **No** — standard library only |
| **Orchestration** | `project/dags/` | Yes — the real, deployable DAGs |
| **Local execution** | `project/local_runner.py` | No — a mini Airflow |

Because the logic is pure, `pytest` runs in **0.35 seconds** with Airflow absent, and
you can cross-validate the result against a reference implementation. The DAG files in
`project/dags/` are the artefact you actually deploy to Composer — the local runner
does not reimplement them, it exercises the *same* core functions.

```bash
python project/local_runner.py --dag etl_to_gcs
# region,order_count,revenue_eur
# AMER,318,113592.19
# APAC,285,108194.92
# EMEA,322,118423.22
# LATAM,320,110646.18
```

---

## What You Will Learn

- **Why orchestration exists** — and the difference between a pipeline that computes
  and a pipeline that *coordinates*.
- **Airflow's architecture** — the scheduler, the DAG processor, the metadata
  database, the executors, and the task lifecycle that follows from them.
- **DAGs and scheduling** — `start_date`, `schedule`, `catchup`, `max_active_runs`,
  and the **half-open data interval** convention that quietly breaks daily pipelines.
- **Every core concept** — operators, tasks, Jinja templating, Variables, params,
  Connections, XCom, branching, trigger rules, sensors, dynamic task mapping.
- **Reliability** — SLAs versus timeouts versus retries, idempotency, backfill safety,
  and the `WRITE_TRUNCATE` versus `WRITE_APPEND` decision that decides whether a
  retry double-counts your revenue.
- **Production operations** — testing DAG structure without a scheduler, monitoring,
  cost control, and the "forgot to delete the environment" failure story.
- **Composer specifically** — provisioning, environment sizing and cost, the UI, IAM,
  and how to clean up so you do not pay for a forgotten environment.
- **120 interview questions** with answers written the way a senior engineer answers them.

---

## Course Structure

### Module 1 — Airflow Fundamentals & Orchestration

| # | Chapter | Covers |
|---|---------|--------|
| 1.1 | [What Is Orchestration & Why Airflow?](chapters/01-what-is-orchestration-and-why-airflow.md) | The problem, the DAG model, task vs workflow, Airflow vs Spark vs Beam |
| 1.2 | [Airflow Architecture & Concepts](chapters/02-airflow-architecture-and-concepts.md) | Scheduler, DAG processor, metadata DB, executors, task lifecycle |
| 1.3 | [DAGs & Scheduling](chapters/03-dags-and-scheduling.md) | `schedule`, `catchup`, logical date, the half-open data interval |
| 1.4 | [Tasks & Operators](chapters/04-tasks-and-operators.md) | Operators vs sensors, the common operators, choosing one, TaskFlow |
| 1.5 | [Templates & Jinja](chapters/05-templates-and-jinja.md) | The context, `template_fields`, why undefined variables fail loudly |
| 1.6 | [Variables, Params & Connections](chapters/06-variables-params-and-connections.md) | The layering rule, and why secrets go in Connections |
| 1.7 | [XCom](chapters/07-xcom.md) | The metadata-DB storage model, the 48 KB limit, control data vs bulk data |
| 1.8 | [Branching & Dynamic Tasks](chapters/08-branching-and-dynamic-tasks.md) | `BranchOperator`, trigger rules, the join point, dynamic task mapping |

### Module 2 — Production Orchestration

| # | Chapter | Covers |
|---|---------|--------|
| 2.1 | [Sensors & Deferrable Operators](chapters/09-sensors-and-deferrable-operators.md) | Poke vs reschedule, timeouts, the triggerer, why sensors are expensive |
| 2.2 | [Executors & Workers](chapters/10-executors-and-workers.md) | Local, Celery, Kubernetes; what an executor actually does |
| 2.3 | [SLAs & SLOs](chapters/11-slice-and-slas.md) | SLA vs timeout vs retry, `sla_miss_callback`, what a miss means |
| 2.4 | [Idempotency & Reliability](chapters/12-idempotency-and-reliability.md) | Re-runnable DAGs, the double-count failure story, backfill safety |
| 2.5 | [Testing DAGs](chapters/13-testing-dags.md) | Testing structure without a scheduler, the pure-logic split, CI |
| 2.6 | [Orchestration Patterns](chapters/14-orchestration-patterns.md) | Fan-out/fan-in, dynamic mapping, cross-DAG dependencies, Datasets |
| 2.7 | [Airflow vs Beam vs Spark](chapters/15-airflow-vs-beam-vs-spark.md) | Orchestration vs processing, and when you need both |
| 2.8 | [Airflow on Kubernetes](chapters/16-airflow-on-kubernetes.md) | The pod-per-task model, RBAC, and the pod-startup cost |

### Module 3 — Cloud Composer on GCP

> The Composer-specific material is distributed through the course rather than
> isolated in one block — provisioning is taught where it matters, alongside the
> Airflow concept it serves. Notebook 09 is the consolidated, hands-on tour.

| Resource | Covers |
|---|---|
| [Notebook 09 — Composer on GCP](notebooks/09-composer-on-gcp.ipynb) | Architecture, `gcloud` provisioning, environment sizing and cost, the UI, IAM, cleanup |
| [Notebook 10 — End-to-End Project](notebooks/10-end-to-end-project.ipynb) | The full project, cross-validated, plus the deployment checklist |
| [Interview 05 — Composer & GCP](interview/05-composer-and-gcp.md) | The 12 Composer-specific questions |

---

## Hands-On Notebooks

Ten notebooks, each of which **executes top-to-bottom with no Airflow and no GCP
account**. Every cloud command is clearly marked as one to run in a terminal.

| # | Notebook | Module | What you build |
|---|----------|--------|----------------|
| 01 | [Setup & Environment](notebooks/01-setup-and-environment.ipynb) | 1.1–1.2 | Verify the environment; build the mental model; find the sample data |
| 02 | [DAG Anatomy & Scheduling](notebooks/02-dag-anatomy-and-scheduling.ipynb) | 1.3 | Build DAGs; the data interval; a schedule simulator |
| 03 | [Templates & Variables](notebooks/03-templates-and-variables.ipynb) | 1.5–1.6 | Render every context variable; the undefined-variable failure |
| 04 | [XCom & Branching](notebooks/04-xcom-and-branching.ipynb) | 1.7–1.8 | Push and pull XCom; measure the 48 KB limit; the join point |
| 05 | [Sensors & SLAs](notebooks/05-sensors-and-slAs.ipynb) | 2.1–2.3 | Sensor semantics; SLA vs timeout vs retry; a SLA tracker |
| 06 | [Reliability & Idempotency](notebooks/06-reliability-and-idempotency.ipynb) | 2.4 | Retries; `WRITE_TRUNCATE` vs `WRITE_APPEND`; the double-count demo |
| 07 | [Testing DAGs](notebooks/07-testing-dags.ipynb) | 2.5 | Test DAG structure; test pure logic; a CI checklist |
| 08 | [Patterns & Case Studies](notebooks/08-patterns-and-case-studies.ipynb) | 2.6 | Fan-out/fan-in; dynamic mapping; cross-DAG dependencies; three case studies |
| 09 | [Composer on GCP](notebooks/09-composer-on-gcp.ipynb) | 3 | Provisioning; sizing and cost; the UI; IAM; cleanup |
| 10 | [End-to-End Project](notebooks/10-end-to-end-project.ipynb) | All | The full project, run and cross-validated |

**Verify every notebook yourself:**

```bash
python resources/check_notebooks.py
# All 10 notebooks passed.
```

That script parses each notebook, validates its structure, and **executes every code
cell in order** — so a notebook that would fail on a student's laptop fails here
first.

---

## The Project

A working Airflow project whose logic runs **locally with no Airflow, no credentials
and no bill**. The same DAG files deploy to Composer by changing nothing but the
environment configuration.

```
project/
├── dags/                      # Real Airflow DAGs — deploy these to Composer
│   ├── 01_hello_world.py
│   ├── 02_templating_and_variables.py
│   ├── 03_etl_bigquery.py
│   ├── 04_branching_and_xcom.py
│   └── dag_config.py          # Shared, Variable-overridable configuration
├── core/                      # PURE logic — no Airflow import anywhere
│   ├── pipeline_logic.py      # Validation, currency, aggregation, intervals
│   ├── templating.py          # Airflow-style Jinja rendering
│   ├── fanout.py              # Fan-out / fan-in helpers
│   ├── sla_logic.py           # SLA vs timeout vs retry
│   ├── sla_tracker.py         # SLA miss tracking
│   ├── sensor_conditions.py   # Sensor predicates
│   ├── idempotent_load.py     # Idempotent write patterns
│   └── dedup_load.py          # Deduplication patterns
├── local_runner.py            # A mini Airflow — DAGs, XCom, branches, retries
├── tests/                     # 130 tests, all passing with Airflow ABSENT
└── requirements.txt
```

The design decision that makes it work: `core/` imports **nothing** from Airflow.
That is why `tests/` runs in 0.35 seconds with `apache-airflow` not installed — and
why the local runner's output can be cross-validated against a pure reference
implementation.

```bash
# Generate the deterministic dataset
python resources/sample_data.py --output-dir ./sample_data

# Run a pipeline — no Airflow, no GCP, no bill
python project/local_runner.py --dag etl_to_gcs
python project/local_runner.py --dag branching_load
python project/local_runner.py --dag xcom_pipeline
python project/local_runner.py --dag templating_paths
python project/local_runner.py --dag all

# Run the tests — Airflow not required
python -m pytest project/tests/ -q
# 130 passed, 10 skipped in 0.35s
```

The local runner implements the subset of Airflow's semantics that changes
*observable behaviour* in a pipeline:

| Feature | Behaviour |
|---|---|
| Dependency ordering | Topological, not insertion order |
| Failure propagation | `failed` → `upstream_failed`, a state distinct from `skipped` |
| Trigger rules | `all_success`, `none_failed`, `all_done`, `always` |
| Branching | Downstream tasks not named are skipped; join points survive |
| Retries | With delay, then a terminal `failed` |
| XCom | Push/pull, named keys, the automatic `return_value` push |

---

## Resources

| Resource | Purpose |
|----------|---------|
| [`resources/SETUP.md`](resources/SETUP.md) | The 5-minute local path, the optional GCP path, troubleshooting |
| [`resources/CHEATSHEET.md`](resources/CHEATSHEET.md) | Templates, operators, trigger rules, `gcloud`, the CLI |
| [`resources/GLOSSARY.md`](resources/GLOSSARY.md) | Every Airflow and Composer term, defined |
| [`resources/FAQ.md`](resources/FAQ.md) | The questions students actually ask |
| [`resources/sample_data.py`](resources/sample_data.py) | Deterministic sample data, with `--hot-key-rate` and `--malformed` |
| [`resources/check_notebooks.py`](resources/check_notebooks.py) | Validates and **executes** every notebook |

---

## Getting Started

```bash
cd data-engineering/data-Course/google/composer

# Use the project venv (it already has jinja2, pandas, matplotlib, pytest)
source ../../../../.env/bin/activate

# Generate the deterministic dataset
python resources/sample_data.py --output-dir ./sample_data

# Run a pipeline — no Airflow required
python project/local_runner.py --dag etl_to_gcs

# Run the tests
python -m pytest project/tests/ -q

# Verify every notebook
python resources/check_notebooks.py
```

---

## Course Conventions

- **Chapters** are `NN-kebab-case.md`, numbered from 01, in eight sections: What you
  will learn, Concept, Hands-On, Common Errors and Fixes, Production Notes, Key
  Takeaways, Practice Exercises, Further Reading.
- **DAG diagrams** use ` ```text ` fences, so they are never parsed as Python.
- **Airflow 2.x is the baseline.** `schedule` (not the deprecated
  `schedule_interval`), dynamic task mapping (2.3+), Datasets (2.4+), deferrable
  operators (2.2+), TaskFlow (2.0+), `logical_date` (2.2+).
- **Composer 2** is the baseline environment (Celery executor). Composer 3 uses the
  Kubernetes executor; the differences are called out where they matter.
- **Placeholders** like `YOUR_PROJECT_ID` are expected in shell commands and must be
  replaced with your own values.
- **Every error message quoted in this course is real**, copied from Airflow 2.x.

---

## Interview Preparation

A bank of **70 module questions plus a top-50**, written the way a senior engineer
answers them: a direct answer, the mechanism, the trade-off, a production failure
story, and numbers.

| File | Questions | Theme |
|------|-----------|-------|
| [`interview/01-orchestration-fundamentals.md`](interview/01-orchestration-fundamentals.md) | 14 | The model, the architecture, the scheduler, executors |
| [`interview/02-dags-scheduling-and-templates.md`](interview/02-dags-scheduling-and-templates.md) | 14 | DAGs, schedules, the data interval, templating, config |
| [`interview/03-tasks-xcom-and-branching.md`](interview/03-tasks-xcom-and-branching.md) | 14 | Operators, XCom, trigger rules, branching, sensors |
| [`interview/04-reliability-and-production.md`](interview/04-reliability-and-production.md) | 16 | SLAs, retries, idempotency, testing, cost, security |
| [`interview/05-composer-and-gcp.md`](interview/05-composer-and-gcp.md) | 12 | Provisioning, sizing, versions, IAM, cleanup |
| [`interview/top-50.md`](interview/top-50.md) | 50 | The highest-yield subset — read this the night before |

See [`interview/README.md`](interview/README.md) for the study plan.

---

## Related Courses

- **[Google Dataflow](../Dataflow/README.md)** — the *processing* course. Read it if
  you want to know what runs *inside* the tasks this course orchestrates.
- **[BigQuery for Big Data Engineers](../../../../learning/data-engineering/data-Course/google/BigQuery/README.md)** — the warehouse
  course. This course assumes you know what a partition is.

---

*Built to be run, not just read. Every command has been executed, every notebook has
been executed cell-by-cell, and every error message has been reproduced.*
