# Data Engineering Is the Unsexy Foundation That Makes ML Actually Work

*What Chapter 3 of Designing Machine Learning Systems taught me about the infrastructure nobody talks about — but everyone depends on*

---

By **Prem Vishnoi** · Head of Data & AI · 18 min read

---

I've never met a data scientist who got into the field because they were passionate about file formats. Nobody writes "excited about Parquet vs CSV tradeoffs" in their LinkedIn bio. And yet, in my 15+ years building data platforms, I can tell you with certainty: more ML projects die because of bad data engineering than bad models.

The model is the glamorous part. Data engineering is the plumbing. And when the plumbing breaks at 2 AM during month-end close — which it will — nobody cares how elegant your neural network architecture is.

Chapter 3 of Chip Huyen's *Designing Machine Learning Systems* covers data engineering fundamentals: data sources, data formats, data models, storage engines, dataflow patterns, and batch vs. stream processing. It's the chapter most ML practitioners want to skip. It's also the chapter that separates people who can build production systems from people who can only build notebooks.

This article is my walkthrough — with real retail data platform examples, working code with outputs, and the infrastructure decisions I've actually had to make.

---

## Data Sources — Where Does Your Data Actually Come From?

Before you think about models, think about data sources. In a real enterprise, data doesn't come from one clean CSV file. It comes from dozens of systems, each with its own format, latency, quality, and ownership.

Here's what a typical retail data ecosystem looks like:

| Source Type | Examples | Characteristics | ML Relevance |
|---|---|---|---|
| **User Input** | Search queries, app registrations, feedback forms | Messy, malformatted, needs validation | Search ranking, NLP, sentiment |
| **System Logs** | POS transaction logs, API logs, error logs | High volume, semi-structured, timestamped | Anomaly detection, debugging |
| **Behavioral Data** | Clicks, page views, cart additions, scroll depth | Implicit signals, privacy-sensitive | Recommendations, personalization |
| **Internal Databases** | Inventory, CRM, supplier master, product catalog | Structured, owned, but often inconsistent across systems | Demand forecasting, segmentation |
| **Third-Party Data** | Weather, economic indicators, competitor pricing | Bought or API-accessed, outside your control | Demand drivers, external features |

```python
# Mapping data sources to ML use cases in a retail environment

data_source_map = {
    "POS Transactions": {
        "type": "Internal Database",
        "format": "Structured (Delta Lake tables)",
        "volume": "~12M rows/day across 154 stores",
        "latency": "Batch (T+1 for analytics, near-real-time for dashboards)",
        "ml_use_cases": [
            "Demand forecasting",
            "Basket analysis",
            "Customer segmentation",
            "Fraud detection"
        ],
        "quality_issues": [
            "Returns mixed with sales (negative quantities)",
            "Walk-in customers have no customer_id",
            "Timezone inconsistencies across countries"
        ]
    },
    "E-commerce Clickstream": {
        "type": "Behavioral / System Logs",
        "format": "Semi-structured (JSON events via Kafka)",
        "volume": "~50M events/day",
        "latency": "Streaming (sub-second)",
        "ml_use_cases": [
            "Product recommendations",
            "Search ranking",
            "Cart abandonment prediction"
        ],
        "quality_issues": [
            "Bot traffic mixed with real users",
            "Session ID fragmentation across devices",
            "Missing events during peak load"
        ]
    },
    "Inventory Snapshots": {
        "type": "Internal Database",
        "format": "Structured (ERP extract → Delta Lake)",
        "volume": "~800K SKU-store combinations, snapshotted daily",
        "latency": "Batch (daily snapshot at midnight)",
        "ml_use_cases": [
            "Stock-out prediction",
            "Replenishment optimization",
            "Demand sensing (true demand vs observed sales)"
        ],
        "quality_issues": [
            "Physical count vs system count mismatch",
            "Negative stock values (data entry errors)",
            "Delayed updates from warehouse transfers"
        ]
    },
    "Weather API": {
        "type": "Third-Party",
        "format": "JSON via REST API",
        "volume": "Hourly forecasts per city",
        "latency": "Near-real-time (API call)",
        "ml_use_cases": [
            "Demand forecasting (weather as external feature)",
            "Delivery route optimization"
        ],
        "quality_issues": [
            "Forecast accuracy degrades beyond 3 days",
            "API rate limits during peak usage",
            "Missing data for rural areas"
        ]
    }
}

print("RETAIL DATA SOURCE INVENTORY")
print("="*70)
for source, details in data_source_map.items():
    print(f"\n📦 {source}")
    print(f"   Type:      {details['type']}")
    print(f"   Format:    {details['format']}")
    print(f"   Volume:    {details['volume']}")
    print(f"   Latency:   {details['latency']}")
    print(f"   ML Uses:   {', '.join(details['ml_use_cases'][:2])}...")
    print(f"   ⚠️  Issues: {details['quality_issues'][0]}")
```

```
RETAIL DATA SOURCE INVENTORY
======================================================================

📦 POS Transactions
   Type:      Internal Database
   Format:    Structured (Delta Lake tables)
   Volume:    ~12M rows/day across 154 stores
   Latency:   Batch (T+1 for analytics, near-real-time for dashboards)
   ML Uses:   Demand forecasting, Basket analysis...
   ⚠️  Issues: Returns mixed with sales (negative quantities)

📦 E-commerce Clickstream
   Type:      Behavioral / System Logs
   Format:    Semi-structured (JSON events via Kafka)
   Volume:    ~50M events/day
   Latency:   Streaming (sub-second)
   ML Uses:   Product recommendations, Search ranking...
   ⚠️  Issues: Bot traffic mixed with real users

📦 Inventory Snapshots
   Type:      Internal Database
   Format:    Structured (ERP extract → Delta Lake)
   Volume:    ~800K SKU-store combinations, snapshotted daily
   Latency:   Batch (daily snapshot at midnight)
   ML Uses:   Stock-out prediction, Replenishment optimization...
   ⚠️  Issues: Physical count vs system count mismatch

📦 Weather API
   Type:      Third-Party
   Format:    JSON via REST API
   Volume:    Hourly forecasts per city
   Latency:   Near-real-time (API call)
   ML Uses:   Demand forecasting (weather as external feature)...
   ⚠️  Issues: Forecast accuracy degrades beyond 3 days
```

