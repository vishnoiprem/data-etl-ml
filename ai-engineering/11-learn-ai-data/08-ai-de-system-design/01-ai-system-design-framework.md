# Lesson 1 — AI System Design Framework

> **Type:** Article · Module 8 · AI DE System Design
> The 5-step framework that makes every AI DE system-design question answerable.

---

## Why you need a framework

Open-ended AI design questions ("design a recommendation system") are easy to flounder on. **Without a structure, you spend 30 minutes naming boxes and 5 minutes on the parts that actually matter.**

The 5-step framework forces you to spend your time on the **decisions**, not the drawing. It's the difference between a senior answer and a junior one.

---

## The 5-step framework

```
   ┌──────────────────────────────────────────────────────────────┐
   │  AI DE SYSTEM-DESIGN FRAMEWORK                               │
   │                                                              │
   │   1. CLARIFY    5 min   — what are we building, for whom?    │
   │   2. SKETCH     10 min  — end-to-end, 10–15 boxes           │
   │   3. DEEP-DIVE  15 min  — the 2–3 boxes that matter         │
   │   4. TRADEOFFS  5 min   — explicit pros/cons                │
   │   5. SUMMARY    3 min   — decision + what you'd revisit     │
   │                                                              │
   │   Total: ~38 minutes for a senior interview question.        │
   └──────────────────────────────────────────────────────────────┘
```

---

## Step 1 — CLARIFY (5 min)

The single biggest interview mistake: jumping to a solution. **Before you draw anything, ask questions.**

```
   CLARIFY
   ───────
   1. What is the product, who is the user?
      (consumer / enterprise / internal)

   2. What's the scale?
      - users: 1k / 1M / 100M
      - items: 10k / 10M / 1B
      - QPS: 10 / 1k / 100k

   3. What's the freshness need?
      - real-time (< 1s) / minute / hour / daily

   4. What's the latency budget?
      - online: < 50ms / < 200ms / < 2s
      - batch: minutes / hours

   5. What are the constraints?
      - ACL / tenancy / compliance (HIPAA, SOC2)
      - cost ceiling ($/month)
      - team capability (Spark / ML / LLMs)
      - existing stack (Snowflake / Databricks / AWS)

   6. What's the failure mode we most fear?
      - wrong answer (fraud miss)
      - slow answer (UX)
      - data leak (ACL breach)
      - cost blowout
      - silent model degradation
```

**Write these down. Even in an interview.** The interviewer wants to see you reason from constraints.

---

## Step 2 — SKETCH (10 min)

Draw **10–15 boxes**. Each box has a one-line role. Don't drill into details.

```
   SKETCH (template)
   ────────────────

   [USER] → [CLIENT / APP] → [API GATEWAY]
                                  │
                                  ▼
                            [SERVING TIER]
                                  │
                ┌─────────────────┼─────────────────┐
                ▼                 ▼                 ▼
         [VECTOR DB]      [FEATURE STORE]    [MODEL SERVER]
                │                 │                 │
                └─────────────────┼─────────────────┘
                                  │
                                  ▼
                            [LLM / ML]
                                  │
                                  ▼
                           [ANSWER → USER]

   (parallel:)
   [INGEST] → [TRANSFORM] → [EMBED / FEATURIZE] → [OFFLINE STORES]
                  │
                  ▼
              [EVAL HARNESS]
              [MONITORING]
              [LOGGING]
```

The **boxes** you draw depend on the system:
- **Recommender**: candidates → ranker → blender → serving
- **RAG**: embed → vector DB → rerank → LLM → answer
- **Fraud**: enrich (features) → model → decision → feedback
- **Feature platform**: source → transform → offline store + online store
- **Multi-modal**: type router → per-type parser → embed → unified vector DB

The **boxes you don't draw** are also a signal. If you forget monitoring, eval, ACL, or cost dashboards, the interviewer will note it.

---

## Step 3 — DEEP-DIVE (15 min)

Identify the **2–3 boxes that actually decide the outcome**. Spend your time here.

