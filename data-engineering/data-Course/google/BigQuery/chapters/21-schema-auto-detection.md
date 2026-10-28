# 3.4 — Schema Auto-Detection

> **Section 3 · Running Queries with Various Query Settings · Lecture 3.6 · 5:14**

## 🎯 What you will learn

- How auto-detection works for loads, queries, and external tables
- The detection algorithm and its cost
- The three override parameters that change behaviour
- When auto-detection is right, and when it is dangerous

---

## 🧠 Concept

Schema auto-detection lets BigQuery infer a table's schema from the data you load, avoiding the
manual schema-definition step.

### Where auto-detection is available

| Context | Auto-detect | Notes |
|---------|-------------|-------|
| `bq load` | ✅ `--autodetect` | Most common |
| `LOAD DATA` DDL | ✅ `OPTIONS(schema=auto)` | |
| `CREATE EXTERNAL TABLE` | ✅ `OPTIONS(schema=auto)` | |
| `CTAS` | ❌ | Schema comes from the query |
| `CREATE TABLE ... (schema)` | ❌ | You define it |
| Streaming insert | ❌ | Schema must exist (or use the legacy path) |

---

## 🧠 How Detection Works

```
1. Scan up to the first 100 rows (or 10 MB, whichever comes first)
2. For each column, infer a type from the values
3. Apply the "promotion" rules to reconcile conflicts
4. Build the schema
5. (On load) continue scanning, applying newly-discovered types
```

### The type inference rules

| Inferred type | Example values | Notes |
|---------------|----------------|-------|
| `INTEGER` / `INT64` | `42`, `-7` | |
| `FLOAT` / `FLOAT64` | `3.14`, `1e10` | |
| `BOOLEAN` / `BOOL` | `true`, `false` | |
| `STRING` | anything else | Fallback |
| `TIMESTAMP` | `2026-01-01 12:00:00` | |
| `DATE` | `2026-01-01` | |
| `TIME` | `12:00:00` | |
| `DATETIME` | `2026-01-01 12:00:00` (no TZ) | |
| `NUMERIC` | `1234.56` | Only with explicit override |
| `JSON` | `{"a": 1}` | Only with explicit override |

### Type promotion

When the first 100 rows are not representative, BigQuery promotes the type as it scans more rows:

```
Rows 1–100:  col_a = "123"        → inferred STRING
Row 101:      col_a = 456          → promoted to INT64
Row 500:      col_a = 789.5        → promoted to FLOAT64
```

💡 **This is why auto-detection can be slow on large loads.** Each promotion invalidates the
schema and requires a rewrite of the affected column. If the first row is a string like `"N/A"`
and the rest are numbers, the column becomes `FLOAT64` and every `"N/A"` becomes NULL.

### The cost of auto-detection

Auto-detection requires an extra scan pass over the leading data. On a load job, this means:

- The job reads the first ~100 rows to build the schema
- Then reads the entire file to load
- On promotion, it rewrites the affected column

💡 **For large, well-known files, an explicit schema file is faster** — it skips detection
entirely and avoids promotion rewrites.

---

## 🧠 The Three Override Parameters

These are the escape hatches when auto-detection guesses wrong.

### 1. `schema_update_options`

Controls what happens to the schema when new data arrives with different types.

| Value | Behaviour |
|-------|-----------|
| `ALLOW_FIELD_ADDITION` | New columns are added; existing types unchanged |
| `ALLOW_FIELD_RELAXATION` | Types are *widened* (INT64 → FLOAT64 → NUMERIC → STRING) |
| `ALLOW_FIELD_RELAXATION` + `ALLOW_FIELD_ADDITION` | Both |
| *(none)* | New fields cause the load to fail |

```bash
bq load \
  --source_format=CSV \
  --autodetect \
  --schema_update_options=ALLOW_FIELD_ADDITION,ALLOW_FIELD_RELAXATION \
  YOUR_PROJECT_ID:raw.events \
  gs://YOUR_PROJECT_ID-bq-course/staging/events_2026-01-01.csv
```

