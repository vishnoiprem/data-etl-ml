# 11.2 — Apache Beam Fundamentals

> **Section 11 · File Formats · Lecture 11.2 · 6:30**

## 🎯 What you will learn

- The Beam model in depth: `PCollection`, `PTransform`, `DoFn`, and the runner
- Every core transform, with the SQL equivalent
- Combiners, group-bys, and side inputs
- Beam SQL and the DataFrames API
- Testing, deployment, and monitoring

---

## 🧠 Concept

Beam is a **unified API** for batch and streaming data processing. The same code runs on
Dataflow, Flink, Spark, and the local Direct Runner.

```
        ┌─────────── your pipeline code ───────────┐
        │                                          │
   PCollection ──► PTransform ──► PCollection ──► PTransform ──► PCollection
        │                                          │
        └──────────────► Runner (Dataflow) ────────┘
```

| Concept | Definition |
|---------|-----------|
| **PCollection** | A (possibly unbounded) distributed data set |
| **PTransform** | A function from `PCollection` to `PCollection` |
| **DoFn** | The user function applied element by element |
| **CombineFn** | An associative + commutative aggregation |
| **Runner** | The engine that executes the pipeline |
| **Window** | A time-bounded grouping of elements |
| **Trigger** | When a window's result is emitted |
| **Coder** | How elements are serialized between workers |
| **Side input** | A small extra data set applied to a `DoFn` |
| **Bag / KV** | `Bag` = repeated, `KV` = keyed |

---

## 🧠 The transform catalogue

| Beam transform | SQL equivalent |
|----------------|----------------|
| `beam.Map` | `SELECT expr` |
| `beam.FlatMap` | `SELECT` + `UNNEST` |
| `beam.Filter` | `WHERE` |
| `beam.CombinePerKey` | `GROUP BY` + aggregate |
| `beam.GroupBy` | `GROUP BY` |
| `beam.CombineGlobally` | Aggregate over everything |
| `beam.ParDo` | User-defined function |
| `beam.Join` | `JOIN` |
| `beam.WindowInto` | `GROUP BY` with a time window |
| `beam.Reshuffle` | Rebalance the work |
| `beam.pvalue.AsIter` | Iterate a side input |

### Map and FlatMap

```text
import apache_beam as beam

(p
 | "Read" >> beam.Create([1, 2, 3, 4])
 | "Map" >> beam.Map(lambda x: x * 2)
 | "FlatMap" >> beam.FlatMap(lambda x: [x, x + 1]))
```

```sql
SELECT value * 2 FROM input
UNION ALL
SELECT value, value + 1 FROM input
```

### Filter

```text
| "Filter" >> beam.Filter(lambda row: row["total_amount"] > 100)
```

```sql
WHERE total_amount > 100
```

### CombinePerKey — the workhorse

```text
from apache_beam import combiners

(p
 | "Key by region" >> beam.Map(lambda r: (r["region"], r["amount_eur"]))
 | "Sum per region" >> combiners.Sum.PerKey()
 | "Format" >> beam.Map(lambda kv: {"region": kv[0], "revenue": kv[1]}))
```

```sql
SELECT region, SUM(amount_eur) AS revenue
FROM orders GROUP BY region
```

💡 **Use a `CombineFn` when you need more than a built-in.** A custom `CombineFn` is
associative and commutative, so Beam can parallelize it and merge partial results — which
means it scales, unlike a Python function that accumulates a list.

```text
class AverageRevenueFn(beam.CombineFn):
    def create_accumulator(self):
        return (0.0, 0)          # (sum, count)

    def add_input(self, accumulator, element):
        return (accumulator[0] + float(element["amount_eur"]), accumulator[1] + 1)

    def merge_accumulators(self, accumulators):
        total_sum = sum(a[0] for a in accumulators)
        total_count = sum(a[1] for a in accumulators)
        return (total_sum, total_count)

    def extract_output(self, accumulator):
        total_sum, total_count = accumulator
        return total_sum / total_count if total_count else 0.0


(p
 | "Key" >> beam.Map(lambda r: (r["region"], r))
 | "Average" >> beam.CombinePerKey(AverageRevenueFn())
 | "Format" >> beam.Map(lambda kv: {"region": kv[0], "avg": kv[1]}))
```

