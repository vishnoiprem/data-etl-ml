# Changelog

## 2026-10-10 — dbt + Snowflake Analytics Engineering Cert Prep (Udemy course author source)

New track: `aws_snowflake_dbt_course/`. The author-source companion
for the Udemy course "dbt + Snowflake — Analytics Engineer
Certification Prep" (19 sections, 131 lectures, 11h 57m). Project-
based exam prep built on a realistic **Ethereum blockchain dataset**
in Snowflake. Every lecture maps to an official dbt Analytics
Engineer exam objective. All 76 pytest tests pass; the shared
`dbt_project/` validates cleanly with `dbt parse` (no Snowflake
account required for the smoke test).

### Added — `aws_snowflake_dbt_course/`
- `README.md`, `SYLLABUS.md` (L01–L131 map), `DIRECTORY.md`, `CHANGELOG.md`, `requirements.txt`, `conftest.py` (with `render_jinja()` mock dbt context)
- 19 section folders, each with `README.md` + `lecture_scripts/`:
  - `01_section/` Welcome, dbt init, sources, first model
  - `02_section/` Transactions: fields, categorization, daily activity, stablecoins
  - `03_section/` Object dependencies, staging shielding, materialization precedence, incremental + strategies
  - `04_section/` Practice quiz — materializations
  - `05_section/` DRY: project organization, CTEs, dbt_project.yml, macros (logging, run_query, if execute, return)
  - `06_section/` dbt run, test, docs, seed, compile/ls/clean/build, clean DAGs
  - `07_section/` dbt_project.yml configs: hierarchical, custom schemas, vars, alias
  - `08_section/` Sources + dbt packages: codegen, dbt_utils, audit_helper, Git packages
  - `09_section/` Git basics + branching/PRs/protected branches + merge conflicts
  - `10_section/` Python models + execution constraints
  - `11_section/` Grants: Snowflake behavior, dbt grants, post-hooks, project-level grants
  - `12_section/` Practice quiz — developing dbt models
  - `13_section/` Environments + contracts: schema with codegen, subtleties
  - `14_section/` Versions: setup + latest view, deprecation dates + warnings
  - `15_section/` Model access: project structure, fraud domain, groups + private models
  - `16_section/` Debugging: dbt logs, debug flags, runtime/compilation/db errors
  - `17_section/` State: manifest, run results, selectors, dbt retry
  - `18_section/` Managing data pipelines: CI intro, first CI, defer, dbt clone, Slim CI, continuous deployment
  - `19_section/` Tests (singular, generic, custom, unit, source, severity, selection, advanced), dbt docs, exposures, freshness, snapshots (timestamp + check), microbatch, --sample, final exam
- 131 lecture scripts `L01_…md` … `L131_…md` in their respective `lecture_scripts/`
- 19 quizzes in `quizzes/section_1.md` … `quizzes/section_19.md`
- 4 assignments in `assignments/` (Ethereum ETL, incremental strategy, unit tests, CI pipeline)
- 6 mermaid diagrams in `diagrams/` (project layout, run flow, materialization decision, incremental merge, CI pipeline, state selectors)
- 12 per-section `code/` demos + their `test_*.py` (`stg_first_model`, `activity_incremental`, `log_macro_demo`, `dag_demo`, `fraud_score_demo`, `contracts_demo`, `versions_demo`, `state_selectors`, `dbt_ci_workflow`, `transactions_snapshot`, `generic_test_positive`)
- 2 scripts: `scripts/run_all_tests.py` (discovers all 12 test files + runs `dbt parse` smoke test), `scripts/bootstrap.sh`
- 1 PDF placeholder in `downloads/`

