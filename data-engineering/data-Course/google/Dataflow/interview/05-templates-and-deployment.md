# Module 5 — Templates & Deployment

> **14 questions · Module 5 · Templates & Deployment**

---

## The Dataflow service

### 1. What actually happens between `gcloud dataflow jobs run` and the first row of output?

The command does four things and then returns: it uploads your pipeline to the **staging location** in GCS, asks the Dataflow control plane to create a **Dataflow job** resource, the service spins up **workers** in the chosen region, and those workers pull your code from staging and execute it. The control plane never touches your data — it only schedules the graph. Data movement happens between the workers and your sources/sinks, through GCS, Pub/Sub or BigQuery.

The part that bites people is that job creation is *asynchronous*. `gcloud dataflow jobs run` returns as soon as the job resource exists; the job may sit in `JOB_STATE_PENDING` for 30–90 seconds before a worker is even assigned, because Compute Engine capacity in the region has to be available. If you script `run` followed immediately by `logs tail`, you will often tail a job that has not started. The standard fix is to poll `gcloud dataflow jobs describe JOB_ID --format='value(status.state)'` until it reports `JOB_STATE_RUNNING` before you attach to it.

A production failure I have seen: a CI job that ran `gcloud dataflow jobs run` and then immediately read the output prefix in GCS. Because the job was still `PENDING`, the prefix did not exist and the CI step failed with a 404 — not a pipeline bug at all. The pipeline succeeded 40 seconds later.

### 2. What does the Dataflow service agent actually do, and why does it need its own identity?

The **service agent** (`service-<PROJECT_NUMBER>@gcp-sa-dataflow.iam.gserviceaccount.com`) is the identity the Dataflow control plane uses to create and manage Compute Engine VMs, set up the VPC networking, and read/write the staging and temp locations in GCS. It is *not* the identity your Beam code runs as.

The distinction matters because the two identities need different permissions, and giving one the other's roles creates a security problem. The service agent needs `roles/dataflow.serviceAgent` plus `roles/storage.objectAdmin` on the staging/temp bucket. Your **worker service account** needs `roles/dataflow.worker` plus read/write on your actual data. If you collapse them, the worker gets Compute Engine administrative rights it has no business holding.

The classic papercut: Dataflow creates the service agent automatically on first job submission, and it caches the IAM policy *at creation time*. Adding `roles/storage.objectAdmin` afterwards does nothing until you delete the service agent and let Dataflow recreate it. Creating it by hand with the right roles up front — as `resources/SETUP.md` does — avoids a two-hour debugging session that ends with `403 storage.objects.get` on the very first job.

### 3. What is a flex template, and what is it explicitly not?

A **flex template** is a Python file (or a container image) that Dataflow executes on the worker. You upload it to GCS once, then launch it by pointing `--template` at the GCS path and passing runtime arguments with `--parameters`. The template file itself is the pipeline; there is no separate staging job and no "create template, then launch template" two-step.

What it is *not*: it is not a classic **Dataflow template**. Classic templates were pre-compiled, versioned artefacts created by `gcloud dataflow templates create`, and they were tied to the SDK version used at creation time. They are effectively deprecated. It is also not a container image build in the strict sense — `flex-template build` packages the Python file plus its dependencies into a container image, but the runtime contract is still "a Python file plus parameters".

The practical benefit is that flex templates let you deploy without rebuilding a fat JAR or a wheelhouse for every change, and they are the only template type that supports Python reliably in a custom container.

### 4. Classic templates versus flex templates — when would you still pick the classic path?

You would not, in 2026, unless you are maintaining an existing estate. The differences that matter:

| | Classic | Flex |
|---|---|---|
| Creation | `gcloud dataflow templates create` | upload a Python file |
| Launch | `gcloud dataflow jobs run --template=...` | `gcloud dataflow jobs run --template=... --parameters=...` |
| Python | effectively unsupported | supported, including custom images |
| SDK pinning | baked in at creation time | depends on the image / runtime |

