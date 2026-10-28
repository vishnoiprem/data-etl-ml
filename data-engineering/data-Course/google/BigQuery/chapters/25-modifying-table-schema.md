# 3.8 — Modifying Table Schema

> **Section 3 · Running Queries with Various Query Settings · Lectures 3.11–3.12 · 7:04 + 9:10**

## 🎯 What you can learn

- The complete `ALTER TABLE` reference — add, drop, rename, alter, set options
- Which schema changes are cheap and which rewrite the whole table
- Flexible column names and how to use them
- The safe schema evolution procedure

---

## 🧠 Concept

BigQuery's schema evolution is unusually flexible. It can also be surprisingly expensive, because
some changes trigger a **full table rewrite**.

### The complete ALTER TABLE syntax

```sql
ALTER TABLE [IF EXISTS] table_name
ALTER COLUMN column_name
  [SET OPTIONS (...)]
  [DROP NOT NULL]
  [SET DATA TYPE type]
  [RENAME TO new_name]

ALTER TABLE [IF EXISTS] table_name
ADD COLUMN [IF NOT EXISTS] column_name column_schema
  [OPTIONS (...)]
  [DEFAULT default_value]

ALTER TABLE [IF EXISTS] table_name
DROP COLUMN [IF EXISTS] column_name

ALTER TABLE [IF EXISTS] table_name
RENAME COLUMN column_name TO new_column_name

ALTER TABLE [IF EXISTS] table_name
RENAME TO new_table_name

ALTER TABLE [IF EXISTS] table_name
SET OPTIONS (table_option_list)
```

### Cost classification — the critical knowledge

| Change | Rewrites the table? | Cost | Notes |
|--------|---------------------|------|-------|
| `ADD COLUMN` (nullable) | ❌ No | Free | Metadata only |
| `ADD COLUMN` (with DEFAULT) | ❌ No | Free | Metadata only |
| `DROP COLUMN` | ❌ No | Free | Metadata only |
| `RENAME COLUMN` | ❌ No | Free | Metadata only |
| `RENAME TO` | ❌ No | Free | Metadata only |
| `SET OPTIONS` (labels, description) | ❌ No | Free | Metadata only |
| `SET OPTIONS` (partition/clustering) | ✅ Yes | **Full rewrite** | Expensive |
| `DROP NOT NULL` | ✅ Yes | **Full rewrite** | |
| `ALTER COLUMN SET DATA TYPE` | ✅ Yes | **Full rewrite** | Usually forbidden |

💡 **The rule:** adding, dropping, and renaming columns are **free metadata operations**. Anything
that changes the physical layout — adding or removing `NOT NULL`, changing data types, changing
partitioning or clustering — **rewrites the entire table** and is billed as such.

⚠️ **A table rewrite on a 5 TB table costs real money and takes real time.** For a
`CAPACITY_OPTIMIZED` table it also changes the billing model back to standard.

---

## 🧠 Flexible Column Names

BigQuery allows a wide range of characters in column names — spaces, hyphens, emojis — as long as
the name is 1–300 characters and contains no control characters.

```sql
-- ✅ Valid but requires backticks everywhere
ALTER TABLE `YOUR_PROJECT_ID.raw.events`
ADD COLUMN `order-id` STRING;

SELECT `order-id` FROM `YOUR_PROJECT_ID.raw.events`;
```

```sql
-- ✅ The clean way to reference them
SELECT
    `order-id` AS order_id
FROM `YOUR_PROJECT_ID.raw.events`;
```

💡 **Flexible names are a feature for ingesting messy third-party data** — you can preserve the
source column names exactly rather than renaming during load. But **normalize the names in the
curated layer**. Downstream queries against `"order-id"` are miserable.

---

## 🛠️ Hands-On

### 1. Add a column (free)

```sql
ALTER TABLE `YOUR_PROJECT_ID.curated.orders`
ADD COLUMN discount NUMERIC(10,2) OPTIONS (description = "Order-level discount in USD");
```

```sql
-- Add with a default
ALTER TABLE `YOUR_PROJECT_ID.curated.orders`
ADD COLUMN source_channel STRING DEFAULT 'unknown'
OPTIONS (description = "Acquisition channel");
```

