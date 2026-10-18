# LOOP 7: Migration + Model Upgrades + Dual-Write

**Theme:** Zero-downtime embedding model upgrade, $130k cost control
**Total Duration:** 2 hours (compressed)
**Difficulty:** Medium (5-min rollback is the bar)

---

## Architecture Diagram (Master)

```
┌────────────────────────────────────────────────────────────────────┐
│    ZERO-DOWNTIME EMBEDDING MODEL UPGRADE: v1 → v2                   │
└────────────────────────────────────────────────────────────────────┘

PHASE 1: DUAL-WRITE (Day 1)
───────────────────────────

New Doc → Kafka → Flink → Write to v1 collection (prod)
                       → Write to v2_shadow collection (new)


PHASE 2: BACKFILL (Day 1-10)
────────────────────────────

Spark job: 10% backfill daily, 10 days = 100% migrated
  - Read v1 points
  - Re-embed with v2 model
  - Write to v2_shadow
  - Track progress


PHASE 3: DUAL-READ + EVAL (Day 1-7)
───────────────────────────────────

1% of queries → embed with BOTH v1 and v2
              → Retrieve from both
              → Log both responses + metrics
              → Compare Recall@8, latency, cost

Compare daily:
┌─────────────────────────────────────┐
│ Model    │ Recall@8 │ Latency │ Cost│
├──────────┼──────────┼─────────┼─────┤
│ v1       │ 0.89     │ 420ms   │$0.01│
│ v2_shadow│ 0.91     │ 380ms   │$0.03│  ◀── +2% recall, +200% cost
└─────────────────────────────────────┘


PHASE 4: CUTOVER (Day 8+, only if v2 ≥ v1 for 7 days)
─────────────────────────────────────────────────────

embedding_v2_enabled feature flag = true
↓
100% queries use v2


PHASE 5: ROLLBACK (5 min if needed)
───────────────────────────────────

embedding_v2_enabled feature flag = false
↓
100% queries use v1 (no data loss, just switch the model)

COST CONTROL
────────────
- v2 is 3x more expensive per embedding
- 1B chunks × $0.003 = $3M one-time backfill
- Wait, that's too much! OPTION:
  - Selective backfill: only top 10M most-queried docs (90% of traffic)
  - Cost: $30k instead of $3M
```

---

## Greet (10 min - compressed)

### Q1: How do you upgrade embedding model without downtime?

**L6 Answer (75 sec):**

> "Five phases:
>
> 1. **Create shadow collection** `docs_v2_shadow` in Qdrant, separate from `docs_v1` (prod).
>
> 2. **Dual-write:** New docs go to BOTH v1 and v2 via Kafka + Flink. No data loss.
>
> 3. **Backfill:** Spark job backfills 10% of existing docs daily. 10 days = 100% done. Re-embed with v2 model.
>
> 4. **Dual-read 1%:** For 1% of queries, retrieve from BOTH, log metrics, compare. Need v2 Recall ≥ v1 Recall for 7 consecutive days.
>
> 5. **Cutover:** Flip feature flag `embedding_v2_enabled = true`, 100% traffic on v2.
>
> **Rollback in 5 min** if anything goes wrong: flip flag to false, all traffic back to v1. No data loss because both collections have the same content.
>
> Cost control: backfill only top 10M most-queried docs first (covers 90% of traffic), not all 1B chunks. Saves $2.97M."

**L6 Keywords:** five phases, dual-write, shadow collection, 1% dual-read, 7-day window, 5-min rollback, cost control.

---

### Q2: Migration you owned (compressed)

**L6 STAR (60 sec):**

**S:** ES → Qdrant for 10M docs. ES cost $50k/month, latency 1.2s. Risk: downtime, data loss.

**T:** Zero downtime, zero data loss.

**A:** Dual-write via Kafka, Spark backfill, shadow read 7 days, cutover when Qdrant Recall > ES. Kept ES as backup 2 weeks. Feature flag rollback in 5 min.

**R:** Zero downtime, latency 1.2s → 420ms, cost $50k → $12k/month ($456k/year saved). Runbook used by 2 teams.

---

## AI-Native DE Full Stack (40 min - compressed)

### Q1 Data Model (10 min)

