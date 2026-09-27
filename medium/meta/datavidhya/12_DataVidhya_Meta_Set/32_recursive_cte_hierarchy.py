"""
Q32: Recursive CTE for Hierarchical Data   [Hard | Common Table Expressions]
DataVidhya slug: recursive-cte-hierarchical-data

Walk a parent-child category tree. Emit every category with its depth (root = 1)
and full_path, the root-to-node names joined by ' > '. Sort by full_path.

How to Think:
- Every recursive CTE is two halves glued by UNION ALL, and you should name them
  out loud before writing either:
    ANCHOR    -> the roots. `WHERE parent_id IS NULL`, depth 1, path = own name.
    RECURSIVE -> join the table back to the PREVIOUS iteration's output on
                 child.parent_id = prev.category_id, depth + 1,
                 path = prev.path || ' > ' || child.name.
- The path accumulates in the recursion; it is not computed afterwards. That is
  the whole reason this needs recursion rather than a self-join -- an N-level
  tree would need N self-joins and you do not know N.
- Depth and path advance together, so one recursive step handles both.

The trap:
- Spark 3.5 does NOT support `WITH RECURSIVE` (it landed in Spark 4.0). On
  Spark 3.x you must drive the fixed point yourself in the host language: loop,
  joining the frontier to the table until the frontier is empty. Say this in
  the interview -- claiming a recursive CTE on Spark 3 is a correctness bug, not
  a style choice. The ANSI query is written out below for the Presto/Postgres
  answer, and the iterative version is what actually runs here.
- The sort key is `full_path`, NOT category_id and NOT depth. That is why
  Desktops (id 4) precedes Laptops (id 3) in the expected output -- string
  ordering on the path, so siblings sort alphabetically under their parent.
- Roots have a NULL parent_id which must SURVIVE to the output as NULL.
- Always bound the loop. A cycle in the data (a category that is its own
  ancestor) makes a real recursive CTE spin forever; the guard below fails loudly
  instead.

Spark note:
- Each iteration is a shuffle join, so an N-deep tree costs N jobs. Cache the
  source, and on a wide-but-shallow tree prefer a bounded number of explicit
  self-joins. For a genuinely deep hierarchy, materialise a path/closure table
  once rather than recursing on every query.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("32-recursive-cte-hierarchy")
         .master("local[2]")
         .config("spark.sql.shuffle.partitions", "2")
         .config("spark.ui.showConsoleProgress", "false")
         .getOrCreate())
spark.sparkContext.setLogLevel("ERROR")


def expect_rows(title, df, expected_rows):
    """Assert a DataFrame's exact rows, in order. Decimal/float safe."""
    import decimal

    def norm(v):
        if isinstance(v, decimal.Decimal):
            return float(v)
        if isinstance(v, float):
            return round(v, 6)
        return v

    got = [tuple(norm(c) for c in r) for r in df.collect()]
    exp = [tuple(norm(c) for c in r) for r in expected_rows]
    if got != exp:
        print(f"[FAIL] {title}")
        print(f"   expected: {exp}")
        print(f"   got:      {got}")
        raise AssertionError(title)
    print(f"[PASS] {title}")
    return got


# ---------------------------------------------------------- sample data
# Exactly the rows DataVidhya ships with the question. Category 1 is the root.
spark.createDataFrame(
    [
        (1, "Electronics", None),
        (2, "Computers", 1),
        (3, "Laptops", 2),
        (4, "Desktops", 2),
    ],
    "category_id INT, category_name STRING, parent_id INT",
).createOrReplaceTempView("categories")

from pyspark.sql import functions as F

# ------------------------------------------------ the ANSI answer (Presto/Postgres/Spark 4+)
# Kept as a string because Spark 3.5 cannot parse it. This is what you write
# on a whiteboard; the loop below is what you run on this cluster.
ANSI_RECURSIVE_SQL = """
WITH RECURSIVE tree AS (
    -- anchor: roots
    SELECT category_id,
           category_name,
           parent_id,
           1 AS depth,
           category_name AS full_path
    FROM categories
    WHERE parent_id IS NULL

    UNION ALL

    -- recursive: children of whatever the previous iteration produced
    SELECT c.category_id,
           c.category_name,
           c.parent_id,
           t.depth + 1                                  AS depth,
           CONCAT(t.full_path, ' > ', c.category_name)   AS full_path
    FROM categories c
    JOIN tree t ON c.parent_id = t.category_id
)
SELECT category_id, category_name, parent_id, depth, full_path
FROM tree
ORDER BY full_path
"""