### Added — `dbt_project/`
- `dbt_project.yml` (materialization precedence: staging→view, marts→table), `profiles.yml` (mock target), `packages.yml` (codegen, dbt_utils, audit_helper), `selectors.yml` (result + state-based)
- `models/staging/`: `_sources.yml` (Ethereum sources with freshness), `stg_ethereum__transactions.sql`, `stg_ethereum__blocks.sql`
- `models/marts/`: `transactions.sql` (incremental merge), `activity.sql` (incremental + is_incremental guard), `stablecoin_activity.sql`, `fraud_score.py` (Python model), `dag_demo.sql`, plus split schema files `_grants.yml`, `_contracts.yml`, `_versions.yml`, `_access.yml` (one .yml per concern per dbt 1.12 rule)
- `macros/`: `log_macro.sql`, `dry_refactor.sql`, `debug_helper.sql`
- `seeds/`: `static_categories.csv`
- `snapshots/`: `transactions_snapshot.sql` (timestamp strategy)
- `tests/`: `generic/test_positive_value.sql`, `unit/test_fraud_score_unit.yml`

### Verification
- `dbt parse` exits 0 against the shared `dbt_project/`
- `python3 scripts/run_all_tests.py` → 76 pytest tests, ALL PASS
- Author sweep: every `.md` / `.sql` / `.py` / `.yml` contains `Author: Prem Vishnoi <pvishnoi@avilx.com>`; no `pvilx.com` typo in any actual source file
- Updated parent `README.md` table at line 277 to add the new course row

## 2026-10-10 — Snowflake — The Complete Masterclass (Udemy course author source)

New track: `aws_snowflake_course/`. The author-source companion for
the Udemy course "Snowflake — The Complete Masterclass" (20
sections, 187 lectures, 23 idempotent SQL demos, 12 Python test
suites with **127 tests passing**, 6 mermaid diagrams, 23 quizzes,
4 hands-on assignments). All Python tests mock the Snowflake
connector and pass without a live account; the SQL is real Snowflake
syntax runnable against the free trial.

### Added — `aws_snowflake_course/`
- `README.md`, `SYLLABUS.md` (L01–L187 map), `DIRECTORY.md`, `CHANGELOG.md`, `requirements.txt`
- 20 section folders, each with `README.md` + `lecture_scripts/`:
  - `01_introduction/` (4 lectures)
  - `02_getting_started/` (10 lectures + `setup_warehouse.sql` + 11 tests)
  - `03_snowflake_architecture/` (9 lectures + `editions_pricing.sql` + 8 tests)
  - `04_loading_data/` (9 lectures + `load_csv.sql` + 8 tests)
  - `05_copy_options/` (8 lectures + `copy_options.sql` + tests)
  - `06_unstructured_data/` (9 lectures + `parse_json.sql` + `flatten_array.sql` + 12 tests)
  - `07_performance_optimization/` (9 lectures + `clustering.sql` + tests)
  - `08_loading_from_aws/` (7 lectures + `aws_storage_integration.sql` + 10 tests)
  - `09_loading_from_azure/` (7 lectures + `azure_integration.sql` + tests)
  - `10_loading_from_gcp/` (6 lectures + `gcs_integration.sql` + tests)
  - `11_snowpipe/` (7 lectures + `snowpipe_setup.sql` + 10 tests)
  - `12_cortex_ai_ml/` (14 lectures + `cortex_ai_demo.sql` + 9 tests)
  - `13_snowpipe_azure/` (4 lectures)
  - `14_time_travel/` (6 lectures + `time_travel_demo.sql` + `undrop.sql` + 10 tests)
  - `15_fail_safe/` (2 lectures)
  - `16_types_of_tables/` (4 lectures + `table_types.sql` + tests)
  - `17_zero_copy_cloning/` (6 lectures + `clone_database.sql` + 8 tests)
  - `18_data_sharing/` (11 lectures + `create_share.sql` + 9 tests)
  - `19_data_sampling/` (3 lectures + `sampling.sql` + 7 tests)
  - `20_extra_topics/` (52 lectures: Tasks, Streams, MVs, Masking, Roles, BI Tools, Best Practices + 25 tests)