```
┌────────────────────────────────────────────────────────────┐
│      SHADOW COLLECTIONS + MODEL VERSION DATA MODEL         │
└────────────────────────────────────────────────────────────┘

model_versions                     qdrant_collections
┌────────────────────────┐         ┌──────────────────────────┐
│ model_version    PK    │◀───────▶│ collection_name  PK      │
│ created_at              │  1:N   │ model_version    FK      │
│ is_production   BOOL    │         │ shard_count      INT     │
│ is_shadow       BOOL    │         │ doc_count        BIGINT  │
│ traffic_pct      FLOAT  │         │ created_at       TIMESTAMP│
│ embedding_model_name    │         └──────────────────────────┘
│ cost_per_1m_tokens $    │
└────────────────────────┘         dual_write_log
                                   ┌──────────────────────────┐
                                   │ log_id    PK             │
migration_jobs                    │ doc_id                   │
┌────────────────────────┐         │ v1_status  success|fail  │
│ job_id          PK     │         │ v2_status  success|fail  │
│ from_version     FK    │         │ v1_latency_ms            │
│ to_version       FK    │         │ v2_latency_ms            │
│ status  pending|running│         │ timestamp                │
│   |completed|failed    │         └──────────────────────────┘
│ progress_pct    FLOAT  │
│ start_time              │
│ end_time                │
└────────────────────────┘
```

**SQL:**

```sql
CREATE TABLE model_versions (
  model_version          STRING PRIMARY KEY,
  created_at             TIMESTAMP,
  is_production          BOOLEAN,
  is_shadow              BOOLEAN,
  traffic_pct            FLOAT,
  embedding_model_name   STRING,
  cost_per_1m_tokens     FLOAT
);

CREATE TABLE dual_write_log (
  log_id        BIGINT PRIMARY KEY,
  doc_id        BIGINT,
  v1_status     STRING,
  v2_status     STRING,
  v1_latency_ms INT,
  v2_latency_ms INT,
  `timestamp`   TIMESTAMP
) PARTITIONED BY (DATE(`timestamp`));
```

---

### Q2 Pipeline (10 min)

```
┌────────────────────────────────────────────────────────────┐
│     DUAL-WRITE + BACKFILL + DUAL-READ PIPELINE              │
└────────────────────────────────────────────────────────────┘

DUAL-WRITE (always on, Flink)
─────────────────────────────
New doc → Kafka
            │
            ├──▶ Embed with v1 → Write to docs_v1 (prod)
            │
            └──▶ Embed with v2 → Write to docs_v2_shadow

BACKFILL (Spark, 10% daily)
────────────────────────────
Read 10% of docs_v1
       ↓
Re-embed with v2
       ↓
Write to docs_v2_shadow
       ↓
Track progress in migration_jobs

DUAL-READ (1% of queries)
──────────────────────────
Query →
  ├─ Embed + retrieve from docs_v1 → log metrics
  │
  └─ Embed + retrieve from docs_v2_shadow → log metrics

Compare daily, alert if Recall drop > 2%
```

---

### Q3 SQL (10 min) - Shadow vs Prod Comparison

```sql
-- Compare shadow vs prod over last 7 days
SELECT
  model_version,
  COUNT(*)                          AS query_count,
  AVG(recall_at_8)                  AS avg_recall,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) AS p95_latency,
  AVG(cost_usd)                     AS avg_cost,
  -- Win/loss: how often does shadow match or beat prod
  SUM(CASE WHEN recall_at_8 >= 0.85 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS pct_above_sla
FROM traces
WHERE `timestamp` >= NOW() - INTERVAL '7' DAY
  AND model_version IN ('v1', 'v2_shadow')
GROUP BY model_version
ORDER BY avg_recall DESC;
```

**Decision:** if `v2_shadow.avg_recall >= v1.avg_recall` for 7 days → promote.

---

### Q4 Coding (10 min)

```python
import random
from typing import Tuple


class EmbeddingModelRouter:
    """
    Routes queries between v1 (prod) and v2_shadow based on:
    - Feature flag (for 100% cutover)
    - Shadow traffic percentage (for 1% A/B comparison)
    """

    def __init__(self):
        self.shadow_traffic_pct = 0.01   # 1% dual-read
        self.v1_collection = "docs_v1"
        self.v2_shadow_collection = "docs_v2_shadow"
        self.feature_flag = "embedding_v2_enabled"
        self.v1_model = load_model("text-embedding-3-small")
        self.v2_model = load_model("text-embedding-3-large")

    def embed_query(self, text: str) -> Tuple[list, str, dict]:
        """
        Returns (embedding_for_query, model_version_used, shadow_info).
        shadow_info is None unless we're doing dual-read.
        """
        # 100% cutover mode: all traffic to v2
        if feature_flag_enabled(self.feature_flag):
            emb = self.v2_model.encode(text)
            return emb, "v2", None

        # Normal mode: v1 for the user, dual-read for 1%
        emb_v1 = self.v1_model.encode(text)
        shadow_info = None

        if random.random() < self.shadow_traffic_pct:
            # Dual-read: also embed + retrieve from v2_shadow
            emb_v2 = self.v2_model.encode(text)
            shadow_info = {"v2_emb": emb_v2, "compared_at": time.time()}
            log_shadow_comparison(text, emb_v1, emb_v2)

        # Return v1 embedding for user-facing retrieval
        return emb_v1, "v1", shadow_info

    def rollback(self, reason: str):
        """5-min rollback: disable v2 feature flag."""
        disable_feature_flag(self.feature_flag)
        log_rollback(reason=reason, ts=time.time())
        # All traffic back to v1, no data loss


def create_shadow_collection(v2_model: str, shard_count: int = 20):
    """
    Create v2_shadow collection with same shard config as v1.
    Called once at start of migration.
    """
    qdrant.create_collection(
        collection_name="docs_v2_shadow",
        vectors_config=models.VectorParams(
            size=v2_dimension,        # may differ from v1!
            distance="Cosine"
        ),
        shard_number=shard_count,
        replication_factor=3,
    )
    log_migration_start("v1", "v2_shadow", shard_count)


def backfill_progress() -> dict:
    """Returns % backfilled for migration dashboard."""
    total = qdrant.count(collection_name="docs_v1").count
    done = qdrant.count(collection_name="docs_v2_shadow").count
    return {
        "total_docs": total,
        "backfilled_docs": done,
        "progress_pct": round(100.0 * done / total, 2),
        "eta_days": round((total - done) / (done / days_since_start), 1),
    }
```

