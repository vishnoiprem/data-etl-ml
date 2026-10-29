# 1.5 — Dataflow vs Dataproc
> **Section 1 · Beam Fundamentals & Model · Lecture 1.5 · 6:30**

## 🎯 What you will learn

- What Dataflow actually is: a managed, serverless Beam runner
- What Dataproc actually is: a managed Spark and Hadoop *cluster*, not a runner
- The real decision criteria — team expertise, operational burden, streaming maturity, cost profile, exit options
- The hybrid pattern, and when it beats both pure options
- Why "we already have Spark, so we should use Dataproc" is usually wrong for streaming
- A cost comparison with concrete numbers for a representative workload
- The third option many people miss: **running Beam on Dataproc**

---

## 🧠 Concept

### Two different kinds of "managed"

Dataflow and Dataproc are both "managed" Google Cloud products. They are
managed in *completely different senses*, and confusing the two is the
source of most bad architecture decisions in this space.

```text
┌──────────────────────────────────────────────────────────────────────┐
│  DATAFLOW — a managed RUNNER                                       │
│                                                                      │
│    You submit a Beam pipeline.  Google runs it.                     │
│                                                                      │
│    ┌────────────────────────────────────────────────────────────┐    │
│    │  You manage:   the pipeline code, the options, the outputs │    │
│    │  Google manages: workers, autoscaling, state, checkpointing│    │
│    │                 job scheduling, retries, monitoring       │    │
│    └────────────────────────────────────────────────────────────┘    │
│                                                                      │
│    There is no cluster. There is no cluster to size.                 │
│    You specify a worker range; Dataflow picks the actual count.      │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│  DATAPROC — a managed CLUSTER                                       │
│                                                                      │
│    You request a cluster with N workers of type M.                   │
│    Spark runs on that cluster, using Spark's own execution model.    │
│                                                                      │
│    ┌────────────────────────────────────────────────────────────┐    │
│    │  You manage:   the cluster (size, lifetime, autoscaling    │    │
│    │                policy), the cluster version, the jobs,      │    │
│    │                the Spark configuration, and every          │    │
│    │                operational concern in between              │    │
│    │  Google manages: the VMs, the disks, the network, patching │    │
│    └────────────────────────────────────────────────────────────┘    │
│                                                                      │
│    There IS a cluster. It has a lifetime. It has idle cost.         │
└──────────────────────────────────────────────────────────────────────┘
```

That distinction propagates into everything else: pricing, scaling
latency, failure modes, operational burden, and what your team needs to
know.

### What Dataflow gives you

Dataflow is a **Beam runner**. It takes the portable graph and executes it
on Google's own managed infrastructure.

**Serverless.** You do not create a cluster. You submit a job and it runs.
There is no cluster to size, no node to ssh into, no YARN to configure.

**Autoscaling.** You give Dataflow a range:

```bash
--min_num_workers 1 --max_num_workers 100
```

Dataflow starts small and scales up as the backlog grows, then scales down
when it drains. This is the single biggest practical difference from
Spark-on-Dataproc, where a cluster is a fixed number of VMs for its whole
lifetime.

**Streaming with real checkpointing.** Dataflow Streaming checkpoints the
watermark, the per-key state, and the bundle progress continuously to
Cloud Storage. A failed worker resumes from the last checkpoint. The
recovery time is the checkpoint interval, not the whole job. This is
genuine exactly-once processing for supported sinks, not a best-effort
approximation.

**Per-second billing.** Dataflow bills for the worker-time you actually
consume, in per-second increments, on whatever worker type you pick. A job
that runs for 4 minutes and 12 seconds is billed for 4 minutes and 12
seconds of worker time.

**Flex Templates.** A Flex Template packages a pipeline (its code, its
dependencies, its options) into a versioned template stored in Cloud
Storage. You then *launch* it as a managed job, and you can update the
template's code and parameters independently of the job. This is the
mechanism behind "a pipeline is a deployable artefact", and it is a
genuinely different operational model from running a JAR on a cluster.

**Streaming update.** Dataflow Streaming supports updating a running
streaming job's code and pipeline graph without stopping it, preserving
the state.

**Global.** Dataflow runs in dozens of regions. You pick the region closest
to your data.

### What Dataproc gives you

Dataproc is a **managed cluster platform**. You request a cluster; Spark
runs on it.

**You manage the cluster.** Dataproc can create ephemeral clusters (create,
run, delete) or long-lived ones. Both have real operational consequences:

| Cluster type | Lifecycle | Good for | Pain |
|---|---|---|---|
| Ephemeral | created per job, deleted after | batch jobs, Spark Submit, scheduled pipelines | startup time (~30–90 s), no state between jobs |
| Long-lived | created once, kept for weeks | an interactive session, a streaming job, a Spark platform | idle cost, manual upgrades, drift |

**Persistent VMs.** A cluster of 10 `n1-standard-8` workers is 10
persistent VMs, billed for the whole time they exist, whether or not a job
is running.

**Spark's own execution model.** Spark-on-Dataproc is *not* Beam. The
Runner API proto, the SDK harness, the bundle model — none of it is
involved. Spark uses its own DAG scheduler, its own shuffle service, its
own executors and drivers, and its own notion of stage boundaries.

**The full Hadoop ecosystem.** Dataproc clusters ship YARN, HDFS, Hive,
Spark, and the broader GCP integrations. If your existing architecture is
Hive-on-HDFS, Dataproc is how you run it without migrating.

**Streaming support.** Spark Structured Streaming exists and works on
Dataproc, with micro-batch semantics: a trigger (default: one second)
opens a batch of the streaming query, processes it, writes the output,
and checkpoints. It is a *different execution model* from Dataflow's
continuous, checkpoint-per-bundle model. Structured Streaming has
matured considerably, but it is a micro-batch engine wearing a streaming
API, and its exactly-once story is weaker than Dataflow's.

**Lower cost for sustained batch.** This is Dataproc's genuine win, and
it is substantial. See the cost section below.

### The decision criteria

"Which is better" is the wrong question. The right questions are these
six, in roughly the order they should be asked.

**1. Is the workload streaming?**

This dominates everything else. If it is streaming — a pipeline that must
produce results within seconds of the data arriving, continuously, forever
— then Dataflow is the strong default, for reasons that are not about
features but about operating model:

- Dataflow checkpoints continuously; Spark Structured Streaming checkpoints
  per micro-batch.
- Dataflow autoscaling is continuous and backlog-driven; Dataproc
  autoscaling is per-cluster and periodic, and the granularity is a
  cluster, not a stage.
- Dataflow's streaming update lets you ship a fix without dropping the
  window state. On Dataproc, changing the code means restarting the job
  and losing the in-flight state (or resuming from a checkpoint, at best).

If it is batch, keep reading.

**2. What does the team already know?**

This is the most underrated criterion and often the correct tie-breaker.

- A team of Spark engineers will ship on Dataproc in a week and on
  Dataflow in a month. The Beam model is not hard; the *operational*
  vocabulary is — autoscaling algorithm, worker types, streaming update,
  Flex Templates, Dataflow Monitoring, Dataflow Templates.
- A team of Beam engineers will ship on Dataflow in a week.
- A team with neither will spend their first month on the model either
  way, so the model should win.

The counter-argument: Spark expertise is a *transferable, portable*
asset. Beam expertise is narrower. Choosing Dataflow because the team knows
Spark is defensible; choosing Dataflow because "Spark is what we know" and
then never learning Beam is not.

**3. What is the operational burden?**

| | Dataflow | Dataproc |
|---|---|---|
| Cluster provisioning | none | you create it, size it, and delete it |
| Idle cost | zero (a job that is not running costs nothing) | the cluster bills while it exists |
| Capacity planning | give a max, let autoscaling work | size the cluster for your peak, pay for your peak all month |
| Version upgrades | handled by Google | you upgrade the cluster version, and you do it while it is running |
| Monitoring | built into the Dataflow UI, with metrics per step | you set up a metrics exporter, a dashboard, and alerting |
| Failure | the runner retries; you get a stack trace and a job state | you look at YARN, the Spark UI, the executor logs, and the event log |
| Night-shift work | rare | common — clusters drift, workers die, the disk fills |

If you have no platform team and no on-call rotation for data infrastructure,
the operational burden of Dataproc is real and ongoing.

**4. What is the cost profile?**

Summarised in the cost section below. The short version: Dataflow is
cheaper for bursty, latency-sensitive, and streaming workloads; Dataproc is
cheaper for sustained, predictable, high-throughput batch work — and the
crossover is around a certain scale.

**5. What is the portability escape hatch?**

This is the criterion that should matter most to an engineering leader, and
it is the one that is always considered last.

Beam is portable. If you write your pipeline in the Beam model, you can
move it to Dataflow, to Spark, to Flink, or to a local Prism instance.
That is a genuine strategic asset: it means the *SDK* investment is not
locked to Google Cloud.

But the asset only exists if you actually use the Beam model. If you write
a Beam pipeline that is 90% Spark-specific transforms, you have bought
yourself the *appearance* of portability and none of the substance.

