# 4.2 — Service Accounts & Bucket

> **Section 4 · GCP Setup & Local Execution · Lecture 4.2 · 6:30**

## 🎯 What you will learn

- The three distinct identities a Dataflow job involves, and what each one actually does
- The exact roles each identity needs, and why the roles are not interchangeable
- Why a user key file running as a Dataflow worker is a security incident, not a shortcut
- How to create a bucket with uniform bucket-level access, and why that is the default you want
- The service-agent caching gotcha: adding a role after the agent exists requires a remove-and-re-add
- Key rotation, and why the modern answer is to not have a key at all
- A least-privilege table you can implement directly
- Why BigQuery has no equivalent of this chapter

---

## 🧠 Concept

> **This module is optional.** Nothing in this chapter is needed to run
> the course pipelines locally. It is here because the moment you deploy
> to Dataflow, this is the machinery that decides whether your job
> starts, and — more importantly — what your job is *able* to touch once
> it is running.

### Three identities, three jobs

Most Dataflow permission problems are caused by treating Dataflow as
having *one* identity. It has three, they are created at different times,
they are granted roles in different places, and they are used for
completely different purposes.

```text
        ┌──────────────────────────────────────────────────┐
        │  YOU  (your user account, or a CI service acct) │
        │  • calls the Dataflow API to submit the job       │
        │  • needs roles/dataflow.developer (or owner)      │
        │  • never touches the data                         │
        └───────────────────────┬──────────────────────────┘
                                │  submits
                                ▼
        ┌──────────────────────────────────────────────────┐
        │  DATAFLOW SERVICE AGENT                         │
        │  service-<PROJECT_NUMBER>@gcp-sa-dataflow...     │
        │  • creates and deletes the worker VMs             │
        │  • stages the worker code into GCS               │
        │  • mints access tokens for the workers           │
        │  • needs roles/dataflow.serviceAgent             │
        └───────────────────────┬──────────────────────────┘
                                │  creates VMs running as
                                ▼
        ┌──────────────────────────────────────────────────┐
        │  WORKER SERVICE ACCOUNT                          │
        │  dataflow-worker@YOUR_PROJECT_ID.iam...          │
        │  • the identity your ParDo code runs as           │
        │  • reads input, writes output                    │
        │  • needs roles/dataflow.worker (+ storage)        │
        └──────────────────────────────────────────────────┘
```

#### 1. Your account — the submitter

This is the identity that calls `dataflow.projects.locations.jobs.create`
and uploads the pipeline. It is a *human* identity in a learning project
and a *CI service account* in a real one.

What it needs:

| Role | Why |
|---|---|
| `roles/dataflow.developer` | Submit and cancel jobs, view the job graph and metrics. This is the minimum that works. |
| `roles/iam.serviceAccountUser` **on the worker service account** | Allows the submitter to *act as* the worker identity. Without it, Dataflow refuses to launch workers as that account. |
| `roles/storage.objectAdmin` on the staging bucket | Uploads the worker code. (If the service agent has it and you rely on the service agent to stage, you may not need this yourself — but the submitter uploads the *job* metadata, so in practice you usually do.) |
| `roles/serviceusage.serviceUsageConsumer` | Lets the submitter check that the required APIs are enabled. Without it, you get a confusing failure instead of a clean "API not enabled" message. |

The common mistake: giving the submitter `roles/owner` and moving on.
It works, it is fast, and it is exactly how a course project becomes a
security incident. See the section on user key files below.

#### 2. The Dataflow service agent — the control plane

This identity is special. It is **not created by you**; Google creates
it automatically, and its email is deterministic:

```text
service-<PROJECT_NUMBER>@gcp-sa-dataflow.iam.gserviceaccount.com
```

Its job is to act *on the control plane* — the Dataflow API's own
infrastructure, separate from your workers:

- Create the Compute Engine VMs that will run your job.
- Attach those VMs to the network, with the right service-account scopes.
- Upload the staged worker code to the staging bucket.
- Mint short-lived OAuth access tokens for the worker service account,
  which the workers then use to call GCS, BigQuery, and Pub/Sub.
- Delete the VMs when the job finishes.

The role it needs is `roles/dataflow.serviceAgent`. Google grants this
role to the service agent **automatically** the first time a job is
submitted in a project — but the automatic grant happens *at job
submission time*, which is too late for the job to start cleanly if the
submitter's own permissions are wrong.

> **Create the service agent by hand, before the first job.** This is the
> single most reliable Dataflow setup practice, and it is what
> `resources/SETUP.md` does. A hand-created service agent with explicit
> roles fails loudly and early rather than mysteriously at 2am.

