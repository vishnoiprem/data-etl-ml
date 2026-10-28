# 2.3 — BigQuery Out-of-the-Box Features

> **Section 2 · BigQuery Fundamentals · Lecture 2.3 · 4:01**

## 🎯 What you will learn

- The feature set BigQuery ships with that you'd otherwise build yourself
- Federated querying, time travel, and data governance
- Which features are genuinely free and which are not

---

## 🧠 Concept

"Out-of-the-box" means: features that require **no cluster, no pipeline, and no code** from you.
These are the features that make BigQuery more than a query engine.

### The built-in feature set

| Feature | What it does | Why it matters |
|---------|--------------|----------------|
| **Zero operational overhead** | No provisioning, patching, failover | No DBA on-call |
| **Automatic scaling** | Slots scale per query, up to project max | No capacity planning |
| **Columnar storage + compression** | Only referenced columns read; compressed | Cheapest scans |
| **Federated querying** | Query data in GCS, Cloud Storage, Bigtable, Pub/Sub, Sheets | No load step |
| **Time travel** | Query table state from any point in the last 7 days | Recovery without backups |
| **Streaming inserts** | Write rows and query them in seconds | Low-latency ingest |
| **Materialized views** | Pre-aggregate, auto-refresh | Cheaper repeated queries |
| **Search indexes** | `SEARCH` operator over semi-structured data | Log/message search without ES |
| **JSON support** | Native JSON type, `JSON_EXTRACT`, `LATERAL` | Semi-structured without flattening |
| **Geospatial** | `GEOGRAPHY`, `ST_*` functions | Spatial analytics without GIS tooling |
| **Time-series** | `TIMESTAMP` + RANGE windows | IoT telemetry aggregation |
| **Graph** | Property graph tables, `GRAPH_TABLE` | Relationship analysis |
| **ML in SQL** | `CREATE MODEL` | Train without leaving the warehouse |
| **Data Studio / Looker connectivity** | Native connectors | No custom BI connector |
| **Data Catalog** | Unified metadata, lineage, tags | Governance without a tool |
| **Policy tags** | Column-level classification + masking | PII control without code |
| **Column-level security** | Restrict by IAM condition on column | Fine-grained access |
| **Row-level security** | `SESSION_USER()` in views | Multi-tenant isolation in SQL |
| **Audit logs** | Every query logged to Cloud Logging | Compliance for free |
| **SLA** | 99.9% availability for query processing | Vendor commitment |

---

## 🛠️ Hands-On

### 1. Federated query — no load required

```sql
-- Query Parquet files directly in Cloud Storage, without creating a table
SELECT
    event_type,
    COUNT(*) AS total
FROM `gs://YOUR_PROJECT_ID-bq-course/raw/events_*.parquet`
GROUP BY event_type
ORDER BY total DESC;
```

```sql
-- Federated query across BigQuery AND Cloud Storage in one statement
WITH
    bq_events AS (
        SELECT event_type, COUNT(*) AS n, 'bq' AS src
        FROM `YOUR_PROJECT_ID.analytics.raw_events`
        WHERE event_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
        GROUP BY event_type
    ),
    gcs_events AS (
        SELECT JSON_VALUE(data, '$.event_type') AS event_type,
               COUNT(*) AS n, 'gcs' AS src
        FROM `gs://YOUR_PROJECT_ID-bq-course/raw/events_*.json`
        GROUP BY 1
    )
SELECT * FROM bq_events
UNION ALL
SELECT * FROM gcs_events;
```

### 2. Time travel — recover without a backup

```sql
-- What did the table look like 2 hours ago?
SELECT COUNT(*) AS row_count_2h_ago
FROM `YOUR_PROJECT_ID.analytics.raw_events`
  FOR SYSTEM_TIME AS OF TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR);

-- Restore a deleted table (within the 7-day window)
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.analytics.raw_events`
AS OF TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 3 HOUR)
SELECT * FROM `YOUR_PROJECT_ID.analytics.raw_events`;
```

💡 **Time travel turns "we lost the data" from an incident into a query.** It applies to managed
tables, views, materialized views, and table snapshots. External tables are *not* time-travellable
because BigQuery does not own the files.

### 3. Policy tags and column-level masking

```sql
-- Create a policy tag for PII
CREATE POLICY TAG `YOUR_PROJECT_ID.security.pii_email`
DESCRIPTION = 'Contains customer email addresses';

-- Attach it to a column
ALTER TABLE `YOUR_PROJECT_ID.analytics.customers`
  ALTER COLUMN email SET OPTIONS (policy_tags = ('YOUR_PROJECT_ID.security.pii_email'));
```

