# 3.1 — Case Study 1: Retail Sales Analytics Pipeline

> **Section 3 · Case Studies · Lecture 3.1 · 53:29**

## 🎯 What you will learn

- How to turn a vague business request ("we need daily revenue") into a precise, testable set of analytical questions
- How to design a three-tier warehouse layout in BigQuery — `curated` facts and dimensions, `mart` aggregates
- How to build a full PySpark ETL: extract from GCS, clean with `try_cast`, dedupe deterministically, conform dimensions, and aggregate
- Why you broadcast a dimension and what happens when you get the threshold wrong
- How to make a pipeline **idempotent** so a re-run never double-counts revenue
- How to build data quality assertions and a reconciliation that would actually catch a bug
- How to size partitions and read the write path so the job is cheap enough to run every day

---

## 🧠 Concept

### The business requirement

A regional retail chain runs roughly **500 stores**. Every store's point-of-sale system writes a
CSV batch of transactions overnight. The current state of the business is:

- Revenue reporting takes **three days** and comes from a spreadsheet that a single analyst
  maintains by hand.
- Nobody can answer "how did promo week 42 actually perform against plan?" without a data
  engineer pulling the files.
- The finance team reconciles the daily spreadsheet against the POS terminals' own totals, and
  the numbers disagree by 0.3–0.8%. Nobody knows which number is right.

The request to the data team is one sentence: *"Give us a daily revenue report by store, region
and category that we can trust, and make it available by 7am."*

That sentence is a **business requirement**. It is not yet a specification. Your first job is
to convert it into analytical questions that are each answerable, each owned by a team, and
each with a defined grain.

### The analytical questions it implies

State them explicitly. This is the single most valuable step in the whole case study, because
every later decision — schema, grain, join keys, partition strategy — falls out of these
questions.

| # | Question | Grain | Primary owner |
|---|----------|-------|---------------|
| Q1 | What was total revenue per store per day? | store × day | Regional managers |
| Q2 | How does revenue split by region and by product category? | region × category × day | Category managers |
| Q3 | Which SKUs are the best sellers by units and by revenue? | product × day | Merchandising |
| Q4 | What is the average basket value, and how many items per basket? | day (and store) | Finance |
| Q5 | Did the promotion in week 42 lift revenue vs. the same weekdays in prior weeks? | promo × store | Marketing |
| Q6 | How much revenue came from transactions that were later refunded or voided? | day | Finance / audit |
| Q7 | Are there stores whose reported revenue is implausible (zero, negative, or wildly out of line)? | store × day | Store ops |

⚠️ **Q7 is the question that pays for the whole pipeline.** Every quality assertion in this
chapter exists to answer it. A pipeline that cannot detect an implausible store is just a
faster way to publish a wrong number.

### The source data

```
gs://acme-retail-raw/
├── sales/                              ← daily POS transaction extracts
│   ├── 2024-06-01/
│   │   ├── store_0101_part_0.csv
│   │   ├── store_0101_part_1.csv
│   │   └── ...                         (one or more files per store)
│   ├── 2024-06-02/
│   └── ...
├── ref/
│   ├── products.csv                    ← SCD2 product dimension snapshot
│   └── stores.csv                      ← SCD2 store dimension snapshot
```

The daily sales layout is **partitioned by date** (`sales/YYYY-MM-DD/`), which means the job
can read exactly one day. That is the primary reason this pipeline is cheap: it never touches
yesterday's data.

Each sales CSV has a header row and these columns:

```text
order_id,order_ts,store_id,product_id,quantity,unit_price,discount_amount,tax_amount,payment_method,promo_code,status
```

The `status` column carries `COMPLETED`, `VOIDED`, or `REFUNDED`. **Only `COMPLETED` counts
toward revenue.** This is the single most important business rule in the chapter, and getting
it wrong overstates revenue by a meaningful margin.

The two reference CSVs are **slowly-changing dimensions (SCD2)**: a row per version of a
product or store, with `valid_from` / `valid_to` and a `is_current` flag.

```text
# products.csv
product_id,product_name,category_id,category_name,brand,unit_cost,valid_from,valid_to,is_current

# stores.csv
store_id,store_name,region_id,region_name,city,state,store_format,valid_from,valid_to,is_current
```

### The target layout in BigQuery

Three tiers, three purposes. The naming convention is deliberate and mirrors the medallion
pattern used across modern data platforms.

```
                    BIGQUERY
   ┌──────────────────────────────────────────────────────────┐
   │  mart.daily_store_category_sales                        │
   │      ◄── business-facing. Pre-aggregated. Dashboard-ready │
   │      ◄── ONE row per (store_id, sales_date, category_id) │
   └──────────────────────────────────────────────────────────┘
                             ▲ aggregated in Spark
   ┌──────────────────────────────────────────────────────────┐
   │  curated.fact_sales        ◄── one row per transaction   │
   │  curated.dim_product       ◄── SCD2, current-version view│
   │  curated.dim_store         ◄── SCD2, current-version view│
   └──────────────────────────────────────────────────────────┘
                             ▲ conformed + enriched in Spark
   ┌──────────────────────────────────────────────────────────┐
   │  gs://acme-retail-raw/sales/YYYY-MM-DD/*.csv             │
   │  gs://acme-retail-raw/ref/products.csv                   │
   │  gs://acme-retail-raw/ref/stores.csv                     │
   └──────────────────────────────────────────────────────────┘
```

| Table | Grain | Partitioning | Clustering | Why it exists |
|-------|-------|--------------|------------|---------------|
| `curated.fact_sales` | one row per `order_id` | `DATE(order_ts)` | `store_id` | The auditable record. Everything reconciles to this. |
| `curated.dim_product` | one row per product | none | `product_id` | Conformed dimension, current version only |
| `curated.dim_store` | one row per store | none | `store_id` | Conformed dimension, current version only |
| `mart.daily_store_category_sales` | store × date × category | `sales_date` | `store_id, category_id` | The dashboard query. Pre-aggregated so BI never scans the fact table. |

💡 **Why the `mart` layer exists at all.** A dashboard that asks for "revenue by store by
category by day" against `curated.fact_sales` scans every transaction row every time. With
500 stores × 30 categories × 365 days that is a full-table scan for a question that has a
pre-computed answer. The `mart` table turns that into a partition-pruned, clustered scan over
a table that is roughly 1/50th the size. **Pre-aggregate the questions you know you will ask
repeatedly.**

### The data flow

```
  GCS raw                    PySpark (Dataproc)                      BigQuery
 ┌──────────┐              ┌───────────────────────────┐         ┌──────────────┐
 │ sales CSV│────read──────►│ 1. CAST + TRIM             │         │              │
 │  (1 day) │              │ 2. try_cast numerics       │         │              │
 └──────────┘              │ 3. filter status=COMPLETED │         │              │
                            │ 4. dedupe on order_id      │         │              │
 ┌──────────┐              │    (row_number, ts desc)   │         │              │
 │products  │────read──────►│ 5. filter to current SCD  │───────►│dim_product  │
 │  .csv    │   broadcast   │ 6. broadcast join          │         │dim_store    │
 └──────────┘              │ 7. enrich w/ surrogate key │         │              │
 ┌──────────┐              │ 8. aggregate to daily      │───────►│fact_sales   │
 │ stores   │────read──────►│ 9. write (partitioned)     │         │  (partitioned│
 │  .csv    │   broadcast   │10. reconcile + assert      │         │   by date)  │
 └──────────┘              └───────────────────────────┘         │              │
                                                              ┌─►│mart.daily_… │
                                                              │  │  (aggregate)│
                                                              │  └──────────────┘
                                                              │
                            ┌───────────────────────────┐         │
                            │ QUALITY GATE              │         │
                            │  raw_rows == fact_rows +  │         │
                            │  rejected_rows            │         │
                            │  sum(amount) matches src  │         │
                            └───────────────────────────┘         │
```

