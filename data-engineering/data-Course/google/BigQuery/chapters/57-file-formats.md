# 11.1 — File Formats for BigQuery

> **Section 11 · File Formats · Lecture 11.1 · 5:10**

## 🎯 What you will learn

- Every file format BigQuery supports, and what each is actually for
- The trade-offs: size, speed, schema fidelity, and query cost
- Parquet and Avro as the defaults, and when CSV is acceptable
- Nested and repeated data in each format
- Open table formats (Iceberg, BigLake) and where they fit

---

## 🧠 Concept

File format is not a formality — it determines load cost, query cost, and how faithfully
your data survives the round trip.

| Format | Use case | Load | Query | Schema fidelity |
|--------|----------|------|-------|-----------------|
| **CSV** | Human-readable, simple flat data | Slow | Slow (no pushdown) | Poor — no types, no nested |
| **Newline-delimited JSON** | Semi-structured, nested | Medium | Slow | Good — types inferred, nesting kept |
| **Avro** | Legacy Hadoop, schema evolution | Fast | Fast | Excellent — schema in the file |
| **Parquet** | **The default choice** | Fastest | Fastest | Excellent — types + statistics |
| **ORC** | Hive ecosystem | Fast | Fast | Excellent |
| **Iceberg / BigLake** | Open table format, open-source engines | Varies | Varies | Excellent |

---

## 🧠 Format deep dive

### CSV

```csv
order_id,customer_id,order_date,total_amount,status
o001,c001,2026-01-15,149.99,active
o002,c002,2026-01-15,89.50,complete
```

```bash
bq load --source_format=CSV \
  --schema_file=schemas/orders_schema.json \
  --skip_leading_rows=1 \
  --field_delimiter="," \
  --max_bad_records=10 \
  --replace \
  YOUR_PROJECT_ID:curated.orders \
  gs://YOUR_PROJECT_ID-bq-course/staging/orders_2026-01-15.csv
```

| Aspect | Detail |
|--------|--------|
| Types | None — everything is a string; schema must be supplied |
| Nested data | ❌ Not supported |
| Compression | gzip, deflate, zstd |
| Size | Large — 3–10× larger than Parquet |
| Quoting | RFC 4180; embedded commas need quoting |
| Nulls | Empty string is not NULL; use `\N` in some dialects |

💡 **CSV is a delivery format, not a storage format.** Use it when the source produces it;
convert to Parquet before storing.

### Newline-delimited JSON

```json
{"order_id":"o001","customer_id":"c001","order_date":"2026-01-15","total_amount":149.99}
{"order_id":"o002","customer_id":"c002","order_date":"2026-01-15","total_amount":89.50}
```

```bash
bq load --source_format=NEWLINE_DELIMITED_JSON \
  --schema_file=schemas/orders_schema.json \
  --replace \
  YOUR_PROJECT_ID:curated.orders \
  gs://YOUR_PROJECT_ID-bq-course/staging/orders.ndjson
```

| Aspect | Detail |
|--------|--------|
| Types | Inferred from the first 100 rows, or supplied |
| Nested data | ✅ Objects and arrays preserved |
| Size | Moderate — 2–4× larger than Parquet |
| Compression | gzip, deflate, zstd |
| Malformed | `max_bad_records` skips bad lines |

💡 **NDJSON is the natural format for event streams.** One object per line means it appends
cleanly and streams without rewriting the whole file.

### Avro

```python
import fastavro
from datetime import date

schema = {
    "type": "record",
    "name": "Order",
    "fields": [
        {"name": "order_id", "type": "string"},
        {"name": "customer_id", "type": "string"},
        {"name": "order_date", "type": {"type": "int", "logicalType": "date"}},
        {"name": "total_amount", "type": {"type": "bytes", "logicalType": "decimal", "precision": 12, "scale": 2}},
        {"name": "status", "type": "string", "default": "unknown"},
    ],
}

with open("orders.avro", "wb") as f:
    fastavro.writer(f, schema, [
        {"order_id": "o001", "customer_id": "c001", "order_date": date(2026, 1, 15),
         "total_amount": decimal.Decimal("149.99"), "status": "active"},
    ])
```

```bash
bq load --source_format=AVRO \
  --replace \
  YOUR_PROJECT_ID:curated.orders \
  gs://YOUR_PROJECT_ID-bq-course/staging/orders.avro
```

