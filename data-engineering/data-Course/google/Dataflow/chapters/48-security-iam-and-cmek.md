# 8.5 — Security, IAM & CMEK

> **Section 8 · Production Operations · Lecture 8.5 · 6:30**

## 🎯 What you will learn

- The three identities in a Dataflow job, and exactly what each one is allowed to do
- Least privilege in practice: scoping a worker service account to specific buckets
- Private IP and VPC-native jobs — what they are, why compliance cares, and how to ask for them
- CMEK: what customer-managed encryption keys actually change, and the four things that must be true
- Service account impersonation as the supported way into a customer VPC
- VPC Service Controls as a data-exfiltration control, not an IAM control
- Audit logging: reading the Dataflow audit trail and reconstructing "who ran what"
- Why a secret in a pipeline parameter is a secret in plain text, and what to do instead
- The production security checklist to run against every template you ship

---

## 🧠 Concept

### The three identities

Every Dataflow job involves three separate Google Cloud service accounts.
Confusing them is the single most common cause of a job that fails to start
or a job that can read far too much. Get them straight before anything
else.

| Identity | Who creates it | What it does | Typical role |
|---|---|---|---|
| **The caller** | you | submits the job, reads the template, may cancel it | `roles/dataflow.developer` |
| **The Dataflow service agent** | Google, per project and per region | creates the Compute Engine workers, manages the job, stages files, writes the job metadata | `roles/dataflow.serviceAgent` |
| **The worker service account** | you | the identity the *worker VMs* run as when they touch your data | `roles/dataflow.worker` |

The service agent is a singleton per project+region with a fixed address:

```text
service-<PROJECT_NUMBER>@gcp-sa-dataflow.iam.gserviceaccount.com
```

The worker service account is any account you choose, passed with
`--service_account_email`. A very common default is the service agent
itself, which is convenient and *over-permissioned* — the workers then
inherit the service agent's access to every bucket in the project.

The caller's identity matters in two ways people forget:

1. **The caller must be able to impersonate the worker service account.**
   If the caller holds `roles/iam.serviceAccountUser` on the wrong account,
   the job fails with a permission error at launch even though the worker
   account itself is perfectly configured.
2. **The caller must be able to act as the Dataflow service agent** to
   create workers on their behalf. This is what `roles/dataflow.developer`
   grants when it is granted at the project level.

### Least privilege, concretely

The default `roles/dataflow.worker` role is broad: it can read and write
Cloud Storage, create BigQuery jobs, publish to Pub/Sub, and read several
other services. For a pipeline that only reads one bucket and writes one
bucket, that is far more than it needs.

The production pattern is to grant the worker service account
object-level access on exactly the buckets it touches, and nothing else:

```bash
# The worker account may read the input bucket...
gcloud storage buckets add-iam-policy-binding gs://YOUR_BUCKET \
  --member=serviceAccount:beam-worker@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/storage.objectViewer

# ...and write the output bucket.
gcloud storage buckets add-iam-policy-binding gs://YOUR_BUCKET \
  --member=serviceAccount:beam-worker@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/storage.objectCreator
```

`roles/storage.objectCreator` (write-only, no read) is the right role for
the output bucket, and `roles/storage.objectViewer` (read-only) for the
input. Splitting them this way means a compromised worker cannot read back
the data it wrote, and cannot write into the input bucket.

When the pipeline needs more than Storage — BigQuery, Pub/Sub, Cloud
KMS, a Secret Manager secret — grant those individually, per resource where
the resource supports it:

```bash
# BigQuery, scoped to one dataset.
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member=serviceAccount:beam-worker@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/bigquery.dataEditor \
  --condition='resource.name.startsWith("projects/YOUR_PROJECT_ID/datasets/revenue")'
```

**A custom role** is the right answer when the built-in roles are either
too broad or cannot express what you need — a role that says "read objects
in these buckets, nothing else" is often the cleanest audit story. Custom
roles are defined in YAML and attached to the worker service account:

```yaml
# dataflow-worker-scope.yaml
title: Dataflow Worker Bucket Scope
description: Read one input bucket, write one output bucket. Nothing else.
includedPermissions:
  - storage.buckets.get
  - storage.objects.get
  - storage.objects.list
  - storage.objects.create
  - storage.objects.delete
excludedPermissions:
  - resourcemanager.projects.delete
  - resourcemanager.projects.getIamPolicy
stage: GA
```

