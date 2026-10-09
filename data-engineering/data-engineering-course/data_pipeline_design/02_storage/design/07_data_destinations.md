# 07 — Data Destinations

> **Lesson 7 of 30 — Storage**

The right edge of every pipeline is a data destination. The four
destination types you'll meet are warehouses, lakehouses, serving
stores, and reverse-ETL targets. Each has a different query
pattern, a different cost profile, and a different consistency
guarantee. This lesson is the *when to use which* decision tree.

---

## 1. The four destination types

| Destination | Examples | Query pattern | Cost per TB / month |
|---|---|---|---|
| **Warehouse** | Snowflake, BigQuery, Redshift | SQL analytics, BI | $20-50 |
| **Lakehouse** | Delta Lake, Iceberg, Hudi | SQL on Parquet, ML | $1-5 (S3) + $5-20 compute |
| **Serving store** | Bigtable, Cassandra, Redis, ClickHouse | Point lookups, OLAP | $25-100 |
| **Reverse-ETL** | Hightouch, Census, Salesforce | Operational sync | per-row pricing |

The choice of destination is dictated by the *consumer*, not by
you. A dashboard needs a warehouse. An ML model needs a feature
store. A real-time product feature needs a KV store. The senior
move is to ask "who consumes this and how?" and pick the
destination that matches.

---

## 2. Warehouses (Snowflake, BigQuery, Redshift)

Warehouses are columnar SQL engines optimized for analytics. They
excel at:

- Ad-hoc SQL queries over billions of rows
- BI dashboards (Looker, Tableau, Mode)
- Scheduled reports
- Complex joins across many tables

**They are not good at:**

- Single-row lookups (use a KV store)
- Sub-second latency on large scans
- Storing semi-structured data efficiently (use a lakehouse)
- Cheap storage of raw, uncleaned data (use a lakehouse)

**The 2026 default.** Snowflake for cross-cloud, BigQuery for
GCP-native, Redshift for AWS-native legacy. The differences are
mostly pricing models and ecosystem; the underlying capability is
similar.

```sql
-- The warehouse pattern: star-schema queries
SELECT
  d.date,
  p.category,
  SUM(o.total) AS revenue
FROM fct_orders o
JOIN dim_date d ON o.order_date = d.date
JOIN dim_product p ON o.product_id = p.product_id
WHERE d.date >= '2024-01-01'
GROUP BY 1, 2;
```

---

## 3. Lakehouses (Delta Lake, Iceberg, Hudi)

A lakehouse is a parquet-on-S3 (or GCS / ADLS) data lake with
three extra guarantees:

1. **ACID transactions.** Multi-writer safety, no partial reads.
2. **Schema enforcement.** Bad data is rejected at write time.
3. **Time travel.** Read the table as it was at timestamp T-7.

The three implementations:

| | Delta Lake | Iceberg | Hudi |
|---|---|---|---|
| Backed by | Databricks | Apple / Netflix / Tabular | Uber |
| Strengths | Spark integration, mature | Hive compatibility, hidden partitioning | CDC, record-level updates |
| Weakness | Databricks coupling | Less Spark-native | Smaller community |

**The senior move** is to know that all three solve the same
problem with different tradeoffs. The interview rarely tests
"Delta vs Iceberg internals"; it tests "what does a lakehouse add
on top of Parquet?" Answer: ACID + schema + time travel.

```
Parquet on S3:
  /data/users/part-0001.parquet
  /data/users/part-0002.parquet
  + nothing else

Delta on S3:
  /data/users/part-0001.parquet
  /data/users/part-0002.parquet
  /data/users/_delta_log/000001.json   ← transaction log
  /data/users/_delta_log/000002.json
  + atomicity, schema check, time travel
```

---

## 4. Serving stores (Bigtable, Redis, ClickHouse)

The serving store is what the *product* reads from. Different
products want different shapes:

