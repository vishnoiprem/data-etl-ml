# 5.3 — Executing a Batch Job

> **Section 5 · Dataflow Templates & Deployment · Lecture 5.3 · 6:30**

## 🎯 What you will learn

- `gcloud dataflow flex-template run` and every flag it accepts
- The required flags and what happens when you omit one
- Why concurrent jobs collide on staging, and how to prevent it
- `--wait` versus `--wait=false`
- Worker sizing: `--worker-machine-type`, `--max-workers`, `--min-workers`
- `--autoscaling_algorithm`: `NONE`, `Basic`, `Aggressive`
- `--region` and why the data's location matters
- The job state machine, and how to read it from the CLI
- Reading logs with `gcloud logging read`
- The metrics worth watching, and what a bad value means
- The common failure modes and their first-line fixes

---

## 🧠 Concept

### The command and its shape

```bash
gcloud dataflow flex-template run JOB_NAME \
  --project=YOUR_PROJECT_ID \
  --region=us-central1 \
  --template=gs://YOUR_BUCKET/templates/orders-etl.py \
  --temp-location=gs://YOUR_BUCKET/dataflow/temp \
  --staging-location=gs://YOUR_BUCKET/dataflow/staging \
  --service-account=dataflow-worker@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --parameters="input=gs://YOUR_BUCKET/orders.csv,output=gs://YOUR_BUCKET/summary" \
  --wait=false
```

Read the shape as three groups:

1. **Identity** — `--project`, `--region`. Where the job lives.
2. **Infrastructure** — `--template`, `--temp-location`,
   `--staging-location`, `--service-account`. What it runs on and with what
   permissions.
3. **Payload** — `--parameters`. What it computes.

The `JOB_NAME` is a positional argument, not a flag. It is the display name
in the Dataflow console. It does not have to be unique — the API assigns the
actual job ID — but it should be, because that is what your operators will
search for.

### The required flags, and what each one is really for

| Flag | Why it is required |
|---|---|
| `--project` | the project that owns the job, the staging bucket, and the billing account |
| `--region` | where the workers run, and therefore which Dataflow service handles the job |
| `--template` | the GCS path of the worker script |
| `--temp-location` | scratch space for shuffle and side-input files |
| `--staging-location` | staged metadata and streaming checkpoints |
| `--service-account` | the identity the workers run as |

`--temp-location` and `--staging-location` are required for a *reason*, and
it is worth knowing what that reason is.

- **Temp location** is where the data plane writes intermediate results:
  shuffle files, side-input materialisations, and the temp files the
  BigQuery and GCS sinks use before committing. It is a *data* path.
  It needs a lot of space and it is deleted (eventually) by the service.
- **Staging location** is where the control plane writes the job's staged
  metadata and, for streaming jobs, the periodic checkpoints. It is a
  *state* path. Deleting it while a job runs is how you get a job that
  cannot be drained cleanly.

They can point at the same bucket under different prefixes, and that is
normal. They must not be the same *prefix* if you run concurrent jobs.

### The staging collision

This is the failure that catches every team exactly once.

```text
ERROR: (gcloud.dataflow.flex-template.run) The job cannot be started
because the staging location gs://YOUR_BUCKET/dataflow/staging is already
in use by another job.
```

The mechanism: the Dataflow service writes the staged job metadata — the
serialised pipeline, the options, the worker configuration — into the
staging location under a path derived from the job. If two jobs use the
same location and their staging writes overlap, the second job either
fails outright or, worse, picks up the first job's staged metadata and
behaves in a confusing way.

There is no way to make the default location safe, because the default is
fixed per bucket and per region. The fix is to make the path unique per
job. The standard pattern:

```bash
RUN_ID=$(date +%Y%m%d-%H%M%S)
STAGING=gs://YOUR_BUCKET/dataflow/staging/$RUN_ID
TEMP=gs://YOUR_BUCKET/dataflow/temp/$RUN_ID
```

For scheduled jobs, use the schedule's own identity in the path, so two
instances of the same schedule do not collide:

```bash
RUN_ID=$(date +%Y%m%d-%H%M%S)
STAGING=gs://YOUR_BUCKET/dataflow/staging/scheduled-$RUN_ID
```

