# 3.5 — Cloud Workbench & Beam Basics

> **Section 3 · I/O & Multi-Source Pipelines · Lecture 3.5 · 6:30**

## 🎯 What you will learn

- What Cloud Workbench actually is: a managed JupyterLab VM with GCP credentials already attached
- How it differs from Colab, and which one to reach for on a given day
- Running Beam inside Workbench, and the two things that break when you do
- The **explore → codify** workflow: why the reference implementation comes first
- A walkthrough of `resources/sample_data.py` and the `sample_data/` layout it produces
- Why `malformed_orders.csv` exists, and what each of its five rows is testing
- Exploring the data with pandas *before* writing a single line of Beam
- The pure-Python reference implementation, and how to cross-validate the Beam version against it

---

## 🧠 Concept

### The shape of the problem

You now have three chapters' worth of I/O machinery: a file format
catalogue, a multi-source/multi-sink pattern, and GCS plus BigQuery. What
you do *not* yet have is a workflow that tells you what to write.

The gap between "I know the Beam API" and "I have a correct pipeline" is
almost never filled by learning more API. It is filled by:

1. **Looking at the data** — before writing any transform, know what the
   rows look like, which ones are broken, and what "correct" means.
2. **Writing the answer in plain Python** — a reference implementation
   that a human can read and argue with.
3. **Making the Beam version agree with the reference** — and proving it,
   not assuming it.

This chapter is about that workflow, and about the environment where you
are most likely to do steps 1 and 2: **Cloud Workbench**.

### What Cloud Workbench is

Cloud Workbench (now branded *Agent Platform Workbench*) is a managed
Compute Engine VM with JupyterLab pre-installed, running inside your GCP
project, on your VPC, with your project's credentials attached.

That last clause is the whole point. A Workbench instance is a machine
that is *already inside your cloud boundary*:

| Property | What it means |
|---|---|
| Persistent disk | Your files survive; the VM can be stopped and restarted |
| Pre-warmed VM | Start it and JupyterLab is live — no image build, no package install |
| VPC networking | It sits in your network, next to your Dataflow subnets and your GCS buckets |
| Service account | Its calls to GCP are made as *you*, scoped by that service account's IAM roles |
| Idle shutdown | It stops itself after 180 idle minutes, so you do not pay for it all night |
| Custom containers | You can bake in a specific Python environment, Beam included |

The "pre-warmed" part deserves emphasis, because it is what makes
Workbench a *developing* environment rather than a *developing about
environment*. A Workbench instance is an ordinary Compute Engine VM with
the Jupyter stack already installed. You are not waiting for a container
to be scheduled and pulled; you are waiting for a VM to boot, which
takes well under a minute on an `e2-standard` machine type.

The service account is what makes the environment *useful* rather than
merely convenient. A Workbench instance created with
`--service-account-email=...` makes its GCP API calls as that service
account, using the instance's attached OAuth token. That means:

- `gsutil ls gs://your-bucket` works, with the bucket's IAM, not yours
- `gcloud dataflow jobs list` works, with the Dataflow permissions
  that service account holds
- A `beam.Pipeline()` with `DataflowRunner` submits a job *as that
  service account*, so the job's own permissions are the service
  account's — not the human developer's

That last point is the security argument for using Workbench at all
rather than a laptop with a personal key file. The developer's own
credentials never touch the pipeline. If a pipeline is going to run in
production, it should run in development with the *same* identity, and
Workbench is how you arrange that.

### Workbench vs Colab

Both are managed Jupyter environments. They optimise for different
things, and the difference matters more than the feature checklist
suggests.

| | Colab | Cloud Workbench |
|---|---|---|
| Lifetime | Runtime is disposable; state is lost on idle disconnect | Persistent disk; stop and restart keeps everything |
| Startup | Interactive, near-instant | Boot a VM, then JupyterLab — under a minute on a warm instance |
| Identity | Your personal Google account, or a Colab Enterprise runtime template | A service account you choose, with IAM you control |
| Network | Public internet only (Colab Enterprise adds VPC) | Inside your VPC, peered to Dataflow and GCS |
| Package installs | Ephemeral, per-session | Persistent, per-environment; baked into a custom container if you want |
| GPU | Available, quota-dependent | Available, with reservations |
| Cost | Free tier or pay-as-you-go | You pay for the VM, but it auto-stops when idle |
| Audience | Learning, sharing, quick experiments | Production-adjacent work, data engineering, anything with a VPC |

The practical rule:

> **Use Colab to learn a language and a library. Use Workbench to work on
> a pipeline that will run in your infrastructure.**

If your pipeline will read `gs://` buckets behind VPC Service Controls,
talk to a private BigQuery dataset, or submit Dataflow jobs in a
specific project, Colab's personal identity is the wrong identity and
its public network is the wrong network. Workbench fixes both at once.

And note the idle-shutdown economics. A Workbench instance stops itself
after **180 inactive minutes** by default, and while stopped it incurs
no CPU or GPU charges — though **disk storage charges continue**. So the
cost of leaving a Workbench instance around overnight is the disk, not
the vCPU. That is cheap, but not free, and a disk you never clean up is
still a disk you are paying for. The console lets you set the idle
period anywhere from 10 to 1,440 minutes, and it can be disabled
entirely.

```bash
# 12 hours instead of the 3-hour default
gcloud workbench instances update INSTANCE_NAME \
  --metadata=idle-timeout-seconds=43200

# never shut down (you are paying for the disk anyway, and you want the
# kernel alive between sittings)
gcloud workbench instances update INSTANCE_NAME \
  --metadata=idle-timeout-seconds=
```

### Two things that break when you run Beam in Workbench

**One: the runner does not pick up your `--runner` flag.** This is the
same trap Chapter 3.3 documented, and it bites harder in a notebook,
because a notebook cell is not a script and the flag is nowhere in
sight. `beam.Pipeline()` with no `options=` argument builds
`PipelineOptions([])`, which knows nothing about your command line.

The fix is to construct the options explicitly:

```python
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(["--runner=PrismRunner"])
with beam.Pipeline(options=options) as pipeline:
    ...
```

Pass the flags as a *list of strings* to the `PipelineOptions`
constructor. Do not rely on `sys.argv` — in a notebook, `sys.argv` is
the *kernel's* argv, not your shell's.

**Two: the working directory is not the course root.** A Jupyter
notebook's working directory is the directory the kernel was started
in, which on a Workbench instance is the user's home directory
(`~/`), not wherever you cloned the project. Every relative path —
`./sample_data/orders.csv`, `./out/` — resolves somewhere else.

Two ways to fix it, and you should use the first:

```python
# 1. Explicit, and obvious in review.
from pathlib import Path

PROJECT_ROOT = Path("/home/jupyter/workbench/course")
os.chdir(PROJECT_ROOT)
```

```python
# 2. Resolve paths relative to the notebook, not to the CWD.
PROJECT_ROOT = Path.cwd()  # or Path(__file__).parent for a .py file
DATA = PROJECT_ROOT / "sample_data" / "orders.csv"
```

The habit to build: **never write a bare relative path in a pipeline.**
Paths should be derived from a root constant, so the same code runs in
a notebook, in a script, and in a Dataflow job where the working
directory is a worker sandbox you do not control.

### The explore → codify workflow

This is the chapter's central idea, and it is worth stating plainly
because it is the thing people skip.