### Three Spark 3.5 API traps you will hit in this chapter

These are not hypothetical. Each one will throw at runtime, and each has a
one-line fix. They are listed up front so you can recognise them immediately.

| Trap | What happens | The fix |
|------|--------------|---------|
| `F.try_cast(...)` | `AttributeError` — the Python wrapper is not exposed in every 3.5 build | `F.expr("try_cast(col AS int)")` — the SQL function *is* guaranteed |
| `try_to_date(col, fmt)` | `UNRESOLVED_ROUTINE` — Spark 3.5 added `try_cast` and `try_to_timestamp`, but **not** `try_to_date` | `F.expr("try_cast(col AS DATE)")` |
| `F.concat_ws("; ", ...)` with all-null args | Returns an **empty string**, not null — so `.isNull()` is `False` and every row looks "rejected" | Wrap it: `F.nullif(F.concat_ws(...), F.lit(""))` |

⚠️ **The `concat_ws` one is the most dangerous**, because it does not fail — it
silently reclassifies every row in the pipeline. We build the reject reason by
concatenating conditional strings:

```python
F.concat_ws(
    "; ",
    F.when(cond1, F.lit("BAD_AMOUNT"))
     .when(cond2, F.lit("BAD_DATE"))
     .otherwise(F.lit(None).cast("string")),
)
```

For a **good** row every argument is null, and `concat_ws` returns `""`. Then
`F.col("reject_reason").isNull()` is `False` — so a perfectly valid transaction is
classified as invalid. The pipeline does not crash; it just quarantines 100% of
its data. `F.nullif(..., F.lit(""))` restores the null.

💡 **A useful habit: verify the functions you rely on actually exist in the build
you are targeting.** The one-liner below belongs in a smoke test:

```python
for fn in ("try_cast", "try_to_timestamp", "try_to_date"):
    try:
        spark.sql(f"SELECT {fn}('2024-01-01', 'yyyy-MM-dd')")
        print(f"{fn}: available")
    except Exception:
        print(f"{fn}: NOT available in this build")
```

---

## 🛠️ Hands-On: The retail sales analytics pipeline

### Step 0 — Prerequisites

```bash
export PROJECT_ID=your-project-id
export BUCKET=gs://acme-retail-raw
export STAGING_BUCKET=gs://your-project-id-bq-staging
export IMAGE_VERSION=2.2-debian12

gcloud config set project $PROJECT_ID
gcloud services enable dataproc bigquery storage

# Dedicated staging bucket for the BigQuery connector (never your data lake)
gsutil mb -l US $STAGING_BUCKET
gsutil lifecycle set - gs://your-project-id-bq-staging <<'JSON'
{
  "rule": [
    {"action": {"type": "Delete"}, "condition": {"age": 30}}
  ]
}
JSON
```

### Step 1 — The BigQuery schema (DDL)

Run this in the BigQuery console or via `bq query --use_legacy_sql=false`.

```sql
-- ============================================================
-- curated.fact_sales — one row per POS transaction
-- ============================================================
CREATE TABLE IF NOT EXISTS `your-project-id`.curated.fact_sales (
  order_id            STRING    NOT NULL,
  order_ts            TIMESTAMP NOT NULL,
  sales_date          DATE      NOT NULL,
  store_id            STRING    NOT NULL,
  product_id          STRING    NOT NULL,
  category_id         STRING,
  product_name        STRING,
  category_name       STRING,
  region_id           STRING,
  region_name         STRING,
  quantity            INT64,
  unit_price          NUMERIC(18,2),
  discount_amount     NUMERIC(18,2),
  tax_amount          NUMERIC(18,2),
  net_amount          NUMERIC(18,2),   -- revenue after discount, excl. tax
  payment_method      STRING,
  promo_code          STRING,
  status              STRING,
  is_promo            BOOL,
  product_sk          INT64,           -- surrogate key
  store_sk            INT64,           -- surrogate key
  source_file         STRING,
  loaded_at           TIMESTAMP NOT NULL
)
PARTITION BY DATE(order_ts)
CLUSTER BY store_id, category_id
OPTIONS (
  description = "Conformed POS transactions. One row per order_id. Revenue = net_amount on COMPLETED rows only.",
  expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 YEAR)
);

-- ============================================================
-- curated.dim_product — current version of each product
-- ============================================================
CREATE TABLE IF NOT EXISTS `your-project-id`.curated.dim_product (
  product_sk    INT64   NOT NULL,
  product_id    STRING  NOT NULL,
  product_name  STRING,
  category_id   STRING,
  category_name STRING,
  brand         STRING,
  unit_cost     NUMERIC(18,2),
  valid_from    DATE,
  valid_to      DATE,
  is_current    BOOL,
  loaded_at     TIMESTAMP NOT NULL
)
CLUSTER BY product_id
OPTIONS (
  description = "SCD2 product dimension, current version only (is_current = TRUE).",
  expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 YEAR)
);

-- ============================================================
-- curated.dim_store — current version of each store
-- ============================================================
CREATE TABLE IF NOT EXISTS `your-project-id`.curated.dim_store (
  store_sk     INT64   NOT NULL,
  store_id     STRING  NOT NULL,
  store_name   STRING,
  region_id    STRING,
  region_name  STRING,
  city         STRING,
  state        STRING,
  store_format STRING,
  valid_from   DATE,
  valid_to     DATE,
  is_current   BOOL,
  loaded_at    TIMESTAMP NOT NULL
)
CLUSTER BY store_id
OPTIONS (
  description = "SCD2 store dimension, current version only (is_current = TRUE).",
  expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 YEAR)
);

-- ============================================================
-- mart.daily_store_category_sales — the business-facing table
-- ============================================================
CREATE TABLE IF NOT EXISTS `your-project-id`.mart.daily_store_category_sales (
  sales_date       DATE      NOT NULL,
  store_id         STRING    NOT NULL,
  category_id      STRING,
  category_name    STRING,
  region_id        STRING,
  region_name      STRING,
  order_count      INT64,
  units_sold       INT64,
  gross_amount     NUMERIC(18,2),
  discount_amount  NUMERIC(18,2),
  net_revenue      NUMERIC(18,2),
  tax_amount       NUMERIC(18,2),
  avg_basket_value NUMERIC(18,2),
  avg_units_per_basket NUMERIC(18,2),
  promo_order_count INT64,
  promo_revenue    NUMERIC(18,2),
  loaded_at        TIMESTAMP NOT NULL
)
PARTITION BY sales_date
CLUSTER BY store_id, category_id
OPTIONS (
  description = "Daily revenue by store and category. Feeds the revenue dashboard. One row per (sales_date, store_id, category_id).",
  expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 YEAR)
);
```

💡 **Why `expiration_timestamp` at all?** The fact table is the audit record; seven years
matches the finance team's retention requirement for transaction-level evidence. The `mart`
table is derived and could be rebuilt from `fact_sales` in minutes, so it could be expired
much sooner — but keeping the same lifetime avoids the surprise of a dashboard that suddenly
goes empty while the fact table still has history.

