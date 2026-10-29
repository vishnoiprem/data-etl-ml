---
l_id: L100
title: Hands-on: Clean Up
duration: "4:00"
prereqs: ["L99 - Hands-on: Cortex Service"]
---

# L100 — Hands-on: Clean Up

> **Author:** Prem Vishnoi &lt;pvishnoi&commat;avilx.com&gt;
> **Section:** 13 — Snowpipe for Azure
> **Duration:** 4:00

## Prereqs

The Cortex demo artifacts from section 12 are still live. You have
`OWNERSHIP` on them or a role with the right to drop.

## Lecture

Before we move on to Azure Snowpipe, drop the Cortex demo objects
so they don't keep charging you while we work. **Two cost
categories to kill:**

1. **The Cortex Search service.** It runs as long as it exists
   and is sized by the underlying table. Cheap, but not free.
2. **The Streamlit app's warehouse credits.** Streamlit apps
   attach to a warehouse; if you left the app open in another
   tab, the warehouse has been running.

### Step 1 — drop the Streamlit app

```sql
USE SCHEMA app;
DROP STREAMLIT IF EXISTS review_triage;
```

### Step 2 — drop the Cortex Search service

```sql
USE SCHEMA ml;
DROP CORTEX SEARCH SERVICE IF EXISTS review_search;
```

### Step 3 — drop the demo database

```sql
DROP DATABASE IF EXISTS ai_demo;
```

This cascades to all schemas, tables, views, the Task, the stage,
and the file format. It does **not** drop the warehouse, secrets,
or storage integrations in your account — those are account-level
objects.

### Step 4 — drop the warehouse (optional)

```sql
DROP WAREHOUSE IF EXISTS ai_demo_wh;
```

If you have other work that uses the same warehouse, skip this.

### Step 5 — confirm nothing is left

```sql
SHOW DATABASES LIKE 'ai_demo';
SHOW WAREHOUSES LIKE 'ai_demo_wh';
SHOW CORTEX SEARCH SERVICES IN ACCOUNT;
SHOW STREAMLITS IN ACCOUNT;
```

All four should return zero rows.

### Step 6 — sanity-check the cost views

```sql
SELECT *
FROM TABLE(INFORMATION_SCHEMA.CORTEX_SEARCH_DAILY_USAGE_HISTORY(
  DATE_RANGE_START => DATEADD('day', -7, CURRENT_DATE())
))
ORDER BY usage_date DESC
LIMIT 10;

SELECT *
FROM TABLE(INFORMATION_SCHEMA.AUTO_INGEST_USAGE_HISTORY())
ORDER BY start_time DESC
LIMIT 10;
```

The Cortex search spend should drop to zero from "tomorrow" — the
history is recorded on a daily roll-up.

### Notes

- If you want to keep any artifacts (e.g. the scored view for
  future demos), drop only the Streamlit + Search service and
  leave `ai_demo` in place.
- Storage integration, secret, and notification integration are
  account-scoped; they don't go away with the database.

## Key takeaways

- Always tear down Cortex services and Streamlit apps when you
  stop using them — they charge by the hour.
- `DROP DATABASE` cascades but skips account-scoped objects.
- `CORTEX_SEARCH_DAILY_USAGE_HISTORY` is the post-mortem view
  for cost.

## What's next

In **L101 — High-level steps (Snowpipe Azure)** we lay out the
five-step Azure version of the GCS Snowpipe we built in
section 11.
