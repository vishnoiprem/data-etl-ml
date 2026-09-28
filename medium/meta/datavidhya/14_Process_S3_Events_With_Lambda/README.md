# 14 — Process S3 Events with Lambda

A runnable, **offline-first** implementation of the AWS Skill Builder hands-on
lab **"Process S3 Events with Lambda"**. Drop a CSV in `raw/`, the Lambda
validates each row, enriches the good ones, and writes the split outputs to
`processed/` and `rejected/`. Event-driven ingestion with no scheduler and no
polling.

```
            ┌──────────────────┐   S3 ObjectCreated   ┌──────────────────────┐
   CSV  ───▶│  s3://bkt/raw/   │ ──────────────────▶ │  OrdersProcessor     │
            └──────────────────┘   raw/*.csv only    │  lambda_function/app │
                                                       │   .py:lambda_handler │
                                                       └──────────┬───────────┘
                                                                  │ validate + enrich
                                                                  ▼
                                          ┌───────────────────────┴───────────────────────┐
                                          ▼                                               ▼
                                ┌──────────────────────┐                       ┌──────────────────────┐
                                │  s3://bkt/processed/ │                       │  s3://bkt/rejected/  │
                                │  enriched CSVs       │                       │  CSVs + _rejected_   │
                                │                      │                       │  reason column       │
                                └──────────────────────┘                       └──────────────────────┘
```

## Files

| Path                                  | Purpose                                          |
|---------------------------------------|--------------------------------------------------|
| `lambda_function/app.py`              | The Lambda handler (target of `sam deploy`)      |
| `template.yaml`                       | SAM template — bucket, function, S3 event wire   |
| `events/s3-put-event.json`            | Fixture event for `sam local invoke`             |
| `data/orders_raw.csv`                 | Sample input — 12 rows, 5 deliberately bad        |
| `data/orders_processed_expected.csv`  | Expected `processed/…csv` (compared offline)     |
| `data/orders_rejected_expected.csv`   | Expected `rejected/…csv` (compared offline)      |
| `tests/test_handler.py`               | 6 pytest tests, no AWS creds required            |
| `01_process_csv_upload.py`            | Self-asserting driver (datavidhya style)         |
| `README.md`                           | This file                                        |

## The 8 lab stages — mapped to artifacts

The AWS Skill Builder lab walks you through 8 steps; `01_process_csv_upload.py`
exercises an independent set of 8 offline assertions against the same
artifacts. The tables below are kept separate on purpose — the lab step
number is what you do in the console, the assertion number is what the
driver verifies.

| Stage | Lab step (AWS console)                            | Artifact / behavior                                       |
|-------|---------------------------------------------------|-----------------------------------------------------------|
| L1    | Inspect provisioned bucket + Lambda                | `template.yaml` → `Outputs.OrdersBucket` / `…Function`   |
| L2    | Upload `orders_…csv` to `raw/`                    | `data/orders_raw.csv` (12 rows)                            |
| L3    | Function auto-fires, read the object              | `lambda_function/app.py` → `lambda_handler` + `_read_object` |
| L4    | Validate records (drop the bad ones)              | `_validate()` returns a reason code per row                |
| L5    | Enrich good rows (`amount_usd` etc.)              | `_enrich()` adds 3 derived columns                         |
| L6    | Write results to `processed/`                     | `_write_objects()` + `put_object`                          |
| L7    | Inspect CloudWatch Logs                           | `LOG.info()` calls → `sam logs -n OrdersProcessorFunction --tail` |
| L8    | Find rejection reason, fix, reprocess             | Re-run `python 01_process_csv_upload.py` after editing the CSV |

| Stage | Driver assertion                                  | What it checks                                            |
|-------|---------------------------------------------------|-----------------------------------------------------------|
| A1    | handler returns `{accepted: 7, rejected: 5}`      | The 12-row fixture splits 7/5.                            |
| A2    | stub bucket has BOTH `processed/` and `rejected/` | The split write path is exercised, not just `processed/`. |
| A3    | processed CSV matches expected                    | Row-by-row equality on the 7 accepted rows.               |
| A4    | rejected CSV matches expected                     | Row-by-row equality on the 5 rejected rows.                |
| A5    | rejection reasons covered                         | All five named reasons appear at least once.              |
| A6    | every accepted row has the 3 derived columns      | `amount_usd`, `processed_at`, `row_hash` populated.       |
| A7    | re-running returns identical counts               | Idempotency at the count level (the wall-clock field drifts byte-for-byte). |
| A8    | non-matching key (under `processed/`) is ignored  | The S3-event loop is broken.                              |

## Run it offline (no AWS credentials, no SAM CLI)

```bash
cd medium/meta/datavidhya/14_Process_S3_Events_With_Lambda/

# Self-asserting driver -- 8 stages' worth of checks, all PASS.
../../../.env/bin/python 01_process_csv_upload.py

# pytest suite -- 6 unit tests.
../../../.env/bin/python -m pytest tests/ -v
```

