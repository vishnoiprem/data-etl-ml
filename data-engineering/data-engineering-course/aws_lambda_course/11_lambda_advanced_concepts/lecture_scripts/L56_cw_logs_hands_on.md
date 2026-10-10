---
title: L56 — Lambda Monitoring — CloudWatch Logs — Hands On
author: Prem Vishnoi <prem.vishnoi@example.com>
section: 11
duration: 5:27
---

# L56 — Lambda Monitoring — CloudWatch Logs — Hands On

> This lecture walks through five things you do with Lambda logs
> every week: set retention, find errors, scan cold starts, sum
> business counters, and ship to a longer-term destination
> (CloudWatch Logs Insights in our case).

## Prereqs

- L55 (theory).
- An existing function with some history.

## Key terms

- **CloudWatch Logs Insights** — serverless SQL-like query engine
  over CloudWatch Logs.
- **`StartQuery`** / **`GetQueryResults`** — boto3 API for Insights.
- **Field name `@message`, `@timestamp`, `@duration`** — reserved in
  Insights.

## 1. Set retention

```bash
aws logs put-retention-policy \
    --log-group-name /aws/lambda/my-api \
    --retention-in-days 30
```

Repeat for every function. (If your account has 40 functions,
consider a small script using `describe_log_groups` + paging.)

## 2. Find errors

The Insights query:

```sql
fields @timestamp, @requestId, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 50
```

Run from the console or via:

```python
import boto3, time
logs = boto3.client("logs", region_name="us-east-1")
resp = logs.start_query(
    logGroupName="/aws/lambda/my-api",
    startTime=int((time.time() - 24*3600) * 1000),
    endTime=int(time.time() * 1000),
    queryString="""
        fields @timestamp, @requestId, @message
        | filter @message like /ERROR/
        | sort @timestamp desc
        | limit 50
    """,
)
qid = resp["queryId"]
while True:
    r = logs.get_query_results(queryId=qid)
    if r["status"] in ("Complete", "Failed", "Cancelled"):
        break
    time.sleep(1)
for row in r["results"]:
    print(row)
```

## 3. Scan cold starts

```
fields @timestamp, @duration, @initDuration
| filter @type = "REPORT"
| stats count() as invocations,
        count(@initDuration) as cold_starts,
        avg(@duration) as avg_ms,
        pct(@duration, 95) as p95_ms by bin(15m)
```

Tells you, per 15-minute bucket, how many invocations, what fraction
were cold, and the p95 cold-and-warm duration.

## 4. Sum a business counter (structured log)

Assuming the JSON logging from L55:

```sql
fields @timestamp
| filter @message like /request done/
| parse @message "\"n\":*]" as n
| stats sum(n) as total_processed by bin(1h)
```

## 5. Ship to a destination — async fan-out

To copy `/aws/lambda/*` to S3, Kinesis Data Firehose, or a
cross-account log group:

```python
logs = boto3.client("logs", region_name="us-east-1")
logs.put_subscription_filter(
    logGroupName="/aws/lambda/my-api",
    filterName="to-firehose",
    filterPattern="",
    destinationArn="arn:aws:firehose:us-east-1:111122223333:lambda-logs-firehose",
    roleArn="arn:aws:iam::111122223333:role/CWLtoFirehoseRole",
)
```

After this, every new log event is mirrored to the firehose → S3.
Pre-existing events are *not* copied (CloudWatch only streams
forward).

## 6. A "is everything ok" Insights panel

Three saved queries you can bookmark:

| Query | What it answers |
|---|---|
| `fields @timestamp \| filter @message like /ERROR/ \| stats count() by bin(5m)` | Error rate over time |
| `fields @timestamp \| filter @type = "REPORT" \| stats avg(@duration), pct(@duration,99) by bin(5m)` | Latency trend |
| `fields @timestamp \| filter @type = "REPORT" \| stats count(@initDuration) as cold by bin(5m)` | Cold-start trend |

## Lecture summary

- Set retention on every log group.
- CloudWatch Logs Insights is a serverless SQL over logs — use it.
- Three saved queries (errors, latency, cold starts) cover the
  nightly health check.

## Hands-on (≈ 4 minutes)

```bash
# 1. Set retention on every /aws/lambda/* group to 30 days
python 11_lambda_advanced_concepts/code/cw_set_retention.py --days 30

# 2. Run a saved query against your function
python 11_lambda_advanced_concepts/code/cw_insights.py \
    --function my-api \
    --query errors_5m

# 3. Set up an S3 destination
python 11_lambda_advanced_concepts/code/cw_destination_s3.py \
    --function my-api --bucket my-logs-bucket
```

## Quiz prep

- What boto3 function starts a Logs Insights query?
- How do you set a 90-day retention on `/aws/lambda/my-api`?
- What's the difference between `parse` and `filter` in Insights?

## Further reading

- AWS — [CloudWatch Logs Insights query syntax](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax.html)
- AWS — [Cross-account log subscriptions](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CrossAccountSubscriptions.html)
