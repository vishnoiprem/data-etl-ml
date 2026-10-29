# 4.1 — GCP Project, Billing & APIs

> **Section 4 · GCP Setup & Local Execution · Lecture 4.1 · 6:30**

## 🎯 What you will learn

- How to create a GCP project, and why the project is the *first* thing you configure
- Why a project needs a billing account even when every job you run is free
- The seven APIs a Dataflow project needs, and the specific reason each one is required
- The `gcloud services enable` command, and the console papercut that survives it
- What the GCP free tier actually covers for Dataflow — and what it does not
- How to set a budget alert that actually stops you at 3am
- Regional consistency: bucket location, job region, and BigQuery dataset location
- Why this entire module is optional, and how to skip it without losing anything

---

## 🧠 Concept

> **This module is optional.** The course runs end to end on your laptop
> with no GCP account, no credentials, and no bill. Everything in Module 4
> is about what changes when you *do* deploy. You may skip it entirely
> and lose nothing except the ability to run `DataflowRunner`. The local
> runner — the course default — has no relationship to any of the
> machinery described here.
>
> Read this chapter when you want to understand what a Dataflow deployment
> costs, what it touches, and why the permission errors you will eventually
> hit look the way they do.

### The project is the unit of everything

Everything in GCP hangs off a **project**. It is the container for:

- APIs (each service must be enabled per-project)
- IAM policy (who can do what, per-project)
- billing (a project is linked to a billing account)
- quotas (per-project and per-region)
- data (buckets, datasets, topics all belong to a project)
- audit logs

Dataflow does not have a notion of an "account" or an "organisation" for
job purposes. A Dataflow job is scoped to exactly one project, and that
project determines the API endpoints, the service accounts, the quota
pool, and the bill. Getting the project right is therefore not
bookkeeping — it is the first decision that determines what the job can
and cannot do.

Two things follow that are not obvious:

1. **Your service account's roles are granted at the project level**, not
   per-job. A pipeline that can write to one bucket in your project can
   write to every bucket in it, unless you use bucket-level IAM to narrow
   that.
2. **The Dataflow service agent is per-project.** The email is
   `service-<PROJECT_NUMBER>@gcp-sa-dataflow.iam.gserviceaccount.com`.
   Two projects means two service agents, each with its own IAM policy
   and its own set of grants.

#### Project ID versus project number

GCP gives every project two identifiers, and confusing them causes
real bugs:

| Identifier | Example | Mutable? | Used for |
|---|---|---|---|
| **Project ID** | `revenue-platform` | No — fixed at creation | Human-facing references: `gcloud config set project`, `--project=`, BigQuery table names |
| **Project number** | `812345678901` | No — assigned by Google | Service account email addresses, quota requests, org policy bindings |

The project number is what the Dataflow service agent's email is built
from, which is why you need `gcloud projects describe` to get it:

```bash
export PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format='value(projectNumber)')
echo "service-${PROJECT_NUMBER}@gcp-sa-dataflow.iam.gserviceaccount.com"
```

> **Do not hard-code the project number in a script.** It is stable for the
> life of the project, but it is *opaque* — a reviewer reading
> `service-812345678901@gcp-sa-dataflow.iam.gserviceaccount.com` learns
> nothing. Resolve it from the project ID at run time, as above.

### Why billing is required even for free work

This is the first thing that surprises people, and it is not a
Dataflow-specific quirk — it is how GCP works.

**Most Google Cloud services require the project to have a billing account
linked before the API will do anything useful.** The check happens at API
call time, and the failure is not always a clean "no billing account"
error. Frequently you get a `403` with a message about the API not being
enabled, or a `PERMISSION_DENIED` on a quota project, and the actual
cause is the missing billing link.

More specifically for Dataflow:

- **A Dataflow job cannot even be submitted** without a linked billing
  account, because submission itself calls the Compute Engine API to
  allocate the worker VMs. The API call is billed.
- **Worker VMs are Compute Engine instances.** A Dataflow worker is a
  `n1-standard-2` (or similar) VM with a boot disk and a network
  interface. The Compute Engine API requires billing.
- **The Dataflow API has a per-hour minimum.** There is no free tier
  that makes a Dataflow job genuinely free; see the free tier section
  below.

A billing account is a *billing* concept, not a *payment* concept. You
can link a billing account that belongs to a Google Cloud account with
no payment method on file, and the free tier will still apply to
eligible services. You are not being charged for linking it. You are
being asked to say "if this project spends money, bill here".

```bash
# List the billing accounts you can use
gcloud billing accounts list

# Link one to the project
gcloud billing projects link YOUR_PROJECT_ID --billing-account=BILLING_ACCOUNT_ID

# Confirm
gcloud billing projects describe YOUR_PROJECT_ID
```

