# AWS EventBridge Crash Course

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Format:** 7 sections, 36 lectures, 5 working boto3 + moto code
> demos, 4 mermaid diagrams, 7 quizzes, 1 download.

This is a **beginner-friendly, hands-on** AWS course. Every concept is
backed by either a boto3 script you can read end-to-end or a
`pytest`-runnable demo that uses `moto` to mock AWS — so you can learn
EventBridge without spending a cent on AWS.

## What you will learn

- The mental model: **event bus**, **event**, **rule**, **target**,
  **archive**, **replay**, **pipe**, **scheduler**.
- How to use the **default event bus** and create **custom** +
  **partner** event buses.
- How to write **event patterns** (the JSON predicates that decide
  which events match a rule).
- How to wire **targets**: Lambda, SQS, SNS, Step Functions, ECS
  tasks, Kinesis Streams, API Gateway, EventBridge bus-to-bus, etc.
- How to use **EventBridge Scheduler** for cron + rate expressions
  (the replacement for the deprecated CloudWatch Events schedule API).
- How to use **EventBridge Pipes** to filter + enrich + transform
  between a source (SQS/Kinesis/DynamoDB) and a target, with **partial
  batch response** for failure isolation.
- How to **archive** events and **replay** them — the killer feature
  for retroactive debugging and backfills.
- The 2026 best-practice patterns: dead-letter queues, retry policies,
  cross-account event buses, schema registry, resource-based policies.

## What you build

| # | Section | What runs | Lectures |
|---|---|---|---|
| 1 | Foundations (event-driven architecture) | – | L01–L04 |
| 2 | EventBus basics (default, custom, partner, policy) | `create_event_bus.py` + tests | L05–L09 |
| 3 | Rules + event patterns | `put_rule.py` + tests | L10–L15 |
| 4 | Targets (Lambda, SQS, SNS, Step Functions, …) | `put_targets.py` + tests | L16–L20 |
| 5 | EventBridge Scheduler (cron + rate) | `schedule_cron.py` + tests | L21–L24 |
| 6 | Pipes + Archives + Replay | `archive_replay.py` + tests | L25–L29 |
| 7 | Patterns + Real-World (DLQ, retry, cross-account) | – | L30–L36 |

## Quick start (no AWS account needed)

```bash
cd data-engineering-course/aws_eventbridge_course
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run every test in the course
python scripts/run_all_tests.py
```

Expected: **~30 tests pass** in under 5 seconds, no AWS calls.

## Layout

```
aws_eventbridge_course/
├── README.md                       ← you are here
├── SYLLABUS.md                     ← authoritative L-ID ↔ file map
├── DIRECTORY.md                    ← full file index
├── CHANGELOG.md                    ← v1.0
├── requirements.txt                ← boto3 + moto[events] + pytest
├── 01_foundations/                 ← 4 lectures, no code
├── 02_eventbus_basics/             ← 5 lectures + create_event_bus
├── 03_rules/                       ← 6 lectures + put_rule
├── 04_targets/                     ← 5 lectures + put_targets
├── 05_schedules/                   ← 4 lectures + schedule_cron
├── 06_pipes_archives_replay/       ← 5 lectures + archive_replay
├── 07_patterns_real_world/         ← 7 lectures, no code (best practices)
├── quizzes/                        ← one per section
├── diagrams/                       ← 4 mermaid files
├── assignments/                    ← 1 optional exercise
├── downloads/                      ← PDF slide placeholder
└── scripts/
    ├── run_all_tests.py
    └── bootstrap.sh
```

## Next steps

1. Read `SYLLABUS.md` to find every lecture.
2. Open `01_foundations/lecture_scripts/L01_course_overview.md`.
3. Work through the sections in order — each one builds on the previous.
4. Run the section's `code/` tests after reading the lecture.
5. Take the section quiz in `quizzes/section_N.md` before moving on.
