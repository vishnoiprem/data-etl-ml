# Round 1 RRK — Mock Interview, 10 Rounds With Model Answers

**Role:** Data & Analytics Lead, Google Cloud Consulting (Singapore)
**Format:** 10 questions, ~6 minutes each, the mix the recruiter brief describes: hypothetical, behavioural, hands-on code review, architecture, consulting, practice, people.
**How to use:** cover the answer, speak yours aloud for the time given, then compare. Score each against the 4-line rubric at the end.
**Public-repo safe:** behavioural answers use `[YOUR …]` placeholders. Fill them from your private notes. Never say a number you can't defend (baseline, method, your role).

| # | Type | Topic | Time |
|---|---|---|---|
| 1 | Hypothetical | Vague brief: "do something with data" | 6 min |
| 2 | Technical | Late data + duplicates at 10B rows/day | 6 min |
| 3 | Code review | Short pipeline snippet | 8 min |
| 4 | Architecture | 2,000-pipeline migration, residency, 8 months | 8 min |
| 5 | Hypothetical | Programme 8 weeks in, off track | 6 min |
| 6 | Behavioural | Challenged an executive's assumption | 5 min |
| 7 | Practice | Utilisation, margin, over-delivery | 5 min |
| 8 | Pre-sales | $3M opportunity vs Snowflake/Databricks | 6 min |
| 9 | People | Underperforming senior architect | 5 min |
| 10 | GenAI | Governed RAG/agent platform for a bank | 6 min |

---

## Round 1 — "Help us do something with data."

**Q:** A customer's CIO says: *"We have a lot of data. Help us do something with it."* It's your first meeting. What do you do?

**Model answer**
> "I wouldn't propose anything in the first meeting. I'd turn the sentence into a **business outcome, a decision, and a constraint**.
>
> **Understand.** Three questions: *What decision or process would you most like to be better in 12 months, and what is it worth?* *Who owns that outcome, and who'd use the result?* *What have you tried, and why did it stall?* Then constraints: regulatory (residency), budget range, deadline driver, skills in-house, and existing platforms. If they can't answer, I state assumptions aloud and test them.
>
> **Prepare.** I'd ask for an inventory of data sources and owners, current platform and spend, two or three candidate use cases with a rough value, and access to one business stakeholder, not only IT.
>
> **Options.** (A) A **discovery sprint** (2–3 weeks): rank use cases by value × feasibility × data readiness. (B) A **lighthouse use case** built end-to-end in ~8–12 weeks to prove value and the operating model. (C) A **platform-first** programme. I'd steer away from C: it spends the budget before any business value exists.
>
> **Recommend.** A then B, with explicit go/no-go criteria at the end of A. The platform grows from the lighthouse, so every component is justified by a used outcome.
>
> **Support.** Success is *a decision made faster or better, adopted by named users*, not 'pipelines delivered'. Main risk: the use case is chosen by the loudest voice, not the best value; I mitigate with a scoring rubric agreed with the sponsor up front. I'd confirm the plan and decision rights with the CIO in a one-page summary."

**Why it passes:** structure before solution, outcome vs solution preference, an option you steer away from, measurable success, risk named.

---

## Round 2 — Late data and duplicates at scale

**Q:** A pipeline processes 10B rows/day. Late, out-of-order events and duplicates are corrupting daily aggregates. Diagnose and fix.