The linking command is idempotent and safe to re-run. If the project is
already linked, it returns an error that says so, and you can ignore it.

### The APIs a Dataflow project needs

A brand-new GCP project has every API disabled. Dataflow needs a
surprising number of them, and the failure mode is always the same: a
`403` or a `404` somewhere deep inside a job submission, two hours after
you started debugging, with a message that does not name the missing
API.

Here is the list and the *specific* reason each one is needed.

| API | Service name | Why Dataflow needs it |
|---|---|---|
| **Dataflow** | `dataflow.googleapis.com` | The job submission and control plane. `dataflow.projects.locations.jobs.create` is how a job is launched, and how the console talks to your job. |
| **Compute Engine** | `compute.googleapis.com` | **The workers are Compute Engine VMs.** Dataflow calls this API to create the VMs that run your `ParDo`s, to attach them to a network, and to add service-account scopes. Without this, no job can start. |
| **Cloud Storage** | `storage.googleapis.com` | The staging area (where the worker code is uploaded), the temp area (where shuffles and intermediate state live), and — in most pipelines — your actual input and output. |
| **BigQuery** | `bigquery.googleapis.com` | Only if you use `WriteToBigQuery` or `ReadFromBigQuery`. Dataflow's BigQuery sink writes via the BigQuery **load job** API, and the read path can use the BigQuery storage API or export to GCS. |
| **Pub/Sub** | `pubsub.googleapis.com` | Only for streaming. `ReadFromPubSub` subscribes to a topic, `WriteToPubSub` publishes. The Dataflow streaming service also uses Pub/Sub internally to distribute work between workers. |
| **Cloud Resource Manager** | `cloudresourcemanager.googleapis.com` | Project and folder lookups. Dataflow resolves the project number, checks the project's billing state, and applies the project's default service-account policies when provisioning. |
| **IAM** | `iam.googleapis.com` | Service-account lookups, IAM policy reads and writes, and — critically — **token minting**: Dataflow exchanges the service agent's credentials for short-lived access tokens that the workers use to call GCS, BigQuery, and Pub/Sub. |

Two of these deserve emphasis because they are counter-intuitive:

**Compute Engine** is the one people forget. It is not optional for
"cloud-native" Dataflow — it is not a serverless product. A Dataflow
worker *is* a VM. If your organisation has blocked `compute.googleapis.com`
by policy, Dataflow will not work, full stop.

**IAM** is the one that surprises people most. Dataflow does not hold a
long-lived credential that it passes to workers. Instead the service
agent mints a short-lived OAuth access token, and the workers use that
token. The IAM API is what makes that minting possible. This is also why
the "worker service account" in chapter 4.2 exists as a separate
identity: the token is minted *for* that account, with that account's
roles.

#### Enabling them

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

Read that command carefully. `gcloud services enable` takes **service
names**, not display names. `dataflow.googleapis.com` is the service
name. "Dataflow API" is the display name, and passing the display name
to this command fails with `Invalid argument: Service name must be
provided`.

You can verify what got enabled:

```bash
gcloud services list --enabled --filter="config.name:(dataflow|compute|storage|bigquery|pubsub|cloudresourcemanager|iam)"
```

Enabling an API is a global, project-scoped, asynchronous operation. It
takes a few seconds to a couple of minutes to propagate. Immediately
after the command returns, a job submission may still fail with
`SERVICE_DISABLED`. Wait and retry — this is not a bug in your setup.

#### The Dataflow API console papercut

Here is a specific, well-known papercut that catches almost everyone.

> **The symptom.** You have enabled `dataflow.googleapis.com` with
> `gcloud services enable`. The API is listed as enabled in
> `gcloud services list`. You submit your first Dataflow job and it fails
> with a `403` and a message along the lines of
> `Dataflow API has not been used in project YOUR_PROJECT_ID before or it
> is disabled. Enable it by visiting https://console.cloud.google.com/apis/library/dataflow.googleapis.com?project=YOUR_PROJECT_ID then retry.`

> **The cause.** In a brand-new project, the *first* Dataflow job
> sometimes needs the API to have been visited in the console as well.
> The `gcloud` enable call registers the service, but the Dataflow
> backend's own enablement check has a separate path that is only
> satisfied once the API has been opened in the console.

> **The fix.** Open the console page and click **Enable** (or
> **Manage → Enable** if it is already shown as enabled):
>
> ```
> https://console.cloud.google.com/apis/library/dataflow.googleapis.com?project=YOUR_PROJECT_ID
> ```
>
> Then wait a minute and resubmit. This is not a workaround for a
> misconfiguration; the console visit is genuinely part of the
> enablement flow in a fresh project.

