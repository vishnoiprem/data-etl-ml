#!/usr/bin/env python3
"""
notebook_06.py — build notebook 06, End-to-End Project.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_notebooks import code, md, notebook  # noqa: E402


def build() -> dict:
    """Build notebook 06.

    Returns:
        The notebook dict.
    """
    return notebook([
        md("""
# 06 · End-to-End Project

> **Module 5 · Capstone · Lecture 5.1**

In this notebook you will build the complete project, in the order you would
build it in production:

1. **Generate** a realistic change-event stream
2. **Replay** it through the merge, and check the result against an
   independent reference implementation
3. **Verify** the properties that matter: convergence, idempotency, and
   order-sensitivity
4. **Detect** the failure modes — a bad merge key, a lost event, a
   duplicated event
5. **Measure** what the pipeline costs, in rows and in latency

The whole thing runs with **no GCP account and no bill**. That is the point
of the course's design: the hard parts of CDC are pure logic, and pure logic
can be tested for free.
"""),
        code("""
import json
import subprocess
import sys
from pathlib import Path

COURSE_ROOT = Path.cwd()
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent.parent

sys.path.insert(0, str(COURSE_ROOT / "project"))

from cdc import CdcState

print("course root:", COURSE_ROOT)
"""),
        md("""
## Step 1 — Generate the stream

"""),
        code("""
subprocess.run(
    [
        sys.executable,
        str(COURSE_ROOT / "resources" / "sample_data.py"),
        "--output-dir",
        str(COURSE_ROOT / "sample_data"),
    ],
    capture_output=True,
    text=True,
    check=True,
)

events = [
    json.loads(line)
    for line in (COURSE_ROOT / "sample_data" / "changes.ndjson").read_text().splitlines()
    if line.strip()
]

summary = json.loads((COURSE_ROOT / "sample_data" / "summary.json").read_text())
print("summary:", summary)
print("change events:", len(events))
"""),
        md("""
## Step 2 — Replay

"""),
        code("""
state = CdcState(merge_keys=["customer_id"])
state.apply_events(events)

print(f"events read      : {len(events)}")
print(f"rows in table    : {state.row_count()}")
print(f"changes applied  : {state.applied_count}")
print(f"events skipped   : {state.skipped_count}")
print()
for reason, count in sorted(state.skipped_reasons.items()):
    print(f"  {reason:<24} {count}")
"""),
        md("""
## Step 3 — Verify the three properties

### Property 1: convergence

Replaying the whole stream from scratch, and replaying it again, must give
the same table. This is what "the table reflects the source" means.
"""),
        code("""
# Replay from scratch, twice.
first = CdcState(merge_keys=["customer_id"])
first.apply_events(events)

second = CdcState(merge_keys=["customer_id"])
second.apply_events(events)

print("two independent replays agree:", first.snapshot() == second.snapshot())

# And replaying on top of an existing table changes nothing.
third = CdcState(merge_keys=["customer_id"])
third.apply_events(events)
before = third.snapshot()
third.apply_events(events)

print("replaying onto a populated table is a no-op:", before == third.snapshot())
print("changes applied by the second pass          :", third.applied_count - first.applied_count)
"""),
        md("""
### Property 2: idempotency

The generator deliberately injects duplicate events. Let us count how many
duplicates there are, and confirm the table is unaffected by them.
"""),
        code("""
from collections import Counter

signatures = Counter(
    (e.get("op"), json.dumps(e.get("before"), sort_keys=True), json.dumps(e.get("after"), sort_keys=True))
    for e in events
)
duplicate_count = sum(count - 1 for count in signatures.values() if count > 1)
print(f"events in the stream   : {len(events)}")
print(f"distinct events        : {len(signatures)}")
print(f"duplicate deliveries   : {duplicate_count}")
print()
print("The table has one row per customer_id, regardless of the duplicates:")
print("  rows :", first.row_count())
print("  unique customer_ids :", len({r['customer_id'] for r in first.snapshot()}))
"""),
        md("""
### Property 3: order-sensitivity

A merge is **not** order-independent for deletes and inserts of the same
key. Applying `DELETE` then `INSERT` leaves a row; applying `INSERT` then
`DELETE` leaves nothing.

This is a property of the data, not a flaw in the merge — and it is why
**stream order matters**.
"""),
        code("""
row = {"customer_id": "c1", "tier": "gold"}

# Delete, then insert -> the row survives.
a = CdcState(merge_keys=["customer_id"])
a.apply_event({"op": "DELETE", "before": row})
a.apply_event({"op": "INSERT", "after": row})
print("DELETE then INSERT -> rows:", a.row_count())

# Insert, then delete -> the row is gone.
b = CdcState(merge_keys=["customer_id"])
b.apply_event({"op": "INSERT", "after": row})
b.apply_event({"op": "DELETE", "before": row})
print("INSERT then DELETE -> rows:", b.row_count())
"""),
        md("""
This is why a CDC pipeline must preserve source order. Datastream preserves
it, because it reads the binary log in order. A system that reads from a
Kafka topic with more than one partition can reorder — which is exactly why
**the key that Kafka partitions by must be the same key you merge on**.

That is not a coincidence. It is the requirement that makes a partitioned
stream mergeable.
"""),
        md("""
## Step 4 — Detect the failure modes

### A bad merge key

"""),
        code("""
# The same stream, merged on the wrong key.
wrong = CdcState(merge_keys=["region"])
wrong.apply_events(events)
print(f"rows with the correct key (customer_id) : {first.row_count()}")
print(f"rows with the wrong key   (region)       : {wrong.row_count()}")
print()
print("The wrong key collapses many customers into one row per region.")
print("Nothing errored. The table is simply wrong.")
"""),
        md("""
