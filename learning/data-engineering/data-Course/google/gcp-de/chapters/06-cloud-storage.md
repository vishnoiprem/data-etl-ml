# 2.1 — Cloud Storage

> **Section 2 · Storage & Databases · Lecture 2.1 · 8:00**

## 🎯 What you will learn

- The bucket/object hierarchy, and why Cloud Storage is *not* a filesystem
- Storage classes: Standard, Nearline, Coldline, Archive — and the retrieval charge that trips people up
- Locations: regions, multi-regions, dual-regions, and the data-residency implication of each
- Lifecycle management rules — the mechanism that makes storage classes pay off
- Object versioning, object generation, and the `PreconditionFailed` error that protects against silent overwrites
- Uniform bucket-level access (UBLA) versus per-object ACLs, and why UBLA is the right default
- Signed URLs for temporary access without sharing credentials
- Bucket retention policies and object soft delete — how to make deletion hard
- Customer-managed encryption keys (CMEK), and when you need them
- The `gsutil` CLI and the Python client library, side by side
- Pricing mechanics, and how they map onto the course's `cost_model.py`

---

## 🧠 Concept

### The hierarchy

Cloud Storage has exactly two concepts:

- A **bucket** is a named container that lives in a project. It has a location, a storage class, a lifecycle policy, an IAM policy, and a retention policy. Its name is **globally unique across all of Google Cloud** — not just within your project. That global namespace is why `gs://my-bucket` is safe to hardcode in a config file, and also why you cannot delete a bucket name and reuse it immediately.
- An **object** is a file inside a bucket. Its identity is the pair `(bucket, object-name)`, plus a **generation** number if versioning is on.

The object name is a string, not a path. `gs://bucket/events/2026-01-15/orders.csv` is one object named `events/2026-01-15/orders.csv` — the slashes are conventional, not structural. There are no directories, no inodes, no hard links, no partial writes, no file locking, and no rename. An "update" is a full object replacement.

This matters more than it first appears. If you treat object storage as a filesystem you will write code that fails in production:

| Filesystem assumption | What Cloud Storage actually does |
|---|---|
| `os.rename()` is atomic and cheap | Copy the object, then delete the original. Two operations, two billing events, and a window where both exist. |
| Write to a file, then keep appending | Each write is a complete new object version. Appending is a read-modify-write of the whole object. |
| `mkdir` then write | The prefix is invented at write time. Nothing is created. A "directory" object with zero bytes can exist, but it means nothing. |
| A partial write is visible to readers | Not possible. Readers see either the previous version or the new one. |
| Delete is instant and cheap | Delete marks the object for deletion; a 30-day soft-delete window can restore it. |

### Storage classes

A storage class is a per-object (or per-bucket default) attribute that determines **how the bytes are stored, how quickly they can be read, and what they cost per month**. Four classes matter for data engineering:

| Class | Storage $/GB-month | Retrieval $/GB | Minimum storage duration | Read latency | Intended use |
|---|---|---|---|---|---|
| Standard | $0.020 | $0.00 | none | milliseconds | Active data, frequently read |
| Nearline | $0.010 | $0.01 | 30 days | milliseconds | Data read about once a month |
| Coldline | $0.004 | $0.02 | 90 days | milliseconds | Data read about once a quarter |
| Archive | $0.0012 | $0.05 | 365 days | **hours** | Data read about once a year |

These prices match `STORAGE_CLASS_PRICES` and `STORAGE_RETRIEVAL_PRICES` in `project/core/cost_model.py` exactly, so the arithmetic in this chapter is the arithmetic your code will compute.

The critical mechanic: **the cheap classes charge for retrieval, and the minimum storage duration is a penalty, not a discount.** If you put an object in Nearline and delete it after 5 days, you are billed 30 days of storage. If you put an object in Archive and read it after 20 minutes, you pay $0.05/GB plus 365 days of storage charges.

The break-even point is where the storage saving equals the retrieval cost. Moving 1 TB from Standard to Nearline saves $0.010/GB-month = $10/month per TB. Reading that TB back once costs $0.01/GB = $10.55. So for Archive, reading the data once per year is roughly break-even; reading it twice per year is a net loss. This is why the classes are named for access frequency, and why the lifecycle rules below are the mechanism that makes the whole thing work.

### Locations

A bucket's location is fixed at creation and cannot be changed. You must create a new bucket and copy the data. Locations come in three shapes:

- **Region** (`us-central1`, `europe-west4`, `asia-southeast1`) — data stored in a single region. Lowest latency, lowest price, no data movement cost within the region.
- **Multi-region** (`us`, `eu`, `asia`) — data stored in a pair of regions within a continent set, served from the nearest. Costs roughly twice a region. Correct for a bucket that serves users on multiple continents.
- **Dual-region** — a specific pair of regions, e.g. `nam4` (us-central1 + us-east1). Chosen for a specific residency or latency requirement, not geography in general.

