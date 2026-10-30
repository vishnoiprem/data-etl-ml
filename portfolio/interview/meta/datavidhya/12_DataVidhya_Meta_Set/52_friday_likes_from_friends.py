"""
Q52: Friday Likes from Friends Only   [Medium | Inner Joins, Date/Time Functions]
DataVidhya slug: joins-friday-likes-from-friends

Count, per post author, the likes on their FRIDAY posts that came from users
they are friends with (friendship is bidirectional). Authors with zero
qualifying likes do not appear.

How to Think:
- Three tables, three separate jobs:
    posts       -> the author, and the Friday FILTER (on post_date)
    likes       -> the rows being counted
    friendships -> a membership PREDICATE, after being made bidirectional
- Make the friendship graph symmetric FIRST (UNION ALL both directions into an
  `edges` CTE), then join. Trying to express "either direction" inline as
  `(f.user_id_1 = a AND f.user_id_2 = b) OR (...)` works but is an OR-join,
  which Spark cannot hash and will run as a nested loop.
- "Authors with at least one qualifying like" is inner-join semantics, so no
  HAVING is needed.

The trap:
- Friday comes from `posts.post_date`, NOT `likes.like_date`. The question says
  so explicitly and the data is built to punish the confusion. Here every post
  is a Friday (2024-01-05 and 2024-01-12 both are), so filtering on like_date
  happens to give the same answer -- which is why reading the constraint
  matters more than testing.
- SELF-LIKES. Like 3 is user 101 liking their own post 2. 101 is not their own
  friend, so it does NOT count. An author is absent from their own friend list,
  so the friendship join drops it naturally -- but any solution that counts
  "likes from anyone in the graph" or adds self-edges will report 3 for user
  101 instead of 2.
- Bidirectionality. Like 5 is user 102 liking post 4 by author 103. Friendships
  are (101,102), (101,103), (102,104), (103,104) -- 102 and 103 are NOT friends,
  so it must not count. Getting the mirroring right is what separates 1 from 2
  for user 102, and user 103 must end up absent entirely.
- User 103 authored a Friday post that got a like, and still has no output row,
  because that like was not from a friend.

Spark note:
- `date_format(post_date, 'E') = 'Fri'` is locale-sensitive. `dayofweek()` is
  not, but it is 1-indexed on SUNDAY, so Friday is 6. Use the numeric form and
  say why.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("52-friday-likes-from-friends")
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


FRIDAY = 6   # dayofweek() is 1-indexed on Sunday

# ---------------------------------------------------------- sample data
# Exactly the rows DataVidhya ships with the question.
# 102 and 103 are NOT friends with each other. Like 3 is a self-like.
spark.sql("""
CREATE OR REPLACE TEMP VIEW friendships AS
SELECT * FROM VALUES
    (101, 102), (101, 103), (102, 104), (103, 104)
AS t(user_id_1, user_id_2)
""")
spark.sql("""
CREATE OR REPLACE TEMP VIEW likes AS
SELECT * FROM VALUES
    (1, 1, 102, DATE'2024-01-05'),
    (2, 1, 103, DATE'2024-01-05'),
    (3, 2, 101, DATE'2024-01-12'),
    (4, 3, 104, DATE'2024-01-12'),
    (5, 4, 102, DATE'2024-01-12')
AS t(like_id, post_id, liker_user_id, like_date)
""")
spark.sql("""
CREATE OR REPLACE TEMP VIEW posts AS
SELECT * FROM VALUES
    (1, 101, DATE'2024-01-05'),
    (2, 101, DATE'2024-01-12'),
    (3, 102, DATE'2024-01-12'),
    (4, 103, DATE'2024-01-12')
