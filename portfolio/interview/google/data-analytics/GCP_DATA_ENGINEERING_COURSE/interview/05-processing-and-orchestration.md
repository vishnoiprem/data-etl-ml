# Processing and Orchestration — Interview Questions

## 🎯 How to use this file

Sixteen questions covering Modules 5 and 6: Hadoop and the big-data ecosystem, Spark on Dataproc, Beam on Dataflow, Airflow on Composer, Workflows, Dataform, Cloud Data Fusion and Cloud Dataprep. The pattern across these tools is consistent — **every one of them is a trade between flexibility and operational burden** — so the interviewer is usually listening for whether you can state which burden you are accepting and why.

## Questions

### Q1. What is Hadoop, and what problem does the modern GCP stack still inherit from it?

**Answer.** Hadoop is the original big-data ecosystem: HDFS for distributed storage, YARN for resource management, MapReduce for batch processing. Its ideas are still everywhere — HDFS became Cloud Storage's design ancestor, YARN became the Dataproc and Dataflow job model, and MapReduce became the batch step functions.

**Mechanism.** The core insight was that you scale by adding commodity machines and moving the computation to the data, not the data to the computation. HDFS is a block store with a NameNode and DataNodes; YARN separates resource scheduling from the execution framework so that MapReduce, Spark and Flink can share a cluster.

**Trade-off.** Hadoop's operational model was heavy: a cluster is a fleet of machines you patch, rebalance and keep healthy. Every modern managed service on GCP exists to remove that burden.

**In practice.** I do not run Hadoop on GCP. Dataproc still offers Hadoop and Hive, but for a new batch workload I use Dataproc Serverless (ephemeral clusters) or Dataflow batch, which give the same MapReduce-style programming model with none of the cluster administration. If I have to explain MapReduce in an interview, I explain it as the mental model behind "map, shuffle, reduce" — the shuffle is the expensive part, and every optimisation since has targeted it.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from service_catalog import SERVICES

service = SERVICES["dataproc"]
print(f"{service.name}: {service.summary}")
print("resources:", service.key_resources)
print("pricing:", service.pricing_model)
```

---

### Q2. Explain the MapReduce shuffle, and why it is the expensive part.

**Answer.** The shuffle is the phase where each mapper's intermediate key-value pairs are partitioned by key and shipped across the network to the reducers, where they are sorted and merged.

**Mechanism.** Between map and reduce sits the shuffle: partition, spill to local disk, merge, and network transfer to the partition of the reducer. The network transfer and the disk I/O are why the shuffle dominates a map-reduce job — the compute is often a small fraction of the elapsed time.

**Trade-off.** Moving data is slower than moving compute, but keeping data local is not free either: local disks are limited, and replicating data to avoid the shuffle costs more than the shuffle.

**In practice.** The question behind every performance investigation: *can this shuffle be avoided?* A map-side join against a small dimension table kept in memory eliminates the reduce-side shuffle entirely. A pre-aggregated input eliminates it too. This is the same reasoning as BigQuery's broadcast hash join, and it is why "reduce shuffle" is the number I look for in a slow job's stage breakdown.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import bucket_by_window, aggregate_by_window, ingest_events

lines = open("sample_data/events.csv").read().splitlines()
accepted, _ = ingest_events(lines)

# The "shuffle" in pure Python: group by key, then aggregate each group.
buckets = bucket_by_window(accepted)
print("distinct shuffle keys (windows):", len(buckets))
print("output rows after aggregation:", len(aggregate_by_window(accepted)))
```

---

### Q3. When would you use Spark on Dataproc, and when would you use Dataflow batch?

**Answer.** Use Dataproc with Spark when the existing codebase is Spark, or when the job genuinely needs Spark-specific features — MLlib, GraphX, Spark SQL over many tables, a custom shuffle tuning. Use Dataflow batch when you want one pipeline to run as batch today and streaming tomorrow, or when you want managed autoscaling and no cluster administration.

