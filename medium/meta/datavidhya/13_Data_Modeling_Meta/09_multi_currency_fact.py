"""
Q47: How do you model a multi-currency fact table?
Article: "50 Data Modeling Interview Questions for DEs" — Warehouse Design

Meta flavor: "Ads revenue is billed in 40+ local currencies. Finance wants USD
totals; regional teams want their own currency; and last quarter's USD number
must not move when today's FX rate moves."

How to Think:
- Store THREE things on the fact, and say why each is needed:
    local_amount    the amount as billed (the source of truth)
    currency_code   FK to the currency dimension
    (derived) usd_amount, computed via the rate ON THE TRANSACTION DATE
- Never store ONLY the converted amount. Rates get restated, finance changes the
  reporting currency, and you can no longer re-derive anything. Keeping the
  local amount means every future question is still answerable.
- The rate dimension is SNAPSHOTTED: one row per currency per DAY. That is what
  makes historical totals STABLE -- a March total computed today and computed
  next year give the same answer, because both look up the March rate.
- Keep both columns in the serving layer. Regional teams read local_amount,
  finance reads usd_amount, and neither has to know about the other.

The trap (this is the question):
- USING A SINGLE "CURRENT" RATE. It is the intuitive shortcut and it makes every
  historical report MOVE whenever FX moves -- so last quarter's closed revenue
  changes overnight and finance stops trusting the warehouse. Asserted below
  with a rate change, showing the same quarter reporting two different totals.
- The rate join needs BOTH currency_code AND the date. Joining on currency alone
  fans the fact out to one row per rate-day: with 3 days of rates, revenue
  triples. Silent, and the number still looks like money.
- A MISSING rate (weekend, holiday, new currency) makes the converted amount
  NULL, and SUM skips NULLs -- so the USD total quietly under-reports while the
  local total is right. Either forward-fill the rate dimension to every calendar
  day or LEFT JOIN and alert on unmatched rows. Asserted.
- USD rows need a rate too (1.0). Omitting them from the rate dimension drops
  your largest market.
- Rounding: convert at full precision and round ONCE at presentation. Rounding
  per row then summing drifts from rounding the sum.

Spark note:
- The rate dimension is small (currencies x days) and broadcasts. Materialise
  usd_amount on write so downstream queries never re-join FX.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("09-multi-currency-fact")
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


from pyspark.sql import functions as F

# ---------------------------------------------------------- snapshotted rates
# One row per currency PER DAY. Note USD is present with rate 1.0.
spark.sql("""
CREATE OR REPLACE TEMP VIEW dim_exchange_rate AS
SELECT * FROM VALUES
    ('USD', DATE'2026-03-01', CAST(1.000000 AS DECIMAL(18,6))),
    ('EUR', DATE'2026-03-01', CAST(1.080000 AS DECIMAL(18,6))),
    ('INR', DATE'2026-03-01', CAST(0.012000 AS DECIMAL(18,6))),
    ('USD', DATE'2026-03-02', CAST(1.000000 AS DECIMAL(18,6))),
    ('EUR', DATE'2026-03-02', CAST(1.090000 AS DECIMAL(18,6))),
    ('INR', DATE'2026-03-02', CAST(0.011900 AS DECIMAL(18,6)))
AS t(currency_code, rate_date, rate_to_usd)
""")

# ---------------------------------------------------------- the fact
# local_amount + currency_code. usd_amount is DERIVED, never the only column.
spark.sql("""
CREATE OR REPLACE TEMP VIEW fact_ad_revenue AS
SELECT * FROM VALUES
    (1, 'USD', DATE'2026-03-01', CAST(1000.00 AS DECIMAL(18,2))),
    (2, 'EUR', DATE'2026-03-01', CAST( 500.00 AS DECIMAL(18,2))),
    (3, 'INR', DATE'2026-03-01', CAST(90000.00 AS DECIMAL(18,2))),
    (4, 'EUR', DATE'2026-03-02', CAST( 500.00 AS DECIMAL(18,2)))
AS t(revenue_id, currency_code, revenue_date, local_amount)
""")

# Join on currency AND date -- both, or the fact fans out.
CONVERTED = """
SELECT f.revenue_id,
       f.currency_code,
       f.revenue_date,
       f.local_amount,
       ROUND(f.local_amount * er.rate_to_usd, 2) AS usd_amount
FROM fact_ad_revenue f
JOIN dim_exchange_rate er
  ON er.currency_code = f.currency_code
 AND er.rate_date     = f.revenue_date
