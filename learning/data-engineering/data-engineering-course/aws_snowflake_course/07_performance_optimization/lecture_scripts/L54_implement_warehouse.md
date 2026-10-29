---
l_id: L54
title: "Implement dedicated virtual warehouse"
duration: "7:00"
prereqs:
  - L53 (Create dedicated virtual warehouse)
---

# L54 — Implement dedicated virtual warehouse

> **Section:** 7 — Performance optimization
> **Duration:** 7:00

## Prereqs

- L53 — Create dedicated virtual warehouse

## Key terms

- **`USE WAREHOUSE`** — session-level command that switches the
  active warehouse. All subsequent `COPY INTO` and `SELECT` runs
  on it.
- **Per-session warehouse pinning** — set the warehouse inside
  a stored procedure or task so the workload is always on the
  right size.
- **Query profile** — Snowflake's per-query breakdown showing
  which warehouse ran it, how long, and how many bytes scanned.

## Lecture

In L53 we **created** the four warehouses. This lecture wires
them into the actual ETL pipeline so `loading_wh` runs the
`COPY INTO` from L51, `transform_wh` runs the `INSERT …
SELECT` from L49, and `bi_wh` runs the dashboard queries. The
change is one line at the top of each script.

### Step 1 — load the JSON on `loading_wh`

```sql
USE WAREHOUSE loading_wh;
USE DATABASE demo_db;
USE SCHEMA json_demo;

COPY INTO raw_orders (raw, filename, row_number)
FROM (
    SELECT $1, METADATA$FILENAME, METADATA$FILE_ROW_NUMBER
    FROM @stg_orders_json
)
FILE_FORMAT = (FORMAT_NAME = ff_json)
ON_ERROR    = CONTINUE;
```

`USE WAREHOUSE loading_wh` is the only change. The `COPY INTO`
statement is identical to L44. From this point forward, every
`COPY INTO` in our course lives in a `loading_wh`-prefixed
script.

### Step 2 — transform on `transform_wh`

```sql
USE WAREHOUSE transform_wh;
USE DATABASE demo_db;
USE SCHEMA json_demo;

CREATE OR REPLACE TABLE curated_line_items AS
SELECT
    raw:order_id::STRING                       AS order_id,
    raw:customer.id::STRING                    AS customer_id,
    raw:order_ts::TIMESTAMP_LTZ                AS order_ts,
    f.value:sku::STRING                        AS sku,
    f.value:qty::NUMBER(2, 0)                  AS qty,
    f.value:price::NUMBER(10, 2)               AS price,
    f.value:price::NUMBER(10, 2) * f.value:qty::NUMBER(2, 0) AS line_total,
    raw:currency::STRING                       AS currency
FROM raw_orders,
     LATERAL FLATTEN(input => raw:line_items) f;
```

Why a separate `transform_wh`?

- `transform_wh` can be **sized for ELT** (Large or X-Large)
  without affecting the loading time.
- It can run **concurrently** with another `transform_wh`
  cluster while `loading_wh` keeps loading. No queue.
- The **query profile** clearly shows "this is an ELT query" vs
  "this is a load", which is invaluable for cost allocation.

### Step 3 — dashboard on `bi_wh`

```sql
USE WAREHOUSE bi_wh;
USE DATABASE demo_db;
USE SCHEMA json_demo;

SELECT
    country,
    city,
    SUM(total)            AS revenue,
    COUNT(*)              AS n_orders
FROM curated_orders
GROUP BY country, city
ORDER BY revenue DESC
LIMIT 10;
```

A dashboard query is small and frequent. `bi_wh` is `Small` and
`AUTO_SUSPEND = 60`. A 2-minute gap between dashboards suspends
the warehouse; the next click resumes it in ~1 s.

### Step 4 — admin on `admin_wh`

```sql
USE WAREHOUSE admin_wh;

SHOW WAREHOUSES;
SELECT * FROM TABLE(INFORMATION_SCHEMA.WAREHOUSE_METERING_HISTORY(
    DATE_RANGE_START => DATEADD('day', -7, CURRENT_TIMESTAMP()),
    WAREHOUSE_NAME   => 'LOADING_WH'
));
```

Admin tasks (monitoring, grants, history queries) run on a
tiny `X-Small` so they don't compete with anything.

### Verify in the Query Profile

Open **Activity → Query History** in the Snowflake UI. For each
of the last few queries, confirm:

- **Warehouse column** matches the workload class.
- **Bytes scanned** is reasonable (Parquet should scan less than
  CSV for the same logical query).
- **Partitions scanned / total** is the micro-partition pruning
  ratio — aim for < 5% scanned on selective queries.

If you see a "wrong warehouse" on a query, check the
`USE WAREHOUSE` at the top of the script that ran it. Each
session is pinned until the next `USE` or until it ends.

### Programmatic pin inside a stored procedure

If you write a stored procedure, pin the warehouse inside it:

```sql
CREATE OR REPLACE PROCEDURE sp_load_orders()
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
    USE WAREHOUSE loading_wh;
    COPY INTO raw_orders … ;
    USE WAREHOUSE transform_wh;
    CREATE OR REPLACE TABLE curated_orders AS … ;
    RETURN 'OK';
END;
$$;
```

The `USE` statements are scoped to the procedure call, so the
caller's warehouse is restored on return. This is the
production pattern for "one job, multiple warehouses".

### Cost-allocation view

Finally, a query you'll come back to every Friday:

```sql
SELECT
    warehouse_name,
    SUM(credits_used)        AS credits,
    SUM(credits_used) * 4    AS approx_dollars   -- AWS list ~$4/credit
FROM TABLE(INFORMATION_SCHEMA.WAREHOUSE_METERING_HISTORY(
    DATE_RANGE_START => DATE_TRUNC('month', CURRENT_TIMESTAMP())
))
GROUP BY warehouse_name
ORDER BY credits DESC;
```

Now you can see exactly which workload is the credit hog. In
our setup, `transform_wh` typically dominates, which is why we
size it appropriately.

## Hands-on

Re-run the three scripts from L49 / L50 / L51, each preceded by
the matching `USE WAREHOUSE`. Open the Query History and confirm
each query ran on the expected warehouse.

## Quiz prep

- Why is "one warehouse per workload" cheaper than one big
  warehouse?
- Where in Snowflake can you see which warehouse a query ran on?
- What is the right warehouse size for a dashboard workload vs
  a nightly ELT workload?

## Key takeaways

- Wire the four warehouses into the pipeline with a `USE
  WAREHOUSE` at the top of each script.
- Pin the warehouse **inside** a stored procedure so the caller's
  session is unaffected.
- `INFORMATION_SCHEMA.WAREHOUSE_METERING_HISTORY` gives you
  per-warehouse credit usage for cost allocation.
- The Query History tab is where you confirm "the right query
  ran on the right warehouse".

## What's next

In **L55 — Scaling up** we look at what happens when one query
is just plain slow: resize the warehouse from `Small` to
`Large` and watch the query profile change.