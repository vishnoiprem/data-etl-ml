"""
Problem 07: Ads revenue dropped 3% week-over-week - root-cause playbook.

Meta flavor: Decompose revenue = impressions * CPM * fill_rate * click_rate.
Each component can drop independently. Walk through triage.

How to Think:
- Revenue = sum(impressions * cpm) per ad.
- Decompose: impressions, CPM, fill rate, click-through.
- Hypotheses: auction dynamics, advertiser budget cycles, policy,
  competitor launch, macro-economy, seasonality.

How to Remember:
- "Revenue = Impressions x CPM x Fill x CTR."
- Always decompose into MULTIPLICATIVE components.

AI Use Cases:
- Anomaly detection on each revenue sub-component.
- Auto root-cause via causal driver-tree.
- Auction simulation under changed bid landscape.
"""
REVENUE_EQ = "Revenue = Impressions x CPM x Fill_Rate x CTR"

DECOMPOSITION = [
    ("Impressions",   "ad delivery volume - can drop if ranker de-prioritises ads"),
    ("CPM",           "price per 1k - can drop if advertisers lower bids / budgets"),
    ("Fill rate",     "% ad slots filled - can drop if auction has fewer bidders"),
    ("CTR",           "click-through - affects ranking quality, not raw revenue"),
]

HYPOTHESES = [
    ("Macro / seasonality",       "Check Q4 vs Q3 historical baselines, holiday calendar."),
    ("Advertiser budget cut",     "Top 20 advertisers' spend WoW."),
    ("Auction dynamics",          "Bid landscape, reserve-price changes."),
    ("Policy / sensitive content","Recent ad-policy update blocking verticals (e.g. finance)."),
    ("Competitor (TikTok Ads)",   "Market-share shifts."),
    ("Bug",                       "Tracking pixel failures, ads-delivery error rates."),
]

SQL_DECOMPOSE = """
SELECT wk,
       SUM(impressions)                              AS imps,
       SUM(revenue) / NULLIF(SUM(impressions),0)*1000 AS cpm,
       SUM(revenue) / NULLIF(SUM(billed_imps),0)*1000 AS billed_cpm,
       SUM(billed_imps) * 1.0 / NULLIF(SUM(impressions),0) AS fill_rate
FROM ad_events
WHERE wk >= CURRENT_DATE - INTERVAL '8' DAY
GROUP BY wk
ORDER BY wk DESC;
"""

ACTION_PLAYBOOK = {
    "if_cpm_down":      "Outreach to top advertisers; check reserve-price floors.",
    "if_fill_down":     "Investigate auction liquidity; expand demand sources.",
    "if_imps_down":     "Check ads-density policy, engagement drops, ranking changes.",
    "always":           "Post-mortem + alert tuning + revenue-driver dashboard.",
}
