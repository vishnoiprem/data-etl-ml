# Tech Evaluation Question Prep — "Evaluate and implement modern data and AI technologies to continuously improve platform capabilities"

> **Purpose:** Full preparation file for the technology-evaluation line on the role's responsibility list. Sixth in the series: `strategy-question-prep.md` · `platform-architecture-question-prep.md` · `governance-question-prep.md` · `partnerships-question-prep.md` · `ai-adoption-question-prep.md` · this file.

---

## The Question

- **Round:** Onsite 1 (technical panel — Vu Bui, Que Tran, Son Dao), Onsite 2 (Duke Nguyen, VP Engineering), or Onsite 3 (Rajesh Krishnan, SVP Engineering)
- **Source:** Job posting, line 6 of "Your Responsibilities" (`README.md`)
- **Verbatim:** *"Evaluate and implement modern data and AI technologies to continuously improve platform capabilities."*
- **Likely probes:**
  - "How do you decide build vs buy?"
  - "Snowflake vs Databricks vs BigQuery vs Redshift?"
  - "Open table formats — Iceberg vs Delta vs Hudi?"
  - "When does a vector DB earn its place?"
  - "What about open-source vs managed?"
  - "How do you avoid lock-in?"
  - "How do you evaluate a new AI model?"
  - "You replaced Airflow with what?"
  - "How do you sunset a tool?"
  - "What's the technology radar look like at Katalon?"

---

## Framework Used

- **Strategic:** **Buy-Commodity / Build-Differentiator** + **Decision Record** discipline
- **Tactical:** **T-Shirt Size → POC → Decision Record → Rollout → Sun-Setting**
- **Anchor sentence:** *"The best tool is the one that disappears — the team doesn't talk about it, they just ship."*

🔵 **Hook: "Buy commodity. Build differentiator. Always have an exit."**

---

## 60–90 Second Spoken Answer (lead with this)

> My rule: **buy commodity, build differentiator**. Ingestion, orchestration, observability — buy. The semantic layer for testing-domain metrics, the AI evaluation harness, the tenant-scoped retrieval — those are the edge, so we build.
>
> Every decision is a **decision record** — one page, named owner, the alternatives, the cost in dollars and people, the lock-in risk, and the exit plan. Without an exit, the answer is no.
>
> For the AI side, I treat new models like new hires — they don't ship until they pass an **evaluation harness** on our golden set, with a canary, with a kill switch. Five-percent offline lift that doubles p95 latency and cost doesn't ship to interactive surfaces.
>
> I run a **quarterly technology radar** — Adopt / Trial / Assess / Hold — published to engineering leadership, so we're aligned on what's in, what's out, and what's being deprecated. Sun-setting tools is a feature, not a failure — it frees people to work on what matters.
>
> For Katalon specifically: I'd lean AWS-native (their public docs say AWS), open table formats (Iceberg) for portability, and a thin layer of best-of-breed — not a single vendor stack.

⏱️ ~95 seconds. Trim if rushed.

---

## The Buy/Build Decision Rubric

For every technology decision, score on five axes:

| Axis | Question |
|---|---|
| **Differentiation** | Is this a product edge, or is it commodity? |
| **3-year TCO** | Tool license + cloud + people + integration cost |
| **Time to value** | How long until the first user gets value? |
| **Lock-in / exit cost** | Can we leave in 90 days if needed? |
| **Security / fit** | Does it pass our enterprise-buyer bar? |

**Default:** Buy. **Override:** If the tool is a product edge, or no vendor can meet the SLO/security model, build.

🔵 **Hook: "If three vendors can do it, buy. If one can, build carefully. If none can, you have to build."**

---

## Decision Record Template (one page)

```yaml
decision: Adopt Apache Iceberg as the open table format
owner: data-platform-lead
status: proposed
date: 2026-10-04
context: |
  Lakehouse decision. Need ACID, schema evolution, multi-engine
  (Spark, Flink, Trino) reads. Cost pressure on Snowflake/Databricks.
options_considered:
  - Iceberg (open, multi-engine, strong community)
  - Delta Lake (Databricks-aligned, strong ecosystem)
  - Hudi (Uber-origin, strong streaming upserts)
  - Single-vendor lakehouse (Databricks or Snowflake)
choice: Iceberg
rationale: |
  - Open format → exit cost is engine swap, not data migration
  - Multi-engine reads align with Flink + Spark + Trino stack
  - Strong partition evolution + hidden partitioning
tradeoffs:
  - Delta has stronger ML/Unity integration
  - Hudi has stronger streaming record-level upserts
cost: ~$200k/yr savings vs. single-vendor lakehouse
exit_plan: |
  Migrate to Delta or Hudi by rewriting table metadata
  (~2 weeks per 100 TB at our scale)
risks: |
  - Engine compatibility for advanced features
  - Smaller talent pool than Delta
mitigation: |
  - Pin to 1 specific Iceberg version per quarter
  - Hire/lobby for at least one Iceberg committer
```

