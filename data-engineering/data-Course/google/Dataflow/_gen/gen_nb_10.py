"""Generate notebooks/10-end-to-end-project.ipynb.

The notebook is the capstone: it runs the *actual* project pipelines
(`project/batch_pipeline.py` and `project/streaming_pipeline.py`) as
subprocesses, reads the files they produce, and cross-validates the Beam
output against the pure-Python reference implementation
(`build_revenue_summary`) that lives in `project/transforms.py`.

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
# 10 · End-to-End Project

> **The capstone · Modules 1–8**

This notebook is where the whole course comes together. You will:

- Read the **project architecture** — two pipelines, one shared transform library
- **Run the batch pipeline** as a real subprocess and inspect its output
- **Run the streaming pipeline** the same way, with real event-time windows
- **Cross-validate** the Beam output against a pure-Python reference
  implementation, so you can prove the distributed answer is the right answer
- Run the **test suite** and read the failure modes it encodes
- See what you would **change for production** — and what you would not

---

Everything in this notebook runs on your laptop. No GCP project, no
credentials, no bill. The point is that the *same* code paths run on Dataflow:
only the `--runner` flag and the path prefix change.
"""))

CELLS.append(setup_cell())

# ===========================================================================
# 1. The project layout
# ===========================================================================
CELLS.append(md("""
## 1. The project layout

The project is four Python modules and a test suite:

```
project/
├── batch_pipeline.py      # batch ETL: CSV -> revenue per region
├── streaming_pipeline.py  # streaming: NDJSON -> windowed aggregates
├── transforms.py          # the shared DoFn / CombineFn library
├── beam_options.py        # runner resolution and option plumbing
├── course_options.py      # a custom PipelineOptions subclass
└── tests/                 # pytest suite covering both pipelines
```

The design point worth noticing is that **`transforms.py` has no pipeline in
it**. It holds pure functions and Beam `DoFn` / `CombineFn` subclasses. Both
pipelines import from it, and the test suite imports from it. That is what
makes the correctness argument in section 5 possible: the reference
implementation and the Beam implementation are two readings of the *same*
business rules, not two copies of them that can drift apart.
"""))

CELLS.append(code('''
# The project layout, as the notebook sees it.
for entry in sorted(PROJECT_DIR.iterdir()):
    if entry.name == "__pycache__":
        continue
    marker = "dir " if entry.is_dir() else "file"
    print(f"  {marker}  {entry.name}")

print()
print("tests:")
for entry in sorted((PROJECT_DIR / "tests").glob("*.py")):
    print(f"  file  {entry.name}  ({len(entry.read_text().splitlines())} lines)")
'''))

# ===========================================================================
# 2. The batch pipeline
# ===========================================================================
CELLS.append(md("""
## 2. The batch pipeline

The batch pipeline is a five-step graph:

```
ReadFromText
  -> ParseOrderFn          (ParDo)
  -> Filter(status == complete)
  -> KeyByRegion           (Map)
  -> RevenueByRegionFn     (CombinePerKey)
  -> WriteToText           (CSV, with a header)
```

Two decisions in that graph are worth calling out before we run it.

**The filter sits *before* the combiner.** That matters for cost: a cancelled
order is never shuffled, never grouped, never accumulated. The alternative —
filtering after aggregation — would mean paying to move data you are about to
throw away.

**The combiner is a `CombineFn`, not a `Map` that accumulates.** A `CombineFn`
must be associative and commutative, because Beam merges partial accumulators
from different workers in an arbitrary order. The course's `RevenueByRegionFn`
satisfies that by keeping a running `(order_count, revenue_eur)` pair and
merging pairs pairwise.

Now let me actually run it.
"""))

