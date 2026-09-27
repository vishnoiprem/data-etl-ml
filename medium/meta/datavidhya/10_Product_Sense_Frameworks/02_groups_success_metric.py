"""
Problem 02: Define success for Facebook Groups, then compute it.

Meta flavor: "How would you measure the success of Facebook Groups?"

The model answer, in the spine from problem 01:
  USER VALUE  - "Success means people find groups worth RETURNING to."
  BEHAVIOUR   - repeat PARTICIPATION, not joins. Joins are a one-time vanity
                event; a group with 10,000 members and no posts is dead.
  METRIC      - primary:   weekly active participants per group
                secondary: contributor-to-lurker ratio
  GRAIN       - one row per (user, group, day) activity fact.
  QUERY       - below.

Why "participants" and not "members": membership is monotonic and only ever
grows, so it cannot detect decline. Any metric that cannot go down is not a
health metric. That sentence is worth memorising.

Contributor vs lurker:
  contributor = posted or commented; lurker = viewed only.
  A healthy group needs lurkers (most members always are), so the ratio is a
  balance indicator, not a number to maximise.

Spark note:
- Grain is (user, group, day); dedup to that grain before counting or an
  active-user count silently becomes an event count.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("02-groups-success-metric")
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



# One row per (user, group, day, action). g1 is healthy, g2 is a lurker-only
# group with no contributors at all — exactly the "dead group" case the metric
# has to be able to surface.
spark.createDataFrame([
    ("g1", 1, "2026-01-05", "post"),
    ("g1", 2, "2026-01-05", "comment"),
    ("g1", 3, "2026-01-06", "view"),
    ("g1", 1, "2026-01-07", "comment"),
    ("g1", 4, "2026-01-07", "view"),
    ("g2", 5, "2026-01-05", "view"),
    ("g2", 6, "2026-01-06", "view"),
], ["group_id", "user_id", "activity_date", "action"]).createOrReplaceTempView("group_activity")

expect("weekly active participants per group", """
SELECT group_id,
       COUNT(DISTINCT user_id) AS weekly_active_participants,
       COUNT(DISTINCT CASE WHEN action IN ('post', 'comment') THEN user_id END)
           AS contributors,
       COUNT(DISTINCT CASE WHEN action = 'view' THEN user_id END) AS viewers
FROM group_activity
GROUP BY group_id
ORDER BY group_id
""", [
    ("g1", 4, 2, 2),
    ("g2", 2, 0, 2),
])

# Contributor ratio. g2 scores 0.0 -> the group is pure lurkers and, by the
# definition we committed to, not succeeding regardless of its member count.
expect("contributor-to-participant ratio", """
SELECT group_id,
       ROUND(100.0 * COUNT(DISTINCT CASE WHEN action IN ('post','comment')
                                         THEN user_id END)
                   / COUNT(DISTINCT user_id), 2) AS contributor_pct
FROM group_activity
GROUP BY group_id
ORDER BY group_id
""", [("g1", 50.00), ("g2", 0.00)])


# ===========================================================================
# PySpark DataFrame API — same two questions, expressed with DataFrame ops.
# Mirror of the SQL above; assert at the end of each block so SQL vs. DataFrame
# cannot silently disagree.
# ===========================================================================
from pyspark.sql import functions as F

act_df = spark.table("group_activity")

# Helpers: action-class flags equivalent to the CASE WHEN IN (...) in SQL.
# Use a single isin() predicate instead of chained .when() — cheaper to plan
# and easier to read at scale.
is_contrib = F.col("action").isin("post", "comment")
is_view    = F.col("action") == "view"

# PRIMARY: weekly active participants per group, split by action class.
wa_df = (act_df
         .groupBy("group_id")
         .agg(F.countDistinct("user_id").alias("weekly_active_participants"),
              F.countDistinct(F.when(is_contrib, F.col("user_id"))).alias("contributors"),
              F.countDistinct(F.when(is_view,    F.col("user_id"))).alias("viewers"))
         .orderBy("group_id"))
assert [tuple(r) for r in wa_df.collect()] == [
    ("g1", 4, 2, 2),
    ("g2", 2, 0, 2),
]
print("[PASS] weekly active participants per group — DataFrame API matches SQL")

# SECONDARY: contributor-to-participant ratio.
# 100.0 * (count of distinct contributors) / (count of distinct participants).
# If participants > 0, the division is safe; if it were 0 we'd hit a divide by
# zero, which is the case g2 sits at the boundary of — handled correctly
# because g2 has 2 participants, just 0 contributors.
ratio_df = (act_df
            .groupBy("group_id")
            .agg(F.round(
                100.0 * F.countDistinct(F.when(is_contrib, F.col("user_id")))
                       / F.countDistinct("user_id"),
                2
            ).alias("contributor_pct"))
            .orderBy("group_id"))
assert [tuple(r) for r in ratio_df.collect()] == [("g1", 50.00), ("g2", 0.00)]
print("[PASS] contributor-to-participant ratio — DataFrame API matches SQL")
