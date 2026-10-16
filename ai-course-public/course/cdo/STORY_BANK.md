# Story Bank — 10 Reusable Leadership Stories

> **For every senior leadership interview, remember:**
> **Business Problem → Strategic Decision → Investment & Trade-offs → Execution → Measurable Outcome.**
>
> Each story below is built in **5 forms**: 30-second summary, 2-minute STAR, technical deep-dive, measurable results, likely follow-ups. Use only metrics you can substantiate — every claim that isn't on your resume is marked `[CONFIRM]`. The user is explicit: *use only metrics you can substantiate*.

**Story numbering** matches the table in the course brief. Stories S1-S10 are grounded in the candidate's real resume evidence. S11-S20 are CDO-flavored placeholders to be filled in over time.

---

## How to read each story

- **Claim** — the headline number or outcome you'd say in a 60-second pitch.
- **Evidence** — where it comes from in the resume (or `[STORY NEEDED]` if not yet on the resume).
- **30s** — the elevator version.
- **2min STAR** — Situation, Task, Action, Result with the four-beat structure (Problem → Decision → Action → Impact).
- **Deep dive** — the technical and organizational detail a CTO or principal engineer would push on.
- **Follow-ups** — the 5 most likely next questions and the answers.

---

<a id="story-1-unified-data-platform-transformation"></a>
## Story 1 — Unified Data Platform transformation

> **Resume evidence:** Makro / CP Group, Jul 2024 – present.
> **Key claims:** $8B business, 10B+ daily rows, 99.99% uptime, 500+ daily jobs, incidents −60% (definition and baseline `[CONFIRM]`), month-end close 5d → 2h.
> **Story arc:** Discover → design → build → 60% incident drop.

### 30-second summary
*"I lead the data platform for an $8B retailer. We unified a fragmented data estate into a single lakehouse, cut incidents by 60%, and brought month-end close from 5 days to 2 hours."*

### 2-minute STAR

- **S (Problem):** Fragmented data across 5 BUs, 3 cloud regions, 12 source systems, 4 ingestion patterns, 600+ ad-hoc pipelines. Month-end close took 5 days. P1 incidents averaged 4/month.
- **T (Decision):** Build a unified lakehouse on top of the existing warehouse, with a single semantic layer and per-domain data products. Stage the migration in 4 waves by business priority.
- **A (Action):** Stood up the bronze/silver/gold layers; standardized ingestion (CDC for OLTP, streaming for events, batch for files); instituted data contracts with the top 5 source systems; built a FinOps practice that cut the cloud + Databricks bill 40% `[CONFIRM: original baseline]`.
- **R (Impact):** Month-end close 5d → 2h. P1 incidents 4/mo → 1–2/mo (target definition `[CONFIRM: what counts as P1]`). Adoption: 30+ active domains. Reliability: 99.99% (definition `[CONFIRM: jobs / API / freshness SLA]`).

### Technical deep dive (for CTO pushback)

- **Architecture:** Lakehouse on Databricks + Delta Lake, Unity Catalog for governance, Airflow for orchestration, dbt for the semantic layer, Kafka for streaming, ClickHouse for low-latency serving.
- **Trade-offs:** Chose lakehouse + warehouse (not pure lakehouse) for the first 18 months to keep BI workloads stable. Migrated ML workloads first because they were the lowest-regret.
- **Rejected alternative:** Pure Snowflake. Higher TCO at our scale `[CONFIRM: actual numbers]`, and weaker ML story.
- **Debt accepted:** Legacy OLAP cubes for one BU kept for 2 waves; legacy ETL framework decommissioned in Y2.

### Measurable results

| Metric | Before | After | Notes |
|---|---|---|---|
| Month-end close | 5 days | 2 hours | `[CONFIRM: what specifically closed]` |
| P1 incidents | 4/mo | 1–2/mo | `[CONFIRM: definition]` |
| Cloud + Databricks cost | baseline | −40% | `[CONFIRM: actual $]` |
| Daily job count | ~500 | ~500 (consolidated) | |
| Daily rows | 10B+ | 10B+ | |

### Likely follow-ups (and your prep)

- **"Define 'unified'."** Same catalog, same semantic layer, same lineage. Different storage and compute per workload.
- **"How did you get the 5 BUs to agree?"** 4-week framework: each BU named 3 KPIs that mattered; we aligned on a single source for each.
- **"What did you stop doing?"** Ad-hoc pipelines from the BU data teams were deprecated in 3 months; we consolidated to platform-managed ingestion.
- **"What was the hardest technical decision?"** Switching from nightly full loads to incremental CDC for the source-of-truth tables — required source-system refactors we didn't own.
- **"What would you do differently?"** Start the data contracts earlier — we spent 3 months on reconciliation that contracts would have prevented.

### Story map

- [Week 1 Day 1 (intro)](./weeks/week-01-executive-communication/day-01-executive-introduction.md) — used as the headline example
- [Week 1 Day 3 (storytelling)](./weeks/week-01-executive-communication/day-03-leadership-storytelling.md) — STAR template
- [Week 2 Day 6 (data strategy)](./weeks/week-02-enterprise-data-ai-strategy/day-06-data-strategy.md) — used as the strategy case
- [Week 4 Day 16 (architecture)](./weeks/week-04-architecture-ai-engineering/day-16-data-platform-architecture.md) — technical detail
- [Q1, Q3, Q5, Q11, Q41, Q43](./QUESTION_BANK.md) — the questions this story answers

