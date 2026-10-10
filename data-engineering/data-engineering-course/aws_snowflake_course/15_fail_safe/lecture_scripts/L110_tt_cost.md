---
l_id: L110
title: Time travel cost
duration: "8:00"
prereqs: ["L109 - Retention time"]
---

# L110 — Time travel cost

> **Author:** Prem Vishnoi &lt;pvishnoi&commat;avilx.com&gt;
> **Section:** 15 — Fail Safe
> **Duration:** 8:00

## Prereqs

A few tables with non-trivial history (run some `UPDATE`/`DELETE`
on a scratch table to give it something to bill). `ACCOUNTADMIN`
for some of the views.

## Lecture

Time Travel is "free" until you look at the bill. Every historical
micro-partition is real storage, and the cost is on you. In this
lecture we look at where the cost shows up, how to measure it, and
the levers you have to keep it under control.

### Where Time Travel cost shows up

Two storage buckets in `TABLE_STORAGE_METRICS`:

| Column | What it is |
|---|---|
| `active_bytes` | The current state of the table. |
| `time_travel_bytes` | Historical versions within the Time Travel window. |
| `failsafe_bytes` | Historical versions past Time Travel, in Fail Safe (permanent tables only). |

`time_travel_bytes + failsafe_bytes` is what retention costs
you on top of the live data.

### Measure it across the account

```sql
-- Per-database, per-table storage
SELECT table_catalog,
       table_schema,
       table_name,
       active_bytes,
       time_travel_bytes,
       failsafe_bytes,
       (time_travel_bytes + failsafe_bytes) / NULLIF(active_bytes, 0) AS tt_to_active_ratio
FROM TABLE(INFORMATION_SCHEMA.TABLE_STORAGE_METRICS())
ORDER BY time_travel_bytes DESC
LIMIT 20;
```

The `tt_to_active_ratio` column is the most useful one. Anything
above ~0.5 means you're spending more on history than on the
current state — time to think about retention or
transient/temporary tables.

### Account-wide total

```sql
SELECT SUM(active_bytes)        / POWER(1024, 3) AS active_tb,
       SUM(time_travel_bytes)  / POWER(1024, 3) AS tt_tb,
       SUM(failsafe_bytes)     / POWER(1024, 3) AS fs_tb
FROM TABLE(INFORMATION_SCHEMA.TABLE_STORAGE_METRICS());
```

Multiply by your per-TB storage rate to get the dollar number.

### The four levers

1. **Tune `DATA_RETENTION_TIME_IN_DAYS`.** The single biggest
   lever. 1 day is enough for "I broke it an hour ago" — only
   push higher on tables that genuinely need it.
2. **Use transient tables for staging.** Transient tables have
   `DATA_RETENTION_TIME_IN_DAYS = 1` and **no** Fail Safe — much
   cheaper for short-lived data.
3. **Use temporary tables for session-scoped work.** Zero
   retention, billed like transient.
4. **Force a Time Travel cleanup.** Run
   `ALTER TABLE <t> SET DATA_RETENTION_TIME_IN_DAYS = 0` on
   tables that don't need it. (This drops the history
   immediately — make sure nobody needs it.)

### The pattern of "drop retention on big fact tables"

```sql
-- For a fact table that's append-only and audit-logged elsewhere
ALTER TABLE analytics.gold.fct_events
  SET DATA_RETENTION_TIME_IN_DAYS = 1;
```

`fct_events` is append-only, so the only "history" is the
micro-partition a load just wrote — recovery is "re-run the
load". No need to pay for 30 days of history.

### When the cost is worth it

- **Regulated data.** Audit, finance, healthcare. The cost of
  90-day retention is small compared to the cost of "we can't
  show what changed in the last quarter."
- **Slowly changing dimensions.** SCD2 keeps a row per version;
  the table itself *is* the history. But mistakes happen, and
  Time Travel is a cheap safety net.

### Monitoring

A daily Task + alert is the standard pattern:

```sql
CREATE OR REPLACE TASK daily_tt_cost
  WAREHOUSE = compute_wh
  SCHEDULE = 'USING CRON 0 8 * * * America/Los_Angeles'
AS
  INSERT INTO ops.tt_cost_daily
  SELECT CURRENT_DATE() AS d,
         table_catalog, table_schema, table_name,
         active_bytes, time_travel_bytes, failsafe_bytes
  FROM TABLE(INFORMATION_SCHEMA.TABLE_STORAGE_METRICS())
  WHERE time_travel_bytes > 1e11;  -- 100 GB
```

Alert on `ops.tt_cost_daily` rows for any table over your
budget threshold.

## Key takeaways

- Time Travel cost = `time_travel_bytes + failsafe_bytes` in
  `TABLE_STORAGE_METRICS`.
- The four levers: tune retention, use transient/temporary
  tables, force retention to 0, monitor with a daily Task.
- For append-only fact tables, 1 day is usually enough.

## What's next

In **L111 — Understanding Fail Safe** we cover the 7-day
non-configurable safety net that sits *after* Time Travel ends.
