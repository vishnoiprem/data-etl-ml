# Metadata Management & Data Lineage: Stop Getting Lost in Your Own Data Lake
*How to build a GPS for your lakehouse — because nobody wants to wander in the data wilderness*

---

## Ever Been Lost in the Woods?

Picture this: You're hiking in a new forest. No GPS. No map. Just trees everywhere that look exactly the same.

That panicky feeling? **Data teams experience it every single day.**

"I know the table exists somewhere..."
"Someone told me there's a customer orders dataset..."
"Where did that pipeline output go?"

Sound familiar?

This is exactly what happens when you build a data lake without proper **metadata management**. You have all this valuable data, but nobody can find it. Or worse — they find the *wrong* data and make decisions based on it.

Let me show you how to build a GPS for your lakehouse.

---

## What is Metadata, Really?

Here's the simplest way I can explain it:

```
METADATA = Data about your data
```

Think about a library book:

| The Book | Metadata About the Book |
|----------|------------------------|
| The actual pages and words | Title, author, ISBN |
| The content you read | Publication date, genre |
| The story itself | Where it's located (shelf, row) |
| | Who checked it out last |

Without that metadata, a library would just be a warehouse of random books. Good luck finding anything!

Your data lake is the same. Without metadata, it's just a chaotic pile of files.

---

## The Data Catalog: Your Lakehouse's Search Engine

A **data catalog** is like Google for your data. Instead of searching the web, you search your lakehouse.

At minimum, a good data catalog tells you:

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA CATALOG                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WHAT exists?     → Tables, views, databases                │
│  WHERE is it?     → Storage location, path                  │
│  WHO owns it?     → Team, data steward                      │
│  WHEN updated?    → Last refresh time                       │
│  HOW to access?   → Permissions, connection info            │
│  WHY trust it?    → Quality scores, lineage                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### The IKEA Analogy

Ever shopped at IKEA? You don't wander around hoping to stumble upon a couch. You use their system:

1. Search for "couch" on the website
2. Find the exact model you want
3. Get the aisle and bin number
4. Walk directly to it

A good data catalog works the same way. Data teams have a general idea of what they need, and the catalog makes the journey simple.

---

## Why Manual Catalogs Fail (Every Time)

"We'll just maintain a spreadsheet of all our tables!"

Famous last words.

Here's what happens:

```
Month 1:  Spreadsheet is created. Everyone is excited.
Month 2:  A few tables get added. Things look good.
Month 3:  New tables created but not added to spreadsheet.
Month 6:  Spreadsheet is 50% outdated.
Month 12: Nobody trusts the spreadsheet anymore.
```

**The problem:** Manual processes don't scale. Without automation, your catalog becomes a promise of what *could* be rather than what *actually* is.

The solution? **Automated cataloging** that syncs with your actual data assets in real-time.

---

## The Hive Metastore: Where It All Started

If you've worked with data lakes, you've probably heard of the **Hive Metastore**. Let me explain why it matters.

### The Translation Layer

Before Spark SQL, querying data lakes was painful. The Hive Metastore solved this by translating file-based tables into SQL-queryable structures.

```
┌─────────────────────────────────────────────────────────────┐
│                   HIVE METASTORE                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Physical Files          Metastore          SQL Interface  │
│   (Parquet, Delta)   →   (Postgres/MySQL)  →  (SHOW, SELECT)│
│                                                             │
│   s3://bucket/           database: sales      SHOW TABLES   │
│   └── sales/             table: orders        SELECT * FROM │
│       └── orders/        columns: [...]       sales.orders  │
│           └── *.parquet  location: s3://...                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### What Hive Metastore Provides

```sql
-- List all databases
SHOW DATABASES;

-- List tables in a database
SHOW TABLES IN sales;

-- See table details
DESCRIBE EXTENDED sales.orders;

-- Check table properties
SHOW TBLPROPERTIES sales.orders;
```

### The Big Limitation

Here's the catch: **You can only connect to one catalog per Spark session.**

```python
# This is set globally — can't easily join across catalogs
spark.conf.set("spark.sql.catalog.spark_catalog", "...")
spark.conf.set("spark.sql.warehouse.dir", "...")
```

If you need to join tables from different catalogs? You're stuck copying data between buckets. Not ideal.

---

## Unity Catalog: The Modern Solution

**Unity Catalog** solves the multi-catalog problem and adds a ton of governance features.

### The Three-Tier Namespace

Instead of just `database.table`, Unity Catalog gives you:

```
{catalog}.{database/schema}.{table}

