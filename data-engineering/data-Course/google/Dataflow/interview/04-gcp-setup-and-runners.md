# Module 4 — GCP Setup & Local Execution

> **12 questions · Module 4 · GCP Setup & Local Execution**

---

## Project setup

### 1. What are the three identities in a Dataflow job, and what does each one actually do?

**The caller** submits the job and reads its status. **The Dataflow service agent** creates the Compute Engine workers, stages files, and manages the job. **The worker service account** is the identity the worker VMs run as when they touch *your data*.

The three are distinct and confusing them is the single most common cause of a job that either fails to start or can read far too much.

| Identity | Address | Role |
|---|---|---|
| Caller | your user or CI service account | `roles/dataflow.developer` |
| Service agent | `service-<PROJECT_NUMBER>@gcp-sa-dataflow.iam.gserviceaccount.com` | `roles/dataflow.serviceAgent` |
| Worker | `dataflow-worker@YOUR_PROJECT_ID.iam.gserviceaccount.com` | `roles/dataflow.worker` |

Two consequences people forget. First, the **caller must be able to impersonate the worker service account** — it needs `roles/iam.serviceAccountUser` on it. A job with a perfectly configured worker account still fails to launch if the caller lacks that. Second, the **caller must be able to act as the Dataflow service agent**; `roles/dataflow.developer` at the project level grants it.

The default that people leave in place is the worst one: using the service agent as the worker account. It is convenient, and it means the workers inherit the service agent's access to every bucket in the project — so a pipeline that only reads one file can read the entire bucket.

The production failure story: a job was submitted with the service agent as the worker identity. It worked. Then someone moved a sensitive dataset into another bucket in the same project, and the pipeline — which had no business touching it — could read it. Nobody noticed for a month. The fix was a dedicated worker service account with object-level IAM on exactly the buckets it touches, and the `roles/storage.objectViewer` on the input bucket plus `roles/storage.objectCreator` on the output bucket, so a compromised worker cannot even read back what it wrote.

### 2. Why is running a job with a user key file a security incident rather than a shortcut?

Because a JSON key file is a **permanent credential**. It does not expire, it is not tied to a session, and it cannot be revoked without deleting the key and rotating everything that used it. A `gcloud auth application-default login` session, by contrast, is a short-lived OAuth token with a refresh token held by the CLI — it is scoped, auditable, and revocable.

The reason this shows up in Beam specifically is that the key propagates. A user key file passed to a Dataflow job is shipped to the staging location and made available to every worker, where it is used to authenticate. You have now spread a permanent credential across every worker in the job, wrote it to GCS, and put it in the job metadata. Any worker that is compromised, or anyone with read access to the staging bucket, has the key.

The correct pattern has three parts. Use **Application Default Credentials** (`gcloud auth application-default login`) for local development. In production, use a **dedicated worker service account** with no key file at all — Dataflow attaches it to the workers automatically through the instance's service-account scope, and there is no key to leak. And when you must authenticate *as* a service account from CI, use **service account impersonation**: `gcloud auth activate-config` with an impersonation target, or the `impersonate_service_account` setting in workload identity federation. That gives a short-lived token, not a key.

The failure story: a developer created a service account with `roles/owner`, downloaded a key, and used it for a month of local testing. The key was committed to a repository. When the repository was made public, Google Cloud's automated secret scanning revoked the key — which took down three production pipelines that shared it. The remediation was a full credential rotation across every consumer of the key, plus setting up a dedicated, least-privilege worker account so the next rotation was one key instead of twenty.

### 3. Which APIs do you need to enable, and why does the answer surprise people?

Seven, and the surprise is how many are *not* Dataflow:

```bash
gcloud services enable \
    dataflow.googleapis.com \
    compute.googleapis.com \
    storage.googleapis.com \
    bigquery.googleapis.com \
    pubsub.googleapis.com \
    cloudresourcemanager.googleapis.com \
    iam.googleapis.com
```

Each one has a job. `compute` because Dataflow provisions the workers as Compute Engine VMs. `storage` because the staging and temp locations are in GCS, and because most data lives there. `bigquery` and `pubsub` if your pipeline touches them. `cloudresourcemanager` for project-level operations like reading the project number for the service agent's address. `iam` for service-account creation and impersonation.

