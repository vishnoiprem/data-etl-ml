# 8.2 — Apache Beam: Batch Pipeline

> **Section 8 · Case Study · Lecture 8.2 · 6:40**

## 🎯 What you will learn

- The Beam programming model: `PCollection`, transforms, and the runner
- Writing a batch ingestion pipeline with the Python SDK
- Reading from GCS, transforming, and writing to BigQuery
- Running it on Dataflow, locally, and in a notebook
- I/O connectors, windowing, and error handling

---

## 🧠 Concept

Apache Beam is an open-source SDK for defining data-processing pipelines. The same code runs
on multiple runners — Dataflow, Flink, Spark, or the local Direct Runner.

```
Beam SDK  →  runner  →  execution
              ├── Direct Runner   (local, for tests)
              ├── Dataflow Runner (GCP, for production)
              └── Spark / Flink   (other platforms)
```

### The core vocabulary

| Term | Meaning |
|------|---------|
| `PCollection` | A distributed collection of data (possibly unbounded) |
| `PTransform` | A function that takes a `PCollection` and returns one |
| `Pipeline` | The DAG of transforms |
| `DoFn` | The user-defined function applied element-wise |
| `Window** | A grouping of elements by time (for streaming) |
| `Runner** | The execution engine |

---

## 🧠 The anatomy of a Beam pipeline

```text
import apache_beam as beam
from apache_beam.io.gcp.bigquery_io import BigQueryDisposition
from apache_beam.io.gcp import bigquery_io

PROJECT = "YOUR_PROJECT_ID"
BUCKET = "gs://YOUR_PROJECT_ID-bq-course"
DATASET = "raw"

def run():
    options = PipelineOptions([
        "--runner=DirectRunner",
        "--project", PROJECT,
        "--temp_location", f"{BUCKET}/beam/tmp",
        "--staging_location", f"{BUCKET}/beam/staging",
    ])
    with beam.Pipeline(options=options) as p:
        (
            p
            | "Read GCS" >> beam.io.ReadFromText(
                f"{BUCKET}/staging/orders_*.csv",
                skip_header_lines=1,
            )
            | "Parse CSV" >> beam.Map(parse_order)
            | "Add metadata" >> beam.Map(add_metadata)
            | "Write to BigQuery" >> bigquery_io.WriteToBigQuery(
                f"{PROJECT}:{DATASET}.pos_orders",
                schema=ORDER_SCHEMA,
                create_disposition=BigQueryDisposition.CREATE_IF_NEEDED,
                write_disposition=BigQueryDisposition.WRITE_APPEND,
                custom_gcs_temp_location=f"{BUCKET}/beam/bq_tmp",
            )
        )
```

💡 **The same file runs locally and on Dataflow.** Change `--runner=DataflowRunner` and the
pipeline scales out. This is the single biggest advantage over writing raw Dataflow Java or
Python templates.

---

## 🛠️ Hands-On

### 1. Install Beam

```bash
pip install apache-beam[gcp]
```

### 2. Install the dependencies

```bash
pip install apache-beam[gcp,dataframe,db,filesystem] \
            apache-beam[gcp,postgres] \
            apache-beam[gcp,mysql] \
            google-cloud-bigquery \
            google-cloud-storage
```

### 3. A complete batch ingestion pipeline

