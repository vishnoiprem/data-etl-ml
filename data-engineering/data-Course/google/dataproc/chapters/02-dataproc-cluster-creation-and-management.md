# 1.2 — Dataproc Cluster Creation & Management

> **Section 1 · Foundations · Lecture 1.2 · 5:24**

## 🎯 What you will learn

- The anatomy of a Dataproc cluster: master, primary workers, and secondary (Spot) workers
- How to create a cluster with `gcloud dataproc clusters create` and what every flag actually controls
- Choosing machine types, worker counts, and preemptible/Spot capacity for a given workload
- The lifecycle model: temporary vs persistent clusters, idle auto-deletion, and scheduled deletion
- Labels, metadata, and cluster properties — and why they are not the same thing
- Networking: internal-IP-only clusters, Private Google Access, VPC firewall rules
- Service accounts and the IAM roles required to create, run, and observe a cluster
- The cost-control patterns that keep a Dataproc project from surprising you

---

## 🧠 Concept

A Dataproc cluster is a group of Compute Engine virtual machines, wired together so that
Spark can schedule work across them. Nothing about it is exotic — the important part is
understanding that **the cluster is the unit of cost, and its size is a decision you make
before you know how much work will arrive.**

### The three node roles

```
                    ┌──────────────────────────────┐
                    │        MASTER NODE           │
                    │  ┌────────────────────────┐  │
                    │  │  Dataproc Agent        │  │
                    │  │  YARN ResourceManager  │  │
                    │  │  HDFS NameNode         │  │
                    │  │  Spark History Server  │  │
                    │  │  Spark Driver (per job)│  │
                    │  └────────────────────────┘  │
                    └───────────────┬──────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
      ┌───────▼────────┐   ┌────────▼───────┐   ┌────────▼───────┐
      │ PRIMARY WORKER │   │ PRIMARY WORKER │   │ PRIMARY WORKER │
      │  runs Spark    │   │  runs Spark    │   │  runs Spark    │
      │  executors     │   │  executors     │   │  executors     │
      │  runs HDFS     │   │  runs HDFS     │   │  runs HDFS     │
      │  DataNodes     │   │  DataNodes     │   │  DataNodes     │
      └────────────────┘   └────────────────┘   └────────────────┘

      ┌────────────────┐   ┌────────────────┐   ┌────────────────┐
      │ SECONDARY      │   │ SECONDARY      │   │ SECONDARY      │
      │ (Spot/preempt.)│   │ (Spot/preempt.)│   │ (Spot/preempt.)│
      │  executors only│   │  executors only│   │  executors only│
      └────────────────┘   └────────────────┘   └────────────────┘
```

| Role | Count | Runs | Billed? |
|------|-------|------|---------|
| **Master** | 1 (or 3 for HA) | YARN RM, HDFS NameNode, Spark History Server, and the **driver** for each submitted job | Yes — always |
| **Primary worker** | 0…N | Spark executors **and** HDFS DataNodes | Yes |
| **Secondary worker** | 0…N | Spark executors **only** — no HDFS | Yes, at Spot pricing |

The master is a **single point of failure** in a standard cluster. If it dies, the cluster
is in an unrecoverable state and must be rebuilt. Dataproc offers a high-availability mode
with 3 masters (`--num-masters=3`) that elects a leader, at 3× the master cost.

💡 **The driver runs on the master.** This surprises people. Your PySpark driver program —
the code in `main.py` — executes inside the master JVM's process space. That means:
- Master memory is your driver's memory. A driver that calls `collect()` on a 10 GB result
  will OOM the master, not a worker.
- The master is also running YARN, NameNode, and the History Server, so give it headroom.
  `n1-standard-4` (16 GB) is a reasonable floor for a production job master.

### The `--image-version` contract

The image version pins the entire software stack. It is not a cosmetic detail — it is an
API contract.

| Image family | Spark | Hadoop | Status |
|--------------|-------|--------|--------|
| `1.5` | 3.1.x | 2.10 | Ended support |
| `2.1` | 3.2.x | 3.3 | Ended support (2026-03-31) |
| **`2.2-debian12`** | **3.5.3** | 3.3.6 | GA, supported until 2027-03-31 |
| `2.3-debian12` | 3.5.x | 3.3.x | GA, supported until 2027-06-09 |
| `3.0-debian13` | — | — | GA, supported until 2028-07-15 |

This course uses **`2.2-debian12`** throughout: it ships **Apache Spark 3.5.3**, is a
General Availability image, and remains in the supported window.

⚠️ **Always pin `--image-version`.** If you omit it, gcloud uses the *current default*,
which Google changes as new images reach GA. A pipeline that worked on Tuesday can start
using a different Spark, a different Python, and a different connector set on Wednesday
with no change to your code and no diff in your repo. Pin the version; upgrade it
deliberately.

### Machine types

Dataproc supports all the standard Compute Engine families, and the choice is a statement
about your workload's bottleneck.

