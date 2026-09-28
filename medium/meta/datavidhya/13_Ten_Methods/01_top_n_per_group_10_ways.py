"""
TOP-N PER GROUP — 10 DIFFERENT METHODS
Problem: for each user, return their top 2 posts by engagement.

Why learn ten ways to do one thing: Meta interviewers ask "can you do that
another way?" and "why did you pick that one?" constantly. Having a second and
third approach ready is the difference between "knows a pattern" and "knows SQL".

THE TIE IS THE POINT. User 2 has two posts tied at 70 engagement, so the ten
methods split into two families:

  EXACTLY-N (5 rows)  - needs a deterministic tie-break. ROW_NUMBER and friends.
  WITH-TIES (6 rows)  - returns everything at the cut line. RANK / DENSE_RANK.

Neither is "correct" — they answer different questions. In an interview, ASK:
"user 2 has a tie at the cut-off; do you want exactly 2 rows, or all rows tied
at 2nd place?" That question is scored.

Every exactly-N method below breaks ties by post_id ASC so all five agree.

Data:
  u1: p1=50  p2=80  p3=30            -> top2: p2(80), p1(50)
  u2: p4=90  p5=70  p6=70   <- TIE   -> top2: p4(90), p5(70)  [p6 loses on id]
  u3: p7=20                          -> top2: p7(20)  (only has one)
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("01-top-n-per-group-10-ways")
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


from pyspark.sql import functions as F, Window
from pyspark.sql.types import StructType, StructField, LongType

spark.createDataFrame([
    (1, 1, 50), (2, 1, 80), (3, 1, 30),
    (4, 2, 90), (5, 2, 70), (6, 2, 70),
    (7, 3, 20),
], ["post_id", "user_id", "engagement"]).createOrReplaceTempView("posts")

N = 2
CANON = [(1, 2, 80), (1, 1, 50), (2, 4, 90), (2, 5, 70), (3, 7, 20)]
WITH_TIES = [(1, 2, 80), (1, 1, 50), (2, 4, 90), (2, 5, 70), (2, 6, 70), (3, 7, 20)]

results = {}


def check(name, rows, expected, note):
    got = [tuple(r) for r in rows]
    status = "PASS" if got == expected else "FAIL"
    results[name] = status
    print(f"[{status}] {name:42s} {len(got)} rows — {note}")
    if got != expected:
        print(f"        expected {expected}")
        print(f"        got      {got}")
    return got == expected


def sql_rows(q):
    return spark.sql(q).collect()


# ---------------------------------------------------------------- 1
# ROW_NUMBER — the default answer. Exactly N per group, always.
check("1. ROW_NUMBER + filter", sql_rows(f"""
SELECT user_id, post_id, engagement FROM (
  SELECT user_id, post_id, engagement,
         ROW_NUMBER() OVER (PARTITION BY user_id
                            ORDER BY engagement DESC, post_id ASC) AS rn
  FROM posts) t
WHERE rn <= {N}
ORDER BY user_id, engagement DESC, post_id
"""), CANON, "exactly N; arbitrary tie-break made deterministic")

# ---------------------------------------------------------------- 2
# RANK — ties share a rank and CONSUME the next one (1,2,2,4...).
check("2. RANK + filter (with ties)", sql_rows(f"""
SELECT user_id, post_id, engagement FROM (
  SELECT user_id, post_id, engagement,
         RANK() OVER (PARTITION BY user_id ORDER BY engagement DESC) AS rk
  FROM posts) t
WHERE rk <= {N}
ORDER BY user_id, engagement DESC, post_id
"""), WITH_TIES, "returns 6: both 70s tie at rank 2")

# ---------------------------------------------------------------- 3
# DENSE_RANK — ties share a rank, NO gap after (1,2,2,3...).
# Identical to RANK here; they diverge when you ask for rank <= 3.
check("3. DENSE_RANK + filter (with ties)", sql_rows(f"""
SELECT user_id, post_id, engagement FROM (
  SELECT user_id, post_id, engagement,
         DENSE_RANK() OVER (PARTITION BY user_id ORDER BY engagement DESC) AS dr
  FROM posts) t
