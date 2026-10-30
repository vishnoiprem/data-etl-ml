"""
Problem 01: Measure the health of Facebook Groups.

Meta flavor: Product-sense interview walk-through. The interviewer wants a
structured framework: define the goal, propose a North Star + supporting
metrics, segment users, write a SQL skeleton, then describe an experiment.

How to Think:
- Define the product mission first (Groups = "meaningful communities").
- Pick ONE North Star, then 3-5 supporting metrics across the AAARR funnel.
- Segment: active posters, lurkers, new joiners, admins.
- Counter-metric: moderation load, spam reports.

How to Remember:
- "Goal -> North Star -> Inputs -> Counter-metrics -> SQL -> Experiment."
- North Star for Groups: Weekly Meaningful Communities (active groups
  with >= 5 weekly contributors).

AI Use Cases:
- Auto-generate product-health dashboards.
- Anomaly alerts on North Star movement.
- Driver-tree decomposition of NSM changes.
"""
# Goal
GOAL = "Make every Facebook Group a 'meaningful community' for its members."

# North Star Metric
NORTH_STAR = "Weekly Meaningful Communities (active groups w/ >= 5 contributors/week)"

# Supporting metrics (Acquisition -> Activation -> Retention -> Revenue -> Referral)
SUPPORTING = {
    "acquisition": "New group joins / day, group-creation rate per active user",
    "activation":  "% new joiners who post/comment within D7",
    "retention":   "D7/D30 retention of contributors, weekly active contributors",
    "referral":    "Invites sent per active member, invite -> join conversion",
    "health":      "% groups with >= 5 weekly active contributors",
}

# Counter-metrics (so we don't optimize the wrong thing)
COUNTER_METRICS = [
    "Spam reports per 1k posts",
    "Admin moderation time / week",
    "% groups flagged as low-quality",
    "Member opt-out rate from group notifications",
]

# SQL skeleton (Presto)
SQL = """
WITH weekly_contrib AS (
    SELECT group_id, DATE_TRUNC('week', event_ts) AS wk,
           COUNT(DISTINCT actor_id) AS contributors
    FROM group_events
    WHERE event_type IN ('post','comment','reaction')
      AND event_ts >= CURRENT_DATE - INTERVAL '8' DAY
    GROUP BY 1, 2
)
SELECT wk,
       COUNT(DISTINCT group_id) AS n_groups,
       SUM(CASE WHEN contributors >= 5 THEN 1 ELSE 0 END) AS meaningful_groups,
       SUM(CASE WHEN contributors >= 5 THEN 1 ELSE 0 END) * 1.0
         / COUNT(DISTINCT group_id) AS pct_meaningful
FROM weekly_contrib
GROUP BY wk
ORDER BY wk DESC;
"""

# Experiment: A/B test "suggested groups" recommendation surface
EXPERIMENT = {
    "hypothesis":     "Better group suggestions -> +3% D7 active contributors",
    "primary_metric": "D7 active contributors per joiner",
    "guardrails":     ["unsubscribe rate", "spam reports"],
    "design":         "user-level randomisation, 50/50, 4-week ramp",
}
