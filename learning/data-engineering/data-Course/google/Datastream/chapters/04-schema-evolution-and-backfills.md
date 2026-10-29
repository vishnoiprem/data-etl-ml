# 4.1 — Schema Evolution and Backfills

> **Section 4 · Operations & Recovery · Lecture 4.1 · 28 min**

## 🎯 What you will learn

- The three schema-evolution cases, and the correct response to each
- Why a `NULL` in a newly-added column is correct, and not a bug
- Backfill: what it does, why you almost always want `--backfill-all`, and
  when you do not
- The three backfill modes, and the one that is dangerous
- How to recover a corrupted destination table from the log

---

## 🧠 Concept

### The source schema is not fixed

This is the fact that separates a CDC pipeline that works from one that
works until the first schema change. A source database is not a contract
you can rely on — it changes, and it changes on a Tuesday, without notice,
because someone needed a new column.

A CDC pipeline must handle three cases:

| Case | What happens | Correct response |
|---|---|---|
| **New column** | Events after the change carry it; earlier events do not | Add the column, let old rows be `NULL` |
| **Dropped column** | Events after the change omit it | Stop reading it; keep or drop the destination column |
| **Changed type** | Events before and after carry different types | Widen, or version into a new column |

### Why `NULL` is the right answer for a new column

When a column is added, the rows written before the change have no value
for it. `NULL` is the honest representation.

Inventing a value — a default, a zero, the current timestamp — is a lie
that propagates. A dashboard averaging `loyalty_tier_score` over all
customers would include thousands of fabricated zeros, and the average
would be wrong in a way nobody could explain.

The exception: if the column is genuinely `NOT NULL` with a default in the
source, the source's own log records the default in the `after` image.
There is no ambiguity. The `NULL` only appears for rows that genuinely
predate the column.

### The dangerous case: a changed type

`INT` to `DECIMAL`, `VARCHAR` to `INT`, `TIMESTAMP` to `STRING`. The
stream now contains a mix.

A consumer with a fixed schema will either reject the new events or
silently coerce them. Neither is acceptable, because neither is a decision
anyone made.

There are exactly three defensible responses:

| Response | When it is right | Cost |
|---|---|---|
| **Widen the destination column** | The new type is compatible — `INT` to `DECIMAL` | None. The column accepts both. |
| **New column, keep the old** | The semantics changed — you want both histories | A migration, and a period where the two disagree |
| **A new stream or table** | The change is breaking and you need a migration window | The most work, and the safest |

What is not acceptable is **letting the pipeline decide**. A type change
handled silently produces a table where old rows are strings and new rows
are numbers, and every query that assumes a type fails — usually weeks
later, in a dashboard nobody remembers building.

### The rule

> Treat every row image as a **partial** record. Columns may be absent
> and types may differ, because the schema changed.

```python
# wrong — crashes when the column is absent
value = row["amount"]

# right — and count what you could not read
value = row.get("amount")
if value is None:
    rejected += 1
```

The second half is the important half. A rejected value that is
**counted** is a data quality signal. A rejected value that **raises** is
an outage. A rejected value that is **silently dropped** is a lie you find
in a quarter-end report.

### Backfill

A backfill copies the **existing contents** of the source table into the
destination before the stream starts.

```bash
gcloud datastream streams create main-stream \
    --location=us-central1 \
    --source=mysql-source \
    --destination=bigquery-destination \
    --backfill-all
```

Without a backfill, the destination table starts empty and fills up only
with changes that happen *after* the stream starts. Your table is missing
every row that existed before. This is almost never what you want, and it
is a confusing first run — the table looks like it is working, and it is
missing 99% of the data.

#### The three backfill modes

| Mode | What it does | When to use |
|---|---|---|
| `backfill-all` | Copy the table's current contents, then stream changes | **The default choice.** The table starts correct. |
| `backfill-none` | Stream changes only, from now | The destination already has the data, or the table is genuinely empty. |
| `backfill-config` | Copy the contents, with a filter and a column mapping | The source table has columns you do not want, or you are backfilling a subset. |

#### Why the backfill and the stream must agree

The backfill copies a **snapshot**. The stream delivers **changes that
happened after the snapshot**. The two must be consistent, or you get
either lost updates or duplicates.