WHERE dr <= {N}
ORDER BY user_id, engagement DESC, post_id
"""), WITH_TIES, "same as RANK at N=2; differs at N=3")

# ---------------------------------------------------------------- 4
# Correlated scalar subquery: "how many rows in my group beat me?"
# Pre-window-function classic. Readable, but O(n^2) per group.
check("4. Correlated subquery COUNT", sql_rows(f"""
SELECT p.user_id, p.post_id, p.engagement
FROM posts p
WHERE (SELECT COUNT(*) FROM posts q
       WHERE q.user_id = p.user_id
         AND (q.engagement > p.engagement
              OR (q.engagement = p.engagement AND q.post_id < p.post_id))) < {N}
ORDER BY p.user_id, p.engagement DESC, p.post_id
"""), CANON, "no window functions; O(n^2) per group")

# ---------------------------------------------------------------- 5
# Self-join + GROUP BY/HAVING: same idea as 4, expressed as a join.
# Counts rows >= me (including me), keeps those with count <= N.
check("5. Self-join + HAVING COUNT", sql_rows(f"""
SELECT p.user_id, p.post_id, p.engagement
FROM posts p
JOIN posts q
  ON q.user_id = p.user_id
 AND (q.engagement > p.engagement
      OR (q.engagement = p.engagement AND q.post_id <= p.post_id))
GROUP BY p.user_id, p.post_id, p.engagement
HAVING COUNT(*) <= {N}
ORDER BY p.user_id, p.engagement DESC, p.post_id
"""), CANON, "join form of #4; one shuffle, fans out badly")

# ---------------------------------------------------------------- 6
# LEFT SEMI JOIN against a ranked key set. Useful when the fact table is wide:
# rank a narrow (key, order-col) projection, then semi-join to avoid shuffling
# every column.
check("6. LEFT SEMI JOIN on ranked keys", sql_rows(f"""
WITH ranked AS (
  SELECT post_id FROM (
    SELECT post_id, user_id,
           ROW_NUMBER() OVER (PARTITION BY user_id
                              ORDER BY engagement DESC, post_id ASC) AS rn
    FROM posts) t
  WHERE rn <= {N}
)
SELECT p.user_id, p.post_id, p.engagement
FROM posts p
LEFT SEMI JOIN ranked r ON r.post_id = p.post_id
ORDER BY p.user_id, p.engagement DESC, p.post_id
"""), CANON, "ranks narrow keys only — best for wide tables")

# ---------------------------------------------------------------- 7
# Collect into an array, sort, slice, explode. One shuffle, no window.
# array_sort on a struct sorts field-by-field, so negating engagement gives
# DESC then post_id ASC.
check("7. collect_list + array_sort + slice", sql_rows(f"""
WITH agg AS (
  SELECT user_id,
         SLICE(ARRAY_SORT(COLLECT_LIST(STRUCT(-engagement AS neg, post_id, engagement))),
               1, {N}) AS top
  FROM posts GROUP BY user_id
)
SELECT user_id, x.post_id, x.engagement
FROM agg LATERAL VIEW EXPLODE(top) e AS x
ORDER BY user_id, x.engagement DESC, x.post_id
"""), CANON, "single shuffle; memory risk on huge groups")

# ---------------------------------------------------------------- 8
# PySpark DataFrame API — same physical plan as #1, different surface.
w = Window.partitionBy("user_id").orderBy(F.col("engagement").desc(), F.col("post_id").asc())
df8 = (spark.table("posts")
       .withColumn("rn", F.row_number().over(w))
       .filter(F.col("rn") <= N)
       .orderBy("user_id", F.col("engagement").desc(), "post_id")
       .select("user_id", "post_id", "engagement"))
check("8. DataFrame API window", df8.collect(), CANON, "identical plan to #1")

# ---------------------------------------------------------------- 9
# RDD groupByKey + sort in Python. Shown because interviewers ask, and because
# knowing WHY it is bad matters: groupByKey shuffles every row of every group to
# one executor with no map-side reduction. Never use it in production.
rdd9 = (spark.table("posts").rdd
        .map(lambda r: (r["user_id"], (r["post_id"], r["engagement"])))
        .groupByKey()
        .flatMap(lambda kv: [
            (kv[0], p, e) for p, e in
            sorted(kv[1], key=lambda t: (-t[1], t[0]))[:N]])
        .collect())
check("9. RDD groupByKey + sorted", sorted(rdd9, key=lambda t: (t[0], -t[2], t[1])),
      CANON, "works, but groupByKey has no map-side combine — avoid")

# ---------------------------------------------------------------- 10
# applyInPandas — a real Pandas DataFrame per group. The escape hatch when the
# per-group logic is genuinely hard to express in SQL. Costs serialisation to
# Arrow and back, and each group must fit in one executor's memory.
schema10 = StructType([
    StructField("user_id", LongType()),
    StructField("post_id", LongType()),
    StructField("engagement", LongType()),
])


def top_n_pandas(pdf):
    out = pdf.sort_values(["engagement", "post_id"], ascending=[False, True]).head(N)
    return out[["user_id", "post_id", "engagement"]]


df10 = (spark.table("posts")
        .groupBy("user_id")
        .applyInPandas(top_n_pandas, schema=schema10)
        .orderBy("user_id", F.col("engagement").desc(), "post_id"))
check("10. applyInPandas (nlargest per group)", df10.collect(), CANON,
      "Pandas per group; Arrow serialisation cost")

# ---------------------------------------------------------------- summary
print()
failed = [k for k, v in results.items() if v != "PASS"]
print(f"{len(results) - len(failed)}/{len(results)} methods produced the expected result")
if failed:
    raise AssertionError(f"failed methods: {failed}")

print("""
WHICH ONE TO USE
  default            -> #1 ROW_NUMBER (or #8, same plan). Say the tie-break.
  ties matter        -> #2 RANK / #3 DENSE_RANK
  wide fact table    -> #6 LEFT SEMI on ranked narrow keys
  no window funcs    -> #4 correlated subquery (interview constraint only)
  small groups, 1 job-> #7 collect_list + slice
  genuinely complex
  per-group logic    -> #10 applyInPandas
  never in prod      -> #9 RDD groupByKey
