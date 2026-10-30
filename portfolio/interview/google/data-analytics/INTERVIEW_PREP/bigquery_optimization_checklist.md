# BigQuery Optimization — 30 Techniques Checklist
## Interview-Ready Reference for Google Cloud Data & Analytics Lead

---

## 🎯 Quick Reference: Top 10 (Memorize These)

| # | Technique | Impact | When |
|---|-----------|--------|------|
| 1 | **Partition pruning** | 10-1000x | Date/TIMESTAMP column, filter in WHERE |
| 2 | **Clustering** | 2-10x | High-cardinality filter columns (max 4) |
| 3 | **Column pruning** | 2-10x | SELECT only needed columns |
| 4 | **Materialized views** | 10-100x | Repeated aggregations, pre-computed |
| 5 | **Approximate aggregation** | 10-100x | COUNT DISTINCT, quantiles (HLL, APPROX_QUANTILES) |
| 6 | **Partition elimination** | 10x+ | Partition on ingest time or business date |
| 7 | **Avoid SELECT *** | 2-100x | Explicit columns, especially with STRUCT/ARRAY |
| 8 | **Push filters down** | 5-50x | WHERE before JOIN, subquery filters |
| 9 | **Slot reservations** | Cost 40-60% | Predictable workloads, baseline capacity |
| 10 | **BI Engine** | Sub-second | Dashboards, repeated queries <100GB |

---

## 📋 Complete 30-Technique Checklist

### A. Partitioning & Clustering (Foundation)

| # | Technique | Syntax/Config | Best Practice |
|---|-----------|---------------|---------------|
| 1 | **Ingestion-time partitioning** | `PARTITION BY DATE(_PARTITIONTIME)` | Default for streaming loads |
| 2 | **Column-based partitioning** | `PARTITION BY DATE(event_dt)` | Business date, enables partition pruning |
| 3 | **Integer range partitioning** | `PARTITION BY RANGE_BUCKET(id, GENERATE_ARRAY(1, 10000, 100))` | Uniform numeric keys |
| 4 | **Clustering (max 4 cols)** | `CLUSTER BY customer_id, event_type, region, channel` | High-cardinality, frequent filters, ORDER BY columns |
| 5 | **Partition + Cluster combo** | `PARTITION BY DATE(event_dt) CLUSTER BY customer_id` | Partition for pruning, cluster for sort/colocation |
| 6 | **Partition expiration** | `expirationMs: 2592000000` (30 days) | Auto-cleanup, cost control |
| 7 | **Require partition filter** | `requirePartitionFilter: true` | Force partition pruning, prevent full scans |

### B. Query Patterns (Read Optimization)

| # | Technique | Example | Why |
|---|-----------|---------|-----|
| 8 | **Filter on partition column FIRST** | `WHERE event_dt = '2026-01-15' AND customer_id = 'x'` | Partition pruning before clustering |
| 9 | **Partition pruning with functions** | `WHERE DATE(event_ts) = '2026-01-15'` ❌ vs `WHERE event_dt = '2026-01-15'` ✅ | Functions prevent pruning |
| 10 | **Column pruning** | `SELECT event_id, revenue FROM ...` | Only read needed columns |
| 11 | **Avoid SELECT * with STRUCT/ARRAY** | `SELECT event_id, metadata.key FROM ...` | Nested fields expand to all sub-fields |
| 12 | **Push predicates into subqueries** | `WITH filtered AS (SELECT * FROM t WHERE dt='x') SELECT ...` | Reduce rows early |
| 13 | **SEMI/ANTI JOIN vs IN/EXISTS** | `WHERE id IN (SELECT id FROM small)` → `SEMI JOIN` | Broadcast small table, avoid shuffle |
| 14 | **Broadcast hints** | `/*+ BROADCAST(small_table) */` | Force broadcast join for <100MB tables |
| 15 | **Denormalize with STRUCT/ARRAY** | `SELECT customer_id, ARRAY_AGG(STRUCT(event_id, amount))` | Avoid JOINs, colocation in storage |

### C. Aggregation & Analytics

