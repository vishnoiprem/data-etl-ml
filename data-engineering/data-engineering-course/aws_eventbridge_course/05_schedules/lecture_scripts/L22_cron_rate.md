---
lecture: L22
title: "Cron and Rate Expressions — the Scheduling Syntax"
duration: "8:00"
section: 5
prereqs:
  - L21
downloads:
  - "../../downloads/eventbridge_cheat_sheet.pdf"
---

# L22 — Cron and Rate Expressions — the Scheduling Syntax

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 5 — EventBridge Scheduler
> **Duration:** 8:00

## Prereqs

- Watched **L21 — Scheduler 101** so you know what a schedule group,
  flexible time window, and universal target are.

## Key terms

- **Rate expression** — `rate(1 unit)` or `rate(N units)`. The
  simplest form of Scheduler. Examples: `rate(5 minutes)`,
  `rate(1 hour)`, `rate(7 days)`. **Always UTC.**
- **Cron expression** — `cron(min hour dom mon dow year)` — six
  fields, AWS-flavored. Examples: `cron(0 8 * * ? *)`.
- **`?`** — the wildcard used in **either** day-of-month *or*
  day-of-week, never both. This is the AWS quirk that trips up Linux
  cron refugees.
- **Daylight-saving transition** — Spring Forward and Fall Back days
  when a "2 AM" cron either runs once or not at all. We will cover
  this in L23 with `ScheduleExpressionTimezone`.
- **Service quota** — Scheduler is rate-limited to **one invocation
  per second per account** by default; you can request a quota
  increase if you need thousands per second.

## Lecture

Hi, I'm Prem Vishnoi. This is the lecture you will actually pause and
reread. Scheduler's cron syntax is small but it has three AWS-specific
quirks that bite everyone the first time.

### Rate expressions — the easy 80%

A **rate** expression is what you reach for first. Syntax:

```
rate(VALUE UNIT)
```

`UNIT` is one of `minute | minutes | hour | hours | day | days`. The
`VALUE` is a positive integer. There is no way to say "every 90
seconds" — round to minutes.

| Expression | Meaning |
|---|---|
| `rate(1 minute)` | every 60 seconds |
| `rate(5 minutes)` | every 5 minutes |
| `rate(1 hour)` | every hour, on the hour |
| `rate(12 hours)` | every 12 hours |
| `rate(1 day)` | every 24 hours |
| `rate(7 days)` | every 7 days |

Three rules:

1. **Always UTC.** Rate expressions are evaluated against **UTC**, no
   matter what time zone your schedule group is in. If you need local
   time, use a cron expression in L23.
2. **`1` and `unit` is fine, but `1 units` is not.** Singulars must
   match (`1 minute`, `1 hour`). Plurals must match (`5 minutes`,
   `12 hours`). The service is strict — `rate(1 minutes)` errors.
3. **The first invocation is one interval after creation**, not
   immediately. If you `create_schedule` at 12:00:00 with
   `rate(5 minutes)`, the first invocation lands at 12:05:00.

### Cron expressions — AWS's six-field dialect

A cron expression looks like this:

```
cron(min hour day-of-month month day-of-week year)
```

Six fields, all required. Spaces separate the fields; `*` means "any
value", `,` lists alternatives, `-` defines a range, `/` defines a step,
`?` is the AWS wildcard (covered below).

| # | Field | Allowed values | Special chars |
|---|---|---|---|
| 1 | Minute | `0–59` | `* , - /` |
| 2 | Hour | `0–23` (UTC) | `* , - /` |
| 3 | Day-of-month | `1–31` | `* , - / ? L W` |
| 4 | Month | `1–12` or `JAN–DEC` | `* , - /` |
| 5 | Day-of-week | `1–7` or `SUN–SAT` | `* , - / ? L #` |
| 6 | Year | `1970–2199` | `* , - /` |

Note that `day-of-month` and `day-of-week` both accept `?`. The AWS
docs allow `L`, `W`, and `#` extensions in the latest SDK; in
practice, **most production teams only need `* , - / ?`**.

### The three AWS quirks

#### Quirk 1 — `?` instead of `*` for day-of-week

In Linux cron, day-of-month and day-of-week are *independent* — `* * *`
means "every day." In AWS cron, you **must** set one of them to `?`.
If both are `*` the service rejects the expression because the
*intent* is ambiguous.

| Linux cron | AWS cron | Meaning |
|---|---|---|
| `0 2 * * *` | `cron(0 2 * * ? *)` | every day at 2 AM UTC |
| `0 2 * * 1` | `cron(0 2 ? * 1 *)` | every Monday at 2 AM UTC |
| `0 2 1 * *` | `cron(0 2 1 * ? *)` | first of every month at 2 AM UTC |
| `0 2 1 * MON` | `cron(0 2 ? * MON *)` | same as Monday |