""")

# ---- MySQL way ----------------------------------------------------------
# CREATE TABLE + sample data:
#   CREATE TABLE posts (
#       post_id     INT PRIMARY KEY,
#       user_id     INT NOT NULL,
#       engagement  INT NOT NULL,
#       KEY idx_posts_user_eng (user_id, engagement DESC)
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#   INSERT INTO posts (post_id, user_id, engagement) VALUES
#       (1, 1, 50), (2, 1, 80), (3, 1, 30),
#       (4, 2, 90), (5, 2, 70), (6, 2, 70),
#       (7, 3, 20);
#
# -- 1. ROW_NUMBER + filter  -> CANON (exactly 5 rows)
# SELECT user_id, post_id, engagement
# FROM (
#   SELECT user_id, post_id, engagement,
#          ROW_NUMBER() OVER (PARTITION BY user_id
#                             ORDER BY engagement DESC, post_id ASC) AS rn
#   FROM posts
# ) t
# WHERE rn <= 2
# ORDER BY user_id, engagement DESC, post_id;
#
# -- 2. RANK + filter (with ties)  -> WITH_TIES (6 rows, both 70s kept)
# SELECT user_id, post_id, engagement
# FROM (
#   SELECT user_id, post_id, engagement,
#          RANK() OVER (PARTITION BY user_id ORDER BY engagement DESC) AS rk
#   FROM posts
# ) t
# WHERE rk <= 2
# ORDER BY user_id, engagement DESC, post_id;
#
# -- 3. DENSE_RANK + filter (with ties)  -> WITH_TIES (same as RANK at N=2)
# SELECT user_id, post_id, engagement
# FROM (
#   SELECT user_id, post_id, engagement,
#          DENSE_RANK() OVER (PARTITION BY user_id ORDER BY engagement DESC) AS dr
#   FROM posts
# ) t
# WHERE dr <= 2
# ORDER BY user_id, engagement DESC, post_id;
#
# -- 4. Correlated subquery COUNT  -> CANON (pre-window classic, O(n^2))
# SELECT p.user_id, p.post_id, p.engagement
# FROM posts p
# WHERE (SELECT COUNT(*) FROM posts q
#        WHERE q.user_id = p.user_id
#          AND (q.engagement > p.engagement
#               OR (q.engagement = p.engagement AND q.post_id < p.post_id))) < 2
# ORDER BY p.user_id, p.engagement DESC, p.post_id;
#
# -- 5. Self-join + HAVING COUNT  -> CANON (join form of #4)
# SELECT p.user_id, p.post_id, p.engagement
# FROM posts p
# JOIN posts q
#   ON q.user_id = p.user_id
#  AND (q.engagement > p.engagement
#       OR (q.engagement = p.engagement AND q.post_id <= p.post_id))
# GROUP BY p.user_id, p.post_id, p.engagement
# HAVING COUNT(*) <= 2
# ORDER BY p.user_id, p.engagement DESC, p.post_id;
#
# -- 6. LEFT SEMI JOIN on ranked keys  -> CANON
# -- MySQL has no LEFT SEMI JOIN. Two portable substitutes:
# --   (a) INNER JOIN + DISTINCT
# --   (b) WHERE EXISTS ( ... )   <-- usually preferred by the optimizer
# WITH ranked AS (
#   SELECT post_id FROM (
#     SELECT post_id, user_id,
#            ROW_NUMBER() OVER (PARTITION BY user_id
#                               ORDER BY engagement DESC, post_id ASC) AS rn
#     FROM posts
#   ) t
#   WHERE rn <= 2
# )
# SELECT DISTINCT p.user_id, p.post_id, p.engagement
# FROM posts p
# INNER JOIN ranked r ON r.post_id = p.post_id
# ORDER BY p.user_id, p.engagement DESC, p.post_id;
# -- Equivalent WHERE EXISTS form:
# -- SELECT p.user_id, p.post_id, p.engagement
# -- FROM posts p
# -- WHERE EXISTS (SELECT 1 FROM ranked r WHERE r.post_id = p.post_id)
# -- ORDER BY p.user_id, p.engagement DESC, p.post_id;
#
# -- 7. collect_list + array_sort + slice + LATERAL VIEW EXPLODE
# -- NOT portable. MySQL 8.0 has no COLLECT_LIST / ARRAY_SORT / EXPLODE.
# -- MySQL has JSON_ARRAYAGG + JSON_TABLE as the closest analogue, but the
# -- idiomatic answer is: just use method #1 (ROW_NUMBER). It's simpler, the
# -- optimizer handles it well, and you avoid per-group array materialisation.
# -- Skipped on purpose — see note below.
#
# -- 8. PySpark DataFrame API window
# -- Spark-specific. Same physical plan as #1. Not applicable to MySQL.
#
# -- 9. RDD groupByKey + sorted
# -- Spark-specific. Not applicable to MySQL.
#
# -- 10. applyInPandas (Pandas per group)
# -- Spark-specific. Not applicable to MySQL. In MySQL you'd express any
# -- genuinely custom per-group logic in a stored procedure or app code.
#
# Notes:
# - Methods 1-5 translate cleanly: window functions (ROW_NUMBER / RANK /
#   DENSE_RANK) and correlated subqueries are all in MySQL 8.0+. CANON and
#   WITH_TIES row sets come out identical to the Spark results.
# - Method 6's LEFT SEMI JOIN has no direct MySQL spelling; use INNER JOIN +
#   DISTINCT or WHERE EXISTS against the ranked CTE. Both let MySQL stop at
#   the first match per outer row, which is the semi-join semantics we want.
# - Method 7 (collect_list + array_sort + EXPLODE) is Spark-only; the
#   portable replacement in MySQL is the ROW_NUMBER pattern from #1 — same
#   answer, no array materialisation, no LATERAL VIEW trick.
# - Methods 8-10 are Spark abstractions (DataFrame API, RDDs, applyInPandas)
#   with no MySQL counterpart; they exist in the original file to show
#   Spark-internal alternatives, not SQL alternatives.
# - At Meta volume the B-tree index on (user_id, engagement) lets MySQL stream
#   each user's rows already in DESC-by-engagement order (descending indexes
#   are supported since 8.0), so the ROW_NUMBER window is cheap. The fully-
# -sorted tie-break on (engagement DESC, post_id ASC) is portable everywhere.
