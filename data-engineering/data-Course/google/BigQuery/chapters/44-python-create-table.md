# 7.3 — Python: Create a Table

> **Section 7 · Python Client Library · Lecture 7.3 · 6:15**

## 🎯 What you will learn

- The `bigquery.Table` object and every attribute that matters
- Building schemas with `SchemaField` (nested, repeated, required)
- Partitioning, clustering, and expiration from Python
- Idempotent table creation with `exists_ok=True`
- Loading data with `load_table_from_file` and `load_table_from_dataframe`

---

## 🧠 Concept

A `bigquery.Table` mirrors a BigQuery table. The three things you always set are:

1. **A schema** — the column definitions
2. **A write disposition** — what to do if the table already exists
3. **Physical layout** — partitioning, clustering, expiration

---

## 🧠 The `SchemaField` object

```python
from google.cloud import bigquery

schema = [
    bigquery.SchemaField("order_id", "STRING", mode="REQUIRED", description="Unique order ID"),
    bigquery.SchemaField("customer_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("order_date", "DATE", mode="REQUIRED"),
    bigquery.SchemaField("order_ts", "TIMESTAMP"),
    bigquery.SchemaField("total_amount", "NUMERIC", mode="REQUIRED"),
    bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("is_completed", "BOOLEAN"),
    bigquery.SchemaField(
        name="line_items",
        field_type="RECORD",
        mode="REPEATED",
        fields=[
            bigquery.SchemaField("product_id", "STRING"),
            bigquery.SchemaField("quantity", "INTEGER"),
            bigquery.SchemaField("unit_price", "NUMERIC"),
        ],
    ),
]
```

| Argument | Values | Notes |
|----------|--------|-------|
| `name` | any string | Column name |
| `field_type` | `STRING`, `INTEGER`, `NUMERIC`, `BOOL`, `DATE`, `TIMESTAMP`, `RECORD`, `JSON`, `GEOGRAPHY` | Use `bigquery.enums.SqlTypeNames` |
| `mode` | `NULLABLE` (default), `REQUIRED`, `REPEATED` | `REPEATED` only on non-RECORD? — no, also on RECORD |
| `description` | any string | Column-level documentation |
| `fields` | list of `SchemaField` | Only for `RECORD` |

💡 **`description` on every column is free documentation.** It shows up in the console and in
the schema of every downstream reader.

### Loading a schema from a JSON file

```python
import json
from google.cloud import bigquery

with open("schemas/orders_schema.json") as f:
    raw = json.load(f)

schema = [
    bigquery.SchemaField(
        name=field["name"],
        field_type=field["type"],
        mode=field.get("mode", "NULLABLE"),
        description=field.get("description"),
        fields=[
            bigquery.SchemaField(
                name=sub["name"],
                field_type=sub["type"],
                mode=sub.get("mode", "NULLABLE"),
            )
            for sub in field.get("fields", [])
        ] or None,
    )
    for field in raw
]
```

💡 **Write a schema-to-JSON exporter once** (see Chapter 22) so your schema files and your
Python code never drift.

---

## 🧠 Physical layout

```python
table = bigquery.Table("YOUR_PROJECT_ID.curated.orders", schema=schema)

# Partitioning
table.time_partitioning = bigquery.TimePartitioning(
    type_=bigquery.TimePartitioningType.DAY,
    field="order_date",          # omit for ingestion-time partitioning
    expiration_ms=730 * 24 * 60 * 60 * 1000,   # 730 days
    require_partition_filter=True,
)

# Clustering
table.clustering_fields = ["customer_id", "status"]

# Metadata
table.description = "Orders with line items"
table.labels = {"tier": "silver", "owner": "data-eng"}
table.expires = datetime.datetime(2027, 1, 1, tzinfo=datetime.timezone.utc)
```

| Attribute | Effect |
|-----------|--------|
| `time_partitioning` | Partitioning config |
| `clustering_fields` | Up to 4 clustering columns |
| `description` | Table description |
| `labels` | Cost-attribution labels |
| `expires` | Table-level expiration timestamp |
| `friendly_name` | Display name in the console |
| `schema` | Column definitions |
| `view_query` | Makes it a view |
| `mview_query` | Makes it a materialized view |

---

## 🛠️ Hands-On

### 1. Create a table

```python
from google.cloud import bigquery

client = bigquery.Client(project="YOUR_PROJECT_ID")

table = bigquery.Table("YOUR_PROJECT_ID.curated.orders", schema=schema)
table.time_partitioning = bigquery.TimePartitioning(
    type_=bigquery.TimePartitioningType.DAY,
    field="order_date",
    require_partition_filter=True,
)
table.clustering_fields = ["customer_id"]
table.description = "Orders with line items"
table.labels = {"tier": "silver", "owner": "data-eng"}

table = client.create_table(table, exists_ok=True)
print(f"Created {table.full_table_id}")
```

