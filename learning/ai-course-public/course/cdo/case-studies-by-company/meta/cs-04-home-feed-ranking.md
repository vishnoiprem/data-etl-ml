# CS-04 (Meta) — Designing the Home Feed ranking data plane at 3.54B DAP

> **Mapping:** Original CS-04. Retargeted to Meta's Home Feed ranking at Family-of-Apps scale.
> **Goal:** 30 minutes. Design the data plane that serves Home Feed ranking for FB + IG. Present to the Andromeda lead, the IG ranking lead, and the FB ranking lead.

## The brief

You are pitching the architecture for a unified cross-product ranking data plane that serves Home Feed (FB + IG) and Reels. The Andromeda lead (ad retrieval) is the model-layer peer. The ranking leads want their pods unblocked. The CISO wants zero-trust. The CFO wants the bill under $XM/year.

**Context:**
- 3.54B Family DAP; ad impressions +14% YoY
- Andromeda (ad retrieval) + GEM (ranking) in production
- Meta AI in WhatsApp/IG/FB/Messenger
- Llama 4 cadence; MSL owns the model layer
- Compliance: GDPR, CCPA, EU AI Act, plus Meta's content policies

**Your task:** Design the architecture. 5 layers. Cross-cutting. Build-vs-buy. Cost trajectory. Defend in 30 minutes.

## Solution sketch (do not copy — internalize and re-speak)

**Diagnosis (3 min).**
- Andromeda + GEM are the AI proof points. The data plane that feeds them is the next ceiling.
- `[CONFIRM: 5+ feature stores across FB/IG/WhatsApp/Threads — likely true at Meta scale]`
- The diagnosis: the model layer is best-in-class; the data + feature layer is fragmented.

**Target architecture (10 min).**

```
Source events (FB/IG/Reels user actions, ad events, content signals)
  ↓ CDC + streaming (Scribe / Stylus / mafka)
Lakehouse (Iceberg on Tectonic)  ← single source of truth
  ↓ Transformation (dbt + Spark)
Cross-product feature store (online + offline)  ← single source of feature truth
  ↓
Consumption: Andromeda (ad retrieval), GEM (ranking), Home Feed, Reels, Meta AI, RAG + agents
```

**Cross-cutting:**
- Lineage (Meta-internal)
- Observability (DQ)
- Orchestration (Meta-internal)
- FinOps dashboard per pod
- IAM + zero-trust
- Contracts (in-house framework)

**AI platform:**
- Cross-product feature store (online + offline)
- Andromeda (ad retrieval serving)
- GEM (ranking serving)
- Llama 4 + Meta AI serving
- RAG + Agent runtime
- Eval harness (shared with MSL)
- Guardrails (in-house + vendor)

**Build-vs-buy (5 min):**
1. **Lakehouse on Tectonic + Iceberg** — per Opinion 2.
2. **Cross-product feature store in-house** — per Opinion 4. The features are the IP.
3. **dbt for transformation** — industry standard.
4. **Andromeda + GEM** — Meta-native, not vendored.
5. **Llama serving on Meta-internal infra** — not third-party.
6. **RAG + agent runtime** — LangChain or in-house.
7. **Custom eval harness** — per Opinion 6.
8. **In-house guardrails** — defense in depth.
9. **Multi-region failover** — global scale.
10. **Zero-trust IAM** — Meta's internal standard.
11. **CMEK** — for sensitive features.
12. **EU AI Act compliance** — model registry, eval, human oversight.

**Security posture (5 min).** IAM, encryption, lineage, audit, key mgmt. Plus content-policy guardrails for Meta AI outputs.

**Cost trajectory (5 min).**
- Y0 (today): $XM across `[CONFIRM: current Family of Apps data + AI infra]`
- Y1: $YM (unified data plane, semantic layer, 1 cross-product AI; consolidation saves $Z)
- Y2: $0.9YM (5 cross-product AI; cross-product feature store)
- Y3: $0.85YM (10+ AI; Llama-as-a-service revenue)

**Q&A — be ready for:**
- "Why Andromeda-specific data plane vs. a generic one?" — The features are ad-specific; the model is ad-specific. The cross-product feature store serves the ad-specific features + the user-specific features.
- "Why not a third-party feature store?" — Per Opinion 4. The features are the IP.
- "How do you handle content-policy guardrails for Meta AI?" — In-house pipeline + LLM-as-judge; red-team quarterly; transparency report.

## Watch for when you re-listen

- **Did you draw the architecture?** The ranking leads need to see the boxes.
- **Did you name the rejected alternatives?** If they ask "why not X?" and you don't have an answer, you've lost.
- **Did you quantify the cost?** A cost trajectory without $ is a wish.
- **Did you end on time?** The leads conclude you can't prioritize if you run over.

---

**Source:** Adapted from original CS-04 + Meta case-study brief.