### GroupBy

```text
(p
 | "Key" >> beam.Map(lambda r: (r["region"], r))
 | "GroupBy" >> beam.GroupBy(lambda r: r["region"])
 | "Summarise" >> beam.Map(
     lambda g: {
         "region": g.key,
         "count": len(g.group),
         "revenue": sum(float(r["amount_eur"]) for r in g.group),
     }
))
```

💡 **`GroupBy` is easier to read but does not scale as well as `CombinePerKey`.** `GroupBy`
materialises the whole group on one worker. `CombinePerKey` can merge partial results
incrementally. Use `GroupBy` for small groups; use `CombinePerKey` for large ones.

### Joins

```text
from apache_beam import Join

orders = p | "Orders" >> beam.io.ReadFromParquet(orders_path)
regions = p | "Regions" >> beam.io.ReadFromParquet(regions_path)

joined = orders | "Join" >> Join.RegionsJoin(orders, regions)
```

```text
# Manual join — more control
orders_kv = orders | "Key" >> beam.Map(lambda r: (r["region"], r))
regions_kv = regions | "Key" >> beam.Map(lambda r: (r["region"], r))

joined = (
    {"orders": orders_kv, "regions": regions_kv}
    | "CoGroup" >> beam.Flatten()
    | "Join" >> beam.Map(
        lambda kv: (kv[0], list(kv[1]["orders"]), list(kv[1]["regions"]))
    )
)
```

💡 **Beams's join API is limited. In practice, join in BigQuery and read the result.** It is
faster, simpler, and cheaper than a shuffle join in the pipeline.

### Side inputs

```text
regions = p | "Read regions" >> beam.io.ReadFromParquet(regions_path)
lookup = beam.pvalue.AsSingleton(
    regions | "To dict" >> beam.Map(lambda r: (r["region"], r["name"]))
)

(p
 | "Read orders" >> beam.io.ReadFromParquet(orders_path)
 | "Enrich" >> beam.Map(
     lambda r, names: {**r, "region_name": names.get(r["region"], "Unknown")},
     names=lookup,
 ))
```

### Reshuffle

```text
(p
 | "Read" >> beam.io.ReadFromPubSub(topic=TOPIC)
 | "Parse" >> beam.Map(parse)
 | "Reshuffle" >> beam.Reshuffle()      # rebalance across workers
 | "Write" >> bigquery_io.WriteToBigQuery(TABLE))
```

💡 **`Reshuffle` is a no-op in the batch Direct Runner but matters in streaming.** It
rebalances skewed data so one hot key does not land on one worker.

---

## 🧠 I/O connectors

| Source | Transform |
|--------|-----------|
| Text files | `beam.io.ReadFromText` |
| CSV | `beam.io.ReadFromCsv` |
| JSON | `beam.io.ReadFromJson` |
| Parquet | `beam.io.ReadFromParquet` |
| Avro | `beam.io.ReadFromAvro` |
| Pub/Sub | `beam.io.ReadFromPubSub` |
| Kafka | `beam.io.ReadFromKafka` |
| BigQuery | `ReadFromBigQuery` |
| Spanner | `beam.io.ReadFromSpanner` |
| Cloud Storage | `beam.io.ReadFromText` with a GCS path |
| MySQL / PostgreSQL | `beam.io.ReadFromJdbc` (via JdbcIO) |

| Sink | Transform |
|------|-----------|
| Text / CSV / JSON | `beam.io.WriteToText`, `WriteToCsv`, `WriteToJson` |
| Parquet | `beam.io.WriteToParquet` |
| Avro | `beam.io.WriteToAvro` |
| BigQuery | `bigquery_io.WriteToBigQuery` |
| Pub/Sub | `beam.io.WriteToPubSub` |
| Kafka | `beam.io.WriteToKafka` |
| GCS | `beam.io.WriteToText` with a GCS path |