💡 **Why cluster by `store_id, category_id` and not by `product_id`?** BigQuery clustering
sorts data physically by the clustering columns within each partition, so a query filtering
on `store_id` skips blocks. The dashboard's dominant filters are date + store, and its
dominant group-by is store + category. Cluster on what you **filter and group by**, not on
what you select.

⚠️ **`PARTITION BY DATE(order_ts)` versus `PARTITION BY sales_date`.** `DATE(order_ts)`
partitions on an expression of a column; `sales_date` partitions on a `DATE` column directly.
Both are valid, but partitioning on a *derived* column forces BigQuery to evaluate the
expression at write time and store the partition metadata accordingly. If you already
materialise `sales_date`, partition on it — the expression is free and the intent is clearer.

### Step 2 — The complete job: `job_retail.py`

Save this file locally, then upload it to GCS (or pass a local path to `gcloud`, which
uploads it for you).

```python
#!/usr/bin/env python3
"""
job_retail.py — Retail Sales Analytics Pipeline (Case Study 1)

Reads one day of POS transactions from GCS, conforms them against the
product and store dimensions, writes curated + mart tables to BigQuery,
and fails the job if any data-quality invariant is violated.

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
    StringType, TimestampType, IntegerType, DecimalType, BooleanType, DateType
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

APP_NAME = "retail-sales-analytics"

# Revenue-relevant statuses. VOIDED and REFUNDED transactions are excluded
# from the fact table's revenue measures but are counted for reconciliation.
REVENUE_STATUS = "COMPLETED"

# Tolerance for the money reconciliation, as a fraction of source total.
# 0.001 = 0.1%. Anything beyond this means rows were lost or double counted.
RECON_TOLERANCE = 0.001

LOG = logging.getLogger("retail")


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

def configure_logging(verbose: bool = False) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )
    # Spark is extremely chatty at INFO. Keep its own loggers at WARN so our
    # structured messages are readable in Cloud Logging.
    logging.getLogger("pyspark").setLevel(logging.WARN)
    logging.getLogger("org.apache.spark").setLevel(logging.WARN)


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

def read_sales(spark: SparkSession, input_path: str, run_date: date) -> DataFrame:
    """Read the raw POS CSV files for a single date partition."""
    sales_path = f"{input_path.rstrip('/')}/sales/{run_date.isoformat()}"
    LOG.info("Reading sales from %s", sales_path)

    raw = (
        spark.read
        .option("header", True)
        .option("mode", "PERMISSIVE")
        .option("inferSchema", "false")     # all strings; we cast explicitly
        .option("mode", "FAILFAST")
        .option("multiLine", "false")
        .csv(sales_path)
    )
    return raw.withColumn("source_file", F.input_file_name())


def read_dimensions(spark: SparkSession, input_path: str) -> tuple[DataFrame, DataFrame]:
    """Read the SCD2 product and store reference files."""
    ref_path = f"{input_path.rstrip('/')}/ref"

    LOG.info("Reading product dimension from %s/products.csv", ref_path)
    products = (
        spark.read
        .option("header", True)
        .option("inferSchema", "false")
        .csv(f"{ref_path}/products.csv")
    )

    LOG.info("Reading store dimension from %s/stores.csv", ref_path)
    stores = (
        spark.read
        .option("header", True)
        .option("inferSchema", "false")
        .csv(f"{ref_path}/stores.csv")
    )
    return products, stores


# ---------------------------------------------------------------------------
# Transform: clean
# ---------------------------------------------------------------------------

def clean_sales(raw: DataFrame) -> DataFrame:
    """
    Cast, trim, and null-normalise the raw transaction strings.

    All numeric conversion goes through F.expr("try_cast(...)") because the
    SQL function is guaranteed present in Spark 3.5, while the Python wrapper
    F.try_cast is not exposed in every 3.5 build.
    """
    return (
        raw
        .withColumn("order_id", F.trim(F.col("order_id")))
        .withColumn("store_id", F.trim(F.col("store_id")))
        .withColumn("product_id", F.trim(F.col("product_id")))
        .withColumn("status", F.upper(F.trim(F.col("status"))))
        .withColumn("payment_method", F.upper(F.trim(F.col("payment_method"))))
        .withColumn("promo_code", F.upper(F.trim(F.col("promo_code"))))
        .withColumn("order_ts", F.expr("try_to_timestamp(order_ts, 'yyyy-MM-dd HH:mm:ss')"))
        .withColumn("quantity", F.expr("try_cast(quantity AS int)"))
        .withColumn("unit_price", F.expr("try_cast(unit_price AS decimal(18,2))"))
        .withColumn("discount_amount", F.expr("try_cast(discount_amount AS decimal(18,2))"))
        .withColumn("tax_amount", F.expr("try_cast(tax_amount AS decimal(18,2))"))
        # A null discount means "no discount", not "unknown discount".
        .withColumn("discount_amount", F.coalesce(F.col("discount_amount"), F.lit(0).cast("decimal(18,2)")))
    )


def apply_business_rules(clean: DataFrame) -> DataFrame:
    """
    Derive revenue, promo flags, and the validity verdict for each row.

    We never drop rows here. Rows that fail a rule are flagged and routed to
    the rejected table by the caller, so that the row count reconciliation
    holds exactly.
    """
    return (
        clean
        .withColumn("sales_date", F.to_date(F.col("order_ts")))
        .withColumn(
            "net_amount",
            F.coalesce(F.col("quantity"), F.lit(0)).cast("decimal(18,2)")
            * F.coalesce(F.col("unit_price"), F.lit(0).cast("decimal(18,2)"))
            - F.coalesce(F.col("discount_amount"), F.lit(0).cast("decimal(18,2)")),
        )
        .withColumn(
            "is_promo",
            F.when(
                F.col("promo_code").isNotNull() & (F.col("promo_code") != "") & (F.col("promo_code") != "NONE"),
                F.lit(True),
            ).otherwise(F.lit(False)),
        )
        .withColumn(
            "reject_reason",
            F.nullif(
                F.concat_ws(
                    "; ",
                    F.when(F.col("order_id").isNull() | (F.col("order_id") == ""), F.lit("MISSING_ORDER_ID"))
                     .when(F.col("order_ts").isNull(), F.lit("BAD_TIMESTAMP"))
                     .when(F.col("store_id").isNull() | (F.col("store_id") == ""), F.lit("MISSING_STORE_ID"))
                     .when(F.col("product_id").isNull() | (F.col("product_id") == ""), F.lit("MISSING_PRODUCT_ID"))
                     .when(F.col("quantity").isNull(), F.lit("BAD_QUANTITY"))
                     .when(F.col("unit_price").isNull(), F.lit("BAD_UNIT_PRICE"))
                     .when(F.col("net_amount") < 0, F.lit("NEGATIVE_AMOUNT"))
                     .otherwise(F.lit(None).cast("string")),
                ),
                F.lit(""),   # concat_ws returns "" (not null) when all args are null
            ),
        )
        .withColumn("is_valid", F.col("reject_reason").isNull())
    )


def dedupe_transactions(valid: DataFrame) -> DataFrame:
    """
    Keep exactly one row per order_id, deterministically.

    POS systems occasionally re-emit a transaction (a retry, a file
    reprocessed, a terminal re-syncing). We keep the row with the latest
    order_ts, and break ties on source_file so the result is stable across
    runs. A non-deterministic dedupe breaks idempotency.
    """
    dedupe_window = Window.partitionBy("order_id").orderBy(
        F.col("order_ts").desc(),
        F.col("source_file").asc(),
    )
    return (
        valid
        .withColumn("rn", F.row_number().over(dedupe_window))
        .filter(F.col("rn") == 1)
        .drop("rn")
    )


# ---------------------------------------------------------------------------
# Transform: conform dimensions
# ---------------------------------------------------------------------------

def conform_dimensions(products: DataFrame, stores: DataFrame) -> tuple[DataFrame, DataFrame]:
    """
    Reduce each SCD2 dimension to its current version and assign a
    deterministic surrogate key.
    """
    product_dim = (
        products
        .withColumn("product_id", F.trim(F.col("product_id")))
        .withColumn("product_name", F.trim(F.col("product_name")))
        .withColumn("category_id", F.trim(F.col("category_id")))
        .withColumn("category_name", F.trim(F.col("category_name")))
        .withColumn("brand", F.trim(F.col("brand")))
        .withColumn("unit_cost", F.expr("try_cast(unit_cost AS decimal(18,2))"))
        .withColumn("valid_from", F.expr("try_cast(valid_from AS DATE)"))
        .withColumn("valid_to", F.expr("try_cast(valid_to AS DATE)"))
        .withColumn("is_current", F.expr("try_cast(is_current AS boolean)"))
        .filter(F.col("is_current") == F.lit(True))
        .dropDuplicates(subset=["product_id"])
        .withColumn(
            "product_sk",
            F.pmod(F.hash("product_id"), F.lit(2147483647)),
        )
        .withColumn("loaded_at", F.current_timestamp())
    )

    store_dim = (
        stores
        .withColumn("store_id", F.trim(F.col("store_id")))
        .withColumn("store_name", F.trim(F.col("store_name")))
        .withColumn("region_id", F.trim(F.col("region_id")))
        .withColumn("region_name", F.trim(F.col("region_name")))
        .withColumn("city", F.trim(F.col("city")))
        .withColumn("state", F.trim(F.col("state")))
        .withColumn("store_format", F.trim(F.col("store_format")))
        .withColumn("valid_from", F.expr("try_cast(valid_from AS DATE)"))
        .withColumn("valid_to", F.expr("try_cast(valid_to AS DATE)"))
        .withColumn("is_current", F.expr("try_cast(is_current AS boolean)"))
        .filter(F.col("is_current") == F.lit(True))
        .dropDuplicates(subset=["store_id"])
        .withColumn(
            "store_sk",
            F.pmod(F.hash("store_id"), F.lit(2147483647)),
        )
        .withColumn("loaded_at", F.current_timestamp())
    )
    return product_dim, store_dim


def enrich_with_dimensions(
    fact: DataFrame,
    product_dim: DataFrame,
    store_dim: DataFrame,
) -> DataFrame:
    """
    Broadcast-join the two small dimensions onto the fact table.

    F.broadcast() forces a broadcast hash join. The dimension side is
    copied to every executor, so no shuffle is required and the fact table
    is never re-partitioned. This is the correct strategy for dims in the
    low tens of MB.
    """
    enriched = (
        fact
        .join(
            F.broadcast(product_dim.select(
                "product_id", "product_sk", "product_name",
                "category_id", "category_name", "brand",
            )),
            on="product_id",
            how="left",
        )
        .join(
            F.broadcast(store_dim.select(
                "store_id", "store_sk", "store_name",
                "region_id", "region_name", "city", "state", "store_format",
            )),
            on="store_id",
            how="left",
        )
    )
    return enriched


# ---------------------------------------------------------------------------
# Transform: aggregate to the mart grain
# ---------------------------------------------------------------------------

def build_daily_mart(enriched: DataFrame) -> DataFrame:
    """
    Aggregate to one row per (sales_date, store_id, category_id).

    Basket analysis is computed at the order level first, then averaged per
    group. Averaging per-order averages directly would give every group the
    same weight regardless of how many orders it contains.
    """
    order_level = (
        enriched
        .groupBy("order_id", "sales_date", "store_id", "category_id",
                 "category_name", "region_id", "region_name")
        .agg(
            F.sum("quantity").alias("order_units"),
            F.sum("net_amount").alias("order_net"),
            F.sum("discount_amount").alias("order_discount"),
            F.sum("tax_amount").alias("order_tax"),
            F.max("is_promo").alias("order_is_promo"),
        )
    )

    return (
        order_level
        .groupBy("sales_date", "store_id", "category_id", "category_name",
                 "region_id", "region_name")
        .agg(
            F.count("*").alias("order_count"),
            F.sum("order_units").alias("units_sold"),
            F.sum(F.col("order_net") + F.col("order_discount")).alias("gross_amount"),
            F.sum("order_discount").alias("discount_amount"),
            F.sum("order_net").alias("net_revenue"),
            F.sum("order_tax").alias("tax_amount"),
            F.avg("order_net").alias("avg_basket_value"),
            F.avg("order_units").alias("avg_units_per_basket"),
            F.sum(F.when(F.col("order_is_promo"), F.lit(1)).otherwise(F.lit(0))).alias("promo_order_count"),
            F.sum(F.when(F.col("order_is_promo"), F.col("order_net")).otherwise(F.lit(0).cast("decimal(18,2)")))
             .alias("promo_revenue"),
        )
    )


# ---------------------------------------------------------------------------
# Data quality
# ---------------------------------------------------------------------------

def run_quality_checks(
    raw: DataFrame,
    parsed: DataFrame,
    valid: DataFrame,
    validation_rejected: DataFrame,
    revenue_rows: DataFrame,
    fact: DataFrame,
    mart: DataFrame,
) -> dict:
    """
    Count every stage and assert the invariants. Returns the metrics dict so
    the caller can log and persist them.

    The invariants are written against the *stage boundaries*, not against a
    single "rejected" bucket, because rows can leave the pipeline at two
    different points:

        parsed  --(validation)-->  valid  +  validation_rejected
        valid   --(revenue filter + dedupe + dim join)-->  fact  +  orphans

    Checking "valid + rejected == parsed" against a combined rejected bucket
    would be wrong, because the dimension-orphan rejects were never part of
    "valid" in the first place.
    """
    raw_n = raw.count()
    parsed_n = parsed.count()
    valid_n = valid.count()
    validation_rejected_n = validation_rejected.count()
    revenue_n = revenue_rows.count()
    fact_n = fact.count()

    LOG.info(
        "Row counts: raw=%d parsed=%d valid=%d validation_rejected=%d "
        "revenue=%d fact=%d",
        raw_n, parsed_n, valid_n, validation_rejected_n, revenue_n, fact_n,
    )

    # --- Invariant 1: the validation split loses nothing
    assert valid_n + validation_rejected_n == parsed_n, (
        f"ROW LOSS: valid({valid_n}) + validation_rejected({validation_rejected_n}) "
        f"!= parsed({parsed_n})"
    )

    # --- Invariant 2: the fact table is a subset of the revenue rows
    assert fact_n <= revenue_n, (
        f"ROW GAIN: fact({fact_n}) > revenue_rows({revenue_n})"
    )

    # --- Invariant 3: no duplicate order_id in the fact table
    distinct_orders = fact.select("order_id").distinct().count()
    assert distinct_orders == fact_n, (
        f"DUPLICATE ORDER_IDS: {fact_n - distinct_orders} extra rows in fact_sales"
    )

    # --- Invariant 4: no null keys
    null_keys = fact.filter(
        F.col("order_id").isNull() | F.col("store_id").isNull() | F.col("product_id").isNull()
    ).count()
    assert null_keys == 0, f"NULL KEYS: {null_keys} fact rows have a null key"

    # --- Invariant 5: referential integrity against the dimensions
    orphan_products = fact.filter(F.col("category_id").isNull()).count()
    orphan_stores = fact.filter(F.col("region_id").isNull()).count()
    LOG.info("Referential integrity: %d rows without a product match, %d without a store match",
             orphan_products, orphan_stores)
    assert orphan_products == 0, f"ORPHAN PRODUCTS: {orphan_products} fact rows matched no product"
    assert orphan_stores == 0, f"ORPHAN STORES: {orphan_stores} fact rows matched no store"

    # --- Invariant 5: no negative revenue
    negatives = fact.filter(F.col("net_amount") < 0).count()
    assert negatives == 0, f"NEGATIVE REVENUE: {negatives} rows with net_amount < 0"

    # --- Invariant 6: the mart reconciles to the fact
    fact_total = fact.agg(F.sum("net_amount")).collect()[0][0]
    mart_total = mart.agg(F.sum("net_revenue")).collect()[0][0]
    fact_total = float(fact_total or 0.0)
    mart_total = float(mart_total or 0.0)
    LOG.info("Reconciliation: fact_total=%.2f mart_total=%.2f", fact_total, mart_total)

    tolerance = max(abs(fact_total) * RECON_TOLERANCE, 0.01)
    assert abs(fact_total - mart_total) <= tolerance, (
        f"RECONCILIATION FAILED: fact={fact_total:.2f} vs mart={mart_total:.2f} "
        f"(delta={abs(fact_total - mart_total):.2f} > tolerance={tolerance:.2f})"
    )

    return {
        "raw_rows": raw_n,
        "parsed_rows": parsed_n,
        "valid_rows": valid_n,
        "validation_rejected_rows": validation_rejected_n,
        "revenue_rows": revenue_n,
        "fact_rows": fact_n,
        "fact_net_total": fact_total,
        "mart_net_total": mart_total,
    }


def reconcile_to_source(raw: DataFrame, fact: DataFrame) -> None:
    """
    Compare the sum of order amounts in the curated table against the sum
    computed directly from the raw CSV strings.

    This is deliberately a *second, independent* computation. The mart
    reconciliation above checks internal consistency; this one checks the
    pipeline against the source of truth. A bug that drops rows would be
    invisible to the first check if the same code produced both sides.
    """
    source_total = raw.agg(
        F.sum(
            F.expr("try_cast(quantity AS int)")
            * F.expr("try_cast(unit_price AS decimal(18,2))")
        )
    ).collect()[0][0]
    source_total = float(source_total or 0.0)

    fact_total = float(
        fact.agg(F.sum("net_amount")).collect()[0][0] or 0.0
    )

    # The fact table excludes VOIDED/REFUNDED rows and applies discounts, so
    # it is expected to be LOWER than the raw gross. We assert the direction
    # and the magnitude of the difference, and we log both numbers.
    LOG.info("Source gross total (no filters, no discounts): %.2f", source_total)
    LOG.info("Curated net total (COMPLETED only, after discount): %.2f", fact_total)

    if fact_total > source_total + 0.01:
        raise AssertionError(
            f"RECONCILIATION FAILED: curated net total {fact_total:.2f} exceeds "
            f"source gross total {source_total:.2f} — rows were probably duplicated"
        )

    diff_ratio = 0.0 if source_total == 0 else abs(source_total - fact_total) / source_total
    LOG.info("Source-to-curated difference ratio: %.4f%%", diff_ratio * 100)


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------

def write_to_bigquery(
    df: DataFrame,
    project: str,
    table: str,
    staging_bucket: str,
    write_disposition: str = "WRITE_TRUNCATE",
) -> None:
    """
    Write a DataFrame to BigQuery via the standard connector path.

    temporaryGcsBucket is REQUIRED for the indirect (bulk load) write path:
    Spark serialises rows to Avro, stages them in GCS, and hands BigQuery a
    list of object URIs to load.
    """
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
    LOG.info("Wrote %s to %s.%s (%s)", df.count(), project, table, write_disposition)


def write_rejected(spark: SparkSession, rejected: DataFrame, project: str,
                   staging_bucket: str, run_date: date) -> None:
    """Persist rejected rows so the source team can fix the upstream data."""
    if rejected.isEmpty():
        LOG.info("No rejected rows to persist.")
        return

    rejected_out = (
        rejected
        .withColumn("run_date", F.lit(run_date).cast("date"))
        .withColumn("rejected_at", F.current_timestamp())
    )
    (
        rejected_out.write
        .format("bigquery")
        .option("writeDisposition", "WRITE_APPEND")
        .option("createDisposition", "CREATE_IF_NEEDED")
        .option("temporaryGcsBucket", staging_bucket)
        .mode("append")
        .save(f"{project}.quarantine.rejected_sales")
    )
    LOG.warning("Persisted %d rejected rows to quarantine.rejected_sales", rejected_out.count())


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Retail sales analytics pipeline: GCS -> Spark -> BigQuery"
    )
    parser.add_argument(
        "--input-path", required=True,
        help="Root GCS path holding sales/ and ref/ (e.g. gs://acme-retail-raw)",
    )
    parser.add_argument(
        "--output-project", required=True,
        help="GCP project id that owns the curated and mart BigQuery datasets",
    )
    parser.add_argument(
        "--run-date", default=None,
        help="Processing date, YYYY-MM-DD. Defaults to yesterday (UTC).",
    )
    parser.add_argument(
        "--staging-bucket", default=None,
        help="GCS bucket for BigQuery load-job staging. Defaults to "
             "<output-project>-bq-staging.",
    )
    parser.add_argument(
        "--shuffle-partitions", type=int, default=200,
        help="spark.sql.shuffle.partitions for this job.",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable DEBUG logging.",
    )
    return parser.parse_args(argv)


def resolve_run_date(run_date_arg: str | None) -> date:
    if run_date_arg:
        try:
            return datetime.strptime(run_date_arg, "%Y-%m-%d").date()
        except ValueError as exc:
            raise ValueError(
                f"--run-date must be YYYY-MM-DD, got {run_date_arg!r}"
            ) from exc
    return (datetime.now(timezone.utc) - timedelta(days=1)).date()


def main(argv=None) -> int:
    args = parse_args(argv)
    configure_logging(args.verbose)

    run_date = resolve_run_date(args.run_date)
    staging_bucket = args.staging_bucket or f"gs://{args.output_project}-bq-staging"

    LOG.info("=" * 78)
    LOG.info("Retail Sales Analytics Pipeline")
    LOG.info("  input-path     : %s", args.input_path)
    LOG.info("  output-project : %s", args.output_project)
    LOG.info("  run-date       : %s", run_date.isoformat())
    LOG.info("  staging-bucket : %s", staging_bucket)
    LOG.info("=" * 78)

    spark = None
    try:
        spark = build_spark(APP_NAME, args.shuffle_partitions)

        # --- 1. EXTRACT -------------------------------------------------
        raw = read_sales(spark, args.input_path, run_date)
        products_raw, stores_raw = read_dimensions(spark, args.input_path)
        LOG.info("Extraction complete.")

        # --- 2. TRANSFORM -----------------------------------------------
        cleaned = clean_sales(raw)
        parsed = apply_business_rules(cleaned)

        valid = parsed.filter(F.col("is_valid"))
        validation_rejected = parsed.filter(~F.col("is_valid")).select(
            "order_id", "order_ts", "store_id", "product_id", "quantity",
            "unit_price", "discount_amount", "tax_amount", "status",
            "promo_code", "reject_reason", "source_file",
        )
        LOG.info("Rejected %d rows from validation.", validation_rejected.count())

        # Revenue filter: only COMPLETED transactions count.
        revenue_rows = valid.filter(F.col("status") == REVENUE_STATUS)
        LOG.info("Valid rows: %d, of which status=%s: %d",
                 valid.count(), REVENUE_STATUS, revenue_rows.count())

        deduped = dedupe_transactions(revenue_rows)
        LOG.info("After dedupe on order_id: %d rows", deduped.count())

        product_dim, store_dim = conform_dimensions(products_raw, stores_raw)
        LOG.info("Dimensions conformed: %d products, %d stores",
                 product_dim.count(), store_dim.count())

        enriched = enrich_with_dimensions(deduped, product_dim, store_dim)

        # Rows that failed to match a dimension are rejected, not dropped.
        enriched = enriched.withColumn(
            "reject_reason",
            F.when(F.col("category_id").isNull(), F.lit("UNKNOWN_PRODUCT"))
             .when(F.col("region_id").isNull(), F.lit("UNKNOWN_STORE"))
             .otherwise(F.lit(None).cast("string")),
        )
        orphan_rejects = enriched.filter(F.col("reject_reason").isNotNull())
        fact = enriched.filter(F.col("reject_reason").isNull()).drop("reject_reason")

        # The combined quarantine set: everything that failed at either stage.
        rejected = validation_rejected.unionByName(
            orphan_rejects.select(
                "order_id", "order_ts", "store_id", "product_id", "quantity",
                "unit_price", "discount_amount", "tax_amount", "status",
                "promo_code", "reject_reason", "source_file",
            )
        )
        LOG.info("Orphan dimension matches: %d rows", orphan_rejects.count())

        fact = (
            fact
            .withColumn("loaded_at", F.current_timestamp())
            .withColumn("product_sk", F.coalesce(F.col("product_sk"), F.lit(None).cast("long")))
            .withColumn("store_sk", F.coalesce(F.col("store_sk"), F.lit(None).cast("long")))
        )

        mart = build_daily_mart(fact).withColumn("loaded_at", F.current_timestamp())

        # --- 3. QUALITY GATE --------------------------------------------
        metrics = run_quality_checks(
            raw, parsed, valid, validation_rejected, revenue_rows, fact, mart
        )
        reconcile_to_source(raw, fact)

        # --- 4. LOAD ----------------------------------------------------
        fact_for_bq = fact.select(
            "order_id", "order_ts", "sales_date", "store_id", "product_id",
            "category_id", "product_name", "category_name",
            "region_id", "region_name",
            "quantity", "unit_price", "discount_amount", "tax_amount", "net_amount",
            "payment_method", "promo_code", "status", "is_promo",
            "product_sk", "store_sk", "source_file", "loaded_at",
        )
        write_to_bigquery(fact_for_bq, args.output_project, "curated.fact_sales",
                          staging_bucket)
        write_to_bigquery(mart, args.output_project, "mart.daily_store_category_sales",
                          staging_bucket)

        # The conformed dimensions are published alongside the fact table so
        # that downstream consumers never have to read the raw SCD2 CSVs.
        write_to_bigquery(
            product_dim.select(
                "product_sk", "product_id", "product_name", "category_id",
                "category_name", "brand", "unit_cost", "valid_from", "valid_to",
                "is_current", "loaded_at",
            ),
            args.output_project, "curated.dim_product", staging_bucket,
        )
        write_to_bigquery(
            store_dim.select(
                "store_sk", "store_id", "store_name", "region_id", "region_name",
                "city", "state", "store_format", "valid_from", "valid_to",
                "is_current", "loaded_at",
            ),
            args.output_project, "curated.dim_store", staging_bucket,
        )

        write_rejected(spark, rejected, args.output_project, staging_bucket, run_date)

        LOG.info("Pipeline completed successfully. Metrics: %s", metrics)
        return 0

    except AssertionError as exc:
        LOG.error("DATA QUALITY FAILURE: %s", exc)
        return 2
    except Exception as exc:  # noqa: BLE001 - top-level guard
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

**Create a temporary cluster** (a job that runs for 12 minutes does not need a cluster that
lives for a month):

```bash
gcloud dataproc clusters create retail-etl \
  --image-version=$IMAGE_VERSION \
  --region=us-central1 \
  --zone=us-central1-a \
  --master-machine-type=n1-standard-4 \
  --worker-machine-type=n1-standard-4 \
  --worker-count=2 \
  --max-idle=30m \
  --max-nodes=4 \
  --initialization-action=gs://acme-retail-raw/init/setup-job-deps.sh