| # | Technique | Function | Use Case |
|---|-----------|----------|----------|
| 16 | **Approximate COUNT DISTINCT** | `APPROX_COUNT_DISTINCT(col)` | 10x faster, <1% error |
| 17 | **Approximate Quantiles** | `APPROX_QUANTILES(col, 100)[OFFSET(50)]` | Median/percentiles without sort |
| 18 | **HyperLogLog++** | `HLL_COUNT.MERGE(sketch)` | Merge sketches across partitions |
| 19 | **Materialized View** | `CREATE MATERIALIZED VIEW mv AS SELECT ...` | Auto-rewrite, incremental refresh |
| 20 | **Partitioned Materialized View** | `PARTITION BY DATE(event_dt) CLUSTER BY customer_id` | Align with base table partitioning |
| 21 | **Avoid GROUP BY on high-cardinality** | Pre-aggregate in pipeline, or use `APPROX_TOP_COUNT` | Shuffle reduction |

### D. Cost Control & Slot Management

| # | Technique | Config | Savings |
|---|-----------|--------|---------|
| 22 | **Slot Reservations (Baseline)** | `capacity_commitment` (1yr/3yr) | 40-60% vs on-demand |
| 23 | **Flex Slots** | `flex_slots` (per-second) | Burst capacity, pay per second |
| 24 | **Editions (Standard/Enterprise)** | `edition: 'STANDARD'` | Feature-based pricing |
| 25 | **Query Cost Control** | `maximum_bytes_billed` | Fail fast if scan > threshold |
| 26 | **Information Schema Auditing** | `INFORMATION_SCHEMA.JOBS_BY_PROJECT` | Track top scanners, optimize |
| 27 | **Label-based Cost Attribution** | `labels: {team: 'analytics', env: 'prod'}` | Chargeback, FinOps dashboards |

### E. Advanced Patterns

| # | Technique | When |
|---|-----------|------|
| 28 | **Search Index (Full-text)** | `CREATE SEARCH INDEX ON table(col)` — text search without scanning |
| 29 | **Vector Index (Embeddings)** | `CREATE VECTOR INDEX ON table(embedding)` — similarity search |
| 30 | **Change Data Capture (CDC)** | `BigQuery CDC` — incremental sync from OLTP |

---

## 🔍 Query Diagnosis — EXPLAIN Output Reading

### Key Fields in `EXPLAIN`
```json
{
  "queryPlan": [
    {
      "name": "Stage 1",
      "id": "1",
      "startMs": "0",
      "endMs": "1200",
      "recordsRead": "1000000",
      "recordsWritten": "1000",
      "shuffleOutputBytes": "50000000",
      "steps": [
        {"kind": "READ", "substeps": ["$event_dt", "$customer_id"]},
        {"kind": "FILTER", "predicate": "event_dt = '2026-01-15'"},
        {"kind": "AGGREGATE", "groupBy": ["customer_id"]}
      ]
    }
  ],
  "estimatedBytesProcessed": "104857600",
  "billingTier": 1
}
```

### Red Flags to Spot
| Signal | Problem | Fix |
|--------|---------|-----|
| `recordsRead` >> `recordsWritten` (early stage) | Late filtering | Push WHERE up |
| `shuffleOutputBytes` high | Data redistribution | Broadcast small table, denormalize |
| `estimatedBytesProcessed` > expected | Missing partition pruning | Check partition column filter |
| Multiple stages with same `READ` | Repeated table scans | Materialized view / CTE reuse |

---

## 🎯 Interview Scenarios & Answers

### Scenario 1: "Query scans 2TB but only needs 50GB"
> **My approach:**
> 1. `EXPLAIN` → check `recordsRead` vs `recordsWritten` per stage
> 2. **Partition pruning**: Is `WHERE DATE(event_ts)` used? Change to `WHERE event_dt = '...'`
> 3. **Clustering**: Are filter columns clustered? Add `CLUSTER BY customer_id, event_type`
> 4. **Column pruning**: `SELECT *`? Change to explicit columns
> 5. **Materialized view**: Is this repeated aggregation? Create MV with same partition/cluster
> **Result:** 2TB → 50GB (40x reduction) in 3 steps

### Scenario 2: "One store has 40% of data — skew killing performance"
> **My approach:**
> 1. **Salting**: Add `salt = ABS(FARM_FINGERPRINT(store_id)) % 10` → `GROUP BY store_id, salt` → re-aggregate
> 2. **Custom partitioning**: `PARTITION BY RANGE_BUCKET(store_id, ...)` isolate hot store
> 3. **Approximate**: `APPROX_TOP_COUNT(store_id, 10)` for top stores only
> 4. **Separate pipeline**: Hot store → dedicated processing path

