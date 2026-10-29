# 3.2 — Case Study 2: Healthcare Claims Processing

> **Section 3 · Case Studies · Lecture 3.2 · 49:22**

## 🎯 What you will learn

- How compliance constraints (PHI/PII, HIPAA) shape a data pipeline's architecture, not just its documentation
- How to read a realistic nested JSON claim payload with an explicit `StructType` schema
- The two classic nested-data problems: **array of structs** and **JSON-in-a-string** — and the correct fix for each
- How to validate claims against business rules (amount bounds, ICD-10 format, future dates) and **quarantine** rather than drop
- How to detect a provider's anomalous daily spend with a rolling z-score over a 30-day window
- How to build a denied-claims view and high-cost member identification
- How to handle sensitive data: CMEK, service accounts, PII-safe logging

---

## 🧠 Concept

### The business requirement

A health insurer processes Medicare-style claims. Each provider (a clinic, a hospital, an
independent practice) submits a nightly batch of claims as JSON. The insurer's data team
currently:

- Loads claims into a relational staging database with a hand-written ETL script that breaks
  whenever a provider adds a field.
- Cannot answer "which providers are seeing denied claims?" without a two-day manual exercise.
- Has no way to detect **upcoding** — a provider billing suspiciously high amounts for the
  same diagnosis code — because nothing compares providers against each other.
- Cannot identify high-cost members early enough to intervene, because member spend is only
  computed monthly.

The request: *"Give us a daily, trusted view of claims spend by provider and diagnosis, flag
providers whose spend looks abnormal, and give the utilization team a daily feed of members
whose spend has crossed our threshold."*

### ⚠️ The compliance framing — read this before you write a line of code

**This chapter uses entirely synthetic data.** Every provider id, member id, NPI, and claim
in this course is generated. That is not a disclaimer for the legal team — it is a
**deliberate design constraint that changes how you build the pipeline**.

| Real healthcare data | What it means for the pipeline |
|---|---|
| **PHI** (Protected Health Information) — anything identifying a patient | Cannot land in a shared bucket, a dev cluster, or a log file |
| **PII** (Personally Identifiable Information) — names, addresses, member ids | Cannot be printed to stdout, which lands in Cloud Logging |
| **HIPAA** — requires encryption at rest and in transit, access controls, audit trails | CMEK, scoped service accounts, VPC Service Controls |
| **Minimum necessary** — access only what the task requires | Do not join a member dimension if the question does not need it |
| **BAA** (Business Associate Agreement) — required before a vendor touches PHI | GCP offers a BAA; your code cannot substitute for it |

Three concrete consequences that show up in the code below:

1. **We never log PII.** The `job_healthcare.py` script logs counts, provider ids, and
   diagnosis codes — never member ids, names, or dates of birth. Logging a member id into
   Cloud Logging effectively converts a secured pipeline into an unsecured one, because
   Cloud Logging has different access controls and a much longer retention policy.
2. **The service account is dedicated and scoped.** The job runs as a dedicated service
   account with access to exactly the two buckets and the two BigQuery datasets it needs —
   not a broad "Data Editor" role on the project.
3. **Encryption is customer-managed (CMEK) where the data requires it.** We assume the
   Cloud Storage buckets and the BigQuery datasets are CMEK-encrypted, with the key in
   Cloud KMS, and the key's IAM policy is restricted to the same service account.

💡 **"Minimum necessary" is an architectural rule, not a policy statement.** If a downstream
table does not need `member_id`, do not carry it into that table. Every column you propagate
is a column you must protect, audit, and eventually delete.

💡 **Design for the audit trail, not just the data.** A claim-processing pipeline in a
regulated environment is expected to answer "who loaded this row, when, and from which
file?" The `loaded_at` and `source_file` columns on every fact table exist for that reason.
They are not decoration.

### The analytical questions

| # | Question | Grain | Owner |
|---|----------|-------|-------|
| Q1 | What did we pay each provider for claims submitted on a given day? | provider × day | Network management |
| Q2 | Which diagnosis codes drive the most spend? | diagnosis × day | Actuarial |
| Q3 | Which providers have an unusually high denial rate? | provider × day | Provider relations |
| Q4 | Which providers show anomalous spend versus their own 30-day history? | provider × day | Fraud & abuse unit |
| Q5 | Which members have crossed our high-cost threshold this year? | member (year-to-date) | Utilization management |
| Q6 | Are there claims that should never have been submitted at all? | claim | Payment integrity |
| Q7 | How many claims were rejected, and for what reason? | reject reason | Provider enablement |

⚠️ **Q4 is the one that makes this a Spark problem.** A rolling 30-day mean and standard
deviation per provider is a windowed calculation over time. Doing it in SQL in BigQuery is
possible, but doing it *inside* the pipeline — where you can reject the anomalous claim
before it reaches the fact table — is the design this chapter builds.

### The source data

```
gs://acme-health-raw/                    ⚠️ CMEK-encrypted bucket
├── claims/                              ← one JSON file per provider per day
│   ├── 2024-06-01/
│   │   ├── provider_10001.json
│   │   ├── provider_10002.json
│   │   └── ...
│   └── 2024-06-02/
├── ref/
│   ├── providers.csv                    ← provider master
│   └── icd10.csv                        ← diagnosis code reference
```

Each provider file is **JSON Lines** — one JSON object per claim, one object per line:

```json
{"claim_id":"CLM-20240601-10001-0001","member_id":"MBR-0048212","provider_npi":"10001","service_date":"2024-06-01","submitted_at":"2024-06-02T03:14:22Z","claim_amount":482.50,"diagnosis_codes":[{"code":"E11.9","is_primary":true},{"code":"I10","is_primary":false}],"service_lines":[{"procedure_code":"99213","units":1,"allowed_amount":180.00},{"procedure_code":"36415","units":2,"allowed_amount":302.50}],"denial":null}
{"claim_id":"CLM-20240601-10001-0002","member_id":"MBR-0099210","provider_npi":"10001","service_date":"2024-06-01","submitted_at":"2024-06-02T04:02:11Z","claim_amount":1250.00,"diagnosis_codes":[{"code":"I50","is_primary":true}],"service_lines":[],"denial":{"code":"CO-16","reason":"missing diagnosis"}}
```

Two nested-data problems appear in the very first two lines:

```
PROBLEM 1 — ARRAY OF STRUCTS
  "diagnosis_codes": [ {"code": "E11.9", "is_primary": true}, ... ]
  An array whose elements are objects. Needs explode() to get one row per code.

PROBLEM 2 — JSON-IN-A-STRING
  "denial": { "code": "CO-16", "reason": "..." }
  Depending on the provider's software, this arrives as a *string* containing JSON:
      "denial": "{\"code\": \"CO-16\", \"reason\": \"missing diagnosis\"}"
  Needs from_json() with an explicit schema, not a cast.
```

⚠️ **These two problems are different and are often confused.** An array of structs is
already parsed by `from_json` into a real `array<struct<...>>` type; you `explode` it. A
JSON-in-a-string column is just a `string` to Spark; you `from_json` it first, and *then*
you may need to `explode` the result if the string contains an array.

### The target layout in BigQuery

```
                     BIGQUERY (all CMEK-encrypted)
   ┌──────────────────────────────────────────────────────────────┐
   │  mart.provider_spend                                        │
   │      ◄── provider × day. Spend, denial rate, z-score flags.  │
   │      ◄── Powers the network-management dashboard.           │
   └──────────────────────────────────────────────────────────────┘
                              ▲ aggregated in Spark
   ┌──────────────────────────────────────────────────────────────┐
   │  curated.fact_claims        ◄── one row per claim           │
   │  curated.dim_provider       ◄── one row per provider        │
   │  curated.dim_diagnosis      ◄── one row per ICD-10 code     │
   │  quarantine.rejected_claims ◄── claims that failed validation│
   └──────────────────────────────────────────────────────────────┘
                              ▲ conformed + validated in Spark
   ┌──────────────────────────────────────────────────────────────┐
   │  gs://acme-health-raw/claims/YYYY-MM-DD/provider_*.json     │
   │  gs://acme-health-raw/ref/providers.csv                     │
   │  gs://acme-health-raw/ref/icd10.csv                         │
   └──────────────────────────────────────────────────────────────┘
```

