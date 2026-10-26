# Meta L6 Onsite Mock - Round 3: Sr Tech Design (60 mins)

**Role:** L6 AI-Native Data Engineer (Full Stack) - Meta
**Format:** System design deep dive
**Problem:** PYMK (People You May Know) + Time-Travel + Bounded Fanout
**Goal:** Design a 1B-user scale "People You May Know" recommendation system that supports time-travel queries, with bounded fanout for candidate generation, and a feedback/eval loop for quality.

---

## Round Structure

| Section | Time | Focus |
|---------|------|-------|
| Clarify & Scope | 5 min | Ask 5-7 questions, find the real problem |
| High-Level Design | 10 min | Components, data flow, APIs |
| Deep Dive #1: Bounded Fanout | 15 min | Candidate generation at scale |
| Deep Dive #2: Time-Travel | 15 min | Point-in-time correctness, freshness |
| Deep Dive #3: Eval + Feedback | 10 min | Recall@K, groundedness, online metrics |
| Wrap & Tradeoffs | 5 min | What you'd build next, monitoring |

**L6 Bar:** You drive the conversation, name the metrics, make tradeoffs explicit, leave a system behind (not just an algorithm).

---

## Section 1: Clarify & Scope (5 min)

**Ask these questions FIRST - L6 signal:**

> "Before I design, I want to make sure I solve the right problem. A few questions:
>
> 1. **Scale & latency SLO:** How many MAU? What's the p99 latency budget for the PYMK endpoint - 100ms, 200ms, 500ms? Is this on the home feed or a dedicated page?
>
> 2. **Definition of 'good':** Are we measuring click-through-rate, friend-accept-rate, long-term retention, or all three? Do we have a gold-standard eval set from past accepts?
>
> 3. **Cold start:** What about new users with 0 friends and 0 interactions - is this in scope? Bot/celebrity accounts excluded?
>
> 4. **Time-travel:** Do you mean (a) replay queries against historical snapshots for offline eval, (b) backfill features as-of a date to prevent leakage, or (c) debug why a recommendation appeared at T-1? My guess is all three.
>
> 5. **Constraints:** Graph size, fanout budget per user, privacy rules (no PII in joins), can we use precomputed embeddings?
>
> 6. **Online vs offline:** Is this a batch pipeline that runs nightly + online serving layer, or pure online retrieval?"

**What you're really doing:** Showing that you don't jump to a graph DB or Neo4j solution. You define SLOs, metrics, edge cases, and time-travel semantics first. L6 = "define the problem before the solution."

---

## Section 2: High-Level Design (10 min)

**Draw this on the whiteboard:**

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PYMK System                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [Offline / Nightly]              [Online / Realtime]               │
│                                                                     │
│  ┌──────────────┐                 ┌──────────────────┐              │
│  │ Graph Builder│                 │ PYMK Service     │              │
│  │ (Spark/Flink)│                 │ (C++/Java)       │              │
│  └──────┬───────┘                 └────────┬─────────┘              │
│         │                                  │                        │
│         ▼                                  ▼                        │
│  ┌──────────────┐                 ┌──────────────────┐              │
│  │ Feature Store│◄───time-travel──│ Feature Lookup   │              │
│  │ (SCD2/PDT)   │                 │ (Point-in-time)  │              │
│  └──────┬───────┘                 └────────┬─────────┘              │
│         │                                  │                        │
│         ▼                                  ▼                        │
│  ┌──────────────┐                 ┌──────────────────┐              │
│  │ Candidate    │──precomputed───►│ Candidate        │              │
│  │ Generator    │   candidate     │ Retrieval (Top-K)│              │
│  │ (Bounded     │   sets          │                  │              │
│  │  Fanout)     │                 └────────┬─────────┘              │
│  └──────┬───────┘                          │                        │
│         │                                  ▼                        │
│         ▼                          ┌──────────────────┐              │
│  ┌──────────────┐                  │ Ranker (LightGBM│              │
│  │ Eval Harness │                  │ or 2-tower NN)   │              │
│  │ (Recall@K,   │                  └────────┬─────────┘              │
│  │  nDCG, AUC)  │                           │                       │
│  └──────┬───────┘                           ▼                       │
│         │                          ┌──────────────────┐              │
│         └───────feedback loop─────►│ PYMK API         │              │
│                                    │ (gRPC/HTTP)      │              │
│                                    └────────┬─────────┘              │
│                                             │                        │
│                                             ▼                        │
│                                    ┌──────────────────┐              │
│                                    │ Client (Home     │              │
│                                    │ Feed)            │              │
│                                    └──────────────────┘              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Components (name them with scale):**