This is a genuine race, and it is why Datastream coordinates them: the
snapshot is taken at a point in the log, and the stream resumes from
exactly that point. Everything before the snapshot is in the backfill;
everything after it is in the stream. Nothing is lost, and nothing is
applied twice.

**This is why the destination must be empty before a backfill.** If the
destination already has rows, the backfill's snapshot and the existing
rows will conflict, and you get duplicates that no merge can fix — because
the merge has no way to know which copy is correct.

### Recovery: rebuilding the table from the log

The log is the source of truth. If the destination is corrupted, you
rebuild it:

```text
  1. Stop the stream.                      (so nothing new arrives)
  2. Truncate or drop the destination table.
  3. Recreate the table with the same schema.
  4. Restart the stream with --backfill-all.
```

Step 4 re-copies the current table contents and resumes the stream from
the log position. The result is a correct table.

The window where the stream is stopped means changes are not lost — they
are in the log, and the stream resumes from where it left off.

---

## 🛠️ Hands-On: Schema Evolution

### A new column appears

```python
from cdc import CdcState

state = CdcState(merge_keys=["customer_id"])

state.apply_event({"op": "INSERT", "after": {"customer_id": "c1", "name": "Ada"}})
state.apply_event({"op": "UPDATE",
                   "before": {"customer_id": "c1", "name": "Ada"},
                   "after": {"customer_id": "c1", "name": "Ada", "loyalty_tier": "gold"}})

for row in state.snapshot():
    print(row)
```

```text
{'customer_id': 'c1', 'name': 'Ada', 'loyalty_tier': 'gold'}
```

The first event's row had no `loyalty_tier`. The update overwrote the row
with a complete image, so the final row has it.

The case where the `NULL` survives is when the row is **never updated
again** — it keeps the image from its insert, which predates the column.

```python
from cdc import CdcState

state = CdcState(merge_keys=["customer_id"])

state.apply_event({"op": "INSERT", "after": {"customer_id": "c1", "name": "Ada"}})
state.apply_event({"op": "INSERT", "after": {"customer_id": "c2", "name": "Grace"}})

# A column appears in the source. New rows carry it; old rows do not.
state.apply_event({"op": "UPDATE",
                   "after": {"customer_id": "c2", "name": "Grace", "loyalty_tier": "gold"}})

for row in state.snapshot():
    print(row)
```

```text
{'customer_id': 'c1', 'name': 'Ada'}
{'customer_id': 'c2', 'name': 'Grace', 'loyalty_tier': 'gold'}
```

Customer `c1` has no `loyalty_tier`. That is correct — the row genuinely
predates the column.

### A dropped column breaks naive code

```python
event = {"op": "INSERT", "after": {"customer_id": "c2", "name": "Grace"}}

# The bug:
try:
    _ = event["after"]["loyalty_tier"]
except KeyError as exc:
    print("KeyError:", exc)

# The fix:
print("value:", event["after"].get("loyalty_tier"))
```

```text
KeyError: 'loyalty_tier'
value: None
```

In a streaming consumer, that `KeyError` is not a single failed message. It
is usually a crash loop — the message is retried forever, or the consumer
is restarted, and the pipeline makes no progress.

### A changed type

```python
from decimal import Decimal, InvalidOperation

mixed = [
    {"amount": 100},
    {"amount": 250},
    {"amount": "99.50"},   # the source changed the type mid-stream
]

def naive_total(rows):
    total = 0
    for row in rows:
        total += row["amount"]   # TypeError
    return total

try:
    naive_total(mixed)
except TypeError as exc:
    print("TypeError:", exc)
```

```text
TypeError: unsupported operand type(s) for +=: 'int' and 'str'
```

The fix is to **coerce explicitly and count what you cannot read**:

```python
def coerce_amount(value):
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
```

```text
total    : 449.50
rejected : 0
```

### Detect a dropped event — with values, not counts

```python
import json
from pathlib import Path

events = [
    json.loads(line)
    for line in Path("./sample_data/changes.ndjson").read_text().splitlines()
    if line.strip()
]

from cdc import CdcState

complete = CdcState(merge_keys=["customer_id"])
complete.apply_events(events)

without_updates = CdcState(merge_keys=["customer_id"])
without_updates.apply_events([e for e in events if e.get("op") != "UPDATE"])

print(f"rows, complete        : {complete.row_count()}")
print(f"rows, without updates : {without_updates.row_count()}")
print("row count difference   :", complete.row_count() - without_updates.row_count())

correct = {r["customer_id"]: r for r in complete.snapshot()}
stale = {r["customer_id"]: r for r in without_updates.snapshot()}
differing = [k for k in correct if k in stale and correct[k] != stale[k]]
print(f"rows with a stale value: {len(differing)}")
```

