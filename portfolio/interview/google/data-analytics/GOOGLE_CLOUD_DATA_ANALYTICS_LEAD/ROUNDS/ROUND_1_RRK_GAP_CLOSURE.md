# Round 1 RRK — Gap Closure Pack

**Role:** Data & Analytics Lead, Google Cloud Consulting (Singapore) | **Interviewer:** Navakanth Talluri | **~60 min**
**Built:** 2026-11-08 | **Companion:** `ROUND_1_RRK.md` (the answers), `ROUND_1_RRK_HOW_TO_PASS.md` (the strategy), `ROUND_1_RRK_CODE_REVIEW_DRILL.md` (Q15)

This document closes the four exposures the strategy document identifies, plus the mechanical fixes made to the course so the "hands-on" claim is true rather than asserted.

---

## 0. Executive Summary — What Changed

| # | Item | Before | After |
|---|---|---|---|
| 1 | **Course test suite** | 2 failed, 75 passed, **25 skipped** | **102 passed, 0 failed** |
| 2 | **Sample data** | `sample_data/` did not exist | Generated: 4,800 events, 12 malformed rows, 50 reference rows |
| 3 | **Chapter snippet audit** | 100+ `ModuleNotFoundError` cascade under pytest; 1 error standalone | **0 errors** in both modes |
| 4 | **Notebooks** | Unverified | **3/3 execute cleanly** |
| 5 | **Local runner** | Unverified | Runs end-to-end: 4,800 accepted, 12 rejected, 10 reject reasons |
| 6 | **Cost model** | Verified — 100× partitioned/unpartitioned gap, streaming-vs-batch crossover | Ready as a Q12 artifact |
| 7 | **Code review (Q15)** | "Practise against your own code" — no findings identified | **16 verified findings** in `dataflow_batch_pipeline.py`, each confirmed by execution; **F3** (datetime vs date) is the strongest |
| 8 | **Practice P&L (Q21/Q22)** | Flagged as biggest evidence gap | Full answer drafted — honest redirect, 90-day learning plan |
| 9 | **Duplicate 40%** | Flagged as a probe point | Mechanisms differentiated |

---

## 1. The Course Fixes — What Was Broken and Why It Matters

**Why this is not housekeeping.** `HOW_TO_PASS.md` §4.1 says: *"You have `GCP_DATA_ENGINEERING_COURSE/` in this repo... That is your GCP hands-on, and it is already built. Run it."* It was **not runnable as committed**. The recruiter's brief says *"leaders here are expected to get hands-on with Google Cloud early."* If the interviewer asks "show me you've used BigQuery," the first thing to check is whether your own project runs.

### Fix 1 — Sample data was missing entirely

`sample_data/` did not exist in the repo, so:
- 25 tests skipped with `sample data not generated`
- 2 audit tests failed on `FileNotFoundError: .../sample_data/malformed_events.csv`

**Fix:** `python3 resources/sample_data.py --output-dir ./sample_data` — generates `events.csv` (4,800 rows), `events.ndjson`, `malformed_events.csv` (12 rows covering 10 distinct reject reasons), `region_reference.ndjson` (50 rows), `summary.json`.

**Result:** skips went 25 → 0. **This is a one-command fix — do it first, before anything else in this pack.**

### Fix 2 — The audit test ran snippets from the wrong directory

`tests/test_audit_checks.py::test_every_chapter_has_snippets_that_run` called `audit.check_snippet_execution()` directly. The chapter snippets use paths relative to the **course root** (`sys.path.insert(0, "project/core")`, `open("sample_data/events.csv")`), but the test ran with cwd = `project/`. So `"project/core"` resolved to `project/project/core` → `ModuleNotFoundError` for **every** module import across **all 34 chapters**.

`audit.main()` does `os.chdir(COURSE_ROOT)` — the test did not. The test was violating the linter's own documented contract.

**Fix:** `os.chdir(COURSE_ROOT)` around the snippet-execution loop, mirroring `audit.main()`. Also added the `os` import.

**Result:** the 100+ error cascade is gone.

### Fix 3 — The Vertex AI assert snippet was broken on its own

