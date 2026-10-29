# Detect Bot Network Inflating Engagement

## Problem
Walk through how you'd detect a coordinated bot network inflating engagement
metrics.

## How to Think
1. **Signals** – temporal, network, device, behavioral, content, graph.
2. **Combine** multiple weak signals into one strong detector.
3. **Validate** by manual review of high-confidence clusters.
4. **Action** – quarantine, rollback, notify, retrain.

## How to Remember
- **"Bots cluster in time, network, behavior."**
- **One signal = noise; combined = detection.**

## Detection Signals
| Signal | Description |
|---|---|
| Temporal | Burst of N actions within M seconds from many accounts |
| Network | Tightly connected component with mutual engagement |
| Device | Shared device fingerprint / IP subnet |
| Behavioral | No photo, no bio, no friends, only reactions |
| Content | Near-duplicate comments / reactions |
| Graph | High clustering coefficient + low path diversity |

## SQL (Candidate Accounts - Behavioral)
```sql
WITH acc AS (
    SELECT user_id,
           DATEDIFF(day, created_at, CURRENT_DATE) AS account_age_days,
           (profile_pic_flag = 0) AS no_pic,
           (bio_flag = 0)        AS no_bio,
           (friend_count < 5)    AS few_friends
    FROM users
),
eng AS (
    SELECT user_id,
           COUNT(*) AS actions_30d,
           COUNT(*) * 1.0 / NULLIF(DATEDIFF(day, MIN(event_ts), MAX(event_ts))+1, 0)
             AS actions_per_active_day
    FROM events
    WHERE event_ts >= CURRENT_DATE - INTERVAL '30' DAY
    GROUP BY user_id
)
SELECT a.user_id,
       a.account_age_days, a.no_pic, a.no_bio, a.few_friends,
       e.actions_30d, e.actions_per_active_day
FROM acc a JOIN eng e USING (user_id)
WHERE a.no_pic = 1 AND a.no_bio = 1 AND a.few_friends = 1
  AND e.actions_30d > 1000
ORDER BY e.actions_30d DESC;
```

## Code (Mutual Engagement Graph Signal)
```python
from collections import defaultdict

def mutual_engagement_score(edges):
    fwd = defaultdict(set)
    for u, v in edges:
        fwd[u].add(v)
    score = {}
    for u, vs in fwd.items():
        for v in vs:
            if u in fwd.get(v, set()):
                score[(min(u,v), max(u,v))] = score.get((min(u,v), max(u,v)), 0) + 1
    return score
```

## Follow-up Actions
- Auto-quarantine high-confidence clusters.
- Roll back inflated engagement metrics.
- Notify impacted advertisers / partners.
- Feed confirmed cases back into the detection model.

## Common Mistakes
- Single-signal detection (high false positives).
- Forgetting to roll back inflated metrics.
- Not feeding confirmed cases back into the model.

## AI Use Cases
- Graph neural networks for fake-account clusters.
- Anomaly detection on engagement velocity per cohort.
- LLM-based text similarity for spam campaigns.
