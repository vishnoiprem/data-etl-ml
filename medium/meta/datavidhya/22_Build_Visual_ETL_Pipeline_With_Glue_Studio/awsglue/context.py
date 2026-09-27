"""``GlueContext`` -- the offline equivalent of ``awsglue.context.GlueContext``.

Glue Studio's generated script calls:

    glueContext.create_dynamic_frame.from_catalog(
        database, table_name, transformation_ctx=...)
    glueContext.write_dynamic_frame.from_options(
        frame, connection_type, connection_options, format, format_options, ...)

``create_dynamic_frame.from_catalog`` reads from the offline catalog
under ``glue_lib/_catalog/<database>/<table_name>/`` (CSV + a sibling
``_schema.json`` declaring column types). The schema is applied as the
DynamicFrame's field types -- matching the all-string pre-crawled state
the lab starts with.

``write_dynamic_frame.from_options`` translates ``format="glueparquet"``
into ``df.write.parquet(path)``. Glue's "glueparquet" format is just
Parquet + a Glue catalog registration, which we don't simulate here --
slot 19 covers catalog registration separately.

The sub-method objects (``from_catalog``, ``from_options``) are bound
on first access via ``__getattr__`` so the API surface matches AWS.
"""
from __future__ import annotations

import glob
import json
import os
import shutil
from typing import Any, Dict, List, Optional

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import StructField, StructType

from .dynamic_frame import DynamicFrame


HERE = os.path.dirname(os.path.abspath(__file__))
CATALOG_ROOT = os.path.join(HERE, "_catalog")


# ============================================================ catalog shim
def _catalog_dir(database: str, table_name: str) -> str:
    return os.path.join(CATALOG_ROOT, database, table_name)


def _load_schema(database: str, table_name: str) -> List[Dict[str, str]]:
    schema_path = os.path.join(_catalog_dir(database, table_name),
                                "_schema.json")
    with open(schema_path, "r", encoding="utf-8") as fh:
        return json.load(fh)["columns"]


def _read_catalog_table(database: str, table_name: str,
                          spark: SparkSession) -> DataFrame:
    """CSV under ``_catalog/<db>/<table>/*.csv`` -> Spark DataFrame.

    All columns are read as string and then re-typed per the schema. For
    the lab's pre-crawled ``customers_raw`` everything is already string.
    """
    table_dir = _catalog_dir(database, table_name)
    csv_files = sorted(glob.glob(os.path.join(table_dir, "*.csv")))
    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files in offline catalog for {database}.{table_name}: "
            f"looked under {table_dir}")
    df = (spark.read
                .option("header", True)
                .option("inferSchema", False)            # all-string first
                .csv([os.path.abspath(p) for p in csv_files]))
    schema = _load_schema(database, table_name)
    # Re-apply the schema's declared types so the DynamicFrame carries
    # the same column types the Glue Data Catalog would.
    from pyspark.sql.functions import col
    type_map = {"string": "string", "int": "int", "long": "long",
                "double": "double", "boolean": "boolean",
                "timestamp": "timestamp", "date": "date"}
    for col_def in schema:
        target = type_map.get(col_def["type"], "string")
        if target == "string":
            continue
        df = df.withColumn(col_def["name"], col(col_def["name"]).cast(target))
    return df


# ============================================================ sub-methods
class _CreateDynamicFrame:
    """``glueContext.create_dynamic_frame.from_catalog(...)``."""

    def __init__(self, glue_context: "GlueContext") -> None:
        self._ctx = glue_context

    def from_catalog(self, database: str, table_name: str,
                      transformation_ctx: str = "",
                      push_down_predicate: Optional[str] = None,
                      additional_options: Optional[Dict[str, Any]] = None
                      ) -> DynamicFrame:
        df = _read_catalog_table(database, table_name, self._ctx._spark)
        return DynamicFrame(df,
                             name=transformation_ctx or f"{database}.{table_name}")


class _WriteDynamicFrame:
    """``glueContext.write_dynamic_frame.from_options(...)``."""

    def __init__(self, glue_context: "GlueContext") -> None:
        self._ctx = glue_context

    def from_options(self, frame: DynamicFrame, connection_type: str,
                      connection_options: Dict[str, Any],
                      format: str = "json",
                      format_options: Optional[Dict[str, Any]] = None,
                      transformation_ctx: str = "") -> None:
        path = connection_options.get("path")
        if not path:
            raise ValueError("connection_options['path'] is required")
        os.makedirs(path, exist_ok=True)
        # Clear any previous output so the writer produces a clean dir.
        for entry in os.listdir(path):
            full = os.path.join(path, entry)
            if os.path.isfile(full):
                os.remove(full)
            elif os.path.isdir(full):
                shutil.rmtree(full)
        df = frame.toDF()
        if format in ("parquet", "glueparquet"):
            (df.write
                .mode(connection_options.get("mode", "overwrite"))
                .format("parquet")
                .save(path))
        elif format == "json":
            df.write.mode("overwrite").json(path)
        elif format == "csv":
            df.write.mode("overwrite").csv(path)
        else:
            raise NotImplementedError(f"unsupported format: {format}")


class _CreateDataFrame:
    """``glueContext.create_data_frame.from_catalog(...)`` -- unused by lab."""

    def __init__(self, glue_context: "GlueContext") -> None:
        self._ctx = glue_context

    def from_catalog(self, database: str, table_name: str, **kwargs: Any
                      ) -> DataFrame:
        return _read_catalog_table(database, table_name, self._ctx._spark)


# ============================================================ GlueContext
class GlueContext:
    """Top-level Glue context. Mirrors ``awsglue.context.GlueContext``."""

    def __init__(self, spark_context_or_session: Any) -> None:
        # Glue accepts SparkContext OR SparkSession; normalise to SparkSession.
        self._sc_or_session = spark_context_or_session
        if hasattr(spark_context_or_session, "read"):       # already a SparkSession
            self._spark = spark_context_or_session
        elif hasattr(spark_context_or_session, "sparkSession"):  # SparkContext-ish
            self._spark = spark_context_or_session.sparkSession
        else:                                                # bare SparkContext
            self._spark = SparkSession.builder.getOrCreate()
        self.create_dynamic_frame = _CreateDynamicFrame(self)
        self.write_dynamic_frame = _WriteDynamicFrame(self)
        self.create_data_frame = _CreateDataFrame(self)

    @property
    def spark_session(self) -> SparkSession:
        """The SparkSession this GlueContext is bound to."""
        return self._spark

    def getSink(self, path: str, connection_type: str = "s3",
                 **options: Any) -> Any:
        # Real Glue returns a DataSink; the lab doesn't use it but we keep
        # the API honest.
        return {"path": path, "connection_type": connection_type, **options}
