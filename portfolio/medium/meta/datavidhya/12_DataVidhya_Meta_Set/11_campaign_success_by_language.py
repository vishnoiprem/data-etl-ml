"""
Q11: Campaign Success Rate by Language   [Medium | Aggregation]

Success rate grouped by language, sorted by rate.

How to Think:
- AVG over a 0/1 flag IS the rate; you rarely need SUM/COUNT.
  AVG(is_success) * 100 is shorter and less error-prone than two counts.
- Multiply by 100.0 (decimal literal) so integer division cannot bite.
- Always return the denominator alongside a rate. "100% success" on 3 campaigns
  means nothing, and volunteering the sample size is a product-sense signal.

Spark note:
- Single shuffle aggregate; nothing clever required.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("11-campaign-success-by-language")
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
    (1, "en", 1), (2, "en", 1), (3, "en", 0), (4, "en", 0),   # 2/4 = 50.00
    (5, "th", 1), (6, "th", 1), (7, "th", 1),                 # 3/3 = 100.00
    (8, "ja", 0), (9, "ja", 0),                               # 0/2 = 0.00
],
    ["campaign_id", "language", "is_success"]
).createOrReplaceTempView("campaigns")


SQL = """
SELECT language,
       COUNT(*) AS campaigns,
       SUM(is_success) AS successes,
       ROUND(100.0 * AVG(is_success), 2) AS success_rate_pct
FROM campaigns
GROUP BY language
ORDER BY success_rate_pct DESC, language
"""

expect("Q11 campaign success rate by language", SQL, [
    ("th", 3, 3, 100.00),
    ("en", 4, 2, 50.00),
    ("ja", 2, 0, 0.00),
])

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 supports AVG over a 0/1 flag identically. is_success is stored as
# TINYINT(1) -- MySQL's idiomatic BOOLEAN. Multiplying by 100.0 forces DECIMAL
# arithmetic so AVG * 100 cannot truncate to 0 on a low-rate group.
#
# CREATE TABLE campaigns (
#     campaign_id INT         NOT NULL,
#     language    VARCHAR(8)  NOT NULL,
#     is_success  TINYINT(1)  NOT NULL,
#     PRIMARY KEY (campaign_id),
#     KEY ix_campaigns_lang (language)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO campaigns (campaign_id, language, is_success) VALUES
#     (1, 'en', 1), (2, 'en', 1), (3, 'en', 0), (4, 'en', 0),
#     (5, 'th', 1), (6, 'th', 1), (7, 'th', 1),
#     (8, 'ja', 0), (9, 'ja', 0);
#
# SELECT language,
#        COUNT(*) AS campaigns,
#        SUM(is_success) AS successes,
#        ROUND(100.0 * AVG(is_success), 2) AS success_rate_pct
# FROM campaigns
# GROUP BY language
# ORDER BY success_rate_pct DESC, language;
#
# -- Expected:
# -- th  3  3  100.00
# -- en  4  2  50.00
# -- ja  2  0  0.00
