-- 03_bars_5m.sql
-- Aggregate the `stock.ticks` Kafka stream into 5-minute OHLCV bars and write
-- them to TimescaleDB table `bars_5m` via JDBC sink.
--
-- Same open/close approximation strategy as 02_bars_1m.sql (ROW_NUMBER over the
-- TUMBLE partition, ordered by event-time). Each job file is self-contained
-- for sql-client submission, so the Kafka source is redeclared here.

CREATE TABLE ticks_source_5m (
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

CREATE TABLE bars_5m_sink (
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
  'table-name' = 'bars_5m',
  'username' = 'stocks',
  'password' = 'stocks',
  'driver' = 'org.postgresql.Driver',
  'sink.buffer-flush.max-rows' = '500',
  'sink.buffer-flush.interval' = '5 s'
);

INSERT INTO bars_5m_sink
WITH ranked AS (
  SELECT ticker,
         TO_TIMESTAMP(ts)                                  AS event_ts,
         price,
         volume,
         ROW_NUMBER() OVER (
           PARTITION BY ticker, TUMBLE(TO_TIMESTAMP(ts), INTERVAL '5' MINUTE)
           ORDER BY TO_TIMESTAMP(ts) ASC
         ) AS rn_first,
         ROW_NUMBER() OVER (
           PARTITION BY ticker, TUMBLE(TO_TIMESTAMP(ts), INTERVAL '5' MINUTE)
           ORDER BY TO_TIMESTAMP(ts) DESC
         ) AS rn_last
  FROM ticks_source_5m
)
SELECT ticker,
       TUMBLE_START(event_ts, INTERVAL '5' MINUTE)          AS bar_ts,
       SUM(CASE WHEN rn_first = 1 THEN price ELSE 0 END)    AS open,
       MAX(price)                                           AS high,
       MIN(price)                                           AS low,
       SUM(CASE WHEN rn_last  = 1 THEN price ELSE 0 END)    AS close,
       SUM(volume)                                          AS volume
FROM ranked
GROUP BY ticker,
         TUMBLE(event_ts, INTERVAL '5' MINUTE);
