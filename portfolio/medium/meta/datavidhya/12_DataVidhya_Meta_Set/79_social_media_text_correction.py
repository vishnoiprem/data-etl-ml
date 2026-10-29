"""
Q79: Social Media Text Correction   [Easy | Regular Expression]
DataVidhya slug: social-media-text-correction

Replace every CASE-SENSITIVE occurrence of 'Python' with 'PySpark' in `text`.
Return all rows, ordered by comments ascending, with columns in the order
comments, date, id, likes, platform, shares, text.

How to Think:
- One row-level string replace, no aggregation, no filter, nothing dropped.
- `replace(text, 'Python', 'PySpark')` is the right tool: plain literal
  substitution, no pattern to get wrong. `regexp_replace` also works and is
  what you need the moment the match becomes a pattern (e.g. word boundaries).

The trap:
- COLUMN ORDER. The output is comments, date, id, likes, platform, shares, text
  -- i.e. ALPHABETICAL, which is nothing like the table's declaration order
  (id, text, date, likes, comments, shares, platform). `SELECT *` returns the
  right VALUES in the wrong SHAPE, which is the intended failure.
- The sort key is `comments`, not id and not date. The expected output starts
  with id 6 (comments 1) and ends with id 5 (comments 9) -- so an id-ordered
  answer is visibly wrong, and a date-ordered one coincides with id order here.
- Case-SENSITIVE: 'python' in lowercase must NOT be replaced. Spark's `replace`
  is case-sensitive by default, so the correct answer needs no extra work --
  but `regexp_replace` with an `(?i)` flag, or a lower()-then-replace, would
  over-match. Asserted below, since no shipped row has lowercase 'python'.
- 'date' is a SQL keyword used as a column name -- backtick it.
- Every occurrence, not just the first: `replace` is global by default in Spark.

Spark note:
- A narrow projection plus one sort. Nothing else.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("79-social-media-text-correction")
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


OLD, NEW = "Python", "PySpark"

# ---------------------------------------------------------- sample data
# Exactly the rows DataVidhya ships with the question.
spark.sql("""
CREATE OR REPLACE TEMP VIEW correct_social_media_post AS
SELECT * FROM VALUES
    (1, 'This is a Python post.',                     DATE'2022-03-01', 10, 3, 2, 'Twitter'),
    (2, 'Another post about Python.',                 DATE'2022-03-02', 20, 5, 3, 'Instagram'),
    (3, 'Python is great for data analysis.',         DATE'2022-03-03', 30, 2, 4, 'Facebook'),
    (4, 'I am learning Python for machine learning.', DATE'2022-03-04', 40, 7, 5, 'Twitter'),
    (5, 'Python vs. R for data science.',             DATE'2022-03-05', 50, 9, 6, 'Instagram'),
    (6, 'Python web development is awesome.',         DATE'2022-03-06', 60, 1, 1, 'Facebook'),
    (7, 'Python for finance.',                        DATE'2022-03-07', 70, 4, 3, 'Twitter'),
    (8, 'Python libraries for data visualization.',   DATE'2022-03-08', 80, 6, 2, 'Instagram')
AS t(id, text, `date`, likes, comments, shares, platform)
""")

from pyspark.sql import functions as F

# Columns in the required (alphabetical) order; `date` backticked.
SQL = f"""
SELECT comments,
       `date`,
       id,
       likes,
       platform,
       shares,
       REPLACE(text, '{OLD}', '{NEW}') AS text
