# LOOP 8: Personalization + Multi-tenant + 500M Users

**Theme:** Personalized search at scale, no filter bubble, no cross-tenant leak
**Total Duration:** 2 hours (compressed)
**Difficulty:** Hard (multi-tenant is L7 territory)

---

## Architecture Diagram (Master)

```
┌────────────────────────────────────────────────────────────────────┐
│  PERSONALIZED WORKPLACE SEARCH - 500M USERS, MULTI-TENANT          │
└────────────────────────────────────────────────────────────────────┘

USER SIGNAL COLLECTION
──────────────────────

User Query ─▶ Click ─▶ Search ─▶ Read ─▶ Share
   │             │        │         │        │
   ▼             ▼        ▼         ▼        ▼
┌──────────────────────────────────────────────────┐
│ user_history (Flink aggregation)                 │
│ - last 90 days                                  │
│ - (query, clicked_doc_id, dwell_ms, rating)     │
└──────────────────┬───────────────────────────────┘
                   │ Nightly batch
                   ▼
┌──────────────────────────────────────────────────┐
│ user_embedding (computed nightly)                │
│ = avg(clicked_doc_embeddings) * recency_decay   │
│ Stored in user_preferences table + Qdrant        │
└──────────────────────────────────────────────────┘

QUERY PATH (with personalization)
─────────────────────────────────

User query "How do I deploy a service?"
   │
   ▼
┌────────────────────────────────┐
│ Embed query                     │
└─────────────┬──────────────────┘
              │
              ▼
┌──────────────────────────────────────────────┐
│ Qdrant hybrid search                         │
│ ────────────────────────────────────────────│
│ Filter 1: tenant_id = user.tenant_id         │ ◀── TENANT ISOLATION
│ Filter 2: team_id IN user.teams             │ ◀── ACL
│ Top 100 candidates                          │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌──────────────────────────────────────────────┐
│ Personalized Rerank                         │
│ ────────────────────────────────────────────│
│ For each candidate:                         │
│   score = base_sim(query, doc)              │
│         + 0.3 * user_sim(user_emb, doc)     │ ◀── PERSONALIZATION
│         + 0.1 * recency_weight              │
│         + diversity_penalty (anti-bubble)    │
│ Top 20                                      │
└─────────────┬──────────────────────────────┘
              │
              ▼
┌──────────────────────────────────────────────┐
│ LLM with personalized context               │
└─────────────┬──────────────────────────────┘
              │
              ▼
       Grounded answer

MULTI-TENANT SHARDING
─────────────────────
- 50 logical tenants
- 100 physical shards
- Routing: shard = hash(tenant_id) % 100
- Per-tenant rate limit
- Per-tenant cost dashboard
- Audit cross-tenant access attempts
```

---

## Greet (10 min - compressed)

### Q1: How do you personalize RAG?

**L6 Answer (60 sec):**

> "Three signals stacked together:
>
> 1. **User history embedding** — build a user vector from last 90 days of clicked docs, with exponential decay (recent clicks weighted higher). Updated nightly.
>
> 2. **Team context filter** — narrow to the user's team's docs first. This is personalization at the corporate level.
>
> 3. **Time-of-day and recency** — morning = work docs, evening = personal. Plus recency boost for docs updated in last 7 days.
>
> Combine via rerank formula: `score = base_sim + 0.3 * user_sim + 0.1 * recency_weight + diversity_penalty`. The 0.3 weight on user_sim is critical — too high creates filter bubbles.
>
> **Anti-bubble:** I added a diversity constraint. Top 20 must have at least 3 different 'clusters' (workplace, school, mutual friends). Measured by graph conductance."

**L6 Keywords:** user history embedding, decay weight, rerank formula, anti-bubble diversity.

---

### Q2: How do you handle multi-tenant?

**L6 Answer (60 sec):**

> "Hard isolation at every layer:
>
> 1. **Qdrant payload:** every point has `tenant_id`. Filter at the storage layer with `WHERE tenant_id = user_tenant`.
>
> 2. **Sharding:** 100 physical shards, `hash(tenant_id) % 100` for routing. Logical tenants share shards but never cross.
>
> 3. **Per-tenant rate limits:** 1000 RPS for premium tenants, 100 RPS for free.
>
> 4. **Per-tenant cost dashboard** so finance can bill accurately.
>
> 5. **Cross-tenant audit log** — every access that touches a non-user tenant is logged + alerted. This catches bugs early.
>
> **No joins across tenants. No shared caches. No shared embeddings.**"

