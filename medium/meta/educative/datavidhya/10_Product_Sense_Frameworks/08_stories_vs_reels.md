# Stories vs Reels - Resource Allocation

## Problem
You're asked: how should we compare Stories and Reels, and allocate eng
investment between them?

## How to Think
1. **Common axes** – DAU, time, retention, revenue.
2. **Differentiated purpose** – Stories = intimacy, Reels = discovery.
3. **Differentiated metrics** – depth, half-life, content lifetime.
4. **Allocation** – marginal ROI per $, discounted by strategic value.

## How to Remember
- **Compare on common; differentiate on purpose.**
- **Allocation = opportunity cost** of NOT investing in the other.

## Common Comparison Axes
- DAU
- Time spent
- Engagement rate
- D7/D30 retention
- Creator-side engagement
- Revenue per DAU

## Differentiated Metrics
| Axis | Stories | Reels |
|---|---|---|
| Purpose | Intimacy / close friends | Discovery / entertainment |
| Depth | % viewers who DM the poster | % views on first-time-seen creator |
| Half-life | hours (ephemeral) | days-weeks (long-tail) |
| Frequency | active posting per user | passive consumption per user |

## Allocation Framework
- Inputs: incremental DAU per $1M, incremental revenue per $1M, strategic value.
- Method: marginal ROI per surface, discounted by strategic value.
- Guard: don't fully defund either (network effects, brand).

## SQL (Side-by-Side)
```sql
SELECT event_date, surface,
       COUNT(DISTINCT user_id)                              AS dau,
       SUM(time_spent_ms) / 1000.0 / COUNT(DISTINCT user_id) AS avg_seconds_per_dau
FROM events
WHERE event_date >= CURRENT_DATE - INTERVAL '28' DAY
GROUP BY event_date, surface
ORDER BY event_date, surface;
```

## Common Mistakes
- Comparing only DAU (different purposes).
- Ignoring long-tail half-life (Reels keeps paying back).
- Fully defunding one surface (kills network effects).

## AI Use Cases
- Counterfactual "what-if we invested $5M more in Reels?" model.
- Auto dashboards comparing surfaces on common+specific axes.
- Embedding similarity of content consumption patterns.
