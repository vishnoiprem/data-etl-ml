# Dataflow Course Project — Batch and Streaming Pipelines

A working Apache Beam project for the **Google Dataflow with Apache Beam** course.

Everything here runs **locally with no GCP account, no credentials, and no bill**.
The same code deploys to Dataflow by changing two things: the `--runner` flag and
the path prefix.

---

## What is in here

| File | Purpose |
|------|---------|
| [`transforms.py`](transforms.py) | Shared logic — parsing, validation, currency conversion, the revenue combiner |
| [`beam_options.py`](beam_options.py) | Runner and pipeline-option resolution, `.env` loading |
| [`batch_pipeline.py`](batch_pipeline.py) | Batch ETL: orders → validate → convert currency → revenue per region |
| [`streaming_pipeline.py`](streaming_pipeline.py) | Streaming: events → fixed windows → counts and totals per region |
| [`templates/batch_template.py`](templates/batch_template.py) | Dataflow flex template for the batch pipeline |
| [`templates/streaming_template.py`](templates/streaming_template.py) | Dataflow flex template for the streaming pipeline |
| [`tests/test_transforms.py`](tests/test_transforms.py) | Unit tests for the pure logic — **no Apache Beam required** |
| [`tests/test_pipelines.py`](tests/test_pipelines.py) | Integration tests that run the real pipelines |
| [`requirements.txt`](requirements.txt) | Python dependencies |

---

## Quick start

### 1. Set up the environment

```bash
cd data-engineering/data-Course/google/Dataflow

python3 -m venv .venv
source .venv/bin/activate
pip install -r project/requirements.txt
```

> **Python version.** Apache Beam supports Python 3.10–3.13. The course was
> developed and tested on Python 3.13.

### 2. Generate the sample data

```bash
python resources/sample_data.py --output-dir ./sample_data
```

This creates a deterministic dataset — the same bytes every run, so the
expected outputs in the chapters stay correct.

```
sample_data/
├── orders.csv              5,000 orders
├── orders.ndjson           the same orders as NDJSON
├── events.ndjson          20,000 clickstream events
├── events.csv              the same events as CSV
├── malformed_orders.csv         5 deliberately broken rows
├── product_reference.ndjson    50 product lookup rows
└── summary.json
```

Useful flags:

```bash
# 50% of orders onto one customer — demonstrates key skew
python resources/sample_data.py --output-dir ./sample_data --hot-key-rate 0.5

# Backdate 100 events past their window — demonstrates late data
python resources/sample_data.py --output-dir ./sample_data --late-events 100
```

### 3. Run the batch pipeline

```bash
python project/batch_pipeline.py \
    --input ./sample_data/orders.csv \
    --output ./out/summary
```

Expected output in `./out/summary`:

```csv
region,order_count,revenue_eur
AMER,318,113592.19
APAC,285,108194.92
EMEA,322,118423.22
LATAM,320,110646.18
```

Only `complete` orders are counted. Amounts are converted to EUR using the
static rate table in `transforms.py`.

### 4. Run the streaming pipeline

```bash
python project/streaming_pipeline.py \
    --input ./sample_data/events.ndjson \
    --output ./out/streaming \
    --window-seconds 3600
```

Expected output:

```csv
region,event_count,total_value
APAC,4885,291314.62
EMEA,5099,302548.0
LATAM,4979,299522.51
AMER,5037,302651.93
```

---

## Running the tests

```bash
# The pure logic — works even without apache-beam installed
python3 -m pytest project/tests/test_transforms.py -v

# Everything
python -m pytest project/tests/ -v
```

The pure tests are deliberately separated so you can check your parsing and
aggregation logic in 0.05 seconds, without waiting for Beam to import.

---

## Deploying to Dataflow

The local and cloud runs share the same code. Only the paths and the runner
change.

```bash
export PROJECT_ID=my-project
export REGION=us-central1
export BUCKET=gs://my-bucket

python project/batch_pipeline.py \
    --runner DataflowRunner \
    --project "$PROJECT_ID" \
    --region "$REGION" \
    --input "$BUCKET/orders.csv" \
    --output "$BUCKET/summary" \
    --staging_location "$BUCKET/dataflow/staging" \
    --temp_location "$BUCKET/dataflow/temp"
```

`--staging_location` and `--temp_location` are **required** for Dataflow, and
must be different from every other concurrent job's paths — the default
locations collide.

### Configuration via `.env`

The project reads the repository-root `.env` file if one exists, so a single
checkout can configure every project at once. Recognised variables:

| Variable | Purpose |
|----------|---------|
| `BEAM_RUNNER` | The runner to use (default `BundleBasedDirectRunner`) |
| `PROJECT_ID` | The GCP project |
| `REGION` | The GCP region (default `us-central1`) |
| `TEMP_LOCATION` | The Dataflow temp path |
| `STAGING_LOCATION` | The Dataflow staging path |
| `SERVICE_ACCOUNT_EMAIL` | The worker service account |
| `SUBNETWORK` | The subnetwork for private IP jobs |

---

## Two design decisions worth knowing

### The runner

Beam 2.60+ ships a new Go-based in-process runner under the name
`DirectRunner` (the "Prism" runner). It is faster, but it does not yet
support every trigger and windowing combination — it panics on the
`AfterWatermark` trigger and on the `+inf` watermark evaluation that
`TestPipeline` performs.

The course therefore defaults to `BundleBasedDirectRunner`, the classic
pure-Python runner, which supports the full feature set. Try Prism yourself
with `--runner DirectRunner` on the batch pipeline.

### The guarded import

`transforms.py` splits into a **pure half** (parsing, validation, currency
conversion — standard library only) and a **Beam half** (`ParseOrderFn`,
`RevenueByRegionFn`).

```python
try:
    import apache_beam as beam
    BEAM_AVAILABLE = True
except ImportError:
    BEAM_AVAILABLE = False
    beam = None
```

This is why `tests/test_transforms.py` runs without Beam installed. It also
gives you a pure reference implementation of the combiner —
`build_revenue_summary` — which you can compare against the Beam result to
prove the pipeline is correct.

---

## The transforms this project uses

| Transform | Where |
|-----------|-------|
| `ReadFromText` | both pipelines |
| `ReadFromPubSub` | `streaming_pipeline.py` (`--topic`) |
| `ParDo` + `DoFn` | `ParseOrderFn` in `transforms.py` |
| `Map` | keying, formatting, side-input enrichment |
| `FlatMap` | `CoGroupByKey` unpacking |
| `Filter` | status filtering |
| `Flatten` | multi-source pipelines |
| `CombinePerKey` | `RevenueByRegionFn`, `Count.PerKey` |
| `GroupByKey` | via `CoGroupByKey` |
| `CoGroupByKey` | merging the count and sum aggregations |
| `WindowInto` + `FixedWindows` | the streaming pipeline |
| `AfterWatermark` trigger | the safe streaming trigger |
| `AccumulationMode` | `ACCUMULATING` / `DISCARDING` |
| `WriteToText` | both pipelines |
| `WriteToBigQuery` | optional, via `--bigquery-table` |
| Side inputs | `beam.pvalue.AsIter` for the product reference |