Examples:
  prod.sales.orders
  dev.marketing.campaigns
  staging.finance.transactions
```

This means you can finally do:

```python
# Join tables across catalogs in ONE query!
spark.sql("""
    SELECT *
    FROM prod.sales.orders o
    JOIN prod.marketing.campaigns c ON o.campaign_id = c.id
    JOIN analytics.reporting.metrics m ON o.order_id = m.order_id
""")
```

No more copying data between buckets!

### Unity Catalog Features

| Feature | What It Does |
|---------|-------------|
| **Centralized Metastore** | One place for all metadata |
| **Three-Tier Namespace** | catalog.schema.table |
| **Cross-Catalog Queries** | Join across boundaries |
| **Unified Governance** | Tables, notebooks, ML models, dashboards |
| **Credential Vending** | Secure access to S3/cloud storage |
| **Open Source** | Apache 2.0 license |

### Quick Start with Unity Catalog OSS

```bash
# Clone and start the server
git clone git@github.com:unitycatalog/unitycatalog.git
cd unitycatalog
bin/start-uc-server
```

You'll see:

```
###################################################################
#  _   _       _ _          _____      _        _                 #
# | | | |_ __ (_) |_ _   _ / ____|__ _| |_ __ _| | ___   __ _     #
# | | | | '_ \| | __| | | | |   / _` | __/ _` | |/ _ \ / _` |     #
# | |__| | | | | | |_| |_| | |__| (_| | || (_| | | (_) | (_| |     #
#  \____/|_| |_|_|\__|\__, |\____\__,_|\__\__,_|_|\___/ \__, |     #
#                      __/ |                            __/ |     #
#                     |___/                            |___/      #
###################################################################
```

List available tables:

```bash
bin/uc table list --catalog unity --schema default
```

---

## Data Lineage: The Flight Recorder

Now let's talk about **data lineage** — one of the most underrated capabilities in data engineering.

### What is Data Lineage?

Data lineage tracks the journey of your data:

- Where it came from (sources)
- How it was transformed (processing)
- Where it went (destinations)

Think of it like a flight recorder for your data.

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA LINEAGE                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  External Sources    →    Bronze    →    Silver    →   Gold │
│  (APIs, vendors)         (raw)        (cleaned)    (curated)│
│                                                             │
│  📦 Vendor A ─────┐                                         │
│                   ├──→ 📊 raw_events ──→ 📊 clean_events    │
│  📦 Vendor B ─────┘                              │          │
│                                                  ↓          │
│  📦 CRM System ──────→ 📊 customers ────→ 📊 customer_360   │
│                                                             │
│  The lineage shows: dependencies, transformations, owners   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Why Lineage Matters

**Scenario:** Your CEO dashboard shows wrong numbers. Everyone is panicking.

**Without lineage:**
- "Which table feeds this dashboard?"
- "Who owns that pipeline?"
- "When did the data stop flowing?"
- Hours of investigation...

**With lineage:**
- Click the dashboard → see upstream tables
- Click the table → see the pipeline that produces it
- See the last successful run → find the failure
- 15 minutes to root cause

### The Vendor Swap Example

Say you receive marketing data from Vendor A. They charge too much, so you switch to Vendor B.

**The problem:** Vendor A and Vendor B have completely different data formats.

**The solution:** Your internal data domain transforms vendor-specific data into a common format. The downstream consumers never need to know which vendor you're using.

```
Vendor A Format          Common Format           Gold Layer
┌──────────────┐        ┌──────────────┐       ┌──────────────┐
│ email_sent   │        │              │       │              │
│ click_count  │───────→│ notification │──────→│ campaign     │
│ vendor_id    │        │ _events      │       │ _performance │
└──────────────┘        │              │       │              │
                        │ (standardized)│       │ (insights)   │
┌──────────────┐        │              │       │              │
│ notification │        │              │       │              │
│ clicks       │───────→│              │       │              │
│ source_key   │        └──────────────┘       └──────────────┘
└──────────────┘
  Vendor B Format