| Aspect | Detail |
|--------|--------|
| Schema | Embedded in the file — self-describing |
| Types | Full, including logical types (date, decimal, timestamp) |
| Nested data | ✅ Full support |
| Schema evolution | ✅ Excellent — `avro_schema_update_options` |
| Compression | Deflate, Snappy, Zstandard, Bzip2 |

### Parquet

```python
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd

df = pd.DataFrame({
    "order_id": ["o001", "o002"],
    "customer_id": ["c001", "c002"],
    "order_date": [pd.Timestamp("2026-01-15").date()] * 2,
    "total_amount": [149.99, 89.50],
    "status": ["active", "complete"],
})

table = pa.Table.from_pandas(df, preserve_index=False)
pq.write_table(table, "orders.parquet", compression="snappy")
```

```bash
bq load --source_format=PARQUET \
  --replace \
  YOUR_PROJECT_ID:curated.orders \
  gs://YOUR_PROJECT_ID-bq-course/staging/orders_*.parquet
```

| Aspect | Detail |
|--------|--------|
| Columnar | ✅ Only the columns you query are read |
| Statistics | Row-group min/max — enables predicate pushdown |
| Types | Full, including nested and logical types |
| Compression | Snappy, GZIP, Brotli, LZ4, ZSTD |
| Size | **Smallest** — typically 3–10× smaller than CSV |
| Load speed | **Fastest** — no parsing needed |

💡 **Parquet is the default for everything.** It is the smallest on disk, the fastest to load,
and the fastest to query because BigQuery reads only the column chunks it needs.

### ORC

```bash
bq load --source_format=ORC \
  --replace \
  YOUR_PROJECT_ID:curated.orders \
  gs://YOUR_PROJECT_ID-bq-course/staging/orders.orc
```

| Aspect | Detail |
|--------|--------|
| Columnar | ✅ |
| Types | Full |
| Nested data | ✅ |
| Best for | Hive/Impala interoperability |
| Use over Parquet | Rarely — Parquet is generally better |

---

## 🧠 The comparison you will actually be asked for

| | CSV | NDJSON | Avro | Parquet |
|---|-----|--------|------|---------|
| File size (100k rows) | 12 MB | 18 MB | 4 MB | 2 MB |
| Load time | 8 s | 6 s | 2 s | 1.5 s |
| Query time (2 of 8 cols) | 4.1 s | 4.4 s | 1.8 s | 0.9 s |
| Bytes scanned | 12 MB | 18 MB | 4 MB | 2 MB |
| Cost per query (on-demand) | $0.073 | $0.110 | $0.024 | $0.012 |
| Nested data | ❌ | ✅ | ✅ | ✅ |
| Schema evolution | ❌ | ⚠️ | ✅ | ✅ |

---

## 🧠 Nested and repeated data in each format

```sql
-- Target schema
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.orders` (
  order_id    STRING NOT NULL,
  order_date  DATE   NOT NULL,
  line_items ARRAY<STRUCT<
    product_id STRING,
    quantity   INT64,
    unit_price NUMERIC
  >>,
  metadata   JSON
)
PARTITION BY order_date;
```

```json
{"order_id":"o001","order_date":"2026-01-15","line_items":[{"product_id":"p1","quantity":2,"unit_price":25.00}],"metadata":{"channel":"web"}}
```

```python
# Parquet with nested structures
import pyarrow as pa
import pyarrow.parquet as pq

schema = pa.schema([
    pa.field("order_id", pa.string()),
    pa.field("order_date", pa.date32()),
    pa.field("line_items", pa.list_(
        pa.struct([
            pa.field("product_id", pa.string()),
            pa.field("quantity", pa.int64()),
            pa.field("unit_price", pa.decimal128(12, 2)),
        ])
    )),
    pa.field("metadata", pa.string()),   # JSON as string
])

table = pa.Table.from_pylist([
    {
        "order_id": "o001",
        "order_date": pa.scalar(__import__("datetime").date(2026, 1, 15)).as_py(),
        "line_items": [{"product_id": "p1", "quantity": 2, "unit_price": "25.00"}],
        "metadata": '{"channel":"web"}',
    }
], schema=schema)

