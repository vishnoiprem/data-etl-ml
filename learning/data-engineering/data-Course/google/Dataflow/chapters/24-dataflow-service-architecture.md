# 5.1 — Dataflow Service Architecture

> **Section 5 · Dataflow Templates & Deployment · Lecture 5.1 · 6:30**

## 🎯 What you will learn

- The Dataflow job lifecycle, stage by stage, from submission to drain
- How the job graph is turned into *stages*, and what a *step* means in the UI
- Workers, worker pools, and the autoscaler that decides how many exist
- The Job Manager and the Streaming Job Monitor, and why both exist
- The worker heartbeat, and how a "zombie job" happens
- The three identities involved: your user, the service agent, and the worker service account
- Why a batch job ends and a streaming job never does
- What happens when a worker dies mid-bundle, and what exactly-once really guarantees
- How to read the four tabs of the Dataflow UI

---

## 🧠 Concept

### The managed service in one paragraph

Dataflow is a control plane plus a fleet of Compute Engine VMs. You hand it a
graph; it works out how to break that graph into stages, rents machines from
Compute Engine, moves your data between them, keeps them alive, and takes them
back when the work is done. You never see a worker. You only ever see a job ID,
a state, and a bill.

This matters because almost every confusing thing about Dataflow is a
misunderstanding of which of those two halves — **control plane** or **data
plane** — is responsible for what.

| Concern | Owner | You observe it as |
|---|---|---|
| Validate the graph, assign stage names | Job Manager | `JOB_STATE_PENDING` → `JOB_STATE_RUNNING` |
| Decide how many workers, of what type | Autoscaler | `max_workers` metric rising |
| Lease, monitor, replace workers | Worker pool | `worker_health` metric |
| Move bundles between stages | Data plane (GCS) | `bundle_size` / `bytes_counter` metrics |
| Decide what is "done" | Job Manager | `JOB_STATE_DONE` |

### The job lifecycle

A Dataflow job moves through a fixed sequence. The exact state names below
are what `gcloud dataflow jobs list --format='value(status)'` prints.

```text
JOB_STATE_UNKNOWN
        │
        ▼
JOB_STATE_PENDING  ──────────────┐
   (staging, graph validation,    │
    worker lease request)         │
        │                         │
        ▼                         │
JOB_STATE_RUNNING  ◄─────────────┘
   (stages executing, autoscaler
    active, workers heartbeating)
        │
        ├──► JOB_STATE_DRAINING ──► JOB_STATE_DONE
        │      (stop accepting work,
        │       finish in-flight bundles)
        │
        ├──► JOB_STATE_FAILED
        │
        └──► JOB_STATE_CANCELLED
```

#### 1. Submitted

`gcloud dataflow flex-template run` packages the request and hands it to the
Dataflow API. The API returns a **job ID** — a timestamp-prefixed identifier
like `2026-10-28-14_03_11_42-1234567890123456`. From this moment the job
exists and is billed for the resources it holds.

The submission is where your template's GCS path, your staging and temp
locations, the region, the worker machine type and the service account are
recorded. **These are frozen at submission time.** Nothing you change later
applies to a running job.

#### 2. Staged

The Job Manager downloads the template file from GCS, validates that it can
be parsed, and stages the job's metadata: the graph, the options, and the
serialised pipeline proto into the **staging location** you provided.

This is where the `staging_location` collision bites. Two jobs submitted
seconds apart with the same staging path can overwrite each other's staged
metadata, and the second job fails with a misleading error. Unique staging
paths are not hygiene — they are a correctness requirement for concurrent
submissions.

#### 3. Workers leased

The Job Manager asks Compute Engine for worker VMs. Each worker comes up
with:

- the Beam SDK for the Python version you specified,
- your template file,
- any `--py-files` and `--requirements-file-requirements` you attached,
- a job name and a work-item lease endpoint.

Workers do **not** ask for work. The Job Manager *leases* bundles to them.
This inversion is what makes the autoscaler possible: the control plane can
stop handing out work before it shuts a machine down.

#### 4. Graph executed

Each stage pulls bundles from its input (usually GCS, sometimes Pub/Sub or
BigQuery), processes them, and writes the results out. A **bundle** is the
unit of work — typically 100 elements or a size threshold, whichever comes
first.

#### 5. Autoscaled

