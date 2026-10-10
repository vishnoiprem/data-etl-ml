# Section 7 — Patterns + Real-World

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 7
> **Lectures:** L30–L36
> **Total duration:** ~75 min
> **Status:** full content in `lecture_scripts/`, no code demo

## What this section covers

This is the capstone. Sections 2–6 taught you the moving parts of
EventBridge — buses, rules, patterns, targets, scheduler, pipes,
archives. Section 7 puts those moving parts together into the
**production patterns** that real AWS accounts ship every day.

You will leave the course with:

- A **catalog of the 10 most common EventBridge patterns** and the
  decision tree for picking one (L30).
- A detailed walkthrough of the **S3 → Lambda** ingestion pattern
  with the exact JSON event pattern and IAM policy (L31).
- A detailed walkthrough of the **CloudWatch Alarm → SNS + SSM
  runbook** alerting pattern, including the self-healing
  remediation path (L32).
- A detailed walkthrough of the **API Gateway → Step Functions**
  long-running async workflow pattern, including why the
  EventBridge indirection is preferable to a direct integration
  (L33).
- A **DLQ strategy** with three concrete patterns (cross-target,
  per-target, self-healing re-drive) and the trade-offs of each
  (L34).
- A **cross-account + cross-region fan-out** strategy with the
  event bus resource policy and the organization-wide bus
  feature (L35).
- A **course wrap-up** with what you built, what to read next,
  and a personal sign-off (L36).

There is **no new code demo in this section**. The patterns
themselves are the artifact; everything you need to ship them is
in the lecture scripts and the existing `boto3` scripts from
sections 2–6.

## The 10 patterns (from L30)

| # | Name | Source → Bus | Typical Target(s) | When you reach for it |
|---|---|---|---|---|
| 1 | **S3 → Lambda** | S3 → default bus | Lambda | Object ingestion, image resize, CSV → Parquet |
| 2 | **CloudWatch Alarm → SNS** | CW → default bus | SNS topic (+ SSM runbook) | Paging humans, automated remediation |
| 3 | **API Gateway → Step Functions** | APIGW → custom bus | SFN state machine | Long-running async workflows started by an HTTP POST |
| 4 | **SQS → Step Functions** | SQS → Pipes | SFN | Worker pool + durable workflow combo |
| 5 | **DynamoDB Streams → Lambda** | DDB Streams → Pipes | Lambda (with partial batch response) | CDC, audit, materialized views |
| 6 | **Schedule → Lambda** | Scheduler → target bus | Lambda (or any SDK target) | Cron jobs, batch kickoff, "every 5 minutes" ETL |
| 7 | **Cross-account bus fan-out** | Account A bus → Account B bus | Lambda / SQS in account B | Centralized event ingestion across an org |
| 8 | **SaaS partner → Lambda** | Partner bus (Auth0, Datadog, Zendesk, …) | Lambda | Third-party webhook ingestion without a public API |
| 9 | **CodePipeline state change → SNS** | CW → default bus | SNS | CI/CD notifications, deployment audits |
| 10 | **DLQ depth alarm → Lambda** | CW metric on SQS → default bus | Lambda (re-drive or page) | Self-healing, alerting on the alert system |

L31–L35 cover patterns 1, 2, 3, the DLQ pattern, and 7 in detail.

## Lecture-to-file map

| L# | Title | Min | File |
|---|---|---|---|
| L30 | The 10 Most Common EventBridge Patterns | 9:30 | `lecture_scripts/L30_patterns_intro.md` |
| L31 | S3 → EventBridge → Lambda | 11:15 | `lecture_scripts/L31_s3_lambda.md` |
| L32 | CloudWatch Alarm → EventBridge → SNS (with SSM Runbook) | 10:45 | `lecture_scripts/L32_cw_alarm_sns.md` |
| L33 | API Gateway → EventBridge → Step Functions | 10:20 | `lecture_scripts/L33_api_gateway_stepfn.md` |
| L34 | Dead-Letter Queue Patterns | 12:00 | `lecture_scripts/L34_dlq_patterns.md` |
| L35 | Cross-Account + Cross-Region Fan-Out | 11:30 | `lecture_scripts/L35_cross_account.md` |
| L36 | Course Wrap-Up + What to Read Next | 8:45 | `lecture_scripts/L36_course_wrapup.md` |

## Where this section fits

Sections 2–6 were mechanical: you learned what each EventBridge
piece is and how to operate it. Section 7 is **architectural**: you
are now combining the pieces into the topologies that real AWS
accounts ship. The diagram in L30 — `Source → Bus → Rule → Targets
(+ DLQ)` — is the spine that every pattern in the section shares.

The 5 working boto3 + moto code demos from sections 2–6
(`create_event_bus.py`, `put_rule.py`, `put_targets.py`,
`schedule_cron.py`, `archive_replay.py`) all stay relevant. When
L31 talks about the S3 event pattern, the same `events.put_rule`
call from section 3 is the one you would use in your own account;
only the pattern and the target ARN change.

## Working artifacts

This section has **no new code demo** by design. The lectures
themselves are the artifact. The patterns include inline JSON
event patterns, IAM policies, Lambda handler sketches, and CDK
construct references that you can copy into your own codebase.

| # | Artifact | Where | Lecture |
|---|---|---|---|
| 1 | Section overview + 10-pattern table | this file | L30 |
| 2 | S3 event pattern (JSON) | L31 lecture | L31 |
| 3 | CW alarm event pattern (JSON) | L32 lecture | L32 |
| 4 | API Gateway → EventBridge request template | L33 lecture | L33 |
| 5 | DLQ topology diagrams (3 patterns) | L34 lecture | L34 |
| 6 | Cross-account bus resource policy | L35 lecture | L35 |
| 7 | Quiz | `quizzes/section_7.md` | L30–L36 |

## Prerequisites

- Sections 1–6 completed (you are comfortable with event buses,
  rules, patterns, targets, scheduler, pipes, and archives).
- Familiarity with at least one of: S3 event notifications, CW
  alarms, API Gateway integrations, Step Functions state machines.
  The patterns use these services as the source or target, and
  the lectures assume you have used them at least conceptually.
- An AWS account if you want to wire any of these patterns
  hands-on. The lectures themselves do not require one.

## Course wrap-up (L36)

L36 closes the course with:

- A **section-by-section recap** of what you built.
- A **"what to read next"** list (EventBridge FAQs, AWS What's
  New, CDK v2 `events` module, Schema Registry, Well-Architected
  EDA lens, ServerlessLand workshop, SAA-C03 / SAP-C02 study
  guides).
- A **"what to do in your own account"** three-step list (stand
  up the S3 → Lambda pattern, add an org-wide bus + archive,
  wire a real CW alarm → SNS + SSM runbook).
- A **personal note** on the patterns vs the features, and a
  thank-you from the author.

Welcome to the next pattern you build.
