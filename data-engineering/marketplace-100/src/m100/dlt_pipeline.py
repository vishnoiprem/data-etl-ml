"""
dlt_pipeline.py — Lakeflow Declarative Pipeline definitions.

Each iteration's bronze table gets promoted through:

    bronze.<id>      ─► silver.<id>      ─► gold.<id>_profile

Where:

  * `silver`  is a typed, deduplicated, expectation-checked
              view of the bronze data. Schema is normalized,
              nulls / ranges / uniqueness enforced via
              `@dlt.expect` / `@dlt.expect_or_drop`.
  * `gold`    is a per-iteration profile: row count, column
              count, null ratio per column, cardinality per
              column, distinct count, sample values. This is
              the table the agent reads to score the iteration.

The driver deploys this as a `pipeline_task` per iteration —
not a long-lived pipeline — so we stay under the Free Edition
1-active-pipeline quota. The pipeline is created, runs once,
and is destroyed.

Why a per-iteration pipeline?
  * Each bronze has a different schema. A long-lived pipeline
    would need a dynamic table per iteration; a per-iteration
    pipeline just compiles a tiny DLT spec and runs it.
  * Free Edition's 1-active-pipeline cap makes a long-lived
    pipeline impossible anyway.
  * Crash-safety: a per-iteration pipeline is a unit of work;
    if it fails, the driver retries just that one iteration.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


# ============================================================
# Result type — what the driver persists + what the agent reads
# ============================================================

@dataclass
class DLTResult:
    """What the Lakeflow pipeline produced for one iteration.

    The agent reads `gold_table` to score the iteration. The
    driver reads `expectation_pass_rate` to short-circuit bad
    iterations before spending FM API tokens. The DQX scores
    give a finer-grained quality signal than the simple
    expectation pass rate.
    """
    listing_id: str
    silver_table: str
    gold_table: str
    silver_row_count: int
    gold_row_count: int
    expectation_pass_rate: float  # 0.0 - 1.0
    column_count: int
    schema_json: str
    dq_quality_score: float = 1.0
    dq_drop_rate: float = 0.0
    dq_quarantine_rate: float = 0.0

    @property
    def summary(self) -> str:
        return (
            f"DLT {self.silver_table} → {self.gold_table}  "
            f"({self.silver_row_count:,} rows, "
            f"{self.column_count} cols, "
            f"expectations={self.expectation_pass_rate:.0%}, "
            f"dq={self.dq_quality_score:.2f})"
        )


# ============================================================
# Spec — JSON the DLT runtime reads
# ============================================================

def build_pipeline_spec(
    bronze_table: str,
    *,
    catalog: str = "marketplace_100",
    listing_id: str = "",
) -> dict:
    """Build the Lakeflow Declarative Pipeline spec for one iteration.

    Returns a dict that can be serialized to a .pipeline.yml
    and deployed via DAB. The shape mirrors the Lakeflow
    Python DSL (`@dlt.table`, `@dlt.expect`), but in JSON
    so the driver can synthesize it without a code-build step.
    """
    silver = f"{catalog}.silver.{listing_id}"
    gold = f"{catalog}.gold.{listing_id}_profile"
    return {
        "name": f"m100_dlt_{listing_id}",
        "catalog": catalog,
        "target": "silver",
        "channel": "PREVIEW",
        "edition": "ADVANCED",
        "libraries": [
            {"notebook": {"path": f"/Workspace/Users/prem/m100/dlt_{listing_id}"}},
        ],
        "configuration": {
            "bronze_table": bronze_table,
            "silver_table": silver,
            "gold_table": gold,
        },
    }


# ============================================================
# Plain-Python fallback — runs when there's no Databricks runtime.
#
# Why: the local smoke test + the unit tests need to exercise
# the bronze → silver → gold promotion without a live
# workspace. This is *not* the production path — production
# uses the Lakeflow spec above and runs it as a `pipeline_task`
# in the driver Job.
# ============================================================

def promote_locally(
    spark,
    listing_id: str,
    bronze_table: str,
    *,
    catalog: str = "marketplace_100",
) -> DLTResult:
    """Read bronze → write silver (typed) + gold (profile).

    Mirrors what the Lakeflow pipeline does in production:
      * silver:  cast common types, drop fully-empty rows,
                 compute null ratio per column.
      * gold:    one row per column with name, type, null_ratio,
                 distinct_count, sample.

    The promotion is followed by a DQX pass that:
      * Tier-WARN rules log + keep
      * Tier-DROP rules filter the row
      * Tier-QUARANTINE rules route the row to a side table
    The DQResult.quality_score is folded into the gold profile
    so the agent reads it on the next iteration.
    """
    from .dqx import DQEngine, default_rules_for_silver

    bronze = spark.read.table(bronze_table)
    if bronze.rdd.isEmpty():
        raise ValueError(f"bronze table {bronze_table} is empty")

    # ---- silver:  promote strings → typed where the column name
    # ---- looks like an int/float/timestamp, drop fully-empty rows
    silver_path = f"{catalog}.silver.{listing_id}"
    from pyspark.sql.functions import col, length, when
    from pyspark.sql.types import StringType, IntegerType, LongType, DoubleType, TimestampType

    # Type promotion: try to cast every string column to a wider type
    promoted = bronze
    for field in bronze.schema.fields:
        if not isinstance(field.dataType, StringType):
            continue
        name = field.name
        c = col(name)
        # Try int
        int_cast = when(c.rlike(r"^-?\d+$"), c.cast(IntegerType()))
        # Try float
        float_cast = when(c.rlike(r"^-?\d+\.\d+$"), c.cast(DoubleType()))
        # Default: keep as string
        promoted = promoted.withColumn(
            name,
            when(length(c) == 0, None)
            .otherwise(coalesce_typed(int_cast, float_cast, c))
        )

    # Drop rows where every promoted column is null
    non_null_cols = [c for c in promoted.columns if c != "_rescued_data"]
    promoted = promoted.na.drop(how="all", subset=non_null_cols)

    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.silver")
    promoted.write.mode("overwrite").saveAsTable(silver_path)
    silver_count = spark.read.table(silver_path).count()

    # ---- DQX pass on the silver table
    # Pull the rows as a list of dicts (small datasets only — for
    # large, we'd switch to DQX's native apply_rules on the
    # DataFrame). The agent reads the dq_quality_score + the
    # reasons from the resulting DQResult.
    silver_rows = [r.asDict() for r in spark.read.table(silver_path).collect()]
    rules = default_rules_for_silver([f.name for f in bronze.schema.fields])
    dq_engine = DQEngine(rules)
    dq_result = dq_engine.evaluate(silver_rows, listing_id=listing_id)
    logger.info("DQX %s: %s", listing_id, dq_result.summary())

    # Re-write silver with the kept rows only, and write the
    # quarantine rows to a side path so a data engineer can audit.
    if dq_result.rows_kept < dq_result.rows_in:
        kept_df = spark.createDataFrame(dq_result.kept)
        kept_df.write.mode("overwrite").saveAsTable(silver_path)
        silver_count = dq_result.rows_kept
        if dq_result.rows_quarantine:
            q_path = f"{catalog}.quarantine.{listing_id}"
            spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.quarantine")
            quarantine_df = spark.createDataFrame(
                [r for r, _ in dq_result.quarantine]
            )
            quarantine_df.write.mode("overwrite").saveAsTable(q_path)
            logger.info("DQX %s: quarantined %d rows → %s",
                        listing_id, dq_result.rows_quarantine, q_path)

    # ---- gold:  one row per column with profile metrics
    gold_path = f"{catalog}.gold.{listing_id}_profile"
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.gold")

    profile_rows = []
    for field in bronze.schema.fields:
        name = field.name
        c = col(name)
        null_count = bronze.filter(c.isNull() | (length(c) == 0) if isinstance(field.dataType, StringType) else c.isNull()).count()
        distinct_count = bronze.select(c).distinct().count()
        sample_value = (
            bronze.where(c.isNotNull())
            .select(c)
            .limit(1)
            .collect()[0][0] if bronze.count() > 0 else None
        )
        profile_rows.append({
            "column_name": name,
            "data_type": str(field.dataType),
            "null_count": null_count,
            "distinct_count": distinct_count,
            "sample_value": str(sample_value)[:200] if sample_value is not None else None,
        })

    # Write gold as a single-row table with the full profile in
    # a JSON column. Cheap, schema-stable, easy to query.
    # Also include the DQX summary so the agent can read both in
    # one query.
    profile_df = spark.createDataFrame([{
        "listing_id": listing_id,
        "column_count": len(profile_rows),
        "row_count": bronze.count(),
        "profile_json": json.dumps(profile_rows),
        "dq_quality_score": dq_result.quality_score,
        "dq_drop_rate": dq_result.drop_rate,
        "dq_quarantine_rate": dq_result.quarantine_rate,
        "dq_drop_count": dq_result.rows_drop,
        "dq_quarantine_count": dq_result.rows_quarantine,
        "dq_warn_count": dq_result.rows_warn,
        "dq_warn_reasons": json.dumps(dq_result.warn_reasons),
        "dq_quarantine_reasons": json.dumps(dq_result.quarantine_reasons),
    }])
    profile_df.write.mode("overwrite").saveAsTable(gold_path)
    gold_count = profile_df.count()

    # ---- expectation pass rate: rows kept by DQX / rows in
    expectation_pass_rate = (
        dq_result.rows_kept / dq_result.rows_in
        if dq_result.rows_in else 1.0
    )

    schema_json = json.dumps([str(f.dataType) for f in bronze.schema.fields])

    return DLTResult(
        listing_id=listing_id,
        silver_table=silver_path,
        gold_table=gold_path,
        silver_row_count=silver_count,
        gold_row_count=gold_count,
        expectation_pass_rate=expectation_pass_rate,
        column_count=len(bronze.schema.fields),
        schema_json=schema_json,
        dq_quality_score=dq_result.quality_score,
        dq_drop_rate=dq_result.drop_rate,
        dq_quarantine_rate=dq_result.quarantine_rate,
    )


def coalesce_typed(*cols):
    """Spark `coalesce` on multiple columns — picks the first non-null.

    Used to chain int → float → string casts.
    """
    from pyspark.sql.functions import coalesce
    return coalesce(*cols)
