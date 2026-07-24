# Intrepid Asia — Head of Data & Analytics — CTO ROUND Prep (Prem Vishnoi)

> **The CTO round is different from the CEO round.** The CEO asks *"will this move the business?"* The CTO asks *"can you actually build it, and do I want you as a peer?"*
> Expect: architecture depth, stack-specific probing, build-vs-buy judgment, cost, governance, and how you'd work with his engineering org.

---

## 🎯 What the CTO Is Really Assessing
1. **Technical credibility** — can you hold your own in an architecture debate?
2. **Judgment over dogma** — do you have opinions, and can you defend *and* change them?
3. **Their stack, specifically** — BigQuery, StarRocks, Airflow, DBT, Cube.dev, Superset
4. **Pragmatism** — will you rebuild everything (bad) or evolve it (good)?
5. **Peer fit** — data and platform engineering must partner, not fight. Will you overreach into his territory?

**⚠️ Biggest trap:** coming in as "the new leader who'll replace the stack." Their tech team has existed since 2017 and the JD calls it a "well-oiled machine." **Respect what exists, evolve it.**

---

## 🧠 KNOW THEIR STACK COLD (study this section)

| Tool | What it is | Your honest position |
|------|-----------|---------------------|
| **BigQuery** | Serverless columnar warehouse. Cost = **bytes scanned**. | Same principles as your Databricks/Redshift work — partitioning, clustering, avoiding `SELECT *`. Learn fast. |
| **StarRocks** | Real-time OLAP/MPP engine. Sub-second queries, high concurrency. Used alongside BQ for speed. | Analogous to **ClickHouse**, which you ran at Lazada. Say this — it's a direct transfer. |
| **Airflow** | Orchestration/scheduling DAGs. | You've used Airflow — listed on your CV. Comfortable. |
| **DBT** | SQL transformation, version-controlled, testable. The "T" in ELT. | Conceptually your medallion layers (bronze/silver/gold) expressed in SQL + Git. Fast to pick up. |
| **Cube.dev** | **Semantic layer** — defines metrics once (what "GMV" means), serves all tools consistently. | 🔑 **You built a semantic layer for Text-to-SQL at Makro.** You understand *why* it matters — which is the hard part. |
| **Looker Studio / Superset** | BI/visualization. | Equivalent to your Power BI work. Non-issue. |

**Where they're heading (from the JD):** real-time/streaming, vector databases, MCP, LLM integration, feature stores, MLOps, agentic orchestration.

**Your strongest line on the stack gap:**
> "The tools differ, the principles don't. StarRocks is essentially the role ClickHouse played for me at Lazada. DBT is the medallion architecture I built, expressed as version-controlled SQL. And Cube is the semantic layer — I built one for the Text-to-SQL platform at Makro, so I know why it's the foundation for any AI-on-data ambition, not a nice-to-have."

---

# SECTION 1 — ARCHITECTURE QUESTIONS

## Q1: "How would you evolve our current stack into an AI-native platform?"
**⚠️ Do NOT propose a rebuild. Propose layers on top.**

> "I'd start from the principle that the current stack is working — BigQuery, DBT, Airflow and Cube is a solid modern foundation. I wouldn't touch it. What's missing isn't the warehouse, it's four layers above and around it.
>
> **First, harden the semantic layer.** Cube is already there, but for AI the question is whether every metric is defined once and correctly. Any LLM interface is only as good as its semantic grounding — if 'GMV' means three things, your copilot will confidently give three answers. This is the highest-leverage unglamorous work.
>
> **Second, real-time paths where they earn it.** Social commerce and livestreaming are genuinely time-sensitive — campaign performance, stock-outs, creator activity. I'd add streaming ingestion into StarRocks for the use cases that need seconds, not the ones that don't. I wouldn't make everything real-time; that's expensive and usually unnecessary.
>
> **Third, the ML/AI layer** — feature store, model registry, monitoring, retraining. Right now I'd guess models, where they exist, are somewhat bespoke. Industrialising that is what makes ML repeatable rather than heroic.
>
> **Fourth, the LLM/agent layer** — vector store, retrieval, guardrails, and orchestration. This is where NL2SQL, copilots and agents live.
>
> Sequenced that way, each layer is independently valuable — you don't need all four before anything works."