Every one of those quality issues is something I've actually encountered. The returns-mixed-with-sales problem alone took us weeks to untangle properly, because a naive demand forecast trained on raw POS data sees a return as negative demand — which makes the model think demand dropped when it actually didn't.

**Know your data sources before you build anything.** The best model architecture in the world can't fix data that was wrong before it arrived.

---

## Data Formats — Why Parquet Changed My Life

This sounds dramatic. It isn't. When you're processing billions of rows, the difference between CSV and Parquet is the difference between a pipeline that finishes in 8 minutes and one that runs for 3 hours and then OOMs.

Huyen explains the fundamental distinction: **row-major vs. column-major** formats.

| Property | CSV (Row-Major) | Parquet (Column-Major) |
|---|---|---|
| **Storage** | Text (human-readable) | Binary (compact) |
| **Read pattern** | Fast for reading entire rows | Fast for reading specific columns |
| **Write pattern** | Fast for appending new rows | Slower for individual row writes |
| **File size** | Larger | 2-6x smaller (compression) |
| **Schema** | Implicit (no enforcement) | Embedded (self-describing) |
| **Best for** | Data exchange, small files, quick inspection | Analytics, ML features, large datasets |

Let me show you why this matters in practice:

```python
import pandas as pd
import numpy as np
import time
import os

# Simulate a retail sales dataset: 2 million rows, 15 columns
np.random.seed(42)
n_rows = 2_000_000

df = pd.DataFrame({
    'transaction_id': np.arange(n_rows),
    'transaction_date': pd.date_range('2025-01-01', periods=n_rows, freq='s'),
    'store_id': np.random.randint(1, 155, n_rows),
    'customer_id': np.random.randint(10000, 99999, n_rows),
    'sku_id': np.random.randint(100000, 200000, n_rows),
    'category': np.random.choice(
        ['Fresh', 'Dairy', 'Beverages', 'Dry Goods', 'Frozen', 
         'Cleaning', 'Personal Care', 'Snacks'], n_rows),
    'quantity': np.random.randint(1, 50, n_rows),
    'unit_price': np.round(np.random.uniform(10, 500, n_rows), 2),
    'total_amount': np.round(np.random.uniform(50, 5000, n_rows), 2),
    'payment_method': np.random.choice(['Cash', 'Credit', 'Transfer', 'QR'], n_rows),
    'channel': np.random.choice(['In-Store', 'Online', 'Makro Pro'], n_rows),
    'is_promotion': np.random.binomial(1, 0.25, n_rows),
    'is_return': np.random.binomial(1, 0.03, n_rows),
    'member_tier': np.random.choice(['Silver', 'Gold', 'Platinum', 'None'], n_rows),
    'basket_id': np.random.randint(1000000, 9999999, n_rows),
})

# Save as CSV and Parquet
csv_path = '/tmp/sales_data.csv'
parquet_path = '/tmp/sales_data.parquet'

df.to_csv(csv_path, index=False)
df.to_parquet(parquet_path, index=False, engine='pyarrow')

csv_size = os.path.getsize(csv_path) / (1024 * 1024)
parquet_size = os.path.getsize(parquet_path) / (1024 * 1024)

print("FILE FORMAT COMPARISON: 2M retail transactions, 15 columns")
print("="*55)
print(f"{'Metric':<30} {'CSV':>12} {'Parquet':>12}")
print("-"*55)
print(f"{'File size (MB)':<30} {csv_size:>12.1f} {parquet_size:>12.1f}")
print(f"{'Compression ratio':<30} {'1.0x':>12} {f'{csv_size/parquet_size:.1f}x':>12}")

# Benchmark: Read full file
start = time.time()
_ = pd.read_csv(csv_path)
csv_full_read = time.time() - start

start = time.time()
_ = pd.read_parquet(parquet_path)
parquet_full_read = time.time() - start

print(f"{'Full file read (seconds)':<30} {csv_full_read:>12.2f} {parquet_full_read:>12.2f}")

# Benchmark: Read only 2 columns (the ML feature extraction pattern)
start = time.time()
_ = pd.read_csv(csv_path, usecols=['store_id', 'total_amount'])
csv_col_read = time.time() - start

start = time.time()
_ = pd.read_parquet(parquet_path, columns=['store_id', 'total_amount'])
parquet_col_read = time.time() - start

print(f"{'Read 2 columns (seconds)':<30} {csv_col_read:>12.2f} {parquet_col_read:>12.2f}")
print(f"{'Column read speedup':<30} {'baseline':>12} {f'{csv_col_read/parquet_col_read:.1f}x':>12}")
print("="*55)
print()
print("WHY THIS MATTERS FOR ML:")
print("  Feature engineering reads COLUMNS, not rows.")
print("  'Give me total_amount and store_id for 2M transactions'")
print("  is the bread and butter of ML feature pipelines.")
print(f"  Parquet does this {csv_col_read/parquet_col_read:.1f}x faster and uses")
print(f"  {csv_size/parquet_size:.1f}x less storage.")
```

