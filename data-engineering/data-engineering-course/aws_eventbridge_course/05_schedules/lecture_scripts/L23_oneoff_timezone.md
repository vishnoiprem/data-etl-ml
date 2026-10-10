---
lecture: L23
title: "One-Off Schedules, Time Zones, and Flexible Time Windows"
duration: "7:30"
section: 5
prereqs:
  - L22
downloads:
  - "../../downloads/eventbridge_cheat_sheet.pdf"
---

# L23 — One-Off Schedules, Time Zones, and Flexible Time Windows

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 5 — EventBridge Scheduler
> **Duration:** 7:30

## Prereqs

- Watched **L22 — Cron and Rate Expressions** so you understand the
  `cron(…)` and `rate(…)` syntax.

## Key terms

- **At-expression** — `at(YYYY-MM-DDThh:mm:ss)`. Fires **exactly
  once** at the named instant, then the schedule is "done." Used for
  one-shot reminders, expirations, and contract-end jobs.
- **ScheduleExpressionTimezone** — an IANA tz string
  (`America/Los_Angeles`, `Europe/Berlin`, `Asia/Tokyo`) that the
  scheduler uses to **interpret** the cron. Without it, cron is
  evaluated in UTC.
- **Daylight saving time (DST)** — twice a year, a local clock
  either jumps forward (skipping an hour) or back (repeating an
  hour). Your cron either fires once, not at all, or twice — depends
  on the day and the hour.
- **Flexible time window** — `FlexibleTimeWindow={"Mode":
  "FLEXIBLE", "MaximumWindowInMinutes": N}`. Lets the scheduler pick
  any minute in the window to invoke the target. Default is
  `{"Mode": "OFF"}` (fire exactly on time).
- **Thundering herd** — a thousand clients that all hit a downstream
  service at exactly the top of the hour. Flexible windows defuse
  this by spreading invocations across N minutes.

## Lecture

Hi, I'm Prem Vishnoi. In L22 we learned the rate and cron syntax. In
this lecture we add the three features that turn Scheduler from "cron
on AWS" into "real production scheduling":

1. **At-expressions** — fire exactly once.
2. **Time zones** — make cron mean *local* time, not UTC.
3. **Flexible time windows** — defuse thundering-herd invocations.

### One-off schedules with `at(…)`

Sometimes you do not want a recurring schedule. You want a
**single fire** at a specific moment:

- "Send a contract renewal reminder at 9 AM on the day the contract
  expires."
- "Cancel an order exactly 24 hours after the customer placed it."
- "Trigger a one-shot data migration at 2 AM Saturday."

That is what `at(…)` does. Syntax:

```
at(YYYY-MM-DDThh:mm:ss)
```

Examples:

```python
"at(2026-12-31T23:59:00)"        # 2026-12-31 23:59:00 UTC
"at(2026-12-31T18:59:00)"        # 2026-12-31 18:59:00 UTC
```

The full ISO-8601 format is required. The timestamp is **UTC**. If
you need local time, the trick is to compute the UTC equivalent
yourself:

```python
import datetime, zoneinfo
local = zoneinfo.ZoneInfo("America/Los_Angeles")
dt = datetime.datetime(2026, 12, 31, 15, 59, 0, tzinfo=local)  # 3:59 PM PST
utc = dt.astimezone(datetime.timezone.utc)
expr = f"at({utc.strftime('%Y-%m-%dT%H:%M:%S')})"
# at(2026-12-31T23:59:00)
```

After the at-expression fires, the schedule is **not deleted** — it
stays in `DISABLED` state. You can re-enable it manually if you want
to reuse the same name, or leave it as an audit trail.

```python
scheduler.create_schedule(
    Name="send-renewal-reminder",
    GroupName="one-off",
    ScheduleExpression="at(2027-01-15T17:00:00)",
    FlexibleTimeWindow={"Mode": "OFF"},
    State="ENABLED",
    Target={
        "Arn": "arn:aws:lambda:...:function:send-reminder",
        "RoleArn": "arn:aws:iam::...:role/scheduler-invoke-lambda",
        "Input": '{"contractId":"C-1234"}',
    },
)
```

The IAM role requirements are identical to a cron/rate schedule.

### Time zones

By default, `cron(0 9 * * ? *)` means **9 AM UTC**. That is rarely
what a human wants. If you are a US retailer and the marketing team
wants "8 AM Eastern every weekday," you have two options:

#### Option A — use a time zone in the schedule

Pass `ScheduleExpressionTimezone="America/New_York"` (IANA tz
database) and write the cron in **local** time:

```python
scheduler.create_schedule(
    Name="weekday-morning-digest",
    GroupName="daily",
    ScheduleExpression="cron(0 8 * * MON-FRI *)",  # 8 AM local
    ScheduleExpressionTimezone="America/New_York",  # Eastern, with DST
    FlexibleTimeWindow={"Mode": "OFF"},
    State="ENABLED",
    Target={...},
)
```

That is the entire trick. The scheduler uses the IANA tz database
(zoneinfo on Linux) to convert the local cron into UTC at every
invocation.

#### Option B — convert UTC manually in your application code

If you only have one schedule and you can do the math, just set the
UTC time and skip the field. This is fine; the field is purely
ergonomic.

#### DST gotchas

DST is the time-zone problem. Two days a year your local clock
behaves weirdly:

| Day | Local event | Cron behavior |
|---|---|---|
| Spring Forward (2 AM → 3 AM) | 2 AM does not exist | A `cron(0 2 * * ? *)` in `America/Los_Angeles` **does not fire** that day |
| Fall Back (2 AM → 1 AM) | 2 AM happens twice | A `cron(0 2 * * ? *)` in `America/Los_Angeles` fires **once** (the first occurrence) |