AS t(post_id, user_id, post_date)
""")

from pyspark.sql import functions as F

SQL = f"""
WITH edges AS (
    -- make the graph symmetric before joining
    SELECT user_id_1 AS a, user_id_2 AS b FROM friendships
    UNION ALL
    SELECT user_id_2 AS a, user_id_1 AS b FROM friendships
),
friday_posts AS (
    SELECT post_id, user_id
    FROM posts
    WHERE DAYOFWEEK(post_date) = {FRIDAY}     -- Friday from POST date
)
SELECT p.user_id,
       COUNT(*) AS friday_friend_likes
FROM friday_posts p
JOIN likes l ON l.post_id = p.post_id
JOIN edges e ON e.a = p.user_id              -- author ...
            AND e.b = l.liker_user_id        -- ... is friends with the liker
GROUP BY p.user_id
ORDER BY friday_friend_likes DESC, p.user_id
"""

spark.sql(SQL).show(truncate=False)

expect("Q52 Friday likes from friends", SQL, [(101, 2), (102, 1)])

# DataFrame API equivalent.
fr = spark.table("friendships")
edges = (fr.select(F.col("user_id_1").alias("a"), F.col("user_id_2").alias("b"))
         .unionAll(fr.select(F.col("user_id_2").alias("a"), F.col("user_id_1").alias("b"))))
friday_posts = (spark.table("posts")
                .filter(F.dayofweek("post_date") == FRIDAY)
                .select("post_id", "user_id"))
df = (friday_posts.join(spark.table("likes"), "post_id")
      .join(F.broadcast(edges),
            (F.col("a") == F.col("user_id")) & (F.col("b") == F.col("liker_user_id")))
      .groupBy("user_id").agg(F.count(F.lit(1)).alias("friday_friend_likes"))
      .orderBy(F.col("friday_friend_likes").desc(), F.col("user_id")))
assert [tuple(r) for r in df.collect()] == [(101, 2), (102, 1)]
print("[PASS] Q52 DataFrame API matches SQL")

# ------------------------------------------------ confirm both dates are Fridays
days = spark.sql("""
SELECT DISTINCT post_date, DAYOFWEEK(post_date) AS dow, DATE_FORMAT(post_date, 'E') AS nm
FROM posts ORDER BY post_date
""").collect()
assert all(r[1] == FRIDAY for r in days), days
print(f"[PASS] Q52 both post dates are Fridays (dayofweek 6): {[str(r[0]) for r in days]}")

# ------------------------------------------------ the self-like trap
# Like 3 is 101 liking their own post. Counting all likes on Friday posts
# gives 101 three instead of two.
all_likes = spark.sql("""
SELECT p.user_id, COUNT(*) AS likes_any_source
FROM posts p JOIN likes l ON l.post_id = p.post_id
WHERE DAYOFWEEK(p.post_date) = 6
GROUP BY p.user_id ORDER BY p.user_id
""").collect()
assert [(r[0], r[1]) for r in all_likes] == [(101, 3), (102, 1), (103, 1)], all_likes
print("[PASS] Q52 counting all likes gives 101 -> 3 (self-like) and revives 103")

# ------------------------------------------------ the bidirectional trap
# 102 liked 103's post but they are not friends, so 103 gets no row.
authors = {r[0] for r in spark.sql(SQL).collect()}
assert 103 not in authors, authors
non_friends = spark.sql("""
WITH edges AS (
    SELECT user_id_1 AS a, user_id_2 AS b FROM friendships
    UNION ALL SELECT user_id_2, user_id_1 FROM friendships
)
SELECT COUNT(*) FROM edges WHERE a = 103 AND b = 102
""").collect()[0][0]
assert non_friends == 0
print("[PASS] Q52 102 and 103 are not friends, so author 103 is absent from the output")

# ------------------------------------------------ one-directional graph undercounts
# CAREFUL: on the SHIPPED data every needed edge happens to be stored
# author-first, so the one-directional join coincidentally gives the right
# answer. It is still wrong, and only reordered input reveals it.
ONE_WAY_SQL = """
SELECT p.user_id, COUNT(*) AS c
FROM posts p
JOIN likes l ON l.post_id = p.post_id
JOIN friendships f ON f.user_id_1 = p.user_id AND f.user_id_2 = l.liker_user_id
WHERE DAYOFWEEK(p.post_date) = 6
GROUP BY p.user_id ORDER BY p.user_id
"""
one_way = [(r[0], r[1]) for r in spark.sql(ONE_WAY_SQL).collect()]
assert one_way == [(101, 2), (102, 1)], one_way
print("[PASS] Q52 on the shipped data the one-way join coincidentally agrees "
      "-- every edge is stored author-first")

# Store (102,101) instead of (101,102): the same friendship, the other way round.
# The bidirectional answer is unchanged; the one-way join silently drops a like.
spark.sql("""
CREATE OR REPLACE TEMP VIEW friendships AS
SELECT * FROM VALUES
    (102, 101), (101, 103), (102, 104), (103, 104)