The same papercut has a sibling for **Cloud Storage**: a new project
sometimes needs `storage.googleapis.com` opened in the console before
`gcloud storage` commands or `gs://` writes succeed. If you see a `404`
on a bucket that you know exists, check the API's state in the console
first, then check that the bucket name is globally unique.

### The free tier, honestly

Google Cloud's Free Tier gives every project a monthly credit, and it is
tiered by product. For the services in this course:

| Service | Free tier monthly credit | What it means for Dataflow |
|---|---|---|
| **Compute Engine** | $1 of credit, plus an "always free" `e2-micro` tier (one VM per region, US only) | The always-free `e2-micro` tier is **not usable by Dataflow**. Dataflow requires specific machine types; `e2-micro` is not among them, and the always-free tier explicitly excludes GPUs and most managed services. |
| **Cloud Storage** | 5 GB-months of standard storage, 5,000 class A and 50,000 class B operations | Enough for a small course project's inputs and outputs, and the free tier **does** cover the staging/temp traffic a small job generates. |
| **BigQuery** | 1 TiB of query processing per month, 10 GB of storage | Comfortably covers a course project. Note that *query* and *load* are billed differently: a BigQuery **load job** that writes a table costs nothing for the write itself, but a full table scan costs query bytes. |
| **Pub/Sub** | 10 GiB of message volume per month | Enough for a streaming demo. Dataflow's own internal Pub/Sub usage is **not** billed to you separately. |
| **Dataflow** | **No dedicated free tier.** | You are billed through Compute Engine for the worker VMs, plus Dataflow pipeline pricing for the graph processing. |
| **Cloud Logging** | 50 GB of log ingestion per month, 30 days of retention | A streaming job's logs can burn through this. |

**The honest summary:** the free tier comfortably covers the *storage*
around Dataflow, and it covers BigQuery and Pub/Sub. It does **not**
make Dataflow free, because Dataflow's cost is Compute Engine worker
time, and the always-free Compute Engine tier does not extend to
Dataflow's machine types.

**The realistic numbers.** A small batch job on the course dataset
(1,245 orders, a few hundred KB) with one `n1-standard-2` worker
finishes in well under a minute. At the current on-demand rate for
`n1-standard-2` in `us-central1`, the compute alone is on the order of
**$0.03–$0.05 per job**, plus the Dataflow pipeline fee, which is
per-worker-hour with a floor. The *floor* is the part that surprises
people: Dataflow bills a minimum of one hour of worker time for a job
that takes ninety seconds, and there is a per-stage minimum as well.
That floor exists because the workers need to start, download your code,
and shut down — and it is why "my job only ran for 20 seconds but cost
$2" happens.

**A job that is killed mid-run still bills** for the time it ran. And a
job that fails to start still bills for the time between the VM being
provisioned and the failure being detected. The single most common way
course participants accidentally spend money is a pipeline with an
infinite input: `ReadFromText` on a growing file, or a streaming job with
no `--window` limit, running for three hours while the author is asleep.

### Budget alerts

A budget alert is a **notification**, not a cap. This distinction
matters enormously, and most people learn it the hard way.

```bash
# Create a budget with a $1 threshold
gcloud billing budgets create \
    --billing-account=BILLING_ACCOUNT_ID \
    --display-name="Dataflow course budget" \
    --budget-amount=1 \
    --threshold-rule=0.5,0.9,1.0
```

The `--threshold-rule` values are fractions of the budget amount:
`0.5` fires at $0.50, `0.9` at $0.90, `1.0` at $1.00.

**A budget alert does not stop spend.** It sends an email (and, if you
enable Pub/Sub notifications, publishes a message) when the threshold is
crossed. If you are asleep, the job keeps running and the bill keeps
growing. Google Cloud has no "hard cap" on a project, by design — a
hard cap that silently killed a production job would be worse than a
bill.

What to do instead:

1. **Set the budget low** — $1 for a learning project. You want the
   notification to be a fire alarm, not a report.
2. **Enable Pub/Sub budget notifications** so you can build an
   automated response.
3. **Use a dedicated project for experimentation.** A project can be
   deleted, and deleting a project stops all its billing. Keeping the
   "I am learning" project separate from anything real is the cheapest
   insurance available.
4. **Set the timeout on your jobs.** `--experiments=...` aside, the
   practical control is to not launch an unbounded job.

```bash
# Inspect existing budgets
gcloud billing budgets list --billing-account=BILLING_ACCOUNT_ID

# Check current spend
gcloud billing accounts describe BILLING_ACCOUNT_ID
```

### Regional consistency

This is the chapter's most practically important section, because a
region mismatch is a **performance** bug and a **cost** bug, and neither
one produces an error message.

