"""
Q51: Find all posts which were reacted to with a heart   [Medium | Inner Joins, Aggregate Functions]
DataVidhya slug: find-all-posts-which-were-reacted-to-with-a-heart

Posts with at least one 'heart' reaction: post_id, post_text, heart_count.
Ordered by heart_count DESC, then post_id ASC.

How to Think:
- "At least one heart" is INNER JOIN semantics: no hearts, no row. So filter
  reactions to hearts and inner-join -- the "at least one" requirement needs no
  HAVING at all, it falls out of the join.
- heart_count is then just COUNT(*) over the surviving reaction rows.
- The output drops poster_id and post_date. Select the three named columns
  only; `SELECT p.*` is a spec violation even though it "works".

The trap:
- WHERE vs ON with an outer join. These three are NOT the same:
    INNER JOIN ... WHERE reaction_type = 'heart'   -> correct
    LEFT JOIN  ... WHERE reaction_type = 'heart'   -> also correct (the WHERE
                                                     nullifies the outer-ness)
    LEFT JOIN  ... ON  reaction_type = 'heart'     -> WRONG: keeps posts 4 and 9
                                                     with a phantom heart_count
  and in that third case COUNT(*) returns 1 for a post with NO hearts, because
  the outer join manufactures a row. COUNT(r.reaction_id) would give 0, which is
  still a row that should not exist. This is the question.
- Post 1 has three reactions but only two hearts. COUNT(*) without the
  reaction_type filter gives 3.
- Post 9's only reaction is a 'like' and post 4 has none -- both must be absent.
- The sort is two-level and mixed-direction: heart_count DESC, post_id ASC.
  Posts 3 and 8 both have 3 hearts, and 3 must come first. Omitting the
  tiebreak makes the output non-deterministic on exactly that tie.
- 'heart' is matched EXACTLY -- not LIKE '%heart%', which would also match
  'hearted' or 'broken_heart'.

Spark note:
- Push the reaction_type filter before the join so the shuffle carries only
  heart rows. `posts` is the small side and broadcasts.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("51-posts-reacted-with-heart")
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
# Exactly the rows DataVidhya ships with the question.
# Post 1: 2 hearts + 1 like. Post 4: no reactions. Post 9: one 'like' only.
spark.sql("""
CREATE OR REPLACE TEMP VIEW posts AS
SELECT * FROM VALUES
    (1, 101, DATE'2023-01-15', 'Great day at the beach'),
    (2, 102, DATE'2023-01-20', 'Just finished a great book'),
    (3, 101, DATE'2023-02-10', 'Excited about the new project'),
    (4, 103, DATE'2023-02-22', 'Coffee and coding'),
    (8, 101, DATE'2023-04-25', 'Happy Friday everyone'),
    (9, 106, DATE'2023-05-08', 'Loving this weather')
AS t(post_id, poster_id, post_date, post_text)
""")
spark.sql("""
CREATE OR REPLACE TEMP VIEW reactions AS
SELECT * FROM VALUES
    ( 1, 1, 201, 'heart'),
    ( 2, 1, 202, 'like'),
    ( 3, 1, 203, 'heart'),
    ( 4, 2, 204, 'like'),
    ( 5, 2, 205, 'heart'),
    ( 6, 3, 206, 'heart'),
    ( 7, 3, 207, 'heart'),
    ( 8, 3, 208, 'heart'),
    (18, 8, 218, 'heart'),
    (19, 8, 219, 'heart'),
    (20, 8, 220, 'heart'),
    (21, 9, 221, 'like')
AS t(reaction_id, post_id, user_id, reaction_type)
""")

from pyspark.sql import functions as F

SQL = """
SELECT p.post_id,
       p.post_text,
       COUNT(*) AS heart_count
