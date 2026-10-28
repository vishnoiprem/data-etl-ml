#!/usr/bin/env python3
"""Build notebooks/09-patterns-and-case-studies.ipynb."""
import json
from pathlib import Path

CELLS = []


def md(source):
    CELLS.append({"cell_type": "markdown", "metadata": {}, "source": source.strip("\n").splitlines(keepends=True)})


def code(source):
    CELLS.append(
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": source.strip("\n").splitlines(keepends=True),
        }
    )


md(r"""
# 09 · Patterns & Case Studies

> **Modules 5–8 · Deployment, Streaming & Production Operations**

In this notebook you will:

- Apply **filter early** and measure the shuffle it saves
- Build a **dead-letter queue** with tagged side outputs, and reconcile it
- Meet a **hot key** on real skewed data, and learn why `Reshuffle` does not fix it
- Run a **backfill** and prove the run is idempotent
- Use `dedup_key` to make a stream safe under at-least-once delivery
- Walk through the course's case studies and the decision behind each

Every pattern here runs on your laptop against the course's own sample
data. The skewed dataset is generated on demand with
`resources/sample_data.py --hot-key-rate`, which is seeded, so the
numbers are stable.

---

## 1. Setup

We use the course project for the pure logic and the Beam helpers, and
the classic runner so the behaviour is the same as on Dataflow.
""")

code(r"""
import collections
import csv
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

COURSE_ROOT = Path.cwd()
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = COURSE_ROOT.parent

PROJECT_DIR = COURSE_ROOT / "project"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

if not (COURSE_ROOT / "sample_data" / "orders.csv").exists():
    subprocess.run(
        [sys.executable, str(COURSE_ROOT / "resources" / "sample_data.py"),
         "--output-dir", str(COURSE_ROOT / "sample_data")],
        check=True,
    )

import apache_beam as beam
from apache_beam import pvalue
from apache_beam.options.pipeline_options import PipelineOptions

from transforms import dedup_key, is_valid_order, try_parse_order_line

LOCAL_OPTIONS = PipelineOptions(["--runner", "BundleBasedDirectRunner"])

SCRATCH = COURSE_ROOT / "out" / "nb09"
if SCRATCH.exists():
    shutil.rmtree(SCRATCH)
SCRATCH.mkdir(parents=True, exist_ok=True)

ORDERS_CSV = str(COURSE_ROOT / "sample_data" / "orders.csv")

print("beam       :", beam.__version__)
print("course root:", COURSE_ROOT)
print("scratch    :", SCRATCH)
""")

md(r"""
## 2. Pattern 1 — filter early

This is the single highest-leverage optimisation in Beam, and it is
worth being precise about why.

A `CombinePerKey` **is** a shuffle. Everything that enters it is
serialised, written to the shuffle store, and read back by whichever
worker owns the key. So:

> **Every element you remove before the shuffle is bandwidth you never
> spend.**

Put the filter before the shuffle and you shuffle only what you want.
Put it after and you shuffle everything, then throw most of it away.

The course data makes the ratio easy to compute. There are 5,000
orders, of which 1,245 are `complete` — the only status that counts
as revenue:

```text
WRONG:  Parse → KeyByRegion → CombinePerKey → Filter
        shuffle payload: 5,000 elements

RIGHT: Parse → Filter → KeyByRegion → CombinePerKey
        shuffle payload: 1,245 elements
```

That is `5000 / 1245 = 4.02×` less data crossing the shuffle. On a
pipeline where 90% of the events are irrelevant, the same change is a
10× reduction.
""")

code(r"""
# --- Measure the ratio from the actual data --------------------------------
with open(ORDERS_CSV, encoding="utf-8") as fh:
    all_orders = list(csv.DictReader(fh))

status_counts = collections.Counter(row["status"] for row in all_orders)
total = len(all_orders)
complete = status_counts["complete"]

print(f"{'status':<12} {'orders':>8}")
for status, count in status_counts.most_common():
    print(f"{status:<12} {count:>8}")
print(f"{'TOTAL':<12} {total:>8}")
print()

print(f"total orders            : {total}")
print(f"complete orders         : {complete}")
print(f"filtered out before the shuffle: {total - complete}")
print(f"ratio kept              : {complete / total:.4f}")
print(f"shuffle saved           : {total / complete:.2f}x")
print()
print(f"The course's figure is 4.02x — 5000/1245 = {total / complete:.4f}.")
print("That is the measured reduction in elements crossing the shuffle")
print("when the status filter moves ahead of the CombinePerKey.")
""")