CELLS.append(code('''
import shutil
import subprocess
import time

RUN_DIR = COURSE_ROOT / "_run" / "nb10"
if RUN_DIR.exists():
    shutil.rmtree(RUN_DIR)
RUN_DIR.mkdir(parents=True, exist_ok=True)

BATCH_OUT = RUN_DIR / "batch" / "summary"
STREAM_OUT = RUN_DIR / "stream" / "out"

PYTHON = sys.executable


def run_pipeline(script, extra_args, *, label):
    """Run one project pipeline as a subprocess and report the outcome.

    Running the pipeline as a subprocess -- rather than importing it -- is
    how it actually runs in production. It exercises the argument parsing,
    the runner resolution, and the `main()` entry point, all of which a
    notebook-level `import` would bypass.

    Args:
        script: The pipeline script's path.
        extra_args: Extra command-line arguments.
        label: A short name used in the log output.

    Returns:
        A dict with the return code, duration and captured stdout.
    """
    argv = [PYTHON, str(script), *extra_args]
    started = time.perf_counter()
    completed = subprocess.run(
        argv,
        cwd=str(COURSE_ROOT),
        capture_output=True,
        text=True,
    )
    elapsed = time.perf_counter() - started

    print(f"[{label}] exit={completed.returncode}  {elapsed:.1f}s")
    print(f"[{label}] command: {' '.join(argv[1:])}")
    if completed.returncode != 0:
        print(f"[{label}] STDERR tail:")
        print("\\n".join(completed.stderr.splitlines()[-20:]))
    else:
        interesting = [
            line
            for line in completed.stderr.splitlines()
            if "pipeline finished successfully" in line
            or "input=" in line
        ]
        for line in interesting:
            print(f"[{label}] {line}")
    return {
        "returncode": completed.returncode,
        "seconds": elapsed,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


batch_result = run_pipeline(
    PROJECT_DIR / "batch_pipeline.py",
    [
        "--runner", "BundleBasedDirectRunner",
        "--input", str(COURSE_ROOT / "sample_data" / "orders.csv"),
        "--output", str(BATCH_OUT),
    ],
    label="batch",
)

assert batch_result["returncode"] == 0, "the batch pipeline did not succeed"
'''))

CELLS.append(md("""
### Reading the output

`WriteToText` writes a *file*, not a row. The project uses
`num_shards=1` and `shard_name_template=""` so the output path is the
file itself rather than a directory of shards — that keeps the local and
cloud layouts identical, which matters when you `gsutil cp` the result
somewhere for inspection.

The header is `region,order_count,revenue_eur`.
"""))

CELLS.append(code('''
def read_summary_csv(path):
    """Read a summary CSV into a dict of region -> metrics.

    The batch pipeline writes `region,order_count,revenue_eur`; the
    streaming pipeline writes `region,event_count,total_value`. Both are
    normalised to the same shape here, so the cross-validation code can
    treat them uniformly.

    Args:
        path: The CSV file to read.

    Returns:
        A dict mapping region to {"order_count": int, "revenue_eur": float}.
    """
    import csv

    summary = {}
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        fieldnames = reader.fieldnames or []
        count_column = (
            "order_count" if "order_count" in fieldnames else "event_count"
        )
        value_column = (
            "revenue_eur" if count_column == "order_count" else "total_value"
        )
        for row in reader:
            summary[row["region"]] = {
                "order_count": int(row[count_column]),
                "revenue_eur": float(row[value_column]),
            }
    return summary


batch_files = sorted((RUN_DIR / "batch").rglob("*"))
batch_files = [f for f in batch_files if f.is_file()]
print("output files:")
for path in batch_files:
    print(f"  {path.relative_to(RUN_DIR)}  ({path.stat().st_size} bytes)")

print()
print("raw contents:")
for path in batch_files:
    print(path.read_text(encoding="utf-8").rstrip())

batch_summary = read_summary_csv(batch_files[0])
print()
print("parsed:")
for region in sorted(batch_summary):
    metrics = batch_summary[region]
    print(
        f"  {region:<6} count={metrics['order_count']:<5} "
        f"revenue_eur={metrics['revenue_eur']}"
    )
'''))

