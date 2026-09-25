-- 03_bars_5m.sql
-- Aggregate the `stock.ticks` Kafka stream into 5-minute OHLCV bars and write
-- them to TimescaleDB table `bars_5m` via JDBC sink.
--
-- Same open/close approximation as 02_bars_1m.sql (MIN/MAX as proxies — exact
-- first/last requires OVER windows, which Flink 1.17 disallows with TUMBLE).

CREATE TABLE ticks_source_5m (
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

CREATE TABLE bars_5m_sink (
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
  'table-name' = 'bars_5m',
  'username' = 'stocks',
  'password' = 'stocks',
  'driver' = 'org.postgresql.Driver',
  'sink.buffer-flush.max-rows' = '500',
  'sink.buffer-flush.interval' = '5 s'
);

INSERT INTO bars_5m_sink
SELECT ticker,
       TUMBLE_START(ts_ltz, INTERVAL '5' MINUTE)   AS ts,
       MIN(price)                                  AS `open`,
       MAX(price)                                  AS `high`,
       MIN(price)                                  AS `low`,
       MAX(price)                                  AS `close`,
       SUM(`volume`)                               AS `volume`
FROM ticks_source_5m
GROUP BY ticker,
         TUMBLE(ts_ltz, INTERVAL '5' MINUTE);