pq.write_table(table, "orders.parquet", compression="snappy")
```

💡 **JSON columns in Parquet are stored as strings** unless you use a type annotation. BigQuery
reads them as `JSON` only if the destination column is `JSON` — the source type does not
matter.

---

## 🧠 Compression

| Codec | Ratio | Speed | Use for |
|-------|-------|-------|---------|
| None | 1× | Fastest | Already compressed |
| Snappy | ~2× | Very fast | Parquet default — best balance |
| GZIP | ~3× | Medium | Legacy CSV/NDJSON |
| Zstandard | ~4× | Fast | Best ratio/speed trade-off today |
| Brotli | ~4× | Slower | Read-heavy archives |
| LZ4 | ~2.5× | Very fast | High-throughput ingest |

```bash
# Load gzip-compressed CSV
bq load --source_format=CSV --compression=GZIP --skip_leading_rows=1 \
  YOUR_PROJECT_ID:curated.orders gs://bucket/orders.csv.gz
```

💡 **Compression does not change query cost** — BigQuery bills the *uncompressed* logical
bytes scanned. Compressing files saves storage and network, not query dollars.

---

## 🧠 Open table formats: Iceberg and BigLake

```sql
-- Create an Iceberg table in BigQuery
CREATE TABLE `YOUR_PROJECT_ID.curated.orders_iceberg`
WITH CONNECTION `YOUR_PROJECT_ID.us.my-connection`
OPTIONS (
  file_format = 'ICEBERG',
  table_format = 'ICEBERG',
  storage_uri = 'gs://YOUR_PROJECT_ID-bq-course/iceberg/orders'
);
```

```sql
-- Write to it
INSERT INTO `YOUR_PROJECT_ID.curated.orders_iceberg`
SELECT * FROM `YOUR_PROJECT_ID.curated.orders`;
```

```sql
-- Merge into it
MERGE INTO `YOUR_PROJECT_ID.curated.orders_iceberg` AS t
USING `YOUR_PROJECT_ID.curated.orders` AS s
ON t.order_id = s.order_id
WHEN MATCHED THEN UPDATE SET t.status = s.status
WHEN NOT MATCHED THEN INSERT (order_id, order_date, status) VALUES (s.order_id, s.order_date, s.status);
```

| Feature | Standard BigQuery table | Iceberg table |
|---------|------------------------|---------------|
| Engine | BigQuery only | BigQuery, Spark, Flink, Trino |
| Metadata | BigQuery-internal | Metadata file in GCS |
| Transactions | Limited DML | Full ACID MERGE |
| Schema evolution | Limited | Full |
| Snapshot isolation | ❌ | ✅ |
| Open format | ❌ | ✅ |
| Cost | Standard | Standard + storage |

💡 **Iceberg is the right choice when other engines need the same data.** If only BigQuery
reads it, a standard table is simpler and cheaper to operate.

---

## 🧠 Choosing a format — decision guide

| Situation | Format | Why |
|-----------|--------|-----|
| The source emits CSV | CSV → convert to Parquet | CSV cannot express types |
| Event stream, one object per line | NDJSON | Appends cleanly |
| Apache Spark / Hive pipeline | Parquet | Native, fastest |
| Legacy Hadoop with schema evolution | Avro | Schema in file |
| Another team needs the same data | Parquet or Iceberg | Open, typed |
| Archival for 7 years | Parquet + GCS lifecycle | Cheap, queryable |
| Regulatory requirement for human review | CSV export | Readable |
| BI tool that cannot read GCS | CSV export to a sheet | Convenience |

---

## 🛠️ Hands-On: convert CSV → Parquet

```python
"""
csv_to_parquet.py — convert CSV landing files to Parquet in GCS.
"""
import io

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from google.cloud import bigquery, storage

PROJECT = "YOUR_PROJECT_ID"
BUCKET_NAME = "YOUR_PROJECT_ID-bq-course"
SCHEMA = {
    "order_id": pa.string(),
    "customer_id": pa.string(),
    "order_date": pa.date32(),
    "total_amount": pa.decimal128(12, 2),
    "status": pa.string(),
}


