# Section 14 — Time Travel

> **Author:** Prem Vishnoi &lt;pvishnoi&commat;avilx.com&gt;
> **Lectures:** L104–L109
> **Duration:** ~50 min

Every Snowflake table has a built-in rewind button. **Time Travel**
lets you `SELECT` and `CLONE` any table as it was at a point in the
past (up to 90 days back, depending on your edition and
`DATA_RETENTION_TIME_IN_DAYS`).

The most common use cases:

- A bad `UPDATE`/`DELETE` was issued at 2 a.m. — restore the
  rows.
- A developer `DROP`ped the wrong table — `UNDROP` it.
- You want to compare today's data with yesterday's for a
  metric-debugging session.
- You want a zero-copy clone of *last Friday's* state for an
  audit review.

By the end of this section you will know how to use `AT |
BEFORE` offsets, restore a table from a past version, recover
a dropped object, and tune the retention period to balance
recovery needs against storage cost.

| L# | Title | Min |
|---|---|---|
| L104 | Create pipe and load data (Azure) | 8:00 |
| L105 | What is Time Travel? | 8:00 |
| L106 | Using time travel | 10:00 |
| L107 | Restoring data | 9:00 |
| L108 | UNDROP tables | 7:00 |
| L109 | Retention time | 8:00 |

## Key concepts you'll need later

- **Time Travel** — every table retains historical data for
  `DATA_RETENTION_TIME_IN_DAYS` (default 1, up to 90 on
  Enterprise+).
- **`AT | BEFORE`** — the SQL clause that anchors a query to a
  past point: `TIMESTAMP`, `OFFSET`, or `STATEMENT`.
- **Restoring** — `CREATE TABLE ... AS SELECT ... AT | BEFORE ...`
  is the safe pattern; never `INSERT` from a past version.
- **UNDROP** — recovers a dropped table, schema, or database
  within the retention window.
- **Cost** — Time Travel storage is billed monthly like any
  other storage; tune retention to match your recovery SLA.

## What comes next

Section 15 is **Fail Safe** — the 7-day, non-configurable
"after Time Travel ends" safety net for permanent tables. We
also cover the cost trade-off of `DATA_RETENTION_TIME_IN_DAYS`.
