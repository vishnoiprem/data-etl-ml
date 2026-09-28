"""Q22: Build a Visual ETL Pipeline with Glue Studio    [AWS | Glue Studio, PySpark, Data Catalog]

A runnable, **offline-first** mirror of the AWS Skill Builder lab
"Build a Visual ETL Pipeline with Glue Studio." Seven stages, seven shell
scripts that map exactly to the lab's "click in the console" steps, plus
a pytest suite that drives the same in-memory Glue Studio shim. No AWS
credentials needed for verification.

How to think:
    Glue Studio is a *UI front-end for PySpark*. The user draws nodes;
    Glue Studio emits a script; Glue runs that script on managed Spark
    workers. Offline we model the graph as JSON, ship the same script,
    and run it through a 100-line ``glue_lib`` shim that mirrors the
    ``awsglue`` package's surface. The script is identical in both
    environments -- only the import path differs.

The trap:
    Glue's ``ApplyMapping.apply`` is the *only* way Glue Studio drops
    columns. A source column not listed in the mappings list is silently
    dropped (no warning). If you forget to list every column you want to
    keep, you lose data. There is no separate "Drop Fields" node in
    Glue Studio -- the absence from ApplyMapping IS the drop.

AWS note:
    Production Glue ships the real ``awsglue`` package on the worker.
    The shim here is only for offline runs. Because the shim implements
    the same API surface the script uses, the same script runs in both
    environments. Glue Studio's UI never edits the script after it's
    generated -- so the script IS the contract.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from typing import Any, Dict, List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# The lab ships an `awsglue/` package next to this driver -- it's the
# offline shim that mirrors AWS's real `awsglue` package. Production Glue
# workers ship the real package; offline we shadow it because the lab
# dir is on sys.path (and only when this driver runs the script).
from pyspark.sql import SparkSession  # noqa: E402

from awsglue.context import GlueContext       # noqa: E402
from awsglue.dynamic_frame import DynamicFrame  # noqa: E402
from awsglue.transforms import Filter, ApplyMapping  # noqa: E402


# ============================================================ test harness
PASS, FAIL = "\u2713", "\u2717"
_results: List[Tuple[bool, str]] = []


def expect(title: str, ok: bool, detail: str = "") -> None:
    tag = PASS if ok else FAIL
    line = f"  [{tag}] {title}" + (f" -- {detail}" if detail else "")
    print(line)
    _results.append((ok, title))


def section(title: str) -> None:
    print(f"\n--- {title} ---")


# ============================================================ shared spark
def _build_spark() -> SparkSession:
    return (SparkSession.builder
            .appName("q22_visual_driver")
            .config("spark.sql.shuffle.partitions", "1")
            .config("spark.ui.showConsoleProgress", "false")
            .getOrCreate())


# ============================================================ main
def run() -> int:
    graph_path = os.path.join(HERE, "graph", "customer_etl_graph.json")
    script_path = os.path.join(HERE, "glue_jobs",
                                "customer_etl_glue_studio.py")
    sample_csv = os.path.join(HERE, "sample_data", "customers_raw.csv")
    catalog_root = os.path.join(HERE, "awsglue", "_catalog",
                                 "studio_db_local", "customers_raw")
    with open(graph_path, "r", encoding="utf-8") as fh:
        graph = json.load(fh)

    # ---------------------------------------------------------- stage 1
    section("Stage 1 -- load the visual graph")
    expect("graph is a dict", isinstance(graph, dict))
    expect("graph has 4 nodes", len(graph["nodes"]) == 4,
           f"got {len(graph['nodes'])}")
    expect("graph has 3 edges", len(graph["edges"]) == 3)
    node_types = [n["type"] for n in graph["nodes"]]
    expect("node types include DataCatalogSource",
           "DataCatalogSource" in node_types)
    expect("node types include Filter", "Filter" in node_types)
    expect("node types include ChangeSchema",
           "ChangeSchema" in node_types)
    expect("node types include S3ParquetTarget",
           "S3ParquetTarget" in node_types)

    # Validate DAG (linear chain: 0 -> 1 -> 2 -> 3).
    edges_from = {n["id"]: [] for n in graph["nodes"]}
    for e in graph["edges"]:
        edges_from[e["from"]].append(e["to"])
    expect("topology is a linear chain (no branching)",
           all(len(v) <= 1 for v in edges_from.values()))
    chain_order = list(edges_from.keys())
    for i in range(len(chain_order) - 1):
        cur = chain_order[i]
        nxt = chain_order[i + 1]
        expect(f"edge {cur} -> {nxt}", nxt in edges_from[cur])

    # ---------------------------------------------------------- stage 2
    section("Stage 2 -- verify the auto-generated PySpark script")
    expect("script file exists", os.path.isfile(script_path))
    script_text = open(script_path, "r", encoding="utf-8").read()
    for marker in [
        "# Script generated for node Data Catalog source customers_raw",
        "# Script generated for node Filter active_customers",
        "# Script generated for node Change Schema mapped_customers",
        "# Script generated for node S3 Parquet target curated_customers",
    ]:
        expect(f"comment present: {marker[:50]}...", marker in script_text)
    expect("script imports awsglue.transforms",
           "from awsglue.transforms import" in script_text)
    expect("script imports awsglue.context",
           "from awsglue.context import" in script_text)
    expect("script imports awsglue.job",
           "from awsglue.job import" in script_text)

    # ---------------------------------------------------------- stage 3
    section("Stage 3 -- inspect the (all-string) Glue catalog table")
    schema_path = os.path.join(catalog_root, "_schema.json")
    with open(schema_path, "r", encoding="utf-8") as fh:
        catalog_schema = json.load(fh)
    expect("catalog schema declares 5 columns",
           len(catalog_schema["columns"]) == 5)
    type_by_name = {c["name"]: c["type"] for c in catalog_schema["columns"]}
    for col in ("customer_id", "name", "email", "status", "created_at"):
        expect(f"catalog column '{col}' is type 'string'",
               type_by_name.get(col) == "string",
               f"got {type_by_name.get(col)!r}")

    # ---------------------------------------------------------- stage 4
    section("Stage 4 -- run the Glue Studio script")
    out_dir = tempfile.mkdtemp(prefix="q22_curated_")
    env = os.environ.copy()
    # The lab ships `awsglue.py` at the lab-dir level so the generated
    # script's `from awsglue...` resolves to the offline shim. Production
    # Glue workers have the real `awsglue` package installed system-wide;
    # the local `awsglue.py` shadows it only when this lab dir is on
    # PYTHONPATH (which it isn't in production).
    env["PYTHONPATH"] = HERE
    proc = subprocess.run(
        [sys.executable, script_path, "/unused", out_dir],
        capture_output=True, text=True, env=env)
    expect("subprocess exit code 0", proc.returncode == 0,
           f"stderr={proc.stderr[:500]}")
    expect("Parquet output written", os.path.isdir(out_dir))
    parquet_files = [f for f in os.listdir(out_dir)
                     if f.startswith("part-") and f.endswith(".parquet")]
    expect("at least one part-*.parquet present",
           len(parquet_files) >= 1,
           f"got {parquet_files}")

    # ---------------------------------------------------------- stage 5
    section("Stage 5 -- inspect the Parquet output")
    spark = _build_spark()
    spark.sparkContext.setLogLevel("ERROR")
    out_df = spark.read.parquet(out_dir)
    expect("output has 9 rows (filtered to active)",
           out_df.count() == 9, f"got {out_df.count()}")
    out_cols = [f.name for f in out_df.schema.fields]
    expect("output columns = customer_id, name, email, created_at",
           sorted(out_cols) == ["created_at", "customer_id", "email", "name"],
           f"got {out_cols}")
    expect("status column dropped by ApplyMapping",
           "status" not in out_cols)
    schema_types = {f.name: f.dataType.simpleString()
                     for f in out_df.schema.fields}
    expect("created_at is timestamp",
           schema_types.get("created_at") == "timestamp",
           f"got {schema_types.get('created_at')!r}")
    expect("customer_id stays string",
           schema_types.get("customer_id") == "string")
    expect("name stays string", schema_types.get("name") == "string")
    expect("email stays string", schema_types.get("email") == "string")

    # ---------------------------------------------------------- stage 6
    section("Stage 6 -- re-read the auto-generated script")
    expect("script calls create_dynamic_frame.from_catalog",
           "create_dynamic_frame.from_catalog" in script_text)
    expect("script calls Filter.apply", "Filter.apply" in script_text)
    expect("script calls ApplyMapping.apply",
           "ApplyMapping.apply" in script_text)
    expect("script uses format='glueparquet'",
           'format="glueparquet"' in script_text)
    expect("script calls write_dynamic_frame.from_options",
           "write_dynamic_frame.from_options" in script_text)
    expect("script wraps nodes in Job.init / Job.commit",
           "job.init(" in script_text and "job.commit()" in script_text)

    # ---------------------------------------------------------- stage 7
    section("Stage 7 -- Athena-style queries (Spark SQL)")
    out_df.createOrReplaceTempView("curated_customers")
    count_row = spark.sql("SELECT COUNT(*) AS n FROM curated_customers").first()
    expect("Athena count(*) returns 9",
           count_row["n"] == 9, f"got {count_row['n']}")

    top3 = spark.sql("""
        SELECT name, created_at
        FROM curated_customers
        ORDER BY created_at DESC LIMIT 3
    """).collect()
    expect("top 3 by created_at DESC returns 3 rows",
           len(top3) == 3, f"got {len(top3)}")
    # The two latest rows are C012 (2026-09-27 19:10) and C011 (2026-09-27 06:30).
    # The third-latest is C009 (2026-09-26 17:55).
    expect("top 3 newest customer is C012 (Leo)",
           top3[0]["name"] == "Leo",
           f"got {top3[0]['name']}")
    expect("top 3 second-newest is C011 (Kim)",
           top3[1]["name"] == "Kim",
           f"got {top3[1]['name']}")
    expect("top 3 third-newest is C009 (Ivan)",
           top3[2]["name"] == "Ivan",
           f"got {top3[2]['name']}")

    per_day = spark.sql("""
        SELECT DATE(created_at) AS day, COUNT(*) AS n
        FROM curated_customers
        GROUP BY DATE(created_at)
        ORDER BY day
    """).collect()
    expect("per-day grouping returns 8 distinct days",
           len(per_day) == 8, f"got {len(per_day)}")
    # Two customers (C011, C012) joined on 2026-09-27 -- the rest have
    # one customer each. The day-bucket distribution is the lab's
    # proof that date parsing succeeded.
    counts = sorted(r["n"] for r in per_day)
    expect("per-day distribution is seven 1s + one 2",
           counts == [1, 1, 1, 1, 1, 1, 1, 2],
           f"counts={counts}")
    expect("2026-09-27 is the 2-customer day",
           any(r["n"] == 2 and str(r["day"]) == "2026-09-27" for r in per_day))

    # ---------------------------------------------------------- summary
    total = len(_results)
    passed = sum(1 for ok, _ in _results if ok)
    print(f"\n=== {passed}/{total} checks passed ===")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(run())

# ---- MySQL way ----------------------------------------------------------
# The Glue Studio visual ETL produces a `curated_customers` table. In MySQL the
# equivalent is a single LOAD DATA INFILE + a typed `curated_customers` table,
# with the same Athena-style SQL run against it.
#
# CREATE TABLE + sample data:
#   CREATE TABLE curated_customers (
#       customer_id VARCHAR(20) PRIMARY KEY,
#       name        VARCHAR(120) NOT NULL,
#       email       VARCHAR(200) NOT NULL,
#       country     VARCHAR(60),
#       created_at  DATETIME NOT NULL,
#       KEY idx_curated_created (created_at)
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#   INSERT INTO curated_customers (customer_id, name, email, country, created_at) VALUES
#       ('C001', 'Alice',  '[email protected]',   'US', '2026-09-20 10:15:00'),
#       ('C002', 'Bob',    '[email protected]',     'US', '2026-09-21 08:42:00'),
#       ('C003', 'Cara',   '[email protected]',  'GB', '2026-09-22 14:30:00'),
#       ('C004', 'Drew',   '[email protected]', 'CA', '2026-09-23 11:00:00'),
#       ('C005', 'Eli',    '[email protected]',   'AU', '2026-09-24 09:00:00'),
#       ('C006', 'Fay',    '[email protected]',   'US', '2026-09-25 13:20:00'),
#       ('C007', 'Gus',    '[email protected]',   'NZ', '2026-09-25 19:45:00'),
#       ('C008', 'Hana',   '[email protected]', 'JP', '2026-09-26 03:10:00'),
#       ('C009', 'Ivan',   '[email protected]',   'DE', '2026-09-26 17:55:00'),
#       ('C010', 'Jane',   '[email protected]',   'US', '2026-09-27 02:00:00'),
#       ('C011', 'Kim',    '[email protected]',   'KR', '2026-09-27 06:30:00'),
#       ('C012', 'Leo',    '[email protected]',   'US', '2026-09-27 19:10:00');
#
# COUNT(*) over curated_customers:
#   SELECT COUNT(*) AS n FROM curated_customers;
#
# Top 3 newest by created_at DESC (mirrors the Athena-style Spark SQL):
#   SELECT name, created_at
#   FROM curated_customers
#   ORDER BY created_at DESC LIMIT 3;
#
# Per-day customer count (DATE(created_at) -> DATE():
#   SELECT DATE(created_at) AS day, COUNT(*) AS n
#   FROM curated_customers
#   GROUP BY DATE(created_at)
#   ORDER BY day;
#
# Notes:
# - Glue Studio's visual job emits a script that calls
#   `write_dynamic_frame.from_options(format="glueparquet")`. The MySQL
#   equivalent is one `LOAD DATA INFILE ... INTO TABLE curated_customers`
#   wrapped in a transaction (idempotent: TRUNCATE + LOAD).
# - created_at is loaded as DATETIME; `DATE(created_at)` is the MySQL equivalent
#   of Spark's `DATE(created_at)` (both yield a calendar day, time stripped).
# - The `KEY idx_curated_created (created_at)` index makes ORDER BY created_at
#   DESC LIMIT 3 a backward-index scan (cheap), matching what Athena does
#   against the Parquet metadata.
