-- realtime-x-sentiment — continuous aggregates
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
--
-- The Live tab charts hourly and daily sentiment for every tracked tag.
-- Querying `tweets` directly on every dashboard reload is wasteful: with
-- 90 days of retention and ~12 tags scraping every 5 min, the underlying
-- hypertable holds ~310k rows and the per-tag `time_bucket` scan is the
-- most expensive thing the dashboard does.
--
-- These three continuous aggregates pre-compute the (bucket, symbol)
-- breakdown at 1-minute, 1-hour, and 1-day resolution. The
-- application-side queries in `global_sentiment_buckets` and
-- `per_symbol_buckets` (src/store/db.py) keep the parameter-driven
-- `time_bucket(:width, ts)` shape so SQLite tests still work; in
-- production the dashboard can opt in to the pre-aggregated tables.
--
-- All three use `WITH NO DATA` so the initial apply is a no-op. The
-- policies below backfill continuously and catch up on the first run.

-- tweets per minute, per symbol
CREATE MATERIALIZED VIEW IF NOT EXISTS tweets_1m
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 minute', ts) AS bucket,
    symbol,
    COUNT(*)                    AS tweet_count,
    COUNT(DISTINCT author)      AS unique_authors,
    AVG(sentiment_score)        AS avg_sentiment,
    SUM(likes)                  AS total_likes,
    SUM(retweets)               AS total_retweets
FROM tweets
WHERE sentiment_score IS NOT NULL
GROUP BY bucket, symbol
WITH NO DATA;

SELECT add_continuous_aggregate_policy('tweets_1m',
    start_offset => INTERVAL '1 hour',
    end_offset   => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute',
    if_not_exists => TRUE);

-- tweets per hour, per symbol (powers the Live tab's "Hourly" chart)
CREATE MATERIALIZED VIEW IF NOT EXISTS tweets_1h
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', ts) AS bucket,
    symbol,
    COUNT(*)                    AS tweet_count,
    COUNT(DISTINCT author)      AS unique_authors,
    AVG(sentiment_score)        AS avg_sentiment,
    SUM(likes)                  AS total_likes,
    SUM(retweets)               AS total_retweets
FROM tweets
WHERE sentiment_score IS NOT NULL
GROUP BY bucket, symbol
WITH NO DATA;

SELECT add_continuous_aggregate_policy('tweets_1h',
    start_offset => INTERVAL '7 days',
    end_offset   => INTERVAL '1 hour',
    schedule_interval => INTERVAL '15 minutes',
    if_not_exists => TRUE);

-- tweets per day, per symbol (powers the Live tab's "Daily" chart and
-- the Top-10 trending topics leaderboard)
CREATE MATERIALIZED VIEW IF NOT EXISTS tweets_1d
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', ts) AS bucket,
    symbol,
    COUNT(*)                    AS tweet_count,
    COUNT(DISTINCT author)      AS unique_authors,
    AVG(sentiment_score)        AS avg_sentiment,
    SUM(likes)                  AS total_likes,
    SUM(retweets)               AS total_retweets
FROM tweets
WHERE sentiment_score IS NOT NULL
GROUP BY bucket, symbol
WITH NO DATA;

SELECT add_continuous_aggregate_policy('tweets_1d',
    start_offset => INTERVAL '60 days',
    end_offset   => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE);