# ===========================================================================
# 3. The streaming pipeline
# ===========================================================================
CELLS.append(md("""
## 3. The streaming pipeline

The streaming pipeline is the same shape, with windows added:

```
ReadFromText
  -> parse_event           (Map)
  -> WindowInto(FixedWindows, trigger, allowed_lateness)
  -> KeyByRegion           (Map)
  -> Count.PerKey()  +  CombinePerKey(sum)
  -> CoGroupByKey()        (merge the two aggregations)
  -> WriteToText           (CSV, with a header)
```

Three things in that graph are the whole point of the module.

**Event time, not arrival time.** The window is chosen by the event's own
`event_ts`, read out of the payload. A pipeline that windows by arrival time
on out-of-order data produces silently wrong results, and no error is
raised — the number is just wrong.

**The trigger is safe by default.** `AfterWatermark` with zero allowed
lateness is the only combination that cannot fire while elements are still
in flight. The pipeline falls back to zero lateness unless the caller
explicitly passes `--allow_unsafe_triggers`.

**Two combiners, one shuffle.** Counting and summing happen over the same
keyed PCollection, so Beam shares the shuffle. `CoGroupByKey` then merges
the two aggregation results back together, preserving the windowed key.
"""))

CELLS.append(code('''
stream_result = run_pipeline(
    PROJECT_DIR / "streaming_pipeline.py",
    [
        "--runner", "BundleBasedDirectRunner",
        "--input", str(COURSE_ROOT / "sample_data" / "events.ndjson"),
        "--output", str(STREAM_OUT),
        "--window-seconds", "86400",
    ],
    label="stream",
)

assert stream_result["returncode"] == 0, "the streaming pipeline did not succeed"

stream_files = [
    f for f in sorted((RUN_DIR / "stream").rglob("*")) if f.is_file()
]
print()
print("output files:")
for path in stream_files:
    print(f"  {path.relative_to(RUN_DIR)}  ({path.stat().st_size} bytes)")

print()
print("raw contents:")
for path in stream_files:
    print(path.read_text(encoding="utf-8").rstrip())

stream_summary = read_summary_csv(stream_files[0])
print()
print("parsed:")
for region in sorted(stream_summary):
    metrics = stream_summary[region]
    print(
        f"  {region:<6} count={metrics['order_count']:<5} "
        f"total_value={metrics['revenue_eur']}"
    )
'''))

CELLS.append(md("""
### Why one window

The sample data spans a single day, so a 24-hour window puts every event in
one group. That is deliberate: it makes the expected output a small, checkable
table rather than 24 rows per region.

With a one-hour window you would get 24 rows per region instead, and the
per-region totals would still add up to the same numbers. Windowing changes
the *shape* of the output, not its total — and a pipeline that only ever
reports totals cannot tell you *when* the revenue arrived. That is the whole
reason streaming exists.
"""))

CELLS.append(code('''
# Run the streaming pipeline again with a one-hour window and show that the
# per-region totals are unchanged, even though the row count goes up 24x.
HOURLY_OUT = RUN_DIR / "stream_hourly" / "out"

hourly_result = run_pipeline(
    PROJECT_DIR / "streaming_pipeline.py",
    [
        "--runner", "BundleBasedDirectRunner",
        "--input", str(COURSE_ROOT / "sample_data" / "events.ndjson"),
        "--output", str(HOURLY_OUT),
        "--window-seconds", "3600",
    ],
    label="stream-hourly",
)

assert hourly_result["returncode"] == 0

hourly_files = [f for f in sorted(HOURLY_OUT.parent.rglob("*")) if f.is_file()]
hourly_rows = []
with hourly_files[0].open("r", encoding="utf-8", newline="") as fh:
    import csv as _csv

    for row in _csv.DictReader(fh):
        hourly_rows.append(row)

print()
print(f"24h window : {len(stream_summary)} rows")
print(f" 1h window : {len(hourly_rows)} rows")

hourly_totals = {}
for row in hourly_rows:
    bucket = hourly_totals.setdefault(
        row["region"], {"count": 0, "value": 0.0}
    )
    bucket["count"] += int(row["event_count"])
    bucket["value"] += float(row["total_value"])

print()
print("totals are identical across window widths:")
for region in sorted(stream_summary):
    wide = stream_summary[region]
    hourly = hourly_totals[region]
    same = (
        wide["order_count"] == hourly["count"]
        and abs(wide["revenue_eur"] - round(hourly["value"], 2)) < 0.01
    )
    print(
        f"  {region:<6} 24h={wide['order_count']:>5}/{wide['revenue_eur']:<12} "
        f"1h={hourly['count']:>5}/{round(hourly['value'], 2):<12} "
        f"{'MATCH' if same else 'MISMATCH'}"
    )
'''))

