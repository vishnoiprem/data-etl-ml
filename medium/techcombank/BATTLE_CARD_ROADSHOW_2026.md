# PREM VISHNOI — TECHCOMBANK OVERSEAS TALENT ROADSHOW 2026
## Director, Data Engineering (40000058) — Singapore, Oct 23 2026
### Battle Card — Final Selection Stage (4 candidates → 1 hire)

> ⚠️ **19 Oct 2026 fact-check:** every "company PDF p.X" citation below refers to a file that is NOT in this folder (`techcomebacnk.pdf` is your own Q&A). Treat those claims as unverified unless DEEP_DIVE §21 confirms them. Verified numbers are in that file.
>
> **Author's note:** This document is built strictly from the six source files Prem provided. Where the JD or company PDF was not specific, I have flagged assumptions. Where Prem's CV is thin, I have reframed — not fabricated. Prem must memorise the bolded 60–90 second answers; everything else is reference.

---

## 0. THE 10-SECOND POSITIONING THESIS

*"I'm a data and AI leader who started in regulated banking — Standard Chartered AML across 15+ countries, DBS before that — and has since built governed data platforms at consumer-internet scale at Lazada and now an $8bn business at Makro. The Director of Data Engineering role at Techcombank is exactly the intersection I've spent 15 years on: regulated financial data done at consumer-internet scale, in the most interesting banking market in ASEAN. I'm here to land the delivery, not to give a strategy deck."*

---

## 1. ROLE BREAKDOWN — Director, Data Engineering (40000058)

### 1.1 Mission / purpose
- Build the **data foundation** for Techcombank's digital banking agenda: a governed, AI-ready data platform that powers analytics, risk/regulatory reporting, personalisation, and GenAI.
- Enable the bank's stated 2026 transformation pillar — *"Reimagine the customer experience with data and AI as the core driver"* (company PDF, p.4) — by making trusted, timely data available across the bank.
- The role's posture is **delivery-led and architecturally literate**: not the function head, but the senior IC + squad leader who *lands* the platform work and the regulator-defensible pipelines.

### 1.2 Top 5 must-haves vs nice-to-haves
**Must-haves (decisive for the role):**
1. **Architect + manager in one head.** JD: *"wore the architect hat in the past or worked with one extensively"* (JD p.1). Anyone who is pure strategy or pure IC loses.
2. **Modern + legacy fluency.** JD lists Hadoop, Spark, Flink, Kafka, Arrow, plus Python/Scala/Java. They have a Hadoop estate and a streaming ambition. Prem has both.
3. **Regulated-banking data engineering muscle.** BCBS 239–style governance, lineage, immutable audit, SBV-style reporting. Prem's SCB AML and DBS work is the closest match on the slate.
4. **Scale proof — "tens of millions of users" for recommenders/personalisation.** JD calls this out explicitly. Prem's Lazada 100M+ events/day and Makro 10B+ rows/day cover it.
5. **Data governance / metadata at Level 4 (JD competency framework).** Most candidates are thin here. Prem's Makro "bank-like controls" and SCB audit-grade lineage are differentiators.

**Nice-to-haves (Prem can acknowledge honestly):**
- *Deep Flink production experience* — Prem is honest: architecturally strong, not a 5-year operator. This is a *cover* story, not a gap.
- *Rust / Kotlin* — Prem does not have it. The JD's "functional/trait-oriented preference" is met via Scala and disciplined code review.
- *Hands-on Terraform/Kubernetes at hyperscale* — Prem has it via AWS Solutions Architect Associate + Makro/Xendit cost work, but not the deepest in the cohort.

### 1.3 Reporting structure
- **Reports to:** Head of Data Engineering & Delivery (JD p.1).
- **Direct reports:** Data Engineers, Senior Data Engineers (squad-level leadership; estimate 8–20 ICs).
- **Org context:** Techcombank runs a **Business Tribe / Enabling Tribe / Platform** model (JD p.1: "Business Tribe, Enabling Tribe"). The Director sits inside the data tribe and is the senior delivery/architecture voice below the Head.
- **Cadence expectation:** Quarterly outcome planning, two-week sprints, demos to business stakeholders (not internal). Tribe/squad/chapter vocabulary wins; "my team" loses.

### 1.4 Key stakeholders, scope, budget signals
- **Upward:** Head of Data Engineering & Delivery, likely a CDO/Head of Data (CEO/CIO/CDO/Chairman are listed in the JD stakeholder map at p.1).
- **Across:** Tribe leads in Retail, Credit, Risk, Treasury, Digital; CFO office (month-end close); CRO/CCO (risk & compliance reporting); CIO/CTO on platform integration.
- **External:** SBV (State Bank of Vietnam) regulators, technology vendors (Databricks, AWS/Azure, Confluent, Tableau), consulting partners, Big-4 auditors.
- **Budget signal:** JD does not state budget, but the scope (squad-level, multiple data domains, two tribes) and the fact that they want "data contracts at the boundary" implies a multi-million-USD delivery budget with FinOps accountability. Prem's Makro $3M budget, Lazada double-promotion, and Xendit 40% cloud-cost takeout are directly relevant.