And if you want a job to be reproducible, put the *data* identity in the
path instead of the wall clock:

```bash
RUN_ID=$(date +%Y%m%d)          # one per day, not one per launch
STAGING=gs://YOUR_BUCKET/dataflow/staging/daily-$RUN_ID
```

### `--wait` versus `--wait=false`

By default, `gcloud dataflow flex-template run` **blocks** until the job
finishes, and streams the worker logs to your terminal.

| | `--wait` (default) | `--wait=false` |
|---|---|---|
| Terminal | blocked, logs streaming | returns immediately with the job ID |
| Output | the job's final state and a log dump | the job ID and a success message |
| Good for | interactive runs, small jobs | CI, orchestration, anything you script |
| Risk | your terminal session is tied up for hours | you have to poll for the result yourself |

The default is a trap in a script. If you write a shell script that runs a
six-hour batch job without `--wait=false`, the script blocks for six hours
and your CI runner burns six hours of wall-clock time. Every scripted
invocation should pass `--wait=false` and then poll explicitly — which
gives you control over the timeout, the poll interval, and the failure
handling.

The `$?` exit code also differs. With `--wait` (the default), `gcloud`
exits non-zero if the job fails. With `--wait=false`, it exits zero if the
*submission* succeeded — which says nothing about whether the *job* later
failed. This is the most important trap in the whole command surface, and
chapter 5.6 covers how to script around it.

### Worker sizing

```bash
--worker-machine-type=n1-standard-2 \
--max-workers=20 \
--min-workers=1
```

Note the flag name carefully: the CLI flag is `--worker-machine-type`, while
the *Python SDK* option is `--machine_type`. This is a genuine inconsistency
in the Dataflow surface, and it is a common source of "the flag was
ignored" reports.

| Machine type | vCPUs | RAM | Good for |
|---|---|---|---|
| `n1-standard-1` | 1 | 3.75 GB | tiny inputs, I/O-bound work |
| `n1-standard-2` | 2 | 7.5 GB | the sensible default |
| `n1-standard-4` | 4 | 15 GB | CPU-bound transforms, large side inputs |
| `n1-standard-8` | 8 | 30 GB | heavy aggregation, wide shuffles |
| `n1-highmem-4` | 4 | 26 GB | large in-memory state, sorting |
| `n2-standard-4` | 4 | 16 GB | better price/performance, newer instances |
| `e2-standard-4` | 4 | 16 GB | cheapest; good for bursty batch |

The vCPU-to-RAM ratio is fixed at 4 GB per vCPU for the `standard` family.
A `CombinePerKey` that materialises a large group in memory will OOM on a
`n1-standard-2` and succeed on a `n1-highmem-8`. If your job is dying with
`OutOfMemoryError`, the machine type is the first thing to change.

`--min-workers` sets the floor the autoscaler will not go below. `--max-workers`
sets the ceiling. Both matter, and the defaults are conservative: min 0 (for
batch) or 1 (for streaming), max 20.

### `--autoscaling_algorithm`

Three values, and the difference between them is significant.

| Value | Behaviour | Use when |
|---|---|---|
| `NONE` | no autoscaling; the pool is fixed at `--num-workers` | small, predictable batch jobs; streaming jobs where you want a fixed pool |
| `Basic` | scales up and down based on CPU utilisation and backlog | most batch jobs — **the default** |
| `Aggressive` | scales up faster and stays up longer | bursty inputs, jobs with a short high-load phase |

`NONE` and `--num-workers` are a pair. If you set `--autoscaling_algorithm=NONE`
without `--num-workers`, you get the service default — which is not what
most people mean.

```bash
# Fixed pool of 1 worker — perfect for a 50 MB nightly job
gcloud dataflow flex-template run orders-etl \
  --project=YOUR_PROJECT_ID --region=us-central1 \
  --template=gs://YOUR_BUCKET/templates/orders-etl.py \
  --temp-location=gs://YOUR_BUCKET/dataflow/temp \
  --staging-location=gs://YOUR_BUCKET/dataflow/staging \
  --service-account=dataflow-worker@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --autoscaling_algorithm=NONE \
  --num_workers=1 \
  --worker-machine-type=n1-standard-2 \
  --wait=false
```

