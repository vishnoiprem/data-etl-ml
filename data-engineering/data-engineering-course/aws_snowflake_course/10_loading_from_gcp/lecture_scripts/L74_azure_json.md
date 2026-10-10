---
l_id: L74
title: "Load JSON file (Azure)"
duration: "6:00"
prereqs:
  - L73 (Load CSV file (Azure))
---

# L74 — Load JSON file (Azure)

> **Section:** 10 — Loading from GCP
> **Duration:** 6:00

## Prereqs

- L73 — Load CSV file (Azure)

## Key terms

- **`STRIP_OUTER_ARRAY`** — `TRUE` for "one big array"
  files, `FALSE` for "one JSON object per line".
- **`BINARY_AS_TEXT = TRUE`** — for files that are
  actually UTF-8 text but lack the `.json` extension.
- **`.json.gz`** — JSON compressed with gzip. Snowflake
  auto-decompresses when `COMPRESSION = GZIP_DETECT` or
  the file ends in `.gz`.

## Lecture

This lecture extends the Azure pipeline to a **gzipped
JSON** file. The `ff_json` file format from L43 is
already configured for gzip, so the change is a `COPY
INTO` against the same Azure stage.

### Step 1 — upload a gzipped JSON file

```bash
gzip -k code/orders.json        # creates code/orders.json.gz
az storage blob upload \
    --container-name orders \
    --file code/orders.json.gz \
    --name raw/orders/2026-10-01/orders.json.gz \
    --account-name pvsfcourse2026 \
    --overwrite
```

The `gzip -k` keeps the original `orders.json` and adds
`orders.json.gz` next to it.

### Step 2 — verify the file format handles gzip

Recall the `ff_json` from L43:

```sql
CREATE OR REPLACE FILE FORMAT ff_json
    TYPE = JSON
    STRIP_OUTER_ARRAY = FALSE
    COMPRESSION = AUTO;
```

`COMPRESSION = AUTO` is the right setting for
mixed-compression files: Snowflake detects `.gz`,
`.bz2`, `.zstd`, etc. and decompresses accordingly.

If your JSON is **always** gzipped, set
`COMPRESSION = GZIP` explicitly. `AUTO` is the safer
default.

### Step 3 — `LIST` shows the gzipped file

```sql
LIST @stg_orders_azure_json;
```

Expected:

```text
azure://pvsfcourse2026.blob.core.windows.net/orders/raw/orders/2026-10-01/orders.json.gz   ~150 KiB
```

The size is the **compressed** size on Azure; the
decompressed size is much larger.

### Step 4 — `COPY INTO`

```sql
USE WAREHOUSE loading_wh;

COPY INTO raw_orders (raw, filename, row_number)
FROM (
    SELECT
        $1                              AS raw,
        METADATA$FILENAME               AS filename,
        METADATA$FILE_ROW_NUMBER        AS row_number
    FROM @stg_orders_azure_json
)
FILE_FORMAT = (FORMAT_NAME = ff_json)
ON_ERROR    = CONTINUE
PATTERN     = '.*[.]json[.]gz';
```

`PATTERN = '.*[.]json[.]gz'` matches the gzipped file
specifically. Without the pattern, both `.json` and
`.json.gz` would be loaded (idempotent on the second
run, but slower).

### Step 5 — verify

```sql
SELECT
    filename,
    COUNT(*)        AS n_rows
FROM raw_orders
WHERE filename LIKE '%.json.gz'
GROUP BY filename;
```

Expected: the `.json.gz` file with the same row count as
the uncompressed `.json` from L67.

### The compressed-vs-uncompressed trade-off

| Format | Storage | Network | Parse cost |
|---|---|---|---|
| `.json` | baseline | baseline | baseline |
| `.json.gz` | ~10× smaller | ~10× less | +small decompress |
| `.json.zst` | ~15× smaller | ~15× less | +small decompress |

Most analytics pipelines ship gzipped JSON because the
**network egress** cost dominates the storage and parse
costs. Snowflake's auto-decompression makes the choice
invisible at query time.

### When `STRIP_OUTER_ARRAY` matters

If the gzipped file is one big array like
`[{…}, {…}, …]`, set `STRIP_OUTER_ARRAY = TRUE`:

```sql
CREATE OR REPLACE FILE FORMAT ff_json_array
    TYPE = JSON
    STRIP_OUTER_ARRAY = TRUE
    COMPRESSION = AUTO;
```

A common API export format is "always wrap in a top-level
array" — set `STRIP_OUTER_ARRAY = TRUE` to handle that.

For our `code/orders.json` (one object per line), the
default `STRIP_OUTER_ARRAY = FALSE` is correct. If the
gzip export uses a top-level array, switch to `TRUE`.

### Detecting the format

If you're unsure whether a file is "one-per-line" or
"top-level array", peek at the first byte:

```bash
zcat code/orders.json.gz | head -c 1
# '{' → one-per-line
# '[' → top-level array
```

The first character is the key.

### Cost of the load

Loading a 1 MB compressed JSON file from Azure:

| Component | Cost |
|---|---|
| Azure egress | ~$0.01 |
| Snowflake compute (loading_wh, ~3 s) | ~$0.0003 |
| Storage in `raw_orders` | ~$0.0001 |

Effectively free. The expensive part of a real pipeline
is the **parsing** of large JSON arrays — but at 1 MB
the parsing cost is sub-second.

## Hands-on

Run steps 1–5. Verify the `raw_orders` table now has
rows from both `.json` and `.json.gz`. The row count
for the gzipped file should match the uncompressed
file from L67.

## Quiz prep

- What does `COMPRESSION = AUTO` do?
- How do you tell if a JSON file is "one-per-line" vs
  "top-level array"?
- What does `PATTERN` restrict in a `COPY INTO`?

## Key takeaways

- `COMPRESSION = AUTO` detects `.gz`, `.bz2`, `.zstd` and
  decompresses automatically.
- The same `COPY INTO` pattern works for compressed and
  uncompressed JSON.
- `STRIP_OUTER_ARRAY = TRUE` is needed for files that wrap
  the whole document in `[ ]`.
- Use `PATTERN` to disambiguate `.json` from `.json.gz`
  in a mixed prefix.

## What's next

In **L75 — Sign up for free trial (GCP)** we set up a
GCP account so we can switch the source of truth from
Azure to **Google Cloud Storage**.