Classic templates froze the SDK version at build time, so a pipeline created with Beam 2.40 still ran with 2.40 years later — deterministic, but stuck on old APIs. Flex templates move that decision to the image or the runtime, which is what makes a "SDK-version problem" manageable at all.

The migration cost is low: take the classic template's parameter dict, turn it into `--parameters` flags, and move the pipeline body into a Python file with a `if __name__ == "__main__":` entry point.

### 5. Why do flex templates have an SDK-version problem, and how do you actually mitigate it?

Because the template runs on the worker with whatever SDK the **runtime or image** provides, and Dataflow's default worker image is not pinned to the version you developed against. A pipeline that worked on Beam 2.60 locally can fail on the worker with `AttributeError: module 'apache_beam' has no attribute 'SomeNewTransform'`, or with a changed coder default that breaks your `assert_that` expectations.

Three mitigations, in order of preference:

1. **Build a custom container image** with the exact SDK pinned (`apache-beam[gcp]==2.77.0`) and pass `--image` to `flex-template build`. This is the only true fix — it makes the worker environment byte-identical to your test environment.
2. **Pin the version in `requirements.txt` and rebuild the image** on every SDK bump, so the image tag is the source of truth for the SDK version.
3. **Stay on long-lived supported APIs** (`beam.Map`, `beam.CombinePerKey`, `WriteToText`) and avoid anything added in the last few releases.

What does *not* help: passing `--requirements_file` with a loose constraint and hoping pip resolves. Worker startup then downloads and resolves dependencies on every cold start, adding 30–120 seconds per worker and producing version drift between workers.

A production symptom worth recognising: a job that succeeds on the first few workers and then fails with a different error as autoscaling adds capacity — that is usually a heterogeneous environment, not a code bug.

### 6. What flags does a flex template launch actually require, and why does each one exist?

The minimum viable set for `gcloud dataflow jobs run --template=gs://BUCKET/templates/worker.py` is `--project`, `--region`, `--temp-location`, `--staging-location`, `--service-account`, and `--parameters`. Plus `--image` if you are using a custom container.

- **`--project`** — which project's quota, billing and IAM apply.
- **`--region`** — where the workers are created. Must match your bucket's region or you pay a cross-continent egress bill.
- **`--temp-location`** — scratch space for the shuffle and intermediate state. This is where `GroupByKey` spills to disk. It is deleted when the job succeeds.
- **`--staging-location`** — where the job's code and job model are staged. It must be **unique per concurrent job**; this is the single most common cause of a confusing "job already exists" or "staging location already in use" error when you launch two jobs from the same bucket.
- **`--service-account`** — the identity the *workers* run as, not the one you authenticate as.
- **`--parameters`** — runtime arguments, as a comma-separated `key=value` list.

`--parameters` is the flex-template analogue of command-line flags. The template reads them with `RuntimeValue.getRuntimeOptions()` or, in the common pattern, by letting `argparse` parse `sys.argv` as `batch_template.py` does.

### 7. How do you read template parameters, and what happens when the user omits one?

The parameters arrive as a string on the command line and Beam parses them into a runtime options dictionary. In Python the cleanest route is to read `sys.argv` directly with `argparse`, exactly as `project/templates/batch_template.py` does — the file is both a template and a local script, so the same parser serves both.

The thing that bites is **required arguments**. `argparse` with `required=True` will exit with status 2 and a usage message *on the worker*, not at submission. So the template launches, Dataflow spins up workers, and then the job fails with a confusing `usage: worker.py ...` in the worker log and a generic `Job worker failed` in the console. The submission succeeded; the failure is 90 seconds later and lives in worker logs.

Mitigation: validate parameters *before* the `with beam.Pipeline(...)` block and fail fast with a clear message, and give every parameter a sensible default. A missing `input` should print `input= is required` in the first second, not after two minutes of worker provisioning.

### 8. Two jobs from the same bucket fail with a staging collision — what exactly collides?

The staging location. Dataflow writes the job's serialized pipeline graph, the worker bootstrap files and the job model into `gs://BUCKET/staging`. If two jobs use the same staging path, the second job's files overwrite or are mistaken for the first's, and you get errors like `The job 'xyz' already exists` or a worker that boots the *other* job's code.

