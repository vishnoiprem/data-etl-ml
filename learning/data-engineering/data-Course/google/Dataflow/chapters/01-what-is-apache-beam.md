# 1.1 — What Is Apache Beam?

> **Section 1 · Beam Fundamentals & Model · Lecture 1.1 · 6:30**

## 🎯 What you will learn

- Why Apache Beam exists, and the problem it was born to solve
- The three abstractions that make up the Beam model: PCollection, PTransform, PRunner
- What "portability" actually means in practice — and where it stops
- The one-paragraph version you should be able to recite in an interview
- How to write your first Beam pipeline and read its output

---

## 🧠 Concept

### The problem

Every data system has a batch mode and a streaming mode, and they are
usually implemented with different code. A company might have a Spark job
that runs the nightly aggregation and a Kafka Streams application that
does the same aggregation in real time. The business logic — the rules
that decide what counts as a valid order, how revenue is converted, what
a "session" is — is written twice. The two implementations drift. The
nightly number stops matching the dashboard.

Apache Beam's thesis is that **batch and streaming are the same problem**.
A batch pipeline is a streaming pipeline whose input ends. If you express
your pipeline in the Beam model, the same code runs on a batch engine
overnight and a streaming engine continuously.

### The three abstractions

Everything in Beam is built from three ideas.

**1. PCollection — the data.**

A PCollection is a distributed collection of elements. Not a Python list
that happens to be big: a description of a dataset that may not exist
yet, may be spread across a thousand machines, and may never be
materialised in full.

Two properties matter:

- **Immutable.** A PCollection's contents never change. Every transform
  produces a *new* PCollection. This is why you can consume the same
  PCollection from five different branches without worrying about
  ordering or mutation.
- **Lazy.** Creating a PCollection does no work. The graph is built
  first, and the runner executes it when the pipeline runs.

**2. PTransform — the operation.**

A PTransform takes one or more PCollections and produces one or more
PCollections. `beam.Map`, `beam.Filter`, `beam.CombinePerKey` are all
PTransforms.

**3. PRunner — the executor.**

The runner takes the graph and executes it: `DirectRunner` in-process,
`DataflowRunner` on Google Cloud, `SparkRunner`, `FlinkRunner`.

```text
PCollection  ──[PTransform]──▶  PCollection
                                    │
                                    ▼
                              executed by a PRunner
```

The key property of this design is that **the runner can rearrange the
graph**. When you write `Map` then `Filter`, the runner may fuse them
into one step that never writes an intermediate result. That optimisation
is not available to you if you write a shell script or a hand-rolled
Spark job — it is a benefit of expressing the work in the Beam model.

### Portability, honestly

Beam's portability claim is real but bounded, and understanding the
boundary is what separates someone who has used Beam from someone who
*understands* Beam.

| Layer | Portable? | Notes |
|---|---|---|
| Core model (PCollection, Map, CombinePerKey) | yes | the portable core |
| Common I/O (text, Avro, Parquet) | yes | via the portability framework |
| Runner-specific I/O (BigQuery, Pub/Sub) | no | Dataflow-only |
| Runner-specific tuning (`--autoscaling_algorithm`) | no | Dataflow-only |
| Java SDK | closest to the metal | fastest, most complete |

The rule of thumb: **the pipeline graph is portable; the deployment
configuration is not.** If you want to run the same pipeline on Flink and
Dataflow, you can — but you will use different flags for each.

The portability framework is a specific technical mechanism: Beam
serialises the pipeline graph into a proto (the "Runner API"), and each
runner implements a "SDK harness" that translates that proto into its own
execution model. Flink, for instance, translates Beam's windowing into
Flink's native windowing. This is why Beam on Flink supports real
stateful streaming rather than an emulation.

### Why Google built on Beam

Dataflow is Google's managed Beam runner. Google needed a single API for
batch (MapReduce successor) and streaming (Dataflow Streaming) and wanted
the runner to be the differentiating part, not the SDK. Beam lets Google
own the runner while the SDK stays open — which, in turn, is why Beam
exists at all: it was extracted from Google's internal codebase so that
other runners could exist and so that the SDK would not be a Google-only
artefact.

The practical consequence for you: **the Python SDK you learn here is the
same SDK that runs on Dataflow**, and the APIs are stable. Dataflow adds
runner-specific options on top of the portable core, not instead of it.

### Batch is streaming with an end

This is the single most useful mental model in Beam.

| | Batch | Streaming |
|---|---|---|
| Input | bounded | unbounded |
| End | known | never (or until cancelled) |
| Watermark | advances to `+inf` at the end | advances as data arrives |
| Result | complete when the job succeeds | never complete |
| Termination | automatic | you cancel it |

