---
lecture: L24
title: "Section 5 Recap + Walk-Through of schedule_cron.py"
duration: "8:00"
section: 5
prereqs:
  - L21
  - L22
  - L23
downloads:
  - "../../downloads/eventbridge_cheat_sheet.pdf"
---

# L24 — Section 5 Recap + Walk-Through of `schedule_cron.py`

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 5 — EventBridge Scheduler
> **Duration:** 8:00

## Prereqs

- Watched **L21, L22, L23** in this section.
- Python 3.11+ installed and the `requirements.txt` dependencies
  installed (`boto3`, `moto[events]`, `pytest`).

## Key terms

- **Idempotent script** — a script that can be run twice in a row
  and produce the same end state. Our demo uses
  `update_schedule` (or `create_schedule_group` for the group),
  which is a *create-or-update* call against the resource name.
- **`--dry-run`** — a CLI flag that prints the boto3 call we *would*
  have made, without actually making it. Every script in this
  course supports it; it is invaluable for code review.
- **ScheduleExpressionTimezone** — the IANA tz string from L23.
- **FlexibleTimeWindow** — the `OFF`/`FLEXIBLE` window from L23.

## Lecture

Hi, I'm Prem Vishnoi. Welcome to the section-5 recap. In the last
three lectures we covered Scheduler 101 (L21), cron/rate syntax
(L22), and one-off schedules + time zones + flexible windows (L23).
Now we put it all together with a real, idempotent, dry-run-able
boto3 program.

### The full set of section-5 concepts

| Lecture | Concept | How it shows up in code |
|---|---|---|
| L21 | Scheduler replaces CW Events schedule | we use `boto3.client("scheduler")`, **not** `events` |
| L21 | Universal targets | we target a Lambda via `Target.Arn` |
| L21 | IAM role | every schedule needs `Target.RoleArn` |
| L22 | `rate(…)` | one of the demo schedules |
| L22 | `cron(…)` | one of the demo schedules |
| L22 | `?` wildcard | the cron expressions use `?` for day-of-week |
| L23 | `at(…)` one-off | one of the demo schedules |
| L23 | `ScheduleExpressionTimezone` | the cron schedule uses `America/Los_Angeles` |
| L23 | `FlexibleTimeWindow` | one schedule uses `FLEXIBLE` for load smoothing |

### Walk-through of `05_schedules/code/schedule_cron.py`

Open the file. The top of the file is a `SCHEDULES` table — a list
of dictionaries, one per schedule we want to create:

```python
SCHEDULES = [
    {
        "name": "demo-rate-5min",
        "expression": "rate(5 minutes)",
        "expression_timezone": None,
        "flexible_window_minutes": 0,   # 0 = OFF (exact)
        "input_payload": {"job": "heartbeat"},
    },
    {
        "name": "demo-cron-weekday-morning",
        "expression": "cron(0 8 * * MON-FRI *)",
        "expression_timezone": "America/Los_Angeles",
        "flexible_window_minutes": 10,  # 10-minute flexible window
        "input_payload": {"job": "morning-digest"},
    },
    {
        "name": "demo-at-one-off",
        "expression": "at(2099-12-31T23:59:00)",
        "expression_timezone": None,
        "flexible_window_minutes": 0,
        "input_payload": {"job": "century-mark"},
    },
]
```

The three rows deliberately exercise:

- A `rate(5 minutes)` schedule (L22).
- A `cron(0 8 * * MON-FRI *)` schedule in
  `America/Los_Angeles` with a 10-minute flexible window
  (L22 + L23).
- An `at(2099-12-31T23:59:00)` one-off (L23).

#### Function: `build_flexible_window(minutes)`

A small helper that turns the integer `0` (or any int) into the
correctly-typed `FlexibleTimeWindow` dict. `0` means "fire exactly
on time," so we return `{"Mode": "OFF"}`. Otherwise we return
`{"Mode": "FLEXIBLE", "MaximumWindowInMinutes": minutes}`.

This is the kind of small helper that prevents a class of bugs
in real code. If you forget to set `MaximumWindowInMinutes` for a
`FLEXIBLE` window, the API returns a `ValidationException`.

#### Function: `create_or_update_schedule(client, spec, dry_run)`

The idempotency workhorse. It tries `create_schedule` and falls
back to `update_schedule` if the schedule already exists:

```python
try:
    client.create_schedule(**params)
except client.exceptions.ConflictException:
    client.update_schedule(**params)
```