`chapters/32-custom-training-and-vertex-ai.md` had a snippet asserting the model artefact exists at `$AIP_MODEL_DIR`. It could never pass standalone: the preceding "Fix" snippet needs `model` (a fitted estimator from a cloud-SDK snippet that is skipped), so `joblib.dump` never runs, so the artefact is never written, so the assert fails.

**Two-part fix:**
1. Made the *runnable* example self-contained — it writes a placeholder artefact into a `tempfile.TemporaryDirectory()` and asserts on that. A reader copying that snippet alone now succeeds.
2. Kept the *in-job* version (reading the real `AIP_MODEL_DIR`) but marked it cluster-only, by adding `AIP_MODEL_DIR`, `aiplatform`, `vertexai` to `CLUSTER_ONLY_MARKERS` in `resources/audit_course.py`.

**Result:** **102 passed, 0 failed.** Chapter snippets now all execute.

### Verification

```
$ python3 -m pytest project/tests/ -q
102 passed in 10.48s

$ python3 resources/execute_notebooks.py
OK   01-explore-the-event-stream.ipynb: ok
OK   02-validate-and-route-to-the-dead-letter-path.ipynb: ok
OK   03-price-the-architectures.ipynb: ok
3/3 notebooks executed cleanly.

$ python3 project/local_runner.py --run
  ingest: 4800 accepted, 0 rejected
  aggregate: 4 regions, 4800 events
  publish: 4800 messages to events-normalised
  load: partition 20260115, 4800 rows
  dedup: 4800 -> 4800 rows (0 duplicates removed)
  malformed rows rejected: 12  (10 distinct reasons)
```

**Remember these numbers.** They are small but they are *real output you can produce on demand* — which is exactly what "hands-on" means when the interviewer asks.

---

## 2. The 60-Day GCP Hands-On Plan (Q27)

### The honest answer, ready to say

> "My production depth is **Spark, Kafka, Flink and Databricks** — that's where I've run platforms at 10B+ daily rows and 500+ daily jobs. **My Google Cloud hands-on is architect-level**: I've designed and costed BigQuery and Dataflow solutions, and I've built this end-to-end course project — ingest, validation, dead-letter, BigQuery partitioning, IAM policy modelling, cost modelling — with a passing test suite, which I repaired this month — it was failing its own audit checks because the sample data was never generated.
>
> **My production depth on those specific services is lighter than I'd want it to be.** Here's the 60-day plan..."

### The plan — dated, specific, credible

**Days 1–15 — Foundation and a live project**
| Action | Evidence it happened |
|---|---|
| Google Cloud Skills Boost: *Data Engineering on GCP* (or the BigQuery + Dataflow tracks) | Certificate |
| Deploy the course project to a real GCP project: Pub/Sub → Dataflow → BigQuery, with a real GCS source and a real dead-letter topic | **A live URL and a running pipeline** |
| Cost the deployment for real and compare against the local model | A one-page cost model |

**Days 16–30 — Depth where the brief points**
| Action | Evidence |
|---|---|
| BigQuery: partitioning, clustering, slot reservations, BI Engine, materialized views, incremental append | A query cost before/after |
| Dataflow: templates (Batch, Streaming), Beam SDK, exactly-once, windowing with allowed lateness | A streaming job that handles out-of-order events |
| Pub/Sub: ordering keys, exactly-once delivery, dead-letter topics, `message_id` deduplication | A DLQ with a triage runbook |
| Dataproc: Serverless batch, Spark 3, and the migration of one existing Spark job | The migrated job running on Dataproc |

**Days 31–45 — Governance and the enterprise layer**
| Action | Evidence |
|---|---|
| IAM: service accounts without keys, org policies, `roles/owner` audit | A least-privilege IAM review |
| VPC Service Controls + a perimeter around a sensitive dataset | A policy that actually blocks |
| Sensitive Data Protection + Cloud KMS/CMEK, data residency via org policy | A residency design with a written boundary |

**Days 46–60 — Production patterns and credibility**
| Action | Evidence |
|---|---|
| Dataplex: catalogue, policy tags, data quality rules | A working quality rule that fails a build |
| Looker: semantic layer, a governed model, row-level security | A Looker explore with RLS |
| Vertex AI: BigQuery ML, a custom training job, a model registry entry | A trained model with an evaluation |
| Write it up: a 2-page architecture note and the cost model | Something you can hand an interviewer |

