# Section 5 — EventBridge Scheduler (L21–L24)

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>

This section covers **EventBridge Scheduler**, the service that
replaces the legacy CloudWatch Events schedule API. By the end of
the four lectures you will know how to write cron, rate, and
one-off schedules, target any of the 20+ supported AWS services,
and tune the firing model for time zones and load.

## Lecture map

| L# | Title | File |
|---|---|---|
| L21 | Scheduler 101 (replacement for CW Events schedule) | `lecture_scripts/L21_scheduler_101.md` |
| L22 | Cron + rate expressions | `lecture_scripts/L22_cron_rate.md` |
| L23 | One-off schedules, time zones, flexible windows | `lecture_scripts/L23_oneoff_timezone.md` |
| L24 | Section recap + `schedule_cron.py` walk-through | `lecture_scripts/L24_section_recap.md` |

## What the demo does

`code/schedule_cron.py` is an **idempotent** boto3 program that
creates (or updates) three schedules inside a `default` schedule
group:

1. `demo-rate-5min` — a `rate(5 minutes)` schedule. Fires every 5
   minutes, in UTC, exactly on the minute. (L22)
2. `demo-cron-weekday-morning` — a `cron(0 8 * * MON-FRI *)` schedule
   in `America/Los_Angeles`, with a 10-minute flexible time window.
   Fires at 8 AM Pacific on weekdays, but the scheduler may pick any
   minute in the 8:00–8:10 PT window. (L22 + L23)
3. `demo-at-one-off` — an `at(2099-12-31T23:59:00)` schedule. Fires
   exactly once. (L23)

The script uses `boto3.client("scheduler")` (the **new** API, not
`events`) and supports `--dry-run` so you can review the boto3
payload before any real AWS call. The `create_or_update_schedule`
helper catches `ConflictException` and falls back to
`update_schedule`, which is what makes the script idempotent.

## What the tests do

`code/test_schedule_cron.py` runs **6 tests**:

- 3 pure-Python unit tests on the cron/rate syntax and the
  `build_flexible_window` helper.
- 2 moto tests (`mock_aws`) that verify `--dry-run` does not call
  AWS and that `create_or_update_schedule` is idempotent.
- 1 fallback `events.put_rule` test for environments where the
  `scheduler` mock backend is not available.

A note on moto support: as of `moto` 5.x, `mock_aws` registers a
`scheduler` backend that supports `create_schedule_group`,
`create_schedule`, `update_schedule`, `get_schedule`, and
`delete_schedule`. In some pinned CI environments the `scheduler`
mock is partial; in that case, fall back to testing through the
public `events` rule API (`events:PutRule` + `ScheduleExpression`),
which has been fully supported by `moto[events]` for years. The
demo and tests use `mock_aws`, with a comment documenting the
fallback strategy.

## How to run

```bash
# Dry-run — no AWS calls, just prints the boto3 payloads
python3 05_schedules/code/schedule_cron.py --dry-run

# Real AWS — idempotent
python3 05_schedules/code/schedule_cron.py

# Run the tests
python3 -m pytest 05_schedules/code/test_schedule_cron.py -v
```

## Quiz

See `../quizzes/section_5.md` for 10 questions on Scheduler, cron
syntax, rate expressions, time zones, and flexible windows.