Three locations must agree:

| Location | What it is | Set by |
|---|---|---|
| **Bucket location** | Where the GCS objects physically live | `gcloud storage buckets create --location=...` |
| **Job region** | Where the Dataflow workers run | `--region=...` on the job |
| **BigQuery dataset location** | Where the BigQuery tables are stored | `bq mk --dataset_location=...` |

#### What actually happens when they disagree

Say your bucket is in `us-central1` (Iowa) and your job runs in
`europe-west1` (Belgium).

**The staging and temp traffic is the expensive part.** Before your
`ParDo` runs a single element, Dataflow uploads your pipeline code and
worker environment to the staging bucket, and it uses the temp location
for every shuffle. On a job with significant shuffle state, the temp
location receives and re-reads **the entire shuffled dataset**, plus
intermediate state for every stage. If the bucket is on another
continent, all of that crosses the Atlantic **twice** — once in, once
out — on every stage boundary.

Concretely, for a 1 TB shuffle:
- Same region: the data never leaves the Google network path.
- Cross-region within a continent: roughly tens of MB/s to a few
  hundred MB/s, plus **egress charges** on the bytes leaving
  `us-central1`.
- Cross-continent: single-digit to low-tens of MB/s, plus egress.

The **egress** is the part that turns a performance annoyance into a
bill. Google Cloud charges for data leaving a region to the internet,
and for cross-region transfers. A pipeline that shuffles 1 TB through a
mismatched bucket pays a data transfer charge that can exceed the
compute cost of the job itself.

#### The BigQuery dataset rule is different — and stricter

BigQuery datasets are **immutable in location**. You cannot move a
dataset. You can move a *table* (with a copy, which costs money), but
not the dataset.

This creates a hard constraint. If your BigQuery dataset is in `EU`, then
your Dataflow job **must** run in the EU — Dataflow refuses to write
from outside the relevant jurisdiction, and the "EU" BigQuery
requirement is enforced by the platform, not by a setting you can toggle.

More generally, for a BigQuery sink the relevant question is not just
"is it fast" but "is it legal and permitted":

- A BigQuery dataset in the **EU** requires the job to be in the EU.
- A BigQuery dataset in the **US** accepts jobs from most US regions.
- A BigQuery dataset in a specific region (e.g. `us-east1`) will accept
  jobs in that region or in the US multi-region.

So the rule of thumb is:

> **Pick one region. Put the bucket there, the job there, and the
> BigQuery dataset there. Then never change any of the three without
> changing all three.**

A good choice for a first project is `us-central1` for everything, or
`europe-west1` for everything if you are in Europe and have data
residency obligations. Do not pick a region because a colleague
mentioned it once.

```bash
# Create a bucket in one region
gcloud storage buckets create gs://YOUR_BUCKET \
    --location=us-central1 \
    --uniform-bucket-level-access

# Check where a bucket lives
gcloud storage buckets describe gs://YOUR_BUCKET --format="value(location)"

# Create a BigQuery dataset in the same region
bq mk --dataset_location=us-central1 YOUR_PROJECT_ID:revenue

# Check the Dataflow region you are about to use
gcloud config get-value compute/region
```

#### A note on multi-region

`us`, `eu`, and `asia` are **multi-regions**: two or more full regions
with automatic failover. They cost slightly more on storage
(roughly double the single-region rate) but give you higher durability
and better cross-region resilience.

For a staging/temp bucket, a single region is fine — the data is
disposable. For a bucket holding your only copy of production data, the
multi-region premium is usually worth it. For a course project, either
is fine; just be consistent.

---

## 🛠️ Hands-On

This hands-on has two halves. The first runs entirely on your machine
and is the part that matters for the course. The second is the GCP half,
which you run only if you have a project.

### Part 1 — Local: inspect what the course already knows

The course's `resources/beam_client.py` prints the environment the
pipelines will run in. Run it before you change anything:

```bash
cd data-engineering/data-Course/google/Dataflow
source .venv/bin/activate
python resources/beam_client.py
```

You should see something like:

```text
==============================================================
DATAFLOW COURSE ENVIRONMENT
==============================================================
  python               3.13.16
  executable           /path/to/.venv/bin/python
  beam_version         2.77.0
  runner               BundleBasedDirectRunner
  gcloud_available     False
  project_id           None
  region               us-central1
  bucket               None
  staging_location     None
  temp_location        None
  service_account      None
```

Every field that would point at a cloud resource is `None` or unset, and
`gcloud_available` is `False`. **That is a fully working configuration.**
The pipeline will run, and it will run locally.

Now see what the options layer resolves:

```bash
python resources/beam_client.py --runner DataflowRunner --json
```