Both run against a stub S3 client implemented in `tests/test_handler.py` and
`01_process_csv_upload.py`, so they exercise the real handler code path but
need no AWS account.

## Deploy to AWS (when you want a real event-driven run)

```bash
sam build                                                # produces .aws-sam/
sam deploy --guided                                      # provisions bucket + function
aws s3 cp data/orders_raw.csv \
    s3://orders-lab-<account>-<region>/raw/orders_2026-09-27.csv
sam logs -n OrdersProcessorFunction --tail               # watch CloudWatch

# Local invoke against the bundled event fixture (no AWS account required)
sam local invoke -e events/s3-put-event.json
#   (uses events/s3-put-event.json's payload shape; raw/orders_2026-09-27.csv
#    still has to exist locally for the handler to read -- `sam local start-api`
#    + curl/POST is the alternative when the bucket doesn't exist yet)
```

The first `sam deploy --guided` will prompt for a stack name and region. After
that, `sam deploy` reuses `samconfig.toml`.

## What the handler actually does

1. **Skip** — non-matching keys (anything not under `raw/` and `*.csv`) are
   ignored. The SAM-side `S3Key.Rules` filter also enforces this, but the
   handler re-checks because in production an outside party could write
   directly to `processed/` and you want to be defensive.
2. **Read** — `get_object` returns the body as a `StringIO` for `DictReader`.
3. **Validate** — every row is checked for:
   - missing required field (`missing_field:<col>`)
   - amount ≤ 0 or non-numeric (`bad_amount:not_a_number` / `…:not_positive`)
   - currency not in `{USD, EUR, GBP, JPY, INR}` (`bad_currency:<code>`)
   - date not matching `YYYY-MM-DD` (`bad_date:<value>`)
4. **Deduplicate** — rows with the same `order_id` as an already-accepted row
   are rejected (`duplicate_order_id`). First occurrence wins.
5. **Enrich** — accepted rows gain `amount_usd`, `processed_at`, `row_hash`.
6. **Write** — both lists are written to `processed/` and `rejected/` with the
   same basename. The handler NEVER round-trips back to `raw/` — otherwise
   each write would re-trigger the function and you'd pay forever.

## Traps the lab expects you to hit

- **Same-prefix loop** — if `processed/` had the same prefix as `raw/`, every
  output would re-trigger the function. The SAM `S3Key` filter on `raw/` AND
  the handler's `_should_process` are both required to break it.
- **Unfiltered `ObjectCreated:*`** — fires for every create, including
  `processed/` writes. Same defense.
- **Idempotency** — re-uploading the same file should produce the same
  `processed_at` IF the timestamp were derived from the input. Currently it
  isn't (`_now()` is wall-clock). The lab accepts this; for true idempotency
  you'd hash `(bucket, key, etag)` and reuse that as the marker.
- **CSV `DictReader` swallows missing columns** — it returns an empty string.
  The handler checks for empty strings, not key-presence, which is the right
  call for "the field is there but blank."
- **`round(99.5, 2)` is fine numerically, but `str()` drops the trailing zero**
  → `99.5`, not `"99.50"`. The handler formats with `f"{…:.2f}"` to make the
  output byte-stable across re-runs.
- **Lab IAM is over-broad** — `AmazonS3ReadOnlyAccess` + `AmazonS3FullAccess`
  is convenient for a 60-min lab but would never pass a security review. The
  "Going to production" section below shows the correct policy.

## Going to production

Three things to change before this leaves a lab:

1. **Scope IAM to the bucket ARN:**
   ```yaml
   Policies:
     - Version: '2012-10-17'
       Statement:
         - Effect: Allow
           Action: s3:GetObject
           Resource: !Sub "arn:aws:s3:::${OrdersBucket}/raw/*"
         - Effect: Allow
           Action: s3:PutObject
           Resource:
             - !Sub "arn:aws:s3:::${OrdersBucket}/processed/*"
             - !Sub "arn:aws:s3:::${OrdersBucket}/rejected/*"
   ```
2. **Dead-letter queue** — failed invocations (the handler raises) currently
   retried twice, then dropped. Add an `SQS` or `SNS` `DeadLetter` config.
3. **Concurrency limit** — without a reserved-concurrency cap, a noisy bucket
   could scale to thousands of parallel handlers and exhaust your account
   limit. Add `ReservedConcurrentExecutions: 10` to the function.

## Verification (the lab's definition of done)

The lab's "lab complete" check is: a CSV dropped in `raw/` produces a
`processed/` CSV containing only the valid rows, with the calculated fields,
and the bad rows end up in `rejected/` with a reason. `01_process_csv_upload.py`
asserts exactly that, against the expected CSVs in `data/`. When the driver
prints `=== All Q14 stages pass ===`, the local mock of the lab is green.
