# 16 — Build a Mini Data Lake on Amazon S3

A runnable, **offline-first** mirror of the AWS Skill Builder lab
**"Build a Mini Data Lake on Amazon S3."** Six stages, eight shell
scripts that map exactly to the lab's "click in the console"
instructions, plus a pytest suite that simulates S3 in-process via
moto. No AWS credentials needed for verification.

```
   raw/                  curated/                 processed/
   ├── sales/            ├── customers/            (populated by ETL,
   │   └── january-…csv  │   └── customers.json      e.g. slot 14's
   └── customers/        └── sales/                   S3→Lambda processor)
       └── customers.json    └── january-…csv

       raw is immutable landing zone; curated is cleaned / deduped;
       processed is the output of an actual job (Glue / Lambda / EMR).
```

## Files

| Path                                | Purpose                                                |
|-------------------------------------|--------------------------------------------------------|
| `sample_data/january-sales.csv`     | The 10-row sales file the lab seeds into `raw/sales/`  |
| `sample_data/customers.json`        | The 5-record customers file the lab seeds into `raw/customers/` |
| `scripts/00_set_bucket.sh`          | Helper: set / print the `BUCKET` env-var               |
| `scripts/01_inspect_objects.sh`     | Stage 1: list + peek at each seeded file               |
| `scripts/02_create_zones.sh`        | Stage 2: `curated/` and `processed/` + raw → curated   |
| `scripts/03_storage_class.sh`       | Stage 3: STORAGE_CLASS STANDARD → STANDARD_IA          |
| `scripts/04_versioning.sh`          | Stage 4: enable bucket versioning                      |
| `scripts/05_overwrite_recover.sh`   | Stage 5: bad write + recover via prior VersionId       |
| `scripts/06_teardown.sh`            | Stage 6: delete every version + delete the bucket      |
| `scripts/run_all.sh`                | Optional: run stages 0–5 in sequence                   |
| `tests/conftest.py`                 | moto-mocked bucket fixture                             |
| `tests/test_data_lake.py`           | 8 pytest tests, no AWS creds                           |
| `01_inspect_data_lake.py`           | Self-asserting driver (datavidhya style)               |
| `README.md`                         | This file                                              |

## The 6 lab stages — mapped to artifacts

| Stage | Lab step                                                | Artifact                                          |
|-------|---------------------------------------------------------|---------------------------------------------------|
| 1     | Inspect raw/ contents (sales CSV + customers JSON)       | `01_inspect_objects.sh`, `test_stage1_*`          |
| 2     | Create curated/ and processed/ zone folders; copy raw → curated | `02_create_zones.sh`, `test_stage2_*`        |
| 3     | Change a file's storage class to STANDARD_IA            | `03_storage_class.sh`, `test_stage3_*`            |
| 4     | Enable bucket versioning                                | `04_versioning.sh`, `test_stage4_*`               |
| 5     | Overwrite a file with bad data, recover the original    | `05_overwrite_recover.sh`, `test_stage5_*`        |
| 6     | Tear down: delete every version, then the bucket        | `06_teardown.sh`, `test_stage6_*`                 |

## Run it offline (no AWS account, no moto setup beyond pip)

```bash
cd medium/meta/datavidhya/16_Build_Mini_Data_Lake_On_S3/

# Self-asserting driver -- 12 checks, all PASS.
../../../.env/bin/python 01_inspect_data_lake.py

# pytest -- 8 tests, all PASS.
../../../.env/bin/python -m pytest tests/ -v
```

Internally the driver and tests use `moto.mock_aws()` to spin up an
in-process S3 simulator; both run with zero network and zero credentials.

## Run it against a real AWS bucket

```bash
export BUCKET=s3-intro-data-lake-bucket-XXXX        # the lab's bucket name
./scripts/00_set_bucket.sh                         # confirm
./scripts/run_all.sh                               # stages 0-5
./scripts/06_teardown.sh                           # clean up
```

`run_all.sh` runs the five mutating scripts in order. Each one logs its
stage number and prints the AWS CLI's response on success.

## What each lab stage actually does (deep dive)

### Stage 1 — Inspect raw/

The lab starts with two files already in the bucket:

- `raw/sales/january-sales.csv` — 10 rows, the lab's sample data
- `raw/customers/customers.json` — 5 records, one per customer

You list the bucket, click into each file, and verify it looks right.

