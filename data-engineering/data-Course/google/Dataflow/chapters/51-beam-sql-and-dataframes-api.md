# 8.8 — Beam SQL & Dataframes API

> **Section 8 · Production Operations · Lecture 8.8 · 6:30**

## 🎯 What you will learn

- What the Beam SQL / DataFrames surface actually is, and why `beam.dataframe` is an optional extra
- The `Schema` and `Row` model, and why Beam has its own type system
- What the DataFrames API is genuinely good at — and where it is not
- The performance truth: fusion in the DataFrames API versus the core SDK
- A side-by-side of the same pipeline in the core SDK and in the DataFrames API
- How Beam SQL relates to BigQuery SQL, and when BigQuery SQL is strictly better
- When the DataFrames API *is* the right choice, and the honest verdict

---

## 🧠 Concept

### What "Beam SQL" actually is

First, a clarification that removes most of the confusion. **Beam has
two different things that people call "Beam SQL".**

**1. The DataFrames API** (`apache_beam.dataframe`) — a Python library
that gives you a pandas-like, schema-aware, relational API on top of
Beam. It is the thing most people mean. It is an *optional extra*:

```bash
pip install apache-beam[dataframe]
```

**2. Beam Calcite** (the `beam-sdks-java-experimental` SQL
transform) — a Java-only, experimental SQL frontend that never left
incubation. It is not something you will use, and it is not what this
chapter is about.

So: this chapter is about the **Python DataFrames API**, which ships in
the `dataframe` extra. In the course virtualenv that extra is **not**
installed, which is itself informative: the DataFrames API is a
readability aid, not the core of what Beam is, and the course's project
does not depend on it.

That last point deserves emphasis, because it is the practical answer to
"should I use it?": the core SDK is what production pipelines are
built from, the core SDK is what the course teaches, and the DataFrames
API is a layer on top that you can reach for when a transformation is
genuinely relational.

### The `Schema` and `Row` model

Beam's DataFrames API needs a schema, because it is a *relational* API —
"select these columns", "join on this key", "group by this". That means
Beam needs its own type system rather than relying on Python's.

The two objects at the centre:

- **`Schema`** — an ordered list of columns, each with a name, a type,
  and a nullable flag. It is the contract of a DataFrame.
- **`Row`** — a tuple-like, immutable record that conforms to a
  `Schema`. It is what a `select` or an `aggregate` produces.

The type system is Beam's own, and it is *not* pandas' or SQL's:

| Beam type | Notes |
|---|---|
| `INT64` | 64-bit signed integer |
| `FLOAT64` | double precision |
| `BOOL` | boolean |
| `STRING` | UTF-8 string |
| `BYTES` | opaque byte string |
| `ARRAY` | a list of another type |
| `STRUCT` | a nested record |
| `DATETIME` | a timestamp |

Two things follow from this that matter in practice:

**1. There is no null type.** A column is nullable or it is not. That is
a stronger guarantee than SQL's, and it means the schema is a real
contract you can validate against.

**2. `FLOAT64` is a double, and doubles do not sum the way money sums.**
This is the same issue as the rounding question in chapter 8.7, but
sharper here: the DataFrames API will not give you a decimal type, so
money arithmetic in a DataFrame is floating-point arithmetic. If you are
summing revenue, you want the core SDK with `Decimal`, or you accept
the float and round at the boundary.

### The DataFrames API surface

The API lives under `beam.dataframe.transforms`, and it is organised
around a small number of methods on a DataFrame object:

| Method | What it does |
|---|---|
| `Schema` | declares a schema for a source or an output |
| `select` | projects columns, and can compute new ones |
| `filter` | row-level predicate |
| `group_by` | groups by one or more columns |
| `aggregate` | reduces each group to a row |
| `join` | equi-join against another DataFrame |
| `assign` | adds or replaces a column |
| `drop` | removes columns |
| `sort_values` | orders rows (note: expensive) |
| `to_pcollection` | converts a DataFrame back into a Beam PCollection |

The shape of a DataFrames pipeline looks like this — in outline, since
the module is an optional extra:

```text
beam.dataframe.transforms
  ├─ Schema         — the column contract
  ├─ select         — projection
  ├─ filter         — predicate
  ├─ group_by       — grouping
  ├─ aggregate      — reduction
  ├─ join           — relational join
  └─ to_pcollection  — back to the Beam model
```

And the pipeline itself is assembled from a `beam.Pipeline` and a
`beam.dataframe.DataFrame`:

```text
  schema  →  DataFrame  →  select / filter / group_by / aggregate  →  PCollection
```

### What the DataFrames API is good at

**1. Readability for SQL-fluent teams.** A `group_by`/`aggregate` chain
reads like the SQL it replaces. For a team of analysts and data
engineers who think in relations, this is a genuine reduction in
cognitive load, and it shortens the review cycle.

**2. Schema-aware operations.** In the core SDK, a `Map` that renames a
column is a string operation with no type checking; a typo produces a
`KeyError` on a worker at 3am. In the DataFrames API, the schema is
checked at graph-construction time, and a rename that breaks a
downstream select fails immediately, in the submitter's process.

**3. Relational joins without hand-rolled grouping.** A `join` against a
lookup DataFrame is one call, rather than the `CoGroupByKey` +
`FlatMap` + filter dance that the core SDK requires.

**4. A clearer expression of intent.** `df.groupby("region").agg(...)`
communicates "this is a relational aggregation" in a way that
`beam.CombinePerKey` with a hand-written `CombineFn` does not. That
matters in code review.

### What the DataFrames API is bad at

**1. Performance — it does not always fuse as aggressively as the core
SDK.** This is the most important point and the one the documentation
is quiet about.

In the core SDK, the runner fuses compatible steps: a `Map` followed by
a `Filter` followed by a `Map` becomes **one** stage, with no
intermediate materialisation and no network traffic. This fusion is one
of the main reasons the core SDK is fast.

In the DataFrames API, the library builds a Beam graph *underneath*, and
that graph's fusion behaviour depends on how the library emits it. The
DataFrames API optimises some operations — particularly scans, filters
and column projections — but it does **not** guarantee the same
step-level fusion the core SDK gets for free. The practical consequence:
a DataFrames pipeline can be *slower* than the equivalent core SDK
pipeline, sometimes by a meaningful margin, and the difference is not
always visible in the job graph without looking.

The honest summary: **the DataFrames API is a readability layer, not a
performance win.** If you rewrite a core SDK pipeline in the DataFrames
API and expect it to be faster, you will be disappointed.

**2. Limited transform coverage.** Not every core SDK transform has a
DataFrames equivalent, and not every Beam feature is available in a
DataFrame context. Specifically:

- **Custom `DoFn`s** — the DataFrames API has no general "apply this
  arbitrary Beam transform" escape hatch. You can use a
  `beam.dataframe` UDF, but it is not the same thing as a `DoFn`, and
  it does not get `PaneInfo`, state, or timers.
- **Windowing and state** — the DataFrames API is fundamentally a
  *batch* relational model. There is no first-class equivalent of
  `beam.WindowInto`, `beam.GroupByKey` with state, or a streaming
  `DoFn` with timers. For a streaming pipeline, the core SDK is not
  optional.
- **Side inputs and other PCollection-valued inputs** — awkward or
  unsupported.
- **Some sinks and sources** — the DataFrames API's IO story is thinner
  than the core SDK's.

**3. A smaller community.** Very few public Beam codebases use the
DataFrames API. That means: fewer Stack Overflow answers, fewer blog
posts, fewer people to ask, and less institutional knowledge. In a
production setting, the bus factor of a DataFrames-based pipeline is
measurably lower.

**4. The execution model is different, and the difference is not
cosmetic.** In the core SDK, your pipeline is a **graph of
PTransforms**, and the runner executes that graph — with fusion, with
shuffles where the graph says so, with stage-level autoscaling. In the
DataFrames API, your pipeline is a **DataFrame**, and the library
*translates* it into a Beam graph for you.

That translation is where the trouble lives. The DataFrame you wrote is
not the graph that runs. This means:

- You cannot read the DataFrame and know exactly what will run. You have
  to look at the generated graph.
- Beam features that live *outside* the relational model — custom
  `DoFn`s, side inputs, streaming windowing — either do not compose
  with the DataFrame, or they force you back to the core SDK.
- Debugging is harder, because the thing you wrote is not the thing that
  failed.

This is not an argument that the DataFrames API is bad. It is an
argument that it is a **different programming model** with a different
trade-off profile, and you should choose it deliberately.

### The core SDK versus the DataFrames API, side by side

The same pipeline — count orders and sum revenue per region — in both
models.

**Core SDK:**

```python
import apache_beam as beam


def parse_line(line):
    """Split one CSV line into a field dict, skipping the header."""
    values = line.split(",")
    if values[0] == "order_id":
        return None
    return {
        "region": values[3],
        "status": values[6],
        "amount": float(values[7]),
    }


def parse_line_or_none(line):
    """Map wrapper that drops the header row."""
    row = parse_line(line)
    return [row] if row is not None else []


with beam.Pipeline() as p:
    (
        p
        | "ReadOrders" >> beam.io.ReadFromText("./sample_data/orders.csv")
        | "Parse" >> beam.FlatMap(parse_line_or_none)
        | "KeepComplete" >> beam.Filter(lambda r: r["status"] == "complete")
        | "KeyByRegion" >> beam.Map(lambda r: (r["region"], r["amount"]))
        | "RevenueByRegion" >> beam.CombinePerKey(sum)
    )
```

**DataFrames API** (requires the `dataframe` extra — the shape is
illustrative, not runnable in the course virtualenv):

```text
  schema  =  Schema(...)                      # region: STRING, amount: FLOAT64, status: STRING
  orders  =  p | "ReadOrders"  >>  read_csv(schema)
  valid   =  orders.filter(valid_orders)       # predicate
  totals  =  valid.groupby("region").agg(...)  # relational aggregation
  rows    =  totals.to_pcollection()           # back to the Beam model
```

Reading the two side by side:

| Dimension | Core SDK | DataFrames API |
|---|---|---|
| Expressiveness | Total — anything the SDK can do | Relational subset |
| Fusion | Guaranteed, runner-level | Good but not identical |
| Custom `DoFn` | Yes | No general escape hatch |
| Streaming windowing | Yes | No |
| Side inputs | Yes | Awkward |
| Type checking | At runtime, per element | At graph-construction time, per schema |
| Readability | Lower | Higher |
| Community | Large | Small |
| Schema source | Implicit, from coders | Explicit, a first-class object |
| Failure mode | Runtime, on a worker | Construction time, or runtime |

The right way to read this table: **the DataFrames API buys you type
safety and readability, and charges you in flexibility and in the
guarantees you lose about the generated graph.** Whether that is a good
trade depends entirely on whether your transformation is relational.

### How this relates to BigQuery SQL

This is the comparison that actually matters in production, and it is
not close.

| | Beam DataFrames API | BigQuery SQL |
|---|---|---|
| Runs on | Dataflow workers (autoscaling, per your config) | BigQuery's own distributed engine |
| Reads from | Anything Beam can read | BigQuery tables, external tables, and (via Data Catalog) some external sources |
| Writes to | Anything Beam can write | BigQuery tables |
| Schema | You declare it | Inferred, or declared |
| Cost | vCPU-hours on Dataflow + storage | BigQuery query bytes (roughly $0.01 per TB scanned) |
| Elapsed time for a small query | 30–90 seconds (worker startup dominates) | 2–15 seconds |
| Elapsed time for a large query | Scales with the data and your worker count | Scales with the data, on BigQuery's fleet |
| UDFs | Python `DoFn`s, full expressiveness | SQL UDFs and JavaScript UDFs |
| Streaming | Yes, via Pub/Sub | Yes, via Storage Write API |
| Portable off GCP | Yes | No |

**If your data is already in BigQuery, BigQuery SQL is strictly better
for most workloads.** It is faster to write, faster to run, cheaper on
small queries, and it needs no pipeline job at all. The Dataflow
streaming engine exists for the case where BigQuery's ingestion latency
does not meet the requirement — and that is a real and common case, but
it is a case, not a default.

