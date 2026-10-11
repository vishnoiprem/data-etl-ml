# Section 15 — Fail Safe

> **Author:** Prem Vishnoi &lt;pvishnoi&commat;avilx.com&gt;
> **Lectures:** L110–L111
> **Duration:** ~16 min

The shortest section in the course, and the natural close to the
Time Travel story. Two lectures:

1. **Time Travel cost** — how retention shows up on the bill, and
   the levers to keep it under control.
2. **Fail Safe** — the 7-day, non-configurable safety net for
   permanent tables that sits *after* the Time Travel window ends.
   Only Snowflake Support can read it; it exists for catastrophic
   recovery.

| L# | Title | Min |
|---|---|---|
| L110 | Time travel cost | 8:00 |
| L111 | Understanding Fail Safe | 8:00 |

## Key concepts you'll need later

- **Time Travel cost** — billed like any other storage; tune
  `DATA_RETENTION_TIME_IN_DAYS` to your recovery SLA.
- **Fail Safe** — 7 days, automatic, no SQL access for users.
  Reachable only by Snowflake Support.
- **Permanent vs transient** — only permanent tables get Fail
  Safe. Transient tables have neither Time Travel (beyond the
  default 1) nor Fail Safe — covered in detail in section 16.

## What comes next

Section 16 is **Types of tables** — permanent, transient, and
temporary — and the cost / recovery trade-offs of each.
