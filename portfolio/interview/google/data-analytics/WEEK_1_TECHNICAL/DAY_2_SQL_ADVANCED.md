# Day 2: SQL Advanced - Window Functions, CTEs, Optimization
## Google Data Analyst Interview Prep - Week 1

---

### 🎯 Learning Objectives
By end of Day 2, you can:
- [ ] Master all window functions: ROW_NUMBER, RANK, DENSE_RANK, LAG, LEAD, NTILE, FIRST_VALUE, LAST_VALUE
- [ ] Write complex CTEs with multiple levels, recursive CTEs
- [ ] Optimize queries: partitioning, clustering, predicate pushdown
- [ ] Handle BigQuery-specific features: ARRAY, STRUCT, QUALIFY
- [ ] Solve 15 advanced problems in <60 minutes

---

### 📖 Advanced Concepts Reference

#### Window Function Syntax Mastery
```sql
-- General syntax
FUNCTION() OVER (
  PARTITION BY column1, column2  -- Groups (optional)
  ORDER BY column3               -- Order within partition (required for ranking)
  ROWS/RANGE BETWEEN ...         -- Frame clause (advanced)
)

-- ROWS vs RANGE
ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW      -- Running total
ROWS BETWEEN 2 PRECEDING AND 2 FOLLOWING              -- Moving average
RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING  -- Full partition
```

#### Window Function Quick Reference
| Function | Use Case | Example |
|----------|----------|---------|
| `ROW_NUMBER()` | Unique sequential rank | Deduplication, pagination |
| `RANK()` | Rank with gaps (1,2,2,4) | Competition ranking |
| `DENSE_RANK()` | Rank without gaps (1,2,2,3) | Tier assignment |
| `LAG(col, n)` | Access previous row | MoM growth, session gaps |
| `LEAD(col, n)` | Access next row | Time to next event |
| `FIRST_VALUE()` | First in partition | Baseline comparison |
| `LAST_VALUE()` | Last in partition | Latest status |
| `NTILE(n)` | Buckets (percentiles) | Customer segmentation |
| `PERCENT_RANK()` | Relative rank 0-1 | Percentile scoring |
| `CUME_DIST()` | Cumulative distribution | Inclusive percentile |

#### Advanced CTE Patterns

**Multi-level CTE (Read Top-to-Bottom)**
```sql
WITH
raw AS (SELECT * FROM source_table),
cleaned AS (
  SELECT
    CAST(id AS INT64) as id,
    TRIM(name) as name,
    DATE(created_at) as created_date
  FROM raw
  WHERE id IS NOT NULL
),
aggregated AS (
  SELECT
    created_date,
    COUNT(DISTINCT id) as daily_users
  FROM cleaned
  GROUP BY created_date
),
final AS (
  SELECT
    created_date,
    daily_users,
    LAG(daily_users) OVER (ORDER BY created_date) as prev_day_users
  FROM aggregated
)
SELECT * FROM final;
```

**Recursive CTE (Hierarchical Data)**
```sql
WITH RECURSIVE org_chart AS (
  -- Anchor: top-level managers
  SELECT employee_id, name, manager_id, 0 as level, CAST(name AS STRING) as path
  FROM employees
  WHERE manager_id IS NULL

  UNION ALL

  -- Recursive: direct reports
  SELECT e.employee_id, e.name, e.manager_id, oc.level + 1, CONCAT(oc.path, ' > ', e.name)
  FROM employees e
  JOIN org_chart oc ON e.manager_id = oc.employee_id
  WHERE oc.level < 10  -- Prevent infinite loops
)
SELECT * FROM org_chart ORDER BY level, path;
```

#### BigQuery-Specific Power Features

**QUALIFY Clause (Filter Window Functions Directly)**
```sql
-- Instead of CTE wrapper
SELECT
  user_id,
  event_date,
  ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY event_date) as rn
FROM events
QUALIFY rn = 1;  -- Only first event per user!
```

**ARRAY & STRUCT (Nested Data)**
```sql
-- Create arrays
SELECT
  user_id,
  ARRAY_AGG(STRUCT(event_name, event_timestamp)) as events
FROM events
GROUP BY user_id;

-- Unnest arrays
SELECT
  user_id,
  event.event_name,
  event.event_timestamp
FROM user_events,
UNNEST(events) as event;
```

**PIVOT / UNPIVOT**
```sql
-- Pivot: rows to columns
SELECT * FROM (
  SELECT quarter, product, revenue
  FROM sales
)
PIVOT(SUM(revenue) FOR quarter IN ('Q1', 'Q2', 'Q3', 'Q4'));

-- Unpivot: columns to rows
SELECT * FROM quarterly_sales
UNPIVOT(revenue FOR quarter IN (q1_rev, q2_rev, q3_rev, q4_rev));
```

