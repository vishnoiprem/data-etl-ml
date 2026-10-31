# CS-04 (Google) — Designing the BigQuery + Vertex AI unified data plane for Ads + Search

> **Mapping:** Original CS-04 (10M-customer platform). Retargeted to GCP at Alphabet scale.
> **Goal:** 30 minutes. Design a secure, scalable, AI-ready enterprise data plane. Present to the CTO of Google Cloud (Amin Vahdat) and the CISO.

## The brief

You are pitching the architecture for a unified BigQuery + Vertex AI data plane that serves both internal Google workloads (Ads, Search) and external Cloud customers. The CTO wants the unified architecture. The CISO wants zero-trust. Kurian wants Cloud revenue. The CFO wants the bill under $XM/year.

**Context:**
- BigQuery = the warehouse. Vertex AI = the AI platform. BigQuery ML = the seam.
- Internal Google workloads: Ads reporting, Search analytics, YouTube creator metrics.
- External Cloud customers: `[CONFIRM: top 3-5 use cases]`.
- Compliance: SOC 2 + ISO 27001 + FedRAMP `[CONFIRM]` + EU AI Act posture.

**Your task:** Design the architecture. 5 layers. Cross-cutting platform. Build-vs-buy. Cost trajectory. Defend in 30 minutes.

## The structure (30 min)

| Section | Time | What to say |
|---|---|---|
| Diagnosis | 3 min | The current state of the BigQuery + Vertex AI seam |
| Target architecture | 10 min | 5 layers + cross-cutting + AI |
| Build-vs-buy | 5 min | The 12 most-debated choices |
| Security posture | 5 min | The 5 controls + AI Act |
| Cost trajectory | 5 min | $XM today, $YM Y1, $ZM Y3 |
| Q&A | 2 min | Defend the rejected alternatives |

## Solution sketch (do not copy — internalize and re-speak)

**Diagnosis (3 min).**
- BigQuery is the warehouse; Vertex AI is the AI platform. The seam is the bottleneck — `[CONFIRM: % of Cloud customers hit the seam in first 90 days]`.
- Internal Google workloads: Ads reporting is on `[CONFIRM]`; Search analytics is on `[CONFIRM]`; YouTube is on `[CONFIRM]`. The seam is internal too.
- The diagnosis: the architecture is right; the seam is the ceiling.

**Target architecture (10 min).**

```
Source systems (Ads events, Search logs, YouTube events, Cloud telemetry)
  ↓ CDC + streaming (Pub/Sub, Dataflow, Kafka)
Lakehouse (Iceberg on GCS)  ← single source of truth for raw data
  ↓ Transformation (dbt, Dataform, Spark)
BigQuery (semantic layer + ML feature store)  ← single source of metric truth
  ↓
Consumption: Looker (BI), Vertex AI (training + serving), RAG + agents, APIs
```

**Cross-cutting:**
- DataHub (lineage) — or Google's internal equivalent if known
- Monte Carlo or Google's internal observability (DQ)
- Dataform / dbt (orchestration)
- FinOps dashboard per team
- IAM + VPC Service Controls (security)
- Contracts (in-house framework)

**AI platform:**
- BigQuery ML (training on warehouse-resident data)
- Vertex AI (model serving, MLOps)
- Feature Store (Vertex)
- RAG + Agent runtime (LangChain on Vertex)
- Eval harness (custom)
- Guardrails (in-house + vendor)

**Build-vs-buy (5 min):**
1. **BigQuery over multi-warehouse.** Single source of metric truth. Per Opinion 2 — at this scale, the cost trajectory favors the lakehouse pattern, but BigQuery is the public face.
2. **Vertex AI over multi-model.** Single ML platform. Multi-model (Claude, Llama) is supported but Vertex is the default.
3. **BigQuery ML + Vertex feature store.** The seam. In-house, not Tecton. Per Opinion 4 — at 10M+ customers, build.
4. **DataHub for lineage** (or internal Google equivalent). Open source.
5. **Monte Carlo for observability** (or internal).
6. **dbt for transformation.** Industry standard.
7. **LangChain for RAG orchestration.** Open standards.
8. **Custom eval harness.** Per Opinion 6 — the eval is the IP.
9. **In-house guardrails.** Defense in depth.
10. **VPC Service Controls + IAM.** Zero-trust.
11. **Customer-managed encryption keys (CMEK).** For Cloud customers.
12. **Multi-region failover.** For the global scale.

**Security posture (5 min).**
- IAM: RBAC + ABAC, least privilege, JIT access, MFA mandatory
- Encryption: AES-256 at rest (GCS, BigQuery), TLS 1.3 in transit, CMEK
- Lineage: column-level, required for GDPR right-to-erasure
- Audit: every query logged (Cloud Audit Logs), every model version logged (Vertex Model Registry), every prompt logged
- Key mgmt: Cloud KMS, rotation policy, dual control for master keys
- AI Act: model registry, eval reports, human oversight, transparency

**Cost trajectory (5 min).**
- Y0 (today): $XM across `[CONFIRM: current Cloud Data + Vertex spend]`
- Y1: $YM (unified data plane, semantic layer, 1 cross-plane AI; consolidation saves $Z)
- Y2: $0.9YM (5 cross-plane AI; data products to Cloud customers)
- Y3: $0.85YM (10+ AI in production; externalized data products; agentic AI)

**Q&A — be ready for:**
- "Why BigQuery over Snowflake / Databricks?" — BigQuery is the Google-native data plane; the integration with Vertex AI is the seam. Snowflake/Databricks are vendor partnerships, not native.
- "Why not multi-cloud for resilience?" — Per Opinion 7. At Cloud scale, multi-cloud is a Y3 problem, not Y1.
- "How do you handle the AI Act for the EU Cloud customers?" — Model registry, eval reports, human oversight, transparency. The architecture is compliant by design.

## Watch for when you re-listen

- **Did you draw the architecture?** The CTO needs to see the boxes.
- **Did you name the rejected alternatives?** If the CISO asks "why not X?" and you don't have an answer, you've lost.
- **Did you quantify the cost?** A cost trajectory without $ is a wish.
- **Did you end on time?** The CTO concludes you can't prioritize if you run over.

---

**Source:** Adapted from original CS-04 + Google case-study brief.