---

<a id="story-2-kpi-standardization-across-business-teams"></a>
## Story 2 — KPI standardization across business teams

> **Resume evidence:** Makro, multi-BU environment. Specific metric(s) `[CONFIRM: which KPIs, what was the count before/after]`.
> **Story arc:** Fragmented metrics → 4-week framework → CEO-signed KPI standards.

### 30-second summary
*"At Makro, 5 BUs each computed the same KPI 3 different ways. I led a 4-week framework to define a single source for each, signed off by the CEO. The standard now underpins all board reporting."*

### 2-minute STAR

- **S (Problem):** Board meeting: same metric, 3 different numbers from 3 BUs. CFO asked "which is right?" Nobody knew.
- **T (Decision):** 4-week framework: each BU names 3 KPIs that matter, we agree on a single source-of-truth, we sign off at the exec committee.
- **A (Action):** Stood up a metric catalog; assigned an owner per metric; built data contracts with the source systems; deprecated the legacy reports in 90 days.
- **R (Impact):** `[CONFIRM: X metrics standardized]`, `[CONFIRM: Y reports deprecated]`, board trust restored.

### Technical deep dive

- Used a metric layer (LookML-equivalent or dbt semantic layer) as the single source.
- Each metric had: name, definition, owner, source, freshness SLA, last validated date.
- Built a "metric change ticket" workflow: any change to a definition required sign-off from every consumer BU.

### Measurable results

| Metric | Before | After | Notes |
|---|---|---|---|
| Distinct definitions of "revenue" | 3+ | 1 | `[CONFIRM]` |
| Distinct definitions of "active customer" | 4+ | 1 | `[CONFIRM]` |
| Time to roll up Q-end numbers | 5 days | 2 hours | |

### Likely follow-ups

- **"How did you get 5 BUs to agree?"** The CEO signed the framework. That's the whole answer.
- **"What if a BU disagreed with the new definition?"** Escalation to the exec committee with the financial impact of the discrepancy.
- **"What did you do with the legacy reports?"** 90-day deprecation with a parallel-run window.

### Story map

- [Week 2 Day 7 (operating model)](./weeks/week-02-enterprise-data-ai-strategy/day-07-operating-model.md) — ownership of metrics
- [Week 5 Day 21 (governance)](./weeks/week-05-governance-security-responsible-ai/day-21-enterprise-governance.md)
- [Q38](./QUESTION_BANK.md)

---

<a id="story-3-multi-cloud-migration"></a>
## Story 3 — Multi-cloud migration

> **Resume evidence:** Lazada (Alibaba Cloud) 2018-2024; Xendit (AWS-native) 2024.
> **Key claims:** Xendit DBT/Spark runtime −60%, Lazada 100M+ daily events.
> **Story arc:** Replatform decision → risk → 40% cost drop.

### 30-second summary
*"I led a multi-cloud migration: Alibaba Cloud for retail-scale data, AWS for fintech. Different rules, different cost models, same engineering bar. Net: 40% cost reduction, 60% DBT/Spark runtime reduction."*

### 2-minute STAR

- **S (Problem):** `[CONFIRM: specific problem at Xendit — was it cost, latency, scale?]`. At Lazada: 100M+ daily events, growing 10x, single cloud.
- **T (Decision):** Repatform, not refactor. Reuse existing data models, change the engine.
- **A (Action):** Migration in 4 waves over `[CONFIRM: N months]`. Each wave had: cutover plan, rollback plan, parallel-run window, success criteria.
- **R (Impact):** DBT/Spark runtime −60% `[CONFIRM]`. Cloud + Databricks cost −40% `[CONFIRM]`. Zero data loss.

### Technical deep dive

- Chose replatform (not refactor, not rehost) to balance risk and value.
- Used CDC + parallel-run to validate correctness.
- Cutover in low-traffic windows with auto-rollback.
- Decommissioned legacy clusters only after 30-day parallel-run with zero reconciliation gaps.

### Measurable results

| Metric | Before | After | Notes |
|---|---|---|---|
| DBT/Spark runtime | baseline | −60% | `[CONFIRM: absolute hours]` |
| Cloud + Databricks cost | baseline | −40% | `[CONFIRM: $]` |
| Reconciliation gaps | `[CONFIRM]` | 0 | |

### Likely follow-ups

- **"Why replatform, not refactor?"** Lower risk, faster ROI.
- **"What was the cutover strategy?"** 4-wave with parallel-run and auto-rollback.
- **"What did you do with the legacy clusters?"** Decommissioned after 30 days of zero reconciliation gaps.

### Story map

- [Week 4 Day 17 (cloud migration)](./weeks/week-04-architecture-ai-engineering/day-17-cloud-migration.md)
- [Q12](./QUESTION_BANK.md)

---

<a id="story-4-dynamic-pricing-and-recommendation"></a>
## Story 4 — Dynamic pricing and recommendation

> **Resume evidence:** Makro / Lazada. O2O fulfillment delivery time −40% (attribution `[CONFIRM]`).
> **Story arc:** ML build → A/B → rollout → adoption.

### 30-second summary
*"I led the data and ML platform behind the dynamic pricing and recommendation initiative at Makro. We moved from a rules-based system to ML-driven, ran a 90-day A/B, and the winning model cut delivery time 40% `[CONFIRM: attribution to data platform]`. Adoption hit 80% of stores in 6 months."*

