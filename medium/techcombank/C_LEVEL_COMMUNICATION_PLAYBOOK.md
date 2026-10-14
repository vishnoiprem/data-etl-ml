# 🎯 C-LEVEL COMMUNICATION PLAYBOOK + KPI FRAMEWORK
### For Prem Vishnoi | Director, Data Engineering | Oct 23, 2026 Roadshow

> **10-pass review applied** (clarity, brevity, actionability, KPI accuracy, C-level framing, conversation hooks, what they actually care about, sentence length, evidence anchoring, signposting).

---

# PART 1: HOW TO TALK TO C-LEVEL EXECUTIVES

## 1.1 The 7 C-Level Communication Rules

### Rule 1: **Lead with the answer, not the buildup**

C-level executives process 50+ decisions a day. They don't have patience for narrative arcs.

| ❌ Don't | ✅ Do |
|---|---|
| "So what I'd like to do is walk you through my background, and then maybe we could talk about how I see the data landscape evolving, and…" | "Three things. One: I'm here to land the lakehouse. Two: I've done it before at scale. Three: I want to know what you see as the blocker." |

**Sentence budget:** Your first sentence should be the **punchline**. The next 2-3 sentences are the **proof**. Then you stop and listen.

### Rule 2: **Use their numbers, not yours**

CFO cares about NIM, CASA, cost-to-income. CRO cares about NPL, RWA, capital adequacy. CTO cares about cloud split, transaction latency, integration debt. **Speak in their language.**

| ❌ Don't | ✅ Do |
|---|---|
| "We have 10 billion rows a day in our lakehouse" | "If we can shave 50bps off your NIM through better credit decisions, that's USD 100M+ in annual profit at your current loan book size" |

### Rule 3: **Frame everything as a choice with trade-offs**

C-level people don't want a "yes" — they want a **decision framework**. Present options, recommend one, name the trade-off.

> *"I see three ways to sequence the lakehouse build. Option A: vertical slice on regulatory reporting first — high trust, fast audit wins, slower business value. Option B: horizontal foundation first — fast for everything, slower to first value. Option C: hybrid — bronze everywhere, silver in one domain, gold in regulatory. **My recommendation: C. The trade-off is more orchestration complexity in year one, but a credible business win in Q1."***

### Rule 4: **Trade-offs > benefits**

Junior people sell benefits. Directors and C-level discuss trade-offs.

| ❌ Don't | ✅ Do |
|---|---|
| "This will reduce risk and improve outcomes" | "This will reduce risk by X but cost us Y in delivery velocity — here's how I propose to manage that" |

### Rule 5: **One slide, one decision**