For a data platform the default is a **region matching your compute and your warehouse**. A bucket in `us` feeding a BigQuery dataset in `us-central1` pays inter-region egress on every load. A bucket in `us-central1` feeding a `us-central1` BigQuery dataset does not — and BigQuery's free tier for GCS reads means the load itself can be free.

### Lifecycle management

A **lifecycle rule** is a configuration on the bucket that transitions objects between storage classes or deletes them, based on age, creation time, or a custom timestamp. This is the mechanism that turns storage classes from a naming convention into a policy.

```text
age < 30 days   → keep Standard
age >= 30 days  → transition to Nearline
age >= 90 days  → transition to Coldline
age >= 365 days → transition to Archive
age >= 2555 days (7 years) → delete
```

Two flags matter enormously:

- **`isLive`** — when false, the transition only happens if the object has **not** been accessed since the last transition. This is the flag that stops your archive from becoming a hot archive that re-archives monthly and pays the penalty forever.
- **`matchesPrefix`** — scope the rule to a prefix, so `/raw/` can age differently from `/curated/`.

Lifecycle actions are `SetStorageClass`, `Delete`, `DeleteWithVersioning`, and (with a lifecycle condition) `AbortIncompleteMultipartUpload`.

The cost trap: **transitioning to a class with a minimum storage duration resets the retention clock.** A file that has been in Nearline for 29 days, gets transitioned again, resets to 0. If a lifecycle rule keeps re-transitioning objects, you pay the minimum duration over and over. The fix is `isLive: false` plus a well-chosen first-transition threshold.

### Object versioning

Versioning keeps every generation of every object. Each write increments the generation number. You can list generations, read a specific one, and delete a specific one.

Versioning changes three things about error handling:

1. A `PUT` no longer destroys data — it creates generation 3 of an object that already had generations 1 and 2. This is why versioned buckets are the safe place to run a pipeline.
2. **`Delete` becomes a marker**, not a removal. The object appears deleted, but its generations remain until you delete them or the soft-delete window expires.
3. Delete markers themselves can be deleted to "undelete" the object.

Enabling versioning costs nothing on its own — you pay for the extra generations' storage. A daily job that writes a 10 GB file with versioning on keeps 30 days of history: 300 GB of Standard storage for a 10 GB dataset.

Versioning also introduces a real error you will hit:

```text
PreconditionFailed: 412 At least one of the pre-conditions you specified did not hold
```

This comes from `gsutil rsync` or `gcloud storage cp` when the source and destination have the same generation number — the client sends `ifGenerationMatch` to avoid duplicating work, and the server refuses because the object has changed. The fix is `--ignore-source-mtime` off / `-c` behavior, or deleting the destination generation first.

### Uniform bucket-level access versus ACLs

This is the single most consequential security decision on Cloud Storage, and it is the one people get wrong most often.

**ACL-based access** gives you per-object permissions. Every object has its own access list. It is powerful, it is expressive, and it is a disaster at scale because:

- Every object write must carry an ACL, and every ACL must be tracked.
- A `gsutil cp` that does not specify `--acl` silently applies a **default** ACL, which may not be what you wanted.
- You cannot answer "who can read this object?" by reading one policy. You have to list every object.
- The ACL model makes it easy to accidentally make an object public (`allUsers:objectViewer`) and impossible to prove you did not.

**Uniform bucket-level access (UBLA)** disables per-object ACLs entirely. Access is granted only by the bucket's IAM policy. `roles/storage.objectViewer` on the bucket grants read on every object in it, and there is no other way to grant read.

My position, which is also the platform's direction: **always use UBLA**. The only exception is a legacy bucket you cannot change, and even then you should migrate it.

With UBLA you still get fine-grained control through **IAM Conditions**. You can grant a role on objects with a prefix:

```text
roles/storage.objectViewer on buckets/raw-events/objects/curated/*
```

You can grant access only to objects whose metadata matches a tag:

```text
role: roles/storage.objectViewer
condition:
  resource.name.startsWith('projects/_/buckets/raw-events/objects/')
  AND resource.tags.name == 'environment' AND resource.tags.value == 'prod'
```

So UBLA does not reduce your control — it moves control from a scattered, per-object ACL model into one auditable, versioned IAM policy.

### Signed URLs

A **signed URL** grants temporary, unauthenticated access to a specific object for a bounded time, with a bounded permission. It is the correct way to hand a file to something that cannot hold a credential: a browser download link, a partner integration, a colleague without a project membership.