The `runner` field flips, and `is_local` is not shown here but is
`False` for `DataflowRunner`. That single boolean is the difference
between "works on my laptop" and "needs a project, a bucket, and a
bill".

### Part 2 — Write the project-and-bucket checklist into a script

The following script encodes the whole of this chapter as an executable
checklist. It uses `gcloud` when it is available and reports what is
missing when it is not. Run it and read the output; it is a checklist you
can re-run before every deployment.

Save it as `check_gcp_setup.sh` in the course root:

```bash
cat > check_gcp_setup.sh <<'SCRIPT'
#!/usr/bin/env bash
# check_gcp_setup.sh — verify the prerequisites for a Dataflow deployment.
# Exits 0 when everything needed is present, 1 otherwise.
set -u

PROJECT_ID="${PROJECT_ID:-YOUR_PROJECT_ID}"
BUCKET="${BUCKET:-gs://YOUR_BUCKET}"
REGION="${REGION:-us-central1}"

fail=0

check() {
  local label="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    printf '  [ ok ] %s\n' "$label"
  else
    printf '  [FAIL] %s\n' "$label"
    fail=1
  fi
}

echo "Dataflow deployment checklist"
echo "  project : $PROJECT_ID"
echo "  bucket  : $BUCKET"
echo "  region  : $REGION"
echo

if ! command -v gcloud >/dev/null 2>&1; then
  echo "gcloud is not installed."
  echo "Everything in Module 4 is optional; the local runner needs none of it."
  exit 0
fi

echo "APIs"
for api in dataflow.googleapis.com compute.googleapis.com \
           storage.googleapis.com bigquery.googleapis.com \
           pubsub.googleapis.com cloudresourcemanager.googleapis.com \
           iam.googleapis.com; do
  check "$api enabled" \
    gcloud services list --enabled --filter="config.name=$api" \
      --format="value(config.name)"
done

echo
echo "Billing"
if gcloud billing projects describe "$PROJECT_ID" \
     --format="value(billingAccountName)" 2>/dev/null | grep -q .; then
  echo "  [ ok ] a billing account is linked"
else
  echo "  [FAIL] no billing account linked"
  fail=1
fi

echo
echo "Bucket"
if gcloud storage buckets describe "$BUCKET" \
     --format="value(location)" 2>/dev/null | grep -q .; then
  echo "  [ ok ] the bucket exists"
  bucket_region=$(gcloud storage buckets describe "$BUCKET" \
    --format="value(location)" 2>/dev/null)
  echo "         bucket location: $bucket_region"
  if [ "$bucket_region" != "$REGION" ]; then
    echo "  [WARN] bucket is in $bucket_region but the job region is $REGION"
    echo "         every shuffle byte crosses a region boundary"
  fi
else
  echo "  [FAIL] the bucket does not exist"
  fail=1
fi

echo
echo "Service accounts"
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" \
  --format='value(projectNumber)' 2>/dev/null)
SERVICE_AGENT="service-${PROJECT_NUMBER}@gcp-sa-dataflow.iam.gserviceaccount.com"
if gcloud iam service-accounts describe "$SERVICE_AGENT" >/dev/null 2>&1; then
  echo "  [ ok ] the Dataflow service agent exists"
else
  echo "  [FAIL] the Dataflow service agent does not exist yet"
  echo "         it is created by the first job, or by hand (chapter 4.2)"
  fail=1
fi

echo
if [ "$fail" -eq 0 ]; then
  echo "All checks passed."
else
  echo "Some checks failed. See resources/SETUP.md for the fix for each."
fi
exit "$fail"
SCRIPT

chmod +x check_gcp_setup.sh
./check_gcp_setup.sh
```

With no `gcloud` installed, the script prints the reassuring message and
exits 0. With `gcloud` but no project, it walks the checklist and tells
you exactly which step to run next.

### Part 3 — Verify the region-mismatch cost in the abstract

You cannot create a real mismatch without a project, but you can make the
principle concrete locally by measuring how much of a pipeline's work is
I/O. Beam exposes the pipeline's own metrics:

```python
import apache_beam as beam
from apache_beam.io.textio import ReadFromText, WriteToText

INPUT = "./sample_data/orders.csv"
OUTPUT = "./out/region_check"

with beam.Pipeline() as p:
    (
        p
        | "ReadOrders" >> ReadFromText(INPUT, skip_header_lines=1)
        | "ParseOrders" >> beam.Map(lambda line: line.split(","))
        | "KeyByRegion" >> beam.Map(lambda row: (row[3], float(row[7])))
        | "SumRevenue" >> beam.CombinePerKey(sum)
        | "Format" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]}")
        | "WriteSummary" >> WriteToText(OUTPUT, num_shards=1)
    )
```

