"""
Problem 02: Reels engagement dropped 5% week-over-week.

Meta flavor: Diagnostic playbook. Walk the interviewer through a structured
investigation: scope -> decompose -> hypothesize -> validate -> act.

How to Think:
- Is it real? Check data quality, definition changes, seasonality.
- Decompose by: country, surface (Feed vs Reels tab), device, cohort.
- Hypothesize: ranking change? creator supply? competitor? bug?
- Validate: correlate with ranker deploy timestamps, supply metrics, NPS.

How to Remember:
- "Scope -> Decompose -> Hypothesize -> Validate -> Act."
- Always check DATA before MODEL before PRODUCT.

AI Use Cases:
- Auto root-cause for metric drops.
- Anomaly correlation with deploy / event logs.
- Driver-tree SHAP for metric decomposition.
"""
SCOPE_CHECKS = [
    "Confirm metric definition hasn't changed (e.g., like vs like+share).",
    "Confirm event pipeline is healthy (lag, duplicates).",
    "Check seasonality (holidays, school terms, sports events).",
]

# Decomposition dimensions
DECOMPOSE = ["country", "device_os", "age_band", "acquisition_channel",
             "surface (Feed/Reels/Reels tab)", "creator tier", "video length"]

# Hypotheses
HYPOTHESES = [
    ("Ranking model regression",     "Check MSE on offline eval; correlate with deploy time."),
    ("Creator supply shock",         "Top 1% creator posting volume vs prior week."),
    ("Engagement bait classifier",   "Did we tighten policy and demote bait?"),
    ("Bug in client",                "Check client-side error rates for Reels."),
    ("External (competitor launch)", "Cross-reference with TikTok / YouTube Shorts news."),
]

# Validation queries (Presto)
SQL_VALIDATION = """
-- 1. Reels engagement by country (compare WoW)
SELECT country, wk,
       SUM(likes + comments + shares) / NULLIF(SUM(impressions), 0) AS eng_rate,
       LAG(SUM(likes + comments + shares) / NULLIF(SUM(impressions), 0))
         OVER (PARTITION BY country ORDER BY wk) AS prev_eng_rate
FROM reels_events
WHERE wk >= CURRENT_DATE - INTERVAL '14' DAY
GROUP BY country, wk
ORDER BY country, wk DESC;
"""

ACTION_PLAN = [
    "If ranking -> roll back, retrain with fresh data.",
    "If creator supply -> outreach to top creators, ship collab stickers.",
    "If bug -> hotfix, comms to users.",
    "Always: post-mortem + alert tuning + runbook update.",
]