## Q2: "Walk me through an architecture you've designed end to end."
> "The clearest one is the Makro lakehouse. Sources across finance, supply chain, retail and ecommerce feeding into a Databricks Lakehouse — medallion structure, so bronze holds raw immutable data, silver is cleaned and conformed with business keys resolved, gold is curated marts serving specific consumption patterns. Delta Lake underneath for ACID guarantees on the lake, which is what makes the lakehouse pattern actually viable versus files in a bucket.
>
> On top: BI for executives, feature-ready datasets for ML, and eventually the GenAI layer.
>
> The decisions I'd defend: lakehouse over separate lake-plus-warehouse, because copying data between them creates cost and inconsistency; medallion because it gives you clear reprocessing boundaries when something upstream breaks; and governance at the silver layer, so consumers can't accidentally bypass it.
>
> Scale was 10 billion-plus rows daily across 600-plus tables at Lazada equivalent, and the platform supported multi-country expansion through reusable patterns."

## Q3: "How would you handle real-time for social commerce?"
> "This is close to what I built at Lazada. There, orders, traffic and driver telemetry flowed into Kafka at 100 million-plus events daily, Flink did stream processing, ClickHouse served fast analytical queries and HBase handled low-latency lookups. That produced 20 million-plus daily insights for last-mile logistics.
>
> The pattern I'd bring here: split the stream. One path optimised for speed — aggregate in-flight, land in StarRocks, drive alerts and live dashboards. A second path writes raw to the warehouse for history and reprocessing. You need both, because the fast path is lossy and you'll always want to recompute later.
>
> For Intrepid specifically, the real-time candidates are livestream performance, campaign anomalies, and inventory across marketplaces. I'd be deliberate about which use cases justify streaming cost — I've seen teams stream everything and triple their bill for dashboards nobody watches in real time."

## Q4: "How do you approach data quality and governance?"
> "Three layers, and I'd say the third is the one most teams skip.
>
> **Testing in the pipeline** — DBT tests are good for this: uniqueness, not-null, referential, and business-rule assertions. Fail loudly and early rather than propagating bad data into a dashboard.
>
> **Observability** — freshness, volume anomalies, schema drift. You want to know a source broke before the business tells you.
>
> **Contracts and ownership** — every critical dataset has a named owner and a defined schema contract with upstream producers. This is the part that's organisational rather than technical, and it's why data quality is really a leadership problem.
>
> On governance specifically — I've worked under GDPR, PDPA and MAS regulatory requirements, and built AML compliance platforms across 15-plus countries at Standard Chartered. So lineage, access control and PII handling aren't abstract to me. With multiple client brands here, tenant isolation and making sure one brand's data can't leak into another's reporting would be a first-order design concern, not an afterthought."

## Q5: "How do you manage cost on a platform like this?"
> "BigQuery cost is driven by bytes scanned, so the levers are well understood: partitioning and clustering on the columns people actually filter by, materialised aggregates for repeated heavy queries, killing `SELECT *` habits, and storage lifecycle policies for cold data.
>
> But the biggest wins I've seen aren't technical — they're behavioural. At Makro, cost optimisation was an explicit part of my remit under a $3M budget. The pattern is usually a handful of poorly-written recurring queries and dashboards refreshing far more often than anyone needs. Making cost visible per team changes behaviour faster than any optimisation I can do centrally.
>
> For real-time, I'd be especially disciplined — streaming is where costs run away quietly."

---

# SECTION 2 — AI / ML DEPTH

## Q6: "How would you build NL2SQL / conversational BI here?" 🔑 **your best answer**
> "I've built exactly this, so let me be concrete about what's hard.
>
> At Makro I delivered a Text-to-SQL platform for business users. Everyone assumes the LLM is the challenge. It isn't — the model generates syntactically valid SQL easily. The problems are:
>
> **Semantic grounding.** The model needs to know what your business means by a metric. This is precisely why Cube matters — if the semantic layer defines GMV once, the LLM queries *that*, not raw tables it might join wrongly. I'd say the semantic layer *is* the NL2SQL project.
>
> **Guardrails.** Read-only enforcement, row limits, cost caps, timeout. An LLM will happily write a query that scans your entire warehouse.
>
> **Validation and retry.** Check the generated SQL before executing; if it fails or returns something implausible, feed the error back and re-prompt rather than showing the user an exception.
>
> **Trust calibration.** The dangerous failure isn't a wrong query that errors — it's a plausible query that returns a subtly wrong number. I'd show users the generated SQL and the assumptions, so they can sanity-check. Confidence without transparency destroys adoption after the first wrong answer reaches a client.
>
> That's the design I'd bring, adapted to Cube and BigQuery."

