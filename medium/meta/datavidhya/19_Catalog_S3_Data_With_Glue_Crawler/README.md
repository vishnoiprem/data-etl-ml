# 19 — Catalog S3 Data with a Glue Crawler

A runnable, **offline-first** mirror of the AWS Skill Builder lab
**"Catalog S3 Data with a Glue Crawler."** Seven stages, eight shell
scripts that map exactly to the lab's "click in the console"
instructions, plus a pytest suite that simulates Glue + S3 + Athena
in-process via moto. No AWS credentials needed for verification.

```
                       ┌──────────────────────────────────┐
                       │   glue-crawler-catalog-bucket-…   │
                       │                                    │
                       │   raw/orders/orders.csv   (CSV)    │
                       │   raw/customers/customers.json    │
                       │              (JSON array)         │
                       └───────────────┬────────────────────┘
                                       │  one folder per table
                                       ▼
                       ┌──────────────────────────────────┐
                       │   Glue Crawler                    │
                       │     - reads sample of values      │
                       │     - infers per-column type      │
                       │     - writes Glue Data Catalog    │
                       └───────────────┬────────────────────┘
                                       │  create_table (1 per prefix)
                                       ▼
                       ┌──────────────────────────────────┐
                       │   Glue Data Catalog               │
                       │     catalog_db_xxxxx              │
                       │       orders   (CSV; 6 columns)   │
                       │       customers (JSON; 5 columns) │
                       └───────────────┬────────────────────┘
                                       │  Glue = metadata layer
                                       ▼
                       ┌──────────────────────────────────┐
                       │   Athena (engine v3)               │
                       │     SELECT ... FROM orders        │
                       │     JOIN customers ON ...         │
                       └────────────────────────────────────┘
```

## Files

| Path                                              | Purpose                                  |
|---------------------------------------------------|------------------------------------------|
| `sample_data/orders/orders.csv`                   | The 12-row seed CSV (with one "N/A" row that triggers the type-mis-inference trap) |
| `sample_data/customers/customers.json`            | The 7-record JSON customer dataset        |
| `catalog.py`                                      | moto-backed Glue + S3 + Athena simulator with crawler type-inference logic |
| `01_catalog_s3_with_glue_crawler.py`              | Self-asserting driver (7 stages, 24 checks) |
| `scripts/00_set_lab.sh`                           | Helper: set BUCKET / DATABASE / ROLE_ARN / WORKGROUP |
| `scripts/01_inspect_bucket.sh` through `07_teardown.sh` | Seven stage scripts (one per lab stage) |
| `scripts/run_all.sh`                              | Optional: run stages 1–6 in sequence      |
| `tests/conftest.py`                               | Pytest fixture: fresh catalog per test     |
| `tests/test_catalog.py`                           | 10 pytest tests, no AWS creds             |
| `README.md`                                       | This file                                |

## The 7 lab stages — mapped to artifacts

| Stage | Lab step                                                       | Artifact                              |
|-------|----------------------------------------------------------------|---------------------------------------|
| 1     | Inspect the seed bucket (1 CSV folder + 1 JSON folder)         | `01_inspect_bucket.sh`, `test_stage1_*` |
| 2     | Create the Glue crawler pointed at both prefixes                | `02_create_crawler.sh`, `test_stage2_*` |
| 3     | Run the crawler, wait for it to finish                          | `03_run_crawler.sh`, `test_stage3_*`   |
| 4     | Review the catalog tables; spot the `order_date` mis-inference | `04_review_schemas.sh`, `test_stage4_*` |
| 5     | Edit `order_date` from `string` → `date` via `UpdateTable`     | `05_fix_schema.sh`, `test_stage5_*`    |
| 6     | Query both tables via Athena (count + JOIN + GROUP BY)          | `06_query_join.sh`, `test_stage6_*`    |
| 7     | Drop the catalog tables; S3 data survives                      | `07_teardown.sh`, `test_stage7_*`      |

## Run it offline (no AWS account)

```bash
cd medium/meta/datavidhya/19_Catalog_S3_Data_With_Glue_Crawler/

# Self-asserting driver -- 24 checks, all PASS.
../../../.env/bin/python 01_catalog_s3_with_glue_crawler.py

# pytest -- 10 tests, all PASS.
../../../.env/bin/python -m pytest tests/ -v
```

Internally the driver and tests use `moto.mock_aws()` to simulate the
S3 bucket, Glue Data Catalog, Glue crawler, and Athena workgroup
in-process; both run with zero network and zero credentials. The crawler
type-inference is a real CSV/JSON sampler — not mocked — so the lab's
"trap" column actually falls back to `string` because the seed CSV
contains a row with `order_date = "N/A"`.

## Run it against a real AWS account

```bash
export BUCKET=glue-crawler-catalog-bucket-a1b2c3
export DATABASE=catalog_db_x7k2q9
export ROLE_ARN="arn:aws:iam::123456789012:role/GlueCrawlerLabRole-Ab3xYz"
export WORKGROUP=crawler-catalog-Ab3xYz
export AWS_REGION=us-east-1

./scripts/run_all.sh      # stages 1-6
./scripts/07_teardown.sh  # explicit teardown
```

`run_all.sh` runs the six mutating scripts in order. Stage 0 (capture
resource names) is run separately because it requires pasting from the
lab console. Stage 7 (teardown) is also separate so you can inspect the
catalog before destroying it.

## What each lab stage actually does

### Stage 1 — Inspect the seed bucket

Two prefixes, two formats. The crawler's "one folder per table" rule
means we'll end up with exactly **two** catalog tables, one per prefix:

```
s3://$BUCKET/raw/orders/orders.csv        (CSV -- OpenCSVSerde)
s3://$BUCKET/raw/customers/customers.json (JSON -- JsonSerDe)
```

