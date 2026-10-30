"""
Q68: String Parsing and JSON-like Extraction   [Medium | ETL, String Manipulation, Regex]
DataVidhya slug: string-parsing-json

metadata holds pipe-separated key=value pairs. Extract color and size as text
(EMPTY STRING when absent) and weight_value as the numeric part of weight
(NULL when absent).

How to Think:
- Turn the blob into a MAP once, then read keys off it: split on '|', then on
  '=', and `str_to_map(metadata, '\\|', '=')` does both in one call. Three
  separate regexes over the same string is the version that drifts when the
  format changes.
- Then the only work left is the two different missing-value conventions.

The trap (this IS the question):
- MISSING VALUES ARE REPRESENTED TWO DIFFERENT WAYS in the same row:
      color / size -> '' (empty string) when the key is absent
      weight_value -> NULL when absent
  Map lookup returns NULL for a missing key, so color/size need an explicit
  COALESCE(..., '') while weight_value must be left alone. Applying one
  convention to all three columns is the intended failure -- and listing 3
  (no size) and listing 6 (no weight) are the rows that catch it.
- weight is '0.3kg' -- strip the unit and CAST. `regexp_extract` with
  `[0-9.]+` pulls the numeric head. Returning '0.3' as a string fails the type.
- `regexp_extract` returns '' (not NULL) when there is no match, so casting
  gives NULL for free on listing 6 -- but only if you do not COALESCE it first.
- The pipe must be escaped in the split pattern: `|` is regex alternation, and
  `split(s, '|')` splits on every character.
- Size values are not all words: '10' and 'one size' both appear, so do not
  assume a single token or a numeric type.

Spark note:
- `str_to_map` builds the map once per row -- a single narrow projection, no
  explode, no shuffle.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("68-string-parsing-json")
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
# Listing 3 has NO size (-> ''), listing 6 has NO weight (-> NULL).
spark.sql("""
CREATE OR REPLACE TEMP VIEW product_listings AS
SELECT * FROM VALUES
    (1, 'Blue T-Shirt', 'color=blue|size=medium|weight=0.3kg',   DATE'2024-01-10'),
    (2, 'Red Dress',    'color=red|size=large|weight=0.5kg',     DATE'2024-01-12'),
    (3, 'Jeans',        'color=blue|weight=0.6kg',               DATE'2024-01-15'),
    (4, 'Winter Coat',  'color=black|size=xl|weight=2.5kg',      DATE'2024-01-18'),
    (5, 'Sneakers',     'color=white|size=10|weight=0.4kg',      DATE'2024-01-20'),
    (6, 'Shorts',       'color=green|size=small',                DATE'2024-01-22'),
    (7, 'Sweater',      'color=gray|size=medium|weight=0.7kg',   DATE'2024-01-25'),
    (8, 'Socks',        'color=black|size=one size|weight=0.1kg', DATE'2024-01-28')
AS t(listing_id, product_name, metadata, list_date)
""")

from pyspark.sql import functions as F

# Two different missing-value conventions: '' for color/size, NULL for weight.
SQL = r"""
WITH parsed AS (
    SELECT listing_id,
           product_name,
           list_date,
           str_to_map(metadata, '\\|', '=') AS kv
    FROM product_listings
)
SELECT listing_id,
       product_name,
       COALESCE(kv['color'], '') AS color,      -- absent -> empty string
       COALESCE(kv['size'],  '') AS size,       -- absent -> empty string
       CAST(NULLIF(regexp_extract(COALESCE(kv['weight'], ''), '[0-9.]+', 0), '')
            AS DOUBLE) AS weight_value,         -- absent -> NULL
       list_date
FROM parsed
ORDER BY listing_id
"""

spark.sql(SQL).show(truncate=False)

import datetime as dt


def d(day):
    return dt.date(2024, 1, day)


EXPECTED = [
    (1, "Blue T-Shirt", "blue",  "medium",   0.3, d(10)),
    (2, "Red Dress",    "red",   "large",    0.5, d(12)),
    (3, "Jeans",        "blue",  "",         0.6, d(15)),
    (4, "Winter Coat",  "black", "xl",       2.5, d(18)),
    (5, "Sneakers",     "white", "10",       0.4, d(20)),
    (6, "Shorts",       "green", "small",   None, d(22)),
    (7, "Sweater",      "gray",  "medium",   0.7, d(25)),
    (8, "Socks",        "black", "one size", 0.1, d(28)),
]
expect("Q68 parsed listing metadata", SQL, EXPECTED)

# DataFrame API equivalent.
kv = F.expr(r"str_to_map(metadata, '\\|', '=')")
df = (spark.table("product_listings")
      .withColumn("kv", kv)
      .select("listing_id", "product_name",
              F.coalesce(F.col("kv")["color"], F.lit("")).alias("color"),
              F.coalesce(F.col("kv")["size"], F.lit("")).alias("size"),
              F.nullif(F.regexp_extract(
                  F.coalesce(F.col("kv")["weight"], F.lit("")), "[0-9.]+", 0), F.lit(""))
               .cast("double").alias("weight_value"),
              "list_date")
      .orderBy("listing_id"))
assert [(r[0], r[1], r[2], r[3], r[4], r[5]) for r in df.collect()] == EXPECTED
print("[PASS] Q68 DataFrame API matches SQL")

# ------------------------------------------------ the two conventions, asserted
l3 = [r for r in spark.sql(SQL).collect() if r[0] == 3][0]
l6 = [r for r in spark.sql(SQL).collect() if r[0] == 6][0]
assert l3[3] == "" and l3[3] is not None, l3      # missing size -> ''
assert l6[4] is None, l6                          # missing weight -> NULL
print("[PASS] Q68 listing 3 missing size is '' (not NULL); listing 6 missing weight "
      "is NULL (not 0 and not '')")

# ------------------------------------------------ the unescaped-pipe trap
escaped, unescaped = spark.sql(r"""
SELECT size(split('color=blue|size=medium', '\\|')) AS escaped,
       size(split('color=blue|size=medium', '|'))   AS unescaped