| Family | Shape | Use it when | Example |
|--------|-------|-------------|---------|
| **General purpose** (`n1`, `n2`, `n2d`, `n4`, `n4d`, `e2`, `c3`, `c4`) | 1:1 vCPU:RAM (varies) | Balanced ETL, mixed CPU+shuffle work | `n2-standard-4` |
| **Memory-optimized** (`m1`, `m2`) | High RAM per vCPU | Caching, wide aggregations, `collect()`-heavy | `m2-ultramem-16` |
| **Compute-optimized** (`c2`, `c2d`) | High vCPU per RAM | CPU-bound scans, tight loops, large UDFs | `c2-standard-8` |
| **ARM** (`c4a`) | Ampere, good price/perf | ARM-compatible builds only — Spark is fine, some native libs are not | `c4a-standard-4` |
| **Custom** (`custom-6-23040`) | You pick vCPU + MB | Workload between two standard sizes | `custom-6-23040` |

The suffix is the shape: `n2-standard-4` = 4 vCPU, 16 GB RAM. `n2-highmem-4` = 4 vCPU,
32 GB. `n2-highcpu-4` = 4 vCPU, ~3.6 GB. Dataproc requires a minimum of **3.5 GB (3584 MB)**
of memory per node.

**The highmem/highcpu distinction is about the *ratio*, not the absolute amount.** A
`highmem-4` gives you 32 GB; a `highcpu-4` gives you 3.6 GB. Choosing `highcpu` for a
shuffle-heavy join is the classic Dataproc mistake: you get four cores and then spend
your time in GC.

| Workload | Master | Workers |
|----------|--------|---------|
| Batch ETL, 1:1 CPU:memory | `n2-standard-4` | `n2-standard-4` |
| Heavy shuffle / large group-bys | `n2-standard-4` | `n2-highmem-4` |
| CPU-bound string processing | `n2-standard-4` | `n2-highcpu-8` |
| Interactive exploration | `n2-highmem-4` | `n2-highmem-4` |

⚠️ **`n1-standard-1` is not supported on 2.0+ images.** Shared-core types (`e2-micro`,
`e2-small`, `e2-medium`, `f1-micro`, `g1-small`) are not supported at all. If you need a
tiny cluster, use `--cluster-type=single-node` (a 1-node cluster) rather than trying to
squeeze into a micro machine.

### Primary vs secondary workers: the preemptible decision

This is the single highest-leverage cost decision in Dataproc.

```
  PRIMARY WORKERS                      SECONDARY WORKERS
  ───────────────                      ─────────────────
  Standard (on-demand) price           Spot (preemptible) price
  ~4× the cost for ~1/4 throughput     ~60-80% cheaper
  Guaranteed to run                    Can be reclaimed by Google at any time
  Run executors AND HDFS DataNodes     Run executors ONLY
  Stable — no task loss                Tasks die; Spark re-runs them
```

The reason secondary workers are safe is that **Spark's execution model is fault-tolerant
by design.** Each stage of a job is split into tasks. If a worker VM is preempted, the
tasks it was running are reported back to the scheduler and re-assigned to another worker.
For a job whose stages write to GCS (or that recompute from a lineage), the loss is
compute time, not correctness.

💡 **The classic high-availability pattern:** 2 primary workers (guaranteed, hold HDFS
state and provide baseline capacity) + 10 secondary workers (Spot, soak up the variable
load). The primary workers guarantee a floor of throughput; the secondary workers provide
the burst.

### The flags that control this

```bash
--num-workers=3                  # number of PRIMARY workers (on-demand by default)
--num-secondary-workers=5        # number of SECONDARY workers
--secondary-worker-type=spot     # preemptible | non-preemptible | spot  (default: preemptible)
```

⚠️ **`--num-workers` sets the *primary* worker count, and primary workers are on-demand
VMs by default.** There is no `--no-preemptible` flag on `gcloud dataproc clusters
create` — older tutorials and blog posts show it, but it does not exist in the current
CLI. The Spot/on-demand choice is made **per group**:

- **Primary workers** → on-demand (guaranteed).
- **Secondary workers** → controlled by `--secondary-worker-type`, which accepts
  `preemptible` (the default), `non-preemptible`, or `spot`. `spot` is the modern
  Compute Engine term and behaves like `preemptible`; `preemptible` is kept for
  compatibility.

If you want *all* workers to be Spot, you set `--secondary-worker-type=spot` and keep
`--num-workers=0`, putting all capacity in the secondary group — but remember secondary
workers cannot host HDFS DataNodes, so on-cluster HDFS becomes unavailable.

⚠️ **Spot preemption in Dataproc is not instant.** A preempted VM goes into a termination
sequence, and the executor must be reported dead before Spark retries its tasks. On a
cluster that is *only* Spot workers, a mass preemption event can cause noticeable
"task not found" retry churn. Spark's `spark.task.maxFailures` (default 4) bounds this, and
Dataproc sets sensible defaults, but do not run a single huge task per worker.

### Autoscaling

Autoscaling is a reusable policy object you attach to a cluster. It scales **primary
workers only** by default (secondary workers get their own `secondaryWorkerConfig`).