⚠️ **Field relaxation is one-directional.** You can widen INT64 → FLOAT64 → NUMERIC → STRING, but
never narrow. STRING → INT64 is **not** allowed.

### 2. `ignore_unknown_values`

```bash
bq load \
  --source_format=CSV \
  --autodetect \
  --ignore_unknown_values \
  YOUR_PROJECT_ID:raw.events \
  gs://YOUR_PROJECT_ID-bq-course/staging/events_2026-01-01.csv
```

Extra columns in the data that are not in the schema are silently dropped instead of erroring.

⚠️ **This silently loses data.** Use it only when you know the extra columns are junk.

### 3. `ignore_unknown_values` + `max_bad_records`

```bash
bq load \
  --source_format=CSV \
  --autodetect \
  --max_bad_records=5 \
  YOUR_PROJECT_ID:raw.events \
  gs://YOUR_PROJECT_ID-bq-course/staging/events_2026-01-01.csv
```

Up to N malformed rows are skipped; the (N+1)th fails the load. A good practice: set this to a
small non-zero number so a corrupt file does not fail an entire pipeline, but bad data is still
visible in the job log.

---

## 🛠️ Hands-On

### 1. Auto-detect a CSV

```bash
# Create a sample file
cat > /tmp/events_sample.csv <<'EOF'
event_id,user_id,event_type,event_ts,amount
e001,u001,click,2026-01-01 10:00:00,12.50
e002,u002,view,2026-01-01 10:01:00,0
e003,u001,purchase,2026-01-01 10:02:00,99.99
EOF

# Load with auto-detection
bq load \
  --source_format=CSV \
  --autodetect \
  --replace \
  YOUR_PROJECT_ID:raw.events \
  /tmp/events_sample.csv
```

```sql
-- Check what it inferred
SELECT column_name, data_type, is_nullable
FROM `YOUR_PROJECT_ID.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'events'
ORDER BY ordinal_position;
```

### 2. See where it guessed wrong

```sql
-- A file with a placeholder in a numeric column
-- "N/A" forces the whole column to STRING
```

```bash
cat > /tmp/messy.csv <<'EOF'
event_id,amount
e001,12.50
e002,N/A
e003,99.99
EOF

bq load --source_format=CSV --autodetect --replace \
  YOUR_PROJECT_ID:raw.messy_events /tmp/messy.csv
```

Result: `amount` is inferred as `STRING`, not `NUMERIC`.

```sql
-- The fix: cast it explicitly
SELECT
    event_id,
    SAFE_CAST(amount AS NUMERIC) AS amount_numeric
FROM `YOUR_PROJECT_ID.raw.messy_events`;
```

💡 **`SAFE_CAST` returns NULL instead of failing** on a bad value. It is the correct function for
dirty data — `CAST` will abort the entire query on the first unparseable value.

### 3. Auto-detect for JSON

```bash
bq load \
  --source_format=NEWLINE_DELIMITED_JSON \
  --autodetect \
  YOUR_PROJECT_ID:raw.json_events \
  gs://YOUR_PROJECT_ID-bq-course/staging/events.ndjson
```

💡 **For JSON, always specify the schema explicitly** unless the structure is genuinely trivial.
JSON auto-detection is notoriously bad with nested objects and mixed types.

```sql
-- Explicit JSON schema
CREATE TABLE `YOUR_PROJECT_ID.raw.json_events` (
    event_id   STRING,
    user_id    STRING,
    event_type STRING,
    event_ts   TIMESTAMP,
    properties JSON
)
OPTIONS (format = 'NEWLINE_DELIMITED_JSON');
```

### 4. Auto-detect for an external table

```sql
CREATE EXTERNAL TABLE `YOUR_PROJECT_ID.raw.events_external`
OPTIONS (
  format = 'CSV',
  uris = ['gs://YOUR_PROJECT_ID-bq-course/staging/events_*.csv'],
  schema = (
    event_id   STRING,
    user_id    STRING,
    event_type STRING,
    event_ts   TIMESTAMP,
    amount     NUMERIC
  )
);
```

💡 For external tables, an explicit schema avoids a scan on every query. With
`schema = AUTO`, BigQuery may re-detect the schema — which is slow and can produce inconsistent
results if the files differ.

### 5. The override matrix in practice

```bash
# Strict: fail on any schema mismatch (default)
bq load --source_format=CSV --autodetect \
  YOUR_PROJECT_ID:raw.events_strict gs://.../events.csv