**Model answer**
> "**Clarify:** is it a *count* problem (double counting) or a *state* problem (an old update overwriting a newer one)? Exact duplicates (same event ID) or near-duplicates (same business key, different payload)? What's the arrival-lateness distribution (p50/p99), not the mean?
>
> **Diagnose** with evidence: sample reconciliations against source control totals, duplicate rate by source and hour, and the share of events arriving after the window closed.
>
> **Fix in three layers.** (1) *Containment this week:* quarantine and dedupe at the sink with `MERGE` on a deterministic event key, partition-scoped so reprocessing is cheap. (2) *Source:* make producers assign a stable event ID and sequence number so retries are safe. (3) *Processing semantics:* event-time windows, a watermark and allowed lateness set from the measured p99, upserts keyed by `(window, key)`, and a side-output/dead-letter table for too-late events reconciled in a daily batch.
>
> **On GCP:** Pub/Sub (ordering keys only where order matters; exactly-once delivery prevents redelivery but doesn't remove producer duplicates), Dataflow for event-time state, BigQuery Storage Write API with offsets or `MERGE` for an idempotent sink.
>
> **Measure:** duplicate rate at zero, source-to-sink reconciliation within tolerance, freshness SLO matching measured lateness. **Risk:** if producers can't change, sink idempotency becomes permanent architecture, so I'd plan it as such."

---

## Round 3 — Code review (read it live)

**Snippet**

```python
def load_orders(rows, table):
    seen = set()
    out = []
    for r in rows:
        if r["order_id"] in seen:
            continue
        seen.add(r["order_id"])
        r["amount_usd"] = r["amount"] * rates[r["currency"]]
        r["order_date"] = r["ts"][:10]
        out.append(r)
    bq.insert_rows_json(table, out)               # streaming insert
    logger.info("loaded %s rows: %s", len(out), out[:5])
    return len(out)
```

**Model review (say your order aloud: correctness → idempotency → scale → semantics → security → maintainability)**
1. **Correctness:** `rates[r["currency"]]` raises `KeyError` on an unknown currency and kills the batch; no null/zero handling on `amount`; floats for money (use `Decimal`/`NUMERIC`); which rate and as-of date? `ts[:10]` assumes UTC ISO strings, so a timezone bug moves orders across dates.
2. **Idempotency/restart:** dedupe is in-memory per batch only. A retry after partial failure re-inserts; `insert_rows_json` has no `insertId`, so duplicates land. Re-running the job duplicates every row. Fix: deterministic key + `MERGE`, or Storage Write API with offsets.
3. **Dedupe rule:** "first seen wins" ignores which version is newer; late updates to an order are dropped or the wrong one kept. Needs an ordering field (`updated_at`/version).
4. **Scale:** all rows in one list, one call: memory grows and the API payload limit is hit; no batching, no backoff. The `seen` set grows unbounded.
5. **Failure handling:** `insert_rows_json` returns per-row errors that are ignored, so failed rows vanish silently. No dead-letter path. Function returns `len(out)` even if inserts failed.
6. **Security:** logs the first 5 raw rows → PII in logs. Mutates input dicts (`r[...] =`), a side effect on the caller's data.
7. **Maintainability:** global `rates`, `bq`, `logger`; no types, no tests, no schema validation.

**The senior line:** *"The code is probably correct on the happy path. It's only correct if upstream guarantees one delivery and clean data, and nothing here enforces that. I'd make the write idempotent, explicit about its ordering rule, and route failures to an auditable dead-letter table."* Lead with items 2 and 5 (duplicate on rerun, silent loss).

---

## Round 4 — 2,000 pipelines, residency, 8 months

**Q:** Design the platform and plan for a customer with 2,000 pipelines across five lines of business, a data-residency requirement, and an 8-month deadline.

**Model answer**
> "**Understand:** how many pipelines actually matter (typically 20–40% are dead or duplicate), whether residency is by country or data class, whether 8 months is a regulatory or a board date, and who can authorise retiring a pipeline. The last one drives the schedule.
>
> **Prepare:** inventory every pipeline with owner, consumers, source, SLA, last-used date; that inventory is deliverable #1.
>
> **Options:** (A) big-bang replacement: won't fit 8 months. (B) **domain-by-domain waves**, each a full vertical slice (ingest → transform → serve → monitor) adopted before the next wave. (C) lift-and-shift only: fast, but preserves the cost and the mess. **Recommend B**, with C as a **stabilisation lane** for what won't be redesigned in time.
>
> **Architecture:** Datastream/Pub/Sub ingest → GCS raw → BigQuery layers (per-domain datasets, per-jurisdiction projects) → Looker semantic layer; Dataflow for streaming, Dataproc only for real Spark; Composer + Dataform for orchestration/transform; Dataplex catalog, quality scans, lineage, policy tags; VPC-SC, CMEK per boundary, resource-location org policy.
>
> **Operating model:** named owner per data product, SLOs, data contracts, **retirement funded as a deliverable per wave**, platform team owns standards.
>
> **Plan:** M1 inventory + landing zone + wave plan; M2–M3 lighthouse domain; M4–M7 remaining waves (parallel with SI partner for the factory work, we own architecture and QA); M8 decommission + hypercare.
>
> **Risks/measures:** waves 'done' but unused → track adopters; no retirement incentive → KPI; residency violation count must be zero; each wave has parallel-run reconciliation and a rollback."

---

## Round 5 — 8 weeks in and off track

**Q:** A transformation programme is 8 weeks in and clearly off track. First 72 hours?

**Model answer**
> "**Hours 0–24, listen and get facts.** Interview the sponsor, the delivery lead, two engineers and the customer's lead; pull plan vs actuals, burn-down, defect and blocker logs, and the contract scope. I'm separating *symptoms* (slipping dates) from *causes* (unclear scope, unmade decisions, wrong skills, dependency on another team, a flawed estimate).
>
> **Hours 24–48, diagnose.** Classify causes: scope, people, technical, governance, commercial. Quantify the gap: what's done, what's left, realistic velocity. Identify the **top 3 blockers** and which need an executive decision.
>
> **Hours 48–72, reset.** Present the sponsor with: honest status, root causes, 2–3 recovery options (cut scope / add capacity / move the date) with cost and risk, my recommendation, and the decision needed with a date. Then re-baseline: smaller milestones, weekly demos, a RAID log with owners, and a clear escalation path.
>
> **What I won't do:** hide the status, add people blindly (Brooks's law), or promise the original date.
>
> **Measure recovery:** plan variance, blocker age, demo acceptance, and sponsor confidence. And I'd run a short retrospective on how we missed it at week 2, because the earlier warning is the lasting fix."