```

Data lineage makes this transition visible and manageable.

---

## OpenLineage: The Open Standard

**OpenLineage** is an open-source framework for capturing data lineage automatically.

### The Core Entities

```
┌─────────────────────────────────────────────────────────────┐
│                    OPENLINEAGE MODEL                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────┐     ┌───────────┐     ┌───────────┐         │
│  │  DATASET  │     │    JOB    │     │    RUN    │         │
│  │           │     │           │     │           │         │
│  │ • name    │     │ • name    │     │ • run_id  │         │
│  │ • namespace     │ • namespace     │ • state   │         │
│  │ • schema  │     │ • inputs  │     │ • start   │         │
│  │           │     │ • outputs │     │ • end     │         │
│  └───────────┘     └───────────┘     └───────────┘         │
│                                                             │
│  Dataset = Your tables                                      │
│  Job = Your data application                                │
│  Run = One execution of the job                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Python Implementation

Here's working code to capture lineage with OpenLineage:

```python
"""
OpenLineage Integration Example
Capture data lineage for your pipelines
"""

from openlineage.client import OpenLineageClient
from openlineage.client.run import (
    RunEvent, RunState, Run, Job, Dataset
)
from datetime import datetime
from uuid import uuid4

# Initialize the client
client = OpenLineageClient.from_environment()

# Define your job metadata
producer = 'common_foods.consumer.clickstream'
job_name = 'consumer.clickstream.orders'

# Define input datasets (tables you read from)
input_datasets = [
    Dataset(namespace='consumer', name='consumer.clickstream'),
    Dataset(namespace='consumer', name='consumer.customers')
]

# Define output datasets (tables you write to)
output_datasets = [
    Dataset(namespace='consumer', name='consumer.order_events')
]

# Create Job and Run objects
job = Job(namespace='consumer', name=job_name)
run = Run(runId=str(uuid4()))


def emit_start():
    """Emit event when job starts"""
    event = RunEvent(
        eventType=RunState.START,
        eventTime=datetime.now().isoformat(),
        run=run,
        job=job,
        producer=producer
    )
    client.emit(event)
    print(f"✅ Started: {job_name}")


def emit_complete(inputs, outputs):
    """Emit event when job completes successfully"""
    event = RunEvent(
        eventType=RunState.COMPLETE,
        eventTime=datetime.now().isoformat(),
        run=run,
        job=job,
        producer=producer,
        inputs=inputs,
        outputs=outputs
    )
    client.emit(event)
    print(f"✅ Completed: {job_name}")


def emit_failed(error_message):
    """Emit event when job fails"""
    event = RunEvent(
        eventType=RunState.FAIL,
        eventTime=datetime.now().isoformat(),
        run=run,
        job=job,
        producer=producer
    )
    client.emit(event)
    print(f"❌ Failed: {job_name} - {error_message}")


# Example usage in your pipeline
if __name__ == "__main__":
    try:
        # Start lineage tracking
        emit_start()
        
        # === YOUR DATA PIPELINE CODE HERE ===
        # df = spark.read.table("consumer.clickstream")
        # result = df.transform(...)
        # result.write.saveAsTable("consumer.order_events")
        # =====================================
        
        # Complete lineage tracking
        emit_complete(input_datasets, output_datasets)
        
    except Exception as e:
        emit_failed(str(e))
        raise
```

### Simplify with Decorators

For cleaner code, use a decorator pattern:

```python
from functools import wraps

def track_lineage(producer, job_name, inputs, outputs):
    """Decorator to automatically track lineage"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Emit start event
            emit_start()
            
            try:
                # Run the actual function
                result = func(*args, **kwargs)
                
                # Emit complete event
                emit_complete(inputs, outputs)
                
                return result
                
            except Exception as e:
                # Emit failed event
                emit_failed(str(e))
                raise
        
        return wrapper
    return decorator


# Usage
@track_lineage(
    producer='sales.team',
    job_name='daily_revenue_calc',
    inputs=[Dataset('sales', 'orders'), Dataset('sales', 'products')],
    outputs=[Dataset('analytics', 'daily_revenue')]
)
def calculate_daily_revenue():
    """Your pipeline logic here"""
    # Spark transformations...
    pass
```

---

## Data Reliability: SLAs for Data