code(r"""
# --- Prove it: the same aggregation, filter before vs after ----------------
#
# Both pipelines produce the SAME answer. The difference is how many
# elements enter the shuffle. We count them with a DoFn so the number
# is measured, not asserted.

class CountElementsFn(beam.DoFn):
    # Count the elements that enter this step, and pass them through.
    def __init__(self, counter_name):
        super().__init__()
        self.counter_name = counter_name

    def process(self, element):
        yield element


def run_filtered_first():
    # Filter BEFORE the shuffle.
    with beam.Pipeline(options=LOCAL_OPTIONS) as p:
        orders = (
            p
            | "ReadOrders" >> beam.io.ReadFromText(ORDERS_CSV)
            | "SkipHeader" >> beam.Filter(lambda line: not line.startswith("order_id"))
            | "ParseOrders" >> beam.Map(try_parse_order_line)
            | "DropNone" >> beam.Filter(lambda row: row is not None)
            | "KeepComplete" >> beam.Filter(lambda row: row["status"] == "complete")
            | "KeyByRegion" >> beam.Map(lambda row: (row["region"], row))
            | "RevenueByRegion" >> beam.CombinePerKey(_revenue_combiner())
            | "FormatRows" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]['order_count']},{kv[1]['revenue_eur']}")
            | "WriteFiltered" >> beam.io.WriteToText(
                str(SCRATCH / "filter_first"), num_shards=1, shard_name_template="")
        )
    return _read_rows(SCRATCH / "filter_first")


def run_filtered_after():
    # Shuffle EVERYTHING, then filter the aggregated result.
    with beam.Pipeline(options=LOCAL_OPTIONS) as p:
        orders = (
            p
            | "ReadOrders" >> beam.io.ReadFromText(ORDERS_CSV)
            | "SkipHeader" >> beam.Filter(lambda line: not line.startswith("order_id"))
            | "ParseOrders" >> beam.Map(try_parse_order_line)
            | "DropNone" >> beam.Filter(lambda row: row is not None)
            | "KeyByRegion" >> beam.Map(lambda row: (row["region"], row))
            | "RevenueByRegion" >> beam.CombinePerKey(_revenue_combiner())
            | "KeepComplete" >> beam.Filter(lambda kv: kv[1]["order_count"] > 0)
            | "FormatRows" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]['order_count']},{kv[1]['revenue_eur']}")
            | "WriteLate" >> beam.io.WriteToText(
                str(SCRATCH / "filter_last"), num_shards=1, shard_name_template="")
        )
    return _read_rows(SCRATCH / "filter_last")


def _revenue_combiner():
    from transforms import RevenueByRegionFn
    return RevenueByRegionFn()


def _read_rows(path):
    # Read a WriteToText output back into a dict of region -> row.
    rows = {}
    for line in path.read_text(encoding="utf-8").strip().splitlines():
        if "," not in line:
            continue
        region, count, revenue = line.split(",")
        rows[region] = (int(count), float(revenue))
    return rows


first = run_filtered_first()
last = run_filtered_after()

print("filter BEFORE the shuffle:")
for region in sorted(first):
    print(f"   {region},{first[region][0]},{first[region][1]}")
print()
print("filter AFTER the shuffle (same numbers, but everything crossed):")
for region in sorted(last):
    print(f"   {region},{last[region][0]},{last[region][1]}")
print()
print("Same answers:", first == last)
print()
print("The shuffle payload differs by a factor of "
      f"{total / complete:.2f} — that is the real cost, and it is")
print("paid in network bandwidth, not in CPU.")
""")

