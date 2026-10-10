# DIRECTORY — Full file index

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;

## Top level

- `README.md` — course overview, what you build, quick start
- `SYLLABUS.md` — authoritative L-ID ↔ file map
- `DIRECTORY.md` — this file
- `CHANGELOG.md` — v1.0 release notes
- `requirements.txt` — boto3 + moto[events] + pytest

## Sections (7)

| Folder | Title | Lectures | Code |
|---|---|---|---|
| `01_foundations/` | Foundations | L01–L04 | – |
| `02_eventbus_basics/` | EventBus basics | L05–L09 | `create_event_bus.py` |
| `03_rules/` | Rules + patterns | L10–L15 | `put_rule.py` |
| `04_targets/` | Targets | L16–L20 | `put_targets.py` |
| `05_schedules/` | Scheduler | L21–L24 | `schedule_cron.py` |
| `06_pipes_archives_replay/` | Pipes + Archives + Replay | L25–L29 | `archive_replay.py` |
| `07_patterns_real_world/` | Patterns + Real-World | L30–L36 | – |

## Quizzes

- `quizzes/section_1.md` (8 questions)
- `quizzes/section_2.md` (10 questions)
- `quizzes/section_3.md` (12 questions)
- `quizzes/section_4.md` (10 questions)
- `quizzes/section_5.md` (10 questions)
- `quizzes/section_6.md` (10 questions)
- `quizzes/section_7.md` (10 questions, final)

## Diagrams

- `diagrams/eventbus_anatomy.mmd`
- `diagrams/rule_pattern_flow.mmd`
- `diagrams/scheduler_cron.mmd`
- `diagrams/pipes_pipeline.mmd`

## Scripts

- `scripts/run_all_tests.py` — runs every `test_*.py`
- `scripts/bootstrap.sh` — venv + pip + test run

## Assignments and downloads

- `assignments/assignment_1_eventbridge_dr_ha.md` — optional extension exercise
- `downloads/slides.pdf` — placeholder
