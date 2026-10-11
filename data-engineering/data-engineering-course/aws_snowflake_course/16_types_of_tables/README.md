# Section 16 — Types of tables

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Lectures:** L112–L115
> **Duration:** ~18 min

Section 15 introduced **Fail Safe** — the second safety net behind Time Travel. Section 16 is the natural follow-up: now that you know what Fail Safe costs, you need to know *which* tables actually pay for it. Snowflake gives you three table types — **permanent**, **transient**, and **temporary** — and one of them skips Fail Safe entirely, which directly cuts your storage bill.

We start with **Fail Safe storage** (L112) — the 7-day backup window, who can use it (only Snowflake Support), and the storage cost it adds on top of Time Travel retention. **Different table types** (L113) lays out the three flavors in one view: their retention period, Fail Safe availability, and typical use case. **Permanent tables & databases** (L114) covers the default, the safest option, which is what you should use for production data. We close with **Transient + Temporary tables & schemas** (L115), where we look at the cheaper-and-shorter options for staging, session scratch, and dev environments.

By the end of this section you should be able to pick the right table type for any workload based on a single trade-off: how much are you willing to pay for disaster recovery?

| L# | Title | Min |
|---|---|---|
| L112 | Fail Safe storage | 4:30 |
| L113 | Different table types | 4:00 |
| L114 | Permanent tables & databases | 4:30 |
| L115 | Transient + Temporary tables & schemas | 5:00 |

## Key concepts you'll need later

- **Fail Safe** = 7-day non-configurable backup after Time Travel expires. Snowflake-only, billed as storage.
- **Permanent** = default. Has Time Travel + Fail Safe. Use for production.
- **Transient** = has Time Travel (1 day max, Enterprise; 0 days Standard) but **no Fail Safe**. Use for staging / ETL scratch.
- **Temporary** = session-scoped. Auto-dropped on session end, **no Fail Safe**. Use for ad-hoc exploration.
- Table type is inherited from schema/database if you don't override it.

## What comes next

Section 17 is **Zero-Copy Cloning** — arguably the most loved Snowflake feature. We'll clone a whole production table in seconds, with zero extra storage, and then start mutating the clone without touching the source.