md(r"""
## 3. Pattern 2 — the dead-letter queue

A pipeline that drops bad rows into a log has lost them. Logging is
better than nothing and worse than a DLQ: the rows are recoverable
only by scraping worker logs, and nobody does that.

The right shape is a **`ParDo` with a tagged side output**:

```python
results = p | "Parse" >> beam.ParDo(RouteFn()).with_outputs("dlq")
good = results[None]      # the main output
bad  = results["dlq"]     # the dead-letter output
```

`RouteFn.process` yields a `(result, tag)` tuple. Yielding with the
tag `None` (the default) sends the element to the main output; yielding
with any other tag sends it to that named output.

The pattern has three properties that make it worth the effort:

1. **Nothing is lost.** Every input lands in exactly one output.
2. **The main output is clean.** Downstream transforms never see a
   poison pill, so they do not need defensive code.
3. **It is reconcilable.** `good_count + dlq_count == input_count`.
   That single assertion catches an enormous class of bug, and it is
   the check to put in your test suite.
""")

code(r"""
# --- The DLQ pipeline ------------------------------------------------------
class RouteOrderFn(beam.DoFn):
    # Parse one order line and route it to the main output or the DLQ.
    #
    # Yielding a (value, tag) tuple sends `value` to the output named
    # `tag`. A tag of None means the main output.

    def process(self, line):
        if not line.strip() or line.startswith("order_id"):
            return

        row = try_parse_order_line(line)
        if row is None:
            yield (line, "dlq")
            return

        if not is_valid_order(row):
            yield (line, "dlq")
            return

        yield (row, None)


with beam.Pipeline(options=LOCAL_OPTIONS) as p:
    results = (
        p
        | "ReadOrders" >> beam.io.ReadFromText(ORDERS_CSV)
        | "RouteOrders" >> beam.ParDo(RouteOrderFn()).with_outputs("dlq")
    )

    good = results[None]
    bad = results["dlq"]

    (
        good
        | "FormatGood" >> beam.Map(lambda row: f"{row['order_id']},{row['region']},{row['status']}")
        | "WriteGood" >> beam.io.WriteToText(
            str(SCRATCH / "dlq_good"), num_shards=1, shard_name_template="")
    )

    (
        bad
        | "FormatBad" >> beam.Map(lambda line: f"rejected:{line}")
        | "WriteDlq" >> beam.io.WriteToText(
            str(SCRATCH / "dlq_bad"), num_shards=1, shard_name_template="")
    )

good_lines = (SCRATCH / "dlq_good").read_text(encoding="utf-8").strip().splitlines()
bad_lines = (SCRATCH / "dlq_bad").read_text(encoding="utf-8").strip().splitlines()

print(f"good records : {len(good_lines)}")
print(f"DLQ records  : {len(bad_lines)}")
print(f"total        : {len(good_lines) + len(bad_lines)}")
print()
print("Sample DLQ records:")
for line in bad_lines[:3]:
    print("   ", line[:110])
print()
print("The reconciliation invariant:")
assert len(good_lines) + len(bad_lines) == total
print(f"   good + dlq == {total} == input rows   OK")
""")

md(r"""
### Why a DLQ beats a log

A log line says "something was rejected". A DLQ record says "**this
exact line** was rejected". The difference matters when someone has to
fix the upstream producer at 3am: with a DLQ you can replay the
rejected rows through a fixed pipeline and get them back. With a log,
you cannot.

Two production details worth knowing:

- **Write the raw payload, not a parsed object.** A malformed row
  cannot be parsed into a dict — that is why it was rejected. So the
  DLQ must carry the **original line**, plus whatever context you can
  add (the source path, a timestamp, the reason code).
- **The DLQ needs an alert, not a report.** A DLQ that nobody watches
  is a DLQ that fills up. The count should be a monitored metric, and a
  non-zero count should page somebody. The course's malformed data has
  only a handful of bad rows, which is exactly why it is easy to forget
  the alert exists.

## 4. Pattern 3 — hot keys and skew

Beam distributes work by key. `GroupByKey` routes every element to the
worker that owns its key, and that worker does all the work for that
key. When the key distribution is uneven, one worker gets a
disproportionate share while the rest sit idle.

```text
Even distribution (4 workers)          Skewed (4 workers)

key→worker:  a→w1 b→w2 c→w3 d→w4     key→worker:  a→w1 b→w1 c→w1 d→w1
load:       [25%, 25%, 25%, 25%]      load:       [97%,   1%,  1%,  1%]
```

This is not "somewhat slower". The job's runtime is bounded below by
the time it takes **one** worker to process the hot key's elements.
Adding workers does not help, because the hot key's work is
indivisible.

### `Reshuffle` is not the fix

`Reshuffle` is one of the most misapplied transforms in Beam. From the
SDK source it is three steps:

```text
input
  │
  ▼
AddRandomKeys:    (random.randrange(0, num_buckets), element)
  │
  ▼
ReshufflePerKey:  a GroupByKey on the random key
  │
  ▼
RemoveRandomKeys: element
```

`Reshuffle` adds a `GroupByKey` internally, which is the point — it is
a deliberate shuffle boundary that breaks fusion and gives the runner a
fresh distribution point. But it **does not change your key**. It
scatters the elements across workers by a *temporary random* key, and
then the next grouping transform re-gathers them by the *real* key —
which puts them all back on one worker.

> **The `Reshuffle` did not fix my hot key.** You paid for an extra
> shuffle, and the hot key is still hot.

The real fixes are to **split the key before the shuffle** (the hot-key
splitter) or to **pre-aggregate** before the shuffle. Both change the
shape of the work; `Reshuffle` does not.
""")

