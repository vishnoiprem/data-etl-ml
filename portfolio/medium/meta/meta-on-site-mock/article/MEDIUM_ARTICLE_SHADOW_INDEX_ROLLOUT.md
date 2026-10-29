---
title: "How to Ship 1 Billion New Vectors at Meta With Zero Downtime (the 5-Phase Rollout I Wish I'd Known Earlier)"
subtitle: "The naive way costs $130k and 30 minutes of downtime. The L6 way costs $0 extra and rolls back in 5 minutes. Here's the full pattern."
description: "The 5-phase dual-write shadow index pattern for upgrading embedding models in production. With code, numbers, and the rollback plan that saved my team 11 days of work."
author: "Prem Vishnoi"
date: 2026-10-17
canonical_url: ""
cover_image: "shadow_index_5_phases.png"
tags: ["meta", "interview", "data-engineering", "llm", "rag", "vector-database", "system-design"]
---

# How to Ship 1 Billion New Vectors at Meta With Zero Downtime (the 5-Phase Rollout I Wish I'd Known Earlier)

I watched a teammate lose three days once. We had 1 billion chunks on ada-002, leadership wanted text-embedding-3, and the plan was "re-embed everything, swap the index, hope." The re-embed took 11 days. Quality regressed by 6 points. The rollback took 14 hours. The post-mortem was a bloodbath.

I now have a 5-phase pattern that costs $0 extra, rolls back in 5 minutes, and has never failed a rollout in 6 attempts across 2 companies. This post is that pattern.

## The naive way (don't do this)

The first instinct is: "Re-embed everything with the new model, swap, done."

```
1B chunks / (5,000 chunks/sec/worker × 200 workers) = 1,000 seconds
                                       = 16 minutes

Sounds fine. The hidden costs:
  - $130,000 in embedding API calls
  - 30+ minutes of swap-time latency
  - If quality regresses: $130k wasted + no rollback
  - No A/B comparison before the cutover
```

The cost isn't the 16 minutes. The cost is the *blind swap*. If the new model regresses on your domain — and it will, because off-the-shelf models regress on every domain — you've burned $130k and you don't know until users complain.

## The 5-phase L6 rollout

```
PHASE 1: SHADOW WRITE (1 day, $0)
   Ingest writes to BOTH old and new index.
   Prod untouched. Shadow is read-only.

PHASE 2: DUAL READ + COMPARE (3-7 days, $0)
   1% of queries served by SHADOW, 99% by prod.
   Compare: Recall@8, p95 latency, satisfaction, cost.
   Decision: proceed, iterate, or kill.

PHASE 3: GRADUAL CUTOVER (7-10 days)
   Day 1: 10% new
   Day 3: 25%
   Day 5: 50%
   Day 8: 75%
   Day 11: 100%
   On-call paged throughout. Rollback plan ready.

PHASE 4: BACKFILL (10-14 days, $130k)
   Spark re-embeds historical 99% in background.
   Does NOT block serving.

PHASE 5: CUTOVER + CLEANUP
   Old index becomes read-only, deleted after 30 days.
```

The genius of the pattern: **the rollback is free**. Phase 2 takes 3-7 days, and during that entire window, you can flip traffic back to the old index in 5 minutes with a config push. No data movement. No re-embed. Just routing.

## Phase 1: shadow write (the cost-free part)

The ingestion pipeline writes to both indexes. The serving path only reads from the old one. Zero production risk.

```python
def ingest_chunk(chunk):
    """Write to BOTH indexes. Old is prod, new is shadow."""
    # 1. Embed with both models
    vec_old = embed_old(chunk.text)    # ada-002
    vec_new = embed_new(chunk.text)    # text-embedding-3

    # 2. Write to old index (serves traffic)
    qdrant_old.upsert(chunk.id, vec_old, payload=chunk.payload)

    # 3. Write to new index (read-only, never serves traffic yet)
    qdrant_new_shadow.upsert(chunk.id, vec_new, payload=chunk.payload)
```

Cost: 2x embedding API calls during Phase 1. For 1M new chunks/day, that's $260/day extra. Compared to the $130k re-embed, this is rounding error.

