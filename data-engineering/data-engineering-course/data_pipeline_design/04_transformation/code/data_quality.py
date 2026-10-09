"""Great Expectations-style data quality assertions.

A tiny implementation of the four most-used expectations.
Each function returns ``True`` if the expectation is met,
``False`` otherwise. Failures are logged with the row count
that failed.

The functions are pure: they query the table, evaluate, and
return. They don't modify the data. A pipeline can call them
in sequence and fail fast on the first ``False``.

Author: Prem Vishnoi <prem.vishnoi.example.com>
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from common import QueryRunner

log = logging.getLogger("data_quality")


def _q(sql: str) -> str:
    """Quote an identifier (table or column) for safe SQL."""
    return '"' + sql.replace('"', '""') + '"'


def expect_column_values_to_not_be_null(
    q: QueryRunner, table: str, col: str
) -> bool:
    """Assert that ``col`` in ``table`` has no NULLs.

    Returns ``True`` if the expectation is met, ``False`` if
    any row has a NULL in the column.
    """
    sql = f"SELECT COUNT(*) AS n FROM {_q(table)} WHERE {_q(col)} IS NULL"
    result = q.query_one(sql)
    n = (result or {}).get("n", 0) or 0
    if n:
        log.warning("not_null failed for %s.%s: %d NULLs", table, col, n)
        return False
    return True


def expect_column_values_to_be_unique(
    q: QueryRunner, table: str, col: str
) -> bool:
    """Assert that ``col`` in ``table`` has no duplicate values."""
    sql = (
        f"SELECT COUNT(*) - COUNT(DISTINCT {_q(col)}) AS dup_count "
        f"FROM {_q(table)}"
    )
    result = q.query_one(sql)
    n = (result or {}).get("dup_count", 0) or 0
    if n:
        log.warning("unique failed for %s.%s: %d duplicates", table, col, n)
        return False
    return True


def expect_column_value_lengths_to_be_between(
    q: QueryRunner,
    table: str,
    col: str,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
) -> bool:
    """Assert that the length of ``col`` is between ``min_length`` and
    ``max_length`` (inclusive on both ends).

    ``min_length`` defaults to 0. ``max_length`` defaults to
    ``None`` (no upper bound). NULLs are ignored.
    """
    lo = min_length if min_length is not None else 0
    hi_clause = f"AND LENGTH({_q(col)}) <= {int(max_length)}" if max_length is not None else ""
    sql = (
        f"SELECT COUNT(*) AS n FROM {_q(table)} "
        f"WHERE {_q(col)} IS NOT NULL "
        f"AND (LENGTH({_q(col)}) < {lo} {hi_clause})"
    )
    result = q.query_one(sql)
    n = (result or {}).get("n", 0) or 0
    if n:
        log.warning(
            "length_between failed for %s.%s: %d out-of-range",
            table, col, n,
        )
        return False
    return True


def expect_column_values_to_be_in_set(
    q: QueryRunner, table: str, col: str, value_set: List[Any]
) -> bool:
    """Assert that all non-NULL values of ``col`` are in ``value_set``."""
    placeholders = ", ".join("?" for _ in value_set)
    sql = (
        f"SELECT COUNT(*) AS n FROM {_q(table)} "
        f"WHERE {_q(col)} IS NOT NULL "
        f"AND {_q(col)} NOT IN ({placeholders})"
    )
    result = q.query_one(sql, list(value_set))
    n = (result or {}).get("n", 0) or 0
    if n:
        log.warning("in_set failed for %s.%s: %d out-of-set", table, col, n)
        return False
    return True


def expect_row_count_to_be_between(
    q: QueryRunner, table: str, min_value: int, max_value: int
) -> bool:
    """Assert that the row count of ``table`` is between ``min_value``
    and ``max_value`` (inclusive).
    """
    sql = f"SELECT COUNT(*) AS n FROM {_q(table)}"
    result = q.query_one(sql)
    n = (result or {}).get("n", 0) or 0
    if not (min_value <= n <= max_value):
        log.warning(
            "row_count_between failed for %s: %d not in [%d, %d]",
            table, n, min_value, max_value,
        )
        return False
    return True


def expect_column_mean_to_be_between(
    q: QueryRunner, table: str, col: str, min_value: float, max_value: float
) -> bool:
    """Assert that the mean of numeric ``col`` is between ``min_value``
    and ``max_value``. NULLs are ignored.
    """
    sql = f"SELECT AVG({_q(col)}) AS mean FROM {_q(table)}"
    result = q.query_one(sql)
    mean = (result or {}).get("mean")
    if mean is None:
        # No rows: vacuously true.
        return True
    if not (min_value <= mean <= max_value):
        log.warning(
            "mean_between failed for %s.%s: mean=%.2f not in [%.2f, %.2f]",
            table, col, mean, min_value, max_value,
        )
        return False
    return True


def run_suite(
    q: QueryRunner, expectations: List[Dict[str, Any]]
) -> Dict[str, bool]:
    """Run a list of expectations and return per-expectation results.

    Each expectation is a dict like::

        {"fn": "expect_column_values_to_not_be_null",
         "args": ["users", "email"]}

    The function looks up the named function in this module.
    """
    import inspect

    results: Dict[str, bool] = {}
    for exp in expectations:
        name = exp["fn"]
        args = exp.get("args", [])
        kwargs = exp.get("kwargs", {})
        fn = globals().get(name)
        if fn is None or not callable(fn):
            log.error("unknown expectation: %s", name)
            results[name] = False
            continue
        try:
            sig = inspect.signature(fn)
            bound = sig.bind_partial(q, *args, **kwargs)
            results[name] = fn(*bound.args, **bound.kwargs)
        except Exception as exc:  # noqa: BLE001
            log.error("expectation %s raised: %s", name, exc)
            results[name] = False
    return results
