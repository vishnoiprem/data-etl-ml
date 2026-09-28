"""
Q34: Sentiment Analysis on Text   [Hard | CASE WHEN, String Manipulation, Aggregate Functions]
DataVidhya slug: sentiment-analysis-text

Score each review as (positive keyword occurrences - negative keyword
occurrences), case-insensitively, then roll up per product: total_reviews,
avg_sentiment_score, and counts of positive-scoring and negative-scoring
reviews. Score 0 is neutral and counts in neither.

How to Think:
- Two grains, so two layers. Layer 1 scores ONE REVIEW. Layer 2 aggregates
  reviews per product. Trying to do both at once is how the counts get wrong.
- Layer 2 needs three different aggregates over the same scored rows:
  COUNT(*), AVG(score), and two conditional counts. Conditional counts are
  `SUM(CASE WHEN ... THEN 1 ELSE 0 END)` -- or COUNT(CASE WHEN ... THEN 1 END),
  since COUNT ignores NULLs.

The trap:
- Neutral reviews. `positive + negative` does NOT equal `total_reviews`,
  because score = 0 is neither. So the two counts must both be strict: `> 0`
  and `< 0`. Writing negative as `<= 0` (or deriving it as total - positive)
  silently absorbs neutrals and is the intended failure.
- Note the CONTRAST with Q26 (`text-features`), which is the same corpus but a
  different rule: Q26 says punctuation is RETAINED in tokens, so "Excellent,"
  does not match. Q34 says nothing of the kind and asks for OCCURRENCES, so
  splitting on non-word characters is correct here. Two near-identical questions
  with opposite tokenising rules -- read the constraints, don't pattern-match.
- Substring matching is wrong: `LIKE '%love%'` matches "lovely" and `'%bad%'`
  matches "badge". Match whole tokens.
- Occurrences, not presence: a review saying "great great" scores 2, not 1. So
  count array elements; do not use a boolean EXISTS test.
- AVG over integers truncates in some engines. Here (2 + -2 + 2) / 3 = 0.667
  must round to 0.67, not to 0 or 1.

Spark note:
- higher-order `filter()` over the split array keeps scoring in one narrow
  projection, then a single shuffle for the GROUP BY.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("34-sentiment-analysis-text")
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


POSITIVE = ["great", "good", "excellent", "amazing",
            "love", "best", "fantastic", "wonderful"]
NEGATIVE = ["bad", "terrible", "awful", "worst",
            "poor", "hate", "horrible", "disappointing"]

# ---------------------------------------------------------- sample data
# Exactly the rows DataVidhya ships with the question.
# Scores: review 1 = +2, review 2 = -2, review 3 = +2  ->  avg 0.67
spark.createDataFrame(
    [
        (1, 101, "This product is great and amazing", "2024-01-15"),
        (2, 101, "Terrible quality worst experience ever", "2024-01-16"),
        (3, 101, "Love it fantastic product", "2024-01-17"),
    ],
    "review_id INT, product_id INT, review_text STRING, review_date STRING",
).createOrReplaceTempView("product_reviews")

from pyspark.sql import functions as F

SQL = r"""
WITH scored AS (
    SELECT review_id,
           product_id,
           size(filter(split(lower(review_text), '\\W+'), w -> array_contains(
                array('great','good','excellent','amazing',
                      'love','best','fantastic','wonderful'), w)))
         - size(filter(split(lower(review_text), '\\W+'), w -> array_contains(
                array('bad','terrible','awful','worst',
                      'poor','hate','horrible','disappointing'), w)))
             AS sentiment_score
    FROM product_reviews
)
SELECT product_id,
       COUNT(*)                                      AS total_reviews,
       ROUND(AVG(sentiment_score), 2)                AS avg_sentiment_score,
       SUM(CASE WHEN sentiment_score > 0 THEN 1 ELSE 0 END) AS positive_review_count,
       SUM(CASE WHEN sentiment_score < 0 THEN 1 ELSE 0 END) AS negative_review_count