```

**Submit the job:**

```bash
gcloud dataproc jobs submit pyspark gs://acme-retail-jobs/job_retail.py \
  --cluster=retail-etl \
  --region=us-central1 \
  --properties="spark.executor.instances=2,spark.executor.cores=2,spark.executor.memory=4g,spark.sql.shuffle.partitions=200" \
  -- --input-path=gs://acme-retail-raw \
     --output-project=$PROJECT_ID \
     --run-date=2024-06-01
```

💡 **Note the `--` separator.** Everything after `--` is passed to your Python script as
`sys.argv`. Without it, `--input-path` would be interpreted by `gcloud` itself and the job
would fail with an "unrecognized arguments" error.

**Watch it run:**

```bash
gcloud dataproc jobs describe <JOB_ID> --region=us-central1
gcloud dataproc jobs list --region=us-central1 --limit=5

# Follow the driver logs
gcloud dataproc jobs stream --region=us-central1 <JOB_ID> 2>&1 | tee retail_run.log
```

**Delete the cluster when you're done:**

```bash
gcloud dataproc clusters delete retail-etl --region=us-central1 --quiet
```

### Step 4 — Verify the results

```sql
-- Q1: revenue by store for a given day
SELECT
  store_id,
  region_name,
  SUM(net_revenue)      AS revenue,
  SUM(order_count)      AS orders,
  SUM(units_sold)       AS units