🔵 **Hook: "If you can't write the exit plan, the answer is no."**

---

## Quarterly Technology Radar

| Ring | Meaning | Action |
|---|---|---|
| **Adopt** | Production-ready, recommended default | Use by default, document in paved road |
| **Trial** | Promising, real project needed | 1–2 bounded pilots, success criteria upfront |
| **Assess** | Worth understanding | Spike / lunch-and-learn, no production |
| **Hold** | Don't use, or sunset | Migration plan if already in use |

Published quarterly, with **diff against last quarter** so leaders see what's moving.

🔵 **Hook: "The radar is the team's compass, not a list of shiny things."**

---

## Common Tech Choices & How to Talk About Them

### Lakehouse / Warehouse

| Option | Strength | Weakness | When I pick it |
|---|---|---|---|
| **Snowflake** | Separation of storage/compute, easy ops | Cost at scale, Iceberg support maturing | Mixed BI + light ML, ops-light org |
| **Databricks** | Unified platform, ML-first, Delta Lake | Vendor gravity, higher skill bar | Heavy ML/AI, large Spark workloads |
| **BigQuery** | Serverless, ML in SQL | Streaming weak, partition model limited | GCP-native shops, simple BI |
| **Redshift** | AWS-native, mature | Concurrency, ecosystem catching up | AWS-only shops with steady DW needs |
| **Open Iceberg + Trino** | Open, portable, cost-efficient | You operate more of the stack | When lock-in is a board-level concern |

🔵 **Hook: "Katalon is on AWS. Lean native. Open table format. Best-of-breed on top."**

### Open Table Formats

| Format | Sweet spot | Why pick |
|---|---|---|
| **Iceberg** | Multi-engine, hidden partitioning, schema evolution | Default for portable lakehouse |
| **Delta** | Databricks-aligned, ML/Unity integration, CDF | Already on Databricks, or want UniForm |
| **Hudi** | Streaming record-level upserts, indexing | Heavy CDC / record-level merge needs |

### Orchestration

| Tool | Strength | When I pick it |
|---|---|---|
| **Airflow / MWAA** | Mature, Pythonic, large community | Default for batch + most teams |
| **Dagster** | Software-defined assets, typed IO | Asset-centric teams, modern ergonomics |
| **Prefect** | Dynamic workflows, good DX | Cloud-y, dynamic pipelines |
| **Dagster / Prefect / Temporal** | Native durable execution, retries | Long-running, stateful, microservice-style |
| **dbt** | Transformations, lineage, tests | The transform layer, not orchestration |

🔵 **Hook: "dbt is for transforms. Airflow/Dagster is for orchestration. Don't conflate."**

### Streaming

| Tool | Strength | When I pick it |
|---|---|---|
| **Kafka / MSK** | Durable, replayable, partitioned | Default for event backbone |
| **Pulsar** | Tiered storage, multi-tenant | Geo-replication, very large retention |
| **Kinesis** | AWS-native, simple | Low-volume AWS-only, simple ops |
| **Flink** | Stateful stream processing | Event-time joins, exactly-once, complex CEP |
| **Spark Structured Streaming** | Micro-batch, unified with batch | Existing Spark shop, simpler semantics |

### AI / Vector

| Tool | Strength | When I pick it |
|---|---|---|
| **pgvector** | One less system, transactional | <10M vectors, simple needs |
| **OpenSearch / Elasticsearch** | Hybrid search, mature | Already deployed, BM25 + vector |
| **Pinecone** | Managed, serverless | Fast start, willing to pay |
| **Weaviate** | Open source, hybrid | Self-host preference, rich filters |
| **Qdrant** | Open source, fast | Performance-sensitive, self-host |
| **Bedrock / Vertex** | Managed model API | Don't want to operate model serving |

🔵 **Hook: "Don't add a vector DB until you've outgrown pgvector or your existing search system."**

---

## Tech-Evaluation Lifecycle (memorize this)

```
1. BUSINESS TRIGGER
   Pain or opportunity, not "vendor pitched us"
        │
        ▼
2. T-SHIRT SIZE
   S = single dev, week  | M = small team, month  | L = org, quarter
        │
        ▼
3. POC (success criteria pre-agreed)
   Functional check + scale test + cost benchmark + security review
        │
        ▼
4. DECISION RECORD
   One page, owner, alternatives, TCO, exit plan
        │
        ▼
5. PILOT (1–2 production use cases)
   Real traffic, real users, measured outcome
        │
        ▼
6. ROLLOUT (paved road)
   Docs, golden path, training, deprecation of legacy
        │
        ▼
7. RENEW OR SUNSET
   Quarterly review: still earning its keep? Sun-setting is OK
```

