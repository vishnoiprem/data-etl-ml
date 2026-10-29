# 4.4 — Saving to GCS

> **Section 4 · GCP Setup & Local Execution · Lecture 4.4 · 6:30**

## 🎯 What you will learn

- How writing to `gs://` differs from writing to a local path — the answer is: the path string
- How Beam's filesystem abstraction picks the right backend from the URI scheme
- The GCS connector: what it actually is, and which package provides it
- Why a local runner still needs the GCS connector when the path is `gs://`
- The staging and temp location requirement, and what happens when they are missing
- How to read back what you wrote
- The "many small files" trap, and the shard-explosion problem
- `gsutil` and `gcloud storage` for inspection
- Cleanup and lifecycle rules

---

## 🧠 Concept

> **This module is optional**, but unlike chapters 4.1 and 4.2, this one
> has a part you can run right now. The filesystem abstraction in Beam is
> the same for local paths and `gs://` paths, and understanding it is
> useful even if you never deploy.

### The path is the only thing that changes

This is the headline, and it is worth internalising before anything else:

> **To write to Cloud Storage instead of the local disk, change the path
> string. Nothing else.**

```python
# Local
OUTPUT = "./out/summary"

# Cloud Storage
OUTPUT = "gs://my-bucket/summary"
```

The transform is the same:

```python
beam.io.WriteToText(OUTPUT)
```

Beam does not have a separate "GCS sink". It has a **filesystem
abstraction**, and the URI scheme in the path selects the
implementation.

```text
              ┌──────────────────────────────────────┐
  "./out/x"  │ LocalFileSystem   (os, posix paths)   │
              ├──────────────────────────────────────┤
  "gs://b/x" │ GCSFileSystem     (google-cloud-storage)│
              ├──────────────────────────────────────┤
  "hdfs://…" │ HadoopFileSystem                    │
              ├──────────────────────────────────────┤
  "s3://…"   │ S3FileSystem                         │
              └──────────────────────────────────────┘
```

The dispatch happens in `apache_beam.io.filesystems.FileSystems`, which
looks up the scheme, finds the registered `FileSystem` subclass, and
instantiates it with the pipeline options.

You can see the registry yourself:

```python
from apache_beam.io.filesystems import FileSystems

print(FileSystems.get_scheme("gs://my-bucket/path"))
print(FileSystems.get_scheme("./local/path"))
```

```text
gs
None
```

A local path has no scheme, so `get_scheme` returns `None` and Beam
falls back to the local filesystem. A `gs://` path returns `gs`.

### What the GCS connector actually is

This is where most tutorials mislead you, so it is worth being precise.

**Beam's GCS connector is `google-cloud-storage`, not `gcsfs`.**

Beam's `apache_beam.io.gcp.gcsio` module implements a `GcsIO` class
that wraps the `google-cloud-storage` Python client. The
`GCSFileSystem` class in `apache_beam.io.gcp.gcsfilesystem` implements
Beam's `FileSystem` interface on top of it.

You will see `gcsfs` mentioned constantly in the Beam ecosystem —
`apache_beam.io.filesystems` in older versions had a `gcsfs` path, and
`gcsfs` is the standard way to treat GCS as a POSIX filesystem in
pandas, Dask, and Spark. But **Beam's own GCS I/O does not use it**,
and apache-beam 2.77 does not declare `gcsfs` as a dependency at all.

Check for yourself:

```bash
pip show apache-beam | grep -i requires
.venv/bin/python -c "import gcsfs" 2>&1 | tail -1
```

```text
.venv/bin/python -c "import gcsfs" 2>&1 | tail -1
ModuleNotFoundError: No module named 'gcsfs'
```

> **If you are following a tutorial that tells you to `pip install
> gcsfs` to make Beam work with GCS, that tutorial is out of date.** The
> package you need is `google-cloud-storage`, which arrives with
> `apache-beam[gcp]` — and the course's `project/requirements.txt`
> already installs it.

The practical point is about the *extras*:

| Extra | Brings | Needed for |
|---|---|---|
| `apache-beam[gcp]` | `google-cloud-storage`, `google-cloud-bigquery`, `google-cloud-pubsub`, `google-cloud-dataflow`, `grpcio`, and more | `gs://` paths, BigQuery, Pub/Sub, `DataflowRunner` |

The course installs `apache-beam[gcp]>=2.53.0` already, so the GCS
connector is present in your environment. This is convenient, but it is
worth knowing *which* dependency is doing the work, because a slim
production image that installs only `apache-beam` will fail on a `gs://`
path with a confusing error.

### Why a local runner still needs the GCS connector

This surprises people, and the reason is architectural.

**The runner and the filesystem are independent.** The runner decides
*where the computation happens*. The filesystem decides *where the bytes
go*. A local runner running a pipeline with a `gs://` output path will
happily compute on your laptop and then upload the results to
Cloud Storage from your laptop.

```text
   your laptop                          Cloud Storage
  ┌───────────────┐                    ┌───────────────┐
  │ Direct Runner │─── upload bytes ─▶│  gs://bucket  │
  │  (compute)   │                    │  (storage)    │
  └───────────────┘                    └───────────────┘
```

The GCS client library is imported and used by the **sink**, running in
your local process, using **your** credentials. The runner has nothing
to do with it.

This has two consequences:

**First**, writing to `gs://` from a local runner requires valid
credentials *in your shell*. This is the failure you will hit if you
try the `gs://` path without authenticating:

```text
google.auth.exceptions.DefaultCredentialsError: Your default credentials were not found. To set up Application Default Credentials, see https://cloud.google.com/docs/authentication/external/set-up-adc for more information.
```

**Second**, the connector must be *installed* even for the local runner.
If you `pip install apache-beam` without the `gcp` extra and then write
to a `gs://` path, you get an import error at pipeline-construction
time, not a helpful message about extras:

```text
ModuleNotFoundError: No module named 'google.cloud.storage'
```

> **The rule.** The **runner** determines *compute*. The **extras**
> determine *connectors*. `gs://` needs `apache-beam[gcp]`;
> `DataflowRunner` needs `apache-beam[gcp]`; `BigQuery` needs
> `apache-beam[gcp]`. They are the same requirement for different
> reasons, which is why one extra covers them all.

### Staging and temp: the two locations you cannot skip

Dataflow needs two GCS locations, and they do different things.

| Location | What it holds | Lifetime | Who uses it |
|---|---|---|---|
| **Staging** | The worker code — your pipeline, its dependencies, the environment the workers run in. | Until the job ends, then cleaned up. | The Dataflow service agent, at job submission. |
| **Temp** | **Shuffle state.** Every `GroupByKey`, every `CombinePerKey` that needs to combine across bundles, every intermediate result between stages. | Until the job ends, then cleaned up. | The workers, during execution. |

Both are **required** by `DataflowRunner`. Omit them and the job fails
at submission with a validation error, not at runtime.

**The temp location is the one that surprises people**, because it is
where the *data* goes, and it can be much larger than your input and
output combined. A pipeline that reads 1 GB and writes 10 MB can
shuffle 50 GB through the temp location, depending on the number of
stages and the skew.

**They must be in the same region as the job**, and ideally the same
region as the bucket. Chapter 4.1 covers why: a mismatch means every
shuffle byte crosses a region boundary, twice, and you pay egress for
it.

**The staging and temp locations must not collide between concurrent
jobs.** This is the default behaviour and it is a genuine footgun:
Dataflow's default temp location is a shared path, and two jobs
running at once in the same region can corrupt each other's shuffle
state. The course's `apply_dataflow_defaults` fixes this by deriving
both from a bucket-specific prefix:

```python
def apply_dataflow_defaults(options, *, bucket=None):
    if not bucket:
        return options
    base = bucket.rstrip("/")
    if not getattr(options, "staging_location", None):
        options.staging_location = f"{base}/dataflow/staging"
    if not getattr(options, "temp_location", None):
        options.temp_location = f"{base}/dataflow/temp"
    return options
```

**Note that the local runner does not need either.** The
`BundleBasedDirectRunner` does not stage anything and does not use a
remote temp location — its shuffle happens in memory, in your process.
You can see this in the course's `batch_pipeline.py`, which only
requires them when the runner is not local:

```python
runner = resolve_runner(options)
if not is_local(runner):
    bucket = options.staging_location or options.temp_location
    if bucket:
        apply_dataflow_defaults(options, bucket=bucket)
    if not options.project:
        log.error("--project is required for the %s", runner)
        return 2
    if not options.staging_location or not options.temp_location:
        log.error("--staging_location and --temp_location are required for the %s", runner)
        return 2
```

### Reading back what you wrote

Reading is the same abstraction. `ReadFromText` takes a path and works
out the backend the same way.

But there is one GCS-specific detail that catches people: **GCS object
names are not file paths.**

In a local filesystem, a path has a hierarchy. A directory contains
files. In GCS, there are no directories — only a flat namespace of
objects whose names may contain `/` characters. The console renders
those as a folder hierarchy, but the API is flat.

This matters for three things:

**Prefixes, not directories.** `gs://bucket/output` does not create a
directory. It creates a namespace under which objects with names
starting `output/` live. `gcloud storage ls gs://bucket/` shows the
prefix as if it were a directory, and `gcloud storage ls
gs://bucket/output/` shows the objects under it.

**`ReadFromText` on a prefix.** `ReadFromText("gs://bucket/output")`
does *not* read the objects under that prefix. It treats the string as
a path and fails. You need a wildcard:

```python
beam.io.ReadFromText("gs://bucket/output/*")
```

Or, more robustly, use the pattern form that GCS natively supports:

```python
beam.io.ReadFromText("gs://bucket/output-*.csv")
```

**`WriteToText` writes a prefix, not a file.** `WriteToText("gs://b/out")`
does not create `gs://b/out`. It creates `gs://b/out-00000-of-00001`,
`gs://b/out-00001-of-00003`, and so on. The prefix is a *base name*,
and the runner appends the shard suffix.

### The "write many small files" trap

This is the single most common GCS anti-pattern, and it is a
performance and cost problem before it is a correctness problem.

**The trap.** A pipeline that writes one file per element, or one file
per key, or one file per window, produces a huge number of tiny
objects. Then something downstream tries to read them all.

**Why it hurts.** GCS operations are priced and latency-bound per
object, not per byte:

| Operation | Class | Typical cost |
|---|---|---|
| List objects (1,000 per call) | A | ~$0.005 per 1,000 |
| Read an object | B | ~$0.0004 per 10,000 |
| Write an object | B | ~$0.005 per 1,000 |
| **Delete an object** | B | ~$0.005 per 1,000 |

Deleting is a *class B* operation, not free. A pipeline that writes
100,000 small objects and is later cleaned up costs real money on the
deletion alone.

