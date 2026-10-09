# 08 — Extraction Patterns: Full vs Incremental

> **Lesson 8 of 30 — Extraction**

The first decision every pipeline makes: do we reload all the data,
or only what changed since last time? Full load is the simpler
pattern. Incremental is the cheaper one. This lesson is the
tradeoff.

---

## 1. The two patterns

**Full load:** truncate the destination, copy the entire source.

```sql
-- The full-load pattern, in one line:
TRUNCATE TABLE warehouse.users;
INSERT INTO warehouse.users SELECT * FROM source.users;
```

**Incremental:** read only rows that changed since the last run.

```sql
-- The incremental pattern, in one query:
SELECT id, name, status, updated_at
FROM source.users
WHERE updated_at > :last_run_ts
ORDER BY updated_at;
```

Full load is the default for small tables. Incremental is the
default for everything else. The cutoff is roughly 1 M rows: below
that, full is fine. Above that, incremental saves both time and
money.

---

## 2. When to use full

Full load is the right call when:

- **The source is small** (under ~1 M rows, under ~1 GB).
- **There is no `updated_at` column** (you can't incremental without it).
- **The destination needs to be a clean snapshot** (audit, replay).
- **The data is cheap to recompute** (e.g. summary tables).

The benefit: the pipeline is *idempotent by construction*. Run it
twice, get the same result. There is no "watermark" to manage.

The cost: every run touches every row. A 100 GB table at 1 GB/sec
network is 100 seconds per run, every run. At hourly cadence, that's
2400 GB/day of network traffic for no reason.

---

## 3. When to use incremental

Incremental is the right call when:

- **The source is large** (over ~1 M rows, over ~1 GB).
- **The source has an `updated_at` or version column** (you have a way to detect changes).
- **The pipeline runs frequently** (hourly or more).
- **The downstream can tolerate a small lag** (the incremental pipeline sees only new changes since the last run).

The benefit: 99% of the time, the pipeline touches 1% of the data.
100x faster, 100x cheaper.

The cost: the pipeline is *fragile*. If you miss an `updated_at`
update, you miss the row forever. If a row is updated twice in the
same second, you might process it twice. The pipeline needs
*state management* — where is the watermark stored, how is it
checkpointed, what happens on restart.

---

## 4. The `updated_at` watermark

The most common incremental pattern:

```sql
CREATE TABLE source.users (
  id INTEGER PRIMARY KEY,
  name TEXT,
  status TEXT,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

The pipeline tracks the last-seen `updated_at` and queries:

```sql
SELECT * FROM users
WHERE updated_at > :last_watermark
ORDER BY updated_at
LIMIT 10000;
```

The pitfalls:

| Pitfall | Mitigation |
|---|---|
| `updated_at` is in source's local timezone | Always store/compare in UTC. |
| Multiple rows with the same `updated_at` | Use `>=` not `>`; track the *highest seen id* for tie-breaking. |
| A row's `updated_at` is in the future (clock skew) | Reject rows with `updated_at > NOW() + 5min`. |
| The source has no `updated_at` | Fall back to full load, or add a CDC layer. |

The senior move is to know that the watermark pattern is *the*
default for SQL sources, and to name the four pitfalls unprompted.

---

## 5. The keyset / cursor pattern

An alternative to `updated_at` is the *keyset* pattern — track the
highest-seen primary key:

```sql
SELECT * FROM users
WHERE id > :last_id
ORDER BY id
LIMIT 10000;
```

This works when:

- The primary key is monotonic (auto-increment, UUIDv7).
- New rows are append-only (no updates to old rows).

The benefit: no clock-skew issues, no timezone issues, no missing
updates. The cost: doesn't catch updates to existing rows (only
new rows). For a CDC pipeline, the keyset pattern is the *initial
load* phase; CDC is the *ongoing* phase.

---

## 6. The merge pattern (upsert)

Incremental pipelines usually upsert, not insert. The destination
table gets:

```sql
-- The upsert pattern (PostgreSQL syntax; SQLite has INSERT OR REPLACE)
INSERT INTO warehouse.users (id, name, status, updated_at)
VALUES (?, ?, ?, ?)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    status = EXCLUDED.status,
    updated_at = EXCLUDED.updated_at;
```

The pipeline is *idempotent*: re-running it with the same data
produces the same destination. This is the cornerstone of every
production incremental pipeline. Lesson 21 covers upsert in detail.

---

## 7. The full-then-incremental pattern

The most common production pattern is a hybrid: full load the first
time, incremental every time after.

```
Run 1:  TRUNCATE dest; INSERT all rows from source. (full)
Run 2+: INSERT ... ON CONFLICT ... WHERE updated_at > last_run. (incremental)
```

This handles the bootstrap case (no previous watermark) and the
ongoing case (watermark exists). The senior move is to know that
*every* production pipeline has a bootstrap story. If you can't
answer "what does run 1 look like?" the pipeline is incomplete.

---

## 8. Choosing full vs incremental

```
Is the source small (< 1M rows, < 1 GB)?
  └─ Yes → Full load, no watermark needed
  └─ No  → Is there an updated_at / version column?
              └─ Yes → Incremental with updated_at watermark
              └─ No  → Is there a monotonic primary key?
                         └─ Yes → Keyset incremental
                         └─ No  → Add CDC (Lesson 09) or accept full load
```

The decision tree is simple. The complexity is in the *pitfalls*:
every branch has a "but" — clock skew, missing updates, late
arrivals, restart semantics. The senior answer names the "but"
for whichever branch you'd pick.

---

## Try it

Look at the most recent pipeline you've worked on. Is it full or
incremental? Is there a watermark table? Where is the watermark
stored (database? file? in-memory?)? If the pipeline crashes
mid-run, what happens to the watermark — does it advance, or does
it stay put? The answer tells you a lot about reliability.