**Mechanism.** Dataproc gives you a Spark cluster — either a long-lived one with a specific version, or **Serverless** batches that spin up a cluster for the job and tear it down. Dataflow is a runner for Apache Beam, so the same code can execute in batch mode or streaming mode, and it autoscales workers based on the work in flight.

**Trade-off.** Dataproc is cheaper per vCPU-hour ($0.0476) than Dataflow ($0.0595), and you can keep a warm cluster. But a warm cluster is a warm bill, and Dataproc's autoscaling and version management are yours to operate. Dataflow's autoscales to zero between jobs and gives you a unified model, at a higher per-vCPU price.

**In practice.** New work with no legacy constraint goes to Dataflow, because the batch/streaming symmetry pays for the higher unit price within a few months. Existing Spark goes to Dataproc Serverless — you keep the Spark code, and you stop paying for an idle cluster. The migration to Beam is a project, not a weekend, and it is worth scoping honestly.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from cost_model import DATAFLOW_PER_VCPU_HOUR, DATAPROC_PER_VCPU_HOUR, estimate

hours = 24 * 4
print("Dataproc:", estimate("dataproc", vcpu_hours=hours, apply_free_tier=False).total)
print("Dataflow:", estimate("dataflow", vcpu_hours=hours, apply_free_tier=False).total)
print(f"Dataflow is {DATAFLOW_PER_VCPU_HOUR / DATAPROC_PER_VCPU_HOUR:.2f}x Dataproc per vCPU-hour")
```

---

### Q4. What is Apache Beam, and why would you write a pipeline in it?

**Answer.** Beam is a unified programming model for batch and streaming data processing. You write one pipeline, and the same code runs on Dataflow, Flink, Spark, or a local runner.

**Mechanism.** The core abstractions are `PCollection` (a dataset), `DoFn` (a per-element transform), `GroupByKey` (a grouping), and a `Pipeline` that wires them together. The runner executes the DAG, and Dataflow's runner translates it into Cloud Dataflow jobs. Beam's model is deliberately *agnostic* — you pick the runner, and the semantics (windowing, grouping, triggering) are defined by the model rather than the runner.

**Trade-off.** Portability is the payoff, and abstraction cost is the price. Some highly engine-specific optimisations are unavailable, and debugging a Beam pipeline means understanding both the model and the runner. A hand-written Spark job will always be able to do something Beam cannot express.

**In practice.** I choose Beam when I want the option to change execution mode later, or when the team already knows it. For a pipeline that is unambiguously batch forever and has a heavy Spark dependency, Spark is the better answer. Beam's real strength shows up in the streaming migration: the course's `bucket_by_window` and `aggregate_by_window` are exactly Beam's fixed-window and grouped-aggregation semantics expressed in pure Python.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from service_catalog import SERVICES

service = SERVICES["dataflow"]
print(f"{service.name}: {service.summary}")
print("pricing:", service.pricing_model)
print("resources:", service.key_resources)
```

---

### Q5. What is a watermark in Beam, and what happens to late data?

**Answer.** A watermark is the pipeline's declaration that it will not receive any more events with a timestamp at or before it. Events that arrive after the watermark is past their timestamp are **late data**.

**Mechanism.** In Beam, a `GroupByKey` in streaming mode fires when the watermark passes the end of the window. Data that arrives afterwards goes to a **side output** (or is dropped, if you do not define one). The course models the same idea with `watermark_lag`, which measures the gap between the current processing time and the newest event.

**Trade-off.** A watermark that is too aggressive (advancing too fast) drops data you needed. A watermark that is too conservative holds windows open longer, increasing state, latency and cost.

**In practice.** I set the watermark from the *observed lateness distribution*, not from a guess: if 99.9% of events arrive within 90 seconds of their event time, the watermark sits at 90 seconds. And I always define a side output for late data so it can be reprocessed — a silently dropped late event is a wrong number with no trace.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import watermark_lag, ingest_events

lines = open("sample_data/events.csv").read().splitlines()
accepted, _ = ingest_events(lines)