The autoscaler watches throughput, backlog, and CPU utilisation, and adjusts
the number of leased workers. It scales up when workers are saturated and
down when they are idle. It runs continuously for a streaming job and in
bursts for a batch job.

The key property: **the autoscaler never kills a worker that is holding a
bundle.** It marks the worker for retirement, and the worker finishes its
current bundle, returns the result, and then exits. This is why a scale-down
does not lose data.

#### 6. Checkpointed

For streaming, the worker periodically writes its state (window contents,
timers, pending bundles) to the **staging location** as a checkpoint. A
checkpoint is what makes the pipeline resumable and what allows the
exactly-once guarantee to hold across a worker failure.

For batch, "checkpointing" is much weaker — mostly the checkpoint file that
records which work items completed. A batch job that fails is generally
**restarted from the beginning**, not resumed. This is worth internalising:
batch retry semantics are "rerun", streaming retry semantics are "resume".

#### 7. Drained

When the work is done — or when you cancel — the Job Manager stops leasing
new bundles, lets in-flight bundles finish, tears down the workers, and
releases the resources. Only then does the job reach `JOB_STATE_DONE` or
`JOB_STATE_CANCELLED`.

Draining is why a cancelled streaming job can take several minutes to reach
`JOB_STATE_CANCELLED`. That delay is not a hang.

### The job graph, stages and steps

Three levels of structure matter, and they are easy to confuse.

**Step.** A step is what *you* wrote. Every `Map`, `Filter`, `CombinePerKey`
and `WriteToBigQuery` you put in the pipeline is a step, and it keeps the
label you gave it. The label is the thing you search for in the logs.

**Stage.** A stage is what the *runner* produced. The Dataflow optimizer
groups consecutive compatible steps into a stage, because a stage is the unit
of parallelism and the unit of resource accounting. A stage runs on a set of
workers; a step inside that stage runs on whichever worker owns the bundle.

**Graph.** The whole thing, stage by stage, with the edges showing data
flow. Edges labelled `Shuffle` or `GroupByKey` are the expensive ones:
they mean data is being written to GCS and read back.

```text
step:    ReadOrders ──▶ ParseOrders ──▶ KeepCompleted ──▶ KeyByRegion
                              │
                              ▼
stages:  [S00: ReadFromText]  [S01: Parse/Filter]  [S02: CombinePerKey]
                              │
                              ▼
graph:   S00 ──────▶ S01 ──────▶ S02 ──────▶ S03: WriteSummary
                                 └──── shuffle ────┘
```

#### Fusion, and why it matters

The optimizer fuses steps whenever it can: a `Map` immediately followed by a
`Filter` can run in one pass, with no intermediate write. This is the whole
point of expressing work in the Beam model, and it is why
`Map` → `Filter` is much cheaper than `Map` → `WriteToText` → `ReadFromText`
→ `Filter`.

Fusion is blocked by:

- a **shuffle** — `GroupByKey`, `CombinePerKey`, `Reshuffle`,
  `CoGroupByKey`,
- a **side input** — the side input must be fully materialised,
- a **materialised write** — `WriteToBigQuery` with certain dispositions, and
  `WriteToText` in some modes,
- a change of **resource requirement** — one step needs many more bytes of
  memory than its neighbour.

So the difference between a good pipeline graph and a bad one is usually the
number of shuffle edges. When you look at the Job graph tab and count the
shuffle edges, you have found the cost.

### Workers and worker pools

A **worker** is one Compute Engine VM running the Beam worker harness. A
**worker pool** is the set of workers currently leased to one job.

| Concept | What it is | Where you see it |
|---|---|---|
| Worker | one VM | the `workers` table on the Job details tab |
| Worker pool | all workers for a job | the `max_workers` / `current_workers` metrics |
| Autoscaler | the controller that sizes the pool | `autoscaling_algorithm` flag, metrics tab |

The worker pool is bounded by the flags you set:

- `--min-workers` — the floor the autoscaler will not go below.
- `--max-workers` — the ceiling.
- `--autoscaling_algorithm=NONE` — the pool is fixed at `--num-workers`, and
  the autoscaler is switched off entirely.

Setting `--max-workers` too low is the most common self-inflicted Dataflow
outage. The job does not fail; it just gets slower and slower, and the
backlog grows. You need to watch the `max_workers` metric to notice.

### The Job Manager and the Streaming Job Monitor

Two different controllers, often confused.

**The Job Manager** is the per-job control plane. It validates the graph,
manages the stages, leases work, and decides when the job is done. It exists
for every job, batch and streaming.

