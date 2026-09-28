"""
Q29: Index Strategy for Performance   [Hard | Aggregate Functions, Index Strategy, Performance Tuning]
DataVidhya slug: index-strategy-performance

A slow-query log stores three comma-separated column lists per query
(where_columns, join_columns, order_columns). Rank (table, column, usage_type)
candidates for indexing by priority_score = frequency * avg_execution_time / 1000.

How to Think:
- The input is three columns that all mean the same thing ("columns used this
  way"), so step one is an UNPIVOT: three SELECTs UNION ALL'd into a tidy
  (table_name, usage_type, cols) shape. Do this before you split anything --
  trying to explode three lists in one pass is how this gets tangled.
- Step two is a second normalization: split the comma list and explode. Now the
  grain is one row per (query, table, column, usage_type), which is what the
  GROUP BY needs.
- Say the grain out loud at each layer. Two reshapes stacked is exactly where
  candidates lose the thread.

The trap:
- The tie-break is a THREE-level sort and the middle level is not alphabetical:
  usage_type must order `order`, `where`, `join`. That is a deliberate
  non-lexical sequence (it is not alphabetical, and not the column order in the
  table either), so it needs an explicit CASE expression. `ORDER BY usage_type`
  silently gives join/order/where and fails.
- NULL and empty lists must be dropped, not turned into an empty column name.
  `split(NULL, ',')` is NULL and explode drops it, but `split('', ',')` yields
  one EMPTY-STRING token that survives -- so filter on trim(cols) <> '' too.
- frequency counts QUERY APPEARANCES, so it is COUNT(*) over the exploded rows,
  not COUNT(DISTINCT column_name).

Spark note:
- The UNION ALL scans slow_queries three times. On a real log you would scan
  once and `stack(3, ...)` instead, which is the Spark-idiomatic unpivot and
  reads the source a single time.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("29-index-strategy")
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
# Exactly the rows DataVidhya ships with the question. NULL means SQL NULL.
# order_columns is NULL in every row, so the schema must be declared
# explicitly -- Spark cannot infer a type from all-None values.
spark.createDataFrame(
    [
        (100001, "orders", "status,amount", None, None, 11476, 335277),
        (100002, "products", "date", "product_id", None, 4602, 933882),
    ],
    "query_id INT, table_name STRING, where_columns STRING, join_columns STRING, "
    "order_columns STRING, execution_time_ms INT, row_count INT",
).createOrReplaceTempView("slow_queries")

from pyspark.sql import functions as F

SQL = """
WITH unpivoted AS (
    SELECT query_id, table_name, execution_time_ms, 'where' AS usage_type, where_columns AS cols
    FROM slow_queries
    UNION ALL
    SELECT query_id, table_name, execution_time_ms, 'join'  AS usage_type, join_columns  AS cols
    FROM slow_queries
    UNION ALL
    SELECT query_id, table_name, execution_time_ms, 'order' AS usage_type, order_columns AS cols
    FROM slow_queries
),
tokens AS (
    SELECT query_id,
           table_name,
           execution_time_ms,
           usage_type,
           trim(col) AS column_name
    FROM unpivoted
    LATERAL VIEW explode(split(cols, ',')) t AS col
    WHERE cols IS NOT NULL
      AND trim(cols) <> ''
)
SELECT table_name,
       column_name,
       usage_type,
       COUNT(*)                                            AS frequency,
       ROUND(AVG(execution_time_ms), 2)                    AS avg_execution_time,
       ROUND(COUNT(*) * AVG(execution_time_ms) / 1000, 2)  AS priority_score
FROM tokens
WHERE column_name <> ''
GROUP BY table_name, column_name, usage_type
ORDER BY priority_score DESC,
         CASE usage_type WHEN 'order' THEN 0 WHEN 'where' THEN 1 WHEN 'join' THEN 2 END,
         column_name