The fix is to make the staging path unique per job. Two standard approaches:

```bash
JOB_ID=$(gcloud dataflow jobs run --format='value(name)' ...)
# or, more simply, generate one yourself
STAMP=$(date +%s)
--staging-location=gs://YOUR_BUCKET/staging/${STAMP}
--temp-location=gs://YOUR_BUCKET/temp/${STAMP}
```

Doing the same for `--temp-location` matters for a different reason: the temp location holds shuffle spill files, and two concurrent jobs sharing it can corrupt each other's intermediate state — a failure mode that shows up as corrupted aggregation output rather than a clean error.

The production-safe pattern is to derive both paths from a single unique token (job name, timestamp, or UUID) and pass them together, so they can never diverge.

### 9. What are the autoscaling flags, and what are the real trade-offs?

For batch, `--num_workers` sets a fixed worker count and `--autoscaling_algorithm=NONE` disables scaling. For streaming, `--max_workers` is the ceiling and the algorithm is one of `Basic`, `Aggressive`, or `TargetUtilization`.

`Basic` scales roughly 1 worker per 1.5× the current CPU target and is conservative; `Aggressive` targets 85% utilisation and scales up faster, at the risk of a sawtooth: scale up, utilisation drops, scale down, backlog returns. `TargetUtilization` (available on newer Dataflow) is the most stable because it scales on a predicted backlog rather than instantaneous CPU.