### Scenario 3: "Dashboard queries too slow for 50 concurrent users"
> **My approach:**
> 1. **BI Engine**: Reserve 10-50GB for hot tables → sub-second latency
> 2. **Materialized views**: Pre-compute dashboard aggregations
> 3. **Clustering**: Align with dashboard filter columns
> 4. **Caching**: 24hr query cache + BI Engine cache

### Scenario 4: "Cost exploded — $5K/month on BigQuery"
> **My approach:**
> 1. **Audit**: `INFORMATION_SCHEMA.JOBS_BY_PROJECT` → top 10 scanners
> 2. **Partition pruning**: Fix queries missing partition filter
> 3. **Slot reservation**: 1-year baseline = 40% savings
> 4. **Maximum bytes billed**: Guardrails on ad-hoc queries
> 5. **Labels**: Cost attribution by team/project

---

## 💰 Cost Model Cheat Sheet

| Model | Price | Best For |
|-------|-------|----------|
| **On-Demand** | $6.25/TB scanned | Ad-hoc, unpredictable |
| **Standard Edition (Slots)** | $0.04/slot-hour | Predictable, baseline |
| **Enterprise Edition** | $0.06/slot-hour | High concurrency, BI Engine |
| **Flex Slots** | $0.000011/slot-second | Burst, per-second billing |
| **Storage (Active)** | $0.02/GB/mo | Hot data |
| **Storage (Long-term)** | $0.01/GB/mo | >90 days unused |

**Slot Math:** 1 slot = 1 vCPU + 0.5 GB RAM. Query uses slots proportional to complexity.

---

## 🎯 60-Second Recitation (Practice This)

> **"My BigQuery optimization checklist — 30 techniques across 5 categories:**
>
> **Foundation (7):** Partitioning (ingestion-time, column, integer-range), clustering (max 4 cols), partition+cluster combo, expiration, require partition filter.
>
> **Query Patterns (7):** Filter partition column first, no functions on partition col, column pruning, no SELECT* with STRUCT, push predicates down, SEMI/ANTI joins, broadcast hints.
>
> **Aggregation (4):** Approximate COUNT DISTINCT, quantiles, HLL++, materialized views (partitioned+clustered).
>
> **Cost Control (6):** Slot reservations (40-60% savings), flex slots, editions, max bytes billed, Information Schema auditing, label-based attribution.
>
> **Advanced (3):** Search index, vector index, CDC.
>
> **Top 3 for any slow query:** 1) Partition pruning check, 2) Clustering alignment, 3) Column pruning. These fix 80% of cases."**

---

## 📋 Practice Drills

### Drill 1: Draw Partitioning Decision Tree (2 min)
```
Is there a natural date/timestamp column?
  YES → Column-based partitioning (DATE(event_dt))
  NO  → Ingestion-time partitioning (_PARTITIONTIME)
  
  Is there high-cardinality filter column?
  YES → Clustering (customer_id, event_type, region, channel)
  NO  → No clustering needed
  
  Combo: PARTITION BY DATE(event_dt) CLUSTER BY customer_id
```

### Drill 2: Optimize This Query (3 min)
```sql
-- SLOW: Scans full 500GB table
SELECT * 
FROM events 
WHERE DATE(event_ts) = '2026-01-15' 
  AND customer_id = 'CUST-123'
  AND event_type = 'purchase';

-- FAST: 3 fixes
SELECT event_id, customer_id, amount, event_dt
FROM events 
WHERE event_dt = '2026-01-15'           -- Partition pruning (no function)
  AND customer_id = 'CUST-123'          -- Clustering filter
  AND event_type = 'purchase';          -- Clustering filter
-- Table: PARTITION BY DATE(event_dt) CLUSTER BY customer_id, event_type
```

### Drill 3: Explain Output Analysis (2 min)
Given EXPLAIN showing: `recordsRead=10M, recordsWritten=100K, shuffleOutputBytes=5GB`
- **Diagnosis:** Late filter + shuffle
- **Fix:** Push WHERE up, broadcast small dimension table

---

*Keep this as your Round 2/3/4 reference. The 30 techniques cover every optimization question Google asks. The top 10 handle 90% of scenarios.*