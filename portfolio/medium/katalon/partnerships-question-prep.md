# Partnerships Question Prep — "Partner with Product, Engineering, Marketing, Sales, and Customer Success to deliver actionable insights and AI-ready data capabilities"

> **Purpose:** Full preparation file for the cross-functional partnership line on the role's responsibility list. Fourth in the series: `strategy-question-prep.md` · `platform-architecture-question-prep.md` · `governance-question-prep.md` · this file.

---

## The Question

- **Round:** Onsite 2 (Duke Nguyen, VP Engineering) or Onsite 3 (Rajesh Krishnan, SVP Engineering); can also surface in Onsite 1 with the technical panel
- **Source:** Job posting, line 4 of "Your Responsibilities" (`README.md`)
- **Verbatim:** *"Partner with Product, Engineering, Marketing, Sales, and Customer Success to deliver actionable insights and AI-ready data capabilities."*
- **Likely probes:**
  - "How do you create a data-driven culture?"
  - "Executives distrust the numbers. What do you do?"
  - "How do you prevent the data team becoming a report factory?"
  - "Engineering won't instrument events. What do you do?"
  - "Sales wants a lead score by Friday; data isn't ready."
  - "How do you say no?"
  - "Product and Finance disagree on active customer count."
  - "How do you measure the data team's impact?"
  - "What does AI-ready data mean?"

---

## Framework Used

- **Strategic:** **Function-First / Asset-First** — for each function, name their question, your first asset, and the ongoing rhythm
- **Anchor sentence:** *"A Head of Data turns raw product and customer events into trusted decisions and AI features, safely and cheaply, through a team people want to join."*

🔵 **Hook: "One number and one question, per function."**

---

## 60–90 Second Spoken Answer (lead with this)

> Different functions ask different questions — my job is to give each **its one number and its one question answered**. Product wants to know what drives retention. Engineering wants instrumentation that doesn't break their events and AI-ready data they can consume. Marketing wants to know which channels produce paying teams. Sales wants whom to call. CS wants who will churn.
>
> For each, I deliver a **first asset**: Product — activation definition + feature adoption dashboard. Engineering — data contracts on the top ten events + a feature/retrieval platform. Marketing — single lead-to-revenue source. Sales — PQL list inside the CRM. CS — weekly at-risk list with reasons. Finance/Exec — certified revenue model.
>
> Delivery model is **hub-and-spoke**: a central platform team owns the paved road — ingestion, semantic layer, governance, AI platform — and **embedded analysts** sit with each function for speed.
>
> The catch: I protect the team's focus with **one intake, one scoring model** (impact × confidence ÷ effort), a mandatory field "what decision changes if we have this?", and **20% capacity reserved for platform health** so we're not only firefighting. **Silent over-commitment is worse than a clear no.**
>
> AI-ready data capability means: governed context plane, evaluation harness before any model, hybrid retrieval, tenant-scoped access, citations, abstention. Internal pilot first, then product-facing.

⏱️ ~80 seconds.

---

## Function-First Asset Map

For every cross-functional partnership: **who they are → their question → your first asset → ongoing rhythm**.

| Function | Their question | First asset | Ongoing rhythm |
|---|---|---|---|
| **Product** | What drives retention? | Activation definition + feature adoption dashboard | Weekly cohort review |
| **Engineering** | Stop breaking our events. Give me AI-ready data. | Data contracts on top-10 events + feature/retrieval platform | Monthly schema review |
| **Marketing** | Which channels produce paying teams? | Single lead-to-revenue source | Weekly funnel review |
| **Sales** | Whom should I call? | PQL list inside the CRM | Daily push to CRM |
| **Customer Success** | Who will churn / expand? | Weekly at-risk list with reasons | Weekly at-risk standup |
| **Finance/Exec** | What's ARR, NRR, burn, forecast? | Certified revenue model | Monthly close |
| **Legal/Security** | Are we compliant? | PII map + DSAR runbook | Quarterly access review |

🔵 **Hook: "Give each function its one number and its one question."**

---

## Hub-and-Spoke Operating Model

```
        ┌────────────── HEAD OF DATA ──────────────┐
        │                                            │
   ┌────▼────┐  ┌──────────┐  ┌─────────┐  ┌───────▼────────┐
   │Platform │  │Analytics │  │ ML/AI   │  │ Governance &  │
   │& Reliab.│  │Engin.    │  │ Data    │  │ Privacy        │
   └────┬────┘  └────┬─────┘  └────┬────┘  └───────┬────────┘
        │            │             │              │
   ─────┼────────────┼─────────────┼──────────────┼──────
        │            │             │              │
   ┌────▼────┐  ┌────▼─────┐  ┌────▼────┐  ┌─────▼─────┐
   │Embedded│  │Embedded   │  │Embedded │  │ Embedded  │
   │Product │  │ GTM       │  │ CS      │  │ Finance   │
   │Analyst │  │ Analyst   │  │ Analyst │  │ Partner   │
   └─────────┘  └──────────┘  └────────┘  └───────────┘
```