The URL embeds a signature computed from the private key, the expiry, the HTTP method, the resource path, and (optionally) custom headers. The server recomputes the signature on each request and compares. There is no server-side session and no revocation list — **the URL is valid until it expires, whoever holds it**.

Two flavours matter:

- **V2 signed URL** — signs the resource path and the expiry. Query-string parameters: `GoogleAccessId`, `Expires`, `Signature`.
- **V4 signed URL** — signs the HTTP method, the resource path, the expiry, and optionally headers, plus the `x-goog-content-sha256` payload hash. It is the modern form, supports `POST` for uploads, and its query parameter names are lowercase (`X-Goog-Signature`, `X-Goog-Expires`).

For V4, the canonical request includes the method and the hashed payload, which is why a V4 URL used with a different HTTP method fails with a signature mismatch. You can also generate **V4 signed POST policy** URLs, which let a browser upload directly to a bucket with a policy that constrains content type, size, and key prefix — no credentials reach the client at all.

The security model: the signer needs the private key (or the IAM signBlob permission). The recipient needs nothing. The expiry is the only revocation mechanism. Set it to the shortest workable window, and scope the URL to one object rather than a prefix.

### Retention policies and soft delete

Two independent mechanisms make deletion harder:

**Bucket lock / retention policy.** A retention policy has a *duration* (e.g. 7 years) or a *timestamp*. While active, **no one — not even a project owner — can delete or replace an object** in the bucket. Attempting to do so returns an error. The policy can be *unlocked*, which is what lets an authorised administrator shorten or remove it, and the unlock is recorded in the bucket's activity logs and subject to IAM permission `storage.buckets.update` with the `storage.forcedObjectOwnership` style controls. The retention period itself cannot be reduced below the currently-elapsed retention of any object.

**Soft delete.** With soft delete enabled, a deleted or overwritten object is retained for a configurable window (7 to 90 days) and can be restored. Unlike a retention policy, soft delete does not prevent deletion — it makes it recoverable. Versioning is not required.

The distinction matters for compliance: a retention policy is a *control* ("this data must not be deleted"), soft delete is a *recovery aid* ("we can undo a mistake").

### Encryption

All Cloud Storage data is encrypted at rest by default with Google-managed keys. There are three levels:

1. **Google-managed keys** (default) — no configuration, keys rotate automatically, no extra cost, no key-level audit.
2. **Customer-managed encryption keys (CMEK)** — you create the key in Cloud KMS and supply it at bucket creation or per-object. You control the key lifecycle: rotation, revocation, and, critically, **the ability to make the data unreadable by revoking the key**. This is the only way to satisfy a requirement that says "we must be able to cryptographically destroy this data."
3. **Customer-supplied encryption keys (CSEK)** — you upload the key material yourself. You are responsible for its protection. Google does not store it.

CMEK costs extra: the KMS key version and the encrypt/decrypt calls are billed, and KMS has its own latency on the request path. Use it where a regulatory or contractual requirement demands it, not by default — the operational burden of key rotation across many buckets is real.

### `gsutil` versus the client library

`gsutil` is the command-line tool. It is `cp`-shaped, which makes it wonderful for scripts and terrible for application logic. `gcloud storage` is the newer command set; `gsutil` remains available and stable.

```text
gsutil ls gs://bucket
gsutil cp ./events.csv gs://bucket/events/2026-01-15/
gsutil rsync ./local-dir gs://bucket/prefix/     # incremental, mirrors
gsutil -m cp -r ./big-dir gs://bucket/           # parallel transfers
gsutil cat gs://bucket/key.json                  # print to stdout
gsutil stat gs://bucket/key.json
gsutil mb -l us-central1 gs://bucket
gsutil lifecycle set - gs://bucket < lifecycle.json
```

The Python client library is what you use inside a Dataflow job or a service. It exposes the same resources with an object model:

- `storage.Client()` — authenticated client, project inferred from credentials
- `client.bucket(name)` — a bucket handle
- `bucket.blob(name)` — an object handle
- `blob.upload_from_string(data, content_type=...)`
- `blob.generate_signed_url(expiration=timedelta(hours=1), method="GET")`

The client library gives you `precondition_failed` handling, resumable uploads, retries with exponential backoff built in, and `Bucket.list_blobs()` for pagination — none of which `gsutil` exposes to a program.

### Pricing, precisely

Cloud Storage bills four things:

1. **Storage** — per GB-month, by class and location. Billed on the average daily stored size, so a bucket that grows is billed on the growth.
2. **Retrieval** — per GB read, by class. Zero for Standard.
3. **Operations** — per 1,000 operations. Class A (mutations: insert, delete, list, copy) and Class B (reads). Listing is Class A and is not free — a pipeline that lists a bucket with a million objects pays meaningfully.
4. **Network egress** — per GB out to the internet, $0.12/GB from us-central1. **Egress within Google Cloud is often free or cheaper**: GCS → BigQuery is free, GCS → Compute Engine in the same region is free.