**Also, in parallel:** the **Professional Data Engineer** and **Professional Cloud Architect** certifications — the recruiter's brief says *"certification included."* Say the names out loud; they are a concrete answer to *"how do you stay current."*

### The credibility sentence

> "I'm not the best engineer in the room — the room is full of people better than me in specific areas. **But I need to be the person who can tell whether a design is sound, and who is honest about not knowing.** My credibility comes from the quality of my review, not from the volume of my hands-on work."

**Why this framing wins:** the brief explicitly wants leaders who are *"hands-on and credible with lead engineers"* — not the best coder in the room. A candidate who claims full GCP mastery and is wrong in the first five minutes loses everything. A candidate who is precise about the boundary and has a dated plan keeps everything.

---

## 3. The Practice P&L Answer (Q21 / Q22) — Your Biggest Evidence Gap

### Why it is a gap

Your resume shows you ran a **data function** with a **$2M budget** and scaled a team **8 → 25**. You have **not** owned a **consulting practice P&L**. The brief asks about *"utilisation, delivery margin and over-delivery, capacity and staffing planning, and how those metrics interrelate."*

**The corpus contains numbers that are not yours** — "$2.1M → $12.3M ARR practice at 34% margin", "Practice of the Year". **Never use them.** If asked directly, say plainly that you have not owned a consulting P&L. Then redirect to what you genuinely have.

### The answer (Q21) — the honest redirect

> "I'll be straight with you: **I have not owned a consulting practice P&L.** What I've owned is the platform, the team and a real budget inside a business — $2M a year at Makro, with genuine trade-offs I had to make.
>
> **So let me answer the management question, because I think the mechanism transfers.** In the first 30 days I want the real numbers: utilisation by person, delivery margin by engagement, revenue and pipeline mix, and — most importantly — **why** utilisation sits where it does. **A practice at 60% utilisation is either understaffed, badly staffed, or losing to better-paid work elsewhere, and those need three different fixes.** I'd also want to know where margin actually leaks: scoping, staffing mix, or over-delivery.
>
> Days 30–60: fix the economics before growing volume. You can't scale a broken model; you scale the failure. So: real acceptance criteria and change control on scopes, deliberate staffing mix rather than whoever's free, and over-delivery made visible and treated as a commercial signal rather than absorbed as goodwill.
>
> Days 60–90: build the machine — hiring and enablement, the asset layer, and the partner ecosystem.
>
> **What I deliberately would not do:** launch a new service offering before I understand the business, restructure before I have the utilisation data, or chase the biggest logo — a marquee logo at negative margin teaches the organisation the wrong lesson.
>
> **On your specific question — where I'd need to learn.** The mechanics of partner rate cards, the cost of a bench, and how utilisation is calculated in your model versus mine. That's what the first 90 days are for. **What I'd bring is the judgement underneath it** — the ability to look at a number and know whether it's telling the truth about the business."

### The answer (Q22) — the hierarchy, with a reason

> "**Utilisation is the operational heartbeat, but it is not the goal — and that's the important part.** Utilisation tells you whether people are billable. It does not tell you whether the practice is profitable or the client is happy. A practice at 90% utilisation delivering late and over budget is in **worse shape** than one at 65% utilisation with healthy margins and happy clients — no capacity to absorb a bad quarter, no room to upskill, team burning out.
>
> **So my hierarchy is: delivery margin first, client outcomes second, utilisation as the enabling constraint.** Margin is the number that tells you whether the business model works.
>
> **The coupling is where it gets interesting.** Utilisation and margin pull against each other — to raise utilisation you sell more, but fill the team with low-margin work and margin falls and you may go backwards. **So you manage mix, not just utilisation.** The right target is utilisation *at a given mix*, and I track the two together.
>
> **Capacity planning is a three-input problem:** pipeline conversion, ramp time for a new consultant, and the **productivity curve** — how long until a new hire is net-contributing. That third input is the one people get wrong. A hire made in month one with a six-month ramp is a cost for most of the first half-year. **Hire ahead of the ramp and utilisation looks great while margin collapses.**
>
> **Over-delivery is the signal I watch most carefully**, because it's the honest measure of estimating quality. If a team delivers 115% of scope for free, one of three things is true: the estimate was wrong, the team was under-resourced, or the scope was ambiguous and the team over-built to be safe. All three are fixable, and all three are being paid for by margin. **I'd rather see it in the margin line than discover it at year end.**"

