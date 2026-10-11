-- realtime-x-sentiment — convenience views
-- Author: Prem Vishnoi <pvishnoi@avilx.com>

-- Latest signal per symbol (last 24h)
CREATE OR REPLACE VIEW latest_signals_per_symbol AS
SELECT DISTINCT ON (symbol)
    symbol, action, score, sentiment_zscore, momentum_zscore, reason, ts
FROM signals
WHERE ts > NOW() - INTERVAL '24 hours'
ORDER BY symbol, ts DESC;

-- Top 10 mentioned symbols in last 24h
CREATE OR REPLACE VIEW top_mentions_24h AS
SELECT
    symbol,
    COUNT(*)                                AS tweet_count,
    COUNT(DISTINCT author)                  AS unique_authors,
    AVG(sentiment_score)                    AS avg_sentiment,
    MAX(ts)                                 AS last_mention
FROM tweets
WHERE ts > NOW() - INTERVAL '24 hours'
  AND sentiment_score IS NOT NULL
GROUP BY symbol
ORDER BY tweet_count DESC
LIMIT 10;

-- Paper-trade log (in chronological order)
CREATE OR REPLACE VIEW paper_pnl_per_trade AS
SELECT
    pt.ts,
    pt.symbol,
    pt.side,
    pt.qty,
    pt.price,
    pt.fee,
    pt.cash_after
FROM paper_trades pt
ORDER BY pt.ts;

-- Daily PnL summary (per symbol)
CREATE OR REPLACE VIEW daily_pnl AS
SELECT
    DATE_TRUNC('day', ts) AS day,
    symbol,
    SUM(CASE WHEN side = 'SELL' THEN qty * price - fee
             WHEN side = 'BUY'  THEN -(qty * price + fee)
             ELSE 0 END) AS net_pnl,
    COUNT(*)             AS trade_count
FROM paper_trades
GROUP BY 1, 2
ORDER BY 1 DESC, 3 DESC;