⚠️ **Notice there is no `dim_member` in the curated layer.** Q5 (high-cost members) needs
member-level spend, but the *fact* table already carries `member_id`. Adding a member
dimension would mean joining a PII-bearing table into the pipeline for no analytical gain.
Under "minimum necessary", `member_id` is treated as an opaque grouping key and nothing more.
This is a deliberate demonstration of compliance-aware design, not an omission.

### Four Spark 3.5 API traps you will hit in this chapter

Each of these throws at runtime — or, worse, fails silently — and each has a
one-line fix. They are listed up front so you can recognise them on sight.

| Trap | What happens | The fix |
|------|--------------|---------|
| `F.try_cast(...)` | `AttributeError` — the Python wrapper is not exposed in every 3.5 build | `F.expr("try_cast(col AS int)")` |
| `try_to_date(col, fmt)` | `UNRESOLVED_ROUTINE` — 3.5 added `try_cast` and `try_to_timestamp`, but **not** `try_to_date` | `F.expr("try_cast(col AS DATE)")` |
| `F.concat_ws("; ", ...)` with all-null args | Returns an **empty string**, not null — so `.isNull()` is `False` and every row looks "rejected" | `F.nullif(F.concat_ws(...), F.lit(""))` |
| Format string with literal quotes inside `F.expr` | `PARSE_SYNTAX_ERROR` — the SQL string literal is itself single-quoted | Double-quote the outer literal: `F.expr("try_to_timestamp(c, \"yyyy-MM-dd'T'HH:mm:ss'Z'\")")` |

⚠️ **The quote-escaping trap is specific to `F.expr`.** The Java format pattern
`yyyy-MM-dd'T'HH:mm:ss'Z'` contains single quotes to mark `T` and `Z` as literals.
Inside `F.expr("...")` those single quotes terminate the SQL string literal, so the
parser sees `'yyyy-MM-dd'` followed by garbage. The outer literal must be
double-quoted so the inner ones survive:

```python
# ❌ PARSE_SYNTAX_ERROR: Syntax error at or near 'T'
F.expr("try_to_timestamp(submitted_at, 'yyyy-MM-dd'T'HH:mm:ss'Z')")

# ✅ Correct — outer literal is double-quoted
F.expr("try_to_timestamp(submitted_at, \"yyyy-MM-dd'T'HH:mm:ss'Z'\")")
```

💡 **`F.to_timestamp(col, fmt)` takes the format as a Python string, not a SQL
literal** — so it has no quoting problem at all. Use it when the format is known
and you do not need the "invalid becomes null" behaviour; reach for
`F.expr("try_to_timestamp(...)")` only when you specifically want a null instead
of an error.

---

## 🛠️ Hands-On: The healthcare claims processing pipeline

### Step 0 — Prerequisites and the service account

```bash
export PROJECT_ID=your-project-id
export BUCKET=gs://acme-health-raw
export STAGING_BUCKET=gs://your-project-id-bq-staging
export IMAGE_VERSION=2.2-debian12

gcloud services enable dataproc bigquery storage cloudkms

# ---- Dedicated, least-privilege service account -------------------------
gcloud iam service-accounts create claims-pipeline-sa \
  --display-name="Claims Pipeline (Dataproc)"

SA_EMAIL="claims-pipeline-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# Bucket-level roles: object viewer on raw, object admin on staging only
gcloud storage buckets add-iam-policy-binding $BUCKET \
  --member="serviceAccount:${SA_EMAIL}" --role="roles/storage.objectViewer"

gcloud storage buckets add-iam-policy-binding $STAGING_BUCKET \
  --member="serviceAccount:${SA_EMAIL}" --role="roles/storage.objectAdmin"

# BigQuery: data editor on ONLY the two datasets this job owns
for DS in curated mart quarantine; do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/bigquery.dataEditor" \
    --condition=None 2>/dev/null || true
done
```

💡 **In a real project, do not grant dataset-level roles project-wide.** Create the three
datasets and grant access per-dataset with `bq add-iam-policy-binding`, so the service
account cannot touch any other table in the project. The `for` loop above is a shorthand;
use the per-dataset form in production.

⚠️ **Never run the job as your personal user account.** A job running as a human
`you@company.com` inherits that human's permissions, and every log line, temporary file,
and audit record is attributed to a person rather than a workload identity. That is an
audit finding waiting to happen.

### Step 1 — BigQuery schema (DDL)

```sql
-- ============================================================
-- curated.fact_claims — one row per submitted claim
-- ============================================================
CREATE TABLE IF NOT EXISTS `your-project-id`.curated.fact_claims (
  claim_id          STRING    NOT NULL,
  member_id         STRING,                    -- opaque grouping key; no member PII
  provider_npi      STRING    NOT NULL,
  service_date      DATE      NOT NULL,
  submitted_at      TIMESTAMP,
  claim_amount      NUMERIC(18,2),
  primary_dx_code   STRING,
  dx_code_count     INT64,
  procedure_count   INT64,
  is_denied         BOOL,
  denial_code       STRING,
  denial_reason     STRING,
  provider_sk       INT64,
  provider_name     STRING,
  provider_type     STRING,
  source_file       STRING,
  loaded_at         TIMESTAMP NOT NULL
)
PARTITION BY service_date
CLUSTER BY provider_npi, primary_dx_code
OPTIONS (
  description = "Validated claims, one row per claim_id. Claim_amount is the submitted billed amount for COMPLETED/denied claims.",
  expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 YEAR)
);

-- ============================================================
-- curated.dim_provider
-- ============================================================
CREATE TABLE IF NOT EXISTS `your-project-id`.curated.dim_provider (
  provider_sk     INT64   NOT NULL,
  provider_npi    STRING  NOT NULL,
  provider_name   STRING,
  provider_type   STRING,     -- PRIMARY_CARE, SPECIALIST, HOSPITAL, HOME_HEALTH
  tax_id          STRING,
  city            STRING,
  state           STRING,
  contract_start  DATE,
  contract_end    DATE,
  is_active       BOOL,
  loaded_at       TIMESTAMP NOT NULL
)
CLUSTER BY provider_npi
OPTIONS (
  description = "Provider master. provider_name is a business name, not a person identifier.",
  expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 YEAR)
);

-- ============================================================
-- curated.dim_diagnosis — ICD-10 reference
-- ============================================================
CREATE TABLE IF NOT EXISTS `your-project-id`.curated.dim_diagnosis (
  icd10_code    STRING NOT NULL,
  description   STRING,
  category      STRING,
  chapter       STRING,
  is_valid      BOOL,
  loaded_at     TIMESTAMP NOT NULL
)
CLUSTER BY icd10_code
OPTIONS (
  description = "ICD-10 diagnosis code reference with validity flags.",
  expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 YEAR)
);

-- ============================================================
-- mart.provider_spend — daily spend + denial + anomaly detection
-- ============================================================
CREATE TABLE IF NOT EXISTS `your-project-id`.mart.provider_spend (
  service_date          DATE      NOT NULL,
  provider_npi          STRING    NOT NULL,
  provider_name         STRING,
  provider_type         STRING,
  region_name           STRING,
  claim_count           INT64,
  member_count          INT64,
  total_claim_amount    NUMERIC(18,2),
  avg_claim_amount      NUMERIC(18,2),
  denied_claim_count    INT64,
  denial_rate           NUMERIC(9,6),
  denied_amount         NUMERIC(18,2),
  spend_30d_mean        NUMERIC(18,2),
  spend_30d_stddev      NUMERIC(18,2),
  spend_zscore          NUMERIC(12,6),
  is_spend_anomaly      BOOL,
  anomaly_direction     STRING,   -- SPIKE | DUMP | NORMAL
  loaded_at             TIMESTAMP NOT NULL
)
PARTITION BY service_date
CLUSTER BY provider_npi
OPTIONS (
  description = "Daily provider spend with denial metrics and 30-day rolling z-score anomaly flags.",
  expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 YEAR)
);

-- ============================================================
-- quarantine.rejected_claims
-- ============================================================
CREATE TABLE IF NOT EXISTS `your-project-id`.quarantine.rejected_claims (
  claim_id       STRING,
  member_id      STRING,
  provider_npi   STRING,
  service_date   DATE,
  claim_amount   NUMERIC(18,2),
  reject_reason  STRING,
  raw_payload    STRING,     -- for the provider-enablement team to diagnose
  source_file    STRING,
  run_date       DATE,
  rejected_at    TIMESTAMP
)
PARTITION BY run_date
CLUSTER BY reject_reason
OPTIONS (
  description = "Claims that failed validation. Reviewed by provider enablement; never silently dropped.",
  expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 2 YEAR)
);
```