"""

spark.sql(SQL).show(truncate=False)

expect("Q29 index priority ranking", SQL, [
    ("orders", "amount", "where", 1, 11476.0, 11.48),
    ("orders", "status", "where", 1, 11476.0, 11.48),
    ("products", "date", "where", 1, 4602.0, 4.60),
    ("products", "product_id", "join", 1, 4602.0, 4.60),
])

# DataFrame API equivalent -- single scan via stack(), the idiomatic unpivot.
usage_rank = F.when(F.col("usage_type") == "order", 0) \
              .when(F.col("usage_type") == "where", 1) \
              .otherwise(2)

df = (spark.table("slow_queries")
      .select("query_id", "table_name", "execution_time_ms",
              F.expr("stack(3, 'where', where_columns, "
                     "        'join',  join_columns, "
                     "        'order', order_columns) AS (usage_type, cols)"))
      .filter(F.col("cols").isNotNull() & (F.trim("cols") != ""))
      .withColumn("column_name", F.explode(F.split("cols", ",")))
      .withColumn("column_name", F.trim("column_name"))
      .filter(F.col("column_name") != "")
      .groupBy("table_name", "column_name", "usage_type")
      .agg(F.count(F.lit(1)).alias("frequency"),
           F.round(F.avg("execution_time_ms"), 2).alias("avg_execution_time"))
      .withColumn("priority_score",
                  F.round(F.col("frequency") * F.col("avg_execution_time") / 1000, 2))
      .orderBy(F.col("priority_score").desc(), usage_rank, F.col("column_name")))
assert [(r[0], r[1], r[2], r[3], float(r[4]), float(r[5])) for r in df.collect()] == [
    ("orders", "amount", "where", 1, 11476.0, 11.48),
    ("orders", "status", "where", 1, 11476.0, 11.48),
    ("products", "date", "where", 1, 4602.0, 4.60),
    ("products", "product_id", "join", 1, 4602.0, 4.60),
]
print("[PASS] Q29 DataFrame API matches SQL")

# ------------------------------------------------- the usage_type ordering trap
# Alphabetical would give join < order < where. The spec wants order/where/join.
alpha = [r[0] for r in spark.sql("""
SELECT DISTINCT usage_type FROM (
    SELECT 'where' AS usage_type UNION ALL SELECT 'join' UNION ALL SELECT 'order'
) ORDER BY usage_type
""").collect()]
spec = [r[0] for r in spark.sql("""
SELECT usage_type FROM (
    SELECT 'where' AS usage_type UNION ALL SELECT 'join' UNION ALL SELECT 'order'
)
ORDER BY CASE usage_type WHEN 'order' THEN 0 WHEN 'where' THEN 1 WHEN 'join' THEN 2 END
""").collect()]
assert alpha == ["join", "order", "where"], alpha
assert spec == ["order", "where", "join"], spec
print("[PASS] Q29 explicit CASE ordering required -- alphabetical is wrong")

# ------------------------------------------------- the empty-list trap
# split(NULL) vanishes, but split('') yields one empty token that survives.
sizes = spark.sql("""
SELECT size(split(CAST(NULL AS STRING), ',')) AS from_null,
       size(split('', ','))                   AS from_empty
""").collect()[0]
assert (sizes[0], sizes[1]) == (-1, 1), f"unexpected split sizes: {sizes}"
print("[PASS] Q29 empty string yields a phantom token -- must be filtered, not just NULL-checked")

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 has no LATERAL VIEW EXPLODE. The portable substitute is a JSON
# table: rebuild the comma-separated list as a JSON array, then use
# JSON_TABLE to expand one row per (query, column, usage_type). The CASE
# ordering for usage_type must remain explicit -- alphabetical would give
# join/order/where, but the spec is order/where/join.
#
# CREATE TABLE slow_queries (
#     query_id         INT         NOT NULL,
#     table_name       VARCHAR(32) NOT NULL,
#     where_columns    VARCHAR(64) NULL,
#     join_columns     VARCHAR(64) NULL,
#     order_columns    VARCHAR(64) NULL,
#     execution_time_ms INT        NOT NULL,
#     row_count        INT         NOT NULL,
#     PRIMARY KEY (query_id)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO slow_queries (query_id, table_name, where_columns, join_columns, order_columns, execution_time_ms, row_count) VALUES
#     (100001, 'orders',    'status,amount', NULL,    NULL, 11476, 335277),
#     (100002, 'products',  'date',          'product_id', NULL, 4602, 933882);
#
# WITH unpivoted AS (
#     SELECT query_id, table_name, execution_time_ms, 'where' AS usage_type, where_columns AS cols
#     FROM slow_queries
#     UNION ALL
#     SELECT query_id, table_name, execution_time_ms, 'join'  AS usage_type, join_columns  AS cols
#     FROM slow_queries
#     UNION ALL
#     SELECT query_id, table_name, execution_time_ms, 'order' AS usage_type, order_columns AS cols
#     FROM slow_queries
# ),
# tokens AS (
#     SELECT u.query_id, u.table_name, u.execution_time_ms, u.usage_type,
#            TRIM(j.col) AS column_name
#     FROM unpivoted u
#     JOIN JSON_TABLE(
#              CONCAT('["', REPLACE(IFNULL(u.cols, ''), ',', '","'), '"]'),
#              '$[*]' COLUMNS (col VARCHAR(64) PATH '$')
#          ) j
#     WHERE u.cols IS NOT NULL
#       AND TRIM(u.cols) <> ''
# )
# SELECT table_name,
#        column_name,
#        usage_type,
#        COUNT(*)                                              AS frequency,
#        ROUND(AVG(execution_time_ms), 2)                      AS avg_execution_time,
#        ROUND(COUNT(*) * AVG(execution_time_ms) / 1000, 2)    AS priority_score
# FROM tokens
# WHERE column_name <> ''
# GROUP BY table_name, column_name, usage_type
# ORDER BY priority_score DESC,
#          CASE usage_type WHEN 'order' THEN 0 WHEN 'where' THEN 1 WHEN 'join' THEN 2 END,
#          column_name;
#
# -- Expected:
# -- orders    amount       where  1  11476.00  11.48
# -- orders    status       where  1  11476.00  11.48
# -- products  date         where  1   4602.00   4.60
# -- products  product_id   join   1   4602.00   4.60