---

## Sr Tech Design (40 min - compressed) - Embedding Model Upgrade System

```
┌────────────────────────────────────────────────────────────────┐
│       EMBEDDING MODEL UPGRADE SYSTEM: v1 → v2                  │
└────────────────────────────────────────────────────────────────┘

KEY DESIGN DECISIONS
────────────────────
1. Selective backfill: only top 10M most-queried docs (90% traffic)
2. Dual-write via Kafka Flink (no data loss)
3. 7-day dual-read window for confidence
4. 5-min rollback via feature flag
5. Cost control: $30k instead of $3M

PHASES
──────

Phase 0: SELECTIVE BACKFILL
  - Query traces for last 30 days
  - Top 10M docs by query count = 90% of traffic
  - Backfill these first, ignore cold 990M

Phase 1: DUAL-WRITE (Day 1)
  - Flink writes new docs to BOTH v1 and v2_shadow
  - Verification: count matches every 5 min

Phase 2: BACKFILL (Day 1-7)
  - Spark: read top 10M from v1, re-embed with v2, write to v2_shadow
  - Estimated time: 10M docs × 5ms = 50k machine-seconds
  - 100 Spark cores → 8 min
  - Run daily, 7 days covers retries for failures

Phase 3: DUAL-READ + EVAL (Day 1-7)
  - 1% queries: dual-read from v1 + v2_shadow
  - Compute: Recall@8, latency, cost, satisfaction
  - Daily comparison report
  - Promote criteria: v2 ≥ v1 for 7 days

Phase 4: CUTOVER (Day 8+)
  - Set feature flag embedding_v2_enabled = true
  - Monitor p95 latency, satisfaction for 24h
  - If regression: rollback in 5 min

Phase 5: CLEANUP (Day 30)
  - Delete v1 collection (after 30-day safety window)
  - Savings: 50% storage reduction

ROLLBACK PROCEDURE
──────────────────
1. Detect regression (alert fires)
2. PagerDuty → oncall paged
3. Run: feature_flag set embedding_v2_enabled false
4. Verify: 100% queries now hitting v1 (5 min)
5. Postmortem within 24h
```

---

## Sr Ownership (15 min - compressed)

### Migration that went wrong - rollback

**L6 STAR (60 sec):**

**S:** Qdrant cutover to v2 embeddings. After 1h, p95 spiked 420ms → 2s, satisfaction 73% → 50%. P0.

**T:** Rollback in 5 min, then fix.

**A:**
1. Flipped feature flag `embedding_v2_enabled = false` → 100% traffic to v1
2. Latency back to 420ms in 3 min (Qdrant v2 collection still warm)
3. Root cause: v2 model is 3x larger, Qdrant shards undersized for bigger vectors
4. Fix: Upgraded Qdrant shard memory 2x, retried 1 week later — smooth cutover

**R:** MTTR 5 min, prevented 1h outage, no data loss. Feature flag was the only reason we recovered fast. Runbook updated.

---

## Full Stack (15 min - compressed) - Model Upgrade Dashboard