## Q7: "What's your view on agentic AI here — realistically?"
> "Start narrow, earn autonomy, and design the guardrails before the agent.
>
> A sensible first agent for Intrepid: monitors campaign and marketplace performance, detects an anomaly, investigates likely cause across related data, and produces a recommendation for a human to approve. That's genuinely useful and low-risk — the human is the safety layer.
>
> The engineering underneath matters more than the prompt: tool definitions with tight scopes, a retrieval layer so the agent has context about the brand and campaign, observability so you can audit what it did and why, and evaluation so you can measure whether its recommendations were right.
>
> Only once you can show it's right often enough would I widen to bounded autonomous action — say, bid adjustments within a range, with limits and rollback.
>
> On MCP — it's a sensible standard for exposing tools and data to agents consistently rather than bespoke integrations per model. I'd want that as the interface layer rather than hardcoding."

## Q8: "What ML would you prioritise for this business?"
> "I'd anchor on where a model changes a decision that has money attached.
>
> **Anomaly detection** first — highest value per effort. Campaign performance, listing health, inventory. It's the difference between finding a problem in hours versus at month-end.
>
> **Forecasting** — demand and inventory. I built ML demand forecasting across 1,000-plus vendors at Makro, and inventory forecasting is one of the clearest ROI cases in commerce.
>
> **ROAS optimization / bid and budget allocation** — direct marketing efficiency, and it's measurable, which matters for proving the team's value.
>
> **Recommendation and pricing** — I owned a dynamic pricing model end to end at Makro, gradient boosting on transactional and competitor data.
>
> **Content and catalogue intelligence** — I built embedding-based item matching to deduplicate SKUs across online and offline. That maps directly to a multi-marketplace catalogue problem.
>
> I'd sequence by time-to-proof, not by technical interest."

## Q9: "How do you productionise ML — MLOps?"
> "The thing I care most about is that a model in production is a *system*, not an artifact.
>
> That means: versioned features in a feature store so training and serving don't drift apart, model registry with lineage back to the training data, monitoring for both performance and input drift, and an automated retraining path with a human gate.
>
> At Lazada I led exactly this — industrialising models from prototype to production with monitoring, retraining and governance, in partnership with the data science team. Before that, models were built and then quietly decayed because nobody owned them after launch.
>
> The organisational half matters as much: someone must own the model *after* it ships. Otherwise you get a graveyard of models everyone stopped trusting."

---

# SECTION 3 — WORKING WITH THE CTO / ENGINEERING

## Q10: "How do you see data and engineering working together?"
**⚠️ Critical — don't overreach into his org.**
> "Clear boundaries, shared goals. My view: platform and product engineering own the systems that generate data and the applications that consume it. My team owns the data platform, the modelling and semantic layer, and the intelligence on top.
>
> Where it works well is data contracts — engineering commits to schema stability and notifies on change; we commit to not reaching into their databases unannounced. Where it fails is when data teams silently depend on internal tables and break every time engineering ships.
>
> I'd also want my team embedded enough to understand the products. At Lazada I partnered closely with product and data science teams; at Makro I work across four business domains. I don't want a central team that throws dashboards over a wall."

## Q11: "How technical do you stay? Will you code?"
**Be honest — they said "hands-on" in the JD.**
> "I'm hands-on by preference. I review architecture and critical PRs, I'll sit with an engineer on a hard modelling or performance problem, and I've personally built things recently — the Text-to-SQL platform and the item-matching pipeline were mine end to end.
>
> What I won't do is be in the critical path of daily delivery — that makes me a bottleneck and stunts the team. My rule is: technical enough to make good decisions and earn the team's respect, not so involved that nothing ships without me."

## Q12: "What would you change in your first 90 days?"
> "Honestly, less than people expect. First 30 days I'd mostly be listening and auditing — where does data break, which numbers do people argue about, what does the platform cost and why, what does the business actually decide weekly.
>
> The things I'd expect to move early: metric definitions and semantic layer consistency, because everything AI depends on it; data quality testing and observability if it's thin; and one visible win with real business value to build credibility.
>
> What I'd deliberately *not* do is propose a re-platform. Your stack is reasonable. Replacing working infrastructure is how data leaders burn their first year and all their political capital."

