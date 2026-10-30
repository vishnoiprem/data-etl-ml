# Example Question Prep — Template

> **Purpose:** This file shows the structure for prepping a single interview question end-to-end. Copy this template for each question you want to rehearse. One file per question keeps prep atomic and reviewable.

---

## The Question

> *Copy the question verbatim here. Include the round, the interviewer (if known), and the source.*

- **Round:** Onsite 1 — Technical Panel (Vu Bui, Que Tran, Son Dao)
- **Source:** Flagship system-design from `Katalon_Head_of_Data_Interview_Prep.md` Section 5
- **Verbatim:** *"Design Katalon's global data and AI platform for test execution analytics, live monitoring, company-wide BI, flakiness detection, and AI-assisted failure analysis."*

---

## Framework Used

> *Pick ONE framework per question. Don't blend.*

- **Technical:** **C-C-T-M** = Context → Choice → Trade-off → Metric
- **Behavioral:** **STAR-R** = Situation → Task → Action → Result → Reflection
- **Strategy:** **W-N-N** = What is true today → Near-term wins → North-star

*For this question:* **C-C-T-M**.

---

## 60–90 Second Spoken Answer

> *Write it exactly as you'd say it. Short sentences. Spoken rhythm. ~180–220 words.*

> I want to start with three planes — business data, product data, AI data — all built on one governed foundation. Business data is company BI: ARR, NRR, funnel, exec dashboards. Product data is the high-volume stream of test executions, results, logs, screenshots, defects. AI data is the governed context plane for failure analysis, flakiness detection, and recommendations.
>
> Architecturally, I'd separate a low-latency streaming path — Kafka or MSK into Flink for live state — from a durable lakehouse path on S3 with Iceberg, processed by Spark and dbt. The curated warehouse and semantic layer publish certified metrics. Artifact storage stays separate because screenshots and traces have different retention and cost.
>
> I'd lead with governance as a platform feature: tenant-scoped keys, classification at ingestion, row-level security, lineage, deletion workflows — all built in, not bolted on. AI only consumes governed products, never raw production stores.
>
> For AI: I'd start with the job-to-be-done and an evaluation harness before any model. Hybrid retrieval, tenant-filtered, schema-constrained outputs, citations, abstention rules. Then ship a lighthouse use case with measurable task outcomes, not vanity usage.
>
> First 90 days: baseline data trust, ship two certified exec metrics, one governed ingestion path with SLOs, and one offline-evaluated AI lighthouse. Hire for platform first, embedded analytics second.

🟡 *Word count: ~200. ~75 spoken seconds at calm pace. Good.*

---

## The Anchor Diagram

> *Always have one diagram you can draw from memory. Practice drawing it before the interview.*

```
                        ┌──── CONTROL PLANE ────┐
                        │ tenant / policies /   │
                        │ schemas / identity    │
                        └──────────┬────────────┘
                                   │
Producers ─► Kafka/MSK ─► Flink stream ─► Live state (Redis/DDB)
                       │                 └► Real-time OLAP (optional)
                       │
                       └─► S3 + Iceberg (bronze/silver/gold)
                              │
                              ├─► Spark + dbt (curated)
                              ├─► Warehouse + semantic layer (BI)
                              ├─► ML features + retrieval (governed AI)
                              └─► Artifact store (screenshots, traces)
                                       │
                                       └── AI: hybrid retrieve + LLM + guardrails
```

**Draw time goal:** <2 minutes. Practice until automatic.

---

## Model Answer Deep-Dive (the bullets)

> *This is the "expanded" version. Use when they ask follow-up. Each bullet is a possible probe.*

### 1. Clarifying questions to ask first (5–8)

- Primary users: testers, eng leaders, execs, internal analysts, ML systems?
- What must be real-time vs daily?
- Volumes: tenants, executions, results, artifacts, queries (today + 3-year)?
- Strict ordering per execution, or eventual correction OK?
- Retention + residency tiers?
- Tenant isolation guarantees + enterprise access models?
- Is this greenfield or migration with zero dashboard downtime?
- Customer artifacts permitted as model input? Opt-in / BYOK policy?

### 2. Quantify the scale (back-of-envelope)

```
Assume 10k daily-active teams
× 20 executions/team/day
× 100 results/execution
= 20M test results/day

20 lifecycle/step events/result
= 400M events/day ≈ 4.6k events/sec avg
× 10 peak = 46k events/sec peak

~1.2 TB/day compressed events
~1 TB/day artifacts (screenshots, logs, video)

ARTIFACTS DOMINATE STORAGE COST
→ tiering and lifecycle matter
```

