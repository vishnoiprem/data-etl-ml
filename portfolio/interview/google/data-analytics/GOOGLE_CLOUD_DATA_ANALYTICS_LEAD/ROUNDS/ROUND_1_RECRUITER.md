# Round 1: Recruiter Screen
## Google Cloud Data & Analytics Lead — Cloud Consulting

---

> ## ⚠️ READ THIS FIRST — these are scripts, not testimony
>
> The model answers below were originally written for a **generic Google Cloud candidate**, not for you. They contain numbers that are **not your history**: a "12 direct reports" team, a "$2.5M migration / 120 TB", "$1.2M/yr savings", "500+ TB migrated", "$3M+ engagements", "4 years at an SI Partner". **None of these are yours.** Do not deliver them.
>
> The purpose of this file is the **structure** — the framework, the sequencing, the things a recruiter is checking for. The content must be rewritten from `portfolio/interview/meta/coach/resume-facts.md`.
>
> **Three checks before you say any of it:**
> 1. **Is it true?** Does it trace to your resume?
> 2. **Is it yours?** Could someone else have said it?
> 3. **Would you defend the follow-up?** "How did you measure that?" must have an answer.
>
> **Never present a number you cannot source. If you cannot defend it, drop the claim.** A recruiter screen is a gate — it is the cheapest place to be caught overclaiming, and the most expensive, because it ends the process before the RRK.

---

### 🎯 Round Overview
| Attribute | Details |
|-----------|---------|
| **Duration** | 30 minutes |
| **Format** | Phone / Video call |
| **Interviewer** | Technical Recruiter (not engineer) |
| **Goal** | Validate scope match, leadership experience, cloud consulting fit, logistics |
| **Weight** | Gate — must pass to proceed |

---

### 📋 What They're Assessing

| Criteria | Minimum Bar | Strong Signal |
|----------|-------------|---------------|
| **Leadership Scope** | 5+ direct reports, 2+ years | 10+ reports, multi-team, hiring authority |
| **Cloud Consulting** | Some client-facing delivery | SI partner mgmt, migration factory, practice building |
| **Technical Fluency** | Can speak GCP data services | Architects solutions, explains trade-offs |
| **Communication** | Clear, concise, structured | Executive presence, asks good questions |
| **Motivation** | Wants this role specifically | Knows Google Cloud Consulting model |

---

### ❓ Likely Questions & Model Answers

#### Q1: "Walk me through your background and current role."
**Framework:** 90-second narrative — Scope → Impact → Why This Role

**Model answer — rewrite from your resume, do not deliver as written:**
> "I'm currently **Head of Data** at **Makro/CP Group** in [location]. I run the enterprise data platform and the data strategy there: a team that has grown from **8 to 25**, a **$2M annual cloud and vendor budget**, **10B+ rows a day** and **500+ daily production jobs**. Before this I was **VP Data Engineering at Lazada (Alibaba Group)**, and earlier **Principal at Xendit** and a **Big Data Consultant at SCB Bank** doing AML work across **15+ countries**.
>
> I've spent my career in the data platform layer — Spark, Kafka, Flink, Databricks — and that's the depth I'm bringing. What I'm moving toward is the consulting layer: **architecture plus client outcomes plus practice building**. I want to help Google's enterprise customers do the migration work I've done as a practitioner, and build the team and reusable assets that make it repeatable."

**⚠️ What changed and why:** the original answer said *"Senior Data Engineering Manager, 12 engineers, 500+ TB, $3M+ engagements, 4 years at an SI Partner."* **None of that is your history.** You have never worked at an SI or Deloitte/Accenture; your team is 8 → 25, not 12; your scale is 10B+ daily rows, not 500TB migrated. The rewritten version uses only `resume-facts.md` figures.

**Key Elements:** Quantified scope, GCP-specific, partner experience, consulting DNA, clear motivation.

---

#### Q2: "What's the largest team you've managed? How did you structure it?"
**Model answer — rewrite from your resume:**
> "Largest team: **Head of Data at Makro, 8 → 25**. [⚠️ **FILL THIS**: how you structured it — platform vs product vs analytics pods, how many in each, who you inherited vs hired. The `ROUND_1_RRK.md` **Q4** TODO is exactly this, and it is one of the nine things only you know.]
>
> Structure I ran: [⚠️ **FILL**: cadence — 1:1s, standups, retros, planning rhythm; how you set technical direction; how you split the team].
>
> **Why I led with this:** the recruiter is checking for scope, not for a specific org chart. What must be true is that you can name the number, the structure, and your own contribution to hiring and direction. The [brackets] are the whole answer — if you can't fill them from memory, this question will not be answered well."