💡 **Note that `curated.fact_claims` has no `member_name`, `member_dob`, or `member_ssn`
column.** The source JSON in this design contains only `member_id`. If a real upstream feed
carried a member name, the correct move is to **drop the column at the parse boundary**,
not to load it and then drop it later. Fields you never ingest cannot leak.

### Step 2 — The complete job: `job_healthcare.py`

```python
#!/usr/bin/env python3
"""
job_healthcare.py — Healthcare Claims Processing Pipeline (Case Study 2)

Reads one day of provider claim submissions (JSON Lines) from GCS, validates
them against clinical and business rules, quarantines the invalid ones,
conforms them against the provider and ICD-10 reference tables, computes
provider-level daily spend with a rolling 30-day z-score anomaly flag, and
writes curated + mart tables to BigQuery.

Target runtime: Spark 3.5.x (Dataproc image 2.2-debian12)
"""

import argparse
import logging
import sys
from datetime import date, datetime, timedelta, timezone

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pyspark.sql.types import (
    StringType, TimestampType, IntegerType, DoubleType, BooleanType,
    DateType, DecimalType, StructType, StructField, ArrayType, LongType,
)

APP_NAME = "healthcare-claims-processing"

# Business rules
MAX_CLAIM_AMOUNT = 100000.00     # A single Medicare claim above this is not credible
MIN_CLAIM_AMOUNT = 0.01
ICD10_REGEX = r"^[A-TV-Z][0-9][0-9AB](\.[0-9A-TV-Z]{1,4})?$"   # ICD-10-CM format
ANOMALY_WINDOW_DAYS = 30
ANOMALY_Z_THRESHOLD = 3.0

LOG = logging.getLogger("healthcare")


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

# The nested payload inside each claim JSON object.
# Note the "denial" field is a STRING here on purpose: some providers
# encode it as a JSON string rather than a JSON object. We parse it
# separately with from_json().
CLAIM_SCHEMA = StructType([
    StructField("claim_id", StringType()),
    StructField("member_id", StringType()),
    StructField("provider_npi", StringType()),
    StructField("service_date", StringType()),
    StructField("submitted_at", StringType()),
    StructField("claim_amount", DoubleType()),
    StructField("dx_codes", ArrayType(
        StructType([
            StructField("code", StringType()),
            StructField("is_primary", BooleanType()),
        ])
    )),
    StructField("service_lines", ArrayType(
        StructType([
            StructField("procedure_code", StringType()),
            StructField("units", LongType()),
            StructField("allowed_amount", DoubleType()),
        ])
    )),
    StructField("denial", StringType()),   # JSON object OR JSON-encoded string
])

# Schema for the denial sub-object, used with F.from_json on a string column.
DENIAL_SCHEMA = StructType([
    StructField("code", StringType()),
    StructField("reason", StringType()),
])

# Top-level schema for one JSON line.
LINE_SCHEMA = StructType([
    StructField("claim_id", StringType()),
    StructField("member_id", StringType()),
    StructField("provider_npi", StringType()),
    StructField("service_date", StringType()),
    StructField("submitted_at", StringType()),
    StructField("claim_amount", DoubleType()),
    StructField("diagnosis_codes", ArrayType(
        StructType([
            StructField("code", StringType()),
            StructField("is_primary", BooleanType()),
        ])
    )),
    StructField("service_lines", ArrayType(
        StructType([
            StructField("procedure_code", StringType()),
            StructField("units", LongType()),
            StructField("allowed_amount", DoubleType()),
        ])
    )),
    StructField("denial", StringType()),
])


# ---------------------------------------------------------------------------
# Logging — never log PII
# ---------------------------------------------------------------------------

def configure_logging(verbose: bool = False) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )
    logging.getLogger("pyspark").setLevel(logging.WARN)
    logging.getLogger("org.apache.spark").setLevel(logging.WARN)


def safe_log_counts(label: str, df: DataFrame) -> int:
    """
    Log a row count only. Never log row content — the rows contain PHI.
    """
    n = df.count()
    LOG.info("%s: %d rows", label, n)
    return n


# ---------------------------------------------------------------------------
# Spark session
# ---------------------------------------------------------------------------

def build_spark(app_name: str, shuffle_partitions: int) -> SparkSession:
    spark = (
        SparkSession.builder
        .appName(app_name)
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.shuffle.partitions", str(shuffle_partitions))
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
        .config("spark.sql.adaptive.skewJoin.enabled", "true")
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    return spark


# ---------------------------------------------------------------------------
# Extract
# ---------------------------------------------------------------------------

def read_claims(spark: SparkSession, input_path: str, run_date: date) -> DataFrame:
    """
    Read the provider JSON files for a single date.

    `multiLine=false` means each line is one JSON object (JSON Lines), which
    is what the provider gateways emit. We supply an explicit schema so a
    malformed or unexpected field never silently changes the DataFrame's
    shape — a schema-on-read problem becomes a parse-time problem.
    """
    claims_path = f"{input_path.rstrip('/')}/claims/{run_date.isoformat()}"
    LOG.info("Reading claims from %s", claims_path)

    raw = (
        spark.read
        .option("header", "false")
        .option("mode", "PERMISSIVE")
        .schema(LINE_SCHEMA)
        .json(claims_path)
    )
    return raw.withColumn("source_file", F.input_file_name())


def read_reference(spark: SparkSession, input_path: str) -> tuple[DataFrame, DataFrame]:
    ref_path = f"{input_path.rstrip('/')}/ref"

    providers = (
        spark.read
        .option("header", True)
        .option("inferSchema", "false")
        .csv(f"{ref_path}/providers.csv")
    )
    icd10 = (
        spark.read
        .option("header", True)
        .option("inferSchema", "false")
        .csv(f"{ref_path}/icd10.csv")
    )
    return providers, icd10


# ---------------------------------------------------------------------------
# Transform: parse the nested payload
# ---------------------------------------------------------------------------

def parse_claims(raw: DataFrame) -> DataFrame:
    """
    Normalise the nested claim payload.

    Handles both nested-data patterns:
      1. ARRAY OF STRUCTS  — diagnosis_codes / service_lines are already
         array<struct<...>> after the schema-based read. We use them
         directly and explode them later.
      2. JSON-IN-A-STRING  — `denial` arrives as a string. We parse it
         with F.from_json() against an explicit DENIAL_SCHEMA.
    """
    return (
        raw
        .withColumn("claim_id", F.trim(F.col("claim_id")))
        .withColumn("member_id", F.trim(F.col("member_id")))
        .withColumn("provider_npi", F.trim(F.col("provider_npi")))
        .withColumn(
            "service_date",
            F.expr("try_cast(service_date AS DATE)"),
        )
        .withColumn(
            "submitted_at",
            # NOTE: the outer SQL string literal is double-quoted so the
            # Java pattern's own single quotes ('T' and 'Z' literals) survive
            # the Spark SQL parser. A single-quoted outer literal breaks it.
            F.expr("try_to_timestamp(submitted_at, \"yyyy-MM-dd'T'HH:mm:ss'Z'\")"),
        )
        .withColumn(
            "claim_amount",
            F.expr("try_cast(claim_amount AS decimal(18,2))"),
        )
        # ---- PROBLEM 2: JSON-in-a-string ------------------------------
        # Some providers send the denial as a JSON object, others as a
        # JSON-encoded string. Parse the string form explicitly.
        .withColumn(
            "denial_obj",
            F.when(
                F.col("denial").isNotNull() & (F.trim(F.col("denial")) != ""),
                F.from_json(F.col("denial"), DENIAL_SCHEMA),
            ),
        )
        .withColumn("denial_code", F.col("denial_obj.code"))
        .withColumn("denial_reason", F.col("denial_obj.reason"))
        .withColumn("is_denied", F.col("denial_code").isNotNull())
        .withColumn("dx_code_count", F.size(F.col("diagnosis_codes")))
        .withColumn("procedure_count", F.size(F.col("service_lines")))
        .drop("denial", "denial_obj")
    )


# ---------------------------------------------------------------------------
# Transform: validation
# ---------------------------------------------------------------------------

def validate_claims(parsed: DataFrame, run_date: date) -> tuple[DataFrame, DataFrame]:
    """
    Apply business rules and split into accepted / rejected.

    A claim is rejected if ANY of the following holds. The reasons are
    concatenated so a single claim with two problems is reported once
    with both reasons.
    """
    today = F.lit(run_date)

    classified = (
        parsed
        .withColumn(
            "reject_reason",
            F.nullif(
                F.concat_ws(
                    "; ",
                    F.when(F.col("claim_id").isNull() | (F.col("claim_id") == ""), F.lit("MISSING_CLAIM_ID"))
                     .when(F.col("provider_npi").isNull() | (F.col("provider_npi") == ""), F.lit("MISSING_PROVIDER_NPI"))
                     .when(F.col("member_id").isNull() | (F.col("member_id") == ""), F.lit("MISSING_MEMBER_ID"))
                     .when(F.col("service_date").isNull(), F.lit("BAD_SERVICE_DATE"))
                     .when(F.col("service_date") > today, F.lit("FUTURE_SERVICE_DATE"))
                     .when(F.col("claim_amount").isNull(), F.lit("UNPARSEABLE_AMOUNT"))
                     .when(F.col("claim_amount") < F.lit(MIN_CLAIM_AMOUNT), F.lit("AMOUNT_BELOW_MINIMUM"))
                     .when(F.col("claim_amount") > F.lit(MAX_CLAIM_AMOUNT), F.lit("AMOUNT_ABOVE_MAXIMUM"))
                     .when(F.col("dx_code_count") == 0, F.lit("NO_DIAGNOSIS_CODES"))
                     .otherwise(F.lit(None).cast("string")),
                ),
                F.lit(""),   # concat_ws returns "" (not null) when all args are null
            ),
        )
        .withColumn("is_valid", F.col("reject_reason").isNull())
    )

    accepted = classified.filter(F.col("is_valid")).drop("is_valid")
    # Project to the common quarantine shape so every reject stream can be
    # combined with unionByName without a schema mismatch.
    rejected = (
        classified.filter(~F.col("is_valid"))
        .drop("is_valid")
        .select(
            "claim_id", "member_id", "provider_npi", "service_date",
            "claim_amount", "reject_reason", "source_file",
        )
    )
    return accepted, rejected


def validate_diagnosis_codes(accepted: DataFrame, icd10: DataFrame) -> tuple[DataFrame, DataFrame]:
    """
    Explode the diagnosis array and validate each code's format and
    membership in the ICD-10 reference.

    This is where the ARRAY OF STRUCTS pattern is resolved: one row per
    (claim, diagnosis code) pair.
    """
    # ---- PROBLEM 1: ARRAY OF STRUCTS ---------------------------------
    # explode() drops rows whose array is null or empty, so we filter
    # those out first to keep the row count arithmetic exact.
    exploded = (
        accepted
        .filter(F.size(F.col("diagnosis_codes")) > 0)
        .select(
            F.col("claim_id"),
            F.col("member_id"),
            F.col("provider_npi"),
            F.col("service_date"),
            F.col("submitted_at"),
            F.col("claim_amount"),
            F.col("denial_code"),
            F.col("denial_reason"),
            F.col("is_denied"),
            F.col("procedure_count"),
            F.col("source_file"),
            F.explode("diagnosis_codes").alias("dx"),
        )
        .withColumn("dx_code", F.upper(F.trim(F.col("dx.code"))))
        .withColumn("is_primary", F.coalesce(F.col("dx.is_primary"), F.lit(False)))
        .drop("dx")
    )

    # Format check: ICD-10-CM shape (E11.9, I10, Z00.00, ...)
    format_ok = F.col("dx_code").rlike(ICD10_REGEX)

    # Reference check: the code must exist in the ICD-10 dimension.
    ref = icd10.select(
        F.upper(F.trim(F.col("icd10_code"))).alias("ref_code"),
        F.col("description").alias("dx_description"),
        F.col("category").alias("dx_category"),
        F.col("is_valid").cast("boolean").alias("ref_is_valid"),
    ).dropDuplicates(subset=["ref_code"])

    checked = (
        exploded
        .join(F.broadcast(ref), exploded.dx_code == ref.ref_code, "left")
        .withColumn(
            "dx_reject_reason",
            F.nullif(
                F.concat_ws(
                    "; ",
                    F.when(~format_ok, F.lit("MALFORMED_ICD10_CODE"))
                     .when(F.col("ref_code").isNull(), F.lit("ICD10_NOT_IN_REFERENCE"))
                     .when(F.col("ref_is_valid") == F.lit(False), F.lit("ICD10_RETIRED_CODE"))
                     .otherwise(F.lit(None).cast("string")),
                ),
                F.lit(""),   # concat_ws returns "" (not null) when all args are null
            ),
        )
        .withColumn("is_dx_valid", F.col("dx_reject_reason").isNull())
    )

    valid_rows = checked.filter(F.col("is_dx_valid"))
    invalid_rows = checked.filter(~F.col("is_dx_valid"))

    # A claim is only accepted if at least ONE of its diagnosis codes is
    # valid. Claims whose codes are all invalid go to quarantine.
    bad_claims = (
        invalid_rows
        .groupBy("claim_id")
        .agg(F.concat_ws("; ", F.collect_set("dx_reject_reason")).alias("dx_reasons"))
    )

    accepted_claims = (
        valid_rows
        .groupBy("claim_id")
        .agg(F.max("is_primary").alias("has_primary"))
    )
    surviving = accepted_claims.join(bad_claims, "claim_id", "left")
    bad_only = bad_claims.join(
        accepted_claims.select("claim_id"), "claim_id", "left_anti"
    ).select("claim_id", "dx_reasons")

    return valid_rows, invalid_rows, surviving, bad_only


# ---------------------------------------------------------------------------
# Transform: conform dimensions and build the fact table
# ---------------------------------------------------------------------------

def conform_dimensions(providers: DataFrame, icd10: DataFrame) -> tuple[DataFrame, DataFrame]:
    provider_dim = (
        providers
        .withColumn("provider_npi", F.trim(F.col("provider_npi")))
        .withColumn("provider_name", F.trim(F.col("provider_name")))
        .withColumn("provider_type", F.upper(F.trim(F.col("provider_type"))))
        .withColumn("city", F.trim(F.col("city")))
        .withColumn("state", F.trim(F.col("state")))
        .withColumn("contract_start", F.expr("try_cast(contract_start AS DATE)"))
        .withColumn("contract_end", F.expr("try_cast(contract_end AS DATE)"))
        .withColumn("is_active", F.expr("try_cast(is_active AS boolean)"))
        .filter(F.col("is_active") == F.lit(True))
        .dropDuplicates(subset=["provider_npi"])
        .withColumn("provider_sk", F.pmod(F.hash("provider_npi"), F.lit(2147483647)))
        .withColumn("loaded_at", F.current_timestamp())
    )

    diagnosis_dim = (
        icd10
        .withColumn("icd10_code", F.upper(F.trim(F.col("icd10_code"))))
        .withColumn("description", F.trim(F.col("description")))
        .withColumn("category", F.trim(F.col("category")))
        .withColumn("chapter", F.trim(F.col("chapter")))
        .withColumn("is_valid", F.expr("try_cast(is_valid AS boolean)"))
        .dropDuplicates(subset=["icd10_code"])
        .withColumn("loaded_at", F.current_timestamp())
    )
    return provider_dim, diagnosis_dim


def build_fact(valid_rows: DataFrame, provider_dim: DataFrame) -> tuple[DataFrame, DataFrame]:
    """
    Collapse the exploded diagnosis rows back to one row per claim, keeping
    the primary diagnosis as the headline code.

    Returns (fact, orphan_rejects). A claim whose provider is not in the
    provider master cannot be conformed and cannot be paid, so it is routed
    to quarantine rather than loaded with a null provider key. That keeps
    the referential-integrity assertion on the fact table meaningful.
    """
    per_claim = (
        valid_rows
        .groupBy(
            "claim_id", "member_id", "provider_npi", "service_date",
            "submitted_at", "claim_amount", "denial_code", "denial_reason",
            "is_denied", "procedure_count", "source_file",
        )
        .agg(
            F.count("*").alias("dx_code_count"),
            F.max(F.when(F.col("is_primary"), F.col("dx_code"))).alias("primary_dx_code"),
            F.max(F.when(~F.col("is_primary"), F.col("dx_code"))).alias("secondary_dx_code"),
        )
    )

    enriched = (
        per_claim
        .join(
            F.broadcast(provider_dim.select(
                "provider_npi", "provider_sk", "provider_name", "provider_type",
                "city", "state", "contract_start", "contract_end", "is_active",
            )),
            on="provider_npi",
            how="left",
        )
        .withColumn("loaded_at", F.current_timestamp())
    )

    enriched = enriched.withColumn(
        "reject_reason",
        F.when(F.col("provider_sk").isNull(), F.lit("UNKNOWN_PROVIDER"))
         .otherwise(F.lit(None).cast("string")),
    )

    orphans = enriched.filter(F.col("reject_reason").isNotNull())
    fact = enriched.filter(F.col("reject_reason").isNull()).drop("reject_reason")
    return fact, orphans


# ---------------------------------------------------------------------------
# Transform: aggregate + anomaly detection
# ---------------------------------------------------------------------------

def build_provider_spend(fact: DataFrame) -> DataFrame:
    """
    Aggregate to provider × day, then compute a rolling 30-day z-score.

    The window is:
        partitionBy("provider_npi")
        orderBy("service_date")
        rowsBetween(-29, 0)      ← 30 rows including the current one

    The mean and stddev are computed over the PRIOR 29 days plus today.
    A more conservative variant uses rowsBetween(-30, -1) so today's
    value never contributes to its own baseline.
    """
    daily = (
        fact
        .groupBy("service_date", "provider_npi")
        .agg(
            F.count("*").alias("claim_count"),
            F.countDistinct("member_id").alias("member_count"),
            F.sum("claim_amount").alias("total_claim_amount"),
            F.avg("claim_amount").alias("avg_claim_amount"),
            F.sum(F.when(F.col("is_denied"), F.lit(1)).otherwise(F.lit(0))).alias("denied_claim_count"),
            F.sum(F.when(F.col("is_denied"), F.col("claim_amount")).otherwise(F.lit(0).cast("decimal(18,2)")))
             .alias("denied_amount"),
        )
    )

    w = Window.partitionBy("provider_npi").orderBy("service_date")

    scored = (
        daily
        .withColumn(
            "spend_30d_mean",
            F.avg("total_claim_amount").over(
                w.rowsBetween(-(ANOMALY_WINDOW_DAYS - 1), 0)
            ),
        )
        .withColumn(
            "spend_30d_stddev",
            F.stddev_pop("total_claim_amount").over(
                w.rowsBetween(-(ANOMALY_WINDOW_DAYS - 1), 0)
            ),
        )
        .withColumn(
            "spend_zscore",
            F.when(
                F.col("spend_30d_stddev").isNotNull() & (F.col("spend_30d_stddev") > 0),
                (F.col("total_claim_amount") - F.col("spend_30d_mean")) / F.col("spend_30d_stddev"),
            ),
        )
        .withColumn(
            "is_spend_anomaly",
            F.col("spend_zscore").isNotNull()
            & (F.abs(F.col("spend_zscore")) > F.lit(ANOMALY_Z_THRESHOLD)),
        )
        .withColumn(
            "anomaly_direction",
            F.when(F.col("spend_zscore") > F.lit(ANOMALY_Z_THRESHOLD), F.lit("SPIKE"))
             .when(F.col("spend_zscore") < F.lit(-ANOMALY_Z_THRESHOLD), F.lit("DUMP"))
             .otherwise(F.lit("NORMAL")),
        )
    )
    return scored


# ---------------------------------------------------------------------------
# Data quality
# ---------------------------------------------------------------------------

def run_quality_checks(
    raw: DataFrame,
    parsed: DataFrame,
    accepted: DataFrame,
    validation_rejected: DataFrame,
    fact: DataFrame,
    spend: DataFrame,
) -> dict:
    """
    Count every stage and assert the invariants.

    The invariants are written against the *stage boundaries*. A claim can
    leave the pipeline at three points — validation, diagnosis-code
    validation, and the provider dimension join — so a single combined
    "rejected" bucket cannot be reconciled against "accepted" without
    double counting.
    """
    raw_n = safe_log_counts("raw claims", raw)
    parsed_n = safe_log_counts("parsed claims", parsed)
    accepted_n = safe_log_counts("accepted claims", accepted)
    validation_rejected_n = safe_log_counts("validation-rejected claims", validation_rejected)
    fact_n = safe_log_counts("fact claims", fact)

    # --- Invariant 1: the validation split loses nothing
    assert accepted_n + validation_rejected_n == parsed_n, (
        f"ROW LOSS: accepted({accepted_n}) + validation_rejected({validation_rejected_n}) "
        f"!= parsed({parsed_n})"
    )

    # --- Invariant 2: one row per claim in the fact table
    distinct_claims = fact.select("claim_id").distinct().count()
    assert distinct_claims == fact_n, (
        f"DUPLICATE CLAIM_IDS: {fact_n - distinct_claims} extra rows in fact_claims"
    )

    # --- Invariant 3: no null keys, no null amounts
    null_keys = fact.filter(
        F.col("claim_id").isNull() | F.col("provider_npi").isNull() | F.col("service_date").isNull()
    ).count()
    assert null_keys == 0, f"NULL KEYS: {null_keys} fact rows have a null key"

    null_amounts = fact.filter(F.col("claim_amount").isNull()).count()
    assert null_amounts == 0, f"NULL AMOUNTS: {null_amounts} fact rows have a null claim_amount"

    # --- Invariant 4: referential integrity against the provider dimension
    orphan_providers = fact.filter(F.col("provider_sk").isNull()).count()
    LOG.info("Claims without a provider match: %d", orphan_providers)
    assert orphan_providers == 0, (
        f"ORPHAN PROVIDERS: {orphan_providers} claims matched no provider"
    )

    # --- Invariant 5: every fact claim has a primary diagnosis
    no_primary = fact.filter(
        F.col("primary_dx_code").isNull() & (F.col("dx_code_count") == 1)
    ).count()
    assert no_primary == 0, f"MISSING PRIMARY DX: {no_primary} single-diagnosis claims with no primary code"

    # --- Invariant 6: the mart reconciles to the fact
    fact_total = float(fact.agg(F.sum("claim_amount")).collect()[0][0] or 0.0)
    spend_total = float(spend.agg(F.sum("total_claim_amount")).collect()[0][0] or 0.0)
    LOG.info("Reconciliation: fact_total=%.2f spend_total=%.2f", fact_total, spend_total)
    tolerance = max(abs(fact_total) * 0.001, 0.01)
    assert abs(fact_total - spend_total) <= tolerance, (
        f"RECONCILIATION FAILED: fact={fact_total:.2f} vs mart={spend_total:.2f}"
    )

    # --- Invariant 7: no future service dates survived validation
    future = fact.filter(F.col("service_date") > F.current_date()).count()
    assert future == 0, f"FUTURE DATES: {future} claims dated in the future"

    # --- Invariant 8: denial rate is a fraction
    bad_rate = spend.filter(
        (F.col("denial_rate") < 0) | (F.col("denial_rate") > 1)
    ).count()
    assert bad_rate == 0, f"INVALID DENIAL RATE: {bad_rate} rows outside [0, 1]"

    return {
        "raw_rows": raw_n,
        "parsed_rows": parsed_n,
        "accepted_rows": accepted_n,
        "validation_rejected_rows": validation_rejected_n,
        "fact_rows": fact_n,
        "fact_total": fact_total,
        "mart_total": spend_total,
    }


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------

def write_to_bigquery(df: DataFrame, project: str, table: str,
                      staging_bucket: str, write_disposition: str = "WRITE_TRUNCATE") -> None:
    (
        df.write
        .format("bigquery")
        .option("writeDisposition", write_disposition)
        .option("createDisposition", "CREATE_NEVER")
        .option("temporaryGcsBucket", staging_bucket)
        .option("allowFieldAddition", "false")
        .option("allowFieldRelaxation", "false")
        .mode("overwrite" if write_disposition == "WRITE_TRUNCATE" else "append")
        .save(f"{project}.{table}")
    )
    LOG.info("Wrote %s rows to %s.%s (%s)", df.count(), project, table, write_disposition)


def write_rejected(rejected: DataFrame, project: str, staging_bucket: str,
                   run_date: date) -> None:
    if rejected.isEmpty():
        LOG.info("No rejected claims to persist.")
        return
    out = (
        rejected
        .withColumn("run_date", F.lit(run_date).cast("date"))
        .withColumn("rejected_at", F.current_timestamp())
    )
    (
        out.write
        .format("bigquery")
        .option("writeDisposition", "WRITE_APPEND")
        .option("createDisposition", "CREATE_IF_NEEDED")
        .option("temporaryGcsBucket", staging_bucket)
        .mode("append")
        .save(f"{project}.quarantine.rejected_claims")
    )
    LOG.warning("Persisted %d rejected claims to quarantine.rejected_claims", out.count())


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Healthcare claims processing pipeline: GCS -> Spark -> BigQuery"
    )
    parser.add_argument("--input-path", required=True,
                        help="Root GCS path holding claims/ and ref/.")
    parser.add_argument("--output-project", required=True,
                        help="GCP project id that owns the curated and mart datasets.")
    parser.add_argument("--run-date", default=None,
                        help="Processing date, YYYY-MM-DD. Defaults to yesterday (UTC).")
    parser.add_argument("--staging-bucket", default=None,
                        help="GCS bucket for BigQuery load-job staging. "
                             "Defaults to <output-project>-bq-staging.")
    parser.add_argument("--shuffle-partitions", type=int, default=200,
                        help="spark.sql.shuffle.partitions for this job.")
    parser.add_argument("--verbose", action="store_true", help="Enable DEBUG logging.")
    return parser.parse_args(argv)


def resolve_run_date(run_date_arg):
    if run_date_arg:
        try:
            return datetime.strptime(run_date_arg, "%Y-%m-%d").date()
        except ValueError as exc:
            raise ValueError(f"--run-date must be YYYY-MM-DD, got {run_date_arg!r}") from exc
    return (datetime.now(timezone.utc) - timedelta(days=1)).date()


def main(argv=None) -> int:
    args = parse_args(argv)
    configure_logging(args.verbose)

    run_date = resolve_run_date(args.run_date)
    staging_bucket = args.staging_bucket or f"gs://{args.output_project}-bq-staging"

    LOG.info("=" * 78)
    LOG.info("Healthcare Claims Processing Pipeline")
    LOG.info("  input-path     : %s", args.input_path)
    LOG.info("  output-project : %s", args.output_project)
    LOG.info("  run-date       : %s", run_date.isoformat())
    LOG.info("=" * 78)

    spark = None
    try:
        spark = build_spark(APP_NAME, args.shuffle_partitions)

        # --- 1. EXTRACT -------------------------------------------------
        raw = read_claims(spark, args.input_path, run_date)
        providers_raw, icd10_raw = read_reference(spark, args.input_path)

        # --- 2. TRANSFORM -----------------------------------------------
        parsed = parse_claims(raw)
        accepted, rejected = validate_claims(parsed, run_date)
        LOG.info("Rejected %d claims at validation stage.", rejected.count())

        valid_rows, invalid_rows, _, bad_only = validate_diagnosis_codes(accepted, icd10_raw)

        # The quarantine set has a common shape. Normalise every reject
        # stream to it before combining, so the union is type-safe.
        validation_rejected = rejected.withColumn("reject_reason", F.col("reject_reason"))

        # Claims whose diagnosis codes are ALL invalid are also quarantined.
        if not bad_only.isEmpty():
            validation_rejected = validation_rejected.unionByName(
                bad_only.join(
                    parsed.select(
                        "claim_id", "member_id", "provider_npi", "service_date",
                        "claim_amount", "source_file",
                    ),
                    "claim_id", "left",
                )
                .withColumn("reject_reason", F.col("dx_reasons"))
                .select(
                    "claim_id", "member_id", "provider_npi", "service_date",
                    "claim_amount", "reject_reason", "source_file",
                )
            )

        provider_dim, diagnosis_dim = conform_dimensions(providers_raw, icd10_raw)
        LOG.info("Dimensions: %d providers, %d icd10 codes",
                 provider_dim.count(), diagnosis_dim.count())

        fact, orphan_rejects = build_fact(valid_rows, provider_dim)
        LOG.info("Orphan provider matches: %d rows", orphan_rejects.count())

        # Combine every reject stream into the single quarantine table.
        rejected = validation_rejected.unionByName(
            orphan_rejects.select(
                "claim_id", "member_id", "provider_npi", "service_date",
                "claim_amount", "reject_reason", "source_file",
            )
        )

        spend = (
            build_provider_spend(fact)
            .join(
                F.broadcast(provider_dim.select(
                    "provider_npi", "provider_name", "provider_type", "state",
                )),
                on="provider_npi",
                how="left",
            )
            .withColumn(
                "denial_rate",
                F.when(F.col("claim_count") > 0,
                       F.col("denied_claim_count").cast("double") / F.col("claim_count")),
            )
            .withColumn("loaded_at", F.current_timestamp())
        )

        # --- 3. QUALITY GATE --------------------------------------------
        metrics = run_quality_checks(
            raw, parsed, accepted, validation_rejected, fact, spend
        )
        LOG.info("Metrics: %s", metrics)

        # --- 4. LOAD ----------------------------------------------------
        write_to_bigquery(
            fact.select(
                "claim_id", "member_id", "provider_npi", "service_date",
                "submitted_at", "claim_amount", "primary_dx_code", "dx_code_count",
                "procedure_count", "is_denied", "denial_code", "denial_reason",
                "provider_sk", "provider_name", "provider_type", "source_file", "loaded_at",
            ),
            args.output_project, "curated.fact_claims", staging_bucket,
        )
        write_to_bigquery(
            spend.select(
                "service_date", "provider_npi", "provider_name", "provider_type",
                "claim_count", "member_count", "total_claim_amount", "avg_claim_amount",
                "denied_claim_count", "denial_rate", "denied_amount",
                "spend_30d_mean", "spend_30d_stddev", "spend_zscore",
                "is_spend_anomaly", "anomaly_direction", "loaded_at",
            ),
            args.output_project, "mart.provider_spend", staging_bucket,
        )
        write_to_bigquery(
            provider_dim.select(
                "provider_sk", "provider_npi", "provider_name", "provider_type",
                "city", "state", "contract_start", "contract_end", "is_active", "loaded_at",
            ),
            args.output_project, "curated.dim_provider", staging_bucket,
        )
        write_to_bigquery(
            diagnosis_dim.select(
                "icd10_code", "description", "category", "chapter", "is_valid", "loaded_at",
            ),
            args.output_project, "curated.dim_diagnosis", staging_bucket,
        )
        write_rejected(rejected, args.output_project, staging_bucket, run_date)

        LOG.info("Pipeline completed successfully.")
        return 0

    except AssertionError as exc:
        LOG.error("DATA QUALITY FAILURE: %s", exc)
        return 2
    except Exception as exc:  # noqa: BLE001
        LOG.exception("Pipeline failed: %s", exc)
        return 1
    finally:
        if spark is not None:
            spark.stop()
            LOG.info("Spark session stopped.")


if __name__ == "__main__":
    sys.exit(main())
```

