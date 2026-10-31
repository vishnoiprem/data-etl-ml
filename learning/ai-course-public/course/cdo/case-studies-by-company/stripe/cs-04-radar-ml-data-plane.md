# CS-04 (Stripe) — Designing the Radar + smart-retries ML data plane at $1.4T TPV scale

> **Mapping:** Original CS-04. Retargeted to Stripe's Radar fraud ML + smart-retries workload.
> **Goal:** 30 minutes. Design the ML data plane that serves Radar + smart-retries + Issuing ML. Present to the Radar lead, the Payments engineering lead, and the CFO.

## The brief

You are pitching the architecture for the ML data plane that powers all production ML at Stripe. The Radar lead wants sub-100ms decision latency. The Payments engineering lead wants zero-trust. The CFO wants the bill under $XM/year. The CISO wants PCI-DSS + SOC2 clean.

**Context:**
- $1.4T TPV 2024
- Radar: 100% of payment traffic passes through; sub-100ms decision
- Smart-retries: 2022 published +10.5% revenue lift on retried declines
- Issuing ML: credit decisioning, spend management
- Compliance: PCI-DSS, SOC2, BSA/AML, 50-state money transmission, EU/UK regulators

**Your task:** Design the architecture. 5 layers. Cross-cutting. Build-vs-buy. Cost trajectory. Defend in 30 minutes.

## Solution sketch (do not copy — internalize and re-speak)

**Diagnosis (3 min).**
- Radar is the proof point — 10+ years of ML production at the highest scale
- The data plane that feeds Radar + smart-retries + Issuing ML is the next ceiling
- `[CONFIRM: 3+ feature stores across Radar / smart-retries / Issuing]`
- The diagnosis: ML model layer is best-in-class; the data + feature layer is fragmented.

**Target architecture (10 min).**

```
Authorization events (cards, wallets, ACH, 3DS, BIN, IP, device, behavior)
  ↓ streaming (Kafka + Flink)
Lakehouse (Iceberg on internal storage)  ← single source of truth
  ↓ Transformation (dbt + Spark)
Cross-ML feature store (online + offline)  ← single source of feature truth
  ↓
Consumption: Radar (fraud), smart-retries (decline retry), Issuing (credit), Sigma (merchant analytics)
```

**Cross-cutting:**
- Lineage (internal; required for PCI / SOC2)
- Observability (feature drift, model drift, data quality)
- Orchestration (internal; based on Airflow-like)
- FinOps dashboard per ML workload
- IAM + zero-trust (Radar secrets are crown-jewel)
- Contracts (data + model contracts per BU)

**ML platform:**
- Online feature store (sub-10ms lookup) — Redis-like internal
- Offline feature store (Iceberg)
- Model registry (in-house) with continuous eval
- Eval harness (in-house) with adversarial-robustness tooling
- LLM/AI serving for Sigma NL→SQL, Stripe Assistant, merchant-facing AI
- RAG + Agent runtime for merchant-facing AI
- Guardrails (in-house; PCI + content-safety)

**Build-vs-buy (5 min):**
1. **Lakehouse on internal storage + Iceberg** — privacy + cost; don't ship TPV to a third-party warehouse
2. **Cross-ML feature store in-house** — the features are the IP; merchant-behavior features are unique
3. **dbt for transformation** — industry standard
4. **Online feature store in-house** — sub-10ms requires it; vendors can't get there
5. **Radar ML** — Stripe-native, not vendored
6. **LLM serving** — use providers (OpenAI / Anthropic) + Stripe-built guardrails; do NOT build a foundation model
7. **RAG + agent runtime** — in-house; the merchant context is unique
8. **Custom eval harness** — adversarial robustness is Radar-specific
9. **In-house guardrails** — PCI + content safety
10. **Multi-region failover** — global TPV; downtime = lost revenue
11. **Zero-trust IAM** — Radar secrets are crown-jewel
12. **CMEK** — for sensitive features (card, identity)
13. **PCI-DSS / SOC2 / BSA-AML compliance** — model risk, data lineage, audit log

**Security posture (5 min).**
- IAM, encryption, lineage, audit, key mgmt
- PCI-DSS scope: feature store + model serving must be in-scope; lineage mandatory
- BSA/AML: Radar is the AML line of defense; data quality scorecard mandatory
- Content policy: Sigma NL→SQL must respect data-privacy rules (no PII to LLMs)

**Cost trajectory (5 min).**
- Y0 (today): $XM across `[CONFIRM: current Radar + smart-retries + Issuing infra]`
- Y1: $YM (unified ML data plane, cross-ML feature store, 1 cross-ML model; consolidation saves $Z)
- Y2: $0.9YM (5 cross-ML models; online + offline feature store)
- Y3: $0.85YM (10+ ML models; first merchant-facing AI agent in production)

**Q&A — be ready for:**
- "Why a Radar-specific data plane vs. a generic one?" — The features are fraud-specific; the model is fraud-specific. The cross-ML feature store serves fraud + credit + merchant-analytics features.
- "Why not a third-party feature store?" — The features are the IP. A vendor sees the feature schema. PCI / customer trust says no.
- "How do you handle adversarial-robustness?" — Quarterly red-team; eval harness; online drift detection; merchant-level feedback loop.
- "What about Issuing ML?" — Same feature store, different feature subset, different model. The cross-ML feature store is the platform; the BU owns the features.

## Watch for when you re-listen

- **Did you draw the architecture?** The Radar lead needs to see the boxes.
- **Did you name the rejected alternatives?** If they ask "why not X?" and you don't have an answer, you've lost.
- **Did you quantify the cost?** A cost trajectory without $ is a wish.
- **Did you end on time?** The leads conclude you can't prioritize if you run over.

---

**Source:** Adapted from original CS-04 + Stripe case-study brief.