Worse, **listing** is the operation that hurts. A downstream job that
does `ReadFromText("gs://bucket/output/*")` must first *list* the
prefix. Listing is paginated at 1,000 objects per request, and the
listing call has a minimum cost of one unit. For 1 million objects,
that is 1,000 list requests before a single byte is read.

**The fix: shard deliberately.** `WriteToText` has a `num_shards`
parameter for exactly this reason. Choose a shard count that gives you
files of a reasonable size — a few hundred MB to a few GB each, not
kilobytes.

```python
beam.io.WriteToText(
    "gs://my-bucket/output",
    num_shards=64,                        # explicit — the file count
    shard_name_template="-SSSSS-of-NNNNN", # the default — the file names
    file_name_suffix=".csv",
)
```

**Two parameters, two jobs.** `num_shards` decides how *many* files
there are. `shard_name_template` decides what they are *called*. They
are independent, and confusing them is a common mistake: setting
`num_shards=500` with `shard_name_template=""` does **not** give you
500 files — it gives you one, because all 500 shards are renamed to the
same empty-suffix name and the last one wins. The hands-on
demonstrates this.

The course's batch pipeline uses `num_shards=1` and an empty
`shard_name_template`, which is a deliberate choice for a small
deterministic output:

```python
rows | "FormatCsv" >> beam.Map(format_summary_csv) | "WriteSummaryCsv" >> WriteToText(
    output_path,
    header="region,order_count,revenue_eur",
    num_shards=1,
    shard_name_template="",
)
```

That produces a single, stable, human-readable file — which is what
you want for a four-row summary, and emphatically not what you want
for a million-row output.

### The shard-explosion problem

**Shard explosion** is what happens when the number of output files
becomes a function of something that grows without bound — usually
time.

The classic case is a streaming pipeline that writes each window to its
own file. With a one-minute window and a job that runs for a year, you
get 525,600 objects. At $0.005 per 1,000 deletes, cleaning that up
costs real money, and the listing cost to read it back is worse.

The general shape of the problem:

```text
   output files
       ▲
       │          ╱‾‾‾‾‾‾‾‾‾  ← one file per window / per key / per element
       │        ╱
       │      ╱
       │    ╱
       │  ╱
       └──────────────────▶ time (or input size, or key cardinality)
```

**The solutions, in order of preference:**

**1. Never shard by time. Shard by size.** Use a fixed `num_shards`
and let the runner distribute elements across them. The file count is
then constant, regardless of how long the job runs.

**2. Write to a rolling window, not a windowed file.** If you need
time-partitioned output, use a sink that supports it natively —
BigQuery's partitioning, or a table format like Parquet with
Hive-style directory partitioning. One file per partition per
*batch*, not one per window.

**3. Compact periodically.** A daily compaction job that reads the
hourly files and writes one merged file, then deletes the originals.
This is the pattern Hive, Delta Lake, and Iceberg all use.

**4. If you must write many files, use lifecycle rules.** GCS lifecycle
rules delete objects on an age schedule without counting each
deletion as a billed API call — the rule itself is free, and the
background deletion does not incur class B operation charges. This is
the correct tool for the "I need one file per window, and I need them
gone in 30 days" problem.

> **The `max_bytes_per_shard` parameter.** Newer Beam versions let the
> runner roll shards based on size rather than on a fixed count:
>
> ```text
> beam.io.WriteToText(
>     "gs://my-bucket/output",
>     num_shards=1,
>     max_bytes_per_shard=512 * 1024 * 1024,   # roll at 512 MB
> )
> ```
>
> This is the right answer for a streaming job that must not accumulate
> unbounded files. The runner starts a new shard when the current one
> exceeds the limit, and `num_shards` becomes a *minimum* rather than a
> fixed count.

### Inspecting GCS from the command line

`gsutil` is the older tool; `gcloud storage` is the newer one, and
both work. The `gcloud` form is preferred for new material because it
is faster and integrates with the rest of the CLI.

```bash
# List the top level of a bucket
gcloud storage ls gs://YOUR_BUCKET

# List the contents of a prefix
gcloud storage ls gs://YOUR_BUCKET/output/

# Human-readable sizes
gcloud storage ls -l gs://YOUR_BUCKET/output/

# Count the objects
gcloud storage ls gs://YOUR_BUCKET/output/ | wc -l

# Total size
gcloud storage du gs://YOUR_BUCKET

# Show a single object's metadata
gcloud storage objects describe gs://YOUR_BUCKET/output/output-00000-of-00001

# Copy down a single file
gcloud storage cp gs://YOUR_BUCKET/output/output-00000-of-00001 ./local_copy.csv

# Copy a whole prefix down
gcloud storage cp -r gs://YOUR_BUCKET/output/ ./downloaded/

# Stream an object to stdout
gcloud storage cat gs://YOUR_BUCKET/output/output-00000-of-00001 | head -5
```

The equivalent `gsutil` commands, for when you have an older toolchain:

```bash
gsutil ls gs://YOUR_BUCKET
gsutil ls -l gs://YOUR_BUCKET/output/
gsutil du -sh gs://YOUR_BUCKET
gsutil cp gs://YOUR_BUCKET/output/output-00000-of-00001 ./local_copy.csv
gsutil cat gs://YOUR_BUCKET/output/output-00000-of-00001 | head -5
```

One thing to be careful about: `gcloud storage ls` on a prefix with
millions of objects is slow, because it pages through the whole
namespace. Use `--page-size` and the pagination flags if you are
working at scale, and never put an unbounded `ls` in a loop.

### Lifecycle rules and cleanup

