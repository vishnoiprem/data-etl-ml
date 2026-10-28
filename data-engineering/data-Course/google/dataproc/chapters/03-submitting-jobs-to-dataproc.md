# 1.3 — Submitting Jobs to Dataproc

> **Section 1 · Foundations · Lecture 1.3 · 5:48**

## 🎯 What you will learn

- The `gcloud dataproc jobs submit` command and its subcommands: `pyspark`, `spark`, `spark-sql`
- How to package dependencies: `--jars`, `--py-files`, `--files`, `--archives`, and `--properties`
- The `--` separator, and why getting it wrong produces a baffling error
- Job states in the Dataproc API — and how they differ from the labels you see in the console
- Where driver logs live and how to pull them with `gcloud dataproc jobs describe` and Cloud Logging
- Three ways to get an interactive session: Jupyter, SSH, and Spark Connect
- The cluster metadata server, and how to read cluster details from inside a driver
- Auto Zone placement, and what happens when you omit `--zone`

---

## 🧠 Concept

Cluster creation was the setup. Now we actually run code. There are two fundamentally
different ways to run a Spark program on a Dataproc cluster, and confusing them is the
source of most beginner frustration.

```
   ┌──────────────────────────────────────────────────────────────┐
   │                                                              │
   │   JOB SUBMISSION (batch)                                     │
   │                                                              │
   │   gcloud dataproc jobs submit pyspark main.py ...            │
   │        │                                                     │
   │        ├──► gcloud uploads main.py + deps to staging bucket │
   │        ├──► Dataproc Jobs API creates a job resource        │
   │        ├──► Agent on master launches spark-submit           │
   │        ├──► Driver runs on master, executors on workers     │
   │        ├──► stdout/stderr captured → driverOutputUri        │
   │        └──► Job ends in DONE or ERROR. Cluster persists.    │
   │                                                              │
   │   No session survives the job. Reproducible. Auditable.     │
   └──────────────────────────────────────────────────────────────┘

   ┌──────────────────────────────────────────────────────────────┐
   │                                                              │
   │   INTERACTIVE SESSION                                        │
   │                                                              │
   │   Jupyter / SSH / Spark Connect                              │
   │        │                                                     │
   │        ├──► Long-lived session attached to the cluster      │
   │        ├──► You type, it runs, state persists               │
   │        ├──► Session dies when you disconnect                │
   │        └──► Cluster persists. State is ephemeral.           │
   │                                                              │
   │   Fast feedback. Non-reproducible. Exploratory.              │
   └──────────────────────────────────────────────────────────────┘
```

| | Job submission | Interactive session |
|---|---|---|
| **Reproducible?** | ✅ Yes — the exact command is the artifact | ❌ No — you have to remember what you did |
| **Auditable?** | ✅ Every job is an API resource with logs | ❌ Only the cluster's console output |
| **Cost** | Billed per job | Billed for the whole session |
| **Good for** | Production pipelines, scheduled ETL | Development, exploration, teaching |
| **Failure mode** | Job fails, cluster survives | Session dies, you lose uncommitted work |

💡 **The rule for this course:** develop interactively, ship by submission. Every piece of
production code in this course is submitted with `gcloud dataproc jobs submit`.

---

## The command

The current, correct command is:

```bash
gcloud dataproc jobs submit SUBCOMMAND --cluster=CLUSTER [flags] -- [args to driver]
```

The available subcommands are:

| Subcommand | Runs | Main class / file | Requires |
|------------|------|-------------------|----------|
| `pyspark` | A PySpark driver | A `.py` file (local or `gs://`) | — |
| `spark` | A Spark Java/Scala driver | `--class` + `--jar`, or `--jar` alone | `--class` or `--jar` |
| `spark-sql` | Spark SQL statements | A `.sql` file | — |
| `hadoop` | A MapReduce job | `--jar` | — |
| `hive` | Hive queries | `--file` | — |
| `pig` | A Pig script | `--file` | — |
| `presto` / `trino` | A Presto/Trino query | `--file` | — |
| `flink` | A Flink job | `--jar` | — |

⚠️ **The command is `gcloud dataproc jobs submit`, not `gcloud dataproc clusters
submit`.** The older `gcloud dataproc clusters submit ...` form was the shape of the CLI
for years and still appears in most tutorials, Stack Overflow answers, and AI-generated
code. It has been superseded by `gcloud dataproc jobs submit`. Always check
`gcloud dataproc jobs submit --help` for the current surface.

### The `--` separator

The single most important syntactic rule:

```bash
gcloud dataproc jobs submit pyspark --cluster=my-cluster --jars=gs://b/lib.jar -- main.py arg1 arg2
                                                               ▲
                                                    everything after this goes to YOUR program
```

```
   gcloud flags        │   your script + its arguments
   ────────────────────┼────────────────────────────────
   --cluster=...       │
   --jars=...          │
   --properties=...    │
                       ▼
                    main.py  arg1  arg2
```

⚠️ **Omitting `--` is the most common submission error.** Without it, gcloud tries to
interpret `main.py` as a flag and fails with something like `ERROR: (gcloud.dataproc.jobs.submit.pyspark)
unrecognized arguments: main.py`. Conversely, putting `--` too early means your flags are
passed to the driver instead of gcloud, and your driver gets a wall of `--cluster=...`
arguments it does not understand.

