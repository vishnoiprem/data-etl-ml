---
lecture: L29
title: "Hands-on: build `subscription_filter.py` + 4 moto tests"
duration: "14:00"
section: 6
prereqs: ["L28"]
---

# L29 — Hands-on: build `subscription_filter.py` + 4 moto tests

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 6 — Logs Insights + Subscriptions
> **Duration:** 14:00

## Prereqs

L28 (Lambda destination).

## Key terms

(All covered in L25–L28.)

## Lecture

This lecture walks you through `06_logs_insights_subs/code/subscription_filter.py`
and its 4 moto tests.

### What the script does

1. Creates a CloudWatch log group `/myapp/api` (idempotent).
2. Creates a Kinesis data stream `cw-demo-logs-stream` (1 shard).
3. Creates a subscription filter `errors-to-kinesis` with pattern
   `ERROR`, destination = the stream ARN, role = a placeholder.
4. Confirms the filter is in place via `describe_subscription_filters`.

### How to run

```bash
cd aws_cloudwatch_course
python3 06_logs_insights_subs/code/subscription_filter.py
# or:
python3 06_logs_insights_subs/code/subscription_filter.py --dry-run
```

Required IAM permissions (real AWS):

```
logs:CreateLogGroup
logs:PutSubscriptionFilter
logs:DescribeSubscriptionFilters
kinesis:CreateStream
kinesis:DescribeStream
iam:PassRole
```

### How the tests work

`test_subscription_filter.py` uses `moto.mock_aws`. Four tests cover:

1. `test_create_subscription_filter` — filter is in place after the
   `put_subscription_filter` call.
2. `test_subscription_filter_destination_attached` — the filter's
   `destinationArn` matches the stream.
3. `test_subscription_filter_pattern_matches` — the filter's
   `filterPattern` is what we set.
4. `test_dry_run_does_not_call_put_subscription_filter` — `--dry-run`
   suppresses the API call.

### Run the tests

```bash
cd aws_cloudwatch_course
python3 -m pytest 06_logs_insights_subs/code/ -v
```

4 tests pass in < 1 second.

## Hands-on

```bash
cd /Users/vishnoiprem/PycharmProjects/data-etl-ml/data-engineering/data-engineering-course/aws_cloudwatch_course
python3 06_logs_insights_subs/code/subscription_filter.py
python3 -m pytest 06_logs_insights_subs/code/ -v
```

## Quiz prep

- What destinations can a subscription filter target? (Kinesis,
  Firehose, Lambda.)
- How many filters per log group? (2.)
- What does `--dry-run` do? (Prints API calls, suppresses them.)

## Further reading

- `06_logs_insights_subs/code/subscription_filter.py` — the script.
- `06_logs_insights_subs/code/test_subscription_filter.py` — the tests.

## What's next

Section 7 — Real-World Patterns.
