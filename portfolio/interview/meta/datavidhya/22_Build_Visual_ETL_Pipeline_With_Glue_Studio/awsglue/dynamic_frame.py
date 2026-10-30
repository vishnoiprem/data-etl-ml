"""``DynamicFrame`` -- the Glue-specific DataFrame wrapper.

Glue's DynamicFrame carries a schema with nullable bits + format hints
that vanilla Spark DataFrames don't. For the lab's purpose we only need
``.toDF()`` (escape hatch to Spark) plus the operations ``Filter.apply``
and ``ApplyMapping.apply`` call on us.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List

from pyspark.sql import DataFrame


class DynamicFrame:
    """Thin wrapper over a Spark DataFrame with the Glue Studio surface."""

    def __init__(self, df: DataFrame, name: str = "dynamic_frame") -> None:
        self._df = df
        self.name = name

    # ---- escape hatch
    def toDF(self) -> DataFrame:
        return self._df

    # ---- row count (Glue's DynamicFrame.count() is eager)
    def count(self) -> int:
        return self._df.count()

    # ---- schema helpers (mirrors awsglue DynamicFrame.schema)
    @property
    def schema(self) -> Dict[str, Any]:
        """Glue schema is a list of ``{name, type, partition}`` dicts."""
        return {"fields": [
            {"name": f.name, "type": f.dataType.simpleString(), "partition": 0}
            for f in self._df.schema.fields
        ]}

    # ---- direct filter (used by glue_lib Filter.apply + tests)
    def filter(self, predicate: Callable[[Any], bool]) -> "DynamicFrame":
        # Spark's .filter accepts a SQL expression OR a column-expression.
        # Glue Studio's emitted code passes a Python lambda; we evaluate
        # it row-wise via toDF().rdd.filter to honour the lambda contract.
        df = self._df
        # The emitted predicate is `lambda r: (r["status"] == "active")`,
        # so we hand each Row to the lambda.
        rows = df.rdd.filter(predicate).collect()
        # Rebuild a DataFrame from the filtered rows (preserves schema).
        from pyspark.sql import SparkSession
        spark = SparkSession.builder.getOrCreate()
        if not rows:
            return DynamicFrame(df.limit(0), name=self.name)
        return DynamicFrame(spark.createDataFrame(rows, df.schema),
                             name=self.name)

    # ---- direct ApplyMapping (used by glue_lib ApplyMapping.apply)
    def apply_mapping(self, mappings: List[Any]) -> "DynamicFrame":
        from pyspark.sql.functions import col
        from pyspark.sql.types import TimestampType

        df = self._df
        source_cols = {f.name for f in df.schema.fields}
        keep_targets: List[Any] = []
        rename_map: Dict[str, str] = {}
        cast_map: Dict[str, Any] = {}

        for src, _src_type, tgt, tgt_type in mappings:
            if src not in source_cols:
                continue                  # Glue silently drops unknown srcs
            keep_targets.append(tgt)
            if src != tgt:
                rename_map[src] = tgt
            if tgt_type == "timestamp":
                cast_map[tgt if src != tgt else src] = TimestampType()
            # Glue "string" / "long" casts are identity here -- PySpark
            # infers the source type from the catalog schema.

        projected = df.select([col(c) for c in source_cols
                                if c in {m[0] for m in mappings}])
        for src, tgt in rename_map.items():
            projected = projected.withColumnRenamed(src, tgt)
        for tgt, spark_type in cast_map.items():
            projected = projected.withColumn(tgt, col(tgt).cast(spark_type))
        return DynamicFrame(projected, name=self.name)