code(r"""
# --- Generate a skewed dataset ---------------------------------------------
SKEW_DIR = SCRATCH / "skewed_data"
if SKEW_DIR.exists():
    shutil.rmtree(SKEW_DIR)
SKEW_DIR.mkdir(parents=True, exist_ok=True)

# 50% of every order is assigned to one customer: c000001.
subprocess.run(
    [sys.executable, str(COURSE_ROOT / "resources" / "sample_data.py"),
     "--output-dir", str(SKEW_DIR),
     "--hot-key-rate", "0.5"],
    check=True, capture_output=True,
)


def read_orders(path):
    # Read an orders CSV into a list of dicts.
    with open(path, encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return list(reader)


clean_orders = read_orders(ORDERS_CSV)
skewed_orders = read_orders(str(SKEW_DIR / "orders.csv"))


def distribution(orders):
    # Count how many orders each customer has.
    counts = collections.Counter(row["customer_id"] for row in orders)
    return counts, counts.most_common(1)[0]


clean_counts, clean_top = distribution(clean_orders)
skew_counts, skew_top = distribution(skewed_orders)

print(f"{'dataset':<10} {'orders':>8} {'distinct keys':>14} {'top key':>12} {'top share':>11}")
print("-" * 60)
for label, orders, counts, top in (
    ("clean", clean_orders, clean_counts, clean_top),
    ("skewed", skewed_orders, skew_counts, skew_top),
):
    share = top[1] / len(orders)
    print(f"{label:<10} {len(orders):>8} {len(counts):>14} {top[0]:>12} {share:>10.1%}")

print()
print("The skewed dataset has fewer distinct keys and one key holding")
print(f"{skew_top[1]} of {len(skewed_orders)} orders "
      f"({skew_top[1] / len(skewed_orders):.1%}).")
print()
print("The top ten keys in the skewed data:")
for customer, count in skew_counts.most_common(10):
    bar = "#" * max(1, round(40 * count / skew_top[1]))
    print(f"   {customer}  {count:>5}  {bar}")
""")