FROM correct_social_media_post
ORDER BY comments
"""

spark.sql(SQL).show(truncate=False)

import datetime as dt


def d(day):
    return dt.date(2022, 3, day)


EXPECTED = [
    (1, d(6), 6, 60, "Facebook",  1, "PySpark web development is awesome."),
    (2, d(3), 3, 30, "Facebook",  4, "PySpark is great for data analysis."),
    (3, d(1), 1, 10, "Twitter",   2, "This is a PySpark post."),
    (4, d(7), 7, 70, "Twitter",   3, "PySpark for finance."),
    (5, d(2), 2, 20, "Instagram", 3, "Another post about PySpark."),
    (6, d(8), 8, 80, "Instagram", 2, "PySpark libraries for data visualization."),
    (7, d(4), 4, 40, "Twitter",   5, "I am learning PySpark for machine learning."),
    (9, d(5), 5, 50, "Instagram", 6, "PySpark vs. R for data science."),
]
expect("Q79 Python -> PySpark, ordered by comments", SQL, EXPECTED)

# DataFrame API equivalent.
df = (spark.table("correct_social_media_post")
      .select("comments", "date", "id", "likes", "platform", "shares",
              F.replace(F.col("text"), F.lit(OLD), F.lit(NEW)).alias("text"))
      .orderBy("comments"))
assert [tuple(r) for r in df.collect()] == EXPECTED
print("[PASS] Q79 DataFrame API matches SQL")

# ------------------------------------------------ the column-order trap
cols = spark.sql(SQL).columns
assert cols == ["comments", "date", "id", "likes", "platform", "shares", "text"], cols
table_cols = spark.table("correct_social_media_post").columns
assert table_cols == ["id", "text", "date", "likes", "comments", "shares", "platform"]
print(f"[PASS] Q79 output order {cols} differs from the table's {table_cols}")

# ------------------------------------------------ the sort-key trap
by_comments = [r[2] for r in spark.sql(SQL).collect()]
assert by_comments == [6, 3, 1, 7, 2, 8, 4, 5], by_comments
print("[PASS] Q79 ordering by comments gives ids 6,3,1,7,2,8,4,5 -- not 1..8")

# ------------------------------------------------ nothing is dropped
assert spark.sql(SQL).count() == spark.table("correct_social_media_post").count() == 8
print("[PASS] Q79 8 rows in, 8 rows out")

# ------------------------------------------------ case sensitivity
spark.sql("""
CREATE OR REPLACE TEMP VIEW correct_social_media_post AS
SELECT * FROM VALUES
    (1, 'Python and python and PYTHON', DATE'2022-03-01', 1, 1, 1, 'Twitter')
AS t(id, text, `date`, likes, comments, shares, platform)
""")
expect("Q79 only the exact-case 'Python' is replaced", SQL, [
    (1, d(1), 1, 1, "Twitter", 1, "PySpark and python and PYTHON"),
])

insensitive = spark.sql(f"""
SELECT REGEXP_REPLACE(text, '(?i){OLD}', '{NEW}') AS t
FROM correct_social_media_post
""").collect()[0][0]
assert insensitive == "PySpark and PySpark and PySpark", insensitive
print("[PASS] Q79 a case-insensitive regex over-matches all three spellings")

# ------------------------------------------------ every occurrence, not just the first
spark.sql("""
CREATE OR REPLACE TEMP VIEW correct_social_media_post AS
SELECT * FROM VALUES
    (1, 'Python, Python, and more Python', DATE'2022-03-01', 1, 1, 1, 'Twitter')
AS t(id, text, `date`, likes, comments, shares, platform)
""")
expect("Q79 all occurrences in a row are replaced", SQL, [
    (1, d(1), 1, 1, "Twitter", 1, "PySpark, PySpark, and more PySpark"),
])

# ---- MySQL way ----------------------------------------------------------
# MySQL's REPLACE(str, from, to) is a global literal substitution and is
# case-sensitive, just like Spark's. The `date` column needs backticks
# because it collides with a reserved word.
#
# CREATE TABLE correct_social_media_post (
#     id        INT          NOT NULL,
#     text      TEXT         NOT NULL,
#     date      DATE         NOT NULL,
#     likes     INT          NOT NULL,
#     comments  INT          NOT NULL,
#     shares    INT          NOT NULL,
#     platform  VARCHAR(16)  NOT NULL,
#     PRIMARY KEY (id),
#     KEY ix_csmp_comments (comments)        -- the spec's sort key
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO correct_social_media_post
#     (id, text, `date`, likes, comments, shares, platform) VALUES
#     (1, 'This is a Python post.',                     '2022-03-01', 10, 3, 2, 'Twitter'),
#     (2, 'Another post about Python.',                 '2022-03-02', 20, 5, 3, 'Instagram'),
#     (3, 'Python is great for data analysis.',         '2022-03-03', 30, 2, 4, 'Facebook'),
#     (4, 'I am learning Python for machine learning.', '2022-03-04', 40, 7, 5, 'Twitter'),
#     (5, 'Python vs. R for data science.',             '2022-03-05', 50, 9, 6, 'Instagram'),
#     (6, 'Python web development is awesome.',         '2022-03-06', 60, 1, 1, 'Facebook'),
#     (7, 'Python for finance.',                        '2022-03-07', 70, 4, 3, 'Twitter'),
#     (8, 'Python libraries for data visualization.',   '2022-03-08', 80, 6, 2, 'Instagram');
#
# -- Case-sensitive global replace, then alphabetical column order,
# -- then ORDER BY comments -- all identical to Spark.
# SELECT comments,
#        `date`,
#        id,
#        likes,
#        platform,
#        shares,
#        REPLACE(text, 'Python', 'PySpark') AS text
# FROM correct_social_media_post
# ORDER BY comments;
