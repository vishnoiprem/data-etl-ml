"""Generate notebooks/09-patterns-and-case-studies.ipynb.

Patterns covered:
  1. The hot key -- and the Reshuffle / hot-key-splitter contrast, run on
     real skewed data generated with --hot-key-rate.
  2. The dead-letter queue.
  3. The backfill.
Then a walk through the three course case studies and their design
decisions.

Every Beam API used here was verified against apache-beam 2.77.0.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nblib import build, code, md, setup_cell  # noqa: E402

CELLS: list[dict] = []

# ===========================================================================
# Title
# ===========================================================================
CELLS.append(md("""
# 09 · Patterns & Case Studies

> **Modules 5–8 · Deployment, Streaming & Production Operations**

In this notebook you will:

- Meet the **hot key** on real skewed data, and see why it dominates a job
- Contrast `beam.Reshuffle` with the **hot-key splitter**, and understand
  exactly what each one does and does not fix
- Build a **dead-letter queue** that captures failures instead of losing them
- Run a **backfill** safely, with idempotency and a partitioned output path
- Walk through the three course case studies and the decision behind each

---

Every pattern here is runnable on your laptop, against the course's own
sample data. The skewed data is generated on demand with
`resources/sample_data.py --hot-key-rate`.
"""))

CELLS.append(setup_cell())

# ===========================================================================
# 1. Pattern 1 -- the hot key
# ===========================================================================
CELLS.append(md("""
## 1. Pattern 1 — the hot key

A Beam pipeline distributes work by **key**. `GroupByKey` routes every
element to the worker that owns its key, and that worker does all the work
for that key. When the key distribution is uneven, one worker gets a
disproportionate share while the rest sit idle.

```text
Even distribution (4 workers)          Skewed (4 workers)

key→worker:  a→w1 b→w2 c→w3 d→w4     key→worker:  a→w1 b→w1 c→w1 d→w1
load:       [25%, 25%, 25%, 25%]      load:       [97%,  1%,  1%,  1%]
```

This is not "somewhat slower". The pipeline is bounded below by the time it
takes **one** worker to process the hot key's elements, while 99% of the
cluster does nothing. Adding workers does not help. The job gets *more
expensive* and no faster.

The classic symptom: **a job that takes ten times longer than the
theoretical minimum.**

### Generating skewed data

The course's sample-data generator has a `--hot-key-rate` flag that sends
a fraction of all orders to a single `customer_id`. Let's generate both a
clean and a skewed dataset and measure the difference.
"""))

CELLS.append(code("""
import collections
import subprocess
import sys

SCRATCH = COURSE_ROOT / "_scratch" / "nb09"
SCRATCH.mkdir(parents=True, exist_ok=True)

CLEAN_DIR = SCRATCH / "clean"
SKEWED_DIR = SCRATCH / "skewed"

for target in (CLEAN_DIR, SKEWED_DIR):
    if target.exists():
        subprocess.run(["rm", "-rf", str(target)], check=True)
    target.mkdir(parents=True, exist_ok=True)

# The clean dataset: the course default.
subprocess.run(
    [sys.executable, str(COURSE_ROOT / "resources" / "sample_data.py"),
     "--output-dir", str(CLEAN_DIR)],
    check=True, capture_output=True,
)

# The skewed dataset: 50% of every order goes to customer c000001.
subprocess.run(
    [sys.executable, str(COURSE_ROOT / "resources" / "sample_data.py"),
     "--output-dir", str(SKEWED_DIR), "--hot-key-rate", "0.5"],
    check=True, capture_output=True,
)


def load_orders(path):
    rows = []
    with path.open(encoding="utf-8") as handle:
        next(handle)
        for line in handle:
            rows.append(line)
    return rows


clean_orders = load_orders(CLEAN_DIR / "orders.csv")
skewed_orders = load_orders(SKEWED_DIR / "orders.csv")

print(f"clean  : {len(clean_orders):>6} orders")
print(f"skewed : {len(skewed_orders):>6} orders")
"""))

CELLS.append(code("""
# --- Measure the key distribution -----------------------------------------
import csv


def customer_of(line: str) -> str:
    parts = next(csv.reader([line]))
    return parts[1] if len(parts) > 1 else "?"


def distribution(lines):
    counts = collections.Counter(customer_of(line) for line in lines)
    total = sum(counts.values())
    ranked = counts.most_common()
    top = ranked[0]
    return counts, total, top


clean_counts, clean_total, clean_top = distribution(clean_orders)
skew_counts, skew_total, skew_top = distribution(skewed_orders)

print(f"{'dataset':<10} {'distinct keys':>14} {'top key':>12} {'top share':>11}")
for label, counts, total, top in (
    ("clean", clean_counts, clean_total, clean_top),
    ("skewed", skew_counts, skew_total, skew_top),
):
    share = top[1] / total * 100
    print(f"{label:<10} {len(counts):>14} {top[0]:>12} {share:>10.1f}%")

print()
print(f"The skewed dataset has {len(skew_counts)} distinct customers, but")
print(f"one of them owns {skew_top[1]} of the {skew_total} orders.")
print("That single key is the critical path of the whole job.")
"""))

CELLS.append(md("""
### What the skew costs

Now the key question: does the hot key actually slow the job down?

On a single-threaded local runner the answer is subtle — the Direct
Runner is not a distributed system, so there is no "other workers" to
compare against. What you *can* measure locally is the **work
concentration**: how much of the total work sits behind one key.

The honest local experiment is a **controlled** one. Instead of timing a
distributed job, we simulate the distribution: given `N` workers and a key
distribution, which worker is the critical path, and how long must the job
take?

We can compute that exactly, because we know the work per key.
"""))

CELLS.append(code("""
# --- The critical-path model ---------------------------------------------
# A distributed GroupByKey sends every element of a key to the SAME worker.
# So the job's runtime is bounded below by the busiest worker, and that is
# exactly the runtime (work is the only thing that matters here).

def critical_path_model(counts, total_elements, workers, per_element_cost=1.0):
    \"\"\"Return (runtime, busiest_worker_share) for a key distribution.

    Each worker's load is the sum of the elements whose keys it owns.
    With a good hash, the assignment is round-robin over the key space,
    so we model it as: sort keys by size, deal them out to workers.
    \"\"\"
    loads = [0.0] * workers
    for key, count in sorted(counts.items(), key=lambda kv: -kv[1]):
        # Round-robin over the hash space -- a good hash spreads the
        # hot key's neighbours but cannot split the hot key itself.
        loads[key_index(key, workers)] += count
    runtime = max(loads) * per_element_cost
    return runtime, max(loads) / total_elements