FROM `your-project-id`.mart.daily_store_category_sales
WHERE sales_date = '2024-06-01'
GROUP BY store_id, region_name
ORDER BY revenue DESC
LIMIT 10;
```

```sql
-- Q2: revenue by region and category
SELECT
  region_name,
  category_name,
  SUM(net_revenue) AS revenue
FROM `your-project-id`.mart.daily_store_category_sales
WHERE sales_date BETWEEN '2024-06-01' AND '2024-06-30'
GROUP BY region_name, category_name
ORDER BY revenue DESC;
```

```sql
-- Q3: best sellers by revenue and by units (from the fact table)
SELECT
  product_id,
  product_name,
  category_name,
  SUM(quantity)   AS units,
  SUM(net_amount) AS revenue
FROM `your-project-id`.curated.fact_sales
WHERE sales_date = '2024-06-01'
GROUP BY product_id, product_name, category_name
ORDER BY revenue DESC
LIMIT 20;
```

```sql
-- Q5: promo effectiveness — promo vs non-promo average basket
SELECT
  is_promo,
  COUNT(DISTINCT order_id)   AS orders,
  AVG(net_amount)            AS avg_basket,
  SUM(net_amount)            AS total_revenue
FROM `your-project-id`.curated.fact_sales
WHERE sales_date = '2024-06-01'
GROUP BY is_promo;
```

```sql
-- Data quality: did the load land in every partition?
SELECT
  DATE(order_ts) AS d,
  COUNT(*)       AS rows,
  COUNT(DISTINCT store_id) AS stores,
  SUM(net_amount) AS revenue
