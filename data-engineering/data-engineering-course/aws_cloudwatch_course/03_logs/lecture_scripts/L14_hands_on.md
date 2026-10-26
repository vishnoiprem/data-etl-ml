---
lecture: L14
title: "Hands-on: build `create_log_group.py` + 5 moto tests"
duration: "8:00"
section: 3
prereqs: ["L13"]
---

# L14 — Hands-on: build `create_log_group.py` + 5 moto tests

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 3 — CloudWatch Logs
> **Duration:** 8:00

## Prereqs

L13 (Insights primer).

## Key terms

(All covered in L10–L13. No new terms.)

## Lecture

This lecture walks you through `03_logs/code/create_log_group.py` and
its 5 moto tests.

### What the script does

1. Creates the log group `/myapp/api` (idempotent).
2. Sets the retention policy to 30 days.
3. Creates a log stream `demo-stream` inside that group.
4. Writes 3 structured (JSON) log events with timestamps 60 s apart.
5. Reads back the events with `filter_log_events` filtered by
   `startTime` / `endTime`.
6. Confirms only 2 of the 3 events are returned (the time filter
   excludes the oldest).

### How to run

```bash
cd aws_cloudwatch_course
python3 03_logs/code/create_log_group.py
# or:
python3 03_logs/code/create_log_group.py --dry-run
```

Required IAM permissions for real AWS:

```
logs:CreateLogGroup
logs:CreateLogStream
logs:PutLogEvents
logs:PutRetentionPolicy
logs:FilterLogEvents
logs:DescribeLogGroups
```

### How the tests work

`test_create_log_group.py` uses `moto.mock_aws`. Five tests cover:

1. `test_create_log_group_is_idempotent` — running the create twice
   does not raise.
2. `test_log_stream_is_created` — the demo stream appears in
   `describe_log_streams`.
3. `test_put_log_events_records_three_events` — the put call writes
   3 events to the (mocked) store.
4. `test_filter_log_events_by_time_returns_window` — the time filter
   excludes events outside the window.
5. `test_dry_run_does_not_call_put_log_events` — `--dry-run` suppresses
   the API call.

### Run the tests

```bash
cd aws_cloudwatch_course
python3 -m pytest 03_logs/code/ -v
```

5 tests pass in < 1 second.

## Hands-on

```bash
cd /Users/vishnoiprem/PycharmProjects/data-etl-ml/data-engineering/data-engineering-course/aws_cloudwatch_course
python3 03_logs/code/create_log_group.py
python3 -m pytest 03_logs/code/ -v
```

## Quiz prep

- Why is the demo's time filter useful? (Demonstrates
  `filter_log_events` with a real window — the basis for
  "show me errors in the last 5m" patterns.)
- What happens if you re-run `create_log_group`? (It's idempotent;
  no exception is raised.)

## Further reading

- `03_logs/code/create_log_group.py` — the script.
- `03_logs/code/test_create_log_group.py` — the tests.

## What's next

Section 4 — CloudWatch Alarms.