```yaml
# autoscaling-policy.yaml
clusterType: STANDARD
workerConfig:
  minInstances: 2
  maxInstances: 20
  weight: 1
secondaryWorkerConfig:
  minInstances: 0
  maxInstances: 50
  weight: 1
basicAlgorithm:
  cooldownPeriod: 2m
  yarnConfig:
    scaleUpFactor: 0.05
    scaleDownFactor: 1.0
    gracefulDecommissionTimeout: 1h
```

```bash
gcloud dataproc autoscaling-policies import my-policy \
  --source=autoscaling-policy.yaml \
  --region=us-central1

gcloud dataproc clusters create my-cluster \
  --region=us-central1 \
  --autoscaling-policy=my-policy \
  --master-machine-type=n2-standard-4 \
  --worker-machine-type=n2-standard-4 \
  --image-version=2.2-debian12
```

| Field | Meaning |
|-------|---------|
| `cooldownPeriod` | How long to wait after the last scaling action before scaling again. Default `2m`. |
| `scaleUpFactor` | Fraction of the *pending* YARN demand to add when scaling up. `0.05` = add 5%. |
| `scaleDownFactor` | Fraction of the *excess* capacity to remove when scaling down. `1.0` = remove all excess. |
| `gracefulDecommissionTimeout` | Max time to wait for running tasks to finish on a node being removed. Default `1h`. |
| `weight` | Relative priority of this worker group when computing total cluster size. |

⚠️ **Autoscaling is horizontal only.** It changes the *number* of workers, never the machine
type. And it explicitly does **not** work with:
- **HDFS-based workloads** — DataNode decommissioning copies blocks before removing a node,
  which can take hours.
- **Spark Structured Streaming** — a long-running streaming job pins the cluster shape.
- **YARN Node Labels** — YARN reports metrics incorrectly when node labels are used.
- **Idle-cluster scale-down** — creating a new cluster is as fast as resizing one. Delete
  idle clusters instead of shrinking them.

### Cluster properties: the real configuration surface

Flags cover the top-level shape. `cluster properties` cover everything else, using a
`prefix:key=value` syntax that maps onto the underlying config files.

| Prefix | File | Controls |
|--------|------|----------|
| `spark` | `spark-defaults.conf` | Spark runtime config (executor memory, shuffle partitions, jars) |
| `spark-env` | `spark-env.sh` | Spark environment variables |
| `hdfs` | `hdfs-site.xml` | HDFS block size, replication, nameservice |
| `yarn` | `yarn-site.xml` | YARN scheduler, node labels, container sizes |
| `core` | `core-site.xml` | General Hadoop config |
| `mapred` | `mapred-site.xml` | MapReduce |
| `hive` | `hive-site.xml` | Hive / metastore |
| `hadoop-env` | `hadoop-env.sh` | Hadoop env vars |
| `capacity-scheduler` | `capacity-scheduler.xml` | YARN Capacity Scheduler |
| `pig` | `pig.properties` | Pig |
| `distcp` | `distcp-default.xml` | DistCp |

Two properties you will use constantly:

```bash
# Default executor sizing for every job on the cluster
--properties="spark:spark.executor.memory=8g,\
spark:spark.executor.cores=2,\
spark:spark.executor.instances=10"

# Ship a JAR to every job on the cluster (alternative to --jars per job)
--properties="spark:spark.jars=gs://my-bucket/lib/custom-connector.jar"
```

💡 **Use `spark:spark.jars` for cluster-wide dependencies and `--jars` for job-specific
ones.** Never copy custom JARs into `/usr/lib/spark/jars/` on the node — doing so pollutes
the classpath of the Dataproc agent, and transitive dependency conflicts (Guava, Hadoop
libs) cause `ClassNotFoundException` / `NoClassDefFoundError` during job management
operations like cancelling a job, which crashes the agent and orphans YARN applications.

### Labels vs metadata vs properties

Three different mechanisms, and conflating them causes real problems.

| | Purpose | Visible to running processes? | Queryable via API? | Use for |
|---|---|---|---|---|
| **Label** | Indexing & filtering | ❌ | ✅ | `env=prod`, `team=analytics`, `cost-center=1234` |
| **Metadata** | Environment variables for processes | ✅ | ✅ | Config the job needs to read |
| **Property** | Spark/Hadoop/YARN configuration | ✅ (as config) | ✅ | `spark.executor.memory`, `yarn.scheduler...` |

```bash
gcloud dataproc clusters create my-cluster \
  --region=us-central1 \
  --labels=env=prod,team=analytics,owner=data-platform \
  --metadata=spark-env=prod,pipeline-name=nightly-orders
```

Dataproc injects its own reserved metadata keys onto every node:

| Metadata key | Value |
|--------------|-------|
| `dataproc-bucket` | Name of the cluster's staging bucket |
| `dataproc-region` | Region of the cluster's endpoint |
| `dataproc-cluster-name` | Cluster name |
| `dataproc-cluster-uuid` | Cluster UUID |
| `dataproc-role` | `Master` or `Worker` |
| `dataproc-worker-count` | Number of worker nodes (0 for single-node) |
| `dataproc-master` | Hostname of the first master (`[CLUSTER]-m` or `[CLUSTER]-m-0`) |
| `dataproc-master-additional` | Comma-separated extra master hostnames in an HA cluster |

