"""Glue transforms -- the ``Filter`` and ``ApplyMapping`` Glue Studio emits.

These are the only two transforms the lab's 4-node graph uses. The real
``awsglue.transforms`` package has dozens; we ship just enough to compile
and run the script Glue Studio produces for this lab.

In production the real ``awsglue`` shadows this module. The script is
identical because both expose ``Filter.apply(frame, f, transformation_ctx)``
and ``ApplyMapping.apply(frame, mappings, transformation_ctx)``.
"""
from __future__ import annotations

from typing import Any, Callable, List

from .dynamic_frame import DynamicFrame


class Filter:
    """Glue's ``Filter.apply`` -- row-wise predicate over a DynamicFrame.

    Predicate is a ``lambda r: ...`` taking a Spark ``Row`` and returning
    bool. Glue evaluates it lazily via RDD ``.filter`` because Spark's
    DataFrame filter only accepts SQL/column expressions, not lambdas.
    """

    @staticmethod
    def apply(frame: DynamicFrame, f: Callable[[Any], bool],
              transformation_ctx: str = "") -> DynamicFrame:
        return frame.filter(f)


class ApplyMapping:
    """Glue's ``ApplyMapping.apply`` -- rename + cast + drop in one call.

    Mappings is a list of ``(src, srcType, tgt, tgtType)`` tuples. A
    source column absent from the list is dropped (Glue's documented
    behaviour -- the whole point of using ApplyMapping instead of
    ``withColumn`` + ``drop``).
    """

    @staticmethod
    def apply(frame: DynamicFrame, mappings: List[Any],
              transformation_ctx: str = "") -> DynamicFrame:
        return frame.apply_mapping(mappings)