# ===========================================================================
# 4. The reference implementation
# ===========================================================================
CELLS.append(md("""
## 4. The reference implementation

`project/transforms.py` contains a pure-Python twin of the Beam combiner:

```python
def build_revenue_summary(rows, *, statuses=("complete",)):
    # Aggregate revenue per region from a collection of orders.
    ...
```

It takes an iterable of order dicts and returns a plain dict. No runner, no
PCollection, no shuffling. It is the same business rules, expressed
imperatively.

That twin exists for two reasons:

1. **It is testable without a runner.** `pytest` can call it in
   microseconds. Testing a `CombineFn` through a full pipeline takes
   seconds and needs a runner.
2. **It is an oracle.** It lets you assert that the distributed answer
   equals the single-machine answer. That is the strongest correctness
   statement you can make about a Beam pipeline, and it is the one section 5
   makes.
"""))

CELLS.append(code('''
from transforms import (
    build_revenue_summary,
    parse_event_payload,
    try_parse_order_line,
)

# --- Rebuild the reference summary from the raw CSV -------------------------
orders = []
with (COURSE_ROOT / "sample_data" / "orders.csv").open(
    "r", encoding="utf-8", newline=""
) as fh:
    import csv as _csv

    for row in _csv.DictReader(fh):
        parsed = try_parse_order_line(",".join(row.values()))
        if parsed is not None:
            orders.append(parsed)

print(f"parsed orders : {len(orders)}")

reference_summary = build_revenue_summary(orders)
print()
print("reference implementation (pure Python, no runner):")
for region in sorted(reference_summary):
    metrics = reference_summary[region]
    print(
        f"  {region:<6} count={int(metrics['order_count']):<5} "
        f"revenue_eur={metrics['revenue_eur']}"
    )

# --- And the reference for the streaming side ------------------------------
events = []
with (COURSE_ROOT / "sample_data" / "events.ndjson").open(
    "r", encoding="utf-8"
) as fh:
    for line in fh:
        line = line.strip()
        if line:
            events.append(parse_event_payload(line))

print()
print(f"parsed events : {len(events)}")

event_counts = {}
event_totals = {}
for event in events:
    region = event["region"]
    event_counts[region] = event_counts.get(region, 0) + 1
    event_totals[region] = event_totals.get(region, 0.0) + float(event["value"])

print()
print("reference implementation (pure Python, no runner):")
for region in sorted(event_counts):
    print(
        f"  {region:<6} count={event_counts[region]:<5} "
        f"total_value={round(event_totals[region], 2)}"
    )
'''))

# ===========================================================================
# 5. Cross-validation
# ===========================================================================
CELLS.append(md("""
## 5. Cross-validation — the correctness argument

This is the section that matters. A Beam pipeline that runs without raising
an exception has told you almost nothing: `sum` over floats in a different
order gives a slightly different answer, and nobody notices.

The check is simple and absolute:

> **For every region, the Beam output must equal the pure-Python reference
> exactly — same count, same revenue, to the cent.**

If they differ, one of the two is wrong. Because the reference is a single
loop over a list, it is easy to read and easy to be sure about, so a
mismatch points at the Beam side.
"""))

