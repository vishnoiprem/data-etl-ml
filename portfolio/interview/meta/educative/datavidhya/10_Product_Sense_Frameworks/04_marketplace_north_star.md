# Marketplace Health - North Star + Supporting Metrics

## Problem
Define the North Star and supporting metrics for Facebook Marketplace.

## How to Think
1. **Goal** – liquidity in two-sided marketplace.
2. **NSM** – successful connections (transactions or qualified contacts).
3. **Buyer-side** – acquisition, activation, retention, conversion.
4. **Seller-side** – same funnel + listings-to-sale lag.
5. **Counter** – fraud, dead inventory, CSAT.

## How to Remember
- **Liquidity = # successful matches / # listings.**
- **Always** track both sides of the marketplace.

## Buyer-side Metrics
| Stage | Metric |
|---|---|
| Acquisition | new buyers / wk, listing views per buyer |
| Activation | % new buyers contacting a seller in D7 |
| Retention | W4 repeat-purchase rate |
| Conversion | contact-to-purchase rate |

## Seller-side Metrics
| Stage | Metric |
|---|---|
| Acquisition | new listings / wk |
| Activation | % new sellers getting first contact in D7 |
| Retention | W4 active-seller rate |
| Liquidity | median days-to-sale, listings-to-sale conversion |

## Counter-metrics
- Scam / fraud report rate
- Listing takedown rate
- % listings with no views after 7 days
- Buyer NPS / Seller CSAT

## SQL (Liquidity by Region + Category)
```sql
SELECT wk, category, region,
       COUNT(DISTINCT listing_id)             AS listings,
       COUNT(DISTINCT transaction_id)         AS transactions,
       COUNT(DISTINCT transaction_id) * 1.0
         / NULLIF(COUNT(DISTINCT listing_id),0) AS liquidity_ratio,
       APPROX_PERCENTILE(DATEDIFF(day, listed_at, sold_at), 0.5)
         AS median_days_to_sale
FROM marketplace_events
WHERE wk >= CURRENT_DATE - INTERVAL '8' DAY
GROUP BY wk, category, region
ORDER BY wk DESC, liquidity_ratio ASC;
```

## Common Mistakes
- Tracking only buyer OR only seller side.
- Conflating "listings" with "engagement" (vanity).
- Ignoring regional cold-start.

## AI Use Cases
- Liquidity dashboards by sub-market.
- Cold-start detection (regional supply/demand imbalance).
- Pricing recommendation A/B.
