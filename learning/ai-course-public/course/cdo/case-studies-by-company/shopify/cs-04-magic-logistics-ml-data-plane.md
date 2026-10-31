# CS-04 (Shopify) — Designing the data plane that powers Magic + Logistics ML + Capital underwriting

> **Mapping:** Original CS-04. Retargeted to Shopify's Magic + Logistics + Capital workloads.
> **Goal:** 30 minutes. Design the data plane that serves all production ML at Shopify. Present to the Magic lead, the Logistics ML lead, and the CFO.

## The brief

You are pitching the architecture for the data plane that powers Magic (GenAI), Logistics ML, Capital underwriting, and Shop Pay fraud. The Magic lead wants low-latency LLM serving + merchant-context. The Logistics ML lead wants real-time routing. The CFO wants the bill under $XM/year. The CISO wants SOC2 + PCI-DSS clean.

**Context:**
- 2M+ merchants; 175+ countries
- Magic in production (since 2023); Sidekick in beta
- Logistics ML in production (SFN + Deliverr)
- Capital ML in production
- Shop Pay fraud ML in production
- Compliance: SOC2, PCI-DSS, GDPR, EU AI Act, country-specific data-residency (175+ markets)

**Your task:** Design the architecture. 5 layers. Cross-cutting. Build-vs-buy. Cost trajectory. Defend in 30 minutes.

## Solution sketch (do not copy — internalize and re-speak)

**Diagnosis (3 min).**
- Magic is the proof point — GenAI in production at the highest scale
- The data plane that feeds Magic + Logistics + Capital is the next ceiling
- `[CONFIRM: 3+ feature stores across Magic / Logistics / Capital / Shop Pay]`
- The diagnosis: ML model layer is best-in-class; the data + feature layer is fragmented.

**Target architecture (10 min).**

```
Merchant events (orders, products, checkout, fulfillment, customer, marketing)
  ↓ CDC + streaming (Pub/Sub + Dataflow)
Lakehouse (BigQuery + Iceberg)  ← single source of truth
  ↓ Transformation (dbt + Spark)
Cross-ML feature store (online + offline)  ← single source of feature truth
  ↓
Consumption: Magic (GenAI), Logistics ML (routing), Capital (underwriting), Shop Pay (fraud), Plus (analytics), Hydrogen / Oxygen (merchant apps)
```

**Cross-cutting:**
- Lineage (required for SOC2 + EU AI Act)
- Observability (feature drift, model drift, data quality)
- Orchestration (Airflow-like internal)
- FinOps dashboard per BU
- IAM + zero-trust
- Contracts (data + model contracts per BU)

**AI / ML platform:**
- Cross-ML feature store (online + offline)
- Magic LLM serving (provider-based + in-house guardrails)
- Logistics ML serving (real-time routing)
- Capital underwriting serving (real-time)
- Shop Pay fraud serving (real-time)
- RAG + agent runtime for Sidekick + merchant-facing AI
- Eval harness (in-house; merchant-specific)
- Guardrails (in-house + vendor)

**Build-vs-buy (5 min):**
1. **BigQuery + Iceberg** — already in production; don't migrate
2. **Cross-ML feature store in-house** — the features are the IP; merchant features are unique
3. **dbt for transformation** — industry standard
4. **LLM serving** — use providers (OpenAI / Anthropic); do NOT build a foundation model
5. **RAG + agent runtime** — in-house; the merchant context is unique
6. **Custom eval harness** — Magic is merchant-specific
7. **In-house guardrails** — content safety + brand voice
8. **Multi-region failover** — 175+ countries; data residency matters
9. **Zero-trust IAM** — merchant data is crown-jewel
10. **CMEK** — for sensitive features
11. **EU AI Act compliance** — model registry, eval, human oversight

**Security posture (5 min).**
- IAM, encryption, lineage, audit, key mgmt
- PCI-DSS scope: Shop Pay fraud + Capital underwriting must be in-scope
- GDPR + EU AI Act: Magic outputs must respect data-privacy rules; merchant data is in the EU, must stay in the EU
- Brand voice: Magic outputs must respect the Shopify brand voice (in-house content-safety pipeline)

**Cost trajectory (5 min).**
- Y0 (today): $XM across `[CONFIRM: current Magic + Logistics + Capital + Shop Pay infra]`
- Y1: $YM (unified ML data plane, cross-ML feature store, 1 cross-ML model; consolidation saves $Z)
- Y2: $0.9YM (5 cross-ML models; Magic v3)
- Y3: $0.85YM (10+ ML models; Magic v4; merchant agent in production)

**Q&A — be ready for:**
- "Why a Magic-specific data plane vs. a generic one?" — The features are merchant-specific; the model is merchant-specific. The cross-ML feature store serves merchant + order + fulfillment features.
- "Why not a third-party feature store?" — The features are the IP. A vendor sees the feature schema. Merchant trust says no.
- "How do you handle brand voice?" — In-house content-safety pipeline + LLM-as-judge; red-team quarterly; merchant-feedback loop.
- "What about EU AI Act?" — Model registry, eval, human oversight, transparency report. Magic is in scope.
- "What about Logistics ML?" — Same feature store, different feature subset, different model. The cross-ML feature store is the platform; the BU owns the features.

## Watch for when you re-listen

- **Did you draw the architecture?** The Magic lead needs to see the boxes.
- **Did you name the rejected alternatives?** If they ask "why not X?" and you don't have an answer, you've lost.
- **Did you quantify the cost?** A cost trajectory without $ is a wish.
- **Did you end on time?**

---

**Source:** Adapted from original CS-04 + Shopify case-study brief.