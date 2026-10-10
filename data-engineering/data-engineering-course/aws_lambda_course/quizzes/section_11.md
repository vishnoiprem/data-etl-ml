# Section 11 Quiz — AWS Lambda Advanced Concepts

> **10 questions** covering L47–L59. Answers are in collapsible
> blocks. Take the quiz *after* L59.

---

## Q1 — Concurrency fundamentals

What is the default account-level concurrent execution limit per
Region, and which AWS API do you call to change it?

<details>
<summary>Show answer</summary>

Default: **1,000 concurrent executions** per Region, per account.
Change with **`put_account_concurrency`** in the AWS SDK, or via
**Lambda → Settings → Concurrency → Edit account concurrency** in
the console. Increases are subject to AWS approval (soft limit).
</details>

---

## Q2 — Reserved vs. provisioned concurrency

A function sits behind an API Gateway endpoint. Its p99 cold start
is 1.4 seconds, which violates the team's 300 ms latency SLO. The
team is on a tight budget but cannot tolerate the latency. Which
concurrency feature should they reach for first, and why?

<details>
<summary>Show answer</summary>

**Provisioned concurrency** on the function's production alias.
Reserved concurrency only *caps* how many instances can run; it does
not pre-warm any of them, so it does not fix cold starts. Provisioned
concurrency keeps N environments warm and ready, eliminating cold
starts for the configured count. They can pair it with Application
Auto Scaling to track demand so they don't pay for peak at 3 a.m.
</details>

---

## Q3 — Memory limits

What is the relationship between Lambda memory setting, CPU, and
ephemeral disk size?

<details>
<summary>Show answer</summary>

They scale **linearly and proportionally**. Memory is the master
knob; CPU, network bandwidth, and `/tmp` disk space are derived from
it. At 1,769 MB you get approximately 0.5 vCPU; at 10,240 MB you get
approximately 6 vCPU. `/tmp` ranges from 512 MB to 10,240 MB, scaling
with memory. There is no separate CPU setting.
</details>

---

## Q4 — VPC networking

A function needs to query an RDS Postgres instance in a private
subnet. Which of the following is *not* required?

A. The function's execution role must include the
   `AWSLambdaVPCAccessExecutionRole` policy (or equivalent).
B. The function must be placed in a private subnet.
C. The function's security group must allow inbound traffic from the
   RDS security group on port 5432.
D. The Lambda must be invoked through a VPC Endpoint.

<details>
<summary>Show answer</summary>

**D.** A VPC Endpoint is not required. The Lambda connects to RDS
through the VPC's router using the Hyperplane ENI. (A), (B), and (C)
are all required: the execution role needs ENI permissions, the
subnet must be private, and the security groups must allow the
Lambda-to-RDS connection (typically as an outbound rule on the
Lambda SG and an inbound rule on the RDS SG, since Lambda is never
called on its ENI).
</details>

---

## Q5 — CloudWatch metrics

Which CloudWatch metric tells you that your function is being
throttled by Lambda's concurrency controls?

<details>
<summary>Show answer</summary>

`AWS/Lambda → Throttles` (namespace). Throttles count the
invocations rejected with `TooManyRequestsException` (HTTP 429).
Watch this in conjunction with `ConcurrentExecutions` (current
in-flight count) and your account's concurrent execution limit.
</details>

---

## Q6 — Logs and retention

A function's log group `/aws/lambda/my-api` has no retention policy
set. After 12 months of running, what is the consequence?

<details>
<summary>Show answer</summary>

**Log events are kept forever** and you pay CloudWatch Logs storage
forever. A typical 128 MB function logging ~5 lines per invocation
at 1,000 RPS produces dozens of GB per day. After a year, the bill
is significant. Set a retention policy (e.g. 30 days dev, 90 days
prod) with `aws logs put-retention-policy` or
`put_retention_policy` in boto3.
</details>

---

## Q7 — Versions

You publish version 5 of `my-api`. Tomorrow you change the
function's memory on `$LATEST` from 1,024 MB to 2,048 MB, but you
do *not* publish a new version. Does version 5 run with 1,024 MB
or 2,048 MB?

