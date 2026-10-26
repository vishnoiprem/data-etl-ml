# SYLLABUS — AWS EventBridge Crash Course

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Format:** 7 sections, 36 lectures, 5 working boto3 + moto code
> demos, 4 mermaid diagrams, 7 quizzes, 1 download.

This is the **authoritative lecture-to-file map**. The lecture order is
preserved exactly as L01–L36 below. Section folders are numbered to
match the course's 7 logical sections.

| Section | Lectures | Title | Working artifact |
|---|---|---|---|
| 1 | L01–L04 | Foundations (event-driven architecture) | – |
| 2 | L05–L09 | EventBus basics (default, custom, partner, policy) | `create_event_bus.py` + tests |
| 3 | L10–L15 | Rules + event patterns | `put_rule.py` + tests |
| 4 | L16–L20 | Targets (Lambda, SQS, SNS, Step Functions, …) | `put_targets.py` + tests |
| 5 | L21–L24 | EventBridge Scheduler (cron + rate) | `schedule_cron.py` + tests |
| 6 | L25–L29 | Pipes + Archives + Replay | `archive_replay.py` + tests |
| 7 | L30–L36 | Patterns + Real-World (DLQ, retry, cross-account) | – |

**Total: 36 lectures, 7 quizzes, 5 working code samples + tests.**

---

## Section 1 — Foundations (L01–L04)

| L# | Title | File |
|---|---|---|
| L01 | Course Overview | `01_foundations/lecture_scripts/L01_course_overview.md` |
| L02 | What is Event-Driven Architecture? | `01_foundations/lecture_scripts/L02_event_driven.md` |
| L03 | The Pub/Sub Pattern (and how it differs from a queue) | `01_foundations/lecture_scripts/L03_pubsub.md` |
| L04 | Why EventBridge? (and where CloudWatch Events fits) | `01_foundations/lecture_scripts/L04_why_eventbridge.md` |

## Section 2 — EventBus Basics (L05–L09)

| L# | Title | File |
|---|---|---|
| L05 | What is an Event Bus? | `02_eventbus_basics/lecture_scripts/L05_event_bus.md` |
| L06 | The Default Event Bus | `02_eventbus_basics/lecture_scripts/L06_default_bus.md` |
| L07 | Custom Event Buses | `02_eventbus_basics/lecture_scripts/L07_custom_bus.md` |
| L08 | Partner Event Bus (SaaS events) | `02_eventbus_basics/lecture_scripts/L08_partner_bus.md` |
| L09 | Section Recap + `create_event_bus.py` + tests | `02_eventbus_basics/lecture_scripts/L09_section_recap.md` |

## Section 3 — Rules + Event Patterns (L10–L15)

| L# | Title | File |
|---|---|---|
| L10 | Rules 101 | `03_rules/lecture_scripts/L10_rules_101.md` |
| L11 | Event Pattern Matching (the JSON predicate) | `03_rules/lecture_scripts/L11_pattern_matching.md` |
| L12 | Content Filtering ($.detail, $.detail-type) | `03_rules/lecture_scripts/L12_content_filtering.md` |
| L13 | Prefix Matching + Wildcards + Arrays | `03_rules/lecture_scripts/L13_prefix_wildcards.md` |
| L14 | Cross-Account + Cross-Region Event Patterns | `03_rules/lecture_scripts/L14_cross_account.md` |
| L15 | Section Recap + `put_rule.py` + tests | `03_rules/lecture_scripts/L15_section_recap.md` |

## Section 4 — Targets (L16–L20)

| L# | Title | File |
|---|---|---|
| L16 | Targets 101 (the 15+ supported AWS targets) | `04_targets/lecture_scripts/L16_targets_101.md` |
| L17 | Lambda Targets + Async Invocation | `04_targets/lecture_scripts/L17_lambda_targets.md` |
| L18 | SQS + SNS Targets (queue + pub/sub fanout) | `04_targets/lecture_scripts/L18_sqs_sns.md` |
| L19 | Dead-Letter Queues + Retry Policies | `04_targets/lecture_scripts/L19_dlq_retry.md` |
| L20 | Section Recap + `put_targets.py` + tests | `04_targets/lecture_scripts/L20_section_recap.md` |

## Section 5 — EventBridge Scheduler (L21–L24)

| L# | Title | File |
|---|---|---|
| L21 | Scheduler 101 (the replacement for CW Events schedule) | `05_schedules/lecture_scripts/L21_scheduler_101.md` |
| L22 | Cron + Rate Expressions | `05_schedules/lecture_scripts/L22_cron_rate.md` |
| L23 | One-Off Schedules + Time Zones | `05_schedules/lecture_scripts/L23_oneoff_timezone.md` |
| L24 | Section Recap + `schedule_cron.py` + tests | `05_schedules/lecture_scripts/L24_section_recap.md` |

## Section 6 — Pipes + Archives + Replay (L25–L29)

| L# | Title | File |
|---|---|---|
| L25 | Pipes 101 (source → filter → enrich → target) | `06_pipes_archives_replay/lecture_scripts/L25_pipes_101.md` |
| L26 | Partial Batch Response (failure isolation) | `06_pipes_archives_replay/lecture_scripts/L26_partial_batch.md` |
| L27 | Archives (the event backup) | `06_pipes_archives_replay/lecture_scripts/L27_archives.md` |
| L28 | Replay (the killer feature) | `06_pipes_archives_replay/lecture_scripts/L28_replay.md` |
| L29 | Section Recap + `archive_replay.py` + tests | `06_pipes_archives_replay/lecture_scripts/L29_section_recap.md` |

## Section 7 — Patterns + Real-World (L30–L36)

| L# | Title | File |
|---|---|---|
| L30 | Schema Registry + Code Bindings | `07_patterns_real_world/lecture_scripts/L30_schema_registry.md` |
| L31 | Resource-Based Policies + Cross-Account Bus | `07_patterns_real_world/lecture_scripts/L31_resource_policies.md` |
| L32 | EventBridge + Step Functions (the workflow duo) | `07_patterns_real_world/lecture_scripts/L32_step_functions.md` |
| L33 | EventBridge + S3 (object-level events) | `07_patterns_real_world/lecture_scripts/L33_s3_events.md` |
| L34 | EventBridge + DynamoDB Streams | `07_patterns_real_world/lecture_scripts/L34_dynamodb_streams.md` |
| L35 | Cost Model + Limits (the 2026 numbers) | `07_patterns_real_world/lecture_scripts/L35_cost_limits.md` |
| L36 | Course Wrap-Up + Final Quiz | `07_patterns_real_world/lecture_scripts/L36_course_wrapup.md` |