```bash
gcloud iam roles create dataflowWorkerScope \
  --project YOUR_PROJECT_ID \
  --file=dataflow-worker-scope.yaml

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member=serviceAccount:beam-worker@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --role=projects/YOUR_PROJECT_ID/roles/dataflowWorkerScope
```

### Private IP and VPC-native jobs

A default Dataflow worker is a Compute Engine VM with an **ephemeral
external IP address**. Its traffic to Cloud Storage, BigQuery, Pub/Sub and
the Google APIs leaves the VPC over the public internet. For a lot of
workloads that is fine. For a lot of regulated workloads it is not.

**VPC-native (private IP) jobs** run the workers inside your own VPC with
no external IP address at all. Traffic to Google services stays on Google's
private backbone. The flags:

```bash
gcloud dataflow jobs run my-job \
  --project YOUR_PROJECT_ID \
  --region us-central1 \
  --network my-vpc \
  --subnetwork my-subnet \
  --no-public-ip \
  --service-account-email beam-worker@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --temp-location gs://YOUR_BUCKET/tmp \
  --staging-location gs://YOUR_BUCKET/staging
```

| Flag | Effect |
|---|---|
| `--network` | the VPC the workers join |
| `--subnetwork` | the subnet within that VPC (and, for VPC-native, the subnet's region must match the job's region) |
| `--no-public-ip` | workers get no external IP; they reach Google APIs over the private backbone |
| `--use-public-ips` | explicitly *allow* public IPs (the default is to allow them) |
| `--service-account-email` | the identity the workers run as |

Note the symmetry in the last two: `--no-public-ip` and `--use-public-ips`
are two spellings of the same underlying `use_public_ips` setting, one
negative and one positive. Some `gcloud` versions accept only one of
them; `--no-public-ip` is the current documented spelling.

Three practical requirements for a private-IP job:

1. **The subnet must have Private Google Access enabled**, and a private
   range that does not overlap your on-premises network.
2. **The subnet's region must match the job's region.** A
   `us-central1` job cannot use a `us-east1` subnet, and Dataflow will
   reject the launch with a confusing message about VPC peering.
3. **The Dataflow service agent needs `roles/compute.networkUser`** on the
   subnet, so it can attach workers to it.

```bash
gcloud compute networks subnets update my-subnet \
  --region us-central1 \
  --enable-private-ip-google-access

gcloud compute subnets add-iam-policy-binding my-subnet \
  --region us-central1 \
  --member=serviceAccount:service-PROJECT_NUMBER@gcp-sa-dataflow.iam.gserviceaccount.com \
  --role=roles/compute.networkUser
```

Why compliance cares: a private-IP job has **no route to the public
internet at all**. Data cannot leave except through the Google APIs the
worker is authorised to call. That turns "we did not exfiltrate data" from
a policy statement into a network-level property, which is exactly the
kind of claim a regulator or a bank's internal security team will accept.

### CMEK — customer-managed encryption keys

By default, Dataflow encrypts your data at rest with **Google-managed
keys** (Google owns the key, Google rotates it, and you have no
visibility into or control over the key lifecycle). **CMEK** replaces
those with a key you create and own in Cloud KMS.

The mechanism is not complicated, but it has four preconditions that are
frequently missed, and each one produces a different failure.

```bash
# 1. A keyring in the region where the data will live.
gcloud kms keyrings create dataflow-keyring \
  --location us-central1 \
  --project YOUR_PROJECT_ID

# 2. A key in that keyring.
gcloud kms keys create dataflow-job-key \
  --location us-central1 \
  --keyring dataflow-keyring \
  --purpose encryption \
  --project YOUR_PROJECT_ID

# 3. The Dataflow service agent must be able to use the key.
gcloud kms keys add-iam-policy-binding \
  projects/YOUR_PROJECT_ID/locations/us-central1/keyRings/dataflow-keyring/cryptoKeys/dataflow-job-key \
  --member=serviceAccount:service-PROJECT_NUMBER@gcp-sa-dataflow.iam.gserviceaccount.com \
  --role=roles/cloudkms.cryptoKeyEncrypterDecrypter \
  --project YOUR_PROJECT_ID
```

Then point the job at the key:

```bash
gcloud dataflow jobs run my-job \
  --project YOUR_PROJECT_ID \
  --region us-central1 \
  --kms-key projects/YOUR_PROJECT_ID/locations/us-central1/keyRings/dataflow-keyring/cryptoKeys/dataflow-job-key \
  --temp-location gs://YOUR_BUCKET/tmp \
  --staging-location gs://YOUR_BUCKET/staging
```

The four preconditions, each of which fails differently:

| Precondition | Failure if violated |
|---|---|
| The key exists and is enabled | `KMS key not found` at launch |
| The key is in the **same region as the data** | `Permission denied` on the key, or a "location mismatch" error — KMS keys never leave their region |
| The Dataflow service agent holds `cloudkms.cryptoKeyEncrypterDecrypter` on the key | `403 PERMISSION_DENIED` on `cloudkms.cryptoKeyVersions.useToEncrypt` |
| The key's purpose is `encryption` | rejected at launch |

A note on scope. The `--kms-key` flag keys the job's **staging, temp and
job metadata** — the files Dataflow writes on your behalf in GCS, and the
shuffle data. It does **not** re-key the Cloud Storage bucket the data
lives in, and it does not re-key a BigQuery table. If your requirement is
"the data is encrypted with a key we control", you still need a
**bucket-level CMEK** (a `gcloud storage buckets update
--default-encryption-key`) and a **BigQuery CMEK key** on the dataset. The
two are complementary, not alternatives. Many organisations end up with
all three, because the audit asks about each layer separately.

The practical argument for CMEK beyond the compliance checkbox is
**key rotation and revocation**. Because you own the key, you can rotate
it without re-uploading your data, and you can revoke it to make existing
ciphertext permanently unreadable. That is a real capability you do not
have with Google-managed keys.

### Service account impersonation for a customer VPC

When the workers must reach into a VPC you do not own — a customer
network, a partner network, an on-premises cluster behind Cloud VPN —
the pattern is **service account impersonation**. The Dataflow job runs
as a service account that the *customer* can trust, and that service
account impersonates a dedicated identity in the customer project.

```bash
# The Dataflow job runs as the Dataflow service agent (or a dedicated
# worker account) and impersonates a customer-project account.
gcloud iam service-accounts create dataflow-vpc-runner \
  --project YOUR_PROJECT_ID

# The Dataflow service agent must be allowed to impersonate it.
gcloud iam service-accounts add-iam-policy-binding \
  dataflow-vpc-runner@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --project YOUR_PROJECT_ID \
  --member=serviceAccount:service-PROJECT_NUMBER@gcp-sa-dataflow.iam.gserviceaccount.com \
  --role=roles/iam.serviceAccountTokenCreator
```

Then grant *that* account the network reach:

```bash
gcloud compute networks add-iam-policy-binding my-shared-vpc \
  --member=serviceAccount:dataflow-vpc-runner@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/compute.networkUser
```

The impersonation chain is:

```text
caller  --serviceAccountTokenCreator-->  dataflow-vpc-runner
                                              |
                                              +-- runs on the worker
                                              +-- reaches the customer VPC
```

The security property: the worker never holds the customer's credentials.
It holds a short-lived OAuth token minted on the customer's behalf, with
the customer's own policy deciding what it can reach. The Dataflow project
never stores the customer's key material. This is the pattern that makes
a shared-VPC or cross-project deployment auditable — the customer can
audit the impersonated account, revoke it, and see exactly what the job
did under its identity.

### VPC Service Controls

IAM answers *"is this identity allowed to do this?"*. VPC Service Controls
answers a different question: *"is this identity allowed to do this with
this data, even though IAM says yes?"*

The perimeter sits around a set of services and resources. Data can only
cross the perimeter if both the source and the destination are inside it
(or an explicit exception is granted). A Dataflow worker reading from a
bucket outside the perimeter and writing to a BigQuery table inside it
will be **blocked**, with an error in the audit log naming the perimeter
and the blocked egress.

For Dataflow this has one specific consequence people miss: **the staging
and temp locations must be inside the perimeter**, because Dataflow moves
data through them as part of every job. A job with
`--temp-location gs://outside-the-perimeter/tmp` and a source inside the
perimeter will fail with a `VPC Service Controls` violation even though
every IAM check passes.

Two mechanisms are worth knowing:

- **Ingress rules** — allow a specific path across the perimeter, e.g.
  "this one external bucket may be read by jobs in this perimeter".
- **Egress rules** — allow data to leave the perimeter to a specific
  destination, e.g. "analytics results may be exported to this partner
  project".