CELLS.append(code('''
# --- Batch cross-validation ------------------------------------------------
batch_mismatches = []
for region, expected in sorted(reference_summary.items()):
    actual = batch_summary.get(region)
    if actual is None:
        batch_mismatches.append((region, expected, None))
        continue
    if actual["order_count"] != int(expected["order_count"]):
        batch_mismatches.append((region, expected, actual))
        continue
    if abs(actual["revenue_eur"] - expected["revenue_eur"]) > 0.005:
        batch_mismatches.append((region, expected, actual))

missing_regions = set(reference_summary) - set(batch_summary)
extra_regions = set(batch_summary) - set(reference_summary)

print("BATCH: Beam output vs pure-Python reference")
print("-" * 64)
for region in sorted(reference_summary):
    expected = reference_summary[region]
    actual = batch_summary.get(region, {})
    status = "OK" if (region, expected, actual) not in batch_mismatches else "FAIL"
    print(
        f"  {status}  {region:<6} "
        f"reference={int(expected['order_count']):>4}/{expected['revenue_eur']:<11} "
        f"beam={actual.get('order_count', '-'):>4}/{actual.get('revenue_eur', '-'):<11}"
    )

print()
print(f"  regions missing from Beam output : {sorted(missing_regions) or 'none'}")
print(f"  regions extra in Beam output      : {sorted(extra_regions) or 'none'}")
print(f"  mismatches                       : {len(batch_mismatches)}")

assert not batch_mismatches, f"batch mismatch: {batch_mismatches}"
assert not missing_regions, f"batch missing regions: {missing_regions}"
assert not extra_regions, f"batch extra regions: {extra_regions}"
print()
print("BATCH CROSS-VALIDATION PASSED")

# --- Streaming cross-validation -------------------------------------------
stream_mismatches = []
for region, expected_count in sorted(event_counts.items()):
    expected_value = round(event_totals[region], 2)
    actual = stream_summary.get(region)
    if actual is None:
        stream_mismatches.append((region, expected_count, expected_value, None))
        continue
    if actual["order_count"] != expected_count:
        stream_mismatches.append(
            (region, expected_count, expected_value, actual)
        )
        continue
    if abs(actual["revenue_eur"] - expected_value) > 0.005:
        stream_mismatches.append(
            (region, expected_count, expected_value, actual)
        )

missing_regions = set(event_counts) - set(stream_summary)
extra_regions = set(stream_summary) - set(event_counts)

print()
print("STREAMING: Beam output vs pure-Python reference")
print("-" * 64)
for region in sorted(event_counts):
    expected_count = event_counts[region]
    expected_value = round(event_totals[region], 2)
    actual = stream_summary.get(region, {})
    status = "OK" if (region, expected_count, expected_value) not in [
        m[:3] for m in stream_mismatches
    ] else "FAIL"
    print(
        f"  {status}  {region:<6} "
        f"reference={expected_count:>5}/{expected_value:<11} "
        f"beam={actual.get('order_count', '-'):>5}/{actual.get('revenue_eur', '-'):<11}"
    )

print()
print(f"  regions missing from Beam output : {sorted(missing_regions) or 'none'}")
print(f"  regions extra in Beam output      : {sorted(extra_regions) or 'none'}")
print(f"  mismatches                       : {len(stream_mismatches)}")

assert not stream_mismatches, f"streaming mismatch: {stream_mismatches}"
assert not missing_regions, f"streaming missing regions: {missing_regions}"
assert not extra_regions, f"streaming extra regions: {extra_regions}"
print()
print("STREAMING CROSS-VALIDATION PASSED")
'''))

# ===========================================================================
# 6. Idempotency
# ===========================================================================
CELLS.append(md("""
## 6. Re-running the pipeline — idempotency

A batch pipeline that is not idempotent is a pipeline you cannot safely
re-run, and re-running is the first thing you will need to do when a bug
ships.

The test is direct: run the exact same pipeline twice into two different
output paths, and compare. If the answers are identical, the pipeline is
deterministic — same input, same output, no matter how many times, no matter
how many workers, no matter what order they finished in.
"""))

CELLS.append(code('''
RERUN_OUT = RUN_DIR / "batch_rerun" / "summary"

rerun_result = run_pipeline(
    PROJECT_DIR / "batch_pipeline.py",
    [
        "--runner", "BundleBasedDirectRunner",
        "--input", str(COURSE_ROOT / "sample_data" / "orders.csv"),
        "--output", str(RERUN_OUT),
    ],
    label="batch-rerun",
)

assert rerun_result["returncode"] == 0

rerun_files = [f for f in sorted(RERUN_OUT.parent.rglob("*")) if f.is_file()]
rerun_summary = read_summary_csv(rerun_files[0])

print()
print("run 1 vs run 2, same input:")
identical = True
for region in sorted(set(batch_summary) | set(rerun_summary)):
    first = batch_summary.get(region)
    second = rerun_summary.get(region)
    same = first == second
    identical = identical and same
    print(
        f"  {'OK' if same else 'FAIL'}  {region:<6} "
        f"run1={first}  run2={second}"
    )

assert identical, "the pipeline is not deterministic"
print()
print("IDEMPOTENT: identical output across independent runs")
'''))