```
   DEEP-DIVE candidates (pick the ones that matter for THIS question)
   ─────────────────────────────────────────────────────────────────
   - Retrieval quality (RAG, search)
   - Online inference latency (recsys, fraud)
   - Online/offline feature parity (feature platform)
   - Cost at scale (everything with LLMs)
   - ACL / multi-tenancy (enterprise)
   - Drift / monitoring (everything in production)
   - Eval set quality (everything with LLMs)
   - Backfill / replay (training data versioning)
```

For each deep-dive box, you answer four questions:
1. **What is it doing?** (one sentence)
2. **What's the data shape?** (rows × columns × freshness)
3. **What's the tech choice?** (with one alternative)
4. **What's the failure mode?** (and how do you detect it)

---

## Step 4 — TRADEOFFS (5 min)

For every major choice, **state the alternative and why you didn't pick it.**

```
   TRADEOFFS (template)
   ────────────────────

   Choice A:  Pinecone (managed vector DB)
   vs Choice B: Weaviate (self-hosted)
   Why A:     team is small, ops budget is tight, sub-50ms p95 SLA
   Tradeoff:  higher per-query cost ($X/mo vs $Y/mo), less control
   Revisit if: cost > $10k/mo OR we need custom index type

   Choice A:  Claude Opus for top-tier answers
   vs Choice B: Claude Haiku for everything
   Why A:     accuracy on the eval set is 92% vs 78%
   Tradeoff:  10× cost; route only the hard queries to Opus
   Revisit if: cost > $X/mo OR Haiku quality catches up
```

The act of stating tradeoffs **is the answer**. Interviewers want to see that you know the alternatives and that you can defend your choice.

---

## Step 5 — SUMMARY (3 min)

State your decision in one paragraph. Then say what would change your mind.

```
   SUMMARY
   ───────
   Decision: tiered LLM (Haiku for routing/extraction, Opus for answer),
             managed vector DB (Pinecone), online features from
             feature store, eval-driven deployment with shadow/canary.

   Revisit if:
   - cost grows > $X/mo (consider self-hosted vector DB)
   - latency p95 > 200ms (consider caching, smaller LLM)
   - eval faithfulness < 90% (consider reranker, better KB)
   - ACL breach (consider row-level security, audit log)
```

The summary forces you to **commit** to a design. Half the value of system design is the willingness to defend your choices.

---

## What "good" looks like in an interview

- **Frameworks over features.** Boxes are roles, not product names. "Vector store" beats "Pinecone S2."
- **Numbers everywhere.** "100M users, 1k QPS, < 50ms p95." Show you've done the math.
- **Cost next to latency.** "$5k/mo, 30ms p95." Both matter.
- **Tradeoffs explicit.** "I picked X because Y, the cost is Z."
- **Failure modes addressed.** Drift, ACL breach, silent regression — name them.
- **Operations included.** Monitoring, eval, on-call — not bolted on.
- **What you'd change.** Nothing is perfect; show you know the limits.

---

## The common interview traps

```
   TRAP                                   FIX
   ────                                   ───
   Jumping to a solution                  Ask clarifying questions first
   Drawing boxes without roles            One-line role per box
   Forgetting offline / batch             Both online and offline paths
   No ACL story                           Always say "row-level security"
   No eval story                          Always say "200-query eval set"
   No cost story                          Always say "$X/mo at Y QPS"
   No monitoring story                    Always say "drift, latency, cost"
   "We'll use Spark" without sizing       "Spark on X nodes for Y TB"
   "We'll use Kafka" without topic design "topic per entity class, retention X"
   "We'll fine-tune" without data story   "fine-tune on N examples, eval M"
```

---

## The "system design cheat sheet" template

Keep one of these for every system design you practice:

```markdown
# <System name> — system design

## Clarify
- users: ...
- scale: ...
- freshness: ...
- latency: ...
- constraints: ...
- failure mode: ...

## Sketch
[ASCII diagram]

## Deep-dive
- Box A: ...
- Box B: ...
- Box C: ...

## Tradeoffs
| Choice | Alt | Why | Revisit if |

## Summary
Decision: ...
Revisit if: ...
```

Practise 3–5 designs with this template. You'll internalise the structure.

---

## What Comes Next

> Lesson 2 — **Recommendation Pipeline** — full worked design at billion-scale. Follow the framework end-to-end.