Just like services have SLAs (Service Level Agreements), your data products should have **DLAs (Data Level Agreements)**.

### DLOs and DLIs

| Term | Meaning | Example |
|------|---------|---------|
| **DLO** (Data Level Objective) | The guarantee you make | "All columns will never be NULL" |
| **DLI** (Data Level Indicator) | The metric you measure | "Table lag: 5 minutes behind real-time" |

### Example: Streaming Table DLO

```sql
-- Define constraints as part of your DLO
ALTER TABLE sales.orders
ADD CONSTRAINT orders_not_null 
CHECK (order_id IS NOT NULL AND customer_id IS NOT NULL);

-- This constraint is enforced by Delta Lake
-- Your DLO is automatically met!
```

### Measuring Table Freshness (DLI)

```python
def get_table_freshness(table_path):
    """
    Calculate how far behind real-time our table is
    This is our DLI for streaming tables
    """
    from delta.tables import DeltaTable
    from pyspark.sql.functions import max, current_timestamp
    
    # Get the latest event timestamp in our table
    df = spark.read.format("delta").load(table_path)
    latest_event = df.select(max("event_timestamp")).first()[0]
    
    # Calculate lag
    lag_seconds = (datetime.now() - latest_event).total_seconds()
    
    return {
        "table": table_path,
        "latest_event": latest_event,
        "lag_seconds": lag_seconds,
        "lag_minutes": lag_seconds / 60,
        "status": "OK" if lag_seconds < 300 else "WARNING"
    }

# Example output:
# {
#     "table": "s3://bucket/sales/orders",
#     "latest_event": "2025-01-14 10:55:00",
#     "lag_seconds": 180,
#     "lag_minutes": 3.0,
#     "status": "OK"
# }
```

---

## Automating Data Life Cycles

Data doesn't live forever. Here's how to automate retention policies using table properties.

### Step 1: Define Retention Policy

```sql
-- Add retention properties to your table
ALTER TABLE delta.`s3://bucket/sales/orders`
SET TBLPROPERTIES (
    'catalog.table.gov.retention.enabled' = 'true',
    'catalog.table.gov.retention.date_col' = 'event_date',
    'catalog.table.gov.retention.policy' = 'interval 28 days'
);
```

### Step 2: Parse the Interval

```python
import re
from pyspark.sql.functions import lit, make_dt_interval

def convert_to_interval(interval_str: str):
    """
    Convert string like 'interval 28 days' to Spark interval
    """
    # Clean the string
    target = interval_str.lower().strip()
    if target.startswith("interval"):
        target = target.replace("interval", "").strip()
    
    # Parse number and type
    number, interval_type = re.split(r"\s+", target)
    amount = int(number)
    
    # Build the interval
    if interval_type == "days":
        return make_dt_interval(days=lit(min(amount, 365)))
    elif interval_type == "hours":
        return make_dt_interval(hours=lit(min(amount, 24)))
    elif interval_type == "minutes":
        return make_dt_interval(mins=lit(min(amount, 60)))
    else:
        raise ValueError(f"Unknown interval type: {interval_type}")
```

### Step 3: Check Compliance

```python
from delta.tables import DeltaTable

def check_retention_compliance(table_path: str):
    """
    Check if a table is compliant with retention policy
    Returns the cutoff date for data retention
    """
    # Load table and get properties
    dt = DeltaTable.forPath(spark, table_path)
    props = dt.detail().first()['properties']
    
    # Check if retention is enabled
    enabled = props.get('catalog.table.gov.retention.enabled', 'false')
    if enabled.lower() != 'true':
        return {"status": "SKIPPED", "reason": "Retention not enabled"}
    
    # Get policy
    policy = props.get('catalog.table.gov.retention.policy', 'interval 90 days')
    date_col = props.get('catalog.table.gov.retention.date_col', 'event_date')
    
    # Calculate cutoff date
    interval = convert_to_interval(policy)
    
    cutoff = spark.sql("SELECT current_timestamp() as now") \
        .withColumn("interval", interval) \
        .withColumn("retain_after", (col("now") - col("interval")).cast("date")) \
        .first()
    
    return {
        "status": "OK",
        "table": table_path,
        "policy": policy,
        "date_column": date_col,
        "retain_after": cutoff["retain_after"],
        "delete_before": cutoff["retain_after"]
    }