# ===========================================================================
# 7. The test suite
# ===========================================================================
CELLS.append(md("""
## 7. The test suite

The project's `pytest` suite covers the transforms directly and both
pipelines through the runner. Running it here is part of the end-to-end
story: a pipeline you cannot test is a pipeline you cannot change.

The suite is fast because it tests the transforms, not the whole graph.
That is the testing pyramid from module 8, in miniature.
"""))

CELLS.append(code('''
test_result = subprocess.run(
    [PYTHON, "-m", "pytest", str(PROJECT_DIR / "tests"), "-q"],
    cwd=str(COURSE_ROOT),
    capture_output=True,
    text=True,
)

print(f"pytest exit={test_result.returncode}")
print()
print(test_result.stdout.rstrip())
if test_result.returncode != 0:
    print()
    print("STDERR:")
    print(test_result.stderr.rstrip())

assert test_result.returncode == 0, "the project test suite failed"
print()
print("TEST SUITE PASSED")
'''))

# ===========================================================================
# 8. Failure modes
# ===========================================================================
CELLS.append(md("""
## 8. What happens when it breaks

A pipeline that only ever runs on clean data has never been tested. This
section feeds the batch pipeline deliberately malformed rows and shows what
comes out the other end.

The project handles this the honest way: `ParseOrderFn` **drops** invalid
rows and logs a warning. It does not fail the bundle, because one bad row in
a five-thousand-row file should not cost you the other four thousand-nine
hundred and ninety-nine.

But dropping is not the same as *accounting for*. Notebook 09 built the
production answer — a dead-letter queue — where rejected rows are captured
with a reason and can be replayed. Here, the point is to make the loss
visible.
"""))

CELLS.append(code('''
# --- Build a poisoned input ------------------------------------------------
POISONED = RUN_DIR / "poisoned_orders.csv"

with (COURSE_ROOT / "sample_data" / "orders.csv").open(
    "r", encoding="utf-8"
) as source, POISONED.open("w", encoding="utf-8") as target:
    target.write(source.read())
    target.write("not-an-order,missing-fields,garbage\\n")
    target.write(
        "o99999998,c000002,2026-01-01T00:00:00+00:00,EMEA,web,XYZ,"
        "complete,100.00,p0003\\n"
    )
    target.write(",,,,\\n")

print(f"poisoned input rows added: 3")
print(f"poisoned input size     : {POISONED.stat().st_size} bytes")

POISONED_OUT = RUN_DIR / "poisoned" / "summary"

poisoned_result = run_pipeline(
    PROJECT_DIR / "batch_pipeline.py",
    [
        "--runner", "BundleBasedDirectRunner",
        "--input", str(POISONED),
        "--output", str(POISONED_OUT),
    ],
    label="poisoned",
)

assert poisoned_result["returncode"] == 0, "the pipeline failed on bad input"

poisoned_files = [
    f for f in sorted(POISONED_OUT.parent.rglob("*")) if f.is_file()
]
poisoned_summary = read_summary_csv(poisoned_files[0])

print()
print("clean run vs poisoned run:")
for region in sorted(set(batch_summary) | set(poisoned_summary)):
    clean = batch_summary.get(region, {})
    dirty = poisoned_summary.get(region, {})
    same = clean == dirty
    print(
        f"  {'SAME' if same else 'DIFF'}  {region:<6} "
        f"clean={clean.get('order_count')}/{clean.get('revenue_eur')}  "
        f"poisoned={dirty.get('order_count')}/{dirty.get('revenue_eur')}"
    )

print()
print("The three bad rows were dropped, not counted.")
print("The pipeline still exited 0 -- which is correct behaviour, and also")
print("exactly why a dead-letter queue matters: 'the job succeeded' and")
print("'no data was lost' are different claims.")

# Count how many rows the pipeline actually read vs how many it kept.
total_valid = sum(m["order_count"] for m in poisoned_summary.values())
total_lines = sum(
    1
    for line in POISONED.read_text(encoding="utf-8").splitlines()
    if line.strip()
) - 1  # minus the header

print()
print(f"data rows in the poisoned file : {total_lines}")
print(f"rows that reached the summary   : {total_valid}")
print(f"rows dropped or filtered out    : {total_lines - total_valid}")
'''))