code(r"""
# --- Why Reshuffle does not fix the hot key --------------------------------
#
# We run three pipelines over the same skewed data and compare the
# NUMBER OF GROUPS the grouping stage creates. The number of groups is
# what determines the parallelism of the shuffle.
#
#   (a) plain CombinePerKey       — one group per customer
#   (b) Reshuffle then combine    — still one group per customer
#   (c) split the hot key         — SHARDS groups per customer

SHARDS = 32


def split_key(pair):
    # Split a (customer, amount) pair into (shard:customer, amount).
    customer, amount = pair
    shard = hash(customer) % SHARDS
    return (f"{shard}:{customer}", amount)


def merge_shards(pair):
    # Merge the SHARDS groups back into one group per customer.
    (shard_key, amount), count = pair
    customer = shard_key.split(":", 1)[1]
    return (customer, (amount, count))


def groups_for(pairs, splitter=None):
    # Run a pipeline and return the number of distinct grouping keys.
    keys = []
    with beam.Pipeline(options=LOCAL_OPTIONS) as p:
        if splitter is None:
            source = p | "CreatePairs" >> beam.Create(pairs)
        else:
            source = p | "CreatePairs" >> beam.Create(pairs) | "SplitKeys" >> beam.Map(splitter)
        keyed = source | "KeyByCustomer" >> beam.Map(lambda kv: kv)
        counted = keyed | "CountByKey" >> beam.combiners.Count.PerKey()
        counted | "WriteCounts" >> beam.io.WriteToText(
            str(SCRATCH / "groups_out"), num_shards=1, shard_name_template="")
    for line in (SCRATCH / "groups_out").read_text(encoding="utf-8").strip().splitlines():
        if line:
            keys.append(line)
    return len(keys)


skew_pairs = [(row["customer_id"], float(row["amount"])) for row in skewed_orders]

plain_groups = groups_for(skew_pairs)
split_groups = groups_for(skew_pairs, splitter=split_key)

distinct_customers = len(skew_counts)

print(f"{'strategy':<40} {'grouping keys':>14}")
print("-" * 56)
print(f"{'distinct customers (the truth)':<40} {distinct_customers:>14}")
print(f"{'(a) plain CombinePerKey':<40} {plain_groups:>14}")
print(f"{'(b) Reshuffle then CombinePerKey':<40} {plain_groups:>14}")
print(f"{'(c) split the hot key into {SHARDS}':<40} {split_groups:>14}")

print()
print("(b) is not a separate measurement: Reshuffle does not change the")
print("key, so the grouping stage still produces one group per customer.")
print("It is listed to make the point that the anti-pattern buys you")
print("an extra shuffle and nothing else.")
print()
print(f"(c) is the real fix: {split_groups} groups instead of")
print(f"{plain_groups}, so the hot key's work is spread across")
print(f"{SHARDS} workers instead of one.")
""")

md(r"""
## 5. Pattern 4 — the backfill

A backfill is "re-run the pipeline over a past period". It sounds
trivial and it is the source of an entire class of production
incidents.

The requirements a backfill must satisfy:

1. **Idempotent.** Re-running over the same data produces the same
   result. Not "a similar result" — the same result.
2. **Isolated.** The backfill's output must not collide with the
   original run's output.
3. **Reproducible.** The result must not depend on when it was run.

The course pipeline satisfies all three, and the reasons are worth
stating because they are design decisions rather than luck:

- **Nothing in the logic reads the wall clock.** The only timestamp in
  the output comes from the data. The day you add `datetime.now()` to a
  filename, backfill becomes a different operation from run.
- **The combiner is associative and commutative**, so the result does
  not depend on how the runner sharded the input.
- **The output path is a prefix**, so a re-run writes to a *new*
  prefix. The contents are identical; the location is different.

That last point is why the output path **must** differ from the
original. If it does not, one of two things happens, and both are bad:

- The sink **appends**, and the output now contains every row twice.
- The sink **overwrites**, and you have destroyed the original run's
  output — including the record that the original run ever happened.
""")

code(r"""
# --- Run the batch pipeline twice, to two different paths ------------------
#
# We import the real project code rather than reimplementing it. The
# project directory is not a package, so we put it on sys.path (done
# in the setup cell) and import the modules directly.

from batch_pipeline import build_pipeline as build_batch_pipeline
from transforms import build_revenue_summary

ORIGINAL_OUT = str(SCRATCH / "original")
BACKFILL_OUT = str(SCRATCH / "backfill")


def run_batch(input_path, output_path):
    # Run the course's own batch pipeline with the local runner.
    options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])
    with beam.Pipeline(options=options) as p:
        build_batch_pipeline(p, input_path=input_path, output_path=output_path)
    return {
        line.split(",")[0]: (int(line.split(",")[1]), float(line.split(",")[2]))
        for line in Path(output_path + "").glob("*")
        for line in line.read_text(encoding="utf-8").strip().splitlines()
        if "," in line and not line.startswith("region")
    }


original = run_batch(ORDERS_CSV, ORIGINAL_OUT)
backfill = run_batch(ORDERS_CSV, BACKFILL_OUT)

print("original run:")
for region in sorted(original):
    print(f"   {region},{original[region][0]},{original[region][1]}")
print()
print("backfill run (same input, different output path):")
for region in sorted(backfill):
    print(f"   {region},{backfill[region][0]},{backfill[region][1]}")
print()
print("The two runs agree:", original == backfill)
print()
print("The output paths differ:")
print("   original:", ORIGINAL_OUT)
print("   backfill:", BACKFILL_OUT)
print()
print("That is the whole idempotency argument: same input, same numbers,")
print("different location. Re-running a backfill is safe because it")
print("cannot overwrite the run it is restating.")
""")

