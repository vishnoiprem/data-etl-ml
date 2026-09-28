"""
Q75: Email Validation Filter   [Easy | Regular Expression]
DataVidhya slug: email-validation-filter

Keep only emails that start with a letter, use only [A-Za-z0-9_.-] in the local
part, and end EXACTLY with '@dataplatform.com'.

NOTE ON THE SOURCE DATA:
The site's explanation says "The table contains 7 rows in total" but only 6 are
published. This file uses the 6 published rows, which reproduce the published
expected output (customers 1, 3, 4) exactly. The 7th row is not recoverable.

How to Think:
- Translate the three prose rules into ONE anchored pattern, in order:
      ^[A-Za-z]                     starts with a letter
      [A-Za-z0-9_.-]*               rest of the local part
      @dataplatform\\.com$           exact domain, anchored at the end
  Building it piece by piece in the same order as the spec is how you avoid
  losing a rule.
- Spark's `RLIKE` is a SEARCH (unanchored), so the `^` and `$` are doing real
  work. `regexp_like` behaves the same way.

The trap:
- The `$` anchor. Without it, 'alice@dataplatform.com.evil.net' matches, because
  the pattern is only required to appear SOMEWHERE. This is a security-shaped
  bug in a data-cleaning filter, and no row in the sample exposes it.
- The `.` in '.com' must be ESCAPED. Unescaped, `.` matches any character, so
  'alice@dataplatformXcom' would pass.
- A TRAILING HYPHEN IS VALID: 'charlie-@dataplatform.com' is in the expected
  output. Any "tidier" pattern that requires the local part to end in an
  alphanumeric drops customer 3 -- the row is there specifically to catch
  over-engineering.
- The character class is [A-Za-z0-9_.-] and the hyphen must be LAST (or
  escaped), or it reads as a range and the class breaks.
- Eve's '#' and Frank's gmail.com are the two obvious rejects; Bob has no '@'
  at all.

Spark note:
- RLIKE compiles to a java.util.regex predicate -- a narrow projection, no
  shuffle, and it pushes down to the scan on file-based sources.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("75-email-validation-filter")
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


# Anchored at both ends; '.' escaped; hyphen last in the class.
PATTERN = r"^[A-Za-z][A-Za-z0-9_.-]*@dataplatform\.com$"

# Spark SQL string literals consume ONE level of backslash escaping, so a
# pattern embedded in SQL text needs the backslash DOUBLED or the regex engine
# receives a bare '.' (which matches any character). The DataFrame API takes the
# pattern as a plain Python string and needs no doubling.
PATTERN_SQL = PATTERN.replace("\\.", "\\\\.")

# ---------------------------------------------------------- sample data
# The 6 rows DataVidhya publishes with the question.
# Customer 3's trailing hyphen is VALID and must survive.
spark.sql("""
CREATE OR REPLACE TEMP VIEW fve_sample AS
SELECT * FROM VALUES
    (1, 'Alice',   'alice@dataplatform.com'),
    (2, 'Bob',     'bob_the_great'),
    (3, 'Charlie', 'charlie-@dataplatform.com'),
    (4, 'Daniel',  'daniel.data@dataplatform.com'),
    (5, 'Eve',     'eve#2022@dataplatform.com'),
    (6, 'Frank',   'frank77@gmail.com')
AS t(customer_id, full_name, email)
""")

from pyspark.sql import functions as F

SQL = rf"""
SELECT customer_id, full_name, email
FROM fve_sample
WHERE email RLIKE '{PATTERN_SQL}'
ORDER BY customer_id
"""

spark.sql(SQL).show(truncate=False)

EXPECTED = [
    (1, "Alice",   "alice@dataplatform.com"),
    (3, "Charlie", "charlie-@dataplatform.com"),
    (4, "Daniel",  "daniel.data@dataplatform.com"),
]
expect("Q75 valid dataplatform.com emails", SQL, EXPECTED)

# DataFrame API equivalent.
df = (spark.table("fve_sample")
      .filter(F.col("email").rlike(PATTERN))
      .select("customer_id", "full_name", "email")
      .orderBy("customer_id"))
assert [tuple(r) for r in df.collect()] == EXPECTED
print("[PASS] Q75 DataFrame API matches SQL")

# ------------------------------------------------ the trailing hyphen is valid
assert any(r[2] == "charlie-@dataplatform.com" for r in spark.sql(SQL).collect())
stricter = spark.sql(r"""
SELECT COUNT(*) FROM fve_sample
WHERE email RLIKE '^[A-Za-z][A-Za-z0-9_.-]*[A-Za-z0-9]@dataplatform\\.com$'
""").collect()[0][0]
assert stricter == 2, stricter
print("[PASS] Q75 requiring an alphanumeric before '@' drops Charlie (2 rows, not 3)")

# ------------------------------------------------ the missing-$ trap
spark.sql("""
CREATE OR REPLACE TEMP VIEW fve_sample AS
SELECT * FROM VALUES
    (1, 'Alice',  'alice@dataplatform.com'),
    (9, 'Spoofer', 'evil@dataplatform.com.attacker.net')