# Example output:
# {
#     "status": "OK",
#     "table": "s3://bucket/sales/orders",
#     "policy": "interval 28 days",
#     "date_column": "event_date",
#     "retain_after": "2024-12-17",
#     "delete_before": "2024-12-17"
# }
```

### Step 4: Auto-Delete Old Data

```python
def enforce_retention(table_path: str):
    """
    Delete data older than retention policy
    """
    compliance = check_retention_compliance(table_path)
    
    if compliance["status"] != "OK":
        print(f"Skipping: {compliance.get('reason', 'Unknown')}")
        return
    
    dt = DeltaTable.forPath(spark, table_path)
    date_col = compliance["date_column"]
    cutoff = compliance["delete_before"]
    
    # Delete old data
    deleted = dt.delete(f"{date_col} < '{cutoff}'")
    
    print(f"✅ Deleted data before {cutoff} from {table_path}")
    
    # Vacuum to reclaim storage
    dt.vacuum(retentionHours=168)  # 7 days
    
    print(f"✅ Vacuumed old files")
```

---

## Data Discovery: Finding What You Need

**Data discovery** is the search engine for your lakehouse. It helps users find the right data without knowing exactly where to look.

### What Makes Good Discovery?

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA DISCOVERY                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Search: "customer orders"                                  │
│                                                             │
│  Results:                                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 📊 prod.sales.customer_orders                       │    │
│  │    ⭐ Verified | 👤 Owner: Sales Team               │    │
│  │    📅 Updated: 5 mins ago | 📈 Used by: 47 reports  │    │
│  │    Tags: #customers #orders #revenue                │    │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 📊 staging.sales.orders_v2                          │   │
│  │    ⚠️ Staging | 👤 Owner: Data Engineering          │   │
│  │    📅 Updated: 2 days ago | 📈 Used by: 3 reports  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Key Discovery Features

| Feature | Why It Matters |
|---------|---------------|
| **Full-text search** | Find tables by name, description, column names |
| **Verified badges** | Trust indicators for production-ready data |
| **Ownership info** | Know who to contact |
| **Freshness** | Is this data current? |
| **Usage stats** | Is this table actually used? |
| **Lineage preview** | Quick view of upstream/downstream |
| **Tags & labels** | Categorization for filtering |

### Simple Implementation with ElasticSearch

For most lakehouses (under 1M assets), a simple ElasticSearch index works great:

```python
from elasticsearch import Elasticsearch

es = Elasticsearch()

def index_table(table_info):
    """Add a table to the discovery index"""
    doc = {
        "catalog": table_info["catalog"],
        "schema": table_info["schema"],
        "table": table_info["table"],
        "full_name": f"{table_info['catalog']}.{table_info['schema']}.{table_info['table']}",
        "columns": table_info["columns"],
        "owner": table_info["owner"],
        "description": table_info.get("description", ""),
        "tags": table_info.get("tags", []),
        "last_updated": table_info["last_updated"],
        "verified": table_info.get("verified", False),
        "usage_count": table_info.get("usage_count", 0)
    }
    
    es.index(index="data-catalog", id=doc["full_name"], document=doc)


def search_tables(query: str, verified_only: bool = False):
    """Search for tables matching query"""
    search_body = {
        "query": {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": query,
                            "fields": ["table^3", "description^2", "columns", "tags"]
                        }
                    }
                ]
            }
        }
    }
    
    if verified_only:
        search_body["query"]["bool"]["filter"] = [
            {"term": {"verified": True}}
        ]
    
    results = es.search(index="data-catalog", body=search_body)
    return results["hits"]["hits"]
```

---

## Monitoring & Alerting

### Compliance Monitoring

Using our retention properties, we can automatically scan for non-compliant tables:

```python
def scan_for_compliance():
    """
    Daily scan to check all tables for compliance
    """
    # Get all tables from catalog
    tables = spark.sql("SHOW TABLES IN prod").collect()
    
    non_compliant = []
    
    for table in tables:
        table_name = f"prod.{table.tableName}"
        
        # Check if retention is configured
        props = spark.sql(f"SHOW TBLPROPERTIES {table_name}").collect()
        props_dict = {row.key: row.value for row in props}
        
        if 'catalog.table.gov.retention.enabled' not in props_dict:
            non_compliant.append({
                "table": table_name,
                "issue": "Retention policy not configured",
                "owner": props_dict.get("catalog.engineering.owner", "Unknown")
            })
    
    # Alert on non-compliant tables
    if non_compliant:
        send_slack_alert(
            channel="#data-governance",
            message=f"⚠️ {len(non_compliant)} tables missing retention policies",
            details=non_compliant
        )
    
    return non_compliant