lag = watermark_lag(accepted)
print("watermark lag:", lag)
print("lag in seconds:", lag.total_seconds())
```

---

### Q6. What is a side input, and when would you use one?

**Answer.** A side input is a smaller dataset made available to every element of a main `PCollection` — a lookup table, a configuration, a broadcast dictionary.

**Mechanism.** Beam passes a side input as a keyed view that the `DoFn` reads during processing. The critical rule: the side input is read *per element*, so a lookup against a huge side input is a network round-trip per element. Beam offers broadcast-style side inputs for small data, and the pattern to avoid is accidentally using a 10 GB side input as a per-element lookup.

**Trade-off.** Side inputs are the idiomatic way to avoid a shuffle-join. They are also a performance trap when the data is big, and a correctness trap when the side input is being updated while the pipeline runs.

**In practice.** I use a side input for a currency-rate table and a small region mapping — exactly like the course's `CURRENCY_TO_EUR`, which is applied per row in `normalise_currency`. For anything larger than a few megabytes I filter with a join instead, and I make sure the side input is a fixed snapshot so the output is deterministic and reproducible.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import CURRENCY_TO_EUR, normalise_currency

print("rate table (the side input):", CURRENCY_TO_EUR)
print("100 GBP ->", normalise_currency(100.0, "GBP"), "EUR")
```

---

### Q7. How do you choose between Cloud Composer and Workflows?

**Answer.** Composer when the orchestration is a DAG with dependencies, backfills, and data-aware logic. Workflows when the orchestration is a chain of API calls and service invocations with no branching data logic.

**Mechanism.** Composer is managed Apache Airflow: you write Python DAGs, Airflow gives you a scheduler, a dependency graph, the concept of a *logical date* (and therefore backfills), XComs for small data passing, and a rich operator ecosystem. Workflows is a serverless state machine: you define a series of steps and transitions, each of which calls an API or a service, and it is event-driven and billed per transition.

**Trade-off.** Composer is a full orchestrator with a real learning curve, a control-plane UI and a per-environment-node-hour cost ($0.0564). Workflows has no idle cost and no infrastructure, but its expressiveness is limited to steps and transitions — no Python, no complex branching on data.

**In practice.** My default: Composer for anything that involves a data pipeline with a real dependency graph, because backfills are non-negotiable once you are in production. Workflows for glue — a webhook that triggers a Dataflow job and then a BigQuery query, with a notification at the end.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from cost_model import COMPOSER_PER_ENV_NODE_HOUR, estimate

print("per env-node-hour:", COMPOSER_PER_ENV_NODE_HOUR)
print(estimate("composer", environment_nodes=730, monthly=True))
```

---

### Q8. What is a logical date, and why is it the most important concept in Airflow?

**Answer.** The logical date is the label of a DAG run, representing the *data interval* it processes, not the moment it ran. A run labelled `2026-01-15` processes the data for that day, whether it executed on the 15th or the 20th.

**Mechanism.** Every DAG run has a `logical_date` (Airflow calls it `execution_date` historically, which is a misnomer). The schedule interval defines the data window, and the run's parameters interpolate it into the task commands — so a query filters `event_date = '{{ ds }}'`. Because the label is stable, you can **re-run any historical date** and get the same result.

**Trade-off.** Logical dates give you reproducibility and backfills, at the cost of a mental model that trips up newcomers — a DAG that runs daily has a logical date of *yesterday* at midnight, which confuses people expecting "today".

**In practice.** The rule I teach: **never use `now()` in a task; always use the logical date.** If a task computes `CURRENT_DATE()`, a backfill produces wrong data silently. Every task filters on the interval, and the catchup and backfill commands work because of that discipline.

**Failure story.** A team had a DAG that inserted rows using `CURRENT_DATE()` in the filter. It ran correctly for months. Then they backfilled three months after a schema change and the backfilled rows went into the wrong partitions — a silent, retroactive data corruption that took a full reconciliation cycle to detect.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import partition_for_date

# The logical date is what the partition decorator is derived from.
for logical_date in ("2026-01-15", "2026-01-16", "2026-02-01"):
    print(logical_date, "->", partition_for_date(logical_date))
```

---

