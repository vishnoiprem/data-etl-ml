# 17 — S3 Lifecycle Rules and Access Logging

A runnable, **offline-first** mirror of the AWS Skill Builder lab
**"S3 Lifecycle Rules and Access Logging."** Six stages, eight shell
scripts that map exactly to the lab's "click in the console"
instructions, plus a pytest suite that simulates S3 in-process via moto.
No AWS credentials needed for verification.

```
                       ┌──────────────────────────────────┐
                       │     s3-lifecycle-data-bucket-…    │
                       │                                    │
   upload ──────────▶  │  raw/   (STANDARD, hot)           │
                       │  curated/  (warm)                  │
                       │  processed/  (hot)                 │
                       │                                    │
                       │  Lifecycle rule on prefix raw/:    │
                       │    day  30 -> STANDARD_IA          │
                       │    day  90 -> GLACIER_IR           │
                       │    day 365 -> DELETE               │
                       │                                    │
                       │  Server access logging ->          │
                       │     logs/ prefix in LOG bucket     │
                       └───────────────┬────────────────────┘
                                       │  every request, async
                                       ▼
                       ┌──────────────────────────────────┐
                       │  s3-lifecycle-logs-bucket-…        │
                       │                                    │
                       │  logs/<date>/<hour>-<rand>-<bucket>│
                       │  ─────────────────────────────     │
                       │  <bucket_owner> <bucket> [<time>]  │
                       │  <ip> <requester> <op> <key> ...   │
                       └────────────────────────────────────┘
```

## Files

| Path                                              | Purpose                                          |
|---------------------------------------------------|--------------------------------------------------|
| `sample_data/lifecycle-rule.json`                 | The JSON rule the lab attaches to the data bucket |
| `sample_data/example-access-log.txt`              | The 5-record log file the lab seeds into the log bucket |
| `sample_data/log-bucket-policy.json`              | Bucket policy granting `logging.s3.amazonaws.com` write |
| `scripts/00_set_buckets.sh`                       | Helper: set `DATA_BUCKET` and `LOG_BUCKET`       |
| `scripts/01_inspect_buckets.sh` through `06_teardown.sh` | Six stage scripts (one per lab stage)         |
| `scripts/run_all.sh`                              | Optional: run stages 0–5 in sequence              |
| `tests/conftest.py`                               | moto fixture: data + log bucket pair              |
| `tests/test_lifecycle.py`                         | 8 pytest tests, no AWS creds                      |
| `01_inspect_lifecycle.py`                         | Self-asserting driver (datavidhya style)         |
| `README.md`                                       | This file                                        |

## The 6 lab stages — mapped to artifacts

| Stage | Lab step                                                       | Artifact                                       |
|-------|----------------------------------------------------------------|------------------------------------------------|
| 1     | Inspect both buckets; confirm log bucket has its seed file     | `01_inspect_buckets.sh`, `test_stage1_*`       |
| 2     | Attach a lifecycle rule to the data bucket                    | `02_lifecycle_rule.sh`, `test_stage2_*`        |
| 3     | Walk the rule: 30d → IA, 90d → Glacier, 365d → delete          | `03_storage_transition.sh`, `test_stage3_*`    |
| 4     | Enable server access logging on the data bucket               | `04_access_logging.sh`, `test_stage4_*`        |
| 5     | Read the seeded access log, parse a record                     | `05_read_log.sh`, `test_stage5_*`              |
| 6     | Tear down: disable logging, empty + delete both buckets        | `06_teardown.sh`, `test_stage6_*`              |

## Run it offline (no AWS account)

```bash
cd medium/meta/datavidhya/17_S3_Lifecycle_Rules_And_Access_Logging/

# Self-asserting driver -- 18 checks, all PASS.
../../../.env/bin/python 01_inspect_lifecycle.py

# pytest -- 8 tests, all PASS.
../../../.env/bin/python -m pytest tests/ -v
```

Internally the driver and tests use `moto.mock_aws()` to simulate the
two buckets in-process; both run with zero network and zero credentials.

## Run it against a real AWS account

```bash
export DATA_BUCKET=s3-lifecycle-data-bucket-a1b2c3
export LOG_BUCKET=s3-lifecycle-logs-bucket-x7k2q9
./scripts/run_all.sh
```

`run_all.sh` runs the five mutating scripts in order. Stage 6 (teardown)
is run manually when the lab is done.

## What each lab stage actually does