### Step 3 — Run it on Dataproc

```bash
gcloud dataproc clusters create claims-etl \
  --image-version=$IMAGE_VERSION \
  --region=us-central1 \
  --zone=us-central1-a \
  --master-machine-type=n1-standard-4 \
  --worker-machine-type=n1-standard-4 \
  --worker-count=3 \
  --max-idle=30m \
  --service-account=$SA_EMAIL \
  --metadata="spark-env=SPARK_VERSION=3.5" \
  --initialization-action=gs://acme-health-raw/init/setup-job-deps.sh
```

```bash
gcloud dataproc jobs submit pyspark gs://acme-health-jobs/job_healthcare.py \
  --cluster=claims-etl \
  --region=us-central1 \
  --service-account=$SA_EMAIL \
  --properties="spark.executor.instances=3,spark.executor.cores=2,spark.executor.memory=4g,spark.sql.shuffle.partitions=200" \
  -- --input-path=gs://acme-health-raw \
     --output-project=$PROJECT_ID \
     --run-date=2024-06-01
```

```bash
gcloud dataproc jobs stream --region=us-central1 <JOB_ID> 2>&1 | tee claims_run.log

gcloud dataproc clusters delete claims-etl --region=us-central1 --quiet
```

### Step 4 — Verify the results

```sql
-- Q1: provider spend for a day
SELECT
  provider_npi,
  provider_name,
  provider_type,
  claim_count,
  total_claim_amount,
  denied_claim_count,
  denial_rate
FROM `your-project-id`.mart.provider_spend
WHERE service_date = '2024-06-01'
ORDER BY total_claim_amount DESC
LIMIT 20;
```