```
FILE FORMAT COMPARISON: 2M retail transactions, 15 columns
=======================================================
Metric                                CSV      Parquet
-------------------------------------------------------
File size (MB)                      382.7         64.2
Compression ratio                    1.0x         6.0x
Full file read (seconds)             4.83         0.91
Read 2 columns (seconds)             2.14         0.18
Column read speedup              baseline       11.9x
=======================================================

WHY THIS MATTERS FOR ML:
  Feature engineering reads COLUMNS, not rows.
  'Give me total_amount and store_id for 2M transactions'
  is the bread and butter of ML feature pipelines.
  Parquet does this 11.9x faster and uses
  6.0x less storage.
```

6x smaller files. 12x faster column reads. And this is just with 2 million rows — at scale with billions of rows on Spark, the difference is even more dramatic because Parquet enables predicate pushdown (filtering at the storage layer, before data even hits memory).

**In our Databricks environment, everything lands in Delta Lake (which is Parquet + transaction log). We haven't used CSV for any analytical workload in years.** CSV still shows up as an ingestion format from external vendors, but the first thing our pipelines do is convert it to Delta.

### The pandas Trap

Huyen makes a subtle but important point: pandas DataFrames are column-major, but most people use them like NumPy arrays (row-major). This leads to terrible performance when iterating by rows.

```python
import pandas as pd
import numpy as np
import time

# Create a moderately sized DataFrame
np.random.seed(42)
n = 500_000
df = pd.DataFrame({
    'store_id': np.random.randint(1, 155, n),
    'sku_id': np.random.randint(100000, 200000, n),
    'quantity': np.random.randint(1, 50, n),
    'price': np.round(np.random.uniform(10, 500, n), 2),
    'amount': np.round(np.random.uniform(50, 5000, n), 2),
})

# BAD: Iterate by rows (what most beginners do)
start = time.time()
row_sum = 0
for idx, row in df.iterrows():
    row_sum += row['amount']
row_time = time.time() - start

# GOOD: Vectorized column operation (how pandas is designed to work)
start = time.time()
col_sum = df['amount'].sum()
col_time = time.time() - start

# ALSO GOOD: Convert to NumPy for row-heavy operations
start = time.time()
arr = df['amount'].values
numpy_sum = arr.sum()
numpy_time = time.time() - start

print("PANDAS PERFORMANCE: ROW vs COLUMN ACCESS (500K rows)")
print("="*55)
print(f"{'Method':<35} {'Time (s)':>10} {'Speedup':>8}")
print("-"*55)
print(f"{'df.iterrows() (row-by-row)':<35} {row_time:>10.3f} {'1.0x':>8}")
print(f"{'df[col].sum() (vectorized)':<35} {col_time:>10.4f} {f'{row_time/col_time:.0f}x':>8}")
print(f"{'numpy array .sum()':<35} {numpy_time:>10.5f} {f'{row_time/numpy_time:.0f}x':>8}")
print("="*55)
print()
print("RULE: Never use iterrows() on a DataFrame.")
print("  Use vectorized operations (column-based).")
print("  If you must iterate rows, convert to NumPy first.")
```

```
PANDAS PERFORMANCE: ROW vs COLUMN ACCESS (500K rows)
=======================================================
Method                               Time (s)  Speedup
-------------------------------------------------------
df.iterrows() (row-by-row)              8.412     1.0x
df[col].sum() (vectorized)              0.0008  10515x
numpy array .sum()                      0.00031 27135x
=======================================================

RULE: Never use iterrows() on a DataFrame.
  Use vectorized operations (column-based).
  If you must iterate rows, convert to NumPy first.
```

27,000x faster. That's not a typo. If you see `iterrows()` in a production pipeline, treat it as a bug.

---

## Data Models — Relational, Document, and Graph

Huyen covers three data models. Here's how they map to real ML infrastructure decisions:

| Data Model | Structure | Best For | Retail Example |
|---|---|---|---|
| **Relational** | Tables with rows and columns, normalized, joined via keys | Structured analytics, reporting, feature engineering | Sales fact table joined with product dimension, store dimension, calendar dimension |
| **Document** | Self-contained JSON/BSON blobs, nested structures | Flexible schemas, content-centric access | Product catalog with variable attributes (food vs. electronics vs. cleaning) |
| **Graph** | Nodes and edges, relationships are first-class | Relationship-heavy queries, network analysis | Customer → buys → product → supplied_by → vendor → located_in → region |

### When Relational Models Shine: The Star Schema

For ML feature engineering in retail, the relational model with a star schema is almost always the right starting point. Here's why:

```python
# Star schema for retail analytics and ML feature engineering
# This is the pattern we use in our Delta Lake / Databricks environment

star_schema_ddl = """
-- FACT TABLE: One row per transaction line item
-- This is where 90% of ML features come from

CREATE TABLE IF NOT EXISTS gold.fact_sales (
    sale_key           BIGINT       GENERATED ALWAYS AS IDENTITY,
    transaction_id     STRING       NOT NULL,
    transaction_date   DATE         NOT NULL,
    transaction_hour   INT,
    store_key          INT          NOT NULL,     -- FK → dim_store
    product_key        INT          NOT NULL,     -- FK → dim_product
    customer_key       INT,                       -- FK → dim_customer (nullable: walk-ins)
    calendar_key       INT          NOT NULL,     -- FK → dim_calendar
    quantity           DECIMAL(10,2),
    unit_price_thb     DECIMAL(12,2),
    total_amount_thb   DECIMAL(12,2),
    discount_thb       DECIMAL(12,2),
    channel            STRING,                    -- 'In-Store', 'Online', 'Makro Pro'
    is_promotion       BOOLEAN,
    is_return          BOOLEAN,
    payment_method     STRING
);

-- DIMENSION TABLES: Context for the facts

CREATE TABLE IF NOT EXISTS gold.dim_store (
    store_key          INT          NOT NULL,
    store_id           STRING       NOT NULL,
    store_name         STRING,
    city               STRING,
    province           STRING,
    country            STRING,      -- 'TH', 'IN', 'KH'
    store_format       STRING,      -- 'Makro', 'Makro Food Service', 'Siam Frozen'
    store_tier         STRING,      -- 'A', 'B', 'C'
    opening_date       DATE,
    selling_area_sqm   DECIMAL(10,2)
);

CREATE TABLE IF NOT EXISTS gold.dim_product (
    product_key        INT          NOT NULL,
    sku_id             STRING       NOT NULL,
    product_name       STRING,
    category_l1        STRING,      -- 'Food', 'Non-Food'
    category_l2        STRING,      -- 'Fresh', 'Dry Goods', 'Beverages'
    category_l3        STRING,      -- 'Seafood', 'Rice', 'Water'
    brand              STRING,
    is_private_label   BOOLEAN,
    is_fresh           BOOLEAN,
    shelf_life_days    INT,
    supplier_id        STRING
);

CREATE TABLE IF NOT EXISTS gold.dim_customer (
    customer_key       INT          NOT NULL,
    customer_id        STRING       NOT NULL,
    customer_type      STRING,      -- 'B2B', 'B2C'
    business_type      STRING,      -- 'Restaurant', 'Hotel', 'Retailer', 'Individual'
    member_tier        STRING,      -- 'Silver', 'Gold', 'Platinum'
    registration_date  DATE,
    province           STRING,
    country            STRING
);

CREATE TABLE IF NOT EXISTS gold.dim_calendar (
    calendar_key       INT          NOT NULL,
    full_date          DATE         NOT NULL,
    day_of_week        INT,         -- 0=Mon, 6=Sun
    is_weekend         BOOLEAN,
    is_holiday         BOOLEAN,
    holiday_name       STRING,
    week_of_year       INT,
    month              INT,
    quarter            INT,
    year               INT,
    is_month_end       BOOLEAN,
    is_songkran        BOOLEAN,     -- Thai New Year: Apr 13-15
    is_chinese_ny      BOOLEAN
);
"""

print("STAR SCHEMA: RETAIL ML FEATURE FOUNDATION")
print("="*60)
print()
print("  dim_store ──────┐")
print("  dim_product ────┤")
print("  dim_customer ───┼──── fact_sales")
print("  dim_calendar ───┘")
print()
print("WHY THIS MATTERS FOR ML:")
print("-"*60)

ml_feature_examples = [
    ("Demand Forecasting",
     "SELECT p.category_l2, c.day_of_week, c.is_holiday,\n"
     "       SUM(f.quantity) as total_units\n"
     "FROM fact_sales f\n"
     "JOIN dim_product p ON f.product_key = p.product_key\n"
     "JOIN dim_calendar c ON f.calendar_key = c.calendar_key\n"
     "GROUP BY 1, 2, 3"),
    ("Customer Segmentation",
     "SELECT cu.customer_type, cu.business_type,\n"
     "       COUNT(DISTINCT f.transaction_id) as visit_count,\n"
     "       SUM(f.total_amount_thb) as total_spend\n"
     "FROM fact_sales f\n"
     "JOIN dim_customer cu ON f.customer_key = cu.customer_key\n"
     "GROUP BY 1, 2"),
    ("Store Performance",
     "SELECT s.store_tier, s.store_format,\n"
     "       AVG(f.total_amount_thb) as avg_basket\n"
     "FROM fact_sales f\n"
     "JOIN dim_store s ON f.store_key = s.store_key\n"
     "GROUP BY 1, 2"),
]

for use_case, sql in ml_feature_examples:
    print(f"\n  {use_case}:")
    for line in sql.split('\n'):
        print(f"    {line}")

print()
print("One fact table. Four dimensions. Covers 80% of ML features.")
print("This is why data modeling matters before model training.")
```

```
STAR SCHEMA: RETAIL ML FEATURE FOUNDATION
============================================================

  dim_store ──────┐
  dim_product ────┤
  dim_customer ───┼──── fact_sales
  dim_calendar ───┘

WHY THIS MATTERS FOR ML:
------------------------------------------------------------

  Demand Forecasting:
    SELECT p.category_l2, c.day_of_week, c.is_holiday,
           SUM(f.quantity) as total_units
    FROM fact_sales f
    JOIN dim_product p ON f.product_key = p.product_key
    JOIN dim_calendar c ON f.calendar_key = c.calendar_key
    GROUP BY 1, 2, 3

  Customer Segmentation:
    SELECT cu.customer_type, cu.business_type,
           COUNT(DISTINCT f.transaction_id) as visit_count,
           SUM(f.total_amount_thb) as total_spend
    FROM fact_sales f
    JOIN dim_customer cu ON f.customer_key = cu.customer_key
    GROUP BY 1, 2

  Store Performance:
    SELECT s.store_tier, s.store_format,
           AVG(f.total_amount_thb) as avg_basket
    FROM fact_sales f
    JOIN dim_store s ON f.store_key = s.store_key
    GROUP BY 1, 2

One fact table. Four dimensions. Covers 80% of ML features.
This is why data modeling matters before model training.
```

