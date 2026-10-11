-- realtime-x-sentiment — continuous aggregates
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
--
-- 1-minute refresh; query via tweets_1m.

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