Now run it with `--direct_running_mode=multi_processing` and with the
default `in_memory`, and compare:

```bash
time python project/batch_pipeline.py --runner BundleBasedDirectRunner \
    --input ./sample_data/orders.csv --output ./out/mode_inmemory

time python project/batch_pipeline.py --runner BundleBasedDirectRunner \
    --direct_running_mode=multi_processing \
    --input ./sample_data/orders.csv --output ./out/mode_multiproc
```

On this tiny dataset the difference is noise — the pipeline is dominated
by Python interpreter startup, not by data movement. On a dataset that
actually needs shuffling, the difference between an aligned and a
misaligned region is an order of magnitude, and the misaligned one
shows up in the bill as egress charges.

### Part 4 — The GCP commands, for when you have a project

Run these in order, from the course root. Each one is safe to re-run.

```bash
# 1. Create the project
gcloud projects create YOUR_PROJECT_ID --name="Dataflow Course"
gcloud config set project YOUR_PROJECT_ID

# 2. Enable the APIs
gcloud services enable \
    dataflow.googleapis.com \
    compute.googleapis.com \
    storage.googleapis.com \
    bigquery.googleapis.com \
    pubsub.googleapis.com \
    cloudresourcemanager.googleapis.com \
    iam.googleapis.com

# 3. Link a billing account
gcloud billing accounts list
gcloud billing projects link YOUR_PROJECT_ID --billing-account=BILLING_ACCOUNT_ID

# 4. Set a $1 budget with three thresholds
gcloud billing budgets create \
    --billing-account=BILLING_ACCOUNT_ID \
    --display-name="Dataflow course budget" \
    --budget-amount=1 \
    --threshold-rule=0.5,0.9,1.0

# 5. Create the bucket in the same region you will run jobs in
gcloud storage buckets create gs://YOUR_BUCKET \
    --location=us-central1 \
    --uniform-bucket-level-access

# 6. Create the BigQuery dataset in the same region
bq mk --dataset_location=us-central1 YOUR_PROJECT_ID:revenue

# 7. Configure the environment for the course
export PROJECT_ID=YOUR_PROJECT_ID
export REGION=us-central1
export BUCKET=gs://YOUR_BUCKET
export TEMP_LOCATION=gs://YOUR_BUCKET/dataflow/temp
export STAGING_LOCATION=gs://YOUR_BUCKET/dataflow/staging

# 8. Confirm the course sees the configuration
python resources/beam_client.py
```

Step 8 should now show `project_id`, `bucket`, `staging_location`, and
`temp_location` populated. That is the signal that the course is ready
to deploy — but read chapter 4.2 first, because the service accounts are
the next thing that will fail.

---

## 🛠️ Common Errors and Fixes

### `PERMISSION_DENIED: Cloud Resource Manager API has not been used in project ... before or it is disabled`

**The actual message:**

```text
google.api_core.exceptions.PermissionDenied: Cloud Resource Manager API has not been used in project YOUR_PROJECT_ID before or it is disabled. Enable it by visiting https://console.cloud.google.com/apis/library/cloudresourcemanager.googleapis.com?project=YOUR_PROJECT_ID then retry.
```

**The fix.** Enable the API, and wait for propagation:

```bash
gcloud services enable cloudresourcemanager.googleapis.com
```

If it is already enabled and the error persists, the account you are
using genuinely lacks the permission. The API being enabled and the
account being allowed to call it are two different checks, and the
message only names the first.

### `Invalid argument: Service name must be provided`

**The actual message:**

```text
ERROR: (gcloud.services.enable) Invalid argument: Service name must be provided.
```

**The cause.** You passed a display name or a URL instead of a service
name. The command wants `dataflow.googleapis.com`, not `Dataflow API`
and not the console URL.

**The fix.** Use the service name:

```bash
gcloud services enable dataflow.googleapis.com
```

### `Dataflow API has not been used in project ... before or it is disabled`

**The actual message:**

```text
google.api_core.exceptions.Forbidden: Dataflow API has not been used in project YOUR_PROJECT_ID before or it is disabled. Enable it by visiting https://console.cloud.google.com/apis/library/dataflow.googleapis.com?project=YOUR_PROJECT_ID then retry.
```

**The fix.** This is the console papercut. Open the URL the message
gives you and click **Enable**, even though `gcloud services list` says
the API is already enabled. Then wait a minute and resubmit.

### `The project YOUR_PROJECT_ID has no billing account associated`

**The actual message:**

```text
google.api_core.exceptions.Forbidden: The project YOUR_PROJECT_ID has no billing account associated with it. Please enable billing at https://console.cloud.google.com/billing?project=YOUR_PROJECT_ID
```

**The fix.**

