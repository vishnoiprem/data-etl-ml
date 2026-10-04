# Strategy Question Prep — "Define & Execute Katalon's Enterprise Data Strategy"

> **Purpose:** Full preparation file for the #1 line on the role's responsibility list. Copy structure for other strategy questions. One file per question keeps prep atomic and reviewable.

---

## The Question

- **Round:** Onsite 2 — Duke Nguyen (VP Engineering) or Onsite 3 — Rajesh Krishnan (SVP Engineering)
- **Source:** Job posting, line 1 of "Your Responsibilities" (`README.md`)
- **Verbatim:** *"Define and execute Katalon's enterprise data strategy to support business growth, product innovation, and AI initiatives."*
- **Likely probes:**
  - "How would you define data strategy?"
  - "What's your 100-day plan?"
  - "How do you prioritize across Product / GTM / CS?"
  - "How do you prove ROI?"
  - "What's your North Star?"
  - "Build vs buy?"
  - "How do you say no?"

---

## Framework Used

- **Strategy:** **W-N-N** = What is true today → Near-term wins → North-star
- **Anchor sentence:** *"A Head of Data turns raw product and customer events into trusted decisions and AI features, safely and cheaply, through a team people want to join."*

---

## 60–90 Second Spoken Answer (lead with this)

> I'd start from the **decisions** the company needs to make better — not from the technology. For Katalon that means: which trial teams will convert, which accounts are at risk, which AI features customers actually use, and how we can safely learn from usage to make the product better.
>
> For each top decision, I'd name an owner, a metric, and the minimum data needed. That produces a prioritized use-case list. Then I'd build the smallest platform slice that supports those top 5 — not a full lakehouse on day one.
>
> Execution has three layers: **people** (team topology, skills, operating model), **platform** (ingest, store, transform, serve, observe), and **govern** (quality, security, privacy, AI). I prioritize top-down: pick the use case first, then the platform slice.
>
> In 90 days: a shared strategy, 3–5 trusted executive KPIs, SLOs on Tier-1 data, one lighthouse AI use case with offline + online evals, and a team operating model that gives domains ownership while the central team provides the paved road.
>
> The success measure isn't dashboards shipped — it's decisions made faster and better, and verified time-to-value for AI features.

⏱️ ~85 seconds at calm pace. Stop there unless they ask for more.

🔵 **Hook: "Decisions, not dashboards."**

---

## The 5-Layer Strategy Stack

```
5. VALUE      → use cases with owners and $ targets
4. ENABLE     → self-service, semantic layer, experimentation, ML platform
3. GOVERN     → quality, security, privacy, AI governance
2. PLATFORM   → ingest, store, transform, serve, observe
1. PEOPLE     → team shape, skills, operating model
```

**Build bottom-up, prioritize top-down:**
- Pick the **value use case** first.
- Then build the **thinnest platform slice** that supports it.
- Governance is built in from day 1 — never bolted on.

---

## W-N-N Breakdown

### W — What is true today (Days 1–30)

You must *not* assume — Katalon's current state is unknown to you. Frame this as discovery, not analysis:

| What to find | How |
|---|---|
| Existing stack (sources, pipelines, warehouses, BI tools) | Audit + 1:1s with platform leads |
| Top decisions made weekly + their data pain | Interview function heads (Product, Eng, GTM, CS, Finance, Sec) |
| Existing data team — size, shape, skills, gaps | Org chart + 1:1s |
| Cost — tools + cloud consumption + people | Vendor bills + FinOps report |
| AI features in flight | Product roadmap |
| Compliance obligations (SOC 2, ISO 27001, GDPR, CCPA) | Security/Legal review |
| Trust score — do execs trust the numbers? | Survey + ask in interviews |

**Deliverable:** *current-state map* + *risk register* by day 30.

---

### N — Near-term wins (Days 31–90)

One visible win per month that builds trust:

| Window | Theme | Concrete deliverable |
|---|---|---|
| **Days 1–30** | Listen | Inventory + decision-pain list + first trust signal |
| **Days 31–60** | Fix & prove | One agreed definition for 3–5 exec KPIs + SLOs on Tier-1 tables + cost baseline + 1 dashboard that replaces a spreadsheet |
| **Days 61–100** | Plan | Now/next/later roadmap with cost & ROI + governance charter + 1 AI pilot with measurable success metric + first 2–3 hires |

🔵 **Hook: "Listen, Fix, Plan."** Never propose a migration in the first 30 days.

---

### N — North-star (12–24 months)

