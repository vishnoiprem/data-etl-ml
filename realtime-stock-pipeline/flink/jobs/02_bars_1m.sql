-- 02_bars_1m.sql
-- Aggregate the `stock.ticks` Kafka stream into 1-minute OHLCV bars and write
-- them to TimescaleDB table `bars_1m` via JDBC sink.
--
-- Design choice (open / close):
--   * Flink SQL has no FIRST_VALUE / LAST_VALUE with window-frame support in
--     1.17 TUMBLE windows without ordering. We approximate `open` with the
--     price of the earliest tick in the window and `close` with the price of
--     the latest tick, using ROW_NUMBER over the window partition.
--   * ROW_NUMBER is ordered by event-time (TO_TIMESTAMP(ts)). Because Flink
--     processes ticks in event-time order within a TUMBLE window for the same
--     key, this gives the correct first/last price in practice.
--   * high/low are exact (MAX / MIN).
--
-- This job declares its own ticks_source for self-contained sql-client
-- submission. In a streaming pipeline this duplicates the source declaration
-- from 01_ticks_to_jdbc.sql, but Flink sql-client treats each file as an
-- isolated session.

CREATE TABLE ticks_source_1m (
  ticker STRING,
  ts STRING,
  price DOUBLE,
  volume BIGINT,
  day_high DOUBLE,
  day_low DOUBLE,
  day_open DOUBLE,
  previous_close DOUBLE
) WITH (
  'connector' = 'kafka',
  'topic' = 'stock.ticks',
  'properties.bootstrap.servers' = 'kafka:9092',
  'scan.startup.mode' = 'latest-offset',
  'format' = 'json',
  'json.ignore-parse-errors' = 'true'
);

CREATE TABLE bars_1m_sink (
  ticker STRING,
  ts TIMESTAMP(3),
  open  DOUBLE,
  high  DOUBLE,
  low   DOUBLE,
  close DOUBLE,
  volume BIGINT,
  PRIMARY KEY (ticker, ts) NOT ENFORCED
) WITH (
  'connector' = 'jdbc',
  'url' = 'jdbc:postgresql://timescaledb:5432/stocks',
  'table-name' = 'bars_1m',
  'username' = 'stocks',
  'password' = 'stocks',
  'driver' = 'org.postgresql.Driver',
  'sink.buffer-flush.max-rows' = '500',
  'sink.buffer-flush.interval' = '5 s'
);

INSERT INTO bars_1m_sink
WITH ranked AS (
  SELECT ticker,
         TO_TIMESTAMP(ts)                                  AS event_ts,
         price,
         volume,
         ROW_NUMBER() OVER (
           PARTITION BY ticker, TUMBLE(TO_TIMESTAMP(ts), INTERVAL '1' MINUTE)
           ORDER BY TO_TIMESTAMP(ts) ASC
         ) AS rn_first,
         ROW_NUMBER() OVER (
           PARTITION BY ticker, TUMBLE(TO_TIMESTAMP(ts), INTERVAL '1' MINUTE)
           ORDER BY TO_TIMESTAMP(ts) DESC
         ) AS rn_last
  FROM ticks_source_1m
)
SELECT ticker,
       TUMBLE_START(event_ts, INTERVAL '1' MINUTE)          AS bar_ts,
       SUM(CASE WHEN rn_first = 1 THEN price ELSE 0 END)    AS open,
       MAX(price)                                           AS high,
       MIN(price)                                           AS low,
       SUM(CASE WHEN rn_last  = 1 THEN price ELSE 0 END)    AS close,
       SUM(volume)                                          AS volume
FROM ranked
GROUP BY ticker,
         TUMBLE(event_ts, INTERVAL '1' MINUTE);