```bash
export PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format='value(projectNumber)')
export SERVICE_ACCOUNT="service-${PROJECT_NUMBER}@gcp-sa-dataflow.iam.gserviceaccount.com"

# Create it explicitly (idempotent — an error means it already exists)
gcloud iam service-accounts create service-${PROJECT_NUMBER} \
    --project=YOUR_PROJECT_ID \
    --display-name="Dataflow Service Agent" || true

# Grant the role
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/dataflow.serviceAgent"
```

#### 3. The worker service account — the data plane

This is the identity **your pipeline code runs as**. Every `ParDo` that
calls GCS, BigQuery, or Pub/Sub uses this account's credentials. It is
the one you must think about when you ask "what can my pipeline touch?"

| Role | Why |
|---|---|
| `roles/dataflow.worker` | The baseline role for a Dataflow worker. Grants the minimum needed to function as a worker. |
| `roles/storage.objectAdmin` | Read input, write output, and — importantly — read and write the **temp location**, which is where shuffle state lives during the job. |
| `roles/bigquery.dataEditor` | Only if the pipeline reads or writes BigQuery. |
| `roles/pubsub.publisher` / `roles/pubsub.subscriber` | Only if the pipeline reads or writes Pub/Sub. |

The distinction between `roles/dataflow.serviceAgent` and
`roles/dataflow.worker` is the one people get wrong, and it is worth
being pedantic about:

- `roles/dataflow.serviceAgent` is a **project-level** role, granted to
  a Google-managed identity, that lets it *manage Dataflow resources*.
  It is powerful by design — it can create VMs, which means it can spend
  money.
- `roles/dataflow.worker` is the role for a **user-managed** service
  account that runs your code. It does **not** let that account create
  VMs or submit jobs.

Granting `serviceAgent` to your worker account is a privilege
escalation: your pipeline code could then launch more Dataflow jobs. In
a multi-tenant environment — a shared project, a pipeline that processes
untrusted input — that is a real attack path.

### Why a user key file is a security incident

The older Dataflow setup — and still the most common tutorial on the
internet — looks like this:

```bash
gcloud iam service-accounts keys create ./key.json \
    --iam-account=my-sa@my-project.iam.gserviceaccount.com

python my_pipeline.py \
    --runner DataflowRunner \
    --service_account_email=my-sa@my-project.iam.gserviceaccount.com \
    --key_file=./key.json
```

**Do not do this.** Three things are wrong with it, and they compound.

**First, a key file is a permanent credential.** An access token expires
in one hour. A service-account key does not expire until you revoke it,
and it can be used from anywhere on the internet by anyone who has the
file. It bypasses every conditional-access policy you have, because IAM
does not know *who* is using the key — only *that* a valid key is being
presented.

**Second, the key ends up in places keys should never be.** The file
lives in your checkout. It gets committed — and `.gitignore` is a
convention, not a control. It gets copied to a CI runner, a Docker
image layer, a laptop backup, a chat message, a support ticket. Every
one of those is a copy you now have to revoke.

**Third, the key's owner is usually a human.** If you created the key on
your own user account, then a leaked key is *your* access, with every
role you have, including `roles/owner`. Dataflow workers run your code
on machines you do not control, processing data you do not own. Giving
that code a copy of your personal credentials is the textbook definition
of excessive privilege.

> **The rule.** A Dataflow job should have **no key files at all**. The
> worker service account should be attached to the job by *email*, and
> the credentials should be minted at run time by the Dataflow service
> agent using the standard OAuth 2.0 service-account flow. If you find
> a `--key_file` flag in your pipeline's arguments, delete it.

The modern equivalent is exactly the `resources/SETUP.md` configuration:

```bash
export SERVICE_ACCOUNT_EMAIL=dataflow-worker@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

```bash
python project/batch_pipeline.py \
    --runner DataflowRunner \
    --project YOUR_PROJECT_ID \
    --region us-central1 \
    --staging_location gs://YOUR_BUCKET/dataflow/staging \
    --temp_location gs://YOUR_BUCKET/dataflow/temp \
    --service_account_email dataflow-worker@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

No key. The identity is expressed as an email, and the credential is
minted at job start.

### The bucket, and uniform bucket-level access

Two decisions when creating the bucket.

**Decision 1: uniform bucket-level access (UBLA).** With UBLA, IAM
policies attach to the *bucket* rather than to individual objects. It is
the default for new buckets, and it is the correct choice.

```bash
gcloud storage buckets create gs://YOUR_BUCKET \
    --location=us-central1 \
    --uniform-bucket-level-access
```

The alternative is *fine-grained* (per-object) ACLs, where every object
can carry its own ACL list. Fine-grained ACLs are a legacy mechanism with
a serious operational property: **they interact with IAM in
non-obvious ways**, and a bucket with fine-grained ACLs can end up
with a public object even when the bucket-level IAM policy is correct.

One more subtlety worth knowing: when you enable UBLA on an existing
bucket, you are limited to 1,000 objects in a 24-hour window, because
the platform has to rewrite the ACLs. On a fresh bucket this is
irrelevant.

