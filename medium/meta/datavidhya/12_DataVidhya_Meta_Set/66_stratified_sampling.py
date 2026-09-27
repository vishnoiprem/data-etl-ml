"""
Q66: Sampling and Stratified Selection   [Medium | Window Functions, Sampling]
DataVidhya slug: stratified-sampling

Per (age_group, gender) stratum, take the 2 smallest person_ids and label them
stratum_rank 1 and 2.

How to Think:
- Top-N-per-group again, with a COMPOSITE partition key. The only new idea is
  that a stratum is defined by TWO columns, so `PARTITION BY age_group, gender`.
- ROW_NUMBER is correct because person_id is a primary key: no ties are possible,
  so rank 1 and 2 are unambiguous and the sample is exactly reproducible.
- "Reproducible" is the operative word in the question. That is why the spec
  picks "smallest person_id" rather than a random draw -- deterministic ordering
  IS the sampling method here.

The trap:
- This is NOT random sampling, despite the title and the "research team"
  framing. `TABLESAMPLE`, `rand()`, or `df.sample()` all give a different answer
  on every run and cannot produce stratum_rank 1/2 at all. Naming that trade-off
  is the point: a reproducible sample is auditable, a random one is not (unless
  you pin a seed -- which is the follow-up worth volunteering).
- The output ORDER (age_group, gender, person_id) puts the F stratum BEFORE M,
  so person 13 leads and person 1 comes third. Sorting by person_id alone
  reverses the blocks and looks perfectly reasonable.
- A stratum with only ONE member must still return that member. `LIMIT 2` per
  group is not expressible without the window, and rank <= 2 handles short
  strata for free.

Spark note:
- One shuffle on the composite key. If a stratum were huge this is still cheap:
  only the top 2 per partition survive the filter.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("66-stratified-sampling")
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


PER_STRATUM = 2

# ---------------------------------------------------------- sample data
# Exactly the rows DataVidhya ships with the question.
# Two strata: (18-25, M) = 1,2,3 and (18-25, F) = 13,14,15.
spark.sql("""
CREATE OR REPLACE TEMP VIEW population AS
SELECT * FROM VALUES
    ( 1, '18-25', 'M', 'North', 'Low'),
    ( 2, '18-25', 'M', 'North', 'Medium'),
    ( 3, '18-25', 'M', 'North', 'High'),
    (13, '18-25', 'F', 'North', 'Low'),
    (14, '18-25', 'F', 'North', 'Medium'),
    (15, '18-25', 'F', 'North', 'High')
AS t(person_id, age_group, gender, region, income)
""")

from pyspark.sql import functions as F, Window as W

SQL = f"""
SELECT person_id, age_group, gender, region, income, stratum_rank
FROM (
    SELECT person_id, age_group, gender, region, income,
           ROW_NUMBER() OVER (PARTITION BY age_group, gender   -- composite stratum
                              ORDER BY person_id) AS stratum_rank
    FROM population
)
WHERE stratum_rank <= {PER_STRATUM}
ORDER BY age_group, gender, person_id
"""

spark.sql(SQL).show(truncate=False)

EXPECTED = [
    (13, "18-25", "F", "North", "Low",    1),
    (14, "18-25", "F", "North", "Medium", 2),
    ( 1, "18-25", "M", "North", "Low",    1),
    ( 2, "18-25", "M", "North", "Medium", 2),
]
expect("Q66 two smallest ids per stratum", SQL, EXPECTED)

# DataFrame API equivalent.
w = W.partitionBy("age_group", "gender").orderBy("person_id")
df = (spark.table("population")
      .withColumn("stratum_rank", F.row_number().over(w))
      .filter(F.col("stratum_rank") <= PER_STRATUM)
      .orderBy("age_group", "gender", "person_id"))
assert [tuple(r) for r in df.collect()] == EXPECTED
print("[PASS] Q66 DataFrame API matches SQL")

# ------------------------------------------------ reproducible, not random
# Running the same query twice must give identical rows.
first = [tuple(r) for r in spark.sql(SQL).collect()]
second = [tuple(r) for r in spark.sql(SQL).collect()]
assert first == second == EXPECTED
print("[PASS] Q66 two consecutive runs return identical rows -- deterministic by design")

# TABLESAMPLE cannot honour the stratum contract at all: it samples globally.
sampled = spark.sql("SELECT * FROM population TABLESAMPLE (50 PERCENT)").collect()
by_stratum = {}
for r in sampled:
    by_stratum.setdefault((r.age_group, r.gender), []).append(r.person_id)
assert len(sampled) <= 6
print(f"[PASS] Q66 TABLESAMPLE returned {len(sampled)} rows across "
      f"{len(by_stratum)} strata -- no per-stratum guarantee, no stratum_rank")

# ------------------------------------------------ the sort-order trap
# Ordering by person_id alone puts the M block first.
by_id = [r[0] for r in spark.sql(f"""
SELECT person_id FROM ({SQL.replace('ORDER BY age_group, gender, person_id', '')})
ORDER BY person_id
""").collect()]
assert by_id == [1, 2, 13, 14], by_id
print("[PASS] Q66 ordering by person_id alone reverses the strata blocks (1,2,13,14)")

# ------------------------------------------------ a short stratum keeps its one member
spark.sql("""
CREATE OR REPLACE TEMP VIEW population AS
SELECT * FROM VALUES
    ( 1, '18-25', 'M', 'North', 'Low'),
    ( 2, '18-25', 'M', 'North', 'Medium'),
    (13, '18-25', 'F', 'North', 'Low'),
    (99, '26-35', 'F', 'South', 'High')
AS t(person_id, age_group, gender, region, income)
""")
expect("Q66 strata with fewer than 2 members return all they have", SQL, [
    (13, "18-25", "F", "North", "Low",    1),
    ( 1, "18-25", "M", "North", "Low",    1),
    ( 2, "18-25", "M", "North", "Medium", 2),
    (99, "26-35", "F", "South", "High",   1),
])