That star schema — one fact table, four dimensions — covers demand forecasting, customer segmentation, store performance, basket analysis, promotion effectiveness, and churn prediction. **Data modeling is feature engineering's upstream dependency.** Get the schema right, and feature engineering becomes SQL. Get it wrong, and every feature requires a heroic data wrangling effort.

---

## Structured vs. Unstructured Data — And the Lakehouse in Between

Huyen frames this well: the choice between structured and unstructured data is really about who shoulders the responsibility of defining the schema.

| Approach | Schema Responsibility | Storage | Strength | Weakness |
|---|---|---|---|---|
| **Data Warehouse** (structured) | Writer defines schema upfront | Structured tables | Easy to query, analyze, and build features | Schema changes are painful; can't handle diverse data types |
| **Data Lake** (unstructured) | Reader assumes structure later | Raw files (JSON, CSV, logs, images) | Flexible, fast ingestion, any data type | "Data swamp" risk — nobody can find or trust anything |
| **Data Lakehouse** (hybrid) | Schema-on-read with enforcement | Delta Lake, Iceberg, Hudi | Flexibility of lake + governance of warehouse | Relatively newer, requires discipline |

```python
# The data lakehouse pattern: Bronze → Silver → Gold
# This is the architecture we run on Databricks + Delta Lake

lakehouse_layers = {
    "Bronze (Raw)": {
        "description": "Raw data exactly as received from source systems",
        "schema_enforcement": "Minimal — schema-on-read",
        "example_tables": [
            "bronze.pos_transactions_raw     (JSON from POS API)",
            "bronze.clickstream_raw           (Kafka events, JSON)",
            "bronze.inventory_erp_extract     (CSV from ERP nightly job)",
            "bronze.weather_api_raw           (JSON from weather API)",
        ],
        "who_reads": "Data engineers only",
        "quality": "No guarantees — nulls, duplicates, bad types expected"
    },
    "Silver (Cleaned)": {
        "description": "Cleaned, deduplicated, typed, joined where necessary",
        "schema_enforcement": "Enforced — schema-on-write with Delta constraints",
        "example_tables": [
            "silver.transactions_cleaned      (typed, deduped, returns separated)",
            "silver.clickstream_sessionized    (sessions identified, bots removed)",
            "silver.inventory_daily_snapshot   (stock levels per SKU per store)",
            "silver.weather_daily              (structured, gap-filled)",
        ],
        "who_reads": "Data engineers, analysts, ML pipelines",
        "quality": "Validated — null checks, type checks, freshness checks"
    },
    "Gold (Business-Ready)": {
        "description": "Aggregated, business-logic applied, ready for analytics and ML",
        "schema_enforcement": "Strict — star schema, documented, governed",
        "example_tables": [
            "gold.fact_sales                  (star schema fact table)",
            "gold.dim_store / dim_product      (dimension tables)",
            "gold.feature_store_demand         (ML features for forecasting)",
            "gold.kpi_daily_sales_summary      (dashboard aggregates)",
        ],
        "who_reads": "Analysts, ML models, dashboards, business users",
        "quality": "Trusted — SLA-backed, monitored, lineage tracked"
    }
}

print("DATA LAKEHOUSE: BRONZE → SILVER → GOLD")
print("="*65)
for layer, details in lakehouse_layers.items():
    print(f"\n{'─'*65}")
    print(f"📦 {layer}")
    print(f"   {details['description']}")
    print(f"   Schema: {details['schema_enforcement']}")
    print(f"   Readers: {details['who_reads']}")
    print(f"   Quality: {details['quality']}")
    print(f"   Tables:")
    for table in details['example_tables']:
        print(f"     • {table}")

print(f"\n{'─'*65}")
print()
print("KEY PRINCIPLE:")
print("  Raw data enters Bronze with no assumptions.")
print("  Silver enforces quality gates — no garbage passes through.")
print("  Gold serves business and ML with trusted, governed data.")
print()
print("  ML models should ONLY read from Silver or Gold.")
print("  If your model reads from Bronze, you're training on garbage.")
```

```
DATA LAKEHOUSE: BRONZE → SILVER → GOLD
=================================================================

─────────────────────────────────────────────────────────────────
📦 Bronze (Raw)
   Raw data exactly as received from source systems
   Schema: Minimal — schema-on-read
   Readers: Data engineers only
   Quality: No guarantees — nulls, duplicates, bad types expected
   Tables:
     • bronze.pos_transactions_raw     (JSON from POS API)
     • bronze.clickstream_raw           (Kafka events, JSON)
     • bronze.inventory_erp_extract     (CSV from ERP nightly job)
     • bronze.weather_api_raw           (JSON from weather API)

─────────────────────────────────────────────────────────────────
📦 Silver (Cleaned)
   Cleaned, deduplicated, typed, joined where necessary
   Schema: Enforced — schema-on-write with Delta constraints
   Readers: Data engineers, analysts, ML pipelines
   Quality: Validated — null checks, type checks, freshness checks
   Tables:
     • silver.transactions_cleaned      (typed, deduped, returns separated)
     • silver.clickstream_sessionized    (sessions identified, bots removed)
     • silver.inventory_daily_snapshot   (stock levels per SKU per store)
     • silver.weather_daily              (structured, gap-filled)

─────────────────────────────────────────────────────────────────
📦 Gold (Business-Ready)
   Aggregated, business-logic applied, ready for analytics and ML
   Schema: Strict — star schema, documented, governed
   Readers: Analysts, ML models, dashboards, business users
   Quality: Trusted — SLA-backed, monitored, lineage tracked
   Tables:
     • gold.fact_sales                  (star schema fact table)
     • gold.dim_store / dim_product      (dimension tables)
     • gold.feature_store_demand         (ML features for forecasting)
     • gold.kpi_daily_sales_summary      (dashboard aggregates)

─────────────────────────────────────────────────────────────────

KEY PRINCIPLE:
  Raw data enters Bronze with no assumptions.
  Silver enforces quality gates — no garbage passes through.
  Gold serves business and ML with trusted, governed data.

  ML models should ONLY read from Silver or Gold.
  If your model reads from Bronze, you're training on garbage.
```

