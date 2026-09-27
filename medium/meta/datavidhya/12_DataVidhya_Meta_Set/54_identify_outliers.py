"""
Q54: Identify and Handle Outliers   [Medium | Mathematical Functions]
DataVidhya slug: identify-outliers

Per sensor: Q1/Q3 with linear interpolation, then Tukey fences
lower = Q1 - 1.5*IQR and upper = Q3 + 1.5*IQR (each rounded to 2dp). Flag every
reading 0/1 against ITS OWN sensor's fences. Every reading is returned.

How to Think:
- Two grains again: the FENCES are per sensor (an aggregate), the FLAG is per
  reading (a row-level test). So aggregate per sensor in a CTE, then join the
  fences back onto the readings. Every row survives and carries its sensor's
  bounds -- that repetition is required, not redundant.
- Tukey's rule is the standard outlier definition; say the name. It is
  distribution-free, which is why ops teams use it on sensor data instead of
  mean +/- 3 sigma (a single 147.2 reading drags the mean and the sd with it,
  so a sigma rule hides the very outlier you are hunting).
- Fences are ROUNDED BEFORE the comparison, per the spec. Comparing against
  unrounded fences can flip a borderline reading.

The trap:
- Per-sensor, not fleet-wide. S001 sits around 30 and S002 around 60, so global
  fences would flag half of S001 as low and miss real anomalies. "Each sensor
  has its own normal range" is the first line of the question.
- `percentile()` interpolates; `percentile_approx()` returns a real data point.
  Same distinction as Q42, and here it moves the fences.
- `value` is DECIMAL, and Spark's `percentile` needs a numeric it can
  interpolate -- cast to DOUBLE or the arithmetic comes back as unexpected
  decimal scale.
- `timestamp` must be TEXT in 'yyyy-MM-dd HH:mm:ss' (Java pattern), not the
  Postgres 'HH24:MI:SS' the question writes. Same translation as Q44.
- `timestamp` is also a SQL keyword used as a column name -- backtick it.
- The flag is strictly OUTSIDE the fences (`<` and `>`); a reading exactly on a
  fence is not an outlier.

Spark note:
- `percentile` is exact so it buffers each sensor's values. The fences CTE is
  tiny, so joining it back broadcasts.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("54-identify-outliers")
         .master("local[2]")
         .config("spark.sql.shuffle.partitions", "2")
         .config("spark.ui.showConsoleProgress", "false")
         .getOrCreate())
spark.sparkContext.setLogLevel("ERROR")


def expect(title, sql, expected_rows):
    """Run a query and assert its exact rows, in order. Decimal/float safe."""
    import decimal

    def norm(v):
        if isinstance(v, decimal.Decimal):
            return float(v)
        if isinstance(v, float):
            return round(v, 6)
        return v

    got = [tuple(norm(c) for c in r) for r in spark.sql(sql).collect()]
    exp = [tuple(norm(c) for c in r) for r in expected_rows]
    if got != exp:
        print(f"[FAIL] {title}")
        print(f"   expected: {exp}")
        print(f"   got:      {got}")
        raise AssertionError(title)
    print(f"[PASS] {title}")
    return got


IQR_MULTIPLIER = 1.5   # Tukey's fence

# ---------------------------------------------------------- sample data
# Exactly the rows DataVidhya ships with the question.
# S001 normally ~30 with one spike at 113.03; S002 normally ~60 with one at 147.2.
spark.sql("""
CREATE OR REPLACE TEMP VIEW sensor_readings AS
SELECT * FROM VALUES
    ( 1, 'S001', TIMESTAMP'2024-01-01 00:00:00', CAST( 30.24 AS DECIMAL(10,2))),
    ( 2, 'S001', TIMESTAMP'2024-01-01 01:00:00', CAST( 36.94 AS DECIMAL(10,2))),
    ( 3, 'S001', TIMESTAMP'2024-01-01 02:00:00', CAST( 34.05 AS DECIMAL(10,2))),
    ( 4, 'S001', TIMESTAMP'2024-01-01 03:00:00', CAST(113.03 AS DECIMAL(10,2))),
    ( 5, 'S001', TIMESTAMP'2024-01-01 04:00:00', CAST( 29.28 AS DECIMAL(10,2))),
    (10, 'S002', TIMESTAMP'2024-01-01 00:00:00', CAST( 58.97 AS DECIMAL(10,2))),
    (11, 'S002', TIMESTAMP'2024-01-01 01:00:00', CAST( 60.25 AS DECIMAL(10,2))),
    (12, 'S002', TIMESTAMP'2024-01-01 02:00:00', CAST( 61.83 AS DECIMAL(10,2))),
    (13, 'S002', TIMESTAMP'2024-01-01 03:00:00', CAST(147.20 AS DECIMAL(10,2))),
    (14, 'S002', TIMESTAMP'2024-01-01 04:00:00', CAST( 55.69 AS DECIMAL(10,2)))