```text
# Write partitioned Parquet by date
(p
 | "Read" >> beam.io.ReadFromPubSub(topic=TOPIC)
 | "Parse" >> beam.Map(parse)
 | "Key by date" >> beam.Map(lambda e: (e["event_date"], e))
 | "Write" >> beam.io.WriteToParquet(
     f"{BUCKET}/events/",
     file_name_prefix="events",
     partition_keys=["event_date"],
     codec="snappy",
 ))
```

---

## 🧠 Beam SQL

```text
from apache_beam.sql import register_table

with beam.Pipeline(options=options) as p:
    schema = """
        COLNAME:STRING, CUSTID:INT64, ORDER_DATE:DATE, AMOUNT:DOUBLE
    """
    p | "Create" >> beam.Create([("o1", 1, "2026-01-15", 10.5)]) \
                | "ToTable" >> beam.Map(
                    lambda t: beam.TableRow(t[0], t[1], t[2], t[3])
                ) \
                | "Register" >> register_table("orders", schema, by_name=True)

    (
        p
        | "Select" >> beam.Sql("""
            SELECT CUSTID, SUM(AMOUNT) AS total
            FROM orders
            GROUP BY CUSTID
          """)
        | "Print" >> beam.Map(print)
    )
```

💡 **Beam SQL is convenient for prototyping and for simple aggregations.** It does not
support joins between registered tables, and it is not the place to build a production
transformation layer. Use BigQuery SQL for that.

---

## 🧠 The DataFrames API

```text
import apache_beam as beam
from apache_beam.dataframe.io import read_csv, to_parquet

(p
 | "Read" >> read_csv("gs://bucket/orders/*.csv")
 | "Filter" >> beam.dataframe.Filter(lambda df: df["amount"] > 100)
 | "GroupBy" >> beam.dataframe.GroupBy("region").aggregate(
     revenue=beam.dataframe.aggregate.sum("amount")
 )
 | "Write" >> to_parquet("gs://bucket/output/")
)
```

```text
# With a schema
schema = {
    "fields": [
        {"name": "order_id", "type": "STRING"},
        {"name": "amount", "type": "DOUBLE"},
    ]
}
(p
 | "Read" >> read_csv("gs://bucket/orders/*.csv", schema=schema)
 | "Write" >> to_parquet("gs://bucket/output/"))
```

💡 **The DataFrames API gives you a pandas-like API that Beam converts into a Beam pipeline.**
It is a nice middle ground for transformations too complex for `Map` but simpler than raw
Beam. It has limitations (no joins between differently-partitioned frames, limited UDFs) and
is not the recommended approach for new production code — but it is excellent for exploration.

---

## 🛠️ Hands-On: a complete word-count pipeline

```text
"""
wordcount.py — the canonical Beam example, in three dialects.
"""
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions


def run(argv=None):
    options = PipelineOptions(argv)
    options.view_as(StandardOptions).streaming = False

    with beam.Pipeline(options=options) as p:
        (
            p
            | "Read" >> beam.io.ReadFromText("gs://bucket/wordcount/*.txt")
            | "Split" >> beam.FlatMap(lambda line: line.split())
            | "Count" >> beam.combiners.Count.PerKey()
            | "Format" >> beam.Map(lambda kv: f"{kv[0]}: {kv[1]}")
            | "Write" >> beam.io.WriteToText("gs://bucket/output/wordcount")
        )


if __name__ == "__main__":
    run()
```

```text
# The same thing with the CombinePerKey API
with beam.Pipeline(options=options) as p:
    (
        p
        | "Read" >> beam.io.ReadFromText("gs://bucket/wordcount/*.txt")
        | "Split+Count" >> beam.Map(lambda line: (word, 1) for word in line.split())
        | "Count" >> beam.combiners.Count.PerKey()
        | "Write" >> beam.io.WriteToText("gs://bucket/output/wordcount")
    )
```