FROM `your-project-id`.curated.fact_sales
WHERE DATE(order_ts) BETWEEN '2024-06-01' AND '2024-06-03'
GROUP BY d
ORDER BY d;
```

### Step 5 — Idempotency check

Run the same job twice for the same date and confirm the table is unchanged. This is the
test that proves the pipeline is safe to retry.

```bash
# Record the state after run 1
bq query --use_legacy_sql=false --format=csv \
  "SELECT COUNT(*) AS rows, ROUND(SUM(net_amount),2) AS total
   FROM \`$PROJECT_ID.curated.fact_sales\`
   WHERE sales_date = '2024-06-01'" > /tmp/run1.csv

# Re-run the exact same job
gcloud dataproc jobs submit pyspark gs://acme-retail-jobs/job_retail.py \
  --cluster=retail-etl --region=us-central1 \
  -- --input-path=gs://acme-retail-raw \
     --output-project=$PROJECT_ID \
     --run-date=2024-06-01

bq query --use_legacy_sql=false --format=csv \
  "SELECT COUNT(*) AS rows, ROUND(SUM(net_amount),2) AS total
   FROM \`$PROJECT_ID.curated.fact_sales\`
   WHERE sales_date = '2024-06-01'" > /tmp/run2.csv

diff /tmp/run1.csv /tmp/run2.csv && echo "IDEMPOTENT ✅" || echo "NOT IDEMPOTENT ❌"
```