`ConflictException` is the boto3 type for a "resource with that
name already exists." Catching it and falling back to
`update_schedule` is the standard pattern for any "create-or-update"
script in AWS-land.

In `--dry-run` mode, the function only prints the JSON payload it
would have sent:

```python
print(json.dumps(params, indent=2, default=str))
```

This is the single most useful pattern in the whole course — you
can run the script in dry-run mode during code review and see
*exactly* what it intends to do.

#### Function: `main()`

The CLI entry point. Parses `--dry-run`, optionally accepts
`--region`, then iterates the `SCHEDULES` table and calls
`create_or_update_schedule` for each row. The function also creates
the `default` schedule group if it does not exist (idempotently).

### What the tests do

`test_schedule_cron.py` has **6 tests**:

1. `test_rate_expression_format` — pure-Python check that
   `rate(5 minutes)` is the canonical form.
2. `test_cron_six_fields` — pure-Python check that every cron in
   `SCHEDULES` has the AWS-required 6 fields and that exactly one
   of `day-of-month` / `day-of-week` is `?`.
3. `test_flexible_window_helper` — unit test for
   `build_flexible_window(0)` → `OFF` and
   `build_flexible_window(10)` → `FLEXIBLE` with the right window.
4. `test_dry_run_does_not_call_aws` — uses moto's `mock_aws` to
   prove that `--dry-run` does not actually create a schedule.
5. `test_create_or_update_is_idempotent` — runs the create
   function twice under `mock_aws`; the second call should
   succeed and end with exactly one schedule in the group.
6. `test_legacy_events_rule_still_works` — a smaller-scoped
   `events.put_rule` test that demonstrates the legacy
   CloudWatch Events schedule syntax. This is the
   "you may need to patch the boto3 client lookup" comment
   the spec asked for: in some CI environments `mock_aws` does
   not register a full `scheduler` backend, and you can fall
   back to testing through the public `events` rule API.

### How to run it

```bash
# 1. Dry-run (no AWS calls)
python3 schedule_cron.py --dry-run

# 2. With real AWS credentials (idempotent — safe to re-run)
python3 schedule_cron.py

# 3. In a specific region
python3 schedule_cron.py --region us-west-2
```

The `default` schedule group is created if missing, and every
schedule is created-or-updated.

### Common failure modes the demo guards against

| Failure | How the demo handles it |
|---|---|
| Schedule already exists | `ConflictException` → `update_schedule` |
| Group already exists | `ConflictException` → swallow |
| `?` missing from cron | The unit test catches this; cron validator would catch it in CI |
| `MaximumWindowInMinutes` missing for `FLEXIBLE` | `build_flexible_window` requires the int; passing `None` would be a `TypeError` |
| Time zone typo | IANA tz strings are validated lazily; `boto3` returns `ValidationException` if the tz is unknown |

## Hands-on

Run the demo locally:

```bash
cd 05_schedules/code
python3 schedule_cron.py --dry-run
```

You should see three JSON payloads, one per row in `SCHEDULES`. Then
run the test suite:

```bash
cd /Users/vishnoiprem/PycharmProjects/data-etl-ml/data-engineering/data-engineering-course/aws_eventbridge_course
python3 -m pytest 05_schedules/code/test_schedule_cron.py -v
```

All 6 tests should pass. The `mock_aws` decorator provides a
fake AWS environment; no real AWS calls are made.

## Quiz prep

These are the section-5 recap questions to focus on:

- Which boto3 client do you use for EventBridge Scheduler?
  (`scheduler`, **not** `events`)
- What is the difference between `create_schedule` and
  `update_schedule`? (create errors if the schedule exists;
  update creates or modifies)
- How do you make a cron fire at 8 AM Eastern? (set
  `ScheduleExpressionTimezone="America/New_York"` and write
  `cron(0 8 * * ? *)`)

## Further reading

- AWS docs: [EventBridge Scheduler API reference](https://docs.aws.amazon.com/scheduler/latest/UserGuide/managing-schedule.html)
- `../code/schedule_cron.py` — the demo
- `../code/test_schedule_cron.py` — the tests
- `../../quizzes/section_5.md` — section quiz
- `../../downloads/eventbridge_cheat_sheet.pdf` — one-page reference

## What's next

In **section 6** we move on to **Pipes, Archives, and Replay** —
the three features that make EventBridge useful for *reactive*
(point-to-point) workloads, not just pub/sub and cron. The recap
lecture for section 6 is **L29**.

**Ready? Let's look at Pipes.**