The Beam DataFrames API's real niche is **the awkward middle**: data
that is *not* in BigQuery but that you want to process relationally
before it goes somewhere else. Files on GCS, Kafka topics, a SaaS API
polled into a PCollection, an on-premises database via JDBC. There,
a DataFrame-shaped transformation with a schema is a good fit, because
you are doing the relational work on data that BigQuery cannot see
without first ingesting it.

### When the DataFrames API *is* the right choice

Concretely:

1. **A team that thinks in SQL.** Six engineers who all write SQL will
   review a DataFrames pipeline faster than a `CombineFn`. The
   cognitive saving is real, and in a large team it compounds.
2. **A transformation that is genuinely relational.** A multi-table join
   with a projection, an aggregation and a filter is exactly what the
   DataFrames API is for. A pipeline that is 90% `DoFn` logic is not.
3. **A schema you want enforced.** If a column rename would silently
   corrupt a downstream report, the schema check at construction time is
   worth a great deal.
4. **A batch pipeline with no streaming requirements.** The DataFrames
   API's batch orientation is not a limitation when you only need batch.

And when it is the wrong choice:

1. **The logic is not relational.** If you need a custom `DoFn`, a
   stateful transform, or a windowing rule, use the core SDK.
2. **It is streaming.** The DataFrames API has no first-class streaming
   story. Use the core SDK.
3. **You need a guaranteed performance characteristic.** The DataFrames
   API does not promise the same fusion as the core SDK.
4. **Nobody on the team knows it.** The community is small enough that
   the bus factor matters.

### The honest verdict

For a course graduate and for most production work: **the core SDK is
the right default.** It is more expressive, it is better documented,
it has a larger community, and it has stronger performance guarantees.
Learn it properly.

The DataFrames API is a **readability aid, not a performance win**. It
is worth using when the transformation is relational *and* the team
would benefit from SQL-shaped code. It is worth learning so that you
can read it when you encounter it, and so that you have the option.

---

## 🛠️ Hands-On: Comparing the Models

### Step 1 — Confirm the extra is not installed

This is a useful thing to check, because it tells you what the course
project depends on:

```bash
cd data-engineering/data-Course/google/Dataflow
source .venv/bin/activate
python -c "
import apache_beam as beam
print('apache-beam version :', beam.__version__)
print('has dataframe attr  :', hasattr(beam, 'dataframe'))
print('has combiners attr :', hasattr(beam, 'combiners'))
"
```

Expected:

```text
apache-beam version : 2.77.0
has dataframe attr  : False
has combiners attr  : True
```

`hasattr(beam, "dataframe")` is `False` because the `dataframe` extra
is not installed. This is why every DataFrames API snippet in this
chapter is in a `text` fence — a `python` fence would reference
`beam.dataframe`, which does not exist in this environment.

### Step 2 — Install the extra in a throwaway environment (optional)

Do **not** do this in the course virtualenv — it pulls in pandas, pyarrow
and a large dependency tree, and it can change the behaviour of the
core SDK in ways the course tests do not expect. Use a separate venv:

```bash
cd /tmp
python3 -m venv dfenv
source dfenv/bin/activate
pip install "apache-beam[dataframe]==2.77.0"
python -c "
import apache_beam as beam
print('has dataframe attr:', hasattr(beam, 'dataframe'))
"
```

### Step 3 — Inspect the real API surface

With the extra installed, the API is discoverable:

```bash
source /tmp/dfenv/bin/activate
python -c "
import beam.dataframe.transforms as t
names = [n for n in dir(t) if not n.startswith('_')]
print(sorted(names))
"
```

The names you should see include `Schema`, `select`, `filter`,
`group_by`, `aggregate`, `join`, `assign`, `drop`, `sort_values`,
`to_pcollection`, `to_dataframe`, `concat`, `read_csv`, `read_json`,
`write_csv` and `write_parquet`.

And the `Schema` constructor:

```bash
source /tmp/dfenv/bin/activate
python -c "
import beam.dataframe.transforms as t
import inspect
print(inspect.signature(t.Schema.__init__))
"
```

### Step 4 — The core SDK version, in full, and runnable

This is the version the course project actually ships, and it is the
one to master:

```python
import apache_beam as beam


def parse_line(line):
    """Split one CSV line into a field dict, skipping the header."""
    values = line.split(",")
    if values[0] == "order_id":
        return None
    return {
        "region": values[3],
        "status": values[6],
        "amount": float(values[7]),
    }


def parse_line_or_none(line):
    """Map wrapper that drops the header row."""
    row = parse_line(line)
    return [row] if row is not None else []


def build_summary_pipeline(
    pipeline: beam.Pipeline,
    *,
    input_path: str,
    output_path: str,
) -> None:
    """Count orders and sum revenue per region using the core SDK.

    Args:
        pipeline: The pipeline to add transforms to.
        input_path: The input CSV path.
        output_path: The output path prefix.
    """
    summary = (
        pipeline
        | "ReadOrders" >> beam.io.ReadFromText(input_path)
        | "Parse" >> beam.FlatMap(parse_line_or_none)
        | "KeepComplete" >> beam.Filter(lambda row: row["status"] == "complete")
        | "KeyByRegion" >> beam.Map(lambda row: (row["region"], row["amount"]))
        | "RevenueByRegion" >> beam.CombinePerKey(sum)
        | "Format" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]:.2f}")
    )

    summary | "WriteSummary" >> beam.io.WriteToText(output_path)


with beam.Pipeline() as p:
    build_summary_pipeline(
        p,
        input_path="./sample_data/orders.csv",
        output_path="./out/core_sdk",
    )
```

Run it:

```bash
python project/batch_pipeline.py \
  --input ./sample_data/orders.csv \
  --output ./out/core_sdk
cat out/core_sdk*
```

The full project pipeline gives the currency-converted figures:

```text
region,order_count,revenue_eur
AMER,318,113592.19
APAC,285,108194.92
EMEA,322,118423.22
LATAM,320,110646.18
```

The simplified `build_summary_pipeline` above deliberately skips the
currency conversion — it sums the raw amounts, so its numbers are
larger and it is not comparable to the table above. The point of that
snippet is the *shape* of the core SDK chain, not its arithmetic. The
authoritative numbers always come from `project/batch_pipeline.py`.

### Step 5 — The DataFrames version, in outline

The equivalent in the DataFrames API — a `text` fence, because the
`dataframe` extra is not part of this environment:

```text
  import apache_beam as beam
  import beam.dataframe.transforms as transforms

  schema = transforms.Schema(
      region="STRING",
      amount="FLOAT64",
      status="STRING",
  )

  with beam.Pipeline() as p:
      orders = (
          p
          | "ReadOrders" >> transforms.read_csv("orders.csv", schema=schema)
          | "KeepComplete" >> transforms.filter(lambda row: row["status"] == "complete")
      )

      summary = (
          orders
          | "GroupByRegion" >> transforms.group_by("region")
          | "Aggregate" >> transforms.aggregate(
                count=transforms.count(),
                revenue=transforms.sum("amount"),
            )
      )

      rows = summary | "ToPCollection" >> transforms.to_pcollection()
```

Note the shape: the *whole* relational part is one expression, and then
you leave the DataFrame world with `to_pcollection` and return to the
core SDK for the sink. That is the normal way the two models are
combined, and it is a good illustration of the relationship: the
DataFrames API handles the relational middle, and the core SDK handles
everything else.

### Step 6 — The hybrid: DataFrames for the join, core SDK for the sink

This is the pattern most worth copying, because it takes the DataFrames
API's strength (readable relational work) without giving up the core
SDK's strengths (custom `DoFn`s, streaming, sinks):