When a batch pipeline finishes reading its input, Beam advances the
watermark to `+inf`, which closes every window. That is why a batch
pipeline produces the same windowed output as a streaming one — the
streaming one just does it incrementally.

---

## 🛠️ Hands-On: Your First Beam Pipeline

### Install

```bash
cd data-engineering/data-Course/google/Dataflow
python3 -m venv .venv
source .venv/bin/activate
pip install -r project/requirements.txt
```

Confirm the SDK imports:

```bash
python -c "import apache_beam; print(apache_beam.__version__)"
```

You should see something like `2.77.0`.

### The smallest possible pipeline

```python
import apache_beam as beam

with beam.Pipeline() as p:
    result = (
        p
        | "Create" >> beam.Create([1, 2, 3, 4, 5])
        | "Double" >> beam.Map(lambda x: x * 2)
    )

print(result)
```

Nothing printed. That is not a bug — **the graph was built, not run**.
`beam.Pipeline()` as a context manager runs the pipeline when the block
exits, but the `result` PCollection is a *description*. To see the
values, you must add a sink.

### Adding a sink

```python
import apache_beam as beam

with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create([1, 2, 3, 4, 5])
        | "Double" >> beam.Map(lambda x: x * 2)
        | "Print" >> beam.Map(print)
    )
```

`beam.Map(print)` is the simplest possible sink: it runs `print` on each
element as it passes through. The output is unordered — the runner may
process elements in any order.

### The shape of a real pipeline

Every production pipeline has the same four stages: **read → transform →
aggregate → write**. Here is the complete version, writing to a file:

```python
import apache_beam as beam

INPUT = "./sample_data/orders.csv"
OUTPUT = "./out/first_pipeline"

with beam.Pipeline() as p:
    (
        p
        | "Read" >> beam.io.ReadFromText(INPUT)
        | "Parse" >> beam.Map(lambda line: line.split(","))
        | "Valid" >> beam.Filter(lambda row: len(row) > 6 and row[6] == "complete")
        | "KeyByRegion" >> beam.Map(lambda row: (row[3], float(row[7])))
        | "SumRevenue" >> beam.CombinePerKey(sum)
        | "Format" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]:.2f}")
        | "Write" >> beam.io.WriteToText(OUTPUT)
    )
```

Read that chain carefully — it is the shape of most of this course:

| Stage | Transform | Why |
|---|---|---|
| Read | `ReadFromText` | the source |
| Parse | `Map` | string → structured row |
| Valid | `Filter` | drop what we cannot process |
| KeyByRegion | `Map` | `(key, value)` pairs |
| SumRevenue | `CombinePerKey(sum)` | the aggregation |
| Format | `Map` | back to a string for a text sink |
| Write | `WriteToText` | the sink |

### Generate the sample data first

```bash
python resources/sample_data.py --output-dir ./sample_data
```

Then run the pipeline and read the output:

```bash
python -c "
import apache_beam as beam
with beam.Pipeline() as p:
    (
        p
        | 'Read' >> beam.io.ReadFromText('./sample_data/orders.csv')
        | 'Parse' >> beam.Map(lambda line: line.split(','))
        | 'Valid' >> beam.Filter(lambda row: len(row) > 6 and row[6] == 'complete')
        | 'KeyByRegion' >> beam.Map(lambda row: (row[3], float(row[7])))
        | 'SumRevenue' >> beam.CombinePerKey(sum)
        | 'Format' >> beam.Map(lambda kv: f'{kv[0]},{kv[1]:.2f}')
        | 'Write' >> beam.io.WriteToText('./out/first_pipeline')
    )
"
ls out/first_pipeline*
cat out/first_pipeline*
```

> **Note the output filename.** `WriteToText` writes `first_pipeline00000of00001`
> — a sharded file with a suffix. This is deliberate, and it is covered
> in chapter 2.3. Never hard-code the exact output filename in a script.

### Reading the pipeline graph

Beam can describe the graph it built. This is the fastest way to
understand what you actually wrote:

```python
import apache_beam as beam

p = beam.Pipeline()
(
    p
    | "Create" >> beam.Create([1, 2, 3])
    | "Double" >> beam.Map(lambda x: x * 2)
)
print(p)
```

```text
<pipeline [
  Create[None],
  Double[None]>] at 0x...>
```

Each line is a step. The labels are the ones you gave with `>>`.

---

## 🛠️ Common Errors and Fixes

### The pipeline runs but prints nothing

You built a PCollection and never consumed it. A PCollection is a
description, not data. Add a sink:

```text
| "Print" >> beam.Map(print)
```

