# Rounds 3–6 — Detailed Model Answers

**Role:** Data & Analytics Lead, Google Cloud Consulting (Singapore)
**Covers:** Round 3 (case study), Round 4 (leadership), Round 5 (Googleyness), Round 6 (executive). Rounds 1–2 are in `ROUND_1_RRK.md`, `ROUND_1_RRK_TOPIC_DEEP_DIVE.md`, `ROUND_1_RRK_MOCK_10.md` and `ROUND_2_TECHNICAL_ARCHITECTURE.md`.
**Public-repo safe:** every personal fact is a `[YOUR …]` placeholder. Fill from private notes. Say only numbers you can defend (baseline, method, your role). Anonymise employers and customers.

---

## 0. Review of the Existing Round 3–6 Docs (what was weak, what this file fixes)

| Doc | Finding | Fix here |
|---|---|---|
| `ROUND_4_LEADERSHIP.md` | Story bank is 8 empty rows; no model answers or "likely question" answers | §2 gives worked structures and 6 full answers |
| `ROUND_5_GOOGLEYNESS.md` | Same: prompts only; "failure" story is the known weak spot | §3 gives answers incl. a failure template that scores |
| `ROUND_6_EXECUTIVE.md` | One-pager is a skeleton; no answers for 40% growth, decline-an-engagement, GenAI | §4 gives full answers and a filled one-pager |
| `ROUND_3_CASE_STUDY.md` | Good frameworks, but its figures are illustrative — the scenario prompts ("200 TB", "9 months", "$150K vs $50K/month", "40% reduction in 60 days") read as if fixed | §1 keeps the logic, states assumptions, replaces fixed claims with ranges |
| `HOW_TO_PASS.md` | Placeholder metrics ("hired 15", "$5M practice") look like facts | Replace with your own verified numbers or drop |

**Universal answer shapes used below**
- Hypothetical: **Understand → Prepare → Options → Recommend → Support**.
- Behavioural: **STAR + Reflection** (S 15s, T 10s, A 60s with "I", R 20s with a metric, Reflection 15s).
- Engagement: **Discover → Design → Deliver → Operate**; migration: **Assess → Plan → Migrate → Validate → Optimise**.

---

## 1. Round 3 — Case Study (consulting delivery)

### Case 1. Teradata/Oracle 200 TB → BigQuery, 9-month contract-expiry deadline, SI partner involved

**Understand (say these questions aloud)**
- Is 9 months a *hard* date (licence expiry, penalty) or a target? What's the cost of a 3-month extension of the old licence? (This sets the whole risk posture.)
- How many workloads are actually used? (Typically a large share of tables and reports are dead; usage logs tell you.)
- Who consumes it: reports, downstream apps, data science, external feeds? What are the SLAs?
- Regulatory/residency limits? Skills in the customer team? What has the SI already committed to?

**Prepare** — what I'd ask for and from whom: query/job logs (usage-based inventory), schema and object counts, ETL tool inventory, report inventory, data volumes by domain, SLAs, the SI statement of work, licence terms, the sponsor's success criteria.

**Options**
- A. *Lift-and-shift with automated SQL translation, minimal redesign*: fastest, preserves tech debt, risk of poor BigQuery cost/performance.
- B. *Wave-based replatform with selective refactor*: translate and migrate by domain, refactor only the high-value/high-cost workloads, retire the unused.
- C. *Full rebuild*: best end-state, will not fit 9 months.

**Recommend B**, with a "licence-extension option" negotiated as insurance. Rationale: it protects the date, bounds risk to one wave at a time, and avoids paying twice to refactor everything.

**Plan (illustrative; present ranges, state assumptions)**
| Phase | Timing (approx.) | Output |
|---|---|---|
| Assess | Weeks 1–6 | Usage-based inventory, retire list, complexity score, wave plan, target architecture, TCO baseline |
| Foundation | Weeks 4–8 (overlaps) | Landing zone, IAM, networking, CMEK, org policies, CI/CD, reconciliation framework |
| Wave 1 (lighthouse) | Weeks 8–16 | One domain end-to-end, parallel run, KPI parity, cutover, runbook |
| Waves 2–N | Weeks 14–32 | Factory execution by the SI under our design authority and QA gates |
| Final cutover + decommission | Weeks 30–36 | Licence exit, rollback window closed, hypercare |

