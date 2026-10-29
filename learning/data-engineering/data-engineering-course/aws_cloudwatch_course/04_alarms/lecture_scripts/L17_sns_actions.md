---
lecture: L17
title: "SNS as Alarm Action — wiring the on-call pager"
duration: "10:00"
section: 4
prereqs: ["L16"]
---

# L17 — SNS as Alarm Action — wiring the on-call pager

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 4 — CloudWatch Alarms
> **Duration:** 10:00

## Prereqs

L16 (period / datapoints).

## Key terms

- **SNS topic** — Amazon Simple Notification Service. A pub/sub bus
  that fans out a message to N subscribers.
- **Subscription** — a destination (email, SMS, Lambda, SQS, HTTP
  endpoint) attached to a topic.
- **Topic policy** — the IAM policy on the topic that controls who can
  publish and subscribe.
- **CloudWatch → SNS → Lambda → PagerDuty** — the canonical on-call
  pipeline.

## Lecture

The canonical pattern for an alarm to page a human:

```
CloudWatch alarm  →  SNS topic  →  Lambda  →  PagerDuty / Slack / email
```

(SMS and email subscriptions are also possible directly from SNS, but
most teams route through Lambda for transformation, deduplication, and
integration with their on-call tool.)

### Creating the SNS topic

```python
import boto3

sns = boto3.client("sns")
cw  = boto3.client("cloudwatch")

# 1. Create the topic
topic = sns.create_topic(Name="oncall-pager")
topic_arn = topic["TopicArn"]

# 2. Subscribe an email
sns.subscribe(
    TopicArn=topic_arn,
    Protocol="email",
    Endpoint="oncall@example.com",
)
# (User must click the confirmation link in the email.)

# 3. Allow CloudWatch to publish
sns.set_topic_attributes(
    TopicArn=topic_arn,
    AttributeName="Policy",
    AttributeValue=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "AllowCloudWatchAlarms",
            "Effect": "Allow",
            "Principal": {"Service": "cloudwatch.amazonaws.com"},
            "Action": "SNS:Publish",
            "Resource": topic_arn,
        }],
    }),
)

# 4. Wire the alarm
cw.put_metric_alarm(
    AlarmName="checkout-p99-latency",
    ...,
    AlarmActions=[topic_arn],   # ← here
)
```

### What the SNS message looks like

SNS delivers a JSON blob to subscribers. The default CloudWatch
message looks like:

```json
{
  "AlarmName": "checkout-p99-latency",
  "AlarmDescription": "p99 > 500ms for 3-of-5 minutes",
  "AWSAccountId": "111122223333",
  "NewStateValue": "ALARM",
  "NewStateReason": "Threshold Crossed: 3 datapoints were ...",
  "StateChangeTime": "2026-10-10T14:23:01.000+0000",
  "Region": "us-east-1",
  "Trigger": {
    "MetricName": "Latency",
    "Namespace": "AWS/ApiGateway",
    "Statistic": "p99",
    "Dimensions": [{"name": "ApiName", "value": "checkout"}],
    "Period": 60,
    "EvaluationPeriods": 5,
    "DatapointsToAlarm": 3,
    "Threshold": 500,
    "ComparisonOperator": "GreaterThanThreshold"
  }
}
```

A Lambda subscriber can parse this and post to PagerDuty, Slack, etc.

### Gotchas

1. **Email subscriptions need confirmation** — the recipient has to
   click the link in the initial email before notifications start
   arriving.
2. **Cross-region** — SNS topics are regional. If your alarm is in
   `us-east-1`, the topic must be in `us-east-1`.
3. **Account-level fan-out** — for centralised paging across many
   accounts, create the topic in the *security / log-archive* account
   and use a Lambda to relay.
4. **`ActionsEnabled`** — a master switch. If you ever set it to
   `False` (e.g. during a planned maintenance), alarms still go to
   the ALARM state but **no actions fire**.

## Hands-on

In your AWS account:

1. Create a topic `oncall-demo`, subscribe your email.
2. Confirm the subscription (check inbox).
3. Create an alarm for any metric (e.g. `AWS/Lambda → Errors > 0` for
   1 min) with the topic as the alarm action.
4. Trigger the function with an error and watch the email arrive.

## Quiz prep

- What protocol types does SNS support? (email, sms, lambda, sqs,
  http/https, firehose, application)
- What is `ActionsEnabled=False`? (Master switch — alarms still
  transition but no actions fire.)
- Is SNS regional or global? (Regional.)

## Further reading

- `https://docs.aws.amazon.com/sns/latest/dg/sns-getting-started.html`

## What's next

L18 — Composite Alarms & Anomaly Detection Alarms.