If you see a `ValidationException` complaining that "the day-of-month
and day-of-week fields cannot both contain a wildcard," **swap one of
the `*` for `?`**. This single change fixes ~80% of cron syntax
errors.

#### Quirk 2 — UTC by default

The hour field is `0–23` **in UTC**. A cron that says `cron(0 9 * * ? *)`
fires at 9 AM UTC, which is 4 AM EST, 1 AM PST, etc. We fix this
in L23 with `ScheduleExpressionTimezone="America/Los_Angeles"`.

#### Quirk 3 — year is required

Linux cron uses 5 fields. AWS cron uses 6. **You must include the
year** even if it is `*`. `cron(0 9 * * ?)` (no year) fails with a
validation error.

### Real cron examples for production

| Cron | Meaning |
|---|---|
| `cron(0 2 * * ? *)` | 2 AM UTC, every day |
| `cron(0 2 ? * MON-FRI *)` | 2 AM UTC, weekdays |
| `cron(0 0 1 * ? *)` | midnight UTC on the 1st of every month |
| `cron(0 */4 * * ? *)` | every 4 hours, on the hour |
| `cron(15 9 ? * MON-FRI *)` | 9:15 AM UTC, weekdays |
| `cron(0 8 ? * 2#1 *)` | 8 AM UTC on the **first Monday** of the month |
| `cron(0 0 L * ? *)` | midnight UTC on the **last day** of the month |
| `cron(30 14 ? * WED *)` | 2:30 PM UTC, every Wednesday |

### Idempotency and quotas

A single AWS account gets:

- **1 million active schedules** per region (soft quota).
- **1 invocation per second per account** for the Scheduler service
  by default. If your cron fires 100k invocations per minute the
  service will **buffer** them and may fail-fast if the backlog grows
  too large. The fix is `FlexibleTimeWindow` (L23).
- **14 million invocations per month** in the free tier.

### What if I want both rate and cron features?

You cannot combine them. A `ScheduleExpression` is either a `rate(…)`
or a `cron(…)` literal. If you need "every 5 minutes, but only
between 9 and 5," you use a cron with `0/5` in the minute field and
`9-17` in the hour field:

```python
"cron(0/5 9-17 * * ? *)"  # every 5 min, 9 AM to 5 PM UTC
```

That single expression replaces what would otherwise be a 9-line
Lambda function.

### Pitfalls

1. **Storing cron strings in environment variables.** A common
   mistake is shipping a cron in a `.env` file with the *Linux* 5-field
   format. Always validate against the AWS 6-field dial in CI; the
   fastest check is `botocore.validate` or a regex like
   `^cron\(\S+ \S+ \S+ \S+ \S+ \S+\)$`.
2. **Forgetting UTC.** A `cron(0 9 * * ? *)` is *not* "9 AM in your
   local time." If you mean local time, set
   `ScheduleExpressionTimezone="America/Los_Angeles"` (covered in L23).
3. **DST gaps.** A `cron(0 2 * * ? *)` in `America/Los_Angeles` on
   the spring-forward day will not fire because 2 AM does not exist
   that day. Either pick a different hour or accept the gap.

## Hands-on

Open `05_schedules/code/schedule_cron.py` and look at the `SCHEDULES`
table near the top. Try writing your own cron expression by changing
one of the entries and re-running with `--dry-run` (see L24). The
script will *print* the boto3 payload it would have sent, so you can
verify your cron syntax before you ever hit AWS.

```bash
cd 05_schedules/code
python3 schedule_cron.py --dry-run
```

You should see a JSON dump of the `create_schedule` call for every
schedule in the `SCHEDULES` table.

## Quiz prep

These are the section-5 cron/rate questions:

- What does `?` mean, and why do you need it?
- Write a cron for "every 5 minutes between 9 AM and 5 PM UTC."
- What's the difference between `rate(1 hours)` and `rate(1 hour)`?

## Further reading

- AWS docs: [Cron and rate expressions](https://docs.aws.amazon.com/scheduler/latest/UserGuide/schedule-types.html)
- AWS docs: [Cron expression reference](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-schedule-expressions.html)
- `../../SYLLABUS.md` — full lecture map.

## What's next

In **L23** we cover **one-off schedules** (`at(…)`) and **time zones**.
This is where 8 AM *PST* becomes possible, and where you finally
learn how `FlexibleTimeWindow` works.

**Ready? Let's get time-zone aware.**