Two positional orders are both accepted:

```bash
# Script before the cluster flag
gcloud dataproc jobs submit pyspark main.py --cluster=my-cluster -- arg1

# Script after the cluster flag
gcloud dataproc jobs submit pyspark --cluster=my-cluster main.py -- arg1
```

💡 **Put the script path first and the `--` last.** It reads cleanly and makes the
boundary obvious.

### The four ways to get code onto the cluster

```
   ┌──────────────┐   --jars      ┌───────────────────────────┐
   │  your JARs   │──────────────▶│                           │
   └──────────────┘                │                           │
   ┌──────────────┐   --py-files   │      Spark classpath      │
   │  your .py /  │──────────────▶│      + working dir       │
   │  .zip / .egg │                │                           │
   └──────────────┘                │   driver + executors      │
   ┌──────────────┐   --files      │   see the same layout     │
   │  config,     │──────────────▶│                           │
   │  data, CSV   │                └───────────────────────────┘
   ┌──────────────┐   --archives
   │  .zip/.tar.gz│──────────────▶  extracted into the working dir
   └──────────────┘
```

| Flag | Accepts | Lands in | Use for |
|------|---------|----------|---------|
| `--jars` | Comma-separated JAR URIs | Driver + executor classpath | Java/Scala libraries, JDBC connectors |
| `--py-files` | `.py`, `.zip`, `.egg` | Added to `sys.path` | Your own helper modules, packaged deps |
| `--files` | Any file | Working directory | Config files, small lookup CSVs |
| `--archives` | `.zip`, `.tar`, `.tar.gz`, `.tgz` | Extracted into working dir | Bundled code + data |

All four accept both local paths and `gs://` URIs. Local paths are uploaded to the
cluster's staging bucket automatically.

⚠️ **`--py-files` accepts `.py`, `.zip`, and `.egg` — and `.egg` is a dead format.** Modern
Python packaging means you should ship a wheel's contents as a zip, or (much better)
install dependencies in an initialization action or use a custom image. If you find
yourself fighting with `--py-files`, the answer is almost always "use an initialization
action" or "use a custom image", not "add another flag".

💡 **`--files` is for small files only.** Anything you put in `--files` is copied to every
executor. A 500 MB CSV in `--files` means 500 MB × N executors of staging traffic on every
job launch. Put bulk data in GCS and read it with a `gs://` path in your code.

### `--properties` vs `--properties-file`

`--properties` sets Spark configuration for **this job only**, in plain
`key=value` form (no `spark:` prefix — that prefix is for *cluster* properties).

```bash
gcloud dataproc jobs submit pyspark main.py \
  --cluster=my-cluster \
  --properties="spark.executor.memory=8g,spark.executor.cores=2,spark.sql.shuffle.partitions=400"
```

`--properties-file` reads the same thing from a file, which is far better for anything
non-trivial:

```bash
# spark.properties
spark.executor.memory=8g
spark.executor.cores=2
spark.executor.instances=20
spark.sql.shuffle.partitions=400
spark.sql.adaptive.enabled=true
spark.serializer=org.apache.spark.serializer.KryoSerializer
spark.dynamicAllocation.enabled=true
spark.dynamicAllocation.maxExecutors=50
```

```bash
gcloud dataproc jobs submit pyspark main.py \
  --cluster=my-cluster \
  --properties-file=spark.properties
```

⚠️ **If a property is set in both, `--properties` wins.** This is stated explicitly in the
gcloud reference — a common source of "why isn't my property taking effect?" confusion.

### The Spark configuration that actually matters

| Property | Why it matters |
|----------|----------------|
| `spark.executor.instances` | Number of executors. **Set this.** If unset, Spark defaults to 1 executor regardless of cluster size — a classic "my 50-node cluster runs as fast as 1 node" bug. |
| `spark.executor.memory` | Per-executor heap. |
| `spark.executor.cores` | vCPUs per executor. 4–5 is the sweet spot; more means worse GC. |
| `spark.sql.shuffle.partitions` | Number of output partitions after a shuffle. Defaults to 200 — too few for big data, too many for small data. |
| `spark.sql.adaptive.enabled` | AQE — coalesces shuffle partitions automatically. Enable it. |
| `spark.sql.adaptive.skewJoin.enabled` | AQE skew handling — fixes the "one task takes 10× longer" problem. |
| `spark.dynamicAllocation.enabled` | Scale executors with demand. Requires `spark.executor.instances` to be unset. |
| `spark.serializer` | `KryoSerializer` is faster than Java serialization. |
| `spark.sql.parquet.outputTimestampType` | Write `INT96` instead of `INT64` timestamps for Hive compatibility. |

💡 **Dynamic allocation and autoscaling are two different things.** Dataproc's
`--autoscaling-policy` scales *worker VMs*. Spark's `spark.dynamicAllocation` scales
*executors* within those VMs. You can use either, both, or neither. If you use Dataproc
autoscaling, leave `spark.executor.instances` unset and let Spark decide how many
executors to run per worker.

⚠️ **Setting `spark.executor.instances` disables dynamic allocation.** If you set both,
the explicit count wins and you have turned off the elasticity you thought you enabled.

### `--driver-python-version`

Dataproc 2.2 image ships **Python 3** by default. The flag exists for the cases where you
need an explicit version or a Conda environment:

```bash
gcloud dataproc jobs submit pyspark main.py \
  --cluster=my-cluster \
  --driver-python-version=3.11
```

⚠️ **`--driver-python-version` is not a pyspark-submit flag.** You may see
`--driver-python-version` used with `spark-submit` directly (where it does exist), but
the `gcloud dataproc jobs submit pyspark` surface does **not** expose it. If you need to
control the Python version, the right lever is the **cluster image version** and
**cluster properties** (`dataproc:conda.python-version` for Conda-based images), set at
cluster creation time — not a per-job flag.

---

## Job states: the API truth

Dataproc's `JobStatus.state` is an enum with ten values. These are the **API** states,
which is what `gcloud dataproc jobs describe` and the REST API return:

| State | Meaning |
|-------|---------|
| `STATE_UNSPECIFIED` | The job state is unknown. |
| `PENDING` | Submitted, not yet running. |
| `SETUP_DONE` | Received by the service, initial setup complete; will soon be submitted to the cluster. |
| `RUNNING` | Running on the cluster. |
| `CANCEL_PENDING` | A cancel request has been received but is pending. |
| `CANCEL_STARTED` | Transient resources canceled; the cancel has been issued to the cluster. |
| `CANCELLED` | Cancellation succeeded. |
| **`DONE`** | **Completed successfully.** |
| **`ERROR`** | **Completed with an error.** |
| `ATTEMPT_FAILURE` | This attempt failed (restartable jobs only). The `details` field has the specifics. |

There is also a `substate`, which refines `RUNNING`:

| Substate | Meaning |
|----------|---------|
| `UNSPECIFIED` | Unknown. |
| `SUBMITTED` | The job has been submitted to the agent. |
| `QUEUED` | Received and awaiting execution (waiting on a condition). The `details` field says why. |
| `STALE_STATUS` | The agent's reported status is out of date — usually a communication loss between agent and Dataproc. |

⚠️ **The console labels differ from the API enum.** In the Google Cloud console you will
see **"Running", "Succeeded", "Failed", "Cancelled", "Pending"**. Those map onto the API
as:

| Console label | API `status.state` |
|---------------|--------------------|
| Pending | `PENDING` |
| Running | `RUNNING` |
| Succeeded | `DONE` |
| Failed | `ERROR` |
| Cancelled | `CANCELLED` |

So there is **no `SUCCEEDED` state in the API** — success is `DONE`. And there is **no
`FAILED` state** — failure is `ERROR`. If you write automation that checks
`state == "SUCCEEDED"` or `state == "FAILED"`, it will never match. This trips up
people who learned the console labels first and then wrote a script.

```bash
# The reliable way to check job outcome in a script
gcloud dataproc jobs describe JOB_ID --region=us-central1 \
  --format="value(status.state)"      # → DONE / ERROR / CANCELLED

# Exit code reflects success
gcloud dataproc jobs wait JOB_ID --region=us-central1
echo "exit code: $?"                   # 0 on success, non-zero on failure
```

💡 **Use `gcloud dataproc jobs wait` in scripts, not a polling loop.** It blocks until the
job reaches a terminal state and returns a proper exit code, so it composes correctly with
`set -e` in a shell script.

### Job concurrency

A cluster has a limit on concurrent jobs:

```
  max( (masterMemoryMb - 3584) / masterMemoryMbPerJob , 5 )
```

With `masterMemoryMb` from the master's machine type and `masterMemoryMbPerJob = 1024` by
default. You can override it with the cluster property
`dataproc:dataproc.scheduler.max-concurrent-jobs`, and the per-job driver size with
`dataproc:dataproc.scheduler.driver-size-mb`.

⚠️ **Submitting jobs in a tight loop can cause a race condition and job failures.** Space
submissions out by at least a fraction of a second. If you are launching 50 jobs from a
script, add a small sleep between them.

---

## Reading the logs

Every submitted job produces a `driverOutputUri` pointing at its captured stdout/stderr
in the staging bucket:

```text
gs://<staging-bucket>/google-cloud-dataproc-metainfo/<job-id>/<driver-id>/
```

### Via gcloud

```bash
# Wait for completion and print driver output
gcloud dataproc jobs wait JOB_ID --region=us-central1

# Full job resource as JSON
gcloud dataproc jobs describe JOB_ID --region=us-central1

# Just the driver output URI
gcloud dataproc jobs describe JOB_ID --region=us-central1 \
  --format="value(driverOutputUri)"

# State, start time, and details
gcloud dataproc jobs describe JOB_ID --region=us-central1 \
  --format="table(
    jobId,
    status.state,
    status.substate,
    status.stateStartTime,
    status.details
  )"

# List recent jobs
gcloud dataproc jobs list --region=us-central1 --limit=20

# Restrict to one cluster
gcloud dataproc jobs list --region=us-central1 --cluster=course-dev

# Only jobs still running or pending (ACTIVE)
gcloud dataproc jobs list --region=us-central1 --state-filter=active

# Finished jobs (DONE / ERROR / CANCELLED) — INACTIVE
gcloud dataproc jobs list --region=us-central1 --state-filter=inactive

# Kill a running job
gcloud dataproc jobs kill JOB_ID --region=us-central1
```