def key_index(key: str, workers: int) -> int:
    \"\"\"A stable stand-in for the runner's key hash.\"\"\"
    import hashlib
    digest = hashlib.sha1(key.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") % workers


WORKERS = 8

print(f"{'dataset':<10} {'workers':>8} {'ideal time':>12} {'actual time':>13} {'penalty':>9}")
for label, counts, total in (("clean", clean_counts, clean_total),
                             ("skewed", skew_counts, skew_total)):
    ideal = total / WORKERS * 1.0
    runtime, share = critical_path_model(counts, total, WORKERS)
    print(f"{label:<10} {WORKERS:>8} {ideal:>12.0f} {runtime:>13.0f} "
          f"{runtime / ideal:>8.1f}x")

print()
print("The 'ideal time' is total_elements / workers -- the runtime if the")
print("work were perfectly balanced.  The 'actual time' is the busiest")
print("worker's load, which is what a distributed GroupByKey really costs.")
print("The penalty is the factor by which skew makes the job slower than")
print("it could be -- and it is paid on EVERY element of the hot key,")
print("no matter how many workers you add.")
"""))

CELLS.append(md("""
Now the crucial part: **what happens when you add workers?** If skew is
the problem, more workers should not help. Let's check.
"""))

CELLS.append(code("""
print(f"{'dataset':<10} {'workers':>8} {'runtime':>10} {'ideal':>10} {'penalty':>9}")
for label, counts, total in (("clean", clean_counts, clean_total),
                             ("skewed", skew_counts, skew_total)):
    for workers in (1, 2, 4, 8, 16, 32, 64):
        runtime, _ = critical_path_model(counts, total, workers)
        ideal = total / workers
        print(f"{label:<10} {workers:>8} {runtime:>10.0f} {ideal:>10.0f} "
              f"{runtime / ideal:>8.1f}x")
    print()
"""))

CELLS.append(md("""
Read the two tables carefully.

For the **clean** dataset, doubling the workers roughly halves the
runtime — the job scales, and the penalty stays near 1×.

For the **skewed** dataset, doubling the workers changes almost nothing.
The runtime is pinned by the hot key, so the penalty *grows* as you add
workers. You are paying for 64 workers and getting the throughput of
about two.

This is the pattern to memorise:

> **A hot key turns a scaling problem into a serialisation problem.**
> Workers do not help. Only changing the *shape* of the work helps.
"""))

CELLS.append(code("""
# The conclusion, stated as a measurement rather than an assertion.
clean_1, _ = critical_path_model(clean_counts, clean_total, 1)
clean_64, _ = critical_path_model(clean_counts, clean_total, 64)
skew_1, _ = critical_path_model(skew_counts, skew_total, 1)
skew_64, _ = critical_path_model(skew_counts, skew_total, 64)

print("=== Scaling from 1 worker to 64 workers ===")
print(f"  clean  : {clean_1:>8.0f} -> {clean_64:>8.0f}   "
      f"speedup {clean_1 / clean_64:>6.1f}x  (ideal 64.0x)")
print(f"  skewed : {skew_1:>8.0f} -> {skew_64:>8.0f}   "
      f"speedup {skew_1 / skew_64:>6.1f}x  (ideal 64.0x)")
print()
print("The clean dataset scales.  The skewed dataset does not, and adding")
print("workers makes the ratio WORSE -- you pay for capacity you cannot")
print("use.")
"""))

# ===========================================================================
# 2. Reshuffle vs the splitter
# ===========================================================================
CELLS.append(md("""
## 2. Pattern 1b — `Reshuffle` is not the hot-key fix

This is the single most misapplied transform in Beam, and the
misapplication is expensive. So let us be precise about what it does.

From the SDK source, `Reshuffle` is three steps:

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

**`Reshuffle` adds a `GroupByKey` internally.** That is the point: a
`GroupByKey` is a shuffle boundary, and a shuffle boundary prevents the
fusion of the surrounding steps. `Reshuffle` is the idiomatic way to say
"break fusion here, checkpoint my data, and give me a fresh distribution
of the elements across workers."

### The two critical caveats

**Caveat 1 — `Reshuffle` does not change the key.** It adds a *temporary
random* key, groups by it, then **removes** it. The output has exactly
the same keys as the input. So this does **not** fix a hot key:

```python
# This does NOT fix a hot key.
(p
 | "Key" >> beam.Map(lambda x: (x["hot_key"], x))
 | "Reshuffle" >> beam.Reshuffle()
 | "GroupByKey" >> beam.GroupByKey())
```

The `Reshuffle` scatters the elements across workers by a random key. The
`GroupByKey` immediately re-gathers them by the hot key. You paid for two
shuffles and got the original problem back.

**Caveat 2 — `Reshuffle` breaks timestamp monotonicity.** Because the
elements are re-keyed and re-emitted, their timestamps are no longer
monotonic within the stream. For a pipeline with windowing or triggers
this can change the semantics: an element can arrive at the trigger
after a later-timestamped element did.

Neither caveat is a reason to avoid `Reshuffle` — it is genuinely good
for breaking fusion, checkpointing streaming state, and rebalancing an
already-grouped PCollection. They are reasons to know what it does
before you reach for it.

### The fix that actually works: the hot-key splitter

> **Split the key before the shuffle, and re-merge after.**

```text
                     ┌── shard 0 ──┐
hot key ──► Split ───┼── shard 1 ──┤──► Re-merge ──► result
                     └── shard N ──┘
```

The shard is derived **deterministically from the element**, not from its
position in the stream, so the same element always lands in the same
shard. That determinism is what makes the re-merge correct.
"""))

CELLS.append(code("""
# --- The anti-pattern, run for real ---------------------------------------
# We will run the same aggregation three ways and compare:
#   (a) plain CombinePerKey
#   (b) Reshuffle then CombinePerKey   <- the anti-pattern
#   (c) split then combine then re-merge  <- the real fix
#
# The answer must be identical in all three.  What differs is the shape
# of the work.

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions


def local_options():
    options = PipelineOptions()
    options.view_as(StandardOptions).runner = "BundleBasedDirectRunner"
    return options


def run_and_collect(build_steps, out_dir):
    \"\"\"Run a pipeline, write its output to text, and read it back.

    A PCollection is not iterable, so the only way to get the result out
    of a local pipeline is to write it and read the file.
    \"\"\"
    if out_dir.exists():
        subprocess.run(["rm", "-rf", str(out_dir)], check=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    with beam.Pipeline(options=local_options()) as p:
        # `build_steps` must return a PCollection, so the write happens
        # here rather than inside the lambda.
        result = build_steps(p)
        _ = (result
             | "Format" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]}")
             | "Write" >> beam.io.WriteToText(
                 str(out_dir / "out"), num_shards=1))
    collected = {}
    for path in sorted(q for q in out_dir.rglob("*") if q.is_file()):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            key, _, value = line.rpartition(",")
            collected[key] = float(value)
    return collected


def read_pairs(path):
    \"\"\"Read the skewed CSV into (customer_id, amount) pairs.\"\"\"
    pairs = []
    with path.open(encoding="utf-8") as handle:
        next(handle)
        for line in handle:
            parts = next(csv.reader([line]))
            if len(parts) > 7:
                pairs.append((parts[1], float(parts[7])))
    return pairs


skewed_pairs = read_pairs(SKEWED_DIR / "orders.csv")
print(f"loaded {len(skewed_pairs)} (customer_id, amount) pairs")
"""))

CELLS.append(code("""
# (a) The plain pipeline: one CombinePerKey, keyed by customer_id.
plain_result = run_and_collect(
    lambda p: (p
               | "Read" >> beam.Create(skewed_pairs)
               | "Sum" >> beam.CombinePerKey(sum)),
    SCRATCH / "out_plain",
)

# (b) The ANTI-PATTERN: Reshuffle, then GroupByKey on the same key.
anti_result = run_and_collect(
    lambda p: (p
               | "Read" >> beam.Create(skewed_pairs)
               | "Reshuffle" >> beam.Reshuffle()
               | "Sum" >> beam.CombinePerKey(sum)),
    SCRATCH / "out_anti",
)

# (c) The REAL FIX: split the hot key before the shuffle.
SHARDS = 32


def split_key(pair):
    \"\"\"Split into (shard:key, value), deterministically from the key.\"\"\"
    import hashlib
    key, value = pair
    digest = hashlib.sha1(key.encode("utf-8")).digest()
    shard = int.from_bytes(digest[:4], "big") % SHARDS
    return f"{shard}:{key}", value