The same logic applies in reverse: if you write on Spark and later need
Dataflow, you rewrite. That is the cost of the decision, and it is paid
once, in a quarter you will not enjoy.

**6. Does the workload need the Hadoop ecosystem?**

If the pipeline reads HDFS, writes Hive tables, or depends on a YARN
library, Dataproc is the pragmatic answer and the portability question is
moot.

### The hybrid pattern

The real answer for most organisations is not "pick one" — it is "use
both, deliberately."

```text
  ┌───────────────────────────────────────────────────────────────┐
  │  HYBRID: Beam on Dataproc for Spark-idiomatic batch,         │
  │          Dataflow for streaming                               │
  └───────────────────────────────────────────────────────────────┘

    Batch ETL (revenue reconciliation, historical loads)
      └─▶ Beam pipeline on the SPARK RUNNER on a Dataproc cluster
          ├─ Spark-flavoured: uses Spark's own shuffle, tuned for
          │  large-scale shuffle-heavy batch work
          ├─ Fits the team's existing Spark operational tooling
          └─ Cheap on sustained batch volume

    Streaming (clickstream, CDC, fraud signals)
      └─▶ Beam pipeline on DATAFLOW
          ├─ Continuous checkpointing
          ├─ Per-second billing, no idle cluster
          ├─ True streaming autoscaling
          └─ Streaming update without state loss

    SHARED: the same SDK, the same model, the same transforms
```

Note the direction of the hybrid. It is *not* "Dataflow for batch, Dataproc
for streaming" — that would be backwards. It is **Dataproc for batch,
Dataflow for streaming**, because the two products are strong in
opposite places.

The hybrid is only worth its complexity if the two workloads genuinely
have different characteristics. If you have one streaming pipeline and one
batch pipeline, you already have the hybrid, whether you call it that or
not.

### Why "we already have Spark, so we should use Dataproc" is often wrong

This is the argument you will hear, and it is usually wrong for streaming
workloads. It contains a true premise and a false inference.

**The true premise:** the team knows Spark, the existing code is Spark, and
the existing tooling is Spark. Switching to Dataflow costs time.

**The false inference:** therefore Dataproc is the right choice.

Here is what the inference misses:

**Spark's Structured Streaming is a micro-batch engine.** Every trigger
(default: one second) opens a batch, processes it, writes the output, and
checkpoints. This is a fundamentally different execution model from
Dataflow's continuous one. It works, and it is good — but it is not the
same thing, and the operational characteristics differ:

| | Dataflow Streaming | Spark Structured Streaming |
|---|---|---|
| Unit of work | bundle, continuously | micro-batch, per trigger |
| State checkpoint | continuous, per bundle | per trigger, whole micro-batch |
| Recovery | resume from the last bundle checkpoint | replay the last incomplete micro-batch |
| Latency floor | sub-second | one trigger interval (default 1 s) |
| Late data | first-class, with allowed lateness | supported via watermark + allowed lateness, with sharp edges |
| State backend | managed, autoscaling | your cluster's memory/disk; HDFS checkpointing is slow |
| Exactly-once | supported for compatible sinks | limited; depends on the sink and the checkpoint format |

**A streaming job on Dataproc needs a long-lived cluster.** To run a
continuous stream, you need a cluster that does not terminate — which
means paying for it 24/7, whether or not there is data. The economics
invert completely the moment the workload is "bursty stream" or "idle
stream."

**Autoscaling is coarser.** Dataproc clusters autoscale as a unit, on a
policy interval, and typically with a minimum node count. Dataflow
scales the worker count continuously, per step, based on the actual
backlog.

**The migration cost is paid either way, but Dataflow is where you end
up.** If streaming maturity is a requirement now or in two years, the
question is not "Spark or Dataproc" — it is "how long do we run the
streaming workload somewhere we will have to migrate it from?"

The honest, complete answer:

> **If the workload is streaming and the streaming requirement is
> strategic, use Dataflow — and accept the learning cost, because you
> would pay a larger migration cost later.** If the workload is batch,
> or the streaming requirement is marginal, Dataproc is a legitimate and
> often cheaper choice.

### The third option: Beam on Dataproc

This is the option people miss, and it is genuinely real.

Beam's **Spark runner** lets you run a *Beam* pipeline on a *Spark*
cluster. It is not a hypothetical: `SparkRunner` is a first-class runner
in `StandardOptions.ALL_KNOWN_RUNNERS`, and it ships in the standard
`apache-beam` distribution.