The realistic scope of VPC Service Controls is large — it needs
coordinated configuration across Storage, BigQuery, Pub/Sub, IAM and
KMS, and it changes how you write pipelines (no more reading from a
"helpful" public bucket). For most teams it is an enterprise-scale
program, not a sprint. But you should know it exists, know that it
constrains where you put your temp and staging locations, and know that
"we could add VPC-SC later" is not quite true.

### Audit logging

Dataflow writes **Dataflow audit logs** to Cloud Audit Logs, and so do
GCS, BigQuery and KMS. These are the answers to "who ran what".

The log types you care about:

| Log | What it records | Type |
|---|---|---|
| `dataflow.googleapis.com/Activity` | job creation, update, cancellation | `ADMIN_READ` |
| `dataflow.googleapis.com/DataAccess` | job state snapshots, worker metrics | `DATA_READ` |
| `dataflow.googleapis.com/JobMessage` | messages Dataflow emits about a job | `DATA_READ` |
| `storage.googleapis.com/ObjectRead` / `ObjectData` | who read/wrote which object | `DATA_READ` / `DATA_WRITE` |
| `cloudkms.googleapis.com/CryptoKeyAccess` | who used which key | `DATA_READ` |

Reading them:

```bash
# Every job activity in the last 24 hours, with the caller.
gcloud logging read \
  'resource.type="dataflow_step" OR protoPayload.resourceName:"projects/YOUR_PROJECT_ID/locations" \
   AND protoPayload.methodName:"jobs.createJob"' \
  --project YOUR_PROJECT_ID \
  --limit=50 \
  --format='table(timestamp, protoPayload.authenticationInfo.principalEmail, protoPayload.methodName, protoPayload.resourceName)'

# The audit trail for one specific job.
gcloud dataflow jobs describe JOB_ID \
  --project YOUR_PROJECT_ID \
  --region us-central1 \
  --format=json > job.json
```

`gcloud dataflow jobs describe` returns the `jobMetadata` block, which
records the **user who submitted the job**, the SDK version, the job name,
the parameters, the state, and the worker service account. It is the
single most useful command for "who ran this and with what".

Two audit-log settings are worth turning on in a production project:

- **Data Access logs** — by default, GCS and BigQuery data-access logs
  are **off** (they are high-volume). Turn them on for the buckets that
  matter, so you can answer "who read this object".
- **Log retention** — Cloud Logging retains for a bounded period
  (30 days by default, longer with log buckets). If your compliance
  requirement is a two-year audit trail, you need a **log bucket with a
  retention policy**, not the default `_Default` sink.

### The "never use a user key" rule, restated

The concrete failure mode, because "don't do it" without a reason is just
a slogan:

You write a flex template and put an API key in a parameter:

```text
gcloud dataflow jobs run my-job \
  --image gcr.io/YOUR_PROJECT_ID/dataflow/batch-template:latest \
  --api-key AIzaSyD-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

What happens:

1. The parameter is stored **in the job metadata** in the Dataflow
   control plane.
2. `gcloud dataflow jobs describe JOB_ID` prints it, in plain text, to
   anyone with `roles/dataflow.viewer` — which usually means everyone on
   the team, including contractors.
3. It appears in the **Cloud Audit Logs** entry for the job creation.
4. It appears in the **shell history** of whoever ran the command.
5. It is visible in the **Dataflow web UI** on the job parameters panel.
6. If the key is a *user* key, revoking it requires the human who owns
   it to go and rotate it — and until they do, the leak is live.

The correct pattern is to pass a **Secret Manager resource path**, not a
secret value, and to fetch the secret at runtime:

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions


class ReadSecretFn(beam.DoFn):
    """Fetch a secret from Secret Manager at runtime, never at build time."""

    def __init__(self, project_id: str, secret_id: str, version: str = "latest"):
        self._project_id = project_id
        self._secret_id = secret_id
        self._version = version

    def process(self, _ignored):
        from google.cloud import secretmanager

        client = secretmanager.SecretManagerServiceClient()
        name = (
            f"projects/{self._project_id}/secrets/{self._secret_id}/versions/{self._version}"
        )
        response = client.access_secret_version(request={"name": name})
        payload = response.payload.data.decode("utf-8")
        yield payload
```

The worker service account needs `roles/secretmanager.secretAccessor` on
that one secret, and the secret value never appears in job metadata, in
the audit log, in the UI, or in a shell history. The *name* of the secret
is not sensitive; the value is. Pass the name.