**Rules:**
- **Central platform team = paved road** (ingestion, semantic layer, governance, AI platform)
- **Embedded analysts = daily partnership** for each function
- **Domain data products owned by domain teams, governed by central**
- **60% roadmap / 20% enablement / 20% ad-hoc** capacity split

🔵 **Hook: "Central paved road. Embedded translators. Domain ownership."**

---

## Why "Embedded Analysts" (the magic)

An embedded analyst:
- **Speaks the domain's language** — same vocabulary, same KPIs
- **Attends the team's standups** — knows when a feature ships
- **Has faster context** — answers in hours, not weeks
- **Builds trust** — answers questions once, and the team keeps coming back
- **Surfaces data needs early** — instruments before launch, not after

The **risk** they fix: dashboard teams that build "what data thinks Product wants" instead of what Product actually needs.

🔵 **Hook: "Domain trust is the product. Anything else is a report factory."**

---

## Intake Model (one intake, one scoring model)

- **Mandatory field:** *"What decision changes if we have this?"*
- **Scoring:** impact × confidence ÷ effort (RICE-style)
- **Routing:**
  - One-off question → self-service or Slack answer
  - Recurring question → dashboard or metric
  - Strategic ask → roadmap
- **Publish the ranked backlog** so trade-offs are transparent
- **Reserve ~20% capacity** for platform health

🔴 **Trap:** "I'll take the request and prioritize later" — silent over-commitment kills the team.

---

## AI-Ready Data Capability (the AI part of the line)

When asked "what does AI-ready data mean?", answer in **four categories**:

| Capability | What it means | Concrete deliverable |
|---|---|---|
| **Product features** | Customer-facing AI in the product | RAG over docs, agents, in-app AI |
| **Internal productivity** | AI for the team itself | Code review, doc Q&A, text-to-SQL |
| **Model training** | Governed training corpora + eval sets | Curated, versioned, opt-in only |
| **Retrieval context** | Tenant-filtered, citation-tracked | Vector index with row-level policy |

🔵 **Hook: "Four kinds of AI-readiness. Build the evaluation harness before any model."**

---

## Common Probes — Pre-Rehearsed Answers

### Q1: "How do you create a data-driven culture?"

🟢 *"Make good data easy and bad data visible. Easy: certified datasets, a semantic layer so definitions agree, dashboards people actually open, embedded analysts who sit with each function. Visible: freshness + quality badges, a public glossary, a regular 'metrics review' where leadership uses the same numbers. Teach: office hours, short trainings. Lead by example — my own recommendations always show the data, the assumption, and what would change my mind."*

### Q2: "Executives distrust the numbers. What do you do?"

🟢 *"Trust is rebuilt with consistency and transparency. Find the 3 most-argued metrics, document a single definition for each with Finance + the business owner, publish it in one certified place, retire the rival versions. Add freshness + quality indicators on the dashboard, visible changelog. When a number is wrong I tell people first, explain, fix root cause."*

### Q3: "How do you prevent the data team from becoming a report factory?"

🟢 *"Deflect repeatable questions to self-service. Publish certified datasets + semantic layer. Intake that asks which decision it supports. The team's time goes to ~60% roadmap / 20% enablement / 20% ad-hoc. Every repeated question becomes a dashboard or a metric. Measure dashboard adoption, not dashboards built."*

### Q4: "Engineering won't instrument events properly. What do you do?"

🟢 *"Make it their win. Don't ask for 'more tracking' — show them what's broken in the data and what it blocks (e.g. 'we can't tell if the new feature works'). Provide a tracking plan template, SDK helpers, schema checks in CI so instrumenting is minutes. Agree the top ten events first. Escalate through the product lead with the business cost of not having the data."*

### Q5: "Sales wants a lead score by Friday; the data isn't ready."

🟢 *"Offer a thin, honest version: a rules-based PQL score from 3 signals we trust (team size, test runs in first 14 days, number of integrations), clearly labelled v0, with a plan to move to a model once data quality allows. Deliver value fast without overpromising, and agree how we'll measure whether it helps (conversion of scored vs unscored)."*

### Q6: "How do you say no?"

🟢 *"'Yes, and here's the trade-off.' Show the ranked backlog, what would be delayed, what the requester gains. If it's still the top priority for the business, I reprioritize openly. Silent over-commitment is worse than a clear no."*

### Q7: "Product and Finance disagree on active customer count. How do you resolve it?"

🟢 *"Reconcile from the top. Same definition? Same source? Same grain + filters? Same time zone + cutoff? I bisect by slicing both numbers by month + segment until the gap localises, then trace lineage. Long-term fix: one certified model in the semantic layer; both sides point to it. Until that's done, document both definitions and the gap."*

### Q8: "Engineering wants streaming; Finance needs daily accuracy. How do you prioritize?"

🟢 *"Both. Streaming for the use cases where freshness drives decisions (alerting, in-app personalization). Batch for everything else. Cost is the tie-breaker: stream where the incremental decision value exceeds the 3-5x ops+infra premium. Tell Finance the streaming decision enables $X in conversion; tell Engineering the streaming stack is paid for, not blocked."*

