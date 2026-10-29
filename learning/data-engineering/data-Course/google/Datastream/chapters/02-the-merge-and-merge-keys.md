# 2.1 — The Merge and the Merge Key

> **Section 2 · The BigQuery Destination · Lecture 2.1 · 30 min**

## 🎯 What you will learn

- The three clauses of the `MERGE` that Datastream effectively runs
- Why the `MERGE` is idempotent, and what that property is worth
- The **merge key** rule: unique, immutable, minimal
- The three ways a merge key can be wrong, and the **silent** failure each
  produces
- How to write a value-level comparison — because a row-count check will
  never catch a merge bug

---

## 🧠 Concept

### The merge

Datastream's BigQuery destination is not "write the events to a table". It
is **apply the events to a table by a keyed merge**. The difference is
everything.

```sql
MERGE `project.dataset.customers` AS target
USING `project.dataset.customers_stream` AS source
    ON target.customer_id = source.customer_id
WHEN NOT MATCHED BY TARGET THEN
    INSERT (customer_id) VALUES (source.customer_id)
WHEN MATCHED AND source.__op__ != 'DELETE' THEN
    UPDATE SET target.customer_id = source.customer_id
WHEN MATCHED AND source.__op__ = 'DELETE' THEN
    DELETE
```

Three clauses, three situations:

| Situation | Clause | Result |
|---|---|---|
| Key not in the target | `NOT MATCHED BY TARGET` | insert a new row |
| Key in the target, not a delete | `MATCHED` + `__op__ != 'DELETE'` | update the row |
| Key in the target, a delete | `MATCHED` + `__op__ = 'DELETE'` | remove the row |

`__op__` is Datastream's synthetic column carrying the operation. It is
not a column in your source table — it is how one `MERGE` handles all
three operations.

### The clause that is NOT in streaming Datastream

You will see this in blog posts:

```sql
WHEN NOT MATCHED BY SOURCE THEN DELETE
```

It deletes target rows that have no matching source row. It makes the
target a **synchronised snapshot**.

Datastream does not use it when streaming, and the reason is conceptual
rather than a limitation. In a stream there is no "the source" as a whole.
The stream contains *changes*, and **the absence of a change is not
evidence of a deletion**. A table that deleted every row it had not heard
about in the last minute would be empty, constantly.

| | Streaming merge | Synchronised merge |
|---|---|---|
| Source | An unbounded stream of changes | A finite, complete snapshot |
| `NOT MATCHED BY SOURCE` | **Never** | Deletes rows absent from the snapshot |
| Use | Live replication | Backfill, one-off sync |
| Datastream offers | Yes | Yes, as a backfill mode |

This distinction is worth being able to explain, because "why does
Datastream not delete rows I removed from the source table?" is a
reasonable question with a subtle answer: **it does**, via the delete
events in the stream. It just does not *infer* deletions from absence.

### Why idempotency falls out of the merge

Every clause is an upsert or a delete **by key**. There is no clause that
appends. Therefore:

> Applying the same event twice has the same effect as applying it once.

This is not a feature you configure. It is a consequence of the shape of
the merge, and it is the property the whole system's safety rests on:

- **Retries.** A failed delivery is redelivered. Safe.
- **Replays.** You rebuild the table from the log. Safe.
- **Restarts.** The transport restarts mid-stream. Safe.
- **Multi-consumer.** Two consumers write to the same table. Safe.

Without idempotency, every one of those is a corruption event. The
classic symptom of a non-idempotent CDC pipeline is a customer table where
every customer appears twice, and nobody can say when it started — because
it started the first time a consumer retried.

### The merge key rule

> The merge key must be the **smallest set of columns that uniquely
> identifies a row in the source table**.

That is usually the primary key, and it is usually one column. It may be
composite — a tenant id plus a customer id, in a multi-tenant system.

Three properties it must have:

| Property | Why | What breaks without it |
|---|---|---|
| **Unique** | A merge must match exactly one row | One update overwrites several rows |
| **Immutable** | The merge looks rows up by key | A changed key orphans the row |
| **Minimal** | Fewer columns means fewer chances to be wrong | A composite key with a nullable part fails to match |

**Uniqueness** is the important one, and the failure it produces is the
worst kind: silent.

### The three ways a merge key is wrong

**1. The key is not unique.**

You merge on `region`. Two customers are in EMEA. An update for one of
them matches both rows and overwrites both.

Nothing errors. The row count does not change. The table now contains a
row for customer `c002` carrying customer `c001`'s new value.

**2. The key is mutable.**

You merge on `email`, and a customer changes their email address. Now
there are two rows: the old one, which the update never matched (so it
keeps the old email), and the new one, which was inserted by the update.