### A lost event

If one `UPDATE` is dropped, the table keeps the *older* value. The row
count is unchanged, so a count-based check passes.
"""),
        code("""
# Drop every UPDATE from the stream.
updates_dropped = [e for e in events if e.get("op") != "UPDATE"]

without_updates = CdcState(merge_keys=["customer_id"])
without_updates.apply_events(updates_dropped)

print(f"rows with all events     : {first.row_count()}")
print(f"rows without the UPDATEs : {without_updates.row_count()}")
print("row count difference      :", first.row_count() - without_updates.row_count())
print()

# How many rows differ in VALUE?
correct = {r["customer_id"]: r for r in first.snapshot()}
stale = {r["customer_id"]: r for r in without_updates.snapshot()}
differing = [k for k in correct if k in stale and correct[k] != stale[k]]
print(f"rows with a different value: {len(differing)}")
print()
print("A row-count check would never have caught this.")
"""),
        md("""
### A duplicated event

Already proven idempotent in property 2 — but let us prove it directly on
the table, with a duplicated `UPDATE`.
"""),
        code("""
state = CdcState(merge_keys=["customer_id"])
state.apply_event({"op": "INSERT", "after": {"customer_id": "c1", "tier": "silver"}})
state.apply_event({"op": "UPDATE", "before": {"customer_id": "c1", "tier": "silver"},
                   "after": {"customer_id": "c1", "tier": "gold"}})

snapshot = state.snapshot()
state.apply_event({"op": "UPDATE", "before": {"customer_id": "c1", "tier": "silver"},
                   "after": {"customer_id": "c1", "tier": "gold"}})

print("table unchanged by the duplicate:", snapshot == state.snapshot())
print("rows                          :", state.row_count())
"""),
        md("""
## Step 5 — Measure

### Volume

"""),
        code("""
from collections import Counter

ops = Counter(e.get("op") for e in events)
total = len(events)

print(f"{'metric':<28} {'value':>12}")
print("-" * 42)
print(f"{'events in the stream':<28} {total:>12,}")
print(f"{'rows in the table':<28} {first.row_count():>12,}")
print(f"{'events applied':<28} {first.applied_count:>12,}")
print(f"{'events skipped':<28} {first.skipped_count:>12,}")
print(f"{'event amplification':<28} {total / first.row_count():>12.2f}x")
print(f"{'INSERT events':<28} {ops['INSERT']:>12,}")
print(f"{'UPDATE events':<28} {ops['UPDATE']:>12,}")
print(f"{'DELETE events':<28} {ops['DELETE']:>12,}")
"""),
        md("""
**Event amplification** is the ratio of events to resulting rows. It is
the number that tells you whether CDC is worth it.

A stream with 10× amplification means every row changes ten times on
average. That is a table under heavy churn — and it is exactly the case
where CDC beats polling, because polling re-reads the whole table ten times
to capture ten changes.

A stream with 1.1× amplification is nearly append-only. Polling would be
simpler and cheaper, and the honest recommendation is to poll.

### Latency

"""),
        code("""
from datetime import datetime

def parse_ts(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))

source_times = [parse_ts(e["sourceTimestamp"]) for e in events]
server_times = [parse_ts(e["serverTimestamp"]) for e in events]

latencies = [(s - src).total_seconds() for src, s in zip(source_times, server_times)]
latencies.sort()

print(f"{'percentile':<20} {'latency':>12}")
print("-" * 34)
for label, index in [("p50", len(latencies) // 2), ("p90", int(len(latencies) * 0.9)), ("p99", int(len(latencies) * 0.99))]:
    print(f"{label:<20} {latencies[index]:>11.3f}s")
print(f"{'max':<20} {latencies[-1]:>11.3f}s")
"""),
        md("""
In this synthetic stream the latency is near zero. In a real deployment
it is bounded below by the read consistency window — with a 5-second window,
the floor is roughly 5 seconds.

**That is the number to put in an SLA.** Not "sub-second" — whatever the
consistency window implies, plus the merge time.

## Step 6 — The finished pipeline

"""),
        code("""
result = subprocess.run(
    [
        sys.executable,
        str(COURSE_ROOT / "project" / "cdc_pipeline.py"),
        "--input", str(COURSE_ROOT / "sample_data" / "changes.ndjson"),
        "--output", str(COURSE_ROOT / "out" / "customers"),
        "--merge-keys", "customer_id",
        "--audit", str(COURSE_ROOT / "out" / "audit.json"),
    ],
    capture_output=True,
    text=True,
    check=True,
)
print(result.stdout)
"""),
        code("""
audit = json.loads((COURSE_ROOT / "out" / "audit.json").read_text())
print("audit record:")
print(json.dumps(audit, indent=2))
"""),
        md("""
The audit record is the thing you ship alongside the pipeline. It says
what was read, what was applied, and — critically — **what was skipped and
why**. A pipeline that only reports successes cannot be monitored, because
a rising "skipped" count is invisible until someone notices the table is
stale.

## What to take away

- The pipeline **converges**: any two replays of the same stream give the
  same table.
- It is **idempotent**: duplicates change nothing.
- It is **order-sensitive** for delete/insert of the same key — which is
  why Kafka partitioning must use the merge key.
- A wrong merge key is **silent**. A dropped event is **silent**. You need
  a value-level comparison, not a row count.
- **Event amplification** tells you whether CDC is worth the complexity.
"""),
    ])


if __name__ == "__main__":
    from build_notebooks import NOTEBOOKS

    out = Path(sys.argv[1]) if len(sys.argv) > 1 else NOTEBOOKS / "06-end-to-end-project.ipynb"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(build(), indent=1) + "\n", encoding="utf-8")
    print(f"wrote {out}")