**Decision 2: the location.** Already covered in chapter 4.1, but it
repeats here because it is a bucket-creation decision: use the same
region as your Dataflow job and your BigQuery dataset.

```bash
# Verify after creation
gcloud storage buckets describe gs://YOUR_BUCKET \
    --format="value(name,location,iamConfiguration.uniformBucketLevelAccess)"
```

Expected output shape:

```text
name                    location     iamConfiguration.uniformBucketLevelAccess
YOUR_BUCKET             US-CENTRAL1  True
```

Note the casing: GCS reports `US-CENTRAL1` and `EUROPE-WEST1`, while
Dataflow and `gcloud` use lowercase `us-central1`. This trips people up
in scripts that compare the two.

### The caching gotcha

Here is a genuine, well-documented, and deeply annoying Dataflow
behaviour that costs people hours.

**The rule.** The Dataflow service agent's IAM policy is read and
**cached** when the service agent is created. If you add a role to the
service agent *after* that, the change may not take effect.

**The symptom.** The job fails with a 403 on a GCS operation, even
though `gcloud projects get-iam-policy` clearly shows the role:

```text
google.api_core.exceptions.Forbidden: 403 GET https://storage.googleapis.com/storage/v1/b/YOUR_BUCKET/o/... : your-service-account@YOUR_PROJECT_ID.iam.gserviceaccount.com does not have storage.objects.get access to the Google Cloud Storage object.
```

And yet:

```bash
gcloud projects get-iam-policy YOUR_PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:YOUR_BUCKET" \
    --format="value(bindings.role)"
```

shows `roles/storage.objectAdmin` right there.

**The fix — remove and re-add.** Deleting the binding and adding it back
invalidates the cache and forces Dataflow to re-read the policy:

```bash
export SERVICE_ACCOUNT="service-${PROJECT_NUMBER}@gcp-sa-dataflow.iam.gserviceaccount.com"

gcloud projects remove-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/storage.objectAdmin"
```

**The better fix — do it before the first job.** The caching only
matters because the service agent already exists. If you create the
service agent by hand with all its roles in one pass, before any job has
ever run, there is nothing to invalidate. This is the single strongest
argument for the hand-creation approach.

> **Diagnostic order for a 403 on GCS.** Work through it in this order,
> because the error message is usually misleading:
>
> 1. Is the **worker** service account missing `roles/storage.objectAdmin`?
>    This is the most common cause, and the error names the worker
>    identity.
> 2. Is the **service agent** missing it too? Check for the caching
>    gotcha, and remove-and-re-add if the role is already present.
> 3. Is the bucket in a **different project** than the one your
>    credentials are scoped to? A cross-project bucket needs a binding
>    in *the bucket's* project, not the job's.
> 4. Is UBLA enabled but the object has a stale fine-grained ACL? Not
>    possible on a fresh UBLA bucket, so this is rare.
> 5. Is the **input** object the problem rather than the output? A
>    `storage.objects.get` 403 on a file that exists is almost always
>    the worker account missing the role.

### Key rotation — and why the answer is "no key"

Service-account keys have a maximum lifetime. Google Cloud IAM enforces
a maximum key age, and a key older than that is automatically
disabled.

**The modern position: do not have keys.** The keyless flow is:

1. You tell Dataflow the worker's service-account **email**.
2. Dataflow's service agent, using the `iamcredentials` API, **mints a
   short-lived OAuth 2.0 access token** for that identity.
3. The token is scoped to the worker's roles and expires in about an
   hour.
4. The worker refreshes it automatically.

Every property of this is better than a key file: the credential
expires on its own, it is never written to disk, it is scoped to the
exact identity and roles, and there is nothing to rotate because there is
nothing persistent.

**If you genuinely must have a key** — an on-prem workload, a system
that cannot use the metadata server, a legacy integration — then:

| Practice | Why |
|---|---|
| Set an expiry of at most 90 days | Limits the blast radius. Google's maximum key age is 100 days, but 90 leaves you a margin. |
| Never commit the key file | Add it to `.gitignore` **and** use a secret manager, not just the ignore file. |
| Prefer Secret Manager or Cloud KMS | Reference the secret by name, not the value. |
| Prefer Workload Identity over a key | On GKE, Workload Identity Federation maps a Kubernetes service account to a GCP one with no key at all. |
| Have a rotation runbook | Know which systems break when you rotate, and when the key is disabled. |

