# Onboarding New Users - D1-D30 Funnel

## Problem
Design and interpret the new-user onboarding funnel from signup to D30.

## How to Think
1. **Stages** – signup -> profile -> first friend -> first post -> first engagement -> D7 -> D30.
2. **Compute** – stage counts + stage-to-stage conversion.
3. **Identify** – the biggest drop-off (biggest leakage point).
4. **Hypothesize** – what's blocking users.
5. **A/B** – test the intervention.

## How to Remember
- **"Stage -> conversion -> biggest drop -> A/B."**
- **Highly segment-dependent**: country, source, device all matter.

## Funnel Stages
1. signup
2. profile_complete
3. first_friend_added
4. first_post
5. first_engagement_received
6. D7_active
7. D30_active

## SQL (Stage Counts)
```sql
WITH stage_events AS (
    SELECT user_id,
           MAX(CASE WHEN event='signup' THEN 1 ELSE 0 END) AS s1,
           MAX(CASE WHEN event='profile_complete' THEN 1 ELSE 0 END) AS s2,
           MAX(CASE WHEN event='first_friend_added' THEN 1 ELSE 0 END) AS s3,
           MAX(CASE WHEN event='first_post' THEN 1 ELSE 0 END) AS s4,
           MAX(CASE WHEN event='first_engagement_received' THEN 1 ELSE 0 END) AS s5,
           MAX(CASE WHEN event='d7_active' THEN 1 ELSE 0 END) AS s6,
           MAX(CASE WHEN event='d30_active' THEN 1 ELSE 0 END) AS s7
    FROM onboarding_events
    WHERE signup_date >= CURRENT_DATE - INTERVAL '60' DAY
    GROUP BY user_id
)
SELECT 's1_signup' AS stage, SUM(s1) AS users FROM stage_events UNION ALL
SELECT 's2_profile', SUM(s2) FROM stage_events UNION ALL
SELECT 's3_friend',  SUM(s3) FROM stage_events UNION ALL
SELECT 's4_post',    SUM(s4) FROM stage_events UNION ALL
SELECT 's5_engage',  SUM(s5) FROM stage_events UNION ALL
SELECT 's6_d7',      SUM(s6) FROM stage_events UNION ALL
SELECT 's7_d30',     SUM(s7) FROM stage_events
ORDER BY stage;
```

## Interventions by Stage
| Drop | Intervention |
|---|---|
| signup -> profile | Simpler flow, skip optional fields |
| profile -> friend | Suggest contacts, address-book import |
| friend -> post | Pre-fill first post, friend-activity nudge |
| post -> engagement | "Who viewed you" spark return |
| D7 -> D30 | Push notifications, weekly digest, social proof |

## Code (Biggest Drop Identifier)
```python
def biggest_drop(stage_counts):
    drops = []
    for i in range(1, len(stage_counts)):
        prev, curr = stage_counts[i-1], stage_counts[i]
        if prev > 0:
            drops.append((f"s{i+1}_vs_s{i}", (prev - curr) / prev))
    return max(drops, key=lambda x: x[1])
```

## Common Mistakes
- One-size-fits-all funnel (forget country/device segmentation).
- Optimising only the biggest drop without long-term ROI lens.
- Ignoring the QUALITY of users passing each stage.

## AI Use Cases
- Auto-detection of biggest stage drop + root-cause hints.
- Personalised onboarding via ML (which path for which user).
- Causal A/B evaluation of intervention impact.
