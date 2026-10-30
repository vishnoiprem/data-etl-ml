#!/usr/bin/env python3
"""
notebook_02.py — build notebook 02, Change Events, Schema & Types.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_notebooks import code, md, notebook  # noqa: E402


def build() -> dict:
    """Build notebook 02.

    Returns:
        The notebook dict.
    """
    return notebook([
        md("""
# 02 · Change Events, Schema & Types

> **Module 1 · Foundations & Mental Model · Lecture 1.2**

In this notebook you will:

- Read a real change-event stream from the sample data
- Understand the **Datastream event envelope** and where each piece comes from
- See how a column's type changes ripple through a CDC pipeline
- Handle the three schema-evolution cases that actually bite: a new column, a
  dropped column, and a **changed type**

The lesson that matters: **the source schema is not fixed**. A CDC pipeline
that survives contact with production is one that has decided, in advance,
what happens when the source changes.
"""),
        code("""
import json
import sys
from collections import Counter
from pathlib import Path

COURSE_ROOT = Path.cwd()
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent.parent

sys.path.insert(0, str(COURSE_ROOT / "project"))

events = [
    json.loads(line)
    for line in (COURSE_ROOT / "sample_data" / "changes.ndjson").read_text().splitlines()
    if line.strip()
]
print("change events loaded:", len(events))
"""),
        md("""
## 1. The event envelope

Every change event carries the same set of fields. Datastream's wire format
nests the row images under `data`; the course's sample data uses the
flattened form, which is what you get once a payload is extracted from a
Kafka message.
"""),
        code("""
sample = events[0]
print(json.dumps(sample, indent=2))
"""),
        code("""
# The fields, and what each one is for.
FIELDS = {
    "op": "The operation: INSERT, UPDATE or DELETE.",
    "before": "The row image before the change. Null for INSERT.",
    "after": "The row image after the change. Null for DELETE.",
    "sourceTimestamp": "When the SOURCE DATABASE committed the change.",
    "serverTimestamp": "When DATASTREAM observed the change.",
}

for field, description in FIELDS.items():
    print(f"{field:<16} {description}")
"""),
        md("""
### The two timestamps are not the same thing, and the difference is a latency budget

`sourceTimestamp` is when the source database committed the transaction.
`serverTimestamp` is when Datastream saw it. The gap between them is your
**end-to-end replication latency**, and it is the number you put in an SLA.

```text
  source DB commits          Datastream observes          BigQuery merges
        |                            |                            |
        v                            v                            v
   sourceTimestamp             serverTimestamp                   |
        |<---------- replication latency ---------->|             |
        |<------------------ end-to-end latency ------------------>|
```

The gap is almost always dominated by the **read consistency window** — how
long Datastream waits before reading a transaction's changes to make sure
they are all visible. That is the knob, and chapter 4 covers it.
"""),
        code("""
from datetime import datetime

def parse_ts(value):
    text = value.replace("Z", "+00:00")
    return datetime.fromisoformat(text)

latencies = []
for event in events:
    source_ts = parse_ts(event["sourceTimestamp"])
    server_ts = parse_ts(event["serverTimestamp"])
    latencies.append((server_ts - source_ts).total_seconds())

print(f"events with a measurable latency : {len(latencies)}")
print(f"min latency  : {min(latencies):.3f}s")
print(f"max latency  : {max(latencies):.3f}s")
print(f"mean latency : {sum(latencies) / len(latencies):.3f}s")
"""),
        md("""
In this synthetic stream the latency is near-zero because the generator
writes both timestamps at the same moment. In a real deployment it is
seconds, not milliseconds, and it is the number your stakeholders will ask
about.

## 2. The operation distribution
"""),
        code("""
counts = Counter(event.get("op") for event in events)
total = len(events)

print(f"{'operation':<10} {'count':>8} {'share':>8}")
print("-" * 28)
for op, count in counts.most_common():
    print(f"{op:<10} {count:>8,} {count / total * 100:>7.1f}%")
"""),
        md("""
Real-world ratios are informative. A table where 80% of events are
`INSERT` and 5% are `UPDATE` is an append-only log masquerading as a table,
and CDC is the wrong tool for it — a simple batch extract would be cheaper.
CDC earns its cost when updates and deletes are frequent, because that is
the case where incremental replication actually saves work.

## 3. Before and after images

The `before` image is what makes CDC auditable. It is also the only reason
a `DELETE` can be applied: there is no "after" state for a row that no
longer exists, so the merge uses the `before` image to work out the key.
"""),
        code("""
updates = [e for e in events if e.get("op") == "UPDATE"]
print("updates:", len(updates))
print()
print("The first update, showing what changed:")
print(json.dumps(updates[0], indent=2))
"""),
        code("""
