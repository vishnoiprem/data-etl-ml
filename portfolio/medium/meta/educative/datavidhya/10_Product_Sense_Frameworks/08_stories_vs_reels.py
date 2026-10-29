"""
Problem 08: Stories vs Reels - how would you compare and allocate eng resources?

Meta flavor: Strategic product question. Show how to evaluate two product
surfaces with comparable + differentiated metrics.

How to Think:
- Define purpose: Stories = close friends (intimacy), Reels = discovery (reach).
- Compare on common axes: DAU, time-spent, retention.
- Differentiate on: depth of connection (DMs), discovery (% new creators).
- Trade-off: time-spent vs depth, broad reach vs targeted reach.

How to Remember:
- "Compare on common; differentiate on purpose."
- Resource allocation = opportunity cost of NOT investing in the other.

AI Use Cases:
- Counterfactual models for "what-if we invested more in X?"
- Auto-comparable dashboards across surfaces.
- Embedding-based similarity of consumed content.
"""
COMMON_AXES = ["DAU", "time spent", "engagement rate", "D7/D30 retention",
               "creator-side engagement", "revenue per DAU"]
DIFFERENTIATED = {
    "Stories": {
        "purpose":     "intimacy / close friends",
        "depth":       "% viewers who DM the poster",
        "frequency":   "postings per active user / day",
        "half-life":   "median content lifetime (hours)",
    },
    "Reels": {
        "purpose":     "discovery / entertainment",
        "depth":       "% views on creator first-time seen",
        "frequency":   "passive consumption per DAU",
        "half-life":   "long-tail content lifetime (days-weeks)",
    },
}

ALLOCATION_FRAMEWORK = {
    "inputs":  ["incremental DAU per $1M invested",
                "incremental revenue per $1M invested",
                "strategic value (network effects, brand)"],
    "method":  "Marginal ROI per surface, discounted by strategic value.",
    "guard":   "Don't fully defund either surface (network effects).",
}

# SQL: side-by-side DAU + time-spent
SQL_COMPARE = """
SELECT event_date, surface,
       COUNT(DISTINCT user_id)                              AS dau,
       SUM(time_spent_ms) / 1000.0 / COUNT(DISTINCT user_id) AS avg_seconds_per_dau
FROM events
WHERE event_date >= CURRENT_DATE - INTERVAL '28' DAY
GROUP BY event_date, surface
ORDER BY event_date, surface;
"""
