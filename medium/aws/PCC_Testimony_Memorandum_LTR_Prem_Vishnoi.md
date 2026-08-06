# Intrepid Asia — Panel Round: Solutions Architect + Business Lead — Prep (Prem Vishnoi)

> **📅 Thursday, 6 Aug, 1:00pm SGT · Zoom · Niall Reilly + Suney Sharma**
> A "coffee chat" with two senior stakeholders *together*. Framed as casual — it isn't. You're being assessed on two axes at once: **can you build it** (Solutions Architect) and **will it move the business** (Business Lead). Passing means satisfying both, often in the same answer.

---

## 🔍 First: Do Your Homework on Them
I couldn't pull their exact roles (LinkedIn is login-walled). **Before Thursday, look up both on LinkedIn:**
- **Niall Reilly** — likely the Solutions Architect / technical side. Check: background (engineering? architecture? ex-vendor?), how long at Intrepid, what he's built.
- **Suney Sharma** — likely the Business Lead. Check: which part of the business (commercial? client services? growth?), what outcomes he owns.

Knowing who's who lets you *aim* each answer — technical depth toward Niall, business impact toward Suney — and address both.

**Company context worth knowing (verified):** Intrepid was acquired by Ascential's Flywheel, briefly under Omnicom, then did a management buyout and is now Flywheel's strategic SEA partner. It has **near-doubled in scale three years running** across all 6 SEA markets. So: high-growth, recently independent again, scaling fast. That shapes everything — they need someone who builds for scale *and* justifies cost in a growth business.

---

## 🎯 The Core Dynamic: Two Audiences, One Answer
This is the skill they're testing. Every strong answer does both:
> **[Technical substance for Niall] + [Business outcome for Suney]**

Example: *"I'd add streaming ingestion into StarRocks for livestream performance [Niall: real architecture] — so account teams catch a collapsing campaign in minutes instead of at month-end, which is direct margin for the client [Suney: business impact]."*

Practice ending every technical point with "…which means [business outcome]." And grounding every business claim in "…and technically that works by [substance]."

---

# SECTION 1 — FOR THE SOLUTIONS ARCHITECT (Niall)

*He's checking: can you actually architect this, or just talk about it? Is he going to have to carry you technically?*

## Likely questions & your angles:

**"How would you evolve our stack — BigQuery, StarRocks, DBT, Cube — into an AI platform?"**
> Don't rebuild. Add four layers: harden the **semantic layer** (Cube) so metrics are defined once, **streaming** into StarRocks where latency earns its cost, an **ML layer** (feature store, registry, monitoring), and the **LLM/agent layer** (vector store, retrieval, guardrails, orchestration). Each independently valuable.
> **Map your experience:** StarRocks ≈ ClickHouse (Lazada). DBT ≈ your medallion layers as SQL. Cube = the semantic layer you built for Text-to-SQL at Makro.

**"Walk me through a real-time architecture you've built."**
> Lazada: Kafka → Flink → ClickHouse + HBase, 100M+ events/day, 20M+ daily insights. Split-stream pattern — fast path for alerts, history path to warehouse. For Intrepid: livestream performance, campaign anomalies, inventory across marketplaces.

**"How do you handle multi-tenant data — multiple client brands?"** 🔑 *(specific to their agency model)*
> This is critical and I'd flag it as a first-order concern. Every brand's data must be isolated — one client's numbers can never leak into another's reporting. Row/column-level governance, tenant isolation in the semantic layer, access control by brand. *"I built AML platforms across 15+ countries under MAS scrutiny at Standard Chartered — regulated multi-jurisdiction data isolation is a problem I know."*

**"How would you build NL2SQL / conversational analytics here?"**
> Your strongest technical story. The LLM is easy; the hard parts are semantic grounding (why Cube matters), guardrails (read-only, cost caps, row limits), validation/retry, and transparency (show the SQL). You built exactly this at Makro.

**"What about cost? We're scaling fast."**
> BigQuery cost = bytes scanned. Partitioning, clustering, materialised aggregates, killing SELECT *, per-team cost visibility. You've owned a $3M budget with explicit cost-optimisation remit.

**Show restraint:** Don't propose replacing his stack. Evolve, don't rip out. Ask what hurts most before prescribing.

---

# SECTION 2 — FOR THE BUSINESS LEAD (Suney)

*He's checking: will this person drive GMV and client value, or build a beautiful platform nobody uses? Can he talk to clients?*

## Likely questions & your angles:

**"How does data actually make our clients more money?"**
> Four levers in ecommerce/social commerce: **speed of reaction** (anomaly detection catches a broken campaign in hours, not month-end), **scale of judgment** (models watch many brands across 6 countries — leverage without linear headcount), **self-serve** (NL2SQL removes the data-team bottleneck), and — the big one — **client-facing differentiation** (predictive insights and scenario planning clients will pay more for). That last one turns data from a cost centre into part of the product.

**"How do you measure success?"**
> Business outcomes first: GMV uplift, marketing efficiency, cost reduction, automation rate (their own JD metrics). Then adoption — a model nobody uses is worth zero. Then platform health. *"At Makro I set my team's KPIs against business outcomes, not engineering output — it changes what engineers build."*