### The production security checklist

Run this against every template before it ships:

| # | Check | How |
|---|---|---|
| 1 | A dedicated worker service account, not the service agent | `--service_account_email` points at a named account |
| 2 | Worker SA scoped to specific buckets | `gcloud storage buckets get-iam-policy` shows object-level bindings, not project-level |
| 3 | The caller can impersonate the worker SA | `roles/iam.serviceAccountUser` on the worker account |
| 4 | Private IP where the compliance regime requires it | `--no-public-ip --network ... --subnetwork ...` |
| 5 | The staging and temp locations are inside the VPC-SC perimeter | checked against the perimeter definition |
| 6 | CMEK configured if the policy requires it | `--kms-key` plus a bucket-level CMEK |
| 7 | No secrets in parameters | grep the template and the launch scripts for anything that looks like a credential |
| 8 | Secrets fetched from Secret Manager at runtime | `roles/secretmanager.secretAccessor` on the worker SA only |
| 9 | Data Access logs on for the sensitive buckets | `gcloud storage buckets update --enable-data-access-logging` |
| 10 | A log sink with the required retention | `gcloud logging sinks list` |

---

## 🛠️ Hands-On: Auditing and Hardening a Job

Everything below that needs a project is optional and clearly marked. The
local parts run with no credentials.

### Step 1 — See what your template leaks

Start by looking at what a job's parameters actually contain. This works
on any Dataflow project.

```bash
# The full job metadata, including the parameters you passed.
gcloud dataflow jobs describe JOB_ID \
  --project YOUR_PROJECT_ID \
  --region us-central1 \
  --format='yaml(metadata.name, metadata.parameters, jobMetadata)'
```

Look at `jobMetadata.parameters` — every `--key value` you passed at
launch is there, verbatim.

### Step 2 — Build a secret-fetching DoFn and test it locally

The Secret Manager client is not installed in the course virtualenv, so
the import is inside the `DoFn` — which is correct anyway, because the
client is created per worker, not per pipeline. Here is the local-safe
version, with the network call stubbed:

```python
import apache_beam as beam


class FetchSecretFn(beam.DoFn):
    """Fetch one secret from Secret Manager, once per worker.

    The client is created inside `process` (not `__init__`) because the
    `DoFn` is pickled and shipped to the workers, and a live gRPC channel
    cannot be pickled.
    """

    def __init__(self, project_id: str, secret_id: str, version: str = "latest"):
        self._project_id = project_id
        self._secret_id = secret_id
        self._version = version

    def _path(self) -> str:
        return (
            f"projects/{self._project_id}/secrets/{self._secret_id}"
            f"/versions/{self._version}"
        )

    def process(self, _trigger):
        from google.cloud import secretmanager

        client = secretmanager.SecretManagerServiceClient()
        response = client.access_secret_version(request={"name": self._path()})
        yield response.payload.data.decode("utf-8")
```

A `DoFn` that takes a side input, so the secret is only fetched when
there is work to do:

```python
import apache_beam as beam


class SecretLookupFn(beam.DoFn):
    """Resolve a secret id to its value, using a side input."""

    def __init__(self, project_id: str):
        self._project_id = project_id

    def process(self, secret_id: str, known=beam.pvalue.AsDict("known")):
        from google.cloud import secretmanager

        if secret_id not in known:
            yield None
            return
        client = secretmanager.SecretManagerServiceClient()
        name = (
            f"projects/{self._project_id}/secrets/{secret_id}/versions/latest"
        )
        response = client.access_secret_version(request={"name": name})
        yield response.payload.data.decode("utf-8")
```

### Step 3 — Check the identities the template will use

The course templates take the worker service account from the
environment, via `beam_options.describe_environment()`:

```bash
cd data-engineering/data-Course/google/Dataflow
source .venv/bin/activate
python -c "
from beam_options import describe_environment
import json
print(json.dumps(describe_environment(), indent=2))
"
```

You should see `"service_account": "(not set)"` locally. In a Dataflow
environment it is populated from `SERVICE_ACCOUNT_EMAIL`.

### Step 4 — Grant the least-privilege bindings

On a real project, this is the sequence:

```bash
# Create a dedicated worker account.
gcloud iam service-accounts create beam-worker \
  --project YOUR_PROJECT_ID \
  --display-name="Dataflow worker"

# Read on the input bucket only.
gcloud storage buckets add-iam-policy-binding gs://YOUR_BUCKET \
  --member=serviceAccount:beam-worker@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/storage.objectViewer

# Write on the output bucket only.
gcloud storage buckets add-iam-policy-binding gs://YOUR_BUCKET \
  --member=serviceAccount:beam-worker@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/storage.objectCreator

# The caller needs to be able to act as the worker.
gcloud iam service-accounts add-iam-policy-binding \
  beam-worker@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --project YOUR_PROJECT_ID \
  --member=group:data-engineers@example.com \
  --role=roles/iam.serviceAccountUser

# The service agent needs Cloud KMS on the key.
gcloud kms keys add-iam-policy-binding \
  projects/YOUR_PROJECT_ID/locations/us-central1/keyRings/dataflow-keyring/cryptoKeys/dataflow-job-key \
  --member=serviceAccount:service-PROJECT_NUMBER@gcp-sa-dataflow.iam.gserviceaccount.com \
  --role=roles/cloudkms.cryptoKeyEncrypterDecrypter \
  --project YOUR_PROJECT_ID
```

### Step 5 — Launch a private-IP, CMEK job

```bash
gcloud dataflow jobs run secure-batch \
  --project YOUR_PROJECT_ID \
  --region us-central1 \
  --image gcr.io/YOUR_PROJECT_ID/dataflow/batch-template:latest \
  --network my-vpc \
  --subnetwork my-subnet \
  --no-public-ip \
  --service-account-email beam-worker@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --kms-key projects/YOUR_PROJECT_ID/locations/us-central1/keyRings/dataflow-keyring/cryptoKeys/dataflow-job-key \
  --temp-location gs://YOUR_BUCKET/tmp \
  --staging-location gs://YOUR_BUCKET/staging \
  --input gs://YOUR_BUCKET/orders.csv \
  --output gs://YOUR_BUCKET/summary
```

### Step 6 — Verify the audit trail

```bash
# Who created jobs in the last day, and with what parameters?
gcloud logging read \
  'protoPayload.resourceName:"projects/YOUR_PROJECT_ID/locations" \
   AND protoPayload.methodName:"CreateJob"' \
  --project YOUR_PROJECT_ID \
  --limit=20 \
  --format='table(timestamp, protoPayload.authenticationInfo.principalEmail, protoPayload.resourceName)'
```

```bash
# Is data-access logging on for the bucket?
gcloud storage buckets get-iam-policy gs://YOUR_BUCKET \
  --format=json | head -40
```

### Step 7 — The checklist, as a script

A minimal version of the security checklist that can run in CI:

```python
"""A deliberately small security checklist for a Dataflow template."""

import re
from pathlib import Path

FORBIDDEN_PATTERNS = {
    "hardcoded key": re.compile(r"AIza[0-9A-Za-z\-_]{35}"),
    "aws access key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "bearer literal": re.compile(r"(?i)bearer\s+[a-z0-9\-_\.]{20,}"),
    "private key block": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}


def scan(path: Path) -> list[str]:
    """Return a list of findings for one file.

    Args:
        path: The file to scan.

    Returns:
        A list of human-readable findings. Empty means clean.
    """
    text = path.read_text(encoding="utf-8")
    findings = []
    for name, pattern in FORBIDDEN_PATTERNS.items():
        if pattern.search(text):
            findings.append(f"{path}: possible {name}")
    return findings


def scan_tree(root: Path) -> list[str]:
    """Scan every Python file under a directory.

    Args:
        root: The directory to scan.

    Returns:
        A list of findings across all files.
    """
    findings: list[str] = []
    for path in sorted(root.rglob("*.py")):
        findings.extend(scan(path))
    return findings


if __name__ == "__main__":
    problems = scan_tree(Path("project"))
    for line in problems:
        print(line)
    print(f"{len(problems)} finding(s)")
```

---

## 🛠️ Common Errors and Fixes

### `Permission denied: resource 'projects/.../locations/us-central1'`

The caller cannot create the job in that region, or the Dataflow service
agent for that region does not exist yet.

```bash
gcloud beta services identity create --service=dataflow.engine \
  --project YOUR_PROJECT_ID
```

Wait a minute — the service agent is created asynchronously — and retry.

### `The caller does not have permission 'iam.serviceAccounts.actAs'`