```text
  # 1. Read with the core SDK — any source, any format.
  lines = p | "ReadOrders" >> beam.io.ReadFromText(input_path)

  # 2. Parse and enrich with the core SDK — custom logic goes here.
  orders = lines | "Parse" >> beam.Map(parse_line)

  # 3. Convert to a DataFrame for the relational part.
  df = orders | "ToDataFrame" >> transforms.to_dataframe(schema=schema)

  # 4. Relational work, readably.
  totals = (
      df
      | "Filter" >> transforms.filter(lambda row: row["status"] == "complete")
      | "GroupBy" >> transforms.group_by("region")
      | "Aggregate" >> transforms.aggregate(
            count=transforms.count(),
            revenue=transforms.sum("amount"),
        )
  )

  # 5. Back to the core SDK for the sink.
  rows = totals | "ToPCollection" >> transforms.to_pcollection()
  rows | "WriteSummary" >> beam.io.WriteToText(output_path)
```

### Step 7 — The `Schema` you would declare

For the course's order data, the schema a DataFrames pipeline would
declare:

```text
  order_schema = transforms.Schema(
      order_id="STRING",
      customer_id="STRING",
      order_ts="STRING",
      region="STRING",
      channel="STRING",
      currency="STRING",
      status="STRING",
      amount="FLOAT64",
      product_id="STRING",
  )
```

Compare that with the `ORDER_FIELDS` list in `project/transforms.py`.
That list is the *implicit* schema — the core SDK infers it from the
coders, with no declaration and no check. The DataFrames API makes it
explicit. That explicitness is the DataFrames API's best feature, and it
is worth adopting as a discipline even if you never use the library:
**know the shape of your data, and write it down.**

### Step 8 — BigQuery SQL for the same query

For comparison, the same aggregation as BigQuery SQL:

```sql
SELECT
  region,
  COUNT(*) AS order_count,
  SUM(
    CASE currency
      WHEN 'EUR' THEN amount * 1.00
      WHEN 'USD' THEN amount * 0.92
      WHEN 'GBP' THEN amount * 1.17
      WHEN 'JPY' THEN amount * 0.0064
      ELSE 0
    END
  ) AS revenue_eur
FROM `YOUR_PROJECT_ID.revenue.orders`
WHERE status = 'complete'
GROUP BY region
ORDER BY region
```

Which is better? **If the table is in BigQuery, this one.** It is
shorter, it runs in seconds instead of a minute, it costs a fraction of
the Dataflow cost for a small result, and there is no job to operate.
The DataFrames API only earns its place when the data is *not* already
in BigQuery.

### Step 9 — Verify the core SDK output

```bash
python project/batch_pipeline.py \
  --input ./sample_data/orders.csv \
  --output ./out/core_sdk
cat out/core_sdk*
```

Expected:

```text
region,order_count,revenue_eur
AMER,318,113592.19
APAC,285,108194.92
EMEA,322,118423.22
LATAM,320,110646.18
```

These are the numbers to compare against any future rewrite. If you
rewrite the pipeline in the DataFrames API, they must not change.

---

## 🛠️ Common Errors and Fixes

### `AttributeError: module 'apache_beam' has no attribute 'dataframe'`

The `dataframe` extra is not installed. Either install it in a separate
environment (Step 2), or accept that the core SDK is the model you are
working in — which, for this course, is the intended path.

### `ImportError: cannot import name 'dataframe' from 'apache_beam'`

The same problem, different phrasing. The extra is a separate
distribution (`apache-beam[dataframe]`), not part of the base package.

### `ValueError: Unknown type 'STRING'` (or a similar type error)

The DataFrames API uses Beam's type names, not SQL's and not pandas'
dtypes. The valid names are `INT64`, `FLOAT64`, `BOOL`, `STRING`,
`BYTES`, `ARRAY`, `STRUCT` and `DATETIME`. `str`, `int`, `float` and
`bool` are **not** accepted.

### `TypeError: Expected a schema, got None`

A `to_dataframe` or `read_csv` call needs an explicit schema when the
source's types are not inferable. This is a common and legitimate
complaint: the DataFrames API's insistence on an explicit schema is
both its best feature and its most common friction point.

### `AttributeError: 'DataFrame' object has no attribute 'groupby'`