**Hypothesis (validate, don't dictate):**

> **"Weekly active teams executing automated tests that complete successfully and feed decisions."**

Decomposed into a **metric tree**:

```
Weekly active teams (NS)
├── Adoption
│   ├── New teams
│   ├── Activation (first successful test in 7 days)
│   ├── Activation quality (depth: integrations + modules used)
│   └── Retention (4/8/12-week)
├── Quality outcome
│   ├── Time to detect a meaningful failure
│   ├── Time from failure to verified fix
│   ├── Release-blocking defect escape rate
│   └── Flakiness trend
├── Reliability / trust
│   ├── Data product SLO attainment
│   ├── AI groundedness + override rate
│   └── Incident MTTR
└── Business outcome
    ├── Trial → paid conversion
    ├── NRR / GRR
    ├── Expansion
    ├── CAC payback
    └── Cost to serve
```

A Head-level answer ends with: *"I'd validate that this NS predicts renewal before locking it in."*

---

## The Operating Model (hub-and-spoke)

```
                  Head of Data
   ┌─────────────┼─────────────┬──────────────┐
   │             │             │              │
 Data Platform  Analytics   Applied ML /   Governance &
 & Reliability  Engineering  AI Data        Privacy
 (ingestion,    (dbt,       (features,      (shared with
 orchestration, semantic    retrieval,     Sec/Legal)
 lakehouse,     layer,      evaluation,
 reliability)   certified    model ops)
                metrics)
```

──────────── **EMBEDDED**: product analysts, GTM analysts, CS analysts ────────────

**Rules:**
- **Foundations first** — platform + analytics engineering before ML/AI hires
- **Central team owns the paved road; domains own the data products**
- **Embedded analysts** for daily partnership; **central team** for standards + tooling

**Hiring order (first 12 months):**
1. Senior data-platform/reliability lead (if ingestion/trust is the bottleneck)
2. Analytics engineering lead (if metric inconsistency blocks decisions)
3. Embedded product analyst
4. ML platform/evaluation lead (when AI products need shared foundations)
5. Governance lead (paired with engineering, not a policy silo)

---

## Katalon-Specific Anchors

Anchor on public facts. State as hypothesis, then ask them to correct:

| Katalon signal (public) | Strategy implication |
|---|---|
| 30,000+ teams, 80+ countries | Multi-region residency, scale > SaaS startup; design for sparse vs heavy tenants |
| AI-augmented testing is core product | **Data quality = product quality**; AI plane is non-negotiable |
| AWS hosting (public docs) | Lean AWS-native; MSK, MWAA, Redshift/Snowflake on AWS, Bedrock for GenAI |
| MCP server exposed publicly | Test-management artifacts are queryable by AI tools → governance under AI exposure |
| Fortune Global 500 customers | Enterprise compliance, audit, residency, BYOK, deletion SLA are table stakes |
| "Hybrid testers" (manual + automation + AI) | Multi-modal usage signals; product telemetry is rich, varied, and worth instrumenting well |
| True Platform analytics | Existing product surface — know it before designing against it |
| Test quality metrics (flakiness, slow, new-failure) already shipped | AI plane can build on existing signals — start with measurable extension, not greenfield |

🔵 **Hook: "AI is the product. Data quality IS product quality."**

---

## ROI Story (how you prove it's working)

Three buckets — say these aloud:

1. **Revenue:** conversion lift, expansion, churn reduction — with a control group.
2. **Efficiency:** analyst hours saved, requests deflected by self-service, infrastructure cost per query.
3. **Risk:** audit findings, privacy incidents avoided, data-quality incidents prevented.

Always agree **baseline with Finance before the project starts** — so the dollar number is credible.

🔴 **Trap:** measuring pipelines built. That's output, not outcome.

---

## Likely Strategy Questions & Model Answers

### Q1: "How do you define data strategy for a company like Katalon?"

🟢 *"I start from the business goals — growth, retention, AI differentiation — and translate each into decisions data should improve. For each decision I name an owner, a metric, and the minimum data needed. That produces a prioritized use-case list. Then I size the platform and governance work for the top five — not for everything. I review quarterly against outcomes: revenue influenced, hours saved, cost to serve."*

🔴 **Trap:** starting with technology ("we need a lakehouse").

### Q2: "How do you prioritize across Sales, Marketing, Product?"

🟢 *"One intake, one scoring model: impact × confidence ÷ effort (RICE). Mandatory field: 'what decision changes if we have this?' One-off questions → self-service. Strategic asks → roadmap. Publish the ranked backlog so trade-offs are transparent. Reserve ~20% capacity for platform health so the team isn't only firefighting."*

### Q3: "How do you prove data is delivering ROI?"

🟢 *"Three buckets. Revenue — conversion lift, expansion, churn reduction attributed with a control group. Efficiency — analyst hours saved, requests deflected by self-service, infrastructure cost per query. Risk — audit findings, privacy incidents, quality incidents avoided. I agree the baseline with Finance up-front so the number is credible."*

### Q4: "What's your North Star for a testing platform?"

🟢 *"Hypothesis: 'Weekly active teams executing automated tests.' It captures both adoption and real value — teams only run tests regularly if the product works. Supporting metrics: activation rate, depth (tests per team, CI integrations), retention. Commercial layer: trial-to-paid, NRR, expansion. I'd validate it predicts renewal before locking it in."*

### Q5: "Build vs buy for data tools?"

🟢 *"Buy commodity, build differentiators. Ingestion connectors, orchestration, observability → usually buy unless cost flips. Build where data is the product edge: AI features, domain-specific models, key metric logic. Decision rubric: strategic differentiation, 3-year TCO including people, time to value, lock-in/exit cost, security fit. One-page decision record."*

### Q6: "What would you do in your first 90 days?"

🟢 *"First 30 I listen: every function head, plus inventory of sources, pipelines, dashboards, spend. I ask what 10 decisions are made every week and what data backs them. Days 30–60 I fix what hurts most: one agreed definition for the executive KPIs, quality checks on Tier-1 tables, cost baseline. By day 100 I present a now/next/later roadmap for data and AI with cost and ROI, governance charter, hiring plan, and one AI pilot with a measurable success metric. I avoid big migrations early because trust is built by small, visible wins."*

🔴 **Trap:** "I'd migrate everything to X" in the first answer.

### Q7: "How do you communicate a 1-year investment case?"

🟢 *"Headcount, platform cost, expected outcomes, risks — anchored in dollar terms. Example shape: 'Year-1 platform investment $X delivers $Y in conversion lift, Z% analyst hours saved, and reduces audit-prep time by W weeks. Risk: leadership changes, vendor lock-in. Mitigation: open formats, exit plan, named business owners.'"*

### Q8: "How do you handle pushback from Finance on a data project?"

🟢 *"Show the alternative cost. If Finance says no to a churn model, ask: what's the cost of CSMs working from gut feel? What's the lost ARR from one missed churn we could have caught? Same for cost levers: showing dollars-per-query is more persuasive than technical elegance. If Finance is still saying no, defer the project, don't hide it."*

### Q9: "How do you say no to a request?"

🟢 *"I say 'yes, and here's the trade-off.' Show the ranked backlog, what would be delayed, what the requester gains. If it's still the top priority for the business, I reprioritize openly. Silent over-commitment is worse than a clear no."*

### Q10: "How do you handle a high-performing leader who resists governance standards?"

🟢 *"Make governance remove work, not add it. Show how the paved road (catalog, lineage, quality tests, RBAC) makes *their* job easier. If they still resist, the failure is mine — either the standard is wrong, or I haven't made the value clear. If after that they still won't align, that's an executive conversation, not a data-team one."*

---

## Common Traps (red-flag answers)

- ❌ "I'd migrate everything to Snowflake" on day 1
- ❌ "We need a lakehouse" before any use case is named
- ❌ Picking a North Star without saying "I'd test it first"
- ❌ Output-focused success measures ("X pipelines built")
- ❌ "Governance is Legal's job"
- ❌ Inventing Katalon's stack, traffic, or your past metrics
- ❌ Silent over-commitment ("yes" to everything)

---

## Practice Log

> *Track reps. Practice until each answer is ≤90s.*

| Date | Time | Mode | Self-score (1–4) | Notes |
|---|---|---|---|---|
| | | (cold / timed / peer) | | |
| | | | | |
| | | | | |

---

## Linked Material

- **Main prep doc:** `Katalon_Head_of_Data_Interview_Prep.md` Section 4 (100-day plan), Section 5 (architecture), Section 18 (strategy + operating model), Section 19 (stakeholders)
- **Stories bank:** Section 21 — fill `[BLANK]`s with your own real numbers; private versions in `Katalon_Stories_PRIVATE.md`
- **Flashcards:** Section 23
- **Scoring rubric:** Section 20
- **Template used:** `example-question-prep.md` (same structure)

---

## Checklist Before Walking In

- [ ] 90-second answer said aloud, no notes
- [ ] 100-day plan (Listen / Fix / Plan) said in 60 sec
- [ ] Three KPI candidates for North Star + how you'd validate
- [ ] ROI buckets (Revenue / Efficiency / Risk) named with examples
- [ ] Build vs buy rubric stated
- [ ] "How do you say no?" answer ready
- [ ] "What would you stop doing?" answer ready (Q12 from prep doc Section 16)
- [ ] No invented numbers / stack claims
- [ ] Three questions ready to *ask* Duke/Rajesh — see `Katalon_Head_of_Data_Interview_Prep.md` Section 22

---

## Closing Sentence (if asked "anything else?")

> My goal would be to make trusted data and safe AI a **product capability** for Katalon, not a collection of pipelines — measured by faster customer outcomes, better decisions, lower operational risk, and a platform teams can adopt without waiting on the central data group.