def convert(client: bigquery.Client, gcs: storage.Client, date_str: str) -> None:
    src = f"staging/orders_{date_str}.csv"
    dst = f"staging/parquet/orders_{date_str}.parquet"

    blob = gcs.bucket(BUCKET_NAME).blob(src)
    if not blob.exists():
        raise FileNotFoundError(src)

    df = pd.read_csv(io.BytesIO(blob.download_as_bytes()))
    df["order_date"] = pd.to_datetime(df["order_date"]).dt.date
    df["total_amount"] = pd.to_numeric(df["total_amount"]).round(2)

    table = pa.Table.from_pandas(df, schema=pa.schema(SCHEMA), preserve_index=False)
    out = io.BytesIO()
    pq.write_table(table, out, compression="zstd")

    gcs.bucket(BUCKET_NAME).blob(dst).upload_from_string(out.getvalue(), content_type="application/octet-stream")
    print(f"✓ {dst} ({len(out.getvalue()) / 1024**2:.2f} MB)")


if __name__ == "__main__":
    import sys
    convert(bigquery.Client(), storage.Client(), sys.argv[1])
```

### Comparing the cost of each format

```python
def compare_formats(table: str, project: str = "YOUR_PROJECT_ID") -> None:
    client = bigquery.Client(project=project)

    for fmt, source in (("CSV", "gs://bucket/orders.csv"),
                        ("NDJSON", "gs://bucket/orders.ndjson"),
                        ("PARQUET", "gs://bucket/orders.parquet")):
        config = bigquery.LoadJobConfig(
            source_format=fmt,
            skip_leading_rows=1,
            autodetect=True,
            write_disposition="WRITE_TRUNCATE",
        )
        job = client.load_table_from_uri(source, table, job_config=config)
        job.result()
        print(f"{fmt:<10} rows={job.output_rows:>10,} bytes={job.output_bytes:>12,}")
```

---

## 💡 Production Notes

- **Convert to Parquet at the boundary.** Everything downstream is faster and cheaper.
- **Compression saves storage, not query cost.** BigQuery bills uncompressed logical bytes.
- **Use Zstandard for Parquet** — the best ratio/speed trade-off available today.
- **Always validate a format conversion** by comparing row counts and a checksum of key columns.
- **Use NDJSON for event streams** — it appends without rewriting.
- **Do not use `autodetect` in production** for anything that matters. The first 100 rows decide
  the schema, and one bad row can change a column's type forever.
- **Keep the Avro schema with the data.** Without it, an Avro file is unreadable.
- **Consider Iceberg** when more than one engine needs the table.

---

## 🔑 Key Takeaways

- **Parquet is the default.** Smallest, fastest to load, fastest to query, full type fidelity.
- CSV has no types and no nested data — it is a delivery format, not a storage format.
- NDJSON is the natural streaming format; one object per line.
- Avro is still excellent for schema evolution and Hadoop interop.
- **Compression reduces storage and transfer, not query cost.**
- BigQuery bills **uncompressed logical bytes scanned** — always check the dry run.
- Iceberg/BigLake is the answer when other engines need the same table.

---

## 📚 Practice Exercises

1. **Format benchmark.** Take a 10M-row dataset. Produce it in all five formats. Measure file
   size, load time, query time, and bytes scanned for 3 different query shapes. Write a
   recommendation with a decision tree.

2. **CSV → Parquet pipeline.** Build a scheduled converter (Cloud Function + Scheduler) that
   converts incoming CSVs to Zstandard Parquet and loads them into a partitioned table. Include
   validation and a failure path.

3. **Nested data in every format.** Write the same nested dataset (orders with line items and
   a JSON metadata blob) in CSV (flattened), NDJSON, Avro, and Parquet. Load each into BigQuery
   and compare the resulting schemas and query performance.

4. **Compression study.** Measure the size and load-time impact of Snappy, GZIP, Zstandard, and
   Brotli for Parquet and for NDJSON. Then verify (or disprove) that query cost is unaffected.

5. **Iceberg pilot.** Create an Iceberg table in BigLake, write data with `MERGE`, and read the
   same table from Spark. Document what worked and what did not.

---

## 📖 Further Reading

- BigQuery loading data — https://cloud.google.com/bigquery/docs/loading-data
- Supported formats and options — https://cloud.google.com/bigquery/docs/loading-data-cloud-storage-parquet-avro
- BigLake Iceberg tables — https://cloud.google.com/bigquery/docs/iceberg-tables
- Parquet format — https://parquet.apache.org/docs/file-format/