---

## Round 6 — Challenged an executive's assumption (STAR)

**Q:** Tell me about a time you pushed back on an executive's unrealistic assumption while keeping their trust.

**Model answer (fill the brackets with your real story)**
> "**Situation:** At [industry/size anonymised], an executive sponsor wanted [e.g. all reporting migrated in 3 months]. **Task:** I was accountable for [the platform/delivery]; I believed the date was unachievable without [data quality / scope risk].
>
> **Action:** I separated the outcome from the solution, *'what decision needs this by that date?'*, and learned [the real deadline was X]. I brought evidence, not opinion: [a one-page estimate with dependencies, the failure history of similar efforts, a cost/risk table]. I offered three options (reduced scope on date, full scope later, extra capacity with its cost) and recommended one. I agreed decision rights and a checkpoint.
>
> **Result:** [what changed, e.g. phased delivery, the critical reports met the date, the rest followed; quantify]. The sponsor [kept/expanded] the engagement. **Reflection:** I'd [raise the evidence earlier / involve the finance partner sooner]."

**Rubric tip:** the line that scores is *"I gave a decision with a recommendation, not a veto, and I committed fully once decided."*

---

## Round 7 — Utilisation, margin, over-delivery

**Q:** How do you run a practice? Utilisation, delivery margin and capacity: which matters most?