### Q9. How do you make an Airflow DAG failure-safe in production?

**Answer.** Make every task idempotent, give it a bounded retry with exponential backoff, use a pool to limit concurrency against a scarce resource, and always set a `timeout` so a hung task does not hold a slot forever.

**Mechanism.** A task that times out is killed and retried. A task that is *not* idempotent will duplicate work on every retry — which is why the course's pipeline has a deterministic `dedup_key`. Concurrency control matters because a DAG with 200 tasks that all query the same BigQuery table will hit the project's query concurrency limit and start failing with "too many concurrent queries".

**Trade-off.** Aggressive retries turn a transient failure into a storm against a struggling downstream. A pool that is too tight makes the pipeline slow; too loose and it starves other DAGs.

**In practice.** My defaults: `retries=3`, `retry_delay=timing.exponential(minutes=2)`, `timeout=timing.hours(2)`, a `Pool` sized to the downstream's limit, and a `TriggerDagRunOperator` instead of `SubDagOperator` for cross-DAG dependencies. And every task writes a checkpoint keyed by the logical date, so a retry resumes rather than restarts.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import dedup_key, partition_for_date

# Idempotency is what makes retries safe.
logical_date = "2026-01-15"
partition = partition_for_date(logical_date)
print("task writes rows keyed by:", dedup_key("evt-0042", partition))
print("re-running the task produces the same key, so the load is safe")
```

---

### Q10. Why would you use Dataform instead of plain SQL in BigQuery?

**Answer.** Dataform gives you version-controlled, tested, dependency-aware SQL with generated lineage — you write `ref()` and `source()` instead of hand-maintaining table names, and the repository becomes reviewable in a pull request.

**Mechanism.** A Dataform repository is a set of `.sqlx` files with `config()` blocks declaring table type, description, tags and tests. `ref('stg_events')` resolves to the full table name and creates a DAG edge, so Dataform builds the dependency graph and runs models in topological order. **Assertions** are built-in tests — `unique`, `not_null`, `relationships` — and they fail the run when the data is wrong.

**Trade-off.** Dataform adds a layer over SQL: you need to learn the templating (Jinja-like) syntax, the config blocks and the compilation model. For a handful of ad-hoc queries that is pure overhead.

**In practice.** I use Dataform as soon as there are more than about five models that depend on each other, because that is exactly when hand-maintained SQL starts to break — someone renames a table and three other models fail at 3am. The tests are the real value: a `not_null` on a primary key catches an upstream schema change before it reaches the dashboard.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from service_catalog import SERVICES

service = SERVICES["dataform"]
print(f"{service.name}: {service.summary}")
print("pricing:", service.pricing_model)
print("resources:", service.key_resources)
```

---

### Q11. What is a Dataform assertion, and how do you design one that actually catches problems?

**Answer.** An assertion is a test that runs after the model and fails the workflow when the data violates a rule. Good assertions test the things that would silently corrupt downstream results.

**Mechanism.** Dataform ships generic assertions (`unique`, `not_null`, `relationships`) and custom SQL assertions, which run a query and fail if it returns rows. Assertions can be scoped to `severity: warn` so a failure does not block the pipeline but is still recorded.

**Trade-off.** Assertions that are too strict stop the pipeline for a condition nobody cares about, and people learn to ignore red builds. Assertions that are too loose let corruption through to the dashboard.

**In practice.** My assertion set for every model: `not_null` and `unique` on the primary key, `relationships` for every foreign key, a custom row-count check against a threshold, and a freshness check on the load timestamp. And I tie the row-count check to the reject counts — if the pipeline rejected 12 malformed rows, that is a signal, and the course's `reject_counts` output is exactly the shape to alert on.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import EXPECTED_REJECT_COUNTS, reject_counts, ingest_events

lines = open("sample_data/malformed_events.csv").read().splitlines()
_, rejected = ingest_events(lines)