```text
"""
beam_pos_ingest.py — ingest daily POS CSV extracts into BigQuery.
"""
from __future__ import annotations

import argparse
import logging
from datetime import datetime, timezone

import apache_beam as beam
from apache_beam.io.gcp import bigquery_io
from apache_beam.io.gcp.bigquery_io import BigQueryDisposition
from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions

log = logging.getLogger(__name__)

PROJECT = "YOUR_PROJECT_ID"
BUCKET = "gs://YOUR_PROJECT_ID-bq-course"
DATASET = "retailmart"
TABLE = "retailmart.raw.pos_orders"

ORDER_SCHEMA = {
    "fields": [
        {"name": "order_id", "type": "STRING", "mode": "REQUIRED"},
        {"name": "store_id", "type": "STRING", "mode": "REQUIRED"},
        {"name": "order_ts", "type": "TIMESTAMP", "mode": "REQUIRED"},
        {"name": "amount_local", "type": "NUMERIC", "mode": "REQUIRED"},
        {"name": "currency", "type": "STRING", "mode": "REQUIRED"},
        {"name": "status", "type": "STRING", "mode": "REQUIRED"},
        {"name": "line_count", "type": "INTEGER", "mode": "REQUIRED"},
    ]
}


def parse_order(line: str, target_date: str) -> dict:
    """Parse one CSV line into a typed dict."""
    parts = line.split(",")
    if len(parts) != 7:
        raise ValueError(f"Malformed row ({len(parts)} cols): {line[:120]}")

    order_id, store_id, order_ts, amount_local, currency, status, line_count = parts

    return {
        "order_id": order_id.strip(),
        "store_id": store_id.strip(),
        # POS sends local time; convert to UTC
        "order_ts": (
            datetime.fromisoformat(order_ts.strip())
            .replace(tzinfo=timezone.utc)
            .isoformat()
        ),
        "amount_local": amount_local.strip(),
        "currency": currency.strip(),
        "status": status.strip(),
        "line_count": int(line_count),
        "order_date": target_date,
    }


def add_metadata(row: dict, target_date: str) -> dict:
    row["ingested_at"] = datetime.now(timezone.utc).isoformat()
    row["source_system"] = "pos"
    return row


def run(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--target_date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--runner", default="DirectRunner")
    args, beam_args = parser.parse_known_args(argv)

    options = PipelineOptions(beam_args)
    options.view_as(SetupOptions).save_main_session = True

    pattern = f"{BUCKET}/staging/pos/orders_{args.target_date.replace('-', '')}.csv"

    with beam.Pipeline(options=options) as p:
        rows = (
            p
            | "Read CSV" >> beam.io.ReadFromText(pattern, skip_header_lines=1)
            | "Parse" >> beam.Map(parse_order, args.target_date)
            | "Metadata" >> beam.Map(add_metadata, args.target_date)
            | "Write BQ" >> bigquery_io.WriteToBigQuery(
                TABLE,
                schema=ORDER_SCHEMA,
                create_disposition=BigQueryDisposition.CREATE_IF_NEEDED,
                write_disposition=BigQueryDisposition.WRITE_APPEND,
                custom_gcs_temp_location=f"{BUCKET}/beam/bq_tmp",
            )
        )

    log.info("Ingested POS orders for %s", args.target_date)


if __name__ == "__main__":
    run()
```

### 4. Running it locally

```bash
python beam_pos_ingest.py \
  --target_date 2026-01-15 \
  --runner DirectRunner \
  --project YOUR_PROJECT_ID \
  --temp_location gs://YOUR_PROJECT_ID-bq-course/beam/tmp \
  --staging_location gs://YOUR_PROJECT_ID-bq-course/beam/staging
```

### 5. Running it on Dataflow

```bash
python beam_pos_ingest.py \
  --target_date 2026-01-15 \
  --runner DataflowRunner \
  --project YOUR_PROJECT_ID \
  --region europe-west1 \
  --temp_location gs://YOUR_PROJECT_ID-bq-course/beam/tmp \
  --staging_location gs://YOUR_PROJECT_ID-bq-course/beam/staging \
  --job_name pos-ingest-20260115 \
  --machine_type n1-standard-2 \
  --max_num_workers 20 \
  --save_main_session
```

```bash
# With a service account and autoscaling
python beam_pos_ingest.py \
  --runner DataflowRunner \
  --service_account_email bq-pipeline@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --autoscaling_algorithm=THROUGHPUT_BASED \
  --max_num_workers=50 \
  --worker_disk_type=pd-ssd \
  ...
```

💡 **`--save_main_session` is required** when your pipeline imports local modules or uses
non-serializable state. Without it, workers fail with a confusing import error.

### 6. Writing to a partition

```text
| "Write BQ" >> bigquery_io.WriteToBigQuery(
    TABLE,
    schema=ORDER_SCHEMA,
    write_disposition=BigQueryDisposition.WRITE_APPEND,
    custom_gcs_temp_location=f"{BUCKET}/beam/bq_tmp",
    with_sharding=True,
)
```

```python
# To target one partition, use a table decorator in the destination
TABLE = "retailmart.raw.pos_orders$20260115"
```

💡 **`with_sharding=True`** splits a large write into many parallel load jobs. Without it, a
write over roughly 50,000 rows per job can hit BigQuery's load-job limits.

### 7. Filtering, deduplicating, and grouping