FROM scored
GROUP BY product_id
ORDER BY product_id
"""

spark.sql(SQL).show(truncate=False)

expect("Q34 sentiment rollup per product", SQL, [(101, 3, 0.67, 2, 1)])

# DataFrame API equivalent.
tokens = F.split(F.lower("review_text"), r"\W+")
score = (F.size(F.filter(tokens, lambda w: w.isin(POSITIVE)))
         - F.size(F.filter(tokens, lambda w: w.isin(NEGATIVE))))
df = (spark.table("product_reviews")
      .withColumn("sentiment_score", score)
      .groupBy("product_id")
      .agg(F.count(F.lit(1)).alias("total_reviews"),
           F.round(F.avg("sentiment_score"), 2).alias("avg_sentiment_score"),
           F.sum(F.when(F.col("sentiment_score") > 0, 1).otherwise(0)).alias("positive_review_count"),
           F.sum(F.when(F.col("sentiment_score") < 0, 1).otherwise(0)).alias("negative_review_count"))
      .orderBy("product_id"))
assert [(r[0], r[1], float(r[2]), r[3], r[4]) for r in df.collect()] == [(101, 3, 0.67, 2, 1)]
print("[PASS] Q34 DataFrame API matches SQL")

# ------------------------------------------------ the neutral-review trap
# Add a review that scores exactly 0. It must count in total_reviews only, so
# positive + negative < total.
spark.createDataFrame(
    [
        (1, 101, "This product is great and amazing", "2024-01-15"),
        (2, 101, "Terrible quality worst experience ever", "2024-01-16"),
        (3, 101, "Love it fantastic product", "2024-01-17"),
        (4, 101, "It arrived on Tuesday in a box", "2024-01-18"),   # score 0
        (5, 101, "great but terrible", "2024-01-19"),               # +1 -1 = 0
    ],
    "review_id INT, product_id INT, review_text STRING, review_date STRING",
).createOrReplaceTempView("product_reviews")

# Scores are now 2, -2, 2, 0, 0 -> avg 2/5 = 0.4, positives 2, negatives 1.
got = expect("Q34 neutral reviews counted in neither bucket", SQL, [(101, 5, 0.4, 2, 1)])
total, pos, neg = got[0][1], got[0][3], got[0][4]
assert pos + neg == 3 and total == 5, got
print("[PASS] Q34 positive + negative (3) != total_reviews (5) -- neutrals are excluded")

# ------------------------------------------------ occurrences, not presence
repeats = spark.sql(r"""
SELECT size(filter(split(lower('great great good'), '\\W+'),
            w -> array_contains(array('great','good','excellent','amazing',
                                      'love','best','fantastic','wonderful'), w))) AS hits
""").collect()[0][0]
assert repeats == 3, repeats
print("[PASS] Q34 repeated keywords count each time (3, not 2) -- occurrences, not presence")

# ------------------------------------------------ substring matching is wrong
substring_hit = spark.sql("SELECT 'lovely day' LIKE '%love%' AS m").collect()[0][0]
token_hit = spark.sql(r"""
SELECT array_contains(split(lower('lovely day'), '\\W+'), 'love') AS m
""").collect()[0][0]
assert substring_hit is True and token_hit is False
print("[PASS] Q34 'lovely' matches LIKE '%love%' but is not the token 'love'")

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 has no array types or higher-order filter. The portable substitute
# is JSON_TABLE: rebuild the review text as a JSON array of word tokens and
# join row-per-token, then count positive/negative hits. The score is
# occurrences, not presence -- a review saying "great great" scores 2.
# Splits on non-word characters (NOT whitespace only, the way Q26 keeps
# punctuation attached) -- that is the opposite rule and the question
# states it explicitly.
#
# CREATE TABLE product_reviews (
#     review_id   INT         NOT NULL,
#     product_id  INT         NOT NULL,
#     review_text TEXT        NOT NULL,
#     review_date DATE        NOT NULL,
#     PRIMARY KEY (review_id),
#     KEY ix_pr_product (product_id)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO product_reviews (review_id, product_id, review_text, review_date) VALUES
#     (1, 101, 'This product is great and amazing',                 '2024-01-15'),
#     (2, 101, 'Terrible quality worst experience ever',            '2024-01-16'),
#     (3, 101, 'Love it fantastic product',                         '2024-01-17'),
#     (4, 101, 'It arrived on Tuesday in a box',                    '2024-01-18'),
#     (5, 101, 'great but terrible',                                '2024-01-19');
#
# -- Tokenise via JSON_TABLE over the regex-split text. MySQL 8 has no native
# -- regex split, so substitute: replace each non-word run with a unique
# -- separator (here ' '), then split on space. Keep occurrences, not
# -- presence, so "great great" gives two rows.
# WITH tokens AS (
#     SELECT r.review_id, r.product_id, LOWER(j.word) AS word
#     FROM product_reviews r
#     JOIN JSON_TABLE(
#              CONCAT('["',
#                     REPLACE(
#                        REGEXP_REPLACE(r.review_text, '[^a-zA-Z]+', ' '),
#                        ' ', '","'),
#                     '"]'),
#              '$[*]' COLUMNS (word VARCHAR(64) PATH '$')
#          ) j
#     WHERE LENGTH(j.word) > 0
# ),
-- (continuation)
# scored AS (
#     SELECT review_id, product_id,
#            SUM(CASE WHEN word IN ('great','good','excellent','amazing',
#                                   'love','best','fantastic','wonderful')
#                     THEN 1 ELSE 0 END)
#          - SUM(CASE WHEN word IN ('bad','terrible','awful','worst',
#                                   'poor','hate','horrible','disappointing')
#                     THEN 1 ELSE 0 END) AS sentiment_score
#     FROM tokens
#     GROUP BY review_id, product_id
# )
# SELECT product_id,
#        COUNT(*)                                               AS total_reviews,
#        ROUND(AVG(sentiment_score), 2)                          AS avg_sentiment_score,
#        SUM(CASE WHEN sentiment_score > 0 THEN 1 ELSE 0 END)   AS positive_review_count,
#        SUM(CASE WHEN sentiment_score < 0 THEN 1 ELSE 0 END)   AS negative_review_count
# FROM scored
# GROUP BY product_id
# ORDER BY product_id;
#
# -- Expected: (101, 5, 0.4, 2, 1) -- neutral reviews count in total only.