<details>
<summary>Show answer</summary>

**1,024 MB.** Versions are immutable snapshots of `$LATEST` at the
moment of `publish_version`. Editing `$LATEST` after publishing
version 5 has no effect on version 5. If you want version 5 to use
2,048 MB, you would have to publish a new version (6) after the
change.
</details>

---

## Q8 — Aliases and weighted routing

You want to send 95% of traffic to version 12 and 5% to version 13
of `my-api`, using a `prod` alias. Write the boto3 call.

<details>
<summary>Show answer</summary>

```python
import boto3
lam = boto3.client("lambda", region_name="us-east-1")
lam.update_alias(
    FunctionName="my-api",
    Name="prod",
    FunctionVersion="12",                       # primary
    RoutingConfig={"AdditionalVersionWeights": {"13": 0.05}},
)
```

95% goes to version 12 (the primary), 5% to version 13. To roll
forward, update the call to make 13 primary and remove the
`RoutingConfig`. To roll back, change `FunctionVersion` back to 12
and remove the routing.
</details>

---

## Q9 — Environment variables and secrets

You want the function to use a database password that lives in
Secrets Manager, but you do not want the plaintext password visible
in the function configuration. How do you do this?

<details>
<summary>Show answer</summary>

Set the env var to a **Secrets Manager reference placeholder**:

```python
lam.update_function_configuration(
    FunctionName="my-api",
    Environment={
        "Variables": {
            "DB_PASSWORD": (
                "{{resolve:secretsmanager:"
                "arn:aws:secretsmanager:us-east-1:111122223333:secret:db-pw-XXXXXX}}"
            )
        }
    },
)
```

Lambda resolves the placeholder before invoking your code. The
function's execution role must have `secretsmanager:GetSecretValue`
on the secret ARN. Note: the resolved value is cached for the
lifetime of the execution environment, so rotated secrets may take
up to 15 minutes to take effect in a warm function.
</details>

---

## Q10 — Putting it together

A team has 8 Lambda functions across 3 services. They want a single
dashboard that shows invocations, errors, p99 duration, and
throttles for each function, plus an alarm that pages when *any*
function's error rate exceeds 5% for 5 minutes. Sketch the
implementation in 5–8 lines of boto3 (pseudocode is fine).

<details>
<summary>Show answer</summary>

```python
import json, boto3
cw = boto3.client("cloudwatch", region_name="us-east-1")
functions = ["svc-a-worker", "svc-b-api", "svc-c-api", "..."]
widgets = []
for i, fn in enumerate(functions):
    widgets += [{
        "type": "metric",
        "x": (i % 4) * 6, "y": (i // 4) * 6,
        "width": 6, "height": 6,
        "properties": {
            "title": fn,
            "metrics": [
                ["AWS/Lambda", "Invocations", "FunctionName", fn, {"stat": "Sum"}],
                ["...", "Errors",  ".",          ".",   {"stat": "Sum", "color": "#d62728"}],
                ["...", "Duration", ".",          ".",   {"stat": "p99"}],
                ["...", "Throttles", ".",         ".",   {"stat": "Sum", "color": "#ff7f0e"}],
            ],
            "view": "timeSeries",
        },
    }]
cw.put_dashboard(DashboardName="all-functions", DashboardBody=json.dumps({"widgets": widgets}))
for fn in functions:
    cw.put_metric_alarm(
        AlarmName=f"{fn}-error-rate",
        Namespace="AWS/Lambda", MetricName="Errors",
        Statistic="Sum", Period=60, EvaluationPeriods=5,
        DatapointsToAlarm=3, Threshold=10,
        ComparisonOperator="GreaterThanThreshold",
        Dimensions=[{"Name": "FunctionName", "Value": fn}],
        AlarmActions=["arn:aws:sns:us-east-1:111122223333:oncall"],
    )
```

(Real-world: alarm on `Errors / Invocations > 0.05` with a metric
math expression; the above uses an absolute threshold as a
simplification.) The dashboard has one widget per function with four
metric lines. The alarms use `put_metric_alarm` and an SNS topic.
</details>