---

## AI-Native DE Full Stack (40 min - compressed)

### Q1 Data Model (10 min)

```
┌────────────────────────────────────────────────────────────┐
│          PERSONALIZATION + MULTI-TENANT MODEL              │
└────────────────────────────────────────────────────────────┘

users                          user_preferences
┌────────────────────────┐     ┌────────────────────────────┐
│ user_id         PK     │◀───▶│ user_id        PK FK       │
│ tenant_id               │     │ user_embedding VECTOR      │
│ team_id                 │     │ preferred_collections AR   │
│ email                   │     │ preferred_languages   AR   │
│ created_at              │     │ click_history_count INT    │
└────────────────────────┘     │ updated_at TIMESTAMP       │
                               └────────────────────────────┘

user_history                    tenants
┌────────────────────────┐     ┌────────────────────────────┐
│ user_id                │     │ tenant_id       PK         │
│ query          TEXT    │     │ name                      │
│ clicked_doc_id  BIGINT │     │ shard_strategy            │
│ dwell_ms        INT    │     │ rate_limit_rps INT        │
│ feedback_rating        │     │ monthly_cost_quota $FLOAT │
│ timestamp              │     │ created_at                │
└────────────────────────┘     └────────────────────────────┘
  PARTITIONED BY (DATE(timestamp))
```

**SQL:**

```sql
CREATE TABLE user_preferences (
  user_id               BIGINT PRIMARY KEY,
  user_embedding        ARRAY<FLOAT>,    -- 1536-dim for ada
  preferred_collections ARRAY<STRING>,
  preferred_languages   ARRAY<STRING>,
  click_history_count   INT,
  updated_at            TIMESTAMP
);

CREATE TABLE user_history (
  user_id         BIGINT,
  query           STRING,
  clicked_doc_id  BIGINT,
  dwell_ms        INT,
  feedback_rating STRING,
  `timestamp`     TIMESTAMP
) PARTITIONED BY (DATE(`timestamp`));
```

---

### Q2 Pipeline (10 min)

```
┌──────────────────────────────────────────────────────────┐
│          PERSONALIZATION PIPELINE (nightly)              │
└──────────────────────────────────────────────────────────┘

User clicks during the day
        │
        ▼
┌────────────────────────────┐
│ Flink aggregation          │
│ (per user_id, per doc)     │
│ - click count             │
│ - total dwell time        │
│ - avg rating              │
└─────────────┬──────────────┘
              │
              ▼
┌────────────────────────────┐
│ Spark: build user_embedding│
│ ─────────────────────────│
│ For each user:            │
│   1. Get last 90d clicked │
│      docs                 │
│   2. Get each doc's emb   │
│   3. Weighted avg:        │
│      weight = exp(-age_d) │
│        * dwell_ms         │
│        * rating           │
│   4. Normalize            │
│   5. Write user_preferences│
└─────────────┬──────────────┘
              │
              ▼
┌────────────────────────────┐
│ Qdrant: re-index doc emb   │
│ with user_overlap payload │
└────────────────────────────┘

QUERY (with personalization)
────────────────────────────
Query → embed → Qdrant search
  filter: tenant_id = X, team_id IN user_teams
  → top 100 → personalized rerank → top 20 → LLM
```

---

### Q3 SQL (10 min) - Personalization Lift

```sql
-- Compare satisfaction: personalized (treatment) vs non-personalized (control)
SELECT
  u.tenant_id,
  COUNT(DISTINCT t.user_id)                                    AS users,
  AVG(CASE WHEN t.personalized = TRUE  THEN t.satisfaction END) AS avg_sat_personalized,
  AVG(CASE WHEN t.personalized = FALSE THEN t.satisfaction END) AS avg_sat_control,
  AVG(CASE WHEN t.personalized = TRUE  THEN t.satisfaction END) -
  AVG(CASE WHEN t.personalized = FALSE THEN t.satisfaction END) AS lift,
  AVG(CASE WHEN t.personalized = TRUE  THEN t.click_rate END)  AS avg_ctr_personalized,
  AVG(CASE WHEN t.personalized = FALSE THEN t.click_rate END)  AS avg_ctr_control
FROM traces t
JOIN users u ON t.user_id = u.user_id
WHERE t.`timestamp` >= NOW() - INTERVAL '30' DAY
  AND t.satisfaction IS NOT NULL
GROUP BY u.tenant_id
HAVING COUNT(*) > 100
ORDER BY lift DESC;
```