**Equivalent CLI** — `aws s3 ls s3://$BUCKET/raw/ --recursive`

### Stage 2 — Zones + raw → curated copy

A "data lake" is just an S3 bucket used with **prefix conventions**:

- **`raw/`** — immutable landing zone (write-only)
- **`curated/`** — cleaned, deduplicated, maybe schema-enforced
- **`processed/`** — output of actual ETL (Glue / Lambda / EMR)

You create the empty zones (a "folder" in S3 is just `PutObject` with a
key ending in `/`), then copy raw into curated.

```bash
aws s3api put-object --bucket $BUCKET --key curated/
aws s3api put-object --bucket $BUCKET --key processed/
aws s3 cp s3://$BUCKET/raw/sales/january-sales.csv \
         s3://$BUCKET/curated/sales/january-sales.csv
```

### Stage 3 — Storage class STANDARD_IA

`STANDARD_IA` (Infrequent Access) is roughly **half the price** of
STANDARD, with the trade-off of a retrieval fee. Perfect for files that
are written once and read rarely (backups, recent archives). The lab
moves the curated sales file to STANDARD_IA; the copy of the file
itself triggers the storage-class transition.

```
   Standard:    $0.023/GB-month
   Standard-IA: $0.0125/GB-month (cheaper storage, extra retrieval fee)
   Glacier IR:  $0.004/GB-month (cheapest, 180-day minimum on small files)
```

### Stage 4 — Bucket versioning

Once on, **every** PutObject keeps the previous version under a new
`VersionId`. Versioning can only be Suspended (not Disabled) once
turned on — that's a lab-stage trap if you tried to "undo" it.

### Stage 5 — Overwrite + recover

You overwrite `curated/customers/customers.json` with deliberately bad
data. With versioning on, the bad write gets a fresh `VersionId` and
the original is still listed under the old one. `get-object
--version-id <old-id>` returns the original bytes.

```
   $ aws s3api list-object-versions --bucket $BUCKET \
         --prefix curated/customers/customers.json
   {
     "Versions": [
       { "VersionId": "v2...", "IsLatest": true,  ... },  ← CORRUPT
       { "VersionId": "v1...", "IsLatest": false, ... }   ← ORIGINAL (recoverable)
     ]
   }
```

### Stage 6 — Teardown

A single `delete_objects` call lists **every** VersionId and **every**
DeleteMarker and removes them all. Without this, the bucket still
holds the old versions and `delete-bucket` returns `BucketNotEmpty`.

## Traps the lab expects you to hit

- **"Folder" deletion with versioning on leaves orphans.** Deleting a
  "folder" via the console is a no-op on hidden versions; the
  `delete_objects` call must include both `Versions` and
  `DeleteMarkers`. The teardown script does this; the lab's "Empty"
  console button does it under the hood.
- **Storage class is a Bucket-scoped + Object-level setting.** You can
  default a bucket to STANDARD_IA via the lifecycle policy, but
  individual objects still need their own PutObject or copy.
- **`get-bucket-versioning` returns empty Status, not "Off".** A
  bucket that has never had versioning enabled returns `Status` field
  absent. Treat absent and "Suspended" as the same state.
- **Object lock + versioning interact.** If you ever enable Object
  Lock, every version becomes immutable per the lock policy. The lab
  doesn't go there, but it's the next thing to read about.

## Going to production

Four things to add before this leaves a lab:

1. **Lifecycle rules** — auto-archive raw files to Glacier after 90
   days, expire the delete-markers after 30.
2. **Bucket policy** — block any `s3:DeleteObject` for raw/* (it's the
   immutable landing zone).
3. **KMS encryption** — `aws s3api put-bucket-encryption --bucket $BUCKET
   --server-side-encryption-configuration {...}` with a CMK, not the
   default AWS-managed key.
4. **Access logging** — write S3 server access logs to a separate
   `audit/` bucket and never read them again.

## Verification

The lab's "lab complete" check is: bucket contains 4 keys (2 raw, 2
curated), the curated sales file is `STANDARD_IA`, versioning is
`Enabled`, and a deliberately-bad overwrite can be undone via
`VersionId`. Both `01_inspect_data_lake.py` and `tests/test_data_lake.py`
exercise every one of those without AWS. The shell scripts are kept in
sync with the boto3 calls in the tests so the AWS-side run follows the
same code path.