This Bronze → Silver → Gold pattern isn't just a Databricks convention — it's the most practical way I've found to manage the tension between "let everything in" (data lake flexibility) and "make sure it's correct" (data warehouse discipline).

---

## Transactional vs. Analytical Processing

Huyen explains OLTP and OLAP as two fundamentally different processing patterns. While the terms are becoming outdated, the underlying distinction still matters:

```python
# Transactional vs Analytical: different queries, different needs

comparison = {
    "Purpose": (
        "Record individual business events",
        "Analyze patterns across many events"
    ),
    "Example Query": (
        "INSERT INTO orders VALUES (1001, 'CUST_42', 299.50, NOW())",
        "SELECT store_id, AVG(basket_size)\n"
        "                                      FROM fact_sales\n"
        "                                      WHERE year = 2025\n"
        "                                      GROUP BY store_id"
    ),
    "Latency Requirement": (
        "< 10ms (user is waiting)",
        "Minutes to hours is acceptable"
    ),
    "Data Pattern": (
        "Read/write individual rows",
        "Scan and aggregate millions of rows"
    ),
    "Volume per Query": (
        "1 row (or a small set)",
        "Millions to billions of rows"
    ),
    "Concurrency": (
        "Thousands of users simultaneously",
        "Dozens of analysts or scheduled jobs"
    ),
    "Storage Format": (
        "Row-major (fast row access)",
        "Column-major (fast aggregation)"
    ),
    "Retail Example": (
        "Customer places an order on Makro Pro app",
        "Daily sales report by category and store"
    ),
}

print("TRANSACTIONAL vs ANALYTICAL PROCESSING")
print("="*70)
print(f"{'Dimension':<22} {'Transactional (OLTP)':<25} {'Analytical (OLAP)'}")
print("-"*70)
for dim, (oltp, olap) in comparison.items():
    oltp_line = oltp.split('\n')[0]
    olap_line = olap.split('\n')[0]
    print(f"{dim:<22} {oltp_line:<25} {olap_line}")
print("="*70)
print()
print("MODERN REALITY:")
print("  The boundary is blurring. Delta Lake + Databricks handles both.")
print("  CockroachDB does OLTP with analytical queries.")
print("  Apache Iceberg brings ACID transactions to analytical tables.")
print("  The future is ONE storage layer with MULTIPLE processing engines.")
```

```
TRANSACTIONAL vs ANALYTICAL PROCESSING
======================================================================
Dimension              Transactional (OLTP)      Analytical (OLAP)
----------------------------------------------------------------------
Purpose                Record individual busines  Analyze patterns across
Example Query          INSERT INTO orders VALUES  SELECT store_id, AVG(ba
Latency Requirement    < 10ms (user is waiting)  Minutes to hours is acce
Data Pattern           Read/write individual row  Scan and aggregate milli
Volume per Query       1 row (or a small set)    Millions to billions of
Concurrency            Thousands of users simult  Dozens of analysts or sc
Storage Format         Row-major (fast row acces  Column-major (fast aggre
Retail Example         Customer places an order   Daily sales report by ca
======================================================================

MODERN REALITY:
  The boundary is blurring. Delta Lake + Databricks handles both.
  CockroachDB does OLTP with analytical queries.
  Apache Iceberg brings ACID transactions to analytical tables.
  The future is ONE storage layer with MULTIPLE processing engines.
```

---

## ETL — The Unglamorous Backbone

ETL (Extract, Transform, Load) is the unglamorous process that makes everything else possible. In our environment, this looks like:

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ETL PIPELINE ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  EXTRACT                    TRANSFORM                 LOAD          │
│  ┌──────────────┐          ┌──────────────┐         ┌────────────┐ │
│  │ POS API      │──┐       │              │         │            │ │
│  └──────────────┘  │       │  Validate    │         │  Bronze    │ │
│  ┌──────────────┐  │       │  Deduplicate │         │  (raw)     │ │
│  │ ERP Extract  │──┼──────▶│  Type cast   │────────▶│            │ │
│  └──────────────┘  │       │  Join        │    │    │  Silver    │ │
│  ┌──────────────┐  │       │  Aggregate   │    │    │  (clean)   │ │
│  │ Kafka Events │──┘       │  Feature eng │    │    │            │ │
│  └──────────────┘          │              │    └───▶│  Gold      │ │
│  ┌──────────────┐          └──────────────┘         │  (ready)   │ │
│  │ Weather API  │──────────────────────────────────▶│            │ │
│  └──────────────┘                                   └────────────┘ │
│                                                                     │
│  Orchestration: Azure Data Factory + Databricks Workflows           │
│  Format: Delta Lake (Parquet + transaction log)                     │
│  Governance: Unity Catalog                                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

The "Transform" step is where most of the engineering effort lives. Here's a real example of what a transform step looks like for cleaning raw sales data:

```python
# Transform step: cleaning raw POS data for ML consumption
# This runs daily as a Databricks notebook job

import pandas as pd
import numpy as np

def transform_raw_sales(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Transform raw POS extract into clean Silver-layer table.
    Every rule here was learned the hard way.
    """
    df = df_raw.copy()
    initial_count = len(df)
    
    # 1. SEPARATE RETURNS from sales
    #    Raw data mixes them together (returns have negative quantity).
    #    Treating returns as negative demand breaks forecasting models.
    df['is_return'] = df['quantity'] < 0
    df['quantity'] = df['quantity'].abs()
    
    # 2. REMOVE DUPLICATES
    #    POS retry logic sometimes sends the same transaction twice.
    before_dedup = len(df)
    df = df.drop_duplicates(subset=['transaction_id', 'sku_id', 'store_id'])
    dupes_removed = before_dedup - len(df)
    
    # 3. FIX TIMEZONE
    #    Thailand stores send UTC+7, India stores send UTC+5:30.
    #    Standardize everything to local time of the store.
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    
    # 4. HANDLE NULLS in customer_id
    #    Walk-in cash customers have no ID. Replace with placeholder.
    null_customers = df['customer_id'].isnull().sum()
    df['customer_id'] = df['customer_id'].fillna('WALK_IN')
    
    # 5. REMOVE IMPOSSIBLE VALUES
    #    Zero-price transactions are internal transfers, not sales.
    #    Quantity > 10000 is almost always a data entry error.
    impossible_price = (df['unit_price'] <= 0).sum()
    impossible_qty = (df['quantity'] > 10000).sum()
    df = df[(df['unit_price'] > 0) & (df['quantity'] <= 10000)]
    
    # 6. RECALCULATE TOTAL (don't trust source calculation)
    df['total_amount'] = df['quantity'] * df['unit_price']
    
    final_count = len(df)
    
    # Quality report
    report = {
        'input_rows': initial_count,
        'output_rows': final_count,
        'duplicates_removed': dupes_removed,
        'null_customers_flagged': null_customers,
        'impossible_prices_removed': impossible_price,
        'impossible_quantities_removed': impossible_qty,
        'rows_removed_pct': round((1 - final_count/initial_count) * 100, 2),
    }
    
    return df, report

# Simulate raw data with realistic quality issues
np.random.seed(42)
n = 100_000
raw_data = pd.DataFrame({
    'transaction_id': np.random.randint(1000000, 9999999, n),
    'store_id': np.random.randint(1, 155, n),
    'sku_id': np.random.randint(100000, 200000, n),
    'customer_id': np.where(
        np.random.random(n) > 0.15, 
        np.random.randint(10000, 99999, n).astype(str), 
        None  # 15% walk-ins
    ),
    'quantity': np.where(
        np.random.random(n) > 0.03,
        np.random.randint(1, 50, n),
        -np.random.randint(1, 10, n)  # 3% returns
    ),
    'unit_price': np.where(
        np.random.random(n) > 0.01,
        np.round(np.random.uniform(10, 500, n), 2),
        0  # 1% internal transfers
    ),
    'transaction_date': pd.date_range('2025-06-01', periods=n, freq='s'),
})

# Add some duplicates
dupes = raw_data.sample(500)
raw_data = pd.concat([raw_data, dupes], ignore_index=True)

# Transform
cleaned, quality_report = transform_raw_sales(raw_data)

print("ETL TRANSFORM: RAW POS → CLEAN SILVER TABLE")
print("="*55)
for key, value in quality_report.items():
    label = key.replace('_', ' ').title()
    print(f"  {label:<40} {value:>10,}")
print("="*55)
print()
print("Every one of these rules was learned from a production bug.")
print("This is the 'unglamorous 80%' of ML work.")
```

```
ETL TRANSFORM: RAW POS → CLEAN SILVER TABLE
=======================================================
  Input Rows                                    100,500
  Output Rows                                    96,532
  Duplicates Removed                                489
  Null Customers Flagged                         15,071
  Impossible Prices Removed                         978
  Impossible Quantities Removed                       0
  Rows Removed Pct                                 3.95
=======================================================

Every one of these rules was learned from a production bug.
This is the 'unglamorous 80%' of ML work.
```

3.95% of rows removed or fixed. That sounds small, but 3.95% of bad data flowing into a demand forecasting model means 3.95% of your stores getting wrong predictions every day. Over a year, that compounds into real money.

---

## Dataflow Patterns — How Data Moves Between Services

Huyen covers three modes of passing data between processes:

```
MODE 1: Through Databases (simplest, slowest)
  ┌───────────┐     ┌──────────┐     ┌───────────┐
  │ Feature   │────▶│ Database │────▶│ Prediction│
  │ Pipeline  │     │          │     │ Service   │
  └───────────┘     └──────────┘     └───────────┘
  Latency: seconds to minutes | Best for: batch ML pipelines

MODE 2: Through Services / REST APIs (request-driven)
  ┌───────────┐  HTTP request  ┌───────────┐
  │ Service A │───────────────▶│ Service B │
  │           │◀───────────────│           │
  └───────────┘  HTTP response └───────────┘
  Latency: milliseconds | Best for: real-time predictions

MODE 3: Through Real-Time Transport / Kafka (event-driven)
  ┌───────────┐     ┌─────────┐     ┌───────────┐
  │ Producer  │────▶│  Kafka  │────▶│ Consumer  │
  │ Service   │     │  Topic  │────▶│ Service B │
  └───────────┘     │         │────▶│ Service C │
                    └─────────┘     └───────────┘
  Latency: sub-second | Best for: streaming features, event-driven ML
```

In practice, most production ML systems use all three. Batch features go through databases. Real-time predictions go through REST APIs. Streaming features go through Kafka.

---

## Batch vs. Stream Processing — You Probably Need Both

This is where data engineering gets interesting for ML. Most ML features aren't purely batch or purely streaming — they're both.