---

### ⚡ Query Optimization for BigQuery

#### Partitioning & Clustering
```sql
-- Partitioned table (by date)
CREATE TABLE dataset.sales_partitioned
PARTITION BY DATE(sale_timestamp)
CLUSTER BY customer_id, product_category
AS SELECT * FROM dataset.sales_raw;

-- Query benefits:
-- - Partition pruning: WHERE DATE(sale_timestamp) = '2024-01-15'
-- - Cluster pruning: WHERE customer_id = 123
-- - Both: massive cost reduction
```

#### Optimization Checklist
| Technique | When to Use | Impact |
|-----------|-------------|--------|
| **Partition pruning** | Date/time filters | High - scans only relevant partitions |
| **Clustering** | High-cardinality filter columns | High - sorts data within partitions |
| **Predicate pushdown** | Filter early in CTEs | Medium - reduces intermediate rows |
| **Avoid SELECT *** | Always | High - reduces bytes processed |
| **Use INT64 for joins** | Join keys | Medium - faster than STRING |
| **Materialize intermediate** | Reused CTEs | Medium - avoids recomputation |
| **Approximate aggregates** | Large cardinality (HLL++) | High - `APPROX_COUNT_DISTINCT()` |

#### Cost Estimation
```sql
-- Dry run to estimate bytes processed
-- In BigQuery UI: "Query settings" → "Dry run"
-- Or CLI: bq query --dry_run "SELECT ..."

-- Rule of thumb: 1 TB processed = ~$5-6
-- Optimize to stay under 100 GB per query when possible
```

---

### 💪 Practice Problems (Advanced)

#### Set A: Complex Window Functions (1-5)

1. **Moving Average with Gap Handling**
   > 7-day moving average of daily revenue, treating missing days as 0
   ```sql
   -- Generate date spine, LEFT JOIN, then AVG() OVER with frame
   ```

2. **Customer Lifetime Value Tiers**
   > Assign each customer to quintile (NTILE(5)) based on LTV, show tier transitions over time
   ```sql
   -- NTILE() OVER (PARTITION BY year ORDER BY ltv)
   ```

3. **First/Last Touch Attribution**
   > For each conversion, attribute to first and last marketing touchpoint
   ```sql
   -- FIRST_VALUE/LAST_VALUE with proper frame clause
   ```

4. **Session-Based Metrics**
   > For each session: duration, event count, bounce flag (1 event), conversion flag
   ```sql
   -- Sessionization + aggregation per session_id
   ```

5. **Running Retention**
   > Day 1, Day 7, Day 30 retention for each cohort week
   ```sql
   -- Cohort table + conditional aggregation with CASE
   ```

#### Set B: CTE Mastery (6-10)

6. **Multi-Step Data Pipeline**
   > Raw events → Clean → Sessionize → Aggregate daily → Calculate WoW growth
   ```sql
   -- 4-5 CTE levels, each with single responsibility
   ```

7. **Recursive: Bill of Materials**
   > Explode product hierarchy: final product → components → sub-components
   ```sql
   -- RECURSIVE CTE with quantity multiplication
   ```

8. **Data Quality Dashboard Query**
   > One query: null rates, duplicate rates, outlier counts, freshness per table
   ```sql
   -- UNION ALL multiple checks, pivot for readability
   ```

9. **Incremental Load Pattern**
   > Select only new/changed records since last run (using watermark table)
   ```sql
   -- MAX(updated_at) from target, filter source
   ```

10. **Self-Join Alternative with Windows**
    > Find users active in both Jan and Feb (without self-join)
    ```sql
    -- SUM(CASE WHEN month=1 THEN 1 END) OVER (PARTITION BY user_id)
    ```

#### Set C: BigQuery Specialties & Optimization (11-15)

11. **ARRAY_AGG with Ordering**
    > User's last 5 events as ordered array of structs
    ```sql
    -- ARRAY_AGG(STRUCT(...) ORDER BY timestamp DESC LIMIT 5)
    ```

12. **QUALIFY for Top-N-Per-Group**
    > Top 3 products per category by revenue (single query, no CTE)
    ```sql
    -- ROW_NUMBER() OVER (PARTITION BY category ORDER BY revenue DESC)
    -- QUALIFY rn <= 3
    ```

13. **Optimize This Query**
    > Given: `SELECT * FROM large_table WHERE date > '2024-01-01' AND customer_id IN (subquery)`
    > Fix: Partition pruning + clustering + EXISTS instead of IN
    ```sql
    -- Rewrite with partition filter first, EXISTS, explicit columns
    ```

14. **Approximate Distinct Count**
    > Estimate unique users per day for 1B row table
    ```sql
    -- APPROX_COUNT_DISTINCT(user_id) with 95% confidence
    ```

