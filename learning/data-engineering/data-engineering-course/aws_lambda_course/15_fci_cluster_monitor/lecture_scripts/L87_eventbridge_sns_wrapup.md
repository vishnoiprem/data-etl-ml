---
id: L87
title: EventBridge schedule, SNS topic, end-to-end test, course wrap-up
section: 15
duration: "12:00"
prereqs:
  - L82-L86
---

# L87 — EventBridge Schedule, SNS Topic, End-to-End Test, Course Wrap-up

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 15
> **Duration:** 12:00
> **Prereqs:** L82–L86

## What you will learn

By the end of this lecture you will be able to:

1. wire the monitor Lambda to an **EventBridge schedule** so it runs
   every 5 minutes without any servers;
2. publish to an **SNS topic** that fans out to email (and optionally
   PagerDuty) when the Lambda decides to grow the file system;
3. run the **end-to-end test** that simulates a low-storage condition
   using a `dry_run` flag in the event payload;
4. decide when the FCI pattern is the right tool and when a cheaper
   CloudWatch alarm + Lambda alone is enough;
5. summarise what you have built across sections 6, 8, and 15 — the
   three enterprise use cases — and where to go next.

## Key terms

- **EventBridge rule** — a cron-like scheduler that targets a Lambda,
  SQS queue, or SNS topic. The replacement for the old CloudWatch
  Events API.
- **SNS topic** — a pub/sub topic that fans out to N subscribers
  (email, SMS, Lambda, SQS, HTTP/S, mobile push).
- **Dry-run mode** — running the handler logic without performing the
  destructive side effect (here, `UpdateFileSystem`). Lets you
  exercise the code path in a test account without touching the
  file system.
- **End-to-end test** — a single test that drives the system through
  its real entry point (here, a scheduled event payload) and asserts
  on the observable side effect (an SNS publish, a log line, a tag
  on the file system).

## Lecture

Section 15's first five lectures built the data plane — the file
system, the directory, the monitor Lambda, the IAM role. This final
lecture wires the **control plane**: the schedule that wakes the
Lambda up, and the topic that notifies humans when the Lambda has
done something.

**EventBridge rule.** The schedule is a single `events:PutRule` plus
`events:PutTargets` call. The expression `cron(*/5 * * * ? *)` means
"every 5 minutes" — replace with whatever cadence the workload
actually needs (most FCI clusters do well with 15-30 minutes; the
cost is negligible because the function's idle time is free). The
target is the monitor Lambda's ARN, and the input is a constant JSON
document that the Lambda sees as its `event` argument. The same input
serves as the test fixture in `code/event_payloads/scheduled_event.json`,
which is what the `pytest` suite uses to drive the handler.

**SNS topic.** When the monitor decides to grow the volume, it
publishes a `Notification` to the topic with the FSx id, the old
size, the new size, and a human-readable reason. Subscribers are
configured out-of-band (an email address for ops, an HTTPS endpoint
for PagerDuty, a Lambda that opens a ticket). The course's
`fci_monitor_stack.yaml` provisions the topic; the email
subscription is a one-liner you can add from the console.

**End-to-end test.** The CloudFormation template ships with a
**dry-run parameter**. When set to `true`, the monitor's
environment has `DRY_RUN=1` and the handler's grow step is a no-op:
it logs the would-be call but does not invoke `UpdateFileSystem`.
The test fixture is just the JSON payload above; the assertion is
"the Lambda exited 0, the SNS publish happened, and the
CloudWatch log group received a `would-grow` line". In a real
account, flip the parameter to `false` and the file system grows
on the next tick.

**When to use the FCI pattern.** Section 15 is the right tool when
you have a real Windows workload (SQL Server, FSx for Windows,
.NET applications) that is sensitive to free-space outages and
where growing the file system is a routine, automated operation.
For a Linux workload, the same shape works — `DescribeVolumes` on
EBS instead of `DescribeFileSystems` on FSx — and the lecture
flags this as an exercise in `assignments/assignment_7_fci_monitor.md`.

**Course wrap-up.** Across the three enterprise use cases, you have
now built:

- **Section 6 (S3 + Lambda + DynamoDB):** an event-driven file
  processor with DLQ + retry, end-to-end observable.
- **Section 8 (API Gateway + Lambda + S3 + Cognito):** a serverless
  CRUD API with two flavours of auth (Lambda Authorizer + Cognito)
  and the full 4xx/5xx error model.
- **Section 15 (FCI Cluster Monitor):** a scheduled ops automation
  with EventBridge + SNS + CloudWatch + the auto-grow loop.

All three patterns share the same backbone: small, focused
Lambdas; least-privilege IAM; observable via CloudWatch; testable
end-to-end with `moto`. That is the 2026 serverless canon, and
the next courses in the track (advanced CDK, step functions,
event-driven architectures) build directly on top of it.

## Hands-on

Deploy the stack and watch the schedule run:

```bash
cd 15_fci_cluster_monitor/code/cloudformation
./deploy.sh
# wait 5 minutes
aws logs tail /aws/lambda/fci-monitor --follow
```

Then flip `DryRun` to `false` in the stack parameters and re-deploy
to watch the file system grow on the next tick.

## Quiz prep

- The cron expression for "every 5 minutes" is `cron(*/5 * * * ? *)`.
  Why is the day-of-week field `?` and not `*`?
- What is the difference between an SNS topic and an SNS FIFO topic?
- What does `dry_run=true` actually skip, and what does it still run?
- Which of the three enterprise use cases (sections 6, 8, 15) would
  you reach for first when the workload is event-driven file
  processing, and why?

## Further reading

- [EventBridge cron expressions](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-create-rule-schedule.html)
- [SNS subscription protocols](https://docs.aws.amazon.com/sns/latest/dg/sns-basic-subscribe.html)
- [FSx for Windows File Server auto-grow limits](https://docs.aws.amazon.com/fsx/latest/WindowsGuide/managing-file-systems.html)