```bash
gcloud billing accounts list
gcloud billing projects link YOUR_PROJECT_ID --billing-account=BILLING_ACCOUNT_ID
```

The link can take a minute to take effect. The message names a *billing
account*, not a *payment method* — a free-tier account with no card on
file still works.

### `Invalid project id` or `project YOUR_PROJECT_ID not found`

**The actual message:**

```text
ERROR: (gcloud.projects.describe) Invalid project id [YOUR_PROJECT_ID].
```

**The cause.** `YOUR_PROJECT_ID` is a literal placeholder, and the
project you actually created has a different ID. Or the project ID
contains characters that are not allowed.

**The fix.** Project IDs must be 6–30 characters, lowercase letters,
digits, and hyphens, and must start with a letter. Check what you
actually have:

```bash
gcloud projects list
```

### `google.auth.exceptions.DefaultCredentialsError: Your default credentials were not found`

**The actual message:**

```text
google.auth.exceptions.DefaultCredentialsError: Your default credentials were not found. To set up Application Default Credentials, see https://cloud.google.com/docs/authentication/external/set-up-adc for more information.
```

**The fix.** Either authenticate, or stay local:

```bash
gcloud auth application-default login
```

The `gcloud auth login` command is **not** sufficient — the Beam SDK
reads *Application Default Credentials*, which is a different file.
`gcloud auth application-default login` writes the right one.

If you have no Google account, do not solve this. Use the local runner:

```bash
python project/batch_pipeline.py --runner BundleBasedDirectRunner \
    --input ./sample_data/orders.csv --output ./out/summary
```

### `The bucket you are trying to access does not exist` (or `404`)

**The actual message:**

```text
google.api_core.exceptions.NotFound: 404 GET https://storage.googleapis.com/storage/v1/b/YOUR_BUCKET?projection=noAcl&prettyPrint=false. The bucket you are trying to access does not exist.
```

**The causes**, in order of likelihood:

1. The bucket name is not globally unique and someone else owns it.
2. The bucket is in a different project than the one your credentials
   are scoped to.
3. The Storage API is not enabled in the console for a brand-new project
   (the sibling of the Dataflow console papercut).

**The fix.**

```bash
gcloud storage buckets describe gs://YOUR_BUCKET
gcloud services list --enabled --filter="config.name=storage.googleapis.com"
```

### `The project is not associated with a billing account` (BigQuery)

**The actual message:**

```text
google.api_core.exceptions.Forbidden: The project YOUR_PROJECT_ID has not enabled BigQuery API or the project is not authorized to use the BigQuery API.
```

This message is misleading: it says "not authorized", but the usual
cause is a missing billing link or a missing API enablement, not an IAM
problem.

**The fix.**

```bash
gcloud services enable bigquery.googleapis.com
gcloud billing projects link YOUR_PROJECT_ID --billing-account=BILLING_ACCOUNT_ID
```

### `Failed to create the Dataflow job: Could not find the Dataflow service agent`

**The actual message:**

```text
RuntimeError: Failed to create the Dataflow job: Could not find the Dataflow service agent service-<PROJECT_NUMBER>@gcp-sa-dataflow.iam.gserviceaccount.com
```

**The cause.** The service agent has not been created yet, and the job's
first submission did not create it — usually because the creating
identity lacked `roles/dataflow.serviceAgent` or
`roles/iam.serviceAccountAdmin`.

**The fix.** Create it by hand, with the right roles, before the first
job. Chapter 4.2 has the exact commands.

---

## 💡 Production Notes

- **Use a dedicated project for learning, and delete it when you are
  done.** Deleting a project stops all its billing immediately. It is
  the single most effective cost control available, and it costs you
  thirty seconds.

- **A budget alert is a siren, not a brake.** Set it at $1 for a
  learning project so the notification is urgent. If you need a hard
  stop, build one: publish budget notifications to Pub/Sub and have a
  Cloud Function call `gcloud dataflow jobs cancel` on the affected
  jobs. That is a real project, and it is worth building once.

- **Never hard-code a project number or a service-account email.** Resolve
  the number from the project ID at run time. Project IDs are meaningful;
  numbers are opaque, and a hard-coded number will be wrong the moment
  you copy a script into a different project.

- **Pin your region in one place.** The course does this with the
  `REGION` environment variable, read once in `beam_options.py`. Every
  other module reads it from there. Do the same in your own code — a
  region that is written in six places is a region that will be wrong in
  one of them.

- **The Dataflow API console papercut is a deployment-order problem, not
  a permissions problem.** When you write a deployment script, put the
  console enablement into the runbook even though it is not
  scriptable. When onboarding a new engineer, tell them about it before
  they lose an afternoon to it.