A lifecycle rule tells GCS to delete objects on a schedule. It costs
nothing to define, and the automated deletion it performs **does not
incur per-object API charges** — which makes it dramatically cheaper
than deleting objects yourself with a script.

```bash
# Delete objects under a prefix after 30 days
gcloud storage buckets update gs://YOUR_BUCKET \
    --lifecycle=delete-after-30-days.txt
```

The lifecycle file format:

```yaml
# delete-after-30-days.txt
- action:
    type: Delete
  condition:
    age: 30
    matchesPrefix:
      - output/
```

The `matchesPrefix` is what makes this useful: you delete the
*output* prefix but keep the *input* prefix forever, and you never
have to remember which is which.

Two rules that are worth having on any Dataflow bucket:

1. **Delete the temp prefix aggressively** — after 7 days, say. The
   shuffle state has no value a week later.
2. **Delete the staging prefix** — Dataflow usually cleans it up, but a
   failed job may leave artefacts behind.

```yaml
- action:
    type: Delete
  condition:
    age: 7
    matchesPrefix:
      - dataflow/temp/
- action:
    type: Delete
  condition:
    age: 1
    matchesPrefix:
      - dataflow/staging/
```

Cleanup, when you need to be surgical:

```bash
# Delete one object
gcloud storage rm gs://YOUR_BUCKET/output/output-00000-of-00001

# Delete a whole prefix
gcloud storage rm -r gs://YOUR_BUCKET/output/

# Delete everything in the bucket
gcloud storage rm -r gs://YOUR_BUCKET/**
```

> **`gcloud storage rm -r` is not transactional and does not prompt by
> default in a script.** Double-check the path. A typo in the prefix
> deletes the wrong data, and there is no undo.

---

## 🛠️ Hands-On

The hands-on has two halves. The first works entirely on your machine
and teaches the filesystem abstraction. The second is gated on a real
bucket.

### Part 1 — The path is the only thing that changes

Start with a local write, then rewrite the *same pipeline* to write to
a `gs://` prefix. First, the local version:

```python
import apache_beam as beam
from apache_beam.io.textio import ReadFromText, WriteToText

INPUT = "./sample_data/orders.csv"
LOCAL_OUTPUT = "./out/gcs_demo/local"

with beam.Pipeline() as p:
    (
        p
        | "ReadOrders" >> ReadFromText(INPUT, skip_header_lines=1)
        | "ParseOrders" >> beam.Map(lambda line: line.split(","))
        | "KeyByRegion" >> beam.Map(lambda row: (row[3], float(row[7])))
        | "SumRevenue" >> beam.CombinePerKey(sum)
        | "FormatRows" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]}")
        | "WriteLocal" >> WriteToText(LOCAL_OUTPUT, num_shards=1)
    )
```

Run it and look at the file that comes out:

```bash
python - <<'EOF'
import apache_beam as beam
from apache_beam.io.textio import ReadFromText, WriteToText

INPUT = "./sample_data/orders.csv"
LOCAL_OUTPUT = "./out/gcs_demo/local"

with beam.Pipeline() as p:
    (
        p
        | "ReadOrders" >> ReadFromText(INPUT, skip_header_lines=1)
        | "ParseOrders" >> beam.Map(lambda line: line.split(","))
        | "KeyByRegion" >> beam.Map(lambda row: (row[3], float(row[7])))
        | "SumRevenue" >> beam.CombinePerKey(sum)
        | "FormatRows" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]}")
        | "WriteLocal" >> WriteToText(LOCAL_OUTPUT, num_shards=1)
    )
EOF

ls -la out/gcs_demo/
cat out/gcs_demo/local*
```

```text
-rw-r--r--  1 pvishnoi  staff  77 Aug 28 14:52 out/gcs_demo/local-00000-of-00001
AMER,608044.31
EMEA,605463.2099999998
LATAM,593813.37
APAC,589517.0700000002
```

Two things to notice. The **filename** carries the default shard
suffix `-00000-of-00001`, and the **revenue values** are unrounded
floats — `605463.2099999998` is the honest result of summing binary
floating point numbers, and it is why the course's own pipeline
formats the value to two decimals before writing it.

Now the **identical** pipeline, with only the output path changed to a
`gs://` URI. The `gs://` version is guarded by an environment check,
so it only runs when you actually have a bucket:

```python
import os

import apache_beam as beam
from apache_beam.io.textio import ReadFromText, WriteToText

INPUT = "./sample_data/orders.csv"

# The ONLY difference from the local pipeline is this one string.
GCS_OUTPUT = os.environ.get(
    "DEMO_GCS_OUTPUT", "gs://YOUR_BUCKET/demo/output"
)

with beam.Pipeline() as p:
    (
        p
        | "ReadOrders" >> ReadFromText(INPUT, skip_header_lines=1)
        | "ParseOrders" >> beam.Map(lambda line: line.split(","))
        | "KeyByRegion" >> beam.Map(lambda row: (row[3], float(row[7])))
        | "SumRevenue" >> beam.CombinePerKey(sum)
        | "FormatRows" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]}")
        | "WriteGcs" >> WriteToText(GCS_OUTPUT, num_shards=1)
    )
```

Run it locally first, against a **local** output, to prove the pipeline
is correct, and then against GCS when you have one:

```bash
# Always works: the local path
python project/batch_pipeline.py \
    --input ./sample_data/orders.csv \
    --output ./out/gcs_demo/local2

# Only with a real bucket and credentials
export DEMO_GCS_OUTPUT="gs://YOUR_BUCKET/demo/output"
gcloud auth application-default login
python - <<'EOF'
import os
import apache_beam as beam
from apache_beam.io.textio import ReadFromText, WriteToText

INPUT = "./sample_data/orders.csv"
GCS_OUTPUT = os.environ["DEMO_GCS_OUTPUT"]

with beam.Pipeline() as p:
    (
        p
        | "ReadOrders" >> ReadFromText(INPUT, skip_header_lines=1)
        | "ParseOrders" >> beam.Map(lambda line: line.split(","))
        | "KeyByRegion" >> beam.Map(lambda row: (row[3], float(row[7])))
        | "SumRevenue" >> beam.CombinePerKey(sum)
        | "FormatRows" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]}")
        | "WriteGcs" >> WriteToText(GCS_OUTPUT, num_shards=1)
    )
EOF
```

**Without credentials**, the `gs://` version fails with:

```text
google.auth.exceptions.DefaultCredentialsError: Your default credentials were not found. To set up Application Default Credentials, see https://cloud.google.com/docs/authentication/external/set-up-adc for more information.
```

That error is the proof that the GCS connector is doing the work in
*your* process. A local runner does not grant you Cloud Storage
access; you need credentials of your own.

### Part 2 — Inspect the filesystem registry

```python
from apache_beam.io.filesystems import FileSystems

# Which backend handles this URI?
print("gs://bucket/path ->", FileSystems.get_scheme("gs://bucket/path"))
print("./local/path    ->", FileSystems.get_scheme("./local/path"))

# Does a local path exist?
print("exists ./sample_data/orders.csv:",
      FileSystems.exists("./sample_data/orders.csv"))
print("exists ./nope.csv:",
      FileSystems.exists("./nope.csv"))

# What files match a pattern? `match` returns a list of MatchResult,
# and each MatchResult holds a `metadata_list` of FileMetadata objects.
for result in FileSystems.match(["./out/gcs_demo/*"]):
    for metadata in result.metadata_list:
        print("  ", metadata.path, metadata.size_in_bytes, "bytes")
```

```text
gs://bucket/path -> gs
./local/path    -> None
exists ./sample_data/orders.csv: True
exists ./nope.csv: False
  ./out/gcs_demo/local-00000-of-00001 77 bytes
```

`FileSystems.match` is the Beam-native way to list files, and it works
across local and GCS paths with the same call. That is the abstraction
paying off.

### Part 3 — See the shard naming rule

The shard suffix is not arbitrary. Here is the template Beam uses:

```python
from apache_beam.io.filebasedsink import DEFAULT_SHARD_NAME_TEMPLATE

print("default template:", DEFAULT_SHARD_NAME_TEMPLATE)
```

```text
default template: -SSSSS-of-NNNNN
```

The default template is `-SSSSS-of-NNNNN`, which produces
`output-00000-of-00003`, `output-00001-of-00003`,
`output-00002-of-00003`. The `NNNNN` part is the total shard count and
the `SSSSS` part is the shard index; both are zero-padded to five
digits. The reason for the fixed width is that the files sort
lexicographically in the order they were written, which matters when
you read them back in order.

Now see what the course's deliberate choice produces:

```python
import apache_beam as beam
from apache_beam.io.textio import WriteToText

with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create(["a", "b"])
        | "WriteOneShard" >> WriteToText(
            "./out/gcs_demo/shard_demo",
            num_shards=1,
            shard_name_template="",
        )
    )
```

```bash
ls out/gcs_demo/shard_demo*
```

```text
out/gcs_demo/shard_demo
```

No suffix at all. `shard_name_template=""` gives you a clean, stable
filename — which is what you want for a small deterministic output, and
what you do **not** want for a production output that might need
multiple shards.

Now see what the course's deliberate choice produces:

```python
import apache_beam as beam
from apache_beam.io.textio import WriteToText

with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create(["a", "b"])
        | "WriteOneShard" >> WriteToText(
            "./out/gcs_demo/shard_demo",
            num_shards=1,
            shard_name_template="",
        )
    )
```

```bash
ls out/gcs_demo/shard_demo*
```

```text
out/gcs_demo/shard_demo
```

No suffix at all. `shard_name_template=""` gives you a clean, stable
filename — which is what you want for a small deterministic output, and
what you do **not** want for a production output that might need
multiple shards.

### Part 4 — Demonstrate the shard-explosion problem

**First, a correction to a natural assumption.** The shard count is
controlled by `num_shards`, *not* by `shard_name_template`. The
template only controls the *names*. If you set `num_shards=500` and
`shard_name_template=""`, you get **one** file — the runner writes 500
shards and then renames them all to the same empty-suffix name, so the
last one wins.

```python
import os
import shutil

import apache_beam as beam
from apache_beam.io.textio import WriteToText

shutil.rmtree("./out/gcs_demo", ignore_errors=True)
os.makedirs("./out/gcs_demo", exist_ok=True)

# 500 shards, but an empty template — they all collapse into one name
with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create([f"key-{i:04d}" for i in range(500)])
        | "WriteCollapsed" >> WriteToText(
            "./out/gcs_demo/collapsed",
            num_shards=500,
            shard_name_template="",
        )
    )

print("collapsed files:", len(os.listdir("./out/gcs_demo")))
```

```text
collapsed files: 1
```

Now the real shard explosion — a high `num_shards` with the **default**
template, so every shard keeps its own name:

```python
import os

import apache_beam as beam
from apache_beam.io.textio import WriteToText

with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create([f"key-{i:04d}" for i in range(500)])
        | "Explode" >> beam.FlatMap(
            lambda key: [f"{key}-part-{j}" for j in range(4)]
        )
        | "WriteMany" >> WriteToText(
            "./out/gcs_demo/many",
            num_shards=500,                # one file per element-ish
        )
    )

print("many files:", len([f for f in os.listdir("./out/gcs_demo")
                          if f.startswith("many")]))
```

```text
many files: 500
```

500 files for 2,000 elements. That is the trap in miniature. The same
pipeline on Dataflow would write 500 GCS objects, and the cost of
listing them, reading them, and deleting them later is entirely
disproportionate to the 40 KB of actual data.

The fix is a bounded shard count:

```python
import os

import apache_beam as beam
from apache_beam.io.textio import WriteToText

with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create([f"key-{i:04d}" for i in range(500)])
        | "Explode" >> beam.FlatMap(
            lambda key: [f"{key}-part-{j}" for j in range(4)]
        )
        | "WriteFew" >> WriteToText(
            "./out/gcs_demo/few",
            num_shards=8,                     # bounded
        )
    )

print("few files:", len([f for f in os.listdir("./out/gcs_demo")
                         if f.startswith("few")]))
```

```text
few files: 8
```

Eight files instead of 500, and the same 2,000 lines of output. The
file count is now a function of your configuration, not of your data.

### Part 5 — Read back what you wrote

Reading a GCS prefix back is where the "prefix is not a directory"
lesson bites. Locally you can do this:

```python
import apache_beam as beam
from apache_beam.io.textio import ReadFromText

# A local path works directly
with beam.Pipeline() as p:
    (
        p
        | "ReadBack" >> ReadFromText("./out/gcs_demo/few*")
        | "PrintLines" >> beam.Map(print)
    )
```

But for GCS, a bare prefix does **not** work. You need a wildcard:

```python
import apache_beam as beam
from apache_beam.io.textio import ReadFromText

# The wildcard is what makes this a pattern, not a path
with beam.Pipeline() as p:
    (
        p
        | "ReadBackGcs" >> ReadFromText("gs://YOUR_BUCKET/demo/output*")
        | "PrintLines" >> beam.Map(print)
    )
```

Note the `*` **after** the prefix, not a `/` before it. Both
`gs://bucket/output*` and `gs://bucket/output/*` work, but they are
different patterns: the first matches `output-00000-of-00001`; the second
matches `output/whatever`. For `WriteToText` output — which has no
slash — the first form is the correct one.

### Part 6 — Inspect a real bucket

With a bucket and credentials:

```bash
# What did we write?
gcloud storage ls -l gs://YOUR_BUCKET/demo/

# How many objects?
gcloud storage ls gs://YOUR_BUCKET/demo/output* | wc -l

# How big is the bucket?
gcloud storage du gs://YOUR_BUCKET

# One object's metadata
gcloud storage objects describe gs://YOUR_BUCKET/demo/output-00000-of-00001

# Read it back without downloading it
gcloud storage cat gs://YOUR_BUCKET/demo/output-00000-of-00001
```

```text
gs://YOUR_BUCKET/demo/output-00000-of-00001    77    2026-10-28T14:52:11Z
AMER,608044.31
EMEA,605463.2099999998
LATAM,593813.37
APAC,589517.0700000002
```

The file is 77 bytes. The same four lines the local run produced.

### Part 7 — Set up lifecycle rules

```bash
cat > lifecycle.yaml <<'YAML'
- action:
    type: Delete
  condition:
    age: 30
    matchesPrefix:
      - output/
- action:
    type: Delete
  condition:
    age: 7
    matchesPrefix:
      - dataflow/temp/
- action:
    type: Delete
  condition:
    age: 1
    matchesPrefix:
      - dataflow/staging/
YAML

gcloud storage buckets update gs://YOUR_BUCKET --lifecycle=lifecycle.yaml

# Confirm
gcloud storage buckets describe gs://YOUR_BUCKET --format="value(lifecycle)"
```

---

## 🛠️ Common Errors and Fixes

### `ModuleNotFoundError: No module named 'google.cloud.storage'`

**The actual message:**

```text
ModuleNotFoundError: No module named 'google.cloud.storage'
```

**The cause.** `apache-beam` was installed without the `gcp` extra, so
the GCS connector is not present. This happens on a slim production
image, or after a `pip install apache-beam` that overwrote a
`apache-beam[gcp]` install.

**The fix.**

```bash
pip install "apache-beam[gcp]"
```

This is the same error you get for `DataflowRunner` and for
`WriteToBigQuery` — one extra covers all three.

### `google.auth.exceptions.DefaultCredentialsError: Your default credentials were not found`

**The actual message:**

```text
google.auth.exceptions.DefaultCredentialsError: Your default credentials were not found. To set up Application Default Credentials, see https://cloud.google.com/docs/authentication/external/set-up-adc for more information.
```

**The cause.** You are writing to a `gs://` path from a local runner
with no credentials in your shell. The connector is doing the upload
from your machine, and it has nothing to authenticate with.

**The fix.**

```bash
gcloud auth application-default login
```

`gcloud auth login` is **not** enough — the Beam SDK and the Google
client libraries read *Application Default Credentials*, which is a
different file. If you prefer a key file for a local test, set
`GOOGLE_APPLICATION_CREDENTIALS`, but remember what chapter 4.2 said
about key files.

### `google.api_core.exceptions.NotFound: 404 No such object: bucket/prefix/output-00000-of-00001`