**The Streaming Job Monitor** is a separate, continuously-running service
that watches *all* streaming jobs in a region. It exists because streaming
jobs have a failure mode the Job Manager alone cannot see: a job can be
"running" with every stage idle, because the source has stopped delivering
or because the workers have lost contact with the control plane. The
Streaming Job Monitor notices that the watermark has stopped advancing and
that no work is being processed, and it can fail the job or restart it.

The practical difference: a **batch** job that stops making progress is
usually just slow, and you leave it alone. A **streaming** job that stops
making progress is usually broken, and the monitor will fail it for you.
If your streaming job is healthy, the monitor never touches it.

### The heartbeat and the zombie job

Workers heartbeat to the Job Manager roughly every 30 seconds. The Job
Manager tracks the last heartbeat per worker. If a worker misses several
consecutive heartbeats, it is declared dead, its bundle is retried
elsewhere, and its VM is reclaimed.

The failure mode this guards against is the **zombie job**: a job whose
control plane still believes it is running, but whose workers are all gone
or wedged. Symptoms:

- `JOB_STATE_RUNNING`, but `current_workers` is 0 and `current_parallelism`
  is 0,
- the `worker_health` metric reads `0` or drops sharply,
- no new bundles are processed — the `bundle_size` counter stops moving,
- the job sits there indefinitely, billing for a worker pool that does
  nothing.

Dataflow has a **zombie job cleanup** mechanism: the service detects a job
that has been running with no activity for a long period and fails it, which
frees the workers and stops the billing. It is a safety net, not a fix. If
you see a zombie job, the question is not "how do I stop it" but "why did the
heartbeat stop" — the usual answers are a preemptible VM that was reclaimed
without notification, an expired credential, or a network policy change that
blocked the worker's outbound traffic.

### The three identities

This trips up almost everyone the first time. Three different identities are
involved in one submission.

| Identity | Who it is | What it does |
|---|---|---|
| **You** | the person or CI service account running `gcloud` | submits the job, reads the graph, cancels it |
| **Service agent** | `service-{PROJECT_NUMBER}@gcp-sa-dataflow.iam.gserviceaccount.com` | the service-level identity that the Dataflow service itself acts as; it owns the worker pool and the streaming job monitor |
| **Worker service account** | usually `dataflow-worker@PROJECT.iam.gserviceaccount.com` | what the workers themselves run as; this is the identity that reads your GCS paths, writes to BigQuery, and reads from Pub/Sub |

The **service agent** is created automatically when you enable the Dataflow
API. The **worker service account** is the one you must create and grant
roles to — and it is the one that needs
`roles/dataflow.worker`, `roles/storage.objectAdmin` (or a narrower bucket
role), and `roles/bigquery.dataEditor` on the target dataset.

The most common deployment mistake: granting permissions to the service
agent but forgetting the worker service account. The job submits happily and
then fails on the first GCS read with a `403`. See chapter 5.3's failure
table.

### Batch lifecycle vs streaming lifecycle

| | Batch | Streaming |
|---|---|---|
| Input | bounded — ends | unbounded — never ends |
| Watermark | advances to `+inf` at the end | advances as data arrives |
| Termination | automatic at `DONE` | only by cancellation |
| Autoscaler | scales up, then back down to zero | holds a steady pool, scales with traffic |
| Checkpoint | coarse; a failure means rerun | fine-grained; a failure means resume |
| Worker pool | grows during the run | persists for the life of the job |
| Idempotency | `WRITE_TRUNCATE` / `WRITE_APPEND` per run | sink must tolerate repeated windows |
| Typical duration | minutes to hours | days to months |
| Typical state | `PENDING` → `RUNNING` → `DONE` | `PENDING` → `RUNNING` → `DRAINING` → `CANCELLED` |

**A streaming job never terminates on its own.** This is not a bug and there
is no "end of stream" in Pub/Sub. A streaming Dataflow job runs until you
cancel it. If you want it to stop, you cancel it — and the way to do that in
an automated pipeline is to compare your data's event time against the
current time, not to wait for the job to finish.

### When a worker dies mid-bundle

Here is the sequence, and it is the heart of the exactly-once story.

1. Worker W is leased bundle `B` containing elements `e1..e100`.
2. W processes `e1..e40` and begins writing output for the bundle.
3. W dies — preempted, OOM-killed, machine reclaimed.
4. The Job Manager notices the missed heartbeats and declares W dead.
5. The bundle `B` is **retried** on another worker.
6. The partial output of the first attempt must not be visible.