```bash
# Create a key with a 90-day expiry
gcloud iam service-accounts keys create ./dataflow-worker-key.json \
    --iam-account=dataflow-worker@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    --key-file-type=json \
    --expires=2026-12-31T00:00:00Z

# List the keys and their ages
gcloud iam service-accounts keys list \
    --iam-account=dataflow-worker@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    --format="table(name,validAfterTime,expireTime)"

# Disable a key without deleting it (reversible, immediate)
gcloud iam service-accounts keys disable KEY_ID \
    --iam-account=dataflow-worker@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

Disable before delete. `disable` is immediate and reversible; `delete`
is permanent, and a key you delete while a job is running will fail that
job.

### The least-privilege table

This is the table to implement. Roles not listed are not needed.

| Identity | Role | Scope | Purpose |
|---|---|---|---|
| **You (submitter)** | `roles/dataflow.developer` | project | Submit and cancel jobs, read the job graph. |
| **You (submitter)** | `roles/serviceusage.serviceUsageConsumer` | project | Check that APIs are enabled. |
| **You (submitter)** | `roles/iam.serviceAccountUser` | **on the worker SA only** | Act as the worker identity. |
| **You (submitter)** | `roles/storage.objectAdmin` | **on the staging bucket only** | Upload worker code. |
| **Dataflow service agent** | `roles/dataflow.serviceAgent` | project | Create workers, stage code, mint tokens. |
| **Dataflow service agent** | `roles/storage.objectAdmin` | **on the staging and temp buckets only** | Stage code, write shuffle state. |
| **Worker service account** | `roles/dataflow.worker` | project | The baseline worker role. |
| **Worker service account** | `roles/storage.objectAdmin` | **on the input, output, and temp paths only** | Read input, write output, write shuffle state. |
| **Worker service account** | `roles/bigquery.dataEditor` | **on the dataset only** | Only if the pipeline touches BigQuery. |
| **Worker service account** | `roles/pubsub.publisher` / `subscriber` | **on the topic/subscription only** | Only if the pipeline touches Pub/Sub. |

Note how many rows say "only on X". That is the point of least
privilege: the project-level role is the *baseline*, and every data
access is narrowed to a bucket, a dataset, or a topic. The staging and
temp paths are the ones people forget, and they are the ones that
produce the confusing "permission denied" on a job that was otherwise
fine.

### Why BigQuery has no equivalent of this chapter

This is worth calling out, because the contrast is instructive.

**BigQuery does not have workers.** When you write to BigQuery from
BigQuery, there is no VM, no service account running your code, no
staging area, and no temp location. The BigQuery service executes the
work itself. There is no third identity to configure.

That has a concrete consequence for how you reason about BigQuery
pipelines:

| Concern | Dataflow | BigQuery |
|---|---|---|
| Worker identity | A third service account, granted `roles/dataflow.worker` | None — the query runs as the caller. |
| Staging location | Required, must be in GCS | None. |
| Temp location | Required, must be in GCS | None. |
| Compute cost | Billed per worker-hour | Billed per byte scanned. |
| Failure blast radius | A worker VM can be replaced mid-job; the job is retried on another worker | A query either completes or fails; there is no partial state to reconcile. |
| Scaling | You pick worker counts and autoscaling parameters | The service scales; you pick a reservation or a slot count. |
| Region | Job region, and it must match your data | Dataset location, and it is immutable. |

The one thing BigQuery *does* need is a service identity — but it is
the **one you run as**, not a third one. A BigQuery job authenticates
with your ADC and inherits your roles directly.

The practical lesson: **the number of moving identities scales with the
number of moving parts.** BigQuery has fewer parts, so it has fewer
identities, so it has fewer ways to misconfigure. That is not a
coincidence — the identity configuration *is* the complexity.

---

## 🛠️ Hands-On

### Part 1 — Local: inspect the identities the pipeline would use

The course resolves the service-account email from the environment. Check
what it currently resolves to:

```bash
cd data-engineering/data-Course/google/Dataflow
source .venv/bin/activate
python resources/beam_client.py
```

The `service_account` field will read `(not set)`. That is correct for
a local run, and it means the pipeline is running **as you**, in
**your** process, with **no** delegated identity. There is no worker
service account, no service agent, and no bucket. The three-identity
model only exists once you deploy.

Now let the course resolve the runner and see how it treats a cloud
runner:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path("project").resolve()))

from beam_options import build_options, is_local, resolve_runner

for runner in ("BundleBasedDirectRunner", "DirectRunner", "DataflowRunner"):
    options = build_options([f"--runner={runner}"])
    name = resolve_runner(options)
    print(f"{name:24} local={is_local(name)}")
```

```text
BundleBasedDirectRunner   local=True
DirectRunner              local=True
DataflowRunner            local=False
```

`is_local()` is the predicate that decides whether the pipeline demands
a project, a bucket, and a bill. Chapter 4.1's `gcloud` work is only
reachable through that `False`.

### Part 2 — Local: prove that no key is needed

The important claim of this chapter is that a Dataflow job needs no key
file. You can verify the local half of that claim right now: the
pipeline runs with no credentials, no key file, and no `GOOGLE_APPLICATION_CREDENTIALS`
environment variable.