`Aggressive` is worth understanding precisely: it keeps workers around
longer after a spike, and it scales up more eagerly. For a job whose load
comes in bursts — a nightly job that processes a big file for 10 minutes
then idles — `Aggressive` gets you the workers faster. The cost is that
idle workers keep billing. `Aggressive` on a job that idles for 20 hours
between runs is an expensive mistake.

A subtlety worth knowing: with `Basic` and `Aggressive`, Dataflow starts
with a small pool and scales up. The ramp-up is not instant. A job with a
20-minute runtime and a 5-minute ramp spends 25% of its life in the ramp.
For a job that is short and predictable, `NONE` with an explicit worker
count is often *both* faster and cheaper than letting the autoscaler work.

### `--region` and where the data lives

`--region` determines:

- which Dataflow service endpoint handles the job,
- where the workers are provisioned,
- which regional service account and quota apply,
- which regional BigQuery and Cloud Storage resources you can reach without
  a cross-region hop.

The last point is the one that costs money. Dataflow workers in
`europe-west1` reading a bucket in `us-central1` pay for cross-region
egress on every byte. Reading 100 GB across regions costs roughly $10–$20
in egress, on top of the vCPU-hours, and it is 2–5× slower than a
regional read.

The rules:

- **Put the workers where the data is.** If the data is in
  `europe-west1`, run the job in `europe-west1`.
- **Put the workers where the consumers are**, if the data is not
  co-located with either. Regional data residency rules (GDPR, for
  instance) make this a legal requirement, not a preference.
- **Do not run a single job across regions.** Each region is a separate
  job with its own workers, its own staging, and its own bill.

### The job state machine

```text
JOB_STATE_UNKNOWN
        │
        ▼
JOB_STATE_PENDING     graph validated, staging written, workers requested
        │
        ▼
JOB_STATE_RUNNING     workers leased, stages executing
        │
        ├──► JOB_STATE_DRAINING  ──► JOB_STATE_DONE
        │
        ├──► JOB_STATE_FAILED
        │
        └──► JOB_STATE_CANCELLED
```

From the CLI:

```bash
gcloud dataflow jobs describe JOB_ID --project=YOUR_PROJECT_ID \
  --format='value(status.state)'
```

The states you will actually see in practice, and what each one means for
your monitoring:

| State | Meaning | What to do |
|---|---|---|
| `PENDING` | not started yet | wait; if it stays here for >5 min, check the service agent and the API |
| `RUNNING` | executing | watch the metrics |
| `DRAINING` | finishing in-flight work | wait |
| `DONE` | succeeded | verify the output |
| `FAILED` | the job failed | read the logs; the first error is the real one |
| `CANCELLED` | you cancelled it | check whether it was supposed to be cancelled |
| `CANCELLING` | cancellation requested, drain in progress | wait for `CANCELLED` |
| `UPDATED` | the job's metadata changed | usually benign — a label edit |
| `JOB_STATE_UNKNOWN` | the API has no record | wrong job ID, or wrong project |

A `FAILED` job's `status.state` is not the interesting part. The interesting
part is in `status.state` plus the *terminal* state details:

```bash
gcloud dataflow jobs describe JOB_ID --project=YOUR_PROJECT_ID --format=json \
  | jq '.status'
```

### Reading the logs

The Dataflow UI's Logs tab is a browser over Cloud Logging. The CLI is
faster, scriptable, and works when the console is down.

```bash
# Everything the job logged
gcloud logging read \
  "resource.type=cloud_dataflow_job AND resource.labels.job_id=JOB_ID" \
  --project=YOUR_PROJECT_ID --limit=200

# Just the errors
gcloud logging read \
  "resource.type=cloud_dataflow_job AND resource.labels.job_id=JOB_ID AND severity>=ERROR" \
  --project=YOUR_PROJECT_ID --limit=50

# Just the worker harness lines, no application noise
gcloud logging read \
  "resource.type=cloud_dataflow_job AND resource.labels.job_id=JOB_ID AND textPayload:\"worker\"" \
  --project=YOUR_PROJECT_ID --limit=100

# The last 20 lines, which usually contain the traceback
gcloud logging read \
  "resource.type=cloud_dataflow_job AND resource.labels.job_id=JOB_ID AND severity>=ERROR" \
  --project=YOUR_PROJECT_ID --limit=20 --sort-by="~timestamp"
```

