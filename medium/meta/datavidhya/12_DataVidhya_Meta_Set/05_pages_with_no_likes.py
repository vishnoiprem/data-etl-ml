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

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 supports LEFT JOIN ... IS NULL and NOT EXISTS for anti-joins.
# NOT IN is portable but breaks if the subquery can return NULL -- the result
# collapses to an empty set silently. NOT EXISTS and LEFT JOIN ... IS NULL are
# both NULL-safe. MySQL has no native LEFT ANTI join keyword, so use one of
# these two forms.
#
# CREATE TABLE pages (
#     page_id   INT         NOT NULL,
#     page_name VARCHAR(64) NOT NULL,
#     PRIMARY KEY (page_id)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# CREATE TABLE page_likes (
#     page_id INT NOT NULL,
#     user_id INT NOT NULL,
#     PRIMARY KEY (page_id, user_id),
#     KEY ix_pl_user (user_id),
#     CONSTRAINT fk_pl_page FOREIGN KEY (page_id) REFERENCES pages(page_id)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO pages (page_id, page_name) VALUES
#     (101, 'Cooking Daily'), (102, 'Tech Weekly'),
#     (103, 'Empty Page'),    (104, 'Also Empty');
#
# INSERT INTO page_likes (page_id, user_id) VALUES
#     (101, 1), (101, 2), (102, 1);
#
# SELECT p.page_id, p.page_name
# FROM pages p
# LEFT JOIN page_likes l ON l.page_id = p.page_id
# WHERE l.page_id IS NULL
# ORDER BY p.page_id;
#
# -- Equivalent NOT EXISTS form (often optimiser-preferred):
# SELECT p.page_id, p.page_name
# FROM pages p
# WHERE NOT EXISTS (SELECT 1 FROM page_likes l WHERE l.page_id = p.page_id)
# ORDER BY p.page_id;
#
# -- Expected:
# -- 103  'Empty Page'
# -- 104  'Also Empty'