```text
from apache_beam import combiners
from apache_beam import filters

with beam.Pipeline(options=options) as p:
    (
        p
        | "Read" >> beam.io.ReadFromText(pattern, skip_header_lines=1)
        | "Parse" >> beam.Map(parse_order, args.target_date)
        | "Valid only" >> beam.Filter(lambda r: r["status"] in ("COMPLETED", "REFUNDED"))
        | "Dedupe by order_id" >> beam.Map(lambda r: (r["order_id"], r))
        | "Keep latest" >> beam.combiners.Top(
            1, key=lambda kv: kv[1]["order_ts"]
        )
        | "Count by store" >> beam.Map(lambda kv: (kv[1]["store_id"], 1))
        | "Sum" >> combiners.Sum.Int64()
        | "Format" >> beam.Map(
            lambda kv: {"store_id": kv[0], "order_count": kv[1]}
        )
        | "Write" >> bigquery_io.WriteToBigQuery(
            f"{PROJECT}:{DATASET}.pos_daily_counts",
            write_disposition=BigQueryDisposition.WRITE_TRUNCATE,
        )
    )
```

### 8. Reading from BigQuery

```text
from apache_beam.io.gcp.bigquery_io import ReadFromBigQuery

(
    p
    | "Read BQ" >> ReadFromBigQuery(
        query="SELECT * FROM `retailmart.curated.orders` WHERE order_date = '2026-01-15'",
        use_standard_sql=True,
    )
    | "Transform" >> beam.Map(enrich)
    | "Write" >> bigquery_io.WriteToBigQuery(
        f"{PROJECT}:{DATASET}.orders_enriched",
        write_disposition=BigQueryDisposition.WRITE_TRUNCATE,
    )
)
```

💡 **Reading with a query lets BigQuery do the filtering and projection.** It pushes the work
into the engine instead of pulling the whole table into the pipeline.

### 9. Grouping into dictionaries

```text
| "Group by customer" >> beam.GroupBy(lambda r: r["customer_id"])
| "Aggregate" >> beam.Map(
    lambda g: {
        "customer_id": g.key,
        "order_count": len(g.group),
        "total": sum(float(r["amount_eur"]) for r in g.group),
    }
)
```

### 10. Handling errors

```text
from apache_beam import pvalue
from apache_beam.io.gcp.bigquery_io import BigQueryDisposition
from apache_beam.io import WriteToText
from apache_beam.io.filesystem import CompressionTypes

class ParseError(beam.DoFn):
    """Split good rows from bad rows instead of failing the whole pipeline."""

    VALID = "valid"
    INVALID = "invalid"

    def process(self, line, target_date):
        try:
            row = parse_order(line, target_date)
        except Exception as exc:                     # noqa: BLE001
            yield {
                "error": str(exc),
                "raw": line,
                "target_date": target_date,
                "failed_at": datetime.now(timezone.utc).isoformat(),
            }
        else:
            yield row


with beam.Pipeline(options=options) as p:
    output = p | "Read" >> beam.io.ReadFromText(pattern, skip_header_lines=1) | "Parse" >> beam.ParDo(ParseError(), args.target_date)

    valid = output[f"tag:{ParseError.VALID}"] if False else None  # use pvalue tags in practice

    (
        p
        | "Read" >> beam.io.ReadFromText(pattern, skip_header_lines=1)
        | "Parse" >> beam.ParDo(ParseError(), args.target_date)
        | "Write BQ" >> bigquery_io.WriteToBigQuery(
            TABLE,
            schema=ORDER_SCHEMA,
            write_disposition=BigQueryDisposition.WRITE_APPEND,
            custom_gcs_temp_location=f"{BUCKET}/beam/bq_tmp",
        )
    )
```

💡 **In production, use `pvalue.TaggedOutput`** so one `DoFn` can emit good rows and bad rows to
two separate branches. The pipeline never fails because of one malformed row.

### 11. Testing with the Direct Runner

```python
import apache_beam.testing.test_pipeline as test_pipeline
from apache_beam.testing.util import assert_that, equal_to

class TestPosIngest(test_pipeline.PTest):
    def test_parse_order(self):
        with self.assertPipelineRanSuccessfully():
            rows = (
                self.pipeline
                | beam.Create([
                    "o1,s1,2026-01-15T10:00:00,10.50,EUR,COMPLETED,2",
                ])
                | beam.Map(parse_order, "2026-01-15")
            )
            assert_that(rows, equal_to([{
                "order_id": "o1", "store_id": "s1",
                "order_ts": "2026-01-15T10:00:00+00:00",
                "amount_local": "10.50", "currency": "EUR",
                "status": "COMPLETED", "line_count": 2,
                "order_date": "2026-01-15",
            }]))
```