The caller cannot impersonate the worker service account. Fix:

```bash
gcloud iam service-accounts add-iam-policy-binding \
  beam-worker@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --member=user:you@example.com \
  --role=roles/iam.serviceAccountUser
```

### `403 PERMISSION_DENIED on cloudkms.cryptoKeyVersions.useToEncrypt`

The Dataflow service agent cannot use the CMEK. Two common causes:

1. The IAM binding was added to the **wrong principal**. It must be the
   service agent, not the worker account:
   `service-PROJECT_NUMBER@gcp-sa-dataflow.iam.gserviceaccount.com`.
2. The binding was added to the **key**, but the job's `--kms-key` path
   points at a *different* key. Copy the key resource name from
   `gcloud kms keys list --location us-central1` rather than typing it.

### `Key location 'us-east1' does not match the job region 'us-central1'`

Cloud KMS keys are regional and never replicate. The key must live in the
same region as the Dataflow job **and** the same region as the data.
Move the key or run the job in the key's region.

### `VPC Service Controls violation` / `Egress denied for perimeter`

The staging or temp location is outside the perimeter. Dataflow moves
every job's data through temp and staging, so both must be inside. Fix
the location, or add an explicit egress rule for the specific path.

### `PERMISSION_DENIED: User does not have storage.objects.get access`

Two different identities could be missing access. Identify which by
reading the worker's own log line — it names the principal. If it is the
worker account, add `roles/storage.objectViewer` on the specific bucket.
If it is the service agent, add `roles/storage.objectAdmin` (or, better,
object-level roles) — and remember that adding a role to an existing
service agent does not always take effect until the service agent is
removed and re-added.

### `Failed to create a VPC peering` / `Invalid value for field 'subnetwork'`

The subnet is in a different region from the job, or Private Google
Access is off:

```bash
gcloud compute networks subnets update my-subnet \
  --region us-central1 --enable-private-ip-google-access
```

### `AttributeError: 'PipelineOptions' object has no attribute 'region'`

The Dataflow-specific flags live on the `DataflowOptions` subclass, not
on the base `PipelineOptions`. The course's `beam_options.build_options`
handles this by setting each attribute only when the options object
declares it. If you are rolling your own:

```python
from apache_beam.options.pipeline_options import DataflowOptions, PipelineOptions

options = PipelineOptions(["--runner", "DataflowRunner"])
dataflow_options = options.view_as(DataflowOptions)
dataflow_options.region = "us-central1"
dataflow_options.project = "YOUR_PROJECT_ID"
```

### The job runs, but I cannot see who ran it

Data Access logs are off by default for GCS and BigQuery. Turn them on
for the buckets that matter:

```bash
gcloud storage buckets update gs://YOUR_BUCKET --enable-data-access-logging
```

And make sure you are reading the right log: `Activity` logs show job
creation, `DataAccess` logs show what the job read and wrote.

---

## 💡 Production Notes

- **The service agent is a singleton per project and region.** Granting it
  project-wide access to every bucket is the default state of a new
  project and almost always too much. Scope it to the buckets it needs.
- **Grant the worker account and the service agent different roles.** They
  have different jobs: one stages files, the other reads and writes your
  data. A single over-permissioned account for both doubles your blast
  radius.
- **A private-IP job is the single highest-leverage compliance control.**
  It costs nothing, it makes "data cannot leave the VPC" a network fact
  rather than a policy promise, and it removes a whole class of audit
  questions. It does require Private Google Access and a subnetwork in
  the job's region.
- **CMEK is a three-layer question, not a one-flag question.** Job-level
  `--kms-key` covers staging, temp and shuffle. Bucket-level CMEK covers
  the data at rest. BigQuery dataset CMEK covers the warehouse. If the
  audit asks "is the data encrypted with a key we control", you need the
  layers that actually hold the data.
- **Rotating a CMEK key does not re-encrypt existing data.** Cloud KMS
  rotates the *key version*; new writes use the new version, old data
  stays under the old version until you re-encrypt it. Re-encryption is a
  separate, deliberate operation — and it is one of the reasons to own
  your keys.
- **The parameters of a job are part of the audit surface.** Treat
  `gcloud dataflow jobs describe` output as potentially sensitive: it
  contains everything you passed at launch.
- **Secret Manager is the answer for credentials, and the
  `secretmanager.secretAccessor` role should be granted on one secret,
  not on the project.** A worker that can read every secret in the
  project can read every credential in it.
