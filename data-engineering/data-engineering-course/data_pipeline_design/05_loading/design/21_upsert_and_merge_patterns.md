# 21 — Upsert and Merge Patterns

> **Lesson 21 of 30 — Loading**

The most common write pattern: insert new rows, update existing
ones, leave the rest alone. The destination's `MERGE INTO` (or
`INSERT ON CONFLICT`) is the workhorse. This lesson is the
patterns, the pitfalls, and the SCD2 close-and-insert dance.

---

## 1. What upsert is

An *upsert* is a write that inserts if the row is new, updates
if it exists. The standard syntax:

```sql
-- Postgres / SQLite
INSERT INTO users (id, name, email, updated_at)
VALUES (?, ?, ?, ?)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    email = EXCLUDED.email,
    updated_at = EXCLUDED.updated_at;

-- Snowflake / BigQuery / Redshift
MERGE INTO target.users t
USING staging.users s
ON t.id = s.id
WHEN MATCHED THEN
  UPDATE SET name = s.name, email = s.email, updated_at = s.updated_at
WHEN NOT MATCHED THEN
  INSERT (id, name, email, updated_at)
  VALUES (s.id, s.name, s.email, s.updated_at);
```

Both do the same thing: insert-or-update on a primary key.

---

## 2. When to use upsert

Upsert is the right pattern when:
- The source is incremental (only new / changed rows).
- The destination needs to reflect the latest state.
- The primary key is stable (no changing IDs).

The senior move: "For CDC pipelines I'd use upsert on the
primary key. The alternative — truncate and reload — is too
expensive for large tables."

---

## 3. The merge pattern (full diff)

`MERGE INTO` is the most powerful upsert. It can also do
*deletes* and *conditional* updates:

```sql
MERGE INTO target.users t
USING staging.users s
ON t.id = s.id
-- New: insert
WHEN NOT MATCHED BY TARGET THEN
  INSERT (id, name, status) VALUES (s.id, s.name, s.status)
-- Updated: update
WHEN MATCHED AND s.status != t.status THEN
  UPDATE SET name = s.name, status = s.status
-- Deleted: delete
WHEN NOT MATCHED BY SOURCE THEN
  DELETE;
```

The three clauses:
- `WHEN NOT MATCHED BY TARGET`: rows in source but not in target.
- `WHEN MATCHED`: rows in both. Optionally with a predicate.
- `WHEN NOT MATCHED BY SOURCE`: rows in target but not in source.

The senior move: "I'd use `MERGE INTO` for the silver layer
because it handles inserts, updates, and deletes in one
statement. The `WHEN NOT MATCHED BY SOURCE THEN DELETE` is the
key for handling hard deletes from the source."

---

## 4. The performance pitfall

`MERGE INTO` is *expensive* on large tables. The classic
mistake: `MERGE INTO` a 1 B-row table on every pipeline run,
even when only 1000 rows changed.

The mitigation: *pre-filter* the source. Only upsert rows that
have actually changed since the last run.

```sql
-- The pre-filter pattern
MERGE INTO target.users t
USING (
  SELECT * FROM staging.users
  WHERE updated_at > :last_run_ts  -- only changed rows
) s
ON t.id = s.id
WHEN MATCHED THEN UPDATE ...
WHEN NOT MATCHED THEN INSERT ...;
```

The senior move: "I'd never run `MERGE INTO` against the full
table. Always pre-filter the source by `updated_at` or by the
CDC event timestamp."

---

## 5. The SCD2 close-and-insert

For SCD2 dimensions, upsert is a two-step dance:

```sql
-- Step 1: close the previous version
UPDATE dim_users_scd2 t
SET valid_to = s.valid_from,
    is_current = 0
FROM staging_users s
WHERE t.user_id = s.user_id
  AND t.is_current = 1
  AND t.country != s.country;  -- only if the dimension changed

-- Step 2: insert the new version
INSERT INTO dim_users_scd2 (user_id, country, valid_from, valid_to, is_current)
SELECT user_id, country, valid_from, '9999-12-31', 1
FROM staging_users s
WHERE NOT EXISTS (
  SELECT 1 FROM dim_users_scd2 t
  WHERE t.user_id = s.user_id AND t.is_current = 1
);
```

The senior move: "For SCD2 I'd do the close-then-insert in a
single transaction. If the insert fails, the close is rolled
back. The dimension is always consistent."

---

## 6. The delete pattern

`MERGE INTO` handles deletes via `WHEN NOT MATCHED BY SOURCE`.
The pattern:

```sql
MERGE INTO target.users t
USING staging.users s
ON t.id = s.id
WHEN NOT MATCHED BY TARGET THEN
  INSERT (id, name) VALUES (s.id, s.name)
WHEN NOT MATCHED BY SOURCE
  AND t.updated_at < :run_window_start THEN
  DELETE;
```

The `AND t.updated_at < :run_window_start` predicate is
critical: it ensures you only delete rows that haven't been
touched in *this* run. Without it, a row that's late from
the source would be wrongly deleted.

The senior move: name this guard unprompted. "I'd add a
timestamp predicate to the delete clause so late-arriving
rows aren't deleted."

---

## 7. The code: `code/upsert.py`

The course provides a `merge_into` function that implements
upsert via SQLite's `INSERT OR REPLACE` (a subset of the
real `MERGE INTO`):

```python
from data_pipeline_design.05_loading.code.upsert import merge_into

merge_into(
    q=query_runner,
    target="users",
    source=[{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
    on_keys=["id"],
    update_cols=["name"],
)
```

The test in `tests/test_loading.py` exercises the spec'd
10→5 change case.

---

## 8. The interview answer

> "For incremental loads I'd use `MERGE INTO` (Snowflake) or
> `INSERT ON CONFLICT` (Postgres / SQLite). The pattern is
> three clauses: `WHEN NOT MATCHED BY TARGET` for inserts,
> `WHEN MATCHED` for updates, and `WHEN NOT MATCHED BY SOURCE`
> for deletes. I'd always pre-filter the source by
> `updated_at` to avoid scanning the whole table. For SCD2
> dimensions I'd do the close-then-insert in a single
> transaction. The delete clause needs a timestamp guard so
> late-arriving rows aren't wrongly deleted."

That single paragraph covers: tool syntax, three clauses,
pre-filter, SCD2 dance, delete guard. Senior answer in 30
seconds.

---

## Try it

Look at the most recent upsert you've worked on. Is it
`MERGE INTO` or `INSERT ON CONFLICT`? Is the source
pre-filtered? Is there a delete guard? If any is "no," the
upsert is either slow or wrong.