| Product need | Right store |
|---|---|
| Real-time product feature (e.g. "is this user premium?") | Redis (KV) |
| Time-series metrics (e.g. "page views per minute") | ClickHouse, Druid |
| User-profile lookups (e.g. "give me user 12345") | Bigtable, Cassandra |
| Full-text search (e.g. "find products matching 'red shoes'") | Elasticsearch, OpenSearch |

**The senior move** is to recognize that the warehouse is *not*
the right destination for a product feature. Putting product
reads on a warehouse means the BI workload competes with the
product workload, and the product latency is dominated by the
BI scan. Separate them.

**The pipeline pattern:** the lakehouse/warehouse is the source
of truth. The serving store is a *projection* — a denormalized,
indexed, partial view of the truth. The pipeline keeps them in
sync. The serving store can be stale; the source of truth cannot.

---

## 5. Reverse-ETL (Hightouch, Census)

Reverse-ETL is the pattern of *syncing* warehouse data back into
operational systems: Salesforce, HubSpot, Zendesk, Marketo. The
"ETL" word is reversed because data flows from the warehouse
*out* to the operational system, instead of the other way.

**The senior move** is to know that reverse-ETL is its own
category with its own tradeoffs:

| Pro | Con |
|---|---|
| Warehouse is the source of truth for all data | Sync lag (typically minutes to hours) |
| Operations team uses tools they already know | Two-way sync is hard (operational system may overwrite warehouse) |
| No custom code per integration | Vendor lock-in to Hightouch / Census |

The 2026 default for new architectures: Hightouch or Census for
the SaaS destinations, custom Python for the in-house ones.

---

## 6. The Medallion pattern (where each layer lives)

The Medallion pattern (bronze / silver / gold) maps to
destinations as follows:

```
Bronze (raw): Delta / Iceberg on S3
              └─► cheap, schema-on-read, replayable
Silver (cleaned): Delta / Iceberg on S3
              └─► ACID, schema-enforced, queryable
Gold (curated): Snowflake / BigQuery
              └─► SQL, BI tools, fast aggregations
Serving: Redis / Bigtable / ClickHouse
              └─► low-latency product reads
```

The bridge between lakehouse and warehouse is *dbt* or *Spark*
running SQL transformations. The medallion pattern is the single
most important answer in any data architecture interview.

---

## 7. The cost story

The senior answer includes cost unprompted. A 2026 cost comparison:

| Destination | $ / TB / month | Query cost |
|---|---|---|
| S3 standard | $23 | $0 |
| Delta on S3 | $23 + small compute | $5-10 per scan |
| Snowflake | $40 (compressed) | $2-5 per credit |
| BigQuery | $20 (active) + $10 (long-term) | $6.25 per TB scanned |
| ClickHouse Cloud | $50-100 | $0.01 per query |

**The senior move** is to know that the warehouse is the most
expensive layer per query, but the cheapest per analyst-hour
(BI tools just work). The lakehouse is the cheapest per TB, but
the most expensive per analyst-hour (more setup). The serving
store is the most expensive per query, but the only choice for
real-time.

---

## 8. Choosing the right destination

```
Who consumes this and at what latency?
  └─ BI dashboards (minutes) → Warehouse (Snowflake / BigQuery)
  └─ ML training (hours) → Lakehouse (Delta / Iceberg)
  └─ Product feature (sub-second) → Serving store (Redis / Bigtable)
  └─ Operational system (sync) → Reverse-ETL (Hightouch / Census)
  └─ Audit / replay (forever) → Lakehouse (raw, no transforms)
```

This is the decision tree you'll recite in the interview. The
right answer is rarely "I'd use Snowflake for everything." The
right answer is "Given the consumers, I'd use X for Y and A for B."

---

## Try it

Pick a pipeline you've worked on. Map every destination table to
the Medallion layer (bronze / silver / gold) and the storage type
(lakehouse / warehouse / serving). If you can't, your pipeline
probably has an unclear contract between layers — that's a
real-world smell, not just an interview answer.