```sql
-- Q3: providers with an unusual denial rate
SELECT
  provider_npi,
  provider_name,
  claim_count,
  denied_claim_count,
  ROUND(denial_rate, 4) AS denial_rate
FROM `your-project-id`.mart.provider_spend
WHERE service_date = '2024-06-01'
  AND claim_count >= 20
  AND denial_rate > 0.15
ORDER BY denial_rate DESC;
```

```sql
-- Q4: spend anomalies (the z-score flag)
SELECT
  service_date,
  provider_npi,
  provider_name,
  total_claim_amount,
  spend_30d_mean,
  spend_30d_stddev,
  spend_zscore,
  anomaly_direction
FROM `your-project-id`.mart.provider_spend
WHERE is_spend_anomaly
ORDER BY service_date DESC, spend_zscore DESC;
```

```sql
-- Q5: high-cost members, year to date
WITH member_spend AS (
  SELECT
    member_id,
    SUM(claim_amount) AS ytd_spend,
    COUNT(*)          AS claim_count,
    COUNT(DISTINCT provider_npi) AS provider_count
  FROM `your-project-id`.curated.fact_claims
  WHERE service_date BETWEEN '2024-01-01' AND '2024-06-01'
  GROUP BY member_id
)
SELECT member_id, ytd_spend, claim_count, provider_count
FROM member_spend
WHERE ytd_spend > 50000
ORDER BY ytd_spend DESC;
```