```bash
# Confirm there is no ADC file in the way
ls ~/.config/gcloud/application_default_credentials.json 2>/dev/null \
  && echo "ADC present" \
  || echo "no ADC — and the local runner still works"

# Confirm the pipeline runs with no credentials at all
env -u GOOGLE_APPLICATION_CREDENTIALS \
    python project/batch_pipeline.py \
    --runner BundleBasedDirectRunner \
    --input ./sample_data/orders.csv \
    --output ./out/no_credentials
```

```text
INFO __main__: pipeline finished successfully
```

That succeeded. The local runner needs nothing. When you switch to
`DataflowRunner`, the same code will need a *project* and a *bucket*,
but still not a key — the identity travels as an email address.

### Part 3 — Local: model the three identities in code

The role assignments are `gcloud` calls, but the *shape* of the
configuration is something you can express and test in Python. This is
worth doing, because it is the configuration you will want to template
per environment.

```python
"""A minimal model of the three Dataflow identities and their roles.

This is the shape you will replicate in Terraform, in a deployment
script, or in a runbook. Nothing here talks to GCP.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Identity:
    """One identity in the Dataflow model."""

    name: str
    email: str
    roles: tuple[str, ...]
    scope: str = "project"


@dataclass(frozen=True)
class DataflowIdentities:
    """The three identities a Dataflow job involves."""

    project_id: str
    project_number: str
    bucket: str
    region: str

    @property
    def submitter(self) -> Identity:
        """The identity that submits the job — usually a human or CI account."""
        return Identity(
            name="submitter",
            email=f"ci-runner@{self.project_id}.iam.gserviceaccount.com",
            roles=(
                "roles/dataflow.developer",
                "roles/serviceusage.serviceUsageConsumer",
                "roles/storage.objectAdmin",
            ),
            scope=f"storage bucket {self.bucket}",
        )

    @property
    def service_agent(self) -> Identity:
        """The Google-managed identity that provisions the workers."""
        return Identity(
            name="dataflow-service-agent",
            email=(
                f"service-{self.project_number}"
                "@gcp-sa-dataflow.iam.gserviceaccount.com"
            ),
            roles=(
                "roles/dataflow.serviceAgent",
                "roles/storage.objectAdmin",
            ),
            scope=f"storage bucket {self.bucket}",
        )

    @property
    def worker(self) -> Identity:
        """The identity the pipeline code runs as."""
        return Identity(
            name="dataflow-worker",
            email=f"dataflow-worker@{self.project_id}.iam.gserviceaccount.com",
            roles=(
                "roles/dataflow.worker",
                "roles/storage.objectAdmin",
            ),
            scope=f"storage bucket {self.bucket}",
        )

    def all_identities(self) -> tuple[Identity, ...]:
        """Return the three identities."""
        return (self.submitter, self.service_agent, self.worker)


config = DataflowIdentities(
    project_id="revenue-platform",
    project_number="812345678901",
    bucket="revenue-pipeline-data",
    region="us-central1",
)

for identity in config.all_identities():
    print(f"{identity.name}")
    print(f"  email : {identity.email}")
    print(f"  scope : {identity.scope}")
    for role in identity.roles:
        print(f"  role  : {role}")
    print()
```

```text
submitter
  email : ci-runner@revenue-platform.iam.gserviceaccount.com
  scope : storage bucket revenue-pipeline-data
  role  : roles/dataflow.developer
  role  : roles/serviceusage.serviceUsageConsumer
  role  : roles/storage.objectAdmin

dataflow-service-agent
  email : service-812345678901@gcp-sa-dataflow.iam.gserviceaccount.com
  scope : storage bucket revenue-pipeline-data
  role  : roles/dataflow.serviceAgent
  role  : roles/storage.objectAdmin

dataflow-worker
  email : dataflow-worker@revenue-platform.iam.gserviceaccount.com
  scope : storage bucket revenue-pipeline-data
  role  : roles/dataflow.worker
  role  : roles/storage.objectAdmin
```

Three identities, three email addresses, three role sets, three scopes.
Notice that `roles/dataflow.serviceAgent` appears **only** on the
service agent, and `roles/dataflow.worker` **only** on the worker. That
separation is the point.

### Part 4 — The `gcloud` commands, for when you have a project

Run these **before** your first Dataflow job, not after.