AS t(reading_id, sensor_id, `timestamp`, value)
""")

from pyspark.sql import functions as F

SQL = f"""
WITH fences AS (
    -- per-sensor grain: one row of bounds per sensor
    SELECT sensor_id,
           ROUND(PERCENTILE(CAST(value AS DOUBLE), 0.25)
                 - {IQR_MULTIPLIER} * (PERCENTILE(CAST(value AS DOUBLE), 0.75)
                                     - PERCENTILE(CAST(value AS DOUBLE), 0.25)), 2) AS lower_bound,
           ROUND(PERCENTILE(CAST(value AS DOUBLE), 0.75)
                 + {IQR_MULTIPLIER} * (PERCENTILE(CAST(value AS DOUBLE), 0.75)
                                     - PERCENTILE(CAST(value AS DOUBLE), 0.25)), 2) AS upper_bound
    FROM sensor_readings
    GROUP BY sensor_id
)
SELECT r.reading_id,
       r.sensor_id,
       DATE_FORMAT(r.`timestamp`, 'yyyy-MM-dd HH:mm:ss') AS `timestamp`,
       r.value,
       CASE WHEN r.value < f.lower_bound OR r.value > f.upper_bound
            THEN 1 ELSE 0 END AS is_outlier,
       f.lower_bound,
       f.upper_bound
