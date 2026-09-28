# Lesson 2 — Recommendation Pipeline

> **Type:** Article · Module 8 · AI DE System Design
> End-to-end recommendation system at billion-scale. A worked design.

---

## The problem

> Design a personalised "for you" feed for 200M daily active users, 1B items, 100k QPS at p95 < 100ms. Freshness: new items within 5 minutes. Cold start: handle brand-new users with zero history. Multi-tenant (separate feeds per region).

This is a classic interview question. Use the 5-step framework.

---

## Step 1 — CLARIFY

```
   users:        200M DAU, multi-region (NA / EU / APAC)
   items:        1B (videos, products, posts, ...)
   interactions: 10B events/day
   QPS:          100k peak (recommendation requests / sec)
   freshness:    new items visible in 5 min
                 interaction feedback in 5 min
   latency:      p95 < 100ms
   cold start:   brand-new users (no history) → popular / global fallback
   ACL:          per-region feed (geo-restricted content)
   cost:         < $500k/mo for serving + offline
   failure mode: bad recommendations (silent, user leaves)
                 data leak across regions
```

---

## Step 2 — SKETCH

```
   ┌──────────────────────────────────────────────────────────────┐
   │                                                              │
   │   USER REQUEST                                               │
   │        │                                                     │
   │        ▼                                                     │
   │   [API Gateway / CDN]   ◄──── geo-routing                    │
   │        │                                                     │
   │        ▼                                                     │
   │   [Candidate Generation]   ◄──── 1000 candidates per user   │
   │        │                                                     │
   │        ▼                                                     │
   │   [Light Ranker]           ◄──── filter to 100               │
   │        │                                                     │
   │        ▼                                                     │
   │   [Heavy Ranker (DNN)]     ◄──── filter to 30                │
   │        │                                                     │
   │        ▼                                                     │
   │   [Blender / Re-ranker]    ◄──── diversity, freshness        │
   │        │                                                     │
   │        ▼                                                     │
   │   [RESPONSE]                                                │
   │                                                              │
   │   ──── offline paths ────                                   │
   │                                                              │
   │   [Events Kafka] ─► [Spark / Flink] ─► [Feature Store]      │
   │                                       (offline + online)   │
   │                                                              │
   │   [Items DB] ──► [Two-Tower Embedding] ─► [ANN Index]       │
   │                                                              │
   │   [Train: PyTorch / Spark ML] ─► [Model Registry]           │
   │        │                                                     │
   │        ▼                                                     │
   │   [Online Ranker Service]                                 │
   │                                                              │
   │   ──── operations ────                                      │
   │                                                              │
   │   [Eval Harness]   [Drift / Quality Monitoring]             │
   │   [Cost Dashboard] [PII / ACL Audit]                        │
   └──────────────────────────────────────────────────────────────┘
```

12–15 boxes. Each has a role.

---

## Step 3 — DEEP-DIVE

### Box 1: Candidate generation (the funnel)

Three sources of candidates:

```
   CANDIDATE POOLS
   ───────────────
   1. ANN search over user embedding × item embedding (two-tower)
      - top-500 from 1B items
      - p95 < 20ms (Faiss / ScaNN / Pinecone)

   2. Co-occurrence / item-CF
      - "users who liked X also liked Y"
      - top-200 from precomputed matrix

   3. Trending / popularity / regional
      - top-200 per region
      - fallback for cold-start users

   Combined: ~1000 candidates, deduped, ACL-filtered
```

The **two-tower model** is the workhorse: encode user and item as vectors, dot-product similarity, ANN search. Train on (user, item, label=interacted).

```
   USER TOWER                  ITEM TOWER
   ──────────                  ─────────
   user_id ──►                 item_id ──►
   history ──► DNN ──► 256-d   metadata ──► DNN ──► 256-d
   features                     features
        │                            │
        └─────── DOT PRODUCT ────────┘
                     score
```

### Box 2: Feature store (online + offline parity)

For real-time personalisation, features must be **online and < 50ms p95**:

```
   ONLINE FEATURES (Redis / DynamoDB)
   ──────────────────────────────────
   user_features: age, region, last_active
   user_history_last_30d: list of item_ids watched
   user_affinities: category preference scores
   contextual: time_of_day, device, locale

   ONLINE LATENCY: 5–20ms (mget + parse)
```

Without a feature store, you can't do per-user real-time personalisation. This is the moat.

### Box 3: Heavy ranker (DNN)

The deep ranker takes the 100 candidates from the light ranker and scores them with a full feature set.

```python
# Simplified DNN ranker
class Ranker(torch.nn.Module):
    def __init__(self, num_features):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(num_features, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 1),  # score
        )

    def forward(self, user_features, item_features, context):
        x = torch.cat([user_features, item_features, context], dim=-1)
        return self.net(x)
```

Trained on **interactions** with **delayed labels** (clicks → 5 min, watch-time → minutes, conversion → days).

Serving:
- Model served on GPUs (A10G / T4) or specialised accelerators
- 100 candidates × 1 user = 100 forward passes per request
- Use **batched serving** to amortise GPU cost
- p95 < 30ms with batching

### Box 4: Cold start

```
   COLD START
   ──────────
   - Brand-new user (no history)
     → use trending + geo + demographic priors

   - New item (no interactions)
     → use item embedding (from content) + co-occurrence
     → boost in candidate pool for first 24h

   - New region
     → start with global trending, train local model
       after enough data
```

Cold start is solved by **multi-armed bandit / explore-exploit** during the first interactions.

---

## Step 4 — TRADEOFFS

| Choice | Alternative | Why | Revisit if |
|---|---|---|---|
| **Two-tower + ANN** | GraphSAGE / item-CF only | Two-tower captures both sides, scales to 1B | ANN quality insufficient (recall@100 < 80%) |
| **Managed ANN (Pinecone / ScaNN)** | Self-hosted Faiss | Ops simplicity; cost acceptable at 100k QPS | cost > $100k/mo OR latency SLA breach |
| **Online feature store (Redis)** | Compute features at request time | Sub-50ms requirement | staleness tolerable at hour-level |
| **GPU ranker serving** | CPU ranker | Better throughput per node | GPU utilisation < 30% (downsize) |
| **Daily training** | Continuous training | Faster iteration; simpler MLOps | drift detected within hours |
| **Multi-region with replicated models** | Single global model | Geo-compliance, lower cross-region latency | traffic patterns change |

---

## Step 5 — SUMMARY

**Decision:**
- Two-tower candidate gen (ANN, top-500) + co-occurrence (top-200) + trending (top-200) → 1000 candidates
- Light ranker (linear / GBDT) → 100
- Heavy ranker (DNN on GPU) → 30
- Blender applies diversity, freshness, ACL → final response
- Online features from feature store, offline training on PySpark
- Daily model retrain, nightly feature recompute, 5-min interaction freshness

**Cost (rough):**
- ANN index serving: ~$30k/mo (Pinecone / ScaNN)
- Online feature store: ~$10k/mo (Redis cluster)
- GPU ranker: ~$50k/mo (10× A10G)
- Kafka + Flink ingest: ~$30k/mo
- Offline training: ~$20k/mo
- **Total: ~$140k/mo for 100k QPS**

**Revisit if:**
- p95 > 100ms → cache, smaller model, reduce candidates
- Cost > $500k/mo → smaller model, self-host ANN, fewer GPUs
- Cold start quality bad → more explore, better priors
- Drift detected → retrain more often, faster feedback

---

## The "metrics that matter" dashboard

| Metric | Why |
|---|---|
| **Engagement rate** | CTR, watch-time, conversion |
| **Coverage** | % of catalog being recommended (avoid popularity bias) |
| **Diversity** | Intra-list similarity (lower = more diverse) |
| **Freshness** | % of recommendations < 5 min old |
| **Latency p95** | < 100ms SLA |
| **Cost per 1k requests** | trending over time |
| **Per-region ACL compliance** | 0 leaks |

---

## What Comes Next

> Lesson 3 — **Enterprise RAG** — multi-tenant RAG with ACL, hybrid search, citations, and eval at 100M-chunk scale.