**⚠️ The original answer ("12 direct reports across 3 functional squads: Platform (4), Migration (5), ML Ops (3), plus 8 contractors") is entirely invented. Do not use it.**

---

#### Q3: "Describe a complex cloud data migration you led."
**Framework:** Situation → Architecture → Challenges → Outcome (2 min max)

**Model answer — pick your real migration and use the framework:**
> "**Situation:** [⚠️ **FILL**: which real migration — SCB Bank's AML estate on Hadoop/Hive across **15+ countries** is the strongest fit for "complex cloud data migration" because of the regulatory dimension. Makro's lakehouse is the strongest for scale: **10B+ rows/day**, **500+ daily jobs**. Lazada is strongest for streaming volume: **100M+ daily events**. Choose one and go deep — do not blend them.]
>
> **Architecture:** [⚠️ **FILL**: what was in scope, what the target platform was, how you decided replatform vs refactor vs retire. Use the **6 R's** framework — that part of the original answer is good methodology and is safe to keep.]
>
> **Challenges:** [⚠️ **FILL**: real obstacles. Regulatory/data residency if SCB; cost and a **$2M** budget if Makro; throughput and correctness if Lazada.]
>
> **Outcome:** [⚠️ **FILL**: a real number with its method. For Makro the defensible one is **month-end close from 5 days to 2 hours**, and **incidents −60%** — but both need the baseline you can state. For a cost outcome, the **40%** claim needs you to name whether it is spend or runtime and which employer.]
>
> **The shape of the answer is what earns it.** The recruiter is checking that you can scope, decide, and land an outcome — not the size of your numbers. A real 50TB project explained properly beats a fictional 120TB one."

**⚠️ The original answer ("$2.5M migration, 120 TB, $1.2M/yr savings, 99.99% data validation pass, reusable accelerator used across 3 accounts") is a corpus story, not yours.** `ROUND_1_RRK.md` explicitly warns against borrowing `$2.5M / 120TB` from the wider corpus.

---

#### Q4: "What GCP data services have you used in production?"
**Model answer — do NOT claim production GCP you do not have.** This is the highest-risk question in the file, because the recruiter may follow up on any one of them and "in production" invites exactly that.

**Answer honestly, and make the honesty the strength:**

> "My production depth is **Spark, Kafka, Flink and Databricks** — that's where I've run platforms at **10B+ daily rows** and **500+ daily jobs**. My **Google Cloud** depth is **architect-level**: I've designed and costed BigQuery and Dataflow solutions, and I've built an end-to-end course project — ingest, validation, dead-letter, BigQuery partitioning, IAM policy modelling, cost modelling — with a passing test suite.
>
> **My production depth on those specific services is lighter than I'd want it to be.** What I'd do first in this role is get onto the services with real customer data early, and lean on the team's GCP depth rather than pretend I have it."

**The equivalent breadth, in the order the recruiter asked:**
> "**BigQuery** — partitioned and clustered tables, BI Engine, materialized views, slot reservations *(designed and costed; built in the project)*.
> **Dataflow** — streaming and batch, flex templates, custom transforms, windowing *(designed; built in the project)*.
> **Dataproc** — Spark/Hive/Flink, autoscaling, init actions, Hive metastore migration.
> **Dataplex** — lakehouse governance, data lineage, quality scans.
> **Pub/Sub** — event ingestion, dead-letter handling, ordering keys.
> **Cloud Composer (Airflow)** — DAG design, sensor patterns, dynamic task mapping. **This one is real production experience** — Airflow is a genuine part of my stack.
> **Vertex AI / Looker** — architect-level only."

**⚠️ The original answer listed all eight services in one flat block with no distinction, which reads as "I have run all of these in production."** Split them. Claiming Vertex AI feature store and Looker LookML as production experience is overclaiming, and `ROUND_1_RRK.md` flags the GCP gap as one of the four exposures. **The `GAP_CLOSURE.md` §2 60-day plan is what you say when pushed on this.**

---

#### Q5: "How do you work with System Integrator (SI) partners?"
**Model answer — the framework is good, the example must be yours:**
> "I treat SIs as **extensions of my team** with clear governance:
> 1. **Joint planning** — shared sprint cycles, unified backlog
> 2. **Architecture ownership** — we own design; they own execution
> 3. **Quality gates** — code review, automated validation, UAT checklists
> 4. **Escalation paths** — weekly steering, monthly exec sync
> 5. **Knowledge transfer** — runbooks, training, asset contribution
>
> Example: [⚠️ **FILL**: a real instance. The strongest is your **SCB Bank** engagement, where the AML estate ran across **15+ countries** — the governance question there was how many teams own which jurisdictions' data and who signs off. If you have run a delivery model with an external or partner team, use that. If you have not, say honestly: *"I have not run an SI-delivery model myself; here is how I would set it up, and here is the closest thing I have done"* — and name that thing.]"

**⚠️ The original example ("the financial services migration, embedded our architects in their pods, defined Definition of Done, co-authored the migration playbook") describes a project that did not happen. Remove it or replace it with a real one.**

---

#### Q6: "Why Google Cloud Consulting? Why now?"
**Model Answer:**
> "Three reasons:
> 1. **Market moment** — Enterprises are accelerating cloud data migrations; Google's **data + AI differentiation** (BigQuery, Vertex AI, Gemini) is unique.
> 2. **Consulting model** — I prefer **outcome-based delivery** over staff augmentation. Google's **'land, expand, transform'** aligns with how I work.
> 3. **Practice building** — The opportunity to **codify patterns into reusable assets** that scale across the region is exactly the leverage I want.
>
> Timing: I've built the platform and the team, and delivered the outcomes inside a business — now I want to do it at **Google's scale with Google's technology**, and add the consulting and practice dimension I haven't had."

---

#### Q7: "What are your salary expectations / notice period / location flexibility?"
**Model Answer:**
> "I'm targeting **$[X]–$[Y] base + equity + bonus** aligned with L6/L7 Cloud Consulting leads. **Notice period: [X] weeks**. **Location: [City/Remote]** — flexible for travel to client sites (comfortable with 50% travel)."

---

### 🎯 Your Questions for Recruiter (Pick 3)

1. "How is the **Data & Analytics practice structured** across the region — dedicated pods vs. fluid resourcing?"
2. "What's the **split between migration delivery vs. practice building/asset creation** for this role?"
3. "How does the **SI partner ecosystem work** — preferred partners, joint GTM, quality governance?"
4. "What does **success look like in the first 90 days** for this Lead role?"
5. "How does the **hiring committee process** work for Cloud Consulting leads?"

---

### ✅ Pass Checklist (Post-Call)

- [ ] Quantified scope: team size, budget, data volume, $ impact
- [ ] Named GCP services with architectural context
- [ ] SI partner experience with governance model
- [ ] Clear "Why Google Cloud Consulting" narrative
- [ ] Asked 3 insightful questions
- [ ] Recruiter confirmed next steps + timeline

---

### 🔴 Red Flags (Auto-Fail)

- ❌ "I've only worked internal, no client-facing"
- ❌ "I don't manage people directly"
- ❌ Vague on GCP: "I know cloud" → can't name services
- ❌ No migration experience: "We built new platforms"
- ❌ Can't articulate migration patterns (6 R's)
- ❌ Salary misaligned >20% from band

> **⚠️ Two of these do NOT apply to you, and you should not treat them as gaps.**
> - **"Only worked internal, no client-facing."** Your resume shows SCB Bank and DBS as **employers**, not internal functions — the AML work across **15+ countries** was delivered into a regulated bank. If asked to prove client-facing delivery, use SCB: *"I delivered AML data engineering for a bank across 15+ countries."* [⚠️ **Check**: was that delivered to the bank directly or through a consultancy? `resume-facts.md` lists SCB as your employer, so state it as delivery *for* the bank — and if you were in fact embedded at a consultancy, say which, because the recruiter will ask.]
> - **"No migration experience."** You have migration and replatforming experience from the **Makro lakehouse** decision. The real risk here is the opposite — a recruiter may read your history as *too* platform-internal. **Say so explicitly**: *"I have not run a consulting P&L, and my client-facing work has been in a bank's programme rather than a partner-delivered engagement. Here's what I'd need to learn."*
>
> **What is genuinely a risk for you is the opposite of these red flags**: appearing to be an internal platform leader who has never billed for outcomes. The recruiter's job is to check you can sell and lead inside a partner model. `ROUND_1_RRK_GAP_CLOSURE.md` §3 has the honest practice-P&L redirect.

---

*Next: ROUND_2_TECHNICAL_ARCHITECTURE.md*