**Model answer**
> "They're linked, so the hierarchy matters: **margin → customer outcomes → utilisation as an enabling constraint**. Utilisation is an input; margin is the result; and chasing utilisation alone drives bad staffing and burnout.
>
> *Utilisation* has different root causes at 60%: under-demand, mis-staffing (right people, wrong projects), or leakage to unbillable work, and each needs a different fix. *Delivery margin* leaks through scoping errors, staffing mix (too many seniors on commodity work), and **over-delivery**: scope creep absorbed free. *Capacity planning* runs on a 3-month forward view, pipeline probability-weighted, with a bench plan and a hiring/partner trigger.
>
> Over-delivery: it's sometimes strategic (a land-and-expand investment) but must be a **conscious, approved decision**, tracked, and converted to a change request or a follow-on. Otherwise it's silent margin loss.
>
> **Honesty:** [if you haven't owned a consulting P&L, say so]: *'I've owned a platform budget with real trade-offs, [$ and team size], and here's how I'd transfer that: tracking cost-to-deliver per outcome, staffing mix, and change control. In the first 90 days I'd learn the practice's actual rate card, utilisation targets and margin model.'*"

---

## Round 8 — $3M pre-sales opportunity

**Q:** An account team brings a $3M data-transformation opportunity. How do you approach it, and how do you position against Snowflake/Databricks?

**Model answer**
> "**Qualify first** with the account team: sponsor and budget owner, the business trigger, the competition, the decision timeline, and whether there's a funded outcome. **Discover** the customer's real workloads, skills and constraints before choosing a technology.
>
> **Shape the offer:** a short paid discovery/architecture phase, then phased delivery with a lighthouse, with fixed-price discovery and time-and-materials or capped delivery to manage risk; assumptions and exclusions in writing; a delivery-model split with a partner for volume work (we own architecture and quality). **Estimate** bottom-up by wave with ranges and contingency, and challenge any estimate resting on an undiscovered inventory.
>
> **Position honestly.** Snowflake: strong multi-cloud sharing and simplicity. Databricks: Spark/Delta depth and a data-science culture. Where Google wins: serverless BigQuery with no sizing, tight AI/ML (Gemini, Vertex), streaming, Looker's semantic layer, and open formats that cut lock-in. They can coexist (Databricks for heavy Spark, BigQuery for serving). I tell the customer where we're weaker.
>
> **Hand-off:** a written assumptions pack and a joint kickoff so delivery doesn't discover scope after signature. **Win/lose:** we run a review either way."

---

## Round 9 — The underperforming senior architect

**Q:** A senior architect on your team is underperforming. What do you do?

**Model answer**
> "First **diagnose, not judge**: is it *skill* (a gap vs the level), *will* (motivation/engagement), or *situation* (unclear expectations, personal circumstances, poor fit with the project)? I'd get specific evidence against the written level expectations, e.g. design quality, delivery, stakeholder feedback, not impressions.
>
> **Conversation:** private, direct, early: *here's the bar, here's what I'm seeing, what's your view?* Listen for obstacles I own. **Plan:** 30/60/90 days with measurable outcomes, a mentor or pairing, regular check-ins, and written follow-ups. Support is real: I remove blockers.
>
> **Outcomes:** if they improve, recognise it publicly. If not, move to a formal process with HR, with dignity: a role change if there's a better fit, otherwise a managed exit. I protect the team's delivery meanwhile; ignoring it costs the team's trust in me.
>
> **Example [YOUR STORY]:** [situation, what you did, outcome, what you'd do differently, e.g. 'I waited too long to have the first direct conversation']."

---

## Round 10 — Governed GenAI/RAG platform for a bank

**Q:** A regional bank wants a GenAI assistant over internal documents and data. Design it, and tell me where it goes wrong.

**Model answer**
> "**Clarify:** users and decisions supported, data sensitivity, residency/regulator expectations (MAS TRM), accuracy vs cost vs latency needs, and the human-in-the-loop line for risky actions.
>
> **Architecture:** classified sources → ingestion with **DLP redaction** and document-level ACLs carried as metadata → chunk, embed, index (BigQuery vector search or Vertex AI Vector Search) → **hybrid retrieval** (keyword + vector) with **permission filtering at query time** → rerank → grounded prompt to Gemini with citations → output filters (Model Armor/safety), audit logging of prompts and responses. For actions: tool-using agents with least-privilege tool scopes, step/time/cost limits, and approval gates.
>
> **Where it goes wrong:** (1) *data readiness*: stale, duplicated, unclassified documents give confident wrong answers; (2) *permission leakage*: retrieval ignoring the user's entitlements; (3) *prompt injection* from documents; (4) *no evaluation*: shipping without a golden question set; (5) *cost* per query; (6) *residency*: models/endpoints in the wrong region.
>
> **Measure:** groundedness/faithfulness, retrieval recall@k, answer acceptance, escalation rate, latency and cost per query, and zero entitlement-leak incidents in red-team tests. **Rollout:** pilot with one team, regression-test every prompt/model change, human review for high-risk answers.
>
> **The consulting point:** the value and the risk are in the governed corpus and operating model, not the model choice."

---

## Scoring Rubric (score each round 0–2 per line; 8 per round, 80 total)

| Line | 0 | 1 | 2 |
|---|---|---|---|
| **Structure** | Jumped to solution | Some clarifying | Clarified, stated assumptions, then options |
| **Judgement** | Component list / "it depends" | Options, weak pick | 2–3 options, trade-offs, a clear recommendation |
| **Evidence & numbers** | Vague | Some figures | Defensible numbers with baseline and your role |
| **Enterprise scope** | Single-project | Mentions ops | Ownership, adoption, rollback, decommission, cost |

**Targets:** ≥ 60/80 = ready. 45–59 = repeat the weakest three rounds. < 45 = restudy `ROUND_1_RRK_TOPIC_DEEP_DIVE.md` first.

**Hard-fail behaviours:** claiming results you can't defend; blaming others; no clarifying questions; a recommendation with no risk or measure.

**Final tactic:** after every answer, close with one of: *what could go wrong and how I'd measure it*, *what I need from you by when*, or *what I'd do differently*.
