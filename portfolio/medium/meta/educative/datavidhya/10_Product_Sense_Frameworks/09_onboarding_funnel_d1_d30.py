"""
Problem 09: Onboarding new users - D1-D30 funnel.

Meta flavor: Classic onboarding analytics. Walk through how to define the
funnel, compute it, identify biggest drop-off, design interventions.

How to Think:
- Define stages: signup -> D1 active -> D7 active -> D14 active -> D30 active.
- Or: signup -> profile complete -> 1 friend added -> 1 post -> 1 engagement.
- Compute stage-to-stage conversion.
- Identify biggest drop; hypothesize causes; A/B test fix.

How to Remember:
- "Stage -> conversion -> biggest drop -> A/B."
- Onboarding funnels are HIGHLY segment-dependent (country, source, device).

AI Use Cases:
- Auto-detection of biggest funnel drop-off.
- Personalized onboarding via ML.
- Causal inference on intervention impact.
"""
FUNNEL_STAGES = [
    "signup",
    "profile_complete",
    "first_friend_added",
    "first_post",
    "first_engagement_received",
    "D7_active",
    "D30_active",
]

# SQL: stage-to-stage conversion
SQL_FUNNEL = """
WITH stage_events AS (
    SELECT user_id,
           MAX(CASE WHEN event = 'signup' THEN 1 ELSE 0 END) AS s1,
           MAX(CASE WHEN event = 'profile_complete' THEN 1 ELSE 0 END) AS s2,
           MAX(CASE WHEN event = 'first_friend_added' THEN 1 ELSE 0 END) AS s3,
           MAX(CASE WHEN event = 'first_post' THEN 1 ELSE 0 END) AS s4,
           MAX(CASE WHEN event = 'first_engagement_received' THEN 1 ELSE 0 END) AS s5,
           MAX(CASE WHEN event = 'd7_active' THEN 1 ELSE 0 END) AS s6,
           MAX(CASE WHEN event = 'd30_active' THEN 1 ELSE 0 END) AS s7
    FROM onboarding_events
    WHERE signup_date >= CURRENT_DATE - INTERVAL '60' DAY
    GROUP BY user_id
)
SELECT 's1_signup' AS stage, SUM(s1) AS users
FROM stage_events UNION ALL
SELECT 's2_profile', SUM(s2) FROM stage_events UNION ALL
SELECT 's3_friend',  SUM(s3) FROM stage_events UNION ALL
SELECT 's4_post',    SUM(s4) FROM stage_events UNION ALL
SELECT 's5_engage',  SUM(s5) FROM stage_events UNION ALL
SELECT 's6_d7',      SUM(s6) FROM stage_events UNION ALL
SELECT 's7_d30',     SUM(s7) FROM stage_events
ORDER BY stage;
"""

INTERVENTIONS = {
    "signup->profile":    "Simpler profile flow, skip optional fields.",
    "profile->friend":    "Suggest contacts, import address book.",
    "friend->post":       "Pre-fill first post, friend activity nudge.",
    "post->engagement":   "Show 'who viewed you' to spark return.",
    "d7->d30":            "Push notifications, weekly digest, social proof.",
}

# Drop-off identification
def biggest_drop(stage_counts):
    """Return (stage_pair, drop_pct) where drop is largest."""
    drops = []
    for i in range(1, len(stage_counts)):
        prev, curr = stage_counts[i-1], stage_counts[i]
        if prev > 0:
            drops.append((f"s{i+1}_vs_s{i}", (prev - curr) / prev))
    return max(drops, key=lambda x: x[1])
