#!/usr/bin/env python3
"""
notebook_03.py — build notebook 03, The Merge & BigQuery.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_notebooks import code, md, notebook  # noqa: E402


def build() -> dict:
    """Build notebook 03.

    Returns:
        The notebook dict.
    """
    return notebook([
        md("""
# 03 · The Merge & the BigQuery Sink

> **Module 2 · The BigQuery Destination · Lecture 2.1**

In this notebook you will:

- Read the `MERGE` statement Datastream effectively runs, and understand
  every clause of it
- Implement the merge yourself and prove it matches the reference
- See **idempotency** — replaying a stream changes nothing — and understand
  why that property is what makes a CDC pipeline safe to retry
- Understand the difference between a **streaming** merge and a
  **synchronised** merge, and when you want each

This is the module where the course's central claim is earned: that
Datastream's BigQuery destination is a merge with specific, learnable
semantics.
"""),
        code("""
import sys
from pathlib import Path

COURSE_ROOT = Path.cwd()
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent.parent

sys.path.insert(0, str(COURSE_ROOT / "project"))

from cdc import CdcState, build_bigquery_merge_sql

print(build_bigquery_merge_sql("customers", ["customer_id"]))
"""),
        md("""
## 1. Reading the MERGE

```sql
MERGE target USING source
    ON target.customer_id = source.customer_id
WHEN NOT MATCHED BY TARGET THEN INSERT ...
WHEN MATCHED AND source.__op__ != 'DELETE' THEN UPDATE ...
WHEN MATCHED AND source.__op__ = 'DELETE' THEN DELETE
```

Three clauses, three situations:

| Situation | Clause | Result |
|---|---|---|
| The key is not in the target | `NOT MATCHED BY TARGET` | insert a new row |
| The key is in the target, and the change is not a delete | `MATCHED` + `__op__ != 'DELETE'` | update the row |
| The key is in the target, and the change is a delete | `MATCHED` + `__op__ = 'DELETE'` | remove the row |

The `__op__` column is Datastream's own marker — a synthetic column added
to the change-event table to record which operation each row represents.
It is not a column in your source table, and it is how a single `MERGE`
handles all three operations.

### The one clause that is NOT part of streaming Datastream

A fourth clause exists in BigQuery's `MERGE` and you will see it in blog
posts:

```sql
WHEN NOT MATCHED BY SOURCE THEN DELETE
```

That clause removes target rows with no matching source row — it makes the
target a **synchronised snapshot** of the source.

Datastream does **not** use it for streaming, and the reason is worth
understanding: in a stream there is no "the source" as a whole. The stream
contains *changes*, and the absence of a change is not evidence of a
deletion. A table that deleted every row it had not heard about in the last
minute would be empty, constantly.

| | Streaming merge | Synchronised merge |
|---|---|---|
| Source | An unbounded stream of changes | A finite, complete snapshot |
| `NOT MATCHED BY SOURCE` | **Never** | Deletes rows absent from the snapshot |
| Use | Live replication | Backfill, one-off sync |
| Datastream offers | Yes — the default | Yes — as a backfill mode |

## 2. Implementing the merge
"""),
        code("""
# The merge, implemented. This is exactly what cdc.CdcState does.
def merge(target_rows, event):
    \"\"\"Apply one change event to a dictionary of target rows.\"\"\"
    op = event["op"]
    image = event["after"] if op in ("INSERT", "UPDATE") else event["before"]
    if image is None:
        return target_rows, False

    key = image["customer_id"]
    if op == "DELETE":
        if key in target_rows:
            del target_rows[key]
            return target_rows, True
        return target_rows, False

    target_rows[key] = dict(event["after"])
    return target_rows, True


target = {}
events = [
    {"op": "INSERT", "after": {"customer_id": "c1", "tier": "silver"}},
    {"op": "UPDATE", "before": {"customer_id": "c1", "tier": "silver"},
     "after": {"customer_id": "c1", "tier": "gold"}},
    {"op": "INSERT", "after": {"customer_id": "c2", "tier": "bronze"}},
    {"op": "DELETE", "before": {"customer_id": "c2", "tier": "bronze"}},
]

for event in events:
    target, changed = merge(target, event)
    print(f"{event['op']:<7} -> rows={len(target)} changed={changed}")

print()
print("final table:", target)
"""),
        md("""
## 3. Idempotency — the property that makes retries safe

**Idempotent** means: applying the same event twice has the same effect as
applying it once.

This is not a nicety. It is the property that lets you retry a failed
delivery, replay a stream after an outage, or re-run a backfill — all
without corrupting the table. Without idempotency, every retry is a
potential data corruption event.