**The actual message:**

```text
google.api_core.exceptions.NotFound: 404 No such object: my-bucket/output/output-00000-of-00001
```

**The cause.** Almost always a **path shape** mistake, not a missing
file. You wrote with `WriteToText("gs://bucket/output")`, which
produces `gs://bucket/output-00000-of-00001` — no slash, because the
prefix is a base name, not a directory. You are then reading
`gs://bucket/output/output-00000-of-00001`, with a slash.

**The fix.** Match the shape exactly:

```bash
gcloud storage ls gs://YOUR_BUCKET/ | grep output
```

The listing tells you the real object names. Then read what is there:

```python
beam.io.ReadFromText("gs://YOUR_BUCKET/output*")
```

### `FileNotFoundError: [Errno 2] No such file or directory: 'gs://my-bucket/output'`

**The actual message:**

```text
FileNotFoundError: [Errno 2] No such file or directory: 'gs://my-bucket/output'
```

**The cause.** The `gs://` scheme was not dispatched to the GCS
filesystem — most often because the `gcp` extra is missing, so the
`GCSFileSystem` was never registered, and Beam treated the whole URI
as a local path.

**The fix.** Install the extra and verify the scheme is recognised:

```bash
pip install "apache-beam[gcp]"
.venv/bin/python -c "
from apache_beam.io.filesystems import FileSystems
print(FileSystems.get_scheme('gs://b/p'))
"
```

```text
gs
```

### `OSError: No such file or directory: gs://my-bucket/output` at pipeline construction

**The actual message:**

```text
OSError: No such file or directory: gs://my-bucket/output
```

**The cause.** `ReadFromText` validates its input paths at pipeline
**construction** time by default. It tried to stat `gs://my-bucket/output`
as a file, and the object does not exist — because `WriteToText`
produced `output-00000-of-00001`, not `output`.

**The fix.** Use a pattern, and turn off validation if the input is
produced by an earlier step in the same pipeline:

```python
beam.io.ReadFromText("gs://my-bucket/output*")
```

```python
beam.io.ReadFromText(path, validate=False)
```

### `RuntimeError: Dataflow job creation failed: ... staging_location is required`

**The actual message:**

```text
RuntimeError: Dataflow job creation failed: The staging_location is required for a Dataflow job.
```

**The cause.** `DataflowRunner` requires both `staging_location` and
`temp_location`, and you did not set them.

**The fix.**

```bash
python project/batch_pipeline.py \
    --runner DataflowRunner \
    --project YOUR_PROJECT_ID \
    --region us-central1 \
    --staging_location gs://YOUR_BUCKET/dataflow/staging \
    --temp_location gs://YOUR_BUCKET/dataflow/temp
```

Or set them in the environment and let `apply_dataflow_defaults` fill
them in from a bucket.

### `RuntimeError: ... The temp location is not writable`

**The actual message:**

```text
RuntimeError: Dataflow job creation failed: The temp location gs://my-bucket/dataflow/temp is not writable by the service account service-812345678901@gcp-sa-dataflow.iam.gserviceaccount.com.
```

**The cause.** The Dataflow service agent cannot write to the temp
location. Either the bucket does not exist, the service agent lacks
`roles/storage.objectAdmin`, or the role was added after the agent was
created and the policy is cached (chapter 4.2).

**The fix.**

```bash
# Does the bucket exist?
gcloud storage buckets describe gs://YOUR_BUCKET

# Does the service agent have the role?
gcloud projects get-iam-policy YOUR_PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:gcp-sa-dataflow" \
    --format="value(bindings.role)"

# If the role is present but the job still fails, invalidate the cache
gcloud projects remove-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-dataflow.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-dataflow.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"
```

### `ValueError: Invalid GCS path: 'my-bucket/output'`

**The actual message:**

```text
ValueError: Invalid GCS path: 'my-bucket/output'
```

**The cause.** A missing `gs://` prefix. A GCS path always starts with
the scheme.

**The fix.** Use the full URI: `gs://my-bucket/output`.

### `AccessDeniedException: 403 ... does not have storage.buckets.get access to the Google Cloud Storage bucket`

**The actual message:**

```text
google.api_core.exceptions.Forbidden: 403 GET https://storage.googleapis.com/storage/v1/b/my-bucket?projection=noAcl&prettyPrint=false: your-account@your-project.iam.gserviceaccount.com does not have storage.buckets.get access to the Google Cloud Storage bucket.
```

**The cause.** You are authenticated, but your identity has no access to
*that* bucket. Common reasons: the bucket is in a different project,
or your identity has object-level access but not bucket-level access.

**The fix.**

```bash
# Where does the bucket actually live?
gcloud storage buckets describe gs://YOUR_BUCKET --format="value(projectNumber)"

# Grant yourself access
gcloud storage buckets add-iam-policy-binding gs://YOUR_BUCKET \
    --member="user:you@example.com" \
    --role="roles/storage.objectAdmin"
```

---

## 💡 Production Notes

- **Shard by size, not by time.** A fixed `num_shards` gives you a
  constant file count regardless of job duration. `max_bytes_per_shard`
  gives you a size-bounded rolling output. Both are bounded; a
  windowed-file-per-window sink is not.

- **Set `num_shards` deliberately.** The default of `0` means "the
  runner decides", which on Dataflow is based on the input size and
  can produce a surprising number of files. An explicit number is a
  decision you can defend in a design review.

