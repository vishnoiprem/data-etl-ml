# DIRECTORY — aws_cloudwatch_course

> Full file index for the course. See `SYLLABUS.md` for the lecture-to-file
> map. **All paths are relative to this file.**

## Top-level

| Path | Purpose |
|---|---|
| `README.md` | Course overview |
| `SYLLABUS.md` | L01–L35 ↔ file map |
| `DIRECTORY.md` | this file |
| `CHANGELOG.md` | changelog |
| `requirements.txt` | Python dependencies (root) |
| `diagrams/` | 3 Mermaid diagrams |
| `downloads/` | PDF/zip student resources |
| `quizzes/` | 7 quiz files (one per section) |
| `scripts/` | `run_all_tests.py`, `bootstrap.sh` |
| `assignments/` | 1 graded task (SLO dashboard) |

## Sections

| # | Folder | L-IDs | Lectures |
|---|---|---|---|
| 1 | `01_foundations/` | L01–L04 | 4 |
| 2 | `02_metrics/` | L05–L09 | 5 |
| 3 | `03_logs/` | L10–L14 | 5 |
| 4 | `04_alarms/` | L15–L19 | 5 |
| 5 | `05_dashboards/` | L20–L24 | 5 |
| 6 | `06_logs_insights_subs/` | L25–L29 | 5 |
| 7 | `07_real_world/` | L30–L35 | 6 |
| | **Total** | | **35** |

## Per-section layout

Every section folder has the same shape:

```
<NN_topic>/
├── README.md              ← short summary of the section
├── lecture_scripts/       ← L##_topic.md (one per lecture)
│   ├── L01_…
│   ├── L02_…
│   └── …
└── code/                  ← runnable boto3 + moto code samples
    ├── <demo_1>/
    │   ├── README.md
    │   ├── script.py
    │   └── test_script.py
    └── …
```

## Quizzes (7)

| # | File | Questions |
|---|---|---|
| 1 | `quizzes/section_1.md` | 10 |
| 2 | `quizzes/section_2.md` | 10 |
| 3 | `quizzes/section_3.md` | 10 |
| 4 | `quizzes/section_4.md` | 10 |
| 5 | `quizzes/section_5.md` | 9 |
| 6 | `quizzes/section_6.md` | 9 |
| 7 | `quizzes/section_7.md` | 8 |

## Diagrams

```
diagrams/
├── cloudwatch_anatomy.mmd
├── alarm_state_machine.mmd
└── subscription_filter_flow.mmd
```

## Downloads

| File | Purpose |
|---|---|
| `downloads/cloudwatch_cheat_sheet.md` | All CW limits, namespaces, alarms at a glance |
| `downloads/cloudwatch_logs_insights_cheat_sheet.md` | Logs Insights query language reference |
| `downloads/cloudwatch_widget_json_cheat_sheet.md` | Widget JSON reference for dashboards |
| `downloads/README.md` | Index / placeholders for the three PDF placeholders |

## Assignments (1)

| # | File |
|---|---|
| 1 | `assignments/assignment_1_slo_dashboard.md` |