# Lenient: allow new columns, widen types
bq load --source_format=CSV --autodetect \
  --schema_update_options=ALLOW_FIELD_ADDITION,ALLOW_FIELD_RELAXATION \
  YOUR_PROJECT_ID:raw.events_lenient gs://.../events.csv

# Tolerant: also drop unknown columns, skip up to 5 bad rows
bq load --source_format=CSV --autodetect \
  --schema_update_options=ALLOW_FIELD_ADDITION,ALLOW_FIELD_RELAXATION \
  --ignore_unknown_values \
  --max_bad_records=5 \
  YOUR_PROJECT_ID:raw.events_tolerant gs://.../events.csv
```

---

## 💡 Production Notes

- **Never auto-detect in production pipelines.** Write the schema explicitly. The cost of a
  surprise type promotion (INT64 → FLOAT64) breaking a downstream `CAST` is far higher than the
  minutes saved.
- **`SAFE_CAST` over `CAST` for any column that comes from outside your control.**
- **Auto-detect scans the first 100 rows.** A file whose first 100 rows are headers, footers, or
  metadata will produce a nonsense schema.
- **`ignore_unknown_values` is a data-loss switch.** If you enable it, add a row-count check
  comparing source to destination so a silent drop is detected.

```sql
-- Safety net: compare source and destination row counts
WITH src AS (
  SELECT COUNT(*) AS n FROM `gs://YOUR_PROJECT_ID-bq-course/staging/events_*.csv`
),
dst AS (
  SELECT COUNT(*) AS n FROM `YOUR_PROJECT_ID.raw.events`
)
SELECT src.n AS source_rows, dst.n AS dest_rows, src.n - dst.n AS dropped
FROM src, dst;
```

---

## 🔑 Key Takeaways

- Auto-detection infers types from the first ~100 rows and **promotes** types as it scans more.
- Available for `bq load`, `LOAD DATA`, and `CREATE EXTERNAL TABLE` — not for `CTAS`.
- Three overrides: `schema_update_options`, `ignore_unknown_values`, `max_bad_records`.
- Type promotion is one-directional (widening only); `STRING → INT64` is not allowed.
- **Use `SAFE_CAST` for dirty data** — `CAST` aborts the whole query on one bad value.
- **Production pipelines should always define the schema explicitly.**

---

## 📚 Practice Exercises

1. **Type promotion experiment.** Create a CSV with 100 rows of integers, then 200 rows of floats,
   then 300 rows with one string. Load it with auto-detection. Record the inferred type after each
   load and explain the promotion path.

2. **Override selection.** For each source, choose the load flags:
   - (a) A partner file where a new column appears monthly
   - (b) A file with a known corrupt footer row
   - (c) A file with 3 extra columns you do not need
   - (d) A file where a numeric column sometimes contains `"—"`

3. **SAFE_CAST vs CAST.** Demonstrate the difference: write a query where one row breaks `CAST`
   but `SAFE_CAST` succeeds. Then write a query that counts and reports the bad values.

4. **Explicit schema template.** Write a `schema.json` for a typical event file with 12 fields
   including one nested object and one array. Then write the equivalent `CREATE TABLE` DDL.

---

## 📖 Further Reading

- Auto-detect schema — https://cloud.google.com/bigquery/docs/schema-detection
- Load job options — https://cloud.google.com/bigquery/docs/reference/rest/v2/Job
- `SAFE_CAST` — https://cloud.google.com/bigquery/docs/reference/standard-sql/string-functions#safe_cast