```bash
python project/batch_pipeline.py \
  --runner SparkRunner \
  --spark_master_url spark://<cluster-master>:7077 \
  --spark_submit_uber_jar \
  --spark_rest_url http://<cluster-master>:8500 \
  --input gs://YOUR_BUCKET/orders.csv \
  --output gs://YOUR_BUCKET/summary
```

What happens: your Beam pipeline is translated into the Runner API proto,
the Spark harness translates the proto into a Spark job, and the job runs
on your Dataproc cluster. Your *code* is Beam; your *execution* is Spark.

**When this is the right choice:**

- You want to write in the Beam model — for the portability, the
  readability, the unified batch/streaming story — but run on the Spark
  infrastructure your organisation already operates.
- You are migrating an existing Spark estate incrementally. Write the new
  pipeline in Beam, run it on Spark via the Spark runner, and move it to
  Dataflow later by changing one flag.
- You need Beam's windowing and trigger semantics on Spark, which
  Spark's native API does not offer in the same form.
- You want to exercise the portability path on real infrastructure as part
  of a migration rehearsal.

**The caveats, honestly:**

- **The harness is not perfect.** Beam's windowing on Spark is a
  translation, and subtle differences exist in late-data handling and
  trigger behaviour.
- **Performance is Spark's.** The translation has overhead, and Spark's
  shuffle characteristics apply. A Beam-on-Spark pipeline is not
  faster than a native Spark pipeline doing the same work.
- **Some Beam features do not translate.** `userstate`, some timer
  combinations, and session windows do not map cleanly onto Spark's
  executor model.
- **You are still managing a cluster.** The Spark runner does not give you
  Dataflow's autoscaling or continuous checkpointing.

**The realistic use of this option** is as a migration tool, not as a
permanent destination. Write in Beam, run on Dataproc now, move to
Dataflow when streaming or autoscaling becomes a requirement. The code
does not change.

### A cost comparison with real numbers

Let us cost a representative workload: **a nightly batch aggregation over
1 TB of CSV, plus a continuous streaming aggregation of the same
business metrics.**

Assumptions, stated explicitly so you can change them:

- Batch: 1 TB of CSV input, heavy shuffle (group by region and product),
  ~4 hours of wall-clock on a well-sized cluster.
- Streaming: ~200 events/second sustained, 24×7, ~17.3 billion events per
  day.
- Region: `us-central1`.
- Prices are representative 2026 list prices for `n1-standard-4`-class
  workers and are **illustrative, not a quote** — always check the current
  pricing page.

#### Batch: 1 TB, 4 hours

**Dataproc (Spark on a persistent cluster of 20 workers):**

```text
  Worker type            n1-standard-8 (8 vCPU)
  Cluster size           1 master + 20 workers  ≈ 21 nodes
  On-demand rate         ≈ $0.50 / node-hour (n1-standard-8, us-central1)
  Wall-clock             4 hours
  Idle time              20 hours/day (a persistent cluster)

  Compute for the run:  21 × 4 h × $0.50            = $42.00
  Idle cost (20 h):     21 × 20 h × $0.50           = $210.00
  ─────────────────────────────────────────────────────────────
  Subtotal, persistent cluster                          = $252.00 / night
  With 30 days of uptime:                               = $7,560 / month
```

**Dataproc (ephemeral cluster — created for the job, deleted after):**

```text
  Compute for the run:  21 × 4 h × $0.50            = $42.00
  Cluster creation + teardown                        ≈  $1.00
  ─────────────────────────────────────────────────────────────
  Per night                                               = $43.00
  With 30 runs                                            = $1,290 / month
```

The gap between $7,560 and $1,290 is the entire argument for ephemeral
clusters — and it is why "Dataproc is expensive" is often an artefact of
someone leaving a cluster running.

**Dataflow (serverless, autoscaled):**

```text
  Worker type            n1-standard-4
  vCPU rate              ≈ $0.0305 / vCPU-hour
  Worker cost            4 vCPU × $0.0305            = $0.1220 / worker-hour
  Average workers        ≈ 40 (autoscaled, peaks above this)
  Wall-clock             4 hours

  Compute:               40 × 4 h × $0.1220         = $19.52
  Storage + egress (est.)                             ≈  $8.00
  ─────────────────────────────────────────────────────────────
  Per run                                                 = $27.52
  With 30 runs                                            = $826 / month
```

**Dataflow wins the batch comparison** — modestly, and note that it wins
*because* it autoscales to 40 workers rather than sitting at a fixed 20.

#### Streaming: 200 events/second, 24×7

This is where the gap becomes decisive.

**Dataflow Streaming:**