**Roles:** We (Google Cloud Consulting) own architecture, migration method, quality gates and accelerators; the **SI** supplies factory delivery capacity; the **customer** owns data decisions, UAT, and run.

**Validation:** per table: row counts, per-column checksums/aggregates, sampled row diffs, then business-KPI parity over at least one month-end; automated, with a reconciliation report as the acceptance artefact.

**Risks and mitigations**
| Risk | Mitigation |
|---|---|
| Hidden consumers / undocumented feeds | Query-log analysis; consumer sign-off per wave |
| SQL dialect and semantic differences (NULL ordering, implicit casts, dates) | Migration Service translator + test suites per rule; edge-case library |
| BigQuery cost shock after cutover | Partition/cluster standards, reservations modelled from usage, `maximum_bytes_billed`, labels |
| SI quality / junior substitution | Named roles in SOW, code-review gates, defect SLAs, acceptance by validated waves not hours |
| Customer team can't run it | Enablement plan, runbooks, pairing, handover criteria |
| No decommission → double running costs | Hard decommission milestone with owner |

**Success criteria:** zero Sev-1 data discrepancies at cutover, KPI parity for N cycles, licence exit on the date, run cost within [x]% of the modelled TCO, adoption by named users.

**Go/no-go gates:** end of Assess (is the plan credible?), after Wave 1 (does the factory reproduce quality at speed?), before final cutover (parity + rollback ready).

### Case 2. Failed migration by another partner; client distrusts everyone

> "Trust is the first deliverable, so I won't pitch a solution on day one.
> **Listen and diagnose (2 weeks, small paid or no-regret scope):** interview business and IT, review what was delivered, quantify the data-quality defects, find the root causes (scope, testing, governance, skills), and separate *what's salvageable* from *what must be redone*.
> **Rebuild credibility with proof, not promises:** a small, tightly scoped win in 4–6 weeks (fix the most painful data-quality problem, with a reconciliation report the business can verify), then widen.
> **Change the controls that failed:** independent validation owned jointly with the business, weekly demos with their users, defect transparency, a joint steering committee with decision rights.
> **Commercial structure:** milestone-based commitments tied to validated outcomes, so risk is shared.
> **Don't** disparage the previous partner; present findings neutrally and factually."

### Case 3. Greenfield Customer 360 + real-time personalisation, $3M, 12 months, strong engineers but little data experience

> "**Outcome first:** what business metric moves (conversion, retention, margin) and what's the personalisation decision and its latency need? **Phase it:** (1) 8–10 weeks: identity resolution and a unified customer profile with batch segments (value early), (2) streaming events + feature serving, (3) real-time decisioning and experimentation. **Architecture:** Pub/Sub + Dataflow for events, BigQuery for the profile and features, Vertex AI for models and serving, Looker for measurement; consent and PII governed with DLP, policy tags and CMEK. **People:** because the customer is strong on engineering but light on data, I'd staff for enablement: paired delivery, shared standards, and a clear transition plan. **Risks:** identity-resolution quality, consent management, over-building real-time before the business can act on it. **Measure:** uplift from controlled experiments, not model accuracy alone."

### Case 4. Cost crisis: 3× estimate, CFO wants –40% in 60 days

> "**Week 1: visibility.** Billing export, labels, `INFORMATION_SCHEMA.JOBS`, top spenders by service, project, team, query. **Weeks 1–3: no-regret savings:** delete unused tables/dashboards/schedules, add `require_partition_filter` and `maximum_bytes_billed`, fix the top 10 expensive queries, set table expiry, move cold storage to cheaper classes, right-size Dataproc/Dataflow, use Spot VMs. **Weeks 3–6: structural:** partition/cluster the big tables, reservations/Editions sized from slot-usage history with separate ETL/BI/ad hoc reservations, materialised views for repeated aggregates. **Sticking:** budgets and alerts, showback by team, cost lint in CI. **Be honest about the target:** –40% may be achievable but I'd model it first and not promise a number I can't show; I'd also protect SLAs the business depends on. A saving that degrades an SLA is deferred cost."

### Case presentation format (15 min + 10 min Q&A)
1. Restate the problem and outcome (1 min). 2. Assumptions and open questions (1 min). 3. Options with trade-offs (3 min). 4. Recommendation and architecture (4 min). 5. Plan, phases, gates, roles (3 min). 6. Risks, KPIs, commercials (2 min). 7. Ask: decisions needed from the sponsor (1 min).