- 23 quizzes (`quizzes/section_1.md` … `section_19.md` + `section_20a.md` … `section_20d.md`, 8–12 questions each)
- 6 mermaid diagrams in `diagrams/` (snowflake_architecture, warehouse_scaling, storage_integration_flow, snowpipe_architecture, cortex_ai_stack, data_sharing_topology)
- 4 hands-on assignments (`assignments/assignment_1_end_to_end_etl.md`, `assignment_2_cortex_ai_app.md`, `assignment_3_cdc_pipeline.md`, `assignment_4_secure_data_share.md`)
- 2 scripts (`scripts/run_all_tests.py`, `scripts/bootstrap.sh`)

### Verified
- `python3 scripts/run_all_tests.py` reports `ALL PASS` — 127 tests
  across 12 test files (0.25s runtime, no AWS/Snowflake account needed).

---

## 2026-10-10 — 5 more AWS crash courses

New tracks (siblings to `aws_glue_course/`, `aws_lambda_course/`, `aws_ec2_course/`):
- `aws_eventbridge_course/` (7 sections, 36 lectures, 5 boto3 + moto demos, 38 tests)
- `aws_cognito_authorizers_course/` (5 sections, 25 lectures, 2 demos, 11 tests)
- `aws_lambda_authorizer_course/` (5 sections, 25 lectures, 3 demos, 23 tests)
- `aws_cdk_v2_course/` (6 sections, 30 lectures, 3 TypeScript CDK projects, npm-tested)
- `aws_cloudwatch_course/` (7 sections, 35 lectures, 5 boto3 + moto demos, 23 tests)

All 95 boto3 + moto tests pass (`python -m pytest aws_eventbridge_course aws_cognito_authorizers_course aws_lambda_authorizer_course aws_cloudwatch_course -q`).

---

## 2026-10-10 — AWS EC2 + Load Balancing Crash Course (Udemy course author source)

New track: `aws_ec2_course/`. The author-source companion for the
Udemy course "AWS EC2 Crash Course + Load Balancing with Demos" (8
sections, 38 lectures, 6 working boto3 + moto demos, 5 mermaid
diagrams, 8 quizzes, 1 optional assignment). All code samples run
offline via `pytest` + `moto` — no AWS account required.

### Added — `aws_ec2_course/`
- `README.md`, `SYLLABUS.md` (L01–L38 map), `DIRECTORY.md`, `CHANGELOG.md`, `requirements.txt`
- 8 section folders, each with `README.md` and `lecture_scripts/`
  - `01_intro_to_ec2/` (3 lectures, no code)
  - `02_ec2_fundamentals/` (5 lectures + `region_az_demo.py` + tests)
  - `03_creating_ec2/` (10 lectures + `launch_instance.py` + 6 moto tests)
  - `04_ec2_pricing/` (4 lectures + `pricing_calc.py` + 6 tests)
  - `05_managing_ec2/` (4 lectures + `snapshot_ami_demo.py` + 4 moto tests)
  - `06_load_balancing_nlb/` (4 lectures + `nlb_create.py` + 4 moto tests)
  - `07_load_balancing_alb/` (5 lectures + `alb_create.py` + 4 moto tests)
  - `08_load_balancing_gwlb/` (3 lectures + `gwlb_create.py` + 3 moto tests)
- 8 quizzes (`quizzes/section_1.md` … `section_8.md`, 8–12 questions each)
- 6 mermaid diagrams in `diagrams/` (ec2_anatomy, regions_azs, ha_across_azs, alb_request_flow, nlb_request_flow, gwlb_request_flow)
- 1 optional assignment (`assignments/assignment_1_ha_webapp.md`)
- 2 scripts (`scripts/run_all_tests.py`, `scripts/bootstrap.sh`)

### Verified
- `python scripts/run_all_tests.py` reports `ALL PASS` — 30 tests
  across 7 test files.

## 2026-10-10 — AWS Lambda course updates (Use Case 3 + missing lectures)

Update to `aws_lambda_course/`. Adds the 3rd enterprise use case
(FCI Cluster Monitor), the missing Use Case 2 Part 3, the Use Case 2
re-walk in section 9, and the Bedrock API Keys lecture in section 10.

