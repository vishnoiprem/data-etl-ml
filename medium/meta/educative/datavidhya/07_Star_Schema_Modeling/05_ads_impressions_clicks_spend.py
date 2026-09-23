"""
Problem 05: Ads Impressions + Clicks + Spend
Meta product: "Meta Ads Manager - Campaign Analytics"

How to Think:
- Three metrics per grain (impression, click, spend) - modeled as one
  consolidated ad-performance fact with flags and measures.
- Grain: one ad-event (impression, click, or conversion) per user per
  ad. Spend is aggregated up but can be prorated to impression grain.
- Use a fact table with measure columns: impressions, clicks, spend,
  conversions - all numeric - and a date_key for time analysis.

How to Remember:
- For ad performance, prefer a single consolidated fact over three
  separate facts (avoid join explosions).
- Spend per impression is a derived metric at query time.
- Add factless rows for "ad shown but no engagement" to keep CTR honest.

AI Use Cases
- Auction / bid optimization models use CTR and CVR features.
- Anomaly detection on sudden spend spikes.
- Lookalike audience modeling from converter demographics.
"""

DDL = """
-- fact_ad_performance: one row per (ad, user, day, surface) - rolled up
CREATE TABLE fact_ad_performance (
  ad_perf_key        BIGINT PRIMARY KEY,
  ad_key             BIGINT NOT NULL,
  advertiser_key     BIGINT NOT NULL,
  campaign_key       BIGINT NOT NULL,
  user_key           BIGINT,                -- NULL = anonymous impression
  date_key           INT    NOT NULL,
  time_key           INT,
  surface_key        BIGINT,                -- feed / reels / stories / search
  device_key         BIGINT,
  placement_key      BIGINT,
  impressions        INT DEFAULT 0,
  clicks             INT DEFAULT 0,
  conversions        INT DEFAULT 0,
  spend_usd          DECIMAL(12,4) DEFAULT 0,
  revenue_usd        DECIMAL(12,4) DEFAULT 0,
  reach_count        INT DEFAULT 0,         -- unique users
  frequency          DECIMAL(6,2)
);

-- dim_ad (SCD2 - creatives rotate frequently)
CREATE TABLE dim_ad (
  ad_key             BIGINT PRIMARY KEY,
  ad_id              VARCHAR(64),
  campaign_key       BIGINT,
  creative_type      VARCHAR(30),           -- image, video, carousel, collection
  objective          VARCHAR(40),           -- awareness, traffic, conversion
  effective_from     DATE,
  effective_to       DATE,
  is_current         BOOLEAN
);

-- dim_advertiser (SCD2)
CREATE TABLE dim_advertiser (
  advertiser_key     BIGINT PRIMARY KEY,
  advertiser_id      VARCHAR(64),
  industry           VARCHAR(100),
  effective_from     DATE, effective_to DATE, is_current BOOLEAN
);

-- dim_campaign (SCD2)
CREATE TABLE dim_campaign (
  campaign_key       BIGINT PRIMARY KEY,
  campaign_id        VARCHAR(64),
  campaign_name      VARCHAR(200),
  start_date         DATE, end_date         DATE,
  daily_budget_usd   DECIMAL(12,4),
  effective_from DATE, effective_to DATE, is_current BOOLEAN
);

-- dim_surface (SCD1), dim_device (SCD1), dim_placement (SCD1).
"""