⚠️ **`gcloud dataproc jobs list --filter` only accepts `status.state` values of `ACTIVE`
or `INACTIVE`** — you cannot filter by `ERROR` or `DONE` directly. `ACTIVE` groups
`PENDING`, `SETUP_DONE`, and `RUNNING`; `INACTIVE` groups `CANCELLED`, `DONE`, and
`ERROR`. To find failed jobs specifically, filter on `INACTIVE` and then inspect each
job's `status.state` with `jobs describe`, or filter on labels — which is exactly why
labelling your jobs (`--labels=run_date=2026-10-28`) is worth doing.

### Via Cloud Logging

Driver and executor logs are also shipped to Cloud Logging. The resource type is
`cloud_dataproc_cluster`, and the logs carry structured labels.

```bash
# All logs for a cluster
gcloud logging read \
  "resource.type=cloud_dataproc_cluster \
   AND resource.labels.cluster_name=my-cluster \
   AND severity>=WARNING" \
  --project=YOUR_PROJECT_ID \
  --limit=50 \
  --format="table(timestamp,severity,labels.'logging.googleapis.com/source_location'.file,textPayload)"
```

```bash
# Python errors (stderr) from the driver
gcloud logging read \
  "resource.type=cloud_dataproc_cluster \
   AND resource.labels.cluster_name=my-cluster \
   AND textPayload:\"Traceback (most recent call last)\"" \
  --project=YOUR_PROJECT_ID \
  --limit=20
```

💡 **Driver stdout is the single most important log.** Spark's structured progress bars go
to stderr and are extremely noisy. The `print()` statements in your driver are what you
actually want, and they land in the driver output — both via `gcloud dataproc jobs
describe` and as `stdout` entries in Cloud Logging.

### Reading the driver output from GCS directly

```bash
# List the job's output directory
gcloud storage ls gs://STAGING_BUCKET/google-cloud-dataproc-metainfo/JOB_ID/

# Download and read it
gcloud storage cat gs://STAGING_BUCKET/google-cloud-dataproc-metainfo/JOB_ID/*/stdout
```

---

## The cluster metadata server

Every VM in a Dataproc cluster runs the **GCE metadata server**, and Dataproc populates it
with cluster-specific attributes. This is how a driver program discovers facts about the
cluster it is running on, without any hardcoding or API calls.

```bash
# From inside the cluster (SSH or from a job)
curl -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/attributes/dataproc-cluster-name
```

The available attributes:

| Attribute | Value |
|-----------|-------|
| `dataproc-bucket` | Staging bucket name |
| `dataproc-region` | Region of the cluster's endpoint |
| `dataproc-cluster-name` | Cluster name |
| `dataproc-cluster-uuid` | Cluster UUID |
| `dataproc-role` | `Master` or `Worker` |
| `dataproc-worker-count` | Number of worker nodes |
| `dataproc-master` | Hostname of the first master |
| `dataproc-master-additional` | Comma-separated extra master hostnames (HA) |
| `SPARK_BQ_CONNECTOR_VERSION` | Version of the pre-installed BigQuery connector |

From PySpark:

```python
import json
import urllib.request

def metadata_attribute(name: str, default: str = "") -> str:
    """Read a Dataproc instance attribute from the GCE metadata server."""
    url = (
        "http://metadata.google.internal/computeMetadata/v1/instance/attributes/"
        + name
    )
    req = urllib.request.Request(url, headers={"Metadata-Flavor": "Google"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.read().decode("utf-8").strip()
    except Exception:
        return default


CLUSTER_NAME = metadata_attribute("dataproc-cluster-name", "local")
BUCKET       = metadata_attribute("dataproc-bucket")
REGION       = metadata_attribute("dataproc-region")
ROLE         = metadata_attribute("dataproc-role", "local")

print(f"running on {CLUSTER_NAME} in {REGION} as {ROLE}")
```

💡 **Why this matters.** A job that writes to `gs://BUCKET/...` normally hardcodes the
bucket name. If the same code runs on a dev cluster and a prod cluster, the bucket differs.
Reading `dataproc-bucket` from the metadata server makes the job portable — one code path,
two environments, no configuration drift.

⚠️ **The metadata server is only reachable from inside the cluster.** A driver running on
your laptop cannot read it. And the `dataproc-*` attributes do not exist on a generic
Compute Engine VM, so always supply a sensible default.

---

## Interactive sessions: three ways

### 1. Jupyter via the Component Gateway (the modern way)

Jupyter is an **optional component**. You install it at cluster creation and expose it
through the **Component Gateway**, which proxies the UI over an authenticated, TLS-
terminated URL.

```bash
gcloud dataproc clusters create jupyter-cluster \
  --region=us-central1 \
  --image-version=2.2-debian12 \
  --master-machine-type=n2-highmem-4 \
  --worker-machine-type=n2-highmem-4 \
  --num-workers=2 \
  --optional-components=JUPYTER \
  --enable-component-gateway \
  --delete-max-idle=1h \
  --labels=env=dev
```

```bash
# List the cluster's web UIs and their Component Gateway URLs
gcloud dataproc clusters describe jupyter-cluster --region=us-central1 \
  --format="value(config.endpointConfig.webAccessPort)"

# The Jupyter endpoint specifically
gcloud dataproc clusters describe jupyter-cluster --region=us-central1 \
  --format="value(config.endpointConfig.webAccessPort)"
```

