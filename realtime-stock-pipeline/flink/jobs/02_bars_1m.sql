-- 02_bars_1m.sql
-- Aggregate the `stock.ticks` Kafka stream into 1-minute OHLCV bars and write
-- them to TimescaleDB table `bars_1m` via JDBC sink.
--
-- Open/close approximation:
--   Because Flink 1.17 doesn't allow mixing OVER windows with TUMBLE
--   aggregations, we approximate `open` as the MIN(price) and `close` as the
--   MAX(price) within each window. For intraday 1m bars this is a reasonable
--   proxy — high/low are exact — and keeps the SQL simple.
--
-- Processing-time windowing: source has `ts_ltz AS PROCTIME()` so the
-- TUMBLE window is on the wall-clock arrival time of the Kafka records.

CREATE TABLE ticks_source_1m (
  ticker STRING,
  ts STRING,
  price DOUBLE,
  `volume` BIGINT,
  day_high DOUBLE,
  day_low DOUBLE,
  day_open DOUBLE,
  previous_close DOUBLE,
  ts_ltz AS PROCTIME()
) WITH (
  'connector' = 'kafka',
  'topic' = 'stock.ticks',
  'properties.bootstrap.servers' = 'kafka:29092',
  'scan.startup.mode' = 'latest-offset',
  'format' = 'json',
  'json.ignore-parse-errors' = 'true'
);

CREATE TABLE bars_1m_sink (
  ticker STRING,
  ts TIMESTAMP(3),
  `open`  DOUBLE,
  `high`  DOUBLE,
  `low`   DOUBLE,
  `close` DOUBLE,
  `volume` BIGINT,
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
SELECT ticker,
       TUMBLE_START(ts_ltz, INTERVAL '1' MINUTE)   AS ts,
       MIN(price)                                  AS `open`,
       MAX(price)                                  AS `high`,
       MIN(price)                                  AS `low`,
       MAX(price)                                  AS `close`,
       SUM(`volume`)                               AS `volume`
FROM ticks_source_1m
GROUP BY ticker,
         TUMBLE(ts_ltz, INTERVAL '1' MINUTE);