```sql
-- Add multiple columns at once
ALTER TABLE `YOUR_PROJECT_ID.curated.orders`
ADD COLUMN IF NOT EXISTS currency STRING DEFAULT 'USD',
ADD COLUMN IF NOT EXISTS exchange_rate NUMERIC(18,8),
ADD COLUMN IF NOT EXISTS base_amount NUMERIC(14,2);
```

### 2. Drop a column (free, but destroys the data)

```sql
ALTER TABLE `YOUR_PROJECT_ID.curated.orders`
DROP COLUMN IF EXISTS legacy_status;
```

⚠️ **`DROP COLUMN` is irreversible** (except via time travel within 7 days). The data is gone.

### 3. Rename a column (free)

```sql
ALTER TABLE `YOUR_PROJECT_ID.curated.orders`
RENAME COLUMN customer_id TO cust_id;
```

```sql
-- Rename the table itself
ALTER TABLE `YOUR_PROJECT_ID.curated.orders`
RENAME TO orders_v2;
```

### 4. Change column options (free)

```sql
ALTER TABLE `YOUR_PROJECT_ID.curated.orders`
ALTER COLUMN status SET OPTIONS (
  description = "Order lifecycle status: pending|completed|cancelled|refunded"
);

-- Set the policy tag for governance
ALTER TABLE `YOUR_PROJECT_ID.curated.orders`
ALTER COLUMN email SET OPTIONS (
  policy_tags = ('YOUR_PROJECT_ID.security.pii_email')
);
```

### 5. Drop NOT NULL (⚠️ rewrites the table)

```sql
-- ⚠️ This rewrites the entire table
ALTER TABLE `YOUR_PROJECT_ID.curated.orders`
ALTER COLUMN status DROP NOT NULL;
```

### 6. Change table options

```sql
-- Add labels and a description (free)
ALTER TABLE `YOUR_PROJECT_ID.curated.orders`
SET OPTIONS (
  description = "Curated order line items with customer and pricing detail",
  labels = [('tier', 'silver'), ('owner', 'data-eng'), ('reviewed', '2026-10')]
);

-- Set partition expiration (⚠️ rewrites the table)
ALTER TABLE `YOUR_PROJECT_ID.curated.orders`
SET OPTIONS (partition_expiration_days = 730);
```

### 7. The safe schema evolution procedure

```sql
-- ══════════════════════════════════════════════════════════
-- STEP 1: ADD the column as nullable (free, instant)
-- ══════════════════════════════════════════════════════════
ALTER TABLE `YOUR_PROJECT_ID.curated.orders`
ADD COLUMN IF NOT EXISTS discount NUMERIC(10,2);

-- ══════════════════════════════════════════════════════════
-- STEP 2: Backfill it in bounded batches
--    (a full-table UPDATE rewrites everything — do it in chunks)
-- ══════════════════════════════════════════════════════════
DECLARE offset_value INT64 DEFAULT 0;
DECLARE batch_size INT64 DEFAULT 100000;

WHILE offset_value < (SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders`) DO
    EXECUTE IMMEDIATE FORMAT(
        "UPDATE `YOUR_PROJECT_ID.curated.orders`
         SET discount = (
             SELECT SUM(COALESCE(item.discount, 0))
             FROM UNNEST(line_items) AS item
         )
         WHERE order_id IN (
             SELECT order_id
             FROM `YOUR_PROJECT_ID.curated.orders`
             ORDER BY order_id
             LIMIT %s OFFSET %s
         )", batch_size, offset_value
    );
    SET offset_value = offset_value + batch_size;
END WHILE;
```

⚠️ **DML on BigQuery mutates in place and rewrites the affected data blocks.** A full-table
`UPDATE` on a 5 TB table is expensive and slow. Batch it, or use a CTAS + swap instead:

```sql
-- ══════════════════════════════════════════════════════════
-- BETTER: CTAS into a new table, then swap
-- ══════════════════════════════════════════════════════════
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.orders_new`
PARTITION BY order_date
CLUSTER BY customer_id, status
AS
SELECT
    o.* EXCEPT (discount),
    COALESCE(
        o.discount,
        (SELECT SUM(COALESCE(item.discount, 0))
         FROM UNNEST(o.line_items) AS item)
    ) AS discount
FROM `YOUR_PROJECT_ID.curated.orders` AS o;

-- Swap atomically
DROP TABLE `YOUR_PROJECT_ID.curated.orders`;
ALTER TABLE `YOUR_PROJECT_ID.curated.orders_new` RENAME TO orders;
```