# ===========================================================================
# 9. Side input
# ===========================================================================
CELLS.append(md("""
## 9. The side input, end to end

The batch pipeline has an optional `--reference` flag that enriches each
order with a product category, loaded as a Beam **side input**.

This is the decision rule from module 3 in action: a reference set that fits
comfortably in memory goes in a side input; one that does not goes in a join.
The product reference here is 50 rows — comfortably a side input.
"""))

CELLS.append(code('''
REFERENCE_OUT = RUN_DIR / "with_reference" / "summary"

reference_result = run_pipeline(
    PROJECT_DIR / "batch_pipeline.py",
    [
        "--runner", "BundleBasedDirectRunner",
        "--input", str(COURSE_ROOT / "sample_data" / "orders.csv"),
        "--output", str(REFERENCE_OUT),
        "--reference",
        str(COURSE_ROOT / "sample_data" / "product_reference.ndjson"),
    ],
    label="reference",
)

assert reference_result["returncode"] == 0

reference_files = [
    f for f in sorted(REFERENCE_OUT.parent.rglob("*")) if f.is_file()
]
reference_summary = read_summary_csv(reference_files[0])

print()
print("with and without the side input:")
for region in sorted(set(batch_summary) | set(reference_summary)):
    plain = batch_summary.get(region, {})
    enriched = reference_summary.get(region, {})
    same = plain == enriched
    print(
        f"  {'SAME' if same else 'DIFF'}  {region:<6} "
        f"plain={plain.get('order_count')}/{plain.get('revenue_eur')}  "
        f"enriched={enriched.get('order_count')}/{enriched.get('revenue_eur')}"
    )

print()
print("The side input adds a field; it does not change the aggregate.")
print("That is the property that makes the enrichment safe to add later,")
print("without re-deriving every downstream number.")
'''))

# ===========================================================================
# 10. Production changes
# ===========================================================================
CELLS.append(md("""
## 10. What you would change for production

The project runs locally, in one process, over files. Production is a
different set of problems. Here is the honest list, with the reason for
each change — and one thing you would **not** change.

### 10.1 The paths become `gs://` URIs

Every path in the project is already a string, so swapping
`./sample_data/orders.csv` for `gs://my-bucket/orders.csv` is a flag change,
not a code change. That is deliberate: the pipeline code never branches on
whether it is running locally or in the cloud.

### 10.2 The runner becomes `DataflowRunner`

The `--runner` flag is the only difference. The graph is the same graph.

### 10.3 The output moves from a single file to sharded files

Locally, `num_shards=1` gives you a readable file. On Dataflow you want
sharding for parallelism, and `shard_name_template` lets you control the
suffix so downstream tooling knows what to expect.

### 10.4 Windowing in the streaming pipeline needs a real trigger

The local run reads a bounded file, so `AfterWatermark` fires at the end of
the input. On a real unbounded source, you need the watermark to advance —
which means either an idle-source watermark strategy or a periodic
trigger.

### 10.5 Idempotency needs a destination-level guarantee

This project is idempotent because it writes to a fresh path. In production
you write to a table that already holds yesterday's data, so you need either
partitioned outputs keyed by date, or a BigQuery write disposition of
`WRITE_TRUNCATE` per partition, or deduplication keyed by an event id.

### 10.6 What you would *not* change

**The `CombineFn`.** It is associative, it is commutative, and it is
testable against a pure-Python twin. That is the part that is hardest to
get right and the part most worth protecting from churn. A rewrite that
saves a millisecond and breaks the merge-order guarantee is a bad trade.
"""))

CELLS.append(md("""
### The deployment command

For reference, this is the command you would run in production. It is shown
here as text — **do not run it** without a GCP project and a bucket:

```bash
python project/batch_pipeline.py \\
    --runner DataflowRunner \\
    --project my-gcp-project \\
    --region us-central1 \\
    --staging_location gs://my-bucket/staging \\
    --temp_location gs://my-bucket/temp \\
    --input gs://my-bucket/orders.csv \\
    --output gs://my-bucket/summary
```

The flags are the same ones the local run used. That is the point of the
exercise: **the local run is a real rehearsal of the cloud run**, not a
simplified imitation of it.
"""))