The trade-off is startup latency against cost. A streaming job that must respond within 5 seconds needs aggressive scaling and a low `max_workers` ceiling is wrong; a nightly batch job with 4 hours of runtime should use `--num_workers` sized to the data (roughly 1 worker per 1–2 CPUs' worth of shuffle work) and `NONE`, because autoscaling on a batch job spends its time scaling rather than processing.

The mistake I have watched people make: leaving `--max_workers=200` on a 10 MB job. Dataflow bills vCPU-hour, so the ceiling is not a target — but with a streaming job that stays up for a month, the floor matters more: even one idle streaming worker costs roughly $0.01–0.02 per GB processed, and a fleet of 200 idle workers can run five figures a month.

### 10. How do you read Dataflow logs and metrics when a job fails on a worker?

Two levels, and you almost always need both. The **job-level** log and metrics come from `gcloud dataflow jobs messages describe JOB_ID --format=json` and `gcloud dataflow jobs describe JOB_ID --format='value(metrics)'`. The **worker-level** log — the actual Python traceback — is in Cloud Logging and must be read with `gcloud logging read` filtered on `resource.type=cloud_dataflow_job`.

```bash
gcloud logging read \
  "resource.type=cloud_dataflow_job AND resource.labels.job_id=JOB_ID AND severity>=ERROR" \
  --project=YOUR_PROJECT_ID --limit=200 --format=json
```

The trap: `gcloud dataflow jobs describe` shows a state like `JOB_STATE_FAILED` with a reason of "The job failed because a worker encountered an error", which tells you nothing. The traceback is only in the worker log. I have lost hours to jobs whose console summary said only "Job worker failed".

The metrics that earn their keep: `counters/ElementCount/out` (how many rows you produced), `counters/ElementCount/in` (how many you read), and the per-stage `mean_processing_time`. A stage with a huge input count and a zero output count is where the bug is; a stage where both counts are zero means the read never happened.

### 11. How do you cancel a streaming job, and what actually stops?

`gcloud dataflow jobs cancel JOB_ID` sends a cancellation request to the control plane. Dataflow then stops the workers, checkpoints their state, and moves the job to `JOB_STATE_CANCELLED`. The workers are torn down, so you stop paying for them.

For a **Dataflow Streaming** job, cancellation is graceful in the sense that in-flight state is checkpointed, so a job cancelled and restarted from the same subscription resumes from its last checkpoint rather than replaying from the beginning. That is a real property of the streaming runner.

For a **streaming job running on the batch runner** (a streaming-mode job launched with `--runner=DataflowRunner` but a bounded source), cancellation is a hard stop — state is not usefully checkpointed because there is no long-lived source offset to resume from.

The operational point: cancelling is not the same as deleting. `gcloud dataflow jobs delete JOB_ID --force` removes the job record; the pipeline name stays reserved unless you also pass `--now` on the name. A forgotten job name that cannot be reused is a common cause of "I can't deploy this pipeline any more".

### 12. Why should you use `--wait=false` when launching a job from CI?

Because `--wait=false` returns as soon as the job is *submitted*, rather than blocking until it reaches a terminal state. That is what you want in automation: the script can record the job ID and poll separately, or hand off to a monitoring system.

The subtle failure with `--wait=true` (the default) is that the CLI blocks inside the process, and the command's exit code encodes the *job* state. A pipeline that fails logically — say the BigQuery sink rejects rows because the schema changed — will make `gcloud dataflow jobs run --wait` exit non-zero, and a naive CI script that treats that as "the submission failed" will retry, creating a storm of duplicate jobs, each of which bills.

The pattern I use: launch with `--wait=false`, capture the job ID, poll `gcloud dataflow jobs describe` for a terminal state with a timeout, and decide success or failure from the *state* and the output row count, not from the submit command's exit code.

### 13. What does a forgotten streaming job actually cost?

Dataflow bills streaming work on **vCPU-hour** for the workers plus a per-GB charge for data processed. A modest streaming job — `n1-standard-4`, 3 workers — left running for 30 days costs roughly 3 × 4 vCPU × 720 hours × $0.05–0.10 per vCPU-hour ≈ **$430–860**, before any per-GB data charge. At 20 workers it is five figures.

The number people are surprised by is the idle one: an idle streaming job still holds its workers, and it still pays the per-GB charge for the data it reads. If it is subscribed to a Pub/Sub topic that never stops, it keeps paying forever.

The mitigation is boring and effective: a scheduled sweep that lists streaming jobs older than N days and cancels them, plus a budget alert at $1 as `resources/SETUP.md` recommends. I would also put a TTL on the pipeline *name* rather than relying on human discipline.

The related trap: cancelling the job does not cancel the Pub/Sub subscription. Messages published while no job is running accumulate in the subscription, and when you restart, every one of them is delivered — so the "small restart" can trigger a multi-hour replay that looks like a traffic spike.

### 14. What are the `gcloud dataflow` commands you should have memorised?

The working set is small and worth having in your fingers:

```bash
gcloud dataflow jobs list --project=YOUR_PROJECT_ID --format="table(name,state,createTime)"
gcloud dataflow jobs describe JOB_ID --project=YOUR_PROJECT_ID
gcloud dataflow jobs describe JOB_ID --format='value(status.state)'
gcloud dataflow jobs messages describe JOB_ID --format=json
gcloud dataflow jobs graph show JOB_ID --format=json
gcloud dataflow jobs cancel JOB_ID
gcloud dataflow jobs delete JOB_ID --force
```

Plus the flex-template pair:

```bash
gcloud dataflow flex-template build JOB_NAME \
  --template-file-gcs-path=gs://YOUR_BUCKET/templates/worker.py \
  --temp-location=gs://YOUR_BUCKET/dataflow/temp \
  --staging-location=gs://YOUR_BUCKET/dataflow/staging

gcloud dataflow flex-template run JOB_NAME \
  --template=gs://YOUR_BUCKET/templates/worker.py \
  --parameters="input=gs://YOUR_BUCKET/orders.csv" \
  --project=YOUR_PROJECT_ID --region=us-central1 \
  --service-account=dataflow-worker@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

Two of these are not obvious. `jobs graph show` returns the **execution graph** — the fused stages Dataflow actually built, not the graph you wrote. It is the fastest way to answer "why did this not fuse?" and "where did my filter go?". And `jobs messages describe` returns the job's progress messages, which is where "Job worker failed" and "Could not find any credentials" live.

`jobs list` with `--format="table(name,state,createTime)"` is the first command to run when you inherit a pipeline and need to know what is currently running.