The `--sort-by="~timestamp"` matters. The default sort is ascending, so
`--limit=50` gives you the *oldest* 50 lines — which for a job that failed
after an hour are the least useful ones. You almost always want the newest
first.

To see the traceback specifically, filter for the Python stack frames:

```bash
gcloud logging read \
  "resource.type=cloud_dataflow_job AND resource.labels.job_id=JOB_ID AND severity>=ERROR" \
  --project=YOUR_PROJECT_ID --limit=10 --sort-by="~timestamp" --format=json \
  | jq -r '.[] | .textPayload // (.jsonPayload | tostring)'
```

### The metrics worth watching

The Metrics tab is where you diagnose "the job is running but it is
wrong". The metrics that matter, in priority order:

#### `estimated_cpu_seconds`

The primary cost driver, and the number your invoice is built from. It rises
while workers are busy and plateaus when the job is waiting on I/O.

- **Rising steadily** → healthy.
- **Flat at zero** → the job is doing no work. Almost always the source
  produced nothing, or every stage is stuck.
- **Growing while `bundle_size` is flat** → workers are spinning without
  making progress.

One `estimated_cpu_second` is one vCPU-second. Multiply by the hourly rate
(roughly $0.056–$0.10 per vCPU-hour in `us-central1`) and divide by 3600
to get the cost. A job that used 3,600 `estimated_cpu_seconds` cost about
$0.06–$0.10.

#### `max_workers` and `current_workers`

`max_workers` is the size of the pool. `current_workers` is how many are
alive.

- `max_workers` pinned at the ceiling for a long time → you are capped.
  Raise the ceiling or the job will not finish faster.
- `current_workers` at 0 while `RUNNING` → zombie job.
- `current_workers` oscillating wildly → the autoscaler is thrashing. Check
  the machine type; a worker that is too small for the work looks idle and
  gets replaced, which looks like thrashing.

#### `worker_health`

The fraction of workers that are actually healthy. It should sit at 1.0.

- Below 0.9 → workers are being replaced. If this is constant, you are
  paying for churn: the job runs, the worker dies, the bundle is retried,
  the job runs again.
- Below 0.5 → something is actively killing workers. Look for OOM kills,
  preemptions, or a crash in your `DoFn`.

#### `bundle_size`

The number of elements per bundle. It is a proxy for throughput.

- Steady → healthy.
- Dropping to 0 → no bundles are being processed.
- Very small → your bundles are tiny and you are paying per-bundle overhead
  rather than per-element. This happens when a `DoFn` filters out almost
  everything: Beam keeps the bundle structure but the work is trivial.

#### `bytes_counter` and `input_bytes` / `output_bytes`

Data movement.

- `input_bytes` should roughly match the size of your input. If it is zero,
  the source never ran.
- `bytes_counter` flat while `RUNNING` → the data plane is stuck.
- A large `input_bytes` / `output_bytes` gap → data is being dropped, which
  is a bug in your pipeline, not a configuration problem.

#### `system_lag` and `current_parallelism` (streaming)

Only meaningful for streaming.

- `system_lag` is how far behind real time the job is. A `system_lag` that
  grows without bound means the job cannot keep up.
- `current_parallelism` is how many bundles are in flight. At 0 with a
  healthy source, the job is idle or broken.

### Common failure modes

A catalogue of what actually goes wrong, with the first thing to check.