counts = reject_counts(rejected)
print("observed:", counts)
print("expected:", EXPECTED_REJECT_COUNTS)
print("match:", counts == EXPECTED_REJECT_COUNTS)
```

---

### Q12. When would you choose Cloud Data Fusion over a code-first pipeline?

**Answer.** Data Fusion when the integration is glue that a business analyst must maintain — connectors, a few transforms, a schedule — and the pipeline's logic changes monthly rather than daily.

**Mechanism.** Data Fusion is a visual ETL tool: you build a **pipeline** from nodes (source, transform, sink), with connectors for databases, SaaS, Google services and files. Pipelines can be batch or streaming, and they run on a Dataproc cluster under the hood. It supports data lineage and a low-code canvas.

**Trade-off.** Visual pipelines are excellent for the first version and painful for the tenth. Business logic embedded in a canvas cannot be reviewed in a pull request, cannot be unit-tested, and the transform set is limited to what the canvas offers. Data Fusion's own pricing is per cluster-hour plus egress, and it runs on your Dataproc — so the costs stack.

**In practice.** I use Data Fusion for connector-heavy integration where the logic is a filter, a join and a schedule, especially where a business team owns it. The moment the logic becomes a real algorithm, I move it to code — a Dataflow job, a Dataform model, or a Spark job in Dataproc — because the code path is the one that can be tested.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from service_catalog import SERVICES

service = SERVICES["data-fusion"]
print(f"{service.name}: {service.summary}")
print("pricing:", service.pricing_model)
print("resources:", service.key_resources)
print("preview:", service.availability.preview)
```

---

### Q13. When would you choose Cloud Dataprep, and what are its real limits?

**Answer.** Dataprep for browser-based, self-service data preparation — profiling, cleaning, wrangling and shaping files for analysis, mostly by a data analyst rather than an engineer.

**Mechanism.** Dataprep is a visual interface over a Dataproc Spark cluster. You build a **flow** from datasets and recipes (curated transformation sets), and the interface gives you profile cards, data quality bars, and a visual diff of every change. It runs in an instance group and is billed per user-hour ($0.60) with a free tier.

**Trade-off.** Dataprep's power is in the profiler and the visual recipes; its weakness is that the transformations are not code, so they cannot be version-controlled properly, unit-tested, or reproduced outside the tool. Pricing is per user-hour, which means a team of ten analysts costs ten times what one costs — a real consideration.

**In practice.** I use Dataprep when the user is a business analyst and the task is "profile this file and get it clean enough to load". I do not use it for a pipeline that must run reliably for years. The honest boundary: Dataprep for exploration and one-off preparation, code for anything that runs on a schedule.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from cost_model import DATAPREP_PER_USER_HOUR, estimate

print("per user-hour:", DATAPREP_PER_USER_HOUR)
print(estimate("dataprep", user_hours=8 * 20, monthly=True))
```

---

### Q14. What is the difference between Data Fusion and Dataprep?

**Answer.** Data Fusion is a general-purpose visual **ETL and integration** tool for building pipelines between systems; Dataprep is a specialised **data preparation and profiling** tool for wrangling data files for analysis.

**Mechanism.** Data Fusion nodes connect sources to sinks — databases, SaaS, Google services, file systems — and its pipelines can be streaming. Dataprep works over datasets (files and tables) with recipes and profiling, and its output is typically a cleaned dataset, not a production feed. They share a visual canvas and both run on Dataproc, which is why they get confused.

**Trade-off.** Overlap is real: both can do a CSV-to-BigQuery load with a filter. The choice comes down to intent — if the requirement is "connect these systems and keep it running", it is Data Fusion; if it is "profile this file, clean it, and understand it", it is Dataprep.

**In practice.** I have seen teams install both and use them for the same job, which is the worst outcome — two visual pipelines to maintain, two sets of Dataproc clusters, and no code review. I pick one based on the requirement's shape and standardise.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from service_catalog import SERVICES, services_by_category

for service in services_by_category("Integration"):
    print(f"{service.name:<18} {service.data_role:<8} {service.summary}")
    print(f"{'':18} resources: {service.key_resources}")
```

---

### Q15. How do you choose between Composer, Dataflow and Dataproc for a job that must run every night?