The papercut that costs the most time: **enabling the API in the console is sometimes required even after `gcloud services enable` succeeds.** In a brand-new project, the first Dataflow job sometimes fails with a permission error until you open **APIs & Services → Dataflow API → Enable** in the console. This is a known first-job issue and the symptom — a `403` on a service that is demonstrably enabled — sends people looking in completely the wrong place.

The production failure story: a new project was created with `gcloud projects create`, the APIs were enabled with a loop, and the first job failed with `PERMISSION_DENIED: User does not have storage.objects.get access` — even though the submitter was the project owner. The owner had `roles/owner`, which includes everything, so IAM was not the issue. The cause was the Dataflow API not being fully activated for the first job in a brand-new project. The fix was the console enable, after which the same command worked unchanged.

### 4. Why does region matching matter so much, and what exactly breaks when it does not?

Three things must agree: the **Dataflow job's region**, the **GCS bucket's location**, and the **BigQuery dataset's location**. When they do not, you pay for cross-continent egress and you add latency to every byte.

The economics: a `us-central1` job reading a `europe-west1` bucket sends every byte across the Atlantic. Google Cloud Storage charges egress for data leaving a region — roughly $0.08–$0.12 per GB for inter-continental transfers — and the latency adds up on a pipeline that makes many small reads. A 500 GB cross-region pipeline pays roughly $40–60 in egress *for the read alone*, before any of the work.

There is a second, harder failure: **VPC-native jobs require the subnet's region to match the job's region.** A `us-central1` job cannot use a `us-east1` subnet, and Dataflow rejects the launch with a confusing message about VPC peering rather than about region mismatch.

There is also a CMEK constraint: the **Cloud KMS key's location must match the job's region**, or you get `Key location 'us-east1' does not match the job region 'us-central1'`.

The production failure story: a team deployed to `us-east1` because that was where their compute quota was, while the bucket and the BigQuery dataset were in `us-central1`. The pipeline worked and nobody complained, because the correctness was fine. But the monthly egress bill was consistently $200–$400 higher than the compute bill, which nobody could explain. The fix was to move the job to `us-central1` — or, better, to move the data and keep everything in one region. The lesson is that region is a *cost architecture* decision, not a deployment detail, and the bill is where it shows up.

### 5. How do billing and budget alerts protect you, and what is the cheapest insurance?

Budget alerts are the cheapest insurance in the platform. A budget in Google Cloud does **not** cap spending — it only notifies — so you must pair it with something that actually stops the job.

```bash
gcloud billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --budget-display-name="Dataflow guardrail" \
  --budget-amount=100 \
  --budget-threshold-type=PERCENT \
  --budget-threshold-value=50 \
  --budget-threshold-type=ABSOLUTE \
  --budget-threshold-value=75
```

Billing is required even for a job that costs nothing, which surprises people: you cannot create a project that can launch Dataflow workers without a linked billing account, even if the job will be cancelled in 30 seconds.

The reason the alert matters is the shape of the Dataflow failure mode. The expensive accident is not a single huge job — it is a **streaming job left running**. A streaming job holds its workers whether or not data is flowing, so three `n1-standard-4` workers left running for 30 days cost roughly 3 × 4 vCPU × 720 hours × $0.05–0.10 per vCPU-hour ≈ **$430–860**, before any per-GB data charge. An alert at $1 catches that within the hour; an alert at $500 catches it after the damage.

The complement to the alert is a **scheduled sweep** that cancels streaming jobs older than N days. Alerts notify a human; the sweep acts without one. Together they turn a potential five-figure surprise into a two-line cron job.

The production failure story: a team set a $1000 budget alert on a project with twelve active pipelines and ignored it for a month. A staging streaming job was left running after a demo, with `--max_workers=50`. It cost roughly $3,400 before anyone looked at the alert email, which had gone to a distribution list that had been auto-replied "out of office" for two weeks. The fix was a $1 alert on the specific project *plus* a daily sweep that cancelled any streaming job whose name matched `*-dev-*` and was older than 24 hours.