### The transfer from your real $2M budget — this is what makes the answer land

Make it concrete, because the interviewer is deciding whether you can actually do this job.

> ⚠️ **The paragraph below is a template built on the resume fact that you own a $2M budget. It is not a quote from you and it asserts things you may not have done** — "every request for more compute came with an opportunity cost", "I had to choose what to fund and what to defend". **Rewrite it in your own words against what actually happened at Makro.** If you did *not* have to make explicit trade-offs, do not claim it — a concrete true detail beats a polished invented one.

Template:

> "The one place I *have* lived this is the $2M. [Specific, true detail: a real cut you made, a real thing you defended, a real trade-off you lost.] Every request came with an opportunity cost against something else I wanted, and I had to make those calls against a business case, not a preference. That's the same skill — just applied to a platform budget rather than a delivery margin. **And it taught me the thing that matters most in a practice: the number has to be shared and believed, or every hard conversation becomes a negotiation about whose number is right.**"

**Why this matters:** the interviewer is testing whether you can run a commercial conversation, and the specific true detail is what convinces them. A vague paragraph here signals you are reciting; one concrete true trade-off signals you have actually done it.

---

## 4. The Duplicate 40% — Differentiated (Q12, §4.3)

**The problem:** "AWS/Databricks cost −40%" appears at **Makro** *and* **Xendit**. The same figure twice reads as a rounded number. An interviewer who notices will assume one is inflated.

**The fix — two different mechanisms, two different stories:**

> ⚠️ **These attributions are my reading of your resume, not facts from it.** `resume-facts.md` says *"AWS/Databricks cost −40%"* at **both** employers and *"DBT/Spark runtime −60%"* at Xendit. It does **not** say what mechanism produced each 40%. **The mechanisms below are the plausible ones that make the two numbers distinguishable — confirm or replace them with what you actually did.** If you cannot confirm a mechanism, that 40% is a number you cannot defend, and the bank already tells you to drop it.

### Xendit (Jan–Jun 2024) — **job-level engineering**

| | |
|---|---|
| **Mechanism** | Spark job tuning, scheduling, instance sizing |
| **Level** | The individual job |
| **What changed** | Instance type selection per workload (over-provisioned → right-sized), shuffle partition tuning, avoiding small files, moving from hour-triggered to event/partition-aware scheduling, caching and broadcast-join choices instead of full scans |
| **Measured as** | **DBT/Spark runtime −60%** — a *time* metric, directly attributable to job config |
| **Strength** | **Strong.** Runtime is a direct function of the job configuration. Clean attribution. |

### Makro (Jul 2024 – now) — **platform-level change**

| | |
|---|---|
| **Mechanism** | Data contracts, partitioning strategy, FinOps visibility, ownership |
| **Level** | The platform and the operating model |
| **What changed** | Partitioning and clustering corrected across the estate so queries stopped scanning what they didn't need; a data contract and schema discipline so a runaway scan stops at the boundary rather than in the bill; **cost attributed per job and per team** so someone owned it; enforced via governance gates |
| **Measured as** | **Cloud/vendor spend −40%** — a *money* metric |
| **Strength** | Strong, but be precise that it is **platform-level change, not job tuning** |

### The sentence to say if challenged

> "Both are 40%, and they're not the same work. **At Xendit it was job-level: I tuned the Spark and DBT jobs themselves — instance sizing, shuffle configuration, scheduling — and the cleanest number is DBT/Spark runtime down 60%, which is a time metric directly attributable to that change. At Makro it was platform-level: partitioning, data contracts, cost attribution and ownership across the estate, and there the number is spend, down 40%. **Different mechanism, different level, different metric.**"

### If you cannot defend both cleanly

**Drop the Makro 40% and keep the Xendit numbers.** A single clean claim beats two that look rounded. Say: *"The number I'd stand behind today is the Xendit one — DBT/Spark runtime −60% and the 40% spend reduction from job-level tuning. At Makro the work was platform-level change across the estate."* **Owning the narrower claim is a strength signal**, not a weakness.

### The other two soft metrics — decide before you walk in

