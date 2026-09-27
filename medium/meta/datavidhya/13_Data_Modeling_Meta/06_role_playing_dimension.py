"""
Q34 / Q18: Role-playing dimensions, and the date dimension's job.
Article: "50 Data Modeling Interview Questions for DEs" — Advanced / Star Schema

Meta flavor: "fact_marketplace_order has order_date, ship_date and
delivery_date. Analysts keep writing three joins to dim_date and getting
column-name collisions, or worse, joining the wrong one."

How to Think:
- ONE physical dim_date, referenced N times by the same fact with different
  foreign keys. Each reference "plays a different role". You do NOT build
  dim_order_date, dim_ship_date and dim_delivery_date as separate tables --
  that triples storage and guarantees they drift apart.
- Make the roles self-documenting with VIEWS over the one table
  (`vw_order_date`, `vw_ship_date`), each aliasing its columns with a role
  prefix. BI users then pick "Order Year" vs "Ship Year" from a list instead of
  reasoning about join order.
- While you are here, say what a date dimension is FOR: pre-computing
  fiscal_quarter, is_holiday, day_of_week, week_number ONCE so that fiscal
  calendar logic is not reimplemented slightly differently in forty queries.
  ~7300 rows for 20 years, so it fits in memory and always broadcasts.

The trap:
- WITHOUT aliasing, the three joins produce THREE columns literally named
  `year`, and `SELECT year` is ambiguous -- Spark raises, and engines that do
  not raise silently resolve to the first match. That is the bug: a report
  labelled "orders by year" that is actually grouped by DELIVERY year.
- Role-playing dimensions interact badly with NULLs. `ship_date` is NULL for an
  unshipped order, so an INNER JOIN on the ship role silently drops every
  pending order -- and "orders by order_year" comes back missing the newest
  ones. Use LEFT JOIN for optional roles, or point them at an Unknown member
  (see `08_null_fk_unknown_member.py`). Asserted below.
- Do not store the raw date INSTEAD of the key "because it is simpler". You then
  parse dates at query time, lose the fiscal calendar, and cannot filter on
  is_holiday without reimplementing a holiday list.
- The three roles must reference the SAME conformed dim_date. Two teams each
  building their own fiscal calendar is the Q16 conformed-dimension failure.

Spark note:
- dim_date is tiny, so all three joins broadcast. Keep the fact's role keys as
  INT date-keys (yyyymmdd) rather than DATE -- smaller, and they partition well.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("06-role-playing-dimension")
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


ROLES = ["order", "ship", "delivery"]

# ---------------------------------------------------------- the date dimension
# One row per day, with the derived attributes pre-computed once.
# date_key is an INT yyyymmdd, not a DATE -- smaller and it partitions cleanly.
spark.sql("""
CREATE OR REPLACE TEMP VIEW dim_date AS
SELECT CAST(date_format(d, 'yyyyMMdd') AS INT)           AS date_key,
       d                                                 AS full_date,
       YEAR(d)                                           AS year,
       QUARTER(d)                                        AS quarter,
       MONTH(d)                                          AS month,
       date_format(d, 'EEEE')                            AS day_name,
       DAYOFWEEK(d) IN (1, 7)                            AS is_weekend,
       -- Meta's fiscal year is the calendar year; a Feb-start fiscal calendar
       -- would live here so no query ever recomputes it.
       CONCAT('FY', YEAR(d), '-Q', QUARTER(d))           AS fiscal_quarter
FROM (SELECT explode(sequence(DATE'2025-12-28', DATE'2026-01-10', INTERVAL 1 DAY)) AS d)
""")
spark.table("dim_date").orderBy("date_key").show(5, truncate=False)

n_days = spark.table("dim_date").count()
assert n_days == 14, n_days
print(f"[PASS] Q18 dim_date has one row per day ({n_days} days) with derived attributes")

from pyspark.sql import functions as F

# ---------------------------------------------------------- the fact
# THREE foreign keys into the SAME dim_date. Order 4 is unshipped (NULLs).
spark.sql("""
CREATE OR REPLACE TEMP VIEW fact_marketplace_order AS
SELECT * FROM VALUES
    (1, 20251230, 20251231, 20260102, CAST(120.00 AS DECIMAL(12,2))),
    (2, 20251231, 20260102, 20260105, CAST( 80.00 AS DECIMAL(12,2))),
    (3, 20260101, 20260103, 20260106, CAST(200.00 AS DECIMAL(12,2))),
    (4, 20260102, CAST(NULL AS INT), CAST(NULL AS INT), CAST( 50.00 AS DECIMAL(12,2)))
AS t(order_id, order_date_key, ship_date_key, delivery_date_key, amount)
""")

# ---------------------------------------------------------- role views
# Each view aliases dim_date's columns with a role prefix, so joins cannot collide.
for role in ROLES:
    spark.sql(f"""
    CREATE OR REPLACE TEMP VIEW vw_{role}_date AS
    SELECT date_key        AS {role}_date_key,
           full_date       AS {role}_date,
           year            AS {role}_year,
           quarter         AS {role}_quarter,
           day_name        AS {role}_day_name,
           is_weekend      AS {role}_is_weekend,
           fiscal_quarter  AS {role}_fiscal_quarter
    FROM dim_date
    """)
print(f"[PASS] Q34 built {len(ROLES)} role views over ONE physical dim_date")

# ---------------------------------------------------------- unambiguous join
ROLE_JOIN = """
SELECT f.order_id,
       o.order_year,
       o.order_fiscal_quarter,
       s.ship_year,
       d.delivery_year,
       DATEDIFF(d.delivery_date, o.order_date) AS days_to_deliver
