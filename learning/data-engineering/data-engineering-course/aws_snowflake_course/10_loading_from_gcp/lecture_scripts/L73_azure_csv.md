---
l_id: L73
title: "Load CSV file (Azure)"
duration: "6:00"
prereqs:
  - L72 (Create stage & test connection (Azure))
---

# L73 — Load CSV file (Azure)

> **Section:** 10 — Loading from GCP
> **Duration:** 6:00

## Prereqs

- L72 — Create stage & test connection (Azure)

## Key terms

- **`TYPE = CSV`** — file format for delimited text files.
- **`FIELD_OPTIONALLY_ENCLOSED_BY = '"'`** — handles CSV
  columns that are quoted (e.g. `"Ada Lovelace"`).
- **`SKIP_HEADER = 1`** — drops the first line (the column
  header).
- **`COMPRESSION = GZIP`** — automatically decompresses
  `.csv.gz` files. Azure often serves gzipped data.

## Lecture

We've loaded Parquet and JSON from S3 and Azure. This
lecture loads a **CSV** from the Azure container — the
classic delimited text file. The pattern is the same; the
file format is different.

### Step 1 — upload a CSV to the container

```bash
az storage blob upload \
    --container-name orders \
    --file code/orders.csv \
    --name raw/orders/2026-10-01/orders.csv \
    --account-name pvsfcourse2026 \
    --overwrite
```

`code/orders.csv` is a comma-delimited file with one order
per line:

```csv
order_id,order_ts,customer_id,customer_name,total,currency
ORD-1001,2026-10-01 12:34:56,C-42,"Ada Lovelace",149.97,USD
ORD-1002,2026-10-01 12:36:11,C-43,"Grace Hopper",29.99,USD
```

Notice the second row's customer name is **quoted**
(`"Ada Lovelace"`) because it contains a space.

### Step 2 — create a CSV file format

```sql
CREATE OR REPLACE FILE FORMAT ff_csv
    TYPE = CSV
    FIELD_DELIMITER = ','
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    COMPRESSION = GZIP
    NULL_IF = ('', 'NULL', 'null')
    EMPTY_FIELD_AS_NULL = TRUE
    TRIM_SPACE = TRUE;
```

Field-by-field:

- `FIELD_DELIMITER = ','` — the column separator.
- `SKIP_HEADER = 1` — drop the first line.
- `FIELD_OPTIONALLY_ENCLOSED_BY = '"'` — handle quoted
  columns; the parser ignores the quotes for unquoted
  fields.
- `COMPRESSION = GZIP` — automatically decompress
  `.csv.gz`.
- `NULL_IF` — interpret the strings `''`, `NULL`, and
  `null` as `NULL`.
- `EMPTY_FIELD_AS_NULL` — empty fields are `NULL`, not `''`.
- `TRIM_SPACE` — strip leading/trailing whitespace.

### Step 3 — create a CSV stage (or reuse)

```sql
CREATE OR REPLACE STAGE stg_orders_azure_csv
    STORAGE_INTEGRATION = azure_orders_int
    URL = 'azure://pvsfcourse2026.blob.core.windows.net/orders/raw/orders/'
    FILE_FORMAT = (FORMAT_NAME = ff_csv);
```

Same `STORAGE_INTEGRATION` as L72; only the file format
and stage name change.

### Step 4 — `LIST` to confirm

```sql
LIST @stg_orders_azure_csv;
```

Expected: the new `orders.csv` row, plus the existing
Parquet and JSON files. (The `LIST` doesn't care about the
file format; it lists everything in the prefix.)

### Step 5 — load with explicit column list

```sql
CREATE OR REPLACE TABLE raw_orders_csv (
    order_id       VARCHAR,
    order_ts       TIMESTAMP_LTZ,
    customer_id    VARCHAR,
    customer_name  VARCHAR,
    total          NUMBER(10, 2),
    currency       VARCHAR,
    filename       VARCHAR AS METADATA$FILENAME::VARCHAR,
    row_number     NUMBER  AS METADATA$FILE_ROW_NUMBER,
    loaded_at      TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);

COPY INTO raw_orders_csv (
    order_id, order_ts, customer_id, customer_name, total, currency,
    filename, row_number
)
FROM (
    SELECT
        $1::STRING,                              -- order_id
        $2::TIMESTAMP_LTZ,                       -- order_ts
        $3::STRING,                              -- customer_id
        $4::STRING,                              -- customer_name
        $5::NUMBER(10, 2),                       -- total
        $6::STRING,                              -- currency
        METADATA$FILENAME,
        METADATA$FILE_ROW_NUMBER
    FROM @stg_orders_azure_csv
)
FILE_FORMAT = (FORMAT_NAME = ff_csv)
ON_ERROR    = CONTINUE
PATTERN     = '.*[.]csv';
```

The `PATTERN = '.*[.]csv'` restricts the load to the CSV
file (otherwise the Parquet and JSON files would be
rejected with type errors).

### Step 6 — verify

```sql
SELECT * FROM raw_orders_csv LIMIT 5;
```

Expected: 5 rows with `order_id`, `order_ts`, `total`, etc.
properly parsed. The `customer_name` should be `Ada Lovelace`
(not `"Ada Lovelace"` with the quotes).

### Common CSV pitfalls

- **The header is not skipped.** Set `SKIP_HEADER = 1`.
- **Quoted fields break the parser.** Set
  `FIELD_OPTIONALLY_ENCLOSED_BY = '"'`.
- **Trailing whitespace** in fields. Set `TRIM_SPACE = TRUE`.
- **Mixed line endings** (`\r\n` on Windows, `\n` on Unix).
  Snowflake handles both, but check if the file has odd
  terminators.
- **Empty strings vs `NULL`.** Use `NULL_IF` and
  `EMPTY_FIELD_AS_NULL` to be explicit.

### Why CSV at all?

CSV is the **lingua franca** of data interchange. Every
tool can read it; every human can read it. The trade-off:

- **Pros**: universal, debuggable, easy to fix with `sed`.
- **Cons**: large files, no schema, slow to parse, no
  nested data.

For new pipelines, prefer Parquet (columnar) or JSON
(nested). Use CSV only when the source is CSV.

## Hands-on

Upload `orders.csv` to the container, run the
`CREATE FILE FORMAT`, the `LIST`, and the `COPY INTO`.
Verify the `customer_name` is unquoted.

## Quiz prep

- What does `FIELD_OPTIONALLY_ENCLOSED_BY` do?
- Why is `PATTERN = '.*[.]csv'` useful in this `COPY INTO`?
- What is the difference between `NULL_IF` and
  `EMPTY_FIELD_AS_NULL`?

## Key takeaways

- `TYPE = CSV` is the file format; `SKIP_HEADER = 1` and
  `FIELD_OPTIONALLY_ENCLOSED_BY = '"'` handle typical
  CSV quirks.
- `COMPRESSION = GZIP` automatically decompresses
  `.csv.gz`.
- The `COPY INTO` is the same shape as the JSON / Parquet
  versions; only `$1, $2, $3, …` change.
- Use `PATTERN` to load only the CSV from a mixed prefix.

## What's next

In **L74 — Load JSON file (Azure)** we extend the
pipeline to a gzipped JSON file in the same container
and verify the `STRIP_OUTER_ARRAY` setting.