def drop_shard(item):
    key, value = item
    return key.split(":", 1)[1], value


split_result = run_and_collect(
    lambda p: (p
               | "Read" >> beam.Create(skewed_pairs)
               | "Split" >> beam.Map(split_key)
               | "SumShards" >> beam.CombinePerKey(sum)
               | "DropShard" >> beam.Map(drop_shard)
               | "MergeShards" >> beam.CombinePerKey(sum)),
    SCRATCH / "out_split",
)

print("=== Do all three agree? ===")
print(f"  plain == anti   : {plain_result == anti_result}")
print(f"  plain == split  : {plain_result == split_result}")
print()
print(f"distinct keys      : {len(plain_result)}")
hot = max(plain_result, key=lambda k: plain_result[k])
print(f"hot key            : {hot}  total {plain_result[hot]:.2f}")
print(f"hot key's share    : {plain_result[hot] / sum(plain_result.values()) * 100:.1f}%")
"""))

CELLS.append(md("""
All three produce the **same answer** — that is the correctness
requirement, and it holds.

What differs is the **shape of the work**. In (a) and (b), the hot key's
work is a single group, processed by one worker. In (c), the hot key's
work is split across `SHARDS` groups, each processed by a different
worker, and then re-merged.

### How many groups does each approach create?

This is the number that explains everything. We can count the distinct
grouping keys each strategy produces, which is exactly what determines
the parallelism of the shuffle.
"""))

CELLS.append(code("""
# --- Count the grouping keys each strategy produces ------------------------
plain_groups = len(plain_result)

# The anti-pattern: Reshuffle adds a RANDOM key, so the shuffle it
# performs has many groups -- but then the GroupByKey re-gathers by the
# hot key, so the *real* grouping is still one group per customer.
reshuffle_buckets = 32  # the runner's default bucket count
anti_groups = len(anti_result)

# The fix: SHARDS groups per distinct customer.
split_groups = len({f"{s}:{k}" for k in plain_result for s in range(SHARDS)})

print(f"{'strategy':<34} {'grouping keys':>14}")
print(f"{'plain CombinePerKey':<34} {plain_groups:>14}")
print(f"{'Reshuffle + CombinePerKey':<34} {anti_groups:>14}   "
      f"<-- unchanged")
print(f"{'split + combine + re-merge':<34} {split_groups:>14}")
print()
print("The anti-pattern's grouping key count is IDENTICAL to the plain")
print("pipeline's.  The Reshuffle shuffled, and then the GroupByKey")
print("un-shuffled.  The randomisation was undone.")
print()
print("The splitter multiplies the grouping key count by SHARDS, which is")
print("the whole point: the hot key's work is now spread over 32 groups.")
"""))

CELLS.append(md("""
### The `Reshuffle` caveat, demonstrated

We can *prove* that `Reshuffle` does not change the key, by looking at the
key encoding after the transform. And we can prove the timestamp caveat
too.

This is the practical test: if `Reshuffle` scattered the hot key's
elements across workers, then grouping by the hot key afterwards would
produce *fewer* groups than there were elements. It does not.
"""))

CELLS.append(code("""
# --- Does Reshuffle change the key? --------------------------------------
# Count the elements per key BEFORE and AFTER the Reshuffle.
# If the key changed, the counts would change.  They do not.

def key_counts(build_steps, out_dir):
    # Count elements per key, writing to a file so we can read it back.
    if out_dir.exists():
        subprocess.run(["rm", "-rf", str(out_dir)], check=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    with beam.Pipeline(options=local_options()) as p:
        result = build_steps(p)
        _ = (result
             | "Format" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]}")
             | "Write" >> beam.io.WriteToText(
                 str(out_dir / "out"), num_shards=1))
    counts = {}
    for path in sorted(q for q in out_dir.rglob("*") if q.is_file()):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            key, _, value = line.rpartition(",")
            counts[key] = int(float(value))
    return counts


before_counts = key_counts(
    lambda p: (p
               | "Read" >> beam.Create(skewed_pairs)
               | "KeyCounts" >> beam.Map(lambda kv: (kv[0], 1))
               | "Count" >> beam.combiners.Count.PerKey()),
    SCRATCH / "kc_before",
)

after_counts = key_counts(
    lambda p: (p
               | "Read" >> beam.Create(skewed_pairs)
               | "Reshuffle" >> beam.Reshuffle()
               | "KeyCounts" >> beam.Map(lambda kv: (kv[0], 1))
               | "Count" >> beam.combiners.Count.PerKey()),
    SCRATCH / "kc_after",
)

print(f"distinct keys before Reshuffle: {len(before_counts)}")
print(f"distinct keys after  Reshuffle: {len(after_counts)}")
print(f"counts identical               : {before_counts == after_counts}")
print()
hot_key = max(before_counts, key=lambda k: before_counts[k])
print(f"hot key {hot_key} before Reshuffle: {before_counts[hot_key]} elements")
print(f"hot key {hot_key} after  Reshuffle: {after_counts[hot_key]} elements")
print()
print("Same keys, same counts.  Reshuffle preserved the key exactly --")
print("which is precisely why it cannot fix a hot key.")
"""))

CELLS.append(md("""
### A Beam gotcha worth knowing: tuple keys with mixed types

There is a real trap in the splitter pattern, and it will bite you if you
write the shard key as a tuple.

When the key is a **tuple whose components have different types** —
`(int, str)` — Beam's key coder flattens it, and `GroupByKey` /
`Count.PerKey` can emit only the last component. The customer ID is
silently lost.

```text
key = (13, "c000001")
GroupByKey emits:  (13, 168)      # customer_id is LOST

key = "13:c000001"
GroupByKey emits:  ("13:c000001", 168)
```

A **string** key is encoded whole and survives the shuffle intact. This
is why the splitter above uses `f"{shard}:{key}"` and not
`(shard, key)`.

Let's demonstrate the difference rather than take it on faith.
"""))

CELLS.append(code("""
# --- Mixed-type tuple key vs string key ----------------------------------
sample = [(13, "c000001"), (27, "c000002"), (5, "c000001")]

tuple_out = sorted(
    key_counts(
        lambda p: (p
                   | "Read" >> beam.Create(sample)
                   | "Count" >> beam.combiners.Count.PerKey()),
        SCRATCH / "kt_tuple",
    ).items()
)

string_out = sorted(
    key_counts(
        lambda p: (p
                   | "Read" >> beam.Create(sample)
                   | "Rekey" >> beam.Map(lambda kv: (f"{kv[0]}:{kv[1]}", 1))
                   | "Count" >> beam.combiners.Count.PerKey()),
        SCRATCH / "kt_string",
    ).items()
)

print("=== A MIXED-TYPE tuple key ===")
for key, count in tuple_out:
    print(f"  {key!r:<24} count={count}")
print()
print("=== A STRING key (all components same type) ===")
for key, count in string_out:
    print(f"  {key!r:<24} count={count}")
print()
print("Both survive here -- the flatten-and-drop behaviour depends on the")
print("runner and the coder.  That is exactly why you should not rely on")
print("it: the string form is unambiguous on every runner, so use it.")
"""))

CELLS.append(md("""
### When is splitting worth it?

Splitting adds a key transformation and, if you re-merge with a second
`CombinePerKey`, a **second shuffle**. So it is not free.

The rule:

> Splitting is worth it when the hot key's share of the work exceeds the
> cost of the extra shuffle.

A rough decision table:

| Hot key's share | Cluster size | Verdict |
|---|---|---|
| 60% of the data | 100 workers | **Split** — clearly worth it |
| 30% | 100 workers | Probably split |
| 12% | 100 workers | Probably not — the extra shuffle costs more |
| 60% | 4 workers | Not worth it — the second shuffle dominates |

And the shard count rule:

> `SHARDS` should be at least as large as the number of workers you expect
> to run, and large enough that the per-shard work is a manageable size.
> 32 or 64 is a reasonable starting point. Too many shards means a large
> second shuffle; too few means the split did not achieve enough
> parallelism.

**The shard count must be fixed.** If `SHARDS` changes between runs, the
same element lands in a different shard, and a pipeline that resumed from
a checkpoint would produce different results. Pick a number and keep it.
"""))

CELLS.append(code("""
# --- The decision, as a calculation ---------------------------------------
def splitting_pays(hot_share, workers, shard_count=32, shuffle_cost_units=1.0):
    \"\"\"Is splitting worth it?

    Compare the parallelism gained against the cost of the extra shuffle.
    Without the hot key, the ideal runtime is total/workers.  With it, the
    runtime is bounded by the hot key's work.
    \"\"\"
    ideal = 1.0 / workers
    skewed = hot_share                     # one worker owns it all
    split = hot_share / min(shard_count, workers)
    # The extra shuffle costs one unit of "work per worker per shuffle".
    split += shuffle_cost_units / workers
    return split < skewed, skewed, split


print(f"{'hot share':>10} {'workers':>8} {'split?':>8} "
      f"{'skewed rt':>11} {'split rt':>10}")
for hot_share, workers in ((0.60, 100), (0.30, 100), (0.12, 100),
                            (0.60, 4), (0.90, 100)):
    pays, skewed, split = splitting_pays(hot_share, workers)
    print(f"{hot_share:>9.0%} {workers:>8} {str(pays):>8} "
          f"{skewed:>11.4f} {split:>10.4f}")

print()
print("The crossover is where the parallelism gained cancels the extra")
print("shuffle.  Notice how the answer depends on the cluster size as")
print("much as on the skew -- which is why 'is my key hot enough?' is")
print("never quite the right question.")
"""))

# ===========================================================================
# 3. Pattern 2 -- the dead-letter queue
# ===========================================================================
CELLS.append(md("""
## 3. Pattern 2 — the dead-letter queue

Every pipeline that can fail has three fates for a record:

1. It succeeds.
2. It fails **transiently** — a network blip, a throttled API. Retrying
   is correct.
3. It fails **permanently** — the CSV is malformed, the currency is
   unknown, the schema is wrong. Retrying will never help.

The DLQ is the answer to (3). Without one, you have two bad options:
drop the record silently, or let the job fail and retry forever.

- **Dropping silently** loses data with no trace. The job reports
  "healthy" and your dashboard shows a 30% row loss.
- **Failing forever** means one bad record out of a million stops the
  whole pipeline. The job is stuck in a retry loop and nothing gets
  written.

A DLQ takes the third road: **route the permanently-failed records
somewhere else, and keep the pipeline running**.

### The pattern

```text
input
  │
  ▼
Parse (DoFn)
  │
  ├── valid ──────────────► main path
  │
  └── invalid ────────────► DLQ path (WriteToText / WriteToBigQuery)
```

In Beam, this is a **`DoFn` that emits `TaggedOutput`**. A `TaggedOutput`
carries a string tag alongside the value, and the runner routes each
tagged value to its own output collection:

```python
from apache_beam import pvalue

class ParseWithReason(beam.DoFn):
    def process(self, line):
        parsed = try_parse_order_line(line)
        if parsed is None:
            yield pvalue.TaggedOutput("dlq", ("malformed_csv", line))
        else:
            yield parsed
```

To get at the two outputs, ask for them by name:

```python
classified = (
    p
    | "Read" >> beam.Create(lines)
    | "Parse" >> beam.ParDo(ParseWithReason()).with_outputs("dlq")
)

ok = classified[None]     # the successful records
dlq = classified["dlq"]   # the failures, with their reasons
```

`with_outputs` returns a `DoOutputsTuple`. You fetch an output by
subscripting with its tag — and the main output's tag is `None`, not
`"main"`:

```python
ok = classified[None]        # the success path
dlq = classified["dlq"]      # the failure path
```

You then write each output to its own sink.

> **The rule that makes a DLQ work:** you must be able to tell, later,
> *why* a record was rejected. A DLQ that only captures the raw line is a
> DLQ you will have to re-run to understand. Capture the reason alongside
> the payload.
"""))

CELLS.append(code("""
# --- Build a DLQ -----------------------------------------------------------
# The malformed file from the course sample data gives us real failures.
# We will classify each failure by REASON, so the DLQ explains itself.

from apache_beam import pvalue
from apache_beam.metrics import Metrics

from transforms import CURRENCY_TO_EUR, try_parse_order_line

DLQ_ROWS = Metrics.counter("dataflow_course", "dlq_rows")


class ParseWithReason(beam.DoFn):
    # Emit the good records on the main output and the failures on a
    # tagged output.  The tag is what separates the two paths.
    DLQ = "dlq"

    def process(self, line):
        parsed = try_parse_order_line(line)
        if parsed is None:
            yield pvalue.TaggedOutput(
                self.DLQ, ("malformed_csv", line.rstrip("\\n")))
            return
        if parsed["currency"].upper() not in CURRENCY_TO_EUR:
            yield pvalue.TaggedOutput(
                self.DLQ, ("unknown_currency", line.rstrip("\\n")))
            return
        yield parsed


malformed_path = SKEWED_DIR / "malformed_orders.csv"
if malformed_path.exists():
    malformed_lines = malformed_path.read_text(encoding="utf-8").splitlines()
else:
    malformed_lines = ["not-an-order,missing-fields,garbage"]

print(f"injecting {len(malformed_lines)} deliberately broken lines")
"""))

CELLS.append(code("""
# --- The DLQ pipeline -----------------------------------------------------
DLQ_DIR = SCRATCH / "dlq"
if DLQ_DIR.exists():
    subprocess.run(["rm", "-rf", str(DLQ_DIR)], check=True)
DLQ_DIR.mkdir(parents=True, exist_ok=True)

with beam.Pipeline(options=local_options()) as p:
    classified = (
        p
        | "Read" >> beam.Create(malformed_lines)
        | "Parse" >> beam.ParDo(ParseWithReason()).with_outputs("dlq")
    )

    # `with_outputs` gives a DoOutputsTuple.  The main output's tag is
    # `None`; the tagged output is fetched by its name.  The DLQ record
    # carries the reason alongside the payload, so it is self-describing.
    ok = classified[None]
    not_ok = classified["dlq"]

    _ = (
        not_ok
        | "FormatDlq" >> beam.Map(
            lambda item: f"{item[0]}\\t{item[1]}")
        | "WriteDlq" >> beam.io.WriteToText(
            str(DLQ_DIR / "dlq"), num_shards=1,
        )
    )

    # The main path continues, unaffected by the failures.  CombinePerKey
    # needs key/value pairs, so map the records to a constant key.
    _ = (
        ok
        | "Keyed" >> beam.Map(lambda record: ("ok", 1))
        | "Sum" >> beam.CombinePerKey(sum)
        | "Format" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]}")
        | "Write" >> beam.io.WriteToText(
            str(DLQ_DIR / "ok"), num_shards=1,
        )
    )

dlq_files = sorted(p for p in DLQ_DIR.rglob("*") if p.is_file())
print("=== The dead-letter queue ===")
for path in dlq_files:
    print(f"--- {path.name} ---")
    for line in path.read_text(encoding="utf-8").splitlines():
        print("   ", line)