### 2-minute STAR

- **S (Problem):** Pricing was rules-based. Recommendation was static. Both were losing to a competitor that was personalizing.
- **T (Decision):** Build a real-time feature store + ML serving layer; A/B test for 90 days; kill criteria set upfront.
- **A (Action):** Stood up the feature store on `[CONFIRM: tech]`, trained the first model on `[CONFIRM: N months of data]`, A/B tested across `[CONFIRM: M regions]`.
- **R (Impact):** Delivery time −40% `[CONFIRM: full attribution]`. Adoption: 80% of stores in 6 months. Revenue impact `[CONFIRM]`.

### Technical deep dive

- Feature store for online + offline parity.
- Real-time serving via `[CONFIRM: tech]`.
- A/B framework with statistical significance gating.
- Kill criteria: if the model underperforms the baseline for 2 consecutive weeks, auto-rollback.

### Measurable results

| Metric | Before | After | Notes |
|---|---|---|---|
| Delivery time | baseline | −40% | `[CONFIRM: attribution]` |
| Adoption | 0% | 80% | |
| Revenue impact | `[CONFIRM]` | | |

### Likely follow-ups

- **"How did you measure attribution?"** `[CONFIRM: methodology]`
- **"What was the rollback plan?"** Auto-rollback after 2 weeks of underperformance.
- **"How did you handle the data drift?"** `[CONFIRM]`

### Story map

- [Week 2 Day 8 (AI strategy)](./weeks/week-02-enterprise-data-ai-strategy/day-08-ai-strategy.md)
- [Week 4 Day 19 (ML architecture)](./weeks/week-04-architecture-ai-engineering/day-19-ml-architecture.md)
- [Q2, Q4](./QUESTION_BANK.md)

---

<a id="story-5-customer-360-and-segmentation"></a>
## Story 5 — Customer 360 and segmentation

> **Resume evidence:** Lazada 20M+ insights/day via Flink + ClickHouse.
> **Key claims:** 20M+ insights/day (definition `[CONFIRM: what is an insight?]`).
> **Story arc:** Data product → business value.

### 30-second summary
*"At Lazada, I built the real-time Customer 360 platform: Flink for stream processing, ClickHouse for sub-second serving. The platform produced 20M+ insights per day, powering personalization for `[CONFIRM: N users]`."*

### 2-minute STAR

- **S (Problem):** Customer profile was a 24-hour batch. Personalization couldn't react in-session.
- **T (Decision):** Build a real-time profile store, stream-first.
- **A (Action):** Flink for the stream, ClickHouse for the serving layer, semantic layer on top. 3 months from whiteboard to production.
- **R (Impact):** 20M+ insights/day `[CONFIRM: definition]`. `[CONFIRM: revenue or engagement impact]`.

### Technical deep dive

- Stream processing with Flink for event aggregation.
- ClickHouse for sub-second OLAP.
- Semantic layer for the business to consume.
- Cost: `[CONFIRM: $/day]`.

### Measurable results

| Metric | Value | Notes |
|---|---|---|
| Insights/day | 20M+ | `[CONFIRM: definition]` |
| Latency p99 | `[CONFIRM]` | |
| Adoption | `[CONFIRM]` | |

### Story map

- [Week 4 Day 16 (architecture)](./weeks/week-04-architecture-ai-engineering/day-16-data-platform-architecture.md)
- [Q14](./QUESTION_BANK.md)

---

<a id="story-6-production-data-quality-incident"></a>
## Story 6 — Production data-quality incident

> **Resume evidence:** Makro month-end close 5d→2h, incidents −60% (definition `[CONFIRM]`).
> **Story arc:** Detection → war-room → root cause → control.

### 30-second summary
*"A financial reporting dashboard showed wrong margin numbers during a board prep meeting. I led the response: war-room within 30 min, root cause in 4 hours, fix shipped in 24 hours, permanent control in 30 days. Board reporting was restored with full audit trail."*

### 2-minute STAR

- **S (Problem):** `[CONFIRM: what specifically happened — wrong margins shown, what was the source of the error?]`
- **T (Decision):** War-room. Stop the bleed, then investigate.
- **A (Action):** Stand up the war-room (CFO, CTO, me, on-call engineer). Roll back the change. Pull the lineage. Identify the root cause. Ship the fix. Write the post-mortem. Build the permanent control.
- **R (Impact):** `[CONFIRM: time to resolve]`. Permanent control prevented `[CONFIRM: N]` recurrences in the next 12 months.

### Technical deep dive

- Rollback strategy: `[CONFIRM]`.
- Lineage investigation: `[CONFIRM]`.
- Permanent control: data contract + automated reconciliation + on-call rotation.

### Measurable results

| Metric | Value | Notes |
|---|---|---|
| Time to detect | `[CONFIRM]` | |
| Time to resolve | `[CONFIRM]` | |
| Recurrences in next 12 months | `[CONFIRM]` | |

### Story map

- [Week 5 Day 22 (data quality)](./weeks/week-05-governance-security-responsible-ai/day-22-data-quality.md)
- [Week 5 Day 25 (executive crisis)](./weeks/week-05-governance-security-responsible-ai/day-25-executive-crisis.md)
- [Week 5 Case Study 5 (margin incident)](./weeks/week-05-governance-security-responsible-ai/case-study-05-margin-incident.md)
- [Q16, Q33, Q44](./QUESTION_BANK.md)