## IAM and identities

### 6. How do you give a Dataflow worker exactly the access it needs, and no more?

Grant at the **resource** level, not the project level, and split read from write. The built-in `roles/dataflow.worker` is broad: it can read and write Cloud Storage, create BigQuery jobs, publish to Pub/Sub, and read several other services. For a pipeline that reads one bucket and writes another, that is far more than it needs.

The pattern:

```bash
# The worker may read the input bucket...
gcloud storage buckets add-iam-policy-binding gs://YOUR_BUCKET \
  --member=serviceAccount:beam-worker@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/storage.objectViewer

# ...and write the output bucket, but not read it back.
gcloud storage buckets add-iam-policy-binding gs://YOUR_BUCKET \
  --member=serviceAccount:beam-worker@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/storage.objectCreator
```

`roles/storage.objectCreator` is write-only and `roles/storage.objectViewer` is read-only. Splitting them means a compromised worker cannot read back the data it wrote, and cannot write into the input bucket. For BigQuery, scope `roles/bigquery.dataEditor` to one dataset with an IAM condition rather than granting it project-wide.

When the built-in roles are either too broad or cannot express what you need, a **custom role** is the cleanest audit story — one that says "read objects in these buckets, nothing else" is exactly what a security reviewer wants to see, and it excludes the permissions you do not want by default.

The production failure story: a pipeline's worker account had project-level `roles/storage.objectAdmin` "because that was in the setup docs". When a second team started using the same project, the first team's pipeline gained read access to the second team's raw customer exports — not because anyone changed the pipeline, but because the project-level role had always been there. The fix was to move to object-level bindings on two buckets and a custom role, and to add a policy in the security review that no Dataflow worker account gets a project-level Storage role.

### 7. What does the Dataflow service agent do that the worker account does not, and why must it be created up front?

The **service agent** is the identity the Dataflow *control plane* uses to create and manage the Compute Engine VMs, wire up networking, and read and write the staging and temp locations in GCS. It is not the identity your Beam code runs as, and its address is fixed: `service-<PROJECT_NUMBER>@gcp-sa-dataflow.iam.gserviceaccount.com`.

The operational point that catches people: Dataflow creates the service agent **automatically on the first job submission**, and it caches the IAM policy at creation time. So granting it `roles/storage.objectAdmin` *after* the first job has run does nothing — the permissions were captured when the agent was created. You have to delete the service agent and let Dataflow recreate it, which is a confusing, undocumented-looking operation.

The fix is to create it by hand with the right roles before the first job:

```bash
export PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format='value(projectNumber)')
export SERVICE_ACCOUNT="service-${PROJECT_NUMBER}@gcp-sa-dataflow.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/dataflow.serviceAgent"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/storage.objectAdmin"
```

The production failure story: a team's first job failed with `403 storage.objects.get` on the very first bundle. They spent two hours on the worker's IAM — which was correctly configured — before discovering the service agent had been auto-created at first submission without `roles/storage.objectAdmin`, and that adding the role afterwards changed nothing. The fix was to delete the service agent (`gcloud iam service-accounts delete`), let Dataflow recreate it, and confirm it picked up the role. Creating it by hand up front is the practice that removes the whole class of problem.

## Runners and options

### 8. How does `PipelineOptions` parse flags, and what makes it hostile to a script with its own arguments?

`PipelineOptions` is a flag-parsing framework built on `argparse`. It declares every known option as an `argparse` argument, and when it encounters a flag it does not know, it raises `SystemExit` — it does not ignore it, and it does not pass it through.

That behaviour is the problem. A pipeline script almost always has its own arguments (`--input`, `--output`, `--statuses`), and Beam will reject them. The course's `beam_options.build_options()` solves this by **filtering the argument list before Beam sees it**: it enumerates the known Beam flags via `PipelineOptions([]).get_all_options()`, keeps only the flags in that set, and drops the rest (along with the value that followed them, when the value was a separate argument).