💡 **The CTAS + swap pattern is almost always better than DML for bulk backfills.** It is
parallel, it is cheaper, and it leaves the original intact until the swap.

### 8. Verify the evolution

```sql
-- Check the schema
SELECT column_name, data_type, is_nullable, description
FROM `YOUR_PROJECT_ID.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'orders'
ORDER BY ordinal_position;

-- Check for NULLs in the new column
SELECT
    COUNT(*) AS total_rows,
    COUNTIF(discount IS NULL) AS null_rows,
    COUNTIF(discount IS NOT NULL) AS populated_rows
FROM `YOUR_PROJECT_ID.curated.orders`;
```

---

## 💡 Production Notes

- **Adding a nullable column with a default is free and instant.** There is no need to rewrite
  data — the default is materialized at read time.
- **`DROP NOT NULL` on a partitioned table is a full rewrite.** Budget for it.
- **`ALTER TABLE SET OPTIONS` for partitioning/clustering rewrites the table.** The more
  expensive the table, the longer this takes — plan it as a maintenance operation.
- **Prefer CTAS + swap over DML for anything touching more than a few million rows.**
- **After any schema change, update the downstream views.** A view that references a renamed
  column breaks immediately. BigQuery does *not* cascade renames to dependent views.

---

## 🔑 Key Takeaways

- `ADD COLUMN`, `DROP COLUMN`, `RENAME COLUMN`, `RENAME TO`, `SET OPTIONS` (metadata) are **free
  metadata operations**.
- `DROP NOT NULL`, `SET DATA TYPE`, and changing partitioning/clustering **rewrite the whole
  table** and cost accordingly.
- BigQuery supports flexible column names (spaces, hyphens) — use them at ingestion, normalize at
  the curated layer.
- **For bulk backfills, use CTAS + atomic swap, not DML** — it is faster, cheaper, and safer.
- Schema changes **do not cascade** to dependent views. Audit and update them.

---

## 📚 Practice Exercises

1. **Cost classification.** For each alteration, state whether it rewrites the table and estimate
   the cost on a 5 TB table:
   - `ADD COLUMN x STRING`
   - `ADD COLUMN x STRING DEFAULT 'a'`
   - `DROP COLUMN x`
   - `RENAME COLUMN x TO y`
   - `ALTER COLUMN x DROP NOT NULL`
   - `SET OPTIONS (partition_expiration_days = 30)`
   - `SET OPTIONS (labels = [...])`

2. **Safe evolution plan.** Design the complete, zero-downtime procedure for adding a
   `NOT NULL` `discount NUMERIC(10,2)` column to a 5 TB table with 200 dependent views. Include
   ordering, batching, validation, and the view-update strategy.

3. **Batch update.** Write a parameterized script that updates a table in batches of N rows using
   a keyset pagination pattern (not `OFFSET`, which gets slower as you advance). Explain why
   keyset pagination is better here.

4. **DDL diff.** Write a script that compares the schema of two tables via
   `INFORMATION_SCHEMA.COLUMNS` and generates the exact `ALTER TABLE` statements to make table B
   match table A. This is your schema-drift detector.

5. **Flexible names.** Design a normalization pipeline that loads a third-party file with columns
   like `"Customer ID"`, `"order-date"`, and `"TOTAL $"` into a table with clean names, using only
   flexible naming plus a CTAS.

---

## 📖 Further Reading

- `ALTER TABLE` reference — https://cloud.google.com/bigquery/docs/reference/standard-sql/data-definition-language#alter_table_statement
- Schema evolution best practices — https://cloud.google.com/bigquery/docs/schema-evolution
- Flexible column names — https://cloud.google.com/bigquery/docs/reference/standard-sql/lexical#flexible_column_names