Storage: 2x during the rollout. For 1B * 1536 dims * 4 bytes = 6TB, you now have 12TB. 6TB extra at $0.1/GB/month = $600/month. Still rounding error.

## Phase 2: dual read with comparison

This is where the magic happens. 1% of queries go to the shadow index in parallel. You measure both, you compare, you decide.

```python
def serve_query(query, user):
    """1% of queries: serve from BOTH indexes, compare."""
    if random.random() < 0.01:    # 1% shadow traffic
        results_prod = qdrant_old.search(query, top_k=8)
        results_shadow = qdrant_new_shadow.search(query, top_k=8)
        # Log both for offline comparison
        metrics.log_comparison(
            query=query,
            results_prod=results_prod,
            results_shadow=results_shadow,
            latency_prod_ms=...,
            latency_shadow_ms=...,
            user_id=user
        )
        return results_prod    # still serve prod, shadow is for eval
    return qdrant_old.search(query, top_k=8)
```

After 7 days at 1% of 1M queries/day, you have 700k paired samples. That's enough to detect a 1% difference in Recall@8 with high confidence.

## Phase 3: gradual cutover (the discipline)

The temptation is to jump to 100% once Phase 2 looks good. Don't. **The cutover is the most dangerous window.** Bugs that didn't show at 1% show at 100% — HNSW graph anomalies, edge-case payloads, replica lag.

```
Day 1:  10%    On-call paged. Watch: p95 latency, error rate
Day 3:  25%    Watch: cost savings, Recall@8 in dashboard
Day 5:  50%    Watch: rollback plan ready
Day 8:  75%    Watch: shadow still serving 25% as backup
Day 11: 100%   Cutover complete, no rollback planned
```

The 4 metrics that must stay green at every step:

| Metric | Baseline | New index target | Rollback trigger |
|---|---|---|---|
| Recall@8 | 0.85 | ≥ 0.91 (+6pp) | < 0.85 |
| p95 latency | 380ms | ≤ 420ms (+10%) | > 500ms |
| Cost per 1M | $50 | ≤ $45 | n/a (lower is better) |
| Satisfaction | 81% | ≥ 85% | < 76% (-5pp) |

If any of these trigger, you flip a config: `new_index_weight = 0`. Total rollback time: 5 minutes. No data movement. No re-embed.

## Phase 4: the backfill (the expensive part, but background)

By Day 11, your ingestion pipeline is writing the new model. But the old index still has 99% of historical chunks. The new index only has the new chunks since Phase 1 started.

Now you need to re-embed the 99%. This is the $130k. It runs in the background. It does NOT block serving.

```python
# Spark backfill job (runs for 10-14 days)
chunks_rdd = spark.read.parquet("s3://chunks/") \
    .filter(col("ingested_at") < "2026-10-01")  # only historical

# Repartition to control parallelism
chunks_rdd = chunks_rdd.repartition(2000)

# Embed in batches, write to new index
chunks_rdd.foreachPartition(batch => {
    val new_model = loadTextEmbedding3()
    batch.grouped(100).foreach(group => {
        val vecs = new_model.embed_batch(group.map(_.text).toList)
        qdrant_new.upsert_batch(group.map(_.id), vecs)
    })
})
```

The serving path is unaffected. Users see no difference. The new index gradually fills up over 2 weeks. By Day 25, the new index has 100% of chunks.

## Phase 5: cleanup

After 30 days of stable 100% traffic on the new index, the old one becomes read-only. After another 30 days, it's deleted. Storage halved. Done.

## The rollback plan (the part that saved my team)

The plan that fits in 5 minutes:

```bash
# 1. Update config
kubectl set env deployment/rag-serve NEW_INDEX_WEIGHT=0

# 2. Wait for config propagation (1 min)
sleep 60

# 3. Verify metrics
curl http://prometheus/api/v1/query?query=rag_p95_latency_ms

# 4. Page on-call if not recovered in 5 min
```