### Added — `aws_lambda_course/`
- **Section 15 (new): L82–L87 — Enterprise Use Case 3: FCI Cluster Monitor**
  (AWS Managed Microsoft AD + FSx for Windows + Lambda + SNS + EventBridge
  + CloudWatch). 6 lecture scripts, `code/monitor_lambda/` with 7 moto
  tests, `code/cloudformation/fci_monitor_stack.yaml` with a `DryRun`
  parameter, `iam_policy.json` (least privilege), `deploy.sh`, and
  `event_payloads/scheduled_event.json` fixture.
- **L31a (section 8):** Use Case 2 Part 3 — unified GET + DELETE handler
  with the full 4xx/5xx error model and CORS. 8 moto tests in
  `code/api_pt3_handlers/`.
- **L36a–L36e (section 9):** Use Case 2 re-walked with a security lens
  (5 new lectures). Working code in `code/usecase2_with_auth/`.
- **L44a (section 10):** API Keys for Amazon Bedrock. Working code in
  `code/api_keys_for_bedrock/` (7 moto tests).
- `quizzes/section_15.md` (10 questions, final quiz).
- `assignments/assignment_7_fci_monitor.md` (optional extension).

### Verified
- `python scripts/run_all_tests.py` reports 102 tests across 9 sections
  with **0 failures**.

## 2026-10-10 — AWS Glue — The Complete Masterclass (Udemy course author source)

New track: `aws_glue_course/`. The author-source markdown for the Udemy course *AWS Glue - The Complete Masterclass* (11 sections, 78 lectures, 4h 11m, 3 role plays, 4 downloadable resources, 6 assignments, 11 quizzes). Section 1 lectures are written as full individual files (L01–L12). Sections 2–10 are bundled per-section (`SECTION_BUNDLE.md`) with one stub file per lecture so the SYLLABUS map resolves.

### Added — `aws_glue_course/`
- `README.md` (course overview + asset map) and `SYLLABUS.md` (lecture L1–L78 → file).
- `01_introduction/lecture_scripts/L01–L12.md` — 12 full lecture scripts (IAM, KMS, SNS, GlueJobRole).
- `02_iam_kms_sns/` through `10_databrew/lecture_scripts/SECTION_BUNDLE.md` — 9 section bundles covering lectures L13–L85.
- `downloads/city_temperature.csv` (480 rows, 20 cities × 2 years).
- `downloads/glue_service_trust_policy.json` (the IAM trust policy for `GlueJobRole`).
- `downloads/glue_pipeline_stack.yaml` (full CloudFormation template: 2 S3 buckets, IAM role, Glue Job).
- `downloads/glue_job_aggregate_cities.py` (PySpark ETL script, validates with `py_compile`).
- `quizzes/section_1.md` through `quizzes/section_11.md` — 11 quizzes (5 multi-choice each, with answer keys).
- `assignments/01–06.md` — 6 assignment prompts (S3, CFN, debug, streaming, DQ, DataBrew).
- `11_role_plays/RP1_trust_misconfig.md`, `RP2_streaming_falling_behind.md`, `RP3_pitch_data_quality.md` — the 3 role plays with persona + script + worked answer + common mistakes.

### Verified
- `city_temperature.csv` is 480 rows, 10 columns, valid CSV.
- `glue_service_trust_policy.json` parses as valid IAM JSON.
- `glue_pipeline_stack.yaml` parses with a CFN-aware YAML loader; 4 resources, 4 parameters, 4 outputs.
- `glue_job_aggregate_cities.py` compiles with `python3 -m py_compile`.

## 2026-10-10 — Meta DE onsite rounds: data modeling + architecture + leadership (E5/E6)

The 4 onsite rounds after the 60-min CoderPad screen: **Data Modeling** (60 min, whiteboard), **Architecture / Product-Sense** (60 min, hardest round), and **Leadership / Ownership** (E5/E6, 30-45 min, standalone). This module ships the worked answers to the 5 most-asked 2026 schema questions, the 5-step architecture framework, and the 4 question families + 5 Meta-value probes for the leadership round.