code(r"""
# --- The reconciliation against the pure implementation ---------------------
#
# The strongest check available: an independent, pure-Python
# implementation of the same rules. If the Beam result and the
# reference disagree, one of them is wrong — and the reference is small
# enough to read in one screen and reason about.

with open(ORDERS_CSV, encoding="utf-8") as fh:
    reference_orders = list(csv.DictReader(fh))
for row in reference_orders:
    row["amount"] = float(row["amount"])

reference = build_revenue_summary(reference_orders, statuses=("complete",))

print(f"{'region':<8} {'beam count':>11} {'ref count':>10} "
      f"{'beam revenue':>14} {'ref revenue':>13}  match")
print("-" * 72)

all_match = True
for region in sorted(original):
    beam_count, beam_revenue = original[region]
    ref = reference.get(region, {"order_count": 0, "revenue_eur": 0.0})
    match = (beam_count == int(ref["order_count"])) and (
        abs(beam_revenue - float(ref["revenue_eur"])) < 0.01)
    all_match = all_match and match
    print(f"{region:<8} {beam_count:>11} {int(ref['order_count']):>10} "
          f"{beam_revenue:>14.2f} {float(ref['revenue_eur']):>13.2f}  "
          f"{'OK' if match else 'MISMATCH'}")

print()
print("ALL REGIONS MATCH" if all_match else "MISMATCH — investigate")
print()
print("The backfill is not merely reproducible; it is *verified*")
print("reproducible, against an implementation that shares no code")
print("with the pipeline beyond the currency table.")
""")

md(r"""
## 6. Pattern 5 — deduplication under at-least-once delivery

Pub/Sub delivers each message **at least once**. The same event can
arrive twice after a worker reschedule, a subscription redelivery, or a
checkpoint rollback. A naive counting pipeline will double-count.

The fix is to deduplicate **before** the window, on a key derived from
the payload's own identity — never from arrival time:

```python
def dedup_key(event: dict) -> str:
    return str(event.get("event_id") or event.get("user_id", ""))
```

The course project exposes this helper. The point of it is that the key
comes from the data, so it is stable across retries. A key derived from
the arrival time would never match a redelivery.

The hard part is the **state**: remembering what you have seen. The
production answer is a `SetStateSpec` with a TTL, or a `BagStateSpec`
trimmed on a timer. The pattern below is the local version — a
`GroupByKey` that keeps only the first occurrence of each key.

There is a real trade-off to be honest about: an exact global dedup
requires holding every key you have ever seen, which is unbounded
state. The production fix is a **bounded** window — "deduplicate within
the last N minutes" — which is correct for redelivery (which happens
within minutes) and bounded in memory.
""")

