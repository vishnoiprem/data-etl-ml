# FAQ

The questions students actually ask, with real answers. If your question is not here, it is probably in [GLOSSARY.md](GLOSSARY.md) or [CHEATSHEET.md](CHEATSHEET.md).

## 🚀 Getting Started

**1. Do I need a GCP account to do this course?**

No. The whole course runs on your laptop with Python 3.11+ and `pytest`. The labs use a local simulation — `project/core/` contains a service catalogue, an IAM policy evaluator, a cost model and a pipeline, and `project/local_runner.py` exposes them as a command-line console. There are no credentials to configure and no network calls. The [optional GCP path](SETUP.md#-the-optional-gcp-path) is there if you want to deploy for real, but nothing depends on it.

**2. How long does the course take?**

The 34 chapters are a reading course with hands-on sections. Most people take 6–10 hours end to end, plus the time spent on the optional deployment labs. If you are preparing for the certification, budget closer to 40 hours including practice exams.

**3. Do I need to know SQL, Python or Java?**

Python and SQL. The pipeline is written in Python and the BigQuery labs are SQL. You do not need Java, Scala or Hadoop experience. The Spark and Beam chapters explain what you need as you go.

**4. I am new to cloud. Is that a problem?**

No. Chapter 1 starts from what a region is. The course assumes you can use a terminal and read Python, not that you have worked in the cloud before.

**5. What is the difference between `sample_data/events.csv` and `sample_data/malformed_events.csv`?**

`events.csv` holds the 4800 clean events, one per line with a header. `malformed_events.csv` holds 12 deliberately broken rows used to exercise the validation and dead-letter path. The `--run` command reads `events.csv` first — that clean run rejects nothing — then merges in the malformed rows and prints the **Dead-letter path** section, so you can see every reason code the validator can emit. The malformed rows are also covered by the test suite, which asserts the exact reject counts:

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import ingest_events, reject_counts

lines = open("sample_data/malformed_events.csv").read().splitlines()
accepted, rejected = ingest_events(lines)
print(len(accepted), len(rejected))
print(reject_counts(rejected))
```

Expected output:

```text
0 12
{'wrong_field_count': 2, 'bad_amount': 1, 'unknown_region': 2, 'unknown_channel': 1, 'unknown_currency': 1, 'unknown_event_type': 1, 'missing_event_id': 1, 'missing_user_id': 1, 'negative_amount': 1, 'bad_timestamp': 1}
```

**6. Why does `--run` report 0 rejects when the summary says 12 malformed rows?**

Because the 12 malformed rows are a separate file, not part of `events.csv`. The generator prints `malformed_rows: 12` as a property of the dataset it wrote. The runner loads the clean file.

**7. Do I have to run the labs in order?**

No, but it helps. Chapters 2–4 establish regions, zones, IAM and networking, which later chapters assume. If you only care about BigQuery, read chapters 12–15 and skip ahead.

**8. How do I run a single module without the runner?**

Import it directly. Every core module uses only the standard library:

```python
import sys
sys.path.insert(0, "project/core")

from service_catalog import get_service, regions_for

print(get_service("bigquery").summary)
print(len(regions_for("bigquery")), "regions")
```

**9. What is the `sys.path.insert` for?**

The core modules are plain files, not an installed package. Adding `project/core` to the path lets `import service_catalog` work from the course root without installing anything.

**10. The linter says "Ran 1060 checks". Will that number change?**

Yes. The count grows as chapters and resources are added, because it counts every link, every snippet and every expected output. The pass/fail result is what matters.

## 💸 Cost and Billing

**11. How much will this cost me if I deploy it for real?**

More than the free tier, and you should assume a real bill. The free tier covers 5 GB-month of storage, 1 TB of BigQuery scans, 1 GB of egress, 10 GB of Pub/Sub, and trivially small Compute, Cloud Run and Cloud Functions allowances. A full pipeline in one region typically lands between **$50 and $400 per month**, dominated by BigQuery scans, network egress and always-on streaming workers. Set a budget alert before you create anything, and delete the project when you are done — see the [cost section of SETUP.md](SETUP.md#5-free-tier-caveats).

**12. Why did my query cost so much?**

Almost always because it scanned more than you expected. The four usual causes, in order of frequency:

1. **No partition filter.** A partitioned table queried without `WHERE event_date = ...` scans every partition.
2. **`SELECT *`.** BigQuery is columnar, so you pay for every column read, even ones you never reference.
3. **A function on the partition column.** `WHERE DATE(event_ts) = ...` defeats pruning. Filter on the raw column instead.
4. **Small tables scanned repeatedly.** Many tiny queries each carry a fixed overhead.

Check with a dry run before executing:

```text
bq query --use_legacy_sql=false --dry_run 'SELECT region, SUM(revenue_eur) FROM PROJECT_ID:DATASET.events GROUP BY region'
```

The dry run reports bytes processed without charging you.

**13. What is the cheapest way to run this pipeline?**

Batch on BigQuery with a partitioned table. The course's own comparison prices the same workload four ways:

| Architecture | Monthly cost |
|---|---|
| Streaming on Dataflow | $0.0000 |
| Spark on Dataproc | $0.0000 |
| Batch on BigQuery (partitioned) | $0.0625 |
| Batch on BigQuery (unpartitioned) | $6.2500 |

The streaming and Spark rows show $0 because the demo workload is smaller than the free-tier allowances. Partitioning is the 100× difference between the last two rows, and it is the cheapest real lever you have.

**14. Do budget alerts stop me from being charged?**

No. Budgets send notifications. They do not cap spending or shut anything down. The only reliable way to stop charges is to delete the resources.

**15. When do I actually get charged?**

Usage is billed per hour or per second, but the charges appear on your statement with a delay — often a few hours to a day for the underlying usage, and up to several days to appear on the invoice. Deleting a project stops the usage immediately; the final bill still arrives.

**16. How do I control costs once the project is real?**

| Lever | Effect |
|---|---|
| Partition every large table | 100× fewer bytes scanned |
| Use Standard storage only for hot data | Move cold data to Nearline or Coldline |
| Set a BigQuery slot reservation | Caps capacity spend, adds a commitment |
| Label every resource | Makes the cost report legible |
| Set per-team budgets | Alerts before the surprise |
| Use Cloud Run and Cloud Functions | Scale to zero when idle |
| Delete dev projects on a schedule | Removes forgotten clusters |

**17. Why is Archive storage cheaper but sometimes the wrong answer?**

Archive costs $0.0012 per GB-month, 16.7× less than Standard. But retrieval costs $0.05 per GB, so reading a 1 TB archive costs **$50** in retrieval alone, versus $0 for Standard. Archive is for data you will read yearly or never. The moment a dashboard queries it, the saving disappears.

**18. What is a slot, and do I need reservations?**

A slot is a unit of BigQuery compute. One slot-hour costs $0.06. On-demand pricing bills by bytes scanned and allocates slots behind the scenes; flat-rate and reservation pricing bill by slot-hour and commit you to capacity. Reservations save money only when you can commit to a minimum spend and your usage is predictable.

## 🤔 Choice of Service

**19. BigQuery or Dataproc?**

BigQuery if the work is SQL over tabular data — it is serverless, you pay per byte scanned, and there is no cluster to size. Dataproc if you need to run existing Spark, Hadoop or Hive code, need custom JVM libraries, or must process data that does not fit the BigQuery execution model. If you are starting from scratch with SQL, BigQuery wins; if you have a Spark estate, Dataproc wins.

| | BigQuery | Dataproc |
|---|---|---|
| Programming model | SQL, UDFs, DataFrame API | Spark, Scala, Java, Python |
| Infrastructure | None | Cluster you size |
| Pricing | $6.25 per TB scanned, or slot-hour | $0.0476 per vCPU-hour |
| Scales to | Petabytes | Thousands of nodes |
| Best for | Analytical SQL | Existing Spark workloads |

**20. Dataflow or Dataproc — which do I pick?**

Dataflow for Beam. Dataproc for Spark. The deciding question is which API your team already knows, and whether your pipelines need both batch and streaming from one codebase. Dataflow also gives you managed streaming with autoscaling, while Dataproc gives you the full Spark ecosystem including Spark SQL, MLlib and Spark Structured Streaming.

| | Dataflow | Dataproc |
|---|---|---|
| Model | Apache Beam | Apache Spark |
| Batch and streaming | One pipeline, both modes | Separate job types |
| Streaming | Fully managed, autoscaling | Spark Structured Streaming, self-tuned |
| Per vCPU-hour | $0.0595 | $0.0476 |
| Best for | Unified batch + streaming | Spark-native teams |

**21. Why not just use Airflow for everything?**

Because Airflow orchestrates; it does not process. Airflow is a scheduler and dependency manager. It will happily run a Dataflow job, a BigQuery query and a Dataproc submission, but the data movement between them needs a processing engine. Using Airflow alone for heavy transformations means writing Python tasks that run on workers, which gives up autoscaling, streaming, and Beam's unified model.

Use Airflow for *when* things run. Use Dataflow, Dataproc or BigQuery for *what* happens to the data.

**22. Do I need Dataform?**

Not to start. Dataform adds version control, testing, dependency management and lineage on top of BigQuery SQL. It becomes necessary the moment you have more than a handful of transformations, because otherwise you end up with scheduled queries that nobody can reason about. If you are writing production dbt-style models in BigQuery, use Dataform. If you are running one exploratory query, do not.

**23. Pub/Sub or Kafka?**

Pub/Sub if you want a fully managed Google Cloud service with simple topics and subscriptions, and you do not need the Kafka protocol. Kafka if you already run Kafka, need its consumer-group model, or need to talk to existing Kafka clients. Confluent Cloud on Google Cloud gives you Kafka with Google Cloud billing and networking.

| | Pub/Sub | Kafka |
|---|---|---|
| Managed by Google Cloud | Fully | No — Confluent Cloud |
| Consumer groups | No | Yes |
| Exactly-once | Pull subscribers | Transactional producers |
| Cost | $0.40 per GB ingest | Cluster plus storage |
| Best for | Decoupling producers and consumers | Existing Kafka estates |

**24. Data Fusion, Dataprep, or hand-written code?**

Dataprep for interactive data exploration and cleaning in the browser — it is row-limited and meant for analysts. Data Fusion for visual pipeline building that must run continuously. Neither replaces code when the logic is complex, the logic is tested, or the pipeline needs to be version-controlled.

**25. When do I need Dataplex or Data Catalog?**

When you have more than one team reading the data and nobody agrees on what `revenue` means. Dataplex gives you a governed catalog, lineage and quality across lakes, warehouses and streams. Data Catalog is the older, lighter search service. For a single-team warehouse, BigQuery's own dataset and table metadata is enough.

**26. Cloud SQL or Cloud Spanner?**

Cloud SQL for ordinary relational workloads with familiar Postgres or MySQL, where you want to write SQL and manage the schema yourself. Spanner when you need to scale writes and reads across regions with strong consistency and no manual sharding. Spanner costs roughly 5–10× more per unit of capacity, so it is a deliberate step up, not a default.

**27. How many regions should I use?**

One, to start. Multi-region adds availability and it adds cost, and it complicates the residency story. Choose a second region only when you have a specific requirement: data residency, latency for users in another geography, or an availability target that a single region cannot meet.

## 🏗️ Architecture and Design

**28. What breaks at 3am?**

In order of likelihood:

1. **A stream falls behind and hits Pub/Sub retention.** No dead-letter topic, so poison messages retry forever and block the backlog. Configure a DLQ with `--max-delivery-attempts`.
2. **The BigQuery table was never partitioned.** The daily query scans everything, gets slower as data grows, and eventually fails on quota or times out.
3. **The service account's key rotated.** A Compute Engine instance with a key-based credential stops authenticating. Use attached service accounts instead of keys.
4. **The Composer environment ran out of quota.** Idle intervals hit the scheduler's task quota, and the DAG silently stops scheduling.
5. **A partition expired before the backfill ran.** The late-arriving data has nowhere to land.
6. **Egress crossed a region boundary.** A copy job moved 500 GB out of Cloud Storage overnight at $0.12 per GB.

Every one of these has a preventive control, and the course covers each in the relevant chapter. The through-line: **alert on data freshness, not just on job success.** A job that succeeds but writes nothing is the failure mode that wakes people up.

**29. How do I design the pipeline — push or pull ingestion?**

Push when the source can make outbound calls, or when the producer and consumer are both Google Cloud services that can authenticate with IAM. Pull when the source is behind a firewall, when you need to control the rate, or when you need to batch for efficiency.

| | Push | Pull |
|---|---|---|
| Direction | Source calls the target | Target fetches from the source |
| Needs inbound connectivity | Yes | No |
| Rate control | Target must absorb it | Consumer controls it |
| Use for | APIs, webhooks, event producers | Databases, batch files, rate-limited sources |

**30. Should I use event time or processing time?**

Event time for anything involving facts about when something happened — revenue, SLA breaches, order totals. It lets you correct late-arriving data and reprocess a window correctly. Processing time for operational metrics about your own pipeline — ingestion lag, throughput, error rate. Mixing them is the classic source of irreproducible numbers.

**31. What is a watermark, in practice?**

A streaming pipeline cannot wait forever for a late event. The watermark says "I have processed all events up to this event time". Data older than the watermark is late. Practical consequences:

- Set your watermark tolerance to match reality — usually a few minutes to a couple of hours.
- Beyond the watermark, data goes to a late-arrival path, not into the window it belongs to.
- A watermark that is too aggressive drops data; too lax and the pipeline stalls waiting.

**32. How do I make a pipeline idempotent?**

Write to a deterministic destination and make the write a replace, not an append:

- Write to a fixed partition — `event_date = '2026-01-15'` — not to "today".
- Use a deterministic key. This course uses `dedup_key(event_id, partition)`.
- Make the step replace the partition rather than append to it.
- Use `MERGE` or `CREATE OR REPLACE`, not `INSERT`.

Then running the same logical date twice leaves the same state.

**33. What is exactly-once, and do I need it?**

Exactly-once means each message is processed exactly once. In Pub/Sub it is available only for pull subscribers with an exactly-once-enabled subscription. You need it when double-processing causes real harm: billing, audit logs, compliance records. For analytics and ML training, at-least-once plus idempotent writes is usually enough and much cheaper.

**34. How do I choose between push and pull Pub/Sub?**

Push for serverless consumers — a Cloud Run service or a Cloud Run function — where you want Pub/Sub to scale the consumer for you. Pull for long-running consumers, Dataflow pipelines, and batch drains, where you control the rate and the consumer holds the connection. Push also needs a public or VPC-accessible endpoint with an OIDC token; pull just needs credentials.

**35. Should the pipeline be batch or streaming?**

Batch when the data arrives in files, the requirement is not real-time, and you want the cheapest option. Streaming when a decision must be made in seconds, or when the source is a continuous event feed. A common pattern is both: stream into BigQuery for the dashboard, and run a batch job for the authoritative numbers.

**36. How do I handle late-arriving data?**

Three options: keep a lookback window and reprocess the last N days on every run; write late rows into a dedicated staging table and merge them separately; or use BigQuery's `MERGE` against a target partition keyed on `event_id`, which makes reprocessing safe. The course's `deduplicate()` implements the last of these.

## 🔧 Operations and Troubleshooting

**37. `ModuleNotFoundError: No module named 'service_catalog'`**

You are in the wrong directory. The import path is relative to the course root. `cd` to the directory containing `project/` and `resources/`, then run `python project/local_runner.py --run`.

**38. `ModuleNotFoundError: No module named 'pytest'`**

`pytest` is not installed in the active environment. Run `source .venv/bin/activate`, then `python -m pip install pytest`. It is the only third-party dependency in the course.

**39. `python: command not found`**

macOS ships `python3`, not `python`. Either use `python3` everywhere or activate the virtual environment, which puts a `python` on the path pointing at 3.11+.

**40. `sample data not found at .../sample_data/events.csv`**

The generator has not run. Execute `python resources/sample_data.py --output-dir ./sample_data` from the course root.

**41. `gcloud: command not found`**

The Cloud SDK is not installed. Install it, or skip the optional GCP path entirely — the course is complete without it. See [SETUP.md](SETUP.md).

**42. `ERROR: (gcloud.billing) The project ... has no billing account`**

Google Cloud requires a billing account. Run `gcloud billing projects link PROJECT_ID --billing-account=YOUR_BILLING_ACCOUNT`, then confirm with `gcloud billing accounts list`.

**43. `ERROR: Could not create the service account`**

The IAM API is not enabled. Run `gcloud services enable iam.googleapis.com`.

**44. My Pub/Sub subscription is stuck and messages are piling up**

Three things to check, in order:

1. **Is the consumer running?** A subscription with no active consumer accumulates messages until retention expires them.
2. **Is there a dead-letter topic?** Without one, poison messages retry until the max delivery attempts and are then dropped. Configure `--dead-letter-topic` and `--max-delivery-attempts`.
3. **Is the ack deadline too short?** If processing takes longer than the deadline, Pub/Sub redelivers while you are still working on the message. Raise `--ack-deadline` or extend it from the client.

**45. My BigQuery query returns "Resources exceeded during query execution"**

Usually quota, not size. Check the BigQuery reservation and slot usage for the project. The fix is a reservation, or lower concurrency. A correlated subquery that re-reads a large table can also blow up slot usage — rewrite it as a join.

**46. How do I debug an IAM permission error?**

The IAM policy evaluator in the course answers exactly this. `evaluate()` returns which roles matched and why:

```python
import sys
sys.path.insert(0, "project/core")

from iam_policy import Principal, Binding, Policy, evaluate

policy = Policy()
policy.add(
    Principal("user", "analyst@example.com"),
    Binding("roles/bigquery.dataViewer"),
    resource="projects/gcp-de-course/datasets/curated",
)

decision = evaluate(
    policy,
    "analyst@example.com",
    "bigquery.tables.getData",
    resource="projects/gcp-de-course/datasets/curated",
)
print(decision.allowed)
print(decision.reason)
print(decision.matched_roles)
```

Expected output:

```text
True
bigquery.tables.getData is granted at the resource via roles/bigquery.dataViewer
('roles/bigquery.dataViewer',)
```

The `--iam` command runs the same checks against the demo project and prints a ✓ or ✗ for each identity.

**47. Why is my Composer environment costing money when nothing is running?**

Composer environments are always on. You are billed per environment-node-hour, 24 hours a day, whether or not your DAGs run. For a course or a low-traffic project, consider turning the environment off and on around the times you need it.

**48. The linter reports a broken link — now what?**

The message names the file and the target path, for example `resources/SETUP.md: broken link -> ../chapters/99-missing.md`. Either the target was renamed or the link is wrong. The linter checks every relative link in every chapter, interview file and resource file, so a fix in one place can surface a broken link elsewhere.

**49. The linter reports a Python snippet that does not parse**

Fenced blocks tagged `python` are parsed with `ast.parse`. A snippet with a typo fails the check. The message names the snippet index within that file. A block that ends with `...` is treated as an abbreviated call and is exempt.

**50. How do I know my environment is correct?**

The 12-point checklist in [SETUP.md](SETUP.md#-verification-checklist). The four that catch most problems: `python3 --version` shows 3.11+, `wc -l sample_data/events.csv` shows `4801`, `python3 -m pytest project/tests/ -q` shows `102 passed`, and `python resources/audit_course.py` shows `No errors. The course is clean.`

## 🎓 Career and Certification

**51. Is the Google Cloud Data Engineer certification worth it?**

It carries real weight with recruiters, particularly for roles where the posting names it. It also forces you through the material systematically. But it is a signal, not a substitute for being able to build something. Most hiring managers in data engineering will still ask you to talk through a pipeline you have actually run. This course exists so that the answer to that question is not "I've only read about it".

**52. What does the certification cover?**

Data engineering on Google Cloud: ingestion (Pub/Sub, Kafka, Datastream, Transfer), storage (Cloud Storage, BigQuery, BigLake, databases), processing (Dataflow, Dataproc, Composer, Dataform, Data Fusion), orchestration, analytics, and ML integration (Vertex AI, BigQuery ML). It is a multiple-choice and multiple-select exam, so breadth matters as much as depth.

**53. What do I need to know before I sit the exam?**

Fluent SQL, including window functions and joins. Comfortable with the GCP resource hierarchy, IAM and service accounts. Clear on when to choose BigQuery versus Dataflow versus Dataproc versus Composer. Cost awareness — partitioning, slots and egress. And enough hands-on to have opinions.

**54. How long should I study for it?**

Two to four weeks of focused work, if you already know cloud basics. Longer if you are coming from a self-taught background with no production exposure. Take the practice exams early — they are the best diagnostic.

**55. Do I need to take the exam before or after building something?**

After. The exam tests judgement about trade-offs, and judgement comes from having made the trade-off. Do the optional deploy path in this course first, even a minimal version, so you have a real cost spike, a real IAM error and a real backfill to talk about.

**56. Which jobs does this qualification lead to?**

Data engineer, cloud data engineer, analytics engineer, data platform engineer, and streaming engineer are the common titles. The preparation is the same: SQL, orchestration, cost control and a grasp of when each managed service fits.

**57. What other certifications pair well with it?**

AWS Data Analytics, Databricks Data Engineer and Confluent Developer are the closest peers. A cloud-agnostic certification paired with a deep GCP one reads as "understands the principles and one platform deeply", which is a strong combination.

**58. Is a certification enough to get a job?**

No, and hiring managers know it. What gets you interviews is a portfolio that shows you can design a system, explain the trade-offs and talk about what broke. A single well-documented end-to-end project beats four certificates. The [end-to-end capstone](../chapters/34-end-to-end-capstone.md) is designed to be that project — build it, document it, and put it on your CV.

**59. How do I prepare for the behavioural interview as well?**

The technical questions come from the [interview bank](../interview/README.md) and the [top 40](../interview/top-40.md). For the behavioural side, prepare two stories: one where you owned a decision that went wrong and what you changed afterwards, and one where you had to make a trade-off between cost, speed and reliability. Be specific about what *you* did, and be honest — interviewers can tell.

**60. Should I learn Terraform and infrastructure as code?**

Yes, alongside the data skills. `terraform` is the expected tool for managing the resource hierarchy described in [chapter 2](../chapters/02-regions-zones-and-resource-hierarchy.md), and being able to describe a landing zone — projects, folders, org policy, IAM — is increasingly part of the senior end of the role.

## 🔗 Related

| Document | Contents |
|---|---|
| [SETUP.md](SETUP.md) | Installation, the optional GCP path, troubleshooting |
| [CHEATSHEET.md](CHEATSHEET.md) | Commands, cost formulas, decision tables |
| [GLOSSARY.md](GLOSSARY.md) | Every term, defined |
| [../CURRICULUM.md](../CURRICULUM.md) | The 34-chapter plan |
| [../interview/README.md](../interview/README.md) | The interview question bank |