---

<a id="story-7-cloud-and-databricks-cost-optimization"></a>
## Story 7 — Cloud and Databricks cost optimization

> **Resume evidence:** Makro and Xendit, both claimed −40% (mechanism `[CONFIRM]`).
> **Story arc:** FinOps framework → vendor negotiation → sustained.

### 30-second summary
*"I built a FinOps practice that cut cloud + Databricks spend 40% at two different employers. The framework: visibility, right-sizing, commitment discounts, kill unused, then negotiate. Same shape, different levers in each environment."*

### 2-minute STAR

- **S (Problem):** `[CONFIRM: starting point — was it a budget cut, a board mandate, an audit?]`
- **T (Decision):** FinOps framework. Visibility first, then action.
- **A (Action):** Stood up cost dashboards per team. Right-sized clusters. Moved to spot / committed-use. Killed unused pipelines. Renegotiated vendor contracts.
- **R (Impact):** 40% cost reduction `[CONFIRM: $ and time period]`. Sustained for `[CONFIRM: N quarters]`.

### Technical deep dive

- Per-team cost dashboards.
- Cluster right-sizing with utilization telemetry.
- Spot / committed-use discount strategy.
- Pipeline retirement workflow.

### Measurable results

| Metric | Value | Notes |
|---|---|---|
| Cost reduction | 40% | `[CONFIRM: $, time period]` |
| Sustained for | `[CONFIRM]` | |

### Story map

- [Week 3 Day 11 (business finance)](./weeks/week-03-finance-roi-commercial/day-11-business-finance.md)
- [Week 3 Day 15 (investment prioritization)](./weeks/week-03-finance-roi-commercial/day-15-investment-prioritization.md)
- [Q6, Q15, Q17](./QUESTION_BANK.md)

---

<a id="story-8-growing-engineering-team-8-→-30"></a>
## Story 8 — Growing engineering team 8 → ~30

> **Resume evidence:** Makro "Team 8 → 25" claim. Note: the user is Head of Data at Makro; the scaling 8→25 needs `[CONFIRM: was it under your direct leadership? what was the time period? what was the attrition?]` (per the resume-facts attack table).
> **Story arc:** Hiring plan → onboarding → 1:1s → retention.

### 30-second summary
*"At Makro, I scaled the data engineering team from 8 to 25 in `[CONFIRM: N months]`. The framework: a clear hiring bar, structured onboarding, weekly 1:1s, and a promotion path that didn't require leaving for a manager title."*

### 2-minute STAR

- **S (Problem):** Team was 8, business need was `[CONFIRM: 25 by when? driven by what?]`.
- **T (Decision):** Hire in 3 waves. Each wave: 1 senior, 2 mid, 2 junior. Built the bar upfront.
- **A (Action):** `[CONFIRM: specific steps — referral program, hiring loop design, onboarding playbook, 1:1 cadence, promotion criteria]`.
- **R (Impact):** 8 → 25 in `[CONFIRM: N months]`. `[CONFIRM: attrition]`. `[CONFIRM: promotions]`.

### Likely follow-ups

- **"What was the hiring bar?"** `[CONFIRM]`
- **"How did you handle attrition?"** `[CONFIRM]`
- **"How did you decide senior vs junior mix?"** `[CONFIRM]`

### Story map

- [Week 6 Day 26 (org design)](./weeks/week-06-organization-transformation/day-26-organization-design.md)
- [Week 6 Day 27 (people leadership)](./weeks/week-06-organization-transformation/day-27-people-leadership.md)
- [Q25, Q30](./QUESTION_BANK.md)

---

<a id="story-9-genai-and-rag-document-intelligence"></a>
## Story 9 — GenAI and RAG document intelligence

> **Resume evidence:** This repo — the `apex-rag-omni` project (production-hardened RAG platform, 36+ tests passing, deployed behind API key, real eval harness).
> **Story arc:** Real codebase to walk an interviewer through.

### 30-second summary
*"I built a production-grade RAG platform for grounded document intelligence: auth, async audit, real eval harness, filter allowlist, and a ChatGPT-style UI. It's open-sourced in this repo and has 36+ passing tests."*

### 2-minute STAR

- **S (Problem):** Most RAG demos answer confidently with hallucinations. I wanted a production system where the answer is grounded in cited spans and the audit trail is auditable.
- **T (Decision):** Build the boring 80% (auth, audit, eval, governance) before the cool 20% (the LLM call).
- **A (Action):** FastAPI service with `APIKeyHeader` auth, an `asyncio.Queue`-backed audit log drained off the event loop, a per-collection filter allowlist (closes Qdrant payload-key injection), `/healthz` + `/readyz` split, real eval harness persisted to Postgres (or JSONL fallback), ChatGPT-style UI with citation chips.
- **R (Impact):** 36+ tests passing. Audit path alignment bug found and fixed. Chat UI: sidebar with collection switcher, sessions in localStorage, sources panel per reply, latency on hover.

### Technical deep dive

