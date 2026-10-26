---
l_id: L111
title: Understanding Fail Safe
duration: "8:00"
prereqs: ["L110 - Time travel cost"]
---

# L111 — Understanding Fail Safe

> **Author:** Prem Vishnoi &lt;pvishnoi&commat;avilx.com&gt;
> **Section:** 15 — Fail Safe
> **Duration:** 8:00

## Prereqs

A permanent table. (Transient and temporary tables do not have
Fail Safe — covered in section 16.)

## Lecture

Time Travel is the recovery window **you** control. Fail Safe is
the recovery window **Snowflake** controls. It is automatic,
non-configurable, and only accessible by Snowflake Support. It
exists so the platform always has a last-resort fallback when a
customer has a true catastrophe.

### What Fail Safe is

- A **7-day, non-configurable** period that begins when the
  Time Travel retention ends.
- Available **only for permanent tables** (and permanent
  schemas / databases).
- **Not queryable by users.** No `AT | BEFORE` clause reaches
  into Fail Safe. No `SELECT * FROM t FAIL_SAFE;`.
- Reachable **only by Snowflake Support** through a manual
  recovery process.

### The timeline, end to end

```mermaid
flowchart LR
  T0["Change made"] --> T1["Time Travel window<br/>(1-90 days)"]
  T1 --> T2["Fail Safe<br/>(7 days, fixed)"]
  T2 --> T3["Purged"]
```

| Window | Duration | Who can read |
|---|---|---|
| Time Travel | `DATA_RETENTION_TIME_IN_DAYS` (1–90) | You |
| Fail Safe | 7 days, fixed | Snowflake Support |
| (after) | — | — |

### Why it exists

- **Catastrophic customer mistakes.** "I ran
  `TRUNCATE` on the wrong table and `DROP TABLE` on the next."
  The Time Travel window might cover part of it, but Fail Safe
  gives Snowflake the runway to do a deeper recovery.
- **Hardware/cloud failure.** Even though Snowflake stores data
  in cloud object storage with high durability, Fail Safe is
  the operational safety net.
- **Regulatory evidence.** Some compliance regimes assume the
  vendor keeps *some* history. Fail Safe is part of meeting
  that.

### How to invoke Fail Safe recovery

You don't. You open a Snowflake support case, provide the table
name, schema, and the timestamp range you need, and Support
runs the recovery. Expect a turnaround measured in hours to
days, not minutes — this is a manual process.

### What Fail Safe does NOT do

- It does **not** apply to transient or temporary tables.
  Those have no Fail Safe at all.
- It does **not** apply to dropped objects. After the Time
  Travel window ends, a `DROP TABLE`'d object is gone.
- It does **not** include row-level recovery from
  `UPDATE`/`DELETE` once Time Travel ends. (You need a
  downstream backup or an SCD2 table for that.)
- It does **not** give you self-service access. Don't plan
  your recovery around it.

### Cost

Fail Safe storage shows up in `failsafe_bytes` in
`TABLE_STORAGE_METRICS` and is billed at the same rate as
active storage. For most tables, the 7-day overlap with Time
Travel's tail means the incremental cost is modest. For very
large tables, it's a real line item.

### Decision: should you depend on Fail Safe?

**No.** Plan your own backups and recovery on top of Time
Travel. Treat Fail Safe as a "if everything else failed, call
Support" fallback, not a recovery SLA.

Practical consequences:

- For audit-critical data, do **not** rely on Fail Safe. Keep
  your own out-of-Snowflake backups (e.g. unload to S3 with
  daily Tasks) and your own Time Travel retention high.
- For dev/sandbox data, transient tables are cheaper and
  don't have Fail Safe — they're the right call.
- For production data, decide your own SLA: how long after a
  mistake can you tolerate "we cannot recover"? Set retention
  + backup frequency to meet it.

### Inspecting Fail Safe on a table

```sql
SELECT table_name,
       active_bytes,
       time_travel_bytes,
       failsafe_bytes
FROM TABLE(INFORMATION_SCHEMA.TABLE_STORAGE_METRICS(
  TABLE_NAME => 'finance.audit.transactions'
));
```

If `failsafe_bytes` is non-zero, the table has been around long
enough (or had enough churn) to have data in Fail Safe.

## Key takeaways

- Fail Safe is 7 days, automatic, non-configurable, and only
  reachable by Snowflake Support.
- Only **permanent** tables get Fail Safe; transient and
  temporary tables do not.
- Don't plan your recovery around it — keep your own backups.

## What's next

In **Section 16 — Types of tables** we cover permanent,
transient, and temporary tables in depth, including how to
choose between them for cost, retention, and recovery.
