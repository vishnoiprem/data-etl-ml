"""
Q16: Spam Post Percentage by Day   [Medium | Joins, String Manipulation]

Percentage of VIEWED posts that are spam, per day. Spam = content contains
the word 'spam'.

How to Think:
- The grain is (day, viewed post). Join views to content, then aggregate by day.
- Denominator = posts viewed that day, NOT all posts. Post 4 is spam but never
  viewed, so it must not appear anywhere in the calculation.
- Case sensitivity: 'SPAM offer inside' is spam. LIKE is case-SENSITIVE in
  Presto/Spark, so LOWER() the column first. Forgetting this undercounts.

The trap and the question worth asking:
- 'anti-spamming tools review' contains 'spam' as a SUBSTRING but is not spam.
  LIKE '%spam%' flags it. Whether that is desired is a definition question you
  should raise: substring match, or word-boundary match via RLIKE '\\\\bspam\\\\b'?
  This query uses substring matching (the literal reading of the question) and
  the docstring records the ambiguity — that is the behaviour to copy in a real
  interview. Post 4 is never viewed here, so the two definitions agree on this
  data; on real data they would not.

Spark note:
- Broadcast the small content/dim table; the views fact is the big side.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("16-spam-post-percentage")
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
    (1, "buy cheap spam now"),
    (2, "normal holiday photo"),
    (3, "SPAM offer inside"),
    (4, "anti-spamming tools review"),
    (5, "just a regular post"),
],
    ["post_id", "content"]
).createOrReplaceTempView("posts_content")

spark.createDataFrame(
    [
    (1, "2026-01-01"), (2, "2026-01-01"), (3, "2026-01-01"), (5, "2026-01-01"),
    (2, "2026-01-02"), (5, "2026-01-02"),
],
    ["post_id", "view_date"]
).createOrReplaceTempView("post_views")


SQL = """
SELECT v.view_date,
       COUNT(*) AS posts_viewed,
       SUM(CASE WHEN LOWER(c.content) LIKE '%spam%' THEN 1 ELSE 0 END) AS spam_viewed,
       ROUND(100.0 * SUM(CASE WHEN LOWER(c.content) LIKE '%spam%' THEN 1 ELSE 0 END)
                   / COUNT(*), 2) AS spam_pct
FROM post_views v
JOIN posts_content c ON c.post_id = v.post_id
GROUP BY v.view_date
ORDER BY v.view_date
"""

expect("Q16 spam post % by day", SQL, [
    ("2026-01-01", 4, 2, 50.00),
    ("2026-01-02", 2, 0, 0.00),
])