```
   ┌──────────────────────────────────────────────────┐
   │  1. EXPLORE                                      │
   │     What is in this file?                        │
   │     Which rows are broken, and in how many ways?  │
   │     What does "correct" mean here?               │
   │                                                  │
   │     Tools: pandas, a shell, a text editor        │
   │     Output: a set of questions, answered        │
   └───────────────────────┬──────────────────────────┘
                           │
                           ▼
   ┌──────────────────────────────────────────────────┐
   │  2. REFERENCE                                    │
   │     Write the answer in plain Python.            │
   │     No Beam. No runner. No cluster.              │
   │                                                  │
   │     Output: a function whose output you believe  │
   └───────────────────────┬──────────────────────────┘
                           │
                           ▼
   ┌──────────────────────────────────────────────────┐
   │  3. CODIFY                                      │
   │     Write the Beam pipeline.                    │
   │     Same logic, distributed primitives.          │
   │                                                  │
   │     Output: a pipeline that produces a PCollection│
   └───────────────────────┬──────────────────────────┘
                           │
                           ▼
   ┌──────────────────────────────────────────────────┐
   │  4. CROSS-VALIDATE                              │
   │     Run both on the same input.                  │
   │     Assert they agree.                          │
   │                                                  │
   │     Output: a test that fails when the pipeline  │
   │              is wrong                             │
   └──────────────────────────────────────────────────┘
```

The order matters, and each step is cheaper than the one after it.

**Step 1 is cheapest of all** and it is the step most often skipped.
Twenty minutes with `pandas.read_csv` and `value_counts` will tell you
that 12% of orders are `refunded` and that 5 rows are malformed.
Discovering the same thing by running a Beam pipeline means waiting
for a runner, reading logs, and interpreting a stack trace.

**Step 2 is where the thinking happens.** Writing
`build_revenue_summary(rows)` in plain Python forces you to decide what
"revenue" means: which statuses count, how currency is converted, what
happens to a row with an unknown region. In Beam, you can hide all
three decisions inside a `CombineFn` and never confront them.

**Step 3 is the mechanical translation.** Once you know what the answer
should be, the Beam version is mostly a matter of choosing primitives:
a `Map` here, a `CombinePerKey` there.

**Step 4 is what makes the whole thing trustworthy.** And this is the
step the course's `project/transforms.py` is built around.

### The reference implementation pattern

`project/transforms.py` contains two implementations of the same
revenue calculation.

The pure one:

```python
def build_revenue_summary(
    rows: Iterable[dict[str, Any]],
    *,
    statuses: Sequence[str] = ("complete",),
) -> dict[str, dict[str, float]]:
    """Aggregate revenue per region from a collection of orders.

    This is the reference implementation of what `RevenueByRegionFn` does
    inside a Beam pipeline. Keeping a pure twin makes the combiner testable
    without a runner, and makes the combiner's correctness self-evident.
    """
    wanted = set(statuses)
    summary: dict[str, dict[str, float]] = {}

    for row in rows:
        if not is_valid_order(row):
            continue
        if row["status"] not in wanted:
            continue
        region = row["region"]
        bucket = summary.setdefault(region, {"order_count": 0.0, "revenue_eur": 0.0})
        bucket["order_count"] += 1
        bucket["revenue_eur"] += normalise_currency(float(row["amount"]), row["currency"])

    for bucket in summary.values():
        bucket["revenue_eur"] = round(bucket["revenue_eur"], 2)
    return summary
```

The Beam one:

```python
class RevenueByRegionFn(beam.CombineFn):
    """Aggregate order count and revenue per region.

    A `CombineFn` must be *associative* and *commutative*, because Beam
    merges partial accumulators from different workers in an arbitrary
    order. `add_input` accumulates one order, `merge_accumulators` merges
    two partial sums, and the merge must produce the same result as
    adding the inputs in any other order.
    """

    def create_accumulator(self) -> dict[str, float]:
        """Create an empty accumulator."""
        return {"order_count": 0.0, "revenue_eur": 0.0}

    def add_input(self, accumulator: dict[str, float], order: dict[str, Any]) -> dict[str, float]:
        """Add one order to the accumulator."""
        accumulator["order_count"] += 1
        accumulator["revenue_eur"] += normalise_currency(
            float(order["amount"]), order["currency"]
        )
        return accumulator

    def merge_accumulators(
        self, accumulators: Iterable[dict[str, float]]
    ) -> dict[str, float]:
        """Merge partial accumulators from different workers."""
        total = self.create_accumulator()
        for partial in accumulators:
            total["order_count"] += partial["order_count"]
            total["revenue_eur"] += partial["revenue_eur"]
        return total
```

Read them side by side and the relationship is obvious. `add_input` is
the body of the `for` loop. `merge_accumulators` is the same addition
applied to partial sums. `extract_output` is the rounding loop. The
Beam version is *structurally* the pure version with the loop replaced
by a distributed merge.

Now, the reason this matters is not elegance. It is that the pure
version is **testable in microseconds, with no runner, no cluster, no
credentials, and no network**. You can assert on it directly:

```python
def test_reference_summary():
    """The reference implementation should be exactly right."""
    rows = [
        {"order_id": "o1", "customer_id": "c1", "order_ts": "2026-01-15T00:00:00+00:00",
         "region": "EMEA", "channel": "web", "currency": "EUR",
         "status": "complete", "amount": 100.0, "product_id": "p1"},
        {"order_id": "o2", "customer_id": "c1", "order_ts": "2026-01-15T00:00:00+00:00",
         "region": "EMEA", "channel": "web", "currency": "GBP",
         "status": "complete", "amount": 50.0, "product_id": "p1"},
        {"order_id": "o3", "customer_id": "c1", "order_ts": "2026-01-15T00:00:00+00:00",
         "region": "EMEA", "channel": "web", "currency": "EUR",
         "status": "refunded", "amount": 999.0, "product_id": "p1"},
    ]
    summary = build_revenue_summary(rows)
    assert summary["EMEA"]["order_count"] == 2
    assert summary["EMEA"]["revenue_eur"] == 158.5
```

The `refunded` order is the interesting one. It is in the input, it
parses fine, it passes every structural check — and it is excluded
because revenue counts only `complete` orders. A test that did not
include it would not notice if the status filter were silently
dropped. Tests are built from the cases you know are hard, and the
hard cases are the ones that are excluded.

**Why the twin exists at all.** The alternative is to test the
`CombineFn` directly. You can do that — `beam.testing.util.assert_that`
with `beam.testing.TestStream` or a `Create` source — but it requires a
runner, it is slower, and its failure messages are worse. The pure
twin lets you test the *arithmetic* in one place and the *plumbing* in
another, and the cross-validation step ties them together.

### `resources/sample_data.py`

The course's exercises run against generated data rather than checked-in
data, for two reasons: the data is deterministic, and it can be
regenerated at whatever scale the exercise needs.

`resources/sample_data.py` generates the `sample_data/` directory:

```bash
python resources/sample_data.py --output-dir ./sample_data
```

Everything it produces is seeded (`SEED = 42`), so every run produces
byte-identical output. That is a deliberate design decision for a
course: the expected outputs printed in the chapters stay correct no
matter when you run them, and on which machine.

| File | Format | Rows | What it is for |
|---|---|---|---|
| `orders.csv` | CSV with header | 5,000 | The main order source for the batch chapters |
| `orders.ndjson` | newline-delimited JSON | 5,000 | The same orders, JSON-shaped |
| `events.ndjson` | newline-delimited JSON | 20,000 | Clickstream events, for the streaming chapters |
| `events.csv` | CSV with header | 20,000 | The same events, CSV-shaped |
| `malformed_orders.csv` | CSV, no header | 5 | Rows that fail — for the error-handling chapters |
| `product_reference.ndjson` | newline-delimited JSON | 50 | A small lookup table, for side inputs |
| `summary.json` | JSON | — | Counts and metadata about the generated set |

The useful flags:

```bash
# More rows, to see how behaviour changes with scale
python resources/sample_data.py --orders 50000 --events 200000

# A different target day — the timestamps all move
python resources/sample_data.py --date 2026-03-01

# Skew: 50% of orders land on one customer key.
# This is the input for the CombinePerKey skew chapter.
python resources/sample_data.py --hot-key-rate 0.5

# Late data: the last N events are backdated to 23:59.
# This is the input for the allowed-lateness and watermark chapters.
python resources/sample_data.py --late-events 500

# Push it to a bucket
python resources/sample_data.py --upload gs://YOUR_BUCKET/staging
```