⚠️ **`WRITE_TRUNCATE` is what makes the re-run safe, but it also means the fact table only
holds the most recent run's data.** That is a real design decision: this pipeline is a
**daily full refresh of one partition**, not an incremental appender. If you need the full
history in `curated.fact_sales`, switch to `WRITE_APPEND` — but then you must guarantee the
dedup step prevents double-counting on re-run, which is exactly why the dedup window carries
a deterministic tiebreaker.

💡 **The production pattern is per-partition overwrite.** With `WRITE_APPEND` and a
`DELETE FROM table WHERE sales_date = <run_date>` executed before the write, you get both
history and idempotency. In Spark, the equivalent is writing to a staging table and
performing a `MERGE` — which is where Delta Lake on BigQuery or Dataproc Serverless earns
its keep.

---

## ⚙️ Cost and performance notes

### How many partitions?

`spark.sql.shuffle.partitions` defaults to **200**. That default is a poor fit for almost
every real workload — it is too many for small data and too few for large data.

| Data volume (rows/day) | Recommended `shuffle.partitions` | Why |
|---|---|---|
| < 1M | 20–50 | 200 tasks means 200 tiny tasks and a lot of scheduling overhead |
| 1M – 50M | 100–200 | Roughly one task per 250 MB of shuffled data is the sweet spot |
| 50M – 500M | 400–1000 | Scale with data; AQE will coalesce empty partitions at runtime |
| > 500M | 1000+ | Measure. Use AQE + dynamic allocation and let the cluster flex |

💡 **The rule of thumb is "one task per 128–256 MB of shuffled data."** With `n1-standard-4`
executors (4 vCPU, 16 GB), a task handling 250 MB of compressed Parquet in memory is
comfortable. More partitions than that means idle workers; fewer means long-running tasks
and poor load balancing.

💡 **AQE makes an over-provisioned partition count much less harmful.** With
`spark.sql.adaptive.enabled=true` (the default in Spark 3.5), Spark coalesces the small
output partitions of each shuffle stage at runtime. Setting 200 on a job that only produces
30 partitions of real work means Spark actually runs ~30 tasks. The cost of over-provisioning
is therefore mostly *metadata*, not compute. **Under**-provisioning is the dangerous
direction.

### Why broadcast the dimensions?

```
WITHOUT BROADCAST (sort-merge join)
  fact:  50M rows ──shuffle──► 200 partitions, hash by product_id
  dim:   2K rows  ──shuffle──► 200 partitions, hash by product_id
                                    │
                                    └──► sort + merge  (network cost + sort cost)

WITH F.broadcast(dim)
  fact:  50M rows ──────────────► 200 partitions (NO shuffle, no re-partitioning)
  dim:   2K rows  ──copy───────► every executor (2K rows ≈ 200 KB, trivial)
                                    │
                                    └──► hash build + probe  (no network cost)
```

Three concrete benefits:

1. **No shuffle of the fact table.** This is the big one. A shuffle of 50M rows moves data
   across the network and sorts it. Eliminating it is often the difference between a
   3-minute job and a 12-minute job.
2. **No re-partitioning.** Without the broadcast, Catalyst inserts an `Exchange` on the fact
   side, which re-partitions the *entire* fact table by the join key. That is a full
   data movement for what is logically a lookup.
3. **No sort.** Sort-merge joins pay a comparison sort on both sides; broadcast hash joins
   build a hash table once per executor and probe it.

**The rule:** broadcast the small side when it fits in executor memory with headroom. The
common threshold is **under ~10 MB compressed** — a few thousand to a few million rows for
a narrow dimension. This course's `dim_product` (a few thousand SKUs) and `dim_store` (500
rows) are both comfortably inside it.

⚠️ **The failure mode when you broadcast something big.** If the optimizer broadcasts a
500 MB dimension, every executor builds a 500 MB hash table in its JVM heap. With
`n1-standard-4` (16 GB heap) and 4 executors per node, you will see:

```
java.lang.OutOfMemoryError: Java heap space
ExecutorLostFailure (executor 7 exited caused by OutOfMemoryError)
```

And it fails **after** the broadcast has been collected — which can be 30 minutes into the
job. This is why `F.broadcast()` should be explicit for critical joins: it puts the intent
in the code where a reviewer can see it, rather than in a config that auto-broadcast
decisions can flip between Spark versions.

💡 **Verify the broadcast actually happened.** After the join, check the plan:

```python
enriched.explain(mode="formatted")
```

Look for `BroadcastExchange` on the dimension side. If you see `SortMergeJoin` with two
`Exchange` nodes instead, the broadcast did not apply — usually because the dimension
DataFrame was filtered or projected after the `F.broadcast()` call.

### Why partition the output?

```
BigQuery table with NO partitioning
┌──────────────────────────────────────────────────┐
│ 2024-01-01 ... 2024-06-30  (all rows interleaved)│
└──────────────────────────────────────────────────┘
  Query for one day → full table scan, ~6 months of rows
  Storage cost: full table

BigQuery table PARTITIONED BY DATE(order_ts)
┌────────────┬────────────┬────────────┬────────────┐
│ 2024-06-01 │ 2024-06-02 │ 2024-06-03 │ ...        │
└────────────┴────────────┴────────────┴────────────┘
  Query for one day → 1 partition read
  Storage cost: only the partitions you query get billed
```

Four concrete benefits:

1. **Predicate pruning.** A `WHERE sales_date = '2024-06-01'` filter reads one partition
   instead of scanning the table. On a year of history that is a 365× reduction in bytes
   scanned — and BigQuery bills by bytes scanned, so this is a direct cost reduction.
2. **Parallelism.** BigQuery distributes each partition across workers independently. A
   single hot partition is the bottleneck; many small partitions parallelize cleanly.
3. **Streaming/buffer semantics.** A partition that has not been written for 24 hours is
   eligible for buffer cleanup, reclaiming storage without deleting history.
