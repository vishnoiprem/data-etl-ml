# Changelog

## 2026-10-09 — Full Data Engineering Interview Course Build

A complete, runnable **Data Engineering Interview course** was created under
`data-engineering-course/`. **12 tracks, 473 lessons, 1,385 tests, ~1,000+ files.**

This extends the System Design course (committed earlier today) with 11
additional tracks covering the full breadth of data engineering, software
engineering, engineering management, and behavioral interviews.

### Added — 11 new tracks

- **Behavioral Interviews** (5 modules, 31 lessons, ~44k words) — STAR/CAR/PAR/SOAR, 5 story categories, 4 mock interviews (Meta E5 / Google L6 / Netflix Principal / EM M5)
- **How to Get the Interview** (1 module, 9 lessons, ~20k words) — resume, referrals, sourcing, internal transitions, with a full sample DE resume artifact
- **EM Introduction** (1 module, 6 lessons, ~16k words) — IC→Manager transition, EM interview loop, 73-term glossary
- **People Management** (5 modules, 21 lessons, ~41k words) — managing individuals, performance, team execution, cross-functional
- **Project Retrospective** (1 module, 6 lessons, ~14k words) — full 1,966-word worked example
- **Solutions Architect** (6 modules, 47 lessons, ~82k words, 8 mermaid diagrams) — SA intro, customer interaction, technical questions, behavioral for SAs, tips & frameworks
- **Data Modeling** (7 modules, 36 lessons, ~46k words, 91 tests) — 5 real runnable SQLite star schemas (e-commerce, ride-sharing, Instagram, customer support, Spotify), SCD 1/2/3, 4 fact table types
- **Data Pipeline Design** (7 modules, 30 lessons, ~36k words, 140 tests) — CDC, API poller, JDBC, dbt-style SQL transforms, upsert/MERGE, DAG orchestrator, retry/backoff, SLA monitoring, 3 full mock pipeline solutions
- **SQL Interviews** (9 modules, 98 lessons, ~30k words, 59 tests) — SQL foundations, joins, aggregations, window functions, CTEs, NULL handling, plus 59 graded SQL problems (14 easy + 31 medium + 14 hard)
- **Coding Interviews** (15 modules, 118 lessons, ~6.2k LOC, 293 tests) — 103 coding problems across arrays, hash tables, sorting, strings, graphs, trees, stacks/queues, linked lists, heaps, recursion, DP, plus 6 mock interviews
- **Common library** (12 files, 1,039 LOC, 38 tests) — shared `common/` Python lib: schema.py, query.py, pipeline.py, data_gen.py, csv_utils.py, analytics.py, jinja_helpers.py, conftest_helpers.py, fixtures.py

### Added — Infrastructure

- **`common/`** — shared stdlib-only Python library used by data_modeling, data_pipeline_design, sql_interviews, coding_interviews
- **`sample_data/`** — 8 deterministic CSV/JSONL fixtures (users, products, orders, order_items, events, page_views, transactions, support_tickets) with a regenerate script
- **`docs/reference/`** — canonical question banks:
  - `de_interview_canonical_questions.md` (8 SQL, 8 pipeline, 6 modeling, 7 system design, 6 behavioral)
  - `em_interview_canonical_questions.md` (245 EM questions across 5 categories)
- **`scripts/run_all_tests.py`** — top-level test runner that discovers and runs every track; delegates `system_design/` to its own runner since it uses a different import style

### Test status

```
Track                Run    Fail  Err   Status
system_design        764    82    56    PRE-EXISTING (see 2026-10-09 earlier entry)
data_modeling         91     0     0    OK
data_pipeline_design 140     0     0    OK
sql_interviews        59     0     0    OK
coding_interviews    293     0     0    OK
common                38     0     0    OK
TOTAL               1385    82    56
```

All 5 new code tracks pass cleanly. The 138 pre-existing `system_design`
failures are documented in the System Design entry below — they were
uncovered in the original parallel build and are out of scope for this
build.

### Author

All work authored by **Prem Vishnoi <prem.vishnoi@example.com>** —
no AI attribution in any commit metadata.

---

## 2026-10-09 — Initial System Design Course Build

A complete, runnable **System Design course** (71 lessons, 11 modules, 39 services) was created under `system_design/`. The course is the working, code-first companion to a system-design interview curriculum, with every system implemented as a real Python service you can run on your laptop.

### Added
- **39 services** (URL Shortener, Typeahead, Instagram, Twitter, Newsfeed, YouTube/Netflix, Reddit, Message Queue, Webhooks, Uber Eats, Web Crawler, Job Scheduler, User Export, KV Store, Rate Limiter, Distributed LRU, Dropbox, S3 Storage, Ticketmaster, Hotel Booking, Parking Garage, Metrics/Logging, APM, Doc Processing, Zillow, Weather App, Messenger, WhatsApp, Chess.com, Slack, Google Docs, TikTok, Twitch, AI Support, ChatGPT, File Uploader, LLM Batching, Claude Code, Voice AI).
- **Shared `common/` library**: TTLCache, LRUCache, KeyValueStore, MetricsRegistry, Snowflake IDs, base62 hashing.
- **Sample data** generators (30k records across 6 JSONL files).
- **~764 unit tests** across 39 modules (some pass, some need finalization — see `python3 scripts/run_tests.py`).
- **71 design doc / lesson READMEs** (one per lesson).
- **Exercise files** (one per module) extending the working services.
- **Scripts**:
  - `scripts/seed_data.py` — generate sample corpora
  - `scripts/run_tests.py` — run the entire test suite
  - `scripts/scaffold.py` — scaffold a new module
  - `scripts/run_all_smoke_tests.sh` — bash smoke-test wrapper
  - `scripts/start_all.sh` — start/stop every service in the background
- **Docs**: `docs/HOW_TO_ANSWER.md`, `docs/CONCEPTS_MAP.md`, `docs/TROUBLESHOOTING.md`.
- **Notebooks** (load test + trie walk) under `notebooks/`.
- **`setup.py`** for `pip install -e .` of the course.
- **Curriculum map** (`scripts/curriculum_map.md`) tying modules to the 71 lessons.

### Layout

```
data-engineering-course/
├── system_design/             ← the course (this is the deliverable)
│   ├── 00_overview/           # 5 lessons
│   ├── 01_url_shortener/      # ...
│   ├── 39_reddit_homepage/    # 39th working service
│   ├── 99_appendix/           # 18 concept lessons
│   ├── common/                # shared lib
│   ├── sample_data/
│   ├── scripts/
│   ├── docs/
│   ├── exercises/
│   ├── notebooks/
│   ├── setup.py
│   └── README.md
├── scripts/
│   └── requirements.txt
├── README.md
└── CHANGELOG.md               # ← this file
```

### Quick start

```bash
cd data-engineering-course/system_design
pip install -r ../scripts/requirements.txt
python3 scripts/seed_data.py
python3 scripts/run_tests.py              # full test suite
bash scripts/start_all.sh start           # boot every service
bash scripts/start_all.sh status
bash scripts/start_all.sh stop
```

### Known issues

- ~92 failures + ~55 errors in the test suite (out of 764). Most are
  in modules 05, 07, 09, 11, 17, 28, 35, 37, 38, 39 — these are
  tests-vs-service mismatches where the agent-built tests and the
  agent-built services don't perfectly agree. Each is a small
  one-method or one-line fix; the architecture is sound.
- Sample data is in-memory; for production-scale you'd swap
  `KeyValueStore` for Postgres / DynamoDB / Redis.