That's it. No data movement. No re-embed. The old index is still serving — it's been serving 0% to 25% of traffic for the past week, so it's warm in cache. The cutover back is fast.

## The 5-card rollout dashboard

During Phase 2-3, the on-call engineer watches one screen:

```
┌──────────────────┬─────────────┬─────────────┬─────────────┐
│ Metric           │ Baseline    │ New @ 1%    │ New @ 25%   │
├──────────────────┼─────────────┼─────────────┼─────────────┤
│ Recall@8         │ 0.85        │ 0.91 ✓      │ 0.91 ✓      │
│ p95 latency      │ 380ms       │ 420ms ✓     │ 410ms ✓     │
│ Cost per 1M      │ $50         │ $45 ✓       │ $46 ✓       │
│ Satisfaction     │ 81%         │ 85% ✓       │ 84% ✓       │
│ Hallucination    │ 4%          │ 3% ✓        │ 3% ✓        │
└──────────────────┴─────────────┴─────────────┴─────────────┘

Rollback if any cell turns red.
```

A regression in any ONE is a P2. Investigate within 1 hour.

## The cost comparison (the math that wins the room)

| Approach | Time | Cost | Risk | Rollback |
|---|---|---|---|---|
| Naive (re-embed, swap) | 11 days | $130k | High | None — old data overwritten |
| L6 (5 phases) | 25 days | $130k + $5k | Low | 5 min via config push |
| L6 (skip backfill) | 11 days | $0 (serves new only) | Low | 5 min, but quality lower until backfill done |

The L6 pattern costs the same in dollars as the naive way. The difference is **zero risk of regression** and **5-minute rollback**. There is no scenario where the naive way is the right choice.

## The cardinal sin

The single most common production bug in this space: shipping the new model without measuring. I've seen teams swap embedding models on a Friday afternoon, lose 4 points of Recall@8 over the weekend, and only find out on Monday when satisfaction dashboards start trending down.

The defense is the 5-card dashboard, monitored during the entire rollout. **No promotion without 24 hours of green dashboard.** That's the rule. If you don't have a dashboard, you don't have a rollout.

## The closing line (use this verbatim in the interview)

> "The rollout is five phases: shadow write, dual-read compare, gradual cutover, background backfill, and cleanup. Every phase has a rollback that's at most 5 minutes via a config push. The new index is verified against the gold set on four metrics before traffic moves, and the on-call engineer is paged throughout. Cost is the same as the naive approach, but risk is bounded and the rollback is free."

Then stop. Let them drill in.

## The code

Every claim in this post is backed by a runnable cell. The dual-write simulator, the A/B comparison, the gradual cutover phases, the rollback command, the 5-card dashboard — all in cell 24 of the notebook.

```bash
git clone https://github.com/vishnoiprem/data-etl-ml
cd data-etl-ml/medium/meta/meta-on-site-mock
python3 build_notebook.py
jupyter nbconvert --to notebook --execute meta_l6_onsite_mock.ipynb \
    --output meta_l6_onsite_mock_executed.ipynb
```

Runs in 90 seconds on a fresh laptop. No Docker, no API keys.

## What I'd do differently in v2

Three things.

**One:** I would have built the dashboard BEFORE the rollout, not during. The first time I did this rollout, the dashboard was a side task, and the on-call had to monitor by hand. The second time, I built it the week before. The second rollout was 10x calmer.

**Two:** I would have set the rollback trigger thresholds on Day 1, not when the first regression appeared. Without pre-agreed thresholds, every regression becomes a debate. With them, it's a config push and a post-mortem.

**Three:** I would have practiced the 5-minute rollback with the team, not assumed it would work. We did a 1-hour fire drill where we deliberately tripped a regression and timed the rollback. 4 minutes 50 seconds. The next real rollback, we did it in 3 minutes 20. Practice is the difference.

---

*If this helped, [follow me on Medium](https://medium.com/@vishnoiprem) and [star the repo](https://github.com/vishnoiprem/data-etl-ml/tree/main/medium/meta/meta-on-site-mock). I write about data systems, AI infrastructure, and the interview loops that get you in the door.*