| Symptom | Cause | First check |
|---|---|---|
| Fails in 5–30 seconds with a permission error | the worker service account lacks a role | `gcloud projects get-iam-policy` / `add-iam-policy-binding` |
| Fails with `FileNotFoundError` on the worker | `--template` path is wrong, or the file is not in GCS | `gcloud storage ls gs://YOUR_BUCKET/templates/` |
| Fails with `ModuleNotFoundError` | the template imports a module that was not shipped | add it to `--py-files` |
| Fails with `AttributeError` on a Beam API | SDK version mismatch, or you bundled Beam | check `sdkSupportStatus` |
| Fails with `Can't pickle __main__.X` | `save_main_session` is off and you use a `DoFn` class | add `--save_main_session=True` |
| Fails with "staging location already in use" | concurrent jobs, same staging path | unique path per run |
| `RUNNING` for hours, `current_workers` 0 | zombie job | worker logs; check for preemptions |
| `RUNNING` forever, `max_workers` at ceiling | you are capped | raise `--max-workers` |
| `FAILED` with `OutOfMemoryError` | the machine is too small for the group being materialised | raise the machine type, or use `CombinePerKey` over `GroupByKey` |
| `FAILED` with a `403` on BigQuery | the worker SA lacks `roles/bigquery.dataEditor` | grant it on the dataset |
| Succeeds but the output is empty | the source produced nothing, or a filter dropped everything | check `input_bytes` and the filter |
| Succeeds but the output has duplicates | the sink was `WRITE_APPEND` and the job ran twice | use `WRITE_TRUNCATE` for a full refresh |
| Very slow, `bundle_size` tiny | bundles too small, or heavy per-element overhead | check the `DoFn` for per-element network calls |

---

## 🛠️ Hands-On: Run a Batch Job

### Generate the input

```bash
cd data-engineering/data-Course/google/Dataflow

python resources/sample_data.py --output-dir ./sample_data

wc -l sample_data/orders.csv
head -3 sample_data/orders.csv
```

### Run the pipeline locally first — always

Before you spend a cent, run the same pipeline with the local runner. The
course default is `BundleBasedDirectRunner`, so this needs no credentials.

```bash
python project/batch_pipeline.py \
  --input=./sample_data/orders.csv \
  --output=./out/batch_local
```

Check the output:

```bash
ls -la out/batch_local*
head -5 out/batch_local*
wc -l out/batch_local*
```

The exact filename has a shard suffix. Never hard-code it.

### Submit the same job to Dataflow

Now the real thing. Set the variables once:

```bash
export PROJECT=YOUR_PROJECT_ID
export REGION=us-central1
export BUCKET=YOUR_BUCKET
export TEMPLATE=gs://$BUCKET/templates/orders-etl.py
export RUN_ID=$(date +%Y%m%d-%H%M%S)
```

Upload the template and run it:

```bash
gcloud dataflow flex-template build orders-etl \
  --project=$PROJECT \
  --region=$REGION \
  --template-file=./project/templates/batch_template.py \
  --template-file-gcs-path=$TEMPLATE \
  --metadata="version=1.0.0,owner=data-platform" \
  --temp-location=gs://$BUCKET/dataflow/temp \
  --staging-location=gs://$BUCKET/dataflow/staging \
  --service-account=dataflow-worker@$PROJECT.iam.gserviceaccount.com

gcloud dataflow flex-template run orders-etl \
  --project=$PROJECT \
  --region=$REGION \
  --template=$TEMPLATE \
  --temp-location=gs://$BUCKET/dataflow/temp/$RUN_ID \
  --staging-location=gs://$BUCKET/dataflow/staging/$RUN_ID \
  --service-account=dataflow-worker@$PROJECT.iam.gserviceaccount.com \
  --parameters="input=gs://$BUCKET/orders.csv,output=gs://$BUCKET/summary/$RUN_ID,statuses=complete" \
  --worker-machine-type=n1-standard-2 \
  --max-workers=10 \
  --min-workers=1 \
  --autoscaling_algorithm=Basic \
  --wait=false
```

Note the unique `$RUN_ID` in both the staging and temp paths, and in the
output path.

### Capture the job ID and poll it

The submission prints the job ID. Capture it programmatically:

```bash
JOB_ID=$(gcloud dataflow flex-template run orders-etl \
  --project=$PROJECT --region=$REGION \
  --template=$TEMPLATE \
  --temp-location=gs://$BUCKET/dataflow/temp/$RUN_ID-2 \
  --staging-location=gs://$BUCKET/dataflow/staging/$RUN_ID-2 \
  --service-account=dataflow-worker@$PROJECT.iam.gserviceaccount.com \
  --parameters="input=gs://$BUCKET/orders.csv,output=gs://$BUCKET/summary/$RUN_ID-2" \
  --wait=false \
  --format='value(job.id)')

echo "job: $JOB_ID"
```