assert "WITH RECURSIVE" in ANSI_RECURSIVE_SQL
try:
    spark.sql(ANSI_RECURSIVE_SQL).collect()
    print("[NOTE] this Spark build parses WITH RECURSIVE (Spark 4+)")
except Exception:
    print(f"[NOTE] Spark {spark.version} cannot parse WITH RECURSIVE -- driving the fixed point manually")


# ------------------------------------------------ the iterative fixed point (Spark 3.x)
def walk_hierarchy(max_depth=64):
    """Expand the tree one level per iteration until no new children appear."""
    cats = spark.table("categories").cache()

    frontier = (cats.filter(F.col("parent_id").isNull())
                .select("category_id", "category_name", "parent_id",
                        F.lit(1).alias("depth"),
                        F.col("category_name").alias("full_path")))
    accumulated = frontier
    depth = 1

    while frontier.count() > 0:
        depth += 1
        if depth > max_depth:
            # A cycle in the data would otherwise loop forever.
            raise RuntimeError(f"hierarchy deeper than {max_depth} -- cycle in categories?")
        frontier = (cats.alias("c")
                    .join(frontier.alias("p"),
                          F.col("c.parent_id") == F.col("p.category_id"))
                    .select(F.col("c.category_id"),
                            F.col("c.category_name"),
                            F.col("c.parent_id"),
                            (F.col("p.depth") + 1).alias("depth"),
                            F.concat_ws(" > ", F.col("p.full_path"),
                                        F.col("c.category_name")).alias("full_path")))
        frontier.cache()
        if frontier.count() == 0:
            break
        accumulated = accumulated.unionByName(frontier)

    return accumulated.orderBy("full_path")


tree = walk_hierarchy()
tree.show(truncate=False)

expect_rows("Q32 hierarchy depth + full_path", tree, [
    (1, "Electronics", None, 1, "Electronics"),
    (2, "Computers", 1, 2, "Electronics > Computers"),
    (4, "Desktops", 2, 3, "Electronics > Computers > Desktops"),
    (3, "Laptops", 2, 3, "Electronics > Computers > Laptops"),
])

# ------------------------------------------------ the sort-key trap
# ORDER BY full_path puts Desktops (id 4) before Laptops (id 3). Ordering by
# category_id would reverse them and fail.
by_path = [r[0] for r in tree.collect()]
by_id = [r[0] for r in tree.orderBy("category_id").collect()]
assert by_path == [1, 2, 4, 3], by_path
assert by_id == [1, 2, 3, 4], by_id
print("[PASS] Q32 ORDER BY full_path gives 1,2,4,3 -- ordering by category_id is wrong")

# ------------------------------------------------ the cycle guard
# A category that is its own ancestor must fail loudly, not spin.
spark.createDataFrame(
    [(1, "A", 2), (2, "B", 1)],
    "category_id INT, category_name STRING, parent_id INT",
).createOrReplaceTempView("categories")
cyclic = walk_hierarchy()
assert cyclic.count() == 0, "a cycle with no root should yield no rows"
print("[PASS] Q32 all-cycle input has no root, so the anchor is empty -- no infinite loop")

spark.createDataFrame(
    [(1, "Root", None), (2, "B", 1), (3, "C", 2), (4, "D", 3), (2, "B-again", 4)],
    "category_id INT, category_name STRING, parent_id INT",
).createOrReplaceTempView("categories")
try:
    walk_hierarchy(max_depth=8).count()
    raise AssertionError("expected the depth guard to trip on a cyclic branch")
except RuntimeError as e:
    assert "cycle in categories" in str(e), e
    print("[PASS] Q32 depth guard trips on a cyclic branch instead of looping forever")