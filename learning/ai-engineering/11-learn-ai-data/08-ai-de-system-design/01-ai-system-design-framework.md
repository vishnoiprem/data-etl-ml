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

## Worked Example — "real-time ad CTR prediction" through the full framework

> **Interview question:** *"Design a real-time ad click-through-rate prediction system. 100B events/day, p99 < 50ms, 100M ads. Predict probability of click given user, ad, context."*

### Step 1 — CLARIFY (5 min)

```
   users:        200M DAU
   ads:          100M, refresh 1M/day
   events:       100B/day (impressions + clicks), peak 1.5M QPS
   traffic:      100B events → request-time scoring at ~30K QPS average, peak ~80K QPS
   freshness:    user features:        < 5 min
                 ad features:          < 5 min
                 context features:     < 1 min (e.g., time of day, device class)
                 model weight:         retrain hourly
   latency:      p99 < 50ms end-to-end (request → response)
   precision:    AUC > 0.85 on the eval set
   ACL:          per-advertiser, ad visibility, brand-safety filters
   cost:         < $500k/mo for serving + features + training
   failure mode: silent accuracy drop (more impressions, fewer clicks, revenue falls)
```

The clarifying questions you ask:

1. "Is this a per-impression auction, or a feed ranker?" (Affects whether you need a heavy model in the path.)
2. "Are we optimising CTR or conversion?" (Conversion delays 30 days; CTR is same-session.)
3. "What's the freshness budget on user features — minutes, hours?"
4. "Are there brand-safety / advertiser filters (e.g., never show alcohol to minors)?"
5. "Multi-region, or single?"

### Step 2 — SKETCH (10 min)

15 boxes, each with a one-line role:

```
   USER REQUEST
        │
        ▼
   [CDN / Edge]   geo-routing, basic cache for repeat requests
        │
        ▼
   [Auction Service]   selects ad candidate from inventory, runs bid logic
        │
        ▼
   [Ad Candidate Gen]   top-100 ads given user (from retrieval index)
        │
        ▼
   [Feature Fetch]   online store, < 5ms
        │              fetches user features + ad features + context features
        ▼
   [Light Ranker]   GBDT, top-100 → top-20
        │
        ▼
   [Heavy Ranker (DNN)]   GPU-served, top-20 → top-5
        │
        ▼
   [Bid / Price]   second-price auction, reserve price
        │
        ▼
   [Response]   bid + ad creative + click URL
        │
        ▼
   [Impression Logged]   Kafka, downstream

   ──── offline paths ────
   [Click Stream Kafka] → [Flink Streaming Features]
                                      │
                                      ├──► [Online Store (Redis)]
                                      └──► [Offline Store (Iceberg)]

   [Hourly Trainer]   Spark + PyTorch
        │
        ▼
   [Model Registry]   MLflow
        │
        ▼
   [Online Ranker Service]
```

**Total: 15 boxes. Each has a role. Numbers next to each latency budget.**

### Step 3 — DEEP-DIVE (15 min)

Pick the 3 boxes that decide the outcome.

#### Box A: Heavy Ranker (DNN)

```
   Latency budget: 20ms (5 candidates × 1 forward pass each, batched)

   Model: DNN on user embedding × ad embedding → P(click)
     user_tower: user_id → history features → DNN → 256-d
     ad_tower:   ad_id → content features → DNN → 256-d
     context:    time, device, location → DNN → 64-d
     concat → MLP → 256 → 128 → 1 → sigmoid

   Served on GPU (A10G, 4× GPUs):
     - Batched inference: collect 20ms of requests, batch them
     - Effective throughput: 50K QPS / 4 GPUs ≈ 12K QPS per GPU
     - p99 batch latency: 15-20ms

   Fallback: if GPU unavailable, CPU GBDT (slightly worse quality)
```

#### Box B: Feature fetch (online)

```
   Latency budget: 5-15ms

   Per request, fetch:
     - 50 user features (clicks_30d, last_5_categories, etc.)
     - 20 ad features (ctr_7d, ctr_30d, advertiser_id, etc.)
     - 10 context features (time_of_day, device, geo, page_category)
     = ~80 features total

   Storage: Redis cluster, key = entity_id
     mget 80 keys per request → ~5-10ms

   Hot key handling: if user_id is a top-1% high-traffic user, the
     Redis shard for that user becomes hot. Use read-replicas + jitter.

   Single-tenant vs multi-tenant: per-tenant key prefixes for ACL.
```