Poll it:

```bash
gcloud dataflow jobs describe $JOB_ID --project=$PROJECT --format='value(status.state)'

gcloud dataflow jobs list \
  --project=$PROJECT --region=$REGION \
  --filter='state=RUNNING' \
  --format='table(name,state,createTime)'
```

### Read the metrics while it runs

```bash
gcloud dataflow jobs describe $JOB_ID --project=$PROJECT --format=json \
  | jq '.metrics | {
           cpu: .estimatedCpuSeconds,
           max_workers: .maxWorkers,
           current_workers: .currentWorkers,
           worker_health: .workerHealth,
           bundle_size: .bundleSize,
           bytes: .bytesCounter
         }'
```

### Read the logs

```bash
# The newest errors first
gcloud logging read \
  "resource.type=cloud_dataflow_job AND resource.labels.job_id=$JOB_ID AND severity>=ERROR" \
  --project=$PROJECT --limit=20 --sort-by="~timestamp" \
  --format='value(textPayload)'

# The last few lines of the job log
gcloud logging read \
  "resource.type=cloud_dataflow_job AND resource.labels.job_id=$JOB_ID" \
  --project=$PROJECT --limit=20 --sort-by="~timestamp" \
  --format='value(textPayload)'
```

### Verify the output

```bash
gcloud storage ls gs://$BUCKET/summary/$RUN_ID/

gcloud storage cat gs://$BUCKET/summary/$RUN_ID/* | head -10

# Compare the row count against the local run
gcloud storage cat gs://$BUCKET/summary/$RUN_ID/* | wc -l
```

The counts should match the local run exactly. If they do not, the
difference is in the input, not in Dataflow — check that the GCS input is
the same file you ran locally.

### Cancel a job that should not be running

```bash
gcloud dataflow jobs cancel $JOB_ID --project=$PROJECT

# Confirm it actually stopped
gcloud dataflow jobs describe $JOB_ID --project=$PROJECT --format='value(status.state)'
```

The state goes `CANCELLING` → `CANCELLED` after the drain. A job that sits
in `CANCELLING` for a long time has a worker wedged in a long `DoFn`.

---

## 🛠️ Common Errors and Fixes

### `The job cannot be started because the staging location ... is already in use`

```text
ERROR: (gcloud.dataflow.flex-template.run) The job cannot be started
because the staging location gs://YOUR_BUCKET/dataflow/staging is already
in use by another job.
```

Two jobs, one staging path. Add a unique suffix:

```bash
RUN_ID=$(date +%Y%m%d-%H%M%S)
--staging-location=gs://YOUR_BUCKET/dataflow/staging/$RUN_ID
--temp-location=gs://YOUR_BUCKET/dataflow/temp/$RUN_ID
```

### `PERMISSION_DENIED: User ... does not have permission to access bucket`

```text
Permission 'storage.objects.get' denied on resource
'gs://YOUR_BUCKET/orders.csv' (or it may not exist)
```

The worker service account cannot read the input. Grant it:

```bash
gcloud storage buckets add-iam-policy-binding gs://YOUR_BUCKET \
  --member=serviceAccount:dataflow-worker@$PROJECT.iam.gserviceaccount.com \
  --role=roles/storage.objectAdmin \
  --project=$PROJECT
```

### `The Dataflow service account ... does not have permission to create jobs`

The **service agent** is missing a role. It normally has
`roles/dataflow.serviceAgent`. Check with:

```bash
gcloud projects get-iam-policy $PROJECT \
  --flatten="bindings[].members" \
  --filter="bindings.members:service-$PROJECT_NUMBER@gcp-sa-dataflow.iam.gserviceaccount.com" \
  --format='table(bindings.role)'
```

### `PERMISSION_DENIED: ... does not have permission to create a query job`

The worker SA cannot write to BigQuery:

```bash
gcloud projects add-iam-policy-binding $PROJECT \
  --member=serviceAccount:dataflow-worker@$PROJECT.iam.gserviceaccount.com \
  --role=roles/bigquery.dataEditor \
  --project=$PROJECT
```

### `AttributeError: module 'apache_beam' has no attribute 'io'`

Two possible causes:

1. The SDK version on the worker is older than the code.
2. **You bundled apache-beam** with `--py-files` or a wheel, and your copy
   shadows the service's.

Check the version, and remove every bundled copy:

```bash
gcloud dataflow jobs describe JOB_ID --project=$PROJECT \
  --format='value(environment.sdkSupportStatus)'
```

### `ModuleNotFoundError: No module named 'transforms'`

The template imports a module that was not shipped:

```bash
gcloud dataflow flex-template build orders-etl \
  --template-file=./project/templates/batch_template.py \
  --template-file-gcs-path=$TEMPLATE \
  --py-files=./project/transforms.py \
  ...
```

Or inline the shared code into the template file.

### The job runs but the output is empty

Check the metrics in this order:

```bash
gcloud dataflow jobs describe JOB_ID --project=$PROJECT --format=json \
  | jq '.metrics | {input_bytes: .inputBytes, elements: .elements, bundles: .bundles}'
```

`input_bytes` at 0 means the source never ran — usually a bad input path.
`input_bytes` non-zero but `elements` at 0 means a filter dropped
everything.

### The job is slow and `max_workers` is pinned at the ceiling

You are capped. Raise `--max-workers`. But check the cost first: a job that
uses 100 workers for an hour costs roughly $11–$20 in `us-central1`. A
slow job is usually a shuffle problem, not a worker-count problem — read the
job graph before adding workers.

### `gcloud` hangs after submitting

You forgot `--wait=false`. The default is to block. Ctrl-C out; the job
keeps running. Cancel it explicitly if that is not what you want.

### `OutOfMemoryError` in a `CombinePerKey`

The group is being materialised in memory on a worker that is too small.
Options, in order of preference:

1. Use a proper `CombineFn` with a compact accumulator instead of
   `GroupByKey`.
2. Raise the machine type (`--worker-machine-type=n1-highmem-8`).
3. Reduce the group size by adding a finer key.

---

## 💡 Production Notes

- **Run locally first, every time.** The local runner costs nothing and
  catches syntax errors, missing modules, and logic bugs. A Dataflow job
  that fails in 40 seconds after a 30-second staging phase has wasted two
  minutes and your attention.
- **Always use `--wait=false` in a script.** And then poll. The default
  blocking behaviour is the single most common cause of a CI pipeline that
  appears to hang.
- **Make staging and temp paths unique per run.** Use a timestamp, a UUID,
  or the data's identity. The one case where sharing a path is correct is
  a *re-run of the same logical job* — and even then, prefer a fresh path
  and clean up afterwards.
- **Set `--max-workers` to what you would be willing to pay for**, not
  what you hope you need. 20 workers on `n1-standard-2` for an hour is
  about $2.20. 100 workers is about $11.
- **Consider `NONE` for small batch jobs.** A nightly job over 50 MB does
  not need autoscaling; it needs one worker and no ramp-up. `NONE` with
  `--num-workers=1` is often both faster and cheaper than `Basic`.
- **Match the machine type to the work, not to the data.** The data size
  does not determine the machine type; the working set does. A
  `CombinePerKey` over 1 GB groups needs `highmem`; a filter over a 1 TB
  file does not.
- **Put the job in the same region as the data.** Cross-region reads cost
  egress and take 2–5× longer. This is a routine money leak in
  organisations with several regions.
- **Keep a lifecycle rule on the temp and staging prefixes.** They
  accumulate. A `gsutil`/`gcloud storage` lifecycle rule that deletes
  objects under `dataflow/temp/` after 7 days is two lines of JSON and
  prevents a surprise storage bill.
- **Watch `worker_health` in the first 30 days of running a new pipeline.**
  A pipeline that produces correct output but churns workers is quietly
  burning budget and producing late data.
- **Cancel jobs you did not mean to start.** A batch job that should take
  20 minutes and has been running for 4 hours is a configuration bug, and
  it is billing every second you leave it alone.

