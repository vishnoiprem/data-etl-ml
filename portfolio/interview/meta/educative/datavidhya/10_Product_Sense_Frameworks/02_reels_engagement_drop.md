# Reels Engagement Dropped 5% WoW - Investigation

## Problem
Reels weekly engagement rate dropped 5% week-over-week. Walk the interviewer
through how you'd triage, root-cause, and fix.

## How to Think
1. **Scope** – is it real? Data quality, definition changes, seasonality.
2. **Decompose** – country, device, cohort, surface, creator tier.
3. **Hypothesize** – ranking / supply / bug / competitor / policy.
4. **Validate** – correlate with deploy timestamps, supply curves, errors.
5. **Act** – rollback, fix, comms, post-mortem.

## How to Remember
- **Framework**: "Scope -> Decompose -> Hypothesize -> Validate -> Act."
- **Order**: DATA before MODEL before PRODUCT.

## Decomposition Dimensions
- Country / region
- Device OS / app version
- Age / gender band
- Acquisition channel
- Surface (Feed, Reels, Reels tab)
- Creator tier (top 1%, mid, long-tail)
- Video length bucket

## Hypotheses & Validation
| Hypothesis | Validation |
|---|---|
| Ranking regression | Offline NDCG vs baseline; deploy timestamps |
| Creator supply shock | Top 1% creator posting volume WoW |
| Engagement bait policy | Classifier threshold changes |
| Client bug | Client error rate for Reels surface |
| Competitor launch | TikTok/Shorts news in same week |

## SQL (Presto)
```sql
-- Country-level engagement WoW
SELECT country, wk,
       SUM(likes + comments + shares) / NULLIF(SUM(impressions), 0) AS eng_rate,
       LAG(SUM(likes + comments + shares) / NULLIF(SUM(impressions), 0))
         OVER (PARTITION BY country ORDER BY wk) AS prev_eng_rate
FROM reels_events
WHERE wk >= CURRENT_DATE - INTERVAL '14' DAY
GROUP BY country, wk
ORDER BY country, wk DESC;
```

## Common Mistakes
- Diving into model debug without checking pipeline/data first.
- Looking at only one country or device.
- Attributing to a launch without a counterfactual.

## AI Use Cases
- LLM-driven root-cause summaries from deploy + metric logs.
- Causal attribution across metric movement.
- Auto-run playbook on anomaly detection.
