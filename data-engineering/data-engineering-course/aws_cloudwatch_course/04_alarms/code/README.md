# `put_metric_alarm` — CloudWatch Alarms demo

> Companion to L17/L19. Author: Prem Vishnoi <prem.vishnoi@example.com>

## What it does

1. Creates an SNS topic `cw-demo-pager` (idempotent).
2. Sets a topic policy so CloudWatch can publish to it.
3. Subscribes a placeholder email.
4. Creates a metric alarm: `AWS/EC2 CPUUtilization > 70%` for 3 of 3
   60-second periods, with the SNS topic as the alarm action.
5. Calls `describe_alarms` to confirm the alarm.

## Run

```bash
python3 04_alarms/code/put_metric_alarm.py
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

## Test

```bash
python3 -m pytest 04_alarms/code/ -v
```

5 moto tests pass; no AWS credentials needed.
