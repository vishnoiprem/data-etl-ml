---
lecture: L19
title: "Hands-on: build `put_metric_alarm.py` + 5 moto tests"
duration: "10:00"
section: 4
prereqs: ["L18"]
---

# L19 — Hands-on: build `put_metric_alarm.py` + 5 moto tests

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 4 — CloudWatch Alarms
> **Duration:** 10:00

## Prereqs

L18 (composite + anomaly detection).

## Key terms

(All covered in L15–L18.)

## Lecture

This lecture walks you through `04_alarms/code/put_metric_alarm.py`
and its 5 moto tests.

### What the script does

1. Creates an SNS topic `cw-demo-pager` (idempotent).
2. Subscribes a placeholder email subscription (we don't actually
   confirm it — the test mock doesn't deliver).
3. Creates a metric alarm on `AWS/EC2` `CPUUtilization` > 70% for 3 of
   3 periods of 60 s.
4. Wires the SNS topic as the alarm action.
5. Calls `describe_alarms` to confirm the alarm is configured
   correctly.

### How to run

```bash
cd aws_cloudwatch_course
python3 04_alarms/code/put_metric_alarm.py
# or:
python3 04_alarms/code/put_metric_alarm.py --dry-run
```

Required IAM permissions (real AWS):

```
cloudwatch:PutMetricAlarm
cloudwatch:DescribeAlarms
sns:CreateTopic
sns:Subscribe
sns:SetTopicAttributes
```

### How the tests work

`test_put_metric_alarm.py` uses `moto.mock_aws`. Five tests cover:

1. `test_create_alarm_writes_alarm` — the alarm is present after
   `put_metric_alarm`.
2. `test_create_alarm_is_idempotent` — re-running the create does
   not duplicate the alarm.
3. `test_alarm_has_sns_action` — the alarm's `AlarmActions` includes
   the topic ARN.
4. `test_alarm_is_enabled` — `ActionsEnabled=True` and
   `StateValue=INSUFFICIENT_DATA` (new alarms start in this state).
5. `test_dry_run_does_not_call_put_metric_alarm` — `--dry-run`
   suppresses the API call.

### Run the tests

```bash
cd aws_cloudwatch_course
python3 -m pytest 04_alarms/code/ -v
```

5 tests pass in < 1 second.

## Hands-on

```bash
cd /Users/vishnoiprem/PycharmProjects/data-etl-ml/data-engineering/data-engineering-course/aws_cloudwatch_course
python3 04_alarms/code/put_metric_alarm.py
python3 -m pytest 04_alarms/code/ -v
```

## Quiz prep

- What's the default starting state of a new alarm?
  (`INSUFFICIENT_DATA`.)
- Can an alarm have multiple actions? (Yes, up to 5 per state.)
- What does `TreatMissingData=notBreaching` do? (Treats a missing
  datapoint as not-breaching, so the alarm stays OK.)

## Further reading

- `04_alarms/code/put_metric_alarm.py` — the script.
- `04_alarms/code/test_put_metric_alarm.py` — the tests.

## What's next

Section 5 — CloudWatch Dashboards.