FROM posts p
JOIN reactions r ON r.post_id = p.post_id
WHERE r.reaction_type = 'heart'          -- exact match, not LIKE
GROUP BY p.post_id, p.post_text
ORDER BY heart_count DESC, p.post_id     -- mixed directions
"""

spark.sql(SQL).show(truncate=False)

EXPECTED = [
    (3, "Excited about the new project", 3),
    (8, "Happy Friday everyone", 3),
    (1, "Great day at the beach", 2),
    (2, "Just finished a great book", 1),
]
expect("Q51 posts with heart reactions", SQL, EXPECTED)

# DataFrame API equivalent -- filter before the join.
hearts = spark.table("reactions").filter(F.col("reaction_type") == "heart")
df = (F.broadcast(spark.table("posts")).join(hearts, "post_id")
      .groupBy("post_id", "post_text")
      .agg(F.count(F.lit(1)).alias("heart_count"))
      .orderBy(F.col("heart_count").desc(), F.col("post_id")))
assert [tuple(r) for r in df.collect()] == EXPECTED
print("[PASS] Q51 DataFrame API matches SQL")

# ------------------------------------------------ the ON vs WHERE trap
on_clause = spark.sql("""
SELECT p.post_id, COUNT(*) AS heart_count, COUNT(r.reaction_id) AS non_null_hearts
FROM posts p
LEFT JOIN reactions r ON r.post_id = p.post_id AND r.reaction_type = 'heart'
GROUP BY p.post_id ORDER BY p.post_id
""").collect()
rows = [(r[0], r[1], r[2]) for r in on_clause]
assert rows == [(1, 2, 2), (2, 1, 1), (3, 3, 3), (4, 1, 0), (8, 3, 3), (9, 1, 0)], rows
print("[PASS] Q51 LEFT JOIN with the filter in ON keeps posts 4 and 9 -- "
      "COUNT(*) even reports 1 heart for posts with none")

where_clause = spark.sql("""
SELECT p.post_id, COUNT(*) AS heart_count
FROM posts p
LEFT JOIN reactions r ON r.post_id = p.post_id
WHERE r.reaction_type = 'heart'
GROUP BY p.post_id ORDER BY p.post_id
""").collect()
assert [(r[0], r[1]) for r in where_clause] == [(1, 2), (2, 1), (3, 3), (8, 3)], where_clause
print("[PASS] Q51 moving the filter to WHERE restores inner semantics (4 rows)")

# ------------------------------------------------ the unfiltered-count trap
unfiltered = spark.sql("""
SELECT p.post_id, COUNT(*) AS reaction_count
FROM posts p JOIN reactions r ON r.post_id = p.post_id
GROUP BY p.post_id ORDER BY p.post_id
""").collect()
assert [(r[0], r[1]) for r in unfiltered] == [(1, 3), (2, 2), (3, 3), (8, 3), (9, 1)], unfiltered
print("[PASS] Q51 without the heart filter, post 1 counts 3 reactions and post 9 reappears")

# ------------------------------------------------ the tie ordering
top_two = [r[0] for r in spark.sql(SQL).collect()][:2]
assert top_two == [3, 8], top_two
print("[PASS] Q51 posts 3 and 8 tie at 3 hearts; post_id ASC puts 3 first")

# ------------------------------------------------ exact match, not LIKE
spark.sql("""
CREATE OR REPLACE TEMP VIEW reactions AS
SELECT * FROM VALUES
    (1, 1, 201, 'heart'),
    (2, 1, 202, 'broken_heart'),
    (3, 1, 203, 'hearted')
AS t(reaction_id, post_id, user_id, reaction_type)
""")
expect("Q51 only the exact 'heart' type counts", SQL, [(1, "Great day at the beach", 1)])

like_count = spark.sql("""
SELECT COUNT(*) FROM reactions WHERE reaction_type LIKE '%heart%'
""").collect()[0][0]
assert like_count == 3, like_count
print("[PASS] Q51 LIKE '%heart%' matches 3 rows including 'broken_heart' and 'hearted'")

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 supports the same INNER JOIN + WHERE filter pattern verbatim.
# The ON-vs-WHERE trap with LEFT JOIN translates identically: filter on the
# heart type in WHERE for inner semantics, in ON for outer.
#
# CREATE TABLE posts (
#     post_id    INT          NOT NULL,
#     poster_id  INT          NOT NULL,
#     post_date  DATE         NOT NULL,
#     post_text  VARCHAR(256) NOT NULL,
#     PRIMARY KEY (post_id)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# CREATE TABLE reactions (
#     reaction_id   INT         NOT NULL,
#     post_id       INT         NOT NULL,
#     user_id       INT         NOT NULL,
#     reaction_type VARCHAR(16) NOT NULL,
#     PRIMARY KEY (reaction_id),
#     KEY ix_r_post_type (post_id, reaction_type),
#     CONSTRAINT fk_r_post FOREIGN KEY (post_id) REFERENCES posts(post_id)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO posts (post_id, poster_id, post_date, post_text) VALUES
#     (1, 101, '2023-01-15', 'Great day at the beach'),
#     (2, 102, '2023-01-20', 'Just finished a great book'),
#     (3, 101, '2023-02-10', 'Excited about the new project'),
#     (4, 103, '2023-02-22', 'Coffee and coding'),
#     (8, 101, '2023-04-25', 'Happy Friday everyone'),
#     (9, 106, '2023-05-08', 'Loving this weather');
#
# INSERT INTO reactions (reaction_id, post_id, user_id, reaction_type) VALUES
#     ( 1, 1, 201, 'heart'),   ( 2, 1, 202, 'like'),
#     ( 3, 1, 203, 'heart'),   ( 4, 2, 204, 'like'),
#     ( 5, 2, 205, 'heart'),   ( 6, 3, 206, 'heart'),
#     ( 7, 3, 207, 'heart'),   ( 8, 3, 208, 'heart'),
#     (18, 8, 218, 'heart'),   (19, 8, 219, 'heart'),
#     (20, 8, 220, 'heart'),   (21, 9, 221, 'like');
#
# SELECT p.post_id,
#        p.post_text,
#        COUNT(*) AS heart_count
# FROM posts p
# JOIN reactions r ON r.post_id = p.post_id
# WHERE r.reaction_type = 'heart'
# GROUP BY p.post_id, p.post_text
# ORDER BY heart_count DESC, p.post_id;
#
# -- Expected:
# -- (3, 'Excited about the new project', 3)
# -- (8, 'Happy Friday everyone', 3)
# -- (1, 'Great day at the beach', 2)
# -- (2, 'Just finished a great book', 1)
