# SYLLABUS — AWS CloudWatch Crash Course — Beginner to Advanced

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Format:** **7 sections**, **35 lectures** (L01–L35), **~6h** total. 5 working `boto3 + moto` demos, 7 quizzes, 1 graded assignment, 3 Mermaid diagrams.
> **Source:** Udemy-published curriculum "AWS CloudWatch Crash Course" (October 2026 edition).

This is the **authoritative lecture-to-file map**. The Udemy lecture order
is preserved exactly as L01–L35 below.

| Section | Lectures | Min | Title |
|---|---|---|---|
| 1 | L01–L04 | 30 | Foundations — What is Observability, Metrics, Logs, Traces |
| 2 | L05–L09 | 60 | CloudWatch Metrics — Namespaces, Dimensions, Resolution, Statistics |
| 3 | L10–L14 | 60 | CloudWatch Logs — Groups, Streams, Retention, Insights |
| 4 | L15–L19 | 55 | CloudWatch Alarms — Metric, Composite, Anomaly Detection |
| 5 | L20–L24 | 55 | CloudWatch Dashboards — Widgets, Text, Logs Insights |
| 6 | L25–L29 | 60 | Logs Insights + Subscriptions + Kinesis / Firehose |
| 7 | L30–L35 | 50 | Real-World Patterns — SLO/SLI, Cost Optimization, Alarms at Scale |

**Total: 35 lectures, ~6h 10m, 5 working demos, 7 quizzes, 1 assignment.**

---

## Section 1 — Foundations (L01–L04, ~30 min)

| L# | Title | Min | File |
|---|---|---|---|
| L01 | Course Introduction & What You'll Build | 5:00 | `01_foundations/lecture_scripts/L01_course_intro.md` |
| L02 | The Three Pillars of Observability (Metrics / Logs / Traces) | 12:00 | `01_foundations/lecture_scripts/L02_three_pillars.md` |
| L03 | CloudWatch Service Overview, Pricing & Free Tier | 8:00 | `01_foundations/lecture_scripts/L03_cw_overview_pricing.md` |
| L04 | Console Tour — Metrics, Logs, Alarms, Dashboards | 5:00 | `01_foundations/lecture_scripts/L04_console_tour.md` |

---

## Section 2 — CloudWatch Metrics (L05–L09, ~60 min)

| L# | Title | Min | File |
|---|---|---|---|
| L05 | Metrics 101 — Namespaces, Metric Names, Dimensions | 10:00 | `02_metrics/lecture_scripts/L05_metrics_101.md` |
| L06 | Standard vs. High-Resolution Metrics, Storage Resolution | 12:00 | `02_metrics/lecture_scripts/L06_resolution.md` |
| L07 | Statistics: Average, Sum, Min, Max, p99, Percentile | 10:00 | `02_metrics/lecture_scripts/L07_statistics.md` |
| L08 | `put_metric_data` + `get_metric_data` with boto3 | 18:00 | `02_metrics/lecture_scripts/L08_put_metric_data.md` |
| L09 | Hands-on: build `put_metric_data.py` + 5 moto tests | 10:00 | `02_metrics/lecture_scripts/L09_hands_on.md` |

---

## Section 3 — CloudWatch Logs (L10–L14, ~60 min)

| L# | Title | Min | File |
|---|---|---|---|
| L10 | Logs 101 — Log Groups, Log Streams, Retention | 12:00 | `03_logs/lecture_scripts/L10_logs_101.md` |
| L11 | Log Events, Timestamps, Ingestion, Storage Costs | 12:00 | `03_logs/lecture_scripts/L11_log_events.md` |
| L12 | `create_log_group` + `put_log_events` + `filter_log_events` | 18:00 | `03_logs/lecture_scripts/L12_boto3_logs.md` |
| L13 | CloudWatch Logs Insights — query language primer | 10:00 | `03_logs/lecture_scripts/L13_insights.md` |
| L14 | Hands-on: build `create_log_group.py` + 5 moto tests | 8:00 | `03_logs/lecture_scripts/L14_hands_on.md` |

---

## Section 4 — CloudWatch Alarms (L15–L19, ~55 min)

| L# | Title | Min | File |
|---|---|---|---|
| L15 | Metric Alarms 101 — OK / ALARM / INSUFFICIENT_DATA | 10:00 | `04_alarms/lecture_scripts/L15_metric_alarms_101.md` |
| L16 | Threshold types, Period, Evaluation Periods, Datapoints-to-Alarm | 12:00 | `04_alarms/lecture_scripts/L16_threshold_period.md` |
| L17 | SNS as Alarm Action — wiring the on-call pager | 10:00 | `04_alarms/lecture_scripts/L17_sns_actions.md` |
| L18 | Composite Alarms & Anomaly Detection Alarms | 13:00 | `04_alarms/lecture_scripts/L18_composite_anomaly.md` |
| L19 | Hands-on: build `put_metric_alarm.py` + 5 moto tests | 10:00 | `04_alarms/lecture_scripts/L19_hands_on.md` |

---