```bash
python -m pytest beam_pos_ingest_test.py -v
```

### 12. Launching Dataflow from Python

```python
from apache_beam.runners.runner import PipelineResult
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import DataflowRunnerOptions

options = PipelineOptions([
    "--runner=DataflowRunner",
    "--project", PROJECT,
    "--region", "europe-west1",
    "--temp_location", f"{BUCKET}/beam/tmp",
    "--staging_location", f"{BUCKET}/beam/staging",
])
result = run(beam_args=None, options=options)
```

---

## 🛠️ Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `RuntimeError: ... ImportError` on workers | Local imports not available | `--save_main_session` |
| `IOError: ... Unable to find any matching files` | Glob path wrong or file not there | Check the path; use `file_exists` transform |
| `BigQuery write failed: schema mismatch` | Row shape differs from the schema | Normalize every row to the schema's exact keys |
| `Pipeline failed due to ... Table already exists` | `CREATE_IF_NEEDED` not set | Use `BigQueryDisposition.CREATE_IF_NEEDED` |
| `Job exceeded ... max outstanding ...` | Too many parallel writes | `with_sharding=True`, fewer workers |
| `AttributeError: module 'apache_beam' has no attribute 'io'` | Missing optional extras | `pip install apache-beam[gcp]` |
| `Dataflow job stuck in Pending` | Region quota exhausted | Check regional quota; switch region |
| `Permission denied writing to GCS` | Service account lacks Storage roles | Grant `roles/storage.objectAdmin` on the bucket |
| Beam runs locally, fails on Dataflow | Pickling or closure issue | Avoid closures over unpicklable objects; use module-level functions |

---

## 💡 Production Notes

- **Always write unit tests against the Direct Runner.** They run in seconds and catch schema
  drift before a Dataflow job bills you.
- **Set `--temp_location` and `--staging_location` explicitly** on every Dataflow job.
- **Use `with_sharding=True`** for large BigQuery writes.
- **Prefer a BigQuery `query` over a table scan in `ReadFromBigQuery`** — push the work to the
  engine.
- **Use module-level functions, not closures**, for `beam.Map` — they must be picklable.
- **Set `custom_gcs_temp_location`** per pipeline to avoid collisions between concurrent jobs.
- **Version the Beam job name with the target date** so a backfill is identifiable in the
  console.
- **Budget for retries.** Dataflow retries failed bundles; your pipeline must be idempotent.

---

## 🔑 Key Takeaways

- Beam defines the pipeline; the runner executes it. Dataflow is the GCP runner.
- `PCollection` → transforms → `PCollection`; `beam.Map`, `Filter`, `GroupBy`, `FlatMap`.
- `WriteToBigQuery` needs a schema, a disposition, and `custom_gcs_temp_location`.
- **`with_sharding=True`** for large writes; `ReadFromBigQuery(query=...)` to push work to BQ.
- **`--save_main_session`** is required for local imports.
- Test locally with the Direct Runner before every Dataflow launch.

---

## 📚 Practice Exercises

1. **Batch ingest, two sources.** Write one Beam pipeline that ingests both POS CSV and product
   CSV, routes them to two BigQuery tables, and uses `TaggedOutput` for bad records.

2. **Beam vs `bq load`.** Implement the POS ingest twice — once with `bq load`, once with Beam.
   Compare runtime, cost, and the failure behaviour. Write the recommendation.

3. **Beam test suite.** Write unit tests for the parse transform covering malformed rows, nulls,
   bad types, and unicode.

4. **Resilient pipeline.** Add checkpointing, retries, and a dead-letter table. Simulate a
   failing bundle and prove the pipeline recovers without duplicate rows.

5. **Backfill driver.** Write a script that launches the Beam pipeline for a date range, one job
   per date, with a concurrency limit of 5. Track job IDs and report failures.

---

## 📖 Further Reading

- Beam Python SDK tutorial — https://beam.apache.org/documentation/sdks/python/apache-beam-intro/
- Beam Dataflow runner — https://beam.apache.org/documentation/runners/dataflow/
- `WriteToBigQuery` — https://beam.apache.org/documentation/sdks/python/apache-beam-doc/generated/apache_beam.io.gcp.bigquery_io.WriteToBigQuery.html
