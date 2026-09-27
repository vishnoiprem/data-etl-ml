"""
Q26: Create Features from Text   [Hard | String Manipulation, Feature Engineering]
DataVidhya slug: text-features

Per review, emit word_count, char_count, avg_word_length, contains_negative,
and sentiment_score (positive keyword tokens minus negative keyword tokens).

How to Think:
- Five features, one pass. Build the token array ONCE in a CTE, then derive
  every feature off it. Re-splitting the string per feature is the slow answer
  and the one that drifts when the split rule changes.
- "Exact tokens, case-insensitive" is a token-equality test, NOT a substring
  test. `LIKE '%bad%'` would match "badge" and is wrong.

The trap:
- Punctuation is RETAINED in tokens, so "Excellent," does NOT match the
  keyword `excellent`. Review 5 scores 1 (only `best` matches), not 2.
  Every naive solution that strips punctuation returns 2 here and fails.
- char_count counts EVERY character including whitespace, so avg_word_length
  (char_count / word_count) is inflated by the spaces -- it is not the mean
  length of a word. Don't "fix" it; the spec defines it this way.

Spark note:
- higher-order `filter(array, lambda)` keeps this a single narrow projection:
  no explode, no shuffle, no regroup.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("26-text-features")
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
spark.createDataFrame(
    [
        (1, "P002", "This product is great and amazing", "2024-01-02"),
        (2, "P003", "Terrible quality, very bad experience", "2024-01-03"),
        (5, "P001", "Excellent, best product I have", "2024-01-06"),
    ],
    ["review_id", "product_id", "review_text", "review_date"],
).createOrReplaceTempView("reviews")

from pyspark.sql import functions as F

POSITIVE = ["great", "good", "excellent", "amazing", "love", "best"]
NEGATIVE = ["bad", "terrible", "awful", "worst", "poor", "hate"]

_POS_SQL = ", ".join(f"'{w}'" for w in POSITIVE)
_NEG_SQL = ", ".join(f"'{w}'" for w in NEGATIVE)

SQL = f"""
WITH tokenized AS (
    SELECT review_id,
           product_id,
           review_text,
           split(review_text, '\\\\s+') AS words
    FROM reviews
),
features AS (
    SELECT review_id,
           product_id,
           size(words)          AS word_count,
           length(review_text)  AS char_count,
           size(filter(words, w -> array_contains(
                array({_POS_SQL}),
                lower(w)))) AS pos_hits,
           size(filter(words, w -> array_contains(
                array({_NEG_SQL}),
                lower(w)))) AS neg_hits
    FROM tokenized
)
SELECT review_id,
       product_id,
       word_count,
       char_count,
       ROUND(char_count / word_count, 2)          AS avg_word_length,
       CASE WHEN neg_hits > 0 THEN 1 ELSE 0 END   AS contains_negative,
       pos_hits - neg_hits                        AS sentiment_score
FROM features
ORDER BY review_id
"""

spark.sql(SQL).show(truncate=False)

expect("Q26 text features", SQL, [
    (1, "P002", 6, 33, 5.5, 0, 2),
    (2, "P003", 5, 37, 7.4, 1, -2),
    (5, "P001", 5, 30, 6.0, 0, 1),
])

# DataFrame API equivalent -- same single-projection plan.
words = F.split(F.col("review_text"), r"\s+")
pos = F.size(F.filter(words, lambda w: F.lower(w).isin(POSITIVE)))
neg = F.size(F.filter(words, lambda w: F.lower(w).isin(NEGATIVE)))

df = (spark.table("reviews")
      .select(
          "review_id",
          "product_id",
          F.size(words).alias("word_count"),
          F.length("review_text").alias("char_count"),
          F.round(F.length("review_text") / F.size(words), 2).alias("avg_word_length"),
          F.when(neg > 0, F.lit(1)).otherwise(F.lit(0)).alias("contains_negative"),
          (pos - neg).alias("sentiment_score"))
      .orderBy("review_id"))
assert [tuple(r) for r in df.collect()] == [
    (1, "P002", 6, 33, 5.5, 0, 2),
    (2, "P003", 5, 37, 7.4, 1, -2),
    (5, "P001", 5, 30, 6.0, 0, 1),
]
print("[PASS] Q26 DataFrame API matches SQL")

# The punctuation trap, asserted so it stays documented:
# "Excellent," is not the token `excellent`, so only `best` scores.
trap = spark.sql(r"""
SELECT size(filter(split('Excellent, best product I have', '\\s+'),
            w -> array_contains(array('great','good','excellent','amazing','love','best'),
                                lower(w)))) AS hits
""").collect()[0][0]
assert trap == 1, f"punctuation trap changed: expected 1 keyword hit, got {trap}"
print("[PASS] Q26 punctuation retained in tokens -> 'Excellent,' does not match 'excellent'")