FROM sensor_readings r
JOIN fences f ON f.sensor_id = r.sensor_id
ORDER BY r.reading_id
"""

spark.sql(SQL).show(truncate=False)


def ts(hour):
    return f"2024-01-01 0{hour}:00:00"


EXPECTED = [
    ( 1, "S001", ts(0),  30.24, 0, 20.19, 46.99),
    ( 2, "S001", ts(1),  36.94, 0, 20.19, 46.99),
    ( 3, "S001", ts(2),  34.05, 0, 20.19, 46.99),
    ( 4, "S001", ts(3), 113.03, 1, 20.19, 46.99),
    ( 5, "S001", ts(4),  29.28, 0, 20.19, 46.99),
    (10, "S002", ts(0),  58.97, 0, 54.68, 66.12),
    (11, "S002", ts(1),  60.25, 0, 54.68, 66.12),
    (12, "S002", ts(2),  61.83, 0, 54.68, 66.12),
    (13, "S002", ts(3), 147.20, 1, 54.68, 66.12),
    (14, "S002", ts(4),  55.69, 0, 54.68, 66.12),
]
expect("Q54 per-sensor Tukey outlier flags", SQL, EXPECTED)

# DataFrame API equivalent.
q1 = F.expr("percentile(cast(value as double), 0.25)")
q3 = F.expr("percentile(cast(value as double), 0.75)")
fences = (spark.table("sensor_readings").groupBy("sensor_id")
          .agg(q1.alias("q1"), q3.alias("q3"))
          .withColumn("iqr", F.col("q3") - F.col("q1"))
          .select("sensor_id",
                  F.round(F.col("q1") - IQR_MULTIPLIER * F.col("iqr"), 2).alias("lower_bound"),
                  F.round(F.col("q3") + IQR_MULTIPLIER * F.col("iqr"), 2).alias("upper_bound")))
df = (spark.table("sensor_readings").alias("r")
      .join(F.broadcast(fences.alias("f")), "sensor_id")
      .select(F.col("reading_id"),
              F.col("sensor_id"),
              F.date_format("timestamp", "yyyy-MM-dd HH:mm:ss").alias("timestamp"),
              F.col("value"),
              F.when((F.col("value") < F.col("lower_bound")) |
                     (F.col("value") > F.col("upper_bound")), 1).otherwise(0).alias("is_outlier"),
              F.col("lower_bound"), F.col("upper_bound"))
      .orderBy("reading_id"))
assert [(r[0], r[1], r[2], float(r[3]), r[4], float(r[5]), float(r[6]))
        for r in df.collect()] == EXPECTED
print("[PASS] Q54 DataFrame API matches SQL")

# ------------------------------------------------ verify the fences by hand
# S002 sorted: 55.69, 58.97, 60.25, 61.83, 147.20. n=5.
# Q1 position = 0.25*(5-1) = 1 -> 58.97 exactly. Q3 position = 3 -> 61.83.
iqr = 61.83 - 58.97
assert round(58.97 - 1.5 * iqr, 2) == 54.68
assert round(61.83 + 1.5 * iqr, 2) == 66.12
print(f"[PASS] Q54 hand-computed S002 fences: 54.68 / 66.12 (IQR {round(iqr, 2)})")

# ------------------------------------------------ every reading survives
assert spark.sql(SQL).count() == spark.table("sensor_readings").count() == 10
print("[PASS] Q54 10 readings in, 10 rows out -- flagged, not filtered")

# ------------------------------------------------ the fleet-wide trap
# Pooling both sensors gives fences roughly 5x wider than S001's own. On the
# shipped data the two extreme spikes still clear even that, so global fences
# coincidentally catch them -- the damage shows on a merely-anomalous reading.
GLOBAL_FENCE_SQL = """
WITH f AS (
    SELECT ROUND(PERCENTILE(CAST(value AS DOUBLE), 0.25)
                 - 1.5*(PERCENTILE(CAST(value AS DOUBLE), 0.75)
                      - PERCENTILE(CAST(value AS DOUBLE), 0.25)), 2) AS lo,
           ROUND(PERCENTILE(CAST(value AS DOUBLE), 0.75)
                 + 1.5*(PERCENTILE(CAST(value AS DOUBLE), 0.75)
                      - PERCENTILE(CAST(value AS DOUBLE), 0.25)), 2) AS hi
    FROM sensor_readings
)
SELECT SUM(CASE WHEN r.value < f.lo OR r.value > f.hi THEN 1 ELSE 0 END) AS flagged, f.lo, f.hi
FROM sensor_readings r CROSS JOIN f GROUP BY f.lo, f.hi
"""
g = spark.sql(GLOBAL_FENCE_SQL).collect()[0]
assert (g[0], float(g[1]), float(g[2])) == (2, -5.22, 101.43), g
print(f"[PASS] Q54 fleet-wide fences are ({g[1]}, {g[2]}) -- ~5x wider than S001's "
      f"(20.19, 46.99), though both spikes still clear them here")

# Replace S001's 113.03 spike with 90.0: clearly abnormal for a ~30C sensor,
# but comfortably inside the pooled fence of 101.43.
spark.sql("""
CREATE OR REPLACE TEMP VIEW sensor_readings AS
SELECT * FROM VALUES
    ( 1, 'S001', TIMESTAMP'2024-01-01 00:00:00', CAST( 30.24 AS DECIMAL(10,2))),
    ( 2, 'S001', TIMESTAMP'2024-01-01 01:00:00', CAST( 36.94 AS DECIMAL(10,2))),
    ( 3, 'S001', TIMESTAMP'2024-01-01 02:00:00', CAST( 34.05 AS DECIMAL(10,2))),
    ( 4, 'S001', TIMESTAMP'2024-01-01 03:00:00', CAST( 90.00 AS DECIMAL(10,2))),
    ( 5, 'S001', TIMESTAMP'2024-01-01 04:00:00', CAST( 29.28 AS DECIMAL(10,2))),
    (10, 'S002', TIMESTAMP'2024-01-01 00:00:00', CAST( 58.97 AS DECIMAL(10,2))),
    (11, 'S002', TIMESTAMP'2024-01-01 01:00:00', CAST( 60.25 AS DECIMAL(10,2))),
    (12, 'S002', TIMESTAMP'2024-01-01 02:00:00', CAST( 61.83 AS DECIMAL(10,2))),
    (13, 'S002', TIMESTAMP'2024-01-01 03:00:00', CAST(147.20 AS DECIMAL(10,2))),
    (14, 'S002', TIMESTAMP'2024-01-01 04:00:00', CAST( 55.69 AS DECIMAL(10,2)))
