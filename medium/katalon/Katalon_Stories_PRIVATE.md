# Katalon Head of Data — YOUR story bank (Lazada + current retailer)

> LOCAL ONLY. Gitignored (`medium/katalon/*_PRIVATE.md`). Do not move into a tracked path.
> Companion to `Katalon_Head_of_Data_Interview_Prep.md` Section 21.
> Built from `medium/meta/coach/resume-facts.md`. Every number below is a claim from your resume.
> `[CONFIRM: ...]` = I do not know this; fill it from your memory **before** you say it out loud.
> `[HYPOTHESIS]` = a plausible mechanism I inferred; keep it only if it is true for you.

Legend: 🔵 hook · 🟡 tip · 🟢 spoken draft · 🔴 attack you must be ready for

---

## 0. Your positioning in one breath (open every conversation with this)

🟢 *"I'm a Head of Data with 15 years across e-commerce, payments and retail. I spent five and a half years at Lazada, part of Alibaba, building event and analytics platforms at 100-million-plus daily events, and now I run the data platform at a retailer in Thailand, with a team that grew from 8 to 25. My pattern is the same in both: make the numbers trustworthy, make the platform cheap and reliable, then put AI on top of clean data. That's why Katalon's brief — strategy, platform, governance and AI-ready data, in a SaaS company — fits exactly."*

🔵 **Hook: "Scale at Lazada, trust and cost at the retailer, AI on top."**

### Why this role fits (the level problem from Meta is gone here)

For Meta you had to explain going from Head to IC. For Katalon the title **matches** your resume. Your risk flips:

| Risk | What they may probe | Your honest line |
|---|---|---|
| **Retail/e-commerce, not SaaS** | "You haven't worked at a B2B SaaS company." | *"The mechanics transfer: events, funnels, cohorts, retention, subscription-style KPIs. What's new for me is SaaS metrics like NRR and PQL, which I'd learn from your Finance and Sales teams in the first 30 days."* [CONFIRM: any subscription/membership, marketplace seller or B2B or wholesale-customer analytics you did — that is your bridge]. |
| **Xendit ~6 months** | "Why so short?" | See Story S9 below. Non-bitter, factual. |
| **Hands-on vs manager** | "Can you still build?" | Lead with Airflow/Spark/dbt/Databricks specifics; offer to whiteboard. |
| **Tool names** | They list Snowflake/BigQuery/Redshift; you list Databricks/Alibaba Cloud/ClickHouse | *"Same concepts: storage/compute separation, partitioning, cost control. I've run Databricks and AWS; I'd evaluate Snowflake on the same criteria."* Never claim Snowflake production experience you don't have. |
| **Generative AI depth** | "RAG in production?" | [CONFIRM: a real GenAI/RAG project at the retailer, scope and users]. If it was a pilot, say pilot. |

---

## S1 — Built and scaled a data platform (JD: "Build and scale modern data platforms")

**Two source stories — pick by the interviewer:**
- **Retailer Lakehouse** (current, Databricks, Unity Catalog, Delta Lake): 10B+ daily rows, 99.99% uptime, 500+ daily jobs.
- **Lazada event platform** (Alibaba stack, Flink + ClickHouse): 100M+ daily events, 10x growth, 600+ production tables.

🟢 **Retailer draft (C-C-T-M):**
> *Situation:* The retailer (a large business in Thailand) needed one trusted platform behind stores, O2O and finance. [CONFIRM: what existed before — silos? on-prem? multiple warehouses?]
> *Task:* I owned the platform end to end — architecture, reliability, cost and the team.
> *Action:* (1) Built a Databricks lakehouse on Delta Lake with Unity Catalog for access control and lineage; (2) standardised layers — raw, cleaned, business marts — with Airflow orchestration and dbt/Spark transformations; (3) put SLOs on the critical jobs. [CONFIRM: your actual three biggest decisions, and the one alternative you rejected and why.]
> *Result:* 10B+ rows a day, 500+ daily jobs, 99.99% uptime [CONFIRM: *what* uptime measures — job success, API availability, or data freshness SLA?].
> *Reflection:* [CONFIRM: one thing you would do differently, e.g. contracts earlier].

