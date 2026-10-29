"""
Problem 04: Marketplace health - North Star + supporting metrics.

Meta flavor: Two-sided marketplace (buyers + sellers). Healthy marketplace =
matches that close. Walk through framework.

How to Think:
- NSM: Successful connections (transactions or high-intent contacts).
- Liquidity is the meta-goal: supply matches demand.
- Split metrics by buyer side and seller side.
- Counter: low-quality listings, scam reports, listing-to-sale lag.

How to Remember:
- "Liquidity = # successful matches / # listings."
- Two-sided metrics ALWAYS (don't only track buyers OR sellers).

AI Use Cases:
- Liquidity dashboards with market-depth views.
- Cold-start detection in regional sub-markets.
- Pricing engine A/B tests.
"""
NSM = "Weekly Successful Connections (buyer<>seller completed transactions OR qualified contacts)"

BUYER_METRICS = {
    "acquisition": "new buyers / wk, listing views / buyer",
    "activation":  "% new buyers contacting a seller in D7",
    "retention":   "W4 buyer repeat-purchase rate",
    "conversion":  "contact-to-purchase rate",
}
SELLER_METRICS = {
    "acquisition": "new seller listings / wk",
    "activation":  "% new sellers getting first contact in D7",
    "retention":   "W4 seller active rate (re-listings)",
    "liquidity":   "median days-to-sale, listings-to-sale conversion",
}
COUNTER = [
    "Scam / fraud report rate",
    "Listing takedown rate",
    "% listings with no views after 7 days (dead inventory)",
    "Buyer NPS / Seller CSAT",
]

# Liquidity ratio
SQL_LIQUIDITY = """
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
"""