### Q9: "How do you influence a team that doesn't report to you?"

🟢 *"By being useful. Show up with insights they didn't ask for. Instrument their events before they ask. Fix a dashboard they hate. Build trust one small win at a time. Then when I need a schema change or a behavior change, the team listens because we've earned it. Influence is leverage built over time, not authority asserted."*

### Q10: "How do you measure the data team's impact?"

🟢 *"Outcomes, not outputs. Revenue influenced (with control group). Decisions reversed because of data. Hours saved via self-service. Trust-score survey (quarterly). MTTR on incidents. Time-to-onboard a new governed source. Adoption: weekly active users of dashboards, % dashboards on certified metrics. Cost per active tenant / per million events."*

### Q11: "How do you handle a high-performing leader who resists governance standards?"

🟢 *"Make governance remove work, not add it. Show how the paved road (catalog, lineage, quality tests, RBAC) makes *their* job easier. If they still resist, the failure is mine — either the standard is wrong, or I haven't made the value clear. If after that they still won't align, that's an executive conversation, not a data-team one."*

### Q12: "How do you communicate a material data incident to executives?"

🟢 *"Business language first: what decision was affected, for whom, for how long. Then technical root cause, contained to one slide. Then prevention — what control prevents recurrence, with an owner and a date. Open with impact, end with prevention; the technical detail goes in appendix. Same shape externally to customers if it's user-visible."*

### Q13: "A PM and a Finance VP both want the same data team member next quarter. How do you resolve it?"

🟢 *"Show the same scoring model to both. Higher impact × confidence ÷ effort wins. If it's a tie, ask: which delay hurts the business more? Sometimes the answer is split: shared analyst with clear allocation, or temporary staffing while the high-priority work finishes. Document the trade-off; let the executive sponsor decide if it's still close."*

### Q14: "How do you handle a stakeholder who wants to bypass governance for speed?"

🟢 *"Don't say no. Ask what they need and when. Find the paved-road way to deliver in time. If the request genuinely can't be done safely in the timeframe, say so with options: scope down, extend timeline, take the risk with documented exception. Silent bypass is worse than a documented exception. Always log the exception with an expiry."*

---

## Common Traps (red-flag answers)

- ❌ "I meet with each team monthly" — that's reporting, not partnering
- ❌ "The analysts know what the team needs" — without intake discipline, they build what's asked, not what's needed
- ❌ "We built it once and they use it" — partnership is ongoing, not a project
- ❌ "AI-ready means we have a vector DB" — AI-ready means **evaluation harness + governance + retrieval quality**, not tools
- ❌ "I'll take the request and prioritize later" — silent over-commitment kills the team
- ❌ "Yes, of course, whatever you need" — they want a partner, not a yes-machine
- ❌ Inventing adoption metrics you can't defend

---

## Three Things Katalon Is Hiring For (tied to this line)

Per Section 1 of `Katalon_Head_of_Data_Interview_Prep.md`:

1. **Builder-leader** — hands-on credible. *Demonstrated by:* drawing the platform + reviewing actual SQL.
2. **AI-readiness owner** — RAG, eval, governance. *Demonstrated by:* owning the AI plane design + governance.
3. **Cross-functional translator** — speak CFO / lawyer / engineer in one afternoon. *Demonstrated by:* this line of the role.

🔵 **This line of the role IS the third signal. Treat it as a leadership story, not a checklist.**

---

## Practice Log

| Date | Time | Mode | Self-score (1–4) | Notes |
|---|---|---|---|---|
| | | (cold / timed / peer) | | |
| | | | | |

---

## Linked Material

- **Main prep doc:** `Katalon_Head_of_Data_Interview_Prep.md` Sections 1, 11, 18, 19
- **Sister files:**
  - `strategy-question-prep.md` (line 1: Define and execute enterprise data strategy)
  - `platform-architecture-question-prep.md` (line 2: Build and scale modern data platforms)
  - `governance-question-prep.md` (line 3: Establish enterprise-wide governance)
  - `example-question-prep.md` (template)
- **Stories bank:** Section 21 — find stories tagged "cross-functional" / "executive influence" / "disagreement"
- **Flashcards:** Section 23
- **Scoring rubric:** Section 20

---

## Checklist Before Walking In

- [ ] 90-second answer said aloud, no notes
- [ ] Function-First asset map drawn from memory
- [ ] Hub-and-spoke diagram drawn in <2 min
- [ ] "How do you say no?" answer ready
- [ ] "Executives distrust the numbers" answer ready
- [ ] "Engineering won't instrument events" answer ready
- [ ] "AI-ready means…" answer ready (four categories)
- [ ] One real cross-functional story (S5) from your own career
- [ ] No invented adoption metrics

---

## Closing Sentence (if asked "anything else?")

> My job is to be the translator — same conversation in the morning with a CFO about cost, in the afternoon with a lawyer about GDPR, in the evening with an engineer about partitions. **Trust is built one small answer at a time, in business language**, and the data team earns the room by delivering those answers with no surprises.