ORDER BY f.revenue_id
"""
spark.sql(CONVERTED).show(truncate=False)

import datetime as dt

D1, D2 = dt.date(2026, 3, 1), dt.date(2026, 3, 2)
expect("Q47 conversion uses the rate on the transaction date", CONVERTED, [
    (1, "USD", D1,  1000.00, 1000.00),
    (2, "EUR", D1,   500.00,  540.00),   # 500 x 1.08
    (3, "INR", D1, 90000.00, 1080.00),   # 90000 x 0.012
    (4, "EUR", D2,   500.00,  545.00),   # 500 x 1.09 -- a DIFFERENT day's rate
])

# DataFrame API equivalent.
df = (spark.table("fact_ad_revenue").alias("f")
      .join(F.broadcast(spark.table("dim_exchange_rate").alias("er")),
            (F.col("er.currency_code") == F.col("f.currency_code")) &
            (F.col("er.rate_date") == F.col("f.revenue_date")))
      .select("revenue_id", "f.currency_code", "revenue_date", "local_amount",
              F.round(F.col("local_amount") * F.col("rate_to_usd"), 2).alias("usd_amount"))
      .orderBy("revenue_id"))
assert [(r[0], r[1], r[2], float(r[3]), float(r[4])) for r in df.collect()] == [
    (1, "USD", D1, 1000.00, 1000.00),
    (2, "EUR", D1,  500.00,  540.00),
    (3, "INR", D1, 90000.00, 1080.00),
    (4, "EUR", D2,  500.00,  545.00),
]
print("[PASS] Q47 DataFrame API matches SQL")

# The same nominal 500 EUR converts differently on different days -- as it must.
eur = spark.sql(f"""
SELECT revenue_date, usd_amount FROM ({CONVERTED}) WHERE currency_code = 'EUR'
ORDER BY revenue_date
""").collect()
assert [(r[0], float(r[1])) for r in eur] == [(D1, 540.00), (D2, 545.00)], eur
print("[PASS] Q47 500 EUR -> 540.00 on Mar 1 and 545.00 on Mar 2 -- rate is per-day")

# ---------------------------------------------------------- historical stability
DAILY_TOTAL = f"""
SELECT revenue_date, ROUND(SUM(usd_amount), 2) AS usd_revenue
FROM ({CONVERTED}) GROUP BY revenue_date ORDER BY revenue_date
"""
expect("Q47 daily USD totals", DAILY_TOTAL, [(D1, 2620.00), (D2, 545.00)])

# Now FX moves: a June snapshot lands with EUR at 1.20. The March rows are
# untouched, which is exactly why history stays stable.
spark.sql("""
CREATE OR REPLACE TEMP VIEW dim_exchange_rate_extended AS
SELECT * FROM VALUES
    ('USD', DATE'2026-03-01', CAST(1.000000 AS DECIMAL(18,6))),
    ('EUR', DATE'2026-03-01', CAST(1.080000 AS DECIMAL(18,6))),
    ('INR', DATE'2026-03-01', CAST(0.012000 AS DECIMAL(18,6))),
    ('USD', DATE'2026-03-02', CAST(1.000000 AS DECIMAL(18,6))),
    ('EUR', DATE'2026-03-02', CAST(1.090000 AS DECIMAL(18,6))),
    ('INR', DATE'2026-03-02', CAST(0.011900 AS DECIMAL(18,6))),
    ('USD', DATE'2026-06-01', CAST(1.000000 AS DECIMAL(18,6))),
    ('EUR', DATE'2026-06-01', CAST(1.200000 AS DECIMAL(18,6))),
    ('INR', DATE'2026-06-01', CAST(0.010000 AS DECIMAL(18,6)))
AS t(currency_code, rate_date, rate_to_usd)
""")

# Snapshotted lookup: March totals are UNCHANGED by the June rate.
stable = spark.sql("""
SELECT ROUND(SUM(f.local_amount * er.rate_to_usd), 2) AS march_usd
FROM fact_ad_revenue f
JOIN dim_exchange_rate_extended er
  ON er.currency_code = f.currency_code AND er.rate_date = f.revenue_date