## Section 5 — CloudWatch Dashboards (L20–L24, ~55 min)

| L# | Title | Min | File |
|---|---|---|---|
| L20 | Dashboards 101 — Body JSON, Widget Coordinate System | 10:00 | `05_dashboards/lecture_scripts/L20_dashboards_101.md` |
| L21 | Widget Types — Metric, Logs Table, Logs Insights, Text, Stacked | 13:00 | `05_dashboards/lecture_scripts/L21_widget_types.md` |
| L22 | Cross-Region / Cross-Account Dashboards | 10:00 | `05_dashboards/lecture_scripts/L22_cross_region_account.md` |
| L23 | `put_dashboard` + `get_dashboard` with boto3 | 12:00 | `05_dashboards/lecture_scripts/L23_boto3_dashboards.md` |
| L24 | Hands-on: build `create_dashboard.py` + 4 moto tests | 10:00 | `05_dashboards/lecture_scripts/L24_hands_on.md` |

---

## Section 6 — Logs Insights + Subscriptions + Kinesis / Firehose (L25–L29, ~60 min)

| L# | Title | Min | File |
|---|---|---|---|
| L25 | Subscription Filters 101 — Real-Time Log Fan-out | 12:00 | `06_logs_insights_subs/lecture_scripts/L25_subscription_filters.md` |
| L26 | Filter Pattern Syntax — exact, json, space-delimited tokens | 10:00 | `06_logs_insights_subs/lecture_scripts/L26_filter_patterns.md` |
| L27 | Kinesis Data Streams + Firehose as Destinations | 12:00 | `06_logs_insights_subs/lecture_scripts/L27_kinesis_firehose.md` |
| L28 | Lambda as Subscription Destination (the canonical pattern) | 12:00 | `06_logs_insights_subs/lecture_scripts/L28_lambda_destination.md` |
| L29 | Hands-on: build `subscription_filter.py` + 4 moto tests | 14:00 | `06_logs_insights_subs/lecture_scripts/L29_hands_on.md` |

---

## Section 7 — Real-World Patterns (L30–L35, ~50 min)

| L# | Title | Min | File |
|---|---|---|---|
| L30 | SLO / SLI fundamentals & error-budget burn-rate alerts | 12:00 | `07_real_world/lecture_scripts/L30_slo_sli.md` |
| L31 | Cost Optimization — log retention, metric filters, anomaly bands | 10:00 | `07_real_world/lecture_scripts/L31_cost_optimization.md` |
| L32 | Alarms at Scale — naming conventions, tag strategy, multi-account | 10:00 | `07_real_world/lecture_scripts/L32_alarms_at_scale.md` |
| L33 | Observability for Serverless (Lambda + API Gateway + DynamoDB) | 8:00 | `07_real_world/lecture_scripts/L33_serverless_observability.md` |
| L34 | Observability for Containers (ECS / EKS) | 5:00 | `07_real_world/lecture_scripts/L34_container_observability.md` |
| L35 | Course Wrap-up & Where to Go Next | 5:00 | `07_real_world/lecture_scripts/L35_wrapup.md` |

---

## Quizzes (7 — one per section)

| # | Section | File |
|---|---|---|
| 1 | Foundations | `quizzes/section_1.md` |
| 2 | Metrics | `quizzes/section_2.md` |
| 3 | Logs | `quizzes/section_3.md` |
| 4 | Alarms | `quizzes/section_4.md` |
| 5 | Dashboards | `quizzes/section_5.md` |
| 6 | Logs Insights + Subs | `quizzes/section_6.md` |
| 7 | Real-World Patterns | `quizzes/section_7.md` |

---

## Diagrams (3)

| File | Purpose |
|---|---|
| `diagrams/cloudwatch_anatomy.mmd` | Tree: CloudWatch → Metrics / Logs / Alarms / Dashboards / Events / Insights / Synthetics / RUM |
| `diagrams/alarm_state_machine.mmd` | State diagram: OK ↔ ALARM ↔ INSUFFICIENT_DATA with transitions |
| `diagrams/subscription_filter_flow.mmd` | Sequence: App → Logs (filter) → Kinesis → Lambda consumer |

---

## Downloads (3)

| # | File |
|---|---|
| 1 | `downloads/cloudwatch_cheat_sheet.pdf` (placeholder) |
| 2 | `downloads/cloudwatch_logs_insights_cheat_sheet.pdf` (placeholder) |
| 3 | `downloads/cloudwatch_widget_json_cheat_sheet.pdf` (placeholder) |

---

## Working demos (5)

| # | Section | File |
|---|---|---|
| 1 | 2 | `02_metrics/code/put_metric_data.py` (+ 5 moto tests) |
| 2 | 3 | `03_logs/code/create_log_group.py` (+ 5 moto tests) |
| 3 | 4 | `04_alarms/code/put_metric_alarm.py` (+ 5 moto tests) |
| 4 | 5 | `05_dashboards/code/create_dashboard.py` (+ 4 moto tests) |
| 5 | 6 | `06_logs_insights_subs/code/subscription_filter.py` (+ 4 moto tests) |
