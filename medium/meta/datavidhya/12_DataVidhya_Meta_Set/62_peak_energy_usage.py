"""
Q62: Peak Energy Usage Period   [Medium | Aggregate Functions, Union]
DataVidhya slug: peak-energy-usage-period

Three regional tables with identical shape. Total consumption per date across
all three, return the single highest date; earliest date wins a tie.

How to Think:
- Three tables, one schema -> UNION ALL them into one stream, then GROUP BY
  date. This is the "vertically partitioned by region" pattern, and UNION ALL is
  the only thing that reunifies it.
- Then it is a top-1 with a deterministic tiebreak: ORDER BY total DESC, date
  ASC, LIMIT 1.

The trap:
- UNION ALL, never UNION. UNION dedupes, and Asia and EU BOTH record 400 on
  2020-01-01. UNION would collapse those two identical (date, consumption) rows
  into one and report 800 for Jan 1 instead of 1050. This is the whole question,
  and it is silent -- 800 is a perfectly plausible number.
- Dates appear in only SOME tables. Jan 5 exists only in Asia (1200) and that is
  the winner; Jan 6 only in NA. A three-way INNER JOIN on date would keep only
  Jan 1 and Jan 2 (the dates present in all three) and miss the answer entirely.
  FULL OUTER JOIN would work but needs COALESCE on every key and every value --
  UNION ALL is strictly simpler.
- The tie rule (earliest date) must be an explicit second sort key, or the
  result is non-deterministic when two dates share the max.
- Do not SUM across regions with a join; that fans out.

Spark note:
- UNION ALL is a no-shuffle append; the GROUP BY is the only exchange. Three
  small scans beat any join formulation here.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("62-peak-energy-usage")
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


# ---------------------------------------------------------- sample data
# Exactly the rows DataVidhya ships with the question.
# Asia and EU both record 400 on 2020-01-01 -- identical rows UNION would eat.
# Jan 5 exists ONLY in Asia and is the winning date.
spark.sql("""
CREATE OR REPLACE TEMP VIEW pec_asia_energy AS
SELECT * FROM VALUES
    (DATE'2020-01-01',  400),
    (DATE'2020-01-02',  400),
    (DATE'2020-01-04',  675),
    (DATE'2020-01-05', 1200)
AS t(date, consumption)
""")
spark.sql("""
CREATE OR REPLACE TEMP VIEW pec_eu_energy AS
SELECT * FROM VALUES
    (DATE'2020-01-01', 400),
    (DATE'2020-01-02', 350),
    (DATE'2020-01-03', 500),
    (DATE'2020-01-04', 500)
AS t(date, consumption)
""")
spark.sql("""
CREATE OR REPLACE TEMP VIEW pec_na_energy AS
SELECT * FROM VALUES
    (DATE'2020-01-01', 250),
    (DATE'2020-01-02', 375),
    (DATE'2020-01-03', 600),
    (DATE'2020-01-06', 500)
AS t(date, consumption)
""")

from pyspark.sql import functions as F

SQL = """
WITH all_regions AS (
    SELECT date, consumption FROM pec_asia_energy
    UNION ALL                                   -- ALL: identical rows must survive
    SELECT date, consumption FROM pec_eu_energy
    UNION ALL
    SELECT date, consumption FROM pec_na_energy
)
SELECT date,
       SUM(consumption) AS total_consumption
