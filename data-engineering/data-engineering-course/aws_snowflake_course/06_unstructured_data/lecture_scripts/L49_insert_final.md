---
l_id: L49
title: "Insert final data"
duration: "7:00"
prereqs:
  - L48 (Flatten hierarchical data)
---

# L49 — Insert final data

> **Section:** 6 — Loading unstructured data
> **Duration:** 7:00

## Prereqs

- L48 — Flatten hierarchical data

## Key terms

- **`CREATE TABLE AS SELECT` (CTAS)** — atomically creates a table
  from a `SELECT`. The new table is empty before the statement runs;
  you cannot incrementally add to it.
- **`INSERT INTO … SELECT`** — adds rows to an existing table.
  Idempotent if you filter on a key.
- **MERGE** — upsert pattern. Covered later in the course; this
  section uses plain `INSERT`.

## Lecture

This is the **last lecture of section 6** — the moment the parsed
JSON becomes the analytics-ready curated tables. You have two
options: `CREATE TABLE AS SELECT` (CTAS) for a clean rebuild, or
`INSERT INTO … SELECT` for an incremental load. Both produce the
same rows; the difference is how they behave when you re-run them.

### Step 1 — the curated **orders** (1 row per order)

```sql
CREATE OR REPLACE TABLE curated_orders AS
SELECT
    raw:order_id::STRING                       AS order_id,
    raw:order_ts::TIMESTAMP_LTZ                AS order_ts,
    raw:customer.id::STRING                    AS customer_id,
    raw:customer.name::STRING                  AS customer_name,
    raw:customer.email::STRING                 AS customer_email,
    raw:customer.address.city::STRING          AS city,
    raw:customer.address.country::STRING       AS country,
    raw:total::NUMBER(10, 2)                   AS total,
    raw:currency::STRING                       AS currency,
    raw:payment.method::STRING                 AS payment_method,
    raw:payment.last4::STRING                  AS payment_last4,
    ARRAY_SIZE(raw:line_items)                 AS line_count,
    loaded_at
FROM raw_orders;
```

`CREATE OR REPLACE TABLE … AS SELECT …` is **atomic** and
**idempotent** — re-running it gives you a fresh table with the
same shape. The `loaded_at` default column carries through from
`raw_orders`.

### Step 2 — the curated **line_items** (1 row per item)

```sql
CREATE OR REPLACE TABLE curated_line_items AS
SELECT
    raw:order_id::STRING                       AS order_id,
    raw:customer.id::STRING                    AS customer_id,
    raw:order_ts::TIMESTAMP_LTZ                AS order_ts,
    f.value:sku::STRING                        AS sku,
    f.value:qty::NUMBER(2, 0)                  AS qty,
    f.value:price::NUMBER(10, 2)               AS price,
    f.value:price::NUMBER(10, 2)
        * f.value:qty::NUMBER(2, 0)            AS line_total,
    raw:currency::STRING                       AS currency
FROM raw_orders,
     LATERAL FLATTEN(input => raw:line_items) f;
```

### Step 3 — incremental inserts (the production pattern)

In production, you rarely want to blow away the curated table every
night. Instead, **append** new rows from new files:

```sql
INSERT INTO curated_orders (order_id, order_ts, customer_id, …)
SELECT
    raw:order_id::STRING                       AS order_id,
    raw:order_ts::TIMESTAMP_LTZ                AS order_ts,
    raw:customer.id::STRING                    AS customer_id,
    …
FROM raw_orders
WHERE loaded_at > (SELECT COALESCE(MAX(loaded_at), '1900-01-01'::TIMESTAMP_LTZ)
                   FROM curated_orders);
```

That `WHERE loaded_at > (SELECT MAX(loaded_at) …)` is the
**watermark pattern** — it inserts only rows that arrived after
the last successful curated insert. It's the basis of every
Snowflake pipeline that handles append-only JSON.

### Step 4 — sanity check

```sql
SELECT
    (SELECT COUNT(*) FROM curated_orders)        AS n_orders,
    (SELECT COUNT(*) FROM curated_line_items)   AS n_line_items;
```

The two counts must satisfy:

- `n_line_items = SUM(line_count)` — every line item became a row.
- `n_orders <= (SELECT COUNT(*) FROM raw_orders)` — you can have
  fewer (e.g. `WHERE` filters), but never more.

If `n_orders` is zero, your `WHERE` predicate is too aggressive.
If `n_orders` is the same as `raw_orders` but `n_line_items` is
zero, you forgot the `LATERAL FLATTEN`.

### Step 5 — sample queries

The whole point of curating is that you can now run regular SQL:

```sql
-- Top cities by total revenue
SELECT
    country,
    city,
    SUM(total)            AS revenue,
    COUNT(*)              AS n_orders
FROM curated_orders
GROUP BY country, city
ORDER BY revenue DESC
LIMIT 10;

-- Average line item value per customer
SELECT
    customer_id,
    customer_name,
    COUNT(DISTINCT order_id) AS n_orders,
    AVG(line_total)          AS avg_line_total
FROM curated_line_items
GROUP BY customer_id, customer_name
ORDER BY avg_line_total DESC
LIMIT 10;
```

Notice there is **no `VARIANT`** anywhere in those queries.
The curated tables are ordinary SQL.

### Section recap

You have built a complete JSON-to-curated pipeline:

```text
orders.json (stage)
   ↓  COPY INTO
raw_orders (VARIANT)
   ↓  parse + FLATTEN
curated_orders   +   curated_line_items
```

Three tables, one file format object, one stage. This pattern
will reappear in **Section 7 (Parquet)**, **Section 8 (S3)**, and
**Section 9 (Azure)** — the only thing that changes is the source
bucket.

## Hands-on

Run the two `CREATE TABLE AS SELECT` statements, then run the two
sample queries. Save the SQL into `code/parse_json.sql` for
reference; you will be modifying it in the next section to load
**Parquet** instead of JSON.

## Quiz prep

- What is the difference between CTAS and `INSERT … SELECT`?
- What does the watermark `WHERE loaded_at > MAX(loaded_at)`
  pattern guarantee?
- Why must `n_line_items = SUM(line_count)`?

## Key takeaways

- `CREATE OR REPLACE TABLE AS SELECT` is the **atomic, idempotent**
  way to rebuild a curated table.
- `INSERT INTO … SELECT … WHERE loaded_at > MAX(loaded_at)` is
  the **incremental watermark pattern** for append-only JSON.
- The whole point of curating is that the rest of the warehouse
  reads **typed SQL**, not `VARIANT`.

## What's next

In **Section 7 — Performance optimization** we'll load the same
data as **Parquet** (columnar binary), set up a dedicated
warehouse, and learn the three caches Snowflake uses to make the
same query faster the second time.