The `--hot-key-rate` and `--late-events` flags are worth understanding
now, even though their chapters come later. They are the two ways real
pipelines break that a naive dataset never reveals: **skew**, where one
key gets a disproportionate share of the data, and **late data**, where
records arrive after the window they belong to has closed.

The generated `summary.json` is the fastest way to confirm what you
generated:

```json
{
  "orders": 5000,
  "events": 20000,
  "malformed_rows": 5,
  "reference_rows": 50,
  "target_date": "2026-01-15"
}
```

### `malformed_orders.csv` and why it exists

A pipeline that rejects bad input needs bad input to reject. Without
it, every error-handling exercise is theoretical, and — worse — a
pipeline that *silently* drops rows looks identical to one that works
perfectly. The five rows in `malformed_orders.csv` are not random
garbage; each one exercises a *different* failure path, and the paths
are different in kind.

```text
not-an-order,missing-fields,garbage
o99999999,c000001,not-a-timestamp,EMEA,web,EUR,complete,not-a-number,p0001
o99999998,c000002,2026-01-01T00:00:00+00:00,UNKNOWN_REGION,web,EUR,complete,100.00,p0002
o99999997,c000003,2026-01-01T00:00:00+00:00,EMEA,web,XYZ,complete,100.00,p0003
,,,,
```

| Row | What is wrong | Which check catches it |
|---|---|---|
| 1 | 3 fields instead of 9 | `try_parse_order_line` → `None` (field count) |
| 2 | `not-a-timestamp`, `not-a-number` | `try_parse_order_line` → `None` (amount coercion) |
| 3 | `UNKNOWN_REGION` | `is_valid_order` → `False` (region not in `VALID_REGIONS`) |
| 4 | `XYZ` is not a currency | `is_valid_order` → `False` (currency not in `CURRENCY_TO_EUR`) |
| 5 | all fields empty | `try_parse_order_line` → `None` (empty after strip) |

Rows 1, 2 and 5 are **parse** failures: the row does not have the shape
of an order, so no amount of downstream processing will help. Rows 3
and 4 are **validation** failures: the row has the right shape but
breaks a *business* rule.

That distinction is the point of the file, and it is why
`project/transforms.py` has two functions rather than one:

```python
def try_parse_order_line(line: str) -> dict[str, Any] | None:
    """Parse one CSV line into an order dict, returning None when malformed.

    Returns the order dict, or None when the line cannot be parsed.
    """
    text = line.strip()
    if not text:
        return None
    try:
        values = next(csv.reader(io.StringIO(text)))
    except (csv.Error, StopIteration):
        return None
    if len(values) != len(ORDER_FIELDS):
        return None
    row = dict(zip(ORDER_FIELDS, values))

    # Coerce the numeric field so downstream code can trust its type.
    try:
        row["amount"] = float(row["amount"])
    except (TypeError, ValueError):
        return None
    return row
```

`try_parse_order_line` answers a *structural* question: is this the
right shape? `is_valid_order` answers a *semantic* question: is this
row one we are willing to count?

The two failure kinds have different operational responses, and
conflating them is a real operational mistake:

- **A parse failure** is usually a **producer bug** or a **schema
  change upstream**. The row count that suddenly drops is a signal
  something changed. You want to page someone.
- **A validation failure** is usually **data**. A row from a region you
  have not onboarded, a currency you have not priced. You want to
  count it, route it to a dead-letter queue, and review it later.

The course's `ParseOrderFn` currently logs both and skips both, which
is the right *starting* point and the wrong *end state* — the
error-handling chapter replaces it with a DLQ. But the log message
already distinguishes them:

```python
class ParseOrderFn(beam.DoFn):
    """Parse CSV lines into order dicts, skipping malformed rows.

    The malformed rows are logged rather than raised, because one bad
    line in a 10-million-line file should not fail the entire bundle.
    A pipeline that must not lose data should route them to a
    dead-letter topic instead — see the "Error Handling and DLQ"
    chapter.
    """

    def process(self, line: str, timestamp=beam.DoFn.TimestampParam) -> Iterable[Any]:
        """Parse one line and emit the resulting order dict."""
        row = try_parse_order_line(line)
        if row is None:
            log.warning("skipping malformed order line: %.120s", line)
            return
        if not is_valid_order(row):
            log.warning("skipping invalid order: %s", row.get("order_id"))
            return
        yield row
```

Note the two different messages: "malformed order line" versus "invalid
order". They are different problems and they get different responses.

### Exploring with pandas before you write Beam

This is the part people push back on, because pandas feels like a
different tool from Beam and using both feels redundant. It is not
redundant — they answer different questions.

**pandas answers questions about the data.** How many rows? What
fraction are `refunded`? Which region is missing? Is `amount` ever
negative? Is there a row where `order_ts` is not a timestamp?

**Beam answers questions about the pipeline.** Can this run at scale? Is
the combiner associative? What happens when a shard fails halfway?

You cannot answer the first set of questions with the second tool
efficiently, and you *must* answer the first set before you write the
second.

A ten-minute pandas session on `sample_data/orders.csv` will typically
surface:

```python
import pandas as pd

orders = pd.read_csv("sample_data/orders.csv")

print(orders.shape)
print(orders["status"].value_counts())
print(orders["region"].value_counts())
print(orders["currency"].value_counts())
print(orders["amount"].describe())
print(orders.isna().sum().sum())
```

The output for the standard 5,000-order dataset is:

```text
(5000, 9)
status
refunded    1305
active      1262
complete    1245
cancelled   1188
Name: count, dtype: int64

region
AMER     1284
LATAM    1265
EMEA     1240
APAC     1211
Name: count, dtype: int64

currency
EUR    1284
JPY    1268
GBP    1231
USD    1217
Name: count, dtype: int64
```

Immediately useful facts, none of which required a Beam runner:

- 1,245 of 5,000 orders (24.9%) are `complete`. If your pipeline
  reports 5,000 orders in the revenue summary, it is not filtering by
  status.
- The four regions are near-uniformly distributed (1,211 to 1,284).
  A heavily skewed region count would tell you your keying is wrong.
- Four currencies, roughly uniform. If the pipeline's EUR revenue
  implies a conversion you cannot reproduce, the rate table is the
  thing to check.

**A warning about the numbers above.** They are for the *unfiltered*
file, which includes rows that are `complete` but not *valid* — the
`UNKNOWN_REGION` and `XYZ` rows. The reference implementation filters
those out, so the valid-and-complete count is 1,245 minus any
`complete` rows that fail validation. On the standard dataset the
malformed file is separate, so the 1,245 stands; but on a dataset where
bad rows are mixed in, the pandas count and the pipeline count will
differ, and *that difference is the point of the cross-validation step*.

### Cross-validation: the step that makes it trustworthy

Now the payoff. You have:

- `build_revenue_summary(rows)` — pure Python, no runner needed
- `RevenueByRegionFn` — the `CombineFn` that does the same thing inside
  a pipeline

The check is to run both over the same input and assert they agree.

```python
from transforms import build_revenue_summary, try_parse_order_line, is_valid_order

rows = []
with open("sample_data/orders.csv") as fh:
    next(fh)  # skip the header
    for line in fh:
        row = try_parse_order_line(line)
        if row is not None and is_valid_order(row):
            rows.append(row)

summary = build_revenue_summary(rows)
```

The pure version gives:

```text
AMER,318,113592.19
APAC,285,108194.92
EMEA,322,118423.22
LATAM,320,110646.18
```

And the Beam pipeline gives exactly the same four lines. Every count
and every amount to the cent.

**Why this catches real bugs.** Because the two implementations fail
*differently*. The pure version has a single `for` loop, so the only
way it is wrong is if the logic is wrong. The Beam version has
`add_input` and `merge_accumulators` and a `CombinePerKey` and a
type-inference layer, and each of those is a place to make a mistake.

