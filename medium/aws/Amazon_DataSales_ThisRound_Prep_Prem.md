# Amazon Senior Data Sales Specialist — THIS Round Prep (Prem Vishnoi)

> **📅 July 21, 2026 · 4:00–5:00pm ICT (Bangkok) · Zoom (video optional) · Interviewer: Son Vu, Account Manager, ENT-FSI Vietnam**
> 60 min, technical + behavioral. Assessing communication + role fitment. Below is exactly what to prepare for *this* call.

---

## 🎯 Interviewer Intelligence — use this
**Son Vu = Account Manager, Enterprise Financial Services Industry (FSI), Vietnam.**

Three things this tells you:
1. **He sells to banks/insurers/financial firms.** Your **SCB Bank AML** and **DBS** experience is directly relevant — lead with FSI stories. You've built regulated, MAS-compliant data systems across 15+ countries. Speak his customers' language (compliance, risk, data governance, latency).
2. **Vietnam focus.** You're a **Vietnam TRC holder** — mention it naturally. It signals commitment to the ASEAN territory and removes a logistics concern.
3. **He's an AM, not a pure specialist** — he cares about how you'd *partner with account teams* to grow revenue in his accounts. Show you make the AM's job easier, not harder.

**Rapport opener (if natural):** "I saw you're focused on FSI in Vietnam — I've spent years building data platforms in banking, at Standard Chartered and DBS, and I'm a Vietnam TRC holder, so this territory and vertical are close to home for me."

---

## ⚠️ The Core Gap — own it in the first 10 minutes
This is a **quota-carrying field sales role**. You've never carried a quota. The JD literally says "*even if you don't meet all qualifications, apply*" and "*build the playbook, not just run it*" — they're open to non-traditional backgrounds. Your job: convert "not a salesperson" into "the technical seller FSI CXOs actually trust."

**Your honest framing:**
> "Let me be direct — I haven't carried a sales quota. What I bring instead: 15 years as the enterprise data *buyer* and *builder*. I've sat across the table from AWS, Databricks, and cloud vendors with a $3M budget; I know how CIOs and CDOs actually evaluate a data platform, where migrations fail, and what makes them commit. For a technical sale to a CXO, that credibility is hard to fake — and it's exactly what I'd bring to your accounts."

**Why this works:** A Data Sales Specialist selling to CIO/CDO/CTO must be *technically credible* and *speak the buyer's language*. You are the buyer. That's your unfair advantage.

---

## 📚 AWS Data Portfolio — know this cold (current 2026)

You must be able to **whiteboard a modern AWS data architecture** (a basic qualification). Here's the current stack and how to position it:

**The pitch: "Unified, open, secure lakehouse — a single copy of data for analytics AND AI."**

```
INGEST          STORE (lake+warehouse)      GOVERN         CONSUME
Kinesis/MSK  →  S3 + S3 Tables (Iceberg) →  Lake Formation → Athena (serverless SQL)
Zero-ETL     →  Redshift (warehouse)     →  (fine-grained,  → Redshift (high-concurrency)
(from Aurora,   ↕ unified via              row/col/cell)   → EMR/Glue (Spark)
 RDS, DynamoDB) SageMaker Lakehouse                        → QuickSight (BI)
                (single copy, Iceberg)                     → SageMaker (ML)
                                                           → Bedrock / Amazon Q (GenAI)
```

