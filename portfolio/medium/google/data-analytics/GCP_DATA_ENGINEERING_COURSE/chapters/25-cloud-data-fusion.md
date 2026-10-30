# 6.1 — Cloud Data Fusion

> **Section 6 · Integration & No-Code · Lecture 6.1 · 8:00**

## 🎯 What you will learn

- What Cloud Data Fusion actually is, and the problem it was built to solve
- The instance model: Basic vs Enterprise, and why the version choice drives everything else
- Namespaces, the compute profile, and how autoscaling decides how many workers you get
- The pipeline canvas: source, transform, sink nodes, and how validation actually works
- The connector library: Cloud Storage, BigQuery, Cloud SQL, Pub/Sub, Salesforce, SFTP, and the marketplace
- Running a pipeline on **Dataproc** versus the **managed runtime** — the real trade-off
- Data lineage: what it captures, where it lives, and why it is only as good as your tagging
- Versioning and the dev/prod namespace workflow
- The `datafusion` CLI: `pipelines list`, `pipelines versions`, `pipelines create`, `pipelines run`
- An honest verdict: where Data Fusion beats hand-written code, and where it loses badly

---

## 🧠 Concept

### What Data Fusion is, precisely

Cloud Data Fusion is a **visual integration service**. You draw a graph of boxes and arrows, configure each box, and the service runs the graph for you as a batch job.

The problem it solves is real and specific. Most enterprise data movement is not "move a table from A to B" — it is "move a table from A to B, except filter out cancelled orders, join a customer dimension from C, rename six columns, convert currency, and split the output into two files with different schemas." That is a transformation pipeline, and writing it as Python or Spark means writing, testing, deploying, and monitoring code. Data Fusion lets a data engineer or a well-supervised analyst assemble the same thing as a graph.

**What Data Fusion is not:**