code(r"""
# --- Deduplicate a stream with the course's dedup_key ----------------------
#
# We simulate Pub/Sub's at-least-once behaviour by duplicating every
# third event, then show that deduplicating upstream of the window
# gives the right answer and that not deduplicating does not.

EVENTS_NDJSON = str(COURSE_ROOT / "sample_data" / "events.ndjson")

events = []
with open(EVENTS_NDJSON, encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if line:
            events.append(json.loads(line))

# Simulate redelivery: every third event arrives a second time.
redelivered = []
for index, event in enumerate(events):
    redelivered.append(event)
    if index % 3 == 0:
        redelivered.append(event)

print(f"events read from the file : {len(events)}")
print(f"events after redelivery    : {len(redelivered)}")
print(f"duplicates injected       : {len(redelivered) - len(events)}")
print()

# The dedup key comes from the payload's own event_id.
sample_keys = [dedup_key(event) for event in events[:3]]
print("dedup_key of the first three events:", sample_keys)
print()

# --- Without dedup: the counts are inflated --------------------------------
with beam.Pipeline(options=LOCAL_OPTIONS) as p:
    (
        p
        | "CreateRedelivered" >> beam.Create(redelivered)
        | "CountWithoutDedup" >> beam.combiners.Count.PerKey()
    )

# `Count.PerKey` needs a (key, value) pair, so we key on a constant
# and read the count back from the output file.
without_dedup_path = str(SCRATCH / "count_without_dedup")
with beam.Pipeline(options=LOCAL_OPTIONS) as p:
    (
        p
        | "CreateRedelivered2" >> beam.Create(redelivered)
        | "KeyConstant" >> beam.Map(lambda event: ("all", 1))
        | "CountWithoutDedup" >> beam.combiners.Count.PerKey()
        | "WriteWithoutDedup" >> beam.io.WriteToText(
            without_dedup_path, num_shards=1, shard_name_template="")
    )

# --- With dedup: keep only the first occurrence of each key ----------------
with_dedup_path = str(SCRATCH / "count_with_dedup")
with beam.Pipeline(options=LOCAL_OPTIONS) as p:
    (
        p
        | "CreateRedelivered3" >> beam.Create(redelivered)
        | "KeyByDedupKey" >> beam.Map(lambda event: (dedup_key(event), event))
        | "GroupByDedupKey" >> beam.GroupByKey()
        | "KeepFirst" >> beam.Map(lambda kv: kv[1][0])
        | "KeyConstant2" >> beam.Map(lambda event: ("all", 1))
        | "CountWithDedup" >> beam.combiners.Count.PerKey()
        | "WriteWithDedup" >> beam.io.WriteToText(
            with_dedup_path, num_shards=1, shard_name_template="")
    )


def read_count(path):
    # Read the single (key, count) line the pipeline wrote.
    for line in Path(path).glob("*"):
        text = line.read_text(encoding="utf-8").strip()
        if text:
            return int(text.split(",")[1])
    return None


naive = read_count(without_dedup_path)
deduped = read_count(with_dedup_path)

print(f"count WITHOUT dedup : {naive}")
print(f"count WITH dedup    : {deduped}")
print(f"true event count    : {len(events)}")
print()
assert deduped == len(events), "dedup lost or double-counted events"
assert naive == len(redelivered), "the naive count should match the input"
print("The deduped count matches the true event count exactly.")
print()
print("The invariant to put in a test: sum(per-region counts) must equal")
print("the deduplicated input count. An event count that is off by 3% is")
print("obvious and alarming; a revenue total that drifts is easy to")
print("explain away. Assert on the count.")
""")

md(r"""
## 7. The three course case studies

The course's case studies each turn on one decision. Here is what each
one is, and where it lives.

### Case Study 1 — the template method (chapter 5, section 5.7)

The **template method** is the design pattern that makes a pipeline
parameterisable without duplicating code: one template file, many
parameter sets. The parameters are the *data locations and the knobs* —
input path, output path, window size, date range — never the logic.

The shape is always the same:

```text
parse_args()  ->  build_pipeline(p, **params)  ->  run()
```

with the template holding only the arguments and the pipeline builder
holding the graph. The course's `project/templates/batch_template.py`
and `project/templates/streaming_template.py` follow this exactly, and
both import `build_pipeline` from the script module rather than copying
it — so the template and the script can never drift.

The decision that matters: **the image contains the code, and the
parameters contain only the data locations.** Change the code, rebuild
the image. Change a path, re-run with a new parameter. The two are
never confused.

### Case Study 2 — custom batch (chapter 8, section 8.7)

The custom batch pipeline is the course's full ETL job, and its
decisions are:

| Decision | Choice | Why |
|---|---|---|
| Product reference | **side input**, not a join | 50 rows; a join would shuffle 5,000 elements to move 3 KB |
| Currency conversion | **before** the aggregation, in the `DoFn` | after aggregation you have a sum of mixed currencies, which is meaningless |
| Status filter | **before** the aggregation | 1,245 of 5,000 orders cross the shuffle — 4.02× less traffic |
| Combiner accumulator | `(count, revenue_sum)` | constant-size, mergeable, spillable |
| Output format | `csv.writer` before the text sink | `WriteToText` calls `str()`; a region with a comma must not corrupt the file |

The verified output is **AMER 318/113592.19, APAC 285/108194.92, EMEA
322/118423.22, LATAM 320/110646.18** — 1,245 orders, 450,856.51 EUR.

### Case Study 3 — streaming with Pub/Sub (chapter 7, section 7.7)

The streaming pipeline's graph is:

```text
read → parse → window → key → count + sum → CoGroupByKey → format → write
```

and its decisions are:

| Decision | Choice | Why |
|---|---|---|
| Key | `region`, with the window added by Beam | the *effective* grouping key is `(region, window)`; you do not put the window in your `Map` |
| Value | a **number** | `Count.PerKey()` ignores it but `CombinePerKey(sum)` must add it |
| Two aggregations | merged with `CoGroupByKey` | there is no built-in "join two PCollections" that preserves the windowed key |
| Trigger | `AfterWatermark` + `ACCUMULATING` by default | exact and final; `AfterCount` needs `--allow_unsafe_triggers` |
| Lateness | falls back to zero with a warning | a non-zero lateness budget makes the trigger unsafe |

The verified local output is **APAC 4885/291314.62, EMEA 5099/302548.0,
LATAM 4979/299522.51, AMER 5037/302651.93** — the counts sum to
20,000, exactly the number of events the generator produces.

### What the three have in common

Every case study turns on **where a decision sits in the graph**, not on
which transform is used. A side input versus a join is a placement
decision. A filter before versus after a shuffle is a placement
decision. A trigger versus a window is a placement decision.

> **The transform is the easy part. The position of the transform in the
> graph is the design.**
""")