- **Watch the first bill.** A first Dataflow bill typically contains
  three line items: Compute Engine (worker time), Dataflow (pipeline
  processing), and Cloud Storage (staging/temp, and egress if you have
  a region mismatch). If you see a Cloud Storage *data transfer* line
  item you did not expect, you have a region mismatch — go back and
  align the bucket, the job, and the dataset.

- **Enable the APIs in a dedicated setup step, not in the deployment
  step.** API enablement is idempotent but takes time to propagate, and
  mixing it into a deploy script turns a fast failure into a slow one.

---

## 🔑 Key Takeaways

- **Everything in this module is optional.** The course runs fully
  locally with no GCP account, no credentials, and no bill. Skip this
  module if you are not deploying.
- **Billing is required even for free work**, because Dataflow workers
  are Compute Engine VMs and the submission call itself is billed. A
  billing *account* is not a *payment method*.
- **Seven APIs, each for a specific reason.** `dataflow` (control
  plane), `compute` (the workers are VMs), `storage` (staging, temp,
  data), `bigquery`, `pubsub`, `cloudresourcemanager`, and `iam` (which
  mints the workers' access tokens).
- **The Dataflow API console papercut is real.** Enabling the API with
  `gcloud` is sometimes not enough in a brand-new project — open the
  console page and click Enable.
- **The free tier covers storage, BigQuery, and Pub/Sub around
  Dataflow, not Dataflow itself.** Worker time is billed through
  Compute Engine, and the always-free Compute Engine tier does not
  apply to Dataflow's machine types.
- **A budget alert notifies; it does not cap.** Set it at $1, and build
  an automated cancel if you need a real stop.
- **One region, three places.** The bucket, the job, and the BigQuery
  dataset must agree — BigQuery dataset locations are immutable, and a
  mismatch charges you egress on every shuffle byte.

---

## 📚 Practice Exercises

1. **Build a pre-flight check.** Extend `check_gcp_setup.sh` from the
   hands-on to also verify that the Dataflow service agent exists and
   carries `roles/dataflow.serviceAgent`, and that the worker service
   account carries `roles/dataflow.worker`. Use
   `gcloud projects get-iam-policy` and parse the JSON with
   `--format=json` rather than with `grep`, so the check is not fooled
   by a role bound at the folder level.

2. **Enumerate the APIs a project actually needs.** Write a script that,
   given a pipeline's source and sinks, prints the `gcloud services
   enable` command that would prepare the project. Start with the seven
   in this chapter, and add a rule: if the pipeline writes to BigQuery,
   `bigquery.googleapis.com` is required; if it reads Pub/Sub,
   `pubsub.googleapis.com` is required.

3. **Reason about a region mismatch.** Your bucket is in `us-central1`;
   your Dataflow job runs in `europe-west1`. A stage shuffles 2 TB.
   Write down, in order, the number of times that 2 TB crosses the
   region boundary, which of those crossings is billed, and which part
   of the bill it appears on. Then explain why putting the bucket in
   `us` (the multi-region) is a *worse* fix than moving the job to
   `us-central1`.

4. **Prove the free tier is not free for Dataflow.** Using the pricing
   page (link in Further Reading), compute the cost of a Dataflow batch
   job that runs for 4 minutes on one `n1-standard-2` worker, including
   the per-stage and per-job minimums. Compare it with a job that runs
   for 4 hours on the same worker. Explain why the marginal cost of the
   second job is not simply 60× the first.

5. **Make the budget real.** Enable Pub/Sub budget notifications on a
   $1 budget, write a Cloud Function that cancels any Dataflow job in
   the project when a budget notification arrives, and describe how you
   would test it without spending money. (Hint: the budget threshold
   can be set to a fraction of a cent for testing.)

6. **Reflect.** This chapter says the console visit is part of the
   enablement flow. Using only the facts in this chapter, construct the
   most likely explanation — you do not need to be right, you need to
   reason about what kind of system produces this behaviour.

---

## 📖 Further Reading

- Google Cloud Dataflow overview — https://cloud.google.com/dataflow/docs/about-dataflow
- Dataflow pricing — https://cloud.google.com/dataflow/pricing
- Google Cloud Free Tier — https://cloud.google.com/free/docs/free-cloud-features
- Setting up a Google Cloud project — https://cloud.google.com/resource-manager/docs/creating-managing-projects
- Enabling and disabling services — https://cloud.google.com/service-infrastructure/docs/service-management/enabling-disabling-services
- BigQuery locations and datasets — https://cloud.google.com/bigquery/docs/locations
- Managing billing accounts and budgets — https://cloud.google.com/billing/docs/how-to/budgets
- Dataflow service accounts and roles — https://cloud.google.com/dataflow/docs/access-control
