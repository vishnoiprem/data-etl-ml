"""
Q04: Monthly Active User Retention   [Medium | Joins, Date Functions]

Find users active in July 2022 AND also active in June 2022.
Active = performed 'sign-in', 'like', or 'comment'.

How to Think:
- The action filter is the whole question. Applying it to only one side of the
  comparison is the classic wrong answer.
- Two equally valid shapes: self-join on user_id across the two months, or
  aggregate with conditional flags and HAVING. The flag form scans once.
- Month boundaries: use a half-open range [2022-07-01, 2022-08-01) rather than
  BETWEEN with an end date, so a timestamp at 23:59 does not fall out.

The traps:
- User 4 was active in June and appears in July, but their July row is 'logout',
  which is NOT a qualifying action. Excluded.
- User 5 is active June and August, skipping July. Excluded.

Spark note:
- Single pass + HAVING. No self-join means no second shuffle of the big table.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("04-monthly-active-retention")
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
    (1, "sign-in", "2022-06-10"), (1, "like",    "2022-07-11"),
    (2, "comment", "2022-07-05"),
    (3, "like",    "2022-06-20"),
    (4, "sign-in", "2022-06-15"), (4, "logout",  "2022-07-15"),
    (5, "sign-in", "2022-06-01"), (5, "comment", "2022-08-02"),
],
    ["user_id", "action", "action_date"]
).createOrReplaceTempView("user_actions")


SQL = """
SELECT user_id
FROM user_actions
WHERE action IN ('sign-in', 'like', 'comment')
GROUP BY user_id
HAVING MAX(CASE WHEN action_date >= DATE '2022-07-01'
                 AND action_date <  DATE '2022-08-01' THEN 1 ELSE 0 END) = 1
   AND MAX(CASE WHEN action_date >= DATE '2022-06-01'
                 AND action_date <  DATE '2022-07-01' THEN 1 ELSE 0 END) = 1
ORDER BY user_id
"""

expect("Q04 monthly active retention", SQL, [(1,)])