- **Service account impersonation is the supported way into a customer
  VPC.** Do not ask a customer for a service account key file, and do not
  build a tunnel with a shared static credential. The impersonation chain
  is auditable, revocable and short-lived.
- **Budget the audit-logging cost.** Data Access logs on a busy bucket
  generate a lot of entries. Use a log bucket with a cost budget, and
  filter at the sink rather than at the source.

---

## 🔑 Key Takeaways

- A Dataflow job has **three identities** — the caller, the Dataflow
  service agent, and the worker service account — and they need three
  different, non-overlapping sets of roles.
- **Least privilege on the worker account** means object-level bucket
  roles, not project-level ones. `objectViewer` in, `objectCreator` out.
- **Private IP jobs** (`--network`, `--subnetwork`, `--no-public-ip`)
  remove the public internet from the worker's routing table entirely.
  They need Private Google Access and a same-region subnet.
- **CMEK needs four things**: an enabled key, a key in the same region as
  the data, `cloudkms.cryptoKeyEncrypterDecrypter` on the Dataflow
  service agent, and an `encryption` purpose. Miss one and you get a
  different error for each.
- **`--kms-key` keys the job's own storage, not the bucket.** Add
  bucket-level and BigQuery-level CMEK if the requirement is about the
  data.
- **Service account impersonation**, not a shared key, is how a job
  reaches a customer VPC — and it gives the customer an auditable,
  revocable identity.
- **VPC Service Controls is a perimeter, not a role.** It changes where
  you can put your temp and staging locations, which is why it is
  expensive to retrofit.
- **A pipeline parameter is not a secret store.** A secret in a parameter
  is in the job metadata, the audit log, the UI and someone's shell
  history. Pass a Secret Manager *path* and fetch the value at runtime.
- Audit logging answers "who ran what" only if Data Access logs are on
  and the retention policy is longer than the default 30 days.

---

## 📚 Practice Exercises

1. **Enumerate the identities.** On a project you have access to, list
   the Dataflow service agents, the worker service accounts, and the IAM
   bindings on each. Produce a table of identity → roles → resources.
   *Expected answer:* the service agent holds `roles/dataflow.serviceAgent`
   and often `roles/storage.objectAdmin` at project level — that project-level
   storage role is the thing to fix first.

2. **Scope a worker account.** Write the exact `gcloud` commands that
   give `beam-worker@YOUR_PROJECT_ID.iam.gserviceaccount.com` read access
   to `gs://YOUR_BUCKET` and write access to `gs://YOUR_BUCKET`, and
   nothing else. Then verify with `gcloud storage buckets get-iam-policy`.

3. **CMEK preconditions.** List the four preconditions for a job-level
   `--kms-key` to work, and the exact error each one produces when it is
   violated. Then extend the list to a full three-layer CMEK story (job,
   bucket, BigQuery).

4. **Secret hygiene.** Take any launch script you have written and audit
   it for credentials. Write a short script that greps a directory for
   the four patterns in the "Step 7" listing above and exits non-zero on
   a hit. Run it against `project/`. *Expected answer:* zero findings.

5. **Private IP design.** Write the `gcloud` commands to launch the
   course's batch template as a private-IP job, including the subnet
   update for Private Google Access and the `roles/compute.networkUser`
   binding for the Dataflow service agent.

6. **Audit reconstruction.** Using `gcloud dataflow jobs describe` and
   `gcloud logging read`, write the commands that answer: "which user
   launched job X, with what parameters, and which objects did it read?"
   Note which of the three needs Data Access logging to be enabled.

---

## 📖 Further Reading

- Dataflow service accounts and roles — https://cloud.google.com/dataflow/docs/concepts/security-and-access-control
- Dataflow access control using IAM — https://cloud.google.com/dataflow/docs/concepts/iam
- VPC-native pipelines — https://cloud.google.com/dataflow/docs/concepts/vpc-native
- Using customer-managed encryption keys with Dataflow — https://cloud.google.com/dataflow/docs/concepts/customer-managed-encryption-keys
- Service account impersonation — https://cloud.google.com/iam/docs/impersonating-service-accounts
- VPC Service Controls overview — https://cloud.google.com/vpc-service-controls/docs/overview
- Cloud Audit Logs — https://cloud.google.com/logging/docs/audit
- Secret Manager — https://cloud.google.com/secret-manager/docs