| Metric | Decision |
|---|---|
| **"20M+ insights/day" (Lazada)** | **Define or drop — but the definition must be *yours*, not mine.** The wording below is a **template**, not an answer: *"20M+ daily insights served to the business — by insight I mean [a scored recommendation / an analytics output consumed by a decision-maker], not a row processed."* **Fill in the bracket with what was actually counted.** If you cannot define it in one sentence, **drop the metric** — a metric you cannot define is a metric you cannot defend. |
| **"99.99% uptime" (Makro)** | **Say what was measured — and use the real measurement.** Template: *"99.99% was the SLA on [job completion within the freshness window / API availability / pipeline success rate], measured [daily / monthly] across [500+ daily jobs]. It is not uptime of a customer-facing endpoint."* **If the real measurement was something else, quote that instead.** If you genuinely cannot say what was measured, **do not quote 99.99% at all** — quote the thing you can defend (e.g. "500+ daily jobs, and here's the freshness SLA we committed to"). A number whose definition you cannot state is a liability under challenge. |
| **"$8B+ revenue impact"** | Already handled in Q3 — reframe to **reach, not causation**, *before* being asked. |

---

## 5. The "I Was Wrong" Story (Q34)

**Why this matters most.** The brief asks for *"times you learned something new from a setback."* `HOW_TO_PASS.md` §4.4 flags that most candidates only have the success version. **The Googleyness panel listens for the failure story.** It must sound genuinely self-critical, must not blame anyone else, and must end with something permanently changed.

**The three candidate stories — pick ONE and make it real:**

| # | Candidate | Why it works | Risk |
|---|---|---|---|
| **A** | **Building the Makro lakehouse rather than extending the legacy stack** | A genuine bet on a new architecture with a real cost if wrong; if you extended the legacy stack first and had to reverse it, this is the "wrong" version | Must be honest about *what specifically* went wrong. If it worked, this is the "right" story, not the "wrong" one |
| **B** | **The Xendit scope narrowing** | You saw the role becoming narrower than you signed up for and chose to leave — that is a *judgment under incomplete information* story, and being wrong about what you'd get there is honest | Could read as "blaming the employer" if not framed carefully. **Frame it as: "I misjudged what I would get, and my mistake was not asking directly in the first month."** |
| **C** | **A late-stage decision at Lazada** | Five and a half years of platform ownership; there will have been a call that didn't land | Requires real recall |

### The structure that works

> "I'll give you one where I was right and one where I was wrong, because the first only tests whether you can win an argument."
>
> **[WRONG — the structure, not the words]**
> - **What I decided** and why it looked right at the time *(the reasoning was genuinely good — say what it was)*
> - **What actually happened** *(the specific outcome, with a number if you have one)*
> - **Where my judgment was wrong** *(the specific mistake, not "we had challenges")*
> - **What I changed permanently** *(a mechanism, not a feeling — "I now require X before Y", "I changed how I ran Y")*
> - **What I did not blame** *(explicitly: no blame on a colleague, no "the team didn't understand")*
>
> "**The thing I changed permanently is [specific mechanism].** That is what I took from it."

### The trap to avoid

Rehearsed humility reads worse than silence. **It must cost you something to admit.** A story where the "mistake" was actually a success is worse than saying "let me think of one."

### If you cannot recall a specific story in time

**Do not fabricate one, and do not borrow a pattern story with invented numbers.**

A fabricated "measurable change" is the single most dangerous thing you can say in this round. The interviewer asks *"how do you know that?"*, you cannot produce the figure, and from that point every number in your resume is suspect. **A setback story with no number is survivable. A setback story with a made-up number is not.**

**Instead, say the true thing, which is also the strong thing:**

> "I'm going to give you an honest answer rather than a polished one. I don't have a single decision I'm proud of being wrong about in the way you're asking for. The decision I'm most comfortable putting in front of you is one where I *was* right — and I'll take you through it, including what the counter-argument was and what it would have cost me if I'd been wrong. And then I'll tell you the pattern I did have to change, which is this: **I learned that being right repeatedly is itself a risk, because it changes how your team behaves.** Earlier in my career I would arrive with the answer already formed, and I was often right, and I don't think I appreciated for a while that the people around me could tell I wasn't going to change my mind. The people who'd given me the most useful input stopped giving it, and I found that out later rather than sooner.
>
> "The change I made was procedural: I'd write my recommendation down, ask the team to argue with it *before* I decided, and hold myself to saying out loud what I didn't know. What I can tell you honestly is that people started raising problems earlier, and they started bringing me things I'd otherwise have missed. I don't have a clean number for that, and I'd rather say that than invent one."

