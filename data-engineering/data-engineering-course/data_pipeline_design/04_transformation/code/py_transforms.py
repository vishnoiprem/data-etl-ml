"""Pure-Python (no pandas) transform utilities.

The transformation layer is SQL-first, but some operations are
clearer in Python: complex type coercion, deep JSON
normalization, deduplication by composite key, enrichment
against a lookup table.

This module provides tiny, dependency-free helpers that work on
plain ``list[dict]`` inputs. The same patterns work in pandas
or PySpark with minimal changes.

Author: Prem Vishnoi <pvishnoi@avilx.com>
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple


# ---- normalization ---------------------------------------------------


def coerce_types(
    rows: Iterable[Dict[str, Any]],
    types: Dict[str, str],
) -> List[Dict[str, Any]]:
    """Coerce the values of each row to the given types.

    ``types`` maps column name → ``"int"``, ``"float"``, ``"str"``,
    ``"bool"``, or ``"json"`` (parses a JSON string into a dict).

    Bad values are passed through unchanged; the caller can
    apply a quality check after.
    """
    out: List[Dict[str, Any]] = []
    for row in rows:
        new = dict(row)
        for col, typ in types.items():
            if col not in new:
                continue
            v = new[col]
            try:
                if typ == "int":
                    new[col] = int(v) if v not in (None, "") else None
                elif typ == "float":
                    new[col] = float(v) if v not in (None, "") else None
                elif typ == "str":
                    new[col] = str(v) if v is not None else None
                elif typ == "bool":
                    if isinstance(v, bool):
                        new[col] = v
                    elif isinstance(v, str):
                        new[col] = v.lower() in ("true", "1", "yes")
                    else:
                        new[col] = bool(v)
                elif typ == "json":
                    if isinstance(v, str):
                        new[col] = json.loads(v) if v else None
                    else:
                        new[col] = v
            except (ValueError, json.JSONDecodeError):
                # Leave the value as-is; quality check can flag it.
                pass
        out.append(new)
    return out


def normalize_keys(
    rows: Iterable[Dict[str, Any]],
    case: str = "lower",
) -> List[Dict[str, Any]]:
    """Normalize dict keys to lower or upper snake_case.

    Useful when ingesting JSON where keys are camelCase or
    PascalCase.
    """
    out: List[Dict[str, Any]] = []
    for row in rows:
        new = {}
        for k, v in row.items():
            if case == "lower":
                new[k.lower()] = v
            elif case == "upper":
                new[k.upper()] = v
            else:
                new[k] = v
        out.append(new)
    return out


def parse_dates(
    rows: Iterable[Dict[str, Any]],
    columns: Sequence[str],
    fmt: str = "%Y-%m-%dT%H:%M:%SZ",
) -> List[Dict[str, Any]]:
    """Parse ISO-8601 strings in the given columns into ``datetime``."""
    out: List[Dict[str, Any]] = []
    for row in rows:
        new = dict(row)
        for col in columns:
            v = new.get(col)
            if isinstance(v, str) and v:
                try:
                    new[col] = datetime.strptime(v, fmt)
                except ValueError:
                    pass
        out.append(new)
    return out


# ---- deduplication ---------------------------------------------------


def dedupe_by_key(
    rows: Iterable[Dict[str, Any]],
    keys: Sequence[str],
    strategy: str = "last",
) -> List[Dict[str, Any]]:
    """Deduplicate rows by a composite key.

    ``strategy`` is ``"last"`` (keep the most recent) or
    ``"first"`` (keep the earliest).
    """
    seen: Dict[Tuple[Any, ...], Dict[str, Any]] = {}
    for row in rows:
        k = tuple(row.get(key) for key in keys)
        if strategy == "last":
            seen[k] = row
        else:
            seen.setdefault(k, row)
    return list(seen.values())


# ---- enrichment ------------------------------------------------------


def enrich(
    rows: Iterable[Dict[str, Any]],
    lookup: Dict[Any, Dict[str, Any]],
    on: str,
    columns: Optional[Sequence[str]] = None,
    how: str = "left",
) -> List[Dict[str, Any]]:
    """Left/right join ``rows`` against ``lookup`` on column ``on``.

    If ``columns`` is None, all columns of the lookup are added.
    Otherwise, only the named columns are added (with a prefix
    ``_`` if they collide with existing column names).
    """
    # Decide the column set once, using a sample of the lookup
    # so the left-join null-fill knows what to add.
    sample_match = next(iter(lookup.values()), {}) if lookup else {}
    if columns is None:
        add_cols = list(sample_match.keys())
    else:
        add_cols = list(columns)

    out: List[Dict[str, Any]] = []
    for row in rows:
        new = dict(row)
        match = lookup.get(row.get(on))
        if match is None:
            if how == "inner":
                continue
            for col in add_cols:
                if col not in new:
                    new[col] = None
        else:
            for col in add_cols:
                v = match.get(col)
                target = col if col not in new else f"_{col}"
                new[target] = v
        out.append(new)
    return out


# ---- aggregation -----------------------------------------------------


def group_aggregate(
    rows: Iterable[Dict[str, Any]],
    by: Sequence[str],
    aggs: Dict[str, Tuple[str, Callable[[List[Any]], Any]]],
) -> List[Dict[str, Any]]:
    """Group by ``by`` and apply aggregations.

    ``aggs`` maps output column → (input column, function).
    """
    grouped: Dict[Tuple[Any, ...], List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        k = tuple(row.get(b) for b in by)
        grouped[k].append(row)

    out: List[Dict[str, Any]] = []
    for k, group in grouped.items():
        result: Dict[str, Any] = dict(zip(by, k))
        for out_col, (in_col, fn) in aggs.items():
            values = [r.get(in_col) for r in group if r.get(in_col) is not None]
            result[out_col] = fn(values) if values else None
        out.append(result)
    return out