**Key 2026 talking points (these show you're current):**
- **SageMaker Lakehouse** — unifies S3 data lakes + Redshift warehouses on **one copy of data**, fully **Apache Iceberg**-compatible. This is AWS's flagship modern-data answer.
- **S3 Tables** — first cloud object store with **built-in Iceberg** support; optimized for analytics, auto-compaction.
- **Zero-ETL** — near-real-time from operational DBs (Aurora, RDS, DynamoDB) into the lakehouse *without building pipelines*. Huge selling point (no 3am Glue jobs).
- **Amazon Q** — natural-language / agentic layer over data (ties to your Text-to-SQL work!).
- **Governance = Lake Formation** — fine-grained (row/column/cell) — critical for FSI/regulated customers.
- **Open** — Iceberg means no lock-in; can even federate to **Snowflake/BigQuery**. Use this against competitors.

**Migration plays the JD names (be ready to discuss):**
- **SQL Server / Oracle migration** → Aurora PostgreSQL / RDS (cost, no license lock-in). Your PostgreSQL familiarity helps.
- **Analytics migration** → from legacy warehouses (Teradata — *you know Teradata!*) to Redshift/lakehouse.

---

## 🥊 Competitive Positioning (JD explicitly asks — "compete vs collaborate")

You've *used* these (Databricks at Makro, multi-cloud) — huge credibility. Positioning:

| Competitor | Their strength | AWS angle (how you'd position) |
|-----------|----------------|-------------------------------|
| **Databricks** | Unified Spark + ML, Delta | AWS = open (Iceberg not just Delta), deeper native integration, no separate platform cost; but *collaborate* where customer is Databricks-committed (runs on AWS anyway) |
| **Snowflake** | Simple, predictable warehousing | AWS = open lakehouse, single copy for AI+analytics, better cost control at scale, federate to Snowflake rather than rip-out |
| **Microsoft Fabric** | Bundled with M365/Azure | AWS = best-of-breed depth, broadest service choice, open formats, avoids Azure lock-in |
| **Google BigQuery** | Serverless simplicity | AWS = broader portfolio, Iceberg openness, stronger enterprise/FSI footprint in ASEAN |

**The mature answer AWS wants:** "Lead with the customer's problem, not the product. Sometimes you compete; sometimes the customer's already on Databricks and you *collaborate* — it runs on AWS, so you grow consumption anyway. Know when to do which." *(This shows judgment — exactly what a specialist advising account teams needs.)*

---

## 🗣️ Functional Answers (frame delivery experience as sales)

**"Walk me through helping a customer modernize their data foundation."**
> "At Makro — an $8B omnichannel retailer — finance closed books over 5 days on fragmented legacy systems. I diagnosed the root cause, made the business case for a lakehouse modernization, and led delivery: a Databricks Lakehouse processing 10B+ rows/day. Close dropped to 2 hours, 50+ exec dashboards adopted. That's the consultative arc — diagnose the business problem, design the architecture, quantify the value, land it, expand. On AWS I'd map that same journey onto SageMaker Lakehouse and S3 Tables."

**"How would you position a modern data platform to a CXO?"**
> "I don't lead with services — I lead with their business problem. To a CDO I'd say: 'Your AI ambitions are only as good as your data foundation. Today your data's siloed across warehouses and lakes, you're copying it, governance is fragmented. A unified open lakehouse gives you one governed copy that powers both analytics and GenAI — and with zero-ETL you stop babysitting pipelines.' Then I'd whiteboard it."

**"Tell me about driving adoption / measurable value."** (Customer Obsession + Deliver Results)
> "Text-to-SQL GenAI at Makro — I put natural-language querying in the hands of non-technical business users, with guardrails for accuracy. Adoption spread across merchandising and marketing because it solved a real pain: waiting days for analysts. Adoption *is* the metric that matters — a platform nobody uses delivers zero value."

---

## 🎯 The 5 Tested LPs — your STAR stories ("I", metrics, FSI-weighted)

**Customer Obsession** — Text-to-SQL for business users (started from their pain, worked backward).

**Learn and Be Curious** — Self-taught GenAI/LLM/RAG (UT Austin AI program, agentic AI cert, M.S. in progress) to deliver conversational analytics.

**Insist on the Highest Standards** — Refused to ship the automated financial close until parallel reconciliation matched exactly; wrong financials are unacceptable.

**Deliver Results** — Lazada real-time platform, 100M+ events/day, 20M+ daily insights, double promotion.

**Invent and Simplify** — Reusable architecture/templates so new-country expansion onboarded on one common foundation instead of rebuilding.

**Failure (have 1 ready)** — An early ML model (pricing/forecasting) that underperformed in production due to data quality / adoption resistance; lesson: validate data readiness + secure stakeholder buy-in *before* building. Own it with "I."

> 🔑 **FSI-flavored story to have ready** (for Son Vu): SCB AML across 15+ countries — built fuzzy-matching/entity-resolution that cut false positives and investigation time under MAS regulatory scrutiny. Shows you understand regulated-industry data problems firsthand.

---

## ❓ Questions to Ask Son Vu (pick 3)
1. "For FSI accounts in Vietnam and ASEAN, what's driving the most data demand right now — Oracle/SQL Server migration, lakehouse modernization, or GenAI enablement?"
2. "How does the data specialist partner with you as the AM on a complex deal — where does the specialist add the most leverage?"
3. "This role is described as 'build the playbook, not just run it' — what's still unwritten that you'd want a specialist to figure out?"
4. "How do you balance competing vs collaborating with Databricks and Snowflake in FSI accounts here?"
5. "Given my background is technical delivery and the buyer's seat rather than quota-carrying sales — what would you want me to ramp on fastest, and where does my depth help most?"

---

## ✅ Pre-Call Checklist
- [ ] Whiteboard the AWS lakehouse architecture from memory (practice 2-3x)
- [ ] Memorize: SageMaker Lakehouse, S3 Tables, Iceberg, zero-ETL, Lake Formation, Amazon Q
- [ ] 3-4 success stories + 1 failure, all in "I" with metrics
- [ ] FSI/banking story front-loaded for Son Vu
- [ ] Mention Vietnam TRC naturally
- [ ] Competitive positioning table — know compete-vs-collaborate
- [ ] Own the quota gap honestly → pivot to buyer credibility
- [ ] 3 questions ready
- [ ] Zoom tested, quiet room, note ICT timezone (Bangkok = same as Vietnam, GMT+7)
- [ ] Join early — waiting-room admission can take up to 10 min

---

## The one sentence to anchor everything
> "I'm the technical data leader who's been the buyer — I know what FSI CXOs need to hear because I've had to make those decisions myself, and I can whiteboard the AWS architecture that solves their problem."