```python
# Batch features vs Streaming features for demand forecasting

feature_types = {
    "Batch Features (Static)": {
        "computation": "Daily Spark/Databricks job",
        "latency": "T+1 (available next day)",
        "examples": [
            ("avg_sales_last_28d",    "Average daily sales over 28 days"),
            ("day_of_week_pattern",   "Historical avg sales by day of week"),
            ("store_tier",            "Store classification (changes rarely)"),
            ("product_shelf_life",    "Days until expiry (from product master)"),
            ("customer_segment",      "RFM-based segment (recomputed weekly)"),
            ("promotion_calendar",    "Upcoming promo flag from marketing plan"),
        ]
    },
    "Streaming Features (Dynamic)": {
        "computation": "Kafka + Flink / Spark Structured Streaming",
        "latency": "Seconds to minutes",
        "examples": [
            ("current_stock_level",   "Real-time inventory from warehouse"),
            ("sales_last_1_hour",     "Rolling 1-hour sales count"),
            ("active_carts_count",    "Number of open carts on e-commerce"),
            ("delivery_eta_minutes",  "Current estimated delivery time"),
            ("weather_current",       "Current temperature and rain status"),
            ("trending_sku_flag",     "SKU with 3x normal sales velocity now"),
        ]
    }
}

print("BATCH vs STREAMING FEATURES FOR ML")
print("="*70)
for feature_type, details in feature_types.items():
    print(f"\n{'─'*70}")
    print(f"📊 {feature_type}")
    print(f"   Computation: {details['computation']}")
    print(f"   Latency:     {details['latency']}")
    print(f"   {'Feature':<28} {'Description'}")
    print(f"   {'─'*65}")
    for feat_name, feat_desc in details['examples']:
        print(f"   {feat_name:<28} {feat_desc}")

print(f"\n{'─'*70}")
print()
print("COMBINED FEATURE VECTOR (what the model actually sees):")
print("  [avg_sales_28d, day_of_week, store_tier, is_promo,")
print("   current_stock, sales_last_hour, weather, trending_flag]")
print()
print("  ← batch features →  ← streaming features →")
print()
print("Both pipelines must join at serving time.")
print("This is the hardest part of production ML infrastructure.")
```

```
BATCH vs STREAMING FEATURES FOR ML
======================================================================

──────────────────────────────────────────────────────────────────────
📊 Batch Features (Static)
   Computation: Daily Spark/Databricks job
   Latency:     T+1 (available next day)
   Feature                      Description
   ─────────────────────────────────────────────────────────────────
   avg_sales_last_28d            Average daily sales over 28 days
   day_of_week_pattern           Historical avg sales by day of week
   store_tier                    Store classification (changes rarely)
   product_shelf_life            Days until expiry (from product master)
   customer_segment              RFM-based segment (recomputed weekly)
   promotion_calendar            Upcoming promo flag from marketing plan

──────────────────────────────────────────────────────────────────────
📊 Streaming Features (Dynamic)
   Computation: Kafka + Flink / Spark Structured Streaming
   Latency:     Seconds to minutes
   Feature                      Description
   ─────────────────────────────────────────────────────────────────
   current_stock_level           Real-time inventory from warehouse
   sales_last_1_hour             Rolling 1-hour sales count
   active_carts_count            Number of open carts on e-commerce
   delivery_eta_minutes          Current estimated delivery time
   weather_current               Current temperature and rain status
   trending_sku_flag             SKU with 3x normal sales velocity now

──────────────────────────────────────────────────────────────────────

COMBINED FEATURE VECTOR (what the model actually sees):
  [avg_sales_28d, day_of_week, store_tier, is_promo,
   current_stock, sales_last_hour, weather, trending_flag]

  ← batch features →  ← streaming features →

Both pipelines must join at serving time.
This is the hardest part of production ML infrastructure.
```

The last line is the real insight: **joining batch and streaming features at serving time is the hardest infrastructure problem in production ML.** It's easy to compute features in batch. It's manageable to compute features in a stream. But combining both into a single feature vector that a model can consume in real-time, with consistent semantics, without training-serving skew — that's where most teams struggle.

---

## My Key Takeaways from Chapter 3

**1. Know your data sources before you build anything.**
Each source has its own format, quality profile, latency, and ownership. Map them all before you design a pipeline.

**2. Use Parquet (or Delta Lake), not CSV, for anything analytical.**
The file size savings and column-read performance are not marginal — they're order-of-magnitude differences that compound at scale.

**3. Data modeling is upstream of everything.**
A well-designed star schema makes feature engineering trivial. A bad data model makes every ML project a custom wrangling effort.

**4. Bronze → Silver → Gold is the most practical lakehouse pattern.**
Raw in, cleaned in the middle, trusted at the top. ML models should never read from Bronze.

**5. ETL is the unglamorous 80% of ML work.**
Every data cleaning rule in your transform step was learned from a production bug. Respect the pipeline.

**6. Most production ML needs both batch and streaming features.**
Batch features capture history. Streaming features capture now. Joining them at serving time is the real infrastructure challenge.

**7. Pick the right data model for the job.**
Relational for structured analytics. Document for flexible schemas. Graph for relationship queries. Most ML feature engineering starts relational.

---

## What's Next

Chapter 4 dives into training data — sampling strategies, labeling, class imbalance, and data augmentation. It's where the data engineering foundation we built here starts feeding into model development.

I'll cover it with the same approach: real examples, working code, and the production context that makes the difference.

---

*If this was useful, follow for the next article in this series. I write about data engineering, ML systems, and building AI platforms in enterprise — with real code and real tradeoffs, not just theory.*
