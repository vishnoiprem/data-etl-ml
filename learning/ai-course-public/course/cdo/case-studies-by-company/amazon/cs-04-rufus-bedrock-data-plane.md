# CS-04 (Amazon) — Designing the data plane that powers Rufus + Q + Bedrock + the recommendation engines

> **Mapping:** Original CS-04. Retargeted to Amazon's Rufus + Q + Bedrock + recommendation workloads.
> **Goal:** 30 minutes. Design the data plane that serves all production ML + AI at Amazon. Present to the Bedrock lead, the Rufus lead, the Q lead, and the CFO.

## The brief

You are pitching the architecture for the data plane that powers Rufus (consumer AI), Q (enterprise AI), Bedrock (FM marketplace), the retail recommendation engines, and the supply chain ML. The Bedrock lead wants low-latency model serving. The Rufus lead wants real-time personalization. The Q lead wants enterprise-grade governance. The CFO wants the bill under $XM/year. The CISO wants SOC2 + FedRAMP clean.

**Context:**
- $638B revenue; 3 segments (NA, Intl, AWS)
- Bedrock in production (since 2023); Anthropic as the primary model partner
- Q in production (since 2023); Q for Business / Developer / QuickSight
- Rufus in production (since 2024); consumer AI shopping assistant
- Trainium + Inferentia as the custom silicon
- Compliance: SOC2, FedRAMP, PCI-DSS, GDPR, EU AI Act, state AGs on advertising

**Your task:** Design the architecture. 5 layers. Cross-cutting. Build-vs-buy. Cost trajectory. Defend in 30 minutes.

## Solution sketch (do not copy — internalize and re-speak)

**Diagnosis (3 min).**
- Bedrock is the proof point — FM marketplace at the largest enterprise scale
- The data plane that feeds Rufus + Q + Bedrock + the recommendation engines is the next ceiling
- `[CONFIRM: 3+ feature stores across Rufus / Q / Bedrock / retail recs / supply chain]`
- The diagnosis: ML + AI model layer is best-in-class; the data + feature layer is fragmented.

**Target architecture (10 min).**

```
Source events (retail, marketplace, AWS, devices, ads, supply chain, Prime)
  ↓ CDC + streaming (Kinesis + Dataflow)
Lakehouse (S3 + Iceberg via Lake Formation)  ← single source of truth
  ↓ Transformation (dbt + Spark / EMR)
Cross-AI feature store (online + offline)  ← single source of feature truth
  ↓
Consumption: Rufus (consumer AI), Q (enterprise AI), Bedrock (FM marketplace), retail recs, supply chain ML, ads ML, Alexa LLM, Buy with Prime
```

**Cross-cutting:**
- Lineage (required for SOC2 + FedRAMP + EU AI Act)
- Observability (feature drift, model drift, data quality)
- Orchestration (Step Functions / Airflow)
- FinOps dashboard per BU
- IAM + zero-trust
- Contracts (data + model contracts per BU)

**AI / ML platform:**
- Cross-AI feature store (online + offline)
- Bedrock FM marketplace (Anthropic, Meta, Mistral, Cohere, Stability, Amazon Titan)
- Q for Business / Developer / QuickSight
- Rufus consumer AI serving
- Retail recommendation serving (low-latency)
- Supply chain ML serving
- Ads ML serving
- Alexa LLM serving
- RAG + agent runtime for Rufus + Q + Bedrock
- Eval harness (in-house; FM-specific)
- Guardrails (in-house; enterprise-grade)
- Trainium + Inferentia (custom silicon)

**Build-vs-buy (5 min):**
1. **S3 + Lake Formation + Iceberg** — already in production; the largest object store in the world
2. **Cross-AI feature store in-house** — the features are the IP; cross-segment features are unique
3. **dbt for transformation** — industry standard
4. **Bedrock FM marketplace** — already in production; multi-model is the hedge
5. **Anthropic as primary model partner** — $4B+ investment; the right answer
6. **Trainium + Inferentia** — cost + performance play
7. **RAG + agent runtime** — in-house; the cross-segment context is unique
8. **Custom eval harness** — Bedrock + Q + Rufus are Amazon-specific
9. **In-house guardrails** — enterprise-grade; FedRAMP clean
10. **Multi-region failover** — global; data residency matters
11. **Zero-trust IAM** — cross-segment access is crown-jewel
12. **CMEK** — for sensitive features
13. **EU AI Act compliance** — model registry, eval, human oversight

**Security posture (5 min).**
- IAM, encryption, lineage, audit, key mgmt
- PCI-DSS scope: retail payment + ads must be in-scope
- GDPR + EU AI Act: Rufus + Q outputs must respect data-privacy rules
- FedRAMP: Q for Government must be FedRAMP-clean
- Brand safety: Q + Bedrock outputs must respect the Amazon brand voice (in-house content-safety pipeline)

**Cost trajectory (5 min).**
- Y0 (today): $XM across `[CONFIRM: current Rufus + Q + Bedrock + retail recs + supply chain infra]`
- Y1: $YM (unified AI data plane, cross-AI feature store, 1 cross-segment AI model; consolidation saves $Z)
- Y2: $0.9YM (5 cross-segment AI models; Bedrock v2)
- Y3: $0.85YM (10+ AI models; first autonomous retail AI in production)

**Q&A — be ready for:**
- "Why a Bedrock-specific data plane vs. a generic one?" — The features are FM-specific; the model is FM-specific. The cross-AI feature store serves retail + AWS + Prime features.
- "Why not a third-party feature store?" — The features are the IP. A vendor sees the feature schema. Cross-segment trust says no.
- "How do you handle brand safety?" — In-house content-safety pipeline + LLM-as-judge; red-team quarterly; customer-feedback loop.
- "What about EU AI Act?" — Model registry, eval, human oversight, transparency report. Bedrock + Q + Rufus are in scope.
- "What about supply chain ML?" — Same feature store, different feature subset, different model. The cross-AI feature store is the platform; the BU owns the features.
- "What about the Anthropic partnership?" — Anthropic is the primary model partner; Bedrock is the marketplace; Trainium is the silicon. The right answer is "Anthropic + Bedrock + Trainium, not Anthropic alone."

## Watch for when you re-listen

- **Did you draw the architecture?** The Bedrock lead needs to see the boxes.
- **Did you name the rejected alternatives?** If they ask "why not X?" and you don't have an answer, you've lost.
- **Did you quantify the cost?** A cost trajectory without $ is a wish.
- **Did you end on time?**

---

**Source:** Adapted from original CS-04 + Amazon case-study brief.