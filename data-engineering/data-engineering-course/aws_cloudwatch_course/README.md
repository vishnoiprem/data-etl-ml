# AWS CloudWatch Crash Course — Beginner to Advanced

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Format:** **7 sections, 35 lectures (L01–L35), ~6h total** — Udemy-published 2026 edition.
> **Companion repo:** Local companion to the published AWS CloudWatch Crash Course.

This is the local companion repo for the **AWS CloudWatch Crash Course**.
The lecture-to-file map in `SYLLABUS.md` is authoritative.

## What you'll learn

- Understand the **three pillars of observability** — metrics, logs, and
  traces — and how CloudWatch covers the first two (and integrates with
  X-Ray for the third).
- Publish and query **CloudWatch Metrics** (custom namespaces, dimensions,
  resolution, statistics) using `boto3` and the AWS console.
- Use **CloudWatch Logs** for log groups, streams, retention policies, and
  ad-hoc **Logs Insights** queries.
- Author and tune **metric alarms** (threshold, anomaly detection,
  composite) and route them via **SNS** to operators.
- Build **CloudWatch Dashboards** with metric, log, text, and Logs Insights
  widgets.
- Stream logs in real time with **subscription filters** to Kinesis /
  Firehose / Lambda.
- Apply **SLO/SLI** monitoring, **cost optimization**, and **alarms at
  scale** patterns (L30–L35).

## What you build

| # | Working artifact | Section | L-IDs |
|---|---|---|---|
| 1 | `put_metric_data.py` — custom namespace, dimensions, get statistics | 2 | L05–L09 |
| 2 | `create_log_group.py` — group, stream, events, time-filtered read | 3 | L10–L14 |
| 3 | `put_metric_alarm.py` — CPU alarm + SNS action + describe | 4 | L15–L19 |
| 4 | `create_dashboard.py` — 3-widget dashboard (metric + insights + text) | 5 | L20–L24 |
| 5 | `subscription_filter.py` — log group → Kinesis stream filter | 6 | L25–L29 |

## Repo layout

```
aws_cloudwatch_course/
├── README.md                       ← you are here
├── SYLLABUS.md                     ← authoritative L-ID ↔ file map
├── DIRECTORY.md                    ← every file in the course
├── CHANGELOG.md
├── 01_foundations/                 ← L01–L04
├── 02_metrics/                     ← L05–L09
├── 03_logs/                        ← L10–L14
├── 04_alarms/                      ← L15–L19
├── 05_dashboards/                  ← L20–L24
├── 06_logs_insights_subs/          ← L25–L29
├── 07_real_world/                  ← L30–L35
├── diagrams/                       ← 3 mermaid diagrams
├── downloads/                      ← PDF/zip resources
├── quizzes/                        ← 7 quiz files (one per section)
├── scripts/                        ← run_all_tests.py, bootstrap.sh
└── assignments/                    ← SLO dashboard assignment
```

Each section follows the **lecture_scripts/** + **code/** + **assignments/**
convention established in `../aws_lambda_course/`. Every lecture is a
standalone `.md` you can read top-to-bottom; every `code/` folder is
runnable end-to-end with `moto`.

## Prerequisites

- AWS account (free tier is enough for all sections)
- Python 3.11+ (we use `boto3` 1.34+ and `moto` 5+)
- AWS CLI v2
- No prior CloudWatch experience required

```bash
git clone <this-repo>
cd aws_cloudwatch_course
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
aws configure
```

## How to use this repo

- **Linear read:** start at `01_foundations/lecture_scripts/L01_course_intro.md`.
- **Reference:** every lecture file has a **Prereqs**, **Key terms**,
  **Lecture**, **Hands-on** and **Quiz** section.
- **Hands-on:** all code lives under `<section>/code/`. Each subdir has a
  `README.md` that walks you through running it.
- **Quizzes:** `quizzes/section_N.md` — 8–12 questions, hidden answers in
  a collapsible block.
- **Assignment:** `assignments/assignment_1_slo_dashboard.md` — extended
  SLO dashboard + burn-rate alerts task.

## AWS Services used in the course

CloudWatch Metrics, CloudWatch Logs, CloudWatch Alarms, CloudWatch
Dashboards, CloudWatch Logs Insights, CloudWatch Anomaly Detection,
CloudWatch Composite Alarms, CloudWatch Subscription Filters, SNS,
Kinesis Data Streams, Kinesis Data Firehose, IAM, EventBridge (briefly),
boto3, moto.

## License & attribution

Course material authored by **Prem Vishnoi &lt;prem.vishnoi@example.com&gt;**.
Code samples are MIT-licensed. See `../../LICENSE` for the full text.