```text
  Worker type            n1-standard-4
  Worker cost            4 vCPU × $0.0305            = $0.1220 / worker-hour
  Steady-state workers   ≈ 3 (200 events/s is modest)
  Uptime                 730 hours/month

  Compute:               3 × 730 h × $0.1220        = $267.18
  State + checkpoint storage (est.)                    ≈ $25.00
  ─────────────────────────────────────────────────────────────
  Per month                                               = $292
```

**Dataproc (Spark Structured Streaming on a persistent cluster):**

```text
  To sustain 200 events/s with headroom:  1 master + 8 workers = 9 nodes
  Structured Streaming needs the driver alive continuously, so the
  cluster must be alive continuously.

  Compute:               9 × 730 h × $0.50            = $3,285.00
  Idle master + overhead                                 ≈ $400
  ─────────────────────────────────────────────────────────────
  Per month                                               = $3,685
```

#### The summary

| Workload | Dataproc (persistent) | Dataproc (ephemeral) | Dataflow |
|---|---|---|---|
| Batch, 1 TB, nightly | $7,560 / month | $1,290 / month | $826 / month |
| Streaming, 200 ev/s, 24×7 | $3,685 / month | n/a (must be persistent) | $292 / month |
| **Combined** | **$11,245** | n/a | **$1,118** |

**Read this table carefully, because the naive conclusion is wrong.**

Dataflow is roughly **10× cheaper** on this workload, but the reason is
not that Dataflow's compute is cheaper per worker. It is that:

1. **Dataflow only bills for what runs.** A persistent Dataproc cluster
   bills 24/7 whether or not there is a job.
2. **Dataflow autosales.** The batch job used ~40 workers for 4 hours; a
   fixed 20-worker cluster would have taken longer or under-parallelised.
3. **Dataflow's per-second billing suits bursty work.** A job that
   finishes in 4 minutes and 12 seconds is billed for exactly that.

**And the table also has a case where Dataproc wins.** If the batch job
were 20× larger — 20 TB, 80 hours of wall-clock — then Dataproc's
per-node-hour rate on a machine-optimised instance type could beat
Dataflow, because at that scale you are buying dedicated capacity rather
than paying a premium for serverless elasticity and the convenience of
not managing a cluster. The crossover depends on your workload's
*wall-clock-to-data ratio*: the longer the job and the more predictable
the schedule, the more a dedicated cluster wins.

**What the numbers actually tell you to do:**

- **Streaming: Dataflow, decisively.** Not because of features — because
  of idle cost and because a persistent cluster for a small stream is
  paying a 10× premium for the privilege of running Spark's executor
  model.
- **Nightly batch on a small-to-medium scale: Dataflow, unless the team
  is strongly Spark-specialist.** The economics are close, and the
  operational simplicity tips it.
- **Nightly batch at large scale with a Spark-specialist team: Dataproc
  with ephemeral clusters.** Do not leave the cluster running. That one
  habit is worth more than the entire argument above.
- **Never decide on cost alone.** The cost differences above are
  recoverable. Migrating a codebase in eighteen months is not.

---

## 🛠️ Hands-On

### Proving the Portability Escape Hatch

The hands-on demonstrates the third option — Beam running on Spark — and
shows that a Beam pipeline can move between runners by changing one flag.

### Step 1 — Confirm both runners are registered

```python
from apache_beam.options.pipeline_options import StandardOptions

print("Known runners:")
for name in StandardOptions.KNOWN_RUNNER_NAMES:
    print("  -", name)
```

`DataflowRunner`, `SparkRunner`, `FlinkRunner`, `PrismRunner` and the
direct runners all appear. They are all first-class.

### Step 2 — Resolve the Spark runner and its options

```python
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions

options = PipelineOptions(["--runner", "SparkRunner"])
print("runner:", options.view_as(StandardOptions).runner)

spark_options = options.view_as(PipelineOptions)
for name in ("spark_master_url", "spark_submit_uber_jar", "spark_rest_url", "spark_version"):
    print(f"  {name} =", getattr(spark_options, name, None))
```

The Spark runner is a *portable* runner: it uses the Runner API proto and
the SDK harness, exactly like Dataflow does. That is why the same Beam
code can run on both.

### Step 3 — Run the course pipeline on a local Spark master

The Spark runner can start a local Spark master for development:

```bash
cd data-engineering/data-Course/google/Dataflow
pip install "apache-beam[gcp]" pyspark

python project/batch_pipeline.py \
  --runner SparkRunner \
  --spark_master_url "local[4]" \
  --input ./sample_data/orders.csv \
  --output ./out/ch05_spark
```

Note that the *pipeline code* is untouched. The only thing that changed is
the runner and its options. This is the escape hatch in practice.