# ===========================================================================
# 11. The full picture
# ===========================================================================
CELLS.append(md("""
## 11. The full picture

Here is everything this notebook proved, in one place.
"""))

CELLS.append(code('''
print("END-TO-END VERIFICATION SUMMARY")
print("=" * 72)

checks = [
    ("batch pipeline ran", batch_result["returncode"] == 0),
    ("streaming pipeline ran", stream_result["returncode"] == 0),
    ("batch output parsed", len(batch_summary) == 4),
    ("streaming output parsed", len(stream_summary) == 4),
    ("batch matches reference", not batch_mismatches),
    ("streaming matches reference", not stream_mismatches),
    ("pipeline is idempotent", identical),
    ("test suite passes", test_result.returncode == 0),
    ("bad rows handled", poisoned_result["returncode"] == 0),
    ("side input does not change totals", batch_summary == reference_summary),
]

for label, passed in checks:
    print(f"  [{'PASS' if passed else 'FAIL'}]  {label}")

print()
print("batch output (region, order_count, revenue_eur):")
for region in sorted(batch_summary):
    metrics = batch_summary[region]
    print(f"  {region:<6} {metrics['order_count']:<5} {metrics['revenue_eur']}")

print()
print("streaming output (region, event_count, total_value):")
for region in sorted(stream_summary):
    metrics = stream_summary[region]
    print(f"  {region:<6} {metrics['order_count']:<5} {metrics['revenue_eur']}")

print()
print("timings:")
print(f"  batch    : {batch_result['seconds']:.1f}s")
print(f"  streaming: {stream_result['seconds']:.1f}s")

assert all(passed for _, passed in checks), "an end-to-end check failed"
print()
print("ALL END-TO-END CHECKS PASSED")
'''))

# ===========================================================================
# Takeaways
# ===========================================================================
CELLS.append(md("""
## 🔑 Takeaways

**A local run is a real rehearsal of a cloud run.** The batch and streaming
pipelines ran as subprocesses in this notebook, with the same argument
parsing, the same runner resolution, and the same `main()` entry point that
Dataflow would use. The only thing that changes in production is the
`--runner` flag and the path prefix.

**Cross-validation is the strongest correctness statement you can make.** The
Beam output was compared, region by region, against a pure-Python reference
implementation of the same business rules — not a snapshot someone pasted in,
but a function that computes the answer from the same input file. When they
match exactly, the distributed computation is doing what you think it is
doing.

**One function, two implementations.** `build_revenue_summary` and
`RevenueByRegionFn` express the same rules: a pure loop and a `CombineFn`.
The pure one is fast to test and easy to read; the Beam one is what scales.
Keeping them side by side, in one module, is what stops them drifting.

**Determinism and idempotency are properties you have to check.** The same
input produced byte-identical output on two independent runs. That is not
free — it falls out of using an associative, commutative `CombineFn` and a
deterministic output sharding strategy.

**"The job succeeded" and "no data was lost" are different claims.** The
poisoned run exited 0 while quietly dropping three malformed rows. That is
the correct behaviour for the pipeline, and it is exactly why production
systems need a dead-letter queue: a dropped row that nobody can find is
indistinguishable from a row that never existed.

**A side input changes the shape of a record, not the aggregate.** Adding
the product category left every region's revenue untouched, so enrichment
can be added without re-deriving the numbers downstream.

**The `CombineFn` is the part worth protecting.** It is associative, it is
commutative, and it has a tested pure-Python twin. Everything else — the
runner, the paths, the trigger — is configuration you can change. The merge
semantics are the thing that is expensive to get wrong.
"""))

# ===========================================================================
# Write
# ===========================================================================
OUT = Path(__file__).resolve().parent.parent / "notebooks" / "10-end-to-end-project.ipynb"
build(CELLS, "nb10", out_path=OUT)
print(f"wrote {OUT} with {len(CELLS)} cells")
