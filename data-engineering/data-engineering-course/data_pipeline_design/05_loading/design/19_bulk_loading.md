# 19 — Bulk Loading (COPY INTO, Parquet, ORC)

> **Lesson 19 of 30 — Loading**

The fastest way to land data: a single bulk load from a file. No
row-by-row INSERTs, no upserts, no per-row validation. Just dump
the file into the warehouse. This lesson is when to use bulk,
and how to do it without corrupting downstream.

---

## 1. What bulk loading is

A bulk load reads a file (CSV, JSON, Parquet) and writes all
rows to a destination table in a single operation. The
warehouse's bulk loader is highly optimized: it skips per-row
transaction overhead, uses parallel readers, and validates in
chunks.

The standard SQL syntax (Snowflake / Redshift / BigQuery):

```sql
-- Snowflake / Redshift
COPY INTO warehouse.orders
FROM 's3://data/orders/2024/01/15/'
IAM_ROLE 'arn:aws:iam::...:role/...'
FILE FORMAT = (TYPE = PARQUET);

-- BigQuery
LOAD DATA OVERWRITE warehouse.orders
FROM FILES (FORMAT = 'PARQUET', uris = ['gs://...']);
```

The result: 1 GB of Parquet lands in seconds. The same data via
INSERT statements would take minutes.

---

## 2. When to use bulk

Bulk load is the right choice when:
- The data is a single file (or a small set of files).
- The destination table is overwritten or appended wholesale.
- Latency is not the priority (hourly or daily is fine).
- The file is in a warehouse-friendly format (Parquet, ORC).

The 2026 default for new pipelines: **Parquet on S3 → bulk load
into Snowflake/BigQuery**. The file is the API; the warehouse
just consumes it.

---

## 3. The file format tradeoffs

| Format | Pros | Cons | When to use |
|---|---|---|---|
| **CSV** | Human-readable, universal | Slow to parse, no schema | Legacy, small files |
| **JSON** | Nested data, flexible | Slow, verbose | API responses, logs |
| **Parquet** | Columnar, compressed, schema | Not human-readable | Default for analytics |
| **ORC** | Like Parquet, Hive-native | Less ecosystem support | Hive / old Hadoop |
| **Avro** | Schema evolution, row-based | Larger than Parquet | Kafka events |

The senior move: name the format. "I'd use Parquet for the
landing zone because it's columnar, compressed, and the
warehouse can prune columns at scan time."

---

## 4. The Parquet format

Parquet is a *columnar* format. Each column is stored
contiguously, with run-length encoding, dictionary encoding, and
optionally Snappy or Gzip compression.

```
Parquet file:
  Row group 1:
    Column "id":    [1, 2, 3, 4, 5, 6, 7, 8]
    Column "name":  ["Alice", "Bob", "Carol", "Dan", "Eve", ...]
    Column "total": [50.0, 30.0, 75.0, 22.0, 18.0, ...]
  Row group 2:
    ...
```

The benefits:
- **Column pruning:** a query that reads only `total` doesn't
  read `name` (saves I/O).
- **Compression:** same column = similar values = high compression.
- **Predicate pushdown:** row group statistics let the reader
  skip entire row groups.

The senior move: name the three benefits unprompted.

---

## 5. The bulk load pattern

The standard bulk load pattern:

```
1. Producer writes Parquet to S3 (or GCS, ADLS).
2. Producer writes a _SUCCESS marker file.
3. Pipeline notices the marker (event, polling).
4. Pipeline issues COPY INTO from the S3 path.
5. Pipeline runs validation: row count, schema, freshness.
6. Pipeline commits the load as "done."
```

The marker file pattern is critical: it tells the consumer
"all parts of the file are written, you can read safely." A
half-written file is a corruption waiting to happen.

---

## 6. The error handling

Bulk loads can fail in three ways:

| Failure | Mitigation |
|---|---|
| File missing | Retry with backoff; alert after 5 min. |
| Schema mismatch | Schema contract test before load. |
| Partial load | Most warehouses are transactional; partial load is rare. |

The senior move: "I never trust a bulk load. After the load I
run a row count check (source vs destination) and a schema check
(destination matches the contract). If either fails, the
pipeline alerts."

---

## 7. The performance pattern

For very large files, the standard optimization is *split into
many smaller files*:

```
Bad:   s3://data/orders/single-100gb-file.parquet
Good:  s3://data/orders/2024/01/15/part-0001.parquet
       s3://data/orders/2024/01/15/part-0002.parquet
       ...
       s3://data/orders/2024/01/15/_SUCCESS
```

The warehouse reads the files in parallel. The senior move:
"Each file is 100-200 MB compressed. Smaller files = more
parallelism but more S3 GET requests. 100-200 MB is the sweet
spot."

---

## 8. The interview answer

> "For the bronze layer I'd use bulk loading from Parquet on S3.
> The producer writes `part-NNNN.parquet` files plus a `_SUCCESS`
> marker; the consumer issues `COPY INTO` from the prefix. The
> file format is Parquet because it's columnar, compressed, and
> supports column pruning. After the load I'd run a row count
> check and a schema check — I never trust a bulk load. The
> performance pattern is 100-200 MB per file for parallelism."

That single paragraph covers: load pattern, marker file, format
choice, validation, performance. Senior answer in 30 seconds.

---

## Try it

Look at the most recent bulk load you've worked on. What file
format? Is there a `_SUCCESS` marker? Is there a row count check
after? Is the file size in the 100-200 MB sweet spot? If any is
"no," the load is fragile.