⚠️ **Do not use `--metadata` to set `dataproc-*` keys.** You will silently break
initialization actions that depend on them.

### Lifecycle: temporary, persistent, and everything between

```
   CREATE ──▶ RUNNING ──▶ (jobs) ──▶ IDLE ──▶ DELETING ──▶ (gone)
                │                      │
                │                      └─▶ STOPPED (scheduled stop)
                │
                └─▶ ERROR ──▶ DELETING
```

**Temporary cluster** — created per job, deleted when it finishes. The economic default
for batch ETL.

**Persistent cluster** — long-lived, used for interactive development, streaming jobs, or a
shared dev environment. Costs money every hour it exists.

**Scheduled deletion** is the safety net for persistent clusters. Three flavours:

| Flag | Semantics | Granularity | Range |
|------|-----------|-------------|-------|
| `--delete-max-idle` | Delete after N of *cluster idle* | seconds/minutes/hours/days | 1 second – 14 days |
| `--delete-max-age` | Delete N after the cluster was created | same | 10 minutes – 14 days |
| `--delete-expiration-time` | Delete at a specific timestamp | RFC 3339 | — |

The same three flags exist for **scheduled stop** as `--stop-max-idle`, `--stop-max-age`,
and `--stop-expiration-time`. On `gcloud dataproc clusters update`, the negation flags
`--no-delete-max-idle` and `--no-delete-max-age` cancel an existing schedule.

"Cluster idle" is not "no jobs in the API". By default, the
`dataproc:dataproc.cluster-ttl.consider-yarn-activity` property is `true`, which means
**both** YARN activity **and** Dataproc Jobs API activity must be idle before the idle
timer starts. That is the behaviour you want: a job you submitted via `spark-submit` on
the master also keeps the cluster alive.

⚠️ **Jobs running on a cluster are killed when it is deleted.** A scheduled deletion that
fires mid-job fails that job. Size the idle window generously (30m+ for a dev cluster) and
remember that the console's default idle window is short — 10 minutes in some templates.

**Scheduled stop** is the middle option — `--stop-max-idle` / `--stop-expiration-time` /
`--stop-max-age` freeze the cluster (preserving state and disks) instead of destroying
it. You pay for the disks, not the CPU.

### Networking: internal IP only is the default

Since image 2.2, **Dataproc clusters are provisioned with internal-IP-only addresses** by
default. There is no public IP on the nodes. This is a security improvement and it has
operational consequences you must plan for.

```
   ┌─────────────────────────────────────────────────────────┐
   │  Your VPC                                              │
   │                                                         │
   │   ┌──────────┐        ┌──────────┐                     │
   │   │  Master  │◀──────▶│ Workers  │  (internal only)    │
   │   └────┬─────┘        └──────────┘                     │
   │        │                                                │
   │        │  default route → Default Internet Gateway      │
   │        ▼                                                │
   │   ┌──────────────────────────────┐                      │
   │   │  Private Google Access (PGA) │                      │
   │   │  traffic stays in Google's  │                      │
   │   │  network, never the public  │                      │
   │   │  internet                   │                      │
   │   └──────────┬───────────────────┘                      │
   └──────────────┼────────────────────────────────────────┘
                  ▼
        GCS · BigQuery · Logging · Monitoring
```

**Private Google Access (PGA)** is what makes internal-only clusters work. Dataproc
enables it on the cluster subnet automatically, giving the subnet a static route
`0.0.0.0/0 → default internet gateway`. Traffic to Google APIs rides that route and
**never leaves Google's network**, even though the next hop is called the "default internet
gateway". That naming is the single most confusing thing in GCP networking.

Requirements for a Dataproc VPC:

1. **A route to the internet gateway** must exist (Dataproc creates the PGA route for you;
   if you deleted the default route, you must add it back).
2. **Ingress allow firewall rule** — cluster VMs must be able to talk to *each other*.
   The VPC's default `ingress deny all` implied rule blocks this. You must allow
   TCP/UDP (all ports) and ICMP between the cluster VMs.
3. **Egress allow firewall rule** — required if you have added overriding egress deny
   rules. The destination must be `0.0.0.0/0` because the Dataproc control API's IP
   ranges are not static.

```bash
# Ingress: allow all cluster VMs to talk to each other
gcloud compute firewall-rules create dataproc-allow-internal \
  --network=my-vpc \
  --direction=INGRESS \
  --action=ALLOW \
  --rules=tcp:0-65535,udp:0-65535,icmp \
  --source-ranges=10.128.0.0/20 \
  --target-tags=goog-dataproc-node \
  --priority=1000

# Egress: allow cluster VMs to reach Google APIs
gcloud compute firewall-rules create dataproc-allow-egress \
  --network=my-vpc \
  --direction=EGRESS \
  --action=ALLOW \
  --rules=tcp:0-65535,udp:0-65535,icmp \
  --destination-ranges=0.0.0.0/0 \
  --target-tags=goog-dataproc-node \
  --priority=1000
```