Then open the **Jupyter** link from the **Component Gateway** section of the cluster
details page in the console. The gateway URL looks like:

```text
https://<port>-m.<cluster-id>.<region>.dataproc.googleusercontent.com/
```

Key details:

- The Jupyter UI runs on **port 8123** on the cluster's first master node.
- By default the property `dataproc:jupyter.listen.all.interfaces` is **`false`**, which
  restricts the notebook server to `127.0.0.1`. The Component Gateway is a reverse proxy
  that forwards to localhost — so the notebook is *never* directly exposed to the internet.
  This is a deliberate mitigation for remote code execution in notebook APIs.
- The component gateway **must** be enabled for the Jupyter component to work.
- Notebooks are saved to the staging bucket by default. Change the location with the
  cluster property `dataproc:jupyter.notebook.gcs.dir`.

⚠️ **Do not set `dataproc:jupyter.listen.all.interfaces=true` on a cluster with a public
IP.** That is the "remote code execution over unsecured notebook server APIs" risk the
default protects against. Leave it `false` and use the Component Gateway.

⚠️ **There is no `gcloud dataproc clusters submit-jupyter` and no
`gcloud dataproc clusters start-jupyter` in the current CLI.** Older tutorials reference
these; they do not exist today. The supported flow is: install the `JUPYTER` optional
component + enable the Component Gateway, then use the gateway URL.

For **serverless** Spark (Dataproc Serverless), there *is* a separate
`gcloud dataproc sessions create` surface with its own JupyterLab tooling — that is a
different deployment mode, covered in the serverless chapter.

### 2. SSH to the master

The most direct access, and the one that gives you `spark-shell`, `pyspark`, `spark-sql`,
and `yarn`.

```bash
# SSH to the master
gcloud compute ssh jupyter-cluster-m --zone=us-central1-a

# Once in:
yarn list                      # running YARN applications
yarn application -list         # same thing
spark-shell --master yarn      # Scala REPL
pyspark --master yarn          # Python REPL with Spark preloaded
spark-sql --master yarn        # SQL REPL
```

```
# In the Python REPL
>>> spark
<pyspark.sql.session.SparkSession object at 0x...>
>>> spark.range(10).show()
+----------------+
|               id|
+----------------+
|               0|
|               1|
|               2|
...
```

💡 **`pyspark` in the REPL already has a live `SparkSession` named `spark`.** This is
different from a submitted script, where you must create it yourself. In a submitted job
you write:

```python
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("my-etl")
         .getOrCreate())
```

⚠️ **SSH access is enabled by default on image versions before 3.1 and disabled by default
on 3.1 and later.** On `2.2-debian12` (our course image), SSH just works. On newer images
you must pass `--enable-ssh` at cluster creation time.

⚠️ **Anything you `pip install` on the master over SSH does not persist** to the workers,
and it vanishes when the cluster is deleted. Use initialization actions or a custom image
for real dependencies.

### 3. Spark Connect (the modern client-server model)

Spark Connect lets your **local** Python process drive a **remote** Spark cluster. It
inverts the classic model: instead of shipping your code to the cluster, the cluster runs
the code and your laptop sends it operations over a gRPC channel.

```
   ┌────────────────────┐        gRPC / Spark Connect        ┌──────────────────┐
   │  YOUR LAPTOP       │◀──────────────────────────────────▶│  Spark cluster   │
   │                    │                                     │  (serverless     │
   │  pyspark           │   session created lazily,           │   session)       │
   │  .read.csv(...)    │   plan sent to server,              │                  │
   │  .show()           │   results streamed back             │  executors       │
   └────────────────────┘                                     └──────────────────┘
```

```bash
# Install the Dataproc Spark Connect client
pip install -U dataproc-spark-connect
```

```bash
export GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
export GOOGLE_CLOUD_REGION=us-central1
# If running outside GCP:
# export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
```

```python
from dataproc.spark_connect import DataprocSessionBuilder

spark = (DataprocSessionBuilder()
         .project("YOUR_PROJECT_ID")
         .region("us-central1")
         .getOrCreate())

df = spark.read.csv("gs://my-bucket/data/*.csv", header=True)
df.groupBy("category").count().show()
```

Relevant environment variables:

| Variable | Purpose |
|----------|---------|
| `GOOGLE_CLOUD_PROJECT` | Project for the session |
| `GOOGLE_CLOUD_REGION` | Region for the session |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to a service account key, when running outside GCP |
| `MANAGED_SPARK_CONNECT_AUTH_TYPE` | `SERVICE_ACCOUNT` or `END_USER_CREDENTIALS` |
| `MANAGED_SPARK_CONNECT_TTL_SECONDS` | Session lifetime |
| `MANAGED_SPARK_CONNECT_IDLE_TTL_SECONDS` | Idle timeout before the session terminates |
| `MANAGED_SPARK_CONNECT_SESSION_TERMINATE_AT_EXIT` | Terminate the session when the client exits |
| `MANAGED_SPARK_CONNECT_SUBNET` | Subnet name or URI for the session |

💡 **Spark Connect is the direction the ecosystem is moving.** It decouples the driver
from the cluster, which means your IDE's debugger, autocomplete, and type checking all work
against a real Spark cluster. That is a genuine developer-experience win over
`spark-submit`.