The method is `group_by`, not `groupby`. The API is Beam's, not
pandas' — the names are snake_case with underscores, and the
aggregation API is `aggregate`, not `agg` (though some pandas-style
aliases exist).

### `NotImplementedError: Streaming is not supported by the DataFrames API`

As expected. The DataFrames API is a batch relational model. For a
streaming pipeline, use the core SDK, with `beam.WindowInto`,
`beam.GroupByKey` and stateful `DoFn`s.

### `RuntimeError: Transform name is already used` after a hybrid pipeline

The DataFrames API emits its own transforms into the same graph as your
core SDK transforms, and they are labelled. If you build two DataFrame
branches in one pipeline, the generated labels can collide. Give your
own branches explicit labels and check the graph with `print(p)` when
combining the two models.

### The DataFrames pipeline is slower than the core SDK one

This is the expected behaviour, not a bug. The DataFrames API does not
guarantee the same step-level fusion. Check the job graph for an extra
stage between what you expected to be fused steps, and compare the
element counts in the stage metrics.

### `pandas.errors.MergeError` (or a pyarrow error) inside a DataFrames pipeline

The DataFrames API falls back to pandas internally for some operations,
and pandas has its own rules about dtypes and nullability that Beam's
schema does not always match. When you hit one, the fix is usually to
make the schema more precise — mark a column non-nullable, or give it
the exact type pandas expects.

---

## 💡 Production Notes

- **The DataFrames API is a readability aid, not a performance win.**
  This is the sentence to remember. It optimises scans, filters and
  projections; it does not promise the core SDK's step-level fusion, and
  a rewrite can be slower.
- **The `dataframe` extra is not installed in the course virtualenv, on
  purpose.** The course project depends only on the core SDK. If you
  add the extra, do it in a separate environment — pandas and pyarrow
  are large dependencies and they can change core SDK behaviour in ways
  the course tests do not expect.
- **Choose the DataFrames API for the relational middle of a pipeline,
  and the core SDK for the ends.** Read with the core SDK (any source),
  do the relational work in a DataFrame, write with the core SDK (any
  sink). This is the hybrid pattern in Step 6, and it is the shape you
  will see in real code.
- **Beam's `FLOAT64` is a double, and money does not sum in doubles.**
  If you are summing revenue, the core SDK with `Decimal` — or a
  BigQuery `NUMERIC` — is the right tool. The DataFrames API has no
  decimal type.
- **If the data is already in BigQuery, BigQuery SQL wins.** It is
  faster to write, faster to run, and cheaper for a small result. The
  Dataflow streaming engine exists for the case where BigQuery's
  ingestion latency is insufficient — a real case, but not a default.
- **The DataFrames API's execution model is not a `PTransform` graph.**
  You write a DataFrame; the library emits a graph. That means the thing
  you wrote is not the thing that runs, and debugging means reading the
  generated graph. Budget for that when you choose it.
- **The community is small.** Very few public Beam codebases use the
  DataFrames API. The bus factor is a real, quantifiable cost, and it is
  the strongest practical argument for the core SDK in a team that
  might move on.
- **An explicit schema is worth having even without the library.** The
  `Schema` discipline — knowing the column names, types and nullability
  of your data, and writing it down — is what makes the DataFrames API
  valuable. You can adopt the discipline without adopting the library.
- **Do not expect streaming support.** If the pipeline is streaming, the
  core SDK is the only option, and there is no workaround in the
  DataFrames API.

---

## 🔑 Key Takeaways

- "Beam SQL" usually means the **Python DataFrames API**
  (`apache_beam.dataframe`), which is an **optional extra** — it is not
  installed in the course virtualenv, and the course project does not
  depend on it.
- The DataFrames API has its own type system — `INT64`, `FLOAT64`,
  `BOOL`, `STRING`, `BYTES`, `ARRAY`, `STRUCT`, `DATETIME` — and an
  explicit `Schema`/`Row` model with **no null type**.
- It is good at **readability for SQL-fluent teams**, **construction-time
  schema checking**, and **relational joins**.
- It is bad at **performance** (no guaranteed core-SDK fusion), **custom
  `DoFn`s**, **windowing and state**, **side inputs**, and **streaming**.