### `NameError: name 'beam' is not defined`

You forgot the import, or the import is inside a function that did not
run before the pipeline was built.

```python
import apache_beam as beam
```

### `AttributeError: module 'apache_beam' has no attribute 'io'`

In Beam 2.x, `beam.io` is a submodule that must be imported explicitly.
`beam.Map` works without it; `beam.io.ReadFromText` does not.

```python
import apache_beam as beam
import apache_beam.io.textio  # or just use beam.io after an explicit import
```

In practice `import apache_beam as beam` exposes `beam.io` in recent
versions, but if you hit this, the explicit import always works.

### `RuntimeError: Transform name is already used`

Two transforms in the same pipeline share a label. The error does not
say which ones.

```bash
python resources/audit_course.py
```

The course linter finds this statically, before you run anything.

### `ValueError: Key must be a hashable type`

You keyed by a dict or a list. Use a tuple:

```python
# wrong
beam.Map(lambda row: ({"region": row[3]}, row[7]))
# right
beam.Map(lambda row: (row[3], row[7]))
```

### `FileNotFoundError: ./sample_data/orders.csv`

You have not generated the sample data yet:

```bash
python resources/sample_data.py --output-dir ./sample_data
```

### `ModuleNotFoundError: No module named 'apache_beam'`

Wrong virtualenv. Check with:

```bash
which python
pip show apache-beam
```

### The output has more rows than you expected

`ReadFromText` reads **every** line, including the header. Skip it:

```text
| "SkipHeader" >> beam.Filter(lambda line: not line.startswith("order_id"))
```

---

## 💡 Production Notes

- **Never build a pipeline without a sink.** A pipeline that constructs a
  PCollection and discards it does no work and proves nothing. In
  production, every branch ends in a sink or in a `CombinePerKey` whose
  result is written.
- **Label every transform.** Unlabelled transforms get auto-generated
  names like `ParDo(Split)`, which are useless in a job graph and
  actively harmful when the same transform appears twice. A label is
  your unit of debugging.
- **Keep `DoFn` classes picklable.** They are serialised to workers.
  No open sockets, no database connections, no lambdas capturing
  unpicklable state.
- **Prefer `Map`/`Filter` over `ParDo` when you can.** `ParDo` has more
  power and more footguns (it can emit zero elements, which silently
  drops data).
- **Read the job graph before you optimise.** The Dataflow UI shows
  exactly which stage is slow. Optimising without looking is guessing.

---

## 🔑 Key Takeaways

- Beam has three abstractions: **PCollection** (data), **PTransform**
  (operation), **PRunner** (executor).
- PCollections are **immutable** and **lazy**. Nothing runs until a sink
  consumes them.
- **Batch is streaming whose input ends.** When a batch job finishes,
  the watermark advances to `+inf` and every window closes.
- Portability is real at the **graph** level and bounded at the
  **configuration** level. Runner-specific I/O and flags are not
  portable.
- The runner may **fuse and reorder** your steps. That is a feature —
  and the reason to express work in the model rather than scripting it.
- Every production pipeline is **read → transform → aggregate → write**.

---

## 📚 Practice Exercises

1. **Add a stage.** Extend the hands-on pipeline to also count the orders
   per region, alongside the revenue. Write both to the output file as
   `region,count,revenue`.

2. **Two sinks, one source.** Write a pipeline that reads
   `orders.csv` once and writes *two* different outputs — one per
   region, to two different prefixes. Confirm that the source is read
   only once by checking the job graph.

3. **Prove immutability.** Build a PCollection, apply two different
   `Map`s to it, and show that both branches produce the expected
   results. Explain why this is safe.

4. **Read the graph.** Build a pipeline with five stages and print the
   pipeline object. Identify which stages the runner would fuse.

5. **Batch vs streaming.** Write the same "count by region" pipeline
   twice — once reading a file, once reading from a Pub/Sub topic.
   Identify every line that differs between them.

6. **Reflection.** Explain the phrase "the runner can rearrange the graph"
   to a colleague who has only written Spark jobs. What capability does
   that give you that Spark's DataFrame API does not?

---

## 📖 Further Reading

- Apache Beam documentation — https://beam.apache.org/documentation/
- Beam SDKs — https://beam.apache.org/documentation/sdks/python/
- Beam's "A Beam Primer" (the official model overview) — https://beam.apache.org/documentation/basic-topics/
- Google Cloud Dataflow overview — https://cloud.google.com/dataflow/docs/about-dataflow
- Apache Beam: The Top 10 Challenges for Big Data (the paper that
  motivated the project) — https://research.google/pubs/pub43018/