💡 **`exists_ok=True` makes creation idempotent.** It is the single most important argument
when provisioning infrastructure from Python.

### 2. The SQL equivalent

```python
client.query(
    """
    CREATE TABLE IF NOT EXISTS `YOUR_PROJECT_ID.curated.orders` (
      order_id     STRING NOT NULL,
      customer_id  STRING NOT NULL,
      order_date   DATE   NOT NULL,
      total_amount NUMERIC NOT NULL,
      status       STRING NOT NULL,
      line_items   ARRAY<STRUCT<product_id STRING, quantity INT64, unit_price NUMERIC>>
    )
    PARTITION BY order_date
    CLUSTER BY customer_id
    OPTIONS(
      description = "Orders with line items",
      require_partition_filter = TRUE,
      labels = [("tier", "silver"), ("owner", "data-eng")]
    )
    """
)
```

### 3. Create an external table

```python
table = bigquery.Table("YOUR_PROJECT_ID.raw.events_external")
# `ExternalConfig` is the SDK equivalent of `WITH PARTITION OPTIONS`.
# Format-specific knobs live on `config.options` (see external_config.CSVOptions
# / AvroOptions / ParquetOptions / HivePartitioningOptions).
table.external_data_configuration = bigquery.ExternalConfig(
    bigquery.ExternalSourceFormat.PARQUET
)
table.external_data_configuration.source_uris = [
    "gs://YOUR_PROJECT_ID-bq-course/raw/events_*.parquet"
]
table.external_data_configuration.autodetect = True
table.schema = [
    bigquery.SchemaField("event_id", "STRING"),
    bigquery.SchemaField("user_id", "STRING"),
    bigquery.SchemaField("event_date", "DATE"),
]

table = client.create_table(table, exists_ok=True)
```

### 4. Create a view and a materialized view

```python
view = bigquery.Table("YOUR_PROJECT_ID.curated.v_active_orders")
view.view_query = """
    SELECT order_id, customer_id, total_amount
    FROM `YOUR_PROJECT_ID.curated.orders`
    WHERE status = 'active'
"""
view = client.create_view(view, exists_ok=True)
```

```python
mv = bigquery.Table("YOUR_PROJECT_ID.mart.mv_daily_revenue")
mv.mview_query = """
    SELECT order_date, customer_id, SUM(total_amount) AS revenue
    FROM `YOUR_PROJECT_ID.curated.orders`
    GROUP BY 1, 2
"""
mv.time_partitioning = bigquery.TimePartitioning(
    type_=bigquery.TimePartitioningType.DAY, field="order_date"
)
mv.clustering_fields = ["customer_id"]
mv = client.create_table(mv, exists_ok=True)
```

💡 **Materialized views can only reference a single base table.** If your logic needs more than
one, build a view over the join first, then materialize the view.

### 5. Load data from a local CSV

```python
from google.cloud import bigquery

job_config = bigquery.LoadJobConfig(
    source_format=bigquery.SourceFormat.CSV,
    skip_leading_rows=1,
    schema=schema,
    write_disposition="WRITE_APPEND",
    time_partitioning=bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY, field="order_date"
    ),
)

with open("data/orders_2026-01-01.csv", "rb") as f:
    job = client.load_table_from_file(f, "YOUR_PROJECT_ID.curated.orders", job_config=job_config)

job.result()   # blocks until the load finishes
print(f"Loaded {job.output_rows} rows, {job.output_bytes} bytes")
```

⚠️ **You must call `job.result()`.** The load is asynchronous — the call returns immediately
with a job handle. Without `.result()` your script exits and the load may be cancelled.

### 6. Load data from a pandas DataFrame

```python
import pandas as pd

df = pd.DataFrame(
    {
        "order_id": ["o001", "o002"],
        "customer_id": ["c001", "c002"],
        "order_date": pd.to_datetime(["2026-01-01", "2026-01-01"]).date,
        "total_amount": [10.5, 22.0],
        "status": ["active", "complete"],
    }
)

job_config = bigquery.LoadJobConfig(
    schema=schema,
    write_disposition="WRITE_APPEND",
    source_format=bigquery.SourceFormat.CSV,
)
job = client.load_table_from_dataframe(df, "YOUR_PROJECT_ID.curated.orders", job_config=job_config)
job.result()
```

💡 **Loading from a DataFrame goes through CSV by default** and is fast for anything under a few
million rows. Beyond that, write Parquet to GCS and use `load_table_from_uri` with
`source_format="PARQUET"`.

### 7. Load from Cloud Storage

