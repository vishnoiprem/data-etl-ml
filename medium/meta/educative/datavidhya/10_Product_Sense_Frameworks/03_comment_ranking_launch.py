"""
Problem 03: Launch a new comment ranking algorithm.

Meta flavor: Product launch + experimentation framework. Show how to set
goals, pick metrics, design the A/B, plan the rollout.

How to Think:
- North Star: high-quality conversations (meaningful comment threads).
- Primary metric: % threads with >= 3 replies; reply-rate per comment.
- Secondary: time-to-first-reply, comment length, positive reactions.
- Counter: hides bad comments, slower moderation, creator dissatisfaction.
- Rollout: 1% -> 5% -> 25% -> 100% with daily guardrail checks.

How to Remember:
- "NSM -> Primary -> Secondary -> Counter -> Rollout plan."
- A/B needs: randomization unit, MDE, power, duration, guardrails.

AI Use Cases:
- Auto-generated experiment design templates.
- Sequential monitoring with always-valid p-values.
- Driver-tree for ranking changes.
"""
NORTH_STAR = "% threads with >= 3 unique commenters (meaningful thread)"

PRIMARY = ["% threads reaching 3+ unique commenters", "replies per top-level comment"]
SECONDARY = [
    "Median time to first reply (seconds)",
    "Avg comment word count",
    "Positive reaction rate on comments",
    "% users who wrote >= 1 comment in week",
]
COUNTER = [
    "Hide / report rate on comments",
    "Creator complaints volume",
    "Moderation queue growth",
    "Mean comment-position for high-quality replies (regression check)",
]

EXPERIMENT = {
    "unit":          "user_id",
    "split":         "50/50",
    "duration":      "4 weeks",
    "mde":           "+2% relative on primary",
    "power":         0.8,
    "alpha":         0.05,
    "guardrails":    ["reply latency p95", "report rate", "creator NPS"],
}

ROLLOUT = [
    ("Day 0-2",   "1%  ramp",  ["primary metric", "guardrails"]),
    ("Day 3-7",   "5%  ramp",  ["primary", "secondary", "guardrails"]),
    ("Day 8-14",  "25% ramp",  ["all metrics", "subgroup analysis"]),
    ("Day 15-28", "100% ramp", ["holdout analysis", "long-term effects"]),
]

# SQL for the primary metric
SQL_PRIMARY = """
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
"""
