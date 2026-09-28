# Lesson 1 — AI-Assisted SQL Writing

> **Type:** Article · Module 2 · AI for SQL & Analytics
> How to write production-grade SQL faster with AI as a copilot — and the verification rituals that make it safe.

---

## What this lesson covers

AI assistance for SQL is the **highest-ROI** daily activity for a DE. The gain is real (3–5× on complex queries, from Lesson 2). The failure modes are real too. This lesson gives you the working patterns: the prompt template, the verification checklist, and the specific silent bugs to watch for.

---

## The SQL-writing loop with AI

```
   ┌──────────────────────────────────────────────────────────┐
   │  THE 5-STEP SQL LOOP                                     │
   │                                                          │
   │   1. SPEC     what question, what grain, what timeframe  │
   │   2. DRAFT    AI produces first cut                      │
   │   3. READ     you read every line                        │
   │   4. VERIFY   row count + sample + EXPLAIN               │
   │   5. SHIP     commit + monitor for 24 hours              │
   └──────────────────────────────────────────────────────────┘
```

If you skip step 1, you re-do work. If you skip step 3 or 4, you ship the silent bug.

---

## The SQL prompt template (DE-flavored)

```text
ROLE: senior analytics engineer at {COMPANY}.
DIALECT: {Snowflake | BigQuery | Databricks SQL | Postgres}
SCHEMA: @schema.md (or paste the relevant CREATE TABLE)
CONVENTIONS:
  - lowercase keywords, 4-space indent, snake_case
  - explicit JOINs, no comma joins
  - CTEs over nested subqueries
  - always alias columns
  - date columns end in _at (UTC) or _date (DATE)
  - always handle NULL explicitly

TASK: {the business question, with grain and timeframe}

CONSTRAINTS:
  - no SELECT *
  - handle NULL {field} explicitly
  - respect {business rule}
  - return only the SQL + verification

FORMAT:
  1. SQL in a ```sql block
  2. 2-line explanation of choices
  3. 2 sample row-check queries

VERIFICATION:
  - expected row count: {N}
  - NULL check on {field}
  - {specific edge case for this query}
```

---

## The four silent SQL bugs to always check

### 1. Silent fan-out joins
**Symptom:** query returns 3× the rows you expect because of a 1-to-many join you didn't account for.

**Check:**
```sql
SELECT COUNT(*) FROM <result>;
-- compare to upstream fact row count, or to a known-good control query
```

**Fix:** switch INNER JOIN to LEFT JOIN, or aggregate before joining.

### 2. NULL exclusion in negation
**Symptom:** `WHERE region != 'APAC'` silently drops 8% of rows where region IS NULL.

**Check:**
```sql
SELECT region, COUNT(*) FROM orders GROUP BY region;
-- expect "NULL" to be its own row
```

**Fix:** `WHERE COALESCE(region, '') != 'APAC'` or `WHERE region IS DISTINCT FROM 'APAC'`.

### 3. Wrong window frame
**Symptom:** `LAST_VALUE()` returns the current row instead of the actual last value.

**Check:**
```sql
SELECT *, LAST_VALUE(x) OVER (PARTITION BY ... ORDER BY ...
       ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)
FROM ...
```

**Fix:** always specify the frame explicitly.

### 4. Timezone drift
**Symptom:** report looks fine in dev (UTC), wrong in prod (IST). Off by one day at boundaries.

**Check:** print `CURRENT_TIMESTAMP()` and the user's expected timezone.

**Fix:** convert at the warehouse boundary, store in UTC, document the convention.

---

## Verification checklist (use before every commit)

- [ ] Row count matches the expected control
- [ ] 10-row sample by hand (read the actual values)
- [ ] EXPLAIN plan shows expected join order
- [ ] No full-table scans on large tables (unless intended)
- [ ] NULL handling explicit on every filter
- [ ] Date/timezone conversion is correct
- [ ] Window frame specified on every window function
- [ ] No `SELECT *`
- [ ] Cost estimate reasonable (Snowflake query profile, BigQuery dry-run)

---

## What AI is good at (the skeleton)

- CTE structure and naming
- Picking the right window function
- Choosing join order for readability
- Dialect-specific syntax (Snowflake vs BigQuery vs Postgres)
- Translating from one dialect to another
- First-draft coverage of edge cases when you explicitly name them

## What AI is bad at (the joints)

- Knowing your specific business rule for "active customer"
- Choosing grain when the spec is ambiguous
- SCD strategy
- Performance tuning on your actual data
- Joins that depend on undocumented org conventions

---

## Senior-level habit: the "explain the SQL back" prompt

After AI writes the SQL, ask it to **explain it back to you in plain English**. If the explanation doesn't match what you wanted, the SQL doesn't either.

```text
Explain the SQL above as if to a non-technical stakeholder.
Include:
- what each CTE does
- what each join's cardinality is (1:1, 1:many, many:many)
- what happens if column X is NULL
- what the final grain is (one row per ...)
```

If the AI's explanation is hand-wavy where the logic is subtle, the SQL is too. Push back.

---

## What Comes Next

> Lesson 2 — **Text-to-SQL** — the real accuracy of AI on a 200-table warehouse, the failure modes that drive the gap, and when text-to-SQL is the right tool vs. the wrong one.
