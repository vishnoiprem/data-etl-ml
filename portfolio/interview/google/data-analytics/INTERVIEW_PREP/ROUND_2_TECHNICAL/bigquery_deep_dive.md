# BigQuery Deep Dive - Technical Mastery
## Architecture, Optimization, SQL Patterns for Interview

---

## 🏗️ BigQuery Architecture (Memorize & Draw)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BIGQUERY ARCHITECTURE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        STORAGE LAYER (Colossus)                      │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │  │  Tablet 1   │  │  Tablet 2   │  │  Tablet 3   │  │  Tablet N   │  │   │
│  │  │ (Colossus)  │  │ (Colossus)  │  │ (Colossus)  │  │ (Colossus)  │  │   │
│  │  │  Columnar   │  │  Columnar   │  │  Columnar   │  │  Columnar   │  │   │
│  │  │  Capacitor  │  │  Capacitor  │  │  Capacitor  │  │  Capacitor  │  │   │
│  │  │  Compressed │  │  Compressed │  │  Compressed │  │  Compressed │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │   │
│  │         │               │               │               │             │   │
│  │         └───────────────┼───────────────┼───────────────┘             │   │
│  │                         ▼                                           │   │
│  │              ┌─────────────────────┐                                │   │
│  │              │   Metadata Store    │                                │   │
│  │              │   (Schema, Stats,   │                                │   │
│  │              │    Partitions,      │                                │   │
│  │              │     Clustering)     │                                │   │
│  │              └─────────────────────┘                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                    STORAGE ≠ COMPUTE SEPARATION                             │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        COMPUTE LAYER (Borg)                          │   │
│  │                                                                       │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │                      SLOT POOL                                │   │   │
│  │  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌────────┐  │   │   │
│  │  │  │ Slot 1  │ │ Slot 2  │ │ Slot 3  │ │ Slot 4  │ │ Slot N │  │   │   │
│  │  │  │ ~1 vCPU │ │ ~1 vCPU │ │ ~1 vCPU │ │ ~1 vCPU │ │ ~1 vCPU│  │   │   │
│  │  │  │ ~4 GB   │ │ ~4 GB   │ │ ~4 GB   │ │ ~4 GB   │ │ ~4 GB  │  │   │   │
│  │  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └────────┘  │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │                                    │                                 │   │
│  │                    Dynamic Allocation                                │   │
│  │                                    ▼                                 │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │                    QUERY EXECUTION                            │   │   │
│  │  │  1. Parse & Analyze  →  2. Optimize  →  3. Execute         │   │   │
│  │  │       (SQL)                (Plan)         (Slots)           │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  KEY PROPERTIES:                                                             │
│  • Storage: $0.02/GB/month (active), $0.01/GB/month (long-term)            │
│  • Compute: $0.04/slot/hour (on-demand), Editions/Reservations cheaper     │
│  • Scale independently - no cluster resizing                                │
│  • Time travel: 7 days default (configurable up to 90 days)                │
│  • Fail-safe: 7 days after time travel (non-configurable)                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Slot Mechanics (Critical for Optimization)

### Slot Allocation Models
| Model | Use Case | Cost | Control |
|-------|----------|------|---------|
| **On-Demand** | Ad-hoc, unpredictable | $0.04/slot/hr | None - fair share |
| **Flex Slots** | Burst capacity | $0.06/slot/hr | 60-sec commitment |
| **Baseline Reservations** | Predictable workloads | ~$0.025/slot/hr (1yr) | Guaranteed capacity |
| **Editions (Standard/Enterprise)** | Committed use | 30-50% discount | Features + slots |

### Fair Scheduling
- **Per-project fairness** - each project gets fair share of slots
- **Job-level fairness** - within project, jobs share slots
- **Priority** - interactive > batch (but both can starve)
- **Reservation assignments** - assign projects to reservations for isolation

---

## 🎯 Optimization Checklist (MEMORIZE - 10 Items)