```sql
-- Q7: what was rejected, and why
SELECT
  reject_reason,
  COUNT(*) AS claims,
  MIN(service_date) AS earliest,
  MAX(service_date) AS latest
FROM `your-project-id`.quarantine.rejected_claims
WHERE run_date = '2024-06-01'
GROUP BY reject_reason
ORDER BY claims DESC;
```

```sql
-- The anomaly trend for one provider — a sparkline of daily spend
SELECT
  service_date,
  total_claim_amount,
  spend_30d_mean,
  ROUND(spend_zscore, 3) AS z,
  is_spend_anomaly
FROM `your-project-id`.mart.provider_spend
WHERE provider_npi = '10001'
  AND service_date BETWEEN '2024-05-01' AND '2024-06-01'
ORDER BY service_date;
```

### Step 5 — The one-liner that breaks things (deliberately)

Inject a bad claim and watch the pipeline quarantine it instead of publishing it:

```json
{"claim_id":"CLM-20240601-10001-9999","member_id":"MBR-0000001","provider_npi":"10001","service_date":"2099-01-01","submitted_at":"2024-06-02T05:00:00Z","claim_amount":99999999.00,"diagnosis_codes":[{"code":"NOT_A_CODE","is_primary":true}],"service_lines":[],"denial":null}
```