FROM fact_marketplace_order f
JOIN      vw_order_date    o ON o.order_date_key    = f.order_date_key
LEFT JOIN vw_ship_date     s ON s.ship_date_key     = f.ship_date_key
LEFT JOIN vw_delivery_date d ON d.delivery_date_key = f.delivery_date_key
ORDER BY f.order_id
"""
spark.sql(ROLE_JOIN).show(truncate=False)

expect("Q34 three roles, no name collisions, unshipped order preserved", ROLE_JOIN, [
    (1, 2025, "FY2025-Q4", 2025, 2026, 3),
    (2, 2025, "FY2025-Q4", 2026, 2026, 5),
    (3, 2026, "FY2026-Q1", 2026, 2026, 5),
    (4, 2026, "FY2026-Q1", None, None, None),
])

# DataFrame API equivalent.
f_ = spark.table("fact_marketplace_order")
df = (f_.join(F.broadcast(spark.table("vw_order_date")), "order_date_key")
      .join(F.broadcast(spark.table("vw_ship_date")), "ship_date_key", "left")
      .join(F.broadcast(spark.table("vw_delivery_date")), "delivery_date_key", "left")
      .select("order_id", "order_year", "order_fiscal_quarter", "ship_year",
              "delivery_year",
              F.datediff("delivery_date", "order_date").alias("days_to_deliver"))
      .orderBy("order_id"))
assert [tuple(r) for r in df.collect()] == [
    (1, 2025, "FY2025-Q4", 2025, 2026, 3),
    (2, 2025, "FY2025-Q4", 2026, 2026, 5),
    (3, 2026, "FY2026-Q1", 2026, 2026, 5),
    (4, 2026, "FY2026-Q1", None, None, None),
]
print("[PASS] Q34 DataFrame API matches SQL")

# ---------------------------------------------------------- the ambiguity trap
# Joining dim_date three times unaliased gives three columns named `year`.
try:
    spark.sql("""
    SELECT f.order_id, year
    FROM fact_marketplace_order f
    JOIN dim_date o ON o.date_key = f.order_date_key
    JOIN dim_date s ON s.date_key = f.ship_date_key
    JOIN dim_date d ON d.date_key = f.delivery_date_key
    """).collect()
    raise AssertionError("expected an ambiguous-reference error for bare `year`")
except Exception as e:
    assert type(e).__name__ != "AssertionError", e
    assert "AMBIGUOUS" in str(e).upper(), str(e)[:200]
    print("[PASS] Q34 an unaliased triple join makes `year` ambiguous -- Spark rejects it")

# ---------------------------------------------------------- the INNER JOIN trap
# Order 4 is unshipped. An inner join on the ship role drops it, so a report
# grouped by ORDER year silently loses the newest orders.
inner = spark.sql("""
SELECT o.year AS order_year, COUNT(*) AS orders, ROUND(SUM(f.amount), 2) AS revenue
FROM fact_marketplace_order f
JOIN dim_date o ON o.date_key = f.order_date_key
JOIN dim_date s ON s.date_key = f.ship_date_key      -- INNER on an optional role
GROUP BY o.year ORDER BY o.year
""").collect()
assert [(r[0], r[1], float(r[2])) for r in inner] == [
    (2025, 2, 200.00), (2026, 1, 200.00),
], inner

left = spark.sql("""
SELECT o.year AS order_year, COUNT(*) AS orders, ROUND(SUM(f.amount), 2) AS revenue
FROM fact_marketplace_order f
JOIN dim_date o ON o.date_key = f.order_date_key
LEFT JOIN dim_date s ON s.date_key = f.ship_date_key
GROUP BY o.year ORDER BY o.year
""").collect()
assert [(r[0], r[1], float(r[2])) for r in left] == [
    (2025, 2, 200.00), (2026, 2, 250.00),
], left
print("[PASS] Q34 INNER on the ship role reports 2026 revenue as 200.00; "
      "LEFT gives the true 250.00")

# ---------------------------------------------------------- one table, not three
# The whole point: a fiscal-calendar change is made ONCE.
tables = {r.tableName for r in spark.sql("SHOW TABLES").collect()}
assert "dim_date" in tables
assert not {"dim_order_date", "dim_ship_date", "dim_delivery_date"} & tables
print("[PASS] Q34 exactly one physical date table exists -- the roles are views")

# ---------------------------------------------------------- derived attrs are shared
# is_weekend / fiscal_quarter are available in EVERY role for free.
WEEKEND = """
SELECT f.order_id, o.order_day_name, o.order_is_weekend, d.delivery_is_weekend
FROM fact_marketplace_order f
JOIN vw_order_date o ON o.order_date_key = f.order_date_key
LEFT JOIN vw_delivery_date d ON d.delivery_date_key = f.delivery_date_key
ORDER BY f.order_id
"""
expect("Q34 derived attributes are available in every role", WEEKEND, [
    (1, "Tuesday",   False, False),
    (2, "Wednesday", False, False),
    (3, "Thursday",  False, False),
    (4, "Friday",    False, None),
])
print("[PASS] Q18 no query reimplements weekend or fiscal-quarter logic")
