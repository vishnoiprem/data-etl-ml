#!/usr/bin/env python3
"""
notebook_01.py — build notebook 01, Setup & the CDC Mental Model.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_notebooks import code, md, notebook  # noqa: E402


def build() -> dict:
    """Build notebook 01.

    Returns:
        The notebook dict.
    """
    return notebook([
        md("""
# 01 · Setup & the CDC Mental Model

> **Module 1 · Foundations & Mental Model · Lecture 1.1**

In this notebook you will:

- Verify the course's Python environment and the sample data
- Build the mental model that the whole course rests on: **an immutable log of
  changes, applied to a mutable table**
- Write your first change event and apply it to a table
- See, concretely, why the merge key is the most dangerous field in a CDC
  configuration

Everything here runs with **no GCP account, no credentials and no bill**.
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

PROJECT_DIR = COURSE_ROOT / "project"
sys.path.insert(0, str(PROJECT_DIR))

print("course root :", COURSE_ROOT)
print("python      :", sys.version.split()[0])
print("project dir :", PROJECT_DIR)
"""),
        md("""
## 1. Generate the sample data

The course ships a deterministic generator. Seeded, so every run produces
byte-identical output — which is what lets the chapters quote exact numbers.
"""),
        code("""
result = subprocess.run(
    [
        sys.executable,
        str(COURSE_ROOT / "resources" / "sample_data.py"),
        "--output-dir",
        str(COURSE_ROOT / "sample_data"),
    ],
    capture_output=True,
    text=True,
)
print(result.stderr.strip().splitlines()[-2] if result.stderr else "ok")
"""),
        code("""
sample_dir = COURSE_ROOT / "sample_data"
for name in ("customers.csv", "changes.ndjson", "transactions.ndjson"):
    path = sample_dir / name
    size = path.stat().st_size
    print(f"{name:<24} {size:>8,} bytes")

summary = json.loads((sample_dir / "summary.json").read_text())
print()
print("summary:", summary)
"""),
        md("""
## 2. The mental model

Everything about change data capture follows from one distinction:

| | The log | The table |
|---|---|---|
| Shape | an append-only sequence of change events | a mutable set of rows |
| Content | what changed, with before/after images | what is true now |
| Written by | the source database, then the connector | the merge |
| Replayable | yes, always | no |

Datastream reads the source's write-ahead log and produces the **log**. It
writes change events into BigQuery, and a merge turns them into the **table**.

The single most common misunderstanding is that "the table" and "the stream"
are the same thing. They are not, and the difference is why a CDC pipeline
can be replayed, audited, and recovered from — and why a table-only pipeline
cannot.

Concretely, one row changing twice produces **two events** but the table
ends up with **one row**. If you count rows in the stream you get 2. If you
count rows in the table you get 1. Both are correct; they answer different
questions.
"""),
        code("""
from cdc import CdcState

state = CdcState(merge_keys=["customer_id"])

customer = {
    "customer_id": "c000001",
    "first_name": "Ada",
    "region": "EMEA",
    "tier": "silver",
}

print("--- 1. INSERT ---")
state.apply_event({"op": "INSERT", "after": customer})
print("rows in table :", state.row_count())
print("row           :", state.get(customer))

print()
print("--- 2. UPDATE (tier silver -> gold) ---")
updated = {**customer, "tier": "gold"}
state.apply_event({"op": "UPDATE", "before": customer, "after": updated})
print("rows in table :", state.row_count())
print("row           :", state.get(customer))
"""),
        md("""
Look at the count. Two events have been applied. The table has **one row**.
That is the whole model in one screen.
"""),
        code("""
print("events applied :", state.applied_count)
print("rows in table  :", state.row_count())
print()
print("The table always reflects the LATEST image of each key,")
print("no matter how many changes arrived on the way there.")
"""),
        md("""
## 3. DELETE