- **Put the lifecycle rule on the bucket on day one.** It costs nothing
  to define, the automated deletion is not billed per object, and it
  removes an entire class of "why is my storage bill $400" questions.
  Delete `dataflow/temp/` after 7 days and `dataflow/staging/` after 1.

- **Keep the bucket, the job, and the dataset in one region.** Every
  shuffle byte goes through the temp location. A mismatch means egress
  charges and a big latency penalty, and neither shows up as an error.

- **Do not `gcloud storage ls` an unbounded prefix in a loop.** Listing
  is paginated at 1,000 objects per call and each call is billed. A
  monitoring script that lists a million-object prefix every minute is
  an expensive monitoring script.

- **GCS object names are not paths.** There is no directory hierarchy
  in the API. `gcloud storage ls` renders one, and that rendering is a
  convenience, not a contract. Build your read patterns from what
  `gcloud storage ls` actually prints.

- **Prefer a table format for long-lived output.** Parquet or ORC with
  partition directories gives you columnar reads, predicate pushdown,
  and one file per partition per batch. CSV gives you human readability
  and very little else. For anything you will query repeatedly, use a
  table.

- **Remember that the connector runs in your process locally.** When
  you write to `gs://` from a laptop, the bytes travel over your
  network connection, not over Google's. A slow uplink makes a local
  "GCS write" embarrassingly slow, and it is not a Beam problem.

---

## 🔑 Key Takeaways

- **The path string is the only thing that changes.** `WriteToText`
  takes a path; the URI scheme selects the filesystem backend.
- **Beam's GCS connector is `google-cloud-storage`, not `gcsfs`.** It
  arrives with `apache-beam[gcp]`, which the course already installs.
  Tutorials that tell you to `pip install gcsfs` for Beam are out of
  date.
- **A local runner still needs the connector** when the path is
  `gs://` — the sink uploads the bytes from your process, using your
  credentials. The runner and the filesystem are independent.
- **Staging and temp are required by `DataflowRunner` and optional
  locally.** The temp location holds the shuffle state, which can be
  far larger than your input and output combined, and it must not
  collide between concurrent jobs.
- **A GCS prefix is not a directory.** `WriteToText("gs://b/out")`
  produces `gs://b/out-00000-of-00001` — no slash. To read it back, use
  the pattern `gs://b/out*`.
- **The "many small files" trap is a cost trap**, because GCS bills per
  *operation*, not per byte — and deletion is a billed operation.
  Bound your file count with `num_shards`.
- **Lifecycle rules are free to define and their deletions are not
  billed per object.** They are the right tool for expiring output and
  temp data.

---

## 📚 Practice Exercises

1. **Measure the operation cost.** Create a bucket, enable request
   logging, and run a pipeline that writes 5,000 small objects. Then
   use `gcloud storage ls` and `gcloud storage rm` and read the request
   log to count the class A and class B operations. Compare that to the
   cost of the same data written as 10 shards. Explain why the
   difference is not proportional to the bytes.

2. **Reproduce the prefix bug.** Write to `gs://YOUR_BUCKET/prefix`
   and then try to read `gs://YOUR_BUCKET/prefix` (no wildcard) with
   `ReadFromText`. Record the exact error. Then try
   `gs://YOUR_BUCKET/prefix*` and `gs://YOUR_BUCKET/prefix/*` and show
   which one matches the object `WriteToText` produced. Explain the
   difference between the two wildcards in terms of what the prefix
   actually is.

3. **Design the shard count.** For a pipeline that will write 2 TB of
   CSV, design the `num_shards` and `file_name_suffix` configuration.
   Justify the file size you targeted from three directions: the cost
   of a downstream `ReadFromText` listing, the cost of a re-run that
   rewrites one shard, and the practical limits of a human opening one
   file. Then check whether `max_bytes_per_shard` would be a better
   answer.

4. **Write the lifecycle policy.** Produce a lifecycle file for a
   Dataflow bucket that expires: the staging prefix after 1 day, the
   temp prefix after 7 days, the raw input after 90 days, and the
   curated output after 365 days. Then explain what would happen if a
   compliance requirement said the raw input must be retained for
   seven years, and how you would satisfy both.

5. **Measure the local GCS overhead.** Time the batch pipeline writing
   to a local path, then to a `gs://` path, with a valid bucket. Report
   the difference and attribute it: how much is the upload, how much is
   the listing, and how much is the extra API calls the connector
   makes? Then repeat with a single large shard versus 32 shards and
   explain why the number of objects affects the total time.

6. **Reflect.** This chapter said the connector runs in your process
   when you use a local runner. Chapter 4.2 said the Dataflow service
   agent mints the tokens for the workers. Combine the two: when you
   deploy to Dataflow, *whose* bytes leave *whose* machine, and *whose*
   credentials sign the request? The answer is different in the two
   cases, and the difference is exactly why a staging bucket needs its
   own IAM story.

---

## 📖 Further Reading

- Cloud Storage overview — https://cloud.google.com/storage/docs
- Beam's GCS I/O — https://beam.apache.org/documentation/io/io-lists/
- Cloud Storage object names and prefixes — https://cloud.google.com/storage/docs/object-names
- Cloud Storage pricing — https://cloud.google.com/storage/pricing
- Cloud Storage lifecycle management — https://cloud.google.com/storage/docs/lifecycle
- Cloud Storage request logging — https://cloud.google.com/storage/docs/req-logging
- Beam's file-based sink and sharding — https://beam.apache.org/documentation/io/file-based-sink/
- `gcloud storage` reference — https://cloud.google.com/sdk/gcloud/reference/storage