🟢 **Lazada draft:**
> *Situation:* Lazada's event volume grew 10x to 100M+ daily events and the existing reporting could not keep up with real-time questions.
> *Task:* [CONFIRM: your scope vs the team's — they will ask] I owned the real-time analytics path and 600+ production tables.
> *Action:* (1) Streaming ingest to Flink; (2) ClickHouse as the serving store for low-latency analytics; (3) layered modelling — your resume lists ODS/CDM/ADS — plus ownership and lineage for the tables.
> *Result:* 100M+ daily events at 10x growth. "20M+ insights per day" — 🔴 **define "insight" (e.g. dashboard queries/API responses served) or drop the phrase.**
> *Reflection:* [CONFIRM].

🔴 Attacks: "How did you measure 99.99%?" · "What broke first at 10x?" · "Why ClickHouse over the warehouse?" · "How do you govern 600+ tables?" (answer: owners per domain, tiering, tests on Tier-1 only, retire unused tables from query logs).

🔵 **Katalon link:** product telemetry + CRM + billing needs exactly this: events in, trusted marts out, serve to BI and ML.

---

## S2 — Fixed trust in numbers (JD: "governance, quality, KPIs")

**Source:** Retailer month-end close **5 days → 2 hours**; incidents **−60%**.

🟢 **Draft:**
> *Situation:* Month-end close took about five days because finance numbers had to be reconciled by hand across systems. [CONFIRM: which systems — POS, ERP, supply chain, promotions?]
> *Task:* Make the close fast and the numbers trustworthy; Finance had to sign off on the result.
> *Action:* (1) [CONFIRM: the real bottleneck — HYPOTHESIS candidates: manual extracts, late-arriving feeds, inconsistent store/product keys, reruns after corrections]; (2) automated the pipeline with quality gates and reconciliation to the source ledgers; (3) agreed a single definition and owner for each close metric with Finance.
> *Result:* Close fell from 5 days to 2 hours [CONFIRM: is this the *data-availability* step or the whole close? Finance may say the full close is longer — be exact]. Platform incidents down 60% [CONFIRM: baseline count/month, incident definition, severity mix, period].
> *Reflection:* [CONFIRM].

🔴 Attacks: "60x is huge — what exactly was slow?" · "Who verified it?" · "Did incidents drop because you fixed things or because you stopped counting?" (have the definition and the baseline ready).

🟡 Safer phrasing if the baseline is soft: *"The data-preparation step for month-end went from about five days to about two hours, confirmed with Finance."* Only say "confirmed with Finance" if true.

🔵 **Katalon link:** "Executives distrust the numbers" is the classic first-90-days problem; ARR/NRR must have one certified definition.

---

## S3 — Influenced executives with data / budget (JD: "influence executive stakeholders")

**Source:** Retailer **$2M** annual cloud/vendor budget; C-level stakeholders.

🟢 **Draft:**
> *Situation:* Cloud and vendor spend was a visible line for senior leadership and rising with data volume.
> *Task:* Own the $2M budget and show leadership what it bought.
> *Action:* (1) Made cost visible by team and workload [CONFIRM: tagging/chargeback approach]; (2) reported unit cost, not just total; (3) took trade-off decisions to the C-level in business terms: what we cut, what we defended, and why. [CONFIRM: one specific thing you *defended* against a cut, and one you got wrong.]
> *Result:* Platform cost down ~40% [see S8 for mechanism] while volume grew.
> *Reflection:* [CONFIRM].

🔴 Attacks: "What did you cut? What did you defend? What did you get wrong?" — prepare all three, with one genuine mistake.

---

## S4 — ML/AI value with measurable impact (JD: "advanced analytics, ML, GenAI where measurable")

**Source:** Retailer O2O / real-time fulfilment, delivery time **−40%**. GenAI/RAG listed on resume.

🟢 **Draft (O2O):**
> *Situation:* Online-to-offline orders from stores needed faster fulfilment; delivery time was a customer and cost issue.
> *Task:* Provide the real-time data foundation (and models, if any) behind routing/fulfilment. [CONFIRM: exactly your part — platform, features, or algorithm?]
> *Action:* (1) Real-time stock and order signals available in minutes, not next day; (2) [CONFIRM: routing/ETA model or rules?]; (3) measured against a baseline. [CONFIRM: A/B, pilot stores vs others, or before/after?]
> *Result:* Delivery time down 40%. 🔴 **Attribution is the weak point:** routing algorithm vs data platform vs operations changes. Say: *"The data platform enabled it; the improvement came from ops and routing together. My part was [X]."*
> *Reflection:* [CONFIRM: e.g. should have set up a holdout from day one].

🟢 **GenAI/RAG slot:** [CONFIRM: what you shipped — internal assistant? product-data search? text-to-SQL? — users, accuracy measure, cost]. If it is a pilot, say so; Katalon wants honesty on AI maturity, and your answer to "how do you evaluate it" (golden set, faithfulness, acceptance rate — guide Section 15) is what impresses.

🔵 **Katalon link:** same pattern for AI-assisted test authoring: real-time signals in, measurable outcome (time saved), A/B to prove it.

---

## S5 — Cross-functional transformation (JD: "Data + AI transformation across business functions")

**Source:** Retailer — stores, supply chain, finance, O2O, e-commerce all on one platform.

🟢 **Draft:**
> *Situation:* Business functions each had their own data and definitions. [CONFIRM: concrete example — e.g. stock availability counted differently by supply chain and stores.]
> *Task:* Create one platform and shared metrics without stopping operations.
> *Action:* (1) Mapped stakeholders and picked one pilot function with a willing champion [CONFIRM: which]; (2) delivered a visible win in weeks; (3) scaled to other functions with training and a published glossary; (4) embedded it in process (monthly metrics review) so it survived beyond me.
> *Result:* [CONFIRM: number of functions onboarded, dashboards retired, adoption].
> *Reflection:* [CONFIRM].

🟡 Retail-to-SaaS bridge sentence: *"Store, supply chain and finance were my Product, Sales and CS — different incentives, one set of numbers."*

---

## S6 — Built and grew a team (JD: "Build, mentor and lead a high-performing Data team")

**Source:** Team **8 → 25** at the retailer.

🟢 **Draft:**
> *Situation:* I took over/led a team of 8 with a growing platform scope. [CONFIRM: inherited vs hired split.]
> *Task:* Scale to what the platform and business needed without losing quality.
> *Action:* (1) Defined roles — platform engineering, analytics engineering, analysts, [CONFIRM: ML?]; (2) hired in sequence: foundations first, then specialists; [CONFIRM: your hiring bar and one hiring mistake]; (3) career ladders and mentoring by design review and code review; [CONFIRM: one person you grew into a bigger role]; (4) on-call and blameless post-mortems.
> *Result:* 8 to 25. [CONFIRM: attrition, promotions, how quality held — incidents −60% is your best evidence.]
> *Reflection:* [CONFIRM].

🔴 Attacks: "Who did you hire vs inherit?" · "Attrition?" · "Did quality hold?" · "Tell me about a bad hire." Have a real answer to each.

---

## S7 — Privacy, security, compliance (JD: "GDPR, CCPA/CPRA")

**Source:** GDPR / PDPA / MAS on resume; SCB AML for 15+ countries; Lazada multi-country (SEA); Thailand PDPA at the retailer.

🟢 **Draft:**
> *Situation:* [CONFIRM: pick one real event — e.g. PDPA readiness for Thailand at the retailer, or customer-data handling across Lazada's SEA countries, or AML data at SCB across 15+ countries.]
> *Task:* Make data handling provable: where PII lives, who can see it, how long we keep it, how we delete it.
> *Action:* (1) Classified PII and tagged columns; (2) access via roles and masking (Unity Catalog at the retailer); (3) retention and deletion runbook; (4) audit evidence from logs. [CONFIRM which of these you actually did.]
> *Result:* [CONFIRM: passed audit? number of datasets classified? DSAR turnaround?]
> *Reflection:* [CONFIRM].

🟡 Honest bridge: *"My regulatory experience is PDPA and MAS-style rules plus GDPR concepts; CCPA/CPRA is the same control set with different rights, and I'd have Legal confirm the interpretation."* Don't claim hands-on CCPA work unless true.

---

## S8 — Cut cost / said no (JD: "operational excellence", "evaluate technologies")

**Source:** AWS/Databricks cost **−40%** (retailer **and** Xendit); dbt/Spark runtime **−60%** (Xendit); FX pipeline manual effort **−80%** (Xendit).

🔴 **Warning:** the same "40%" at two employers reads suspicious. Use **different mechanisms** and say so explicitly.

🟢 **Draft:**
> *Situation:* Cloud spend was growing faster than the business.
> *Task:* Cut cost without hurting reliability or speed.
> *Action:* [CONFIRM which actually applied at the retailer: job clusters instead of all-purpose clusters · autoscaling and spot · right-sizing · removing unused tables/jobs found from usage logs · incremental models instead of full refresh · storage lifecycle · small-file compaction.] At Xendit the 40% came from a *different* lever: [CONFIRM].
> *Result:* About 40% lower at the retailer [CONFIRM: absolute dollars/month and period]. Unit cost per [query/job/pipeline] also fell.
> *Reflection:* [CONFIRM: one cut you regretted].

🟢 **Xendit mini-story (dbt/Spark −60%, FX −80%):** [CONFIRM: what was slow — e.g. HYPOTHESIS: full-table rebuilds, skewed joins, over-large cluster — what you changed, how you measured; for FX: manual hours per month before/after in absolute terms.]

---

## S9 — Xendit, six months (the question you will be asked)

🟢 **Draft (non-bitter, forward-looking):**
> *"Xendit was a Principal Data Engineer role of about six months. I contributed [FIRST — your concrete wins: dbt/Spark runtime −60%, FX pipeline manual effort −80%], and then [CONFIRM: honest reason — e.g. an opportunity to lead a platform at the retailer at much larger scale / relocation / role scope changed]. I'd rather be direct that it was short, and what I took from it: [CONFIRM: one lesson]."*

🟡 Rules: no criticism of Xendit · no vague "it wasn't a fit" · lead with what you delivered · say the reason in one sentence · pivot to what you are choosing now (Katalon).

---

## S10 — "Why Katalon?" (prepare this verbatim)

🟢 *"Three reasons. First, Katalon sells AI-augmented testing, so data quality is part of your product — I've spent my career making data trustworthy at scale. Second, the role covers strategy, platform, governance and AI-ready data in one seat, which is what I've been doing at the retailer with a team that grew from 8 to 25. Third, the SaaS motion — product telemetry, trial-to-paid, expansion — is a new domain where my event-platform experience from Lazada transfers directly, and I'm excited to learn the commercial side with your Finance and Sales leaders."*

[CONFIRM: add one sentence of genuine research — a Katalon product you tried, a feature, a G2 review insight. Concrete beats generic.]

---

## Claim-defence cheat sheet (say the baseline before they ask)

| Claim | Have ready |
|---|---|
| $8B business | You **supported the platform** behind it. Never say you "drove" $8B. |
| 8 → 25 | Inherited vs hired · attrition · promotions · quality evidence |
| $2M budget | One cut · one defended · one mistake |
| Incidents −60% | Baseline/month · definition · period · severity mix |
| 10B+ rows/day, 99.99%, 500+ jobs | What 99.99% measures · what broke first · how you monitor |
| Close 5 days → 2 hours | The bottleneck · what step ended · who confirmed |
| Delivery −40% | Your part vs ops/algorithm · baseline · how measured |
| Cost −40% (×2 employers) | Different mechanisms · absolute dollars · period |
| dbt/Spark −60% | What was slow · what you changed · how measured |
| FX −80% | Hours/month absolute |
| 100M+ events, 10x | Your scope vs team |
| 20M+ insights/day | Define "insight" or drop it |
| 600+ tables | Governance at that count: owners, tiers, tests, retirement |

---

## Fill-in order (30 minutes)

/2. Record yourself saying S1, S2, S6 in 90 seconds each.
3. Decide your single "mistake I made" story (S3 or S6) — interviewers always ask.
4. Rehearse S9 and S10 until they sound unforced.