⚠️ **Spark Connect is not yet feature-complete against classic Spark.** Some APIs and
DataFrame operations behave differently or are unavailable. Check the compatibility matrix
before committing to it for a production pipeline.

### A quick comparison

| | Jupyter | SSH | Spark Connect |
|---|---|---|---|
| Setup | `--optional-components=JUPYTER` + gateway | Built in (pre-3.1) | `pip install dataproc-spark-connect` |
| Runs on | Cluster | Cluster | Serverless session (or cluster) |
| Best for | Teaching, notebooks, exploration | `spark-shell`, debugging on the node | Local IDE against remote compute |
| Persistence | Notebook saved to GCS | None | None |
| Local tooling | ❌ | ❌ | ✅ Full IDE integration |

---

## Auto Zone placement

If you specify `--region` but omit `--zone`, Dataproc picks a zone for you using **Auto
Zone placement**. All nodes in the cluster land in that single zone.

```bash
# Auto Zone: let Dataproc choose
gcloud dataproc clusters create my-cluster \
  --region=us-central1 \
  --image-version=2.2-debian12 \
  --master-machine-type=n2-standard-4 \
  --worker-machine-type=n2-standard-4
```

⚠️ **Omitting `--zone` is not always enough.** If you have set a default zone with
`gcloud config set compute/zone`, that default is picked up instead. To force Auto Zone,
you must either pass `--zone=""` explicitly or use `--auto-zone-exclude-zones`.

```bash
# Explicitly force Auto Zone
gcloud dataproc clusters create my-cluster \
  --region=us-central1 \
  --zone="" \
  --image-version=2.2-debian12

# Auto Zone, but not in these zones
gcloud dataproc clusters create my-cluster \
  --region=us-central1 \
  --auto-zone-exclude-zones=us-central1-b,us-central1-c \
  --image-version=2.2-debian12
```

The exclusion flag requires the region to have **at least two non-excluded zones**.

**How Auto Zone picks:** it prioritizes zones by total **vCPU reservations** available, so
reserved capacity is consumed first. If the request can be fully satisfied by reserved
plus on-demand resources in a zone, that zone wins. Otherwise, it picks the zone most
likely to satisfy the request on-demand.

💡 **Auto Zone is the right default for most clusters.** It is how you get capacity in a
capacity-constrained region without hardcoding a zone that may be out of capacity.

⚠️ **The whole cluster lands in one zone.** That is a zonal resource, not regional. If
that zone has an outage, your entire cluster is unavailable. For genuinely critical
workloads, run clusters in two regions and fail over.

---

## 🛠️ Hands-On: Submit, Observe, Iterate

### Step 1 — Set up a cluster to work against

```bash
gcloud dataproc clusters create course-dev \
  --region=us-central1 \
  --image-version=2.2-debian12 \
  --master-machine-type=n2-standard-4 \
  --worker-machine-type=n2-standard-4 \
  --num-workers=2 \
  --num-secondary-workers=2 \
  --secondary-worker-type=spot \
  --optional-components=JUPYTER \
  --enable-component-gateway \
  --delete-max-idle=1h \
  --labels=course=dataproc,env=dev

# Wait for it to be RUNNING
gcloud dataproc clusters describe course-dev --region=us-central1 \
  --format="value(status.state)"
```

### Step 2 — Write a job

```python
# main.py
import sys
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

def main():
    spark = (SparkSession.builder
             .appName("course-etl")
             .getOrCreate())

    # Demonstrate the metadata server from inside a driver
    try:
        import urllib.request
        req = urllib.request.Request(
            "http://metadata.google.internal/computeMetadata/v1/"
            "instance/attributes/dataproc-cluster-name",
            headers={"Metadata-Flavor": "Google"},
        )
        cluster = urllib.request.urlopen(req, timeout=5).read().decode()
    except Exception:
        cluster = "local"

    print(f"=== Running on cluster: {cluster} ===")

    df = spark.createDataFrame(
        [(1, "alice", 100.0), (2, "bob", 250.0), (3, "alice", 50.0)],
        ["id", "name", "amount"],
    )

    result = (df.groupBy("name")
                .agg(F.sum("amount").alias("total"),
                     F.count("*").alias("orders"))
                .orderBy(F.desc("total")))

    result.show()
    print("Spark version:", spark.version)

    # Arguments after the -- separator land in sys.argv
    if len(sys.argv) > 1:
        print(f"Received argument: {sys.argv[1]}")

    spark.stop()

if __name__ == "__main__":
    main()
```

### Step 3 — Submit it

```bash
gcloud dataproc jobs submit pyspark main.py \
  --cluster=course-dev \
  --region=us-central1 \
  --properties="spark.executor.instances=4,spark.executor.cores=1,spark.executor.memory=2g" \
  -- "hello-world"
```

Expected output:

```text
=== Running on cluster: course-dev ===
+-----+------+-------+
| name| total|orders|
+-----+------+-------+
|alice|  150.0|     2|
|  bob|  250.0|     1|
+-----+------+-------+
Spark version: 3.5.3
Received argument: hello-world
```

### Step 4 — Package dependencies

