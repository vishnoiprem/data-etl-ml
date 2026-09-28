"""
Q17: Advertiser Payment Status Classification   [Hard | Joins, CASE WHEN]

Classify advertisers per month as New / Existing / Churn / Resurrected from
payment history.

How to Think:
- Same state machine as Q06, now emitted per entity per month rather than as
  totals. Write the definitions down before any SQL:
      New         = paid this month, and this is their first-ever paying month
      Existing    = paid this month and paid last month
      Resurrected = paid this month, did NOT pay last month, but paid earlier
      Churn       = did NOT pay this month, but paid last month
- Churn describes a month with NO row for that advertiser, so a month spine
  cross joined to advertisers is mandatory. This is the structural insight.
- Rows that are neither active nor newly-churned (before first payment, or long
  after churn) must be dropped, not labelled.

The trap:
- a4 pays in January, skips February, pays again in March. A naive query calls
  March "New" (no prior month) or "Existing". It is Resurrected, and the test
  that distinguishes it is `month > first_paying_month`.

Spark note:
- Spine is tiny and broadcastable; one window per advertiser for the LAG.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("17-advertiser-payment-status")
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
spark.createDataFrame(
    [
    ("a1", "2026-01-10"), ("a1", "2026-02-10"),
    ("a2", "2026-02-05"),
    ("a3", "2026-01-20"),
    ("a4", "2026-01-15"), ("a4", "2026-03-15"),
],
    ["advertiser_id", "payment_date"]
).createOrReplaceTempView("advertiser_pay")


SQL = """
WITH am AS (
    SELECT DISTINCT advertiser_id, DATE_FORMAT(payment_date, 'yyyy-MM') AS ym
    FROM advertiser_pay
),
first_pay AS (SELECT advertiser_id, MIN(ym) AS first_ym FROM am GROUP BY advertiser_id),
months AS (SELECT DISTINCT ym FROM am),
grid AS (
    SELECT m.ym, a.advertiser_id, f.first_ym,
           CASE WHEN p.advertiser_id IS NOT NULL THEN 1 ELSE 0 END AS active
    FROM months m
    CROSS JOIN (SELECT DISTINCT advertiser_id FROM am) a
    JOIN first_pay f ON f.advertiser_id = a.advertiser_id
    LEFT JOIN am p ON p.advertiser_id = a.advertiser_id AND p.ym = m.ym
),
flagged AS (
    SELECT ym, advertiser_id, first_ym, active,
           LAG(active) OVER (PARTITION BY advertiser_id ORDER BY ym) AS prev_active
    FROM grid
)
SELECT advertiser_id, ym,
       CASE WHEN active = 1 AND ym = first_ym                          THEN 'New'
            WHEN active = 1 AND prev_active = 1                        THEN 'Existing'
            WHEN active = 1 AND prev_active = 0 AND ym > first_ym      THEN 'Resurrected'
            WHEN active = 0 AND prev_active = 1                        THEN 'Churn'
       END AS status
FROM flagged
WHERE (active = 1) OR (active = 0 AND prev_active = 1)
ORDER BY advertiser_id, ym
"""

expect("Q17 advertiser payment status", SQL, [
    ("a1", "2026-01", "New"),
    ("a1", "2026-02", "Existing"),
    ("a1", "2026-03", "Churn"),
    ("a2", "2026-02", "New"),
    ("a2", "2026-03", "Churn"),
    ("a3", "2026-01", "New"),
    ("a3", "2026-02", "Churn"),
    ("a4", "2026-01", "New"),
    ("a4", "2026-02", "Churn"),
    ("a4", "2026-03", "Resurrected"),
])

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 supports CTEs, CROSS JOIN to a month spine, and LAG. The status
# definitions map directly to the CASE arms: New = active AND first_paying
# month; Existing = active AND prior month active; Resurrected = active AND
# prior month inactive AND month > first; Churn = inactive AND prior month
# active. Rows that are neither (before first payment, or long after churn)
# are dropped by the final WHERE.
#
# CREATE TABLE advertiser_pay (
#     advertiser_id VARCHAR(8)  NOT NULL,
#     payment_date  DATE        NOT NULL,
#     PRIMARY KEY (advertiser_id, payment_date),
#     KEY ix_ap_date (payment_date)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO advertiser_pay (advertiser_id, payment_date) VALUES
#     ('a1', '2026-01-10'), ('a1', '2026-02-10'),
#     ('a2', '2026-02-05'),
#     ('a3', '2026-01-20'),
#     ('a4', '2026-01-15'), ('a4', '2026-03-15');
#
# WITH am AS (
#     SELECT DISTINCT advertiser_id, DATE_FORMAT(payment_date, '%Y-%m') AS ym
#     FROM advertiser_pay
# ),
# first_pay AS (SELECT advertiser_id, MIN(ym) AS first_ym FROM am GROUP BY advertiser_id),
# months AS (SELECT DISTINCT ym FROM am),
# grid AS (
#     SELECT m.ym, a.advertiser_id, f.first_ym,
#            CASE WHEN p.advertiser_id IS NOT NULL THEN 1 ELSE 0 END AS active
#     FROM months m
#     CROSS JOIN (SELECT DISTINCT advertiser_id FROM am) a
#     JOIN first_pay f ON f.advertiser_id = a.advertiser_id
#     LEFT JOIN am p ON p.advertiser_id = a.advertiser_id AND p.ym = m.ym
# ),
# flagged AS (
#     SELECT ym, advertiser_id, first_ym, active,
#            LAG(active) OVER (PARTITION BY advertiser_id ORDER BY ym) AS prev_active
#     FROM grid
# )
# SELECT advertiser_id, ym,
#        CASE WHEN active = 1 AND ym = first_ym                          THEN 'New'
#             WHEN active = 1 AND prev_active = 1                        THEN 'Existing'
#             WHEN active = 1 AND prev_active = 0 AND ym > first_ym      THEN 'Resurrected'
#             WHEN active = 0 AND prev_active = 1                        THEN 'Churn'
#        END AS status
# FROM flagged
# WHERE (active = 1) OR (active = 0 AND prev_active = 1)
# ORDER BY advertiser_id, ym;
#
# -- Expected:
# -- a1  2026-01  New
# -- a1  2026-02  Existing
# -- a1  2026-03  Churn
# -- a2  2026-02  New
# -- a2  2026-03  Churn
# -- a3  2026-01  New
# -- a3  2026-02  Churn
# -- a4  2026-01  New
# -- a4  2026-02  Churn
# -- a4  2026-03  Resurrected