### Stage 2 — Lifecycle rule

`lifecycle-rule.json` says, for any object under the `raw/` prefix:

| Day | Storage class | $/GB-month (us-east-1) | Rationale                       |
|-----|---------------|------------------------|---------------------------------|
| 0   | STANDARD      | $0.023                 | Hot landing zone                |
| 30  | STANDARD_IA   | $0.0125                | "infrequent access" -- still ms retrieval |
| 90  | GLACIER_IR    | $0.004                 | Archive-ish, ms retrieval       |
| 365 | DELETED       | --                     | Cost boundary                   |

The rule also covers noncurrent versions (when versioning is on): older
versions age out at 30d/365d the same way, and abandoned multipart
uploads expire after 7 days.

### Stage 3 — Storage transitions

S3 walks the bucket **once per day**. A 31-day-old object under `raw/`
will be STANDARD_IA on the next daily pass. The lab's "verify" check
therefore targets the *configuration*, not real-time transitions.

### Stage 4 — Access logging

```
   Data bucket  --put-bucket-logging-->  Log bucket
   (request source)                       (audit destination)
```

Two-sided setup:

1. **Data bucket** — `put-bucket-logging` with `TargetBucket` and
   `TargetPrefix`. S3 then begins writing log records for every request.
2. **Log bucket** — bucket policy granting `logging.s3.amazonaws.com`
   permission to `s3:PutObject` into `arn:aws:s3:::<log>/<prefix>/*`.

Without the log bucket policy the data bucket refuses to enable logging
(this is enforced by S3 itself, not just best practice).

### Stage 5 — Reading a log record

Each line is one request. The fields, in order:

```
   <bucket_owner>  <bucket>  [<time>]  <ip>  <requester>  <request_id>
   <operation>     <key>     <http_request_line>
   <http_status>   <error_code>  <bytes_sent>  <bytes_received>
   <total_time>    <turnaround_time>
   <referrer>      <user_agent>
   <version_id>    <sigv>  <cipher>  <auth_type>  <endpoint>  <tls>
```

The seeded log in `sample_data/example-access-log.txt` shows 5 records,
including a `403 AccessDenied` so you can see what a denied request
looks like.

### Stage 6 — Teardown

Disable logging FIRST (so the data bucket stops writing into the log
bucket). Then empty + delete both buckets. With versioning on, empty
must include both `Versions` AND `DeleteMarkers`. The shell script
does this automatically.

## Traps the lab expects you to hit

- **Lifecycle transitions are async.** S3 may take up to 24h after a
  transition day to actually move an object. The "verification" check
  is the *configuration*, not the objects.
- **Logging requires a log-bucket policy.** Forgetting to add the
  policy yields `InvalidTargetBucketForLogging` from
  `put-bucket-logging`. The script applies the policy before enabling
  logging.
- **Disabling logging ≠ deleting lifecycle.** Two separate things. The
  teardown explicitly disables both, in order.
- **The access log is space-delimited with quoted fields.** Naive
  `split()` breaks on the `"GET /path HTTP/1.1"` token. Use a real
  parser (the lab doesn't go there) or read the log with
  `aws s3 cp | head` and eyeball it.
- **Access logs are best-effort.** S3 may drop log records under high
  load; they're not a substitute for CloudTrail data events on the
  control plane.

## Going to production

Four things to add before this leaves a lab:

1. **Lifecycle rules on EVERY prefix.** The lab covers `raw/`. In
   production, `curated/`, `processed/`, and `archive/` each need their
   own rule.
2. **Lifecycle for incomplete multipart uploads.** Without
   `AbortIncompleteMultipartUpload`, abandoned uploads persist forever
   (and bill at STANDARD rates). The shipped rule has a 7-day expiry.
3. **Lifecycle for delete markers** with versioning on. Delete markers
   are 0-byte objects; they don't cost much, but they prevent the
   `IsLatest` pointer from going to a real version.
4. **Server access logging → CloudWatch Logs or a SIEM.** Raw log files
   are a poor audit trail. The lab seeds text logs; production would
   pipe them through a log router.

## Verification

The lab's "lab complete" check is: data bucket has a lifecycle rule
that ages `raw/` from STANDARD through STANDARD_IA through GLACIER_IR to
deletion at 365d, AND the log bucket has the example log file, AND
the log records include at least one 200 and one 403. The driver and
the pytest suite exercise all three without AWS. The shell scripts are
the manual-run equivalent for the live account.