What makes step 6 work is that Beam's sinks are **transactional with respect
to the bundle**. The output of a bundle is written to a temporary location
and only made visible (by a rename, a BigQuery load-job commit, or a
Pub/Sub publish) when the bundle commits successfully. A failed bundle's
partial output is discarded.

That is the exactly-once guarantee, and it has a precise scope:

- **Exactly once with respect to the runner.** The runner guarantees that a
  bundle's side effects are committed at most once and at least once.
- **Not exactly once with respect to your business logic.** If your
  `DoFn` writes to an external system *inside* `process()` — an HTTP call, a
  database insert, an email — that side effect is **not** covered. It will
  happen again on retry. The runner cannot roll back an HTTP request.
- **Not exactly once with respect to non-deterministic code.** If your
  transform reads a clock, calls a random number generator, or queries a
  live API, the retried bundle produces different output than the first
  attempt. The runner guarantees the *bundle* is retried; it cannot guarantee
  your code is deterministic.

The rule that follows: **side effects belong in sinks, not in `DoFn`s.**
Read from external systems inside the pipeline; write to external systems
through a Beam sink that understands bundle commits.

### The four tabs of the Dataflow UI

| Tab | What it answers | When to open it |
|---|---|---|
| **Job graph** | Where did my data go, and where did it stop? | First, always. Read the graph before touching the code. |
| **Metrics** | Is it fast, slow, or stuck? | When the graph looks right but the job does not finish. |
| **Job details** | What was the configuration, and who ran it? | When reproducing a job or auditing a run. |
| **Logs** | What exactly happened? | Last, because logs are expensive and noisy. |

#### Job graph

Shows stages as rounded boxes connected by arrows. Shuffle edges are
labelled and drawn differently from ordinary edges — **they are the edges to
look at first**. Expand a stage to see the individual steps and their
labels. The expanded view is also where fusion is visible: two steps inside
one stage box were fused, and there is no data movement between them.

The graph also shows, per stage, the parallelism actually used and the
worker instances assigned. A stage that is wide but only ever has one
instance is a stage that is not scaling.

#### Metrics

The important ones, and what a bad value looks like:

| Metric | Healthy | Bad means |
|---|---|---|
| `estimated_cpu_seconds` | rises steadily, then plateaus | flat at 0 — the job is not doing work |
| `max_workers` | grows with the backlog | pinned at the ceiling — you are capped |
| `current_workers` | tracks `max_workers` within a factor | 0 while `RUNNING` — zombie job |
| `worker_health` | 1.0 or near it | dropping — workers are being replaced |
| `bundle_size` | roughly constant | 0 — no bundles are being processed |
| `bytes_counter` | rises with throughput | flat — no data is moving |
| `input_bytes` / `output_bytes` | sum to the expected data size | a large gap — data is being dropped |

`estimated_cpu_seconds` is the cost driver. It is the number your invoice is
built from. It is also the number that tells you whether a job is worth
re-running at a different machine type.

#### Job details

The full request as submitted: template path, staging and temp locations,
region, service account, machine type, autoscaling settings, the
`--parameters` string, and the SDK version. The SDK version matters more
than it looks — see chapter 5.2.

#### Logs

Worker logs, aggregated by instance. The filter box accepts the same
expressions as `gcloud logging read`. Three things to know:

- Logs are per-worker, so a failure that only happens on one machine shows
  up once, not in every instance.
- The most useful log is usually the **first** error in a worker, not the
  last. The last error is often a cascade.
- `gcloud logging read` with the right filter is faster and more precise
  than the UI for large jobs.

---

## 🛠️ Hands-On: Reading the Architecture

This exercise needs no GCP account. It builds a graph locally, prints it,
and shows you the shape that the Dataflow UI would render.

### Inspect the graph the runner will see

```python
import apache_beam as beam

with beam.Pipeline() as p:
    orders = p | "ReadOrders" >> beam.io.ReadFromText("./sample_data/orders.csv")
    parsed = orders | "ParseOrders" >> beam.Map(lambda line: line.split(","))
    valid = parsed | "KeepValid" >> beam.Filter(lambda row: len(row) > 6)
    keyed = valid | "KeyByRegion" >> beam.Map(lambda row: (row[3], float(row[7])))
    total = keyed | "SumRevenue" >> beam.CombinePerKey(sum)

print(p)
```