**Case Q&A traps:** "Why not Snowflake/Databricks?" (answer by customer need, not loyalty); "What if the SI is late?" (gates, escalation, capacity buffer); "What if the date is fixed?" (cut scope, not validation); "How do you price it?" (phased, discovery fixed, delivery capped/T&M with ranges).

---

## 2. Round 4 — Leadership (STAR answers)

Fill the brackets from real experience. The structure is the answer; the details are yours.

### L1. "Tell me about the hardest hire you made and how you decided."
> **S:** I needed a [senior data architect] for [a platform of X scale]; two finalists, one stronger on technical depth, one stronger on client leadership.
> **T:** Hire for the role's real gap without lowering the bar.
> **A:** I wrote the **scorecard first** (technical judgement, client influence, ownership, coaching), ran structured interviews with the same questions, added a **work-sample** (a design review on a real problem), and checked references on the specific gap. When the panel split, I weighed which gap I could coach: depth can be built faster than judgement and ownership, so I chose [the candidate with judgement]. I told the other finalist why, with feedback.
> **R:** [Hired person reached full productivity in X months; led Y; retained Z]. **Reflection:** I'd [involve a peer architect earlier to test technical depth].

### L2. "Describe a time you put someone on a PIP."
> **S:** A senior [engineer] consistently missed [design quality / delivery] against the level expectations; peers were compensating.
> **T:** Give a fair chance to recover while protecting delivery.
> **A:** I gathered specific, dated evidence against the written expectations, held a direct private conversation to hear their view and obstacles (I removed [the blocker I owned]), agreed a 60–90-day plan with measurable outcomes, weekly check-ins, a mentor, and documented it with HR. I never surprised them: every checkpoint was written.
> **R:** [Either: they met the bar and were later promoted/stable, or: they left with dignity and an agreed message, team trust held]. **Reflection:** I should have had the first direct conversation [two months earlier].

### L3. "A top engineer wants a promotion but isn't ready."
> "I don't say 'not yet'; I say **'here's the gap, and here's how we close it'**. I map their work against the next level's written expectations (scope, influence, design ownership), show two or three specific gaps with evidence, and design a **stretch assignment** that exercises exactly those gaps, with a sponsor and a checkpoint in [3–6 months]. I tell them the criteria, not a date I can't guarantee. If the gap is mostly a visibility problem, I fix visibility. If they're flight-risk, I address recognition and scope now (not only title)."

### L4. "Keep a distributed team motivated through a long migration."
> "Long migrations fail on **fatigue and invisible progress**. I break the programme into wave milestones with visible demos, celebrate each cutover, rotate people between repetitive factory work and design/automation work, make the metric of progress *business outcomes unlocked*, protect the team from scope churn, and run short, honest retrospectives. I also watch for burnout signals (after-hours load, rising rework) and act early. I name the end state, including decommissioning the old platform, so the work has a finish line."

### L5. "An SI partner engineer underperforms on your engagement."
> "I separate **person** from **process**. First a factual conversation with the partner's delivery lead using defect and rework data against the agreed SLAs. Ask for a specific remediation (pairing, code-review gates, or replacement) within a set time. Protect the customer: tighten our QA gate on that workstream meanwhile. If the pattern repeats, escalate through the commercial channel and, if needed, change the allocation. I keep the relationship working, because we need the partner's capacity, but quality is non-negotiable."

### L6. "Build a career ladder for consultants vs engineers."
> "One shared **skill dimensions** framework (technical depth, delivery, client influence, leadership/multiplier effect) with level expectations per dimension. **Engineers** weight depth and delivery; **consultants** weight client influence and commercial awareness; senior levels on both converge on scope and multiplier effect. Each level has observable behaviours and example evidence, promotions are decided by a calibrated panel against evidence, and there's a **dual track** so a technical expert can grow without managing people."

### Retention / team health / diversity (short answers)
- **Retention:** know why people leave: growth, scope, manager, comp, load. Run stay-interviews, act on the top two reasons each quarter, fix inequity, give meaningful scope.
- **Diversity:** widen sourcing (structured, same-questions interviews, diverse panels), remove bias in job descriptions and promotion calibration, build sponsorship (not just mentoring), and measure pipeline and promotion rates. [Add one concrete action you took.]
- **Culture:** blameless postmortems, written decisions (ADRs), psychological safety: *I say "I was wrong" first.*