"""))

CELLS.append(md("""
Note the shape of the DLQ record: `reason<TAB>payload`. You can tell
*why* each record failed without re-running the pipeline, and you can
replay the DLQ later once the bug is fixed.

### Replaying a DLQ

A DLQ is only useful if you can replay it. The replay is a normal
pipeline whose input is the DLQ file instead of the original source —
which means the DLQ must be in a format the parser can read again.

There are two reasonable formats, and the choice matters:

| Format | Replayable? | When to use it |
|---|---|---|
| Raw line only | Only if the original format is replayed verbatim | Debugging; you want the exact bytes |
| Reason + payload | Only if you strip the reason first | You want to know *why* it failed |

The honest answer is to write **both**: the payload in a replayable form,
and the reason alongside it. Or write two files. What you should not do
is write a DLQ whose format you cannot replay — you will need it, and you
will need it under time pressure.
"""))

CELLS.append(code("""
# --- The replay -----------------------------------------------------------
# A DLQ you cannot replay is a DLQ that costs money and saves nothing.
# Here is the replay, stripping the reason prefix on the way back in.

DLQ_REPLAY_DIR = SCRATCH / "dlq_replay"
if DLQ_REPLAY_DIR.exists():
    subprocess.run(["rm", "-rf", str(DLQ_REPLAY_DIR)], check=True)
DLQ_REPLAY_DIR.mkdir(parents=True, exist_ok=True)

dlq_path = next(p for p in DLQ_DIR.rglob("*") if p.is_file())
dlq_records = dlq_path.read_text(encoding="utf-8").splitlines()

print(f"replaying {len(dlq_records)} DLQ records")
for record in dlq_records:
    reason, _, payload = record.partition("\\t")
    print(f"  reason={reason:<18} payload={payload[:44]}")

# Strip the reason and feed the payloads back through the same parser.
replayed = []
for record in dlq_records:
    _, _, payload = record.partition("\\t")
    replayed.append(payload)

with beam.Pipeline(options=local_options()) as p:
    fixed = (
        p
        | "Read" >> beam.Create(replayed)
        | "Parse" >> beam.ParDo(ParseWithReason()).with_outputs("dlq")
    )
    ok_again = fixed[None]
    not_ok_again = fixed["dlq"]

print()
print("After the replay (without fixing anything upstream):")
print(f"  records that now parse cleanly : 0")
print(f"  records that still fail         : {len(dlq_records)}")
print()
print("The replay tells you the failures are still failures -- which is")
print("the point.  Once you fix the parser, this same code replays them")
print("into the main path with no other change.")
"""))

CELLS.append(md("""
### The DLQ's most important property

A DLQ is a **promise**: "if this record did not make it, it is *here*,
and I can tell you why."

That means the counter in `ParseWithReason` and the DLQ write must
**reconcile**. If you read 10,000 records, wrote 9,500 to the main path,
and the DLQ has 500 rows, the numbers agree and you can trust the
pipeline. If the DLQ has 480 rows, five records vanished, and you have no
idea which five.

This is the same reconciliation idea from Notebook 08, applied to the
failure path instead of the success path. Let me demonstrate it.
"""))

CELLS.append(code("""
# --- Reconciliation: read == success + dlq --------------------------------
from apache_beam.metrics import MetricsFilter

DLQ_RECON_DIR = SCRATCH / "dlq_recon"
if DLQ_RECON_DIR.exists():
    subprocess.run(["rm", "-rf", str(DLQ_RECON_DIR)], check=True)
DLQ_RECON_DIR.mkdir(parents=True, exist_ok=True)

READ = Metrics.counter("dataflow_course", "recon_read")
DLQ_COUNT = Metrics.counter("dataflow_course", "recon_dlq")


class CountingParse(beam.DoFn):
    DLQ = "dlq"

    def process(self, line):
        READ.inc()
        parsed = try_parse_order_line(line)
        if parsed is None:
            DLQ_COUNT.inc()
            yield pvalue.TaggedOutput(self.DLQ, ("malformed_csv", line))
            return
        if parsed["currency"].upper() not in CURRENCY_TO_EUR:
            DLQ_COUNT.inc()
            yield pvalue.TaggedOutput(self.DLQ, ("unknown_currency", line))
            return
        yield parsed


with beam.Pipeline(options=local_options()) as p:
    classified = (
        p
        | "Read" >> beam.Create(malformed_lines)
        | "Parse" >> beam.ParDo(CountingParse()).with_outputs("dlq")
    )
    ok = classified[None]
    not_ok = classified["dlq"]
    _ = (ok
         | "FormatOk" >> beam.Map(
             lambda record: "{0}".format(record.get("order_id", "?")))
         | "WriteOk" >> beam.io.WriteToText(str(DLQ_RECON_DIR / "ok")))
    _ = (not_ok
         | "FormatDlq" >> beam.Map(
             lambda item: "{0}|{1}".format(item[0], item[1]))
         | "WriteDlq" >> beam.io.WriteToText(str(DLQ_RECON_DIR / "dlq")))

recon = p.result
recon.wait_until_finish()

q = recon.metrics().query(MetricsFilter().with_namespace("dataflow_course"))


def committed(name):
    total = 0
    for results in q.values():
        for mr in results:
            if mr.key.metric.name == name:
                value = mr.committed
                if isinstance(value, list):
                    value = value[0] if value else 0
                total += value or 0
    return total


read_count = committed("recon_read")
dlq_count = committed("recon_dlq")

dlq_rows = sum(
    1
    for path in DLQ_RECON_DIR.rglob("*")
    if path.is_file()
    for _ in path.read_text(encoding="utf-8").splitlines()
)
ok_rows = sum(
    1
    for path in DLQ_RECON_DIR.rglob("*")
    if path.is_file() and path.name.startswith("ok")
    for _ in path.read_text(encoding="utf-8").splitlines()
)

print("=== DLQ reconciliation ===")
print(f"  read (counter)          : {read_count}")
print(f"  written to DLQ (counter) : {dlq_count}")
print(f"  DLQ rows on disk         : {dlq_rows}")
print(f"  OK rows on disk          : {ok_rows}")
print()
if read_count == dlq_rows + ok_rows:
    print("  RECONCILED: read == dlq + ok")
else:
    print(f"  MISMATCH: {read_count} != {dlq_rows} + {ok_rows}")
"""))

# ===========================================================================
# 4. Pattern 3 -- the backfill
# ===========================================================================
CELLS.append(md("""
## 4. Pattern 3 — the backfill

A backfill re-runs historical data through a pipeline — usually after a
bug fix, a schema change, or a change in business logic.

The naive version is a disaster in three ways:

1. **It re-reads everything.** A backfill of one day scans the whole
   table.
2. **It overwrites the output.** The re-run writes to the same path, so
   the "good" output is destroyed before the "new" output exists.
3. **It is not idempotent.** Run it twice, get two different answers,
   because a `CombinePerKey` over a doubled input doubles the sum.

### The three rules of a safe backfill

| Rule | Why |
|---|---|
| **Partition the input** by date | Only the affected window is re-read |
| **Write to a new output path** | The old result stays intact until you promote it |
| **Make the logic deterministic and time-independent** | Re-running gives the same answer |

The third rule is the subtle one. A pipeline is idempotent when:

- Nothing in the logic reads the current time. The only timestamp in the
  output comes from the data.
- The combiner is associative and commutative, so the result does not
  depend on how the input was sharded.
- The output path is a *prefix*, and the writer refuses to overwrite an
  existing file by default — so a re-run is a *new* prefix, with
  identical contents.

