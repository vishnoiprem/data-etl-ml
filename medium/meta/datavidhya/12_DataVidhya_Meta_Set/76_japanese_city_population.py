"""
Q76: Japanese City Population Sum   [Easy | Aggregate Functions]
DataVidhya slug: japanese-city-population-sum

Total population of all cities with countrycode 'JPN'. One row, one column,
aliased `Total Population`.

How to Think:
- The simplest question in the set: filter, then SUM. No GROUP BY, because the
  output is a single scalar over the whole filtered set.
- The only thing to get right is the output column NAME, which contains a
  SPACE. That needs backticks in Spark (double quotes in Postgres, square
  brackets in T-SQL) -- unquoted, it parses as two columns and fails.

The trap:
- COUNT vs SUM. `COUNT(population)` returns 3 (the number of Japanese cities),
  not 18095023. Both are plausible-looking integers in an "aggregate" question.
- The alias must match exactly, including the space and capitalisation. The
  site's expected output header renders as "TOTAL POPULATION" but the spec says
  `Total Population`; SQL identifiers are case-insensitive in Spark, so either
  reads back the same -- the SPACE is the part that actually matters.
- An empty filter result returns one row of NULL (aggregates over no rows), not
  zero rows and not 0. Worth knowing; asserted below.

Spark note:
- `WHERE countrycode = 'JPN'` is sargable and prunes if the table is partitioned
  by country. The SUM is a single-partition final aggregate.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("76-japanese-city-population")
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


COUNTRY = "JPN"

# ---------------------------------------------------------- sample data
# Exactly the rows DataVidhya ships with the question.
# Tokyo + Osaka + Kyoto are JPN; Seoul (KOR) and Paris (FRA) are not.
spark.sql("""
CREATE OR REPLACE TEMP VIEW jcp_city_pop AS
SELECT * FROM VALUES
    (1, 'Tokyo', 'JPN', 'Kanto',         13929286),
    (2, 'Osaka', 'JPN', 'Kansai',         2691167),
    (3, 'Seoul', 'KOR', 'Seoul',          9776000),
    (4, 'Kyoto', 'JPN', 'Kansai',         1474570),
    (5, 'Paris', 'FRA', 'Ile-de-France',  2138551)
AS t(Id, Name, COUNTRYCODE, DISTRICT, POPULATION)
""")

from pyspark.sql import functions as F

# The alias contains a space -> backticks in Spark.
SQL = f"""
SELECT SUM(POPULATION) AS `Total Population`
FROM jcp_city_pop
WHERE COUNTRYCODE = '{COUNTRY}'
"""

spark.sql(SQL).show(truncate=False)

expect("Q76 total Japanese city population", SQL, [(18095023,)])

# DataFrame API equivalent.
df = (spark.table("jcp_city_pop")
      .filter(F.col("COUNTRYCODE") == COUNTRY)
      .agg(F.sum("POPULATION").alias("Total Population")))
assert [tuple(r) for r in df.collect()] == [(18095023,)]
assert df.columns == ["Total Population"], df.columns
print("[PASS] Q76 DataFrame API matches SQL")

# ------------------------------------------------ verify by hand
assert 13929286 + 2691167 + 1474570 == 18095023
print("[PASS] Q76 13929286 + 2691167 + 1474570 = 18095023")

# ------------------------------------------------ SUM vs COUNT
both = spark.sql(f"""
SELECT SUM(POPULATION) AS total, COUNT(POPULATION) AS cities
FROM jcp_city_pop WHERE COUNTRYCODE = '{COUNTRY}'
""").collect()[0]
assert (both[0], both[1]) == (18095023, 3), both
print("[PASS] Q76 SUM gives 18095023; COUNT gives 3 (the number of cities)")

# ------------------------------------------------ the filter matters
unfiltered = spark.sql("SELECT SUM(POPULATION) FROM jcp_city_pop").collect()[0][0]
assert unfiltered == 30009574, unfiltered
print("[PASS] Q76 without the JPN filter the total is 30009574")

# ------------------------------------------------ the space in the alias
try:
    spark.sql("SELECT SUM(POPULATION) AS Total Population FROM jcp_city_pop").collect()
    raise AssertionError("expected an unquoted alias with a space to fail parsing")
except Exception as e:
    assert type(e).__name__ != "AssertionError", e
    print("[PASS] Q76 an unquoted alias containing a space fails to parse")

# ------------------------------------------------ an empty filter yields one NULL row
spark.sql("""
CREATE OR REPLACE TEMP VIEW jcp_city_pop AS
SELECT * FROM VALUES
    (3, 'Seoul', 'KOR', 'Seoul', 9776000)
AS t(Id, Name, COUNTRYCODE, DISTRICT, POPULATION)
""")
expect("Q76 no JPN cities -> one row of NULL, not zero rows and not 0", SQL, [(None,)])