### Stage 2 — Create the Glue crawler

A crawler has four moving parts: a name, an IAM role (the lab pre-
provisions `GlueCrawlerLabRole-XXXXX`), a target Glue database, and one
or more S3 targets. Two `S3Target` entries = one table per prefix.

### Stage 3 — Run the crawler

`StartCrawler` transitions the crawler to `RUNNING`. The lab polls
`GetCrawler.State` until it flips back to `READY`, indicating the last
run completed. Crawlers take 30–90 seconds for a small bucket; 5–15
minutes for a million-object prefix.

### Stage 4 — The type-inference trap

The crawler reads a sample of records per file and assigns each column a
**broadest-match type**:

| Column         | Sample values                         | Inferred |
|----------------|---------------------------------------|----------|
| `order_id`     | `1001, 1002, 1003`                    | `bigint` |
| `customer_id`  | `42, 17, 33`                          | `bigint` |
| `amount`       | `99.50, 250.00, 15.00`                | `double` |
| `currency`     | `USD, EUR, GBP`                       | `string` |
| `order_date`   | `2026-09-20, 2026-09-21, N/A, …`      | **`string`** ← trap |
| `status`       | `placed, cancelled`                    | `string` |
| `customers.id` | `42, 17, 33`                          | `bigint` |
| `customers.signup_date` | `2024-03-15, …` (all clean)   | `date` ✓ |

The single `N/A` row poisons the `order_date` column. The crawler can't
say "11 of 12 dates are valid, so the column is `date`" — Glue's rule
is "all-or-nothing," and one bad value falls back to `string`. Stage 5
fixes this in the catalog without touching S3.

### Stage 5 — Patch the schema in place

```bash
aws glue update-table --database-name "$DATABASE" \
    --table-input "$(...)"          # full TableInput JSON, with order_date = "date"
```

`UpdateTable` rewrites the catalog entry and **only** the catalog entry.
The S3 file still has `"N/A"` for row 1009. In production the fix is two-
step:

1. Edit the catalog (this stage).
2. Fix the bad row in S3 (open the CSV, replace `"N/A"` with a real date
   or remove the row).

A consumer that runs `SELECT CAST(order_date AS DATE) FROM orders`
against the now-typed `date` column will fail-projection on the `N/A`
row. Athena logs the row's offset but doesn't refile the CSV.

### Stage 6 — Athena queries against both tables

Two queries; one warm-up, one the lab's "money shot":

```sql
-- Per-customer order totals, ranked:
SELECT c.name, c.tier, COUNT(*)    AS orders,
                     SUM(CAST(o.amount AS double)) AS total
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.name, c.tier
ORDER BY total DESC
LIMIT 5;
```

The lab's expected output ranks `Alice Johnson` (id=42) at the top
because she has three orders (1001, 1006, 1012) totalling **$354.75**.

### Stage 7 — DROP TABLE keeps S3 intact

`DeleteTable` removes the Glue catalog entry. The S3 objects survive
because Glue tables are **metadata**; the S3 bucket is the data. In
production you might:

- Have hundreds of crawlers re-classify the data every night.
- Manually fix catalog tables after each crawler run.
- Or replace Glue tables with Glue table versions (`UpdateTable` with
  `VersionId`) for safer rollback.

## Traps the lab expects you to hit

- **One folder, one table.** Glue will *not* merge two different schemas
  into one table. Drop the second heterogeneous CSV into `raw/orders/`
  and the crawler logs an error and skips the new file.
- **The crawler doesn't know what's "good" data.** It samples the first
  megabyte (or first 1000 rows) and types each column. Domain knowledge
  (`order_date` is logically always a date) has to come from you. Stage 5
  is exactly that step.
- **`UpdateTable` reads-modify-writes.** Forget to copy a column and it
  disappears from the catalog. The script reads the table via
  `get-table`, patches the column, and sends the full `TableInput` back
  -- this is the canonical AWS pattern.
- **Crawlers bill per object.** Every object the crawler reads costs.
  For an S3 inventory that grows by 100k objects a day, the daily crawl
  is a non-trivial line item.
- **Glue has quotas.** A single database caps at 100k tables; a single
  account caps at 100 databases. The lab's `catalog_db_xxxxx` is one
  database; production data lakes either partition by use-case
  (catalog_raw, catalog_curated, catalog_marts) or use Lake Formation.

## Going to production

Four things to add before this leaves a lab:

1. **Schedule the crawler on EventBridge.** A one-shot crawler gives you
   "what the data looked like when I clicked run." Production wants
   nightly (or per-prefix-on-write via S3 events) — EventBridge
   `aws.glue.crawler.state_change` + a scheduled rule.
2. **Add a Glue Data Quality rule.** The lab's `order_date` trap is
   exactly what Data Quality rules catch — "expect 100% parseable
   dates, fail otherwise." Set up a DQ ruleset on the catalog table.
3. **Tag every catalog table.** Glue table tags propagate to Lake
   Formation, IAM policies, and Athena cost allocation. The lab skips
   this; production can't skip it.
4. **Replace the crawler with a custom classifier when inference is bad.**
   Glue classifiers let you pre-define a schema for known folder layouts
   (e.g. "any CSV whose first row is order_id, customer_id, amount is
   the `orders` table with `bigint, bigint, double` types"). The crawler
   honors classifiers over inference when both apply.

## Verification

The lab's "lab complete" check is: the Glue database contains two
tables (`orders` and `customers`); the `orders` table has 6 columns with
`order_date` overridden to `date`; an Athena SELECT-JOIN returns the
expected per-customer totals. The driver and pytest suite exercise all
three without AWS. The shell scripts are the live-account equivalent.