AS t(user_id_1, user_id_2)
""")
expect("Q52 reversed storage does not change the bidirectional answer", SQL,
       [(101, 2), (102, 1)])

one_way_reversed = [(r[0], r[1]) for r in spark.sql(ONE_WAY_SQL).collect()]
assert one_way_reversed == [(101, 1), (102, 1)], one_way_reversed
print("[PASS] Q52 with the edge stored (102,101), the one-way join drops 101 to 1")

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 supports UNION ALL into a symmetric edges CTE, DAYOFWEEK()
# (1 = Sunday, 6 = Friday in MySQL too), and the same inner-join chain.
#
# CREATE TABLE friendships (
#     user_id_1  INT NOT NULL,
#     user_id_2  INT NOT NULL,
#     PRIMARY KEY (user_id_1, user_id_2)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# CREATE TABLE posts (
#     post_id   INT  NOT NULL,
#     user_id   INT  NOT NULL,
#     post_date DATE NOT NULL,
#     PRIMARY KEY (post_id),
#     KEY ix_posts_date (post_date)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# CREATE TABLE likes (
#     like_id        INT  NOT NULL,
#     post_id        INT  NOT NULL,
#     liker_user_id  INT  NOT NULL,
#     like_date      DATE NOT NULL,
#     PRIMARY KEY (like_id),
#     KEY ix_l_post (post_id),
#     CONSTRAINT fk_l_post FOREIGN KEY (post_id) REFERENCES posts(post_id)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO friendships (user_id_1, user_id_2) VALUES
#     (101, 102), (101, 103), (102, 104), (103, 104);
#
# INSERT INTO posts (post_id, user_id, post_date) VALUES
#     (1, 101, '2024-01-05'),
#     (2, 101, '2024-01-12'),
#     (3, 102, '2024-01-12'),
#     (4, 103, '2024-01-12');
#
# INSERT INTO likes (like_id, post_id, liker_user_id, like_date) VALUES
#     (1, 1, 102, '2024-01-05'),
#     (2, 1, 103, '2024-01-05'),
#     (3, 2, 101, '2024-01-12'),
#     (4, 3, 104, '2024-01-12'),
#     (5, 4, 102, '2024-01-12');
#
# WITH edges AS (
#     SELECT user_id_1 AS a, user_id_2 AS b FROM friendships
#     UNION ALL
#     SELECT user_id_2 AS a, user_id_1 AS b FROM friendships
# ),
# friday_posts AS (
#     SELECT post_id, user_id FROM posts WHERE DAYOFWEEK(post_date) = 6
# )
# SELECT p.user_id, COUNT(*) AS friday_friend_likes
# FROM friday_posts p
# JOIN likes  l ON l.post_id = p.post_id
# JOIN edges  e ON e.a = p.user_id AND e.b = l.liker_user_id
# GROUP BY p.user_id
# ORDER BY friday_friend_likes DESC, p.user_id;
#
# -- Expected: (101, 2), (102, 1).