The most common Beam-only bug is a **non-associative combiner**. If
`merge_accumulators` rounds, or if `add_input` rounds, the result
depends on how the data was partitioned — which is different on every
run, and different again on a cluster. The pure version has no merge
step, so it cannot have this bug. Comparing the two is how you find it.

The second most common is a **filter that lives in the wrong place**. If
you filter `status == "complete"` after the combine instead of before,
the counts come out as 5,000 and the revenues are far too large. The
pure implementation puts the filter in one obvious place, and the
cross-validation says the Beam one must match.

The third is a **type-inference surprise**. `CombinePerKey` needs to
know the key type and the value type. If the key is a `str` and the
value is a `dict`, Beam has to pick a coder for the dict, and the
default fallback is `PickleCoder` — which works on the `DirectRunner`
and fails on Dataflow workers. The pure version has no coders at all,
so the mismatch shows up only in the Beam run, and the
cross-validation is what makes you look.

**How to make it a test, not a ritual.** A cross-validation you run by
hand once is worth much less than one that runs in CI. The course's
`project/tests/` directory already has the pattern:

```python
def test_beam_summary_matches_reference():
    """The Beam pipeline should agree with the pure reference."""
    expected = reference_summary()
    actual = beam_summary()
    assert actual == expected
```

The point is that this test fails *loudly and specifically* when
someone changes the combiner, and it does so in a second rather than
after a cluster spin-up.

---

## 🛠️ Hands-On

Everything in this section runs in the course root, with no credentials
and no cloud resources. Where a step is Workbench-specific, it is
marked as such and the equivalent local command is given.

### Step 1 — look at what you have

Start by seeing the sample data, not by writing a pipeline.

```bash
ls -la sample_data/
cat sample_data/summary.json
head -3 sample_data/orders.csv
```

Expected:

```text
total 12384
drwxr-xr-x@  9 pvishnoi  1077912953      288 Oct 28 11:17 .
drwxr-xr-x@ 22 pvishnoi  1077912953      704 Oct 28 15:49 ..
-rw-r--r--@  1 pvishnoi  1077912953   1414490 Oct 28 15:08 events.csv
-rw-r--r--@  1 pvishnoi  1077912953   3434428 Oct 28 15:08 events.ndjson
-rw-r--r--@  1 pvishnoi  1077912953      284 Oct 28 15:08 malformed_orders.csv
-rw-r--r--@  1 pvishnoi  1077912953    407269 Oct 28 15:08 orders.csv
-rw-r--r--@  1 pvishnoi  1077912953   1062189 Oct 28 15:08 orders.ndjson
-rw-r--r--@  1 pvishnoi  1077912953      4043 Oct 28 15:08 product_reference.ndjson
-rw-r--r--@  1 pvishnoi  1077912953      118 Oct 28 15:08 summary.json
{
  "orders": 5000,
  "events": 20000,
  "malformed_rows": 5,
  "reference_rows": 50,
  "target_date": "2026-01-15"
}
order_id,customer_id,order_ts,region,channel,currency,status,amount,product_id
o00000000,c000914,2026-01-15T00:54:38+00:00,AMER,web,GBP,complete,700.97,p0173
o00000001,c004469,2026-01-15T03:09:55+00:00,EMEA,web,JPY,active,211.61,p0129
```

The `summary.json` file is the fastest sanity check: if the numbers do
not match what you expect, the data is not what the chapter assumes,
and every expected output below will be wrong.

### Step 2 — regenerate the data and prove it is deterministic

The seeded generator is what makes the expected outputs in this course
stable. Prove it: regenerate to a second directory and compare.

```bash
python resources/sample_data.py --output-dir ./sample_data_check
diff -r sample_data sample_data_check && echo "IDENTICAL"
```

Expected:

```text
IDENTICAL
```

`diff -r` compares every file byte for byte. If the generator were not
seeded, this would report differences and every expected output in
every chapter would be a lie.

Clean up when you are done:

```bash
rm -rf sample_data_check
```

### Step 3 — explore with pandas

This is step 1 of the explore → codify workflow. Create
`work/explore_orders.py`:

```python
"""Explore the orders dataset before writing any Beam logic."""

import pandas as pd

orders = pd.read_csv("sample_data/orders.csv")

print(f"shape: {orders.shape}")
print()

print("status:")
print(orders["status"].value_counts())
print()

print("region:")
print(orders["region"].value_counts())
print()

print("currency:")
print(orders["currency"].value_counts())
print()

print("amount:")
print(orders["amount"].describe())
print()

print(f"rows with any null: {orders.isna().any(axis=1).sum()}")
print(f"duplicate order_ids: {orders['order_id'].duplicated().sum()}")
print(f"negative amounts: {(orders['amount'] < 0).sum()}")
print(f"orders per customer (top 5):")
print(orders["customer_id"].value_counts().head())
```

Run it:

```bash
python work/explore_orders.py
```

Expected:

```text
shape: (5000, 9)

status:
status
refunded     1305
active       1262
complete     1245
cancelled    1188
Name: count, dtype: int64

region:
region
AMER     1284
LATAM    1265
EMEA     1240
APAC     1211
Name: count, dtype: int64

currency:
currency
EUR    1284
JPY    1268
GBP    1231
USD    1217
Name: count, dtype: int64

amount:
count    5000.000000
mean     479.367592
std      270.929196
min        5.240000
25%      245.317500
50%      480.100000
75%      713.372500
max      949.990000
Name: amount, dtype: float64

rows with any null: 0
duplicate order_ids: 0
negative amounts: 0
orders per customer (top 5):
customer_id
c000142    7
c002614    7
c001036    6
c000179    6
c004373    6
Name: count, dtype: int64
```

(The `status` / `region` / `currency` / `customer_id` lines repeated
above each table are pandas' `Series` name, which is the column name
it inferred. They are not part of the data.)

The last block is worth a second look. The most orders any single
customer has is 7, out of 5,000 orders spread across nearly 5,000
distinct customers. That is an almost perfectly uniform spread — which
means this dataset is *not* skewed. When you want to see what skew does
to a `CombinePerKey`, regenerate with `--hot-key-rate 0.5` and watch
the top customer jump to roughly 2,500.

Note also `rows with any null: 0` and `duplicate order_ids: 0`. The
sample data is clean by construction. The malformed rows live in a
*separate file* on purpose — a mixed-in bad row would make the
"expected" numbers in the chapters depend on how many bad rows you
generated, and nobody wants expected outputs that move.

### Step 4 — find out what the malformed rows are actually testing

Create `work/inspect_malformed.py`:

```python
"""Show what each malformed row is actually testing."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "project"))

from transforms import is_valid_order, try_parse_order_line  # noqa: E402

PATH = "sample_data/malformed_orders.csv"

with open(PATH) as fh:
    lines = fh.read().splitlines()

print(f"{len(lines)} rows in {PATH}\n")

for number, line in enumerate(lines, 1):
    row = try_parse_order_line(line)
    if row is None:
        kind = "PARSE failure"
        detail = "row is not the right shape"
    elif not is_valid_order(row):
        kind = "VALIDATION failure"
        if row.get("region") not in ("AMER", "EMEA", "APAC", "LATAM"):
            detail = f"unknown region {row.get('region')!r}"
        elif row.get("currency") not in ("EUR", "USD", "GBP", "JPY"):
            detail = f"unknown currency {row.get('currency')!r}"
        else:
            detail = "some other business rule"
    else:
        kind = "VALID"
        detail = "this row should not be here"

    print(f"row {number}: {kind} — {detail}")
    print(f"         {line[:80]}")
    print()
```

Run it:

```bash
python work/inspect_malformed.py
```

Expected:

```text
5 rows in sample_data/malformed_orders.csv

row 1: PARSE failure — row is not the right shape
         not-an-order,missing-fields,garbage

row 2: PARSE failure — row is not the right shape
         o99999999,c000001,not-a-timestamp,EMEA,web,EUR,complete,not-a-number,p0001

row 3: VALIDATION failure — unknown region 'UNKNOWN_REGION'
         o99999998,c000002,2026-01-01T00:00:00+00:00,UNKNOWN_REGION,web,EUR,complete,100.

row 4: VALIDATION failure — unknown currency 'XYZ'
         o99999997,c000003,2026-01-01T00:00:00+00:00,EMEA,web,XYZ,complete,100.00,p0003

row 5: PARSE failure — row is not the right shape
         ,,,,
```

Two kinds of failure, and the distinction is the point. Parse failures
mean the row is not an order. Validation failures mean the row *is* an
order-shaped row but breaks a business rule.

One caveat on row 2: it fails at the `amount` coercion, not at the
timestamp. `try_parse_order_line` coerces `amount` to a float but
leaves `order_ts` as a string, so the timestamp check happens later, in
`is_valid_order`. That is why the script reports it as a parse failure
— it never reaches the validation stage.

### Step 5 — write the reference implementation first

Before any Beam, write the answer in plain Python. The course already
has one in `project/transforms.py`; let us *use* it rather than write a
new one, and check it against a hand-computed case first.

Create `work/reference_summary.py`:

```python
"""Run the pure-Python reference implementation over the sample data."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "project"))

from transforms import (  # noqa: E402
    build_revenue_summary,
    is_valid_order,
    try_parse_order_line,
)

ORDERS = "sample_data/orders.csv"


def load_orders(path: str) -> list[dict]:
    """Parse an orders CSV into validated order dicts."""
    rows = []
    with open(path) as fh:
        next(fh)  # skip the header
        for line in fh:
            row = try_parse_order_line(line)
            if row is not None and is_valid_order(row):
                rows.append(row)
    return rows


def main() -> int:
    """Print the reference revenue summary."""
    rows = load_orders(ORDERS)
    print(f"loaded {len(rows)} valid orders")

    summary = build_revenue_summary(rows)
    print()
    for region in sorted(summary):
        bucket = summary[region]
        print(
            f"{region},{int(bucket['order_count'])},"
            f"{bucket['revenue_eur']:.2f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Run it:

```bash
python work/reference_summary.py
```

Expected:

```text
loaded 5000 valid orders

AMER,318,113592.19
APAC,285,108194.92
EMEA,322,118423.22
LATAM,320,110646.18
```

No Beam. No runner. No cluster. It ran in well under a second.

Now check a hand-computed case, because a reference implementation you
have not verified against a hand calculation is not a reference:

```python
from transforms import build_revenue_summary

# One EUR order, one GBP order, one refunded order.
rows = [
    {"order_id": "o1", "customer_id": "c1",
     "order_ts": "2026-01-15T00:00:00+00:00", "region": "EMEA",
     "channel": "web", "currency": "EUR", "status": "complete",
     "amount": 100.0, "product_id": "p1"},
    {"order_id": "o2", "customer_id": "c1",
     "order_ts": "2026-01-15T00:00:00+00:00", "region": "EMEA",
     "channel": "web", "currency": "GBP", "status": "complete",
     "amount": 50.0, "product_id": "p1"},
    {"order_id": "o3", "customer_id": "c1",
     "order_ts": "2026-01-15T00:00:00+00:00", "region": "EMEA",
     "channel": "web", "currency": "EUR", "status": "refunded",
     "amount": 999.0, "product_id": "p1"},
]

summary = build_revenue_summary(rows)
assert summary["EMEA"]["order_count"] == 2, summary
# 100.00 EUR + 50.00 GBP * 1.17 = 100.00 + 58.50 = 158.50
assert summary["EMEA"]["revenue_eur"] == 158.5, summary
print("reference implementation checks out")
```

Expected:

```text
reference implementation checks out
```

The refunded order is in the input and is not in the output. That
assertion is the one that matters, because a status filter that
silently stopped working is invisible in the aggregate numbers — until
you notice the revenue is 1,157.50 instead of 158.50.

### Step 6 — cross-validate the Beam version against it

Now the Beam version, and the comparison. Create
`work/cross_validate.py`:

```python
"""Cross-validate the Beam pipeline against the pure reference."""

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "project"))

import apache_beam as beam  # noqa: E402
from apache_beam.options.pipeline_options import PipelineOptions  # noqa: E402

from transforms import (  # noqa: E402
    ParseOrderFn,
    RevenueByRegionFn,
    build_revenue_summary,
    is_valid_order,
    to_summary_row,
    try_parse_order_line,
)

ORDERS = "sample_data/orders.csv"
OUTPUT = "out/cross_validate"


def reference_summary() -> dict[str, dict[str, float]]:
    """Compute the expected answer with pure Python."""
    rows = []
    with open(ORDERS) as fh:
        next(fh)
        for line in fh:
            row = try_parse_order_line(line)
            if row is not None and is_valid_order(row):
                rows.append(row)
    return build_revenue_summary(rows)


def beam_summary() -> dict[str, dict[str, float]]:
    """Compute the same answer with a Beam pipeline."""
    options = PipelineOptions(["--runner=PrismRunner"])

    with beam.Pipeline(options=options) as pipeline:
        rows = (
            pipeline
            | "ReadOrders" >> beam.io.ReadFromText(ORDERS)
            | "ParseOrders" >> beam.ParDo(ParseOrderFn())
            | "KeepCompleted" >> beam.Filter(
                lambda order: order["status"] == "complete"
            )
            | "KeyByRegion" >> beam.Map(lambda order: (order["region"], order))
            | "Aggregate" >> beam.CombinePerKey(RevenueByRegionFn())
            | "ToRow" >> beam.Map(to_summary_row)
        )

        rows | "WriteRows" >> beam.io.WriteToText(
            OUTPUT,
            num_shards=1,
            shard_name_template="",
            header="region,order_count,revenue_eur",
        )

    result = {}
    with open(OUTPUT) as fh:
        next(fh)  # skip the header
        for line in fh:
            # WriteToText stringifies a dict. `ast.literal_eval` is safe
            # here — it only evaluates literals, never arbitrary code.
            row = ast.literal_eval(line.strip())
            result[row["region"]] = {
                "order_count": float(row["order_count"]),
                "revenue_eur": float(row["revenue_eur"]),
            }
    return result


