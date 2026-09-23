"""
Problem 10: Detect a bot network inflating engagement.

Meta flavor: Trust & safety / integrity analytics. Show signals, queries,
and follow-up actions.

How to Think:
- Signals: temporal clustering (bursts), IP clustering, device fingerprint,
  account age, content similarity, follower/following graph patterns.
- Graph-based: detect near-cliques with high mutual engagement.
- Anomaly: distribution drift on engagement velocity per account cohort.

How to Remember:
- "Bots cluster in time, network, behavior."
- One signal is noise; combined signals = detection.

AI Use Cases:
- Graph neural networks for fake-account detection.
- Anomaly detection on engagement velocity.
- LLM-based text similarity for spam campaigns.
"""
SIGNALS = {
    "temporal":    "burst of N actions within M seconds from many accounts",
    "network":     "tightly connected component with mutual engagement",
    "device":      "shared device fingerprint / IP subnet",
    "behavioral":  "no photo, no bio, no friends, just reactions",
    "content":     "near-duplicate comments / reactions",
    "graph":       "high clustering coefficient + low path diversity",
}

# SQL: candidate bot accounts (behavioral)
SQL_CANDIDATES = """
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
WHERE a.no_pic = 1
  AND a.no_bio = 1
  AND a.few_friends = 1
  AND e.actions_30d > 1000
ORDER BY e.actions_30d DESC;
"""

# Graph signal: tight clusters with mutual engagement (Presto + Python sketch)
def mutual_engagement_score(edges):
    """edges: list of (src, dst). Return dict of (u,v) -> mutual_count."""
    from collections import defaultdict
    fwd = defaultdict(set)
    for u, v in edges:
        fwd[u].add(v)
    score = {}
    for u, vs in fwd.items():
        for v in vs:
            if u in fwd.get(v, set()):
                score[(min(u,v), max(u,v))] = score.get((min(u,v), max(u,v)), 0) + 1
    return score

ACTIONS = [
    "Auto-quarantine high-confidence clusters.",
    "Roll back inflated metrics.",
    "Notify impacted advertisers / partners.",
    "Improve detection model with confirmed cases.",
]