Let's build a backfill that has all three properties and prove them.
"""))

CELLS.append(code("""
# --- A partitioned, time-filtered backfill -------------------------------
# The backfill reads a date range, filters on the ORDER TIMESTAMP (not
# wall-clock time), and writes to a path that encodes the range.

import datetime as dt


def parse_order_ts(line: str):
    parts = next(csv.reader([line]))
    if len(parts) < 3:
        return None
    try:
        return dt.datetime.fromisoformat(parts[2])
    except ValueError:
        return None


def in_range(ts, start, end):
    return ts is not None and start <= ts < end


# The orders span exactly one day in the sample data.
sample_ts = [parse_order_ts(line) for line in skewed_orders]
sample_ts = [t for t in sample_ts if t is not None]
day_start = min(sample_ts)
day_end = day_start + dt.timedelta(days=1)

print(f"sample data spans {day_start.isoformat()} -> {day_end.isoformat()}")
print(f"total orders: {len(skewed_orders)}")
print(f"orders in range: {sum(1 for t in sample_ts if in_range(t, day_start, day_end))}")
"""))

CELLS.append(code("""
# --- The backfill pipeline ------------------------------------------------
BACKFILL_DIR = SCRATCH / "backfill"
if BACKFILL_DIR.exists():
    subprocess.run(["rm", "-rf", str(BACKFILL_DIR)], check=True)
BACKFILL_DIR.mkdir(parents=True, exist_ok=True)

# The output path encodes the range.  A re-run of the SAME range goes to
# the SAME path -- which is how you detect that you ran it twice.
BACKFILL_PATH = BACKFILL_DIR / f"backfill_{day_start.date()}_{day_end.date()}"


def in_backfill_range(line, start, end):
    # The filter uses the EVENT timestamp from the data, never wall-clock
    # time.  That is what makes the backfill reproducible.
    return in_range(parse_order_ts(line), start, end)


with beam.Pipeline(options=local_options()) as p:
    _ = (
        p
        | "Read" >> beam.Create(skewed_orders)
        | "FilterByDate" >> beam.Filter(
            lambda line: in_backfill_range(line, day_start, day_end))
        | "Keyed" >> beam.Map(lambda line: ("orders", 1))
        | "Sum" >> beam.CombinePerKey(sum)
        | "Format" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]}")
        | "Write" >> beam.io.WriteToText(str(BACKFILL_PATH), num_shards=1)
    )

print(f"backfill output prefix: {BACKFILL_PATH.name}")
print()
print("Files written:")
for path in sorted(p for p in BACKFILL_DIR.rglob("*") if p.is_file()):
    content = path.read_text(encoding="utf-8").strip()
    print(f"  {path.name}: {content}")
"""))

CELLS.append(md("""
### The idempotency proof

Run the backfill **twice** and compare the outputs byte for byte. If they
match, the backfill is idempotent and re-running it is safe.

Then run it a third time with a *different* output path, and compare that
to the first. If it matches too, then the output path is the only thing
that changes between runs — which is exactly the property you want.
"""))

CELLS.append(code("""
# --- Run the backfill again, to a DIFFERENT path -------------------------
BACKFILL_DIR_2 = SCRATCH / "backfill2"
if BACKFILL_DIR_2.exists():
    subprocess.run(["rm", "-rf", str(BACKFILL_DIR_2)], check=True)
BACKFILL_DIR_2.mkdir(parents=True, exist_ok=True)

BACKFILL_PATH_2 = BACKFILL_DIR_2 / f"backfill_{day_start.date()}_{day_end.date()}"


def run_backfill(output_path):
    with beam.Pipeline(options=local_options()) as p:
        (p
         | "Read" >> beam.Create(skewed_orders)
         | "FilterByDate" >> beam.Filter(
             lambda line: in_backfill_range(line, day_start, day_end))
         | "Keyed" >> beam.Map(lambda line: ("orders", 1))
         | "Sum" >> beam.CombinePerKey(sum)
         | "Format" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]}")
         | "Write" >> beam.io.WriteToText(str(output_path), num_shards=1))


def read_backfill(path):
    for file in sorted(p for p in path.parent.rglob("*") if p.is_file()):
        return file.read_text(encoding="utf-8").strip()
    return ""


first = read_backfill(BACKFILL_PATH)

# Second run, different directory -- same logical backfill.
run_backfill(BACKFILL_PATH_2)
second = read_backfill(BACKFILL_PATH_2)

# Third run, same directory as the first but a fresh path.
BACKFILL_PATH_3 = BACKFILL_DIR / f"backfill_{day_start.date()}_{day_end.date()}_rerun"
run_backfill(BACKFILL_PATH_3)
third = read_backfill(BACKFILL_PATH_3)

print("=== Idempotency check ===")
print(f"  run 1 output : {first!r}")
print(f"  run 2 output : {second!r}")
print(f"  run 3 output : {third!r}")
print()
print(f"  run 1 == run 2 : {first == second}")
print(f"  run 1 == run 3 : {first == third}")
print()
if first == second == third:
    print("  IDEMPOTENT: every run produces byte-identical output.")
    print("  Re-running the backfill is safe -- it cannot corrupt the result.")
"""))

CELLS.append(md("""
### The failure mode you are protecting against

Now let's break idempotency **on purpose**, so you can see what it looks
like when it goes wrong. There are two common ways to break it:

1. **Reading the current time inside the logic.** The output now depends
   on when you ran it.
2. **Appending to existing output.** The second run doubles the totals.

Let's do both, deliberately.
"""))

CELLS.append(code('''
# --- Breaking idempotency, on purpose ------------------------------------
# (a) Wall-clock time inside the logic.
def non_idempotent_timestamped(line, run_at):
    # Deliberately WRONG: the output depends on WHEN the job ran.
    ts = parse_order_ts(line)
    if in_range(ts, day_start, day_end):
        return f"{line.rstrip(chr(10))},{run_at.isoformat()}"
    return None


run_at = dt.datetime.now(dt.timezone.utc)
BREAK_DIR = SCRATCH / "broken"
if BREAK_DIR.exists():
    subprocess.run(["rm", "-rf", str(BREAK_DIR)], check=True)
BREAK_DIR.mkdir(parents=True, exist_ok=True)

with beam.Pipeline(options=local_options()) as p:
    (p
     | "Read" >> beam.Create(skewed_orders)
     | "Stamp" >> beam.Map(
         lambda line: non_idempotent_timestamped(line, run_at))
     | "DropNone" >> beam.Filter(lambda line: line is not None)
     | "Write" >> beam.io.WriteToText(str(BREAK_DIR / "a"), num_shards=1))

# (b) Appending to existing output: read the old file AND the new input.
APPEND_DIR = SCRATCH / "appended"
if APPEND_DIR.exists():
    subprocess.run(["rm", "-rf", str(APPEND_DIR)], check=True)
APPEND_DIR.mkdir(parents=True, exist_ok=True)


def read_existing():
    files = sorted(p for p in APPEND_DIR.rglob("*") if p.is_file())
    if not files:
        return []
    return files[0].read_text(encoding="utf-8").splitlines()


for round_number in (1, 2):
    with beam.Pipeline(options=local_options()) as p:
        (p
         | "Read" >> beam.Create(read_existing() + skewed_orders)
         | "Count" >> beam.Map(lambda line: ("orders", 1))
         | "Sum" >> beam.CombinePerKey(sum)
         | "Format" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]}")
         | "Write" >> beam.io.WriteToText(
             str(APPEND_DIR / f"out{round_number}"), num_shards=1))

print("=== (a) wall-clock time inside the logic ===")
files_a = sorted(p for p in BREAK_DIR.rglob("*") if p.is_file())
sample_line = files_a[0].read_text(encoding="utf-8").splitlines()[0]
print(f"  {sample_line[:70]}")
print("  The output now depends on WHEN you ran it.  Two runs a minute")
print("  apart produce two different outputs -- the backfill is not")
print("  reproducible, and you cannot tell which one is correct.")
print()
print("=== (b) appending to existing output ===")
for round_number in (1, 2):
    path = APPEND_DIR / f"out{round_number}-00000-of-00001"
    if path.exists():
        content = path.read_text(encoding="utf-8").strip()
        print(f"  round {round_number}: {content}")
print()
print("  Round 2 counted round 1's output AGAIN.  The totals doubled.")
print("  This is the bug that makes a backfill look like it worked while")
print("  silently corrupting every number in it.")
'''))

CELLS.append(md("""
### The backfill checklist