AS t(reading_id, sensor_id, `timestamp`, value)
""")

per_sensor_flags = spark.sql(f"SELECT SUM(is_outlier) FROM ({SQL})").collect()[0][0]
g2 = spark.sql(GLOBAL_FENCE_SQL).collect()[0]
assert (per_sensor_flags, g2[0]) == (2, 1), (per_sensor_flags, g2[0])
print(f"[PASS] Q54 a 90.0 reading on a ~30C sensor: per-sensor flags 2, "
      f"fleet-wide ({g2[1]}, {g2[2]}) flags only 1 -- the anomaly is missed")

# ------------------------------------------------ the mean +/- 3-sigma trap
sigma_flags = spark.sql("""
WITH s AS (
    SELECT sensor_id, AVG(CAST(value AS DOUBLE)) AS mu, STDDEV(CAST(value AS DOUBLE)) AS sd
    FROM sensor_readings GROUP BY sensor_id
)
SELECT SUM(CASE WHEN ABS(r.value - s.mu) > 3 * s.sd THEN 1 ELSE 0 END) AS flagged
FROM sensor_readings r JOIN s ON s.sensor_id = r.sensor_id
""").collect()[0][0]
assert sigma_flags == 0, sigma_flags
print("[PASS] Q54 mean +/- 3-sigma flags 0 -- the outlier inflates the sd that should catch it")

# ------------------------------------------------ percentile_approx moves the fences
# Restore the shipped rows -- the trap above replaced S001's spike.
spark.sql("""
CREATE OR REPLACE TEMP VIEW sensor_readings AS
SELECT * FROM VALUES
    ( 1, 'S001', TIMESTAMP'2024-01-01 00:00:00', CAST( 30.24 AS DECIMAL(10,2))),
    ( 2, 'S001', TIMESTAMP'2024-01-01 01:00:00', CAST( 36.94 AS DECIMAL(10,2))),
    ( 3, 'S001', TIMESTAMP'2024-01-01 02:00:00', CAST( 34.05 AS DECIMAL(10,2))),
    ( 4, 'S001', TIMESTAMP'2024-01-01 03:00:00', CAST(113.03 AS DECIMAL(10,2))),
    ( 5, 'S001', TIMESTAMP'2024-01-01 04:00:00', CAST( 29.28 AS DECIMAL(10,2))),
    (10, 'S002', TIMESTAMP'2024-01-01 00:00:00', CAST( 58.97 AS DECIMAL(10,2))),
    (11, 'S002', TIMESTAMP'2024-01-01 01:00:00', CAST( 60.25 AS DECIMAL(10,2))),
    (12, 'S002', TIMESTAMP'2024-01-01 02:00:00', CAST( 61.83 AS DECIMAL(10,2))),
    (13, 'S002', TIMESTAMP'2024-01-01 03:00:00', CAST(147.20 AS DECIMAL(10,2))),
    (14, 'S002', TIMESTAMP'2024-01-01 04:00:00', CAST( 55.69 AS DECIMAL(10,2)))
AS t(reading_id, sensor_id, `timestamp`, value)
""")

approx = spark.sql("""
SELECT sensor_id,
       PERCENTILE_APPROX(CAST(value AS DOUBLE), 0.25) AS q1_approx,
       PERCENTILE(CAST(value AS DOUBLE), 0.25)        AS q1_exact
FROM sensor_readings GROUP BY sensor_id ORDER BY sensor_id
""").collect()
assert [(r[0], float(r[1]), float(r[2])) for r in approx] == [
    ("S001", 30.24, 30.24), ("S002", 58.97, 58.97),
], approx
print("[PASS] Q54 at n=5, approx and exact agree -- Q1 position 0.25*(5-1) = 1 is an "
      "integer, so no interpolation happens and the functions cannot diverge")

# Add a 6th reading to S001: now Q1 position = 0.25*5 = 1.25 falls BETWEEN two
# values, interpolation kicks in, and percentile_approx stops matching.
spark.sql("""
CREATE OR REPLACE TEMP VIEW sensor_readings AS
SELECT * FROM VALUES
    ( 1, 'S001', TIMESTAMP'2024-01-01 00:00:00', CAST( 30.24 AS DECIMAL(10,2))),
    ( 2, 'S001', TIMESTAMP'2024-01-01 01:00:00', CAST( 36.94 AS DECIMAL(10,2))),
    ( 3, 'S001', TIMESTAMP'2024-01-01 02:00:00', CAST( 34.05 AS DECIMAL(10,2))),
    ( 4, 'S001', TIMESTAMP'2024-01-01 03:00:00', CAST(113.03 AS DECIMAL(10,2))),
    ( 5, 'S001', TIMESTAMP'2024-01-01 04:00:00', CAST( 29.28 AS DECIMAL(10,2))),
    ( 6, 'S001', TIMESTAMP'2024-01-01 05:00:00', CAST( 32.00 AS DECIMAL(10,2)))
AS t(reading_id, sensor_id, `timestamp`, value)
""")
n6 = spark.sql("""
SELECT PERCENTILE_APPROX(CAST(value AS DOUBLE), 0.25) AS q1_approx,
       PERCENTILE(CAST(value AS DOUBLE), 0.25)        AS q1_exact
FROM sensor_readings WHERE sensor_id = 'S001'
""").collect()[0]
assert (float(n6[0]), float(n6[1])) == (30.24, 30.68), n6
print("[PASS] Q54 at n=6 the position is fractional: approx gives 30.24, "
      "exact interpolates to 30.68")
