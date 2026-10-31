# Lesson 32: CTO interview

> **Week 7 · Day 32 · 90 min**
> **Deliverable:** The 5 most-asked CTO questions, each with a 90-second answer skeleton.

## 🎯 Architect Level
Staff.

## 🧠 Concept

The CTO interview is a peer interview. The CTO is asking: "can this person make technology decisions I can defend to my board?" The bar is technical depth, judgment, and humility (knowing when to defer).

The 5 most-asked CTO questions:

1. **"Walk me through your current architecture."** (5 layers; the choices; the trade-offs.)
2. **"Why this stack over the alternatives?"** (Named alternatives, named reasons.)
3. **"How do you handle the build-vs-buy decision?"** (Framework, not vendor pitch.)
4. **"What's the hardest technical problem you've solved?"** (A real story with depth.)
5. **"How do you keep up with the pace of change in AI?"** (A learning practice, not a hype list.)

The single biggest mistake is to **oversell**. The CTO has seen a thousand "we use the latest of everything" pitches. The CTO respects the CDO who has opinions, defends them, and knows the limits.

The second biggest mistake is to **not show the build-vs-buy framework**. "We use Snowflake" is not an answer. "We use Snowflake because [X], and we considered [Y, Z] and chose against them because [reasons]" is an answer.

The third biggest mistake is to **not be humble**. The CDO is the peer of the CTO, not the CTO's report. The CDO who defers to the CTO on every technical question loses the seat. The CDO who fights the CTO on every technical question also loses. The right posture: defend your domain, defer on the CTO's domain, find the joint decision.

## 🛠️ Build It

**Spec:** Build the 5 CTO answers, each in 90 seconds, each with a follow-up defense.

**Acceptance:**
- 5 questions, 5 answers
- Each answer: 90 seconds, named stack, named alternative, named reason
- Each answer: 1 follow-up defense (90 seconds)
- 1 paragraph on the trade-off (depth vs. humility)

**Starter:** Use Day 16-20 architectures. Synthesize.

**Solution (5 CTO answers, abridged):**

**Q1: Walk me through your current architecture.**
> "Five layers. Ingestion: Fivetran + Airbyte for SaaS, Kafka for events. Storage: lakehouse on Iceberg + S3, with Snowflake as the query engine. Transformation: dbt for 80%, Spark for 20%. Semantic: dbt semantic layer + Cube. Consumption: Looker for BI, APIs for data products, RAG + agents for AI. Cross-cutting: DataHub for lineage, Monte Carlo for observability, Dagster for orchestration, in-house FinOps."

**Q2: Why this stack over the alternatives?**
> "Lakehouse over pure warehouse: open table format, cost at our scale is 2-3× lower, no vendor lock. dbt over hand-rolled: SQL-native, version-controlled, testable. Feature store in-house over Tecton: cost at our scale is 3-5× lower, and the feature definitions are our IP. Multi-model LLM: vendor diversification, route by task."

**Q3: How do you handle build-vs-buy?**
> "Three questions. Does it differentiate us? Buy if no, build if yes. Can we hire for it? Buy if no, build if yes. Is it core to the platform? Build, always. Examples: feature store (build, IP); semantic layer (build, IP); observability (buy, commodity); transformation (build, IP); RAG orchestration (build, IP); vector store (buy, scale later)."

**Q4: What's the hardest technical problem you've solved?**
> "Real-time customer 360 at Lazada — 20M+ customer events per day, joined across web, app, and in-store, with sub-second freshness for personalization. The hard part was the join — 6 different identity resolution strategies depending on the event type. We built it on Flink + ClickHouse. [CONFIRM: get the real architecture and metrics.]"

**Q5: How do you keep up with the pace of change in AI?**
> "Three practices. One, a weekly 'AI radar' with the team — 30 minutes, 2-3 papers / blog posts, 1 model release. Two, a quarterly 'build vs. buy' review — re-assess every vendor and every build. Three, a personal weekly read — I spend 2-3 hours/week on arXiv, vendor blogs, and conference talks. The goal is not to be the expert; the goal is to know what questions to ask."

**Trade-off (depth vs. humility):** Defend your domain, defer on the CTO's, find the joint. If the CTO says "we use AWS," and you say "we use GCP," find the reason, defend it, then ask "what's the joint call?"

## 🏛️ Architect Notes

- **Trade-off:** Show your work vs. show the result. The CTO wants both. Default: 30 seconds on the result, 60 seconds on the work, 30 seconds on the alternatives.
- **Capacity / cost:** 5 answers × 90 seconds = 7.5 minutes. The depth comes in the follow-up.
- **When NOT to use:** Don't argue tech religion. "Postgres is better than MySQL" is a waste of the CTO's time. The CDO who fights tech religion is the CDO who doesn't ship.
- **Production checklist:**
  - [ ] 5 questions, 5 answers
  - [ ] 90 seconds per answer
  - [ ] Named stack
  - [ ] Named alternative
  - [ ] Named reason
  - [ ] 1 follow-up defense per answer

## 🌙 Reflect

- Which answer is your weakest? Re-record.
- Which architecture choice would the CTO in your actual interview challenge? Pre-write.
- Write 3 sentences you'll say out loud tomorrow.

---

**Next:** Day 33 — CFO Interview.