A `DELETE` carries the **before** image, not the after image — there is no
"after" state for a row that no longer exists. The merge uses the before
image to work out *which* key to remove.
"""),
        code("""
print("--- 3. DELETE ---")
state.apply_event({"op": "DELETE", "before": updated})
print("rows in table :", state.row_count())
print("row           :", state.get(customer))
"""),
        md("""
## 4. The merge key is the dangerous field

Here is the bug that costs a week.

If the merge key is **not unique**, one `UPDATE` can match several rows and
overwrite all of them. Nothing errors. The table simply becomes wrong, and
the wrongness is silent — no exception, no alert, just a dashboard that
disagrees with the source of truth.
"""),
        code("""
# A merge key that is NOT unique: "region" identifies many customers.
bad_state = CdcState(merge_keys=["region"])

for cid, region, tier in [
    ("c001", "EMEA", "silver"),
    ("c002", "EMEA", "gold"),
    ("c003", "APAC", "bronze"),
]:
    bad_state.apply_event({
        "op": "INSERT",
        "after": {"customer_id": cid, "region": region, "tier": tier},
    })

print("rows after inserts   :", bad_state.row_count())
print("expected             : 3")
print()

# An UPDATE aimed at c001 — but the merge key is "region".
bad_state.apply_event({
    "op": "UPDATE",
    "before": {"customer_id": "c001", "region": "EMEA", "tier": "silver"},
    "after": {"customer_id": "c001", "region": "EMEA", "tier": "platinum"},
})

print("rows after update    :", bad_state.row_count())
for row in bad_state.snapshot():
    print("   ", row)
"""),
        md("""
**c002 was overwritten.** The merge matched on `region = EMEA`, found two
rows, and applied the update to both — so the row for `c002` now carries
`c001`'s new tier. The row count did not change, so nothing looks wrong.

This is the failure mode the merge key guards against. The fix is always the
same: use the source table's **primary key**.

The general rule, and the one to take to an interview:

> The merge key must be the smallest set of columns that uniquely identifies
> a row in the source table. Usually that is the primary key. Never a
> non-unique column, and never a column that can change — a mutable merge
> key breaks the merge in a way that is very hard to diagnose, because the
> row's key changes underneath the merge.
"""),
        code("""
# Proof that the row count did not change — the bug is invisible to a count.
print("Row count before and after the bad update is identical:", 3)
print()
print("The damage shows up in the VALUES, not the counts.")
print("A count-based smoke test would never have caught this.")
"""),
        md("""
## 5. A composite merge key

Sometimes the primary key is more than one column — a tenant id plus a
customer id, for example. That is fine, and it is why Datastream's merge
key configuration is a *list*.
"""),
        code("""
state = CdcState(merge_keys=["tenant_id", "customer_id"])

state.apply_event({"op": "INSERT", "after": {"tenant_id": "t1", "customer_id": "c1", "v": 1}})
state.apply_event({"op": "INSERT", "after": {"tenant_id": "t2", "customer_id": "c1", "v": 2}})

print("rows :", state.row_count())
print("t1/c1:", state.get({"tenant_id": "t1", "customer_id": "c1"}))
print("t2/c1:", state.get({"tenant_id": "t2", "customer_id": "c1"}))
"""),
        md("""
## What to take away

- A CDC pipeline is **an immutable log of changes, applied to a mutable table**.
- Two changes to one row produce two events and one table row.
- The merge key is how a change is matched to a row. Get it wrong and the
  table is silently wrong.
- The merge key must be **unique and immutable** — the source's primary key.
"""),
    ])


if __name__ == "__main__":
    from build_notebooks import NOTEBOOKS  # noqa: F401

    out = Path(sys.argv[1]) if len(sys.argv) > 1 else NOTEBOOKS / "01-setup-and-cdc-mental-model.ipynb"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(build(), indent=1) + "\n", encoding="utf-8")
    print(f"wrote {out}")
