-- realtime-crypto-sentiment — continuous aggregates
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
--
-- 1-minute refresh; query via tweets_1m / prices_1m.

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

-- prices per minute (first/last/vwap)
CREATE MATERIALIZED VIEW IF NOT EXISTS prices_1m
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 minute', ts) AS bucket,
    symbol,
    FIRST(price_usd, ts)        AS open,
    LAST(price_usd, ts)         AS close,
    MAX(price_usd)              AS high,
    MIN(price_usd)              AS low,
    SUM(volume_usd)             AS total_volume,
    SUM(price_usd * volume_usd) / NULLIF(SUM(volume_usd), 0) AS vwap
FROM prices
GROUP BY bucket, symbol
WITH NO DATA;

SELECT add_continuous_aggregate_policy('prices_1m',
    start_offset => INTERVAL '1 hour',
    end_offset   => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute',
    if_not_exists => TRUE);