```tsx
import { useState, useEffect } from "react";

const ModelUpgradeDashboard = () => {
  const [comparison, setComparison] = useState(null);
  const [progress, setProgress] = useState(null);
  const [actionPending, setActionPending] = useState(false);

  useEffect(() => {
    const fetchStatus = async () => {
      const c = await fetch("/api/upgrade/comparison").then(r => r.json());
      const p = await fetch("/api/upgrade/progress").then(r => r.json());
      setComparison(c);
      setProgress(p);
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 30_000);
    return () => clearInterval(interval);
  }, []);

  const canPromote = comparison?.v2?.recall >= comparison?.v1?.recall
                   && comparison?.days_above_threshold >= 7;

  const promote = async () => {
    setActionPending(true);
    await fetch("/api/upgrade/promote", { method: "POST" });
    alert("v2 promoted to 100%");
  };

  const rollback = async () => {
    if (!confirm("Rollback to v1? This affects all production traffic.")) return;
    setActionPending(true);
    await fetch("/api/upgrade/rollback", { method: "POST" });
    alert("Rolled back to v1");
  };

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">
        Model Upgrade: v1 → v2_shadow
      </h1>

      {/* Progress bar */}
      <div className="mb-6">
        <h2 className="font-semibold mb-2">
          Backfill Progress: {progress?.progress_pct}%
        </h2>
        <div className="w-full bg-gray-200 rounded h-8">
          <div
            className="bg-blue-500 h-full rounded transition-all"
            style={{ width: `${progress?.progress_pct}%` }}
          />
        </div>
        <p className="text-sm text-gray-600 mt-1">
          {progress?.backfilled_docs?.toLocaleString()} / {progress?.total_docs?.toLocaleString()} docs
          {" · "} ETA: {progress?.eta_days} days
        </p>
      </div>

      {/* Side-by-side comparison */}
      <h2 className="font-semibold mb-2">v1 vs v2_shadow (7-day window)</h2>
      <table className="w-full border-collapse mb-6">
        <thead className="bg-gray-100">
          <tr>
            <th className="border p-2">Metric</th>
            <th className="border p-2">v1 (prod)</th>
            <th className="border p-2">v2_shadow</th>
            <th className="border p-2">Delta</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td className="border p-2 font-medium">Recall@8</td>
            <td className="border p-2">{comparison?.v1.recall?.toFixed(3)}</td>
            <td className="border p-2">{comparison?.v2.recall?.toFixed(3)}</td>
            <td className={`border p-2 font-bold ${
              comparison?.v2.recall > comparison?.v1.recall ? "text-green-600" : "text-red-600"
            }`}>
              {((comparison?.v2.recall - comparison?.v1.recall) * 100).toFixed(1)}%
            </td>
          </tr>
          <tr>
            <td className="border p-2 font-medium">p95 Latency</td>
            <td className="border p-2">{comparison?.v1.latency}ms</td>
            <td className="border p-2">{comparison?.v2.latency}ms</td>
            <td className="border p-2">
              {comparison?.v2.latency - comparison?.v1.latency}ms
            </td>
          </tr>
          <tr>
            <td className="border p-2 font-medium">Avg Cost / query</td>
            <td className="border p-2">${comparison?.v1.cost?.toFixed(4)}</td>
            <td className="border p-2">${comparison?.v2.cost?.toFixed(4)}</td>
            <td className="border p-2">
              ${(comparison?.v2.cost - comparison?.v1.cost).toFixed(4)}
            </td>
          </tr>
          <tr>
            <td className="border p-2 font-medium">Satisfaction</td>
            <td className="border p-2">{(comparison?.v1.satisfaction * 100).toFixed(1)}%</td>
            <td className="border p-2">{(comparison?.v2.satisfaction * 100).toFixed(1)}%</td>
            <td className="border p-2">
              {((comparison?.v2.satisfaction - comparison?.v1.satisfaction) * 100).toFixed(1)}%
            </td>
          </tr>
          <tr>
            <td className="border p-2 font-medium">Days ≥ v1</td>
            <td className="border p-2">—</td>
            <td className="border p-2">{comparison?.days_above_threshold} / 7</td>
            <td className="border p-2">
              {comparison?.days_above_threshold >= 7 ? "✓ Ready" : "⏳ Waiting"}
            </td>
          </tr>
        </tbody>
      </table>

      {/* Action buttons */}
      <div className="flex gap-3">
        <button
          onClick={promote}
          disabled={!canPromote || actionPending}
          className="bg-green-500 text-white px-6 py-3 rounded font-medium disabled:bg-gray-300"
        >
          Promote v2 to 100%
        </button>
        <button
          onClick={rollback}
          disabled={actionPending}
          className="bg-red-500 text-white px-6 py-3 rounded font-medium"
        >
          🆘 Rollback to v1
        </button>
      </div>

      <p className="text-xs text-gray-500 mt-4">
        Promote requires v2 ≥ v1 for 7 consecutive days. Rollback affects 100% of traffic.
      </p>
    </div>
  );
};
```

---

## Day 5 (Loop 7) Checkpoint

Can you:
- [ ] Name the **5 migration phases** in order?
- [ ] Explain **why 7-day window** before cutover (avoid flapping)?
- [ ] Code `EmbeddingModelRouter` with feature flag and shadow traffic?
- [ ] Compute **shadow vs prod SQL** comparison with promotion criteria?
- [ ] Describe **5-min rollback procedure**?

If yes, you're ready for Loop 8.