💡 **Use the `goog-dataproc-node` network tag** to scope firewall rules to Dataproc VMs
only. Without it you are writing rules that apply to every VM in the VPC.

**Private Google Access** is the VPC-level feature; **Private Service Connect** is the
newer, per-service alternative (a private endpoint to a specific Google API). For most
Dataproc workloads, VPC-native + PGA is the right answer.

### IAM: who may do what

Dataproc's real predefined roles are:

| Role | Grants | Give it to |
|------|--------|-----------|
| `roles/dataproc.admin` | Full control of Dataproc resources | Platform admins only |
| `roles/dataproc.editor` | View + manage clusters, jobs, operations | Data engineers who create clusters |
| `roles/dataproc.viewer` | Read-only access to clusters, jobs, operations | Analysts, dashboards |
| `roles/dataproc.worker` | Worker/data-plane access | **The cluster's VM service account** |
| `roles/dataproc.serverlessEditor` | Manage serverless batches and sessions | Serverless users |
| `roles/dataproc.serverlessViewer` | Read-only serverless access | Observability |

⚠️ **There is no `roles/dataproc.clusterUser` and no `roles/dataproc.developer`.** You will
see these in older blog posts and in some interview questions. The actual roles are
`roles/dataproc.admin`, `roles/dataproc.editor`, `roles/dataproc.viewer`,
`roles/dataproc.worker`, `roles/dataproc.serverlessEditor`, and
`roles/dataproc.serverlessViewer`.

The permission-level API surface:

| API method | Required permission(s) |
|------------|----------------------|
| `clusters.create` | `dataproc.clusters.create` + `iam.serviceAccounts.actAs` |
| `clusters.get` / `list` | `dataproc.clusters.get` / `.list` |
| `clusters.patch` | `dataproc.clusters.update` + `dataproc.operations.get` |
| `clusters.delete` | `dataproc.clusters.delete` |
| `jobs.submit` | `dataproc.jobs.create` **+ `dataproc.clusters.use`** |
| `jobs.get` / `list` | `dataproc.jobs.get` / `.list` |
| `jobs.cancel` | `dataproc.jobs.cancel` |
| `autoscalingPolicies.use` | Required to attach an autoscaling policy to a cluster |

Note `dataproc.clusters.use` — you need it to submit a job. This is the granular-IAM
mechanism: it lets you grant "run jobs on cluster X" without granting "create clusters".

💡 **The `iam.serviceAccounts.actAs` requirement is the one that bites.** To create a
cluster, the caller must be able to *act as* the cluster's VM service account. If you
create a dedicated service account for your cluster, you must also grant
`roles/iam.serviceAccountUser` on it to whoever creates clusters. Forget this and you get
a confusing permission error that has nothing to do with Dataproc.

### Service accounts: separate the control plane from the data plane

The **VM service account** is the identity your cluster's nodes run as. It determines what
your Spark code can reach.

```bash
# 1. Create a dedicated service account for the cluster's VMs
gcloud iam service-accounts create dataproc-cluster-sa \
  --display-name="Dataproc Cluster Service Account" \
  --project=my-project

# 2. Grant it the data-plane role and the storage/bigquery access it needs
gcloud projects add-iam-policy-binding my-project \
  --member="serviceAccount:dataproc-cluster-sa@my-project.iam.gserviceaccount.com" \
  --role="roles/dataproc.worker"

gcloud storage buckets add-iam-policy-binding gs://my-data-lake \
  --member="serviceAccount:dataproc-cluster-sa@my-project.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

# 3. Grant cluster-creators the right to act as it
gcloud iam service-accounts add-iam-policy-binding \
  dataproc-cluster-sa@my-project.iam.gserviceaccount.com \
  --member="user:alice@example.com" \
  --role="roles/iam.serviceAccountUser"

# 4. Use it when creating the cluster
gcloud dataproc clusters create my-cluster \
  --region=us-central1 \
  --service-account=dataproc-cluster-sa@my-project.iam.gserviceaccount.com \
  --scopes=https://www.googleapis.com/auth/cloud-platform
```

⚠️ **Always set `--scopes=https://www.googleapis.com/auth/cloud-platform`.** The default
scope set on Compute Engine instances is the legacy `compute.readonly`-era scope list,
which does **not** include BigQuery, Pub/Sub, or Cloud Storage write access. A job that
works perfectly in Jupyter will fail the moment you submit it with the default scopes.
This is one of the most common "works locally, fails in the cluster" bugs in Dataproc.

⚠️ **Do not leave the default Compute Engine service account with `roles/editor`.** Many
projects auto-grant it. Replace it with `roles/dataproc.worker` plus the specific
permissions your jobs need (GCS object access, BigQuery job user + data viewer). The
`dataproc.worker` role alone is not enough — it does not grant data access to your
buckets or tables.

---

## 🛠️ Hands-On: Create, Inspect, and Destroy

### Step 0 — Prerequisites

```bash
gcloud --version
gcloud auth list
gcloud config set project YOUR_PROJECT_ID
gcloud config set dataproc/region us-central1

# Dataproc API must be enabled
gcloud services list --enabled --filter="config.name:dataproc.googleapis.com"
```