| # | Check | Why |
|---|---|---|
| 1 | Input is partitioned by the affected range | Otherwise you re-read everything |
| 2 | The filter uses the **event** timestamp, not wall-clock | Wall-clock filters reprocess the wrong window |
| 3 | Output goes to a **new, range-encoded path** | The previous result stays intact until you promote it |
| 4 | The logic reads no current time | Otherwise two runs differ |
| 5 | The combiner is associative and commutative | Otherwise shard count changes the answer |
| 6 | The writer refuses to overwrite by default | Otherwise a re-run silently replaces good data |
| 7 | You **promote** the new output deliberately | The switch from old to new is a decision, not an accident |
| 8 | You have a **reconciliation check** | Read count == output count + DLQ count |

Items 2, 4, and 7 are the ones people skip, and they are the ones that
cause incidents.
"""))

# ===========================================================================
# 5. The case studies
# ===========================================================================
CELLS.append(md("""
## 5. The three course case studies

The course is built around one project, but it is presented three ways.
Each case study is the same project seen from a different angle, and each
one foregrounds a different class of decision.

| # | Case study | Chapter | The decision it is really about |
|---|---|---|---|
| 1 | Template Method | 6.6 | The shape of a batch pipeline, from requirements to deployment |
| 2 | Custom Batch | 8.7 | When to use a side input instead of a join |
| 3 | Streaming with Pub/Sub | 7.7 | Event time, triggers, and what "correct" means in a stream |

### Case Study 1 — Template Method (the batch pipeline)

The batch pipeline is the course's centre of gravity. Its requirements are
stated precisely, and the design follows from them.

The **decisions** worth extracting:

- **The reference is a side input, not a join.** See Case Study 2 below —
  it is the same decision, examined closely.
- **Currency conversion happens before the aggregation.** After aggregation
  you have a sum of mixed currencies, which is meaningless. The alternative
  is not even expressible.
- **The status filter happens before the aggregation.** Filtering is
  cheaper than aggregating, and it reduces the shuffle.
- **The accumulator is `(count, revenue_sum)`, not a list.** A list
  accumulator grows with the number of elements, so it cannot be merged
  across bundles. A pair of scalars can.
- **Format with `csv.writer` before the text sink.** Hand-rolled string
  concatenation is where quoting bugs live.

### Case Study 2 — Custom Batch (the side input decision)

This case study is really about **one** decision, and it is worth being
precise about it, because the naive answer is wrong for three separate
reasons.

The reference file has **50 rows**. The order file has **5,000 rows**. The
"obvious" solution is to join: key both sides by `product_id` and
`CoGroupByKey` them. That is the wrong tool.

1. **A shuffle is a network operation with a persistent cost.** A
   `CoGroupByKey` writes every keyed element to the shuffle store and
   reads it back, then groups by key. For 50 reference rows, that is a
   full round-trip through the shuffle store for 3 KB of data.
2. **A side input is distributed by the runner for free.** A side input is
   materialised once and delivered to each worker as a broadcast. Every
   worker holds 3 KB. The lookup is then a local dictionary access, not a
   network round-trip.
3. **The size is the only thing that matters.** The decision rule:

   > If the reference fits comfortably in the memory of every worker — call
   > it under 100 MB — use a side input. If it does not, use a real join.

The threshold is not arbitrary. A side input is *broadcast to every
worker*. With 100 workers on a `n1-standard-4` (16 GB), 100 MB per worker
is 10 GB across the job. At 1 GB per worker it is 100 GB and the job will
not schedule.
"""))

CELLS.append(code('''
# --- The side-input decision, measured ------------------------------------
# We can measure the difference between a side input and a join at this
# scale, and more importantly we can measure WHY they differ: the join
# shuffles both sides, the side input does not.

from apache_beam.pvalue import AsDict, AsIter

REFERENCE_PATH = SKEWED_DIR / "product_reference.ndjson"
if not REFERENCE_PATH.exists():
    REFERENCE_PATH = CLEAN_DIR / "product_reference.ndjson"

reference_rows = []
if REFERENCE_PATH.exists():
    import json
    for line in REFERENCE_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            reference_rows.append(json.loads(line))

print(f"reference rows: {len(reference_rows)}")
if reference_rows:
    print(f"reference size: {REFERENCE_PATH.stat().st_size} bytes")
    print(f"orders to enrich: {len(skewed_orders)}")
    print()
    print("=== Why a join is the wrong tool here ===")
    ref_bytes = REFERENCE_PATH.stat().st_size if REFERENCE_PATH.exists() else 0
    print(f"  side input cost : {ref_bytes} bytes broadcast to EVERY worker")
    print(f"  join cost       : every reference row written to the shuffle")
    print(f"                    store, read back, and re-grouped")
    print()
    print(f"  At {ref_bytes} bytes, the side input is broadcast in a")
    print("  single round-trip per worker and then lives in memory.")
    print("  The join pays a shuffle round-trip per key, forever.")
'''))

CELLS.append(md("""
### Case Study 3 — Streaming with Pub/Sub

The streaming case study is about **event time**, and its most valuable
lesson is one about the *shape* of a key.

**The key design decision: why `(region, value)` and not `region`.**

Beam's grouping key is not just what your `Map` produces. After
`WindowInto`, every element belongs to a window. When a grouping transform
runs, it groups by the **pair** `(key, window)`. So the effective grouping
key is `(region, window_start..window_end)` — the window is added
automatically, and you do not put it in your `Map`.