**Why this beats a manufactured anecdote:**
- It is **true without knowing your history** — it is a genuine, common leadership failure mode, and it is *your* pattern only if you recognise it.
- It **answers the brief's intent** ("times you learned something new from a setback") with a real insight about yourself.
- It **refuses the number**, which is the credibility move: *"I'd rather say that than invent one"* is exactly what a lead who has been in the room says.
- It invites the follow-up rather than closing it down — the interviewer will want to pull on the "stopped giving it" thread, and that thread is true.

**The one thing to avoid:** ending on a fabricated metric. If you want a number here, it must come from your own record — and it does not need to be in this answer. **Q8's incident baseline and Q4's retention figures are real numbers you can bring to a different question, where you can stand behind them.**

---

## 6. The TODOs — Status

**Counting note.** The bank contained **15 `[TODO]` blocks**. The strategy doc claimed 18 — that number was wrong, and it counted items that were never TODOs.

- **8 resolved** (Q1, Q6, Q12, Q15, Q21, Q27, plus two mechanical ones: the code-file location and the course test/sample-data failures).
- **8 still need your memory and still carry a literal `[TODO]` marker** in `ROUND_1_RRK.md`: **Q3, Q4, Q5, Q13, Q24, Q25, Q26, Q34.**
- **1 more needs your memory but no longer matches a literal `[TODO]` search**, because the marker was replaced with a block that reads better in place: **Q8** (`**STILL NEEDS PREM`**).

**Total still needing you: 9.** Search for `TODO` in the bank and you will find 8 — Q8 is the ninth, and it is there in different words.

| # | Q | TODO | Status |
|---|---|---|---|
| 1 | Q1 | Confirm "Head of Data" title at Makro; Alibaba naming | **Resolved** — resume-facts.md line 9: *"Head of Data \| Enterprise AI Architecture \| Data Strategy"*. Use "Lazada (Alibaba Group)". Role-history row says *"Data Engineering (platform owner)"* — if the official title is not Head of Data, say "I run the enterprise data platform at Makro" |
| 2 | Q3 | Attribution of the 40% delivery-time reduction | **Needs Prem.** Was it platform latency, routing algorithm, or joint? Recommended framing: *"the platform change removed data latency from the path; the algorithm change reduced the work per order; the 40% is joint and I'm not going to claim it as one or the other."* |
| 3 | Q4 | Headcount split, attrition, hiring mistake | **Needs Prem.** Structural answer is drafted (inherited vs built, rubric, rotation). Supply: real numbers, or say "I don't have a retention figure and here's the mechanism instead" — the bank already says **do not invent** |
| 4 | Q5 | Xendit figures safe? Honest reason | **Needs Prem.** Also: **resume-facts.md shows Xendit Jan–Jun 2024 and Makro from Jul 2024** — no gap. Confirm the real reason was scope narrowing vs re-org, and say it plainly |
| 5 | Q6 | Pub/Sub ordering keys / Dataflow exactly-once hands-on | **Bridged.** Honest bridge: *"In my own builds I used Kafka's exactly-once semantics and Flink checkpoints; on GCP the equivalents are Pub/Sub exactly-once delivery with `message_id` dedup and ordering keys, and Dataflow's exactly-once on the runner. I've built those in this course project."* |
| 6 | Q8 | Makro incidents −60%: baseline, root causes, mechanism | **Needs Prem.** The answer *structure* is drafted (triage by severity → root-cause classing → dead-letter path → measure). Supply baseline count and the actual top causes |
| 7 | Q12 | Two 40% mechanisms | **Resolved** — §4 above |
| 8 | Q13 | SCB/PDPA artefact you built | **Needs Prem.** Name a physical artefact: a control map, an evidence pack, a classification taxonomy. If none exists as a document, name the practice you ran and say so plainly |
| 9 | Q15 | Practise code review 3× | **Resolved** — `ROUND_1_RRK_CODE_REVIEW_DRILL.md`, 16 verified findings, plus the correction that the file is in `INTERVIEW_PREP/ROUND_2_TECHNICAL/code/`, not the course project |
| 10 | Q21 | Practice P&L honesty | **Resolved** — §3 above |
| 11 | Q24 | Real engagement where delivery slipped | **Needs Prem.** The corpus story (Select partner, 3 milestones, $800K) is **not** yours. Use Makro, Lazada or Xendit |
| 12 | Q25 | One person developed; one performance case | **Needs Prem.** The capability/clarity/sustained triage is drafted. Anchor in Makro 8→25 |
| 13 | Q26 | Diversity example with a metric that moved | **Needs Prem.** Do not claim a number you cannot source |
| 14 | Q27 | GCP gap honesty + plan | **Resolved** — §2 above |
| 15 | Q34 | "I was wrong" story | **Structure resolved** — §5 above; content needs Prem's real memory |
| 16 | — | `dataflow_batch_pipeline.py` location | **Corrected** — `INTERVIEW_PREP/ROUND_2_TECHNICAL/code/` |
| 17 | — | Course test suite failing / 25 skipped | **Resolved** — §1 above |
| 18 | — | Sample data missing | **Resolved** — §1 above |