Expected result: the claim lands in `quarantine.rejected_claims` with
`reject_reason = "FUTURE_SERVICE_DATE; AMOUNT_ABOVE_MAXIMUM"` and the
`NOT_A_CODE` diagnosis adds `MALFORMED_ICD10_CODE`. The fact table is unchanged, and the
job **succeeds** — because quarantine is not a failure, it is the pipeline working correctly.

⚠️ **A rejected claim is a business event, not a job failure.** The pipeline should succeed
and publish the rejection count. Failing the whole job because 3 of 50,000 claims were
invalid means one bad provider stops every other provider's claims from being paid. **Fail
the job on an invariant violation; quarantine the data for a content problem.** These are
different failure modes and conflating them is a serious operational mistake.

---

## 🔧 Handling sensitive data

### CMEK — Customer-Managed Encryption Keys

```bash
# 1. Create a KMS key ring and key
gcloud kms keyrings create claims-keyring --location=us-central1 --project=$PROJECT_ID
gcloud kms keys create claims-data-key \
  --location=us-central1 \
  --keyring=claims-keyring \
  --purpose=encryption \
  --project=$PROJECT_ID

# 2. Grant the service account permission to USE the key (not admin)
gcloud kms keys add-iam-policy-binding \
  gs://acme-health-raw \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/cloudkms.cryptoKeyEncrypterDecrypter" \
  --project=$PROJECT_ID
```

```bash
# 3. Create the bucket with CMEK
gcloud storage buckets create gs://acme-health-raw \
  --location=us-central1 \
  --project=$PROJECT_ID \
  --default-encryption-key="projects/$PROJECT_ID/locations/us-central1/keyRings/claims-keyring/cryptoKeys/claims-data-key"

# 4. BigQuery dataset with CMEK
bq mk --project_id=$PROJECT_ID \
  --default_kms_key_name="projects/$PROJECT_ID/locations/us-central1/keyRings/claims-keyring/cryptoKeys/claims-data-key" \
  curated
```

💡 **Why CMEK over Google-managed keys.** With CMEK, *you* control the key's IAM policy and
its lifecycle. You can revoke the key — which makes the data permanently unreadable, even
to Google. That is the property you need for incident response: "we no longer have the
right to read this data" becomes a real, enforceable statement rather than a policy
document.

⚠️ **CMEK is a second line of defence, not the first.** The first line is that the data is
never exposed to an unnecessary principal. A CMEK key whose IAM policy grants decrypt to
50 engineers is not protecting anything.

### Never write PII to logs

```python
# ❌ WRONG — member_id goes to Cloud Logging
LOG.info("Rejected claim %s for member %s: %s", claim_id, member_id, reason)
```

```python
# ✅ RIGHT — counts and business identifiers only
LOG.info("Rejected %d claims for provider_npi=%s on %s: %s",
         rejected_n, provider_npi, run_date, reason)
```

