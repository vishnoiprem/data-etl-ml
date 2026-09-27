"""
Q74: Duplicate Job Listings   [Easy | Aggregate Functions, Deduplication]
DataVidhya slug: duplicate-job-listings

Count the DISTINCT COMPANIES that have posted the same title more than once.

How to Think:
- Aggregate-of-an-aggregate again (same shape as Q45), and naming the grains is
  the whole job:
    inner -> one row per (company, title) with a count, kept only where > 1
    outer -> COUNT(DISTINCT company_id) over those rows
- The answer is a single scalar, so no GROUP BY in the outer query.

The trap:
- The outer count must be DISTINCT on company_id. A company that duplicated TWO
  different titles would otherwise be counted twice. The shipped data has only
  one duplicated title per company, so a plain COUNT(*) gives the same 2 --
  asserted on constructed data below.
- Only the TITLE identifies a duplicate; `description` is explicitly ignored.
  Grouping by (company_id, title, description) is the natural-looking mistake.
  Here the duplicated rows happen to share descriptions too, so it cannot be
  caught by the sample -- asserted separately.
- Company 2 posted "Software Engineer" as well, but only ONCE. Duplication is
  per-company, not global: grouping by title alone would flag it, giving 2
  companies for the wrong reason (companies 1 and 3 by luck, or a different
  set entirely).
- `HAVING COUNT(*) > 1`, not `>= 1`.

Spark note:
- Two shuffles, but the first collapses to one row per (company, title), so the
  second is tiny.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("74-duplicate-job-listings")
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
# Company 1 repeats "Software Engineer"; company 3 repeats "Sales Manager".
# Company 2 also posts "Software Engineer" but only once.
spark.sql("""
CREATE OR REPLACE TEMP VIEW job_listings AS
SELECT * FROM VALUES
    (1, 1, 'Software Engineer', 'Build scalable systems'),
    (2, 1, 'Software Engineer', 'Build scalable systems'),
    (3, 1, 'Data Analyst',      'Analyze trends'),
    (4, 2, 'Software Engineer', 'Build scalable systems'),
    (5, 2, 'Product Manager',   'Manage products'),
    (6, 3, 'Sales Manager',     'Lead sales team'),
    (7, 3, 'Sales Manager',     'Lead sales team'),
    (8, 4, 'DevOps Engineer',   'Deploy systems')
AS t(job_id, company_id, title, description)
""")

from pyspark.sql import functions as F

# Group by (company, title) only -- description is ignored by spec.
SQL = """
SELECT COUNT(DISTINCT company_id) AS duplicate_company_count
FROM (
    SELECT company_id, title
    FROM job_listings
    GROUP BY company_id, title
    HAVING COUNT(*) > 1
)
"""

spark.sql(SQL).show(truncate=False)

expect("Q74 companies with a repeated title", SQL, [(2,)])

# DataFrame API equivalent.
df = (spark.table("job_listings")
      .groupBy("company_id", "title")
      .agg(F.count(F.lit(1)).alias("n"))
      .filter(F.col("n") > 1)
      .agg(F.countDistinct("company_id").alias("duplicate_company_count")))
assert [tuple(r) for r in df.collect()] == [(2,)]
print("[PASS] Q74 DataFrame API matches SQL")

# ------------------------------------------------ show which companies
which = spark.sql("""
SELECT company_id, title, COUNT(*) AS n
FROM job_listings GROUP BY company_id, title HAVING COUNT(*) > 1
ORDER BY company_id
""").collect()
assert [(r[0], r[1], r[2]) for r in which] == [
    (1, "Software Engineer", 2), (3, "Sales Manager", 2),
], which
print("[PASS] Q74 flagged: company 1 (Software Engineer x2), company 3 (Sales Manager x2)")

# ------------------------------------------------ the per-company scoping trap
# Grouping by title alone treats company 2's single posting as part of a
# 3-way duplicate and flags companies 1, 2 AND 3.
global_titles = spark.sql("""
SELECT COUNT(DISTINCT company_id) AS c FROM job_listings
WHERE title IN (SELECT title FROM job_listings GROUP BY title HAVING COUNT(*) > 1)
""").collect()[0][0]
assert global_titles == 3, global_titles
print("[PASS] Q74 grouping by title alone flags 3 companies -- duplication is per-company")

# ------------------------------------------------ the DISTINCT trap
# Company 5 duplicates TWO titles. Without DISTINCT it is counted twice.
spark.sql("""
CREATE OR REPLACE TEMP VIEW job_listings AS
SELECT * FROM VALUES
    (1, 5, 'Engineer', 'a'),
    (2, 5, 'Engineer', 'a'),
    (3, 5, 'Analyst',  'b'),
    (4, 5, 'Analyst',  'b')
AS t(job_id, company_id, title, description)
""")
expect("Q74 a company duplicating two titles still counts once", SQL, [(1,)])

no_distinct = spark.sql("""
SELECT COUNT(*) AS c FROM (
    SELECT company_id, title FROM job_listings
    GROUP BY company_id, title HAVING COUNT(*) > 1
)
""").collect()[0][0]
assert no_distinct == 2, no_distinct
print("[PASS] Q74 COUNT(*) without DISTINCT returns 2 for a single company")

# ------------------------------------------------ the description trap
# Same company, same title, DIFFERENT descriptions -> still a duplicate title.
spark.sql("""
CREATE OR REPLACE TEMP VIEW job_listings AS
SELECT * FROM VALUES
    (1, 6, 'Engineer', 'first wording'),
    (2, 6, 'Engineer', 'reworded posting')
AS t(job_id, company_id, title, description)
""")
expect("Q74 differing descriptions do not save a repeated title", SQL, [(1,)])

with_descn = spark.sql("""
SELECT COUNT(DISTINCT company_id) AS c FROM (
    SELECT company_id, title FROM job_listings
    GROUP BY company_id, title, description HAVING COUNT(*) > 1
)
""").collect()[0][0]
assert with_descn == 0, with_descn
print("[PASS] Q74 including description in the GROUP BY finds no duplicates (0, not 1)")