The scheduler does *not* rerun the missed spring-forward cron. If
that matters, use a time that is outside the DST jump (most teams
pick 3 AM or later) or schedule a Lambda that does the math and
chains to the next workday.

For **at-expressions**, DST does not apply — the timestamp is in
UTC, full stop.

### Flexible time windows

The third feature. Default behavior of any cron is "fire *exactly*
on the wall clock minute." If you have 100,000 schedules all set to
`cron(0 2 * * ? *)` for a 2 AM nightly batch, every one of them
fires in the same 60-second window. For some downstream services —
a Step Functions state machine, a small Aurora cluster, a vendor
API with a 100 req/sec limit — that is a thundering herd.

`FlexibleTimeWindow` lets you tell the scheduler: "fire this within
N minutes of the scheduled time, *not necessarily on the minute*."

```python
scheduler.create_schedule(
    Name="nightly-batch",
    GroupName="batches",
    ScheduleExpression="cron(0 2 * * ? *)",
    FlexibleTimeWindow={
        "Mode": "FLEXIBLE",
        "MaximumWindowInMinutes": 15,
    },
    State="ENABLED",
    Target={...},
)
```

The scheduler will pick a random minute in `[02:00, 02:15)` for each
invocation. You cannot predict which minute, but you can be sure
the invocations are spread out.

When **not** to use flexible windows:

- **Strict wall-clock SLAs.** "I need the email at exactly 8 AM."
  Use `Mode: "OFF"`.
- **Time-sensitive chains.** If schedule A must fire *before*
  schedule B, fixed windows (`Mode: "OFF"`) are easier to reason
  about.
- **Audit trails.** If a regulator requires a record of the exact
  minute the cron fired, you have to log the actual `Time` from
  CloudWatch Metrics — flexible windows complicate that audit.

When **to** use them:

- **Bursts.** When you have many crons hitting the same target.
- **Rate-limited APIs.** When the target is a vendor API or a
  third-party service with a per-second cap.
- **Cost smoothing.** When the target charges per-second (Lambda
  does, Step Functions does) and a flexible window smooths
  billing.

### End-to-end: a single demo using all three

```python
import boto3, datetime, zoneinfo

scheduler = boto3.client("scheduler", region_name="us-east-1")
scheduler.create_schedule_group(Name="ops")

# A one-off at-expiration
local = zoneinfo.ZoneInfo("America/Los_Angeles")
expire = datetime.datetime(2027, 1, 15, 9, 0, 0, tzinfo=local)
expire_utc = expire.astimezone(datetime.timezone.utc)
scheduler.create_schedule(
    Name="contract-expiry-alert",
    GroupName="ops",
    ScheduleExpression=f"at({expire_utc.strftime('%Y-%m-%dT%H:%M:%S')})",
    FlexibleTimeWindow={"Mode": "OFF"},
    State="ENABLED",
    Target={
        "Arn": "arn:aws:lambda:us-east-1:111122223333:function:send-expiry",
        "RoleArn": "arn:aws:iam::111122223333:role/scheduler-invoke-lambda",
        "Input": '{"contractId":"C-1234"}',
    },
)

# A daily cron in Pacific time, with a flexible window
scheduler.create_schedule(
    Name="weekday-morning-report",
    GroupName="ops",
    ScheduleExpression="cron(0 8 * * MON-FRI *)",
    ScheduleExpressionTimezone="America/Los_Angeles",
    FlexibleTimeWindow={"Mode": "FLEXIBLE", "MaximumWindowInMinutes": 10},
    State="ENABLED",
    Target={
        "Arn": "arn:aws:lambda:us-east-1:111122223333:function:morning-report",
        "RoleArn": "arn:aws:iam::111122223333:role/scheduler-invoke-lambda",
        "Input": '{"reportType":"morning"}',
    },
)
```

That single script demonstrates: a cron in Pacific time, a
flexible time window, and a one-off at-expression. All three
features at once.

### Cost and quotas reminder

- Each at-expression is **1 invocation** (it fires once and is
  done). Free tier covers 14 million.
- Flexible time windows do **not** cost extra.
- Time-zone aware schedules do **not** cost extra.

## Hands-on

Try a quick experiment:

1. In the AWS console, go to **EventBridge → Scheduler → Create
   schedule**.
2. Pick `at(2026-10-10T20:30:00)` and a Lambda that just writes
   `now()` to CloudWatch Logs.
3. Wait 5 minutes, then check the log stream — confirm the
   invocation was at exactly 20:30:00 UTC.
4. Now create a second schedule, `cron(0 12 * * ? *)`, with
   `ScheduleExpressionTimezone="America/Los_Angeles"`. Confirm it
   fires at noon PST (which is 20:00 UTC during daylight time).

Both schedules are free.

## Quiz prep

These are the L23 questions to focus on:

- What does `at(…)` do? How is it different from `cron(…)` and
  `rate(…)`?
- What IANA tz string would you use for London? (Europe/London)
- A `cron(0 2 * * ? *)` with `America/Los_Angeles` on the
  spring-forward day: does it fire?

## Further reading

- AWS docs: [One-time schedules](https://docs.aws.amazon.com/scheduler/latest/UserGuide/managing-schedule-flexible-time-window.html)
- AWS docs: [Time zones in EventBridge Scheduler](https://docs.aws.amazon.com/scheduler/latest/UserGuide/time-zones.html)
- IANA tz database: <https://www.iana.org/time-zones>
- `../../SYLLABUS.md` — full lecture map.

## What's next

In **L24** we close out section 5 with a section recap and a
walk-through of `code/schedule_cron.py` — a real, idempotent boto3
program that creates three schedules (a rate, a cron, and an at).

**Ready? Let's run the demo.**