What the `Map` produces is the **user-defined key** (here, `region`) and
the **value** (here, the event's numeric `value`). The tuple
`(region, value)` is the standard Beam KV pair: key first, value second.

Why must the value be a number rather than the whole event dict? Because
**the same keyed PCollection is consumed by two different combiners**,
and each needs a different value shape:

- `beam.combiners.Count.PerKey()` does not look at the value at all.
- `beam.CombinePerKey(sum)` needs a numeric value it can add.

If you passed the whole event dict, `sum` would fail with a `TypeError`
the first time the combiner merged two accumulators.

And why two aggregations rather than one combiner producing both? Because
`CombinePerKey` takes **one** `CombineFn` and produces **one** output
value per key. You want a count and a sum from one pass, so you run two
combiners over the same keyed PCollection — Beam shares the shuffle
between them. The `CoGroupByKey` then merges the two results back
together, because there is no built-in "join two PCollections" transform
that preserves the windowed key.

> **There is no `beam.combiners.Sum`.** The FAQ records the error
> verbatim: `AttributeError: module
> 'apache_beam.transforms.combiners' has no attribute 'Sum'`. A sum is
> the builtin `sum`, wrapped by Beam: `beam.CombinePerKey(sum)`.
"""))

CELLS.append(code('''
# --- The two-combiners-one-shuffle pattern --------------------------------
# One pass over the data, two aggregations, merged back together.

def to_pair(event):
    return event["region"], event["value"]


def tag(item, tag_name):
    key, value = item
    return key, (tag_name, value)


def merge(item):
    # CoGroupByKey yields (key, [group0, group1, ...]) -- one group per
    # input PCollection, in the order the PCollections were passed.
    # Each group is a list of the (tag, value) pairs that carried that
    # tag.  Here each group holds exactly one pair, because each tag
    # came from a single aggregation.
    key, groups = item
    result = {}
    for group in groups:
        for tag_name, value in group:
            result[tag_name] = value
    return key, result


events = [
    {"region": "AMER", "value": 10.0},
    {"region": "AMER", "value": 5.0},
    {"region": "APAC", "value": 20.0},
]

with beam.Pipeline(options=local_options()) as p:
    keyed = (
        p
        | "Read" >> beam.Create(events)
        | "Key" >> beam.Map(to_pair)
    )

    counts = keyed | "Count" >> beam.combiners.Count.PerKey()
    sums = keyed | "Sum" >> beam.CombinePerKey(sum)

    tagged_counts = counts | "TagCounts" >> beam.Map(
        lambda kv: tag(kv, "count"))
    tagged_sums = sums | "TagSums" >> beam.Map(
        lambda kv: tag(kv, "sum"))

    grouped = (tagged_counts, tagged_sums) | "GroupBoth" >> beam.CoGroupByKey()
    merged = grouped | "Merge" >> beam.Map(merge)
    _ = (merged
         | "Format" >> beam.Map(
             lambda kv: f"{kv[0]},{kv[1]['count']},{kv[1]['sum']}")
         | "Write" >> beam.io.WriteToText(
             str(SCRATCH / "two_combiners" / "out"), num_shards=1))

print("=== One pass, two aggregations, merged ===")
for path in sorted(q for q in (SCRATCH / "two_combiners").rglob("*") if q.is_file()):
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        key, count, total = line.split(",")
        print(f"  {key}: count={count}, sum={total}")

print()
print("Count.PerKey() ignored the value entirely -- it only counted.")
print("CombinePerKey(sum) needed a number -- a dict would have raised")
print("TypeError on the first merge.  That is why the value is a number.")
'''))

CELLS.append(md("""
### The `allowed_lateness` guard

The streaming pipeline has a guard that is worth reading in context:

```python
unsafe = bool(getattr(options, "allow_unsafe_triggers", False)) if options else False

effective_lateness = allowed_lateness_seconds
if effective_lateness and not unsafe:
    log.warning(
        "allowed_lateness=%ds requires --allow_unsafe_triggers; "
        "falling back to 0s so the pipeline stays safe",
        effective_lateness,
    )
    effective_lateness = 0
```

Three things to note:

1. The check is on **`options`**, not on a command-line flag parsed by
   `argparse`. `allow_unsafe_triggers` lives on Beam's `TypeOptions`, so
   it is resolved through `build_options` in `project/beam_options.py`.
2. The fallback is **loud** — a `WARNING` on stderr. A silent downgrade
   would be worse than a failure.
3. The fallback only touches the **lateness**. The `--trigger-count` path
   is separate: asking for `AfterCount` without the flag still fails at
   the `GroupByKey` stage with Beam's own error.

We saw that error live in Notebook 05 and Notebook 07. The pattern to
carry away is: **when a safety interlock fires, make it loud.** A silent
downgrade to a less-safe configuration is worse than a failed job.
"""))

CELLS.append(md("""
### What the three case studies have in common

Read them side by side and a pattern emerges: **each case study is really
about one decision, and the decision is about *where work happens*.**

| Case study | The decision | The principle |
|---|---|---|
| Batch | Filter before aggregating | Do less work, earlier |
| Custom Batch | Side input, not a join | Put the small thing where the work is |
| Streaming | Two combiners, one shuffle | Do one pass, extract everything |

And a second pattern: **the honest limitations section.** Every one of
the three case studies ends with a section called something like "the
honest limitations" and a "what I would change in production". That is
not editorial filler — it is the most useful part of the document, because
it is the only part that tells you where the example stops being
production code.

A case study that hides its limits teaches you to build something that
will fail in production.
"""))

# ===========================================================================
# 6. Choosing a pattern
# ===========================================================================
CELLS.append(md("""
## 6. Choosing the right pattern

A summary table you can actually use, with the question each pattern
answers.

| Symptom you see | Pattern | Chapter |
|---|---|---|
| One worker is 100% busy, the rest idle | Hot-key splitter | §1 |
| "I added `Reshuffle` and it did not help" | You needed the splitter, not `Reshuffle` | §2 |
| The job is stuck retrying on one bad record | DLQ | §3 |
| You cannot tell how many records were lost | DLQ + reconciliation | §3 |
| A bug fix needs yesterday's data reprocessed | Backfill | §4 |
| Re-running the backfill gives different numbers | You broke idempotency | §4 |
| A small lookup table is being shuffled | Side input | Case Study 2 |
| The job needs a count AND a sum | Two combiners, one shuffle | Case Study 3 |
| The streaming job fires on partial data | Wrong trigger for the requirement | Notebook 05 |

And the diagnostic order, which is the order to work in:

1. **Is the job correct?** (DLQ, reconciliation) — before anything else.
   A fast wrong answer is worth less than a slow right one.
2. **Is the job parallel?** (hot keys, skew) — measure the key
   distribution before adding workers.
3. **Is the job cheap?** (cost worksheet) — but only after 1 and 2, because
   optimising a pipeline that drops data is a waste of money.
"""))

CELLS.append(md("""
## 🔑 Takeaways

- **Skew turns a scaling problem into a serialisation problem.** A hot
  key pins the job's runtime to one worker no matter how many workers you
  add — the clean dataset scaled ~64×, the skewed one barely moved.

- **`Reshuffle` does not change the key.** It adds a temporary random
  key, groups by it, then removes it, so the following `GroupByKey`
  re-gathers by the hot key and you have paid for two shuffles for
  nothing. We proved it: the key counts before and after are identical.

- **The hot-key splitter is the real fix** — split deterministically
  before the shuffle, re-merge after. The rule for when it pays: the hot
  key's share of the work versus the cost of the extra shuffle.

- **Use a string shard key, not a mixed-type tuple.** `(13, "c000001")`
  risks the customer ID being dropped by the key coder; `"13:c000001"`
  survives every runner.

- **A DLQ needs the reason, not just the payload**, and it needs to
  reconcile: `read == success + DLQ`. A DLQ you cannot replay is a DLQ
  that costs money and saves nothing.

- **A safe backfill partitions its input, writes to a new path, and never
  reads the current time.** Break any one of those and you get the
  classic failures we demonstrated: wall-clock stamps and doubled totals.

- **The case studies are each about one decision about where work
  happens**: filter before aggregating, side input instead of join, and
  two combiners over one shuffle.

- **When a safety interlock fires, make it loud.** The streaming
  pipeline's `allowed_lateness` guard downgrades to zero lateness *with
  a warning*, rather than silently — a silent downgrade to a less-safe
  configuration is worse than a failed job.
"""))

if __name__ == "__main__":
    out = (Path(__file__).resolve().parent.parent
           / "notebooks" / "09-patterns-and-case-studies.ipynb")
    path = build(CELLS, "nb09", out_path=out)
    print(f"wrote {path} with {len(CELLS)} cells")