⚠️ **Cloud Logging has a long retention and a different access model than BigQuery.** A
member id written to stdout is now in a log sink, a log bucket, a log explorer, and every
exported log archive. A member id written to BigQuery is in a table with its own IAM
policy. **These are not the same security boundary.**

The rule: **logs carry counts, identifiers that are not person-identifying, and error
classes.** Anything that could identify a person goes in a table, with the table's access
policy, and nowhere else.

💡 **A useful pattern: hash the member id for log correlation.** If you need to correlate
log lines to a specific member without exposing the member id, log a salted hash:

```python
F.sha2(F.concat_ws("|", F.lit(run_date.isoformat()), F.col("member_id")), 256)
```

The log line is correlatable within a run, and the member id is not recoverable from it
without the salt.

### Dedicated service account and least privilege

```bash
# The Dataproc cluster itself runs as this identity. Keep it narrow.
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/dataproc.worker"          # create/delete clusters

# Per-dataset BigQuery access, not project-wide
bq add-iam-policy-binding \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/bigquery.dataEditor" \
  $PROJECT_ID:curated

bq add-iam-policy-binding \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/bigquery.dataEditor" \
  $PROJECT_ID:mart

bq add-iam-policy-binding \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/bigquery.dataEditor" \
  $PROJECT_ID:quarantine
```

💡 **Enable audit logging on BigQuery.** `roles/bigquery.auditor` plus Data Access audit
logs give you "who read this table, and when" — which is a specific HIPAA audit
requirement and which you cannot reconstruct after the fact.

### The compliance checklist

| Control | Implementation in this pipeline |
|---------|-------------------------------|
| Encryption at rest | CMEK on the bucket and the BigQuery datasets |
| Encryption in transit | TLS everywhere (GCS, BigQuery); no unencrypted endpoints |
| Least privilege | Dedicated service account, per-dataset BigQuery roles, per-bucket GCS roles |
| Access auditing | BigQuery Data Access audit logs; Cloud Audit Logs for GCS |
| Minimum necessary | No `dim_member`; no member PII columns in any table |
| Log hygiene | Counts and business ids only; no member ids, no names |
| Integrity | SHA-256 `claim_id` uniqueness assertion; row-count reconciliation on every run |
| Retention | `expiration_timestamp` on every table; quarantine expires in 2 years, facts in 7 |
| Breach response | CMEK revocation is a real, enforceable kill switch |
| Vendor agreement | A BAA with the cloud provider is a prerequisite, not a code change |

---

## 🔑 Key Takeaways

- **Compliance shapes the architecture.** "Minimum necessary" means you never ingest a column you do not need — a field you never parse cannot leak.
- **Use synthetic data for learning and for CI.** This chapter's data is generated. Real claim data requires a BAA, CMEK, scoped service accounts, and audit logging before a single line of this code runs.
- **Never log PII.** Log counts, business identifiers, and error classes. Cloud Logging is a different security boundary from BigQuery with a longer retention.
- **An array of structs needs `explode`; JSON-in-a-string needs `from_json` first.** These are different problems: `from_json` with an explicit `StructType` turns the string into a struct; `explode` then flattens a real array into rows.
- **Use `F.expr("try_cast(...)")` for all conversions** — the SQL function is guaranteed in Spark 3.5, the Python wrapper is not. There is **no `try_to_date`** in 3.5; use `try_cast(col AS DATE)`.
- **In `F.expr`, double-quote the outer string literal** when the format pattern contains single quotes (`"try_to_timestamp(c, \"yyyy-MM-dd'T'HH:mm:ss'Z'\")"`). Single-quoting the outer literal breaks the SQL parser.
- **`F.concat_ws` returns an empty string, not null, when every argument is null.** Wrap conditional-reason builders in `F.nullif(..., F.lit(""))` or your `.isNull()` check silently rejects every row.
- **Quarantine, never silently drop.** A rejected claim goes to `quarantine.rejected_claims` with a reason, and the job still succeeds. Content problems and invariant violations are different failure modes.
- **Explode changes your row count.** One claim with three diagnosis codes becomes three rows. Track counts at every stage or the reconciliation will lie to you.
- **A rolling z-score is a window with an explicit frame.** `rowsBetween(-29, 0)` over `partitionBy("provider_npi").orderBy("service_date")` gives a 30-day baseline including today; `rowsBetween(-30, -1)` excludes it.
- **Guard the division.** `stddev = 0` (a provider with identical spend every day) makes the z-score infinite. The `stddev > 0` check turns that into a null instead of an error or a false positive.
- **Broadcast the small reference tables.** `dim_provider` and `dim_diagnosis` are tiny; broadcasting them removes a fact-table shuffle entirely.
- **Assert the invariants.** `accepted + rejected == parsed`, one row per `claim_id`, no orphan providers, and fact-vs-mart reconciliation are cheap checks that catch real bugs.
- **Always `spark.stop()` in a `finally` block**, and return a distinct exit code for quality failure so the orchestrator can page the right team.

---

## 📚 Practice Exercises

1. **Handle both denial encodings.** Some providers send `"denial": {...}` (a JSON object) and
   some send `"denial": "{\"code\": \"CO-16\"}"` (a JSON string). With an explicit
   `StructType`, both arrive as a `string` column. Write the parsing logic that handles
   both forms — including a form where the string contains an *array* of denials — and
   prove it with a test DataFrame containing all three shapes. Explain why
   `mode("FAILFAST")` would break on the string-encoded form.

2. **Tune the anomaly detector.** The 30-day z-score with a threshold of 3.0 will
   false-positive on a provider whose business genuinely grew. Implement a **robust**
   alternative using the median and the interquartile range instead of the mean and
   standard deviation (Spark exposes `percentile_approx`), and compare the two
   detectors against a synthetic provider with a gradual ramp. Explain which one you
   would actually deploy to a fraud unit, and why.

3. **Build the high-cost member feed.** Implement Q5 as a *streaming-safe* daily output: a
   `mart.member_spend_ytd` table that accumulates year-to-date spend per member. It must
   be idempotent when re-run for the same date, must not double count, and must not store
   member PII. Write the BigQuery SQL that produces the daily incremental table and the
   Spark logic that feeds it.

4. **Prove the leak-free design.** Write a test that scans every column of every table the
   job writes and asserts that no column name matches a PHI pattern
   (`name`, `dob`, `ssn`, `address`, `phone`, `email`). Then deliberately add a
   `member_name` field to the source JSON and show that the pipeline drops it at the parse
   boundary rather than loading it. Explain why "drop it later" is not equivalent to
   "never parse it".

---

## 📖 Further Reading

- HIPAA Security Rule overview — https://www.hhs.gov/hipaa/for-professionals/security/index.html
- Google Cloud HIPAA compliance and BAA — https://cloud.google.com/security/compliance/hipaa
- BigQuery DDL reference — https://cloud.google.com/bigquery/docs/reference/standard-sql/data-definition-language
- BigQuery partition and cluster requirements — https://cloud.google.com/bigquery/docs/partitioned-tables
- Reading JSON with a schema in Spark — https://archive.apache.org/dist/spark/docs/3.5.3/sql-ref-datatypes.html
- Spark SQL built-in functions (Spark 3.5) — https://archive.apache.org/dist/spark/docs/3.5.3/sql-ref-functions-builtin.html
- Spark window functions — https://archive.apache.org/dist/spark/docs/3.5.3/api/python/reference/pyspark.sql/window.html
- Cloud KMS for Cloud Storage — https://cloud.google.com/kms/docs/cmek
- BigQuery audit logging — https://cloud.google.com/bigquery/docs/reference/auditlogs
- Dataproc job submission (`pyspark`) — https://cloud.google.com/sdk/gcloud/reference/dataproc/jobs/submit/pyspark
- Dataproc image versions — https://cloud.google.com/dataproc/docs/concepts/versioning
- Dataproc serverless (optional, for bursty workloads) — https://cloud.google.com/dataproc-serverless/docs/concepts/overview
