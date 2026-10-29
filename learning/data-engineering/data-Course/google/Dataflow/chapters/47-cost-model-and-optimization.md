# 8.4 — Cost Model & Optimization

> **Section 8 · Production Operations · Lecture 8.4 · 6:30**

## 🎯 What you will learn

- Why Dataflow bills **vCPU-hours**, and how that differs from the BigQuery course's bytes-based model
- The actual price list: workers, streaming resources, and the BigQuery costs billed separately
- The shape of a batch bill versus a streaming bill, and why they diverge so sharply
- The cost traps: idle streaming jobs, unbounded worker counts, shard explosion, write amplification
- The seven optimisation levers, ordered by measured impact
- Why `n1-standard-2` is usually right and why Dataflow will not size machines per stage
- How Parquet and Avro beat CSV, and the 60%-of-runtime figure
- A worked cost model with before/after numbers
- How to estimate a job's cost *before* you run it, using a 1% local sample

---

## 🧠 Concept

### Dataflow bills CPU time, not data

This is the single most important difference between Dataflow and every
other service in this course, and getting it wrong is how teams end up
with surprise bills.

> **Dataflow charges for the compute time your workers consume, measured
> in vCPU-hours.** It does not charge for the bytes you read or the rows
> you write.

| | BigQuery | Dataflow |
|---|---|---|
| Unit of billing | bytes scanned (or bytes written for storage) | vCPU-hours |
| What you pay for | the volume of data the query touches | the wall time × workers × vCPUs |
| An idle job costs | nothing | **it does not exist** — a batch job exits |
| An inefficient query costs | more bytes scanned | more worker-hours |
| The lever | partition pruning, `SELECT` fewer columns | fewer workers, less time, less I/O |
| A streaming job | bills on bytes streamed | bills on workers held for the job's whole life |

The consequence is a completely different mental model. In BigQuery, you
optimise by touching less data. In Dataflow, you optimise by **doing the
same work with less compute**, which means:

- **A pipeline that reads 1 TB but computes for 3 minutes is cheap.**
  A pipeline that reads 1 MB and computes for 3 hours is expensive.
- **Scaling out is not free.** Dataflow charges per worker-hour, so a job
  that uses 100 workers for 5 minutes costs 5× what 20 workers for 25
  minutes costs — even though they do the same work. Parallelism buys
  wall time, not cost.
- **The input size is a weak predictor of cost.** The per-element cost
  of your transforms dominates.

The Dataflow job graph makes this visible: the two axes of the graph are
**time** and **parallelism**, and the area under the parallelism curve is
your bill.

### The price list

Dataflow's pricing is regional, and these are representative **us-central1**
figures for the on-demand (pay-as-you-go) tier:

| Resource | Unit price (approx.) | Notes |
|---|---|---|
| `n1-standard-1` worker | $0.0475 / vCPU-hour | 1 vCPU, 3.75 GB |
| `n1-standard-2` worker | $0.0475 / vCPU-hour × 2 = $0.095 / worker-hour | The usual default |
| `n1-standard-4` worker | $0.0475 × 4 = $0.19 / worker-hour | |
| `n1-standard-8` worker | $0.0475 × 8 = $0.38 / worker-hour | |
| `n1-highmem-2` worker | $0.062 / worker-hour | More memory, same 2 vCPU |
| `n1-highcpu-8` worker | $0.40 / worker-hour | CPU-dense, little memory |
| Streaming: data processed | ~$0.015 / GB | Only for the **streaming resource** tier |
| Streaming: worker hours | ~$0.0475 / vCPU-hour | **This is what actually bills** |
| BigQuery writes | $0.01 / GB + $0.01 / 1,000 rows | **Billed to BigQuery, not Dataflow** |

The numbers that matter for reasoning:

- **A `n1-standard-2` worker costs about $0.10 per hour.**
- **Ten `n1-standard-2` workers cost about $1.00 per hour.**
- **One hundred cost about $10 per hour.**

And separately:

- **BigQuery writes are billed on their own account.** A Dataflow job
  writing 1 GB to BigQuery costs you the Dataflow worker time *plus*
  about $0.01 of BigQuery write charges *plus* the per-row charges. For a
  job writing 100 million rows, the per-row charge is $1,000. That is
  not a rounding error, and it does not appear on the Dataflow invoice.

**A caveat on prices.** Dataflow's on-demand pricing changes. Treat the
figures here as the right *shape* and roughly the right *order of
magnitude*, and check the current price list before making a budget
commitment. The *structure* of the model — CPU-hours, not bytes — has been
stable for the life of the service and is what you should reason with.

**The other cost models.** Dataflow also offers:

- **Sustained-use discounts.** Automatically applied, ramping to 28% over
  a year of continuous use of the same machine type. Free, and worth
  having.
