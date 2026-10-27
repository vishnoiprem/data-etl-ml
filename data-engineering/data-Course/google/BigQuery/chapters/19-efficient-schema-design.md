# 3.5 — Design an Efficient Schema

> **Section 3 · Running Queries with Various Query Settings · Lecture 3.7 · 5:09**

## 🎯 What you will learn

- How column type choice affects storage and query cost
- The type-by-type decision framework
- Column naming conventions that scale
- Required vs nullable, and why `NOT NULL` is a performance feature

---

## 🧠 Concept

Schema design in BigQuery is not a formality — it directly determines bytes scanned, and bytes
scanned determine cost. A 10% schema improvement is a 10% cost reduction, forever, on every query.

### The cost model

```
Cost = (bytes of referenced columns) × (number of rows read) × $6.25 / TiB
```

You control the first term through schema design, and the second through partitioning and
clustering.

### The type decision framework

| Logical type | Use | Avoid | Why |
|--------------|-----|-------|-----|
| Monetary amount | `NUMERIC(p, s)` | `FLOAT64` | Exact decimal arithmetic; FLOAT64 has binary rounding error |
| Count / ID | `INT64` | `FLOAT64` | Smaller, exact, 8 bytes vs 8 but no float semantics |
| Ratio / percentage | `FLOAT64` or `NUMERIC` | `STRING` | String requires parsing at query time |
| Event timestamp | `TIMESTAMP` | `STRING`, `DATETIME` | Native time functions, partitioning support |
| Calendar date | `DATE` | `STRING`, `TIMESTAMP` | Smaller, semantically correct, partitionable |
| Local wall time | `DATETIME` | `TIMESTAMP` | No timezone confusion |
| Boolean | `BOOL` | `STRING` | `'true'`/`'false'` are 4-5 bytes + parse cost |
| Enum / category | `STRING` (or `INT64` + lookup) | | Filtering on short strings is cheap |
| Free text | `STRING` | | |
| Semi-structured | `JSON` | `STRING` | Native functions, better compression |

### 💡 `NUMERIC` vs `FLOAT64` — the rule that matters most

```sql
-- ❌ WRONG — floating point
SELECT 0.1 + 0.2 = 0.3;              -- FALSE

-- ❌ WRONG — FLOAT64 money
SELECT CAST(19.99 AS FLOAT64);       -- 19.990000000000002
SELECT SUM(amount) FROM orders;      -- 1234.5600000000001

-- ✅ CORRECT — NUMERIC
SELECT CAST(19.99 AS NUMERIC);       -- 19.99
SELECT SUM(amount) FROM orders;      -- 1234.56
```

⚠️ **Never use `FLOAT64` for money, quantities that must be exact, or anything you will sum.**
This is not a style preference — it produces wrong financial reports that are very hard to debug
later.

### Type sizes and storage

| Type | Storage | Notes |
|------|---------|-------|
| `BOOL` | 1 byte | |
| `INT64` | 8 bytes | Compresses well with dictionary encoding |
| `FLOAT64` | 8 bytes | |
| `NUMERIC` | 8-16 bytes | Precision-dependent |
| `DATE` | 4 bytes | |
| `DATETIME` | 8 bytes | |
| `TIMESTAMP` | 8 bytes | |
| `STRING` | variable | Dictionary + front coding |

💡 **The biggest storage lever is `STRING` on high-cardinality columns.** A column of 1M unique
UUID strings barely compresses. A column of 1M values from a set of 20 categories compresses
enormously. If you have a high-cardinality string column that is never filtered on, consider
hashing it into an `INT64` — but only if you never need to join it back to the original.

---

## 🧠 Required vs Nullable

```sql
CREATE TABLE `YOUR_PROJECT_ID.curated.orders` (
    order_id      STRING    NOT NULL,   -- always present, always non-NULL
    customer_id   STRING    NOT NULL,
    order_date    DATE      NOT NULL,   -- partition column — must be non-NULL
    order_ts      TIMESTAMP,           -- nullable — genuinely sometimes missing
    total_amount  NUMERIC(12,2) NOT NULL,
    status        STRING    NOT NULL,
    discount      NUMERIC(10,2)         -- nullable — new column, backfill pending
)
PARTITION BY order_date
CLUSTER BY customer_id, status;
```