### Step 4 — Prove the outputs match across runners

```bash
python project/batch_pipeline.py \
  --runner BundleBasedDirectRunner \
  --input ./sample_data/orders.csv \
  --output ./out/ch05_direct

python project/batch_pipeline.py \
  --runner PrismRunner \
  --input ./sample_data/orders.csv \
  --output ./out/ch05_prism

python project/batch_pipeline.py \
  --runner SparkRunner \
  --spark_master_url "local[4]" \
  --input ./sample_data/orders.csv \
  --output ./out/ch05_spark

diff <(cat out/ch05_direct*)  <(cat out/ch05_prism*)  && echo "direct == prism"
diff <(cat out/ch05_direct*)  <(cat out/ch05_spark*)   && echo "direct == spark"
```

Three different execution engines — pure Python, Go, and JVM Spark — and
identical output. The business logic is written once.

### Step 5 — Inspect how the runner changes the environment

The runner decides *where* your user code runs, via
`environment_type`. This is the concrete mechanism behind portability:

```python
from apache_beam.options.pipeline_options import PipelineOptions, PortableOptions

for runner in ("BundleBasedDirectRunner", "PrismRunner", "SparkRunner", "DataflowRunner"):
    options = PipelineOptions(["--runner", runner])
    portable = options.view_as(PortableOptions)
    print(f"{runner:<26} environment_type={portable.environment_type!r}")
```

`LOOPBACK` means "run it right here, in this process". `DOCKER` means
"run it in a container". The Spark runner sets `LOOPBACK` automatically
when the master URL is a local pattern — which is exactly why the local
Spark run needs no container image.

### Step 6 — Check the requirement set the Spark harness must satisfy

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(["--runner", "SparkRunner"])

with beam.Pipeline(options=options) as p:
    (
        p
        | "Create" >> beam.Create([("a", 1), ("b", 2), ("a", 3)])
        | "Double" >> beam.Map(lambda kv: (kv[0], kv[1] * 2))
        | "Group" >> beam.GroupByKey()
    )

proto = p.to_runner_api()
print("requirements:", sorted(proto.requirements))
print("transforms:", sorted(t.unique_name for t in proto.components.transforms.values()))
```

The requirement set is what the Spark harness checks before it will
accept the job. If your pipeline needs something the Spark harness cannot
translate, it is rejected at submission — not halfway through the run.

### Step 7 — Model the cost of a persistent Dataproc cluster

A quick calculation to make the idle-cost argument concrete:

```python
NODE_HOURLY_USD = 0.50     # n1-standard-8, us-central1, illustrative list price
NODES = 21                 # 1 master + 20 workers
RUN_HOURS = 4              # the nightly batch job
IDLE_HOURS = 20            # the rest of the day


def persistent_cluster_cost(months=1):
    """Cost of a cluster that exists all month to serve one nightly job."""
    hours = (RUN_HOURS + IDLE_HOURS) * 30 * months
    return NODES * hours * NODE_HOURLY_USD


def ephemeral_cluster_cost(months=1):
    """Cost of a cluster created for the job and deleted straight after."""
    return NODES * RUN_HOURS * 30 * months + 30 * months


def dataflow_cost(avg_workers=40, worker_hourly=0.1220, months=1):
    """Cost of the same job on Dataflow, autoscaled and billed per second."""
    return avg_workers * worker_hourly * RUN_HOURS * 30 * months


for name, cost in (
    ("Dataproc persistent", persistent_cluster_cost()),
    ("Dataproc ephemeral", ephemeral_cluster_cost()),
    ("Dataflow", dataflow_cost()),
):
    print(f"{name:<22} ${cost:>10,.2f} / month")

print()
print(f"Idle cost of the persistent cluster: "
      f"${NODES * IDLE_HOURS * 30 * NODE_HOURLY_USD:,.2f} / month "
      f"for a job that runs {RUN_HOURS} hours")
```

The last line is the one to remember: **a persistent Dataproc cluster
spends most of its life idle, and idle time is not free.**

### Step 8 — See what the streaming pipeline needs from a runner

```bash
python project/streaming_pipeline.py \
  --runner SparkRunner \
  --spark_master_url "local[2]" \
  --input ./sample_data/events.ndjson \
  --output ./out/ch05_spark_streaming 2>&1 | tail -20
