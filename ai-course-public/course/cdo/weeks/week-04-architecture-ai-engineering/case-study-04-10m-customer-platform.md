# Case Study 4: The 10M-Customer Platform

> **Week 4 · Case Study · 90 min**
> **Deliverable:** A secure, scalable enterprise data & AI platform for 10M customers.

## The brief

You are pitching the CTO and CISO of a 10M-customer retailer. The CTO wants a unified data platform. The CISO wants zero-trust security. The CEO wants AI in production in 12 months. The CFO wants the bill under $XM/year.

**The brief:**
- 10M customers, 1,200 stores, 5 BUs
- 50B events/day
- 4M MAU across web, app, in-store
- Regulated (PCI-DSS, GDPR, CCPA, soon AI Act)
- Current state: 3 warehouses, 6 BI tools, no contracts, 4 definitions of "active customer"
- Target: 1 platform, 1 semantic layer, 5 AI use cases in production, SOC 2 + ISO 27001

You have 30 minutes to present the architecture. The CTO and CISO will challenge every choice.

## The structure (30 minutes total)

| Section | Time | What to say |
|---|---|---|
| The diagnosis | 3 min | The state of the platform today |
| The target architecture | 10 min | The 5 layers + cross-cutting + AI |
| The build-vs-buy | 5 min | The 12 most-debated choices |
| The security posture | 5 min | The 5 security controls + the AI Act |
| The cost trajectory | 5 min | $XM today, $YM year 1, $ZM year 3 |
| Q&A | 2 min | Defend the rejected alternatives |

## The scoring rubric (out of 100)

| Competency | Weight | What "great" looks like |
|---|---|---|
| Technical judgment and architecture | 50% | The architecture has a story; the trade-offs are named |
| Strategic and business thinking | 20% | The architecture supports the business strategy |
| Commercial and financial understanding | 15% | The build-vs-buy and cost trajectory are credible |
| Governance and risk | 10% | The security and compliance controls are in the design |
| Communication and structure | 5% | The diagram is clear; the narrative is short |

A score below 90 means Week 4 is not done. Re-record.

## Acceptance criteria

- 30 minutes, no overrun
- 0 acronyms in the opening 2 minutes
- 5 layers drawn and named
- Cross-cutting platform named (observability, lineage, FinOps, security, governance)
- AI architecture (feature store, RAG, agent, eval, guardrail) named
- 12 build-vs-buy choices justified
- 5 security controls named
- Cost trajectory named with $X, $Y, $Z
- "Why not Snowflake / Databricks / AWS / Azure / GCP?" answered

## Starter

Use Day 16's 5 layers, Day 17's 6 R's, Day 18's reliability plan, Day 19's ML architecture, Day 20's GenAI architecture. Synthesize into one coherent story.

## Solution sketch (do not copy — internalize and re-speak)

**Diagnosis (3 min):**
- 3 warehouses, 6 BI tools, 4 metric definitions → no single source of truth
- 50B events/day going into 3 different stacks → wasted infra, no cross-BU insights
- No data contracts → pipeline breaks every time a source system changes
- 0 AI use cases in production → 18 months of "almost" with nothing shipped
- The diagnosis is "we have data, but we don't have a platform."

**Target architecture (10 min):**

```
Sources (POS, e-com, app, ERP, supply, IoT)
  ↓ CDC + streaming (Kafka, Fivetran)
Lakehouse (Iceberg on S3)  ← single source of truth
  ↓ Transformation (dbt, Spark)
Semantic layer (dbt SL + Cube)  ← single source of metric truth
  ↓
Consumption: Looker (BI), APIs (data products), RAG (AI), Agents (AI)
```

**Cross-cutting:** DataHub (lineage), Monte Carlo (observability), Dagster (orchestration), FinOps dashboard, IAM + Unity Catalog (security), contracts (in-house).

**AI platform:** Feature store (Feast), training (Databricks ML), registry (MLflow), serving (SageMaker + Spark), monitoring (Evidently), GenAI (pgvector + LangChain + custom eval + guardrails).

**Build-vs-buy (5 min):**
1. **Lakehouse (Iceberg) over S3** — open table format; not locked to one vendor. *Why not Snowflake only?* Cost at 50B events/day is 2-3× a lakehouse.
2. **dbt for transformation** — SQL-native, version-controlled, testable. *Why not Spark only?* 80% of transformations are SQL; Spark is the 20%.
3. **Feature store in-house (Feast)** — the feature definitions are the IP. *Why not Tecton?* Cost at 10M customers is 3-5× an OSS build.
4. **Multi-model LLM (OpenAI + Anthropic)** — route by task; vendor diversification.
5. **pgvector for vector store (start)** — start with Postgres, scale to Pinecone if needed. *Why not Pinecone from day 1?* Cost; complexity; can move later.
6. **LangChain for orchestration (start)** — open standards; replace per use case.
7. **Custom eval harness** — this is the IP. *Why not a vendor?* Vendor eval is shallow; we need domain-specific.
8. **In-house guardrails (start) + vendor (defense in depth)** — LLM-as-judge + PII filter.
9. **DataHub for lineage** — open source, integrates with the lakehouse.
10. **Monte Carlo for observability** — best-in-class data quality monitoring.
11. **Dagster for orchestration** — asset-centric, lineage-aware.
12. **Unity Catalog for security** — fine-grained access; integrates with the lakehouse.

**Security posture (5 min):**
- IAM: role-based + attribute-based; least privilege
- Encryption: at rest (AES-256) + in transit (TLS 1.3); customer-managed keys
- Lineage: column-level; required for GDPR right-to-erasure
- Audit: every query logged; every model version logged; every prompt logged
- Key mgmt: KMS, rotation policy, break-glass procedure
- AI Act: model registry, eval reports, human oversight, transparency

**Cost trajectory (5 min):**
- Y0 (today): $XM across 3 warehouses, 6 BI tools, ad-hoc infra [CONFIRM]
- Y1: $YM (lakehouse + semantic + 1 AI use case; consolidate 3 → 1 saves $Z)
- Y2: $0.9YM (5 BUs on platform; 5 AI use cases; data products)
- Y3: $0.85YM (10+ AI use cases; externalized data products; agentic AI)

**Q&A — be ready for:**
- "Why not all-Snowflake?" (cost at scale; vendor lock)
- "Why not all-Databricks?" (cost; we want best-of-breed per layer)
- "Why not AWS only?" (we want multi-cloud for resilience and negotiation)
- "Why build a feature store?" (it's the IP; vendor cost at our scale is 3-5×)
- "How do you handle the AI Act?" (model registry, eval, human oversight, transparency)

## What to watch for when you re-listen

- **Did you draw the architecture?** The CTO needs to see the boxes, not just hear the words.
- **Did you name the rejected alternatives?** If the CISO asks "why not Snowflake?" and you don't have an answer, you've lost the room.
- **Did you quantify the cost?** A cost trajectory without $ is a wish.
- **Did you end on time?** If you run over, the CTO concludes you can't prioritize.

## Re-record until you score ≥ 90

A CDO who can't defend a platform architecture in 30 minutes is not a CDO. The architecture defense is the most-asked technical interview question.

---

**Next:** Week 5, Day 21 — Enterprise Data Governance.