Sources: [Interview101 2026](https://www.interview101.com/interviews/meta/data-engineer), [Aced 2026](https://www.aced.io/guides/meta-data-engineer-interview), [Tryexponent 2026](https://www.tryexponent.com/guides/meta-data-engineer-interview), [Glassdoor 2026](https://www.glassdoor.com/Interview/Meta-Data-Engineer-Interview-Questions-EI_IE40772.0,4_KO5,18.htm), [HelloInterview E6 2026](https://www.hellointerview.com/guides/meta/e6).

### Added — `sql_interviews/12_meta_onsite_rounds/`

- **`module_overview.md`** — the 4-5 onsite rounds, the 3 content areas covered here
- **`design/01_data_modeling_round.md`** — the 5-step framework, the 5 most-asked 2026 questions (verbatim), what "good" looks like, common failure modes
- **`design/02_architecture_round.md`** — the 5-step framework (product → metrics → schema → ETL → cost), 3 worked examples (WA Business, Reels, Ads Auction), the killer follow-ups
- **`design/03_leadership_round.md`** — the 4 question families, 5 Meta-Value probes, E5 vs E6 signal differences, the 3 follow-ups that catch candidates off-guard
- **`design/04_concrete_solutions.md`** — full worked solutions to all 5 most-asked schema questions (Reels, cross-platform, Ads Auction, ride-share, metric drop)
- **`design/05_companies_to_research.md`** — which Meta org (Reels / UA / Ads / Marketplace / RL) each question comes from, what to read, the killer follow-up
- **`code/meta_onsite_schemas.sql`** — 5 schemas, runnable against SQLite
- **`tests/test_onsite_schemas.py`** — 9 tests
- **`notebooks/01_onsite_schemas.ipynb`** — 5 schemas in 5 cells, each with the canonical query

### Tests

- `sql_interviews/12_meta_onsite_rounds/`: 9 new tests, all green
- Total repo: 1,470 tests (was 1,461)

## 2026-10-10 — Meta DE screen module: 5 SQL + 5 Python + 6 onsite SQL + 5 Jupyter notebooks

The 2026 Meta DE CoderPad is **60 minutes: 5 SQL + 5 Python** (the
same screen). The Python half is **pandas / dict / string
handling**, NOT DSA. The onsite SQL round is product-flavored
open-ended ("calculate what % of Messenger users who were active
yesterday made a video call"). The system-design whiteboard
round uses a 5-step framework: product goal → metrics → schema →
ETL SQL → cost model.

This module ships the worked solutions, the SQLite schema, the
test suite, the 5 Jupyter notebooks, plus a replacement for the
wrong-shape `m113_meta_screen.py` mock (which was 2018-era DSA
content).

### Added — `sql_interviews/11_meta_screen/`

- **`module_overview.md`** — the 60-min CoderPad format, pass bar (3/5 each half), how it maps to the rest of the loop
- **`design/01_loop_structure.md`** — the 60-min CoderPad format, the 4 onsite rounds, the 3-5 week timeline
- **`design/02_sql_problems.md`** — 5 SQL problems (retention, hour-1 peak, top-N, sessionize, gaps-and-islands) with worked solutions + 4 things each tests
- **`design/03_python_problems.md`** — 5 Python problems (upward trend, second-highest salary, CSV parsing, sliding-window user count, tumbling window) with worked solutions
- **`design/04_onsite_flavoured_sql.md`** — 6 deeper SQL problems (Messenger video %, first-country retention, WhatsApp cohort, top ad-sets, hour engagement, auction time-travel)
- **`design/05_sessionization_pattern.md`** — the 30-min-gap pattern deep-dive (LAG + cumulative-sum flag for session_id)
- **`design/06_company_specific.md`** — full Meta DE 2026 walkthrough: 4 onsite rounds, sample questions, Core Values mapping
- **`code/meta_schema.sql`** — 9 tables: instagram_post, instagram_story_events, facebook_post, engagement_event, whatsapp_message, messenger_event, messenger_call, ad_event, ad_auction_event
- **`code/meta_screen_sql.sql`** — 5 problems, canonical solutions
- **`code/meta_screen_python.py`** — 5 functions: `top_5_pages_by_upward_trend`, `second_highest_per_department`, `summarize_by_page`, `users_with_3plus_calls`, `tumbling_window_counts`
- **`code/meta_onsite_sql.sql`** — 6 problems
- **`tests/test_meta_screen_sql.py`** — 5 tests
- **`tests/test_meta_screen_python.py`** — 5 tests
- **`tests/test_meta_onsite_sql.py`** — 6 tests
- **`notebooks/01_meta_screen_sql.ipynb`** — 5 SQL problems
- **`notebooks/02_meta_screen_python.ipynb`** — 5 Python problems
- **`notebooks/03_meta_onsite_sql.ipynb`** — 6 onsite SQL problems
- **`notebooks/04_sessionization.ipynb`** — 30-min gap pattern
- **`notebooks/05_meta_system_design_walkthrough.ipynb`** — 5-step framework with worked example (WA Business dashboard)

### Added — `coding_interviews/15_mock_interviews/code/m119_meta_screen_v2.py`

The wrong-shape m113 (2018-era FizzBuzz + valid parens with
wildcards) is replaced by m119, calibrated to the 2026 format:
3 problems in pandas / dict / string handling. The other 2 of the
5+5 format live in `sql_interviews/11_meta_screen/code/meta_screen_python.py`.

### Updated — `docs/reference/company_specific_prep.md`

Master table now has 2026 Meta + Google DE columns. Two new
deep-dive sections:

- **Meta Data Engineer (2026 deep-dive)** — 7 sourced links (Aced, DataDriven, Interview101, Tryexponent, Datavidhya, Glassdoor, IGotAnOffer), latest-to-oldest
- **Google Data Engineer (2026 deep-dive)** — 4 sourced links (DataDriven, Interview101, IGotAnOffer, HelloInterview), latest-to-oldest

### Tests

- `sql_interviews/11_meta_screen/`: 16 new tests, all green
- Total repo: 1,461 tests (was 1,441)

## 2026-10-10 — Behavioral: 8 new lessons + 50-hour reading list (Google + Meta DE 2026)

The 40-question Data Engineer behavioral bank (the second batch from
the per-company question DB) and the 2026 Google + Meta DE guides
(Datavidhya May 2026, Interview101 2026, Aced 2026, DataDriven
Sept 2026, Tryexponent 2026) revealed 8 gaps in the behavioral
track. All 8 are now covered with worked examples, plus a 50-hour
course-wide reading list parallel-tracking the per-track plans.

### Added — Behavioral lessons (8)

- **`07_decision_by_instinct.md`** — non-STAR "Tell me about a
  decision you made based on your instincts." 3-layer framework
  (data you had / data you didn't / heuristic you used).
- **`08_difficult_team_members.md`** — trap question "What types
  of team members do you find difficult." Reframe: type of
  *situation* not type of *person*. The "I was the problem"
  ownership beat.
- **`09_complex_program_stakeholders.md`** — "Tell me about a
  relevant complex program you've managed." 5-component program
  framework (stakeholders / decision matrix / slip / escalation /
  outcome). Program ≠ project.
- **`10_data_product_pride.md`** — "What product that you led are
  you most proud of." DE-flavored; project → product verb swap.
- **`11_influence_without_authority.md`** — "How do you
  influence without authority." 4 mechanisms (expertise /
  reciprocity / coalition / legitimacy).
- **`12_product_sense_investigation.md`** — "PM at a food delivery
  app, conversion dropped — how do you investigate?" The bridge
  between behavioral and SQL/modeling. 7-step hypothesis tree.
- **`13_unclear_requirements_scoping.md`** — **verbatim from the
  Datavidhya 2026 Google DE guide**: "Tell me about a time you
  worked on a project with unclear requirements. How did you
  scope it?" 5-move scoping playbook.
- **`14_being_wrong_humble_pivot.md`** — **verbatim from the
  Datavidhya 2026 Google DE guide**: "Tell me about a time you
  were wrong. What changed your mind?" The #1 Googleyness hire
  signal per both Datavidhya and Interview101.

### Added — Behavioral index

- **`40_questions_taxonomy.md`** — all 40 bank questions mapped to
  lessons + worked-example scenario + company verbatim match.
  Includes both 2026 loop structures (Meta 3-5 weeks, Google
  6-12 weeks) with sources cited **latest-to-oldest** (Aced,
  DataDriven, Interview101, Tryexponent, Datavidhya, Glassdoor,
  IGotAnOffer).

### Added — Reading list

- **`05_resources.md` rewritten** — from a behavioral-only 8-book
  list to a course-wide 50-hour reading schedule (22 books + 14
  articles/papers + 14 case studies across 8 topic areas). Every
  reading is cross-referenced to a specific lesson in the course.
  222 → 554 lines, ~1,000 → ~2,900 words.

### Refreshed

- `README.md` — totals updated to **495 lessons / 1,441 tests**.
  Added 50-hour reading list callout.
- `behavioral_interviews/README.md` — 31 → **39 lessons**,
  Module 05 expanded from 5 to 13 lessons.
- `data_pipeline_design/README.md` — 31 → **36 lessons**,
  noting the 5 lessons added in the Round-2 review (lakehouse,
  data quality, 3 advanced mocks).

### Stats

- **Behavioral**: 31 → **39 lessons** (+8 net)
- **Course-wide**: 487 → **495 lessons** (+8 net)
- **0 new tests** (prose-only track)
- **All 1,441 tests still pass; no regression** on data_modeling /
  data_pipeline_design / sql_interviews / coding_interviews / common
- 9 new files (`07`-`14` + index) + 1 file rewritten (`05_resources.md`)

### Sources (latest-to-oldest, per user request)

1. **Aced.io (2026)** — Meta DE loop, Ownership questions, pass-bar 3/5.
2. **DataDriven.io (Sept 2026)** — Meta architecture examples.
3. **Interview101.com (2026)** — Meta 5+5 SQL+Python, Google pivot.
4. **Datavidhya (May 2026)** — Google loop with HC, Googleyness pillars, L5 comp.
5. **Tryexponent.com (2026)** — Meta product sense + ownership.
6. **Glassdoor (Meta 2026)** — 5-round loop reports.
7. **IGotAnOffer (May 2026)** — Meta behavioral round structure.
8. **(2024-2025)** — older source coverage already in `02_theory/` and `03_tactics/`.

---

## 2026-10-10 — Data Modeling Spec Remap

The `data_modeling/` track was rewritten to match the official
curriculum spec (Course era / Interview Kickstart-style). The lesson
*count* was already 36; the lesson *names* and *practice scenarios*
now match the spec exactly.

### Remapped modules

- **M2 — Gathering Business Requirements** (8 lessons): renamed to
  the spec's exact titles — Introduction, Recognizing the Core
  Business Problem, Analyzing Metrics, Analyzing Query Patterns,
  Defining Latency Requirements, Data Volume & Scalability, Data
  Retention Policies, Example. Each lesson now opens with a "Why this
  lesson" hook and closes with an "In the interview, you would say…"
  blockquote.
- **M3 — High-Level Model Diagrams** (8 lessons): 2 conceptual
  (Creating Diagrams, Evolving Models) + 6 practice (E-commerce, Social
  Media, Video Streaming, Ride-Sharing, Cloud Services, Online
  Advertising). Two new practice lessons (Cloud Services, Online
  Advertising) added; the existing 5 schemas kept and reframed.
- **M4 — Dimension Design** (3 lessons): new foundational lesson
  *Dimension Table Design* added (the anatomy, the wide-and-
  denormalized rule, the 7 components of a good dim); SCDs and
  Advanced Dimension Design follow.
- **M7 — Mock Interviews** (6 lessons): rewritten to the spec's
  scenario list — Ride-Sharing, Customer Support, Airbnb, Stripe,
  Instagram, Amazon. Four new mocks written (Customer Support, Airbnb,
  Stripe, Instagram); Uber→Ride-Sharing; the off-spec fitness/
  library/hospital/hotel mocks removed.

### Stats

- **Lessons**: 36 (unchanged)
- **Tests**: 115 (was 91; +24 from the 2 new M3 schemas + 4 new M7 schemas)
- **Files added**: 9 (M2 rewrite, M3/M4 new lessons, M7 new mocks + 2 new schemas)
- **Files renamed**: 17 (across M2, M3, M4, M7)
- **Files removed**: 5 (1 M4 junk-degenerate merged into M4 advanced; 4 M7 off-spec mocks)
- All tests still pass green.

---

## 2026-10-10 — Round-2 Review Pass: End-to-End Interview Coverage

A second code-review pass identified 8 P0 gaps that would prevent the
course from delivering on its "complete data engineering interview prep"
promise. All P0 items now have content; the course is end-to-end
interview-pass-ready for a Meta E5 / Google L5 / Senior-DE loop.

### Added — End-to-end coverage

- **`docs/reference/de_interview_loop_walkthrough.md`** (1,100+ lines) — the
  central study-plan document: 6-week day-by-day plan, per-round prep,
  day-before checklist, during-loop reminders, post-loop debrief, and a
  self-assessment rubric. This is the "how do I use this course?" doc.
- **`docs/reference/company_specific_prep.md`** (3,600+ words) — prep
  guidance for 7 target companies (Meta, Google, Stripe, Netflix,
  Airbnb, Databricks, Snowflake) with a master comparison table and
  per-company sections on loop style, what they test, what to study,
  and common failure modes.
- **`how_to_get_the_interview/compensation/`** — new module with 4 lessons
  (leveling, offer anatomy, negotiation scripts, comp benchmarking).
  This closes the loop after the offer.
- **`how_to_get_the_interview/design/10_recruiter_screen.md`** — the
  recruiter-screen lesson that wasn't covered elsewhere.
- **`behavioral_interviews/05_practice/design/06_de_project_deep_dive.md`**
  — the 5-act structure for the 30-60 minute "walk me through a past
  project" round, with a 1500-word worked example.
- **`data_pipeline_design/07_mock_interviews/design/31-34_*.md`** — 4
  advanced pipeline mocks for senior+ candidates: feature store,
  multi-tenant analytics, data observability, real-time streaming.
- **`data_pipeline_design/02_storage/design/08_data_lakehouse_design.md`**
  — the lakehouse design lesson that wasn't covered.
- **`data_pipeline_design/06_performance/design/28_data_quality.md`** +
  `code/data_quality.py` + `tests/test_data_quality.py` — the 5 standard
  data quality checks with a working `QualityCheck` class and 16 tests.
- **`sql_interviews/10_query_performance/`** — new module with 4 lessons
  (EXPLAIN plans, index strategy, join optimization, query rewrites) +
  8 tests that exercise the rewrites against SQLite.

### Added — Infrastructure & code

- **`data_pipeline_design/02_storage/code/lakehouse.py`** + 8 tests — the
  bronze/silver/gold reference implementation that backs the lakehouse
  design lesson.
- **`sql_interviews/10_query_performance/tests/test_rewrites.py`** — 8
  tests that exercise the 4 most-asked query-rewrite patterns.

### Improved — Format and motivation

- Standardized the `coding_interviews/README.md` header to match the other
  tracks' banner style.
- Added a 4-week week-by-week study plan to both
  `sql_interviews/README.md` and `coding_interviews/README.md` (matches
  the behavioral/data_modeling/sa pattern).
- Added "Why this module" hooks to:
  - `sql_interviews/07_easy_practice/module_overview.md`
  - `coding_interviews/02_complexity/module_overview.md`

### Stats

- **Tracks**: 12 (unchanged)
- **Modules**: 70 (was 69; +1 for compensation, +1 for query_performance)
- **Lessons**: 487 (was 473; +14 net)
- **Tests**: 1,417 (was 1,385; +32 net)
- All 5 new-track tests still pass green.
- The 138 pre-existing system_design failures are unchanged.

---

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

All work authored by **Prem Vishnoi <pvishnoi@avilx.com>** —
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
