# L16 — CloudWatch 101 (for Glue Job monitoring)

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 3 — S3 / CLI / CloudFormation / CloudWatch
> **Duration target:** 3:30

## What this lecture covers

- The 3 CloudWatch concepts every Glue user must know: **Metrics**, **Logs**, and **Alarms**.
- The Glue-specific log group: `/aws-glue/jobs/logs-v2/`.
- The Glue-specific metrics we'll use in Section 9 (streaming) and Section 10 (DQ).

## Narration

> "CloudWatch is the AWS monitoring service. The 3 things it does: 1) **Metrics** — a time series of numerical values (e.g., `glue.driver.streaming.batchProcessingTimeInMs` over the last hour). 2) **Logs** — a stream of text from your Glue Job's stdout/stderr, organized into log groups and log streams. 3) **Alarms** — a rule that watches a metric and fires when the rule is violated (e.g., `glue.driver.streaming.batchProcessingTimeInMs > 60000` for 1 minute → send to SNS). For Glue, the most common log group is `/aws-glue/jobs/logs-v2/`. Your Glue Job's stdout goes to a log stream inside this group; you can find it by Job run ID in the console. The 3 most common Glue metrics: `glue.driver.streaming.batchProcessingTimeInMs` (Section 9 streaming p99 latency), `glue.driver.streaming.schemaDiscovered` (Section 9 schema-drift detection), and `glue.dataset.metrics.RuleEvaluationStatus` (Section 10 DQ pass/fail). In Section 7, we'll see the Job's logs in CloudWatch. In Section 9, we'll graph the streaming metrics. In Section 10, we'll wire a CloudWatch alarm to an SNS topic for DQ alerts."

## Key bullets

- **Metrics** are time-series of numbers; CloudWatch stores them with a configurable retention (default 15 months).
- **Logs** are text streams; CloudWatch Logs Insights lets you query them with a SQL-like language.
- **Alarms** are rules on metrics; they can fire actions (SNS, Lambda, Auto Scaling).
- For Glue: log group is `/aws-glue/jobs/logs-v2/`; metrics are in the `glue.*` namespace.
- The 3 Glue metrics we use: `batchProcessingTimeInMs`, `schemaDiscovered`, `RuleEvaluationStatus`.

## On-screen

- A diagram: Glue Job → CloudWatch Logs (stdout/stderr) + CloudWatch Metrics (counters) + CloudWatch Alarms (rules).
- The 3 metrics listed in a table: name / namespace / what it measures.