```bash
export PROJECT_ID=YOUR_PROJECT_ID
export BUCKET=YOUR_BUCKET
export REGION=us-central1

# Resolve the project number
export PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
export SERVICE_AGENT="service-${PROJECT_NUMBER}@gcp-sa-dataflow.iam.gserviceaccount.com"
export WORKER_SA="dataflow-worker@${PROJECT_ID}.iam.gserviceaccount.com"

# 1. Create the bucket with uniform bucket-level access
gcloud storage buckets create "gs://${BUCKET}" \
    --location="$REGION" \
    --uniform-bucket-level-access

# 2. Create the worker service account
gcloud iam service-accounts create dataflow-worker \
    --project="$PROJECT_ID" \
    --display-name="Dataflow Worker"

# 3. Create the Dataflow service agent BY HAND, with its roles
gcloud iam service-accounts create "service-${PROJECT_NUMBER}" \
    --project="$PROJECT_ID" \
    --display-name="Dataflow Service Agent" || true

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SERVICE_AGENT}" \
    --role="roles/dataflow.serviceAgent"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SERVICE_AGENT}" \
    --role="roles/storage.objectAdmin"

# 4. Grant the worker its roles
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${WORKER_SA}" \
    --role="roles/dataflow.worker"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${WORKER_SA}" \
    --role="roles/storage.objectAdmin"

# 5. Confirm the policy — every role above should be present
gcloud projects get-iam-policy "$PROJECT_ID" \
    --flatten="bindings[].members" \
    --filter="bindings.members:(${SERVICE_AGENT}|${WORKER_SA})" \
    --format="table(bindings.role,bindings.members)"
```

Expected output:

```text
bindings.role                              bindings.members
roles/dataflow.serviceAgent                serviceAccount:service-812345678901@gcp-sa-dataflow.iam.gserviceaccount.com
roles/dataflow.worker                      serviceAccount:dataflow-worker@revenue-platform.iam.gserviceaccount.com
roles/storage.objectAdmin                  serviceAccount:dataflow-worker@revenue-platform.iam.gserviceaccount.com
roles/storage.objectAdmin                  serviceAccount:service-812345678901@gcp-sa-dataflow.iam.gserviceaccount.com
```

**Notice: no key was created.** Step 5 is the whole setup. There is no
`gcloud iam service-accounts keys create` anywhere in that list, and
that is deliberate.

Finally, wire it into the course:

```bash
export SERVICE_ACCOUNT_EMAIL="$WORKER_SA"
export STAGING_LOCATION="gs://${BUCKET}/dataflow/staging"
export TEMP_LOCATION="gs://${BUCKET}/dataflow/temp"

python resources/beam_client.py
```

### Part 5 — Reproduce the caching gotcha (optional, costs nothing)

This is worth doing once, because the symptom is so confusing that
seeing it deliberately makes it recognisable later. It requires a
project.

```bash
# 1. Remove the storage role from the service agent
gcloud projects remove-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SERVICE_AGENT}" \
    --role="roles/storage.objectAdmin"

# 2. Show the policy — the role really is gone
gcloud projects get-iam-policy "$PROJECT_ID" \
    --flatten="bindings[].members" \
    --filter="bindings.members:${SERVICE_AGENT}" \
    --format="value(bindings.role)"

# 3. Add it back
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SERVICE_AGENT}" \
    --role="roles/storage.objectAdmin"

# 4. Now do the remove-and-re-add dance, which is the actual fix
gcloud projects remove-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SERVICE_AGENT}" \
    --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SERVICE_AGENT}" \
    --role="roles/storage.objectAdmin"
```

The lesson is not the four commands. The lesson is that **step 2
shows the role present, and a job can still fail** — because the
service agent's policy is cached from creation time, and the only
supported way to invalidate that cache is to remove the binding and
add it back.

---

## 🛠️ Common Errors and Fixes

### `403: ... does not have storage.objects.get access to the Google Cloud Storage object`

**The actual message:**

```text
google.api_core.exceptions.Forbidden: 403 GET https://storage.googleapis.com/storage/v1/b/YOUR_BUCKET/o/orders.csv?alt=media: ci-runner@revenue-platform.iam.gserviceaccount.com does not have storage.objects.get access to the Google Cloud Storage object.
```

Notice the identity in the message. **That is the account that lacks the
role** — read it, do not guess.

**The fix.** The first thing to establish is *which* identity that is:

- If it is the **worker** account (`dataflow-worker@...`), it needs
  `roles/storage.objectAdmin` on the bucket.
- If it is the **submitter** account, it needs it on the staging bucket.
- If it is the **service agent** account (`service-<number>@gcp-sa-dataflow...`),
  you have the caching gotcha — remove and re-add the role.

```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:${WORKER_SA}" \
    --role="roles/storage.objectAdmin"
```

### `The caller does not have permission` on the service agent's own email

**The actual message:**

```text
google.api_core.exceptions.PermissionDenied: The caller does not have permission
```

**The cause.** You are trying to grant a role to a service account that
does not exist yet, or you are using the wrong project number.

**The fix.** Create the service agent first, then grant:

```bash
gcloud iam service-accounts create "service-${PROJECT_NUMBER}" \
    --project=YOUR_PROJECT_ID \
    --display-name="Dataflow Service Agent"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-dataflow.iam.gserviceaccount.com" \
    --role="roles/dataflow.serviceAgent"
```

### `The request was forbidden: ... is not authorized to perform serviceusage.services.enable`

**The actual message:**

```text
google.api_core.exceptions.PermissionDenied: The request was forbidden: 1234567890@cloudservices.gserviceaccount.com is not authorized to perform serviceusage.services.enable on the project YOUR_PROJECT_ID.
```

**The cause.** You are enabling an API as a service account that lacks
`roles/serviceusage.serviceUsageAdmin` (or is a service agent with the
`service-<number>` prefix, which is managed by Google and cannot be
given extra roles).

**The fix.** Enable APIs with your own user account, and remember that
the `service-...@gcp-sa-dataflow.iam.gserviceaccount.com` identity is
**not yours to grant roles to** beyond what Google already gives it.

```bash
gcloud auth list
gcloud services enable dataflow.googleapis.com
```

### `Dataflow job creation failed: ... the service account does not have the required permissions`

**The actual message:**

```text
RuntimeError: Dataflow job creation failed: The provided service account (dataflow-worker@revenue-platform.iam.gserviceaccount.com) does not have the role roles/dataflow.worker in the project.
```

**The fix.**

```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:dataflow-worker@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/dataflow.worker"
```

### `The requester does not have permission to act as the service account`

**The actual message:**

```text
google.api_core.exceptions.Forbidden: The caller does not have permission 'iam.serviceAccounts.actAs' on service account 'dataflow-worker@revenue-platform.iam.gserviceaccount.com'.
```

**The cause.** The **submitter** is not allowed to act as the worker
account. This is the `roles/iam.serviceAccountUser` grant, and it is
granted on the *service account*, not on the project.

**The fix.**

```bash
gcloud iam service-accounts add-iam-policy-binding \
    dataflow-worker@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    --member="user:you@example.com" \
    --role="roles/iam.serviceAccountUser"
```

### `Bucket is owned by another project`

**The actual message:**

```text
google.api_core.exceptions.Forbidden: 403 GET https://storage.googleapis.com/storage/v1/b/YOUR_BUCKET: your-service-account@YOUR_PROJECT_ID.iam.gserviceaccount.com does not have storage.buckets.get access to the Google Cloud Storage bucket.
```

**The cause.** The bucket name is globally unique, and someone else
already owns `YOUR_BUCKET`. This is not a permissions problem with
your setup — the bucket is not yours.

**The fix.** Pick a different, unique name. Add a random suffix:

```bash
gcloud storage buckets create "gs://${BUCKET}-$(date +%s)" \
    --location="$REGION" \
    --uniform-bucket-level-access
```

### `The key file is not a valid service account credential`

**The actual message:**

```text
google.auth.exceptions.MalformedError: File ./key.json is not a valid credential file.
```

**The cause.** The JSON key is truncated, has been edited, or is an
older key format that this library version no longer accepts.

**The fix.** Create a fresh key, and strongly consider not creating one
at all — see the keyless section above. If you truly need a key:

```bash
gcloud iam service-accounts keys create ./dataflow-worker-key.json \
    --iam-account=dataflow-worker@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    --key-file-type=json \
    --expires=2026-12-31T00:00:00Z
```

### `Failed to create the Dataflow job: ... does not have permission to act as the service account`

**The actual message:**

```text
RuntimeError: Failed to create the Dataflow job: The Dataflow service agent service-812345678901@gcp-sa-dataflow.iam.gserviceaccount.com does not have permission to act as the service account dataflow-worker@revenue-platform.iam.gserviceaccount.com.
```

**The cause.** The service agent cannot act as the worker account. Either
the worker account does not exist, or the service agent has not been
granted `roles/iam.serviceAccountUser` on it.

**The fix.**

```bash
gcloud iam service-accounts add-iam-policy-binding \
    dataflow-worker@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    --member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-dataflow.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"
```

---

## 💡 Production Notes

- **Create the Dataflow service agent by hand, before the first job.**
  The automatic creation happens at submission time, which is too late
  to fail cleanly. Hand-creation costs one extra command and eliminates
  an entire class of first-job failures.

- **The role names in this table are not decoration.** Swapping
  `roles/dataflow.serviceAgent` for `roles/dataflow.worker` on the
  worker account will make a pipeline that can *create VMs* — that is,
  one that can spend money and reach other projects' networks. Keep them
  separate.

- **Narrow the storage grant to the bucket, not the project.** A
  project-level `roles/storage.objectAdmin` on the worker account means
  the pipeline can read and delete every object in the project, including
  the audit logs of whatever else lives there. Bind the role at the
  bucket:

