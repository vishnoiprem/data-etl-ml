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
from _seeds import spark, expect

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