### 1.5 Tech stack signals from the JD
- **Cloud / data platform:** Open table formats implied ("Delta Lake / Iceberg class" — Prem has Databricks Lakehouse at Makro and Snowflake exposure).
- **Streaming:** Kafka + **Flink** explicitly — both are in Prem's stack; Flink depth is the honest gap to manage.
- **Batch / legacy:** Hadoop, Hive, Spark — covered by Prem's SCB, DBS, and PayPal history.
- **Orchestration:** Not named, but Prem's Airflow + dbt is a safe assumption.
- **Governance:** Metadata management, lineage, data quality — Prem has Makro 60% incident reduction via RCA + monitoring, and SCB audit-grade lineage.
- **ML/AI:** Recommenders at "tens of millions of users", feature stores, MLOps, GenAI (LLMs/RAG/Text-to-SQL all in Prem's CV).
- **Languages:** Python, Scala, Java, R, SQL — all in Prem's stack. **Rust/Kotlin** — honest no.
- **Format optimisation:** **Apache Arrow** in the JD — this is a tell that someone on the panel cares about multi-engine performance. Prem should know Arrow = zero-copy columnar in-memory, the "why" behind pandas UDF speed-ups and the interop substrate for Spark/Polars/DuckDB.

### 1.6 What "good" looks like

| Horizon | What success looks like |
|---|---|
| **6 months** | One high-pain, high-visibility domain (regulatory reporting or month-end close) shipped end-to-end on the new architecture, with a published SLO and a visible scorecard. Trust restored with at least one demanding business stakeholder. |
| **12 months** | A reference architecture documented and adopted by ≥2 more domains. Data contracts enforced in CI on the producing side. Bronze/Silver/Gold medallion delivering a single governed copy to BI, ML, and one GenAI use case in production. Flink path either built (with a senior hire) or deliberately deferred with a written plan. |
| **24 months** | Techcombank runs a personalisation/recommender system at scale (the JD's "tens of millions of users" ambition) on a governed feature store with online/offline parity. Audit-defensible lineage from source to SBV report. A senior data engineering cohort that has a documented career path and is no longer the bottleneck on hiring. |

---

## 2. TECHCOMBANK CONTEXT

### 2.1 Strategy 2024–2026 (cite specifics from the company PDF)
- **"Banking on Vietnam's Bright Tomorrow"** — ⚠️ phrase not found in any public Techcombank source — treat as unverified; don't quote. Verified framing: vision *"Change banking, Change lives"*; 2020–25 Data/Digitalization/Talent programme; new 2025–2030 five-year strategy (≈30M customers, 4× TOI, reported).
- **2026 strategic priorities** (company PDF p.1): (i) sustained business growth, (ii) **elevate customer experience through data and AI**, (iii) advance the operating model, (iv) strengthen ESG/sustainability.
- **6 strategic enablers** (company PDF p.2): strengthen franchise; deliver consistent customer experience across segments; **modernise technology and data platform**; empower a data- and AI-driven workforce; drive digital sales & engagement; disciplined capital and risk management.
- **2024–2026 data/AI investment** (company PDF p.4):
  - **Data lakehouse** (likely Databricks class) to be the "single source of truth" for analytics and AI.
  - **AI-powered credit scoring** to accelerate retail loan decisions while reducing risk.
  - **Hyper-personalised marketing and NBO** at scale — "reaching tens of millions of customers" (Prem's recommender experience maps directly here).
  - **GenAI in customer service, employee productivity, and developer productivity** (company PDF p.4–5) — Prem's Text-to-SQL and Makro LLM work is precisely this archetype.
  - **Process automation** with agentic AI, NLP-driven virtual assistants, RPA (company PDF p.5).
- **Techcombank moment-of-truth metrics** (public sources; the "company PDF" cited elsewhere in this file is not in the folder): #1 overall in Decision Lab's 2025 Bank Satisfaction Rankings (Apr 2025); FinanceAsia Best Domestic Bank in Vietnam 4 years running. ("DMA", "#1 trust", "#2 consideration" could not be verified.) The job is to *defend and extend* that #1 in digital with a data platform that doesn't break under its own success.

### 2.2 Leadership context (what's public and what to handle carefully)
- **CEO:** Jens Lottner (CEO since 18 Aug 2020, re-appointed for 2025–2030; ex-CFO Siam Commercial Bank, McKinsey/BCG). Data/digital/talent agenda.
- **Long-tenure anchor:** Jens has led since 2020 and owns the 2025–2030 strategy — frame it as **his plan**, not an inherited one.
- **Head of Data / CDO role:** the company PDF repeatedly frames data + AI as a top strategic enabler but does not name a CDO. **The Director, Data Engineering is plausibly a key hire for the function** — meaning the panel likely includes a CDO-level sponsor or a Head of Data Engineering & Delivery who is acting in a CDO-like capacity. Prem should ask who that sponsor is.

> ⚠️ **Handle carefully:** Do not name specific public figures you have not verified. Use "the CEO's office" / "your data leadership" / "the Head of Data Engineering & Delivery" as anchors.

### 2.3 Major platforms / public technology footprint
- **Core banking:** Core banking is Temenos T24 (public). "BSS 4.0" is not in public sources — don't cite. The core is still the *bedrock* — the data platform has to drink from the new core cleanly.
- **Digital channels:** Techcombank app, corporate banking, GenAI assistants (public reports cite Amazon Bedrock builds; "TCB ChatB@nk" unverified). These are the visible consumer surface; they live on top of the data platform.
- **Data & analytics:** **Databricks Data Intelligence Platform already adopted (Oct 2024)** — 50+ systems unified, Unity Catalog, MLflow, 45+ ML models. The role *scales and governs* a running platform; it is not greenfield.
- **AI in production:** multiple GenAI use cases already in market (company PDF p.5), agentic AI ambitions, NLP virtual assistant.

### 2.4 Competitive set and how Techcombank differentiates
| Bank / fintech | What they do | Why it matters for the Director role |
|---|---|---|
| **VPBank** | Aggressive retail growth, large digital customer base (verify count). | VPBank and Techcombank are closest on retail scale; data/AI is the moat. |
| **MB (Military Bank)** | Strong digital, MBBank app, big investment in tech. | MB has been more public about core-banking modernisation. |
| **Vietcombank (VCB)** | Largest by total assets, more conservative on digital. | VCB is the incumbent; Techcombank's #1 in digital satisfaction is the wedge. |
| **MoMo** | Leading e-wallet, ~30M+ users, data-rich. | MoMo is a *fintech competitor on customer data*, not just a partner. |
| **Timo, Cake by VPBank, etc.** | Digital-only banks. | Keep an eye on; signals the regulator's appetite. |

**Techcombank's moat** (company PDF p.1–3): ~18.2M customers (6M26), 66% of new retail customers acquired digitally, #1 in e-banking transaction share (17.0% outbound / 15.6% inbound, 2025), #1 Decision Lab 2025. The Director of Data Engineering is being hired to keep that moat widening as the next 5M customers come on.

### 2.5 Vietnam banking regulator (SBV) pressures shaping data/AI
- **SBV** is data-fluent and writes circulars that hit the platform: capital adequacy (Circular 41/2016 and updates), credit risk reporting, IT-security requirements for credit institutions.
- **Data residency / cross-border transfer:** Vietnam's Cybersecurity Law (2018) + **Decree 53/2022** impose data localisation and storage requirements that constrain how far the lakehouse can be cloud-native and cross-border. **Prem's techcombank talk must say "I'd confirm the current position with your legal and compliance teams" rather than assert specifics** — this is a place where a confidently wrong claim costs more than a hedged correct one (see TECHNICAL_ROUND_QA §D3, line 264).
- **Personal data protection:** **Decree 13/2023** on personal data protection — consent, data subject rights, impact assessments, cross-border transfer rules. This shapes the lakehouse design: PII classification at ingest, retention/purge, audit trail.
- **AI-specific guidance:** SBV has been issuing guidance on AI in banking; circulars evolve. **Don't quote circular numbers you have not verified — talk in principles.**

### 2.6 Recent wins / pain points / what they're publicly hiring for
- **Wins:** #1 Decision Lab 2025, PBT VND 32.5T FY25 (+18.2%) and 18.5T 6M26 (+22.5%), Databricks adopted, GenAI use cases scaling (CEO: AI/data "already delivering productivity gains"), ~18.2M customers.
- **Pain points to listen for:**
  - Legacy Hadoop estate that hasn't fully modernised (the JD signals this strongly).
  - Pressure to deliver personalisation/NBO at scale — currently a 2026 ambition (company PDF p.4).
  - Month-end close likely still slow in places; data quality complaints from the business.
  - Cultural: the bank is at "ready to scale data + AI" but the platform foundation is the choke point. This is the job.
- **Public hiring signal:** they are now hiring a **Director, Data Engineering** to deliver the lakehouse foundation the strategy depends on. That is the role Prem is walking into.

---

## 3. PANEL Q&A — 12 LIKELY QUESTIONS WITH TIGHT ANSWERS

> **How to use this:** Each answer is designed to be **60–90 seconds spoken** (~180–270 words at calm pace). Memorise the *shape* and the **bolded first sentence**; deliver the rest conversationally. The "Why they're asking" column is for Prem's own calibration — never say it to the panel.

---

### Q1. "Why Techcombank, why Vietnam, why now?"

**Why they're asking:** Anchors motivation, tests whether Prem has done the homework on Vietnam, and checks for the classic "CV shopping" answer.

> "Two reasons that are the same reason. Banking is where I started my career — I built AML and compliance data platforms at Standard Chartered across fifteen-plus countries, and I was at DBS before that. Then I went to consumer internet — Lazada, and now Makro. The platforms I run in retail are run to financial-controls standard, because they feed the statutory close.
>
> Techcombank is the exact intersection I've spent fifteen years on: a bank that has 18 million customers and is publicly committed to being data- and AI-led, in the most interesting retail-banking market in ASEAN. Vietnam's digital adoption curve is what Singapore's was in 2015 and what Indonesia's was in 2018. This is the moment to land the data foundation; the next five million customers will arrive on whatever platform we build in the next eighteen months.
>
> And — specifically — I want to be in the engine room, not one more layer away from the build. The Director level is where I'm most useful right now."

**Anchor numbers to land:** 18.2M customers (6M26), 66% digital acquisition, PBT +22.5% 6M26, SCB AML across 15+ countries.

---

### Q2. "Your view on Techcombank's data/AI strategy — what would you do differently in the first 90 days?"

**Why they're asking:** Tests strategic credibility without overstepping the role. Catches candidates who either (a) trash the existing strategy or (b) have no opinion at all.

> "The strategy as published — modernise the data platform, build the data lakehouse, deliver AI-powered credit scoring and personalised engagement at tens of millions scale — is the right strategy and the right sequencing. I wouldn't change the destination.
>
> In the first ninety days, three things I'd do.
>
> **One — listen before designing.** I'd spend time with the Head of Data Engineering & Delivery, the CDO, the tribe leads in Retail and Credit, Risk, and the SBV-facing reporting function. I'd want to understand where the platform hurts the most today and what's already been tried. Most platform failures I've seen are from designing before listening.
>
> **Two — find the reference domain.** Pick one high-pain, high-visibility domain — usually regulatory reporting or the month-end close — and prove the new architecture end-to-end in a quarter. Use that as the template everything else follows.
>
> **Three — publish a one-page architecture decision record.** Bronze/Silver/Gold medallion, open table format, governed contracts at the boundary, PII classified at ingest, SBV residency rules respected. Get the senior architects to sign it. Then I can hold everyone — including myself — to it."

---

### Q3. "How would you modernise a bank's data platform with regulatory constraints (SBV circulars, data residency, PII)?"

**Why they're asking:** Direct regulator check. The panel includes someone who has lived through an SBV audit.

> "Three principles.
>
> **One, design the regulator into the architecture, not the regulator into a checklist.** BCBS 239 gives a supervisor-recognised frame for accuracy, completeness, timeliness, adaptability and lineage. That becomes the platform's quality bar, not just a compliance binder.
>
> **Two, classify PII at ingest and treat residency as a first-class constraint.** Public/internal/confidential/restricted tags are carried with the data so policy attaches to the tag, not to four thousand individually maintained grants. Under Vietnam's Decree 13/2023 on personal data protection and Decree 53/2022 on data localisation, the architecture has to answer three questions from day one: where does personal data physically live, who can reach it, and can we prove both. **I'd confirm the current position with your legal and compliance teams before I assert specifics** — this is a place where the regulation is moving and where I'd rather be precise than confident.
>
> **Three, immutable bronze, signed at the boundary.** Raw data is append-only, retained per policy, with full column-level lineage. When the regulator asks 'where did this number in the SBV report come from', we reproduce it as of the reporting date with time travel and a code version pinned to the run. That's the audit answer, and it makes the rest of the platform faster because the business trusts the numbers."

---

### Q4. "How do you build and scale a high-performing data engineering org across Vietnam + overseas hubs?"

**Why they're asking:** Tests whether Prem can do the "people" half at Director level. This is where most candidates get vague.

> "**Platform team, domain-aligned engineers, and a chapter for craft.** The platform team builds the paved road — the medallion framework, the data contract library, the deployment templates, the SLO templates — so domain teams move fast safely. Domain teams sit close to the business. The chapter owns standards, code review, career growth and design review so we don't end up with eight squads inventing eight ingestion frameworks.
>
> **Where the org goes wrong** is one of two failure modes I've inherited. Pure central team — bottleneck, three-month wait for a new pipeline. Pure embedded — eight frameworks, no governance, eight definitions of 'active customer'. The hybrid is what Techcombank's tribe model already implies; I'd work *with* that grain, not against it.
>
> **On geography** — the Vietnam core for the platform team, with overseas hub presence for the specialist roles — Flink, ML platform, MLOps — where the talent is in Singapore, Bangalore, Eastern Europe. I've run multi-country teams at Lazada and Makro. Async-by-default, weekly sync, quarterly in-person, and a clear rule: every domain squad has a named tech lead in Vietnam.
>
> **Hiring in this market:** fundamentals (SQL, distributed systems, debugging) over tool familiarity. Take-home on a realistic broken pipeline, not algorithm puzzles. Build the pipeline from graduates and analysts as well as buying senior. And retain by interesting problems, modern stack, visible impact — not just comp."

---

### Q5. "Tell us about a platform you built from scratch and the business outcome."

**Why they're asking:** They want a STAR with a *number* and a *choice*, not a list of tools.

> "**Situation.** When I joined Makro in 2024, there was no unified data platform. Twelve countries' worth of data, three legacy data warehouses, multiple business units, and a month-end close that took five days because of manual reconciliation.
>
> **Task.** Build the platform from zero to governed lakehouse in eighteen months, on a Databricks stack, on AWS, with a $3M annual budget and a team I scaled from eight to thirty.
>
> **Action.** I designed a medallion lakehouse — bronze/silver/gold — with open table format, dimensional marts on top, and data contracts at the source boundary. I hired the chapter leads, set the SLOs, and split the team into four domain squads plus a platform squad. I personally ran the architecture review board for the first six months.
>
> **Result.** Today the platform processes ten billion rows a day. Month-end close went from five days to two hours. We delivered fifty-plus executive dashboards. I took forty percent out of the AWS and Databricks spend while we grew. And the same governed layer now feeds ML — pricing, forecasting, segmentation — and the GenAI Text-to-SQL platform we put in production.
>
> **What I'd do better:** I'd start the FinOps initiative in month three, not month nine. The first six months of cloud spend were a missed opportunity."

---

### Q6. "How do you balance build vs buy (lakehouse, MDM, observability, FinOps)?"

**Why they're asking:** This separates operator from theorist.

> "**Four tests, in order.**
>
> **One — is it differentiating?** Nobody wins by building their own scheduler. You might win by building your own feature engineering for fraud. The default is buy for plumbing, build for differentiation.
>
> **Two — what's the true TCO?** Including the two engineers who will own it forever, not just licence versus zero. I have seen 'free open source' cost more than the commercial product because of the people it consumed.
>
> **Three — what's the exit cost?** Can I get my data out in an open format? If the vendor is a lock-in moat, the buy decision needs a written exit plan.
>
> **Four — time-to-value** against the business window. In a bank the window for regulatory reporting is the regulator's window, not yours.
>
> **The line I never cross:** I will not build anything whose failure mode is 'the one person who understood it left'. That's how a Director burns the team's goodwill and the bank's money at the same time."

---

### Q7. "How do you handle data quality, lineage, and governance at scale?"

**Why they're asking:** This is the JD's Level 4 competency. Most candidates are thin here. **This is Prem's most differentiated answer.**

> "The reason governance fails in banks isn't tooling — it's that it's run as a documentation exercise by a central team with no authority. **Four things I insist on, in order of leverage.**
>
> **One — ownership with teeth.** Every domain has a named business **data owner** who is accountable for definitions and access decisions, and a data steward who does the day-to-day. If the owner of 'customer' is the data team, nobody owns customer. The data owner sits in the business; the data team runs the platform that enforces their decisions.
>
> **Two — data contracts at the boundary.** Producing systems commit to schema, semantics, freshness and quality thresholds. The contract is enforced in CI and at ingest — a breaking change fails the build, it doesn't fail my six-am pipeline. This is the single highest-leverage thing I have ever implemented; it moves quality upstream where it is cheap.
>
> **Three — quality measured and published.** Six dimensions — completeness, validity, accuracy, consistency, timeliness, uniqueness — tested as code, with thresholds per dataset, and a visible scorecard. Nothing changes behaviour like a dashboard your peers can see.
>
> **Four — governance in the flow of work.** Certification badges in the catalog so users can see what is trustworthy. Access requests through a workflow, not a favour. Lineage available so impact analysis takes minutes, not weeks. And **active metadata** — metadata that drives behaviour. Classification tags automatically applying masking policies. Freshness SLOs generating alerts. Unused tables flagged for retirement. That is the level I aim for, and it is also what makes GenAI-on-data viable — my Text-to-SQL at Makro only worked because the semantic metadata was good; the LLM was the easy part."

---

### Q8. "Your experience with cloud (AWS/Azure/GCP) and on-prem/hybrid in banking"

**Why they're asking:** They have a hybrid estate — Hadoop on-prem and a cloud target. They want someone who has lived in both.

> "**I have run data platforms on AWS, Azure, Alibaba Cloud, and on-prem Hadoop.** At Makro it is AWS plus Databricks; at Lazada it was Alibaba Cloud plus a heavy Hadoop estate plus Flink and Kafka. At Standard Chartered it was on-prem Hadoop with a regulated architecture. At Xendit I ran a FinOps initiative that took forty percent out of AWS and Databricks spend while volumes grew.
>
> **On banking specifically** — Standard Chartered and DBS taught me that the constraint isn't the technology, it is what you are allowed to put where. **The architecture I would design for a Vietnamese bank is hybrid by default, not cloud-only by ideology.** Hot, latency-sensitive, regulatorily-confined workloads stay close to home. Cold, analytical, elastic workloads move to cloud. **The mistake I have seen in every migration that ran late** is treating hybrid as a transitional state. It is the destination, and the platform had better be designed for it.
>
> **On-prem Hadoop specifically** — I do not do big-bang. I have never seen one land on time. I inventory by workload, kill the dead jobs, dual-run and reconcile to the cent before I cut over, and I am honest with the exec sponsor that during dual-run you pay for both — budget for it or the programme gets killed at month six."

---

### Q9. "How do you drive AI/ML platform adoption with business stakeholders?"

**Why they're asking:** Techcombank's published strategy is heavy on NBO, credit scoring, GenAI — but adoption is the part the platform team owns.

> "**The adoption problem is a data problem, not a model problem.**
>
> **First, kill the 80%.** Every data science team I have inherited spends eighty percent of its time finding and cleaning data. My job is to remove that, not to gatekeep. Concretely: reusable, certified data assets at the right grain; a feature store with an offline store for training and an online store for serving — that is the only reliable cure for training-serving skew; self-service sandboxes with real compute, cost visibility, and a clear promotion path from notebook to production; and point-in-time correct joins as a platform capability, because feature leakage from naive joins invalidates models.
>
> **Second, ship the first one with the business, not for them.** I do not let a model go to production unless an engineering lead has been in the room from design, not at handover. That fixes the two failure modes — the model that does not work in production because nobody owned the data contract, and the model that works in production but is never used because nobody in the business trusts it.
>
> **Third, measure the business, not the model.** A model that improves offline AUC and does not move a business metric is a hobby. The business metric is the only report card. For Techcombank's published NBO ambition, that means a personalisation system with A/B testing tied to incremental revenue per active customer, with fairness and explainability checks for any model that touches a credit-adjacent decision.
>
> **Fourth, the GenAI specific point I'd make to the exec team:** the best GenAI investment a bank can make in year one is usually finishing the data foundation. The LLM is the easy part."

---

### Q10. "Tell us about a failure — what did you learn?"

**Why they're asking:** Director-band honesty test. They are listening for whether Prem can own a judgment failure.

> "**The failure that taught me the most was a launch I led two years in.** Technically it was excellent — clean architecture, good data contracts, SLOs in place. Adoption was ten percent of forecast. I had invested the engineering in the platform and assumed the business would come. They did not, because I had not invested in the change management. I had not given the relationship managers a reason to change how they worked, and the old habit of pulling a CSV was still easier than the new tool.
>
> **The change I made permanently:** I now budget fifteen percent of every data programme's time and effort for adoption. Named user champions in the business, training baked into the rollout, and a 'first win' within thirty days that is small enough to be unblockable. I also stopped letting a programme close on go-live. We close on first business outcome.
>
> **The principle I now hold:** a technically correct platform with insufficient adoption is a failed platform, full stop. As a Director, adoption is my accountability, not someone else's."

---

### Q11. "How do you hire, retain, and grow senior data engineers in a competitive market?"

**Why they're asking:** Vietnam's data engineering market is competitive; they are worried about attrition.

> "**Hire for fundamentals, not tools.** SQL, distributed systems reasoning, debugging a real production pipeline, and clear written communication. Tools are teachable in weeks; fundamentals take years. The take-home exercise I use is a realistic broken pipeline with a real cause — schema drift, late-arriving data, skew — not a LeetCode puzzle. I have hired people who failed the puzzle and passed the pipeline exercise and became senior engineers inside twelve months.
>
> **Build the pipeline, not just buy the senior.** I run a graduate pipeline with a structured rotation across the platform, and I partner with the universities in Ho Chi Minh City and Hanoi that are serious about data engineering. The best senior engineers three years from now are the juniors I hire and develop this year.
>
> **Retain by problems, not just pay.** I cannot win on cash alone; the big tech firms have deeper pockets. I can win on interesting regulated-data problems, a modern stack, and visible business impact. **I never let a good engineer discover their market value from a recruiter first** — I do a comp review twice a year, and I fight for the adjustments I can get. I lose fewer people than my peers because my engineers feel they are growing, not just earning.
>
> **The retention stat I'd want to be known for:** attrition under ten percent in a market running fifteen. The team I built at Makro has not lost a senior engineer in eighteen months."

---

### Q12. "What would you ask the CEO if you had 5 minutes?"

**Why they're asking:** They want to know if Prem thinks at CEO level. They are also testing for ego — candidates who say "I wouldn't need to ask the CEO anything" fail this question.

> "I'd ask three things in five minutes.
>
> **One — what is the one decision the data platform is currently blocking?** Not the wish list. The single thing. Because that is what I would ship in the first ninety days.
>
> **Two — what is the one cultural habit I would need to change to make this platform successful?** Because in a bank the technology is rarely the limiting factor; the operating model is. I want to know the answer to that question *before* I take the job, not after.
>
> **Three — what does the CEO personally use from the data platform today?** If the answer is 'I get a monthly PDF', I have my first project. If the answer is 'I use the live dashboard every morning', I know I have a sponsor."

---

## 4. ELEVATOR PITCH — 3 VERSIONS

### 4.1 30-second pitch (casual reception intro)
> "I'm Prem — I lead data and AI platform engineering. Most recently I built the Databricks lakehouse that runs an eight-billion-dollar retail business across three countries, before that I was at Lazada running the data platform for Southeast Asia's largest e-commerce business, and my career started in regulated banking — Standard Chartered, DBS. I'm here because Techcombank looks like the exact place where both halves of my career meet. And I'm personally very interested in how you're approaching the data lakehouse build."

### 4.2 60-second pitch (panel Q&A opener or senior-leader follow-up)
> "I'm Prem Vishnoi, fifteen years across banking and consumer internet. My career started in regulated banking — I built AML and compliance data platforms at Standard Chartered across fifteen-plus countries, and I worked at DBS before that. Then I moved to consumer-internet scale: Lazada, where I led data engineering for Southeast Asia's largest e-commerce business, and now Makro, where I own the data and AI platform for an eight-billion-dollar omnichannel business across three countries — about thirty people, a three-million-dollar budget, a Databricks lakehouse doing ten billion rows a day.
>
> Techcombank is the intersection I've spent my career on: regulated financial data done at consumer-internet scale, in the most interesting retail-banking market in ASEAN. The Director of Data Engineering role is exactly where I'm most useful — closer to the build, in the engine room, shipping the lakehouse that the bank's published data and AI strategy depends on. That's why I'm here."

### 4.3 2-minute pitch (1:1 with a senior leader at the reception)
> [First 30 seconds = 4.1 above, then:]
>
> "What I am most proud of from the last two years is taking an organisation that had no unified data platform — three legacy warehouses, manual reconciliation, a five-day month-end close — and building, with a team I scaled from eight to thirty, a Databricks lakehouse that today processes ten billion rows a day and has cut that close to two hours. We took forty percent out of the cloud spend while volumes grew. We put a Text-to-SQL GenAI platform in production on top of the governed data layer. We have fifty-plus executive dashboards in use by the CEO, CFO, COO. That is the same muscle I want to bring to Techcombank.
>
> The reason I am looking is specific. I want to be closer to the build, and I want to do it in a domain where the controls matter as much as the scale. I started in banking, I have stayed disciplined in retail, and Techcombank is the first role in five years where I see both halves of my career converging. I am also a Vietnamese TRC holder — I can be on the ground in Ho Chi Minh City inside thirty days — and the market is the one I find most exciting in the region right now.
>
> What I would love to ask you, if you have a minute, is what you see as the single biggest blocker to the data and AI strategy today. The CEO question I always ask first is: what is the one decision the data platform is currently blocking? Whoever answers that wins my first ninety days."

---

## 5. CONVERSATION STARTERS / NETWORKING TACTICS

### 5.1 Likely panel composition and what each person probably cares about
Prem cannot be certain who is on the panel, but the JD and the company PDF give strong signals.

| Likely panelist | What they probably care about | Prem's hook |
|---|---|---|
| **Head of Data Engineering & Delivery** (line manager) | Will you deliver, will you be a peer or a problem, will you be a cultural fit with the team | "I want to be the person who lands the platform, not the one who gives the strategy deck." |
| **CDO or Head of Data** (sponsor) | Will you scale the lakehouse to power AI, will you partner with the business, will you raise the team's capability | "I have shipped the AI-on-data part. I have the scars from the data foundation part. Both halves matter." |
| **CTO or CIO** (technology peer) | Will you integrate with the platform, will you keep the bank secure, will you be sensible on cloud | "Hybrid by design, not by transition. Regulator in the architecture, not the checklist." |
| **CFO or Finance tribe lead** | Will the month-end close get faster, will audit be painless, will the cost story be credible | "I cut month-end from five days to two hours at Makro. Same pattern will work here." |
| **CRO or Risk lead** | Will lineage and audit hold up, will SBV reporting be defensible, will data quality improve | "BCBS 239 as the frame, immutable bronze, signed at the boundary. The audit answer is a reproduction of the number as of the reporting date." |
| **CHRO or People lead** | Will you hire and retain, will you build the pipeline, will you develop local talent | "Fundamentals over tools, pipeline not just purchase, attrition under ten percent." |
| **A senior architect** (peer IC) | Will you defend the architectural bar, will you still review code, will you challenge me | "I read PRs, I run design reviews, I still debug prod. The Director band I want is the one that stays close to the code." |

### 5.2 Three smart questions to ask each panelist type at the reception

**To the CFO / Finance tribe lead:**
1. "What does the month-end close look like today, end to end — and where is the manual reconciliation that hurts the most?"
2. "What is the next SBV reporting change you are preparing for, and how is the data team involved in the design?"
3. "If you could change one thing about the data you receive, what would it be?"

**To the CTO / CIO:**
1. "What is the current split between on-prem and cloud for the data estate — and what is the target over the next three years?"
2. "Where is the integration between the data lakehouse and the new core banking system the most painful today?"
3. "What is the architectural decision you most wish you had made differently two years ago?"

**To the CDO / Head of Data:**
1. "What does the data team look like today — what is working, what would you change if you could?"
2. "Where is the single biggest gap between the data strategy as published and the data platform as delivered?"
3. "What is the AI use case you want to ship first that you cannot ship today — and what is the platform gap blocking it?"

**To the CHRO / People lead:**
1. "Where are you finding senior data engineering talent, and where is the pinch point?"
2. "What does the career path for a senior engineer in the data function look like today?"
3. "How much appetite is there to invest in a graduate pipeline versus buying senior?"

### 5.3 Positioning Prem's AWS Professional Services delivery experience as directly applicable
- **AWS Solutions Architect Associate** + delivery experience is a direct match for Techcombank's AWS/Databricks stack (public reports show Amazon Bedrock use at Techcombank; verify). Prem is not "consulting" — he has *operated* the platforms.
- **Reframe the Xendit FinOps story** as a banking-relevant discipline: "In a regulated environment the cost story is the trust story — if you cannot explain the bill to the CFO, you cannot defend the architecture to the board. I cut forty percent out of cloud spend in a regulated-payments business while growing volumes. That muscle transfers directly."
- **Reframe Makro's "bank-like controls"** explicitly: "My retail platforms are run to financial-controls standard because they feed the statutory close. The audit, lineage, and access-control patterns from SCB AML are the patterns my retail team operates under today."

### 5.4 How to subtly stand out from 3 other candidates without being political

> ⚠️ **The single most important principle of this event:** three other people will be trying to be the loudest, the smartest, the most senior. Prem should try to be the **most prepared, the most specific, and the most useful.**

Concrete tactics:

1. **Be the person with the question, not the person with the answer.** The candidates who ask the best questions get remembered. Use the Q12 line — "what is the one decision the data platform is currently blocking?" — at the reception.
2. **Be specific, not generic.** When asked "tell me about a platform you built", the answer is *ten billion rows a day, month-end from five days to two hours, forty percent cost takeout, 50+ executive dashboards*. Not "we modernised data infrastructure".
3. **Bring one piece of value.** Have one concrete observation that the panel does not already know. Example: "I saw Decision Lab's 2025 ranking has you #1 on satisfaction, and your NPS data would be a fantastic first project for the personalisation roadmap — the model is the easy part, the labelling on your own NPS data is the hard part." That is a sentence only Prem would say.
4. **Use the tribe/squad vocabulary correctly.** It signals Prem has read the JD *and* the company context. Most candidates will use "team" and "stakeholders"; Prem uses "squad, chapter, tribe, paved road."
5. **Close loops.** If Prem says "I'll send you the lakehouse pattern we used at Makro", send the link the next day. Three of the four candidates will not. This alone can be decisive.
6. **Help the other candidates.** Offer to introduce a candidate to someone in your network if you overhear a fit. This is counter-intuitive but it is read as senior behaviour and it is remembered.

### 5.5 What to wear, body language, follow-up plan

**Dress code (Singapore business formal, evening reception):**
- **Default:** dark navy or charcoal suit, white shirt, no tie unless the host's dress code specifies. Conservative.
- **Shoes:** polished, conservative. Black or oxblood.
- **Watch:** wear one. Don't fiddle with it.
- **Grooming:** neat; beard trimmed or clean-shaven. Hair tidy.
- **Bags:** leather laptop bag or portfolio, not a backpack. Have business cards in the *inner* pocket so you do not fumble.

**Body language (the soft signals that decide the reception):**
- **Handshake:** firm, dry, eye contact, smile before you extend the hand. Vietnamese greeting is a slight bow or a handshake depending on context — mirror what the other person does.
- **Name recall:** use the person's name twice in the first ninety seconds, and once at the end. "*Jens, that's a sharp question. Thank you, Jens.*" Most candidates never do this.
- **Posture:** upright, not stiff. Don't lean on walls or bars. Hold your drink in the *left* hand so the right hand is free to shake.
- **Eye contact:** 60/40 — most of the time on the speaker, glance away to think. Do not scan the room while someone is talking to you.
- **Smile:** real, not fixed. The single highest-leverage piece of body language at a reception.
- **Pacing:** slow. Move between groups deliberately. Don't rush.

**Follow-up plan (the part 80% of candidates skip):**
- **Within 12 hours:** send a LinkedIn connection request to every panelist and every 1:1 conversation. Use a short note — **see template below**.
- **Within 24 hours:** send a personalised thank-you email to each panelist you spoke with. **See template below.**
- **Within 48 hours:** if Prem promised anyone a resource (the Makro lakehouse write-up, an article, an introduction), deliver it.
- **Within 1 week:** if there has been no response, send one short follow-up. After that, stop.

**LinkedIn connection request template (under 300 characters):**
> "Dear [Name], I was grateful for the conversation at the Techcombank roadshow on Thursday — the point you made about [one specific thing] stayed with me. I'd welcome staying in touch. — Prem"

**Thank-you email template (under 150 words):**
> Subject: Thank you, [Name] — Techcombank Roadshow
>
> Dear [Name],
>
> Thank you for the conversation at the Techcombank roadshow on Thursday evening. The point you made about [one specific thing they said] stayed with me — it changed how I am thinking about [a specific area].
>
> If it would be useful, I would be happy to share the [specific resource — the Makro lakehouse architecture write-up, the medium article on data contracts, the BCBS 239 mapping, etc.] that I mentioned. No pressure.
>
> Thank you again for your time. I am even more enthusiastic about the Director, Data Engineering role after the conversation.
>
> Best regards,
> Prem Vishnoi

---

## 6. RISKS / GOTCHAS — 4 things that could sink Prem and how to avoid each

### Risk 1: Looking too senior / "why would he take a Director role?"
**Symptom:** Panel wonders if Prem will be bored, will leave in 18 months, or will go over the Head of Data Engineering & Delivery's head.
**Avoidance:**
- **Own the framing in the first 60 seconds.** "I'm deliberately looking for this level. At Makro my span grew faster than my hands-on time, and I miss it. The Director band I want is the one that stays close to the build."
- **Never posture as the CDO.** Prem reports to the Head. Talk about *landing delivery for the Head*, not "my vision for data at the bank."
- **Use "we" liberally and "I" sparingly** when talking about platform-wide moves.

### Risk 2: Looking like a retail person who dabbled in banking
**Symptom:** Panel hears "Lazada, Makro" and thinks "not a real banker."
**Avoidance:**
- **Lead with the banking origin in every version of the pitch.** SCB AML across 15+ countries, DBS, MAS regulatory exposure.
- **Use the language of controls, not just the language of platforms.** "Audit-grade lineage" not "nice dashboards". "Reconciliation to source control totals" not "data quality".
- **Anchor the Makro story in the month-end close.** That is banking discipline applied in retail. Make the connection explicit.

### Risk 3: Bluffing on Flink (or any other depth question)
**Symptom:** Panel asks "have you run Flink in production?" and Prem fudges. One of the other three candidates will be a former Flink engineer. This will be exposed.
**Avoidance:**
- **Pre-empt with the honesty line from TECHNICAL_ROUND_QA §C3, line 207:** "I've run Spark Structured Streaming in production at scale. Flink I know architecturally and have evaluated, but I'd be overstating it to claim I've operated a large Flink estate. If that's core here, that's something I'd ramp on fast and I'd hire or grow the depth in the team rather than pretend."
- **Pivot to the architectural strengths that are Flink-relevant:** event time vs processing time, watermarks, checkpointing with RocksDB state backend, exactly-once via two-phase commit, side outputs for late data. These are language-agnostic and the panel will read them as serious.
- **Never bluff Rust, Kotlin, or any depth question.** A Director who bluffs gets found out in week three. Honesty reads as senior, not weak.

### Risk 4: Cultural missteps on the night (Vietnamese business culture, hierarchy, "face")
**Symptom:** Prem comes across as too direct, too casual, or too American. Vietnamese business culture values hierarchy, restraint, and "face" (giữ thể diện) — both one's own and others'.
**Avoidance:**
- **Address the most senior person in the room first.** Not obsequiously; just a clear acknowledgement of the pecking order.
- **Use titles.** "Mr. [Surname]", "Ms. [Surname]" until invited otherwise. Do not assume first-name basis even with peers.
- **Be restrained in disagreement.** If challenged, say "*That's a fair point. Let me think about it.*" Do not push back hard in front of a more senior person. Save the technical challenge for the architect peer, in private.
- **Listen more than talk at the reception.** Vietnamese business culture rewards the patient listener. Prem's natural advantage — he has the substance — is undermined if he talks too much.
- **Reciprocate hospitality.** If someone offers a drink, accept; do not refuse outright. If they toast, return it.
- **Never criticise Vietnam publicly** — not the regulator, not the infrastructure, not the talent market. Speak in "what's exciting about working here" not "what needs to be fixed."
- **Gifts and cards:** the standard at an event like this is a business card exchange, not gifts. Prem's cards should be clean, two-sided if needed, with Vietnamese on one side if he has time before Oct 23. **He should have 30+ cards in his inner pocket, not 10.**

### Things Prem should NOT say (one-line cheatsheet)
- "I would do it differently" — *without immediately naming what is right about the current strategy.*
- "I don't do hands-on anymore" — *he does, and the panel needs to believe it.*
- "My team does it this way" — *the JD says tribe/squad; use that vocabulary.*
- "In my experience" — overused filler; cut it.
- Anything critical about Makro, Lazada, Standard Chartered, DBS, or Xendit. *No negatives on past employers.*
- "Vietnam is behind Singapore" or any variant. *Do not. Ever.*
- "I would build it from scratch" without explaining what to do with the existing estate.
- "AI will replace" or "AI won't replace" — *stay out of the AI theology debate.*
- Specific SBV circular numbers or dates that have not been verified. *Speak in principles, not specifics.*
- A specific salary number first. *"I'd rather understand the level and scope properly first" — see TECHNICAL_ROUND_QA §12, line 442.*

---

## 7. 24-HOUR PRE-EVENT CHECKLIST

### Tonight (Oct 22) — research and preparation

**Research (90 min total):**
- [ ] Read the **Techcombank 2025 Annual Report** summary on the company website. Note any new CDO/CIO appointment, the data platform language they use, the regulatory references.
- [ ] Read the **two most recent Techcombank press releases** on data / AI / digital. Quote one specific phrase from one of them in the 2-minute pitch.
- [ ] Skim Decision Lab's 2025 Bank Satisfaction Rankings (Vietnam News, 21 Apr 2025) and the 6M26 press release; read the 9M26 release (20 Oct).
- [ ] Read the **two most recent Techcombank LinkedIn posts from the CEO** (Jens Lottner) so Prem can reference one specific initiative in conversation.
- [ ] Identify the **panelist names** from the RSVP / agenda if Techcombank publishes them. If not, ask the recruiter for names tomorrow morning.
- [ ] **LinkedIn research:** for each panelist, find their last 5 posts. One specific question per panelist, prepared in advance.

**Numbers to memorise cold (no prompting):**
- [ ] 18.2M customers (6M26), 66.3% digitally acquired, PBT VND 18.5T +22.5% (6M26 release)
- [ ] #1 Decision Lab 2025; NIM LTM 3.6%; CASA 38.3%; NPL 1.15%; CIR ~30%
- [ ] Databricks adopted Oct 2024 (50+ systems, 45+ ML models)
- [ ] Prem's CV: 15+ years, ~30 people, $3M, 10bn+ rows/day, 5 days → 2 hours, 50+ dashboards, 40% cloud cost takeout, 100M+ events/day at Lazada, 15+ countries at SCB

**Talking points to rehearse out loud (3× each, timed):**
- [ ] 30-second pitch (Section 4.1) — **under 35 seconds spoken, no umms**
- [ ] 60-second pitch (Section 4.2) — **under 70 seconds spoken**
- [ ] 2-minute pitch (Section 4.3) — **under 2:10 spoken, with one pause to look up**
- [ ] Q2 answer (90 days plan) — **under 90 seconds**
- [ ] Q5 answer (Makro platform from zero) — **under 90 seconds, with the numbers**
- [ ] Q7 answer (data governance, the differentiator) — **under 90 seconds, delivered as the strongest answer of the night**
- [ ] Q10 answer (the failure) — **under 90 seconds, no defensiveness**
- [ ] The honesty line on Flink — **relaxed, not apologetic**

**Outfit and materials:**
- [ ] Suit pressed, shirt pressed, shoes polished. Backup shirt in the bag.
- [ ] Belt and shoes same colour. Tie decided (or no tie, decided).
- [ ] **30+ business cards** in the inner left pocket, with Vietnamese side if possible.
- [ ] Notebook: small, leather-bound, **with 4 questions pre-written** on the inside cover (one architectural, one people, one success, one "the past person in this seat").
- [ ] Pen: a real pen, not a hotel pen. Black ink.
- [ ] Phone: charged, on silent, **personal notifications off**. Only the recruiter's number on vibrate.
- [ ] Breath mints. Glass of water before walking in.
- [ ] Copy of Prem's CV in the bag, in case anyone asks.
- [ ] A copy of one of Prem's Medium articles on data engineering, as a leave-behind if asked. *Do not* push it on anyone.

### On the day (Oct 23) — final 3 hours

**T-3 hours (15:00 SGT):**
- [ ] Light meal. Not heavy; you'll be standing for 3 hours.
- [ ] Read this battle card once. **Do not** re-memorise; trust the rehearsal.
- [ ] One slow walk outside the hotel for ten minutes. Land your breathing.

**T-1 hour (17:00 SGT):**
- [ ] Arrive at PARKROYAL COLLECTION Marina Bay. **Be 15 minutes early, not 30.** The networking advantage of being early is the chance to meet the panel before the room fills.
- [ ] Check in with the host. Get a name and a face for one person on the inside.
- [ ] Identify the **first 1:1 target** for the reception. The smartest move is the **most junior person on the panel** — the architect or the data product lead — who is most likely to be honest about the role. The best 1:1 at a reception is often the one nobody else is trying to have.

**T-0 (18:00 SGT) — Opening Remarks through Strategy Spotlight:**
- [ ] Sit where you can see **all** of the panel. Not at the back.
- [ ] **Write down one specific phrase from the Strategy Spotlight** that you will reference in your first 1:1. The panel will be flattered.
- [ ] Do not look at your phone.

**T+30 (18:30 SGT) — Panel Discussion + Q&A:**
- [ ] **Ask one question if the floor opens.** The question should be the one Prem has prepared — "what is the one decision the data platform is currently blocking?" — and it should be **asked only if no one else asks it well**. If someone else asks a better one, do not duplicate.
- [ ] If not asking, **make eye contact with the panelist who is answering**, and nod when they say something Prem has a follow-up on. The eye contact is the seed of the 1:1 later.
- [ ] Have one specific phrase from the answer written in the notebook.

**T+80 (19:20 SGT) — Networking Reception:**
- [ ] **First 10 minutes:** stand near the bar, not in a corner. Smile. Be introduced by the host if possible.
- [ ] **Three 1:1s, not ten.** Quality over quantity. Target:
  1. **The most junior panelist** (architect, data product lead) — 7 minutes. *Ask* about the team and the architecture. Listen 70%.
  2. **The CDO / Head of Data** (or the most senior person who is not the CEO) — 7 minutes. *Ask* the Q12 question — "what is the one decision the data platform is currently blocking?" Listen carefully. Take notes after.
  3. **One cross-functional panelist** (CFO/CRO/CTO) — 7 minutes. *Ask* the question from §5.2 that matches their function.
- [ ] **Between 1:1s:** introduce yourself to one or two other candidates *briefly* and *positively*. Do not interrogate them. They are not the enemy; the panel is watching how Prem treats them.
- [ ] **One leave-behind:** if the right moment comes, offer the Medium article. *Only* if the right moment comes. Most of the time, it is a LinkedIn connection that lands the follow-up.
- [ ] **Last 15 minutes:** do not leave early. The last 15 minutes of a reception is where the most candid conversations happen. Stay until at least 20:45. Thank the host by name on the way out.

**Within 12 hours of leaving (before sleep):**
- [ ] Send LinkedIn connection requests to every panelist and 1:1.
- [ ] Send the personalised thank-you email to each panelist.
- [ ] Write down three observations from the night that did not make it into the card. These become the substance of the second-round interview.

---

## 8. CLOSING — THE TWO SENTENCES THAT SHOULD STICK

If Prem only gets to say two things at the end of the night, they should be:

> "I've spent fifteen years on the exact intersection this role sits on — regulated banking data at consumer-internet scale. I want to land the delivery for you. The first thing I'd want to know is: what is the one decision the data platform is currently blocking?"

The first sentence is the **fit**. The second sentence is the **bias to action** that the JD rewards. Together, they make Prem the candidate the panel remembers on Saturday morning.

---

### Assumptions I flagged (Prem — please correct any that are wrong)
- I assumed the panel likely includes a Head of Data Engineering & Delivery, a CDO/Head of Data, a CTO/CIO, a CFO or Finance tribe lead, a CRO/Risk lead, and a senior architect. If the actual composition is different, the questions in §5.2 should be re-mapped.
- I assumed the format is "panel speaks for 30 minutes, then moderated Q&A for 20 minutes" based on the 18:30–19:20 block. If the Q&A is shorter or the panel allows candidate questions, the strategy shifts.
- I assumed the dress code is "business formal, evening reception" — the default for a Singapore bank roadshow at a 5-star venue. If the host has specified cocktail or business casual, adjust.
- I have not named any specific public Techcombank leaders other than Jens Lottner, because the company PDF did not name them and I want Prem to be precise, not speculative.
- I have not assumed Prem's specific compensation expectations or notice period — those are §12 of TECHNICAL_ROUND_QA, line 442, and the recruiter, not the panel, is the right venue.

---

*End of battle card. Length: ~5,400 words. Copy-paste ready.*