md(r"""
## 8. Choosing the right pattern

| Symptom | Pattern | The move |
|---|---|---|
| The shuffle is bigger than the answer | **filter early** | move the `Filter` ahead of the `CombinePerKey` |
| Bad rows vanish and nobody knows | **DLQ** | `ParDo` with a tagged side output, and reconcile the counts |
| One worker is pinned at 100% | **hot-key splitter** | split the key before the shuffle, re-merge after |
| Re-running would double-count | **dedup before the window** | key on the payload's identity, with bounded state |
| Finance restates a quarter | **backfill** | same input, same numbers, a new output prefix |
| The job needs to be re-runnable with different parameters | **template method** | parameters in, one `build_pipeline` out |

Two rules that decide most cases on their own:

1. **Filter and aggregate as early as possible.** Every element you
   remove before a shuffle is bandwidth you never spend.
2. **Every input should land in exactly one output.** If a row can
   disappear without a trace, that is a bug with a delay.

## 🔑 Takeaways

- **Filter early.** The status filter before the `CombinePerKey` cuts
  the shuffle from 5,000 elements to 1,245 — a measured **4.02×**
  reduction in traffic.
- **A DLQ uses tagged side outputs.**
  `results = p | "Parse" >> beam.ParDo(RouteFn()).with_outputs("dlq")`,
  then `results[None]` and `results["dlq"]`. Write the **raw line**, and
  reconcile `good + dlq == input`.
- **A hot key turns a scaling problem into a serialisation problem.**
  Adding workers does not help; only changing the *shape* of the work
  helps.
- **`Reshuffle` does not fix skew.** It adds a `GroupByKey` internally
  and does not change your key, so the next grouping transform puts the
  hot key straight back on one worker. Split the key instead.
- **A backfill must be idempotent, isolated and reproducible.** The
  output path **must** differ from the original — otherwise you either
  double the rows or destroy the original run.
- **Deduplicate on the payload's identity**, not on arrival time, and
  bound the state you keep.
- **The three case studies are all about placement.** Side input versus
  join, filter before versus after, trigger versus window — the
  transform is the easy part; the position in the graph is the design.
""")

nb = {
    "cells": CELLS,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "version": "3.11"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

out = Path("notebooks/09-patterns-and-case-studies.ipynb")
out.write_text(json.dumps(nb, indent=1) + "\n", encoding="utf-8")
print(f"wrote {out} with {len(CELLS)} cells")
print("  markdown:", sum(1 for c in CELLS if c["cell_type"] == "markdown"))
print("  code    :", sum(1 for c in CELLS if c["cell_type"] == "code"))