**Output:**
| tenant_id | users | avg_sat_personalized | avg_sat_control | lift | avg_ctr_p | avg_ctr_ctrl |
|-----------|-------|----------------------|-----------------|------|-----------|--------------|
| tenant_a  | 50,000| 0.78                 | 0.71            | +0.07| 0.42      | 0.35         |
| tenant_b  | 30,000| 0.74                 | 0.72            | +0.02| 0.38      | 0.36         |

**Decision rule:** if `lift > 0.05` → ship personalization. Below → tune or kill.

---

### Q4 Coding (10 min)

```python
import numpy as np
from typing import List, Dict, Tuple


def personalized_rerank(
    query_emb: np.ndarray,
    user_emb: np.ndarray,
    candidates: List[Dict],
    base_weight: float = 0.6,
    user_weight: float = 0.3,
    recency_weight: float = 0.1,
    diversity_penalty: float = 0.05,
) -> List[Tuple[Dict, float]]:
    """
    Rerank with personalization, recency, and diversity penalty.
    final_score = base_weight * query_sim
                + user_weight * user_sim
                + recency_weight * recency
                - diversity_penalty * cluster_concentration
    """
    if user_emb is None or len(user_emb) == 0:
        user_emb = query_emb   # fallback

    scored = []
    for doc in candidates:
        # Base similarity
        q_sim = cosine_sim(query_emb, doc["embedding"])
        # User personalization
        u_sim = cosine_sim(user_emb, doc["embedding"]) if user_emb is not None else 0
        # Recency (0 to 1)
        days_old = (now() - doc["updated_at"]).days
        recency = math.exp(-days_old / 30)
        # Diversity penalty: same cluster as already-selected
        cluster = doc.get("cluster_id", 0)
        cluster_count = sum(1 for _, d, _ in scored if d.get("cluster_id") == cluster)
        diversity = cluster_count * diversity_penalty

        final = base_weight * q_sim + user_weight * u_sim + recency_weight * recency - diversity
        scored.append((doc, final))

    return sorted(scored, key=lambda x: x[1], reverse=True)


def tenant_isolation_filter(user_id: int, candidates: List[Dict]) -> List[Dict]:
    """
    STRICT filter — never return candidates from another tenant.
    This is enforced before everything else, even before scoring.
    """
    user_tenant = get_user_tenant(user_id)  # cached lookup
    return [c for c in candidates if c["tenant_id"] == user_tenant]


def build_user_embedding(user_id: int, days: int = 90) -> np.ndarray:
    """
    Build user embedding from last 90 days of clicks.
    Weighted by recency (exp decay) + dwell time + rating.
    """
    history = get_user_history(user_id, days=days)
    if not history:
        return None

    embeddings = []
    weights = []
    for event in history:
        doc_emb = get_doc_embedding(event["clicked_doc_id"])
        if doc_emb is None:
            continue
        # Recency weight: more recent = higher
        age_days = (now() - event["timestamp"]).days
        recency = math.exp(-age_days / 30)
        # Engagement: dwell_ms / 1000 (seconds), capped at 60
        engagement = min(event["dwell_ms"] / 1000, 60) / 60
        # Rating: thumbs_up = 1, down = 0
        rating = 1.0 if event["feedback_rating"] == "thumbs_up" else 0.3

        weight = recency * engagement * rating
        embeddings.append(doc_emb)
        weights.append(weight)

    if not embeddings:
        return None

    # Weighted average + normalize
    weights = np.array(weights) / sum(weights)
    user_emb = np.average(embeddings, axis=0, weights=weights)
    return user_emb / np.linalg.norm(user_emb)
```

---

## Sr Tech Design (40 min - compressed) - Personalized Workplace Search