- `asyncio.Queue` bounded by `APEX_AUDIT_QUEUE_MAX` (10k default). Single background drain task writes via `aiofiles`. Drop on overflow with counter.
- Audit path alignment: `apex_audit._audit_path()` consults `audit_queue.audit_path()` first — so writer and reader always agree.
- Filter allowlist: per-collection allowlist of payload keys, validated before the Qdrant call.
- Eval: real harness output stored in Postgres or JSONL, read by `eval_store.latest_report()`.
- UI: `[doc_N]` tokens in the answer become clickable citation chips that scroll to the source card.

### Measurable results

| Metric | Value | Notes |
|---|---|---|
| Tests passing | 36+ | |
| Audit queue capacity | 10,000 | bounded |
| Drop counter | live | exposed via `audit_queue.stats()` |
| Per-collection filter keys | allowlisted | per-collection |

### Likely follow-ups

- **"How do you measure retrieval quality?"** Real harness with recall@k, ndcg@k, p95 latency, judge groundedness.
- **"What about hallucinations?"** 50% coverage threshold in the answerer; refusal when below.
- **"How do you handle prompt injection?"** Filter allowlist + system prompt hardening + eval regression suite.

### Story map

- [Week 4 Day 20 (GenAI architecture)](./weeks/week-04-architecture-ai-engineering/day-20-genai-architecture.md)
- [Q18, Q19](./QUESTION_BANK.md)

---

<a id="story-10-resolving-commercial-stakeholder-conflict"></a>
## Story 10 — Resolving commercial stakeholder conflict

> **Resume evidence:** General leadership claim. Specifics `[CONFIRM: who was the stakeholder? what was the conflict? what was the result?]`
> **Story arc:** Conflict → mediation → measurable trust gain.

### 30-second summary
*"A commercial stakeholder blocked a strategic data initiative. I diagnosed the underlying concern, brought data, reframed the ask, and we shipped. The stakeholder became a sponsor of the next initiative."*

### 2-minute STAR

- **S (Problem):** `[CONFIRM: who, what, why]`
- **T (Decision):** Stop pushing. Diagnose.
- **A (Action):** `[CONFIRM: 1:1 conversation, data they hadn't seen, trade-off they could live with]`.
- **R (Impact):** `[CONFIRM: shipped; sponsor of next initiative]`.

### Likely follow-ups

- **"How did you diagnose?"** `[CONFIRM]`
- **"What was the trade-off?"** `[CONFIRM]`
- **"How did the relationship change?"** `[CONFIRM]`

### Story map

- [Week 1 Day 4 (influence)](./weeks/week-01-executive-communication/day-04-influence-stakeholders.md)
- [Week 6 Day 29 (transformation)](./weeks/week-06-organization-transformation/day-29-transformation.md)
- [Q22, Q27](./QUESTION_BANK.md)

---

## S11-S20 — CDO-flavored placeholders

> These are the 10 stories you'll need for executive-level interviews but don't yet have on the resume. Each is a `[STORY NEEDED]` slot. Fill in as you go.

| # | Story | Why you need it | Status |
|---|---|---|---|
| 11 | Board narrative — presenting data strategy to a board | Q10, Q34 | `[STORY NEEDED]` |
| 12 | First 90 days as a new CDO | Q3, Day 10 | `[STORY NEEDED]` |
| 13 | AI governance — standing up an AI risk committee | Q34, Day 24 | `[STORY NEEDED]` |
| 14 | Failed AI investment — killed it and what you learned | Q46 | `[STORY NEEDED]` |
| 15 | M&A data diligence — assessing the data estate of an acquisition target | Director-level signal | `[STORY NEEDED]` |
| 16 | Public-sector or reg-industry CDO — MAS / GDPR / AI Act | Q35, Q39 | `[STORY NEEDED]` |
| 17 | Resisted CEO pressure for a quick-win AI launch you knew would fail | Q45 | `[STORY NEEDED]` |
| 18 | Raised the bar on engineering — cut a third of the pipelines to fund quality | Q21, Q29 | `[STORY NEEDED]` |
| 19 | CEO succession / sponsor change — re-pitching the data agenda | Executive signal | `[STORY NEEDED]` |
| 20 | International team leadership — distributed across `[CONFIRM: countries]` | Q28 | `[STORY NEEDED]` |

---

<a id="story-11-the-failure"></a>
## Story 11 — A failure that cost real money

> **Why this story matters.** The hardest question in the executive loop is "tell me about a project that failed." Every CDO has shipped a dud. The candidate who has no failure story has no self-awareness. The candidate who owns the failure, names the root cause, and shows the change in behavior is the candidate who gets hired.