The course's `estimate("cloud-storage", storage_gb=..., storage_class=..., retrieval_gb=..., egress_gb=...)` computes lines 1, 2 and 4. Free tier: 5 GB-month of Standard storage, 1 GB egress.

---

## 🛠️ Hands-On

### 1. Create a bucket with the right defaults from the start

```text
gcloud storage buckets create gs://YOUR_PROJECT_ID-raw-events \
    --project=YOUR_PROJECT_ID \
    --location=us-central1 \
    --default-storage-class=NEARLINE \
    --uniform-bucket-level-access \
    --public-access-prevention
```

What each flag buys you:

- `--location` — immutable after creation. Pick the region where your compute and warehouse live.
- `--default-storage-class=NEARLINE` — objects inherit this unless overridden. With lifecycle rules you usually want the *hot* class as the default and let lifecycle age data down.
- `--uniform-bucket-level-access` — disables ACLs. Do it on day one; it cannot be undone without recreating the bucket.
- `--public-access-prevention` — the organisational-policy-style guard that blocks `allUsers` and `allAuthenticatedUsers` bindings. It is on by default for new buckets; stating it explicitly documents the intent.

### 2. Inspect and configure the bucket

```text
gcloud storage buckets describe gs://YOUR_PROJECT_ID-raw-events
gcloud storage buckets update gs://YOUR_PROJECT_ID-raw-events --enable-object-soft-delete --soft-delete-duration=14d
gcloud storage buckets update gs://YOUR_PROJECT_ID-raw-events --versioning
```

Verify the IAM policy is what you expect, and that there are no ACLs hanging around:

```text
gcloud storage buckets get-iam-policy gs://YOUR_PROJECT_ID-raw-events
gcloud storage buckets ls gs://YOUR_PROJECT_ID-raw-events
```

The `ls` output must show `uniformBucketLevelAccess: true` under `acl:`. If it does not, you have a legacy bucket.

### 3. Upload the course sample data, with content type and metadata

```text
gsutil -m cp sample_data/events.csv        gs://YOUR_PROJECT_ID-raw-events/raw/events/2026-01-15/events.csv
gsutil -m cp sample_data/events.ndjson     gs://YOUR_PROJECT_ID-raw-events/raw/events/2026-01-15/events.ndjson
gsutil -m cp sample_data/malformed_events.csv gs://YOUR_PROJECT_ID-raw-events/raw/events/2026-01-15/malformed_events.csv
gsutil -m cp sample_data/region_reference.ndjson gs://YOUR_PROJECT_ID-raw-events/ref/region_reference.ndjson
```

Set content type and metadata at write time. An object stored as `application/octet-stream` will be downloaded as a binary blob by every browser, and metadata drives BigQuery external table autodetection.

```text
gsutil -m cp \
  -h "Content-Type:text/csv" \
  -h "Cache-Control:no-store" \
  sample_data/events.csv \
  gs://YOUR_PROJECT_ID-raw-events/raw/events/2026-01-15/events.csv
```

### 4. Use the Python client library, with the pieces that matter

```python
from google.cloud import storage
from google.auth.exceptions import DefaultCredentialsError

BUCKET_NAME = "YOUR_PROJECT_ID-raw-events"
OBJECT_NAME = "raw/events/2026-01-15/events.csv"


def get_client() -> storage.Client:
    """Build an authenticated Storage client.

    Returns:
        The authenticated client.
    """
    return storage.Client()


def upload_events(client: storage.Client, path: str) -> str:
    """Upload the sample events file with explicit content type.

    Args:
        client: An authenticated client.
        path: The local path of the CSV file.

    Returns:
        The object's gs:// URI.
    """
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(OBJECT_NAME)
    blob.content_type = "text/csv"
    blob.metadata = {"tier": "raw", "schema_version": "1"}
    blob.upload_from_filename(path)
    return f"gs://{BUCKET_NAME}/{OBJECT_NAME}"


def list_and_size(client: storage.Client) -> list[tuple[str, int]]:
    """List every object in the bucket with its size in bytes.

    Args:
        client: An authenticated client.

    Returns:
        A list of (name, size) tuples, sorted by name.
    """
    bucket = client.bucket(BUCKET_NAME)
    entries = []
    for blob in client.list_blobs(BUCKET_NAME):
        entries.append((blob.name, blob.size or 0))
    return sorted(entries)


def signed_download_url(client: storage.Client, name: str, minutes: int = 60) -> str:
    """Create a V4 signed URL for one object.

    Args:
        client: An authenticated client.
        name: The object name.
        minutes: How long the URL stays valid.

    Returns:
        The signed URL.
    """
    from datetime import timedelta

    blob = client.bucket(BUCKET_NAME).blob(name)
    return blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=minutes),
        method="GET",
    )


def read_prefix(client: storage.Client, prefix: str) -> int:
    """Count the bytes stored under a prefix.

    Args:
        client: An authenticated client.
        prefix: The object name prefix.

    Returns:
        The total number of bytes.
    """
    total = 0
    for blob in client.list_blobs(BUCKET_NAME, prefix=prefix):
        total += blob.size or 0
    return total


if __name__ == "__main__":
    try:
        client = get_client()
    except DefaultCredentialsError as exc:
        raise SystemExit(
            "No Application Default Credentials found. "
            "Run: gcloud auth application-default login"
        ) from exc

    uri = upload_events(client, "sample_data/events.csv")
    print("uploaded:", uri)
    for name, size in list_and_size(client):
        print(f"  {name}  {size} bytes")
    print("raw bytes:", read_prefix(client, "raw/"))
    print("signed url:", signed_download_url(client, OBJECT_NAME))
```