```
□ 1. PARTITION PRUNING
   WHERE event_date >= '2024-01-01'          ✅ GOOD
   WHERE DATE(event_ts) >= '2024-01-01'      ❌ BAD - function on column
   WHERE event_date = CURRENT_DATE()         ❌ BAD - non-deterministic

□ 2. CLUSTERING (Max 4 columns, high cardinality first)
   CLUSTER BY customer_id, region, product_category, channel
   → Enables block pruning + sort optimization

□ 3. COLUMN PRUNING
   SELECT customer_id, revenue               ✅ GOOD
   SELECT *                                  ❌ BAD - reads all columns

□ 4. MATERIALIZED VIEWS
   CREATE MATERIALIZED VIEW daily_sales AS
   SELECT date, SUM(revenue) FROM sales GROUP BY date
   → Auto-refresh, query rewrite, 10-100x faster for aggregations

□ 5. BI ENGINE
   Reservation: 50-100GB for sub-second dashboards
   → Auto-detects frequent queries, in-memory acceleration

□ 6. SLOT ESTIMATION
   SELECT job_id, total_slot_ms, bytes_billed
   FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
   WHERE creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)

□ 7. QUERY PLAN ANALYSIS
   EXPLAIN SELECT ...  →  Look for:
   • "Broadcast" joins → consider clustering both sides
   • "Shuffle" → check partitioning/clustering alignment
   • Stage count → too many = over-partitioned or complex

□ 8. CACHING
   Deterministic UDFs, no NOW()/RAND()/CURRENT_* → 100% cache hits
   Cache: 24 hours, ~100GB per project

□ 9. RESERVATIONS STRATEGY
   Baseline (predictable) + Flex (burst) + Edition (commitment discount)
   Monitor: slot utilization %, queue time, cost per TB

□ 10. ADVANCED: SEARCH OPTIMIZATION SERVICE
   For point lookups on high-cardinality columns (user_id, session_id)
   CREATE SEARCH INDEX ON table(col) → 10-100x faster WHERE col = 'x'
```

---

## 📊 Partitioning vs Clustering Decision Matrix

| Scenario | Partition By | Cluster By | Why |
|----------|--------------|------------|-----|
| Time-series analytics | DATE(event_ts) | user_id, region | Partition prune time, cluster filter users |
| Multi-tenant SaaS | tenant_id | user_id, feature | Partition isolate tenants, cluster user queries |
| High-cardinality lookups | (none) | user_id, session_id | Search Index better than partition |
| Small tables (<1GB) | (none) | (none) | Overhead not worth it |
| Append-only logs | DATE(ingest_ts) | source_system | Partition by ingest, cluster by source |
| ML feature store | DATE(feature_ts) | entity_id, feature_name | Partition time, cluster entity+feature |

### Anti-Patterns to Avoid
- ❌ Partition by high-cardinality column (user_id) → too many partitions
- ❌ Cluster by low-cardinality column (country, status) → no pruning benefit
- ❌ Partition + cluster on same column → redundant
- ❌ Too many partitions (>4000) → metadata overhead

---

## 💰 Cost Optimization Patterns

### Real Example: 2TB → 90GB Scan (95% Reduction)
```sql
-- BEFORE: Full scan
SELECT customer_id, COUNT(*) as orders, SUM(amount) as revenue
FROM `project.dataset.orders`
WHERE order_date >= '2024-01-01'
GROUP BY customer_id;
-- Bytes scanned: 2.3 TB | Cost: $14.38 | Time: 45 min

-- AFTER: Partitioned + Clustered + Materialized View
-- Table: PARTITION BY DATE(order_date) CLUSTER BY customer_id, region
-- MV: CREATE MATERIALIZED VIEW daily_customer_revenue AS
--   SELECT DATE(order_date) as order_date, customer_id, region,
--          COUNT(*) as orders, SUM(amount) as revenue
--   FROM `project.dataset.orders`
--   GROUP BY 1,2,3;

-- Query rewritten to hit MV:
SELECT customer_id, SUM(orders), SUM(revenue)
FROM `project.dataset.daily_customer_revenue`
WHERE order_date >= '2024-01-01'
GROUP BY customer_id;
-- Bytes scanned: 47 GB | Cost: $0.29 | Time: 8 sec
```