**What changes the design:**
- 10× peak → more partitions + hot-tenant isolation
- Artifacts at 100MB instead of 5MB → tiering wins
- Sub-second joins across many dims → real-time OLAP justified
- 5-min freshness tolerable → fewer systems

### 3. Architecture choices & why

| Decision | Pick | Why |
|---|---|---|
| Ingestion | Kafka/MSK | Replay, durable, multi-consumer |
| Stream processing | Flink | Stateful, event-time, late handling |
| Lake storage | S3 + Iceberg | Open, cheap, ACID, multi-engine |
| Curated transform | Spark + dbt | dbt = lineage + tests, Spark = scale |
| Warehouse | Snowflake or Databricks | Open Iceberg support; benchmark on cost |
| Real-time OLAP | ClickHouse or Pinot (optional) | Only if latency SLO demands it |
| Artifact store | S3, lifecycle to Glacier | Different cost + retention profile |
| Vector index | pgvector or managed vector search | One fewer system if pg suffices |
| Orchestration | Airflow / MWAA | Existing skills, EKS-friendly |

### 5. Trade-offs to name aloud

- "Real-time OLAP is an *option*, not a default — adds cost and ops."
- "Lakehouse + warehouse is two systems; synchronize via the same open table format to avoid drift."
- "Tenant isolation in S3 via prefix policy + IAM, not via separate accounts unless required."
- "AI plane reads governed outputs, not production stores."

### 6. Metrics of success

- **Trust:** % critical data products meeting freshness + completeness SLO
- **Cost:** $/1M events, $/query, $/active tenant
- **AI:** verified reduction in time-to-triage (not thumbs-up)
- **Adoption:** % dashboards on certified metrics, weekly active users
- **Incidents:** MTTD, MTTR, recurrence rate

---

## Follow-ups They Will Probe

> *For each, prep a 30-second answer.*

1. **"Why not one platform for everything?"** — Workload boundaries still matter: live state ≠ durable history ≠ governed BI ≠ retrieval. Verify one platform covers several before adding a second. Add specialized stores only when SLOs demand it.

2. **"Would you choose a data mesh?"** — Federated ownership yes; data-mesh reorganization no. Domain owners + central paved road. Measure outcomes, not # of data products.

3. **"How do you guarantee exactly-once?"** — I don't claim a universal guarantee. At-least-once transport, stable event IDs, per-aggregate versions, idempotent merges, reconciliation against execution manifests.

4. **"Why not send the whole log to the LLM?"** — Cost, latency, relevance, privacy, injection surface. Deterministic extraction + bounded retrieval + tenant-filtered context + structured outputs.

5. **"What's your AI north-star?"** — Verified reduction in time-from-failure-to-correct-triage. Subject to correctness, safety, cost guardrails. Thumbs-up is diagnostic, not the metric.

6. **"How hands-on should a Head of Data be?"** — Hands-on enough to review architecture, models, SQL, incidents. Not the bottleneck for every implementation. Code and design reviews set the bar.

---

## Common Traps (red-flag answers)

- ❌ "I'd migrate everything to Snowflake" in day 1.
- ❌ "I'd build a data lakehouse to solve everything."
- ❌ "Use Kafka for ordering across topics" (Kafka only orders within a partition).
- ❌ "Send the entire log to GPT."
- ❌ "We have exactly-once delivery." (It's at-least-once + idempotent sink.)
- ❌ "Governance is Legal's job."
- ❌ Inventing Katalon's stack, traffic, or your past metrics.

---

## Practice Log

> *Track reps. Practice until each answer is ≤90s and the diagram is <2 min.*

| Date | Time | Mode | Self-score (1–4) | Notes |
|---|---|---|---|---|
| | | (cold / timed / peer) | | |
| | | | | |
| | | | | |

---

## Linked Material

- **Source prep doc:** `Katalon_Head_of_Data_Interview_Prep.md` Section 5
- **Stories:** fill `[BLANK]`s in Section 21 — link to `Katalon_Stories_PRIVATE.md`
- **Flashcards:** Section 23 of the source doc
- **Scoring rubric:** Section 20 of the source doc (1–4 across 10 dimensions)

---

## Checklist Before Walking In

- [ ] 90-second answer said aloud, no notes
- [ ] Diagram drawn from memory in <2 min
- [ ] Each follow-up probe answered in <30 sec
- [ ] Trade-off stated, not just choice
- [ ] Metric named at the end
- [ ] No invented numbers / stack claims