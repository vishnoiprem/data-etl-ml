# Amazon Senior Data Sales Specialist — FULL SCRIPTED ANSWERS (Prem Vishnoi)

> **July 21, 2026 · 4–5pm ICT · Son Vu (AM, ENT-FSI Vietnam)**
> Every likely question with a complete answer. **Rehearse these OUT LOUD** — 3 times each. Don't memorize word-for-word; internalize the structure and the numbers.

---

## ⏱️ How the 60 Minutes Will Likely Run
| Time | What happens | Your job |
|------|--------------|----------|
| 0–5 min | Intros, small talk | Warm, confident. Build FSI/Vietnam rapport. |
| 5–10 min | "Tell me about yourself" | 90-sec pitch that pre-empts the sales gap |
| 10–35 min | Functional/technical probing | Whiteboard-level fluency + consultative stories |
| 35–50 min | 2–3 LP behavioral questions | STAR, "I", metrics |
| 50–60 min | Your questions | Ask 3 sharp ones |

---

# SECTION 1 — THE OPENING (get this perfect)

## Q1: "Tell me about yourself."
**⚠️ This is your most important answer. It must pre-empt the sales gap before he asks.**

> "I'm a data and AI leader with 15 years building enterprise data platforms across Southeast Asia — in banking, e-commerce, and retail.
>
> Today I'm Head of Data Engineering at Makro, part of CP Group, where I own the data, analytics and AI strategy for an $8 billion omnichannel retail business across three countries. I lead a 30-person organisation and own a $3 million budget — which means I'm also the person who evaluates, negotiates with, and buys from cloud and data platform vendors.
>
> Before that I was VP of Data Engineering at Lazada, Alibaba's e-commerce arm, and before that I built AML and compliance data platforms at Standard Chartered across 15+ countries, and worked at DBS — so financial services is where I started.
>
> Now, I want to be direct about something: I haven't carried a sales quota. What I bring instead is that I've been on the *other side of the table* — the enterprise data buyer and builder. I know how a CIO or CDO actually evaluates a data platform, where modernization projects break, and what makes a customer commit. And I can whiteboard the architecture, not just the slideware.
>
> That's why this role interests me — bringing real technical credibility to help ASEAN customers build the data foundations that make AI actually work."

**Why this works:** Establishes scale + FSI + buyer credibility, and takes the sting out of the gap by naming it yourself with confidence.

## Q2: "Why AWS? Why this role?"
> "Three reasons.
>
> First, timing. Every enterprise I talk to wants GenAI, but most can't get it into production — because their data foundation isn't ready. That's not a model problem, it's a data problem. I've lived it: I built a Text-to-SQL GenAI platform and the hard part was never the LLM, it was the governed data underneath it. AWS owns that entire stack.
>
> Second, the portfolio. AWS's lakehouse approach — one governed copy of data serving both analytics and AI, on open Iceberg — is genuinely the right architecture. I've built the equivalent on other platforms, so I'm not repeating marketing; I believe it.
>
> Third, this is where I want to grow. I've spent 15 years building. I want to apply that depth at customer scale — across many enterprises rather than one — and be the trusted technical advisor in the room when a CDO is making a bet."

---

# SECTION 2 — FUNCTIONAL / TECHNICAL (the biggest block)

