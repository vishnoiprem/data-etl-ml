"""
Q05: Pages With No Likes   [Easy | Left Join, NULL Handling]

Find Facebook pages that have received zero likes.

How to Think:
- Anti-join. Three correct forms; know all three and why you picked one:
    1. LEFT JOIN ... WHERE right_key IS NULL   (most portable)
    2. NOT EXISTS (correlated)                 (usually the optimiser's favourite)
    3. NOT IN (subquery)                       (DANGEROUS - see trap)
- The NULL check must be on a column from the RIGHT table that can never be
  null for a matched row (the join key), not on any nullable attribute.

The trap:
- NOT IN with a subquery that can return NULL yields an EMPTY result set,
  silently. If page_likes.page_id were nullable, form 3 breaks. Mentioning
  this unprompted is a strong signal.

Spark note:
- Spark has a native LEFT ANTI join, which is the cleanest expression of intent
  and avoids materialising the null-extended rows at all.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("05-pages-with-no-likes")
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
    (101, "Cooking Daily"), (102, "Tech Weekly"),
    (103, "Empty Page"), (104, "Also Empty"),
],
    ["page_id", "page_name"]
).createOrReplaceTempView("pages")

spark.createDataFrame(
    [
    (101, 1), (101, 2), (102, 1),
],
    ["page_id", "user_id"]
).createOrReplaceTempView("page_likes")


SQL = """
SELECT p.page_id, p.page_name
FROM pages p
LEFT JOIN page_likes l ON l.page_id = p.page_id
WHERE l.page_id IS NULL
ORDER BY p.page_id
"""

expect("Q05 pages with no likes", SQL, [(103, "Empty Page"), (104, "Also Empty")])

# Spark-native LEFT ANTI join — same answer, clearer intent.
anti = (spark.table("pages").join(spark.table("page_likes"), "page_id", "left_anti")
        .orderBy("page_id").select("page_id", "page_name"))
assert [tuple(r) for r in anti.collect()] == [(103, "Empty Page"), (104, "Also Empty")]
print("[PASS] Q05 LEFT ANTI join matches")