```bash
# A helper module imported by main.py
cat > utils.py <<'PY'
def normalise_name(name: str) -> str:
    return name.strip().lower()
PY

# Submit with the helper module on the PYTHONPATH
gcloud dataproc jobs submit pyspark main.py \
  --cluster=course-dev \
  --region=us-central1 \
  --py-files=utils.py
```

```bash
# A JAR dependency
gcloud dataproc jobs submit pyspark main.py \
  --cluster=course-dev \
  --region=us-central1 \
  --jars=gs://my-bucket/libs/some-connector.jar

# A config file in the working directory
cat > app.properties <<'PROPS'
warehouse.path=gs://my-bucket/warehouse
mode=overwrite
PROPS

gcloud dataproc jobs submit pyspark main.py \
  --cluster=course-dev \
  --region=us-central1 \
  --files=app.properties
```

### Step 5 — Submit Spark SQL and Spark (Scala/Java)

```bash
# Spark SQL — from a file
cat > analysis.sql <<'SQL'
CREATE EXTERNAL TABLE sales (name STRING, amount DOUBLE)
  USING parquet
  LOCATION 'gs://my-bucket/sales/';

SELECT name, SUM(amount) AS total
FROM sales
GROUP BY name
ORDER BY total DESC;
SQL

gcloud dataproc jobs submit spark-sql \
  --cluster=course-dev \
  --region=us-central1 \
  --file=analysis.sql

# Spark SQL — inline, with variables
gcloud dataproc jobs submit spark-sql \
  --cluster=course-dev \
  --region=us-central1 \
  --execute="SELECT count(*) FROM sales" \
  --params=cutoff=100

# Spark SQL — with a UDF jar on the classpath
gcloud dataproc jobs submit spark-sql \
  --cluster=course-dev \
  --region=us-central1 \
  --file=analysis.sql \
  --jars=gs://my-bucket/libs/udfs.jar

# Spark Java/Scala — needs a main class and a JAR
gcloud dataproc jobs submit spark \
  --cluster=course-dev \
  --region=us-central1 \
  --class=com.example.SalesApp \
  --jars=gs://my-bucket/libs/sales.jar \
  -- 1000
```

⚠️ **`spark-sql` requires `--file` or `--execute` — one of them is mandatory.** The file
must be an HCFS URI, so a local path is uploaded to the staging bucket automatically. It
also has a `--params` flag for setting variables in the queries, and `--jars` for
registering UDFs.

### Step 6 — Observe the job

```bash
# List recent jobs
gcloud dataproc jobs list --region=us-central1 --limit=10

# Pick the most recent job ID
JOB_ID=$(gcloud dataproc jobs list --region=us-central1 --limit=1 \
  --format="value(jobId)")

# Watch it, then print the output
gcloud dataproc jobs wait "$JOB_ID" --region=us-central1

# Inspect the state
gcloud dataproc jobs describe "$JOB_ID" --region=us-central1 \
  --format="table(jobId,status.state,status.substate,status.stateStartTime)"

# Where did the output go?
gcloud dataproc jobs describe "$JOB_ID" --region=us-central1 \
  --format="value(driverOutputUri)"
```

```bash
# Read logs from Cloud Logging
gcloud logging read \
  "resource.type=cloud_dataproc_cluster \
   AND resource.labels.cluster_name=course-dev \
   AND severity>=WARNING" \
  --project=YOUR_PROJECT_ID \
  --limit=20 \
  --format="table(timestamp,severity,textPayload)"
```

### Step 7 — Try the interactive paths

```bash
# Jupyter: get the gateway URL from the console, or use the cluster detail page
gcloud dataproc clusters describe course-dev --region=us-central1 \
  --format="value(config.endpointConfig.webAccessPort)"

# SSH to the master and open a REPL
gcloud compute ssh course-dev-m --zone=us-central1-a
#   then:  pyspark --master yarn
#           spark.sql("SELECT * FROM range(10)").show()
```

### Step 8 — Submit asynchronously from a script

```bash
#!/usr/bin/env bash
set -euo pipefail

CLUSTER=course-dev
REGION=us-central1
BUCKET=gs://my-bucket/jobs

for day in 01 02 03 04 05; do
  gcloud dataproc jobs submit pyspark "daily_etl.py" \
    --cluster="$CLUSTER" \
    --region="$REGION" \
    --async \
    --labels="run_date=${day}" \
    -- "$day" &
  # Space submissions out to avoid the concurrency race condition
  sleep 1
done

wait
echo "All jobs submitted."
```

💡 **`--async` returns immediately with a job ID** instead of streaming the output. Use it
when you are orchestrating many jobs; use the default (blocking) mode when you want to
see the output immediately.

### Step 9 — Clean up

```bash
gcloud dataproc clusters delete course-dev --region=us-central1
```

---

## 🔑 Key Takeaways

- The command is **`gcloud dataproc jobs submit`**, not `gcloud dataproc clusters submit`.
  Subcommands: `pyspark`, `spark`, `spark-sql`, `hadoop`, `hive`, `pig`, `presto`,
  `trino`, `flink`.
- **The `--` separator is mandatory.** Everything after it goes to your driver program;
  everything before it is a gcloud flag.
- Four ways to ship code: `--jars` (classpath), `--py-files` (Python path), `--files`
  (working dir), `--archives` (extracted). All accept local paths or `gs://` URIs.
- `--properties` sets Spark config per job (`key=value`, **no** `spark:` prefix);
  `--properties-file` is the same thing from a file. `--properties` wins on conflict.