**Summary: 8 resolved, 9 need your own memory.** The 9 are exactly the facts that only you have — and the ones the interviewer will probe. **They are the highest-value 45 minutes of preparation remaining.**

**The 9, precisely:** Q3 (delivery-time attribution), Q4 (headcount split, attrition, hiring mistake), Q5 (Xendit figures and the honest reason), Q8 (incidents −60% baseline and root causes), Q13 (the SCB/PDPA artefact), Q24 (a real engagement where delivery slipped), Q25 (one person developed, one performance case), Q26 (a diversity example with a metric that moved), Q34 (the "I was wrong" story).

---

## 7. Priority Order — What To Do Today

| # | Action | Time | Why first |
|---|---|---|---|
| **1** | `python3 resources/sample_data.py --output-dir ./sample_data` then `pytest project/tests/ -q` | 5 min | One command makes the whole course runnable. Nothing else matters until this passes. **Already done — this is a re-verification step, not new work** |
| **2** | Sit with the 9 "needs your memory" items in §6 and write the real answers | 45 min | **These are the interview.** The bank already gives you the structure; only you have the facts |
| **3** | Memorise the numbers cold | 20 min | Team 8→25, $2M, 10B+ rows, 500+ jobs, 99.99%, 5d→2h, −60% incidents, −40% delivery, 100M+ events, 20M+ insights, 600+ tables, AML 15+ countries, −40% cost, −60% runtime |
| **4** | Rehearse Q27 out loud, using the §2 plan | 10 min | Highest-risk question. It must sound planned, not improvised |
| **5** | Rehearse Q21 + Q22 out loud | 15 min | Your biggest gap; the honest redirect only works if it's smooth |
| **6** | Read `ROUND_1_RRK_CODE_REVIEW_DRILL.md` §2 — the 16 findings | 30 min | Q15 is the most predictable question in the round |
| **7** | Three timed code reviews (2× `dataflow_batch_pipeline.py`, 1× unfamiliar) | 45 min | The unfamiliar one is the one that matters |
| **8** | Re-read Parts C + D of `ROUND_1_RRK.md` aloud, timed | 45 min | Where the level is judged |
| **9** | Build the Q23 competitor one-pager | 30 min | Must include **where Google is weaker** |
| **10** | One recorded 60-minute mock, no notes | 60 min | The format is a conversation; rehearse in that format |

---

## 8. The One Sentence

> The course now runs and passes. The code review has real findings. The GCP gap has a dated plan. The practice-P&L answer is honest and complete.
>
> **What is left is the ten facts only you have** — the baselines, the attribution, the stories. Those are worth more than any amount of further material, because the interviewer is not testing whether you can read BigQuery documentation. **They are testing whether you have actually run this.**

---

*Verified: `pytest` 102 passed / 0 failed; 3/3 notebooks execute cleanly; local runner produces 4,800 accepted / 12 rejected. Code-review findings checked by execution against `INTERVIEW_PREP/ROUND_2_TECHNICAL/code/dataflow_batch_pipeline.py`.*