The row counts are close — a count-based check would pass. The value
comparison catches every dropped update.

---

## 🛠️ Common Errors and Fixes

### `KeyError: 'column_name'` in the consumer

The source dropped or renamed the column. Use `.get()` and count the
misses.

### `Invalid schema: field 'x' has changed type from STRING to INTEGER`

The destination table's column type conflicts with the source's. Widen the
destination column:

```sql
ALTER TABLE `YOUR_PROJECT_ID.datastream.customers`
ALTER COLUMN amount TYPE NUMERIC;
```

### `Duplicate rows in the destination table` after a backfill

The destination was not empty before the backfill. The merge cannot
resolve it — it has no way to know which copy is right. Drop and recreate:

```sql
DROP TABLE `YOUR_PROJECT_ID.datastream.customers`;
-- Then restart the stream with --backfill-all
```

### The backfill ran but the table is still missing old rows

Check the source config's `include_tables`. A backfill only copies the
tables the source is configured to capture.

### Changes are not appearing after a schema change

Check whether the stream is still `READY`. A destination config that
needs a schema change goes into `MIGRATING` while it applies, and errors
if the change is incompatible.

---

## 💡 Production Notes

- **Treat row images as partial.** `.get()`, never `[...]`, for any column
  that could be added or dropped.
- **Count what you reject.** A schema change that breaks 5% of your events
  should be a visible event, not a silent data loss.
- **Test schema changes.** Add a column to a test source, run the
  pipeline, and assert that the destination has the column and the old
  rows are `NULL`. This is a cheap test that catches an expensive class
  of outage.
- **Empty the destination before a backfill.** Always. It is the one
  recovery procedure where a shortcut produces data you cannot repair.
- **Never let the pipeline decide a type change.** Make the decision
  explicitly, in a migration, with a human.
- **Keep the source's `updated_at` as a secondary path.** CDC is the
  primary path, but a nightly reconciliation query against the source is a
  cheap safety net that catches anything the merge got wrong.

---

## 🔑 Key Takeaways

- The source schema **will** change, and it will change without warning.
- A new column means old rows have `NULL`. That is **correct**, not a bug.
- A **dropped column** breaks `row["col"]`. Use `.get()` and count the
  misses.
- A **changed type** must be handled explicitly — widen, version, or
  migrate. Never let it happen silently.
- `--backfill-all` is almost always right. Without it, the destination
  starts missing every pre-existing row.
- A backfill requires an **empty destination**. This is not negotiable.
- The log is the source of truth: you can rebuild a corrupted destination
  by replaying it.

---

## 📚 Practice Exercises

1. **Model a rename.** The source renames `first_name` to `given_name`.
   Write the code that handles the transition without losing data, and
   explain what the destination table looks like during the transition.

2. **Write the reconciliation query.** Write the BigQuery SQL that
   compares the destination table against a nightly extract of the source,
   and returns only the rows that differ. This is your safety net.

3. **Test a backfill into a dirty table.** Create a table with a row,
   then run a backfill into it. Show what goes wrong, and write the
   recovery steps.

4. **Choose a consistency strategy.** For each case, say whether you would
   widen, version, or migrate — and defend it:
   (a) `amount` changes from `INT` to `DECIMAL(10,2)`
   (b) `status` changes from `VARCHAR` to an enum
   (c) `created_at` changes from `TIMESTAMP` to a `STRING` in a legacy
   system being migrated in

5. **Reflection.** Your team proposes handling schema changes by having
   the pipeline ignore any column it does not recognise. List every way
   that can go wrong.

---

## 📖 Further Reading

- BigQuery schema flexibility — https://cloud.google.com/bigquery/docs/schemas
- Datastream's schema handling — https://cloud.google.com/datastream/docs/schema-management
- Postgres logical replication and column lists — https://www.postgresql.org/docs/current/logical-replication.html
- Debezium's schema history — https://debezium.io/documentation/reference/operations.html
