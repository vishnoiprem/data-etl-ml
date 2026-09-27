"""
Q78: Social Media PII Extraction   [Easy | String Manipulation]
DataVidhya slug: social-media-pii-extraction

Mask phones to '******' + last 4 digits, reduce emails to their domain, cast
user_id to INT. Columns in the order anon_phone, email_domain, user_id, sorted
by anon_phone.

How to Think:
- Three independent row-level transforms; the query is one projection.
    domain      -> everything after '@'      SUBSTRING_INDEX(email, '@', -1)
    masked      -> '******' || last 4 digits CONCAT('******', RIGHT(phone, 4))
    user_id     -> CAST(... AS INT)
- The privacy framing is real: this is a redaction step, so the output must not
  carry the original phone or the local part of the email at all. Selecting
  them "just for debugging" is the thing you must not do here.

The trap:
- THE SORT IS ON A STRING. anon_phone is '******1234' etc., so sorting it puts
  user 5 first and user 3 last -- the output is deliberately NOT in user_id
  order. The site's own explanation calls this out. Sorting by user_id gives
  five well-formed rows in the wrong order.
- COLUMN ORDER is anon_phone, email_domain, user_id -- not the table's order
  and not alphabetical. The spec states it explicitly because it is scored.
- `SUBSTRING_INDEX(email, '@', 1)` (positive 1) returns the LOCAL PART -- the
  exact opposite of what is wanted, and a PII leak. It must be -1.
- user_id is stored as TEXT and must come back as an INT, so a string '10'
  would sort before '2' if left as text. Cast it.
- '******' is exactly SIX asterisks for a 10-digit phone. Count them.

Spark note:
- A single narrow projection: no shuffle except the final sort.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("78-social-media-pii-extraction")
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


MASK = "******"   # six asterisks for the first six digits of a 10-digit phone

# ---------------------------------------------------------- sample data
# Exactly the rows DataVidhya ships with the question. All columns are TEXT.
spark.sql("""
CREATE OR REPLACE TEMP VIEW social_media_pii_input AS
SELECT * FROM VALUES
    ('1', 'alice@example.com',  '5551234567'),
    ('2', 'bob@domain.net',     '5559876543'),
    ('3', 'carol@email.org',    '5551239876'),
    ('4', 'dave@site.com',      '5554567890'),
    ('5', 'eve@platform.io',    '5559871234')
AS t(user_id, email, phone)
""")

from pyspark.sql import functions as F

# -1 takes the LAST segment (the domain). Positive 1 would leak the local part.
SQL = f"""
SELECT CONCAT('{MASK}', RIGHT(phone, 4))        AS anon_phone,
       SUBSTRING_INDEX(email, '@', -1)          AS email_domain,
       CAST(user_id AS INT)                     AS user_id
FROM social_media_pii_input
ORDER BY anon_phone                              -- STRING sort, not user_id order
"""

spark.sql(SQL).show(truncate=False)

EXPECTED = [
    ("******1234", "platform.io", 5),
    ("******4567", "example.com", 1),
    ("******6543", "domain.net",  2),
    ("******7890", "site.com",    4),
    ("******9876", "email.org",   3),
]
expect("Q78 redacted PII projection", SQL, EXPECTED)

# DataFrame API equivalent.
df = (spark.table("social_media_pii_input")
      .select(F.concat(F.lit(MASK), F.expr("right(phone, 4)")).alias("anon_phone"),
              F.substring_index("email", "@", -1).alias("email_domain"),
              F.col("user_id").cast("int").alias("user_id"))
      .orderBy("anon_phone"))
assert [tuple(r) for r in df.collect()] == EXPECTED
print("[PASS] Q78 DataFrame API matches SQL")

# ------------------------------------------------ the sort order is the question
ids = [r[2] for r in spark.sql(SQL).collect()]
assert ids == [5, 1, 2, 4, 3], ids
print("[PASS] Q78 sorting by anon_phone gives user order 5,1,2,4,3 -- not 1..5")

# ------------------------------------------------ column order and types
cols = spark.sql(SQL).columns
assert cols == ["anon_phone", "email_domain", "user_id"], cols
types = dict(spark.sql(SQL).dtypes)
assert types["user_id"] == "int", types
print(f"[PASS] Q78 columns are {cols} with user_id typed {types['user_id']}")

# ------------------------------------------------ the substring_index direction trap
leak, correct = spark.sql("""
SELECT SUBSTRING_INDEX('alice@example.com', '@',  1) AS leaked_local,
       SUBSTRING_INDEX('alice@example.com', '@', -1) AS domain
""").collect()[0]
assert (leak, correct) == ("alice", "example.com"), (leak, correct)
print("[PASS] Q78 positive index returns 'alice' (a PII leak); -1 returns 'example.com'")

# ------------------------------------------------ the mask is exactly six stars
assert len(MASK) == 6
masked = spark.sql(SQL).collect()[0][0]
assert len(masked) == 10 and masked.startswith("******") and masked[6:] == "1234"
print(f"[PASS] Q78 '{masked}' is 6 stars + 4 digits = 10 characters")

# ------------------------------------------------ no original PII survives
row = spark.sql(SQL).collect()[0]
assert "eve" not in str(row) and "5559871234" not in str(row), row
print("[PASS] Q78 neither the email local part nor the full phone appears in the output")

# ------------------------------------------------ the text-sort trap on user_id
# Left as TEXT, '10' would sort before '2'. The cast prevents that downstream.
text_sorted = [r[0] for r in spark.sql("""
SELECT user_id FROM VALUES ('2'), ('10') AS t(user_id) ORDER BY user_id
""").collect()]
int_sorted = [r[0] for r in spark.sql("""
SELECT CAST(user_id AS INT) AS user_id FROM VALUES ('2'), ('10') AS t(user_id) ORDER BY user_id
""").collect()]
assert text_sorted == ["10", "2"] and int_sorted == [2, 10]
print("[PASS] Q78 as text, '10' sorts before '2'; cast to INT it does not")