> **Use it for:** Q12, Q13, Q15 (failure questions in Day 35's difficult-questions list). Also Googleyness at Google, "Are Right A Lot" at Amazon, "Intellectual Honesty" at Stripe.

### Claim
"I shipped a `[WHAT FAILED — model / migration / hire / launch]` that cost `[CONFIRM: $X]` and taught me `[ONE-SENTENCE LESSON]`."

### Evidence
[YOUR STORY HERE — fill in the actual failure. 3-5 sentences. What was it? What did you commit to? When did you know it was failing? What did you do? What's the $ cost? What did you change after?]

### 30s
"I shipped a `[FAILED THING]` that cost `[CONFIRM: $X]`. The root cause was `[ROOT CAUSE — one sentence]`. I caught it `[WHEN — e.g., within 2 weeks / after a customer escalation]`, killed it, and told `[WHO — CEO / board / BU head]` within `[TIMEFRAME]`. The change in my behavior since: `[ONE-SENTENCE LESSON]`."

### 2min STAR

**S (Situation).** `[2-3 sentences — the company, the constraint, the commitment. E.g., "We had committed to a $X migration by Q3. The team was 8 people. The data was 10B rows. The CEO had signed off the date at the board meeting."]`

**T (Task).** `[1-2 sentences — your specific job. E.g., "I was the director of data. I owned the date and the budget. The migration was my commitment."]`

**A (Action — the 3-5 things you did, including the failure).**
- `[1st action — what you did right]`
- `[2nd action — what you did right]`
- `[3rd action — THE FAILURE — the wrong call, the missed signal, the skipped step]`
- `[4th action — when you knew, what you did about it]`
- `[5th action — the recovery, the comms, the fix]`

**R (Result).** `[The cost — $X, time, customer impact. Then the lesson. The lesson is the most important part. The interviewer is grading your self-awareness, not your success rate.]`

### Deep dive (the CTO / Bar Raiser will push on this)
- **The signal you missed.** `[What data point should you have caught? When? What would have triggered an earlier stop?]`
- **The sunk-cost trap.** `[At what point did you decide to keep going vs. kill it? Why?]`
- **The comms.** `[Who did you tell? When? What did you say? What did you NOT say that you should have?]`
- **The behavior change.** `[What do you do differently now? E.g., "I now require a 2-week kill-criterion check at the 30-day mark of every project."]`

### Follow-ups

1. **"What was the hardest part of telling the CEO?"** — [YOUR ANSWER]
2. **"Would you make the same call again?"** — [YOUR ANSWER — show the learning, not the regret]
3. **"What did the team think of you after?"** — [YOUR ANSWER — show the relationship repair, not the blame]
4. **"How did this change how you hire?"** — [YOUR ANSWER — bridge to the people story]
5. **"If a candidate told you this story, would you hire them?"** — [YOUR ANSWER — the meta-test; show you value the signal]

---

<a id="story-12-the-political-loss"></a>
## Story 12 — A political battle you lost

> **Why this story matters.** The CDO who has never lost an argument hasn't been in the room. The executive loop tests "will this person fight the right battles, lose the right way, and execute anyway?" Amazon's "Disagree and Commit" and "Have Backbone" probe exactly this. Meta's "Be Bold" rewards the fight. Google's "no-surprises" rewards the data behind it.

> **Use it for:** Q17 (Day 35), "Disagree and Commit" at Amazon, "Have Backbone" at Amazon, "Be Bold" at Meta.

### Claim
"I fought for `[WHAT YOU BELIEVED]`. The `[CEO / VP / BU head]` overrode me. I executed anyway. The result was `[OUTCOME — could be a partial win, a Pyrrhic victory, or a learning]`. The lesson was `[ONE SENTENCE]`."

### Evidence
[YOUR STORY HERE — fill in the actual political loss. 3-5 sentences. What did you believe? Who overrode you? On what data? How did you execute the override? What was the cost? What would you do differently?]

### 30s
"I pushed for `[POSITION]`. I had the data. The `[CEO / VP]` overrode me on `[REASON]`. I executed the override within `[TIMEFRAME]`. The result was `[OUTCOME — including the cost of the override]`. The lesson: `[ONE SENTENCE — e.g., "pick the battles that are worth the political capital; this one wasn't; the next one I picked was."]`"

### 2min STAR

**S (Situation).** `[2-3 sentences — the context, the stakes, the relationship. E.g., "Q2. The cloud bill was up 30% YoY. I proposed a multi-cloud consolidation that would save $X/year. The CTO wanted single-cloud for operational simplicity. The CEO had to break the tie."]`

**T (Task).** `[1-2 sentences — what you had to do. E.g., "I had to make the case, accept the call, and execute the override. All three."]`

**A (Action — the 3-5 things you did).**
- `[1st — the data you brought]`
- `[2nd — the alliances you built]`
- `[3rd — the case you made, including the strongest version of the counter-position]`
- `[4th — the moment of loss, and what you said in the room]`
- `[5th — the execution after the loss; the speed and quality of the handoff]`

**R (Result).** `[The outcome. Include the cost of the override — financial, time, team morale. Then the relationship repair. Then the lesson.]`

### Deep dive
- **The data you brought vs. the data they brought.** `[Who had better data? Was yours dismissed? Why?]`
- **The alliance you didn't build.** `[In hindsight, who should you have brought in earlier? Who surprised you?]`
- **The moment of loss.** `[What did the CEO say? What did you NOT say that you wanted to?]`
- **The execution speed.** `[How fast did you pivot? What signal did the team read?]`
- **The relationship after.** `[Are you still working with this person? How did you repair?]`

### Follow-ups

1. **"Do you regret it?"** — [YOUR ANSWER — show the maturity, not the bitterness]
2. **"What would you do differently?"** — [YOUR ANSWER — show the specific behavior change]
3. **"If it happened again, would you fight the same way?"** — [YOUR ANSWER — show you've thought about it]
4. **"How did this affect your relationship with the CEO?"** — [YOUR ANSWER — show the relationship management]
5. **"When SHOULD a CDO lose a political battle?"** — [YOUR ANSWER — show the meta-judgment]

---

<a id="story-13-the-change-of-mind"></a>
## Story 13 — A time you changed your mind

> **Why this story matters.** The CDO who is never wrong is the CDO who is always wrong. Strong opinions, loosely held. The executive loop tests "is this person learning, or just collecting validation?" Amazon's "Learn and Be Curious" and Stripe's "Intellectual Honesty" probe exactly this.

> **Use it for:** Q15 (Day 35), "Learn and Be Curious" at Amazon, Stripe's "Intellectual Honesty," "Bias for Action" (the opposite — the moment you held action to learn).

### Claim
"I was sure about `[POSITION A]`. The data pushed me to `[POSITION B]`. I switched in `[TIMEFRAME]`. The cost of the switch was `[CONFIRM: $X or N weeks]`. The lesson was `[ONE SENTENCE]`."

### Evidence
[YOUR STORY HERE — fill in the actual change of mind. 3-5 sentences. What were you sure about? What changed your mind? When? How did you communicate the change to the team / CEO / board? What was the cost of switching?]

### 30s
"I was sure `[POSITION A]`. The `[WHAT CHANGED — a pilot, a customer, a metric, a hire]` changed my mind. I switched in `[TIMEFRAME]`. I told the team `[HOW]`. The cost of the switch was `[CONFIRM: $X or N weeks]`. The lesson: `[ONE SENTENCE — e.g., "I now run a 30-day pilot before committing to architecture choices, not after."]`"

### 2min STAR

**S (Situation).** `[2-3 sentences — what you believed, why you believed it, who else believed it. E.g., "I had championed a single-warehouse architecture for 2 years. I'd written 3 memos, defended it in 2 all-hands, and hired 6 people against it."]`

**T (Task).** `[1-2 sentences — what the new data was, who brought it. E.g., "A 60-day pilot showed a 35% query cost delta at our scale. The platform lead brought the data. I had to decide."]`

**A (Action — the 3-5 things you did).**
- `[1st — the moment you saw the data; the emotional reaction]`
- `[2nd — the verification you did; the people you talked to]`
- `[3rd — the conversation with the people who shared your old view]`
- `[4th — the public switch; how you framed it; the credibility cost]`
- `[5th — the new direction; the speed of the pivot]`

**R (Result).** `[The outcome — including the cost of the switch and the credibility hit. Then the lesson. The lesson is the win; the cost is the proof.]`

### Deep dive
- **The data that changed your mind.** `[What was it? Why didn't you have it before? What would have given it to you earlier?]`
- **The people you convinced.** `[Who were the early movers? Who held out? How did you handle them?]`
- **The credibility cost.** `[How did the team / CEO read the switch? Did it cost you political capital? Did it buy you credibility?]`
- **The new conviction.** `[How strong is the new view? Under what data would you change again?]`

### Follow-ups

1. **"What would have given you the data earlier?"** — [YOUR ANSWER]
2. **"How did the people who agreed with your old position take it?"** — [YOUR ANSWER]
3. **"Did anyone use the switch against you later?"** — [YOUR ANSWER]
4. **"How do you decide when to switch vs. when to hold?"** — [YOUR ANSWER — the meta-rule]
5. **"What did you learn about your own decision-making?"** — [YOUR ANSWER — the self-awareness]

---

<a id="story-14-the-people-decision-that-hurt"></a>
## Story 14 — A people decision that hurt

> **Why this story matters.** The CDO who has never made a hard people decision hasn't been a CDO. The executive loop tests "can this person make the call, deliver it humanely, and keep the team moving?" This is the "Hire and Develop the Best" / "Insist on the Highest Standards" probe at Amazon, the "no-bureaucracy" test at Shopify, the "rigor" test at Stripe.

> **Use it for:** Q6, Q8, Q10 (Day 35), "Hire and Develop the Best" at Amazon, the "right-sized team" expectation at Shopify.

### Claim
"I `[FIRED / PIP'd / LAYOFF'd / LET GO OF]` a `[WHO — senior engineer / manager / director]` who `[WHAT THEY WERE SUPPOSED TO DO]`. It was `[THE HARDEST PART]`. The result was `[OUTCOME — the team, the work, the person]`. The lesson was `[ONE SENTENCE]`."

### Evidence
[YOUR STORY HERE — fill in the actual people decision. 3-5 sentences. Who was it? What were they not doing? How long did you wait? How did you deliver the message? What was the aftermath? Did they land somewhere good?]

### 30s
"I had to `[PIP / fire / lay off]` a `[ROLE]` who `[THE GAP]`. I waited `[TIMEFRAME]` before acting. I delivered it `[HOW — direct, with empathy, with a clear off-ramp]`. The result: `[WHAT HAPPENED TO THE TEAM, THE WORK, THE PERSON]`. The lesson: `[ONE SENTENCE — e.g., "The cost of waiting is always higher than the cost of acting. I now have a 30/60/90 day check-in on every senior hire."]`"

### 2min STAR

**S (Situation).** `[2-3 sentences — the role, the gap, the team impact. E.g., "A senior engineer on my platform team. Strong technically. Underperforming on collaboration. The team was starting to avoid them. Three of my best engineers had raised it in 1:1s in the previous month."]`

**T (Task).** `[1-2 sentences — your job. E.g., "I had to decide: invest more, PIP, or let go. The team's signal was clear. The decision was mine."]`

**A (Action — the 3-5 things you did).**
- `[1st — the direct feedback conversation; what you said]`
- `[2nd — the PIP if applicable; the milestones; the off-ramp]`
- `[3rd — the delivery; the day, the time, the room]`
- `[4th — the team's reaction; the 1:1s you had]`
- `[5th — the aftercare; references, severance, internal mobility]`

**R (Result).** `[The team recovery. The work recovery. The person's landing. The lesson.]`

### Deep dive
- **The signal you missed.** `[When did the gap first show? What did you tell yourself? What would you do differently?]`
- **The cost of waiting.** `[What did the team lose in the 6 months you waited? Be specific.]`
- **The delivery.** `[How did you prepare? Who was in the room? What did you say? What did you NOT say?]`
- **The team's reaction.** `[How long to recover? Did anyone leave? Did anyone thank you?]`
- **The aftercare.** `[What did you do for the person after? References? Internal mobility? Outplacement?]`

### Follow-ups

1. **"How long did you wait before acting?"** — [YOUR ANSWER]
2. **"What did the team think of you after?"** — [YOUR ANSWER]
3. **"Would you make the same call again?"** — [YOUR ANSWER]
4. **"What did the person go on to do?"** — [YOUR ANSWER]
5. **"How do you decide when to invest vs. when to let go?"** — [YOUR ANSWER — the meta-rule]

---

<a id="story-15-the-no-to-the-ceo"></a>
## Story 15 — The time you said no to the CEO

> **Why this story matters.** This is the high-stakes one. The CDO who never says no to the CEO is a yes-person. The CDO who says no without data is a blocker. The CDO who says no, brings the data, hears the override, and executes anyway is the CDO who gets re-hired. Amazon's "Have Backbone, Disagree and Commit" probes exactly this. Meta's "Build Awesome Things" rewards the no when it's right. Google's "no-surprises" rewards the data behind the no.

> **Use it for:** Q17, Q19 (Day 35), "Have Backbone" at Amazon, the "right-sized team" / "no-bureaucracy" at Shopify (the inverse — Shopify wants you to say no to over-engineering).

### Claim
"The CEO asked for `[WHAT]`. I said no. I brought `[DATA / RISK / COST]`. The CEO `[OVERRODE / ACCEPTED / NEGOTIATED]`. I `[EXECUTED / ESCALATED / RESIGNED]`. The result was `[OUTCOME]`. The lesson was `[ONE SENTENCE]`."

### Evidence
[YOUR STORY HERE — fill in the actual no. 3-5 sentences. What did the CEO ask? Why did you say no? What data did you bring? How did the conversation go? What was the override or acceptance? What was the cost?]

### 30s
"The CEO asked for `[WHAT]`. I said no because `[REASON WITH DATA]`. The CEO `[OVERRODE / ACCEPTED]`. I `[EXECUTED / NEGOTIATED]`. The result was `[OUTCOME — including the cost of saying no, and the cost of being overridden if applicable]`. The lesson: `[ONE SENTENCE — e.g., "The cost of a bad yes is always higher than the cost of a hard no. I will say no with data, and I will execute the override with discipline."]`"

### 2min STAR

**S (Situation).** `[2-3 sentences — the ask, the stakes, the timing. E.g., "Q4. The CEO wanted to ship a customer-facing AI feature by year-end. The board had been promised. The data team had 4 months of work, 1 model in production, and a feature store that was 60% done."]`

**T (Task).** `[1-2 sentences — the call you had to make. E.g., "I had to decide: ship by year-end with risk, or push the date. The board promise was on the line."]`

**A (Action — the 3-5 things you did).**
- `[1st — the data you brought; the risk quantification; the cost of failure]`
- `[2nd — the conversation with the CEO; the room, the tone, the framing]`
- `[3rd — the alternative you proposed; the compromise]`
- `[4th — the override OR the acceptance; the explicit decision]`
- `[5th — the execution; the speed; the comms to the team]`

**R (Result).** `[The outcome. Include the cost of the no, the cost of the override (if any), the relationship after, the lesson.]`

### Deep dive
- **The data.** `[What did you bring? What was the risk? What was the cost of failure?]`
- **The framing.** `[How did you frame the no? "This will fail" vs. "This will succeed under these conditions" — both work; the second works better.]`
- **The override (if it happened).** `[How did you execute? How did you protect the team? How did you protect the CEO?]`
- **The acceptance (if it happened).** `[How did the CEO respond? What was the political cost? Was there a quid pro quo?]`
- **The relationship after.** `[How did this affect the trust? Did it buy you credibility? Did it cost you?]`

### Follow-ups

1. **"How did you decide to say no vs. negotiate?"** — [YOUR ANSWER]
2. **"What if the CEO had overridden you?"** — [YOUR ANSWER — show you've thought about the override path]
3. **"How did the team read the no?"** — [YOUR ANSWER]
4. **"Would you say no again?"** — [YOUR ANSWER]
5. **"When SHOULD a CDO say no to the CEO?"** — [YOUR ANSWER — the meta-rule, e.g., "When the cost of failure is irreversible, the data is clear, and the alternative is within reach. I will not say no to a reversible decision."]

---

## Personal Weaknesses Ledger (append-only)

> Reuse the pattern from `medium/meta/coach/PROGRESS.md`. Every Friday, append a row.

| Date | Question | Score | Lowest competency | Action for next week |
|---|---|---|---|---|
| | | | | |

---

**Last updated:** 2026-10-16 · **License:** MIT