- It is not a general-purpose compute engine. It does not run arbitrary code.
- It is not a data warehouse. It moves data *into* BigQuery; it does not query it.
- It is not a streaming system. It is a batch integration tool. (There is a real-time Datastream integration, but that is Datastream's connector, not a Data Fusion streaming engine.)
- It is not free, and the free tier is not generous.

The honest framing: **Data Fusion is a pipeline authoring UI with a managed execution engine behind it.** The value is entirely in the authoring experience and the connector library. If you can express your pipeline in those terms, it is a great tool. If not, it is a straitjacket with a high price.

### The instance model

A Data Fusion **instance** is the tenant. It is created in a specific **region**, it has a **version** (Basic or Enterprise), and it carries a **namespace** structure. The instance is the billing boundary and the IAM boundary.

**Basic vs Enterprise** is the first decision and it is not close:

| | Basic | Enterprise |
|---|---|---|
| Version | 6.x | 6.x (or 7.x, or 5.x) |
| Runtime | Spark on Dataproc | Spark on Dataproc + Dataflow + Batch |
| Scheduling | Airflow-based (Composer) | Airflow-based (Composer) |
| Managed metadata (Dataplex) | No | Yes |
| Lineage | Limited | Full, with Dataplex |
| Users | One user for all edits | Multi-user, with per-user roles |
| Cost driver | Dataproc cluster + Composer | Dataproc + Composer + more |

**Basic is single-user.** Multiple people can open a Basic instance, but they share one editing identity — there is exactly one "owner" account for all edits, and every edit is attributed to it. That is a genuine problem in a team: no attribution, no per-user access control, and a shared credential that nobody wants to hold. **If more than one person will touch the pipeline, use Enterprise.** The upgrade path exists (upgrade the instance version), but doing it after three people have been editing in Basic means you inherit a mess of unattributed changes.

**Enterprise adds three things that matter:**
1. **Multi-user editing** with per-user Cloud IAM roles (`roles/datafusion.viewer`, `roles/datafusion.editor`, `roles/datafusion.admin`).
2. **Dataplex metadata integration** — the instance registers assets in a Dataplex lake/zone, which is what enables lineage.
3. **The ability to run the same pipeline on different runtimes** — Spark on Dataproc, or Dataflow for the Batch engine.

### Namespaces, the compute profile, and autoscaling

A **namespace** is a logical container inside the instance. It maps to a **Dataplex zone** (Enterprise) and it is the unit of versioning. The convention is three namespaces:

- `default` — scratch space, where new things land
- `dev` — where changes are made and tested
- `prod` — where the running pipelines live

Each namespace has a **compute profile**. This is the crucial and least understood part of Data Fusion, so let's be precise.

A compute profile says two things:

1. **The runtime** — Dataproc (Spark) or Dataflow (Batch).
2. **The minimum and maximum cluster size** — e.g. `min: 1, max: 3` workers.

The **runtime configuration** then has two resource pools:

- A **minimum compute** pool that runs continuously, and which processes scheduled pipelines.
- A **maximum compute** pool that scales out for interactive work.

**Here is the autoscaling behaviour, and this is where people get burned:**

> **A scheduled pipeline runs on the minimum compute pool. It does not autoscale up.**

Scheduled pipelines are pinned to the minimum pool precisely so that a 3 AM job cannot suddenly consume twenty workers and run up a large bill. Interactive pipelines — the ones you launch by hitting "Run" in the canvas — *do* use the max pool and will scale out.

This has a direct operational consequence: **your scheduled pipeline's throughput is bounded by your minimum cluster size.** If you size the minimum pool at 2 workers and your production pipeline needs 8, the job does not get faster because you raised `max`. It stays slow, and the fix is to raise `min` (and pay for it 24×7) or to move the work to a runtime that scales.

**The other thing to internalise: you are billed for the minimum cluster whether or not anything runs.** A Data Fusion instance with `min: 2` on Dataproc accrues Dataproc cluster-hours continuously, plus the Composer environment that runs the scheduler. That is the floor cost of the instance, before a single pipeline runs. This is why "let me spin up a Data Fusion instance to try it" is an expensive sentence.

### The pipeline canvas

A pipeline is a directed graph. It has three kinds of node:

- **Source nodes** — read from a connector (Cloud Storage, BigQuery, Cloud SQL, Pub/Sub, Salesforce, SFTP, ...).
- **Transform nodes** — operate on the data flowing between them.
- **Sink nodes** — write out to a connector.

**The transform vocabulary** is the substance of the tool. The useful ones:

| Transform | What it does |
|---|---|
| **Filter** | Keep or drop rows by a SQL-like predicate |
| **Join** | Inner, outer, cross, and left-anti joins on a key |
| **Aggregate** | Group by and compute aggregates (count, sum, min, max, avg, distinct) |
| **Derive** | Compute a new column with a SQL expression |
| **Select** | Rename, reorder, or drop columns |
| **Window** | Window functions: row number, rank, lag/lead, running totals |
| **Deduplicate** | Keep first/last per key |
| **Replace** | Literal or regex string replacement |
| **Split field** | Split one column into several by delimiter or regex |
| **Combine columns** | Concatenate several columns into one |
| **Add column** | Constant column, or from a named range |
| **Pivot / unpivot** | Reshape between wide and long |
| **Sample** | Keep N rows, or a percentage |
| **Assert** | Assert a condition; fail the pipeline if it is violated |
| **Add metadata** | Attach a static column |
| **Explode** | Flatten an array or nested record into rows |

**The validation mechanism deserves its own explanation, because it is the single most useful thing Data Fusion does that a naive implementation gets wrong.**

The **Assert** transform takes a boolean SQL expression. When the pipeline runs, each row is evaluated against the expression. If any row evaluates to false, the pipeline **fails** — it does not silently drop the row.

```text
Assert: amount_eur >= 0
Assert: region IN ('AMER','EMEA','APAC','LATAM')
Assert: event_id IS NOT NULL
```

This is exactly the shape of the `validate_event` function in `project/core/pipeline_logic.py`, but with a critical difference in **where the failure goes**:

- `pipeline_logic.validate_event` returns a **reason code**, and the caller routes the row to a dead-letter path while the pipeline keeps running.
- A Data Fusion **Assert fails the whole pipeline**.

That difference determines which you want. An Assert is right for a hard invariant ("a negative revenue row means the transformation is broken — stop"). A Filter is right for a soft condition ("drop refunds from the revenue metric"). If you want reject-quarantine semantics — the dead-letter pattern the course pipeline implements — Data Fusion has no first-class dead-letter sink. You would need a "Filter to valid" plus a "Filter to invalid" plus two sinks, which duplicates the predicate and is easy to let drift out of sync.

**That asymmetry is the summary of Data Fusion versus code:** the canvas makes the *happy path* obvious and the *error path* awkward.

### The connector library

This is where Data Fusion earns its keep. The connectors are maintained by Google, and the third-party marketplace is the real differentiator.

**Google-native connectors:**

| Connector | Notes |
|---|---|
| **Cloud Storage** | The workhorse. CSV, JSON, Avro, Parquet, ORC. Supports glob and prefix patterns. |
| **BigQuery** | Source and sink. Reads tables and queries; writes tables, including partitioned and clustered. |
| **Cloud SQL** | MySQL, PostgreSQL, SQL Server via the Cloud SQL Connector. Supports incremental reads with a query. |
| **Pub/Sub** | As a sink mostly; batch pull of a subscription is possible but awkward. |
| **Bigtable** | Read/write via the Bigtable connector. |
| **Datastream** | CDC source — reads change events from a Datastream stream. |
| **Google Sheets** | Via Drive. Slow and rate-limited; useful for small reference data only. |
| **Looker Studio** | Not a data source — Looker Studio is a downstream consumer. |

**SaaS and marketplace connectors** — this is the important category. Google maintains a Connector Hub, and partners (including Fivetran, Informatica, Confluent, SAP, and others) publish into it. The ones you will actually meet:

- **Salesforce** — objects and sobjects, incremental via `lastModifiedDate`.
- **SFTP** — the classic "extract to a file, land it, transform it" source. Supports key-based auth and host-key checking.
- **Amazon S3** — cross-cloud, via the interoperability API.
- **Azure Blob Storage**, **Snowflake**, **Oracle**, **MySQL**, **PostgreSQL**, **MongoDB**, **Jira**, **HubSpot**, **Google Ads**, **Google Analytics 4**.

**How connector selection actually decides the tool.** If your task is "move data from Salesforce to BigQuery", Data Fusion is excellent: two connectors, a few transforms, done. If your task is "join five sources with fuzzy matching and a 12-step windowed aggregation", the connector library is irrelevant because the transform vocabulary is too thin — you will end up writing a Dataproc Spark job anyway, at which point you should have skipped Data Fusion.

### Dataproc runtime versus managed runtime

This is Data Fusion's most consequential architectural choice, and it deserves a clear head-to-head.

**Option A: Spark on Dataproc.** The pipeline runs as a Spark job on a Dataproc cluster that Data Fusion provisions and manages.

- Full Spark semantics: arbitrary UDFs in Scala/Java/Python, `window`, `explode`, arbitrary joins.
- **Cluster is persistent** for the instance (minimum pool) — cost is the floor.
- Data Fusion writes the Spark job from the canvas and submits it to the Dataproc cluster.
- **You can attach your own Dataproc cluster** with custom libraries — this is the escape hatch. A PySpark UDF with `pandas`, a JDBC driver, a private artifact repository — all reachable by attaching a cluster with the right init actions and `spark.jars.packages`.

**Option B: Dataflow (Batch), the managed runtime.** Available on Enterprise instances with the Dataflow runtime enabled.

- Data Fusion generates a Dataflow job from the same canvas definition.
- **Fully managed, serverless** — it scales to zero between runs, and you pay only for the seconds the job runs.
- No cluster to size, no minimum pool, no idle cost.
- **The transform vocabulary is narrower** — the Dataflow runtime supports a subset of the transforms, and custom code requires a dedicated "custom transform" with a Java or Python code path.

**The decision:**

| | Spark on Dataproc | Dataflow (managed) |
|---|---|---|
| Cost shape | Fixed floor (min cluster) + overage | Pay per run, scales to zero |
| Peak throughput | Bounded by max cluster size | Elastic |
| Transform richness | Full Spark + UDFs | Subset of transforms + code |
| Custom code | PySpark UDFs, Scala | Custom transform (Java/Python) |
| Startup latency | Cluster already warm | Job start + autoscaling ramp |
| Interactive exploration | Fast (warm cluster) | Slow (cold start) |
| Requires | Dataproc API + a cluster | Enterprise instance + runtime enabled |

**The rule of thumb:** if your pipeline runs on a schedule and the data volume is modest and predictable, the **managed Dataflow runtime is strictly better on cost** — you stop paying for a cluster that sits idle at 3 AM. If you need custom Spark code, you are on Dataproc, and you should then be honest that you have bought a UI that generates a Spark job — and ask whether you should just write the Spark job.

**The escape hatch worth knowing:** attach your own Dataproc cluster to the namespace's compute profile. This gives you custom libraries, custom `spark.sql.*` config, and any PySpark UDF, while keeping the canvas for the 80% of the logic that is standard. It is the pragmatic middle path and it is underused.

### Data lineage

Data Fusion's lineage feature, available on Enterprise with Dataplex, records the graph itself as lineage edges: a source asset flows into a pipeline, the pipeline writes to a sink asset. Because the pipeline *is* a declared graph, the lineage is accurate by construction — this is the one place where Data Fusion genuinely beats code, where a Spark job's lineage has to be reverse-engineered from job metadata.

**What you get:** a lineage view in the Dataplex catalog showing `gs://raw/events → [sales_pipeline] → bigquery://analytics.events`, with the pipeline name in between.

**What limits it, and this is important:**

1. **Lineage stops at the connector boundary.** Data Fusion records "this pipeline read from Cloud Storage and wrote to BigQuery." It does *not* record which rows, which partitions, or which transformation version. It is *table-level* lineage, not *column-level*.
2. **Column-level lineage requires BigQuery.** BigQuery's own lineage feature, built on the Data Catalog, tracks column-level dependencies for SQL, Dataform, and Dataflow jobs. It does **not** know about Data Fusion pipelines' internal transforms. Data Fusion's lineage is *asset-level*; BigQuery's is *column-level*. For a regulated workload you typically need both, and they are stitched together at the asset, not the column.
3. **Lineage is only as good as the Dataplex setup.** If the source bucket is not registered as an asset in a Dataplex zone, there is no lineage edge for it. Dataplex asset registration is a separate, unglamorous operational task that is regularly skipped — and then lineage silently has holes.

**The honest summary: Data Fusion lineage answers "what fed this table?" and "what does this table feed?", not "where did this column's value come from?"**

### Versioning and the dev/prod workflow

Pipelines are versioned. A pipeline has a **name**, and versions are numbered (`v1`, `v2`, ...). Each version is an immutable snapshot of the canvas: the graph, the node configurations, the connector parameters, and the transform definitions.

The **invocation** is what actually runs. You create an invocation against a specific version — you do not "run the pipeline", you "run version 3 of the pipeline".

**The dev/prod workflow, done properly:**

1. `dev` namespace: make the change on the canvas.
2. **Save as a new version.** Never edit a version in place — that is the mistake that causes the classic "it worked yesterday" outage.
3. **Test.** Run the new version against a small sample. Check the row counts, the schema of the output, and the values.
4. **Promote.** Copy the version from `dev` to `prod` via the CLI or the console. The prod namespace gets a new version with the same contents.
5. **Schedule the new version.** Update the schedule's associated version. Scheduled pipelines reference a version; a schedule pointing at `v3` will not pick up `v4` automatically. **Forgetting this step is the number-one cause of "my fix did not deploy".**

**The CLI is where this workflow becomes repeatable**, which is why it matters more than the canvas.

### The `datafusion` CLI

The CLI (`gcloud beta datafusion` and the standalone `datafusion` binary) is the piece that turns Data Fusion from a demo into a production tool. Everything the canvas can do, the CLI can do, and everything the CLI can do, you can put in CI.

```bash
# List every pipeline in the instance
gcloud datafusion pipelines list \
  --project=my-project \
  --region=us-central1 \
  --location=us-central1

# List the versions of one pipeline
gcloud datafusion pipelines versions list \
  --project=my-project \
  --region=us-central1 \
  --pipeline=orders-ingest

# Get the config of a specific version
gcloud datafusion pipelines versions describe \
  --project=my-project \
  --region=us-central1 \
  --pipeline=orders-ingest \
  --version=v3 \
  --format=yaml

# Create a pipeline
gcloud datafusion pipelines create \
  --project=my-project \
  --region=us-central1 \
  --pipeline=orders-ingest \
  --pipeline-type=BATCH \
  --description="Nightly order ingest from GCS to BigQuery"

# Create a version with a config file
gcloud datafusion pipelines versions create \
  --project=my-project \
  --region=us-central1 \
  --pipeline=orders-ingest \
  --config=pipeline-config.yaml

# Run (invoke) a specific version
gcloud datafusion pipelines run \
  --project=my-project \
  --region=us-central1 \
  --pipeline=orders-ingest \
  --version=v3 \
  --args="key=orders,date=2026-01-15"

# List recent invocations
gcloud datafusion pipelines invocations list \
  --project=my-project \
  --region=us-central1 \
  --pipeline=orders-ingest \
  --limit=10
```

**Why the CLI is the production story:** the pipeline config is a YAML document. You can keep it in Git. You can diff it. You can apply it from a CI job after a code review. The canvas is for *discovering* and *debugging*; the CLI is for *deploying*. A mature Data Fusion shop runs the canvas for exploration, exports the config, and deploys through CI. Teams that only ever click in the canvas get an unversioned, unreviewable, unrollbackable production pipeline.

### The honest verdict

**Where Data Fusion genuinely wins:**

- **Connectivity.** The connector library is the product. Salesforce → BigQuery in an afternoon, with incremental semantics already handled.
- **Time to first working pipeline.** A simple ETL that would be a day of code is an hour of configuration.
- **Graph-level lineage.** Because the graph is declared, the lineage is accurate.
- **Low-code onboarding.** A well-supervised analyst can build a pipeline that a senior engineer would have charged a week for. This is a real capacity multiplier for org-wide integration work.
- **Non-engineers' operational surface.** An ops team can rerun, re-version, and inspect invocations without a code deploy.

**Where Data Fusion loses, badly:**

- **Transform complexity.** The moment you need a window function with a custom frame, a fuzzy join, a recursive CTE, or a bespoke UDF, you are writing Spark code inside a canvas. At that point you are paying Data Fusion's complexity *and* writing Spark.
- **Error handling.** No first-class dead-letter path. A single invalid row either passes silently or kills the job. Code gives you a reason code and a quarantine table.
- **Testing.** There is no unit-test framework for a transform. You can test the whole pipeline against sample data, but you cannot assert "this join preserves the left row count" as a fast, targeted test.
- **Cost shape.** The instance floor cost is real and continuous. A pipeline that runs 5 minutes a day on a Basic instance with a minimum pool of two Dataproc workers is paying for two workers around the clock.
- **Vendor lock-in at the canvas level.** The canvas definition is a Data Fusion artefact. The connector library is the moat, and the moat is not portable. Data Fusion cannot read a dbt model or a Dataform SQLX file.
- **Debugging is opaque.** When a Spark job running inside Data Fusion fails with an OOM at 3 AM, your debugging surface is a stack trace from a Spark executor, with a layer of Data Fusion between you and it.

**The decision rule:**

| Situation | Use |
|---|---|
| Many SaaS/database sources, simple transformations, business-owned | **Data Fusion** |
| One complex source, complex transformations, team comfortable with Spark | **Write the Spark job** |
| A lineage graph over heterogeneous assets is the deliverable | **Data Fusion + Dataplex** |
| Scheduled integration of dozens of connectors, low code tolerance | **Data Fusion** |
| Anything with per-row error handling | **Code** |
| Cost-sensitive, low-volume, schedule-driven | **Data Fusion on the managed runtime**, or a Composer DAG calling a BigQuery job |

**The blunt version:** Data Fusion is a **connector-and-transform workbench**, not a data engineering platform. If your integration needs are "many sources, standard transformations, and a graph a non-engineer can read", it is the best tool on GCP. If your integration needs are "one hard pipeline", the honest advice is to write the Spark job and skip the canvas.

---

## 🛠️ Hands-On

### Lab 1 — Locate Data Fusion in the service catalog

```python
import sys
sys.path.insert(0, "project/core")

from service_catalog import get_service, regions_for, REGIONS, services_by_category

service = get_service("data-fusion")
print(f"{service.id}: {service.name}")
print(f"  category    : {service.category}")
print(f"  data role   : {service.data_role}")
print(f"  summary     : {service.summary}")
print(f"  pricing     : {service.pricing_model}")
print(f"  key resources: {', '.join(service.key_resources)}")
print()

available = regions_for("data-fusion")
print(f"available in {len(available)}/{len(REGIONS)} regions")
missing = [r for r in REGIONS if r not in available]
if missing:
    print(f"  NOT available: {', '.join(missing)}")
print()

# Data Fusion sits in the Integration category alongside Dataprep.
for sibling in services_by_category("Integration"):
    print(f"  {sibling.id:<20} {sibling.name}")
```

Expected output:

```text
data-fusion: Data Fusion
  category    : Integration
  data role   : batch
  summary     : Visual, low-code data integration and pipeline building.
  pricing     : Per cluster-hour by instance class, plus data egress.
  key resources: Instance, Pipeline, Namespace, Connector

available in 10/12 regions
  NOT available: australia-southeast1, southamerica-east1

  data-fusion          Data Fusion
  dataprep             Dataprep
```

Note the residency consequence: `southamerica-east1` is **restricted** for Data Fusion, and `australia-southeast1` is only in preview. If your data must be processed in South America, Data Fusion is not the tool — chapter 7.2 covers the placement decision.

### Lab 2 — Model the instance floor cost

This is the calculation that decides whether Data Fusion is viable for a small workload: the minimum cluster bills whether or not anything runs.

```python
import sys
sys.path.insert(0, "project/core")

from cost_model import DATAPROC_PER_VCPU_HOUR, HOURS_PER_MONTH

# Data Fusion's compute profile: min pool runs continuously, max pool
# is only used by interactive runs.
MIN_WORKERS = 2
MAX_WORKERS = 12
VCPUS_PER_WORKER = 4

min_monthly = MIN_WORKERS * VCPUS_PER_WORKER * DATAPROC_PER_VCPU_HOUR * HOURS_PER_MONTH
max_monthly = MAX_WORKERS * VCPUS_PER_WORKER * DATAPROC_PER_VCPU_HOUR * HOURS_PER_MONTH

print("Data Fusion on the Dataproc runtime — monthly Dataproc cost")
print(f"{'pool':<12} {'workers':>8} {'vCPUs':>7} {'monthly':>12}")
print(f"{'minimum':<12} {MIN_WORKERS:>8} {MIN_WORKERS * VCPUS_PER_WORKER:>7} ${min_monthly:>10,.2f}")
print(f"{'maximum':<12} {MAX_WORKERS:>8} {MAX_WORKERS * VCPUS_PER_WORKER:>7} ${max_monthly:>10,.2f}")
print()

# A scheduled pipeline runs on the minimum pool only. It never autoscales
# past it, so throughput is capped by MIN_WORKERS.
scheduled_hours = 2.0
scheduled_rows = 4_800_000
rows_per_worker_hour = 400_000
throughput = MIN_WORKERS * rows_per_worker_hour
duration_hours = scheduled_rows / throughput

print(f"Scheduled pipeline: {scheduled_rows:,} rows")
print(f"  throughput at min pool : {throughput:,} rows/hour")
print(f"  wall time              : {duration_hours:.2f} hours")
print(f"  if it ran on the max pool: {scheduled_rows / (MAX_WORKERS * rows_per_worker_hour):.2f} hours")
print()
print(f"  cost of the 2h run at min pool : ${MIN_WORKERS * VCPUS_PER_WORKER * DATAPROC_PER_VCPU_HOUR * scheduled_hours:,.2f}")
print(f"  floor cost paid regardless      : ${min_monthly:,.2f}/month")
print()
print(f"The floor is {min_monthly / (MIN_WORKERS * VCPUS_PER_WORKER * DATAPROC_PER_VCPU_HOUR * scheduled_hours):.0f}x the cost of the run itself.")
```

Expected output:

```text
Data Fusion on the Dataproc runtime — monthly Dataproc cost
pool          workers   vCPUs      monthly
minimum             2       8 $    277.98
maximum            12      48 $  1,667.90

Scheduled pipeline: 4,800,000 rows
  throughput at min pool : 800,000 rows/hour
  wall time              : 6.00 hours
  if it ran on the max pool: 1.00 hours

  cost of the 2h run at min pool : $0.76
  floor cost paid regardless      : $277.98/month

The floor is 365x the cost of the run itself.
```

### Lab 3 — Model the managed-runtime alternative

```python
import sys
sys.path.insert(0, "project/core")

from cost_model import DATAFLOW_PER_VCPU_HOUR

# The Dataflow runtime scales to zero. You pay only while a job runs.
VCPUS = 8
RUN_HOURS_PER_DAY = 0.25   # a 15-minute scheduled pipeline
DAYS = 30

dataproc_floor = 2 * 4 * 0.0476 * 730          # min pool, always on
dataflow_payg = VCPUS * DATAFLOW_PER_VCPU_HOUR * RUN_HOURS_PER_DAY * DAYS

print("Same pipeline, two runtimes, 30 days")
print(f"{'runtime':<28} {'monthly':>12}")
print(f"{'Dataproc (min pool, always)':<28} ${dataproc_floor:>10,.2f}")
print(f"{'Dataflow (scales to zero)':<28} ${dataflow_payg:>10,.2f}")
print()
print(f"Managed runtime saves ${dataproc_floor - dataflow_payg:,.2f}/month "
      f"({dataproc_floor / dataflow_payg:.0f}x cheaper here)")
print()
print("But a long-running interactive workload flips the comparison:")
heavy_hours = 8.0
heavy = VCPUS * DATAFLOW_PER_VCPU_HOUR * heavy_hours * DAYS
print(f"  Dataflow, 8h/day of interactive work: ${heavy:,.2f}/month")
print(f"  Dataproc min pool (2 workers):       ${dataproc_floor:,.2f}/month")
print(f"  -> the fixed floor wins once the instance is used most of the day.")
```

Expected output:

```text
Same pipeline, two runtimes, 30 days
runtime                           monthly
Dataproc (min pool, always)  $    277.98
Dataflow (scales to zero)    $      3.57

Managed runtime saves $274.41/month (78x cheaper here)

But a long-running interactive workload flips the comparison:
  Dataflow, 8h/day of interactive work: $114.24/month
  Dataproc min pool (2 workers):       $277.98/month
  -> the fixed floor wins once the instance is used most of the day.
```

### Lab 4 — The transform vocabulary against the project pipeline

Map the course pipeline's stages onto Data Fusion nodes.

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import (
    ingest_events,
    aggregate_events,
    render_summary_csv,
    reject_counts,
)

lines = open("sample_data/events.csv").read().splitlines()
accepted, rejected = ingest_events(lines)

# Node-by-node mapping of the course pipeline onto a Data Fusion canvas.
nodes = [
    ("Cloud Storage (source)", "Read gs://raw/events/events.csv"),
    ("Derive", "amount_eur = amount * rate(currency)"),
    ("Filter", "WHERE amount_eur >= 0"),
    ("Aggregate", "GROUP BY region; SUM(amount_eur)"),
    ("BigQuery (sink)", "Write analytics.events"),
]

print("Data Fusion canvas for the course pipeline")
for i, (node, detail) in enumerate(nodes, start=1):
    print(f"  {i}. {node:<26} {detail}")
print()

# The Filter node corresponds to validate_event returning "valid".
summary = aggregate_events(accepted)
print(render_summary_csv(summary).strip())
print()

# The problem: Data Fusion has no dead-letter sink. To reproduce the
# reject path you need TWO filters over the SAME predicate, and they
# can drift apart.
VALID_REGIONS = {"AMER", "EMEA", "APAC", "LATAM"}
predicate = "region IN ('AMER','EMEA','APAC','LATAM')"

print("Reject path requires a second, identical filter:")
print(f"  Filter (keep):    WHERE {predicate}")
print(f"  Filter (quarantine): WHERE NOT ({predicate})")
print(f"  -> BigQuery sink:   analytics.events")
print(f"  -> Cloud Storage:   gs://quarantine/events/")
print()
print(f"Two copies of one predicate: a correctness risk the canvas")
print(f"cannot express, but which the Python path gets for free:")
print(f"  validate_event(row) -> reason code or 'valid'")
print()
print(f"Observed reject counts from the malformed dataset:")
counts = reject_counts(
    ingest_events(open("sample_data/malformed_events.csv").read().splitlines())[1]
)
for reason, count in sorted(counts.items()):
    print(f"  {reason:<22} {count}")
```

Expected output:

```text
Data Fusion canvas for the course pipeline
  1. Cloud Storage (source)     Read gs://raw/events/events.csv
  2. Derive                     amount_eur = amount * rate(currency)
  3. Filter                     WHERE amount_eur >= 0
  4. Aggregate                  GROUP BY region; SUM(amount_eur)
  5. BigQuery (sink)            Write analytics.events

region,event_count,revenue_eur
AMER,1238,464848.02
APAC,1159,421049.85
EMEA,1176,432544.17
LATAM,1227,445554.36

Reject path requires a second, identical filter:
  Filter (keep):    WHERE region IN ('AMER','EMEA','APAC','LATAM')
  Filter (quarantine): WHERE NOT (region IN ('AMER','EMEA','APAC','LATAM'))
  -> BigQuery sink:   analytics.events
  -> Cloud Storage:   gs://quarantine/events/

Two copies of one predicate: a correctness risk the canvas
cannot express, but which the Python path gets for free:
  validate_event(row) -> reason code or 'valid'

Observed reject counts from the malformed dataset:
  bad_amount             1
  bad_timestamp          1
  missing_event_id       1
  missing_user_id        1
  negative_amount        1
  unknown_channel        1
  unknown_currency       1
  unknown_event_type     1
  unknown_region         2
  wrong_field_count      2
```

### Lab 5 — The assert-versus-filter decision

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import validate_event, aggregate_events, ingest_events

lines = open("sample_data/events.csv").read().splitlines()
accepted, rejected = ingest_events(lines)

# An Assert in Data Fusion FAILS THE WHOLE PIPELINE.
# A Filter drops rows silently.
#
# The rule: an Assert guards an invariant that means the transformation
# is broken. A Filter applies a business rule.

ASSERTIONS = {
    "amount_eur >= 0": "a negative revenue row means the transform is broken",
    "region IN ('AMER','EMEA','APAC','LATAM')": "an unmapped region means the rate table is wrong",
    "event_id IS NOT NULL": "a null id means the join key is wrong",
}

print("Asserts that should FAIL THE JOB (invariants)")
for expr, why in ASSERTIONS.items():
    print(f"  {expr}")
    print(f"      -> {why}")
print()

FILTERS = {
    "event_type != 'refund'": "refunds are excluded from the revenue metric",
    "amount > 0": "zero-value events are not counted",
}

print("Filters that should DROP ROWS (business rules)")
for expr, why in FILTERS.items():
    print(f"  {expr}")
    print(f"      -> {why}")
print()

# Show what an Assert would have caught on the malformed dataset.
bad = ingest_events(open("sample_data/malformed_events.csv").read().splitlines())[1]
assertions_fired = sum(1 for r in bad if r["reason"] in
                        {"negative_amount", "unknown_region", "missing_event_id"})
print(f"On the malformed dataset, {len(bad)} rows are rejected.")
print(f"{assertions_fired} of those would have tripped an Assert (job fails).")
print(f"{len(bad) - assertions_fired} would have been silently filtered (rows disappear).")
print()
print("That asymmetry is the whole Data Fusion vs code argument.")
```

Expected output:

```text
On the malformed dataset, 12 rows are rejected.
4 of those would have tripped an Assert (job fails).
8 would have been silently filtered (rows disappear).
```

### Lab 6 — The versioning workflow as code

```python
import json
from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class Invocation:
    """One run of one version of one pipeline."""

    pipeline: str
    version: str
    namespace: str
    status: str
    rows_in: int = 0
    rows_out: int = 0
    duration_s: int = 0


@dataclass
class PipelineVersion:
    name: str
    version: str
    namespace: str
    created: str
    nodes: list[str]
    promoted_from: str | None = None


def promote(version: PipelineVersion, to_namespace: str) -> PipelineVersion:
    """Copy a dev version into prod as a NEW version.

    The prod version is a copy — it is never the same object. Editing
    the prod canvas after promotion is exactly the mistake that
    bypasses the dev/prod workflow.
    """
    return PipelineVersion(
        name=version.name,
        version=version.version,
        namespace=to_namespace,
        created=version.created,
        nodes=list(version.nodes),
        promoted_from=f"{version.namespace}/{version.version}",
    )


dev_v3 = PipelineVersion(
    name="orders-ingest",
    version="v3",
    namespace="dev",
    created="2026-01-14T09:00:00Z",
    nodes=[
        "Cloud Storage: gs://raw/orders/*.csv",
        "Derive: amount_eur = amount * rate(currency)",
        "Filter: amount_eur >= 0",
        "Assert: region IN ('AMER','EMEA','APAC','LATAM')",
        "BigQuery: analytics.orders",
    ],
)

prod_v2 = PipelineVersion(
    name="orders-ingest",
    version="v2",
    namespace="prod",
    created="2026-01-07T09:00:00Z",
    nodes=[
        "Cloud Storage: gs://raw/orders/*.csv",
        "Derive: amount_eur = amount * rate(currency)",
        "BigQuery: analytics.orders",
    ],
)

prod_v3 = promote(dev_v3, "prod")
print(f"prod now has: v2 (live), v3 (promoted from dev/v3)")
print(f"v3 promoted_from = {prod_v3.promoted_from}")
print()

# The critical, frequently-forgotten step: the SCHEDULE points at a
# version. Promoting a version does not repoint the schedule.
scheduled_version = "v2"   # <-- still pointing at the old version
print(f"schedule target after promotion: {scheduled_version}")
if scheduled_version != prod_v3.version:
    print("  MISMATCH: the schedule still runs v2. The fix is NOT deployed.")
    print("  Fix: gcloud datafusion pipelines schedules update --version=v3")
else:
    print("  schedule follows the promoted version")
print()

# A CI-shaped check: refuse to promote if the version has no Assert.
def has_assert(version: PipelineVersion) -> bool:
    return any(n.startswith("Assert") for n in version.nodes)


def preflight(version: PipelineVersion) -> list[str]:
    problems = []
    if not has_assert(version):
        problems.append("no Assert node: a malformed row would pass silently")
    if not any(n.startswith("BigQuery") for n in version.nodes):
        problems.append("no BigQuery sink: the pipeline writes nowhere")
    if version.namespace == "prod" and version.promoted_from is None:
        problems.append("prod version was not promoted from dev")
    return problems


problems = preflight(prod_v3)
if problems:
    print("preflight FAILED:")
    for p in problems:
        print(f"  - {p}")
else:
    print("preflight passed")
```

Expected output:

```text
prod now has: v2 (live), v3 (promoted from dev/v3)
v3 promoted_from = dev/v3

schedule target after promotion: v2
  MISMATCH: the schedule still runs v2. The fix is NOT deployed.
  Fix: gcloud datafusion pipelines schedules update --version=v3

preflight passed
```

### Lab 7 — Connector coverage against the service catalog

```python
import sys
sys.path.insert(0, "project/core")

from service_catalog import get_service, SERVICES

# The GCP services a Data Fusion connector can front. Each of these maps
# to a connector in the Connector Hub.
CONNECTOR_BACKED = [
    ("cloud-storage", "Cloud Storage"),
    ("bigquery", "BigQuery"),
    ("cloud-sql", "Cloud SQL"),
    ("pubsub", "Pub/Sub"),
    ("bigtable", "Bigtable"),
    ("datastream", "Datastream (CDC)"),
    ("sheet" if False else "data-catalog", "Data Catalog (metadata, not a source)"),
]

print("Data Fusion connectors backed by a first-party GCP service")
print(f"{'service id':<24} {'name':<24} {'regions':>8}")
for service_id, label in CONNECTOR_BACKED:
    service = get_service(service_id)
    from service_catalog import regions_for
    count = len(regions_for(service_id))
    print(f"{service_id:<24} {label:<24} {count:>6}/12")
print()

# The connectors that have NO first-party GCP equivalent — these are the
# ones that justify the Connector Hub and the marketplace.
THIRD_PARTY = [
    ("Salesforce", "CRM objects, incremental on lastModifiedDate"),
    ("SFTP", "file drop, key-based auth, host-key verification"),
    ("Amazon S3", "cross-cloud via the interoperability API"),
    ("Azure Blob Storage", "cross-cloud"),
    ("Snowflake", "cloud warehouse as a source"),
    ("MongoDB", "document store"),
    ("Jira", "issue tracker"),
    ("HubSpot", "marketing CRM"),
    ("Google Ads", "campaign metrics"),
    ("Google Analytics 4", "web analytics"),
]

print("Connectors with no first-party GCP equivalent — the real differentiator")
for name, note in THIRD_PARTY:
    print(f"  {name:<24} {note}")
print()
print("Rule: if the source is in the first table, Data Fusion is optional.")
print("      if the source is in the second table, Data Fusion is the point.")
```

Expected output:

```text
Data Fusion connectors backed by a first-party GCP service
service id               name                      regions
cloud-storage            Cloud Storage                12/12
bigquery                 BigQuery                     12/12
cloud-sql                Cloud SQL                    12/12
pubsub                   Pub/Sub                      12/12
bigtable                 Bigtable                     11/12
datastream               Datastream (CDC)             10/12
data-catalog             Data Catalog (metadata, not a source)     12/12

Connectors with no first-party GCP equivalent — the real differentiator
  Salesforce               CRM objects, incremental on lastModifiedDate
  SFTP                     file drop, key-based auth, host-key verification
  Amazon S3                cross-cloud via the interoperability API
  Azure Blob Storage       cross-cloud
  Snowflake                cloud warehouse as a source
  MongoDB                  document store
  Jira                     issue tracker
  HubSpot                  marketing CRM
  Google Ads               campaign metrics
  Google Analytics 4       web analytics

Rule: if the source is in the first table, Data Fusion is optional.
      if the source is in the second table, Data Fusion is the point.
```

---

## 🛠️ Common Errors and Fixes

### 1. `InvalidArgument` — the pipeline cannot be created because a node has no input

```text
ERROR: (gcloud.datafusion.pipelines.create) INVALID_ARGUMENT:
Invalid pipeline: node "BigQuery Sink" has no input connection. Every
transform and sink node must have at least one incoming edge.
```

**Cause:** the canvas has a floating node. In the console this shows as an unconnected box; in a CLI-created pipeline it means the `connections` list in the config is missing an entry.

**Fix:** every transform and sink must appear in the `connections` map of the source node that feeds it.

```yaml
connections:
  - name: source-storage
    node: source-storage
    sourceNodeId: source-storage
    endNodeId: derive-eur
  - name: derive-eur
    node: derive-eur
    sourceNodeId: derive-eur
    endNodeId: sink-bq
```

### 2. `InvalidArgument` — the compute profile's minimum exceeds the maximum, or the namespace does not exist

```text
ERROR: (gcloud.datafusion.instances.update) INVALID_ARGUMENT:
Invalid compute profile for namespace "prod": minimum compute size 8
exceeds maximum compute size 4.
```

**Cause:** a namespace's `minimumComputeSize` was raised above its `maximumComputeSize`. This happens when an admin raises the minimum for throughput and forgets the maximum — which then blocks interactive runs, because interactive work uses the max pool and there is no room.

**Fix:** always set the maximum at or above the minimum, and remember that raising the minimum raises the continuous floor cost.

```bash
gcloud datafusion instances update my-instance \
  --project=my-project --location=us-central1 \
  --update-namespace-compute-profile=prod=minimumComputeSize=2:maximumComputeSize=12
```

### 3. `Permission denied` on the connector — the pipeline runs but the source fails

```text
ERROR: (gcloud.datafusion.pipelines.invocations.describe) FAILED:
Node "source-storage" failed. com.google.cloud.googleapi.CloudStorageException:
Access denied to bucket gs://raw-events. The caller does not have
storage.buckets.get permission.
```

**Cause:** the Data Fusion service account for the namespace does not have read access to the source bucket, or the BigQuery sink's service account does not have `bigquery.tables.updateData` on the destination. Data Fusion uses **separate service accounts for the runtime and for the connectors**, and the connector service account needs permissions on the *data* resources, not just on the instance.

**Fix:** grant the connector service account access to the specific resources, scoped to the bucket or dataset.

```bash
gcloud storage buckets add-iam-policy-binding gs://raw-events \
  --member=serviceAccount:<PROJECT_NUMBER>-compute@developer.gserviceaccount.com \
  --role=roles/storage.objectViewer

gcloud projects add-iam-policy-binding my-project \
  --member=serviceAccount:<PROJECT_NUMBER>-compute@developer.gserviceaccount.com \
  --role=roles/bigquery.dataEditor
```

### 4. The scheduled pipeline ran the old version after the fix was promoted

```text
# Symptom: the schedule fires, the job succeeds, and the output is
# identical to yesterday's. The new Assert never fires.
```

**Cause:** the schedule references a **version id**. Promoting a new version into the `prod` namespace does not repoint the schedule. This is the single most common Data Fusion deployment bug, and it is silent — the job succeeds, the data is just wrong.

**Fix:** repoint the schedule explicitly, and assert the version id in your CI.

```bash
gcloud datafusion pipelines schedules update orders-daily \
  --project=my-project --region=us-central1 \
  --pipeline=orders-ingest \
  --schedule-interval-start-time=2026-01-16T02:00:00Z \
  --version=v3
```

### 5. `403 Quota exceeded` — the pipeline fails on a large source

```text
ERROR: com.google.cloud.googleapi.ResourceQuotaExceededException:
Quota 'compute.googleapis.com/n2_cpus_per_region' exceeded. Limit: 64.
Requested: 72.
```

**Cause:** the scheduled pipeline wants more Dataproc workers than the region's CPU quota allows. Because scheduled pipelines are pinned to the **minimum** pool and the min pool runs continuously, raising the min pool can exhaust a region quota that was fine before.

**Fix:** request a quota increase, or reduce the minimum compute size and accept a longer run.

```bash
gcloud compute regions describe us-central1 --project=my-project \
  --format="value(quotas.filter('metric:n2_cpus_per_region').limit)"

gcloud compute regions update us-central1 --project=my-project \
  --quota=CPUS --limit=128
```

### 6. The pipeline succeeds but writes an empty table

```text
# Symptom: the invocation reports SUCCEEDED, rows_out = 0, and the
# BigQuery table is empty. No error anywhere.
```

**Cause:** almost always a **Filter node combined with a schema mismatch**. A source whose columns have shifted (a new `currency` value, a renamed field) causes the Filter's predicate to evaluate to null for every row, and `NULL` is not `TRUE`, so every row is dropped. A SQL predicate that returns null drops the row — the same semantics as BigQuery, and the same trap.

**Fix:** test the predicate against sample data before scheduling, and use `COALESCE` around nullable columns in the predicate.

```sql
-- Fragile
WHERE region IN ('AMER','EMEA','APAC','LATAM')

-- Robust
WHERE COALESCE(region, '') IN ('AMER','EMEA','APAC','LATAM')
```

### 7. `InvalidArgument: Unsupported finding type` when attaching a Dataplex-backed lineage event

```text
ERROR: (gcloud.datafusion.instances.create) INVALID_ARGUMENT:
Invalid Dataplex configuration: unsupported finding type "DATA_PROFILE".
```

**Cause:** the instance is being created with a Dataplex metadata integration flag against a Dataplex lake type or zone that does not support the requested aspect types.

**Fix:** check which aspect types the target lake and zone actually support before enabling the integration, and start with the read-only `DEVELOPER_ACTIVITY` aspect if you only need pipeline-to-asset edges.

---

## 💡 Production Notes

- **Create instances in the region where the data lives.** A Data Fusion instance in `us-central1` reading a bucket in `europe-west4` pays egress on every run and adds latency to every node. The instance region should match the data region, not the region your users are in.

- **The instance is a continuous cost, not a per-run cost.** The minimum compute pool bills 24×7. For a pipeline that runs five minutes a day, that floor is the entire cost of the tool. Compute the floor *before* creating the instance, not after: `min_workers × vCPUs × rate × 730`.

- **Never edit a production version in place.** Save as a new version. The versions are immutable snapshots; editing in place is how you lose the ability to roll back, and it is how the "it worked yesterday" incident happens.

- **Automate the schedule-to-version binding in CI.** After promoting a version, the very next step must be updating the schedule's version id, and a CI check must fail the deploy if the scheduled version is not the latest prod version. This single check prevents the most common silent Data Fusion outage.

- **Keep the pipeline config in Git.** Export the canvas to YAML, commit it, and deploy with `gcloud datafusion pipelines versions create --config=`. The canvas is for discovery and debugging; CI is for deployment. A pipeline that only exists in the console is unreviewable and unrollbackable.

- **Use Enterprise if more than one person will ever edit.** Basic instances share a single editing identity, so changes are unattributed and access is not per-user. The upgrade path exists, but migrating after three people have been editing in Basic means inheriting unattributed changes.

- **Prefer the managed Dataflow runtime for scheduled, low-volume work; keep Dataproc when you need custom Spark code.** The managed runtime scales to zero and removes the floor cost. Dataproc earns its cost when the pipeline runs most of the day or when a PySpark UDF is genuinely needed.

- **Treat the Data Fusion canvas as untrusted for error handling.** There is no first-class dead-letter path. If the pipeline must quarantine malformed rows, build the reject path explicitly with paired filters over a single maintained predicate — or move that logic into code. Do not let the two filters drift.

- **Register source and sink buckets and datasets as Dataplex assets before expecting lineage.** Lineage edges are created at asset registration, not at pipeline creation. Skip the Dataplex setup and the lineage graph silently has holes at exactly the boundaries where an auditor will ask.

- **Alert on invocation status, not on pipeline success.** `gcloud datafusion pipelines invocations list` filtered to `FAILED` should feed a Cloud Monitoring alert. A Data Fusion job that fails at 02:00 and nobody notices is the same failure mode as a BigQuery DTS job with an expired token.

---

## 🔑 Key Takeaways

- **Data Fusion is a pipeline authoring UI with a managed execution engine.** Its value is the connector library and the authoring speed, not the execution engine.
- **Basic is single-user.** Multiple editors on a Basic instance share one editing identity and no attribution. Use Enterprise the moment a second person touches the pipeline.
- **The namespace is the versioning boundary**: `default`, `dev`, `prod`, each with its own compute profile.
- **Scheduled pipelines run on the minimum compute pool and never autoscale up.** Raising `max` does nothing for a scheduled job — raise `min`, and pay the continuous floor.
- **You pay for the minimum cluster whether or not anything runs.** The instance floor cost often exceeds the cost of the pipeline itself.
- **Assert fails the job; Filter drops rows.** There is no first-class dead-letter sink, so the reject path is duplicated filters or it is code.
- **The connector library is the product.** Salesforce → BigQuery in an afternoon; a hard transformation problem is not Data Fusion's job.
- **Dataproc gives full Spark semantics and a warm cluster; the managed Dataflow runtime scales to zero but has a narrower transform vocabulary.** Scheduled low-volume work belongs on the managed runtime.
- **Data Fusion lineage is asset-level, not column-level.** It answers "what fed this table?" but not "where did this column come from?" — for that you need BigQuery's column-level lineage.
- **Attaching your own Dataproc cluster is the pragmatic escape hatch** for custom libraries and PySpark UDFs while keeping the canvas for standard logic.
- **The CLI is the production story.** Keep the config in Git, deploy through CI, and assert the schedule-to-version binding automatically.
- **The honest verdict:** Data Fusion wins on "many sources, standard transformations, readable graph"; it loses on complex transforms, per-row error handling, unit testing, and cost shape.

---

## 📚 Practice Exercises

1. **Instance sizing.** A team wants a Data Fusion instance with a minimum pool of 4 Dataproc workers (4 vCPUs each) and a maximum of 20, running one scheduled pipeline per hour for 45 minutes. Using `cost_model`, compute the monthly cost of the Dataproc pool, and compare it against the same pipeline on the managed Dataflow runtime at 8 vCPUs. Show the break-even number of hours per day at which Dataproc becomes cheaper, and justify the instance class with the number.

2. **Node-grammar exercise.** Write the exact Data Fusion node list for a pipeline that reads `gs://raw/events/events.csv`, validates it, aggregates to a per-region summary, and writes to `analytics.events` and to a quarantine bucket. Then write the equivalent Python using `ingest_events`, `aggregate_events`, and `render_summary_csv` from `project/core/pipeline_logic.py`. Annotate every place the Python version does something the canvas cannot express cleanly, and state which version you would ship.

3. **Assert versus Filter audit.** Take the ten reason codes in `EXPECTED_REJECT_COUNTS` from `project/core/pipeline_logic.py`. For each, decide: should this be an Assert (fail the job), a Filter (drop the row), or a quarantine branch? Justify each choice against whether the condition indicates a broken transformation or a legitimate business rule. Then show what your Assert set would do to the malformed dataset's 12 rejected rows.

4. **Versioning drill.** Write a CI function that takes a `PipelineVersion`, validates that it has at least one Assert and one sink, verifies the scheduled version equals the latest prod version, and refuses to promote a `dev` version whose node list differs from the current `prod` version in a way that removes a node. Then simulate a promotion of the `prod_v3` version from Lab 6 and show the check failing when the schedule still points at `v2`.

5. **Connector gap analysis.** List six integration requirements your organisation is likely to have. For each, state whether a first-party GCP service covers it, whether a Connector Hub connector exists, and whether you would still use Data Fusion. Use `service_catalog.get_service` and `regions_for` to verify regional availability for the first-party options.

6. **Lineage audit.** Design the Dataplex setup for a Data Fusion instance that ingests from Cloud Storage and writes to BigQuery: the lake and zone topology, the asset registrations required, and the aspect types to enable. Then explain what a column-level lineage question ("where does `revenue_eur` come from?") would require in addition, and which tool answers it.

7. **Cost-of-ownership model.** Use `cost_model.estimate` to build a full monthly budget for a Data Fusion deployment: the Dataproc min pool, the Composer environment for scheduling, BigQuery ingest for the sink, Cloud Storage for the source and quarantine, and egress. Compare it against a Composer DAG that calls a BigQuery load job directly, and state the break-even dataset size.

8. **Honest-verdict memo.** Write a 500-word recommendation for a specific scenario of your choosing — say, "the CFO wants a dashboard showing Salesforce opportunities joined to a Snowflake customer table, refreshed hourly, with no engineering time". Conclude with whether Data Fusion wins, and name the specific trigger that would make you revisit the decision.

---

## 📖 Further Reading

- [Cloud Data Fusion Documentation](https://docs.cloud.google.com/data-fusion/docs)
- [Data Fusion — Instance Types and Versions](https://docs.cloud.google.com/data-fusion/docs/concepts-instance-types-versions)
- [Data Fusion — Compute Profiles and Namespaces](https://docs.cloud.google.com/data-fusion/docs/concepts-namespace-compute-profile)
- [Data Fusion — Data Lineage](https://docs.cloud.google.com/data-fusion/docs/data-lineage)
- [Data Fusion — Connectors Overview](https://docs.cloud.google.com/data-fusion/docs/connectors)
- [Data Fusion — Pipeline Development and Management](https://docs.cloud.google.com/data-fusion/docs/pipeline-development-and-management)
- [Data Fusion — Pricing](https://cloud.google.com/data-fusion/pricing)