```python
job_config = bigquery.LoadJobConfig(
    source_format=bigquery.SourceFormat.PARQUET,
    write_disposition="WRITE_APPEND",
    schema=schema,
)
job = client.load_table_from_uri(
    ["gs://YOUR_PROJECT_ID-bq-course/staging/orders_*.parquet"],
    "YOUR_PROJECT_ID.curated.orders",
    job_config=job_config,
)
job.result()
```

### 8. Update a table's schema

```python
table = client.get_table("YOUR_PROJECT_ID.curated.orders")

table.schema = [
    *table.schema,                                      # keep everything
    bigquery.SchemaField("source_channel", "STRING", description="New in 2026-01"),
]

table = client.update_table(table, update_mode="update_fields")
print("Schema updated")
```

💡 **`update_mode="update_fields"`** applies only the fields you set. `"update_full"` replaces
everything — and drops fields you omitted.

### 9. Add a column with SQL

```python
client.query(
    """
    ALTER TABLE `YOUR_PROJECT_ID.curated.orders`
    ADD COLUMN source_channel STRING DEFAULT 'unknown'
    """
)
```

### 10. Delete a table

```python
from google.cloud.exceptions import NotFound

try:
    client.delete_table("YOUR_PROJECT_ID.curated.orders")
    print("Deleted")
except NotFound:
    print("Already gone")
```

---

## 🛠️ Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `ValueError: Schema must be a list of SchemaField` | Passed a dict or a list of tuples | Build a real `SchemaField` list |
| `AttributeError: 'Table' object has no attribute 'external_source_configuration'` | Wrong SDK version | `pip install -U google-cloud-bigquery` |
| `Already Exists` | Table exists | Pass `exists_ok=True` |
| `SchemaMismatchError` | Data does not match the schema | Check `job.errors`; relax with `schema_update_options` |
| `Partitioning must be on a DATE, TIMESTAMP, DATETIME, or INTEGER_RANGE column` | Partition field type wrong | Change the column type or the partitioning type |
| `Load job failed: no such field` | CSV column missing from schema | Fix the CSV or relax the schema |
| `Invalid schema: Field is_repeated` | `REPEATED` mode on a non-RECORD you meant as an array | Use `RECORD` + `REPEATED` |
| Load job "completes" but nothing arrives | `job.result()` never called | Always block on `.result()` |

---

## 💡 Production Notes

- **Always use `exists_ok=True`.** Provisioning code must be re-runnable.
- **Store schemas in JSON and load them.** One source of truth, reusable by `bq load` and Python.
- **Use `WRITE_TRUNCATE` for full refreshes and `WRITE_APPEND` for incremental loads.** Never
  mix them in the same pipeline.
- **Set `require_partition_filter=True`** on every partitioned table you do not want scanned by
  accident.
- **Prefer Parquet over CSV** for anything above a few hundred MB — smaller, faster, typed.
- **Always call `job.result()`.** Add it to your code template; it is the #1 cause of "the load
  did not work."
- **Check `job.errors` on failure**, not just the exception message.

---

## 🔑 Key Takeaways

- `bigquery.Table` + `bigquery.SchemaField` mirror BigQuery tables 1:1.
- `SchemaField` supports `mode`, `description`, and nested `fields` for `RECORD` types.
- Partitioning via `bigquery.TimePartitioning`, clustering via `table.clustering_fields`.
- **`exists_ok=True` is the idempotency key.**
- `client.create_view()` for views, `mview_query` for materialized views.
- Load with `load_table_from_file`, `load_table_from_dataframe`, or `load_table_from_uri` —
  and **always block on `job.result()`**.

---

## 📚 Practice Exercises

1. **Table provisioner.** Write a function that creates any table from a JSON schema file plus a
   dict of options (partitioning, clustering, labels, description). It must be idempotent.

2. **Schema round-trip.** Write `schema_to_json(table)` that exports a table's schema back to the
   JSON format your loader accepts, including nested fields. Prove the round trip is lossless.

3. **CSV → Parquet → table.** Build a pipeline that converts a CSV in GCS to Parquet and loads
   it, and compare load times against a direct CSV load.

4. **Schema evolution drill.** Take a table, add a column, relax a field from `REQUIRED` to
   `NULLABLE`, add a nested `RECORD` field, and then load a file that exercises all three. Write
   down what broke and how you fixed it.

5. **Full-refresh vs incremental.** Build two loaders with the same interface — one
   `WRITE_TRUNCATE`, one `WRITE_APPEND` to a specific partition decorator — and prove the
   incremental one is idempotent.

---

## 📖 Further Reading

- `Table` reference — https://cloud.google.com/python/docs/reference/bigquery/latest/bigquery.table.Table
- `SchemaField` — https://cloud.google.com/python/docs/reference/bigquery/latest/bigquery.schema.SchemaField
- Loading data — https://cloud.google.com/bigquery/docs/loading-data-python