1. **Graph Storage (TAO or custom MyRocks):** Social graph, ~1B users, ~200B edges (friend + interactions). Read-heavy, point lookups by user_id.
2. **Feature Store (SCD2 with PDT - Point-in-Devices-Tables):** Per-user features as-of a timestamp. Solves time-travel for offline training.
3. **Candidate Generator (Bounded Fanout):** Pre-computed candidate sets per user, stored in TAO. Top 500 candidates per user, refreshed daily.
4. **Online Ranker:** Lightweight model (logistic regression or shallow NN) that scores candidates using current features. p99 <50ms.
5. **Eval Harness:** Offline Recall@K, online A/B on accept-rate, long-term retention.
6. **Feedback Loop:** User accepts/declines -> labels for retraining.

**Data flow (name QPS):**

- Online: 1B MAU, each opens app 8x/day = 8B PYMK fetches/day = ~100K QPS average, ~500K QPS peak.
- Each PYMK fetch: read 500 candidate IDs, score, return top 20. That's 500 reads + 20 writes (logs) per request.
- Feature lookups: 5-10 per request, must be <5ms each (Memcache/TAO).

**APIs (write them out):**

```protobuf
service PYMKService {
  rpc GetPYMK(PYMKRequest) returns (PYMKResponse);
  rpc LogFeedback(PYMKFeedback) returns (Ack);
  rpc EvalCandidateSet(EvalRequest) returns (EvalResponse);  // time-travel
}

message PYMKRequest {
  int64 user_id = 1;
  int32 limit = 2;             // default 20
  int64 as_of_timestamp = 3;   // for time-travel debug
  string request_id = 4;
}

message PYMKResponse {
  repeated Candidate candidates = 1;
  string model_version = 2;
  string feature_version = 3;
}

message Candidate {
  int64 user_id = 1;
  float score = 2;
  string reason_code = 3;  // "mutual_friend", "co_workspace", "contact_import"
}
```

**L6 Bar:** You wrote actual API contracts, named QPS, distinguished offline/online, and explained the feedback loop. Not just "use a graph DB and ML."

---

## Section 3: Deep Dive #1 - Bounded Fanout (15 min)

**The core problem:** For each user, find their Top-K friends-of-friends. Naive = O(degree^2) = O(5000^2) = 25M hops per user = doesn't scale.

