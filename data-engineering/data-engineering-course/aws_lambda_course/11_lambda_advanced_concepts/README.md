# Section 11 — AWS Lambda Advanced Concepts

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Lectures:** L47–L59
> **Duration:** ~60 minutes
> **Hands-on artifacts:** VPC-deployed Lambda, CloudWatch dashboard, CloudWatch Insights query, Version+Alias demo

## What this section covers

The previous sections treated Lambda as a black box that you write code
into. Section 11 opens the box. You will learn the operational
properties that distinguish a toy Lambda from a production-grade one —
how it scales, what slows it down, how to pin memory/CPU, how to put it
inside a VPC, how to observe it, and how to ship it without breaking
the live version.

## Lecture map

| L# | Title | Min | File |
|---|---|---|---|
| L47 | Section Overview | 0:29 | `lecture_scripts/L47_section_overview.md` |
| L48 | Lambda Execution and Concurrency | 8:24 | `lecture_scripts/L48_concurrency.md` |
| L49 | Lambda — Reserved and Provisioned Concurrency | 5:32 | `lecture_scripts/L49_reserved_provisioned_concurrency.md` |
| L50 | Lambda Limits — Memory | 4:22 | `lecture_scripts/L50_memory_limits.md` |
| L51 | Lambda — VPC Networking Configuration | 5:44 | `lecture_scripts/L51_vpc_networking.md` |
| L52 | Lambda — VPC Networking Configuration Hands On | 5:34 | `lecture_scripts/L52_vpc_networking_hands_on.md` |
| L53 | Lambda Monitoring — CloudWatch Metrics | 5:55 | `lecture_scripts/L53_cw_metrics.md` |
| L54 | Lambda Monitoring — CloudWatch Metrics — Hands On | 6:17 | `lecture_scripts/L54_cw_metrics_hands_on.md` |
| L55 | Lambda Monitoring — CloudWatch Logs | 2:17 | `lecture_scripts/L55_cw_logs.md` |
| L56 | Lambda Monitoring — CloudWatch Logs — Hands On | 5:27 | `lecture_scripts/L56_cw_logs_hands_on.md` |
| L57 | Lambda Versions | 5:44 | `lecture_scripts/L57_versions.md` |
| L58 | Lambda Aliases | 5:25 | `lecture_scripts/L58_aliases.md` |
| L59 | Lambda — Environment Variables | 4:42 | `lecture_scripts/L59_env_vars.md` |

## What you build

| # | Working artifact | Lecture |
|---|---|---|
| 1 | Lambda deployed into a VPC with a custom SG (talks to a private RDS) | L51, L52 |
| 2 | CloudWatch dashboard with Lambda invocations/errors/throttles | L53, L54 |
| 3 | CloudWatch Logs Insights query against `/aws/lambda/*` log groups | L55, L56 |
| 4 | Versioned Lambda + weighted alias routing 90/10 | L57, L58 |
| 5 | Lambda with Secrets Manager + SSM Parameter Store env vars | L59 |

## Prerequisites

- Sections 2 and 5 (Lambda basics, invocation model, timeout).
- Comfortable with boto3 from section 4.
- An AWS account with permissions to create Lambda, IAM, VPC, RDS,
  CloudWatch, and Secrets Manager resources.

## How to use this section

1. Read `L47` for the orientation map.
2. Watch L48–L50 in order — they build a mental model of *how Lambda
   runs your code*.
3. L51–L52 are a tight pair: theory + hands-on for VPC.
4. L53–L56 are a tight pair: theory + hands-on for CloudWatch.
5. L57–L58 are a tight pair: theory + hands-on for safe deployments.
6. L59 closes with secrets handling.

Every `code/` subfolder has a `README.md` walking you through running
it end-to-end against your own AWS account.