def main() -> int:
    """Run both implementations and compare."""
    expected = reference_summary()
    actual = beam_summary()

    print("reference:")
    for region in sorted(expected):
        bucket = expected[region]
        print(f"  {region}: {int(bucket['order_count'])} {bucket['revenue_eur']:.2f}")

    print()
    print("beam:")
    for region in sorted(actual):
        bucket = actual[region]
        print(f"  {region}: {int(bucket['order_count'])} {bucket['revenue_eur']:.2f}")

    print()
    if expected == actual:
        print("MATCH — the Beam pipeline agrees with the reference")
        return 0

    print("MISMATCH")
    for region in sorted(set(expected) | set(actual)):
        want = expected.get(region)
        got = actual.get(region)
        if want != got:
            print(f"  {region}: reference={want} beam={got}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

Run it:

```bash
python work/cross_validate.py
```

Expected:

```text
reference:
  AMER: 318 113592.19
  APAC: 285 108194.92
  EMEA: 322 118423.22
  LATAM: 320 110646.18

beam:
  AMER: 318 113592.19
  APAC: 285 108194.92
  EMEA: 322 118423.22
  LATAM: 320 110646.18

MATCH — the Beam pipeline agrees with the reference
```

The exit code is 0 on a match and 1 on a mismatch, so this works
directly as a CI check.

**A note on the parsing hack.** `WriteToText` stringifies a dict, so
the output file contains Python dict reprs, not CSV. The script parses
them back. That is ugly, and it is deliberate — it keeps the
comparison focused on the *aggregation*, which is what the cross
validation is for. When you want a real CSV, use the course's
`format_summary_csv` helper, which uses `csv.writer` and quotes
correctly. Do not build production output by string-formatting a dict.

### Step 7 — break it, and watch the check catch it

A validation that has never failed is not a validation. Change the
Beam pipeline — deliberately — and confirm the check catches it.

In `work/cross_validate.py`, move the status filter to *after* the
combine:

```python
rows = (
    pipeline
    | "ReadOrders" >> beam.io.ReadFromText(ORDERS)
    | "ParseOrders" >> beam.ParDo(ParseOrderFn())
    | "KeyByRegion" >> beam.Map(lambda order: (order["region"], order))
    | "Aggregate" >> beam.CombinePerKey(RevenueByRegionFn())
    | "KeepCompleted" >> beam.Filter(
        lambda row: row["status"] == "complete"
    )
    | "ToRow" >> beam.Map(to_summary_row)
)
```

(Yes, that is a type error — the aggregate has no `status` key. That
is the point: the mistake does not fail silently, it fails loudly. But
to see a *numeric* mismatch rather than an exception, remove the
filter entirely and change the reference to match the same mistake.)

The cleaner demonstration: change the *reference* to use
`statuses=("complete", "active")` and leave the Beam pipeline alone.

```python
return build_revenue_summary(rows, statuses=("complete", "active"))
```

Run it again:

```bash
python work/cross_validate.py
```

Expected:

```text
reference:
  AMER: 634 222386.30
  APAC: 598 225810.57
  EMEA: 608 215970.20
  LATAM: 667 237869.33

beam:
  AMER: 318 113592.19
  APAC: 285 108194.92
  EMEA: 322 118423.22
  LATAM: 320 110646.18

MISMATCH
  AMER: reference={'order_count': 634.0, 'revenue_eur': 222386.3} beam={'order_count': 318.0, 'revenue_eur': 113592.19}
  APAC: reference={'order_count': 598.0, 'revenue_eur': 225810.57} beam={'order_count': 285.0, 'revenue_eur': 108194.92}
  EMEA: reference={'order_count': 608.0, 'revenue_eur': 215970.2} beam={'order_count': 322.0, 'revenue_eur': 118423.22}
  LATAM: reference={'order_count': 667.0, 'revenue_eur': 237869.33} beam={'order_count': 320.0, 'revenue_eur': 110646.18}
```

The mismatch is detected, the expected and actual values are printed
side by side, and the script exits 1 — so a CI job running it fails
loudly.

**Put the reference back before moving on.** A validation you have
seen fail once is worth ten you have not.

### Step 8 — the Workbench version of the same thing

Everything above runs on a laptop. Here is the same workflow on a
Workbench instance, where the pipeline will eventually run against
real GCS and real BigQuery.

**Create the instance:**

```bash
gcloud workbench instances create beam-course \
  --project=YOUR_PROJECT_ID \
  --location=us-central1-a \
  --vm-image-project=cloud-notebooks-managed \
  --vm-image-name=workbench-instances \
  --machine-type=e2-standard-4 \
  --service-account-email=YOUR_SERVICE_ACCOUNT \
  --network=YOUR_VPC \
  --subnet=YOUR_SUBNET \
  --metadata=idle-timeout-seconds=7200
```

Note the flag names. There is **no** `--service-account` flag — it is
`--service-account-email`. And there is no `--idle-timeout` flag
either; the idle timeout is set through the `--metadata` flag, which
takes `key=value` pairs. The value is in **seconds**, and the default
is 180 minutes (10,800 seconds). The console lets you pick anything
from 10 to 1,440 minutes.

To change it on an instance that already exists, use `update`:

```bash
gcloud workbench instances update beam-course \
  --metadata=idle-timeout-seconds=7200
```

**Open it:**

```bash
gcloud workbench instances list --location=us-central1-a
gcloud workbench instances describe beam-course --location=us-central1-a
```

The `describe` output has the `proxyUri` field, which is the URL to
open in your browser.

**In the notebook, two things must be true.** The working directory is
the course root, and the options are explicit:

```python
import os
import sys
from pathlib import Path

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

# 1. Fix the working directory. A Workbench notebook starts in ~.
COURSE_ROOT = Path("/home/jupyter/workbench/course")
os.chdir(COURSE_ROOT)
sys.path.insert(0, str(COURSE_ROOT / "project"))

from transforms import ParseOrderFn, RevenueByRegionFn, to_summary_row  # noqa: E402

# 2. Be explicit about the runner. The kernel's sys.argv is not
#    your shell's argv.
options = PipelineOptions(["--runner=PrismRunner"])

with beam.Pipeline(options=options) as pipeline:
    rows = (
        pipeline
        | "ReadOrders" >> beam.io.ReadFromText("sample_data/orders.csv")
        | "ParseOrders" >> beam.ParDo(ParseOrderFn())
        | "KeepCompleted" >> beam.Filter(lambda o: o["status"] == "complete")
        | "KeyByRegion" >> beam.Map(lambda o: (o["region"], o))
        | "Aggregate" >> beam.CombinePerKey(RevenueByRegionFn())
        | "ToRow" >> beam.Map(to_summary_row)
    )
    rows | "WriteRows" >> beam.io.WriteToText(
        "out/workbench_summary", num_shards=1, shard_name_template=""
    )
```

**Then the cloud path.** When the pipeline moves to Dataflow, the only
things that change are the options and the paths:

```python
options = PipelineOptions(
    [
        "--runner=DataflowRunner",
        "--project=YOUR_PROJECT_ID",
        "--region=us-central1",
        "--staging_location=gs://YOUR_BUCKET/staging",
        "--temp_location=gs://YOUR_BUCKET/temp",
    ]
)
```

and

```text
    | "ReadOrders" >> beam.io.ReadFromText("gs://YOUR_BUCKET/raw/orders.csv")
```

```text
    | "WriteRows" >> beam.io.WriteToText("gs://YOUR_BUCKET/curated/summary")
```

The *business logic* — the `ParDo`, the `Filter`, the `CombinePerKey` —
is byte for byte identical. That is the whole point of the Beam model,
and it is the thing that makes "develop in Workbench, deploy to
Dataflow" a real workflow rather than two projects.

**A note on what the service account changes.** The Dataflow job
submitted from Workbench runs as the *instance's* service account, not
as you. That is the desired behaviour: the job's permissions are
whatever you granted the service account, and no developer ever needs
`bigquery.tables.updateData` on their personal account. It also means
that a permission you forget to grant the service account shows up as
a job failure, not as a local failure — check the service account's
roles first.

---

## 🛠️ Common Errors and Fixes

### `ModuleNotFoundError: No module named 'transforms'`

The course's `project/` directory is not on `sys.path`.

```text
ModuleNotFoundError: No module named 'transforms'
```

The fix is to add it, relative to the file rather than to the working
directory:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "project"))
```

In a notebook, `Path(__file__)` does not exist, so use an absolute
path or `Path.cwd()`:

```python
sys.path.insert(0, str(Path.cwd() / "project"))
```

### `FileNotFoundError: [Errno 2] No such file or directory: 'sample_data/orders.csv'`

You are in the wrong directory. This is the single most common
Workbench failure, and it is the reason the chapter insists on absolute
paths.

```python
from pathlib import Path
import os

print("cwd:", os.getcwd())
print("course root exists:", Path("/home/jupyter/workbench/course").exists())
```

The fix is to `os.chdir` once, at the top of the notebook:

```python
os.chdir("/home/jupyter/workbench/course")
```

### `RuntimeError: The --runner flag was not specified`

Beam did not know which runner to use, or the flag never reached it.

```text
RuntimeError: The --runner flag was not specified
```

In a script, the flag works:

```bash
python my_pipeline.py --runner=PrismRunner
```

In a notebook it does not, because `sys.argv` belongs to the kernel.
Construct the options explicitly:

```python
options = PipelineOptions(["--runner=PrismRunner"])
with beam.Pipeline(options=options) as pipeline:
    ...