### Edition Commitment Savings
| Commitment | Slot Discount | Best For |
|------------|---------------|----------|
| 1-year | ~20% | Stable workloads |
| 3-year | ~35% | Predictable enterprise |
| Enterprise Edition | + features (CMEK, VPC-SC, SLA) | Regulated industries |

---

## 🔍 Query Plan Reading (Whiteboard Skill)

### Key Operators to Recognize
| Operator | Meaning | Optimization Signal |
|----------|---------|---------------------|
| **SCAN** | Reading table | Check partition pruning |
| **FILTER** | WHERE clause | Push down predicates |
| **AGGREGATE** | GROUP BY | Consider materialized view |
| **JOIN** | Table join | Broadcast vs Shuffle |
| **SORT** | ORDER BY | Limit + Order = TopN optimization |
| **SHUFFLE** | Data redistribution | Clustering alignment? |
| **BROADCAST** | Small table to all slots | Good if <10MB, bad if large |

### Skew Detection
```sql
-- Find skew in query execution
SELECT stage_id, step_id, 
       MAX(shuffle_output_bytes) / NULLIF(AVG(shuffle_output_bytes), 0) as skew_ratio
FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT j,
     UNNEST(job_stages) as stage,
     UNNESS(stage.steps) as step
WHERE j.job_id = 'your_job_id'
GROUP BY stage_id, step_id
HAVING skew_ratio > 10;  -- 10x skew = problem
```

### Skew Mitigation (Your War Story)
```
Problem: user_id = NULL represented 40% of 5TB dataset → single slot OOM
Solution:
1. Salting: user_id || '_' || CAST(RAND()*100 AS INT64) for NULL keys
2. Custom partitioner: Separate NULL keys to dedicated partition
3. Shuffle service: Enable for managed shuffle (Disk + Memory)
4. Result: 14hr+OOM → 4hr successful completion
```

---

## 🧠 BI Engine (Sub-Second Dashboards)

### When to Use
- Looker / Data Studio dashboards with high concurrency
- Repeated query patterns (same filters, different values)
- Sub-second SLA for executive dashboards

### Configuration
```sql
-- Reserve BI Engine capacity
-- Console: BigQuery → BI Engine → Reserve 50GB (minimum)

-- Check what's accelerated
SELECT * FROM `region-us`.INFORMATION_SCHEMA.BI_ENGINE_QUERY_STATS
WHERE acceleration_status = 'FULL';
```

---

## 📝 Interview Talking Points

### "Explain BigQuery Architecture" (3 min)
1. **Storage-Compute Separation** - Colossus (storage) vs Borg (compute)
2. **Slots** - Unit of compute (~1 vCPU + 4GB), dynamic allocation
3. **Capacitor Format** - Columnar, compressed, encoding per type
4. **Metadata Layer** - Partition/clustering stats for pruning
5. **BI Engine** - In-memory acceleration for repeated queries
6. **Pricing Model** - Pay per TB scanned + slot reservations

### "How Do You Optimize a Slow Query?" (Structured Answer)
1. **Profile** - EXPLAIN, slot_ms, bytes_billed, timeline
2. **Prune** - Partition filter, column selection
3. **Cluster** - High-cardinality filter columns (max 4)
4. **Pre-aggregate** - Materialized view for common GROUP BY
5. **Accelerate** - BI Engine for dashboards
6. **Reserve** - Baseline + Flex slots for predictable performance
7. **Monitor** - Set up alerts for scan bytes, slot wait time

---

## 🔗 Related Files
- `code/bigquery_optimization.sql` - Runnable optimization examples
- `notebooks/bigquery_optimization_demo.ipynb` - Interactive demo
- `migration_strategies.md` - Migration-specific BQ patterns

---

*Last Updated: 2026-01-15 | For: Google Cloud Data & Analytics Lead Technical Screen*