```
┌────────────────────────────────────────────────────────────────┐
│       PERSONALIZED WORKPLACE SEARCH - 500M USERS               │
└────────────────────────────────────────────────────────────────┘

KEY DESIGN PRINCIPLES
─────────────────────
1. Tenant isolation at STORAGE layer (Qdrant filter)
2. User embedding built nightly, not real-time (cheap)
3. Diversity penalty to prevent filter bubble
4. Per-tenant rate limit + cost dashboard
5. Cross-tenant access attempts logged

ARCHITECTURE
────────────

USER EMBEDDING PIPELINE (nightly, batch)
────────────────────────────────────────
Last 90 days of clicks
  → weighted average by recency × dwell × rating
  → normalize
  → write user_preferences.user_embedding

QUERY PATH (real-time, <500ms p95)
──────────────────────────────────
1. Embed query (50ms)
2. Get user_embedding from user_preferences (10ms)
3. Qdrant hybrid search:
   filter: (tenant_id = X AND team_id IN user_teams)
   limit 100 (200ms)
4. Personalized rerank (50ms):
   score = 0.6 * query_sim + 0.3 * user_sim + 0.1 * recency - diversity_penalty
5. Top 20 → LLM (200ms)
6. Total: ~450ms

MULTI-TENANT SHARDING
──────────────────────
- 50 logical tenants (e.g., company divisions)
- 100 physical shards
- Routing: shard = hash(tenant_id) % 100
- Per-shard: 10M points max
- Per-tenant rate limit: 1000 RPS premium, 100 RPS free

DIVERSITY (anti-filter-bubble)
──────────────────────────────
- Top 20 must include ≥ 3 different cluster_ids
- cluster_id = Louvain community detection on doc graph
- If personalization forces all 20 to same cluster → force diversity
```

---

## Sr Ownership (15 min - compressed)

### Q1: Personalization went wrong - filter bubble

**L6 STAR (60 sec):**

**S:** Shipped personalized RAG, user satisfaction up. After 3 months, long-term retention dropped 5%.

**T:** Find why personalization is hurting long-term.

**A:**
1. Analyzed: personalized users had 80%+ overlap with their team's docs only. No exploration of other teams.
2. Identified: filter bubble. Users got the same 5 docs every time.
3. Fix: Added diversity constraint. Top 20 must have ≥ 3 different clusters (Louvain communities).
4. A/B test: diversity group had +5% long-term retention vs control, same short-term satisfaction.

**R:** Shipped diversity. Prevented retention drop. Lesson: personalization without diversity = echo chamber.

---

### Q2: Multi-tenant incident

**L6 STAR (60 sec):**

**S:** Tenant A's user accidentally saw Tenant B's private doc. P0 incident.

**T:** Patch in 1 hour.

**A:**
1. Root cause: `tenant_id` filter missing in Qdrant query. Bug in new code path.
2. Added **mandatory** tenant_id filter (CI gate fails if missing).
3. Audit log caught it: only 1 user affected, 1 doc.
4. Notified Tenant B + GDPR officer.
5. Added test: every query MUST have tenant_id filter.

**R:** 1h MTTR, 1 user affected, prevented future leaks. Lesson: tenant isolation is non-negotiable, enforce at storage layer + CI test.

---

## Full Stack (15 min - compressed) - Personalization Debugger