Why `NOT NULL` matters:

1. **Correctness** — the schema documents the invariant
2. **Storage** — a nullable column needs a null bitmap; a required column does not
3. **Query safety** — `NOT NULL` prevents a "no rows" result from a NULL join key
4. **Partitioning** — a partition column must be `NOT NULL` (a NULL partition is a special
   "NULL partition" that breaks pruning)

⚠️ **A partition column must be `NOT NULL`.** BigQuery allows NULL in a partition column but
routes those rows to a special NULL partition, which breaks partition pruning and confuses
retention.

### Schema evolution and `NOT NULL`

```sql
-- Adding a NOT NULL column to a table with existing rows fails
ALTER TABLE `YOUR_PROJECT_ID.curated.orders`
ADD COLUMN discount NUMERIC(10,2) NOT NULL;
-- ❌ Error: Column discount cannot be added as REQUIRED

-- Correct: add it as nullable first, backfill, then it is effectively required
ALTER TABLE `YOUR_PROJECT_ID.curated.orders`
ADD COLUMN discount NUMERIC(10,2);
```

---

## 🧠 Column Naming Conventions

Consistency is not cosmetic — it makes your schemas self-documenting and your queries safe.

```sql
-- ✅ Good
order_id              -- primary key
customer_id           -- foreign key
order_date            -- _date suffix for DATE
order_ts              -- _ts for TIMESTAMP
is_completed          -- is_ prefix for BOOL
total_amount          -- descriptive, not amt
customer_lifetime_value_usd  -- unit suffix
order_count_30d       -- window suffix
```

```sql
-- ❌ Bad
id, oid, cid, dt, ts, amt, qty, flag
```

| Convention | Rule | Example |
|------------|------|---------|
| Primary keys | `<entity>_id` | `order_id` |
| Foreign keys | `<entity>_id` | `customer_id` |
| Dates | `_date` | `order_date` |
| Timestamps | `_ts` | `created_ts` |
| Booleans | `is_` / `has_` | `is_active` |
| Currency | `_usd` / `_eur` | `revenue_usd` |
| Counts | `_count` | `session_count` |
| Rates/ratios | `_rate` / `_pct` | `conversion_rate` |
| Avoid | SQL reserved words, `id` alone, abbreviations | |

💡 **Avoid SQL reserved words as column names.** `order`, `group`, `table`, `select` all need
backticks and cause friction. `order_id` is better than `order`.

---

## 🛠️ Hands-On: Compare Type Costs

### 1. Build two tables with different types

```sql
-- Table A: FLOAT64 money (wrong)
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.orders_float` AS
SELECT
    CAST(order_id AS STRING)         AS order_id,
    CAST(customer_id AS STRING)      AS customer_id,
    order_date,
    CAST(total_amount AS FLOAT64)    AS total_amount,
    status
FROM `YOUR_PROJECT_ID.raw.orders`
WHERE order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY);

-- Table B: NUMERIC money (right)
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.orders_numeric` AS
SELECT
    CAST(order_id AS STRING)         AS order_id,
    CAST(customer_id AS STRING)      AS customer_id,
    order_date,
    CAST(total_amount AS NUMERIC(12,2)) AS total_amount,
    status
FROM `YOUR_PROJECT_ID.raw.orders`
WHERE order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY);
```

### 2. Compare storage and scan cost

```sql
SELECT
    table_name,
    ROUND(size_bytes / POW(1024, 2), 2) AS size_mb,
    row_count
FROM `YOUR_PROJECT_ID.INFORMATION_SCHEMA.TABLES`
WHERE table_name IN ('orders_float', 'orders_numeric');
```

```sql
-- Measure the scan cost of each
SELECT
    job_id,
    ROUND((total_bytes_processed / POW(1024, 3)), 2) AS mb_processed
FROM `region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE job_type = 'QUERY'
  AND query LIKE '%orders_float%'
