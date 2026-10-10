# Company-Specific Data Engineering Interview Prep

> A reference guide that maps 7 target companies to their typical data
> engineering loop, what each round actually tests, and which tracks in
> this course you should prioritize for each one. Read this **after**
> you've skimmed `de_interview_canonical_questions.md` — that file is
> the question bank; this file is the routing table.
>
> **Audience:** engineers targeting E4/E5 (Meta), L4/L5 (Google),
> Senior/Staff (Stripe, Airbnb, Databricks, Snowflake), and Staff/Principal
> (Netflix) data engineering roles.

---

## Master comparison table

| Company | Loop length | Heaviest round | Key differentiator | Top 3 tracks to prioritize |
|---|---|---|---|---|
| **Meta (Facebook)** | **3-5 weeks, 5+5+4+1** (2026) | **60-min CoderPad: 5 SQL + 5 Python** | Dedicated data-modeling round; bar-raiser; 5 Core Values (Ownership) | `sql_interviews/11_meta_screen/`, `sql_interviews/12_meta_onsite_rounds/`, `behavioral_interviews/` |
| **Google** | **6-12 weeks, 7 stages** (2026) | Data System Design (45 min) | Hiring Committee (post-loop); Googleyness = 30% of eval | `coding_interviews`, `system_design`, `behavioral_interviews` |
| **Stripe** | 4–5 rounds, ~3 weeks | Coding + API/system design | Customer-first culture; written take-home; "engineers who care about correctness" | `coding_interviews`, `system_design`, `data_modeling` |
| **Netflix** | 4–5 rounds, ~3 weeks | System design (discussion, not whiteboard) | "Highly effective" calibration; culture deck; senior+ roles only | `behavioral_interviews`, `system_design`, `coding_interviews` |
| **Airbnb** | 4–5 rounds, ~3 weeks | Coding + System design with product lens | "Belong anywhere" customer-centric; product/cross-functional round | `coding_interviews`, `system_design`, `behavioral_interviews` |
| **Databricks** | 4–5 rounds, ~3 weeks | Pipeline / Spark / Delta Lake | Deep technical pipeline focus; fewer behavioral rounds | `data_pipeline_design`, `coding_interviews`, `sql_interviews` |
| **Snowflake** | 4–5 rounds, ~3 weeks | SQL + warehouse design | SQL + warehouse deep dive; very technical; small loops | `sql_interviews`, `data_pipeline_design`, `data_modeling` |

> Loop length is end-to-end (recruiter screen to offer); expect 1 week
> of prep between each round for senior+ roles.
>
> **2026 update.** The Meta + Google rows above reflect the most recent
> 2026 guides. Meta's loop is now 3-5 weeks end-to-end with a 60-min
> CoderPad screen that is *5 SQL + 5 Python* (pass bar 3/5 in each
> half) and a **dedicated data-modeling round** that's their
> signature differentiator. Google's loop is 6-12 weeks with a
> **Hiring Committee** stage after the loop; the candidate never
> meets the committee. See the per-company deep-dive sections below
> and the `sql_interviews/11_meta_screen/` module for the worked
> Meta screen problems.

---

## Meta Data Engineer (2026 deep-dive)