- **Always set `spark.executor.instances`** (or enable dynamic allocation). Otherwise Spark
  runs one executor no matter how big your cluster is.
- The API job states are `PENDING`, `SETUP_DONE`, `RUNNING`, `CANCEL_PENDING`,
  `CANCEL_STARTED`, `CANCELLED`, **`DONE`** (success), **`ERROR`** (failure),
  `ATTEMPT_FAILURE`. The console's "Succeeded"/"Failed" map to `DONE`/`ERROR`.
- Use `gcloud dataproc jobs wait` in scripts — it blocks and returns a meaningful exit
  code. Avoid polling loops.
- Every job has a `driverOutputUri` in the staging bucket. `gcloud dataproc jobs
  describe` returns it; `gcloud logging read` gives you structured driver and executor logs.
- The **metadata server** exposes `dataproc-cluster-name`, `dataproc-bucket`,
  `dataproc-region`, `dataproc-role`, and more. Read them from your driver to make jobs
  portable across environments.
- Three interactive paths: **Jupyter** (`--optional-components=JUPYTER` +
  `--enable-component-gateway`, then the Component Gateway URL), **SSH** (`gcloud compute
  ssh`, then `pyspark --master yarn`), and **Spark Connect** (`pip install
  dataproc-spark-connect`, client-server model).
- There is **no `gcloud dataproc clusters submit-jupyter`** and **no `start-jupyter`**.
  Install the component and use the Component Gateway.
- Omit `--zone` for **Auto Zone** placement — but pass `--zone=""` if you have a default
  zone configured. All nodes land in the one chosen zone.

---

## 📚 Practice Exercises

1. **Reproducibility drill.** Take a notebook you have been exploring in Jupyter. Convert
   it into a `main.py` that produces the identical result when submitted with
   `gcloud dataproc jobs submit pyspark`. Then submit it three times with different
   `--properties` values for `spark.sql.shuffle.partitions` and explain, using the Spark
   UI or the driver logs, why the output order changes but the values do not.

2. **The dependency trap.** Write a driver that imports a module `helpers.py` and reads a
   config file `settings.properties` from the working directory. Submit it *without*
   `--py-files` or `--files` and record the exact error. Then fix it with the right flags.
   Finally, explain why adding a 200 MB CSV via `--files` would be a bad idea and where
   that data should live instead.

3. **Job state automation.** Write a bash script that submits a job with `--async`,
   polls `gcloud dataproc jobs describe` for its state, and exits non-zero if the final
   state is not `DONE`. Then find the bug in this version and explain why it fails:
   ```bash
   while [[ "$(gcloud dataproc jobs describe "$JOB" --format='value(status.state)')" == "SUCCEEDED" ]]; do
     sleep 5
   done
   ```
   Explain the difference between the console's "Succeeded" label and the API's `DONE`
   state, and where else in GCP you might see this same naming mismatch.

4. **Cost and scale.** Submit a job that reads a 2 GB Parquet dataset from GCS and
   aggregates it, first with `spark.executor.instances=1`, then with `=50` on a 10-worker
   cluster. Record the wall-clock time of each. Then delete the cluster, create one with
   `--num-workers=0 --num-secondary-workers=10 --secondary-worker-type=spot`, and repeat.
   Explain, using the job logs, what changed about how the work was distributed.

5. **Portability by design.** Rewrite your ETL so that the target bucket, the output
   prefix, and the run date all come from arguments and the metadata server rather than
   hardcoded strings. Then prove portability by running the identical command against two
   different clusters in two different regions and diffing the output locations.

---

## 📖 Further Reading

- Submit a job (console, gcloud, REST) — https://cloud.google.com/dataproc/docs/guides/submit-job
- `gcloud dataproc jobs submit` reference — https://cloud.google.com/sdk/gcloud/reference/dataproc/jobs/submit
- `gcloud dataproc jobs submit pyspark` reference — https://cloud.google.com/sdk/gcloud/reference/dataproc/jobs/submit/pyspark
- `gcloud dataproc jobs submit spark` reference — https://cloud.google.com/sdk/gcloud/reference/dataproc/jobs/submit/spark
- `gcloud dataproc jobs describe` reference — https://cloud.google.com/sdk/gcloud/reference/dataproc/jobs/describe
- `gcloud dataproc jobs wait` reference — https://cloud.google.com/sdk/gcloud/reference/dataproc/jobs/wait
- The Jupyter optional component — https://cloud.google.com/dataproc/docs/concepts/components/jupyter
- Cluster metadata (attributes and labels) — https://cloud.google.com/dataproc/docs/concepts/configuring-clusters/metadata
- Auto Zone placement — https://cloud.google.com/dataproc/docs/concepts/configuring-clusters/auto-zone
- Cluster properties reference — https://cloud.google.com/dataproc/docs/concepts/configuring-clusters/cluster-properties
- Dataproc IAM roles and permissions — https://cloud.google.com/dataproc/docs/concepts/iam
- Spark configuration reference — https://spark.apache.org/docs/latest/configuration.html
- Spark tuning guide — https://spark.apache.org/docs/latest/sql-performance-tuning.html
- Dataproc REST API — https://cloud.google.com/dataproc/docs/reference/rest/v1/projects.regions.jobs
