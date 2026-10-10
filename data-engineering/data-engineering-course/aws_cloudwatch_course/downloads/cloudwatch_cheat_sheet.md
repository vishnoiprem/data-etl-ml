# CloudWatch Cheat Sheet

> Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;

## Service limits (October 2026)

| Resource | Default limit |
|---|---|
| Alarms per region | 10,000 |
| Metric data points per `put_metric_data` call | 1,000 |
| Log groups per region | 20,000,000 |
| Log streams per log group | 100,000 (soft) |
| Subscription filters per log group | 2 |
| Dashboards per region | 500 (soft) |
| Widgets per dashboard | 100 (soft) |
| Metric filters per log group | 100 |

## Standard namespaces (subset)

| Namespace | Source |
|---|---|
| `AWS/EC2` | EC2 instance metrics |
| `AWS/Lambda` | Lambda invocations, duration, errors, throttles |
| `AWS/RDS` | RDS instance metrics |
| `AWS/ApiGateway` | API Gateway (REST + HTTP) |
| `AWS/States` | Step Functions |
| `AWS/S3` | S3 storage metrics (request metrics must be enabled) |
| `AWS/DynamoDB` | DynamoDB table + GSI metrics |
| `AWS/ELB` | ELB / ALB |
| `AWS/ECS` | ECS cluster + service metrics |
| `AWS/Kinesis` | Kinesis Data Streams |
| `AWS/Logs` | CloudWatch Logs |

## Alarm state cheatsheet

| State | Meaning | Default entry from |
|---|---|---|
| `OK` | Metric below threshold | alarm creation |
| `ALARM` | Threshold breached (m-of-n datapoints) | evaluation |
| `INSUFFICIENT_DATA` | Not enough datapoints yet | alarm creation |

## Alarm action targets

- `arn:aws:sns:<region>:<acct>:topic-name` — SNS topic
- `arn:aws:autoscaling:<region>:<acct>:autoScalingGroup:...` — ASG policy
- `arn:aws:lambda:<region>:<acct>:function:...` — Lambda
- `arn:aws:swf:<region>:<acct>:/actions/actions/AWS_EC2.InstanceId.Reboot/1.0` — EC2 action

## Common dimensions

- `InstanceId` (EC2)
- `FunctionName` (Lambda)
- `TableName` (DynamoDB)
- `ApiName`, `Stage` (API Gateway)
- `LogGroupName` (Logs)

## Common statistics

- `Average`, `Sum`, `Minimum`, `Maximum`, `SampleCount`
- `p99`, `p95`, `p90`, `p50`, `p10`, `p5` (extended statistics / percentiles)