""").collect()[0][0]
assert float(stable) == 3165.00, stable
print(f"[PASS] Q47 with snapshotted rates, March total stays {stable} after FX moves")

# ---------------------------------------------------------- the current-rate trap
# Using ONE latest rate restates history every time FX moves.
current_rate = spark.sql("""
WITH latest AS (
    SELECT currency_code, rate_to_usd,
           ROW_NUMBER() OVER (PARTITION BY currency_code ORDER BY rate_date DESC) AS rn
    FROM dim_exchange_rate_extended
)
SELECT ROUND(SUM(f.local_amount * l.rate_to_usd), 2) AS march_usd_at_current_rate
FROM fact_ad_revenue f
JOIN latest l ON l.currency_code = f.currency_code AND l.rn = 1
""").collect()[0][0]
assert float(current_rate) == 3100.00, current_rate
print(f"[PASS] Q47 a single current rate restates the SAME March revenue as "
      f"{current_rate} instead of {stable} -- closed periods move")

# ---------------------------------------------------------- the fan-out trap
# Joining on currency only, ignoring the date.
fanned = spark.sql("""
SELECT COUNT(*) AS rows, ROUND(SUM(f.local_amount * er.rate_to_usd), 2) AS usd
FROM fact_ad_revenue f
JOIN dim_exchange_rate_extended er ON er.currency_code = f.currency_code
""").collect()[0]
assert (fanned[0], float(fanned[1])) == (12, 9421.00), fanned
print(f"[PASS] Q47 joining on currency alone gives {fanned[0]} rows and "
      f"{fanned[1]} USD -- 3x inflation, still looks like money")

# ---------------------------------------------------------- the missing-rate trap
# A weekend transaction with no rate row: inner join drops it, outer NULLs it.
spark.sql("""
CREATE OR REPLACE TEMP VIEW fact_ad_revenue AS
SELECT * FROM VALUES
    (1, 'USD', DATE'2026-03-01', CAST(1000.00 AS DECIMAL(18,2))),
    (5, 'EUR', DATE'2026-03-07', CAST( 800.00 AS DECIMAL(18,2)))
AS t(revenue_id, currency_code, revenue_date, local_amount)
""")
local_total = spark.sql(
    "SELECT ROUND(SUM(local_amount), 2) FROM fact_ad_revenue").collect()[0][0]
inner_usd = spark.sql("""
SELECT ROUND(SUM(f.local_amount * er.rate_to_usd), 2) AS usd
FROM fact_ad_revenue f
JOIN dim_exchange_rate_extended er
  ON er.currency_code = f.currency_code AND er.rate_date = f.revenue_date
""").collect()[0][0]
assert (float(local_total), float(inner_usd)) == (1800.00, 1000.00)
print(f"[PASS] Q47 local total {local_total} but USD only {inner_usd} -- "
      "the Mar 7 row has no rate and vanishes")

# LEFT JOIN surfaces it as an alertable NULL instead of silently dropping it.
unmatched = spark.sql("""
SELECT COUNT(*) FROM fact_ad_revenue f
LEFT JOIN dim_exchange_rate_extended er
  ON er.currency_code = f.currency_code AND er.rate_date = f.revenue_date
WHERE er.rate_to_usd IS NULL
""").collect()[0][0]
assert unmatched == 1
print("[PASS] Q47 a LEFT JOIN makes the 1 missing rate detectable -- alert on it, "
      "or forward-fill the rate dimension to every calendar day")

# ---------------------------------------------------------- forward-fill fixes it
# LAST_VALUE(... IGNORE NULLS) over a dense calendar is the Spark idiom for a
# forward fill -- a correlated "most recent rate" subquery is not supported.
spark.sql("""
CREATE OR REPLACE TEMP VIEW dim_rate_filled AS
WITH cal AS (
    SELECT explode(sequence(DATE'2026-03-01', DATE'2026-03-10', INTERVAL 1 DAY)) AS d
),
cur AS (SELECT DISTINCT currency_code FROM dim_exchange_rate_extended),
scaffold AS (
    SELECT c.currency_code, cal.d AS rate_date
    FROM cal CROSS JOIN cur c
),
sparse AS (
    SELECT s.currency_code, s.rate_date, er.rate_to_usd
    FROM scaffold s
    LEFT JOIN dim_exchange_rate_extended er
           ON er.currency_code = s.currency_code AND er.rate_date = s.rate_date
)
SELECT currency_code,
       rate_date,
       LAST_VALUE(rate_to_usd, TRUE) OVER (
           PARTITION BY currency_code ORDER BY rate_date
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
       ) AS rate_to_usd
FROM sparse
""")
filled = spark.sql("""
SELECT ROUND(SUM(f.local_amount * er.rate_to_usd), 2) AS usd
FROM fact_ad_revenue f
JOIN dim_rate_filled er
  ON er.currency_code = f.currency_code AND er.rate_date = f.revenue_date
""").collect()[0][0]
assert float(filled) == 1872.00, filled     # 1000 + 800 x 1.09 (Mar 2 carried forward)
print(f"[PASS] Q47 forward-filling the rate dimension recovers the full {filled} USD")

# ---------------------------------------------------------- round once
per_row = spark.sql("""
SELECT ROUND(SUM(ROUND(f.local_amount * er.rate_to_usd, 2)), 2) AS round_then_sum,
       ROUND(SUM(f.local_amount * er.rate_to_usd), 2)           AS sum_then_round
FROM dim_rate_filled er
JOIN fact_ad_revenue f
  ON er.currency_code = f.currency_code AND er.rate_date = f.revenue_date
""").collect()[0]
print(f"[PASS] Q47 round-then-sum {per_row[0]} vs sum-then-round {per_row[1]} "
      "-- convert at full precision, round once at presentation")
