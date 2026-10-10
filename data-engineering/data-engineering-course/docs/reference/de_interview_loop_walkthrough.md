# The Data Engineering Interview Loop: A 6-Week End-to-End Walkthrough

> **One document. Twelve tracks. Six weeks. A clear path from "I think I
> should interview" to "I have an offer."**
>
> This is the usage guide for the rest of the course. If you are staring
> at 473 lessons wondering "in what order do I do this thing?" — this
> document answers that question completely. Read the per-track READMEs
> for depth; read this for the synthesis.
>
> Audience: senior data engineers targeting Meta E5, Google L5, Stripe,
> Netflix, Databricks, Snowflake, or equivalent Senior-DE roles.
> Difficulty: assumes 3+ years of production DE experience.

---

## Table of Contents

1. [The DE interview loop in 2026](#1-the-de-interview-loop-in-2026)
2. [The 6-week study plan](#2-the-6-week-study-plan)
3. [Per-round preparation](#3-per-round-preparation)
   - 3.1 [Recruiter screen](#31-recruiter-screen)
   - 3.2 [SQL round](#32-sql-round)
   - 3.3 [Coding round](#33-coding-round)
   - 3.4 [Pipeline design round](#34-pipeline-design-round)
   - 3.5 [Data modeling round](#35-data-modeling-round)
   - 3.6 [Behavioral round](#36-behavioral-round)
   - 3.7 [Hiring manager / deep-dive round](#37-hiring-manager--deep-dive-round)
   - 3.8 [System design round](#38-system-design-round)
4. [Company-specific tweaks](#4-company-specific-tweaks)
5. [The day before the loop](#5-the-day-before-the-loop)
6. [During the loop](#6-during-the-loop)
7. [After the loop](#7-after-the-loop)
8. [Self-assessment rubric](#8-self-assessment-rubric)
9. [Appendix: pacing variations](#9-appendix-pacing-variations)

---

## 1. The DE interview loop in 2026

The shape of the loop is fairly stable across the big tech / data
platform companies. The total elapsed time from first recruiter email
to written offer is **2-4 weeks**. The total interview time is
**4-7 hours** spread across **4-6 rounds**.

### Typical loop structure

| Round | Length | Format | What it tests | Bar |
|---|---|---|---|---|
| Recruiter screen | 30 min | Phone / video | Motivation, comp, timing, visa | Recruiter judgment |
| Technical phone (SQL) | 60 min | CoderPad / live SQL | Window functions, joins, aggregations | L4 / junior L5 |
| Technical phone (coding) | 60 min | CoderPad / whiteboard | Python/Scala, data structures, complexity | L4 / junior L5 |
| Onsite: SQL deep-dive | 60 min | Live SQL | Multi-step query, optimization, business framing | L5 |
| Onsite: Coding | 45-60 min | Whiteboard / CoderPad | Medium-hard algorithmic problem | L5 |
| Onsite: Pipeline design | 60 min | Whiteboard | End-to-end pipeline architecture, trade-offs | L5 |
| Onsite: Data modeling | 45-60 min | Whiteboard | Star schema, SCD, fact/dim design | L5 |
| Onsite: System design | 60 min | Whiteboard | Distributed systems + DE twist | L5 (Senior add) |
| Onsite: Behavioral | 45-60 min | Conversational | STAR stories, leadership, conflict | All levels |
| Onsite: Hiring manager / deep-dive | 60 min | Conversational + walk-through | Past project, technical depth, ownership | L5+ |

### Company-specific overlays

| Company | Distinctive round | Note |
|---|---|---|
| **Meta (E5)** | **Bar-raiser** in the loop. A non-team interviewer calibrated to the company-wide E5 bar. Independent vote; can veto. Expect one extra round, plan 5-6 onsites. SQL and coding are weighted higher than at Google. |
| **Google (L5)** | **Google Cloud Assessment (GCA)** — usually before onsite, ~3 hrs covering coding + system design. Then 4-5 onsites including a "Googliness" round. Heavy on distributed systems / system design. |
| **Stripe** | Heavy "build it" round — they want a working data pipeline sketch with concrete API/tool choices. Less trivia, more production realism. |
| **Netflix** | Culture fit / "Dream Team" round weighted heavily. They pay top of market, expect senior autonomy, ask about judgment under ambiguity. |
| **Databricks** | Heavy Spark / lakehouse / Delta Lake. Expect pipeline questions to lean into Photon, Delta, Unity Catalog, MLflow. |
| **Snowflake** | Heavy SQL, Snowflake-specific features (streams/tasks, dynamic tables, semi-structured data). |
| **Anthropic, OpenAI** | Smaller loops (3-4 rounds), heavier on system design and behavioral judgment, less trivia. |

### The calendar reality

| Stage | Typical duration |
|---|---|
| Application → recruiter screen | 1-2 weeks |
| Recruiter screen → tech phone | 3-7 days |
| Tech phone → onsite | 1-2 weeks |
| Onsite → debrief | 3-7 days |
| Debrief → offer | 1-3 days |
| **Total** | **3-6 weeks** |

You have less time than you think. That is why we compress prep into
6 weeks.

---

## 2. The 6-week study plan

### How to read this table

- Each row is a **study block** of 2-3 hours.
- 5 blocks per week, ~12 hours/week. Plus weekend review.
- Total: ~70 blocks over 6 weeks.
- Track codes: `SQL` = `sql_interviews/`, `COD` = `coding_interviews/`,
  `PIPE` = `data_pipeline_design/`, `MOD` = `data_modeling/`, `SD` =
  `system_design/`, `BEH` = `behavioral_interviews/`, `GET` =
  `how_to_get_the_interview/`, `SOL` = `solutions_architect/`.
- Mark each block done with a checkbox. If you miss a block, the
  weekend review is your first catch-up.

### Week 1 — Foundation & self-assessment

| # | Day | Track | Module / lesson | Goal |
|---|---|---|---|---|
| 1.1 | Mon AM | GET | `how_to_get_the_interview/` lessons 1-3 | Resume baseline + targeting |
| 1.2 | Mon PM | GET | `how_to_get_the_interview/` lessons 4-6 | LinkedIn, GitHub, portfolio |
| 1.3 | Tue AM | GET | `how_to_get_the_interview/` lessons 7-9 + referrals | Outreach playbook |
| 1.4 | Tue PM | `self-assessment` | Section 8 of this doc | Score yourself 1-4 on every competency |
| 1.5 | Wed AM | SQL | `sql_interviews/01_overview/` | What this course expects you to know |
| 1.6 | Wed PM | SQL | `sql_interviews/02_fast_track/` | Refresh the mental model |
| 1.7 | Thu AM | SQL | `sql_interviews/03_basic_querying/` module 1-2 | SELECT, WHERE, ORDER BY |
| 1.8 | Thu PM | SQL | `sql_interviews/03_basic_querying/` module 3-end | CASE, NULL, basic joins |
| 1.9 | Fri AM | COD | `coding_interviews/01_overview/` | What the coding round looks like |
| 1.10 | Fri PM | COD | `coding_interviews/02_complexity/` | Big-O refresher + data engineer focus |
| 1.11 | Sat AM | BEH | `behavioral_interviews/01_fast_track/` | STAR in 30 minutes |
| 1.12 | Sat PM | BEH | `behavioral_interviews/02_theory/` | What interviewers actually score |

> **End-of-week 1 checkpoint**: You can write 5 STAR bullets from your
> last 3 years. You can write a basic SQL query with joins, CASE, NULL
> handling. You can solve a 30-line LeetCode easy in 10 minutes. Resume
> is updated. If any of these are false, do not move to Week 2.

### Week 2 — Core SQL + light coding

| # | Day | Track | Module / lesson | Goal |
|---|---|---|---|---|
| 2.1 | Mon AM | SQL | `sql_interviews/04_aggregations/` module 1-2 | GROUP BY, HAVING, COUNT/SUM tricks |
| 2.2 | Mon PM | SQL | `sql_interviews/04_aggregations/` module 3-end + tests | Aggregate edge cases |
| 2.3 | Tue AM | SQL | `sql_interviews/05_joins/` module 1-3 | INNER, LEFT, anti-join, self-join |
| 2.4 | Tue PM | SQL | `sql_interviews/05_joins/` module 4-end + tests | Multi-table joins + interview patterns |
| 2.5 | Wed AM | SQL | `sql_interviews/06_window_functions/` module 1-3 | ROW_NUMBER, RANK, DENSE_RANK |
| 2.6 | Wed PM | SQL | `sql_interviews/06_window_functions/` module 4-6 | LAG, LEAD, running totals |
| 2.7 | Thu AM | SQL | `sql_interviews/06_window_functions/` module 7-end | NTILE, frame clauses, advanced frames |
| 2.8 | Thu PM | SQL | `sql_interviews/07_easy_practice/` | 10-15 easy problems, timed |
| 2.9 | Fri AM | COD | `coding_interviews/03_patterns/` | Two pointers, sliding window, hash |
| 2.10 | Fri PM | COD | `coding_interviews/04_arrays/` + `05_hash_tables/` | Data engineer relevant patterns |
| 2.11 | Sat AM | COD | `coding_interviews/06_searching_sorting/` | Practice 3 medium problems |
| 2.12 | Sat PM | BEH | `behavioral_interviews/03_story_bank/` module 1 | Brainstorm 6 stories (target 90 min) |

> **End-of-week 2 checkpoint**: You can solve any easy/medium SQL
> problem with a window function or CTE in under 15 minutes. You can
> write a 2-pointer or hash-table solution to a LeetCode medium in
> under 25 minutes. You have 6 STAR stories drafted.

### Week 3 — Heavy SQL practice + pipeline design foundations

| # | Day | Track | Module / lesson | Goal |
|---|---|---|---|---|
| 3.1 | Mon AM | SQL | `sql_interviews/08_medium_practice/` problems 1-4 | Timed, 25 min each |
| 3.2 | Mon PM | SQL | `sql_interviews/08_medium_practice/` problems 5-8 | Timed |
| 3.3 | Tue AM | SQL | `sql_interviews/08_medium_practice/` problems 9-12 | Timed, focus on DENSE_RANK + running totals |
| 3.4 | Tue PM | SQL | `sql_interviews/08_medium_practice/` problems 13-end | Timed, focus on optimization |
| 3.5 | Wed AM | PIPE | `data_pipeline_design/01_overview/` | Pipeline design framework |
| 3.6 | Wed PM | PIPE | `data_pipeline_design/02_storage/` | Warehouses, lakes, lakehouse, formats |
| 3.7 | Thu AM | PIPE | `data_pipeline_design/03_extraction/` | CDC, batch, streaming |
| 3.8 | Thu PM | PIPE | `data_pipeline_design/04_transformation/` | dbt, Spark, schema evolution |
| 3.9 | Fri AM | PIPE | `data_pipeline_design/05_loading/` | Serving patterns, indexes, marts |
| 3.10 | Fri PM | PIPE | `data_pipeline_design/06_performance/` | Scaling, partitioning, monitoring |
| 3.11 | Sat AM | SQL | `sql_interviews/09_hard_practice/` problems 1-3 | Hard problems — get used to multi-CTE |
| 3.12 | Sat PM | BEH | `behavioral_interviews/03_story_bank/` module 2-3 | Refine 6 stories to 2 minutes each |

> **End-of-week 3 checkpoint**: You can solve a 4-table join + window
> function problem in under 30 minutes. You can sketch a pipeline
> (source → ingest → transform → serve) with concrete tech choices.
> Your 6 STAR stories are 2 minutes each and end with a quantified
> result.

### Week 4 — Data modeling + system design + interview simulation

| # | Day | Track | Module / lesson | Goal |
|---|---|---|---|---|
| 4.1 | Mon AM | MOD | `data_modeling/01_overview/` + `02_requirements/` | Kimball vs Inmon, dimensional primer |
| 4.2 | Mon PM | MOD | `data_modeling/03_high_level_diagrams/` module 1-2 | Fact/dim, grain, SCD types |
| 4.3 | Tue AM | MOD | `data_modeling/03_high_level_diagrams/` module 3-end | Practice: fitness app, ride-sharing |
| 4.4 | Tue PM | MOD | `data_modeling/04_dimension_design/` | SCD2 in depth, junk dims, role-playing |
| 4.5 | Wed AM | MOD | `data_modeling/05_fact_modeling/` | Fact tables, measures, late-arriving |
| 4.6 | Wed PM | MOD | `data_modeling/06_performance/` | Partitioning, sort keys, query plans |
| 4.7 | Thu AM | SD | `system_design/00_overview/` + `01_url_shortener/` or simpler | DE-tinted system design primer |
| 4.8 | Thu PM | SD | `system_design/03_instagram/` + `06_yt_or_netflix/` | DE-adjacent (data-heavy) designs |
| 4.9 | Fri AM | PIPE | `data_pipeline_design/07_mock_interviews/` design 1-2 | Walk through a full pipeline problem |
| 4.10 | Fri PM | MOD | `data_modeling/07_mock_interviews/` design 1-2 | Walk through a full schema problem |
| 4.11 | Sat AM | SQL | `sql_interviews/09_hard_practice/` problems 4-end | Hard problems — recursive CTEs |
| 4.12 | Sat PM | BEH | `behavioral_interviews/04_mock_interviews_and_analyses/` | Mock 1 with a friend or record yourself |

> **End-of-week 4 checkpoint**: You can design a star schema for
> Instagram or a fitness app in under 45 minutes. You can design a
> system with a data-heavy twist (e.g. newsfeed ranking) in 60
> minutes. You can do a full mock interview end-to-end.

### Week 5 — Mock interviews + weak-area drilling

| # | Day | Track | Module / lesson | Goal |
|---|---|---|---|---|
| 5.1 | Mon AM | SQL | `sql_interviews/09_hard_practice/` redo 3 hardest | Targeted drilling |
| 5.2 | Mon PM | COD | `coding_interviews/13_recursion/` + `14_dp/` | Two hardest patterns for DE |
| 5.3 | Tue AM | PIPE | `data_pipeline_design/07_mock_interviews/` design 3-4 | Timed, 60 min each |
| 5.4 | Tue PM | PIPE | `data_pipeline_design/07_mock_interviews/` design 5-end | Timed |
| 5.5 | Wed AM | MOD | `data_modeling/07_mock_interviews/` design 3-4 | Timed, 45 min each |
| 5.6 | Wed PM | MOD | `data_modeling/07_mock_interviews/` design 5-end | Timed |
| 5.7 | Thu AM | BEH | `behavioral_interviews/04_mock_interviews_and_analyses/` 2-3 | Mocks with feedback |
| 5.8 | Thu PM | BEH | `behavioral_interviews/05_practice/` lessons 1-3 | Targeted question practice |
| 5.9 | Fri AM | SD | `system_design/07_message_queue/` + `12_user_data_export/` | DE-flavored systems |
| 5.10 | Fri PM | SD | `system_design/15_distributed_lru/` + `17_s3_storage/` | Storage-flavored systems |
| 5.11 | Sat AM | SQL | Re-run your 5 hardest problems | Verify you still solve them |
| 5.12 | Sat PM | ALL | Full mock loop (2 hours) | SQL + coding + pipeline + behavioral |

> **End-of-week 5 checkpoint**: You can run a 4-round mock loop in
> under 3 hours and score 4/4 on at least 2 of the 4 rounds.

### Week 6 — Polish, company-specific, applications, recovery

| # | Day | Track | Module / lesson | Goal |
|---|---|---|---|---|
| 6.1 | Mon AM | ALL | Re-do your 3 weakest lessons | Targeted drilling |
| 6.2 | Mon PM | SOL | `solutions_architect/` module 1-2 | Adjacent skill for senior |
| 6.3 | Tue AM | SOL | `solutions_architect/` module 3-end | Architecture patterns |
| 6.4 | Tue PM | BEH | `behavioral_interviews/05_practice/` lessons 4-end | Targeted question practice |
| 6.5 | Wed AM | ALL | Company-specific research (see §4) | Read job descriptions, recent engineering blogs |
| 6.6 | Wed PM | GET | Re-engage referral network | 10-20 warm referrals |
| 6.7 | Thu AM | SQL | `sql_interviews/exercise.md` | Final cold-run |
| 6.8 | Thu PM | COD | `coding_interviews/exercise.md` | Final cold-run |
| 6.9 | Fri AM | ALL | Light review only | Do not cram |
| 6.10 | Fri PM | ALL | Print/queue your STAR stories | Ready to recite |
| 6.11 | Sat AM | ALL | **Day-before prep** (see §5) | The doc, checklist, kit |
| 6.12 | Sat PM | — | Rest. Sleep 8+ hours. | — |

> **End-of-week 6 checkpoint**: You are ready. Sleep is the next-best
> study session.

### Optional: track-specific deepening

If after week 4 you realize a single track is your weakness, swap a
block from a stronger track. The recommended deepening moves:

| Weakness | Add this block |
|---|---|
| SQL window functions | `sql_interviews/06_window_functions/` redo all modules |
| SQL recursive CTEs | `sql_interviews/09_hard_practice/` problems 6-8 |
| Coding trees/graphs | `coding_interviews/08_graphs/` + `09_trees/` |
| Coding DP | `coding_interviews/14_dp/` |
| Pipeline at scale | `data_pipeline_design/06_performance/` + Kafka deep-dive (web) |
| Data modeling | `data_modeling/03_high_level_diagrams/` redo all |
| Behavioral | `behavioral_interviews/04_mock_interviews_and_analyses/` redo all |

---

## 3. Per-round preparation

### 3.1 Recruiter screen

#### What this round tests

| Dimension | What they're really asking |
|---|---|
| Motivation | "Will this person actually accept if we offer?" |
| Comp | "Is their expectation in our band?" |
| Timing | "Are they available when we need them?" |
| Visa | "Can they legally start in 30-60 days?" |
| Communication | "Will my hiring managers want to talk to this person?" |

#### Which track(s) and lessons to use

- `how_to_get_the_interview/` — all 9 lessons, especially the
  targeting + comp negotiation modules
- `behavioral_interviews/01_fast_track/` — the 30-second "tell me
  about yourself" template

#### Common failure modes

| Failure mode | Why it kills you |
|---|---|
| Vague comp expectation | Recruiter can't place you in a band → no loop |
| Bad-mouthing current employer | Signals risk, makes recruiter nervous |
| "I'm flexible on role" | Sounds like you don't know what you want |
| Not knowing the company | Recruiter takes it as lack of seriousness |
| Asking about comp/benefits first | Wait until they bring it up |

#### If you only do 3 things

1. **Have a one-sentence pitch** ready. "I'm a senior data engineer
   with 4 years of experience building streaming pipelines in Kafka
   and Spark at [current company], and I'm looking for a role where I
   can own a larger surface area end-to-end."
2. **Know your comp number** — base, RSUs, bonus — and have a
   flexibility band (e.g. "X to X+20%"). Don't lowball.
3. **Ask 3 smart questions** at the end: "What does the team own?"
   "What's the biggest data problem you're trying to solve right now?"
   "What does success look like in the first 6 months?"

---

### 3.2 SQL round

#### What this round tests

| Skill | Weight | What "good" looks like |
|---|---|---|
| Window functions | Highest | Reach for them instinctively; know the difference between RANK, DENSE_RANK, ROW_NUMBER |
| CTEs | High | Multi-CTE solutions, not nested subqueries |
| Joins | High | Comfortable with self-joins, anti-joins, lateral joins |
| Aggregations | Medium | GROUP BY + HAVING, conditional aggregation with FILTER/CASE |
| Query optimization | Medium | Reads EXPLAIN plans, knows when to denormalize vs index |
| Business framing | Medium | Asks clarifying questions, restates the problem, names trade-offs |

#### Which track(s) and lessons to use

- `sql_interviews/01_overview/` through `06_window_functions/` — full
  sequence, in order
- `sql_interviews/07_easy_practice/` — warm-up
- `sql_interviews/08_medium_practice/` — the meat
- `sql_interviews/09_hard_practice/` — for senior-level
- `docs/reference/de_interview_canonical_questions.md` — sample answers
  for DENSE_RANK and running totals

#### Common failure modes

| Failure mode | What to do instead |
|---|---|
| Jumping into code | Restate the problem, ask about edge cases, sketch on paper first |
| Using nested subqueries | Default to CTEs. Interviewers explicitly penalize this. |
| Wrong window frame | When in doubt, draw the partition + order + frame on paper |
| Not handling NULLs | Always ask: "Are NULLs expected here? Should they be excluded?" |
| Slow query, no explanation | Talk through index choice, partition pruning, denormalization |
| No business framing | "Top 3 by department" → ask: top 3 by what period? ties? ties handled how? |

#### If you only do 3 things

1. **Master window functions cold.** DENSE_RANK, ROW_NUMBER, LAG/LEAD,
   running totals with `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT
   ROW`. If you don't reach for these instinctively, you fail the
   round.
2. **Always start with a CTE.** Even for simple queries. It signals
   maturity and is easier to debug live.
3. **Ask clarifying questions before writing SQL.** "What is the
   expected output? Ties? NULLs? Time zone?" This is 30% of the
   signal.

---

### 3.3 Coding round

#### What this round tests

| Skill | Weight | What "good" looks like |
|---|---|---|
| Problem decomposition | Highest | Breaks problem into pieces before coding |
| Data structure choice | Highest | Hash table for O(1) lookup, heap for top-K, etc. |
| Big-O analysis | High | Articulates time/space complexity at every step |
| Edge case handling | High | Empty input, single element, duplicates, large N |
| Code quality | Medium | Clean variable names, no copy-paste, comments on tricky bits |
| Communication | Medium | Thinks out loud, asks before assuming |

#### Which track(s) and lessons to use

- `coding_interviews/01_overview/` + `02_complexity/`
- `coding_interviews/03_patterns/` — the 12 patterns framework
- `coding_interviews/04_arrays/` through `13_recursion/` — pick the
  4-5 most relevant for DE: arrays, hash tables, strings, trees,
  heaps
- `coding_interviews/14_dp/` — for L5; skip for some companies
- `coding_interviews/15_mock_interviews/` — final practice

#### DE-specific coding note

For Meta E5 / Google L5, the coding round is **not** "build a
pipeline." It is the same LeetCode-medium style problem you would see
in a SWE interview. Focus there. Save Spark/Kafka for the pipeline
round.

#### Common failure modes

| Failure mode | What to do instead |
|---|---|
| Coding first, thinking later | Spend 5-10 min talking before any code |
| Wrong data structure | Always ask: "What operations am I doing most?" |
| O(n²) when O(n) is possible | Walk through with a small example to catch this |
| Not testing | After coding, trace through 2-3 inputs by hand |
| Giving up on the optimal | Brute force first, then improve. Don't sit silent. |
| Wrong language | Pick Python or your strongest language. The interview is in your strongest language. |

#### If you only do 3 things

1. **Practice the 12 patterns.** Most DE coding problems are
   variations on: two pointers, sliding window, hash map, BFS/DFS,
   binary search, heap, linked list, tree BFS/DFS, top-K, merge
   intervals. Master these.
2. **Always say complexity out loud.** After writing the solution, end
   with "this is O(n) time and O(n) space." Even if wrong, it signals
   you think about it.
3. **Brute force is a valid first step.** If stuck, code the
   O(n²) version, then say "now let me think about how to make this
   faster." Interviewers reward that progression.

---

### 3.4 Pipeline design round

#### What this round tests

| Skill | Weight | What "good" looks like |
|---|---|---|
| Requirements gathering | Highest | Asks 8-10 questions before drawing anything |
| High-level architecture | Highest | Sources → ingest → transform → serve → monitor |
| Tech selection | High | Names concrete tools with trade-offs (Kafka vs Kinesis, dbt vs Spark) |
| Trade-off articulation | High | "I'd pick X because Y, but Z is reasonable if W" |
| Failure modes | High | "What if Kafka is down for 2 hours? Backpressure? Replay?" |
| Monitoring/observability | Medium-high | Always volunteered unprompted |
| Cost awareness | Medium | Mentions storage cost, compute cost, partitioning cost |

#### Which track(s) and lessons to use

- `data_pipeline_design/01_overview/` — the framework
- `data_pipeline_design/02_storage/` — warehouse, lake, lakehouse,
  Parquet vs Avro vs ORC
- `data_pipeline_design/03_extraction/` — CDC, batch, streaming
- `data_pipeline_design/04_transformation/` — dbt, Spark
- `data_pipeline_design/05_loading/` — serving patterns
- `data_pipeline_design/06_performance/` — scaling, partitioning,
  retry, DLQ
- `data_pipeline_design/07_mock_interviews/` — full walkthroughs
- `docs/reference/de_interview_canonical_questions.md` — the
  Pipeline Design Framework (Clarify → Source → Ingest → Transform →
  Serve → Monitor)

#### Common failure modes

| Failure mode | What to do instead |
|---|---|
| Drawing boxes without asking | Always ask 8-10 clarifying questions first |
| "It depends" without specifics | "It depends" is fine if followed by 2-3 named options |
| Skipping monitoring | Always end with: "How do we know it's broken? SLAs? Alerts?" |
| Ignoring scale | Always give a number: "At 10TB/day, 1B events/day, X workers" |
| No failure mode discussion | Spend the last 10-15 min on "what breaks first" |
| Single tool fetishism | "Spark is great, but for this case dbt on Snowflake is simpler" |

#### If you only do 3 things

1. **Ask 8-10 questions before drawing.** Volume, velocity, format,
   freshness SLA, downstream consumers, retention, cost ceiling,
   existing infra, team skills. Write them on the board.
2. **Always include monitoring.** Even if the interviewer doesn't ask.
   Name a metric (lag, success rate, cost per pipeline), a threshold,
   and an alert destination.
3. **Name a specific failure mode and how you'd handle it.** "If the
   upstream Kafka topic is down for 30 min, we have a 30-min lag in
   the warehouse. Recovery: replay from offset using the last 7 days
   retained in Kafka."

---

### 3.5 Data modeling round

#### What this round tests

| Skill | Weight | What "good" looks like |
|---|---|---|
| Clarifying the use case | Highest | "What decisions does this model support?" |
| Grain statement | Highest | "One row per [entity] per [period]" |
| Fact vs dimension | High | Distinguishes measures from context |
| SCD choice | High | Justifies SCD1 vs SCD2 vs SCD3 |
| Schema quality | High | No nullable primary keys, no fan traps, no chasm traps |
| Trade-off articulation | Medium | Star vs snowflake, denormalized vs normalized |

#### Which track(s) and lessons to use

- `data_modeling/01_overview/` + `02_requirements/`
- `data_modeling/03_high_level_diagrams/` — 6 practice problems
- `data_modeling/04_dimension_design/` — SCD2 in depth
- `data_modeling/05_fact_modeling/` — fact tables, measures
- `data_modeling/06_performance/` — partitioning, sort keys
- `data_modeling/07_mock_interviews/` — final practice
- `docs/reference/de_interview_canonical_questions.md` — fitness app
  schema sample answer

#### Common failure modes

| Failure mode | What to do instead |
|---|---|
| Drawing tables without grain | "What is the grain?" — answer this first, always |
| Single big table | Resist. Interviewers want to see normalization thinking. |
| Wrong SCD | When in doubt, SCD2. Justify the choice. |
| Ignoring "how does it change?" | Every dim needs: "How does this change over time?" |
| No thought to query patterns | "What are the 3 most common queries? My model optimizes for those." |

#### If you only do 3 things

1. **State the grain first.** "One row per workout per user per day."
   Then design around that.
2. **Use the canonical schemas.** Practice the 6 high-level diagrams
   until you can draw a star schema for an Instagram / ride-sharing /
   Spotify / Amazon / fitness / support analytics use case in under
   45 minutes.
3. **Always discuss SCD2.** SCD2 is the most common dimension
   pattern. Show you understand effective_date, expiry_date, and the
   `current_flag` column.

---

### 3.6 Behavioral round

#### What this round tests

| Signal | What "good" looks like |
|---|---|
| Self-awareness | Names mistakes, talks about growth, doesn't blame others |
| Impact | Quantifies outcomes (latency reduced 40%, cost saved $X/year) |
| Technical judgment | When asked, explains trade-offs made in past projects |
| Leadership | Drives projects, mentors, influences without authority |
| Conflict resolution | "Disagreement with X" → resolved by Y, with positive outcome |
| Communication | Concise, structured, no rambling |

#### Which track(s) and lessons to use

- `behavioral_interviews/01_fast_track/` — STAR in 30 min
- `behavioral_interviews/02_theory/` — what they actually score
- `behavioral_interviews/03_story_bank/` — your 6-8 stories
- `behavioral_interviews/04_mock_interviews_and_analyses/` — practice
- `behavioral_interviews/05_practice/` — question-by-question drilling
- `docs/reference/de_interview_canonical_questions.md` — the
  "mistake" sample answer

#### Common failure modes

| Failure mode | What to do instead |
|---|---|
| "We" instead of "I" | Use "I" for your actions, "we" for team outcomes |
| 10-minute stories | Practice to 2-3 minutes max. Cut the backstory. |
| Vague impact | "Improved performance" → "Reduced p95 latency from 4s to 600ms" |
| No lesson learned | Every story ends with "the lesson was X" or "I now do Y" |
| Same story for every question | Have 6-8 distinct stories covering: leadership, conflict, mistake, technical judgment, project, cross-team, prioritization, failure |
| No specific tools named | "I built a streaming pipeline in Kafka + Flink that handled 1B events/day" |

#### If you only do 3 things

1. **Have 6 distinct STAR stories ready**, each ≤2.5 min, each ending
   with a quantified result. Cover: leadership, conflict, mistake,
   project, cross-team, technical judgment.
2. **Cut the backstory to 1 sentence.** "Situation: I was the lead
   DE on the payments team at X, and we needed to migrate 4TB of
   transaction data from Redshift to Snowflake in 6 weeks." Then
   jump to action.
3. **Quantify impact in every story.** Pipeline uptime, latency,
   cost, team size, lines of code, data volume. If you can't quantify,
   the story is too vague.

---

### 3.7 Hiring manager / deep-dive round

#### What this round tests

| Signal | What "good" looks like |
|---|---|
| Depth of past work | Walk through a project, including architecture and code |
| Decision-making | "Why did you pick X over Y?" |
| Ownership | "What was fully yours vs shared?" |
| Self-evaluation | "What would you do differently?" |
| Future fit | "How does this role align with your goals?" |

#### Which track(s) and lessons to use

- `behavioral_interviews/03_story_bank/` — your longest, deepest
  project story, 5-7 min
- `em_introduction/` — engineering manager lens, even if you're not
  applying for EM
- `people_management/` — for senior+
- `project_retrospective/` — your recent project write-up

#### Common failure modes

| Failure mode | What to do instead |
|---|---|
| Generic project summary | Be ready to whiteboard the architecture. Pull up code if asked. |
| "I was on a team that did X" | Own the slice you touched. "I owned the streaming layer, my teammate owned batch." |
| No numbers | Be ready with: scale, latency, team size, time-to-deliver, downstream users |
| Badmouthing ex-coworkers | Even when asked about conflict, focus on your actions and lessons |
| No "what I'd do differently" | This question will come. Have a real, specific answer. |

#### If you only do 3 things

1. **Pick your deepest project and prepare a 5-7 min walkthrough**
   including whiteboard diagram, scale numbers, and 3-4 design
   decisions you'd defend.
2. **Prepare answers to "what would you do differently?"** for each
   of your top 3 projects. Be honest — interviewers sniff out fake
   humility.
3. **Prepare 3 questions about the role and team** — what's the
   current biggest pain, what does the team own, what's the
   interviewer's history with the team.

---

### 3.8 System design round

#### What this round tests

This round overlaps with the pipeline design round but at higher
abstraction: distributed systems design with a data engineering twist.
The DE lens is: data flow, scale, consistency, durability, recovery.

| Signal | What "good" looks like |
|---|---|
| Requirements | Asks about scale, freshness, consistency, durability |
| High-level | Draws data flow + control flow separately |
| Storage choice | Names DB type with reason (OLTP vs OLAP, key-value vs SQL) |
| Data model | Sketches schema on the board |
| API / query layer | Defines contracts before implementation |
| Scale | Names bottleneck, names solution (sharding, partitioning, caching) |
| Failure modes | Always discussed: what if X dies |

#### Which track(s) and lessons to use

- `system_design/00_overview/` — framing
- `system_design/03_instagram/` — feed storage (DE-heavy)
- `system_design/06_yt_or_netflix/` — video metadata (DE-heavy)
- `system_design/07_message_queue/` — Kafka-style queue
- `system_design/11_job_scheduler/` — Airflow-style scheduler
- `system_design/12_user_data_export/` — async pipeline
- `system_design/15_distributed_lru/` + `17_s3_storage/` — storage
- Cross-reference: `data_pipeline_design/02_storage/` for the
  Parquet/Avro/Delta distinction

#### Common failure modes

| Failure mode | What to do instead |
|---|---|
| Jumping to component list | Always: requirements → high-level → drill into 1-2 components |
| No scale numbers | Always: "At 100M DAU, X events/sec, Y TB/day..." |
| No consistency discussion | Pick a model: strong, eventual, read-your-writes. Justify. |
| No failure mode discussion | Always end with: "What if [component] dies?" |
| Ignoring the data pipeline | For DE, you must draw the pipeline even if not asked |

#### If you only do 3 things

1. **Always do the 4-step opener**: (1) functional requirements
   (1-2 sentences), (2) non-functional requirements (scale, freshness,
   consistency), (3) high-level architecture, (4) drill into 1-2
   components.
2. **For DE-flavored problems, draw the data pipeline even if not
   asked.** Even a URL shortener question should end with "and we
   stream click events to Kafka → warehouse for analytics."
3. **Have 3-4 systems design templates ready.** Queue, cache, sharded
   SQL, event-sourced pipeline. Memorize the components, customize
   per problem.

---

## 4. Company-specific tweaks

The full per-company guide is in
`docs/reference/de_interview_company_guides.md` (separate doc). For
now, the highest-leverage differences:

### Meta (E5)

| Round | Specifics |
|---|---|
| Recruiter | Fast, formal, comp band discussed early |
| SQL | Heavy. 2 SQL rounds, ~4-5 problems total. Window functions + multi-CTE expected. |
| Coding | Standard LeetCode medium. Trees/graphs common. |
| Pipeline | Less weight than SQL/coding. Be ready for a data-modeling-flavored question. |
| Modeling | Star schema + SCD2. Practice the 6 high-level diagrams. |
| Bar-raiser | One extra round with a non-team interviewer. Independent vote, can veto. They look for cross-functional impact and "would I want to work with this person?" signal. |
| Offer | 4-year RSU grant, refreshers yearly. Negotiate base + sign-on + RSU mix. |

### Google (L5)

| Round | Specifics |
|---|---|
| GCA | 3 hrs before onsite. Coding (2 problems) + system design. Pass / fail gate. |
| SQL | 1 round, 1-2 problems. Easier than Meta's SQL. |
| Coding | Standard. Slightly harder than Meta. |
| Pipeline | Higher weight than Meta. Be ready to discuss GCP services (Dataflow, Pub/Sub, BigQuery). |
| System design | Heavy. Distributed systems, consistency, CAP. |
| Googliness | Cultural round. "What if you disagreed with your manager?" |
| Offer | 4-year RSU grant, GSUs. Negotiate sign-on, refreshers, level calibration. |

### Stripe

| Round | Specifics |
|---|---|
| SQL | Strong. Multi-step queries, business framing. |
| Pipeline | "Build it" round. They want concrete API/tool choices and a working sketch, not just boxes. |
| Coding | Standard. |
| Behavioral | Strong culture fit emphasis. |
| Offer | Cash-heavy. Limited RSUs. Negotiate base hard. |

### Netflix

| Round | Specifics |
|---|---|
| Dream Team round | "Would I want to work with this person every day?" — heavy signal. |
| SQL | Solid. |
| Pipeline | Real-world ambiguity. They want senior judgment, not perfect answers. |
| Coding | Standard. |
| Behavioral | Senior autonomy: "tell me about a time you operated without clear direction." |
| Offer | All cash (no RSUs). Top of market. Negotiate base. |

### Databricks

| Round | Specifics |
|---|---|
| Pipeline | Heavy Spark / Delta / Lakehouse / Photon / Unity Catalog. They assume you know these. |
| Coding | Standard. |
| System design | Distributed compute-heavy (Spark internals, shuffle, partitioning). |
| Behavioral | "Customer obsession" + "bias for action" (Amazon-style, but Databricks-flavored). |
| Offer | RSUs + cash. Negotiate sign-on. |

### Snowflake

| Round | Specifics |
|---|---|
| SQL | Heavy. Snowflake-specific features: streams, tasks, dynamic tables, semi-structured (VARIANT, PARSE_JSON). |
| Pipeline | SnowSQL / Snowpipe / tasks heavy. |
| Coding | Standard. |
| Modeling | Standard. |
| Offer | RSUs + cash. |

---

## 5. The day before the loop

### Sleep

| Item | Recommendation |
|---|---|
| Total sleep | 8+ hours. Non-negotiable. |
| Bedtime | 10 PM or earlier. Set 2 alarms. |
| Caffeine | Cut off at noon. |
| Screens | Off by 9 PM. |

### Food

| Meal | Recommendation |
|---|---|
| Breakfast | Protein + complex carbs. Eggs + oats. Avoid heavy sugar. |
| Lunch | Light. Salad + protein. Heavy meals make you sleepy. |
| Snacks | Almonds, banana, water. |
| Coffee | Same amount you normally drink. Don't experiment. |
| Water | 2-3L total. Dehydration = brain fog. |

### Prep kit

| Item | Why |
|---|---|
| Laptop charger + working laptop | Backup if hotel Wi-Fi dies |
| Phone charger | Both cables (USB-C and Lightning) |
| Notebook + 2 pens | Whiteboard isn't always available for pre-round notes |
| Bottle of water | Stay hydrated through 4-6 hours of talking |
| Chewing gum or mints | Between rounds, fresh breath |
| Snacks (almonds, protein bar) | Blood sugar crashes after lunch |
| Backup headphones (wired) | For virtual rounds |
| Quiet space + tested mic | For virtual rounds — test 30 min before |
| Glasses / contact case | If applicable |
| Tide-to-go pen | Spills happen |

### Mental prep

| Block | Activity |
|---|---|
| 30 min before bed | Skim this document's §6 (during the loop). Internalize the reminders. |
| 10 min before bed | One SQL window-function problem (DENSE_RANK by department). Light review only. |
| First alarm | Wake up. Do not check email yet. |
| Morning | Shower, breakfast, walk for 15 min. No cramming. |
| 60 min before round 1 | Light review of STAR stories, one SQL warmup, your "tell me about yourself" once out loud. |
| 15 min before round 1 | Stop. Hydrate. Breathe. You are ready. |

### What to read (in order)

1. This document, §6.
2. The job description for the role.
3. The team's recent engineering blog posts (if any).
4. Your STAR stories (skim).
5. Your 3 hardest SQL problems (skim).
6. Nothing else. No new material.

### What NOT to do

- Cram new content. You will muddle existing knowledge.
- Read interview horror stories on Reddit.
- Stare at a screen for hours.
- Reformat your resume. The resume is locked.
- Cold-message recruiters. They cannot help you in the next 24 hours.

---

## 6. During the loop

A round-by-round reminder sheet. Print or pin this.

### Before every round

| Step | Action |
|---|---|
| 1 | Water + breath. 3 deep breaths. |
| 2 | Skim your one-page notes for this round. |
| 3 | Put away your phone. |
| 4 | Smile at the interviewer. "Hi, thanks for taking the time." |

### Recruiter screen

- Lead with your 30-second pitch.
- Have comp number ready.
- Ask 3 questions at the end.
- Do not negotiate comp yet.

### SQL round

| # | Reminder |
|---|---|
| 1 | Restate the problem, ask clarifying questions (NULLs, ties, time range). |
| 2 | Sketch the output columns on paper before writing SQL. |
| 3 | Default to CTEs. Multi-CTE for clarity. |
| 4 | Reach for window functions when ranking/running/period-comparison. |
| 5 | Walk through with sample data after writing. |

### Coding round

| # | Reminder |
|---|---|
| 1 | Read the problem twice. Restate. Ask edge-case questions. |
| 2 | Talk for 5 min before any code. Names + complexity. |
| 3 | Brute force is fine. Optimize after. |
| 4 | Say complexity out loud at the end. |
| 5 | Test by tracing through 2-3 inputs. |

### Pipeline design round

| # | Reminder |
|---|---|
| 1 | Ask 8-10 questions first. Write them on the board. |
| 2 | Draw the boxes: source → ingest → transform → serve. |
| 3 | Name concrete tools with reasons (Kafka not "streaming"). |
| 4 | Discuss scale: events/sec, GB/day, freshness SLA. |
| 5 | Always end with monitoring + a named failure mode + recovery. |

### Data modeling round

| # | Reminder |
|---|---|
| 1 | State the use case + decisions supported. |
| 2 | State the grain of every fact table explicitly. |
| 3 | Identify facts vs dimensions. |
| 4 | Address SCD2 for any user/account-like dimension. |
| 5 | End with 3 sample queries to validate the design. |

### Behavioral round

| # | Reminder |
|---|---|
| 1 | STAR. Always STAR. |
| 2 | Cut backstory to 1 sentence. |
| 3 | Use "I" for actions, "we" for outcomes. |
| 4 | Quantify the result. |
| 5 | End every story with the lesson or the systemic change. |

### Hiring manager / deep-dive round

| # | Reminder |
|---|---|
| 1 | Lead with a 2-min project walkthrough. |
| 2 | Whiteboard the architecture if asked. |
| 3 | Own the slice you touched. Be specific. |
| 4 | Have 3 "what would I do differently" answers ready. |
| 5 | Ask 3 questions about the team and the role. |

### System design round

| # | Reminder |
|---|---|
| 1 | Functional + non-functional requirements first. |
| 2 | High-level architecture: data flow + control flow. |
| 3 | Drill into 1-2 components in detail. |
| 4 | Discuss consistency + failure modes. |
| 5 | For DE, draw the data pipeline. Always. |

### Between rounds

| Step | Action |
|---|---|
| 1 | Stand up, walk for 2-3 min. |
| 2 | Drink water. |
| 3 | Eat a small snack if needed. |
| 4 | Re-read the relevant row of this document. |
| 5 | 3 deep breaths. Smile. Next round. |

### After the loop

| Step | Action |
|---|---|
| 1 | Thank the recruiter. Send a thank-you note within 24 hrs. |
| 2 | Write down every question you got — while fresh. |
| 3 | Self-assess on §8 of this document. |
| 4 | Decide: do I want to debrief with the recruiter this week? |
| 5 | Don't check your email obsessively. Debriefs take 3-7 days. |

---

## 7. After the loop

### Immediate (within 24 hours)

| Action | Detail |
|---|---|
| Thank-you notes | One per interviewer, 3-4 sentences. Reference something specific they said. Do NOT mass-template. |
| Self-debrief | Write down every question you got. Score yourself per §8. |
| Pipeline reset | Stop studying. You need a day off. |

### If you got the offer

| Step | Action |
|---|---|
| 1 | Express excitement. Ask for the written offer. |
| 2 | Read every line of the offer. RSUs vs options, vesting, cliff. |
| 3 | Negotiate. Always. See `how_to_get_the_interview/lesson_8` (or equivalent). |
| 4 | Typical levers: base, sign-on bonus, RSUs/refreshers, start date. |
| 5 | Get final terms in writing. |
| 6 | If you have other loops in flight, ask for an extension. |

### If you were rejected

| Step | Action |
|---|---|
| 1 | Ask the recruiter for feedback within 48 hours. |
| 2 | Typical response: "It was close but we went with another candidate." Push politely. |
| 3 | Identify the weakest round from your self-assessment. |
| 4 | Re-apply after 6-12 months at the same company, or immediately at a different one. |
| 5 | The new loop is 4-6 weeks again. The same prep cycle applies. |

### When to negotiate

- Always. Even if you love the first number.
- The company expects it. Not negotiating is a negative signal.
- Lead with your strongest competing offer, even if it's hypothetical
  ("I have an offer at $X from Y").
- Be ready to walk. The strongest negotiating position is willingness
  to say no.
- Final rule: never accept verbally in the moment. Always ask for
  written offer, 24-48 hours to review.

### Re-application strategy

| Situation | Recommended action |
|---|---|
| Failed at recruiter screen | Re-apply in 6 months. Strengthen resume in the interim. |
| Failed at tech phone | Re-apply in 6-12 months. Drill the specific weakness. |
| Failed at onsite, 1 round weak | Re-apply in 6-9 months. Drill the specific round. |
| Failed at onsite, multiple rounds weak | Re-apply at the same level, or down-level (L4 → L4) immediately. |
| Withdrew voluntarily | Re-apply anytime. Stronger signal than a reject. |
| Got far, lost to internal candidate | Re-apply in 3-6 months. Internal candidates often leave within 18 months. |

---

## 8. Self-assessment rubric

Use this to score yourself before starting (baseline), after Week 3
(mid-course), and after Week 6 (post-prep). Be honest. The number
tells you where to focus.

### Scoring levels

| Level | Description |
|---|---|
| 1 / 4 | Novice. Could not answer an interview question on this. |
| 2 / 4 | Working knowledge. Can answer a basic question with help. |
| 3 / 4 | Interview-ready. Can answer most questions independently. |
| 4 / 4 | Senior-level. Can answer + design + critique trade-offs. |

### Competency matrix

| Competency | What "4/4" looks like | 1/4 | 2/4 | 3/4 | 4/4 |
|---|---|---|---|---|---|
| **SQL — basic** | SELECT, WHERE, GROUP BY, ORDER BY with NULLs and CASE | Can't write a multi-table query | Single-table only, with notes | Solid, no help | Could teach it |
| **SQL — joins** | Self-join, anti-join, multi-table lateral | Doesn't know LEFT vs INNER | INNER + LEFT only | Adds anti-joins confidently | Knows when to use EXISTS vs IN |
| **SQL — window functions** | RANK, DENSE_RANK, ROW_NUMBER, LAG/LEAD, frames | Never used | Used once, needs docs | Reaches for them by default | Knows edge cases (ties, NULL ordering) |
| **SQL — CTEs** | Multi-CTE, recursive CTE | Doesn't use | One CTE, then nested subqueries | Multi-CTE with comments | Recursive + named window CTEs |
| **SQL — optimization** | Reads EXPLAIN, picks sort/dist keys, denormalizes | Doesn't think about it | Knows "add an index" | Reads plans, picks partitions | Designs schema for query patterns |
| **Coding — complexity** | Articulates time/space for any solution | Doesn't know Big-O | Knows the basics | Articulates per-line | Designs for the target complexity from the start |
| **Coding — data structures** | Hash, heap, tree, graph — picks the right one | Arrays only | Hash table for O(1) | Picks heap, tree, graph confidently | Knows amortized cost, e.g. LRU |
| **Coding — patterns** | 12 patterns: two pointers, sliding window, BFS, etc. | Doesn't recognize patterns | Recognizes 2-3 | Recognizes 6+ | Sees the pattern in the first 5 min |
| **Coding — Python/Scala** | Clean, idiomatic code in 30 min | Slow, syntax errors | Works but ugly | Clean, with comments | Production-grade |
| **Pipeline — high-level** | Sources → ingest → transform → serve → monitor | Doesn't know where to start | Sketches boxes, no tools | Names tools with reasons | Discusses trade-offs, picks per scenario |
| **Pipeline — storage** | Lakehouse, warehouse, formats, partitioning | Doesn't know warehouse vs lake | Knows one option | Compares 2-3 | Discusses Delta/Iceberg/Hudi trade-offs |
| **Pipeline — streaming** | Kafka, Flink, exactly-once, watermarks | Never used streaming | Knows concepts | Designs a streaming pipeline | Discusses rebalancing, late events, state |
| **Pipeline — orchestration** | Airflow, dependencies, retries, SLAs | Doesn't use orchestrators | Basic DAGs | Handles backfills, retries | DAG sensors, dynamic tasks, SLAs |
| **Pipeline — failure modes** | DLQ, retries, backfill, replay, idempotency | Doesn't think about it | Mentions "retry" | Names 2-3 failure modes | Designs for them in advance |
| **Modeling — grain** | States grain before drawing tables | Doesn't think about grain | States it when asked | States it first | Picks the right grain per use case |
| **Modeling — fact/dim** | Distinguishes measures from context | Mixes them up | Mostly correct | Confident | Justifies per table |
| **Modeling — SCD** | SCD1/2/3, when to use which | Doesn't know what SCD is | Knows SCD2 | Justifies SCD choice | Handles late-arriving + corrections |
| **Modeling — schema quality** | No fan traps, no chasm traps, naming | Doesn't think about it | Names tables, no comments | Adds comments, FKs | Catches traps, normalizes correctly |
| **System design — high-level** | Requirements → architecture → drill | Doesn't know where to start | Boxes without requirements | Functional + non-functional | Drives the discussion |
| **System design — scale** | Names bottleneck + solution | Doesn't think about scale | Mentions "shard" | Quantifies with numbers | Designs for 10x |
| **System design — failure modes** | Discusses what breaks first | Doesn't discuss | Mentions "retry" | Names 2-3 failure modes | Designs for them, includes monitoring |
| **Behavioral — STAR** | 6 stories, 2 min each, quantified impact | Can't tell a story | Rambling | STAR structure, 3-4 min | Tight 2 min, quantified result |
| **Behavioral — leadership** | Owned a project end-to-end, mentored, influenced | "I was on a team" | Owned a slice | Owned a project | Owned an org-wide initiative |
| **Behavioral — self-awareness** | Names mistakes, talks about growth | Blames others | Acknowledges role | Specific mistake + lesson | Systemic change post-mistake |
| **Communication** | Concise, structured, asks clarifying questions | Rambles, jumps to code | Mostly clear | Asks before assuming | Drives the discussion |
| **Compensation** | Knows band, has flexibility, negotiates | Doesn't know market | Has a single number | Has a band | Negotiates confidently |

### Self-assessment template

```markdown
# Self-Assessment — [Date]

Total score: __/108 (27 competencies × 4 max)

Top 3 strengths:
1. _______________
2. _______________
3. _______________

Top 3 weaknesses:
1. _______________ (score __/4)
2. _______________ (score __/4)
3. _______________ (score __/4)

This week's focus:
1. _______________
2. _______________
3. _______________
```

Take this assessment:
- **Day 1** of Week 1 (baseline)
- **End of Week 3** (mid-course) — adjust the plan if any score is
  still 1/4
- **End of Week 6** (post-prep) — final readiness check
- **Before each interview** (sanity check)

A total score of 75+ is interview-ready for Senior-DE / L5. Below 60,
extend the plan to 8 weeks. Below 45, focus on a different role
level.

---

## 9. Appendix: pacing variations

### 8-week plan (recommended for first-time interviewees)

If 6 weeks feels compressed, stretch to 8 weeks. The change:

- Weeks 1-2: same
- Weeks 3-5: same as the original 3-5
- Week 6: full mock loop + redo 3 weakest
- Week 7: company-specific research + applications + referrals
- Week 8: light review + the day before

### 4-week plan (only if you have 3+ years of recent interview reps)

- Week 1: SQL only, fast track + medium practice
- Week 2: Pipeline + modeling
- Week 3: Coding + system design
- Week 4: Behavioral + mocks

This plan assumes you can already solve LeetCode mediums in 25
minutes and have a current STAR story bank. Don't do 4 weeks unless
you've been in a recent loop.

### For senior+ (L6 / Staff)

Add 1-2 weeks. Add `em_introduction/` and `people_management/` for
the leadership signal. Add `solutions_architect/` for the
architecture lens. Practice 2-3 system design rounds instead of 1.
Practice a 5-min "walk me through your most complex system" answer.

### For junior (L4 / E4)

Cut the `system_design/15_distributed_lru/` and similar advanced
lessons. Spend more time on `coding_interviews/13_recursion/` and
`14_dp/`. Add `coding_interviews/15_mock_interviews/`. Plan 8-10
weeks.

### For career switchers (e.g. SWE → DE)

Use the 8-week plan, but redirect Week 1-2 to:
- `data_pipeline_design/01_overview/` + `02_storage/` (foundation)
- `data_modeling/01_overview/` (foundation)
- Then resume the standard plan from Week 3.

---

## Closing

The interview loop is not a single test. It is 4-6 short tests. The
way to pass it is to prepare for each short test independently, in
the order they happen, with the right material for each.

This course has 473 lessons. You will use ~250 of them in the next 6
weeks. The rest are depth material you'll reach for as you grow into
the role.

If you do the 6-week plan above, you will be ready. If you do the
per-round prep in §3, you will pass. If you do the day-before
checklist in §5, you will show up at your best.

The interview is not asking you to be the best data engineer in the
world. It is asking: "Can this person do this job at this level,
start in 4-6 weeks, and grow?" The plan above helps you show them
yes.

Good luck.

*Author: Prem Vishnoi <prem.vishnoi@example.com>*