```

This is the boundary of the Spark harness. The pipeline uses `WindowInto`
with `AfterWatermark` and a `FixedWindows` strategy — and Beam's Spark
harness has to translate that into Spark's windowing. It works, but the
semantics are a translation, not an identity.

---

## 🛠️ Common Errors and Fixes

### `ImportError: Google Cloud Dataflow runner not available, please install apache_beam[gcp]`

```text
ImportError: Google Cloud Dataflow runner not available, please install apache_beam[gcp]
```

`DataflowRunner` lives in the `gcp` extra. A plain `pip install
apache-beam` does not include it.

**Fix:**

```bash
pip install "apache-beam[gcp]"
```

### `ValueError: Option spark_rest_url must be set.`

```text
ValueError: Option spark_rest_url must be set.
```

You passed `--spark_submit_uber_jar` without `--spark_rest_url`. The
Spark runner's uber-jar job server needs the REST endpoint of the Spark
History or the job server.

**Fix:** set both, or drop `--spark_submit_uber_jar` and let the runner
use its default Java job server.

### `ValueError: Unexpected pipeline runner: Dataflow. Valid values are ...`

```text
ValueError: Unexpected pipeline runner: Dataflow. Valid values are DataflowRunner,
BundleBasedDirectRunner, DirectRunner, ...
```

You abbreviated the runner name. The lookup tries the exact name, then the
name with `runner` appended — `Dataflow` becomes `DataflowRunner`, but
`DataflowRun` does not match anything.

**Fix:** use the full name: `--runner DataflowRunner`.

### `apache_beam.io.gcp.pubsub.ReadFromPubSub ... is not supported on this runner`

```text
RuntimeError: ReadFromPubSub is not supported on the DataflowRunner ...
```

A runner-specific transform submitted to a runner that does not implement
it. The proto's `requirements` list carries the capability, and the runner
rejects the job at submission.

**Fix:** guard runner-specific I/O behind a factory that branches on the
runner, so the portable core stays portable.

### `OSError: [Errno 111] Connection refused` connecting to the Spark master

```text
java.net.ConnectException: Connection refused
```

The Spark master is not running, or the URL is wrong. `spark://host:7077`
is the master; `http://host:8080` is the master *UI*.

**Fix:** check that the cluster is running, and that the master URL uses
the `spark://` scheme.

### `ValueError: Required staging_location is not set for DataflowRunner`

```text
ValueError: Required staging_location is not set for DataflowRunner
```

Dataflow needs somewhere to stage the job's files and somewhere for its
temp/shuffle data. Both are usually GCS paths.

**Fix:** set both, and give them distinct prefixes so concurrent jobs do
not collide:

```bash
--staging_location gs://YOUR_BUCKET/dataflow/staging \
--temp_location gs://YOUR_BUCKET/dataflow/temp
```

The course's `apply_dataflow_defaults` in `project/beam_options.py` does
this for you when you pass a bucket.

### The Dataproc job runs but the output is empty

```text
# Job succeeded. No output files.
```

Usually the cluster ran out of memory during the shuffle and Spark retried
the stage until it failed — but on some configurations a task failure in a
`WriteToText` can leave no finalised files.

**Fix:** check the YARN application logs for `OutOfMemoryError` and
`ExecutorLostFailure`. Raise `--max_num_workers` on Dataflow, or add
executors and memory on Dataproc.

---

## 💡 Production Notes

- **Do not leave Dataproc clusters running.** The single largest cost
  mistake in this space is a persistent cluster kept alive for a nightly
  job. Ephemeral clusters cost roughly 6× less in the worked example
  above. If you keep a cluster for a streaming job, that is defensible —
  but you should be able to point at the streaming job, not at
  convenience.
- **Dataflow bills per second, so short jobs are cheap.** A 4-minute
  validation job on 10 workers costs well under a dollar. On Dataproc,
  the same validation needs a cluster that exists for at least a few
  minutes, plus the creation and teardown overhead. For development and
  CI, Dataflow's economics are dramatically better.
- **The portability argument only holds if you actually use portable
  constructs.** A Beam pipeline full of Dataflow-specific transforms is a
  Dataflow pipeline with extra ceremony. Review the portability of new
  pipelines the way you review a dependency's licence.
- **Write in Beam, run on Spark, migrate to Dataflow later.** The Spark
  runner makes this a real strategy rather than a rewrite project. This
  is the most under-used feature in the Beam ecosystem.
- **Streaming is where Dataflow's advantage is structural, not
  incremental.** The 10× cost gap and the operational differences
  (continuous checkpointing, backlog-driven autoscaling, streaming
  update) all point the same way. If you are building a streaming
  platform, choose the product that is built for it.
- **Do not compare a Dataflow batch job to a Dataproc batch job without
  normalising the worker types.** A `n2-standard-8` Dataproc node is
  meaningfully cheaper per vCPU-hour than a Dataflow worker of the same
  generation, because Dataflow's price includes the serverless machinery.
  A fair comparison holds the machine generation constant on both sides.
