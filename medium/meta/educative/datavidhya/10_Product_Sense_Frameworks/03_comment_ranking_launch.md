# Launch New Comment Ranking Algorithm

## Problem
You are shipping a new comment ranking algorithm. How do you design the
launch, metrics, and rollout?

## How to Think
1. **NSM** – meaningful conversations (3+ unique commenters per thread).
2. **Primary** – 1-2 metrics that capture the goal.
3. **Secondary** – depth, latency, quality of replies.
4. **Counter** – what could regress (moderation, creator satisfaction).
5. **A/B** – unit, MDE, power, duration.
6. **Rollout** – ramped with guardrails.

## How to Remember
- **Framework**: "NSM -> Primary -> Secondary -> Counter -> Rollout."
- Rollout: "1% -> 5% -> 25% -> 100% with daily checks."

## Metrics
| Tier | Metric |
|---|---|
| NSM | % threads with >= 3 unique commenters |
| Primary | % threads reaching 3+ commenters, replies per comment |
| Secondary | Time-to-first-reply, comment length, positive reactions |
| Counter | Hide/report rate, creator complaints, moderation load |

## A/B Setup
- Unit: user_id
- Split: 50/50
- Duration: 4 weeks
- MDE: +2% relative on primary
- Power 0.8, alpha 0.05

## Rollout Plan
| Phase | Traffic | Monitor |
|---|---|---|
| Day 0-2 | 1% | primary + guardrails |
| Day 3-7 | 5% | primary + secondary + guardrails |
| Day 8-14 | 25% | all metrics + subgroup analysis |
| Day 15-28 | 100% | holdout + long-term |

## SQL (Primary Metric)
```sql
WITH thread_stats AS (
    SELECT post_id,
           COUNT(DISTINCT commenter_id) AS unique_commenters
    FROM comments
    WHERE created_ts >= CURRENT_DATE - INTERVAL '28' DAY
    GROUP BY post_id
)
SELECT
    SUM(CASE WHEN unique_commenters >= 3 THEN 1 ELSE 0 END) * 1.0
      / COUNT(*) AS pct_meaningful_threads
FROM thread_stats;
```

## Common Mistakes
- No counter-metrics (ranking can lift engagement but hurt quality).
- Skipping ramped rollout (one-shot 50% can break things).
- Forgetting long-term effects (novelty bias in week 1).

## AI Use Cases
- Auto generate experiment design docs.
- Sequential testing (always-valid p-values).
- Auto post-launch cohort decomposition.