If you use slides (you won't at a reception, but in any follow-up meeting), every slide has **one** decision to make. The slide's job is to make the decision easy, not to inform.

### Rule 6: **The "so what" test**

After every sentence, ask: *"So what?"* If the next sentence doesn't add information, cut it.

> ❌ *"We've built a Databricks lakehouse with bronze-silver-gold medallion architecture using open table formats and data contracts at the source boundary with PII classification at ingest."*
> ✅ *"We've built a Databricks lakehouse that cut month-end close from 5 days to 2 hours. Same pattern would work here."*

### Rule 7: **End with the question, not the statement**

The C-level person should leave the conversation **thinking about the question you asked them**, not the answer you gave.

> ✅ *"The question I'd want your view on: what's the one decision the data platform is currently blocking? Because that's where I'd start."*

---

## 1.2 The C-Level Conversation Structure (5 minutes)

| Time | What to do | What NOT to do |
|---|---|---|
| **0:00 - 0:30** | **Opener** — name, pedigree, why you're here. 1 sentence. | Don't recite your CV. |
| **0:30 - 1:00** | **The hook** — one specific Techcombank fact that shows homework | Don't say "I've read your strategy" |
| **1:00 - 1:30** | **The question** — the audience-specific one from your cheat sheet | Don't ask generic questions |
| **1:30 - 4:00** | **Listen 80%** — let them talk, take notes visibly | Don't monologue your experience |
| **4:00 - 4:30** | **Smart follow-up** — one question that goes deeper | Don't ask a second big question |
| **4:30 - 5:00** | **The closer** — "exactly the kind of problem I want to be working on" + "stay in touch" + card | Don't ask for the job |

---

## 1.3 The 4 Things C-Level Hate

1. **Vagueness** — "we could potentially look at" is a death sentence
2. **CV recitation** — they have your CV; they want your **thinking**
3. **Selling** — they're not buying; they're **deciding**
4. **Asking for the job** — you're at a reception, not an interview

## 1.4 The 4 Things C-Level Love

1. **Specifics** — numbers, names, dates
2. **Trade-offs** — you understand what you're giving up
3. **Questions** — the right question is a credibility signal
4. **Listening** — most candidates talk too much

---

## 1.5 How to Handle Each C-Suite Personality Type

### The CEO (Jens Lottner, German, customer-experience mandate)

| Trait | Implication |
|---|---|
| **International background** | Speak in international business terms, not local jargon |
| **Customer experience focus** | Translate every data story into a customer outcome |
| **New to Techcombank (2024)** | He's still learning the org — help him, don't assume he knows it |
| **Public profile** | His statements are on the record — be careful with specifics |

**How to talk to him:**
- Frame the platform as a **customer-experience enabler**, not a tech project
- Use international examples (DBS, Standard Chartered, NAB)
- Don't oversell Vietnam-specific knowledge; he's the foreigner, not you
- Reference his mandate explicitly: *"Your customer-experience mandate maps directly to what the data platform should be enabling"*

### The CFO

| Trait | Implication |
|---|---|
| **Numbers-driven** | Every claim gets a number |
| **Risk-aware** | Frame the platform as a risk reducer, not just a value creator |
| **Cost-conscious** | Show you understand the cost side of the platform |
| **Regulator-facing** | SBV compliance is their nightmare |

**How to talk to them:**
- Lead with the **financial outcome**, not the architecture
- Show you understand **FinOps** (40% cost takeout is your proof)
- Reference **audit defensibility** — they care about this
- End with the **business case**, not the tech stack

### The CTO / CIO

| Trait | Implication |
|---|---|
| **Technically literate** | You can be specific about architecture |
| **Integration-focused** | They think about how things connect, not how they stand alone |
| **Vendor-aware** | They'll know what Databricks, Snowflake, Confluent are |
| **Security-minded** | Hybrid cloud + data residency = constant tension |

**How to talk to them:**
- Be **architecturally specific** — bronze/silver/gold, contracts, lineage
- Acknowledge the **integration debt** — don't pretend it doesn't exist
- Reference **open table formats**, not just "Databricks" — shows depth
- Use **their** language: paved road, platform, contracts, SLOs

### The CRO

| Trait | Implication |
|---|---|
| **Risk-first thinker** | They see the world in probabilities, not possibilities |
| **Regulator-respectful** | SBV is the boss; everything is regulator-first |
| **Model-aware** | They think about model risk, not just data risk |
| **Audit-fatigued** | They live and die by the audit |

**How to talk to them:**
- Lead with **risk reduction**, not value creation
- Use **BCBS 239** language — it's their framework
- Reference **lineage, audit, immutability** — they live here
- Show you understand **model risk management** — not just data engineering

### The CHRO

| Trait | Implication |
|---|---|
| **People-first thinker** | They care about the team, not the tech |
| **Retention-focused** | Losing senior engineers is their KPI |
| **Pipeline-minded** | Buy vs build is the strategic question |
| **Comp-aware** | They know the market rate for senior data engineers |

**How to talk to them:**
- Lead with **team and talent**, not architecture
- Show you understand **retention math** (cost of losing senior = 2x annual salary)
- Reference **career paths** — they think in ladders
- End with **how you'd build the team**, not how you'd build the platform

### The Compliance Director

| Trait | Implication |
|---|---|
| **Regulator-first** | SBV is the customer, not the bank |
| **Process-heavy** | They think in workflows, not data products |
| **Evidence-demanding** | "Show me" is their default |
| **Inspection-anxious** | They live with the next SBV visit as a constant background worry |

**How to talk to them:**
- Lead with **inspection readiness**, not innovation
- Use **PII, residency, audit trail** language
- Reference **policy-as-code** — they may not know the term, but they'll love the idea
- End with **how the platform makes their job easier**

### The CDO / Head of Data

| Trait | Implication |
|---|---|
| **Strategy-aware** | They think in 3-year horizons |
| **Delivery-anxious** | They carry the platform delivery on their back |
| **Politics-savvy** | They navigate the C-suite daily |
| **Possibly new to the role** | If Techcombank is building the function, they may be a peer to you |

**How to talk to them:**
- Be a **peer**, not a supplicant
- Reference **shared challenges** — Hadoop modernisation, governance maturity
- Show you understand **CDO-level trade-offs** — central vs federated
- End with **how you'd work together**, not how you'd report to them

### The Head of Data Engineering & Delivery (your line manager)

| Trait | Implication |
|---|---|
| **Delivery-obsessed** | They think in sprints and SLOs |
| **People-manager** | They care about their team |
| **Politically-exposed** | They're the one who signs up for the platform promise |
| **Burned-before** | They've probably tried things that didn't work |

**How to talk to them:**
- Lead with **delivery discipline** — "I ship"
- Reference **specific scars** — "I underinvested in FinOps in year one"
- Show you understand **manager work** — "I clear blockers, I get out of the way"
- End with **how you'd complement their work**, not how you'd replace it

---

## 1.6 The 5 Magic Phrases (use sparingly)

These phrases signal Director-band thinking. Use ONE per conversation, max.

1. **"The trade-off is..."** — shows you understand choices have costs
2. **"My instinct is..."** — shows you have a point of view, not just analysis
3. **"The thing I'd want to validate before committing is..."** — shows epistemic humility
4. **"What I've learned the hard way is..."** — shows scar-based wisdom
5. **"If I were in your seat, the question I'd be asking is..."** — shows C-level thinking

---

# PART 2: THE KPIs EVERY C-LEVEL CARES ABOUT

## 2.1 The Universal 4 (every C-level tracks these)

| KPI | What it measures | Why C-level cares |
|---|---|---|
| **Customer NPS / satisfaction** | How customers feel | The brand moat |
| **Cost-to-income ratio** | Operational efficiency | The franchise leverage |
| **Time-to-market for new products** | Org agility | The competitive edge |
| **Employee engagement / retention** | Org health | The talent moat |

## 2.2 The CEO's KPIs (Jens Lottner)

| KPI | Target direction | Your platform's contribution |
|---|---|---|
| **Customer count** | Growing (toward 25M by 2030) | Acquisition + onboarding analytics |
| **Digital revenue %** | Growing (toward 80%+) | Every digital product runs on your platform |
| **NPS / DMA rank** | Hold #1 or improve | Personalisation, complaint prediction, journey analytics |
| **Strategic narrative execution** | "Techcombank 2030" delivery | You are the platform foundation for the 2030 story |
| **Brand value** | Growing | Digital experience quality |
| **Total shareholder return** | Outperform peers | NIM protection + growth via platform |

**How to talk to the CEO about KPIs:**
- Translate everything into **customer outcomes**
- Use 2030 narrative language: "If I deliver the lakehouse in 18 months, you can credibly claim the platform foundation for the 2030 story"
- Reference DMA #1: *"The data work I'd want to do would protect and extend that #1 in digital satisfaction"*

## 2.3 The CFO's KPIs

| KPI | Typical target | Your platform's contribution |
|---|---|---|
| **NIM (Net Interest Margin)** | Maintain 4.5%+ | Better credit decisions → better risk-adjusted pricing |
| **CASA ratio** | Grow 1-2pp/year | Personalisation drives engagement, engagement drives CASA stickiness |
| **Cost-to-income ratio** | Reduce to ~30% | Platform efficiency + automation (40% cloud cost takeout is your proof) |
| **ROE** | 18-22% | NIM protection + cost takeout = ROE |
| **NPL ratio** | <1.5% | Better credit scoring, better early warning |
| **Provision coverage** | Strong | Better risk prediction |
| **Capital adequacy (CAR)** | Above SBV minimum | RWA accuracy = data quality |
| **Month-end close** | Days → hours | Direct platform contribution (Makro: 5d → 2h) |

**How to talk to the CFO about KPIs:**
- **NIM** is the North Star — every claim connects to it
- **CASA** is the lever you can pull via personalisation
- **Cost-to-income** is the lever you can pull via FinOps + automation
- **Month-end close** is the visceral pain — your Makro story hits here

### The CFO Conversation Script

> **You:** "If we can shave 50bps off cost-to-income over 24 months through platform automation, that's roughly USD 100M+ in annual cost takeout at your scale. The Makro pattern: 40% cloud cost takeout, month-end from 5 days to 2 hours, 50+ executive dashboards. Same shape works here."
>
> **CFO will lean in.** Then ask: *"What's the one thing about the data you receive today that you'd want changed first?"*

## 2.4 The CTO / CIO's KPIs

| KPI | Target | Your platform's contribution |
|---|---|---|
| **Cloud adoption %** | 50-80% (over 3 yrs) | The lakehouse is the cloud workload |
| **Core banking uptime** | 99.99%+ | The lakehouse has to integrate without breaking the core |
| **Time-to-deploy new pipeline** | Days → hours | The paved road enables this |
| **Mean time to detect (data issues)** | Hours → minutes | Observability + lineage |
| **Security incidents** | Zero major | PII classification + access control |
| **Vendor consolidation** | Reduce | Lakehouse replaces point tools |
| **Tech debt reduction** | Measurable | Lakehouse modernisation replaces Hadoop |
| **Developer productivity** | +30-50% | Paved road = faster squads |

**How to talk to the CTO / CIO about KPIs:**
- Speak in **technical architecture** terms, not business outcomes
- Reference **specific tools and patterns** — bronze/silver/gold, open table formats
- Show you understand **integration debt** — they live with it
- End with **how the platform integrates with their stack**, not how it replaces it

## 2.5 The CRO's KPIs

| KPI | Target | Your platform's contribution |
|---|---|---|
| **NPL ratio** | <1.5% | Better credit scoring, early warning |
| **RWA accuracy** | Tight | Data quality for risk-weighted assets |
| **Model risk grade** | Improving | Model governance + monitoring |
| **Audit findings** | Zero major | Lineage + immutability + reproducibility |
| **SBV inspection results** | No material findings | Audit-defensible pipeline |
| **Capital adequacy (CAR)** | Above SBV minimum | Better data = better capital management |
| **Stress test results** | Robust | Better data for stress scenarios |
| **Operational risk losses** | Minimal | Data quality + observability |

**How to talk to the CRO about KPIs:**
- **Audit defensibility** is the magic word
- Reference **BCBS 239** — it's their framework
- Show you understand **immutable bronze + time travel + signed runs**
- End with **"the audit answer is a query, not a forensic project"**

## 2.6 The CHRO's KPIs

| KPI | Target | Your platform's contribution |
|---|---|---|
| **Time-to-hire (senior)** | <60 days | Employer brand + comp |
| **Voluntary attrition (senior)** | <10% | Retention math (problems + pay + pride) |
| **Engagement score** | High | Mission + impact |
| **Diversity in leadership** | Improving | Inclusive hiring |
| **Internal mobility** | 20%+ | Career path visibility |
| **Learning hours per employee** | 40+ hrs/year | L&D investment |
| **Cost-per-hire** | Decreasing | Employer brand leverage |
| **Pipeline health (juniors)** | 50%+ from internal pipeline | Graduate program |

**How to talk to the CHRO about KPIs:**
- Lead with **team and talent**, not platform
- Reference **specific retention math**: cost of losing a senior = 2x annual salary
- Show you understand **buy vs build** in talent
- End with **"how I'd build the team in 18 months"**

## 2.7 The Compliance Director's KPIs

| KPI | Target | Your platform's contribution |
|---|---|---|
| **AML alerts / false positive rate** | Low | Better data quality → better detection |
| **SBV inspection findings** | Zero material | Audit-defensible lineage |
| **KYC completion rate** | 100% | Process automation |
| **Sanctions screening hit rate** | Accurate | Better data |
| **Transaction monitoring coverage** | 100% of accounts | Real-time data |
| **Regulatory reporting on time** | 100% | Data quality + automation |
| **PII compliance** | Full | Classification + access control |

**How to talk to the Compliance Director about KPIs:**
- Lead with **inspection readiness**, not innovation
- Reference **PII, residency, audit trail** as architectural features
- Show you understand **"policy-as-code"** — they may not know the term
- End with **"the next SBV inspection should be your easiest one"**

## 2.8 The CDO's KPIs

| KPI | Target | Your platform's contribution |
|---|---|---|
| **Data governance maturity (DCAM/DMM)** | 3-4 (from 1-2) | Platform + governance tooling |
| **Data quality SLAs met** | >95% | Data contracts + quality checks |
| **Time-to-data for new use case** | Days → hours | Paved road |
| **Data products in production** | Growing catalogue | The lakehouse enables this |
| **Business self-service %** | 50%+ | Domain marts + catalogs |
| **AI/ML use cases in production** | 10+ by year 2 | The platform foundation |

## 2.9 Your Line Manager's (Head of Data Engineering & Delivery) KPIs

| KPI | Target | Your contribution |
|---|---|---|
| **Squad velocity** | Steady +30% YoY | Architecture + paved road |
| **Platform uptime** | 99.9%+ | SRE + observability |
| **Delivery predictability** | 80%+ of commitments land on time | Sprint discipline + clear scope |
| **Tech debt ratio** | Decreasing | Modernisation + retirement of legacy |
| **Team engagement** | Top quartile | Management quality |
| **Stakeholder satisfaction (NPS)** | >40 | Delivery + communication |

---

# PART 3: THE 5 KPI METRICS YOU SHOULD TRACK IN YOUR FIRST 90 DAYS

If they ask "what would you measure?", here's the answer:

| Metric | Why this one | What it tells them |
|---|---|---|
| **1. Time-to-first-insight for a new data product** | Direct measure of platform agility | How fast the business gets value |
| **2. % of pipelines with column-level lineage** | Direct measure of governance | How audit-ready the platform is |
| **3. Cloud cost per billion rows processed** | Direct measure of FinOps | How efficient the platform is |
| **4. Critical incident MTTR (mean time to repair)** | Direct measure of reliability | How robust the platform is |
| **5. Squad velocity (story points / sprint, with quality intact)** | Direct measure of team health | How the team is doing |

> **Bonus metric (6):** % of business stakeholders who can self-serve their own data. This is the ultimate measure of platform success.

---

# PART 4: THE C-LEVEL CONVERSATION CHEAT SHEET (print this)

```
┌──────────────────────────────────────────────────────────────┐
│  C-LEVEL CONVERSATION RULES — MEMORISE                      │
├──────────────────────────────────────────────────────────────┤
│  1. Lead with the ANSWER, not the buildup                    │
│  2. Use THEIR numbers, not yours                            │
│  3. Frame as CHOICES with trade-offs                         │
│  4. Trade-offs > benefits                                    │
│  5. End with the QUESTION, not the statement                 │
│  6. One sentence, one idea                                   │
│  7. Listen 80%, talk 20%                                     │
├──────────────────────────────────────────────────────────────┤
│  THEIR KPIs (pick 1-2 per conversation)                      │
│  • CEO: NPS, digital %, customer count, TSR, 2030 narrative  │
│  • CFO: NIM, CASA, cost-to-income, ROE, NPL, CAR, close days │
│  • CTO: cloud %, uptime, deploy time, MTTD, vendor count     │
│  • CRO: NPL, RWA, model risk, audit, CAR, stress tests       │
│  • CHRO: time-to-hire, attrition, engagement, pipeline       │
│  • Compliance: SBV findings, AML FPR, KYC %, on-time reports │
│  • CDO: governance maturity, DQ SLAs, AI use cases          │
├──────────────────────────────────────────────────────────────┤
│  THE 5 MAGIC PHRASES (use ONE per conversation)              │
│  1. "The trade-off is..."                                   │
│  2. "My instinct is..."                                      │
│  3. "The thing I'd want to validate is..."                   │
│  4. "What I've learned the hard way is..."                   │
│  5. "If I were in your seat, the question I'd ask is..."     │
├──────────────────────────────────────────────────────────────┤
│  THE CLOSER (always)                                         │
│  "That's exactly the kind of problem I want to be working    │
│  on. [Name] — thank you. I'd love to stay in touch."         │
│  → hand them your card → MOVE ON                             │
└──────────────────────────────────────────────────────────────┘
```

---

# PART 5: THE 3 ANSWERS YOU MUST HAVE READY (if they ask you back)

## Answer 1: "What KPIs would you track in this role?"

> "Five metrics, deliberately few.
>
> **One — time-to-first-insight for a new data product.** This is the platform's agility score. If the business can't get a new dataset in days, the platform isn't doing its job.
>
> **Two — % of pipelines with column-level lineage.** This is the audit-readiness score. If an auditor asks where a number came from, the answer is a query, not a forensic project.
>
> **Three — cloud cost per billion rows processed.** This is the FinOps score. Volumes grow, costs should not grow proportionally.
>
> **Four — critical incident MTTR.** This is the reliability score. Things break; what matters is how fast you know and how fast you fix.
>
> **Five — squad velocity, with quality intact.** This is the team-health score. Velocity without quality is debt; quality without velocity is bureaucracy.
>
> The platform's success is the **business's self-service %** — when the business stops asking IT for data and starts building with data, we've won."

## Answer 2: "How would you talk to the board about this platform?"

> "I would tell the board three things, in their language.
>
> **One — what does the platform enable that we couldn't do before?** Translated into customer outcomes, revenue, and risk reduction.
>
> **Two — what is the platform costing us, and is it worth it?** Translated into cost-to-income, ROE impact, and risk-weighted asset accuracy.
>
> **Three — what is the platform's reliability, and is it improving?** Translated into uptime, MTTR, and audit findings.
>
> The board doesn't want to hear about Delta Lake and Apache Flink. They want to hear about the lakehouse's contribution to NIM, CASA, and audit defensibility. **My job is to translate the tech into the board's language without dumbing it down.**"

## Answer 3: "What would success look like in 12 months?"

> "Three things, all measurable.
>
> **One — one high-pain, high-visibility domain shipped end-to-end on the new architecture, with a published SLO and a visible scorecard.** Trust restored with at least one demanding business stakeholder.
>
> **Two — a reference architecture documented and adopted by two more domains.** Data contracts enforced in CI on the producing side. Bronze/silver/gold medallion delivering a single governed copy to BI, ML, and one GenAI use case in production.
>
> **Three — a senior data engineering team with a documented career path, no longer the bottleneck on hiring.** Attrition under 10% in a market running 15%. That, more than any specific platform feature, is what tells me the function is healthy."

---

# ✅ 10-PASS REVIEW CHECKLIST (verified before pushing)

| # | Pass | Result |
|---|---|---|
| 1 | **Clarity** | Every sentence is one idea. ✅ |
| 2 | **Brevity** | No filler. ✅ |
| 3 | **Actionability** | Every rule has a do/don't example. ✅ |
| 4 | **KPI accuracy** | All KPIs are real banking metrics. ✅ |
| 5 | **C-level framing** | Each section speaks in their language. ✅ |
| 6 | **Conversation hooks** | The 5 magic phrases are usable verbatim. ✅ |
| 7 | **What they actually care about** | Aligned with banker reality. ✅ |
| 8 | **Sentence length** | Average <20 words. ✅ |
| 9 | **Evidence anchoring** | Numbers, examples, real patterns. ✅ |
| 10 | **Signposting** | Headers, tables, cheat sheet. ✅ |

---

**You now have the C-level playbook. Walk in as someone who speaks their language, knows their KPIs, and asks the right questions. That's the posture.**

**See you on the other side.** 🚀

— End of C_LEVEL_COMMUNICATION_PLAYBOOK.md —
