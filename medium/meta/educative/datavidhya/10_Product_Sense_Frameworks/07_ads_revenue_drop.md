# Ads Revenue Dropped 3% WoW - Root-Cause Playbook

## Problem
Ads revenue is down 3% WoW. Walk the interviewer through root-cause.

## How to Think
1. **Decompose** revenue into multiplicative components.
2. **Identify** which component fell.
3. **Hypothesize** drivers of that component.
4. **Validate** with data.
5. **Act** with playbook.

## How to Remember
- **Revenue = Impressions x CPM x Fill_Rate x CTR.**
- Decompose FIRST, then hypothesize.

## Decomposition
| Component | What it captures |
|---|---|
| Impressions | ad delivery volume |
| CPM | price per 1k impressions |
| Fill rate | % ad slots that got a paid bid |
| CTR | click-through rate |

## Hypotheses
| Hypothesis | Validation |
|---|---|
| Macro / seasonality | Compare to historical Q4 baselines |
| Advertiser budget cut | Top 20 advertisers' spend WoW |
| Auction dynamics | Bid landscape, reserve-price changes |
| Policy / sensitive verticals | Recent ad-policy updates |
| Competitor launch | TikTok / Google Ads news |
| Bug | Tracking pixel failure, delivery error rates |

## SQL (Decompose WoW)
```sql
SELECT wk,
       SUM(impressions)                              AS imps,
       SUM(revenue) / NULLIF(SUM(impressions),0)*1000 AS cpm,
       SUM(revenue) / NULLIF(SUM(billed_imps),0)*1000 AS billed_cpm,
       SUM(billed_imps) * 1.0 / NULLIF(SUM(impressions),0) AS fill_rate
FROM ad_events
WHERE wk >= CURRENT_DATE - INTERVAL '8' DAY
GROUP BY wk
ORDER BY wk DESC;
```

## Action Playbook
- **CPM down** -> outreach top advertisers, check reserve-price floors.
- **Fill down** -> investigate auction liquidity, expand demand.
- **Imps down** -> check ads-density policy, engagement drops.
- **Always** -> post-mortem + alert tuning.

## Common Mistakes
- Looking only at total revenue, no decomposition.
- Ignoring macro / seasonality.
- No counterfactual (would revenue have dropped anyway?).

## AI Use Cases
- Anomaly detection on each sub-component.
- Causal driver-tree attribution.
- Auction simulation under changed bid landscape.