""").collect()[0]
assert (escaped, unescaped) == (2, 23), (escaped, unescaped)
print(f"[PASS] Q68 escaped split gives 2 pairs; unescaped '|' splits into "
      f"{unescaped} single characters")

# ------------------------------------------------ weight must be numeric
wtype = dict(spark.sql(SQL).dtypes)["weight_value"]
assert wtype == "double", wtype
print(f"[PASS] Q68 weight_value has type {wtype} -- '0.3kg' is stripped and cast")

# ------------------------------------------------ regexp_extract returns '' not NULL
nomatch = spark.sql("SELECT regexp_extract('', '[0-9.]+', 0) AS r").collect()[0][0]
assert nomatch == "", repr(nomatch)
print("[PASS] Q68 regexp_extract with no match returns '' -- NULLIF is what makes it NULL")

# ------------------------------------------------ key order does not matter
spark.sql("""
CREATE OR REPLACE TEMP VIEW product_listings AS
SELECT * FROM VALUES
    (1, 'Reordered', 'weight=1.25kg|color=teal|size=xxl', DATE'2024-02-01'),
    (2, 'NoColor',   'size=s|weight=0.2kg',               DATE'2024-02-02')
AS t(listing_id, product_name, metadata, list_date)
""")
expect("Q68 map lookup is order-independent; a missing color is ''", SQL, [
    (1, "Reordered", "teal", "xxl", 1.25, dt.date(2024, 2, 1)),
    (2, "NoColor",   "",     "s",    0.2, dt.date(2024, 2, 2)),
])

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 has no str_to_map. The portable translation is JSON_TABLE with
# JSON_OBJECT('a', 'a\\|b', 'b', 'b\\|c'), but for the simpler pipe-delimited
# format here, a recursive CTE or SUBSTRING_INDEX chain works cleanly.
# The cleanest approach is to convert the metadata to JSON once and then
# use JSON_EXTRACT / JSON_UNQUOTE.
#
# CREATE TABLE product_listings (
#     listing_id   INT          NOT NULL,
#     product_name VARCHAR(128) NOT NULL,
#     metadata     TEXT         NOT NULL,    -- 'color=blue|size=medium|weight=0.3kg'
#     list_date    DATE         NOT NULL,
#     PRIMARY KEY (listing_id)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO product_listings (listing_id, product_name, metadata, list_date) VALUES
#     (1, 'Blue T-Shirt', 'color=blue|size=medium|weight=0.3kg',   '2024-01-10'),
#     (2, 'Red Dress',    'color=red|size=large|weight=0.5kg',     '2024-01-12'),
#     (3, 'Jeans',        'color=blue|weight=0.6kg',               '2024-01-15'),
#     (4, 'Winter Coat',  'color=black|size=xl|weight=2.5kg',      '2024-01-18'),
#     (5, 'Sneakers',     'color=white|size=10|weight=0.4kg',      '2024-01-20'),
#     (6, 'Shorts',       'color=green|size=small',                '2024-01-22'),
#     (7, 'Sweater',      'color=gray|size=medium|weight=0.7kg',   '2024-01-25'),
#     (8, 'Socks',        'color=black|size=one size|weight=0.1kg','2024-01-28');
#
# -- Strategy: rebuild the blob as JSON {"k":"v", ...}, then JSON_UNQUOTE
# -- the keys. The two different missing-value conventions are kept:
# --     COALESCE for the text keys (missing -> '')
# --     CAST(NULLIF(REGEXP_SUBSTR(...), '')) for weight (missing -> NULL)
# WITH parsed AS (
#     SELECT listing_id,
#            product_name,
#            list_date,
#            CONCAT('{"',
#                   REPLACE(metadata, '|', '","'),
#                   '"}') AS jstr
#     FROM product_listings
# )
# SELECT listing_id,
#        product_name,
#        COALESCE(JSON_UNQUOTE(JSON_EXTRACT(jstr, '$.color')), '')        AS color,
#        COALESCE(JSON_UNQUOTE(JSON_EXTRACT(jstr, '$.size')),  '')        AS size,
#        CAST(NULLIF(REGEXP_SUBSTR(
#                   COALESCE(JSON_UNQUOTE(JSON_EXTRACT(jstr, '$.weight')), ''),
#                   '^[0-9.]+'), '')
#             AS DECIMAL(10,2))                                          AS weight_value,
#        list_date
# FROM parsed
# ORDER BY listing_id;