#### Box C: Ad candidate generation (the funnel)

```
   Latency budget: 15ms

   Three sources:
     1. ANN search:    user_embedding × ad_embedding via two-tower
                       top-500 candidates, p95 < 20ms (Faiss / ScaNN)
     2. Co-occurrence: "users like you also saw"
                       top-200 from precomputed matrix
     3. Trending:      top-100 trending ads by region

   Combined: 800 candidates, ACL-filtered (skip restricted categories
              for this user), deduped → 100 → light ranker
```

### Step 4 — TRADEOFFS (5 min)

| Choice | Alt | Why this | Revisit if |
|---|---|---|---|
| **GPU DNN serving (heavy ranker)** | CPU-only ranker (e.g., single XGBoost) | Latency at p99 < 50ms requires GPU | GPU util < 30%, cost > $200k/mo |
| **Two-tower ANN candidate gen** | Co-occurrence only | Catches novel ads; co-occurrence alone is stale | ANN recall < 80% on offline eval |
| **Redis online store** | DynamoDB | Redis is faster; latency budget is tight | ops complexity > benefit |
| **Hourly model retrain** | Daily | CTR shifts within hours (news, sports, daypart) | drift > 1 day detectable vs hourly |
| **Edge-cache top results** | Always compute | Common ad/user pairs avoid 50ms entirely | cache freshness < 5 min acceptable |
| **Single global model** | Per-region models | Geo-compliance not required here | cross-region privacy law appears |

### Step 5 — SUMMARY (3 min)

```
   Decision:
   - Two-tower ANN candidate gen (top-500) + co-occurrence (top-200) +
     trending (top-100), deduped + ACL-filtered, → 100 candidates
   - Light GBDT ranker on CPU: 100 → 20
   - Heavy DNN ranker on GPU (batched): 20 → 5
   - Bid computation: second-price auction
   - Online features from Redis (mget 80 keys, 5-10ms)
   - Streaming feature update (Flink → Redis) every 5 min
   - Hourly retrain on PyTorch + Spark
   - Eval-driven deployment (shadow → canary → 100%)

   Cost (rough):
   - GPU serving (4× A10G, ~50K QPS batched):  ~$80k/mo
   - Redis cluster (100M user keys + 100M ad keys): ~$15k/mo
   - ANN index (Pinecone / ScaNN, 100M ads):     ~$10k/mo
   - Kafka + Flink (100B events/day streaming):   ~$60k/mo
   - Offline training (hourly, GPU spot):         ~$40k/mo
   - Eval + monitoring:                           ~$5k/mo
   - ──────────────────────────────────────────
   - Total:                                       ~$210k/mo

   Revisit if:
   - p99 > 50ms              → reduce candidates, smaller model, more batching
   - AUC < 0.85              → bigger embedding, more features, longer training
   - Cost > $500k/mo         → smaller DNN, fewer GPUs, cache more
   - Brand-safety breach      → tighter filter, audit creative uploads
   - Drift detected in hours → more frequent retrain
```

### The five things that distinguish a senior answer from a junior answer

1. **You wrote numbers everywhere.** "200M users, 100M ads, 50K QPS, p99 < 50ms." Not "lots of users, many ads, fast."
2. **You spent time on the boxes that decide the outcome** (heavy ranker, feature fetch, candidate gen) and **drew-but-didn't-over-explain** the boxes that don't (CDN, bidding).
3. **You stated alternatives** for every major choice. "GPU over CPU because..." not "we use GPU."
4. **You addressed monitoring and failure modes** explicitly (drift, brand-safety, hot keys).
5. **You committed to a decision** and said what would change your mind.

The 38-minute version of this answer is the difference between a hire at L5 and a hire at L6 (staff/principal). The framework is the structure that lets you allocate the time correctly.

---

## What Comes Next

> Lesson 2 — **Recommendation Pipeline** — full worked design at billion-scale. Follow the framework end-to-end.