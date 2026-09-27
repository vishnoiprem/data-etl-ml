"""Offline pytest suite for the Glue Studio visual-ETL lab -- no AWS.

Asserts:
    - Graph JSON: 4 nodes, 3 edges, linear topology
    - Auto-generated script: contains the right glueContext / transforms calls
    - Catalog schema (pre-crawled): all columns typed string
    - End-to-end run: 9 active rows, schema-correct Parquet, status dropped,
      created_at cast to timestamp
    - Top-3 by created_at DESC returns the expected order
    - Per-day distribution is seven 1s + one 2 (C011 + C012 on 2026-09-27)
"""
from __future__ import annotations

from typing import Any, Dict

import pytest


def test_graph_has_four_nodes(graph: Dict[str, Any]) -> None:
    assert len(graph["nodes"]) == 4


def test_graph_has_three_edges(graph: Dict[str, Any]) -> None:
    assert len(graph["edges"]) == 3


def test_graph_node_types(graph: Dict[str, Any]) -> None:
    types = {n["type"] for n in graph["nodes"]}
    assert types == {"DataCatalogSource", "Filter",
                       "ChangeSchema", "S3ParquetTarget"}


def test_graph_is_linear_chain(graph: Dict[str, Any]) -> None:
    edges_from: Dict[str, list] = {n["id"]: [] for n in graph["nodes"]}
    for e in graph["edges"]:
        edges_from[e["from"]].append(e["to"])
    for v in edges_from.values():
        assert len(v) <= 1


def test_generated_script_has_three_node_comments(script_text: str) -> None:
    for marker in [
        "# Script generated for node Data Catalog source customers_raw",
        "# Script generated for node Filter active_customers",
        "# Script generated for node Change Schema mapped_customers",
        "# Script generated for node S3 Parquet target curated_customers",
    ]:
        assert marker in script_text


def test_script_uses_gluecontext_api(script_text: str) -> None:
    assert "glueContext.create_dynamic_frame.from_catalog" in script_text
    assert "Filter.apply" in script_text
    assert "ApplyMapping.apply" in script_text
    assert "write_dynamic_frame.from_options" in script_text
    assert 'format="glueparquet"' in script_text
    assert "job.init(" in script_text
    assert "job.commit()" in script_text


def test_catalog_schema_is_all_string(catalog_schema: Dict[str, Any]) -> None:
    assert len(catalog_schema["columns"]) == 5
    for col in catalog_schema["columns"]:
        assert col["type"] == "string"


def test_run_visual_job_writes_parquet(run_script,
                                          curated_dir: str) -> None:
    proc = run_script(curated_dir)
    assert proc.returncode == 0, proc.stderr


def test_output_has_nine_active_rows(run_script, spark,
                                       curated_dir: str) -> None:
    proc = run_script(curated_dir)
    assert proc.returncode == 0
    out = spark.read.parquet(curated_dir)
    assert out.count() == 9


def test_status_column_is_dropped_by_apply_mapping(run_script, spark,
                                                      curated_dir: str) -> None:
    proc = run_script(curated_dir)
    assert proc.returncode == 0
    out = spark.read.parquet(curated_dir)
    cols = [f.name for f in out.schema.fields]
    assert "status" not in cols
    assert sorted(cols) == ["created_at", "customer_id", "email", "name"]


def test_created_at_is_casted_to_timestamp(run_script, spark,
                                              curated_dir: str) -> None:
    proc = run_script(curated_dir)
    assert proc.returncode == 0
    out = spark.read.parquet(curated_dir)
    types = {f.name: f.dataType.simpleString()
              for f in out.schema.fields}
    assert types["created_at"] == "timestamp"
    assert types["customer_id"] == "string"
    assert types["name"] == "string"
    assert types["email"] == "string"


def test_top_three_newest_customers(run_script, spark,
                                       curated_dir: str) -> None:
    proc = run_script(curated_dir)
    assert proc.returncode == 0
    out = spark.read.parquet(curated_dir)
    out.createOrReplaceTempView("curated")
    top3 = spark.sql("""
        SELECT name FROM curated
        ORDER BY created_at DESC LIMIT 3
    """).collect()
    names = [r["name"] for r in top3]
    assert names == ["Leo", "Kim", "Ivan"]


def test_per_day_distribution(run_script, spark, curated_dir: str) -> None:
    proc = run_script(curated_dir)
    assert proc.returncode == 0
    out = spark.read.parquet(curated_dir)
    out.createOrReplaceTempView("curated")
    rows = spark.sql("""
        SELECT DATE(created_at) AS day, COUNT(*) AS n
        FROM curated GROUP BY DATE(created_at)
        ORDER BY day
    """).collect()
    counts = sorted(r["n"] for r in rows)
    assert counts == [1, 1, 1, 1, 1, 1, 1, 2]
    # 2026-09-27 must be the 2-customer day.
    day_with_two = [r["day"] for r in rows if r["n"] == 2]
    assert str(day_with_two[0]) == "2026-09-27"