The consequence for the script's own parser: it must use `parse_known_args` rather than `parse_args`, so that Beam's flags survive to be handed to `PipelineOptions`. The course's `batch_pipeline.py` does exactly this.

```python
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--input", default="./sample_data/orders.csv")
parser.add_argument("--output", default="./out/summary")
args, unknown = parser.parse_known_args()
```

The mechanism detail worth remembering: `PipelineOptions` **rejects unknown attributes**, and the Dataflow-specific options (`region`, `service_account_email`, `staging_location`) only exist on the `DataflowOptions` subclass, not on the base class. So `options.region = "us-central1"` on a plain `PipelineOptions` raises `AttributeError: 'PipelineOptions' object has no attribute 'region'` — you must use `options.view_as(DataflowOptions).region = ...`, or set the attribute on an object that actually declares it.

The production failure story: a script used `parse_args` and the pipeline worked locally — because the local runner path never hit Beam's flag parser — but failed on Dataflow with `SystemExit: 2` and the usage message, which says nothing about what was wrong. The fix was `parse_known_args` plus the filter in `build_options`.

### 9. What is `view_as` for, and why is `runner` read-only?

`view_as` projects a `PipelineOptions` object onto one of its registered *views* — `StandardOptions`, `TypeOptions`, `GoogleCloudOptions`, `DataflowOptions`. Each view declares its own flags, and `view_as` is how you reach them:

```python
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions, TypeOptions

options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])
options.view_as(StandardOptions).streaming = True
options.view_as(TypeOptions).allow_unsafe_triggers = True
```

You need `view_as` because the options are namespaced. `options.region` raises `AttributeError` if the base object does not declare `region`; `options.view_as(DataflowOptions).region` works.

`runner` is read-only because the runner is resolved at `Pipeline` construction, and Beam resolves it by **name** through `create_runner` — an exact-match lookup first, then `name + "runner"`. Assigning a string to `options.runner` raises, and assigning a runner *class* is a different thing from assigning its name. The supported ways to choose a runner are `--runner=DataflowRunner` on the command line, `beam.Pipeline(runner="DataflowRunner")` as a constructor argument, or passing options whose `runner` was set by the command line.

The resolution order has one more wrinkle: if you pass **both** a runner object and options whose `runner` differs, the constructor argument wins. That matters when a wrapper builds options and a caller also passes a runner.

The production failure story: someone wrote `options.runner = "DataflowRunner"` in a shared helper and it raised at import time in a unit test. The confusing part was that the same *intent* worked when written as `PipelineOptions(["--runner", "DataflowRunner"])`. The lesson is that the runner is selected by name at parse time, and every later stage reads the already-resolved value.

### 10. What do `--allow_unsafe_triggers` and `--save_main_session` actually do, and when do you need them?

**`--allow_unsafe_triggers`** tells Beam that you accept triggers which may lose data. It is required for `AfterCount` and `AfterProcessingTime` without a watermark guarantee, and for `AfterWatermark` combined with a non-zero allowed lateness. Beam's check raises `ValueError: Unsafe trigger: AfterCount(100) may lose data` otherwise, and the error explains *why*: these triggers can fire and discard elements that arrive later.

The trade-off is real and you should state it to an interviewer: an `AfterCount(10)` trigger on a window emits after every ten elements, so the first nine firings are partial and the tenth is final. With `DISCARDING` accumulation the panes compose to the whole window; with `ACCUMULATING` each pane is the running total. The flag is not a workaround for a bug — it is a declaration that your semantics are "emit partial results" and you accept the risk that a late element falls outside the count.

**`--save_main_session`** makes the runner serialise the `__main__` module's state so that the code you defined at the top level of your script is available on the workers. Without it, worker processes start with a fresh `__main__` and any function or variable defined there is undefined there. The symptom is a `NameError: name 'parse_order' is not defined` on the worker, while the same code runs perfectly on the Direct Runner because your process is already the worker.

The mechanism: the runner pickles the session's globals and injects them into the worker's `__main__` namespace. The cost is that the whole session state travels to every worker, so a large in-memory DataFrame in your `__main__` gets shipped to every worker — slow, and sometimes unserialisable.