```bash
gcloud storage buckets add-iam-policy-binding "gs://${BUCKET}" \
    --member="serviceAccount:${WORKER_SA}" \
    --role="roles/storage.objectAdmin"
```

- **Do not forget the temp location in the storage grant.** The shuffle
  state lives there, and the worker needs to write it. Granting storage
  on the output path but not the temp path gives you a job that reads
  fine and then fails halfway through with a 403 on a path you did not
  know was in play.

- **Audit the key list, not just the key count.** A zero-key service
  account is a good state. One key that expires in 200 days is a smell.
  Run the list command in a monthly job and alert on anything.

- **In a shared project, use separate service accounts per pipeline.**
  One shared worker account across pipelines means one compromised
  pipeline has the union of every pipeline's access, and the audit log
  cannot tell you which pipeline did what.

- **Do not use the service agent as the worker account.** It is
  possible, it will work, and it grants your pipeline code the ability
  to create VMs. The service agent is a control-plane identity; the
  worker is a data-plane identity. Keep them separate.

---

## 🔑 Key Takeaways

- **Dataflow has three identities**, not one: the **submitter** (you),
  the **Dataflow service agent** (creates workers, mints tokens), and
  the **worker service account** (the identity your code runs as).
- **The roles are not interchangeable.**
  `roles/dataflow.serviceAgent` belongs to the control plane;
  `roles/dataflow.worker` belongs to the data plane. Granting the
  former to your worker account lets your pipeline create VMs.
- **A user key file is a security incident**, not a shortcut. A Dataflow
  job should have no key at all — the identity travels as an email
  address and the credential is minted for one hour at run time.
- **Create the service agent by hand, with its roles, before the first
  job.** The automatic creation happens at submission time, which is
  too late to fail cleanly.
- **The caching gotcha is real:** adding a role to an already-created
  service agent requires removing and re-adding it, because Dataflow
  caches the policy at creation time.
- **Use uniform bucket-level access**, bind storage roles to the bucket
  rather than the project, and remember that the **temp location** needs
  the storage role too.
- **BigQuery has no equivalent of this chapter** because it has no
  workers, no staging area, and no temp location. The number of moving
  identities scales with the number of moving parts.

---

## 📚 Practice Exercises

1. **Write the Terraform.** Create a `main.tf` that provisions the
   bucket (with UBLA), the worker service account, the Dataflow service
   agent, and every binding in the least-privilege table — with the
   storage bindings scoped to the bucket, not the project. Then explain
   what happens to your Terraform state when you destroy the project.

2. **Audit an over-privileged setup.** Write a script that reads
   `gcloud projects get-iam-policy` as JSON and flags any of these:
   a service account with a key older than 90 days; the worker service
   account holding `roles/dataflow.serviceAgent`; any identity holding
   `roles/owner`; any user service account with a key file referenced in
   a pipeline's arguments. Run it against your own project.

3. **Prove the caching gotcha.** In a project, grant the service agent
   `roles/storage.objectAdmin` *after* it has been created, submit a job
   that writes to GCS, and record the failure. Then remove and re-add
   the binding and record the success. Time both attempts. Note in your
   write-up why the role was present in the policy the whole time.

4. **Model the three identities in code.** Extend the `DataflowIdentities`
   dataclass from the hands-on to support pipelines that touch BigQuery
   and Pub/Sub. Add the extra roles conditionally — a pipeline with no
   BigQuery sink should not grant `roles/bigquery.dataEditor`. Then
   write a test that asserts the worker never holds
   `roles/dataflow.serviceAgent`.

5. **Design the rotation runbook.** Write the exact steps for rotating
   credentials for a pipeline that *does* need a key. Include: how you
   create the new key, how you deploy it, how you verify the new key
   works, the order of operations for cutting over, and how you revoke
   the old one. State which step has to happen first and why.

6. **Reflect.** Chapter 4.1 said the free tier does not make Dataflow
   free because workers are Compute Engine VMs. Given what you now know
   about the three identities, explain which one is responsible for
   creating those VMs, and therefore which one you would scope down
   first if you wanted to reduce the blast radius of a compromised
   pipeline.

---

## 📖 Further Reading

- Dataflow access control and service accounts — https://cloud.google.com/dataflow/docs/access-control
- Dataflow service agent — https://cloud.google.com/dataflow/docs/service-account
- Creating and managing service accounts — https://cloud.google.com/iam/docs/service-accounts
- Creating short-lived service account credentials — https://cloud.google.com/iam/docs/create-short-lived-credentials-direct
- Service account key management — https://cloud.google.com/iam/docs/keys-manage
- Workload Identity Federation — https://cloud.google.com/iam/docs/workload-identity-federation
- Uniform bucket-level access — https://cloud.google.com/storage/docs/uniform-bucket-level-access
- Cloud Storage IAM roles — https://cloud.google.com/storage/docs/access-control/iam-roles