```text
# The same thing with Beam SQL
from apache_beam.sql import register_table

with beam.Pipeline(options=options) as p:
    p | "Create" >> beam.Create([("hello",), ("world",)]) \
                | "ToRow" >> beam.Map(lambda t: beam.TableRow(t[0])) \
                | "Register" >> register_table("words", "word:STRING", by_name=True)

    (
        p
        | "Sql" >> beam.Sql("SELECT word, COUNT(*) AS n FROM words GROUP BY word")
        | "Print" >> beam.Map(print)
    )
```

---

## 🛠️ Testing strategies

### 1. Unit test the pure logic

```python
def test_parse_order():
    line = "o001,s1,2026-01-15T10:00:00,10.50,EUR,COMPLETED,2"
    result = parse_order(line, "2026-01-15")
    assert result["order_id"] == "o001"
    assert result["line_count"] == 2
```

### 2. Test the pipeline end-to-end with the Direct Runner

```python
import apache_beam.testing.test_pipeline as test_pipeline
from apache_beam.testing.util import assert_that, equal_to


class TestIngest(test_pipeline.PTest):
    def test_counts(self):
        with self.assertPipelineRanSuccessfully():
            result = (
                self.pipeline
                | beam.Create(["a b", "b c"])
                | beam.FlatMap(lambda line: line.split())
                | beam.combiners.Count.PerKey()
            )
            assert_that(result, equal_to([("a", 1), ("b", 2), ("c", 1)]))
```

### 3. Test with a temporary file

```python
import tempfile


class TestParquet(test_pipeline.PTest):
    def test_write_and_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = f"{tmp}/out"
            with self.assertPipelineRanSuccessfully():
                (
                    self.pipeline
                    | beam.Create([{"id": 1}, {"id": 2}])
                    | beam.io.WriteToParquet(path)
                )

            with self.assertPipelineRanSuccessfully():
                rows = self.pipeline | beam.io.ReadFromParquet(path)
                assert_that(rows, equal_to([{"id": 1}, {"id": 2}]))
```

### 4. Integration test on Dataflow

```bash
python -m pytest tests/ -v --beam_args="--runner=DataflowRunner \
  --project=YOUR_PROJECT_ID --region=europe-west1 \
  --temp_location=gs://bucket/beam/tmp --staging_location=gs://bucket/beam/staging"
```

---

## 🛠️ Deployment and monitoring

```bash
# Deploy a streaming job
python pipeline.py \
  --runner DataflowRunner \
  --project YOUR_PROJECT_ID \
  --region europe-west1 \
  --streaming \
  --staging_location gs://bucket/beam/staging \
  --temp_location gs://bucket/beam/tmp \
  --save_main_session \
  --autoscaling_algorithm=THROUGHPUT_BASED \
  --max_num_workers=50 \
  --service_account_email beam@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Update a running streaming job (fast worker restart)
python pipeline.py ... --streaming_update --sdk_location=gs://bucket/beam/sdk
```

```python
# Deploy from Python and get the job ID
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.runners.runner import PipelineResult

result = run(options=PipelineOptions([...]))
print(result.state)
```

```bash
# Monitor
gcloud dataflow jobs list --region=europe-west1 \
  --filter="state=RUNNING" \
  --format="table(id,name,state,createTime)"

gcloud dataflow jobs describe <job-id> --region=europe-west1 \
  --format="value(jobMetrics)"

# Cancel
gcloud dataflow jobs cancel <job-id> --region=europe-west1
```

**Key metrics to watch:**

| Metric | Meaning | Alert on |
|--------|---------|-----------|
| `worker/worker_healthy` | Healthy workers | Below expected count |
| `worker/execution_parallelism` | Active parallelism | Drops to 0 |
| `worker/execution_duration` | Time per bundle | Rising trend |
| `sys/byte_count` | Bytes processed | Deviation from baseline |
| `pubsub/subscription/num_undelivered_messages` | Backlog | Growing |