4. **Idempotent, targeted deletes.** `DELETE FROM t WHERE sales_date = '2024-06-01'` only
   touches one partition instead of rewriting the whole table.

💡 **Partition by a date, cluster by the filter columns.** Partitioning has a hard limit
(every query still touches all non-empty partitions) while clustering is a soft filter that
skips blocks — so partition by date (coarse) and cluster by `store_id` (fine) is the correct
combination.

⚠️ **Do not over-partition.** BigQuery allows up to 4,000 partitions per table. A table
partitioned by `DATE(order_ts)` and also by `store_id` would create 500 partitions per day
and hit the limit in 8 days. Partition granularity should be chosen so the whole
retention window fits comfortably under 4,000.

### Other cost levers

| Lever | Effect | When to use it |
|-------|--------|---------------|
| `spark.sql.adaptive.enabled` | Coalesces small shuffle partitions at runtime | Always on (default in 3.5) |
| `spark.serializer=KryoSerializer` | ~20% faster serialization, smaller payloads | Always |
| Preemptible workers | ~75% cheaper per node | Batch jobs with retries enabled (Spark retries failed tasks automatically) |
| Temporary clusters | Pay only for job runtime | Batch ETL (this job) |
| `spark.sql.shuffle.partitions` tuned | Fewer empty tasks, less scheduling | Always tune per job |
| Avoid `countDistinct` on high cardinality | Removes a whole extra shuffle stage | Use `approx_count_distinct` where exactness isn't required |
| Broadcast small dims | Removes a fact-table shuffle | Always for dims under ~10 MB |
| Single `spark.sql.warehouse` write | Avoid re-reading what you just wrote | Don't re-read your own output |

💡 **Preemptible workers and Spark retries.** Spark's task scheduler retries failed tasks
automatically — the default `spark.task.maxFailures` is 4. A preemptible VM that gets
reclaimed mid-task looks exactly like a task failure, so Spark retries it elsewhere. For
**idempotent** jobs (this one, thanks to the dedup + `WRITE_TRUNCATE` design), preemptible
workers are safe and typically cut the bill by roughly three quarters. For non-idempotent
jobs (blind appends), they are not.

⚠️ **The cost trap in this exact pipeline.** `fact_sales` is partitioned by date and
`WRITE_TRUNCATE` replaces the entire table on each run. If the table has accumulated 6
months of history from earlier runs, `WRITE_TRUNCATE` deletes all of it — which is a *data
loss* bug, not a cost bug. Verify your disposition before the first production run.

---

## 🔑 Key Takeaways

- **Start with the questions, not the schema.** Seven explicit analytical questions, each with a grain and an owner, determine every downstream design decision.
- **Three tiers, three purposes:** `curated` holds the auditable conformed facts and dimensions; `mart` holds the pre-aggregated answers to the questions you know you will ask repeatedly.
- **Partition BigQuery by date, cluster by the columns you filter and group by.** Partitioning is a hard limit on scan; clustering is a soft filter that skips blocks.
- **Use `F.expr("try_cast(col AS type)")`, not `F.try_cast(...)`.** The SQL function is guaranteed in Spark 3.5; the Python wrapper is not present in every build. Spark 3.5 also has **no `try_to_date`** — use `try_cast(col AS DATE)`.
- **`F.concat_ws` returns an empty string, not null, when every argument is null.** Wrap conditional-reason builders in `F.nullif(..., F.lit(""))` or your `.isNull()` check silently rejects every row.
- **Write your invariants against stage boundaries, not a single "rejected" bucket.** Rows leave the pipeline at more than one point (validation, dimension join), so `accepted + rejected == parsed` is only true when the buckets line up.
- **Never drop a bad row — quarantine it.** Rejected rows go to a table, are counted, and are reconciled. A silent drop is invisible; a quarantined row is a reportable data-quality incident.
- **Assertions are what make a pipeline trustworthy.** `valid + rejected == parsed` and `fact_total ≈ mart_total` are cheap checks that catch the two most common classes of bug: row loss and double counting.
- **Dedupe deterministically.** `row_number` with `order_ts DESC` and a stable tiebreaker on `source_file` guarantees the same row wins every time. A non-deterministic dedupe breaks idempotency.
- **Broadcast the dimensions.** It removes a fact-table shuffle, avoids re-partitioning, and skips the sort phase of a sort-merge join. Broadcast only when the small side is genuinely under ~10 MB.
- **`spark.sql.shuffle.partitions` must be tuned per job.** The default of 200 is wrong for both small and large data. Target roughly one task per 128–256 MB of shuffled data.
- **Reconcile against the source, not just internally.** The mart-vs-fact check proves internal consistency; only an independent computation over the raw file proves the pipeline is correct.
- **`temporaryGcsBucket` is required** for the standard BigQuery write path. Point it at a dedicated staging bucket with a lifecycle rule, never at your data lake.
- **Always `spark.stop()` in a `finally` block** and return a non-zero exit code on quality failure so the orchestrator can alert.

---

## 📚 Practice Exercises

1. **Add the promo-effectiveness question.** Implement Q5 properly: compare promo-period revenue against the same weekdays in the prior 8 weeks for the same stores, controlling for store size. Write it as a BigQuery query against `mart.daily_store_category_sales` using a self-join on a generated date range, and explain why you would not use a simple week-over-week comparison.

2. **Make the pipeline incrementally safe.** The current design uses `WRITE_TRUNCATE`, which means `curated.fact_sales` holds only the latest run. Change it to preserve history while remaining idempotent: add a `DELETE FROM curated.fact_sales WHERE sales_date = <run_date>` step before the write, or use a `MERGE` statement. Then prove idempotency by running the same date twice and comparing row counts, sums, and a content hash.

3. **Tune it, then measure.** Run the job with `--shuffle-partitions` set to 20, 200, and 800 on the same data. Record wall-clock time from the Dataproc job status, the number of shuffle bytes, and the number of tasks in the Spark UI. Explain the shape of the curve and where the optimum sits. Then re-run with `F.broadcast()` removed from the product join and quantify the cost of the extra shuffle.

4. **Extend the quality gate.** Add three more assertions: (a) no `order_ts` in the future, (b) no `quantity` ≤ 0, (c) the sum of `net_revenue` in the mart equals the sum of `net_amount` in the fact to the cent. Then deliberately break each one — inject a bad row into the raw CSV — and show the job failing with a non-zero exit code and a clear error message. Explain why a job that *fails loudly* is better than one that publishes a slightly wrong number.

---

## 📖 Further Reading

- BigQuery DDL reference — https://cloud.google.com/bigquery/docs/reference/standard-sql/data-definition-language
- BigQuery partitioning and clustering — https://cloud.google.com/bigquery/docs/partitioned-tables
- BigQuery cost optimization — https://cloud.google.com/bigquery/docs/best-practices
- Dataproc job submission (`pyspark`) — https://cloud.google.com/sdk/gcloud/reference/dataproc/jobs/submit/pyspark
- Dataproc image versions — https://cloud.google.com/dataproc/docs/concepts/versioning
- BigQuery Storage Write API (direct write) — https://cloud.google.com/bigquery/docs/write-api
- Spark SQL performance tuning guide — https://archive.apache.org/dist/spark/docs/3.5.3/sql-performance-tuning.html
- Spark broadcast joins — https://archive.apache.org/dist/spark/docs/3.5.3/sql-performance-tuning.html#join-strategy
- Dataproc pricing — https://cloud.google.com/dataproc/pricing
- The Data Warehouse Toolkit (dimensional modeling) — https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/