```

And be aware of what the names resolve to in Beam 2.77:

| You write | You get |
|---|---|
| `--runner=DirectRunner` | `SwitchingDirectRunner` → Prism when supported |
| `--runner=BundleBasedDirectRunner` | the classic pure-Python runner, always |
| `--runner=PrismRunner` | Prism, always |
| `--runner=SwitchingDirectRunner` | the switching behaviour, explicitly |

### `KeyError: 'status'` while running 'KeepCompleted'

The status filter is running *after* the aggregation, so the rows it
sees are summary rows, not orders. A summary row has `region`,
`order_count` and `revenue_eur` — no `status`.

```text
KeyError: 'status' [while running 'KeepCompleted/Map']
```

The fix is ordering: filter first, aggregate second.

```text
| "ParseOrders" >> beam.ParDo(ParseOrderFn())
| "KeepCompleted" >> beam.Filter(lambda o: o["status"] == "complete")
| "KeyByRegion" >> beam.Map(lambda o: (o["region"], o))
| "Aggregate" >> beam.CombinePerKey(RevenueByRegionFn())
```

This is a good example of a class of bug that the cross-validation
step catches *before* it reaches a cluster, because the reference
implementation has the filter in one unambiguous place.

### `AssertionError` in `test_beam_summary_matches_reference`

The two implementations disagree. The assertion output names the
region:

```text
E       assert {'order_count': 515.0, 'revenue_eur': 197809.36} == {
E              'order_count': 318.0, 'revenue_eur': 113592.19}
```

Read it as a question. Is the *reference* wrong, or is the *pipeline*
wrong? In this case the count is larger, which means the pipeline is
filtering less than it should — the status filter is missing, or
running in the wrong place.

The reference implementation is usually right, because it is ten lines
of plain Python that a human can read. But it is not always: if you
just changed the reference's `statuses` argument, the reference is the
one that is wrong. Check which side you changed last.

### `apache_beam.io.filesystem.BeamIOError: Match operation failed with exceptions {...}`

The path is wrong or the credentials are not. See Chapter 3.4 for the
full diagnosis table; the short version is that `Invalid bucket name`
means the path and `does not have ... access` means the credentials.

On a Workbench instance the credentials are the service account's, so
the fix is usually to grant the *service account* the missing role:

```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT" \
  --role="roles/storage.objectViewer"
```

### `ValueError: Invalid GCS location: None. ... FILE_LOADS method requires a GCS location`

The BigQuery sink has nowhere to stage its files. Set
`--temp_location` on the runner:

```bash
--temp_location=gs://YOUR_BUCKET/temp
```

or set `custom_gcs_temp_location` in the sink. Chapter 3.4 covers this
in detail, including why a local path does not work.

### `apache_beam.io.gcp.bigquery.BigQueryTableNotFoundException` or `403 Permission denied`

The service account on the Workbench instance does not have the
BigQuery permissions. Check what it actually has:

```bash
gcloud projects get-iam-policy YOUR_PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:YOUR_SERVICE_ACCOUNT" \
  --format="table(bindings.role)"
```

The role you need for a `WriteToBigQuery` sink is
`roles/bigquery.dataEditor`, plus `roles/bigquery.jobUser` for the
load job that `FILE_LOADS` creates.

---

## 💡 Production Notes

### The cost of an idle Workbench instance

A Workbench instance that is stopped costs you disk but no CPU. A
`e2-standard-4` with a 100 GB disk left running for a month costs
roughly the disk plus 720 hours of a 4-vCPU machine — comfortably four
figures, for an environment nobody used. The default 180-minute idle
shutdown exists to stop that, and it is worth understanding the shape
of the trap: the instance stops, so it looks handled. But:

- **Disk charges continue while stopped.** A 100 GB disk at standard
  persistent disk pricing is a few tens of dollars a month, per
  instance, forever.
- **Scheduled notebook executions keep running** while the instance is
  stopped. "It shut down" does not mean "it stopped working".
- **The default is 180 minutes.** Long enough that a laptop closed
  overnight means eight hours of charges.

If you spin up several instances while learning, shut them down
explicitly when you are done, and delete the ones you are not using:

```bash
gcloud workbench instances delete beam-course --location=us-central1-a
```

Deleting removes the disk. Stopping does not.

### The working-directory trap, and how it costs real money

The most expensive version of "the working directory is not what you
thought" is this: you develop in a notebook with a relative path,
you deploy to Dataflow, and the job fails on a worker because
`sample_data/orders.csv` does not exist in the worker's sandbox.

The failure is not subtle on Dataflow — it fails in the first minute,
with a `FileNotFoundError` naming the path. The expensive version is
different: the job *succeeds* but reads the wrong file, because a
relative path in the worker sandbox happened to resolve to a
directory that had a file with the right name in it. That is rare, and
it is catastrophic, and it is entirely preventable.

**Rule: no bare relative paths in a pipeline that will run on a
cluster.** Derive every path from a root constant. If the path is
`gs://`, the cluster and the notebook agree and the problem cannot
happen.

### Why the reference implementation pays for itself

The pure twin is one function and about twenty lines. What it buys:

- **A fast test.** The reference test runs in microseconds with no
  runner. A pipeline test that needs a cluster is a test nobody runs
  before pushing.
- **A specification.** When a new engineer asks "what counts as
  revenue?", the answer is a function they can read, not a `CombineFn`
  with four methods and a docstring about associativity.
- **A debugging tool.** When the pipeline produces the wrong number,
  you run the reference on the same input. If they differ, the bug is
  in the Beam half. If they agree, the bug is in the data or the
  filter — and you have just halved the search space.

The cost is keeping the two in sync. That is a real cost, and the way
to pay it is to make the cross-validation a test that fails when they
diverge. A twin that can drift is a liability, not an asset; a twin
with a test that catches the drift is the most valuable function in
the repository.

### Skew and late data: generate them, do not wait for them

`--hot-key-rate` and `--late-events` exist because the two most common
ways a Beam pipeline fails in production are both invisible in a
uniformly-random test dataset.

**Skew.** If one key receives 50% of the records, the `CombinePerKey`
for that key becomes a serial bottleneck. On 4 workers, three sit idle
while the fourth does half the work. The symptom is a job that takes
5× longer than expected and shows one hot worker in the Dataflow
console. The mitigation is to split the hot key into sub-keys before
combining, then merge the results — but you will only think to do that
if you have *seen* the skew.

**Late data.** Events that arrive after their window has closed are
dropped by default, or held until the watermark advances past them. The
symptom is a total that is slightly too low and a number that
*changes* between reruns, which is worse than a number that is
consistently too low because at least the consistent one looks
deliberate.

Both flags cost nothing to use and both change the shape of the
exercise. Run the pipeline once with each, and once with neither, and
compare the outputs.

### The order of writing, revisited

The explore → codify workflow is not a style preference. It is a cost
argument:

| If you write the pipeline first | Cost of being wrong |
|---|---|
| Wrong about the data shape | A failed job, a log dive, a re-run |
| Wrong about the business rule | A *successful* job with wrong numbers, found days later |
| Wrong about the combiner's associativity | A job that passes on small data and fails on large data |

The third is the one that bites. A non-associative combiner — one that
rounds inside `add_input`, say — produces a different answer depending
on how the data was sharded. On the 5,000-row sample it looks fine,
because the whole dataset fits in one bundle. On 50 million rows spread
across 200 workers, the rounding error accumulates and the totals
drift. The cross-validation against a pure reference catches this
*if* you run the reference on a dataset large enough to shard. Which
is why `--orders 50000` is worth running before you believe a
combiner.

### What to do at 3am

If a Workbench-based pipeline fails in production, the debugging order
that actually helps:

1. **Check the service account, not your own permissions.** The job
   runs as the service account. If it worked yesterday and fails today,
   and you changed nothing in the code, the service account's roles
   changed, or the bucket policy changed.