The printed graph shows the **steps** with their labels. It does not show
stages — the Dataflow optimizer computes those, and only the Dataflow runner
does it. Locally, `BundleBasedDirectRunner` runs each step almost as written,
so a local run tells you nothing about fusion. This is worth stating plainly:
**you cannot see the Dataflow job graph without running on Dataflow.**

### Show the fusion boundary explicitly

```python
import apache_beam as beam


def build_pipeline() -> None:
    """Build a pipeline with a deliberate fusion boundary."""
    with beam.Pipeline() as p:
        source = p | "Read" >> beam.io.ReadFromText("./sample_data/orders.csv")
        cleaned = source | "Clean" >> beam.Map(lambda line: line.strip())
        filtered = cleaned | "Filter" >> beam.Filter(bool)
        keyed = filtered | "Key" >> beam.Map(lambda row: (row[0], row))
        _ = keyed | "Shuffle" >> beam.CombinePerKey(len)


build_pipeline()
```

`Clean` and `Filter` will fuse into one stage on Dataflow. `Key` and
`Shuffle` will not, because `CombinePerKey` introduces a shuffle edge. You
can verify the shuffle exists by reading the graph: the edge into
`Shuffle` is labelled as a shuffle.

### Count the shuffle edges

```python
import apache_beam as beam


def build_pipeline() -> None:
    """Build a pipeline whose shuffle edges are easy to count."""
    with beam.Pipeline() as p:
        source = p | "Read" >> beam.io.ReadFromText("./sample_data/orders.csv")
        keyed = source | "Key" >> beam.Map(lambda row: (row[0], row))
        _ = keyed | "Combine" >> beam.CombinePerKey(len)


build_pipeline()
```

One `CombinePerKey` means exactly one shuffle edge in the Dataflow graph. If
you ever see three `CombinePerKey` transforms in a row, you are paying for
three GCS round-trips before the data even reaches your sink.

### Check what the Dataflow runner options look like

The architecture described above is configured entirely through
`DataflowOptions`. This is the same mechanism the flex-template CLI uses
underneath, and it is worth seeing directly:

```python
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(
    [
        "--runner=DataflowRunner",
        "--project=example-data-project",
        "--region=us-central1",
        "--temp_location=gs://example-data-bucket/dataflow/temp",
        "--staging_location=gs://example-data-bucket/dataflow/staging",
        "--service_account_email=dataflow-worker@example-data-project.iam.gserviceaccount.com",
        "--machine_type=n1-standard-2",
        "--num_workers=1",
        "--autoscaling_algorithm=NONE",
    ]
)

print("runner:      ", options.runner)
print("project:     ", getattr(options, "project", None))
print("region:      ", getattr(options, "region", None))
print("machine:     ", getattr(options, "machine_type", None))
print("workers:     ", getattr(options, "num_workers", None))
print("autoscaling: ", getattr(options, "autoscaling_algorithm", None))
```

This constructs a `PipelineOptions` object without contacting Dataflow. It
is a safe way to check what a flag *would* resolve to before you spend
money discovering it the hard way.

### Read the state machine from the CLI

When you do have a project, these are the four commands that matter. They
are non-destructive and cost nothing:

```bash
# Every job in the region, newest first
gcloud dataflow jobs list \
  --project=YOUR_PROJECT_ID \
  --region=us-central1 \
  --format='table(name,state,createTime,type)' \
  --limit=10

# One job's full request and current state
gcloud dataflow jobs describe JOB_ID --project=YOUR_PROJECT_ID

# Just the state, for scripting
gcloud dataflow jobs describe JOB_ID --project=YOUR_PROJECT_ID \
  --format='value(status.state)'

# The graph, as JSON
gcloud dataflow jobs graph show JOB_ID --project=YOUR_PROJECT_ID \
  --format=json > graph.json
```

---

## 🛠️ Common Errors and Fixes

### The job is `RUNNING` but nothing is happening

```text
state: JOB_STATE_RUNNING
current_workers: 0
current_parallelism: 0
```

This is the zombie job. The control plane believes the job is running but
there are no workers. Check the logs for the worker-side exception:

```bash
gcloud logging read \
  "resource.type=cloud_dataflow_job AND resource.labels.job_id=JOB_ID AND severity>=ERROR" \
  --project=YOUR_PROJECT_ID --limit=50 --format=json
```