```tsx
import { useState } from "react";

const PersonalizationDebugger = () => {
  const [userId, setUserId] = useState("");
  const [docId, setDocId] = useState("");
  const [personalized, setPersonalized] = useState(true);
  const [debug, setDebug] = useState(null);

  const analyzeRanking = async () => {
    const res = await fetch(
      `/api/debug/ranking?user_id=${userId}&doc_id=${docId}&personalized=${personalized}`
    );
    setDebug(await res.json());
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Personalization Debugger</h1>

      <div className="grid grid-cols-3 gap-3 mb-4">
        <input
          value={userId}
          onChange={e => setUserId(e.target.value)}
          placeholder="user_id"
          className="border p-2 rounded"
        />
        <input
          value={docId}
          onChange={e => setDocId(e.target.value)}
          placeholder="doc_id"
          className="border p-2 rounded"
        />
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={personalized}
            onChange={e => setPersonalized(e.target.checked)}
          />
          Personalized
        </label>
      </div>

      <button
        onClick={analyzeRanking}
        className="bg-blue-500 text-white px-4 py-2 rounded mb-6"
      >
        Analyze Ranking
      </button>

      {debug && (
        <div className="space-y-4">
          {/* Score breakdown */}
          <div className="border rounded p-4">
            <h2 className="font-bold mb-3">Score Breakdown</h2>
            <table className="w-full">
              <tbody>
                <tr>
                  <td className="py-1">Base similarity (query ↔ doc)</td>
                  <td className="text-right font-mono">{debug.base_score?.toFixed(3)}</td>
                  <td className="text-right text-gray-500">× 0.6</td>
                </tr>
                <tr>
                  <td className="py-1">User history similarity</td>
                  <td className="text-right font-mono">{debug.user_sim?.toFixed(3)}</td>
                  <td className="text-right text-gray-500">× 0.3</td>
                </tr>
                <tr>
                  <td className="py-1">Recency weight</td>
                  <td className="text-right font-mono">{debug.recency?.toFixed(3)}</td>
                  <td className="text-right text-gray-500">× 0.1</td>
                </tr>
                <tr>
                  <td className="py-1">Diversity penalty</td>
                  <td className="text-right font-mono text-red-600">
                    -{debug.diversity_penalty?.toFixed(3)}
                  </td>
                  <td className="text-right text-gray-500">cluster #{debug.cluster_id}</td>
                </tr>
                <tr className="border-t-2">
                  <td className="py-2 font-bold">Final score</td>
                  <td className="text-right font-bold font-mono">
                    {debug.final_score?.toFixed(3)}
                  </td>
                  <td></td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Why ranked here */}
          <div className={`border rounded p-4 ${
            debug.ranked_correctly ? "bg-green-50" : "bg-yellow-50"
          }`}>
            <h2 className="font-bold mb-2">Why ranked #{debug.rank} of {debug.total_candidates}</h2>
            <ul className="text-sm space-y-1">
              {debug.reasons.map((r, i) => (
                <li key={i}>• {r}</li>
              ))}
            </ul>
          </div>

          {/* History match details */}
          {debug.matching_history && (
            <div className="border rounded p-4">
              <h2 className="font-bold mb-2">User History Match</h2>
              <p className="text-sm text-gray-600 mb-2">
                This doc matches your history because:
              </p>
              <ul className="text-sm space-y-1">
                <li>• You clicked this doc {debug.matching_history.click_count} times</li>
                <li>• Last click: {debug.matching_history.last_click}</li>
                <li>• Avg dwell: {debug.matching_history.avg_dwell_sec}s</li>
                <li>• Topic overlap: {debug.matching_history.topic_overlap}</li>
              </ul>
            </div>
          )}

          {/* Comparison: personalized vs not */}
          <div className="border rounded p-4">
            <h2 className="font-bold mb-2">Comparison: Personalized vs Control</h2>
            <table className="w-full text-sm">
              <thead className="bg-gray-100">
                <tr>
                  <th className="p-2 text-left">Mode</th>
                  <th className="p-2">Rank</th>
                  <th className="p-2">Final Score</th>
                  <th className="p-2">Recency</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="p-2 font-medium">With personalization</td>
                  <td className="p-2 text-center">#{debug.personalized_rank}</td>
                  <td className="p-2 text-center">{debug.personalized_score?.toFixed(3)}</td>
                  <td className="p-2 text-center">+{debug.personalization_boost?.toFixed(3)}</td>
                </tr>
                <tr>
                  <td className="p-2 font-medium">Control (no personalization)</td>
                  <td className="p-2 text-center">#{debug.control_rank}</td>
                  <td className="p-2 text-center">{debug.control_score?.toFixed(3)}</td>
                  <td className="p-2 text-center">—</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
```

---

## Day 5 (Loop 8) Checkpoint

Can you:
- [ ] Name the **3 personalization signals** (history, team, time)?
- [ ] State the **rerank formula** with weights (0.6/0.3/0.1)?
- [ ] Explain **why 30% weight on user_sim** (avoid bubble)?
- [ ] Code `tenant_isolation_filter` enforced before everything?
- [ ] Compute **personalization lift SQL** comparing treatment vs control?

If yes, you're ready for Loop 10.