🔵 **Hook: "No POC without success criteria. No adoption without an exit plan. No retention without a renewal."**

---

## Evaluating AI Models (the special case)

Same rigor as a vendor, with extra layers:

| Layer | Test |
|---|---|
| **Capability** | Golden-set task score, calibrated against human eval |
| **Safety** | Red-team: prompt injection, PII, off-policy |
| **Latency** | p50 / p95 at our request shape |
| **Cost** | $/1k tokens in + out, per-request total |
| **Compliance** | Data residency, training opt-out, audit access |
| **Lock-in** | Switch cost to a peer model |
| **Ops** | Rate limits, observability, fallback behavior |

**Decision rule:** *5% offline lift that doubles latency and cost → don't ship to interactive. Ship to batch if high-value.*

🔵 **Hook: "A new model is a new hire. They don't ship without an interview, an eval, and a probation period."**

---

## Common Probes — Pre-Rehearsed Answers

### Q1: "How do you decide build vs buy?"

🟢 *"Buy commodity, build differentiator. The rubric: differentiation, 3-year TCO, time to value, lock-in/exit, security fit. If three vendors can do it, buy. If one can, build carefully. If none can, you have to build. Always have a written exit plan — if you can't write one, the answer is no."*

### Q2: "Snowflake vs Databricks vs BigQuery vs Redshift?"

🟢 *"Pick by workload shape and org DNA. Snowflake: ops-light, mixed BI + light ML. Databricks: ML/AI-heavy, large Spark, want one platform. BigQuery: GCP-native, simple BI. Redshift: AWS-native steady DW. For Katalon on AWS, I'd lean native + open table format + best-of-breed on top — not a single vendor stack."*

### Q3: "Iceberg vs Delta vs Hudi?"

🟢 *"Iceberg = portable, multi-engine, strong partitioning. Delta = Databricks-aligned, ML/Unity integration, UniForm for cross-format. Hudi = strong streaming record-level upserts. Default to Iceberg for portable lakehouse; Delta if you're on Databricks and want Unity; Hudi for heavy CDC."*

### Q4: "When does a vector DB earn its place?"

🟢 *"When you've outgrown pgvector or your existing search system — usually >10M vectors, sub-100ms latency at scale, complex filters, or hybrid search beyond what your search cluster does well. Don't add a system to add a system. Pick a managed one if you don't want to operate it; pick an OSS one if you do."*

### Q5: "What about open-source vs managed?"

🟢 *"Managed unless the cost flips, the control matters, or the managed product can't meet an SLO. Open-source means you own the on-call, the upgrades, the security patches, the version skew. Open formats are a different question — open *table format* (Iceberg) is almost always worth it for the exit."*

### Q6: "How do you avoid lock-in?"

🟢 *"Three habits. (1) Open formats and open interfaces — Iceberg not Delta-only, SQL not only vendor APIs. (2) Thin proprietary layer with adapters below it. (3) The decision record requires an exit plan. Run a 'what would it cost to leave' exercise once a year on top three vendors."*

### Q7: "How do you evaluate a new AI model?"

🟢 *"Treat it like a new hire. Golden-set task score, calibrated against human eval. Red-team for safety and prompt injection. Measure p50/p95 latency at our request shape, $/1k tokens, rate limits, observability, fallback. Compliance: data residency, training opt-out, audit access. Decision: ship if 5% offline lift is worth the cost/latency at the use case."*

### Q8: "You replaced Airflow with what? Why?"

🟢 *"Probably not. Airflow is mature, well-known, MWAA removes the ops burden. I'd only move if we had a specific reason — asset-centric model needed (Dagster), durable execution needed (Temporal), or ops cost was clearly the bottleneck. Migration cost is real: DAGs, plugins, on-call knowledge. Don't migrate for novelty."*

### Q9: "How do you sunset a tool?"

🟢 *"Same rigor as adoption. (1) Decide to sunset with a date. (2) Find consumers via catalog/usage data. (3) Communicate twice — 90 days and 30 days. (4) Provide migration path or replacement. (5) On the date, freeze writes, redirect reads. (6) Archive for compliance. Sun-setting is a feature — it returns focus to the team."*

### Q10: "What's your technology radar look like at Katalon?"

🟢 *"Hypotheses to validate with the team. Adopt: Kafka/MSK, Iceberg, dbt, Flink or Spark, Snowflake/Databricks, pgvector or managed vector. Trial: hybrid search engines, eval harnesses (RAGAS, Promptfoo), feature stores. Assess: durable execution (Temporal), agent frameworks, smaller open-source LLMs. Hold: bespoke orchestrators, custom vector DBs, fine-tuning-first approaches."*