### Step 1 — A temporary, ephemeral cluster (the production default)

This is the command to memorize. Every flag is annotated.

```bash
gcloud dataproc clusters create etl-temp \
  --region=us-central1 \
  --image-version=2.2-debian12 \
  --master-machine-type=n2-standard-4 \
  --worker-machine-type=n2-standard-4 \
  --num-workers=3 \
  --num-secondary-workers=5 \
  --secondary-worker-type=spot \
  --delete-max-idle=30m \
  --delete-max-age=2h \
  --initialization-action-timeout=10m \
  --optional-components=JUPYTER \
  --enable-component-gateway \
  --labels=env=dev,team=data-eng,course=dataproc \
  --metadata=pipeline=daily-orders \
  --service-account=dataproc-cluster-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --scopes=https://www.googleapis.com/auth/cloud-platform \
  --bucket=gs://YOUR_STAGING_BUCKET
```

| Flag | What it does |
|------|--------------|
| `--region=us-central1` | Regional placement. Resources are namespaced per region. |
| `--image-version=2.2-debian12` | Pins Spark 3.5.3 / Hadoop 3.3.6 / Python. **Always pin.** |
| `--master-machine-type=n2-standard-4` | 4 vCPU / 16 GB for master + driver. |
| `--worker-machine-type=n2-standard-4` | Machine type for **primary** workers. |
| `--num-workers=3` | Three **primary** workers (on-demand; also HDFS DataNodes). |
| `--num-secondary-workers=5` | Five **secondary** workers for burst capacity. |
| `--secondary-worker-type=spot` | Secondary workers are Spot VMs (`preemptible` also accepted). |
| `--delete-max-idle=30m` | Auto-delete after 30 minutes with no activity. |
| `--delete-max-age=2h` | Hard delete 2 hours after creation, regardless of activity. |
| `--initialization-action-timeout=10m` | Per-action timeout (default `10m`). |
| `--optional-components=JUPYTER` | Install the Jupyter component (requires Component Gateway). |
| `--enable-component-gateway` | Exposes Jupyter/Hive UIs through an authenticated proxy. |
| `--labels=...` | Searchable tags. Not visible to processes. |
| `--metadata=...` | Env-style values visible to processes. |
| `--service-account=...` | The identity the cluster's VMs run as. |
| `--scopes=...cloud-platform` | **Required** for GCS write / BigQuery access. |
| `--bucket=gs://...` | Staging bucket for job dependencies and driver output. |

💡 **Note the interplay of the two deletion flags:** `--delete-max-idle` and
`--delete-max-age` are independent. The cluster is deleted when *either* condition fires.
`--delete-max-idle=30m` protects you from a forgotten cluster; `--delete-max-age=2h` is
your backstop if the idle calculation misbehaves.

### Step 2 — A persistent development cluster

```bash
gcloud dataproc clusters create dev-sandbox \
  --region=us-central1 \
  --image-version=2.2-debian12 \
  --master-machine-type=n2-highmem-4 \
  --worker-machine-type=n2-highmem-4 \
  --num-workers=2 \
  --delete-max-idle=1h \
  --optional-components=JUPYTER \
  --enable-component-gateway \
  --labels=env=dev,purpose=exploration
```

More memory per core, because interactive exploration is `collect()`-heavy and you will
be pulling data back to the driver.

### Step 3 — A production cluster with autoscaling

```bash
cat > autoscaling-policy.yaml <<'YAML'
clusterType: STANDARD
workerConfig:
  minInstances: 2
  maxInstances: 20
secondaryWorkerConfig:
  minInstances: 0
  maxInstances: 50
basicAlgorithm:
  cooldownPeriod: 2m
  yarnConfig:
    scaleUpFactor: 0.05
    scaleDownFactor: 1.0
    gracefulDecommissionTimeout: 1h
YAML

gcloud dataproc autoscaling-policies import prod-policy \
  --source=autoscaling-policy.yaml \
  --region=us-central1

gcloud dataproc clusters create prod-cluster \
  --region=us-central1 \
  --image-version=2.2-debian12 \
  --master-machine-type=n2-standard-4 \
  --worker-machine-type=n2-standard-4 \
  --autoscaling-policy=prod-policy \
  --num-secondary-workers=0 \
  --delete-max-idle=2h \
  --labels=env=prod
```

### Step 4 — List and describe

```bash
# All clusters in the region
gcloud dataproc clusters list --region=us-central1

# Only running ones
gcloud dataproc clusters list --region=us-central1 \
  --filter="status.state=RUNNING"

# Only clusters with a given label
gcloud dataproc clusters list --region=us-central1 \
  --filter="labels.env=prod"

# Detailed view of one cluster
gcloud dataproc clusters describe etl-temp --region=us-central1

# Just the key facts, as a table
gcloud dataproc clusters describe etl-temp --region=us-central1 \
  --format="table(
    clusterName,
    status.state,
    config.softwareConfig.imageVersion,
    config.gceClusterConfig.masterConfig.machineType.uri,
    config.gceClusterConfig.workerConfig.machineType.uri,
    config.gceClusterConfig.workerConfig.numInstances,
    config.gceClusterConfig.secondaryWorkerConfig.numInstances
  )"

# The cluster's web endpoints (Jupyter, Hive UI, YARN, Spark History...)
gcloud dataproc clusters describe etl-temp --region=us-central1 \
  --format="value(config.endpointConfig.webAccessPort)"

# The staging bucket
gcloud dataproc clusters describe etl-temp --region=us-central1 \
  --format="value(config.gceClusterConfig.configFileUri)"
```