```

### Pipeline Health Monitoring

```python
def monitor_table_freshness():
    """
    Check if tables are updating as expected
    """
    # Tables with expected refresh frequency
    critical_tables = [
        {
            "table": "prod.sales.orders",
            "expected_frequency_minutes": 60,
            "owner_slack": "@sales-data-team"
        },
        {
            "table": "prod.marketing.campaigns",
            "expected_frequency_minutes": 120,
            "owner_slack": "@marketing-analytics"
        }
    ]
    
    alerts = []
    
    for config in critical_tables:
        freshness = get_table_freshness(config["table"])
        
        if freshness["lag_minutes"] > config["expected_frequency_minutes"]:
            alerts.append({
                "table": config["table"],
                "expected_minutes": config["expected_frequency_minutes"],
                "actual_minutes": freshness["lag_minutes"],
                "owner": config["owner_slack"]
            })
    
    # Send alerts
    for alert in alerts:
        send_pagerduty_alert(
            title=f"Table Stale: {alert['table']}",
            message=f"Expected refresh every {alert['expected_minutes']}m, "
                    f"but last update was {alert['actual_minutes']:.0f}m ago",
            notify=alert["owner"]
        )
```

---

## Key Takeaways

1. **Metadata is your GPS**
   - Without it, you're lost in your own data lake
   - Automate catalog updates — manual processes fail

2. **Data lineage is your flight recorder**
   - Know where data comes from
   - Quickly find root cause when things break
   - Use OpenLineage for standardized tracking

3. **Unity Catalog solves multi-catalog problems**
   - Three-tier namespace: catalog.schema.table
   - Cross-catalog joins in single queries
   - Unified governance for all assets

4. **Automate life cycle management**
   - Use table properties for retention policies
   - Build automated compliance checks
   - Delete old data programmatically

5. **Data discovery saves hours**
   - Build a search engine for your lakehouse
   - Add verification badges for trust
   - Include ownership and freshness info

6. **Monitor and alert proactively**
   - Don't wait for users to report problems
   - Check compliance daily
   - Alert on stale critical tables

---

## Quick Reference: Table Properties for Governance

```sql
-- Retention policy
ALTER TABLE my_table SET TBLPROPERTIES (
    'catalog.table.gov.retention.enabled' = 'true',
    'catalog.table.gov.retention.date_col' = 'event_date',
    'catalog.table.gov.retention.policy' = 'interval 28 days'
);

-- Ownership and contact
ALTER TABLE my_table SET TBLPROPERTIES (
    'catalog.engineering.owner' = 'data-platform-team',
    'catalog.engineering.comms.slack' = '#data-platform',
    'catalog.engineering.comms.email' = 'data-team@company.com'
);

-- Freshness expectations
ALTER TABLE my_table SET TBLPROPERTIES (
    'catalog.table.deprecated' = 'false',
    'catalog.table.expectations.sla.refresh.frequency' = 'interval 1 hour',
    'catalog.table.expectations.checks.frequency' = 'interval 15 minutes',
    'catalog.table.expectations.checks.alert_after_num_failed' = '3'
);
```

---

## Final Thought

Building a data lake is easy. Building a data lake you can actually navigate? That takes metadata management, lineage tracking, and good governance practices.

Start with the basics:
1. Catalog your tables automatically
2. Track lineage from day one
3. Set retention policies on every table
4. Build discovery so people can find what they need

Your future self (and your entire data team) will thank you.

---

**References:**
- Unity Catalog OSS: github.com/unitycatalog/unitycatalog
- OpenLineage: openlineage.io
- Delta Lake Documentation: delta.io

---

*Thanks for reading! Drop a comment if you have questions about implementing any of this.*

**Tags:** #DataEngineering #Lakehouse #Metadata #DataLineage #DataGovernance #UnityCatalog #DeltaLake
