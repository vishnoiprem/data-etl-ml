# RRK Study Index and Open Items

**Role:** Data & Analytics Lead, Google Cloud Consulting (Singapore)
**Purpose:** one page that says what exists, what order to use it, and what only you can fill in. Last updated 2026-11-09.

> **Public repo.** Do not type real numbers, employer names or customer names into this file. Keep your filled-in stories in a private, gitignored location (check with `git check-ignore -v --no-index <path>`).

---

## 1. Use in this order

| # | File | Use it for | Time |
|---|---|---|---|
| 1 | `ROUND_1_RRK_HOW_TO_PASS.md` | What is scored, pass and fail signals | 20 min |
| 2 | `ROUND_1_RRK_TOPIC_DEEP_DIVE.md` | Technology topics at 15-year depth, correctness playbook, competitors | 2 h |
| 3 | `ROUND_1_RRK.md` | The 35-question bank (Parts A to E) | 3 h |
| 4 | `ROUND_1_RRK_MOCK_LAB.ipynb` | Run the code: bug review, late data, write-audit-publish, reconciliation, SQL, FinOps | 1.5 h |
| 5 | `ROUND_1_RRK_CODE_REVIEW_DRILL.md` | Six-pass review order and findings | 1 h |
| 6 | Scenario answers (below) | Model answers for each question type | 3 h |
| 7 | `ROUND_1_RRK_MOCK_10.md` | Ten timed mock questions and a rubric | 2 h |
| 8 | `ROUNDS_3_TO_6_DETAILED_ANSWERS.md` | Case study, leadership, Googleyness, executive | 2 h |
| 9 | `ROUND_1_RRK_GAP_CLOSURE.md` | The 60-day GCP plan, practice P&L answer, "I was wrong" story | 1 h |

### Scenario answers (step 6)
| Topic | File |
|---|---|
| Pub/Sub to BigQuery code review | `ROUND_1_RRK_PART1_CODE_REVIEW_ANSWER.md` |
| Governance, PII, residency | `ROUND_1_RRK_GOVERNANCE_ANSWER.md` |
| People leadership | `ROUND_1_RRK_PEOPLE_LEADERSHIP_ANSWER.md` |
| Practice commercials and competitors | `ROUND_1_RRK_PRACTICE_COMMERCIAL_ANSWER.md` |
| Challenging an executive | `ROUND_1_RRK_EXECUTIVE_INFLUENCE_ANSWER.md` |
| Troubled engagement (first 72 hours) | `ROUND_1_RRK_TROUBLED_ENGAGEMENT_ANSWER.md` |
| Backfill and atomic publish | `ROUND_1_RRK_BACKFILL_ATOMIC_PUBLISH_ANSWER.md` |
| Real-time RAG design | `ROUND_1_RRK_RAG_DESIGN_ANSWER.md` |

---

## 2. Mock interview scores so far (your own answers)

| Question | Score /8 | Main lesson |
|---|---|---|
| Q1 background | 5 | Add real numbers and a "why Google" thesis, not generic reasons |
| Q1 follow-up (freshness) | 4 | Give a baseline, a result, and the measurement method |
| Q2 late data and duplicates | 7 | Strong. Add the producer-duplicate caveat and an owner |
| Q2 follow-up (MERGE cost, no event ID) | 7 | Add `require_partition_filter`, `maximum_bytes_billed`, a bounded dedup window |
| Q3 off-track programme | 5 | Answered a different question. Restate before answering |
| Q4 utilisation, margin, capacity | 6 | Add capacity planning and numbers |
| Round 2 code reviews (two) | not scored | Answer text said the code was missing. Redo in your own words |

**Pattern:** strong technical reasoning; weaker on opening narrative, evidence, enterprise scope, and staying on the question asked.

---

## 3. Open items only you can close

| # | Item | Why it matters |
|---|---|---|
| 1 | Resolve the 8 `[TODO]`s in `ROUND_1_RRK.md` | Interviewers probe exactly these |
| 2 | Redo the two code reviews in your own words | The code review is a stated part of the round |
| 3 | Fill the migration story (template below) | Highest-probability behavioural topic |
| 4 | Fill the troubled-engagement story (template below) | Highest-probability behavioural topic |
| 5 | Write the "I was wrong" story | Googleyness gate |
| 6 | State the GCP-gap and the dated 60-day plan aloud | Biggest exposure |
| 7 | Reconcile your team-size figures (current headcount versus the 8-to-25 growth) | Inconsistent numbers get noticed |
| 8 | Book the Google Cloud certification date | The brief expects it |
| 9 | One live mock with a person who interrupts | Calibrates timing and follow-ups |

---

## 4. Story templates (fill in privately, outside this repo)

### 4.1 Migration: on-premises to BigQuery
> **S:** At [employer, anonymised], [source system] with about [X] TB served [N teams], cost about [$/year], and the pain was [reason].
> **T:** I was accountable for [architecture or delivery] by [date] without breaking [critical reports].
> **A:** I [retired about Y% unused data]; moved in [N] waves; ran **dual-run for [N weeks, including a month-end]**; reconciled with [counts, checksums, key-level diffs, KPI parity signed off by finance]; cut over by domain behind [a view switch]; kept the source read-only for [N days]; decommissioned with [owner].
> **R:** [X] TB migrated; [runtime A to B]; **time saved** [what, how measured]; **cost saved** [baseline, result, mechanism]; [zero Sev-1 discrepancies at cutover]. **My part:** [decisions]. **Differently:** [one real thing].

| Number | Be ready to say |
|---|---|
| TB | Total, and how much after retiring unused data |
| Dual-run | Length, and whether it covered a month-end |
| Reconciliation | Checks used, and defects caught |
| Time saved | From A to B, measured by M |
| Cost saved | Baseline, result, mechanism |

### 4.2 Troubled engagement
> **S:** [N weeks] into [programme: scope, size, budget]. **What broke:** [root cause, impact].
> **T:** I was [accountable or brought in] to recover it within [N days].
> **A:** 0 to 24 h: [who I talked to, data I pulled, people I protected]. 24 to 48 h: [diagnosed causes by owner; unblocked the dependency]. 48 to 72 h: [options with cost and risk; recommendation; re-baselined plan with an owner].
> **Recovery:** [the mechanism that stopped it recurring: steering cadence, defect SLA, test gate, scope].
> **R:** [dates, defects A to B, budget variance]. **CSAT restored:** [score, written feedback, renewal, follow-on]. **My part:** [decisions]. **Differently:** [one real thing].

### 4.3 Rules for every story
1. Lead with the outcome and your specific role ("I", not "we").
2. Every number has a baseline, a method, and a reason it was you.
3. One honest miss per story.
4. Under 2 minutes, then stop.
5. Never reuse the same percentage for two different employers unless you can explain each mechanism.

---

## 5. Seven-day finish

| Day | Do |
|---|---|
| 1 | Resolve the `[TODO]`s; reconcile numbers |
| 2 | Write and say the migration and troubled-engagement stories |
| 3 | Run the lab notebook; redo both code reviews aloud |
| 4 | Drill the topic deep-dive (BigQuery, streaming, security, migration, GenAI) |
| 5 | Practice Parts C and D aloud (consulting, practice, people) |
| 6 | Full 60-minute mock, recorded, with interruptions |
| 7 | Fix the weakest three answers; rest; logistics |
