# Ads Impressions + Clicks + Spend

## Problem
Meta Ads Manager lets advertisers run campaigns across Facebook,
Instagram, Messenger, and Audience Network. Advertisers want to
analyze impressions, clicks, conversions, and spend per campaign,
ad set, ad creative, surface, device, and audience. The model must
support CTR, CVR, CPM, CPC, ROAS calculations and feed ML bidding.

## How to Think
1. List the metrics:
   - Impressions, clicks, conversions per ad per surface.
   - Spend, revenue, ROAS per campaign.
   - Reach and frequency per audience.
   - CTR = clicks / impressions, CVR = conversions / clicks.
2. Identify the grain - one row = one (ad, user, day, surface, placement).
   Aggregating at this grain keeps BI fast and ML feature-ready.
3. Pick fact-table type: transactional snapshot rolled up to the
   (ad, user, day) level - too granular for raw event-grain storage.
4. Design dimensions and SCD choices:
   - `dim_ad` SCD2 because creatives are rotated frequently and
     historical creative attributes matter for learning.
   - `dim_advertiser` SCD2 (industry reassignments).
   - `dim_campaign` SCD2 (budgets change).
   - `dim_surface`, `dim_device`, `dim_placement` SCD1 lookups.

## How to Remember
- **Pattern**: "Consolidated ad-performance fact + SCD2 dims."
- **Grain mnemonic**: "One row = one ad-user-day-surface combo."
- Use NULL `user_key` for anonymous impressions to keep reach honest.

## Schema (DDL)
```sql
CREATE TABLE fact_ad_performance (
  ad_perf_key   BIGINT PRIMARY KEY,
  ad_key BIGINT, advertiser_key BIGINT, campaign_key BIGINT,
  user_key BIGINT,                -- NULL for anonymous
  date_key INT, time_key INT,
  surface_key BIGINT, device_key BIGINT, placement_key BIGINT,
  impressions INT, clicks INT, conversions INT,
  spend_usd DECIMAL(12,4), revenue_usd DECIMAL(12,4),
  reach_count INT, frequency DECIMAL(6,2)
);
-- dim_ad (SCD2), dim_advertiser (SCD2), dim_campaign (SCD2),
-- dim_surface (SCD1), dim_device (SCD1), dim_placement (SCD1).
```

## Common Mistakes
- Three separate facts for impressions/clicks/spend - explodes joins.
- Storing CTR or ROAS as columns (calculated metrics must stay derived).
- Modeling campaign budget as a fact measure when it's an attribute.

## AI Use Cases
- Bid optimization (pCTR, pCVR features from user/device/surface).
- Anomaly detection on spend spikes per advertiser.
- Lookalike modeling from converter demographics + surface mix.