```sql
-- Conditional policy tags are created with DDL, not with client-library
-- constructors. The taxonomy must already exist in Policy Tags.
CREATE POLICY TAG `YOUR_PROJECT_ID.security.pii_email`
DESCRIPTION = 'Email address'
;

-- Attach it to a column
ALTER TABLE `YOUR_PROJECT_ID.analytics.customers`
  ALTER COLUMN email SET OPTIONS (policy_tags = ('YOUR_PROJECT_ID.security.pii_email'));
```

```python
# From Python, the same DDL runs as an ordinary query job.
from google.cloud import bigquery

client = bigquery.Client()

ddl = """
CREATE POLICY TAG `YOUR_PROJECT_ID.security.pii_email`
DESCRIPTION = 'Email address'
"""

job = client.query(ddl)
job.result()
print(f"✓ policy tag created")

# And attach it to a column
attach = """
ALTER TABLE `YOUR_PROJECT_ID.analytics.customers`
  ALTER COLUMN email SET OPTIONS (policy_tags = ('YOUR_PROJECT_ID.security.pii_email'))
"""

job = client.query(attach)
job.result()
print(f"✓ policy tag attached to analytics.customers.email")
```

> **Note:** policy tags live in the **Policy Tags** API (`policytags.googleapis.com`),
> not the BigQuery API. Create the taxonomy and tag there first, then reference
> the tag by name from BigQuery DDL. The `bigquery.ConditionalPolicyTag` and
> related classes do not exist in `google-cloud-bigquery`.

### 4. Row-level security via a view

```sql
CREATE OR REPLACE VIEW `YOUR_PROJECT_ID.analytics.v_customer_orders`
OPTIONS (
  description = 'Orders visible to the signed-in user territory',
  labels = [('security', 'rls')]
) AS
SELECT
    o.order_id,
    o.customer_id,
    o.order_date,
    o.total_amount
FROM `YOUR_PROJECT_ID.curated.orders` o
WHERE o.territory IN (
    SELECT territory
    FROM `YOUR_PROJECT_ID.security.user_territories`
    WHERE email = SESSION_USER()
);
```

### 5. Search index over semi-structured data

```sql
-- Create a search index
CREATE SEARCH INDEX `YOUR_PROJECT_ID.search.idx_event_logs`
ON `YOUR_PROJECT_ID.analytics.event_logs`(payload);

-- Query it
SELECT
    log_id,
    payload,
    SUBSTR(payload, 1, 120) AS snippet
FROM `YOUR_PROJECT_ID.analytics.event_logs`
WHERE SEARCH(payload, 'error OR timeout');
```

---

## 💡 Production Notes

- **Federated queries are great for exploration and bad for production serving.** Scanning GCS files
  has no table-level cache, no partitioning metadata, and no clustering — so you pay full file-scan
  cost every time.
- **Time travel costs money.** Restored and snapshot data is billed as active storage until deleted.
- **Policy tags propagate.** Attaching a tag to a column makes it apply to every downstream view and
  derived table automatically — this is the highest-leverage governance feature in BigQuery.
- **Data Catalog lineage is automatic** for BigQuery assets — no instrumentation required.
- **Row-level security via views has a subtle risk:** if a user has direct table access, the view's
  filter is bypassed. Use views *plus* restrict table grants, or use authorized views with
  `authorized_user`/`authorized_group` bindings.

---

## 🔑 Key Takeaways

- BigQuery ships with federation, time travel, materialized views, policy tags, RLS, search, ML,
  geospatial, and time-series built in.
- **Federated queries** remove the load step but forfeit partitioning/clustering benefits.
- **Time travel** (7 days) is free recovery — use it before reaching for snapshots.
- **Policy tags** are the governance feature that scales; they propagate automatically downstream.
- Authorized views are safer than plain views for row-level isolation, because they bind access to
  the view, not the base table.

---

## 📚 Practice Exercises

1. **No-build vs build.** For each feature, describe what you would have had to build on a
   traditional stack: materialized views, time travel, policy tags, federated queries, search index.

2. **Time travel recovery.** A `DELETE` removed 4 hours of rows. Write the exact recovery SQL for:
   (a) recovering into a new table for analysis, (b) restoring the original table in place.

3. **Governance design.** Design the policy-tag taxonomy for a company with PII (email, phone,
   national ID), financial data (salary, revenue), and internal-only data (support notes). Which
   tags are conditional, which are unconditional?

4. **Federated vs loaded.** You query a 10 TB Parquet dataset in GCS daily for BI. Compare:
   external table vs managed table vs federated query — for query cost, latency, and operations.

---

## 📖 Further Reading

- BigQuery feature overview — https://cloud.google.com/bigquery/docs/features
- Time travel — https://cloud.google.com/bigquery/docs/time-travel
- Policy tags — https://cloud.google.com/bigquery/docs/column-security
- Authorized views — https://cloud.google.com/bigquery/docs/authorized-views