15. **Pivot for Executive Dashboard**
    > Transform: date, metric_name, metric_value → date, dau, mau, revenue, churn_rate
    ```sql
    -- PIVOT with multiple aggregations
    ```

---

### ⚡ Google Interview Advanced Patterns

#### Pattern 1: "Running Difference with Reset"
```sql
-- Track streak of consecutive active days
WITH daily_activity AS (
  SELECT user_id, DATE(event_timestamp) as active_date
  FROM events
  GROUP BY user_id, active_date
),
with_lag AS (
  SELECT
    user_id,
    active_date,
    LAG(active_date) OVER (PARTITION BY user_id ORDER BY active_date) as prev_date
  FROM daily_activity
),
streaks AS (
  SELECT
    user_id,
    active_date,
    CASE
      WHEN DATE_DIFF(active_date, prev_date, DAY) = 1 THEN 0
      ELSE 1 END as streak_reset
  FROM with_lag
),
streak_ids AS (
  SELECT
    user_id,
    active_date,
    SUM(streak_reset) OVER (PARTITION BY user_id ORDER BY active_date) as streak_id
  FROM streaks
)
SELECT user_id, streak_id, COUNT(*) as streak_length
FROM streak_ids
GROUP BY user_id, streak_id
ORDER BY streak_length DESC;
```

#### Pattern 2: "Funnel with Drop-off Points"
```sql
WITH funnel_steps AS (
  SELECT
    user_id,
    MAX(CASE WHEN event = 'view' THEN 1 ELSE 0 END) as step1_view,
    MAX(CASE WHEN event = 'cart' THEN 1 ELSE 0 END) as step2_cart,
    MAX(CASE WHEN event = 'purchase' THEN 1 ELSE 0 END) as step3_purchase
  FROM events
  WHERE event IN ('view', 'cart', 'purchase')
  GROUP BY user_id
)
SELECT
  SUM(step1_view) as viewers,
  SUM(step2_cart) as carters,
  SUM(step3_purchase) as purchasers,
  SUM(step2_cart)/NULLIF(SUM(step1_view),0) as view_to_cart,
  SUM(step3_purchase)/NULLIF(SUM(step2_cart),0) as cart_to_purchase
FROM funnel_steps;
```

#### Pattern 3: "Gap Filling with Last Known Value"
```sql
-- Fill missing dates with last known value (forward fill)
WITH date_spine AS (
  SELECT generate_date_array('2024-01-01', '2024-12-31', INTERVAL 1 DAY) as dt
),
data AS (
  SELECT date, value FROM metrics
),
joined AS (
  SELECT d.dt, m.value
  FROM date_spine d
  LEFT JOIN data m ON d.dt = m.date
)
SELECT
  dt,
  LAST_VALUE(value IGNORE NULLS) OVER (ORDER BY dt ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as filled_value
FROM joined;
```

---

### 🏋️ Day 2 Practice Routine

| Time | Activity |
|------|----------|
| 0:00-0:30 | Review window function syntax, write from memory |
| 0:30-1:30 | Solve Problems 1-15 (timed) |
| 1:30-2:00 | Study solutions, focus on QUALIFY, ARRAY, RECURSIVE |
| 2:00-2:30 | Re-solve 5 hardest without reference |
| 2:30-3:00 | Practice explaining optimization choices out loud |

---

### ✅ Day 2 Completion Checklist
- [ ] All 15 advanced problems solved
- [ ] Can write recursive CTE from memory
- [ ] QUALIFY clause usage fluent
- [ ] ARRAY_AGG/STRUCT/UNNEST comfortable
- [ ] Can explain partition/clustering optimization
- [ ] BigQuery date functions: DATE_TRUNC, DATE_ADD, DATE_DIFF, GENERATE_DATE_ARRAY

---

### 📝 Notes Space
```
Window function patterns to remember:
______________________________________________________________________________

Optimization techniques for Google-scale data:
______________________________________________________________________________

Queries that were tricky:
______________________________________________________________________________
```

---

### 🔗 Resources
- [BigQuery Window Functions](https://cloud.google.com/bigquery/docs/reference/standard-sql/window-function-calls)
- [BigQuery QUALIFY Clause](https://cloud.google.com/bigquery/docs/reference/standard-sql/query-syntax#qualify_clause)
- [BigQuery Arrays & Structs](https://cloud.google.com/bigquery/docs/reference/standard-sql/array-functions)
- [SQL Performance Tuning](https://cloud.google.com/bigquery/docs/best-practices-performance-overview)

---

*Next: DAY_3_SPREADSHEETS.md - Pivot tables, VLOOKUP/XLOOKUP, data cleaning, dashboarding*