## Q3: "Walk me through helping a customer build a modern data foundation."
*(Frame internal stakeholders as customers — that's legitimate.)*

> "**Situation:** At Makro, the finance organisation was closing the books manually over five days. The root cause wasn't finance — it was fragmented legacy data across finance, supply chain, retail and e-commerce, with no single source of truth.
>
> **Task:** I owned the enterprise data strategy and had to modernize the foundation.
>
> **Action:** I started with the business problem, not the technology. I quantified the cost of the slow close, built the business case for a lakehouse modernization, and got executive sponsorship for a $3M program. Then I designed and led delivery of a Databricks Lakehouse processing 10 billion-plus rows daily, with a medallion structure — raw, conformed, curated — so one governed foundation could serve BI, ML and GenAI. I personally drove the change management, because the technical build was never the risk; adoption was.
>
> **Result:** Month-end close went from five days to two hours. We delivered 50-plus executive dashboards, launched near real-time inventory visibility across 200 stores and 5 distribution centres, and ML demand forecasting across 1,000-plus vendors.
>
> On AWS, that same journey maps directly onto S3 with Iceberg tables, SageMaker Lakehouse unifying lake and warehouse, Lake Formation for governance, and Redshift and Athena for consumption."

## Q4: "How would you position AWS to a CIO or CDO?"
> "I never lead with services — I lead with their problem.
>
> To a CDO I'd say something like: 'You've told the board you're doing AI this year. But your data is spread across an on-prem warehouse, three databases, and a lake. You're copying data between them, governance is inconsistent, and your engineers spend most of their time maintaining pipelines instead of creating value. So your AI pilots work in a demo and stall in production.'
>
> Then I'd draw it: one governed copy of data on S3 with Iceberg, lake and warehouse unified through SageMaker Lakehouse, fine-grained governance in Lake Formation, zero-ETL replacing the pipelines they're maintaining by hand — and Bedrock and Amazon Q sitting on top so AI is reading trustworthy data.
>
> And I'd close on the business case: how many engineers are maintaining pipelines today, and what would you do with that capacity back?"

## Q5: "How do you handle competitors — Databricks, Snowflake, Fabric?"
**⚠️ The JD explicitly asks about "compete vs collaborate." Show judgment, not aggression.**

> "First, I'd say I've *used* these platforms — I run Databricks at Makro today — so I can speak about them honestly rather than from a battlecard.
>
> The judgment call is compete versus collaborate. If a customer is deeply committed to Databricks and it's working, trying to rip it out damages trust and usually loses. But Databricks runs on AWS — so I'd collaborate: help them optimize on AWS infrastructure, and grow consumption on storage, streaming and the services around it.
>
> Where I'd compete is on openness and TCO. AWS's lakehouse is built on Apache Iceberg, so the customer isn't locked into one vendor's format. And because you can federate to Snowflake or BigQuery rather than migrate everything, the customer gets a path that doesn't require a risky big-bang.
>
> My rule: lead with the customer's problem. If our answer is genuinely better, that shows up in the architecture conversation. If it isn't, I'd rather keep the relationship and win the next workload."

## Q6: "How do you work with Solutions Architects, Professional Services, and partners?"
> "In my experience the specialist's job is to bring the point of view and the business case; the SA validates and deepens the architecture; ProServe and partners de-risk delivery.
>
> Concretely, at Makro I ran a large modernization with vendor and partner teams under a $3M budget. My role was to own the outcome — define the architecture direction and success criteria, then hold everyone to them. I've also worked cross-functionally at Lazada with product and data science teams to industrialise ML models from prototype into production with monitoring and governance.
>
> For this role, the thing I'd add for an account manager is that I can go deep with the customer's engineers *and* translate it upward to the CFO's business case — so you don't need two separate people in the room."

## Q7: "How do you connect data foundations to GenAI and agentic AI?"
**🔑 Your strongest technical differentiator — take your time here.**

> "This is the conversation I most want to have with customers, because most get it backwards.
>
> I built a Text-to-SQL GenAI platform at Makro — business users ask questions in plain English and get answers from enterprise data. Everyone assumes the hard part is the LLM. It isn't. The LLM was the easy part. The hard part was everything underneath: schema understanding, a semantic layer so the model knows what 'revenue' actually means in our business, and guardrails — validating generated SQL, enforcing read-only access, limiting result sets, and re-prompting when the query was wrong.
>
> That's the lesson: **AI is only as good as the governed data foundation beneath it.** Agentic AI raises the bar further, because agents take actions — so they need not just data but *context and constraints*, or they confidently do the wrong thing.
>
> So when a customer says 'we want agentic AI,' my first questions are: is your data unified and governed? Do you have a semantic layer? Can you control what the agent is allowed to see and do? That's a lakehouse and Lake Formation conversation before it's ever a Bedrock conversation. And that sequencing is exactly where AWS is strong."

## Q8: "Tell me about a migration — Oracle, SQL Server, or legacy warehouse."
> "I've done the legacy warehouse side directly — I worked extensively with Teradata earlier in my career, and at Makro I led the migration off legacy systems onto a modern lakehouse.
>
> What I learned is that these migrations fail for non-technical reasons. The technology path is well understood. What kills them is: nobody quantified the business case, the workloads weren't prioritised so the team tried to move everything at once, and the users didn't trust the new numbers.
>
> So my approach is: prioritise workloads by business value and migration difficulty, land a visible win early to build credibility, run old and new in parallel until the numbers reconcile exactly, and only then decommission. At Makro I ran exactly that parallel reconciliation with finance before cutting over.
>
> For an Oracle or SQL Server motion on AWS, the pitch is straightforward — move to Aurora PostgreSQL, drop the licensing cost, keep the SQL skills. The urgency lever is usually a renewal date."

## Q9: "Do you have quantifiable results? Deal sizes, revenue?"
**⚠️ Be honest, then redirect to what you DO have.**

> "I'll be straightforward — I don't have quota attainment or closed-deal numbers, because I've been on the delivery and buying side.
>
> What I do have is the numbers that matter to a customer's business case. I own a $3 million budget and serve an $8 billion business across three countries. I've delivered a platform processing 10 billion-plus rows daily, and at Lazada a real-time platform handling 100 million-plus events daily producing 20 million daily insights. I took month-end close from five days to two hours. I scaled an organisation from 8 to 30 people. I've negotiated and managed multi-million dollar vendor contracts.
>
> And on adoption — which I'd argue is the metric that actually predicts renewal — I drove 50-plus executive dashboards into daily use and rolled out GenAI analytics to non-technical business teams who'd never written a query.
>
> So my numbers are business-outcome numbers rather than bookings numbers. In a technical sale to a CDO, those are the numbers that win the room."

---

# SECTION 3 — THE 5 TESTED LPs (full STAR scripts)

> **Rules:** "I" not "we". Metrics in every answer. 90 seconds each. Don't ramble.

## 🎯 Customer Obsession
**Q: "Tell me about a time you worked backwards from a customer need."**

> "**Situation:** At Makro, business teams in merchandising and marketing needed data to make daily decisions, but every question meant filing a request with the analytics team and waiting days. They were making decisions on gut feel because the data was too slow to be useful.
>
> **Task:** I wanted to put answers directly in their hands, not build another dashboard they'd have to ask us to change.
>
> **Action:** I started by sitting with them to understand how they actually ask questions — in plain business language, not SQL. So I designed a Text-to-SQL GenAI platform. I built the semantic layer so business terms mapped correctly to our data model, engineered prompts and guardrails so results were accurate and safe, and I personally ran hands-on enablement sessions with non-technical users, because I knew adoption would be the real test.
>
> **Result:** Business users started self-serving questions that previously took days. Adoption spread across merchandising and marketing. And it changed our team's role — we moved from being a bottleneck answering ad-hoc requests to building capability.
>
> The lesson I carry: the customer didn't want a dashboard, they wanted an answer. Starting from their behaviour, not our tooling, is what made it work."

## 🎯 Learn and Be Curious
**Q: "Tell me about a time you had to learn something new."**

> "**Situation:** When the business asked for conversational analytics, GenAI and LLMs were outside my core expertise. My background was data engineering and classical ML, not language models.
>
> **Task:** I needed to get genuinely competent fast — not enough to talk about it, enough to ship it to production.
>
> **Action:** I invested in structured learning — I'd already completed UT Austin's AI/ML program, and I took an agentic AI systems certification, and I'm currently doing a Master's in Data Science at Northwestern. But more importantly I learned by building: I prototyped RAG approaches, tested embedding models for our item-matching problem, and learned guardrail design largely by watching my own early versions fail — generating plausible SQL that was subtly wrong.
>
> **Result:** I shipped the Text-to-SQL platform to production, plus an embedding-based item matching pipeline that deduplicated SKUs across online and offline channels. And it reshaped how I think — agentic AI is now central to how I approach data strategy, not a side topic.
>
> I also write on Medium about data architecture and leadership, which forces me to keep learning in public."

## 🎯 Insist on the Highest Standards
**Q: "Tell me about a time you refused to accept 'good enough'."**

> "**Situation:** During the Makro finance automation, we reached a point where the automated close was working and the team wanted to ship. The numbers were close to the manual close — but not identical.
>
> **Task:** Decide whether 'close enough' was acceptable for financial reporting.
>
> **Action:** I said no. For financial numbers, 'nearly right' is the same as wrong — it's a regulatory and trust issue, not a rounding issue. I insisted we run the automated close in parallel with the manual process for multiple cycles, and I made the team investigate every single discrepancy until we understood the root cause. Some were genuine data quality issues we'd have shipped into production. This was unpopular — it delayed the cutover and people felt we were being pedantic.
>
> **Result:** When we finally cut over, close went from five days to two hours *and* finance trusted the numbers completely — no shadow spreadsheets, no parallel manual checking. If I'd shipped early, we'd have spent the next year fighting credibility problems and finance would have kept their own version.
>
> The high standard wasn't perfectionism — it was recognising that trust, once lost with a finance team, is extremely expensive to rebuild."

## 🎯 Deliver Results
**Q: "Tell me about a time you delivered a difficult result."**

> "**Situation:** At Lazada, one of Southeast Asia's largest e-commerce businesses, logistics needed real-time visibility into last-mile delivery. The existing platform was batch-based and couldn't scale to the event volume — so operations were making routing decisions on stale data across multiple markets.
>
> **Task:** Deliver a real-time data platform at very large scale, in production, across markets.
>
> **Action:** I architected the platform end to end — Kafka for ingestion, Flink for stream processing, ClickHouse for fast analytical queries and HBase for low-latency lookups. I chose Flink over micro-batch alternatives specifically because true event-time processing mattered for delivery SLAs. I drove the build and the rollout across markets, and built the logistics analytics engine on top.
>
> **Result:** The platform processed 100 million-plus events daily and generated 20 million-plus daily insights, directly improving delivery routing and visibility. It moved logistics data from reporting into actual decision support. I earned a double promotion for the platform's impact and cross-functional leadership.
>
> What made it deliver was focusing on the input that mattered — latency — rather than trying to build every feature at once."

## 🎯 Invent and Simplify
**Q: "Tell me about a time you simplified something."**

> "**Situation:** At Makro, we were expanding into new countries. The first expansion was painful — the team essentially rebuilt data pipelines, reporting, and integrations from scratch, and it was slow and expensive.
>
> **Task:** Make every subsequent country expansion faster and cheaper, without a bigger team.
>
> **Action:** Instead of treating each country as a project, I designed a reusable foundation — common architecture patterns, standardised reporting templates, and repeatable integration patterns. I deliberately resisted the pressure to customise per country, because customisation is what makes platforms unmaintainable. Where local requirements genuinely differed — regulatory reporting, for example — I handled it through configuration rather than separate codebases.
>
> **Result:** New countries onboarded onto a common foundation much faster, with lower cost and fewer people. It also meant a fix or improvement made once benefited every market instead of needing three separate implementations.
>
> That's the pattern I look for generally: the invention is the reusable platform, the simplification is refusing to let it fragment."

## 💡 FAILURE STORY (they will ask — have this ready)
**Q: "Tell me about a time you failed."**

> "**Situation:** Early in a machine learning initiative, I led development of a forecasting model that performed well in testing but underperformed badly once it hit production.
>
> **Task:** Understand why, and fix it.
>
> **Action:** When I dug in, the failure was mine and it wasn't the algorithm. I'd underestimated two things. First, data readiness — the historical data had quality gaps and inconsistencies that didn't show up in my curated test set. Second, and more important, I'd built it without deeply enough involving the business users who'd have to act on the output, so when the model's recommendations conflicted with their intuition, they simply didn't use it. A model nobody uses has zero value regardless of its accuracy.
>
> **Result:** I changed my approach permanently. Now I validate data readiness before committing to a model, and I involve the business owner from problem framing — not at handover. I applied that directly to the dynamic pricing model at Makro: I framed the problem *with* the commercial team from day one, and drove adoption with merchandising as part of the project, not as an afterthought. That one landed and influenced pricing across the catalogue.
>
> The lesson: in data and AI, adoption risk is usually bigger than technical risk — and it's the one people forget to plan for."

---

# SECTION 4 — YOUR QUESTIONS (ask 3)

1. **"For FSI accounts in Vietnam and across ASEAN, where's the strongest data demand right now — Oracle and SQL Server migration, lakehouse modernization, or GenAI enablement?"**
2. **"How does the data specialist add the most leverage for you as an account manager — is it early architecture credibility, or later in the deal?"**
3. **"The JD says 'build the playbook, not just run it.' What's still unwritten that you'd want a specialist to figure out in ASEAN?"**
4. **"Given my background is technical delivery and the buyer's seat rather than quota-carrying sales — what would you want me to ramp on fastest?"** *(shows self-awareness)*
5. **"How do you approach compete-versus-collaborate with Databricks and Snowflake in regulated FSI accounts here?"**

---

# SECTION 5 — FINAL CHECKLIST

**Content ready:**
- [ ] 90-sec intro rehearsed out loud (3x) — pre-empts the sales gap
- [ ] 5 LP stories + 1 failure, all in "I", all with metrics
- [ ] Can whiteboard: Ingest → Store → Process/Govern → Consume
- [ ] Can name: SageMaker Lakehouse, S3 Tables, Iceberg, zero-ETL, Lake Formation, Redshift, Athena, Bedrock, Amazon Q
- [ ] Compete-vs-collaborate answer ready
- [ ] FSI story (SCB AML, MAS compliance) front-loaded for Son Vu
- [ ] Vietnam TRC mentioned naturally
- [ ] 3 questions ready

**Logistics:**
- [ ] Zoom tested, video on (recommended — builds rapport)
- [ ] Quiet room, good headset, strong connection
- [ ] Join 10 min early (waiting room admission can take time)
- [ ] Bangkok = Vietnam time, GMT+7 — 4:00pm ICT
- [ ] Paper + pen ready (you may be asked to describe an architecture)
- [ ] Notes visible but don't read from them

**Mindset:**
> Don't apologise for not being a traditional seller. You're the technical leader who's been the buyer — that's rarer and more valuable in a CXO conversation than another quota-carrier. Confidence, not defensiveness.