---

## 3. Round 5 — Googleyness & Leadership (STAR answers)

### G1. "Act with incomplete information."
> **S:** [A client's data platform decision had a 2-week window; half the requirements were unknown.]
> **T:** Decide without waiting for certainty.
> **A:** I listed what was known/unknown, identified the **decisions that are reversible vs irreversible**, chose a reversible option with a defined checkpoint, ran a two-week spike to retire the biggest unknown, and communicated the assumptions to the sponsor.
> **R:** [Delivered on time; two assumptions proved wrong and the reversible design let us adjust at low cost]. **Reflection:** I'd write assumptions in the decision record earlier.

### G2. "Disagreed with your manager."
> **S:** [My manager wanted to commit to a date/scope I believed was unsafe.] **T:** Raise it without damaging trust.
> **A:** I asked to understand their driver, brought evidence (estimate, risks, similar past effort), proposed options, and made the disagreement about the **goal**, not the person. After the decision, I committed fully.
> **R:** [Outcome]. **Reflection:** I'd bring the data in the first conversation, not the third.

### G3. "A failure you're still thinking about." (the highest-value story — must be real)
Structure that scores (genuine, specific, owned, changed):
> **S:** [Real situation with real stakes.] **T:** [My responsibility, stated plainly.]
> **A (what I got wrong):** "I was wrong because **I** [assumed X without testing it / didn't escalate Y in time / chose speed over a control Z]." *No blame on others, no 'I cared too much'.*
> **R:** [The real cost: delay, wrong data, lost trust, money.] **What I changed:** [a concrete mechanism: a checklist, a contract test, an escalation rule, a review gate], and **[evidence it worked since]**.
> **Reflection:** the principle I now apply.

**Avoid:** a strength disguised as a weakness; blaming a team; a failure with no consequence; a rehearsed-sounding humility.

### G4. "How did you get a team you don't manage to follow your direction?"
> "Influence without authority is **shared goal + evidence + making their job easier**. I find what each party is measured on, tie the change to their goals, use data to show the problem, run a small pilot to reduce their risk, give credit publicly, and agree decision rights. [Example: moved three teams to a common data contract by showing incident cost and doing the first integration for them.]"

### G5. "Changed your mind because of someone else's input."
> "[Situation where a junior engineer/peer challenged my design.] I tested their point against the evidence, found they were right about [the failure mode], said so openly, changed the design, and credited them in the decision record. It also changed how I run reviews: I now ask for the strongest objection before approving."

### G6. "Said no to a senior stakeholder."
> "I said no to the *solution*, not the need. I asked what outcome they needed, showed the cost and risk of their option with evidence, offered an alternative that met the outcome, and agreed how we'd measure it. They [accepted/escalated]; either way, I kept the relationship by being transparent and consistent."

### Googleyness attributes checklist (have a story ready for each)
Thrive in ambiguity · challenge the status quo effectively · value feedback · put the user first · do the right thing · care about the team · mobilise others · get things done through influence · self-development.

---

## 4. Round 6 — Executive (answers)

### E1. "First 90 days?" (use the one-pager)
| Window | Actions | Measures |
|---|---|---|
| **Days 1–30 Listen** | Meet every team member 1:1, top accounts, partner leads, account teams; review pipeline, delivery health, utilisation, margin, skills map; read the last 5 post-engagement reviews | Baseline pack: pipeline, utilisation, margin, NPS/CSAT, attrition, skills gaps |
| **Days 31–60 Align** | Agree 3–4 priorities with leadership; fix the top 2 delivery risks; define KPIs and the operating cadence; start the hiring plan | Agreed KPI set; risk list with owners |
| **Days 61–90 Act** | Launch 1–2 reusable accelerators (migration assessment, reconciliation framework); first QBR with metrics; partner scorecard; hands-on Google Cloud certification booked/progress | Accelerators in use on live accounts; QBR delivered |

### E2. "Which engagements do you take or decline?"
> "A **qualification scorecard**: strategic fit (customer type, reference value), win-probability and sponsor strength, delivery risk (scope clarity, data readiness, timeline realism), commercial quality (margin, payment, change control), and team capacity. I decline or reshape work that is **fixed-price with undefined scope**, has **no executive sponsor**, or needs skills we can't staff. Declining well builds trust: *'we're not the right fit now; here's what would change that.'*"

### E3. "Grow this practice 40% in a year."
> "Growth = **more wins + higher win-rate + better pull-through + more repeatable delivery**, constrained by quality. Levers: (1) *Pipeline*: joint account plans with Google field teams, 5–8 named target accounts, repeatable offers (migration assessment, FinOps health-check, governed GenAI foundation); (2) *Conversion*: stronger discovery and proposals, reference stories; (3) *Capacity*: hire to the pipeline, use SI partners for volume work, with quality gates; (4) *Leverage*: assets and accelerators that reduce effort per engagement; (5) *Expansion*: land with assessment, expand to build and managed services. **Constraints and honesty:** growth without delivery quality destroys reputation, so I'd track margin, CSAT and on-time delivery alongside revenue, and I'd set the 40% target only after seeing the baseline pipeline and capacity."

### E4. "Where does GenAI change the data practice?"
> "Three places. (1) **Demand:** customers ask for governed AI over their data; the constraint is data readiness, quality and governance, so the data practice becomes the foundation for AI. (2) **Delivery:** GenAI accelerates code translation, documentation, testing and data-quality rule generation, shrinking migration effort, but needs human review and evaluation. (3) **Products:** semantic layers, vector search, agents over governed data tools. **Risk:** hype ahead of readiness; ungoverned corpora, prompt-injection, PII leakage. My stance: *start with a lighthouse use case, build the evaluation set first, govern the corpus, then scale.*"

### E5. "How do you measure the health of a practice?"
| Area | Metrics |
|---|---|
| Financial | Revenue vs plan, delivery margin, forecast accuracy |
| Delivery | On-time/in-budget %, defect/rework, customer CSAT/NPS, repeat business |
| People | Utilisation (healthy band, not max), attrition, promotion rate, engagement, skills coverage |
| Growth | Pipeline coverage, win-rate, expansion from lighthouse engagements |
| Leverage | Asset reuse rate, effort saved per engagement, partner-delivered share and quality |

> "The leading indicators matter most: pipeline coverage, forecast accuracy, and rework rate warn me before margin does."

### E6. "Why Google Cloud, and why this role?"
> "Three reasons: **capability fit** (large-scale streaming and warehouse work, cost and governance under a real budget, regulated APAC markets); **market thesis** (most enterprise data programmes fail on operating model and adoption, which is a consulting problem and exactly what PSO sells); and **ambition**: I want to build a repeatable capability and help a region adopt it, not run one platform. [Add one specific personal link.]"

### E7. 3-year vision (sequenced, with measures)
- **Year 1:** playbook and accelerators (assessment, migration, reconciliation, FinOps), partner scorecards, team at target size and certified. *Measure:* reuse, margin, CSAT.
- **Year 2:** managed-service and optimisation offers, governed GenAI-on-data offer, regional bench. *Measure:* recurring revenue share, pull-through.
- **Year 3:** regional leadership, productised IP, a talent pipeline with internal promotions. *Measure:* revenue and margin growth, attrition, partner-led share.

---

## 5. Ten Follow-Up Probes To Rehearse (the interviewer will use these)

1. "What exactly did *you* do versus the team?"
2. "What was the baseline, and how did you measure it?"
3. "What would have happened without you?"
4. "What did it cost, and who paid?"
5. "What went wrong?"
6. "What would you do differently?"
7. "How do you know it lasted?"
8. "What did the customer/executive actually say?"
9. "If the sponsor had said no, what then?"
10. "How would this change at 10× the scale?"

---

## 6. Coverage Map: All Six Rounds

| Round | Doc | Status |
|---|---|---|
| 1 Recruiter / RRK | `ROUND_1_RECRUITER.md`, `ROUND_1_RRK.md` (Q1–35), `…TOPIC_DEEP_DIVE.md`, `…MOCK_10.md` | Answers written; 8 `[TODO]` need your facts |
| 2 Technical | `ROUND_2_TECHNICAL_ARCHITECTURE.md` + deep-dive §15 | Answered; exactly-once fixed |
| 3 Case study | `ROUND_3_CASE_STUDY.md` + §1 above | Answered with assumptions stated |
| 4 Leadership | §2 above | Structures + answers; stories need your facts |
| 5 Googleyness | §3 above | Structures + answers; failure story must be real |
| 6 Executive | §4 above | Answered; one-pager filled |

**Honesty rule:** an answer you can't defend under three follow-ups is worse than a shorter true one.