FROM all_regions
GROUP BY date
ORDER BY total_consumption DESC, date           -- earliest date breaks the tie
LIMIT 1
"""

spark.sql(SQL).show(truncate=False)

import datetime as dt

expect("Q62 peak consumption date", SQL, [(dt.date(2020, 1, 5), 1200)])

# DataFrame API equivalent.
all_regions = (spark.table("pec_asia_energy")
               .unionAll(spark.table("pec_eu_energy"))
               .unionAll(spark.table("pec_na_energy")))
df = (all_regions.groupBy("date")
      .agg(F.sum("consumption").alias("total_consumption"))
      .orderBy(F.col("total_consumption").desc(), F.col("date"))
      .limit(1))
assert [tuple(r) for r in df.collect()] == [(dt.date(2020, 1, 5), 1200)]
print("[PASS] Q62 DataFrame API matches SQL")

# ------------------------------------------------ show every daily total
totals = spark.sql("""
WITH all_regions AS (
    SELECT date, consumption FROM pec_asia_energy
    UNION ALL SELECT date, consumption FROM pec_eu_energy
    UNION ALL SELECT date, consumption FROM pec_na_energy
)
SELECT date, SUM(consumption) AS total FROM all_regions GROUP BY date ORDER BY date
""").collect()
assert [(str(r[0]), r[1]) for r in totals] == [
    ("2020-01-01", 1050), ("2020-01-02", 1125), ("2020-01-03", 1100),
    ("2020-01-04", 1175), ("2020-01-05", 1200), ("2020-01-06", 500),
], totals
print(f"[PASS] Q62 daily totals: {[(str(r[0]), r[1]) for r in totals]}")

# ------------------------------------------------ the UNION trap
# Asia's and EU's identical (2020-01-01, 400) rows collapse under UNION.
dedup = spark.sql("""
WITH all_regions AS (
    SELECT date, consumption FROM pec_asia_energy
    UNION SELECT date, consumption FROM pec_eu_energy
    UNION SELECT date, consumption FROM pec_na_energy
)
SELECT date, SUM(consumption) AS total FROM all_regions
WHERE date = DATE'2020-01-01' GROUP BY date
""").collect()[0]
assert (str(dedup[0]), dedup[1]) == ("2020-01-01", 650), dedup
print("[PASS] Q62 UNION collapses the duplicate 400 -> Jan 1 reports 650, not 1050")

# ------------------------------------------------ the INNER JOIN trap
# Only Jan 1 and Jan 2 appear in all three tables; the winner is lost.
inner = spark.sql("""
SELECT a.date, a.consumption + e.consumption + n.consumption AS total
FROM pec_asia_energy a
JOIN pec_eu_energy e ON e.date = a.date
JOIN pec_na_energy n ON n.date = a.date
ORDER BY total DESC, a.date
""").collect()
assert [(str(r[0]), r[1]) for r in inner] == [
    ("2020-01-02", 1125), ("2020-01-01", 1050),
], inner
print("[PASS] Q62 three-way INNER JOIN keeps only 2 dates and misses Jan 5 entirely")

# ------------------------------------------------ the tie rule
# Make Jan 3 tie with Jan 5 at 1200; the EARLIER date must win.
spark.sql("""
CREATE OR REPLACE TEMP VIEW pec_na_energy AS
SELECT * FROM VALUES
    (DATE'2020-01-01', 250),
    (DATE'2020-01-02', 375),
    (DATE'2020-01-03', 700),
    (DATE'2020-01-06', 500)
AS t(date, consumption)
""")
expect("Q62 tie resolves to the earliest date", SQL, [(dt.date(2020, 1, 3), 1200)])

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 supports the same UNION ALL + GROUP BY + ORDER BY ... LIMIT 1
# pattern verbatim. UNION (without ALL) would dedupe Asia's and EU's
# identical (2020-01-01, 400) row -- the test below shows it losing 400.
#
# CREATE TABLE pec_asia_energy (
#     date         DATE NOT NULL,
#     consumption  INT  NOT NULL,
#     PRIMARY KEY (date)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# CREATE TABLE pec_eu_energy (
#     date         DATE NOT NULL,
#     consumption  INT  NOT NULL,
#     PRIMARY KEY (date)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# CREATE TABLE pec_na_energy (
#     date         DATE NOT NULL,
#     consumption  INT  NOT NULL,
#     PRIMARY KEY (date)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO pec_asia_energy (date, consumption) VALUES
#     ('2020-01-01',  400), ('2020-01-02',  400),
#     ('2020-01-04',  675), ('2020-01-05', 1200);
#
# INSERT INTO pec_eu_energy (date, consumption) VALUES
#     ('2020-01-01', 400), ('2020-01-02', 350),
#     ('2020-01-03', 500), ('2020-01-04', 500);
#
# INSERT INTO pec_na_energy (date, consumption) VALUES
#     ('2020-01-01', 250), ('2020-01-02', 375),
#     ('2020-01-03', 600), ('2020-01-06', 500);
#
# WITH all_regions AS (
#     SELECT date, consumption FROM pec_asia_energy
#     UNION ALL
#     SELECT date, consumption FROM pec_eu_energy
#     UNION ALL
#     SELECT date, consumption FROM pec_na_energy
# )
# SELECT date, SUM(consumption) AS total_consumption
# FROM all_regions
# GROUP BY date
# ORDER BY total_consumption DESC, date
# LIMIT 1;
#
# -- Expected: ('2020-01-05', 1200).
