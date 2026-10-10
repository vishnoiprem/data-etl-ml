---
l_id: L138
title: Using CRON
duration: "4:30"
prereqs: ["L137"]
---

# L138 — Using CRON

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 1. Tasks
> **Duration:** 4:30

## Prereqs

L137 — Creating tasks. You should be comfortable with the basic
`SCHEDULE = 'N MINUTE'` syntax.

## Key terms

- **CRON expression** — a 6- or 7-field string describing a
  schedule. Snowflake uses the standard unix-cron syntax with an
  optional seconds field.
- **`TIMEZONE`** — when used with `CRON`, sets the time zone for
  the schedule. Defaults to UTC.

## Lecture

Welcome back. The `'60 MINUTE'` schedule is fine for "every hour",
but production needs "every day at 2am" or "every Monday at 8am"
or "the 1st of every month". For those, we need **CRON
expressions**.

### The CRON syntax

```text
 ┌──────── minute (0-59)
 │  ┌───── hour (0-23)
 │  │  ┌── day of month (1-31)
 │  │  │  ┌─ month (1-12 or JAN-DEC)
 │  │  │  │  ┌─ day of week (0-6 or SUN-SAT; 0 = Sunday)
 │  │  │  │  │
 *  *  *  *  *
```

That's 5 fields. Snowflake's CRON supports an optional 6th field
for seconds at the front, but the 5-field form is what you'll
write 99% of the time.

### Common expressions

```sql
-- Every day at 2am UTC
SCHEDULE = 'USING CRON 0 2 * * * UTC'

-- Every Monday at 8am UTC
SCHEDULE = 'USING CRON 0 8 * * MON UTC'

-- The 1st of every month at midnight UTC
SCHEDULE = 'USING CRON 0 0 1 * * UTC'

-- Every 15 minutes
SCHEDULE = 'USING CRON */15 * * * * UTC'

-- Weekdays at 6pm UTC
SCHEDULE = 'USING CRON 0 18 * * MON-FRI UTC'
```

The `USING CRON` prefix tells Snowflake the string is a CRON
expression, not a simple interval. The trailing `UTC` (or another
zone) sets the time zone.

### The `TIMEZONE` parameter

The cleanest way to set the zone is the `TIMEZONE` parameter:

```sql
CREATE TASK nightly_etl
  WAREHOUSE = etl_wh
  SCHEDULE  = 'USING CRON 0 2 * * * Europe/Berlin'
  TIMEZONE  = 'Europe/Berlin'
AS
  CALL sp_run_etl();
```

The `TIMEZONE` parameter is preferred over the trailing `UTC`
field, because it also affects the `CURRENT_TIMESTAMP()` value
the task sees. They must agree — pick one style and stick with it.

### Verifying a CRON

Use the `CRON` Snowflake task history. The `SCHEDULED_TIME` column
in `TASK_HISTORY` shows the next planned runs:

```sql
SELECT name, scheduled_time, state, error_code
FROM   TABLE(INFORMATION_SCHEMA.TASK_HISTORY())
WHERE  name = 'NIGHTLY_ETL'
ORDER BY scheduled_time DESC
LIMIT 10;
```

### Common mistakes

- **6 fields when you meant 5.** Putting seconds in by accident is
  the most common cause of "task never fires".
- **Wrong zone.** A 2am `UTC` schedule fires at 2am UTC, which may
  be the middle of the day in your local zone. Always set
  `TIMEZONE` explicitly.
- **Day-of-month + day-of-week conflict.** CRON treats them as
  *OR* when both are set. A schedule of `0 0 1 * MON` fires on
  the 1st of every month OR every Monday — which is *every* day
  between them. Use `?` (or a single `*` and adjust) to disambiguate.

## Hands-on

```sql
USE ROLE SYSADMIN;
USE SCHEMA DEMO_DB.PUBLIC;

-- Every 5 minutes, all week
CREATE OR REPLACE TASK five_min_task
  WAREHOUSE = compute_wh
  SCHEDULE  = 'USING CRON */5 * * * * UTC'
AS
  INSERT INTO TICK_LOG VALUES (CURRENT_TIMESTAMP(), 'five-min tick');

ALTER TASK five_min_task RESUME;

-- Inspect
SELECT * FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY())
WHERE  name = 'FIVE_MIN_TASK'
ORDER BY scheduled_time DESC
LIMIT 5;
```

## Key takeaways

- `SCHEDULE = 'USING CRON ...'` switches from interval to CRON.
- Use 5 fields: minute, hour, day-of-month, month, day-of-week.
- Set `TIMEZONE` explicitly — UTC vs local matters.
- Verify with `INFORMATION_SCHEMA.TASK_HISTORY`.

## What's next

L139 — Understand tree of tasks. We chain tasks together so the
output of one becomes the input of the next.