> **Sources** (latest to oldest): [Aced.io (2026)](https://www.aced.io/guides/meta-data-engineer-interview) ·
> [DataDriven.io (Sept 2026)](https://datadriven.io/companies/meta/interview) ·
> [Interview101.com (2026)](https://www.interview101.com/interviews/meta/data-engineer) ·
> [Tryexponent.com (2026)](https://www.tryexponent.com/guides/meta-data-engineer-interview) ·
> [Glassdoor (Meta 2026)](https://www.glassdoor.com/Interview/Meta-Data-Engineer-Interview-Questions-EI_IE40772.0,4_KO5,18.htm) ·
> [IGotAnOffer (May 2026)](https://igotanoffer.com/blogs/product-manager/behavioral-interview-questions-tech-companies)

### The loop (3-5 weeks)

| Stage | Duration | Format | Pass signal |
|---|---|---|---|
| Recruiter screen | 30 min, phone | Non-technical: "How much data? What tools? Why Meta?" | Move to phone screen |
| **Technical screen** | **60 min, CoderPad** | **5 SQL + 5 Python** (~25 min each half) | **3 of 5 in each half** |
| Onsite: SQL/coding | 60 min | Funnel/cohort/time-series + Python on social event data | Pass |
| Onsite: **data modeling** | 60 min | **Dedicated round — Meta's #1 differentiator** | Pass |
| Onsite: product sense / full-stack | 60 min | Product goal → metric → schema → ETL SQL | Pass |
| Onsite: Ownership | 30 min | Meta Core Values (Move Fast, Be Bold, Be Open, Build Social Value, Focus on Long-Term Impact) | Pass |
| Team match | 1-2 weeks | Manager calls | Offer |

### What makes Meta's loop different from Google's

1. **No DSA in the Python screen.** Meta's Python is pandas / dict /
   string handling on million-row data. Iterative loops on a
   DataFrame are *rejected*. If you have only prepared
   FizzBuzz / parens-with-wildcards, you will fail the 2026 screen.
2. **Dedicated data-modeling round.** Google embeds modeling in
   1/3 of interviews; Meta has a *full 60-min dedicated round*.
   The star schema + SCD + bridge tables + partitioning signals
   are the differentiator.
3. **No system-design round as a separate slot.** Scale
   trade-offs (partitioning, bucketing, indexing) are pushed
   *inside* the data-modeling and SQL rounds. The "design a
   pipeline at Meta scale" example is an *architecture probe*,
   not a dedicated round.
4. **Product sense is the opening 10 min of every onsite
   technical round.** Not its own round. But the candidate
   who fails to *frame* their SQL/modeling in product
   terms scores 2/4.

### What to study (per the canonical Meta sources)

- **SQL screen prep** — `sql_interviews/11_meta_screen/`. The
  5+5 problems in `code/meta_screen_sql.sql` and
  `code/meta_screen_python.py` are calibrated to the 2026
  format. The signature patterns are sessionization
  (`design/05_sessionization_pattern.md`), gaps-and-islands
  (Problem 5 in `02_sql_problems.md`), and top-N-after-filter
  (Problem 3).
- **Data modeling prep** — `sql_interviews/12_meta_onsite_rounds/`
  for the 5 most-asked 2026 questions with worked solutions
  (Reels, cross-platform, Ads Auction, ride-share, metric drop) and
  the SQL schema that backs them; also
  `data_modeling/03_high_level_diagrams/` for the 5 working star
  schemas; `data_modeling/04_dimension_design/` for SCD 1/2/3;
  `data_modeling/07_mock_interviews/` for 6 full mock interviews.
  The Meta 2026 guide explicitly lists Instagram Reels / cross-platform
  user behavior / ads auction as the 3 most-asked modeling questions;
  all 3 are in this module.
- **Architecture / product-sense prep** —
  `sql_interviews/12_meta_onsite_rounds/design/02_architecture_round.md`
  for the 5-step framework (product goal → metrics → schema → ETL SQL
  → cost model) with the WA Business worked example. The
  `notebooks/05_meta_system_design_walkthrough.ipynb` in Module 11
  has the live execution.
- **Leadership (E5/E6) prep** —
  `sql_interviews/12_meta_onsite_rounds/design/03_leadership_round.md`
  for the 4 question families, 5 Meta-Value probes, and E5-vs-E6
  signal differences. Pairs with the broader
  `behavioral_interviews/05_practice/` track.
- **Product sense prep** — `behavioral_interviews/05_practice/design/12_product_sense_investigation.md`
  for the 7-step hypothesis-tree framework; the sessionization
  notebook (`notebooks/04_sessionization.ipynb`) for the
  30-min gap pattern that shows up in every product-sense
  investigation.
- **Ownership (behavioral) prep** —
  `behavioral_interviews/05_practice/design/40_questions_taxonomy.md`
  for the 40-question map; `behavioral_interviews/04_mock_interviews_and_analyses/`
  for the 4 full mock interviews (Meta E5 / Google L6 / Netflix Principal / EM M5).
- **Comp & leveling** — `how_to_get_the_interview/compensation/`
  for the negotiation scripts. IC5 (the L5 target) is ~$311K
  base per levels.fyi 2026.

### Failure modes specific to Meta

1. **Treating the Python screen as DSA.** 80% of fail reports
   cite "I prepared FizzBuzz; the screen was pandas on social
   event data." Don't be the 80%.
2. **No sessionization pattern.** The 30-min-gap is asked in
   *every* Meta DE loop. If you don't have it cold, you fail.
3. **Skipping the data-modeling round prep.** The dedicated
   round is Meta's differentiator; the candidate who has
   only practiced SQL fails here.
4. **Forgetting the Meta Core Values.** The Ownership round
   is the tiebreaker per the 2026 guide. Generic answers
   "cost offers" — see the 5 Core Values worked examples
   in `behavioral_interviews/05_practice/`.

---

## Google Data Engineer (2026 deep-dive)

> **Sources** (latest to oldest): [Datavidhya (May 2026)](https://datavidhya.com/blog/google-data-engineering-interview-guide/) ·
> [Interview101 (2026)](https://www.interview101.com/interviews/google/data-engineer) ·
> [Preper (2026)](https://preper.app/guides/google-behavioral-interview-prep) ·
> [HelloInterview (2026)](https://www.hellointerview.com/guides/google/l5)

### The loop (6-12 weeks)

7 stages with a **Hiring Committee (HC)** in the middle. The
candidate never meets the HC — they read the 4 packets the
interviewers wrote. This means the most important artifact
the candidate produces isn't their live performance; it's
*the 4 packets the interviewers wrote about them*.

| Stage | Duration | Format |
|---|---|---|
| Recruiter screen | 30 min, phone | |
| Phone screen 1 | 45 min | SQL + light coding |
| Phone screen 2 (optional, senior+) | 45 min | Borderline or senior candidates |
| Onsite 1: Algorithm coding | 45 min | Medium LeetCode |
| Onsite 2: Data System Design | 45 min | YouTube watch time, search analytics, ad targeting |
| Onsite 3: SQL & Data Modeling | 45 min | BigQuery nested/repeated, SCD, partition/cluster |
| Onsite 4: Googleyness & Leadership | 45 min | **30% of overall eval** |
| Hiring Committee | 2-4 weeks | (Internal — you don't meet them) |
| Team matching | 1-4 weeks | After the loop |
| Offer & comp | 1 week | Comp committee |

### What to study

- **Algorithm coding** — `coding_interviews/04_arrays/`,
  `05_hash_tables/`, `06_searching_sorting/`, `08_graphs/`,
  `09_trees/`. Medium LeetCode. **Note:** the DE loop has
  *one* algorithm round, not two. The other onsite rounds
  are DE-specific.
- **Data system design** — `system_design/00_overview/` +
  the 18 concept lessons in `system_design/99_appendix/`.
  The 2026 Google DE guide lists YouTube watch time, search
  analytics, and ad targeting as the 3 most-asked prompts.
  Each of these maps to a system_design module:
  - YouTube/Netflix → `system_design/06_youtube/`
  - Search analytics → `system_design/02_typeahead/`
  - Ad targeting → `system_design/04_instagram/` or
    `system_design/05_twitter/`
- **SQL & data modeling** — `sql_interviews/10_query_performance/`
  for the 4 query-rewrite lessons; `data_modeling/` for the
  modeling half. BigQuery nested/repeated is in
  `sql_interviews/10_query_performance/design/03_query_rewrites.md`.
- **Googleyness** — `behavioral_interviews/05_practice/design/14_being_wrong_humble_pivot.md`
  for the #1 Googleyness signal (Datavidhya 2026 verbatim);
  `13_unclear_requirements_scoping.md` for the most-asked
  Google DE behavioral Q.

### L5 comp (2026, Datavidhya)

- Base: $195K-$240K
- Yr-1 RSU: $130K-$250K
- Yr-1 TC: $365K-$550K
- Negotiation leverage: competing Meta/Apple offers
  (per Datavidhya 2026).

See `how_to_get_the_interview/compensation/04_comp_benchmarking.md`
for the full negotiation scripts.

---

## 1. Meta (Facebook)

**Typical loop.** Recruiter screen → Technical phone screen (45 min, SQL + 1 easy/medium coding) → Onsite (5 rounds over 1-2 days: SQL, Coding, System design, Data modeling, Pipeline design, Behavioral + Bar-raiser, Hiring manager). The bar-raiser round is the most distinctive part of Meta's loop — a senior Meta engineer from outside the hiring team is brought in to provide an independent "raise the bar" vote. The bar-raiser is empowered to veto hires and is specifically trained to detect inflated stories and weak technical depth.

**What makes them different.** "Move fast" is not just a poster on the wall — it shows up in the loop. Meta's system design rounds are often **NLQ-style** ("here's a product question, design a system that answers it in under 200ms"). They care less about a clean whiteboard diagram and more about whether you can scope a problem, ask the right clarifying questions, and produce a working design in 45 minutes. Values-based behavioral is real: every behavioral question will get explicitly mapped to a Meta value (Move Fast, Be Bold, Focus on Long-Term Impact, Be Open, Build Social Value). The SQL bar is high — expect window functions, recursive CTEs, and "compute this metric for the 7-day rolling window" questions.

**What they test.** SQL fluency under time pressure; clean, testable code (not just correct, but readable); modeling decisions (grain, SCD choice, fact vs dimension); and whether your behavioral stories are specific and own the impact rather than describing the team's work.

**What to study from this course.**
- `sql_interviews/` — 98 lessons, 59 graded problems. Focus on the `06_window_functions/`, `08_medium_practice/`, and `09_hard_practice/` modules. Meta's phone screen regularly hits `DENSE_RANK`, self-joins, and retention-cohort queries.
- `coding_interviews/` — 118 lessons, 293 tests. Practice the medium-difficulty array, hash-table, and graph problems. Meta's onsite coding is LeetCode-medium-hard.
- `behavioral_interviews/` — Module 04 has a full Meta mock interview. Map your stories to the 5 values before your onsite.
- `system_design/` — focus on the discussion-style problems in `00_overview/` and the "design a metric / design an experimentation platform" lessons.
- `data_modeling/` — the `03_high_level_diagrams/` module has Instagram and other Meta-flavored schemas.

**Common failure modes at Meta.**
1. **Blowing the bar-raiser round** by telling generic stories. The bar-raiser is *trained* to spot recycled STAR answers. Use real numbers, real trade-offs, and a real lesson.
2. **Spending 20 of 45 minutes on a perfect SQL solution** when the interviewer wanted to see you ask clarifying questions about edge cases first.
3. **Designing a system that "moves fast" without considering reliability** — Meta's production stack punishes flakiness, and your design must mention monitoring and rollback even if not asked.

---

## 2. Google

**Typical loop.** Recruiter screen → Phone screen (45 min, 1 coding problem on Google Docs) → Onsite (5 rounds: Coding ×2, System design, Behavioral/LPs, Googliness). Total ~4 weeks. The Googliness round is a separate dedicated interview with a trained interviewer — it is not folded into the behavioral round. Google uses a structured rubric called the **Hiring Committee** for every full-time hire above L4, which is why calibration against the LPs is so strict.

**What makes them different.** Google has the most **structured** behavioral rubric of any company. Every story you tell will be graded against four LPs: **Googleyness & Leadership**, **Role-Related Knowledge**, and **Thinker-Doer** (the latter is often phrased as "Emerging Leader" or "Problem Solver/Doer"). The system design round uses a "Google Cloud Architecture" (GCA) framing — they want to hear trade-offs across GCP services, not a generic system. The coding bar is also the highest: expect two LeetCode-medium or one medium-hard problem, with a strong expectation that you'll think out loud and test your own code.

**What they test.** Problem decomposition under time pressure; trade-off reasoning (not just "I'll use Bigtable" — *why* Bigtable over Spanner here?); LP-aligned storytelling (especially the "Googliness" round, which is its own interview, not a behavioral aside); and the ability to write production-quality code on a Google Doc without an IDE.

**What to study from this course.**
- `coding_interviews/` — focus on `04_arrays/`, `08_graphs/`, `09_trees/`, `14_dp/`. Google's coding is the most demanding of the seven; aim for 25-30 problems at medium-hard.
- `system_design/` — Google's system design interviews reward breadth. The 39 services in `01_url_shortener/ .. 39_reddit_homepage/` cover most patterns. Also study the `99_appendix/` concept lessons.
- `behavioral_interviews/` — Module 04 includes a full Google mock interview. Map every story to a specific LP before your onsite.
- `sql_interviews/` — Google DE loops include at least one SQL round. Practice `07_easy_practice/` and `08_medium_practice/`.

**Common failure modes at Google.**
1. **Failing the Googliness round by treating it as a "fun" interview** — it has its own calibrated rubric and is just as graded as the coding rounds.
2. **Designing systems that ignore Google's actual stack** — interviewers want to hear you reason about Spanner vs Bigtable vs Pub/Sub, not just generic Kafka.
3. **Coding without testing your own work** — Google's rubric explicitly scores "did the candidate validate their solution with example inputs?" Run through 2-3 traced examples before declaring done.

---

## 3. Stripe

**Typical loop.** Recruiter screen → Take-home (sometimes; 2-4 hour written exercise, often a small system design + SQL + code combo) OR phone screen (coding) → Onsite (4 rounds: Coding, System design, Customer-focused behavioral, Stripe-specific values). Total ~3 weeks. The take-home, when present, is the most distinctive part — it's graded carefully and is your first real signal.

**What makes them different.** Stripe's culture is "**customer-first, engineers who care about correctness**." The interview will probe whether you've thought about *correctness, idempotency, money handling, and the API contract* — not just throughput. Their system design rounds often have an **API design** angle ("design the public API for a money-movement feature, then design the data layer behind it"). Stripe's data model is one of the deepest in fintech: payments, ledgers, multi-currency, dispute states, payouts, balance transactions, and the reconciliation between them. Expect a data modeling round even when the job description says "platform DE."

**What they test.** Correctness under edge cases (don't lose a cent); API ergonomics and consistency; modeling precision (no ambiguous grain, no leaked implementation detail into the schema); and whether your behavioral stories show **judgment about user impact**, not just "I shipped this fast."

**What to study from this course.**
- `coding_interviews/` — focus on correctness, not speed. Practice writing tests for your solutions; Stripe values TDD-flavored thinking.
- `system_design/` — the `99_appendix/` lessons on consistency, idempotency, and exactly-once semantics are directly relevant to payments.
- `behavioral_interviews/` — Module 03 has the "5 story categories" workshop; pick stories that show stakeholder empathy and correctness advocacy.
- `data_modeling/` — `03_high_level_diagrams/` and `05_fact_modeling/` (the 4 fact table types) — Stripe-style data modeling rewards precise grain choice.

**Common failure modes at Stripe.**
1. **Writing a take-home that ships a "happy path" without testing edge cases** — the graders look for `null` handling, retries, and idempotency keys.
2. **Designing a system that loses data on retries** — Stripe is a payments company; if your design can double-charge or drop a charge, you fail.
3. **Treating behavioral as optional** — the customer-first value is graded as rigorously as the technical rounds.

---

## 4. Netflix

**Typical loop.** Recruiter screen → Hiring manager phone (45-60 min, design discussion) → Onsite (4 rounds: System design, Coding, Behavioral "highly effective" × 2-3). Total ~3 weeks. Senior+ roles only — Netflix generally does not hire L3/L4 DEs externally; if you get a Netflix interview, expect a Staff- or Senior-level bar.

**What makes them different.** Netflix's culture deck is the actual culture. The famous lines — **"no process, no rules, no vacation policy"** — show up in the interview as **"highly effective" calibration**: interviewers are looking for self-directed judgment, not process compliance. There is **no whiteboard** — system design is a discussion, often in a conference room with no marker. Behavioral is *the* differentiator: 2-3 of your 4 onsite rounds will probe whether you're the kind of person who operates well in a high-autonomy environment. Senior+ roles at Netflix carry explicit expectations: you've led ambiguous projects, you've set direction without a manager telling you what to do, and you've raised the bar on others around you.

**What they test.** Senior+ judgment under ambiguity; design depth (Netflix's data platform serves some of the largest real-time workloads in streaming); behavioral fit with the "highly effective" rubric; and the ability to disagree-and-commit in a room where everyone is senior.

**What to study from this course.**
- `behavioral_interviews/` — this is the single most important track for Netflix. The Module 04 Netflix mock is calibrated for this exact loop. Mine 10-15 stories; cross-reference them against the 5 story categories in Module 03.
- `system_design/` — focus on large-scale real-time and near-real-time designs (clickstream pipelines, A/B test data infra, content recommendation data). `01_url_shortener/` .. `39_reddit_homepage/` cover most patterns; pick 5-6 that map to streaming data.
- `coding_interviews/` — expect 1-2 medium LeetCode problems. Less volume than Google/Meta; correctness and senior-level trade-off discussion matter more.

**Common failure modes at Netflix.**
1. **Performing "process"** — saying "I rallied stakeholders" or "I drove alignment" is Netflix-antipattern. They want "I noticed X, I decided Y, I told my manager after." Reorder your stories.
2. **Designing for the median case** — Netflix interviewers probe edge cases (network partition, regional outage, schema drift mid-flight). Show that you think about failure modes naturally.
3. **Underpreparing behavioral** because the loop feels "technical." Behavioral is 50-60% of the signal at Netflix.

---

## 5. Airbnb

**Typical loop.** Recruiter screen → Phone screen (45 min, 1 coding problem) → Onsite (4 rounds: Coding, System design, Product/cross-functional, Behavioral). Total ~3 weeks. The **product/cross-functional round** is the most distinctive part of Airbnb's loop — it is a system design or design discussion interview where the interviewer (often a PM or a cross-functional partner) probes how you think about the *user* impact of your technical decisions.

**What makes them different.** "**Belong anywhere**" is a customer-centric value, and the product/cross-functional round is where it shows up. Airbnb's system design rounds are asked with a **product lens** — the interviewer will care about latency for the end user, about how the design supports a feature like "list your home in 3 minutes," about the data model that lets a host see their earnings. The coding bar is solid-medium (not Meta-hard, not Netflix-staff). The behavioral round is grounded in Airbnb's values (Champion the Mission, Be a Host, etc.) but is less ruthlessly calibrated than Netflix's "highly effective" framework.

**What they test.** Customer empathy expressed through technical decisions; product sense in system design (the interviewer will ask "what if the user is on 3G?" or "how does this design help a new host?"); clean medium LeetCode coding; and stakeholder-management stories.

**What to study from this course.**
- `coding_interviews/` — focus on `04_arrays/`, `05_hash_tables/`, `07_strings/`, `09_trees/`. Airbnb's coding is medium-difficulty, often 1 medium LeetCode with a follow-up.
- `system_design/` — pick problems that have a clear user-facing surface (URL shortener, Instagram, Yelp, Uber). The `00_overview/` and `99_appendix/` lessons are good primers.
- `behavioral_interviews/` — Module 03's "5 story categories" will help you build a story bank that maps to Airbnb's values.

**Common failure modes at Airbnb.**
1. **Designing a system with no user-facing language** — saying "I'll add a Kafka topic" instead of "the host will see updated earnings within 5 minutes" loses the product round.
2. **Telling "I shipped X" stories** without naming the user/customer who benefited.
3. **Underpreparing the cross-functional round** because the job description says "data engineer" — it's a real round with its own rubric.

---

## 6. Databricks

**Typical loop.** Recruiter screen → Technical screen (60 min: SQL + Spark/DataFrame code) → Onsite (4-5 rounds: Coding, Pipeline design with Spark/Delta, System design, Behavioral). Total ~3 weeks. Note the **technical screen is heavier than typical** — it often includes a live DataFrame/Spark transformation, not just SQL.

**What makes them different.** Databricks is a **deep technical** company; fewer behavioral rounds; the loop is heavily weighted toward pipeline and storage design. The pipeline design rounds are very specific: you'll be asked about Spark internals (shuffle, partitions, wide vs narrow transformations, broadcast joins), Delta Lake features (ACID, time travel, OPTIMIZE, Z-ORDER), Photon, Unity Catalog, and how to choose between batch and structured streaming. The system design rounds often have a lakehouse lens — design a lakehouse for a specific workload, with trade-offs about file format, partitioning, and update semantics.

**What they test.** Spark / Delta fluency; the ability to reason about partition strategy, skew, and shuffle; correctness in a write-heavy lakehouse; and solid SQL/coding fundamentals.

**What to study from this course.**
- `data_pipeline_design/` — this is the single most important track for Databricks. The 30 lessons, especially `02_storage/` (Delta Lake, lakehouse), `03_extraction/` (Spark, PySpark), `05_loading/` (bulk/streaming/upsert), and `06_performance/` (DAG/retry/monitoring), are directly relevant.
- `coding_interviews/` — focus on `04_arrays/`, `05_hash_tables/`, `08_graphs/`. Expect 1-2 medium problems.
- `sql_interviews/` — the technical screen is SQL-heavy. Practice `06_window_functions/` and `08_medium_practice/`.
- `system_design/` — focus on the lakehouse- and pipeline-flavored problems. The `99_appendix/` lessons on Parquet/Avro and OLTP/OLAP are prerequisite reading.

**Common failure modes at Databricks.**
1. **Recommending a non-lakehouse design unprompted** — Databricks lives and breathes Delta Lake; if your design ignores it, the interviewer wonders why you're interviewing there.
2. **Writing Spark code that triggers unnecessary shuffles** — interviewers will ask "what does this trigger?" Be ready to discuss narrow vs wide transformations and how to avoid shuffles (broadcast joins, repartition by key, AQE).
3. **Skipping the behavioral round because it's "only one"** — Databricks has fewer, but the one they have is graded. Don't show up with 5 stories when they need 10.

---

## 7. Snowflake

**Typical loop.** Recruiter screen → Technical phone (60 min: SQL-heavy) → Onsite (4 rounds: SQL, Coding, System design with warehouse lens, Pipeline, Behavioral). Total ~3 weeks. Loops are small — you may see the same interviewer for two adjacent rounds, so consistency matters.

**What makes them different.** Snowflake's DE interview is **the most SQL-heavy** of the seven. The technical phone screen is often a single 60-minute SQL deep dive: complex joins, window functions, query optimization, and "here's a 200-line stored procedure, find the bug" style questions. The system design rounds are explicitly **warehouse-lens**: micro-partition strategy, clustering keys, virtual warehouse sizing, separation of storage and compute, Snowpipe, dynamic tables, and the trade-offs between Snowflake and open formats (Iceberg, Delta). Behavioral is shorter than Netflix/Meta but real — Snowflake cares about customer obsession and engineering rigor.

**What they test.** SQL at the level of a database internals engineer (you don't need to know the C++ internals, but you should know *why* a query is slow); warehouse architecture fluency; pipeline design (especially ELT vs ETL, dbt-on-Snowflake, dynamic tables vs tasks); and clean coding.

**What to study from this course.**
- `sql_interviews/` — the deepest, most SQL-heavy of the seven companies. Cover every module; pay special attention to `06_window_functions/`, `08_medium_practice/`, and `09_hard_practice/`. Be ready to optimize a slow query on a whiteboard.
- `data_pipeline_design/` — focus on `02_storage/`, `05_loading/`, and `06_performance/`. The ELT vs ETL and partitioning trade-offs are Snowflake staples.
- `data_modeling/` — `03_high_level_diagrams/` and `04_dimension_design/`. Snowflake rewards precise grain and SCD discipline.
- `system_design/` — `99_appendix/` concept lessons (Parquet, OLAP) are prerequisites; pick 2-3 warehouse-shaped design problems.

**Common failure modes at Snowflake.**
1. **Writing SQL that works but doesn't scale** — "this query returns the right answer on 100 rows" is not enough; you need to discuss partition pruning, clustering, and result-set size.
2. **Designing a system that uses Snowflake like a transactional database** — the warehouse-lens interview will probe whether you understand the storage/compute separation.
3. **Skipping the behavioral round** because the loop is technical — Snowflake's loop is small, so the one behavioral round carries disproportionate signal.

---

## How to choose where to apply

The seven companies fall into three rough archetypes, and the choice between them is mostly a choice between archetypes:

**Archetype A — SQL + coding grind.** **Meta, Google.** These loops reward raw problem-solving volume. If you have 6+ weeks of prep time and your fundamentals are shaky, these are honest interviews — your prep pays off directly. The trade-off is that the loops are the most standardized, so the bar is hardest to clear without grinding 50+ LeetCode problems.

**Archetype B — Senior judgment + design.** **Netflix, Airbnb, Stripe.** These loops reward a smaller, deeper body of work. If you have 8+ years of experience, can talk fluently about a 2-year project, and prefer design discussions to whiteboard coding, this archetype fits. The trade-off is that "senior judgment" is harder to fake — you need real stories with real impact numbers.

**Archetype C — Deep technical niche.** **Databricks, Snowflake.** These loops reward specialist depth (Spark/Delta for Databricks, SQL + warehouse for Snowflake). If you have prior exposure to one of these stacks, that's your wedge. The trade-off is that the loops are smaller and more "in-the-weeds" — surface-level prep won't help.

**Practical decision rule.**
- If your resume already names Spark, Kafka, Airflow, dbt, Delta → prioritize **Databricks** and **Meta** (the most familiar-to-the-company signal).
- If your resume is heavy SQL + BI + modeling → prioritize **Snowflake** and **Stripe**.
- If your resume is "I built X" (leadership/architect-level) → prioritize **Netflix** and **Airbnb**.
- If you have 3+ months of prep and want to maximize offers → apply to all three archetypes; the prep effort is largely shared.

---

## Re-prioritizing mid-prep

The most common mid-prep shock is: *you've been grinding Meta-style SQL/coding for 8 weeks, and a recruiter from Google calls with an interview in 2 weeks, or your top-priority company is suddenly Netflix.* Here's the triage:

**If you have 2 weeks until a Google interview after Meta prep:**
- Reweight 60% of your remaining time to `coding_interviews/` (you need 25-30 medium-hard problems at speed, not the 50+ you'd do for full Google prep).
- Spend 1 day on `system_design/99_appendix/` to refresh GCP-shaped trade-offs (Bigtable vs Spanner, Pub/Sub, GCS).
- Spend 1 day on `behavioral_interviews/` Module 02 and Module 04's Google mock — you need LP-aligned stories, not generic ones.
- Don't try to learn new content; you don't have time. Maximize signal on what you already know.

**If you have 2 weeks until a Netflix interview after Meta prep:**
- The flip is harder: Netflix's bar is "senior judgment," not "raw problem-solving." Spend 4-5 of the 10 days on `behavioral_interviews/` — re-mine your stories for "I decided X, I told my manager after" framing.
- Spend 2 days on `system_design/`, picking 5 streaming-data problems (clickstream, A/B test infra, recommendation data) and being able to discuss them conversationally.
- Spend 1 day on `coding_interviews/` for warm-up; Netflix coding is lighter than Meta's.

**If you have 2 weeks until a Databricks interview after generalist prep:**
- Spend 4-5 days on `data_pipeline_design/`, especially `02_storage/`, `03_extraction/`, `05_loading/`, and `06_performance/`. The Spark/Delta vocabulary is the single biggest unlock.
- Spend 2 days on `sql_interviews/` (window functions, hard practice).
- Spend 1 day on `system_design/` picking 3 lakehouse-flavored problems.

**If you have 2 weeks until a Snowflake interview after generalist prep:**
- Spend 5-6 days on `sql_interviews/` (every module, especially `06_window_functions/`, `08_medium_practice/`, `09_hard_practice/`).
- Spend 2 days on `data_pipeline_design/02_storage/` and `data_modeling/03_high_level_diagrams/`.
- Spend 1 day on `system_design/99_appendix/` for Parquet/OLAP/partitioning.

**Universal re-prioritization rules.**
1. **Don't restart from zero.** The prep effort across companies is ~70% shared. Reweight, don't restart.
2. **Preserve behavioral prep.** It's the slowest to build (you need real stories) and the fastest to forget. Keep 1-2 hours/week on it no matter what.
3. **Do one mock interview in the new format** in the last 48 hours. `behavioral_interviews/04_mock_interviews_and_analyses/` has Meta, Google, Netflix, and EM mocks. Switch to the right one.

---

*Author: Prem Vishnoi <pvishnoi@avilx.com>*