2. **Check the input.** A `ReadFromText` on a GCS path that matches
   nothing produces "no files found", not a clear "the upstream job
   did not run". Compare the object count in the bucket against what
   the upstream job should have written.
3. **Reproduce locally against the same data.** Download a shard, run
   it through the pure reference, and see whether the reference agrees
   with the job. If the reference is also wrong, the data is wrong and
   you have found it in minutes rather than hours.
4. **Suspect the working directory last**, but not never. On Dataflow
   it is a local path, and a local path that happens to resolve is
   worse than one that does not.

---

## 🔑 Key Takeaways

- **Cloud Workbench is a persistent, VPC-connected Jupyter VM with a
  service account attached.** The service account is the point: the
  pipeline's identity in development is the identity it will have in
  production.
- **Workbench for production-adjacent work, Colab for learning.** The
  dividing line is whether the pipeline needs your network and your
  IAM, not which tool has a nicer UI.
- **Idle shutdown stops the VM, not the disk.** A stopped instance
  incurs no CPU charges but still incurs disk charges. Delete instances
  you are not using.
- **The explore → codify workflow is a cost argument.** Exploring
  first is minutes of pandas; exploring last is a failed job and a log
  dive. The reference implementation first is a specification, a test,
  and a debugging tool.
- **The reference implementation in `project/transforms.py` is not
  duplication — it is the specification.** `build_revenue_summary` and
  `RevenueByRegionFn` are the same logic in two languages, and the
  cross-validation is what keeps them honest.
- **Parse failures and validation failures are different problems.**
  `try_parse_order_line` answers "is this the right shape?";
  `is_valid_order` answers "is this a row we will count?". The
  malformed sample file exists to keep both paths exercised.
- **Never write a bare relative path in a pipeline.** Derive every path
  from a root constant, and construct `PipelineOptions` explicitly —
  a notebook's `sys.argv` is not your shell's.
- **Cross-validate against a dataset large enough to shard.** A
  non-associative combiner looks correct on 5,000 rows and drifts on
  50 million.

---

## 📚 Practice Exercises

1. **Build the dataset and verify determinism.** Regenerate
   `sample_data/` into a new directory with
   `--orders 50000 --events 200000`, and diff it against the original
   with `diff -r`. Explain, in terms of the `SEED` constant in
   `resources/sample_data.py`, why the *original* directory and the new
   one differ in size but are each internally reproducible. Then
   regenerate the new one a second time and diff those two — they
   should be identical.

   *Expected answer:* the first diff reports differences, because the
   row counts differ. The second diff reports no differences, because
   `generate_orders` and `generate_events` are called with
   `random.Random(SEED)` and `random.Random(SEED + 1)`, and both
   generators are deterministic given their seed and their arguments.

2. **Break the reference implementation in three ways and predict the
   damage.** In a copy of `work/reference_summary.py`, make each of
   these changes and, *before running anything*, write down what you
   expect the output to be:

   a. Move the `status != "complete"` check to *after* the accumulation
   b. Change `normalise_currency(float(row["amount"]), row["currency"])`
      to use `float(row["amount"])` with no conversion
   c. Remove the `round(bucket["revenue_eur"], 2)` at the end

   Then run each and compare against your prediction. The third one is
   the interesting case: without the final rounding, the sum of
   per-order rounded amounts is not the same as the rounded sum of
   unrounded amounts, and the difference shows up in the cents. Say
   which of the three a cross-validation against the Beam pipeline
   would catch, and which it might not.

   *Expected answer:* (a) is caught immediately — the counts jump to
   about 5,000 per region. (b) is caught — the revenues change by
   whatever the currency mix implies, and the region with the most
   non-EUR orders changes most. (c) is the subtle one: it is caught
   only if the two implementations happen to differ in the rounding,
   which they will, but the difference is a few cents, not a
   percentage. This is the same class of bug as a non-associative
   combiner: small, growing with scale, and invisible in a
   single-bundle test.

3. **Add a third cross-validation target.** The course's
   `project/tests/test_pipelines.py` already compares the Beam
   pipeline against the reference. Add a *third* implementation —
   a pandas version using `groupby` — and assert all three agree.

   ```python
import pandas as pd

orders = pd.read_csv("sample_data/orders.csv")
orders = orders[orders["status"] == "complete"]
orders["revenue_eur"] = orders["amount"] * orders["currency"].map(RATES)
pandas_summary = orders.groupby("region").agg(
    order_count=("order_id", "count"),
    revenue_eur=("revenue_eur", "sum"),
)
   ```

   Watch out for two things: pandas `sum` does not round, and pandas
   `groupby` does not drop rows with `NaN` keys the way `CombinePerKey`
   might. Report which of the two differences you hit first.

   *Expected answer:* the pandas sum is an unrounded float while the
   reference rounds to two decimals, so the comparison needs a
   tolerance or a rounding step on the pandas side. This is a real
   difference in semantics, not a bug in either implementation, and it
   is worth understanding that pandas `groupby` drops rows whose group
   key is `NaN` by default (`dropna=True`) whereas a `CombinePerKey`
   groups them under a `None` key.

4. **Measure what skew does.** Generate a skewed dataset and time the
   pipeline against the uniform one:

   ```bash
   python resources/sample_data.py --output-dir ./sample_data_skew --hot-key-rate 0.5
   ```

   Run the cross-validation script against both directories. Then
   change the key from `region` to `customer_id` and run it again.
   Write down the runtime and the output for all four combinations, and
   explain what you see. The expected answer is that keying by
   `customer_id` on the skewed dataset is dramatically slower, because
   one key now receives half of all the records and its
   `CombinePerKey` becomes a serial bottleneck.

5. **Add the malformed rows to the main dataset and watch the counts
   move.** Concatenate `malformed_orders.csv` into `orders.csv`,
   skipping both headers, and re-run the cross-validation. The
   reference and the Beam version should *still* agree — but the
   counts will be unchanged, because the malformed rows are all
   rejected. Then remove the `is_valid_order` check from the reference
   and re-run: the reference will now include the `UNKNOWN_REGION` row
   in a region of its own, and the two will disagree.

   *Expected answer:* the malformed rows are all rejected, so the
   counts do not change. Removing `is_valid_order` admits the
   `UNKNOWN_REGION` row, creating a fifth region with one order, and
   the cross-validation fails on that region. This demonstrates the
   difference between the parse check and the validation check: the
   parse check alone is not enough to keep the output clean.

6. **Write the Workbench setup as a script.** The commands in Step 8
   are for a human to paste. Write `work/create_workbench.sh` that
   takes the project, location, machine type, service account, network
   and subnet as arguments, creates the instance, and sets the idle
   timeout. Make it idempotent: if the instance already exists, update
   it rather than failing.

   *Expected answer:* check with
   `gcloud workbench instances describe` first, and branch on the exit
   code; then call `gcloud workbench instances create` or
   `gcloud workbench instances update` accordingly, followed by the
   `--metadata=idle-timeout-seconds=...` update. The two commands are
   not interchangeable — `create` fails if the instance exists, and
   `update` fails if it does not.

---

## 📖 Further Reading

- Google Cloud Workbench overview —
  https://docs.cloud.google.com/vertex-ai/docs/workbench
- Create a Workbench instance —
  https://docs.cloud.google.com/gemini-enterprise-agent-platform/notebooks/workbench/instances/create
- Workbench idle shutdown —
  https://docs.cloud.google.com/gemini-enterprise-agent-platform/notebooks/workbench/instances/idle-shutdown
- `gcloud workbench instances create` reference —
  https://docs.cloud.google.com/sdk/gcloud/reference/workbench/instances/create
- Apache Beam: your first pipeline —
  https://beam.apache.org/documentation/sdks/python/your-first-pipeline/
- Apache Beam: fundamentals — combining collections —
  https://beam.apache.org/documentation/glossary/combinefn/
- Apache Beam: Python SDK reference — `PipelineOptions` —
  https://beam.apache.org/documentation/_modules/apache_beam/options/pipeline_options.html
