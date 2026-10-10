# `create_log_group` — CloudWatch Logs demo

> Companion to L12/L14. Author: Prem Vishnoi <prem.vishnoi@example.com>

## What it does

1. Creates the log group `/myapp/api` (idempotent).
2. Sets retention to 30 days.
3. Creates a log stream `demo-stream`.
4. Writes 3 structured (JSON) log events 60 s apart.
5. Reads back with `filter_log_events`, filtered by a time window.
6. Prints how many events fall inside the window.

## Run

```bash
python3 03_logs/code/create_log_group.py
python3 03_logs/code/create_log_group.py --dry-run
```

Required IAM permissions (real AWS):

```
logs:CreateLogGroup
logs:CreateLogStream
logs:PutLogEvents
logs:PutRetentionPolicy
logs:FilterLogEvents
```

## Test

```bash
python3 -m pytest 03_logs/code/ -v
```

5 moto tests pass; no AWS credentials needed.