The table has a duplicate customer, and no error was raised.

**3. The key does not exist in the destination.**

You merge on `customer_id`, but the destination table is clustered on `id`.
Every event inserts rather than updates, and the table grows without
bound.

### Why these failures are silent

All three produce a table that is **plausible**. The row count is roughly
right. The columns are populated. Nothing throws.

This is the reason a CDC pipeline needs a **value-level** validation, not
a row-count one:

```python
# Useless — passes with a wrong merge key.
assert len(destination_rows) == len(expected_rows)

# Useless — passes when events are dropped.
assert set(r["customer_id"] for r in destination_rows) == set(
    r["customer_id"] for r in expected_rows
)

# This one catches it.
assert destination_rows == expected_rows
```

A full row-by-row comparison catches every merge bug. It is more expensive
than a count, and it is still cheap — compare the two sides offline, once
a night, over a sample.

---

## 🛠️ Hands-On: Reproducing the Merge Bug

### The correct merge

```python
from cdc import CdcState

state = CdcState(merge_keys=["customer_id"])
state.apply_event({"op": "INSERT", "after": {"customer_id": "c1", "tier": "silver"}})
state.apply_event({"op": "UPDATE", "before": {"customer_id": "c1", "tier": "silver"},
                   "after": {"customer_id": "c1", "tier": "gold"}})

print(state.snapshot())
# [{'customer_id': 'c1', 'tier': 'gold'}]
```

### Now break it

```python
from cdc import CdcState

# The merge key is "region" — which is NOT unique.
state = CdcState(merge_keys=["region"])

state.apply_event({"op": "INSERT", "after": {"customer_id": "c1", "region": "EMEA", "tier": "silver"}})
state.apply_event({"op": "INSERT", "after": {"customer_id": "c2", "region": "EMEA", "tier": "gold"}})
state.apply_event({"op": "INSERT", "after": {"customer_id": "c3", "region": "APAC", "tier": "bronze"}})

print("rows before:", state.row_count())   # 3

state.apply_event({
    "op": "UPDATE",
    "before": {"customer_id": "c1", "region": "EMEA", "tier": "silver"},
    "after": {"customer_id": "c1", "region": "EMEA", "tier": "platinum"},
})

print("rows after :", state.row_count())   # 3  <- unchanged!
for row in state.snapshot():
    print("   ", row)
```

```
rows before: 3
rows after : 3
    {'customer_id': 'c1', 'region': 'EMEA', 'tier': 'platinum'}
    {'customer_id': 'c3', 'region': 'APAC', 'tier': 'bronze'}
```

**Customer `c002` is gone.** Its row was overwritten by `c001`'s update,
because both matched on `region = EMEA`.

The row count never changed. A count-based smoke test passes. The bug is
only visible by looking at the values.

### Prove the merge is idempotent

```python
from cdc import CdcState

events = [
    {"op": "INSERT", "after": {"customer_id": "c1", "tier": "silver"}},
    {"op": "UPDATE", "before": {"customer_id": "c1", "tier": "silver"},
     "after": {"customer_id": "c1", "tier": "gold"}},
    {"op": "INSERT", "after": {"customer_id": "c2", "tier": "bronze"}},
    {"op": "DELETE", "before": {"customer_id": "c2", "tier": "bronze"}},
]

first = CdcState(merge_keys=["customer_id"])
first.apply_events(events)

second = CdcState(merge_keys=["customer_id"])
second.apply_events(events)
second.apply_events(events)   # replay the whole thing again

print("identical after replaying twice:", first.snapshot() == second.snapshot())
print("rows:", second.row_count())
```

`True` and `1`. The second replay changed nothing.

### The reference implementation and the state class

`cdc.py` contains two implementations of the same merge: the `CdcState`
class and the `apply_changes` function. They are independent, so their
agreement is evidence.

```python
from cdc import apply_changes, CdcState

events = [
    {"op": "INSERT", "after": {"customer_id": "c1", "tier": "silver"}},
    {"op": "UPDATE", "before": {"customer_id": "c1", "tier": "silver"},
     "after": {"customer_id": "c1", "tier": "gold"}},
]

reference = apply_changes(events, ["customer_id"])
state = CdcState(merge_keys=["customer_id"])
state.apply_events(events)

print("reference:", reference.snapshot())
print("state    :", state.snapshot())
print("agree    :", reference.snapshot() == state.snapshot())
```

### The generated SQL

```python
from cdc import build_bigquery_merge_sql

print(build_bigquery_merge_sql("customers", ["customer_id"]))
```