ORDER BY creation_time DESC LIMIT 1;
```

### 3. Test the arithmetic difference

```sql
-- FLOAT64 rounding error
SELECT
    SUM(total_amount) AS float_sum,
    COUNTIF(total_amount != ROUND(total_amount, 2)) AS imprecise_rows
FROM `YOUR_PROJECT_ID.curated.orders_float`;

-- NUMERIC exact
SELECT
    SUM(total_amount) AS numeric_sum,
    COUNTIF(total_amount != ROUND(total_amount, 2)) AS imprecise_rows
FROM `YOUR_PROJECT_ID.curated.orders_numeric`;
```

### 4. Measure the effect of column pruning

```sql
-- Broad
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders_numeric`;   -- reads all columns

-- Narrow
SELECT COUNT(order_id) FROM `YOUR_PROJECT_ID.curated.orders_numeric`;  -- reads one column
```

Compare `total_bytes_processed` between the two.

### 5. Add a description to every column

```sql
ALTER TABLE `YOUR_PROJECT_ID.curated.orders_numeric`
ALTER COLUMN total_amount SET OPTIONS (description = "Order total in USD, exact decimal");

ALTER TABLE `YOUR_PROJECT_ID.curated.orders_numeric`
ALTER COLUMN order_date SET OPTIONS (description = "Date the order was placed (UTC calendar date)");
```

💡 **Column descriptions are free documentation.** They show up in the console schema view, in
Data Catalog, and in the Python client. Writing them takes 30 seconds per column and saves hours
of "what does this field mean?" for the next person.

---

## 💡 Production Notes

- **Standardize types across the warehouse.** If `amount` is `FLOAT64` in one table and `NUMERIC`
  in another, every join between them needs a cast — and casts in the SELECT list prevent
  predicate pushdown.
- **Use `STRING` for identifiers, `INT64` for surrogate keys.** Surrogate integer keys compress far
  better and cluster more effectively.
- **Avoid `FLOAT64` for anything requiring exact equality** — money, IDs, quantities.
- **Do not store timestamps as strings.** String timestamps block partitioning, break time
  functions, and waste bytes.
- **Use `JSON` over `STRING` for semi-structured data** — it is faster to query, compresses
  better, and supports `JSON_VALUE`/`JSON_QUERY` pushdown.

---

## 🔑 Key Takeaways

- Schema design directly controls bytes scanned, which directly controls cost.
- **`NUMERIC` for money. Never `FLOAT64`.** Float arithmetic produces wrong totals.
- `TIMESTAMP` for event times, `DATE` for calendar dates, `DATETIME` for local wall time.
- `NOT NULL` is a correctness and performance feature; partition columns must be `NOT NULL`.
- Consistent naming (`order_id`, `order_date`, `is_completed`, `revenue_usd`) makes schemas
  self-documenting.
- Column descriptions are free documentation — always write them.
- High-cardinality strings compress poorly; consider `INT64` surrogate keys.

---

## 📚 Practice Exercises

1. **Type audit.** Take this schema and rewrite it with the correct types, naming, and modes:
   ```
   id: STRING
   cust: STRING
   dt: STRING
   total: FLOAT64
   flag: STRING
   items: STRING
   meta: STRING
   ```
   Justify every change.

2. **Cost measurement.** Create a 10-column table where one column is a 1M-distinct-value UUID
   string. Measure its contribution to table size. Then test the `INT64` hash alternative and
   measure again.

3. **Evolution plan.** Design the safe sequence for adding a `NOT NULL` column to a 5 TB table
   with 3 years of history. Include the exact DDL, the backfill query, the validation query, and
   how you avoid rewriting the table.

4. **Standardization.** Write a query that finds every table in your project and reports columns
   whose names violate your naming convention. This is your schema-lint monitor.

5. **Arithmetic proof.** Demonstrate the exact difference between `FLOAT64` and `NUMERIC` for a
   large sum of realistic invoice amounts, and show the magnitude of the error.

---

## 📖 Further Reading

- BigQuery data types — https://cloud.google.com/bigquery/docs/reference/standard-sql/data-types
- Column and table constraints — https://cloud.google.com/bigquery/docs/column-constraints
- Storage-optimized schemas — https://cloud.google.com/bigquery/docs/storage-optimization