The usual root causes are a preemptible VM being reclaimed (use
non-preemptible for anything with a SLA), an expired service account key,
or a VPC firewall change that blocked the worker's outbound traffic.

### `Worker heartbeat failed` in the logs

```text
Worker heartbeat failed: ...
```

The worker could not reach the Job Manager's lease endpoint. This is
almost always a networking problem, not a Beam problem. Check that the
worker subnet can reach `googleapis.com` on port 443, and that the
`compute-firewall` rules for the Dataflow worker range are intact.

### `The job cannot be started because the staging location is already in use`

```text
The job cannot be started because the staging location
gs://YOUR_BUCKET/dataflow/staging is already in use by another job.
```

Two jobs submitted with the same staging location. Give every job a unique
staging path:

```bash
RUN_ID=$(date +%Y%m%d-%H%M%S)

gcloud dataflow flex-template run orders-etl \
  --project=YOUR_PROJECT_ID \
  --region=us-central1 \
  --template=gs://YOUR_BUCKET/templates/orders.py \
  --temp-location=gs://YOUR_BUCKET/dataflow/temp/$RUN_ID \
  --staging-location=gs://YOUR_BUCKET/dataflow/staging/$RUN_ID \
  --parameters="input=gs://YOUR_BUCKET/orders.csv" \
  --wait=false
```

### `PERMISSION_DENIED` on the first GCS read, but the job submitted fine

The submission identity and the worker identity are different. Your user
(or CI service account) could create the job, but the *worker service
account* cannot read the input bucket. Grant the worker account the role:

```bash
gcloud storage buckets add-iam-policy-binding gs://YOUR_BUCKET \
  --member=serviceAccount:dataflow-worker@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/storage.objectAdmin \
  --project=YOUR_PROJECT_ID
```

### The streaming job is `RUNNING` but the watermark is not advancing

Check the Streaming Job Monitor's view of the job and the source. A
Pub/Sub subscription with no publisher, a subscription whose deadline
exceeded backlog is not being drained, or an input file that stopped
growing will all produce a healthy-looking but idle job. Look at
`current_parallelism` — if it is 0, the job has nothing to do.

### `JOB_STATE_DRAINING` for a very long time

Draining is the graceful shutdown. It waits for in-flight bundles. If a
worker is wedged in a long-running `DoFn`, draining waits for it too. If
you need it gone now, cancel again with `--force` semantics, or accept the
delay — the job will be marked `CANCELLED` once the workers are reclaimed.

### The graph shows more stages than you expected

Fusion did not happen where you assumed it would. The usual reasons: a
shuffle edge, a side input, or a step whose resource requirements differ
sharply from its neighbour. Read the graph, find the edge that is labelled
as a shuffle, and that is your cost.

---

## 💡 Production Notes

- **Read the Job graph tab first, every time.** Not the logs, not the
  metrics — the graph. It tells you the shape of the computation and where
  the money goes. Logs are the third tab you open, not the first.
- **Count shuffle edges.** A shuffle edge means a full GCS write and read
  of the intermediate data. Three shuffles on a 1 TB dataset is roughly
  $40–$60 of GCS traffic plus the vCPU-hours to do it. Two `CombinePerKey`
  transforms in a row can usually be one.
- **Set `--max-workers` explicitly, and set it high.** The default ceiling
  is 20. A job that outgrows that ceiling does not fail — it just stops
  getting faster, which is far harder to notice. Set it to the number you
  would be willing to pay for, then watch the metric.
- **Understand what a "worker" costs.** A `n1-standard-2` is 2 vCPUs.
  Dataflow vCPU pricing in `us-central1` is roughly $0.056–$0.10 per
  vCPU-hour depending on commitment. One worker running for an hour on a
  standard machine is roughly $0.11–$0.20. A 100-worker job running for
  two hours is $22–$40. The number surprises people the first time.
- **Streaming jobs are a standing cost.** A streaming job that processes
  100 MB a day and holds 20 workers costs roughly $50 a day whether or not
  the data is interesting. If nobody is watching the output, cancel the job.
- **Watch `worker_health`, not `current_workers`.** `current_workers` tells
  you how many are alive; `worker_health` tells you how many are *stuck*.
  A pool at 20 workers with `worker_health` at 0.4 is a pool being rebuilt
  continuously, which costs money and produces slow, late data.