- **Consider the "no cluster" operational cost seriously.** Even if
  Dataproc is cheaper on paper, someone has to create the cluster, watch
  it, upgrade it, and delete it. That is a person-hours cost that does
  not appear on the invoice, and it is usually the deciding factor for a
  team without a platform function.

---

## 🔑 Key Takeaways

- **Dataflow is a managed runner; Dataproc is a managed cluster.** Dataflow
  has no cluster to size and bills per second; Dataproc has persistent
  VMs that bill while idle.
- The decision criteria that matter are: **is it streaming, what does the
  team know, what is the operational burden, what is the cost profile,
  what is the portability exit, and does it need the Hadoop ecosystem**.
- **"We already have Spark" is a true premise and a false inference.** It
  is right for batch, and usually wrong for streaming — where Spark's
  micro-batch model, the need for a 24/7 cluster, and the coarser
  autoscaling all count against it.
- The realistic hybrid is **Dataproc for batch, Dataflow for streaming** —
  the products are strong in opposite places.
- **Beam on Dataproc is a real third option**: the `SparkRunner` executes
  your *Beam* pipeline on your *Spark* cluster through the same proto and
  harness path as Dataflow. It is the best migration tool in the
  ecosystem.
- **In the worked example, Dataflow was ~10× cheaper overall**, but mostly
  because Dataproc clusters were idle 20 hours a day, not because
  Dataflow's compute is cheaper. The crossover depends on your
  workload's wall-clock-to-data ratio.
- **The cost differences are recoverable; the codebase migration is not.**
  Decide on the workload, the team, and the operational model first — and
  use portability as insurance, not as a constraint.

---

## 📚 Practice Exercises

1. **Run the course pipeline on three runners.** Run
   `project/batch_pipeline.py` under `BundleBasedDirectRunner`,
   `PrismRunner`, and `SparkRunner` (with `--spark_master_url local[4]`).
   Expected answer: byte-identical output from all three. Then add a
   `beam.Reshuffle` and re-run — the Spark run is the one most likely to
   diverge in *performance* while producing the same answer.

2. **Make the Spark runner's requirements visible.** Build the streaming
   pipeline (windowing plus `AfterWatermark`) under the `SparkRunner` and
   print `proto.requirements`. Then do the same under the
   `BundleBasedDirectRunner`. Expected answer: the requirement set
   differs — the Spark harness declares different capabilities. Explain
   what that tells you about what the Spark harness can and cannot
   translate.

3. **Cost a realistic workload of your own.** Rewrite the cost script from
   the hands-on with your own numbers: your data volume, your worker type,
   your job duration, your expected event rate. Expected answer: a
   monthly figure for Dataproc persistent, Dataproc ephemeral, and
   Dataflow — and a clear statement of which wins and *why* (idle time,
   autoscaling, or per-worker rate).

4. **Find the crossover.** Double the batch job's wall-clock time in the
   cost script and re-run. At what point does Dataproc's per-node-hour
   rate beat Dataflow's autoscaled spend? Expected answer: there is a
   crossover, and it depends on how much of the Dataflow run is spent
   scaling up from the minimum. Explain why a job with a *predictable*
   schedule favours a dedicated cluster.

5. **Design the hybrid.** Your company has (a) a nightly Hive-on-HDFS
   reconciliation job, (b) a Spark Structured Streaming job on Dataproc
   that is currently idle 60% of the day, and (c) a new clickstream
   pipeline. Write a one-page recommendation covering: which workload goes
   where, what the migration order is, and what the portable core (the
   part that stays in Beam) consists of.

6. **Reflection.** Beam's portability is frequently described as a
   first-class feature and frequently ignored in practice. Write a short
   argument — for or against — that portability is worth paying for, and
   identify the one design decision in a Beam codebase that most
   determines whether the portability claim is real or cosmetic.

---

## 📖 Further Reading

- Google Cloud Dataflow overview — https://cloud.google.com/dataflow/docs/about-dataflow
- Google Cloud Dataflow pricing — https://cloud.google.com/dataflow/pricing
- Google Cloud Dataproc overview — https://cloud.google.com/dataproc/docs/concepts/overview
- Google Cloud Dataproc pricing — https://cloud.google.com/dataproc/pricing
- Apache Beam: the Spark runner — https://beam.apache.org/documentation/runners/spark/
- Google Cloud Dataflow: choosing a runner — https://cloud.google.com/dataflow/docs/concepts/choosing-runner