**"Give me an example of data driving real business value."**
> Makro: diagnosed slow 5-day financial close → lakehouse modernisation → 2 hours, 50+ dashboards adopted, real-time inventory across 200 stores, ML forecasting across 1,000+ vendors. Frame it as: diagnose business pain → build → quantify → drive adoption.

**"You've done retail/logistics — can you handle agency, multi-client, social commerce?"** *(the honest gap)*
> The domain differs, the shape is the same. O2O at Makro = online+offline commerce, unified customer data, campaign activation, catalogue problems. Lazada = marketplace scale + logistics. Item matching across channels = your catalogue-intelligence problem. **New for me: the multi-client agency dimension — serving brands vs one P&L. I'd learn that fast. But multi-country, multi-platform data I know deeply.** Be honest, then bridge.

**"How do you make business teams actually use what you build?"**
> Push, not pull. Move from dashboards people must remember to open → proactive alerts and recommendations in their workflow. And involve business owners from problem-framing, not handover — *"I learned this from a forecasting model that failed because I built it without the users; a model nobody acts on is worthless."*

---

# SECTION 3 — QUESTIONS THAT HIT BOTH

**"Where would you start in your first 90 days?"**
> 30 days: listen + audit (what breaks, which numbers people argue about, what the platform costs). 60: publish a staged roadmap, agree impact metrics, start one quick win. 90: ship something visible, standardise the semantic layer. *"I'd rather show one real business result in 90 days than a beautiful architecture nobody sees."* (Satisfies both: method for Niall, outcome for Suney.)

**"What's your view on agentic AI for us?"**
> Start narrow, earn autonomy. First agent: monitors campaign/marketplace performance, detects anomaly, explains cause, *recommends* — human approves. Underneath: tight tool scopes, retrieval, observability, evaluation. Widen to bounded autonomous action (bid adjustments in a range) only once accuracy is proven. *"Autonomy is earned through demonstrated accuracy, not switched on because it's exciting."* (Technical rigor + business caution — lands with both.)

**"Why this role, why Intrepid?"**
> The leap from reporting → autonomous intelligence is the one I care most about, in ecommerce, at regional scale, with genuinely rich data across marketplaces, creators and marketing. And I'd be building the intelligence backbone of the business, not a support function. Bigger swing than optimising what I've already built at Makro.

---

# SECTION 4 — HOW TO RUN A 2-PERSON "COFFEE CHAT"

**It's casual in tone, rigorous in substance.** Tips:
- **Address both people.** When Niall asks something technical, land the point, then turn briefly to Suney with the business implication (and vice versa). Shows range.
- **Read the room on depth.** If Niall goes deep architecturally, match him. If Suney looks lost, translate immediately — *"in plain terms, that means…"* That translation skill is literally in the JD.
- **It's a conversation, not a Q&A.** Ask them things mid-flow. "How are you handling that today?" turns an interview into a working session — which is how they imagine you in the job.
- **Bring a point of view.** These two will work with you daily. They want a peer with opinions, not someone auditioning. Disagree gently where you genuinely do.
- **Don't over-talk.** 90-second answers, then pass the ball back. Two-on-one, silence is fine — let them steer.

---

# SECTION 5 — YOUR QUESTIONS (ask 3–4, aim some at each)

**For Niall (technical):**
1. "Where does the current platform hurt most — cost, reliability, modelling, or delivery speed?"
2. "How do you split ownership between platform engineering and the data team today?"
3. "How much of the stack is real-time today versus batch — and where do you wish it were faster?"

**For Suney (business):**
4. "Is the data platform mainly internal efficiency, or do you see it becoming something clients buy?" *(best strategic question)*
5. "What business decision do you most wish data could answer today that it can't?"
6. "Given you've near-doubled three years running — where does data most need to keep up with that growth?"

**For both:**
7. "What would make you look back in a year and say this hire was a success?"

---

# ✅ CHECKLIST

**Before Thursday:**
- [ ] Read Niall & Suney on LinkedIn — confirm who's technical, who's business
- [ ] Re-read the JD's Data & AI vision section (their exact words)
- [ ] Skim intrepid.asia — understand the client-services / Flywheel model

**Be ready to whiteboard/describe:**
- [ ] The 4 layers you'd add to their stack
- [ ] Real-time split-stream pattern (Lazada)
- [ ] Multi-tenant / multi-brand data isolation
- [ ] NL2SQL flow with guardrails

**Your flagship stories:**
- [ ] Text-to-SQL GenAI (most relevant — AI-native)
- [ ] Makro lakehouse + close automation (business impact)
- [ ] Lazada real-time (scale + ecommerce)
- [ ] Scaling 8→30 (leadership)
- [ ] Forecasting failure (humility + adoption lesson)

**Numbers:** 8→30 · $3M · $8B · 3 countries · 10B+ rows/day · 100M+ events/day · 5 days→2 hrs · 50+ dashboards · 1,000+ vendors

**Posture:**
> Every answer: technical substance + business outcome. Address both people. Bring opinions. It's a working session, not an exam — act like their future colleague, because that's what they're deciding.