```
-- Synchronise the destination table from a change-event table.
MERGE `YOUR_PROJECT_ID.your_dataset.customers` AS target
USING `YOUR_PROJECT_ID.your_dataset.customers_stream` AS source
    ON target.customer_id = source.customer_id
WHEN NOT MATCHED BY TARGET THEN
    INSERT (customer_id)
    VALUES (source.customer_id)
WHEN MATCHED AND source.__op__ != 'DELETE' THEN
    UPDATE SET
        target.customer_id = source.customer_id
WHEN MATCHED AND source.__op__ = 'DELETE' THEN
    DELETE
```

You do not write this by hand — Datastream generates and runs something
equivalent. But when a pipeline misbehaves, the fastest way to diagnose it
is to run the equivalent `MERGE` yourself in BigQuery against the same
rows and see what it does.

---

## 🛠️ Common Errors and Fixes

### `ValueError: merge key column 'customer_id' is missing from the row image`

The event's image does not contain the merge key column. Either the source
table has no such column, or the event predates the column being added.

```python
# wrong
key = image["customer_id"]

# right — and decide what to do when it is missing
if "customer_id" not in image:
    log.warning("event has no merge key; skipping")
    return
```

### `ValueError: merge_keys must not be empty`

You constructed `CdcState(merge_keys=[])` or passed an empty string to
`--merge-keys`. A merge with no key cannot match anything.

### The table grows without bound

Every event is inserting instead of updating. Almost always the merge key
does not match the destination table's primary key:

```bash
bq show --table --format=prettyjson YOUR_PROJECT_ID:datastream.customers | \
  grep -A 5 '"primaryKey"'
```

### The table has duplicate customers

The merge key is **mutable** — usually an email address or a username. The
old row was orphaned when the key changed. Switch to the primary key.

### The update did nothing

The `after` image and the `before` image are identical. That happens when
the source logs only the columns it thinks changed (`binlog_row_image =
MINIMAL`). Set it to `FULL`.

---

## 💡 Production Notes

- **The merge key is a schema decision, not a config detail.** Review it
  with the same care as a primary key on a new table.
- **Validate with values, not counts.** Compare the full row sets. A
  count check will never catch a merge bug.
- **Log the merge key in your pipeline metadata.** When a stream is
  misconfigured three months later, you want to know what key it was
  configured with without reading the terraform.
- **Composite keys are fine.** A tenant id plus an id is a legitimate
  merge key, and is often necessary in a multi-tenant system.
- **The merge must be deterministic.** The same event set must always
  produce the same table. If your merge has a time-dependent branch, it is
  not replayable.

---

## 🔑 Key Takeaways

- The sink is a **keyed merge**: insert when new, update when matched,
  delete when matched-and-deleted.
- **`WHEN NOT MATCHED BY SOURCE` is not used when streaming.** Absence of
  a change is not evidence of a deletion.
- Every clause is an upsert or delete **by key**, so the merge is
  **idempotent** — which is what makes retries, replays and restarts safe.
- The merge key must be **unique, immutable and minimal**. Usually the
  source's primary key.
- A wrong merge key produces a **silent** failure. Row counts will not
  catch it; a value-level comparison will.
- The source must have `binlog_row_image = FULL` or the `before` images
  are incomplete.

---

## 📚 Practice Exercises

1. **Reproduce the mutable-key bug.** Merge on `email`, then change a
   customer's email. Show that the table ends up with two rows for one
   customer, and that no error was raised.

2. **Write the reference check.** Write a function that takes the
   destination rows and a list of source events, and returns the rows the
   destination *should* have. Then show that a wrong merge key fails it.

3. **Prove the streaming merge cannot delete absent rows.** Attempt to
   add a `NOT MATCHED BY SOURCE` clause to the model and explain, in
   terms of what a stream is, why it would empty the table.

4. **Test a composite key.** Model a `tenant_id` + `customer_id` merge
   key. Show that an update for tenant 1 does not affect tenant 2, and
   explain what would go wrong if the merge key were `customer_id` alone.

5. **Reflection.** A team argues that the merge key should be "whatever
   makes the reports work" — a column that appears in every dashboard.
   Give the three reasons that is wrong, using the failure modes from
   this chapter.

---

## 📖 Further Reading

- BigQuery `MERGE` statement — https://cloud.google.com/bigquery/docs/reference/standard-sql/dml-syntax#merge_statement
- Datastream's BigQuery destination — https://cloud.google.com/datastream/docs/bigquery-destination
- BigQuery table constraints (`PRIMARY KEY`, `FOREIGN KEY`) — https://cloud.google.com/bigquery/docs/reference/standard-sql/data-definition-language#table_constraints
- *Designing Event-Driven Data Applications*, Martin Kleppmann — the
  idempotent-consumer pattern