**Answer.** If the job is SQL over warehouse tables, use BigQuery plus a scheduled query. If it needs custom code, use Dataproc Serverless for Spark or Dataflow batch for Beam. If it needs several steps with dependencies, use Composer to orchestrate any of them.

**Mechanism.** The three solve different layers: Dataproc and Dataflow are **execution** engines, Composer is **orchestration**. A nightly job frequently uses more than one — Composer runs a Dataproc job, then a Dataform workflow invocation, then a BigQuery validation query.

**Trade-off.** Every additional engine in the stack adds a runtime, a failure mode, and a bill. A "just use Airflow to run SQL" approach looks elegant and becomes a debugging nightmare at scale, because Airflow's own scheduler and the query engine are now coupled.

**In practice.** I default to the fewest moving parts: BigQuery for anything SQL-shaped, with Composer only when there is genuine dependency management to justify it. The course's own pipeline is the model — the logic is pure Python, the orchestration is a schedule, and the components are swappable.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from platform_sim import build_demo_project, format_pipeline_log

project = build_demo_project()
lines = open("sample_data/events.csv").read().splitlines()
result = project.run_pipeline(lines)
print(format_pipeline_log(result))
```

---

### Q16. How do you test a data pipeline, and what does "the pipeline passed" actually mean?

**Answer.** Test in layers: pure logic with unit tests, the wiring with an integration test against a real (small) source, and the output with a data-quality assertion. "The pipeline passed" means the output satisfies invariants — not that the job exited zero.

**Mechanism.** The course's design is the answer: all the business rules live in `pipeline_logic.py` as pure functions, with no cloud imports, so `pytest` runs in under a second with no credentials. `validate_event` is the single source of truth for event validity, so a rule cannot be enforced in one place and forgotten in another.

**Trade-off.** Pure-function testing requires the discipline to keep business rules out of the deployment script. The alternative — testing only by running the pipeline — means every test needs a live project, and the suite becomes slow and flaky, so people stop running it.

**In practice.** The layers I insist on: unit tests on every rule (the course asserts the exact expected summary and reject counts), an integration test that runs the whole pipeline against the sample data, and a data-quality gate at the end of the run that compares the output to expected invariants and fails the job if they do not match. The exact numbers — 4800 events, 12 malformed rows, the per-region revenue totals — are assertable precisely because the logic is deterministic.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import EXPECTED_SUMMARY, ingest_events, aggregate_events

lines = open("sample_data/events.csv").read().splitlines()
accepted, _ = ingest_events(lines)
summary = aggregate_events(accepted)

for region, expected in EXPECTED_SUMMARY.items():
    actual = summary[region]
    ok = int(actual["event_count"]) == expected["event_count"]
    print(f"{region}: count={int(actual['event_count']):>5} revenue={actual['revenue_eur']:>12,.2f} {'ok' if ok else 'MISMATCH'}")
```

---

## 📚 Related chapters

- [5.1 — Hadoop & the Big Data Ecosystem](../chapters/20-hadoop-and-big-data-ecosystem.md)
- [5.2 — Apache Spark & Cloud Dataproc](../chapters/21-apache-spark-and-dataproc.md)
- [5.3 — Apache Beam & Cloud Dataflow](../chapters/22-apache-beam-and-dataflow.md)
- [5.4 — Airflow, Composer & Workflows](../chapters/23-airflow-composer-and-workflows.md)
- [5.5 — Dataform & the Transformation Layer](../chapters/24-dataform-and-the-transformation-layer.md)
- [6.1 — Cloud Data Fusion](../chapters/25-cloud-data-fusion.md)
- [6.2 — Cloud Dataprep](../chapters/26-cloud-dataprep.md)

## 📖 Further Reading

- [Apache Beam documentation](https://beam.apache.org/documentation/)
- [Cloud Dataflow documentation](https://cloud.google.com/dataflow/docs)
- [Cloud Dataproc documentation](https://cloud.google.com/dataproc/docs)
- [Cloud Composer documentation](https://cloud.google.com/composer/docs)
- [Dataform documentation](https://cloud.google.com/dataform/docs)