# Which columns actually change in an update?
changed_columns = Counter()
for event in updates:
    before = event.get("before") or {}
    after = event.get("after") or {}
    for column in set(before) | set(after):
        if before.get(column) != after.get(column):
            changed_columns[column] += 1

print(f"{'column':<16} {'times changed':>14}")
print("-" * 32)
for column, count in changed_columns.most_common():
    print(f"{column:<16} {count:>14,}")
"""),
        md("""
## 4. Schema evolution — the three cases that bite

### Case 1: a new column appears

The source adds a column. New events carry it; old events do not.

Datastream's behaviour: the destination table gains the column, and rows
written before the change have `NULL` in it. That is the correct and
expected outcome — **the historical rows genuinely do not have a value for
the new column**, and inventing one would be a lie.

"""),
        code("""
# Simulate a schema change: a new column appears mid-stream.
state_events = [
    {"op": "INSERT", "after": {"customer_id": "c1", "name": "Ada"}},
    {"op": "UPDATE", "before": {"customer_id": "c1", "name": "Ada"},
     "after": {"customer_id": "c1", "name": "Ada", "loyalty_tier": "gold"}},
]

for event in state_events:
    print(event["op"], "->", event["after"])
"""),
        md("""
The first row has no `loyalty_tier`. The second has it. When merged into a
table, the first row's `loyalty_tier` is `NULL`.

### Case 2: a column is dropped

The source removes a column. New events simply do not carry it.

This is the case that **breaks naive pipelines**. A consumer that expects
every column to be present crashes with a `KeyError` — and in a streaming
consumer, a crash usually means the message is retried forever, or dropped
silently.

The rule: **never index a row image with `row["column"]` when the column
could be absent.** Use `.get()`.
"""),
        code("""
event_without_column = {"op": "INSERT", "after": {"customer_id": "c2", "name": "Grace"}}

# The bug:
try:
    _ = event_without_column["after"]["loyalty_tier"]
except KeyError as exc:
    print("KeyError:", exc, " <- this is the crash")

# The fix:
print("value:", event_without_column["after"].get("loyalty_tier"))
"""),
        md("""
### Case 3: a column's type changes — the dangerous one

The source changes `amount` from `INT` to `DECIMAL`, or from `VARCHAR` to
`INT`.

This is the case that breaks pipelines, because it breaks them **in the
middle of a stream**. Events before the change carry one representation;
events after it carry another. A consumer with a fixed schema will either
reject the new events or silently coerce them.

There are exactly three defensible responses:

| Response | When it is right |
|---|---|
| **Widen the destination column** | The new type is compatible — `INT` to `DECIMAL` |
| **Create a new column, keep the old** | The semantics changed — you want both histories |
| **Add a new stream / new table** | The change is breaking and you need a migration window |

What is *not* acceptable is letting the pipeline decide. A type change
handled silently produces a table where old rows are strings and new rows
are numbers, and every downstream query that assumes a type fails — usually
weeks later, in a dashboard nobody remembers building.
"""),
        code("""
# The failure mode, concretely.
def naive_total(rows):
    # The naive consumer: assumes every value is a number.
    total = 0
    for row in rows:
        total += row["amount"]   # TypeError if the value is a string
    return total

mixed = [
    {"amount": 100},
    {"amount": 250},
    {"amount": "99.50"},   # the source changed the type mid-stream
]

try:
    naive_total(mixed)
except TypeError as exc:
    print("TypeError:", exc)
"""),
        code("""
# The fix: coerce explicitly, and decide what a bad value means.
from decimal import Decimal, InvalidOperation

def coerce_amount(value):
    \"\"\"Return a Decimal, or None when the value cannot be read.\"\"\"
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None

total = Decimal("0")
rejected = 0
for row in mixed:
    amount = coerce_amount(row["amount"])
    if amount is None:
        rejected += 1
        continue
    total += amount

print(f"total    : {total}")
print(f"rejected : {rejected}")
"""),
        md("""
Coercing explicitly means you decide what happens to a value you cannot
read — and you **count** it. A rejected value that is counted is a data
quality signal. A rejected value that raises is an outage. A rejected value
that is silently dropped is a lie you will discover in a quarter-end report.

## 5. The rule, stated once

> Treat every row image as a **partial** record. Columns may be absent,
> because the schema changed. Types may differ between events, because the
> schema changed. Code that assumes otherwise is code that breaks on a
> Tuesday afternoon, in a stream you did not write.
"""),
    ])


if __name__ == "__main__":
    from build_notebooks import NOTEBOOKS

    out = Path(sys.argv[1]) if len(sys.argv) > 1 else NOTEBOOKS / "02-change-events-and-schema.ipynb"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(build(), indent=1) + "\n", encoding="utf-8")
    print(f"wrote {out}")
