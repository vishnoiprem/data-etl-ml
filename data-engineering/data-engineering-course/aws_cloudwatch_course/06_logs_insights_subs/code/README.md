# `subscription_filter` — CloudWatch subscription filter demo

> Companion to L25/L29. Author: Prem Vishnoi <pvishnoi@avilx.com>

## What it does

1. Creates a CloudWatch log group `/myapp/api` (idempotent).
2. Creates a Kinesis data stream `cw-demo-logs-stream` (1 shard).
3. Creates a subscription filter `errors-to-kinesis` with pattern
   `ERROR` and destination = the stream ARN.
4. Confirms the filter via `describe_subscription_filters`.

## Run

```bash
python3 06_logs_insights_subs/code/subscription_filter.py
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

## Test

```bash
python3 -m pytest 06_logs_insights_subs/code/ -v
```

4 moto tests pass; no AWS credentials needed.