The production failure story: a pipeline defined its parsing function at module level in the script and worked on the Direct Runner for months. It failed on Dataflow with `NameError: name 'parse_order_line' is not defined` in the worker log. The fix was to move the function into a separate module that the worker imports — which is strictly better than `--save_main_session`, because it also keeps the code testable and stops the whole session being shipped. `--save_main_session` is the right answer for a quick notebook-style script, and the wrong answer for anything you intend to operate.

### 11. What are the staging and temp locations, and why must the staging location be unique per job?

**Staging location** is where Dataflow puts the job's code and its serialized pipeline graph before the workers start. **Temp location** is scratch space — shuffle spill files, intermediate state, and the staging copies of the job model.

The staging location **must be unique per concurrent job**. Dataflow writes the job's serialized graph and worker bootstrap files into that path; if two jobs share it, the second job's files overwrite or are mistaken for the first's. The symptoms are confusing: `The job 'xyz' already exists`, or a worker that boots the *other* job's code and runs the wrong pipeline.

The temp location has a different but equally real requirement: it holds shuffle spill files, and two concurrent jobs sharing it can corrupt each other's intermediate state. That failure mode is much nastier than a clean error — it shows up as *corrupted aggregation output*, a wrong number, and no exception anywhere.

The fix is to derive both paths from a single unique token — the job name, a timestamp, or a UUID — so they can never diverge:

```bash
STAMP=$(date +%s)
--staging-location=gs://YOUR_BUCKET/dataflow/staging/${STAMP}
--temp-location=gs://YOUR_BUCKET/dataflow/temp/${STAMP}
```

The course's `apply_dataflow_defaults` does exactly this, deriving both from a bucket prefix. The default Dataflow locations are shared, which is why *every* concurrent launch collides.

The production failure story: a CI pipeline ran two jobs concurrently from the same bucket — a backfill and the nightly — using the default staging location. The nightly job failed with "job already exists", and the backfill, which appeared to succeed, wrote output that was a mixture of both pipelines' aggregation states. The output was wrong and nothing errored. The fix was unique per-run staging and temp paths derived from a run ID, plus a change to CI so the backfill and the nightly cannot overlap.

### 12. What does `beam.io.ReadFromText`'s file-splitting behaviour imply about how you should store data?

`ReadFromText` splits files into bundles for parallel reading, and it can only split an **uncompressed** file. A compressed file is one bundle, regardless of its size. So a single 50 GB `.gz` file is read by exactly one worker, no matter how many workers the job has, and the job's runtime is bounded by one worker's throughput rather than by the cluster's.

The same applies to output: the number of shards `WriteToText` produces follows the parallelism the runner chose, and compressed shards cannot be split either.

The practical rules that follow. Store large data **uncompressed** and let the read path split it. If compression is mandatory for storage cost, then **split the file at the producer** into many smaller compressed files — 128 MB to 1 GB each — rather than one huge archive. And when you compress a CSV, use a format that is splittable: gzip blocks are independently decompressible, so a concatenated gzip of many independently-compressed blocks *is* splittable, whereas a single gzip stream is not.

The mechanism: Beam's file source computes split offsets by seeking to a boundary and scanning forward to the next newline. That is only possible on a seekable, uncompressed file. The error message when it cannot split is explicit — `ValueError: Could not split file ... it is compressed` — but it surfaces during graph expansion, and the symptom people report is "the job runs but only one worker is busy".

The production failure story: a team archived daily exports as one 300 GB `.tar.gz` per day in GCS and read them with `ReadFromText`. The nightly job took 6 hours with 50 workers, of which 49 were idle — the job was reading a single bundle. Splitting the archive into 512 MB chunks dropped the same job to 8 minutes on 30 workers. The extra storage from uncompressed data was a fraction of the compute they had been wasting, and nobody had noticed because the job "worked".

The related detail for local testing: Beam cannot split a file on the local filesystem the way it splits one in GCS, so local runs of a multi-gigabyte file are serial by construction. That is fine for a test, and it is a good reason to keep a small sample dataset — the course's `resources/sample_data.py` generates exactly that.