Cluster `status.state` values are `CREATING`, `RUNNING`, `UPDATING`, `DELETING`, `ERROR`,
`STOPPED`. Note that `ACTIVE` is a *filter alias* that groups `CREATING`, `UPDATING`, and
`RUNNING`; `INACTIVE` groups `DELETING` and `ERROR`.

### Step 5 — Update a cluster

```bash
# Change the primary worker count (a rolling operation)
gcloud dataproc clusters update etl-temp \
  --region=us-central1 \
  --num-workers=5

# Change the secondary (Spot) worker count
gcloud dataproc clusters update etl-temp \
  --region=us-central1 \
  --num-secondary-workers=8

# Change the idle-deletion window
gcloud dataproc clusters update etl-temp \
  --region=us-central1 \
  --delete-max-idle=4h

# Cancel idle-based auto-deletion
gcloud dataproc clusters update etl-temp \
  --region=us-central1 \
  --no-delete-max-idle

# Cancel age-based auto-deletion
gcloud dataproc clusters update etl-temp \
  --region=us-central1 \
  --no-delete-max-age

# Add or replace labels
gcloud dataproc clusters update etl-temp \
  --region=us-central1 \
  --update-labels=env=prod

# Remove specific labels
gcloud dataproc clusters update etl-temp \
  --region=us-central1 \
  --remove-labels=team
```

⚠️ **You cannot combine scheduled-deletion flags with other cluster update flags in one
command.** Update the deletion schedule in its own invocation. Note also that on
`clusters update`, label edits use `--update-labels` / `--remove-labels` /
`--clear-labels` — not the `--labels` flag used at creation time.

### Step 6 — Export and import a cluster configuration

```bash
# Export the exact configuration of a cluster to YAML
gcloud dataproc clusters export etl-temp \
  --region=us-central1 \
  --destination=etl-temp.yaml

# Recreate it (or clone it into a new environment) from the YAML
gcloud dataproc clusters import etl-temp-clone \
  --region=us-central1 \
  --source=etl-temp.yaml
```

💡 **This is the best way to manage cluster configuration in Git.** Export a working
cluster's YAML, commit it, and use `import` to reproduce it. Cluster-specific fields
(name, output-only fields, auto-applied labels) are filtered out on export and are
disallowed on import.

### Step 7 — SSH to the master

```bash
# Connect to the master node
gcloud compute ssh etl-temp-m --zone=us-central1-a

# Or, with a specific project/region context
gcloud compute ssh \
  --project=YOUR_PROJECT_ID \
  --zone=us-central1-a \
  etl-temp-m

# Check what the cluster thinks it is
curl -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/attributes/dataproc-cluster-name
```

The master hostname is `<cluster-name>-m` for a standard cluster, or `<cluster-name>-m-0`
for a high-availability cluster.

⚠️ **SSH access is disabled by default on image 3.1+ and enabled by default before that.**
On 2.2-debian12, SSH works out of the box. On newer images you must pass
`--enable-ssh` explicitly at cluster creation.

### Step 8 — Delete

```bash
# Delete a single cluster
gcloud dataproc clusters delete etl-temp --region=us-central1

# Delete every cluster in the region (nuclear option — be very careful)
gcloud dataproc clusters list --region=us-central1 \
  --format="value(clusterName)" | \
  xargs -I{} gcloud dataproc clusters delete {} --region=us-central1 --quiet

# Delete clusters by label
gcloud dataproc clusters list --region=us-central1 \
  --filter="labels.env=dev" \
  --format="value(clusterName)" | \
  xargs -I{} gcloud dataproc clusters delete {} --region=us-central1 --quiet
```

### Step 9 — The console path

The console is not a separate product — it is the GUI over the same API. It is genuinely
better for a few tasks:

- **Create cluster page → "Equivalent command line"** button at the bottom. It renders the
  exact `gcloud` command for the configuration you just built in the UI. This is the
  single best way to learn the CLI: build it in the console, then copy the command.
- **Cluster details page → Cluster properties / Jobs / Instances tabs** — faster than
  `describe` for exploring.
- **Labels** — create and edit label sets with a form, and see the "Label inheritance"
  behaviour for workflows.

---

## 🔑 Key Takeaways

- A Dataproc cluster is a master plus **primary** workers (executors + HDFS) and
  **secondary** workers (executors only). The master runs the driver, so give it headroom.
- **Always pin `--image-version`.** `2.2-debian12` ships Spark 3.5.3 and is supported
  until 2027-03-31. The default image changes under you.