---

# SECTION 4 — LIKELY CHALLENGES

## Q13: "You haven't used BigQuery, StarRocks, DBT or Cube. Concern?"
> "Fair challenge. Let me be precise about what transfers and what doesn't.
>
> StarRocks — I ran ClickHouse at Lazada for exactly the same role, real-time OLAP at scale. Direct transfer.
> DBT — it's the transformation layer of the medallion architecture I've built repeatedly, expressed as version-controlled, testable SQL. The concepts are mine; the syntax is a few weeks.
> Cube — I built a semantic layer for the Text-to-SQL platform. Knowing *why* the semantic layer is the foundation for AI is the hard-won part.
> BigQuery — a columnar warehouse where cost tracks scanned bytes. Same optimisation instincts as everything I've tuned.
> Airflow — I've used it.
>
> So realistically I'd be productive in weeks and fully fluent in a couple of months. And I'd rather be honest about that than claim instant expertise. Where I'd add value from day one is the AI and ML layer, the architecture direction, and the team — which is what you're actually hiring for."

## Q14: "Would you replace any of our stack?"
**⚠️ Trap question. Show restraint.**
> "Not on day one, and probably not at all without a strong reason.
>
> My default is to evolve rather than replace. Replacing infrastructure is expensive, risky, and rarely the actual bottleneck — usually the bottleneck is modelling, governance, or adoption, and a new tool doesn't fix any of those.
>
> I'd only propose a change where there's a clear ceiling — a genuine scale limit, a cost problem I can't optimise away, or a capability gap blocking something the business needs. And I'd want to prove it with data, not preference.
>
> What I *would* add is the layers that aren't there yet — streaming where it's justified, feature store, vector store and the LLM orchestration layer. Additive, not disruptive."

## Q15: "What's the hardest technical problem you've solved?"
> "The Lazada real-time platform, for scale reasons — 100 million-plus events daily, multi-market, with delivery SLAs depending on it. Choosing Flink over micro-batch mattered because event-time semantics were genuinely necessary, not a preference.
>
> But the *hardest* was probably entity resolution at Standard Chartered — fuzzy matching high-risk entities across multilingual customer records for AML screening across 15-plus countries, under MAS regulatory scrutiny. Hard because there's no clean ground truth, the cost of a false negative is regulatory and the cost of a false positive is investigator time, and the data was genuinely messy across languages and scripts. I built the matching and similarity algorithms and materially cut false positives and investigation time.
>
> That problem taught me more about precision-recall tradeoffs having real business consequences than any clean ML project has."

---

# SECTION 5 — QUESTIONS FOR THE CTO

1. **"Where does the current platform hurt most — cost, reliability, modelling, or speed of delivery?"** *(Best opener. Reveals the real job.)*
2. **"How do you see the boundary between your platform teams and the data org?"** *(Signals you respect his territory.)*
3. **"What's the appetite for real-time? Which use cases genuinely need seconds versus minutes?"**
4. **"Where are you on build-vs-buy for the AI layer — vector store, orchestration, evaluation?"**
5. **"You've had the tech team since 2017 — what's the engineering culture, and what would you not want changed?"**
6. **"What does the data team look like today, and what's the biggest capability gap?"**

---

# ✅ CTO ROUND CHECKLIST

**Be able to draw on a whiteboard:**
- [ ] Medallion lakehouse (bronze/silver/gold) — your Makro architecture
- [ ] Real-time split-stream pattern (fast path + history path) — your Lazada architecture
- [ ] NL2SQL flow: question → semantic layer → LLM → guardrails → validate → execute
- [ ] The four layers you'd add to their stack (semantic, real-time, ML, LLM/agent)

**Have crisp opinions on:**
- [ ] Lakehouse vs warehouse+lake · Streaming vs batch (when each earns its cost)
- [ ] Why the semantic layer is the foundation of AI-on-data
- [ ] Build vs buy for the AI layer
- [ ] Why you'd *not* replace their stack

**Posture:**
> This is a **peer conversation**, not an exam. Bring opinions, defend them with reasoning, and change your mind when he makes a better point — CTOs value that far more than someone who's never wrong. Show restraint about their existing stack; show conviction about the AI layer, because that's what they're hiring you for.