**Naive approach (DON'T do this):**
```
for each friend f of u:
  for each friend ff of f:
    add (u, ff) to candidate set
```
This is O(deg(u) * avg_deg) = 5K * 5K = 25M ops per user. With 1B users, that's 2.5e16 ops. Won't finish in 24h on 10K machines.

**Bounded Fanout - 3 levels of optimization:**

### Level 1: Random walk with restart (Apache Giraph / Spark GraphX)

```
For each user u:
  Start at u, walk 2-3 hops, sample edges with prob 0.15 (decay).
  Collect visited nodes, score by visit count.
```

**Problem:** Stochastic, hard to bound compute. Could miss top candidates.

### Level 2: Pre-compute friend-of-friend (FoF) with capping (Meta's TAO approach)

```
For each user u:
  candidates = {}
  for each friend f of u (capped at 500):
    for each friend ff of f (capped at 500):
      if ff != u and ff not already friend with u:
        candidates[ff] += 1
  return top-K candidates
```

**Cap = bounded fanout.** Each user reads at most 500 friends * 500 friends-of-friends = 250K candidate edges. Still expensive at 1B scale, but doable in nightly Spark job (4-6 hours on 5K machines).

### Level 3: Per-edge-type weighting + early termination

```
For each user u:
  candidates = min_heap(top-K=500)
  for each friend f of u (sorted by edge_weight DESC, capped at 500):
    for each friend ff of f (sorted by edge_weight DESC, capped at 500):
      score = edge_weight(u,f) * edge_weight(f,ff) * type_boost
      if score > heap_min or heap.size < K:
        candidates.push(ff, score)
        if heap.size > K: pop min
  return top-K
```

**Why this wins:**
- 500 * 500 = 250K per user, but early termination cuts ~50% in practice.
- Total: 1B users * 250K = 2.5e14 ops. At 1M ops/sec/machine = 250K machine-seconds = ~70 machine-hours per shard.
- With 1000-way parallelism: 4 minutes. Realistic at Meta scale.

**Storage:** Store in TAO (The Associations and Objects) - Meta's distributed data store. Key: `user_id`, value: list of 500 candidate IDs + scores + reasons.

**Update strategy:**
- Incremental update on friend-add: only recompute for u and the new friend's first-degree neighbors (~1000 users affected).
- Full recompute nightly for stale users (no activity in 7 days).

**L6 Bar:** You computed the math (1B * 250K = 2.5e14 ops), gave a parallel-machine estimate, named the storage (TAO), and explained incremental vs full recompute.

---

## Section 4: Deep Dive #2 - Time-Travel (15 min)

**The problem:** Three different needs, all called "time-travel":

### Need 1: Offline training with point-in-time correctness

**Problem:** If you're training a ranker, you must NOT leak future info. E.g., if user accepted friend X on day 30, features at day 25 must not include X.

**Solution: SCD2 (Slowly Changing Dimension Type 2) feature store**

```sql
CREATE TABLE user_features_scd2 (
  user_id BIGINT,
  feature_name STRING,
  feature_value STRING,
  valid_from TIMESTAMP,
  valid_to TIMESTAMP,  -- NULL = current
  PRIMARY KEY (user_id, feature_name, valid_from)
) PARTITIONED BY (valid_from);

-- Query features as-of day D
SELECT * FROM user_features_scd2
WHERE user_id = 123
  AND valid_from <= '2024-01-15'
  AND (valid_to > '2024-01-15' OR valid_to IS NULL);
```

**Why this works:** Each row is immutable once written. As-of queries use range scan. For 1B users * 100 features = 100B rows. Compress by storing JSON blob per (user_id, valid_from).

### Need 2: Debug "why did PYMK show X on day D?"

**Problem:** User reports a bad recommendation. You need to replay the exact candidate set, ranker, and features from day D.

**Solution: Immutable logs + snapshot IDs**

```
Every PYMK response includes:
  - model_version: "ranker_v123"
  - feature_snapshot_id: "fs_2024_01_15_0300"
  - candidate_set_id: "cand_2024_01_14_nightly"
  - as_of_timestamp: <request timestamp>
```

To replay: load the exact (model, features, candidates) by version, rerun on the same user_id, get identical output.

### Need 3: Backfill features after schema change

**Problem:** You add a new feature `mutual_friend_count_30d`. You need to backfill for all users as-of historical dates.

**Solution: Reprocessing pipeline with point-in-time join**

```python
# Spark job: backfill new feature for last 90 days
for day in range(90):
  # Read graph edges as-of day
  edges = spark.read.parquet(f"s3://graph/snapshot_{day}")
  # Compute feature per (user, day)
  features = edges.groupBy("user_id").agg(...)
  # Write to feature store with valid_from = day
  features.write.mode("append").saveAsTable("user_features_scd2")
```

**Key insight:** Time-travel is not one thing. It's three problems with three different storage patterns:
1. **Training:** SCD2 with as-of queries (PDT pattern).
2. **Debug:** Versioned models + versioned features + immutable logs.
3. **Backfill:** Reprocessing with point-in-time joins.

**L6 Bar:** You distinguished 3 use cases, gave SQL/schema, explained the "why" for each.

---

## Section 5: Deep Dive #3 - Eval + Feedback (10 min)

**The question interviewer will ask:** "How do you know PYMK is good?"

### Three-layer eval:

**Layer 1: Offline (Recall@K, nDCG@K, MAP@K)**

```python
# Gold set = past friend-accepts
# For each user, compare PYMK top-K vs gold set
recall_at_20 = mean([len(gold & predicted[:20]) / len(gold) for u in users])
ndcg_at_20 = mean([ndcg(gold, predicted[:20]) for u in users])

# Time-travel: evaluate at day D using features as-of D
# Critical: no future leakage
```

**Layer 2: Online A/B (accept-rate, long-term retention)**

```
Variant A: control (current ranker)
Variant B: new ranker with new feature
Metric: friend_accept_rate_7d, sessions_30d
Decision: ship if B > A with p<0.05 AND no regression on diversity/latency
```

**Layer 3: Counterfactual (IPS - Inverse Propensity Scoring)**

If you want to know "would users have liked this candidate even if it wasn't shown?", use IPS to debias logged data.

```
ips_estimate = mean(reward * shown / propensity_score)
```

### Feedback loop:

```
User sees PYMK -> clicks/ignores/accepts -> log to ClickHouse
  -> daily Spark job: build gold set = (user, accepted_candidate, timestamp)
  -> weekly: retrain ranker on gold set with point-in-time features
  -> shadow deploy new ranker, dual-score 1% traffic, compare offline metrics
  -> ship if Recall@20 improves AND no regression on online A/B
```

**Key metrics to track in dashboard:**
- Recall@20 (offline)
- Friend-accept-rate-7d (online, primary)
- Diversity (entropy of friend graph neighborhood - prevent echo chambers)
- Latency p50/p95/p99
- Candidate-set coverage (% of accepted friends that were in candidate set)

**L6 Bar:** You named 3 eval layers with concrete formulas, explained IPS briefly, drew the feedback loop with all stages.

---

## Section 6: Wrap & Tradeoffs (5 min)

**Interviewer will ask:** "What would you build next / what did you skip?"

**Your answer:**

> "Three things I deliberately scoped out:
>
> 1. **Graph Neural Network (GNN) ranker:** GNNs like GraphSAGE would catch multi-hop signals but add 50ms to p99 and are hard to debug. I went with engineered features + LightGBM for v1. Could revisit with distilled GNN if offline Recall plateaus.
>
> 2. **Real-time candidate generation:** I went with nightly + incremental. True real-time (e.g., within 1 minute of friend-add) costs 10x compute and needs a streaming graph store. Not worth it for PYMK - friend-add events are sparse per user.
>
> 3. **Privacy / federated learning:** Edge-side candidate generation for privacy-sensitive users. Out of scope for v1, but design should leave room - keep feature store server-side but allow client-side rerank with on-device embeddings.
>
> **What I'd build next:** Diversity constraint in the ranker. Right now I optimize for accept-rate, which can create echo chambers. I'd add a constraint that top-20 has at least 3 from different social clusters (e.g., workplace, school, mutual friends), measured by graph conductance."

**L6 Bar:** You named what you cut and why, and proposed a next-step that shows you think about second-order effects (echo chambers, diversity).

---

## Scoring Checklist

### Clarify (5m)
- [ ] Asked about SLO, scale, edge cases, time-travel definition
- [ ] Did NOT jump to "use Neo4j" or "use a graph database"

### High-Level (10m)
- [ ] Drew components with names (TAO, feature store, ranker)
- [ ] Named QPS: 100K avg, 500K peak
- [ ] Wrote API contract (protobuf or similar)
- [ ] Distinguish offline vs online

### Bounded Fanout (15m)
- [ ] Computed the math (1B * 250K = 2.5e14 ops)
- [ ] Named the cap (500 friends * 500 FoF = 250K)
- [ ] Explained early termination + scoring
- [ ] Named storage (TAO)
- [ ] Incremental vs full recompute

### Time-Travel (15m)
- [ ] Distinguished 3 needs: training, debug, backfill
- [ ] SCD2 schema with SQL
- [ ] Versioned models/features for replay
- [ ] Reprocessing with point-in-time joins

### Eval (10m)
- [ ] 3 layers: offline, online A/B, counterfactual (IPS)
- [ ] Named metrics: Recall@20, accept-rate, diversity
- [ ] Drew feedback loop

### Wrap (5m)
- [ ] Named what you cut and why
- [ ] Proposed diversity / echo-chamber next step

---

## Red Flags (What fails L6)

- "Use Neo4j" without computing scale
- "Just use a graph database" - shows no DE depth
- "Time-travel means versioned data" - too vague, didn't distinguish 3 use cases
- "We can evaluate by looking at CTR" - no Recall@K, no point-in-time correctness
- "I'll use GNN" - jumps to ML without engineered features first
- No SLO, no QPS, no concrete numbers

---

## Phrases That Score L6

- "1B users * 250K fanout = 2.5e14 ops, parallelizable to 4 mins on 1000 machines"
- "Time-travel is three different problems: training, debug, backfill"
- "I'd cut GNN for v1, ship LightGBM with engineered features, revisit if Recall plateaus"
- "Bounded fanout caps at 500*500 = 250K per user, with early termination at top-K"
- "SCD2 with as-of queries solves point-in-time without leakage"

---

## Up Next: Round 4 - Coding (45 mins)

Standard L6 coding: LRU cache, distributed mutex, or system-level "design a rate limiter." Expect follow-ups on concurrency, failure modes, and test design.

Ready when you are.