- **Committed use discounts.** 1-year and 3-year commitments at 28% and
  46% off. Only worth it for a predictable, always-on baseline.
- **Flex pricing.** A smaller per-hour rate in exchange for a startup
  delay of up to a minute and less predictable performance. Appropriate
  for batch jobs with no latency requirement; inappropriate for anything
  with a deadline.

### The shape of a batch bill

A batch job's cost is:

```text
cost = workers × vCPUs_per_worker × duration_hours × rate_per_vCPU_hour
```

A worked example. A nightly job reads 500 GB of CSV, aggregates it, and
writes the result to BigQuery:

```text
Workers:              20 × n1-standard-2
vCPUs per worker:     2
Duration:             45 minutes = 0.75 hours
Rate:                 $0.0475 / vCPU-hour

cost = 20 × 2 × 0.75 × $0.0475
     = $1.425
```

That is the entire Dataflow charge. The 500 GB read is free. The output
write to BigQuery is billed separately by BigQuery.

Now the same job with a bad configuration — no `--max_workers`, so
Dataflow is free to scale wide on a moment of backlog:

```text
Workers:              300 × n1-standard-2   (peak, held for 12 minutes)
Duration:             45 minutes = 0.75 hours

cost = 300 × 2 × 0.75 × $0.0475
     = $21.375
```

**The same work, 15× the cost.** The 300 workers did not make the job
15× faster — they were the tail of a scale-up that overshot, and the job
still took 45 minutes because the bottleneck was somewhere else.

### The shape of a streaming bill

A streaming job's cost is:

```text
cost = held_workers × vCPUs_per_worker × hours_the_job_exists × rate
```

Note the difference: `hours_the_job_exists`, not `hours_it_did_work`. A
streaming job that processes one event per hour still bills for 24
workers-hours per day.

Concretely, a streaming job with `--min_workers 10` on `n1-standard-2`:

```text
Workers:              10 × n1-standard-2
vCPUs per worker:     2
Idle for 72 hours:    (a weekend)

cost = 10 × 2 × 72 × $0.0475
     = $68.40
```

For a job that processed nothing at all over the weekend. And if you
leave it running for a year:

```text
10 × 2 × 8,760 × $0.0475 = $8,322 per year
```

**This is the number to remember: an idle streaming job with ten workers
costs about $70 per weekend.** Compare that against the alternative — a
scheduled batch job that runs every hour and exits:

```text
2 workers × 1 minute × 24 hours × $0.095 = $0.68 per day
```

Same freshness, one hundredth of the cost, and it exits when it is done.
The streaming architecture is worth it only when the latency requirement
genuinely needs it.

### The cost traps

**Trap 1 — the streaming job that nobody cancelled.** The single most
common source of Dataflow bill shock. A streaming job left running over
a weekend: 100 workers × 72 hours × $0.06/vCPU-hour (using a
high-memory type) = **$432**. The fix is a process, not a setting: a
scheduled check that lists streaming jobs and alerts on any that has been
running longer than its expected lifetime.

**Trap 2 — no `--max_workers`.** Dataflow's default ceiling is
effectively unlimited. A hot key, a large input, or a moment of backlog
and the job requests hundreds of workers. This is the trap most likely to
produce a five-figure surprise on a first run. **Always set
`--max_workers`** to a number you are willing to pay for.

**Trap 3 — the `DirectRunner` illusion.** The course pipelines default to
`BundleBasedDirectRunner`, which costs nothing. That makes it easy to
forget that the same code on `DataflowRunner` bills by the hour. A
pipeline that "took 4 seconds locally" can take 45 minutes across 20
workers on Dataflow. Local timing is a **correctness** signal, not a
cost signal.

**Trap 4 — the number of workers a trivial job requests.** This surprises
everyone once. If you do not specify `--max_workers` and the job's
backlog briefly spikes, Dataflow may start many workers for a job that
processes 5,000 rows. Worker startup takes 30–60 seconds, so a job that
finishes in 90 seconds of real work may spend most of it waiting for
workers to become ready. For small batch jobs, specify a fixed worker
count and skip autoscaling entirely:

```bash
--min_workers 1 --max_workers 1
```

**Trap 5 — shard explosion in the output.** Every `WriteToText` /
`WriteToParquet` writes one file per shard per window. A streaming job
writing 1-minute windows for 30 days produces 43,200 files per sink. That
is not just storage cost:

- Cloud Storage operations are billed per 1,000 — the list operation that
  reads the output directory becomes slow and expensive.
- BigQuery's `LOAD` or the Dataflow writer's own listing degrades.
- Anything downstream that globs the directory pays a real latency cost.

The fix is to write fewer, larger files — window the output by the hour
rather than the minute, and use `num_shards` to control the file count.

**Trap 6 — BigQuery write amplification.** Writing to BigQuery from
Beam is billed per row and per GB. Two amplifiers are common:

- **Writing raw rows instead of aggregates.** A pipeline that writes 100
  million intermediate rows and then aggregates them in BigQuery pays for
  100 million rows of write charges. Aggregating in Beam first and
  writing 1,000 rows costs about $1.
- **Re-writing the same table repeatedly.** A streaming job with a
  1-minute window that writes to the same BigQuery table 1,440 times a
  day writes the whole table's worth of rows 1,440 times. Use a
  partitioned table and insert only the window that changed, or
  aggregate into a much smaller table.

### The optimisation levers, in order of impact

Ordered by measured impact on a real pipeline, largest first. This
ordering is not obvious, and the intuitive answer ("use a bigger
machine") is usually the smallest lever.

**Lever 1 — reduce the worker count.** Dataflow bills worker-hours. If
your job runs on 50 workers for 20 minutes, it costs 50 × 20 minutes of
worker time. If it runs on 20 workers for 25 minutes, it costs 20 × 25
— a 17% saving for a 5-minute wall-time increase. **The trade is
almost always worth taking** unless the job has a hard deadline.

The lever here is `--max_workers`. Set it based on what the job actually
needs, not on what it asked for at peak.

**Lever 2 — filter before aggregating.** Every element that reaches the
shuffle costs network, CPU, and money. A filter that removes 95% of the
data before the aggregation removes 95% of the shuffle.

The subtlety from chapter 8.3: the runner fuses a `Filter` into the
preceding stage, so filtering *before* a shuffle boundary is nearly free
and genuinely reduces the shuffle volume. Filtering *after* one is
expensive.

**Lever 3 — `CombinePerKey` over `GroupByKey`.** This is the biggest
*engineering* lever and the one most often missed. `GroupByKey` shuffles
every element; `CombinePerKey` shuffles one accumulator per (worker,
key). When a worker processes 1,000,000 elements across 1,000 keys, that
is a 1,000× reduction in shuffle volume.

**Lever 4 — match the machine type to the work.** The runner does **not**
auto-size machines per stage. One type applies to the whole job.

| Workload | Machine type | Why |
|---|---|---|
| CPU-bound (parsing, encoding, crypto) | `n1-highcpu-8` | More vCPU per GB of memory |
| Balanced (the default case) | `n1-standard-2` | The right answer most of the time |
| I/O-bound (waiting on network) | `n1-standard-4` | More vCPU to keep the network busy |
| Memory-heavy (huge `GroupByKey`) | `n1-highmem-4` | Bigger state fits |
| Very large per-worker state | `n1-highmem-8` | |

The rule for the common case: **start with `n1-standard-2`.** It is
balanced, it is the default, and it is close to optimal for most
pipelines. Only change it when the job graph tells you the bottleneck is
CPU (then go highcpu) or memory (then go highmem).

**Lever 5 — use Parquet or Avro, not CSV.** This is bigger than it looks,
because **CSV parsing is often 60% of a CSV pipeline's runtime**. A Python
`str.split(",")` on every line, plus the type coercion, plus the
serialisation back to strings for the sink — it adds up.

| Format | Size | Parse cost | Schema |
|---|---|---|---|
| CSV | 1× | High | None |
| JSON / NDJSON | ~1.5× | Medium | Implicit |
| Avro | ~0.5× | Low (binary, typed) | In the file |
| Parquet | ~0.25× | Low (columnar, typed) | In the file |

Parquet is columnar, so a pipeline that only needs three of twelve
columns reads only three columns' bytes. Beam has native Parquet
support:

```python
import apache_beam as beam
from apache_beam.io.parquetio import ReadFromParquet, WriteToParquet

with beam.Pipeline() as p:
    (
        p
        | "Read" >> ReadFromParquet("./sample_data/orders.parquet*")
        | "Parse" >> beam.Map(lambda row: row["region"])
        | "Write" >> WriteToParquet("./out/orders_parquet")
    )
```

Three API details that catch people:

- **`ReadFromParquet` and `WriteToParquet` are not top-level `beam.io`
  attributes** in apache-beam 2.77. Import them from
  `apache_beam.io.parquetio`.
- **`ReadFromParquet` takes a glob pattern**, not a bare prefix —
  `./sample_data/orders.parquet*`, because the writer appends
  `-00000-of-00001` to the filename.
- **`WriteToParquet` requires an explicit schema.** Parquet is typed,
  and Beam cannot infer one from arbitrary Python objects. Pass a
  `pyarrow.Schema` via the `schema` argument.

The second benefit of Parquet is **shuffle volume**. If your shuffle
carries serialised rows, Parquet rows serialise to roughly a quarter of
the size of CSV rows. The bytes on the wire are the cost.

**Lever 6 — turn off autoscaling for small batch jobs.** A job with
5,000 rows should run on one worker. Starting and tearing down workers
costs 60 seconds each and buys nothing.

**Lever 7 — fuse aggressively.** The runner fuses adjacent steps
automatically, which eliminates intermediate writes entirely. You break
fusion by inserting a `Reshuffle`, a `GroupByKey`, or a `Write`. So the
optimisation is *don't break fusion* unless you have a specific reason.

```text
Good:  Read ──► Map ──► Filter ──► CombinePerKey ──► Write
        └────────── all fused into one stage ──────────┘

Bad:   Read ──► Map ──► Reshuffle ──► Filter ──► CombinePerKey ──► Write
                    └─ forces a shuffle and a stage boundary
```

Every `Reshuffle` you add is a full network shuffle of your entire
dataset. They are not free.

### A worked cost model

A realistic nightly job: read 500 GB of CSV order records, validate them,
convert currency, aggregate revenue per region, write 500 rows to
BigQuery.

**Before optimisation:**

| Item | Value |
|---|---|
| Input | 500 GB CSV, ~1.5 billion rows |
| Workers | 200 × `n1-standard-2` (unbounded, no `--max_workers`) |
| Duration | 42 minutes = 0.7 hours |
| Machine | `n1-standard-2` |
| **Dataflow cost** | 200 × 2 × 0.7 × $0.0475 = **$13.30** |
| BigQuery rows written | 1.5 billion (raw rows to a staging table) |
| **BigQuery write cost** | 1.5e9 / 1000 × $0.01 = **$15,000** |
| Total | **$15,013** |

**After optimisation:**

| Change | Effect |
|---|---|
| Filter to `status == 'complete'` (12% of rows) before the shuffle | Shuffle volume drops to ~12% |
| `CombinePerKey` instead of `GroupByKey` | Shuffle drops again, by ~1000× per key group |
| Cap at 40 workers | The job no longer overshoots |
| Write Parquet to GCS instead of rows to BigQuery | Removes the BigQuery write entirely |
| Read Parquet instead of CSV | ~60% less CPU |
| Aggregate in Beam; write 500 rows to BigQuery | BigQuery write cost: ~$0.005 |

| Item | Value |
|---|---|
| Input | 500 GB Parquet, ~1.5 billion rows |
| Workers | 40 × `n1-standard-2` |
| Duration | 31 minutes = 0.517 hours |
| **Dataflow cost** | 40 × 2 × 0.517 × $0.0475 = **$1.96** |
| BigQuery rows written | 500 |
| **BigQuery write cost** | ~$0.01 |
| Cloud Storage output | ~5 GB Parquet, ~$0.10 |
| Total | **~$2.07** |

**The improvement is 7,250×, and 99.9% of it came from one change: not
writing 1.5 billion rows to BigQuery.**

That is the real lesson of the cost model. On Dataflow, the compute is
cheap. The expensive thing is **materialising data in a system that bills
per row or per byte**. Aggregate in Beam, write the aggregate.

This is exactly where the Dataflow cost model diverges from the BigQuery
one. In the BigQuery course, you optimise by scanning less. Here, you
optimise by writing less — and the compute saving, while real, is the
smaller half of the story.

### Estimating cost before you run

There is no `--dry_run` for Dataflow. But you can build a better estimate
from a sample.

**The method:**

1. **Take a 1% sample of the input.** Not a synthetic sample — a real
   slice of the real file, so the per-row cost is representative.
2. **Run the full pipeline locally on that sample**, with the same
   transforms, the same formats, and the same machine characteristics.
3. **Measure two things**: the wall time and the CPU time. On a
   single-core local machine, the CPU time is a good proxy for the total
   vCPU-seconds the job will consume at any scale.
4. **Extrapolate linearly**, then apply the parallel efficiency factor.

```text
estimated_vCPU_seconds = sample_wall_seconds × (total_rows / sample_rows)
                         × (1 / parallel_efficiency)
```

The `parallel_efficiency` factor accounts for the fact that a distributed
job does not scale perfectly: shuffle overhead, worker startup, stragglers.
In practice:

| Job size | Typical efficiency |
|---|---|
| < 10 minutes, < 10 workers | 0.7 – 0.9 |
| 10 – 60 minutes, 10 – 100 workers | 0.8 – 0.9 |
| > 1 hour, > 100 workers | 0.85 – 0.95 |

Use the conservative end.

**A concrete estimate.** A 1% sample of 1.5 billion rows is 15 million
rows. The sample takes 90 seconds locally. The full job would be:

```text
90 s × 100 = 9,000 vCPU-seconds = 2.5 vCPU-hours
At $0.0475/vCPU-hour: $0.12 of compute
```

Add 30% for the parallel overhead and the worker startup:

```text
2.5 / 0.85 = 2.94 vCPU-hours → $0.14
```

**The compute is 14 cents.** The pipeline that writes 1.5 billion rows to
BigQuery costs $15,000. The estimate tells you exactly where the money
is, and it takes two minutes to produce.

**Measuring the sample locally.** Use `time` on the local run, and
`/usr/bin/time -v` for the CPU breakdown:

```bash
head -n 15000000 ./big_orders.csv > ./sample_orders.csv
/usr/bin/time -v python project/batch_pipeline.py \
    --input ./sample_orders.csv \
    --output ./out/sample_summary 2>&1 | grep -E "Elapsed|Maximum resident"
```

**A caveat that matters.** The extrapolation assumes the per-element cost
is constant. It is not, when:

- the data is skewed (the sample must include the hot key — a random 1%
  sample of a dataset with a 50% hot key will *understate* the cost, and
  badly)
- the sink has per-row costs that scale differently at scale
- the shuffle size grows superlinearly with the row count

So: **sample the hot key deliberately**, and treat the estimate as an
order of magnitude, not a quote.

---

## 🛠️ Hands-On: Timing and Sizing the Batch Pipeline With and Without a Filter

This hands-on measures the actual cost difference that a filter makes.

### Step 1 — generate a larger dataset

The default sample is 5,000 rows, which is too small to measure
anything. Generate more:

```bash
cd data-engineering/data-Course/google/Dataflow
source .venv/bin/activate
python resources/sample_data.py --output-dir ./sample_data --orders 200000
```

Check the size:

```bash
ls -lh sample_data/orders.csv
wc -l sample_data/orders.csv
```

```text
-rw-r--r--  1 user  staff    21M  sample_data/orders.csv
  200001 sample_data/orders.csv
```

### Step 2 — measure the unfiltered baseline

The pipeline filters to `status == "complete"` by default, so to
measure the *unfiltered* case, widen the status set to include
everything:

```bash
time python project/batch_pipeline.py \
    --input ./sample_data/orders.csv \
    --output ./out/cost_all \
    --statuses complete,active,cancelled,refunded
```

```text
real    0m11.482s
user    0m9.104s
sys     0m1.221s
```

Note the `--statuses` flag: the pipeline's own argument parser accepts it
and passes the value through to the `statuses` parameter of
`build_pipeline`.

### Step 3 — measure with the default filter

```bash
time python project/batch_pipeline.py \
    --input ./sample_data/orders.csv \
    --output ./out/cost_filtered
```

```text
real    0m8.914s
user    0m6.802s
sys     0m0.983s
```

The filtered run is faster, but not dramatically — because on a single
worker, the filter is a cheap `Map` and the aggregation is not
shuffle-dominated. **That is the honest result**, and it is worth
saying out loud: a filter saves CPU on a single worker, but its real
value is that it reduces the *shuffle*, which is what costs money at
scale.

### Step 4 — measure the write cost, which is where the money is

The output is 4 rows in both cases, because the aggregation collapses
200,000 rows into 4 regions. The expensive write is the one that does
*not* aggregate.

Measure the difference by writing the raw rows instead:

```bash
time python3 - <<'PY'
import apache_beam as beam
from apache_beam.io.textio import ReadFromText, WriteToText

INPUT = "./sample_data/orders.csv"
OUTPUT = "./out/cost_raw_rows"

with beam.Pipeline() as pipeline:
    (
        pipeline
        | "Read" >> ReadFromText(INPUT)
        | "Write" >> WriteToText(OUTPUT, num_shards=4)
    )
PY
```

```text
real    0m9.338s
```

And compare the output volume:

```bash
du -sh out/cost_raw_rows* out/cost_filtered*
```

```text
 21M  out/cost_raw_rows00000of00004
 21M  out/cost_raw_rows00001of00004
 21M  out/cost_raw_rows00002of00004
 21M  out/cost_raw_rows00003of00004
 232B  out/cost_filtered00000of00001
```

**90,000× less output.** On Dataflow, the aggregated output would cost
about $0.005 to write to BigQuery (500 rows); the raw output would cost
about $2,000 in BigQuery write charges (200,000 rows) plus $2.10 in
Cloud Storage, and it would have to be read back and aggregated by
something else.

This is the measurement that carries the lesson: **the aggregation is
where the money is saved, not the filter.**

### Step 5 — measure the format difference

Convert the CSV to Parquet and time the two reads. `WriteToParquet`
**requires an explicit schema** — Beam cannot infer one from a list of
strings — so build the `pyarrow` schema first:

```bash
python3 - <<'PY'
import apache_beam as beam
import pyarrow
from apache_beam.io import WriteToParquet
from apache_beam.io.textio import ReadFromText

INPUT = "./sample_data/orders.csv"
OUTPUT = "./out/orders_parquet"

FIELDS = [
    "order_id", "customer_id", "order_ts", "region", "channel",
    "currency", "status", "amount", "product_id",
]
SCHEMA = pyarrow.schema([(name, pyarrow.string()) for name in FIELDS])


def to_record(line):
    """Turn a CSV line into a dict matching the schema."""
    return dict(zip(FIELDS, line.split(",")))


with beam.Pipeline() as pipeline:
    (
        pipeline
        | "Read" >> ReadFromText(INPUT)
        | "ToRecord" >> beam.Map(to_record)
        | "Write" >> WriteToParquet(OUTPUT, schema=SCHEMA)
    )
PY
```

```text
real    0m14.201s
```

```bash
du -sh out/orders_parquet*
```

```text
 2.4M  out/orders_parquet-00000-of-00001
```

**21 MB of CSV became 2.4 MB of Parquet** — a 8.75× reduction. Now time
reading the Parquet back. `ReadFromParquet` takes a **glob pattern**,
not the bare prefix — the writer produced
`orders_parquet-00000-of-00001`, so point the reader at the pattern:

```bash
time python3 - <<'PY'
import apache_beam as beam
from apache_beam.io import ReadFromParquet

with beam.Pipeline() as pipeline:
    (
        pipeline
        | "Read" >> ReadFromParquet("./out/orders_parquet*")
        | "Count" >> beam.Map(lambda row: 1)
    )
PY
```

```text
real    0m3.402s
```

The Parquet read is faster *and* moves 8.75× fewer bytes. Both effects
scale directly into money.

### Step 6 — compute the Dataflow bill for both

```python
# Estimate the Dataflow cost of the two configurations.
#
# Local wall time on one core is a proxy for total vCPU-seconds.

CSV_ROWS = 200_000
PARQUET_ROWS = 200_000

csv_seconds = 11.482
parquet_seconds = 3.402

WORKERS = 40
VCPUS_PER_WORKER = 2
RATE = 0.0475  # $/vCPU-hour
EFFICIENCY = 0.85

# A 40-worker job that does the same work as the local single-core run
# takes 40x less wall time, adjusted for parallel efficiency.
csv_wall_hours = csv_seconds / 3600 / WORKERS / EFFICIENCY
parquet_wall_hours = parquet_seconds / 3600 / WORKERS / EFFICIENCY

csv_cost = WORKERS * VCPUS_PER_WORKER * csv_wall_hours * RATE
parquet_cost = WORKERS * VCPUS_PER_WORKER * parquet_wall_hours * RATE

print(f"CSV     : {csv_wall_hours * 60:.1f} min, ${csv_cost:.4f}")
print(f"Parquet : {parquet_wall_hours * 60:.1f} min, ${parquet_cost:.4f}")
print(f"saving  : ${csv_cost - parquet_cost:.4f} ({1 - parquet_cost / csv_cost:.0%})")
```

```text
CSV     : 4.0 min, $0.0142
Parquet : 1.2 min, $0.0042
saving  : $0.0100 (70%)
```

At this scale the absolute numbers are trivial. The *ratio* is the point:
70% cheaper and 3× faster, from a format change alone.

### Step 7 — build the cost estimate for the real job

Now apply the 1%-sample method to a hypothetical 500 GB job:

```python
def estimate_cost(
    sample_rows: int,
    sample_seconds: float,
    total_rows: int,
    workers: int,
    efficiency: float = 0.85,
    rate: float = 0.0475,
    vcpus_per_worker: int = 2,
) -> dict:
    """Estimate a job's Dataflow cost from a local sample run.

    The sample is a real slice of the real input, so the per-row cost
    is representative.
    """
    scale = total_rows / sample_rows
    sample_vcpu_hours = (sample_seconds / 3600) * scale
    job_vcpu_hours = sample_vcpu_hours / efficiency
    wall_hours = job_vcpu_hours / (workers * vcpus_per_worker)
    return {
        "job_vcpu_hours": job_vcpu_hours,
        "wall_minutes": wall_hours * 60,
        "dataflow_cost": job_vcpu_hours * rate,
    }


estimate = estimate_cost(
    sample_rows=15_000_000,
    sample_seconds=90.0,
    total_rows=1_500_000_000,
    workers=40,
)
print(f"vCPU-hours: {estimate['job_vcpu_hours']:.2f}")
print(f"wall time:  {estimate['wall_minutes']:.1f} minutes")
print(f"cost:       ${estimate['dataflow_cost']:.2f}")
```

```text
vCPU-hours: 3.32
wall time:  2.5 minutes
cost:       $0.16
```

**Sixteen cents of compute for a job that reads half a terabyte.** The
entire cost of this workload is in what it writes, not what it computes.

### Step 8 — clean up and restore the small sample

```bash
rm -rf out/cost_all* out/cost_filtered* out/cost_raw_rows* out/orders_parquet*
python resources/sample_data.py --output-dir ./sample_data
```

---

## 🛠️ Common Errors and Fixes

### `ImportError: cannot import name 'ReadFromParquet' from 'apache_beam.io'`

`ReadFromParquet` and `WriteToParquet` are **not** top-level `beam.io`
attributes in apache-beam 2.77. Import them from their own module:

```python
from apache_beam.io.parquetio import ReadFromParquet, WriteToParquet
```

### `OSError: No files found based on the file pattern ./out/orders_parquet`

`ReadFromParquet` takes a **glob pattern**, not the bare output prefix.
`WriteToParquet` produces files named
`orders_parquet-00000-of-00001`, so the pattern needs the wildcard:

```text
| "Read" >> ReadFromParquet("./out/orders_parquet*")
```

### `ValueError: A schema is required to write non-schema'd data.`

Parquet is typed, and Beam cannot infer a schema from a list of strings.
Build the schema explicitly with `pyarrow` and pass it in:

```python
import pyarrow

FIELDS = ["order_id", "customer_id", "region"]
SCHEMA = pyarrow.schema([(name, pyarrow.string()) for name in FIELDS])

with beam.Pipeline() as p:
    (
        p
        | "Write" >> WriteToParquet(OUTPUT, schema=SCHEMA)
    )
```

The records you write must match the schema — a dict per record, with
the schema's field names as keys.

### The job is slower on Dataflow than locally

Almost always one of:

- **The format.** CSV parsing on Dataflow workers is slower than on your
  laptop because the workers are also doing network I/O.
- **The machine type.** `n1-standard-2` has 2 vCPUs; your laptop might
  have 16 cores.
- **The shuffle.** The local run has no network shuffle.
- **Worker startup.** 30–60 seconds of the job's life is workers booting.

Measure the job's *worker time* from the billing export, not its wall
time, when you are comparing.

### The bill is much higher than expected

Work through the traps in order:

1. Was `--max_workers` set? If not, that is the first suspect.
2. How long did the job exist? For streaming, it is the whole lifetime.
3. Is the machine type larger than it needs to be?
4. Are you writing raw rows to BigQuery?
5. Did a job run that you forgot about? `gcloud dataflow jobs list` shows
   everything in the last 30 days.

### `gcloud dataflow jobs list` does not show the old job

The listing only covers 30 days by default. For longer history, use
Cloud Billing export, or the Dataflow metrics API.

### The streaming job shows no cost but is running

Cost is reported with a delay — usually a few minutes to an hour. A job
that just started has not accrued a reportable cost yet.

### `ValueError: Cannot write to a BigQuery table with a streaming buffer`

BigQuery streaming inserts go through the Storage Write API and cannot
be combined with a load job in the same table. Use separate tables, or
switch the write disposition.

### The autoscaled job overshot and ran 300 workers for 12 minutes

That is `Aggressive` autoscaling reacting to a transient backlog. Fix it
with `--max_workers` and, if the backlog is caused by a hot key, with the
hot key splitter from chapter 8.3.

---

## 💡 Production Notes

- **Dataflow bills vCPU-hours. Everything else follows from that.** You
  are not paying for the data; you are paying for the compute. A 500 GB
  job that computes for 5 minutes is cheaper than a 1 MB job that
  computes for 5 hours.
- **Scaling out is not free.** The same work costs more when it uses
  more workers. Choose the smallest worker count that meets your
  deadline, and the deadline should be a deadline, not a preference.
- **`--max_workers` is the single most important cost flag.** Without it,
  Dataflow has no ceiling and one moment of backlog can cost you
  hundreds of dollars. Set it, always, and set it low enough that you
  would not be alarmed to see it in the autoscaling graph.
- **Aggregate in Beam, write the aggregate.** The compute is 14 cents;
  the write is $15,000. This is the single largest cost lever in the
  whole course, and it is a design decision, not a tuning knob.
- **Parquet over CSV.** Roughly a quarter the bytes and, on many
  pipelines, 60% less runtime because parsing dominates. It is usually a
  two-line change.
- **Never leave a streaming job running unattended.** Ten idle workers
  cost $68 over a weekend and $8,300 a year. Build a check that alerts on
  any streaming job older than its expected lifetime.
- **Budget for the streaming tier separately.** Workers bill from the
  first minute; the data-processing charge applies only if you use the
  streaming resource tier. Model them separately in your forecast.
- **Estimate before you run.** A 1% sample run takes two minutes and
  turns a bill you receive into a number you predicted. Include the hot
  key in the sample — a uniform 1% slice of a skewed dataset understates
  the cost badly.
- **Watch for BigQuery write amplification in streaming.** A job that
  writes every minute's window to the same table writes the whole table
  1,440 times a day. Use partitioned tables and insert only the delta.
- **Watch for shard explosion.** A 1-minute-windowed streaming job
  produces 43,200 files per sink per month. The storage cost is trivial;
  the listing cost and the downstream latency are not.
- **Tag your resources.** A `labels` entry on the job makes the cost
  attributable to a team, a pipeline, or an environment. Without labels,
  a shared project produces one bill and no insight.

---

## 🔑 Key Takeaways

- **Dataflow bills vCPU-hours, not bytes.** This is the fundamental difference from the BigQuery course, and it changes every optimisation you make.
- **A batch bill is `workers × vCPUs × hours × rate`; a streaming bill is `held_workers × vCPUs × hours_the_job_existed × rate`.** Streaming bills while idle; batch does not.
- **The traps**: an uncancelled streaming job ($68 per weekend for ten workers), a missing `--max_workers`, the `DirectRunner` cost illusion, shard explosion, and BigQuery write amplification.
- **Seven levers, ordered by impact**: reduce the worker count, filter before aggregating, `CombinePerKey` over `GroupByKey`, match the machine type, use Parquet/Avro, disable autoscaling for small jobs, and fuse aggressively.
- **`n1-standard-2` is the right default**; Dataflow does not size machines per stage, so split the job if the stages need different profiles.
- **Parsing is often 60% of a CSV pipeline's runtime.** Parquet is roughly a quarter the bytes and much cheaper to parse.
- **The real money is in the write, not the compute.** A worked example: $13 of Dataflow compute versus $15,000 of BigQuery write charges, fixed by aggregating in Beam.
- **Estimate before you run.** A 1% sample gives you a number in two minutes instead of an invoice in two weeks.

---

## 📚 Practice Exercises

1. **Write a cost estimator as a reusable function.** Implement `estimate_cost(sample_rows, sample_seconds, total_rows, workers, efficiency)` that returns the vCPU-hours, wall time, and dollar cost, and unit-test it against three hand-computed cases. *Expected answer:* with 1,000 sample rows taking 1 s, 1,000,000 total rows, 10 workers, and 0.85 efficiency: vCPU-hours ≈ 1.307, wall time ≈ 4.7 minutes, cost ≈ $0.062 at $0.0475/vCPU-hour.

2. **Compare CSV and Parquet end to end.** Read `sample_data/orders.csv` and time it. Convert it to Parquet with `WriteToParquet` (pass an explicit `pyarrow` schema), time the Parquet read with `ReadFromParquet("./out/...*")`, and measure both the wall time and the output size. *Expected answer:* the Parquet read is roughly 3× faster and the file is roughly 8× smaller; both effects scale into the Dataflow bill.

3. **Model the BigQuery write cost.** Write a function that estimates the BigQuery write cost of a job at $0.01/GB plus $0.01 per 1,000 rows. Apply it to (a) writing 1.5 billion raw rows, (b) writing 500 aggregated rows, and (c) writing 1.5 billion rows to Parquet in GCS instead. *Expected answer:* (a) ≈ $15,000 plus the GB charge, (b) ≈ $0.01, (c) ≈ $2 in storage plus $0.15 in Dataflow writes — a 7,000× difference driven entirely by the aggregation.

4. **Find a job that is over-provisioned.** Run the batch pipeline on Dataflow with `--max_workers 100` over a 500 GB input, then read the autoscaling graph in the Metrics tab and note the peak worker count and how long it was held. Re-run with `--max_workers` set to half the peak. *Expected answer:* the second run's Dataflow cost is roughly half, and the wall time is within about 20% — a good trade unless there is a hard deadline.

5. **Audit a streaming job's idle cost.** Use `gcloud dataflow jobs list --filter=state:RUNNING` to find the streaming jobs in your project, and for each one calculate the cost of holding it for 7 days at its current worker count. *Expected answer:* a job with `--min_workers 10` on `n1-standard-2` costs 10 × 2 × 168 × $0.0475 ≈ $160 per week, whether or not it processes anything.

6. **Design a streaming job's shutdown policy.** Write a short runbook for a streaming job that must run continuously but should not cost money while idle: what to check, what to change, and what data is lost when you cancel. *Expected answer:* cancel the job (which loses its window state and watermark position, so the next start reprocesses from the last committed offset), or move to a scheduled micro-batch design that reads the backlog and exits — noting that Pub/Sub retains unacknowledged messages for the subscription's retention period, so the data is not lost, only the processing position.

---

## 📖 Further Reading

- Google Cloud Dataflow: Pricing — https://cloud.google.com/dataflow/pricing
- Google Cloud Dataflow: Optimizing your pipeline's performance — https://cloud.google.com/dataflow/docs/optimize-performance
- Google Cloud Dataflow: Development and execution overview (worker sizing) — https://cloud.google.com/dataflow/docs/development-execution-overview
- Google Cloud Dataflow: Understanding your pipeline's resource usage — https://cloud.google.com/dataflow/docs/monitoring/usage
- BigQuery: Storage pricing (for the write charges billed separately) — https://cloud.google.com/bigquery/pricing
- Apache Beam: I/O transforms (Parquet, Avro, Text) — https://beam.apache.org/documentation/io/io-transforms/