Two details in that code are load-bearing. `blob.metadata` sets **custom metadata**, which is stored in the object's metadata and is what BigQuery's external tables and Dataplex use for lineage — it is not the same as custom HTTP headers. And `generate_signed_url` with `version="v4"` needs no service-account key file on disk when you run it through the client library: it calls `signBlob` on the IAM API as the calling identity, so you need only the `iam.serviceAccounts.signBlob` permission.

### 5. Apply a lifecycle rule and verify it

```text
gsutil lifecycle set - gs://YOUR_PROJECT_ID-raw-events <<'JSON'
{
  "rule": [
    {
      "action": {"type": "SetStorageClass", "storageClass": "NEARLINE"},
      "condition": {"age": 30, "isLive": false, "matchesPrefix": ["raw/"]}
    },
    {
      "action": {"type": "SetStorageClass", "storageClass": "COLDLINE"},
      "condition": {"age": 90, "isLive": false, "matchesPrefix": ["raw/"]}
    },
    {
      "action": {"type": "Delete"},
      "condition": {"age": 2555, "matchesPrefix": ["raw/"]}
    }
  ]
}
JSON

gsutil lifecycle get gs://YOUR_PROJECT_ID-raw-events
```

The `isLive: false` on the first two rules is the important bit. Without it, an object that is read every week gets re-transitioned every 30 days, resets its Nearline clock, and you pay the 30-day minimum over and over.

### 6. Prove the versioning behaviour

```text
gsutil cp sample_data/events.csv gs://YOUR_PROJECT_ID-raw-events/versions/demo.csv
gsutil cp sample_data/malformed_events.csv gs://YOUR_PROJECT_ID-raw-events/versions/demo.csv
gsutil ls -a gs://YOUR_PROJECT_ID-raw-events/versions/demo.csv
```

The output shows two generations. Now test the precondition error:

```text
gsutil rsync sample_data/versions gs://YOUR_PROJECT_ID-raw-events/versions/
```

If a generation changed between the listing and the copy, the client sends `ifGenerationMatch` and gets:

```text
PreconditionFailed: 412 At least one of the pre-conditions you specified did not hold
```

The fix, when the error is benign, is to let the client re-list and retry, or to delete the destination generation before copying.

### 7. Cost the storage decision with the course's own model

```python
import sys

sys.path.insert(0, "project/core")

from cost_model import (
    STORAGE_CLASS_PRICES,
    STORAGE_RETRIEVAL_PRICES,
    estimate,
)


def storage_comparison(tb: float) -> list[tuple[str, float, float]]:
    """Compare the monthly and retrieval cost of each storage class.

    Args:
        tb: The size of the dataset, in terabytes.

    Returns:
        A list of (class, monthly_cost, one_read_cost) tuples.
    """
    gb = tb * 1024
    rows = []
    for name in ("standard", "nearline", "coldline", "archive"):
        monthly = estimate(
            "cloud-storage",
            storage_gb=gb,
            storage_class=name,
            retrieval_gb=0,
            monthly=True,
            apply_free_tier=False,
        ).total
        one_read = gb * STORAGE_RETRIEVAL_PRICES[name]
        rows.append((name, monthly, one_read))
    return rows


if __name__ == "__main__":
    for name, monthly, read in storage_comparison(1.0):
        print(
            f"{name:<10} monthly=${monthly:>10.2f}  "
            f"one full read=${read:>8.2f}  "
            f"store price=${STORAGE_CLASS_PRICES[name]}/GB-mo"
        )
```

The output for 1 TB:

```text
standard   monthly=    20.48  one full read=    0.00  store price=0.02/GB-mo
nearline   monthly=    10.24  one full read=   10.24  store price=0.01/GB-mo
coldline   monthly=     4.10  one full read=   20.48  store price=0.004/GB-mo
archive    monthly=     1.23  one full read=   52.43  store price=0.0012/GB-mo
```

Read the table carefully. Nearline for 1 TB costs half of Standard and one full read costs exactly the amount of one month of the storage saving — so Nearline breaks even on a single monthly read, which matches its "read once a month" positioning precisely. Archive costs 6% of Standard but a single read costs 43 months of storage savings: **Archive is only correct for data you read at most about once a year.** If your pipeline re-reads an archive bucket nightly, Nearline or even Standard is cheaper. This is the calculation that should drive the storage class decision, not intuition.

---

## 🛠️ Common Errors and Fixes

### 1. `403` on every write, even though you are the project owner

```text
CommandException: Could not upload file: gs://bucket/file.csv
HTTPError: 403: Access denied: project-owner@your-project.iam.gserviceaccount.com does not have storage.objects.create access to the Google Cloud Storage bucket.
```

The cause is almost always a **project-level IAM change plus a bucket-level policy**, or an org policy. Two more specific causes:

- `constraints/storage.publicAccessPrevention` is set to `enforce` and your policy binds `allUsers`.
- The bucket has **Uniform Bucket-Level Access** enabled and you are trying to use `gsutil acl set` — but that produces a different error (see #2).

Check what the *bucket* policy actually says, not just the project:

```text
gcloud storage buckets get-iam-policy gs://YOUR_BUCKET
gcloud storage buckets describe gs://YOUR_BUCKET --format="value(iamConfiguration)"
```

The fix is to grant the role at the bucket, not the project:

```text
gcloud storage buckets add-iam-policy-binding gs://YOUR_BUCKET \
    --member="serviceAccount:pipeline-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.objectCreator"
```

`roles/storage.objectCreator` is the right role for a pipeline that writes but must not read — and note it does **not** include `storage.objects.delete`, which means an aborted multipart upload leaves the part objects behind. Add `roles/storage.objectAdmin` if you need cleanup.

### 2. `gsutil acl set` fails on a UBLA bucket

```text
CommandException: Could not set the ACL for gs://bucket/file.csv: Access controls are not supported on this bucket.
```

You cannot have both UBLA and ACLs. If you enabled UBLA on a bucket that had per-object ACLs, the ACLs are gone — permanently — and any policy you had on individual objects was lost. Recover by rebuilding access from the IAM policy.

To find legacy buckets in a project:

```text
gcloud storage buckets list --format="table(name,iamConfiguration.uniformBucketLevelAccess)" | grep -v "true"
```

The fix for a legacy bucket is a migration: create the target bucket with UBLA, `rsync` the data, re-point your jobs, delete the old bucket. Do not try to flip the flag in place on a bucket with meaningful ACLs.

### 3. `PreconditionFailed: 412` when copying or syncing

```text
PreconditionFailed: 412 At least one of the pre-conditions you specified did not hold
```

The client sent a generation precondition (`ifGenerationMatch`) and the object's current generation does not match what the client expected. This happens when:

- The object was rewritten between the client's list and its write.
- You passed `-h x-goog-if-generation-match:0` to require "create only, do not overwrite" and the object exists.
- `gsutil rsync` found a candidate it wanted to skip but the object changed under it.

The fix depends on intent. To overwrite deliberately:

```text
gsutil -m cp ./file.csv gs://bucket/file.csv     # no precondition header
```

To require "must not already exist" (a safe write-once pattern):

```text
gcloud storage cp --predefined-acl=private --no-clobber ./file.csv gs://bucket/file.csv
```

`--no-clobber` is the idempotent-write flag. If you see 412 in a `rsync` loop and the loop should converge, the usual cause is two writers racing on the same prefix — serialise the writers or give each its own prefix.

### 4. `BucketNotFoundException: 404` immediately after creating a bucket

```text
google.api_core.exceptions.NotFound: 404 GET https://storage.googleapis.com/storage/v1/b/YOUR_BUCKET?projection=noAcl: notFound
```

Two causes:

- **Propagation delay.** The bucket's metadata is available on the global endpoint before it is available on the regional endpoint your client is configured with. Retry with backoff. The client library's built-in retries handle this; a raw `requests.get` does not.
- **Wrong endpoint or wrong credentials.** A service account from project A trying to read a bucket in project B gets a 404 (not a 403) if it has no `storage.buckets.get` permission — GCP deliberately returns 404 for buckets you cannot see, to avoid leaking their existence.

Check which project your client is actually talking to:

```python
from google.cloud import storage

client = storage.Client()
print("project:", client.project)
for bucket in client.list_buckets():
    print(bucket.name, bucket.location)
```

### 5. Lifecycle rules silently not applying

```text
gsutil lifecycle get gs://YOUR_BUCKET
```

shows the rules, but objects are not transitioning. Three likely causes:

- **Age is measured from object creation, not from the last transition.** An object created two years ago and read yesterday still has `age > 90`, so it transitions on the next evaluation. That is usually what you want, but if you expected a clock reset, this is why it did not happen.
- **`isLive: true` on the rule.** With `isLive` true, the rule only applies to objects that *have not* been accessed. For `SetStorageClass` the semantics are the reverse of what people expect: `isLive: false` means "transition only if the object has not been read since the last transition".
- **The lifecycle evaluation is asynchronous and can take up to 24 hours.** It is a background scanner, not a real-time trigger. Do not write a test that uploads an object and expects a transition in a minute.

### 6. Signed URL returns `403` in the browser but works from the CLI

```text
<Error>
<Code>AccessDenied</Code>
<Message>Request has insufficient authentication scopes for this resource.</Message>
</Error>
```

This is the classic V2-vs-V4 and GET-vs-POST mismatch. A V4 URL signs the HTTP method. If the browser issued a `HEAD` (or a `POST` for an upload) against a URL signed for `GET`, the signature does not match and the server rejects it.

For uploads, sign a POST policy instead:

```python
from google.cloud import storage

client = storage.Client()
bucket = client.bucket("YOUR_BUCKET")

policy = bucket.generate_upload_policy(
    object_name="raw/upload.csv",
    expires=3600,
    content_type="text/csv",
    max_size_mb=100,
)

print("POST to:", bucket.client._connection.API_BASE_URL)
print("fields:", policy)
```

Another cause is clock skew on the client. A signed URL is validated against the server's clock, and the signature embeds the issue time. If the caller's clock is more than a few minutes off, the request fails with a signature mismatch.

---

## 💡 Production Notes

- **Enable UBLA on every bucket, from the create command.** It is irreversible in the sense that object ACLs are lost when you turn it on, and `gsutil acl set` then fails. Put `--uniform-bucket-level-access` in your Terraform module and in the course's setup scripts so nobody has to remember.
- **Turn on soft delete (14–30 days) and versioning on every bucket holding anything you would hate to lose.** The cost is a small multiple of storage; the benefit is that a botched `gsutil rm -r` or a bad pipeline `DELETE` is a five-minute recovery instead of an incident.
- **Treat a lifecycle rule as a cost control that must be tested.** Write a test that asserts: object older than 30 days → Nearline; object older than 90 days → Coldline; and, crucially, that a *recently-read* object is **not** re-transitioned. The `isLive` behaviour is where lifecycle rules go wrong.
- **Never use a multi-region bucket for a data platform landing zone.** `gs://bucket` in `us` costs roughly double a region bucket and adds a copy to the other region. Use a region that matches your BigQuery dataset and your compute.
- **Watch egress, not storage.** Storage is $0.02/GB-month; egress is $0.12/GB, one-shot. A 10 TB backup copied out of GCP costs $1,200 in egress and $20 in storage. The bill line that hurts is almost never the storage line.
- **Do not let a pipeline list objects in a loop.** `list_blobs` is a Class A operation, billed per 1,000. A job that lists a million objects every hour generates millions of Class A operations — a real bill for zero business value. Use `gsutil rsync` (which is incremental and smart) or a manifest file.
- **Keep signed URL lifetimes short and scope them to one object.** A V4 URL signed for `GET` on a specific object path with a 15-minute expiry is a download link. A signed URL for `*` on a prefix with a 7-day expiry is a data leak waiting for a screenshot.
- **Give the pipeline service account `roles/storage.objectCreator`, not `roles/storage.admin`.** The narrower role cannot delete or overwrite objects, which means a compromised pipeline cannot destroy history. If you need cleanup of failed multipart uploads, grant `storage.objects.delete` specifically with a condition on the object prefix.

---

## 🔑 Key Takeaways

- A bucket is a container with an immutable location; an object is an immutable blob identified by `(bucket, name, generation)`. There is no filesystem semantics — no rename, no append, no partial write.
- Storage class is a **lifetime policy**, not a storage decision: Standard for hot, Nearline for monthly, Coldline for quarterly, Archive for annual. The retrieval charge makes the cheap classes expensive if you read often, and the minimum duration makes early deletion expensive.
- Lifecycle rules with `isLive: false` are the mechanism that makes classes pay off. Without them you are paying Standard prices for cold data.
- UBLA is the correct default. Express fine-grained access with IAM Conditions on prefixes and tags, not with per-object ACLs.
- Versioning is the safety net: it makes `PUT` non-destructive, makes `DELETE` a marker, and produces `412 PreconditionFailed` when a writer races.
- Retention policies *prevent* deletion; soft delete *recovers* from it. They solve different problems and you want both.
- Signed URLs give temporary access with no credentials on the client; the expiry is the only revocation. Prefer V4, scope to one object, keep it short.
- The storage/egress asymmetry is the one that shows up on real bills: storage is cheap, egress and Class A operations are not.
- In the course's model: `estimate("cloud-storage", storage_gb=..., storage_class=..., retrieval_gb=..., egress_gb=...)` computes the same four charges, so you can price a storage tier decision before you write the Terraform.

---

## 📚 Practice Exercises

1. **Enumerate the storage services in the course catalogue.** Use `project/core/service_catalog.py` to print the Storage category, and then answer: which storage services are available in `southamerica-east1`? Use `services_by_category("Storage")` and `region_status_matrix(["cloud-storage", "storage-transfer"])`. Note that `cloud-storage` is available in all 12 regions while `storage-transfer` is available in all 12 — check `REGIONS` and explain why the catalogue lists `datastore`, `bigtable` and `memorystore` as `restricted` or `preview` in `southamerica-east1` while `cloud-storage` is not.
2. **Price a storage-tier strategy.** Extend the `storage_comparison` function from the Hands-On to accept a *read frequency* (reads per month) and a *retention* (months), and report the total monthly cost of each class including the minimum-duration penalty. Then answer: for a 5 TB dataset read twice a month and retained for 60 days, which class wins? Show the arithmetic using `STORAGE_CLASS_PRICES` and `STORAGE_RETRIEVAL_PRICES`.
3. **Model the egress surprise.** Using `estimate("cloud-storage", storage_gb=10240, storage_class="standard", egress_gb=10240)`, compute the cost of storing and then exporting 10 TB. Then repeat with `storage_class="nearline"`. Explain why the *second* option can be more expensive than the first, and state the condition under which it is not.
4. **Write a lifecycle-rule validator.** Write a Python function that takes a list of lifecycle rules (as dicts, the shape `gsutil lifecycle set` accepts) and raises `ValueError` when a rule would re-transition an object that is already in the target class (which resets the minimum-duration clock). Then apply it to a rule set that transitions to Nearline at 30 days and Coldline at 90 days, and confirm it passes.
5. **Implement the signed-URL flow locally.** Write a function `signed_url_for(client, object_name, minutes)` in a new module under `project/core/` that wraps `blob.generate_signed_url(version="v4", ...)`. Add a pure-function fallback `v4_expiry_is_valid(now, expires_at, clock_skew_seconds=300)` that returns `False` when the expiry has passed or the clock skew is too large, and unit-test it in `project/tests/test_iam_and_cost.py`. The point is the *expiry semantics*, not the API call.
6. **Wire the landing zone into the simulator.** In `project/core/platform_sim.py`, the demo project already creates a bucket named `raw-events`. Extend `build_demo_project()` to also create a second bucket `raw-events-archive` in the same project, grant the pipeline service account `roles/storage.objectCreator` on it instead of `roles/storage.objectViewer`, and use `project.can(...)` to assert that the service account can write to `raw-events-archive` but cannot read from `raw-events`. Then use `iam_policy.explain_principal()` to show why the read is denied.
7. **Design a bucket layout for the course pipeline.** The pipeline writes raw events, a curated summary, and a dead-letter file. Propose a bucket (or bucket-prefix) layout, the storage class for each prefix, and the lifecycle rule for each — using the naming convention already in `platform_sim.build_demo_project()` (`raw-events` with `labels={"tier": "raw"}`). Then write the `gsutil` commands to create and configure it, including the lifecycle JSON inline.

---

## 📖 Further Reading

- [Cloud Storage overview](https://cloud.google.com/storage/docs) — the official landing page for the service
- [Storage classes](https://cloud.google.com/storage/docs/storage-classes) — durations, retrieval fees, and the lifecycle interaction
- [Object lifecycle management](https://cloud.google.com/storage/docs/lifecycle) — how rules are evaluated, and `isLive`
- [Object versioning](https://cloud.google.com/storage/docs/object-versioning) — generations, delete markers, and cost
- [Uniform bucket-level access](https://cloud.google.com/storage/docs/uniform-bucket-level-access) — the UBLA model and the migration path
- [Signed URLs](https://cloud.google.com/storage/docs/access-control/signed-urls) — V2 vs V4, and signed POST policies
- [Encryption options](https://cloud.google.com/storage/docs/encryption) — Google-managed keys, CMEK, and CSEK
- [gsutil reference](https://cloud.google.com/storage/docs/gsutil) — the full command set