- **Preemptible VMs for batch, never for streaming.** A preemptible worker
  can be reclaimed with 30 seconds' notice. For a batch job, the bundle
  retry absorbs it. For a streaming job, it means periodic worker churn
  and a visible dip in `worker_health`.
- **The service agent is not a substitute for the worker identity.** They
  have different roles and different permissions. Granting the service
  agent `roles/editor` "to be safe" is how you end up with a security
  finding in an audit and no explanation.
- **Know your cancellation cost.** Cancelling a batch job halfway through
  still bills for the workers that ran. Cancelling a streaming job bills
  for the drain period. There is no free cancel.

---

## 🔑 Key Takeaways

- Dataflow has a **control plane** (Job Manager, autoscaler) and a **data
  plane** (workers, GCS). Most confusion is about which half owns what.
- The lifecycle is **submitted → staged → workers leased → graph executed →
  autoscaled → checkpointed → drained**, ending in `DONE`, `FAILED` or
  `CANCELLED`.
- A **step** is what you wrote; a **stage** is what the runner produced.
  Stages are the unit of parallelism and the unit of cost.
- **Fusion** merges adjacent steps and removes intermediate writes. A
  **shuffle edge** blocks fusion and is the expensive thing to look for in
  the graph.
- The **Job Manager** runs per job; the **Streaming Job Monitor** runs
  per region and catches streaming jobs that are alive but idle.
- Workers **heartbeat every ~30 seconds**. A missed heartbeat means a
  dead worker; a job with no workers is a **zombie job**, and it bills you
  for nothing.
- **Three identities**: you, the Dataflow service agent, and the worker
  service account. Permissions belong on the worker account.
- **Batch jobs end on their own. Streaming jobs never do** — you cancel
  them.
- A **dead worker mid-bundle** means the bundle is retried. Exactly-once
  covers bundle commits, not side effects inside your `DoFn`, and not
  non-deterministic code.
- The UI has **four tabs**: Job graph, Metrics, Job details, Logs — read
  them in that order.

---

## 📚 Practice Exercises

1. **Map the lifecycle to the CLI.** Write the exact sequence of
   `gcloud dataflow` commands that observes a job from submission to
   completion: one command to submit, one to poll the state, one to pull
   the graph, one to pull the metrics. Then describe what each command
   would show at `PENDING`, at `RUNNING`, and at `DONE`.

2. **Count the stages.** Take the course batch pipeline
   (`project/batch_pipeline.py`) and, by hand, draw the Dataflow job graph
   it would produce. Mark every shuffle edge. Then change the pipeline so
   that the two aggregations share a single shuffle, and explain why the
   new graph is cheaper.

3. **Explain a zombie job.** A job has been `RUNNING` for four hours.
   `current_workers` is 0, `current_parallelism` is 0, and `estimated_cpu_seconds`
   has not moved. Answer in one paragraph: what does Dataflow do about it,
   what does it cost you, and what are the three most likely causes?

4. **Design the retry.** You have a `DoFn` that calls a payment-gateway
   HTTP API, and the worker dies half-way through a bundle. Explain, step
   by step, what happens to the API call. Then rewrite the design so the
   guarantee is meaningful, and say what the new failure mode is.

5. **Batch vs streaming table.** Fill in a table with these rows: watermark
   end, worker pool lifetime, checkpoint granularity, termination
   condition, behaviour on worker death, and the sink's idempotency
   requirement. Justify each answer with the lifecycle from this chapter,
   not from intuition.

6. **Inspect the graph JSON.** On a real project, run
   `gcloud dataflow jobs graph show JOB_ID --format=json` and write a
   small Python script that reads the JSON and prints, for each stage, the
   number of steps it contains and whether it is preceded by a shuffle
   edge. The script should work on any job's graph JSON.

---

## 📖 Further Reading

- Google Cloud Dataflow overview — https://cloud.google.com/dataflow/docs/about-dataflow
- Dataflow job lifecycle and states — https://cloud.google.com/dataflow/docs/guides/job-lifecycle
- Dataflow monitoring and operations — https://cloud.google.com/dataflow/docs/guides/monitoring
- Dataflow autoscaling — https://cloud.google.com/dataflow/docs/guides/autoscaling
- Dataflow worker impact and machine types — https://cloud.google.com/dataflow/docs/guides/worker-impact
- Apache Beam: Execution Model — https://beam.apache.org/documentation/runtime/model/
