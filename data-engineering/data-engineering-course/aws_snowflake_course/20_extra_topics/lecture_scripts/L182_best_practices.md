---
l_id: L182
title: Best practices
duration: "5:00"
prereqs: ["L181"]
---

# L182 — Best practices

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 7. Best Practices & Bonus
> **Duration:** 5:00

## Prereqs

L181 — Snowflake Marketplace.

## Key terms

- **Production hardening** — the practice of applying
  security, monitoring, and cost controls to a
  production account.
- **Convention over configuration** — picking a sensible
  default and applying it consistently.

## Lecture

Welcome to the final sub-group of the course. By now you've
learned every primitive Snowflake offers: warehouses,
tables, time travel, fail safe, zero-copy cloning, sharing,
sampling, tasks, streams, materialized views, masking, and
BI integration. The last 6 lectures (L182–L187) consolidate
the most important production patterns.

Today's lecture is the **best practices overview**: a
single view of the operational, security, and cost rules
that, when followed, prevent 80% of the production issues
we see in customer accounts.

### The 10 production rules

1. **Two or three `ACCOUNTADMIN` users only.** All with
   MFA. Used for emergencies only.
2. **Custom roles under `SYSADMIN`.** Never grant
   `ACCOUNTADMIN` to humans or service accounts for
   day-to-day work.
3. **Permanent tables for production, transient for
   staging, temporary for scratch.** Save Fail Safe for
   the data that needs it.
4. **Clustering keys on hot filters.** Especially for
   tables > 1 TB.
5. **Right-size warehouses.** Don't use a 4XL for a
   query that fits on a Medium.
6. **Auto-suspend at 60 seconds or less.** Idle
   warehouses are the #1 source of credit waste.
7. **Use `WHEN SYSTEM$STREAM_HAS_DATA` for stream
   consumers.** Don't poll naively.
8. **Resource monitors on every account.** Set a hard
   credit cap.
9. **Masking policies on every PII column.** Document
   the policy in the `COMMENT`.
10. **Audit `ACCOUNTADMIN` and `SECURITYADMIN` activity
    weekly.** Use `LOGIN_HISTORY` and `QUERY_HISTORY`.

### The single-most-important rule

If you have to pick *one* rule, pick **#6: auto-suspend at
60 seconds or less**. A warehouse that runs 24/7 burns
~720 credits per month on a Medium. Auto-suspend at 60s
typically cuts that to <50 credits for the same workload.

### The cost-control triangle

Three knobs control Snowflake costs:

- **Warehouse size** (compute per second).
- **Auto-suspend** (idle time).
- **Scaling policy** (Economy vs Standard).

The default for new warehouses is "Standard" scaling and
60-second auto-suspend. For most workloads, the default is
fine. Tune the warehouse size for the *heaviest* query in
the workload, not the average.

### The operational triangle

Three things every production account needs:

- **Monitoring.** A resource monitor on the account; an
  alert on the credit cap.
- **Backups.** A daily clone of the production database,
  stored in a backup account or in the same account.
- **Documentation.** The role hierarchy, the share list,
  and the data retention policies, in a repo.

### The single rule for new tables

> If you don't know whether a table is permanent or
> transient, choose **transient**. It's cheaper, and you
> can `ALTER TABLE ... SET DATA_RETENTION_TIME_IN_DAYS`
> later if you need a permanent upgrade.

This is the safe default. Promote to permanent only when
you know the data is critical.

## Hands-on

For each of your 10 production rules, write the SQL or
the policy that enforces it. Examples:

- Auto-suspend: `ALTER WAREHOUSE compute_wh SET
  AUTO_SUSPEND = 60;`
- Resource monitor: `CREATE RESOURCE MONITOR monthly_cap
  WITH CREDIT_QUOTA = 1000;`
- Masking policy: see L165.

## Key takeaways

- 10 production rules cover 80% of operational risk.
- Auto-suspend is the #1 cost-control lever.
- The cost-control triangle: size × auto-suspend × scaling.
- The operational triangle: monitoring × backups × docs.

## What's next

L183 — Warehouse Usage. The deeper dive on warehouse sizing
and patterns.