- Choose machine types by **ratio**: `highmem` for shuffles and aggregations, `highcpu`
  for CPU-bound scans, `standard` for balanced ETL. Minimum 3.5 GB RAM per node.
- **Secondary (Spot) workers are the primary cost lever.** Spark retries preempted tasks,
  so fault tolerance is built in. 2 primary + 10 secondary is the standard HA pattern.
- `--num-workers` sets the **primary** worker count (on-demand by default);
  `--num-secondary-workers` sets the secondary group, whose VM type is chosen by
  `--secondary-worker-type=preemptible|non-preemptible|spot`. There is no
  `--no-preemptible` flag.
- Autoscaling is **horizontal only**, attaches via `--autoscaling-policy`, and does not
  work with HDFS, Structured Streaming, or YARN node labels.
- `--delete-max-idle` and `--delete-max-age` are your billing safety net. **A forgotten
  cluster is the #1 cost surprise.** Set one on every cluster.
- `--labels` are for API search; `--metadata` is for processes to read; `--properties`
  (`spark:`, `hdfs:`, `yarn:` prefixes) are for engine configuration. They are not
  interchangeable.
- Clusters are **internal-IP-only by default** and reach Google APIs through Private
  Google Access. You must create an **ingress allow** firewall rule between cluster VMs.
- Use `roles/dataproc.editor` for engineers, `roles/dataproc.viewer` for read-only users,
  and `roles/dataproc.worker` for the **VM service account**. There is no
  `roles/dataproc.clusterUser` or `roles/dataproc.developer`.
- Always set `--scopes=https://www.googleapis.com/auth/cloud-platform` — the default
  Compute Engine scopes will not let Spark write to GCS or BigQuery.
- `gcloud dataproc clusters export` → commit YAML → `import` is the cleanest way to manage
  cluster configuration as code.

---

## 📚 Practice Exercises

1. **Cluster sizing for a real job.** You have a job that reads 4 TB of Parquet from GCS,
   does a 3-way shuffle join on a 500 GB dimension table, and writes 2 TB back. The
   dimension table fits in memory on one worker. Design a cluster: how many primary
   workers, what machine type, how many secondary workers, and why. Then re-do the
   design using a `highmem` worker type and explain the trade-off in wall-clock time and
   cost.

2. **Cost modelling with Spot.** Price three configurations for a 6-hour nightly job:
   (a) 4 standard primary + 0 secondary, (b) 2 standard primary + 10 preemptible
   secondary, (c) 4 preemptible primary + 0 secondary. Use the Google Cloud Pricing
   Calculator. For each, estimate wall-clock time and total cost. Which would you pick
   for a job with a 4-hour SLA, and what happens to that SLA under a mass Spot
   preemption event?

3. **Firewall and Private Google Access.** Your cluster fails to read from GCS with
   `403` or a connection timeout. The nodes have no external IP. Diagnose the failure
   step by step: what is the default egress behaviour, what does PGA do, which implied
   VPC rule is blocking inter-node traffic, and what exact `gcloud compute firewall-rules
   create` command fixes it?

4. **Least privilege IAM.** Design the IAM bindings for this organisation: a data
   engineer who must create and delete clusters, a data scientist who may only submit
   jobs to the cluster labelled `env=prod`, and an analyst who may only read job output.
   Name the exact roles, the exact permissions each needs (including
   `dataproc.clusters.use` and `iam.serviceAccounts.actAs`), and explain where the
   service account for the cluster's VMs fits.

5. **Configuration as code.** Export a cluster's YAML, commit it, and write a script that
   recreates an identical cluster in a different region. Then explain what breaks if you
   forget to re-upload the initialization action script to the new region's bucket.

---

## 📖 Further Reading

- Dataproc cluster types and configuration — https://cloud.google.com/dataproc/docs/guides/create-cluster
- Supported machine types — https://cloud.google.com/dataproc/docs/concepts/compute/supported-machine-types
- Optional components (Jupyter, Hive, Ranger, …) — https://cloud.google.com/dataproc/docs/concepts/configuring-clusters/optional-components
- Cluster properties reference — https://cloud.google.com/dataproc/docs/concepts/configuring-clusters/cluster-properties
- Cluster metadata and labels — https://cloud.google.com/dataproc/docs/concepts/configuring-clusters/metadata
- Cluster network configuration and Private Google Access — https://cloud.google.com/dataproc/docs/concepts/configuring-clusters/network
- Scheduled cluster deletion — https://cloud.google.com/dataproc/docs/concepts/configuring-clusters/scheduled-deletion
- Autoscale clusters — https://cloud.google.com/dataproc/docs/concepts/configuring-clusters/autoscaling
- Auto Zone placement — https://cloud.google.com/dataproc/docs/concepts/configuring-clusters/auto-zone
- Service accounts and IAM roles — https://cloud.google.com/dataproc/docs/concepts/iam
- Dataproc image versions — https://cloud.google.com/dataproc/docs/concepts/versioning/dataproc-version-clusters
- `gcloud dataproc clusters create` reference — https://cloud.google.com/sdk/gcloud/reference/dataproc/clusters/create
- Dataproc pricing — https://cloud.google.com/dataproc/pricing