- **The execution model is different**: you write a DataFrame, the
  library emits a Beam graph. The thing you wrote is not the thing that
  runs.
- **If the data is already in BigQuery, BigQuery SQL is strictly
  better** for most workloads. The DataFrames API's niche is relational
  work on data BigQuery cannot see.
- **The honest verdict: the core SDK is the right default** for a course
  and for production. The DataFrames API is worth learning and worth
  reaching for when the transformation is genuinely relational and the
  team thinks in SQL.
- **The hybrid is the pattern to copy**: core SDK to read, DataFrames for
  the relational middle, core SDK to write.

---

## 📚 Practice Exercises

1. **Install and inspect.** Install `apache-beam[dataframe]==2.77.0` in
   a separate virtualenv, then run `dir(beam.dataframe.transforms)` and
   list every public name. Write down the ten you would expect to use
   and mark which of them exist.
   *Expected answer:* the main names exist
   (`Schema`, `select`, `filter`, `group_by`, `aggregate`, `join`,
   `assign`, `drop`, `to_pcollection`, `to_dataframe`), and several
   pandas-flavoured aliases exist alongside them.

2. **Rewrite the course pipeline in the DataFrames API.** Using the
   extra from exercise 1, rewrite `project/batch_pipeline.py`'s
   aggregation in the DataFrames API and confirm the output matches the
   core SDK's exactly: AMER 318/113592.19, APAC 285/108194.92,
   EMEA 322/118423.22, LATAM 320/110646.18. Then measure the wall-clock
   time of both on the sample data.
   *Expected answer:* the numbers match; the timings are within noise on
   5,000 rows, because at this size worker startup dominates and the
   fusion difference is invisible.

3. **Prove the fusion difference.** Find a dataset large enough that
   the fusion difference shows — generate one with
   `python resources/sample_data.py --output-dir ./big_sample
   --hot-key-rate 0.5`, or download a public CSV. Compare the number of
   stages in the job graph between the two implementations.
   *Expected answer:* the core SDK fuses the parse, filter and key
   stages into fewer stages than the DataFrames API's generated graph.

4. **Write the schema.** Write the `Schema` for the events data
   (`EVENT_FIELDS` in `project/transforms.py`) and then check every
   field against the actual sample data for type consistency — is
   `value` always numeric? Is `event_ts` always a timestamp?
   *Expected answer:* `value` is a float, `event_ts` is a string in
   ISO-8601 (which is why the `Schema` says `STRING` and not
   `DATETIME` — the parsing happens in the `DoFn`).

5. **Find the boundary.** Take your own current project and mark, for
   each stage, whether it is relational or not. Then draw the line
   between the two.
   *Expected answer:* read, parse and enrich are not relational;
   the aggregation is; the sink is not. The DataFrames API would own
   the middle stage only.

6. **Compare with BigQuery SQL.** Write the BigQuery SQL equivalent of
   the course's revenue pipeline, including the currency conversion, and
   compare it line by line with the DataFrames API version. Then answer:
   if the orders table were already in BigQuery, which would you use,
   and what would make you use the other one anyway?
   *Expected answer:* BigQuery SQL, unless the requirement is
   sub-minute freshness from Pub/Sub, in which case the Dataflow
   streaming pipeline wins.

---

## 📖 Further Reading

- Beam's DataFrames API — https://beam.apache.org/documentation/sdks/python/dataframe-overview/
- The DataFrames API reference — https://beam.apache.org/documentation/sdks/python/dataframe-api/
- The `dataframe` extra on PyPI — https://pypi.org/project/apache-beam/
- Beam's type system (type hints and schemas) — https://beam.apache.org/documentation/sdks/python/type-hints/
- BigQuery SQL reference — https://cloud.google.com/bigquery/docs/reference/standard-sql/
- BigQuery vs Dataflow: choosing the right tool — https://cloud.google.com/bigquery/docs/introduction-bigquery-dataflow
- Dataflow's Beam SQL / Calcite status — https://beam.apache.org/documentation/sdks/java/testing/