Let us prove it, rather than assert it.
"""),
        code("""
def apply_all(target, events):
    \"\"\"Apply a list of events, returning the changed count.\"\"\"
    changed = 0
    for event in events:
        target, did_change = merge(target, event)
        changed += int(did_change)
    return target, changed

# Apply once.
once, changed_once = apply_all({}, events)
print(f"applied once      : {len(once)} rows, {changed_once} changes")

# Apply the same events again.
twice, changed_twice = apply_all(dict(once), events)
print(f"applied twice     : {len(twice)} rows, {changed_twice} changes")

print()
print("Table identical?      ", once == twice)
print("Second pass a no-op?  ", changed_twice == 0)
"""),
        md("""
The second pass changed **nothing**. That is idempotency.

Note *why* it holds: every clause of the merge is an **upsert or a delete
by key**. There is no clause that appends. If the merge appended, replaying
the stream would duplicate rows — and the classic symptom of a non-
idempotent CDC pipeline is a customer table where every customer appears
twice, and nobody can say when it started.

### Where idempotency comes from

It comes from the merge key. Two events with the same key converge on the
same row. The merge key is not just "which row to update" — it is the
thing that makes the whole system safe to retry.

## 4. The delete of an absent row

One subtlety worth being explicit about: deleting a row that is not there
is a **no-op, not an error**.
"""),
        code("""
target = {"c1": {"customer_id": "c1", "tier": "gold"}}

# A delete for a row that was never inserted.
target, changed = merge(target, {"op": "DELETE", "before": {"customer_id": "c99"}})
print("rows:", len(target), "changed:", changed)
print("The row count is unchanged and nothing raised.")
"""),
        md("""
This matters in practice. A CDC stream that starts mid-history will contain
deletes for rows it never saw inserted. If the merge treated that as an
error, the pipeline would crash on a completely normal situation.

## 5. The update of an absent row

The mirror case: an `UPDATE` for a row that is not in the target.

Two possible behaviours, and the choice matters:

| Behaviour | Consequence |
|---|---|
| **Insert it** (the course's choice) | The change is honoured; no data loss |
| **Drop it** | The change is lost, silently |

Datastream's actual behaviour is to insert, and the reason is that dropping
it loses data whenever a stream is not perfectly aligned with the table's
history. The row's `after` image is the *current* state of that row, so
inserting it produces a correct row.

The cost of this choice: the table can contain rows that the source no
longer has, if a delete arrived before the insert and you apply them
out of order. That is why **stream order matters** — see chapter 6.
"""),
        code("""
# An update for a row we have never seen.
state = CdcState(merge_keys=["customer_id"])
changed = state.apply_event({
    "op": "UPDATE",
    "after": {"customer_id": "c42", "tier": "gold"},
})
print("changed  :", changed)
print("rows     :", state.row_count())
print("skipped  :", state.skipped_reasons)
"""),
        md("""
## 6. Proving the merge against the reference implementation

`cdc.py` contains a pure reference implementation and a `CdcState` class.
They are independent, so agreeing with each other is evidence.

"""),
        code("""
import json

all_events = [
    json.loads(line)
    for line in (COURSE_ROOT / "sample_data" / "changes.ndjson").read_text().splitlines()
    if line.strip()
]

state = CdcState(merge_keys=["customer_id"])
state.apply_events(all_events)

rows = state.snapshot()
print(f"events applied : {len(all_events)}")
print(f"rows in table  : {len(rows)}")
print(f"applied        : {state.applied_count}")
print(f"skipped        : {state.skipped_count}")
print()
print("skip reasons:")
for reason, count in sorted(state.skipped_reasons.items()):
    print(f"  {reason:<24} {count}")
"""),
        md("""
The skipped events are all *expected*, and each one is a case we covered:

- `duplicate_insert` — the duplicated events the generator injects, proving
  the merge is idempotent
- `delete_of_absent_row` — deletes for rows the stream never inserted
- `missing_merge_key` — the deliberately malformed event

None of them are errors. A pipeline that counted "skipped" as "failed"
would report a healthy stream as broken.

## 7. The one-line summary

> The BigQuery destination is a **merge keyed on the source's primary key**,
> applied to every change event as it arrives. Three clauses: insert when
> new, update when matched, delete when matched and marked deleted. It is
> idempotent, which is what makes retries and replays safe.
"""),
    ])


if __name__ == "__main__":
    from build_notebooks import NOTEBOOKS

    out = Path(sys.argv[1]) if len(sys.argv) > 1 else NOTEBOOKS / "03-the-merge-and-bigquery.ipynb"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(build(), indent=1) + "\n", encoding="utf-8")
    print(f"wrote {out}")