---

## 🛠️ Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `PicklingError` / `Can't pickle local object` | Lambda or closure in a transform | Use a module-level function |
| `TypeError: unhashable type` | Non-scalar key in `CombinePerKey` | Convert to a string or tuple key |
| `RuntimeError: Transform name is already used` | Duplicate transform labels | Give each transform a unique label |
| `AttributeError: 'NoneType' object has no attribute 'value'` | Coder inference failure | Set `beam.coders.ProtoCoder` or a `RowCoder` |
| `Job exceeded resource limits` | Too many workers for the quota | Lower `--max_num_workers` |
| Pipeline hangs at Direct Runner | A transform blocks (e.g. an API call) | Use `mode="reschedule"` semantics, or mock it in tests |
| `Dataflow job fails on worker 0 only` | Missing dependency on the worker | `--save_main_session` and `--requirements_file` |
| `Oversized element` | One huge element | Batch before writing, or raise the size limit |
| `AttributeError: module 'apache_beam' has no attribute 'dataframe'` | Missing extras | `pip install apache-beam[gcp,dataframe]` |

---

## 💡 Production Notes

- **Use module-level functions, never lambdas,** for anything that must be picklable. A lambda
  works locally and fails on a worker.
- **Test on the Direct Runner first.** It is free and runs in seconds.
- **Prefer BigQuery for joins and aggregations.** The pipeline's job is ingest; BigQuery's job
  is transformation.
- **`--save_main_session` is not optional** for any pipeline that imports local code.
- **Always set `--temp_location` and `--staging_location`.** The default collides between
  concurrent jobs.
- **Version the SDK.** `--sdk_location` pointing at your own bucket lets you deploy a new
  version without waiting for a managed upgrade.
- **`--streaming_update`** for fast deploys of streaming jobs.
- **Make the pipeline idempotent.** Dataflow retries bundles; a non-idempotent write produces
  duplicates.
- **Monitor with Cloud Monitoring alerts**, not by looking at the console.

---

## 🔑 Key Takeaways

- Beam = `PCollection` + `PTransform` + a **runner**; the same code runs anywhere.
- The transform catalogue mirrors SQL: `Map`, `Filter`, `CombinePerKey`, `GroupBy`, `WindowInto`.
- **`CombineFn` must be associative and commutative** — that is what makes it scalable.
- Side inputs for small lookup tables; `Reshuffle` for skew in streaming.
- **Beam SQL and the DataFrames API** are useful middle grounds, not the production default.
- Module-level functions, `--save_main_session`, Direct Runner tests, idempotent writes.

---

## 📚 Practice Exercises

1. **Transform drill.** Implement the same word count five ways: `Map` + `Count`,
   `CombinePerKey`, `CombineFn`, `GroupBy`, and Beam SQL. Compare readability and runtime.

2. **Custom CombineFn.** Build a `TopNCombineFn` that returns the top 3 products by revenue
   per region, and prove it merges correctly across bundles.

3. **Skew handling.** Simulate a hot key (one customer with 50% of the traffic). Show the
   problem, then fix it with `Reshuffle` or a two-phase aggregation. Measure the improvement.

4. **Side input vs join.** Compare a `Beam.Map` with a side input against a BigQuery join for
   enriching 100M orders. Measure time, cost, and complexity. Write the recommendation.

5. **Full test suite.** Write a test suite for a realistic pipeline: unit tests for each
   transform, an integration test on the Direct Runner with a real Parquet file, and a
   Dataflow integration test. Get it running in CI.

---

## 📖 Further Reading

- Beam programming model — https://beam.apache.org/documentation/programming-model/
- Beam Python SDK — https://beam.apache.org/documentation/sdks/python/apache-beam-intro/
- Beam Dataflow runner — https://beam.apache.org/documentation/runners/dataflow/
- Dataflow best practices — https://cloud.google.com/dataflow/docs/best-practices
- Apache Beam website — https://beam.apache.org/