### Q11: "A vendor offers 50% off for 3-year commit. Take it?"

🟢 *"Almost never without an exit clause. Discount now vs lock-in cost later. Decision rule: if the 3-year cost of switching is greater than the discount, no. If we have a credible exit (data in open format, adapters in place), and the workload is stable, maybe. Always ask: what happens at year 3 if the price doubles?"*

### Q12: "How do you keep up with the pace of new tools?"

🟢 *"I don't try to keep up with all of them. I keep up with the *categories* — what's the state of vector DBs, lakehouse formats, orchestration models, eval tooling. Quarterly radar forces me to make explicit Adopt/Trial/Assess/Hold calls. The team contributes — every engineer can propose a Trial."*

### Q13: "A high-performer wants to introduce a new tool the team hasn't approved. What do you do?"

🟢 *"Listen first. They usually see something the team doesn't. Ask for a one-pager: problem, alternatives, TCO, exit plan, scope. If it's a Trial with a real project and a sunset date, approve. If it's 'I just want to use this,' push back to the radar. Most important: don't make the team feel like every new idea is a fight."*

### Q14: "How do you balance innovation with platform stability?"

🟢 *"Paved road for the 80%, escape hatches for the 20%. The paved road has SLOs, docs, golden path — that gets 80% of teams unblocked in days, not months. The 20% with genuinely different needs get a fast-tracked exception process, not a denial. Innovation happens in the escape hatches; the paved road stays stable."*

---

## Anti-Patterns (red-flag answers)

- ❌ "We use the best tool for the job" — that means you have no paved road
- ❌ "We never use open source" or "we only use open source" — both are dogma
- ❌ "We'll build a custom vector DB" — almost never the right answer
- ❌ "Just take the multi-year discount" — without an exit, you'll regret it
- ❌ "We replaced Airflow with [X]" without a specific reason
- ❌ "The vendor said it's fast" — benchmark on your workload, your data
- ❌ "We'll evaluate later, ship now" — POC without success criteria is a budget leak
- ❌ Inventing Katalon's stack, vendors, or your past tooling choices

---

## Three Things Katalon Is Hiring For (tied to this line)

Per Section 1 of `Katalon_Head_of_Data_Interview_Prep.md`:

1. **Builder-leader** — hands-on credible. *Demonstrated by:* this line — you can name the picks and the rationale.
2. **AI-readiness owner** — RAG, eval, governance. *Demonstrated by:* the AI model evaluation answer.
3. **Cross-functional translator** — speak CFO / lawyer / engineer. *Demonstrated by:* the TCO and lock-in framing.

🔵 **This line of the role IS the credibility test. Be specific. Cite tools you've actually used.**

---

## Practice Log

| Date | Time | Mode | Self-score (1–4) | Notes |
|---|---|---|---|---|
| | | (cold / timed / peer) | | |
| | | | | |

---

## Linked Material

- **Main prep doc:** `Katalon_Head_of_Data_Interview_Prep.md` Section 5 (architecture), Section 6 (build vs buy), Section 7 (tooling), Section 16 (anti-patterns)
- **Sister files:**
  - `strategy-question-prep.md`
  - `platform-architecture-question-prep.md`
  - `governance-question-prep.md`
  - `partnerships-question-prep.md`
  - `ai-adoption-question-prep.md`
  - `team-leadership-question-prep.md` (line 8)
  - `example-question-prep.md` (template)
- **Stories bank:** Section 21 — find stories tagged "build vs buy", "vendor migration", "AI model swap"
- **Flashcards:** Section 23
- **Scoring rubric:** Section 20

---

## Checklist Before Walking In

- [ ] 90-second answer said aloud, no notes
- [ ] Buy/build rubric stated
- [ ] Decision record template explained (one page, owner, exit plan)
- [ ] Radar (Adopt / Trial / Assess / Hold) named
- [ ] Snowflake vs Databricks vs BigQuery vs Redshift contrast ready
- [ ] Iceberg vs Delta vs Hudi contrast ready
- [ ] "When does a vector DB earn its place?" answer ready
- [ ] AI model evaluation answer (interview → eval → probation)
- [ ] Sun-setting answer (process, not just "deprecate")
- [ ] One real tech-decision story from your own career
- [ ] No invented Katalon vendors or numbers

---

## Closing Sentence (if asked "anything else?")

> The job of tech evaluation is to **return focus to the team**. The right tool disappears; the wrong tool absorbs an org. **Buy commodity, build differentiator, always have an exit, sunset without guilt.** That's how a platform compounds value instead of debt.