---

## 🔑 Key Takeaways

- `gcloud dataflow flex-template run` takes an identity group
  (`--project`, `--region`), an infrastructure group (`--template`,
  `--temp-location`, `--staging-location`, `--service-account`), and a
  payload group (`--parameters`).
- **Staging and temp locations must be unique per concurrent job.** The
  default location collides and the error message does not explain why.
- **`--wait=false` in every script.** The default blocks, and with it the
  exit code reports the job's fate rather than the submission's.
- Worker sizing is `--worker-machine-type`, `--max-workers`, `--min-workers`
  — note the CLI flag differs from the SDK's `--machine_type`.
- `--autoscaling_algorithm` is `NONE`, `Basic` or `Aggressive`. `NONE`
  pairs with `--num-workers`; `Aggressive` is for bursty loads and is
  expensive on jobs that idle.
- **Put the workers where the data is.** Cross-region reads cost egress
  and 2–5× latency.
- The state machine is `PENDING` → `RUNNING` → `DONE` / `FAILED` /
  `CANCELLED`, with `DRAINING` in between.
- Read logs with `gcloud logging read` and **`--sort-by="~timestamp"`** —
  the default sort gives you the oldest lines, which are rarely the ones
  you need.
- The metrics that matter are `estimated_cpu_seconds`, `max_workers`,
  `current_workers`, `worker_health`, `bundle_size` and `bytes_counter`.

---

## 📚 Practice Exercises

1. **Build a submission script.** Write
   `scripts/run_batch_job.sh` that takes the input and output paths as
   arguments, generates a unique `RUN_ID`, submits with `--wait=false`,
   captures the job ID, polls every 30 seconds, and exits non-zero if the
   job reaches `FAILED` or `CANCELLED`. Test it against a deliberately
   bad input path and confirm it exits non-zero.

2. **Find the cost of a job.** Pick a completed job. Read
   `estimated_cpu_seconds` from the metrics. Convert it to a dollar figure
   using the regional vCPU-hour rate. Then compute the same job's GCS and
   BigQuery costs from the storage and BigQuery billing exports. Write down
   the total and the percentage each component contributes.

3. **Diagnose a capped job.** A job has been `RUNNING` for 40 minutes with
   `max_workers` at 20 and `current_workers` at 20. Explain, in three
   sentences, why it is not finishing faster, what the graph might look
   like, and what you would change first — the worker count or the
   pipeline.

4. **Worker sizing experiment.** Run the same job three times: on
   `n1-standard-1` with `NONE`/`--num-workers=1`, on `n1-standard-4` with
   `NONE`/`--num-workers=1`, and on `n1-standard-2` with `Basic` and
   `--max-workers=10`. Record wall-clock time and `estimated_cpu_seconds`
   for each. Explain why the cheapest job in wall-clock terms is not
   necessarily the cheapest in money.

5. **Region placement.** A bucket lives in `europe-west1` and a BigQuery
   dataset lives in `us-central1`. A job runs in `us-central1`. Draw the
   data path, identify the cross-region hop, and estimate the cost of
   moving 500 GB. Then decide where the job should run and what that
   changes about the BigQuery write.

6. **Failure triage table.** Produce a one-page runbook: a table of
   symptom → likely cause → exact command to confirm → exact command to
   fix. Cover at least: permission denied, module not found, staging
   collision, empty output, OOM, and the zombie job.

---

## 📖 Further Reading

- Google Cloud Dataflow: create a Dataflow job with gcloud — https://cloud.google.com/dataflow/docs/guides/getting-started-pipelines
- Google Cloud Dataflow: pipeline options — https://cloud.google.com/dataflow/docs/guides/pipeline-options
- Google Cloud Dataflow: worker impact and machine types — https://cloud.google.com/dataflow/docs/guides/worker-impact
- Google Cloud Dataflow: autoscaling — https://cloud.google.com/dataflow/docs/guides/autoscaling
- Google Cloud Logging query language — https://cloud.google.com/logging/docs/view/query-language
- Apache Beam: Beam SDKs — https://beam.apache.org/documentation/sdks/python/