AS t(customer_id, full_name, email)
""")
expect("Q75 the anchored pattern rejects a suffixed domain", SQL, [
    (1, "Alice", "alice@dataplatform.com"),
])

unanchored = spark.sql(r"""
SELECT customer_id FROM fve_sample
WHERE email RLIKE '^[A-Za-z][A-Za-z0-9_.-]*@dataplatform\\.com'
ORDER BY customer_id
""").collect()
assert [r[0] for r in unanchored] == [1, 9], unanchored
print("[PASS] Q75 without the '$' anchor, 'dataplatform.com.attacker.net' passes")

# ------------------------------------------------ the unescaped-dot trap
spark.sql("""
CREATE OR REPLACE TEMP VIEW fve_sample AS
SELECT * FROM VALUES
    (1, 'Alice', 'alice@dataplatform.com'),
    (8, 'Sneak', 'sneak@dataplatformXcom')
AS t(customer_id, full_name, email)
""")
expect("Q75 the escaped dot rejects 'dataplatformXcom'", SQL, [
    (1, "Alice", "alice@dataplatform.com"),
])

unescaped = spark.sql(r"""
SELECT customer_id FROM fve_sample
WHERE email RLIKE '^[A-Za-z][A-Za-z0-9_.-]*@dataplatform.com$'
ORDER BY customer_id
""").collect()
assert [r[0] for r in unescaped] == [1, 8], unescaped
print("[PASS] Q75 an unescaped '.' matches any character, so 'dataplatformXcom' passes")

# ------------------------------------------------ must start with a letter
starts = spark.sql(rf"""
SELECT '1abc@dataplatform.com' RLIKE '{PATTERN_SQL}' AS digit_start,
       '_abc@dataplatform.com' RLIKE '{PATTERN_SQL}' AS underscore_start,
       'abc@dataplatform.com'  RLIKE '{PATTERN_SQL}' AS letter_start
""").collect()[0]
assert (starts[0], starts[1], starts[2]) == (False, False, True), starts
print("[PASS] Q75 a leading digit or underscore is rejected; a leading letter passes")

# ------------------------------------------------ the SQL-literal escaping trap
# The SAME pattern behaves differently depending on how it reaches the engine.
sql_single, sql_double = spark.sql(r"""
SELECT 'sneak@dataplatformXcom' RLIKE '^[A-Za-z][A-Za-z0-9_.-]*@dataplatform\.com$'  AS single,
       'sneak@dataplatformXcom' RLIKE '^[A-Za-z][A-Za-z0-9_.-]*@dataplatform\\.com$' AS doubled
""").collect()[0]
assert (sql_single, sql_double) == (True, False), (sql_single, sql_double)
print("[PASS] Q75 in SQL text a single backslash is consumed by the string literal "
      "(match!) -- it must be doubled")

# The DataFrame API takes the pattern verbatim, so a single backslash is right there.
api_result = (spark.createDataFrame([("sneak@dataplatformXcom",)], "email STRING")
              .filter(F.col("email").rlike(PATTERN)).count())
assert api_result == 0, api_result
print("[PASS] Q75 the DataFrame API needs no doubling -- single backslash rejects it")

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0+ uses REGEXP_LIKE (or REGEXP / RLIKE) against POSIX/Java regex.
# Anchors (^, $) are required for an exact match, and the literal dot in
# '.com' is NOT a metacharacter in MySQL's REGEXP engine the way it is in
# Spark/Java -- but escaping it is still safer and identical-looking.
#
# CREATE TABLE fve_sample (
#     customer_id  INT          NOT NULL,
#     full_name    VARCHAR(64)  NOT NULL,
#     email        VARCHAR(255) NOT NULL,
#     PRIMARY KEY (customer_id),
#     KEY ix_fve_email (email)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO fve_sample (customer_id, full_name, email) VALUES
#     (1, 'Alice',   'alice@dataplatform.com'),
#     (2, 'Bob',     'bob_the_great'),
#     (3, 'Charlie', 'charlie-@dataplatform.com'),
#     (4, 'Daniel',  'daniel.data@dataplatform.com'),
#     (5, 'Eve',     'eve#2022@dataplatform.com'),
#     (6, 'Frank',   'frank77@gmail.com');
#
# -- Equivalent of the main Spark RLIKE filter.
# -- MySQL string literals do NOT consume backslashes, so a SINGLE '\\.' is
# -- passed through to the regex engine as the two-character escape sequence
# -- '\.' (matches a literal dot). Spark's SQL text needed '\\\\' for the
# -- same result; here a single backslash is enough.
# SELECT customer_id, full_name, email
# FROM fve_sample
# WHERE email REGEXP '^[A-Za-z][A-Za-z0-9_.-]*@dataplatform\\.com$'
# ORDER BY customer_id;
#
# -- Expected: rows for customer_id 1, 3, 4 (the trailing hyphen is valid).
